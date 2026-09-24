# Live background switcher

Launch the game using `Start live switcher.cmd` in this folder. The helper must stay running. Close any existing game instance first.

- F6 selects the official remastered background textures.
- F7 selects the custom remastered background textures.
- The game's existing classic/remastered toggle is unchanged. When classic graphics are active, F6/F7 choose which remastered background will appear when returning to remastered graphics.

106 custom background views are supported through the ending, plus the duplicate bar room. See [complete coverage](COVERAGE.md) and [previews and prompts](locations/README.md). Characters, game logic, interaction masks, and saves are unaffected. The helper does not write to Throttle.exe or full.data. It works with either the original archive or our installed custom patch by recognizing either texture version. A normal launch without the helper continues to use the version installed in the archive. The additional locations are enabled through the helper, without further archive patching.

## Mechanism

Save8 follow-up: four separately drawn shack debris layers were added, bringing the catalog to 492 texture pairs. Live GPU replacement was verified; see [debris diagnosis and assets](DEBRIS-SAVE8.md).

The supported locations contain 488 texture pairs, including two motorcycle overlay atlases whose opaque scenery previously covered the custom workshop ceiling and drawers. The helper uses Frida to recognize uploads by dimensions, compressed byte count and SHA-256. It remembers their OpenGL texture IDs and replaces their compressed contents on the game's render thread when a hotkey is pressed. The original texture binding is restored after a switch. Hotkeys are read only while the game is the foreground application.

No room reload is necessary when switching modes. Restart the helper and game after adding new textures so the new catalog is loaded. The user confirmed working F6/F7 switching in the dumpster scene; later user-run logs also show workshop, shack and town texture matches and switches. The driver glClear hook handles this GPU's render callback. The latest three backgrounds (safe closeup, corridor, and media room) passed asset validation and offline visual review, but need an in-game check. Some interactive states, including open gates, the lit crane button, ranch door states, parts number reveals, cave object-state scenery patches, kiosk item/sign states, arena doors, safe plate/button states, corridor door/indicator states, and media-room door/image states, retain their original artwork. No game launch was performed for this batch.

## Gas tower freeze investigation (save7)

The helper now loads compressed texture payloads on demand into a 64 MiB cache instead of retaining all 838.4375 MiB of official/custom payloads. The game executable is 32-bit and is not large-address-aware, so the previous preload substantially reduced the address space available for gameplay and cutscenes. This is a suspected cause of the reported hose cutscene freeze; confirmation in the game is still pending.

`test_texture_cache.py` exercised the actual helper in a disposable 32-bit process, without launching the game. All 976 payloads passed hash and upload-fingerprint checks; peak cached payload memory was 64 MiB, pinned allocations survived eviction, evicted data reloaded correctly, and invalid hashes were rejected. Results: `live-switcher/cache-validation.json`. Temporary file-read/hash buffers and the game's own allocations are outside that cache limit. Restart the helper and game to use the change.

## Helper files

Custom mode can now animate the red murder-sequence clouds and Corville's sky
using reconstructed classic palette cycles. See [scope, build steps and timing
limitations](CLOUDS-AND-LETTERING-V9.md). Official mode remains static. Restart
both game and helper after preparing the new catalog.

- `live_switcher.py`: launcher, texture-pair preparation and helper lifecycle.
- `live_switcher.js`: process-local OpenGL hooks and hotkeys.
- `live-switcher/session.log`: diagnostic events for the latest session.
- `live-switcher/textures.json`: hashes and dimensions of the texture pairs.

Technical references: [Frida JavaScript API](https://frida.re/docs/javascript-api/) and [OpenGL reference](https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/).

User preference: the assistant must ask before launching the game for a test.

Object scenery audit: 87 atlases inspected; 16 additional conservative scenery transfers built and checked. Coverage is partial; unresolved states and review evidence are listed in the [audit report](overlay-audit/README.md). Restart the game and helper to load the updated catalog. Gameplay verification is pending.

Latest screenshot follow-up: [status](REPORTED-ISSUES.md).
