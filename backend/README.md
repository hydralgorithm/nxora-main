# Nxora Backend — Smart Shortlisting Engine

Ranks 1 JD against N resumes with a fully local, explainable hybrid engine.
**No LLM anywhere in the scoring path** — embedding models are components of our
own matching logic, per the problem statement's constraint.

## Run

```bash
cd backend
pip install -r requirements.txt          # once
python -m uvicorn main:app --port 8000   # models warm up at startup (~15s)
```

Frontend calls `http://localhost:8000` (CORS open). Swagger docs: `/docs`.

## Endpoints (frozen contract — GAMEPLAN §4)

### `POST /api/analyze` (multipart/form-data)
- `jd_file` (PDF/DOCX/TXT/XML) **or** `jd_text` (string) — exactly one
- `resumes` (files, 1–50): PDF, DOCX, DOC, XML, HTML, TXT

Response: `{jd, ranking[], bias_flags[], meta}`. Per candidate:
`rank, name, file, overall_score, keyword_score, semantic_score, matched_skills,
partial_skills, missing_skills, evidence{sections[], highlight}, explanation`
(top-3 only, `null` below). **Additive optional fields** (safe to ignore):
`band` ("strong"/"medium"/"weak"), `parse_warning`, `skill_evidence`
(skill → best resume line), `requirement_evidence` (per-JD-requirement:
section, similarity, best line — powers the skill-gap heatmap).

Errors: 400/500 `{"detail": "..."}`.

### `POST /api/chat` (JSON)
`{"question": "...", "analysis": <the analysis object currently shown>}` →
`{"answer": "..."}`. Deterministic — answers only from the provided analysis
(compares candidates by rank/name, explains deltas with our own numbers).

## How scoring works

1. **JD decomposition** (`jd_extract.py`): JD → weighted requirements.
   Required skills (weight 3), nice-to-haves (1, section-aware: follows the
   "Nice to have" heading), generic responsibilities (2). Overlap-deduped so
   "REST APIs" is one requirement, not `rest api` + `api`.
2. **Keyword track** (`matcher/keyword.py`): taxonomy regex matching with
   location-aware credit — canonical skill in Experience/Projects = 1.0,
   listed-only = 0.85, synonym-only (e.g. resume says "Express", JD says
   Node.js) = 0.6. Plural-aware, word-boundary safe ("reactive" ≠ react).
3. **Semantic track** (`matcher/semantic.py`): every requirement and every
   resume section embedded in ONE batched pass (`all-MiniLM-L6-v2`); per
   requirement the best-matching section wins; weighted mean → affine
   calibration to 0–100. Then a local cross-encoder
   (`cross-encoder/ettin-reranker-32m-v1`) re-scores each
   (requirement, best-line) pair — a two-stage retrieve+rerank architecture —
   blended 60/40 into the semantic score.
4. **Hybrid** (`matcher/hybrid.py`): `overall = 0.5·keyword + 0.5·semantic`.
5. **Explanations** (`explain.py`): deterministic templates from the engine's
   own evidence — no LLM, fully reproducible.
6. **Bias audit** (`bias.py`): static JD idiom flags (exclusionary/age-coded/
   gendered phrasing) + over-constraint flag (>12 hard requirements) +
   **pool-aware** flags (a required skill almost nobody in the uploaded pool
   demonstrates is called out as screening out the pool).

## Model choice (benchmarked on our task, `bench_models.py` + `bench_results.json`)

| Model | Spearman | AUROC | Spread | Time |
|---|---|---|---|---|
| **all-MiniLM-L6-v2** (chosen) | 0.931 | 1.0 | **0.290** | **3.5s** |
| granite-embedding-small-r2 | 0.931 | 1.0 | 0.093 | 6.7s |
| e5-base-v2 | 0.918 | 1.0 | 0.069 | 23.4s |
| bge-small-en-v1.5 | 0.866 | 1.0 | 0.144 | 6.8s |
| gte-modernbert-base | 0.853 | 1.0 | 0.166 | 238s |
| **ettin-reranker-32m** (chosen reranker) | **0.944** | 1.0 | — | 37s |

MiniLM gave the best tier separation *and* score spread of the bi-encoders at a
fraction of the latency; the cross-encoder adds the highest correlation of all
as a verification stage.

## Env knobs

| Var | Default | Effect |
|---|---|---|
| `NXORA_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | bi-encoder |
| `NXORA_QUERY_PREFIX` / `NXORA_DOC_PREFIX` | `""` | model-specific prefixes (e5: `query: `/`passage: `) |
| `NXORA_RERANKER` | `cross-encoder/ettin-reranker-32m-v1` | reranker model |
| `NXORA_RERANKER_ENABLED` | `1` | `0` disables the rerank stage (faster, slightly less accurate) |

## Performance (18-resume pool, CPU-only)

- Warm server: **~4s** end-to-end including rerank
- Cold start: ~15s model load (happens at server startup, not per request)
- Parser: 220 real files (docx/pdf/txt/xml) — zero warnings, zero failures

## Tests

```bash
python -m pytest tests/ -v   # 12 tests: PS exact case, tier ordering, contract shape, chat
```
