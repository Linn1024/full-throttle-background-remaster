# Pete's chest, banner and pillow v15

The requested chest and banner in 131-petes were redrawn using built-in imagegen, retaining their emblems, placement and dim lighting. Source crops and generated art are stored under reviews/petes-v15. fix_petes_v15.py retains a backup of the source/configuration, reconstructs the previous official-protection blend, then composites generated artwork through object masks before removing the two protection rectangles. The surrounding room is retained.

Updated the open chest CHNK, both raised-pillow CHNK states and the unlocked chest atlas. Generated bedding replaces the old flat artwork exposed under the pillow. Shared scenery is registered to the new packed room; the pillow states use identical artwork outside the tool-removal area to avoid a visual jump when taking the tool. The unlocked chest's distinct lock and atlas control masks are retained.

Original CHNK headers and BC3 alpha are retained exactly. Excluded visible control pixels are checked against the original. The report's protected_foreground_identical flag refers to those excluded pixels; the requested chest/pillow foreground is intentionally redrawn. No helper validation was weakened or changed.

Packed open-chest and both pillow composites were reviewed offline. No game launch occurred. Runtime interaction alignment still needs checking in game. Run fix_petes_v15.py and live_switcher.py --prepare-only; restart both game and helper.
