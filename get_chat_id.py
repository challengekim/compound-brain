"""
Telegram chat ID 확인 스크립트.

Usage:
    1. Telegram에서 봇에게 아무 메시지를 보내세요
    2. python get_chat_id.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        token = input("Telegram Bot Token: ").strip()

    resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
    data = resp.json()

    if not data.get("result"):
        print("\nNo messages found.")
        print("Telegram에서 봇에게 먼저 메시지를 보낸 후 다시 실행하세요.")
        return

    chat_ids = set()
    for update in data["result"]:
        chat = update.get("message", {}).get("chat", {})
        if chat.get("id"):
            name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
            chat_ids.add((chat["id"], name))

    print(f"\n{'=' * 40}")
    for cid, name in chat_ids:
        print(f"  Chat ID: {cid}  ({name})")

    if len(chat_ids) == 1:
        cid = list(chat_ids)[0][0]
        print(f"\n.env 파일에 추가하세요:")
        print(f"TELEGRAM_CHAT_ID={cid}")


if __name__ == "__main__":
    main()
