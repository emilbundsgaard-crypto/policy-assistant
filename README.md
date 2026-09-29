# Company Policy Assistant

Answers company policy questions and names the relevant policy. Compares three approaches on the same 98-policy database (`company_policies.csv`):

| Approach | File | How it works |
|---|---|---|
| Rules-based search | `rules_search.py` | BM25 keyword match, no LLM, 0 tokens |
| LLM without vector index | `llm_full.py` | All 98 policies sent to Gemini in every prompt |
| LLM with vector index (RAG) | `llm_rag.py` | Policies embedded with `gemini-embedding-001`; the 3 nearest are sent to Gemini |

Generation model: `gemini-3.1-flash-lite`. On API errors every call retries every 15 s, up to 25 attempts; the waiting time is excluded from the measured response time.

## Files
- `evaluate.py` runs all three approaches on `testset.json` (21 questions, 5 not covered by the database) and writes `results.json`.
- `app.py` + `static/index.html` is the website (FastAPI), deployed on Render via `render.yaml`.
- `slack_bot.py` is the Slack bot (Socket Mode, runs locally, uses the RAG approach). `slack_manifest.yml` creates the Slack app.

## Run locally
```
python3 -m pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY (+ Slack tokens for the bot)
python3 evaluate.py         # creates results.json
python3 -m uvicorn app:app  # http://127.0.0.1:8000
python3 slack_bot.py        # Slack bot
```

## Metrics
- **Correct policy**: named policy equals the expected policy.
- **Unsupported answer**: the approach named a policy that does not support the answer (wrong policy, or answered a question the database does not cover).
- **Missed**: said "no policy" although one exists.
- **Tokens**: input + output (+ thinking) tokens from Gemini's `usage_metadata`. Query-embedding tokens are not included.
