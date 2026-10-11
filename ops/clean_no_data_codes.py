"""Remove source no-data codes and impossible values from colleges.json (fix #26, Oct 11). Writes an archive list.
Usage: python3 -I ops/clean_no_data_codes.py   (run from the repo root)"""
import json,collections
p='colleges.json'; raw=open(p).read(); d=json.loads(raw)
log=[]; cnt=collections.Counter()
for c in d['colleges']:
    ip=c.get('ipeds') or {}; sc=c.get('scorecard') or {}
    def drop(obj,k,why):
        log.append({'id':c['id'],'name':c['name'],'field':('ipeds.' if obj is ip else 'scorecard.')+k,'value':obj[k],'why':why}); cnt[why]+=1; del obj[k]
    if isinstance(ip.get('retention'),(int,float)) and ip['retention']<=0: drop(ip,'retention','retention no-data code or 0')
    if isinstance(ip.get('yield'),(int,float)) and (ip['yield']<0 or ip['yield']>1): drop(ip,'yield','yield outside 0-1')
    if isinstance(ip.get('studentFacultyRatio'),(int,float)) and (ip['studentFacultyRatio']<=0 or ip['studentFacultyRatio']>60): drop(ip,'studentFacultyRatio','student-faculty ratio impossible')
    if sc.get('gradRate')==0: drop(sc,'gradRate','grad rate exactly 0')
    if sc.get('size')==0: drop(sc,'size','enrollment exactly 0')
    if sc.get('admissionRate')==0: drop(sc,'admissionRate','admit rate exactly 0')
    for k,v in list(sc.items()):
        if isinstance(v,(int,float)) and not isinstance(v,bool) and v in (-1,-2,-3) and k!='netPrice': drop(sc,k,'source no-data code')
open(p,'w').write(json.dumps(d,ensure_ascii=False,separators=(',',':'))+('\n' if raw.endswith('\n') else ''))
json.dump({'note':'No-data codes and impossible values removed from colleges.json on 2026-10-11 (fix #26). The app already hid these on screen (fix #6); this removes them at the source. Negative net prices are kept: they mean aid can exceed cost, and the app shows them as $0.','removed':log},open('archive/removed-no-data-codes-2026-10-11.json','w'),indent=1,ensure_ascii=False)
print(dict(cnt), len(log))
