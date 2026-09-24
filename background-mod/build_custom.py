"""Map the generated scene onto existing game UVs; retain masks and lettering."""
from pathlib import Path
import json
import struct
import subprocess
import zlib
import numpy as np
from PIL import Image, ImageDraw
from scene_assets import ROOT, ROOM, SIZE, read_chunk, render, triangle_pixels

OUT = ROOT / 'custom-v1'
TEXCONV = ROOT / 'tools/texconv.exe'
# Scene-space rectangles enclosing the complete official sign and dumpster label.
PROTECTED = [(1730, 214, 2080, 442), (390, 378, 490, 520)]

def build(location=None):
    artwork_crop = None
    protected_polygons = []
    if location is None:
        out, room, size = OUT, ROOM, SIZE
        artwork = ROOT / 'scene/custom-remaster-v1.png'
        protected_rects = PROTECTED
        paths = [room / f'010-dumpster-layer{n}.chnk' for n in (10,20,30,40)]
    else:
        folder = ROOT / 'locations' / location
        config = json.loads((folder / 'room.json').read_text())
        room, size = ROOT / 'original/rooms' / location, tuple(config['size'])
        out, artwork = folder / 'custom-v1', folder / 'custom-remaster-v1.png'
        protected_rects = config['protected']
        protected_polygons = config.get('protected_polygons', [])
        artwork_crop = config.get('artwork_crop')
        paths = [room / name for name in config['layers']]
    out.mkdir(exist_ok=True)
    polygon_image = Image.new('L', size)
    draw = ImageDraw.Draw(polygon_image)
    for polygon in protected_polygons:
        draw.polygon([tuple(p) for p in polygon], fill=255)
    polygon_mask = np.array(polygon_image) > 0
    art = np.array(Image.open(artwork).convert('RGB'))
    if artwork_crop is not None:
        x0,y0,x1,y1 = artwork_crop
        assert 0 <= x0 < x1 <= art.shape[1] and 0 <= y0 < y1 <= art.shape[0]
        # Source sampling window, before mapping onto unchanged room geometry.
        # Generated panoramas can include extra margins outside the room view.
        art = art[y0:y1,x0:x1]
    ah, aw = art.shape[:2]
    layers = [read_chunk(p) for p in paths]
    alpha = [np.array(render(c,size))[:,:,3] for c in layers]
    summary = []
    for layer_index, chunk in enumerate(layers):
        blocks = []
        for ti, tex in enumerate(chunk['textures']):
            original = np.array(tex['image'])
            target = original.copy()
            th, tw = original.shape[:2]
            editable = np.zeros((th, tw), dtype=bool)
            protected = np.zeros((th, tw), dtype=bool)
            for inds in chunk['indices'][tex['first']:tex['first']+tex['count']].reshape(-1,3):
                verts = chunk['vertices'][inds]
                raster = triangle_pixels(verts[:,2:] * (tw,th), tw, th)
                if raster is None: continue
                lo, hi, weights, inside = raster
                xy = (weights @ verts[:,:2]) / 2
                sx, sy = xy[:,:,0], xy[:,:,1]
                cx = np.clip(sx.astype(int), 0, size[0]-1)
                cy = np.clip(sy.astype(int), 0, size[1]-1)
                visible = inside.copy()
                for front in alpha[layer_index+1:]:
                    visible &= front[cy,cx] < 128
                tx = np.clip((sx * aw / size[0]).astype(int), 0, aw-1)
                ty = np.clip((sy * ah / size[1]).astype(int), 0, ah-1)
                region = target[lo[1]:hi[1],lo[0]:hi[0]]
                # Preserve lettering exactly, with a short transition outside the
                # protected region so its rectangular boundary cannot form a seam.
                amount = np.ones(inside.shape, dtype=np.float32)
                amount[polygon_mask[cy,cx]] = 0
                for x0,y0,x1,y1 in protected_rects:
                    dx=np.maximum(np.maximum(x0-sx,sx-x1),0)
                    dy=np.maximum(np.maximum(y0-sy,sy-y1),0)
                    amount=np.minimum(amount,np.clip(np.hypot(dx,dy)/40,0,1))
                weight=amount[visible,None]
                region[visible,:3] = np.rint(art[ty[visible],tx[visible]]*weight
                    + original[lo[1]:hi[1],lo[0]:hi[0]][visible,:3]*(1-weight)).astype(np.uint8)
                editable[lo[1]:hi[1],lo[0]:hi[0]] |= visible
                keep = polygon_mask[cy,cx].copy()
                for x0,y0,x1,y1 in protected_rects:
                    keep |= (sx >= x0) & (sx <= x1) & (sy >= y0) & (sy <= y1)
                protected[lo[1]:hi[1],lo[0]:hi[0]] |= keep & inside
            stem = chunk['path'].stem + f'-texture{ti}'
            png = out / f'{stem}.png'
            Image.fromarray(target).save(png)
            fmt = 'BC1_UNORM' if tex['format'] == b'DXT1' else 'BC3_UNORM'
            subprocess.run([str(TEXCONV), '-f',fmt,'-m','1','-y','-o',str(out),str(png)],
                           check=True, capture_output=True)
            dds = (out / f'{stem}.dds').read_bytes()
            assert dds[:4] == b'DDS ' and dds[84:88] == tex['format']
            stride = 8 if tex['format'] == b'DXT1' else 16
            encoded = bytearray(dds[128:])
            assert len(encoded) == len(tex['raw'])
            changes = 0
            for by in range(th//4):
                for bx in range(tw//4):
                    at = (by*(tw//4)+bx)*stride
                    ys, xs = slice(by*4,by*4+4), slice(bx*4,bx*4+4)
                    if protected[ys,xs].any() or not editable[ys,xs].any():
                        encoded[at:at+stride] = tex['raw'][at:at+stride]
                    else:
                        changes += 1
                        if stride == 16:
                            # Exact original BC3 alpha, including every edge/mask pixel.
                            encoded[at:at+8] = tex['raw'][at:at+8]
            if stride == 16:
                assert all(encoded[i:i+8] == tex['raw'][i:i+8] for i in range(0,len(encoded),16))
            compressor = zlib.compressobj(9,zlib.DEFLATED,-15)
            payload = tex['payload'][:12] + compressor.compress(encoded) + compressor.flush()
            blocks.append(struct.pack('<I',len(payload)) + payload + b'\0'*(-len(payload)%4))
            summary.append(dict(texture=stem, changed_blocks=changes, alpha_preserved=True,
                                protected_text_blocks_preserved=True))
        packed = chunk['header'] + b''.join(blocks)
        dest = out / chunk['path'].name
        dest.write_bytes(packed)
        decoded = read_chunk(dest)
        assert decoded['header'] == chunk['header']
        for before,after in zip(chunk['textures'],decoded['textures']):
            assert np.array_equal(np.array(before['image'])[:,:,3],np.array(after['image'])[:,:,3])
        print(dest.name,len(packed))
    scene = Image.new('RGBA',size)
    reference = Image.new('RGBA',size)
    for path in paths:
        scene = Image.alpha_composite(scene,render(read_chunk(out / path.name),size))
        reference = Image.alpha_composite(reference,render(read_chunk(path),size))
    scene.convert('RGB').save(out / 'in-game-texture-preview.png')
    before, after = np.array(reference), np.array(scene)
    for x0,y0,x1,y1 in protected_rects:
        assert np.array_equal(before[y0:y1,x0:x1],after[y0:y1,x0:x1]), 'Protected lettering changed'
    assert np.array_equal(before[polygon_mask],after[polygon_mask]), 'Protected silhouette changed'
    (out / 'validation.json').write_text(json.dumps(dict(textures=summary,
        protected_regions=protected_rects,protected_polygons=protected_polygons,
        protected_pixels_identical=True),indent=2))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--room')
    build(parser.parse_args().room)
