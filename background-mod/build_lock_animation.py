"""Register closed-door animation scenery; keep character pixels and alpha."""
import json,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

def main():
 folder=ROOT/'locations/026-gas-gate';out=folder/'custom-v1'
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'));art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 sift=cv2.SIFT_create(nfeatures=8000);k,d=sift.detectAndCompute(cv2.cvtColor(old,cv2.COLOR_RGB2GRAY),None)
 reports=json.loads((out/'overlay-validation.json').read_text())
 for n in range(11,15):
  source=f'costumes/103-pick-lock-cos/pick-lock-cos_akostume_pk_a{n:02}.dxt';path=ROOT/'original'/source
  data,raw,a=read_dxt(path);h,w=a.shape[:2];q,e=sift.detectAndCompute(cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY),(a[:,:,3]>250).astype('uint8')*255)
  matches=[m for m,j in cv2.BFMatcher().knnMatch(e,d,k=2) if m.distance<.65*j.distance]
  aa=np.float32([q[m.queryIdx].pt for m in matches]);bb=np.float32([k[m.trainIdx].pt for m in matches]);A,inliers=cv2.estimateAffine2D(aa,bb,ransacReprojThreshold=2)
  ok=inliers.ravel()>0;assert ok.sum()>=20 and np.max(np.abs(A[:,:2]-np.eye(2)*.5))<.005
  shift=np.median(bb[ok]-aa[ok]*.5,axis=0);yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx*.5+shift[0];my=yy*.5+shift[1]
  before=cv2.remap(old,mx,my,cv2.INTER_LINEAR);after=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
  low=aa[ok].min(0)-32;high=aa[ok].max(0)+32
  region=(xx>=low[0])&(xx<=high[0])&(yy>=low[1])&(yy<=high[1])
  diff=np.max(np.abs(a[:,:,:3].astype(float)-before),axis=2)
  eligible=(region&(diff<24)&(a[:,:,3]==255)).astype('uint8')
  eligible=cv2.erode(eligible,np.ones((5,5),np.uint8));blend=np.minimum(cv2.distanceTransform(eligible,cv2.DIST_L2,5)/8,1)[:,:,None]
  target=a.copy();target[:,:,:3]=np.rint(after*blend+a[:,:,:3]*(1-blend)).astype('uint8')
  png=out/(path.name+'.png');Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
  encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);changed=np.zeros((h,w),bool);count=0
  for by in range(h//4):
   for bx in range(w//4):
    sl=(slice(by*4,by*4+4),slice(bx*4,bx*4+4));at=(by*(w//4)+bx)*16
    if not eligible[sl].all():encoded[at:at+16]=raw[at:at+16]
    else:encoded[at:at+8]=raw[at:at+8];changed[sl]=True;count+=1
  assert count>500
  z=zlib.compressobj(9,zlib.DEFLATED,-15);dest=out/path.name;dest.write_bytes(data[:12]+z.compress(encoded)+z.flush())
  _,_,decoded=read_dxt(dest);assert np.array_equal(a[:,:,3],decoded[:,:,3]);assert np.array_equal(a[~changed],decoded[~changed])
  reports=[r for r in reports if r['file']!=path.name]+[dict(file=path.name,source=source,changed_blocks=count,alpha_preserved=True,excluded_pixels_identical=True,registration_inliers=int(ok.sum()))]
  im=Image.fromarray(decoded);im.thumbnail((900,900));im.save(out/f'lock-state-{n}-atlas.png')
  print(n,count,shift.tolist(),flush=True)
 (out/'overlay-validation.json').write_text(json.dumps(reports,indent=2))

if __name__=='__main__':main()
