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
