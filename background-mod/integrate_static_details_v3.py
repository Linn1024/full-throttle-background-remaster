"""Place reviewed generated crops into their original scene coordinates.

Uses local generated raster inputs; no procedural drawing or global upscale.
Run before the scoped CHNK and object-scenery builders.
"""
import json
import shutil
import numpy as np
from PIL import Image
from scene_assets import ROOT

INPUT = ROOT/'reviews/static-sprites-v3'
JOBS = {
 'label': (None, (340,330,550,560)),
 'bottles': ('007-bar', (0,300,610,790)),
 'signs': ('026-gas-gate', (1060,475,1250,820)),
 'lettering': ('027-junkgate', (140,20,965,445)),
 'exit': ('032-mensroom', (1570,370,1880,960)),
}

def main():
 for key,(room,box) in JOBS.items():
  folder=ROOT/'locations'/room if room else ROOT
  backup=folder/'before-static-v3'
  dest=folder/'custom-remaster-v1.png' if room else ROOT/'scene/custom-remaster-v1.png'
  size=tuple(json.loads((folder/'room.json').read_text())['size']) if room else (2220,1200)
  base=np.array(Image.open(backup/'custom-remaster-v1.png').convert('RGB').resize(size,Image.Resampling.LANCZOS))
  x0,y0,x1,y1=box;w,h=x1-x0,y1-y0
  patch=np.array(Image.open(INPUT/(key+'-generated.png')).convert('RGB').resize((w,h),Image.Resampling.LANCZOS))
  yy,xx=np.mgrid[:h,:w]
  edge=np.minimum.reduce([xx if x0 else np.full_like(xx,20),yy,w-1-xx,h-1-yy])
  weight=np.clip(edge/16,0,1)[:,:,None]
  base[y0:y1,x0:x1]=np.rint(patch*weight+base[y0:y1,x0:x1]*(1-weight)).astype('uint8')
  Image.fromarray(base).save(dest)
  if room:
   cfg=json.loads((backup/'room.json').read_text())
   cfg['protected']=[r for r in cfg['protected'] if not (r[0]<x1 and r[2]>x0 and r[1]<y1 and r[3]>y0)]
   if room=='032-mensroom':
    # The crop includes a small margin above the door; retain the separate sign.
    cfg['protected']=[r for r in json.loads((backup/'room.json').read_text())['protected'] if r[3]<=380]
   (folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n')
 # These switches are scenery, not protected text. Let the existing detailed
 # room artwork reach the formerly excluded left-hand controls.
 f=ROOT/'locations/017-mo-shop';cfg=json.loads((f/'before-static-v3/room.json').read_text())
 cfg['protected']=[r for r in cfg['protected'] if r[0]>1000]
 (f/'room.json').write_text(json.dumps(cfg,indent=2)+'\n')
 shutil.copy2(INPUT/'dimmer-generated.png',ROOT/'locations/025-toddshop/custom-remaster-v1.png')

if __name__=='__main__':main()
