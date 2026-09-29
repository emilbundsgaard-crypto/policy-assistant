"""Lokal Slack-bot via Socket Mode (alternativ til Render).
Kræver i .env: SLACK_BOT_TOKEN (xoxb-...) og SLACK_APP_TOKEN (xapp-...)
Kør: python3 slack_bot.py"""
import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from common import BASE_DIR
from slack_handlers import register

load_dotenv(BASE_DIR / ".env")
app = App(token=os.environ["SLACK_BOT_TOKEN"])
register(app)

if __name__ == "__main__":
    print("Policy bot kører. Stop med Ctrl+C.")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
