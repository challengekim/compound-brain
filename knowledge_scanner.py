import logging
import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")


def _parse_frontmatter(filepath):
    """Extract YAML frontmatter fields from a markdown file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4000)
    except Exception:
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    fields = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def _category_from_path(filepath, vault_path):
    """Derive category from file path relative to vault."""
    rel = os.path.relpath(filepath, vault_path)
    parts = rel.split(os.sep)
    if len(parts) >= 3:
        return parts[-2]
    if len(parts) >= 2:
        return parts[-2]
    return "unknown"


def scan_recent_notes(config, days=7):
    """Scan Obsidian vault for notes saved in the last N days."""
    vault = config.obsidian_vault_path
    cutoff = datetime.now(KST) - timedelta(days=days)
    notes = []

    for scan_path in config.knowledge_scan_paths:
        full_path = os.path.join(vault, scan_path)
        if not os.path.isdir(full_path):
            continue

        for filename in os.listdir(full_path):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(full_path, filename)
            try:
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(filepath), tz=KST
                )
            except Exception:
                continue

            if mtime < cutoff:
                continue

            fm = _parse_frontmatter(filepath)
            title = fm.get("title", filename.replace(".md", ""))
            description = fm.get("description", "")
            category = _category_from_path(filepath, vault)

            notes.append({
                "title": title,
                "description": description,
                "category": category,
                "saved": fm.get("saved", mtime.strftime("%Y-%m-%d")),
                "tags": fm.get("tags", ""),
                "source": fm.get("source", ""),
            })

    notes.sort(key=lambda n: n["saved"], reverse=True)
    logger.info(f"Knowledge scan: {len(notes)} notes in last {days} days")
    return notes


def save_project_ideas(vault_path, ideas_text, date_str):
    """Append project-specific ideas to Obsidian vault for future reference."""
    ideas_dir = os.path.join(vault_path, "20_Projects", "AI Ideas")
    os.makedirs(ideas_dir, exist_ok=True)

    filepath = os.path.join(ideas_dir, "프로젝트별 적용 아이디어.md")

    entry = (
        f"\n\n## {date_str} 주간 리포트\n\n"
        f"{ideas_text}\n"
    )

    if os.path.exists(filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        header = (
            "---\n"
            "title: 프로젝트별 적용 아이디어\n"
            "description: 주간 지식 리포트에서 추출한 프로젝트별 적용 가능한 아이디어 누적 기록\n"
            "type: reference\n"
            "tags: [project-ideas, compound-learning]\n"
            "---\n\n"
            "# 프로젝트별 적용 아이디어\n\n"
            "매주 지식 리포트에서 자동 추출되어 누적됩니다.\n"
            "프로젝트별로 질문하면 이 파일을 참조합니다.\n"
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + entry)

    logger.info(f"Project ideas saved to {filepath}")


def scan_all_notes(config):
    """Scan Obsidian vault for ALL notes (no date cutoff) for content drafting."""
    vault = config.obsidian_vault_path
    notes = []

    for scan_path in config.knowledge_scan_paths:
        full_path = os.path.join(vault, scan_path)
        if not os.path.isdir(full_path):
            continue

        for filename in os.listdir(full_path):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(full_path, filename)
            fm = _parse_frontmatter(filepath)
            title = fm.get("title", filename.replace(".md", ""))
            description = fm.get("description", "")
            category = _category_from_path(filepath, vault)

            notes.append({
                "title": title,
                "description": description,
                "category": category,
                "saved": fm.get("saved", ""),
                "tags": fm.get("tags", ""),
                "source": fm.get("source", ""),
                "applicable_when": fm.get("applicable_when", ""),
                "my_relevance": fm.get("my_relevance", ""),
            })

    notes.sort(key=lambda n: n.get("saved", ""), reverse=True)
    logger.info(f"Full vault scan: {len(notes)} total notes")
    return notes
