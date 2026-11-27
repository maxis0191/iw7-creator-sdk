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

## Pass 1 (live, 27 Nov 22:32): `C:\studio-data\sz\film\arcade\shell\pass1\sheet_{on,off}_{0,1,2}.jpg`
- ON equals OFF pixel for pixel (mean luma 4.5 / 8.4 / 7.4 at three cameras in both): `cp_iwz_darkness.gsc` (lines 196-205) releases
  the dark vision only inside its loop over power banks, and an all-baked map has no bank. Not mine to change; logged in TOOL-FAULTS with
  the change needed. From pass 2 the lit look is shot on a settings-only variant (`film/arcade_litview.py`: its dark vision = the lit
  vision), labelled LIT, never ON. A variant synced into the open session failed ("the map did not come back after the reload"), so each
  state has its own session (`film/arcade_pass.ps1`).
- Ten largest differences from `concept/arcade.png` at `arc_east_long`, in order: (1) the hall near black, light intensities as stored 0.2
  to 1.0; (2) fascias dark plates, the target's are lit boxes; (3) ceiling a black lid with 7 small lit panels, the target's grid is
  bright with a few holes; (4) the directory outside the entrance view; (5) the left wall near the entrance empty, the target runs ad box,
  directory, phones, column; (6) the polisher far away, the target's is the foreground subject; (7) shop interiors dim (same cause as 1);
  (8) the wall's orange band invisible; (9) columns black pillars; (10) banner and bunting dim in the middle distance.
- Round 1 fixes, in that order: `LIGHT_K` 2.5; fascia pictures emissive (1.4); 12 live panels; directory at x -1560 and the phones at
  x -1790..-1688, beside the entrance; polisher and its circle at (-1590, 3850), socket at x -1650; Heel & Key's front gets two tungsten
  bulkheads; `arc_east_long` eye at (-1262, 3700), yaw 172; the Needle Drop oblique camera (it stood outside the hall) mirrored.

## Pass 2 (live, lit-vision variant): `C:\studio-data\sz\film\arcade\shell\pass2\sheet_lit_{0,1,2}.jpg`
The first readable set: fascias read as lit boxes from the entrance, the four shop hues are distinct (Needle Drop amber, Copy Stop cold
white, Hole Number Nine pink, Heel & Key tungsten), the white tile with its orange band and the colonnade read, the directory is the first
thing on the left. Its dark frames failed (the document was rebuilt under the session; my error, reshot in pass 3).
Differences left from the target, largest first, and round 2: (1) floor large plain orange squares -> our own quarry tile
(`film/tiles.py`, 12-unit mottled brown and burnt-orange tiles, glossy, through `B.material`: `w/sz_arcade_quarry`); (2) a column in the
middle of the entrance view -> eye at y 3880; (3) shutter curtains read as rows of white plates -> `w/cp_disco_metal_door_rollup_01`;
(4) the pegboard read cyan -> our brown pegboard `w/sz_arcade_pegboard`; (5) the ceiling still sparse and white against the target's
greenish grid (kept: the brief's half-dead ceiling).

## Pass 3 and pass 4 (round 2 and round 3)
- Pass 3: `pass3\sheet_lit_{0,1,2}.jpg` (lit-vision variant) and `pass3\sheet_off_{0,1,2}.jpg` (the document, dark vision). The entrance
  view takes the target's composition: ad boxes on the tiled wall with its orange band, the colonnade, the polisher in its circle in the
  foreground, the banner, the fronts on the right with readable lit fascias, the mottled quarry floor. Dark: near black with the fascias,
  light boxes and shop glows readable.
- Round 3: lit panels `w/emissive_light_panel_white` and greenish soft spots; floor gloss 205..235. Pass 4: `pass4\sheet_lit_*`,
  `pass4\sheet_off_*`, side by side with the target `pass4\compare_east_long.jpg`. The panels read brighter; the floor's sheen did not
  visibly change (the session's lightmap is a draft bake). Pass 4's dark half was not shot: my start waited for a client slot held by another worker's session and I cancelled it; the latest dark frames are pass 3's (the document then differed by the round 3 panel material and floor gloss only).

### What still differs from the target (pass 4, honest)
1. The shops are empty: the goods are the A3 workers' (anchors.json). The target's fronts are full and lit by their goods.
2. The floor is matte: the target's is wet, mirroring the fronts' colours. Ours is glossy in its gloss map, but the reflection probes of
   this base do not show it; not solved.
3. Proportion: the target is a corridor about half as deep as PLAN's 800-unit hall, so its fronts fill the right half. Ours keeps PLAN's
   box; the hall reads larger and emptier.
4. Light: the target's colour spill from the fronts onto the floor is strong. Ours is darker and lower in contrast (draft bake, auto exposure
   of the lit vision).
5. Ceiling: the target has many greenish panels. Ours keeps the brief's half-dead grid (12 live of 27 lit-capable), white, on a busy stock
   tile texture.
6. Bunting: the target's strings swag across the hall. Ours are flat picture strips seen as loose triangles from below.
7. The polisher is smaller and plainer than the target's, and its cable is not seen from the entrance eye.
8. The directory and phones stand beside the entrance (behind the entrance eye); the target shows them in the same frame as the fronts.

## Round of 28 Nov: the goods merged, the hall against the stock frames
Built and shot from now on: `film/arcade_doc.py` (shell + the four goods layers), document `C:\studio-data\sz\film\arcade\shell\docall`,
this worktree's SDK (`STUDIO_CONFIG` = `C:\studio-data\sz\film\arcade\shell\studio_a2.json`, `IWZ_SDK` = the worktree root: the darkness fix
releases the dark vision on an all-baked map), real ON and OFF (`film/arcade_pass.ps1`); the lit-view copy is retired.
- Requests done: Heel & Key shutter at 0.2 (bottom z 120, clip with it), a warm downlight over the stall, the lasts shelf's south end
  panel removed; Hole Number Nine `arc_hole_nine_inside` at (-1730, 4440, 66) yaw 200, its downlight moved to y 4360 and aimed at the rack
  front (no new light); Copy Stop `pb_seat` removed, `cs_planchest` to y 4392, copier bodies 44 high with a document feeder and the green
  bar at z 47 (anchor `copy_stop.copier_N_top` follows, z 50.2).
- The hall (`film/shell_hall.py`): two bench islands on the centre line (benches back to back, box planters with dead stems: no dead potted
  plant exists in the five zones, `com_potted_plant_small_des` reads green), a bin each; a shuttered newsstand kiosk in the colonnade
  (modelled: closed roll shutter, blank fascia, two magazine racks, newspaper bundles); four luggage lockers on the south wall; two hanging
  Halcyon Rapid Transit signs without words (PIL pictograms: arrow + train, arrow + stair; the roundel on the back).
- The night it stopped, three clusters: the gala buffet by the banner (folding table, glasses, balloons tied to its leg, a dropped dead
  bouquet, streamers), the toast under the banner (glasses and cups round the second island), the rush to D4 (streamers trampled toward the
  door, a bouquet, papers; all of it west of the door's 90-deep mouth). No party hat or streamer model exists: streamers are authored strips.
- A year of damp: water marks under two dead panels (floor and ceiling), the damp foot of the south wall in three places, worn tiles where
  a bench and the lockers rub the wall, tracked dust in the shop lane.
- Fronts by models: bulb strips under the Copy Stop, Hole Number Nine and Heel & Key fascias (emissive props: no light record; Needle Drop
  keeps its two marquee fixtures), and one spot of each shop's own colour from under its fascia onto the tile in front (four rows that
  differ: rule 11; hall hue classes white, warm, red, magenta: rule 12).
- Floor gloss 236..252 (was 205..235).

## Decisions the brief did not dictate
- **Tile kit** (one table `MAT` at the top of the builder, the swap to `B.material` is one edit there): wall `w/dt_tile_ceramic_white` with its
  true twin `w/dt_tile_ceramic_white_dmg` (the cp_disco station's pair; the base tint `w/iwz_tile_cream` has no damaged twin), band
  `w/ceramic_tile_01_orange` (from mp_depot), dark `w/fac_tile_black_01`, floor our own `w/sz_arcade_quarry` since round 2 (`film/tiles.py`; the stock
  `w/linoleum_floor_tiles_orange_01` before). Heel & Key's pegboard is our own `w/sz_arcade_pegboard`.
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
