# Ground beneath Mo's shack debris

The generated broken-state artwork still contained ground painted in the old
palette. These opaque ground patches covered the detailed custom terrain.

`fix_debris_ground_v12.py` registers the current packed room ground into matching
static scenery below scene y=820 in the four debris CHNK layers and the two
registered broken-state regions in atlas a00. It compares the original state
with the original room to exclude debris and state-specific shadows. Entire
BC3 blocks touching visible excluded pixels remain byte-identical, and only
color bytes in eligible blocks change. This is compositing existing terrain;
no new painting or image generation was used.

The repair starts from fresh v12 backups of the current assets, not older
shared-scenery backups. It never rewrites a01 or a02: their complete file hashes
are checked before and after, preserving the later porch seam/coverage fixes.
The four CHNK geometry headers and every alpha pixel remain identical. Excluded
foreground pixels are checked against the preceding custom version.

Validation: 11,089 eligible blocks refreshed in a00 and 8,060 across the four
debris layers. Before/after packed composites, closeups, backups and a JSON
report are in `reviews/debris-ground-v12/`. These are offline checks; gameplay
was not launched. Run this repair after rebuilding broken-state/debris art and
before `live_switcher.py --prepare-only`. Restart game and helper to load it.
