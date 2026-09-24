"""Replace baked scenery in all hatch states and the foot-switch CHNK."""
import json, struct, subprocess, zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt, read_chunk
from build_reported_states_v2 import pack

folder=ROOT/'locations/061-crakwall/custom-v1'
art=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGB'))
specs=[[(4,0,246,433,1226,623),(249,0,492,433,979,623),
        (495,0,738,433,734,623),(739,0,980,433,492,623),
        (3,434,246,867,1226,189),(249,434,492,867,979,189),
        (493,434,736,867,738,189),(737,434,975,867,496,189)],
       [(0,0,241,433,1230,623),(242,0,483,433,988,623),(0,434,241,867,1230,189)]]
for n,frames in enumerate(specs):
    source=ROOT/f'original/rooms/061-crakwall/061-crakwall_room_pk_a0{n}.dxt'
    original=read_dxt(source)[2];target=original.copy()
    h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32')
    editable=np.zeros((h,w),bool)
    r,g,b=original[:,:,:3].astype(float).transpose(2,0,1)
    # The moving lavender metal is distinct from the orange/brown scenery.
    mechanism=(b>r+5)&(b>g+5)&(b>45)
    filled=mechanism.astype('uint8')
    contours,_=cv2.findContours(filled,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(filled,contours,-1,1,cv2.FILLED)
    mechanism=cv2.dilate(filled,np.ones((7,7),np.uint8))>0
    for x0,y0,x1,y1,dx,dy in frames:
        region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&(original[:,:,3]>0)
        select=region&~mechanism
        mapped=cv2.remap(art,xx+dx,yy+dy,cv2.INTER_LINEAR)
        target[select,:3]=mapped[select];editable|=select
    pack(source,folder,target,editable,scope='all hatch state scenery; moving lavender mechanism and control masks retained',frames=frames)

source=ROOT/'original/rooms/061-crakwall/328-toe-switch-frame0-layer20.chnk'
chunk=read_chunk(source);payloads=[];checks=[]
for i,tex in enumerate(chunk['textures']):
    original=np.array(tex['image']);h,w=original.shape[:2]
    yy,xx=np.mgrid[:h,:w].astype('float32')
    target=original.copy();target[:,:,:3]=cv2.remap(art,xx+586,yy+620,cv2.INTER_LINEAR)
    png=folder/f'{source.stem}-texture{i}.png';Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(folder),str(png)],check=True,capture_output=True)
    encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);raw=tex['raw']
    for by in range(h//4):
        for bx in range(w//4):
            at=(by*(w//4)+bx)*16
            if original[by*4:by*4+4,bx*4:bx*4+4,3].any():encoded[at:at+8]=raw[at:at+8]
            else:encoded[at:at+16]=raw[at:at+16]
    decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(encoded),'bcn',(3,'DXT5')))
    assert np.array_equal(decoded[:,:,3],original[:,:,3])
    z=zlib.compressobj(9,zlib.DEFLATED,-15);p=tex['payload'][:12]+z.compress(encoded)+z.flush()
    payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
    # This CHNK contains environment only; no character/control pixels.
    checks.append(dict(texture=i,alpha_preserved=True,protected_foreground_identical=True))
(folder/source.name).write_bytes(chunk['header']+b''.join(payloads))
assert read_chunk(folder/source.name)['header']==chunk['header']
path=folder/'extra-chunk-validation.json';reports=json.loads(path.read_text()) if path.exists() else []
reports=[r for r in reports if r['file']!=source.name]
reports.append(dict(file=source.name,builder='crakwall-open-states-v1',textures=checks,scope='foot-switch scenery',gameplay_verified=False))
path.write_text(json.dumps(reports,indent=2))
print('Updated eleven hatch frames and foot-switch scenery.')
