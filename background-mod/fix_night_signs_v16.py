"""Composite direct night-painted signs without flattening their material contrast."""
import json,shutil
import numpy as np
from PIL import Image
from scene_assets import ROOT
from fix_sign_boundaries_v8 import JOBS
from build_custom import build

def main():
 folder=ROOT/'locations/116-dumpst-n';rev=ROOT/'reviews/night-signs-v16';rev.mkdir(exist_ok=True,parents=True)
 dest=folder/'custom-remaster-v1.png'
 if not (rev/'before.png').exists():shutil.copy2(dest,rev/'before.png')
 base=Image.open(rev/'before.png').convert('RGB');before=np.array(base);coverage=np.zeros(before.shape[:2],bool)
 for key,_,box,_ in JOBS[:2]:
  old=base.crop(box);mask=Image.open(ROOT/'reviews/sign-boundaries-v8'/f'{key}-mask.png')
  art=Image.open(rev/f'{key}-generated.png').convert('RGB').resize(old.size,Image.Resampling.LANCZOS)
  result=Image.composite(art,old,mask);base.paste(result,box[:2]);x0,y0,x1,y1=box;coverage[y0:y1,x0:x1]=np.array(mask)>0
  result.resize((old.width*3,old.height*3)).save(rev/f'{key}-composite.png')
 assert np.array_equal(np.array(base)[~coverage],before[~coverage])
 base.save(dest);build('116-dumpst-n')
 im=Image.open(folder/'custom-v1/in-game-texture-preview.png')
 # Separate comparisons avoid overlap at native crop sizes.
 for key,_,box,_ in JOBS[:2]:
  old=Image.open(rev/'before.png').crop(box);new=im.crop(box);p=Image.new('RGB',(old.width*2,old.height));p.paste(old,(0,0));p.paste(new,(old.width,0));p.resize((p.width*2,p.height*2)).save(rev/f'{key}-before-after.png')
 (rev/'validation.json').write_text(json.dumps(dict(outside_sign_masks_identical=True,room='116-dumpst-n',direct_night_painting=True),indent=2))
if __name__=='__main__':main()
