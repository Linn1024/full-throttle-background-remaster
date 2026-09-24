'use strict';

// Local, process-only OpenGL texture replacement. No executable/archive writes.
const variants = [];
const tracked = new Map();
const hooked = new Set();
const frameHooks = new Set();
const deleteHooks = new Set();
let choice = 'custom', gl = null, imageUpload = null, ready = false;
let uploading = false, pressed6 = false, pressed7 = false, frameCount = 0;
let compressedReadback = null;
const payloadCache = new Map();
let cacheBytes = 0, cacheLimit = 64*1024*1024, cacheClock = 0;
const kernel = Process.getModuleByName('kernel32.dll');
const reservePayload = new NativeFunction(kernel.getExportByName('VirtualAlloc'),'pointer',['pointer','size_t','uint','uint'],{abi:'stdcall',scheduling:'exclusive'});
const freePayload = new NativeFunction(kernel.getExportByName('VirtualFree'),'int',['pointer','size_t','uint'],{abi:'stdcall',scheduling:'exclusive'});
const TARGET = 0x0de1, BINDING = 0x8069;
const win = Process.getModuleByName('user32.dll');
const keyState = new NativeFunction(win.getExportByName('GetAsyncKeyState'),'int16',['int'],'stdcall');
const foreground = new NativeFunction(win.getExportByName('GetForegroundWindow'),'pointer',[],'stdcall');
const windowPid = new NativeFunction(win.getExportByName('GetWindowThreadProcessId'),'uint',['pointer','pointer'],'stdcall');
const intBuf = Memory.alloc(4), pidBuf = Memory.alloc(4);

function log(event, extra={}) { send({event, ...extra}); }
function trimCache(incoming=0) {
    const candidates=[...payloadCache.entries()].filter(([key,p])=>p.pins===0).sort((a,b)=>a[1].used-b[1].used);
    for(const [key,p] of candidates) {
        if(cacheBytes+incoming<=cacheLimit)break;
        if(!freePayload(p.memory,0,0x8000))throw new Error('Texture cache release failed');
        payloadCache.delete(key);cacheBytes-=p.length;
    }
}
function acquirePayload(v,mode) {
    const descriptor=v[mode], key=descriptor.sha256;
    let p=payloadCache.get(key);
    if(p) {p.pins++;p.used=++cacheClock;return p;}
    trimCache(v.size);
    const f=new File(descriptor.path,'rb');
    let data;
    try {data=f.readBytes();} finally {f.close();}
    if(data.byteLength!==v.size || Checksum.compute('sha256',data)!==key)
        throw new Error('Texture payload validation failed: '+v.name+'/'+mode);
    p=payloadCache.get(key);
    if(p) {p.pins++;p.used=++cacheClock;return p;}
    const memory=reservePayload(ptr(0),v.size,0x3000,0x04);
    if(memory.isNull())throw new Error('Texture cache allocation failed: '+v.name);
    try {memory.writeByteArray(data);} catch(error) {freePayload(memory,0,0x8000);throw error;}
    p={memory,length:v.size,pins:1,used:++cacheClock};
    payloadCache.set(key,p);cacheBytes+=v.size;
    return p;
}
function releasePayload(p) {
    if(!p)return;
    p.pins--;trimCache();
}
function sha(pointer,length) { return Checksum.compute('sha256',pointer.readByteArray(length)); }
function select(mode) {
    if (mode !== 'official' && mode !== 'custom') throw new Error('Unknown mode');
    choice = mode;
    log('selected',{mode, tracked:tracked.size});
}
function matches(data, size, width, height) {
    const candidates = variants.filter(v => v.size === size && v.width === width && v.height === height);
    if (!candidates.length || data.isNull()) return null;
    // Small fingerprints exclude unrelated scene/character textures cheaply.
    const fingerprint = [0,Math.floor(size/2),size-32].map(o => sha(data.add(o),32)).join(':');
    for (const v of candidates) {
        for (const mode of ['official','custom']) {
            if (v[mode].fingerprint !== fingerprint) continue;
            if (sha(data,size) === v[mode].sha256) return {variant:v,mode};
        }
        // Older archive-installed custom textures are input identities only.
        // F6/F7 still upload the verified official/current-custom payloads.
        for (const alias of (v.aliases || [])) {
            if (alias.fingerprint === fingerprint && sha(data,size) === alias.sha256)
                return {variant:v,mode:'installed'};
        }
    }
    return null;
}
function installUpload(address) {
    const key = address.toString();
    if (address.isNull() || hooked.has(key)) return;
    hooked.add(key);
    imageUpload = new NativeFunction(address,'void',['uint','int','uint','int','int','int','int','pointer'],'stdcall');
    Interceptor.attach(address,{
        onEnter(args) {
            if (uploading || !ready || args[0].toUInt32() !== TARGET || args[1].toInt32() !== 0) return;
            gl.getInteger(BINDING,intBuf);
            const id = intBuf.readU32();
            tracked.delete(id);
            const found = matches(args[7],args[6].toInt32(),args[3].toInt32(),args[4].toInt32());
            if (!found) return;
            const context = gl.context().toString();
            try {
                this.payload=acquirePayload(found.variant,choice);
                this.record = {id, context, variant:found.variant, format:args[2].toUInt32(), mode:choice, checked:false};
                args[7] = this.payload.memory;
            } catch(error) {log('payload-error',{name:found.variant.name,message:String(error)});}
        },
        onLeave() {
            releasePayload(this.payload);
            if (!this.record) return;
            const r = this.record;
            tracked.set(r.id,r);
            log('texture-matched',{id:r.id,name:r.variant.name,mode:r.mode,context:r.context});
        }
    });
    log('upload-hook',{address:key});
}
function installFrame(address) {
    if(address.isNull() || frameHooks.has(address.toString()))return;
    frameHooks.add(address.toString());
    Interceptor.attach(address,{onEnter:frame});
}
function installDelete(address) {
    if(address.isNull() || deleteHooks.has(address.toString()))return;
    deleteHooks.add(address.toString());
    Interceptor.attach(address,{onEnter(args) {
        const n=args[0].toInt32();
        for(let i=0;i<n;i++)tracked.delete(args[1].add(i*4).readU32());
    }});
}
function cycleSteps(animation,elapsed) {
    return animation.tracks.map(t=>Math.floor(Math.max(0,elapsed)/t.step_ms)%t.frames.length);
}
function updateClouds(now) {
    if(choice!=='custom')return;
    for(const r of tracked.values()) {
        const v=r.variant,a=v.animation;
        if(!a || r.mode!=='custom' || !r.lastUsed || now-r.lastUsed>250 || r.context!==gl.context().toString())continue;
        if(!gl.isTexture(r.id)){tracked.delete(r.id);continue;}
        if(r.cycleStart===undefined)r.cycleStart=now;
        const steps=cycleSteps(a,now-r.cycleStart);
        if(r.cycleSteps && steps.every((s,i)=>s===r.cycleSteps[i]))continue;
        let base;
        try {
            if(!r.cycleBuffer) {
                base=acquirePayload(v,'custom');
                r.cycleBuffer=Memory.alloc(v.size);
                Memory.copy(r.cycleBuffer,base.memory,v.size);
            }
            for(let i=0;i<a.tracks.length;i++) {
                if(r.cycleSteps && steps[i]===r.cycleSteps[i])continue;
                const track=a.tracks[i],descriptor=track.frames[steps[i]];
                let patch;
                try {
                    patch=acquirePayload({size:descriptor.size,name:v.name,custom:descriptor},'custom');
                    let source=0;
                    for(const [offset,length] of track.runs) {
                        Memory.copy(r.cycleBuffer.add(offset),patch.memory.add(source),length);source+=length;
                    }
                } finally {releasePayload(patch);}
            }
            gl.bind(TARGET,r.id);
            imageUpload(TARGET,0,r.format,v.width,v.height,0,v.size,r.cycleBuffer);
            r.cycleSteps=steps;
            if(!r.cycleLogged && steps.some(s=>s!==0)) {
                log('cloud-animation-active',{name:v.name,tracks:a.tracks.length});
                r.cycleLogged=true;
            }
        } catch(error) {log('cloud-animation-error',{name:v.name,message:String(error)});}
        finally {releasePayload(base);}
    }
}
function frame() {
    if (!gl || !ready || uploading || gl.context().isNull()) return;
    frameCount++;
    if (frameCount === 1) log('render-active',{context:gl.context().toString()});
    windowPid(foreground(),pidBuf);
    if (pidBuf.readU32() === Process.id) {
        const six = (keyState(0x75)&0x8000)!==0;
        const seven = (keyState(0x76)&0x8000)!==0;
        if (six && !pressed6) select('official');
        if (seven && !pressed7) select('custom');
        pressed6=six; pressed7=seven;
    } else { pressed6=false; pressed7=false; }
    if (!imageUpload) return;
    const pending = [...tracked.values()].filter(r => r.mode !== choice);
    const animate=choice==='custom' && [...tracked.values()].some(r=>r.variant.animation);
    if (!pending.length && !animate) return;
    gl.getInteger(BINDING,intBuf); const old = intBuf.readU32();
    uploading=true;
    let count=0;
    try {
        for (const r of pending) {
            if (!gl.isTexture(r.id)) { tracked.delete(r.id); continue; }
            // Uploads and drawing must share this context for IDs to be meaningful.
            if (gl.context().toString() !== r.context) {
                if (!r.warned) {log('different-context',{id:r.id});r.warned=true;}
                continue;
            }
            gl.bind(TARGET,r.id);
            const v=r.variant;
            let payload;
            try {
                payload=acquirePayload(v,choice);
                imageUpload(TARGET,0,r.format,v.width,v.height,0,v.size,payload.memory);
            } catch(error) {
                log('payload-error',{name:v.name,message:String(error)});continue;
            } finally {releasePayload(payload);}
            if(compressedReadback) {
                const check=Memory.alloc(v.size);
                compressedReadback(TARGET,0,check);
                if(sha(check,v.size)!==v[choice].sha256) {
                    log('verification-failed',{id:r.id,name:v.name});
                    continue;
                }
            }
            r.mode=choice;
            r.cycleSteps=null;r.cycleBuffer=null;r.cycleStart=undefined;
            count++;
        }
        if(animate)updateClouds(Date.now());
    } finally { gl.bind(TARGET,old); uploading=false; }
    if (count) log('switched',{mode:choice,count});
}
function initGL(module) {
    if (gl) return;
    function fn(name,ret,args) {return new NativeFunction(module.getExportByName(name),ret,args,'stdcall');}
    gl = {
        context:fn('wglGetCurrentContext','pointer',[]),
        getInteger:fn('glGetIntegerv','void',['uint','pointer']),
        bind:fn('glBindTexture','void',['uint','uint']),
        isTexture:fn('glIsTexture','uchar',['uint'])
    };
    Interceptor.attach(module.getExportByName('glBindTexture'),{onEnter(args) {
        if(uploading || args[0].toUInt32()!==TARGET)return;
        const r=tracked.get(args[1].toUInt32());
        if(r && r.variant.animation)r.lastUsed=Date.now();
    }});
    Interceptor.attach(module.getExportByName('wglGetProcAddress'),{
        onEnter(args) {this.name=args[0].readCString();},
        onLeave(result) {
            if (this.name === 'glCompressedTexImage2D' || this.name === 'glCompressedTexImage2DARB') installUpload(result);
            if(this.name==='glClear')installFrame(result);
            if(this.name==='glDeleteTextures')installDelete(result);
            if(this.name==='glGetCompressedTexImage' && !result.isNull())
                compressedReadback=new NativeFunction(result,'void',['uint','int','pointer'],'stdcall');
        }
    });
    installDelete(module.getExportByName('glDeleteTextures'));
    const gdi=Process.getModuleByName('gdi32.dll');
    installFrame(gdi.getExportByName('SwapBuffers'));
    // Some Windows drivers bypass the public GDI SwapBuffers entry point.
    // glClear runs on the game's render context before drawing the next frame.
    installFrame(module.getExportByName('glClear'));
    log('opengl-hooked');
}

rpc.exports = {
    configure(config) {
        choice=config.initial || 'custom';
        cacheLimit=Math.max(16,config.cache_mib || 64)*1024*1024;
        for (const v of config.textures) {
            for (const mode of ['official','custom']) {
                if(!v[mode].fingerprint)throw new Error('Rebuild texture catalog: missing fingerprint');
            }
            variants.push(v);
        }
        ready=true;
        log('ready',{textures:variants.length,mode:choice,cacheLimitMiB:cacheLimit/1048576,lazyPayloads:true});
        return variants.length;
    },
    select,
    adopt(records) {
        for(const r of records) {
            const variant=variants.find(v=>v.name===r.name);
            if(variant)tracked.set(r.id,{...r,variant});
        }
    },
    status() {return {mode:choice,frames:frameCount,cacheBytes,cacheLimit,cacheEntries:payloadCache.size,textures:[...tracked.values()].map(r=>({id:r.id,name:r.variant.name,mode:r.mode,context:r.context,format:r.format}))};}
};
Process.attachModuleObserver({onAdded(m) {if(m.name.toLowerCase()==='opengl32.dll')initGL(m);}});
