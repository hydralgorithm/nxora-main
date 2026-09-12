"""Nxora backend API — Smart Shortlisting Engine.

Endpoints (GAMEPLAN §4 frozen contract):
  POST /api/analyze   multipart: jd_file | jd_text + resumes[]  -> full ranking
  POST /api/chat      JSON: {question, analysis} -> {answer}    (bonus, deterministic)

Scoring path is 100% local: taxonomy keyword matching + sentence embeddings +
a local cross-encoder reranker. No LLM anywhere in ranking.
"""
from __future__ import annotations

import re
import threading
import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import parser as resume_parser
from jd_extract import extract_jd, load_taxonomy
from matcher.hybrid import band, blend
from matcher.keyword import keyword_match
from matcher.semantic import semantic_match_batch
from explain import build_explanation
from bias import audit_bias, pool_coverage_flags

app = FastAPI(title="Nxora Smart Shortlisting Engine", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_RESUMES = 50
ENGINE_NAME = "hybrid-v2-requirements"


def _warm_models() -> None:
    """Load both models at startup so the first /api/analyze isn't paying
    15-20s of model-load time inside its response."""
    try:
        from matcher import engine_config as cfg
        from matcher.semantic import get_model, get_reranker
        get_model().encode(["warm up"], normalize_embeddings=True, show_progress_bar=False)
        if cfg.RERANKER_ENABLED:
            get_reranker().predict([("warm up", "warm up")], show_progress_bar=False)
        print("[startup] semantic models warm")
    except Exception as e:
        print(f"[startup] model warm-up skipped: {type(e).__name__}: {e}")


threading.Thread(target=_warm_models, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": ENGINE_NAME}


@app.post("/api/analyze")
async def analyze(
    jd_file: UploadFile | None = File(default=None),
    jd_text: str | None = Form(default=None),
    resumes: list[UploadFile] = File(default=[]),
) -> dict:
    started = time.perf_counter()

    # ---- Input validation (contract: exactly one JD source, 1-50 resumes).
    if (jd_file is None) == (jd_text is None or not jd_text.strip()):
        raise HTTPException(status_code=400,
                            detail="Provide exactly one of 'jd_file' or 'jd_text'.")
    if not resumes:
        raise HTTPException(status_code=400, detail="Provide at least one resume file.")
    if len(resumes) > MAX_RESUMES:
        raise HTTPException(status_code=400,
                            detail=f"Too many resumes ({len(resumes)}); max is {MAX_RESUMES}.")

    # ---- JD side.
    try:
        if jd_file is not None:
            jd_raw = await jd_file.read()
            jd_str, _ = resume_parser.extract_text(jd_raw, jd_file.filename or "jd.pdf")
        else:
            jd_str = jd_text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read the JD file: {e}")
    taxonomy = load_taxonomy()
    jd = extract_jd(jd_str, taxonomy)
    if not jd.requirements:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any requirements from the JD. Is it a job description?")

    # ---- Resume side: one bad file must never kill the batch.
    parsed: list[resume_parser.ResumeData] = []
    for upload in resumes:
        try:
            data = await upload.read()
            parsed.append(resume_parser.parse_resume(data, upload.filename or "resume"))
        except Exception as e:
            fname = upload.filename or "resume"
            parsed.append(resume_parser.ResumeData(
                name=resume_parser._extract_name("", fname), file=fname, sections=[],
                full_text="", parse_warning=f"unreadable file: {e}"))

    # ---- Dedupe: same person submitted in multiple formats/versions (same
    # email). Keep the best-parsed copy — cleanly parsed and longest text wins.
    # Email is the safe key; resumes without an email are never merged.
    def _quality(r: resume_parser.ResumeData) -> tuple[int, int]:
        return (0 if r.parse_warning is None else -1, len(r.full_text))

    deduped: list[resume_parser.ResumeData] = []
    best_by_email: dict[str, resume_parser.ResumeData] = {}
    dropped: list[dict] = []
    for rd in parsed:
        if not rd.email:
            deduped.append(rd)
            continue
        kept = best_by_email.get(rd.email)
        if kept is None:
            best_by_email[rd.email] = rd
            deduped.append(rd)
        elif _quality(rd) > _quality(kept):
            deduped[deduped.index(kept)] = rd       # replace in place, keep order
            best_by_email[rd.email] = rd
            dropped.append({"name": kept.name, "file": kept.file,
                            "kept_file": rd.file, "email": rd.email})
        else:
            dropped.append({"name": rd.name, "file": rd.file,
                            "kept_file": kept.file, "email": rd.email})
    parsed = deduped

    # ---- Score: keyword track, then one batched semantic pass, then blend.
    keyword_results = [keyword_match(r, jd, taxonomy) for r in parsed]
    try:
        semantic_results = semantic_match_batch(parsed, jd)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Semantic engine failed to load: {e}")

    rows = [{"resume": r, "kw": k, "sem": s, "overall": blend(k, s)}
            for r, k, s in zip(parsed, keyword_results, semantic_results)]
    rows.sort(key=lambda row: (-row["overall"], -row["kw"].score,
                               row["resume"].name.lower()))

    ranking = []
    for idx, row in enumerate(rows, start=1):
        resume, kw, sem = row["resume"], row["kw"], row["sem"]
        ranking.append({
            "rank": idx,
            "name": resume.name,
            "file": resume.file,
            "overall_score": row["overall"],
            "keyword_score": kw.score,
            "semantic_score": sem.score,
            "matched_skills": kw.matched,
            "partial_skills": kw.partial,
            "missing_skills": kw.missing,
            "evidence": {
                "sections": [{"name": name, "similarity": sim}
                             for name, sim in sem.section_scores],
                "highlight": sem.highlight,
            },
            "explanation": (build_explanation(resume.name, idx, row["overall"], kw, sem)
                            if idx <= 3 else None),
            # --- additive optional fields (contract-safe) ---
            "band": band(row["overall"]),
            "parse_warning": resume.parse_warning,
            "skill_evidence": kw.skill_evidence,
            "requirement_evidence": [
                {"requirement": ev.requirement, "skill": ev.skill, "kind": ev.kind,
                 "section": ev.section, "similarity": ev.similarity, "line": ev.line}
                for ev in sem.requirement_evidence],
        })

    bias_flags = audit_bias(jd) + pool_coverage_flags(jd, keyword_results)

    return {
        "jd": {
            "title": jd.title,
            "company": jd.company,
            "required_skills": jd.required_skills,
            "nice_skills": jd.nice_skills,
        },
        "ranking": ranking,
        "bias_flags": bias_flags,
        "meta": {
            "resumes_processed": len(ranking),
            "duplicates_removed": len(dropped),
            "duplicates": dropped,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "engine": ENGINE_NAME,
        },
    }


@app.post("/api/chat")
async def chat(body: dict) -> dict:
    """Deterministic recruiter Q&A over the analysis object the UI is showing.

    No LLM: we locate the candidates the question refers to (by rank number or
    name) and explain the delta using the engine's own numbers and skill lists.
    """
    question = str(body.get("question") or "").strip()
    analysis = body.get("analysis") or {}
    ranking = analysis.get("ranking") or []
    if not question or not ranking:
        return {"answer": "Upload a JD and resumes first, then ask me about the candidates."}

    candidates = _find_candidates(question, ranking)

    if len(candidates) >= 2:
        a, b = candidates[0], candidates[1]
        delta = round(a["overall_score"] - b["overall_score"], 1)
        parts = [f"{a['name']} (#{a['rank']}, {a['overall_score']}) ranks above "
                 f"{b['name']} (#{b['rank']}, {b['overall_score']}) by {delta} points overall."]
        parts.append(f"Keyword {a['keyword_score']} vs {b['keyword_score']}, "
                     f"semantic {a['semantic_score']} vs {b['semantic_score']}.")
        a_only = [s for s in a["matched_skills"] if s not in b["matched_skills"]]
        b_missing = [s for s in b["missing_skills"] if s not in a["missing_skills"]]
        if a_only:
            parts.append(f"{a['name']} demonstrates skills the other doesn't: "
                         f"{', '.join(a_only)}.")
        if b_missing:
            parts.append(f"{b['name']} is missing: {', '.join(b_missing)}.")
        ev = (a.get("evidence") or {}).get("highlight")
        if ev:
            parts.append(f"Strongest evidence for {a['name']}: \"{ev}\"")
        return {"answer": " ".join(parts)}

    if len(candidates) == 1:
        c = candidates[0]
        matched = ", ".join(c["matched_skills"]) or "none of the required skills directly"
        missing = ", ".join(c["missing_skills"]) or "nothing required"
        return {"answer": (
            f"{c['name']} is rank #{c['rank']} with {c['overall_score']}/100 overall "
            f"(keyword {c['keyword_score']}, semantic {c['semantic_score']}). "
            f"Matched: {matched}. Missing: {missing}. Band: {c.get('band', 'n/a')}.")}

    # Generic: no candidate identified -> summarise the podium.
    lines = [f"#{c['rank']} {c['name']} — {c['overall_score']}/100 "
             f"(keyword {c['keyword_score']}, semantic {c['semantic_score']})"
             for c in ranking[:3]]
    return {"answer": "Current top candidates: " + " | ".join(lines) +
            ". Ask about a candidate by name or rank, e.g. 'why is candidate 1 above candidate 2?'."}


# ---------------------------------------------------------------------------

def _find_candidates(question: str, ranking: list[dict]) -> list[dict]:
    """Candidates the question refers to, in order of first mention (max 2)."""
    q = question.lower()
    found: list[dict] = []

    def add(c: dict) -> None:
        if c not in found:
            found.append(c)

    # "candidate 2", "rank 3", "#1", "number 2"
    for m in re.finditer(r"(?:candidate|rank(?:ed|ing)?|#|number)\s*(\d+)", q):
        n = int(m.group(1))
        if 1 <= n <= len(ranking):
            add(ranking[n - 1])
    # Names (case-insensitive; any distinctive word of the name is enough)
    for c in ranking:
        name_words = [w for w in str(c["name"]).lower().split() if len(w) > 2]
        if name_words and any(w in q for w in name_words):
            add(c)
    return found[:2]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
