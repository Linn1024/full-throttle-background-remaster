# Full Throttle background remaster

Source and working notes for a custom background-remaster project for Full Throttle Remastered on Windows. Artwork aims to retain the original composition, palette, lighting and painted style while adding fine material detail. Official lettering and selected foreground objects are preserved during packing.

## Repository contents

- `background-mod/scene_assets.py`: CHNK/DXT decoding and scene rendering.
- `background-mod/build_custom.py`: map artwork onto original layer geometry, preserving alpha and protected rectangles or silhouettes.
- `background-mod/live_switcher.py` and `.js`: Frida-based F6/F7 texture switching, with a bounded texture cache.
- Scene-specific builders and interaction-scenery fixes.
- Room configurations, artwork prompts, registration data and project notes.

The game executable/archive, extracted original artwork, generated replacement artwork, packed textures, tools, virtual environments, saves and runtime logs are deliberately excluded. This is a source repository, **not a ready-to-play mod distribution**. Cloning it alone cannot reproduce the current artwork or launch the complete custom mod. Existing documentation may link to images and local review artifacts absent from this repository.

## Local setup

Use a legally obtained Windows installation of the game. This checkout's `background-mod` folder is expected beside `Throttle.exe` and `full.data`.

1. Create a Python 3.12 environment at `background-mod/tools/nutcracker-py312` and install `background-mod/requirements.txt`.
2. Supply Microsoft DirectXTex `texconv.exe` at `background-mod/tools/texconv.exe`.
3. Supply/extract the appropriate original room and costume assets under `background-mod/original`. `prepare_rooms.py` extracts and renders its selected room list from the local archive; it is not a complete project bootstrap.
4. Supply the generated artwork and existing scene configurations. Each room builder expects `locations/<room>/custom-remaster-v1.png`. Scene-specific builders may require additional local generated state art.
5. From `background-mod`, run `tools/nutcracker-py312/Scripts/python.exe build_custom.py --room <room>` for the chosen room, then the applicable interaction builders.
6. Run `tools/nutcracker-py312/Scripts/python.exe live_switcher.py --prepare-only` to validate and prepare the texture catalog without starting the game.
7. When ready to play, close existing game instances and run `Play with background switcher.cmd`. F6 selects official remastered textures; F7 selects custom textures. The game's classic toggle remains available.

Keep backups of local art and generated assets separately. Do not run all builders indiscriminately: some older builders overwrite newer state fixes. For gas-gate rebuild order, use `build_reported_states_v2.py`, `build_moving_gate_panels.py`, `build_padlock_removed_state.py`, then `build_gate_shared_ground.py` before preparing the catalog.

## Validation and limitations

The current local catalog contains 594 texture pairs. Builders check geometry, alpha and protected pixels; these checks do not establish visual correctness in every animation or save state. Some interactions still need gameplay review. The reported gas-tower cutscene freeze prompted a cache fix, but its in-game resolution remains unconfirmed.

## Installable release

The separate Windows beta package includes a self-contained installer and launcher. Players do not need Python or the development files. See [player instructions](background-mod/RELEASE-README.md), [release build and validation](background-mod/RELEASE-BUILD.md), and [Mod DB listing text](background-mod/MODDB-DESCRIPTION.md). Release binaries and artwork remain outside this source-only repository.

Legacy archive-patching commands are retained for history; the normal workflow is the live switcher. The switcher does not write to the game executable or archive. Launching it without `--prepare-only` starts the game.

Artwork creation used built-in imagegen. Prompts and provenance are stored with scene notes and under `background-mod/reviews`. Original game assets remain the property of their respective owners; this repository does not include them or grant rights to them.
