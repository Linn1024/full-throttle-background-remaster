"""Transfer the existing custom scenery into both motorcycle overlay atlases.

The motorcycle states include an opaque copy of the room behind the bike.
Keep the original bike, suspension cables, alpha and unused atlas blocks.
This is texture integration of the approved artwork, not a new repaint.
"""
import json
import subprocess
import zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt


def main():
    room='017-mo-shop'
    source=ROOT/'original/rooms'/room
    folder=ROOT/'locations'/room
    out=folder/'custom-v1'
    art=np.array(Image.open(out/'in-game-texture-preview.png').convert('RGB'))
    official=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
    # Original game silhouette stored at twice the background texture resolution.
    _,_,mask_atlas=read_dxt(source/f'{room}_room_pk_a02.dxt')
    bike=cv2.resize(mask_atlas[:974,:1298,3],(649,487),interpolation=cv2.INTER_AREA)>0
    reports=[]
    for state,height,bike_y in [('00',864,344),('01',621,128)]:
        name=f'{room}_room_pk_a{state}.dxt'
        data,raw,original=read_dxt(source/name)
        target=original.copy()
        protected=np.zeros(original.shape[:2],np.uint8)
        protected[bike_y:bike_y+487,16:665]=bike.astype(np.uint8)
        # The vertical lifting cables are foreground, absent from the bare room.
        for x0,x1 in [(70,87),(214,235),(371,393),(500,522)]:
            protected[:height,x0:x1]=1
        protected=cv2.dilate(protected,np.ones((5,5),np.uint8))
        dist=cv2.distanceTransform(1-protected,cv2.DIST_L2,5)
        weight=np.minimum(dist[:height,:680]/8,1)[:,:,None]
        target[:height,:680,:3]=np.rint(
            art[:height,669:1349]*weight+original[:height,:680,:3]*(1-weight)).astype(np.uint8)
        editable=np.zeros(original.shape[:2],bool)
        editable[:height,:680]=True
        if state=='00':
            # Separate inventory-state sprite: the small can has been removed.
            # Registered on six independent original floor/cabinet patches.
            # Include its antialiased right/bottom gutter to avoid an old frame.
            x,y,w,h,sx,sy=764,0,161,145,1710,770
            sprite=original[y:y+h,x:x+w]
            before=official[sy:sy+h,sx:sx+w]
            after=art[sy:sy+h,sx:sx+w]
            # Explicit can+shadow footprint, including both versions' edge.
            # A colour-difference mask falsely protected textured floor pixels
            # and let small blue can highlights bleed into the empty state.
            removed=np.zeros((h,w),dtype='uint8')
            points=np.array([(12,0),(138,0),(139,67),(123,93),(18,93),(7,72),(8,45),(17,32)],np.int32)
            cv2.fillPoly(removed,[points],1)
            removed=cv2.dilate(removed,np.ones((5,5),np.uint8))
            blend=np.minimum(cv2.distanceTransform(1-removed,cv2.DIST_L2,5)/8,1)[:,:,None]
            target[y:y+h,x:x+w,:3]=np.rint(after*blend+sprite[:,:,:3]*(1-blend)).astype('uint8')
            protected[y:y+h,x:x+w]|=removed
            editable[y:y+h,x:x+w]=True
        png=out/(name+'.png')
        Image.fromarray(target).save(png)
        subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(out),str(png)],check=True,capture_output=True)
        encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:])
        assert len(encoded)==len(raw)
        changed=0
        for by in range(256):
            for bx in range(256):
                at=(by*256+bx)*16
                # Blocks touching a protected object remain byte-for-byte original.
                keep=not editable[by*4:by*4+4,bx*4:bx*4+4].any() or protected[by*4:by*4+4,bx*4:bx*4+4].any()
                if keep:encoded[at:at+16]=raw[at:at+16]
                else:
                    encoded[at:at+8]=raw[at:at+8]
                    changed+=1
        compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
        dest=out/name
        dest.write_bytes(data[:12]+compressor.compress(encoded)+compressor.flush())
        _,newraw,decoded=read_dxt(dest)
        assert np.array_equal(original[:,:,3],decoded[:,:,3])
        assert np.array_equal(original[protected!=0],decoded[protected!=0])
        # Composite the actual packed overlay for offline visual inspection.
        preview=art.copy()
        preview[:height,669:1349]=decoded[:height,:680,:3]
        Image.fromarray(preview).save(out/f'overlay-state-{state}-preview.png')
        if state=='00':
            preview=Image.fromarray(preview).convert('RGBA')
            preview.alpha_composite(Image.fromarray(decoded[:145,764:925]),(1710,770))
            preview.convert('RGB').save(out/'can-removed-overlay-preview.png')
            preview.crop((1640,710,1940,990)).resize((900,840)).convert('RGB').save(out/'can-removed-detail.png')
            # The empty-can region must remain byte-for-byte original.
            assert np.array_equal(decoded[:145,764:925][removed!=0],sprite[removed!=0])
        reports.append(dict(file=name,changed_blocks=changed,alpha_preserved=True,
                            motorcycle_and_cables_identical=True,can_removed_scenery_updated=state=='00'))
    (out/'overlay-validation.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
