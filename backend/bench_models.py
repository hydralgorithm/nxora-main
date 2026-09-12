"""Benchmark candidate embedding models on OUR task: resume-vs-JD requirement matching.

Ground truth: synthetic dataset tiers (strong=2 > partial=1 > weak=0).
Metric per model: requirement-level semantic score (weighted mean over requirements of
max section cosine), then Spearman correlation vs tiers, tier margins, AUROC
(strong vs weak), score spread, and encode time.

Run:  python bench_models.py          (downloads models on first run; ~1.5GB total)
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# (label, model id, query prefix or None, passage prefix or None)
MODELS = [
    ("all-MiniLM-L6-v2 (baseline)", "sentence-transformers/all-MiniLM-L6-v2", None, None),
    ("bge-small-en-v1.5", "BAAI/bge-small-en-v1.5",
     "Represent this sentence for searching a passage: ", None),
    ("granite-embedding-small-r2", "ibm-granite/granite-embedding-small-english-r2", None, None),
    ("e5-base-v2", "intfloat/e5-base-v2", "query: ", "passage: "),
    ("gte-modernbert-base", "Alibaba-NLP/gte-modernbert-base", None, None),
]
RERANKER = "cross-encoder/ettin-reranker-32m-v1"

# Requirement statements mirroring data/jd.txt (authored by us — synthetic ground truth)
REQUIRED = [  # weight 3
    "Build responsive user interfaces with React, HTML, and CSS",
    "JavaScript (ES6+) programming",
    "Develop backend services using Node.js and Express",
    "Design and query document schemas in MongoDB",
    "REST API development and integration",
    "Git version control and collaborative development",
]
NICE = [  # weight 1
    "Docker containerization",
    "AWS cloud deployment",
    "TypeScript",
    "Writing unit tests with Jest or other testing frameworks",
]
WEIGHTS = [3.0] * len(REQUIRED) + [1.0] * len(NICE)
REQUIREMENTS = REQUIRED + NICE

TIER_VAL = {"strong": 2, "partial": 1, "weak": 0}


def load_corpus():
    with open(os.path.join(DATA, "jd.txt"), encoding="utf-8") as f:
        jd = f.read()
    with open(os.path.join(DATA, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    resumes = []
    for m in manifest:
        with open(os.path.join(DATA, m["file"]), encoding="utf-8") as f:
            resumes.append({**m, "text": f.read()})
    return jd, resumes


def sections_of(text: str) -> list[str]:
    """Cheap stand-in for the real parser: paragraphs + a full-text section."""
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    return paras + [text] if paras else [text]


def ranks(xs: np.ndarray) -> np.ndarray:
    order = np.argsort(xs)
    r = np.empty(len(xs))
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = ranks(a), ranks(b)
    ra -= ra.mean(); rb -= rb.mean()
    denom = np.sqrt((ra @ ra) * (rb @ rb)) + 1e-12
    return float(ra @ rb / denom)


def auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    wins = ties = 0
    for p in pos:
        for n in neg:
            if p > n: wins += 1
            elif p == n: ties += 1
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def score_from_matrix(sim: np.ndarray) -> np.ndarray:
    """sim: (n_resumes, n_requirements) = best section similarity per requirement.
    Weighted mean over requirements -> per-resume score."""
    w = np.array(WEIGHTS)
    return (sim * w).sum(axis=1) / w.sum()


def evaluate(scores: np.ndarray, tiers: np.ndarray, label: str, secs: float) -> dict:
    s, p, w = scores[tiers == 2], scores[tiers == 1], scores[tiers == 0]
    return {
        "model": label,
        "spearman": round(spearman(scores, tiers.astype(float)), 4),
        "auroc_strong_vs_weak": round(auroc(s, w), 4),
        "margin_strong_partial": round(float(s.mean() - p.mean()), 4),
        "margin_partial_weak": round(float(p.mean() - w.mean()), 4),
        "margin_strong_weak": round(float(s.mean() - w.mean()), 4),
        "spread": round(float(scores.max() - scores.min()), 4),
        "seconds": round(secs, 2),
    }


def bench_biencoder(resumes, tiers) -> list[dict]:
    results = []
    for label, model_id, qpre, ppre in MODELS:
        try:
            t0 = time.time()
            model = SentenceTransformer(model_id)
            load_s = time.time() - t0
            req_emb = model.encode(
                [f"{qpre or ''}{r}" for r in REQUIREMENTS], normalize_embeddings=True)
            sim = np.zeros((len(resumes), len(REQUIREMENTS)))
            t0 = time.time()
            for i, r in enumerate(resumes):
                secs = sections_of(r["text"])
                sec_emb = model.encode(
                    [f"{ppre or ''}{s}" for s in secs], normalize_embeddings=True)
                sim[i] = (req_emb @ sec_emb.T).max(axis=1)
            enc_s = time.time() - t0
            scores = score_from_matrix(sim)
            res = evaluate(scores, tiers, label, enc_s)
            res["load_seconds"] = round(load_s, 1)
            results.append(res)
            print(json.dumps(res))
        except Exception as e:
            print(f"FAILED {label}: {type(e).__name__}: {str(e)[:200]}")
    return results


def bench_reranker(resumes, tiers) -> list[dict]:
    """Reranker as an additional semantic scorer: score each (requirement, section) pair,
    per-requirement best section, weighted mean. Logits are monotonic -> rank metrics valid."""
    try:
        t0 = time.time()
        ce = CrossEncoder(RERANKER)
        load_s = time.time() - t0
        sim = np.zeros((len(resumes), len(REQUIREMENTS)))
        t0 = time.time()
        for i, r in enumerate(resumes):
            secs = sections_of(r["text"])
            pairs = [(req, s) for req in REQUIREMENTS for s in secs]
            scores_flat = ce.predict(pairs)
            mat = np.array(scores_flat).reshape(len(REQUIREMENTS), len(secs))
            sim[i] = mat.max(axis=1)
        pred_s = time.time() - t0
        scores = score_from_matrix(sim)
        res = evaluate(scores, tiers, f"RERANKER {RERANKER}", pred_s)
        res["load_seconds"] = round(load_s, 1)
        print(json.dumps(res))
        return [res]
    except Exception as e:
        print(f"FAILED reranker: {type(e).__name__}: {str(e)[:200]}")
        return []


def main() -> None:
    jd, resumes = load_corpus()
    tiers = np.array([TIER_VAL[r["tier"]] for r in resumes])
    results = bench_biencoder(resumes, tiers)
    results += bench_reranker(resumes, tiers)
    out = os.path.join(HERE, "bench_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out}")
    best = max(results, key=lambda r: (r["spearman"], r["auroc_strong_vs_weak"]))
    print(f"BEST: {best['model']} (spearman={best['spearman']}, auroc={best['auroc_strong_vs_weak']})")


if __name__ == "__main__":
    main()
