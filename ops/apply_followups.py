"""Apply Muse's follow-up photo answers (fix #33, Oct 11).
Removes the 4 photos Muse and Claude agree are wrong and still live; adds the 3 held photos Muse
assigned to their rightful school (shared-file rulings), using Commons metadata read on Oct 11.
Mount Carmel and LeTourneau stay removed (Obie decides); nothing else changes.
Usage: python3 -I ops/apply_followups.py <C-followup-verdicts-2026-10-11.json> <commons-meta.json>"""
import json,sys,hashlib,re,urllib.parse,importlib.util
SHA='c7fbd0a2c37a80283c78c126cefe6567a563aac31b783f3bc25ffdf5987ea818'
raw_f=open(sys.argv[1],'rb').read(); assert hashlib.sha256(raw_f).hexdigest()==SHA,'follow-up checksum mismatch - stop'
F=json.loads(raw_f); M=json.load(open(sys.argv[2]))
p='colleges.json'; raw=open(p).read(); d=json.loads(raw); byU={c['unitid']:c for c in d['colleges']}
REMOVE={204006:'re-review: Muse remove',204015:'re-review: Muse remove',219046:'re-review: Muse remove',483124:'main vs online: ASU Digital is the online arm; main campus keeps the photo'}
rv={x['unitid']:x for x in F['unverifiable_reviews']}
for u in (204006,204015,219046): assert rv[u]['verdict']=='remove',u
assert any(483124 in m['remove'] for m in F['predetermined']['main_vs_online']['decisions'])
removed=[]
for u,why in REMOVE.items():
    c=byU[u]; assert c.get('photo'),f'{u} has no photo'
    removed.append({'id':c['id'],'unitid':u,'name':c['name'],'reason':why+(('; '+str(rv[u].get('why') or rv[u].get('reason') or '')) if u in rv else ''),'photo':c.pop('photo')})
ADD=[x for x in F['duplicate_adjudications'] if x.get('belongs_to_unitid')]
added=[]
for x in ADD:
    u=x['belongs_to_unitid']; c=byU[u]; assert not c.get('photo'),f'{u} already has a photo'
    t=M['titles'][str(u)]; m=M['meta'][t]; assert not m['missing'] and t.replace(' ','_').endswith(x['filename'].replace(' ','_')),(u,t)
    mm=re.match(r'https://upload\.wikimedia\.org/wikipedia/commons/([0-9a-f])/([0-9a-f]{2})/(.+)$',m['url']); name=mm.group(3)
    size=960 if m['w']>960 else 500
    c['photo']={'url':f"https://thumb.wikimedia.org/wikipedia/commons/thumb/{mm.group(1)}/{mm.group(2)}/{name}/{size}px-{name}",
                'credit':f"{re.sub(r'\s+',' ',m['artist']).strip()[:80]} via Wikimedia Commons",'license':m['license'],
                'source':'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(t.replace(' ','_'))}
    added.append({'id':c['id'],'unitid':u,'name':c['name'],'why':x['why'],'not_for':[r['unitid'] for r in x['removed_from']],'photo':c['photo']})
# ASU photo no longer shared: drop its allowlist entry
al=json.load(open('photo-guard-allow.json')); al['allow']=[a for a in al['allow'] if a['file']!='Asubiodesign.jpg']
open('photo-guard-allow.json','w').write(json.dumps(al,indent=1,ensure_ascii=False)+'\n')
spec=importlib.util.spec_from_file_location('pg','photo_guard.py'); pg=importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
flags,warns=pg.check(d['colleges'],with_warnings=True); bids={i for b in flags for i in b[0].split('/')}
assert not (bids & {a['id'] for a in added}),('guard blocks an added photo',flags)
open(p,'w').write(json.dumps(d,ensure_ascii=False,separators=(',',':'))+('\n' if raw.endswith('\n') else ''))
json.dump({'note':"Muse's follow-up answers (C-followup-verdicts-2026-10-11.json, sha c7fbd0a2...). Restore a removed photo by copying its 'photo' back.",
           'removed':removed,'kept_removed_for_obie':[{'unitid':204176,'name':'Mount Carmel College of Nursing','muse':'keep (college is on the hospital campus)','claude':'photo shows the hospital; left removed until Obie decides'},
           {'unitid':226231,'name':'LeTourneau University','muse':'keep (with caveat)','claude':'earthmoving equipment, not a campus view; left removed until Obie decides'}]},
          open('archive/removed-photos-followup-2026-10-11.json','w'),indent=1,ensure_ascii=False)
json.dump({'note':"Held shared-file photos assigned to their rightful school by Muse's duplicate rulings; Commons file, license and credit read Oct 11; photo guard passes.",'added':added},
          open('archive/added-photos-followup-2026-10-11.json','w'),indent=1,ensure_ascii=False)
print('removed',len(removed),'added',len(added),'guard flags',len(flags),'warnings on added',len([w for w in warns if w[0] in {a['id'] for a in added}]))
