# A2: the Underpass Arcade shell (worker A2, 27 Nov 2026)

## Resumed (27 Nov, after the pause)
- `ok: false` had one cause: three back-room spawners 18 units from a side wall stood on no navigation cell (`emit.problems`). They now stand
  34 from it, facing along the room (the emergence carries a zombie 62.5 forward; the rooms are 92 deep). `check`: ok, reach 61 of 61.
- `WALKABLE_OFF_NAV` (players can stand there, zombies cannot reach them): bisected by dropping clip boxes one at a time. Copy Stop: the
  service counter and the pigeonholes on the partition left a 56-unit corridor without nav cells; the pigeonholes moved to the east wall.
  Needle Drop: the record bins' clip island.

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
