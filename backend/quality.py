"""Candidate quality flags: honest-matching signals surfaced to the recruiter.

We never silently boost or penalize a score — we FLAG and let the recruiter
decide. Two cheap, high-signal heuristics:
  1. keyword_stuffing_suspected — most matched skills appear only in skills
     lists, never demonstrated in Experience/Projects.
  2. repetition_detected — a single JD skill repeated many times in the text.
"""
from __future__ import annotations

from jd_extract import JdData, _skill_regexes
from matcher.keyword import KeywordResult
from parser import ResumeData

LISTED_ONLY_RATIO = 0.7    # >=70% of matched skills listed-only -> flag
LISTED_ONLY_MIN_MATCHES = 5  # don't flag small evidence sets
REPEAT_THRESHOLD = 6       # same skill this many times -> flag


def quality_flags(resume: ResumeData, kw: KeywordResult, jd: JdData,
                  taxonomy: dict[str, list[str]]) -> list[dict]:
    flags: list[dict] = []

    n_matched = len(kw.matched)
    if n_matched >= LISTED_ONLY_MIN_MATCHES and \
            len(kw.listed_only) / n_matched >= LISTED_ONLY_RATIO:
        flags.append({
            "flag": "keyword_stuffing_suspected",
            "detail": (f"{len(kw.listed_only)}/{n_matched} matched skills appear only in "
                       f"skills lists, never demonstrated in experience or projects."),
        })

    regexes = _skill_regexes(taxonomy)
    for req in jd.skill_requirements:
        if req.skill not in regexes:
            continue
        can_re, syn_re = regexes[req.skill]
        n = len(can_re.findall(resume.full_text)) + len(syn_re.findall(resume.full_text))
        if n >= REPEAT_THRESHOLD:
            flags.append({
                "flag": "repetition_detected",
                "detail": f"'{req.skill}' appears {n} times in this resume.",
            })

    return flags
