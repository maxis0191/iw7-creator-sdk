# Station Zero: from the nine-zone release candidate to the bible's map (22 Nov 2026)

State: the nine-zone map (`station_zero2.py`, builds g27*) is a playable release candidate
([STATION-ZERO-G27J.md](STATION-ZERO-G27J.md), RC3 in progress). The bible (`docs/station-zero/`) describes a larger map:
19 zones, the Terminus quest, four wonder weapons, two new enemies, Tab pages, camos, emotes. This page says what does not
exist yet, what each piece needs from the engine and the tools, and the order. Every line is real engine or map work; no
script stand-in counts as a piece done.

## One line, not two

Two generators make a map called cp_iwz: the nine-zone g27 line and the 19-zone scene line (`scenegen.py`,
`scenes/station_zero.json`, with W1 blockout, W2 dressing of four zones, Q1 quest and T1 Capsule Post proven headless on
11 Nov). The g27 line has what the scene line lacks: the train set, darkness, P1 perk machines, FX, audio, the door,
well and stair fixes of 20-22 Nov. Keeping both doubles every fix. Decision: the scene line becomes the one line. The nine
g27 zones map onto bible zones (ticket hall = Fare Hall, platform A = Platform A West/East, maint corridor + generator room
= Converter Hall, control room = Signal Cabin, service tunnel + platform B = Car Barn approach). Step 0 below moves the g27
systems into the scene line and proves the same acceptance suite on it before anything new is built.

> **Changed 24 Nov 2026 (RC5 thread).** The one line is neither generator: it is the **Studio document** of Station Zero
> (`C:\studio`, repository `iw7-studio`), whose base is the emit of `station_zero2.py` and whose layers and new sections carry
> everything built from now on. `scenegen.py` builds nothing more; `scenes/station_zero.json` and `02-WORLD.md` stay the source
> of the 19 zones' bounds, doors and contents, built as Studio sections in the bible's order (the Underpass Arcade first).
> Package 0 below is replaced by "RC5: plan and state" at the end of this page; packages 1 to 7 keep their order.

## Packages (order; each ends in a measured proof)

| # | Piece | Exists today | Engine / tool work it needs | Proof |
|---|---|---|---|---|
| 0 | One line: g27 systems into the scene line (train, darkness with the lit-exposure finding, P1, FX, audio, door tiles shown, stock stairs on every flight, Capsule Post with travelling blowback) | scene line has 19 zones as rooms, Q1, T1 | none new; `szaccept` / `szq` suites run on both | the g27 acceptance suite (doors, economy, wells, stairs, rounds 1-15, post routes and rules, PaP with real keys) passes on the scene map |
| 1 | 19 zones dressed (W3a-d) | 4 zones dressed (W2) | static models without a template twin (TF10, open): until it passes, props stay template donors; prop budget per view (`tome_cull.py`) | three independent reviewers at 7.5 per zone, frame time against the W1 baseline |
| 2 | Terminus quest (Q1) end to end with its hero objects (clocks, levers, board plates: HO1) | Q1 rules on stand-in models (11 Nov, 37/43 then fixed) | authored static models (HO1) through kit import; Terminus collision encoder fix (done 11 Nov) | Q1 plans on the dressed map; reviewers on the hero objects |
| 3 | Wonder weapons (WW1 EXACT CHANGE first, then WW2-4) | none on this map; the mod's ElevenLabs one-shots exist (names in server `ops/audio/elevenlabs_aliases.json`) | a weapon end to end from Blender on a donor animation set (A1), sticking projectile and alternate-mode chain probes (WW2-4) | the seven proofs of `05-WONDER-WEAPONS.md` each |
| 4 | Night Inspector and Rollers (E3, E4) | none | our animation playing in the game (C1, C2: not yet), actor kit hits on script bodies (E1) | `07-ENEMIES.md` proofs; stand-ins are not the feature |
| 5 | Tab pages and HUD (H1 server-drawn, UT Lua) | none | Lua from a map zone (CF1, unreleased upstream) for UT; H1 needs no client change | element budget, three languages, reviewers on frames |
| 6 | Camos (K1), emotes (M0-M4) | none | camo index of a custom map; full-body animation on a player (M0 probe) | `08-CAMOS.md`, `10-EMOTES.md` criteria |
| 7 | Crowd above 24 (CF2) | engine capacity work in the client fork (server `docs/ZOMBIE-CAPACITY.md`) | native agent capacity, already a separate engine package | the seven proofs of `07-ENEMIES.md` 2.5 with real agents |

## Lighting finding that every later zone uses

Stock cp_zmb renders at mean luma 0.175 (p90 0.34) under the same vision values the generated map uses; the generated map
rendered at 0.442 (p90 0.82) because its many evenly spread lights and fill give the auto exposure nothing dark to keep.
Fields the renderer reads and their offsets: `<runtime>\iwz-stage2\darkness\NOTES.md`, 22 Nov. Dressing a zone includes its
light budget against that target.

## RC5: plan and state (thread of 24 Nov 2026, branch `claude/sz-rc5`)

Tool faults and gaps met on the way are written, one entry each, in `C:\studio-data\sz\TOOL-FAULTS.md` (owner of the fixes:
the Studio lead session). Notes of the thread: `C:\studio-data\sz\notes`.

### What Station Zero needs to be accepted, in order

| # | Item | Cause or content known today | Route | What the new tools change | Proof |
|---|---|---|---|---|---|
| S2 | The map as a Studio document, same map | base = generator emit; the build needs Station Zero's recipe (train, kit of cp_disco and cp_final, FX, audio, darkness with its dark bake, P1, nav obstacles) | recipe file `build.json` in the emit, written by `station_zero2.py`; Studio's build reads it | possible once fault F1 is fixed (accepted by the Studio lead, in work); then an edit is seen in 10 to 20 s instead of 403 s + 154 s | emit files equal; full build's row list equal to g27r's; the RC4 suite on the Studio build |
| L1 | Look: lit state reads as "power on", dark state readable without the flashlight | RC4 review items 3, 4: generator room, platform B, stair exits, tunnel end are black without the flashlight; lit exposure was matched to the stock mean | light per zone in the document: key and wash spots, pools, emissive fixtures, a light budget per zone against stock frames; darkness kept (emergency group) | Studio's bake with prop shadows and emissive, `live sync` for a light in 12 s, `view.shot` without the game. Open in the tool: the dark/lit two-state bake is not a Studio notion (part of F1) | three blind reviewers per round, lines fixed before, raw answers kept: 7.5 or more per zone, lit and dark |
| L2 | Look: flashlight pool with a hard edge, treads blown white | RC4 item 1; the flashlight is one spot particle (fov 40, inner 2, brightness 3.5, radius 900) | effect numbers in the recipe (`darkness.vfx`): wider inner cone, lower brightness, halo carries the falloff | each try is a rebuild of nine effects: needs the recipe build | frames at stair B, platform A, ticket hall; reviewers |
| L3 | Look: hard vertical light cuts on the well walls, angular floor patch on platform B | RC4 item 2; to be read on the lightmap (chart seams or a light's culling box) before any change | bake or light volume, at the cause | `tools/bakecompare.py`, `view.shot` | frames well_e x 1060, well_w x 250 to 330 |
| L4 | Look: black blob on the ticket-hall floor, black rock pile in the tunnel, platform-lip white band, Pack-a-Punch without its own light | models drawn without their material or light: to be identified by position | the model or its material in the document's layer | `python -m store` facts for the model, `live shot` | frames; reviewers |
| L5 | Look: density and composition of every zone | 26 to 160 props per 1000 x 1000 against a stock median of 555 | layers of dressing per zone as the Arcade's rounds: stock models of every dumped zone, lifted stock rooms where they fit, signs, decals | the asset store, prefabs, `prop_scatter`, density and empty-area answers in milliseconds | density numbers per zone against stock; reviewers |
| N1 | New zone 4, Underpass Arcade | box x -3000..-1200, y 3500..4300, floor 0, ceiling 256, five bays y 4300..4600; D4 (1000) in the Fare Hall's west wall x = -1200; free of the present map (stair B ends at y 3400, platform B's roof at z -16) | geometry, dressing and light as a Studio section; door, zone, 12 spawners, Double Takes, wheel position, two wall buys through the generator until fault F2 is fixed | section building in the live loop; gameplay of a layer is NOT merged into a base (F2) | D4 buys and opens; zombies spawn in the Arcade and reach the player; rounds with the player there; reviewers 7.5 |
| G1 | Stair A crowd at the choke | zombies with no melee slot run in place 350 to 430 below a player under the 192-wide top door (x -510, y 2720..2800); nav route normal | to be decided on a census of slots and goals: wider top landing and door, or the stock behaviour for zombies without a slot | `forge run` census plans in 20 s; a geometry try in the live loop | rounds 1-2 and 11-12 pass 3 of 3 with the progress rule |
| G2 | Walkers on long routes without progress for 50 s (rounds 3, 12) | not yet read: census of goal, path length and speed needed | at the cause | same | round plans 11 of 11, three runs |
| G3 | One round 2 stalled 90 s with every zombie dead (g27q, once) | not reproduced | an always-on recorder of the round state in the acceptance script, not retests | none needed | the recorder's line when it happens again; 30 round-2 runs without it |
| R1 | Release candidate 5 | full build, whole suite, real-time run with a joined client, package with manifest | Studio `--full` with the recipe, else the SDK chain | row-list equality of both paths | `STATION-ZERO-RC5.md` |
| R2 | Official-client gate | v1.1.0 has no usermap support and crashes joining the lab server | not in this thread's hands: an upstream release, or the proof on a client built from upstream main | none | stays open; said in RC5 |

Then the packages 2 to 7 of the table above (quest, wonder weapons, enemies, Tab pages, camos and emotes, crowd), each with
its engine limit named where it cannot be done.

### State

- 24 Nov 2026, step 1 (read, no build). Measured: the document with the g27r emit as base and no layer emits 22 of 22 files
  byte-identical in 0.12 s (`C:\studio-data\sz\a1`); `studio check` 2.4 s; today's SDK main regenerates the g27r emit (17 of
  17 generator files equal, 4 s, `C:\studio-data\sz\regen`); Studio's compiler contains the RC4 light-volume commit; the RC4
  package's fastfile has the manifest's hash. Does not exist: a Studio build of Station Zero (F1), layer gameplay on a base (F2).
- 24 Nov 2026, baseline. The RC4 headless batch run again on the g27r build through Forge (compressed time, server with one
  bot; `C:\studio-data\sz\baseline\g27r_headless_24nov.log`, 531 s of runs): doors 70/70, economy 76/76, wells 9/9, stairs 9/9,
  post routes 128/128 and rules 39/39, start closed 20/20, rounds 3 to 10 and 13 to 15 pass; rounds 1-2 fail (round 2: 2 stuck,
  75 %) and 11-12 fail (round 11: 1 stuck at (-534, 2858, -121), 242 from its goal, the bot on stair A): the same two as on
  22 Nov. So the suite and its two failures reproduce today; this is the reference every Studio build is compared with.
- Work places: Station Zero's document scripts live in `tools-source/iwzmap/station_zero/` of this repository (branch
  `claude/sz-rc5`; `arcade.py` first); documents, builds, frames, plans and notes under `C:\studio-data\sz`.
- L4, read from the layout (not yet seen fixed): the black blob and the black rock pile are 27 placements of the static model
  `debris_concrete_rubble_pile_01_dark` (a dark-tinted material variant; the plain `debris_concrete_rubble_pile_01` is in the
  same dumps). Candidate: the plain variant; to be seen on the first recipe build.
- 24 Nov 2026, winding: g27r (RC4) is an UNREVERSED build. `build-sz2.ps1` at the RC4 head `2dce3fd` had no `iwz_wind.py`
  step; since 22 Nov (night) every build reverses the triangles for the engine's clockwise front. A build of the same emit today
  is therefore not the RC4 picture: the RC4 look scores are the baseline of the unreversed map only. Asked of the Studio build
  (fault F1, recipe key `keep_winding`): both usermaps of the g27r emit, to be shot at the RC4 cameras before any look work.
- 24 Nov 2026, G1 and G2 (stair A crowd, long-route walkers): the cause is the acceptance script's rule, not the map.
  `szaccept.gsc` lines 398 to 417 take the first `pathdisttogoal()` sample of a new zombie as its best; with no goal yet that
  sample is 0, the progress clock never restarts, and every zombie alive 50 s more than 200 from the bot counts as stuck.
  Measured on g27r (75 runs, compressed time, server with one bot; `C:\studio-data\sz\g1\REPORT.md`): the 7 flagged at the
  stair-top position walked at 34 to 63 units a second with the distance to the bot falling at every 5 s sample; counts
  follow the route's length (deck 8, stair top 7, half flight 2, hall 0); with a displacement rule (not moved 64 units in
  50 s while more than 200 from the bot) 0 of 30 round-runs flag a zombie and every zombie the old rule flagged reached the
  bot; at most 4 zombies within 110 of the bot (the probe kills on arrival, so a full ring cannot form in it: the crowd at
  the choke with a living player is NOT measured by this probe). Long routes (rounds 3-4, 11-12, 3 runs each): every flagged
  zombie moving at 27 to 70 units a second with 700 to 6,400 of path left. One real halt in 75 runs (deck, (-304, 2332,
  -319), free room, bot not its enemy), not reproduced: open, with G3, for a recorder. The script is the Platform lane's
  (fault FG1 reported); until its fix the round plans run with the corrected copy `C:\studio-data\sz\g1\lib\szg1.gsc`
  through `--library-dir` (a workaround, named as such in every result).
- 24 Nov 2026, Arcade round 1 (`station_zero/arcade.py`, document `C:\studio-data\sz\arcade\r1\doc`): in the game through
  `studio live` (start 61 s, a sync 12 to 19 s): check 0 errors, 12 of 12 spawners reach, 746 props, 63 models, 37 lights;
  frame p50 0.17 to 0.22 on nine cameras, p95 0.60 to 0.71 (below the stock band). Refused by the lead before any review:
  Spaceland props and five shop boxes flooded with one colour each; round 2 (cp_disco kit, dressed shops, small tile floor,
  emissive panels) in work. No play proof yet.
