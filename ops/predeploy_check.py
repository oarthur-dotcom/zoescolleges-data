#!/usr/bin/env python3
"""Run on an APPROVED branch right before it goes live. Read-only.
Blocks anything that could overwrite newer work or good data.
Usage: python3 ops/predeploy_check.py app|data <branch>"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPOS = {"app": os.path.join(HERE, "..", "..", "zoescolleges-app"), "data": os.path.join(HERE, "..")}
which, branch = sys.argv[1], sys.argv[2]; R = os.path.abspath(REPOS[which])
def git(*a): return subprocess.check_output(["git", "-C", R, *a], text=True).strip()
fails, notes = [], []
subprocess.run(["git", "-C", R, "fetch", "-q", "origin"], check=True)
ref = f"origin/{branch}"
base = "origin/live" if which == "data" else "origin/main"   # what is live right now
# 1. Branch must contain everything currently live -> can't overwrite newer work
if subprocess.run(["git", "-C", R, "merge-base", "--is-ancestor", base, ref]).returncode != 0:
    fails.append(f"{branch} does not contain current live {base} ({git('rev-parse','--short',base)}). Deploying it would overwrite newer work. Rebase first.")
files = git("diff", "--name-only", f"{base}...{ref}").splitlines()
notes.append(f"changed files vs live: {files}")
notes.append("diffstat: " + git("diff", "--shortstat", f"{base}...{ref}"))
# 2. Catalog: validator against what's live
if "colleges.json" in files:
    with tempfile.TemporaryDirectory() as t:
        new, old = os.path.join(t, "new.json"), os.path.join(t, "old.json")
        open(new, "wb").write(subprocess.check_output(["git", "-C", R, "show", f"{ref}:colleges.json"]))
        open(old, "wb").write(subprocess.check_output(["git", "-C", R, "show", f"{base}:colleges.json"]))
        # Use the validator (and photo guard) from the branch being deployed, not whatever is checked out here.
        arch = [f for f in git("ls-tree", "-r", "--name-only", ref, "archive").splitlines() if os.path.basename(f).startswith("removed-photos")]
        os.makedirs(os.path.join(t, "archive"), exist_ok=True)
        for f in ("validate_catalog.py", "photo_guard.py", "photo-guard-allow.json", *arch):
            try: open(os.path.join(t, f), "wb").write(subprocess.check_output(["git", "-C", R, "show", f"{ref}:{f}"], stderr=subprocess.DEVNULL))
            except subprocess.CalledProcessError: pass
        v = subprocess.run([sys.executable, os.path.join(t, "validate_catalog.py"), new, old], capture_output=True, text=True)
        notes.append("catalog validator:\n" + v.stdout.strip())
        if v.returncode: fails.append("catalog validator FAILED (would drop good data)")
        n, o = json.load(open(new))["colleges"], json.load(open(old))["colleges"]
        oi, ni = {x["id"]: x for x in o}, {x["id"]: x for x in n}
        gone = [i for i in oi if i not in ni]
        if gone: fails.append(f"{len(gone)} schools removed, e.g. {gone[:5]}")
        lost = [(i, k) for i in oi if i in ni for k in oi[i] if oi[i].get(k) not in (None, "", [], {}) and ni[i].get(k) in (None, "", [], {}) and k != "photo"]
        if lost: fails.append(f"{len(lost)} filled fields would become empty, e.g. {lost[:5]}")
        ph = [i for i in oi if i in ni and oi[i].get("photo") and not ni[i].get("photo")]
        if ph:
            listed = set()
            for f in git("ls-tree", "-r", "--name-only", ref, "archive").splitlines():
                if os.path.basename(f).startswith("removed-photos") and f.endswith(".json"):
                    try: listed |= {r["id"] for r in json.loads(subprocess.check_output(["git", "-C", R, "show", f"{ref}:{f}"]))["removed"]}
                    except Exception: pass
            unlisted = [i for i in ph if i not in listed]
            notes.append(f"NOTE {len(ph)} photos removed; {len(ph)-len(unlisted)} are in the branch's archived removal list")
            if unlisted: fails.append(f"{len(unlisted)} photos removed without being in an archived removal list, e.g. {unlisted[:5]}")
# 3. SQL: no data-destroying statements
for f in files:
    if f.endswith(".sql"):
        sql = subprocess.check_output(["git", "-C", R, "show", f"{ref}:{f}"], text=True)
        body = re.sub(r"--[^\n]*", "", sql)
        bad = re.findall(r"\b(delete\s+from|truncate|drop\s+table|drop\s+column|drop\s+schema|update\s+\w+[\w.]*\s+set)\b", body, re.I)
        if bad: fails.append(f"{f} contains data-changing statements {sorted(set(b.lower() for b in bad))} — needs explicit review + backup first")
        else: notes.append(f"{f}: policy/schema-only, no data-changing statements")
# 4. App: scripts still parse
if which == "app" and "index.html" in files:
    html = subprocess.check_output(["git", "-C", R, "show", f"{ref}:index.html"], text=True)
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t: t.write("\n;\n".join(scripts))
    ok = subprocess.run(["node", "--check", t.name], capture_output=True, text=True)
    if ok.returncode: fails.append("JS syntax error: " + ok.stderr[:300])
    else: notes.append("JS syntax OK")
    # Approval gate (#37): the app must read data either from @live, or from a pinned DATA_REF that is EXACTLY
    # the approved data `live` commit, and the functions' data-ref.mjs must match the page.
    m = re.search(r'const DATA_REF = "([0-9a-f]{7,40})"', html)
    if m:
        live = subprocess.check_output(["git", "-C", REPOS["data"], "rev-parse", "origin/live"], text=True).strip()
        if not live.startswith(m.group(1)): fails.append(f"page DATA_REF {m.group(1)} is not the approved data live commit {live[:7]}")
        else: notes.append(f"page reads data release {m.group(1)} = data live")
        try: fn = subprocess.check_output(["git", "-C", R, "show", f"{ref}:netlify/lib/data-ref.mjs"], text=True)
        except subprocess.CalledProcessError: fn = ""
        if f'DATA_REF = "{m.group(1)}"' not in fn: fails.append("netlify/lib/data-ref.mjs DATA_REF does not match the page")
    elif "@live/colleges.json" not in html: fails.append("app no longer reads catalog from @live or a pinned data release (approval gate removed)")
print(f"PRE-DEPLOY CHECK {which}:{branch} -> live {base}@{git('rev-parse','--short',base)}")
for n in notes: print("  " + n)
for f in fails: print("  BLOCK: " + f)
print("RESULT:", "SAFE TO DEPLOY" if not fails else "BLOCKED"); sys.exit(1 if fails else 0)
