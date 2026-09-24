# Todd lettering and cloud cycling

Todd's trailer (023): improved the four existing plaque inscriptions with
built-in imagegen, then registered the generated crop at `(620,370,920,650)`.
Only plaque interiors are composited. Surrounding wood, fish and furniture
remain identical to the prior custom art; broad lighting is matched to the dim
reference. `improve_todd_lettering_v9.py` performs registration and compositing.
The reviewed source and final crop are in `reviews/todd-lettering-v9/`.

Generated source: `exec-f31bad7b-e13a-47df-b8d3-89d68de3a5f2.png`.
Prompt: improve only the painted inscriptions on the four small wall signs;
preserve placement, perspective, size, silhouettes, frames, dark exposure and
surrounding art. Preserve ZACH, stylized abc, Todd's with underline, and the
faint top lettering without inventing words. Refine painted letterforms with
restrained wear. No new signs, glow, or brightening.

## Clouds

The classic files contain CYCL palette ranges for 033-ambush, 034-scope,
037-benupsht, 038-ripupsht and 051-corville. The opaque remaster backgrounds
do not encode those indexed-palette cycles. `build_cloud_cycles.py` reads the
original ranges, direction and initial speed from local `ft.la1`, and uses the
indexed background as the phase reference. The format and timing calculation
were checked against [ScummVM's palette implementation](https://github.com/scummvm/scummvm/blob/master/engines/scumm/palette.cpp).

The reconstruction applies softened palette-color differences to the existing
custom cloud art. Original/custom outlines differ, so this is an adaptation,
not pixel-identical classic animation. BC1 blocks are restricted to the cloud
mask; no geometry or alpha changes. Disjoint tracks have independent periods.
Corville's electrical-light range is excluded from this cloud-only change.

Packed sparse frames and animated previews live in `reviews/cloud-cycles-v9/`.
The launcher validates their hashes, sizes, bounds, disjoint ownership and base
texture hashes. Rebuild animation after editing those room backgrounds.

The render-thread helper applies frames only to recently bound cloud textures
in custom mode. F6 restores static official bytes; F7 restarts custom animation.
It uses a real-time clock derived from the original initial cycle speeds;
script-driven speed changes, pause/menu synchronization, and original palette
phase are not hooked. No archive or executable writes are involved.

Verification: packed previews and alpha checks, plus isolated Frida tests of
the real scheduling/compositing/switching JavaScript. Gameplay and runtime
performance in Throttle remain unverified; the game was not launched.

The runtime tests passed 150 animation checks across 15 textures and 28 existing
texture-recognition checks. The actual 32-bit payload cache passed 1,612 loads,
including cloud patches, with a 64 MiB peak and successful eviction/reload and
invalid-hash rejection.

Restart both game and helper to load the new animation catalog.

## Open refrigerator follow-up

The lettering build initially left Todd's existing object atlases stale. Opening
the refrigerator drew older sign/wall pixels over the new room, splitting the
lettering at the state boundary. Both atlases have been refreshed from the
packed room preview. Original alpha, guarded object pixels and untouched blocks
pass equality checks. Open/closed and fridge-only packed composites are produced
by `build_todd_overlays.py`. The lettering integration now rebuilds the room and
its object atlases together, preventing this omitted dependency. Gameplay was
not launched for this follow-up.
