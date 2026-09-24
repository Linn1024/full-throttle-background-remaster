"""Refresh baked cargo wall around blueprint sheets; retain sheets and masks."""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

room = '073-cargo'
folder = ROOT/'locations'/room
source = ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
original = read_dxt(source)[2]
h,w = original.shape[:2]
yy,xx = np.mgrid[:h,:w].astype('float32')
# Half-scale registration from three exposed wall strips; refined subpixel.
mx,my = xx*.5+121.25, yy*.5+581.25
art = np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
mapped = cv2.remap(art,mx,my,cv2.INTER_LINEAR)
region = (xx>=1088)&(xx<1828)&(yy<480)&(original[:,:,3]>0)
foreground = np.zeros((h,w),np.uint8)
# Coordinates relative to the inspected blueprint rectangle. Include tape.
polygons = [
 [(61,59),(78,53),(83,31),(104,31),(111,58),(331,79),(366,98),(389,130),(399,342),(415,352),(400,369),(92,379),(83,403),(61,400),(63,376),(44,371),(42,335),(65,290),(77,278),(76,224),(46,240),(43,223),(77,188),(77,140),(63,115)],
 [(390,115),(416,80),(434,86),(429,97),(661,110),(669,104),(713,138),(703,151),(700,323),(720,327),(702,347),(699,371),(481,383),(467,397),(427,372),(424,340),(443,303),(443,172),(424,153)]
]
for points in polygons:
 p=np.array(points,np.int32);p[:,0]+=1088
 cv2.fillPoly(foreground,[p],1)
foreground=cv2.dilate(foreground,np.ones((3,3),np.uint8))>0
editable=region & ~foreground
target=original.copy();target[editable,:3]=mapped[editable]
decoded=pack(source,folder/'custom-v1',target,editable,
             state='blueprint wall scenery',scale=.5,shift=[121.25,581.25],
             scope='wall only; blueprint sheets, tape, character control mask preserved')
Image.fromarray(decoded).crop((1088,0,1828,480)).save(folder/'custom-v1/blueprint-wall-fixed.png')
