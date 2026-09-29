"""Metode 3: LLM med vektorindeks (RAG).
Politikkerne embeddes én gang og gemmes i embeddings.json.
Ved hvert spørgsmål embeddes spørgsmålet, de TOP_K nærmeste politikker findes,
og kun de sendes til Gemini."""
import json
import math
import sys
import time

from common import (BASE_DIR, EMBED_MODEL, ask_gemini, get_client,
                    load_policies, policy_to_text, with_retry)

TOP_K = 3
INDEX_PATH = BASE_DIR / "embeddings.json"
POLICIES = load_policies()
_client = None
_index = None


def _embed(client, texts, task_type, stats=None):
    from google.genai import types
    vectors = []
    for i in range(0, len(texts), 50):  # i portioner for at undgå for store kald
        batch = texts[i:i + 50]
        resp = with_retry(lambda: client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task_type),
        ), stats)
        vectors.extend(e.values for e in resp.embeddings)
    if len(vectors) != len(texts):
        raise RuntimeError(f"Fik {len(vectors)} embeddings for {len(texts)} tekster.")
    return vectors


def build_index(client):
    texts = [policy_to_text(p) for p in POLICIES]
    vectors = _embed(client, texts, "RETRIEVAL_DOCUMENT")
    INDEX_PATH.write_text(json.dumps({"model": EMBED_MODEL, "vectors": vectors}))
    return vectors


def load_index(client):
    if INDEX_PATH.exists():
        data = json.loads(INDEX_PATH.read_text())
        if data.get("model") == EMBED_MODEL and len(data["vectors"]) == len(POLICIES):
            return data["vectors"]
    return build_index(client)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def answer(question):
    global _client, _index
    _client = _client or get_client()
    _index = _index or load_index(_client)

    start = time.perf_counter()
    stats = {}
    qvec = _embed(_client, [question], "RETRIEVAL_QUERY", stats)[0]
    ranked = sorted(range(len(POLICIES)), key=lambda i: _cosine(qvec, _index[i]), reverse=True)[:TOP_K]
    context = "\n\n".join(policy_to_text(POLICIES[i]) for i in ranked)
    ans, policy, tokens = ask_gemini(_client, context, question, stats)
    elapsed = (time.perf_counter() - start) * 1000 - stats.get("retry_wait_ms", 0)
    return {
        "method": "llm_rag",
        "question": question,
        "answer": ans,
        "policy": policy,
        "retrieved": [POLICIES[i]["title"] for i in ranked],
        "time_ms": round(elapsed, 2),  # ekskl. 15-sek ventetid ved retries
        "api_calls": stats.get("attempts", 2),  # 1 embedding + 1 generation uden fejl
        "tokens": tokens,  # generation-tokens; embedding af spørgsmålet er ikke talt med
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How many vacation days do I get?"
    print(answer(q))
