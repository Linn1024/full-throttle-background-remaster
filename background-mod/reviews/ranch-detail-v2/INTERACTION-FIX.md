# Ranch interaction scenery fix

Builder: ../../fix_ranch_interaction_scenery.py

The previous variance/component-filtered registration missed smooth scenery and most parked-bike background rectangles. The new builder addresses both full bike rectangles and both gate rectangles, accepting only pixels agreeing with the original canonical scene and protecting nonmatching foreground. The two pillow CHNK frames were absent from the texture catalog; both are now registered and their matching scenery transferred using their own UV geometry. Pillow pose, wrench, vehicles, and nonmatching gate imagery are retained.

Validated original CHNK headers, decoded alpha, and excluded foreground pixels. Ranch atlas: 21131 changed BC3 blocks. Pillow states: 1016 and 1052 changed blocks. Catalog: 498 texture pairs. Offline compositing reviewed for pillow, bike and gate; no live gameplay verification. Remaining animation-specific imagery may need separate treatment if it appears in game.

Previews:
- ../../locations/131-petes/custom-v1/573-petes-pillow-frame0-layer40-composite.png
- ../../locations/043-ranch/custom-v1/bike1-interaction-composite.png
- ../../locations/043-ranch/custom-v1/gate-interaction-composite.png
