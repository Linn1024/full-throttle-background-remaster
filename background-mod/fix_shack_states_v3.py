"""Integrate coherent generated porch/debris art with unchanged sprite geometry."""
import json,struct,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,read_dxt,render,triangle_pixels
from build_reported_states_v2 import pack

ROOM='018-mo-shack'
FOLDER=ROOT/'locations'/ROOM
OUT=FOLDER/'custom-v1'
INPUT=ROOT/'reviews/static-sprites-v3'

def rgb(path,size=None):
 im=Image.open(path).convert('RGB')
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 return np.array(im)

def chunk_pack(chunk,targets):
 payloads=[];checks=[]
 for i,(tex,target) in enumerate(zip(chunk['textures'],targets)):
  original=np.array(tex['image']);h,w=original.shape[:2]
  png=OUT/f'{chunk["path"].stem}-texture{i}.png';Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(OUT),str(png)],check=True,capture_output=True)
  encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);raw=tex['raw'];count=0
  for y in range(h//4):
   for x in range(w//4):
    at=(y*(w//4)+x)*16
    if not original[y*4:y*4+4,x*4:x*4+4,3].any():encoded[at:at+16]=raw[at:at+16]
    else:encoded[at:at+8]=raw[at:at+8];count+=1
  decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(encoded),'bcn',(3,'DXT5')))
  assert np.array_equal(original[:,:,3],decoded[:,:,3])
  z=zlib.compressobj(9,zlib.DEFLATED,-15);p=tex['payload'][:12]+z.compress(encoded)+z.flush()
  payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
  checks.append(dict(texture=i,changed_blocks=count,alpha_preserved=True,protected_foreground_identical=True))
 dest=OUT/chunk['path'].name;dest.write_bytes(chunk['header']+b''.join(payloads))
 assert read_chunk(dest)['header']==chunk['header']
 return dict(file=dest.name,textures=checks,builder='static-sprites-v3',scope='environment debris only',gameplay_verified=False)

def main():
 old=rgb(FOLDER/'official-remaster.png');art=rgb(OUT/'in-game-texture-preview.png')
 broken=rgb(INPUT/'shack-broken-generated.png',(2220,1200))
 refbroken=rgb(INPUT/'shack-broken-input.png')
 # Keep the new debris within the existing room's broad palette/exposure.
 # This is color registration to the source, not a new painted texture.
 broken=np.clip(broken.astype(float)+cv2.GaussianBlur(refbroken.astype(float),(0,0),18)-cv2.GaussianBlur(broken.astype(float),(0,0),18),0,255).astype('uint8')
 reports=[]
 shifts={10:(1246.4,148.2),20:(1346.35,154.19),30:(1401.43,171.95),40:(1371.33,148.12)}
 for layer,shift in shifts.items():
  c=read_chunk(ROOT/f'original/rooms/{ROOM}/124-debris-image-frame0-layer{layer}.chnk');targets=[]
  for t in c['textures']:
   a=np.array(t['image']);h,w=a.shape[:2];target=a.copy()
   for inds in c['indices'][t['first']:t['first']+t['count']].reshape(-1,3):
    v=c['vertices'][inds];r=triangle_pixels(v[:,2:]*(w,h),w,h)
    if r is None:continue
    lo,hi,weights,inside=r;xy=weights@v[:,:2]/2+shift
    mx=xy[:,:,0].astype('float32');my=xy[:,:,1].astype('float32');sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]))
    sampled=cv2.remap(broken,mx,my,cv2.INTER_LINEAR)
    target[sl][:,:,:3][inside]=sampled[inside]
   targets.append(target)
  reports.append(chunk_pack(c,targets))
 (OUT/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2))
 registrations={
  0:[((0,0,802,1825),(1469.1,95.4)),((804,0,1448,1570),(1107.14,95.43))],
  1:[((0,0,692,1400),(1469.16,131.0)),((694,0,1384,1400),(1123.16,131.0)),((1386,0,1970,965),(857.4,143.85))],
  2:[((1060,0,1850,790),(863.48,527.32)),((0,790,520,1610),(1389.16,123.64))]
 }
 for n,regions in registrations.items():
  src=ROOT/f'original/rooms/{ROOM}/{ROOM}_room_pk_a{n:02}.dxt';a=read_dxt(src)[2];h,w=a.shape[:2]
  target=read_dxt(FOLDER/'before-static-v3/custom-v1'/src.name)[2].copy()
  if n==1:
   target[:,:,:3]=rgb(INPUT/'shack-porch-generated.png',(w,h))
  yy,xx=np.mgrid[:h,:w].astype('float32')
  for bounds,shift in regions:
   x0,y0,x1,y1=bounds;region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&(a[:,:,3]>0)
   mx=xx*.5+shift[0];my=yy*.5+shift[1]
   ref=cv2.remap(refbroken if n==0 else old,mx,my,cv2.INTER_LINEAR)
   dest=cv2.remap(broken if n==0 else art,mx,my,cv2.INTER_LINEAR)
   diff=np.max(np.abs(ref.astype(float)-a[:,:,:3]),axis=2)
   good=region&(diff<25)
   target[good,:3]=dest[good]
   # Shared room scenery must agree right up to sprite edges.
   ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR);dest=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
   good=region&(np.max(np.abs(ref.astype(float)-a[:,:,:3]),axis=2)<24)
   target[good,:3]=dest[good]
  editable=np.any(target[:,:,:3]!=a[:,:,:3],axis=2)
  # Do not recolor white control masks.
  editable&=~(a[:,:,:3].min(axis=2)>225)
  pack(src,OUT,target,editable,scope='coherent porch and debris scenery; control masks retained')
 preview=Image.fromarray(art).convert('RGBA')
 a=Image.fromarray(read_dxt(OUT/(ROOM+'_room_pk_a00.dxt'))[2])
 preview.alpha_composite(a.crop((0,0,802,1825)).resize((401,913),Image.Resampling.LANCZOS),(1469,95))
 for layer,shift in shifts.items():
  c=read_chunk(OUT/f'124-debris-image-frame0-layer{layer}.chnk');c['vertices'][:,:2]+=np.array(shift)*2
  preview=Image.alpha_composite(preview,render(c,(2220,1200)))
 preview.convert('RGB').save(OUT/'broken-state-v3-preview.png')

if __name__=='__main__':main()
