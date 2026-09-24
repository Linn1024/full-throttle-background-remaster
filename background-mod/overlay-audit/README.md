# Object scenery audit

All 87 room DXT atlases in full.data were inventoried; none are missing locally. All were reviewed in contact sheets. Feature registration found candidates in 41 atlases. A match is not by itself approval to edit a foreground object.

16 additional atlases across 12 rooms have conservative scenery transfers. Five existing manually integrated atlases remain in place. The switcher now contains 477 pairs (450 background textures, 21 room object atlases, four lock-animation atlases, and two bench object-layer textures).

Validation: packed BC3 alpha is identical; excluded visible pixels and untouched blocks are identical. The Kick Stand ground-restoration patch is explicitly mapped in full. Other transfers replace confidently matched textured scenery; smooth or ambiguous patches can remain official. This is partial overlay coverage, not a completed playthrough or a guarantee that every seam is gone.

29 scene composites and 16 original/custom atlas comparisons were generated and reviewed. Scene composites use inferred registration and connected alpha components, not engine sprite geometry: connected neighbouring frames (notably crakwall) can appear together in a diagnostic preview. No game was launched.

| Atlas | Result |
| --- | --- |
| 003-cab_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 005-bar-road_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 006-barfront_room_pk_a00.dxt | Conservative scenery transfer built; 16447 blocks. Gameplay pending. |
| 006-barfront_room_pk_a01.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 007-bar_room_pk_a00.dxt | Needs further work: Small bar/key patches not registered confidently. |
| 010-dumpster_room_pk_a00.dxt | Needs further work: Characters overlap scenery; needs explicit foreground guards. |
| 017-mo-shop_room_pk_a00.dxt | Existing manual scenery integration retained. |
| 017-mo-shop_room_pk_a01.dxt | Existing manual scenery integration retained. |
| 017-mo-shop_room_pk_a02.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 018-mo-shack_room_pk_a00.dxt | Conservative scenery transfer built; 77711 blocks. Gameplay pending. |
| 018-mo-shack_room_pk_a01.dxt | Conservative scenery transfer built; 27311 blocks. Gameplay pending. |
| 018-mo-shack_room_pk_a02.dxt | Conservative scenery transfer built; 28438 blocks. Gameplay pending. |
| 020-melnweed_room_pk_a00.dxt | Conservative scenery transfer built; 1178 blocks. Gameplay pending. |
| 021-trailer_room_pk_a00.dxt | Conservative scenery transfer built; 5289 blocks. Gameplay pending. |
| 023-todds_room_pk_a00.dxt | Existing manual scenery integration retained. |
| 023-todds_room_pk_a01.dxt | Existing manual scenery integration retained. |
| 025-toddshop_room_pk_a00.dxt | Conservative scenery transfer built; 4589 blocks. Gameplay pending. |
| 026-gas-gate_room_pk_a00.dxt | Conservative scenery transfer built; 1040 blocks. Gameplay pending. |
| 026-gas-gate_room_pk_a01.dxt | Conservative scenery transfer built; 3283 blocks. Gameplay pending. |
| 026-gas-gate_room_pk_a02.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 027-junkgate_room_pk_a00.dxt | Existing manual scenery integration retained. |
| 027-junkgate_room_pk_a01.dxt | Conservative scenery transfer built; 3326 blocks. Gameplay pending. |
| 028-magnet_room_pk_a00.dxt | Needs further work: Button light states; no confident registration. |
| 032-mensroom_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 033-ambush_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 041-roadblck_room_pk_a00.dxt | Needs further work: Lighting overlay differs from static reference. |
| 043-ranch_room_pk_a00.dxt | Needs further work: Door and vehicle states need individual guards. |
| 044-cu-parts_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 044-cu-parts_room_pk_a01.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 044-cu-parts_room_pk_a02.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 045-vista_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 046-plaque_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 048-caveroad_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 049-caveturn_room_pk_a00.dxt | Needs further work: Bike/ground patches; no confident registration. |
| 050-cavemesa_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 051-corville_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 052-vultrock_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 053-vultures_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 054-souvenir_room_pk_a00.dxt | Needs further work: Small sign/item patches; no sufficiently large eligible region. |
| 055-turnstil_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 056-arena_room_pk_a00.dxt | Needs further work: Repeated door patterns give ambiguous registrations. |
| 057-demowall_room_pk_a00.dxt | Needs further work: Small door fragment; no confident registration. |
| 060-big-door_room_pk_a00.dxt | Needs further work: Light/window states; no confident registration. |
| 061-crakwall_room_pk_a00.dxt | Conservative scenery transfer built; 3595 blocks. Gameplay pending. |
| 061-crakwall_room_pk_a01.dxt | Conservative scenery transfer built; 4681 blocks. Gameplay pending. |
| 062-office_room_pk_a00.dxt | Needs further work: Small door fragments; no confident registration. |
| 063-safe_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 063-safe_room_pk_a01.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 064-corridor_room_pk_a00.dxt | Needs further work: Door/indicator states; no confident registration. |
| 064-corridor_room_pk_a01.dxt | Needs further work: Door/indicator states; no confident registration. |
| 065-media-rm_room_pk_a00.dxt | Needs further work: Door and photograph; no confident registration. |
| 066-projectr_room_pk_a00.dxt | Needs further work: Moving reels overlap matching stationary pixels; needs explicit guards. |
| 066-projectr_room_pk_a01.dxt | Needs further work: Moving reels overlap matching stationary pixels; needs explicit guards. |
| 066-projectr_room_pk_a02.dxt | Needs further work: Moving reels overlap matching stationary pixels; needs explicit guards. |
| 067-stage_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 070-showdown_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 073-cargo_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 073-cargo_room_pk_a01.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 073-cargo_room_pk_a02.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 076-gastower_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 090-c130fore_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 091-junkyard_room_pk_a00.dxt | Needs further work: Small scenery/state fragments; no confident registration. |
| 095-minefld_room_pk_a00.dxt | Needs further work: Crater/ground state differs from static reference. |
| 098-chaufeur_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 099-behind-t_room_pk_a00.dxt | Needs further work: Moving truck panels require state-specific masks. |
| 100-mr-truck_room_pk_a00.dxt | Conservative scenery transfer built; 2520 blocks. Gameplay pending. |
| 1007-bar_room_pk_a00.dxt | Needs further work: Alias of bar; small bar/key patches not registered confidently. |
| 107-barfro-n_room_pk_a00.dxt | Conservative scenery transfer built; 2294 blocks. Gameplay pending. |
| 115-barroa-n_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 116-dumpst-n_room_pk_a00.dxt | Conservative scenery transfer built; 2231 blocks. Gameplay pending. |
| 123-cargofnt_room_pk_a00.dxt | Needs further work: Characters and dashboard require state-specific masks. |
| 129-fuselage_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 130-dustspil_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 130-dustspil_room_pk_a01.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 130-dustspil_room_pk_a02.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 130-dustspil_room_pk_a03.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 130-dustspil_room_pk_a04.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 131-petes_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 132-cu-hand_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 141-cockpit_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 144-scold_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 159-cavetrn2_room_pk_a00.dxt | Conservative scenery transfer built; 1030 blocks. Gameplay pending. |
| 164-cruise_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 169-cock-mon_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 173-crgotruk_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 174-cliffhng_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |
| 191-mr-trkbk_room_pk_a00.dxt | Retained: foreground, mask, text, or state artwork; no verified scenery replacement. |

Rebuild: `audit_object_scenery.py`, `build_audited_overlays.py`, `review_audited_overlays.py`, then `live_switcher.py --prepare-only`. The build script preserves existing dedicated replacements.

Evidence: [registrations](registration.json), [build checks](built.json), [composite index](composites.json).
