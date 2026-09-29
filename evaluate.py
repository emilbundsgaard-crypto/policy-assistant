"""Kører alle tre metoder på testset.json og gemmer results.json.
Kør: python3 evaluate.py"""
import json
import time
from datetime import datetime, timezone

import llm_full
import llm_rag
import rules_search
from common import BASE_DIR, EMBED_MODEL, GEN_MODEL, NO_POLICY, load_policies

METHODS = {"rules": rules_search, "llm_full": llm_full, "llm_rag": llm_rag}
PAUSE_S = 2  # lille pause mellem API-kald for at skåne rate limits
TITLES = {p["title"].lower() for p in load_policies()}


def norm(x):
    return (x or "").strip().lower()


def grade(result, expected):
    got, exp = norm(result["policy"]), norm(expected)
    answered = got != norm(NO_POLICY)
    return {
        "correct": got == exp,
        # Svar givet uden belæg: svarer selvom databasen ikke dækker det,
        # henviser til forkert politik, eller finder på en politik der ikke findes
        "unsupported": answered and got != exp,
        "invented_policy": answered and got not in TITLES,
        "missed": not answered and exp != norm(NO_POLICY),
    }


def summarize(rows, method):
    rs = [r["results"][method] for r in rows]
    n = len(rs)
    avg = lambda key: sum(key(r) for r in rs) / n
    return {
        "n": n,
        "correct": sum(r["grade"]["correct"] for r in rs),
        "unsupported": sum(r["grade"]["unsupported"] for r in rs),
        "invented_policy": sum(r["grade"]["invented_policy"] for r in rs),
        "missed": sum(r["grade"]["missed"] for r in rs),
        "avg_time_ms": round(avg(lambda r: r["time_ms"]), 2),
        "avg_tokens_input": round(avg(lambda r: r["tokens"]["input"]), 2),
        "avg_tokens_output": round(avg(lambda r: r["tokens"]["output"]), 2),
        "avg_tokens_total": round(avg(lambda r: r["tokens"]["total"]), 2),
    }


def main():
    tests = json.loads((BASE_DIR / "testset.json").read_text())
    rows = []
    for i, t in enumerate(tests, 1):
        row = {"question": t["question"], "expected": t["expected"], "results": {}}
        for name, mod in METHODS.items():
            res = mod.answer(t["question"])
            res["grade"] = grade(res, t["expected"])
            row["results"][name] = res
            if name != "rules":
                time.sleep(PAUSE_S)
        mark = " ".join(f"{n}:{'✓' if row['results'][n]['grade']['correct'] else '✗'}" for n in METHODS)
        print(f"[{i}/{len(tests)}] {t['question'][:55]:55} {mark}", flush=True)
        rows.append(row)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": GEN_MODEL,
        "embed_model": EMBED_MODEL,
        "summary": {m: summarize(rows, m) for m in METHODS},
        "rows": rows,
    }
    (BASE_DIR / "results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("\nGemt i results.json")
    for m, s in out["summary"].items():
        print(f"{m:9} korrekt {s['correct']}/{s['n']}  uden belæg {s['unsupported']}  "
              f"tid {s['avg_time_ms']} ms  tokens {s['avg_tokens_total']}")


if __name__ == "__main__":
    main()
