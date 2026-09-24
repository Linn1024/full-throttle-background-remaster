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

## Shared porch seam follow-up

The raised sprite also contains fixed porch boards. The independent generated
crop gave those boards a different texture and orange lighting at the sprite's
left boundary. `fix_shack_seam_v5.py` copies the registered main background into
that shared porch polygon, retaining the moving platform and both lifting ropes.
Run it after the v4 deck builder and before refreshing the cache. Its local
pre-fix backup is `reviews/shack-seam-v5/before.dxt`.

Original alpha, rope pixels and all unedited BC3 blocks pass equality checks.
The actual compressed sprite is inspected against its neighbor in
`reviews/shack-seam-v5/packed-composite.png`. No new generation was needed;
this is registration of existing approved artwork. Gameplay remains unverified.

## Two-layer correction (v6 supersedes v5)

The next screenshot exposed remaining joins, including the neighboring porch
edge sprite in atlas a02. `fix_shack_joins_v6.py` starts from the v4 raised deck
to remove the hard v5 polygon. It transfers shared scenery around the actual
moving deck and narrow rope silhouettes, with a short transition at foreground
edges. It also registers the complete fixed porch-edge sprite to the same room
background. Both atlas a01 and a02 are now included in the compressed composite
review at `reviews/shack-joins-v6/packed-composite.png`.

Run v6 after v4 instead of v5. It retains original alpha, white control masks,
and all pixels outside changed compression blocks. The neighboring white mask
cell is excluded from the offline sprite preview, as it is not rendered by that
sprite's UV region. Cache refreshed; this remains an offline validation and does
not establish that all in-game animation states are free of seams.
