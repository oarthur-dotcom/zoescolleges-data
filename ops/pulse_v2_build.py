"""Build campus-feeds.json v2 from the finder output (ops/pulse_v2_find.py) + the reviewed v1 list.
Keeps every v1 news feed (they were reviewed this morning) unless the finder found a working replacement.
Usage: python3 ops/pulse_v2_build.py <found.json> <targets.json>   (writes campus-feeds.json in place)
"""
import json,sys,datetime as dt
found=json.load(open(sys.argv[1])); targets={t['id']:t for t in json.load(open(sys.argv[2]))}
old=json.load(open('campus-feeds.json'))
today=dt.date.today().isoformat()
schools={}
for sid,e in old['schools'].items(): schools[sid]=dict(e)
# Hand-checked additions (official sites on their own domains, verified 2026-10-11)
MANUAL={'sc-166683':{'admissions':'https://mitadmissions.org/feed/'}}   # MIT's official admissions site
for sid,f in found.items():
    if not isinstance(f,dict): continue
    e=schools.get(sid,{})
    if f.get('news') and len(f['news']['url'])<=200 and '%3C' not in f['news']['url']: e['news']=f['news']['url']; e['newest']=max(e.get('newest',''),f['news']['newest'])
    if f.get('admissions'): e['admissions']=f['admissions']['url']
    if f.get('events'): e['events']={'type':'localist','url':f['events']['url']}
    if any(k in e for k in ('news','admissions','events')): e['checked']=today; schools[sid]=e
for sid,add in MANUAL.items(): schools.setdefault(sid,{}).update(add); schools[sid]['checked']=today
out={'about':"Reviewed public feeds for Campus Pulse. Only these URLs are ever fetched. news/admissions: RSS/Atom on the school's own web domain with a story in the last 120/180 days; events: the school's public Localist calendar with events in the next 30 days. Student-newspaper feeds are added as Muse verifies them (Job E). Checked "+today+".",
     'checked':today,'version':2,'schools':dict(sorted(schools.items()))}
json.dump(out,open('campus-feeds.json','w'),indent=1,ensure_ascii=False); open('campus-feeds.json','a').write('\n')
n=lambda k: sum(1 for v in schools.values() if v.get(k))
print('schools',len(schools),'news',n('news'),'admissions',n('admissions'),'events',n('events'),'any2+',sum(1 for v in schools.values() if sum(bool(v.get(k)) for k in ('news','admissions','events'))>=2))
