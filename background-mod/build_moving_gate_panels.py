"""Project the approved gate material into the previously untouched moving panels.

Retains existing floor replacements, original poses, alpha and hard drawn edges.
No new artwork is generated: material detail comes from the installed closed gate.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scene_assets import ROOT, read_dxt
from build_reported_states_v2 import pack

# Coordinates measured on 512-square atlas previews, clockwise from top-left.
QUADS = [
 [(262,9),(274,12),(271,313),(224,342)],
 [(264,25),(329,1),(323,354),(262,307)],
 [(266,29),(331,1),(322,353),(264,307)],
 [(267,29),(330,1),(322,353),(265,307)],
 [(265,28),(314,1),(324,353),(263,307)],
 [(264,29),(304,1),(320,353),(263,306)],
 [(266,28),(298,1),(287,353),(262,310)],
 [(264,28),(321,1),(315,352),(262,307)],
 [(265,27),(329,1),(323,353),(263,307)],
 [(184,1),(268,26),(268,296),(194,360)],
 [(91,4),(267,7),(262,280),(103,297)],
]

def main():
    folder=ROOT/'locations/026-gas-gate/custom-v1'
    root=ROOT/'original/costumes/103-pick-lock-cos'
    refname='pick-lock-cos_akostume_pk_a11.dxt'
    old=read_dxt(root/refname)[2][:,:,:3].astype('float32')
    new=read_dxt(folder/refname)[2][:,:,:3].astype('float32')
    delta=(new-cv2.GaussianBlur(new,(0,0),12))-(old-cv2.GaussianBlur(old,(0,0),12))
    # Material transfer must not stamp the reference pose's bars, plate border
    # or rivets onto a differently foreshortened pose.
    edges=cv2.Canny(cv2.cvtColor(old.astype('uint8'),cv2.COLOR_RGB2GRAY),10,20)
    edge_guard=cv2.dilate(edges,np.ones((61,61),np.uint8))>0
    delta[edge_guard]=0
    delta=np.clip(delta,-20,20)
    src=np.float32([(153,20),(284,7),(277,284),(151,275)])*4
    cards=[]
    for n,points in enumerate(QUADS):
        source=root/f'pick-lock-cos_akostume_pk_a{n:02}.dxt'
        original=read_dxt(source)[2]; h,w=original.shape[:2]
        backup=folder/(source.name+'.before-panels-v3')
        if not backup.exists():backup.write_bytes((folder/source.name).read_bytes())
        current=read_dxt(backup)[2]
        poly=np.float32(points)*4
        H=cv2.getPerspectiveTransform(src,poly)
        material=cv2.warpPerspective(delta,H,(w,h),flags=cv2.INTER_LINEAR)
        mask=np.zeros((h,w),np.uint8);cv2.fillConvexPoly(mask,poly.astype('int32'),1)
        # Keep solid ink, silhouette edges and Ben's hand in the final turn.
        gray=cv2.cvtColor(original[:,:,:3],cv2.COLOR_RGB2GRAY)
        ink=cv2.dilate((gray<14).astype('uint8'),np.ones((3,3),np.uint8))
        mask[(original[:,:,3]<255)|(ink>0)]=0
        if n==10:mask[:480,:540]=0
        weight=np.minimum(cv2.distanceTransform(mask,cv2.DIST_L2,5)/5,1)
        target=current.copy()
        target[:,:,:3]=np.clip(np.rint(current[:,:,:3].astype(float)+material*weight[:,:,None]),0,255).astype('uint8')
        # All previously edited floor pixels remain eligible for repacking.
        prior=np.any(current!=original,axis=2)
        decoded=pack(source,folder,target,prior|(weight>0),scope='approved gate material on moving panels plus existing ground',
                     panel_pixels=int((weight>0).sum()))
        assert np.array_equal(decoded[:480,:540],original[:480,:540]) if n==10 else True
        card=Image.new('RGB',(600,330),'#292929');draw=ImageDraw.Draw(card)
        for j,a in enumerate([original,decoded]):
            im=Image.fromarray(a);im.thumbnail((300,300));card.paste(im,(j*300,25),im)
            draw.text((j*300+4,4),f'a{n:02} '+['official','custom'][j],fill='white')
        cards.append(card)
    sheet=Image.new('RGB',(1200,330*6),'#292929')
    for i,card in enumerate(cards):sheet.paste(card,((i%2)*600,(i//2)*330))
    sheet.save(ROOT/'previews/moving-panels-v3-review.jpg')
    update_open_state(folder,delta,src)


def update_open_state(folder,delta=None,src=None):
    room=ROOT/'original/rooms/026-gas-gate'
    source=room/'026-gas-gate_room_pk_a01.dxt'
    original=read_dxt(source)[2];h,w=original.shape[:2]
    reference=read_dxt(room/'026-gas-gate_room_pk_a00.dxt')[2]
    replacement=read_dxt(folder/'026-gas-gate_room_pk_a00.dxt')[2]
    backup=folder/(source.name+'.before-panels-v3')
    if not backup.exists():backup.write_bytes((folder/source.name).read_bytes())
    current=read_dxt(backup)[2]
    sift=cv2.SIFT_create(nfeatures=10000)
    k,d=sift.detectAndCompute(cv2.cvtColor(reference[:,:,:3],cv2.COLOR_RGB2GRAY),(reference[:,:,3]>250).astype('uint8')*255)
    q,e=sift.detectAndCompute(cv2.cvtColor(original[:,:,:3],cv2.COLOR_RGB2GRAY),(original[:,:,3]>250).astype('uint8')*255)
    matches=[a for a,b in cv2.BFMatcher().knnMatch(e,d,k=2) if a.distance<.65*b.distance]
    aa=np.float32([q[m.queryIdx].pt for m in matches]);bb=np.float32([k[m.trainIdx].pt for m in matches])
    A,ok=cv2.estimateAffinePartial2D(aa,bb,ransacReprojThreshold=2)
    assert ok.sum()>=40 and np.max(np.abs(A[:,:2]-np.eye(2)))<.002
    shift=np.median(bb[ok.ravel()>0]-aa[ok.ravel()>0],axis=0)
    yy,xx=np.mgrid[:h,:w].astype('float32');mx=xx+shift[0];my=yy+shift[1]
    before=cv2.remap(reference[:,:,:3],mx,my,cv2.INTER_LINEAR)
    after=cv2.remap(replacement[:,:,:3],mx,my,cv2.INTER_LINEAR)
    region=(xx>900)&(xx<1540)&(yy<1240)&(original[:,:,3]>0)
    diff=np.max(np.abs(original[:,:,:3].astype(float)-before),axis=2)
    valid=region&(diff<25)
    weight=np.minimum(cv2.distanceTransform(valid.astype('uint8'),cv2.DIST_L2,5)/4,1)[:,:,None]
    target=current.copy();target[:,:,:3]=np.rint(after*weight+current[:,:,:3]*(1-weight)).astype('uint8')
    # The other piece contains static scenery outside the opening. Its
    # independently audited 49-inlier registration uses room coordinates.
    scene=ROOT/'locations/026-gas-gate'
    old_scene=np.array(Image.open(scene/'official-remaster.png').convert('RGB'))
    new_scene=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGB'))
    mx2=xx*.5+1273.365234375;my2=yy*.5+378.9064025878906
    before2=cv2.remap(old_scene,mx2,my2,cv2.INTER_LINEAR)
    after2=cv2.remap(new_scene,mx2,my2,cv2.INTER_LINEAR)
    static=(xx<900)&(original[:,:,3]==255)&(np.max(np.abs(original[:,:,:3].astype(float)-before2),axis=2)<20)
    blend=np.minimum(cv2.distanceTransform(static.astype('uint8'),cv2.DIST_L2,5)/5,1)[:,:,None]
    target[:,:,:3]=np.rint(after2*blend+target[:,:,:3]*(1-blend)).astype('uint8')
    panel=np.zeros((h,w),np.uint8)
    if delta is not None:
        poly=np.float32([(126,58),(192,30),(184,389),(121,338)])*4
        H=cv2.getPerspectiveTransform(src,poly)
        detail=cv2.warpPerspective(delta,H,(w,h),flags=cv2.INTER_LINEAR)
        cv2.fillConvexPoly(panel,poly.astype('int32'),1)
        panel[(original[:,:,3]<255)|(cv2.cvtColor(original[:,:,:3],cv2.COLOR_RGB2GRAY)<14)]=0
        pw=np.minimum(cv2.distanceTransform(panel,cv2.DIST_L2,5)/5,1)[:,:,None]
        target[:,:,:3]=np.clip(np.rint(target[:,:,:3].astype(float)+detail*pw),0,255).astype('uint8')
    pack(source,folder,target,np.any(current!=original,axis=2)|valid|static|(panel>0),scope='open-state doorway and exterior scenery plus gate material; white controls retained',registration_inliers=int(ok.sum()))

if __name__=='__main__':main()
