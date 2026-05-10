import requests
import os


class TelegramBot:

    def __init__(self):
        self.token   = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set")

        self.url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send(self, message):
        try:
            resp = requests.post(
                self.url,
                json={
                    "chat_id"    : self.chat_id,
                    "text"       : message,
                    "parse_mode" : "HTML"
                },
                timeout=10
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"Telegram error: {e}")
