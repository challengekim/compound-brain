"""Vault search — progressive disclosure with keyword matching and optional LLM synthesis."""
import logging
import threading
import time

from .knowledge_scanner import scan_recent_notes

logger = logging.getLogger(__name__)

# Thread-safe TTL cache (dashboard runs in Flask thread)
_cache_lock = threading.Lock()
_search_cache: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 300  # 5 minutes


def search_vault(config, query: str, max_results: int = 10, days: int = 30,
                 level: str = "titles", summarizer=None) -> list[dict] | str:
    """Progressive disclosure vault search.

    level="titles"    -> list of {title, category, saved, relevance}. Zero LLM calls.
    level="summaries" -> list of {title, category, saved, relevance, summary}. 1 LLM call.
    level="full"      -> Synthesized answer string. 1 LLM call.

    summarizer is required for level="summaries" and level="full".
    """
    notes = _cached_scan(config, query, max_results, days)

    if not notes:
        if level == "full":
            return "관련 노트를 찾지 못했습니다."
        return []

    if level == "titles":
        return notes

    if summarizer is None:
        logger.warning("summarizer required for level=%s, falling back to titles", level)
        return notes

    if level == "summaries":
        return _batch_summarize(summarizer, notes)

    # level == "full"
    return _synthesize_answer(summarizer, query, notes)


def synthesize_answer(summarizer, query: str, notes: list[dict]) -> str:
    """Backward-compatible alias for search_vault with level='full'.

    Deprecated: use search_vault(config, query, level='full', summarizer=summarizer) instead.
    """
    if not notes:
        return "관련 노트를 찾지 못했습니다."
    return _synthesize_answer(summarizer, query, notes)


def _score_relevance(note: dict, keywords: list[str]) -> float:
    """Improved relevance scoring with weighted fields and recency bonus."""
    if not keywords:
        return 0.5

    title = note.get("title", "").lower()
    desc = note.get("description", "").lower()
    category = note.get("category", "").lower()
    tags = str(note.get("tags", "")).lower()

    score = 0.0
    for kw in keywords:
        if kw in title:
            score += 3.0
        if kw in tags:
            score += 2.0
        if kw in desc:
            score += 1.0
        if kw in category:
            score += 1.0

    # Recency bonus: notes from last 7 days get 1.5x
    saved = note.get("saved", "")
    if saved:
        try:
            from datetime import datetime
            saved_date = datetime.strptime(saved, "%Y-%m-%d").date()
            if (datetime.now().date() - saved_date).days <= 7:
                score *= 1.5
        except ValueError:
            pass

    # Normalize to 0-1 range (max possible = 7 keywords * 7 points * 1.5 recency)
    max_possible = max(len(keywords) * 7 * 1.5, 1)
    return min(score / max_possible, 1.0)


def _cached_scan(config, query: str, max_results: int, days: int) -> list[dict]:
    """Return cached title-level results or compute fresh."""
    cache_key = f"{query}:{max_results}:{days}"
    now = time.time()

    with _cache_lock:
        if cache_key in _search_cache:
            expiry, results = _search_cache[cache_key]
            if now < expiry:
                return results

    # Compute outside lock
    notes = scan_recent_notes(config, days=days)
    keywords = [w.lower() for w in query.split() if len(w) >= 2]

    if not keywords:
        results = [
            {
                "title": n.get("title", "Untitled"),
                "category": n.get("category", ""),
                "saved": n.get("saved", ""),
                "relevance": 0.5,
                "description": n.get("description", ""),
            }
            for n in notes[:max_results]
        ]
        with _cache_lock:
            _search_cache[cache_key] = (now + _CACHE_TTL, results)
        return results

    scored = []
    for note in notes:
        relevance = _score_relevance(note, keywords)
        if relevance > 0:
            scored.append({
                "title": note.get("title", "Untitled"),
                "category": note.get("category", ""),
                "saved": note.get("saved", ""),
                "relevance": round(relevance, 3),
                "description": note.get("description", ""),
            })

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    results = scored[:max_results]

    with _cache_lock:
        _search_cache[cache_key] = (now + _CACHE_TTL, results)
        # Prune old entries
        if len(_search_cache) > 100:
            oldest = sorted(_search_cache, key=lambda k: _search_cache[k][0])
            for k in oldest[:50]:
                del _search_cache[k]

    return results


def _batch_summarize(summarizer, notes: list[dict]) -> list[dict]:
    """Generate 1-line summaries in a single LLM call."""
    note_lines = "\n".join(
        f"{i+1}. {n['title']}: {n.get('description', 'No description')}"
        for i, n in enumerate(notes[:10])
    )
    prompt = (
        f"다음 노트들의 핵심을 각각 한 줄(80자 이내)로 요약하세요.\n"
        f"형식: 번호. 요약\n\n{note_lines}"
    )
    raw = summarizer._generate(prompt)

    # Parse summaries back into notes
    result = []
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    for i, note in enumerate(notes[:10]):
        summary = ""
        for line in lines:
            if line.startswith(f"{i+1}."):
                summary = line[len(f"{i+1}."):].strip()
                break
        result.append({**note, "summary": summary or note.get("description", "")})

    return result


def _synthesize_answer(summarizer, query: str, notes: list[dict]) -> str:
    """Use LLM to synthesize an answer from matching vault notes."""
    note_context = "\n".join(
        f"- {n.get('title', 'Untitled')}: {n.get('description', 'No description')}"
        for n in notes[:10]
    )
    prompt = (
        f"사용자 질문: {query}\n\n"
        f"관련 vault 노트:\n{note_context}\n\n"
        f"위 노트들을 바탕으로 사용자의 질문에 답변해주세요. "
        f"답변에 관련 노트 제목을 언급해주세요. 한국어로 답변하세요."
    )
    return summarizer._generate(prompt)
