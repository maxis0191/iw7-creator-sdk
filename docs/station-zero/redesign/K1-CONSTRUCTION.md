# K1: building the Arcade from stock construction pieces (worker K1b, 28 Nov 2026)

Study only: no game run, no build, no bake. Continues the first K1 worker's measurements (`C:\studio-data\sz\film\k1\`, scripts and JSON named below).
Tags: **[m]** measured here (script and file named), **[r]** read in code or docs (file named), **[a]** assumed or chosen by me (a decision, not a fact).
Units are inches. "per 1,000" means per 1,000 square units of footprint (QUALITY-BAR's unit); "per 100x100" means per 10,000 square units
(the first K1 worker's unit: 3.06 per 100x100 = 0.306 per 1,000). Frames cited: `C:\studio-data\sz\film\stockref\cp_disco\` (sheets `sheet_subway_east.png`,
`sheet_shopfronts.png`; I looked at both).

## 0. Result in five lines

1. **Donor kit: cp_disco** (1970s New York subway and street), models and materials; nothing from the other four kits except what is already in the document as goods. Section 1.
2. **The stock station hall is not built from models.** Its columns, walls, floor and vault are world brushes in blend materials: on screen 80 to 86 % of the pixels are world surface and 62 % are blend surfaces; the 327 static models of the east station (box to z 700) hold no column, no wall piece, no ceiling piece, no cornice (hand classification, section 2.3). So "stock construction pieces" exist for the shopfronts, the fixtures, the cables, the street furniture and the signs, and **not for the hall's body: the hall's body has to be authored meshes in stock plain materials** (section 4 spells each mesh out: a column measured from the stock column, 3-unit chamfers, base, band, collar, cap).
3. **Three numbers that most change the plan.** (a) Stock hall density is 0.318 props per 1,000 without the train (0.306 in QUALITY-BAR's box); ours is 0.062 (89 props on 1,440,000), a factor of 5; the re-planned hall needs 230 to 260 props, not 89. (b) Hall width: stock platform clear width 434 to 438 and a 288 column pitch; ours is 716 clear. The re-plan is 480 clear (section 5, a proposal to the lead: it changes PLAN section 3's box). (c) Models alone give 17 % of a station frame (41 % of a shopfront frame); the drawable part of stock wear layers is 69 % of the platform's layer area but only 19 % of the mezzanine's, and our hall carries 3.4 % wear decal coverage today.
4. **Network cost: 0 records** for every stock model and every authored mesh (static props go to `smodels.txt`, not to the snapshot); the document stands at 480 of 768 (495 with four players); the only way the parts list costs a record is `static=False`.
5. **Blocked on R2:** blend layers (62 % of hall pixels) and five stock decal materials need R2's patches 1 to 5; nothing in the parts list waits for them, but the wear fidelity does (section 2.6).

## 1. Donor kit, from data

Dump roots that exist on this PC [m: `ls`]: world dumps `C:\Users\ezvalo\Documents\IW7-Runtime\iwz-blend\ztwork\dump\{cp_disco,cp_final,cp_rave,cp_town}` and `iwz-map-ref-a\dump\cp_zmb`; kit dumps (materials json, techsets) `iwz-stage2\kitimport\ztwork\dump\{cp_disco,cp_final}`; world databases `C:\studio-data\grammar\db\<map>.sqlite` (+ `.mesh`) for all five; stock frames of cp_disco and cp_zmb and cp_final under `stockref`. All five kits are candidates. (`docs/RESTORE-RUNTIME.md` on origin/main lists the `grammar` folder as absent after the disk clean; it is back, rebuilt: I read it today. If it is swept again every number below needs it.)

Script `k1\kit_compare.py` -> `kit_compare.json` [m], by model name (regex families as in the first worker's `m6_parts.py`; static model instances placed in the map):

| kit | static instances / distinct | storefront, door, window, gate | awning, marquee, sign | pipe, wire, duct | light fixture | column, beam, trim, rail | transit furniture | shop goods | models named subway / station / metro | tile models | plain world materials (drawn by the template) | blend share of world triangles |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **cp_disco** | 19,604 / 1,300 | **96** | 144 | 153 | **98** | 110 | **101** | 205 | **23** | **7** | 397 (83) | 0.207 |
| cp_zmb | 17,010 / 916 | 76 | 83 | 89 | 57 | 113 | 38 | 137 | 1 | 1 | 281 (281) | 0.291 |
| cp_rave | 20,039 / 1,213 | 47 | 75 | 76 | 50 | 67 | 66 | 234 | 1 | 1 | 252 (71) | 0.268 |
| cp_town | 17,482 / 1,295 | 55 | 127 | 121 | 51 | 72 | 58 | 288 | 15 (copies of cp_disco's) | 1 | 310 (81) | 0.371 |
| cp_final | 29,889 / 1,001 | 71 | 100 | 191 | 68 | 101 | 33 | 182 | 0 | 1 | 291 (82) | 0.164 |

Reading: cp_disco is the only kit with a transit vocabulary (23 subway models, the station tile kit, entrances, turnstiles, benches, lockers, gate bars, a subway car) and the most storefront and fixture models; it also has the lowest blend share of the four non-final kits, so the largest part of its world surface is plain material that our authored meshes can use exactly. cp_zmb has one real advantage: all 281 of its plain materials are drawn by the template world (no "bring"); against it, it is a fairground (park models, bright pop), and the Arcade's own spec is a tiled 1978 underpass whose tile kit (rule 24) is cp_disco's `dt_tile_ceramic_*` already. cp_rave (lodge, woods), cp_town (1950s town), cp_final (sci-fi) have none of the transit vocabulary. [a: choice]
Cost of cp_disco: 40 of the 55 plain materials I tested are "brought" from `techsets_cp_disco`, 15 are drawn by the template [m: `k1\matverdict.json`, `store.materials.verdict`]; the r19 document already brought 21 [r: INVENTORY.md section 3]. Era: the lore dates the Arcade 1978, sealed 1984, film 1986 [r: `arcade_shell.py` docstring]; 1970s NYC tile and neon is the same decade.

## 2. How stock builds this kind of space, measured

Places (cp_disco, the world database, boxes in world units): the east station `[50, 2300, 250, 1110, 3180, 700]` (two side platforms and the train, vault included: the first worker's box stopped at z 505 and cut the vault off, my first mistake to fix; floor z 286, vault crown z 681 [m: `m5b_profile.json`]); the Pink Cat `[-1865, 4690, 745, -1125, 5110, 1010]` (entertainment, the largest marquee, 203 props); the pizzeria `[-1125, 4690, 745, -685, 5110, 1010]` (a food counter, 51 props); The Lounge (136 props); Crankshaft (closed front, 18 props); the market (670 props, 640 of them bottles).

### 2.1 Surface share: models against world brushes

| Measure | Station | Shop fronts | Source |
|---|---|---|---|
| Model share of lod-0 mesh area in the box (world + models, no caulk) | platforms 22.5 %, mezzanine 23.3 % | market 28 %, Lounge 36 %, Pink Cat 47 %, pizzeria 66 %, Crankshaft 50 % | [m] `m1_area.py` -> `m1_area.log` |
| Model share of the pixels of a stock frame (z-buffer raster 320 x 180 from the eye of a stock reference frame, camera fitted to 0.03 px median) | **17.4 %** (frames east_1..5; closeups 1 %) | **41 %** (7 street and lobby frames), 52 % at the street corner frames | [m] `m2_screen.py` -> `m2_all.log` |
| World plain / world blend / decal (wc, named) | 20 % / **62 %** / 0.8 % | 23 % / 34 % / 1 % | [m] same |
| Models, by the NAME regex of the first worker (construction / fixture / loose) | 5.5 % / 0.5 % / 11.4 % | 19.6 % / 3.7 % / 18 % | [m] same; the regex miscounts (below), read these as upper bounds on construction |
| Station floor band (rows 70-97 %) | **64 % blend, 32 % loose models (trash), 3 % plain** | | [m] `m2_cp_disco_subway_east_1.json` |
| Where blend is, by orientation, platform box area | floor 71 %, wall 45 %, ceiling 40 %; mezzanine floor 79 %, ceiling 66 %, wall 42 % | facade box: floor 41 %, wall 30 %, ceiling 24 % | [m] `m3_wear.py` -> `m3_wear.json` |
| Distinct materials in a frame | 55 world + 33 model | 36 world + 36 model (82 model at the corner frames) | [m] `m2_screen.py` |

Models in the lit pass are light-grid lit in 100 % of cp_disco (19,588 of 19,604 instances: flags grid; 285 of 285 in the station) [m: `m4_smodel_light.py`]; so stock models do not use the lightmap either, and their materials reach the screen through our pipeline unchanged (a static model keeps its model materials; only lifted WORLD surfaces lose blends, `wc/` decals and probes [r: C1-CONTROL.md, R2-PARITY.md 2, 3]).

### 2.2 The station hall's size and rhythm [m: `m5b_profile.py`, QUALITY-BAR A3 for the pitch]

Floor z 286 along the whole east station. Per column of a ray profile at y 2466 / 2760 / 3040: platform clear height at the walls 271 (ceiling z 557) and a low band of 75 to 85 clear at y 2466 (z 361..372: a landing or bridge); the vault rises from 286 clear at the platform edge to **396 clear at the crown** (z 681) over x 160..480 and the same on the other side; the train roof stands 125 to 133 above the floor; the canopy at the east edge 271. Platform clear width 434 to 438 (rays at x 900 and x 250) [m: `m5_dims.json` p25]. The first worker's median widths of mezzanines (531) and tunnels (165 to 270) are noisy (rays escape through openings: p25 to p75 of 250..1,537); passages and tunnels measure 128 to 149 clear, the one open mezzanine 264 [m]. Column row: pitch 288, one row a platform, columns at x 332 and 808 [r: QUALITY-BAR A3, confirmed by my section 2.4 for three columns]. The Arcade's 244 grid and 256 slab sit between the passage heights (128..149) and the platform spring (271): keep the height.
Street frontage: facades at y 4765, curb at y 4560, sidewalk 200 wide at the Lounge (x -2060: floor z 750 from y 4560 to 4760), open plaza at x -1500 [m: `m5b_profile.json`]; shop fronts are 380, 440, 470, 515, 740 wide [r: QUALITY-BAR A1]; ours are 320 and 650.

### 2.3 Construction models of the east station, by hand (not by regex)

`k1\m7b_hand.py` -> `m7b_hand.json`, 327 models in the box to z 700, 0.351 per 1,000 (0.318 without the 30 train body pieces):

| Category (assigned by reading each model name) | Count | Share | Models |
|---|---|---|---|
| litter, cartons, bags, bins, debris, tools (no trade) | 198 | 61 % | food_trash_container_02_open x22, burger box x20, trashbundle x13, trashbag x10, rp_trash_can_* x24, paper debris |
| cable run, hanging wire | 52 | 16 % | slava_crane_tower_wire_82_01 x36, ceiling_mob_wire_bundle_01 x8, hanging_wire_02 x3, bridge_skyway_wires_hanging_* x3, greece_elec_wire_01 x2 |
| train body pieces (not the hall) | 30 | 9 % | subway_car_* (doors, windows, bumpers), locomotive headlights x8 |
| light housing | 21 | 6 % | me_lightfluohang x7, _onebulb x3, _damaged x3, _on x2, hanging ceiling lamps x4, clk_emergency_light x2 |
| hall construction | 17 | 5 % | loudspeaker x6, ind_debris_metal_pipe x3, stairway bars x2, greece_pipes_02 x2, fuse box x2, crr_deckbox x2 |
| transit furniture | 5 | 2 % | worn subway bench x2, metal trash can x3 |
| wayfinding | 4 | 1 % | exit sign x2, ow_sign03 plate x2 |

**No pillar, wall piece, ceiling piece, trim, cornice or rail among them.** The regex of the first worker counts 44 "construction" instances in the platform box; read by hand they are 20 cables, 13 train pieces, 6 loudspeakers, 3 debris pipes and 2 gate bars. Counts of `name`-regex categories are therefore not construction.
Per 288 bay (east platform x 660..1110, 288 long): 28, 31, 46 props and 20, 23, 25 distinct; west platform 40, 20, 30 props and 24, 13, 20 distinct [m: `m6_parts.json`].
The fixture counts agree with QUALITY-BAR: 14 hanging tubes of which 1 on [m].

### 2.4 The stock column, from its world triangles [m: `k1\m10_column.py`]

Three columns measured (x 332 / 808, y 2610 / 2898; floor z 286), `k1\m10b_column.py`: the vertical faces of each column read per material, with the MINIMUM AND MAXIMUM vertex height of each material (the first pass binned centroids in 20-unit bands and gave wrong courses; these are the vertex extents). Heights are above the floor.
- **Base 12 high**, 34 x 34, `w/metal_painted_02_dark` (z+0..+12; one column has a 57 x 57 plinth).
- **Shaft 32 x 32 with 3-unit chamfered corners** (the diagonal faces total 178 square units against 1,403 to 1,485 for a main face: an 8-face section), tile from +12 to +80: in the blend `*824n_4_108n` (white tile with leak and rust layers), the same position is `dt_tile_ceramic_white` / `_dmg` on the cleanest column; a damaged `_dmg` course +65..+80 on one column and +91..+127 on another.
- **Blue band 11 high** at +80..+91, `w/dt_tile_ceramic_blue_01`.
- **White course 36 high** at +91..+127.
- **Collar 24 high** at +127..+151: `w/fac_tile_black_01` on the 4-high lower lip (or the whole 24 on two columns) and a 16-high blend inset (`*555n_274n_4`, `*824n_4`) between +131 and +147.
- **Cap +152..+224 (72 high)** in `*1173n_274n`, which is `w/brick_wall_14_white_painted` with `w/concrete_wall_rustic_01_rvl` on it [m: `m3_wear.json` example], with a 2-high `w/concrete_wall_grunge_01` ring at +224..+226; steel (`w/metal_painted_02_dark`, `w/frag_metal_trim_gray`) from +142 / +161 to +240: the girder, **underside +161, top +240**; the column continues above +240 (my box ends at z 520 = +234).
The wear is blend: the shaft's lowest 68 units and the cap are blend materials. Stock frames: `subway_east_1/3/4` show the same column with graffiti and a rust-stained foot.

### 2.5 Two stock shopfronts, by hand [m: `m7_cats.py` / `m6_parts.json`; the shop models are few, so the regex rows were checked by eye]

| | Pink Cat (740 wide; 310,800 sq) | Pizzeria (440 wide; 184,800 sq) | The Lounge (380; 159,600 sq) |
|---|---|---|---|
| Static models / per 1,000 / per 100x100 | 203 / 0.653 / 6.53 | 51 / 0.276 / 2.76 | 136 / 0.852 / 8.52 |
| Hero sign model | `cp_disco_pk_marquee_01` 280 x 128 x 142.5, 1,224 tris, 7 materials; `sign_city_neon_arrow_01`; 6 `zmb_fe_neon_tube_wavy_02` (184 long) | `cp_disco_bng_marquee_01` 344 x 136 x 128, 330 tris, 8 mats; `cp_disco_pizzeria_sign` 378 wide | `cp_disco_tl_marquee_01` 188 x 8 x 107.5, 1,180 tris, 7 mats |
| Bulbs, recessed lights | 59 (26 `zmb_fe_theater_entry_recessed_light_01_on_dim`, 20 incandescent bulbs, 5 backlit, 4 off) | 12 bulbs | 59 (29 + 9 bulbs, 15 `cp_disco_theather_recessed_blue_light_01`, 6 backlit) |
| Poster and frame models | 10 `cp_disco_marquee_frame` 4.4 x 40 x 70 (eye level) | none | none |
| Awning pieces | none | 5 `cp_disco_modular_awning_middle` 65.3 x 59 x 45.9 + left + right (66.4 x 64 x 46.9) | none |
| Doors | `door_metal_service_01` 11.4 x 49 x 96.1 | `cnd_handle_door_u` x2 (15.7 x 4.2 x 17.1) | `cp_disco_storefront_doors_left` x2 (9.4 x 48.4 x 104) |
| Trim, bracket | none | `p7_sin_rowhouse_set_f_trim_40` x3, `_corner` x3, `_136` x2 | `p7_ibeam_bracket_32_thin_l_01` x4 (32 x 10 x 17) |
| Pipes | none | none | `alien_crafting_pipe_01` x8, `com_standpipe_double` |
| Neon | 6 wavy tubes, arrow | `cp_disco_pizzeria_sign` (neon words) | `cp_disco_peepshow_neon_sign` x2, `neon_open_sign_on_02` x2 (42.8 x 18), woman silhouette x2 |
| Goods and litter | 115 (magazines x12, queue poles x15, cash registers x4, stools x4, file cabinets x8, trash) | 16 | 55 (letters of the sign, trash) |
| Distinct materials on the models | 58 | 21 | 45 |

What the facade slab and the floor are made of [m: `m3_wear.json`, box `[-2760, 4690, 745, -215, 5110, 1010]`]: walls 61 % plain and 30 % blend, floors 57 % plain and 41 % blend, ceilings 76 % plain; bases of the blends `sidewalk_concrete_03_wet3`, `plaster_wall_04_grey_dark_02`, `frag_plaster_yellow`, `cp_disco_sidewalk_01_wet`; layers `wall_stain_01_dec` (288k), `has_plaster_worn_01_dec`, `dirt_stain_leaking_01`, `brick_wall_13_red_plaster_dec_wet`. So a shopfront is a plain brick or plaster slab with sign and marquee MODELS in front: the part of a shopfront that models carry is the part reviewers called "primitive box geometry": hero sign, marquee, awning, doors, bulbs, poster frames.

### 2.6 What can be made from models alone today, and what waits

Of a stock-looking hall frame (the station): models 17 %, world plain 20 % (exact stock material on an authored surface: tile, concrete, metal, all "plain"), world blend 62 %, decals 1 %. Of a stock shopfront frame: models 41 %, plain 23 %, blend 34 %. [m, 2.1]
- **Makeable today at stock fidelity:** 37 % of a hall frame (models + plain world), 64 % of a shopfront frame. Materials: of the 55 plain wall, floor and metal materials I tested, 15 are drawn by the template and 40 are brought; none failed [m: `matverdict.json`]. Models: the final parts list passes `studio check` with `ok: true`, no errors, 147 distinct models, 41 materials, 14 `w/` decal materials [m: `partscheck2.json`, `partsdoc2`, 9.6 s].
- **Makeable only as an approximation:** the 62 % blend share of a hall frame. The blend's BASE material is plain and usable (the lift already draws it); the layer mix of dirt, wet and damage is not. What stands in for it: decal quads (`B.decal`; the 14 `w/` decal materials of `partsdoc2` all pass `studio check`) and authored geometry. The drawable share of the blends' layer area (summed over blends, layers overlap, so this is not a coverage) is **69 % on the platforms and 19 % on the mezzanine**: platforms use `asphalt_flooring_stain_01` (41 %) and `ceiling_waterstains1` (29 %), both drawn by the template with the multiply technique (`w_unlit_multiply_lin_ndw`); the mezzanine's wear is `plaster_damaged_07a_dec` (51 %) and `has_peeling_painted_concrete_01_rvl` (46 %), neither drawable [m: `m3_wear.json`, `store.materials.verdict`]. A decal quad is a flat projected rectangle with its own mask, not a vertex-weighted layer; whether the BROUGHT decal materials (not in the template: `stain_leak_rust_01_dec` and `_mult`, `concrete_stain_01_dec_wet`, `plaster_damaged_03_crack_dec`, `mtl_concrete_crack_01`, `cp_disco_graffiti_03`) draw with alpha or as opaque rectangles is not shown by any frame: R2-PARITY section 3 says the compiler gives a material the template does not use "lit opaque" flags (risk R2, step 3 settles it).
- **Waits for R2 (limit, place, change):** (1) the layer weights and layer bytes: the compiler zeroes the vertex layer stream (`iwzmap.cpp` 2427-2428, `tris.vertexLayerData = 0` at 2188), Studio never reads the colour (`studio/prefab.py:288-291`, `expand_object` 392-398, 531), the world writer writes 255,255,255,255 (`mapgen.py:117`): R2's patches 1 to 5; effect: blends (187 materials, 32.7 % of a lifted room) and, for authored geometry, the five stock decal materials that read per-vertex data (`water_puddle_footprints_02`, `plaster_damaged_07a_dec`, `t7_decal_grunge_garbage_spread_01_reveal`, `has_peeling_painted_concrete_01_rvl`, `concrete_wall_rustic_01_rvl`: `MATERIAL_NOT_DRAWN`). (2) `wc/` decal and glass materials (blood smears, chain-link fence, cracked glass, scuffs): `render_material` returns None (`prefab.py:389-398`) and `B.decal` takes `w/` materials; our authored surfaces cannot use them. (3) Reflection probes (neutral cube per room, LIGHTING-GAP W4) and SSAO (off on client cells, C1): independent of construction; they cap the "wet and glossy" look. (4) Black floors of lifted rooms: not our case (our floors are our own material), but the cause is unknown; do not lift.

## 3. Our hall today, like for like

[m, `m7b`-style count on `C:\studio-data\sz\film\station\doc\layers`, the final document] 854 boxes (733 render-only), 341 meshes, 306 props, 72 distinct models; in the hall (x -3000..-1200, y 3500..4300): 89 props (32 distinct), 246 boxes, 0.062 props per 1,000 against stock 0.306 to 0.318. 293 decals, 282 of them our pictures (signs) and 11 wear decals of 142,200 square units, about 3.4 % of the hall's 4.2 million square units of surface [a: floor 1.44 M + ceiling 1.44 M + walls 1.33 M]; stock's wear carriers (blend) are 40 to 71 % of its hall surface (2.1). Hall construction today: 6 columns as 40 x 40 boxes with three render boxes each; a ceiling of one plane plus about 76 T-bar boxes plus panel boxes; fronts as 3 x 3 box mullions (`frame_v`), thin glass boxes, a three-box "door leaf"; the roll shutter a box; the photo booth and counters boxes. That is what reviewers called "flat extruded slabs".

## 4. The parts list

Legend: **S** the model has a sheet in `C:\studio-data\store\cache\show` (someone looked at it), **U** not seen (14 of the 147 candidate names have a sheet, 8 of the 57 models of the table; the fit of the others is NOT established by bounds: step 1 of the plan is `store show` on all of them, which starts ZoneTool and I did not run). Where a part appears in a stock frame or in a stock shop box, "stock use" says so [m: section 2]. Bounds are the xmodel dump's own (`m9_listbounds.json`), width x depth x height of the model's local axes at the scale given; scales are uniform [r: `build.prop`], so a piece is scaled only where I say so. Triangles are lod 0 [m].
"Replaces" names the function of `tools-source/iwzmap/station_zero/film/` read today: `arcade_shell.py` (`columns` 249-263, `tile_courses` 208-247, `ceiling` 287-316, `unit_room` 319-339 piers, `fascia` 341-348, `frame_v` / `glazing` / `door_leaf` 350-377, `shelving` 396-416, `counter` 424-431, `needle_drop` 441-498, `copy_stop` 500-571, `photo_booth` 572-590, `hole_nine` 592-646, `heel_key` 648-705, `south_wall` 707-749, `west_end` 751-776), `shell_hall.py` (`hall_life`, `kiosk`, `abandonment`, `fronts_by_models`), `shellgeo.py` (only `cylinder`, `torus`, `ribbon`, `merge`, `yaw_points`: no bevelled box, no extrusion: the authoring library of step 2 is new).

### 4.1 Authored meshes (no stock piece exists): spec, never a plain box

Every one is built render-only with a separate clip box (`solid`) for collision (a mesh in mode `both` makes the same triangles the collision: 65,535 triangles a surface, and a bevel would be a collision edge [r: INVENTORY.md section 2]); every edge on a visible silhouette is bevelled or chamfered (0.75 to 3 units, 45 degrees); UVs in tile repeats, one repeat = the stock tile's size (`UV = 32` in `shellgeo.py`; stock tile module to be read from the material's image: step 2).

Material tags: **(CD)** the material is in `techsets_cp_disco` (one donor kit) [m: `store.materials.verdict` zones, 28 Nov]; **(OUT)** not in cp_disco, kept only for a brand colour or an emissive and listed as a decision [a]: `w/ceramic_tile_01_orange` (mp_depot only), `w/emissive_light_panel_white`, `w/zmb_brushed_metal_01_blue`. The current shell also uses `w/ceiling_tile_01`, `w/metal_aluminum_trim_03`, `w/rubber_trim_black`, `w/wood_antique_panel_trim_01` (cp_zmb, cp_town and other zones, not cp_disco): replaced here by the cp_disco twins named in the rows.

| Part | Count | Spec [m from the stock column, a for the rest] | Materials (all stock, plain) | Replaces |
|---|---|---|---|---|
| Column, with base, shaft, band, collar, cap | 6 (existing pitch 288; one more at the east end if the lead wants it) | base 34 x 34 x 12 with a 2-unit top chamfer; shaft 32 x 32, 3-unit chamfers over the whole height; tile +12..+80 with a damaged twin course +65..+80 on columns 1 and 4 and +91..+127 on column 3; band 11 high at +80..+91 standing 0.8 proud (stock blue `dt_tile_ceramic_blue_01`; ours the orange of the 5-tile kit, below); white +91..+127; black collar 24 high at +127..+151 standing 1.5 proud with a 45-degree lower edge; cap +152..+224 in painted brick, flange 28 x 36 to 28 x 40 at +154..+194 and a steel girder stub +161..+240 (the grid is at 244) | `w/dt_tile_ceramic_white` (CD), `_dmg` (CD), `w/ceramic_tile_01_orange` (OUT: mp_depot only), `w/fac_tile_black_01` (CD), `w/metal_painted_02_dark` (CD), `w/brick_wall_14_white_painted` (CD) | `columns()` boxes (6 x 4) |
| Girder between column caps (5 spans of 254 clear along the colonnade line y 3860) and 3 cross girders to the south wall | 8 | I-beam, **underside z 161, top z 240** as the stock girder (+161..+240 above the floor [m]); web 4 x 12, flanges 28 x 3 chamfered, four rivet rows as relief strips 0.6 high, end plates 3 thick with 4 bolt heads; it is an authored mesh, i.e. a lightmapped world surface, not a grid-lit model; stock has these as world brushes (frames `subway_east_1..4`: dark girders over the columns); clear height under them 161 (stock passages 128..149) | `w/metal_painted_02_dark` (CD), `w/frag_metal_trim_gray` (CD) | none |
| Wall dado courses: skirting, band, cap rail | 3 walls | skirting 10 high with a bevelled top lip 1.2 proud; band 16 high 0.6 proud with 45-degree edges; cap rail 8 high; tile joints are the material's; damaged twin patches (`_dmg`) on a rhythm, not random: at 9 stations along the south wall where benches and lockers stood | `w/dt_tile_ceramic_white` (CD), `_dmg` (CD), `w/ceramic_tile_01_orange` (OUT), `w/fac_tile_black_01` (CD) | `tile_courses()` (about 50 render boxes) |
| Floor edging | 5 runs | kerb strip 18 wide, 2.2 high at the walls with a 0.8 round-over, a 6-wide chamfered brass strip at the shop line; replaces the flat 0.25 boxes | `w/fac_tile_black_01` (CD), `w/metal_chrome_trim_03` (CD) | `floor_border_*` (5 boxes) |
| Suspended ceiling | 1 mesh, 368 panels (1,768 x 480 at 48) | panel 47.2 x 47.2 with a 4-unit recessed bevel (8 triangles), T-bar profile (inverted T, 1.4 web, 3 flange) 0.5 proud, 6 missing panels (plenum black; the cable bundles and wire drops of 4.2 hang there: the only visible cables), 9 dead, 8 stained, 12 live; hangers: 40 threaded rods 0.6 radius | `w/cp_disco_ceiling_tile_01` (CD; the shell uses `w/ceiling_tile_01`, a cp_zmb material, today), `w/metal_aluminum_brushed_clearcoat` (CD; instead of `metal_aluminum_trim_03`, not in cp_disco), `w/emissive_light_panel_white` (OUT: moon_port and mp zones; no cp_disco emissive panel tested) | `ceiling()` (plane + about 76 T-bar boxes + panel boxes) |
| Storefront frame (one generator, four finishes) | 4 fronts | mullion 3.2 x 3.6 with 0.6 glass stops, sill with a drip lip 4 deep, kick plate 30 high with a bevelled cap, transom bar, door head; openings sized from stock modules (below) | `w/metal_painted_01_black` (CD), `w/metal_panel_painted_01_white` (CD), `w/metal_aluminum_brushed_clearcoat` (CD), `w/wood_antique_flat_trim_darkbrown_01` (CD, instead of `wood_antique_panel_trim_01`) | `frame_v`, `glazing`, `rbox` frames |
| Roll-shutter curtain | 3 (ND quarter down, HN open, CS up) | slats 2.4 pitch as 0.5 relief, side guides 3 x 4, a bottom bar from the stock piece | `w/cp_disco_metal_door_rollup_01` (CD) | shutter_`<unit>` boxes |
| Photo booth, Copy Stop (no stock model: INVENTORY section 4, 0 hits in all IW7 zones) | 1 | 40 wide x 44 deep x 96 high; cabinet with bevelled 1.5 edges, header light box with a 1.2 recessed lens (emissive), fixed 18 x 24 mirror panel, coin plate with slot (`fac_outlet_brushedmetal` 6 x 9 is the nearest stock plate, scale 1.3), photo-strip slot, stool 12 radius chrome; the curtain is the stock model below; wear: dented lower panel via normal-less relief, a worn patch on the stool top | `w/zmb_brushed_metal_01_blue` (OUT: cp_zmb only; kept for the Copy Stop blue, or tint `w/metal_panel_painted_01_white` by an own material), `w/metal_chrome_trim_03` (CD), `w/plastic_dark_matte` (CD, instead of `rubber_trim_black`) | `photo_booth()` boxes |
| Counters and joinery (Hole Nine's urn shelf, Heel & Key's counter and pegboard frame, Needle Drop's sleeve wall) | 4 | carcass with a 1.5 bevel on every visible arm, a 3-unit overhanging top with a drip edge, a kick recessed 2 deep, a back panel; goods are A3's | `w/wood_antique_flat_trim_darkbrown_01` (CD), `w/sz_arcade_pegboard` (ours) | `shelving()`, `counter()` |
| Directory board frame | 1 | 120 x 80 face with a 5-unit chamfered frame and a light-box depth 6 | `w/metal_aluminum_brushed_clearcoat` (CD) | `south_wall()` boxes |

Openings sized from stock modules [m: m9, section 2.5], not from the current 150-high openings: a leaf pair is 2 x 48.4 = 96.8 wide x 104 (`cp_disco_storefront_doors_left`/`_right`, the Lounge's), window frames 80 x 88 (`cp_disco_bsp_window_01`, white metal) and 60 x 92 / 60 x 120 (`cp_disco_windowframe_01/02_bsp2xmodel`, painted wood), grille 220 x 108 (`cp_disco_storefront_security_gate`), shutter housing 262 x 33 (`roll_up_door_top_02`). The 150 opening is kept for the shutter line (door 104 + a 46 transom); widths: Needle Drop 288 = pair 96.8 + two 80 panes + mullions and a 22 jamb return; Copy Stop 618 = two pairs 193.6 + two side runs of 2 x 80 + 52 of pier and mullion each; Hole Nine 288 = open serving front under the awning; Heel & Key 288 = the grille 220 + a 68 authored side panel. [a]

### 4.2 Stock pieces: exact names, bounds, counts

Totals of this table [m: `k1\parts_table.py`, `parts_table.md`, re-run after the review]: 57 distinct models, 276 instances, **344,290 triangles at lod 0**; of which the bulb strip `cp_disco_bulb_strip_01` (8,160 triangles each, 11 instances: 89,760) is 26 % (risk R3) and the three duffle bags 43,488 (a 14,496-triangle model: replace by `misc_duffelbag_01`, 3,642, or drop to 1). Hall 197,480 over 224 instances; Needle Drop 29,558; Copy Stop 51,086; Hole Nine 42,248; Heel & Key 23,918. Only VISIBLE props are counted as hall density: the 30 cable runs of `slava_crane_tower_wire_82_01` (13 x 82) of the first draft are gone, because the suspended ceiling leaves a 12-unit plenum (grid 244, slab 256) behind six 48 x 48 holes: what shows is the 7 bundles and 3 wire drops hung through the holes, 2 wall cables and 27 conduit pieces on the south wall.
Zone codes: hall; ND Needle Drop, CS Copy Stop, HN Hole Number Nine, HK Heel & Key.

| Zone | Role | Model | Bounds at scale | Count | Scale | Tris | Seen | Replaces |
|---|---|---|---|---|---|---|---|---|
| hall | hanging tube, dead or damaged | `me_lightfluohang_damaged` | 12.9x55.4x4.6 | 4 | 1 | 2984 | U | cp_disco_fluorescent_light_off x4 (ceiling(), tube_dead_*) |
| hall | hanging tube, one bulb | `me_lightfluohang_onebulb` | 12.9x55.4x4.3 | 3 | 1 | 900 | U | same |
| hall | hanging tube, off | `me_lightfluohang` | 12.9x55.4x4.3 | 4 | 1 | 1584 | U | same |
| hall | hanging tube, on (light via B.fixture) | `me_lightfluohang_on` | 12.9x55.4x4.3 | 2 | 1 | 792 | U | fix(ceiling_tube) x3 |
| hall | emergency lamp | `clk_emergency_light` | 26.5x8.5x7.6 | 2 | 1 | 1272 | U | none |
| hall | wall loudspeaker | `misc_wall_mounted_loudspeaker_01` | 3.8x14.2x26.2 | 5 | 1 | 3660 | U | none |
| hall | exit sign, lit | `signage_exit_sign_emergency_only_on` | 1.5x12.7x8.2 | 2 | 1 | 460 | U | none |
| hall | exit sign, framed | `signage_exit_sign_emergency` | 3x20.8x12.5 | 2 | 1 | 4484 | U | none |
| hall | wall clock | `sign_clock_04` | 18.5x3x18.5 | 1 | 1 | 480 | U | none |
| hall | cable bundle through a missing panel | `ceiling_mob_wire_bundle_01` | 8.1x6.4x102.3 | 7 | 0.9 | 12236 | U | HOLES (6 black panels) |
| hall | wire drop | `hanging_wires_01_multicolored` | 9.7x24.1x58.4 | 3 | 1 | 4686 | U | HOLES |
| hall | wall cable | `greece_elec_wire_01` | 177x3.1x7.9 | 2 | 1 | 3160 | U | none |
| hall | riser pipe, south corners | `greece_pipes_02` | 10.9x14.4x237.4 | 2 | 0.82 | 14396 | U | none |
| hall | standpipe | `com_standpipe_double` | 9.2x10.5x10.5 | 1 | 1 | 750 | U | none |
| hall | wall conduit, south wall | `com_electrical_pipe` | 4.8x76x1.7 | 18 | 1 | 1872 | U | none |
| hall | conduit outlet box | `conduit_metal_outlet_box` | 8x3x8 | 9 | 1 | 1188 | U | none |
| hall | bench | `cp_disco_worn_subway_bench` | 40x192x40 | 4 | 1 | 1864 | S | street_bench_long_iw6 x6 (shell_hall.hall_life) |
| hall | locker bank | `cp_disco_subway_lockers_02` | 18.8x29.2x73 | 4 | 1 | 7352 | S | kept (hall_life 3.) |
| hall | pay phone | `street_telephone_booth_old_iw6` | 27.7x24.8x84.9 | 4 | 1 | 10064 | S | cp_disco_street_telephone_booth x4 (south_wall) |
| hall | news vending box | `cp_disco_street_news_vending_01` | 29.2x28.1x54.3 | 2 | 1 | 1988 | U | none |
| hall | bin | `street_trashcan_metal_old_iw6_havok` | 25.5x24.6x46.6 | 3 | 1 | 12828 | U | cp_disco_street_trashcan_01 x3 |
| hall | advertising light box (poster case) | `zmb_poster_now_playing_07` | 7x48x72.5 | 4 | 1 | 1552 | U | south_wall(): four light boxes (boxes) |
| hall | notice frame | `p7_picture_frame_large_01` | 2.6x46x33 | 3 | 1 | 372 | U | none |
| hall | notice frame | `p7_picture_frame_modern_02` | 1x44x60.3 | 2 | 1 | 140 | U | none |
| hall | litter: newspaper | `newspaper_single_fn_01` | 13.3x16.7x1 | 24 | 1 | 10464 | U | rush_litter newspapers (shell_hall.night_it_stopped) |
| hall | litter: newspaper bundle | `newspaper_stack_fn_01` | 13.7x16.9x5.6 | 8 | 1 | 22576 | S | kiosk bundles kept |
| hall | litter: paper sheet | `com_debris_paper_iw6_01` | 59.8x46.7x4.4 | 8 | 1 | 1520 | U | none |
| hall | litter: paper sheet | `com_debris_paper_iw6_02` | 59.6x48x4.2 | 8 | 1 | 208 | U | none |
| hall | litter: loose paper | `office_paper_piece01_iw6` | 10x15.8x1.6 | 30 | 1 | 1020 | S | none |
| hall | litter: magazine | `com_magazine_english_single_01_dyn` | 9x12x0.9 | 10 | 1 | 1100 | U | none |
| hall | litter: cigarette ends | `food_trash_cigarettes` | 4.9x2.9x0.8 | 14 | 1 | 840 | U | none |
| hall | lost property: shopping bag | `misc_luxury_bag_01` | 8.1x19.8x19.9 | 2 | 1 | 2400 | U | none |
| hall | lost property: shopping bag | `misc_luxury_bag_02` | 9.9x17.1x11.2 | 2 | 1 | 2760 | U | none |
| hall | lost property: shopping bag | `misc_luxury_bag_03` | 22.2x17.3x4.5 | 2 | 1 | 2556 | U | none |
| hall | lost property: duffle bag | `cp_disco_equipment_duffle_bag_01` | 29.7x12.2x10.9 | 3 | 1 | 43488 | U | none |
| hall | lost property: duffle bag | `misc_duffelbag_01` | 19.7x21.9x37.5 | 2 | 1 | 7284 | U | none |
| hall | filler: trash bundle | `trash_can_garbagebin_trashbundle_static_no_logo` | 29.2x29.2x13.2 | 5 | 1 | 6480 | U | none |
| hall | filler: food container | `food_trash_container_02_open` | 8.4x12.5x8.1 | 8 | 1 | 3360 | U | none |
| hall | filler: burger box | `food_trash_burger_box_01_open` | 5x8.3x5.4 | 5 | 1 | 360 | U | none |
| ND | door, left leaf | `cp_disco_storefront_doors_left` | 9.4x48.4x104 | 1 | 1 | 704 | U | door_leaf(): 8 boxes |
| ND | door, right leaf | `cp_disco_storefront_doors_right` | 9.4x48.4x104 | 1 | 1 | 632 | U | door_leaf() |
| ND | door pull | `cnd_handle_door_u` | 15.7x4.2x17.1 | 2 | 1 | 1840 | U | rbox chrome bar |
| ND | door mat | `door_mat_coir_01` | 40.8x61.2x1.2 | 1 | 1.7 | 1276 | U | nd_threshold box |
| ND | poster case at eye level | `cp_disco_marquee_frame` | 4.4x40x70 | 2 | 1 | 5464 | U | none |
| ND | OPEN neon | `neon_open_sign_on_02` | 1.6x25.7x10.8 | 1 | 0.6 | 1340 | U | none |
| ND | bulb strip under the fascia | `cp_disco_bulb_strip_01` | 3.7x104.5x3.1 | 2 | 1 | 16320 | S | kept (fronts_by_models) |
| ND | shutter housing | `roll_up_door_top_02` | 50.9x288.2x36.3 | 1 | 1.1 | 534 | U | housing_`<unit>` box |
| ND | shutter bottom bar | `arch_rollup_door_bottom_dmg` | 16x287.2x33.5 | 1 | 1.12 | 1448 | U | shutter_bar_`<unit>` box |
| CS | door, left leaves | `cp_disco_storefront_doors_left` | 9.4x48.4x104 | 2 | 1 | 1408 | U | door_leaf() x2 (cs_leaf_w, cs_leaf_e) |
| CS | door, right leaves | `cp_disco_storefront_doors_right` | 9.4x48.4x104 | 2 | 1 | 1264 | U | same |
| CS | side window, white metal frame | `cp_disco_bsp_window_01` | 80x8x88 | 4 | 1 | 1200 | U | glazing(): cs_win_w, cs_win_e |
| CS | door pull | `cnd_handle_door_u` | 15.7x4.2x17.1 | 4 | 1 | 3680 | U | rbox chrome bar |
| CS | photo booth curtain | `cp_disco_curtain_left` | 3x33.8x103.7 | 1 | 0.85 | 1666 | S | photo_booth(): curtain box |
| CS | bulb strip | `cp_disco_bulb_strip_01` | 3.7x104.5x3.1 | 5 | 1 | 40800 | S | kept |
| CS | shutter housing | `roll_up_door_top_02` | 50.9x288.2x36.3 | 2 | 1.1 | 1068 | U | housing_`<unit>` |
| HN | serving counter, long | `cp_disco_disco_bar_03` | 224.1x96.6x38 | 1 | 1 | 1304 | U | counter(): boxes |
| HN | awning, left end | `cp_disco_modular_awning_left` | 73x70.4x51.6 | 1 | 1.1 | 1578 | U | none |
| HN | awning, middle | `cp_disco_modular_awning_middle` | 71.8x64.9x50.5 | 2 | 1.1 | 564 | U | none |
| HN | awning, right end | `cp_disco_modular_awning_right` | 73x70.4x51.6 | 1 | 1.1 | 1578 | U | none |
| HN | bar stool | `cp_disco_bar_stool_01` | 15x15x28.7 | 4 | 1 | 11640 | U | none |
| HN | bar stool | `cp_disco_bar_stool_02` | 15x15x28.7 | 3 | 1 | 8730 | U | none |
| HN | bulb strip | `cp_disco_bulb_strip_01` | 3.7x104.5x3.1 | 2 | 1 | 16320 | S | kept |
| HN | shutter housing | `roll_up_door_top_02` | 50.9x288.2x36.3 | 1 | 1.1 | 534 | U | housing_`<unit>` |
| HK | folding security grille (half down) | `cp_disco_storefront_security_gate` | 13.7x220.3x108.4 | 1 | 1 | 6144 | S | shutter_`<unit>` box (curtain) |
| HK | door pull / hasp | `cnd_handle_door_u` | 15.7x4.2x17.1 | 1 | 1 | 920 | U | none |
| HK | bulb strip | `cp_disco_bulb_strip_01` | 3.7x104.5x3.1 | 2 | 1 | 16320 | S | kept |
| HK | shutter housing | `roll_up_door_top_02` | 50.9x288.2x36.3 | 1 | 1.1 | 534 | U | housing_`<unit>` |

Stock use [m]: tubes (14 in the station, 1 on); loudspeakers (6); exit signs (2); `slava_crane_tower_wire_82_01` (36), `ceiling_mob_wire_bundle_01` (8), `greece_elec_wire_01` (2) in the station; `cp_disco_storefront_doors_left` x2 at the Lounge; `cnd_handle_door_u` x2 and `door_mat_coir_01` (scale 1.7) at the market; modular awning pieces x9 at the market, x7 at the pizzeria; `cp_disco_marquee_frame` x10 at the Pink Cat; `neon_open_sign_on_02` x2 at the Lounge; `cp_disco_bulb_strip_01` map-wide 85; `roll_up_door_top_02` 23, `arch_rollup_door_bottom_dmg` 5 map-wide; benches 8, lockers, phone booths 4. Others (disco bar 03, bar stools, curtain, bsp window, poster case) are placed elsewhere in the map or are unused catalogue pieces.
Also available and worth a landmark look, not in the list: `cp_disco_firstt_subway_entrance` 346 x 128 x 120 (2,732 tris, 7 materials) and `cp_disco_second_subway_entrance` 298 x 130 x 118: the stock stair mouth, a candidate for the west end's closed Shelter 7 door surround (step 6).
No stock piece, authored (4.1): column, girders, dado and floor edging, ceiling grid, copier, photo booth, key machine, record bins, directory board. No stock copier, key machine, photo booth, polisher turning, pinball, cassette (INVENTORY.md section 4).

## 5. The hall re-planned to stock proportions and density

Fixed (not touched): D4 `y 3804..3996` at x -1200, the unit x ranges (U1 -2960..-2640, U2+U3 -2630..-1980, U4 -1970..-1650, U5 -1640..-1320), the spawners, the wall buys, the closed Shelter 7 door, the 244 grid height. [r: PLAN section 3]

| Quantity | Today | Stock | Re-plan | Basis |
|---|---|---|---|---|
| Clear width (south wall face to bulkhead face) | 716 (y 3516..4232) | platform 434..438 [m] | **480** (south wall face y 3752): **PROPOSAL to the lead, it changes PLAN section 3's box (Y0 3500 -> 3736); the shops, D4 (D4 still opens into the clear hall, 52 from the south wall) and the lane north stay** | 480 is between the platform (438) and the mezzanine 531 [m]; reviewers: "too wide and empty" [r: REVIEW-1]; the clear area drops from 1,265,888 to 848,640 (-33 %) |
| Clear height | 244 under the grid, 256 slab | passages 128..149, mezzanine 264, platform spring 271, crown 396 [m] | unchanged | inside the stock range |
| Length / bay rhythm | 1,768 / pitch 288, 6 columns | pitch 288, 6 columns a platform [m] | unchanged: 6 columns at x -2860 + 288 k, bays of 288, 6.14 bays | same |
| Colonnade line | y 3760, 244 from the south wall | one row, 148 from the platform edge [m: x 332 in a 50..480 platform] | y 3860: 92 to the south wall, 34 column, 155 clear to the lane, the north lane 200 (y 4032..4232) | the lane is stock's 200 sidewalk [m]; bench islands (shell_hall ISLAND_Y 3950) keep 100 |
| Props in the hall | 89 | 0.306..0.318 per 1,000 = 260..270 on 848,640 | **230 floor (QB rule 8: 0.27), 260 target; the list of 4.2 gives 224 visible props, plus about 20 of the existing `night_it_stopped` clusters (gala table, cups, balloons, bouquets, litter) kept = about 244, i.e. 0.29 per 1,000** | [m] |
| Props per 288 bay | 14 | 20..46 (median 31 east, 30 west) [m] | **40 (244 / 6.14)** | box 288 x 480 = 138,240, 0.29 per 1,000, inside the stock bay range at its upper end |
| Distinct models | 32 | 13..25 per bay | **39 in the list of 4.2 plus about 8 existing: 47 in the hall, at least 20 in any bay** | QB rule 7 (19 per 100 props or more: 47 per 244 = 19) |
| Filler (cartons, trash) | high | 61 % litter in stock | **18 of 244 = 7.4 %** (trash bundle 5, food container 8, burger box 5) | QB rule 6 (8.8 %): the stock hall's 61 % is "litter, no trade"; ours is period litter with a cause (newspapers, papers, magazines, bags) |
| Wear coverage (our decals / surface) | 3.4 % | blend carriers 40..71 % [m]; local contrast of the floor band 0.15..0.21 [m: R2-PARITY metric rows] | **target, UNPROVEN: floor wear decals 25 % of the floor area (about 210,000 sq), south and west wall dado 15 %; check by the R2 metric (floor local contrast within 20 % of 0.15..0.21)** | [a]. Evidence that the carrier does not read today: `review1ramesrame_21.png` (`arc_west_long`) sees the lane floor around (-2000, 4180), where the final bake holds a 300 x 120 `asphalt_flooring_stain_01` decal: the floor there is a clean orange checker, no stain reads. Step 3 settles whether decal quads can carry wear at all before any wear is placed |

Props per 288 bay (40, computed from the list of 4.2): cable, bundle, conduit and box 6.4 (39 of 224; the stock 16 %), light housing 2.4 (15: 13 tubes, 2 emergency lamps; the stock 6 %), hall construction 1.3 (8: 5 loudspeakers, 2 risers, a standpipe; the stock 5 %), transit furniture and wayfinding 5 (31: 4 benches, 4 locker banks, 4 pay phones, 2 news boxes, 3 bins, 4 light boxes, 5 notice frames, a clock, 4 exit signs; the stock has 3 %, raised on purpose: an arcade is a place with benches, phones and notices), filler 3 (18), period litter and lost property 18.4 (113, named in 4.2: newspapers 24 and 8 bundles, paper 46, magazines 10, cigarette ends 14, bags 11). Each bay carries at least one ceiling hole with its hanging cables, one dead tube, one leak mark; the clusters of `night_it_stopped()` stay.
Where the numbers come from: stock east station 327 models, 297 without the train, in 932,800 sq = 0.318 per 1,000 [m]; ours 848,640 x 0.318 = 270; the list gives 244 (0.29): 14 props per bay today, 40 after.

## 6. Network cost and other budgets

- **Records:** the document's `build.networked_entities` is total 480, off 471, play 495 [m: `C:\studio-data\sz\film\station\check_final.json`: scriptables 214, player 1, script_model 147, script_brushmodel 24, power lights 0, gameplay 85, power-on 9]; cap 768 official, so 273 headroom (288 with one player). The predictor counts script models, script brushmodels, power lights, gameplay spawns and the reserved scriptables; static props never appear [r: `C:\studio\compile\recipe.py:598-612`; props go to `smodels.txt` and the rows contain no entity: `studio/based.py:456-483`]. So **the parts list adds 0 records**: stock models (static default), authored meshes (world surface), decals (world quads), baked fixtures. It adds a record only for a prop with `static=False` (a script model, +1 each, `recipe.py:605`) and for named runtime lights (power or flicker group). Rule for the execution worker: every part `static=True`; check `studio check` prints 480 before and after each step.
- **Collision:** a static prop has no collision of its own; only its `clip=` box [r: `build.prop` docstring, `expand.py:35`]. Collision shapes are not entities. Every piece a player or zombie can touch gets one clip box (benches, lockers, phone booths, counters, columns, the booth); everything above 72 units or on the ceiling none.
- **Triangles and draws:** 344,290 at lod 0 for the stock parts of the list [m], vs 105,136 render triangles and 36,498 collision triangles in the document today [r: I1-STATION.md] (I could not tell from the documents whether the 105,136 include the 306 props; read it as world surfaces only); the cap per surface is 65,535 [r]. No engine limit for model count was found; the stock maps hold 17,010 to 29,889 static models [m: `kit_compare.json`], the document 306 + 276 = under 600.
- **Lights:** unchanged: every fixture is baked (`B.fixture`), key lights stay bounce-baked runtime unnamed lights (no record, template slots 12 of 256 [r: I1]). New light housings carry no new lights except 2 live tubes and 2 emergency lamps' baked glow.
- **Live loop:** 83 of the 147 candidate models get no live slot (64 do): a model added after a build rebuilds the map (seconds, not 1 s) [m: `partscheck2.json` LIVE_MODELS]; the plan adds parts in batches before one `live start`.

## 7. Risks, and the check that settles each

| # | Risk | Evidence | Check (cost) | If it fails |
|---|---|---|---|---|
| R1 | Pipeline loses blends, decals and probes: stock-looking wear is not reachable by materials alone | C1/R2 [r]; 62 % of hall pixels are blend [m] | R2's metric on the hall frames (floor and ceiling local contrast, black share) against stock poses `subway_east_1..5` | decision rule of PLAN section 5 (1.0 / 2.0 gates) |
| R2 | Brought decal materials draw as opaque rectangles (compiler's lit-opaque default for materials the template lacks), and template-drawn ones may not read either: `frame_21.png` shows no stain from the existing `asphalt_flooring_stain_01` decal | R2-PARITY section 3 [r]; the review frame [m, looked at] | one live session, frames of `partsdoc2`'s `d_*` row: 7 template-drawn decal materials against 6 brought, on a wall under hall light (about 4 min with Forge warm) | restrict wear to the template-drawn set (asphalt_flooring_stain_01, ceiling_waterstains1, wall_stain_01_dec, dirt_stain_water_drips_01, dirt_stain_leaking_01, dust_leaves_cigarettes_dec, plaster_damaged_15_edge_dec) and author wear as geometry |
| R3 | Triangle cost: 344,290 stock triangles, 89,760 in bulb strips | [m] | frame time of one live shot with all strips against none (`forge` frame rate plan); LODs of the bulb strip: read `numLods` and distances in the dump | scale the strips to the stock use (one per 104.5 of fascia, not two rows), or an authored emissive bar of 200 triangles |
| R4 | Long STOCK models light flat. Our cp_disco models are twinless in the cp_zmb template, so each gets the neutral light-grid fit: 2 sample nodes whatever its size, lighting origin at its bounds mid-point [r: `iwzmap_smodel_rules.hpp` 30-60 `neutral_sample_nodes = 2`, `iwzmap.cpp` 1384-1433; `IWZ_SMODEL_UNK=zero` is an env switch, off by default]; stock gives models of 200..500 units a tree (median 7 nodes; 65 at 500 or more) [m: `m4_smodel_light.json`] | the shutter housing 288 (262 x 1.1), the grille 220, awnings 288 in four pieces of 72, marquee-like bulb strips 104.5, door pairs 97 (authored girders, columns and ceilings are lightmapped world surfaces and are not at risk) | one live shot: a housing and a grille beside a coloured pool, luminance along their length | a stock model cannot be split: accept the flat result, or replace that piece by an authored mesh (lightmapped); for awnings use the four 72-unit pieces as stock does |
| R5 | Fit: 133 of 147 candidate models never looked at; bounds do not say "1986 arcade" | 11 sheets exist [m] | step 1: `python -m store show <model>` for the list (starts ZoneTool: not run here) | strike the misfit, take the next of the catalogue (`m6_parts.txt`: 106 door and window, 175 awning and sign, 152 pipe and duct, 109 fixture, 113 trim and rail, 126 transit, 247 goods) |
| R6 | A wide model crashes the client (a LOD over 16 surfaces referenced from the base zone) | `compile/refbuild.py:170` [r], `zmb_souvenir_station_on` crash | `studio check` + one build smoke; the compiler keeps such rows in the map zone itself | remove the piece; surfaces per LOD are not read here (materials are the proxy: none of ours has more than 9); `refbuild` lists them in step 3 |
| R7 | Shadows of static props are baked from bounding boxes of the dump roots only | `studio/bake.py` dump roots fix, bench ratio 0.571 not re-measured [r: R2-PARITY 4] | one bake with the kit roots and a frame at a bench foot | accept bounds boxes |
| R8 | The narrower hall changes navigation, spawners and plans | proposal in section 5 | `studio check` (reach 61/61, no island, 1,403 cells), plans `i1_arcade.json`, `i1_walk.json` | keep the 800 box; make the 480 by a wall across the hall at y 3752 and leave the strip south of it as walled dead space |
| R9 | Authored meshes with bevels cost triangles and collision | mesh `both` mode makes collision = render [r] | every mesh render-only + clip boxes; `studio check` collision count | merge bevels into the clip |
| R10 | Records creep | 480 of 768 [m] | `studio check` after every step | none expected |
| R11 | Disk clean wipes the dumps and databases again | `docs/RESTORE-RUNTIME.md` [r] | `ops/restore` | restore before step 1 |

## 8. Build plan for an execution worker (files, steps, what each must show, when to stop)

Gate [r: PLAN section 5, "The decision rule"]: read the lead's decision from R2's lifted-room vote. Steps 1 to 3 are tools and checks and are valid in all three cases. Steps 4 to 7 start when the lifted room is within 2.0 of stock; at 1.0 or less go in parallel with R2's fixes, at 1.0..2.0 together with R2's first two ranked gaps, at more than 2.0 stop after step 3. No step touches `C:\forge`, `C:\studio`, `ops/` or R2's files.
Owner and place: SDK worktree `sdk-film`, branch `claude/sz-film-k1x` (new), files under `tools-source/iwzmap/station_zero/film/`; gate `python -B ops/quality/fast_gate.py --fix` before each commit; push each commit.

1. **Fit sheets (one background command).** `python -m store show` on the 147 names of `k1\partscheck2_names.json` (the 57 of the table first), read every sheet (Read tool) and mark each part `fits | scale | reject` in `film/parts_final.json`. Shows: 147 rows with a verdict; stop if more than 25 % reject (then re-choose from the catalogue, not from other kits).
2. **Authoring library (no game).** New `film/shellparts.py` (and tests in `film/plans`-style unit file): `bevel_box`, `extrude_profile` (I-beam, mullion, kerb, T-bar), `column()` to the spec of 4.1, `ceiling_grid()`, `dado()`, `storefront_frame(width, finish)`, `roll_curtain()`, `photo_booth()`, `counter()`; same conventions as `shellgeo.py` (inches, z up, uvs in repeats). Shows: each part's triangle count, a preview by `view.shot` on a one-part document next to the stock frame (column against `subway_east_1.png`), `studio check ok`. Stop: a part over 6,000 triangles (the column should be about 400).
3. **Three checks in the game (one live session, `forge sense` first, one session at a time).** On a document built from `partsdoc2` plus the new column: (R2) decal frames, (R3) frame time with and without the 11 bulb strips, (R4) housing and girder lighting. Shows: a frame each and the numbers; read them with the Read tool and say what each shows. Stop: if brought decals draw opaque, limit wear to the template-drawn set in 2.6; if a bulb strip costs more than 1 ms, change its count first.
4. **Hall body (first lead decision on the 480: proposal).** Edit `arcade_shell.py` `hall`, `tile_courses`, `columns`, `ceiling` to call `shellparts` (the whole of `columns` and `tile_courses` and the T-bar loop of `ceiling` go; the dead and live panel logic and the 12 + 9 + 6 + 8 module lists stay); `shell_hall.abandonment` adds the wear decals of section 5. Shows: `studio check` ok, reach 61/61, `networked_entities.total` 480, hall boxes 246 -> under 60, and 6 frames from the `arc_*` cameras of the document. Stop: reach below 61 or records over 480.
5. **Hall dressing to the density table.** `shell_hall.hall_life` and a new `film/hall_dress.py`: about 40 props per bay by the composition of section 5 (the list of 4.2: 224 visible props), every one static with a clip where touchable. Shows: `python -m studio density` per_1000 over 270 (QB rule 8) and rule 6 filler at most 9 %, distinct 55 or more.
6. **The fronts, one at a time** (Needle Drop, Copy Stop with the booth, Hole Nine, Heel & Key): replace the door leaves, windows, shutters, counters, booth by the 4.1 parts and 4.2 models; keep fascia pictures, anchors, light rows, goods hooks. After each: `studio check`, the front's frames at the stock shop eyes (`shopfronts_13`: a lobby at the front; `shopfronts_2`: the front square on) and the R2 metric. Stop: a front whose frames the Read tool shows as a flat card: send it back to step 2.
7. **Full build, bake, the nine plans, then blind review 2** (same form as REVIEW-1: our 14 frames among 14 stock). Bar: REVIEW-1 last paragraph (two of three "could ship", within one point of stock).

## 9. What was not done

- No `store show` (starts ZoneTool): 133 of 147 candidate parts unseen (49 of the 57 in the table). No game run: R2, R3, R4 unsettled. The share of stock decal area that reads as "dirt" to a viewer is not measured (a decal quad is not a layer).
- cp_disco is chosen by vocabulary and by materials, not by a blind comparison of the kits' frames: only cp_disco, cp_zmb and cp_final have stock frames on this PC and only cp_disco's sheets show a transit hall.
- The tile module (UV repeat) of `dt_tile_ceramic_white` is not read; the column's tile courses assume the 32-unit repeat of `shellgeo.UV` until step 2 reads the image.

Data and scripts: `C:\studio-data\sz\film\k1\` (`kit_compare.py/.json`, `m7_cats.py`, `m7b_hand.py`, `m8_pieces.py`, `m9_listbounds.py/.json`, `m10_column.py`, `parts_table.py/.md`, `partscheck2.py`, `partsdoc2`, `partscheck2.json`; the first worker's `m1` to `m6`, `matverdict`).
