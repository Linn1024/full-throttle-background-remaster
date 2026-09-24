"""Build scene composites from decoded atlases and recorded registrations."""
import json
import cv2
import numpy as np
from PIL import Image,ImageDraw
from scene_assets import ROOT,read_dxt

def main():
 audit=ROOT/'overlay-audit';built=json.loads((audit/'built.json').read_text())
 sources={r['file']:r for r in json.loads((audit/'registration.json').read_text())}
 cards=[];index=[]
 for row in built:
  room=row['room'];folder=ROOT/'locations'/room/'custom-v1'
  art=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGBA'))
  _,_,atlas=read_dxt(folder/row['file'])
  _,labels,stats,_=cv2.connectedComponentsWithStats((atlas[:,:,3]>0).astype('uint8'),8)
  for reg in row['registrations']:
   ci=reg['candidate'];c=sources[row['file']]['candidates'][ci]
   x0,y0,x1,y1=c['atlas_bounds'];counts=np.bincount(labels[y0:y1+1,x0:x1+1].ravel());counts[0]=0
   if not counts.any():continue
   label=int(counts.argmax());x,y,w,h,area=stats[label]
   sprite=atlas[y:y+h,x:x+w].copy();sprite[labels[y:y+h,x:x+w]!=label]=0
   scale=reg['scale'];sx,sy=reg['shift']
   matrix=np.array([[scale,0,sx+x*scale],[0,scale,sy+y*scale]],dtype='float32')
   overlay=cv2.warpAffine(sprite,matrix,(art.shape[1],art.shape[0]),flags=cv2.INTER_LINEAR)
   preview=Image.alpha_composite(Image.fromarray(art),Image.fromarray(overlay)).convert('RGB')
   name=f'{row["file"]}-state-{ci}.png';preview.save(audit/name)
   im=preview.copy();im.thumbnail((550,310));card=Image.new('RGB',(560,340),(25,25,25));card.paste(im,(0,25));ImageDraw.Draw(card).text((3,4),f'{room} atlas {row["file"][-6:-4]} state {ci}',fill='white');cards.append(card)
   index.append(dict(room=room,file=row['file'],candidate=ci,preview=name,registration_only=True))
 for start in range(0,len(cards),9):
  page=Image.new('RGB',(1680,1020),(25,25,25))
  for i,card in enumerate(cards[start:start+9]):page.paste(card,((i%3)*560,(i//3)*340))
  page.save(audit/f'scenes-{start//9+1}.jpg')
 (audit/'composites.json').write_text(json.dumps(index,indent=2));print(len(cards),'composite previews')

if __name__=='__main__':main()
