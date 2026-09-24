# Photo sprite scenery correction

fix_media_photo_scenery.py maps the surrounding easel pixels to the packed lighting-v3 background at half scale, shift (949.5,-52.5). An explicit polygon protects the photograph including its white border. All scenery edges are eligible; BC3 alpha and foreground blocks remain unchanged. Local composite: custom-v1/photo-composite-check.png. Gameplay pending.
