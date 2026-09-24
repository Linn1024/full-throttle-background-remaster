"""Reversible, single-entry Full Throttle Remastered background test."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parent / 'full.data'
NAME = 'rooms/010-dumpster/010-dumpster-layer10.chnk'
STATE = ROOT / 'installed-patch.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build():
    original = (ROOT / 'original' / NAME).read_bytes()
    start = 161376
    decoder = zlib.decompressobj(-15)
    raw = bytearray(decoder.decompress(original[start + 12:]))
    end = len(original) - len(decoder.unused_data)
    dds = (ROOT / 'edited/mod-test.dds').read_bytes()
    assert dds[:4] == b'DDS ' and dds[84:88] == b'DXT1'
    assert struct.unpack_from('<II', dds, 12) == (1024, 1024)
    replacement = dds[128:]
    assert len(replacement) == len(raw) == 524288
    # Copy only BC1 blocks containing the wall marking. Every other block stays exact.
    for y in range(32 // 4, 232 // 4):
        a = (y * 256 + 220 // 4) * 8
        b = (y * 256 + 436 // 4) * 8
        raw[a:b] = replacement[a:b]
    encoder = zlib.compressobj(9, zlib.DEFLATED, -15)
    texture = original[start:start + 12] + encoder.compress(raw) + encoder.flush()
    next_start = (end + 3) & ~3
    patched = (original[:start - 4] + struct.pack('<I', len(texture)) + texture
               + b'\0' * (-(start + len(texture)) % 4) + original[next_start:])
    # Validate all three embedded textures after rebuilding alignment and lengths.
    pos = 476
    for _ in range(3):
        size, = struct.unpack_from('<I', patched, pos)
        payload = patched[pos + 4:pos + 4 + size]
        assert payload[:4] == b'DXT1'
        assert len(zlib.decompress(payload[12:], -15)) == 524288
        pos = (pos + 4 + size + 3) & ~3
    assert pos == len(patched)
    (ROOT / 'edited/010-dumpster-layer10.chnk').write_bytes(patched)
    return original, patched

def ensure_closed():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Throttle.exe', '/NH'],
                            capture_output=True, text=True, check=True)
    if 'throttle.exe' in result.stdout.lower():
        raise SystemExit('Close Full Throttle before applying or restoring the patch.')

def apply():
    ensure_closed()
    if STATE.exists():
        raise SystemExit('Patch is already installed; restore it first.')
    original, patched = build()
    entry = next(e for e in json.loads((ROOT / 'manifest.json').read_text()) if e['name'] == NAME)
    with ARCHIVE.open('r+b') as f:
        header = f.read(48)
        assert header[:4] == b'KAPL'
        data_start, = struct.unpack_from('<I', header, 20)
        f.seek(entry['entry_offset']); record = f.read(24)
        offset, namepos, size, size2, flags = struct.unpack('<Q4I', record)
        assert offset + data_start == entry['offset'] and size == len(original) and size == size2 and flags == 0
        f.seek(entry['offset']); assert f.read(size) == original, 'Original asset has changed'
        f.seek(0, 2); old_length = f.tell()
        assert struct.unpack_from('<Q', header, 40)[0] == old_length - data_start
        new_record = struct.pack('<Q4I', old_length - data_start, namepos, len(patched), len(patched), flags)
        new_header = header[:40] + struct.pack('<Q', old_length + len(patched) - data_start)
        state = dict(old_length=old_length, header=header.hex(), record=record.hex(),
                     new_header=new_header.hex(), new_record=new_record.hex(),
                     entry_offset=entry['entry_offset'], patch_size=len(patched), patch_sha256=digest(patched))
        STATE.write_text(json.dumps(state, indent=2))
        f.write(patched); f.flush()
        f.seek(entry['entry_offset']); f.write(new_record)
        f.seek(0); f.write(new_header); f.flush()
        f.seek(old_length); assert digest(f.read()) == state['patch_sha256']
        f.seek(entry['entry_offset']); assert f.read(24) == new_record
    print('Installed and verified. Restart the game and load the opening dumpster scene in remastered mode.')

def restore():
    ensure_closed()
    state = json.loads(STATE.read_text())
    with ARCHIVE.open('r+b') as f:
        assert f.read(48) == bytes.fromhex(state['new_header']), 'Archive header changed; refusing automatic restore'
        f.seek(state['entry_offset']); assert f.read(24) == bytes.fromhex(state['new_record'])
        f.seek(state['old_length']); assert digest(f.read()) == state['patch_sha256'], 'Archive changed'
        f.seek(state['entry_offset']); f.write(bytes.fromhex(state['record']))
        f.seek(0); f.write(bytes.fromhex(state['header']))
        f.truncate(state['old_length'])
    STATE.replace(ROOT / 'last-restored-patch.json')
    print('Original archive restored.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'apply', 'restore'])
    command = parser.parse_args().command
    if command == 'build':
        original, patched = build()
        print(f'Built and validated: {len(original)} -> {len(patched)} bytes')
    elif command == 'apply':
        apply()
    else:
        restore()
