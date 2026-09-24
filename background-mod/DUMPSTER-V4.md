# First room switching and sign correction

The archive still contains the initial four-layer custom dumpster installation.
After later background rebuilds, its seven compressed textures match neither
the official hashes nor the current custom hashes. The upload hook consequently
ignored the room, leaving both its old label and background visible in F6/F7.
The session log contained no matched dumpster textures, and read-only comparison
confirmed all four archive entries differed from both current variants.

`live_switcher.py` now reads those four current archive entries during preparation,
checks their geometry against the originals, and adds their texture hashes as
input-only aliases. `live_switcher.js` recognizes these aliases using both small
fingerprints and full SHA-256. Output payloads remain the original official art
for F6 and the latest custom art for F7. The archive itself is not modified.
Ambiguity checks cover official, custom and alias identities.

The General Surplus sign is now custom as requested. The v3 dumpster label is
retained. `build_custom.py` no longer protects the old shop sign.

## Generated art

Built-in imagegen, using the imagegen skill. Edit target:
`reviews/dumpster-v4/sign-input.png`, scene crop `(1690,180,2120,480)`.
Output copied into the project at `reviews/dumpster-v4/sign-generated.png`.
Generator output: `exec-eeb295c2-2331-4a5e-8f02-217938d96a3a.png` in session
`01a0cd70-1192-7f73-919f-7322a0c4973c`.

Prompt:

> Edit this game background crop. Redraw the GENERAL SURPLUS sign with refined
> hand-painted material detail matching a high-quality Full Throttle
> adventure-game background. Exact text two lines: GENERAL / SURPLUS. Retain
> identical lettering layout, perspective, shape, position, muted red painted
> sign and ivory lettering. Crisp believable painted letters, subtle wear,
> small bolts and restrained depth. Preserve the surrounding wall, shutter,
> wooden foreground post and lighting, no added objects, no extra dirt, no
> shiny photorealism. Keep exact crop framing so this can be registered back
> onto the scene.

Rebuild with `integrate_dumpster_sign_v4.py`, then `build_custom.py`, then
`live_switcher.py --prepare-only`. The integration script retains a local
pre-sign backup and preserves the previously redrawn dumpster label.

## Checks

- Rebuilt all four background layers; alpha and geometry checks passed.
- Inspected `reviews/dumpster-v4/packed-signs.png` after compression.
- Refreshed 510 texture pairs, including seven installed-texture aliases.
- `test_live_texture_aliases.py` exercised the actual JavaScript matcher in an
  isolated Frida helper process: 28 checks passed (seven each of official,
  current custom, archive-installed custom and altered texture rejection).
  Rejection alters a byte outside the fingerprint windows to verify full hashing.
- No game launch or archive modification. In-game F6/F7 rendering needs a check
  after restarting the game and switcher helper with the new script/catalog.
