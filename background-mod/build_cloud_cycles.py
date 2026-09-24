"""Reconstruct classic CYCL lighting on custom cloud art as sparse DXT tracks.

No room geometry, alpha, archive, or executable modifications. Classic palette
indices supply phase/direction; custom cloud silhouettes restrict the effect.
Timing follows SCUMM's 16384/rate delay in 60 Hz ticks. This recreates the visual
effect; it does not hook the game's script-controlled palette clock.
"""
import hashlib
import json
import struct
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from scene_assets import ROOT, read_chunk, triangle_pixels, render
from texture_gutters import scene_maps

ROOMS=['031-reststop','032-mensroom','033-ambush','034-scope','037-benupsht','038-ripupsht','051-corville']
OUT=ROOT/'reviews/cloud-cycles-v11'
GAIN=2.5
BLUR=2.0
RECIPE=f'strongest-block-gain-{GAIN}-blur-{BLUR}'

def classic_cycles(number):
    data=(ROOT/'classic/ft.la1').read_bytes()
    assert data[8:12]==b'LOFF'
    offsets=dict(struct.unpack_from('<BI',data,17+i*5) for i in range(data[16]))
    pos=offsets[number];assert data[pos:pos+4]==b'ROOM'
    end=pos+int.from_bytes(data[pos+4:pos+8],'big');pos+=8
    while pos<end:
        size=int.from_bytes(data[pos+4:pos+8],'big')
        if data[pos:pos+4]==b'CYCL':break
        pos+=size
    else:raise ValueError('Missing CYCL')
    raw=data[pos+8:pos+size];pos=0;cycles=[]
    while raw[pos]:
        c=raw[pos:pos+9];rate=int.from_bytes(c[3:5],'big')
        cycles.append(dict(id=c[0],step_ms=(16384//rate)*1000/60,
                           reverse=bool(int.from_bytes(c[5:7],'big')&2),start=c[7],end=c[8]))
        pos+=9
    return cycles

def descriptor(path):
    data=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),size=len(data))

def build(rooms=None):
    OUT.mkdir(exist_ok=True,parents=True);entries=[]
    previous={e['name']:e for e in json.loads((OUT/'manifest.json').read_text())} if (OUT/'manifest.json').exists() else {}
    if rooms is not None:entries=[e for e in previous.values() if e['name'].split('/')[0] not in rooms]
    for room in (ROOMS if rooms is None else rooms):
        folder=ROOT/'locations'/room;cfg=json.loads((folder/'room.json').read_text())
        size=tuple(cfg['size']);n=int(room[:3]);cycles=classic_cycles(n)
        # Corville's fourth range is electrical lighting, not the requested clouds.
        recipe=RECIPE if n!=51 else 'corville-v24-gutters-normalized-luminance-blur12'
        if n==51:cycles=cycles[:3]
        indexed=Image.open(ROOT/f'classic/ft/IMAGES/backgrounds/LECF_0001_LFLF_{n:04d}_ROOM_RMIM_IM00.png')
        indices=np.array(indexed);palette=np.array(indexed.getpalette(),dtype=np.float32).reshape(-1,3)
        art=np.array(Image.open(folder/'custom-v1/in-game-texture-preview.png').convert('RGB'))
        # Dilated original sky regions allow the remastered outlines to differ.
        union=np.zeros(indices.shape,np.uint8)
        for c in cycles:union[(indices>=c['start'])&(indices<=c['end'])]=1
        sky=cv2.resize(cv2.dilate(union,np.ones((7,7),np.uint8)),size,interpolation=cv2.INTER_NEAREST)>0
        if n!=51:
            rgb=art.astype(float)
            sky &= (rgb[:,:,0]>rgb[:,:,1]*1.65)&(rgb[:,:,0]>rgb[:,:,2]*1.9)&(rgb[:,:,0]>18)
        else:
            # Keep buildings, road, and poles fixed; source palette sky is inset.
            sky=cv2.resize(cv2.dilate(union,np.ones((7,7),np.uint8)),size,interpolation=cv2.INTER_NEAREST)>0
        if n==51:
            # Require painted cloud color as well as original sky ownership.
            rgb=art.astype(float)
            sky &= (rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,0]>rgb[:,:,2]*1.25)&(rgb[:,:,0]>20)
        for x0,y0,x1,y1 in cfg.get('protected',[]):sky[y0:y1,x0:x1]=False
        fade=np.minimum(cv2.distanceTransform(sky.astype('uint8'),cv2.DIST_L2,5)/8,1)
        # The source field is smoothly sampled, retaining the new brushwork.
        fields=[]
        for c in cycles:
            active=(indices>=c['start'])&(indices<=c['end'])
            frames=[]
            for step in range(c['end']-c['start']+1):
                mapped=c['start']+(indices.astype(int)-c['start']+(step if c['reverse'] else -step))%(c['end']-c['start']+1)
                delta=(palette[mapped]-palette[indices])*active[:,:,None]
                delta=cv2.resize(delta,size,interpolation=cv2.INTER_LINEAR)
                if n==51:
                    # Modulate custom shading instead of adding amplified RGB.
                    # This keeps highlights and dark folds coherent at every phase.
                    lum=np.array([.2126,.7152,.0722],np.float32)
                    base_lum=cv2.resize(palette[indices]@lum,size,interpolation=cv2.INTER_LINEAR)
                    coverage=cv2.GaussianBlur(cv2.resize(active.astype('float32'),size),(0,0),12)
                    change=cv2.GaussianBlur(delta@lum,(0,0),12)/np.maximum(coverage,.05)
                    ratio=np.clip(2*change/np.maximum(base_lum,12),-.50,.80)
                    delta=art.astype('float32')*ratio[:,:,None]*fade[:,:,None]/GAIN
                else:
                    delta=cv2.GaussianBlur(delta,(0,0),BLUR)*fade[:,:,None]
                frames.append(delta)
            fields.append(frames)
        peaks=[np.maximum.reduce([np.max(np.abs(d),axis=2) for d in frames]) for frames in fields]
        # Only the opaque base layer contains these clouds.
        path=folder/'custom-v1'/cfg['layers'][0];chunk=read_chunk(path)
        previews={step:[] for step in (0,3,6,9)}
        for ti,tex in enumerate(chunk['textures']):
            assert tex['format'] in (b'DXT1',b'DXT5')
            stride=8 if tex['format']==b'DXT1' else 16
            color_offset=0 if stride==8 else 8
            base=np.array(tex['image']);h,w=base.shape[:2]
            mx=np.full((h,w),-1,np.float32);my=mx.copy()
            for ids in chunk['indices'][tex['first']:tex['first']+tex['count']].reshape(-1,3):
                v=chunk['vertices'][ids];r=triangle_pixels(v[:,2:]*(w,h),w,h)
                if r is None:continue
                lo,hi,weights,inside=r;xy=(weights@v[:,:2])/2
                mx[lo[1]:hi[1],lo[0]:hi[0]][inside]=xy[:,:,0][inside]
                my[lo[1]:hi[1],lo[0]:hi[0]][inside]=xy[:,:,1][inside]
            if n==51:
                mx,my,_=scene_maps(chunk,tex)
            tracks=[];owned=np.zeros((h//4,w//4),bool)
            # The former first-track-wins rule could assign a block to a faint
            # blurred fringe and discard a much stronger overlapping cycle.
            scores=[cv2.remap(p,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
                    .reshape(h//4,4,w//4,4).mean(axis=(1,3)) for p in peaks]
            owners=np.argmax(scores,axis=0)
            sky_pixels=cv2.remap(fade,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)>0
            safe_blocks=sky_pixels.reshape(h//4,4,w//4,4).all(axis=(1,3))
            preview_raw={s:bytearray(tex['raw']) for s in previews}
            for ci,(c,frames) in enumerate(zip(cycles,fields)):
                changes=[cv2.remap(d,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT) for d in frames]
                strength=np.max([np.max(np.abs(d),axis=2) for d in changes],axis=0)
                eligible=(strength>1)&(base[:,:,3]==255)&(mx>=0)
                # Animate fully opaque blocks only. BC3 runs copy color bytes
                # separately, leaving every original alpha block untouched.
                opaque=(base[:,:,3]==255).reshape(h//4,4,w//4,4).all(axis=(1,3))
                blocks=eligible.reshape(h//4,4,w//4,4).any(axis=(1,3))&opaque&safe_blocks&(owners==ci)
                assert not (blocks&owned).any()
                if not blocks.any():continue
                owned|=blocks;block_ids=np.flatnonzero(blocks.ravel())
                # Store adjacent blocks as runs; shared BC1 blocks have one owner.
                runs=[]
                for b in block_ids:
                    offset=int(b)*stride+color_offset
                    if runs and runs[-1][0]+runs[-1][1]==offset:runs[-1][1]+=8
                    else:runs.append([offset,8])
                payloads=[]
                key=f'{room}/{path.stem}/texture{ti}'
                old=previous.get(key,{})
                oldtrack=next((t for t in old.get('tracks',[]) if t['id']==c['id']),None)
                oldblocks=set()
                if oldtrack and old.get('recipe')==recipe and old.get('base_sha256')==hashlib.sha256(tex['raw']).hexdigest():
                    for at,length in oldtrack['runs']:oldblocks.update(range(at,at+length,8))
                reuse=oldtrack is not None and set(int(b)*stride+color_offset for b in block_ids).issubset(oldblocks)
                for step,delta in enumerate(changes):
                    if step==0:encoded=tex['raw']
                    elif reuse:
                        saved=oldtrack['frames'][step];patch=Path(saved['path']).read_bytes()
                        assert hashlib.sha256(patch).hexdigest()==saved['sha256']
                        encoded=bytearray(tex['raw']);cursor=0
                        for at,length in oldtrack['runs']:
                            encoded[at:at+length]=patch[cursor:cursor+length];cursor+=length
                    else:
                        target=base.copy();target[:,:,:3]=np.clip(np.rint(base[:,:,:3].astype(float)+delta*GAIN),0,255).astype('uint8')
                        png=OUT/'encode.png';Image.fromarray(target).save(png)
                        fmt='BC1_UNORM' if stride==8 else 'BC3_UNORM'
                        subprocess.run([str(ROOT/'tools/texconv.exe'),'-f',fmt,'-m','1','-y','-o',str(OUT),str(png)],check=True,capture_output=True)
                        encoded=png.with_suffix('.dds').read_bytes()[128:];assert len(encoded)==len(tex['raw'])
                    data=b''.join(encoded[at:at+length] for at,length in runs)
                    dest=OUT/f'{room}-t{ti}-c{ci}-f{step}.bin';dest.write_bytes(data);payloads.append(descriptor(dest))
                    for s in previews:
                        if s%len(changes)==step:
                            for at,length in runs:preview_raw[s][at:at+length]=encoded[at:at+length]
                tracks.append(dict(**c,runs=runs,frames=payloads))
            for s in previews:
                im=Image.frombytes('RGBA',(w,h),bytes(preview_raw[s]),'bcn',(1 if stride==8 else 3,tex['format'].decode()))
                assert np.array_equal(np.array(im)[:,:,3],base[:,:,3])
                previews[s].append({**tex,'image':im})
            if tracks:
                entries.append(dict(name=f'{room}/{path.stem}/texture{ti}',recipe=recipe,base_sha256=hashlib.sha256(tex['raw']).hexdigest(),tracks=tracks))
            print(room,ti,'tracks',len(tracks),flush=True)
        animation=[]
        for s,textures in previews.items():
            im=render({**chunk,'textures':textures},size)
            for extra in cfg['layers'][1:]:
                im=Image.alpha_composite(im,render(read_chunk(folder/'custom-v1'/extra),size))
            im=im.convert('RGB');im.thumbnail((960,520));animation.append(im)
        animation[0].save(OUT/(room+'-preview.gif'),save_all=True,append_images=animation[1:]+animation[-2:0:-1],duration=500,loop=0)
    (OUT/'manifest.json').write_text(json.dumps(entries,indent=2)+'\n')

if __name__=='__main__':build()
