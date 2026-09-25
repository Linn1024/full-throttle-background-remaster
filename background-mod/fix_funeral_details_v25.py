"""Composite reviewed local funeral corrections; retain scene geometry/alpha."""
import json
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT
from build_custom import build
from fix_texture_gutters_v24 import fix

REV=ROOT/'reviews/funeral-v25'

def main():
 base=np.array(Image.open(REV/'before.png').convert('RGB'))
 boxes=json.loads((REV/'boxes.json').read_text());reports=[]
 for key,(x0,y0,x1,y1) in boxes.items():
  ref=base[y0:y1,x0:x1].copy();h,w=ref.shape[:2]
  art=np.array(Image.open(REV/f'{key}-generated.png').convert('RGB'))
  if key=='coffin':
   rows=np.flatnonzero((art.min(2)<230).mean(1)>.75)
   art=art[rows[0]:rows[-1]+1]
  art=cv2.resize(art,(w,h),interpolation=cv2.INTER_LANCZOS4)
  # Targeted edits preserve the crop framing. Register against unchanged
  # material when enough reliable near-identity features survive the edit.
  sift=cv2.SIFT_create(nfeatures=5000);gray=lambda a:cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
  k,d=sift.detectAndCompute(gray(art),None);q,e=sift.detectAndCompute(gray(ref),None)
  matches=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.7*n.distance and np.linalg.norm(np.array(k[m.queryIdx].pt)-q[m.trainIdx].pt)<20]
  report=dict(key=key,method='fixed reference crop',matches=len(matches))
  if len(matches)>=10 and key!='coffin':
   A,ok=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in matches]),np.float32([q[m.trainIdx].pt for m in matches]),ransacReprojThreshold=2)
   if A is not None and ok.sum()>=10 and np.linalg.norm(A[:,:2]-np.eye(2))<.06:
    art=cv2.warpAffine(art,A,(w,h),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101);report.update(method='registered crop',affine=A.tolist(),inliers=int(ok.sum()))
  mask=np.zeros((h,w),np.uint8)
  if key=='statue':
   cv2.ellipse(mask,(240,133),(58,81),0,0,360,1,-1)
   cv2.fillPoly(mask,[np.array([(25,150),(105,150),(115,335),(90,360),(22,348)],np.int32)],1)
  elif key=='bust':cv2.ellipse(mask,(222,170),(45,75),0,0,360,1,-1)
  elif key=='plaque':
   cv2.fillPoly(mask,[np.array([(119,43),(209,43),(216,109),(222,120),(220,178),(152,191),(112,166),(120,129)],np.int32)],1)
  else:
   mask[:]=1;mask[:5]=0;mask[:,:5]=0;mask[:,-5:]=0
  weight=np.minimum(cv2.distanceTransform(mask,cv2.DIST_L2,5)/5,1)[:,:,None]
  result=np.rint(art*weight+ref*(1-weight)).astype('uint8')
  assert np.array_equal(result[mask==0],ref[mask==0])
  base[y0:y1,x0:x1]=result;reports.append(report)
  Image.fromarray(result).save(REV/f'{key}-composited.png')
 dest=ROOT/'locations/074-funeral/custom-remaster-v1.png';Image.fromarray(base).save(dest)
 build('074-funeral');fix('074-funeral')
 packed=Image.open(dest.parent/'custom-v1/in-game-texture-preview.png')
 for key,box in boxes.items():packed.crop(box).save(REV/f'{key}-packed.png')
 (REV/'registration.json').write_text(json.dumps(reports,indent=2)+'\n')
 print('Four funeral details packed; original geometry and alpha retained.',flush=True)

if __name__=='__main__':main()
