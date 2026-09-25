"""Offline installer regression tests; never starts Throttle.exe."""
import hashlib,json,shutil,struct,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import release_app as app

ROOT=Path(__file__).resolve().parent

class SafetyTests(unittest.TestCase):
 def test_paths(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'release') as d:
   for name in ('../escape','C:/escape','/escape','a/../../b','x\\y',''):
    with self.assertRaises(ValueError):app.safe_path(d,name)
   self.assertEqual(app.safe_path(d,'payloads/file.bin'),Path(d)/'payloads/file.bin')

 def test_bad_payload_rolls_back(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'release') as d:
   root=Path(d);(root/'Throttle.exe').write_bytes(b'MZ fixture only');(root/'full.data').write_bytes(b'no archive')
   before=(root/'full.data').read_bytes();package=root/'bad.zip'
   with zipfile.ZipFile(package,'w') as z:
    z.writestr('package.json',json.dumps(dict(id=app.MARKER,version=app.VERSION,files={'hello.txt':dict(size=5,sha256='bad')})))
    z.writestr('hello.txt',b'hello')
   with patch.object(app,'check_not_running'),self.assertRaisesRegex(ValueError,'Damaged'):
    app.install(root,package,root/'Throttle.exe',lambda x:None)
   self.assertFalse((root/app.DIRECTORY).exists());self.assertEqual((root/'full.data').read_bytes(),before)
   self.assertFalse(list(root.glob(app.DIRECTORY+'.install-*')))

 def test_uninstall_preserves_unknown_and_changed_files(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'release') as d:
   root=Path(d)/app.DIRECTORY;root.mkdir()
   (root/'known').write_bytes(b'ok');(root/'changed').write_bytes(b'edited');(root/'user-note').write_bytes(b'keep')
   (root/'installation.json').write_text(json.dumps(dict(id=app.MARKER,files={'known':app.digest(b'ok'),'changed':app.digest(b'original')},shortcut_sha256='none')))
   with patch.object(app,'check_not_running'):app.uninstall(root,lambda x:None)
   self.assertFalse((root/'known').exists());self.assertEqual((root/'changed').read_bytes(),b'edited');self.assertTrue((root/'user-note').exists())

 def test_uninstall_rejects_escape_before_deleting(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'release') as d:
   root=Path(d)/app.DIRECTORY;root.mkdir();outside=Path(d)/'keep';outside.write_bytes(b'ok')
   (root/'installation.json').write_text(json.dumps(dict(id=app.MARKER,files={'../keep':app.digest(b'ok')},shortcut_sha256='none')))
   with patch.object(app,'check_not_running'),self.assertRaises(ValueError):app.uninstall(root)
   self.assertTrue(outside.exists())

def fixture_archive(path):
 sources=json.loads((ROOT/'release/source-assets.json').read_text());items=sorted(sources.items())
 names=b''.join(name.encode()+b'\0' for name,_ in items);table=48;strings=table+24*len(items);start=strings+len(names)
 records=[];offset=0
 for name,src in items:
  size=Path(src).stat().st_size;records.append(struct.pack('<Q4I',offset,0,size,size,0));offset+=size
 header=[0]*11;header[1]=table;header[3]=strings;header[4]=start;header[6]=24*len(items);header[7]=len(names)
 with path.open('wb') as f:
  f.write(struct.pack('<4s11I',b'KAPL',*header));f.write(b''.join(records));f.write(names)
  for _,src in items:
   with Path(src).open('rb') as data:shutil.copyfileobj(data,f)

def integration():
 package=ROOT/'release'/app.VERSION;exe=package/'Setup.exe'
 with tempfile.TemporaryDirectory(prefix='Install test Пример ',dir=ROOT/'release') as d:
  game=Path(d)/'Game folder';game.mkdir();shutil.copy2(ROOT.parent/'Throttle.exe',game/'Throttle.exe');fixture_archive(game/'full.data')
  before={n:app.digest((game/n).read_bytes()) for n in ('Throttle.exe','full.data')}
  creationflags=0x08000000 if sys.platform=='win32' else 0
  def run(*args):subprocess.run([str(exe),*map(str,args)],check=True,timeout=240,creationflags=creationflags)
  run('--self-test');assert json.loads((package/'self-test.json').read_text())['process_enumeration']
  run('--install',game,'--payload',package/'mod-payload.zip')
  installed=game/app.DIRECTORY;app.verify(installed,lambda x:None)
  config=app.runtime_config(installed)
  for tex in config['textures']:
   for mode in ('official','custom'):assert app.digest(Path(tex[mode]['path']).read_bytes())==tex[mode]['sha256']
   for track in tex.get('animation',{}).get('tracks',[]):
    for frame in track['frames']:assert app.digest(Path(frame['path']).read_bytes())==frame['sha256']
  # Relocation after installation must resolve paths against the new folder.
  moved=Path(d)/'Moved game';game.rename(moved);game=moved;installed=game/app.DIRECTORY
  assert all(Path(t['custom']['path']).is_relative_to(installed) for t in app.runtime_config(installed)['textures'])
  run('--verify',installed)
  (installed/'keep-my-note.txt').write_text('player file')
  run('--uninstall',installed)
  assert list(installed.iterdir())==[installed/'keep-my-note.txt'];assert not (game/app.SHORTCUT).exists()
  assert before=={n:app.digest((game/n).read_bytes()) for n in before}
  result=dict(textures_verified=len(config['textures']),frozen_runtime_self_test=True,install=True,verify=True,relocation=True,uninstall=True,user_files_preserved=True,game_files_unchanged=True,game_launched=False,setup_sha256=app.digest(exe.read_bytes()),payload_sha256=app.digest((package/'mod-payload.zip').read_bytes()))
  (package/'test-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':
 if '--integration' in sys.argv:integration()
 else:unittest.main()
