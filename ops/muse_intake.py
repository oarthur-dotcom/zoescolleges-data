"""Muse handoff intake check (Oct 11). Read-only. Codifies Obie's five handoff rules:
  1. Verify before you trust: SHA-256 + size of every file against MANIFEST.json. A checksum failure STOPS.
  2. Shape-check before merge: every file must match a known shape. Unknown/unexpected shape STOPS.
  3. Holding area always: this script never writes outside the report it prints / --log file.
  5. Log every transaction: prints a ready-to-paste log entry per file (downloaded, checksum, shape, records).
Usage: python3 -I ops/muse_intake.py <folder with MANIFEST.json and the downloaded files> [--log out.md]
Exit code: 0 = all files pass; 1 = STOP (checksum or shape failure, or a file missing).
"""
import json,hashlib,os,re,sys,datetime as dt

def is_int_key(k): return bool(re.fullmatch(r'\d+',k))
# name pattern -> (description, check(obj) -> (ok, detail))
def shape_deadlines(o):
    if not (isinstance(o,dict) and isinstance(o.get('schools'),list)): return False,'expected object with schools[]'
    bad=[s for s in o['schools'] if not (isinstance(s,dict) and isinstance(s.get('unitid'),int) and isinstance(s.get('rounds'),list))]
    if bad: return False,f'{len(bad)} schools missing unitid/rounds'
    rb=[r for s in o['schools'] for r in s['rounds'] if not {'round_key','date','source_url','confidence'}<=set(r)]
    if rb: return False,f'{len(rb)} rounds missing required keys'
    bd=[r['date'] for s in o['schools'] for r in s['rounds'] if r['date'] is not None and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(r['date']))]
    if bd: return False,f'{len(bd)} dates not YYYY-MM-DD'
    return True,f"{len(o['schools'])} schools, {sum(1 for s in o['schools'] for r in s['rounds'] if r['date'])} dated rounds"
def shape_schoollist(o):
    ok=isinstance(o,dict) and isinstance(o.get('schools'),list) and all(isinstance(s,dict) and isinstance(s.get('unitid'),int) for s in o['schools'])
    return ok,(f"{len(o['schools'])} schools (input list)" if ok else 'expected object with schools[] of {unitid,...}')
def shape_verdicts(o):
    v=o.get('verdicts') if isinstance(o,dict) else None
    if not isinstance(v,list): return False,'expected object with verdicts[]'
    bad=[x for x in v if not (isinstance(x,dict) and isinstance(x.get('unitid'),int) and x.get('verdict') in ('keep','remove','replace'))]
    return (not bad),(f'{len(v)} verdicts' if not bad else f'{len(bad)} verdicts missing unitid or keep/remove/replace')
def shape_photos(o):
    if not isinstance(o,list): return False,'expected array'
    bad=[x for x in o if not (isinstance(x,dict) and isinstance(x.get('unitid'),int) and 'verdict' in x and 'photo_url' in x)]
    return (not bad),(f'{len(o)} photo records' if not bad else f'{len(bad)} records missing unitid/verdict/photo_url')
def shape_catalog_part(o):
    if not isinstance(o,dict) or not o: return False,'expected unitid-keyed object'
    if not all(is_int_key(k) for k in o): return False,'keys are not all unitids'
    bad=[k for k,r in o.items() if not (isinstance(r,dict) and str(r.get('unitid'))==k and r.get('name'))]
    return (not bad),(f'{len(o)} schools keyed by unitid' if not bad else f'{len(bad)} records whose unitid != key or no name')
def shape_dictionary(o):
    ok=isinstance(o,dict) and isinstance(o.get('fields'),dict) and 'key' in o
    return ok,(f"{len(o['fields'])} fields documented" if ok else 'expected {key, fields{}}')
def shape_feeds(o):
    S=o.get('schools') if isinstance(o,dict) else None
    if isinstance(S,dict): S=[dict(v,unitid=int(k)) if is_int_key(k) else v for k,v in S.items()]
    if not isinstance(S,list): return False,'expected schools as array or unitid-keyed object'
    bad=[s for s in S if not (isinstance(s,dict) and isinstance(s.get('unitid'),int))]
    return (not bad),(f'{len(S)} schools' if not bad else f'{len(bad)} entries without unitid')
def shape_markdown(b): return (len(b)>0),f'{len(b)} bytes of text'
SHAPES=[(r'^00-.*\.md$','report',None),(r'^B-deadlines-schoollist.*\.json$','deadline input list',shape_schoollist),(r'^B-deadlines.*\.json$','deadlines',shape_deadlines),
        (r'^C-photo-verdicts.*\.json$','photo verdicts',shape_verdicts),(r'^C-photos.*\.json$','photo hunt',shape_photos),(r'^D-catalog-unitid-part\d+-of-\d+\.json$','catalog part',shape_catalog_part),
        (r'^D-field-dictionary.*\.json$','field dictionary',shape_dictionary),(r'^E-campus-feeds.*\.json$','campus feeds',shape_feeds)]

def main(folder, logpath=None):
    m=json.load(open(os.path.join(folder,'MANIFEST.json')))
    now=dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines=[f'### Muse intake check · {now} · manifest made {m.get("made_at","?")}']
    stop=False; warn=False
    for f in m.get('files',[]):
        name=f['name']; p=os.path.join(folder,name)
        if not os.path.exists(p): lines.append(f'- **{name}**: NOT DOWNLOADED'); stop=True; continue
        b=open(p,'rb').read(); h=hashlib.sha256(b).hexdigest()
        if h!=f.get('sha256'): lines.append(f'- **{name}**: CHECKSUM FAIL (got {h[:12]}…, manifest {str(f.get("sha256"))[:12]}…). STOP: tell Obie, do not read or use.'); stop=True; continue
        size_note='' if len(b)==f.get('size_bytes') else f' (manifest size {f.get("size_bytes")} is stale; file is {len(b)}, hash matches)'
        if size_note: warn=True
        kind=next(((d,fn) for pat,d,fn in SHAPES if re.match(pat,name)),None)
        if not kind: lines.append(f'- **{name}**: checksum PASS{size_note}; UNKNOWN FILE TYPE. STOP: ask before using.'); stop=True; continue
        desc,fn=kind
        if fn is None: ok,detail=shape_markdown(b)
        else:
            try: o=json.loads(b)
            except Exception as e: lines.append(f'- **{name}**: checksum PASS; NOT VALID JSON ({e}). STOP.'); stop=True; continue
            ok,detail=fn(o)
        rc=f.get('record_count')
        if ok and rc is not None and fn is not None:
            n=int(re.match(r'\d+',detail).group()) if re.match(r'\d+',detail) else None
            if n is not None and n!=rc: detail+=f' (manifest says {rc} records)'; warn=True
        lines.append(f'- **{name}** ({desc}, built by {f.get("built_by","?")}): downloaded {len(b):,} bytes; checksum PASS{size_note}; shape {"PASS" if ok else "FAIL"}: {detail}.' + ('' if ok else ' STOP: ask Muse, never reshape to fit.'))
        if not ok: stop=True
    extra=sorted(set(os.listdir(folder))-{f['name'] for f in m.get('files',[])}-{'MANIFEST.json'})
    if extra: lines.append(f'- Files in the folder but not in the manifest (not checked, not used): {", ".join(extra)}'); warn=True
    lines.append(f'- **Result: {"STOP" if stop else ("PASS with notes" if warn else "PASS")}.** Nothing has been merged; holding area only. Obie approves before anything reaches the site.')
    out='\n'.join(lines); print(out)
    if logpath: open(logpath,'a').write(out+'\n')
    return 1 if stop else 0
if __name__=='__main__':
    a=sys.argv[1:]; lp=None
    if '--log' in a: i=a.index('--log'); lp=a[i+1]; a=a[:i]+a[i+2:]
    sys.exit(main(a[0],lp))
