"""Build visit-links.json: each school's official admissions office and application pages from IPEDS HD2023
(ADMINURL, APPLURL, WEBADDR). Matched by unitid. Usage: python3 -I visit_links_build.py <HD2023.csv> <colleges.json> <out.json>"""
import csv, json, sys, re
def clean(u):
    u=(u or "").strip()
    if not u or u in ("-2","-1",".") or " " in u: return None
    if not re.match(r"^https?://", u, re.I): u="https://"+u.lstrip("/")
    u=u.replace("http://","https://",1) if u.lower().startswith("http://") else u
    if not re.match(r"^https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/[^\s\"'<>]*)?$", u): return None
    return u
hd={}
for r in csv.DictReader(open(sys.argv[1],encoding="utf-8-sig",errors="replace")):
    hd[r["UNITID"]]={"admissions":clean(r.get("ADMINURL")),"apply":clean(r.get("APPLURL")),"site":clean(r.get("WEBADDR"))}
cat=json.load(open(sys.argv[2]))["colleges"]
out={}; n_adm=n_app=0
for c in cat:
    h=hd.get(str(c.get("unitid")))
    if not h: continue
    rec={k:v for k,v in (("admissions",h["admissions"]),("apply",h["apply"])) if v}
    if rec: out[c["id"]]=rec; n_adm+=("admissions" in rec); n_app+=("apply" in rec)
json.dump({"source":"IPEDS HD2023 (U.S. Dept. of Education): ADMINURL, APPLURL","built":"2026-10-11","schools":out},open(sys.argv[3],"w"),separators=(",",":"))
print(f"schools {len(cat)} matched {len(out)} admissions {n_adm} apply {n_app}")
