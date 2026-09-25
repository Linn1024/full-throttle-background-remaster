"""Package only public release files, with checksums and an allowlist."""
import hashlib,json,zipfile
from pathlib import Path
from release_app import VERSION

ROOT=Path(__file__).resolve().parent

def main():
 folder=ROOT/'release'/VERSION
 report=json.loads((folder/'test-report.json').read_text())
 assert report['install'] and report['uninstall'] and not report['game_launched']
 names=['Setup.exe','mod-payload.zip','README.txt','THIRD-PARTY-NOTICES.txt','MODDB-DESCRIPTION.txt']
 hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in names}
 assert hashes['Setup.exe']==report['setup_sha256'] and hashes['mod-payload.zip']==report['payload_sha256'],'Rerun integration tests after rebuilding'
 (folder/'SHA256SUMS.txt').write_text(''.join(f'{sha}  {name}\n' for name,sha in hashes.items()),encoding='utf8')
 with zipfile.ZipFile(folder/'mod-payload.zip') as z:
  manifest=json.loads(z.read('package.json'))
  assert set(z.namelist())==set(manifest['files'])|{'package.json'}
  config=json.loads(z.read('textures.json'));serialized=json.dumps(config)
  assert 'C:\\' not in serialized and 'C:/' not in serialized and 'linn1' not in serialized
  assert all(not n.startswith('originals/') for n in z.namelist())
  assert len(config['textures'])==report['textures_verified']
  for name,info in manifest['files'].items():
   data=z.read(name);assert len(data)==info['size'] and hashlib.sha256(data).hexdigest()==info['sha256']
 archive=ROOT/'release'/f'Full-Throttle-Background-Remaster-{VERSION}-Windows.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
  for name in names+['SHA256SUMS.txt']:z.write(folder/name,name)
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None
 sha=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(f'{sha}  {archive.name}\n')
 print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha),indent=2))

if __name__=='__main__':main()
