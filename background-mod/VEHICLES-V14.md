# Vehicle scenes v14

Repainted the three reported scenes with the built-in imagegen tool: 100-mr-truck, 190-bikerock, and 191-mr-trkbk. Inputs were each current custom-remaster-v1.png. Prompts required exact framing, vehicle silhouettes, perspective and component positions, with detailed hand-painted worn metal, glass, wood, sandstone and ground. No characters or interface were included. Generated art is stored in edited/<room>-v14.png; originals and configurations are backed up under reviews/vehicles-v14/<room>/.

The truck wall's oversized official-art protection rectangle was removed so the repainted wood and existing lettering appear together. The other two rooms have no protected regions. integrate_vehicles_v14.py builds all three room assets with original geometry and alpha.

Also generated the two open-state atlases from their original rendered atlases, preserving layout and empty space: edited/100-mr-truck-state-v14.png and edited/191-mr-trkbk-state-v14.png. build_vehicle_states_v14.py maps matching shared bodywork/ground from the packed new scenes, while retaining generated state-specific engine/panel details. Original compressed alpha is preserved exactly by the packer. The existing shared moving grille is unchanged.

Reviewed the generated scenes and decoded packed open-state composites in reviews/vehicles-v14/<room>/open-state-packed.png. Room validation passed for all four CHNK layers, and both state atlases passed alpha checks. No game launch occurred; animation and gameplay alignment still require in-game review.

Rebuild order: integrate_vehicles_v14.py, build_vehicle_states_v14.py, live_switcher.py --prepare-only. Restart both helper and game to load the new cache.
