"""Refresh shared earth in the current broken-shack state, preserving debris."""
import hashlib,json,struct,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,read_dxt,triangle_pixels,render
from fix_shack_shared_scenery import transfer

ROOM='018-mo-shack'
OUT=ROOT/'locations'/ROOM/'custom-v1'
REVIEW=ROOT/'reviews/debris-ground-v12'
SHIFTS={10:(1246.4,148.2),20:(1346.35,154.19),30:(1401.43,171.95),40:(1371.33,148.12)}

def encode(name,current,raw,target,mask):
    h,w=mask.shape
    # Avoid recompressing any visible debris pixels in mixed boundary blocks.
    protected=(~mask)&(current[:,:,3]>0)
    blocks=mask.reshape(h//4,4,w//4,4).any(axis=(1,3))&~protected.reshape(h//4,4,w//4,4).any(axis=(1,3))
    png=REVIEW/(name+'.png');Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(REVIEW),str(png)],check=True,capture_output=True)
    candidate=png.with_suffix('.dds').read_bytes()[128:];result=bytearray(raw)
    for b in np.flatnonzero(blocks.ravel()):
        at=int(b)*16;result[at+8:at+16]=candidate[at+8:at+16]
    decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(result),'bcn',(3,'DXT5')))
    assert np.array_equal(decoded[:,:,3],current[:,:,3])
    assert np.array_equal(decoded[protected],current[protected])
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    return z.compress(result)+z.flush(),int(blocks.sum())

def main():
    REVIEW.mkdir(exist_ok=True,parents=True)
    guards={n:hashlib.sha256((OUT/f'{ROOM}_room_pk_a{n:02}.dxt').read_bytes()).hexdigest() for n in (1,2)}
    reports=[]
    for layer,shift in SHIFTS.items():
        name=f'124-debris-image-frame0-layer{layer}.chnk';path=OUT/name
        backup=REVIEW/(name+'.before')
        if not backup.exists():backup.write_bytes(path.read_bytes())
        original=read_chunk(ROOT/'original/rooms'/ROOM/name);current=read_chunk(backup);payloads=[];checks=[]
        for i,(orig,t) in enumerate(zip(original['textures'],current['textures'])):
            a=np.array(orig['image']);base=np.array(t['image']);target=base.copy();h,w=a.shape[:2]
            mx=np.full((h,w),-1,np.float32);my=mx.copy();region=np.zeros((h,w),bool)
            for inds in original['indices'][orig['first']:orig['first']+orig['count']].reshape(-1,3):
                v=original['vertices'][inds];r=triangle_pixels(v[:,2:]*(w,h),w,h)
                if r is None:continue
                lo,hi,weights,inside=r;xy=weights@v[:,:2]/2+shift;sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]))
                mx[sl][inside]=xy[:,:,0][inside];my[sl][inside]=xy[:,:,1][inside];region[sl]|=inside
            mask=transfer(a,target,mx,my,region&(my>820))
            compressed,count=encode(name+f'-{i}',base,t['raw'],target,mask)
            p=t['payload'][:12]+compressed;payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
            checks.append(dict(texture=i,changed_blocks=count,alpha_preserved=True,protected_foreground_identical=True))
        path.write_bytes(current['header']+b''.join(payloads));assert read_chunk(path)['header']==original['header']
        reports.append(dict(file=name,textures=checks,builder='debris-ground-v12',gameplay_verified=False))
    name=f'{ROOM}_room_pk_a00.dxt';path=OUT/name;backup=REVIEW/(name+'.before')
    if not backup.exists():backup.write_bytes(path.read_bytes())
    header,raw,base=read_dxt(backup);original=read_dxt(ROOT/'original/rooms'/ROOM/name)[2];target=base.copy()
    h,w=base.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32');mask=np.zeros((h,w),bool)
    for bounds,shift in [((0,0,802,1825),(1469.1,95.4)),((804,0,1448,1570),(1107.14,95.43))]:
        x0,y0,x1,y1=bounds;mx=xx*.5+shift[0];my=yy*.5+shift[1]
        region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&(my>820)
        mask|=transfer(original,target,mx,my,region)
    compressed,count=encode(name,base,raw,target,mask);path.write_bytes(header[:12]+compressed)
    overlay_path=OUT/'overlay-validation.json';overlay=json.loads(overlay_path.read_text())
    for row in overlay:
        if row['file']==name:row.update(ground_v12_changed_blocks=count,ground_v12_foreground_preserved=True)
    overlay_path.write_text(json.dumps(overlay,indent=2)+'\n')
    (OUT/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2)+'\n')
    for n,digest in guards.items():assert hashlib.sha256((OUT/f'{ROOM}_room_pk_a{n:02}.dxt').read_bytes()).hexdigest()==digest
    def composite(before=False):
        image=Image.open(OUT/'in-game-texture-preview.png').convert('RGBA')
        a=Image.fromarray(read_dxt(backup if before else path)[2])
        image.alpha_composite(a.crop((0,0,802,1825)).resize((401,913),Image.Resampling.LANCZOS),(1469,95))
        for layer,shift in SHIFTS.items():
            name=f'124-debris-image-frame0-layer{layer}.chnk';c=read_chunk(REVIEW/(name+'.before') if before else OUT/name)
            c['vertices'][:,:2]+=np.array(shift)*2;image=Image.alpha_composite(image,render(c,(2220,1200)))
        image.save(REVIEW/('before.png' if before else 'after.png'))
    composite(True);composite()
    result=dict(atlas_changed_blocks=count,debris_layers=reports,porch_atlases_byte_identical=True)
    (REVIEW/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
