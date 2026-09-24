"""Read texture hashes from an already running game; never launches it."""
import json
import threading
import subprocess
import frida
from scene_assets import ROOT

SCRIPT = r'''
const m=Process.getModuleByName('opengl32.dll');
function fn(n,r,a){return new NativeFunction(m.getExportByName(n),r,a,'stdcall');}
const context=fn('wglGetCurrentContext','pointer',[]);
const get=fn('glGetIntegerv','void',['uint','pointer']);
const bind=fn('glBindTexture','void',['uint','uint']);
const exists=fn('glIsTexture','uchar',['uint']);
const level=fn('glGetTexLevelParameteriv','void',['uint','int','uint','pointer']);
const param=fn('glGetTexParameteriv','void',['uint','uint','pointer']);
const proc=fn('wglGetProcAddress','pointer',['pointer']);
const b=Memory.alloc(4), T=0x0de1;
let next=1, reading=false, read=null;
function value(l,p){level(T,l,p,b);return b.readS32();}
Interceptor.attach(m.getExportByName('glClear'),{onEnter(){
 if(reading||next>256||context().isNull())return;
 reading=true;
 get(0x8069,b);const old=b.readU32();
 try {
  if(!read)read=new NativeFunction(proc(Memory.allocUtf8String('glGetCompressedTexImage')),'void',['uint','int','pointer'],'stdcall');
  for(let i=0;i<4&&next<=256;i++,next++){
   if(!exists(next))continue;
   bind(T,next);const levels=[];
   param(T,0x2801,b);const filter=b.readS32();
   for(let l=0;l<3;l++){
    const w=value(l,0x1000),h=value(l,0x1001);
    if(!w||!h)break;
    const compressed=value(l,0x86a1);
    const item={level:l,w,h,compressed};
    if(compressed){const size=value(l,0x86a0);const buf=Memory.alloc(size);read(T,l,buf);item.size=size;item.sha256=Checksum.compute('sha256',buf.readByteArray(size));}
    levels.push(item);
   }
   send({id:next,filter,levels});
  }
  if(next>256)send({done:true});
 }finally{bind(T,old);reading=false;}
}});
'''

if __name__ == '__main__':
    device=frida.get_local_device()
    pids=subprocess.check_output(['powershell','-NoProfile','-Command',
        '(Get-Process Throttle -ErrorAction SilentlyContinue).Id'],text=True).split()
    if len(pids)!=1:raise SystemExit('Expected one already running game')
    records=[];done=threading.Event()
    session=device.attach(int(pids[0]))
    try:
        script=session.create_script(SCRIPT)
        def message(m,data):
            if m.get('type')=='error':print(m);done.set();return
            p=m.get('payload',{})
            if p.get('done'):done.set()
            else:records.append(p)
        script.on('message',message);script.load()
        if not done.wait(45):print('Timed out waiting for rendering')
    finally:session.detach()
    catalog=json.loads((ROOT/'live-switcher/textures.json').read_text())['textures']
    hashes={v[mode]['sha256']:v['name']+'/'+mode for v in catalog for mode in ('official','custom')}
    for r in records:
        for l in r.get('levels',[]):l['match']=hashes.get(l.get('sha256'))
    path=ROOT/'live-switcher/gpu-inspection.json'
    path.write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))
