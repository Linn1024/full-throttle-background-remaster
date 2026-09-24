# Direct night sign repaint v16

The v13 luminance regression compressed the material variation in the approved daytime artwork, making the night signs appear unchanged. Repainted both sign faces directly in their night palette using built-in imagegen instead of recoloring them again.

Inputs were reviews/night-signs-v13/label-night.png and surplus-night.png. Prompts requested exact sign placement and wording, subdued blue moonlight, visibly chipped enamel and worn lettering, with all surrounding scenery retained. General Surplus retains a desaturated burgundy backing under the night light. Outputs are copied to reviews/night-signs-v16/<key>-generated.png.

fix_night_signs_v16.py composites only through the existing v8 sign masks. Source pixels outside these masks are asserted identical. Packed before/after comparisons were visually reviewed; original alpha is preserved by build_custom. No game launch occurred. Restart both helper and game after cache preparation.

Rebuild: fix_night_signs_v16.py then live_switcher.py --prepare-only. This supersedes v13 for night sign appearance.
