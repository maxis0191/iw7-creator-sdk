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
