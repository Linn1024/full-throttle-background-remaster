"""Match vehicle overlay scenery to the repainted cabin backgrounds."""
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

for room in ['003-cab','141-cockpit']:
    folder=ROOT/'locations'/room
    source=ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
    original=read_dxt(source)[2]
    old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
    art=np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
    h,w=original.shape[:2]; yy,xx=np.mgrid[:h,:w].astype('float32')
    target=original.copy(); editable=np.zeros((h,w),bool)
    specs=([(648,0,1300,584,663,527.5)] if room=='003-cab' else
           [(0,0,720,680,1547.5,861.5),(724,0,1376,680,33,861.5)])
    for x0,y0,x1,y1,dx,dy in specs:
        mx,my=xx*.5+dx,yy*.5+dy
        region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&(original[:,:,3]>0)
        ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
        mapped=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
        if room=='003-cab':
            r,g,b=original[:,:,:3].astype(float).transpose(2,0,1)
            protect=(b>r+20)&(b>g+10)&region
        else:
            diff=np.max(np.abs(ref.astype(float)-original[:,:,:3]),axis=2)
            protect=(diff>18)&region
        protect=cv2.dilate(protect.astype('uint8'),np.ones((5,5),np.uint8))>0
        select=region&~protect
        target[select,:3]=mapped[select];editable|=select
    pack(source,folder/'custom-v1',target,editable,
         state='vehicle material revision',registration=specs,
         scope='matched scenery; active screen or yoke foreground preserved')
