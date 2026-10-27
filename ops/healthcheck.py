#!/usr/bin/env python3
"""Zoe's Colleges health check. Read-only. Run before and after every fix.
Usage: python3 ops/healthcheck.py  (from zoescolleges-data; expects ../zoescolleges-app)"""
import hashlib, json, os, re, subprocess, sys, time, urllib.request
APP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "zoescolleges-app"))
DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "ZoesCollegesHealth/1.0"}
def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
    except Exception as e: return None, str(e).encode()
def git(repo, *a): return subprocess.check_output(["git", "-C", repo, *a], text=True).strip()
def sha(b): return hashlib.sha256(b).hexdigest()[:12]
res = {"checks": [], "ok": True}
def check(name, ok, detail):
    res["checks"].append({"name": name, "ok": ok, "detail": detail}); res["ok"] &= bool(ok)
    print(("PASS " if ok else "FAIL ") + name + " — " + detail)
    if not ok and os.environ.get("GITHUB_ACTIONS"):   # annotation: GitHub's failure email then says which check failed and why
        print(f"::error title={name.replace(':', ' ').replace(',', ' ')}::{detail.replace('%', '%25').replace(chr(10), ' ')}")
for r in (APP, DATA): subprocess.run(["git", "-C", r, "fetch", "-q", "--all", "--prune"], check=False)
# 1 live site == app origin/main
st, live = get("https://zoescolleges.com/")
main_html = subprocess.check_output(["git", "-C", APP, "show", "origin/main:index.html"])
main_sha = git(APP, "rev-parse", "--short", "origin/main")
check("Site up", st == 200, f"HTTP {st}")
check("Live site == app main", sha(live) == sha(main_html), f"live {sha(live)} vs main@{main_sha} {sha(main_html)}")
m = re.search(rb'CATALOG_URL\s*=\s*"([^"]+)"', live); cat_url = m.group(1).decode() if m else None
_ref = re.search(rb'const DATA_REF = "([0-9a-f]{7,40})"', live)   # #37: pinned data release
if _ref:
    _r = _ref.group(1).decode(); cat_url = f"https://cdn.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@{_r}/colleges.json"
    check("Site reads approved data release", git(DATA, "rev-parse", "origin/live").startswith(_r), f"DATA_REF {_r}")
else:
    check("Site reads approved catalog branch", bool(cat_url and "@live/" in cat_url), str(cat_url))
# 2 live catalog == data origin/live and healthy
# The CDN has brief hiccups (Oct 14 and Oct 21 2026: a timeout or error page instead of the 3.5 MB catalog),
# so a mismatch is read again up to 3 times over about a minute before it counts as a failure.
live_file = subprocess.check_output(["git", "-C", DATA, "show", "origin/live:colleges.json"])
live_sha = git(DATA, "rev-parse", "--short", "origin/live")
for i in range(3):
    st, cat = get(cat_url or "", 60)
    if sha(cat) == sha(live_file): break
    if i < 2: time.sleep(20)
check("CDN catalog == data live branch", sha(cat) == sha(live_file), f"cdn {sha(cat)} vs live@{live_sha} {sha(live_file)}" + ("" if sha(cat) == sha(live_file) else f" (CDN gave HTTP {st}, {len(cat)} bytes, 3 tries)"))
try:
    c = json.loads(cat)["colleges"]
    cov = {k: sum(1 for x in c if x.get(k)) for k in ("scorecard", "photo", "ipeds", "lifestyle")}
    check("Catalog coverage", len(c) >= 3180 and cov["scorecard"] >= 3180 and cov["photo"] >= 1300, f"n={len(c)} {cov}")
except Exception as e: check("Catalog coverage", False, f"parse error {e}")
# 3 Supabase auth settings (public endpoint)
cfg = open(os.path.join(APP, "supabase-config.js")).read()
u = re.search(r"https://[a-z0-9]+\.supabase\.co", cfg); k = re.search(r"(eyJ[\w.-]+|sb_publishable_[\w-]+)", cfg)
if u and k:
    req = urllib.request.Request(u.group(0) + "/auth/v1/settings", headers={**UA, "apikey": k.group(0)})
    try:
        s = json.load(urllib.request.urlopen(req, timeout=20))
        print(f"INFO Supabase auth: signup_disabled={s.get('disable_signup')} email_autoconfirm={s.get('mailer_autoconfirm')}")
        res["supabase"] = {"disable_signup": s.get("disable_signup"), "mailer_autoconfirm": s.get("mailer_autoconfirm")}
    except Exception as e: check("Supabase reachable", False, str(e))
# 4 functions respond (no AI call made)
for fn in ("zoe-ai", "transcript-read"):
    st, _ = get(f"https://zoescolleges.com/.netlify/functions/{fn}")
    if st is None: st, _ = get(f"https://zoescolleges.com/.netlify/functions/{fn}", 45)  # cold start retry
    check(f"Function {fn} responds", st is not None and st < 500, f"HTTP {st} to GET (no AI call)")
# 4b exposure + headers (report only)
exp=[f for f in ("migration-001-core.sql","netlify/functions/zoe-ai.mjs","package.json") if get("https://zoescolleges.com/"+f)[0]==200]
print("INFO server files downloadable from the site:", exp or "none")
try:
    hdr=urllib.request.urlopen(urllib.request.Request("https://zoescolleges.com/",headers=UA,method="HEAD"),timeout=20).headers
    print("INFO security headers:", {k:hdr.get(k) for k in ("X-Frame-Options","X-Content-Type-Options","Referrer-Policy","Permissions-Policy")})
except Exception as e: print("INFO headers check failed", e)
res["exposed_files"]=exp
# 5 branch inventory
inv = {}
for name, r in (("app", APP), ("data", DATA)):
    br = [b.strip() for b in git(r, "branch", "-r", "--format=%(refname:short)").splitlines() if "HEAD" not in b]
    inv[name] = {b: git(r, "rev-list", "--left-right", "--count", f"origin/main...{b}").replace("\t", " behind/ahead ") for b in br}
print("INFO branches:", json.dumps(inv, indent=1)); res["branches"] = inv
res["app_main"] = main_sha; res["data_live"] = live_sha
print("OVERALL:", "HEALTHY" if res["ok"] else "PROBLEMS FOUND")
json.dump(res, open("/tmp/claude-0/last-health.json", "w"), indent=1)
sys.exit(0 if res["ok"] else 1)
