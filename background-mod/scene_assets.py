"""Decode and render the game's CHNK geometry and compressed texture payloads."""
from pathlib import Path
import struct
import zlib
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ROOM = ROOT / 'original/rooms/010-dumpster'
SIZE = (2220, 1200)

def read_dxt(path):
    """Decode a standalone room-object texture, using the same payload as CHNK."""
    data=Path(path).read_bytes()
    fmt,w,h=struct.unpack_from('<4sII',data)
    assert fmt in (b'DXT1',b'DXT5')
    raw=zlib.decompress(data[12:],-15)
    im=Image.frombytes('RGBA',(w,h),raw,'bcn',(1 if fmt==b'DXT1' else 3,fmt.decode()))
    return data,raw,np.array(im)

def read_chunk(path):
    data = Path(path).read_bytes()
    nv, = struct.unpack_from('<I', data)
    vertices = np.frombuffer(data, '<f4', count=nv * 4, offset=4).reshape(-1, 4).copy()
    pos = 4 + nv * 16
    ni, = struct.unpack_from('<H', data, pos); pos += 2
    indices = np.frombuffer(data, '<u2', count=ni, offset=pos).copy(); pos += ni * 2
    nt, = struct.unpack_from('<H', data, pos); pos += 2
    groups = [struct.unpack_from('<HH', data, pos + i * 4) for i in range(nt)]
    pos = (pos + nt * 4 + 3) & ~3
    header = data[:pos]
    textures = []
    for first, count in groups:
        length, = struct.unpack_from('<I', data, pos); pos += 4
        payload = data[pos:pos + length]
        fmt, w, h = struct.unpack_from('<4sII', payload)
        raw = zlib.decompress(payload[12:], -15)
        image = Image.frombytes('RGBA', (w, h), raw, 'bcn', (1 if fmt == b'DXT1' else 3, fmt.decode()))
        textures.append(dict(first=first, count=count, format=fmt, image=image, raw=raw, payload=payload))
        pos = (pos + length + 3) & ~3
    assert pos == len(data)
    return dict(path=Path(path), vertices=vertices, indices=indices, textures=textures, header=header)

def triangle_pixels(points, width, height):
    low = np.maximum(np.floor(points.min(axis=0)).astype(int), 0)
    high = np.minimum(np.ceil(points.max(axis=0)).astype(int), (width, height))
    if np.any(high <= low): return None
    xx, yy = np.meshgrid(np.arange(low[0], high[0]) + .5, np.arange(low[1], high[1]) + .5)
    a, b, c = points
    den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(den) < 1e-9: return None
    u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1])) / den
    v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1])) / den
    weights = np.stack([u, v, 1-u-v], axis=-1)
    mask = np.all(weights >= -1e-5, axis=-1)
    return low, high, weights, mask

def render(chunk, size=SIZE):
    result = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    for tex in chunk['textures']:
        source = np.array(tex['image'])
        h, w = source.shape[:2]
        for inds in chunk['indices'][tex['first']:tex['first']+tex['count']].reshape(-1, 3):
            verts = chunk['vertices'][inds]
            raster = triangle_pixels(verts[:, :2] / 2, *size)
            if raster is None: continue
            lo, hi, weights, mask = raster
            uv = weights @ verts[:, 2:]
            tx = np.clip((uv[:,:,0] * w).astype(int), 0, w-1)
            ty = np.clip((uv[:,:,1] * h).astype(int), 0, h-1)
            target = result[lo[1]:hi[1], lo[0]:hi[0]]
            target[mask] = source[ty[mask], tx[mask]]
    return Image.fromarray(result)

def render_scene():
    out = ROOT / 'scene'; out.mkdir(exist_ok=True)
    scene = Image.new('RGBA', SIZE)
    for layer in (10,20,30,40):
        chunk = read_chunk(ROOM / f'010-dumpster-layer{layer}.chnk')
        im = render(chunk)
        im.save(out / f'layer{layer}.png')
        scene = Image.alpha_composite(scene, im)
    scene.convert('RGB').save(out / 'official-remaster.png')
    print(out / 'official-remaster.png')

if __name__ == '__main__':
    render_scene()
