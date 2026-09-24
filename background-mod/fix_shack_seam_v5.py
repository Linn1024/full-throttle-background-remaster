"""Use one registered porch texture across the fixed/raised sprite boundary."""
import json,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

def main():
    folder=ROOT/'locations/018-mo-shack/custom-v1'
    review=ROOT/'reviews/shack-seam-v5';review.mkdir(exist_ok=True)
    name='018-mo-shack_room_pk_a01.dxt';dest=folder/name
    backup=review/'before.dxt'
    if not backup.exists():backup.write_bytes(dest.read_bytes())
    header,raw,current=read_dxt(backup)
    art=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGB'))
    h,w=current.shape[:2];yy,xx=np.mgrid[:h,:w].astype('float32')
    sampled=cv2.remap(art,xx*.5+857.4,yy*.5+143.85,cv2.INTER_LINEAR)
    shared=np.zeros((h,w),np.uint8)
    cv2.fillPoly(shared,[np.array([(0,600),(500,600),(500,658),(0,812)],np.int32)+[1386,0]],1)
    ropes=np.zeros((h,w),np.uint8)
    for points in [[(11,0),(39,0),(114,829),(73,829)],
                   [(250,0),(292,0),(376,890),(340,890)]]:
        cv2.fillPoly(ropes,[np.array(points,np.int32)+[1386,0]],1)
    shared[ropes>0]=0
    target=current.copy();target[shared>0,:3]=sampled[shared>0]
    png=review/'target.png';Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(review),str(png)],check=True,capture_output=True)
    encoded=png.with_suffix('.dds').read_bytes()[128:];result=bytearray(raw)
    changed=np.zeros((h,w),bool)
    for y in range(0,h,4):
        for x in range(0,w,4):
            sl=(slice(y,y+4),slice(x,x+4))
            if not shared[sl].any() or ropes[sl].any():continue
            at=((y//4)*(w//4)+x//4)*16
            result[at+8:at+16]=encoded[at+8:at+16];changed[sl]=True
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    dest.write_bytes(header[:12]+z.compress(result)+z.flush())
    decoded=read_dxt(dest)[2]
    assert np.array_equal(decoded[:,:,3],current[:,:,3])
    assert np.array_equal(decoded[~changed],current[~changed])
    assert np.array_equal(decoded[ropes>0],current[ropes>0])
    preview=Image.fromarray(art).convert('RGBA')
    preview.alpha_composite(Image.fromarray(decoded).crop((1386,0,1970,965)).resize((292,482)),(1550,144))
    preview.crop((1370,330,1910,780)).save(review/'packed-composite.png')
    p=folder/'overlay-validation.json';reports=json.loads(p.read_text())
    for report in reports:
        if report['file']==name:
            report.update(shared_porch_registered=True,seam_changed_blocks=int(changed.sum()//16),
                          ropes_identical=True,alpha_preserved=True,gameplay_verified=False)
    p.write_text(json.dumps(reports,indent=2))
    print('Shared porch registered; alpha, ropes and unedited blocks preserved.')

if __name__=='__main__':main()
