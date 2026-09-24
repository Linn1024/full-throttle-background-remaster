# Sprite-state repair, 2026-09-24

Built-in imagegen was used for four edits. Project copies:

- `edited/shack-atlas-0-v2.png`: hoist and wreckage states.
- `edited/shack-atlas-1-v2.png`: intact porch/hoist states.
- `edited/gate-open-atlas-v2.png`: open-gate scenery and illuminated pavement.
- `edited/junkgate-cord-removed-v2.png`: removal of the hanging cord from the existing custom wall.

## Prompt set

1. Edit the original square Full Throttle texture atlas in place as a faithful detailed painted remaster. Keep the canvas, every packed sprite rectangle, all edges, positions and sizes. Preserve dark blue-purple night colors, shadows and lighting. Add crisp wood grain and splinter detail to the debris in both large states, worn metal detail to hoist beams, hooks and pipes, and subtle ground texture. No photorealism, new objects, rearrangement, cropping or extra brightness. Leave white control masks and blank areas untouched; preserve transparency and consistency between states.
2. Edit the second square atlas in place, preserving all three sprite states, silhouettes, layout and colors. Add fine wood grain to siding and porch floorboards and worn painted-metal detail to beams, poles, hooks and hoist. Preserve purple-blue night and orange doorway lighting; no redesign, new objects, changed spacing or cropping. Keep blank areas blank.
3. Edit the square open-gate atlas in place, preserving positions, sizes and silhouettes. Add fine stone/concrete detail to cyan-lit pavement and rocks, weathering on the door frame and fencing, and subtle detail on distant ground/buildings. Retain deep purple night and cyan-green doorway illumination. No new objects or changes to perspective, proportions, brightness, masks or blank areas.
4. Remove only the long hanging black cord from the custom wall crop, keeping the top pulley/support and the small lower attachment hole. Fill its footprint with matching existing corrugated metal and cracked concrete. Preserve all other geometry, cracks, bolts, seams, shadows, colors, crop and style. No new objects or light changes.

## Integration

`build_reported_states_v2.py` packs these edits with original compressed alpha blocks and unchanged white mask pixels. It preserves original broad lighting through color matching. Previously mapped custom scenery is retained in the shack atlases. Generated art is stored locally, not referenced from Codex's cache.

For opening the lock, the open-gate pavement is registered into animation atlases a00–a09 with 23–40 feature inliers. The tiny floor fragment in a10 uses an alpha-masked template (normalized error 0.001414 or less). These edits leave Ben and the rotating door intact. The preceding closed-door replacements in a11–a14 remain installed. a15–a16 contain character poses and are retained.

The junkyard cord-removed sprite now replaces the complete wall rectangle with custom scenery; its old smooth blue wall is no longer conditionally preserved. Only the narrow cord footprint uses the generated removal. Original alpha and all unrelated atlas blocks remain unchanged.

Rebuild: run `build_reported_states_v2.py`, then `live_switcher.py --prepare-only`. This builder must run after older dedicated builders, which would otherwise overwrite its output. The generic audited builder skips these versioned manual replacements.

Offline checks: dimensions, BC3 data sizes, original alpha, untouched blocks and protected visible pixels. Packed atlases and scene composites have been inspected. These checks do not establish engine-state correctness. In-game verification is pending user permission to launch. The prerecorded movie remains unchanged.


## Follow-up: moving panels and persistent open state

The subsequent user session log reports 488 catalog entries in custom mode and successful matches for the lock animation atlases a00-a14. Evidence is preserved in `previews/lock-loading-evidence.txt`. This rules out an absent helper in that recorded session; it does not prove visual correctness.

`build_moving_gate_panels.py` now projects the existing approved closed-gate material into the eleven moving door poses. Reference geometry edges are excluded so bars and rivets are not stamped onto a different pose. Original broad shading, ink outlines, alpha and character poses remain protected. Existing ground replacements are retained.

The persistent open-state room atlas a01 also contained old scenery. Its doorway view is now mapped from the updated room atlas a00 using 48 feature inliers. Matching exterior scenery uses the previously audited 49-inlier room registration; the stationary open panel receives the same material detail as the animation.

Rebuild order: `build_reported_states_v2.py`, `build_moving_gate_panels.py`, then `live_switcher.py --prepare-only`. Catalog size remains 488. The new build still requires a fresh helper/game session and visual verification. No game or computer restart was performed for this follow-up.


## Exact padlock-removal patch (screenshot diagnosis)

The latest close-up identifies the small room-state rectangle at atlas a00 (1,1637), size 250x288. It is displayed at room position (1230,720), half scale. Thirty-four independent 24px template patches agreed on that position. This state replaces the padlock with revealed handle/background while Ben's separate animation runs. Previous opening-pose edits did not replace this rectangle from the custom room.

`build_padlock_removed_state.py` now copies the custom closed-door surface into that exact rectangle, retaining the changed padlock-removal footprint. Its outer blocks no longer contain the old door background. Original alpha and revealed-surface pixels are checked; every compressed block outside this rectangle is preserved from the installed atlas. A packed scene close-up is saved at `previews/padlock-removed-fixed.png`.

Run this builder LAST, after both previous builders, then `live_switcher.py --prepare-only`. Catalog count remains 488 because the atlas was already registered. The screenshot-specific repair is offline validated; gameplay confirmation remains pending. No game launch or computer reboot was performed.


## Shared exterior stones

The open-gate atlas had separately generated stones that visibly disagreed with the main background. `build_gate_shared_ground.py` now samples the existing packed custom background in room coordinates for both room overlays and all eleven opening/turning atlases. The first overlay registration is half-scale plus (898,382.5), corroborated by 29 template patches within one vertical pixel. Animation translations reuse their original feature registrations. Only smooth, bounded illumination differences are retained; independently generated exterior stone shapes are removed from these patches.

All non-ground compressed blocks are copied byte-for-byte from the installed textures. Original alpha and protected actor/door pixels are checked. This preserves the padlock-removal fix. The lit area inside the doorway remains separate. The decoded composite `locations/026-gas-gate/custom-v1/shared-ground-open-preview.png` was reviewed; gameplay verification remains pending.

Final rebuild order: state artwork builder, moving-panel builder, padlock-removed builder, shared-ground builder, then `live_switcher.py --prepare-only`. Run the shared-ground builder last among texture builders. Catalog remains 488.
