# Save8: Mo's shack debris

Live GPU inspection confirmed that texture IDs 51–54 contained the exact official payloads of `124-debris-image-frame0-layer10/20/30/40.chnk`. These four additional object layers were absent from the replacement catalog even though the three room atlases were already included. Evidence: `previews/save8-old-debris-gpu-evidence.json`.

Built-in imagegen produced four project assets: `edited/debris-layer10-v1.png`, `edited/debris-layer20-v1.png`, `edited/debris-layer30-v1.png`, and `edited/debris-layer40-v1.png`.

Prompt, used separately for each original texture: Edit the square game atlas in place; preserve each UV island's position, size, silhouette, edges, orientation and spacing. Add crisp painted wood grain, splinters, worn metal and modest stone texture inside existing wreckage, hoist and rope fragments. Keep the original Full Throttle painted style, dark blue-violet palette, shadows and orange-lit wood; no photorealism, new pieces, rearrangement, cropping or lettering. Keep empty areas unchanged.

`build_shack_debris_layers.py` packs the generated detail with the original broad lighting. All geometry/header bytes and every BC3 alpha block remain exact; fully transparent blocks are also retained. Outputs are in `locations/018-mo-shack/custom-v1/124-debris-image-frame0-layer*.chnk`. Four entries were added through that folder's `extra-chunk-validation.json`; the catalog now has 492 texture pairs.

The four replacements were applied to the already running game using `apply_debris_running.py`, with original GPU hashes checked before adoption and new hashes checked after upload. `live-switcher/debris-live.log` records four verified adoptions and four successful custom uploads. No game launch or reboot occurred. User visual confirmation is pending.

The temporary attached helper remains until the game closes and supports F6/F7 for these four layers. Future normal launcher sessions include them directly. Rebuild: `build_shack_debris_layers.py`, then `live_switcher.py --prepare-only`. This is independent of the gate/ground builders.

## Follow-up: shared ground and porch support

`fix_shack_shared_scenery.py` maps matching background pixels into all four debris layers and all three room atlases, retaining the generated debris wherever the original state differs from the static scene. This removes independently generated ground texture from matching scenery. A previously missed lower porch/support island in atlas a02 maps to room coordinates with half scale plus (1389.16,123.64). Compressed alpha and geometry remain unchanged. The shared-scenery report and offline composite are in the room's custom-v1 folder.

Run this repair after the debris and room-atlas builders, before preparing the catalog. Backups ending `.before-shared` preserve the preceding custom assets. The follow-up is built and checked offline; restart the game/helper to replace their cached versions. It has not been applied to the current running session, and visual confirmation in save8 is pending.
