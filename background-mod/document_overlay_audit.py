"""Write coverage from actual audit/build outputs, without claiming gameplay QA."""
import json
from scene_assets import ROOT

def main():
 audit=ROOT/'overlay-audit';rows=json.loads((audit/'registration.json').read_text())
 built={r['file']:r for r in json.loads((audit/'built.json').read_text())}
 held={'010-dumpster':'Characters overlap scenery; needs explicit foreground guards.',
 '043-ranch':'Door and vehicle states need individual guards.',
 '054-souvenir':'Small sign/item patches; no sufficiently large eligible region.',
 '056-arena':'Repeated door patterns give ambiguous registrations.',
 '066-projectr':'Moving reels overlap matching stationary pixels; needs explicit guards.',
 '099-behind-t':'Moving truck panels require state-specific masks.',
 '123-cargofnt':'Characters and dashboard require state-specific masks.',
 '007-bar':'Small bar/key patches not registered confidently.',
 '1007-bar':'Alias of bar; small bar/key patches not registered confidently.',
 '028-magnet':'Button light states; no confident registration.',
 '041-roadblck':'Lighting overlay differs from static reference.',
 '049-caveturn':'Bike/ground patches; no confident registration.',
 '057-demowall':'Small door fragment; no confident registration.',
 '060-big-door':'Light/window states; no confident registration.',
 '062-office':'Small door fragments; no confident registration.',
 '064-corridor':'Door/indicator states; no confident registration.',
 '065-media-rm':'Door and photograph; no confident registration.',
 '091-junkyard':'Small scenery/state fragments; no confident registration.',
 '095-minefld':'Crater/ground state differs from static reference.'}
 lines=['# Object scenery audit','',
 'All 87 room DXT atlases in full.data were inventoried; none are missing locally. All were reviewed in contact sheets. Feature registration found candidates in 41 atlases. A match is not by itself approval to edit a foreground object.', '',
 f'{len(built)} additional atlases across {len(set(r["room"] for r in built.values()))} rooms have conservative scenery transfers. Five existing manually integrated atlases remain in place. The switcher now contains 488 pairs (450 background textures, 21 room object atlases, 15 lock-animation atlases, and two bench object-layer textures).', '',
 'Validation: packed BC3 alpha is identical; excluded visible pixels and untouched blocks are identical. The Kick Stand ground-restoration patch is explicitly mapped in full. Other transfers replace confidently matched textured scenery; smooth or ambiguous patches can remain official. This is partial overlay coverage, not a completed playthrough or a guarantee that every seam is gone.', '',
 '29 scene composites and 16 original/custom atlas comparisons were generated and reviewed. Scene composites use inferred registration and connected alpha components, not engine sprite geometry: connected neighbouring frames (notably crakwall) can appear together in a diagnostic preview. No game was launched.', '',
 '| Atlas | Result |','| --- | --- |']
 for r in rows:
  name=r['file'];room=r['room'];p=ROOT/'locations'/room/'custom-v1/overlay-validation.json'
  reports=json.loads(p.read_text()) if p.exists() else []
  if name in built:status=f'Conservative scenery transfer built; {built[name]["changed_blocks"]} blocks. Gameplay pending.'
  elif any(x['file']==name for x in reports):status='Existing manual scenery integration retained.'
  elif room in held:status='Needs further work: '+held[room]
  else:status='Retained: foreground, mask, text, or state artwork; no verified scenery replacement.'
  lines.append(f'| {name} | {status} |')
 lines+=['','Rebuild: `audit_object_scenery.py`, `build_audited_overlays.py`, `review_audited_overlays.py`, then `live_switcher.py --prepare-only`. The build script preserves existing dedicated replacements.','',
 'Evidence: [registrations](registration.json), [build checks](built.json), [composite index](composites.json).']
 (audit/'README.md').write_text('\n'.join(lines)+'\n')
 for name in ('COVERAGE.md','LIVE-SWITCHER.md','locations/README.md'):
  p=ROOT/name;s=p.read_text().replace('455 texture pairs','488 texture pairs').replace('471 texture pairs','488 texture pairs').replace('five scenery overlay textures','21 scenery overlay textures').replace('three object overlay atlases','21 object overlay atlases')
  link='../overlay-audit/README.md' if name.startswith('locations/') else 'overlay-audit/README.md'
  note=f'\nObject scenery audit: 87 atlases inspected; 16 additional conservative scenery transfers built and checked. Coverage is partial; unresolved states and review evidence are listed in the [audit report]({link}). Restart the game and helper to load the updated catalog. Gameplay verification is pending.\n'
  if 'Object scenery audit: 87' not in s:s+=note
  p.write_text(s)
 print(len(built),'additional atlases documented')

if __name__=='__main__':main()
