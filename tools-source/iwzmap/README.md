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
| `build_art.py`, `make_art.py` | map browser art zone `<map>_art.ff`: 2D list/vote images and the theater poster model, made from engine renders |
| `lightmap_read.py` | decodes the template lightmap atlas to pick per-room texels |
| `tome_read.py` | reads an Umbra format-20 tome header |
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

Compiler switches (environment): `IWZ_GEN_TOME` (generated conservative Umbra
tome; required for complete rooms), `IWZ_KEEP_ENTSHAPES` (template entity
shapes for the reused trigger model), `IWZ_LOG_PROBES`, `IWZ_DUMP_TOME`.
Older routes (`IWZ_KEEP_UMBRA`, `IWZ_SLOT_SURFACES`) are superseded.

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
