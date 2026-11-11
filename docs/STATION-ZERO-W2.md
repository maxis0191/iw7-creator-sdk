# Station Zero W2: the first four zones dressed (Cordon, Fare Hall, Escalator Hall, Underpass Arcade)

Package W2 of `docs/station-zero/12-BUILD-PLAN.md`, run 11 Nov 2026. The zones are the spawn zone and the three a
player reaches first in the build plan's order (W2's Fare Hall, then W3a's Cordon, Escalator Hall and Arcade). This
page says how the dressing is made, what was measured, and what is not proven. Looks are not judged here: the
reviewers' scores are reported as they were given.

## The recipe (what the next zones follow)

1. **Write the zone as a story, in data.** `tools-source/iwzmap/scenes/station_zero_dress_w2.json` holds, per zone, the
   groups the bible names (02-WORLD section 4 and the wiki page), each with a `note` saying what it is and what
   happened there: the gala's banquet with its chairs knocked back, the cut ribbon on the floor, the coats nobody
   collected, the decontamination corridor, the news crew's car with its mast up. Repeated compound objects are
   **vignettes** (local frame, turned as one); straight runs are **rows**; litter is a seeded **scatter** that keeps
   off everything placed before it and off spawners, interactions and player starts.
2. **Only stock models of the template map** (the 916 of `worldkit/cp_zmb.sqlite`: they compile as static models with
   no entity cost) and the proven materials of `sz2_materials.py`. Architecture that no model gives (columns, the
   board, booths, shutters, canopy, balustrades) is **solids**; signs and posters are **panels** (one fitted image a
   quad, render only).
3. **Light from fixtures only** (02-WORLD section 8): every light stands at a lamp, a sign, a neon, a screen or a bulb
   that is placed; `pool` sets a light by the light it should put on the floor below it. The bake
   (`scenegen.py bake`) turns them into lightmaps and the light grid; zones not dressed yet keep their old flat look
   through automatic fill lights.
4. **Check before building** (`szdress.py build`, seconds): every piece inside its zone, on one floor height, no two
   pieces intersecting (turned bounds, 1 unit), nothing clipped or tall in an opening's approach, no clipped piece or
   solid within 40 of a ground spawner, nothing within 48 of an interaction or a player start, nothing hanging within
   48 of a ceiling spawner, the zone's prop budget, no model more than 25 times in a zone. A wall piece is turned so
   its back faces the wall and snapped to it from its bounds; a floor piece stands on the base of its bounds.
   `szdress.py plan` draws a zone from above (pieces, clip boxes, lights, spawners, interactions, openings) in a second.
5. Then the map's own gates on the emit (`iwz_emitcheck`, `sz2_navconn`, `scenegen.py flights`, ents lint), the bake,
   the incremental build, the view count (`tome_cull.py model`), the headless lab plans, frames from fixed camera
   points with depth, and three independent reviewers.

Collision: the game's static props do not block a player by themselves (a known gap of generated maps), so szdress
gives every floor-standing piece at least 12 units across and 20 tall a clip box from its turned bounds (players and
zombies; the navigation is cut round it). Thin sheets get a box at least 4 thick.

## Measured

Offline (no game), 11 Nov 2026:

| What | Result |
| --- | --- |
| Dressing | 527 props (Cordon 171, Fare Hall 200, Escalator Hall 23, Arcade 133), 149 distinct models in the map, 55 fixture lights, about 155 solids and panels; `szdress.py build` 0 errors in under 2 s |
| Gates on the emit | `iwz_emitcheck` 0 errors (the one island is the Terminus, far by design), `sz2_navconn` 0 fails, `flights` 14 of 14, ents lint no blocker; navigation cells 26,763 -> 25,974 (the clip boxes cut 789) |
| Bake | 247 lights (192 fill lights in the 15 undressed zones, their look 0.97 to 1.35 of flat), 395 s |
| Props per view (`tome_cull.py model`, the perfzones views) | 577 static props map-wide; kept per view median 29, max 278 (Arcade); budget 700 |
| Door sightlines (`tome_cull.py check`, 276 views) | build b: 0 frustum errors, 134 props popped (they kept their template donors' cull distances). Fixed at the source: `scenegen.py emit` now writes the size-rule cull distance for every prop (build c) |
| Build b | 447.9 MB; 4,573 s of wall time, of which the work was about 7 minutes (compile 10 s, full assembly 481 s, zone about 50 s): the rest was waiting for the machine's build slot |
