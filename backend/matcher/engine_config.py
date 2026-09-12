"""Engine configuration — THE place where the benchmarked model choice lives.

Swap MODEL_ID (plus prefixes) after bench_models.py picks a winner; nothing else changes.
"""
from __future__ import annotations

import os

# --- Bi-encoder (semantic similarity backbone) --------------------------------
# Placeholder until the benchmark completes; bench_results.json decides the winner.
MODEL_ID = os.environ.get("NXORA_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
QUERY_PREFIX = os.environ.get("NXORA_QUERY_PREFIX", "")   # e.g. "query: " for e5
DOC_PREFIX = os.environ.get("NXORA_DOC_PREFIX", "")       # e.g. "passage: " for e5

# --- Cross-encoder reranker (verification stage, optional) --------------------
RERANKER_ID = os.environ.get("NXORA_RERANKER", "cross-encoder/ettin-reranker-32m-v1")
RERANKER_ENABLED = os.environ.get("NXORA_RERANKER_ENABLED", "1") == "1"
RERANKER_WEIGHT = 0.4   # final semantic = (1-w)*bi_encoder + w*reranker

# --- Calibration (cosine -> 0-100) ---------------------------------------------
# MiniLM-family cosines for (JD requirement, resume section) pairs empirically
# live in ~[0.15, 0.85]; stretch that band to 0-100 so scores spread visibly.
COS_MIN = 0.15
COS_MAX = 0.85

# Reranker sigmoid outputs: ~0.02 irrelevant .. ~0.98 relevant.
RERANK_SIG_MIN = 0.05
RERANK_SIG_MAX = 0.95
