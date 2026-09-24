"""Pack v14 truck open states, registering shared scenery to new rooms."""
import json,shutil
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt
from build_reported_states_v2 import pack

def main():
 rows=json.loads((ROOT/'overlay-audit/registration.json').read_text())
 for room in ['100-mr-truck','191-mr-trkbk']:
  folder=ROOT/'locations'/room;out=folder/'custom-v1'
  source=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt'
  orig=read_dxt(source)[2];h,w=orig.shape[:2]
  backup=ROOT/'reviews/vehicles-v14'/room/source.name
  if (out/source.name).exists() and not backup.exists():shutil.copy2(out/source.name,backup)
  art=np.array(Image.open(ROOT/'edited'/f'{room}-state-v14.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS))
  target=orig.copy();target[:,:,:3]=art
  old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
  scene=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
  c=next(r for r in rows if r['room']==room)['candidates'][0]
  yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx*c['scale']+c['shift'][0];my=yy*c['scale']+c['shift'][1]
  ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR);mapped=cv2.remap(scene,mx,my,cv2.INTER_LINEAR)
  diff=np.max(np.abs(ref.astype(float)-orig[:,:,:3]),axis=2).astype('float32')
  good=(diff<24)&(cv2.blur(diff,(9,9))<8)&(orig[:,:,3]>0)
  # Full registered shared pixels include sprite borders, eliminating old scenery frames.
  target[:,:,:3][good]=mapped[good]
  decoded=pack(source,out,target,orig[:,:,3]>0,generated_art=f'{room}-state-v14.png',shared_scene_pixels=int(good.sum()))
  # Preview actual alternate-state composite in room coordinates.
  rgba=Image.fromarray(decoded)
  scale=c['scale'];rgba=rgba.resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS)
  preview=Image.fromarray(scene).convert('RGBA');preview.alpha_composite(rgba,(round(c['shift'][0]),round(c['shift'][1])))
  preview.convert('RGB').save(ROOT/'reviews/vehicles-v14'/room/'open-state-packed.png')
if __name__=='__main__':main()
