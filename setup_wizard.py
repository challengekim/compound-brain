#!/usr/bin/env python3
"""Interactive setup wizard for PKM Briefing Bot."""

import json
import os
import subprocess
import sys


def main():
    print("\n" + "=" * 50)
    print("  PKM Briefing Bot — Setup Wizard")
    print("=" * 50 + "\n")

    config = {}
    env = {}

    # 1. Language
    lang = input("Language (ko/en) [ko]: ").strip() or "ko"
    config["language"] = lang

    # 2. LLM Provider
    print("\n--- AI Model ---")
    print("Choose your LLM provider:\n")
    print("  1. Gemini (recommended, free tier available)")
    print("     → Free: 1,500 requests/day, no credit card needed")
    print("     → Get key: https://aistudio.google.com/apikey\n")
    print("  2. OpenRouter (100+ models, some free)")
    print("     → Free models: Gemini Flash, Llama, Mistral")
    print("     → Get key: https://openrouter.ai/keys\n")
    print("  3. OpenAI (gpt-4o-mini ~$0.5/mo)")
    print("     → Get key: https://platform.openai.com/api-keys\n")
    print("  4. Ollama (100% free, runs locally)")
    print("     → Install: https://ollama.com")
    print("     → Then: ollama pull llama3.1:8b\n")

    choice = input("Select provider [1]: ").strip() or "1"

    provider_map = {"1": "gemini", "2": "openrouter", "3": "openai", "4": "ollama"}
    provider = provider_map.get(choice, "gemini")

    default_models = {
        "gemini": "gemini-2.5-flash",
        "openrouter": "google/gemini-2.5-flash-preview-05-20:free",
        "openai": "gpt-4o-mini",
        "ollama": "llama3.1:8b",
    }

    config["llm"] = {"provider": provider}

    if provider == "ollama":
        print(f"\nDefault model: {default_models['ollama']}")
        model = input(f"Model name [{default_models['ollama']}]: ").strip()
        if model:
            config["llm"]["model"] = model
        print("No API key needed for Ollama.")
        print("Make sure Ollama is running: ollama serve")
    else:
        if provider == "gemini":
            print(f"\nGet your free API key at: https://aistudio.google.com/apikey")
            print("(Free tier: 1,500 requests/day — more than enough)")
        elif provider == "openrouter":
            print(f"\nGet your API key at: https://openrouter.ai/keys")
            print("Free models available — no payment needed")
            print(f"\nPopular free models:")
            print("  google/gemini-2.5-flash-preview-05-20:free (recommended)")
            print("  meta-llama/llama-3.3-70b-instruct:free")
            print("  mistralai/mistral-small-3.1-24b-instruct:free")
            model = input(f"\nModel [{default_models['openrouter']}]: ").strip()
            if model:
                config["llm"]["model"] = model
        elif provider == "openai":
            print(f"\nGet your API key at: https://platform.openai.com/api-keys")

        api_key = input("API Key: ").strip()

        env_key = "GEMINI_API_KEY" if provider == "gemini" else "LLM_API_KEY"
        env[env_key] = api_key

    # 3. Telegram Bot
    print("\n--- Telegram Bot ---")
    print("1. Open Telegram, search for @BotFather")
    print("2. Send /newbot and follow the prompts")
    print("3. Copy the bot token")
    bot_token = input("Bot Token: ").strip()
    env["TELEGRAM_BOT_TOKEN"] = bot_token
    print("4. Send a message to your bot, then visit:")
    print(f"   https://api.telegram.org/bot{bot_token}/getUpdates")
    print("5. Find your chat_id in the response")
    chat_id = input("Chat ID: ").strip()
    env["TELEGRAM_CHAT_ID"] = chat_id

    # 4. Google OAuth2 (optional)
    print("\n--- Google OAuth2 (optional, for email/calendar) ---")
    setup_google = input("Set up Gmail/Calendar integration? (y/n) [n]: ").strip().lower()
    if setup_google == "y":
        print("\nPrerequisites:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a project, enable Gmail API and Calendar API")
        print("3. Create OAuth2 Desktop credentials")
        print("4. Download client_secret.json to this directory")
        input("\nPress Enter when client_secret.json is ready...")

        if os.path.exists("client_secret.json"):
            for account in ["personal", "work"]:
                setup_account = input(f"\nSet up {account} account? (y/n) [n]: ").strip().lower()
                if setup_account == "y":
                    print(f"Running OAuth flow for {account}...")
                    subprocess.run([sys.executable, "setup_oauth.py", "--account", account])
        else:
            print("client_secret.json not found. Skipping OAuth setup.")
            print("You can run 'python setup_oauth.py --account personal' later.")

    # 5. Vault path
    print("\n--- Knowledge Vault ---")
    print("Where do you store your markdown notes?")
    vault = input("Vault path [./vault]: ").strip() or "./vault"
    config["vault"] = {
        "path": vault,
        "scan_paths": [
            "10_Knowledge/References/AI Engineering",
            "10_Knowledge/References/AI Tools",
            "10_Knowledge/References/Business",
            "10_Knowledge/References/Engineering",
            "10_Knowledge/References/Marketing",
            "00_Inbox/Read Later",
        ],
        "ideas_file": "20_Projects/AI Ideas/project-ideas.md",
    }

    # Create vault from template if path doesn't exist
    if not os.path.exists(vault) and os.path.exists("vault_template"):
        import shutil

        shutil.copytree("vault_template", vault)
        print(f"Created vault structure at {vault}")

    # 6. Newsletter senders
    print("\n--- Newsletter Senders ---")
    print("Enter newsletter sender names (one per line, empty line to finish):")
    senders = []
    while True:
        s = input("  > ").strip()
        if not s:
            break
        senders.append(s)
    config["accounts"] = {
        "personal": {
            "display_name": "Personal" if lang == "en" else "개인",
            "newsletter_senders": senders or ["Lenny", "Superhuman"],
        },
        "work": {
            "display_name": "Work" if lang == "en" else "회사",
            "label": input("\nWork email label [important]: ").strip() or "important",
            "skip_keywords": ["OTP", "verification", "password reset", "unsubscribe"],
        },
    }

    # 7. Projects
    print("\n--- Your Projects ---")
    print("Enter projects (empty name to finish):")
    projects = []
    while True:
        name = input("  Project name: ").strip()
        if not name:
            break
        desc = input("  Description: ").strip()
        repo = input("  Repo path (optional): ").strip()
        p = {"name": name, "description": desc}
        if repo:
            p["repo_path"] = repo
        projects.append(p)
    config["projects"] = projects or [{"name": "My Project", "description": "Description"}]

    # 8. Notifications
    email_to = input("\nEmail for weekly reports (optional): ").strip()
    if email_to:
        config["notifications"] = {"email_to": email_to}

    # 9. Schedule
    print("\n--- Schedule ---")
    tz = input("Timezone [Asia/Seoul]: ").strip() or "Asia/Seoul"
    config["schedule"] = {
        "timezone": tz,
        "morning": "08:00",
        "trend": "10:00",
        "linkedin": "11:30",
        "evening": "17:00",
        "weekly": "fri 18:00",
        "knowledge": "sat 10:00",
        "meta": "1st 11:00",
    }

    # 10. Trends
    config["trends"] = {
        "subreddits": ["artificial", "MachineLearning", "LocalLLaMA", "singularity", "ChatGPT"],
        "hn_limit": 15,
        "reddit_limit": 8,
        "geeknews_limit": 10,
    }

    # Write config.yaml
    import yaml

    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("\n✓ config.yaml created")

    # Write .env
    with open(".env", "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")
    print("✓ .env created")

    # Validate
    print("\n--- Validation ---")
    try:
        from config import Config

        Config()
        print("✓ Config loads successfully")
    except Exception as e:
        print(f"✗ Config error: {e}")

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print(f"\nTest: python3 main.py --test morning")
    print(f"Run:  python3 main.py")
    print(f"Docker: docker-compose up -d")


if __name__ == "__main__":
    main()
