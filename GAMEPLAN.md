# GAMEPLAN — Smart Shortlisting Engine (InternLoom AI Hackathon)

**Team:** 2 members — Frontend (Rmais) + Backend/ML (teammate)
**Working time:** ~4 hours (assume 3.5 to be safe; be demo-ready at hour 3)
**One-line pitch:** *A transparent, explainable resume ranker that shows recruiters exactly WHY each candidate ranked where they did — hybrid semantic + keyword scoring, visible side-by-side, 100% offline.*

---

## 1. The Problem (condensed)

Rank 15–18 resumes against one Job Description. The output must be:

1. A **ranked list** of all candidates, best-fit first, with meaningful score spread.
2. **Top-3 explanations** — which skills matched, which required skills are missing.
3. Scoring must **genuinely combine semantic matching** (meaning/context — "REST APIs with Express" ≈ Node.js role) **and keyword matching** (explicit skills/tools), both factoring into the result.

**THE HARD CONSTRAINT:** Pasting resume + JD into an LLM API and asking it to rank = disqualified on core criteria. Our own code must do the matching. We comply: **zero LLM calls in the scoring path.**

### Bonus targets (in priority order)
1. **JD bias/narrow-phrasing flags** — startup-friendly, differentiating, cheap to build.
2. **Recruiter Q&A chat** — LLM allowed here ONLY as a natural-language layer over our already-computed scores/evidence (never for ranking).
3. Messy resume formatting — handled by the parser by default.

### Rubric → what we optimize
| Criterion | Weight | Our answer |
|---|---|---|
| Semantic + keyword matching | 35% | Hybrid engine, BOTH scores shown per candidate in UI |
| Ranking quality | 20% | Skill taxonomy with synonym expansion + section-level embeddings |
| Top-3 explanations | 20% | Template-generated from matched/partial/missing + evidence excerpts |
| Working end-to-end demo | 15% | Mock-first frontend, offline everything, rehearsed demo flow |
| Bonus | 10% | Bias flags first, chat second |

### Judges' POV (startup culture, anti-hype)
They want a real problem solved, not a tech demo. Our framing: **"Recruiters don't trust black-box scores. We show the receipts."** Every screen answers "why is this person #1?" Never claim ML we didn't build. The embedding model is a tool we use inside OUR matching logic — say it exactly that way.

---

## 2. Tech Stack (frozen — do not relitigate at the venue)

| Layer | Choice | Why |
|---|---|---|
| Backend | **Python 3.11+ / FastAPI / uvicorn** | Native to sentence-transformers + scikit-learn + pdfplumber; async file upload; auto Swagger docs at `/docs` |
| Semantic engine | **sentence-transformers, model `all-MiniLM-L6-v2`** (82 MB) | Runs fully offline, ~instant on 18 docs, genuinely semantic (384-dim embeddings, cosine similarity) |
| Keyword engine | **Pure Python skill-taxonomy JSON + regex/normalized matching** | Explainable, tunable, no dependency risk |
| PDF parsing | **pdfplumber** (fallback pypdf) | Handles messy multi-column resumes |
| Frontend | **Vite + React + TypeScript + Tailwind CSS** | Fastest scaffold-to-polished-UI path; taste/impeccable skills target this stack |
| Browser QA | Playwright / chrome-devtools MCP (spot checks only) | Verify demo flow visually, no test suites |
| LLM (chat bonus ONLY) | Any API key available, called only by `/api/chat` over precomputed results | Keeps the scoring path LLM-free |

**⏰ BEFORE THE VENUE (do this at home):** `pip install` everything AND run one embedding call so the model is cached locally. Venue Wi-Fi will not download an 82 MB model for you. Same for `npm create vite` + `npm install` — do it on hotel/college Wi-Fi the night before if possible.

---

## 3. Repository Layout & Ownership

```
nexora/
├── GAMEPLAN.md        ← this file (both AIs read this first, every session)
├── FRONTEND.md        ← frontend AI instructions (Rmais's AI ONLY)
├── BACKEND.md         ← backend AI instructions (teammate's AI ONLY)
├── backend/           ← teammate owns 100%. Frontend NEVER edits.
│   ├── main.py            FastAPI app: /api/analyze, /api/chat, static file serving
│   ├── parser.py          PDF/text → structured resume {name, sections, skills_text}
│   ├── taxonomy.json      canonical skills → synonyms/related terms
│   ├── matcher/
│   │   ├── keyword.py     taxonomy matching → keyword_score + matched/partial/missing
│   │   ├── semantic.py    embeddings + cosine → semantic_score + section evidence
│   │   └── hybrid.py      weighted blend → overall_score + final ranking
│   ├── explain.py         top-3 explanation text from computed evidence
│   ├── bias.py            JD bias/narrowness flags
│   ├── synth_data.py      generates 18 synthetic resumes + 1 synthetic JD (fallback)
│   ├── data/              synth_data.py output lands here
│   ├── requirements.txt
│   └── tests/test_scoring.py   # sanity: strong match > weak match
└── frontend/          ← Rmais owns 100%. Backend NEVER edits.
    └── src/
        ├── lib/api.ts         single interface: mock ↔ live switch
        ├── lib/types.ts       TS types mirroring the contract (single source of truth)
        ├── mocks/analyze.json frozen contract fixture
        ├── pages/Landing.tsx  one-screen marketing page → CTA into the app (built LAST)
        ├── pages/Analysis.tsx upload screen (JD + resumes) + processing state
        ├── pages/Results.tsx  the dashboard: ranked list + candidate detail + JD audit
        └── components/        (see FRONTEND.md)
```

**Rule of engagement:** each AI works ONLY inside its folder. The API contract below is the ONLY interface. If a change to the contract is ever needed, BOTH humans approve it in the same room, then both MD files are updated — never silently.

---

## 4. The API Contract (FROZEN at 0:30 — additive changes only after)

Base URL: `http://localhost:8000` (backend serves CORS `*` for `localhost:5173`).

### `POST /api/analyze`
Request (multipart/form-data):
- `jd_file` (PDF, optional) OR `jd_text` (string, optional) — exactly one required
- `resumes` (list of PDF files, 1–50)

Response `200`:
```jsonc
{
  "jd": {
    "title": "Junior Full Stack Developer",
    "company": "TechNova Solutions",
    "required_skills": ["javascript", "react", "node.js", "mongodb"],
    "nice_skills": ["docker", "aws"]
  },
  "ranking": [
    {
      "rank": 1,
      "name": "Ananya Sharma",
      "file": "resume_07.pdf",
      "overall_score": 87.4,          // 0–100, 1 decimal
      "keyword_score": 84.2,          // 0–100
      "semantic_score": 90.6,         // 0–100
      "matched_skills": ["react", "node.js", "rest apis"],
      "partial_skills": ["mongodb"],   // synonym/indirect hits
      "missing_skills": ["docker"],
      "evidence": {
        "sections": [
          { "name": "Projects", "similarity": 0.82 },
          { "name": "Skills", "similarity": 0.74 }
        ],
        "highlight": "Built REST APIs with Express and MongoDB for a food-delivery app"  // best-matching resume line
      },
      "explanation": "Ananya ranks #1 because..."   // top 3 only; null below rank 3
    }
    // ... all candidates, sorted by overall_score desc
  ],
  "bias_flags": [
    { "phrase": "rockstar ninja developer", "why": "exclusionary phrasing",
      "suggestion": "skilled full-stack developer" }
  ],
  "meta": { "resumes_processed": 18, "elapsed_ms": 4210, "engine": "hybrid-v1" }
}
```

Errors: `400` `{ "detail": "..." }` for bad input, `500` same shape. Frontend renders `detail` in a toast.

### `POST /api/chat` (BONUS — build only after hour 3)
Request JSON: `{ "question": "Why is candidate 2 above candidate 3?", "analysis": <the analysis object currently shown> }`
Response: `{ "answer": "..." }`
The endpoint answers ONLY from the provided analysis object. If time is short: a naive keyword lookup over the ranking can substitute for the LLM — still counts as a chat layer.

### Contract change rules (for both AIs)
- ✅ Adding new **optional** fields anywhere.
- ❌ Renaming, removing, retyping, or making any existing field non-optional.
- ❌ Changing status codes or error shape.
- The backend may return extra fields; the frontend ignores unknown keys.

---

## 5. Scoring Engine (design of record)

### Keyword track (`matcher/keyword.py`)
1. Load `taxonomy.json`: `{ "canonical": ["synonym1", "synonym2", ...] }` — seed it with ~60 entries covering the JD domain (js/react/node/express/mongodb/html/css/git/python/java/sql/aws/docker/rest/api/testing/communication…) plus obvious synonyms ("server-side javascript" → node.js; "express.js" → express; "databases" → sql-ish partial).
2. Normalize resume text (lowercase, strip punctuation, collapse whitespace).
3. For each canonical skill: exact/regex hit → **matched**; synonym hit → **matched (partial credit in score, listed under partial_skills)**.
4. Score: `keyword_score = 100 · Σ(weight·credit) / Σ(weight)` where required skill weight = 3, nice-to-have = 1, direct hit credit = 1, synonym hit = 0.6.
5. **Missing-skill penalty is implicit** (no credit), and missing_skills = required ∖ matched — this drives explanations.

### Semantic track (`matcher/semantic.py`)
1. Embed the JD text once.
2. Embed each resume **per section** (Summary, Skills, Experience, Projects, Education — whatever parser extracts).
3. `semantic_score = 100 · max(section cosine similarities)` — max, not mean, so one strongly relevant project surfaces a candidate even when their Skills section is thin (exactly the PS's "Express experience buried in a project" case).
4. Keep per-section similarities as `evidence.sections`; keep the best-scoring source line as `evidence.highlight` (the line whose sentence embedding is closest to the JD).

### Hybrid (`matcher/hybrid.py`)
`overall_score = 0.5·keyword_score + 0.5·semantic_score` — ONE constant `ALPHA` at the top of the file. If ranking quality looks off on synthetic data, tune ALPHA only (0.3–0.7 sane range), never per-candidate.

### Explanations (`explain.py`) — template only, no LLM
Pattern per top-3 candidate:
> "{name} ranks #{rank} with an overall fit of {overall}/100. Strong matches: {matched_skills}; related experience detected: {partial_skills}. Key evidence: “{highlight}”. Gaps: {missing_skills or 'none of the required skills are missing'}."

Deterministic, cheap, and every clause traces to computed data — judges can verify claims against the UI. That is the credibility play.

### Bias flags (`bias.py`) — bonus 1
Small curated lists: exclusionary idioms ("rockstar", "ninja", "young and energetic", "recent grads only"), gendered terms, over-long must-have lists (>8 required skills → "this JD may be too narrow; consider marking some as nice-to-have"). Output = phrase + why + suggestion.

---

## 6. Timeline (wall clock, demo-ready at 3:00)

| Window | Frontend (Rmais) | Backend (teammate) | Checkpoint |
|---|---|---|---|
| 0:00–0:20 | Scaffold Vite+React+TS+Tailwind in the approved design direction (static mocks in `design/`); invoke `design-taste-frontend` for visual direction | Scaffold FastAPI; stub `/api/analyze` returning fixture JSON | Both servers run |
| 0:20–0:30 | **CONTRACT FREEZE** — `types.ts` + mock wired into `api.ts` | Write `parser.py` against `synth_data.py` PDFs | Mock fixture identical on both sides |
| 0:30–1:45 | Upload flow (drag-drop JD + resumes) → ranked list → candidate drawer | `keyword.py` → `semantic.py` → `hybrid.py` + `test_scoring.py` sanity | Backend returns real ranking on synthetic data |
| 1:45–2:30 | Score bars (overall/keyword/semantic), matched/partial/missing chips, top-3 explanation cards | `explain.py`; end-to-end on real-ish data; messy-PDF edge cases | Frontend switches to LIVE api (`VITE_API_MODE=live`) |
| 2:30–3:00 | Integration polish, empty/error/loading states, bias panel UI | `bias.py`; speed pass (embeddings batched) | **FULL DEMO WORKS** |
| 3:00–4:00 | `impeccable` polish pass; **landing page** (one screen — see FRONTEND.md §4); chat panel if backend ships `/api/chat` | `/api/chat`; demo dry-run together; rehearse | Buffer. Nothing after 3:30 is allowed to break what exists |

**The 3:00 rule:** at 3:00, whatever is not merged into the working demo gets cut, not finished. The last 30 minutes are rehearsal + README, never new code.

**If only 3 hours:** cut chat entirely, compress polish to 20 min, keep bias flags (they're ~30 min of backend + a panel you can pre-build against mock).

### Demo script (rehearse this exact flow, 3 minutes)
1. Land on the **landing page** → one sentence of framing ("transparent shortlisting — we show the receipts") → click **"Run an analysis"**.
2. Drag in the real JD + 18 resumes → progress → ranked list appears.
3. Point at #1: both score bars visible → "semantic caught the Express/Node equivalence, keyword caught the explicit stack."
4. Open the drawer: evidence highlight from the actual resume line.
5. Top-3 explanation cards → "generated from our scoring logic, not an LLM."
6. Bias panel → "and the JD itself gets audited."
7. (If chat exists) Ask it "why is #2 above #3?" → answer cites our scores.

---

## 7. Skill & Agent Strategy (both sides have identical skills)

### Frontend AI session
1. **Start:** read GAMEPLAN.md + FRONTEND.md fully.
2. `design-taste-frontend` — once, at scaffold time, to set the visual direction (landing-page skill — apply its taste principles contextually to the product UI).
3. `impeccable:impeccable` — the 3:00+ polish pass, against the taste direction.
4. Playwright / chrome-devtools MCP — spot-check the demo script steps visually. NOT a test suite.
5. `superpowers:systematic-debugging` if integration breaks (mock worked, live doesn't → diff the payloads, don't guess).

### Backend AI session
1. **Start:** read GAMEPLAN.md + BACKEND.md fully.
2. `ecc:python-review` — once, after `hybrid.py` works (catches scoring/index bugs cheaply).
3. `superpowers:test-driven-development` — ONLY for `test_scoring.py` sanity tests (strong>partial>weak ordering). Full TDD wastes hackathon time.
4. `superpowers:systematic-debugging` — when a real resume parses weird.
5. `ecc:fastapi-review` — optional, only if a 30-min window opens post-3:00.

### Both AIs, hard rules
- Work only inside your folder. The other folder is read-only reference.
- Contract changes: never unilateral (see §4 rules).
- No dependency installs after 2:30 (network risk at venue).
- `git commit` at every checkpoint row above — rollback points, named `checkpoint-N`.

---

## 8. Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Venue Wi-Fi dead | Everything offline: model pre-cached, node_modules pre-installed, synthetic data in repo |
| Real resumes are image-scans (no text layer) | Parser detects low text → flag candidate as "unparseable, scored on available text"; don't crash, mention honestly in demo |
| Ranking spread too flat on real data | ALPHA constant is the single tuning knob; tune on synthetic data beforehand, one re-run |
| Frontend blocked on backend | Impossible by design — mock-first. Integration is flipping one env var |
| Feature creep past 3:00 | The 3:00 rule. README + rehearsal > any new feature |
| LLM accusation from judges | Scoring path has zero LLM imports — show the code if asked; chat layer only reads precomputed results |

---

## 9. Definition of Done (hour 3)

- [ ] `POST /api/analyze` returns full ranking for 18 real resumes in < 10 s
- [ ] UI: upload → ranked list → drawer → explanations, all live (mock killed)
- [ ] Top-3 explanations render and are truthful against the drawer data
- [ ] Bias flags panel renders (even if list is empty state)
- [ ] Demo script rehearsed once, end to end, on real data
- [ ] README.md (root): 10 lines — what it is, how to run both servers, the receipts pitch
- [ ] Both folders committed at `checkpoint-final`
