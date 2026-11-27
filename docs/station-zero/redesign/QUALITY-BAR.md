# Station Zero quality bar: what "authored" measures as in the stock maps

Art direction study, 27 Nov 2026. Read-only: nothing built, no game run, nothing exported.

**Sources.** Stock: the world databases `C:\studio-data\grammar\db\<map>.sqlite` (`smodels`, `lights`, `surfaces`, `tris`, `ents`, `ent_kv`; built from the ZoneTool dumps in each `meta.dump_path`: `IW7-Runtime\iwz-map-ref-a\dump\cp_zmb`, `iwz-blend\ztwork\dump\cp_disco`) and `C:\studio-data\rooms\catalogue.json` (168 stock rooms). Ours: `C:\studio-data\sz\arcade\r19\doc\layers\*.json` (Arcade) and `C:\studio-data\sb\base_sb\layout.json`, `surfaces.json` (ticket hall, control room). An object counts when its origin is inside the stated box. Density is **per 1,000 square units of box footprint** (`studio density`'s `per_1000`, divided by 1,000).

**Definitions.** Fixture model: a name with light, lamp, fluo, sconce, bulb, lantern or neon. Loose model: neither a fixture nor structure (pillar, beam, wall, pipe, duct, wire, door, window, rail, post). Hue class of a light, colour scaled to its peak: white (all channels above 0.85), warm, red, green, cool, blue, magenta. Stock light strength is the colour peak / 1000.

Parts A to C are **measured**. Part D is **from memory of the games**.

## A. Three stock places

### A1. Five shopfronts in a row: Shaolin Shuffle, north side of the street (cp_disco, facade y 4765, floor z 750)

Box per shop: its x range, y 4690..5110, z 745..1010. "Behind" = y >= 4795. Columns are named by their sign model.

| | Market | `tl` marquee (peepshow neons) | Pink Cat (`pk` marquee) | Pizzeria (`bng` marquee) | Crankshaft |
|---|---|---|---|---|---|
| Front width | 515 | 380 | 740 | 440 | 470 |
| Static models / distinct | 670 / 31 | 138 / 37 | 205 / 60 | 46 / 17 | 18 / 13 |
| Behind the facade / distinct | 641 / 21 | 9 / 4 | 86 / 25 | 12 / 2 | 0 |
| Depth seen behind the glass | about 325 | a door recess | recess 160..230 | 0 | 0 |
| Hero sign, w x h, centre height | none: awning run 510 wide, 2 painted signs 52x68, 46x22 | 188x107 at +194 | 280x142 at +205 | 344x128 and 378x52 at +192..200 | neon 288x112 at +195 |
| Eye level signs | 2 neon OPEN 43x18 at +85..92 | 2 silhouettes 26x87, 2 neon 42x42, 2 OPEN 26x11, at +55..85 | neon arrow 40x123, 3 A-boards 45x54 at +27, 10 poster frames 40x70 at +53 | 0 | 0 |
| Emissive bulb, tube, recessed models | 0 | 59 | 70 | 8 | 0 |
| Engine lights | 3 (2 cool, 1 warm), r 100..250 | 1 blue, r 200 | 5 (3 warm, 2 white), r 200..300 | 0 | 0 |
| Materials on the facade slab | 46 | 51 | 54 | 40 | 18 |
| Gameplay hosted | `perk_machine_zap` in front | `gourd_station` | 2 `enter_peepshow` doors | none | none |

The trade is told by goods or by one sign. Market: 9 bottle models are 599 of the 641 props behind the glass (93 %). Pink Cat lobby: queue poles, cash registers, stools, magazines and poster frames are 40 of 86 (47 %). Four of five hero signs are a model placed once on the row, faces 19,656 to 44,032 square units. Two fronts are closed: no light, 18 and 46 props. No two shops share a light row.

Spaceland's signs are single placements too (`zmb_galaxy_journey_building_neon_on` 411x49, `zmb_kepler_gate_sign` 187x86). Frame `C:\studio-data\captures\cp_zmb_a\cam2.png`: Galaxy Journey is cyan, its neighbour green, the way to the power is painted on the floor.

### A2. The Pack-a-Punch place

`weapon_upgrade` stands at (-10144, 850, -1592) in cp_zmb, cp_disco, cp_rave and cp_town: one projection room about 10,000 units outside each map. cp_final has a copy inside the map at (5239, -5079, 329).

| | Projection room, cp_zmb (cp_disco: 1 prop less) | cp_final |
|---|---|---|
| Interior | 384 x 412, about 180 high | about 450 x 450 |
| Box measured | 470 x 490 = 230,300 | 220,900 |
| Static models / distinct, per 1,000 | 274 / 97, 1.19 | 192 / 73, 0.87 |
| Lights | 7 spots (0.030 per 1,000): 5 warm pendants (1.00, 0.79, 0.32) 4.94, r 250, each on a lamp model; a desk lamp 12.2; one cool key (0.50, 0.79, 1.00) 198, r 1200, 108 units from the machine (cp_disco: 66, r 600) | 6 warm, 4.46..4.94, no key |
| Signs naming the machine | 0 | 0 |
| Sign materials | 1: Willard film posters, 2 quads 34x52 | the same |
| What the room was | 5 filing cabinets, 6 folding chairs, 2 desks, 8 clipboards, 8 book sets, 7 soda crates, burgers, a tool cabinet; 24 candles, 3 altar tables, a soul jar | the same kit, a CRT, a coffee pot |
| Machine plumbed in | `zmb_pap_pipe_01/02` x 7 (388 long), `zmb_pap_wire_01/02`, 17 hose ends, 16 hoses | the same |
| Arrival | `portal_doorway` (121 x 111 x 130), 341 units from the machine, across the room | portal 346 units from the machine |
| Anchor in the map | cp_disco: the projector, 5 `pickup_reel`, `pap_fusebox`, `pap_fuse_switch` | `reel_change`, `pap_portal`, 3 `pap_bridge` |
| Sound entities | no `audio_pa_speaker` in the room | none |

### A3. A transit space: Shaolin Shuffle's east subway station (cp_disco)

Box x 50..1110, y 2300..3180, z 250..505 = 932,800: two side platforms and the train between.

| Measure | Value |
|---|---|
| Columns | world geometry in the station's tile, 34 wide; one row a platform (x 332, x 808); pitch 288 (y 2322, 2610, 2898, 3188, 3483, 3771); clear height about 214 |
| Tile kit (triangles) | `dt_tile_ceramic_white` 412, `dt_tile_ceramic_white_dmg` 171, `dt_tile_ceramic_blue_01` 308 (the band), `fac_tile_black_01` 715, floor `rubber_tile_bumper_car_floor` 601 |
| Materials | 122 (44 named, 78 map blends) |
| Signage | 4 families: station plates (material `cp_disco_subway_sign_01`, `_reverse`, `_02`) 38..104 wide, 15..23 high, 91..124 above the floor; `ow_sign03` plates 16x10 at +62..73; lit exit signs 15x10 at +134..140; caution plates 30x30 |
| Static models / distinct | 285 / 82; 0.31 per 1,000; most copied loose model 7.7 % (22 food boxes) |
| Lights | 10 spots, 0.011 per 1,000: 6 green-white, r 280..350; 2 white, r 100; 1 red; 1 cyan (4 hue classes, the dominant one 60 %) |
| Fixture models | 24, 0.026 per 1,000: 14 hanging tubes (1 on, 13 off, one-bulb or damaged), 8 train headlights, 2 emergency lamps; 3 of the 10 lights have one within 96 units |
| Sound | 1 `audio_pa_speaker` entity, 6 wall loudspeaker models |
| Gameplay hosted | 10 interactions: a perk, 2 wall weapons, the generator, lost and found, 2 phone booths, a gourd station, a memory TV, trash cans |

West station (1,925,600): 0.27 props and 0.011 lights per 1,000, 8 of 19 tubes off or damaged. Turnstile mezzanines (cp_disco#73, #69, #10): 0.09, 0.18, 0.25 props per 1,000; 4, 3, 6 lights.

**138 stock rooms of the five maps** (30 props or more): distinct models per 100 props, median 37, p10 19; share of the most copied loose model, median 8.8 %, p90 19.3 %; lights per 1,000, median 0.013, p90 0.028, max 0.049; hue classes a room, median 2, max 6; materials a room, median 51, p10 23. Light radius, map-wide median: 175 (cp_zmb), 250 (cp_disco). Lights with a fixture model within 96 units, map wide: 73 % and 66 % (single places: 30 to 100 %).

## B. Our r19 document beside it

| Measure | Stock | Ours |
|---|---|---|
| **Arcade shop bays** (box 320 x 385) | Shaolin row | Photos / Heel & Key / Hole Number Nine / Copy Stop / Needle Drop |
| Hero sign | 4 of 5 unique models, 188..378 x 52..143 | 5 of 5 the same object: text band 224x32, font `impact`, at +170; only the colour differs |
| Hero sign face | 19,656..44,032 | 7,168 |
| Props / distinct | 18..670 / 13..60; two fronts closed | 94 / 27, 175 / 44, 146 / 39, 165 / 59, 90 / 23; none closed |
| Most copied model | the trade's goods | `p7_box_cardboard_c_closed` first in 3 bays, second in 2: 14..20 % of each bay |
| Lights a shop | 0, 0, 1, 3, 5; no row shared | 9, 7, 8, 9, 9; six rows identical in all five (strength, radius, height) |
| Lights per 1,000 | 0.013 median, 0.049 max | 0.057..0.073 |
| Light radius, median | 175..250 | 99 |
| Light strength | 2.75..5.77 median | 0.6..0.8: **not comparable**. `stock/README.md` (M9, M10) measured a baked 0.05 at 0.65 of a stock interior and 1.2 as white: never copy a stock strength into `intensity` |
| Dominant hue | differs from shop to shop: cool, blue, warm | warm in all five bays (6 to 8 of 7 to 9 lights) |
| Materials | 18..54 on the facade | 8..12 box materials; two of them in all five bays |
| Gameplay hosted | 3 of 5 shops | 0 of 5 (2 spawners each); both wall weapons on the corridor wall |
| Posters | per shop | five of the same six `poster_0..5.png` in every bay |
| **Arcade columns** | station tile, pitch 288 | `cp_disco_dojo_column_01..04`, the Shaolin dojo's red columns, pitch 300 |
| **Ticket hall** (2,240,000) | mezzanines; east platforms | |
| Props per 1,000 | 0.09, 0.18, 0.25; 0.31 | 0.039 (87 props, 32 models): 2 to 8 times sparser |
| Lights, per 1,000 | 3 to 6 a mezzanine; 0.011 | 34, 0.015 |
| Signs | 4 families, fixed sizes | 18 signs, 15 images, 7 sizes (64x96 to 384x96) |
| Tile kit | white, damaged white, blue band, black, floor | `tile_white`, `tile_charcoal`, `tile_black`; no damaged twin, no band |
| Perk spacing | nearest two perks 404..1240 apart | three perks and the wheel on one wall, 290 and 450 apart |
| **Control room, our Pack-a-Punch** (960,000) | projection room | |
| Props / distinct, per 1,000 | 274 / 97, 1.19 | 53 / 17, 0.055 |
| Lights | 7: warm practicals, one cool key | 14 omni (8 cool, 4 red, 2 warm), no key |
| Label | none | `sign_pap` 200x50 over a shutter 256x208 |

## C. The bar: 25 rules for one section

Every threshold is a value the stock places of part A pass, or carries its stock pass rate. "Doc" = a count from the document layers. "Blind" = a question to three reviewers (`python -m studio review pack` on `studio live shot --clean` frames).

| # | Rule | Check | Stock number |
|---|---|---|---|
| 1 | Every shop is told by something no other shop of the row has: a hero sign of its own, or goods filling the window | doc: signs 150 or wider grouped by kind and size, 1 member a group | sign 4 of 5, goods 1 of 5 |
| 2 | A hero sign's face is 19,600 square units or more | doc | 19,656..44,032 |
| 3 | Two or more eye level signs (+27..+92) on an open front | doc | 2, 6, 14 |
| 4 | In a row of five, two fronts are closed: 46 props or fewer, no light, hero sign kept | doc | 2 of 5 |
| 5 | In an open shop the trade's own objects are 45 % or more of the props behind the glass | doc; blind: "what does it sell?", name blurred, from 800 units, 2 of 3 right | 47 %, 93 % |
| 6 | A filler model (box, crate, pallet, trash) is under 8.8 % of a room and never a shop's most copied model | doc | 6.0..7.7 % in the stations |
| 7 | 19 distinct models per 100 props or more, shelf goods excepted | doc | p10 19; part A places 21..72; market 4.6 |
| 8 | No hall under 0.09 props per 1,000; a platform at 0.27 or more | `studio density`, `per_1000` / 1,000 | 0.09..0.25; 0.27, 0.31 |
| 9 | At most 0.049 lights per 1,000 | doc | max of 138 rooms |
| 10 | Median light radius 175 or more | doc | 175, 250 |
| 11 | No two shops or bays of a row share a light row (strength, radius, height) | doc | 0 shared among the five fronts |
| 12 | Neighbouring shops differ in dominant hue; four hue classes at most a room | doc | 3 of 3 lit fronts differ; stations 4 |
| 13 | Over the whole section 65 % of lights have a fixture model within 96 units; 40 % of tube fixtures are off or damaged | doc | 66 %, 73 %; 42 %, 93 % |
| 14 | Entertainment fronts glow by models: 59 emissive bulbs or tubes, 5 lights at most | doc | 59, 70; 1, 5 |
| 15 | Each perk machine has a light within 200 units | doc | min 1 (cp_zmb), 3 (cp_disco) |
| 16 | No two perk machines within 404 units | doc | minimum of five maps; four maps 678 or more |
| 17 | Three of five pockets host a gameplay object | doc: `gameplay.json` | 3 of 5 |
| 18 | No sign names the Pack-a-Punch | doc | 0 in 3 rooms |
| 19 | Its room: 230,300 or less, 0.87 props per 1,000 or more, 73 distinct models | doc | 0.87, 1.19; 73, 97 |
| 20 | Its light: warm practicals on lamp models, and one key 13 times their strength within 110 units, in a hue no other light of the room has | doc | key in 2 of 3 rooms: 13x, 40x |
| 21 | The room had a job: 8 object types of it; 7 pipe or cable runs end at the machine | doc; blind: "what was this room?" | 8; 7 pipes, 16 hoses |
| 22 | The machine is reached through a device 340 units away, and an object in the map announces it | doc; play | 341, 346; projector, reels |
| 23 | One column pitch a hall, columns in the hall's own tile, none from another theme | doc | pitch 288 |
| 24 | Tile kit of five: wall, its damaged twin, a band colour, a dark tile, a floor | doc | 5 |
| 25 | Four sign families at most a hall, each one size range and one height band; a landmark a reviewer names from every entrance at 1,500 units | doc: cluster sizes; blind, 2 of 3 | 4; landmark: no stock frames |

**r19 today.** Fails 1, 2, 4, 5 (trade objects among each bay's eight most copied models: 0 to 39 %), 6, 8 (hall 0.039), 9, 10, 11, 12, 16, 17, 18, 19, 20, 23, 24, 25. Passes 7 (bays 25..36), 13 (110 of 119 lights; 38 of 69 tubes off), 15. Not scored: 3, 14, 21, 22.

## D. What the classic maps do for identity (from memory of the games, not measured)

1. **One purpose a place.** Kino der Toten is a theatre: lobby, stage, dressing room, alley.
2. **A former life under the undead one.** Mob of the Dead's cell blocks and laundry still read as a prison; the machines came later.
3. **A colour script by district.** Shadows of Evil gives each district one neon colour and one trade; Spaceland gives each land its own.
4. **One landmark a zone, seen before it is reached.** The Golden Gate bridge, Spaceland's coaster, the dragons of Der Eisendrache.
5. **Named businesses with a logo, a typeface and goods.** Astrocade, the Pink Cat, the Black Cat dojo, the Inferno disco.
6. **Loops with one choke point.** Each district is a training circle with one narrow way out; pockets are dead ends on purpose.
7. **An "aha" reveal.** Kino's curtain, the pyramid under the castle, the portal in Spaceland's centre.
8. **Pack-a-Punch is earned and staged by its room.** Kino's projector room, the bridge reached by plane, IW7's projection booth behind a film reel.
9. **Diegetic interfaces.** Power is a wall switch, the wheel is a fairground wheel, the map's own signs give directions.
10. **Set pieces that are traps or quest steps.** The rollercoaster, the laser dance floor, Mob's fan and acid traps.
11. **Vistas to later places.** Kino's stage from the lobby; every land's sign from Spaceland's gate.
12. **Wear with a rhythm.** Half the tubes dead, one shop shuttered, one looted, one lit.

## Not measurable with the data on disk

- **Stock game frames.** Only Spaceland: 3 in `C:\studio-data\captures\cp_zmb_a`, 2 in `C:\studio-data\m1\cap_zmb` (cam1 is inside a wall). None of the four other maps: `C:\studio-data\rv\r8` holds our own sheets only, the `cap_stock` folders cited by `stock/README.md` are gone, and `C:\studio-data\rooms\pictures` holds unlit renders of the 168 catalogue rooms, not frames. The blind parts of rules 5, 22 and 25 have no stock number until the Shaolin row and station are captured.
- **Palette.** The dumps hold image headers; the store cache has 73 decoded cp_disco images, none of the station's tiles. The unlit render `rooms\pictures\cp_disco_76_top.png` reads mean saturation 0.13, hues 35 to 64 degrees; our lit frames (`r19\sheet_on.png`) read 0.33 to 0.41 in the Arcade: not like for like.
- **Light strength of ours against stock**: no calibrated conversion (part B).
- **Typefaces and logos**: sizes measured, pixels not read. **Sound**: speaker entities counted, the sound tables not parsed. **The Pack-a-Punch machine model**: spawned by script, absent from static models and entities.
- **Black Ops maps**: a Black Ops III install exists (`C:\Users\ezvalo\Desktop\bo3_game_files`) but no world database of it; nothing of BO1 to BO3 is measured.
