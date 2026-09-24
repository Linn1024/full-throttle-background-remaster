"""Launch Full Throttle with F6/F7 live background switching."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import frida
from scene_assets import ROOT, ROOM, read_chunk, read_dxt

LIVE = ROOT / 'live-switcher'

def prepare():
    LIVE.mkdir(exist_ok=True)
    textures=[]
    assets=[(ROOM/f'010-dumpster-layer{layer}.chnk',ROOT/'custom-v1'/f'010-dumpster-layer{layer}.chnk')
            for layer in (10,20,30,40)]
    rooms=['010-dumpster']
    for folder in sorted((ROOT/'locations').glob('*')):
        if not (folder/'custom-v1/validation.json').exists():continue
        cfg=json.loads((folder/'room.json').read_text())
        report=json.loads((folder/'custom-v1/validation.json').read_text())
        assert report['protected_pixels_identical']
        rooms.append(cfg['room'])
        for name in cfg['layers']:
            assets.append((ROOT/'original/rooms'/cfg['room']/name,folder/'custom-v1'/name))
    for report_path in sorted((ROOT/'locations').glob('*/custom-v1/extra-chunk-validation.json')):
        folder=report_path.parent
        for report in json.loads(report_path.read_text()):
            assert all(t['alpha_preserved'] and t['protected_foreground_identical'] for t in report['textures'])
            assets.append((ROOT/'original/rooms'/folder.parent.name/report['file'],folder/report['file']))
    for original_path,custom_path in assets:
        name=original_path.name
        chunks={'official':read_chunk(original_path),'custom':read_chunk(custom_path)}
        assert chunks['official']['header']==chunks['custom']['header']
        assert len(chunks['official']['textures'])==len(chunks['custom']['textures'])
        for i,tex in enumerate(chunks['official']['textures']):
            item=dict(name=f'{original_path.parent.name}/{original_path.stem}/texture{i}',
                      width=tex['image'].width,height=tex['image'].height,size=len(tex['raw']))
            for mode in ('official','custom'):
                raw=chunks[mode]['textures'][i]['raw']
                assert len(raw)==item['size']
                path=LIVE/f'{original_path.stem}-{i}-{mode}.bin';path.write_bytes(raw)
                item[mode]=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),
                               fingerprint=':'.join(hashlib.sha256(raw[o:o+32]).hexdigest()
                               for o in (0,len(raw)//2,len(raw)-32)))
            textures.append(item)
    # Room object atlases can contain opaque scenery behind animated objects.
    # Include only explicitly built and validated replacements.
    for report_path in sorted((ROOT/'locations').glob('*/custom-v1/overlay-validation.json')):
        folder=report_path.parent
        room=folder.parent.name
        for report in json.loads(report_path.read_text()):
            assert report['alpha_preserved']
            name=report['file']
            original_path=ROOT/'original'/report.get('source',f'rooms/{room}/{name}')
            custom_path=folder/name
            before,raw,im=read_dxt(original_path)
            after,newraw,newim=read_dxt(custom_path)
            assert before[:12]==after[:12] and len(raw)==len(newraw)
            assert (im[:,:,3]==newim[:,:,3]).all()
            item=dict(name=f'{room}/{original_path.stem}',width=im.shape[1],
                      height=im.shape[0],size=len(raw))
            for mode,content in [('official',raw),('custom',newraw)]:
                path=LIVE/f'{original_path.stem}-{mode}.bin'
                path.write_bytes(content)
                item[mode]=dict(path=str(path),sha256=hashlib.sha256(content).hexdigest(),
                               fingerprint=':'.join(hashlib.sha256(content[o:o+32]).hexdigest()
                               for o in (0,len(content)//2,len(content)-32)))
            textures.append(item)
    # Hash identification must never map identical input textures to different art.
    seen={}
    for item in textures:
        key=item['official']['sha256']
        value=item['custom']['sha256']
        assert key not in seen or seen[key]==value, 'Ambiguous texture replacement'
        seen[key]=value
    config=dict(textures=textures,initial='custom',rooms=rooms,cache_mib=64)
    (LIVE/'textures.json').write_text(json.dumps(config,indent=2))
    return config

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    config=prepare()
    if args.prepare_only:
        print(f'Prepared {len(config["textures"])} pairs of verified textures.');return
    os.chdir(ROOT.parent)
    device=frida.get_local_device()
    existing=[p for p in device.enumerate_processes() if p.name.lower()=='throttle.exe']
    if existing:
        raise SystemExit('Close the game first, then launch with Start live switcher.cmd.')
    log=(LIVE/'session.log').open('w',encoding='utf8',buffering=1)
    def write(message):
        line=time.strftime('%H:%M:%S')+' '+message
        print(line,flush=True);log.write(line+'\n')
    pid=device.spawn([str(ROOT.parent/'Throttle.exe')],cwd=str(ROOT.parent))
    (LIVE/'game-pid.txt').write_text(str(pid))
    session=device.attach(pid)
    running=True
    def detached(*args):
        nonlocal running
        running=False;write('Game detached: '+str(args))
    session.on('detached',detached)
    def load_script():
        new_script=session.create_script((ROOT/'live_switcher.js').read_text())
        new_script.on('message',lambda message,data:write(json.dumps(message)))
        new_script.load()
        new_script.exports_sync.configure(config)
        return new_script
    script=None
    try:
        script=load_script()
        device.resume(pid)
        write('F6 = official remastered backgrounds; F7 = custom. Existing classic toggle is unchanged.')
        write('Leave this helper running until you close the game.')
        command=LIVE/'command.json'
        if command.exists():command.unlink()
        while running:
            if command.exists():
                request=json.loads(command.read_text());command.unlink()
                if request.get('mode'):script.exports_sync.select(request['mode'])
                if request.get('status'):
                    status=script.exports_sync.status()
                    (LIVE/'status.json').write_text(json.dumps(status,indent=2));write('STATUS '+json.dumps(status))
            time.sleep(.1)
    except KeyboardInterrupt:
        write('Helper stopped; current textures stay until the game reloads them.')
    except Exception:
        write(traceback.format_exc())
        # Never leave a newly launched process suspended after setup failure.
        try:device.resume(pid)
        except Exception:pass
        raise
    finally:
        try:session.detach()
        except Exception:pass
        log.close()

if __name__=='__main__':main()
