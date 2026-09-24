"""Integrate reviewed generated state art, retaining original BC3 alpha/masks.

Generation prompts and provenance are recorded in STATE-ART-V2.md.
This is texture packing/registration, not procedural artwork generation.
"""
import json, subprocess, zlib
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_dxt


def pack(source, folder, target, editable, **details):
    data, raw, original = read_dxt(source)
    h, w = original.shape[:2]
    target[:, :, 3] = original[:, :, 3]
    png = folder / (source.name + '.png')
    Image.fromarray(target).save(png)
    subprocess.run([str(ROOT/'tools/texconv.exe'), '-f', 'BC3_UNORM', '-m', '1', '-y', '-o', str(folder), str(png)], check=True, capture_output=True)
    encoded = bytearray(png.with_suffix('.dds').read_bytes()[128:])
    protected = (~editable) & (original[:, :, 3] > 0)
    changed = np.zeros((h, w), bool)
    for by in range(h//4):
        for bx in range(w//4):
            sl = (slice(by*4, by*4+4), slice(bx*4, bx*4+4)); at = (by*(w//4)+bx)*16
            if not editable[sl].any() or protected[sl].any():
                encoded[at:at+16] = raw[at:at+16]
            else:
                encoded[at:at+8] = raw[at:at+8]
                changed[sl] = True
    z = zlib.compressobj(9, zlib.DEFLATED, -15)
    dest = folder/source.name
    dest.write_bytes(data[:12] + z.compress(encoded) + z.flush())
    decoded = read_dxt(dest)[2]
    assert np.array_equal(decoded[:, :, 3], original[:, :, 3])
    assert np.array_equal(decoded[protected | ~changed], original[protected | ~changed])
    assert changed.sum() > 100
    p = folder/'overlay-validation.json'
    reports = json.loads(p.read_text()) if p.exists() else []
    report = dict(file=source.name, source=source.relative_to(ROOT/'original').as_posix(), builder='reported-states-v2',
                  changed_blocks=int(changed.sum()//16), alpha_preserved=True, excluded_pixels_identical=True, gameplay_verified=False, **details)
    reports = [r for r in reports if r['file'] != source.name] + [report]
    p.write_text(json.dumps(reports, indent=2))
    Image.fromarray(decoded).save(folder/(source.stem+'-v2-packed.png'))
    print(source.name, report['changed_blocks'], flush=True)
    return decoded


def generated_atlas(room, n, filename, retain_transfers):
    source = ROOT/f'original/rooms/{room}/{room}_room_pk_a{n:02}.dxt'
    folder = ROOT/'locations'/room/'custom-v1'
    original = read_dxt(source)[2]
    art = np.array(Image.open(ROOT/'edited'/filename).convert('RGB').resize((original.shape[1], original.shape[0]), Image.Resampling.LANCZOS)).astype('float32')
    base = original[:, :, :3].astype('float32')
    # Keep original broad lighting/color; take generated fine material detail.
    correction = cv2.GaussianBlur(base, (0, 0), 15)-cv2.GaussianBlur(art, (0, 0), 15)
    rgb = np.clip(art + correction*.85, 0, 255)
    if retain_transfers:
        current = read_dxt(folder/source.name)[2]
        backed = folder/(source.name+'.before-v2')
        if not backed.exists(): backed.write_bytes((folder/source.name).read_bytes())
        current = read_dxt(backed)[2]
        weight = (np.max(np.abs(current[:, :, :3].astype(float)-base), axis=2)>3).astype('float32')
        weight = cv2.GaussianBlur(weight, (0, 0), 1.5)[:, :, None]
        rgb = rgb*(1-weight)+current[:, :, :3]*weight
    target = original.copy(); target[:, :, :3] = np.rint(rgb).astype('uint8')
    # White control masks and blank/transparent atlas areas are not artwork.
    editable = (original[:, :, 3]>0) & (original[:, :, :3].min(axis=2)<225)
    return pack(source, folder, target, editable, generated_art=filename)


def lock_floor(new_reference):
    room = '026-gas-gate'; folder = ROOT/'locations'/room/'custom-v1'
    reference = read_dxt(ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt')[2]
    sift = cv2.SIFT_create(nfeatures=12000)
    k, d = sift.detectAndCompute(cv2.cvtColor(reference[:, :, :3], cv2.COLOR_RGB2GRAY), (reference[:, :, 3]>250).astype('uint8')*255)
    for n in range(10):
        source = ROOT/f'original/costumes/103-pick-lock-cos/pick-lock-cos_akostume_pk_a{n:02}.dxt'
        original = read_dxt(source)[2]; h, w = original.shape[:2]
        q, e = sift.detectAndCompute(cv2.cvtColor(original[:, :, :3], cv2.COLOR_RGB2GRAY), (original[:, :, 3]>250).astype('uint8')*255)
        matches = [a for a,b in cv2.BFMatcher().knnMatch(e,d,k=2) if a.distance<.7*b.distance]
        aa=np.float32([q[m.queryIdx].pt for m in matches]); bb=np.float32([k[m.trainIdx].pt for m in matches])
        A, ok=cv2.estimateAffinePartial2D(aa,bb,ransacReprojThreshold=2)
        assert ok.sum()>=20 and np.max(np.abs(A[:, :2]-np.eye(2)))<.002
        shift=np.median(bb[ok.ravel()>0]-aa[ok.ravel()>0],axis=0)
        yy,xx=np.mgrid[:h,:w].astype('float32'); mx=xx+shift[0]; my=yy+shift[1]
        before=cv2.remap(reference[:,:,:3],mx,my,cv2.INTER_LINEAR)
        after=cv2.remap(new_reference[:,:,:3],mx,my,cv2.INTER_LINEAR)
        diff=np.max(np.abs(original[:,:,:3].astype(float)-before),axis=2)
        # Ground lies below the door threshold in the room atlas. Restriction
        # excludes Ben and the rotating door, even when their dark colors match.
        ground=(my>1325)&(mx>185)&(mx<1640)&(my<1643)&(original[:,:,3]>0)
        protected=cv2.dilate((ground&(diff>24)).astype('uint8'),np.ones((5,5),np.uint8))
        editable=ground&(protected==0)
        weight=np.minimum(cv2.distanceTransform(editable.astype('uint8'),cv2.DIST_L2,5)/6,1)[:,:,None]
        target=original.copy();target[:,:,:3]=np.rint(after*weight+original[:,:,:3]*(1-weight)).astype('uint8')
        pack(source,folder,target,editable,registration_inliers=int(ok.sum()),reference_shift=shift.tolist(),scope='open-door ground only; character and door protected')
    # The final turning frame has only a tiny isolated ground sliver. It has
    # too few reliable SIFT points; use its alpha-masked template instead.
    source=ROOT/'original/costumes/103-pick-lock-cos/pick-lock-cos_akostume_pk_a10.dxt'
    original=read_dxt(source)[2];x,y,w,h=1,1261,236,57
    mask=(original[y:y+h,x:x+w,3]>250).astype('uint8')*255
    score=cv2.matchTemplate(reference[1325:1645,:,:3],original[y:y+h,x:x+w,:3],cv2.TM_SQDIFF_NORMED,mask=mask)
    score[~np.isfinite(score)]=1e6;error,_,loc,_=cv2.minMaxLoc(score)
    assert error<.003
    sx,sy=loc[0],loc[1]+1325
    target=original.copy();target[y:y+h,x:x+w,:3]=new_reference[sy:sy+h,sx:sx+w,:3]
    editable=np.zeros(original.shape[:2],bool);editable[y:y+h,x:x+w]=True
    pack(source,folder,target,editable,template_error=error,scope='isolated final-turn ground sliver; all characters and door protected')


def junkgate():
    room='027-junkgate';folder=ROOT/'locations'/room/'custom-v1'
    source=ROOT/f'original/rooms/{room}/{room}_room_pk_a00.dxt'
    original=read_dxt(source)[2]
    scene=np.array(Image.open(folder/'in-game-texture-preview.png').convert('RGB'))
    im=np.array(Image.open(ROOT/'edited/junkgate-cord-removed-v2.png').convert('RGB'))
    # The generated file has white side margins; remove those only.
    columns=np.where((im.min(axis=2)<220).mean(axis=0)>.9)[0]
    im=cv2.resize(im[:,columns[0]:columns[-1]+1],(260,840),interpolation=cv2.INTER_LANCZOS4)
    mask=np.zeros((840,260),np.uint8)
    points=np.array([[148,72],[152,270],[154,500],[152,700],[145,730],[133,750]],np.int32)
    cv2.polylines(mask,[points],False,255,22)
    weight=cv2.GaussianBlur(mask.astype('float32')/255,(0,0),2)[:,:,None]
    crop=scene[100:940,1320:1580].copy()
    crop=np.rint(im*weight+crop*(1-weight)).astype('uint8')
    scene[100:940,1320:1580]=crop
    ys,xs=slice(1,1549),slice(1257,1513)
    replacement=cv2.resize(scene[120:894,1390:1518],(256,1548),interpolation=cv2.INTER_LINEAR)
    target=original.copy();target[ys,xs,:3]=replacement
    editable=np.zeros(original.shape[:2],bool);editable[ys,xs]=True
    decoded=pack(source,folder,target,editable,scope='entire cord-removed wall patch; no old smooth wall retained')
    preview=Image.open(folder/'in-game-texture-preview.png').convert('RGBA')
    preview.alpha_composite(Image.fromarray(decoded[ys,xs]).resize((128,774),Image.Resampling.LANCZOS),(1390,120))
    preview.convert('RGB').save(folder/'cord-removed-v2-preview.png')


if __name__=='__main__':
    generated_atlas('018-mo-shack',0,'shack-atlas-0-v2.png',True)
    generated_atlas('018-mo-shack',1,'shack-atlas-1-v2.png',True)
    gate=generated_atlas('026-gas-gate',0,'gate-open-atlas-v2.png',False)
    lock_floor(gate)
    junkgate()
