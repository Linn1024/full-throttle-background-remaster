# Demolition derby artwork, v21

The derby scenes mixed low-resolution background paintings with original signs,
cars and animated object patches. This pass replaces the six connected views,
registers their paintings to the original camera coordinates, and updates the
visible vehicle and effect atlases.

## Installed scope

- `056-arena`: arena wall, advertisements, asphalt and all hatch animation states.
- `057-demowall`: close wall view, signage and prize-platform overlays.
- `058-derbycar`: cockpit materials, upholstery, cage and straps.
- `059-rips-box`: booth and outside wall, plus all 16 CRT animation frames.
- `096-demoderb`: driver-lineup background, parked cars and advertisements.
- `142-derbypit`: complete top-down arena, borders, ramps, obstacles and signs.
- 40 vehicle atlas files covering the five car colors and their angled/top-down
  views, including repeated directional variants.
- 17 fire atlas files covering car fire, small fires, big fires and huge fires.

The five scene views use 2220×1200 canvases; the top-down arena uses 5380×2400.
Generated paintings are registered/resampled to these native coordinate canvases;
their generation resolution is recorded separately and is not native-resolution
detail. All room vertices, UVs and original alpha are retained. Registration is
rigid: texture-based local flow was rejected because it distorted straight floor
lines. The Corley sign in the top-down view has a separate spelling correction.

Old rectangular sign protections were removed for these fully repainted rooms.
Hatch and platform patches take their unchanged surroundings from the same packed
room painting. Changed object portions use the generated state art. This prevents
independently painted backgrounds forming rectangles around moving objects.

The CRT chunks are placed by the room at a +340-pixel horizontal offset. That
offset is used only for review renders; the actual chunk geometry is unchanged.

## Preserved assets

Character animation, character lighting masks, standalone black shadows and white
control/occlusion pages are unchanged. The unusual legacy pages in costumes 203
and 207 were retained rather than treating their nonstandard colors as visible
car paint. Normal visible derby cars are supplied by 204–209 and 380–390; the white
386 pages are also retained. No costume animation metadata was edited.

## Build and review

Run with `tools/nutcracker-py312/Scripts/python.exe`:

1. `audit_derby_v21.py` and `audit_derby_effects_v21.py` prepare original reviews.
2. `build_derby_v21.py --install` installs all six registered backgrounds.
3. `build_derby_sprites_v21.py --install` packs generated pages and matching variants.
4. `build_derby_overlays_v21.py` installs room states and monitor animation.
5. `validate_derby_v21.py` checks installed geometry, alpha, isolated shadows,
   coverage and flame visibility, and writes decoded review sheets.
6. `live_switcher.py --prepare-only` validates texture identities and prepares the helper.
7. `validate_derby_v21.py --check-helper` confirms that every derby costume page
   is present in the final helper manifest with the current packed hash.

Generation records are in `reviews/derby-v21/prompts.json`. Original assets and
generated binary art remain local and are excluded from the source repository.
Existing background sources/configs were saved in the review directory before
replacement. Re-running the builders requires those local image outputs.

Reviews include `backgrounds-packed.jpg`, `packed-atlases-*.jpg`, the two
`*-states-packed.jpg` sheets and `monitors-packed.gif`. These are offline decoded
asset previews. The game has not been launched or gameplay-tested for this pass.
Restart both the game and helper to load the new assets; a mode toggle alone does
not replace textures already cached by the current processes.

Validation completed for all six backgrounds, 57 costume atlas files, two room
atlases and 16 monitor frames. Geometry and alpha checks passed, isolated black
shadows and white control pixels were unchanged, and the packed flame check found
no material loss of visible fire. All six decoded atlas review sheets and the
background/state sheets were visually inspected. Python compilation and the Git
whitespace check also passed.
