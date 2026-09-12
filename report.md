**InternLoom AI Hackathon · September 2026**
Team: Abdul Fattah (backend / ML) · Rmais (frontend)

## The Problem

Rank 15–220 resumes against one job description — not with a keyword counter, and not with a black-box LLM, but with a system whose scores a recruiter can trust, explain, and defend.

## Our Approach: Requirement-Level Hybrid Matching

Most resume screeners either count keywords (fragile: misses paraphrases, punishes honest resumes) or embed whole documents (opaque: everyone gets a similar-looking score). We do neither. **We decompose the JD into individual weighted requirements** (required skills ×3, nice-to-have ×1, responsibilities ×2) and score every candidate **per requirement** on two independent tracks, blended 50/50:

```
JD ──► requirement extraction (weighted, 56-entry taxonomy)
                │
     ┌──────────┴──────────┐
 keyword track         semantic track
 (exact + synonym       (per-requirement best-section
  matching, credit      cosine via MiniLM embeddings,
  by evidence tier)     verified by a local cross-encoder)
     └──────────┬──────────┘
            calibrated blend ──► ranked shortlist
        with per-requirement evidence lines & explanations
```

## Key Decisions and Why

**1. Score per requirement, not per document.**
A single "75% match" teaches a recruiter nothing. Per-requirement scoring shows, for every candidate and every JD line, whether it matched, where in the resume the evidence is, and how strong that evidence is.

**2. Evidence-tiered credit: 1.0 / 0.85 / 0.60.**
A skill *demonstrated* in Experience or Projects earns full credit; the same skill merely *listed* in a Skills section earns 0.85; a *synonym* hit (resume says "Express" for a Node.js requirement) earns 0.60. This is the difference between a candidate who built with a technology and one who typed its name.

**3. Two tracks, because each fails where the other succeeds.**
Keyword matching is exact but blind to paraphrase ("built server-side services" for a Node.js requirement); embeddings catch paraphrase but can hallucinate relevance. A small local cross-encoder re-verifies each requirement–evidence pair and is blended with the bi-encoder score, keeping both honest.

**4. Models chosen by benchmark, not by vibe.**
We evaluated 5 embedding models and 2 rerankers on a labeled corpus. We chose all-MiniLM-L6-v2 (Spearman 0.931 against ground-truth tiers, best score spread, seconds for the full pool) and ettin-reranker-32m (0.944) — larger models matched accuracy but took minutes per pool, useless in a live demo.

**5. Zero LLM APIs anywhere — by design, not just by rule.**
Every score is computed by deterministic local components; the same input always produces the same ranking. Even the recruiter Q&A chat is deterministic, built from the engine's own numbers rather than a generated opinion.

**6. Honest scores with meaningful spread.**
Affine calibration maps raw similarities to a true 0–100 scale, so strong, medium, and weak candidates visibly separate (a ~63-point spread across our real 144-candidate test pool) instead of clustering at "everyone is 71%".

**7. Robustness as a feature.**
The parser handles PDF, DOCX, legacy DOC, XML/HTML, and TXT, sniffing content before trusting extensions; a corrupt or scanned file never crashes the batch — it scores on what's readable and flags why. Duplicate submissions (same person, different format) are detected by email and merged.

**8. Fairness tooling.**
The JD itself is audited for exclusionary language ("rockstar", age-coded phrases, over-constraint), and pool-coverage analysis warns when a requirement would screen out most of the candidate pool — the tool critiques the job description, not just the applicants.

## How We Validated It

- **15 automated tests** — the exact partial-credit case from the problem statement ("Express" → Node.js partial credit) is asserted by a dedicated test; parser survives corrupt input; calibration bounds; dedupe; API contract.
- **Labeled synthetic corpus** (18 resumes, three quality tiers): strong > partial > weak ordering holds with >60-point spread.
- **Real-world dataset**: 220 real resumes in mixed formats, 144 unique candidates — zero parse failures, correct domain ordering, full score spread. Warm analysis of the whole pool runs in seconds on CPU.

## Stack

FastAPI (Python) · sentence-transformers (MiniLM + local cross-encoder) · custom taxonomy & matching engine · React + Vite + TypeScript frontend. Runs fully offline — no API keys, no data leaves the machine.

## Roadmap

Skills-ontology expansion (ESCO aliases), years-of-experience extraction, OCR fallback for scanned PDFs, and skill-family credit (React Native ≈ React) via embedding similarity — all slotting into the existing per-requirement architecture.

Notes on what I changed vs. your current draft:

- Length: ~1 page instead of ~5 — everything a judge needs to score the rubric, nothing they'd skip.
- Fixed: "55-entry taxonomy" → 56 (verified against taxonomy.json just now).
- Cut: the full architecture ASCII diagram, API contract JSON, repo layout, run instructions, test-name listing, and the rubric self-assessment table — those belong in the README (which already has them), not the judge report. Keep this as REPORT.md for submission; the deep technical detail stays available if judges ask follow-ups.
- Kept the strongest material: the benchmark table narrative (decisions 4), the Express/Node.js example, and the determinism argument — those are your credibility plays during the walkthrough.

One heads-up: I couldn't write this file for you directly — my session is locked to the worktree and the main folder rejects my edits. Paste the block above into C:\Users\Abdul Fattah\Desktop\nxora-main\REPORT.md yourself (or hand it to your main-folder session).

result: Judge-facing REPORT.md replacement written — brief one-pager covering approach, 8 key decisions with rationale, and validation; delivered in chat for pasting into the main repo (my session can't write outside the worktree); taxonomy count corrected from 55 to 56 after verifying taxonomy.json.