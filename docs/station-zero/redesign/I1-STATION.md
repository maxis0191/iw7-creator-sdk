# I1: the one Station Zero document (integrator I1, 28 Nov 2026)

Branch `claude/sz-film-int` of iw7-creator-sdk (worktree `sdk-film-int`). Data: `C:\studio-data\sz\film\station`. **[m]** measured,
**[b]** built but not proven. Compressed-time runs are Forge headless runs (speed 50); the walk is one real-time client run.

## Rebuild from a clean checkout of the integration branch

```
# 1. the base without Pack-a-Punch, lit first, from this SDK (4.6 s); regen.sh = B1's script with SDK = this worktree
sh C:/studio-data/sz/film/station/regen.sh C:/studio-data/sz/film/station/base IWZ_LIT_FIRST=1
# 2. the document (and its Terminus look copy, for room frames only)
set STUDIO_ROOT=C:\studio
python tools-source/iwzmap/station_zero/film/station_doc.py --look
# 3. Studio on this SDK: C:\studio-data\sz\film\station\env.sh (STUDIO_CONFIG = station\studio_i1.json, IWZ_SDK = the worktree root, IWZ_ZONETOOL_EXE)
python -m studio check C:\studio-data\sz\film\station\doc
python -m studio bake C:\studio-data\sz\film\station\doc --final
```
The bake recipe and the shell's build settings come from `C:\studio-data\sz\film\allbaked2\doc\map.json` (`arcade_shell.RECIPE_FROM`); the
pictures from `C:\studio-data\sz\film\art`. The whole chain of this lot: `station\final_run.sh` (document, check, final bake, ON/OFF frames).

## Files
- `film/station_doc.py`: the one `Map` = `arcade_doc.build(base=station\base)` (shell + four goods layers + L1's lights) + `terminus.build(m)`;
  one settings block: the shell's recipe (allbaked2: kit dumps, darkness, dark exposure -5.5) with `light_rules.LIT_VISION` as the lit vision
  and the Terminus variant `term` aliased on `cp_frontend`; checked by `settings_report` before saving. B1's six round-19 layers are not
  carried: 1,808 of their 1,867 dressing objects stand inside the Arcade box (the old Arcade).
- `film/arcade_shell.py`, `film/arcade_doc.py`: `build(..., base=None, settings=None)`, defaults unchanged.
- `film/terminus.py`: the machine key and the ink (below); the derived pictures go to `SZ_TERMINUS_DERIVED` (`station\art` for this document).
- `cp_iwz2.gsc`, `station_zero2.py`: wall prices per place (below).
- Plans `film/plans/i1_arcade.json`, `i1_walk.json`, library `film/plans/lib/szi1.gsc`. Data copies of every plan run: `station\plans\`.

## `studio check` (station\check_prices.json, the final document) [m]
ok; reach 61 sources, 0 failures; `ISLAND: zone terminus: reached only by script (a teleport): its own navigation island of 778 cells`;
arcade 1,403 cells, no island, no unreachable zone; `build.networked_entities.total` **480** (Arcade on the old base 494, Terminus document
487: 494 - 17 Pack-a-Punch records + 3 of the Terminus's `weapon_upgrade`); light rows 12 of 256 (lights.txt +7: the Arcade's six key lights
and the Terminus key); voxel light entries 59 of 65,535; 306 static props (all static); render triangles 105,136, collision 36,498; own
materials 20; pictures 109; 66 lights in the layers (7 `bake='bounce'`). No emit warning (the price warning is gone, below).

## The Terminus machine [m]
Measure: `station\tools\machine_ratio.py`, a fixed mask of the body made on the before frame of `term_machine` (the camera does not move),
display luma (the metric that reproduces T1's 0.13: 0.129 on T1's pass-5 frame), paper = the back wall west of the sign, never inked.

| | body / paper | body / backdrop | frames |
|---|---|---|---|
| before (T1's key: 3.0 baked + a runtime row at x1,000) | 0.126 | 0.141 | `station\mach\shots\on\` |
| (a) key K 3.0, `bake='bounce'` (row 81,000) | 0.311 | 0.349 | `mach\shots\m2_key\on\` |
| (a)+(b) K 3.0 + ink | 0.306 | 0.390 | `mach\shots\m3_key_ink\on\` |
| (a)+(b) K 7.0 + ink (kept) | 0.456 | 0.578 | `mach\shots\m4_key7_ink\on\` |
| the same on the final bake | 0.457 | 0.578 | `station\final_term\on\term_machine.png` |

Clipped pixels at all three Terminus cameras: 0.0 % in every variant.
- (a) a stock `track_spot` on an iron rod, head top (-10149, -4680, 182), 111 units above-front of the body on the side the player arrives from
  and `term_machine` looks from, head pitched toward the body, light aimed at (-10200, -4646, 88), cone 20/38, radius 230, 2,900 K, `bake='bounce'`,
  group `emergency`. Direction checked on a key-alone frame (`mach\shots\m1_keyonly\on\term_machine.png`: tubes and beam at 0.001): the body,
  reels and top lit, the pool on the post and the deck around its foot, no paper wall in the cone.
- (b) ink, PIL in the paper set's hand (round dots, three print lines a green bar, overstruck so neighbouring lines merge into black bars; ragged
  line ends, skipped lines and dropped dots let the paper through; alpha = coverage, so the wall's own green-bar paper shows): a block 440 x 216
  on the back wall where `term_machine`'s line of sight through the machine lands (centre x -10640, z 156), and a validator bay 160 x 200 on the
  deck around the post (the footprint fields it would cover are left out). Pictures `station\art\ink_block_wall.png`, `ink_validator_bay.png`
  (coverage 0.845, 0.857; previews on paper `preview_*.jpg`). A first draw at dot radius 0.78 was a grey hatching (coverage 0.47): rejected.

## Final bake and frames [m]
`studio bake doc --final` 5 min 24 s (texel 8, 256 rays, 3 bounces, 165 lights); both sessions `reused: the remembered final bake`; real
`live power on` (settle 15 s) + 10 s. Sheets (all opened):
- Arcade and every camera of the document, station vision: `station\final\sheet_on_{0..3}.jpg`, `sheet_off_{0..3}.jpg` (34 cameras each)
- the Terminus under its own vision (look copy, T1's way: the camera of `live shot` is no rider): `station\final_term\sheet_on_0.jpg`, `sheet_off_0.jpg`

Light, final bake against L1's draft bake (`station\light_final_vs_draft.txt`; L1 `light\final\m_final.json`), five cameras:

| camera | p5 final / draft | dark % | p99 | clip % | ground (b/r) final / draft |
|---|---|---|---|---|---|
| arc_east_long | 0.066 / 0.065 | 0.05 / 0.13 | 0.741 / 0.743 | 0.11 / 0.11 | |
| arc_hole_nine_front | 0.043 / 0.042 | 0.02 / 0.06 | 0.728 / 0.729 | 0 / 0 | 0.150 (0.32) / 0.151 (0.32) |
| arc_copy_stop_front | 0.040 / 0.040 | 2.0 / 2.2 | 0.867 / 0.869 | 0.02 / 0.01 | 0.127 (0.53) / 0.128 (0.53) |
| arc_needle_drop_front | 0.038 / 0.037 | 0.36 / 0.67 | 0.805 / 0.805 | 0.01 / 0.01 | 0.132 (0.06) / 0.135 (0.06) |
| arc_west_long | 0.043 / 0.042 | 0.58 / 0.66 | 0.693 / 0.697 | 0.01 / 0.01 | |

The final bake moves every number by about 2 % or less. Terminus means (own vision): `term_arrival` 0.575, `term_long` 0.581 (target 0.45
to 0.60), `term_edge` 0.585, `term_machine` 0.564, `term_screen` 0.568; no clipping.

## Wall-buy prices (coordinator's order) [m]
The document's prices were never applied on this base: `cp_iwz2.gsc` (the Station Zero generator's template) never had the price table; it
was added to the scene generator's own `cp_iwz3.gsc` only (852d329), and Studio's merge writes its rows only where `iwz_wall_prices` exists.
Now `cp_iwz2.gsc` carries `iwz_wall_prices`, `iwz_price` and `//@PRICES@` after `table = [];`, and `station_zero2.py` replaces the marker
with an empty table (no generator price). One change from `cp_iwz3.gsc`: a place without a price gets the weapon's stock cost back (the base
sells the same two weapons as the Arcade, and `cp_iwz3.gsc`'s loop leaves a priced place's cost on every place of that weapon; TOOL-FAULTS I1-3).
Regeneration against the base before the change (`station\base_before_prices`): **20 files, 1 differs: `cp_iwz.gsc`** (the thread line,
the function, the empty table). SDK tests `test_terminus`, `test_scenegen`: 37 OK. Measured in `i1_arcade`: `WALL_PRICES places=2 of=2
stock_weapons=5`; Hole Number Nine SMG spent **1000**, then the base's own UMP (stair_a, control) **1250** (stock), Heel & Key marksman **1500**.

## Acceptance on the one build (usermap `station\um\cp_iwz`, compressed time) [m]
```
sz8_doors        PASS    steps 30/30   expects 21/21
sz8_power_perks  PASS    steps 17/17   expects 19/19
sz8_rounds       PASS    steps 9/9     expects 14/14
t1_buy           PASS    steps 13/13   expects 34/34
t1_trip          PASS    steps 27/27   expects 31/31
i1_arcade        PRODUCT steps 50/50   expects 51/52   (the one failure: the marksman reach, below)
```
`i1_arcade` (new): D4 bought (1000), arcade zone active; a player standing on the navigation (nav_d 1) in the arcade volume inside Needle
Drop (-2910, 4400), Copy Stop (-2300, 4400) and Hole Number Nine (-1700, 4390); the two wall buys and the control at the prices above; the
stock wheel moved to Copy Stop by the stock mover (`_id_BC3E("arcade")`: active at (-2554, 4460)), one roll for 950, a weapon given (weapons
1 -> 3); two zombies from each shop's back room spawner reach the player in the hall: Needle Drop 2/2 (33.5 s), Copy Stop 2/2, Hole Number
Nine 2/2, Heel & Key 2/2 in 39 s (the path runs through the service passage: at a 40 s budget one run gave 1/2).
Note: sz8_doors passes its two wall buys because the `use` step stands the player at the nearest buy of that weapon anywhere (TOOL-FAULTS I1-2).

Real time, a client cell (listen client), `i1_walk`: PASS 25/25, 2/2. Every debris door opened by the lab's `doors` step, then a walk with
player physics (`move`; no forward key exists in the input channel) from the ticket hall through D4 along the north shop lane to the west end
and back, all ten legs reached. Frame time, 1280 x 720, uncapped, 10 s windows: `arc_east_long` median **2.74 ms** (95th 4.50, 99th 5.13,
max 6.20); middle of the hall median **2.77 ms** (4.54, 5.14, max 8.49). Client frames `station\final\client_east_long.png`,
`client_mid_hall.png` (evidence `C:\forge-run\runs\20261128-042428-0075-i1_walk`).

## Not done, not proven
- **The Heel & Key marksman buy is probably out of reach from the hall.** A player's hull stops at the stall counter at y 4284.9; from the eye
  there to the buy struct (-1420, 4404, 1) is 133 units against `player_useRadius` 128. The model (eye to struct against the dvar) is not
  the engine's use test reverse engineered, and no Use press exists in the input channel to try it. The change needed (shell, A2's design):
  the buy's struct about 10 units toward the hall, or the stall counter clip moved in.
- **D4 bought on the client cell**: the `use` step fired the trigger and charged nothing (headless it charges 1000 in every run); the walk
  used the `doors` step. After it the D4 prompt still shows at `arc_east_long` (client frame). Not diagnosed.
- The Terminus OFF frames show the room at the dark exposure; the room is reachable only after power, so they are a record, not a state a
  player sees.
- From T1, still: the clock does not run, no dust in the beam, the line printer's sound, the bench numbers, WAY OUT, Strand's tape.

## Decisions the brief did not dictate
- The key on the arrival / `term_machine` side (east-south), not on the use side (west, T1's): the player first sees the machine from the
  arrival, looking west, and the measured camera looks from there; the user at the west side sees the body at close range under the prompt.
- K 7.0 (from 3.0 and 7.0 measured; 3.0 missed the 0.40 target).
- The ink's alpha is the dot coverage only, so the wall's own paper shows through; one wall block (behind the machine as `term_machine` sees
  it) and one floor bay; no ink on the west end wall behind the machine as the arrival sees it.
- The wheel moved to Copy Stop by the stock mover in the plan (the base starts it on platform_a); the plan judges the wheel by the weapon count.
- The walk on the north shop lane: the centre line (y 3960) is blocked by A2's bench islands.

## Superseded build folders (not deleted)
Documents of earlier workers under `C:\studio-data\sz\film\` that this document replaces: `b1\doc`, `b1\doc_emit`, `b1\regen0`, `b1\regen1`,
`b1\base_lit_nopap`, `terminus\doc`, `terminus\doc_look`, `terminus\base_lit_nopap`, `terminus\um`, `terminus\look`, `arcade\shell\doc`,
`arcade\shell\docall`, `arcade\shell\litview`, `arcade\goods_a\doc`, `arcade\goods_b\doc`, `light\doc` and its variant documents
(`light\e1`, `e1b`, `w1`, `w2`, `w2b`, `w4`, `w5`). Still read, not superseded: `allbaked2\doc\map.json` (the recipe), `base_lit` (the shell's
default base), `art`. Mine, removable when this lands: `station\base_before_prices`, `station\mach` (the machine study).
