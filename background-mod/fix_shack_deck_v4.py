"""Replace only the artifacted raised-deck crop, preserving other atlas states."""
import json,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

def main():
    review=ROOT/'reviews/shack-deck-v4'
    folder=ROOT/'locations/018-mo-shack/custom-v1'
    name='018-mo-shack_room_pk_a01.dxt'
    dest=folder/name
    backup=review/'before.dxt'
    if not backup.exists():backup.write_bytes(dest.read_bytes())
    header,raw,current=read_dxt(backup)
    original=read_dxt(ROOT/'original/rooms/018-mo-shack'/name)[2]
    x0,y0,x1,y1=1386,580,1970,950
    w,h=x1-x0,y1-y0
    patch=np.array(Image.open(review/'deck-generated.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS)).astype(float)
    reference=original[y0:y1,x0:x1,:3].astype(float)
    # Match the original low-frequency night lighting; retain new grain detail.
    patch=np.clip(patch+cv2.GaussianBlur(reference,(0,0),12)-cv2.GaussianBlur(patch,(0,0),12),0,255)
    yy,xx=np.mgrid[:h,:w]
    weight=np.clip(np.minimum.reduce([xx,yy,w-1-xx,h-1-yy])/16,0,1)[:,:,None]
    target=current.copy()
    target[y0:y1,x0:x1,:3]=np.rint(patch*weight+current[y0:y1,x0:x1,:3]*(1-weight)).astype('uint8')
    png=review/'target.png';Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(review),str(png)],check=True,capture_output=True)
    encoded=png.with_suffix('.dds').read_bytes()[128:]
    result=bytearray(raw);height,width=current.shape[:2];changed=np.zeros((height,width),bool)
    for y in range((y0+3)//4*4,y1-3,4):
        for x in range((x0+3)//4*4,x1-3,4):
            at=((y//4)*(width//4)+x//4)*16
            if not current[y:y+4,x:x+4,3].any():continue
            result[at+8:at+16]=encoded[at+8:at+16]
            changed[y:y+4,x:x+4]=True
    z=zlib.compressobj(9,zlib.DEFLATED,-15)
    dest.write_bytes(header[:12]+z.compress(result)+z.flush())
    decoded=read_dxt(dest)[2]
    assert np.array_equal(decoded[:,:,3],original[:,:,3])
    assert np.array_equal(decoded[~changed],current[~changed])
    Image.fromarray(decoded[y0:y1,x0:x1]).save(review/'deck-packed.png')
    report_path=folder/'overlay-validation.json'
    reports=json.loads(report_path.read_text())
    for report in reports:
        if report['file']==name:
            report.update(deck_repaired=True,deck_changed_blocks=int(changed.sum()//16),
                          outside_deck_identical=True,alpha_preserved=True,gameplay_verified=False)
    report_path.write_text(json.dumps(reports,indent=2))
    print('Raised deck repaired; original alpha and all pixels outside edited blocks preserved.')

if __name__=='__main__':main()
