# Map build loop: stages, keys, the base-zone question, a map of its own

Written 23 Nov 2026 for lines A6 (loop) and A7 (a map of its own) of [MAP-BUILDER-FINAL](MAP-BUILDER-FINAL.md) and tool line T2.
Everything below is read from the scripts, the build logs under `IW7-Runtime` and the engine logs of real sessions. **Nothing in
the "after" columns was run by the author of this page**: the lead runs every build. Measured and unmeasured are marked.

## 1. The stages, and what each costs

`build-g.ps1` (Station Zero) runs the generator, the gates and the bake, then `build-sz2.ps1`; `build-blend.ps1` (a Blender emit)
runs the gates, an optional bake, then the same stages. Seconds are the `build.json` laps of finished builds.

| Stage | Reads | Invalidated by | Seconds, measured |
| --- | --- | --- | --- |
| gates (`iwz_emitcheck check` and `reach`, `iwzmap_ents_lint`; `build-blend` only) | the emit folder | any emit change | not timed in any log |
| bake (`bake/lmbake.py`; Station Zero, `-Bake` in `build-blend`) | `world.bin`, the light list, bake arguments and bake tool files (stage cache `bake`, `stage_cache.py`) | a change of the render world or the lights; never an entity, script, collision or nav change | 154 s (g27r, lead, 23 Nov); `build-g.ps1` restores it from the stage cache when the key matches |
| compile (`zonetool -iwzcompile`) | the emit folder, the compiler, the template map `cp_zmb_tpl` | any emit change (`-ReuseCompile` skips it for the same `-Src`) | 6 to 7 s (blend, 8 builds), 7 to 22 s (Station Zero, 17 builds); a longer lap is the wait for the machine's build slot |
| volume check | the compiled map and `plan.json` | the compile | inside the compile lap |
| **assembly** (`assemble.py`, `sz2_assemble.py`, then the modules: perks, perk sounds, localize, kit, effects, audio, darkness) | the generated world (`dump/<map>`), 5 stock dumps (136,079 files), module sources and arguments | see the key below | **118 to 147 s** (blend, 8 builds, `incremental: false`); **166 to 447 s** (Station Zero, 22 builds, all `incremental: false`; g27r 272 s). The laps never split link from modules: the new `build.json` carries `assemble_parts` `{key, link, modules}` |
| zone (`zonetool -buildzone`) | `zonetool/<map>` and `zone_source/<map>.csv` | everything above | 36 to 41 s (blend), 45 to 115 s (Station Zero g27: 115 s for g27r); output 471 MB (blend) / 516 MB (Station Zero) |
| art zone (`build_art.py`, `-buildzone <map>_art`; `build-blend` since this change) | the art images, the assembled techsets | the title or the images | not measured (a zone of two 2D materials and a poster) |

Where the time and the bytes go: of the 29,103 rows of Station Zero's zone csv (`iwz-blend/ztwork/zone_source/cp_iwz.csv`) only 32
carry the map's name. 20,073 are stock content written in full (4,696 xmodelsurfs, 4,336 images, 4,304 xanims, 2,882 xmodels, 1,191
vfx, 943 physics assets, 548 animpkgs, 276 scriptables, ...) and 8,955 are `type,,name` references to zones the game loads anyway.
The assembly links those 135,676 files and the zone step compresses them into 471 MB, again for every map and every build.

**Why no build was ever incremental.** `build-sz2.ps1` had `-Incremental` and `assemble.py --incremental` worked (README: 232 to 297 s
full, 1 s incremental, a one-room change 52 s end to end, 11 Nov), but neither `build-g.ps1` nor `build-blend.ps1` passed it, so
all 22 + 8 recorded builds are full. The old key (`$modKey`) was a string of the dump *paths* and module arguments: it did not see
the compiler, a replaced dump file, the sources of `assemble.py` and the modules, `content/`, `IWZ_FULL_STOCK`, or a kit json.

## 2. The incremental assembly and its key (A6)

Incremental assembly is now the default in `build-sz2.ps1` (so in `build-g.ps1`) and `build-blend.ps1`; `-FullAssemble` forces
everything, `-Incremental` is accepted and does nothing.

`assemble_key.py` computes one SHA-256 over: the compiler binary, `assemble.py`, `sz2_assemble.py`, `kit_import.py` (content);
the folders `perks/`, `content/` and, when the switch is on, `darkness/`, `fx/`, the audio folder (content); the five stock dumps, the
kit and effect dump folders, the Deadeye image/scriptable, `PerkMachines` (path + size + modification time of every file, or the
quick stamp); every `techsets_*` runtime csv; the kit json; `IWZ_FULL_STOCK`, `IWZ_KEEP_STOCK_REFS`, the map name and every kit,
effect, audio and darkness argument; the order of the dumps. A missing input is an error, never an empty input.

The key is written beside the kept tree (`zonetool/<map>/.iwz_modules.key`) **only when the whole assembly finished**; it is
deleted before the assembly starts changing the tree, so a failed assembly leaves nothing that could match. A mismatch (or no key)
removes the tree and assembles everything, and says why (`an input of the assembly changed`, `no finished assembly to keep`,
`-FullAssemble`).

| Key mode | Cost (136,079 files, measured 23 Nov 2026, warm) | Sees | Does not see |
| --- | --- | --- | --- |
| default: `--manifest` | **12 to 25 s** (15.7 s typical; 8 threads; the file listing is the cost, not hashing) | a dump file replaced, grown, added or removed | a file overwritten in place with the same size and time (a re-dump that preserves times) |
| `-QuickKey`: `--stamp` | **0.0 s** | every dump's top-level files (its csv is rewritten by every dump run) and the time of every directory directly below it (a file replaced below it moves that time) | a file overwritten in place deeper down: harmless for the stock links, because a hard link sees the new bytes |

`-QuickKey` is for the frozen reference dumps of `iwz-map-ref-a`; the default is the thorough one.

**Proof on a fake tree** (`tests/test_map_build_loop.py`, 20 tests, no game): every input above moves the key (compiler, `assemble.py`,
a module source, a new module file, a dump file of another size, a same-size file with a new time, a new file, a removed file,
arguments, dump order); a missing input fails; and `AssembleTreeTest` runs a full assembly, changes the generated world (one file
changed, one added, one removed, one that shadowed a stock file removed), runs `--incremental`, and compares the tree and the zone
csv with a fresh full assembly of the same world: identical; a sentinel file proves the incremental run kept the tree; other dumps
force a full assembly. Not proven by a run: the **modules** over a kept tree on the real dumps. They were read for idempotence
(`add_perks`, `add_perk_sounds`, `add_localize`, `add_deadeye_machine` remove before they write and skip what is already in the
bank; `kit_import` keeps an existing link; `fx_import` reads the kept `ncs_efx_level.json` and only appends names that are missing,
so a rerun leaves it equal) and the README measured full against incremental with the audio module (`ff_compare.py`: same content,
0 content bytes) on 11 Nov. Kit, effects and darkness were never in a measured incremental run. **The lead's check** (once, on the real
Blender map, after two builds of the same emit):

```
python -I ff_compare.py <um_first>\cp_blend_a.ff <um_second>\cp_blend_a.ff      # build 1 full, build 2 incremental: exit 0 expected
```

What a **geometry-only rebuild** now runs (a changed section, same kit, same dumps, same compiler): gates (blend) + compile 6 to 7 s +
key 15.7 s (0 with `-QuickKey`) + `assemble.py` incremental (relinks only the generated world: README: 1 s) + `sz2_assemble.py` +
the modules over the kept tree (README: included in the 1 s with the audio module) + the zone step 36 to 41 s + the copy of 471 MB.
**Predicted, not measured: about 70 to 85 s for the 360-triangle Blender map (164 to 198 s before), 55 to 65 s with `-QuickKey`.** What
incremental does not remove: the zone step (the whole 471 MB again), the compile, the bake when `world.bin` changes, the gates. To
reach the 20 s of T2 the stock content must leave the map's zone (next section).

## 3. Must the stock content be inside every map's fastfile? (the 10x question)

**No by construction; whether the engine loads it from a second zone is one experiment away.** What the code and the logs say:

1. **Build side needs no ZoneTool change.** `require,<zone>` (`zonetool.cpp:973`) only loads that zone into ZoneTool's own process
   (build time; it has no meaning at run time). The row that makes a zone small is `ignore,<zone>` (`parse_csv_file_ignore`,
   `zonetool.cpp:871`): every `(type, name)` row of that zone's csv goes into `ignore_assets`, and
   `zone_interface::add_asset_of_type` (`zone.cpp:576`) writes an asset of that set as a reference (`,name`) instead of its data. It
   runs inside `ADD_ASSET` before `load_depending`, so a dependency a map asset pulls in is a reference too. This is how the stock
   patch zones refer to the zone they patch.
2. **The csv splits cleanly.** `split_zone.py` (an experiment tool, *not wired into any build script*) on Station Zero's real csv:
   base zone **29,028 rows** (20,073 full stock rows + 8,955 references), map zone **9,020 rows = 65 full rows of its own + the same
   8,955 reference rows** (references cost no data) + `ignore,<base>`. The 65: 23 `netconststrings` lists, 9 map-named rawfiles
   and stringtables, 6 custom/perk materials, 4 perk machine models, the world (`com_map`, `navmesh`, `fx_map`, `gfx_map`,
   `gfx_map_trzone`, `map_ents`, `glass_map`, `aipaths`, `col_map`), `gfxlightmap`, `streaminginfo`, `impactfx`, the sound bank, the
   localized strings. Everything named after the map or changed per map stays in the small zone; the stock-derived content is
   identical from build to build and from map to map.
3. **Run time is the open part.** A reference is resolved by name against the zones that are loaded; an unresolved one is silent
   (Station Zero RC4: 1,435 references to the stock map zone resolved to nothing and the Pack-a-Punch model drew nowhere, which is why
   `assemble.py` turns them into full rows). So the base zone must be loaded **before** the map zone, on the server and on every client,
   for the whole match, and delivered to joining players. What the client does today (iw7-mod `fastfiles.cpp`, `arena.cpp`,
   `party.cpp`, branch `fix/usermaps-cp-map-stats`, `6f9372c`):

| Slot a usermap folder can already hold | Requested by the engine | Served | Delivered | Verdict |
| --- | --- | --- | --- | --- |
| `<map>_load.ff` | yes, **before the map zone** (client log `a85/qa/g27d-start/run/client.stdout.log` lines 73 then 86: `Loading zone cp_iwz_load`, `Loading zone cp_iwz`) | `find_usermap` strips `_load` and serves it (`fastfiles.cpp` 180-186) | `party.cpp` `usermap_files`: `_load.ff` (optional) | **the experiment**: not shown on a dedicated server (the one dedicated log read has no usermap), lifetime unknown (a loading-screen zone may be freed when the map is up, which would leave every reference dangling) |
| `eng_<map>.ff` (language zone) | yes, as an extra of the map (`Tried to load missing language zone: eng_cp_iwz`, line 87) | `find_usermap_localized` | `usermap_loc_hash` | works for the host's language only; the world would have to be shipped under every language code; order against the map zone unknown. Not a product route |
| `<map>_art.ff` | frontend only (`load_fastfiles1_stub` scans `usermaps/` for `<dir>_art`), never on a dedicated server | yes | yes | no |
| `loadzone <zone>` console command | by hand | `find_usermap` | no | **experiment aid**: a permanent, manual, undelivered load of `usermaps/<zone>/<zone>.ff` |
| `patch_<map>.ff` | probably (the stock `patch_cp_zmb` is such an extra; a missing patch is probably tolerated by `db_is_patch_stub`: inferred from the client's code, not from a log) | **no**: `find_usermap` looks for `usermaps/patch_<map>/patch_<map>.ff` | no | needs the client change below |

**Mechanism, in one sentence:** the map zone (`<map>.ff`: world, entities, navigation, scripts, lightmap, the 65 rows) refers to a
base zone (stock models, materials, images, animations, weapons, scripts: 20,073 rows) built once per kit set; the client must load the
base first. **A client change is needed for the product** (the dedicated server, joining players and a base shared between maps all
need it), so `-SplitBase` is **not** wired into the build scripts. The design, in the iw7-mod fork:

* `fastfiles.cpp`: in `find_usermap`, serve `usermaps\<map>\<map>_base.ff` (the name the arena or a sidecar marks) next to `_load`, and
  load it ahead of the map zone: the place that sees every zone request with `is_base_map` is `db_load_x_zone_stub` (hook
  `0x1403BA920`, parameters `parent_name, zone_flags, is_base_map, failure_mode`); the engine chains its own extras (`patch_`,
  language zone) at `0x1403BA9B1` unless the zone carries `DB_ZONE_CUSTOM` (`skip_extra_zones_stub`). Two shapes: (a) when `is_base_map`
  and `usermaps\<name>\<name>_base.ff` exists, call `DB_LoadXAssets` for the base with the map's lifetime flags before invoking the
  original; (b) serve `patch_<name>.ff` from the map folder (a 10-line sibling of `find_usermap_art`) and ship the **world** as the
  patch zone and the base as `<name>.ff`: the engine's own extra-zone chain then loads it after the main zone with the map's lifetime,
  on the server too, with no new load call. Which of (a), (b) is right is decided by the lifetime and order the experiment shows. These
  are named, not verified: no client was built or run for this page.
* `party.cpp`: one more row of `usermap_files` (`_base.ff` / `usermap_base_hash`) so a joining player downloads it; a base shared by two
  maps is the same file by hash.
* Unknown to settle in the same run: whether the engine accepts a zone whose internal name is not the file's map name (a base copied as
  `<map>_load.ff` keeps the name it was built under; `IWZ-CUSTOM-MAP` lists this as the spike's open question 1).

**Experiment E1 for the lead: no client change, two builds, one session** (kills or proves the cheapest slot; ZoneTool and game runs
are the lead's):

```
# 0. a normal build first (monolithic: the baseline that stays in <UmOut>)
pwsh -File build-blend.ps1 -Src <emit> -UmOut <um>\cp_blend_a            # map from layout.json
# 1. split the csv the build left (work = Runtime\iwz-blend\ztwork), base named as the load zone of the map
$W=<Runtime>\iwz-blend\ztwork; $D=<TemplateDump>
python -I split_zone.py $W cp_blend_a --base cp_blend_a_load --junction `
  --stock-csv $D\patch_cp_zmb\patch_cp_zmb.csv --stock-csv $D\cp_zmb\cp_zmb.csv --stock-csv $D\techsets_cp_zmb\techsets_cp_zmb.csv `
  --stock-csv $D\techsets_global_cp\techsets_global_cp.csv --stock-csv $D\techsets_global\techsets_global.csv
#    expected: "split_zone: 29028 rows to cp_blend_a_load, 9020 rows stay in cp_blend_a (ignore,cp_blend_a_load first)" (+/- the kit rows of the map)
# 2. build both zones (under the machine lease, the usual zt.ps1)
pwsh -File zt.ps1 -Work $W -ZtArgs '-buildzone','cp_blend_a_load' -TimeoutSec 2400 -Owner 'split E1'
pwsh -File zt.ps1 -Work $W -ZtArgs '-buildzone','cp_blend_a'      -TimeoutSec 2400 -Owner 'split E1'
#    expected: both "Successfully compiled fastfile"; cp_blend_a.ff far smaller than 471 MB (size = the answer to "how small is the map")
# 3. install both in a second usermap folder, same name, and run the usual local session
copy $W\zone\cp_blend_a.ff, $W\zone\cp_blend_a_load.ff, the .sabl/.sabs and cp_blend_a.arena into <bench>\usermaps\cp_blend_a\
```

Expected client log lines if it works: `Loading zone cp_blend_a_load`, then `Loading zone cp_blend_a`, **zero** new `Error: Could not
find ...` lines against the monolithic run's log, the level script loaded (`Loaded custom gsc 'scripts/cp/maps/cp_blend_a/...'`
lines as before), zombies spawn, the Pack-a-Punch machine draws. Comparing the asset sets is the strict check: `listassetpool` (no
argument lists the pool numbers; then `listassetpool <xmodel pool> *`, material, image, xanim) in the monolithic and in the split
run must name the same assets. **Kills it:** the map starts with black or missing models, `Could not find` lines, or the load zone is
not loaded on a dedicated server (run the same maps on a Forge server cell and read its log for the two `Loading zone` lines).
If E1 is killed or only half works (client yes, server no), the client change above is the experiment E2 (a branch of the iw7-mod
fork; the lead builds and runs it).

What the split would give (**predicted, unmeasured**): the base is built once per kit set (the 160 to 400 s of today) and cached by the
assembly key; a map's own build is compile 7 s + a handful of files + a zone step on ~9,000 mostly reference rows and the world
(guess: under 10 s) + a small ff to copy: **about 20 s**, the T2 target.

## 4. A map of its own (A7)

`build-blend.ps1` took one fixed identity from Station Zero: every Blender map built as `cp_iwz` with Station Zero's arena file
(`cp_iwz-rc1`), so two maps collided and the browser showed STATION ZERO. Now:

* `-Map <name>` is optional: the name is `layout.json` `"map"` (the exporter writes the scene's `iwz_map`, default `cp_iwz`), else
  `cp_iwz`. `map_identity.py` checks it: `^cp_[a-z0-9_]+$` (the prefix is what makes a usermap a Zombies map, `arena.cpp`
  `MAP_INFO_ALIENS`), **at most 15 characters** (the engine's loadname field is 16 bytes, `MAP_INFO_LOADNAME`), not a stock name
  (`cp_zmb`, `cp_rave`, `cp_disco`, `cp_town`, `cp_final`, `cp_frontend`...), and not ending in `_art`, `_load`, `_base`. A request
  that differs from the emit is refused when the emit carries `modules/` (their file names and the level script calls hold the
  exporter's name), or when the emit is not named `cp_iwz`; a `cp_iwz` emit without modules can be renamed at build time.
* `-Title` (default `layout.json` `"title"`, else the name in capitals: `cp_blend_a` is `BLEND A`; at most 30 characters, the engine
  keeps 32 bytes with a 0x1F prefix) and `-Description` (at most 30). The **arena** `usermaps/<map>/<map>.arena` is generated in the
  stock arena format from them (`map_identity.py arena`; image names `image_<map>`, `image_<map>_vote`); `-Arena <file>` still copies
  a hand-made one. The title is also a localized string, key `IWZ_MAPNAME_<MAP>`, in the map zone (`add_localize --extra`); the arena
  uses the literal (the engine turns a literal into a localized one by itself, `make_literal`, and the front end does not load the map
  zone).
* **Browser art:** `<map>_art.ff` is built unless `-NoArt`: `make_art.py --plate "<title>" <dir> <map>` draws the title on a neutral
  plate (no frames, no game image) into `<UmOut>.art\`, `build_art.py` prepares the zone, `zonetool -buildzone <map>_art`, the
  file is copied to the usermap folder. `-Art <dir>` supplies `image_<map>.tga`, `image_<map>_vote.tga` (and
  `zmb_poster_<map>_c.tga`) instead. The theater poster model needs `-FrontendDump` (default `iwz-map-m2-a\dump\cp_frontend`, which holds
  the stock poster model and surface); without it the art zone has the list and vote images only. Needs Pillow (system Python).
* The level script is `<Src>\<map>.gsc` if present, else the exporter's `cp_iwz.gsc`; `assemble.py` moves its `scripts\cp\maps\cp_iwz\`
  paths (the perk module calls) to the map's folder.
* A map without a folder of its own under `content/` gets `content/cp_iwz/` with the name replaced in path and text (the table
  `cp/zombies/<map>_playercash_images.csv` the engine looks up by `level.script`); Station Zero keeps its own folder.

**Every place a map's name lives** (the checklist; each is covered by a test on a fake emit and zone tree unless marked):

| Place | Where it is set | Covered |
| --- | --- | --- |
| `layout.json` `map` | the exporter (`blend2iwz.py` from the scene's `iwz_map`) | `map_identity.resolve` |
| level script file and its `scripts\cp\maps\<dir>\` calls | emit `cp_iwz.gsc`; `assemble.py` | test: no `maps\cp_iwz\` left |
| zone csv rows and the work folders `dump/<map>`, `zonetool/<map>`, `zone_source/<map>.csv`, `zone/<map>.ff` | every build script, by `-Map` | tests |
| `maps/cp/<map>.d3dbsp` world rows, `gfx_map_trzone`, `soundbank <map>.all`, `localize,<map>` | `assemble.py`, `add_perk_sounds.py`, `add_localize.py` | csv test |
| renamed stock tables (`cp_zmb` in the name), `bl_pc_cp_zmb_zombie.bin`, `vision/*cp_zmb*`, `impactfx`, `streaming_info` | `assemble.py` (the streaming-info name is a null-terminated string behind a type byte, not a length) | stringtable test; the others by code reading |
| the content table `<map>_playercash_images.csv` | `content/<map>/` or the `cp_iwz` template | test |
| game script modules `<map>_<name>.gsc` and the Capsule Post call | `sz_modules.py` (from `layout.json`), `sz2_assemble.py` | existing; refusal test for a mismatching `-Map` |
| perk module files `scripts/cp/maps/<map>/cp_iwz_perks.gsc` (module names keep the `cp_iwz_` prefix) | `perks/add_perks.py` | level script test |
| `<map>.ff`, `.sabl`, `.sabs`, `.arena`, `<map>_art.ff` in `usermaps/<map>/` | `build-blend.ps1` | arena test; the rest by the build |
| arena `map`, `longname`, `mapimage`, `mapvoteimage` | `map_identity.py arena` | test |
| art: `image_<map>`, `image_<map>_vote`, `zmb_poster_<map>`, `mo/iwz_poster_<map>` | `make_art.py`, `build_art.py` | the plate renders (checked once, by running it, not judged) |
| the net const strings | taken from the compile's own output (`netconststrings/*_level.json`); nothing carries the name | none needed |

**The two commands for the lead, two maps side by side** (the Blender emits of two scenes whose `iwz_map` is `cp_blend_a` and
`cp_blend_b`; or one emit exported twice with the name changed):

```
pwsh -File tools-source\iwzmap\build-blend.ps1 -Src <emit_a> -UmOut <Runtime>\iwz-blend\um\cp_blend_a -Title "BLEND A"
pwsh -File tools-source\iwzmap\build-blend.ps1 -Src <emit_b> -UmOut <Runtime>\iwz-blend\um\cp_blend_b -Title "BLEND B"
```

`-UmOut` is the usermap folder (`<...>\usermaps\cp_blend_a`: pass it with that last name when installing straight into a game root).
Expected build lines: `map cp_blend_a  title 'BLEND A'`, `full assembly: no finished assembly to keep` once, then `incremental
assembly: the kept tree was made from the same inputs`; `built ...cp_blend_a.ff ... (compile .., assemble .. [key .., link .., modules ..],
zone .., art ..)`; both map folders hold `<map>.ff`, `<map>_art.ff`, `<map>.arena`.

**The browser check** (needs the client fix of the branch `iw7-mod-usermaps-cp`: the stock zombies map list reads per-map player data
`duration[<map>]` and one usermap in the list used to break the whole menu): install both folders in a bench root's `usermaps\`
and run the existing front-end probe:

```
ops\iwzmap\Test-IWZMapLocal.ps1 -Frontend -UiScript tests\fixtures\iwzmap_menu_probe.lua -TimedCmds "<ms>:set paris_iwz_ui_do lobby|<ms>:set paris_iwz_ui_do wrapmaps" ...
```

Expected in the client log: `[IWZ ui] CPMaps count N` with N counting both new maps, and `[IWZ ui] CPMaps row ...` lines naming `BLEND A`
and `BLEND B` (and the `cp_` rows), no `STATION ZERO` row for them, and focusing a row (`focusrow`) shows its poster. Unproven until
run: the title key `IWZ_MAPNAME_*` is not read by any stock script (it exists for the map's own scripts), and the generated plate art
has not been looked at in the game.

## 5. One compiler

`machine.ps1 MapCompiler` is the only place that names it: `IWZ_ZONETOOL_EXE`, else
`<Runtime>\compiler-landing\zonetool-lightvol-ea60b19.exe` (the compiler of the current Station Zero release; the light culling fix
of RC4 is in it). `build-g.ps1`, `build-sz2.ps1` and `build-blend.ps1` take their default from it; an explicit `-ZoneToolExe` still
wins. The three earlier defaults (`playeranim-1dcd449` twice, a worktree build of `x64-zt-iwz-map`) are gone; a test fails if a build
script names a compiler file again. The compiler is part of the assembly key.
