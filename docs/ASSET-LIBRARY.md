# Asset library: what the stock game offers a map, what a stock map reaches, what a generated map can hold

22 Nov 2026. Built for the three dense sections of the map builder ([MAP-BUILDER-FINAL](MAP-BUILDER-FINAL.md), line A4): to see
the stock models, to know the density a shipped map reaches, and to know the caps of the compiler. Code:
`tools-source/iwzmap/library/` (this page's tools) and `tools-source/iwzmap/catalog/` (catalogue, groups). Data lives outside
the repository, in `IW7-Runtime\iwz-blend\library\` (`IWZ_LIBRARY` overrides).

## What exists

| Item | Where | Command |
|---|---|---|
| Catalogue of every model of every dump on disk with LOD0 meshes (10,593 rows, 8 zones plus cp_rave and cp_town) | `library\catalog.json` | `pwsh catalog\build_library_catalog.ps1` (about 40 s) |
| Group and subcategory per model (architecture, structural, transit, retail, utilities, debris, furniture, vegetation, vehicles, misc; weapon, character, vfx, attachment are counted and kept out) | `catalog/iwzgroups.py`, fields `group`, `subcategory`, `resolves`, `lod0Tris`, `placements` | name based, a heuristic: look at the sheet before trusting a label |
| Contact sheets: 256 px tiles, 48 a sheet, 3/4 view with the textures, name, size in inches, triangles | `library\sheets\<group>\<zone>_<n>.png`, `sheets\index.json`, `sheets\failures.json` | `prep.py` then `sheets.py` |
| Picker | `library/pick.py` | `pick.py query --group retail --size-max 96 --zone cp_disco --text shelf`; `pick.py show <model> ...` |
| Stock density and Station Zero density, same measure | `library/density.py`, `library\density.json` | `density.py report --db <cp_zmb.sqlite> --src <emit src>` |
| Fastfile and dump inventory of the machine | `library/inventory.py`, `library\inventory.json` | `inventory.py --json ...` |
| Counts per zone and group | `library/report.py` | `report.py --md` |

The sheet renderer runs in background Blender (`blender_tiles.py`, EEVEE, neutral grey world and one sun): the sheets are data. The
map tool itself does not depend on it; `prep.py` (numpy, texconv, the preview's loaders `preview/iwz_assets.py`) writes plain
`.npz` meshes and PNG textures, which any renderer can take. There is no Blender asset library (dropped by the owner's change of direction).

`index.json` (exact, for a captioning pass): `{"schema": "iwz.library-sheets/1", "tile": 256, "cols": 8, "rows": 6, "sheets": {"<group>/<zone>_<n>.png": [{"name", "row", "col", "size": [x, y, z], "tris", "subcategory"}]}}`.
A tile is at pixel `x = col * 256`, `y = 22 + row * 296` (22 px title, 256 px picture, 40 px label). The zones of a model are in
`catalog.json` (`zones`, first one is its home zone, where its sheet is filed).

## Counts (catalogue of 22 Nov 2026)

Models per zone (a model counts under every zone it ships in) and group. `LOD0` = has LOD0 triangles, `resolves` = every texture of its materials has a file in a dump. Sources: `iwz-map-ref-a\dump` (cp_zmb, patch_cp_zmb, global_cp, global_core_mp, common_core_mp, mp_frontend, patch_cp_frontend), `iwz-stage2\kitimport\ztwork\dump` (cp_disco, cp_final), `chars58\ztwork\dump` (cp_rave, cp_town).

| zone | models | LOD0 | resolves | architecture | attachment | character | debris | furniture | misc | retail | structural | transit | utilities | vegetation | vehicles | vfx | weapon |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_core_mp | 462 | 439 | 387 | 5 | 184 | 10 | 22 | 5 | 31 | 1 | 1 | 0 | 1 | 2 | 60 | 129 | 11 |
| cp_disco | 3093 | 3039 | 2997 | 124 | 157 | 1155 | 230 | 121 | 192 | 215 | 219 | 105 | 325 | 47 | 14 | 186 | 3 |
| cp_final | 2423 | 2363 | 2322 | 30 | 145 | 832 | 178 | 57 | 228 | 137 | 231 | 53 | 332 | 42 | 1 | 157 | 0 |
| cp_rave | 2323 | 2269 | 2224 | 71 | 195 | 543 | 227 | 118 | 312 | 170 | 161 | 45 | 181 | 141 | 16 | 141 | 2 |
| cp_town | 2356 | 2311 | 2270 | 31 | 132 | 457 | 252 | 133 | 299 | 244 | 144 | 77 | 258 | 121 | 25 | 183 | 0 |
| cp_zmb | 2882 | 2866 | 2795 | 59 | 196 | 1282 | 80 | 64 | 220 | 251 | 193 | 119 | 179 | 76 | 12 | 149 | 2 |
| global_core_mp | 1044 | 1044 | 785 | 0 | 876 | 164 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| global_cp | 862 | 862 | 606 | 0 | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| mp_frontend | 42 | 42 | 28 | 0 | 9 | 1 | 3 | 1 | 2 | 0 | 1 | 0 | 0 | 0 | 1 | 20 | 4 |
| patch_cp_frontend | 18 | 17 | 14 | 0 | 1 | 2 | 3 | 2 | 1 | 1 | 2 | 4 | 2 | 0 | 0 | 0 | 0 |

10593 models, 5077 in the library (not weapon / character / vfx / attachment), 5004 of those resolve. The attachment and weapon columns are viewmodel and attachment meshes of global_cp and global_core_mp; the character column is zombie body parts and heroes.


## Density: stock map against Station Zero (target of acceptance line A4)

Measured with `density.py` (`library\density.json`). Stock = cp_zmb: the world kit database built from the dump
`iwz-map-ref-a\dump\cp_zmb` (`maps/cp/cp_zmb.d3dbsp.gfxmap`: 17,010 static model instances, 10,760 world surfaces with material and bounds,
1,039 primary lights; `cp_zmb.d3dbsp.ents`: script_model entities). Station Zero = the emit `iwz-stage2\level\src_g27r_lm`
(`layout.json` decor + models, `smodels.txt`, `surfaces.json` quads, `lights.txt`). No other stock map has a world dump on disk (see below).
A prop is a static model instance or a script model; materials are distinct world surface materials; lights are the primary lights in the box.
The cp_zmb areas are 1000 x 1000 windows (stride 250) inside the playable box (union of the 13 spawn volumes), ranked by props, only covered
ones (at least 60 % of the window under a horizontal surface 100 to 700 above the floor, so indoor), at most 25 % overlap. The Station Zero rows are the zone
boxes (x/y footprint), "props / 1000x1000" is the count scaled to 1,000,000 square units.

| area | box (x0 y0 x1 y1) | covered | props | distinct models | materials | lights | props / 1000x1000 |
|---|---|---|---|---|---|---|---|
| cp_zmb area 1 | -2022 -3568 -1022 -2568 | 0.90 | 840 | 162 | 138 | 38 | 840 |
| cp_zmb area 2 | -1522 -1318 -522 -318 | 0.84 | 636 | 150 | 185 | 31 | 636 |
| cp_zmb area 3 | -272 2682 728 3682 | 0.85 | 555 | 116 | 100 | 22 | 555 |
| cp_zmb area 4 | 2978 -1568 3978 -568 | 0.88 | 550 | 118 | 189 | 25 | 550 |
| cp_zmb area 5 | 978 -818 1978 182 | 0.78 | 512 | 137 | 130 | 24 | 512 |
| SZ ticket_hall | -1200 3200 400 4600 | - | 86 | 24 | 50 | 6 | 38 |
| SZ stair_a | -800 2400 -400 3200 | - | 23 | 4 | 22 | 3 | 71 |
| SZ platform_a | -2400 1200 2400 2400 | - | 152 | 38 | 51 | 13 | 26 |
| SZ maint_corridor | 2400 1680 3200 2400 | - | 45 | 15 | 21 | 8 | 78 |
| SZ generator_room | 2600 2400 3800 3200 | - | 79 | 29 | 27 | 4 | 82 |
| SZ control_room | 2600 3200 3600 4160 | - | 47 | 16 | 22 | 7 | 49 |
| SZ service_tunnel | -3600 1200 -2400 2600 | - | 47 | 17 | 19 | 27 | 28 |
| SZ platform_b | -3600 2600 -2064 3400 | - | 44 | 20 | 31 | 6 | 35 |
| SZ stair_b | -2064 3104 -1200 3400 | - | 41 | 4 | 20 | 2 | 160 |

Reading: the densest indoor 1000 x 1000 of the shipped map holds 510 to 840 props, 115 to 160 distinct models, 100 to 190 world materials and 20 to 40 lights. The
Station Zero zones hold 26 to 160 props per 1000 x 1000 (ticket hall 38, platform A 26), 4 to 38 distinct models a zone, 19 to 51 materials a zone.
**A4 target for a new section (per 1000 x 1000 of floor): at least 500 props, 110 distinct models, 100 world materials, 20 lights**; the stock median over the five areas is 555 props,
137 models, 138 materials, 25 lights. For the section of 1800 x 800 (1.44 million) that is about 800 props, 160 distinct models, 140 materials and 30 lights.

## Limits of a generated map

The compiler builds the new map inside the template map (cp_zmb) and reuses its slots. Source read: the x64-zt checkout
`worktrees\x64-zt-playeranim`, branch `claude/iwzmap-light-volumes-1dcd449` at `cf674e7` (the branch that carries `ea60b19`, the light-volumes compiler of the current
Station Zero release), files `src/zonetool/zonetool/iw7/iwzmap/iwzmap.cpp` (3,156 lines), `iwzmap_lightmap.cpp`, `iwzmap_smodel_rules.hpp`. Template numbers:
`iwz_ledger.py template_caps` on the cp_zmb dump.

| Cap | Value | Source |
|---|---|---|
| Static models (smodels.txt rows) | 65,535 (error "more than 65535 static models"); ids are u16 (`unk9 = i + 1`, `sortedSmodelIndices`) | iwzmap.cpp:378, 1395, 1428 |
| Static model of a model not in the template map (kit model) | no count cap; takes a neutral template instance and gets its model fields fitted; the zone must carry the model (kit import) | iwzmap.cpp:1329-1347, iwzmap_smodel_rules.hpp |
| World surface: vertices and triangles | 65,535 each per surface (`vertexCount`, `triCount` are `unsigned short`); `world.bin` indices are u16 relative to the surface's first vertex; the exporter splits at 20,000 triangles | iwzmap.cpp:2133-2134, 257, 2355; IWZ-EMIT-CONTRACT.md "u16 indices" |
| World surfaces in total, total vertices | no cap in the compiler (u32 counts, one transient zone holds all vertices); the cost is in the lightmap atlas and bake time | iwzmap.cpp:2355-2370 |
| Lights, unnamed | 1,010 static template slots (spot and omni between the last sun and the scriptable range); "no static template light slot left for a generated light" | iwzmap.cpp:1494-1512; `template_caps` |
| Lights, named (switchable) | 25 scriptable slots; the range extends over static slots, so named + unnamed together at most 1,035 | iwzmap.cpp:1462-1475; iwz_ledger.py:15-21 |
| Lights per voxel | omni count in 7 bits (127), spots 9 bits; voxel light lists at most 65,535 entries | iwzmap.cpp:1855, 1863 |
| Reflection probes | 160 cubes (one per room) | iwzmap.cpp:774; iwz_ledger.py:37 |
| Trigger and volume shapes | 142 template trigger models, minus the ones the source names itself (136 free for Station Zero) | iwz_ledger.py:73-85 |
| Entities | engine 2,048 slots, project ceiling 1,800 (entity list plus runtime: zombies, scripted props, effects); script models and door blockers count, static models do not | iwz_ledger.py:36; docs/station-zero/12-BUILD-PLAN.md TF8 |
| Lightmap | primary and second-unorm W x H, secondary W x 2H, W and H multiples of 4; width and height are u16; the template atlas is 4096 x 4096, Station Zero's 2048 x 2048 at 8 units a texel (982,500 texels, 23 %, 6,670 charts) | iwzmap_lightmap.cpp:119-124; bake.json of g27r_lm |
| Materials | no count cap; a material the template world does not use gets the template surface defaults ("using template surface defaults" warning) and must exist in the zone | iwzmap.cpp:2106 |
| Kit models and images | no cap in the compiler; each kit model adds surfaces and image headers (pixels stay in the base game paks); two techset zones loaded together with `require` hung ZoneTool | kit_import.py:1-27 |
| Visible static models in one view | 16,384 record bytes: reported at 6,040 props with no culling ("too many visible static models (record bytes 16392, limit 16384)"), so about 6,000 visible props; with the culling tome the kept props per view were median 877, max 3,013 for 6,000 placed | docs/STATION-ZERO-W1-ST1.md:75; docs/CULLING.md:80-90 |
| Umbra tome objects | at least one, no upper bound in the writer (`width` up to 31 bits) | iwzmap.cpp:113-117 |

**First cap hit by a section of 1800 x 800 with about 760 props.** If the props are static models (a placement line in `smodels.txt`): none. 760 of
65,535 is 1.2 %, 197 + 760 is far under the 6,000 visible; the nearest is the visible-per-view limit at about 16 % of it. If the props are
**script models** (anything that moves, is shot, or carries a `targetname`), the entity ceiling is the first cap: Station Zero's list holds 305
entities, so 760 more is 1,065 of 1,800 (59 %) before runtime entities (the prefab room alone showed 240 live ones), which leaves a margin of
about 500 for zombies and effects. So: dress with static models, script only what the game touches. The second constraint is the lights: 30 to 60 lights for the section is 3 to 6 % of 1,010.
The lightmap is the cap that scales with the section's surface area: Station Zero uses 23 % of a 2048 atlas; the shell of the section (about 4.7 million square units of floor, ceiling and walls at 8 units a texel) adds about 75,000 texels
before chart padding, so it fits; baking time follows the chart count (154 s for 6,670 charts).

## Dumps and fastfiles on this machine

Game folder `IW7-Runtime\private-test-server` (top level, `inventory.py`): 572 fastfiles.

| group | fastfiles | size | with a dump on disk | with a dump holding renderable models (xmodel + xsurface) |
|---|---|---|---|---|
| cp | 6 | 976 MB | 6 | 6 |
| common | 8 | 131 MB | 7 | 5 |
| mp | 380 | 4061 MB | 10 | 1 |
| patch | 85 | 121 MB | 12 | 2 |
| techsets | 86 | 319 MB | 12 | 0 |
| other | 7 | 55 MB | 3 | 0 |
| sp / campaign | 0 | - | - | - |

cp: cp_disco (179 MB, dump, 4426 renderable models); cp_final (203 MB, dump, 3576 renderable models); cp_frontend (15 MB, dump, 341 renderable models); cp_rave (202 MB, dump, 3444 renderable models); cp_town (170 MB, dump, 3705 renderable models); cp_zmb (206 MB, dump, 4096 renderable models).

common: common (10 MB, NO dump); common_core_mp (85 MB, dump, 649 renderable models); common_cp (13 MB, dump, no renderable models); common_mp (2 MB, dump, 36 renderable models); global (0 MB, dump, no renderable models); global_core_mp (15 MB, dump, 1062 renderable models); global_cp (2 MB, dump, 891 renderable models); global_mp (2 MB, dump, 1 renderable models).

other: code_post_gfx (12 MB, NO dump); code_pre_gfx (0 MB, NO dump); ui (40 MB, dump, no renderable models); ui_boot (3 MB, dump, no renderable models); ui_core_mp (0 MB, NO dump); ui_cp (0 MB, dump, no renderable models); ui_mp (0 MB, NO dump).

mp: 380 fastfiles, 33 of them maps (mp_afghan, mp_breakneck, mp_carnage2, mp_codphish, mp_depot, mp_desert, mp_divide, mp_fallen, mp_flip, mp_frontend, mp_frontier, mp_geneva, mp_hawkwar, mp_junk, mp_mansion, mp_marsoasis, mp_metropolis, mp_neon, mp_nova, mp_overflow, mp_paris, mp_parkour, mp_permafrost2, mp_pixel, mp_prime, mp_proto, mp_quarry, mp_rally, mp_renaissance2, mp_riot, mp_rivet, mp_skyway, mp_turista2). Dumps of 10 maps exist: mp_frontend (renderable) and mp_breakneck, mp_depot, mp_divide, mp_fallen, mp_junk, mp_metropolis, mp_quarry, mp_riot, mp_rivet in `iwz-stage2\assets\dumps` with `xmodel` only (473 to 1,025 model headers each, no `xsurface`, images or materials: not renderable). No dump at all: mp_afghan, mp_carnage2, mp_codphish, mp_desert, mp_flip, mp_frontier, mp_geneva, mp_hawkwar, mp_mansion, mp_marsoasis, mp_neon, mp_nova, mp_overflow, mp_paris, mp_parkour, mp_permafrost2, mp_pixel, mp_prime, mp_proto, mp_rally, mp_renaissance2, mp_skyway, mp_turista2. The other mp fastfiles are weapon, head, body and viewhand packs (mp_weapon_* 204, mp_head_* 59, mp_viewhands_* 42, mp_body_* 40).

patch: 85 fastfiles, 12 have a dump (patch_common_cp, patch_common_mp, patch_cp_disco, patch_cp_final, patch_cp_frontend, patch_cp_rave, patch_cp_town, patch_cp_zmb, patch_global, patch_global_mp, patch_mp_frontend, patch_ui). techsets: 86 fastfiles, 12 have a dump (cp_disco, cp_final, cp_rave, cp_town, cp_zmb, global, global_cp, global_mp, global_core_mp, common_cp, common_core_mp, common_mp); the material definitions of a zone live there.

There is no sp or campaign fastfile in the retained game folder. Dumps made but not in the catalogue: cp_frontend (341 models, `iwz-map-m2-a\dump`) and common_mp (36 models).

**Other Call of Duty titles.** GrayWolf (`graywolf_list_installs`) lists two installs: Black Ops III (Steam entry, install path `C:\Users\ezvalo\Desktop\bo3_game_files`; the Steam copy `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III` also exists with `BlackOps3.exe`) and Infinite Warfare (folder install `IW7-Runtime\iwz-map-ref-a`). The Steam library holds no other Call of Duty title. GrayWolf's export folder `C:\Users\ezvalo\AppData\Local\GrayWolf\mcp` already holds BO3 exports (BO3 model format) usable as map material: `props_metro` (95 files, 47 MB), `props_arena` (35 files, 6 MB), `props_veiled` (19 files, 7 MB), `props_waterpark` (54 files, 15 MB) and `models` (61 files, 45 MB), plus weapon, sound and fx exports. Nothing was exported for this page.

**Dumps that would add useful models.** The mp map dumps hold only `xmodel` headers; re-dumping them with `xmodelsurfs,image` and their `techsets_<zone>` would make their models renderable. By model names (subway, metro, train, station, platform, turnstile / mall, shop, store, checkout, shelf, mannequin / office / pipe, duct, generator, catwalk), counts per map: mp_riot 28 / 101 / 22 / 51, mp_fallen 30 / 67 / 12 / 47, mp_metropolis 21 / 20 / 21 / 92, mp_rivet 19 / 6 / 0 / 219, mp_divide 8 / 33 / 19 / 208, mp_depot 10 / 30 / 0 / 154. So mp_riot, mp_fallen and mp_metropolis (transit and shops) first, then mp_divide and mp_depot (shops, industrial). Not dumped at all: mp_paris, mp_geneva, mp_neon, mp_mansion, mp_pixel, mp_proto, mp_prime and 16 other map fastfiles listed above (23 of the 33 maps have no dump); their names suggest street, interior and industrial sets but nothing on disk says what they hold. A world dump (gfxmap, ents) exists for cp_zmb only; cp_disco, cp_final, cp_rave and cp_town are dumped for models, not for placements, so only cp_zmb gives a density reference. Dumping the world of cp_town and cp_disco would add two more.

## State

- Measured: catalogue build, prep, sheets (timings in the report of the run), density numbers, the inventory, 7 unit tests (`checks.json` id `tools-source-iwzmap-library`).
- Built, not proven by a person: the group labels (name heuristics, no review of every model), the pick tool's `show` command.
- Does not exist: a Blender asset library (dropped), sheets for models of the MP maps (their dumps hold `xmodel` only, no surfaces or images), a world dump of cp_disco, cp_rave, cp_town or cp_final.
