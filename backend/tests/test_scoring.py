"""Sanity tests: the PS's exact partial-credit case, tier ordering on the
synthetic corpus, parser robustness, calibration bounds, contract shape, chat.

Run: python -m pytest tests/ -v   (from backend/)
Reranker is disabled via env var to keep the suite fast; the bi-encoder still runs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("NXORA_RERANKER_ENABLED", "0")   # set BEFORE importing engine

import pytest

from jd_extract import extract_jd, load_taxonomy
from parser import parse_resume, extract_text
from matcher.keyword import keyword_match
from matcher.semantic import _calibrate, semantic_match_batch
from matcher.hybrid import blend

TAXONOMY = load_taxonomy()

JD_TEXT = """Junior Full Stack Developer Intern — TechNova Solutions

We are looking for a junior full stack developer intern.

Required skills:
- Strong JavaScript and modern React experience
- Node.js for server-side development
- MongoDB for data storage
- HTML and CSS fundamentals
- Experience building REST APIs
- Comfortable with Git version control

Nice to have:
- Docker, AWS, TypeScript, Jest

Responsibilities:
- Develop and maintain web application features
- Collaborate with the design team
"""

JD = extract_jd(JD_TEXT, TAXONOMY)


# ---------------------------------------------------------------- keyword

def test_ps_case_express_counts_as_node_partial():
    """The PS's exact case: 'Built REST APIs with Express and MongoDB' must give
    partial credit for Node.js (synonym Express) and full credit for MongoDB."""
    resume = parse_resume(
        b"Ananya Sharma\n\nSkills: JavaScript, React, HTML, CSS, Git\n\n"
        b"Projects:\nBuilt REST APIs with Express and MongoDB for a food-delivery app\n",
        "ananya.txt")
    kr = keyword_match(resume, JD, TAXONOMY)
    assert "node.js" in kr.partial          # synonym-only hit -> partial
    assert "mongodb" in kr.matched          # canonical, in Projects (strong section)
    assert "rest api" in kr.matched
    assert "node.js" not in kr.missing
    assert 0 < kr.score < 100


def test_no_false_positives():
    resume = parse_resume(
        b"Ravi Kumar\n\nExperience:\nConstructed reactive dashboards for marketing teams\n",
        "ravi.txt")
    kr = keyword_match(resume, JD, TAXONOMY)
    assert "react" not in kr.matched and "react" not in kr.partial   # 'reactive' != react
    assert "javascript" not in kr.matched


def test_terse_one_line_jd_still_extracts_skills():
    """A JD pasted as a single line must not be skipped as a 'title line'."""
    terse = ("Junior Full Stack Developer Intern. Required: JavaScript, React, "
             "Node.js, MongoDB, REST APIs, Git. Nice to have: Docker, AWS.")
    jd = extract_jd(terse, TAXONOMY)
    assert "react" in jd.required_skills
    assert "javascript" in jd.required_skills
    assert "docker" in jd.nice_skills
    assert len(jd.skill_requirements) >= 6


def test_listed_only_gets_lower_credit_than_demonstrated():
    """Same two skills, but demonstrated in Projects vs listed in a Skills line —
    the demonstrated resume must score higher (1.0 vs 0.85 credit per skill)."""
    demonstrated = parse_resume(
        b"A\n\nProjects:\nBuilt web apps with JavaScript and React\n", "a.txt")
    listed = parse_resume(
        b"B\n\nSkills: JavaScript, React\n", "b.txt")
    kd = keyword_match(demonstrated, JD, TAXONOMY)
    kl = keyword_match(listed, JD, TAXONOMY)
    assert "javascript" in kd.matched and "javascript" in kl.matched
    assert kd.score > kl.score   # section-aware credit, not list membership


def jd_skill_credit(kr, skill):
    return 1.0 if skill in kr.matched else 0.6 if skill in kr.partial else 0.0


# ---------------------------------------------------------------- parser

def test_parser_survives_garbage():
    for garbage in [b"\x00\xff\xfe\x01\x02", b"", b"PK\x03\x04broken",
                    b"%PDF-1.4 not really a pdf"]:
        text, _ = extract_text(garbage, "x.pdf")     # must not raise
        assert isinstance(text, str)
        rd = parse_resume(garbage, "x.pdf")
        assert rd.sections                # always at least one section


def test_parser_sections():
    rd = parse_resume(b"Jane Doe\n\nSkills: python, sql\n\nExperience:\nWrote ETL jobs\n",
                      "jane.txt")
    names = [s.name for s in rd.sections]
    assert "Skills" in names and "Experience" in names


# ---------------------------------------------------------------- calibration / blend

def test_calibration_bounds():
    assert _calibrate(0.0) == 0.0
    assert _calibrate(1.0) == 100.0
    assert 0.0 <= _calibrate(0.5) <= 100.0


def test_blend_bounds():
    class _Kw:
        score = 0.0
    class _Sem:
        score = 100.0
    assert blend(_Kw(), _Sem()) == 50.0


# ---------------------------------------------------------------- end-to-end ordering

SYNTH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@pytest.mark.skipif(not os.path.isdir(SYNTH_DIR), reason="synthetic data not generated")
def test_tier_ordering_on_synth_corpus():
    """Strong resumes must outscore partial, partial must outscore weak (means)."""
    import json
    with open(os.path.join(SYNTH_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    resumes = [parse_resume(open(os.path.join(SYNTH_DIR, m["file"]), "rb").read(), m["file"])
               for m in manifest]
    jd_full = open(os.path.join(SYNTH_DIR, "jd.txt"), encoding="utf-8").read()
    jd = extract_jd(jd_full, TAXONOMY)

    kws = [keyword_match(r, jd, TAXONOMY) for r in resumes]
    sems = semantic_match_batch(resumes, jd, use_reranker=False)
    scores = {m["file"]: blend(k, s) for m, k, s in zip(manifest, kws, sems)}

    tier_mean = lambda tier: sum(scores[m["file"]] for m in manifest if m["tier"] == tier) / \
                             max(1, sum(1 for m in manifest if m["tier"] == tier))
    strong, partial, weak = tier_mean("strong"), tier_mean("partial"), tier_mean("weak")
    assert strong > partial > weak, f"ordering broken: {strong} / {partial} / {weak}"
    # Meaningful spread: the rubric wants visible separation, not everyone at 71.
    assert strong - weak >= 15.0, f"spread too small: {strong - weak}"


# ---------------------------------------------------------------- API contract

def _client():
    from fastapi.testclient import TestClient
    import main as main_module
    return TestClient(main_module.app)


def test_analyze_contract_shape():
    client = _client()
    files = [("resumes", ("a.txt", b"Ananya Sharma\n\nProjects:\n"
                                      b"Built REST APIs with Express and MongoDB\n"
                                      b"Skills: JavaScript, React, HTML, CSS, Git\n", "application/pdf")),
             ("resumes", ("b.txt", b"Ravi Kumar\n\nExperience:\nManaged social media campaigns\n", "application/pdf"))]
    r = client.post("/api/analyze", data={"jd_text": JD_TEXT}, files=files)
    assert r.status_code == 200, r.text
    body = r.json()

    assert set(body) >= {"jd", "ranking", "bias_flags", "meta"}
    assert set(body["jd"]) >= {"title", "company", "required_skills", "nice_skills"}
    for c in body["ranking"]:
        assert set(c) >= {"rank", "name", "file", "overall_score", "keyword_score",
                          "semantic_score", "matched_skills", "partial_skills",
                          "missing_skills", "evidence", "explanation"}
        assert set(c["evidence"]) >= {"sections", "highlight"}
        assert 0.0 <= c["overall_score"] <= 100.0
    assert body["ranking"][0]["explanation"] is not None
    assert [c["rank"] for c in body["ranking"]] == list(range(1, len(body["ranking"]) + 1))
    assert body["ranking"][0]["overall_score"] >= body["ranking"][-1]["overall_score"]
    assert body["meta"]["resumes_processed"] == 2
    assert body["meta"]["elapsed_ms"] > 0


def test_analyze_rejects_missing_jd():
    client = _client()
    r = client.post("/api/analyze",
                    files=[("resumes", ("a.txt", b"some resume", "application/pdf"))])
    assert r.status_code == 400


def test_analyze_rejects_no_resumes():
    client = _client()
    r = client.post("/api/analyze", data={"jd_text": JD_TEXT})
    assert r.status_code == 400


def test_duplicate_resumes_deduped_by_email():
    """Same resume uploaded twice (e.g. .txt and .pdf of the same person) with the
    same email -> one entry in the ranking, the duplicate reported in meta."""
    client = _client()
    resume = (b"Ananya Sharma\nananya.sharma@email.com\n\nProjects:\n"
              b"Built REST APIs with Express and MongoDB\nSkills: JavaScript, React, Git\n")
    files = [("resumes", ("ananya.txt", resume, "text/plain")),
             ("resumes", ("Ananya_Sharma_resume.pdf", resume, "text/plain"))]
    r = client.post("/api/analyze", data={"jd_text": JD_TEXT}, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["duplicates_removed"] == 1
    assert len(body["ranking"]) == 1
    assert body["meta"]["resumes_processed"] == 1


# ---------------------------------------------------------------- quality flags

def test_quality_flags_stuffing_and_repetition():
    from quality import quality_flags
    # Skills-wall resume: 7 matched skills, all listed-only, none demonstrated.
    stuffed = parse_resume(
        b"Stuffer McStuffle\n\nSkills: JavaScript, React, Node.js, MongoDB, Git, Docker, AWS\n",
        "s.txt")
    kr = keyword_match(stuffed, JD, TAXONOMY)
    flags = quality_flags(stuffed, kr, JD, TAXONOMY)
    assert any(f["flag"] == "keyword_stuffing_suspected" for f in flags)

    # Same skills demonstrated in Projects -> no stuffing flag.
    demonstrated = parse_resume(
        b"Real Dev\n\nProjects:\nBuilt apps with JavaScript, React, Node.js, MongoDB, Git\n",
        "d.txt")
    kr2 = keyword_match(demonstrated, JD, TAXONOMY)
    assert not any(f["flag"] == "keyword_stuffing_suspected"
                   for f in quality_flags(demonstrated, kr2, JD, TAXONOMY))

    # A skill repeated 6+ times -> repetition flag.
    spammy = parse_resume(
        b"Spam Sam\n\nSkills: React\n\nProjects:\nReact app. React widgets. React dashboards. "
        b"React tests. React fixes. React more React.\n", "sp.txt")
    kr3 = keyword_match(spammy, JD, TAXONOMY)
    flags3 = quality_flags(spammy, kr3, JD, TAXONOMY)
    assert any(f["flag"] == "repetition_detected" and "react" in f["detail"] for f in flags3)


def test_chat_deterministic_answers():
    client = _client()
    analysis = {"ranking": [
        {"rank": 1, "name": "Ananya Sharma", "overall_score": 88.0, "keyword_score": 90.0,
         "semantic_score": 86.0, "matched_skills": ["react", "node.js"],
         "partial_skills": [], "missing_skills": [],
         "evidence": {"highlight": "Built REST APIs with Express and MongoDB"}},
        {"rank": 2, "name": "Ravi Kumar", "overall_score": 40.0, "keyword_score": 35.0,
         "semantic_score": 45.0, "matched_skills": ["react"], "partial_skills": [],
         "missing_skills": ["node.js"], "evidence": {"highlight": ""}},
    ]}
    r = client.post("/api/chat", json={"question": "Why is candidate 1 above candidate 2?",
                                       "analysis": analysis})
    assert r.status_code == 200
    answer = r.json()["answer"]
    assert "Ananya" in answer and "Ravi" in answer
    assert "48.0" in answer                       # the overall delta
    assert "node.js" in answer                    # the skill gap
    # Same question -> same answer (deterministic, no LLM).
    r2 = client.post("/api/chat", json={"question": "Why is candidate 1 above candidate 2?",
                                        "analysis": analysis})
    assert r2.json()["answer"] == answer
