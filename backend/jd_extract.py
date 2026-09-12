"""JD extraction: raw JD text -> structured requirements.

The critical upstream module: the keyword track scores against `required_skills` /
`nice_skills`, the semantic track embeds one statement per requirement. Taxonomy-driven
(the SAME taxonomy used for resumes), so both sides of the match speak one vocabulary.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))

# Weight of a requirement in both scoring tracks. Skill weights mirror GAMEPLAN §5.
WEIGHT_REQUIRED = 3.0
WEIGHT_NICE = 1.0
WEIGHT_RESPONSIBILITY = 2.0

_NICE_MARKERS = re.compile(
    r"nice to have|good to have|bonus|a plus|\bplus\b|preferred|desirable|not required|optional", re.I)
_NICE_SECTION = re.compile(r"nice to have|good to have|bonus|preferred qualifications|a plus", re.I)
_REQUIRED_SECTION = re.compile(
    r"^(required skills?|must.?haves?|requirements?|responsibilities|role|what you.?ll do)\b", re.I)
_REQ_LINE_MARKER = re.compile(r"\b(required|must.?have)\b", re.I)
_CLAUSE_BREAK = re.compile(r"[.:;]")   # sentence punctuation between skill and nice-cue = new clause
_RESPONSIBILITY_VERBS = re.compile(
    r"\b(develop|build|design|create|maintain|write|collaborate|work|responsible|"
    r"integrate|implement|participate|ship|test|debug|query)\w*\b", re.I)
_META_LINE = re.compile(
    r"^(duration|stipend|salary|location|about|apply|contact|perks|benefits|eligib)\b", re.I)
_TITLE_SPLIT = re.compile(r"\s+[—–\-|:@]\s+")


def load_taxonomy(path: str | None = None) -> dict[str, list[str]]:
    with open(path or os.path.join(_HERE, "taxonomy.json"), encoding="utf-8") as f:
        return json.load(f)


def _skill_regexes(taxonomy: dict[str, list[str]]) -> dict[str, tuple[re.Pattern, re.Pattern]]:
    """canonical -> (canonical-only pattern, synonyms-only pattern). Word boundaries throughout."""
    out: dict[str, tuple[re.Pattern, re.Pattern]] = {}
    for canonical, synonyms in taxonomy.items():
        def word_pattern(terms: list[str]) -> re.Pattern:
            alts = sorted({re.escape(t) for t in terms if t}, key=len, reverse=True)
            # Optional simple plural so "REST APIs" hits canonical "rest api".
            return re.compile(r"(?i)(?<![a-z0-9])(" + "|".join(alts) +
                              r")(?:s|es)?(?![a-z0-9])")
        out[canonical] = (word_pattern([canonical]), word_pattern([s for s in synonyms if s != canonical]))
    return out


@dataclass
class Requirement:
    skill: str | None      # canonical taxonomy skill, or None for a generic responsibility
    statement: str         # the JD line the requirement came from (embedded by semantic track)
    weight: float
    kind: str              # "required" | "nice" | "responsibility"


@dataclass
class JdData:
    title: str
    company: str
    full_text: str
    requirements: list[Requirement]
    required_skills: list[str]
    nice_skills: list[str]

    @property
    def skill_requirements(self) -> list[Requirement]:
        return [r for r in self.requirements if r.skill is not None]


def _lines(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = re.sub(r"^[\s\-–—*•·>#]+", "", raw.strip()).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            out.append(line)
    return out


def _title_company(lines: list[str]) -> tuple[str, str]:
    title, company = "Untitled Role", "—"
    for line in lines[:3]:
        if re.search(r"intern|engineer|developer|analyst|designer|manager|scientist|specialist|architect", line, re.I):
            parts = _TITLE_SPLIT.split(line, maxsplit=1)
            title = parts[0].strip()
            if len(parts) > 1:
                company = parts[1].strip()
            break
    else:
        if lines:
            parts = _TITLE_SPLIT.split(lines[0], maxsplit=1)
            title = parts[0].strip()[:60]
            if len(parts) > 1:
                company = parts[1].strip()[:60]
    # Company fallback: "at <Something Capitalized>" anywhere early.
    if company == "—":
        m = re.search(r"\bat\s+([A-Z][\w&.]+(?:\s+[A-Z][\w&.]+)?)", "\n".join(lines[:8]))
        if m:
            company = m.group(1)
    return title, company


def _line_kind(line: str, start: int, end: int, mode: str) -> str:
    """Kind for a skill hit at line[start:end]: the nearest 'required'/'nice'
    marker BEFORE the hit wins; a nice-phrase trailing just AFTER the hit
    ("Docker is a plus") also means nice. Falls back to the section mode."""
    if mode == "nice":
        return "nice"
    nm = _NICE_MARKERS.search(line)
    rm = _REQ_LINE_MARKER.search(line)
    if nm and 0 <= nm.start() - end <= 30 and not _CLAUSE_BREAK.search(line[end:nm.start()]):
        return "nice"                        # trailing "... is a plus" — closest cue
    before_nice = nm.start() if nm and nm.start() < start else -1
    before_req = rm.start() if rm and rm.start() < start else -1
    if before_nice > before_req:          # nearest preceding marker is a nice marker
        return "nice"
    return "required"


def extract_jd(text: str, taxonomy: dict[str, list[str]] | None = None) -> JdData:
    taxonomy = taxonomy or load_taxonomy()
    regexes = _skill_regexes(taxonomy)
    lines = _lines(text)

    skill_kind: dict[str, str] = {}          # canonical -> "required" | "nice"
    skill_statement: dict[str, str] = {}     # canonical -> first JD line where it appears
    used_lines: set[int] = set()
    mode = "required"                        # section mode: flip on nice/required headers

    for i, line in enumerate(lines):
        line_mode = mode                 # kind fallback for THIS line
        if _NICE_SECTION.search(line):   # mode flips apply to FOLLOWING lines
            mode = "nice"
        elif _REQUIRED_SECTION.match(line):
            mode = "required"
        if i == 0 and len(line) <= 80:
            continue          # short title line: skills there belong to the title, not requirements

        # All canonical hits on this line with their spans, longest match first,
        # then greedily accept non-overlapping ones ("REST APIs" -> rest api, not api+rest api).
        hits: list[tuple[int, int, str]] = []
        for canonical, (can_re, syn_re) in regexes.items():
            if canonical in skill_kind:
                continue
            m = can_re.search(line) or syn_re.search(line)
            if m:
                hits.append((m.start(), m.end(), canonical))
        hits.sort(key=lambda h: (h[1] - h[0]), reverse=True)
        claimed: list[tuple[int, int]] = []
        for start, end, canonical in hits:
            if any(start < ce and end > cs for cs, ce in claimed):
                continue                     # overlaps an already-claimed span
            claimed.append((start, end))
            skill_kind[canonical] = _line_kind(line, start, end, line_mode)
            skill_statement[canonical] = line
            used_lines.add(i)

    requirements: list[Requirement] = []
    required_skills, nice_skills = [], []
    for canonical, kind in skill_kind.items():
        requirements.append(Requirement(
            skill=canonical, statement=skill_statement[canonical],
            weight=WEIGHT_REQUIRED if kind == "required" else WEIGHT_NICE, kind=kind))
        (required_skills if kind == "required" else nice_skills).append(canonical)

    # Generic responsibility statements (no detected skill, verb-driven, not meta lines).
    resp_count = 0
    for i, line in enumerate(lines):
        if resp_count >= 6 or i in used_lines or len(line) < 25:
            continue
        if _META_LINE.match(line) or not _RESPONSIBILITY_VERBS.search(line):
            continue
        requirements.append(Requirement(skill=None, statement=line,
                                        weight=WEIGHT_RESPONSIBILITY, kind="responsibility"))
        used_lines.add(i)
        resp_count += 1

    # Stable order: required skills, nice skills, then responsibilities.
    requirements.sort(key=lambda r: {"required": 0, "nice": 1, "responsibility": 2}[r.kind])

    title, company = _title_company(lines)
    return JdData(
        title=title, company=company, full_text=text, requirements=requirements,
        required_skills=required_skills, nice_skills=nice_skills,
    )
