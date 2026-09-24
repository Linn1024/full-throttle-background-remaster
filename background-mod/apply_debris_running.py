"""Attach the four debris replacements to an existing session; never launch it."""
import json
import subprocess
import threading
import time
import frida
from scene_assets import ROOT

EXTRA=r'''
let adoptDone=false;
const moduleGL=Process.getModuleByName('opengl32.dll');
const resolveGL=new NativeFunction(moduleGL.getExportByName('wglGetProcAddress'),'pointer',['pointer'],'stdcall');
const levelInfo=new NativeFunction(moduleGL.getExportByName('glGetTexLevelParameteriv'),'void',['uint','int','uint','pointer'],'stdcall');
Interceptor.attach(moduleGL.getExportByName('glClear'),{onEnter(){
 if(adoptDone||!ready||!gl||gl.context().isNull())return;
 adoptDone=true;
 installUpload(resolveGL(Memory.allocUtf8String('glCompressedTexImage2D')));
 compressedReadback=new NativeFunction(resolveGL(Memory.allocUtf8String('glGetCompressedTexImage')),'void',['uint','int','pointer'],'stdcall');
 gl.getInteger(BINDING,intBuf);const old=intBuf.readU32();
 try{
  for(let id=1;id<=256;id++){
   if(!gl.isTexture(id))continue;
   gl.bind(TARGET,id);
   levelInfo(TARGET,0,0x86a1,intBuf);if(!intBuf.readS32())continue;
   levelInfo(TARGET,0,0x1000,intBuf);const w=intBuf.readS32();
   levelInfo(TARGET,0,0x1001,intBuf);const h=intBuf.readS32();
   if(w!==2048||h!==2048)continue;
   levelInfo(TARGET,0,0x86a0,intBuf);const size=intBuf.readS32();
   if(size!==4194304)continue;
   const buffer=Memory.alloc(size);compressedReadback(TARGET,0,buffer);
   const hit=matches(buffer,size,w,h);if(!hit)continue;
   tracked.set(id,{id,context:gl.context().toString(),variant:hit.variant,format:0x83f3,mode:hit.mode});
   log('adopt-verified',{id,name:hit.variant.name,mode:hit.mode});
  }
 }finally{gl.bind(TARGET,old);}
}});
'''

if __name__=='__main__':
    pids=subprocess.check_output(['powershell','-NoProfile','-Command',
        '(Get-Process Throttle -ErrorAction SilentlyContinue).Id'],text=True).split()
    if len(pids)!=1:raise SystemExit('Expected one running game')
    config=json.loads((ROOT/'live-switcher/textures.json').read_text())
    config['textures']=[t for t in config['textures'] if '/124-debris-' in t['name']]
    assert len(config['textures'])==4
    done=threading.Event();session=frida.get_local_device().attach(int(pids[0]))
    session.on('detached',lambda *args:done.set())
    log=(ROOT/'live-switcher/debris-live.log').open('w',encoding='utf8',buffering=1)
    try:
        script=session.create_script((ROOT/'live_switcher.js').read_text()+EXTRA)
        script.on('message',lambda m,data:log.write(time.strftime('%H:%M:%S')+' '+json.dumps(m)+'\n'))
        script.load();script.exports_sync.configure(config)
        while not done.wait(1):pass
    finally:
        try:session.detach()
        except Exception:pass
        log.close()
