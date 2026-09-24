"""Check installed derby assets and emit compact decoded-art review sheets."""
import argparse,json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt,read_chunk
from audit_derby_v21 import ROOMS,REV,GENERATED
from build_derby_sprites_v21 import GENERATED_IDS,VARIANTS,inventory,objects

def main():
 report=dict(rooms=[],atlases=[],monitors=[],gameplay_verified=False)
 sheet=Image.new('RGB',(1500,1305),'#222222');d=ImageDraw.Draw(sheet)
 for i,room in enumerate(ROOMS):
  folder=ROOT/'locations'/room;cfg=json.loads((folder/'room.json').read_text());size=tuple(cfg['size'])
  assert Image.open(folder/'custom-remaster-v1.png').size==size
  assert Image.open(folder/'custom-v1/in-game-texture-preview.png').size==size
  for name in cfg['layers']:
   a=read_chunk(ROOT/f'original/rooms/{room}/{name}');b=read_chunk(folder/'custom-v1'/name);assert a['header']==b['header']
   for x,y in zip(a['textures'],b['textures']):assert np.array_equal(np.array(x['image'])[:,:,3],np.array(y['image'])[:,:,3])
  report['rooms'].append(dict(room=room,size=size,geometry_identical=True,alpha_identical=True))
  im=Image.open(folder/'custom-v1/in-game-texture-preview.png');im.thumbnail((748,408));x=i%2*750;y=i//2*435;sheet.paste(im,(x,y+24));d.text((x+5,y+5),room,fill='white')
 sheet.save(REV/'backgrounds-packed.jpg')
 rows=inventory();review=[]
 for i in GENERATED_IDS+list(VARIANTS):
  for name in rows[i]['paths']:
   src=ROOT/name;folder=ROOT/'locations'/('056-arena' if int(src.parent.name[:3])<300 else '142-derbypit')/'custom-v1';dest=folder/src.name
   assert dest.exists(),name
   a=read_dxt(src)[2];b=read_dxt(dest)[2];assert np.array_equal(a[:,:,3],b[:,:,3]),name
   # Isolated all-black shadow sprites, not black paint within a car body.
   n,labels=cv2.connectedComponents((a[:,:,3]>0).astype('uint8'))
   colored=np.bincount(labels.ravel(),weights=(a[:,:,:3].max(axis=2)>0).ravel(),minlength=n)>0
   colored[0]=True;shadow=~colored[labels]
   assert np.array_equal(a[shadow],b[shadow]),name
   changed=(np.max(abs(a[:,:,:3].astype(int)-b[:,:,:3]),axis=2)>3)&(a[:,:,3]>0)
   assert changed.sum()>100,name
   item=dict(id=i,file=name,alpha_identical=True,black_shadows_identical=True,changed_pixels=int(changed.sum()))
   if 13<=i<=17 or i>=100:
    bright=(a[:,:,0]>180)&(a[:,:,1]>100)&(a[:,:,3]>200)
    dark=(b[:,:,:3].max(axis=2)<50)&bright
    item['bright_flame_to_dark_fraction']=float(dark.sum()/max(1,bright.sum()))
    assert item['bright_flame_to_dark_fraction']<.025,item
   report['atlases'].append(item)
  review.append((i,b))
 for page in range(0,len(review),9):
  s=Image.new('RGB',(1200,1260),'#333333');draw=ImageDraw.Draw(s)
  for k,(i,b) in enumerate(review[page:page+9]):
   im=Image.fromarray(b);im.thumbnail((395,390));x=k%3*400;y=k//3*420;s.paste(im,(x,y+24),im);draw.text((x+3,y+3),f'Atlas {i}',fill='white')
  s.save(REV/f'packed-atlases-{page//9}.jpg')
 for frame in range(1,17):
  name=f'extra_tvmonitors_f{frame}.chnk';a=read_chunk(ROOT/'original/rooms/059-rips-box'/name);b=read_chunk(ROOT/'locations/059-rips-box/custom-v1'/name)
  assert a['header']==b['header'];assert all(np.array_equal(np.array(x['image'])[:,:,3],np.array(y['image'])[:,:,3]) for x,y in zip(a['textures'],b['textures']))
  report['monitors'].append(dict(frame=frame,geometry_identical=True,alpha_identical=True))
 # Room overlays exclude every white control/mask component.
 for room in ['056-arena','057-demowall']:
  name=f'{room}_room_pk_a00.dxt';a=read_dxt(ROOT/f'original/rooms/{room}/{name}')[2];b=read_dxt(ROOT/f'locations/{room}/custom-v1/{name}')[2]
  white=(a[:,:,:3].min(axis=2)>245)&(a[:,:,3]>0);assert np.array_equal(a[white],b[white])
 (REV/'validation.json').write_text(json.dumps(report,indent=2))
 prompts=[]
 for p in sorted(REV.glob('generation-*.json')):prompts.append(dict(record=p.name,**json.loads(p.read_text())))
 provenance=dict(backgrounds=[dict(room=room,generated_file=f'exec-{g}.png',reference=f'locations/{room}/official-remaster.png',request_summary='Faithful detailed hand-painted redraw; retain full frame, camera geometry, signs, colors and all object positions.') for room,g in zip(ROOMS,GENERATED)],initial_car_pages=[dict(id=1,generated_file='exec-b22ce1a0-0629-4f03-9ed1-0f2407defa43.png'),dict(id=2,generated_file='exec-2b9fa5e1-7b35-4a3d-ab38-ce8a1964d675.png')],generations=prompts)
 (REV/'prompts.json').write_text(json.dumps(provenance,indent=2))
 print(f"Verified {len(report['rooms'])} backgrounds, {len(report['atlases'])} costume atlases, 2 room atlases and {len(report['monitors'])} monitor frames.")

def check_helper():
 config=json.loads((ROOT/'live-switcher/textures.json').read_text());by={r['name']:r for r in config['textures']};rows=inventory();count=0
 for i in GENERATED_IDS+list(VARIANTS):
  for name in rows[i]['paths']:
   p=ROOT/name;room='056-arena' if int(p.parent.name[:3])<300 else '142-derbypit';key=room+'/'+p.stem
   assert key in by,key
   raw=read_dxt(ROOT/'locations'/room/'custom-v1'/p.name)[1]
   assert by[key]['custom']['sha256']==hashlib.sha256(raw).hexdigest(),key
   count+=1
 print(f'Helper includes all {count} derby costume files with current payload hashes; {len(config["textures"])} total pairs.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check-helper',action='store_true');a=p.parse_args()
 if a.check_helper:check_helper()
 else:main()
