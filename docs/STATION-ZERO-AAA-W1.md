# Station Zero AAA elevation, wave 1: light that points down, props that cast shadows, the station's own voice

Package of 21 Nov 2026 on the g27 map (`tools-source/iwzmap/station_zero2.py`, nine zones, built by `build-g.ps1`).
The owner's brief was to lift the map from "assembled assets, raw bold geometry" to a story-driven map: light, mood,
fog, detail, clues, and a voiced ZERO. This page says what was measured, what changed, how it was checked, and what
is still open. **Nothing here was built or run in the game by this package**: every number is from the generator's
output and from light bakes, offline. The frames of a built map are still the proof of how it looks.

## Canon first (the brief and the bible disagree in two places)

- **No "Group 935", no Paris setting.** `station-zero/01-LORE.md` wins over everything and says every name is ours,
  nothing taken from another game; the map is in Port Halcyon. The corporation that knew is Lodestar Signal &
  Telephone. The French lines of the voice script are a localisation for French-speaking players, not a new setting.
  A Paris map would be a new bible, which is the owner's call.
- **ZERO has no voice of its own.** It speaks through the board, lamps, printers and the recorded Voice of the Rapid
  (Evelyn Marsh, 1984), which it stitches word by word (`01-LORE` section 3, wiki `zero.md`). The "ZERO dispatch AI"
  lines are therefore the Voice, and a sentence she never recorded carries one audible seam.

## Why g27e5 reads as an assembled prototype (measured, not judged)

| Cause | Evidence |
| --- | --- |
| Every light baked as a bare omni light 20 units under the ceiling | 143 layout lights, 0 spots (`layout_lights.py` output). The ceiling and the upper walls received the same direct light as the floor: upper wall / floor E 0.47 to 1.32, ceiling / floor 0.34 to 0.81, and 30 to 60 % of the floor's light was bounce (`bake_zone_contrast.py` on the real g27e5dv bake). That is the even "showroom" fill review B scored 4 of 10 (item 9: ticket hall, generator room, service tunnel "bright, even and flat-lit") |
| No placed model cast a shadow | `bake.json` of g27e5dv: `occluder_boxes: 0`. 431 placed models (benches, turnstiles, lockers, the G-2, the three train cars, crates, desks) stood in light that did not know they were there: no contact shadow, no darkness under the train. The baker always supported light-blocking boxes; nothing gave it any |
| Warm casts in the bake itself | zone mean E max/min channel: maint corridor 1.96, generator room 1.83 (warm lamps on warm albedo, three bounces); the reflection probes carried the g25t frames' yellow (generator 0.74 / 0.59 / 0.36) into every glossy tile |
| The station speaks with another game's voice | the six PA clips of the audio module are BO3 zm_island facility lines (`audio/station_zero_audio.json` amb_iwz_pa_00..05); no line of the map's own canon is spoken |
| Story is thin where the reviews looked | review B item 13 (control room, 4/10): "sparse and tidy, no phone, coat or logs" |
| A baker bug | `lmbake.py` saved `tx_pos` as a file path (the name was reused by the file-copy loop): every bake.npz since lost its texel positions, so `sz2_mood_predict.py` could not run on any recent bake |

## What changed

| Piece | File | What it does |
| --- | --- | --- |
| Lighting design pass | `tools-source/iwzmap/sz2_lightdesign.py` (new), called by `station_zero2.py` | per light a `bake` block: ceiling fluorescents bake as downward spots (inner 42, outer 84 degrees), wall bulkheads as out-and-down spots, hanging and work lamps downward; the housing sends down what the omni record sent up (power 1.4 to 1.6); saturated emergency and signal lamps keep their colour on their own fixture (bake reach 144 instead of 240); the amber interaction cues stay local in the lit bake. Per zone a design record from `02-WORLD` section 8 (key, accent, darkest part) and a key gain where the hub zones must stay readable (ticket hall 1.5, Platform A 1.6, Platform B 1.2, stair B 1.8). Two motivated accents appended: the departure board's amber glow (ZERO's face, lit before power), the control room's test-pattern monitor. It never removes, reorders or changes a record's runtime fields (the audio layout addresses fixtures by index; the darkness build reads type, colour, radius, intensity, group) |
| Prop shadows | `tools-source/iwzmap/bake/occluders.py` (new), `layout_lights.py --occluders --catalog --kit` | every placed model becomes a light-blocking box for the baker: catalog / kit bounds turned by the model's yaw, the port's collision boxes for ported models, the train cars as underframe and roof slabs (the interior lights still leave by the windows), the genset. Walkable models (track, platform edges, sleepers) and boxes under 16 tall or 8 across are skipped, boxes are inset 12 %, a box that holds a light is dropped. g27: 202 boxes |
| Probe chroma | `station_zero2.py` (`IWZ_PROBE_CHROMA`, 0.5 with the pass) | each zone's reflection probe keeps its luma and half its chroma |
| Story vignettes | `station_zero2.py`, models the map already loads, no clip | 23:55, "Control informed": the night controller's desk with a cold mug, the roster, a paper cup by the radio, the evening paper; ZERO's uncollected printout spilled towards the alcove; in the staff corridor under DO NOT RESTART, June 1985, Lodestar's last cleanup shift: a body under a decontamination sheet and the crew's bag. 10 decor records (8 static models, 2 entities) |
| One A/B switch | `build-g.ps1 -NoElevation` (`IWZ_ELEV=0`) | builds the g27e5 look with the same code |
| Bake meter | `tools-source/iwzmap/bake/bake_zone_contrast.py` (new) | per zone, from any bake in seconds: floor E, ceiling / floor, upper wall / floor, pool p90 / median, dark share, bounce share, cast; `--ref` prints the change |
| Baker fixes | `bake/lmbake.py` | `tx_pos` saved as the positions; `texel_positions()` rebuilds them for old bakes (used by the meter and by `sz2_mood_predict.py`); the light grid no longer drops a cell because its rays hit an occluder (see below) |
| Tour plan | `docs/station-zero/iwz-tour-aaa.json` | a Forge / gamelab client plan: two review cameras of each zone, the story views, three light views |
| Voice script | `docs/station-zero/STATION-ZERO-VOICE-SCRIPT.json`, checked by `tools-source/iwzmap/audio/voice_script_check.py` | 273 lines in English and French: the Voice of the Rapid (77: slots V01 to V50 of `11-AUDIO-DIRECTION` 5.1, six PA rotation lines for the slots the map plays today, five lines for the g27 relay quest and purchases, 14 glue words), Strand's eight tapes (the wiki text), the Night Inspector (8), the Conductor (3), the photo booth (5), pay-phone oddities (4), the four heroes in their film roles (42 each: the 40 slots of 5.2 and two for the g27 quest). Every line names its trigger and its status: plays today through a slot the map has (8 lines; 4 hero lines on the same events wait for routing), event exists and needs a play call (13), stock mode event (52), a built thing to wire (16), a zone or mechanic not built yet (180). Voice design prompts per speaker; voice ids stay empty until a voice is designed or listed |
| Tests | `tools-source/iwzmap/tests/test_sz_elevation.py` | occluder rules, the light pass's contract (nothing removed or reordered, runtime fields untouched), the committed voice script passes its checker |

## Checked offline (no game, no build)

Generator output with the environment of `build-g.ps1 -Train -TrainSet g27e -Lights -Smodels -Kit -NeutralProbes -Fx
-Audio` (origin/main 3800cdc as the base):

| Gate | Before | After | Seconds |
| --- | --- | --- | --- |
| generator | | | 4.4 |
| `sz2_plan.py` | 10,289 cells reachable, fails 0 | same | 0.5 |
| `iwz_emitcheck.py check` | 0 errors, 17 warnings | same | 2.3 |
| `iwz_emitcheck.py diff` base -> new | | **0 collision triangles and 0 nav cells changed**, re-test in game: nothing | 2.5 |
| `sz2_artlint.py`, `sz2_seams.py`, `sz2_navconn.py`, `iwz_emitcheck.py reach`, `sz2_flatness.py`, audio anchors | pass | pass | 0.1 to 1.6 each |
| world.bin, colmap.hkx, navgraph.bin, cp_iwz.gsc | | byte-identical | |

Light, three bakes of the same quick settings (texel 8, 64 rays, 3 bounces; 67 to 81 s each), old light list against
new; the meter on the real g27e5dv bake (256 rays) gives the same picture for the old list:

| Zone | floor E (old -> new) | upper wall / floor | ceiling / floor | pool p90 / median | dark share | cast |
| --- | --- | --- | --- | --- | --- | --- |
| ticket hall | 0.173 -> 0.101 | 0.59 -> 0.71 | 0.56 -> 0.81 | 3.58 -> 5.89 | 0.22 -> 0.29 | 1.19 -> 1.30 |
| stair A | 0.460 -> 0.276 | 1.32 -> 0.80 | 0.81 -> 0.52 | 2.58 -> 2.47 | 0.19 -> 0.23 | 1.01 -> 1.07 |
| Platform A | 0.124 -> 0.099 | 0.49 -> 0.45 | 0.62 -> 0.74 | 3.78 -> 6.65 | 0.22 -> 0.32 | 1.13 -> 1.12 |
| maint corridor | 0.236 -> 0.163 | 0.69 -> 0.28 | 0.59 -> 0.24 | 2.11 -> 2.36 | 0.22 -> 0.33 | 1.96 -> 2.34 |
| generator room | 0.336 -> 0.247 | 0.59 -> 0.14 | 0.47 -> 0.23 | 2.07 -> 2.24 | 0.13 -> 0.23 | 1.83 -> 1.96 |
| control room | 0.201 -> 0.176 | 0.66 -> 0.21 | 0.58 -> 0.43 | 2.62 -> 2.66 | 0.24 -> 0.32 | 1.30 -> 1.19 |
| service tunnel | 0.365 -> 0.313 | 0.68 -> 0.29 | 0.59 -> 0.21 | 2.22 -> 2.63 | 0.14 -> 0.23 | 1.42 -> 1.42 |
| Platform B | 0.154 -> 0.162 | 0.42 -> 0.20 | 0.49 -> 0.37 | 2.71 -> 3.37 | 0.19 -> 0.26 | 1.36 -> 1.39 |
| stair B | 0.256 -> 0.146 | 0.32 -> 0.17 | 0.38 -> 0.33 | 2.57 -> 5.27 | 0.17 -> 0.39 | 1.02 -> 1.11 |

Predicted frames (`sz2_mood_predict.py`: the real g27e5 bake and its engine frames of `level\runs\g27e5-views-a`
fit a tone curve, the new bake's irradiance is pushed through it). The control run, the old light list in the same
quick bake, predicts no change (control room median 0.410 -> 0.406), so the numbers below are the light change, not
bake noise:

| View group | median sRGB luma (old -> new) | block contrast p90 / p10 |
| --- | --- | --- |
| ticket hall | 0.303 -> 0.259 | 4.10 -> 4.63 |
| stair A | 0.255 -> 0.237 | 4.36 -> 4.12 |
| Platform A | 0.285 -> 0.264 | 4.26 -> 4.91 |
| maint corridor | 0.318 -> 0.262 | 2.30 -> 3.14 |
| generator room / G-2 views | 0.428 -> 0.336 / 0.526 -> 0.378 | 2.48 -> 2.75 / 3.85 -> 4.24 |
| control room | 0.410 -> 0.335 | 3.43 -> 4.46 |
| service tunnel | 0.245 -> 0.212 | 4.09 -> 4.47 |
| Platform B | 0.361 -> 0.324 | 2.93 -> 2.91 |
| stair B | 0.296 -> 0.257 | 3.55 -> 3.41 |
| interaction views | 0.405 -> 0.354 | 4.08 -> 5.15 |

Readability at the 35 interaction and quest points (`--points layout`, gate 0.22): 34 pass. The one under is the
teddy-bear secret inside the hero car (0.357 -> 0.157): the point is measured on the track-bed texels under the car,
which the train's underframe now shadows; the bear itself is a model lit by the light grid. Its frame is to be looked
at in the tour.

The light grid (what lights every model, zombie and the train) was checked as well: with occluders the baker dropped
every grid cell inside the three train cars (4 of 4 each: it counted a ray that hit an occluder as "inside solid"),
so the 23:47's interior would have taken an outside cell's light. Fixed in `lmbake.py` (an occluder hit is black
light, a back face still marks solid): the cars keep 4 of 4 cells again and Platform A 778 of 778 (1,880 kept
map-wide against 1,901 before; the 21 fewer are cells inside prop boxes).

Read: in the work rooms and tunnels the walls above head height now get a quarter to a half of the light they had
against the floor, the floor has two to three times more of its area in real darkness, and the pools stand out. The
over-bright stairs are darker on purpose (review B). The ticket hall's floor median falls to 58 % with much stronger
pools; its ceiling and upper walls fall less than its floor (they are lit by the floor's pools now), which is the one
zone where the picture is mixed. The warm cast of the maint corridor and generator room is not fixed (it comes from
the warm lamp colour and warm bounce, not from the light's shape); the control room's maroon wash is down (1.30 to
1.19). The irradiance is not the frame: the engine multiplies by the albedo and tone maps with auto exposure.

## Not done, and why

- **Fog.** No tool makes fog in a generated map today: the generator's own FX check found the fog, dust and hanging
  smoke effects not rendering in the engine (`station_zero2.py`, FX list note), and no visionset fog value of this
  map is known. Needed: find the fog state the engine reads for a map (visionset fog fields or the world's fog
  settings) by reverse engineering, prove one value in a frame, then give the generator a per-zone fog table.
- **Architectural trim, the white slabs, the cream rectangles of Platform B, the train's end caps and skirt, the
  mirrored 047, the blue wedges.** Review items of g27e5 not touched here; the blue wedges have no traced source yet.
- **Door collision and the pit wells** are the a85 package's work (`claude/a85-station-zero`, 4 commits not on
  main: the Deadeye machine moved clear, the PaP interaction gated, the door-tile variants). This package does not
  touch those lines; the Coordinator merges both.
- **The voice lines are not generated.** 8 lines play today through slots the map has (PA01 to PA06 replace the six
  BO3 clips of the PA rotation; V17 and V16 are the power sequence's announcement); 5 more (V51 to V55: relays, PaP
  shutter, doors, trap) have their event in `cp_iwz2.gsc` and need one play call each; the rest wait for the stock
  routing or for zones that are not built. Voices must be designed first (`voice_design_prompt` per speaker) and the
  credits checked: the whole script is 16,069 English and 18,832 French characters, more than one month of the
  Starter plan (30,000). Hero lines carry `routing: unproven` (own aliases and a per-character routing,
  `11-AUDIO-DIRECTION` 5.2).
- **The darkness build** (`darkness/dark_build.py`, the dark-before-power bake) writes its own light list and ignores
  the `bake` blocks: a darkness build of this source bakes its power lights as omni lights again. It needs the same
  four lines `layout_lights.py` got.
- **The warm cast** of the maint corridor (1.96 -> 2.34) and generator room (1.83 -> 1.96) is worse in the bake: with
  less white light on the upper walls the warm lamps and the amber cues weigh more. Next: a neutral key in the
  generator room (the work light) and a check of the warm albedo guesses of `layout_lights.py`.

## The A/B switch and the merge, checked

- `IWZ_ELEV=0` (what `-NoElevation` sets) on this branch against origin/main: every emitted file byte-identical
  except `layout.json` (only the informational `mount` keys of the lights and the port `boxes` of ported decor are
  added) and `plan.json` (the same adjacency set in another order); `layout_lights.py` without `--occluders` writes a
  lights.json byte-identical to the g27e5 one. The A/B is one variable.
- g27e5dv is reproduced exactly by the a85 branch (`claude/a85-station-zero` 9f08d2c) with
  `IWZ_WELL_FIX=well_w=stock,well_e=stock`: world.bin byte-identical to `level\src_g27e5dv`, layout.json identical.
  That branch merged with this one (no conflict): every gate of `build-g.ps1` passes, world.bin, colmap.hkx,
  navgraph.bin and cp_iwz.gsc are byte-identical to g27e5dv, `iwz_emitcheck diff` 0 collision triangles and 0 nav
  cells changed.

## Build and tour (the Coordinator)

```powershell
# 1. one checkout with both branches: origin/main + claude/a85-station-zero + claude/sz-aaa-elevation (they merge clean)
# 2. the g27e5dv environment (both pit wells in the stock stair style) and a fresh bake: the light list changed and the
#    stage cache keys on lights.json; never -ReuseBake / -BakeFrom an older tag (world.bin is unchanged, the old bake
#    would be taken)
$env:IWZ_WELL_FIX = 'well_w=stock,well_e=stock'
pwsh -NoProfile -File tools-source\iwzmap\build-g.ps1 -Tag g27e6aaa -SkipPick -Bake -LightArgs "--texel 6 --ambient 0.012" `
     -Train -TrainSet g27e -NeutralProbes -Fx -Audio -NavObstacles -Lights -Smodels -Kit -StairStyle g27 -WithP1
# 3. the A/B twin from the same code
pwsh -NoProfile -File tools-source\iwzmap\build-g.ps1 -Tag g27e6flat ... (the same switches) -NoElevation
```

```powershell
# inside a checkout of iw7-paris-server (origin/main): the Forge client tour of each build
python -B C:\forge\forge.py run tests\scenarios\gamelab\iwz-tour.json --usermap <IWZ_RUNTIME>\iwz-stage2\level\um_g27e6aaa
python -B C:\forge\forge.py run <this repo>\docs\station-zero\iwz-tour-aaa.json --usermap <IWZ_RUNTIME>\iwz-stage2\level\um_g27e6aaa
python -B C:\forge\forge.py run <this repo>\docs\station-zero\iwz-tour-aaa.json --usermap <IWZ_RUNTIME>\iwz-stage2\level\um_g27e6flat
```

`iwz-tour-aaa.json` (25 views, each taken twice) adds to the stock tour two review cameras of every zone, the four
story views (departure board, control desk, printout, last shift) and three light views; the same plan on both builds
gives the A/B pairs. Then `sz2_mood.py --gate` on both runs (interaction views keep a mean luma of 0.22), three
independent reviewers on the pairs (not this package's author), and the owner's playtest.
