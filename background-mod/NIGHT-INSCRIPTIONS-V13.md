# Night inscriptions v13

The night dumpster room (116-dumpst-n) now reuses the approved daytime dumpster label and General Surplus sign faces. `fix_night_inscriptions_v13.py` composites the existing v8 artwork through the same inward-feathered silhouette masks; it does not generate new lettering or paste rectangular backgrounds.

The color conversion fits the official day-to-night sign luminance relationship separately for each sign, preserving the subdued blue-violet nighttime exposure. Before removing the two official-lettering protection regions, the script reconstructs their previous 40-pixel surrounding blend into the source. Pixels outside the sign masks are verified identical to that reconstructed baseline.

Rebuilt both room layers and visually reviewed decoded packed sign crops in `reviews/night-signs-v13/packed.png`. All four packed textures retain original alpha. The night a00 state atlas contains the dumpster lid/right side, not either inscription, and was left unchanged. No other room or porch assets were rebuilt.

Run with the bundled Python: `fix_night_inscriptions_v13.py`, followed by `live_switcher.py --prepare-only`. Restart both game and helper to load updated cached textures. No game was launched; in-game verification remains pending.
