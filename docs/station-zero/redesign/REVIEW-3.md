# Blind review 3: the Arcade after the construction round (28 Nov 2026, night)

Same method as review 2 (three Sonnet 5.5 reviewers, brief `C:\studio-data\sz\film\review3\BRIEF.md`, three reading orders,
key outside their folder: `control\r2\review3_key\key.json`, seed 202611283). 30 frames: the 15 Arcade cameras after the
construction round AC1 (`station\construct1\on`, SDK `claude/sz-film` 5d3dec8), 5 of the same cameras before it
(`station\final\on`), 10 stock frames from review 1.

## Result: the construction round did not close the gap

| set | place | readab. | density | lighting | materials | overall | could ship |
|---|---|---|---|---|---|---|---|
| Arcade after AC1 | 7.36 | 7.00 | 5.87 | 5.67 | 5.40 | **6.26** | 1 of 45 |
| Arcade before | 7.27 | 7.60 | 5.07 | 5.67 | 5.47 | **6.21** | 1 of 15 |
| stock | 8.37 | 7.17 | 7.47 | 7.30 | 7.47 | **7.55** | 24 of 30 |

Per reviewer, after / stock: 6.03 / 7.32, 6.16 / 7.70, 6.59 / 7.64. Best frame `arc_directory` 7.40 (the only "ship"),
then the two long hall views 6.93 and 6.73; worst the three shop interiors 4.80 to 5.33.

Density rose (+0.8), nothing else moved. The gap to stock is 1.3: lighting -1.6, materials -2.1, density -1.6.

## Why, in the reviewers' words (the same on most frames)

1. **Lighting is flat, even and shadowless** ("even, shadowless lighting", "flat unlit-looking floor", "blown-out floor
   patch"). The control room, built through the same pipeline, scored at stock: the difference is our light design, not
   the renderer.
2. **Shop interiors are boxes**: "thin box of low-resolution props", "flat white", "saturated flat magenta wall", "crude
   blocky brown mass" (the goods modules of A3 are authored boxes and cards; the construction round did not touch them).
3. **Crude single pieces in the foreground**: the benches ("huge dark slabs"), black untextured panels and gates read as
   "flat black cutouts", the wall-buy board ("flat cyan outline on a blank board").
4. **Floors repeat**: "flat repeating tile", litter "sprites".

## What follows

Next round, two lots beside each other: (L2) the Arcade's light design measured against the control room's stock lights
(how many sources a 100 square units, cones, shadows, the pool-to-shadow ratio on the floor) and rebuilt to it; (AC2) shop
interiors and the foreground pieces from stock models of the donor kit (K1 section 4.2 shop pieces, never placed so far),
the bench and black panels replaced, floor tile variety by blend paint and a second stock floor material. The bar stays
REVIEW-1's last paragraph.
