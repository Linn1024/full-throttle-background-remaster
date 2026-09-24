# Cargo briefing overlay restoration

`fix_cargo_overlays_v20.py` updates the scenery overlays in room 073-cargo:

- Two blueprint sheets in room atlas a00, including their stale wall backing.
- Both textures in `386-cargo-pipe-shaft-frame0-layer20.chnk`, which previously
  placed many flat old-wall rectangles around the middle pipe and overhead shaft.

The blueprint atlas registers at scene (670,582), at half atlas resolution.
The pipe chunk has a runtime vertical placement offset of 164 scene pixels;
feature registration against the original wall confirmed this offset. The
offset is used for sampling and previews only; the chunk header and vertices
are unchanged. The two character atlases a01/a02 are not modified, and the
white character silhouette in a00 is preserved exactly.

Built-in imagegen produced the two paintings saved locally at:

- `reviews/cargo-v20/diagrams-generated.png`
- `reviews/cargo-v20/pipe-generated.png`

Prompt set: improve only the two taped purple-gray blueprint sheets, retaining
their exact diagram layout, positions, silhouettes, subdued lighting and schematic
marks; add intentional linework, folds and paper texture. Improve only the long
middle bent pipe, collars and overhead shaft with worn hand-painted metal,
preserving shapes, curves, placement and dim light, and remove the flat wall
patches around them. Keep all other scene objects unchanged.

Integration restores the exact custom wall outside the objects. A single affine
registration retains straight structural lines in the generated material pass.
Reviewed object coverage keeps dark pipe and shaft faces intact even where their
colors match the original wall. Original BC3 alpha bytes and excluded blocks are
copied exactly; decoded comparisons and unchanged chunk headers are asserted.

The decoded scene preview is `reviews/cargo-v20/packed-scene.png` (full size),
with a smaller `packed-preview.png`. Visual checks were offline; no game launch.
Restart both game and helper to replace their cached textures.
