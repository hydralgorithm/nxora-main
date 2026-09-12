"""JD bias audit (bonus rubric) + pool-aware coverage flags (approved twist).

Two layers:
  1. Static audit — exclusionary / gendered / ageist idioms in the JD text, with
     concrete rewrite suggestions. Deterministic word-list matching, no LLM.
  2. Pool-aware audit — a required skill that almost nobody in the uploaded pool
     demonstrates is flagged as "screens out the pool": the JD (or the market)
     is over-constraining, which is a bias signal you can only see with data.
"""
from __future__ import annotations

import re

from jd_extract import JdData
from matcher.keyword import KeywordResult

# phrase -> (why, suggestion)
_BIAS_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\brock\s?stars?\b|\bninjas?\b|\bgurus?\b|\bwizards?\b|\bsuperheroes?\b", re.I),
     "Bro-culture jargon — discourages qualified applicants who read it as 'not for me'.",
     "Replace with the concrete skill or responsibility you actually need."),
    (re.compile(r"\byoung\b.{0,30}\b(energetic|dynamic|fresh)\b|\brecent grads? only\b|\bstudents? only\b", re.I),
     "Age-coded language — proxies for age, which is a protected characteristic.",
     "Drop the qualifier; state the actual requirement (e.g. 'available for a 6-month internship')."),
    (re.compile(r"\b(he|his|him)\b\s+(/|or)\s+\b(she|her)\b", re.I),
     "Explicit gender pairing reads as defaulting to male.",
     "Use 'they/the candidate'."),
    (re.compile(r"\bmales?\b|\bfemales?\b|\bguys?\b", re.I),
     "Gender-explicit wording in a hiring context.",
     "Refer to 'candidates' or 'applicants'."),
    (re.compile(r"\bno\s+(freshers|beginners|career\s+changers)\b", re.I),
     "Excludes non-traditional backgrounds that may have the required skills.",
     "State required experience in years instead of excluding groups."),
    (re.compile(r"\bmust\s+be\s+(from|based\s+in)\s+[A-Z]", 0),
     "Location-restrictive phrasing can exclude strong remote-capable candidates.",
     "Say 'remote-friendly' or justify the on-site need explicitly."),
    (re.compile(r"\bworks\s+well\s+under\s+pressure\b|\bfast[- ]paced\s+only\b", re.I),
     "Pressure framing correlates with burnout culture and screens out methodical candidates.",
     "Describe the environment factually and the support provided."),
]

MAX_REQUIRED_SKILLS = 12         # beyond this the JD is a wishlist, not a role
POOL_FRACTION = 0.15             # required skill matched by <15% of pool -> flag
POOL_MIN = 2                     # ...but only when the pool is big enough to tell


def audit_bias(jd: JdData) -> list[dict]:
    """Static JD text audit -> contract-shape bias flags."""
    flags: list[dict] = []
    text = jd.full_text
    for pattern, why, suggestion in _BIAS_PATTERNS:
        m = pattern.search(text)
        if m:
            flags.append({"phrase": m.group(0), "why": why, "suggestion": suggestion})

    if len(jd.required_skills) > MAX_REQUIRED_SKILLS:
        flags.append({
            "phrase": f"{len(jd.required_skills)} hard-required skills",
            "why": "Over-constrained JD — every extra hard requirement shrinks the "
                   "qualified pool, often with no real need.",
            "suggestion": f"Move {len(jd.required_skills) - MAX_REQUIRED_SKILLS} of these "
                          f"to 'nice to have' and re-rank.",
        })
    return flags


def pool_coverage_flags(jd: JdData, keyword_results: list[KeywordResult]) -> list[dict]:
    """Pool-aware flags: required skills almost nobody in this pool demonstrates."""
    if not keyword_results:
        return []
    n = len(keyword_results)
    threshold = max(POOL_MIN, int(n * POOL_FRACTION))
    flags: list[dict] = []
    for skill in jd.required_skills:
        holders = sum(1 for kr in keyword_results
                      if skill in kr.matched or skill in kr.partial)
        if holders < threshold:
            flags.append({
                "phrase": f"Required skill '{skill}' — only {holders}/{n} candidates show it",
                "why": "This requirement screens out nearly the entire pool. Either it is "
                       "rare in this market or the JD is over-specified.",
                "suggestion": f"Consider making '{skill}' a trained-on-the-job skill or a "
                              f"nice-to-have; the ranking currently penalises everyone "
                              f"for this one line.",
            })
    return flags
