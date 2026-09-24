"""Extract original remastered room resources and render their static layers."""
import json
import struct
from pathlib import Path
from PIL import Image
from scene_assets import ROOT, read_chunk, render

ROOMS = ['005-bar-road','006-barfront','007-bar']

def main(rooms=ROOMS):
    with (ROOT.parent/'full.data').open('rb') as f:
        h=struct.unpack('<4s11I',f.read(48)); f.seek(h[4]); names=f.read(h[8]).split(b'\0')
        for room in rooms:
            out=ROOT/'locations'/room;out.mkdir(parents=True,exist_ok=True)
            entries=[]
            for i,n in enumerate(names[:h[7]//24]):
                name=n.decode()
                if not name.startswith(f'rooms/{room}/'):continue
                f.seek(h[2]+i*24);offset,np,size,size2,flags=struct.unpack('<Q4I',f.read(24))
                assert size==size2 and flags==0
                f.seek(h[5]+offset);data=f.read(size)
                target=ROOT/'original'/name;target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert target.read_bytes()==data
                else:target.write_bytes(data)
                entries.append(dict(name=name,offset=h[5]+offset,size=size,size2=size2,flags=flags,entry_offset=h[2]+i*24))
            (out/'manifest.json').write_text(json.dumps(entries,indent=2))
            folder=ROOT/'original/rooms'/room
            data=(folder/f'{room}.room.xml').read_bytes()
            width,height=struct.unpack_from('<ff',data,16)
            size=(round(width/2),round(height/2))
            layers=sorted(folder.glob(f'{room}-layer*.chnk'),key=lambda p:int(p.stem.rsplit('layer',1)[1]))
            image=Image.new('RGBA',size)
            for p in layers:
                layer=render(read_chunk(p),size)
                layer.save(out/(p.stem+'.png'))
                image=Image.alpha_composite(image,layer)
            image.convert('RGB').save(out/'official-remaster.png')
            number=int(room[:3])
            classic=ROOT/f'classic/ft/IMAGES/backgrounds/LECF_0001_LFLF_{number:04d}_ROOM_RMIM_IM00.png'
            if classic.exists():(out/'original-1995.png').write_bytes(classic.read_bytes())
            config=dict(room=room,size=size,layers=[p.name for p in layers],protected=[])
            if (out/'room.json').exists():
                previous=json.loads((out/'room.json').read_text())
                config['protected']=previous.get('protected',[])
                if 'artwork_crop' in previous:
                    config['artwork_crop']=previous['artwork_crop']
            (out/'room.json').write_text(json.dumps(config,indent=2))
            print(room,size,[p.name for p in layers], 'classic reference:',classic.exists())

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rooms',nargs='*')
    main(parser.parse_args().rooms or ROOMS)
