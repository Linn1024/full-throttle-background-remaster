"""Transfer canonical scenery into ranch interaction states, preserving objects."""
import json, struct, subprocess, zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_chunk, read_dxt, triangle_pixels, render
from build_reported_states_v2 import pack

def references(room):
    folder=ROOT/'locations'/room
    return (np.array(Image.open(folder/'official-remaster.png').convert('RGB')),
            np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB')))

def transfer(original,target,old,art,mx,my,region):
    before=cv2.remap(old,mx,my,cv2.INTER_LINEAR)
    after=cv2.remap(art,mx,my,cv2.INTER_LINEAR)
    diff=np.max(np.abs(before.astype(float)-original[:,:,:3]),axis=2).astype('float32')
    # No variance/component cutoffs: smooth ground and sprite edges need coverage.
    bad=cv2.dilate((diff>22).astype('uint8'),np.ones((3,3),np.uint8))>0
    ok=region&~bad&(cv2.blur(diff,(5,5))<9)&(original[:,:,3]>0)
    ok&=(mx>=0)&(my>=0)&(mx<old.shape[1]-1)&(my<old.shape[0]-1)
    target[ok,:3]=after[ok]
    return ok

def ranch():
    room='043-ranch';folder=ROOT/'locations'/room/'custom-v1'
    source=ROOT/'original/rooms'/room/(room+'_room_pk_a00.dxt')
    original=read_dxt(source)[2];target=original.copy();old,art=references(room)
    h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32');editable=np.zeros((h,w),bool)
    # Two parked bike states and both gate states, including surrounding ground.
    states=[((933,2,1345,301),(360.856,667.696)),
            ((313,490,725,789),(670.856,423.760)),
            ((1,489,311,885),(1354.623,186.813)),
            ((1,2,441,486),(1269.931,428.104)),
            ((1,2,441,486),(1314.94,431.0))]
    for (x0,y0,x1,y1),shift in states:
        region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)
        editable|=transfer(original,target,old,art,xx*.5+shift[0],yy*.5+shift[1],region)
    pack(source,folder,target,editable,scope='Both parked bike and gate states: canonical background transfer; nonmatching foreground protected')

def pillow():
    room='131-petes';folder=ROOT/'locations'/room/'custom-v1';old,art=references(room);reports=[]
    for frame in (0,1):
        source=ROOT/'original/rooms'/room/f'573-petes-pillow-frame{frame}-layer40.chnk'
        c=read_chunk(source);payloads=[];checks=[]
        for i,t in enumerate(c['textures']):
            a=np.array(t['image']);target=a.copy();h,w=a.shape[:2]
            mx=np.zeros((h,w),np.float32);my=mx.copy();region=np.zeros((h,w),bool)
            for inds in c['indices'][t['first']:t['first']+t['count']].reshape(-1,3):
                v=c['vertices'][inds];r=triangle_pixels(v[:,2:]*(w,h),w,h)
                if r is None:continue
                lo,hi,weights,inside=r;xy=weights@v[:,:2]/2;sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]))
                mx[sl][inside]=xy[:,:,0][inside];my[sl][inside]=xy[:,:,1][inside];region[sl]|=inside
            editable=transfer(a,target,old,art,mx,my,region)
            # Reuse pack's strict original BC3 alpha and foreground block checks.
            temp=folder/(source.stem+f'-texture{i}.dxt')
            temp.write_bytes(t['payload'])
            png=folder/(source.stem+f'-texture{i}.png');Image.fromarray(target).save(png)
            subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(folder),str(png)],check=True,capture_output=True)
            raw=t['raw'];enc=bytearray(png.with_suffix('.dds').read_bytes()[128:]);changed=0;excluded=(~editable)&(a[:,:,3]>0)
            for y in range(h//4):
                for x in range(w//4):
                    sl=(slice(y*4,y*4+4),slice(x*4,x*4+4));at=(y*(w//4)+x)*16
                    if not editable[sl].any() or excluded[sl].any():enc[at:at+16]=raw[at:at+16]
                    else:enc[at:at+8]=raw[at:at+8];changed+=1
            dec=np.array(Image.frombytes('RGBA',(w,h),bytes(enc),'bcn',(3,'DXT5')))
            assert np.array_equal(a[:,:,3],dec[:,:,3])
            assert np.array_equal(a[excluded],dec[excluded])
            z=zlib.compressobj(9,zlib.DEFLATED,-15);p=t['payload'][:12]+z.compress(enc)+z.flush()
            payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
            checks.append(dict(texture=i,changed_blocks=changed,alpha_preserved=True,protected_foreground_identical=True))
        dest=folder/source.name;dest.write_bytes(c['header']+b''.join(payloads));assert read_chunk(dest)['header']==c['header']
        scene=Image.open(folder/'in-game-texture-preview.png').convert('RGBA')
        Image.alpha_composite(scene,render(read_chunk(dest))).save(folder/(source.stem+'-composite.png'))
        reports.append(dict(file=source.name,textures=checks,builder='ranch-interaction-scenery',gameplay_verified=False))
    (folder/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports))

if __name__=='__main__':
    ranch();pillow()
