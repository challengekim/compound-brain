import logging
import re

import requests

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096
URL_RE = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


class TelegramSender:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def get_updates(self, offset=None):
        """Poll for new messages from Telegram."""
        params = {"timeout": 1, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        try:
            resp = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=5)
            if resp.ok:
                return resp.json().get("result", [])
        except Exception as e:
            logger.debug(f"Telegram poll error: {e}")
        return []

    def send_message(self, text, parse_mode="HTML"):
        chunks = self._split_message(text)
        for chunk in chunks:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
            )
            if not resp.ok:
                logger.error(f"Telegram send failed: {resp.text}")
                return False
        return True

    def _split_message(self, text):
        if len(text) <= MAX_MESSAGE_LENGTH:
            return [text]

        chunks = []
        while text:
            if len(text) <= MAX_MESSAGE_LENGTH:
                chunks.append(text)
                break
            split_idx = text[:MAX_MESSAGE_LENGTH].rfind("\n")
            if split_idx == -1:
                split_idx = MAX_MESSAGE_LENGTH
            chunks.append(text[:split_idx])
            text = text[split_idx:].lstrip("\n")
        return chunks
