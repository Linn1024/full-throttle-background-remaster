"""Redraw the opened entrance with its runtime placement and shared pavement."""
import json
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,render
from build_custom import build
from build_derby_overlays_v21 import chunk_pack
from texture_gutters import scene_maps
from fix_texture_gutters_v24 import fix

def main():
 rev=ROOT/'reviews/seams-v24';folder=ROOT/'locations/060-big-door';out=folder/'custom-v1'
 cfg=json.loads((folder/'room.json').read_text());cfg['protected']=[r for r in cfg['protected'] if r!=[820,260,1435,685]]
 (folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build('060-big-door');fix('060-big-door')
 base=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 reference=np.array(Image.open(rev/'entrance-open-original.png').convert('RGB'))
 art=cv2.resize(np.array(Image.open(rev/'entrance-generated.png').convert('RGB')),(590,910),interpolation=cv2.INTER_LANCZOS4)
 registration=dict(method='fixed crop; manually checked door tip, hinge edge and bottom corner',target_size=[590,910])
 # The open leaf and revealed interior are the only changed silhouettes.
 # The rest of this large rectangular sprite samples the shared background.
 mask=np.zeros((910,590),np.uint8)
 cv2.fillPoly(mask,[np.array([(190,80),(360,8),(378,25),(378,90),(466,104),(466,570),(375,631),(195,590)],np.int32)],1)
 # The floor exposed behind the leaf was hidden by the closed door. Continue
 # the adjacent canonical pavement there instead of restoring the closed leaf.
 floor=np.zeros_like(mask);cv2.fillPoly(floor,[np.array([(378,570),(466,550),(466,590),(375,631)],np.int32)],1)
 yy,xx=np.mgrid[:910,:590].astype('float32')
 pavement=cv2.remap(base,xx+630,np.maximum(yy+140,780),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
 art[floor>0]=pavement[floor>0]
 weight=np.minimum(cv2.distanceTransform(mask,cv2.DIST_L2,5)/4,1)[:,:,None]
 base[140:1050,630:1220]=np.rint(art*weight+base[140:1050,630:1220]*(1-weight)).astype('uint8')
 c=read_chunk(ROOT/'original/rooms/060-big-door/318-big-door-big-door-state-frame0-layer10.chnk');targets=[]
 for t in c['textures']:
  assert t['format']==b'DXT5'
  a=np.array(t['image']);mx,my,inside=scene_maps(c,t);selected=mx!=-1
  paint=cv2.remap(base,mx,my+148,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
  a[selected,:3]=paint[selected];targets.append(a)
 report=chunk_pack(c,targets,out);report.update(builder='entrance-v24',runtime_offset=[0,148],registration=registration)
 for t in report['textures']:t['scope']='Redrawn open leaf and revealed interior, shared pavement and wall backing; original alpha and geometry'
 (out/'extra-chunk-validation.json').write_text(json.dumps([report],indent=2)+'\n')
 packed=read_chunk(out/c['path'].name);packed['vertices'][:,1]+=296
 preview=Image.alpha_composite(Image.open(out/'in-game-texture-preview.png').convert('RGBA'),render(packed,(2220,1200)))
 preview.save(rev/'entrance-open-packed.png')
 print('Entrance open door packed; alpha and geometry preserved.',flush=True)

if __name__=='__main__':main()
