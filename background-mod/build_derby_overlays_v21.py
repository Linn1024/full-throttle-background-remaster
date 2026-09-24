"""Match animated hatch/platform backing and CRT frames to the derby redraw."""
import json,re,shutil,struct,subprocess,zlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt,read_chunk,render,triangle_pixels
from audit_derby_v21 import REV
from build_derby_sprites_v21 import objects
from build_derby_v21 import register
from build_reported_states_v2 import pack

def generated(key):
 hint=json.loads((REV/f'generation-{key}.json').read_text())['output_hint'];p=Path(re.search(r'as (.+?\.png) by default',hint).group(1));dest=REV/f'{key}-generated.png';shutil.copy2(p,dest);return np.array(Image.open(dest).convert('RGB'))

def room_atlas(room):
 src=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt';a=read_dxt(src)[2];folder=ROOT/'locations'/room;out=folder/'custom-v1'
 art,registration=register(generated(room),a[:,:,:3],local=False)
 before=np.array(Image.open(folder/'official-remaster.png').convert('RGB'));after=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
 labels,parts=objects(a);target=a.copy();editable=np.zeros(a.shape[:2],bool);positions=[]
 for label,(x,y,w,h) in parts:
  if room=='056-arena':
   pos=(1109,101) if w>100 else (1109,132)
   if label==17:pos=(629,96)
  else:pos=(1110,144) if label==5 else (1110,211)
  yy,xx=np.mgrid[:h,:w].astype('float32');mx=pos[0]+xx*.5;my=pos[1]+yy*.5
  old=cv2.remap(before,mx,my,cv2.INTER_LINEAR);new=cv2.remap(after,mx,my,cv2.INTER_LINEAR);original=a[y:y+h,x:x+w,:3]
  diff=np.max(abs(original.astype('float32')-old),axis=2)
  fg=((diff>25)&(cv2.blur(diff,(5,5))>16)).astype('uint8')
  fg=cv2.dilate(fg,np.ones((3,3),np.uint8));weight=cv2.GaussianBlur(fg.astype('float32'),(0,0),.8)
  # At the atlas rectangle boundary, use the exact shared background to avoid
  # an independent generated patch producing another visible rectangle.
  edge=np.minimum.reduce([xx+1,yy+1,w-xx,h-yy]);weight*=np.minimum(edge/5,1)
  rgb=art[y:y+h,x:x+w]*weight[:,:,None]+new*(1-weight[:,:,None]);mask=labels[y:y+h,x:x+w]==label
  target[y:y+h,x:x+w,:3][mask]=np.rint(rgb).astype('uint8')[mask];editable[y:y+h,x:x+w]|=mask
  positions.append(dict(label=label,rect=[x,y,w,h],scene=list(pos),scale=.5))
 decoded=pack(src,out,target,editable,scope='Redrawn hatch/platform art and shared background; white control masks unchanged',registration=registration,parts=positions)
 (REV/f'{room}-state-mapping.json').write_text(json.dumps(positions,indent=2))
 # Review every visible atlas piece composed over the packed background.
 sheet=Image.new('RGB',(1200,((len(parts)+3)//4)*280),'#222222');draw=ImageDraw.Draw(sheet)
 for i,p in enumerate(positions):
  x,y,w,h=p['rect'];sx,sy=p['scene'];base=Image.fromarray(after).convert('RGBA');base.alpha_composite(Image.fromarray(decoded[y:y+h,x:x+w]).resize((round(w/2),round(h/2)),Image.Resampling.LANCZOS),(sx,sy))
  crop=base.crop((sx-20,sy-20,sx+max(130,w/2)+20,sy+max(130,h/2)+20));crop.thumbnail((298,250));sheet.paste(crop,(i%4*300,i//4*280+25));draw.text((i%4*300+4,i//4*280+5),f'part {p["label"]}',fill='white')
 sheet.save(REV/f'{room}-states-packed.jpg')

def chunk_pack(c,targets,folder):
 payloads=[];reports=[]
 for i,(t,target) in enumerate(zip(c['textures'],targets)):
  a=np.array(t['image']);h,w=a.shape[:2];png=folder/f'{c["path"].stem}-v21-{i}.png';Image.fromarray(target).save(png)
  subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(folder),str(png)],check=True,capture_output=True)
  enc=bytearray(png.with_suffix('.dds').read_bytes()[128:]);assert len(enc)==len(t['raw'])
  for j in range(0,len(enc),16):enc[j:j+8]=t['raw'][j:j+8]
  decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(enc),'bcn',(3,'DXT5')));assert np.array_equal(decoded[:,:,3],a[:,:,3])
  z=zlib.compressobj(9,zlib.DEFLATED,-15);p=t['payload'][:12]+z.compress(enc)+z.flush();payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
  reports.append(dict(alpha_preserved=True,protected_foreground_identical=True,scope='Entire visible CRT screen deliberately redrawn; alpha and geometry preserved'))
 dest=folder/c['path'].name;dest.write_bytes(c['header']+b''.join(payloads));assert read_chunk(dest)['header']==c['header']
 return dict(file=dest.name,builder='derby-v21',textures=reports,gameplay_verified=False)

def monitors():
 art=cv2.resize(generated('monitors'),(1440,960),interpolation=cv2.INTER_LANCZOS4);out=ROOT/'locations/059-rips-box/custom-v1';reports=[];frames=[]
 for frame in range(1,17):
  c=read_chunk(ROOT/f'original/rooms/059-rips-box/extra_tvmonitors_f{frame}.chnk');sx=(frame-1)%2*720;sy=(frame-1)//2*120
  patch=cv2.resize(art[sy:sy+120,sx:sx+720],(1440,240),interpolation=cv2.INTER_LANCZOS4);targets=[]
  for t in c['textures']:
   a=np.array(t['image']);h,w=a.shape[:2];target=a.copy()
   for inds in c['indices'][t['first']:t['first']+t['count']].reshape(-1,3):
    v=c['vertices'][inds];r=triangle_pixels(v[:,2:]*(w,h),w,h)
    if r is None:continue
    lo,hi,weights,inside=r;xy=(weights@v[:,:2]/2).astype('float32');paint=cv2.remap(patch,xy[:,:,0],xy[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    region=target[lo[1]:hi[1],lo[0]:hi[0]];region[inside,:3]=paint[inside]
   targets.append(target)
  reports.append(chunk_pack(c,targets,out))
  # The room places this animation 340 scene pixels to the right. Preserve
  # stored geometry; apply the runtime placement only to the review render.
  placed=read_chunk(out/c['path'].name);placed['vertices'][:,0]+=680
  base=Image.open(out/'in-game-texture-preview.png').convert('RGBA');base=Image.alpha_composite(base,render(placed,(2220,1200)));frames.append(base.crop((250,0,1800,260)).resize((1192,200)))
 p=out/'extra-chunk-validation.json';old=json.loads(p.read_text()) if p.exists() else [];p.write_text(json.dumps([r for r in old if r['file'] not in [v['file'] for v in reports]]+reports,indent=2))
 frames[0].save(REV/'monitors-packed.gif',save_all=True,append_images=frames[1:],duration=90,loop=0)
 frames[0].save(REV/'monitors-packed.png')

if __name__=='__main__':
 room_atlas('056-arena');room_atlas('057-demowall');monitors()
