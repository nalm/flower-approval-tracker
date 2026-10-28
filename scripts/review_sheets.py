from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'research/candidates.json').read_text(encoding='utf-8'))['records']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
for start in range(0,len(a),16):
    sheet=Image.new('RGB',(1340,8*252),'#eeeeee'); draw=ImageDraw.Draw(sheet)
    for k,r in enumerate(a[start:start+16]):
        x=(k%2)*670;y=(k//2)*252
        label=f"{start+k+1}. {r['id']} {r['method']} {r['endDate']} +{r['approve']} / -{r['disapprove']} / ?{r['unknown']}"
        draw.text((x+8,y+3),label,font=font,fill='black')
        im=Image.open(ROOT/'research/review'/f"{r['id']}.png")
        im.thumbnail((660,225))
        sheet.paste(im,(x+5,y+25))
    sheet.save(ROOT/'research'/f'review-sheet-{start//16+1}.png')
print('8 review sheets saved')
