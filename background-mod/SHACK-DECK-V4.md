# Raised hoist platform repair

The third state in `018-mo-shack_room_pk_a01.dxt` contained extra fragments and
discontinuous planks introduced by the whole-atlas redraw. This correction uses
the original intact platform as the edit reference and replaces only atlas crop
`(1386,580,1970,950)`. Other states and the broken-shack debris are retained.

Built-in imagegen with the imagegen skill produced
`exec-e50bb25b-ca01-4a6e-8bdd-c376782f61de.png`, copied into the project at
`reviews/shack-deck-v4/deck-generated.png`. Original reference:
`reviews/shack-deck-v4/deck-original.png`.

Prompt:

> Precise object edit of this original game sprite crop. Refine only surface
> material detail on the existing intact wooden hoist platform planks. Preserve
> exactly all geometry, plank directions and uninterrupted long straight plank
> edges, deck outer silhouette, perspective, positions of both hanging vertical
> supports, warm light patch on left and very dark blue purple nighttime
> exposure. This is an intact flat deck: NO loose boards, NO debris, NO broken
> planks, NO gaps punched in deck, NO added objects or new raised beams. Add
> subtle fine hand-painted wood grain following each existing plank, restrained
> wear. Keep background and supports in place, do not brighten, no exaggerated
> textures. Same crop composition, no borders.

Run `fix_shack_deck_v4.py` after `fix_shack_states_v3.py`, followed by
`live_switcher.py --prepare-only`. The scoped repair keeps a local pre-fix atlas
in `reviews/shack-deck-v4/before.dxt` for repeatability. The script matches broad
lighting to the official crop and retains the new material detail.

Checks: original alpha is identical; all pixels outside modified BC3 blocks are
identical to the pre-fix atlas. Inspected the decoded packed output at
`reviews/shack-deck-v4/deck-packed.png`. Cache refreshed offline; no game launch.
