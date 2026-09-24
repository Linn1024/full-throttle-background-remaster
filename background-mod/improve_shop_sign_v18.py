"""Integrate reviewed paintings; retain sprite geometry, control masks and alpha."""
import json,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt
from build_custom import build
from build_reported_states_v2 import pack
REV=ROOT/'reviews/shop-v18'

def empty_display(base):
 crop=base[:1060,340:1200].copy()
 empty=np.array(Image.open(REV/'shop-empty-generated.png').convert('RGB').resize((860,1060),Image.Resampling.LANCZOS))
 sift=cv2.SIFT_create(nfeatures=5000)
 k,d=sift.detectAndCompute(cv2.cvtColor(empty,cv2.COLOR_RGB2GRAY),None)
 q,e=sift.detectAndCompute(cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY),None)
 matches=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.7*n.distance]
 A,inliers=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in matches]),np.float32([q[m.trainIdx].pt for m in matches]),ransacReprojThreshold=2)
 assert inliers.sum()>30
 empty=cv2.warpAffine(empty,A,(860,1060),flags=cv2.INTER_LANCZOS4)
 mask=Image.new('L',(860,1060));draw=ImageDraw.Draw(mask)
 draw.polygon([(220,600),(320,568),(330,553),(514,550),(532,566),(532,715),(218,715)],fill=255)
 weight=np.minimum(cv2.distanceTransform((np.array(mask)>0).astype('uint8'),cv2.DIST_L2,5)/14,1)[:,:,None]
 common=np.rint(empty*weight+crop*(1-weight)).astype('uint8')
 blank=base.copy();blank[:1060,340:1200]=common;Image.fromarray(blank).save(REV/'shop-empty-canonical.png')
 # Retain only the box itself; its old cast shadow must not survive removal.
 item=Image.new('L',(860,1060));ImageDraw.Draw(item).polygon([(339,572),(449,570),(497,584),(497,695),(370,698),(339,680)],fill=255)
 item=np.array(item)>0;common[item]=crop[item];base[:1060,340:1200]=common
 return base

def backup(room):
 f=ROOT/'locations'/room
 for name in ['custom-remaster-v1.png','room.json']:
  p=REV/(room+'-before-'+name)
  if not p.exists():shutil.copy2(f/name,p)
 p=REV/(room+'-before-packed.png')
 if not p.exists():shutil.copy2(f/'custom-v1/in-game-texture-preview.png',p)
 return f,np.array(Image.open(p).convert('RGB'))

def room_art():
 f,base=backup('054-souvenir');box=(340,0,1200,1060);x,y,x1,y1=box
 old=base[y:y1,x:x1];art=np.array(Image.open(REV/'shop-generated.png').convert('RGB').resize((860,1060),Image.Resampling.LANCZOS))
 gray=lambda a:cv2.GaussianBlur(cv2.cvtColor(a,cv2.COLOR_RGB2GRAY),(0,0),1.2)
 flow=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(gray(old),gray(art),None)
 flow=np.clip(cv2.GaussianBlur(flow,(0,0),5),-18,18);yy,xx=np.mgrid[:1060,:860].astype('float32')
 art=cv2.remap(art,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101)
 blend=np.clip(np.minimum.reduce([xx,859-xx,1059-yy])/24,0,1)[:,:,None]
 base[y:y1,x:x1]=np.rint(art*blend+old*(1-blend)).astype('uint8')
 base=empty_display(base)
 Image.fromarray(base).save(f/'custom-remaster-v1.png')
 cfg=json.loads((f/'room.json').read_text());cfg['protected']=[];(f/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build('054-souvenir')
 f,base=backup('055-turnstil');box=(1115,150,1310,510);x,y,x1,y1=box
 art=np.array(Image.open(REV/'sign-generated.png').convert('RGB').resize((195,360),Image.Resampling.LANCZOS))
 mask=Image.new('L',(195,360));ImageDraw.Draw(mask).polygon([(12,11),(181,52),(184,337),(11,346)],fill=255)
 m=np.array(mask);weight=np.minimum(cv2.distanceTransform((m>0).astype('uint8'),cv2.DIST_L2,5)/1.5,1)[:,:,None]
 base[y:y1,x:x1]=np.rint(art*weight+base[y:y1,x:x1]*(1-weight)).astype('uint8')
 Image.fromarray(base).save(f/'custom-remaster-v1.png');Image.fromarray(m).save(REV/'sign-mask.png')
 cfg=json.loads((f/'room.json').read_text());cfg['protected']=[r for r in cfg['protected'] if r[0]!=1115];(f/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build('055-turnstil')

def sign_states():
 room='055-turnstil';f=ROOT/'locations'/room;out=f/'custom-v1';src=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt'
 a=read_dxt(src)[2];target=a.copy();editable=np.zeros(a.shape[:2],bool)
 scene=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 # Two geometrically identical sign states, with original brightness difference.
 bright=a[697:1357,965:1355,:3].astype('float32');dim=a[1:661,1333:1723,:3].astype('float32')
 ratio=np.clip((cv2.GaussianBlur(dim,(0,0),3)+10)/(cv2.GaussianBlur(bright,(0,0),3)+10),.35,1.1)
 yy,xx=np.mgrid[:660,:390].astype('float32');paint=cv2.remap(scene,xx*.5+1115,yy*.5+150,cv2.INTER_LINEAR)
 for x,y,r in [(965,697,1),(1333,1,ratio)]:
  valid=a[y:y+660,x:x+390,3]>0
  rgb=np.clip(np.rint(paint*r),0,255).astype('uint8');target[y:y+660,x:x+390,:3][valid]=rgb[valid];editable[y:y+660,x:x+390]=valid
 decoded=pack(src,out,target,editable,scope='Both prize-sign blink states; original alpha and white control masks retained',brightness_states=2)
 p=Image.new('RGB',(390,330))
 for i,(x,y) in enumerate([(965,697),(1333,1)]):p.paste(Image.fromarray(decoded[y:y+660,x:x+390]).resize((195,330)),(i*195,0))
 p.resize((780,660)).save(REV/'prize-blink-packed.png')

def shop_states():
 room='054-souvenir';f=ROOT/'locations'/room;out=f/'custom-v1';src=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt'
 a=read_dxt(src)[2];target=a.copy();editable=np.zeros(a.shape[:2],bool)
 generated=np.array(Image.open(REV/'shop-atlas-generated.png').convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS))
 # Reviewed colored islands only; every white mask is explicitly excluded.
 boxes=[(1,1,174,768),(177,1,105,744),(285,1,160,577),(449,1,320,384),(773,1,240,288),(893,773,320,384),(449,1445,400,384),(853,1445,240,288),(449,1833,240,192)]
 for x,y,w,h in boxes:
  valid=a[y:y+h,x:x+w,3]>0;target[y:y+h,x:x+w,:3][valid]=generated[y:y+h,x:x+w][valid];editable[y:y+h,x:x+w]=valid
 scene=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 # Neon states share one canonical painting. Preserve the original pulse,
 # instead of letting independently generated states change their design.
 for bright,dark,w,h,sx,sy in [((893,773),(449,1),320,384,910,0),((773,1),(853,1445),240,288,630,0)]:
  bx,by=bright;dx,dy=dark;yy,xx=np.mgrid[:h,:w].astype('float32')
  art=cv2.remap(scene,xx*.5+sx,yy*.5+sy,cv2.INTER_LINEAR)
  b=a[by:by+h,bx:bx+w,:3].astype('float32');d=a[dy:dy+h,dx:dx+w,:3].astype('float32')
  ratio=np.clip((cv2.GaussianBlur(d,(0,0),3)+10)/(cv2.GaussianBlur(b,(0,0),3)+10),.25,1.2)
  for (x,y),r in [(bright,1),(dark,ratio)]:target[y:y+h,x:x+w,:3]=np.clip(np.rint(art*r),0,255).astype('uint8')
 # Restore the exact new background wherever an interaction frame shares it.
 # These registrations were checked using isolated edges, not the changed item.
 official=np.array(Image.open(f/'official-remaster.png').convert('RGB'))
 registrations=[(177,1,105,744,937,336),(285,1,160,577,550,817),(449,1445,400,384,670,528),(449,1833,240,192,950,672)]
 for x,y,w,h,sx,sy in registrations:
  yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx*.5+sx;my=yy*.5+sy
  old=cv2.remap(official,mx,my,cv2.INTER_LINEAR);new=cv2.remap(scene,mx,my,cv2.INTER_LINEAR)
  diff=np.max(np.abs(old.astype('float32')-a[y:y+h,x:x+w,:3]),axis=2)
  same=(diff<28)&(cv2.blur(diff,(7,7))<12)
  weight=np.clip(cv2.distanceTransform(same.astype('uint8'),cv2.DIST_L2,5)/6,0,1)
  # Shared outer strips must meet the base without a residual old-color rim.
  edge=(xx<4)|(xx>w-5)|(yy<4)|(yy>h-5);weight[edge&same]=1
  rgb=target[y:y+h,x:x+w,:3];rgb[:]=np.rint(new*weight[:,:,None]+rgb*(1-weight[:,:,None])).astype('uint8')
 # Same canonical wall in both states; only the box differs.
 empty=np.array(Image.open(REV/'shop-empty-canonical.png').convert('RGB'))
 yy,xx=np.mgrid[:384,:400].astype('float32')
 target[1445:1829,449:849,:3]=cv2.remap(empty,xx*.5+670,yy*.5+528,cv2.INTER_LINEAR)
 target[~editable]=a[~editable]
 decoded=pack(src,out,target,editable,scope='Shop doorway, cable, empty merchandise backing, counter and four neon states; white control masks excluded')
 Image.fromarray(decoded).resize((1024,1024)).save(REV/'shop-atlas-packed.png')
 for x,y,w,h,sx,sy in registrations:
  preview=Image.fromarray(scene).convert('RGBA');overlay=Image.fromarray(decoded[y:y+h,x:x+w]).resize((round(w/2),round(h/2)),Image.Resampling.LANCZOS)
  preview.alpha_composite(overlay,(sx,sy));preview.crop((340,0,1200,1120)).save(REV/f'shop-state-{x}-{y}.png')

if __name__=='__main__':room_art();sign_states();shop_states()
