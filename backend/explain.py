"""Deterministic top-3 explanations — no LLM, fully reproducible (rubric: top-3
explanations of matched/missing skills, 20%).

Template renders from the engine's own evidence: scores, matched/partial/missing
skills, and the strongest requirement→line match from the semantic track.
"""
from __future__ import annotations

from matcher.keyword import KeywordResult
from matcher.semantic import SemanticResult


def build_explanation(name: str, rank: int, overall: float,
                      kw: KeywordResult, sem: SemanticResult) -> str:
    matched = ", ".join(kw.matched[:5]) if kw.matched else "no direct skill matches"
    partial = (f"; related experience detected: {', '.join(kw.partial[:4])}"
               if kw.partial else "")
    if kw.missing:
        gaps = ", ".join(kw.missing[:4])
    elif kw.matched or kw.partial:
        gaps = "none of the required skills are missing"
    else:
        gaps = "no evidence of the required skills in this resume"

    evidence = ""
    if sem.highlight and sem.highlight_requirement:
        evidence = (f" Key evidence: \"{sem.highlight[:160]}\" "
                    f"(strongest match for: \"{sem.highlight_requirement[:100]}\").")

    return (f"{name} ranks #{rank} with an overall score of {overall}/100 "
            f"(keyword {kw.score}, semantic {sem.score}). "
            f"Strong matches: {matched}{partial}. "
            f"Gaps: {gaps}.{evidence}")
