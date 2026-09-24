"""Integrate generated derby atlases; retain original alpha, shadows and masks."""
import argparse,json,re,shutil
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt
from audit_derby_v21 import REV
from build_reported_states_v2 import pack
from build_derby_v21 import register

GENERATED_IDS=[1,2,3,4,5,6,9,10,11,12,13,14,15,16,17,18,19,20,30,31,32,34,35,36,38,39,40,50,51,52,100,104,105,106,107,108,109,110,111,112,113,114]
VARIANTS={22:[18,19,20],23:[18,19,20],24:[18,19,20],26:[18,19,20],27:[18,19,20],28:[18,19,20],46:[38,39,40],47:[38,39,40],48:[38,39,40],54:[50,51,52],55:[50,51,52],56:[50,51,52]}
FIRST={1:'b22ce1a0-0629-4f03-9ed1-0f2407defa43',2:'2b9fa5e1-7b35-4a3d-ab38-ce8a1964d675'}
def inventory():
 rows=json.loads((REV/'atlas-inventory.json').read_text())+json.loads((REV/'effects-inventory.json').read_text())
 return {r['id']:r for r in rows}
def collect():
 for i in GENERATED_IDS:
  if i in FIRST:src=Path('C:/Users/linn1/.codex/generated_images/01a0cd70-1192-7f73-919f-7322a0c4973c')/f'exec-{FIRST[i]}.png'
  else:
   p=REV/f'generation-{i:02}.json'
   if not p.exists():continue
   hint=json.loads(p.read_text())['output_hint'];src=Path(re.search(r'as (.+?\.png) by default',hint).group(1))
  shutil.copy2(src,REV/f'atlas-{i:02}-generated.png')

def objects(a):
 n,labels,stats,_=cv2.connectedComponentsWithStats((a[:,:,3]>0).astype('uint8'),8)
 result=[]
 for label in range(1,n):
  x,y,w,h,area=map(int,stats[label]);rgb=a[y:y+h,x:x+w,:3][labels[y:y+h,x:x+w]==label]
  if area<150 or np.percentile(rgb.max(axis=1),95)<35:continue
  if (rgb.min(axis=1)>225).mean()>.95:continue
  result.append((label,(x,y,w,h)))
 return labels,result

def repaint(i):
 a=np.array(Image.open(REV/f'atlas-{i:02}-original.png').convert('RGBA'));g=np.array(Image.open(REV/f'atlas-{i:02}-generated.png').convert('RGB'))
 # Atlas positions are fixed; global registration avoids bending individual
 # roll bars or letters to match different painted shading.
 try:art,report=register(g,a[:,:,:3],local=False)
 except (AssertionError,cv2.error):
  art=cv2.resize(g,(a.shape[1],a.shape[0]),interpolation=cv2.INTER_LANCZOS4);report=dict(registration='Exact atlas canvas resize; per-frame review required')
 labels,parts=objects(a);editable=np.isin(labels,[r[0] for r in parts]);target=a.copy()
 # Keep the original one-pixel outside fringe to prevent resampled atlas
 # background colors from leaking into the unchanged transparency edge.
 weight=np.minimum(cv2.distanceTransform(editable.astype('uint8'),cv2.DIST_L2,5)/2,1)[:,:,None]
 target[:,:,:3]=np.rint(art*weight+a[:,:,:3]*(1-weight)).astype('uint8')
 target[~editable]=a[~editable]
 Image.fromarray(target).save(REV/f'atlas-{i:02}-target.png')
 return target,editable,dict(report,visible_objects=len(parts),generated_art=f'atlas-{i:02}-generated.png')

def variant(i,canonical):
 a=np.array(Image.open(REV/f'atlas-{i:02}-original.png').convert('RGBA'));target=a.copy();labels,parts=objects(a);editable=np.zeros(a.shape[:2],bool);report=[]
 candidates=[]
 for j in canonical:
  b=np.array(Image.open(REV/f'atlas-{j:02}-original.png').convert('RGBA'));paint=np.array(Image.open(REV/f'atlas-{j:02}-target.png').convert('RGBA'))
  rgb=b[:,:,:3].copy();rgb[b[:,:,3]==0]=0;candidates.append((j,rgb,paint))
 for label,(x,y,w,h) in parts:
  crop=a[y:y+h,x:x+w,:3].copy();mask=labels[y:y+h,x:x+w]==label;crop[~mask]=0
  best=None
  for j,b,paint in candidates:
   if b.shape[0]<h or b.shape[1]<w:continue
   scores=cv2.matchTemplate(b,crop,cv2.TM_CCOEFF_NORMED);_,score,_,pos=cv2.minMaxLoc(scores)
   if best is None or score>best[0]:best=(score,j,pos,paint)
  score,j,(sx,sy),paint=best
  assert score>.965,(i,label,score)
  region=target[y:y+h,x:x+w];region[mask,:3]=paint[sy:sy+h,sx:sx+w,:3][mask];editable[y:y+h,x:x+w]|=mask
  report.append(dict(canonical=j,score=score,source=[sx,sy,w,h],target=[x,y,w,h]))
 Image.fromarray(target).save(REV/f'atlas-{i:02}-target.png')
 return target,editable,dict(variant_matches=report,visible_objects=len(parts))

def main(ids=None,install=False):
 collect();rows=inventory();reports=[]
 for i in ids or GENERATED_IDS+list(VARIANTS):
  if i in VARIANTS:target,editable,details=variant(i,VARIANTS[i])
  else:
   if not (REV/f'atlas-{i:02}-generated.png').exists():continue
   target,editable,details=repaint(i)
  if install:
   for name in rows[i]['paths']:
    source=ROOT/name;folder=ROOT/'locations'/('056-arena' if int(source.parent.name[:3])<300 else '142-derbypit')/'custom-v1'
    pack(source,folder,target.copy(),editable,scope='Visible derby vehicles/effects only; shadows and controls excluded',**details)
  reports.append(dict(id=i,**details))
  print(i,details if 'variant_matches' not in details else dict(visible_objects=details['visible_objects'],minimum_match=min(r['score'] for r in details['variant_matches'])),flush=True)
  p=REV/'sprite-registration.json';previous=json.loads(p.read_text()) if p.exists() else []
  p.write_text(json.dumps([r for r in previous if r['id']!=i]+[reports[-1]],indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ids',type=int,nargs='+');p.add_argument('--install',action='store_true');a=p.parse_args();main(a.ids,a.install)
