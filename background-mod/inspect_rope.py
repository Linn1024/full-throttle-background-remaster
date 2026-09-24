import struct
from pathlib import Path
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt
items=[]
with Path('full.data').open('rb') as f:
 h=struct.unpack('<4s11I',f.read(48));f.seek(h[4]);names=f.read(h[8]).split(b'\0')[:h[7]//24]
 for i,n in enumerate(names):
  name=n.decode().replace('\\','/')
  if not any(s in name for s in ['109-climb-rope-cos/','111-hold-rope-cos/']):continue
  f.seek(h[2]+24*i);off,_,size,size2,flags=struct.unpack('<Q4I',f.read(24));assert flags==0
  f.seek(h[5]+off);p=ROOT/'original'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.read(size))
  if p.suffix=='.dxt':
   a=Image.fromarray(read_dxt(p)[2]);a.thumbnail((350,350));items.append((p.name,a))
out=Image.new('RGB',(1050,390*((len(items)+2)//3)), '#555555');d=ImageDraw.Draw(out)
for i,(n,a) in enumerate(items):
 x=i%3*350;y=i//3*390;out.paste(a,(x,y+30),a);d.text((x,y),n,fill='white')
out.save(ROOT/'previews/rope-atlases.jpg');print([n for n,a in items])
