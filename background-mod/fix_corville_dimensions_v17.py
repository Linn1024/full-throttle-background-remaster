"""Register the existing panorama to original room coordinates before packing."""
import shutil,json
import cv2,numpy as np
from PIL import Image
from scene_assets import ROOT
from build_custom import build

def main():
 folder=ROOT/'locations/051-corville';rev=ROOT/'reviews/corville-v17';rev.mkdir(parents=True,exist_ok=True)
 src=folder/'custom-remaster-v1.png';backup=rev/'before.png'
 if not backup.exists():shutil.copy2(src,backup)
 art=np.array(Image.open(backup).convert('RGB'));official=np.array(Image.open(folder/'official-remaster.png').convert('RGB'))
 size=(3820,1200);small=(1910,600)
 a=cv2.resize(art,small);b=cv2.resize(official,small)
 gray=lambda x:cv2.GaussianBlur(cv2.cvtColor(x,cv2.COLOR_RGB2GRAY),(0,0),2)
 flow=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(gray(b),gray(a),None)
 flow=cv2.GaussianBlur(flow,(0,0),12)
 # Smooth coordinate registration, not newly synthesized artwork.
 flow=cv2.resize(flow,size)*2;yy,xx=np.mgrid[:1200,:3820].astype('float32')
 full=cv2.resize(art,size,interpolation=cv2.INTER_LANCZOS4)
 result=cv2.remap(full,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT101)
 Image.fromarray(result).save(src)
 (rev/'registration.json').write_text(json.dumps(dict(original_source_size=[art.shape[1],art.shape[0]],target_size=list(size),registration='Smoothed original-to-custom optical flow',median_displacement=float(np.median(np.linalg.norm(flow,axis=2)))),indent=2))
 build('051-corville')
if __name__=='__main__':main()
