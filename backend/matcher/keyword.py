"""Keyword track: taxonomy matching with location-aware credit.

Credits (per GAMEPLAN §5 + approved upgrades):
  - canonical skill term found in an Experience/Projects section  -> 1.0  (matched)
  - canonical term found only in Skills/other sections           -> 0.85 (matched, "listed only")
  - synonym-only hit (e.g. resume says "Express", JD says Node.js)-> 0.60 (partial)
  - no hit                                                       -> 0    (missing, required only)
Score = 100 * sum(weight * credit) / sum(weight) over SKILL requirements only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from jd_extract import JdData, _skill_regexes
from parser import ResumeData

DIRECT_CREDIT = 1.0
LISTED_CREDIT = 0.85     # exact skill term, but only in a skills list — not demonstrated
SYNONYM_CREDIT = 0.6
STRONG_SECTIONS = ("Experience", "Projects")


@dataclass
class KeywordResult:
    score: float                                       # 0-100
    matched: list[str] = field(default_factory=list)   # direct (canonical) hits
    partial: list[str] = field(default_factory=list)   # synonym-only hits
    missing: list[str] = field(default_factory=list)   # required skills with no hit
    skill_evidence: dict[str, str] = field(default_factory=dict)  # skill -> best resume line
    listed_only: list[str] = field(default_factory=list)  # matched but only in skills lists


def keyword_match(resume: ResumeData, jd: JdData, taxonomy: dict[str, list[str]]) -> KeywordResult:
    regexes = _skill_regexes(taxonomy)
    total_weight = 0.0
    total_credit = 0.0
    result = KeywordResult(score=0.0)

    for req in jd.skill_requirements:
        if req.skill not in regexes:
            continue
        can_re, syn_re = regexes[req.skill]
        direct_strong = direct_weak = False
        syn_hit = False
        best_line = ""
        for section in resume.sections:
            if not section.text:
                continue
            if can_re.search(section.text):
                if section.name in STRONG_SECTIONS:
                    direct_strong = True
                else:
                    direct_weak = True
                for line in section.text.splitlines():
                    if can_re.search(line) and len(best_line) < len(line.strip()) < 200:
                        best_line = line.strip()
            elif syn_re.search(section.text) and not direct_strong and not direct_weak:
                syn_hit = True
                for line in section.text.splitlines():
                    if syn_re.search(line) and len(best_line) < len(line.strip()) < 200:
                        best_line = line.strip()

        if direct_strong:
            credit = DIRECT_CREDIT
            result.matched.append(req.skill)
        elif direct_weak:
            credit = LISTED_CREDIT
            result.matched.append(req.skill)
            result.listed_only.append(req.skill)
        elif syn_hit:
            credit = SYNONYM_CREDIT
            result.partial.append(req.skill)
        else:
            credit = 0.0
            if req.kind == "required":
                result.missing.append(req.skill)

        if best_line:
            result.skill_evidence[req.skill] = best_line
        total_weight += req.weight
        total_credit += req.weight * credit

    result.score = round(100.0 * total_credit / total_weight, 1) if total_weight else 0.0
    return result
