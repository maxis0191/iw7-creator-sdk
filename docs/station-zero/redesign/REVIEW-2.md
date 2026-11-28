# Blind review 2: the control room against stock (28 Nov 2026, evening)

Three independent reviewers (Sonnet 5.5, fresh context, three reading orders; brief `C:\studio-data\sz\film\review2\BRIEF.md`,
the same five criteria and "could ship" question as review 1) scored 22 unlabelled 1280 x 720 frames, shuffled with seed
20261128. Key kept outside their folder (`control\r2\review2_key\key.json`) until all three had answered.

Frames: the control room (stock cp_disco east subway lifted unchanged and built through our whole pipeline: Studio main
b3d879d, SDK main, compiler d3567483, final bake, probe room, blend layers kept, foreign world materials brought) at stock
poses 1, 2, 5 with our vision and with stock's vision; stock's own frames at the same poses; 9 other stock frames and 4 of
our Arcade frames from review 1 as anchors.

## Result: the pipeline is at stock on stock's own room

| set (mean of three reviewers, 1 to 10) | place | readab. | density | lighting | materials | overall | could ship |
|---|---|---|---|---|---|---|---|
| control room, ours, stock vision | 7.89 | 7.33 | 7.33 | 6.22 | 7.67 | **7.29** | 4 of 9 |
| control room, ours, our vision | 7.89 | 6.89 | 7.33 | 5.89 | 7.67 | **7.13** | 4 of 9 |
| control room, stock | 7.78 | 6.89 | 7.11 | 6.11 | 7.78 | **7.13** | 6 of 9 |
| other stock frames | 7.52 | 6.93 | 6.81 | 6.33 | 6.93 | 6.90 | 18 of 27 |
| our Arcade (review 1 frames) | 5.75 | 7.33 | 4.00 | 5.08 | 4.33 | **5.30** | 0 of 12 |

Per reviewer, control ours (our vision / stock vision) against control stock: 6.87 / 7.13 vs 7.13; 7.67 / 7.67 vs 7.33;
6.87 / 7.07 vs 6.93. These reviewers score on a different scale from review 1's (stock other 6.90 here, 7.55 there; our
Arcade 5.30 here, 4.61 there): compare within this review only.

What still separates ours from stock is the grade, named by all three on the frames that did not ship: "over-saturated teal
and orange", "dark, blue, crushed", "floor reads as murky". It matches the measurement (R2-PARITY section 15): stock's
vision fixes the cast, the light level per place is still off (baked light distribution, stock light parameters not
carried). Content, materials and density are at stock.

## What it decides (PLAN section 5, the decision rule)

The lifted room is within one point of stock (0.00 to +0.16): **the pipeline is good enough; the next round of both
sections is construction**, as K1 plans it (cp_disco donor kit, authored meshes in stock plain materials, our surfaces
carrying stock layered materials with painted wear, density to stock). The same set of frames puts our current Arcade 1.6
to 1.8 under stock: that gap is now construction, not the pipeline. Open pipeline items, worked beside the construction:
the grade and the baked light distribution (R2-PARITY 15), decals, glass and fences (R2-PARITY 14, built, not proven).
