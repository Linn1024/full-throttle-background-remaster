import json,shutil,struct,subprocess,zlib
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scene_assets import ROOT,read_chunk,read_dxt,triangle_pixels,render
from build_custom import build
from build_reported_states_v2 import pack
ROOM='131-petes';F=ROOT/'locations'/ROOM;OUT=F/'custom-v1';REV=ROOT/'reviews/petes-v15'

def room():
 for name in ['custom-remaster-v1.png','room.json']:
  if not (REV/('before-'+name)).exists():shutil.copy2(F/name,REV/('before-'+name))
 base=np.array(Image.open(REV/'before-custom-remaster-v1.png').convert('RGB').resize((2220,1200)))
 old=np.array(Image.open(F/'official-remaster.png').convert('RGB'));yy,xx=np.mgrid[:1200,:2220];weight=np.ones(xx.shape)
 for x0,y0,x1,y1 in json.loads((REV/'before-room.json').read_text())['protected']:
  weight=np.minimum(weight,np.clip(np.hypot(np.maximum(np.maximum(x0-xx,xx-x1),0),np.maximum(np.maximum(y0-yy,yy-y1),0))/40,0,1))
 base=np.rint(base*weight[:,:,None]+old*(1-weight[:,:,None])).astype('uint8')
 box=(740,310,1120,1030);art=Image.open(REV/'room-generated.png').convert('RGB').resize((380,720),Image.Resampling.LANCZOS)
 mask=Image.new('L',(380,720));d=ImageDraw.Draw(mask)
 d.polygon([(132,30),(233,30),(330,107),(329,280),(140,280)],fill=255)
 d.rectangle((153,64,210,123),fill=0) # small framed picture is not the banner
 d.polygon([(27,525),(253,525),(253,685),(23,685),(23,548)],fill=255)
 hard=np.array(mask);mask=Image.fromarray(np.minimum(hard,np.array(mask.filter(ImageFilter.GaussianBlur(1)))))
 im=Image.fromarray(base);im.paste(Image.composite(art,im.crop(box),mask),box[:2]);im.save(F/'custom-remaster-v1.png')
 cfg=json.loads((F/'room.json').read_text());cfg['protected']=[];(F/'room.json').write_text(json.dumps(cfg,indent=2)+'\n');build(ROOM)

def shared(a,target,mx,my,valid):
 old=np.array(Image.open(F/'official-remaster.png').convert('RGB'));new=np.array(Image.open(OUT/'in-game-texture-preview.png').convert('RGB'))
 before=cv2.remap(old,mx,my,cv2.INTER_LINEAR);after=cv2.remap(new,mx,my,cv2.INTER_LINEAR)
 diff=np.max(abs(before.astype(float)-a[:,:,:3]),axis=2).astype('float32')
 good=valid&(diff<24)&(cv2.blur(diff,(5,5))<9)&(a[:,:,3]>0)
 target[:,:,:3][good]=after[good]
 return good

def states():
 reports=[]
 for name in ['560-petes-chest-frame0-layer40','573-petes-pillow-frame0-layer40','573-petes-pillow-frame1-layer40']:
  src=ROOT/'original/rooms'/ROOM/(name+'.chnk');c=read_chunk(src);payloads=[]
  if (OUT/src.name).exists() and not (REV/(src.name+'.before')).exists():shutil.copy2(OUT/src.name,REV/(src.name+'.before'))
  for i,t in enumerate(c['textures']):
   a=np.array(t['image']);h,w=a.shape[:2];target=a.copy()
   target[:,:,:3]=np.array(Image.open(REV/(name+'-generated.png')).convert('RGB').resize((w,h),Image.Resampling.LANCZOS))
   if name=='573-petes-pillow-frame1-layer40':
    first=read_chunk(ROOT/'original/rooms'/ROOM/'573-petes-pillow-frame0-layer40.chnk')['textures'][i]
    different=(np.max(abs(np.array(first['image'])[:,:,:3].astype(float)-a[:,:,:3]),axis=2)>8).astype('uint8')
    blend=cv2.GaussianBlur(cv2.dilate(different,np.ones((9,9),np.uint8)).astype('float32'),(0,0),1.5)[:,:,None]
    same=np.array(Image.open(REV/'573-petes-pillow-frame0-layer40-generated.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS))
    target[:,:,:3]=np.rint(same*(1-blend)+target[:,:,:3]*blend).astype('uint8')
   mx=np.zeros((h,w),np.float32);my=mx.copy();valid=np.zeros((h,w),bool)
   for inds in c['indices'][t['first']:t['first']+t['count']].reshape(-1,3):
    v=c['vertices'][inds];r=triangle_pixels(v[:,2:]*(w,h),w,h)
    if r is None:continue
    lo,hi,weights,inside=r;xy=weights@v[:,:2]/2
    if name.startswith('560'):xy[:,:,1]+=718
    sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]));mx[sl][inside]=xy[:,:,0][inside];my[sl][inside]=xy[:,:,1][inside];valid[sl]|=inside
   shared(a,target,mx,my,valid)
   # Keep control strips outside actual visible object region untouched.
   editable=valid&(a[:,:,3]>0)&(my>400)&(mx>700)&(mx<1150)
   target[~editable]=a[~editable]
   png=OUT/(name+'-v15.png');Image.fromarray(target).save(png)
   subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(OUT),str(png)],check=True,capture_output=True)
   enc=bytearray(png.with_suffix('.dds').read_bytes()[128:]);raw=t['raw']
   for y in range(h//4):
    for x in range(w//4):
     sl=np.s_[y*4:y*4+4,x*4:x*4+4];at=(y*(w//4)+x)*16
     if not editable[sl].any() or ((~editable[sl])&(a[sl][:,:,3]>0)).any():enc[at:at+16]=raw[at:at+16]
     else:enc[at:at+8]=raw[at:at+8]
   dec=np.array(Image.frombytes('RGBA',(w,h),bytes(enc),'bcn',(3,'DXT5')));assert np.array_equal(dec[:,:,3],a[:,:,3]);assert np.array_equal(dec[(~editable)&(a[:,:,3]>0)],a[(~editable)&(a[:,:,3]>0)])
   z=zlib.compressobj(9,zlib.DEFLATED,-15);p=t['payload'][:12]+z.compress(enc)+z.flush();payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
  dest=OUT/src.name;dest.write_bytes(c['header']+b''.join(payloads));assert read_chunk(dest)['header']==c['header']
  reports.append(dict(file=src.name,builder='petes-v15',textures=[dict(alpha_preserved=True,protected_foreground_identical=True,scope='Intentional object redraw; excluded control pixels unchanged')],gameplay_verified=False))
  rc=read_chunk(dest)
  if name.startswith('560'):rc['vertices'][:,1]+=1436
  im=Image.open(OUT/'in-game-texture-preview.png').convert('RGBA');Image.alpha_composite(im,render(rc,(2220,1200))).crop((700,310,1140,1030)).save(REV/(name+'-composite.png'))
 (OUT/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2))
 # Unlocked chest atlas: update canonical shared chest, preserving its distinct lock and control masks.
 src=ROOT/'original/rooms'/ROOM/(ROOM+'_room_pk_a00.dxt');a=read_dxt(src)[2];target=a.copy();h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32')
 editable=shared(a,target,xx*.5+749.5,yy*.5+767.5,xx<565)
 pack(src,OUT,target,editable,scope='Unlocked chest shares new room art; lock and control masks preserved')

if __name__=='__main__':room();states()
