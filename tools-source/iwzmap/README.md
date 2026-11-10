# iwzmap: generated IW7 zombies maps (Station Zero)

Code-first authoring of an original IW7 zombies usermap. A Python generator
describes the rooms; our ZoneTool fork (`maxis0191/x64-zt`, branch
`codex/iw7-map-compiler`, `-iwzcompile`) compiles them against the stock
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
| `iwz_emitcheck.py` | offline gate on an emit: collision, nav, links, stairs, spawners, routes, build-to-build diff |
| `iwz_zonecheck.py` | offline gate between "emitted" and "packed": everything built is listed, present in the source tree, and the compiled file is newer than its sources |
| `iwz_probe_forensics.py` | recorded probe logs to per-zombie classes, verdicts, trust flags, flaky cases, hotspots |
| `volume_check.py` (+ `test_volume_check.py`) | offline check of a compiled map's trigger volumes: every info_volume / trigger_* has an entity Havok shape the engine can point-test (ispointinvolume = Havok point query, units / 32, no shape = never inside), of its trigger model's size; spawners and plan nav cells inside their zone volume (`--plan`, `--require-spawners`) |
| `pipeline.ps1`, `build-map-wait.ps1`, `zt.ps1`, `build-zt.ps1`, `new-work.ps1` | build orchestration under the shared resource lease |
| `native/error_journal.c` | diagnostic DLL for the local runner: Com_Error journal, fault dump, timed console commands, LuaFile dump, dvar force, RenderDoc trigger |

Older experiments kept for history: `cp_iwz_v1.gsc`, `m2a_room.py`,
`hktree_check5.py`, `simd_check.py`, `native/xref.py`, `native/disas.py`.

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
