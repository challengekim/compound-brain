# Project: PKM Briefing Bot

## Overview
Automated personal knowledge management system. Sends scheduled briefings (morning, evening, weekly, trend, knowledge, meta review, LinkedIn draft) via Telegram and email.

## Architecture
- **Deployment**: Railway / Docker / Local (Procfile: `worker: python main.py`)
- **Auth**: OAuth2 refresh tokens (Gmail + Calendar scopes) stored as env vars
- **Config**: `config.yaml` for settings, `.env` for secrets. See `config.example.yaml`.
- **AI**: Gemini 2.5 Flash for summarization. Prompt templates in `prompts/{lang}/`

## Key Files
- `main.py` — Orchestrator: fetches data, runs summarizer, calls composer, sends Telegram
- `config.py` — YAML + env var configuration loader
- `gmail_client.py` — Gmail API client (OAuth2 refresh token pattern)
- `calendar_client.py` — Google Calendar API client (same auth pattern)
- `summarizer.py` — Gemini-powered summarization with external prompt templates
- `briefing_composer.py` — Pure formatting module (no API calls, HTML output)
- `telegram_sender.py` — Telegram Bot API sender with 4096-char chunking
- `setup_oauth.py` — Local OAuth2 setup script
- `setup_wizard.py` — Interactive setup wizard for new users

## Conventions
- `briefing_composer.py` is a pure formatter: receives data, returns HTML strings. No API clients inside.
- `main.py` is the only file that creates clients and orchestrates the pipeline.
- Graceful degradation: each data source (Gmail, Calendar) wrapped in try/except.
- Action items extracted via regex from Gemini output (pattern configurable in config.yaml).

## Structural Constraints (Dependency Direction)
```
config.py → *_client.py / *_fetcher.py / *_scanner.py → summarizer.py → briefing_composer.py → main.py
```
- `config.py` imports nothing from the project
- `*_client.py`, `*_fetcher.py`, `*_scanner.py` import only `config.py`
- `summarizer.py` has no project imports (standalone Gemini wrapper + prompt loader)
- `briefing_composer.py` is a pure formatter — NO API clients, NO network calls
- `main.py` is the ONLY orchestrator — creates all clients, calls all functions
- `telegram_sender.py` and `email_sender.py` are standalone senders

## Testing
```bash
python3 main.py --test morning   # Test a specific briefing type
python3 main.py --test trend     # Available: morning, evening, weekly, trend, knowledge, meta, linkedin
```
