"""Transfer the reviewed color grade without replacing any panorama detail."""
import json
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT
from build_custom import build
from fix_texture_gutters_v24 import fix

REV=ROOT/'reviews/funeral-v26'

def main():
 source=np.array(Image.open(REV/'before.png').convert('RGB'))
 ref=np.array(Image.open(REV/'grade-reference.png').convert('RGB'))
 small=cv2.resize(source,(2048,348),interpolation=cv2.INTER_AREA)
 ref=cv2.resize(ref,(2048,round(ref.shape[0]*2048/ref.shape[1])),interpolation=cv2.INTER_AREA)
 sift=cv2.SIFT_create(nfeatures=10000);gray=lambda a:cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
 k,d=sift.detectAndCompute(gray(ref),None);q,e=sift.detectAndCompute(gray(small),None)
 matches=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.72*n.distance]
 A,ok=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in matches]),np.float32([q[m.trainIdx].pt for m in matches]),ransacReprojThreshold=2)
 assert ok.sum()>100 and np.linalg.norm(A[:,:2]-np.eye(2))<.03
 aligned=cv2.warpAffine(ref,A,(2048,348),flags=cv2.INTER_LINEAR)
 # Fit a single global RGB grade. No generated geometry or texture is used.
 x=small.reshape(-1,3).astype(float)/255;y=aligned.reshape(-1,3).astype(float)/255
 X=np.column_stack([x,np.ones(len(x))]);keep=(x.max(1)>.03)&(x.max(1)<.95)
 for _ in range(4):
  M=np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
  error=np.linalg.norm(X@M-y,axis=1);keep=keep&(error<np.quantile(error[keep],.9))
 full=source.astype(np.float32)/255
 grade=np.clip(full@M[:3]+M[3],0,1)
 result=np.uint8(np.rint(np.clip(full*.25+grade*.75,0,1)*255))
 Image.fromarray(result).save(ROOT/'locations/074-funeral/custom-remaster-v1.png')
 luminance=lambda a:float((a@[.2126,.7152,.0722]).mean())
 report=dict(registration=A.tolist(),inliers=int(ok.sum()),rgb_matrix=M.tolist(),grade_strength=.75,before_mean_luminance=luminance(source),after_mean_luminance=luminance(result),size=[7060,1200])
 assert report['after_mean_luminance']<report['before_mean_luminance']*.95
 (REV/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 build('074-funeral');fix('074-funeral')
 packed=Image.open(ROOT/'locations/074-funeral/custom-v1/in-game-texture-preview.png')
 packed.save(REV/'packed-panorama.png')
 packed.crop((1240,170,3780,1200)).resize((1270,515)).save(REV/'graded-detail.png')
 print(json.dumps(report),flush=True)

if __name__=='__main__':main()
