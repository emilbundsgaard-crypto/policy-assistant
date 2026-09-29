"""Webapp til Render: viser sammenligningen og lader brugeren stille et live-spørgsmål.
Lokalt: uvicorn app:app --reload   ->  http://127.0.0.1:8000"""
import json
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import llm_full
import llm_rag
import rules_search
from common import BASE_DIR

app = FastAPI(title="Company Policy Assistant")
RESULTS = BASE_DIR / "results.json"

# Simpel beskyttelse mod misbrug af API-nøglen: maks 10 live-spørgsmål pr. minut pr. IP
_hits = defaultdict(deque)
LIMIT, WINDOW_S = 10, 60


class Ask(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/results")
def results():
    if not RESULTS.exists():
        raise HTTPException(404, "results.json mangler. Kør evaluate.py og commit filen.")
    return JSONResponse(json.loads(RESULTS.read_text()))


@app.post("/api/ask")
def ask(body: Ask, request: Request):
    q = body.question.strip()
    if not q or len(q) > 300:
        raise HTTPException(400, "Question must be 1-300 characters.")

    ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0]
    now, hits = time.time(), _hits[ip]
    while hits and now - hits[0] > WINDOW_S:
        hits.popleft()
    if len(hits) >= LIMIT:
        raise HTTPException(429, "Too many questions. Wait a minute and try again.")
    hits.append(now)

    out = {}
    for name, mod in {"rules": rules_search, "llm_full": llm_full, "llm_rag": llm_rag}.items():
        try:
            out[name] = mod.answer(q)
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


@app.get("/health")
def health():
    return {"ok": True}
