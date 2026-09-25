"""Build the relocatable public package from the validated live catalog."""
import copy,hashlib,importlib.metadata,json,shutil,subprocess,sys,zipfile,urllib.request
from pathlib import Path
from release_app import VERSION,MARKER,texture_payload

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'release'/VERSION

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 config=json.loads((ROOT/'live-switcher/textures.json').read_text())
 original_files={}
 for path in (ROOT/'original').rglob('*'):
  if path.suffix in ('.chnk','.dxt'):original_files.setdefault(path.name,[]).append(path)
 files={};entries={};sources={}
 def add(name,data):
  sha=hashlib.sha256(data).hexdigest()
  if name in entries:assert entries[name]==data;return
  entries[name]=data;files[name]=dict(size=len(data),sha256=sha)
 def blob(desc):
  data=Path(desc['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==desc['sha256']
  name='payloads/'+desc['sha256']+'.bin';add(name,data);desc['path']=name
 for tex in config['textures']:
  parts=tex['name'].split('/');chunk=len(parts)==3
  filename=parts[1]+('.chnk' if chunk else '.dxt')
  candidates=original_files[filename];number=int(parts[2][7:]) if chunk else None
  matches=[p for p in candidates if hashlib.sha256(texture_payload(p.read_bytes(),number)).hexdigest()==tex['official']['sha256']]
  assert matches,(tex['name'],candidates)
  source=matches[0];tex['source']=dict(asset=source.relative_to(ROOT/'original').as_posix())
  if chunk:tex['source']['texture']=number
  sources[tex['source']['asset']]=str(source)
  tex['official']['path']='originals/'+tex['official']['sha256']+'.bin'
  # Development-only archive aliases are not part of the clean public build.
  tex.pop('aliases',None);blob(tex['custom'])
  animation=tex.get('animation',{})
  for track in animation.get('tracks',[]):
   for frame in track['frames']:blob(frame)
 add('textures.json',(json.dumps(config,indent=2)+'\n').encode())
 add('live_switcher.js',(ROOT/'live_switcher.js').read_bytes())
 add('README.txt',(ROOT/'RELEASE-README.md').read_bytes())
 add('THIRD-PARTY-NOTICES.txt',(ROOT/'RELEASE-NOTICES.md').read_bytes())
 dist=importlib.metadata.distribution('frida')
 license_path=next(p for p in dist.files if str(p).endswith('licenses/COPYING'))
 add('licenses/Frida-COPYING.txt',dist.locate_file(license_path).read_bytes())
 python_license=Path(sys.base_prefix)/'LICENSE.txt';assert python_license.is_file()
 add('licenses/Python-LICENSE.txt',python_license.read_bytes())
 pyi=importlib.metadata.distribution('pyinstaller')
 pyi_license=next(p for p in pyi.files if str(p).endswith('licenses/COPYING.txt'))
 add('licenses/PyInstaller-COPYING.txt',pyi.locate_file(pyi_license).read_bytes())
 # Tcl/Tk are bundled by PyInstaller for the installer and launcher UI.
 for label,folder in [('Tcl','tcl8.6'),('Tk','tk8.6')]:
  p=Path(sys.base_prefix)/'tcl'/folder/'license.terms'
  if not p.exists() and label=='Tcl':
   p=ROOT/'release/Tcl-license.terms'
   if not p.exists():p.write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/tcltk/tcl/core-8-6-15/license.terms').read())
  assert p.exists(),f'Missing {label} license'
  if p.exists():add('licenses/'+label+'-license.txt',p.read_bytes())
 manifest=dict(id=MARKER,version=VERSION,files=files)
 payload=OUT/'mod-payload.zip'
 with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for name,data in entries.items():z.writestr(name,data)
  z.writestr('package.json',json.dumps(manifest,indent=2))
 (OUT/'build-report.json').write_text(json.dumps(dict(version=VERSION,textures=len(config['textures']),rooms=len(set(config['rooms'])),payload_files=len(files),payload_bytes=payload.stat().st_size,source_assets=len(sources)),indent=2))
 # Private validation index stays outside the public archive.
 (ROOT/'release/source-assets.json').write_text(json.dumps(sources,indent=2))
 for src,dest in [('RELEASE-README.md','README.txt'),('MODDB-DESCRIPTION.md','MODDB-DESCRIPTION.txt'),('RELEASE-NOTICES.md','THIRD-PARTY-NOTICES.txt')]:shutil.copy2(ROOT/src,OUT/dest)
 print((OUT/'build-report.json').read_text(),flush=True)

if __name__=='__main__':main()
