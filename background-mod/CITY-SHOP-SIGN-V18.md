# City panorama, souvenir shop and blinking prize sign

The city panorama source previously measured 2170 x 725, while the room uses
3820 x 1200. `fix_corville_dimensions_v17.py` registers the existing painting
to the original landmarks and saves the correct canvas. Room geometry and
texture alpha remain unchanged.

Corville's three classic cloud palette cycles now modulate the custom painting's
brightness with normalized, smoothed fields. Painted cloud color and original
sky ownership restrict the effect; the fourth electrical cycle is excluded.
Brightness changes are bounded to retain shading. Other rooms retain v11.
Selective cloud rebuilds preserve their manifest entries.

`improve_shop_sign_v18.py` integrates built-in imagegen paintings for room 054's
shop and room 055's FIRST PRIZE! sign. The room protections that previously
restored their old graphics are removed. The unrelated large 5 remains protected.
The shop includes its alternate doorway, cable, counter and empty display state.
Its S/I neon variants and both prize-sign states share canonical artwork, with
the original relative brightness retained. All atlas alpha and excluded white
control-mask pixels are checked against the originals while packing.

Project assets and decoded reviews are under `reviews/shop-v18/`:

- `shop-generated.png`: painted shop crop.
- `sign-generated.png`: painted prize sign.
- `shop-atlas-generated.png`: interaction-state materials.
- `shop-empty-generated.png`: display after taking the toy box.
- `shop-packed.png`, `prize-blink-packed.png`, `shop-state-449-1445.png`: packed previews.

Generated images and game textures stay local in this source-only repository.
Painting used the built-in imagegen tool. Integration uses masks, coordinate
registration and existing texture geometry, not procedural replacement art.

Prompt set:

1. Repaint the exact souvenir shop crop in polished hand-painted adventure-game
   style; preserve object placement, perspective, neon, logos and readable
   GIFTS / COME CHECK IT OUT / Corley's Toy Cars / NEW STUFF / SOUVENIRS /
   Official BUNNY / 12 BUNNY text. Improve metal, enamel, cloth, cardboard and
   wood, retaining dim surroundings and warm shop lighting.
2. Repaint the exact FIRST PRIZE! sign; retain composition, perspective, red
   block text, motorcycle silhouette, off-white enamel and dark frame. Add
   controlled wear and coherent painted detail without extra objects.
3. Repaint only colored shop-atlas islands to match the new shop; retain layout,
   open doorway, cable and empty display; leave white controls and blank areas.
4. Remove only the 12 BUNNY box from the packed shop; reconstruct the exposed
   wall and shelf continuously, retaining every other object and the framing.

Validation: all 717 packed cloud phases across seven rooms retain alpha and
phase-zero base bytes; 200 isolated runtime scheduling/composition/mode-switch
checks pass across 20 textures. Decoded static and state previews were reviewed.
The game was not launched; live gameplay still needs checking after restarting
both the game and helper, because existing GPU and helper caches retain old art.
