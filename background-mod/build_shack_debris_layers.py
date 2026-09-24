"""Pack generated detail into the four separately drawn debris CHNK assets."""
import json
import struct
import subprocess
import zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_chunk, render

def main():
    room='018-mo-shack'
    folder=ROOT/'locations'/room/'custom-v1'
    reports=[]
    for layer in (10,20,30,40):
        path=ROOT/'original/rooms'/room/f'124-debris-image-frame0-layer{layer}.chnk'
        chunk=read_chunk(path);payloads=[];checks=[]
        for i,tex in enumerate(chunk['textures']):
            original=np.array(tex['image']);h,w=original.shape[:2]
            art=np.array(Image.open(ROOT/'edited'/f'debris-layer{layer}-v1.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS)).astype('float32')
            base=original[:,:,:3].astype('float32')
            # Retain original broad shading and palette while adding painted detail.
            rgb=art+cv2.GaussianBlur(base,(0,0),10)-cv2.GaussianBlur(art,(0,0),10)
            target=original.copy();target[:,:,:3]=np.clip(np.rint(rgb),0,255).astype('uint8')
            png=folder/f'{path.stem}-texture{i}.png';Image.fromarray(target).save(png)
            subprocess.run([str(ROOT/'tools/texconv.exe'),'-f','BC3_UNORM','-m','1','-y','-o',str(folder),str(png)],check=True,capture_output=True)
            encoded=bytearray(png.with_suffix('.dds').read_bytes()[128:]);raw=tex['raw'];count=0
            for by in range(h//4):
                for bx in range(w//4):
                    at=(by*(w//4)+bx)*16
                    if not original[by*4:by*4+4,bx*4:bx*4+4,3].any():
                        encoded[at:at+16]=raw[at:at+16]
                    else:
                        encoded[at:at+8]=raw[at:at+8];count+=1
            decoded=np.array(Image.frombytes('RGBA',(w,h),bytes(encoded),'bcn',(3,'DXT5')))
            assert np.array_equal(decoded[:,:,3],original[:,:,3])
            z=zlib.compressobj(9,zlib.DEFLATED,-15)
            p=tex['payload'][:12]+z.compress(encoded)+z.flush()
            payloads.append(struct.pack('<I',len(p))+p+b'\0'*(-len(p)%4))
            checks.append(dict(texture=i,changed_blocks=count,alpha_preserved=True,protected_foreground_identical=True))
        dest=folder/path.name;dest.write_bytes(chunk['header']+b''.join(payloads))
        packed=read_chunk(dest);assert packed['header']==chunk['header']
        render(packed,(700,1100)).save(folder/f'{path.stem}-preview.png')
        reports.append(dict(file=path.name,textures=checks,builder='shack-debris-layers-v1',
                            scope='environment-only debris; original geometry and compressed alpha retained',gameplay_verified=False))
    (folder/'extra-chunk-validation.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
