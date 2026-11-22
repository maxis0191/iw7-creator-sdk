# Station Zero g27n: release candidate 3 (22 Nov 2026)

Follows [STATION-ZERO-G27J.md](STATION-ZERO-G27J.md) (RC2). Package `<runtime>\iwz-release\cp_iwz-g27n-rc3` (manifest with
hashes and every measurement). Not accepted, not deployed. The map now starts dark and lights zone by zone when the power
comes on. Plan for the content that does not exist yet: [STATION-ZERO-ROADMAP.md](STATION-ZERO-ROADMAP.md).

## Changed since RC2, each with its measurement

| Change | Cause found | Result |
|---|---|---|
| Darkness shipped (`build-g.ps1 -Darkness -DarkZoneFill`) | RC2 "not diagnosed": the lab's generator `use` step left power off in client cells; `szaccept::sz_power_direct` calls the map's own generator activation | power on in 2.8 s, 9 light banks in 13 s; dark state mean luma 0.033 over 14 views |
| Lit vision `tonemapAutoExposureAdjust -2.5` | the lit vision equals stock cp_zmb's, but the generated lighting rendered at mean 0.442 / p90 0.82 against stock 0.175 / 0.34; of the vision keys only AutoExposureAdjust and Auto + ExposureAdjust are read (engine field table 0x141742648, darkness NOTES 22 Nov) | lit mean 0.171, p90 0.403, contrast 0.95 (stock 0.175 / 0.339 / 0.83) |
| RC2 review fixes (platform lip and tactile strip, platform B patches as irregular worn concrete, seated planks / chairs / rubble, stair nosing uvs, train interior and fire light, signal post, well stringer, alcove back wall) | REVIEW-RC2 items 1-9 | the white platform lip still reads blown in the well views (open) |
| Capsule Post hatch: a stock wall panel on the wall (`level.iwz_post_hatch_model`) | the 19-zone pipe stand-in floated in mid air | not separately reviewed |
| Capsule Post drawn-in zombies travel with the capsule | left at the departure hatch, the stock far-from-players cleanup removed all three (BLOWBACK_OUT 0 of 3) | 3 of 3 come out; post_rules 39/39 |
| Round probe (server `szaccept`) | it keyed zombies by entity number (reused) and counted recycled zombies twice: the "idle zombies at spawners" and "stalls" of RC2 were the probe | census: no zombie idles 30 s in rounds 5-8; rounds end on their own (80-88 s of game time); all rounds 1-15 pass |

## Measured on g27n (Forge, compressed time 10x unless said)

doors 70/70; economy 76/76; wells 9/9; stairs 9/9; Capsule Post routes 128/128 and rules 39/39; rounds 1-15 in eight plans all
pass; start of a match with every door closed 20/20; PaP with the real Use key (client) 7/7; door walk with a real client
joined to a dedicated server at real time: blocked at the tunnel door and the PaP shutter.

## Look: three independent reviewers, 28 frames (14 lit, 14 dark), stock Spaceland frames as reference

Lit 6.5 / 6 / 6.5, dark 5 / 5 / 6; target 7.5; verdict "not yet" from all three. Agreed defects for RC4:
1. Stair-stepped, blocky shadow edges on walls and floors (service tunnel, platform B, stair B, hero car, generator room):
   new with the dynamic shadowed power lights of the darkness build.
2. Black voids: generator room right third behind the railing, platform A right block, control room right half.
3. The platform-edge lip still a blown white line (well views), lit and dark.
4. Dark start too dark to navigate at stair A, stair B, the hero car and the service tunnel.
5. Pack-a-Punch alcove reads empty: the alcove camera faces the side wall (the machine is out of frame) and the alcove has no
   signage or dressing; repeated posters and identical seats in the ticket hall; a black blob on the ticket-hall floor.
