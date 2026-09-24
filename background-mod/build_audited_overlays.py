"""Conservative scenery-only transfers from reviewed offline registrations.

Never regenerates artwork. Reuses the packed custom background, retaining
nonmatching foreground blocks, alpha, text, and all existing manual fixes.
"""
import json, subprocess, zlib
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scene_assets import ROOT, read_dxt

AUDIT=ROOT/'overlay-audit'
# Contact-sheet review excludes standalone foreground objects, text-only sprites,
# uncertain transforms, and rooms already handled by dedicated integration code.
ROOMS={'006-barfront','018-mo-shack','020-melnweed','021-trailer',
 '025-toddshop','026-gas-gate','027-junkgate','054-souvenir',
 '061-crakwall','100-mr-truck','107-barfro-n','116-dumpst-n','159-cavetrn2'}

def main():
 rows=json.loads((AUDIT/'registration.json').read_text());summary=[];tiles=[]
 for row in rows:
  room=row['room'];name=row['file'];folder=ROOT/'locations'/room;out=folder/'custom-v1'
  if room not in ROOMS or not row.get('candidates') or not (out/'validation.json').exists():continue
  existing=json.loads((out/'overlay-validation.json').read_text()) if (out/'overlay-validation.json').exists() else []
  if any(r['file']==name and r.get('builder')!='audited-scenery-v1' for r in existing):continue
  old=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
  art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
  cfg=json.loads((folder/'room.json').read_text())
  data,raw,original=read_dxt(ROOT/'original/rooms'/room/name)
  if data[:4]!=b'DXT5':continue
  h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32')
  target=original.copy();eligible=np.zeros((h,w),bool);records=[]
  for ci,c in enumerate(row['candidates']):
   if c['matches']<9:continue
   scale=c['scale'];shift=np.array(c['shift'],dtype='float32');mx=xx*scale+shift[0];my=yy*scale+shift[1]
   ref=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
   diff=np.max(np.abs(ref.astype('float32')-original[:,:,:3]),axis=2)
   # Reject uncertain/changed object pixels and require agreement across a
   # neighbourhood, not merely a coincidentally matching dark pixel.
   similar=(diff<24)&(original[:,:,3]==255)&(mx>=0)&(my>=0)&(mx<old.shape[1]-1)&(my<old.shape[0]-1)
   local=cv2.blur(diff,(9,9))<9
   gray=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY).astype('float32')
   variance=cv2.blur(gray*gray,(15,15))-cv2.blur(gray,(15,15))**2
   possible=(similar&local&(variance>12)).astype('uint8')
   count,labels,stats,_=cv2.connectedComponentsWithStats(possible,8)
   x0,y0,x1,y1=c['atlas_bounds'];selected=np.zeros_like(possible)
   for idx in range(1,count):
    x,y,ww,hh,area=stats[idx]
    if area<1200 or x>x1+64 or y>y1+64 or x+ww<x0-64 or y+hh<y0-64:continue
    selected[labels==idx]=1
   for x0,y0,x1,y1 in cfg.get('protected',[]):
    selected[(mx>=x0-4)&(mx<=x1+4)&(my>=y0-4)&(my<=y1+4)]=0
   # Preserve original blocks touching the foreground; feather the transfer
   # inward so conservative exclusions do not create hard rectangular edges.
   distance=cv2.distanceTransform(selected,cv2.DIST_L2,5)
   amount=np.clip((distance-3)/16,0,1)
   if room=='018-mo-shack':
    # Reviewed state rectangles: update smooth scenery too. The first audit
    # excluded flat sky/wood and left broad old-background patches here.
    boxes={'00':[(1,1,800,1824),(805,1,640,1536),(1597,965,240,192)],
           '01':[(1,1,690,1390),(693,1,690,1392),(1385,1,530,960)],
           '02':[(1053,1,800,768)]}
    x,y,bw,bh=boxes[name[-6:-4]][ci]
    region=(xx>=x)&(xx<x+bw)&(yy>=y)&(yy<y+bh)
    keep=region&((diff>24)|(original[:,:,3]<250))
    keep=cv2.dilate(keep.astype('uint8'),np.ones((5,5),np.uint8))
    amount=np.minimum(cv2.distanceTransform(1-keep,cv2.DIST_L2,5)/8,1)*region
   if room=='006-barfront' and ci==0:
    # Reviewed isolated ground-restoration sprite, not a foreground object.
    # Include its smooth areas and outer edge; sparse feature agreement alone
    # left a visibly old road patch in the scene composite.
    amount=((yy>=540)&(yy<923)&(xx<915)&(original[:,:,3]>0)).astype('float32')
   active=amount>0
   if active.sum()<1200:continue
   mapped=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
   target[active,:3]=np.rint(mapped[active]*amount[active,None]+original[active,:3]*(1-amount[active,None])).astype('uint8')
   eligible|=active
   records.append(dict(candidate=ci,scale=scale,shift=shift.tolist(),feature_matches=c['matches'],eligible_pixels=int(active.sum())))
  if not records:continue
  png=out/(name+'.png');Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
  encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);assert len(encoded)==len(raw)
  # Allow padding in edge blocks: avoid the old one-block sprite frame bug.
  protected=(~eligible)&(original[:,:,3]>0)
  changed=np.zeros((h,w),bool);blocks=0
  for by in range(h//4):
   for bx in range(w//4):
    at=(by*(w//4)+bx)*16;ys=slice(by*4,by*4+4);xs=slice(bx*4,bx*4+4)
    if not eligible[ys,xs].any() or protected[ys,xs].any():encoded[at:at+16]=raw[at:at+16]
    else:encoded[at:at+8]=raw[at:at+8];changed[ys,xs]=True;blocks+=1
  if blocks<50:continue
  comp=zlib.compressobj(9,zlib.DEFLATED,-15);dest=out/name
  dest.write_bytes(data[:12]+comp.compress(encoded)+comp.flush())
  _,_,decoded=read_dxt(dest)
  assert np.array_equal(original[:,:,3],decoded[:,:,3])
  assert np.array_equal(original[protected],decoded[protected])
  assert np.array_equal(original[~changed],decoded[~changed])
  report=dict(file=name,builder='audited-scenery-v1',changed_blocks=blocks,alpha_preserved=True,excluded_pixels_identical=True,registrations=records,gameplay_verified=False)
  existing=[r for r in existing if r['file']!=name]+[report]
  (out/'overlay-validation.json').write_text(json.dumps(existing,indent=2))
  Image.fromarray(changed.astype('uint8')*255).save(out/(name+'.changed.png'))
  # Actual decoded atlas review with changes outlined, not a rendered mockup.
  tile=Image.new('RGB',(900,480),(35,35,35));d=ImageDraw.Draw(tile);d.text((4,4),name,fill='white')
  for j,arr in enumerate((original,decoded)):
   im=Image.fromarray(arr);im.thumbnail((440,430));tile.paste(im,(j*450,30),im.getchannel('A'))
  d.text((4,462),f'Original / packed custom: {blocks} blocks; alpha and excluded pixels identical',fill='white')
  tiles.append(tile);tile.save(AUDIT/(name+'.review.jpg'))
  summary.append(dict(room=room,**report));print(room,name,blocks,flush=True)
 (AUDIT/'built.json').write_text(json.dumps(summary,indent=2))
 for start in range(0,len(tiles),4):
  page=Image.new('RGB',(1800,960),(25,25,25))
  for i,t in enumerate(tiles[start:start+4]):page.paste(t,((i%2)*900,(i//2)*480))
  page.save(AUDIT/f'review-{start//4+1}.jpg')
 print('Built',len(summary),'atlases')

if __name__=='__main__':main()
