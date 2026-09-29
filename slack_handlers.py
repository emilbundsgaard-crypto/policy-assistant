"""Fælles Slack-logik, bruges både af Render (app.py, HTTP) og lokalt (slack_bot.py, Socket Mode)."""
import re
from collections import deque

import llm_rag
from common import NO_POLICY

_seen = deque(maxlen=500)  # event-id'er vi har svaret på (Slack gensender ved langsom opstart)


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


def _first_time(body):
    eid = body.get("event_id")
    if eid and eid in _seen:
        return False
    if eid:
        _seen.append(eid)
    return True


def register(app):
    @app.event("app_mention")
    def on_mention(body, event, say):
        if _first_time(body):
            handle(event.get("text"), say, event.get("thread_ts") or event["ts"])

    @app.event("message")
    def on_dm(body, event, say):
        # Kun direkte beskeder til botten, ikke almindelige kanalbeskeder
        if event.get("channel_type") == "im" and not event.get("bot_id") and _first_time(body):
            handle(event.get("text"), say, None)
