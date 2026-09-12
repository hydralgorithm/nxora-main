"""Hybrid blend: overall = ALPHA * keyword + (1 - ALPHA) * semantic.

ALPHA is THE single tuning knob (GAMEPLAN §5). Confidence bands are an additive
contract field for the UI.
"""
from __future__ import annotations

from matcher.keyword import KeywordResult
from matcher.semantic import SemanticResult

ALPHA = 0.5          # weight of keyword_score; semantic gets 1 - ALPHA

BAND_STRONG = 70.0   # >= this -> "strong"
BAND_MEDIUM = 45.0   # >= this -> "medium"


def blend(keyword: KeywordResult, semantic: SemanticResult) -> float:
    """Overall 0-100."""
    return round(ALPHA * keyword.score + (1.0 - ALPHA) * semantic.score, 1)


def band(overall: float) -> str:
    if overall >= BAND_STRONG:
        return "strong"
    if overall >= BAND_MEDIUM:
        return "medium"
    return "weak"
