"""Register derby paintings to native room coordinates, then pack existing UVs."""
import argparse,json,shutil,re
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt,read_chunk,render
from audit_derby_v21 import ROOMS,REV
from build_custom import build

def register(art,reference,local=True):
 h,w=reference.shape[:2];art=cv2.resize(art,(w,h),interpolation=cv2.INTER_LANCZOS4)
 scale=min(1,1600/w);size=(round(w*scale),round(h*scale))
 a=cv2.resize(art,size);b=cv2.resize(reference,size)
 gray=lambda im:cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
 sift=cv2.SIFT_create(nfeatures=12000);k,d=sift.detectAndCompute(gray(a),None);q,e=sift.detectAndCompute(gray(b),None)
 matches=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.72*n.distance]
 A,ok=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in matches]),np.float32([q[m.trainIdx].pt for m in matches]),ransacReprojThreshold=3)
 assert A is not None and ok.sum()>20,(len(matches),None if ok is None else ok.sum())
 assert np.linalg.norm(A[:,:2]-np.eye(2))<.15,A
 A[:,2]/=scale;art=cv2.warpAffine(art,A,(w,h),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101)
 report=dict(inliers=int(ok.sum()),affine=A.tolist(),target_size=[w,h])
 if local:
  a=cv2.resize(art,size)
  norm=lambda im:cv2.GaussianBlur(gray(im),(0,0),1.5)
  flow=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(norm(b),norm(a),None)
  flow=cv2.GaussianBlur(flow,(0,0),10)
  mag=np.linalg.norm(flow,axis=2);flow*=np.minimum(1,24/np.maximum(mag,.001))[:,:,None]
  report['local_displacement_median_px']=float(np.median(mag)/scale);report['local_displacement_p95_px']=float(np.percentile(mag,95)/scale)
  flow=cv2.resize(flow,(w,h))/scale;yy,xx=np.mgrid[:h,:w].astype('float32')
  art=cv2.remap(art,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101)
 return art,report

def backgrounds(install=False):
 reports=[];sheet=Image.new('RGB',(1500,3*435),'#222222');d=ImageDraw.Draw(sheet)
 for i,room in enumerate(ROOMS):
  folder=ROOT/'locations'/room;cfg=json.loads((folder/'room.json').read_text());size=tuple(cfg['size'])
  art=np.array(Image.open(REV/f'{room}-generated.png').convert('RGB'));old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
  assert old.shape[:2]==(size[1],size[0])
  # Rigid registration preserves straight arena lines. Dense texture flow can
  # mistake freshly painted asphalt detail for geometry and bend the grid.
  result,report=register(art,old,local=False);report.update(room=room,generated_size=[art.shape[1],art.shape[0]])
  if room=='142-derbypit' and (REV/'generation-corley-sign.json').exists():
   hint=json.loads((REV/'generation-corley-sign.json').read_text())['output_hint'];path=Path(re.search(r'as (.+?\.png) by default',hint).group(1));shutil.copy2(path,REV/'corley-sign-generated.png')
   sign=np.array(Image.open(path).convert('RGB'));sh,sw=sign.shape[:2]
   # Crop the painted sign face, excluding the generator's white letterbox.
   sign=sign[round(sh*.294):round(sh*.696),round(sw*.038):round(sw*.939)]
   x0,y0,x1,y1=3023,53,3283,96;sign=cv2.resize(sign,(x1-x0,y1-y0),interpolation=cv2.INTER_AREA)
   yy,xx=np.mgrid[:y1-y0,:x1-x0];edge=np.minimum.reduce([xx+1,yy+1,x1-x0-xx,y1-y0-yy]);weight=np.minimum(edge/1.5,1)[:,:,None]
   result[y0:y1,x0:x1]=np.rint(sign*weight+result[y0:y1,x0:x1]*(1-weight)).astype('uint8')
   report['corley_sign_corrected']=True
  Image.fromarray(result).save(REV/f'{room}-registered.png');reports.append(report)
  im=Image.fromarray(result);im.thumbnail((748,408));x=i%2*750;y=i//2*435;sheet.paste(im,(x,y+24));d.text((x+5,y+5),room,fill='white')
  if install:
   for name in ['custom-remaster-v1.png','room.json']:
    backup=REV/f'{room}-before-{name}'
    if not backup.exists():shutil.copy2(folder/name,backup)
   Image.fromarray(result).save(folder/'custom-remaster-v1.png');cfg['protected']=[];cfg.pop('artwork_crop',None);cfg.pop('protected_polygons',None)
   (folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build(room)
  print(room,report,flush=True)
 sheet.save(REV/'backgrounds-registered.jpg')
 p=REV/'background-registration.json';previous=json.loads(p.read_text()) if p.exists() else []
 p.write_text(json.dumps([r for r in previous if r['room'] not in [v['room'] for v in reports]]+reports,indent=2))

def state_review():
 sheet=Image.new('RGB',(1200,900),'#444444');d=ImageDraw.Draw(sheet)
 for i,room in enumerate(['056-arena','057-demowall']):
  p=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt';a=read_dxt(p)[2];im=Image.fromarray(a);im.save(REV/f'{room}-atlas-original.png');im.thumbnail((580,850));sheet.paste(im,(i*600,40),im);d.text((i*600+5,5),room,fill='white')
 sheet.save(REV/'room-atlases.jpg')
 for p in sorted((ROOT/'original/rooms/059-rips-box').glob('extra_tvmonitors_f*.chnk')):
  if p.stat().st_size<20:continue
  c=read_chunk(p);im=render(c,(2220,1200));im.save(REV/(p.stem+'.png'))
 print('State references saved',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');p.add_argument('--states',action='store_true');a=p.parse_args()
 if a.states:state_review()
 else:backgrounds(a.install)
