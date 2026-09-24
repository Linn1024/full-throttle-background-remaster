"""Check every packed cloud phase and measure visible change against v9."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scene_assets import ROOT,read_chunk
from build_cloud_cycles import OUT

def measure(entry):
    room,stem,number=entry['name'].split('/')
    tex=read_chunk(ROOT/'locations'/room/'custom-v1'/(stem+'.chnk'))['textures'][int(number[7:])]
    base=np.array(tex['image']);peak=np.zeros(base.shape[:2],np.uint8)
    codec=(1,'DXT1') if tex['format']==b'DXT1' else (3,'DXT5')
    count=0
    for track in entry['tracks']:
        for step,frame in enumerate(track['frames']):
            patch=Path(frame['path']).read_bytes();raw=bytearray(tex['raw']);cursor=0
            for at,length in track['runs']:
                raw[at:at+length]=patch[cursor:cursor+length];cursor+=length
            assert cursor==len(patch)
            if step==0:assert raw==tex['raw'], 'Phase zero differs from custom base'
            decoded=np.array(Image.frombytes('RGBA',tex['image'].size,bytes(raw),'bcn',codec))
            assert np.array_equal(decoded[:,:,3],base[:,:,3]), 'Cloud phase changes transparency'
            diff=np.max(np.abs(decoded[:,:,:3].astype(np.int16)-base[:,:,:3]),axis=2).astype('uint8')
            peak=np.maximum(peak,diff);count+=1
    assert (peak>8).sum()>20, 'No visible cloud cycle'
    return peak,count

def main():
    entries=json.loads((OUT/'manifest.json').read_text())
    previous={e['name']:e for e in json.loads((ROOT/'reviews/cloud-cycles-v9/manifest.json').read_text())}
    reports=[];count=0
    for e in entries:
        peak,n=measure(e);count+=n;mask=peak>0
        report=dict(name=e['name'],frames=n,animated_pixels=int(mask.sum()),mean_peak_change=float(peak[mask].mean()))
        if e['name'] in previous:
            old,_=measure(previous[e['name']]);common=(old>0)&mask
            report['previous_mean_on_common_pixels']=float(old[common].mean())
            report['new_mean_on_common_pixels']=float(peak[common].mean())
            report['visibility_ratio']=report['new_mean_on_common_pixels']/report['previous_mean_on_common_pixels']
            assert report['visibility_ratio']>1.4, report
        reports.append(report)
    rooms={e['name'].split('/')[0] for e in entries}
    assert '031-reststop' in rooms and '032-mensroom' in rooms
    result=dict(frames_checked=count,rooms=sorted(rooms),all_alpha_preserved=True,textures=reports)
    (OUT/'asset-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    ratios=[r['visibility_ratio'] for r in reports if 'visibility_ratio' in r]
    print(f'{count} frames checked; {len(rooms)} rooms; visibility ratios {min(ratios):.2f}–{max(ratios):.2f}; all alpha preserved.')

if __name__=='__main__':main()
