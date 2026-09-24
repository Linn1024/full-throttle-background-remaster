# Minefield object-state ground

`fix_minefield_states_v19.py` fixes the two stale ground rectangles in
`095-minefld_room_pk_a00.dxt`. The crater state registers at scene (1193,720)
and the red/yellow item at (1113,1008), using half-resolution atlas coordinates.
Masked template matching against the official room confirmed both placements.

The replacement reuses the packed custom ground. The original scorch's
brightness attenuation is applied over its new texture. The item, original
BC3 alpha, white interaction masks and unrelated box sprite remain protected.
Packing asserts exact original pixels outside editable blocks and exact alpha.
No new generated painting or changes to scripts/geometry were needed.

Decoded before/after previews:

- `reviews/minefield-v19/crater-before-after.png`
- `reviews/minefield-v19/item-before-after.png`

Verified offline; the game was not launched. Restart both game and helper to
reload the replaced texture rather than the cached version.
