# FRONTEND SPEC — Nxora Smart Shortlisting Engine (for Rmais + AI assistant)

Backend is **complete, tested, and running** at `http://localhost:8000` (FastAPI, CORS `allow_origins=["*"]`, all methods/headers — call it directly from any origin, no proxy needed for dev). Swagger docs live at `http://localhost:8000/docs` if you want to verify anything live.

Repo state: there is **no frontend yet** — no `frontend/` dir, no `package.json`, no framework chosen. You own that decision and that directory. Recommended for a same-day demo: **Vite + React + TypeScript** (fast dev server, trivial deploy), but any framework works as long as it lives under `frontend/` (see §6).

---

## 1. Overview & backend capabilities (what the engine does)

Nxora ranks N resumes (1–50) against one job description and returns a fully explainable ranking. **No LLM anywhere in the scoring path** — this is a hackathon judging criterion, worth mentioning in the UI copy.

Pipeline, in plain language:

1. **JD decomposition** — the JD text/file is parsed into weighted requirements: required skills (weight 3), nice-to-haves (weight 1), responsibilities (weight 2). Returned to you in `jd.required_skills` / `jd.nice_skills`.
2. **Keyword track** — taxonomy regex matching with location-aware credit: canonical skill found in Experience/Projects = 1.0; listed-only in a Skills section = 0.85; synonym-only (resume says "Express", JD says "Node.js") = 0.6; no hit = 0. Produces `keyword_score` (0–100) and the `matched_skills` / `partial_skills` / `missing_skills` lists, plus `skill_evidence` (which resume line each skill was found on).
3. **Semantic track** — every JD requirement and every resume section embedded in one batched pass (bi-encoder `all-MiniLM-L6-v2`), then a local cross-encoder (`ettin-reranker-32m-v1`) re-scores the best (requirement, line) pairs, blended 60/40. Produces `semantic_score` (0–100) plus per-requirement evidence (`requirement_evidence`).
4. **Hybrid blend** — `overall_score = 0.5·keyword + 0.5·semantic` (0–100, one decimal).
5. **Bands** — every candidate gets `band`: `"strong"` (≥70), `"medium"` (≥45), `"weak"` (<45). Use for row coloring / badges.
6. **Top-3 explanations** — ranks 1–3 get a deterministic `explanation` string (matched skills, gaps, key evidence quote). Ranks 4+ have `explanation: null`. Render verbatim.
7. **Bias audit** — two layers, both returned in `bias_flags[]`: (a) static JD-idiom flags (bro-culture jargon, age-coded, gendered, exclusionary phrasing, >12 hard requirements = over-constrained) and (b) **pool-aware** flags — a required skill that <15% of the uploaded pool demonstrates is flagged as "screens out the pool". Each flag has `phrase`, `why`, `suggestion` (a concrete rewrite).
8. **Dedupe reporting** — same person submitted in multiple formats/versions (matched by email) is merged, keeping the best-parsed copy. `meta.duplicates_removed` and `meta.duplicates[]` tell you who was merged into whom.
9. **Parse warnings** — one unreadable resume never kills the batch; it appears in the ranking with `parse_warning` set (and typically a near-zero score). Surface the warning in the UI.
10. **Deterministic chat** — `POST /api/chat` answers recruiter questions about the current analysis using only the analysis object the UI sends back. No LLM, no server state: it locates candidates by rank number or name and explains the delta with the engine's own numbers.

Timing (CPU-only, from backend benchmarks): warm server, ~2s for 2 resumes, ~4s for an 18-resume pool, budget **5–8s for 15–50 resumes**. First call after server start can add up to ~20s while models load into memory — the server warms models in a background thread at startup, so if the server has been up for ~20s you won't see this.

---

## 2. Exact API contract

Field names below are **verbatim** from `backend/main.py`. All scores are JSON numbers (float, 0–100, one decimal). All skill lists are arrays of strings.

### `GET /health`

```json
{ "status": "ok", "engine": "hybrid-v2-requirements" }
```

Use at app boot to show "Backend: online/offline" (poll every ~10s; the backend takes ~15–20s to start).

### `POST /api/analyze` — multipart/form-data

Form fields:

| Field | Type | Rules |
|---|---|---|
| `jd_file` | file (PDF/DOCX/TXT/XML) | OR `jd_text` — exactly one, else 400 |
| `jd_text` | string | OR `jd_file`. Empty/whitespace string counts as absent |
| `resumes` | files (repeat the field per file) | 1–50 files. PDF, DOCX, DOC, XML, HTML, TXT. If >50, 400 |

Send as standard multipart: `FormData`, append `resumes` once per file (or `resumes[]` per file — both work with FastAPI). Do NOT set a manual `Content-Type` header; let the browser set the multipart boundary.

**Response 200** — top level:

```json
{
  "jd": {
    "title": "string | null",
    "company": "string | null",
    "required_skills": ["python", "react"],
    "nice_skills": ["kubernetes"]
  },
  "ranking": [ /* per-candidate objects, best first */ ],
  "bias_flags": [ /* may be empty */ ],
  "meta": {
    "resumes_processed": 18,
    "duplicates_removed": 1,
    "duplicates": [
      { "name": "Jane Doe", "file": "jane_v1.pdf", "kept_file": "jane_v2.docx", "email": "jane@x.com" }
    ],
    "elapsed_ms": 4231,
    "engine": "hybrid-v2-requirements"
  }
}
```

**Per-candidate object** (`ranking[i]`) — core fields:

| Field | Type | Meaning |
|---|---|---|
| `rank` | int | 1-based, sorted by score desc |
| `name` | string | extracted candidate name |
| `file` | string | uploaded filename |
| `overall_score` | number | 0–100 hybrid |
| `keyword_score` | number | 0–100 taxonomy track |
| `semantic_score` | number | 0–100 embedding+rerank track |
| `matched_skills` | string[] | canonical hits (demonstrated or listed) |
| `partial_skills` | string[] | synonym-only hits |
| `missing_skills` | string[] | required skills with no hit |
| `evidence` | object | `{ "sections": [{ "name": "Experience", "similarity": 0.71 }, ...], "highlight": "best resume line overall" }` |
| `explanation` | string \| null | deterministic explanation, **ranks 1–3 only, `null` below** — render it, don't regenerate |

Additive optional fields (always present in v2; safe to feature-detect but no need to):

| Field | Type | Meaning |
|---|---|---|
| `band` | string | `"strong"` (≥70) / `"medium"` (≥45) / `"weak"` (<45) |
| `parse_warning` | string \| null | non-null when the file was partially/fully unreadable — show a warning chip on the row |
| `skill_evidence` | object | map `{ skill → best resume line where it was found }` (e.g. `{"python": "Built ETL pipelines in Python and Airflow at Acme"}`) |
| `requirement_evidence` | array | one object per JD requirement: `{ "requirement": "JD statement", "skill": "python" | null, "kind": "required" | "nice" | "responsibility", "section": "Experience", "similarity": 0.71, "line": "best matching resume line" }`. `similarity` is raw cosine 0–1 (not calibrated). Powers the per-requirement heatmap / detail view |

**bias_flags[i]** (array may be empty):

```json
{
  "phrase": "rockstar ninja",
  "why": "Bro-culture jargon — discourages qualified applicants who read it as 'not for me'.",
  "suggestion": "Replace with the concrete skill or responsibility you actually need."
}
```

Pool-aware flags look like: `"phrase": "Required skill 'kubernetes' — only 1/18 candidates show it"` with `why`/`suggestion` about demoting it to nice-to-have.

**Errors** (FastAPI style: status + `{"detail": "human-readable string"}`):

| Status | Trigger |
|---|---|
| 400 | Both or neither of `jd_file`/`jd_text`; zero resumes; >50 resumes; JD file unreadable; JD text yields no requirements ("Could not extract any requirements from the JD. Is it a job description?") |
| 500 | `"Semantic engine failed to load: ..."` — model unavailable (offline without cache) |
| 422 | Malformed multipart (missing `resumes` field entirely) — treat like 400 |

### `POST /api/chat` — JSON

Request: `{"question": string, "analysis": <the exact analysis object you received from /api/analyze and are currently displaying>}`. The backend is stateless — you MUST send the analysis back with every question; keep the latest analysis in app state.

Response: `{"answer": "string"}` — always 200, never errors. Behaviors:

- **Two candidates identified** (comparison) — e.g. *"why is candidate 1 above candidate 2?"* → explains the score delta, keyword vs semantic breakdown, skills one has that the other doesn't, and quotes the strongest evidence line.
- **One candidate identified** — e.g. *"tell me about Sarah"*, *"candidate 3"* → rank, scores, matched, missing, band.
- **No candidate identified** — summarizes the top-3 podium and hints at how to ask.
- **Empty question or empty ranking** (e.g. asked before any analysis) → `"Upload a JD and resumes first, then ask me about the candidates."`

Candidate resolution rules (mirror these in your UI hints): patterns `candidate 2`, `rank 3`, `ranked 4`, `#1`, `number 2` all resolve to rank numbers; any distinctive word (>2 chars, case-insensitive) of a candidate's `name` found in the question resolves by name. First two distinct mentions win.

Good demo questions: `why is candidate 1 above candidate 2?`, `what is Sarah missing?`, `candidate 3`, `top candidates`.

---

## 3. Ideal page structure

Five surfaces; (a)–(c) are the demo spine, (d) and (e) are the wow-factor panels. Keep the whole latest `/api/analyze` response in a single client-side store (React context / Zustand / whatever) — the chat panel and detail drawer both consume it.

### (a) Upload / JD input — route `/`

- **Data consumed:** none (produces the analysis via `POST /api/analyze`).
- **UI elements:** a JD tab-switcher — "Paste JD text" (textarea → `jd_text`) OR "Upload JD file" (file input, PDF/DOCX/TXT/XML → `jd_file`); a resume dropzone with multi-select (accept `.pdf,.docx,.doc,.xml,.html,.txt`, hard-cap client-side at 50 with a visible count "23 / 50 files"); a chip list of selected filenames with remove buttons; a big "Analyze & Rank" CTA, disabled until a JD source AND ≥1 resume exist.
- **States:** loading — full-screen progress with elapsed timer and copy like "Embedding and re-ranking 23 resumes…" (request takes 2–8s; see §5); error — show `detail` from the 400/500 verbatim in a dismissible banner and keep the form state so the user can fix it; empty — pre-fill the JD textarea with a sensible sample JD so a judge can demo in one paste.
- On success, store the response and navigate to `/results`.

### (b) Results / ranking table — route `/results`

- **Data consumed:** full analysis — `ranking[]`, `jd`, `meta`, `bias_flags[]`.
- **UI elements:** header with `jd.title` (fallback "Job Description"), `meta.resumes_processed`, `meta.duplicates_removed` (if >0, a small "1 duplicate merged" chip with a tooltip/hover listing `meta.duplicates`), `meta.elapsed_ms` as "ranked in 4.2s" (nice proof of speed), and the engine badge `meta.engine`.
- Table rows: `rank` (with medal styling for 1–3), `name` (+ `file` as secondary text), `overall_score` (bold, with a bar or donut), `band` badge (strong=green / medium=amber / weak=gray), `keyword_score`, `semantic_score`, matched/missing counts (e.g. "8 matched · 2 missing") — expandable or shown fully in the drawer. Click row → drawer (c).
- **Top-3 explanations:** render `explanation` verbatim in a highlighted card above or inline with the top three rows — this is 20% of the rubric, make it visually prominent, not buried.
- **States:** loading (navigating here happens only after the response, so minimal); empty (navigated directly without an analysis → redirect to `/`); parse-warning rows get a small amber warning icon with `parse_warning` in a tooltip.
- Sorting/filtering is optional; the API order is final. A band filter (all/strong/medium/weak) is cheap and demo-friendly.

### (c) Candidate detail drawer (recommended over a separate page — keeps judges on the results screen)

- **Data consumed:** one `ranking[i]` object, plus `jd.required_skills` for cross-reference.
- **UI elements:** header with `name`, `rank`, `overall_score`, `band`; score breakdown (keyword vs semantic as two bars); three skill columns — `matched_skills` (green, each with its `skill_evidence[skill]` line as a quote beneath it), `partial_skills` (amber), `missing_skills` (red); `evidence.sections` as a small bar list (section name + similarity); `evidence.highlight` as a quote card; `requirement_evidence` as the centerpiece — a per-JD-requirement list showing each `requirement`, the best matching `line` from the resume, the `section` it came from, and `similarity` (0–1, render as a mini progress bar); `explanation` if non-null.
- **States:** this is pure client-side rendering of stored data — no loading state needed; empty-state guards for absent `skill_evidence` / empty `requirement_evidence` (unreadable resumes).

### (d) Bias & pool health panel — a collapsible section or tab on `/results`

- **Data consumed:** `bias_flags[]`, `jd.required_skills`, `meta`.
- **UI elements:** if `bias_flags` is empty, show a green "No bias signals detected in this JD or pool" (don't hide the panel — the clean result is itself a feature). Otherwise one card per flag: the `phrase` in quotes (with the type: JD wording vs pool coverage), `why`, and `suggestion` styled as an actionable rewrite. Pool-aware flags ("only 1/18 candidates show kubernetes") are the differentiator — label them distinctly, e.g. a "Pool health" tag vs "JD wording" tag.

### (e) Recruiter chat panel — fixed bottom-right or right rail on `/results`

- **Data consumed:** `POST /api/chat` — sends `{"question", "analysis": <stored analysis>}`; message list kept client-side.
- **UI elements:** input + send, message bubbles (user right / assistant left), suggested-question chips pre-filled with: *"Why is candidate 1 above candidate 2?"*, *"What is candidate 3 missing?"*, *"Tell me about {top candidate name}"* — these guarantee good demo output.
- **States:** typing indicator while the (fast, local) request is in flight; if the answer is the "Upload a JD and resumes first" string, render it as a hint not an error.

### Demo flow (what judges see at 4:30PM)

1. `/` — paste a JD, drop ~15 resumes, click Analyze (loading state with timer).
2. `/results` — ranked table appears with scores, bands, "ranked in 4.2s", 1 duplicate merged.
3. Top-3 explanation cards read out — engine explains itself in plain English.
4. Click rank 1 → drawer: matched skills with evidence lines, per-requirement heatmap with resume quotes.
5. Bias panel: pool-health flag calls out an over-constraining requirement.
6. Chat: "Why is candidate 1 above candidate 2?" → deterministic delta explanation with evidence quote.

---

## 4. Routing

- `/` — upload/JD input. On successful analysis → navigate to `/results` (store the analysis in memory; a page refresh loses it — acceptable for the demo; alternatively persist the last analysis to `sessionStorage` and hydrate on `/results` mount, which is ~10 lines and makes refresh-safe demos possible).
- `/results` — ranking table + top-3 explanations + bias panel + chat panel; candidate detail is a drawer/overlay on this route (no navigation, keeps the table in context). If you prefer a page instead: `/results/:rank` where `:rank` matches `ranking[i].rank` — but the drawer is recommended.
- Anything else → redirect to `/`.
- Both routes need an "New analysis" / back button → `/` (keep or clear prior form state; keeping it is friendlier).

---

## 5. Error handling requirements

**HTTP errors from `/api/analyze`** — all error bodies are `{"detail": "..."}` with a human-readable message; render `detail` verbatim, do not map to generic messages:

- 400 "Provide exactly one of 'jd_file' or 'jd_text'." — user sent both/either nothing.
- 400 "Provide at least one resume file."
- 400 "Too many resumes (N); max is 50." — also enforce client-side (count badge, block the CTA at 51).
- 400 "Could not read the JD file: …" / "Could not extract any requirements from the JD. Is it a job description?" — most common real-world 400: user pasted a non-JD. Show inline near the JD input and keep everything entered.
- 500 "Semantic engine failed to load: …" — backend model problem; show "Backend model unavailable — restart the backend server" plus the detail.
- 422 — malformed multipart; treat as 400.

**`/api/chat`** never returns an error status; handle only network failure with a retry affordance.

**Per-candidate `parse_warning`** — non-null string on rows whose file was partially/fully unreadable. Amber warning icon on the row; full text in the drawer. These candidates still rank (usually at the bottom) — the warning explains why.

**Network / timeouts:** set the client fetch timeout to **60s** (first-call-after-startup model load can push a request to ~20s+; warm requests are 2–8s). If `/health` fails at app boot, show a persistent "Backend offline — start it with `cd backend && python -m uvicorn main:app --port 8000`" banner. Retry on network error with a manual "Try again" button, never auto-loop.

**Loading state for `/api/analyze` is mandatory:** show elapsed seconds counting up ("Analyzing… 3.2s") plus a note for long waits ("first run loads AI models, up to 20s"). Disable the CTA and the file inputs during flight. Never fire two analyzes concurrently — the backend serializes model inference behind a lock, so a second call just queues.

---

## 6. DO NOT TOUCH rules (merge-conflict avoidance)

Two teams, one repo, same afternoon. Hard boundaries:

**Backend owns, frontend must never create, edit, or delete:**
- `backend/**` — every `.py` file (`main.py`, `parser.py`, `jd_extract.py`, `explain.py`, `bias.py`, `synth_data.py`, `bench_models.py`), `backend/matcher/**`, `backend/taxonomy.json`, `backend/tests/**`, `backend/scripts/**`, `backend/data/**`, `backend/requirements.txt`, `backend/README.md`, `backend/bench_results.json`
- Root: `BACKEND.md`, `GAMEPLAN.md`, `AGENTS.md`, `GEMINI.md`, `research_tmp/`, `PS/`

**Frontend owns (create freely, backend will never touch):**
- `frontend/**` — the entire directory: source, `package.json`, lockfile, configs, components, `frontend/README.md` if wanted. This is yours alone, including `frontend/.gitignore` if desired.

**Shared root files:**
- `FRONTEND_SPEC.md` (this file) — written by the backend side; frontend may append a "Status / decisions" section at the bottom but must not rewrite the contract sections.
- `.gitignore` — already covers standard entries (node_modules is ignored; verify after scaffolding and, if `node_modules/` isn't covered, add it under a clearly-commented `# Frontend` block — additive edits only, never delete backend entries).

**Branches:** the backend work lives on branch `worktree-backend-build` (this worktree). The frontend dev must **branch off `main`** (from the main checkout at `C:\Users\Abdul Fattah\Desktop\nxora-main`) and work on their own branch (e.g. `frontend-build`). Never commit to `worktree-backend-build`; never push to `main` directly.

**API base URL:** hardcode `http://localhost:8000` for the demo; put it in a single constant / env var (`VITE_API_BASE` or equivalent) so it's one-line changeable.

---

## 7. Demo checklist — must work at 4:30PM

- [ ] Paste JD text (and, if time allows, upload a JD PDF) + multi-select ~15 resumes → Analyze → ranked table renders within ~8s with a loading state.
- [ ] Table shows: rank, name, overall_score, band badge, keyword/semantic scores, matched/missing counts.
- [ ] Top-3 `explanation` strings displayed prominently and verbatim.
- [ ] Candidate detail (drawer) shows: `skill_evidence` lines under matched skills, `requirement_evidence` (requirement → best resume line + similarity), `evidence.highlight` quote.
- [ ] Bias panel renders flags (or the clean "no signals" state); pool-coverage flag visually distinguished from JD-wording flags.
- [ ] Chat answers "why is candidate 1 above candidate 2?" with the deterministic delta explanation, including the evidence quote.
- [ ] Duplicate-merge chip (`meta.duplicates_removed` > 0) and parse-warning icon both render when present.
- [ ] Error path sanity: paste a non-JD text → the 400 detail shows inline without losing form state.
- [ ] `/health` polled; offline banner if backend is down.
- [ ] Full flow survives a page refresh on `/results` (sessionStorage hydration) — or the team knows to demo without refreshing.

Pre-demo: start the backend ~30s early so model warm-up is done before judges watch the clock.
