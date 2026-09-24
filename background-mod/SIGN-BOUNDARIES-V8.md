# Sign crop surroundings

The v3/v4 rectangular crop composites replaced surrounding scenery as well as
the intended signs. Feathering the crop edges did not remove the flat wall
patches, and the gate crop also introduced a dark artifact beneath its plates.

`fix_sign_boundaries_v8.py` restores the pre-edit scenery in all four recently
redrawn inscription groups: dumpster label, General Surplus, gas-gate warning
plates, and Todd's / JUNK-YARD / ENTRANCE lettering. It reuses the reviewed
generated artwork inside tight object masks, retaining original outer edges
and the wooden post in front of General Surplus. No new artwork was generated.

The script checks exact restoration outside the masks and unchanged pixels
outside the affected crops. It leaves workshop, shack, and other room fixes
alone. Run it after the older v3/v4 integration scripts, which otherwise
reintroduce rectangular surroundings. Build root, 026-gas-gate and 027-junkgate,
then refresh the live-switcher cache.

Review crops and validation are under `reviews/sign-boundaries-v8/`. CHNK
rebuilds check geometry headers and alpha against the originals. Verification
is offline; this is an audit of the recent custom inscriptions, not a claim
that every original sign in the game was replaced or checked in gameplay.
