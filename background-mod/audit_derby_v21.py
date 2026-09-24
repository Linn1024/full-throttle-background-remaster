"""Inventory derby texture pages and prepare review sheets (no game writes)."""
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt
REV=ROOT/'reviews/derby-v21'
ROOMS=['056-arena','057-demowall','058-derbycar','059-rips-box','096-demoderb','142-derbypit']
GENERATED=['222a17c9-805d-4524-8586-d0c3ca06967a','932384b9-7350-4782-9181-535a40d4fffc','64c5357d-9985-49ff-aa7e-dc039057c591','eab3651a-f0c5-46e6-8413-c6a77aef61f4','21b155f4-bc38-45b3-80e5-f10e9594623e','af2c187f-f8bc-4ea6-b062-1c3401920f9a']
def main():
 REV.mkdir(exist_ok=True,parents=True)
 for room,g in zip(ROOMS,GENERATED):
  shutil.copy2(ROOT.parent.parent.parent.parent/'Users/linn1/.codex/generated_images/01a0cd70-1192-7f73-919f-7322a0c4973c'/f'exec-{g}.png',REV/f'{room}-generated.png')
 pages=[];groups={}
 for p in sorted((ROOT/'original/costumes').glob('*/*.dxt')):
  number=int(p.parent.name[:3])
  if not (203<=number<=210 or 380<=number<=390):continue
  data,raw,a=read_dxt(p);key=hashlib.sha256(data[:12]+raw).hexdigest()
  pages.append(dict(path=p.relative_to(ROOT).as_posix(),hash=key,format=data[:4].decode(),size=[a.shape[1],a.shape[0]],opaque=int((a[:,:,3]>0).sum())))
  groups.setdefault(key,[]).append(p)
 out=[]
 for i,(key,paths) in enumerate(groups.items()):
  a=read_dxt(paths[0])[2];im=Image.fromarray(a);im.save(REV/f'atlas-{i:02}-original.png')
  rgb=a[:,:,:3][a[:,:,3]>0];out.append(dict(id=i,hash=key,paths=[p.relative_to(ROOT).as_posix() for p in paths],size=im.size,range=[int(rgb.min()),int(rgb.max())] if len(rgb) else []))
 for j in range(0,len(out),8):
  sheet=Image.new('RGB',(1200,1320),'#333333');d=ImageDraw.Draw(sheet)
  for k,row in enumerate(out[j:j+8]):
   im=Image.open(REV/f'atlas-{row["id"]:02}-original.png');im.thumbnail((295,595));x=(k%4)*300;y=(k//4)*660
   sheet.paste(im,(x,y+45),im);d.text((x+4,y+4),f'{row["id"]:02} '+row['paths'][0].split('/')[-2]+'\n'+row['paths'][0].split('/')[-1][-7:],fill='white')
  sheet.save(REV/f'atlas-sheet-{j//8}.jpg')
 (REV/'atlas-inventory.json').write_text(json.dumps(out,indent=2))
 print(f'{len(pages)} pages, {len(groups)} unique; saved inventory and sheets')
if __name__=='__main__':main()
