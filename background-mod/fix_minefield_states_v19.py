"""Replace minefield state backing with registered custom ground.

Reuse the existing painting and the original scorch attenuation/item pixels;
no new artwork, geometry or interaction-mask changes are required.
"""
import json
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt
from build_reported_states_v2 import pack

def main():
 room='095-minefld';folder=ROOT/'locations'/room;out=folder/'custom-v1'
 rev=ROOT/'reviews/minefield-v19';rev.mkdir(exist_ok=True,parents=True)
 src=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt'
 a=read_dxt(src)[2];target=a.copy();editable=np.zeros(a.shape[:2],bool)
 official=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 custom=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 registrations=[('crater',1,1,480,192,1193,720),('item',1,197,160,96,1113,1008)]
 reports=[]
 for name,x,y,w,h,sx,sy in registrations:
  yy,xx=np.mgrid[:h,:w].astype('float32');mx=sx+xx*.5;my=sy+yy*.5
  old=cv2.remap(official,mx,my,cv2.INTER_LINEAR).astype('float32')
  new=cv2.remap(custom,mx,my,cv2.INTER_LINEAR).astype('float32')
  state=a[y:y+h,x:x+w,:3].astype('float32')
  # The state adds a dark scorch or item over otherwise identical scenery.
  # Transfer only the scorch's attenuation, retaining the new ground texture.
  lum=np.array([.2126,.7152,.0722],np.float32)
  delta=old@lum-state@lum
  ratio=np.clip((state@lum+1)/(old@lum+1),0,1)
  mark=(delta>7).astype('uint8')
  if name=='crater':
   mark[(xx<45)|(xx>440)|(yy<35)|(yy>180)]=0
  else:
   mark[(xx<17)|(xx>80)|(yy<34)|(yy>90)]=0
  opacity=np.clip((delta-5)/12,0,1)*mark
  opacity=cv2.GaussianBlur(opacity,(0,0),.7)
  rgb=new*(1-opacity[:,:,None]+opacity[:,:,None]*ratio[:,:,None])
  allowed=np.ones((h,w),bool)
  if name=='item':
   # Saturated red/yellow cylinder is gameplay art, not stale backing.
   item=(state[:,:,0]>state[:,:,2]*1.3)&(state[:,:,0]>65)&(xx<80)&(yy>30)
   item=cv2.dilate(item.astype('uint8'),np.ones((3,3),np.uint8))>0
   rgb[item]=state[item];allowed[item]=False
  target[y:y+h,x:x+w,:3]=np.clip(np.rint(rgb),0,255).astype('uint8')
  editable[y:y+h,x:x+w]=allowed
  reports.append(dict(state=name,atlas=[x,y,w,h],scene=[sx,sy],scale=.5))
 decoded=pack(src,out,target,editable,scope='Registered custom ground plus original scorch attenuation; item and control masks protected',registrations=reports)
 for name,x,y,w,h,sx,sy in registrations:
  previews=[]
  for atlas in [a,decoded]:
   im=Image.fromarray(custom).convert('RGBA');patch=Image.fromarray(atlas[y:y+h,x:x+w]).resize((w//2,h//2),Image.Resampling.LANCZOS)
   im.alpha_composite(patch,(sx,sy));im=im.crop((sx-45,sy-45,sx+w//2+45,sy+h//2+45)).convert('RGB');previews.append(im)
  page=Image.new('RGB',(previews[0].width*2,previews[0].height))
  for i,im in enumerate(previews):page.paste(im,(im.width*i,0))
  page.resize((page.width*2,page.height*2)).save(rev/(name+'-before-after.png'))
 print('Minefield states packed; original alpha, item and control pixels verified.')

if __name__=='__main__':main()
