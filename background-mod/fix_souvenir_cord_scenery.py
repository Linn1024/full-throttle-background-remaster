"""Refresh the bunny-absent cord sprite's baked scenery, preserving its cord."""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

room = '054-souvenir'
folder = ROOT/'locations'/room
source = ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
original = read_dxt(source)[2]
old = np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
art = np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
h,w = original.shape[:2]
yy,xx = np.mgrid[:h,:w].astype('float32')
# Registered on the exposed floor beside the cord tip at half atlas scale.
mx,my = xx*.5+407.25, yy*.5+815.75
ref = cv2.remap(old,mx,my,cv2.INTER_LINEAR)
diff = np.max(np.abs(ref.astype(float)-original[:,:,:3]),axis=2)
region = (xx>=285)&(xx<450)&(yy>=1)&(yy<584)&(original[:,:,3]>0)
# Explicit foreground protection lets scenery reach the outer atlas edge.
# A difference threshold here left original border blocks unchanged.
r,g,b = original[:,:,:3].astype(float).transpose(2,0,1)
cord = region & (r>g*1.25) & (r>b*1.4) & (r>40)
cord = cv2.dilate(cord.astype('uint8'),np.ones((7,7),np.uint8))>0
socket = np.zeros((h,w),np.uint8)
cv2.fillPoly(socket,[np.array([[377,58],[396,49],[423,56],[448,64],[448,110],[417,119],[388,108],[375,90]],np.int32)],1)
editable = region & ~cord & (socket==0)
target = original.copy()
mapped = cv2.remap(art,mx,my,cv2.INTER_LINEAR)
target[editable,:3] = mapped[editable]
decoded = pack(source,folder/'custom-v1',target,editable,
               state='bunny absent cord scenery',scale=.5,shift=[407.25,815.75], edge_scenery_included=True)
Image.fromarray(decoded).crop((275,420,455,590)).save(folder/'custom-v1/cord-floor-fixed.png')
