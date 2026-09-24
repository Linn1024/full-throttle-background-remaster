# Projector room scenery states

Room `066-projectr` had detailed static art covered by old object textures.
The room's paper-protection rectangles also restored the original paper sheets
over their existing improved artwork.

`fix_projector_v23.py` now packs all 18 scenery states across its three atlases:
seven reel/film animation frames, six lever positions, the door overlay, and
four dark/blue window states. Built-in image generation supplied the reel and
lever material redraws. Unchanged cabinet, wall, pipe and floor areas share the
packed custom background. The paper overrides are removed so the existing
improved sheets and scroll are visible.

Reel frames use constrained feature registration and a fixed moving-object
mask. Each lever is composited into its original state silhouette; the cabinet
and slots remain shared across all positions. White control masks, atlas
dimensions, CHNK geometry and original BC3 alpha are preserved. No character
art or interaction definitions are modified.

Offline review includes all seven reel frames, all six lever positions and
the four window states. Packing verifies original alpha and excluded pixels.
Helper payload hashes are checked against the final packed atlases. Gameplay
and animation timing have not been tested in the running game.

## Local artifacts

- `reviews/projector-v23/room-packed.png`: room with packed sprites.
- `reviews/projector-v23/reels-packed.gif`: offline reel animation preview.
- `reviews/projector-v23/levers-packed.png`: all control positions.
- `reviews/projector-v23/reels-generated.png` and `levers-generated.png`: source artwork.
- `reviews/projector-v23/prompts.json`: built-in image generation prompts.

Restart both the game and helper after installation. Do not run the old
conservative overlay builder over these replacement atlases.
