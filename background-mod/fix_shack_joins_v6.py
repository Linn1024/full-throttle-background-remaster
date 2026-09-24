"""Register fixed scenery in both raised-platform and porch-edge sprites."""
import json,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

FOLDER=ROOT/'locations/018-mo-shack/custom-v1'
REVIEW=ROOT/'reviews/shack-joins-v6'

def pack(n,backup,target,active):
    name=f'018-mo-shack_room_pk_a{n:02}.dxt'
    header,raw,current=read_dxt(backup)
    original=read_dxt(ROOT/'original/rooms/018-mo-shack'/name)[2]
    # Some neighboring atlas cells are white control masks, not rendered art.
    controls=(original[:,:,:3].min(axis=2)>225)&(original[:,:,3]>0)
    target[controls]=current[controls];active[controls]=False
    png=REVIEW/f'target-{n}.png';Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(REVIEW),str(png)],check=True,capture_output=True)
    encoded=png.with_suffix('.dds').read_bytes()[128:];result=bytearray(raw)
    h,w=current.shape[:2];changed=np.zeros((h,w),bool)
    for y in range(0,h,4):
        for x in range(0,w,4):
            sl=(slice(y,y+4),slice(x,x+4))
            if not active[sl].any() or controls[sl].any():continue
            at=((y//4)*(w//4)+x//4)*16
            result[at+8:at+16]=encoded[at+8:at+16];changed[sl]=True
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    dest=FOLDER/name;dest.write_bytes(header[:12]+z.compress(result)+z.flush())
    decoded=read_dxt(dest)[2]
    assert np.array_equal(decoded[:,:,3],original[:,:,3])
    assert np.array_equal(decoded[~changed],current[~changed])
    assert np.array_equal(decoded[controls],current[controls])
    p=FOLDER/'overlay-validation.json';reports=json.loads(p.read_text())
    for report in reports:
        if report['file']==name:
            report.update(join_revision=6,join_changed_blocks=int(changed.sum()//16),
                          alpha_preserved=True,control_masks_identical=True,gameplay_verified=False)
    p.write_text(json.dumps(reports,indent=2))
    return decoded

def main():
    REVIEW.mkdir(exist_ok=True)
    art=np.array(Image.open(FOLDER/'in-game-texture-preview.png').convert('RGB'))
    # Undo the narrow v5 patch by starting from the repaired v4 deck.
    backup=ROOT/'reviews/shack-seam-v5/before.dxt'
    current=read_dxt(backup)[2];target=current.copy()
    y,x=np.mgrid[580:950,1386:1970].astype('float32')
    sampled=cv2.remap(art,x*.5+857.4,y*.5+143.85,cv2.INTER_LINEAR)
    shared=np.ones((370,584),np.uint8)
    # Actual moving deck and narrow suspension silhouettes, not full columns.
    for points in [[(25,255),(441,84),(527,109),(533,141),(397,301),(32,278)],
                   [(65,0),(83,0),(110,246),(81,246)],
                   [(309,0),(330,0),(369,280),(341,280)]]:
        cv2.fillPoly(shared,[np.array(points,np.int32)],0)
    weight=np.minimum(cv2.distanceTransform(shared,cv2.DIST_L2,5)/5,1)
    weight*=np.minimum(np.arange(370)[:,None]/32,1)
    before=target[580:950,1386:1970,:3]
    before[:]=np.rint(sampled*weight[:,:,None]+before*(1-weight[:,:,None])).astype('uint8')
    active=np.zeros(current.shape[:2],bool);active[580:950,1386:1970]=weight>0
    raised=pack(1,backup,target,active)
    backup=REVIEW/'before-a02.dxt'
    if not backup.exists():backup.write_bytes((FOLDER/'018-mo-shack_room_pk_a02.dxt').read_bytes())
    current=read_dxt(backup)[2];target=current.copy()
    y,x=np.mgrid[790:1610,0:520].astype('float32')
    target[790:1610,:520,:3]=cv2.remap(art,x*.5+1389.16,y*.5+123.64,cv2.INTER_LINEAR)
    active=np.zeros(current.shape[:2],bool);active[790:1610,:520]=True
    edge=pack(2,backup,target,active)
    original=read_dxt(ROOT/'original/rooms/018-mo-shack/018-mo-shack_room_pk_a02.dxt')[2]
    # The room's sprite UV excludes the neighboring white control cell.
    edge[original[:,:,:3].min(axis=2)>225,3]=0
    preview=Image.fromarray(art).convert('RGBA')
    preview.alpha_composite(Image.fromarray(edge).crop((0,790,520,1610)).resize((260,410)),(1389,519))
    preview.alpha_composite(Image.fromarray(raised).crop((1386,0,1970,965)).resize((292,482)),(1550,144))
    preview.crop((1370,330,1910,780)).save(REVIEW/'packed-composite.png')
    print('Both porch layers rebuilt; alpha, controls and unedited blocks checked.')

if __name__=='__main__':main()
