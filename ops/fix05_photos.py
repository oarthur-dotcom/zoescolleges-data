import json, re, sys, time, urllib.request, concurrent.futures as cf
SRC='colleges.json'; d=json.load(open(SRC)); C=d['colleges']; byid={x['id']:x for x in C}
UA={'User-Agent':'ZoesCollegesPhotoCheck/1.0 (oarthur@gmail.com)'}
# ---- 1. removal list: (category, id, filename-substring) from the reviewed audit list
REMOVE_CATS = ('WRONG SCHOOL','WRONG CAMPUS','WRONG PLACE','WRONG INSTITUTION','NOT A CAMPUS','NOT CAMPUS','WRONG SCHOOL + YEARBOOK')
EXTRA = {'university-of-arizona'}   # "ASU_nima" = Arizona State photo on University of Arizona
removals, review = [], []
for line in open('/tmp/claude-0/audit-data/photo_suspects_curated.txt'):
    parts=[p.strip() for p in line.split('|')]
    if len(parts)<4: continue
    cat=parts[0]; m=re.search(r'\(([A-Z]{2}), ([^)]+)\)', parts[1]); sid=m.group(2); fname=parts[2]; why=parts[3]
    x=byid.get(sid)
    if not x or not x.get('photo'): print('SKIP missing', sid); continue
    # safety: the photo on file must still be the one that was reviewed
    from urllib.parse import unquote
    if fname.replace(' ','_')[:25] not in unquote(x['photo']['url']).replace(' ','_'):
        print('SKIP filename mismatch', sid, fname[:40]); continue
    if cat in REMOVE_CATS or sid in EXTRA: removals.append({'id':sid,'name':x['name'],'reason':why,'photo':x['photo']})
    else: review.append({'id':sid,'name':x['name'],'flag':cat,'note':why,'url':x['photo']['url']})
for r in removals: del byid[r['id']]['photo']
# ---- 2. normalise every remaining photo to a 960px thumb on thumb.wikimedia.org
def thumb(url, w):
    m=re.match(r'https://(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/(?:thumb/)?([0-9a-f])/([0-9a-f]{2})/([^/]+)', url)
    if not m: return None
    a,b,name=m.groups(); ext=name.rsplit('.',1)[-1].lower()
    if ext not in ('jpg','jpeg','png','gif'): return None
    return f'https://thumb.wikimedia.org/wikipedia/commons/thumb/{a}/{b}/{name}/{w}px-{name}'
def head(u):
    for attempt in range(4):
        try:
            req=urllib.request.Request(u, headers=UA, method='HEAD')
            with urllib.request.urlopen(req, timeout=25) as r: return r.status, r.headers.get('Content-Type',''), int(r.headers.get('Content-Length') or 0)
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(3*(attempt+1)); continue
            return e.code,'',0
        except Exception as e: time.sleep(2); last=str(e)
    return None,'',0
def work(x):
    old=x['photo']['url']
    for w in (960,500,330):
        u=thumb(old,w)
        if not u: return x['id'], old, 'kept-unconvertible', None
        st,ct,ln=head(u)
        if st==200 and ct.startswith('image/'): return x['id'], u, f'ok-{w}', ln
    st,ct,ln=head(old)
    return x['id'], old, f'kept-original(http {st})', ln
todo=[x for x in C if x.get('photo')]
results={}
with cf.ThreadPoolExecutor(6) as ex:
    for i,(sid,u,status,ln) in enumerate(ex.map(work,todo)):
        results[sid]=(u,status,ln)
        if i%200==0: print('checked',i,'/',len(todo),flush=True)
from collections import Counter
print('status counts', Counter(s for _,s,_ in results.values()))
for sid,(u,status,ln) in results.items(): byid[sid]['photo']['url']=u
json.dump(d, open(SRC,'w'), ensure_ascii=False, separators=(',',':'))  # same compact style as the file
json.dump({'removed':removals,'flagged_for_review':review,'url_results':{k:{'url':v[0],'status':v[1],'bytes':v[2]} for k,v in results.items()}}, open('/tmp/claude-0/f5/photo-report.json','w'), indent=1, ensure_ascii=False)
print('removed', len(removals), 'flagged', len(review))
