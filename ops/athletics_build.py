"""Build athletics.json (#80, Oct 12): varsity sports at every catalog school, all divisions.
Sources (federal, public):
  - EADA 2024-25 (Equity in Athletics, U.S. Dept. of Education): association/division (classification_name) and one row
    per varsity sport with men's / women's / co-ed participant counts (schools.xlsx, column "Sports").
  - IPEDS IC2024 (NCES): NCAA/NAIA conference for football (CONFNO1), basketball (CONFNO2), baseball (CONFNO3),
    cross country/track (CONFNO4), names from IC2024_dict.xlsx.
Matched by unitid only. No rankings (polls are licensed and change weekly; the app links to NCAA.com instead).
Usage: python3 -I ops/athletics_build.py <eada schools.xlsx> <eada instLevel.xlsx> <IC2024.csv> <IC2024_dict.xlsx>"""
import csv, json, sys, openpyxl
sch_x, inst_x, ic_csv, ic_dict = sys.argv[1:5]
cat = json.load(open('colleges.json'))['colleges']; byU = {str(c['unitid']): c['id'] for c in cat}

def level_of(name):
    n = (name or '').lower()
    if n.startswith('ncaa division i-fbs'): return 'D1', 'FBS'
    if n.startswith('ncaa division i-fcs'): return 'D1', 'FCS'
    if n.startswith('ncaa division iii'): return 'D3', None
    if n.startswith('ncaa division ii'): return 'D2', None
    if n.startswith('ncaa division i'): return 'D1', None
    if n.startswith('naia'): return 'NAIA', None
    if n.startswith('njcaa') or n.startswith('cccaa') or 'junior college' in n or n.startswith('nwac'): return 'JUCO', None
    if n.startswith('nccaa'): return 'NCCAA', None
    if n.startswith('uscaa'): return 'USCAA', None
    return 'Other', None

# conference names from the IPEDS dictionary (Frequencies sheet), with the names families actually use
RENAME = {'Ivy Group': 'Ivy League', 'Big Twelve Conference': 'Big 12 Conference', 'Pacific-12 Conference': 'Pac-12 Conference', 'Colonial Athletic Association': 'Coastal Athletic Association (CAA)'}
conf = {}
wb = openpyxl.load_workbook(ic_dict, read_only=True)
for r in wb['Frequencies'].iter_rows(values_only=True):
    v = [x for x in r if x is not None]
    if len(v) >= 4 and str(v[1]).startswith('CONFNO'):
        try: code = int(v[2])
        except (ValueError, TypeError): continue
        if code > 0 and str(v[3]) not in ('Other',): conf[code] = RENAME.get(str(v[3]).strip(), str(v[3]).strip())

ic = {}
for row in csv.DictReader(open(ic_csv, encoding='utf-8-sig')):
    sid = byU.get(row['UNITID'])
    if not sid: continue
    def c(k):
        try: return conf.get(int(row.get(k) or -2))
        except ValueError: return None
    ic[sid] = {'football': c('CONFNO1'), 'basketball': c('CONFNO2'), 'baseball': c('CONFNO3'), 'track': c('CONFNO4')}

def rows(path):
    ws = openpyxl.load_workbook(path, read_only=True).active; it = ws.iter_rows(values_only=True); h = list(next(it))
    for r in it: yield dict(zip(h, r))

out = {}
for r in rows(inst_x):
    sid = byU.get(str(r['unitid']))
    if not sid: continue
    lv, sub = level_of(r.get('classification_name'))
    out[sid] = {'assoc': r.get('classification_name'), 'level': lv, 'sub': sub, 'teams': [], 'athletes': 0,
                'rev': r.get('GRND_TOTAL_REVENUE') if isinstance(r.get('GRND_TOTAL_REVENUE'), (int, float)) else None}
for r in rows(sch_x):
    sid = byU.get(str(r['unitid']))
    if not sid or sid not in out: continue
    sport = str(r.get('Sports') or '').strip()
    if not sport: continue
    n = lambda k: int(r.get(k) or 0)
    m, w = n('PARTIC_MEN'), n('PARTIC_WOMEN'); cm, cw = n('PARTIC_COED_MEN'), n('PARTIC_COED_WOMEN')
    if m > 0: out[sid]['teams'].append([sport, 'm', m])
    if w > 0: out[sid]['teams'].append([sport, 'w', w])
    if cm + cw > 0: out[sid]['teams'].append([sport, 'c', cm + cw])
    out[sid]['athletes'] += m + w + cm + cw
POWER = {'Southeastern Conference', 'Big Ten Conference', 'Big 12 Conference', 'Atlantic Coast Conference'}
for sid, a in out.items():
    a['teams'].sort(key=lambda t: (t[0], t[1]))
    k = ic.get(sid) or {}
    a['conf'] = k.get('basketball') or k.get('track') or k.get('baseball') or k.get('football')
    if k.get('football') and k.get('football') != a['conf']: a['fbConf'] = k['football']
    fb = k.get('football') or (a['conf'] if any(t[0] == 'Football' for t in a['teams']) else None)
    a['gameDay'] = 'power' if (a['sub'] == 'FBS' and fb in POWER) else 'big' if a['sub'] == 'FBS' else 'd1' if a['level'] == 'D1' else 'small'
    a.pop('rev', None)   # not shown; keeps the file small
    if a['sub'] is None: a.pop('sub')
    if not a['conf']: a.pop('conf')
out = {k: v for k, v in out.items() if v['teams']}
doc = {'about': "Varsity sports at each school (all divisions): association and division, conference, and every team with its roster size. Rankings are not included.",
       'source': 'EADA 2024-25 (U.S. Dept. of Education) for teams, rosters and division; IPEDS IC2024 (NCES) for conferences',
       'year': '2024-25', 'schools': dict(sorted(out.items()))}
json.dump(doc, open('athletics.json', 'w'), separators=(',', ':'), ensure_ascii=False); open('athletics.json', 'a').write('\n')
from collections import Counter
print('schools', len(out), 'of', len(cat), Counter(v['level'] for v in out.values()), 'with conf', sum(1 for v in out.values() if v.get('conf')))
