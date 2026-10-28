"""Build public data only from explicitly reviewed PDF hashes."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'research/candidates.json').read_text(encoding='utf-8'))
review=json.loads((ROOT/'research/review.json').read_text(encoding='utf-8'))
assert not source['problems'],source['problems']
assert source['regularCount']==len(source['records'])+len(source['excluded'])
seen=set();pairs=set()
for r in source['records']:
    assert review['approved'].get(r['id'])==r['sha256'],f"Unreviewed {r['id']}"
    assert r['id'] not in seen;seen.add(r['id'])
    assert (r['method'],r['endDate']) not in pairs;pairs.add((r['method'],r['endDate']))
    assert abs(r['approve']+r['disapprove']+r['unknown']-100)<=.21
    assert '국정운영' in r['questionExtract']
    assert source['requestedStart']<=r['startDate']<=r['endDate']<=source['requestedEnd']
    # A legible question transcription checked in the rendered evidence.
    r['question']='이재명 대통령의 국정운영에 대해 어떻게 평가하십니까? (그래도 평가한다면 어떻다고 생각하십니까?)'
    r['reviewedAt']=review['reviewedAt']
    r.pop('fontOffsets',None)
    r.pop('questionExtract',None)
source['reviewedAt']=review['reviewedAt']
source.pop('problems')
(ROOT/'data.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data.js').write_text('window.POLL_DATA = '+json.dumps(source,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
print('Published',len(source['records']),'reviewed rows. CATI/ARS:',[(m,sum(r['method']==m for r in source['records'])) for m in ['CATI','ARS']])
