# Static scenery corrections, 24 September 2026

This pass addresses the ten annotated screenshots: small scenery objects should
match the painted backgrounds, including alternate object states. Original
texture dimensions, mesh geometry and alpha are retained.

| Screenshot | Room | Change |
| --- | --- | --- |
| 1 | 010 dumpster | Redraw the small CVIA label; retain the main shop sign. |
| 2 | 007 bar | Redraw both bottle shelves with glass, cap and paper detail. |
| 3 | 017 Mo shop | Remove protection around the left controls and rebuild the scenery-bearing bike atlases. |
| 4 | 018 Mo shack | Register overlapping porch scenery to the same background and refine the porch atlas. |
| 5 | 025 Todd shop | Dim the room using the official lighting as reference; refresh its scenery atlas. |
| 6 | 019 Mo bench | Replace the large rectangular bike guard with a tight silhouette, allowing new rug detail to reach the bike. |
| 7 | 026 gas gate | Redraw the two warning plates, preserving their symbols. |
| 8 | 027 junkgate | Redraw TODD'S, JUNK-YARD and ENTRANCE with the original wording and perspective. |
| 9 | 032 men's room | Redraw the open doorway, graffiti, frame and threshold. |
| 10 | 018 Mo shack | Refine the broken-state debris from the original composite and repack all four debris layers. |

## Raster provenance

Generated with the imagegen skill and built-in image generator, using existing
scene crops or original state composites as image-edit references. Local inputs
and outputs are in `reviews/static-sprites-v3/`; large game assets and generated
images are intentionally excluded from this source repository.

Generated files under the session image directory
`01a0cd70-1192-7f73-919f-7322a0c4973c`:

| Local input to integration | Generator output |
| --- | --- |
| label-generated.png | exec-fa2da458-04a7-468a-80c8-b08e940a40fb.png |
| bottles-generated.png | exec-55c473a7-68c6-484b-b7d4-655ad93fd5ae.png |
| signs-generated.png | exec-511315f6-64d2-40bc-a9b0-f3a2f51cdd6c.png |
| lettering-generated.png | exec-707938fc-5f3e-4a37-ba68-75381ed7b909.png |
| exit-generated.png | exec-621abd07-16eb-4680-b788-a2a4d360e439.png |
| dimmer-generated.png | exec-36b4e930-499b-4813-b427-a7b9adc0fe9f.png |
| shack-broken-generated.png | exec-00828084-4ed4-4d6b-bc83-1f6c3acf7f67.png |
| shack-porch-generated.png | exec-7981aa5c-bfc9-44c6-a7a5-0f86d0f39b1c.png |

Prompt requirements, summarized:

- Label: exact CVIA text and bullet lines, same perspective and grey/olive palette,
  subtle painted material detail, no additional margins.
- Bottles: retain shapes, positions and colors; refine glass edges, reflections,
  caps and labels. Preserve dark lighting; invent no brands or text.
- Warning plates: identical lightning and geometric symbols, same placement,
  restrained bevels and bolts, dark purple night lighting.
- Junkyard lettering: exact wording, original type and perspective, subtle raised
  shadows; retain dark blue/purple exposure.
- Doorway: identical angle, silhouette and graffiti; refine painted metal,
  hinges and concrete threshold without additional grime.
- Todd shop: use the original room as a lighting reference, reduce ambient
  brightness while retaining localized lamp and workbench illumination.
- Broken shack: use the original composite, preserve board/beam/rope silhouettes
  and positions, subtle wood grain, no invented debris or duplicate ropes.
- Porch: use the original atlas, preserve state placement and silhouettes,
  refine painted wood and metal while retaining night exposure.

## Rebuild order

Requires the local `before-static-v3` backups and generated inputs above.

1. Run `integrate_static_details_v3.py`.
2. Rebuild backgrounds with `build_custom.build` for root 010 and rooms 007,
   017, 025, 026, 027 and 032.
3. Run `build_workshop_overlays.py` and `build_bench_object_layers.py`.
4. Run `fix_shack_states_v3.py`.
5. Run `build_audited_overlays` scoped to `025-toddshop`, using a copied
   registration report in `reviews/static-sprites-v3/overlay-audit`.
6. Run `live_switcher.py --prepare-only` to refresh the offline cache.

Do not run unrelated global state builders afterward: they can overwrite
previously reviewed moving-gate and alternate-state work.

## Validation and limits

Background builds checked geometry, alpha and remaining protected pixels.
Object builders checked original alpha and protected foreground pixels;
extra CHNK headers remain identical. The bench check also composites the
unchanged layer 20 over the corrected layer 10 at its registered position.
Packed crop previews, raised-porch and broken-shack composites were inspected.
Todd's two registered atlas regions were refreshed after dimming.

Review artifacts include `packed-details.jpg`, `bench-both.png`,
`porch-check.png`, and
`locations/018-mo-shack/custom-v1/broken-state-v3-preview.png`.

These are offline checks, not a gameplay verification of every animation state.
The game was not launched. Restart the game and switching helper to load the
refreshed cache; an existing helper does not reload its cache with F7.
