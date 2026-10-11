"""Add photos Muse verified (keep verdicts) to colleges.json, only when every check passes (fix #32, Oct 11).
Inputs: Muse's verdict file (checksum-verified) and Commons metadata fetched today (credit, license, size).
Checks per photo: school has no photo now; Commons file exists; free license; not shared by another school;
jpg/png/webp at least 330px wide; and the photo guard passes. Everything else is held with a reason.
Usage: python3 -I ops/add_verified_photos.py <C-photo-verdicts-858.json> <commons-meta.json>"""
import json,re,sys,urllib.parse,collections,importlib.util,hashlib
SHA='202cbc93570f820b25d1ca72e2c0c73a542ce00a4201b041b677d331b08335c1'
raw_v=open(sys.argv[1],'rb').read(); assert hashlib.sha256(raw_v).hexdigest()==SHA,'verdicts checksum mismatch - stop'
V=json.loads(raw_v)['verdicts']
M=json.load(open(sys.argv[2])); titles={int(k):v for k,v in M['titles'].items()}; meta=M['meta']
spec=importlib.util.spec_from_file_location('pg','photo_guard.py'); pg=importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
p='colleges.json'; raw=open(p).read(); d=json.loads(raw); byU={c['unitid']:c for c in d['colleges']}
FREE=re.compile(r'^(cc[ -]by|cc0|cc-zero|public domain|pd|gfdl|attribution)',re.I)
added=[]; held=collections.defaultdict(list); usecount=collections.Counter(titles[v['unitid']] for v in V if v['verdict']=='keep')
for v in V:
    if v['verdict']!='keep': continue
    c=byU.get(v['unitid']); t=titles[v['unitid']]; m=meta.get(t)
    if not c: held['not in catalog'].append(v['unitid']); continue
    if c.get('photo'): held['already has a photo'].append(v['unitid']); continue
    if not m or m['missing'] or not m.get('url'): held['file not found on Commons'].append(v['unitid']); continue
    if usecount[t]>1: held['same file on 2+ schools'].append(v['unitid']); continue
    if not FREE.search(m['license'] or ''): held['license not free/unknown: '+(m['license'] or 'none')].append(v['unitid']); continue
    u=m['url'].split('?')[0]; ext=u.rsplit('.',1)[-1].lower()
    if ext not in ('jpg','jpeg','png','webp'): held['not a jpg/png: '+ext].append(v['unitid']); continue
    w=m['w'] or 0; size=960 if w>960 else 500 if w>500 else 330 if w>330 else None
    if not size: held['too small (<330px)'].append(v['unitid']); continue
    mm=re.match(r'https://upload\.wikimedia\.org/wikipedia/commons/([0-9a-f])/([0-9a-f]{2})/(.+)$',u)
    if not mm: held['unexpected file URL'].append(v['unitid']); continue
    name=mm.group(3); thumb=f"https://thumb.wikimedia.org/wikipedia/commons/thumb/{mm.group(1)}/{mm.group(2)}/{name}/{size}px-{name}"
    artist=re.sub(r'\s+',' ',m['artist']).strip() or 'Unknown author'
    c['photo']={'url':thumb,'credit':f"{artist[:80]} via Wikimedia Commons",'license':m['license'],'source':'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(t.replace(' ','_'))}
    added.append({'id':c['id'],'unitid':c['unitid'],'name':c['name'],'confidence':v['confidence'],'why':v['why'],'photo':c['photo']})
flags,warns=pg.check(d['colleges'],with_warnings=True); bids={i for b in flags for i in b[0].split('/')}
for a in list(added):
    if a['id'] in bids:
        del byU[a['unitid']]['photo']; added.remove(a); held['blocked by photo guard'].append(a['unitid'])
open(p,'w').write(json.dumps(d,ensure_ascii=False,separators=(',',':'))+('\n' if raw.endswith('\n') else ''))
aw=[w for w in warns if w[0] in {a['id'] for a in added}]
json.dump({'note':"Photos added from Muse's verification of the 858 held photos (keep verdicts): Commons file exists, free license, not shared, >=330px, passes the photo guard. Credit/license read from Commons on 2026-10-11.",'added':added,'held':dict(held),'guard_warnings_on_added':[list(w) for w in aw]},open('archive/added-photos-muse-858-2026-10-11.json','w'),indent=1,ensure_ascii=False)
print('added',len(added),dict(collections.Counter(a['confidence'] for a in added))); print({k:len(v) for k,v in held.items()}); print('guard warnings on added (not blocking):',len(aw))
