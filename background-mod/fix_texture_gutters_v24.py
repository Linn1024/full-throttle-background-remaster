"""Repair filtering borders without changing stored geometry or alpha."""
import json,struct,subprocess,zlib
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,render
from texture_gutters import scene_maps

def fix(room):
 folder=ROOT/'locations'/room;out=folder/'custom-v1';cfg=json.loads((folder/'room.json').read_text())
 art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'));reports=[]
 for name in cfg['layers']:
  path=out/name;c=read_chunk(path);blocks=[]
  for ti,t in enumerate(c['textures']):
   a=np.array(t['image']);target=a.copy();mx,my,inside=scene_maps(c,t)
   selected=(mx!=-1)&~inside;target[selected,:3]=cv2.remap(art,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)[selected]
   png=out/f'{path.stem}-gutter-{ti}.png';Image.fromarray(target).save(png)
   fmt='BC1_UNORM' if t['format']==b'DXT1' else 'BC3_UNORM';stride=8 if fmt=='BC1_UNORM' else 16
   subprocess.run([str(ROOT/'tools/texconv.exe'),'-f',fmt,'-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
   encoded=png.with_suffix('.dds').read_bytes()[128:];raw=bytearray(t['raw']);h,w=a.shape[:2]
   changed=selected.reshape(h//4,4,w//4,4).any(axis=(1,3))
   for b in np.flatnonzero(changed):
    at=int(b)*stride;co=0 if stride==8 else 8;raw[at+co:at+stride]=encoded[at+co:at+stride]
   im=Image.frombytes('RGBA',(w,h),bytes(raw),'bcn',(1 if stride==8 else 3,t['format'].decode()))
   assert np.array_equal(np.array(im)[:,:,3],a[:,:,3])
   z=zlib.compressobj(9,zlib.DEFLATED,-15);p=t['payload'][:12]+z.compress(raw)+z.flush();blocks.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
   reports.append(dict(layer=name,texture=ti,gutter_pixels=int(selected.sum()),blocks=int(changed.sum()),alpha_exact=True))
  path.write_bytes(c['header']+b''.join(blocks));assert read_chunk(path)['header']==c['header']
 scene=Image.new('RGBA',tuple(cfg['size']))
 for name in cfg['layers']:scene=Image.alpha_composite(scene,render(read_chunk(out/name),tuple(cfg['size'])))
 scene.convert('RGB').save(out/'in-game-texture-preview.png')
 rev=ROOT/'reviews/seams-v24';rev.mkdir(exist_ok=True);(rev/f'{room}-gutters.json').write_text(json.dumps(reports,indent=2));print(room,'gutters repaired',flush=True)

if __name__=='__main__':
 import sys
 for room in sys.argv[1:]:fix(room)
