"""Register and transfer approved scenery into Todd's existing object atlases.

This is integration of existing artwork, not generated or repainted object art.
Only matching static scenery is eligible; original BC3 blocks protect objects.
"""
import json, subprocess, zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt

ROOM='023-todds'
# Atlas rectangles and registered half-resolution scene origins. Registration
# uses independent textured patches, not the character or changing objects.
REGIONS={
 '00':[(250,1,240,480,752,336,'wall'),
       (250,578,241,480,752,336,'wall-state'),
       (493,1,640,1056,1150,432,'door'),
       (1137,1,893,964,509,623,'todd-body'),
       (493,1061,234,196,554,623,'todd-head'),
       (1,1445,642,576,990,624,'hatch-open'),
       (645,1445,642,576,990,624,'hatch-closed')],
 '01':[(1381,1,560,481,790,336,'cabinet-open'),
       (1,637,321,384,630,480,'small-cabinet')]
}

def main():
 folder=ROOT/'locations'/ROOM;out=folder/'custom-v1'
 old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 reports=[];sprites={}
 for n,regions in REGIONS.items():
  name=f'{ROOM}_room_pk_a{n}.dxt';data,raw,original=read_dxt(ROOT/'original/rooms'/ROOM/name)
  target=original.copy();allowed=np.zeros(original.shape[:2],bool);records=[]
  protected=np.zeros(original.shape[:2],bool)
  for x,y,w,h,sx,sy,label in regions:
   # Atlas pixels have twice the scene resolution. Match pixel centers.
   mx,my=np.meshgrid(sx+(np.arange(w,dtype=np.float32)+.5)/2-.5,sy+(np.arange(h,dtype=np.float32)+.5)/2-.5)
   before=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
   after=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
   sprite=original[y:y+h,x:x+w]
   diff=np.max(np.abs(sprite[:,:,:3].astype(float)-before),axis=2)
   protect=((diff>22)|(sprite[:,:,3]<255)).astype(np.uint8)
   # Explicit foreground guards prevent coincidentally dark matching pixels
   # inside characters/doors from becoming eligible scenery.
   if label=='door':protect[:1035,40:600]=1
   if label=='small-cabinet':protect[25:365,65:]=1
   if label=='cabinet-open':protect[45:440,95:540]=1
   if label.startswith('hatch-'):
    protect[:510,200:510]=1
    # The lid and revealed hole differ between these two states.
    if label=='hatch-open':
     points=np.array([(15,380),(215,350),(555,495),(275,560)],np.int32)
    else:
     points=np.array([(15,360),(225,350),(560,485),(260,550)],np.int32)
    cv2.fillPoly(protect,[points],1)
   if label=='todd-head':protect[45:,15:]=1
   if label=='todd-body':
    points=np.array([(100,175),(170,175),(170,0),(340,0),(340,170),(500,175),(620,235),(660,360),(705,420),(892,590),(892,735),(835,760),(755,900),(680,963),(530,880),(500,740),(390,800),(140,715),(45,530),(30,350)],np.int32)
    cv2.fillPoly(protect,[points],1)
   protect=cv2.dilate(protect,np.ones((5,5),np.uint8))
   weight=np.minimum(cv2.distanceTransform(1-protect,cv2.DIST_L2,5)/6,1)[:,:,None]
   target[y:y+h,x:x+w,:3]=np.rint(after*weight+sprite[:,:,:3]*(1-weight)).astype(np.uint8)
   allowed[y:y+h,x:x+w]=protect==0
   protected[y:y+h,x:x+w]|=protect!=0
   records.append(dict(label=label,atlas=[x,y,w,h],scene=[sx,sy],eligible_pixels=int((protect==0).sum())))
  png=out/(name+'.png');Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
  encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);assert len(encoded)==len(raw)
  height,width=original.shape[:2];changed=0;actual=np.zeros_like(allowed)
  for by in range(height//4):
   for bx in range(width//4):
    at=(by*(width//4)+bx)*16;ys=slice(by*4,by*4+4);xs=slice(bx*4,bx*4+4)
    # Atlas rectangles start at odd pixel offsets. Requiring all 16 pixels
    # to be editable retained old scenery along every outer rectangle edge.
    # Permit mixed scenery/padding blocks, but never any foreground guard.
    if not allowed[ys,xs].any() or protected[ys,xs].any():encoded[at:at+16]=raw[at:at+16]
    else:
     encoded[at:at+8]=raw[at:at+8];changed+=1;actual[ys,xs]=True
  compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
  dest=out/name;dest.write_bytes(data[:12]+compressor.compress(encoded)+compressor.flush())
  _,_,decoded=read_dxt(dest)
  assert np.array_equal(original[:,:,3],decoded[:,:,3])
  assert np.array_equal(original[~actual],decoded[~actual])
  assert np.array_equal(original[protected],decoded[protected])
  assert changed>0
  for x,y,w,h,sx,sy,label in regions:
   sprites[label]=(decoded[y:y+h,x:x+w],sx,sy)
   if label.startswith('hatch-'):
    # Regression: the old full-block rule left these floor/rug edges intact.
    assert actual[y+h-1,x+16:x+w-16].all(), 'Old bottom border retained'
    assert actual[y+h-40:y+h,x].all(), 'Old left border retained'
  Image.fromarray((actual*255).astype('uint8')).save(out/f'todd-changed-mask-{n}.png')
  reports.append(dict(file=name,changed_blocks=changed,alpha_preserved=True,protected_object_pixels_identical=True,untouched_blocks_identical=True,hatch_border_checks_passed=n=='00',regions=records))
 for state,labels in {'closed':['hatch-closed','door','todd-body','todd-head'],'open':['hatch-open','cabinet-open','small-cabinet','todd-body','todd-head'],
                      'fridge-only':['cabinet-open']}.items():
  preview=Image.fromarray(art).convert('RGBA')
  for label in labels:
   im,sx,sy=sprites[label];p=Image.fromarray(im);p=p.resize((round(p.width/2),round(p.height/2)),Image.Resampling.LANCZOS);preview.alpha_composite(p,(sx,sy))
  preview.convert('RGB').save(out/f'todd-overlays-{state}-preview.png')
 (out/'overlay-validation.json').write_text(json.dumps(reports,indent=2)+'\n')
 print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
