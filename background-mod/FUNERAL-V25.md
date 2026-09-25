# Funeral detail corrections

Four local edits to the existing 7060 x 1200 funeral panorama:

- Repaired the female statue's cross-holding hand and face.
- Restored the male bust's narrow pointed chin beard, using the original game art as reference.
- Removed the suspended plaque behind the small urn, continuing the dark foliage.
- Removed plants, moss, lichen, large cracks and chipped weathering from the new foreground coffin. Its stone material, dimensions, stepped lid and recessed panels remain.

Built-in image generation supplied the four edits. Inputs, outputs, original artwork reference and `prompts.json` are stored in `reviews/funeral-v25`. `before.png` preserves the prior full panorama. `fix_funeral_details_v25.py` registers and composites the edits, then packs both room layers and repairs texture filtering gutters.

Checks: unchanged source pixels outside edit masks are asserted identical; packing preserves original alpha and geometry. Composited and packed crops are available as `*-composited.png` and `*-packed.png`. Verification is offline; the game was not launched. Restart both the game and helper to load the update.

Rebuild: run `fix_funeral_details_v25.py`, then `live_switcher.py --prepare-only`. Running the earlier v24 funeral generator replaces this source; rerun v25 afterward to restore these corrections.
