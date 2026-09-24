"""Replace the photo sprite's baked easel scenery, preserving the photo print."""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

room = '065-media-rm'
folder = ROOT/'locations'/room
source = ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
original = read_dxt(source)[2]
art = np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
h, w = original.shape[:2]
yy, xx = np.mgrid[:h, :w].astype('float32')
# Masked template registration against the original easel, half atlas scale.
mx, my = xx*.5+949.5, yy*.5-52.5
region = (xx>=1)&(xx<242)&(yy>=1157)&(yy<1351)&(original[:,:,3]>0)
photo = np.zeros((h,w), np.uint8)
cv2.fillPoly(photo, [np.array([[75,1175],[218,1172],[208,1324],[43,1322]],np.int32)], 1)
photo = cv2.dilate(photo, np.ones((5,5),np.uint8))>0
editable = region & ~photo
target = original.copy()
mapped = cv2.remap(art,mx,my,cv2.INTER_LINEAR)
target[editable,:3] = mapped[editable]
decoded = pack(source,folder/'custom-v1',target,editable,
               state='photo placed on easel',scale=.5,shift=[949.5,-52.5],
               edge_scenery_included=True)
Image.fromarray(decoded).crop((0,1150,256,1360)).save(folder/'custom-v1/photo-scenery-fixed.png')
