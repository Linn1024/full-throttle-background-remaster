# Funeral color grade

The funeral panorama now has lower brightness, restrained orange/gold highlights and cooler violet stone/shadow tones, closer to the original game. Mean source-image luminance falls from 53.90 to 36.43 (about 32%). The original is a lighting reference, not replacement artwork.

Built-in imagegen produced a grading reference; `reviews/funeral-v26/prompts.json` records the prompt. `grade_funeral_v26.py` registers that reference for color sampling (888 inliers) and fits one global RGB transform. The transform is blended at 75% strength onto the untouched 7060 x 1200 source. No generated geometry or texture replaces the existing detail, so the v25 hand, face, beard, removed plaque and clean coffin remain intact.

Files in `reviews/funeral-v26`: `before.png` (backup), `grade-reference.png`, `validation.json`, `packed-panorama.png`, and `graded-detail.png`. Both scene layers are repacked, retaining original alpha and geometry, then their filtering gutters are repaired.

Rebuild with `grade_funeral_v26.py`, then `live_switcher.py --prepare-only`. Run this after v25 if rebuilding earlier artwork. Checks are offline; no game launch. Restart both game and helper for verification.
