"""Composite reviewed lettering strictly inside Todd's four existing plaques."""
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scene_assets import ROOT

def main():
    review=ROOT/'reviews/todd-lettering-v9'
    folder=ROOT/'locations/023-todds'
    dest=folder/'custom-remaster-v1.png'
    backup=review/'before.png'
    if not backup.exists():shutil.copy2(dest,backup)
    cfgpath=folder/'room.json'
    if not (review/'room-before.json').exists():shutil.copy2(cfgpath,review/'room-before.json')
    base=Image.open(backup).convert('RGB').resize((2220,1200),Image.Resampling.LANCZOS)
    # This rectangle was previously drawn from official pixels by build_custom.
    # Carry that visible surround into the source before removing protection.
    oldcfg=json.loads((review/'room-before.json').read_text())
    official=Image.open(folder/'official-remaster.png').convert('RGB')
    yy,xx=np.mgrid[:1200,:2220]
    weight=np.ones((1200,2220),dtype=float)
    for x0,y0,x1,y1 in oldcfg['protected']:
        dx=np.maximum(np.maximum(x0-xx,xx-x1),0)
        dy=np.maximum(np.maximum(y0-yy,yy-y1),0)
        weight=np.minimum(weight,np.clip(np.hypot(dx,dy)/40,0,1))
    weight=weight[:,:,None]
    base=Image.fromarray(np.rint(np.array(base)*weight+np.array(official)*(1-weight)).astype('uint8'))
    box=(620,370,920,650)
    old=base.crop(box)
    art=Image.open(review/'generated.png').convert('RGB').resize(old.size,Image.Resampling.LANCZOS)
    mask=Image.new('L',old.size);draw=ImageDraw.Draw(mask)
    for p in [[(101,10),(182,0),(184,25),(101,43)],
              [(119,60),(206,56),(205,90),(119,92)],
              [(79,110),(143,122),(136,151),(72,138)],
              [(160,127),(226,126),(226,165),(153,166)]]:
        draw.polygon(p,fill=255)
    hard=np.array(mask);soft=np.minimum(hard,np.array(mask.filter(ImageFilter.GaussianBlur(.6))))
    # Keep the room's subdued sign exposure while retaining generated fine detail.
    a=np.array(art).astype(float);b=np.array(old).astype(float)
    import cv2
    a=np.clip(a+cv2.GaussianBlur(b,(0,0),8)-cv2.GaussianBlur(a,(0,0),8),0,255).astype('uint8')
    result=Image.composite(Image.fromarray(a),old,Image.fromarray(soft))
    assert np.array_equal(np.array(result)[hard==0],b.astype('uint8')[hard==0])
    base.paste(result,box[:2]);base.save(dest);result.save(review/'fixed.png')
    cfg=json.loads(cfgpath.read_text());cfg['protected']=[]
    cfgpath.write_text(json.dumps(cfg,indent=2)+'\n')
    # These state sprites contain parts of the same signs and wall. Updating
    # only the room creates a visible split when the refrigerator opens.
    from build_custom import build
    from build_todd_overlays import main as build_states
    build('023-todds')
    build_states()

if __name__=='__main__':main()
