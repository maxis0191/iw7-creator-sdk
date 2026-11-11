# iwzmap: generated IW7 zombies maps (Station Zero)

Code-first authoring of an original IW7 zombies usermap. A Python generator
describes the rooms; the map compiler of our ZoneTool fork (`-iwzcompile`; the
branch that carries it is named in the x64-zt-extensions documents) compiles
them against the stock
`cp_zmb` world, used as a template for sun, sky, light grid and reflection
probes. Moved here from the server repository on 2026-11-06 (creator tooling
belongs to the SDK); the server keeps only its local test runner, fixtures and
records (`iw7-paris-server`: `ops/iwzmap/`, `tests/fixtures/iwzmap_*`,
`docs/IWZ-CUSTOM-MAP.md`).

## Pieces

| File | Role |
| --- | --- |
| `station_zero.py` | the map: rooms, doors, props, decor, spawners, zones, lighting -> `world.bin`, `colmap.hkx`, `navgraph.bin`, `ents.txt`, `triggers.txt`, `scriptables.txt`, `lighting.txt`, `layout.json` |
| `sz_interactions.py` | stock interactions: debris doors, generator power, perks, wall buys, Pack-a-Punch, scriptable relocations |
| `mapgen.py` | render mesh (GfxWorldVertex), bfx nav graph, entity text |
| `hkcm.py`, `hkcm_write.py`, `hkpack.py` | Havok hk_2014 compressed mesh collision (scale 1/32) |
| `assemble.py` | zone sources for buildzone (level script, content tables, csv) |
| `cp_iwz.gsc` | level script: agents, spawn volumes, interactions, door barrier |
| `art/` (package) | in-map 2D art: procedural grime/water/blood masks and decals, typeset clock/board/diagram/notices/posters, sign ageing, TGA+mipped DDS writer (see art/README.md) |
| `build_art.py`, `make_art.py` | map browser art zone `<map>_art.ff`: 2D list/vote images and the theater poster model, made from engine renders |
| `lightmap_read.py` | decodes the template lightmap atlas to pick per-room texels (LDR preview; superseded by `bake/lm_decode.py`) |
| `bake/lmbake.py` | lightmap baker: charts and atlas, ray traced direct light with soft shadows, cosine-gathered bounces, AO, dilation, BC6H/BC4/R8G8 encoding; rewrites the world.bin lightmap coordinates and lighting.txt (light grid) in a baked copy of the source |
| `bake/rt.py` | numba BVH ray tracer of the baker and the measurements |
| `bake/iw7image.py`, `bake/lm_decode.py` | iw7Image/DDS IO, texconv encode/decode; HDR decode of a lightmap set (A/B/D/S terms) |
| `bake/lm_measure.py` | engine frames against a bake: camera fit, visibility-tested texel projection, per-wall luma CV, rendered-vs-baked correlation, calibration patches |
| `tome_read.py` | reads an Umbra format-20 tome header |
| `tome_cull.py` | the generated map's culling data: per-prop cull distances by size, a check of the tome against every door sightline before the zone step, and the game's depth of door captures ([CULLING](../../docs/CULLING.md)) |
| `iwz_emitcheck.py` | offline gate on an emit: collision, nav, links, stairs, spawners, routes, build-to-build diff |
| `iwz_zonecheck.py` | offline gate between "emitted" and "packed": everything built is listed, present in the source tree, and the compiled file is newer than its sources |
| `iwz_probe_forensics.py` | recorded probe logs to per-zombie classes, verdicts, trust flags, flaky cases, hotspots |
| `volume_check.py` (+ `test_volume_check.py`) | offline check of a compiled map's trigger volumes: every info_volume / trigger_* has an entity Havok shape the engine can point-test (ispointinvolume = Havok point query, units / 32, no shape = never inside), of its trigger model's size; spawners and plan nav cells inside their zone volume (`--plan`, `--require-spawners`) |
| `pipeline.ps1`, `build-map-wait.ps1`, `zt.ps1`, `build-zt.ps1`, `new-work.ps1` | build orchestration under the shared resource lease |
| `native/error_journal.c` | diagnostic DLL for the local runner: Com_Error journal, fault dump, timed console commands, LuaFile dump, dvar force, RenderDoc trigger |

Older experiments kept for history: `cp_iwz_v1.gsc`, `m2a_room.py`,
`hktree_check5.py`, `simd_check.py`, `native/xref.py`, `native/disas.py`.

## Every file of this folder

The table above explains the main pieces. The three tables below list every file that lies directly in
`tools-source/iwzmap`, with the role its own header gives. Sub-folders follow.

### Generic tools (any generated map)

| File | Role |
| --- | --- |
| `scenegen.py`, `cp_iwz3.gsc`, `scenes/` | a whole zombies map from a scene description (zones, heights, doors, flights, spawners, interactions as data): checks, emit, flight / route / pool readers (`docs/SCENEGEN.md`); `scenes/station_zero.json` is the bible's 19 zones |
| `mapgen.py` | iwzcompile sources from a box-based map description: render mesh, nav graph, entity text |
| `brushkit.py` | brush library: textured quads, boxes, wedges, banded walls with openings, stairs |
| `hkpack.py`, `hkcm.py`, `hkcm_write.py` | Havok 2014 packfile reader; decoder and encoder of the compressed mesh collision |
| `assemble.py` | assembles `zonetool/<map>/` (hard links) and `zone_source/<map>.csv` |
| `kit_import.py`, `kit_proof.py` | stock models of other zones into a usermap zone; drawn / textured / lit proof on capture frames |
| `char_pack.py`, `build-charpack.ps1` | stock player characters of other zones (body, head, arms) as the source of a mod zone, with their table; one command dumps, packs and builds (see "Character pack") |
| `build_art.py`, `make_art.py` | map browser art zone and its images from engine renders |
| `iwz_emitcheck.py`, `iwz_zonecheck.py`, `iwz_probe_forensics.py` | offline gates on an emit and on a zone tree; forensics of recorded route probes (tests in `tests/`) |
| `volume_check.py`, `test_volume_check.py` | offline check of a compiled map's trigger and spawn volumes, and its unit tests |
| `lightmap_read.py` | decodes the template lightmap atlas to pick texels (its output feeds `sz2_lmpick.py`; the HDR decode is `bake/lm_decode.py`) |
| `tome_read.py` | reads an Umbra format-20 tome header |
| `tome_cull.py` | the generated map's culling data: per-prop cull distances by size, a check of the tome against every door sightline before the zone step, and the game's depth of door captures ([CULLING](../../docs/CULLING.md)) |
| `machine.ps1` | resolves the machine locations of the build and run scripts (see "Machine locations") |
| `zt.ps1` | runs ZoneTool in a work folder under the shared resource lease |
| `build-zt.ps1` | builds the ZoneTool fork under the lease |
| `new-work.ps1` | makes a ZoneTool work folder from a game folder: copies the executable set, hard-links the zone files |
| `pipeline.ps1`, `build-map-wait.ps1` | build chain of a generated source (compile, pack, optional probe run); the second waits while another owner holds the lease |

### Station Zero level (v1 and v2)

| File | Role |
| --- | --- |
| `station_zero.py`, `sz_interactions.py`, `cp_iwz.gsc` | v1: the compact three-zone map, its stock interactions and its level script |
| `station_zero2.py`, `cp_iwz2.gsc` | v2: the nine-zone metro station from textured brushes and data tables; its level script template |
| `sz2_materials.py`, `sz2_assemble.py` | v2 material table; custom world materials and their images added to the zone |
| `sz2_art_hooks.py` | art drop-ins: an image present under its request name becomes a map material, a missing one changes nothing |
| `sz2_submodels.py` | picks the door blocker sub-model from a compile log made with `IWZ_KEEP_SUBMODELS=1`; writes `sz2_submodels.json` |
| `sz2_kitzone.py` | adds kit models of other CP zones to an assembled map zone |
| `sz2_tables.py` | Markdown tables of a generated layout (zones, doors, interactions, spawners, quest spots, lights) |
| `build-sz2.ps1`, `run-sz2.ps1` | v2 build (own ZoneTool work folder, leased) and private local run (views, walk, gameplay modes) |
| `sz2_plan.py` | offline: plan image and nav / data consistency (exit 1 on failure) |
| `sz2_navconn.py` | offline: nav connectivity of the generated source (stairs, decks) |
| `sz2_artlint.py` | offline: static art lint of a generated source (failed materials, track bed, fake vehicles, ...) |
| `sz2_density.py` | offline: set-dressing density per zone and longest bare wall run |
| `sz2_flatness.py` | offline: largest undetailed wall, floor and ceiling area per zone |
| `sz2_seams.py` | offline: gaps at ceiling edges that show the void |
| `track_clearance.py` | offline: what stands inside the envelope a subway car runs through |
| `sz2_frames.py` | capture run to contact sheets, luma per frame and zone, gallery sampling |
| `sz2_lmpick.py` | per-zone lightmap texels from engine measurements; writes `sz2_lm_table.json` |
| `sz2_contrast.py` | frames: contrast between floor, wall and ceiling families per zone |
| `sz2_mood.py`, `sz2_mood_predict.py` | frames: median luma and lighting spread per zone; prediction of those numbers for a new bake from an old one |
| `sz2_fxcheck.py` | frames: ambient effects render and decal quads blend |
| `sz2_propcheck.py` | frames: props that render as flat black or untextured slabs |
| `sz2_signcheck.py` | frames: custom sign and poster images are not mirrored or flipped |
| `sz2_probecheck.py` | compile log and frames: reflection probe rooms and their colour |
| `sz2_fixproof.py` | before / after crop pairs of a fix at the same camera pose |
| `train_proof.py`, `train_perf.py` | train kit: drawn / textured / lit from A/B frames; frame time with the kit shown and hidden |

### Data files and who reads them

| File | Written by | Read by |
| --- | --- | --- |
| `material_dims.json` | by hand (image name and pixel size per material key) | `sz2_materials.py`, `sz2_artlint.py` |
| `mood_dark_ok.json` | by hand (views that are meant to hold a large black area) | `sz2_mood.py --gate` |
| `probe_colours.json` | from the views of one build (`sz2_probecheck.py`); the source is named in the file | `station_zero2.py` |
| `sz2_submodels.json` | `sz2_submodels.py` | `station_zero2.py` |
| `sz2_lm_table.json` | `sz2_lmpick.py` | `station_zero2.py` |
| `characters_5_8.json` | by hand (the four guest characters: key, source zone, body, head, arms; the table name) | `char_pack.py`, `build-charpack.ps1` |

### Sub-folders

| Folder | Holds |
| --- | --- |
| `art/` | deterministic 2D art package (see `art/README.md`) |
| `audio/` | sound bank, emitters, music, capture and measurement (see `audio/README.md`) |
| `bake/` | lightmap and light grid baker and its measurements |
| `catalog/` | model catalogue and preview booth (see `catalog/README.md`) |
| `content/cp_iwz/` | one content table of the map (`cp_iwz_playercash_images.csv`) |
| `darkness/` | dark-until-power chain (see `darkness/README.md`); `darkness/runs/` (launch arguments of dated proof runs) and `darkness/integration/` (a patch for a script outside the repository) are records |
| `fixtures/` | GSC fixtures for private local runs: `sz2_local.gsc` (views, walk, probes), `sz2_gameplay.gsc`, `sz2_hitch.gsc`, `train_kit.gsc` |
| `fx/` | effect placement, import, variants and proof; `fx/agent/` holds one agent's run scripts and probes (see its `README.txt`) |
| `native/` | diagnostic DLL sources for an owned private test client (`error_journal.c`, `iw7_fxperf.c`, `build.cmd`) |
| `tests/` | unit tests of the three `iwz_*` gates |

`hkcm_write.py` cites `hktree_check.py` in its header; the file is `hktree_check5.py`.

## Machine locations

No script of this folder holds a path of one machine. A location comes from a parameter of the script, or from
`machine.ps1`, which reads these variables and otherwise uses the default beside them:

| Variable | Default | What it is |
| --- | --- | --- |
| `IWZ_RUNTIME` | `<Documents>\IW7-Runtime` | work folders, dumps, runs, the Python environments of the stage |
| `IWZ_PRODUCTS` | `<Documents>\IW7-Products` | checkouts of the products |
| `IWZ_SERVER` | `<Documents>\IW7-Paris-Server` | server checkout that holds the local runner (`ops\iwzmap`) |
| `IWZ_COMPONENTS` | `<IWZ_PRODUCTS>\iw7-mod-components` | resource scheduler (`ops\Resource-Scheduler.Core.ps1`) |
| `IWZ_ZONETOOL_EXE` | `<IWZ_PRODUCTS>\worktrees\<worktree the script names>\build\bin\x64\Release\zonetool.exe` | the ZoneTool build to use |
| `IWZ_ZONETOOL_SOURCE` | `<IWZ_PRODUCTS>\worktrees\x64-zt-iwz-map` | ZoneTool source built by `build-zt.ps1` |
| `IWZ_TEMPLATE_DUMP` | `<IWZ_RUNTIME>\iwz-map-ref-a\dump` | stock dumps (`cp_zmb`, `techsets_*`) |
| `IWZ_GAME_ROOT` | none | game folder for `run-sz2.ps1`, `new-work.ps1`, `pipeline.ps1`, `catalog\Run-Preview.ps1`, `fx\agent\run-fx.ps1`: a bench root, never the owner's game folder |

`<Documents>` is the Documents folder of the account. The Python tools read `IWZ_RUNTIME` for their
fall-backs (their default is `~/Documents/IW7-Runtime`, which differs from the PowerShell default only when the
Documents folder is redirected; set `IWZ_RUNTIME` in that case), next to the variables they already had: `IWZ_TEXCONV`, `GRAYWOLF_EXE`, `IWZ_SMODEL_STOCK_CSV`,
`IWZ_ART_DIR`, and `IWZ_STOCK_DUMP_CP` for the optional case of `test_volume_check.py`.
`catalog\Run-Preview.ps1 -SourcePackage` is mandatory (prepared server inputs).

Three things changed for a caller on the machine the scripts were written on (2026-11-10): the game folder is no
longer assumed (set `IWZ_GAME_ROOT` or pass the parameter); the server runner defaults to the main server checkout
instead of one session's worktree (set `IWZ_SERVER` to choose another); the scripts under `fx\agent` and
`darkness\build-g-dark.ps1` use the tools of the checkout they are in instead of older worktrees. Every other
default resolves to the same path as before.

The records in `darkness/integration/` keep the paths of the runs they describe; they are not tools.

This landed without a map build: every script parses and every default was compared with the path it replaced.
The first agent that builds or runs a map after this change reports the result.

## Build

```powershell
$env:IWZ_DOUBLE_SIDED='1'; $env:IWZ_VOLUME_MODEL='46'
python -I station_zero.py <stock cp_zmb dump> out\sz_src
.\build-map-wait.ps1 -Zt -UmOut out\um_cp_iwz_rc     # IWZ_GEN_TOME + IWZ_KEEP_ENTSHAPES
python -I make_art.py <hero frame.bmp> <second frame.bmp> out\art cp_iwz
python -I build_art.py <zonetool work> cp_iwz <work>\zonetool\cp_iwz out\art <work>\dump\cp_frontend
```

Baked lightmap (Python 3.12 with numpy, numba, scipy, pillow; DirectXTex texconv, path in `IWZ_TEXCONV`):

```powershell
python -I bake\lmbake.py out\sz_src out\sz_src\lights.json out\sz_baked   # station_zero.py writes lights.json
python -I bake\layout_lights.py <src> <src>\lights.json   # or: lights.json from a level generator's layout.json lights
.\build-map-wait.ps1 -Src out\sz_baked -UmOut out\um_cp_iwz_baked             # the compiler ships lightmap\*.dds
python -I bake\lm_measure.py out\sz_baked "<views>" <run dir> measure.json --frames-flat <flat run> --viz <dir> `
       --eye 58.45 --fov 133.14   # frames of a local run vs the bake (camera of the base client, 1280x720)
```

The compiler (`iwzmap_lightmap.cpp`, x64-zt branch `codex/iwzmap-lightmaps`) replaces the template lightmap
images (`*lightmap0_primary/secondary/secondunorm`: same names, own size) when the source has
`lightmap\secondary.dds`. World shader: `E = A + ssao * B * saturate(dot(N, D))`, diffuse = albedo * E, with
A = secondary top half, B = bottom half, D = secondunorm (rotated octahedral, tangent frame) and S = primary
(baked sun visibility; the sun itself is shaded at runtime). Engine evidence (iwz-stage2/lightmaps): calibration
patches give E = A + B * Dz (B-only patches render within 4..11 % of the equal-E A-only patches); the baked/flat luma
ratio follows the baked E (r 0.87..0.985 per view); forcing S = 0/0.5/1 indoors changes nothing measurable.

Compiler switches (environment): `IWZ_GEN_TOME` (generated conservative Umbra
tome; required for complete rooms), `IWZ_KEEP_ENTSHAPES` (template entity
shapes for the reused trigger model), `IWZ_LOG_PROBES`, `IWZ_DUMP_TOME`.
Older routes (`IWZ_KEEP_UMBRA`, `IWZ_SLOT_SURFACES`) are superseded.

### Build time: where it goes and the fast rebuild (TF4)

Every ZoneTool run of `zt.ps1` prints how long it waited for the build reservation and writes
`zt-<time>.timeline.tsv` beside its log (each line with the second it appeared); `python -I zt_timeline.py report
<file>` lists the longest gaps and the time per message source. `build-sz2.ps1` and `build-prefab-room.ps1` write
`<um>.build.json` with compile, assemble and zone seconds. `python -I proc_sample.py <pid>` samples any of your own
running programs (stacks named from the .pdb with `--symbols`).

Measured 11 Nov 2026 (ZoneTool main 26382dd unless said):

| Step | Before | Now | What changed |
| --- | --- | --- | --- |
| Light bake (`bake\lmbake.py`, 256 rays, 3 bounces, Station Zero g27dw) | 225 s (recorded) | 250 s, measured with `bake\New-BakeEnv.ps1`'s environment | only when the render world changes; `-ReuseBake` keeps it otherwise |
| Zone step, prefab room (ZoneTool itself) | 518 s | 49 s | ZoneTool's log went through PowerShell's `Start-Process` redirection; every unbuffered line waited on that pipe (the sampler: 90 % of the main thread in `NtWriteFile`). `zt.ps1` now redirects to the file through cmd.exe. Indexed asset and script string lookups (x64-zt `claude/zone-build-speed`) took it from 518 to 337 s before that |
| Zone step, Station Zero (core: world, collision, navigation, entities, baked light, custom materials; 476 MB) | 482 s (g27dw with kit, effects, audio) | 41 to 63 s | same |
| Assemble (135,676 stock hard links, prefab room) | 166 s | seconds with `-Incremental` | `assemble.py --incremental` keeps the stock links of the previous assembly made from the same dumps and links only the generated world again; `build-sz2.ps1 -Incremental` also keeps what the modules (kit, effects, audio, darkness) added when they ran with the same arguments |

**A one-room change, measured end to end** (11 Nov 2026, Station Zero core from the compiler-landing input plus the
audio module, one prop of one room moved 32 units in `smodels.txt`, x64-zt main with the indexed lookups,
`build-sz2.ps1 -KeepSubmodels -AudioSdk ...`; seconds of work, without the waits for the build reservation):

| Build | Compile | Assemble (+ modules) | Zone | Total | Load headless (command to verdict) |
| --- | --- | --- | --- | --- | --- |
| full, fresh work folder | 7 s | 232 to 297 s | 41 to 63 s | about 5 minutes | 59 s, PASS 13/13 |
| incremental (`-Incremental` after a build of the unchanged source) | 7 s | 1 s | 44 s | **52 s** | 57 s, the map in play (13/13 steps) |

One-room change to a loaded map: **about 110 s** (52 s rebuild + 57 s headless load), against about 20 minutes before
(bake reused in both). `ff_compare.py` on the full and the incremental zone: same content (64,724 differing bytes,
all pointer residue, 0 content bytes); the sound bank files are byte-identical. The same tool between the unchanged
and the changed source finds exactly the 2 bytes of the moved prop's coordinate. A run without the audio module
gave the same result (64 s, same content) but its level script needs the module to start.
The waits were the real cost on 11 Nov: the full build waited 2,584 s and the base build about 1,500 s for the build
reservation behind other agents' sessions (quality ledger: the scheduler has no fairness rule for builds).
Not covered: a change of the render world needs the bake again (250 s for the whole map; no per-room bake yet); the
kit, effects and darkness modules were not in the timed runs.

`ff_compare.py <a.ff> <b.ff>` says whether two built zones hold the same map: it decompresses both and separates
pointer residue (leftover addresses of ZoneTool's own process in fields the game rebuilds at load; they change with
the heap of the run) from content. Two builds of the same source by the same binary differed in 58,613 bytes, all
residue; the zone built with the direct log and with the indexed lookups has the same content as the main-line one
(prefab room and Station Zero g27dw). Needs `pip install lz4`.

Light baker environment: `pwsh bake\New-BakeEnv.ps1` makes `<IWZ_RUNTIME>\iwzmap-bake-venv` (numba, numpy, scipy,
pillow at the versions of `bake\requirements.txt`, 22 s) and prints its python; `machine.ps1 BakePython` names it;
texconv is `IWZ_TEXCONV` or `<Documents>\IW7-Tools\texconv-may2026\texconv.exe`.

## Check before you build (seconds, no game)

The generator output (`colmap.hkx`, `navgraph.bin`, `layout.json`) already
contains what a zombie will walk on. Read it before paying for a zone build
and a game launch. Pure Python, no dependency, about two seconds per emit.

```powershell
python -I -B iwz_emitcheck.py check  out\sz_src                 # gate: exit 1 on any error
python -I -B iwz_emitcheck.py diff   out\sz_prev out\sz_src     # what changed, what to re-test
python -I -B iwz_emitcheck.py stairs out\sz_src                 # step by step: floor, nav, sides
python -I -B iwz_emitcheck.py at     out\sz_src 1936,1694,-355  # a logged position, explained
python -I -B iwz_emitcheck.py route  out\sz_src 2250,2000,-319 -- 1906,1735,-320
```

`check` reports nav cells with no floor, floating or buried cells, links that
cross collision, disconnected islands, spawners and interactions off the nav,
unreachable zones, stairs whose nav or floor has a gap, and walk routes that
leave the nav. `diff` lists the stairs and zones whose collision or nav really
changed: only those need a new game probe, and a build whose diff does not
touch the place under investigation cannot change its result. `at` says
whether a position from a log is on a floor, in the air, inside solid or over
nothing, with the nav offset. `route` gives the nav distance and a walking
time, which is the timeout a probe case needs.

After a probe has run, read every recorded run at once instead of one log at a
time:

```powershell
python -I -B iwz_probe_forensics.py <runs\stairprobe_*> --emit out\sz_src --json forensics.json
```

Each zombie gets a class (`reached`, `sub_surface`, `fell_out_of_world`,
`stuck`, `crossed_level`, `went_away`, `never_moved`, ...), each case a verdict
(`pass`, `geometry_suspect`, `partial`, `probe_artifact`, `inconclusive`) and
trust flags (`ended_early`, `ended_while_walking`,
`changed_floor_not_counted`). Cases that gave different outcomes across runs
are listed as flaky, and failures are grouped into hotspots with the place
where the body left the built surface. A `probe_artifact` verdict means the
probe proved nothing: fix the probe, do not rebuild the map.

Between the emit and the compiled file there is one more stretch nothing used
to read: the source list and the source tree ZoneTool packs from. A file that
was emitted but never listed is silently absent from the map; a compiled file
older than its sources is yesterday's map under today's name.

```powershell
python -I -B iwz_zonecheck.py <ztwork> --zone cp_iwz --emit out\sz_src --stock <dumped stock zones> --table
python -I -B iwz_zonecheck.py <ztwork> --zone cp_iwz --strict   # release gate: exit 2 while a warning stands
```

It reports rows of the source list with no file in the tree, files in the tree
no row lists, emitted files that differ from the copy in the tree, a collision file that
cannot be read, references
to assets no listed zone or stock dump holds, and a compiled file older than
what it was built from. It writes the same report shape
(`iw7.content-audit/1`) as the weapon audits of the asset tools, so one reader
handles all of them. It never judges how the map looks, and a name that is
absent from a stock dump is a note to check, never proof that it is missing.

All three tools read; none builds, launches or writes into an emit. Tests:
`python -B -m unittest discover -s tools-source/iwzmap/tests`.

### Entities and template pools (iwz_ledger.py, under 1 s)

```powershell
python -I iwz_ledger.py check out\sz_src --template <stock dumps>\cp_zmb [--live <gamelab run>\client.stdout.log]
python -I iwz_ledger.py compiled <um>.compile.log      # what the compiler really did with the pools
```

The engine has 2,048 entity slots; the project ceiling is 1,800. `check` counts the entity list (every `ents.txt`
entry that is not a struct) and adds the runtime worst cases each package writes before it builds, in
`<src>\entity_budget.json` (`{"rows": [{"package": "E1", "entities": 120, "why": "..."}]}`); it refuses (exit 1)
above the ceiling. The template pools the compiler reuses are counted against what the stock template has:
generated trigger shapes (`triggers.txt` rows against the template trigger models the source does not name itself,
an upper bound), lights (static and named `lights.txt` rows against 1,010 static and 25 scriptable slots of cp_zmb),
probe rooms (160 cubes), static models (65,535); door blockers and scriptables are reported. A source over a pool
is refused before the build instead of failing in the compiler. `--live` reads the `ents` census of a gamelab run
(the plan step `ents` with no key counts every entity of the running map) and prints how many entities scripts,
players and the engine add.

Measured 11 Nov 2026: Station Zero g27dw, 305 entities in its list (257 script models, 24 brush models, 13 use
triggers, 9 volumes, 2 others; 150 structs not counted), equal to a count of the file by hand; trigger shapes 9 of
136, lights 5 of 1,010, probes 9 of 160; the compiler log agrees (9 shaped triggers, 5 light slots, 9 probe rooms).
The prefab room: 2 entities in its list, 240 live in the running map (the stock gameplay scripts the map carries,
the bot and the engine add 238).

## Players

A zombies usermap also needs the iw7-mod `Usermaps` script fix (fork branch
`fix/usermaps-cp-map-stats`): without it one installed `cp_` usermap breaks the
whole CHOOSE FILM list.

## Station Zero v2 (stage 2 level design)

`station_zero2.py` builds the nine-zone metro station of the stage 2 level design from textured brushes
(`brushkit.py`: world-aligned quads with per-material texture world size, boxes, banded walls with door
openings, reveals and frames, straight stairs with render steps and a smooth collision ramp). Data tables
(`ZONES`, `OPENINGS`, `SPAWNERS`, `PERKS`, `WALL_BUYS`, `WHEELS`, `QUEST`, `PROPS`, `LIGHTS`, `SIGNS`, `VIEWS`,
`WALK`) are kept separate so the static model, light, audio and gameplay tools can plug in. Materials and their
UV scales are in `sz2_materials.py`; custom-image signs/posters and tinted lamps are cloned stock world materials
written by `sz2_assemble.py`. The level script is `cp_iwz2.gsc` (generated door / zone link tables).

```powershell
$env:IWZ_DOUBLE_SIDED='1'                       # optional: IWZ_GALLERY=1 adds the material / texel gallery room
python -I station_zero2.py <stock cp_zmb dump> <src>
python -I sz2_plan.py <src>                     # offline plan image + nav/data checks (exit 1 on failure)
.\build-sz2.ps1 -Src <src> -UmOut <usermap dir> # own zonetool work dir, leased
.\run-sz2.ps1 -Tag <run> -UsermapDir <dir> -Mode views|walk|gameplay -Fixture <src>\iwzmap_sz2_local.gsc
python -I sz2_frames.py <run dir> <src> <analysis dir>   # contact sheets, luma, gallery sampling
python -I sz2_lmpick.py <analysis>\gallery.json sz2_lm_table.json   # measured per-zone texels
```

## Stock models from other zones (kit import)

The template carries cp_zmb only. `kit_import.py` adds stock xmodels of other zones (cp_disco, cp_final, ...) to the
usermap zone: geometry, materials, image headers (pixels stream from the base `imagefile*.pak`), physics assets and
the techsets the template's runtime techset zones lack. Needs ZoneTool x64-zt `codex/iwzmap-kit-import` or later
(`-dumpzonetypes` writes a map zone's materials, whose definitions live in `techsets_<zone>`).

```powershell
# once per source zone, in the zonetool work dir (zt.ps1 lease)
zonetool -dumpzonetypes cp_disco xmodel,xmodelsurfs,material,image,physicsasset,physicsfxshape
zonetool -dumpzone techsets_cp_disco
# build: models from a list or kit_final.json rows; '<zone>=<model dump>;<techsets dump>'
.\build-sz2.ps1 -Src <src> -UmOut <dir> -KitModels 'cp_disco_subway_train_bsp2xmodel,clk_defend_generator_solo' `
  -KitDumps 'cp_disco=<W>\dump\cp_disco;<W>\dump\techsets_cp_disco','cp_final=<W>\dump\cp_final;<W>\dump\techsets_cp_final'
python -I kit_proof.py <kit run> <baseline run> <src> kit_final.json <out>   # drawn / textured / lit per model
```

Rules: a material, image, techset or shader already named by the zone csv or defined by a runtime techset zone is
referenced, not copied; other techsets are embedded from the techsets dump (`.techset`, `.technique`,
`.vertexdecl`, shader `.cso`). Do not `require` extra map techset zones: two of them next to the template's nine hung
ZoneTool. Scriptable movers (the subway train's) are dropped from a patched `.xmb` copy (`--keep-scriptable` keeps
them and then needs the scriptable dump and its dependencies).

### Kit and authored models as static models (TF10)

A kit model (another shipped map) or an authored model (a port folder of `x64-zt-extensions` asset-bridge) can be
placed in `smodels.txt` like a stock model: compiled into the map as a static model, lit by the light grid, not an
entity. It needs the map compiler of x64-zt `main` after the TF10 change (a model with no light grid lit instance in
the template map gets a neutral, fitted draw instance; before, it copied another model's, whose material index read
past a smaller model's material list and crashed the client at `iw7_ship+0xDCE6E7`). The compiler reads the
model's `.xmb` from `<source>\xmodel`; `kit_import.py --stage-xmodels <source>` links it there, and the normal kit
import then puts the model itself into the zone. `build-prefab-room.ps1` does both:

```powershell
.\build-prefab-room.ps1 -Src <src with smodels.txt rows for the models> -UmOut <dir> -Work <work> -ZoneToolExe <zonetool> `
  -TemplateDump <dumps> -KitModels 'cp_disco_worn_subway_bench,train:iwz_fire_hose_cabinet' `
  -KitDumps 'cp_disco=<W>\dump\cp_disco;<W>\dump\techsets_cp_disco','train=<port folder>'
```

The proof plan is the server repository's `tests/scenarios/gamelab/tf10-static-models.json` (frames with depth for
`iw7_see.py visible`, bullet traces, the entity census).

## Character pack: stock player characters in a mod zone

The guest player characters of IW7 Zombies each live in one map zone (the DJ in cp_zmb, Kevin in cp_rave, Pam in
cp_disco, Elvira in cp_town). `build-charpack.ps1` packs their body, head and arms models into the source of a mod
zone, which loads on every map, so each character can be a player character on all five maps. One command:

```powershell
# dumps what the work folder lacks (each source zone's models and its techsets zone, through zt.ps1), writes the pack,
# and with -Build compiles it alone as zone "mod" (a test mod: copy <Out>\mod.ff to mods\<name>\mod.ff)
.\build-charpack.ps1 -Work <ZoneTool work folder from new-work-from-stock.ps1> -Out <new folder> -Build `
  [-Characters characters_5_8.json] [-Scheduler <prepared inputs>\ops\Resource-Scheduler.Core.ps1] [-WaitForSlotSeconds 3600]
```

- `characters_5_8.json`: the characters (`key`, source `zone`, `body`, `head` (empty for a full body), `arms`) and
  the name of the table the pack carries (`paris/characters_5_8.csv`, rows `key,body,head,arms`).
- `char_pack.py <out> --dump <zone>=<dump>;<techsets dump> ...`: the pack itself. It calls `kit_import.py` with
  `--share-runtime-materials`: a material that a shared techset zone (`techsets_common*`, `techsets_global*`,
  `*_cp`, `*_mp`, `*_core_mp`) already defines becomes a `material,,<name>` reference row; the others are copied with
  their image headers (pixels stream from the base `imagefile*.pak`) and their techsets when no shared zone has them.
  The pack's csv starts with `require` rows for those shared techset zones. Report: `<out>\charpack-report.json`.
- `kit_import.py` fills a zone csv with no world rows (no `com_map,` row) by appending: that is how a mod zone takes it.
- The Paris mod takes the pack with `Build-ParisMod.ps1 -CharacterPack <Out>` (server repository,
  `docs/CHARACTER-PACK.md` there, with the measured size, memory and per-map proof).

## Ambient FX (fx/)

Stock IW7 effects render in a usermap through the ordinary script route (`loadfx` in `main()`, then
`spawnfx` + `triggerfx( ent, -4 )` for looping ambience, `playfx` for bursts). Every cp_zmb effect is already in the FF
(assemble.py copies the stock zone rows). What matters: the effect must be in the level effect list
(`netconststrings/ncs_efx_level.json`, IW7 registers effects through it), placed with the stock createfx angles, and
be a top-level effect (child effects such as `vfx_zmb_drips`, `vfx_zb_trash_a_ch` are spawned by their parents).
Particle-cloud effects (techset `particle_cloud_*`, e.g. `vfx_zmb_dust_motes_md`) do not draw in a generated map:
use sprite effects (the cp_disco `vfx_amb_motes` import) for motes.

```powershell
# fx.txt: <name> <alias|vfx path> <x> <y> <z> [angles=p,y,r] [mode=loop|interval:a-b|retrigger:s|flicker:a-b|oneshot]
#         [delay=s] [view=x,y,z,yaw,pitch] [region=r] [region_dz=dz] [zone=z]       (aliases: fx/fx_catalog.json)
python -I fx\fx_place.py <fx.txt> <src> --list-imports               # foreign effects the file needs
python -I fx\fx_place.py <fx.txt> <src> --ncs <ncs_efx_level.json> [--ncs <imported list>] `
  --fixture-out <src>\fxproof.gsc --manifest-out <src>\fx_manifest.json   # patches <src>\cp_iwz.gsc (iwz_fx module)
# foreign effects (cp_disco steam, drips, motes, beams...): dump once, then build with the import
zonetool -dumpzonetypes cp_disco vfx,particlesimanimation,netconststrings
.\build-sz2.ps1 ... -FxImport 'cp_disco:vfx/iw7/levels/cp_disco/amb/vfx_grate_steam_01,...' `
  -FxDumps 'cp_disco=<vfx dump>;<kit dump>;<techsets_cp_disco dump>'
# proof: private run with the generated fixture (+set paris_iwz_mode fxproof +set paris_iwz_fxproof 1
#        +set paris_iwz_fxonly -2 +set paris_iwz_fxphase 0) and the fxperf DLL (IW7_FXPERF=<file>), then
python -I fx\fx_proof.py <run> <src>\fx_manifest.json <out> --perf <fxperf file>
```

fx_proof.py: per effect, same camera, frames with the effect held off (off0, off1) and running (on0..on4 over 4 s);
the luma is box-blurred 7x7 first (IW7 film grain changes ~10% of single pixels between any two frames); PASS when
the changed fraction inside the projected effect region is >= 0.4%, >= 4x the off/off noise and >= 3x the change
outside the region; ANIMATED when consecutive on frames also change in the region. Frame time: the fxperf DLL hooks
DXGI Present and buckets present-to-present intervals by the dvar `paris_iwz_fxphase` (2k+1 effect k off, 2k+2 on,
200/201 every effect off/on at the zone views). In a match the module starts every effect once and never polls.

Power stages (`stage=` in fx.txt): `always`, `dark` (until the stock `power_on` flag), `lit` (from power on),
`poweron` (start-up burst for `for=<s>` seconds). With `level.iwz_light_banks_external` (darkness lighting script) the
dark/lit switch follows each zone's light bank (`iwz_light_bank_on`, <zone>; `iwz_power_lights_done`). Proof runs
ignore stages (every effect is tested on its own) and hold the flickering lamps (`paris_iwz_flickertest 1`).
Engine findings (runs in iwz-stage2\fx): sprite effects render; GPU particle clouds (`particle_cloud_*` techsets,
`vfx_zmb_dust_motes_md`) and `vfx_knee_high_fog_dark` (placeholder material `gfx_test01`) never draw;
`vfx_zb_thu_sparks` and `vfx_zmb_light_strobe_01` emit light (the surroundings brighten); thin drips
(`vfx_water_drips_line`, `vfx_zmb_drips_parent`) stay below the measurement threshold at 200+ units; the effect list
entry is not required for an imported effect (`vfx_light_mist` rendered without it). fx_place refuses effect origins
more than 96 units from any walkable plan cell (inside a wall or the void).

Dark maps (darkness builds: pitch dark before power, flashlight = particle spot light). Lit particle materials
(`eq_effect_*_blend_*`) take the baked light grid AND dynamic lights: they read inside the flashlight cone and next to
baked emergency lamps, nowhere else (fx\NOTES.md probe9 / proof-dfx1-a). `fx_variant.py` makes self-lit variants of
lit stock effects (unlit counterpart techset with the donor's state / constant-buffer files, colour tint) for the dark
stage; `station_zero_fx_dark.txt` pairs them (`stage=dark`) with the lit originals (`stage=lit`). Prove dark FX with the
flashlight carrier in "follow" mode (`+set paris_iwz_fl_mode follow`): the "link" carrier does not follow view pitch.
`vfx_lit.py` (fx/agent) lists the lighting class of every material of an effect.
