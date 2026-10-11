"""Build deadlines-2026-27.json from Muse's Job B file (2026-10-11 handoff).
Input is checksum-verified against Muse's MANIFEST.json before use (sha256 below).
Held back until Muse re-checks them: 25 schools whose source page was for transfer/international/
graduate/department applicants, and every low-confidence round.
Usage: python3 ops/deadlines_build.py <B-deadlines-2026-27.json> [<B-deadlines-2026-27-fixes.json>]
The fixes file (Muse, same day) replaces whole schools by unitid; a school it covers is no longer held.
"""
import json,sys,hashlib,datetime as dt
SHA='61b8bf3855b12586233523a0ae2c2a2737649eaaf785f6c0920bc83676fde100'
raw=open(sys.argv[1],'rb').read(); assert hashlib.sha256(raw).hexdigest()==SHA, 'checksum mismatch - stop'
B=json.loads(raw)
FIX_SHA='8e3cd558330e70cd1ecf57a6d4a6f9c80f06703478b9e7e42b68d3935ebbadc9'
fixed=set()
if len(sys.argv)>2:
    fr=open(sys.argv[2],'rb').read(); assert hashlib.sha256(fr).hexdigest()==FIX_SHA, 'fixes checksum mismatch - stop'
    FX=json.loads(fr); assert isinstance(FX.get('schools'),list), 'unexpected fixes shape - stop'
    byu={s['unitid']:s for s in FX['schools']}; fixed=set(byu)
    B['schools']=[byu.get(s['unitid'],s) for s in B['schools']]
HELD=[138600,164988,161004,190099,148496,150455,169798,212911,191630,159647,153834,209506,121150,123554,122409,200800,100663,110635,110662,110680,126562,169716,170976,102094,206084]
KIND={'ED1':'Early Decision','ED2':'Early Decision II','EA':'Early Action','REA':'Restrictive Early Action','RD':'Regular Decision','PRIORITY':'Priority'}
cat=json.load(open('colleges.json'))['colleges']; byU={c['unitid']:c for c in cat}
assert isinstance(B,dict) and isinstance(B.get('schools'),list) and len(B['schools'])==518, 'unexpected shape - stop'
out={}; heldLow=0
for s in B['schools']:
    u=s['unitid']; c=byU.get(u); assert c, f'unitid {u} not in catalog'
    if u in HELD and u not in fixed: continue
    rounds=[]
    for r in s['rounds']:
        if not r.get('date'): continue
        if r.get('confidence')=='low': heldLow+=1; continue
        dt.date.fromisoformat(r['date'])
        assert r['source_url'].startswith('http')
        rounds.append({'k':r['round_key'],'kind':KIND[r['round_key']],'date':r['date'],'name':r.get('round_name_as_worded') or None,'src':r['source_url'],'conf':r['confidence']})
    if rounds: out[c['id']]={'rounds':sorted(rounds,key=lambda x:x['date']),'checked':s.get('checked_date') or B['checked_date']}
doc={'cycle':'2026-27','checked':B['checked_date'],
     'source':"Muse Job B, B-deadlines-2026-27.json (sha256 "+SHA[:12]+"…), each date from the school's own admissions site",
     'note':"Dates for first-year applicants. Muse's fixes file (30 schools re-sourced from first-year pages) replaces those schools. Low-confidence rounds are left out.",
     'held_unitids':[u for u in HELD if u not in fixed], 'fixes_applied':sorted(fixed),'schools':dict(sorted(out.items()))}
json.dump(doc,open('deadlines-2026-27.json','w'),indent=1,ensure_ascii=False); open('deadlines-2026-27.json','a').write('\n')
print('schools',len(out),'rounds',sum(len(v['rounds']) for v in out.values()),'held schools',len([u for u in HELD if u not in fixed]),'held low-confidence rounds',heldLow)
