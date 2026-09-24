"""Use one room-space ground image in every exterior gate state.

Preserves all compressed blocks outside the ground edits, including the
padlock-removed patch and the previously corrected panel material.
"""
import json, subprocess, zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

FOLDER=ROOT/'locations/026-gas-gate/custom-v1'
ROOM=ROOT/'original/rooms/026-gas-gate'
REFERENCE=read_dxt(ROOM/'026-gas-gate_room_pk_a00.dxt')[2]
CANONICAL=np.array(Image.open(FOLDER/'in-game-texture-preview.png').convert('RGB'))
ORIGINAL_SCENE=np.array(Image.open(FOLDER.parent/'official-remaster.png').convert('RGB'))


def write_ground(source, regions):
    data,base_raw,base=read_dxt(FOLDER/source.name)
    original=read_dxt(source)[2];h,w=base.shape[:2]
    target=base.copy();editable=np.zeros((h,w),bool)
    yy,xx=np.mgrid[:h,:w].astype('float32')
    for region,shift,protect in regions:
        mx=(xx*.5+shift[0]).astype('float32');my=(yy*.5+shift[1]).astype('float32')
        sample=cv2.remap(CANONICAL,mx,my,cv2.INTER_LINEAR)
        old_sample=cv2.remap(ORIGINAL_SCENE,mx,my,cv2.INTER_LINEAR)
        # Exterior floor begins below the closed door threshold. The lit
        # interior behind the opening remains a separate, intentional state.
        valid=region&(my>=1065)&(my<CANONICAL.shape[0]-1)&(mx>=0)&(mx<CANONICAL.shape[1]-1)&(original[:,:,3]>0)&~protect
        # State-dependent illumination is smooth; no old stone edges enter
        # the canonical material. Fade it at the sprite silhouette.
        light=cv2.GaussianBlur(original[:,:,:3].astype('float32')-old_sample.astype('float32'),(0,0),32)
        distance=cv2.distanceTransform(((original[:,:,3]>0)&region).astype('uint8'),cv2.DIST_L2,5)
        lighting_weight=np.minimum(distance/48,1)[:,:,None]
        amount=np.clip((my-1065)/10,0,1)[:,:,None]
        ground=np.clip(sample.astype(float)+np.clip(light,-16,16)*lighting_weight,0,255)
        target[valid,:3]=np.rint(ground[valid]*amount[valid]+base[valid,:3]*(1-amount[valid])).astype('uint8')
        editable|=valid
    png=FOLDER/(source.name+'.shared-ground.png');Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(FOLDER),str(png)],check=True,capture_output=True)
    encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);changed=np.zeros((h,w),bool)
    protected=(~editable)&(original[:,:,3]>0)
    for by in range(h//4):
        for bx in range(w//4):
            sl=(slice(by*4,by*4+4),slice(bx*4,bx*4+4));at=(by*(w//4)+bx)*16
            if not editable[sl].any() or protected[sl].any():encoded[at:at+16]=base_raw[at:at+16]
            else:encoded[at:at+8]=base_raw[at:at+8];changed[sl]=True
    z=zlib.compressobj(9,zlib.DEFLATED,-15);dest=FOLDER/source.name
    dest.write_bytes(data[:12]+z.compress(encoded)+z.flush())
    decoded=read_dxt(dest)[2]
    assert np.array_equal(decoded[:,:,3],original[:,:,3])
    assert np.array_equal(decoded[~changed],base[~changed])
    assert np.array_equal(decoded[protected],base[protected])
    reports=json.loads((FOLDER/'overlay-validation.json').read_text())
    for report in reports:
        if report['file']==source.name:
            report['shared_ground_blocks']=int(changed.sum()//16)
            report['ground_source']='in-game-texture-preview.png in room coordinates'
            report['non_ground_blocks_preserved']=True
    (FOLDER/'overlay-validation.json').write_text(json.dumps(reports,indent=2))
    print(source.name,int(changed.sum()//16),flush=True)
    return decoded


def main():
    h,w=REFERENCE.shape[:2];yy,xx=np.mgrid[:h,:w]
    none=np.zeros((h,w),bool)
    atlas=write_ground(ROOM/'026-gas-gate_room_pk_a00.dxt',[( (yy>1325)&(yy<1636)&(xx<1625), (898,382.5),none)])
    # Independent persistent open-state atlas; two separate scene placements.
    write_ground(ROOM/'026-gas-gate_room_pk_a01.dxt',[
        ((xx<900),(1273.365234375,378.9064),none),
        ((xx>900)&(xx<1540)&(yy<1240),(783.85,491.25),none)])
    sift=cv2.SIFT_create(nfeatures=12000)
    k,d=sift.detectAndCompute(cv2.cvtColor(REFERENCE[:,:,:3],cv2.COLOR_RGB2GRAY),(REFERENCE[:,:,3]>250).astype('uint8')*255)
    for n in range(11):
        source=ROOT/f'original/costumes/103-pick-lock-cos/pick-lock-cos_akostume_pk_a{n:02}.dxt'
        original=read_dxt(source)[2]
        if n==10:
            shift=np.array([197.,223.]);region=(xx>=1)&(xx<237)&(yy>=1261)&(yy<1318)
        else:
            q,e=sift.detectAndCompute(cv2.cvtColor(original[:,:,:3],cv2.COLOR_RGB2GRAY),(original[:,:,3]>250).astype('uint8')*255)
            matches=[a for a,b in cv2.BFMatcher().knnMatch(e,d,k=2) if a.distance<.7*b.distance]
            aa=np.float32([q[m.queryIdx].pt for m in matches]);bb=np.float32([k[m.trainIdx].pt for m in matches])
            A,ok=cv2.estimateAffinePartial2D(aa,bb,ransacReprojThreshold=2)
            assert ok.sum()>=20 and np.max(np.abs(A[:,:2]-np.eye(2)))<.002
            shift=np.median(bb[ok.ravel()>0]-aa[ok.ravel()>0],axis=0)
            region=(yy+shift[1]>1325)&(yy+shift[1]<1636)&(xx+shift[0]>185)&(xx+shift[0]<1625)
        mx=(xx+shift[0]).astype('float32');my=(yy+shift[1]).astype('float32')
        ref=cv2.remap(REFERENCE[:,:,:3],mx,my,cv2.INTER_LINEAR)
        protect=cv2.dilate((region&(np.max(np.abs(original[:,:,:3].astype(float)-ref),axis=2)>24)).astype('uint8'),np.ones((5,5),np.uint8))>0
        write_ground(source,[(region,shift*.5+np.array([898,382.5]),protect)])
    # Registration composite of the open-room atlas over the canonical scene.
    preview=Image.fromarray(CANONICAL).convert('RGBA')
    a=atlas.copy();a[:,1625:]=0;a[1636:]=0
    overlay=cv2.warpAffine(a,np.float32([[.5,0,898],[0,.5,382.5]]),(preview.width,preview.height),flags=cv2.INTER_LINEAR)
    preview=Image.alpha_composite(preview,Image.fromarray(overlay))
    preview.convert('RGB').save(FOLDER/'shared-ground-open-preview.png')


if __name__=='__main__':main()
