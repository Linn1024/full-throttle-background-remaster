# Open engine-part covers

Room `044-cu-parts` previously replaced only its static background. Opening
the circular cover, small rectangular hatch, or large rear cover restored
original art and baked-in scenery from the room atlases.

`fix_parts_states_v22.py` integrates built-in image generation artwork for
all three covers and the second large-cover variant. Unchanged backing is
sampled from the packed custom background. Original puzzle lettering takes
precedence over generated lettering. Explicit moving-cover silhouettes prevent
similar colors from being incorrectly treated as unchanged backing.

Original atlas dimensions and BC3 alpha are preserved. The white control atlas
is untouched. Four placements were checked against unchanged original patches,
with mean errors below 1.6 channel values. Both packed texture payloads are
included in the 593-pair helper manifest. Verification is offline only.

Artwork: `reviews/parts-v22/open-covers-generated.png`.
Prompt: `reviews/parts-v22/prompts.json` (built-in image_gen).
Packed preview: `reviews/parts-v22/all-open-packed.png`.
Restart both the game and helper to reload the new texture pairs.
