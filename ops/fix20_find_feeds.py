import json,re,sys,urllib.request,urllib.parse,concurrent.futures as cf
UA={'User-Agent':'Mozilla/5.0 (compatible; ZoesCollegesFeedFinder/1.0; +https://zoescolleges.com)'}
def get(u,t=12):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return r.geturl(), r.read(400000).decode('utf-8','ignore'), r.headers.get('Content-Type','')
    except Exception as e: return None,None,None
def isfeed(body,ct): return bool(body) and (('xml' in (ct or '') or 'rss' in (ct or '')) or body.lstrip()[:400].lower().find('<rss')>=0 or '<feed' in body[:400].lower()) and ('<item' in body or '<entry' in body)
def items(body):
    out=[]
    for m in re.finditer(r'<(item|entry)\b.*?</\1>',body,re.S|re.I):
        x=m.group(0); t=re.search(r'<title[^>]*>(.*?)</title>',x,re.S|re.I); d=re.search(r'<(pubDate|updated|published|dc:date)[^>]*>(.*?)</\1>',x,re.S|re.I)
        if t: out.append((re.sub(r'<!\[CDATA\[|\]\]>|<[^>]+>','',t.group(1)).strip()[:90], (d.group(2).strip()[:25] if d else '')))
    return out
def find(site):
    if not site: return None
    if not site.startswith('http'): site='https://'+site
    final,html,ct=get(site)
    cands=[]
    if html:
        for m in re.finditer(r'<link[^>]+type=["\']application/(rss|atom)\+xml["\'][^>]*>',html,re.I):
            h=re.search(r'href=["\']([^"\']+)',m.group(0)); 
            if h: cands.append(urllib.parse.urljoin(final,h.group(1)))
    base=(final or site).rstrip('/')
    p=urllib.parse.urlparse(base); root=f"{p.scheme}://{p.netloc}"
    dom=p.netloc.replace('www.','')
    cands+= [root+'/news/feed', root+'/feed', root+'/news/rss', root+'/news/rss.xml', root+'/rss', root+'/feed.xml', root+'/news/feed.xml', root+'/newsroom/feed',
             'https://news.'+dom+'/feed', 'https://news.'+dom+'/rss', 'https://news.'+dom+'/feed.xml', 'https://news.'+dom+'/news.rss',
             'https://today.'+dom+'/feed', 'https://newsroom.'+dom+'/feed', 'https://www.'+dom+'/news/feed/', 'https://stories.'+dom+'/feed']
    seen=set()
    for c in cands:
        if c in seen: continue
        seen.add(c); f,b,ct=get(c,10)
        if isfeed(b,ct):
            it=items(b)
            if it: return {'feed':f,'n':len(it),'top':it[:2]}
    return None
cat=json.load(open('/home/claude/zoescolleges-data/colleges.json'))['colleges']
names=sys.argv[1:] 
pick=[c for c in cat if c['name'] in names] if names else None
if not pick:
    import random; random.seed(7)
    big=[c for c in cat if c.get('degreeType')=='4-year' and (c.get('scorecard') or {}).get('size') and c['scorecard']['size']>5000 and c.get('link')]
    pick=random.sample(big,25)
res={}
with cf.ThreadPoolExecutor(8) as ex:
    for c,r in zip(pick, ex.map(lambda c: find(c.get('link')), pick)): res[c['name']]=r
hit=sum(1 for v in res.values() if v)
for k,v in res.items(): print(('FOUND ' if v else 'none  ')+k[:42].ljust(43)+(v['feed'][:60]+' | '+v['top'][0][0][:50]+' | '+v['top'][0][1] if v else ''))
print(f"\n{hit}/{len(res)} schools with a working feed")
json.dump(res,open('sample.json','w'),indent=1)
