# A. Tools readiness digest for STATION ZERO (cp_iwz)

Read-only research. Written 2026-11-10 from the server repository worktree
`<server-worktree>` (HEAD ddbae138, clean) plus the two side-session notes.
Nothing was launched, built, committed or modified. No account or key data was read or copied.

## 0. How to read this file

Citation form: `DOC:section` (docs are in `docs/` of the worktree). Abbreviations:

| Abbrev | File |
|---|---|
| CC | docs/CREATION-CORE.md |
| DK | docs/DEVKIT.md |
| DP | docs/DEVKIT-PLAN.md |
| TI | docs/TOOLS-INDEX.md |
| ICM | docs/IWZ-CUSTOM-MAP.md |
| IPT | docs/IWZ-PLAYTEST.md |
| KINO | docs/KINO.md |
| EP | docs/ENEMY-PORTING.md |
| BWW | docs/BO3-WONDER-WEAPONS.md |
| MOD | docs/MODULES.md |
| side/CCD | side-session-notes `creation-core-design.md` (information only) |
| side/OQ | side-session-notes `owner-queue-2026-11-10-night.md` (information only) |

Extra files I also read where the ten requested docs pointed to them (all in the same worktree unless noted):
BO3-WW-CATALOG.md (WWC), CAPACITY48.md, RUSH-AUDIT.md (RA), USERMAPS.md, CLIENT-COMPATIBILITY.md (CCOMP), GAMELAB.md (GL),
ATLAS.md, ENGINELAB.md, QUALITY-LEDGER.md, UI.md, MAXIS.md, NEIL-FINALE.md, DJ-PLAYLIST.md, PERKS-REVIVE.md,
`docs/deployments/2026-10-20-capacity48-owner-regression.json`, `config/*.json`, and
`<runtime>/iwz-stage2\CONTEXT.md` (stage2 shared context, 6-9 Nov; label S2CTX).

Status words are the docs' own. CC defines them strictly (CC:"Readiness by kind of creation"): **Works** = an agent in a fresh
session can do it with the documents AND it was proven in the running game by agent tests on a private server. **Built** = the
tool exists but the result was not proven in the running game, or lives on a side branch. **Missing** = nothing exists.
"Accepted" = the owner played it and said yes; "on this date nothing below is accepted except where said" (CC).

Documents are of different ages. Where they disagree I say so in section 6. Rule of thumb: CC (10 Nov evening) and DK
(10 Nov) are newest; ICM (6 Nov, rc1) and USERMAPS (27 Oct) are older and partly superseded.

---

## 1. The readiness table and the work packages

### 1.1 Readiness by kind of creation (CC:"Readiness by kind of creation (10 Nov 2026, evening)") - reproduced faithfully

| Kind | Works | Built, not proven or not landed | Missing |
|---|---|---|---|
| Weapons from Black Ops 3 | Four weapons ported with the one-command porter (Ray Gun, Thundergun, DG-2, Ray Gun Mark II): drawn, fired, reloaded, Pack-a-Punch at the real machine (6 to 8 Nov). The official client downloaded the mod by itself on a private server (6 Nov). File checks in seconds (preflight 1.6 s, audits 3 to 16 s, zone build 7 s) | The combined mod build is on a side branch (`codex/bo3wpn-paris-mod`); per-weapon loudness and the sound capture tool are on side branches. Not deployed to players. Sound never measured as audible. No end-to-end port time was ever recorded | Each new behaviour family needs a hand-written script (only Thundergun push and DG-2 chain exist): charge shots, dual wield, model scaling are unsolved. Weapons from other games |
| New maps | One generated map (Station Zero) builds and runs; file checks in 2 s | Version 2 of the generator, lighting bake, effects, art, audio, darkness, model catalogue, kit import and the map compiler itself are on side branches (being landed 10 Nov). A build takes about 20 minutes. Delivery of a map by a dedicated server to players is unproven | Detail at the level of a shipped map (264 surfaces against 10,760; reviewers about 5 of 10). Rooms reused from shipped maps (a prefab can be lifted; the generator cannot place it yet). Visibility culling for large maps |
| Changes to shipped maps | Read a shipped map as data (`worldkit`, 3.4 s for Spaceland). Hide and restore placed props in the running map, for the author only (792 props of the spawn plaza, proven by frame measures, 10 Nov). Entity edits on a private server through a loose entity file (an arcade game removed, a model added, a key changed; all counts matched, 10 Nov) | Whether clients need the entity file too is not measured | Render changes that other players see. Collision of removed things (hidden props still block). Removing or adding walls and floors. Lighting and navigation of a changed area. Triggers and brush entities added |
| Models and characters | An authored rigid model drawn in the game (7 Oct). A modified skinned body and a recoloured outfit drawn in a custom map (9 Nov) | Any-glTF prop import, skinned writer, zombie body kit: side branches (being landed 10 Nov). The zombie kit was never built into a zone | Collision for imported models. New shaders (looks are stock techniques with custom textures). Hero outfits were rejected by reviewers (2 to 4 of 10). Third person on real players unproven |
| Animations | Black Ops 3 weapon animations retargeted onto the game's hands, played through real input (6, 7 Nov). The codec reads all 4,029 Spaceland animations and writes them back within 0.004 degrees | An original four-key clip survived a zone round trip offline (12 Oct); never seen playing | Any path from Blender or glTF to a game animation. Full-body, additive and root-motion authoring. An animation of ours playing on a character in the game |
| Enemies and bosses | Ported retail enemies: Rhino on Spaceland (owner confirmed 2 Oct, then parked by choice), Slasher partly, Kino script-driven zombies (20 of 20) | (empty cell) | A brand-new enemy with its own model, animations and behaviour (needs the two rows above). Boss arenas and quest services |
| User interface | Server-drawn pages reach every player with no download (the Maxis terminal is deployed on both servers since 8 Nov). Limit: 24 elements per player | A Lua HUD in the Black Ops 3 style: 359 offline tests, one real run with a wrong layout | Menus and HUD replaced for players: the official client (v1.1.0, 26 Sep) does not load Lua from a mod; the change that allows it was merged in the client project on 30 Sep (its pull request 697) and is not released (checked 10 Nov). Any way to read the UI as data (element tree, positions, texts): UI review still needs eyes |
| Knowing what happens in the game | Headless test plans (40 s, 1.1 GB), client plans with frames, frame rate and cost per function, network lab, soak, freeze and crash readers, map atlas, ledger of known problems, several sessions at once | (empty cell) | Which object a pixel shows (depth capture). UI as data. Sound measured from the game (tool on a side branch). Reports for single slow frames. Cause of the join stall (1 in 3 lab joins; runners retry) |

Also in CC, the survey facts of 10 Nov (CC:"Where creation stood"): custom map = Python code emitting boxes with stock materials,
**264 surfaces, about 170 props**; Spaceland = **10,760 surfaces, 17,010 props, 1,039 lights, 160 reflection probes**; independent
reviewers' score of the custom map vs shipped maps **about 5 of 10**; one build = **bake 4 to 8 minutes, then zone build about
14 minutes**. "Not possible today": authoring behaviour trees and animation classes (no on-disk form, copied live from the game);
compiling shaders from source (copied as compiled bytes); a Blender or glTF path to an animation; real visibility culling for a
new map (everything is always drawn); unloading or reloading a zone. "Possible today and under-used": a loose `<map>.ents` file
replaces a shipped map's whole entity list at load with no build; scripts can spawn any loaded model, play animations, effects
and sounds and clone collision; the loader has the game's world/scene/lights/collision structures declared, holds the graphics
device and can copy an engine render target by name; `loadzone` exists (CC:"Where creation stood", repeated in side/CCD).

### 1.2 The eight design pieces (CC:"The design: one description, several backends") with state on 10 Nov

| # | Piece | State on 10 Nov 2026 |
|---|---|---|
| 1 | World as data (`worldkit`, iw7-creator-sdk) | merged 10 Nov (SDK PR 39): Spaceland read in 3.4 s, all counts exact; prefab of spawn plaza lifted (483 props, 437 surfaces, 36 lights) |
| 2 | World patch (one file, two backends) | designed |
| 2a | Live backend (components, lab client) | hide and restore of props proven 10 Nov (792 props, frame measures); collision stays; being landed |
| 2b | Build backend (map compiler, x64-zt-extensions) | needs the compiler branch landed first |
| 3 | Entity overlay (SDK + gamelab) | proven 10 Nov on a private server (5 removed, 1 added, 1 key changed); being landed |
| 4 | Content catalogue | models exist on a branch (13,113 models with sizes); the rest is to build |
| 5 | Seeing through data (depth + camera per frame) | to build (render-target copy exists) |
| 6 | Actors | writer for skinned models exists on a branch; animation path from Blender is missing |
| 7 | Looks and the renderer (shaders, post-process) | to build |
| 8 | Budgets (counts per area, culling) | measuring exists; culling open |

Build order (CC:"Build order"): 1 worldkit; 2 live world editor; 3 entity overlay headless proof; 4 world patch + live backend, then compiler edit mode;
5 prefabs into the generator (props first, then surface meshes with collision); 6 depth capture + pixel-to-object; 7 catalogue beyond models, actors, shaders; 8 landing scattered branches.

World-patch tiers (side/CCD:"World patch: design decisions"): server-only tier can do entity edits and script-spawned props (cannot remove studio geometry or its
collision; entity limit on many props); live tier = author only, collision of hidden things stays; build tier = everything incl. collision but needs the compiler edit mode or an overlay zone.
Open measurements that decide the tier: free entity slots late round per shipped map; does a client also read the loose entity file; sizes (done); does a same-name asset in the mod zone replace a shipped world; bake a prefab into 4-10 models with collision.
Measured (side/CCD): Spaceland render world 95.5 MB, collision 15.0 MB, lights+probes 1.7 MB, entities 1.1 MB, navigation 0.6 MB; whole zone file 196 MB; a patch of about 115 MB before compression.

### 1.3 Work packages (CC:"Work packages")

**Count: CC lists 29 packages (M1-M5, N1-N6, A1-A3, C1-C4, W1-W4, U1-U3, S1-S4), not 26.** (M5+N6+A3+C4+W4+U3+S4 = 29.) DP separately lists 13 lettered packages (A, A2, B..L), see 1.4.
Model rule (CC): Fable 5.2 medium for difficult packages, Sonnet 5.5 only for the easiest.
Status tally: running 6 (M1, N1, N2, A1, C1, U1); queued 3 (M2, N3, S1); blocked outside project 1 (U2); open 19.
"Unlocks" below = what the package gives per its own Package/Proof text, plus the packages that list it under "Needs".

| Id | Title | Status | Proof (CC) | Needs | What it unlocks |
|---|---|---|---|---|---|
| M1 | World patch seen by every player (small file changes the render world of a shipped map, no game copy) | running | Spawn plaza emptied for a client that received the file; frames; file size; stock files untouched | worldkit | Shipped-map transformation for all players; gates M2, M3 |
| M2 | Collision follows the patch (removed props stop blocking, added things block) | queued | Walk through the emptied place; walk against an added thing | M1 | Honest walls/props in a changed map; gates M3 |
| M3 | Walls and floors: remove surfaces; add a room lifted from another place/map as a prefab (few models with collision, or surfaces in the world) | open | New room in Spaceland a player enters; frame rate vs stock | M1, M2 | Whole new rooms in a shipped map; gates M4, M5 |
| M4 | Light of a changed area (lightmaps, probes, baked shadows) | open | Brightness of changed room vs source room, from frames | M3, N2 | Correct lighting in changed areas |
| M5 | Zombies in a changed area: entity edits (spawners, doors, triggers), navigation | open | Zombies spawn in and cross the new room in a headless plan | entity overlay, M3 | Playable changed areas |
| N1 | Map compiler on the main line of ZoneTool | running | Same map compiled by branch build and main build: identical files | - | Gates N3, N4; lands `-iwzcompile` (today only on x64-zt branches) |
| N2 | Generator v2, bake, effects, art, audio, darkness, catalogue, kit import on the SDK main line | running | Their own tests and local checks | - | Gates M4, N3, N4, A3 |
| N3 | Prefabs into the generator: a room dressed with a shipped room's props, then built from its surfaces with collision | queued | Room in the game; counts and reviewers' score vs source room | N1, N2, worldkit | Studio-level detail in Station Zero; gates N5 |
| N4 | Build time from about 20 minutes to minutes (bake only what changed, zone only what changed) | open | Measured time for a one-room change | N1, N2 | Fast iteration |
| N5 | Large maps stay fast: visibility culling or equivalent for generated maps | open | Frame rate across the atlas of a map several times larger than Station Zero | N3 | Maps larger than Station Zero without frame-rate loss |
| N6 | A custom map reaches players from a dedicated server by itself | open | A client without the map joins a private server and plays | - | Online delivery of Station Zero (owner Rule 2) |
| A1 | Model import, skinned writer, zombie kit, sound bank tools on the asset tools' main line | running | Their own tests and local checks | - | Gates A2, C3, W1 |
| A2 | Collision for imported models | open | Player blocked by an imported prop; a bullet trace | A1 | Imported props that block |
| A3 | Catalogue of everything (materials, textures, effects, sounds, animations; cost; where shipped maps use them) | open | Queries answered in under a second; counts against dumps | N2 | "Find me a rusty door" style queries |
| C1 | Animation path: glTF (from Blender) to a game animation and back (full body, root motion, notetracks) | running | Every stock animation through glTF and back within a tolerance; a new clip built into a zone | - | Gates C2 (emotes, new enemy moves) |
| C2 | An animation of ours playing on a model in the game, measured (bone positions in game vs source) | open | Error per bone per frame, no eyes | C1 | Gates C3 |
| C3 | Actor kit: model, animations, hit volumes, sounds, effects, script-driven state machine (the Kino route), as data | open | New enemy walks, attacks, takes damage, dies in a headless plan, then frames | C2, A1 | Brand-new enemies/bosses; gates C4 |
| C4 | Fidelity to a source actor of another game (moves, timings, sizes by numbers) | open | A report per move | C3 | Ported bosses with measured fidelity |
| W1 | Combined mod build, per-weapon loudness and sound capture on main lines; each weapon's sound measured from the game | open | Level and presence of each weapon's fire sound in a capture | A1 | Gates W2 |
| W2 | Fresh-session trial: an agent with only documents ports one new BO3 weapon; time and stuck points recorded | open | End-to-end time written in documents | W1 | Gates W3 |
| W3 | Behaviour families as reusable scripts: charge, dual wield, scaled models, projectiles with area effects | open | One weapon per family in a headless plan | W2 | Gates W4 |
| W4 | Weapons from other games of the series | open | One weapon end to end | W3 | - |
| U1 | UI as data: dump of the client's element tree on request, and checks (overlap, clipping, off-screen) | running | Known wrong layout of the Lua HUD detected without a screenshot | - | Gates U3 |
| U2 | Lua UI for players | blocked outside the project | Needs the client project to release its merged change (PR 697), or players on a client this project builds. Asking the client project is the owner's to do | - | Gates U3 |
| U3 | Full HUD and menu kit on the Lua route, tested with U1 | open | Every screen passes layout checks; frames judged by independent reviewers | U1; U2 for players | Replaced menus/HUD, Tab/scoreboard (not stated in CC) |
| S1 | Depth and camera with every test frame; a pixel names its object through the world database | queued | "What is at pixel x,y" right for 20 known props | live editor | Visual questions answered as data |
| S2 | Reports for single slow frames with the functions that cost the time | open | A provoked hitch found and named | - | Hitch diagnosis |
| S3 | Fresh-session trials for every kind above (time, stuck points) | open | A table in CC, renewed after each fix | - | Measured "can a new agent do it" |
| S4 | Cause of the join stall | open | Stall reproduced on demand or explained | - | Reliable joins in tests (1 in 3 lab joins stall today) |

### 1.4 DP work packages (DP:"Work packages"; older, environment-side)

Sizes S ~ hour, M a few hours, L a day. Status as the doc states (many not stated).

| # | Package | Judge | Size/model | Status in DP |
|---|---|---|---|---|
| A | Finish and run the network lab runner live (0,100,200,300 ms, 2 % loss) | joins at each setting; packet rates | - | Done 10 Nov for one client, 30 s sessions; remaining: two clients, longer, with server scripts loaded |
| A2 | Join stall: find where the join sequence waits | 30 lab joins in a row without a stall | M | open (hole 11: 1 join in 3 stalls) |
| B | The guide (DEVKIT.md) | every command runs as written; fresh agent finds the tool for 10 sample questions | S, Sonnet | DEVKIT.md exists; the 10-question test is not stated |
| C | Get-LabClient | prints path; second call instant | - | Done 10 Nov |
| D | Performance A/B command (-Base -Candidate -Plan -Repeats 3) | identical commits "no difference shown"; +1 ms sleep "slower" | M, Sonnet | not stated (DK only lists `iw7_perf.py compare`, run by hand) |
| E | Crash to named stack (`iw7_crash.py`) | crashed lab client gives a stack | - | Done 10 Nov |
| F | Server pin to current components | Build-Voice runs from server inputs; checks green | L, Opus | not done; branch `claude/components-pin` (2 ahead, unmerged per TI) |
| G | Net counters inside the game | at 200 ms added ping the reported ping rises by 200 ms | L, Opus | partial: client update counter and fire probe proven; per-client ping and server recorder remain |
| H | Gamelab on a dedicated server (clients join, bots) | `buttons-available` passes on a dedicated session; 7 bots hold | L, Opus | not stated |
| I | Engine map names from strings, console-variable table, struct layouts | names from 588 to several thousand | M, Sonnet | not stated |
| J | GPU time per pass from a RenderDoc capture | table of passes summing near frame time | M, Sonnet | not stated (renderdoc_* scripts exist in `ops/iwzmap`) |
| K | Make always-red checks green; install Java and Ghidra | full local run green in each repo | M, Sonnet | not stated |
| L | Measure recorder's own cost and the loader's share of frame time | table | S, Sonnet | not stated |

---

## 2. Tool catalog

Times are as written in the docs (10 Nov 2026 unless said). "Limit" = what the doc says it cannot do. Repos: server = iw7-paris-server, sdk = iw7-creator-sdk,
ext = x64-zt-extensions, comp = iw7-mod-components, x64-zt = ZoneTool fork. "Merged" vs "branch" per TI; where CC contradicts TI I note it.

### 2.1 Map building

| Tool (path) | Question it answers / what it does | Timing | Limits / state |
|---|---|---|---|
| Generator v1: `iw7-creator-sdk/tools-source/iwzmap/station_zero.py`, `mapgen.py`, `assemble.py` | rooms -> world.bin, nav, ents, zone sources (Station Zero rc1) | (build ~20 min incl. bake+zone, CC) | Emits boxes with stock materials: 264 surfaces, ~170 props (CC). Merged 2026-11-06 (TI) |
| Generator v2 (g27e): `station_zero2.py`, `sz2_*.py`, `brushkit.py`, `cp_iwz2.gsc` + lint/proof scripts | Station Zero v2 | not stated | TI says merged 2026-11-10; CC says "on side branches (being landed 10 Nov)"; TI unmerged list still shows tips `codex/iwzmap-station-zero-v2` (186 ahead) and `codex/iwzmap-darkness` (231 ahead), each lacking the other's work |
| Collision writer: `hkcm.py`, `hkcm_write.py`, `hkpack.py` (sdk) | Havok compressed-mesh collision for a generated map | not stated | Merged 2026-11-06. Havok hk_2014 compressed mesh, scale 1/32, tag 382 solid (S2CTX). Imported-model collision missing (A2) |
| Map compiler: ZoneTool `-iwzcompile` (`src/zonetool/zonetool/iw7/iwzmap/iwzmap.cpp`) | compiles world, tome, light grid, doors, lightmap, darkness against a template map (`-iwzcompile cp_zmb_tpl cp_zmb <map> <source dir>`, S2CTX) | zone build ~14 min | **Only on x64-zt branches** (tip `codex/iwzmap-darkness`, 36 ahead, 2026-11-08); N1 running to land it on main. Template = cp_zmb world for sun, sky, light grid, probes (ICM) |
| Compiler add-ons (branches): `iwzmap_volumes.cpp` (trigger volumes with physics shapes), `iwzmap_lightmap.cpp`, door brushmodels, static model collision scope, `dumpzonetypes` | volumes, lightmap atlas, doors, static models, kit import | not stated | All unmerged; volumes branch diverged from the darkness tip (TI) |
| Lighting bake: `tools-source/iwzmap/bake/lmbake.py`, `lm_measure.py` | ray-traced lightmap and light grid for generated worlds; measure | bake 4 to 8 min (CC) | Merged 2026-11-10 (TI); CC lists lighting bake among "side branches". TI "Largest risks": bake in none of the v2 tips |
| `iwz_emitcheck.py check / diff / route / at` (sdk) | map source wrong (walls in path, floating path)? diff of two builds; walk length (to size a timeout); what is built at a point | ~2 s each (DK) | Merged 2026-11-09 |
| `iwz_zonecheck.py` (sdk) | everything emitted is listed, present, packed in a fresh compiled file | not recorded (DK) | Merged 2026-11-10 |
| `iwz_probe_forensics.py` (sdk) | recorded probe runs -> per-zombie verdicts, hotspots | under 1 s | Merged 2026-11-09 |
| `sz2_navconn.py`, `track_clearance.py`, `volume_check.py` (sdk) | offline: can zombies climb/cross as players do; compiled trigger volumes have point-testable physics shapes | not stated | Merged 2026-11-10 (TI) |
| `iwzmap_ents_lint.py` (server `ops/iwzmap`) | entity source vs stock recipe (spawner kinds, door pairs and collision targets, specials, relay/trap markers) before any launch | seconds (DK) | Reproduces every static rc1 finding (IPT) |
| `worldkit` (sdk `tools-source/worldkit`: `iw7_world.py`, `iw7_dump.py`; commands build, stats, box, near, find-model, where-model, rooms, check, compare-smodels, extract, place) | shipped map dump -> database; query by place/name; lift a box as a **prefab**; place a prefab rotated | Spaceland read in 3.4 s; DB 37 MB + 25 MB mesh file; prefab of spawn plaza 483 props / 437 surfaces / 36 lights / 69 entities (side/CCD) | Merged 10 Nov (SDK PR 39, CC). TI "Largest risks" still says "empty folders" (stale). **The generator cannot place a prefab yet (N3 queued)** |
| Entity overlay: `tools-source/mapents/iw7_mapents.py` export/stats/find/patch/write/diff (sdk) | change a shipped map's entity list with no build via loose `<map>.d3dbsp.ents` in `iw7-mod/maps/cp/` | export+patch under 1 s; headless proof ~45 s | Proven 10 Nov on Spaceland (remove 5, add 1, change 1). Server only proven; client reading not measured; adding trigger/brush entities not tried (GL:"Entity census") |
| Live world editor: `src/native/paris_world.cpp` (comp; docs/WORLD-LIVE.md in comp) | read placed props from the running map, hide them in a box (author only) | 792 props, frame-measured | TI: merged 2026-11-10; CC: "being landed". Collision stays |
| Map atlas: `ops/atlas/atlas.py` + gamelab `survey` step | every reachable place of a map visited and measured (frame rate, frame check, floor ray) | survey 3000 pts in 59 s; ~10 s a point; 40 points/plan; 3000 pts = ~75 plans, 10 h | Only 12-point sweep run; whole map not done; follows navmesh only, closed doors/teleporters/ledges missed; one map version (ATLAS:Limits, First live run) |
| Build scripts: `pipeline.ps1`, `build-map-wait.ps1`, `zt.ps1` (sdk) | map build under the shared resource lease | ~20 min | merged 2026-11-06 |
| Map art: `build_art.py`, `make_art.py` (sdk); `tools-source/iwzmap/art/` generators, `sz2_artlint.py`, `sz2_mood.py` | list/vote images + poster model; seeded grime/decals/signs/boards/chalk generators + lints | not stated | merged (TI) |
| Darkness: `tools-source/iwzmap/darkness/` (`dark_build.py`, `dk_measure.py`, `make_vfx_light.py`) | dark until power, flashlights, light groups | not stated | TI merged 2026-11-10; branch-only per CC |
| Train kit: `train_proof.py`, `train_perf.py`, `fixtures/train_kit.gsc` (sdk) | moving train set piece, proof and cost | not stated | merged 2026-11-10 (TI) |
| Catalogue: `catalog/iwzcat.py`, preview booth (sdk) | catalogue of stock models from ZoneTool dumps; engine preview booth | queries target <1 s only for A3 | 13,113 models with sizes (CC). Models only; materials/textures/fx/sounds/anims catalogue = A3 open |
| Kit import: `kit_import.py`, `kit_proof.py` (sdk) | link stock models of other zones into a usermap; prove drawn in engine | not stated | merged 2026-11-10 (TI); CC says side branch |
| `t7-map` (ext `tools-source/asset-bridge/t7-map`) | BO3 map -> IW7 rigid models, images, materials (Kino, 24 rigid xmodels) | not stated | merged 2026-10-27; geometry only, no BSP/clip/navmesh authoring (KINO) |
| Map runners: `Test-IWZMapLocal.ps1`, `Test-IWZMap.ps1` (server `ops/iwzmap`) | private dedicated + client run of a generated map; second client join via timed console commands | session ~ the `-Seconds` given | uses base game + resource lease + lock; stages and restores files (S2CTX) |
| Map playtest: `Test-IWZMapPlaytest.ps1`, `iwzmap_playtest_report.py` | map-agnostic zombies-game QA: phases inv, bounds, isolation, walk, buy, quest, trap, stairs, spawners, cleanup, perf, rounds, routes, climbs | up to `-Seconds` (30 min in the doc); lint seconds | Private local session only; needs a client (it is not headless). Report discards runs whose hashes differ (IPT) |

### 2.2 Testing

| Tool | Question | Timing | Limits |
|---|---|---|---|
| Gamelab: `ops/gamelab/Invoke-GameLab.ps1`, `gamelab.py`, `gamelab_rt.gsc`, `gamelab_input.py` | does it work in the game? JSON plan -> verdict class (pass, product, crash, map_load_failed, input_channel, harness, infra) | `-CompileOnly` seconds; ~45 s a plan; a launch costs ~2 min before the first question; client session ~9 GB | Session max 600 s; local listen session only; frames measured (not black/flat/diff) not judged; buttons need a bench client built from current components (`keys/1`), older client = fire + short aim tap; 29 step kinds (GL) |
| Headless gamelab: `Invoke-GameLabHeadless.ps1` | same plans with a private dedicated + one engine bot, no client | 37 s solo; 4 at once 39-41 s each; 8 at once 7 passed in 146 s; ~1.1 GB peak | **Loads only the five stock maps, no usermap** (refused otherwise); refuses plans needing capture/perf/press/walk/tour/fx/frame expectations. Bot has no input; `chase` with bot target, weapons other than `iw7_fhr_zm`, plans over a minute, other maps, more than two at once: not verified |
| Bench roots: `ops/bench/New-BenchRoot.ps1`, `Test-BenchRoot.ps1`, `Remove-BenchRoot.ps1` | where do I run a game without a 100 GB copy | create 2 s, remove 1 s; client bench ~402 MB; stock 78.7 GB shared | Never force-delete; refuses key files, profiles, bank, `players2`, ports of Main/labs |
| Scheduler (comp `Resource-Scheduler.ps1`) | admission by memory; shareable reservations | 16 server-only sessions (1.5 GB) or 4 clients (5 GB) with 8 GB reserve | only two at once verified live; two scheduler fixes on separate branches |
| Soak: `ops/soak/Invoke-Soak.ps1`, `soak.py` | does it still work after an hour (leaks, tables, stuck rounds) with 0-7 bots | 1-720 min; 6 min, 3 bots PASS recorded | one-hour-per-map run, client in session, server frame times not done |
| Netlab: `ops/netlab/Invoke-NetLab.ps1`, `netlab_proxy.py` | play at chosen ping/jitter/loss; key-to-server time | ~91 s a run; 93 ms no delay, 236 ms at +200 | one client, 30 s sessions proven; two clients, longer, with server scripts not |
| Quality ledger: `ops/quality/ledger.py` | ranked known defects (add, import-crash, import-gamelab, import-log, list, show, close, stats) | <1 s | "Nothing writes into the ledger by itself yet" (QUALITY-LEDGER:Limits) |
| Isolated lab / agent lab: `Isolated-Lab.ps1`, `Agent-Lab.ps1`, `Agent-Pair.ps1` | private test dedicated (loopback, password) with bot/pair | not stated | - |
| Kino E2E: `ops/kino/Test-KinoE2E.ps1` | code-driven end-to-end of the Kino overlay (no client, no screenshots) | not stated | bot-only noise: consumable meter; purchases by real player NOT_PROVEN |
| Weapon E2E / visual: `ops/bo3wpn/Test-WeaponE2E.ps1`, `Test-WeaponVisual.ps1`, `Restore-WeaponVisual.ps1` | weapon definition, bot equips/ammo/projectile damage, PaP machine; client witness incl. auto-download | not stated | visual witness serialised by a system mutex; interrupted runs need Restore |

### 2.3 Engine

| Tool | Question | Timing | Limits |
|---|---|---|---|
| Engine loop `ops/enginelab/Invoke-EngineLab.ps1` | I changed native code: build, bench, plans, verdict | first build 133 s; one-file change 70 s; compile error reported at 38 s; plans 45-52 s | exclusive build slot; one build tree per loop; client cannot be built from the server repo's own pinned inputs (DP hole 1) |
| `Get-LabClient.ps1` | current lab client path | first 70-133 s; then instant | - |
| Engine map (comp `ops/engine-map/iw7_engine_map.py`: build, at, callers, refs, find-string, strings, suggest-names) | what is at an address, who calls it | build ~5 s; 50,095 functions | only 588 named (DP hole 8); callers/refs timing not recorded |
| Perf recorder (`iw7_perf.py report/compare`, gamelab `perf` step; client built with `-BuildSwitch 'ServerModules,IsolatedLab,Debugger,Perf'`) | frame time and cost per function | 2 x 20 s windows; baseline 184 and 318 fps (i5-13400F, RTX 3080, 1280x720) | run-to-run 2.5-3.9 %; below ~5 % needs 3 runs a side; no GPU timing (RenderDoc scripts exist, package J) |
| Crash reader `iw7_crash.py` | where did it crash | 0.2 s a dump | signature uses 3 verified frames |
| Freeze reporter (`-paris-hang`) | where did a >2 s freeze happen | report per freeze | - |
| Memory watch (netlab `-Watch`) | where does the game keep a value | session length | - |
| Net report `iw7_net.py` | server updates reaching client and how late | <1 s | packet-level only (DP hole 6) |
| Debugger `Debug-Server.ps1`, `Debug-Session.ps1`, `iw7_debugger.py` | crash/script failure/slowdown capture | not stated | native instrumentation needs isolated Modules -Debugger build |
| Reverse tools (`query_project.py`, ops/ghidra) | Ghidra project queries | not stated | Ghidra not installed (DP hole 9) |

### 2.4 Weapons

| Tool | What | Timing | Limits |
|---|---|---|---|
| Porter `t7_port_weapon.py`, `t7_mod_assemble.py` (+recipes; ext) | one command ports a BO3 weapon to an IW7 mod zone; assembles into `mod`; rewrites two generated blocks (catalog, behaviours) of `paris_bo3wpn.gsc` | zone build 7 s; no end-to-end port time ever recorded | behaviours exist only for `zm_weap_thundergun` and `_zm_weap_tesla`/lightning_chain (BWW) |
| Audits `iw7_weapon_feel_audit.py`, `_sound_audit.py`, `_fx_audit.py` | weapon fields/sounds/fx against stock | 3 to 16 s each, 22 s for four tools | - |
| Mod preflight `iw7_mod_preflight.py` | whole mod tree fit for a build; weapons changed since accepted | 1.6 s | - |
| Build-log gate `zt_buildlog_gate.py`; loader readback `Read-CompiledZone.ps1` | did the build produce what was asked; does the loader accept it | seconds; ~9 s | - |
| `iw7_mod_reference_audit.py` | stock assets a mod names that only one map carries (a mod zone loads on all five maps) | not stated | found the zapper-template tracer/techset fault on Rave |
| Material/fx/sound/model converters: `t7_material_pack.py`, `t7_fx_to_iw7.py`, `t7_weapon_sound.py`, `t7_env_port.py`, xanim codec, `t7_vm_retarget.py` | BO3 materials (2-UV camo, emissive, glass templates), fx -> IW7 vfx, sounds -> aliases, models, anims, viewmodel retarget | not stated | heat-distortion ring skipped; long-animation layout needed a ZoneTool fix |
| `Build-ParisMod.ps1 -Bo3WpnSource -Audio -DjSongs -MaxisArt` (server) | builds the single mod zone `mod` (mod.ff/.sabl/.sabs) | not stated | one zone + one bank only; combined sizes 29.9 MB (BWW) |
| Audio witness `Capture-ProcessAudio.ps1`, `audio_report.py` | how a weapon sounds in game and how late after the press | unit test 0.2 s | merged 10 Nov; weapon sound still "never measured as audible" in CC |
| `Serve-ModDownload.py/.ps1`; `Install-ServerMod.ps1` | serve the three mod files; separate server root | - | - |

### 2.5 UI

| Tool | What | Limits |
|---|---|---|
| `paris_ui.gsc` HudElem pages (UI.md) | `.menu/.help/.mods` panels, 8 HudElems each | text + two stock materials; no mouse; superseded by Maxis terminal on both servers |
| Maxis terminal + vote (`MAXIS.md`, `ops/maxis/make_art.py`) | LUI tier with HudElem fallback | LUI tier not rendered for stock clients |
| Lua HUD (`bo3_zombies_hud/__init__.lua`, `ops/hud-lab`, `Preview-BO3HUD.ps1`) | BO3-style HUD on the client | one real run with wrong layout; 359 offline tests |
| U1 UI-as-data | dump of client element tree | running, not landed |

### 2.6 Audio

| Tool | What | Limits |
|---|---|---|
| `iw7_sab.py`, `iwz_audio_bank.py` (ext `iw7-audio`) | read stock sound banks; write a ZoneTool bank source for a map | merged 2026-11-10 (TI) |
| `audio/` (sdk): bank spec, hidden-song module, 25 emitters, `audio_measure.py`, `music_find.py`, `soundscape_dsp.py` | map audio and measurement vs source | merged 10 Nov (TI); CC says side branch |
| `lossy_flac.py` (+ lossyWAV, flac) in `Build-ParisMod.ps1` | size-cut FLAC (24.3 MB -> 15 MB for a song; 16 songs 63 min -> 73.3 MB at 28 kHz dual-mono) | stock banks are FLAC only |
| `t7_sab.py`/`kino_sound.py` | list/extract BO3 banks; write a bank source (Abracadavre) | - |
| Sound agent lab | protected client lookup of mod sound | a Run is "blocked pending producer result"; unproven (SOUND-AGENT-LAB) |

### 2.7 Characters and animation

| Tool | What | Limits |
|---|---|---|
| Skinned writer: `build_model.py`, `xmodel.py`, `xsurface.py` (ext `tools-source/iw7-skinned-writer`) | glb from Blender -> IW7 skinned xmodel | TI merged 2026-11-10; CC "side branches" |
| Hero kit: `ship_heroes.py`, `hero_material.py`, `Run-OutfitProof.ps1` | hero outfits, materials, LOD chain | outfits rejected by reviewers (2 to 4 of 10) |
| Zombie kit: `fit_zombie.py`, `run_zombie.py`, `clone_scriptable.py` (Blender) | AI mesh -> 6 zombie parts + 5 gibs | never built into a zone (CC) |
| glTF/BO3 prop import `t7_env_port.py`, `iw7_model_author.py`; `iw7_model_to_glb.py` | glb/BO3 -> rigid IW7 model; back to glb | collision for imported models missing |
| xanim codec `iw7_xanim_codec.py`, `iw7_xanim_layout.py`; `t7_vm_retarget.py` | read/write IW7 animations (all 4,029 Spaceland read, round trip within 0.004 deg); retarget BO3 viewmodel anims | no Blender/glTF path; C1 running |
| Rig tools (`plan_rig_chain.py`...), model lab, rigid-mesh pipeline, model runtime lab | rig chains, authored rigid model into fastfile, show a model in running game | rigid model drawn in game 7 Oct |

---

## 3. The specific needs

Format: **Docs say / Proven (date, evidence) / Missing.** "NS" = not stated.

### (a) Custom static geometry and collision in a custom map; collision for imported models

- **Docs say.** Station Zero's world is generated: "render geometry, Havok collision, bfx navmesh and entities produced by code (`station_zero.py` + `mapgen.py`)", compiled by ZoneTool `-iwzcompile` against the cp_zmb world as template for sun, sky, light grid, reflection probes (ICM:What it is). Collision = Havok hk_2014 compressed mesh, scale 1/32, tag 382 solid; navmesh = bfx NavGraph 0x2B (S2CTX:Proven facts). Decor = 38 stock models as `script_model` map entities; the larger get an invisible collision box and their navmesh cells are removed (ICM:Decor). Static models (class 1) and primary lights (class 4) "not yet generated" as of 6 Nov (S2CTX); a branch documents "static model collision scope" (TI:x64-zt-iwz-smodels, unmerged).
- **Proven.** rc1 map loads, player stands on generated floor, zombies chase on generated navmesh (nearest 788 -> 47), complete walls and ceilings via a generated conservative Umbra tome (ICM:Proven in the engine, local private session, run `IW7-Runtime/iwz-rc0`). Havok collision for generated geometry: used by that run (player walks, spawns on z 0). Kino: collision approximated by cloning stock collision brushmodels streamed near players (KINO:Collision).
- **Missing.** Detail level (264 surfaces vs 10,760; reviewers ~5 of 10; CC). **Collision for imported models: Missing; A2 open** (CC Models row, A2). Real visibility culling: the tome is "one tile, one cell listing every object, each object's bounds the whole scene (Umbra never culls; the GPU still frustum culls)" (ICM:Visibility) - so everything is drawn; N5 open. Kino clone-collision limits: ~1,480 `clonebrushmodeltoscriptmodel` calls in one match = fatal "HIE: 506609a5"; about 240 extra visible entities above Spaceland baseline drop the game; `hide()` unlinks clones; one GSC function of 4,000 literal rows does not load (split into 600); GSC child-variable pool is shared and ran out (KINO:Findings). The compiler (needed for any world geometry) is only on branches (N1 running).

### (b) Props reuse from shipped maps / prefab rooms

- **Docs say.** worldkit `extract` lifts everything in a box as a prefab (props, lights, entities, surface meshes, relative coordinates); `place` puts it anywhere rotated (side/CCD; CC piece 1). Kit import links stock models of other zones into a usermap, "prove drawn in engine" (TI). Station Zero already uses 38 stock models as script_model decor (ICM). Catalogue of stock models: 13,113 models with sizes (CC).
- **Proven.** Prefab of the spawn plaza lifted: 483 props, 437 surfaces, 36 lights, 69 entities (CC piece 1, merged 10 Nov). Live hide/restore of 792 props for the author only (CC). 
- **Missing.** "Rooms reused from shipped maps (a prefab can be lifted; **the generator cannot place it yet**)" (CC New maps row); N3 queued (props first, then surfaces with collision). Baking a prefab to 4-10 models with collision: an "open measurement", not done (side/CCD). Free entity slots per shipped map late round: not measured (side/CCD). Props as script_models hit the entity limit (KINO; MAXIS budget "Entities < 1800 of 2048"); static models need the build route.

### (c) Lights, darkness, reflection, fog/vision

- **Docs say.** rc1 lighting: world surfaces lightmapped against the TEMPLATE cp_zmb atlas, each room's vertices pointing at one measured texel (per-room texels raised mean frame luma 0.11 -> 0.34-0.59); models (decor, perks, characters) lit by the light grid (SH probes, 29 halves each); generator writes `lighting.txt` (ambient + one box per room) and `-iwzcompile` replaces probes in those boxes (1838 / 2186 probes for Station Zero) (ICM:Lighting). "Lighting is ambient only (no local primary lights or baked lightmaps yet)" (ICM:Limits, 6 Nov - superseded in tooling by `bake/lmbake.py`, see below). Bake: ray-traced lightmap + light grid, `lm_measure.py` (TI, merged 10 Nov; CC lists it as side branch). Compiler tip handles "world, tome, light grid, doors, lightmap, darkness" (TI). Darkness: "dark until power, flashlights, light groups" (TI darkness/; `make_vfx_light.py` = effect that carries light). Self-lit fx variants (`fx_variant.py`). Reflection: template reflection probes reused; "neutral probes write the cp_zmb BC6H_UF16 cube array" (TI x64-zt-iwz-doors); reflection probe instances are tome class 5 (ICM).
- **Proven.** rc1 frames mean luma 0.34-0.59 (ICM; frame evidence `iwz-gt2`). Darkness proof fixture ("probe 8: carrier, brightness, kill tests, vision sweeps, last stand") exists on a branch (TI sdk-fx-d12); no pass/fail stated in these docs.
- **Missing / unproven.** Whether baked lightmaps/darkness/self-lit fx work in a built map in game: NS as proven (CC: all "on side branches (being landed)"). Lighting/navigation of changed areas of shipped maps missing (CC; M4 open). Spawned IWZ machine models render dark above Spaceland; `retargetscriptmodellighting` exists in the method table but not at runtime (KINO:Findings). Reflection quality for a custom map: NS. Fog and "vision" (vision sets): NS in these docs. New shaders/post-process: missing (CC piece 7 "to build").

### (d) Scripted doors, purchasable debris, zones/volumes, spawners, pathing/navmesh for zombies

- **Docs say.** `cp_iwz.gsc`: spawn volumes per zone, debris doors (750 / 1000), generator power, four perk machines, three wall buys, Pack-a-Punch, rounds and points (ICM:What it is). Zombies spawn from `<zone>_spawner` structs (`script_noteworthy static`) targeted by `info_volume` spawn volumes; stock interactions reused (S2CTX). Playtest "map contract": zones = stock `spawn_volume` info_volumes; adjacency from door struct pairs + `update_volume_adjacency_by_name`; doors = debris/door interaction structs paired by `target`, `script_area` = zone opened; specials = `brute_hide_org` struct + `dog_spawner` structs (IPT). Kino doors: BO3 door models swinging/sliding with purchase points (KINO). Compiler branches: door brushmodels, trigger volumes with physics shapes (TI).
- **Proven (rc1, local private session).** Zombies spawn and chase on generated navmesh; rounds advance with points (wave 1->2, +600); door purchase opens next zone (`DOOR generator_active=1`); power switch powers perks (`POWER powered_perks=4`) (ICM table). The playtest harness (IPT) can check inv/bounds/isolation/walk/buy/quest/trap/stairs/spawners/cleanup/perf/rounds/routes/climbs; it "reproduces every static rc1 finding" (lint). PaP relay quest + trap contracts exist for v2 (`cp_iwz2.gsc`, `level.iwz_pap_open`, `level.iwz_trap_use`; designed trap values 25 s active / 60 s cooldown / 750 cost).
- **Missing / weak.** Zombie stair/climb problems are a known thread: climb acceptance threshold >= 90 % per case (IPT), probe `g27dw` "solid well steps only (0 of 10 far climbs)", tip g27e "solid well steps off by default" (TI). Navmesh is bfx NavGraph generated by code; offline checks `sz2_navconn.py`/`track_clearance.py`. Triggers and brush entities added to a *shipped* map: missing (CC; their shapes live in compiled zone data, GL:Not verified). Atlas misses places reachable only by trap/teleporter/purchase (ATLAS).

### (e) Perk machines (stock and NEW custom perks: script, machine model, HUD icon, jingle)

- **Docs say / proven.** Stock perk machines on a custom map: four perk machines powered by a generator switch (ICM table, rc1 local run) and playtest `buy` phase checks perks, PaP, wall buys, wheel locations (IPT). Kino relocates retail interaction structs: 8 perks (Jugg -> Tuff 'Nuff, Quick Revive -> Up 'N Atoms, Speed -> Quickies, Double Tap -> Bang Bangs, Mule Kick -> Mule Munchies; Racin' Stripes, Bomb Stoppers, Blue Bolts on spare spots); perk purchase (Tuff 'Nuff) passes in E2E (KINO). Retail perk-machine hooks can be replaced: four shared hooks changed to remove the five-perk limit, with paid Bang Bangs (2000) and Zap (1500) callbacks witnessed (PERKS-REVIVE; private two-client witness).
- **Missing.** **NEW custom perks: not stated anywhere in the docs read** (no script pattern, machine model, HUD icon or jingle recipe). Building blocks that exist elsewhere: rigid model import (glTF/BO3 -> IW7 model, "authored rigid model drawn in the game 7 Oct", CC), 2D materials/images into a mod zone (Maxis art in `mod.ff`, MAXIS), stock perk jingles are rows 21-30 of the jukebox table (DJ-PLAYLIST), `level.attachmentmap_*` style data hooking and `replacefunc` of retail functions (BWW). Machine models spawned above/in a custom map render dark unless the light grid covers them (KINO). Custom perk purchases by a *real* player: NOT_PROVEN even for Kino (KINO:NOT_PROVEN).

### (f) Wall weapons, mystery box, Pack-a-Punch, PaP camos (custom materials, animated/scrolling/emissive, new shaders)

- **Docs say / proven.** rc1: three wall buys + PaP (stock structs). Kino: 11 wall buys (host weapons), 9 magic wheels on BO3 box spots, PaP after power (KINO). v2: PaP behind a relay quest with shutter (`level.iwz_pap_open`) (IPT). Wheel: BO3 weapons added to `level.magic_weapons`, `level.all_magic_weapons` and each wheel's list; PaP via `level.pap["<raw>"]`, `level.attachmentmap_basetounique`, `replacefunc` on `utility::reassign_weapon_name` and `getattachmenttype` (BWW:Magic wheel and Pack-a-Punch). Real cp_zmb machine run by a test client: first PaP + repack with the map's camos PASS (Ray Gun `+camo1`, repack `+camo4`; Thundergun) (BWW 2026-11-08). Camos: retail `get_pap_camo` picks the map's camo (Spaceland camo01/04, Rave 204/205, Shaolin 92/93, Attack 211/212, Beast 32/34); name suffix is the camoTable weapon index (`+camo1`); ported materials built from the 2-UV camo template with the BO3 camo mask; meshes gain a second UV set (`iw7_xsurface_uv2.py`); camo01/camo04 witnessed in game on Ray Gun, DG-2, Thundergun, Mark II. Emissive: "BO3 emissive materials use the stock IW7 emissive weapon technique and BO3 glass the stock Headcutter glass technique" (`t7_material_pack.py --emissive-template --blend-template`); an opaque glass had hidden the lit tube until fixed.
- **Missing.** Which PaP camo a *usermap* gets: NS. Custom camo textures for new maps: NS (camo is a camoTable index). **Animated/scrolling materials: NS.** **New shaders/techsets: Missing** ("looks are stock techniques with custom textures"; shaders copied as compiled bytes; CC). Per-map PaP for other maps' machines: "covered by naming chain only; no client or owner test" (BWW). PaP of generic attachments at the real machine for generated attachments: NOT_PROVEN (BWW 2026-11-08 generated catalog). Magic wheel purchase by a real player: NOT_PROVEN (KINO).

### (g) Custom weapons with special behaviour (what BWW proved)

- **Mechanics proven (agent witness, private test dedicated, cp_zmb).** Added weapon assets (never replacing IWZ ones): Ray Gun `iw7_raygun_zm` + PaP (`iw7_raygun_zm_pap1+rgpap1/2`; projectile 4198 vs 3198 units/s, zombie killed); Thundergun `zm_weap_thundergun`: on fire, fling (immediate ragdoll kill) in a fling cylinder, knockdown/stun beyond, ground effect; bosses/specials excluded; PROVEN_LOCAL: 7 zombies, 5 dead, one stunned at 901 u, one untouched at 1092 (2026-11-07); DG-2 chain (`_zm_weap_tesla`/lightning_chain): chain starts at tracked impact point when the victim is already dead; 6 placed zombies killed (2026-11-07), 4 dead `chained=5` after rename (2026-11-08); Ray Gun Mark II: piercing via `magicbullet` re-fire from just past each zombie hit (up to 4, 6 upgraded), burst fixed by ZoneTool `burstCount` (clip 21->18 per pull); bolt stays ~250 ms (2026-11-08).
- **Scripts.** `src/bo3wpn/paris_bo3wpn.gsc` (dedicated-only): `bo3wpn_catalog()` (`probe alias=weapon:pack-a-punch weapon:pap1 attachment:pap2 attachment`), behaviour lines `weapon|BO3 script namespace|tuning|effects|sounds`; module activates only if the weapon's probe alias exists (`soundexists` is safe without the mod). Behaviour witness `Test-WeaponVisual.ps1 -Module -Horde N` with trace `paris_bo3wpn_trace`.
- **Projectiles/fx/sounds.** Projectile comes from the weapon definition (an attachment cannot override it); BO3 fx read from the held zone (`t7_fx_read.py`) and written as IW7 particle systems (`t7_fx_to_iw7.py`; all 12 Thundergun fx build, heat-distortion ring skipped, no distortion conversion); sounds into `mod.sabl/.sabs` via `t7_weapon_sound.py` (audible playback not proven); DG-2 rail fx tied to notetrack `switch_on`, BO3 also replays it every 8-12 s from client script "which IW7 assets cannot do".
- **Limits recorded.** Attachments only ADD models; a PaP look change needs a definition swap (`_pap1`) (BWW); `getmuzzlepos()` on a player crashed the server (retail calls it on AI only); mod zone is global and must not name assets only one map carries; LOD order fix needed (BO3 least detailed first); weapon naming must be `iw7_<name without underscores>_zm` and raw name must not collide (Ray Gun vs Mark II). CC: "each new behaviour family needs a hand-written script (only Thundergun push and DG-2 chain exist): charge shots, dual wield, model scaling are unsolved". WWC risks: 1 charge shots, 2 dual wield of different weapons, 3 model scale, 4 hero meter, 5 effects, 6 streamed meshes; class B 19 weapons, class C 1 (Gauntlet); owner excluded hero weapons.
- **Not proven.** Sound audible; DG-2 rail visual at reload; world-model LODs in game; deployment; owner acceptance; PaP e2e with generated attachments.

### (h) New enemy types: porting vs new; skinned characters; custom animation; asm; AI types; script-driven zombies (KINO)

- **Porting retail enemies (EP).** Rhino on Spaceland: owner confirmed pursuit/textures/attack animation 2 Oct, then parked. Slasher: protected join, textured spawn/pursuit, corrected Scriptable states, retail death/slot cleanup; contact damage, isolated audio/complete FX, owner acceptance open. Method needs: exact agent definition row, registration script, behavior tree, ASM, animclass, animation tree, XModel/XSurface/materials/techsets/shaders/images, scripts (Rhino: 203 client assets, 27 scriptfiles, 13 live behaviour callbacks), VO, spawn-policy adaptation (EP). Enemy packs per enemy in `ops/enemy-ports`. These ports are *into Spaceland (cp_zmb)*; usage in a usermap: NS. Spaceland already registers `zombie_clown` but suppresses it (`level.no_clown_spawn`). 
- **Script-driven zombies (KINO).** Each ordinary zombie taken over: behavior tree and ASM transitions suspended, retail `*_loop`/`attack_stand` states kept, movement by script along a nav graph "(IW7 agents snap back to the host navmesh otherwise)"; E2E 20/20 including zombie pursuit with anti-stuck rules; a flow-field per player (per-zombie recompute made the dedicated stop answering `getinfo`; one shared flow thread passes).
- **New enemy.** Missing (CC: needs animation + model rows). Needed pieces: skinned writer (exists, branch/merge status contradicted, section 6), zombie kit (never built into a zone), animation path glTF->xanim (C1 running), actor kit (C3 open). Behaviour trees/animclasses cannot be authored (no on-disk form; copied live from the game) (CC). The `asm`: reused (donor scripts `scripts/asm/...` lists exist in `ops/enemy-ports`); authoring asm = NS/missing. AI types: only retail types or script-driven models; boss arenas and quest services Missing (CC).
- **Animation.** Read/write codec for all 4,029 Spaceland anims (<=0.004 deg); retargeted BO3 view-model anims proven; original 4-key clip survived a zone round trip offline (never seen playing); "an animation of ours playing on a character in the game" missing.

### (i) Zombie count above 24

- **What the capacity48 archive did (CAPACITY48.md).** Optional capacity profile: 64 native agent records = ceiling of 48 living ordinary zombies, remaining records for specials/companions/reservations; moves both agent pools, character info and work tables, sentients, corpse indices and the map-entity boundary together; 64 unique agent records, 82 character slots, map boundary 98; retains 8 player corpses + 8 agent corpses; needs a MATCHING client (`paris_capacity=64-v2`, executables `iw7-paris48.exe`/launcher; incompatible clients get an English restart/update message; stock clients rejected); 21 entity-state client-number descriptors and five agent-delta index widths set to seven bits. Source defaults stay `scr_zombie_maxagents=24`, `paris_enemy_capacity=0`. Qualification claimed: paired standard-client 64-v2 matrix on all five maps (48 ordinary + 2 retail specials, 3 cycles of 8 deaths/replacements; Spaceland 108 samples/300 s, Beast 112/120 s, Rave 105/300 s, Disco 110/120 s, Attack 109/120 s; retains 75/78 canonical slots; server median 20 Hz; client present callbacks 30.30 -> 30.31/s, peak private memory 8810.9 -> 8863.3 MiB).
- **The recorded regression (2026-10-20).** Owner: "Extra zombies beyond 24 are invisible while hits, sound and red crosshair remain" and a dedicated crash after about one minute (C0000005 at 140D75BD0, reads 10100000008 through an invalid pointer; `CauseProven: false`, `ExtraActorsVisible: false`, `VisibilityPreviouslyQualified: false`; `docs/deployments/2026-10-20-capacity48-owner-regression.json`). Main restored to 24 native profile; Desktop 48 shortcut disabled; `config/capacity48-release.json` State "suspended", Issue 324, refuses production activation. Earlier finite checks "did not establish actual extra-agent visibility or natural gameplay safety". Next steps recorded: private render/model/animation observation beyond 24, fix the invalid pointer, then natural-round/death/reuse/rotation/performance qualification.
- **Limits that exist (RA, CAPACITY48, KINO, MAXIS).** Retail allocation 24 agents; engine globals 18 (players), 42 (character total), 58 (map entities begin), `0x7FE` end; agent indexing subtracts 18; two serialization loops with hardcoded 42 x 64-byte entries; agent-reference restore rejects index above 24; client loops/lookup reject index >= 42 (RA:Proven engine constraints) -> "a server-only change does not establish that stock clients will render additional agents"; earlier 64-agent experiment crashed at startup on `g_entities[58]`; entity/budget: MAXIS budget "Entities < 1800 of 2048"; KINO: ~240 extra visible entities above Spaceland baseline drop the game; network: reliable ring 128 entries shared by client dvars and chat, remote reliable overflow kicks (SERVER-COMMAND-OVERFLOW); AGENTS: slots 4-7 fail on real clients (LUI error per frame, 31 -> 15 fps; PLAYERS8-AUDIT 2026-11-02).
- **Relevant tags/branches.** Only accepted tag: `accepted/2026-10-01-server-commands`; also `dc-beta-2026-10-06`; archived `archive/codex/capacity48-natural-observation`. AGENTS.md: "No Capacity48/64, custom Rhino or accepted tag follows" the eight-player candidate. Unmerged: components `codex/capacity48-natural-repair` (12 ahead), `codex/automatic-capacity-profile` (22 ahead); iw7-mod `client-zombie-capacity-standard-a99` (82 ahead); server `codex/capacity48-natural-observation` (5 ahead) (TI). Owner queue mentions "enemies and capacity 78" as a build sub-thread (side/OQ); a 78-zombie capacity is not specified in the ten docs. **Today: ordinary Main runs 24.** Custom-map capacity above 24: NS.

### (j) Custom sounds/music/voice in a map; delivery to players

- **Docs say / proven.** A usermap may carry `<name>.sabl` / `<name>.sabs` (redirected into `usermaps\<name>\`) (USERMAPS contract). Sound bank writer for usermaps merged 10 Nov (TI: `iw7_sab.py`, `iwz_audio_bank.py`); map audio with 25 emitters and hidden-song module (TI). Stage2: usermap sound route from a `soundbank` csv row; hidden-song EE module (S2CTX). Mods: three files `mod.ff/.sabl/.sabs` only (BWW). Proven: Abracadavre BO3 song in a mod bank (`kino_mus_abracadavre`, `soundexists` true, alias played in E2E) (KINO); DJ songs in `mod.sabl/.sabs` **owner-accepted 2026-11-09** ("works perfectly", STATE); teddy song finale deployed; Afterlife/YE with `.mute` mix `paris_music_off`.
- **Constraints.** A dedicated server returns 0 for `lookupsoundlength` of mod-bank sounds, so lengths come from a table column (DJ-PLAYLIST); stock banks are FLAC only (rates 12-48 kHz); stock DJ masters -12 LUFS stereo, LRA 1-3 LU; mono files measure ~3.5 dB quieter in game (game sums channels) so store dual-mono; `primed` type = head in `.sabl`, rest streams from `.sabs`; sounds played in space cannot be stopped; players joining during a song do not hear it (NEIL-FINALE); weapon sound "never measured as audible" (CC); sound capture tool = `Capture-ProcessAudio.ps1` (merged). Voice lines (VO) and character voice for a custom actor: NS (character VO for stock heroes uses `vo_prefix` p1_-p4_ aliases; CHARACTER-VOICE). Voice chat (players' mics) never worked (relay retired; replacement untested in game; STATE).
- **Delivery.** Mod route works via `sv_wwwBaseUrl` (below, (o)). Usermap route: see (o).

### (k) Custom FX

- **Docs say.** BO3 fx converted to IW7 vfx (`t7_fx_read.py`, `t7_fx_to_iw7.py`, `t7_fx_material_pack.py`); `iw7_vfx.py` reads/writes IW7 vfx; stock ambient fx placed in a usermap (`fx_import.py`, `fx_place.py`, `fx_variant.py` self-lit, `fx_proof.py`); light-carrying effect for dark maps (`make_vfx_light.py`); gamelab `fx` step reports whether it loaded (client only).
- **Proven.** Thundergun muzzle blast and shockwave ring in game (BWW 2026-11-07); Ray Gun fx in mod (4.0 MiB mod.ff with BO3 FX at 512 px). Map fx in a usermap: tools "merged 10 Nov" (TI); in-game proof of map fx: NS in these docs.
- **Missing.** Authoring brand-new fx from scratch (not conversion): NS. Heat-distortion fx not convertible. Fx loading checks: `FX_NOT_LOADED` automatic gamelab finding.

### (l) Teleporters / moving platforms / script_models moving players / vehicles / ziplines in IW7 GSC

- **Teleporter.** Kino: "stage pad (after power) to the projection room with Pack-a-Punch for 30 s, IWZ tube effect, 20 % bonus room with a power-up"; E2E teleporter + return pass (KINO). Script-only; players moved by script.
- **Moving script_models/platforms.** `moveto` used in module code (`paris_kino.gsc`, `paris_doom.gsc`, `paris_boss_setup.gsc`); Kino clone-collision pool moves clones near players (limits above). Train kit: moving train set piece with proof and perf scripts (`train_proof.py`, `train_perf.py`, `fixtures/train_kit.gsc`, merged 10 Nov per TI); fixture holds player at view points with `playerlinkto` and unlinks for the walk (TI branch `codex/iwzmap-hero-train`).
- **Players riding.** `paris_boss_setup.gsc` uses `playerlinkto( level.boat_vehicle, ...)` for the Rave boat (stock vehicle). Stock map ents include `info_vehicle_node` (124 consumed at load in cp_zmb, GL). Custom vehicles: NS. Ziplines: only zipline traversal ASM scripts for Rave/Shaolin agents appear in `ops/enemy-ports/*scriptfiles.txt`; player ziplines in GSC: NS.
- **Missing.** None of this is accounted in CC readiness; "the train" proof is a fixture, not owner-accepted. Moving geometry with collision in a built map: NS (compiler "door brushmodels" branch only).

### (m) UI: server-drawn HUD, LUI/Lua route, Tab/scoreboard

- **Server-drawn (works).** Retail text HudElems and two stock materials; no download; limit **24 elements per player** (CC; MAXIS budget "HudElems we own per player <= 24"); each panel = 8 HudElems (title, 6 rows, footer); rows 44 chars, 6 rows, incoming message cap 264; vote uses 4 temp elements (or 11-12 in the virtual-cursor vote); every distinct text costs an engine string; client-dvar writes <= 24 per 10 s; reliable ring 128 entries shared with chat; payload ~1 KB; entities < 1800 of 2048 (UI.md, MAXIS.md). IW7 `min` returns float and `getsubstr` needs ints (UI.md). Maxis terminal deployed on both servers 2026-11-08, but "No in-game test yet" for startup with this set, owner gameplay (MAXIS Status).
- **LUI/Lua route.** Mod `mod.ff` can ship `ui_scripts/<folder>/__init__.lua` LuaFile assets (iw7-mod PR #697, merged to develop 30 Sep 2026, proven in HUD lab with a downloaded FF; MAXIS). **Who can load it today:** clients built from `develop` (the owner's native build / clients this project builds); the official updater ships `main` v1.1.0 (26 Sep) which does not load zone Lua; a release request is "an outward action left to the owner" and nothing is posted to Aurora (side/OQ). A client-side protocol exists: server `setclientdvar` -> `maxis_*` dvars; client -> server only through four reused retail `NotifyServer` names (`intel_tab`, `map_select`, `boss_set`, `boss_reset`; MAXIS Protocol). Lua HUD (BO3 style): 359 offline tests, one real run with a wrong layout (CC). Rendering/clicks of LUI not done (MAXIS "Not done").
- **Tab/scoreboard.** NS in the ten docs. Related facts: legacy portraits/scoreboard/EoG are four rows; eight-slot play accepted with four-row legacy portraits/scoreboard/EoG (AGENTS.md owner decision); players 5-8 on a stock client hit a retail LUI error per frame (PLAYERS8-AUDIT). Customising Tab: Missing / not documented.
- **UI as data:** U1 running (none today; UI review still needs eyes).

### (n) Third-person camera and playing arbitrary animations on players (emotes)

- **Docs say.** "Third person on real players unproven" (CC Models row). "An animation of ours playing on a character in the game" missing; "Full-body, additive and root-motion authoring" missing (CC Animations). Weapon-hand animations retargeted and played through real input (CC). `setviewmodel` is used by a fixture (tests/fixtures/bo3wpn_visual.gsc). The client ignores a server `setclientdvar cg_fov` (BWW). Nothing in the ten docs describes a third-person camera, emote wheel, or arbitrary player animation playback. (The owner's emote request lives in `side` brief, not in these docs; C1/C2 are its prerequisite.) Status: **NS / Missing**.

### (o) Auto-download of custom map/mod to players; size limits

- **Mods (works).** Official client compares `mod_hash`/`sabl_hash`/`sabs_hash` from `getinfo` with `mods/<mod>/mod.*`; downloads missing/different from `<sv_wwwBaseUrl>/<fs_game>/mod.<ext>`; reconnects (with `vid_restart`) (CCOMP table; KINO). Hashes are CRC32 hex. Proven: loopback auto-download byte-identical (KINO `kino-autodl-b`); official client downloaded the BO3 weapon mod on a private server (6 Nov); Main runs `fs_game mods/paris` with Canada OVH host `http://<download-host>:8767` (TCP 8767). Only three files: no `.pak`, `.exe`, `.dll`, `.zip`, arbitrary GSC (CCOMP). One mod zone `mod` and one bank only (BWW).
- **Usermaps.** Loader exists upstream (PR 701/705, client half installed 2026-10-17): `usermaps/<name>/<name>.ff`, optional `_load.ff`, `.pak`, `.sabl`, `.sabs`, `<name>_art.ff`, `.arena`; delivery for **party joins**; "a dedicated `connect` download path is not shown", so "installs itself" is **unproven for a dedicated server** (CCOMP, USERMAPS; CC N6 open; CC New maps: "Delivery of a map by a dedicated server to players is unproven"). MAX_ARENAS 64 shared with stock (silent loss). Station Zero package rc1 hashes in `IW7-Runtime/iwz-release/cp_iwz-rc1/manifest.json`; manual copy of `usermaps/cp_iwz/` + a fixed `ui_scripts/Usermaps/__init__.lua` needed today, because without the fixed script the whole zombies map list fails while `cp_iwz` is installed (ICM:Play it locally; bug fixed in our iw7-mod fork branch `fix/usermaps-cp-map-stats`, not upstream).
- **Size/other limits.** Cloudflare Pages 25 MiB file limit is below Kino `mod.ff` ~164 MB / `mod.sabs` ~45 MB (KINO); Canada OVH raw-socket server 5.4-8.6 MB/s from Paris (87 ms RTT) (NEIL-FINALE); current mod 29.9 MB combined for BO3 weapons (BWW) and DJ songs 73.3 MB; Spaceland zone file 196 MB (side/CCD); transformed-Spaceland patch about 115 MB before compression (side/CCD). **A failed download terminates the official client** (async throw; fork fix not upstream) (KINO, CCOMP). Server caches advertised hashes per pathname: replacement needs controlled restart or versioned mod paths. Downloaded files are never deleted client-side (cache cleanup branches unmerged). Station Zero final size: NS in the ten docs.

### (p) Build time of the map and what dominates

- **Docs say.** "One build of the custom map: bake 4 to 8 minutes, then zone build about 14 minutes"; "a build takes about 20 minutes" (CC). N4 target: "from about 20 minutes to minutes (bake only what changed, zone only what changed)"; proof = "measured time for a one-room change". So the zone build (about 14 of about 20 min) dominates; the docs do **not** say why (cause NS). File checks 2 s; weapon zone build 7 s; engine rebuild 70 s for contrast (DK, ENGINELAB). Build runs under the shared Build resource lease (exclusive build slot; `bench` sessions cannot run during the compile).
- Also relevant: a game session costs about 2 min before the first question (GL: 1,340 launches recorded, 79 % refused for a busy slot, 102 builds launched on average 13.1 times, one build 195 times) - the reason for gamelab plans.

---

## 4. Anything flagged buggy, slow, blind or unproven

**Buggy / known defects**
- Join stall: about 1 in 3 lab joins stall while the client loads; not a frozen thread; netlab retry works (DP hole 11, CC S4).
- Capacity48 regression 2026-10-20: invisible zombies beyond 24, dedicated C0000005 at 140D75BD0, cause unproven; production activation refused by config (CAPACITY48.md).
- A failed mod/usermap download terminates the official client (KINO, CCOMP, BWW); fix only in our fork.
- Usermap list bug: whole zombies map list fails while `cp_iwz` is installed unless the fixed `Usermaps` script/client fix is present (ICM, BUGS).
- Kino engine limits: HIE 506609a5 fatal after ~1,480 clone calls; ~240 extra visible entities drop the game; GSC child-variable pool exhausted; 4,000-row literal function does not load (KINO).
- Thundergun first fire crashed dedicated (`getmuzzlepos()` on a player) - fixed; DG-2 lob (`iProjectileSpeedUp` 500 copied from zapper template) - fixed in ext (BWW).
- Station Zero zombie climbing: probe g27dw "0 of 10 far climbs", well steps solid vs not (TI); climb acceptance >= 90 % per case required (IPT).
- Slots 4-7 fail on stock clients: one retail LUI error per frame, 31 -> ~15 fps (PLAYERS8-AUDIT 2026-11-02).
- Perk-machine and other IWZ machine models render dark above Spaceland; `retargetscriptmodellighting` absent at runtime (KINO).
- Three asset-tool checks and one components check are always red for unrelated reasons (DP hole 9). The client cannot be built from the server repo's pinned inputs (DP hole 1, ENGINELAB).
- Retail `min` returns float; `getsubstr` needs int (UI.md); engine bots never finish a weapon switch; test clients skip player connect setup (KINO, GL).
- Last-stand `getweaponbasename` error for bots (harness-only, BWW).
- Spaceland audit false after a Main bank delta (CAPACITY48).

**Slow**
- Map build ~20 min (bake 4-8 + zone ~14) (CC; N4 open). Whole-map atlas sweep: 3000 points = ~75 plans, 10 h (ATLAS). Client session ~9 GB and ~2 min launch overhead (GL). Compiler/engine build exclusive slot (ENGINELAB). Canada mod host 5.4-8.6 MB/s (NEIL-FINALE). A mod download of Kino-size is 164 MB.

**Blind (cannot be measured today)**
- Which object a pixel shows (depth capture S1); UI as data (U1); sound measured from the game (side branch, weapons "never measured as audible"); single slow frames (S2); GPU time per pass (DP J); no network counters beyond packet level (DP hole 6); no engine names for most functions (588 of 50,095); frames judged by reviewers, not by tool, for "looks right" (GL, ATLAS); whether a client reads the loose entity file (GL, CC); free entity slots on shipped maps (side/CCD); Tab/scoreboard layout.

**Unproven**
- Delivery of a usermap by a dedicated server (N6); "installs itself" for custom maps.
- Everything owner-gameplay: "nothing below is accepted except where said" (CC); Maxis UI startup/LUI; BO3 weapon sounds audible; DG-2 rail visual; world-model LODs; purchases by a real player in Kino (perk/door/wheel/PaP/wall buy); round pacing at depth; multiplayer; full-match performance (KINO NOT_PROVEN).
- Map generator v2, lightmap bake, darkness, effects, art, audio, catalogue, kit import: built, mostly on branches, not proven in game as a set (CC).
- Zombie kit never built into a zone; hero outfits rejected by reviewers (2 to 4 of 10); map reviewer score ~5 of 10.
- Voice chat never worked (relay retired; replacement untested in game) (STATE).
- Headless can't run usermaps; map playtest needs a client and base-game staging (GL, IPT).
- DJ: "songs have no volume except one" report on Main after acceptance (side/OQ) - cause unknown, opener nearly constant; LUI terminal still lists `.revive/.drop/.mule` on cp_iwz until a `mod.ff` rebuild (MOD:Known gap).

---

## 5. The modules system (MOD, config/modules.json, src/custom_scripts/cp/paris_modules.gsc)

**What a module is.** A separately switchable server feature, "separate features, not dependency-free files: transfer the catalog, common core, needed scripts/native components and supported map profile together" (MOD).

**Packaging.**
- `config/modules.json` = deployment catalog: `Schema`, `Profile: "server-only"`, `CoreScripts` (`paris_modules.gsc`, `paris_commands.gsc`, `paris_country.gsc`, `paris_diagnostics.gsc`, `paris_stats.gsc`, `paris_cinematic.gsc`, `paris_players8.gsc`) and `Modules[]` each with `Id`, `Dvar` (`paris_mod_<id>`), `Default` (1/0), `Scripts[]`, `Native[]`, `ClientDownload` (bool), `Parked` (bool). Example: doom -> `paris_doom.gsc` + `paris_doom.cpp/.hpp`.
- Module ids (MOD table): bank, afk, counter, map_vote, rush, directors_cut, max_ammo, announcements, loadout, spawn_blessing, country, cleanup, ui, identity, voice (retired in source), afterlife, rhino (parked, cannot enable). Plus doom, directors_cut also owns `paris_boss_setup.gsc` per the JSON.
- `config/server_modules.cfg` = reviewed defaults (`set paris_mod_<id> 1`), plus per-module tunables (e.g. `paris_afterlife_seconds 152`, `paris_ui_art 1`, `paris_rhino_*` 0). Local effective overrides are ignored `runtime/server_modules.cfg`. `config/canonical-budget.json` records 22 catalog scripts, **DynamicIdentifierCount 1130** and `RequiredBeastFreeSlots 64` (each new script/identifier must keep Beast above 64 free canonical slots; litmus: "the compiled catalog goes from 1134 to 1130 identifier-shaped strings"; helper tokens in `config/canonical-helper-tokens.json`, `canonical-private-functions.json`). `config/server-mod.json` records `FsGame mods/paris`, `WwwBaseUrl` and SHA-256 of the three mod files.
- The registry (`paris_modules.gsc`) offers `enabled(id)` / `available(id)`; HUD and `.mods` pages show configured vs available states; "Rush availability is separate from actual match activation".

**Switches.**
- Console: `set paris_mod_<id> 0|1` (temporary unless persisted). Admin: `ops/Modules.ps1 -Action List|Enable|Disable -Module <id> [-ApplyNow]` (verifies UDP and process identity, queues an allowlisted dvar command; success of queue is not behaviour acknowledgement). Without `-ApplyNow` saved for next managed deployment. Public `.mods` never changes settings; owner-only persisted switches (AGENTS.md: "owner-only persisted switches").
- A disabled module stays loaded for shared GSC linkage; disabling stops behaviour only. Changes to match-level features (Director's Cut) apply next match.

**Per-map feature profile (what a map should follow).** `paris_modules.gsc` owns a data-driven per-map list of feature ids that are OFF on a map: code default for `cp_iwz` = `directors_cut|bank|rush|max_ammo|loadout|cleanup|announcements|doom|boss_setup|revive` (`boss_setup` and `revive` are profile ids, not registered modules); other maps' default empty; ops override `paris_map_disable_<mapname>` (nonempty replaces; `none` clears) set in config before the map loads; `enabled()`/`available()` false for an excluded id; stored `paris_mod_*` never written; each excluded module checks the profile before any `replacefunc`, thread or storage access; players get one EN/FR/ES reply "Not available on this map." for excluded commands; `.help`/HUD PLAY/BANK tabs/arrival card omit them; `.mods` shows "Off on this map"; `afterlife` stays on (`.mute` works everywhere, NEIL song/DJ install only on Spaceland). Tests: `tests/ops/map_profile_model.cjs`, `ops/Test-MapProfile.ps1` + `tests/fixtures/map_profile.gsc` (private dedicated, bot; cp_iwz loaded 15/15, cp_zmb 16/16, per MODULES/STATE).

**How to make map features follow it.** (derived, not stated as such) A Station Zero feature = (1) a GSC script listed in `Scripts[]` of a catalog entry with its own `paris_mod_<id>` dvar and default, gated at the top of `main`/`init` by `enabled(id)` and the map profile before any `replacefunc`/thread; (2) optional `Native[]`; (3) `ClientDownload` true only if it needs `mod.ff` assets; (4) entry in `paris_map_disable_*` where it must be off on other maps; (5) a source model test + a private dedicated fixture; (6) record in the canonical budget (Beast free-slot floor 64) and `.mods`/localization (EN/FR/ES; MAXIS records a 591-string localization model; `config/localization.json` exists). Note the Station Zero level script `cp_iwz.gsc`/`cp_iwz2.gsc` lives in the SDK generator, not in this catalog (ICM, S2CTX); wiring map-local logic into the module registry is not described in the docs.
- Related precedents of "optional content via a probe": BO3 weapons module activates only if its probe alias exists in the loaded mod (BWW); Kino is inert unless `fs_game mods/kino`, `cp_zmb` and `paris_kino 1` (KINO); Maxis art ignored without the mod (`paris_ui_art`).

---

## 6. Inconsistencies between the docs (do not trust either blindly)

1. TI says the generator v2, bake, darkness, fx, art, audio, catalogue, kit import, skinned writer, zombie kit, train kit, worldkit, entity overlay and live world editor are **merged 2026-11-10**; TI's own "Largest risks" and "Unmerged work" sections (earlier snapshot) and CC's readiness table still call them side branches "being landed 10 Nov". The map compiler (`-iwzcompile`) is unmerged in both.
2. CC says 29 packages; the brief said 26.
3. ICM (6 Nov rc1) says lighting is ambient only; later tooling (bake, darkness) exists but its in-game proof as part of a built map is NS.
4. USERMAPS (27 Oct) says nothing was launched and the producer is absent; CCOMP "2026-10-27 correction" and ICM show a producer exists and a usermap loads (rc1) but dedicated-server delivery is still unproven.
5. DK row 55 and IPT use `-GameRoot <base game>` while AGENTS.md rule 2 says never test in the owner's game folder (benches); headless cannot take usermaps; usermap gamelab plans go through the client runner with `-UsermapDir`.
6. MODULES gives 13, 16 and 17 deployed scripts in different dated sections and PLAYERS8-AUDIT says 21; the current catalog (config/canonical-budget.json) lists 22 scripts, 1130 identifiers.
7. Capacity48: STATE has both "active on Main" and "suspended" entries (2026-10-20 sequence); the release JSON says suspended.
