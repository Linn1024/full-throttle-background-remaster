"""Self-contained Windows installer and launcher for the public beta."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import queue
import shutil
import struct
import sys
import threading
import time
import traceback
import uuid
import zipfile
import zlib

VERSION = '0.1.0-beta.1'
TITLE = 'Full Throttle Background Remaster'
DIRECTORY = 'FTBackgroundRemaster'
LAUNCHER = 'FTBackgroundRemaster.exe'
SHORTCUT = 'Play Full Throttle Background Remaster.cmd'
MARKER = 'full-throttle-background-remaster'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(root, relative):
    p = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe package path: ' + relative)
    root = Path(root).resolve()
    result = (root / Path(*p.parts)).resolve()
    if result == root or not result.is_relative_to(root):
        raise ValueError('Path escapes the mod folder: ' + relative)
    return result

def archive_index(stream):
    stream.seek(0, 2); length = stream.tell(); stream.seek(0)
    h = struct.unpack('<4s11I', stream.read(48))
    if h[0] != b'KAPL' or h[7] % 24 or h[2]+h[7] > length or h[4]+h[8] > length:
        raise ValueError('Unsupported or damaged full.data archive.')
    stream.seek(h[4]); names = stream.read(h[8]).split(b'\0')
    if len(names) < h[7]//24:
        raise ValueError('Incomplete archive directory.')
    index = {}
    stream.seek(h[2]); records = stream.read(h[7])
    for i in range(h[7]//24):
        offset, _, size, unpacked, flags = struct.unpack_from('<Q4I', records, i*24)
        name = names[i].decode('utf8')
        if h[5]+offset+size > length:
            raise ValueError('Archive entry is outside full.data: ' + name)
        index[name] = (h[5]+offset, size, unpacked, flags)
    return index

def texture_payload(data, number=None):
    if number is not None:
        nv, = struct.unpack_from('<I', data); pos = 4+nv*16
        ni, = struct.unpack_from('<H', data, pos); pos += 2+ni*2
        nt, = struct.unpack_from('<H', data, pos); pos = (pos+2+nt*4+3)&~3
        if not 0 <= number < nt:
            raise ValueError('Missing CHNK texture.')
        for i in range(nt):
            size, = struct.unpack_from('<I', data, pos); pos += 4
            payload = data[pos:pos+size]; pos = (pos+size+3)&~3
            if i == number:
                data = payload; break
    fmt, w, h = struct.unpack_from('<4sII', data)
    if fmt not in (b'DXT1', b'DXT5') or not 0 < w <= 16384 or not 0 < h <= 16384:
        raise ValueError('Unsupported texture format/dimensions.')
    expected = ((w+3)//4)*((h+3)//4)*(8 if fmt == b'DXT1' else 16)
    decoder = zlib.decompressobj(-15)
    raw = decoder.decompress(data[12:], expected+1)
    if len(raw) != expected or not decoder.eof:
        raise ValueError('Invalid compressed texture size.')
    return raw

def check_game(game):
    game = Path(game).resolve()
    if not (game/'Throttle.exe').is_file() or not (game/'full.data').is_file():
        raise ValueError('Choose the Full Throttle Remastered folder containing Throttle.exe and full.data.')
    with (game/'Throttle.exe').open('rb') as f:
        if f.read(2) != b'MZ':
            raise ValueError('Throttle.exe is not a Windows executable.')
    return game

def check_not_running():
    import frida
    if any(p.name.lower() == 'throttle.exe' for p in frida.get_local_device().enumerate_processes()):
        raise ValueError('Close Full Throttle Remastered and its helper before installing, removing or starting the mod.')

def read_install(root):
    path = Path(root)/'installation.json'
    meta = json.loads(path.read_text(encoding='utf8'))
    if meta.get('id') != MARKER:
        raise ValueError('This folder is not a recognized mod installation.')
    return meta

def install(game, package, executable, progress=print):
    game = check_game(game); check_not_running()
    dest = game/DIRECTORY
    if dest.exists():
        raise ValueError('FTBackgroundRemaster already exists. Use its Uninstall button first, then install this version. Saves are unaffected.')
    shortcut = game/SHORTCUT
    if shortcut.exists():
        raise ValueError('The mod launch shortcut already exists. Remove the previous mod installation first.')
    stage = game/(DIRECTORY+'.install-'+uuid.uuid4().hex)
    stage.mkdir(); committed = False
    try:
        with zipfile.ZipFile(package) as z:
            manifest = json.loads(z.read('package.json'))
            if manifest.get('id') != MARKER or manifest.get('version') != VERSION:
                raise ValueError('Installer and payload versions do not match.')
            for i, (name, info) in enumerate(manifest['files'].items()):
                path = safe_path(stage, name); data = z.read(name)
                if len(data) != info['size'] or digest(data) != info['sha256']:
                    raise ValueError('Damaged package file: '+name)
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
                if i%100 == 0: progress(f'Installing files: {i+1}/{len(manifest["files"])}')
        config = json.loads((stage/'textures.json').read_text())
        cache_name = None; cache_data = None
        with (game/'full.data').open('rb') as archive:
            index = archive_index(archive)
            for i, tex in enumerate(config['textures']):
                source = tex['source']; name = source['asset']
                if cache_name != name:
                    if name not in index: raise ValueError('Required game asset is missing: '+name)
                    offset,size,unpacked,flags = index[name]
                    if flags != 0 or size != unpacked: raise ValueError('Unsupported archive compression: '+name)
                    archive.seek(offset); cache_data = archive.read(size); cache_name = name
                raw = texture_payload(cache_data, source.get('texture'))
                if len(raw) != tex['size'] or digest(raw) != tex['official']['sha256']:
                    raise ValueError('Game assets differ from this mod version: '+name+'. Verify/restore your original game files, then try again.')
                path = safe_path(stage, tex['official']['path']);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
                if i%50 == 0: progress(f'Checking original game textures: {i+1}/{len(config["textures"])}')
        shutil.copy2(executable, stage/LAUNCHER)
        owned = {p.relative_to(stage).as_posix(): digest(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}
        command = '@echo off\r\nrem '+MARKER+'\r\nstart "" "%~dp0'+DIRECTORY+'\\'+LAUNCHER+'" --play\r\n'
        meta = dict(id=MARKER,version=VERSION,files=owned,shortcut_sha256=digest(command.encode('utf8')))
        (stage/'installation.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
        stage.rename(dest); committed=True
        try: shortcut.write_bytes(command.encode('utf8'))
        except Exception:
            dest.rename(stage); committed=False; raise
        progress('Installed. Use "Play Full Throttle Background Remaster.cmd" in your game folder.');return dest
    finally:
        if not committed and stage.exists():
            # A freshly created, random staging directory under the selected game.
            if stage.resolve().parent != game or not stage.name.startswith(DIRECTORY+'.install-'):
                raise ValueError('Unexpected staging directory.')
            shutil.rmtree(stage)

def uninstall(root, progress=print):
    root = Path(root).resolve();meta=read_install(root);check_not_running()
    # Validate ALL ownership paths before removing anything.
    paths = [(safe_path(root,name),sha) for name,sha in meta['files'].items()]
    shortcut = root.parent/SHORTCUT
    if shortcut.is_file() and digest(shortcut.read_bytes()) == meta['shortcut_sha256']: shortcut.unlink()
    preserved=[]
    for path,sha in paths:
        if not path.exists():continue
        if digest(path.read_bytes()) != sha:
            preserved.append(str(path));continue
        try:path.unlink()
        except PermissionError:
            # Windows locks the running launcher; remove it after this process exits.
            if path != root/LAUNCHER:raise
            preserved.append(str(path))
    for name in ('session.log','game-pid.txt','status.json','command.json'):
        path=safe_path(root,name)
        if path.is_file():path.unlink()
    (root/'installation.json').unlink()
    for p in sorted(root.rglob('*'),key=lambda p:len(p.parts),reverse=True):
        if p.is_dir():
            try:p.rmdir()
            except OSError:pass
    try:root.rmdir()
    except OSError:pass
    progress('Mod removed. Game files and saves were not changed.')
    if preserved:progress('Preserved changed or currently running files (delete after closing the helper if unwanted): '+', '.join(preserved))

def verify(root, progress=print):
    root=Path(root).resolve();meta=read_install(root)
    for i,(name,sha) in enumerate(meta['files'].items()):
        p=safe_path(root,name)
        if not p.is_file() or digest(p.read_bytes())!=sha:raise ValueError('Missing or changed mod file: '+name)
        if i%100==0:progress(f'Verifying files: {i+1}/{len(meta["files"])}')
    progress('All installed files passed verification.')

def runtime_config(root):
    root=Path(root).resolve();config=json.loads((root/'textures.json').read_text())
    for t in config['textures']:
        for mode in ('official','custom'):t[mode]['path']=str(safe_path(root,t[mode]['path']))
        for track in t.get('animation',{}).get('tracks',[]):
            for frame in track['frames']:frame['path']=str(safe_path(root,frame['path']))
    return config

def log_directory(root):
    base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))
    folder=base/DIRECTORY/digest(str(Path(root).resolve()).encode('utf8'))[:12]
    folder.mkdir(parents=True,exist_ok=True)
    return folder

def play(root, progress=print):
    import frida
    root=Path(root).resolve();read_install(root);game=check_game(root.parent);check_not_running()
    config=runtime_config(root);device=frida.get_local_device();done=threading.Event()
    log_path=log_directory(root)/'session.log'
    log=log_path.open('w',encoding='utf8',buffering=1)
    progress('Session log: '+str(log_path))
    def write(message):
        log.write(time.strftime('%H:%M:%S')+' '+message+'\n')
    pid=None;session=None
    try:
        pid=device.spawn([str(game/'Throttle.exe')],cwd=str(game))
        session=device.attach(pid);session.on('detached',lambda *a:done.set())
        script=session.create_script((root/'live_switcher.js').read_text(encoding='utf8'))
        script.on('message',lambda msg,data:write(json.dumps(msg)))
        script.load();script.exports_sync.configure(config);device.resume(pid)
        progress('Game started. F6: official graphics. F7: custom graphics. Keep this helper open while playing.')
        while not done.wait(.25):pass
        progress('Game closed.')
    except Exception:
        write(traceback.format_exc())
        if pid is not None:
            try:device.resume(pid)
            except Exception:pass
        raise
    finally:
        if session:
            try:session.detach()
            except Exception:pass
        log.close()

def executable_path():
    return Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve()

def gui(auto_play=False):
    import tkinter as tk
    from tkinter import filedialog,messagebox,ttk
    exe=executable_path();home=exe.parent;installed=(home/'installation.json').is_file()
    app=tk.Tk();app.title(TITLE+' '+VERSION);app.geometry('730x440')
    events=queue.Queue();busy=False;buttons=[]
    ttk.Label(app,text=TITLE,font=('Segoe UI',16)).pack(pady=(14,4))
    ttk.Label(app,text='Windows beta • F6 Official / F7 Custom • Original game required').pack()
    folder=tk.StringVar(value=str(home.parent) if installed else '')
    if not installed:
        row=ttk.Frame(app);row.pack(fill='x',padx=18,pady=14)
        ttk.Label(row,text='Game folder:').pack(side='left');ttk.Entry(row,textvariable=folder).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(row,text='Browse…',command=lambda:folder.set(filedialog.askdirectory(title='Select folder containing Throttle.exe') or folder.get())).pack(side='right')
    output=tk.Text(app,wrap='word',height=14);output.pack(fill='both',expand=True,padx=18,pady=10)
    def log(s):events.put(('log',str(s)))
    def run(fn):
        nonlocal busy
        if busy:return
        busy=True
        for b in buttons:b.configure(state='disabled')
        def worker():
            try:fn()
            except Exception as e:events.put(('error',str(e)))
            finally:events.put(('done',''))
        threading.Thread(target=worker,daemon=False).start()
    row=ttk.Frame(app);row.pack(pady=10)
    def add(label,fn):
        b=ttk.Button(row,text=label,command=fn);b.pack(side='left',padx=8);buttons.append(b)
    if installed:
        add('Play mod',lambda:run(lambda:play(home,log)))
        add('Verify files',lambda:run(lambda:verify(home,log)))
        def remove():
            if messagebox.askyesno('Remove mod?','Remove the mod files? Your game files and saves will remain untouched.'):
                run(lambda:uninstall(home,log))
        add('Uninstall',remove)
        log('Ready. Launch the mod here, or use the game-folder shortcut. Keep this window open while playing.')
    else:
        add('Install',lambda:run(lambda:install(folder.get(),home/'mod-payload.zip',exe,log)))
        add('Remove installed mod',lambda:run(lambda:uninstall(Path(folder.get())/DIRECTORY,log)) if messagebox.askyesno('Remove mod?','Remove this mod from the selected game folder?') else None)
        log('Select your Full Throttle Remastered game folder, then Install. Close the game first. No Python installation is needed.')
    def poll():
        nonlocal busy
        while not events.empty():
            kind,msg=events.get()
            if kind=='done':
                busy=False
                for b in buttons:b.configure(state='normal')
            else:
                output.insert('end',('ERROR: ' if kind=='error' else '')+msg+'\n');output.see('end')
        app.after(100,poll)
    def close():
        if busy:messagebox.showinfo('Operation in progress','Close the game and wait for the current operation to finish before closing this helper.')
        else:app.destroy()
    app.protocol('WM_DELETE_WINDOW',close);poll()
    if auto_play and installed:app.after(200,lambda:run(lambda:play(home,log)))
    app.mainloop()

def main():
    parser=argparse.ArgumentParser(description=TITLE)
    parser.add_argument('--install',type=Path);parser.add_argument('--payload',type=Path)
    parser.add_argument('--uninstall',type=Path);parser.add_argument('--verify',type=Path)
    parser.add_argument('--play',action='store_true');parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args();exe=executable_path()
    if args.self_test:
        import frida, tkinter
        window=tkinter.Tk();window.withdraw();window.update();window.destroy()
        report=dict(version=VERSION,frida=frida.__version__,tk=tkinter.TkVersion,process_enumeration=bool(frida.get_local_device().enumerate_processes()))
        (exe.parent/'self-test.json').write_text(json.dumps(report));return
    if args.install:install(args.install,args.payload or exe.parent/'mod-payload.zip',exe)
    elif args.uninstall:uninstall(args.uninstall)
    elif args.verify:verify(args.verify)
    else:gui(args.play)

if __name__=='__main__':
    try:main()
    except Exception:
        (log_directory(executable_path().parent)/'setup-error.log').write_text(traceback.format_exc(),encoding='utf8')
        raise
