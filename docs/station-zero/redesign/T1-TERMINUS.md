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

## Changes after the first frames

- **Machine at yaw 180, not 270 [m].** The relocated scriptable lays the model's long axis 90 degrees from the pap yaw (pass 1: yaw 270 put it along x, reels east). At 180 it lies along y, lens end south toward the screen; the user stands at its west side. Emitted `pap_machine 0 -10200 -4640 40 180` (on the post top).
- **The Terminus's own vision [m].** The station's lit vision (auto exposure, `tonemapAutoExposureAdjust -2.5`) held the room at mean luma 0.13 whatever the tubes did (x3 intensity: 0.127 -> 0.128). The document adds a darkness variant `term` (lit keys, fog and veil off, `tonemapAutoExposureAdjust 0.7`) aliased onto the spare stock vision `cp_frontend` (`cp_zmb_bw` is used by stock weapon passives). `modules/terminus.gsc` sets it on each rider after the crossing and restores the station's (`level.vision_set_override` while the dark holds, else `paris_iwz_lit_vision`, the darkness module's own choice) in `terminus_release` (return, match end). The darkness script re-applies nothing after its release, so the two do not fight; `cp_iwz_darkness.gsc` is unchanged. Room frames were shot with a look copy (`terminus\doc_look`: the lit vision itself = the `term` keys, synced into the session); the client frame after a real trip shows the rider's own.
- **The reel as light on paper.** The emissive route ignores alpha (its feathered border drew black); the picture (`film\terminus\art\screen_second_platform_light.png`: border cropped, x1.35, alpha = its own light x a feather) is a decal lit by the beam (14).
- **Module: zombies held while paused [m].** Without it the four zombies alive at arrival were recycled by the stock far-zombie cleanup 20 to 35 s into the stay; the pause watch now renews `delay_cleanup_until` (+2 s) on every alive zombie while its pause holds (stock skips them, `zombies_spawning.gsc:3560`).
- **Module: the projector runs once armed:** reels `on`, door `open_idle` (as cp_final; `ARMED machine=1` measured). That the reels turn is not seen in a still.
- **Base regenerated from this worktree** (`terminus\regen.sh`, 6.8 s): 19 of 20 files equal to B1's, the module differs. Studio keeps a base module that differs from what its SDK emits, without error (TOOL-FAULTS T1), and `live start` reuses the build when only the base folder changed (TOOL-FAULTS T1): `live sync --force` after a base change.

## Proof

Usermap of the final build: `C:\studio-data\sz\film\terminus\um\cp_iwz` (23:27). Forge, compressed time (speed 50, server and a bot):

| Plan | Verdict |
|---|---|
| `t1_buy` | PASS 13/13 steps, 34/34 expectations: power on, put in the Terminus, standing; 21 hull traces all hit (deck z 0.125, drop z -55.87); `use weapon_upgrade`: found, picked, spent 5,000 in the never-activated island zone; the machine's weapon collected: `iw7_fhr_zm+fhrpap1+mod_recoil+camo1+loot0` |
| `t1_trip` | PASS 27/27, 31/31: cab used at t 107.2 s, standing in the Terminus at t 114.2 s (7.0 s), off grid, trace under him z 0.125; bought and collected the same during the stay; spawning paused by the module; zombies alive 4 at arrival, 4 at +30 s, 4 when the pause ends (+40 s); back in car 1 (277.5, 1488) protections off; cooldown refused a second use; idle again after 150 s |
| `sz8_doors`, `sz8_power_perks`, `sz8_rounds` | PASS 30/30 21/21, 17/17 19/19, 9/9 14/14 |

Real time, a listen client (`t1_client`, not a client joined to a dedicated server: `Joined False`): PASS 15/15, 2/2. The prompt at the machine, UI dump `ui-t1_prompt.json`: `Hold ^3F^7 to validate your FHR40 [Cost: 5000]`; no "Pack-a-Punch" anywhere in the dump. Frames `C:\studio-data\sz\film\terminus\client\iwz_t1_arrive.png` (the rider's view on arrival, the Terminus vision), `iwz_t1_prompt.png`.

Records (`studio check`, `build.networked_entities.total`): **487**: 14 under the 501 of the lit-first map with the old Pack-a-Punch, 3 over B1's 484 (the `weapon_upgrade` interaction's spawned use entities).

Frames, look copy (vision `term`), pass 5 (final): `C:\studio-data\sz\film\terminus\pass5\` (sheet `sheet.jpg`, luma `luma.json`): mean 0.568 to 0.585 on the five cameras; light bars p90 `term_arrival` floor 0.758 wall 0.751, `term_long` 0.723 / 0.725.

## Not done

- **The machine reads as a dark silhouette against the paper:** body 0.13 of the paper behind it in `term_machine` (target 0.40), with a baked key and then a runtime emergency key at about 110 units. Why the runtime row does not light the scriptable is not proven.
- Static that the target shows moving: the clock (stock `sign_clock_04`, hands fixed near 10:10), the beam's dust (no volumetric: a baked spot only, `volumetricSpotBrightness 0` in the vision), the line printer's sound. Bench numbers 1 to 4, the "WAY OUT" sign, the passenger numbers, the hero colours of the fresh pairs, Strand's tape: not built.
- QUALITY-BAR 19 to 21 fail by design of the bible (an empty paper room 1,400 x 900, no job props, no pipes).
