# T1: the Terminus section (27 Nov 2026)

Worker T1, branch `claude/sz-film-terminus` of iw7-creator-sdk (from `claude/sz-film` 801050f). Brief: PLAN decisions 3 and 4,
FILM-LAYER 6, TERMINUS-AND-GAPS B and C, B1-BASE. **[m]** measured, **[b]** built but not proven.

## Files

- `tools-source/iwzmap/station_zero/film/terminus.py`: `build(m)` adds ten layers `terminus_*` to a Studio `Map`;
  `main()` writes `C:\studio-data\sz\film\terminus\doc` = the B1 document (`b1\doc`: base `b1\base_lit_nopap`, its six layers,
  its build settings, its pictures) + the section. Run: `STUDIO_ROOT=C:/studio python terminus.py`.
- `station_zero/film/plans/`: `t1_buy.json`, `t1_trip.json`, library `lib/szt1.gsc` (one GL PROBE line of the trip state).
- Studio for this document: `STUDIO_CONFIG=C:/studio-data/sz/film/terminus/studio_t1.json` (key `sdk` = this worktree's
  `tools-source/iwzmap`), `IWZ_SDK=<this worktree root>` (not its iwzmap folder: the recipe resolves `{sdk}/tools-source/iwzmap`).
- No regeneration of the base: `git diff --stat 09284d1..HEAD -- tools-source/iwzmap` touches only `blender/blend_core.py`
  (the Pack-a-Punch yaw offsets and marker `area`, read by Studio's layer writer, not by the generator).

## The place

| | |
|---|---|
| Box | x -10900..-9500, y -5200..-4300 (1400 x 900), deck z 0, ceiling 320; 6,300 units from the nearest base geometry and every bible zone; inside the light grid |
| Section | the screen wall (south, y -5200), a paper "track bed" 256 wide at z -56 (no track), the edge at y -4944, the deck 644 deep, the back wall (north) |
| Pieces | every floor, wall and ceiling split at x -10200 (no piece wider than 716); the edge clip in two |
| Paper | `w/term_paper_wall` (`paper_greenbar_tile.png`, tile 128: 16 bars of 64 px = one bar 8 units), `w/term_paper_floor` (the same picture turned a quarter, written by `terminus.py` into `film\terminus\art`: on floor and ceiling the bars cross the platform, as on one fan-fold sheet laid along it), `w/term_paper_times` (`paper_times_column.png`, tile 48 x 192, per column face); all `concrete_01` route, gloss 0.12 |
| Folds | 45 degree fold pieces of 16 (render-only meshes) at every floor/wall and wall/ceiling line; sprocket strips (`paper_greenbar_edge.png`) on the edge top, the edge face, under every wall top and over every floor fold |
| Columns | five, 48 square, pitch 288, at y -4372 |
| Benches | four, between the columns against the back wall, stepped fold profile (step 10, seat 18, back 44), paper |
| Printed | 63 fields of `footprints_printed.png` (96 x 96) facing the edge; 4 `footprints_fresh.png` pairs at the four arrival slots; `leader_8` .. `leader_2` along the edge, 8 at the east end |
| Signs | `sign_terminus.png` 216 x 42 on a hung paper board, both faces, near the arrival; `sign_fare_validation.png` 96 x 24 hung over the machine, both faces; `pictogram_validate.png` once, on the post's face toward the user. No sign names the machine |
| Clock | `sign_clock_04` x 2 back to back, scale 2.6 (48 across), on an iron rod. **It does not run** |
| Machine | `pap` at (-10200, -4650, 40), yaw 270: emitted `pap_machine 0 -10200 -4640 40 270` (on the post top) **[m: emit]**; the validator post: foot, shaft, collar, top plate in `w/metal_painted_red_01` (40 high) |
| Light | 15 `ceiling_tube` fixtures (3 rows of 5, radius x1.6), the beam: one warm spot from the lens end to the screen; all `group: emergency` (baked) |
| Screen | `screen_second_platform.png` 384 x 216, emissive sign, centre (-10200, -5200, 150), inside the beam's spot |
| Gameplay | zone `terminus` `island=True`, no spawner; marker `terminus_arrival` at (-9700, -4640, 0) yaw 180 with `area` = the room box (z -72..320); the module's four slots (y -4712, -4664, -4616, -4568) are clear of props |
| Cameras | `term_arrival`, `term_long`, `term_machine`, `term_screen`, `term_edge` (ids = names, `term_` as the brief names them) |

(Proof, records and frames: below, written when measured.)
