"""Fælles kode for de tre metoder: indlæs politikker, Gemini-klient og prompt."""
import csv
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "company_policies.csv"

# Modelnavne kan ændres i .env uden at røre koden
GEN_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

NO_POLICY = "NONE"

RETRY_WAIT_S = 15   # ventetid mellem forsøg ved fejl
MAX_ATTEMPTS = 25   # maks antal forsøg i alt


def with_retry(fn, stats=None):
    """Kører fn(). Ved fejl: vent 15 sek og prøv igen, op til 25 forsøg i alt.
    stats (dict) får 'attempts' og 'retry_wait_ms', så ventetid kan trækkes fra responstiden."""
    import time
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = fn()
            if stats is not None:
                stats["attempts"] = stats.get("attempts", 0) + attempt
            return result
        except Exception as e:
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"Gemini fejlede {MAX_ATTEMPTS} gange i træk. Sidste fejl: {e}") from e
            print(f"[forsøg {attempt}/{MAX_ATTEMPTS}] fejl: {e} — prøver igen om {RETRY_WAIT_S} sek", flush=True)
            time.sleep(RETRY_WAIT_S)
            if stats is not None:
                stats["retry_wait_ms"] = stats.get("retry_wait_ms", 0) + RETRY_WAIT_S * 1000


def load_policies():
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def policy_to_text(p):
    return f"Title: {p['title']}\nDepartment: {p['department']}\nCategory: {p['category']}\nPolicy: {p['policy_text']}"


def get_client():
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
    except ImportError:
        pass
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY mangler. Indsæt den i .env (se .env.example).")
    from google import genai
    return genai.Client()


SYSTEM_PROMPT = f"""You are a company policy assistant.
Answer ONLY using the policies provided below. Do not use outside knowledge.
If none of the policies answer the question, set "policy" to "{NO_POLICY}" and say that the policy database does not cover it.
Respond as JSON: {{"answer": "<short answer>", "policy": "<exact policy title or {NO_POLICY}>"}}"""


def ask_gemini(client, context, question, stats=None):
    """Sender spørgsmål + kontekst til Gemini og returnerer (answer, policy, tokens)."""
    from google.genai import types

    prompt = f"POLICIES:\n{context}\n\nQUESTION: {question}"
    resp = with_retry(lambda: client.models.generate_content(
        model=GEN_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0,
            response_mime_type="application/json",
        ),
    ), stats)
    try:
        data = json.loads(resp.text)
        answer, policy = data.get("answer", ""), data.get("policy", NO_POLICY)
    except (json.JSONDecodeError, TypeError):
        answer, policy = resp.text, NO_POLICY

    u = resp.usage_metadata
    tokens = {
        "input": u.prompt_token_count or 0,
        "output": u.candidates_token_count or 0,
        "thinking": getattr(u, "thoughts_token_count", 0) or 0,
        "total": u.total_token_count or 0,
    }
    return answer, policy, tokens
