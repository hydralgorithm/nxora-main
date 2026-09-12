# Demo Script — Smart Shortlisting Engine (5:00)

**Team Nexora · 2 presenters**

- **A = Engine voice** (backend/ML: how scoring works, models, numbers)
- **B = Product voice** (frontend: what the recruiter sees, why it's designed this way)

Target runtime: **4:30** — leaves a 30s buffer for slow uploads or a stumble.
Spoken lines are written to pace (~140 wpm). **Don't memorize — rehearse twice.**

---

## Before you walk up (checklist)

- [ ] Backend: `cd backend && python -m uvicorn main:app --port 8000` — started **5 min before** presenting (models need ~15s to warm; first analysis must be the fast ~4s one)
- [ ] Frontend: `npm run dev` with `.env` set to `VITE_API_MODE=live`
- [ ] Browser pre-opened on the **Landing page**, zoom ~110%, notifications silenced
- [ ] Sample JD is **pre-filled** and the 18-resume folder is one click away in the file picker
- [ ] Fallback: if anything live fails, flip to mock mode and keep talking — never debug on stage

**Stage cues:** `[A→]` A talks · `[B→]` B talks · `[BOTH]` · timestamps are cumulative targets.

---

## 0:00 — Landing page [B→] (~40s)

> Most shortlisting tools give you a number and ask you to trust it. We built the opposite:
> **Shortlist** ranks every resume against a job description on two independent tracks —
> exact keyword matching and semantic similarity — and shows you **the receipts**: the exact
> resume line behind every score.
>
> Two things before we start. First — **zero LLM calls in the scoring path.** The rule says
> pasting a resume into an LLM and asking for a score doesn't count. Our matching is our own
> logic; the embedding models are just components inside it, like a regex or a sort.
> Second — **everything runs locally, offline, on this laptop.** No API keys, no data leaving
> the room. That's not just demo convenience — real placement data shouldn't leave the machine.

**Click:** "Run an analysis"

## 0:40 — Upload screen [A→] (~40s)

> The JD is pre-filled — TechNova's Junior Full Stack Developer intern role. Notice it says
> **"rockstar coder"** and demands **ten hard requirements**. That's on purpose — watch the
> bias audit light up later.
>
> A design choice worth 30 seconds: we don't score resumes against the *raw JD text*. We
> first **decompose the JD into weighted requirements** — required skills weigh ×3,
> nice-to-haves ×1, generic responsibilities ×2 — using the *same skill taxonomy* the resume
> side uses. Both sides of every match speak one vocabulary. Most teams match resume↔JD
> blobs; we match resume↔requirement, which is what a recruiter actually does.

**Action:** drop the 18 resumes in, hit **Analyze & Rank** (~4s).

## 1:20 — Ranked list [B→] (~50s)

> Here's the full pool, ranked, in about four seconds — on CPU.
>
> Every row shows **three numbers, not one**: overall, keyword, and semantic. Why show both
> tracks? Because they fail differently. Keyword matching catches the exact stack but misses
> paraphrases; semantic matching catches "built REST APIs with Express" ≈ Node.js backend,
> but can't verify a skill was literally claimed. Blended 50/50, each covers the other's
> blind spot — and the rubric's "both must genuinely factor in" is *visible on every row*.
>
> Note the spread — strong candidates in the 80s, weak ones near the bottom. Not everyone
> clumped at 71. That spread is a tuned property: we benchmarked five embedding models and
> picked the one with the best tier separation. More on that in a second.

**Click:** candidate #1 (e.g. Ananya) to open the detail drawer.

## 2:10 — Candidate drawer: the receipts [A→] (~60s)

> This is the core of our submission. For **each JD requirement separately**, we show the
> best-matching resume line and its similarity. This line — *"Built REST APIs with Express
> and MongoDB for a food-delivery app"* — is how you get **partial credit for Node.js
> without the word Node ever appearing**. That's the exact example from the problem
> statement, and there's a test asserting it.
>
> How the semantic track works, briefly: every requirement and every resume section is
> embedded in **one batched pass** with MiniLM; per requirement, the best section wins —
> so one strong project surfaces a candidate even with a thin Skills section. Then a local
> **cross-encoder reranks** each requirement-line pair — a two-stage retrieve-then-rerank,
> blended 60/40. Why rerank? Bi-encoders are fast but coarse; a cross-encoder reads the
> pair together. We measured: it raised Spearman from 0.93 to 0.94 — the best of anything
> we tested.
>
> And **why MiniLM and not a bigger model?** We didn't guess — `bench_models.py` benchmarked
> five candidates on *our* task. MiniLM tied for best correlation, had **3× the score
> spread** of the runner-up, and ran in 3.5 seconds. Bigger models were slower and spread
> scores *less*. Evidence over vibes.

**Scroll briefly:** matched skills each with their resume evidence line; partial/missing chips.

## 3:10 — Explanations + Bias panel [B→] (~45s)

> The top-3 cards are **deterministic templates over the engine's own evidence** — no LLM
> wrote these, and every clause cross-checks against what's on screen. Judges can verify us;
> that's the point.
>
> The bias panel found the **"rockstar" phrasing** and the over-constrained must-have list —
> each with a rewrite suggestion. And the blue-tagged ones are **pool-aware**: if a required
> skill almost nobody in this pool demonstrates, we flag that the JD is screening out the
> pool. That's a bias signal you can only see with data — a static word list can't do it.

**Open chat panel, ask:** "Why is candidate 1 above candidate 2?"

## 3:55 — Chat [A→] (~35s)

> Even the chat is deterministic — no LLM here either. It locates both candidates and explains
> the gap using **our own numbers**: the score deltas, the skills one has that the other
> doesn't, and the strongest evidence quote. Same question, same answer, every time.
>
> One more integrity layer: we **flag, never silently penalize**. A resume with seven skills
> all listed but never demonstrated gets a "keyword stuffing suspected" flag — the recruiter
> decides, not a hidden multiplier. A system that quietly rewrites scores is exactly the
> black box we're building against.

## 4:30 — Close [BOTH — A first] (~30s)

> **[A]** So: hybrid keyword + semantic scoring, per-requirement evidence, rerank
> verification, benchmarked model choice, 15 passing tests including the problem statement's
> own example, ~4 seconds end to end.
>
> **[B]** And every claim on screen traces to a number we computed ourselves. **Recruiters
> don't trust black boxes. We show the receipts.**
>
> **[BOTH]** We're Nexora — happy to walk through the code.

---

## Q&A ammunition (don't say unless asked)

| Question | Answer |
|---|---|
| "Why 50/50 blend?" | `ALPHA = 0.5` is the single tuning knob, tuned once on synthetic data — never per-candidate. 0.3–0.7 is the sane range; 0.5 treated both tracks as equally trustworthy since they fail independently. |
| "What if a resume is an image scan?" | Parser detects low text, returns a `parse_warning` ("possible image scan"), scores on what exists, never crashes — one bad file can't 500 the batch. Shown as a warning icon in the UI. |
| "How do you handle duplicate uploads?" | Email-based dedupe: same candidate in two formats merges, best-parsed copy wins, `meta.duplicates` reports it. |
| "Why max-over-sections, not mean similarity?" | Relevant experience lives in one section; max lets it surface. The keyword track's location-aware credit (demonstrated 1.0 > listed 0.85) guards against a thin Skills section faking depth. |
| "How is this different from an ATS?" | ATS filters on literal keywords. We do synonym expansion + per-requirement semantic matching + evidence — and we audit the *JD itself*, which no ATS does. |
| "Could you rank wrongly?" | The tie-break is deterministic (overall → keyword → name), and tier ordering on our ground-truth corpus is a test: strong > partial > weak with ≥15 points spread. |
| "What would you build next?" | Multi-JD batch endpoint, per-recruiter feedback loop to tune ALPHA, JD-side skill extraction learned from the pool instead of the fixed taxonomy. |

## Timing tripwires

- **Behind at 2:10?** Skip scrolling the drawer — jump straight to the requirement-evidence block.
- **Analysis taking >10s?** Keep talking (cold-start is pre-warmed; if it still lags, say "first-run model load — watch the elapsed counter") and let B narrate the loading state: *"even the loading screen shows what's happening — parsing, matching, ranking."*
- **Live fails entirely?** Mock mode shows the identical UI on realistic data; say "engine restarts between runs" and demo the flow. Never apologize twice.
