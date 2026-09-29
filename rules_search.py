"""Metode 1: Regelbaseret søgning (BM25 keyword-match). Ingen AI, 0 tokens."""
import math
import re
import sys
import time
from collections import Counter

from common import NO_POLICY, load_policies

STOPWORDS = set("""a an the is are was were be been do does did can could may might must should
i you we they he she it my our your their what when where who how which why to of in on for
with at by from about as and or not no if any there this that these those have has had
many much get policy policies company employee employees""".split())

MIN_SCORE = 1.0  # under denne score svarer vi "ingen politik fundet"


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w.rstrip("s") if len(w) > 3 else w for w in words if w not in STOPWORDS]


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [tokenize(d) for d in docs]
        self.k1, self.b = k1, b
        self.avgdl = sum(len(d) for d in self.docs) / len(self.docs)
        n = len(self.docs)
        df = Counter(w for d in self.docs for w in set(d))
        self.idf = {w: math.log((n - f + 0.5) / (f + 0.5) + 1) for w, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def scores(self, query):
        q = tokenize(query)
        out = []
        for tf, doc in zip(self.tf, self.docs):
            s = 0.0
            for w in q:
                if w in tf:
                    f = tf[w]
                    s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            out.append(s)
        return out


POLICIES = load_policies()
INDEX = BM25([f"{p['title']} {p['title']} {p['policy_text']}" for p in POLICIES])  # titel vægtes dobbelt


def answer(question):
    start = time.perf_counter()
    scores = INDEX.scores(question)
    best = max(range(len(scores)), key=scores.__getitem__)
    if scores[best] < MIN_SCORE:
        ans, policy = "No matching policy found.", NO_POLICY
    else:
        ans, policy = POLICIES[best]["policy_text"], POLICIES[best]["title"]
    return {
        "method": "rules",
        "question": question,
        "answer": ans,
        "policy": policy,
        "score": round(scores[best], 3),
        "time_ms": round((time.perf_counter() - start) * 1000, 2),
        "tokens": {"input": 0, "output": 0, "thinking": 0, "total": 0},
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How many vacation days do I get?"
    print(answer(q))
