"""Refresh registered ending-scene scenery; preserve actors and changed states.

Packing only: samples the revised room art, retaining original alpha and
foreground BC3 blocks. Run after rebuilding the three room backgrounds.
"""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

REGIONS = {
 '099-behind-t': [
  ((1,913,789,1494),(1388.375,-74.625)),
  ((793,913,1755,1393),(582.375,-72.625)),
  ((2,1505,882,1986),(982.375,-370.625)),
 ],
 '123-cargofnt': [
  ((977,1,2017,385),(221.375,47.375)),
  ((493,489,1533,873),(463.375,-196.625)),
  ((541,1097,1581,1481),(439.375,-500.625)),
  ((493,1,973,487),(308.5,526.5)),
  ((217,1097,537,1577),(361.5,315.5)),
 ],
 '173-crgotruk': [((1,1,1120,418),(878.5,386.5))],
}

for room, regions in REGIONS.items():
 folder=ROOT/'locations'/room
 source=ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
 original=read_dxt(source)[2]
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 art=np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
 h,w=original.shape[:2]; yy,xx=np.mgrid[:h,:w].astype('float32')
 target=original.copy(); editable=np.zeros((h,w),bool)
 for bounds,shift in regions:
  x0,y0,x1,y1=bounds;mx=xx*.5+shift[0];my=yy*.5+shift[1]
  region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&(original[:,:,3]>0)
  ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
  diff=np.max(np.abs(ref.astype(float)-original[:,:,:3]),axis=2)
  keep=((diff>22)&region).astype('uint8')
  if room=='173-crgotruk':
   # This overlay is the static truck front, with its original cutout alpha.
   keep[:]=0
  if room=='123-cargofnt' and x0==493 and y0==1:
   # Explicit actor silhouette protects dark clothing that can match scenery.
   points=np.array([[133,102],[244,96],[272,145],[354,146],[381,170],
    [415,166],[430,221],[404,249],[390,302],[443,304],[450,349],
    [402,373],[371,416],[356,483],[175,485],[139,458],[132,403],
    [100,387],[40,363],[22,335],[75,283],[90,220],[115,180]],np.int32)
   points+=np.array([x0,y0]);cv2.fillPoly(keep,[points],1)
  keep=cv2.dilate(keep,np.ones((7,7),np.uint8))>0
  active=region&~keep&(mx>=0)&(my>=0)&(mx<art.shape[1]-1)&(my<art.shape[0]-1)
  mapped=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
  target[active,:3]=mapped[active];editable|=active
 pack(source,folder/'custom-v1',target,editable,
      state='ending scene scenery',registrations=regions,
      edge_scenery_included=True)
