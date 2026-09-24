import sys,cv2,numpy as np
from collections import Counter
from scene_assets import *
official=np.array(Image.open(ROOT/'locations/023-todds/official-remaster.png').convert('RGB'))
gray=cv2.cvtColor(official,cv2.COLOR_RGB2GRAY)
regions={'00':[(1,1,160,1440),(250,1,240,480),(493,1,640,1056),(1137,1,893,964),(250,578,241,480),(493,1061,234,196),(1165,1061,160,192),(330,1249,160,192),(1,1445,642,576),(645,1445,642,576),(1885,1445,160,192)],'01':[(1381,1,560,481),(1,637,321,384)]}
for n,boxes in regions.items():
 _,_,atlas=read_dxt(ROOT/f'original/rooms/023-todds/023-todds_room_pk_a{n}.dxt')
 for x,y,w,h in boxes:
  im=cv2.resize(atlas[y:y+h,x:x+w],(w//2,h//2),interpolation=cv2.INTER_AREA)
  g=cv2.cvtColor(im[:,:,:3],cv2.COLOR_RGB2GRAY);hits=[]
  for yy in range(0,g.shape[0]-24,20):
   for xx in range(0,g.shape[1]-24,20):
    patch=g[yy:yy+24,xx:xx+24]
    if patch.std()<8 or im[yy:yy+24,xx:xx+24,3].min()<250:continue
    score=cv2.matchTemplate(gray,patch,cv2.TM_CCOEFF_NORMED);_,v,_,loc=cv2.minMaxLoc(score)
    if v>.96:hits.append((loc[0]-xx,loc[1]-yy))
  print(n,(x,y,w,h),Counter(hits).most_common(5),flush=True)
