"""Transfer approved bench scenery through the extra object's unchanged UVs."""
import json,struct,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,render,triangle_pixels

def main():
 room='019-mo-bench';folder=ROOT/'locations'/room;out=folder/'custom-v1'
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 reports=[];preview=Image.fromarray(art).convert('RGBA')
 # Object-local coordinates: 173 independent feature inliers establish +310 X.
 # Layer20 is the foreground-only bike/ropes mask and remains original.
 for path in sorted((ROOT/'original/rooms'/room).glob('126-bench-object-frame0-layer10.chnk')):
  chunk=read_chunk(path);payloads=[];checks=[]
  for ti,tex in enumerate(chunk['textures']):
   original=np.array(tex['image']);target=original.copy();h,w=original.shape[:2]
   eligible=np.zeros((h,w),bool);guard=np.zeros((h,w),bool)
   for inds in chunk['indices'][tex['first']:tex['first']+tex['count']].reshape(-1,3):
    verts=chunk['vertices'][inds];r=triangle_pixels(verts[:,2:]*(w,h),w,h)
    if r is None:continue
    lo,hi,weights,inside=r;xy=(weights@verts[:,:2])/2
    xy[:,:,0]+=310
    sx=np.clip(xy[:,:,0].astype(int),0,art.shape[1]-1);sy=np.clip(xy[:,:,1].astype(int),0,art.shape[0]-1)
    sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]));before=original[sl]
    difference=np.max(np.abs(before[:,:,:3].astype(float)-old[sy,sx]),axis=2)
    keep=(difference>24)|(before[:,:,3]<250)
    # Black bike panels can coincidentally match the bare room. Protect the
    # complete foreground bike envelope, not just differing colour pixels.
    keep|=((sx>1200)&(sy>690))|(sy>1040)
    guard[sl]|=inside&keep
    eligible[sl]|=inside&~keep
    target[sl][:,:,:3][inside&~keep]=art[sy,sx][inside&~keep]
   guard=cv2.dilate(guard.astype('uint8'),np.ones((5,5),np.uint8))!=0
   eligible&=~guard
   distance=cv2.distanceTransform(eligible.astype('uint8'),cv2.DIST_L2,5)
   weight=np.minimum(distance/8,1)[:,:,None]
   target[:,:,:3]=np.rint(target[:,:,:3]*weight+original[:,:,:3]*(1-weight)).astype('uint8')
   png=out/f'{path.stem}-texture{ti}.png';Image.fromarray(target).save(png)
   fmt='BC3_UNORM' if tex['format']==b'DXT5' else 'BC1_UNORM';stride=16 if fmt=='BC3_UNORM' else 8
   subprocess.run([str(ROOT/'tools/texconv.exe'),'-f',fmt,'-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
   encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);raw=tex['raw'];changed=np.zeros((h,w),bool);count=0
   for by in range(h//4):
    for bx in range(w//4):
     at=(by*(w//4)+bx)*stride;sl=(slice(by*4,by*4+4),slice(bx*4,bx*4+4))
     if not eligible[sl].any() or guard[sl].any():encoded[at:at+stride]=raw[at:at+stride]
     else:
      if stride==16:encoded[at:at+8]=raw[at:at+8]
      changed[sl]=True;count+=1
   decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(encoded),'bcn',(3 if stride==16 else 1,tex['format'].decode())))
   assert np.array_equal(original[:,:,3],decoded[:,:,3])
   assert np.array_equal(original[guard|~changed],decoded[guard|~changed])
   z=zlib.compressobj(9,zlib.DEFLATED,-15);p=tex['payload'][:12]+z.compress(encoded)+z.flush();payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
   checks.append(dict(texture=ti,changed_blocks=count,alpha_preserved=True,protected_foreground_identical=True))
  dest=out/path.name;dest.write_bytes(chunk['header']+b''.join(payloads));assert read_chunk(dest)['header']==chunk['header']
  preview.alpha_composite(render(read_chunk(dest)),(310,0))
  reports.append(dict(file=path.name,textures=checks))
 preview.convert('RGB').save(out/'bench-object-composite.png')
 (out/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))

if __name__=='__main__':main()
