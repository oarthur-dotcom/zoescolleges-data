"""Build school-aid.json (#53, Oct 11): how many first-time, full-time undergraduates get grant money from the
school itself, and the average amount. Source: IPEDS Student Financial Aid 2022-23 (SFA2223, NCES), columns
IGRNT_P (% receiving institutional grants) and IGRNT_A (average institutional grant). Matched by unitid only.
Institutional grants mix need-based and merit aid; the page says so.
Usage: python3 -I ops/school_aid_build.py <sfa2223.csv>"""
import csv,json,sys
cat=json.load(open('colleges.json'))['colleges']; byU={str(c['unitid']):c['id'] for c in cat}
out={}
for row in csv.DictReader(open(sys.argv[1],encoding='latin-1')):
    sid=byU.get(row['UNITID'])
    if not sid: continue
    def num(k,lo,hi):
        try: v=int(row.get(k) or ''); return v if lo<=v<=hi else None
        except ValueError: return None
    p=num('IGRNT_P',0,100); a=num('IGRNT_A',1,100000)
    if p is None: continue
    out[sid]={'pct':p, 'avg':a if p>0 else None}
doc={'about':"Institutional grant aid to first-time, full-time undergraduates: share receiving any grant from the school itself, and the average amount. Mixes need-based and merit aid.",
     'source':'IPEDS Student Financial Aid 2022-23 (NCES), IGRNT_P and IGRNT_A','year':'2022-23','schools':dict(sorted(out.items()))}
json.dump(doc,open('school-aid.json','w'),separators=(',',':')); open('school-aid.json','a').write('\n')
print('schools',len(out),'with avg',sum(1 for v in out.values() if v['avg']))
