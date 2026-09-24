"""Replace the actual closed-door padlock-removed patch (not the opening poses)."""
import cv2
import numpy as np
import json
import zlib
from PIL import Image
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack


def main():
    folder=ROOT/'locations/026-gas-gate/custom-v1'
    source=ROOT/'original/rooms/026-gas-gate/026-gas-gate_room_pk_a00.dxt'
    _,original_raw,original=read_dxt(source)
    _,current_raw,current=read_dxt(folder/source.name)
    # Full opaque state rectangle. Independent 24px template matching gives
    # the same room position for 34 textured patches.
    x,y,w,h=1,1637,250,288
    sx,sy=1230,720
    official=np.array(Image.open(folder.parent/'official-remaster.png').convert('RGB'))
    custom=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGB'))
    old=cv2.resize(official[sy:sy+h//2,sx:sx+w//2],(w,h),interpolation=cv2.INTER_LINEAR)
    new=cv2.resize(custom[sy:sy+h//2,sx:sx+w//2],(w,h),interpolation=cv2.INTER_LINEAR)
    state=original[y:y+h,x:x+w,:3]
    # Only the missing padlock differs from the closed background. Retain
    # its revealed handle surface, so copying the scene cannot resurrect it.
    keep=cv2.dilate((np.max(np.abs(state.astype(float)-old),axis=2)>24).astype('uint8'),np.ones((3,3),np.uint8))
    assert 3000<int(keep.sum())<6000
    weight=np.minimum(cv2.distanceTransform(1-keep,cv2.DIST_L2,5)/5,1)[:,:,None]
    target=current.copy()
    target[y:y+h,x:x+w,:3]=np.rint(new*weight+state*(1-weight)).astype('uint8')
    editable=np.any(current!=original,axis=2)
    editable[y:y+h,x:x+w]=keep==0
    decoded=pack(source,folder,target,editable,scope='padlock-removed handle patch mapped at scene 1230,720; original revealed surface preserved',registration_patch_votes=34)
    data,raw,_=read_dxt(folder/source.name)
    raw=bytearray(raw)
    touched=0
    # Keep every block outside this one rectangle byte-for-byte identical to
    # the installed atlas; do not recompress the other open-gate sprites.
    for by in range(original.shape[0]//4):
        for bx in range(original.shape[1]//4):
            at=(by*(original.shape[1]//4)+bx)*16
            if bx*4>=x+w or bx*4+4<=x or by*4>=y+h or by*4+4<=y:
                raw[at:at+16]=current_raw[at:at+16]
            else:touched+=1
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    (folder/source.name).write_bytes(data[:12]+z.compress(raw)+z.flush())
    decoded=read_dxt(folder/source.name)[2]
    assert np.array_equal(decoded[:,:,3],original[:,:,3])
    outside=np.ones(original.shape[:2],bool)
    outside[(y//4)*4:((y+h+3)//4)*4,(x//4)*4:((x+w+3)//4)*4]=False
    assert np.array_equal(decoded[outside],current[outside])
    report_path=folder/'overlay-validation.json'
    reports=json.loads(report_path.read_text())
    for report in reports:
        if report['file']==source.name:
            report['changed_blocks']=int(np.any(np.frombuffer(raw,dtype='uint8').reshape(-1,16)!=np.frombuffer(original_raw,dtype='uint8').reshape(-1,16),axis=1).sum())
            report['padlock_patch_blocks']=touched
            report['other_atlas_blocks_preserved']=True
    report_path.write_text(json.dumps(reports,indent=2))
    assert np.array_equal(decoded[y:y+h,x:x+w][keep>0],original[y:y+h,x:x+w][keep>0])
    preview=Image.fromarray(custom).convert('RGBA')
    preview.alpha_composite(Image.fromarray(decoded[y:y+h,x:x+w]).resize((w//2,h//2),Image.Resampling.LANCZOS),(sx,sy))
    preview.convert('RGB').save(folder/'padlock-removed-scene-preview.png')
    preview.crop((1180,620,1450,910)).resize((540,580)).save(ROOT/'previews/padlock-removed-fixed.png')


if __name__=='__main__':main()
