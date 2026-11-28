# R2: closing the pipeline gap on the control room (worker R2, 28 Nov 2026)

Started from C1-CONTROL.md and C1's builds and frames. At about the second hour the coordinator stopped every build and game request: a disk
clean deleted the template dump (`IW7-Runtime\iwz-map-ref-a`), the kit dumps (`iwz-stage2`, `chars58`), Forge's stock root, `C:\IW7-Cache\tools`,
the world databases (`C:\studio-data\grammar`), the RenderDoc captures (`C:\studio-data\captures`) and the baker's Python (`IW7-Runtime\iwzmap-bake-venv`).
Everything below is therefore measured on C1's existing frames and build outputs (`C:\studio-data\sz\film\control\emit_b_*`, `s_b_*`, `s_diag`),
read in code, or built and unit-tested without the game. No frame of this lot is new; no pair of item 7 exists.
R2's data: `C:\studio-data\sz\film\control\r2\` (metric, pick, decoded lightmaps, tools, gate logs); the offline tools also in this branch,
`tools-source/iwzmap/station_zero/film/r2/` (`wb.py` world.bin reader, `pick2.py` per-surface black share, `pick4.py` per-pixel hit / lightmap uv /
decoded A, B / depth, `lmdds.py` an emit's installed lightmap decoded, `coplanar.py` layers at a pixel).

Correction to C1-CONTROL line 22: the room is placed by (-7850, -6750, -400) (`control_room.OFFSET`), not (-13000, -7000, 0) (C1 moved it, the
note kept the first value).

## 0. The metric (built, measured)

`python control_compare.py metric <out.json> <stock dir> label=dir[,label=dir...] [--names ...]` (SDK `film/control_compare.py`): per band of the
frame (ceiling rows 0-30 %, wall 30-70 %, floor 70-97 % = LIGHTING-GAP's floor band), on LINEAR values (sRGB decoded): mean luminance, mean
chromaticity, local contrast (mean |log2 lum - log2 9x9 box mean|), black share (display <= 1.5/255); one distance per pose (per band |log2 lum
ratio| + 10 x chroma distance + |log2 contrast ratio| + 2 x black share difference, averaged, plus the 16 x 9 tile-grid layout term with the mean
level removed); the registration of C1 (phase correlation of edges) with a flag when the shift exceeds 8 px or the edge match is under 0.25.
Stock against itself gives 0.00 at every pose.

Baseline (C1's last builds; `r2\metric\m0_baseline.md`):

| pose | frame | ceiling | wall | floor | floor b/r | floor contrast | black % | distance | reg |
|---|---|---|---|---|---|---|---|---|---|
| 1 | stock | 0.0363 | 0.0917 | 0.1021 | 0.73 | 0.207 | 0.0 | - | - |
| 1 | b_bounce | 0.0699 | 0.0875 | 0.0158 | 0.76 | 0.153 | 20.7 | 5.68 | 0,0 / 0.44 |
| 1 | b_baked | 0.0699 | 0.0837 | 0.0159 | 0.75 | 0.154 | 21.7 | 5.72 | 0,0 / 0.45 |
| 2 | stock | 0.0329 | 0.0654 | 0.0433 | 0.48 | 0.151 | 0.0 | - | - |
| 2 | b_bounce | 0.0443 | 0.0962 | 0.0581 | 0.28 | 0.222 | 10.9 | 4.17 | 0,0 / 0.55 |
| 5 | stock | 0.0248 | 0.0537 | 0.1134 | 0.74 | 0.195 | 0.0 | - | - |
| 5 | b_bounce | 0.0401 | 0.0673 | 0.0089 | 1.05 | 0.109 | 40.1 | 7.56 | 0,0 / 0.34 |

Mean distance over poses 1, 2, 5: b_bounce 5.80, b_baked 5.79, b_bounce_occ 5.83. The diag build (draft bake, probes in view, poses 1 and 2 only,
not a baseline): 3.09 against b_bounce's 4.92 on the same two poses; its floor band 0.036 (b_bounce 0.016) with 0 % black.

## 1. The black floors and vaults (cause NOT found; three separate statements)

- PROVEN: the lightmap reaches the build correctly and the black does not follow it (below).
- MEASURED: the lifted room is in no probe room: a flaw of the control document, fixed for the next build (`control_room.build(probe_room=True)`,
  Studio `settings.build.probe_rooms`).
- HYPOTHESIS, not supported strongly by the data: that the missing probe room makes the black. Against it: in the same room, a third of surface
  268 is lit and the floor surfaces 1596 and 1129 are 0 % black; floor black share RISES with the light the lightmap predicts (40 % where it is
  under 0.06, 84 % between 0.06 and 0.15). What the black follows is a region of the world: 20 floor cells (48 units) seen black from both
  pose 1 and pose 5, none lit from both, 3 that differ; not the view.

What is ruled out, each by measurement on C1's builds:
- **Not a material or technique set.** The compile logs of the black build and the drawn diag build are identical line for line (numbers and work
  paths normalised, material lines included). Per surface (offline ray pick of every 10th pixel into the built world.bin, `r2\tools\pick2.py`): the
  floor surface 268 (`w/concrete_bare_patches_clean_03`) is 66 % black at pose 1, and two other surfaces of the same material are 0 and 5 % black;
  `w/concrete_wall_grunge_01` surfaces range 0 to 46 %. Black is spatial inside a surface.
- **Not the lightmap's content.** The installed DDS set (decoded with texconv, `r2\tools\lmdds.py`) equals bake.npz at the floor's texels; the
  texels are valid; D (dominant direction) points out of the floor (D.z 0.86 on black and lit pixels alike). In the baked variant the floor
  pixels with the STRONGEST baked light are black: B >= 0.5: 49 % black, B < 0.01: 11 % (pose 1, `pick3.py`); at pose 5 floor pixels with B > 0.2
  are 94 % black. Picture: `r2\pick\floor_pred_vs_black_1.png` (left: the light the lightmap predicts on the floor, two bright pools; right: red =
  black on screen, green = lit; the pools are red).
- **Not a coplanar layer.** No second world surface within 1 unit of the floor at any sampled pixel, black or lit; no static model of the room's
  537 is a floor cover.
- **Not distance fog.** Floor black share by distance at pose 1: 42 % (0-150), 68 % (150-300), 79 % (300-450), 8 % (600-800): no threshold.
- **Not the bounds, the index ranges or the normals** of the world surfaces (checked on the floor surfaces against their vertices).

What is measured about where the black is:
- By height at pose 5: floor (z -120..-100) 88 % black, walls (z -100..0) 2 %, upper walls 18 %, vault (z 200..300) 70 %: mostly floor and vault,
  but not every floor surface (above).
- **The lifted room is in no probe room.** The build's 9 probe / lighting rooms (`probes.txt`, compile log "probes: room 0..8") all lie in the base;
  the 156 template instances are parked at 1e6 (`iwzmap.cpp` neutralize_reflection_probes, read at 785ba75). 10.8 % of the control build's drawn
  area (the whole lifted room) is in no room; the Arcade build 0.9 %. A room gets a probe and an ambient room only from a zone
  (Studio `basegame.py:249-256`); `control_room.build` gives the room no zone on purpose (TOOL-FAULTS C1-2). So C1's pairs measured a room
  without a reflection probe or an ambient room: not the pipeline as a real section gets it.
- Inferred, NOT proven: the floor shader scales the probe's reflection by `lum(E toward the reflection) / SH(probe)` (LIGHTING-GAP C2). A pixel
  outside every probe volume gets no valid probe; on floors and vaults (reflection vector up or down) the term breaks and the pixel goes black;
  on walls it does not. The diag build is the open contradiction: same probe rooms, floor drawn. It differs from the black build in two things at
  once (draft bake, extra geometry: world hash 5edf... against 37c0...), and its draft bake was cleaned with its live folder, so it cannot be
  compared offline. Picked against the diag's own world.bin (`r2\pick\diag_1d.csv`): in the old black region the diag frame mostly shows C1's
  re-added floor mesh (z -113, 1,543 px) and slabs (z -110), but the lifted floor itself (z -114) is on screen in 424 px of the frame (250 of them
  inside the old black region), 0 % black. The diag build draws the same lifted floor the final builds draw black: E3 decides between bake and
  document. The diag's probe rooms are the same 9 as the black builds' (in no room either), which also argues against the probe hypothesis.

Ready to run when the dumps and a compiler are back (one session, four documents, `forge sense` first; numbers by `control_compare metric`):
- E1 (single variable, first): `control_doc --mode bounce --base-only` (now with the probe room row
  `room -8000 -4800 -170 -6590 -3350 360 0.7 0.65 0.55 0.6` in probes.txt only: the compiler reads probes.txt apart from lighting.txt,
  `iwzmap.cpp:3109`, row format `:633-636`) against the same with `--no-probe-room`, both on one draft bake. A zone is not the route: an island zone
  over the room is refused (C1-2).
- E2: the same document with `settings.build {"compiler": {"env": {"IWZ_PROBES": "template"}}}` (L1's route d).
- E3: the 2 x 2: document {b_bounce, diag} x bake {draft, final}, to close the diag contradiction.
- E4 if E1 to E3 do not decide: `forge capture` at pose 5 of b_baked, pixel history of a black floor pixel (the probe index and the SH term).
- Offline, next: correlate the black floor cells with the world-space fields the build writes (the light grid's kept and dropped cells,
  `bake.npz grid`, `lighting.txt`; the Umbra tome's cells).
New in Studio meanwhile: the bake's answer carries `probe_coverage` and warns above 2 % of the drawn area in no room (`studio/bake.py`, unit test).

### Resume (28 Nov, data back): checks before the 2 x 2, and the prediction written before it ran

(a) What `draft` changes (Studio `bake.SETTINGS`, SDK `bake/lmbake.py`): gather rays 16 against 144 (C1's final: the recipe's 256), light grid rays
64 against 256; direct light 3 x 3 samples in both (`direct_sub` 3). The SAME texel (8), atlas packing (`pack`), pages (one atlas), value range and
encoding (secondary BC6H_UF16 two halves, secondunorm R8G8, primary BC4; `lmbake.py:544`). Nothing of how the engine reads the bake changes.
(b) Black pixels in lightmap ATLAS space (C1's b_baked, floor pixels only, `pick4.py`): no pattern. By atlas v band black is 39 to 80 % (pose 1)
and 89 to 100 % (pose 5) in every band; by chart size 41 to 89 % / 83 to 97 %; by stored light level 35 to 86 % / 91 to 98 %; 31 (pose 1) and 58
(pose 5) charts are part black, part lit. Black follows world position (20 floor cells black from both poses, none lit from both).
Prediction for the 2 x 2: draft and final give the same black (no encoding, range or atlas difference to act through); only the probe room can
move it, and the diag build (same probe rooms, floor drawn) argues it will not. If all four cells keep the black: stop, the cause is in the
document's geometry (what the diag document adds) or in the engine's draw, not in the bake.

## 2. Blend materials (found where the data is lost; carrying it needs the dumps and a compiler patch)

- A stock blend material (`*622n_274n`, map-local) is a layered material: a base plus decal layers. The lift records them: `*387n_86n_354n_362n` =
  `w/concrete_wall_brown_02_wet_less` + `w/concrete_stain_01_dec_wet` + `w/ls_conc_cracks_01_dec_nodsp` + `w/t7_decal_grunge_garbage_spread_01`
  (prefab.json `materials`); 187 such materials, 19,694 of the room's 119,365 vertices.
- **Vertex colours that vary only on blend surfaces exist in the lifted prefab and are dropped after it** (that they are the layer weights is
  not established). `surfaces_extra.bin` holds a colour per vertex: on blend surfaces R 255 and G / B / A graded (means 157 / 78 / 7, 0 % plain
  white), on plain surfaces 99.9 % white. Studio's renderer notes say the engine binds a second vertex buffer (slot 1, the layer stream) at the
  surface's `vertexLayerData` offset when the technique's input layout reads it (`C:\studio\view\renderer.md` line 159): the layered techniques read
  the layer stream; whether also the colour, not read. The store cache keeps cp_disco's transient zone (`store\cache\cp_disco\assets\
  transient_zones\cp_disco.gfxmap_tr`), where the stock layer bytes per vertex can be read without the dumps (not done). Studio drops them at three places:
  `Prefab.surfaces()` never reads the colour (`studio/prefab.py:288-291`); `expand_object` builds records without it and swaps the blend for its base
  (`render_material`, `:392-398`, used at `:531`); the SDK's world writer writes 255,255,255,255 for every vertex (`mapgen.py:117`).
  The lift itself copies a cut triangle's colour from its first vertex instead of interpolating it (`prefab.py:1335`).
- **The compiler copies the vertex colour unchanged** (world.bin vertices are GfxWorldVertex: `iwzmap.cpp:531, 2425, 3051`): no patch for colour.
- **The compiler zeroes the vertex layer stream**: `tz->vld` is 16 zero bytes per vertex (`:2427-2428`) and every surface's
  `tris.vertexLayerData = 0` (`:2188`). Stock layered surfaces have a non-zero offset (the lift records `layered: true` from it, `prefab.py:1353`); the
  layer bytes themselves are NOT in the world database or the prefab (only the offset). Whether IW7's layered techniques read the colour, the
  layer stream, or both is not established: SDK `sz2_materials.py:203` records the same failure for a stock puddle ("reveal/v0 blend needs vertex
  alpha or reveal data").
- **The material file exists**: `rooms/assets.material_record` finds a `*` material's dump json by `_file_key` (`*` -> `_`) with its technique set
  and layers (`json_zone: cp_disco` for every one of the room). The SDK's kit import looks for `materials/<name>.json` with the `*` in the name
  (`kit_import.py:290`), which cannot exist on Windows.

Patches, in order (none applied: each needs the dumps or the compiler to prove):
1. Studio `prefab.py` `surfaces()`: read `(f32, u32 colour)` per vertex after the tangents into `rec['col']`; `_lift_surfaces`: carry the colour
   through `clip_triangle` as four interpolated floats instead of `mesh['colors'][t[0]]`.
2. Studio `expand_object`: an object option `blend: 'keep'` (default `'base'` until proven): material = the `*` name, records get `cols`
   (per triangle, per corner, RGBA bytes).
3. SDK `blender/blend_core.py` `add()`: `cols = rec.get('cols')`, the colour joins the weld key and the vertex tuple; `mapgen.py:117`: pack that
   colour instead of `255, 255, 255, 255` (mapgen is not in this brief: lead).
4. SDK `kit_import.py:290` and the techset/state lookups below it: find `materials/<name with * -> _>.json`; the zone's asset keeps the `*` name
   (how ZoneTool names the file of a `*` material on load: to read in the compiler's material loader before writing the line).
5. Compiler (`x64-zt-weapons` branch `claude/zt-serve`, `iwzmap.cpp`): world.bin version 2 with an optional per-vertex layer stream (N bytes a
   vertex, N read from a stock dump: `vertexLayerDataSize / vertexCount` of cp_disco, logged by the existing IWZ_INJECT_SURFACES line at `:3047`);
   in `read_world` (`:517`) read it; at `:2427` fill `tz->vld` from it instead of zeros; at `:2188` set `surfaces[i].tris.vertexLayerData` to the
   surface's offset into that stream for a layered material, 0 otherwise. The worldkit dumper (`worldkit/iw7_dump.py:228` reads `vldData`) must
   then store the layer bytes per lifted vertex (`surfaces_extra.bin` v2).

## 3. Decals, glass, shadow casters (read, not changed)

`render_material` returns None for any material not under `w/` (all `wc/` decals and glass: 212 triangles) and for `caulk`, `shadowcaster`,
`nodraw`, `clip` (`prefab.py:389-398`); `LIMITS` says every lifted surface is drawn lit opaque (decal and translucent draw classes lost). The
compiler takes a surface's flags and sort from a template surface of the same material, else a fallback lit opaque one (log: "is not used by
the template world; using template surface defaults"). Needed: (a) Studio keeps `wc/` materials as render records with a `draw: 'decal'` flag;
(b) the compiler, for a material not in the template, takes flags / sortKey from the material's own sort class (decal, translucent) instead of
the lit opaque fallback (`iwzmap.cpp` at `:2184`, `by_material` / `fallback`); (c) `caulk_shadow` triangles as baker-only occluders: a record
mode `occluder` that the emitter writes into the baker's scene (not world.bin). Not built: each needs a build to verify the sort.

## 4. Baked shadow of props of other zones (built, unit-proven; frame number pending)

Studio `bake.run` now gives the baker every dump root: the template's, then each root of the emit's `build.json` `kit.dumps` (document and base
merged by the emit), `{runtime}` resolved, existing folders once, missing ones named in the answer's warning (`dump_roots`). The bake key version
is 4 so bakes made without those shadows are made again. Tests: `tests/test_bake.py DumpRoots` (four tests: order and dedup, no kit, the job and
the warning, and the SDK's `occluders.model_bounds` finding a kit zone's model through the roots that it misses with the template root alone).
What the baker can read: the model's bounds box only (`bake/occluders.py`, `ztdump.read_xmodel()['bounds']`); a hull from the model's collision or
lod surfaces is not read today. The bench-foot ratio (0.994 -> 0.571 in C1's variant) is NOT re-measured: the bake Python and the dumps are gone.

## 5. Ambient occlusion on the client cells (plumbing built; not shown in a frame)

Forge's `live start` takes `--dvar-at-launch name=value` (`C:\forge\forge\cli.py:950`, `launch.py`). Studio now passes the document's
`settings.live.dvars_at_launch` over the environment's `STUDIO_LIVE_DVARS` (`studio/live.py session_dvars`, `game/iwzlive.py Session.start`;
none by default; values checked; test in `tests/test_cli_live.py`). To run: `"settings": {"live": {"dvars_at_launch": {"r_ssao": "MDAO"}}}` on
the control document and on stock's frame request (`forge run ... --dvar-at-launch r_ssao=MDAO`). The value `MDAO` is the one C1 read in a server
cell's config_mp.cfg; that it turns the occlusion target on is unproven (C1's RenderDoc script `control\ao\rdoc_ssao.py` checks it; the
captures it read are deleted).

## 6. Reflection probes (route d / b): not started

Precondition found in 1: the lifted room must first be in a probe room at all. Then route d (`IWZ_PROBES=template`) is not "the stock room
with its stock cube": the template is cp_zmb, not cp_disco. Carrying the room's own cp_disco probe needs the cube from cp_disco's
`reflection_probe_array` (Studio's store cache `C:\studio-data\store\cache\cp_disco\assets\images` still holds cp_disco's images, not checked
for that array) and a compiler mode that writes a given cube into a room's slot (beside `neutralize_reflection_probes`, `:713`).

## 7. Verdict: not done

No new frame exists. The table above is the baseline only. Note for the lead: `C:\studio-data\store\cache\cp_disco\assets\vision\cp_disco.vision`
exists (LIGHTING-GAP C3 says no cp_disco vision is on this PC). Studio gate: before 790 tests 0 failures 21 errors, after 796 / 0 / 21, on the final head d2261c6 797 / 0 / 22 (the same causes, Variants.setUpClass counted twice:
the deleted template dump and bake Python; `r2\gate\gate_{before,after}.log`); the classes behind those errors ran neither time, so the gate must
run again on this head before merge. Decision: bake key v4 makes every remembered bake be made again, and none can be until the bake Python is back.
What still differs between stock and ours, with its owner:
black floors and vaults (cause not found; the lightmap is ruled out; E1 to E4 decide: R2); blend layers (data found in the
prefab; Studio patches 1-2 R2, mapgen 3 lead, kit import 4 R2/lead, compiler 5 compiler owner); decals / caulk (3: Studio and compiler);
baked shadow of props (built; frame measure pending); SSAO (plumbing built; frame pending); probes (6); content the lift cannot carry
(far geometry outside the box, effects, the sky, the 115 entities).

## 8. 2 x 2 result (worker R2b, 28 Nov 2026; data back, one batch)

Gate first: Studio `claude/film-parity` head d51d97b (origin/main had not moved, no merge): 832 tests, 0 failures, 0 errors, 18 skipped, 13.4 s
(`r2\gate\gate_resume.log`; the earlier 21-22 errors are gone, they were the deleted files). Not merged to Studio main.

Batch `r2\run_batch2.py` (`r2\batch2.json`, one background job, about 40 min): control room, `--mode bounce --base-only`, kit dump roots on in every
cell (bake log: 824 occluder boxes), draft bake (no remembered bake) or final bake (texel 8, 256 rays, 3 bounces), probe room (`probe_rooms` row in
probes.txt) on or off, frames at stock poses 1, 2, 5 (`ctl_subway_east_1/2/5` = stock `subway_east_1/2/5`), 5 cells, all shots ok and not stale.
Metric: `control_compare.py metric` against `stockref\cp_disco` (`r2\metric\m2_cells.md`; `analyze2.py`).

| pose | cell | ceiling lum | wall lum | floor lum | floor b/r | black % | distance |
|---|---|---|---|---|---|---|---|
| 1 | stock | 0.0363 | 0.0917 | 0.1021 | 0.73 | 0.0 | - |
| 1 | C1 b_bounce (reference, no kit roots, no probe room) | 0.0699 | 0.0875 | 0.0158 | 0.76 | 20.7 | 5.68 |
| 1 | draft, probe room | 0.0678 | 0.0796 | 0.0156 | 0.77 | 22.2 | 5.77 |
| 1 | final, probe room | 0.0681 | 0.0798 | 0.0157 | 0.76 | 22.2 | 5.77 |
| 1 | draft, no probe room | 0.0677 | 0.0795 | 0.0156 | 0.77 | 22.2 | 5.77 |
| 1 | final, no probe room | 0.0681 | 0.0797 | 0.0156 | 0.76 | 22.2 | 5.77 |
| 1 | final + probe room + r_ssao MDAO | 0.0681 | 0.0798 | 0.0157 | 0.76 | 22.2 | 5.77 |
| 2 | stock | 0.0329 | 0.0654 | 0.0433 | 0.48 | 0.0 | - |
| 2 | C1 b_bounce | 0.0443 | 0.0962 | 0.0581 | 0.28 | 10.9 | 4.17 |
| 2 | draft, probe room | 0.0404 | 0.0898 | 0.0573 | 0.28 | 12.7 | 4.16 |
| 2 | final, probe room | 0.0405 | 0.0899 | 0.0576 | 0.28 | 12.6 | 4.16 |
| 2 | draft, no probe room | 0.0405 | 0.0898 | 0.0573 | 0.28 | 12.7 | 4.16 |
| 2 | final, no probe room | 0.0405 | 0.0898 | 0.0576 | 0.28 | 12.6 | 4.16 |
| 2 | final + probe room + MDAO | 0.0405 | 0.0899 | 0.0576 | 0.28 | 12.6 | 4.16 |
| 5 | stock | 0.0248 | 0.0537 | 0.1134 | 0.74 | 0.0 | - |
| 5 | C1 b_bounce | 0.0401 | 0.0673 | 0.0089 | 1.05 | 40.1 | 7.56 |
| 5 | draft, probe room | 0.0389 | 0.0629 | 0.0088 | 1.06 | 40.9 | 7.54 |
| 5 | final, probe room | 0.0392 | 0.0631 | 0.0087 | 1.09 | 40.8 | 7.56 |
| 5 | draft, no probe room | 0.0389 | 0.0629 | 0.0088 | 1.06 | 40.9 | 7.53 |
| 5 | final, no probe room | 0.0392 | 0.0631 | 0.0087 | 1.08 | 40.8 | 7.56 |
| 5 | final + probe room + MDAO | 0.0392 | 0.0631 | 0.0087 | 1.09 | 40.8 | 7.56 |

Mean distance over poses 1, 2, 5: C1 5.80; draft+probe 5.82; final+probe 5.83; draft no probe 5.82; final no probe 5.83; final+probe+MDAO 5.83.
**The black floor share did not move in any cell** (22 / 13 / 41 % at poses 1 / 2 / 5, as C1's 21 / 11 / 40 %). **The prediction held**: draft and
final give the same black, and the probe room did not move it (probe room on against off, draft cells: 22.2 / 12.7 / 40.9 % against 22.2 / 12.7 / 40.9 %).
Frame of the final + probe room cell, pose 5 (stock left, ours right: `r2\metric\look5_pair.png`): ours shows the platform floor, the track bed, the vault and
the tunnel mouths black; the car bodies, walls and the far lit room are drawn.

Other numbers of this batch:
- Bench-foot ratio (`bake_probe.py`, kept final bake of p1_final against C1's emit_b_bounce, same floor box, 4 bench props): near / far light
  0.895 without kit roots, 0.442 with (feet E 0.0116 -> 0.0001). C1's variant gave 0.994 -> 0.571; same direction and size: the bench feet are now
  baked dark. It moved no frame number above (distance +0.03).
- SSAO: stock with `r_ssao=MDAO` set before the first camera (`forge capture --set`) and plain stock: the occlusion target is 255 at every pixel in BOTH
  (share_255 1.0, mean 255): the dvar set that way did not turn occlusion on. Our capture (`cap\ours_ssao`, 69 actions) has no occlusion target at all
  (`ao\summary.json`: empty). Stock frames with `--dvar-at-launch r_ssao=MDAO` (plan run, `stock_mdao\`) differ from the plain stock frames by a mean
  absolute 3.06 / 0.68 / 1.31 grey levels at poses 1 / 2 / 5 (not an occlusion look). So SSAO is not shown on either side by this route; the SSAO cell's
  metric equals the same cell without it. The RenderDoc check on the launch-time dvar was not done (only `--set` captures).

### What the diag document adds that the control document lacks (stop condition: every cell kept the black)

Read from `control\doc_diag\` and `control\doc_b_bounce\`: `map.json` is identical but for the name and the layer list; the diag has ONE more layer,
`ctl_diag.json`, all `mode: render`: (1) three flat slabs 40 x 40 x 2 units at z -111.88..-109.88 and three upright slabs 40 x 4 x 48 at z -113.88..-65.88,
each in one of three materials (`concrete_bare_patches_clean_03`, `concrete_wall_grunge_01`, `dt_tile_ceramic_white`), at x -6990..-6850, y -4230..-4146
(a material swatch row at the room's south edge); (2) `ctl_diag_floor_mesh`: a triangle mesh of `concrete_bare_patches_clean_03` at z -113 covering the room
floor from x -7162 to -6746, y -4284 to -3996, one unit above the lifted floor (z -114). So the diag differs from the control by NEW world geometry authored
in the document, not by any bake or probe setting. The cause of the black is therefore not in the bake (draft = final), not in the probe room (on = off), not in
the kit roots, not in SSAO: it is in the lifted floor and vault surfaces as the lift writes them, or in the engine's draw of those surfaces. Next step: bake and
shoot the control with ONLY `ctl_diag_floor_mesh` added, then only the slabs, to find which row removes the black; then read what differs between the lifted
surface 268 and the mesh in world.bin (flags, sort key, vertex colour, lightmap uv); E4 (pixel history at pose 5) is the other route. Not done here (stop rule).

## 9. Ranking of the pipeline gaps by the metric distance to stock that closing them removed (this batch)

Distance baseline: 5.80 (mean, poses 1, 2, 5).

| gap | removed | basis |
|---|---|---|
| black floors and vaults | not measured (cause not found) | the metric is dominated by them: black share 22 / 13 / 41 %, floor luminance 0.016 / 0.058 / 0.009 against stock 0.102 / 0.043 / 0.113 |
| probe room | 0.00 (5.82 on, 5.82 off, draft; 5.83 / 5.83 final) | measured |
| draft against final bake | 0.00 to +0.01 (5.82 draft, 5.83 final) | measured; final is not closer |
| prop shadows / kit dump roots | +0.02 (C1 5.80 without, 5.82 to 5.83 with); bench feet ratio 0.895 -> 0.442 | measured: real in the bake, invisible in this metric |
| SSAO (`r_ssao` MDAO) | 0.00 | measured, not engaged: the occlusion target stays 255 on stock too |
| blend layers (32.7 % of the lifted surface) | not measured | needs patches 1 to 5 (HOLD) |
| decals, glass, caulk shadow casters | not measured | needs the draw-class patches (HOLD) |
| probes cube (the room's own cp_disco cube) | not measured | needs the compiler mode of section 6 (HOLD) |
