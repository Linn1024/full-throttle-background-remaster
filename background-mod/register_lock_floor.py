import cv2,numpy as np
from scene_assets import *
sift=cv2.SIFT_create(nfeatures=12000)
a=read_dxt(ROOT/'original/rooms/026-gas-gate/026-gas-gate_room_pk_a00.dxt')[2];k,d=sift.detectAndCompute(cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY),(a[:,:,3]>250).astype('uint8')*255)
for n in range(15):
 b=read_dxt(ROOT/f'original/costumes/103-pick-lock-cos/pick-lock-cos_akostume_pk_a{n:02}.dxt')[2];q,e=sift.detectAndCompute(cv2.cvtColor(b[:,:,:3],cv2.COLOR_RGB2GRAY),(b[:,:,3]>250).astype('uint8')*255)
 m=[x for x,y in cv2.BFMatcher().knnMatch(e,d,k=2) if x.distance<.7*y.distance]
 aa=np.float32([q[x.queryIdx].pt for x in m]);bb=np.float32([k[x.trainIdx].pt for x in m]);A,ok=cv2.estimateAffinePartial2D(aa,bb,ransacReprojThreshold=2)
 print(n,len(m),int(ok.sum()) if ok is not None else 0,A.tolist() if A is not None else None,flush=True)
