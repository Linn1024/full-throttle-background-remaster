# Sky, projector, entrance and funeral repairs

The city sky and projector room retained original RGB in the two-pixel texture filtering gutters. Rebuild those gutters from the shared scene, and extend city cloud coordinate maps into the gutters so border blocks participate in animation. Original geometry and transparency remain unchanged.

The projector's narrow left door now has a readable dark panel and latch. All 18 projector state pieces were rebuilt from the updated artwork. This interprets the reported black-void door as the narrow door in the projector screenshot.

The Corley entrance now uses the detailed closed-door painting and a redrawn open leaf. The open state uses its original geometry, original alpha and runtime Y offset of 148 scene pixels. Unchanged wall and pavement areas sample the shared background rather than carrying the old gray pavement rectangle.

The funeral panorama is rebuilt at 7060 x 1200 from four registered, overlapping detailed paintings. This replaces the former small cropped image stretched across the entire panorama. The three 340-pixel overlaps blend continuously; texture filtering gutters are repaired after packing.

## Reproduction

Generated art remains local under `reviews/seams-v24`; prompts are recorded in `prompts.json` there. Earlier artwork backups are retained there as well.

1. Run `integrate_scenery_v24.py funeral door`.
2. Run `fix_entrance_v24.py`.
3. Run `fix_texture_gutters_v24.py 051-corville`, then `build_cloud_cycles.build(['051-corville'])` from Python. Cloud frames must be rebuilt after any city base changes.
4. Run `live_switcher.py --prepare-only` after all asset changes.

## Verification

Packing assertions verify original alpha and CHNK headers. All 148 city cloud texture-phase combinations pass phase-zero and transparency checks. Packed funeral, room and entrance previews were visually inspected. The helper prepares 594 verified texture pairs.

These checks are offline. The game was not launched; both the game and helper need restarting to load the new manifest and assets. Runtime seams and state transitions still need an in-game check.

Preview files: `funeral-0-packed.png` through `funeral-3-packed.png`, `projector-door-packed.png`, and `entrance-open-packed.png` in `reviews/seams-v24`.
