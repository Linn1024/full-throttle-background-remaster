"""Transfer only reviewed gray sign wear, including matching state backing."""
import json,shutil,zlib
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt
from build_derby_v21 import register
from build_custom import build
from build_reported_states_v2 import pack
from fix_texture_gutters_v24 import fix
REV=ROOT/'reviews/shop-v27'

def main():
 folder=ROOT/'locations/054-souvenir';out=folder/'custom-v1'
 for name,src in [('source-before.png',folder/'custom-remaster-v1.png'),('atlas-before.dxt',out/'054-souvenir_room_pk_a00.dxt')]:
  if not (REV/name).exists():shutil.copy2(src,REV/name)
 base=np.array(Image.open(REV/'source-before.png').convert('RGB'));before=base.copy();ref=base[:1120,340:1200]
 art,reg=register(np.array(Image.open(REV/'generated.png').convert('RGB')),ref,local=False)
 allowed=np.zeros((1120,860),np.uint8)
 polygons=[[(62,238),(177,244),(187,663),(76,665)],[(651,288),(826,294),(825,532),(652,532)],[(690,530),(812,526),(820,650),(693,660)],[(89,700),(190,695),(191,1032),(113,1036)],[(701,665),(818,660),(840,938),(741,953)],[(301,802),(763,770),(768,842),(305,895)]]
 for points in polygons:cv2.fillPoly(allowed,[np.array(points,np.int32)],1)
 rgb=art.astype(float);difference=np.max(abs(rgb-ref.astype(float)),2)
 candidate=(allowed>0)&(rgb.max(2)-rgb.min(2)<30)&(rgb.mean(2)>60)&(rgb.mean(2)<190)&(difference>22)
 n,labels,stats,_=cv2.connectedComponentsWithStats(candidate.astype('uint8'))
 mask=np.zeros_like(allowed)
 for i in range(1,n):
  if 5<=stats[i,cv2.CC_STAT_AREA]<=500:mask[labels==i]=1
 mask=cv2.dilate(mask,np.ones((3,3),np.uint8))*(allowed>0)
 weight=cv2.GaussianBlur(mask.astype('float32'),(3,3),.6)[:,:,None]
 base[:1120,340:1200]=np.rint(art*weight+ref*(1-weight)).astype('uint8')
 Image.fromarray(base).save(folder/'custom-remaster-v1.png');build('054-souvenir');fix('054-souvenir')
 # Keep every already-improved state intact, adding only the matching stains
 # where the interaction sprite overlaps an edited sign.
 a=read_dxt(REV/'atlas-before.dxt')[2];target=a.copy();editable=np.zeros(a.shape[:2],bool)
 delta=base.astype('float32')-before.astype('float32')
 for x,y,w,h,sx,sy in [(177,1,105,744,937,336),(285,1,160,577,550,817),(449,1445,400,384,670,528),(449,1833,240,192,950,672)]:
  yy,xx=np.mgrid[:h,:w].astype('float32');d=cv2.remap(delta,xx*.5+sx,yy*.5+sy,cv2.INTER_LINEAR)
  target[y:y+h,x:x+w,:3]=np.clip(np.rint(a[y:y+h,x:x+w,:3]+d),0,255).astype('uint8')
 # Repack changed blocks, then retain the current raw bytes everywhere else.
 editable=np.any(target[:,:,:3]!=a[:,:,:3],axis=2)&(a[:,:,3]>0)
 if editable.any():
  # Expand to complete compression blocks while copying current colors.
  hh,ww=editable.shape;blocks=editable.reshape(hh//4,4,ww//4,4).any(axis=(1,3));editable=np.repeat(np.repeat(blocks,4,0),4,1)&(a[:,:,3]>0)
  source=ROOT/'original/rooms/054-souvenir/054-souvenir_room_pk_a00.dxt'
  pack(source,out,target,(a[:,:,3]>0)&(a[:,:,:3].min(2)<225),revision='shop-v27',scope='Existing v18 states with local gray sign wear; original alpha/control masks retained')
  data,raw,_=read_dxt(REV/'atlas-before.dxt');encoded=read_dxt(out/source.name)[1];merged=bytearray(raw)
  for block in np.flatnonzero(blocks):
   at=int(block)*16;merged[at+8:at+16]=encoded[at+8:at+16]
  z=zlib.compressobj(9,zlib.DEFLATED,-15);(out/source.name).write_bytes(data[:12]+z.compress(merged)+z.flush())
  decoded=read_dxt(out/source.name)[2];assert np.array_equal(decoded[:,:,3],a[:,:,3])
  assert np.array_equal(decoded[~np.repeat(np.repeat(blocks,4,0),4,1)],a[~np.repeat(np.repeat(blocks,4,0),4,1)])
 Image.fromarray(base[:1120,340:1200]).save(REV/'shop-wear-preview.png')
 (REV/'validation.json').write_text(json.dumps(dict(registration=reg,stain_pixels=int(mask.sum()),atlas_updated=bool(editable.any()),gameplay_verified=False),indent=2)+'\n')
 print('Sign stains applied:',int(mask.sum()),'pixels',flush=True)

if __name__=='__main__':main()
