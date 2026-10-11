#!/usr/bin/env python3
"""One-step rollback (Oct 11). Puts the live site and/or catalog back to a known-good version.
Non-destructive: it adds a NEW commit whose files equal the known-good commit (no force-push, no
history lost), pushes it fast-forward, purges the CDN, then runs ops/postdeploy_verify.py.
Default is a DRY RUN that only prints the plan. Nothing changes without --yes, and --yes is only
for when Obie has said "roll back".
Usage:
  python3 ops/rollback.py                       # dry run: show what would roll back to ops/known-good.json
  python3 ops/rollback.py --app --yes           # app main -> known-good app commit (Netlify redeploys)
  python3 ops/rollback.py --data --yes          # data live (and main) -> known-good data commit
  python3 ops/rollback.py --app --to <commit> --yes
Testing: --app-repo/--data-repo point at other clones (used by the rollback drill on throwaway repos).
"""
import argparse, json, os, subprocess, sys, tempfile, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--app", action="store_true"); ap.add_argument("--data", action="store_true")
ap.add_argument("--to"); ap.add_argument("--yes", action="store_true"); ap.add_argument("--no-verify", action="store_true")
ap.add_argument("--app-repo", default=os.path.abspath(os.path.join(HERE, "..", "..", "zoescolleges-app")))
ap.add_argument("--data-repo", default=os.path.abspath(os.path.join(HERE, "..")))
a = ap.parse_args()
good = json.load(open(os.path.join(HERE, "known-good.json")))
def git(repo, *x, **k): return subprocess.check_output(["git", "-C", repo, *x], text=True, **k).strip()
plans = []
if a.app or not (a.app or a.data): plans.append(("app", a.app_repo, ["main"], a.to if a.app and a.to else good["app"]["commit"]))
if a.data or not (a.app or a.data): plans.append(("data", a.data_repo, ["live", "main"], a.to if a.data and a.to else good["data"]["commit"]))
for kind, repo, branches, target in plans:
    git(repo, "fetch", "-q", "origin")
    tgt = git(repo, "rev-parse", "--verify", target + "^{commit}")
    for br in branches:
        cur = git(repo, "rev-parse", f"origin/{br}")
        if git(repo, "rev-parse", f"{cur}^{{tree}}") == git(repo, "rev-parse", f"{tgt}^{{tree}}"):
            print(f"[{kind}] {br}: already at {target[:7]}'s files — nothing to do"); continue
        changed = git(repo, "diff", "--name-only", cur, tgt).splitlines()
        print(f"[{kind}] {br}: {cur[:7]} -> files of {tgt[:7]} ({len(changed)} files differ: {changed[:6]}{'…' if len(changed)>6 else ''})")
        if not a.yes: continue
        msg = f"ROLLBACK {br} to {tgt[:7]} (files restored exactly; history kept)\n\nRun by ops/rollback.py on Obie's instruction."
        new = git(repo, "commit-tree", f"{tgt}^{{tree}}", "-p", cur, "-m", msg)
        subprocess.run(["git", "-C", repo, "push", "-q", "origin", f"{new}:refs/heads/{br}"], check=True)
        print(f"[{kind}] {br}: pushed {new[:7]}")
        if kind == "data" and br == "live" and repo == ap.get_default("data_repo"):   # never purge the real CDN during a drill
            for f in ("colleges.json", "campus-feeds.json", "net-price-by-income.json", "deadlines-2026-27.json"):
                try: urllib.request.urlopen("https://purge.jsdelivr.net/gh/oarthur-dotcom/zoescolleges-data@live/" + f, timeout=30).read()
                except Exception as e: print("  purge", f, "->", e)
if not a.yes: print("\nDRY RUN — nothing changed. Add --yes only after Obie says to roll back.")
elif not a.no_verify:
    sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "postdeploy_verify.py")]).returncode)
