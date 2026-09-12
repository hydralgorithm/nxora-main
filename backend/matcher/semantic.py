"""Semantic track: requirement-level embedding matching + cross-encoder verification.

Pipeline (one batched encode per request):
  1. Embed every JD requirement statement (query side).
  2. Embed every resume section (passage side) and every section line (for highlights).
  3. Per (resume, requirement): similarity = max cosine over the resume's sections.
  4. semantic_score = calibrated weighted mean over requirements (weights mirror keyword track).
  5. Optional: cross-encoder rescore of (requirement, best line) pairs — the two-stage
     retrieve-then-rerank architecture — blended into the final semantic score.

Every number is traceable: per-requirement evidence (section, similarity, line) is kept
for the UI heatmap, drawer evidence, and template explanations.
"""
from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field

import numpy as np

from jd_extract import JdData
from parser import ResumeData
from matcher import engine_config as cfg

_MODEL = None
_RERANKER = None
# FastAPI runs sync endpoints in a threadpool: serialize model inference so two
# concurrent /api/analyze calls never hit encode()/predict() at the same time.
_INFERENCE_LOCK = threading.Lock()


def get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        try:
            _MODEL = SentenceTransformer(cfg.MODEL_ID)
        except Exception as e:  # pragma: no cover - hard dependency, clear failure
            raise RuntimeError(
                f"Could not load semantic model '{cfg.MODEL_ID}' (offline without cache?). "
                f"Original error: {e}") from e
    return _MODEL


def get_reranker():
    global _RERANKER
    if _RERANKER is None:
        from sentence_transformers import CrossEncoder
        _RERANKER = CrossEncoder(cfg.RERANKER_ID)
    return _RERANKER


@dataclass
class RequirementEvidence:
    requirement: str       # JD statement
    skill: str | None      # canonical skill or None
    kind: str              # required | nice | responsibility
    section: str           # best-matching resume section name
    similarity: float      # raw cosine 0-1
    line: str              # best resume line for this requirement


@dataclass
class SemanticResult:
    score: float                                # 0-100 calibrated final (bi + optional reranker)
    raw_score: float                            # weighted mean raw cosine
    section_scores: list[tuple[str, float]]     # (section name, weighted-mean cosine over reqs)
    highlight: str                              # best resume line overall
    highlight_requirement: str = ""             # the requirement the highlight answers
    requirement_evidence: list[RequirementEvidence] = field(default_factory=list)


def _calibrate(cos: float) -> float:
    return 100.0 * max(0.0, min(1.0, (cos - cfg.COS_MIN) / (cfg.COS_MAX - cfg.COS_MIN)))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def _lines_of(section_text: str, cap: int = 20) -> list[str]:
    lines = [l.strip() for l in section_text.splitlines()
             if 25 <= len(l.strip()) <= 250]
    return lines[:cap]


def semantic_match_batch(resumes: list[ResumeData], jd: JdData,
                         use_reranker: bool | None = None) -> list[SemanticResult]:
    """Score every resume against every JD requirement. One batched encode call."""
    use_reranker = cfg.RERANKER_ENABLED if use_reranker is None else use_reranker
    model = get_model()
    reqs = jd.requirements
    if not reqs:
        return [SemanticResult(score=0.0, raw_score=0.0, section_scores=[],
                               highlight="") for _ in resumes]
    weights = np.array([r.weight for r in reqs])
    wsum = float(weights.sum())

    # --- Collect every text to encode (requirements, sections, lines) in one list.
    all_texts: list[str] = [f"{cfg.QUERY_PREFIX}{r.statement}" for r in reqs]
    n_req = len(reqs)
    # Per resume: sections as [(emb_pos, section_index_in_resume)]; lines as
    # (section_index_in_resume, emb_pos, n_lines).
    sec_slices: list[list[tuple[int, int]]] = []
    line_slices: list[list[tuple[int, int, int]]] = []

    for resume in resumes:
        secs: list[tuple[int, int]] = []
        lines: list[tuple[int, int, int]] = []
        for s_idx, section in enumerate(resume.sections):
            if not section.text or len(section.text) < 20:
                continue
            # Positions are RELATIVE to doc_emb (requirements stripped off the front).
            secs.append((len(all_texts) - n_req, s_idx))
            all_texts.append(f"{cfg.DOC_PREFIX}{section.text}")
            sec_lines = _lines_of(section.text)
            lstart = len(all_texts) - n_req
            all_texts.extend(f"{cfg.DOC_PREFIX}{l}" for l in sec_lines)
            lines.append((s_idx, lstart, len(sec_lines)))
        sec_slices.append(secs)
        line_slices.append(lines)

    with _INFERENCE_LOCK:
        embeddings = np.asarray(model.encode(all_texts, normalize_embeddings=True,
                                             show_progress_bar=False, batch_size=64))
    req_emb = embeddings[:n_req]
    doc_emb = embeddings[n_req:]

    # Cross-encoder pairs: (position in results, req_idx, requirement, text).
    pair_meta: list[tuple[int, int, str, str]] = []

    results: list[SemanticResult] = []
    for i, resume in enumerate(resumes):
        secs = sec_slices[i]
        if not secs:
            results.append(SemanticResult(
                score=0.0, raw_score=0.0, section_scores=[],
                highlight="No readable text sections in this resume."))
            continue

        sec_mat = np.vstack([doc_emb[pos:pos + 1] for pos, _ in secs])   # (n_sec, dim)
        sim = req_emb @ sec_mat.T                                         # (n_req, n_sec)
        best_sec_pos = sim.argmax(axis=1)                                 # index into secs
        best_sec_sim = sim.max(axis=1)
        raw = float((best_sec_sim * weights).sum() / wsum)

        section_scores = [
            (resume.sections[s_idx].name, round(float(sim[:, j] @ weights / wsum), 3))
            for j, (_, s_idx) in enumerate(secs)]

        # Lines grouped by their resume-section index for evidence lookup.
        lines_by_sec: dict[int, tuple[int, int]] = {s: (st, n) for s, st, n in line_slices[i]}

        evidence: list[RequirementEvidence] = []
        for r_idx, req in enumerate(reqs):
            s_idx = secs[best_sec_pos[r_idx]][1]
            sec = resume.sections[s_idx]
            best_line, best_line_sim = "", -1.0
            if s_idx in lines_by_sec:
                lstart, llen = lines_by_sec[s_idx]
                if llen:
                    line_sim = (req_emb[r_idx:r_idx + 1] @ doc_emb[lstart:lstart + llen].T).ravel()
                    j = int(line_sim.argmax())
                    best_line_sim = float(line_sim[j])
                    # all_texts is absolute (requirements first); doc positions are relative.
                    best_line = all_texts[n_req + lstart + j][len(cfg.DOC_PREFIX):]
            evidence.append(RequirementEvidence(
                requirement=req.statement, skill=req.skill, kind=req.kind,
                section=sec.name, similarity=round(float(best_sec_sim[r_idx]), 3),
                line=best_line))
            if use_reranker:
                pair_meta.append((len(results), r_idx, req.statement,
                                  best_line or sec.text[:300]))

        # Global highlight: strongest requirement with a concrete line.
        top = max((e for e in evidence if e.line),
                  key=lambda e: e.similarity, default=None)
        results.append(SemanticResult(
            score=round(_calibrate(raw), 1), raw_score=round(raw, 4),
            section_scores=section_scores,
            highlight=top.line if top else "",
            highlight_requirement=top.requirement if top else "",
            requirement_evidence=evidence))

    # --- Cross-encoder verification stage (one predict call for all pairs).
    if use_reranker and pair_meta:
        try:
            ce = get_reranker()
            with _INFERENCE_LOCK:
                logits = np.asarray(ce.predict(
                    [(q, d) for _, _, q, d in pair_meta], show_progress_bar=False))
            # Weighted mean of calibrated pair scores per resume.
            acc: dict[int, list[float]] = {}
            wacc: dict[int, list[float]] = {}
            for (pos, r_idx, _, _), logit in zip(pair_meta, logits):
                sig = _sigmoid(float(logit))
                cal = 100.0 * max(0.0, min(
                    1.0, (sig - cfg.RERANK_SIG_MIN) / (cfg.RERANK_SIG_MAX - cfg.RERANK_SIG_MIN)))
                acc.setdefault(pos, []).append(cal)
                wacc.setdefault(pos, []).append(cal * float(reqs[r_idx].weight))
            for pos, cals in acc.items():
                # Weighted mean = sum(w_i * cal_i) / sum(w_i); pair order follows
                # requirement order per resume, so weights align index-for-index.
                rerank_score = (sum(wacc[pos]) / wsum
                                if len(cals) == len(reqs) else float(np.mean(cals)))
                res = results[pos]
                res.score = round((1 - cfg.RERANKER_WEIGHT) * res.score
                                  + cfg.RERANKER_WEIGHT * rerank_score, 1)
        except Exception as e:  # reranker is an enhancement; never kill the pipeline
            print(f"[semantic] reranker disabled after failure: {type(e).__name__}: {e}")

    return results
