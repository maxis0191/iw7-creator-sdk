# A2: the Underpass Arcade shell (worker A2, 27 Nov 2026)

## Resumed (27 Nov, after the pause)
- `ok: false` had one cause: three back-room spawners 18 units from a side wall stood on no navigation cell (`emit.problems`). They now stand
  34 from it, facing along the room (the emergence carries a zombie 62.5 forward; the rooms are 92 deep). `check`: ok, reach 61 of 61.
- `WALKABLE_OFF_NAV` (players can stand there, zombies cannot reach them): bisected by dropping clip boxes one at a time. Copy Stop: the
  service counter and the pigeonholes on the partition left a 56-unit corridor without nav cells; the pigeonholes moved to the east wall.
  Needle Drop: the record bins' clip island.

## Score against QUALITY-BAR part C (`film/arcade_score.py`, document counts)

| # | Rule | Number | Pass |
|---|---|---|---|
| 1 | every shop told by a hero sign of its own | 6 hero signs, 6 distinct pictures, every shop has one | pass |
| 2 | hero sign face 19,600 or more | {"needle_drop": 20400, "copy_stop": 21080, "hole_nine": 20400, "heel_key": 20400} | pass |
| 9 | at most 0.049 lights per 1,000 | {"hall": "21 lights, 0.0146 per 1,000", "needle_drop": "4 lights, 0.0417 per 1,000", "copy_stop": "4 lights, 0.0205 per 1,000", "hole_nine": "4 lights, 0.0417 per 1,000", "heel_key": "1 lights, 0.0104 per 1,000"} | pass |
| 10 | median light radius 175 or more | 187.4 | pass |
| 11 | no two shops share a light row (strength, radius, height) | 0 shared | pass |
| 12 | neighbouring shops differ in dominant hue; four hue classes at most a room | {"needle_drop": "warm", "copy_stop": "cool", "hole_nine": "magenta", "heel_key": "warm"} | pass |
| 13 | 65 % of lights within 96 of a fixture model; 40 % of tube fixtures off or damaged | 25 of 34 lights (74 %); 5 of 10 tubes off (50 %) | pass |
| 16 | no two perk machines within 404 | 0 perks in the section | pass |
| 17 | three of five pockets host a gameplay object (3 of 4 here) | 3 of 4 | pass |
| 23 | one column pitch, columns in the hall tile, none from another theme | pitch [288.0], 6 columns, material ['w/dt_tile_ceramic_white'] | pass |
| 24 | tile kit of five: wall, its damaged twin, band, dark, floor | {"wall": true, "damaged twin": true, "band": true, "dark": true, "floor": true} | pass |
| 25 | four sign families at most a hall (doc part; the landmark is a blind question) | 5 families | **fail** |

Rule 25 fails by the slot list of the brief: the hall carries five sign families (fascias, 64 x 96 panels, the directory, the notices, the hanging banner and bunting). Merging the notices into the directory's case would make four; not done without the lead's word.

## Decisions the brief did not dictate
- **Tile kit** (one table `MAT` at the top of the builder, the swap to `B.material` is one edit there): wall `w/dt_tile_ceramic_white` with its
  true twin `w/dt_tile_ceramic_white_dmg` (the cp_disco station's pair; the base tint `w/iwz_tile_cream` has no damaged twin), band
  `w/ceramic_tile_01_orange` (from mp_depot), dark `w/fac_tile_black_01`, floor `w/linoleum_floor_tiles_orange_01` (mp_codphish).
  Dado: skirting 0..10, band 58..74 and 220..228, 14 damaged patches (seeded).
- **Columns**: 40 x 40 boxes at y 3760, x -2860 + 288 k (six), dark base to 16, bands 58..74 and 196..212, two with damaged patches.
- **Ceiling**: a panel plane at z 244 (hall clear height 244 under the slab at 256), T-bars every 48, 7 lit panels
  (`plastic_wall_panel_light_02_on`) each with one soft spot, 9 dead, 6 missing (black plenum), 8 water-stained; five tubes over the colonnade
  (three live, two dead) and two dead tubes over the north lane. Bulkhead y 4232..4300 down to z 240: the fascias (z 172..240) sit under it.
- **Shop line**: piers 16 wide at each unit edge in the hall tile; openings z 0..150; shutter housings z 150..172; curtain stops: Needle Drop
  z 112.5, Copy Stop and Hole Number Nine up, Heel & Key z 75 (with a clip over the counter so the stall is not entered).
- **Doors**: Needle Drop door at its west edge (100 wide), Copy Stop central pair (132), Hole Number Nine side door at its east edge (100);
  back-room doors 64 wide in partitions at y 4480; Heel & Key's back room opens east into a service passage (x -1320..-1200) with a staff
  door to the hall.
- **Authored, not stock**: floor polisher (`cp_disco_floor_buffer` is the bladed trap), Shelter 7 hand wheel, photo booth, copier bodies,
  stool bases, the polisher cable.
- **Light colour per brand**: Needle Drop warm orange (pendants 2300 K, an orange window spot, the jukebox glow, a marquee of bulbs under the
  fascia); Copy Stop blue-white tubes (8500 K) with the copier bars as an accent and cold LED bars over its fascia; Hole Number Nine an OPEN
  neon and pink-shaded pendants, a warm downlight over the case, warm wall lamps on its piers; Heel & Key one tungsten desk lamp.
  Fixture radii x 1.6 (`RADIUS_K`) after the first score (median 128 -> 187).

---
(state at the pause, kept for the record)

**State: pass 1 (grey architecture and gameplay) written and checked offline; no live session was run, no frame exists yet.**
Passes 2 to 4 (materials, joinery, light, pictures) are already in the builder as code, but nothing is proven in the game.

## Files
- Builder: `tools-source/iwzmap/station_zero/film/arcade_shell.py` (helpers `shellgeo.py` authored meshes, `standins.py` picture slots),
  scorer `film/arcade_score.py` (QUALITY-BAR part C count rules; not yet run).
- Document: `C:\studio-data\sz\film\arcade\shell\doc` (base `C:\studio-data\sz\film\base_lit`, recipe copied from `allbaked2`), anchors
  `C:\studio-data\sz\film\arcade\shell\anchors.json` (28 named boxes for the goods workers), checks `...\shell\check1.json`, `check2.json`.

## What the document holds (552 objects)
Hall x -3000..-1200, y 3500..4300 with walls, slab, a 48-unit suspended grid at z 244 (7 lit panels, 9 dead, 6 missing, 8 stained), a bulkhead
over the shop line, six square columns at pitch 288 on y 3760 (wall tile, dark base, two orange bands), the five-tile kit
(`dt_tile_ceramic_white`, `dt_tile_ceramic_white_dmg`, `ceramic_tile_01_orange`, `fac_tile_black_01`, floor `linoleum_floor_tiles_orange_01`).
Four fronts of four designs (Needle Drop black frames, door left, shutter a quarter down; Copy Stop white frames, double doors, shutter up;
Hole Number Nine serving counter and side door, shutter up; Heel & Key stall counter, shutter half down, clip over the counter), back rooms
with partitions and doors, a service passage east of Heel & Key. Fixed joinery: sleeve wall, record bins, counters, plan chest, pigeonholes,
authored photo booth and two copier bodies, display case, ledge with authored stool bases, pegboard, bench, lasts shelf.
South wall: 4 payphones, 4 emissive light boxes, directory board lit by a sign lamp, notice frame, poster, 2 benches, a bin. West: the
Shelter 7 blast door (leaf, frame, authored hand wheel). D4: concertina gate folded back, exit sign. Authored floor polisher with its cable
to a wall socket (cp_disco_floor_buffer carries blades: not used). Banner and two bunting strips across the hall.
Light: 34 baked lights, `group: emergency` only (hall 21, Needle Drop 4, Copy Stop 4, Hole Number Nine 4, Heel & Key 1), not yet looked at.
Gameplay: zone `arcade`, door D4 (1000), 10 spawners, SMG 1000 in Hole Number Nine, marksman 1500 on Heel & Key's pegboard, wheel in Copy
Stop's blueprint bay (accepted by the tool, not tried in game). All 23 picture slots read A1's real files; no stand-in at build time.

## `studio check` now (check2.json)
`reach`: 61 sources, 0 failures. Networked entities 494 (budget 501). No error finding left after the fixes of check1 (NAV_FLOATING on the
bins, spawners facing the partition, nav islands). Still open: the answer says `ok: false` (cause not yet read), and two warnings
`WALKABLE_OFF_NAV` in the arcade (Needle Drop x -2832..-2656, y 4352..4480: the bins and counter area; Copy Stop x -2224..-2112,
y 4416..4464: between counter and pigeonholes) - next step is to widen those passages.

## Resume
1. Read why `ok` is false: `python -m studio check C:\studio-data\sz\film\arcade\shell\doc` (from `C:\studio`, `STUDIO_ROOT=C:/studio`), fix the
   two WALKABLE_OFF_NAV areas, rebuild with `python tools-source/iwzmap/station_zero/film/arcade_shell.py`.
2. Then pass 1's live session (sense first): `python -B C:\forge\forge.py sense`, then `python -m studio live start <doc>` in the background,
   power on/off shots of the 15 cameras, sheets under `C:\studio-data\sz\film\arcade\shell\pass1\`.
3. Score with `python film/arcade_score.py`, then the report of the brief.
