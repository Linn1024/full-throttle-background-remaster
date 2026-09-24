"""Pack night truck state art and register shared bodywork to its background."""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt
from build_reported_states_v2 import pack

def main():
 out=ROOT/'locations/107-barfro-n/custom-v1'
 old=np.array(Image.open(out.parent/'official-remaster.png').convert('RGB'))
 scene=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 for key,relative in [('engine','rooms/107-barfro-n/107-barfro-n_room_pk_a00.dxt'),('hood00','costumes/345-truck-hood-cos/truck-hood-cos_akostume_pk_a00.dxt'),('hood01','costumes/345-truck-hood-cos/truck-hood-cos_akostume_pk_a01.dxt')]:
  source=ROOT/'original'/relative;original=read_dxt(source)[2];h,w=original.shape[:2]
  generated=np.array(Image.open(ROOT/'edited'/f'truck-{key}-v2.png').convert('RGB'))
  if key=='hood01':
   # The generator padded this very wide sprite vertically. Register its single
   # connected visible object to the original alpha bounds, not the full canvas.
   count,labels,stats,_=cv2.connectedComponentsWithStats((generated.max(2)>30).astype('uint8'),8)
   x,y,ww,hh,_=stats[1+np.argmax(stats[1:,4])]
   art=original[:,:,:3].copy()
   art[1:168,1:1130]=cv2.resize(generated[y:y+hh,x:x+ww],(1129,167),interpolation=cv2.INTER_LANCZOS4)
  else:art=cv2.resize(generated,(w,h),interpolation=cv2.INTER_LANCZOS4)
  base=original[:,:,:3].astype('float32');art=art.astype('float32')
  # Preserve original lighting and the animation's teal paint while retaining
  # the generated high-frequency material detail.
  target=original.copy();target[:,:,:3]=np.clip(art+cv2.GaussianBlur(base,(0,0),10)-cv2.GaussianBlur(art,(0,0),10),0,255).astype('uint8')
  if key=='engine':
   yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx+469.5084;my=yy+479.4585
   ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR);mapped=cv2.remap(scene,mx,my,cv2.INTER_LINEAR)
   diff=np.max(np.abs(ref.astype(float)-base),axis=2)
   good=(diff<24)&(cv2.blur(diff.astype('float32'),(9,9))<8)&(original[:,:,3]>0)
   target[:,:,:3][good]=mapped[good]
  pack(source,out,target,original[:,:,3]>0,generated_art=f'truck-{key}-v2.png',scope='truck environment only; original alpha retained')

if __name__=='__main__':main()
