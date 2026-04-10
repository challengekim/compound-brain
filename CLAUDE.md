# Project: Compound Brain

## Overview
Automated personal knowledge management system. Sends scheduled briefings (trend, knowledge, meta review, LinkedIn draft) via Telegram.

## Architecture
- **Deployment**: Railway / Docker / Local (Procfile: `worker: python main.py`)
- **Config**: `config.yaml` for settings, `.env` for secrets. See `config.example.yaml`.
- **AI**: Gemini 2.5 Flash for summarization. Prompt templates in `prompts/{lang}/`

## Key Files
- `main.py` — Orchestrator: fetches data, runs summarizer, calls composer, sends Telegram
- `config.py` — YAML + env var configuration loader
- `setup_wizard.py` — Interactive setup wizard for new users
- `core/summarizer.py` — AI summarization with external prompt templates
- `core/composer.py` — Pure formatting module (no API calls, HTML output)
- `core/telegram.py` — Telegram Bot API sender with 4096-char chunking
- `core/trends.py` — HN API + Reddit RSS + GeekNews Atom feed collection
- `core/scanner.py` — Obsidian vault scan + project ideas save + full vault scan for content drafting
- `core/reviewer.py` — Monthly system self-diagnosis (30-day stats + git commits)
- `core/__init__.py` — Re-exports all public symbols for clean `from core import ...`

## Conventions
- `core/composer.py` is a pure formatter: receives data, returns HTML strings. No API clients inside.
- `main.py` is the only file that creates clients and orchestrates the pipeline.
- Graceful degradation: each data source wrapped in try/except.
- All core modules live in `core/` and are re-exported via `core/__init__.py`.

## Structural Constraints (Dependency Direction)
```
config.py → core/trends.py / core/scanner.py → core/summarizer.py → core/composer.py → main.py
```
- `config.py` imports nothing from the project
- `core/trends.py`, `core/scanner.py` import only `config.py`
- `core/summarizer.py` has no project imports (standalone AI wrapper + prompt loader)
- `core/composer.py` is a pure formatter — NO API clients, NO network calls
- `core/reviewer.py` imports from `core.scanner` (internal cross-reference)
- `main.py` is the ONLY orchestrator — imports from `config` and `core`
- `core/telegram.py` is a standalone sender

## Testing
```bash
python3 main.py --test trend      # Available: trend, knowledge, meta, linkedin
```
