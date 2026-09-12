"""One-off: full engine over the REAL resume dataset (deduped by person name).

Checks: parser robustness on real pdf/docx/xml/txt/doc files, score spread across
a genuinely mixed-domain pool, and per-format parse warnings.
"""
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
import main
from parser import parse_resume
from jd_extract import extract_jd, load_taxonomy

BACKEND = os.path.join(os.path.dirname(__file__), "..")
REAL = os.path.join(BACKEND, "data", "real")

taxonomy = load_taxonomy()
jd_text = open(os.path.join(BACKEND, "data", "jd.txt"), encoding="utf-8").read()
jd = extract_jd(jd_text, taxonomy)
print("required:", jd.required_skills)
print("nice:", jd.nice_skills)

# ---- Parse every real file; dedupe same person (name) preferring pdf > docx > others.
priority = {".pdf": 0, ".docx": 1, ".doc": 2, ".xml": 3, ".txt": 4}
files = []
for root, _dirs, names in os.walk(REAL):
    for n in names:
        files.append(os.path.join(root, n))
print(f"real files found: {len(files)}")

parsed_by_name: dict[str, tuple[int, str, object]] = {}
warnings = Counter()
ext_counter = Counter()
for path in sorted(files):
    ext = os.path.splitext(path)[1].lower()
    ext_counter[ext] += 1
    try:
        with open(path, "rb") as f:
            rd = parse_resume(f.read(), os.path.basename(path))
    except Exception as e:
        warnings[f"hard-fail {ext}: {type(e).__name__}"] += 1
        continue
    if rd.parse_warning:
        warnings[rd.parse_warning[:60]] += 1
    key = rd.name.lower()
    prev = parsed_by_name.get(key)
    if prev is None or priority.get(ext, 9) < prev[0]:
        parsed_by_name[key] = (priority.get(ext, 9), os.path.basename(path), rd)

print(f"unique candidates after name-dedupe: {len(parsed_by_name)}")
print(f"file types: {dict(ext_counter)}")
print(f"parse warnings: {dict(warnings) if warnings else 'none'}")

# ---- Run /api/analyze on the deduped pool (API caps at 50; scores are
# fixed-calibrated so batches are directly comparable — merge and re-rank).
resumes = sorted(parsed_by_name.values(), key=lambda t: t[1])
client = TestClient(main.app)
all_entries = []
t0 = time.perf_counter()
for chunk_start in range(0, len(resumes), 50):
    chunk = resumes[chunk_start:chunk_start + 50]
    files_field = [("resumes", (name, open(os.path.join(REAL, name), "rb").read(),
                                "application/octet-stream"))
                   for _, name, _ in chunk]
    r = client.post("/api/analyze", data={"jd_text": jd_text}, files=files_field)
    assert r.status_code == 200, r.text[:500]
    all_entries.extend(r.json()["ranking"])
wall = time.perf_counter() - t0
all_entries.sort(key=lambda c: (-c["overall_score"], -c["keyword_score"], c["name"].lower()))
for i, c in enumerate(all_entries, 1):
    c["rank"] = i
body = {"ranking": all_entries, "meta": {"resumes_processed": len(all_entries)},
        "bias_flags": []}

print(f"\nwall={wall:.1f}s  processed={body['meta']['resumes_processed']}")
scores = [c["overall_score"] for c in body["ranking"]]
bands = Counter(c["band"] for c in body["ranking"])
print(f"spread: top={scores[0]} median={scores[len(scores)//2]} bottom={scores[-1]} "
      f"range={scores[0]-scores[-1]:.1f}")
print(f"bands: {dict(bands)}")
print(f"bias_flags: {[f['phrase'][:70] for f in body['bias_flags']]}")

print(f"\n{'rank':<5}{'name':<26}{'overall':<9}{'kw':<7}{'sem':<7}{'file':<34}warning")
for c in body["ranking"][:15]:
    print(f"{c['rank']:<5}{c['name'][:25]:<26}{c['overall_score']:<9}"
          f"{c['keyword_score']:<7}{c['semantic_score']:<7}{c['file'][:33]:<34}"
          f"{(c['parse_warning'] or '')[:30]}")
print("...")
for c in body["ranking"][-5:]:
    print(f"{c['rank']:<5}{c['name'][:25]:<26}{c['overall_score']:<9}"
          f"{c['keyword_score']:<7}{c['semantic_score']:<7}{c['file'][:33]:<34}"
          f"{(c['parse_warning'] or '')[:30]}")
