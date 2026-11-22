# Station Zero g27r: release candidate 4 (22 Nov 2026)

Follows [STATION-ZERO-RC3.md](STATION-ZERO-RC3.md). Package `<runtime>\iwz-release\cp_iwz-g27r-rc4` (manifest with hashes
and every measurement). Not accepted, not deployed. Look: not yet at 7.5 (scores below).

## Causes found and fixed (each measured)

| Defect | Cause found | Fix | Measured |
|---|---|---|---|
| Stair-stepped light edges and black voids (RC3 review items 1, 2) | the map compiler gave each generated light the culling shapes of the template slot it took; on cp_zmb a spot slot's frustum mesh and view frustum are a cone and a box clipped to the template's rooms (slot 1022 reaches 145 of radius 400), so an omni light or a wider spot placed there was lit only inside that outline | x64-zt `claude/iwzmap-light-volumes-1dcd449` (ea60b19): every generated light gets the 32-vertex sphere mesh of an unused template omni slot scaled to its radius, omni lights no view frustum (as stock omni slots), spot lights the box round their sphere; `IWZ_TEMPLATE_LIGHT_SHAPES=1` keeps the old shapes | A/B build with nothing else changed (g27o_ab against g27n): generator room near-black area 17 % to 6 %, platform B 13 % to 5 %, the stepped edges gone from the tunnel walls |
| Pack-a-Punch machine never drawn (since RC1; the interaction worked) | 1,435 rows of the zone list were references to assets of the stock map's own zone (the patch zone lists them as references), which a generated map replaces and never loads: 876 images, 220 xmodels, 140 xanims, 65 vfx, 55 xmodelsurfs. The machine's surfaces and materials were among them | `assemble.py`: a reference row whose asset a stock dump holds in full becomes a full row (`IWZ_KEEP_STOCK_REFS=1` keeps the old rows); `sz2_assemble.py` adds the models a relocated stock scriptable draws | the machine model placed by script in the open ticket hall beside a control panel drew nowhere (g27q); on g27r the stock machine draws in the alcove, lit and dark, with no stand-in |
| Dark start too dark at the stairs, train and tunnel (RC3 item 4) | no battery light there | warm white battery lamps on stair A, stair B, the service tunnel, a battery lamp in the hero car (emergency group, baked) | dark mean luma 0.029 to 0.083, near-black share 56 % to 29 % over 13 views; stair A 77 % to 35 % |
| PaP alcove empty (RC3 item 5) | the machine was not drawn (above) and the alcove had no dressing | PACK-A-PUNCH bay plate, threshold stripe, cable trays, switchgear; alcove cameras facing the machine | frames lit/dark_pap_alcove_1/2 |
| Ticket hall repetition (RC3 item 5) | the two ad frames drew the same poster; benches identical in a row | east frame keyed to another poster; benches turned and moved | the black blob near the hall camera is still there (reviewers) |
| "Stuck" zombies on stair A, rounds 1-2 and 11-12 (also present on g27l and the first RC3 runs; RC3 reported reruns that passed) | not stuck: census of 13 such zombies over 3 runs, each with its AI goal, path to goal and enemy. Every one had the player as its goal and a valid path: at the player's feet on the slope (3D distance 113-139 against the probe's 110), slow walkers still on their way (1,832 walked, 1,716 to go at 50 s), or milling behind the crowd at the player | server `szaccept` round probe: reached = 110 on the ground plane and 96 in height; stuck = no 64-unit progress along its own path for the window while more than 200 from the player | see "Measured on g27r" |

Platform B lip: the white band is the top of the edge-panel model; a cap in front of it breaks the trackbed rule (the car channel is
kept clear), so it stays open. One round 2 of nine stalled 90 s with every zombie dead (g27q census, not seen again on g27r): open.

## Measured on g27r (Forge, compressed time 10x unless said)

doors 70/70; economy 76/76; wells 9/9; stairs 9/9; Capsule Post routes 128/128 and rules 39/39; start with every door closed 20/20;
PaP with the real Use key (client) 7/7; rounds: see the RC4 report line in `docs/STATE.md` of the server (rerun with the corrected
probe). Lit frames mean luma 0.168, near-black 9 % (stock Spaceland 0.174, 13 %).

## Look: three independent reviewers, 30 frames, stock Spaceland frames as reference

Lit 6.5 / 6.5 / 6.5 (RC3 6.5 / 6 / 6.5), dark 5.5 / 5 / 5 (RC3 5 / 5 / 6); "not yet" from all three. Agreed defects for RC5:
1. The player's flashlight pool in the dark: a hard circular edge, stair treads blown white inside it (stair B, platform A, ticket hall).
2. Hard vertical light cuts on the well walls in the dark (well_e x~1060, well_w x~250-330) and an angular floor patch on platform B.
3. Dark rooms still read only by the flashlight: generator room, platform B, the stair exits and the tunnel end; a blue-white glow with no
   fixture in the generator room; rail sleepers glowing white in the dark tunnel.
4. The lit state reads too dim for "power on" in the control room, platform B and the ticket hall (exposure was matched to stock mean
   luma in RC3; reviewers want a visible difference from the dark state).
5. The black blob on the ticket-hall floor (still there after the backpack swap), the black rock pile in the service tunnel, the
   platform-lip white band, Pack-a-Punch without its own light.
