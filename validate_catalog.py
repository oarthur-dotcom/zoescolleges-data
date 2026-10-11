#!/usr/bin/env python3
"""Fail if colleges.json would break the live app. Run before every push.
Checks the fields index.html reads, and blocks large coverage drops vs. the
previous commit (the Oct 10 incident dropped photos 1412 -> 0, stats 3180 -> 0)."""
import json, os, subprocess, sys
REQUIRED = ["id", "name", "state", "scorecard", "lifestyle"]
COVERAGE = ["scorecard", "photo", "ipeds", "lifestyle", "regularDeadline", "muse"]
def counts(d):
    c = d["colleges"]; return len(c), {k: sum(1 for x in c if x.get(k)) for k in COVERAGE}
PATH = sys.argv[1] if len(sys.argv) > 1 else "colleges.json"
d = json.load(open(PATH)); errs = []
for i, x in enumerate(d["colleges"]):
    miss = [k for k in REQUIRED if k not in x]
    if miss: errs.append(f"{x.get('id', i)} missing {miss}")
    if len(errs) > 10: break
ids = [x["id"] for x in d["colleges"]]
if len(ids) != len(set(ids)): errs.append("duplicate ids")
n, now = counts(d); print("now ", n, now)
try:
    prev = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else json.loads(subprocess.check_output(["git", "show", "HEAD~1:colleges.json"], stderr=subprocess.DEVNULL))
    pn, before = counts(prev); print("prev", pn, before)
    if n < pn * 0.95: errs.append(f"school count dropped {pn} -> {n}")
    for k in COVERAGE:
        if before[k] and now[k] < before[k] * 0.95: errs.append(f"'{k}' coverage dropped {before[k]} -> {now[k]}")
except subprocess.CalledProcessError: pass
# Photo guard (Oct 11): no photo from another country, no non-campus photo, no photo shared by two schools.
_pg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_guard.py")
if os.path.exists(_pg):
    import importlib.util
    _spec = importlib.util.spec_from_file_location("photo_guard", _pg); photo_guard = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(photo_guard)
    bad = photo_guard.check(d["colleges"])
    for b in bad[:20]: errs.append(f"photo guard: {b[1]} — {b[2]} ({b[3][:80]})")
    print("photo guard:", len(bad), "blocked")
if errs: print("FAIL:\n  " + "\n  ".join(errs)); sys.exit(1)
print("OK")
