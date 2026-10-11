"""Campus Pulse v2 feed finder (Oct 11). Read-only: fetches public pages/feeds, writes a candidate list to a scratch file.
For each target school it looks for, on the school's OWN web domain:
  news       official news feed (RSS/Atom), newest story within 120 days
  admissions admissions-office blog/news feed, newest story within 180 days
  events     public Localist campus calendar (JSON API) with at least one event in the next 30 days
Student newspapers are left to Muse (Job E). Nothing here publishes anything.
Usage: python3 ops/pulse_v2_find.py <targets.json> <out.json>
"""
import json,re,sys,urllib.request,urllib.parse,concurrent.futures as cf,datetime as dt,email.utils
UA={'User-Agent':'Mozilla/5.0 (compatible; ZoesCollegesPulse/1.0; +https://zoescolleges.com)'}
NOW=dt.datetime.now(dt.timezone.utc)
def get(u,t=9,limit=600000):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r:
            return r.geturl(), r.read(limit).decode('utf-8','ignore'), r.headers.get('Content-Type','')
    except Exception: return None,None,None
def regdom(host):
    h=(host or '').lower().split(':')[0]
    if h.startswith('www.'): h=h[4:]
    p=h.split('.'); return '.'.join(p[-2:]) if len(p)>=2 else h
def pdate(s):
    s=(s or '').strip()
    if not s: return None
    try:
        d=email.utils.parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception: pass
    try:
        d=dt.datetime.fromisoformat(s.replace('Z','+00:00')[:25])
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception: return None
def feed_items(body):
    out=[]
    for m in re.finditer(r'<(item|entry)\b.*?</\1>',body or '',re.S|re.I):
        x=m.group(0); t=re.search(r'<title[^>]*>(.*?)</title>',x,re.S|re.I)
        d=re.search(r'<(pubDate|published|updated|dc:date)[^>]*>(.*?)</\1>',x,re.S|re.I)
        if t: out.append((re.sub(r'<!\[CDATA\[|\]\]>|<[^>]+>','',t.group(1)).strip()[:100], pdate(d.group(2)) if d else None))
    return out
def isfeed(body,ct):
    if not body: return False
    head=body.lstrip()[:500].lower()
    return ('<rss' in head or '<feed' in head or '<?xml' in head or 'xml' in (ct or '')) and ('<item' in body or '<entry' in body)
def check_feed(url, dom, max_age_days):
    f,b,ct=get(url)
    if not f or not isfeed(b,ct): return None
    if regdom(urllib.parse.urlparse(f).hostname)!=dom: return None
    it=feed_items(b); dates=[d for _,d in it if d]
    if len(it)<2 or not dates: return None
    newest=max(dates)
    if (NOW-newest).days>max_age_days or newest>NOW+dt.timedelta(days=2): return None
    return {'url':f,'newest':newest.date().isoformat(),'n':len(it),'sample':it[0][0]}
def autodiscover(page):
    f,html,ct=get(page)
    if not html: return []
    out=[]
    for m in re.finditer(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>',html,re.I):
        h=re.search(r'href=["\']([^"\']+)',m.group(0))
        if h: out.append(urllib.parse.urljoin(f,h.group(1)))
    return out
def find_news(root,dom,existing):
    cands=([existing] if existing else [])
    cands+=autodiscover(root+'/news')+autodiscover('https://news.'+dom)+autodiscover(root)
    cands+=[root+'/news/feed', root+'/news/feed/', root+'/news/rss', root+'/news/rss.xml', root+'/news/feed.xml', root+'/feed', root+'/rss',
            root+'/newsroom/feed', root+'/news/index.xml', root+'/news/?format=rss',
            'https://news.'+dom+'/feed', 'https://news.'+dom+'/feed/', 'https://news.'+dom+'/rss', 'https://news.'+dom+'/rss.xml', 'https://news.'+dom+'/feed.xml',
            'https://news.'+dom+'/news.rss', 'https://news.'+dom+'/stories/rss', 'https://today.'+dom+'/feed', 'https://newsroom.'+dom+'/feed', 'https://stories.'+dom+'/feed', 'https://www.'+dom+'/news/feed/']
    seen=set()
    for c in cands:
        if c in seen or not c: continue
        seen.add(c)
        if re.search(r'comments|/wp-json|oembed',c,re.I): continue
        r=check_feed(c,dom,120)
        if r: return r
    return None
def find_admissions(root,dom,news_url):
    cands=autodiscover('https://admissions.'+dom)+autodiscover('https://admission.'+dom)+autodiscover(root+'/admissions')+autodiscover(root+'/admission')
    cands+=['https://admissions.'+dom+'/feed', 'https://admissions.'+dom+'/blog/feed', 'https://admission.'+dom+'/feed', 'https://admission.'+dom+'/blog/feed',
            root+'/admissions/feed', root+'/admissions/blog/feed', root+'/admission/blog/feed', root+'/admissions/news/feed', 'https://blogs.'+dom+'/admissions/feed']
    seen=set()
    for c in cands:
        if c in seen or not c or c==news_url: continue
        seen.add(c)
        if re.search(r'comments',c,re.I): continue
        if not re.search(r'admi',c,re.I): continue   # must be an admissions URL, not the site-wide feed again
        r=check_feed(c,dom,180)
        if r: return r
    return None
def find_events(dom):
    for host in ['events.'+dom,'calendar.'+dom,'www.'+dom+'/calendar','www.'+dom+'/events']:
        base='https://'+host
        f,b,ct=get(base+'/api/2/events?days=30&pp=5',t=8)
        if not f or 'json' not in (ct or ''): continue
        try: j=json.loads(b)
        except Exception: continue
        ev=j.get('events') or []
        starts=[]
        for e in ev:
            for inst in (e.get('event') or {}).get('event_instances') or []:
                d=pdate(((inst or {}).get('event_instance') or {}).get('start'))
                if d: starts.append(d)
        if not starts or regdom(urllib.parse.urlparse(f).hostname)!=dom: continue
        if any(NOW-dt.timedelta(days=1)<=d<=NOW+dt.timedelta(days=30) for d in starts):
            return {'type':'localist','url':base+'/api/2/events','sample':(ev[0]['event'] or {}).get('title','')[:100],'n':len(ev)}
    return None
def one(t):
    site=t.get('link') or ''
    if not site: return t['id'],{'error':'no site'}
    if not site.startswith('http'): site='https://'+site
    p=urllib.parse.urlparse(site); dom=regdom(p.hostname); root='https://www.'+dom if not p.hostname.startswith(dom) or p.hostname.startswith('www.') else 'https://'+p.hostname
    out={'dom':dom}
    try: out['news']=find_news(root,dom,t.get('existing_news'))
    except Exception as e: out['news_err']=str(e)[:80]
    try: out['admissions']=find_admissions(root,dom,(out.get('news') or {}).get('url'))
    except Exception as e: out['adm_err']=str(e)[:80]
    try: out['events']=find_events(dom)
    except Exception as e: out['ev_err']=str(e)[:80]
    return t['id'],out
if __name__=='__main__':
    targets=json.load(open(sys.argv[1])); res={}
    with cf.ThreadPoolExecutor(24) as ex:
        for i,(k,v) in enumerate(ex.map(one,targets)):
            res[k]=v
            if i%50==0: print(i,len(targets),flush=True); json.dump(res,open(sys.argv[2],'w'))
    json.dump(res,open(sys.argv[2],'w'),indent=0)
    print('done',len(res),'news',sum(1 for v in res.values() if v.get('news')),'admissions',sum(1 for v in res.values() if v.get('admissions')),'events',sum(1 for v in res.values() if v.get('events')))
