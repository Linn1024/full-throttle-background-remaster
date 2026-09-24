"""Register the reviewed General Surplus crop, retaining the v3 dumpster label."""
import numpy as np
from PIL import Image
from scene_assets import ROOT

def main():
    review=ROOT/'reviews/dumpster-v4'
    destination=ROOT/'scene/custom-remaster-v1.png'
    backup=review/'before-sign.png'
    if not backup.exists():
        Image.open(destination).save(backup)
    base=np.array(Image.open(backup).convert('RGB').resize((2220,1200),Image.Resampling.LANCZOS))
    x0,y0,x1,y1=1690,180,2120,480
    w,h=x1-x0,y1-y0
    patch=np.array(Image.open(review/'sign-generated.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS))
    yy,xx=np.mgrid[:h,:w]
    weight=np.clip(np.minimum.reduce([xx,yy,w-1-xx,h-1-yy])/16,0,1)[:,:,None]
    base[y0:y1,x0:x1]=np.rint(patch*weight+base[y0:y1,x0:x1]*(1-weight)).astype('uint8')
    Image.fromarray(base).save(destination)

if __name__=='__main__':main()
