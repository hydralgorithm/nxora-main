# BACKEND.md — Instructions for the Backend/ML AI (Teammate)

> **Read this + GAMEPLAN.md fully before writing any code.**
> You own `backend/` and ONLY `backend/`. The `frontend/` folder is read-only reference.
> Your human: backend/ML teammate. Time budget: ~4 hours. Demo-ready at hour 3.

---

## 0. Session startup checklist (in order)

1. Read `GAMEPLAN.md` — especially §4 (API contract, your bible) and §5 (scoring engine design of record).
2. Read this file fully.
3. Verify environment (should be pre-installed the night before — see GAMEPLAN §2):
   ```bash
   cd backend && pip install -r requirements.txt
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"   # warms the model cache — MUST succeed offline
   uvicorn main:app --reload --port 8000    # http://localhost:8000/docs
   ```
4. If the model download fails and there's no internet, STOP and tell the human immediately — the offline model cache is a hard dependency.

### Skills to invoke, and when
| Skill | When | What for |
|---|---|---|
| `superpowers:test-driven-development` | Only for `tests/test_scoring.py` (0:30–1:45) | Sanity tests: strong-match resume must outscore partial must outscore weak. Nothing more. |
| `ecc:python-review` (skill) or `ecc:python-reviewer` (agent) | Once, after `hybrid.py` produces a ranking (≈1:45) | Catches scoring math, off-by-one, None-handling bugs before they reach the frontend |
| `superpowers:systematic-debugging` | When a real resume parses weird (2:00–2:30 window) | Root-cause the parse, don't patch symptoms |
| `ecc:fastapi-review` | OPTIONAL, only in the 3:00+ window | Polish pass if time allows |

### Skills NOT to use (time sink)
Full TDD coverage, database layers, Docker, auth, async job queues, logging frameworks. 18 resumes is a synchronous in-memory workload — keep it that way.

---

## 1. The mental model

- **The contract is frozen at 0:30** (GAMEPLAN §4). The frontend builds entirely against a mock of it until ~2:30. Your stub at 0:20 must return EXACTLY that shape (use the fixture from GAMEPLAN §4 verbatim — coordinate with the frontend human so `mocks/analyze.json` and your stub are identical).
- **Zero LLM calls in the scoring path.** This is the hackathon's disqualification constraint. Embeddings via sentence-transformers are OUR logic. The ONLY place an LLM may appear is `/api/chat`, and only as a Q&A layer over already-computed results.
- **Every number you return must be traceable.** The frontend will display `keyword_score`, `semantic_score`, `matched/partial/missing_skills`, and the `evidence.highlight` quote side-by-side. Judges will cross-check them against resumes. Never emit a score you can't justify from the code.
- **The frontend also has a static landing page** (marketing only, plus Analysis and Results screens). It needs NOTHING from you — no route, no static serving, no endpoint. Your surface remains exactly `/api/analyze` + `/api/chat`.

---

## 2. File map — what you create, what you never touch

### You own (create/edit freely)
```
backend/
├── main.py               # FastAPI app — routes ONLY. Thin. No business logic here.
├── parser.py             # PDF/text → ResumeData
├── taxonomy.json         # canonical skill → synonyms (seeded, then grown)
├── matcher/
│   ├── __init__.py
│   ├── keyword.py        # taxonomy match → KeywordResult
│   ├── semantic.py       # embeddings + cosine → SemanticResult
│   └── hybrid.py         # ALPHA blend → overall_score, ranking
├── explain.py            # top-3 explanation templates
├── bias.py               # JD bias/narrowness flags
├── synth_data.py         # generates 18 synthetic resumes + 1 JD → data/
├── data/                 # generated synthetic PDFs + JD (fallback dataset)
├── requirements.txt      # fastapi, uvicorn, python-multipart, pdfplumber, pypdf, sentence-transformers
└── tests/
    └── test_scoring.py   # strong > partial > weak ordering sanity
```

### You NEVER touch
- `frontend/**` — entirely Rmais's. If you think it has a bug, tell the humans; don't fix it.
- `GAMEPLAN.md`, `FRONTEND.md` — shared docs; changes need both humans.

---

## 3. Module contracts (internal interfaces — keep these clean so you can extend later)

```python
# parser.py
@dataclass
class ResumeSection: name: str; text: str
@dataclass
class ResumeData:
    name: str                 # best-effort extraction (first non-empty line heuristics fine)
    file: str
    sections: list[ResumeSection]
    full_text: str
def parse_resume(file_bytes: bytes, filename: str) -> ResumeData
# Edge cases: image-scan PDF (little text) → still return ResumeData with whatever text exists, never raise.

# matcher/keyword.py
@dataclass
class KeywordResult:
    score: float              # 0–100
    matched: list[str]; partial: list[str]; missing: list[str]
def keyword_match(resume: ResumeData, required: list[str], nice: list[str], taxonomy: dict) -> KeywordResult

# matcher/semantic.py
@dataclass
class SemanticResult:
    score: float              # 0–100 = 100 · max(section cosines)
    section_scores: list[tuple[str, float]]   # (section name, cosine)
    highlight: str            # resume line whose sentence embedding is closest to the JD
def semantic_match(resume: ResumeData, jd_text: str, model) -> SemanticResult

# matcher/hybrid.py
ALPHA = 0.5   # weight of keyword_score; semantic gets 1-ALPHA. THE ONLY TUNING KNOB.
def blend(keyword: KeywordResult, semantic: SemanticResult) -> float   # overall 0–100

# explain.py
def explain(candidate_result, jd) -> str   # template, deterministic, no LLM

# bias.py
def audit_jd(jd_text: str) -> list[BiasFlag]   # BiasFlag {phrase, why, suggestion}
```

`main.py` orchestrates: parse all → match all → sort by overall desc → assign rank → explain top 3 → audit JD → assemble response dict EXACTLY matching GAMEPLAN §4. Field names verbatim (`overall_score`, not `score` — the frontend's TS types are frozen).

---

## 4. Build order & checkpoints (mirror of GAMEPLAN §6)

| Time | You build | Done means |
|---|---|---|
| 0:00–0:20 | FastAPI scaffold; `POST /api/analyze` stub returning the fixture JSON; CORS for `localhost:5173` | `/docs` shows the endpoint; curl returns fixture |
| 0:20–0:30 | `synth_data.py` — 18 synthetic resumes (6 strong, 6 partial, 6 weak matches) + 1 synthetic JD, written as PDFs into `data/` | PDFs exist; parser has real inputs |
| 0:30–1:45 | `parser.py` → `keyword.py` + `taxonomy.json` (~60 entries) → `semantic.py` → `hybrid.py`; `test_scoring.py` along the way | Full ranking on synthetic data; strong>partial>weak holds |
| 1:45–2:30 | `explain.py`; feed real JD/resumes if available; messy-PDF pass (multi-column, missing sections, image scans) | End-to-end response is contract-exact |
| 2:30–3:00 | `bias.py`; batch the embeddings (one model call for all sections, not per-resume) — get under 10 s for 18 resumes | **FULL DEMO WORKS with frontend live** |
| 3:00–4:00 | `/api/chat` (LLM over precomputed analysis, or naive keyword-lookup fallback); speed/reliability pass; dry-run the demo with the team | Rehearsed |

Commit at every row: `checkpoint-N`.

---

## 5. Implementation notes that save you an hour

### Taxonomy (`taxonomy.json`)
Seed ~60 canonical skills with synonyms. The PS's own example must work: JD says "Node.js backend", resume says "REST APIs with Express and MongoDB" → `express`, `mongodb`, `rest api` are synonyms/children of node.js-stack skills → partial credit + the semantic track carries the rest. TEST THIS EXACT CASE in `test_scoring.py`.

```json
{
  "node.js": ["node", "nodejs", "express", "express.js", "server-side javascript"],
  "mongodb": ["mongo", "nosql database", "document database"],
  "react": ["react.js", "reactjs"],
  "rest api": ["rest", "restful", "api development", "web services"]
}
```
Watch for false-positive substrings ("C" matching inside "JavaScript") — use word-boundary regex.

### Semantic (`semantic.py`)
- Embed JD once. Embed each resume section once. Batch everything into ONE `model.encode()` call across all resumes for speed.
- `highlight`: split section text into lines/sentences, embed them (or approximate by taking the line from the highest-similarity section containing a matched skill — cheaper and still honest).
- Section splitting heuristic: known headers (Summary/Objective/Skills/Experience/Projects/Education) split; if no headers found, fall back to one section = full text.

### Explanations (`explain.py`)
Template exactly as GAMEPLAN §5. Every clause traces to data. No hedging language, no "seems like".

### Bias (`bias.py`)
Three small word lists + one structural check (>8 required skills → narrowness flag). ~30 minutes, high bonus ROI. Ship it even if the list is short — honest small beats fake big.

### Error handling
- `400` with `{"detail": "..."}` when neither jd_file nor jd_text, or zero resumes.
- One bad resume must NEVER 500 the whole batch — catch per-file, return that candidate with `overall_score: 0`, `matched_skills: []`, and (additive field, allowed) `"parse_warning": "low text extracted"`.
- `elapsed_ms` in `meta` — cheap and makes the demo look engineered.

---

## 6. What NOT to do

- ❌ **No LLM in the scoring path** — no OpenAI/Gemini/Anthropic imports in `parser.py`, `matcher/*`, `explain.py`, `bias.py`. If a judge greps, we're clean.
- ❌ No database, no Celery/queues, no Docker, no auth. Synchronous, in-memory, one request at a time is correct for 18 resumes.
- ❌ No contract renames after 0:30 (additive optional fields only — e.g. `parse_warning` above is fine).
- ❌ No `pip install` after 2:30.
- ❌ Don't "improve" the frontend or the shared docs from your side.
- ❌ Don't tune per-candidate or hardcode names to force a nicer ranking — judges cross-check. If ranking looks wrong, tune ALPHA (0.3–0.7) or fix the taxonomy, on synthetic data, once.

---

## 7. Extension points (post-3:00, without breaking anything)

The frontend ignores unknown keys and the contract allows additive optional fields, so all of these are safe to ADD once the core demo is frozen:

| Feature | Where | Contract addition |
|---|---|---|
| Recruiter chat | new `main.py` route → `/api/chat` | already specced (GAMEPLAN §4) |
| Per-skill detail | `keyword.py` return skill→evidence-text map | `candidate.skill_evidence: {skill: line}` (optional) |
| Match-confidence band | `hybrid.py` | `candidate.band: "strong" \| "medium" \| "weak"` (optional — nice UI payoff) |
| Multiple JDs / batch jobs | new endpoint `/api/analyze_batch` | new endpoint, old one untouched |
| JD-side skill extraction improvements | grow `taxonomy.json` + a `jd_extract.py` | none (better `jd.required_skills` quality) |
| Weight tuning UI | read `alpha` from request (default 0.5) | optional request field only — response unchanged |

**The rule that keeps this safe:** every extension is (a) optional field, (b) new endpoint, or (c) internal quality improvement. Anything that would change an existing response field's name, type, or presence requires both humans to approve and both MD files to be updated first.

---

## 8. If the real dataset arrives at the venue

Drop the real `Sample_JD.pdf` + 18 resume PDFs anywhere, upload them through the frontend. Zero code changes expected. If a real resume breaks the parser: `superpowers:systematic-debugging`, fix the heuristic, keep the no-crash rule. The synthetic data stays in `data/` as the fallback demo dataset forever.
