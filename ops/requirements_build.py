"""Build requirements.json (#54, Oct 11): what each school asks for in a first-year application, from IPEDS.
ADM2023 admission considerations (1 = required, 5 = considered if submitted, 3 = not considered):
  ADMCON7 test scores, ADMCON11 essay/personal statement, ADMCON5 recommendations, ADMCON3 school record, ADMCON1 GPA.
IC2023 APPLFEEU = undergraduate application fee. Matched by unitid. Policies change: the page shows the year and
says to confirm on the school's site.  Usage: python3 -I ops/requirements_build.py <adm2023.csv> <IC2023.csv>"""
import csv,json,sys
cat=json.load(open('colleges.json'))['colleges']; byU={str(c['unitid']):c['id'] for c in cat}
CODE={'1':'required','5':'considered','3':'not_considered'}
out={}
for row in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig',errors='replace')):
    sid=byU.get(row['UNITID'])
    if not sid: continue
    e={k:CODE.get((row.get(c) or '').strip()) for k,c in [('tests','ADMCON7'),('essay','ADMCON11'),('recs','ADMCON5'),('record','ADMCON3'),('gpa','ADMCON1')]}
    e={k:v for k,v in e.items() if v}
    if e: out[sid]=e
fees=0
for row in csv.DictReader(open(sys.argv[2],encoding='utf-8-sig',errors='replace')):
    sid=byU.get(row['UNITID'])
    if not sid: continue
    try: fee=int(row.get('APPLFEEU') or '')
    except ValueError: continue
    if 0<=fee<=500: out.setdefault(sid,{})['fee']=fee; fees+=1
doc={'about':"First-year application requirements as each school reported them to IPEDS: test scores, essay, recommendations (required / considered if sent / not considered) and the undergraduate application fee.",
     'source':'IPEDS Admissions 2023 (ADMCON5, 7, 11, 3, 1) and Institutional Characteristics 2023 (APPLFEEU), NCES','year':'fall 2023','schools':dict(sorted(out.items()))}
json.dump(doc,open('requirements.json','w'),separators=(',',':')); open('requirements.json','a').write('\n')
print('schools',len(out),'with tests',sum(1 for v in out.values() if 'tests' in v),'with fee',fees)
