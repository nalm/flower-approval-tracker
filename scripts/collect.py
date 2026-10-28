"""Collect public NESDC metadata and original result PDFs. Never publishes data."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse, parse_qs
import requests, json, re, time, argparse
from datetime import datetime,timezone,timedelta
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research'
BASE = 'https://www.nesdc.go.kr'
START = '2025-06-04'
END = str(datetime.now(timezone(timedelta(hours=9))).date())
REFRESH = False
CACHE.mkdir(exist_ok=True)

def get(url, path, params=None):
    if path.exists() and not REFRESH:
        return path.read_bytes()
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=45)
            r.raise_for_status()
            path.write_bytes(r.content)
            return r.content
        except requests.RequestException:
            if attempt == 2: raise
            time.sleep(2)

def listing(page):
    raw = get(BASE+'/portal/bbs/B0000005/list.do', CACHE/f'list-{START}-{END}-{page}.html', {
        'menuNo':'200467', 'searchCnd':'1','searchWrd':'꽃',
        'searchTime':'1','sdate':START,'edate':END,'pageIndex':page})
    soup = BeautifulSoup(raw, 'html.parser')
    rows=[]
    for a in soup.select('a.row'):
        cols=[c.get_text(' ',strip=True) for c in a.select('span.col')]
        if len(cols)<8: continue
        rows.append(dict(zip(['registration','agency','client','method_label','frame','title','registered','region'],cols),
            id=parse_qs(urlparse(a['href']).query)['nttId'][0], sourceUrl=BASE+a['href']))
    return rows

def detail(row):
    ident=row['id']
    raw=get(BASE+'/portal/bbs/B0000005/view.do?nttId='+ident,CACHE/f'detail-{ident}.html')
    soup=BeautifulSoup(raw,'html.parser')
    text=soup.get_text(' ',strip=True)
    row['text']=text
    attachments=[]
    for a in soup.select('a[onclick]'):
        code=a.get('onclick','')
        if not code.startswith('javascript:view('): continue
        args=re.findall(r"'([^']*)'",code)
        if len(args)!=4: continue
        url=BASE+'/portal/cmm/fms/FileDown.do?'+ '&'.join(k+'='+v for k,v in zip(['atchFileId','fileSn','bbsId','bbsKey'],args))
        name=a.get_text(' ',strip=True)
        attachments.append({'name':name,'url':url})
        if '결과' in name:
            path=CACHE/f'result-{ident}.pdf'
            content=get(url,path)
            if not content.startswith(b'%PDF'): raise ValueError('Not PDF: '+ident)
    row['attachments']=attachments
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--details',action='store_true'); p.add_argument('--end',default=END); p.add_argument('--refresh',action='store_true'); args=p.parse_args()
    END=args.end; REFRESH=args.refresh
    first=listing(1)
    count=int(re.search(r'Total\s*([\d,]+)',BeautifulSoup((CACHE/f'list-{START}-{END}-1.html').read_bytes(),'html.parser').get_text()).group(1).replace(',',''))
    print('Filtered listings:',count,flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=first+sum(list(pool.map(listing,range(2,(count+9)//10+1))),[])
    (CACHE/'all-listings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[r for r in rows if r['region']=='전국' and '정례' in r['title'] and r['agency']=='(주)여론조사꽃' and START<=r['registered']<=END]
    print('National regular:',len(rows),flush=True)
    (CACHE/'listings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (CACHE/'collection.json').write_text(json.dumps({'collectedAt':END,'requestedStart':START,'requestedEnd':END,'listingsCount':count}),encoding='utf-8')
    if args.details:
        results=[]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for i,r in enumerate(pool.map(detail,rows)):
                results.append(r)
                if i%10==0: print('Details',i+1,'/',len(rows),flush=True)
        (CACHE/'details.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Saved',len(results),'details',flush=True)
