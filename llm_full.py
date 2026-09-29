"""Metode 2: LLM uden vektorindeks. Hele CSV'en sendes med i hver prompt."""
import sys
import time

from common import ask_gemini, get_client, load_policies, policy_to_text

POLICIES = load_policies()
FULL_CONTEXT = "\n\n".join(policy_to_text(p) for p in POLICIES)
_client = None


def answer(question):
    global _client
    _client = _client or get_client()
    start = time.perf_counter()
    stats = {}
    ans, policy, tokens = ask_gemini(_client, FULL_CONTEXT, question, stats)
    elapsed = (time.perf_counter() - start) * 1000 - stats.get("retry_wait_ms", 0)
    return {
        "method": "llm_full",
        "question": question,
        "answer": ans,
        "policy": policy,
        "time_ms": round(elapsed, 2),  # ekskl. 15-sek ventetid ved retries
        "attempts": stats.get("attempts", 1),
        "tokens": tokens,
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How many vacation days do I get?"
    print(answer(q))
