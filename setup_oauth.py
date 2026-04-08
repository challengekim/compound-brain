"""
Google Workspace OAuth2 setup script. Run locally to get refresh tokens.

Usage:
    python setup_oauth.py --account personal
    python setup_oauth.py --account work

Prerequisites:
    1. Go to https://console.cloud.google.com
    2. Create or select a project
    3. Enable "Gmail API" and "Google Calendar API" (APIs & Services > Enable APIs)
    4. Go to "Credentials" > Create Credentials > OAuth client ID
       - Application type: Desktop app
       - Download JSON and save as 'client_secret.json' in this directory
    5. Add your email as a test user in OAuth consent screen

Note:
    After adding calendar.readonly scope, you must re-run this script
    for both accounts to get new refresh tokens with the expanded scope.
"""

import argparse
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def main():
    parser = argparse.ArgumentParser(description="Setup Gmail OAuth2")
    parser.add_argument("--account", choices=["personal", "work"], required=True)
    args = parser.parse_args()

    print(f"\n{'=' * 50}")
    print(f"Gmail OAuth2 Setup - {args.account}")
    print(f"{'=' * 50}\n")

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)

    label = "personal account" if args.account == "personal" else "work account"
    print(f"A browser window will open. Sign in with your {label}.\n")

    creds = flow.run_local_server(port=0)

    env_key = "PERSONAL_GMAIL_REFRESH_TOKEN" if args.account == "personal" else "WORK_GMAIL_REFRESH_TOKEN"

    print(f"\n{'=' * 50}")
    print("Authorization successful!")
    print(f"{'=' * 50}")
    print(f"\n.env 파일에 아래 값을 추가하세요:\n")
    print(f"{env_key}={creds.refresh_token}")
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")

    token_dir = os.path.expanduser("~/.config/productivity-briefing")
    os.makedirs(token_dir, exist_ok=True)
    token_file = os.path.join(token_dir, f"{args.account}_token.json")
    with open(token_file, "w") as f:
        json.dump(
            {
                "refresh_token": creds.refresh_token,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
            },
            f,
            indent=2,
        )
    print(f"\n(백업 저장: {token_file})")


if __name__ == "__main__":
    main()
