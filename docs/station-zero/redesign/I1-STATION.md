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

## `studio check` (station\\check_final.json, the final document) [m]
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
| the same on the final bake, key head moved (below) | 0.460 | 0.580 | `station\final_term\on\term_machine.png` |
| key alone at K 7.0, final position (direction check: draft bake, auto exposure of a dark room, no ratio) | - | - | `station\mach_final\shots\on\` |

Clipped pixels at all three Terminus cameras: 0.0 % in every variant.
- (a) a stock `track_spot` on an iron rod, head top (-10170, -4720, 182) (first at (-10149, -4680): from the arrival it hung in front of the FARE
  VALIDATION board and hid FARE; moved, the board reads whole), about 123 units above-front of the body on the side the player arrives from
  and `term_machine` looks from, head pitched toward the body, light aimed at (-10200, -4646, 88), cone 20/38, radius 230, 2,900 K, `bake='bounce'`,
  group `emergency`. Direction checked on key-alone frames in both positions (`mach\shots\m1_keyonly\on\`, `mach_final\shots\on\`: tubes and beam at
  0.001): the body, reels and top lit, the pool on the post and the deck around its foot, no paper wall in the cone.
- (b) ink, PIL in the paper set's hand (round dots, three print lines a green bar, overstruck so neighbouring lines merge into black bars; ragged
  line ends, skipped lines and dropped dots let the paper through; alpha = coverage, so the wall's own green-bar paper shows): a block 440 x 216
  on the back wall where `term_machine`'s line of sight through the machine lands (centre x -10640, z 156), and a validator bay 160 x 200 on the
  deck around the post (the footprint fields it would cover are left out). Pictures `station\art\ink_block_wall.png`, `ink_validator_bay.png`
  (coverage 0.845, 0.857; previews on paper `preview_*.jpg`). A first draw at dot radius 0.78 was a grey hatching (coverage 0.47): rejected.

## Final bake and frames [m]
`studio bake doc --final` and `studio bake doc_look --final` (about 5.4 min each: a bake is remembered per document, TOOL-FAULTS I1-1;
texel 8, 256 rays, 3 bounces); both sessions `reused: the remembered final bake`; real `live power on` (settle 15 s) + 10 s. Second pass
(after the price script and the key move; the first pass is kept in `final_v1`, `final_term_v1`; a Terminus set shot on a draft bake was
discarded). Sheets (all opened):
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
to 0.60), `term_edge` 0.585, `term_machine` 0.566, `term_screen` 0.568; no clipping. The Arcade numbers of the second pass equal the
first to the third decimal.

## Wall-buy prices (coordinator's order) [m]
The document's prices were never applied on this base: `cp_iwz2.gsc` (the Station Zero generator's template) never had the price table; it
was added to the scene generator's own `cp_iwz3.gsc` only (852d329), and Studio's merge writes its rows only where `iwz_wall_prices` exists.
Now `cp_iwz2.gsc` carries `iwz_wall_prices`, `iwz_price` and `//@PRICES@` after `table = [];`, and `station_zero2.py` replaces the marker
with an empty table (no generator price). One change from `cp_iwz3.gsc`: a place without a price gets the weapon's stock cost back (the base
sells the same two weapons as the Arcade, and `cp_iwz3.gsc`'s loop leaves a priced place's cost on every place of that weapon; TOOL-FAULTS I1-3).
Regeneration against the base before the change (`station\base_before_prices`): **20 files, 1 differs: `cp_iwz.gsc`** (the thread line,
the function, the empty table). SDK tests `test_terminus`, `test_scenegen`: 37 OK. Measured in `i1_arcade`: `WALL_PRICES places=2 of=2
stock_weapons=5`; Hole Number Nine SMG spent **1000**, then the base's own UMP (stair_a, control) **1250** (stock), Heel & Key marksman **1500**.

## Acceptance on the one build (usermap `station\um\cp_iwz`, the final build: prices and key moved; compressed time unless said) [m]
```
sz8_doors        PASS    steps 30/30   expects 21/21
sz8_power_perks  PASS    steps 17/17   expects 19/19
sz8_rounds       PASS    steps 9/9     expects 14/14
t1_buy           PASS    steps 13/13   expects 34/34
t1_trip          PASS    steps 27/27   expects 31/31
i1_arcade        PRODUCT steps 50/50   expects 51/52   (the one failure: the marksman reach, below)
i1_door_power    PASS    steps 8/8     expects 3/3     (D4 bought for 1000 headless with the power on)
i1_reach_client  PASS    steps 16/16   expects 1/1     (real time, a client: its evidence is the UI dumps and frames, below)
t1_client        PASS    steps 15/15   expects 2/2     (real time, a client: the trip ridden, the Terminus vision on the rider)
i1_walk          PASS    steps 25/25   expects 2/2     (real time, a client)
```
`i1_arcade` (new): D4 bought (1000), arcade zone active; a player standing on the navigation (nav_d 1) in the arcade volume inside Needle
Drop (-2910, 4400), Copy Stop (-2300, 4400) and Hole Number Nine (-1700, 4390); the two wall buys and the control at the prices above; the
stock wheel moved to Copy Stop by the stock mover (`_id_BC3E("arcade")`: active at (-2554, 4460)), one roll for 950, a weapon given (weapons
1 -> 3); two zombies from each shop's back room spawner reach the player in the hall: Needle Drop 2/2 (33.5 s), Copy Stop 2/2, Hole Number
Nine 2/2, Heel & Key 2/2 in 39 s (the path runs through the service passage: at a 40 s budget one run gave 1/2).
Note: sz8_doors passes its two wall buys because the `use` step stands the player at the nearest buy of that weapon anywhere (TOOL-FAULTS I1-2).

Client UI dumps (`station\final_checks\`): inside Hole Number Nine the prompt `Hold F to purchase the HVR ($1000)` (the document's price);
at the Terminus machine `Hold F to validate your FHR40 [Cost: 5000]`, no "Pack-a-Punch" in any dump; at the Heel & Key counter NO purchase
prompt (frames `iwz_i1_hk_prompt.png`, `iwz_i1_smg_prompt.png`, `iwz_t1_arrive.png`, `iwz_t1_prompt.png`). The rider's arrival frame shows the
Terminus vision and FARE VALIDATION whole; from the rider's slot the key's spot head sits over the left end of the larger 047 . TERMINUS
board behind it.

`i1_walk`: every debris door opened by the lab's `doors` step, then a walk with player physics (`move`; no forward key exists in the input
channel) from the ticket hall through D4 along the north shop lane to the west end and back, all ten legs reached. Frame time, 1280 x 720,
uncapped, 10 s windows. Alone on the machine (build before the key move): `arc_east_long` median **2.74 ms** (95th 4.50, 99th 5.13), middle
of the hall **2.77 ms** (4.54, 5.14). Final build, while another client cell booted beside it: `arc_east_long` 2.99 ms (6.20, 7.59, max
17.4), middle 2.67 ms (5.52, 6.77). Client frames `station\final_checks\client_east_long.png`, `client_mid_hall.png`.

## Follow-up (29 Nov): the marksman rifle from the hall, D4 on a client [m]
Rebuilt once more after these changes (`station\rebuild_v2.sh`: document, check ok 480 / reach 61-0, final bake, a fresh build, usermap
`station\um\cp_iwz`, session stopped and its folders removed). Verdicts on that build:
```
sz8_doors   PASS  steps 30/30  expects 21/21   (compressed time)
i1_arcade   PASS  steps 49/49  expects 55/55   (compressed time)
i1_prompts  PASS  steps 33/33  expects 11/11   (real time, a client)
i1_walk     PASS  steps 26/26  expects 6/6     (real time, a client)
```
**How a purchase is offered on this map (read in the stock scripts, then measured).** The interaction monitor that runs is cp_zmb's
(`cp_zmb_interactions.gsc` `zmb_player_interaction_monitor`): it offers only the struct nearest the player's origin, within 72 units, and
puts the player's use trigger at that struct's x, y at eye height; it never offers a door. A door is bought through its own `door_buy`
`trigger_use` (`zombie_doors.gsc` `init_door_buys`): the engine draws its prompt, its `trigger` takes the money and opens the door.

**The marksman rifle (Heel & Key).** Three placements, each measured on a client:
- on the back pegboard (y 4404): never offered from the hall (beyond 72);
- on a board behind the counter (y 4336): offered (the monitor picked it, `i1_hint`: hint string, can-give, cost 1500), but no prompt drawn
  at any view pitch (`i1_mk_look`). Cause, isolated with the monitor stopped (`i1_mk_trig`): the use trigger stood behind the stall's player
  clip (`hk_stall_clip`, y 4300..4330); the same trigger moved 42 forward, in front of the clip, drew "Hold F to purchase the M1 ($1500)";
- now: a pegboard display board on the counter's front edge (x -1530..-1450, y 4298..4301, z 44..100, framed in the stall's joinery),
  between the front rail's tagged pairs (x -1535, -1445); the rifle hangs broadside on its hall face (yaw 0, chosen from client frames
  turned by 90 degrees: `final_checks\mk_turn_sheet.jpg`; at 270 it was edge-on). The struct at (-1490, 4296).
Measured on the client from the hall at the counter front (-1490, 4285): prompt "Hold F to purchase the M1 ($1500)" (UI dump and frame
`final_checks\i1_mk_before.png`), offered by the stock monitor itself (`hint=1`, route monitor), 1500 spent, the M1 in hand, then "Hold F to
purchase ammo for the M1 ($750)" (`i1_mk_after.png`). Headless (`i1_arcade`): bought from the same hall position, 1500, no teleport.
The weapon is the emitter's stand-in for the marksman class (`iw7_m1c_zm`, shown as "M1").

**D4 on a client.** Cause: the plan, not the map. The lab's `use` step bought D4 through the interaction struct (it stands the player 44
past the struct along its yaw, x -1204, inside the door plane, and fires the player's interaction trigger by hand): headless that charged
1000, on a client nothing, and it is not how a player buys a door here. Now `i1_door_buy` fires D4's `door_buy` trigger for the player where
he stands in the ticket hall (-1080, 3900). Client: prompt "Hold F to Enter this area ($1000)" from there (`i1_d4_before.png`), 1000 spent,
door open (`DOOR_BOUGHT` in the map log), no `door_buy` trigger of D4 left; after the purchase no D4 prompt from the hall or the Arcade
(`i1_d4_after_hall.png`, `i1_d4_after_arcade.png`). The prompt that stayed after the lab's `doors` step is that step's artifact (it opens
the blockers and leaves the trigger), not a product fault: a real purchase removes it. `i1_walk` now buys D4 this way.
The SMG in Hole Number Nine on the same client: "Hold F to purchase the HVR ($1000)" (`i1_smg_prompt.png`).

**Plans.** `szi1.gsc`: `i1_buy` (an interaction bought from where the player stands; on a client it waits for the stock monitor's pick, headless
it applies the monitor's rule at that position and refuses beyond 72 or when another struct is nearer), `i1_door_buy`, the probes `i1_hint`,
`i1_ww`, and the experiments `i1_trig_hold`, `i1_trig_set` (plans `i1_mk_turn`, `i1_mk_look`, `i1_mk_trig`). sz8_doors once gave 20/21 (one
zombie from Copy Stop's back room stood at (-2272, 4507), 27 north of the partition by its door, until the stock cleanup removed it); the
next two runs passed: intermittent, not diagnosed.

## Not done, not proven
- The Heel & Key marksman buy: fixed (follow-up above).
- D4 on a client: the plan was the cause, fixed (follow-up above).
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
default base), `art`. Mine, removable when this lands: `station\base_before_prices`, `station\mach`, `station\mach_final` (the machine
study), `station\final_v1`, `station\final_term_v1`.
