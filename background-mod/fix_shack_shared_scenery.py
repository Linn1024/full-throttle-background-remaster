"""Register existing background scenery into debris and porch overlays."""
import json,struct,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk,read_dxt,triangle_pixels

ROOM='018-mo-shack'
OUT=ROOT/'locations'/ROOM/'custom-v1'
OLD=np.array(Image.open(OUT.parent/'official-remaster.png').convert('RGB'))
ART=np.array(Image.open(OUT/'in-game-texture-preview.png').convert('RGB'))

def transfer(original,current,mx,my,region):
    before=cv2.remap(OLD,mx,my,cv2.INTER_LINEAR)
    after=cv2.remap(ART,mx,my,cv2.INTER_LINEAR)
    diff=np.max(np.abs(before.astype(float)-original[:,:,:3]),axis=2)
    # State-specific rubble and ropes differ from the bare scene and stay custom.
    ok=region&(mx>=0)&(my>=0)&(mx<OLD.shape[1]-1)&(my<OLD.shape[0]-1)&(original[:,:,3]>0)
    bad=cv2.dilate((diff>24).astype('uint8'),np.ones((3,3),np.uint8))>0
    ok&=~bad&(cv2.blur(diff.astype('float32'),(9,9))<8)
    current[:,:,:3][ok]=after[ok]
    return ok

def encode(stem,target,raw,mask):
    png=OUT/(stem+'-shared.png');Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(OUT),str(png)],check=True,capture_output=True)
    encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);h,w=mask.shape
    for y in range(h//4):
        for x in range(w//4):
            at=(y*(w//4)+x)*16
            if not mask[y*4:y*4+4,x*4:x*4+4].any():encoded[at:at+16]=raw[at:at+16]
            else:encoded[at:at+8]=raw[at:at+8]
    decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(encoded),'bcn',(3,'DXT5')))
    assert np.array_equal(decoded[:,:,3],target[:,:,3])
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    return z.compress(encoded)+z.flush()

def main():
    reports=[]
    shifts={10:(1246.4,148.2),20:(1346.35,154.19),30:(1401.43,171.95),40:(1371.33,148.12)}
    for layer,shift in shifts.items():
        name=f'124-debris-image-frame0-layer{layer}.chnk';path=OUT/name
        backup=OUT/(name+'.before-shared');
        if not backup.exists():backup.write_bytes(path.read_bytes())
        old=read_chunk(ROOT/'original/rooms'/ROOM/name);current=read_chunk(backup);payloads=[]
        for i,tex in enumerate(old['textures']):
            original=np.array(tex['image']);target=np.array(current['textures'][i]['image']);h,w=original.shape[:2]
            mx=np.zeros((h,w),np.float32);my=mx.copy();region=np.zeros((h,w),bool)
            for inds in old['indices'][tex['first']:tex['first']+tex['count']].reshape(-1,3):
                tri=old['vertices'][inds];r=triangle_pixels(tri[:,2:]*(w,h),w,h)
                if r is None:continue
                lo,hi,weights,inside=r;xy=weights@tri[:,:2]/2+shift;sl=(slice(lo[1],hi[1]),slice(lo[0],hi[0]))
                mx[sl][inside]=xy[:,:,0][inside];my[sl][inside]=xy[:,:,1][inside];region[sl]|=inside
            mask=transfer(original,target,mx,my,region)
            p=tex['payload'][:12]+encode(name+f'-{i}',target,current['textures'][i]['raw'],mask)
            payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
            reports.append(dict(file=name,scene_shift=shift,transferred_pixels=int(mask.sum())))
        path.write_bytes(old['header']+b''.join(payloads));assert read_chunk(path)['header']==old['header']
    rows=[r for r in json.loads((ROOT/'overlay-audit/registration.json').read_text()) if r['room']==ROOM]
    for row in rows:
        name=row['file'];path=OUT/name;backup=OUT/(name+'.before-shared')
        if not backup.exists():backup.write_bytes(path.read_bytes())
        data,raw,current=read_dxt(backup);original=read_dxt(ROOT/'original/rooms'/ROOM/name)[2]
        h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32');mask=np.zeros((h,w),bool)
        candidates=list(row['candidates'])
        if name.endswith('a02.dxt'):
            candidates.append(dict(scale=.5,shift=[1389.16,123.64],atlas_bounds=[0,790,520,1610]))
        for c in candidates:
            x0,y0,x1,y1=c['atlas_bounds'];region=(xx>=max(0,x0-24))&(xx<=x1+24)&(yy>=max(0,y0-24))&(yy<=y1+24)
            # Complete known packed state rectangles, including smooth patches.
            if name.endswith('a00.dxt') and c is candidates[0]:region=(xx<802)&(yy<1825)
            mask|=transfer(original,current,xx*.5+c['shift'][0],yy*.5+c['shift'][1],region)
        path.write_bytes(data[:12]+encode(name,current,raw,mask))
        reports.append(dict(file=name,transferred_pixels=int(mask.sum())))
    (OUT/'shared-scenery-validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))

if __name__=='__main__':main()
