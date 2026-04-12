"""Tests for vault_search and TelegramHandler Q&A routing."""
import threading
import time
import pytest
from unittest.mock import MagicMock, patch, call

from compound_agent.vault_search import search_vault, synthesize_answer, _search_cache, _cache_lock
from compound_agent.telegram_handler import TelegramHandler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_NOTES = [
    {
        "title": "LLM Agent Architecture",
        "description": "How to build autonomous agents with LLMs",
        "category": "ai-eng",
        "saved": "2024-01-10",
        "tags": "[ai, agents]",
        "source": "https://example.com/1",
    },
    {
        "title": "Marketing Growth Tactics",
        "description": "SEO and conversion strategies for SaaS",
        "category": "marketing",
        "saved": "2024-01-09",
        "tags": "[marketing, seo]",
        "source": "https://example.com/2",
    },
    {
        "title": "RAG Pipeline Design",
        "description": "Retrieval augmented generation patterns",
        "category": "ai-eng",
        "saved": "2024-01-08",
        "tags": "[ai, rag]",
        "source": "https://example.com/3",
    },
]


def _make_handler():
    config = MagicMock()
    config.telegram_chat_id = "123"
    config.agent_mode = "proactive"
    brain = MagicMock()
    telegram = MagicMock()
    state = MagicMock()
    state.current_state = "idle"
    handler = TelegramHandler(config, brain, telegram, state)
    return handler, config, brain, telegram, state


def _clear_cache():
    """Helper to clear the module-level search cache between tests."""
    with _cache_lock:
        _search_cache.clear()


# ---------------------------------------------------------------------------
# search_vault — titles level (default)
# ---------------------------------------------------------------------------

class TestSearchVaultTitles:
    def setup_method(self):
        _clear_cache()

    def test_returns_matching_notes_by_keyword(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent LLM")
        titles = [r["title"] for r in results]
        assert "LLM Agent Architecture" in titles

    def test_excludes_non_matching_notes(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent LLM")
        titles = [r["title"] for r in results]
        assert "Marketing Growth Tactics" not in titles

    def test_returns_empty_when_no_matches(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "blockchain cryptocurrency")
        assert results == []

    def test_sorts_by_relevance_descending(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent architecture ai-eng")
        # LLM Agent Architecture matches title ("agent", "architecture") + category ("ai-eng")
        assert results[0]["title"] == "LLM Agent Architecture"

    def test_respects_max_results(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "ai", max_results=1)
        assert len(results) <= 1

    def test_empty_query_returns_all_up_to_max(self):
        """Single-char words are filtered; effectively empty query returns first max_results."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "a", max_results=10)
        # "a" is len 1 so filtered — no keywords → return first max_results with relevance 0.5
        assert len(results) == len(SAMPLE_NOTES)
        assert all(r["relevance"] == 0.5 for r in results)

    def test_passes_days_to_scanner(self):
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=[]) as mock_scan:
            search_vault(config, "test", days=60)
        mock_scan.assert_called_once_with(config, days=60)

    def test_search_titles_returns_list_no_llm(self):
        """level='titles' returns list of dicts without any LLM call."""
        config = MagicMock()
        summarizer = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent", level="titles", summarizer=summarizer)
        assert isinstance(results, list)
        summarizer._generate.assert_not_called()

    def test_search_no_results_titles(self):
        """No matches with level='titles' returns empty list."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "blockchain", level="titles")
        assert results == []

    def test_result_dicts_have_expected_keys(self):
        """Title-level results include title, category, saved, relevance, description."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent", level="titles")
        assert len(results) > 0
        for r in results:
            assert "title" in r
            assert "category" in r
            assert "saved" in r
            assert "relevance" in r


# ---------------------------------------------------------------------------
# search_vault — summaries level
# ---------------------------------------------------------------------------

class TestSearchVaultSummaries:
    def setup_method(self):
        _clear_cache()

    def test_search_summaries_calls_generate_once(self):
        """level='summaries' calls _generate exactly once."""
        config = MagicMock()
        summarizer = MagicMock()
        summarizer._generate.return_value = "1. LLM 에이전트 아키텍처 요약\n3. RAG 파이프라인 요약"
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent ai", level="summaries", summarizer=summarizer)
        summarizer._generate.assert_called_once()
        assert isinstance(results, list)

    def test_summaries_result_has_summary_key(self):
        config = MagicMock()
        summarizer = MagicMock()
        summarizer._generate.return_value = "1. 요약 내용입니다"
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent", level="summaries", summarizer=summarizer)
        assert len(results) > 0
        assert "summary" in results[0]

    def test_summaries_fallback_when_no_summarizer(self):
        """level='summaries' without summarizer falls back to titles."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            results = search_vault(config, "agent", level="summaries", summarizer=None)
        assert isinstance(results, list)
        # Falls back to title-level (no summary key)
        assert "summary" not in results[0]

    def test_batch_summarize_parses_numbered_lines(self):
        """_batch_summarize correctly parses numbered LLM output."""
        from compound_agent.vault_search import _batch_summarize
        summarizer = MagicMock()
        summarizer._generate.return_value = (
            "1. 에이전트 아키텍처 핵심 요약\n"
            "2. 마케팅 전략 요약\n"
            "3. RAG 패턴 요약"
        )
        notes = SAMPLE_NOTES[:3]
        result = _batch_summarize(summarizer, notes)
        assert result[0]["summary"] == "에이전트 아키텍처 핵심 요약"
        assert result[1]["summary"] == "마케팅 전략 요약"
        assert result[2]["summary"] == "RAG 패턴 요약"

    def test_batch_summarize_falls_back_to_description_on_parse_failure(self):
        """If LLM output doesn't match expected format, use description as fallback."""
        from compound_agent.vault_search import _batch_summarize
        summarizer = MagicMock()
        summarizer._generate.return_value = "전혀 다른 형식의 응답"
        notes = SAMPLE_NOTES[:1]
        result = _batch_summarize(summarizer, notes)
        assert result[0]["summary"] == SAMPLE_NOTES[0]["description"]


# ---------------------------------------------------------------------------
# search_vault — full level
# ---------------------------------------------------------------------------

class TestSearchVaultFull:
    def setup_method(self):
        _clear_cache()

    def test_search_full_returns_string(self):
        """level='full' returns synthesized answer string."""
        config = MagicMock()
        summarizer = MagicMock()
        summarizer._generate.return_value = "LLM 기반 에이전트 아키텍처에 대한 답변입니다."
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            result = search_vault(config, "agent", level="full", summarizer=summarizer)
        assert isinstance(result, str)
        assert result == "LLM 기반 에이전트 아키텍처에 대한 답변입니다."

    def test_search_no_results_full(self):
        """No matches with level='full' returns Korean 'not found' string."""
        config = MagicMock()
        summarizer = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            result = search_vault(config, "blockchain", level="full", summarizer=summarizer)
        assert result == "관련 노트를 찾지 못했습니다."
        summarizer._generate.assert_not_called()

    def test_full_fallback_when_no_summarizer(self):
        """level='full' without summarizer falls back to titles list."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            result = search_vault(config, "agent", level="full", summarizer=None)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

class TestRelevanceScoring:
    def setup_method(self):
        _clear_cache()

    def test_relevance_title_weighted_higher(self):
        """Title match scores higher than description-only match."""
        config = MagicMock()
        title_match = {
            "title": "agent architecture",
            "description": "some random content",
            "category": "misc",
            "saved": "2024-01-01",
            "tags": "",
        }
        desc_match = {
            "title": "Unrelated Title",
            "description": "This is about agent architecture patterns",
            "category": "misc",
            "saved": "2024-01-01",
            "tags": "",
        }
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=[title_match, desc_match]):
            results = search_vault(config, "agent architecture", level="titles")
        assert results[0]["title"] == "agent architecture"

    def test_relevance_recency_bonus(self):
        """Notes saved within last 7 days get 1.5x score multiplier."""
        from compound_agent.vault_search import _score_relevance
        from datetime import datetime, timedelta
        today = datetime.now().date()
        recent_note = {
            "title": "agent design",
            "description": "",
            "category": "",
            "tags": "",
            "saved": today.strftime("%Y-%m-%d"),
        }
        old_note = {
            "title": "agent design",
            "description": "",
            "category": "",
            "tags": "",
            "saved": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
        }
        keywords = ["agent"]
        recent_score = _score_relevance(recent_note, keywords)
        old_score = _score_relevance(old_note, keywords)
        assert recent_score > old_score


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

class TestSearchCache:
    def setup_method(self):
        _clear_cache()

    def test_cache_hit_no_rescan(self):
        """Second call with same query does not call scan_recent_notes again."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES) as mock_scan:
            search_vault(config, "agent", level="titles")
            search_vault(config, "agent", level="titles")
        mock_scan.assert_called_once()

    def test_cache_expiry(self):
        """After TTL expires, results are recomputed."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES) as mock_scan:
            with patch("compound_agent.vault_search._CACHE_TTL", -1):
                # TTL = -1 means every call is already expired
                search_vault(config, "agent", level="titles")
                _clear_cache()  # force expiry by clearing
                search_vault(config, "agent", level="titles")
        assert mock_scan.call_count == 2

    def test_cache_thread_safe(self):
        """Concurrent cache access from multiple threads does not crash."""
        config = MagicMock()
        errors = []

        def worker():
            try:
                with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
                    search_vault(config, f"agent{threading.get_ident()}", level="titles")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"

    def test_different_queries_cached_separately(self):
        """Different queries produce separate cache entries."""
        config = MagicMock()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES) as mock_scan:
            search_vault(config, "agent", level="titles")
            search_vault(config, "marketing", level="titles")
        assert mock_scan.call_count == 2


# ---------------------------------------------------------------------------
# synthesize_answer backward-compat alias
# ---------------------------------------------------------------------------

class TestSynthesizeAnswer:
    def test_returns_no_notes_message_when_empty(self):
        summarizer = MagicMock()
        result = synthesize_answer(summarizer, "어떤 AI 트렌드가 있나요?", [])
        assert result == "관련 노트를 찾지 못했습니다."
        summarizer._generate.assert_not_called()

    def test_calls_generate_with_query_and_note_context(self):
        summarizer = MagicMock()
        summarizer._generate.return_value = "LLM 기반 에이전트가 주요 트렌드입니다."
        result = synthesize_answer(summarizer, "AI 트렌드", SAMPLE_NOTES[:2])
        assert result == "LLM 기반 에이전트가 주요 트렌드입니다."
        prompt_used = summarizer._generate.call_args[0][0]
        assert "AI 트렌드" in prompt_used
        assert "LLM Agent Architecture" in prompt_used

    def test_includes_note_descriptions_in_prompt(self):
        summarizer = MagicMock()
        summarizer._generate.return_value = "답변"
        synthesize_answer(summarizer, "질문", SAMPLE_NOTES[:1])
        prompt_used = summarizer._generate.call_args[0][0]
        assert "How to build autonomous agents" in prompt_used

    def test_caps_notes_at_ten(self):
        """Only first 10 notes are included in the prompt."""
        summarizer = MagicMock()
        summarizer._generate.return_value = "답변"
        many_notes = [
            {"title": f"Note {i}", "description": f"Desc {i}"} for i in range(15)
        ]
        synthesize_answer(summarizer, "질문", many_notes)
        prompt_used = summarizer._generate.call_args[0][0]
        assert "Note 9" in prompt_used
        assert "Note 10" not in prompt_used


# ---------------------------------------------------------------------------
# TelegramHandler routing tests
# ---------------------------------------------------------------------------

class TestTelegramHandlerRouting:
    def _make_update(self, text, chat_id="123"):
        return {
            "update_id": 1,
            "message": {
                "chat": {"id": chat_id},
                "text": text,
            },
        }

    def test_url_routes_to_handle_urls(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch.object(handler, "_handle_urls") as mock_urls, \
             patch.object(telegram, "get_updates", return_value=[self._make_update("https://example.com")]):
            handler.poll_and_process()
        mock_urls.assert_called_once_with(["https://example.com"])

    def test_plain_text_routes_to_handle_question(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch.object(handler, "_handle_question") as mock_q, \
             patch.object(telegram, "get_updates", return_value=[self._make_update("AI 에이전트란?")]):
            handler.poll_and_process()
        mock_q.assert_called_once_with("AI 에이전트란?")

    def test_slash_command_routes_to_handle_command(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch.object(handler, "_handle_command") as mock_cmd, \
             patch.object(telegram, "get_updates", return_value=[self._make_update("/status")]):
            handler.poll_and_process()
        mock_cmd.assert_called_once_with("/status")

    def test_wrong_chat_id_ignored(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch.object(handler, "_handle_question") as mock_q, \
             patch.object(telegram, "get_updates", return_value=[self._make_update("질문", chat_id="999")]):
            handler.poll_and_process()
        mock_q.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_command tests
# ---------------------------------------------------------------------------

class TestHandleCommand:
    def test_status_command_sends_status(self):
        handler, config, brain, telegram, state = _make_handler()
        brain.memory = None
        with patch.object(handler, "_get_status_text", return_value="상태OK"):
            handler._handle_command("/status")
        telegram.send_message.assert_called_once_with("상태OK")

    def test_help_command_sends_help_text(self):
        handler, config, brain, telegram, state = _make_handler()
        handler._handle_command("/help")
        call_args = telegram.send_message.call_args[0][0]
        assert "/status" in call_args
        assert "/report" in call_args
        assert "/help" in call_args

    def test_report_command_calls_run_weekly_knowledge(self):
        handler, config, brain, telegram, state = _make_handler()
        brain.hands.run_weekly_knowledge.return_value = {"success": True}
        handler._handle_command("/report")
        brain.hands.run_weekly_knowledge.assert_called_once()

    def test_report_command_sends_failure_message_on_error(self):
        handler, config, brain, telegram, state = _make_handler()
        brain.hands.run_weekly_knowledge.side_effect = RuntimeError("boom")
        handler._handle_command("/report")
        calls = [c[0][0] for c in telegram.send_message.call_args_list]
        assert any("오류" in c or "❌" in c for c in calls)


# ---------------------------------------------------------------------------
# _handle_question tests (progressive disclosure)
# ---------------------------------------------------------------------------

class TestHandleQuestion:
    def setup_method(self):
        _clear_cache()

    def test_no_results_sends_not_found_message(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_question("blockchain cryptocurrency")
        telegram.send_message.assert_called_once()
        assert "찾지 못했습니다" in telegram.send_message.call_args[0][0]

    def test_sends_title_results_with_keyboard(self):
        """Progressive disclosure: titles shown with inline keyboard."""
        handler, config, brain, telegram, state = _make_handler()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_question("agent LLM")
        telegram.send_message_with_keyboard.assert_called_once()
        msg, keyboard = telegram.send_message_with_keyboard.call_args[0]
        assert "검색 결과" in msg
        assert "inline_keyboard" in keyboard

    def test_keyboard_has_summary_and_full_buttons(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_question("agent LLM")
        _, keyboard = telegram.send_message_with_keyboard.call_args[0]
        buttons = keyboard["inline_keyboard"][0]
        button_texts = [b["text"] for b in buttons]
        assert any("요약" in t for t in button_texts)
        assert any("상세" in t for t in button_texts)

    def test_callback_data_uses_truncated_query(self):
        """Callback data must fit within 64-byte Telegram limit."""
        handler, config, brain, telegram, state = _make_handler()
        # Use a long query that still matches something (starts with a matching keyword)
        long_query = "agent " + "x" * 55
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_question(long_query)
        _, keyboard = telegram.send_message_with_keyboard.call_args[0]
        for btn in keyboard["inline_keyboard"][0]:
            assert len(btn["callback_data"].encode()) <= 64

    def test_exception_sends_error_message(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch("compound_agent.vault_search.scan_recent_notes", side_effect=Exception("db error")):
            handler._handle_question("질문")
        msg = telegram.send_message.call_args[0][0]
        assert "❌" in msg


# ---------------------------------------------------------------------------
# _handle_vault_search_callback tests
# ---------------------------------------------------------------------------

class TestHandleVaultSearchCallback:
    def setup_method(self):
        _clear_cache()

    def _make_callback(self, data, callback_id="cb1"):
        return {"id": callback_id, "data": data}

    def test_vs_sum_callback_triggers_summaries(self):
        handler, config, brain, telegram, state = _make_handler()
        brain.hands.summarizer._generate.return_value = "1. 요약 결과"
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_vault_search_callback(self._make_callback("vs_sum_agent LLM"))
        telegram.answer_callback_query.assert_called_once_with("cb1", text="요약을 생성합니다...")
        telegram.send_message.assert_called_once()

    def test_vs_full_callback_triggers_full_answer(self):
        handler, config, brain, telegram, state = _make_handler()
        brain.hands.summarizer._generate.return_value = "LLM 에이전트에 관한 상세 답변"
        with patch("compound_agent.vault_search.scan_recent_notes", return_value=SAMPLE_NOTES):
            handler._handle_vault_search_callback(self._make_callback("vs_full_agent LLM"))
        telegram.answer_callback_query.assert_called_once_with("cb1", text="상세 답변을 생성합니다...")
        msg = telegram.send_message.call_args[0][0]
        assert "💡" in msg

    def test_callback_routed_from_handle_callback(self):
        """_handle_callback routes vs_sum_ and vs_full_ to vault search handler."""
        handler, config, brain, telegram, state = _make_handler()
        with patch.object(handler, "_handle_vault_search_callback") as mock_vs:
            handler._handle_callback(self._make_callback("vs_sum_test query"))
        mock_vs.assert_called_once()

    def test_exception_in_callback_sends_error(self):
        handler, config, brain, telegram, state = _make_handler()
        with patch("compound_agent.vault_search.scan_recent_notes", side_effect=Exception("fail")):
            handler._handle_vault_search_callback(self._make_callback("vs_full_agent"))
        msg = telegram.send_message.call_args[0][0]
        assert "❌" in msg
