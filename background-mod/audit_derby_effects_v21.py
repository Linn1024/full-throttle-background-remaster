"""Extract the adjacent derby fire/light effect pages for review."""
import struct,json
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt
from audit_derby_v21 import REV
def main():
 with (ROOT.parent/'full.data').open('rb') as f:
  h=struct.unpack('<4s11I',f.read(48));f.seek(h[4]);names=f.read(h[8]).split(b'\0')
  for i,n in enumerate(names[:h[7]//24]):
   name=n.decode()
   if not any(name.startswith(f'costumes/{j}-') for j in [201,213,214,215]):continue
   p=ROOT/'original'/name
   if p.exists():continue
   f.seek(h[2]+i*24);offset,_,size,size2,flags=struct.unpack('<Q4I',f.read(24));assert size==size2 and flags==0
   f.seek(h[5]+offset);data=f.read(size);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 rows=[]
 for p in sorted((ROOT/'original/costumes').glob('*/*.dxt')):
  if int(p.parent.name[:3]) not in [201,213,214,215]:continue
  i=len(rows)+100;a=read_dxt(p)[2];im=Image.fromarray(a);im.save(REV/f'atlas-{i:02}-original.png');rows.append(dict(id=i,paths=[p.relative_to(ROOT).as_posix()],size=im.size))
 for start in range(0,len(rows),6):
  sheet=Image.new('RGB',(1200,840),'#333333');d=ImageDraw.Draw(sheet)
  for k,row in enumerate(rows[start:start+6]):
   im=Image.open(REV/f'atlas-{row["id"]:02}-original.png');im.thumbnail((395,390));x=k%3*400;y=k//3*420;sheet.paste(im,(x,y+25),im);d.text((x+4,y+4),f'{row["id"]} '+row['paths'][0].split('/')[-1],fill='white')
  sheet.save(REV/f'effects-{start//6}.jpg')
 (REV/'effects-inventory.json').write_text(json.dumps(rows,indent=2));print(len(rows),'effect pages')
if __name__=='__main__':main()
