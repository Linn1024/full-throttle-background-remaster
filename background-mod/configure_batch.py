"""Persist generation prompts and original-art protection rectangles for a batch."""
import json, sys
from pathlib import Path
root = Path(__file__).parent
for d in json.loads((root / sys.argv[1]).read_text()):
    p = root / 'locations' / d['r']
    (p / 'prompt-v1.txt').write_text(d['prompt'] + '\n')
    f = p / 'room.json'
    c = json.loads(f.read_text())
    c['protected'] = d.get('p', [])
    f.write_text(json.dumps(c, indent=2) + '\n')
