"""Install reviewed v14 scene paintings; preserve original room geometry/alpha."""
import json,shutil
from scene_assets import ROOT
from build_custom import build
ROOMS=['100-mr-truck','190-bikerock','191-mr-trkbk']
def main():
 for room in ROOMS:
  folder=ROOT/'locations'/room;review=ROOT/'reviews/vehicles-v14'/room;review.mkdir(parents=True,exist_ok=True)
  for name in ['custom-remaster-v1.png','room.json']:
   if not (review/name).exists():shutil.copy2(folder/name,review/name)
  shutil.copy2(ROOT/'edited'/f'{room}-v14.png',folder/'custom-remaster-v1.png')
  if room=='100-mr-truck':
   cfg=json.loads((folder/'room.json').read_text());cfg['protected']=[]
   (folder/'room.json').write_text(json.dumps(cfg,indent=2)+'\n')
  build(room)
if __name__=='__main__':main()
