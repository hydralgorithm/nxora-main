# FRONTEND.md — Instructions for Rmais's AI (Frontend)

> **Read this + GAMEPLAN.md fully before writing any code.**
> You own `frontend/` and ONLY `frontend/`. The `backend/` folder is read-only reference.
> Your human: Rmais. Time budget: ~4 hours. Demo-ready at hour 3.

---

## 0. Session startup checklist (in order)

1. Read `GAMEPLAN.md` (especially §4 API Contract — your bible).
2. Read this file fully.
3. Invoke the **`design-taste-frontend`** skill once to establish the visual direction BEFORE scaffolding components. (Installed from `Leonxlnx/taste-skill`. Note: it targets landing pages/portfolios — its rules are contextual, so apply its taste principles — typography, color, anti-slop discipline — to this product UI; don't force landing-page patterns onto a ranked list.)
4. Scaffold: `npm create vite@latest frontend -- --template react-ts`, then Tailwind.
5. Build mock-first (below). Never wait on the backend for anything.

### Skills to invoke, and when
| Skill | When | What for |
|---|---|---|
| `design-taste-frontend` | Once, at scaffold time (0:00–0:20) | Visual direction — colors, typography, layout voice. Landing-page-oriented skill: use its taste principles, adapted to a product/data UI |
| `impeccable:impeccable` | 3:00+ polish window only | Final quality pass against the taste direction |
| Playwright / chrome-devtools MCP | After each major UI milestone (3 spot checks max) | Visually verify: upload → list → drawer. NOT a test suite |
| `superpowers:systematic-debugging` | Only if live integration breaks | Diff mock vs live payload first, then bisect — never guess |
| `ecc:react-build` (agent) | Only if the build breaks and you're stuck >10 min | Fast unblock |

### Skills NOT to use (time sink)
Test suites, TDD, a11y audits, Lighthouse, component libraries beyond what's scaffolded, Storybook. A hackathon frontend needs to look excellent and demo flawlessly — not be maintainable for five years.

---

## 1. The mental model (why mock-first matters)

The backend teammate is building the scoring engine in parallel. You will receive the REAL API at ~2:30. Until then — and as a permanent fallback — every screen runs off `mocks/analyze.json`, which is a **frozen fixture of the exact contract in GAMEPLAN.md §4**.

- Backend can never block you.
- If the backend dies at the venue, flip `VITE_API_MODE=mock` and demo still works on realistic data. This is your safety net — protect it.

---

## 2. File map — what you create, what you never touch

### You own (create/edit freely)
```
frontend/
├── index.html
├── vite.config.ts           # add proxy: '/api' → http://localhost:8000 (CORS safety)
├── .env                     # VITE_API_MODE=mock | live ; VITE_API_URL=http://localhost:8000
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx              # routing: Landing → Analysis → Results (3 screens max; chat is a panel on Results, not a page)
    ├── lib/
    │   ├── types.ts         # TS interfaces mirroring GAMEPLAN §4 — SINGLE source of truth
    │   └── api.ts           # the ONLY file that talks to the network. mock/live switch here
    ├── mocks/
    │   └── analyze.json     # frozen contract fixture (realistic: 18 candidates, spread scores)
    ├── pages/
    │   ├── Landing.tsx      # one-screen marketing page → CTA "Run an analysis" (built LAST)
    │   ├── Analysis.tsx     # upload screen (JD + resumes) + processing state
    │   └── Results.tsx      # the dashboard: ranked list + candidate detail + JD audit
    └── components/
        ├── UploadZone.tsx       # drag-drop: 1 JD (pdf/text) + N resumes
        ├── ProcessingState.tsx  # progress / elapsed / count
        ├── RankingTable.tsx     # the hero: ranked list
        ├── CandidateRow.tsx     # rank, name, scores, chips
        ├── ScoreBars.tsx        # overall + keyword + semantic bars (ALWAYS together)
        ├── SkillChips.tsx       # matched (green) / partial (amber) / missing (red)
        ├── CandidateDrawer.tsx  # detail: evidence, section similarities, highlight quote
        ├── ExplanationCard.tsx  # top-3 explanation cards
        ├── BiasPanel.tsx        # JD bias flags
        ├── EmptyState.tsx / ErrorToast.tsx
        └── ChatPanel.tsx        # BONUS — build ONLY in the 3:00+ window, mock-driven
```

### You NEVER touch
- `backend/**` — entirely your teammate's. If you think it has a bug, tell the human, don't fix it.
- `GAMEPLAN.md`, `BACKEND.md` — shared docs; changes need both humans.
- `frontend/src/lib/types.ts` field names after contract freeze (0:30) — additive optional fields only, per GAMEPLAN §4 rules.

---

## 3. The two files that make integration painless

### `lib/types.ts` — mirror the contract exactly
```ts
export interface BiasFlag { phrase: string; why: string; suggestion: string }
export interface SectionEvidence { name: string; similarity: number }
export interface Evidence { sections: SectionEvidence[]; highlight: string }
export interface Candidate {
  rank: number; name: string; file: string;
  overall_score: number; keyword_score: number; semantic_score: number;
  matched_skills: string[]; partial_skills: string[]; missing_skills: string[];
  evidence: Evidence; explanation: string | null;
}
export interface JdInfo { title: string; company: string; required_skills: string[]; nice_skills: string[] }
export interface Analysis {
  jd: JdInfo; ranking: Candidate[]; bias_flags: BiasFlag[];
  meta: { resumes_processed: number; elapsed_ms: number; engine: string };
}
export interface ChatResponse { answer: string }
```

### `lib/api.ts` — the mock/live switch (the ONLY network file)
```ts
import type { Analysis } from './types';
import mockAnalysis from '../mocks/analyze.json';

const MODE = import.meta.env.VITE_API_MODE ?? 'mock';
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function analyze(jdFile: File | null, jdText: string | null, resumes: File[]): Promise<Analysis> {
  if (MODE === 'mock') {
    await new Promise(r => setTimeout(r, 1500));   // simulate work; show ProcessingState
    return mockAnalysis as Analysis;
  }
  const form = new FormData();
  if (jdFile) form.append('jd_file', jdFile);
  if (jdText) form.append('jd_text', jdText);
  resumes.forEach(f => form.append('resumes', f));
  const res = await fetch(`${BASE}/api/analyze`, { method: 'POST', body: form });
  if (!res.ok) throw new Error((await res.json()).detail ?? 'Analysis failed');
  return res.json();
}

export async function chat(question: string, analysis: Analysis): Promise<string> {
  if (MODE === 'mock') return 'Mock answer: candidate 1 scored highest on both keyword and semantic tracks.';
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, analysis }),
  });
  if (!res.ok) throw new Error('Chat failed');
  return (await res.json()).answer;
}
```
Nothing else in the app imports `fetch`. When backend is ready, integration = `.env` → `VITE_API_MODE=live`. That's it.

---

## 4. UI requirements per screen (what judges must SEE)

### Landing page (one screen — built LAST, see scope ladder rung 8)
- Product name, one-line pitch (*"Transparent shortlisting. We show the receipts."*), a 3-step "how it works" (Upload JD + resumes → Hybrid engine scores → Ranked & explained), ONE CTA button: **"Run an analysis"** → Analysis screen.
- NO pricing, testimonials, feature grids, or footer link farms — reads as overhype to startup judges.
- This is the one screen where `design-taste-frontend` applies at full strength (it IS a landing-page skill). The dashboard screens borrow its taste principles only.
- It is a multiplier on first impression, never a substitute for the demo — if the core is broken at 3:00, the landing page gets cut, not the demo.

### Analysis screen (upload — initial state)
- Two drop zones: **Job Description** (PDF or pasted text toggle) and **Resumes** (multi-PDF).
- File chips with remove buttons; count badge; a single prominent **"Shortlist candidates"** CTA.
- Empty state = clear value prop copy: *"Transparent shortlisting. See exactly why each candidate ranks where they do."*
- Guard: disable CTA until (jdFile OR jdText) AND ≥1 resume.

### Processing
- Progress indicator + "processing N resumes" + elapsed counter. (First live run may take 5–10 s — make this feel intentional, not frozen.)

### Ranked list (the hero screen — spend your best design effort here)
- Every row: rank number, name, file, **three score bars side-by-side: Overall / Keyword / Semantic**. This is the 35% rubric criterion made VISIBLE. Never show overall alone.
- Skill chips inline (matched/partial/missing, color-coded, compact).
- Rows 1–3 get a distinct "top 3" treatment (the explanation cards can live above the table or expand with the row).
- Sort = by rank, period. (Judges want to see the ranking, not re-sort it.)

### Candidate drawer (click any row)
- Full skill breakdown, per-section similarity bars (`evidence.sections`), and the **highlight quote rendered as a pull-quote from the actual resume** — this is your single most persuasive element. The recruiter sees the resume line that earned the score.
- `explanation` rendered for top 3; below rank 3 show the computed data without the prose.

### Bias panel
- Cards from `bias_flags`: phrase (quoted from JD), why, suggestion. If empty: friendly empty state ("No bias patterns detected in this JD").

### Chat (BONUS — only after 3:00)
- Panel that calls `chat(question, currentAnalysis)`. Always available to demo, never blocks anything.

### Non-negotiables
- Loading / error / empty states for every async surface.
- Error toast shows backend `detail` verbatim.
- The app must survive an unknown extra field in the response (ignore unknown keys — never `strict`).

---

## 5. Design direction (taste guidance)

Established with `design-taste-frontend` at scaffold time — but the constraints:
- **Approved direction first:** three static mocks live in `design/` (`mock-1-report.html` light report / `mock-2-console.html` dark console / `mock-3-workspace.html` recruiter workspace). The human approves ONE direction before scaffolding; build everything in that direction. The landing page derives its aesthetic from the same system — one accent, one radius scale, one type family across all three screens.
- **Product genre:** recruiter tool. Trust, clarity, precision. Think Linear/Stripe-adjacent calm, not neon dashboard.
- Dark or light — pick ONE and commit; don't build a theme toggle.
- Typography-led hierarchy: rank number and name lead; scores are scannable; chips quiet.
- Score bars need consistent scale (0–100) and accessible color contrast — judges will squint at these.
- The drawer pull-quote (evidence highlight) deserves real typographic love — it's the emotional beat of the demo.

---

## 6. Integration procedure (the 2:30 moment)

1. Confirm backend is running (`http://localhost:8000/docs` shows `/api/analyze`).
2. Flip `.env`: `VITE_API_MODE=live`. Restart dev server (env vars are build-time in Vite).
3. Upload the real JD + resumes. **If anything looks wrong: diff the live response against `mocks/analyze.json` field-by-field before touching a component.** 9 times out of 10 it's a payload mismatch, not a UI bug. Only then use `superpowers:systematic-debugging`.
4. Keep `VITE_API_MODE=mock` one revert away. If backend has a bad 20 minutes, you demo on mock — tell the human, don't hero-debug their code from your side.

## 7. Scope ladder (in strict order — never skip ahead)

1. Upload → mocked ranked list (bars + chips) ✅ **core**
2. Candidate drawer with evidence + highlight ✅ **core**
3. Top-3 explanation cards ✅ **core**
4. Live API integration ✅ **core**
5. Bias panel (mock data is fine until backend ships `bias.py`) ◆ strong-want
6. Empty/error/loading polish pass ◆ strong-want
7. `impeccable` visual polish pass ◆ strong-want
8. Landing page (one screen, `design-taste-frontend` at full strength) ◆ strong-want — ONLY after 1–7 work end-to-end
9. ChatPanel (mock) ◆ bonus
10. ChatPanel (live) ◆ bonus
11. Anything else you dreamed up ✋ only if 1–10 are done AND it's before 3:30

## 8. Hard rules

- **NEVER edit `backend/`.** Read it only to understand payloads.
- **NEVER change field names in `types.ts`/`api.ts` contract** after freeze — additive optional fields only.
- **No new dependencies after 2:30.**
- Commit at every GAMEPLAN §6 checkpoint: `checkpoint-N` messages.
- If the human asks for something that breaks the contract or the timeline, say so out loud before doing it.
