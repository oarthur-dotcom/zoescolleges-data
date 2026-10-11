"""Add each school's founding year (fix #35, Oct 11). Source: Wikidata 'inception' (P571), matched by the
federal school ID (IPEDS unitid, Wikidata P1771) - never by name. Schools whose Wikidata entries disagree are left blank.
Usage: python3 -I ops/add_founded_year.py <founded.json from the Wikidata query>"""
import json,sys
F=json.load(open(sys.argv[1])); one=F['single']
p='colleges.json'; raw=open(p).read(); d=json.loads(raw); n=0
for c in d['colleges']:
    y=one.get(str(c['unitid']))
    if y and 1600<=y<=2026: c['founded']=y; n+=1
open(p,'w').write(json.dumps(d,ensure_ascii=False,separators=(',',':'))+('\n' if raw.endswith('\n') else ''))
json.dump({'note':"Founding years from Wikidata (P571 inception), matched by IPEDS unitid (P1771). Query run 2026-10-11. Conflicting entries left blank.",
           'added':n,'left_blank_conflicts':{u:v for u,v in F['multi'].items()},'wikidata_items':F['item']},open('archive/founded-year-2026-10-11.json','w'),indent=0)
print('founded added',n,'of',len(d['colleges']))
