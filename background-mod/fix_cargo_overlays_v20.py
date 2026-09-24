"""Restore cargo-hold scenery overlays without changing characters or geometry."""
import json,struct,subprocess,zlib
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_chunk,read_dxt,triangle_pixels,render
from build_reported_states_v2 import pack
ROOM='073-cargo';F=ROOT/'locations'/ROOM;OUT=F/'custom-v1';REV=ROOT/'reviews/cargo-v20'

def diagrams():
 src=ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a00.dxt';a=read_dxt(src)[2];target=a.copy()
 new=np.array(Image.open(OUT/'in-game-texture-preview.png').convert('RGB'))
 yy,xx=np.mgrid[:468,:720].astype('float32');ground=cv2.remap(new,670+xx*.5,582+yy*.5,cv2.INTER_LINEAR)
 art=np.array(Image.open(REV/'diagrams-generated.png').convert('RGB').resize((720,472),Image.Resampling.LANCZOS))[:468]
 mask=Image.new('L',(720,468));d=ImageDraw.Draw(mask)
 d.polygon([(34,27),(68,28),(75,53),(324,55),(355,77),(380,106),(386,339),(378,362),(405,367),(392,381),(363,377),(55,379),(49,392),(35,383),(38,368),(29,358),(32,321),(51,291),(51,116),(30,88)],fill=255)
 d.polygon([(402,42),(423,45),(415,53),(678,66),(706,92),(691,111),(694,343),(710,357),(681,375),(440,385),(422,397),(393,375),(386,357),(401,333),(410,159),(380,78)],fill=255)
 weight=np.minimum(cv2.distanceTransform((np.array(mask)>0).astype('uint8'),cv2.DIST_L2,5)/2,1)[:,:,None]
 target[1:469,1097:1817,:3]=np.rint(art*weight+ground*(1-weight)).astype('uint8')
 editable=np.zeros(a.shape[:2],bool);editable[1:469,1097:1817]=True
 decoded=pack(src,OUT,target,editable,scope='Blueprints and registered wall backing only; character silhouette mask untouched',scene_origin=[670,582])
 return decoded

def pipes():
 src=ROOT/f'original/rooms/{ROOM}/386-cargo-pipe-shaft-frame0-layer20.chnk';c=read_chunk(src)
 old=np.array(Image.open(F/'official-remaster.png').convert('RGB'));new=np.array(Image.open(OUT/'in-game-texture-preview.png').convert('RGB'))
 art=np.array(Image.open(REV/'pipe-generated.png').convert('RGB').resize((2220,1200),Image.Resampling.LANCZOS))
 reference=np.array(Image.open(REV/'pipe-edit-target.png').convert('RGB'))
 # Register the generated material pass to the original silhouettes.
 sift=cv2.SIFT_create(nfeatures=8000)
 k,d=sift.detectAndCompute(cv2.cvtColor(art,cv2.COLOR_RGB2GRAY),None)
 q,e=sift.detectAndCompute(cv2.cvtColor(reference,cv2.COLOR_RGB2GRAY),None)
 matches=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.7*n.distance]
 A,ok=cv2.estimateAffinePartial2D(np.float32([k[m.queryIdx].pt for m in matches]),np.float32([q[m.trainIdx].pt for m in matches]),ransacReprojThreshold=3)
 assert ok.sum()>40
 art=cv2.warpAffine(art,A,(2220,1200),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101)
 # Dark pipe/shaft faces can match the dark wall numerically. A difference
 # test alone fragments them, so retain their reviewed full silhouettes.
 objects=Image.new('L',(2220,1200));draw=ImageDraw.Draw(objects)
 draw.line([(0,214),(260,311),(493,393),(742,456),(833,520),(1130,566),(1390,585),(1500,646),(1780,688),(2150,735)],fill=255,width=46,joint='curve')
 draw.polygon([(1320,185),(1465,185),(1550,275),(1825,305),(1870,385),(1850,565),(1640,545),(1450,475),(1310,430)],fill=255)
 objects=cv2.GaussianBlur(np.array(objects).astype('float32')/255,(0,0),3)
 payloads=[];reports=[]
 for i,t in enumerate(c['textures']):
  a=np.array(t['image']);h,w=a.shape[:2];mx=np.zeros((h,w),np.float32);my=mx.copy();valid=np.zeros((h,w),bool)
  for ids in c['indices'][t['first']:t['first']+t['count']].reshape(-1,3):
   v=c['vertices'][ids];r=triangle_pixels(v[:,2:]*(w,h),w,h)
   if r is None:continue
   lo,hi,weights,inside=r;xy=weights@v[:,:2]/2;xy[:,:,1]+=164
   sl=np.s_[lo[1]:hi[1],lo[0]:hi[0]];mx[sl][inside]=xy[:,:,0][inside];my[sl][inside]=xy[:,:,1][inside];valid[sl]|=inside
  before=cv2.remap(old,mx,my,cv2.INTER_LINEAR);after=cv2.remap(new,mx,my,cv2.INTER_LINEAR);paint=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
  diff=np.max(abs(before.astype('float32')-a[:,:,:3]),axis=2)
  foreground=(diff>24)&(cv2.blur(diff,(5,5))>15)&valid&(a[:,:,3]>0)
  n,labels,stats,_=cv2.connectedComponentsWithStats(foreground.astype('uint8'),8);keep=np.zeros((h,w),np.uint8)
  for j in range(1,n):
   if stats[j,4]>75:keep[labels==j]=1
  weight=cv2.GaussianBlur(cv2.dilate(keep,np.ones((3,3),np.uint8)).astype('float32'),(0,0),.7)[:,:,None]
  weight=np.maximum(weight,cv2.remap(objects,mx,my,cv2.INTER_LINEAR)[:,:,None])
  target=a.copy();target[:,:,:3]=np.rint(paint*weight+after*(1-weight)).astype('uint8');editable=valid&(a[:,:,3]>0);target[~editable]=a[~editable]
  png=OUT/f'cargo-pipe-v20-{i}.png';Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(OUT),str(png)],check=True,capture_output=True)
  enc=bytearray(png.with_suffix('.dds').read_bytes()[128:]);changed=np.zeros((h,w),bool)
  for by in range(h//4):
   for bx in range(w//4):
    sl=np.s_[by*4:by*4+4,bx*4:bx*4+4];at=(by*(w//4)+bx)*16
    if not editable[sl].any() or ((~editable[sl])&(a[sl][:,:,3]>0)).any():enc[at:at+16]=t['raw'][at:at+16]
    else:enc[at:at+8]=t['raw'][at:at+8];changed[sl]=True
  decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(enc),'bcn',(3,'DXT5')))
  assert np.array_equal(decoded[:,:,3],a[:,:,3]);assert np.array_equal(decoded[~changed],a[~changed])
  z=zlib.compressobj(9,zlib.DEFLATED,-15);p=t['payload'][:12]+z.compress(enc)+z.flush();payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
  reports.append(dict(alpha_preserved=True,protected_foreground_identical=True,scope='Intentional pipe material redraw; excluded pixels unchanged',changed_blocks=int(changed.sum()//16)))
 dest=OUT/src.name;dest.write_bytes(c['header']+b''.join(payloads));assert read_chunk(dest)['header']==c['header']
 report=dict(file=src.name,builder='cargo-v20',textures=reports,gameplay_verified=False)
 path=OUT/'extra-chunk-validation.json';existing=json.loads(path.read_text()) if path.exists() else []
 path.write_text(json.dumps([r for r in existing if r['file']!=src.name]+[report],indent=2))
 return read_chunk(dest)

def main():
 atlas=diagrams();c=pipes();c['vertices'][:,1]+=328
 base=Image.open(OUT/'in-game-texture-preview.png').convert('RGBA');base=Image.alpha_composite(base,render(c,(2220,1200)))
 base.alpha_composite(Image.fromarray(atlas[1:469,1097:1817]).resize((360,234),Image.Resampling.LANCZOS),(670,582))
 base.save(REV/'packed-scene.png');base.resize((1110,600)).save(REV/'packed-preview.png')
 print('Cargo blueprint and pipe overlays packed; alpha, geometry and excluded pixels preserved.')

if __name__=='__main__':main()
