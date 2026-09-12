"""One-off: end-to-end /api/analyze with reranker ON over the 18 synth resumes."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
import main

BACKEND = os.path.join(os.path.dirname(__file__), "..")
manifest = json.load(open(os.path.join(BACKEND, "data", "manifest.json"), encoding="utf-8"))
jd_text = open(os.path.join(BACKEND, "data", "jd.txt"), encoding="utf-8").read()

client = TestClient(main.app)
t0 = time.perf_counter()
files = [("resumes", (m["file"], open(os.path.join(BACKEND, "data", m["file"]), "rb").read(),
                      "application/octet-stream")) for m in manifest]
r = client.post("/api/analyze", data={"jd_text": jd_text}, files=files)
wall = time.perf_counter() - t0
assert r.status_code == 200, r.text[:500]
body = r.json()

print(f"wall={wall:.1f}s  api_elapsed={body['meta']['elapsed_ms']}ms  engine={body['meta']['engine']}")
print(f"JD: {body['jd']['title']} @ {body['jd']['company']}")
print(f"required={body['jd']['required_skills']}")
print(f"nice={body['jd']['nice_skills']}")
print(f"bias_flags={len(body['bias_flags'])}")
print(f"{'rank':<5}{'name':<22}{'tier':<9}{'overall':<9}{'kw':<7}{'sem':<7}band")
tier_of = {m["file"]: m["tier"] for m in manifest}
for c in body["ranking"]:
    print(f"{c['rank']:<5}{c['name'][:21]:<22}{tier_of.get(c['file'], '?'):<9}"
          f"{c['overall_score']:<9}{c['keyword_score']:<7}{c['semantic_score']:<7}{c['band']}")
scores = [c["overall_score"] for c in body["ranking"]]
print(f"\nspread: top={scores[0]} bottom={scores[-1]} range={scores[0] - scores[-1]:.1f}")

# Warm second call (models already loaded): the latency the demo will actually see.
t1 = time.perf_counter()
r2 = client.post("/api/analyze", data={"jd_text": jd_text}, files=files)
warm = time.perf_counter() - t1
assert r2.status_code == 200
print(f"warm call: {warm:.1f}s (api_elapsed={r2.json()['meta']['elapsed_ms']}ms)")

print(f"\nTop-1 explanation:\n{body['ranking'][0]['explanation']}")
print("\nTop-1 requirement evidence (req -> section/sim/line):")
for ev in body["ranking"][0]["requirement_evidence"][:12]:
    print(f"  [{ev['kind']:<14}] {ev['requirement'][:60]:<62} "
          f"{ev['section']:<11} {ev['similarity']:<7} {ev['line'][:55]}")

