# IWZ emit contract: what the zone build reads

An **emit folder** (a "compiler source", `level/src_*`) is the only interface between whatever authors a map (the Station
Zero generators, `scenegen.py`, the Blender exporter `tools-source/iwzmap/blender/blend2iwz.py`) and the zone build
(`build-sz2.ps1`, `build-g.ps1`, `build-blend.ps1`). This page lists every file, its format, who reads it, and what a
generic (non Station Zero) map must provide. Written 22 Nov 2026 from the readers' source: `iwzmap.cpp` of the ZoneTool
fork (`worktrees/x64-zt-iwz-map`, `compile()` at line 2775), the Python tools of `tools-source/iwzmap`, and `scenegen.py`.
Units are inches (x east, y north, z up), as everywhere in IW7. Workstream E of [BLENDER-MAP-PIPELINE.md](BLENDER-MAP-PIPELINE.md).

## Files

| File | Needed | Format | Read by |
| --- | --- | --- | --- |
| `world.bin` | yes | little endian. `u32 0x575A5749`, `u32 1`, `u32 nmat`, per material `u16 len` + name; `u32 nverts`, per vertex `<3f pos, f 0.0078125, 4B colour (255), 2f uv, 2f lightmap uv, u32 packed normal, u32 packed tangent>` (48 bytes); `u32 nindices`, `u16` indices **relative to the surface's firstVertex**; `u32 nsurf`, per surface `<5I material index, firstVertex, vertexCount, firstIndex (in indices), triangleCount> + 6f bounds`; `6f` world bounds. Normals and tangents are 10:10:10:2 (`mapgen.pack_unit`, w = 3). Writer: `mapgen.write_world` | `iwzcompile` (`read_world`), `bake/lmbake.py`, `preview/iwz_assets.read_world`, `iwz_emitcheck`, `sz2_*` checks |
| `colmap.hkx` | yes | Havok hk_2014.2.5 packfile, `hknpCompressedMeshShape` (scale 1/32), made by `hkcm_write.encode(tris, template colmap, tag, tags=...)` from the template `cp_zmb.d3dbsp.colmap.hkx`. One surface-table tag per triangle (default 382 = solid) | `iwzcompile`; `iwz_emitcheck`, `volume_check` indirectly |
| `navgraph.bin` | yes | bfx NavGraph resource, graph version 0x2B (`mapgen.nav_graph`): one quad area per 32 unit cell, 4 edges, kd tree. One floor height per column | `iwzcompile`; `iwz_emitcheck`, `sz2_navconn` |
| `ents.txt` | yes | map entity string, numeric hashed keys (`157` classname, `822` targetname, `543` origin, `65` angles, `638` noteworthy, `820` target, `60666` area, `61049` parameters, `497` model, `502` groupname, `599` radius, `636` linkname, `60661` animation, `60859` fxid, `687` spawnflags, `51961` dummy, `60803`). First entity is the stock worldspawn (`mapgen.stock_worldspawn`) | `iwzcompile`; `iwzmap_ents_lint.py` (server repository) |
| `triggers.txt` | no (empty file ok) | one line per trigger model `?IWZ<k>` / `?<n>`: `28000001 hx hy hz` (half extents). The k-th line matches the k-th `info_volume` | `iwzcompile` (trigger shapes) |
| `scriptables.txt` | no | `<stock scriptable name> 0 x y z yaw`: relocates a stock scriptable (perk machine, Pack-a-Punch, magic wheel) | `iwzcompile`; `sz2_assemble.py` (adds the models of a relocated `pap_machine`) |
| `smodels.txt` | no | `<xmodel> x y z pitch yaw roll scale [noshadow] [nocollision] [cull=<n>]` per static model; the model must be in the template dump | `iwzcompile` (`read_smodels`); writes `smodels.bounds.json` back; preview |
| `lighting.txt` | no | `ambient r g b up` and `room x0 y0 z0 x1 y1 z1 r g b up` (replaces the template light grid probes inside a box) | `iwzcompile` (`read_lighting`); the baker rewrites it with the baked grid |
| `probes.txt` | no | the `room` rows again (reflection probes, `IWZ_PROBES=neutral`) | `iwzcompile` |
| `smodel_bounds.json` | no | `{model: {mins [x,y,z], maxs [x,y,z]}}` bounds of static models that no dump holds (authored or ported models): the baked prop shadows read it first | `bake/occluders.py` |
| `lights.txt` | no | runtime lights (dynamic, written for every light with `runtime: true`; script switchable ones carry `name=`): `omni\|spot x y z r g b intensity radius [pitch yaw fov] [shadow] [name=<targetname>] [group=<script_noteworthy>]` | `iwzcompile` (`read_lights`); darkness tools |
| `lightmap/` (`primary.dds`, `secondary.dds`, `secondunorm.dds`) | no | the baked atlas; written by `bake/lmbake.py` into the baked copy of the source together with a `world.bin` whose lightmap uv point into it | `iwzcompile` (`prepare_lightmap`) |
| `layout.json` | for tools and the level script | see below | `scenegen` itself, `iwz_emitcheck`, `sz_modules`, `bake/layout_lights.py`, `volume_check --layout`, `sz2_plan/navconn/seams/flatness/artlint`, `preview`, `audio_layout`, `darkness` |
| `plan.json` | for `volume_check --plan`, `sz2_navconn`, preview overlays | `regions [{name, zone, rect}]`, `adj [[regionA, regionB]]`, `cells [[i, j, z, region]]` (32 unit cells), `cell_corners`, `blockers`, `col_tris`, `bounds`, `col_walls` | `build-sz2.ps1` (`volume_check`), `sz2_navconn`, `sz2_plan`, `preview` |
| `cp_iwz.gsc` | yes | the level script, from `cp_iwz3.gsc` with its `//@...@` markers filled (`scenegen.Emitter.level_script`) | `assemble.py` (copied to `scripts/cp/maps/<map>/<map>.gsc`) |
| `custom_materials.json` | yes (key `custom` may be empty) | `{"custom": {key: {path, base, tint, tga, ...}}, "used": [...]}` | `sz2_assemble.py` (reads `custom` only), `preview` |
| `modules/<map>_<name>.gsc` | no | game script modules; `//@MARKERS@` and `//@VOLUMES@` tables filled from `layout.json` by `sz_modules.py` | `sz2_assemble.py` (rawfiles after the level script) |
| `scene_report.json` | no | counts, entity census, problems | humans, `scenegen` |
| `bake.json`, `bake.npz`, `lights_groups.json`, `dark.bake`, `darkness.json`, `surfaces.json`, `plan.png`, `plan_check.json`, `flatness.json`, `fx_manifest.json`, `fxproof.gsc`, `iwzmap_sz2_local.gsc`, `preview_*.png` | no | outputs of the baker and of Station Zero only tools | preview (`bake.npz`), darkness build, humans. A generic map has none |

`iwzcompile` fails with `missing colmap.hkx / navgraph.bin / ents.txt` or a `world.bin` error; everything else is optional.
The compiler is run by `build-*.ps1` as `zonetool -iwzcompile cp_zmb_tpl cp_zmb <map> <src>` with `IWZ_GEN_TOME=1`,
`IWZ_KEEP_ENTSHAPES=1` and, when the map has doors, `IWZ_KEEP_SUBMODELS=1` + `IWZ_TRIGGER_SHAPES=1`.

### Free-form limits (what `mapgen` / `hkcm_write` / `lmbake` do with triangles that no brush generator made)

* **u16 indices.** `world.bin` indices are `u16` relative to the surface's first vertex, so one surface holds at most 65,535
  vertices. `mapgen.write_world` chunks 30,000 *indices x 3* assuming quads (2 triangles per 4 vertices); a mesh of unshared
  triangles (3 vertices a triangle) would overflow `struct.pack('<H')` at 21,845 triangles. The Blender exporter welds
  vertices and splits every material/object into surfaces of at most 20,000 triangles before calling `write_world`.
* **Degenerate triangles** (two equal corners, or zero area) carry no surface and **crash the dedicated server** in Havok
  (`sub_1410AD7F0`, W1a, 11 Nov 2026). `hkcm_write.encode` drops them; the exporter also drops them from the render mesh and
  counts both in `scene_report.json`.
* **Lightmap charts.** `bake/lmbake.py build_charts` makes one chart per *planar* group of triangles (same plane, same
  packed shading frame, welded by position at 1/8 unit). A flat wall is one chart; a curved mesh with per triangle face
  normals becomes one chart per triangle (each at least 1 texel; atlas size and bake time grow with the triangle count).
  The exporter always writes the face normal and a face tangent (as the brush generators do), never smoothed normals,
  because the lightmap direction term is encoded in the vertex shading frame. Authors should keep curved shapes coarse or
  flat shaded as props. Measured on a synthetic cylinder: see README of `tools-source/iwzmap/blender/`.
* **Axis aligned boxes.** Zone volumes (`info_volume` + `triggers.txt` half extents), the light grid `room` boxes, the
  door blockers (copies of the template sub-model `*12`, tiled along x or y) and spawn volume tests are axis aligned
  boxes. A rotated zone or door box is read as its world bounding box. A door must be thin along x or y (thin side <= 48).
* **Collision tags.** Only tags 382 (solid), 411 (stair clip sheet), 387 (riser), 402 (bullet only tread) are evidenced
  (`scenegen.py`, `station_zero2.py`); the stair tags are off by default because a build with them crashed the server in
  Havok. The contents/surface flags of the template surface table are **not decoded** in this repository, so "player
  clip only" and "monster clip only" cannot be told apart yet: a collision-only mesh is a solid (382) invisible brush that
  blocks players, bullets and zombies alike. A mesh may carry an explicit integer `iwz_tag` for experiments.
* **Navigation.** `mapgen.nav_graph` keeps one floor height per 32 unit column. The Blender exporter calls
  `navgen.generate(tris, seeds=starts, detail=True)` (workstream N, any number of floors) when `navgen.py` is importable
  (`iwzmap/` itself, or the folder in `IWZ_NAVGEN_DIR`); else it builds a single layer height field from the collision triangles
  (`blend_core.nav_single_layer`: the lowest floor reachable from a player start per column), reports every column where a
  second floor was dropped, and does not claim two storey navigation. `plan.json` `cells` then holds one entry per area (a column
  can appear twice); older readers of `plan.json` (`sz2_navconn`) assume one cell per column.

## Light settings: `layout.json` `lighting`, runtime lights, `smodel_bounds.json` (23 Nov 2026)

What a map document can say about its light, and who reads it. Every key is optional; without the block the bake and the build are as before
(the baker's 2 bounces, or the 3 that `build-blend.ps1` passes with `--default-bounces 3`; ambient 0.02, no sky), except that static props now cast baked shadows when the build passes model bounds (`prop_shadows`, default on; `build-blend.ps1` passes the template dump, `build-g` and the darkness builds pass none and bake as before). Measured on the Arcade (full bake, 144 rays, 3 bounces): mean lightmap E 0.36 -> 0.26 and indirect 0.150 -> 0.089 with the 1,258 boxes, bake time 122 s -> 124 s.

| Key of `lighting` | Meaning | Read by |
| --- | --- | --- |
| `prop_shadows` | `true` (default) / `false`: every static model of `smodels.txt` blocks light in the bake as the oriented box of its xmodel bounds. Limits: the box is solid (no gap between table legs); a model whose box holds a light, a box over `prop_shadow_max_extent` (200) units, a box under 3 units and a `noshadow` model are skipped (`bake.json` / the layout_lights report counts them); the light grid ignores the boxes. Bounds come from `<emit>/smodel_bounds.json` (`{model: {mins, maxs}}`), else `<emit>/xmodel/<name>.xmb`, else the dump roots of `layout_lights.py --dump` (build-blend passes the template dump) | `bake/occluders.py`, `bake/layout_lights.py` |
| `ambient` | a number (grey), `[r,g,b]`, or `{color, level, ao_radius}`: the fill light (default grey 0.02, blue x 1.1) | `layout_lights.py` -> `lights.json ambient` |
| `bounces` | indirect bounces (written to `lights.json` when set, else `--default-bounces`, else the baker's 2) | `lights.json bounces`, `lmbake.py` |
| `sky` | `[r,g,b]` radiance of the sky seen by rays that leave the map (default 0 = an interior) | `lights.json sky` |
| `sun` | `{dir [x,y,z], color [r,g,b]}`: baked sun visibility | `lights.json sun` |
| `emissive` | `{material: {color [r,g,b], strength s}}` (or `[r,g,b,s]`): the world material emits radiance `color x strength` in the bake (walls beside it take its colour from the bounces). The name rule (`*lamp*`, `*_on`) stays for materials not listed | `layout_lights.py` |
| `emissive_props` | `[{model, origin, angles, scale, color, strength}]`: a static model that emits (its bounds box, seen by the bounce rays). `blend_core` fills it from `props[].emissive` | `layout_lights.py` -> `lights.json occluders[].emissive` |
| `fog`, `exposure`, `vision` | the map's own look, `vision_edit.py`: `fog {color, density, start, max_opacity, intensity}`, `exposure {auto, value, adjust}` (`value` = tonemapExposure did not change the frame in the darkness runs dk3: unproven, use `adjust`), `vision {<stock vision key>: value}` rewrite `vision/<map>.vision` in the zone (assemble.py ships it as a copy of the stock cp_zmb vision); a key no stock vision file holds is refused. One look per map: a look that changes by zone needs a script call on zone entry and is not built | `sz2_assemble.py` |

Lights (`layout.json lights[]`): `runtime: true` writes the light to `lights.txt` too (an engine primary light, shaded per pixel, lights models by position).
`shadows: true|false` adds the `lights.txt` shadow token: the compiler picks a slot with `canUseShadowMap` and lists shadow casters, but writes
`needsDynamicShadows = 0` for every light and marks the shadow path "not engine verified" (`iwzmap.cpp build_com_lights`): a moving shadow is NOT proven; `bake: false` leaves a pure runtime light out of the lightmap (default: it is baked as well, which doubles its light on world surfaces if the engine
also lights them dynamically; check in game). The compiler reads `lights.txt` whenever the file exists: there is no switch (`IWZ_LIGHTS` is a generator
switch of Station Zero, the compiler does not read it). Limits (template cp_zmb): about 860 static spot and 140 static omni slots, 25 scriptable slots (named
lights, the range grows downwards), 459 of 1,039 lights can use a shadow map; the exporter refuses more lights than slots and warns over 64 shadow lights.
The compiler fixes a spot's inner angle (`max(fov/2 - 10, fov/4)`); `inner` of the document does not reach it. `layout.json runtime_lights` counts them.

## `layout.json`: keys by consumer

Always read as a dict; every tool uses `.get` except where noted.

| Key | Meaning | Needed by |
| --- | --- | --- |
| `map` | map name | `sz_modules`, `scenegen` |
| `zones` `{id: {name, box [x0,y0,z0,x1,y1,z1], boxes, floor, ceiling, far, probe, volumes}}` | zone table | `iwz_emitcheck` (labels), `sz2_plan`, preview overlays |
| `volumes [{name, zone, box, spawners}]` | spawn volumes (`info_volume`) | level script (`vol_of`), `sz_modules`, `volume_check` |
| `starts [[x,y,z]]` | player starts | `iwz_emitcheck` (required for reach), preview |
| `spawners [{zone, volume, origin, kind, yaw, on_nav, plate}]` | zombie spawn structs | `iwz_emitcheck check` (path to start), `volume_check --require-spawners` |
| `doors [{name, door, target, cost, zones, axis, plane, lo, hi, z0, z1, blockers}]` | debris door table | level script `//@DOORS@` (read in `Emitter.level_script`), `sz2_plan` |
| `openings [...]` | door/arch records with `zones` | `volume_check` (portal regions), `sz2_plan` |
| `interactions [{kind, origin, yaw, zone, ...}]` | placed stock interactions; wall buys carry `groupname == "wall_buy"` and `price` | level script `//@PRICES@`, `sz2_navconn` (generator), tests |
| `markers [{kind, id, zone, origin, yaw, area}]` | positions kept for game script modules | `sz_modules` |
| `lights [{zone, origin, type, color, radius, intensity, fixture, dir, inner, outer, group, name, fill, runtime, shadows, bake}]` | light list | `bake/layout_lights.py`, darkness |
| `lighting {...}` | light settings of the map (section above) | `bake/layout_lights.py`, `sz2_assemble.py` (vision) |
| `zone_links [[a,b]]` | zones joined without a door (spawn adjacency) | level script `//@LINKS@` |
| `navconn_routes [[regionA, regionB]]` | region pairs `sz2_navconn` proves | `sz2_navconn` |
| `stairs [{span, c, z, axis, zone}]` | flights, for the emit check stair profile | `iwz_emitcheck stairs` (optional) |
| `decor`, `models`, `power_fixtures`, `views`, `sign_views` | props and cameras | preview only (`models` and `decor` drive its props; `views` its cameras) |
| `walk`, `walkcap`, `quest`, `signs`, `geo_props`, `door_dress`, `fx`, `flicker`, `kit_models`, `decals`, `track_spec`, `train_spec`, `art_hooks`, `light_groups`, `genset`, `story`, `throats`, `conduits`, `junctions`, `signals`, `thresholds`, `pipe_chases`, `fx_placed`, `leaks`, `wheel_lamps`, `gallery`, `modules` | Station Zero only | Station Zero tools (`sz2_plan` needs `walk`, `audio_layout` needs decor/light names, the darkness tools need `light_groups`). A generic map omits them |

## Station Zero specific items and how a generic map gets by

| Item | Where | Station Zero | Generic map |
| --- | --- | --- | --- |
| `--gap-regions portal:a_tunnel_platform_b,...` | `build-sz2.ps1` `volume_check` call | four hard coded portal region names | not passed (`build-blend.ps1`); unknown names are inert in `volume_check`, but the gate then also reports cells outside every volume as failures, which is what a generic map wants |
| `sz2_submodels.json` | `scenegen.place_doors` / `door_blockers` | the sub-model `*12` of the template (half 69 x 7.5 x 81) picked by `sz2_submodels.py` from an iwzcompile log. It is a property of the **template** `cp_zmb` map, not of Station Zero | reused as is; `-KeepSubmodels` must be on whenever the map has doors |
| Door costs | `cp_iwz3.gsc` `iwz_door_purchases` hooks `debris_750/1000/1250/1500` | those four | `blend2iwz` refuses any other cost |
| `cp_iwz_perks` calls | `cp_iwz3.gsc` lines 6 and 367 (`init`, `register`) | `perks/add_perks.py` ships the module into the zone | **kept**: the level script links against `scripts\cp\maps\<map>\cp_iwz_perks`, so `build-blend.ps1` runs `add_perks.py` (and `add_perk_sounds.py`, `add_localize.py`) like `build-sz2.ps1`. The four new perk machines (`PerkMachines`, `DeadeyeKitDump`) are only needed when the map places `perk_new` markers; they stay default on, as in `build-sz2.ps1`, until a zone build without them is proven |
| Game script modules `quest`, `post`, `cap` | `sz_modules.emit` writes **every** file of `modules/` | Station Zero's quest and Capsule Post | the exporter points `sz_modules.MODULES` at the scene's own folder (empty by default): a generic map starts no module |
| `//@DARK@`, `//@AUDIO@` hooks | `cp_iwz3.gsc` | left as comments; darkness / audio are opt in build switches | untouched, stay comments |
| Third Rail trap (`//@TRAP*@`) | `cp_iwz3.gsc` `iwz_third_rail` | a fuse box struct and a box in the track pit | the markers are filled with zeros; `iwz_third_rail` returns when it finds no `iwz_trap_third_rail_fusebox` struct |
| `iwz_door_dressing` | `cp_iwz3.gsc` | models `iwz_doordress_*` | none placed, the loop does nothing |
| Audio layout | `audio/`, `build-sz2.ps1 -AudioSdk` | Station Zero bank | not used |
| Perk kit, kit models, FX import, darkness | `build-sz2.ps1` switches | Station Zero | optional switches, not part of `build-blend.ps1` except the perk kit above |
| Hard coded zone ids in tools | `iwz_emitcheck reach` (`platform_a`), `sz2_plan` (`walk`, `gallery`), `scenegen labplans` (`WALK_PAIRS`) | Station Zero | `iwz_emitcheck check` and `sz2_navconn` are generic; `reach`, `sz2_plan`, `labplans` are not used by `build-blend.ps1` |
| Wall weapon classes, perk and wheel scriptable names | `scenegen.Emitter.WALL_WEAPON`, `PERK_SCRIPTABLE`, `WHEEL_SCRIPTABLES` | stock template entities | reused through `blend_core` (subclass of `scenegen.Emitter`) |

## What the level script needs from the emit

`level_script()` fills: `//@DOORS@` (one `iwz_door(...)` per door), `//@LINKS@` (zone links), `//@INITIAL@` (the start
volume), `//@WHEEL@` (zone of the first magic wheel), `//@PRICES@` (wall weapon prices by place), the trap markers and
`//@MODULES@`. Stock systems also look up entities that every generated map must carry (`default_player_start`, 8
`player_use_trigger`, `mp_global_intermission`, the parked `hidden_room_portal`, `center_portal`, `fast_travel_tube_*`,
`hidden_travel_tube_*`, `hidden_room_spot`, `brute_hide_org`): `blend_core` emits them exactly as `scenegen` does.
