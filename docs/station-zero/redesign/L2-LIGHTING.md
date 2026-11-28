# L2: the Arcade's light design, measured against stock and rebuilt (worker L2, 28 Nov 2026)

Why: REVIEW-3 scores the Arcade's lighting 5.67 against stock 7.30 ("flat, even, shadowless", "blown-out floor patch"); REVIEW-2 showed the pipeline lights a
stock room at stock level (control room 7.13 to 7.29 against stock 7.13). The fault is our light design. This page measures stock's design, then ours, then the redesign.

## Tools made for this lot (SDK `tools-source/iwzmap/station_zero/film/`)
- `light_design.py`: `lights <doc|prefab.json>` = the count, spot share, shadowed share, engine share, radius / cone / strength distribution and sources per
  million square units of any document or of the control room's stock prefab; `frames` = per set of frames the numbers that isolate LIGHT from material (below).
- `floor_map.py`: the direct light of a whole document on its floor, ceiling and walls by the baker's own formula with rays for shadows (Studio's `lightwhy`),
  offline, about 1 to 5 minutes, no game and no bake. The design loop: it has no albedo and no bounce, so it measures the DISTRIBUTION of light.
- `l2_lights.py`: the redesign, a post-pass over light records only (called by `station_doc.build` after the goods and the Terminus).

## Frame metrics, and which of them measure light
Local contrast and the 90 / 10 ratio of the raw floor band measure tile pattern, litter and props as much as light: the Arcade reads HIGHER than stock on them (floor
contrast 0.30 against 0.20, floor p90 / p10 23.5 against 9.2) although reviewers call it flat. The ones that isolate illumination:
`ceil_over_floor` (mean linear luminance of rows 0 to 30 % over rows 70 to 97 %: stock's lamps light the floor, a flat fill lights the ceiling as much),
`floor_lp_ps` (p90 / p10 of the floor band after a 41-pixel blur: texture gone, pools and shade left), `tile_sd` (standard deviation of the 16 x 9 tile grid's log2
luminance: how unevenly light falls over the frame), `wall_lum` / `floor_lum`, `clip`, `dark`. Shop-front frames of stock (`shopfronts_N`) are an outdoor street: their ceiling
band is sky, they are used for the ground and front patches only.

## 1. Stock's design, measured (the control room's 29 stock lights, `ctl_subway_east_lay/prefab.json`; the stock cp_disco east subway)
Box x -150..1260, y 1950..3400 (2.04 million square units, track and stairs included: the floor area proper is smaller, so the density below is a floor of the true one).

| measure | stock control room (29 lights) | the Arcade before (hall: 21 lights; hall + shops: 33) |
|---|---|---|
| sources per million square units | 14.2 (29 in 2.04 M) | 24.8 hall (21 in 0.85 M); 38.9 with the shops |
| spots / omnis | 29 / 0 | 20 / 1 in the hall |
| engine lights (a runtime row), shadowed | 29, 26 (90 %) | 1 (the hall), 5 with the shops; 0 shadowed |
| outer half angle, p10 / p50 / p90 | 20 / 40 / 45 degrees | 80 / 85 / 85 |
| inner half angle, p10 / p50 / p90 | 5 / 20 / 30 | 35 / 50 / 50 (panels) |
| radius, p10 / p50 / p90 | 100 / 300 / 450 | 160 / 250 / 250 (hall), 169 / 250 / 388 (all) |
| strength, baker units, p10 / p50 / p90 | 0.14 / 0.42 / 1.04 (engine row 3.7k / 11k / 28k) | 0.39 / 0.71 / 0.86 (hall), pools 5.5 to 7.0 (engine row 150k to 190k) |
| saturated colours (spread of the channels over 0.4 of the peak) | 6 of 29 | pool colours only |
| aim | straight down (beam z component 0.9 or more for 27 of 29) | straight down, but 85 degrees wide |
| height over the floor (stock z - floor) | lamps 130 to 430 over a floor at 230, radius about 1.5 x the drop | panels 238 over floor, radius 250 = 1.05 x the drop |

Read: the DENSITY is the same (14 against 25 a million squares, a dozen lit panels in a hall of 0.85 M); what differs is the SHAPE. Stock's lamps are narrow (half angle 20 to 45), shadow casting
and engine lights, so each makes a pool with an edge, the columns and rails throw shadows, and the ceiling above them is left dark. Ours were twelve 85-degree baked fills of one strength: every wall and the
ceiling got as much light as the floor (the model's ceiling-to-floor irradiance below), and the four shop pools were the only structure, at 5 to 7 times stock's hottest light (the "blown-out floor patch").
The "fewer, stronger" of the brief is not what the numbers say: stock is not hotter than our fills (0.42 against 0.71 median), it is narrower, shadowed and mostly engine lights.

## 2. The redesign (`l2_lights.py`, a post-pass over light records; `light_rules.LIT_VISION`)
What changed, by record (the document's light records: counts in section 4):
- **12 ceiling troffers** (`light_panel_0..11`, the live panels of `arcade_shell.LIVE`, positions kept): from an 85-degree baked fill to a narrow cone straight down (inner 18, outer 46: stock's
  median 20 / 40), radius 380 (1.6 x the drop of 238, stock's 1.5), an engine light with its bounce baked (`bake: bounce`, strength x 27,000 = the engine row). Seven of them shadow casting
  (`shadows: true`: the columns, the benches, the floor machine throw shadows), five not; strengths 0.27 to 0.9 (a bright one 0.9, a middle 0.72 to 0.81, a failing tube 0.27 = 0.3 of a bright one): stock's
  median 0.42, 90th percentile 1.04. The dead panels stay dead (geometry of `hall_body`, untouched).
- **The four shop pools** (`light_pool_*`): strength x 0.35 (5.5 to 7.0 down to 1.9 to 2.5, still above stock's 1.04: they are the shops' signs thrown on the floor), cone 22 / 58 instead of 25 / 45.
- **Shop spill** (`l2_spill_<shop>`, four new engine lights): inside each shop, 70 units behind the shutter line at 96 high, aimed out at the hall (pitch 7 degrees down), cone 30 / 70, radius 380,
  strength 0.8, in the shop's own colour, no shadow flag (they must reach through the glass and shutter: the baker treats glass as an occluder, so the baked interior lights never reached the hall).
- **Shops' own fills**: spots of 80 degrees or more inside a unit narrowed to 28 / 62 and x 0.85, selected by position (not by id).
- **Hall fills**: colonnade tubes, wall lanterns and emergency lamps x 0.5 (baked).
- **Vision** (map-wide, `light_rules.LIT_VISION`, exposure untouched at -1.25): fog colour = stock's `0.749 0.651 0.522`, sky terms = stock's (`fogSkyIntensity 1`, `fogSkyMin 0`, `fogSkyMax 80`,
  `r_hdrSkyIntensity 0.15`); the fog colour's intensity is 0.27, NOT stock's 0.1, so that the fog keeps the luminance L1 tuned the black lift for (0.147 x 1.25 = 0.67 x 0.27). Sun-fog keys are not set
  (no sun in an interior).
Not done: flickering panels (the `flicker` group is a runtime row with no bounce and one network record each; the dim panels are static, 0.3 of a bright one); glow and smoke cards (LIGHTING-GAP C6).
The darkness logic is untouched: every light stays in group `emergency` (on in both states of the lit-first base), no `power` or `flicker` light is added.
