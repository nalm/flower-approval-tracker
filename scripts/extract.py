"""Extract candidate rows; requires review.json before publication."""
import json,re,hashlib
from pathlib import Path
from collections import defaultdict,Counter
import pymupdf
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'research'

def shift(t,n):
    return ''.join(chr(ord(c)-n) if n and 0xAC00+n<=ord(c)<=0xD7A3+n else ' ' if 0xF000<=ord(c)<=0xFF00 else c for c in t)

def pages_decoded(doc):
    pages=[]; fonts=defaultdict(str)
    for p in doc:
        spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
        pages.append(spans)
        for s in spans: fonts[s['font']]+=s['text']+'\n'
    offsets={}
    for font,txt in fonts.items():
        hits=Counter()
        for target in ['국정운영','여론조사','정당지지','잘하고','조사완료']:
            for i in range(len(txt)-len(target)+1):
                n=ord(txt[i])-ord(target[0])
                if 0<=n<6000 and all(ord(txt[i+j])-ord(c)==n for j,c in enumerate(target)):
                    hits[n]+=len(target)
        offsets[font]=hits.most_common(1)[0][0] if hits else 0
    return ['\n'.join(shift(s['text'],offsets[s['font']]) for s in spans) for spans in pages],offsets

def cell(soup,label):
    for th in soup.select('th'):
        if th.get_text(' ',strip=True)==label:
            td=th.find_next('td'); return ' '.join(td.get_text(' ',strip=True).split())
    return ''

def run():
    rows=json.loads((CACHE/'details.json').read_text(encoding='utf-8'))
    collection=json.loads((CACHE/'collection.json').read_text(encoding='utf-8'))
    candidates=[]; excluded=[]; problems=[]
    previous=json.loads((CACHE/'candidates.json').read_text(encoding='utf-8')) if (CACHE/'candidates.json').exists() else {}
    verified_cache={r['id']:r for r in previous.get('records',[])}
    for row in rows:
        ident=row['id']; pdf=CACHE/f'result-{ident}.pdf'
        metadataHash=hashlib.sha256((CACHE/f'detail-{ident}.html').read_bytes()).hexdigest()
        if ident in verified_cache and verified_cache[ident]['sha256']==hashlib.sha256(pdf.read_bytes()).hexdigest() and verified_cache[ident].get('metadataHash')==metadataHash:
            candidates.append(verified_cache[ident]); continue
        soup=BeautifulSoup((CACHE/f'detail-{ident}.html').read_bytes(),'html.parser')
        dates=re.findall(r'\d{4}-\d{2}-\d{2}',cell(soup,'조사일시'))
        if not dates: problems.append([ident,'No dates']); continue
        doc=pymupdf.open(pdf); pages,offsets=pages_decoded(doc)
        match=None
        for i,text in enumerate(pages):
            compact=re.sub(r'\s+','',text)
            if '국정운영' in compact[:230] and '평가' in compact[:230] and any(q in compact[:230] for q in ['(1)','(2)']) and '\nQ\n' in text:
                nums=re.search(r'\((\d[\d,]*)\)\s*\n((?:\d+\.\d+\s*\n){7})',text)
                if nums:
                    values=list(map(float,nums[2].split()))
                    match=(i,text,int(nums[1].replace(',','')),values)
                    break
        if not match:
            reason='국정운영 기대감 문항' if any('국정운영' in t and '기대' in t[:500] for t in pages) else '국정운영 평가 수치 추출 확인 필요'
            excluded.append({'id':ident,'registration':row['registration'],'date':dates[-1],'reason':reason,'sourceUrl':f'https://www.nesdc.go.kr/portal/bbs/B0000005/view.do?nttId={ident}'})
            continue
        i,text,n,v=match
        approve,disapprove,unknown=v[4:7]
        if abs(approve+disapprove+unknown-100)>0.21 or abs(v[0]+v[1]-approve)>0.21 or abs(v[2]+v[3]-disapprove)>0.21:
            problems.append([ident,'Invalid totals',v]); continue
        if str(n)!=cell(soup,'전체'): problems.append([ident,'Sample mismatch',n,cell(soup,'전체')]); continue
        question=text.split('\nQ\n')[1].split('Base=')[0].strip()
        c={'id':ident,'registration':row['registration'],'agency':row['agency'],'client':row['client'],
          'method':'ARS' if 'ARS' in row['method_label'] else 'CATI', 'startDate':min(dates),'endDate':max(dates),
          'publishedDate':cell(soup,'최초 공표·보도 지정일시')[:10],'sampleSize':n,
          'margin':cell(soup,'표본오차'),'responseRate':cell(soup,'전체 응답률'),'contactRate':cell(soup,'전체 접촉률'),
          'target':cell(soup,'조사대상'),'frame':row['frame'],'weighting':cell(soup,'산출방법'),
          'approve':approve,'disapprove':disapprove,'unknown':unknown,'components':v[:4],
          'questionExtract':question,'sourceUrl':f'https://www.nesdc.go.kr/portal/bbs/B0000005/view.do?nttId={ident}',
          'pdfUrl':next(a['url'] for a in row['attachments'] if '결과' in a['name']),
          'pdfName':next(a['name'] for a in row['attachments'] if '결과' in a['name']),
          'pdfPage':i+1,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'metadataHash':metadataHash,'fontOffsets':offsets}
        candidates.append(c)
        (CACHE/f'evidence-{ident}.txt').write_text(text,encoding='utf-8')
        # Compact visual evidence for every extracted nationwide row and question.
        pix=doc[i].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),clip=pymupdf.Rect(45,75,550,240))
        (CACHE/'review').mkdir(exist_ok=True)
        pix.save(str(CACHE/'review'/f'{ident}.png'))
    candidates.sort(key=lambda r:(r['endDate'],r['method']))
    result={**collection,'regularCount':len(rows),'records':candidates,'excluded':excluded,'problems':problems}
    (CACHE/'candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'extracted':len(candidates),'excluded':excluded,'problems':problems,'first':candidates[:1],'last':candidates[-2:]},ensure_ascii=True)[:8000],flush=True)

if __name__=='__main__': run()
