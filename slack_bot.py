"""Lokal Slack-bot via Socket Mode.
Kræver i .env: SLACK_BOT_TOKEN (xoxb-...) og SLACK_APP_TOKEN (xapp-...)
Kør: python3 slack_bot.py"""
import os
import ssl

import certifi
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from common import BASE_DIR
from slack_handlers import register

load_dotenv(BASE_DIR / ".env")

# Mac-fix: Python fra python.org mangler certifikater -> brug certifi's eksplicit
ssl_ctx = ssl.create_default_context(cafile=certifi.where())
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_ctx)

app = App(client=client)
register(app)

if __name__ == "__main__":
    print("Policy bot kører. Stop med Ctrl+C.")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"], web_client=client).start()
