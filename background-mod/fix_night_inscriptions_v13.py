"""Reuse approved daytime sign faces in the night room, retaining its surrounds."""
import json, shutil
import numpy as np
from PIL import Image
from scene_assets import ROOT
from fix_sign_boundaries_v8 import JOBS

def main():
    folder=ROOT/'locations/116-dumpst-n'
    review=ROOT/'reviews/night-signs-v13';review.mkdir(exist_ok=True,parents=True)
    dest=folder/'custom-remaster-v1.png';cfgpath=folder/'room.json'
    for src,name in [(dest,'before.png'),(cfgpath,'room-before.json')]:
        if not (review/name).exists():shutil.copy2(src,review/name)
    size=(2220,1200)
    def read(p):return np.array(Image.open(p).convert('RGB').resize(size,Image.Resampling.LANCZOS)).astype(float)
    base=read(review/'before.png');night=read(folder/'official-remaster.png')
    day=read(ROOT/'scene/official-remaster.png')
    oldcfg=json.loads((review/'room-before.json').read_text())
    yy,xx=np.mgrid[:size[1],:size[0]];weight=np.ones(xx.shape)
    for x0,y0,x1,y1 in oldcfg['protected']:
        dx=np.maximum(np.maximum(x0-xx,xx-x1),0);dy=np.maximum(np.maximum(y0-yy,yy-y1),0)
        weight=np.minimum(weight,np.clip(np.hypot(dx,dy)/40,0,1))
    base=np.rint(base*weight[:,:,None]+night*(1-weight[:,:,None])).astype('uint8')
    before=base.copy();coverage=np.zeros(xx.shape,bool);reports=[]
    for key,_,box,_ in JOBS[:2]:
        x0,y0,x1,y1=box;s=np.s_[y0:y1,x0:x1]
        mask=np.array(Image.open(ROOT/'reviews/sign-boundaries-v8'/f'{key}-mask.png'))
        art=np.array(Image.open(ROOT/'reviews/sign-boundaries-v8'/f'{key}-fixed.png').convert('RGB')).astype(float)
        # Fit the existing day-to-night color relationship on the same sign.
        # A luminance fit avoids unstable RGB coefficients on nearly gray labels.
        lum=day[s]@np.array([.2126,.7152,.0722]);active=mask>240
        design=np.column_stack([lum[active],np.ones(active.sum())])
        coef=np.linalg.lstsq(design,night[s][active],rcond=None)[0]
        mapped=np.clip((art@np.array([.2126,.7152,.0722]))[:,:,None]*coef[0]+coef[1],0,255)
        a=mask[:,:,None]/255
        base[s]=np.rint(mapped*a+base[s]*(1-a)).astype('uint8')
        coverage[s]|=mask>0
        Image.fromarray(base[s]).resize((2*(x1-x0),2*(y1-y0))).save(review/f'{key}-night.png')
        reports.append(dict(sign=key,box=box,luminance_to_night_rgb=coef.tolist()))
    assert np.array_equal(base[~coverage],before[~coverage])
    Image.fromarray(base).save(dest)
    cfg=json.loads(cfgpath.read_text());cfg['protected']=[];cfgpath.write_text(json.dumps(cfg,indent=2)+'\n')
    (review/'validation.json').write_text(json.dumps(dict(signs=reports,outside_sign_masks_unchanged=True),indent=2)+'\n')
    from build_custom import build
    build('116-dumpst-n')

if __name__=='__main__':main()
