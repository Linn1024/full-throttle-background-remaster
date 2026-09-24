"""Install or restore the four-layer custom dumpster background."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from patch_background import ensure_closed, restore as restore_test

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parent / 'full.data'
STATE = ROOT / 'custom-installed.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def apply():
    ensure_closed()
    if STATE.exists():
        raise SystemExit('Custom background already installed. Restore before applying a different version.')
    entries = json.loads((ROOT / 'manifest.json').read_text())
    entries = [e for e in entries if Path(e['name']).name in
               [f'010-dumpster-layer{n}.chnk' for n in (10,20,30,40)]]
    assert len(entries) == 4
    replacements = [(e, (ROOT / 'custom-v1' / Path(e['name']).name).read_bytes()) for e in entries]
    if (ROOT / 'installed-patch.json').exists():
        restore_test()
    with ARCHIVE.open('r+b') as f:
        header = f.read(48)
        assert header[:4] == b'KAPL'
        data_start, = struct.unpack_from('<I',header,20)
        f.seek(0,2); old_length = f.tell()
        assert struct.unpack_from('<Q',header,40)[0] == old_length-data_start
        tail = b''
        records = []
        for e, payload in replacements:
            f.seek(e['entry_offset']); record = f.read(24)
            offset, namepos, size, size2, flags = struct.unpack('<Q4I',record)
            assert offset+data_start == e['offset'] and size == e['size'] and size2 == size and flags == 0
            f.seek(e['offset'])
            assert f.read(size) == (ROOT / 'original' / e['name']).read_bytes(), 'Original asset changed'
            new = struct.pack('<Q4I',old_length+len(tail)-data_start,namepos,len(payload),len(payload),flags)
            records.append(dict(name=e['name'], entry_offset=e['entry_offset'],
                                original=record.hex(), replacement=new.hex(), sha256=sha(payload)))
            tail += payload
        new_header = header[:40] + struct.pack('<Q',old_length+len(tail)-data_start)
        state = dict(version='custom-v1', old_length=old_length, original_header=header.hex(),
                     replacement_header=new_header.hex(), tail_sha256=sha(tail), records=records)
        STATE.write_text(json.dumps(state,indent=2))
        try:
            f.seek(old_length); f.write(tail); f.flush()
            for r in records:
                f.seek(r['entry_offset']); f.write(bytes.fromhex(r['replacement']))
            f.seek(0); f.write(new_header); f.flush()
            f.seek(old_length); assert sha(f.read()) == state['tail_sha256']
            for r in records:
                f.seek(r['entry_offset']); assert f.read(24) == bytes.fromhex(r['replacement'])
        except BaseException:
            for r in records:
                f.seek(r['entry_offset']); f.write(bytes.fromhex(r['original']))
            f.seek(0); f.write(header); f.truncate(old_length)
            STATE.replace(ROOT / 'failed-custom-install.json')
            raise
    print('Installed custom dumpster background v1; verified all four archive entries and payloads.')

def restore():
    ensure_closed()
    if not STATE.exists():
        if (ROOT / 'installed-patch.json').exists():
            restore_test()
            return
        raise SystemExit('No background patch is installed.')
    state = json.loads(STATE.read_text())
    with ARCHIVE.open('r+b') as f:
        assert f.read(48) == bytes.fromhex(state['replacement_header']), 'Archive header changed'
        f.seek(state['old_length']); assert sha(f.read()) == state['tail_sha256'], 'Archive tail changed'
        for r in state['records']:
            f.seek(r['entry_offset']); assert f.read(24) == bytes.fromhex(r['replacement']), 'Asset record changed'
        for r in state['records']:
            f.seek(r['entry_offset']); f.write(bytes.fromhex(r['original']))
        f.seek(0); f.write(bytes.fromhex(state['original_header'])); f.truncate(state['old_length'])
    STATE.replace(ROOT / 'last-restored-custom.json')
    print('Restored the official remastered background.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['apply','restore'])
    args = parser.parse_args()
    apply() if args.command == 'apply' else restore()
