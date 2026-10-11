#!/usr/bin/env python3
"""Post-deploy verification (Oct 11). Read-only. Run right after a release; it replaces the manual checks.
  1. Waits (up to ~5 min) for zoescolleges.com to serve app origin/main's index.html.
  2. Every data file the site reads (catalog, campus feeds, net price, deadlines) is served by the CDN
     byte-for-byte equal to the data `live` branch (purges the CDN once if it's stale).
  3. Server files are not downloadable; security headers present.
  4. Functions refuse anonymous calls (zoe-ai, transcript-read, campus-pulse).
  5. A sample of 40 catalog photos actually load.
  6. Headless browser on phone + desktop: page loads with 0 JavaScript errors, no sideways scroll,
     no "-200%"/"NaN"/"undefined", no ZOE2027, no Niche.
Exit code 0 = all PASS. Usage: python3 ops/postdeploy_verify.py  (from zoescolleges-data)
"""
import hashlib, json, os, random, re, subprocess, sys, time, urllib.request
APP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "zoescolleges-app"))
DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "ZoesCollegesPostDeploy/1.0 (+https://zoescolleges.com)"}
SITE = "https://zoescolleges.com"
CDN = "https://cdn.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@live/"
FILES = ["colleges.json", "campus-feeds.json", "net-price-by-income.json", "deadlines-2026-27.json"]
def get(url, timeout=30, method="GET", headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)
    except Exception as e: return None, str(e).encode(), {}
def git(repo, *a, text=True): return subprocess.check_output(["git", "-C", repo, *a], text=text)
sha = lambda b: hashlib.sha256(b).hexdigest()[:12]
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (" — " + detail if detail else ""), flush=True)
for r in (APP, DATA): subprocess.run(["git", "-C", r, "fetch", "-q", "origin"], check=False)
# 1 site == main
want = git(APP, "show", "origin/main:index.html", text=False); mshort = git(APP, "rev-parse", "--short", "origin/main").strip()
for i in range(16):
    st, live, _ = get(SITE + "/")
    if st == 200 and sha(live) == sha(want): break
    time.sleep(20)
check("Live page = app main", st == 200 and sha(live) == sha(want), f"main@{mshort}, waited {i*20}s")
# 2 data files
lshort = git(DATA, "rev-parse", "--short", "origin/live").strip()
for f in FILES:
    try: exp = subprocess.check_output(["git", "-C", DATA, "show", f"origin/live:{f}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError: print(f"INFO {f} not on the live branch (not published yet)"); continue
    st, body, _ = get(CDN + f, 60)
    if sha(body) != sha(exp):
        get("https://purge.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@live/" + f); time.sleep(15); st, body, _ = get(CDN + f, 60)
    check(f"CDN {f} = live branch", sha(body) == sha(exp), f"live@{lshort}")
# 3 exposure + headers
exposed = [p for p in ("migration-001-core.sql", "netlify/functions/zoe-ai.mjs", "package.json", "tests/chance-test.mjs") if get(f"{SITE}/{p}")[0] == 200]
check("Server files not downloadable", not exposed, ", ".join(exposed) or "none")
_, _, h = get(SITE + "/", method="HEAD")
need = ["X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]
hl = {k.lower(): v for k, v in h.items()}
check("Security headers", all(n.lower() in hl for n in need), ", ".join(n for n in need if n.lower() not in hl) or "all four present")
# 4 functions refuse anonymous calls
for fn, method in (("zoe-ai", "POST"), ("transcript-read", "POST"), ("campus-pulse", "GET")):
    url = f"{SITE}/.netlify/functions/{fn}" + ("?id=sc-166683" if fn == "campus-pulse" else "")
    st, _, _ = get(url, 45, method=method, headers={"Origin": SITE, "Content-Type": "application/json"})
    check(f"{fn} refuses no-login", st == 401, f"HTTP {st}")
# 5 photos
try:
    cat = json.loads(git(DATA, "show", "origin/live:colleges.json", text=False))["colleges"]
    urls = [c["photo"]["url"] for c in cat if isinstance(c.get("photo"), dict) and c["photo"].get("url")]
    random.seed(int(time.time()) // 3600); sample = random.sample(urls, min(40, len(urls)))
    bad = []; limited = 0
    for u in sample:
        st, b, hh = get(u, 30)
        if st == 429: time.sleep(5); st, b, hh = get(u, 30)       # Wikimedia rate-limits this server, not real visitors
        if st == 429: limited += 1; continue
        if st != 200 or not (hh.get("Content-Type") or hh.get("content-type") or "").startswith("image"): bad.append((st, u[-60:]))
        time.sleep(1.0)
    checked = len(sample) - limited
    check("Photo sample loads", checked >= 10 and len(bad) <= 1, f"{checked-len(bad)}/{checked} ok" + (f", {limited} skipped (rate-limited here)" if limited else "") + (f"; failed {bad[:3]}" if bad else ""))
except Exception as e: check("Photo sample loads", False, str(e))
# 6 browser smoke test
js = r"""
import { chromium } from '/tmp/claude-0/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: false, args: ['--no-sandbox','--headless=new'] });
const out = [];
for (const [w,h] of [[390,844],[1440,900]]) {
  const p = await b.newPage({ viewport: { width: w, height: h } }); const errs = [];
  p.on('pageerror', e => errs.push(String(e).slice(0,200)));
  const r = await p.goto('https://zoescolleges.com/', { waitUntil: 'networkidle', timeout: 60000 }); await p.waitForTimeout(2500);
  const html = await p.content(); const text = await p.evaluate(() => document.body.innerText);
  out.push({ w, status: r.status(), errs, overflow: await p.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1),
    bad: /-200%|NaN|undefined/.test(text), zoe2027: html.includes('ZOE2027'), niche: /niche\.com/i.test(html) });
}
console.log(JSON.stringify(out)); await b.close();
"""
open("/tmp/postdeploy-smoke.mjs", "w").write(js)
try:
    o = json.loads(subprocess.run(["node", "/tmp/postdeploy-smoke.mjs"], capture_output=True, text=True, timeout=180).stdout.strip().splitlines()[-1])
    for x in o:
        check(f"Browser {x['w']}px", x["status"] == 200 and not x["errs"] and not x["overflow"] and not x["bad"] and not x["zoe2027"] and not x["niche"],
              f"status {x['status']}, errors {len(x['errs'])}, sideways scroll {x['overflow']}, bad text {x['bad']}, ZOE2027 {x['zoe2027']}, Niche {x['niche']}")
except Exception as e: check("Browser smoke test", False, f"could not run: {e}")
fails = [r for r in results if not r[1]]
print(f"\nPOST-DEPLOY: {'ALL PASS' if not fails else str(len(fails)) + ' FAILED'} ({len(results)} checks) · app main@{mshort} · data live@{lshort}")
sys.exit(1 if fails else 0)
