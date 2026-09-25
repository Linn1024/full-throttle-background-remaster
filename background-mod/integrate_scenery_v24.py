"""Install high-detail funeral sections and the projector's readable door."""
import json,shutil
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT
from build_derby_v21 import register
from build_custom import build
from fix_projector_v23 import main as projector
from fix_texture_gutters_v24 import fix
REV=ROOT/'reviews/seams-v24'

def funeral():
 folder=ROOT/'locations/074-funeral'
 for name in ['custom-remaster-v1.png','room.json']:
  if not (REV/f'funeral-before-{name}').exists():shutil.copy2(folder/name,REV/f'funeral-before-{name}')
 total=np.zeros((1200,7060,3),np.float32);weights=np.zeros((1200,7060,1),np.float32);reports=[]
 for i,x in enumerate([0,1680,3360,5040]):
  old=np.array(Image.open(REV/f'funeral-{i}-original.png').convert('RGB'))
  art,report=register(np.array(Image.open(REV/f'funeral-{i}-generated.png').convert('RGB')),old,local=False)
  w=old.shape[1];weight=np.ones(w,np.float32)
  if i>0:weight[:340]=np.linspace(0,1,340)
  if i<3:weight[-340:]=np.linspace(1,0,340)
  total[:,x:x+w]+=art*weight[None,:,None];weights[:,x:x+w]+=weight[None,:,None];reports.append(report)
 result=np.uint8(np.clip(np.rint(total/np.maximum(weights,1e-6)),0,255));Image.fromarray(result).save(folder/'custom-remaster-v1.png')
 cfg=json.loads((folder/'room.json').read_text());cfg.pop('artwork_crop',None);(folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n')
 build('074-funeral');fix('074-funeral');(REV/'funeral-registration.json').write_text(json.dumps(reports,indent=2))
 for i,x in enumerate([0,1680,3360,5040]):Image.open(folder/'custom-v1/in-game-texture-preview.png').crop((x,0,x+2020,1200)).save(REV/f'funeral-{i}-packed.png')

def door():
 folder=ROOT/'locations/066-projectr';dest=folder/'custom-remaster-v1.png';backup=REV/'projector-before.png'
 if not backup.exists():shutil.copy2(dest,backup)
 base=np.array(Image.open(backup).convert('RGB').resize((2220,1200),Image.Resampling.LANCZOS))
 raw=np.array(Image.open(REV/'door-generated.png').convert('RGB'));valid=np.mean(raw.min(2)<220,axis=0)>.5;columns=np.flatnonzero(valid);raw=raw[:,columns[0]:columns[-1]+1]
 paint=cv2.resize(raw,(190,665),interpolation=cv2.INTER_LANCZOS4)
 mask=np.zeros((665,190),np.uint8);cv2.fillPoly(mask,[np.array([(80,128),(133,151),(133,607),(80,570)],np.int32)],1)
 weight=np.minimum(cv2.distanceTransform(mask,cv2.DIST_L2,5)/3,1)[:,:,None]
 base[325:990,460:650]=np.rint(paint*weight+base[325:990,460:650]*(1-weight)).astype('uint8')
 Image.fromarray(base).save(folder/'closed-door-v24.png')
 # Keep the OPEN doorway in the background; only the engine-controlled
 # closed-door atlas receives the painted panel.
 shutil.copy2(backup,dest)
 projector();fix('066-projectr')
 shutil.copy2(folder/'custom-v1/in-game-texture-preview.png',REV/'projector-door-packed.png')

if __name__=='__main__':
 import sys
 for operation in sys.argv[1:]:globals()[operation]()
