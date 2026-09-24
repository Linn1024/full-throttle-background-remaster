"""Exercise the actual Frida cache in a disposable Python process, not the game."""
import json
import subprocess
import sys
import os
from pathlib import Path
import frida
from scene_assets import ROOT


def main():
    # A hidden 32-bit command interpreter waiting on its private input pipe.
    # It performs no filesystem operations and uses the same ABI as Throttle.
    child=subprocess.Popen([str(Path(os.environ['WINDIR'])/'SysWOW64/cmd.exe'),'/d','/q','/c','set /p cache_test_wait='],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    session=None
    try:
        session=frida.get_local_device().attach(child.pid)
        extra=r'''
        rpc.exports.exercise = function() {
            if(Process.pointerSize!==4)throw new Error('Expected 32-bit test process');
            if(cacheBytes!==0)throw new Error('Configure preloaded texture memory');
            const first=variants[0], pinned=acquirePayload(first,'custom');
            const fingerprint=sha(pinned.memory,pinned.length);
            let loads=0,peak=cacheBytes;
            for(const v of variants) {
                for(const mode of ['official','custom']) {
                    const p=acquirePayload(v,mode);
                    if(sha(p.memory,p.length)!==v[mode].sha256)throw new Error('Payload changed');
                    const hit=matches(p.memory,p.length,v.width,v.height);
                    if(!hit || hit.variant[hit.mode].sha256!==v[mode].sha256)throw new Error('Upload fingerprint did not match');
                    releasePayload(p);loads++;peak=Math.max(peak,cacheBytes);
                    if(cacheBytes>cacheLimit)throw new Error('Cache exceeded its bound');
                }
                for(const track of (v.animation?.tracks || [])) {
                    for(const frame of track.frames) {
                        const patch={name:v.name,size:frame.size,custom:frame};
                        const p=acquirePayload(patch,'custom');
                        if(sha(p.memory,p.length)!==frame.sha256)throw new Error('Cloud patch changed');
                        releasePayload(p);loads++;peak=Math.max(peak,cacheBytes);
                        if(cacheBytes>cacheLimit)throw new Error('Cloud cache exceeded its bound');
                    }
                }
            }
            if(sha(pinned.memory,pinned.length)!==fingerprint)throw new Error('Pinned payload evicted');
            releasePayload(pinned);
            const before=cacheBytes;
            const savedLimit=cacheLimit;cacheLimit=0;trimCache();cacheLimit=savedLimit;
            if(cacheBytes!==0 || payloadCache.size!==0)throw new Error('Cache failed to release');
            const reload=acquirePayload(first,'custom');
            if(sha(reload.memory,reload.length)!==first.custom.sha256)throw new Error('Reload failed');
            releasePayload(reload);
            const invalid={...first,custom:{...first.custom,sha256:'0'.repeat(64)}};
            let rejected=false;
            try {acquirePayload(invalid,'custom');} catch(error) {rejected=true;}
            if(!rejected)throw new Error('Invalid payload accepted');
            return {pointerSize:Process.pointerSize,loads,peakBytes:peak,limitBytes:cacheLimit,releasedBytes:before,
                    pinnedPayloadPreserved:true,reloadVerified:true,invalidHashRejected:true,uploadFingerprintsVerified:true};
        };
        '''
        script=session.create_script("Module.load('user32.dll');\n"+(ROOT/'live_switcher.js').read_text()+extra)
        script.on('message',lambda message,data:print(json.dumps(message),flush=True) if message.get('type')=='error' else None)
        script.load()
        config=json.loads((ROOT/'live-switcher/textures.json').read_text())
        script.exports_sync.configure(config)
        result=script.exports_sync.exercise()
        (ROOT/'live-switcher/cache-validation.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
    finally:
        if session:session.detach()
        child.terminate();child.wait(timeout=10)


if __name__=='__main__':main()
