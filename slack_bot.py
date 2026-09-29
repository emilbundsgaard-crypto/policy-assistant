"""Slack-bot: svarer på @mentions og direkte beskeder med LLM + vektorindeks (RAG).
Kører lokalt via Socket Mode (ingen offentlig URL nødvendig).
Kræver i .env: SLACK_BOT_TOKEN (xoxb-...) og SLACK_APP_TOKEN (xapp-...)
Kør: python3 slack_bot.py"""
import os
import re

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from common import BASE_DIR, NO_POLICY
import llm_rag

load_dotenv(BASE_DIR / ".env")
app = App(token=os.environ["SLACK_BOT_TOKEN"])


def build_reply(question):
    r = llm_rag.answer(question)
    if r["policy"] == NO_POLICY:
        policy_line = "*Relevant policy:* none found in the policy database"
    else:
        policy_line = f"*Relevant policy:* {r['policy']}"
    return f"{r['answer']}\n\n{policy_line}"


def handle(text, say, thread_ts):
    question = re.sub(r"<@[A-Z0-9]+>", "", text or "").strip()
    if not question:
        say(text="Ask me a question about company policy, e.g. _How many vacation days do I get?_", thread_ts=thread_ts)
        return
    try:
        say(text=build_reply(question), thread_ts=thread_ts)
    except Exception as e:
        say(text=f"Sorry, something went wrong: {e}", thread_ts=thread_ts)


@app.event("app_mention")
def on_mention(event, say):
    handle(event.get("text"), say, event.get("thread_ts") or event["ts"])


@app.event("message")
def on_dm(event, say):
    # Kun direkte beskeder til botten (ikke almindelige kanalbeskeder)
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        handle(event.get("text"), say, None)


if __name__ == "__main__":
    print("Policy bot kører. Stop med Ctrl+C.")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
