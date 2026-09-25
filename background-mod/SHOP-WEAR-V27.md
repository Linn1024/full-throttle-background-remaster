# Small gray stains on shop signs

Restored sparse gray paint chips and smudges on the souvenir shop's painted signs, using the official artwork as the wear reference. The current lettering, logos, lighting and scene layout remain. Built-in imagegen created the edit; the prompt and reference crops are in `reviews/shop-v27`.

`fix_shop_wear_v27.py` registers the generated crop and transfers only small gray changed regions inside the sign surfaces. It updates overlapping interaction-state backing, preserving existing atlas blocks outside the changed areas and preserving alpha exactly. Both background layers are packed and texture gutters repaired.

`reviews/shop-v27/source-before.png` and `atlas-before.dxt` are backups. `shop-wear-preview.png` shows the result; `validation.json` records registration and scope. Rebuild with `fix_shop_wear_v27.py`, then `live_switcher.py --prepare-only`. Earlier shop builders overwrite these additions, so run this last.

Verification is offline. Restart the game and helper to load the new textures; the game was not launched for this update.
