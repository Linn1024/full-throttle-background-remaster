"""Replace projector scenery states with registered art and shared backing."""
import json, shutil
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_custom import build
from build_reported_states_v2 import pack

ROOM='066-projectr'
REV=ROOT/'reviews/projector-v23'
REELS=[(0,397,1),(0,961,1),(1,1,1),(1,565,1),(1,1129,1),(2,1,1),(2,565,1)]
LEVERS=[(0,1525,1,768,1430,576),(0,1769,1,768,1430,576),
        (1,1693,1,756,1550,582),(1,1,1157,768,1430,576),
        (1,245,1157,756,1550,582),(1,489,1157,756,1550,582)]

def sample(a,w,h,sx,sy):
 yy,xx=np.mgrid[:h,:w].astype('float32')
 return cv2.remap(a,np.float32(sx)+xx*.5,np.float32(sy)+yy*.5,cv2.INTER_LINEAR)

def align(art,ref):
 h,w=ref.shape[:2];art=cv2.resize(art,(w,h),interpolation=cv2.INTER_LANCZOS4)
 sift=cv2.SIFT_create();gray=lambda a:cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
 k,d=sift.detectAndCompute(gray(art),None);q,e=sift.detectAndCompute(gray(ref),None)
 ms=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.8*n.distance
     and np.linalg.norm(np.array(k[m.queryIdx].pt)-q[m.trainIdx].pt)<25]
 assert len(ms)>=8,len(ms)
 A,ok=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in ms]),np.float32([q[m.trainIdx].pt for m in ms]),ransacReprojThreshold=3)
 assert ok.sum()>=8 and np.linalg.norm(A[:,:2]-np.eye(2))<.08,(A,ok.sum())
 return cv2.warpAffine(art,A,(w,h),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101),dict(inliers=int(ok.sum()),affine=A.tolist())

def main():
 folder=ROOT/'locations'/ROOM;out=folder/'custom-v1'
 for name in ['room.json','custom-remaster-v1.png']:
  if not (REV/f'before-{name}').exists():shutil.copy2(folder/name,REV/f'before-{name}')
 cfg=json.loads((folder/'room.json').read_text());cfg['protected']=[]
 (folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build(ROOM)
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 new=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 originals=[read_dxt(ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a{i:02}.dxt')[2] for i in range(3)]
 targets=[a.copy() for a in originals];editable=[np.zeros(a.shape[:2],bool) for a in originals];records=[]
 def put(page,rect,rgb,scene,kind,**details):
  x,y,w,h=rect;targets[page][y:y+h,x:x+w,:3]=np.uint8(np.clip(np.rint(rgb),0,255))
  editable[page][y:y+h,x:x+w]=originals[page][y:y+h,x:x+w,3]>0
  records.append(dict(page=page,rect=rect,scene=scene,kind=kind,**details))
 # Single closed-door overlay contains no animated foreground: use the exact
 # shared room painting over its original silhouette, including foreground cables.
 put(0,[1,1,377,1525],sample(new,377,1525,474,341),[474,341],'door')
 sheet=np.array(Image.open(REV/'reels-generated.png').convert('RGB').resize((2240,2304),Image.Resampling.LANCZOS))
 for i,(page,x,y) in enumerate(REELS):
  state=originals[page][y:y+1152,x:x+560,:3]
  art,reg=align(sheet[i//4*1152:(i//4+1)*1152,i%4*560:(i%4+1)*560],state)
  # A fixed silhouette envelope covers ALL reel/hole/film positions. Never
  # classify moving metal by color similarity to the stationary background.
  mask=np.zeros((1152,560),np.uint8)
  cv2.fillPoly(mask,[np.array([(162,0),(342,0),(416,75),(475,236),(475,510),
     (442,700),(431,842),(508,901),(415,999),(198,1005),(192,761),
     (153,675),(136,472),(136,150)],np.int32)],1)
  weight=cv2.GaussianBlur(mask.astype('float32'),(0,0),2.0)[:,:,None]
  rgb=art*weight+sample(new,560,1152,1390,0)*(1-weight)
  put(page,[x,y,560,1152],rgb,[1390,0],'reel',frame=i,registration=reg)
 # Knobs and arms are painted once per supplied state; everything around them
 # uses the same static cabinet, so slots and feet never jump between styles.
 lever_art=np.array(Image.open(REV/'levers-generated.png').convert('RGB'))
 # Reviewed boundaries in the generated six-strip sheet (normalized).
 cuts=np.array([0,270,540,821,1118,1416,1717])/1717
 boxes=[(90,515,237,615),(86,287,231,390),(37,47,196,143),
        (86,55,231,160),(37,310,196,413),(38,571,196,658)]
 gen_boxes=[(91,484,236,582),(77,274,230,365),(36,37,192,125),
            (74,42,219,134),(26,287,181,381),(26,517,180,618)]
 for i,(page,x,y,h,sx,sy) in enumerate(LEVERS):
  state=originals[page][y:y+h,x:x+240,:3];back=sample(new,240,h,sx,sy);before=sample(old,240,h,sx,sy)
  x0,y0,x1,y1=boxes[i];delta=np.max(abs(state.astype('float32')-before),2)
  mask=np.zeros((h,240),np.uint8);mask[y0:min(y1,h),x0:x1]=(delta[y0:min(y1,h),x0:x1]>9).astype('uint8')
  mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
  contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  mask[:]=0;cv2.drawContours(mask,[max(contours,key=cv2.contourArea)],-1,1,-1)
  bx,by,bw,bh=cv2.boundingRect(mask)
  piece=lever_art[:,round(cuts[i]*lever_art.shape[1]):round(cuts[i+1]*lever_art.shape[1])]
  piece=cv2.resize(piece,(240,768),interpolation=cv2.INTER_LANCZOS4)
  gx0,gy0,gx1,gy1=gen_boxes[i];paint=cv2.resize(piece[gy0:gy1,gx0:gx1],(bw,bh),interpolation=cv2.INTER_LANCZOS4)
  layer=back.copy();layer[by:by+bh,bx:bx+bw]=paint
  weight=np.minimum(cv2.distanceTransform(mask,cv2.DIST_L2,5)/2,1)[:,:,None]
  put(page,[x,y,240,h],layer*weight+back*(1-weight),[sx,sy],'lever',frame=i,lever_bounds=[bx,by,bw,bh])
 # Dark/blue viewing windows remain distinct. Reuse detailed frame edges and
 # lens hardware, preserving the original interior state tint.
 for x,y,w,h,sx,sy in [(397,1157,289,149,768,421.5),(1,1529,289,149,768,421.5),
                       (1505,1181,172,191,1322,432),(1109,1553,172,191,1322,432)]:
  state=originals[0][y:y+h,x:x+w,:3];before=sample(old,w,h,sx,sy);back=sample(new,w,h,sx,sy)
  # The window blue areas carry state changes; preserve them while transferring
  # local detail and tint from the improved frame/lens.
  delta=state.astype('float32')-before.astype('float32')
  smooth=cv2.GaussianBlur(delta,(0,0),2)
  rgb=np.clip(back.astype('float32')+smooth,0,255)
  put(0,[x,y,w,h],rgb,[sx,sy],'window')
 decoded=[]
 for page in range(3):
  src=ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a{page:02}.dxt'
  decoded.append(pack(src,out,targets[page],editable[page],revision='projector-v23',scope='All scenery states; original alpha and white control masks preserved',states=[r for r in records if r['page']==page]))
 def preview(reel,lever):
  base=Image.fromarray(new).convert('RGBA')
  for r in records:
   if r['kind']=='reel' and r['frame']!=reel:continue
   if r['kind']=='lever' and r['frame'] not in lever:continue
   if r['kind']=='window':continue
   x,y,w,h=r['rect'];sx,sy=r['scene'];patch=Image.fromarray(decoded[r['page']][y:y+h,x:x+w]).resize((round(w/2),round(h/2)),Image.Resampling.LANCZOS)
   base.alpha_composite(patch,(round(sx),round(sy)))
  return base
 frames=[preview(i,[1,4]) for i in range(7)]
 frames[0].save(REV/'room-packed.png')
 crops=[f.crop((1365,0,1695,980)).resize((396,1176)) for f in frames]
 crops[0].save(REV/'reels-packed.gif',save_all=True,append_images=crops[1:],duration=150,loop=0)
 for i,f in enumerate(frames):f.crop((1365,0,1695,590)).save(REV/f'reel-{i}-packed.png')
 sheet=Image.new('RGB',(1000,480))
 for i,lever in enumerate([[0,5],[1,4],[3,2]]):
  im=preview(0,lever).crop((1410,550,1700,995));im.thumbnail((330,475));sheet.paste(im,(i*333,0))
 sheet.save(REV/'levers-packed.png')
 (REV/'validation.json').write_text(json.dumps(dict(states=records,atlas_count=3,alpha_exact=True,control_masks_exact=True,gameplay_verified=False),indent=2))
 print('Packed',len(records),'scenery states')

if __name__=='__main__':main()
