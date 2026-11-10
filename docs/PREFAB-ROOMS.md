# Prefab rooms: a room of a shipped map inside a generated map

A generated map used to be boxes written in Python. A room of one of the game's own maps can now be lifted out as
data (a prefab, [WORLDKIT.md](WORLDKIT.md)) and placed in a generated map: its walls and floors with their shipped
materials, its props, its lights and its collision. This document says what a map maker can do, with the commands,
what was measured on the first room (the spawn plaza of Spaceland, `cp_zmb`), and what is not reproduced.

Nothing here is deployed. Prefabs, dumps and built maps hold the game's data and stay outside the repository.

## From "pick a room" to "it is in my map"

All paths are placeholders. `<db>` is the worldkit database of the shipped map, `<dump>` the folder of its dumps
(`cp_zmb`, `patch_cp_zmb`, `techsets_*`), `<tools>` is `tools-source/iwzmap`.

```powershell
# 1. Find the room (seconds): what is around a point, or which grid cells are the densest
python -B tools-source/worldkit/iw7_world.py near  --db <db> 467 3677 0 --radius 600
python -B tools-source/worldkit/iw7_world.py rooms --db <db> --cell 512

# 2. Lift it out, then put it where the new map wants it (a turn about the vertical axis is allowed)
python -B tools-source/worldkit/iw7_world.py extract --db <db> --box -100 3100 -50 1000 4300 400 --name spawn_plaza --out <prefab>
python -B tools-source/worldkit/iw7_world.py place   --prefab <prefab> --at 2450 6200 78 [--yaw 90] --out <placed>

# 3. Give the prefab the shipped collision of its box (once; writes <placed>/collision.bin)
python -I <tools>/prefab_place.py collision <placed> --colmap <dump>/cp_zmb/maps/cp/cp_zmb.d3dbsp.colmap.hkx

# 4. Emit the map sources and read them before paying for a build (about 2 s each)
python -I <tools>/prefab_room.py <dump>/cp_zmb <placed> <src>
python -I -B <tools>/iwz_emitcheck.py check <src>

# 5. Build (compile, assemble, zone) under the shared build reservation
<tools>/new-work-from-stock.ps1 -Work <work> -StockRoot <retained test stock> -SeedWork <an existing ZoneTool work folder> `
    -ZoneTool <zonetool.exe> -TemplateDump <dump>                                  # once
<tools>/build-prefab-room.ps1 -Src <src> -UmOut <usermap>\cp_pfr -Work <work> -ZoneToolExe <zonetool.exe> `
    -TemplateDump <dump> -Scheduler <Resource-Scheduler.Core.ps1> [-Probes neutral] [-ZoneBuildExe <other zonetool.exe>]

# 6. Prove it in the game against the room it came from (server repository, ops/gamelab; one session per map)
python -I <tools>/prefab_proof.py plans <placed> <spec.json> <plans> --usermap <usermap>\cp_pfr
#    run <plans>/placed.json (the generated map) and <plans>/source.json (the shipped map) with Invoke-GameLab.ps1, then
python -I <tools>/prefab_place.py props-check <placed> <run of the generated map>\perf\cp_pfr-props-placed.json
python -I <tools>/prefab_proof.py compare <run of the generated map> <run of the shipped map> <placed>
python -I <tools>/prefab_proof.py frames  <run of the generated map> <run of the shipped map> --frame-tool <components>/ops/iw7_frame_evidence.py
```

A prefab left at its shipped coordinates (`place --at` the prefab's own origin, then `prefab_room.py --lighting
template`) keeps the template's light grid and reflection probes for its props. Moved anywhere else it needs
`--lighting flat` (the default) and an ambient chosen for the room.

`prefab_room.py` is a whole small map ("Prefab Room", `cp_pfr`: a flat lot, the prefab, four player starts, an
unseen wall round the lot). To put a prefab into another generator, call the same functions from it:

```python
import prefab_place as PP
pre = PP.load(placed_dir)
w = PP.WorldWriter(); PP.add_surfaces(w, placed_dir, pre)           # or feed the meshes to your own world writer
lines = PP.smodel_lines(pre)                                        # smodels.txt
lights, skipped = PP.light_lines(pre)                               # lights.txt
tris, tags, origin = PP.prefab_collision(placed_dir, pre, colmap)   # triangles in game units + surface tags
cells = PP.nav_cells(tris, rect, 32, min_z=floor_z)                 # walkable cells for mapgen.nav_graph
```

## How each part is carried

| Part | Route | Why this route |
|---|---|---|
| Surfaces | Triangle meshes written straight into `world.bin`, one render surface per shipped surface, in the shipped order, under the shipped material name | The compiler's world input is already an arbitrary triangle mesh per material (positions, texture and lightmap coordinates, packed normal and tangent, u16 indices); brushes exist only in the generator. No compiler change and no conversion to models was needed. A surface over 65,535 vertices or triangles is split |
| Vertex data | Position, normal, texture coordinates, **lightmap coordinates**, tangent, vertex colour and the raw fourth vertex float are copied from the shipped vertex (`surfaces.bin` and the new `surfaces_extra.bin` of a prefab). A prefab without the extra file gets tangents derived from its texture coordinates | The generated map is compiled against the shipped map as a template and keeps its lightmap images. A surface that keeps its shipped lightmap coordinates therefore shows its shipped baked light, with no bake |
| Props | `smodels.txt` lines, with `noshadow` and `cull=` taken from `prefab.json` | The compiler's own static model input. Every model of a room of the template map is already in the template zone: nothing to link |
| Lights | `lights.txt`: `omni` and `spot` with the shipped colour, radius, direction and outer cone | The compiler gives each line a light slot of the template |
| Collision | The shipped collision triangles inside the box, cut at the box, moved with the prefab, with their own surface tags (`collision.bin`), encoded by the SDK's Havok writer together with the lot | The shipped collision mesh already holds the clip geometry that stops a player at props; render triangles would give neither that nor the right surface types. Without the shipped file the render triangles are used (`--collision render`) |
| Navigation | 32-unit cells where the collision has a floor, room to stand and no wall across, kept to what is reachable from the player starts | Enough for the map to load and for the offline gate; the shipped navigation mesh is not read (see below) |
| Player starts | The prefab's own `default_player_start` entities (else four points at the centre) | |

## Measured on the spawn plaza of Spaceland

Runs of 10 and 11 Nov 2026, private local sessions (loopback, random password) from bench roots, one lab client build
for all three, 1280 by 720. Two builds of the same prefab: **moved** (placed 2,000 / 2,500 / 128 units away from where
it sits in Spaceland, flat ambient for the props, plain reflection probe) and **in place** (at its shipped
coordinates, no `lighting.txt`, so the template's own light grid and reflection probes stay). Evidence folders are
outside the repository (`prefab-room/runs/moved-placed`, `runs/inplace-placed`, `runs/source`, frames `iwz_*.bmp`).

### What went in

| | Prefab | In the built map |
|---|---|---|
| Props | 483, 101 models | 483 static models, every one with a template instance of its own model; nothing to link, no model refused |
| Surfaces | 437, 11,460 triangles, 17,824 vertices, 108 materials | 437 of 437 surfaces, 11,460 of 11,460 triangles (plus the lot: 438 surfaces); no material unknown to the template |
| Lights | 36 (all spots) | 36 light slots |
| Collision | 4,641 of the map's 283,561 shipped triangles touch the box | 4,233 triangles after the cut (826 were cut at the box), 35 surface tags, plus 64 for the lot and its wall |
| Navigation | not read | 3,350 cells, 3,316 reachable from the starts |
| Entities | 69 | 4 player starts; the other 65 are not placed |

### The proofs

| Proof | Result |
|---|---|
| Props in the running game (`paris_world_dump`, then `props-check`) | Both builds: 483 live props, 483 matched one to one within 0.01 (largest difference 0.00024), 101 of 101 models, orientation, scale and cull distance equal on all, 0 missing, 0 extra. The game reports `props=483 surfaces=438` |
| Floor | At three spots the player dropped from 4 units stands 0.05 to 0.19 above the floor height, 0.05 to 0.12 from where the same drop ends in Spaceland; 3 of 3 expectations pass |
| Wall | A walk east from the spawn stops after 309 units, 15 units before the wall the collision data puts at 325 |
| Large prop | A walk to the candy cart stops after 231 units, 49 from the cart's origin. Spaceland: 232 and 50. The two end points are 0.5 apart |
| What blocks in Spaceland and not here | Two of three walks: east, Spaceland stops the player after 97 units beside the employee door prop; north, after 7 units, where the turnstile props stand (which prop is inferred from the positions); in the generated map the player walks through both (309 and 156 units). See "not reproduced" |
| Frame rate (12 s per view, uncapped, no zombies) | moved map 293 / 262 / 295 / 278 frames a second at the four views, in-place map 267 / 270 / 286 / 282; Spaceland at the same views 124 / 153 / 183 / 186 |

Frames, generated map against Spaceland at the same four poses (the project's frame tool; brightness is the mean
luma, 0 to 1; "changed" is the share of pixels that differ; the hash distance compares the layout of the two
pictures, 0 = same, 64 = opposite):

| View | Spaceland brightness | Moved: brightness (ratio), changed, hash | In place: brightness (ratio), changed, hash |
|---|---|---|---|
| From the spawn, looking south (out of the box) | 0.148 | 0.162 (1.09), 79 %, 30 | 0.114 (0.77), 63 %, 20 |
| From the spawn, looking north (police cars) | 0.113 | 0.226 (2.00), 67 %, 20 | 0.091 (0.81), 45 %, 21 |
| West side, looking north-east | 0.160 | 0.231 (1.44), 66 %, 21 | 0.167 (1.04), 52 %, 12 |
| East side, looking north-west | 0.171 | 0.229 (1.34), 61 %, 18 | 0.168 (0.98), 42 %, 8 |

Two frames of an unchanged Spaceland view differ by 1.5 to 3 % of pixels (components `docs/WORLD-LIVE.md`), so every
pair above is far from "the same picture": that is expected, see the next section. These are measurements. Whether
the room looks right is for independent reviewers on the frame folders.

### Times and sizes

| Step | Measured |
|---|---|
| `extract` 0.6 s, `place` 0.4 s, `collision` 3 s, `prefab_room.py` 2 s, `iwz_emitcheck.py check` 1 s | the whole loop before a build is under 10 s; the gate found two real faults in the first emit (nav links through walls, a lot one can walk off) |
| Build, moved (branch compiler `codex/iwzmap-darkness`, 96ee83a) | 877 s: compile 111 (13 s of it the compile itself, the rest waiting for the reservation), assemble 304 (135,676 hard links), zone 462. Zone file 461,312,940 bytes |
| Build, in place (main-line compiler 07a5aa08 for the compile; zone step by the branch binary) | compile ok, same counts; the main-line binary's zone step fails on this zone (`animclass the_hoff_animclass`: "IW7 animation class/state machine missing"), so the zone was built by the branch binary: assemble 343, zone 796 (with waiting). Zone file 472,027,444 bytes |
| Session | about 5 minutes from client start to the spawn on the first load (the zone carries every asset of Spaceland); the plan itself 237 s; with the wait for the shared game slot the three sessions took 21, 35 and 7 minutes |

## What is not reproduced, and what each needs

| Not reproduced | What is seen or measured | What it needs |
|---|---|---|
| Sky and everything outside the box | Black sky; no car park, no park beyond the gate. The view south from the spawn has the largest hash distance | A sky for generated maps (the template's sky is not drawn); a vista prefab or backdrop models |
| Light on props when the prefab is moved | Props are lit by one flat ambient (`--ambient`, default 0.8 0.8 0.9): the two police cars read white where Spaceland shows them dark under coloured light; brightness of the view 2.0 times Spaceland's | The shipped light grid of the box carried with the prefab (worldkit walks over it, does not decode it), or a light-grid bake from the prefab's lights. Until then: choose the ambient per room from a measured frame |
| Light on props when the prefab stays in place | Much closer: with the template's light grid kept, view brightness is 0.77 to 1.04 of Spaceland's (moved: 1.09 to 2.0) and the hash distance falls to 8 to 21 (moved: 18 to 30). Still not equal: scripted and effect lights are absent | Nothing for the grid itself; it only holds while the room sits at its shipped coordinates |
| Reflection probes | Moved: one plain probe for the room. In place: the template's | Probe cubes copied with the prefab |
| Light on surfaces | Reproduced as baked: surfaces keep their shipped lightmap coordinates (431 of 437 are lightmapped). The bake was not run: it would replace the studio's own baked light by a bake from 36 spots, and the baker needs `numba` and `texconv`, which this session's Python does not have. A turned prefab keeps baked sun shadows that no longer match the sun | For a turned prefab or a new neighbourhood: the SDK baker (`bake/lmbake.py`) on the emitted source; not measured here |
| Shadows from the room's lights | The 36 lights are placed without shadow casting (the compiler's shadow option is marked not engine-verified); scripted lights (the police lights) are absent | Shadow caster lists verified in the game; light entities and their scripts |
| Material blend layers | 435 of the 437 surfaces carry per-vertex layer data in the shipped map; the compiler writes none | Layer data carried by the prefab and written by the compiler |
| Surface draw classes | Every surface is drawn as lit opaque, in the shipped order; the decal, translucent and emissive lists of a generated map are empty | Compiler support for the three lists |
| Collision of props that block by their own shape | The employee door and the turnstiles stop the player in Spaceland and not here (walks of 97 and 7 units became 309 and 156). The compiler writes 443 static-model collision entries, which its own notes say block bullets only. Props that Spaceland blocks with clip geometry in the world mesh (the candy cart) are reproduced exactly | Player-blocking static-model collision in the compiler, or model shapes added to the world mesh by the generator |
| Entities | 65 of 69: interactions (wall buys, doors), zombie spawners and volumes, idle spots, three script brush models, path nodes, one scripted light | The entity tools (`docs/MAPENTS.md`) and trigger volumes of the compiler; each interaction needs its script side |
| Navigation for zombies | Not the shipped navigation mesh: a 32-unit grid derived from collision (3,316 cells). No zombie was spawned in this map; nothing about zombies is proven | Reading the shipped navigation mesh, then a zombie plan |
| Effects, sounds, scripted things | Balloons, neon and fog effects, ambient sound, the HUD portraits (two HUD images draw as placeholders) are absent | Effect and sound placement tools of the generator; the map's HUD images |
| Visibility culling | The generated map draws everything (one cell). It is still faster than Spaceland here because it is one room | Package N5 |
| Zone size and build time | 461 MB and about 15 minutes for one room | Package N4 |

For an independent reviewer: compare `iwz_<view>.bmp` of `runs/moved-placed/run1` and `runs/inplace-placed/run1` with the same
file of `runs/source/run1` (four views each). Things to judge that no number here settles: whether surfaces and
props sit together without gaps or floating pieces, whether decals and glass draw correctly now that they are drawn
as opaque, whether the over-bright props of the moved build spoil the room, and how much the black sky costs.

## Files

| File | Role |
|---|---|
| `tools-source/worldkit/iw7_world.py` | `extract` now also writes `surfaces_extra.bin` (tangent, vertex colour, fourth vertex float) and per-surface `lightmapIndex`, `flags`, `layered`; `place` turns the tangents with the mesh |
| `tools-source/iwzmap/prefab_place.py` | prefab to compile sources (world writer, prop and light lines, collision, navigation cells), `props-check`, `pose`, `collision`, `info` |
| `tools-source/iwzmap/prefab_room.py` | the Prefab Room map generator |
| `tools-source/iwzmap/prefab_proof.py` | the pair of test plans and the comparison of the two sessions |
| `tools-source/iwzmap/build-prefab-room.ps1`, `new-work-from-stock.ps1`, `zt.ps1` | build under the shared reservation; no machine path (parameters; the scheduler defaults to `IW7_RESOURCE_SCHEDULER`, then `machine.ps1`) |
| `tools-source/iwzmap/tests/test_prefab_place.py` | tests on a synthetic prefab (no game data) |
