# C - Inventory of the current Station Zero (cp_iwz), 2026-11-10

Read-only research. Nothing was launched, built, generated or committed. Sources:

- SDK `origin/main` (fetched 2026-11-10), repo `<products>/iw7-creator-sdk`, read with
  `git show origin/main:<path>`. Paths below are relative to that repo. Line numbers are those of the `origin/main` blobs.
  `S2` = `tools-source/iwzmap/station_zero2.py` (3413 lines), `GSC` = `tools-source/iwzmap/cp_iwz2.gsc` (613 lines),
  `BK` = `brushkit.py`, `MG` = `mapgen.py`, `MAT` = `sz2_materials.py` (all in `tools-source/iwzmap/`).
- Recorded generator OUTPUT of real builds (so counts are exact, not estimated): `<runtime>/iwz-stage2\`
  `level\src_g27dw\{layout.json,plan.json,surfaces.json,smodels.txt,world.bin,plan_check.json}` and
  `darkness\src_d16\...` (latest, darkness build on the g27e source). I parsed those files with a script
  (scratchpad `stats.py`, `stats2.py`). I did NOT re-run `station_zero2.py`.
- Stage notes read: `iwz-stage2\CONTEXT.md`, `LEVEL-DESIGN.md`, `level\NOTES.md` (l.740-806), `gameplay\REPORT.md`,
  `gameplay\REPORT-g27.md`, `gameplay\stock-spawn-recipe.md`, `art\REVIEW.md`, `train\REPORT.md`, `vision\g27d\CONSOLIDATED.md`,
  `vision\g27d\review-A.md`, `review-B.md`.

**Which build is "the current map".** The judged numbers (264 surfaces, ~170 props) are exactly build **g27dw**
(`world.bin`: 264 surfaces; `smodels.txt`: 170 static models). The newest recorded build is **d16** (darkness build on the g27e source):
257 surfaces, 193 static models, 431 decor entries, 138 lights, 10,314 nav cells. The two differ only in details; the layout, zones,
doors, spawners are identical. Numbers below are g27dw unless marked d16. The generator needs environment flags to produce this
look (see 2.9): with no flags set it makes a plainer map (no train, no kit models, no darkness).

**Unit scale.** 1 unit = 1 inch. Evidence: standard rail gauge written as 56.5 units (S2:1241), player about 72 tall and
steps <= 18 (`LEVEL-DESIGN.md` l.8), and `sz2_density.py` states "1 m = 39.37 units". x east, y north, z up. 1 nav cell = 32 x 32 units
(S2:57). m2 below = units2 x 0.0254^2. Ticket-hall ceiling 320 units = 8.1 m.

---

## 1. Rooms and areas of the current layout

### 1.1 Totals (g27dw, from the recorded files)

| Item | Count | Where |
| --- | --- | --- |
| Zones (script spawn volumes) | 9 | `layout.json` `zones`; S2:61-71 |
| Walkable nav cells | 10,306 = 10,553,344 units2 = **6,808 m2** (d16: 10,314 / 6,813 m2) | `plan.json` cells |
| Whole footprint | x -3600..3800, y 1200..4600, z -424..326 (world.bin bounds, plus dead tunnel to x -4000) | `world.bin` |
| Render quads / surfaces / materials | 6,728 quads, **264 surfaces** (material x zone), 94 materials, 26,912 vertices (double sided, so 13,456 unique triangles) | `surfaces.json`, `world.bin` |
| Decor entries | 399 = **170 compiled static models** (`smodels.txt`, 41 distinct models) + 229 `script_model` entities (kit / ported / door-dressing models) | `layout.json` `decor` |
| World-geometry "props" (handrails, ribs, pilasters, cordon posts...) | 107 (`geo_props`) | `layout.json` |
| Signs/posters | 46 (`signs`); decals 34 | `layout.json` |
| Lights | 137 records (88 `power`, 44 `emergency` incl. 24 amber `hint_glow` cues, 5 `flicker`) | `layout.json` `lights`, `light_groups` |
| Zombie spawners | 56 (39 ground, 11 wall vent, 6 ceiling) + 19 `dog_spawner` + 18 `player_respawn_loc` + 4 player starts | S2:2629-2670 |
| Doors | 5 debris doors: 750 x2 (hall-stair_a, stair_b-hall), 1000 x2 (platform-corridor, platform-tunnel), 1250 x1 (generator-control); plus 5 free arches and 4 open gaps | S2:81-117 |

For scale, Spaceland (cp_zmb, the template map) has 10,760 surfaces, 17,010 static models, 1,039 primary lights, 403,042 triangles
(`docs/WORLDKIT.md` l.102-107). Station Zero has 2.5 % of its surfaces, 1.0 % of its static models, 13 % of its lights, 3.3 % of its triangles.
One 483-prop box over the Spaceland player start (`docs/WORLDKIT.md` l.36) holds ~2.8x the static models of the whole station.
Trim strips are 64 % of the quads: steel_trim 2,581, ibeam 883, rubber_trim 432, frame 180, chrome_trim 126, molding 112 of 6,728 (`surfaces.json`).

### 1.2 Zone table (x/y box = nav/volume box in S2:61-71; dimensions are room interiors read from the `room()` calls)

| # | Zone (spaces) | Position (x, y) and size | Heights (z) | Walkable area (cells, m2, share) | Style / main materials |
| --- | --- | --- | --- | --- | --- |
| 1 | `ticket_hall` (hall + `street` alcove) | hall x -1200..400 (1600), y 3200..4400 (1200), street alcove x -304..112 (416), y 4400..4600 (200). S2:1065, 1085 | floor 0, ceiling 320; street alcove: 6 collapsed steps of 16 rising to 96 (S2:1086-1087) | 1619 cells, 1,070 m2, 15.7 % | `metro` bands: rubber trim, charcoal tile to 112, steel trim, white tile, molding (S2:147-150); floor `checker` marble + `tile_black` grid; ceiling `ceil_tile` + I-beams every 400 |
| 2 | `stair_a` | x -800..-400 (400), y 2416..3184 (768) | 0 down to -320 southward, 20 steps (rise 16.0), 64-unit landings (S2:1118) | 287 cells, 190 m2, 2.8 % | `metro` tile, conc_floor treads, steel handrails |
| 3 | `platform_a` (deck + track pit + 2 stair wells + east tunnel mouth + hero car) | x -2400..2400 (4800). Deck y 1600..2400 (800; 1566 with train edge), pit y 1200..1600 (400). Wells x -2400..-2192 and 1904..2112, y 1600..1760. East mouth x 2400..3000, y 1216..1584 (visual only). S2:1129-1333 | deck -320, pit -384, ceiling 0 (320 above deck); mouth throat springline -184, crown -128 | **5041 cells, 3,330 m2, 48.9 %** | `metro` walls over `track` base (conc_dark 64 high), deck `conc_tiles` + yellow_grip edge, pit `conc_warm`; I-beams every 256; 8 tiled columns |
| 4 | `maint_corridor` (L: corridor_a + corridor_b) | a: x 2416..3200 (784), y 1680..1920 (240). b: x 2960..3200 (240), y 1920..2384 (464) | -320..-96 (224) | 244 cells, 161 m2, 2.4 % | `maint`: panel_dark, beam_yellow stripe, conc_seam; floor conc_dark; ceiling corrugated |
| 5 | `generator_room` | x 2600..3800 (1200), y 2400..3184 (784) | -320..32 (352) | 751 cells, 496 m2, 7.3 % | `maint`; floor deck_black; corrugated ceiling; yellow floor grid |
| 6 | `control_room` (+ `pap_alcove`) | control x 2600..3600 (1000), y 3200..4000 (800); alcove x 2976..3232 (256), y 4016..4160 (144) | control -320..-32 (288); alcove ceiling -112 (208) | 731 cells, 483 m2, 7.1 % | `control_neutral` (panel_dark, steel trim, panel_wall); alcove `control` (red-tinted panels), diamond-plate floor |
| 7 | `service_tunnel` (L: tunnel_a + tunnel_b; dead west stub) | a: x -3600..-2416 (1184), y 1216..1584 (368). b: x -3600..-3216 (384), y 1584..2584 (1000). Dead stub x -4000..-3600, y 1376..1584 (not walkable, closed by collapse). S2:1439-1441, 1472-1485 | -384..-96 (288); throat crown -124 | 595 cells, 393 m2, 5.8 % | `tunnel`: conc_dark, conc_seam, I-beam rings every 320 |
| 8 | `platform_b` ("old station") | x -3600..-2064 (1536), y 2600..3400 (800). Sunk trench x -3600..-2300, y 3200..3400, bed -424 (S2:1508) | -384..-32 (352) | 799 cells, 528 m2, 7.8 % | `old`: wood_green dado, brick_white, wood trim; floor herringbone; ceiling deck_black |
| 9 | `stair_b` | x -2048..-1216 (832), y 3104..3400 (296) | -384 up to 0 eastward, 23 steps (rise 16.7) | 239 cells, 158 m2, 2.3 % | `metro_cream`: tile_green dado, tile_cream |

Spawn-volume boxes (S2:61-71, x0 y0 z0 - x1 y1 z1): ticket_hall -1200 3200 -16 - 400 4600 336; stair_a -800 2400 -336 - -400 3200 304;
platform_a -2400 1200 -400 - 2400 2400 16; maint_corridor 2400 1680 -336 - 3200 2400 -80; generator_room 2600 2400 -336 - 3800 3200 48;
control_room 2600 3200 -336 - 3600 4160 -16; service_tunnel -3600 1200 -400 - -2400 2600 -80; platform_b -3600 2600 -400 - -2064 3400 -16;
stair_b -2064 3104 -400 - -1200 3400 304. One axis-aligned box per zone; no zone lies above another (nav keeps one height per 32-unit cell:
`LEVEL-DESIGN.md` l.8-9), so the map is one storey of side-by-side rooms joined by stairs.

### 1.3 Zone graph (text)

```
START: ticket_hall (4 player starts at x -700..-280, y 3880, S2:2624; INITIAL_ZONES = ['ticket_hall'], S2:72)
ticket_hall --[DOOR d_hall_stair_a 750, x -696..-504 on wall y 3200]--> stair_a  ==link(no door)==> platform_a
ticket_hall <--[DOOR d_stair_b_hall 750, y 3216..3392 on wall x -1200]-- stair_b
platform_a --[DOOR d_platform_corridor 1000, y 1704..1896 on wall x 2400]--> maint_corridor ==open bend==> corridor_b
      corridor_b --[ARCH a_corridor_generator, free]--> generator_room  (maint_corridor==link==generator_room: zones activate together)
      generator_room --[DOOR d_generator_control 1250, x 3004..3196 on wall y 3184]--> control_room
      control_room --[ARCH a_control_pap, 256 wide, closed by PaP shutter until the 3 relays are on]--> pap_alcove
platform_a (pit level) --[DOOR d_platform_tunnel 1000, y 1392..1584 on wall x -2400, the whole track channel]--> service_tunnel (tunnel_a ==open bend==> tunnel_b)
      service_tunnel --[ARCH a_tunnel_platform_b]--> platform_b (service_tunnel==link==platform_b)
      platform_b --[ARCH a_platform_b_stair_b]--> stair_b (platform_b==link==stair_b)
Loop: hall -> stair_a -> platform_a -> tunnel -> platform_b -> stair_b -> hall.   Branch (dead end): platform_a -> corridor -> generator -> control -> PaP.
Street exit (north of the hall, o_hall_street, free) = collapsed stairs, zombie entry only.
```
Doors/arches: S2:81-117 (14 openings: 5 doors, 5 arches, 4 open). Zone links with no door: S2:74-75 (`stair_a`-`platform_a`, `maint_corridor`-`generator_room`,
`service_tunnel`-`platform_b`, `platform_b`-`stair_b`); the level script activates both zones when one is active (GSC:131-168). Each door gets two
`interaction` structs plus a `trigger_use door_buy` (S2:2856-2886), tiled `script_brushmodel` blockers (24 brush models in total over the 5 doors and the PaP shutter, `layout.json blockers`), and, with the kit flag,
16 boards + 2 street barricades of door dressing per door except the tunnel door (S2:2938-2974; GSC:578-613 removes the dressing when bought).

Opening sizes (`layout.json openings`): hall-stair_a door 192 x 224; stair_a arch 368 x 256; platform-corridor door 192 x 208; corridor bend 208 x 224; corridor-generator arch 176 x 208;
generator-control door 192 x 224; platform-tunnel door 192 x 224 (track width); tunnel bend 384 x 288; tunnel-platform_b arch 272 x 256; platform_b-stair_b arch 264 x 256;
stair_b-hall door 176 x 224; hall street 416 x 320; control-PaP arch 256 x 184; west dead tunnel 208 x 256.

**Total playable area estimate:** 6,808 m2 of nav (10,306 cells). About 49 % of it is `platform_a`, and ~1,240 m2 of that is the track pit
(4800 x ~400 units). Excluding the pit and the two wells, walkable "rooms and corridors" are about 5,500 m2. Route length hall -> PaP in cells is not stated; a walk
test route exists (`layout.json walk`, 59 waypoints).

### 1.4 Room by room (g27dw counts; props = `layout.json decor` entries, "static" = compiled static model, "ent" = script_model entity)

Lights in this section = layout light records without the 24 amber `hint_glow` interaction cues (113 + 24 = 137).

**ticket_hall** (S2:1063-1112, 1750-1759, 2168-2335 decor). Props 75 (25 static, 50 ent): 16 door planks, 13 animated turnstiles (cp_disco kit) +
2 missing-arm turnstiles, 7 rubble piles, 6 worn subway benches, 6 street barricades, 4 trash bins, 6 candles (memorial), 3 emergency lights, 2 traffic cones, ticket booth
(BO3 zm_zod port), vending machine (port), newspapers, backpack, biohazard sheet. Also 11 collision-only turnstile boxes in a row at y 3700 (S2:2168-2171), a
railing with a service gate, 3 columns at x -800/-400/0 (S2:1072-1073), 12 ceiling strip fixtures (x -1000/-600/-200/200 by y 3400/3800/4200, one dead) + 1 over the street exit, ad frames, pilasters,
sign "STATION ZERO" over the street exit, network map, departure board art, 17 signs/posters, blood story drag decals. Gameplay: Up'N Atoms (revive) perk at (370, 3460, 0);
revolver wall buy (-1184, 4100, 64); magic wheel (380, 3300, 0); 7 spawners (4 ground, 2 wall, 1 ceiling); 3 dog spawners; doors to stair_a and stair_b. Connections: street alcove (free), stair_a door, stair_b door.
Lights 15 (12 power, 3 emergency). Collapsed street stairs + collapsed ceiling patch (S2:1769-1776).

**stair_a** (S2:1114-1126). Props 0 (decor), 1 sign, 4 strip lights. One 20-step straight flight, plain side walls and ceiling; 6 spawners (5 ground, 1 ceiling); UMP45 wall buy (-784, 2600, -180).
Handrails 10 geo props. Connects: hall (door) above, platform_a (free arch) below.

**platform_a** (S2:1128-1333, 1824-1985). Props 143 (41 static, 102 ent): 34 platform-edge panels (BO3 mp_metro port, 128 long) + 1 x 64, 25 track segments (256 long, 21 + 4 disused/special), 3 coupled
subway cars (BO3 mp_banzai port, `iwz_t7e_subway_car_a`, centres x 1205.5 / 1739.5 / 2273.5, y 1488, one 533-long car each; only the westmost is walkable), 16 door planks, 9 electrical boxes,
8 rubble piles, 5 trash bins, 5 broken fluorescents in the cars, 4 worn benches, 4 duct vents, 4 barricades, 4 emergency lights, 3 loudspeakers, luggage (5 BO3 pieces), fire-hose cabinet and help point (BO3 ports), 2 clocks. 8 tiled columns at x -1792..1792 every 512 (S2:1233), ad frames on pilasters every 320, 3 hanging signs, 20 signs/posters.
Lights 40 without the amber cues (43 records with them: 34 power, 8 emergency, 1 flicker). Gameplay: Tuff 'Nuff perk (1100, 2370, -320); M4 wall buy (-1250, 2384, -256); start-location magic wheel (600, 2380, -320);
Third Rail trap fuse box (-768, 1975, -300); relay 1 on a column (768, 2027, -300); EE teddy bear in the hero car (1425.5, 1448, -323); door to maintenance corridor (east) and to service tunnel (west, pit level);
8 spawners (6 ground, 2 wall) + 4 dog spawners. East tunnel mouth (x 2400..3000) is a dark curved-lining tunnel ending in a collapse, visual only (clip closes it at x 2410: S2:1215-1230).
Connections: stair_a arch, 2 wells (6 steps of 10.7 into the pit), door east, door west.

**maint_corridor** (S2:1335-1356). L corridor, 161 m2. Props 19 (16 static): 3 electrical boxes, 2 lockers, 2 emergency lights, 2 fans, 2 shutoff panels, 2 cardboard boxes, drum, trash bag, paper, pipes, ladder, ammo crate.
Wall ribs every 200, 2 red pipes, 2 cable trays, 4 wall lamps, yellow floor grid. 6 spawners (4 ground, 1 wall, 1 ceiling), 2 dog spawners. Lights 6. No perk, no wall buy. Connections: door west (platform_a), open bend, arch to generator.

**generator_room** (S2:1358-1388, 1691-1725). 1200 x 784. Props 55 (21 static): 16 door planks + 4 barricades (door to control room), the G-2 generator set (BO3-style port `iwz_g2_genset` at (3469, 2793, -320)) with radiator, 4 lockers, 3 drums, 3 ammo crates, 3 electrical boxes,
2 fuse boxes, 2 oxygen tanks, workbench, fire-hose cabinet, ladder, burn drum with fire FX. Maintenance catwalk on the east wall (visual only), pipes, 2 hanging work lights, hazard markings, cordon around the G-2.
Gameplay: power switch (3500, 2420, -270); Racin' Stripes perk (2630, 2900, -320); shotgun wall buy (3784, 2700, -256); relay 3 (3660, 3180, -260); 6 spawners (4 ground, 2 wall), 2 dog spawners; door to control room (1250). Lights 10.

**control_room + pap_alcove** (S2:1390-1421). Props 23 (22 static): 3 signal desks of 240 x 80 each with 2 lab desks, 6 CRT monitors, 3 consoles, 3 folding chairs (tipped), 2 filing cabinets, radio, test-pattern TV, paper. Evacuation/signal diagram art,
panel wainscot + 8 pilasters, 3 red-tinted wall lamps. PaP machine at (3104, 4100, -320) in the alcove (needs power), hidden behind a two-gate rolling shutter (S2:3037-3042, `gate_warehouse_refinery_01`) opened by the quest.
6 spawners (4 ground, 1 wall, 1 ceiling), 2 dog spawners. Lights 12.

**service_tunnel** (S2:1423-1501, 1680-1688, 1726-1747). Props 41 (33 static): 10 rubble piles, 8 electrical boxes, 4 + 1 + 1 track pieces, buffer stop at x -3560, 3 cones, 2 junk tires, scrap, crates, oxygen tanks, trash bag, tarp.
I-beam ceiling ribs every 320 and matching wall rings, 2 conduit pairs, cable trays, yellow safety line, a dark curved "throat" x -2896..-2416 with a red signal head (S2:1447-1455) and a collapsed dead tunnel west (x -4000..-3600). 0 signs.
6 spawners (4 ground, 2 wall), 2 dog spawners. Lights 19 without the amber cues (20 records: 14 power, 4 emergency, 2 flicker). No perk, no buy. Connections: pit door (east), arch to platform_b.

**platform_b** (S2:1503-1590). Props 23 (12 static): disused track in a sunk trench (4 + end piece + buffer sleepers), BO3 ticket booth (-3300, 3050, -384), 2 planks, bags, trash bin, bench, cones, barrier, rubble, paper, emergency light.
3 boarded windows on the north wall (generated steel frames + planks), bricked tunnel mouth on the west wall with layered "closed" notice, wood/brick walls. Bang Bangs (rat-a-tat) perk (-3570, 2800, -384); M1C wall buy (-2640, 2616, -270); magic wheel (-2100, 3000, -384); relay 2 at the booth (-3300, 2986, -340).
6 spawners (4 ground, 1 wall, 1 ceiling), 2 dog spawners. Lights 4 (1 power lamp: "the one bare light of the old station", S2:1523). Connections: arch from tunnel, arch to stair_b.

**stair_b** (S2:1592-1600). 23-step flight rising east to the hall door. Props 20 (all door dressing: 16 planks + 4 barricades). 5 spawners (4 ground, 1 ceiling), 1 dog spawner. Lights 3. No signs.

---

## 2. What the generator can express

### 2.1 Primitives (BK, S2)

- Everything is **axis-aligned in plan** (x/y), z up. `Builder` (BK:39-146) owns a mesh and nav blockers. Primitives: `quad` (explicit uvs or world-aligned uvs from the material's texture world size, BK:51-93);
  `box` (6 faces, per-face material dict, optional collision, BK:116-146); `slab_x` / `slab_y` (thin protruding box, BK:148-155); `wall_plane` (one vertical rectangle, BK:158-173);
  `wall_sloped` (vertical quad with sloping top/bottom, stair side walls, BK:175-187); `collision_quad`, `collision_box` (BK:95-114); `spans_minus` (BK:190-202).
- **Walls** are banded stacks (floor to ceiling) per style: `metro`, `metro_cream`, `maint`, `old`, `tunnel`, `control_neutral`, `control`, `track`, `brick`, `plain` (S2:145-173), with door/arch/open
  openings cut out, frames (10 wide, 4 deep) and reveals (S2:179-253). Walls are 16 thick between neighbouring spaces (S2:56).
- **Rooms** are flat rectangles: `room()` = floor + ceiling + 4 banded walls (S2:264-280). **Stairs** are straight only (`straight_stair`, S2:731-891): render steps, a smooth collision ramp,
  optional stringers and side walls; stair clip variants by `IWZ_STAIR_STYLE` (S2:724-727, tags 382/411/387/402).
- **Curved shapes exist only as render lining**: `tunnel_throat` bends the side walls into a flat crown by a 6-segment quarter circle plus rings (S2:933-999); collision stays the rectangular box.
  Also `oriented_slab` (leaning rubble slabs), arches are rectangular frames (no curved arch).
- **Details**: `strip_light`, `wall_lamp` (S2:335-408), `sign`, `hanging_sign` (S2:411-486), `decal_floor`, `decal_wall` (S2:506-544), `column` (S2:547-554), `floor_grid`, `drains`, `ceiling_grid`,
  `pilasters`, `ad_frame`, `wall_niche`, `cable_tray`, `rail_run`, `conduit`, `junction_box`, `signal_head`, `rubble_end` (S2:557-1061), `flicker_lamp` (S2:686-689).
- **No** sloped walls in plan, no round rooms, no multi-storey overlap, no domes, no terrain, no arbitrary mesh authoring from the generator itself. Surface meshes lifted from stock maps "have no consumer yet" (`docs/WORLDKIT.md` l.118-119).

### 2.2 Props: how they are placed and which models

- `decor()` (S2:1797-1805) records a stock/kit model with origin, yaw, optional pitch/roll and an optional collision half-box (`clip`) that also cuts the navmesh. Output as `script_model` entities (ents.txt) or, with `IWZ_SMODELS=1`,
  as compiled static models in `smodels.txt` (S2:3046-3081): static = drawn without entity cost, bullet-blocking; player/zombie blocking still comes from the decor clip boxes. Models without a stock static donor stay entities (S2:3048-3063).
- `place_ported()` (S2:1987-2014) places authored/ported models from a JSON spec (`IWZ_TRAIN_PROPS`) with their model-space clip boxes turned by the yaw.
- Model sources: (a) the template zone cp_zmb (free: loaded already); (b) kit import from other stock zones cp_disco / cp_final (`kit_import.py`, `IWZ_KIT=1`; README l.161-182); (c) ported/authored models from the T7/BO3 env-model pipeline,
  `iwz_*` (train report: BO3 mp_banzai car, zm_zod wheels and ticket booth, zm_cosmodrome sleeper and fluorescents, mp_metro platform edges, gravel and luggage, IW7 mp_rivet buffer; `train\REPORT-e3.md` l.82).
- **Model names placed in g27dw** (41 distinct static + entity models; counts over all zones):
  - Stock cp_zmb: `debris_concrete_rubble_pile_01_dark` 27, `electrical_control_box_03` 23, `trashbin_01_iw6` 10, `traffic_cone_sml_01` 7, `com_trashbag2_black` 7, `zmb_tv_crt_01` 6, `lab_desk_02` 6, `p7_box_cardboard_a_closed` 6, `com_debris_paper_iw6_02` 6, `ammo_crate_01_dust` 6, `sign_clock_04` 5,
    `equipment_oxygen_tank_01` 4, `emergency_shutoff_sm_panel_01` 4, `duct_metal_rectangle_vent` 4, `sdf_console_control_panel_08` 3, `p7_candle_01/02` 6, `misc_wall_mounted_loudspeaker_01` 3, `misc_wall_mounted_fan_01` 3, `ind_debris_metal_scrap_04` 3, `chair_folding_iw6` 3, `wall_mounted_pipes_01` 2,
    `misc_zom_duffelbag_03` 2, `ladder01_large_closed` 2, `furniture_filing_cabinet` 2, `fac_sort_machine_fuse_box_set_01` 2, `dns_locker_set_01` 2, `com_junktire` 2, `barrier_pedestrian_01` 2, `zombies_backpack_dropped(_red)` 2, `zom_machinery_generator_portable_01`, `zmb_frequency_device_radio`, `office_paper_stack01_iw6`,
    `mp_dart_workbench_01`, `fac_trash_bin`, `equipment_old_computer`, `dns_fence_tarp_01`, `cup_paper_open_iw6`, `container_coffee_mug_01`, `com_tv2_testpattern`.
  - Kit from cp_disco / cp_final (script_model entities): `cp_disco_subway_turnstyle_animated` 13, `cp_disco_worn_subway_bench` 11, `cp_disco_street_barricade` 18, `cp_disco_subway_lockers_02` 10, `cp_disco_subway_turnstyle_missing_arm` 2, `clk_emergency_light` 15, `equipment_oil_barrel_military_01` / `com_barrel_tan_rust` (drums), `p7_zm_der_plank_wood_2x12x96` 66, `newspaper_single/stack_fn_01`, `ls_biohazard_sheet_01/02`.
  - Ported/authored `iwz_*`: `iwz_platform_edge_128` 34 + `_64` 1, `iwz_track_256` 21 (+ `_3r_from200`, `_disused` 4, `_disused_end`, `iwz_track_buffer_stop`, `iwz_buffer_sleepers`), `iwz_t7e_subway_car_a` 3, `iwz_fluo_subway_broken` 5, `iwz_g2_genset`, `iwz_g2_radiator`, `iwz_fuse_box` 2, `iwz_fire_hose_cabinet` 2, `iwz_help_point`, `iwz_zm_zod_ticket_booth` 2, `iwz_machine_vending_food`, 5 `iwz_luggage_*`.
  - Models placed by the quest/power/door tables (not in `decor`): `icbm_electricpanel9_off/on`, `beacon_light_plasticcase_red_on/off`, `icbm_electricpanel_switch_02`, `gate_warehouse_refinery_01` (PaP shutter), `fac_sort_machine_fuse_box_set_01` (trap box), `weapon_*_wm` wall-buy models, `zmb_magic_wheel_spinner`, `mp_dart_lightfluo(_on)`, `iwz_fluo_subway_on/off`, `clk_wall_light_01(_on)` (dark build).

### 2.3 Materials and textures

- A material table `MAT.MATERIALS` (MAT:36-124): 80 base entries (+ 14 tinted clones, 10 signs, 3 posters, up to 5 story plates, 9 chalk boards, art-hook images), each = a **stock cp_zmb world material** (`w/<name>`, e.g. `dt_tile_ceramic_white`, `concrete_floor_polished_01`, `metal_painted_scratched_yellow`) with a texture world size (su/sv) so surfaces are mapped at real scale;
  trim textures are strip-mapped (MAT:23-25, BK:65-84). Unit = repeat length (tile_white 64, tile_floor 128, conc 256).
- **Custom materials** are written into the map zone by `sz2_assemble.py` (l.8-44): a stock material JSON cloned, then (a) **colour image replaced** (one colour texture only, semantic 2, `assert len(colour)==1`, l.24-27) and/or (b) colour tint / emissive / a named constant overridden.
  So: custom 2D art (signs, posters, notices, decals, chalk boards) = our TGA/DDS on a stock poster/decal base; tinted stock variants (`tile_green/charcoal/cream`, `lamp_cool/warm/red/green`, `panel_*_red`, `conc_warm`...) (MAT:137-190).
  **No custom normal, spec or gloss maps, no custom shaders.** Bases: `zombies_theater_poster01` (opaque art), `wall_stain_01_dec` (alpha decal), `emissive_light_panel_pink` (lamps) (MAT:138-139).
- **Engine-proven failures** (MAT:200-205): `puddle`, `blood_splat`, `yellow_line` render as opaque squares; `exit_sign` art unusable. The stock multiply floor stain (`dirt_water_stain_01`) renders as a black hole/hard shape, so floor stains are disabled by default (S2:508-528, `IWZ_FLOOR_STAINS=0`; `vision/g27d/CONSOLIDATED.md` item 2).
- 94 materials appear in the compiled world.bin for g27dw.

### 2.4 Lights

- Layout light records (`LIGHTS`: origin, colour, radius, intensity, fixture, group) are omni only in the generator (S2:335-408, 893). The **own baker** (`bake/lmbake.py`: charts, ray-traced direct light with soft shadows, cosine-gathered bounces, AO, BC6H/BC4 encode, README l.25, 50-71) writes the lightmap and the light grid.
  Real engine primary lights come with `IWZ_LIGHTS=1` (`lights.txt`, S2:3084-3100; only the red/green signal lamps and a bear fill light) or the darkness route (named scriptable lights, `light_spot` entities).
- Fixture + light pairs: `strip_light` (steel housing + diffuser + light 20 below, half of the fluorescents "dead" in clusters by the g25 mood pass, S2:326-345); `wall_lamp`; caged `clk_emergency_light` lamps with a painted lens and small light (S2:2119-2156);
  `flicker_lamp` (model swap, S2:686); 3 wheel downlights (S2:2784-2794). Fixture counts g27dw: lamp_cool 50, lamp_warm 33, hint_glow 24, emergency 15, lamp_red 5, flicker 5, train_interior 3, work_light 2.
- Light-grid ambient per zone (S2:61-71 `probe`; `lighting.txt` S2:3104-3110), neutral reflection-probe rooms per zone (`probes.txt` S2:3116-3127).
- No sun/sky edit (the template cp_zmb provides sun, sky, light grid and reflection probes; README l.4-6). No light-emitting particles other than the flashlight/FX route; baked emergency + power banks in the darkness build.

### 2.5 FX

- `fx_place.py` places stock and imported effects from a text file (README l.186-232): 20 FX placed in g27dw (`layout.json fx_placed`): hall motes/light cone, platform leak drips, tunnel fog/steam/dust, corridor steam, generator haze/barrel fire/embers/sparks/start-up smoke, control-room mist.
  Plus 2 legacy `vfx_zb_trash_a_ch` loops (S2:2678-2682). Engine findings (README l.220-226): sprite effects render; GPU particle clouds (`particle_cloud_*`, `vfx_zmb_dust_motes_md`) and `vfx_knee_high_fog_dark` never draw; thin drips are below the measurement threshold; effects must be in `ncs_efx_level.json`.
  Power stages `always / dark / lit / poweron`. FX cost measured +0.08 ms per frame (21 FX, dark; `level/NOTES.md` l.740ff).

### 2.6 Sound

- Own sound bank `cp_iwz.all` (`audio/station_zero_audio.json`: 60 aliases, stock + BO3 sources), 9 zone beds, **25 emitters**, 12 soundscape entries, loop caps 8 per zone / 36 total (`station_zero_audio_layout.json`), anchored to layout lights/decor/quest/interactions (`audio_layout.py`).
  Beds are per player, played by script (engine zone beds stay silent in a usermap). Music cues synthesized (`station_zero_music.py`). Hidden-song easter egg (BO3 teddy bear + "Abracadavre") via `song_ee_init`. Witnessed in game 2026-11-07 (audio README l.124-137).

### 2.7 Darkness kit (`darkness/`)

- `IWZ_DARK=1` + `dark_build.py` + `lmbake` on a dark light list: the map is baked **dark** with only the `emergency` group; `power` and `flicker` banks are named script-switchable lights (extends the template's 25 scriptable light slots) driven by `cp_iwz_darkness.gsc`:
  stock flag `power_on` -> 2.65 s -> one bank per zone from the switch outward, 0.8-1.3 s apart, tubes stutter 2-4 times, fixture models swap unlit -> lit (`iwz_power_fixture`, 40 in d16), `iwz_light_bank_on` notifies for audio/FX, flag `iwz_power_lights_done`.
  Dark vision (manual exposure -3) re-applied 8 s and 14 s after each spawn; lit vision with fog 0.03. Per-player **flashlight** (`cp_iwz_flashlight.gsc`): particle spot light on a carrier following eye + view angles (modes follow/link/tag), dimmed after power. d16 is the darkness build; g27dw is lit.
  Not proven as accepted: "the document does not give a final accepted-in-game date" (`docs/CREATION-TOOLS.md` l.21).

### 2.7b Train kit (`IWZ_TRAIN=1`, S2:1824-1985; `track_clearance.py`, `train_proof.py`, `train_perf.py`)

- **The train is static.** 1-3 coupled cars (`IWZ_TRAIN_CARS`, g27dw = 3 at x 1205.5/1739.5/2273.5) standing on the platform-A track, 26 track segments (256 long: 21 platform_a + 5 tunnel) with third rail, a buffer stop at x -3560,
  mp_metro edge panels along the deck edge (EDGE_Y 1566), a hero (westmost) car with a walkable interior through its open +y door bay (aisle region + door region on the nav, S2:1918-1920), one flickering tube + dim emergency lights, a cordon (2 posts + tape) at each door bay, "RUN 047" plate and "23:47" blind on the cab end.
  Other cars: dressing only, no walkable interior (S2:1907-1909). **Nothing moves**: no train arrival/departure script exists; scriptable movers of the stock train are removed on import (README l.181). Walking into the car works (player and zombie enter via the door bay: `gameplay/REPORT-g27.md` l.28; clip boxes block the walls).
  A parallel disused trackbed in a sunk trench on platform_b (S2:2078-2087). Frame time with kit shown/hidden: p50 1.71 ms, p99 4.34/4.46 ms (`train\REPORT.md`).

### 2.8 Collision, navigation, spawners, zones, triggers

- **Collision**: every quad with `collide=True` becomes triangles of one Havok hk_2014 compressed mesh (scale 1/32; `hkcm_write.encode`, S2:2814-2819; tag 382 solid; tags 411/387/402 for stock-style stairs). Decor clip boxes add boxes (S2:1800-1802). Trigger shapes: the generator writes one box per zone (`triggers.txt` S2:2723) or reuses template trigger models (`IWZ_VOLUME_MODEL=46`).
  A new trigger/brush shape needs a template model (`docs/MAPENTS.md` l.24-31).
- **Navigation**: `REGIONS` (rect + height or a function of x,y) become 32-unit cells (one height each, sloped corner heights for stairs), minus solid blockers (S2:2503-2525); a seam pass removes cells so that only designed links stay (S2:2533-2604); written as an IW7 `bfx` NavGraph version 0x2B (`mapgen.nav_graph`, MG:129-199; kd-tree, links when the step <= 18, one quad area per cell).
  No traversal/mantle/jump links, no window or barricade entrances. Known failure: zombies do not reliably climb the two platform wells (east 3/5, west 1/5 in g27d QA; 0/10 in the g27dw probe); unresolved at the 2026-11-09 pause (`level/NOTES.md` l.776-806).
- **Spawners**: `script_struct` `<zone>_spawner`, `script_noteworthy static`, kinds `ground` (`spawn_ground` + `ground_spawn_no_boards` + fx concrete), `wall` (`spawn_wall_low` + `no_boards`, a louvred vent grille is drawn, S2:2735-2760), `ceiling` (`spawn_ceiling`, vent in the ceiling) (S2:2826-2833).
  All spawners are the "no boards" variants: **no barricadable windows exist**. Specials: `dog_spawner` structs (2-4 per zone, S2:2659-2664), `brute_hide_org` at (0,0,-2000) (S2:2846), `zombie_idle_spot`, `player_respawn_loc` (2 per zone, S2:2666-2670).
- **Zones/triggers**: `info_volume` `spawn_volume` per zone, `script_linkname` = zone, `target` = `<zone>_spawner` (S2:2721-2725); 8 `player_use_trigger` (S2:2716-2718); `trigger_use door_buy` per door; `mp_global_intermission`. All entity key ids in `K` (S2:2611-2613).
- **Interactions** (stock IWZ systems, relocated scriptables): debris doors, `generator` power, 4 perk machines (all `requires_power`), 5 wall buys, 3 magic wheels, `weapon_upgrade` (PaP) (S2:2975-3003).
- Quest/trap/EE "spots" are data (`QUEST`, S2:2697-2707); logic lives in `GSC`.

### 2.9 Build flags (environment) that change what the map looks like

`IWZ_DOUBLE_SIDED` (MG:39), `IWZ_VOLUME_MODEL` (S2:2720), `IWZ_GALLERY` (S2:24), `IWZ_LM_TABLE` (S2:9), `IWZ_WELD` (176), `IWZ_CEIL_STAIR` (321), `IWZ_DIM` (326), `IWZ_DARK` (331), `IWZ_STAIR_STYLE` (724), `IWZ_WELL_SOLID` (727), `IWZ_TRAIN` (1135), `IWZ_TRAIN_CARS/_CONSIST_END_X/_TRACK_EAST_X/_EDGE_Y/_CAR_BOXES` (1136-1897),
`IWZ_TRAIN_PROPS` (909, 2069), `IWZ_KIT` (1789), `IWZ_SMODELS` (3046), `IWZ_STORY` (1767), `IWZ_ARCH4` (1630), `IWZ_ART5` (1692), `IWZ_NO_DECOR` (2017), `IWZ_DOOR_DRESS` (2871/2939), `IWZ_FLOOR_STAINS` (528), `IWZ_LIGHTS` (3084), `IWZ_FX_TXT` (2765), `IWZ_AUDIO` (3143), `IWZ_ART_DIR` (MAT:13).
The README build commands (l.43-58) and `build-sz2.ps1` (flags `-KitModels`, `-Darkness`, `-FxImport`, `-AudioSdk`) still carry the machine paths of the original runs.

### 2.10 What it cannot express (from the code and the docs)

- Anything non-axis-aligned in plan; round/curved collision (the curved tunnel throat is render-only); more than one floor above another zone; ramps other than straight stairs; moving world geometry (doors are template brush blockers made non-solid; shutters/gates are model `movez`; the train is static).
- New trigger shapes, new brush models, new collision for imported prefab surfaces: needs template shapes or a new zone (`docs/MAPENTS.md` l.24-31); prefab collision/nav are not extracted (`docs/WORLDKIT.md` l.114).
- Custom normal/spec/gloss textures or shaders; alpha-blend decals except the proven `wall_stain_01_dec` route; stock multiply stain decals; GPU particle clouds.
- Per-vertex lighting, umbra occlusion authored by hand (the map uses a generated conservative Umbra tome, `IWZ_GEN_TOME`), sun/sky/fog changes beyond vision settings.
- Window barricades/boards, traversals, fast travel/hidden rooms (parked entities only, S2:3018-3023), scripted boss arenas.
- Placing stock-map rooms: `iw7_world.py extract/place` writes `smodels.txt` (props) the compiler already takes; the surface meshes and lights of a prefab "have no consumer yet" (`docs/WORLDKIT.md` l.118-119).

---

## 3. The gameplay scripts that exist for the map (`GSC` = cp_iwz2.gsc; level script for v2)

| Feature | What the script does | Status (evidence) |
| --- | --- | --- |
| Init / stock wiring | `main()` GSC:3-73: registers zombie + brute + clown agents, `level.use_adjacent_volumes = 1`, `map_interaction_func`, stock Spaceland interaction/perk/PaP/wheel functions, last-stand weapon lists, relay/trap fx, VO flags; DJ stand-in entity; player-character setup | works; leaderboard errors remain (stock code, no guard; GSC:53-56) |
| Rounds, spawning, clowns, brute | not custom: the **stock Spaceland wave loop** (`_id_E81B`) with the map's spawner/volume data: wave 1-5 counts (solo) 6/8/13/18/24, `24 + 3*0.03*wave^2` from wave 10, spawn delay `2*0.95^(wave-1)`, clowns from wave 5, brute from wave 10 | PROVEN_LOCAL: waves 1-12 in 494 s, 12 clowns at wave 6, brute at wave 11 died (`gameplay/REPORT-g27.md` l.10-12, 50) |
| **Zombie cap** | the map script sets **no cap**; stock rule "max 24 alive" (`gameplay/stock-spawn-recipe.md` l.77). Server-side (Paris module) caps: not stated in these files. Harness spawner test used <= 16 alive (`REPORT.md` l.43) | stock only |
| Doors | `iwz_door_purchases` wraps the stock debris activation for `debris_750/1000/1250` (GSC:76-105); stock `clear_debris` does `connectpaths` + `notsolid` on the tiled blocker brushmodels; blockers hidden, dressing removed on purchase (GSC:547-613) | 5/5 doors, real F key works on g27 (`REPORT-g27.md` l.43-44) |
| Zone links | `iwz_zone_links` (GSC:131-168): updates volume adjacency and activates both zones of a link every 0.5 s | works |
| Power | stock `generator` interaction `power_all` at (3500, 2420, -270) | works (`REPORT-g25.md` l.93) |
| Perks | 4 stock machines relocated, all `requires_power`: Up'N Atoms (hall), Tuff 'Nuff 2500 (platform_a), Racin' Stripes (generator), Bang Bangs 2000 (platform_b) | works ("4/4 perks incl. Rat-a-tat" `REPORT-g24.md` l.35) |
| Wall buys | 5 stock structs: revolver 500, UMP45 1250, M4 1500, sonic shotgun 750, M1C 500 (S2:2801) | 5/5 pass |
| Magic wheel | 3 locations (start platform_a); spin 950; parked template wheels' spinners deleted by `iwz_wheel_cleanup` (GSC:205-227) | works; only the active wheel responds (stock behaviour) |
| Pack-a-Punch quest | `iwz_pap_quest` (GSC:232-328): after `power_on`, three relays (platform_a column, platform_b booth, generator room) each need a 2 s hold Use; panel model swaps, red -> green fx; all three open the PaP shutter (blockers `notsolid` + 2 gates `movez 180` over 3 s) | PROVEN_LOCAL with real 2.6 s hold; persistence through death/join NOT_PROVEN |
| Pack-a-Punch machine | stock `weapon_upgrade` at (3104, 4100, -320), behind the shutter; real F purchase 10000 -> level 2 | pass (one stock `weapon_upgrade` error, upgrade still worked: `REPORT-g27.md` l.60) |
| Third Rail trap | `iwz_third_rail` (GSC:332-407): fuse box on platform_a (-768, 1975, -300), 750, needs power; for 25 s kills every zombie inside the pit box (-2400,1200,-384)-(2600,1600,-350) (`dodamage` with no attacker: no score), 20 damage per 0.25 s to players in the pit, arcs/sparks every 384 units, 60 s cooldown | tested by the harness ("trap" phase: refusal, kills 3 inside / spares outside, damage, cost, cooldown, `REPORT.md` l.35-38); in-game visuals of the arcs not stated |
| Easter egg | hidden BO3 teddy bear in the hero car + hint loop + "Abracadavre": audio module, not in `cp_iwz2.gsc`; Use/damage routes | song, activation, hint falloff, bear Use from a real key press witnessed 2026-11-07 (audio README l.124-137) |
| Ambient FX | `iwz_ambient_fx` (GSC:415-447) from the generated table | works (FX proof) |
| Flicker | `iwz_flicker` lamps (GSC:485-544), unlit until `power_on`; taken over by the darkness module when present | works |
| Darkness, flashlight, audio layout | separate rawfiles, injected by `//@DARK@`, `//@AUDIO@` (S2:3140-3144) | see 2.6 / 2.7 |
| Debug | `iwz_report` prints state every 5 s (GSC:170-201) | debug only |
| **Stubbed / absent** | no boss / major quest beyond the PaP relays; no Spaceland interactions that have no struct (their init functions are disabled by `iwz_register_interactions`, GSC:452-481); fast-travel / hidden-room lookups get parked entities; no custom VO (only two flags kept, GSC:51-52); no window barricades; no trap other than Third Rail; wonder weapons are a separate project | by code |
| **Known failures at the last QA** | east well climb fails (3/5), west 1/5 (g27d); stair B going up failed in g27 (passed g26c); stair B bottom-landing spawners die; blue suitcase on the navmesh; player stops at (-3231,1636) in the tunnel; g27dw probe 0/10 at the wells, work paused 2026-11-09 | `REPORT-g27.md` l.62-67; `level/NOTES.md` l.787-806 |

---

## 4. Custom art assets that exist

All under `<runtime>/iwz-stage2\` unless stated.

- **Signs (10)**, procedural typeset art (`art/signs/<name>.png` + `<name>_c.tga`; aged copies `art/g25/signs_aged`): `sign_station_zero`, `sign_station_zero_plain`, `sign_old_station`, `sign_to_platforms`, `sign_northbound`, `sign_to_old_station`, `sign_staff_only`, `sign_signal_control`, `sign_generator`, `sign_network_map` (MAT:153-156).
- **Posters** (`art/out/`): `poster_mindgap`, `poster_lasttrain`, `poster_station_zero` (+ v2); g25 art set (`art/g25/`, `<name>_c.tga` + DDS): `poster_missing_a/b/c` (AI photo with copy treatment), `poster_illustration_2` (AI painting), `notice_closed_layers`, `notice_quarantine`, `notice_do_not_restart`, `departure_board_suspended`, `evac_signal_diagram`, `clock_face_stopped`, `ad_panel_broken`.
- **Decals**: `decal_blood_hand_smear/_drag/_spatter/_pool/_feathered`, `decal_grime_feathered`, `grime_mask_floor`, `junction_grime`, `water_streak`, `sign_grime_overlay`. Story plates `art/story/`: `story_run_047`, `story_headsign_2347`, `story_danger_g2`, `story_lockout_tag`, `story_clock_big`, `decal_soot_bloom`. Chalk boards `art/chalk/` (9 images, weapon outline + price).
- **Models ported/authored (not stock)**: the `iwz_*` set above, authored GLBs in `train/authored` (ballast, rails, third rail, car end, underframe, genset); ports in `train/port/{banzai*,kit*,genset*}` (x64-zt-extensions branch `codex/t7-env-port`, per `train/REPORT.md`).
- **Audio**: bank `cp_iwz.all` (60 aliases) + synthesized music cues; BO3 teddy bear model `p7_zm_teddybear` converted (audio README l.15-22).
- **Hero/zombie redesigns** (not part of the map geometry): `heroes/` concepts, Hunyuan/Hi3D GLBs, fits; paused 2026-11-09 (`heroes/HANDOFF.md`).
- **Quality records**:
  - `art/REVIEW.md` (g25): the art agent's own review, "not an independent review"; all assets PASS with MINEUR notes; in-engine look NOT_PROVEN at that time (l.1-6, 41-46). Photos in the missing-person posters are AI generated; the copy treatment hides the tell (l.20-22).
  - `vision/g27d` (3 independent reviewers, scores against shipped IWZ maps /10): A **5.0**, B **5.5**, C **4.8** (CONSOLIDATED.md l.1; review-A.md l.3; review-B.md l.3). B's zone scores: Platform B 6.5, Platform A 6, Ticket hall 6, Generator room 6, Maintenance corridor 5, Stair A 5, Control room 5, Stair B 4.5, Service tunnel 4 (review-B.md l.60-70).
  - Best-rated individual items: the 047 + 23:47 train story, the shift roster ("best single story beat"), the evacuation diagram ("excellent"). Lowest: bright flat lighting, colour casts, floating rubble, black floor shapes (CONSOLIDATED.md l.12-48).
  - Open items at the last consolidation (g27d): floating tunnel-end rubble, black floor shapes, perk buried behind crates, planks as shelf stubs, white drums, lime radiator, blue/orange/lime colour casts, ceiling housings, flat lighting, chalk unreadable, train details, untextured white lockers, tidy control room, clipping signs, small clock; MINEUR: blank walls (cess walls, control room, stairs), repeated ghost-poster squares (CONSOLIDATED.md l.12-48). The g27e source claims fixes for most of them; none of the g27e fixes were built or proven before the 2026-11-09 pause.

---

## 5. Honest filler list

Filler = elements with no gameplay purpose and no story weight, or the same module repeated, or surface area that carries nothing. The facts are from the recorded counts; the judgement is mine.

1. **Platform A is half the map and one long strip.** 4800 x 1040 units (122 m x 26 m), 3,330 m2 = 48.9 % of all walkable area (about a quarter of it the track pit). Eight identical square columns every 512 (S2:1233), 4 benches, ad frames on every 320-unit pilaster, 34 identical edge panels, 25 identical track segments. One hero object (the train) and one trap.
2. **Two corridors with nothing in them.** `maint_corridor` (161 m2, 224 high) and `service_tunnel` (393 m2): same ribs every 200/320 repeated, yellow stripe, tray, pipes. No wall buy, perk, door of interest. The tunnel's I-beam is 390 of its 983 quads (40 %). 6 + 6 spawners and nothing else.
3. **Stair A and Stair B (190 + 158 m2, 5 % of the map)** are one `straight_stair` module twice: 20/23 identical steps. Stair A has 0 props; Stair B's only props are door boards (16 identical planks + 4 barricades). Stair B has 0 signs.
4. **Visual-only spaces that cannot be entered**: the east tunnel mouth 600 x 368 with collapse (S2:1215-1230), the dead west tunnel 400 x 208 (S2:1472-1485), the street alcove stair of 6 rubble steps (S2:1085-1087), the Platform B sunk trench with a disused track (S2:1508-1520), the generator-room catwalk (S2:1696-1701) and the faux "cage door" (CONSOLIDATED item 13). They carry mood but no play.
5. **Door dressing is 66 copies of one plank** (`p7_zm_der_plank_wood_2x12x96`, 16 per door x 4 doors + 2) and 18 copies of one barricade; the door tunnel has none. All vanish once the door is bought.
6. **27 copies of one rubble pile and 23 copies of one electrical box** (`debris_concrete_rubble_pile_01_dark`, `electrical_control_box_03`): the code comment at S2:2313 says "bare-wall fills (sz2_density.py --debug)": 8 + 4 boxes and vents on the track wall were added to satisfy the density lint, not for a purpose. The density gate asks >= 4 items per 100 m2 (`sz2_density.py`); the map holds 399 decor entries over 6,808 m2 = 5.9 per 100 m2 (about the minimum).
7. **Control room (483 m2, 288-unit ceiling)**: 3 identical desk pairs (240 x 80, 2 CRT + 2 lab desks each), 2 filing cabinets, a diagram; reviewers call it "hangar-sized, sparse, tidy" and "blank walls" (CONSOLIDATED item 13, B review). The PaP alcove (256 x 144) is the only reason the room exists.
8. **Generator room**: 1200 x 784 around one genset; the rest is crates, drums, lockers along walls. 905 quads, 402 of them steel_trim.
9. **Ticket hall turnstile rows**: 15 turnstile models in two rows (west row of 11 at x -1130..-330 with 11 collision boxes, S2:2168-2171; east row of 4, S2:2089-2091), 13 of them the identical animated model and 2 the missing-arm variant; the fare line has no story or play value beyond blocking.
10. **Signs and posters repeated**: `sign_to_old_station` 5x, `sign_station_zero` 4x, `sign_station_zero_plain` 4x, `art_poster_station_zero_v2` 3x, `art_poster_illustration_2` 3x, `sign_network_map` 3x, `sign_northbound` 3x on identical walls (`layout.json signs`). "Ghost-poster squares" repeat (reviewers).
11. **Trim as geometry**: 64 % of all quads are trim strips (steel_trim 2,581). The map's visible "detail" is mostly bands, ribs and frames repeated per wall rather than distinct architecture; 264 surfaces, 13,456 triangles, 94 materials in a 6,800 m2 space.
12. **Spawners are one template ×56**: every zone gets 4 ground emergers (39 of 56), the same fx; no windows/boards, so no combat position has a reason to be held.
13. **Light is uniform**: 50 + 33 identical fluorescent/lamp fixtures in a grid with half "dead"; reviewers: "still bright/flat", "showroom-bright", "bright warehouse". Colour casts (blue cess walkway, orange flood, maroon control room, lime stair B) came from lights without fixtures.
14. **Perk/buy placement leaves whole zones empty of interaction**: maint_corridor, service_tunnel, stair_a/b (except one wall buy in stair_a), control room (PaP only).

Genuinely purposeful (not filler): the hall -> stair -> platform -> tunnel loop, the generator/control/PaP chain, the relay quest across three rooms, the Third Rail trap on the pit, the hero train with the bear, the boarded Platform B, the story plates.

---

## 6. Tools (docs/CREATION-TOOLS.md and docs/WORLDKIT.md)

### 6.1 `docs/CREATION-TOOLS.md` (table, l.13-25; commands run from `tools-source/iwzmap`)

| Tool | Command | What it does | Limits / state | Timing / tests |
| --- | --- | --- | --- | --- |
| Catalogue | `python -I catalog/iwzcat.py build\|query\|kit ...`; booth `catalog/Run-Preview.ps1`; `catalog/preview_analyze.py` | reads ZoneTool dumps of game models into a catalogue (bounds, LODs, materials, cost), picks a kit, checks each model in a preview booth | "not recorded" in game (pass criteria written, no dated run) | 7 tests (`test_catalog.py`); timing not stated |
| Kit import | `python -I kit_import.py <work> <map> --dump <zone>=<dump> --models ...` (or `build-sz2.ps1 -KitModels`); proof `kit_proof.py` | adds stock models of other zones (disco, final...) to a usermap: geometry, materials, image headers, physics, techsets | no unit tests; do not `require` two extra map techset zones (hung ZoneTool); scriptable movers dropped | not stated |
| Light bake | `python -I bake/lmbake.py <src> <lights.json> <out>`; `bake/layout_lights.py`; `bake/lm_measure.py` | lightmap + light-grid baker, ray-traced direct + bounces, AO, BC6H/BC4; engine-frame measurement | no tests; undated proof: baked-vs-rendered luma correlation 0.87-0.985 | not stated |
| Effects | `python -I fx/fx_place.py <fx.txt> <src> --ncs ...`; `fx/fx_proof.py` | places stock/imported effects, self-lit variants, per-effect frame and frame-time proof | none registered; sprite FX only | FX cost +0.08 ms (21 FX) |
| Art | `python -m art.make_station_zero_art <out> <images dir>` (from `tools-source/iwzmap`) | deterministic 2D art (signs, boards, notices, blood, grime) as TGA + mipped DDS | 18 checks; look in game "not recorded" in the doc | seconds (not stated) |
| Audio | `python -I audio/add_audio.py ...`; `audio/audio_layout.py`; `audio/audio_measure.py` | sound bank, hidden-song egg, zone beds, emitters, music cues, power-on audio, process-only capture | 7 tests; witnessed 2026-11-07 | - |
| Darkness | `python -I darkness/dark_build.py ...`; `build-sz2.ps1 -Darkness`; `darkness/dk_measure.py` | dark until power, baked emergency lights, switchable banks, power-on sequence, dark vision, flashlight | none registered; requires ZoneTool branch `codex/iwzmap-darkness` | - |
| Train kit | `python -I track_clearance.py <src>`; `train_proof.py <run>`; `train_perf.py <run>` | train/car/track kit, clearance, drawn/textured/lit proof, frame time | no doc of its own, no tests, not recorded | - |
| Volumes | `python -I volume_check.py <maps/cp dir> <map> [--plan <src>/plan.json]` | offline check that every trigger/spawn volume has a point-testable shape; spawners and cells inside their zone | 6 tests | - |
| Map generator v2 | `python -I station_zero2.py <stock dump> <src>`; `sz2_plan.py <src>`; `build-sz2.ps1`; `run-sz2.ps1` | builds the 9-zone station from brushes + data tables; plan/nav/data checks; build and run scripts | `tests/` 69 tests cover the gates; acceptance of the whole map not recorded | - |
| Navigation and build checks | `python -I -B iwz_emitcheck.py check <src>`; `iwz_zonecheck.py <work> --zone <map>`; `iwz_probe_forensics.py <runs>`; `sz2_navconn.py <src>`; `sz2_probecheck.py` | gates before a launch: emit (collision, nav, links, stairs, spawners, routes, build diff), zone check, probe forensics, nav connectivity, reflection probes | offline by design | emit check "about two seconds per emit" (README l.79-80) |

Other offline gates on main (file headers): `sz2_artlint.py` (failed materials, track-bed, fake vehicles, floor streaks, void black, uv-aspect...), `sz2_seams.py` (open ceiling seams), `sz2_flatness.py` (largest undetailed wall/floor/ceiling area per zone), `sz2_density.py` (props per 100 m2, longest bare wall run), `sz2_propcheck.py`, `sz2_signcheck.py`, `sz2_fxcheck.py`, `sz2_contrast.py`, `sz2_mood.py` / `sz2_mood_predict.py`, `sz2_fixproof.py` (same-camera before/after crops), `sz2_frames.py`, `sz2_lmpick.py`.
Plan gate result for g27dw (`plan_check.json`): fails none, 10,306 of 10,306 cells reachable, 1 note (the Racin' Stripes perk has no nav cell within one cell; wall mounted).
"What every map maker should know" (l.27-32): the offline gates are the first stop and run on every tool change (`checks.json`); the build scripts still carry the machine paths of the original runs; the chain needs the ZoneTool branches named in the READMEs.

### 6.2 `docs/WORLDKIT.md` (stock map as data, prefabs) - `tools-source/worldkit/iw7_world.py`, `iw7_dump.py`

Reads the ZoneTool dump of a shipped map into a SQLite scene (props with orientation, surfaces with material, lights, entities). Python stdlib only (numpy optional; `IW7_WORLD_NO_NUMPY=1`). Never runs the game or the asset tool. Output `--json`, `--limit N` (default 10, 0 = all); exit 2 on failure.

| Subcommand | Command (l.24-25) | What it does | Spaceland example (l.32-44) |
| --- | --- | --- | --- |
| `build` | `iw7_world.py build --dump <dump> --db out.sqlite [--catalog ...] [--map stem]` | reads `.gfxmap`, `.commap.json`/`.commap`, `.ents`, `transient_zones/*.gfxmap_tr`; mesh buffers to `<db>.mesh` | surfaces 10760, smodels 17010, lights 1039, probes 160; 3-5 s (7 s without numpy) |
| `stats` | `... stats --db` | counts vs header vs ground truth, bounding boxes, 20 top models, 20 top materials | all columns agree |
| `box` | `box X1 Y1 Z1 X2 Y2 Z2` | props, lights, entities inside an AABB; surfaces touching; triangles by centroid | start box: 483 props, 36 lights, 69 entities, 11,460 triangles |
| `near` | `near X Y Z --radius R [--kind props\|lights\|ents\|surfaces]` | same around a point, nearest first | r 600 at start: 407 props, 30 lights, 64 entities |
| `find-model` / `where-model` | `find-model TEXT`, `where-model NAME` | models by name substring with instance count/centroid; every placement of a model | `arcade` 36 models; `zmb_arcade_toy_astronaut_white` 104 |
| `rooms` | `rooms --cell 512` | grid over x,y: props, lights, entities, triangles per non-empty cell | 1861 non-empty cells |
| `check` | `check [--dump DIR]` | sanity checks vs dump folder (model files, material files, outliers, orientation) | measured table |
| `compare-smodels` | `compare-smodels --csv FILE` | compares static models with the compiler's own table | 17010/17010 equal |
| **`extract`** | `extract --box X1 Y1 Z1 X2 Y2 Z2 --name N --out DIR` (the `--db` is required) | writes a **prefab** folder `iw7.prefab/1`: `prefab.json` (props, lights, ents, surfaces), `surfaces.bin` (meshes), `smodels.txt` (compiler format) | `spawn_plaza`: 483 props, 36 lights, 69 ents, 437 surfaces, 11,460 triangles |
| **`place`** | `place --prefab DIR --at X Y Z [--yaw DEG] --out DIR2` | moves and turns a prefab about the vertical axis (right angles exact) | yaw 90 exact |

**Prefab rooms from shipped maps**: yes, as DATA only. A prefab carries props, lights, entities, surface meshes and lightmap coordinates/index (not the lighting). **Not extracted**: Havok collision, navmesh, path nodes; lightmap texels; light grid, reflection probe contents, umbra data; binary `.ents.data` (triggers, splines, dynamic entities, clip data) is listed not read.
"Nothing here builds a map": the compiler already takes `smodels.txt`; surface meshes have no consumer yet (l.118-119). Proven on one real map only (Spaceland; the Rave dump holds no world files, l.126-127).

### 6.3 Entity edits (not in CREATION-TOOLS.md; `docs/MAPENTS.md`, `tools-source/mapents/iw7_mapents.py`)

`export`, `stats`, `find`, `patch`, `diff`, `write` change a shipped map's entity list with no build: the IW7-Mod loader reads `iw7-mod/maps/cp/<map>.d3dbsp.ents` and replaces the list at map load (first hit wins across `<game>/iw7-mod`, mod data `cdata`, engine paths).
Can: add/remove/change entities that use shapes the map already has, spawners, starts, interaction points, doors, placed models already in the zone's pool, script fields. Cannot: geometry, collision, baked light, navmesh, new trigger/brush shapes, models/fx/sounds not loaded in the map's zone (l.20-33).
Proven live on a dedicated server, Spaceland, 2026-11-10 (round trip with equal counts; remove 5, change 1, add 1: 6 of 6 expectations). Not verified: client reads, maps other than Spaceland, new triggers (l.147-149).

---

## 7. Discrepancies and cautions found while reading

1. `tools-source/iwzmap/README.md` l.14-35 ("Pieces") still describes `station_zero.py` (v1) and `cp_iwz.gsc`; the v2 generator `station_zero2.py` with `cp_iwz2.gsc` is in the later section (l.141-159). `cp_iwz.gsc` (108 lines) and `cp_iwz_v1.gsc` (26) are history.
2. `docs/CREATION-TOOLS.md` does not list `mapents` or the `worldkit` (they have their own docs).
3. `LEVEL-DESIGN.md` says Up'N Atoms might not need power; the generator marks all four perks `requires_power` (S2:2985).
4. `LEVEL-DESIGN.md` zone boxes (e.g. `stair_b` x -1600..-1200, platform_b x -3600..-1600) are the v1 plan; the real boxes are S2:61-71.
5. The recorded `d16` numbers (257 surfaces, 193 static models) differ from `g27dw` (264, 170); anything quoted "current" should name its build.
6. The default generator run (no environment) is not the judged map; the judged build needs `IWZ_KIT`, `IWZ_SMODELS`, `IWZ_TRAIN` (+`IWZ_TRAIN_CARS=3`, `IWZ_TRAIN_PROPS`), and a baked lightmap; dark build also `IWZ_DARK`. The exact env of g27dw is not recorded in the files I read.
