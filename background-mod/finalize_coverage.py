"""Document the completed static-background pass from validated build outputs."""
import json, re
from pathlib import Path
root = Path(__file__).parent
config = json.loads((root/'live-switcher/textures.json').read_text())
rooms = config['rooms']; count = len(rooms); pairs = len(config['textures'])
retained = {
 '001-logo':'Blank background behind title graphics.',
 '013-roadrsh':'Blank background for the road combat renderer.',
 '082-bprint-1':'Readable blueprint text and diagrams retained.',
 '083-bprint-2':'Readable blueprint text and diagrams retained.',
 '089-cu-photo':'Photograph, character artwork and inscription retained.',
 '093-vult-gun':'Flat color backing for animation retained.',
 '102-cu-ben-l':'Ben portrait with simple sky retained as character artwork.',
 '105-cu-mo-sr':'Maureen portrait retained as character artwork.',
 '132-cu-hand':'Hand close-up retained as character artwork.',
 '168-copyrite':'Official ending card and Thanks for Playing lettering retained.'
}
folders = sorted(p.parent.name for p in (root/'locations').glob('*/room.json'))
assert set(folders) <= set(rooms)|set(retained)|{'1007-bar'}
assert count == 106
for r in rooms:
 p = root/'custom-v1/validation.json' if r=='010-dumpster' else root/'locations'/r/'custom-v1/validation.json'
 report=json.loads(p.read_text())
 if isinstance(report,dict): assert report['protected_pixels_identical']
 for t in (report['textures'] if isinstance(report,dict) else report):
  assert t['alpha_preserved'] and t['protected_text_blocks_preserved']
lines=['# Background coverage', '', f'{count} custom background views are built, plus the duplicate bar room 1007-bar, which uses the same seven texture payloads as 007-bar. The switcher contains {pairs} texture pairs, including five scenery overlay textures.', '', 'The static scenic background pass reaches the ending. Ten blank, character, blueprint, photograph or ending-card assets intentionally retain official artwork. Animated object-state atlases are a separate remaining integration pass; some can cover custom scenery. No game was launched for this pass, and full playthrough validation remains pending.', '', '| Room | Status | Preview |', '| --- | --- | --- |']
for r in sorted(set(rooms)|set(folders)):
 if r in retained: status=retained[r]; preview=f'locations/{r}/official-remaster.png'
 elif r=='1007-bar': status='Covered by identical 007-bar texture hashes.';preview='locations/007-bar/custom-v1/in-game-texture-preview.png'
 else: status='Custom static background; asset checks passed.';preview='custom-v1/in-game-texture-preview.png' if r=='010-dumpster' else f'locations/{r}/custom-v1/in-game-texture-preview.png'
 lines.append(f'| {r} | {status} | [Preview]({preview}) |')
(root/'COVERAGE.md').write_text('\n'.join(lines)+'\n')
p=root/'locations/README.md';s=p.read_text();rows=[]
for r in rooms:
 if r=='010-dumpster' or f']({r}/custom-v1/' in s:continue
 rows.append(f'| {r} | [Preview]({r}/custom-v1/in-game-texture-preview.png) | [Prompt]({r}/prompt-v1.txt) |')
table_end=s.index('\n\n',s.index('| ---'))
s=s[:table_end]+'\n'+'\n'.join(rows)+s[table_end:]
s=re.sub(r'forty-eight|Forty-eight',str(count),s);s=s.replace('208',str(pairs)).replace('205',str(pairs-5)).replace('The latest batch covers','An earlier batch covers')
s+='\nThe complete static-background pass now covers '+str(count)+' custom views through the ending, plus the duplicate bar alias. See [full coverage and deliberate exclusions](../COVERAGE.md). All packaged previews were reviewed. Original masks and protected regions passed build checks. New animated object states remain official, and gameplay testing is pending.\n'
p.write_text(s)
p=root/'LIVE-SWITCHER.md';s=p.read_text();a=s.index('Forty-eight background views');b=s.index(' Characters,',a)
s=s[:a]+f'{count} custom background views are supported through the ending, plus the duplicate bar room. See [complete coverage](COVERAGE.md) and [previews and prompts](locations/README.md).'+s[b:]
s=s.replace('208 texture pairs',f'{pairs} texture pairs');p.write_text(s)
p=root/'README.md';s=p.read_text();a=s.index('**Additional locations:**');b=s.index('\n\n',a)
s=s[:a]+f'**Background pass complete:** {count} custom static views through the ending, plus the duplicate bar room, are packaged for F6/F7 switching. See [coverage](COVERAGE.md) and [previews and prompts](locations/README.md). Launch with **Play with background switcher.cmd** in the game directory. Asset checks passed; gameplay checks and remaining animated scenery overlays are still pending. No game was launched.'+s[b:];p.write_text(s)
print(f'Documented {count} views, {pairs} pairs, 10 retained assets and 1 alias.')
