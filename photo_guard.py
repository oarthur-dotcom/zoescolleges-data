#!/usr/bin/env python3
"""Photo guard (Oct 11). Blocks a catalog photo that is very likely the wrong picture:
  - the filename names a foreign place the school isn't in (New Zealand, London, Bangkok...),
  - the filename says it isn't a campus (aircraft, press conference, yearbook, logo, highway, police...),
  - the same photo file is attached to two or more schools (how three Bethels and two Andersons got
    one picture).
Softer signals (another US state or another school's name in the filename) are printed as "look at"
warnings but don't block, because many real campus photos mention a street or building with those words.
Known-good exceptions live in photo-guard-allow.json (file name + school ids + reason).
Used by validate_catalog.py, so CI and the pre-deploy check both refuse a catalog with a new bad photo.
"""
import json, re, sys, os, urllib.parse, collections
FOREIGN = ("new zealand|australia|nsw|england|london|scotland|glasgow|ireland|dublin|germany|berlin|munich|france|paris|italy|rome|"
  "spain|madrid|nigeria|kenya|ghana|philippines|manila|china|beijing|shanghai|japan|tokyo|korea|seoul|india|delhi|mumbai|pakistan|"
  "toronto|ontario|quebec|vancouver|british columbia|mexico city|brazil|israel|jerusalem|prague|czech|netherlands|amsterdam|sweden|"
  "norway|denmark|finland|poland|russia|ukraine|turkey|egypt|south africa|singapore|hong kong|taiwan|vietnam|thailand|bangkok|"
  "indonesia|malaysia|switzerland|austria|belgium|portugal|greece").split("|")
NOTCAMPUS = ("boeing|fedex|aircraft|airplane|airliner|press conference|yearbook|first lady|melania|trump|obama|president bill|"
  "president joe|governor|senator|highway|interstate|exit sign|logo|wordmark|seal of|mascot|locator map|map of|coat of arms|flag of|"
  "portrait of|headshot|mugshot|protest|riot|crash|police|mural|soldiers|world war|wwi|pole vault|track meet|vs|versus|"
  "route|custom house|market street|secretary|hospital|clinic|hebrew|fema|sandbag|sandbagging|funeral|casket|flood").split("|")
STATES = {"AL":"alabama","AK":"alaska","AZ":"arizona","AR":"arkansas","CA":"california","CO":"colorado","CT":"connecticut","DE":"delaware",
  "FL":"florida","GA":"georgia","HI":"hawaii","ID":"idaho","IL":"illinois","IN":"indiana","IA":"iowa","KS":"kansas","KY":"kentucky",
  "LA":"louisiana","ME":"maine","MD":"maryland","MA":"massachusetts","MI":"michigan","MN":"minnesota","MS":"mississippi","MO":"missouri",
  "MT":"montana","NE":"nebraska","NV":"nevada","NH":"new hampshire","NJ":"new jersey","NM":"new mexico","NY":"new york",
  "NC":"north carolina","ND":"north dakota","OH":"ohio","OK":"oklahoma","OR":"oregon","PA":"pennsylvania","RI":"rhode island",
  "SC":"south carolina","SD":"south dakota","TN":"tennessee","TX":"texas","UT":"utah","VT":"vermont","VA":"virginia","WA":"washington",
  "WV":"west virginia","WI":"wisconsin","WY":"wyoming"}
# Other-institution phrases in a filename: "<Name> University", "University of <Name>", "<Name> College"
INST = re.compile(r"(university of [a-z]+(?: [a-z]+)?|[a-z]+ (?:university|college))")
GENERIC = {"the","of","and","at","state","community","campus","main","old","new","hall","building","library","center","st","saint"}
SAFE_PHRASES = ["new england", "beth israel", "indiana", "indian ", "jerome", "paris junior", "rome ga"]
HERE = os.path.dirname(os.path.abspath(__file__))
def words(u):
    p = urllib.parse.unquote(urllib.parse.urlparse(u).path).split("/")
    f = re.sub(r"^(lossy-page\d+-|lossless-page\d+-)?\d+px-", "", p[-1])
    if re.fullmatch(r"thumbnail(\.tif)?\.(jpe?g|png)", f, re.I) and len(p) > 2: f = p[-2]   # Commons thumbs of TIFF/PDF files
    t = " " + re.sub(r"[^a-z0-9]+", " ", f.lower()) + " "
    return f, t
def has(t, w): return re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", t) is not None
def photo_url(c):
    ph = c.get("photo"); return (ph or {}).get("url") if isinstance(ph, dict) else (ph or None)
def check(colleges, allow=None, with_warnings=False):
    allow = allow if allow is not None else json.load(open(os.path.join(HERE, "photo-guard-allow.json")))["allow"]
    ok_pairs = {(a["file"], i) for a in allow for i in a["ids"]}
    flags = []; warns = []; byfile = collections.defaultdict(list)
    for c in colleges:
        u = photo_url(c)
        if not u: continue
        f, t = words(u); own = " " + re.sub(r"[^a-z0-9]+", " ", (c.get("name", "") + " " + (c.get("city") or "")).lower()) + " "
        byfile[f].append(c)
        if (f, c["id"]) in ok_pairs: continue
        tt = t
        for s in SAFE_PHRASES: tt = tt.replace(" " + s.strip() + " ", " ")
        for w in FOREIGN:
            if has(tt, w) and not has(own, w): flags.append((c["id"], c["name"], "foreign place: " + w, f)); break
        for w in NOTCAMPUS:
            if has(t, w) and not has(own, w): flags.append((c["id"], c["name"], "not a campus photo: " + w, f)); break
        home = STATES.get(c.get("state", ""), "")
        tt2 = tt.replace(" west virginia ", " wv_state ") if home != "west virginia" else tt
        for code, st in STATES.items():
            name = "wv_state" if st == "west virginia" and home != "west virginia" else st
            if st == home or not has(tt2, name) or has(own, st): continue
            if st == "washington" and (has(tt2, "washington hall") or has(tt2, "george washington") or has(tt2, "washington and lee")): continue
            warns.append((c["id"], c["name"], f"other state in filename: {st} (school is in {c.get('state')})", f)); break
        ownw = set(own.split()) - GENERIC
        for m in INST.finditer(tt):
            phrase = m.group(1); key = set(phrase.split()) - GENERIC - {"university", "college"}
            if key and not (key & ownw): warns.append((c["id"], c["name"], "names another school: " + phrase, f)); break
    for f, cs in byfile.items():
        if len(cs) > 1 and not all((f, x["id"]) in ok_pairs for x in cs):
            flags.append(("/".join(x["id"] for x in cs), " + ".join(f"{x['name']} ({x.get('state','')})" for x in cs), f"same photo on {len(cs)} schools", f))
    return (flags, warns) if with_warnings else flags
if __name__ == "__main__":
    d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "colleges.json"))
    fl, wn = check(d["colleges"], with_warnings=True); print(f"photo guard: {len(fl)} blocked, {len(wn)} to look at (not blocking)")
    for x in fl: print("  BLOCK", x)
    for x in wn: print("  look ", x)
    sys.exit(1 if fl else 0)
