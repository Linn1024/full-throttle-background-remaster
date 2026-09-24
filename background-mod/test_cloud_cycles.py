"""Exercise real cloud runtime JS in an isolated Frida process, never the game."""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
import frida
from scene_assets import ROOT

def main():
    config=json.loads((ROOT/'live-switcher/textures.json').read_text())
    variants=[v for v in config['textures'] if v.get('animation')]
    assert variants
    source=(ROOT/'live_switcher.js').read_text()
    runtime=source[source.index('function cycleSteps('):source.index('function initGL(')]
    js="""
    let choice='custom',uploading=false,frameCount=0,ready=true,pressed6=false,pressed7=false;
    const TARGET=3553,BINDING=32873,tracked=new Map(),intBuf=Memory.alloc(4),pidBuf=Memory.alloc(4);
    let bound=77,uploads=[],compressedReadback=null,errors=[];
    const gl={context:()=>ptr(1),isTexture:()=>true,bind:(t,id)=>{bound=id;},getInteger:(p,b)=>b.writeU32(bound)};
    function log(event,extra){if(event.includes('error'))errors.push({event,...extra});}
    function foreground(){return ptr(0);} function windowPid(w,p){p.writeU32(0);}
    function keyState(){return 0;} function select(mode){choice=mode;}
    function sha(p,n){return Checksum.compute('sha256',p.readByteArray(n));}
    function acquirePayload(v,mode){
      const d=v[mode],f=new File(d.path,'rb');let data;
      try{data=f.readBytes();}finally{f.close();}
      if(data.byteLength!==v.size || Checksum.compute('sha256',data)!==d.sha256)throw Error('Invalid payload');
      const memory=Memory.alloc(v.size);memory.writeByteArray(data);return {memory};
    }
    function releasePayload(){}
    function imageUpload(t,l,f,w,h,b,size,p){uploads.push({bound,sha:sha(p,size)});}
    """+runtime+"""
    rpc.exports={
      setup(v){tracked.clear();uploads=[];errors=[];choice='custom';bound=77;
        tracked.set(1,{id:1,context:'0x1',variant:v,format:33777,mode:'custom',lastUsed:1000,cycleStart:1000});},
      tick(elapsed,mode,active){choice=mode;let r=tracked.get(1);r.lastUsed=active?1000+elapsed:1;
        uploads=[];updateClouds(1000+elapsed);return {uploads,errors,steps:r.cycleSteps};},
      switchmode(mode){choice=mode;uploads=[];tracked.get(1).lastUsed=Date.now();frame();return {uploads,errors,bound,mode:tracked.get(1).mode};}
    };
    """
    worker=subprocess.Popen([sys.executable,'-c','import sys;sys.stdin.read()'],stdin=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    session=None;checks=0
    try:
        session=frida.attach(worker.pid);script=session.create_script(js);script.load();api=script.exports_sync
        for v in variants:
            api.setup(v)
            for elapsed in [0,167,334,1000,2500,4000]:
                expected=bytearray(Path(v['custom']['path']).read_bytes())
                for t in v['animation']['tracks']:
                    step=math.floor(elapsed/t['step_ms'])%len(t['frames'])
                    patch=Path(t['frames'][step]['path']).read_bytes();pos=0
                    for at,length in t['runs']:expected[at:at+length]=patch[pos:pos+length];pos+=length
                r=api.tick(elapsed,'custom',True)
                assert not r['errors'],r
                if r['uploads']:assert r['uploads'][-1]['sha']==hashlib.sha256(expected).hexdigest()
                else:assert elapsed==0 or all(math.floor(elapsed/t['step_ms'])%len(t['frames'])==0 for t in v['animation']['tracks'])
                checks+=1
            assert not api.tick(5000,'official',True)['uploads']
            assert not api.tick(6000,'custom',False)['uploads']
            # Actual frame() mode switch must restore official bytes.
            r=api.switchmode('official');assert r['uploads'][-1]['sha']==v['official']['sha256'] and not r['errors']
            r=api.switchmode('custom');assert r['uploads'][-1]['sha']==v['custom']['sha256'] and not r['errors']
            checks+=4
        print(f'Passed {checks} cloud scheduling, patch composition, inactivity and mode-switch checks across {len(variants)} textures.')
    finally:
        if session:session.detach()
        worker.terminate();worker.wait(timeout=10)

if __name__=='__main__':main()
