"""Offline, read-only registration audit of all room object atlases."""
import json
from collections import Counter
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scene_assets import ROOT, read_dxt

OUT=ROOT/'overlay-audit'

def main():
 OUT.mkdir(exist_ok=True)
 sift=cv2.SIFT_create(nfeatures=12000,contrastThreshold=.025)
 matcher=cv2.BFMatcher()
 rows=[];cache={};thumbs=[]
 for path in sorted((ROOT/'original/rooms').glob('*/*.dxt')):
  room=path.parent.name;folder=ROOT/'locations'/room
  bg=folder/'official-remaster.png'
  if room=='010-dumpster':bg=ROOT/'scene/official-remaster.png'
  if not bg.exists():
   rows.append(dict(room=room,file=path.name,status='no-background-reference'));continue
  if room not in cache:
   ref=np.array(Image.open(bg).convert('RGB'))
   kp,des=sift.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY),None)
   cache[room]=(ref,kp,des)
  ref,kp,des=cache[room]
  _,_,atlas=read_dxt(path)
  ak,ad=sift.detectAndCompute(cv2.cvtColor(atlas[:,:,:3],cv2.COLOR_RGB2GRAY),(atlas[:,:,3]>250).astype('uint8')*255)
  candidates=[]
  if ad is not None and des is not None:
   matches=[m for m,n in matcher.knnMatch(ad,des,k=2) if m.distance<.65*n.distance]
   for scale in (.5,1.):
    pairs=[(ak[m.queryIdx].pt,kp[m.trainIdx].pt) for m in matches if abs(kp[m.trainIdx].size/ak[m.queryIdx].size-scale)<scale*.18]
    if len(pairs)<5:continue
    aa=np.array([a for a,b in pairs]);bb=np.array([b for a,b in pairs]);delta=bb-aa*scale
    bins=Counter(map(tuple,np.rint(delta/3).astype(int)))
    used=[]
    for key,count in bins.most_common():
     near=np.linalg.norm(delta-np.array(key)*3,axis=1)<4
     if near.sum()<5:continue
     shift=np.median(delta[near],axis=0)
     if any(np.linalg.norm(shift-u)<6 for u in used):continue
     used.append(shift)
     pts=aa[near];span=np.ptp(pts,axis=0)
     if min(span)<12:continue
     candidates.append(dict(scale=scale,shift=shift.tolist(),matches=int(near.sum()),atlas_bounds=[*np.floor(pts.min(0)).astype(int).tolist(),*np.ceil(pts.max(0)).astype(int).tolist()]))
  row=dict(room=room,file=path.name,status='candidate' if candidates else 'no-confident-match',candidates=candidates)
  rows.append(row)
  if candidates:
   im=Image.fromarray(atlas);im.thumbnail((360,300));tile=Image.new('RGB',(400,340),(45,45,45));tile.paste(im,(0,30),im.getchannel('A'));d=ImageDraw.Draw(tile);d.text((4,4),path.stem,fill='white')
   d.text((4,320),f'{len(candidates)} mappings; {sum(c["matches"] for c in candidates)} matches',fill='white');thumbs.append(tile)
  print(room,path.name,len(candidates),flush=True)
  (OUT/'registration.json').write_text(json.dumps(rows,indent=2))
 for start in range(0,len(thumbs),12):
  page=Image.new('RGB',(1600,1020),(25,25,25))
  for i,t in enumerate(thumbs[start:start+12]):page.paste(t,((i%4)*400,(i//4)*340))
  page.save(OUT/f'candidates-{start//12+1}.jpg')
 print('Atlases',len(rows),'with candidates',sum(bool(r.get('candidates')) for r in rows))

if __name__=='__main__':main()
