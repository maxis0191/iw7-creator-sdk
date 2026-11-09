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
| `iwz_emitcheck.py` | offline gate on an emit: collision, nav, links, stairs, spawners, routes, build-to-build diff |
| `iwz_probe_forensics.py` | recorded probe logs to per-zombie classes, verdicts, trust flags, flaky cases, hotspots |
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

Both tools read; neither builds, launches or writes into an emit. Tests:
`python -B -m unittest discover -s tools-source/iwzmap/tests`.

## Players

A zombies usermap also needs the iw7-mod `Usermaps` script fix (fork branch
`fix/usermaps-cp-map-stats`): without it one installed `cp_` usermap breaks the
whole CHOOSE FILM list.
