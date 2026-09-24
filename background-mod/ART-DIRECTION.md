# Background remaster art direction

User-approved direction: preserve the original game's composition, shapes, lighting and colors closely; add crisp material detail matching its original painted style; retain lettering exactly as in the official remaster. Do not introduce another artistic style. Avoid the official remaster's smeared or overly smooth surfaces. Use the original game art as the primary style reference for every location.

## Dumpster scene, version 1

- Original reference extracted from the user's game: `classic/ft/IMAGES/backgrounds/LECF_0001_LFLF_0010_ROOM_RMIM_IM00.png`.
- Official remaster reconstructed from native meshes and textures: `scene/official-remaster.png`.
- Generated artwork: `scene/custom-remaster-v1.png` (built-in imagegen).
- Exact generation prompt: `scene/prompt-v1.txt`.
- Preview rendered from the actual packaged textures: `custom-v1/in-game-texture-preview.png`.
- Texture validation record: `custom-v1/validation.json`.

The first draft adds weathered metal, wood grain, cardboard texture, gritty soil and more defined grass. The generated source is 1706x922; the game texture preview is 2220x1200. This is a material-detail redesign, not a claim of native 4K source art.

The game's original geometry, UVs, layer ordering and alpha masks are retained. The GENERAL SURPLUS sign and dumpster label are protected using the original compressed texture blocks. All four static scene layers are repacked. Character animations, interactive object assets and clipping masks are unchanged; check transitions such as opening the dumpster in-game for visual consistency before treating this as final.

## Use

Close the game, then use `Apply custom remaster.cmd`. It restores the earlier MOD TEST patch automatically if present. Launch the game again to see the custom background in remastered graphics mode.

`Restore original.cmd` returns the archive to the official artwork. Keep `custom-installed.json`, which stores original archive metadata, until the custom patch is restored. Patches append replacement assets and leave original payloads intact.

## Rebuild

The local `tools/nutcracker-py312` environment contains Pillow and NumPy. Run its Python with `build_custom.py` to map the artwork onto the existing layer textures, encode with Microsoft's DirectXTex, preserve original alpha and protected text blocks, and validate the resulting CHNK files. Run `python custom_patch.py apply` after restoring any installed custom version.

Original-game extraction uses NUTCracker: https://github.com/BLooperZ/nutcracker . Archive layout reference: https://github.com/bgbennyboy/DoubleFine-Explorer . Texture encoder: https://github.com/microsoft/DirectXTex .
