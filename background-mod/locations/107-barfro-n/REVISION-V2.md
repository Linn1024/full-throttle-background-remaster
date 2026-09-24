# Night truck detail and grille revision

The previous custom scene visibly simplified the original truck's speckled wear. The replacement uses the official scene as the geometry/lighting target and the user-approved daytime dumpster as the material-detail benchmark. Built-in imagegen produced `custom-remaster-v1.png`; the previous version is retained as `custom-remaster-before-v2.png`.

Background prompt: Preserve exact composition, proportions, outlines, night palette, lighting, signs, truck design and closed grille. Keep all original speckling, stains, chips and scuffs; enrich with fine painted pitting, scratches, rust, worn edges, gritty ground, wood grain and weathered rock. Match the approved dumpster's material richness. No smoothing, new objects, photorealism, characters or UI.

The open engine bay is `107-barfro-n_room_pk_a00.dxt`. The raised/moving grille is in the two `345-truck-hood-cos` atlases, previously absent from the catalog. Generated state artwork is saved at `../../edited/truck-engine-v2.png`, `../../edited/truck-hood00-v2.png`, and `../../edited/truck-hood01-v2.png`.

State prompt: Edit each atlas in place with fine painted weathered metal, pitting, paint chips, scratches and restrained rust, retaining original wear, dark palette, grille bars, fan geometry, every packed sprite's layout and blank space. No rearranging or new parts. The wide last-pose output had extra padding; its visible component was registered to the original alpha bounds during packing.

`build_custom.py --room 107-barfro-n` packs the main scene and verifies protected sign pixels. `build_truck_night_v2.py` packs the three state atlases with exact original BC3 alpha. Matching engine-patch bodywork samples the new background to reduce seams; original broad lighting and teal grille paint are retained. Character animation atlases are unchanged.

Catalog preparation validates 494 texture pairs, including both newly added grille atlases. Packed output was visually inspected offline. This revision has not been tested in the running game; restart the helper/game to load it. No game launch was performed.
