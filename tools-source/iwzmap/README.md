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
| `lightmap_read.py` | decodes the template lightmap atlas to pick per-room texels (LDR preview; superseded by `bake/lm_decode.py`) |
| `bake/lmbake.py` | lightmap baker: charts and atlas, ray traced direct light with soft shadows, cosine-gathered bounces, AO, dilation, BC6H/BC4/R8G8 encoding; rewrites the world.bin lightmap coordinates and lighting.txt (light grid) in a baked copy of the source |
| `bake/rt.py` | numba BVH ray tracer of the baker and the measurements |
| `bake/iw7image.py`, `bake/lm_decode.py` | iw7Image/DDS IO, texconv encode/decode; HDR decode of a lightmap set (A/B/D/S terms) |
| `bake/lm_measure.py` | engine frames against a bake: camera fit, visibility-tested texel projection, per-wall luma CV, rendered-vs-baked correlation, calibration patches |
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
patches give E = A + B * Dz exactly (B-only patches render like the equal-E A-only patches); the baked/flat luma
ratio follows the baked E (r 0.87..0.985 per view); forcing S = 0/0.5/1 indoors changes nothing measurable.

Compiler switches (environment): `IWZ_GEN_TOME` (generated conservative Umbra
tome; required for complete rooms), `IWZ_KEEP_ENTSHAPES` (template entity
shapes for the reused trigger model), `IWZ_LOG_PROBES`, `IWZ_DUMP_TOME`.
Older routes (`IWZ_KEEP_UMBRA`, `IWZ_SLOT_SURFACES`) are superseded.

## Players

A zombies usermap also needs the iw7-mod `Usermaps` script fix (fork branch
`fix/usermaps-cp-map-stats`): without it one installed `cp_` usermap breaks the
whole CHOOSE FILM list.
