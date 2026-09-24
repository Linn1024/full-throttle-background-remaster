# Screenshot follow-up

Latest ground correction: both open-gate room overlays and eleven animation atlases now sample the main background stones. The separate generated ground has been removed from the exterior patches. Builder: `build_gate_shared_ground.py`; run after other gate builders.

Latest: the exact padlock-removed handle overlay has now been identified and rebuilt by `build_padlock_removed_state.py`. See the final section of [build notes](STATE-ART-V2.md). Earlier moving-panel work did not address this state.

**2026-09-24 update:** The prior partial fixes below were insufficient in gameplay. V2 now includes dedicated hoist/debris material artwork, open-gate pavement transferred into all eleven opening/turning atlases a00-a10, and the complete custom cord-removed wall patch. The four closed-door replacements remain. Catalog: 488 pairs. [Build details and limitations](STATE-ART-V2.md). Gameplay verification is still pending.

## Previous pass, 2026-09-23

These are offline-validated changes, not confirmed gameplay fixes. No game was launched.

1. **Mo's shack right-side overlays:** expanded transfers into the smooth scenery in three room atlases. Previously only textured patches were eligible. Different hoist/bike states retain their foreground objects. Some unmatched state scenery can remain official.
2. **Picking the gas-gate lock:** found scenery baked into the character animation itself. Added four registered closed-door atlases, a11–a14 of 103-pick-lock-cos. Alpha and untouched blocks remain identical. Moving/open-door frames a00–a10 are not fixed: their geometry does not register reliably against the closed static background.
3. **Junkyard blue stripe:** corrected BC3 boundary handling and static wall edge strips in the cord-removed room sprite. The two rope costumes were inspected: predominantly transparent character/rope animation. The reported climbing state still needs an in-game check; the cord-removed preview alone cannot establish that this is the same stripe.
4. **Workshop reverse view:** added object CHNK layer10 (two textures), previously missed by the DXT-only scan. Its local coordinates require +310 scene pixels on X. Replaced matching scenery while preserving alpha, geometry, and a conservative motorcycle guard. Layer20 and the bike/ropes remain official foreground art. This does not remaster the entire bike sprite.
5. **Scripted exterior scene:** identified videohd/mwc.ogv through EN/VIDEO/MWC.TRS dialogue and decoded preview. It is a 1920×1080 prerecorded movie, 255 frames at 10 fps. Its old scenery is baked into the video. Movie replacement is not implemented; the compressed-texture switcher does not handle these frames.

Catalog: 477 verified texture pairs. Restart both the game and helper using `Play with background switcher.cmd` to load the catalog. F7 selects custom; F6 selects official. Do not launch the game autonomously: the user explicitly requested permission first.

Rebuild scripts: `build_audited_overlays.py`, `build_bench_object_layers.py`, `build_lock_animation.py`, `build_junkgate_overlay.py`, `review_audited_overlays.py`, then `live_switcher.py --prepare-only`.

Further work: validate reported states in-game; register moving door art against per-state references; identify any remaining rope-state seam; build and integrate a separate movie replacement pipeline. Background coverage does not imply complete animation or movie coverage.
