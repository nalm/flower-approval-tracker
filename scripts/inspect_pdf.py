from pathlib import Path
import pymupdf, json, re
ROOT=Path(__file__).resolve().parents[1]
def decode(text):
    # Some HWP PDF ToUnicode tables offset Hangul code points by 0xDFB.
    # Select only when the offset version recovers the known document title.
    fixed=''.join(chr(ord(c)-0xDFB) if 0xB9FB<=ord(c)<=0xE59E else ' ' if c=='\uf684' else c for c in text)
    return fixed if '조사' in fixed and '여론조사' not in text else text

if __name__=='__main__':
    inventory=[]
    for path in sorted((ROOT/'research').glob('result-*.pdf')):
        doc=pymupdf.open(path); pages=[]
        for i,p in enumerate(doc):
            text=decode(p.get_text())
            if ('국정' in text or '대통령' in text) and re.search(r'\(1\)|평가|기대',text):
                pages.append({'page':i+1,'head':text[:800]})
            (ROOT/'research'/f'{path.stem}-p{i+1}.txt').write_text(text,encoding='utf-8')
        inventory.append({'id':path.stem.split('-')[1],'pages':pages})
    (ROOT/'research'/'pdf-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(inventory[:2]+inventory[-2:],ensure_ascii=True)[:10000])
