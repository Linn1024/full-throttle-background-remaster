"""Exercise the real JS matcher in an isolated Frida host, without the game."""
import json
import subprocess
import sys
from pathlib import Path
import frida
from scene_assets import ROOT,read_chunk

def main():
    config=json.loads((ROOT/'live-switcher/textures.json').read_text())
    variants=[v for v in config['textures'] if v['name'].startswith('010-dumpster/')]
    source=(ROOT/'live_switcher.js').read_text()
    matcher=source[source.index('function matches('):source.index('function installUpload(')]
    script_source='const variants='+json.dumps(variants)+';\n'+"""
    function sha(p,n) {return Checksum.compute('sha256',p.readByteArray(n));}
    """+matcher+"""
    rpc.exports.check=function(size,width,height,data) {
        const p=Memory.alloc(size);p.writeByteArray(data);
        const hit=matches(p,size,width,height);
        return hit ? {name:hit.variant.name,mode:hit.mode} : null;
    };
    """
    worker=subprocess.Popen([sys.executable,'-c','import sys; sys.stdin.read()'],
                            stdin=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    session=None
    try:
        session=frida.attach(worker.pid)
        script=session.create_script(script_source);script.load()
        count=0
        for v in variants:
            def check(raw):
                return script.exports_sync.check(v['size'],v['width'],v['height'],raw)
            for mode in ('official','custom'):
                raw=Path(v[mode]['path']).read_bytes()
                assert check(raw)==dict(name=v['name'],mode=mode)
                count+=1
            if v.get('aliases'):
                _,stem,texture=v['name'].split('/')
                c=read_chunk(ROOT/'live-switcher'/('installed-'+stem+'.chnk'))
                raw=c['textures'][int(texture.removeprefix('texture'))]['raw']
                assert check(raw)==dict(name=v['name'],mode='installed')
                # Mutate outside the three fingerprint windows: full hashing
                # must reject even an otherwise identical installed texture.
                corrupt=bytearray(raw);corrupt[100]^=1
                assert check(bytes(corrupt)) is None
                count+=2
        print(f'Passed {count} real JavaScript texture-recognition checks.')
    finally:
        if session is not None:session.detach()
        worker.terminate();worker.wait(timeout=10)

if __name__=='__main__':main()
