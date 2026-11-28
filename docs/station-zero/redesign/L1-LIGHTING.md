# L1: the Arcade's light against stock (lighting worker L1, 28 Nov 2026)


## Tools made for this lot
- `tools-source/iwzmap/station_zero/film/light_measure.py`: `measure` = LIGHTING-GAP section 0's numbers for any frame (p5, p50, p95, p99, share
  under 0.03, clipping, floor band; for shop-front cameras the ground patch, its blue / red, the front patch above it and ground / front).
  The front patch is rows 60 to 70 % of the middle half: that band reproduces the diagnosis's column (stock `shopfronts_2` 0.039 / b/r 0.87
  against 0.038 / 0.71; our pass-8 pink shop 0.033 / 0.19 against 0.033 / 0.20). `shoot` = one session: start, power on, 10 s, the cameras,
  variants synced into the same session (`--session`), stop; a variant whose sync or power failed is skipped, a stale or failed frame is
  renamed `.rejected` and never measured, and each variant's compile log is kept beside its frames.
- `light_variants.py`: variant documents (floor material, pool mode, pool intensity, pool geometry, `--lit` vision keys) built by the
  Arcade's own builder, nothing of the shell's files changed.

## Step 0: baseline (reproduced)
Document `C:\studio-data\sz\film\light\doc` (`film/arcade_doc.py`, all four goods), real `live power on`, 10 s, `--clean`, frames
`C:\studio-data\sz\film\light\s0_base\on\`, numbers `light\m_s0_base.json`. Pink shop ground 0.0146, b/r 0.134 (diagnosis 0.015 / 0.13);
Copy Stop 0.0133 / 0.33 (0.013 / 0.33). Stock in the same script: `shopfronts_2` ground 0.094 b/r 1.41, ground / front 2.38; `shopfronts_13`
0.057 / 3.48 / 2.58; subway (8) median p5 0.070, p50 0.170, p99 0.733, under 0.03 0.04 %, floor band 0.261.

## Step 1: E1 (session 1, `light\e1\shots`, the documents beside them)
Ground patch at the three front cameras (linear luminance; b/r; ground / front):

| variant | Hole Number Nine | Copy Stop | Needle Drop |
|---|---|---|---|
| baseline (all baked, quarry tile) | 0.0146 / 0.13 / 0.44 | 0.0133 / 0.33 / 0.09 | 0.0157 / 0.08 / 0.47 |
| B: pools runtime x1 (rows 4,000 to 5,500) | 0.0091 / 0.16 / 0.23 | 0.0085 / 0.39 / 0.05 | 0.0094 / 0.14 / 0.23 |
| B x0.3 | 0.0088 | 0.0083 | 0.0092 |
| B x3 (rows 12,000 to 16,500) | 0.0097 | 0.0092 | 0.0102 |
| A: stock `concrete_floor_polished_01_ssr`, pools baked | 0.0400 / 0.64 / 1.56 | 0.0361 / 1.10 / 0.26 | 0.0449 / 0.26 / 1.59 |
| C: A + runtime pools | 0.0228 / 0.69 / 0.77 | 0.0173 / 0.96 / 0.11 | 0.0235 / 0.54 / 0.71 |
| stock `shopfronts_2` / `_13` | 0.094 / 1.41 / 2.38 | 0.057 / 3.48 / 2.58 | |

Read: (1) the floor's colour (C4) is the largest single lever measured: a grey polished floor takes the same baked pool to 2.7 times the
ground light and to the pool's hue (pink b/r 0.13 -> 0.64); (2) runtime pools at stock-range rows (stock cp_disco spots: median 6,355, 90th
percentile 28,004, radius 270 to 450, `grammar\db\cp_disco.sqlite`) add almost nothing to the floor: a tenfold change of the row moves the
ground by 10 %. The only lit change of x3 against x0.3 (`e1\diff_hi_lo_*.png`) is a stripe on the Heel & Key shutter housing about 20 units
from its spot. (3) No mirror image of the fronts is visible in A's floor (frames `e1\shots\docA\on`); A0 (same family without `_sref0`)
separates the reflection from the albedo: session 2.

## W1: the light mode "runtime with baked bounce" (built, unit-proven)
- SDK `bake/layout_lights.py`: a layout light with `runtime: true, bake: 'bounce'` becomes a baker light with `direct: false`.
  `bake/lmbake.py`: such lights get their own `direct_light` call; their irradiance (`Ebounce`) is added to what surfaces throw in every
  bounce (`Lout`) and to what the light grid's cells see (`Lfinal`), and is left out of `B`, the direction image and the grid's delta term
  (`light_grid` receives the baked lights only). With no such light the baker's arithmetic is unchanged (`Ebounce` is 0).
  `blender/blend_core.py` (documents without a base) carries `bake: 'bounce'` into the layout record.
- Studio: `B.light(..., bake='bounce')` (implies `runtime`), `B.fixture(..., bake='bounce')`; `baselights.merge` writes BOTH the layout record
  and the `lights.txt` row on a base with darkness (a pure runtime light gets no record there, and the dark split zips the layout with the baker
  list, so the record must exist); a bounce light of group `power`/`flicker` on such a base is refused (its bounce would be baked into the dark
  state). `expand.py` carries the value; `loop.py` never makes such a light a live op (its bounce is in the lightmap).
  `lightwhy` (`studio light`) counts it once (as baked, in baker units): no double count.
- Tests: SDK `tests/test_lmbake_light.py::test_runtime_light_bounce_only` (one room: B under the lamp 27.35 baked, 0.000 bounce-only; the wall's
  A 0.921 both; the grid's c0 sum 51.2 against 12.95); Studio `tests/test_bounce_bake.py` (the document path through `baselights.merge` and the
  SDK's baker: B 25.07 -> 0.000, A 0.845 both) and three merge tests in `tests/test_baselights.py`.
- Records: `studio check` `build.networked_entities` 494 before and 494 after (first with 17 key lights in bounce mode: rows 5 -> 22,
  voxel entries 13 -> 371 predicted; final with 6: rows 11, voxel entries 57 in the compile log). Unnamed rows take static template slots.

## C2 notes for the lead
- Route a (`_sref0` base with OUR floor pictures): `concrete_floor_polished_01_ssr` (techset `w_l_sm_replace_i0c0s0o0n0p0_sref0`, constants
  `colorTint`, `reflectionRa`) reads semantic 14 (`_packed_cs`) and 15 (`_packed_nog`), the same semantics as our `concrete_01` route. Our
  packed 15 image (`port/matconv.pack_normal_gloss`) writes R gloss, G/A octahedral normal and B = 1.0, which is the occlusion channel of the
  `_nog` layout: the pictures fit unchanged. Studio refuses the base today (`materials.BASES`). The patch (Studio `studio/materials.py`, not in
  this lot): add `'concrete_floor_polished_01_ssr': {'route': 'ext', 'normal': True, 'gloss': True}` to `BASES`, and in `entry()` write
  `e['ext'] = {'base': base, ...}` instead of `EXT_BASE`; the document's `settings.build.kit` must bring the material (`fixtures.use_kit` does
  for a placed model only: add `cp_disco:w/concrete_floor_polished_01_ssr` to the kit's materials).
- Route d needs no compiler change: the probe fill runs only when `IWZ_PROBES` is `neutral` (`iwzmap.cpp:677-678`); a document's
  `settings.build` `{"compiler": {"env": {"IWZ_PROBES": "template"}}}` merges over the base's recipe (checked: the emitted `build.json` carries
  it) and leaves the template's captured cubes in place.

## The measured scale of an engine light (calibration, the decisive finding)
E1's runtime pools at rows of 4,000 to 16,500 added almost nothing. They were not missing: one session per variant on a grey floor at a
manual exposure (`tonemapAuto=0`, exposure -2) measured the ground light each pool adds against the same pool baked
(`C:\studio-data\sz\film\light\cal\shots`, `cal.json`, `cal\analyse.py`):

| pools | Hole Number Nine | Copy Stop | Needle Drop |
|---|---|---|---|
| off (x0.01) | 0.1232 | 0.1037 | 0.1516 |
| runtime x10 (row = intensity x 10,000) | +0.0788 | +0.0859 | +0.0810 |
| runtime x20 | +0.1465 | +0.1621 | +0.1497 |
| baked (the baker's own pool) | +0.1995 | +0.1980 | +0.2034 |
| straight down, runtime x20 / baked | +0.1087 / +0.1869 | +0.1535 / +0.1917 | +0.1084 / +0.1832 |
| baked on `concrete_floor_polished_01_ssr` (C2 control) | +0.2127 | +0.2152 | +0.2171 |

The response is close to linear (x10 to x20: 1.86 to 1.89 times). The engine row that equals the baker's light is x23 to x27 of today's
1,000 a unit for the oblique pools (199 units), x25 to x34 straight down (238 units: the engine's falloff is a little steeper than the
baker's). Chosen: **27,000 a document unit for a bounce light** (`studio/baselights.py BOUNCE_ROW_PER_UNIT`, the same constant in the SDK's
`blender/blend_core.py`). Consequences for the lead: (1) a plain runtime row of a document (x1,000) is about 1/27 of the baker's light for
the same number; (2) INFERRED, not measured: the darkness build's power lights are written at x840 (`sz2_recipe.DARK_LIGHTS`), which by this scale is
about 1/32 of the baked light of the same layout intensity; (3) the `_sref0` floor measured +6 to 7 % against the same floor without it,
but its technique set is NOT verified in the zone (the compile log names the material, not `..._sref0`): route a is unproven, not
shown worthless. The scale depends on distance over radius (the row's radius is 1x the document's, the baker's 2.5x): calibrated at
about 0.5 to 0.6 of the radius; the ream spot sits near 0.8.

## Steps 2 to 6
- **W1 in the Arcade** (`film/arcade_shell.py`, `film/shell_hall.py`, lights only): key mode (`KEY_BAKE`, default `bounce`) on the four shop
  pools (moved 32 units in front of the fascia face, under it, cone 45: at 14 units off the front with a 60-degree cone the engine light hit
  the shutter housing 20 units away), the Copy Stop ream spot and the Heel & Key pegboard spot. Sign and front lights that sit 0.2 to 8 units
  off a wall stay baked: at 27,000 a unit they would clip the wall next to them. Rows 5 -> 11 (cap 256), voxel light entries 57 (compile log;
  cap 65,535), records 494 -> 494 (`studio check`, final document).
- **Goods requests**: Copy Stop's ream wall (x -2604..-2500, y 4312..4334) stands behind the window glass, and the baker treats glass as an
  occluder (`studio light --at=-2552,4311,60 --normal=0,-1,0`: every hall light `blocked` by `cs_win_w_g...`, the ream face 0.0). Only an
  engine light reaches it: a key spot from the grid at (-2552, 4000) aimed at the wall's face, under the fascia (from y 4180 it crossed the
  fascia box and lit the B&W COPIES sign). Final frames: the reams read as blocks of yellow, pink, green and blue at `arc_copy_stop_front`
  and `arc_copy_stop_oblique` (sheet_on_1). Heel & Key: a tungsten spot from under the stall ceiling on the pegboard (model: 1.11 of the
  pegboard's 1.57); the stall reads lit and warm, the tagged shoes are still small dark shapes from `arc_heel_key_front`: not yet "cobbler".
- **C5 fill** (`fill_k`, `L1_FILL`): the 12 panel spots by row (lane 0.15, middle 0.2, south 0.3, varied 0.7 to 1.2 a panel), colonnade
  tubes 0.6, pools x1.3. `studio light` on the W1 document (model, baker units, not a frame): pools 4.28 to 5.95 against mid hall 0.41 to 0.64, so 6.7 to 14.5 to 1 (it was
  1.8 to 1). QUALITY-BAR rules 9 to 13 pass (`final\score.txt`; rule 12 needed the ream spot in the pool's blue-white, 8,500 K read 'cool').
- **C4 floor** (`film/tiles.py floor2`, `floor_quarry2_c/g.png`; the old picture is untouched): the same quarry layout in muted browns,
  saturation at most 0.351, smallest channel 0.087 after squaring, a quarter of the tiles wet (gloss 245 to 252, the rest 205 to 225); 3 x 3
  tile test `art\arcade\tiles\floor_quarry2_tiletest.jpg`. Not done: wet patches with a higher F0 (alpha 15 to 25): Studio's material route
  writes F0 0.04 everywhere (`materials.py _pixels`, alpha = F0): a gloss-dependent alpha is a Studio change.
- **W2 lit vision** (one session per variant): veil 0.04 and fog 0.5 / density 150 moved the blacks by 0.01 at most; exposure moves them
  (-1.5, -1.0 in the table). At -1.25: fog 0.95 / density 30 lifts them (p5 0.037 to 0.066, 0 to 2.1 % under 0.03), 0.95 / 3000 lowers
  them (`w2b\shots`). Chosen `film/light_rules.py LIT_VISION`: veil 0.04, fog 0.95 / density 30, exposure -1.25, volumetric ambient 0.2,
  air 0.02, spot 0.15, set over the Arcade's recipe and proposed for the map. No haze seen around the key lights.
- **W4 route d**: `settings.build {"compiler": {"env": {"IWZ_PROBES": "template"}}}` (no compiler change; the build log has no probe fill
  line). The floor is neither black nor blown (pink ground 0.0541 against 0.0555 with the flat cubes) and no mirrored picture is visible at
  `arc_east_long`: the `t33` rule is not shown to be a blocker; the reflection term is too weak to read at these glosses either way.

## The table (five cameras, real `live power on`, 10 s, `--clean`; numbers `C:\studio-data\sz\film\light\m_table.json`)
| step | p5 (5 cams) | under 0.03 | p99 | clip | floor band | pink ground / b/r / g:f | Copy Stop ground / b/r |
|---|---|---|---|---|---|---|---|
| 0 baseline (all baked, old tile, -2.5 EV) | 0.003..0.024 | 7.5..18.4 % | 0.48..0.78 | 0.00 % | 0.100 | 0.0146 / 0.13 / 0.44 | 0.0133 / 0.33 |
| 2 W1 key lights (pools, 2 spots) + C5 fill | 0.003..0.020 | 9.1..17.0 % | 0.57..0.78 | 0.07 % | 0.109 | 0.0256 / 0.09 / 0.79 | 0.0206 / 0.28 |
| 5 + C4 floor (W1 + fill + new tile) | 0.003..0.019 | 7.8..18.7 % | 0.49..0.76 | 0.00 % | 0.139 | 0.0555 / 0.24 / 2.04 | 0.0392 / 0.50 |
| 4 + veil 0.04 | 0.011..0.026 | 5.9..15.1 % | 0.48..0.76 | 0.00 % | 0.142 | 0.0544 / 0.24 / 2.01 | 0.0392 / 0.51 |
| 4 + fog 0.5 / 150 | 0.013..0.027 | 5.7..14.6 % | 0.47..0.75 | 0.00 % | 0.139 | 0.0514 / 0.24 / 1.99 | 0.0373 / 0.51 |
| 4 + exposure -1.5 | 0.027..0.049 | 2.6..6.9 % | 0.67..0.85 | 0.10 % | 0.228 | 0.1313 / 0.30 / 2.29 | 0.1068 / 0.51 |
| 4 + exposure -1.0 | 0.036..0.067 | 1.0..3.2 % | 0.74..0.89 | 0.15 % | 0.288 | 0.1992 / 0.37 / 2.40 | 0.1734 / 0.55 |
| 4 + -1.5 + volumetrics | 0.029..0.052 | 2.2..6.0 % | 0.67..0.85 | 0.10 % | 0.226 | 0.1279 / 0.30 / 2.28 | 0.1043 / 0.51 |
| 6 route d (template cubes) | 0.004..0.020 | 7.8..17.9 % | 0.49..0.55 | 0.00 % | 0.133 | 0.0541 / 0.24 / 2.03 | - |
| FINAL (all of it, -1.25 EV) | 0.033..0.060 | 1.2..3.6 % | 0.70..0.87 | 0.12 % | 0.255 | 0.1588 / 0.33 / 2.34 | 0.1341 / 0.53 |
| stock subway (8) | 0.016..0.113 | 0.0..14.4 % | 0.41..0.89 | 0.03 % | 0.311 | - | - |
| stock shopfronts_2 | 0.069..0.069 | 0.0..0.0 % | 0.86..0.86 | 0.00 % | 0.253 | 0.0943 / 1.41 / 2.38 | - |
| stock shopfronts_13 | 0.057..0.057 | 0.4..0.4 % | 0.83..0.83 | 0.00 % | 0.250 | 0.0574 / 3.48 / 2.58 | - |

Targets of W2 at the final document (`light\final\m_final.json`): p5 at least 0.04 at four of five cameras (Needle Drop 0.037); under
2 % below 0.03 at four of five (Copy Stop 2.2 %); p99 at least 0.7 and clipping under 1 % at all five. Over all 29 cameras: clipping at
most 0.41 %, the darkest frame a Copy Stop interior with 6.6 % under 0.03. The frames still read as a dim interior: dark ceiling between
the live panels, shadowed corners, pools in front of the shops (sheets below; the lead and reviewers judge).

Frame time (`perf_east_long.json`, Forge client cell, uncapped, dark state, the `arc_east_long` eye, 15 s windows): NOT measured as a
before / after. Two pairs, order swapped: base 5.14 ms / final 2.79 ms (base second), then base 3.01 / final 5.38 (final second): the
second run of a pair (the colder, re-booted cell) is the slow one whatever the map; Forge served the repeats from its cache. The cost of
the 6 key lights is below the run-to-run spread (about 2.5 ms median) and needs interleaved runs on one warm cell.

Final sheets ON and OFF, all 29 cameras: `C:\studio-data\sz\film\light\final\shots\sheet_{on,off}_{0..4}.jpg`; side by side with the target
and stock `shopfronts_8`: `final\compare_east_long_target_stock.jpg`.

## What still separates our frame from stock (plainly)
1. Colour on the ground: our pink pool is b/r 0.33 against the Lounge's 1.41: the tile still leans red, and our pools are pastel colours,
   stock's saturated neon (purple, blue). Ground / front is at stock (2.34 against 2.38).
2. No mirror: neither the `_sref0` floor (+6 %) nor the template's cubes show the fronts in the floor; stock's wet street shows highlights of
   many saturated lights, ours has six engine lights in the hall.
3. Lifted blacks: stock's p5 is 0.057 to 0.069 with no pixel under 0.03; ours 0.033 to 0.060 with 1.2 to 3.6 % under it.
4. Light count and haze: stock has 10 to 29 engine spots in view, 259 of them volumetric; ours 6 key lights, none volumetric (the compiler
   writes `isVolumetric = 0`: the `vol` token of LIGHTING-GAP C3 is not built, and the sweep showed no need yet).
5. Glow and smoke cards (C6): none placed; out of this lot.

## Not done of the brief, and the order of merging
- Sign lights, the directory board's light and the jukebox glow are not in key mode (at 27,000 a unit a light 0.2 to 8 units off a wall
  would clip it: E1's x3 row already saturated a housing 20 units away); they stay baked. The change needed: wall fixtures whose light sits
  far enough off the wall (or a smaller cone toward the floor) before they can be key lights.
- Heel & Key from `arc_heel_key_front`: the stall reads lit and warm, the tagged shoes are small dark shapes; at `heel_key_counter_close`
  they read. Not met from the hall.
- `copy_stop_far`: the newsstand kiosk covers the ream window from that eye: the camera fails that check, not the light
  (`arc_copy_stop_front`, `copy_stop_window_close` show the coloured reams).
- `studio check` on a hand-written wrong `bake` value: `B.light` refuses it (ValueError, tested); a value written into a document by hand is
  not validated by `check` (only a bounce light of group power on a dark base is refused, at emit).
- Merge order: the SDK branch first. Studio's bounce mode on an SDK without this baker change would bake the light fully AND write the
  27,000 row (double light). `tests/test_bounce_bake.py` skips on such an SDK.
- Studio `gate.py` on the final head: 825 tests, 0 failures, 3 errors, all `MemoryError` in `test_review` / `test_stock_convex` while the
  machine had 2.9 GB free; those modules pass alone (TOOL-FAULTS L1-2).

## Decisions the brief did not dictate
- E1 A used the stock SSR floor with its own pictures (our pictures on that base need Studio `materials.py`; the patch is above); the
  control A0 (`concrete_floor_polished_01`) was added.
- The engine-row scale was measured and set (27,000 a bounce-light unit) instead of keeping x1,000: without it W1 removes light from the map.
- Key mode only on lights clear of surfaces (pools and two aimed spots); sign lights stay baked.
- The lit vision at -1.25, between the measured -1.0 and -1.5.
- Files outside the brief's list, each a few lines for the new mode: Studio `studio/expand.py`, `studio/loop.py`; SDK `blender/blend_core.py`.
- Sessions: one document per session (TOOL-FAULTS L1-1: a sync inside a session was refused by the disk floor), with an exact-key cleanup of
  each document's live and work folders and build server (`light_measure.clean_doc`).
