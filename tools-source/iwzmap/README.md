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
