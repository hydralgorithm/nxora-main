# Shortlist — Rank every resume. Show the receipts.

**Team Nexora · InternLoom AI Hackathon · Manipal Institute of Technology**

Shortlist ranks a pool of resumes against one job description with a **hybrid keyword + semantic engine** — and shows the **exact resume line behind every score**. Fully local, fully offline, and **zero LLM calls anywhere in the product**.

> Recruiters don't trust black boxes. We show the receipts.

---

## Why we're different

| What others do | What we do |
|---|---|
| Paste resume + JD into an LLM, ask for a score | **Our own logic.** Models are components inside our matching engine — like a regex. Zero LLM, no API keys, nothing leaves the laptop |
| Embed whole JD + whole resume, one cosine blob | **Requirement-level matching.** The JD is decomposed into weighted requirements (required ×3, responsibilities ×2, nice-to-have ×1); each requirement is matched to the best resume section — how a recruiter actually reads |
| Literal keyword filters (ATS) | **Two independent tracks.** Keyword catches the exact stack; semantic catches *"built REST APIs with Express"* ≈ a Node.js role. They fail differently — each covers the other's blind spot |
| A number, trust it | **Receipts.** Per-requirement evidence heatmap, evidence quote on every matched skill, section-similarity bars, pull-quote from the actual resume |
| Trust whatever model the tutorial used | **Benchmarked, not guessed.** 6 models tested on *our* task (`bench_models.py`); the winner had the best tier separation, 3× the score spread, and 3.5 s latency |
| Audit resumes only | **We audit the JD too** — biased phrasing, over-constrained must-have lists, plus *pool-aware* flags (a required skill nobody in the pool demonstrates) |
| Silent score penalties | **Flag, never penalize.** Keyword-stuffing/repetition get visible flags; the recruiter decides |

---

## Key metrics

| Metric | Value |
|---|---|
| End-to-end analysis (18 resumes, warm, CPU-only) | **~4 s** |
| LLM calls in scoring path | **0** |
| Tests passing | **15/15** (incl. the problem statement's own Express/Node example) |
| Spearman with rerank stage | **0.944** (0.931 bi-encoder only) |
| Score spread, chosen model | **0.290** — 3× the runner-up |
| Parser stress test | **220 real files → 0 failures** |
| Model download size | 82 MB (MiniLM) — runs offline |

---

## Quick start

```bash
# Backend — FastAPI, models warm up at startup (~15 s, once)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000      # Swagger at /docs

# Frontend — Vite dev server
cd frontend
npm install
npm run dev                                 # http://localhost:5173

# Tests
cd backend && python -m pytest tests/ -v    # 15 tests
```

The upload screen ships with a **sample JD pre-filled** (deliberately containing a "rockstar" phrase and a 10-item must-have list so the bias audit lights up), and an **18-resume dataset** lives in `backend/data/` as the offline fallback. The demo is one click: paste-text JD → drop resumes → **Analyze & Rank**.

---

## How scoring works

```
JD + resumes ──► PARSER (pdfplumber → pypdf → content sniff; PDF/DOCX/DOC/XML/HTML/TXT,
                 never crashes — one bad file can't 500 the batch)
        │
        ▼
JD DECOMPOSITION (jd_extract.py) — weighted requirements, same taxonomy as the resume side
        │
   ┌────┴─────────────────────┐
   ▼                          ▼
KEYWORD TRACK              SEMANTIC TRACK
taxonomy regex +           all-MiniLM-L6-v2, one batched encode;
location-aware credit:     per requirement, best resume section wins;
 demonstrated  1.0         cross-encoder (ettin-reranker-32m) re-scores
 listed-only   0.85        each (requirement, best-line) pair —
 synonym       0.6         retrieve-then-rerank, blended 60/40
   └────┬─────────────────────┘
        ▼
HYBRID  overall = 0.5·keyword + 0.5·semantic   (ALPHA = 0.5, the one tuning knob)
        + confidence bands (strong ≥70 · medium ≥45 · weak <45)
        ▼
EXPLAIN (deterministic top-3 templates) · BIAS AUDIT (JD + pool) ·
QUALITY FLAGS (stuffing/repetition) · DEDUPE (by email, best copy wins)
```

**The problem statement's exact case, asserted by test:** a resume saying *"Built REST APIs with Express and MongoDB"* gets **partial credit for Node.js** (Express is a taxonomy synonym) and **full credit for MongoDB** — no LLM involved.

### Model selection — benchmarked on our task

| Model | Spearman ↑ | AUROC | Spread ↑ | Encode time ↓ |
|---|---|---|---|---|
| **all-MiniLM-L6-v2** (chosen) | 0.931 | 1.00 | **0.290** | **3.5 s** |
| granite-embedding-small-r2 | 0.931 | 1.00 | 0.093 | 6.7 s |
| e5-base-v2 | 0.918 | 1.00 | 0.069 | 23.4 s |
| bge-small-en-v1.5 | 0.866 | 1.00 | 0.144 | 6.8 s |
| gte-modernbert-base | 0.853 | 1.00 | 0.166 | 238 s |
| **ettin-reranker-32m** (rerank stage) | **0.944** | 1.00 | — | 37 s |

MiniLM tied for best correlation while producing **3× the score spread** of the runner-up — visible tiers, not everyone clumped at 71 — at a fraction of the latency. Models are swappable via env vars (`NXORA_MODEL`, `NXORA_RERANKER`, see `backend/README.md`).

---

## API (frozen contract)

**`POST /api/analyze`** (multipart) — `jd_file` *or* `jd_text` + 1–50 resumes →

```jsonc
{
  "jd": { "title", "company", "required_skills", "nice_skills" },
  "ranking": [{
    "rank", "name", "file",
    "overall_score", "keyword_score", "semantic_score",   // 0–100
    "matched_skills", "partial_skills", "missing_skills",
    "evidence": { "sections": [{ "name", "similarity" }], "highlight" },
    "explanation",            // top-3 only, null below
    "band",                   // strong | medium | weak
    "skill_evidence",         // skill → best resume line
    "requirement_evidence"    // per JD requirement: section, similarity, line
  }],
  "bias_flags": [{ "phrase", "why", "suggestion" }],
  "meta": { "resumes_processed", "duplicates_removed", "elapsed_ms", "engine" }
}
```

**`POST /api/chat`** — `{ "question", "analysis" }` → `{ "answer" }`. **Deterministic**: it answers only from the provided analysis — score deltas, differing skills, the strongest evidence quote. Same question, same answer, every time (asserted by test). Even the chat doesn't outsource judgment to an LLM.

Errors are always `{ "detail": "..." }` with 400/500; the UI renders them verbatim.

---

## The frontend — three screens

1. **Landing** — the pitch and the promise: two tracks, receipts, no LLM.
2. **Analysis** — JD (PDF or paste) + resume drop zone, live count, elapsed counter while scoring.
3. **Results** — the dashboard: ranked list with **keyword + semantic bars side-by-side** on every row, band chips and filters, duplicate-merge badges, parse-warning icons; clickable **top-3 explanation cards**; the **candidate panel** with the requirement-by-requirement evidence heatmap and pull-quote; the **bias & pool-health panel**; and the floating **recruiter chat**.

Built mock-first: the UI develops against a frozen fixture and flips to live with one env var (`VITE_API_MODE=live`). If the backend dies, demo continues on mock — never debug on stage.

---

## Repository layout

```
├── backend/
│   ├── main.py              FastAPI: /api/analyze, /api/chat, /health
│   ├── parser.py            multi-format, never-crash parsing + sectioning
│   ├── jd_extract.py        JD → weighted requirements (taxonomy-driven)
│   ├── taxonomy.json        55 canonical skills + synonym families
│   ├── matcher/
│   │   ├── keyword.py       location-aware credit scoring
│   │   ├── semantic.py      requirement-level embeddings + rerank stage
│   │   ├── hybrid.py        50/50 blend + confidence bands
│   │   └── engine_config.py model IDs, prefixes, calibration constants
│   ├── explain.py           deterministic top-3 explanation templates
│   ├── bias.py              JD wording audit + pool-coverage flags
│   ├── quality.py           keyword-stuffing / repetition flags
│   ├── bench_models.py      embedding-model benchmark → bench_results.json
│   ├── synth_data.py        18-resume ground-truth corpus (strong/partial/weak)
│   └── tests/test_scoring.py  15 tests
└── frontend/
    └── src/
        ├── lib/api.ts       mock ↔ live switch (only network file)
        ├── lib/types.ts     TS mirror of the frozen contract
        ├── pages/           Landing · Analysis · Results
        └── components/      CandidateDetail · ChatPanel · SkillChips · …
```

---

## Test suite

```
tests/test_scoring.py ................ 15 passed

✓ test_ps_case_express_counts_as_node_partial   ← the PS's exact example, asserted
✓ test_no_false_positives                       ← "reactive" ≠ react
✓ test_listed_only_gets_lower_credit_than_demonstrated
✓ test_parser_survives_garbage                  ← 4 kinds of binary garbage, no crash
✓ test_tier_ordering_on_synth_corpus            ← strong > partial > weak, spread ≥ 15 pts
✓ test_analyze_contract_shape                   ← full response-shape assertion
✓ test_duplicate_resumes_deduped_by_email
✓ test_quality_flags_stuffing_and_repetition
✓ test_chat_deterministic_answers               ← identical question → identical answer
```

The corpus-ordering test runs the **real engine end-to-end** over the 18-resume pool with known ground-truth tiers and asserts correct ordering *and* a meaningful spread.

---

*Built in a hackathon sprint by Team Nexora — every claim on screen traces to a number we computed ourselves.*
