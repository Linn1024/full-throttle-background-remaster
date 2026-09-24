"""Remove duplicated fixed-porch coverage, retaining the moving deck RGB."""
import hashlib,json,subprocess,zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_dxt

FOLDER=ROOT/'locations/018-mo-shack/custom-v1'
REVIEW=ROOT/'reviews/shack-joins-v7'

def main():
    REVIEW.mkdir(exist_ok=True)
    for n,bounds in [(1,(1386,580,1970,950)),(2,(0,790,520,1610))]:
        name=f'018-mo-shack_room_pk_a{n:02}.dxt';path=FOLDER/name
        backup=REVIEW/f'before-{n}.dxt'
        if not backup.exists():backup.write_bytes(path.read_bytes())
        header,raw,current=read_dxt(backup);target=current.copy()
        x0,y0,x1,y1=bounds;h,w=y1-y0,x1-x0
        if n==1:
            foreground=np.zeros((h,w),np.uint8)
            for points in [[(25,255),(441,84),(527,109),(533,141),(397,301),(32,278)],
                           [(65,0),(83,0),(110,246),(81,246)],
                           [(309,0),(330,0),(369,280),(341,280)]]:
                cv2.fillPoly(foreground,[np.array(points,np.int32)],1)
            coverage=cv2.GaussianBlur(foreground.astype('float32'),(3,3),.6)
            coverage=np.maximum(coverage,np.clip((24-np.arange(h)[:,None])/24,0,1))
            target[y0:y1,x0:x1,3]=np.rint(current[y0:y1,x0:x1,3]*coverage).astype('uint8')
        else:
            # This static railing/floor piece is already in the background.
            target[y0:y1,x0:x1,3]=0
        original=read_dxt(ROOT/'original/rooms/018-mo-shack'/name)[2]
        controls=original[:,:,:3].min(axis=2)>225
        target[controls,3]=current[controls,3]
        png=REVIEW/f'coverage-{n}.png';Image.fromarray(target).save(png)
        subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(REVIEW),str(png)],check=True,capture_output=True)
        encoded=png.with_suffix('.dds').read_bytes()[128:];result=bytearray(raw)
        height,width=current.shape[:2]
        trial=np.array(Image.frombytes('RGBA',(width,height),encoded,'bcn',(3,'DXT5')))
        for y in range(0,height,4):
            for x in range(0,width,4):
                sl=(slice(y,y+4),slice(x,x+4))
                if np.array_equal(target[sl][:,:,3],current[sl][:,:,3]):continue
                # Protect edge/control blocks outside the reviewed rectangle.
                if controls[sl].any():continue
                if (trial[sl][:,:,3]>current[sl][:,:,3]).any():continue
                at=((y//4)*(width//4)+x//4)*16
                result[at:at+8]=encoded[at:at+8]
        z=zlib.compressobj(9,zlib.DEFLATED,-15)
        path.write_bytes(header[:12]+z.compress(result)+z.flush())
        decoded=read_dxt(path)[2]
        assert np.array_equal(decoded[:,:,:3],current[:,:,:3])
        assert (decoded[:,:,3]<=original[:,:,3]).all()
        p=FOLDER/'overlay-validation.json';reports=json.loads(p.read_text())
        for report in reports:
            if report['file']==name:
                report.update(join_revision=7,alpha_preserved=False,scenery_alpha_removed=True,
                    alpha_change_bounds=[[x0//4*4,y0//4*4,(x1+3)//4*4,(y1+3)//4*4]],rgb_preserved_from_v6=True,
                    custom_alpha_sha256=hashlib.sha256(decoded[:,:,3].tobytes()).hexdigest(),
                    gameplay_verified=False)
        p.write_text(json.dumps(reports,indent=2))
    art=Image.open(FOLDER/'in-game-texture-preview.png').convert('RGBA')
    for n,box,pos,size in [(2,(0,810,520,1610),(1389,529),(260,400)),
                            (1,(1386,0,1970,965),(1550,144),(292,482))]:
        a=Image.fromarray(read_dxt(FOLDER/f'018-mo-shack_room_pk_a{n:02}.dxt')[2])
        art.alpha_composite(a.crop(box).resize(size),pos)
    art.crop((1370,330,1910,780)).save(REVIEW/'packed-composite.png')
    print('Duplicate porch coverage removed; RGB unchanged and opacity only reduced.')

if __name__=='__main__':main()
