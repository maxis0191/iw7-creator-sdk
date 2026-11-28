# Blind review 1: the one document against stock frames (28 Nov 2026)

Three independent reviewers (Fable 5.2, fresh context, each a different reading order) scored 28 unlabelled in-game frames,
1280 x 720, no HUD: 14 of ours (the one document's final bake: 11 of the Underpass Arcade, 3 of the Terminus) and 14 stock
(Shaolin Shuffle's shopfronts and east subway station, Spaceland's projection room), shuffled with a fixed seed. They were
told only that the frames come from maps of one zombies game made by different teams, and were not asked to guess which.
Frames: `C:\studio-data\sz\film\review1\frames`; answers `reviewer_{1,2,3}.json`; key `key\key.json` (kept out of the
reviewers' reach until they had answered).

## Result: we lose, by three points of ten

| criterion (1 to 10, mean of three reviewers) | ours | stock |
|---|---|---|
| sense of place | 5.17 | 8.12 |
| readability | 6.19 | 7.00 |
| density | 4.19 | 7.48 |
| lighting | 4.12 | 7.52 |
| materials | 3.38 | 7.64 |
| **overall** | **4.61** | **7.55** |
| "could ship as it is": yes | **0 of 42** | 41 of 42 |

The three reviewers agree (ours 4.53, 4.63, 4.67; stock 7.61, 7.57, 7.47). Best frame of ours: `arc_east_long` 5.60; every
Arcade frame sits between 4.40 and 5.60; the three Terminus frames are the worst of the set (2.33 to 2.93: "an empty box
room wrapped in one repeating striped texture"). The weakest stock frames (5.47, 5.73) are at our best.

## What works

All three reviewers named the trade of all four shops from the frame alone ("record shop: records, tapes, video rentals",
"copy shop: photocopies, blueprints, passport photos, rubber stamps", "doughnut and coffee counter", "shoe repair and key
cutting kiosk"): the complaint "shops with no identity and no apparent use" is answered. Readability is the one criterion
near stock (6.19 against 7.00). The signage is called "the best element", "crisp and well designed".

## Why we lose (the reviewers' own words, the same in all three)

1. **Box-built architecture.** "Walls, pillars and counters are flat extruded slabs with hard right-angle edges and no
   bevels, trims, wear or decals." "Untouched rectangles ... nothing has a history."
2. **One tiling texture a surface.** "Single tiling textures with uniform roughness and no specular response; floors repeat
   visibly"; "nothing is glossy, wet or dirty".
3. **Light without shadow.** "An even, shadowless wash or a flat colour tint"; "little contact shadow"; "props float".
4. **Thin, small, authored dressing.** "Small, clean and thinly spread, leaving large bare floors and walls"; "flat cards or
   solid colour blocks instead of modelled stock".
5. **The signs outclass what they hang on.** "Sharp signage carrying all the identity, mounted on primitive box geometry."

## What it means for the method

The fault is no longer the idea of the place. Two explanations compete and are NOT yet separated: (A) how surfaces and
objects are made (boxes with tiling materials against stock's modelled and textured assets), (B) the pipeline every
surface of ours goes through (neutral reflection probes, a lightmap texel of 8 units, our vision, perhaps no ambient
occlusion and no baked shadow under render-only goods). The kiosk that passed a blind review on 23 Nov (9 against 9) stood
inside Spaceland, under stock light and probes: it proves nothing about lifted pieces in our own map, and round 19 already
used seven lifted prefabs. A control decides it before anything is rebuilt (package C1, `C1-CONTROL.md`): one stock room
put unchanged through our build, bake and vision, shot from the eye of an existing stock frame of that room. If (A) wins,
the next round of both sections changes the construction, not the design:

- **Arcade:** architecture and interiors from stock construction pieces and stock materials of ONE donor kit (not themed
  rooms lifted whole: that would rebuild the "assembly of found assets" the owner rejected, and break QUALITY-BAR rule
  23), re-planned to the Arcade's spec and carrying our brands, goods and film objects;
  our own boxes only where no stock piece exists, and then with trims, bevels and wear. Stock blend materials and stock
  decals for dirt, damage and wet; contact shadow (a finer lightmap texel at wall feet and under props, the engine's
  ambient occlusion if the vision allows it).
- **Terminus:** it is one material by design, so its form must carry it: sculpted paper (folds, creases, sagging and torn
  sheets, stacked fan-fold, perforated edges that cast shadow), a normal and gloss map for the paper, printed variety on
  the surfaces (timetables, boards, forms), and furniture made of folded paper with real thickness: authored meshes, not
  boxes.

Until a frame of ours is voted "could ship" by at least two of three reviewers and the overall score is within one point
of stock on the same kind of place, neither section is reported as done.
