# Opening dumpster background project

**Background pass complete:** 106 custom static views through the ending, plus the duplicate bar room, are packaged for F6/F7 switching. See [coverage](COVERAGE.md) and [previews and prompts](locations/README.md). Launch with **Play with background switcher.cmd** in the game directory. Asset checks passed; gameplay checks and remaining animated scenery overlays are still pending. No game was launched.

**Current version:** the custom four-layer remaster has replaced the MOD TEST patch. See [ART-DIRECTION.md](ART-DIRECTION.md) for the approved visual direction, source references, generated artwork, final packaged preview and rebuild instructions. Use **Apply custom remaster.cmd** to install it and **Restore original.cmd** to undo it, with the game closed. Both protected lettering regions were verified pixel-for-pixel identical to the official artwork, and all four installed asset payloads passed read-back verification. In-game visual and interaction checks remain for the user.

## Earlier technical test

This test changes the remastered opening location, `rooms/010-dumpster`, by adding cyan MOD TEST graffiti to the dark wall beside the dumpster. Restart the game and enter that location in remastered graphics mode to verify it visually. Archive and texture validation passed; in-game confirmation is still needed.

Close the game before double-clicking **Restore original.cmd** or **Apply test.cmd**.

The patch appends one replacement `010-dumpster-layer10.chnk` to full.data and updates its archive record and data-length field. The original asset bytes remain in the archive. `installed-patch.json` backs up the original header, record and file length and records the replacement hash. Restore checks the installed patch, reinstates the original metadata and removes only the appended bytes. Keep this folder until the patch is restored. Game updates or verification can overwrite the patch.

Extracted original files are in `original/rooms/010-dumpster/`; decoded texture tiles are in `previews/`. The room has four background layers plus clipping masks and interactive object assets. Its CHNK textures contain raw-DEFLATE-compressed DXT1 or DXT5 data. This test replaces only BC1 blocks in a small rectangle of the second texture of layer10; all other blocks and other room assets remain unchanged.

The editable generated artwork is `mod-test.png`; its game-sized BC1 conversion is `edited/mod-test.dds`. `patch_background.py build` produces and validates the replacement CHNK. To change other parts of the scenery, first account for the relevant texture tile and foreground layers; replacing one flat scene image is insufficient.

Tools: built-in imagegen for the artwork; Microsoft's DirectXTex texconv for texture conversion. Archive layout reference: https://github.com/bgbennyboy/DoubleFine-Explorer/blob/master/uDFExplorer_LPAKManager.pas

Image prompt used: Edit target: the provided 1024x1024 game background texture tile. Use case precise-object-edit. Make a minimal obvious mod verification change: paint the exact words "MOD TEST" in vivid cyan graffiti on the dark wooden wall in the upper left quadrant, within x=120..430 and y=60..220. Keep the entire rest of the image identical, including edges, existing sign, objects, ground, perspective, lighting and exact 1024x1024 dimensions. No reframing, no new objects, no other edits. This is a seamless tile in an existing game background, so all four borders must remain unchanged.

The generated image was 1254x1254; texconv resized it to 1024x1024 for the game. Only the marking region's compressed blocks were inserted into the original texture to preserve the original borders and surrounding artwork exactly.
