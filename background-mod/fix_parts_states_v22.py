"""Register opened engine covers and replace their baked-in background backing."""
import json
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_derby_v21 import register
from build_reported_states_v2 import pack

ROOM='044-cu-parts'
REV=ROOT/'reviews/parts-v22'
# Alpha-component bounds; half-resolution scene origins independently matched
# from unchanged patches. The second large-cover state starts two pixels later.
STATES={1:[(917,1,643,684,1590,528),(1,2,912,777,254,476),(1,781,1043,636,1308,150)],
        2:[(1,1,1041,636,1309,150)]}

def main():
 folder=ROOT/'locations'/ROOM;out=folder/'custom-v1'
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 new=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 canonical=read_dxt(ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a01.dxt')[2]
 art,reg=register(np.array(Image.open(REV/'open-covers-generated.png').convert('RGB')),canonical[:,:,:3],local=False)
 # Keep the original broad lighting; retain generated material detail.
 art=np.clip(art.astype('float32')+.8*(cv2.GaussianBlur(canonical[:,:,:3].astype('float32'),(0,0),20)-cv2.GaussianBlur(art.astype('float32'),(0,0),20)),0,255)
 # Exact puzzle glyphs win over generated lettering. Protect both old and
 # generated glyph footprints, avoiding doubled or altered numbers.
 for x0,y0,x1,y1 in [(1080,360,1410,595),(425,420,800,680),(325,960,835,1190)]:
  a=canonical[y0:y1,x0:x1,:3];b=art[y0:y1,x0:x1]
  mask=((a.max(2)<43)|(b.max(2)<43)).astype('uint8')
  mask=cv2.dilate(mask,np.ones((5,5),np.uint8));weight=cv2.GaussianBlur(mask.astype('float32'),(0,0),1)[:,:,None]
  art[y0:y1,x0:x1]=a*weight+b*(1-weight)
 reports=[];composite=Image.fromarray(new).convert('RGBA')
 for page,states in STATES.items():
  src=ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a{page:02}.dxt';a=read_dxt(src)[2];target=a.copy();editable=np.zeros(a.shape[:2],bool);placements=[]
  for index,(x,y,w,h,sx,sy) in enumerate(states):
   state=a[y:y+h,x:x+w];yy,xx=np.mgrid[:h,:w].astype('float32')
   # Refine the translation against the least-different (unchanged) pixels.
   scores=[]
   for dy in np.arange(-1.5,1.6,.5):
    for dx in np.arange(-1.5,1.6,.5):
     sample=cv2.remap(old,np.float32(sx+dx)+xx*.5,np.float32(sy+dy)+yy*.5,cv2.INTER_LINEAR)
     error=np.max(abs(sample.astype('float32')-state[:,:,:3]),2)[state[:,:,3]>250]
     scores.append((float(np.mean(np.partition(error,int(len(error)*.35))[:int(len(error)*.35)])),sx+dx,sy+dy))
   error,sx,sy=min(scores);mx=np.float32(sx)+xx*.5;my=np.float32(sy)+yy*.5
   backing=cv2.remap(new,mx,my,cv2.INTER_LINEAR);before=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
   if page==1:paint=art[y:y+h,x:x+w]
   else:paint=art[781:781+h,3:3+w] # same cover, two atlas pixels cropped
   delta=np.max(abs(before.astype('float32')-state[:,:,:3]),2)
   foreground=((delta>12)&(cv2.blur(delta,(5,5))>10)).astype('uint8')
   foreground=cv2.morphologyEx(foreground,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
   # Similar dark colors are not evidence that a moving surface is backing.
   # Explicit cover silhouettes prevent holes/seams within the lifted lids.
   if page==1 and index==1:
    cv2.fillPoly(foreground,[np.array([(0,145),(45,62),(165,5),(300,8),(425,80),(520,210),(560,310),(550,375),(455,425),(285,425),(115,345),(0,260)],np.int32)],1)
    cv2.ellipse(foreground,(620,568),(267,190),13,0,360,1,-1)
   elif page==1 and index==0:
    cv2.fillPoly(foreground,[np.array([(305,33),(637,109),(490,356),(361,330),(167,262)],np.int32)],1)
    cv2.fillPoly(foreground,[np.array([(184,273),(498,365),(419,603),(56,507)],np.int32)],1)
   else:
    cv2.fillPoly(foreground,[np.array([(222,49),(935,143),(948,473),(233,299)],np.int32)],1)
   weight=cv2.GaussianBlur(foreground.astype('float32'),(0,0),1.3)
   # Exact background at unchanged patch boundaries; changed silhouettes may
   # legitimately reach the edge and retain their original alpha coverage.
   rgb=paint*weight[:,:,None]+backing*(1-weight[:,:,None])
   target[y:y+h,x:x+w,:3]=np.uint8(np.clip(np.rint(rgb),0,255));editable[y:y+h,x:x+w]=state[:,:,3]>0
   placements.append(dict(rect=[x,y,w,h],scene=[sx,sy],unchanged_error=error))
  decoded=pack(src,out,target,editable,scope='All opened engine covers; shared custom backing; original puzzle glyphs and alpha',registration=reg,placements=placements)
  for i,p in enumerate(placements):
   x,y,w,h=p['rect'];sx,sy=p['scene'];base=Image.fromarray(new).convert('RGBA')
   patch=Image.fromarray(decoded[y:y+h,x:x+w]).resize((round(w/2),round(h/2)),Image.Resampling.LANCZOS)
   base.alpha_composite(patch,(round(sx),round(sy)))
   base.crop((round(sx)-20,round(sy)-20,round(sx+w/2)+20,round(sy+h/2)+20)).save(REV/f'page{page}-state{i}-packed.png')
   if page==1:composite.alpha_composite(patch,(round(sx),round(sy)))
  reports.append(dict(page=page,placements=placements,alpha_exact=True))
 composite.save(REV/'all-open-packed.png');(REV/'validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))

if __name__=='__main__':main()

