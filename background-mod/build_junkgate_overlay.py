"""Map approved scenery into the junkyard's cord-removed object state."""
import json
import subprocess
import zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt


def main():
    room='027-junkgate'
    folder=ROOT/'locations'/room
    out=folder/'custom-v1'
    name=f'{room}_room_pk_a00.dxt'
    data,raw,original=read_dxt(ROOT/'original/rooms'/room/name)
    # UV rectangle from room.xml, registered against three independent patches.
    # Full-resolution sprite atlas; room reconstruction is at half world scale.
    ys,xs=slice(1,1549),slice(1257,1513)
    official=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
    custom=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
    old=cv2.resize(official[120:894,1390:1518],(256,1548),interpolation=cv2.INTER_LINEAR)
    new=cv2.resize(custom[120:894,1390:1518],(256,1548),interpolation=cv2.INTER_LINEAR)
    sprite=original[ys,xs,:3]
    # Preserve the pixels that differ from the static room: the removed cord's
    # revealed surface and attachment hole. This never changes state geometry.
    keep=(np.max(np.abs(sprite.astype(float)-old),axis=2)>25).astype(np.uint8)
    keep=cv2.dilate(keep,np.ones((5,5),np.uint8))
    # The outer strips are static wall, not the cord or its attachment.
    # Do not retain a rectangular outline because of subpixel registration
    # differences at the atlas boundary.
    keep[:,:8]=0
    keep[:,-8:]=0
    weight=np.minimum(cv2.distanceTransform(1-keep,cv2.DIST_L2,5)/8,1)[:,:,None]
    weight[:,:4]=1
    weight[:,-4:]=1
    target=original.copy()
    target[ys,xs,:3]=np.rint(new*weight+sprite*(1-weight)).astype(np.uint8)
    png=out/(name+'.png')
    Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
    encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:])
    allowed=np.zeros(original.shape[:2],bool)
    allowed[ys,xs]=keep==0
    protected=np.zeros(original.shape[:2],bool)
    protected[ys,xs]=keep!=0
    changed=np.zeros_like(allowed)
    changes=0
    for by in range(512):
        for bx in range(512):
            at=(by*512+bx)*16
            region=(slice(by*4,by*4+4),slice(bx*4,bx*4+4))
            if not allowed[region].any() or protected[region].any():
                encoded[at:at+16]=raw[at:at+16]
            else:
                encoded[at:at+8]=raw[at:at+8]
                changes+=1
                changed[region]=True
    compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
    dest=out/name
    dest.write_bytes(data[:12]+compressor.compress(encoded)+compressor.flush())
    _,_,decoded=read_dxt(dest)
    assert np.array_equal(original[:,:,3],decoded[:,:,3])
    assert np.array_equal(original[~changed],decoded[~changed])
    assert np.array_equal(original[protected],decoded[protected])
    preview=Image.fromarray(custom).convert('RGBA')
    overlay=Image.fromarray(decoded[ys,xs]).resize((128,774),Image.Resampling.LANCZOS)
    preview.alpha_composite(overlay,(1390,120))
    preview.convert('RGB').save(out/'cord-removed-preview.png')
    report=json.loads((out/'overlay-validation.json').read_text())
    report=[r for r in report if r['file']!=name]+[dict(file=name,changed_blocks=changes,alpha_preserved=True,
                 protected_state_pixels_identical=True,untouched_blocks_identical=True)]
    (out/'overlay-validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
