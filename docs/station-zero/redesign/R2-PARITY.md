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
| black floors and vaults = the foreign world materials missing from the zone | **-3.22** (5.83 -> 2.61 mean; per pose 5.77 -> 2.99, 4.16 -> 2.30, 7.56 -> 2.55; black share 22 / 13 / 41 % -> 0 / 0 / 0 %) | measured, section 12: `claude/film-blend` d1a3911 brings the room's w/ materials into the zone |
| probe room | 0.00 (5.82 on, 5.82 off, draft; 5.83 / 5.83 final) | measured |
| draft against final bake | 0.00 to +0.01 (5.82 draft, 5.83 final) | measured; final is not closer |
| prop shadows / kit dump roots | +0.02 (C1 5.80 without, 5.82 to 5.83 with); bench feet ratio 0.895 -> 0.442 | measured: real in the bake, invisible in this metric |
| SSAO (`r_ssao` MDAO) | 0.00 | measured, not engaged: the occlusion target stays 255 on stock too |
| blend layers (32.7 % of the lifted surface) | about 0.00 on the mean (2.61 for `keep` and `base` alike; frames differ by a mean 2.7 grey levels, 4.6 % of pixels above 8 at pose 5) | measured, section 12: the layers draw but the metric does not see them at this size |
| decals, glass, caulk shadow casters | not measured | needs the draw-class patches (HOLD) |
| probes cube (the room's own cp_disco cube) | not measured | needs the compiler mode of section 6 (HOLD) |

## 10. "Not drawn" tested (worker R2b, 28 Nov 2026): the black surfaces ARE drawn; the fault is in how the stock cp_disco materials draw in our map

Four cells, all `--no-bake` (UNLIT: no lightmap) on the control document with the probe room, poses 1 and 5, one batch each (`r2\batch3.json`, `batch4.json`,
scripts `run_batch3.py`, `run_batch4.py`, `shots_nobake.py`; sheets `r2\metric\sheet3_pose5.png`, `sheet4_pose5.png`; frames `r2\s_u_*`).

### Measured
- **The unlit build shows the same black as the baked ones**: black share 38.5 % (pose 1) and 49.7 % (pose 5), the same frames as the 2 x 2 to the eye. With
  section 8 (draft = final, probe room on = off) the black does not come from the bake, its range or its encoding, nor from the probe room.
- **Not Umbra culling.** `IWZ_TOME=conservative` (scene sized boxes, no distance cull; compile log "generated conservative Umbra tome") gives a frame
  identical to the culling tome's, pixel for pixel in the black share (38.5 / 49.7 %).
- **The black surfaces are drawn.** One document-only change: every surface of the lifted room drawn with one plain material (`w/iwz_tile_cream`, a
  temporary hook in `studio/prefab.py render_material`, reverted, not committed; the emit memo had to be bypassed with `STUDIO_EMITCACHE=0`, otherwise it
  returned the previous cell's expansion: the first flat attempt, `u_flat`, was this stale memo and showed nothing). Result: black share 0.1 % / 0.0 %, mean
  grey 58 / 71 against 34 / 24: the floor, the vault, the car's door and end panels, the tunnel mouths are all there, lit, in the same geometry, same
  tome, same vertices (`r2\pairs\flatmat_1.png`, `flatmat_5.png`, read: pose 5 shows a tiled floor with the light pool, the car with its doors open onto
  the far lit rooms, the vault and girders overhead). So the "missing vault, panels, floor" of `ours_5.png` are drawn surfaces whose stock materials come out black.
  Geometry, visibility data, the tome, the lightmap and the probe room are all ruled out as the cause; the lifted surfaces draw correctly with another material.
- **Black share by material** (pixel picks of C1's b_baked at poses 1 and 5, 14,335 + same px, `r2\pick\baked_*d.csv`): the materials the template world
  uses (`dt_tile_ceramic_white`, `metal_corrugated_01`, `fac_tile_black_01`, `metal_painted_01_black`) are 0 % black; the stock cp_disco materials the
  template does not use ("not used by the template world; using template surface defaults", 124 in the compile log) are 12 to 97 % black
  (`concrete_bare_patches_clean_03` 83 %, `concrete_wall_grunge_01` 53 %, `linoleum_floor_tiles_noline_01` 97 %, `frag_metal_door_rusty` 96 %,
  `frag_metal_trim_gray` 52 %), with exceptions that are dark or flat anyway (`plastic_dark_matte` 1 %, `cp_disco_subway_sign_01` 0 %). The cream material is also
  "not used by the template" and draws fine, so "foreign" alone is not the cause; the cause is something of the cp_disco materials.
- Vertex data is not it: floor surface 268 (66 % black) and 1596 (0 % black) carry the same packed normal 0xfff80200, tangent 0xe00803ff, binormal
  sign and colour; surface bounds in world.bin equal their triangles' (0 of 1,676 differ by more than 1 unit); black share does not follow
  the index buffer (base_index / 65,536 bins 0.27, 0.10, 0.18, 0.27) or the first vertex.
- **Console variants proved nothing about the clear colour**: `set r_clear 2` / `3`, `r_clearColor 1 0 1 1`, `r_drawWorld 0 / 1`, `r_umbraMinObjectContribution 0`
  were accepted by the live link (`hud studio_cmd`, ok) but changed no pixel, `r_drawWorld 0` included: those names are not dvars of this client, or are not
  honoured. No dvar dump or table was found on this PC (docs, SDK, Forge searched). Not needed now: the flat-material cell answers the same question.
  (A command with `"` is refused by the link: `an op holds only printable ASCII and none of | ; " \`.)

### Read (compiler, `x64-zt-serve`, `iwzmap.cpp`, read only)
- Culling is not the route: `build_tome` (`:112-246`) writes one tile, one cell, every object with its own bounds; world surfaces user id k (class 0),
  distance never; the tile scale is the scene extent / 65,536. Surface bounds come from the triangles (`:2204-2205`). `node.surfaceCount = own` and the single
  aabb leaf (`:2437-2452`) cover every surface. All consistent with the measured: drawn.
- A surface of a material the template does not use is built from a template surface "of the same material, else `fallback`"
  (`:2160-2186`: `surfaces[i] = w->dpvs.surfaces[tpl]; draw_surfs[i] = w->dpvs.surfaceMaterials[tpl]`), only the material pointer, first vertex, vertex /
  triangle counts, base index and max edge are replaced; its flags, lightmap index, sort and `objectId` bits are the template surface's.
- Zeroed by the compiler and NOT in the tome path, so candidates for what cp_disco materials need and cream does not: `w->heightfieldCount = 0`
  (`:2334-2335`, "no heightfields", also under `IWZ_KEEP_UMBRA`), the vertex layer stream `tz->vld` 16 zero bytes a vertex and every
  `tris.vertexLayerData = 0` (`:2188`, `:2427`; the layered / blend techniques read it), decal volumes and volumetrics (`:2328-2333`), the per-surface lighting
  data. None is proven.

### Hypothesis, not tested
The black comes from the cp_disco material techniques (techset, state bits, images, or the inputs their shaders read: heightfield, layer stream, a
second lightmap channel, per-material draw data) running in a map that does not give them those inputs. Why it is spatial inside one surface is not explained
by this (a shader input that varies in world space, such as a heightfield lookup, would explain it; an image or tangent problem would not).

### What to do next (lead decides; no compiler edit made)
1. Bisect by material: swap the room's materials in groups (cream already proven) with a template-used material (`w/dt_tile_ceramic_white`) and with single
   cp_disco materials (`concrete_bare_patches_clean_03` alone, `linoleum_floor_tiles_noline_01`, a 97 % black one), to see which materials turn black and whether
   any of them is black everywhere or only in regions.
2. `forge capture` at pose 5 of the baseline and a pixel history on a black floor pixel: the draw's technique, its bound textures and constants (which one is
   black or zero) decides between heightfield / layer stream / image. This is the E4 of section 1, now with a defined target.
3. If a heightfield or the layer stream is the input: the compiler change is in `iwzmap.cpp` `build_gfx`, `:2334-2335` (keep or build `heightfields`) or
   `:2427-2428` and `:2188` (a real layer stream); the exact data to write has to be read from cp_disco's own world first.

## 11. RenderDoc and the material file check (worker R2b, 28 Nov 2026): the cp_disco world materials are name stubs, nothing is brought into the zone

Cell: control document, probe room, `--no-bake` (UNLIT; the black is identical to the baked builds, section 10), `STUDIO_EMITCACHE=0`, forge capture at pose 5
(`r2\cap\ours_p5\cam1.rdc`, D3D11, 879 draws / dispatches / clears, `r2\ao\enum\enum.json`). The capture is darker than the live shot (no studio vision: 64 %
black) and shows no lit floor pool, so no "lit pixel of the same surface" exists in it; the lit comparisons below are other surfaces. Tools (saved in
`r2\tools` and in this branch under `tools-source\iwzmap\station_zero\film\r2\`): `rdoc_pixel.py` (qrenderdoc offline: for chosen pixels, the draws whose
post-vertex-shader triangles cover them, and for chosen events the pixel shader, bound shader resources with size, format and content statistics, and the
constant buffers), `rdoc_enum.py` (every draw: event, indices, outputs).

### Measured
- **Material file check** (the control build's own live folder, `next\cp_iwz.kit_import.json` and `cp_iwz.emit\custom_materials.json`; the build's work
  folder is cleaned by Studio, so this is the live folder of a fresh unlit build of the same document): the kit import brought 314 new and 25 shared
  materials, every one a model material (`mo/...`, `mopw/...`); **0 of them is a `w/` world material**, 3 images and 3 techsets in all. The
  `w/concrete_bare_patches_clean_03`, `w/linoleum_floor_tiles_noline_01`, `w/concrete_wall_grunge_01`, `w/frag_metal_door_rusty` the room's surfaces use are in
  neither (the names appear only in the world surface list). `custom_materials.json` (65 SDK-built materials: `art_*`, `tile_cream` = `w/iwz_tile_cream`, ...) is where
  the cream that draws fine comes from: it is built into the zone with its own techset and images. The compile log says it for 124 materials: "is not used by the
  template world; using template surface defaults". The compiler gives such a surface only a **name stub** of the material (`iwzmap.cpp:2160`
  `materials[i] = name_stub<Material>(mem, src.materials[i])`), so the engine must find `w/concrete_bare_patches_clean_03` in a zone that is loaded with the map.
  The template's own materials (`dt_tile_ceramic_white`, `metal_corrugated_01`: 0 % black) are in the template zone; cp_disco's are in no loaded zone.
  This agrees with the blend-proof worker's finding for the `*` layered materials, and with the black share by material of section 10 (template-used 0 %,
  cp_disco 12 to 97 %, built-in custom cream 0 %).
- **RenderDoc: the floor is not rasterised in the opaque pass.** The black floor pixel (640, 650) is covered by no draw of the opaque scene pass into the
  G-buffer `83153` (events 1450 to 3226, 294 draws) except 3170 to 3226 (8 draws of 640 indices covering every pixel with 3 to 5 triangles: not surfaces),
  and by no earlier draw of the HDR target `83146`; the lit car panel (800, 430) is covered by its own small draws (events 1720 and 1732, 12 indices) and the
  vent (560, 565) by event 1706. The same holds for pixel (84, 532) of surface 268's region. The only draws that cover the floor pixel with a render target are
  the 8 light passes 6312 to 6368 (pixel shader 12438, 19 bound resources, one a 1 x 1 default (`texture5`), the occlusion target `83212` is
  uniform 255, the shadow depth `17136`...), which light what the G-buffer holds: nothing at those pixels (the HDR pixel before the pass is 0,0,0).
  So the floor's pixels are black because **no surface of the floor reaches the G-buffer pass**, not because it is lit black; with a plain built-in material
  (section 10, cream) the same triangles reach it.
- Caveat: coverage is tested on post-vertex-shader positions of each draw (works for the panel and the vent, so the method is sound); `PixelHistory` of
  this RenderDoc build returned only the last event (not used); the G-buffer pass draws report no pixel shader through the state interface of this script
  (`ps None`), so which shader and which images the car and the missing floor use in that pass is NOT read. The partial / spatial black inside one surface
  (surface 268: 66 % black at pose 1) is NOT explained by this: a missing material would hide a surface wholly. Open: the engine may draw a missing material
  with a default technique only in some passes or for some of the surface's draw batches; this needs a capture of the baked live cell (the capture here lacks the lit
  floor pool).

### Hypothesis (kept apart)
A surface whose material asset is unresolved (a name stub that no loaded zone defines) is skipped or drawn with the engine's default material in the G-buffer
pass, which leaves clear colour (black) behind it; the lit pass then lights nothing. Which one of the two, and why part of a surface survives, is not shown.

### The change (read, no edit; for the lead)
1. **Not the layer stream, not the heightfield, not the tome**: none of 2188 / 2427 (`vertexLayerData`, `vld`, branch `claude/zt-layers`), 2334-2335 (heightfields),
   2328-2333 (decal volumes) or 2353-2395 (tome) is involved: the same lifted triangles draw with a material that is in the zone.
2. **Studio / SDK side, bring the world materials**: `tools-source/iwzmap/kit_import.py:283-296` (`add_material`: `find(zone, 'materials/<mat>.json')`) links
   `mo/` model materials of the kit's models only. The world materials a document's surfaces use (`foreign_materials.json` written beside every emit by
   `studio/prefab.py:1175-1199`, "kit_import.py links models only; a --world-materials mode ... needed") need the same treatment: for every `w/...` in
   `foreign_materials.json` (and the lift's blend `*` materials, whose base `sub` is what `render_material` draws): copy the material json from its zone dump
   (`json_zone: cp_disco`), its techset (`techniqueSet->name`), the `.stateinfo/.statebits/.statebitsmap`, and every image it references, into the zone's
   source as the model materials are (`rep['materials']['new']`), so the compiler's name stub resolves inside the zone. Note `kit_import.py:290` looks for
   `materials/<name>.json` with the `*` of a blend name in the file name, which cannot exist on Windows (use `_file_key`).
3. **Compiler side (`iwzmap.cpp:2160`, and `:3074` for the second stub site)**: when the material asset is in the zone's source, the stub is enough (the linker
   resolves by name); nothing to change there if step 2 lands. If it must not be a stub, `name_stub<Material>` is where the real asset would be loaded.
4. A surface of a material the template does not use also copies a template surface's flags / sort / lightmap index (`:2160-2186`): not the cause of this black
   (cream has the same treatment) but worth keeping in mind for decal and translucent materials.

### How a frame proves it
Build the control with the room's `w/` materials brought into the zone (steps 2 above), `--no-bake`, same poses: the black share at poses 1 / 5 must fall
from 38.5 / 49.7 % to under 5 % (the cream cell gave 0.1 / 0.0 %) with the stock materials drawing; then `rdoc_pixel.py` on the same pixel must show the floor's draw in
the G-buffer pass (events 1450 to 3226) covering (640, 650); and the compile log must no longer print "is not used by the template world" for those names
without the material being in `cp_iwz.kit_import.json`'s `materials.new`. If the black stays with the materials in the zone, the hypothesis above is wrong and the
next suspects are the techset state (sort / flags copied from the fallback surface) and the images' streaming.

## 12. The control room on the fix (worker R2b, 28 Nov 2026): the black is gone, mean distance 5.83 to 2.61

Build: Studio `claude/film-blend` d1a3911 with origin/main merged (718ea33, pushed: it already had d51d97b, lacked 8c6900e), SDK `sz-blend` a368a54, compiler
`x64-zt-layers` `zonetool.exe`, `STUDIO_EMITCACHE=0`, control room with probe room, final bake (texel 8, 256 rays, 3 bounces), kit dump roots on, poses 1, 2, 5
(`r2\batch6.json`, `run_batch6.py`). Cells: (a) `v2_base` prefab `blend: "base"`, (b) `v2_keep` prefab `blend: "keep"`. Frames in `r2\s_v2_base`, `r2\s_v2_keep`;
pairs in `r2\pairs_v2` (`stock_N.png`, `ours_N_base.png`, `ours_N_keep.png`, N = 1, 2, 5, full resolution, no HUD; contact sheets `r2\metric\v2_pair_N.png`).
Metric: `r2\metric\m3_v2.md`.

### Before the run (file check on the builds)
`iwz_src\world_materials.json` of both builds (28,775 bytes, copies in `r2\v2\`) lists `w/concrete_bare_patches_clean_03`, `linoleum_floor_tiles_noline_01`,
`concrete_wall_grunge_01`, `frag_metal_door_rusty` and `dt_tile_ceramic_white`: all present. The compile log still prints "is not used by the template world; using
template surface defaults" 124 times (the same count as before: that line is about the template's surface defaults for flags and sort, not about the asset), and
`kit_import.json` still lists 0 `w/` materials among its 314 new model materials (the world materials travel by `world_materials.json`, not by the kit import).
Whether the zone itself now holds the material assets was not read from the zone (only the list and the frames).

### Measured: frames
| pose | cell | ceiling lum | wall lum | floor lum | floor b/r | floor contrast | black % | distance |
|---|---|---|---|---|---|---|---|---|
| 1 | stock | 0.0363 | 0.0917 | 0.1021 | 0.73 | 0.207 | 0.0 | - |
| 1 | before (p1_final, section 8) | 0.0681 | 0.0798 | 0.0157 | 0.76 | 0.153 | 22.2 | 5.77 |
| 1 | v2 base | 0.0396 | 0.0713 | 0.0400 | 1.09 | 0.161 | 0.0 | 2.99 |
| 1 | v2 keep | 0.0396 | 0.0712 | 0.0400 | 1.09 | 0.161 | 0.0 | 2.99 |
| 2 | stock | 0.0329 | 0.0654 | 0.0433 | 0.48 | 0.151 | 0.0 | - |
| 2 | before | 0.0405 | 0.0899 | 0.0576 | 0.28 | 0.222 | 12.6 | 4.16 |
| 2 | v2 base | 0.0405 | 0.0783 | 0.0749 | 0.39 | 0.224 | 0.0 | 2.30 |
| 2 | v2 keep | 0.0405 | 0.0783 | 0.0749 | 0.39 | 0.223 | 0.0 | 2.30 |
| 5 | stock | 0.0248 | 0.0537 | 0.1134 | 0.74 | 0.195 | 0.0 | - |
| 5 | before | 0.0392 | 0.0631 | 0.0087 | 1.09 | 0.108 | 40.8 | 7.56 |
| 5 | v2 base | 0.0498 | 0.0512 | 0.0966 | 1.17 | 0.168 | 0.0 | 2.55 |
| 5 | v2 keep | 0.0498 | 0.0512 | 0.0966 | 1.17 | 0.169 | 0.0 | 2.55 |

Mean distance over poses 1, 2, 5: C1 5.80, before 5.83, **v2 base 2.61, v2 keep 2.61**. Black share 0.0 % at every pose in both cells (expected under 5 %).
Registration match 0.73 / 0.83 / 0.84 (before 0.44 / 0.54 / 0.33): the structure now lines up with stock. Looked at (pose 5 pair, `r2\metric\v2_pair_5.png`, stock left,
ours right): the platform floor with the light pool and its tile joints, the girders and the vault, the car with its door openings and the lit rooms beyond, the end pillar
tiles are all drawn. Stock has what ours lacks: the graffiti and decals on the car, the floor dirt and wet patches (ours is a clean tiled floor); ours is colder and the far lit
room flatter.

Still apart from stock (bands): floor b/r 1.09 / 0.39 / 1.17 against 0.73 / 0.48 / 0.74 (ours bluer on the floor at poses 1 and 5), wall luminance 0.071 / 0.078 / 0.051
against 0.092 / 0.065 / 0.054, pose 5 ceiling 0.050 against 0.025 (twice as bright), floor contrast 0.161 / 0.224 / 0.168 against 0.207 / 0.151 / 0.195.

### Measured: `keep` against `base`
Same to the metric (2.99 / 2.30 / 2.55 in both); the frames differ by a mean 2.74 grey levels at pose 5, 4.6 % of the pixels by more than 8. So the stock layered
materials draw with their layers, and the visible effect on the control frames is small at this size and exposure (the eye may see more than the metric; not judged here).

### RenderDoc on (b), pose 5, floor pixel (640, 650) (`rdoc_pixel.py`, `rdoc_vslots.py`; capture `r2\cap\v2_keep_p5`, logs `r2\ao\kp*`)
- **The floor is in the G-buffer now**: the pixel is covered by two small opaque-pass draws, events 3314 (66 indices) and 3400 (51 indices) into `83096`, and by the lit
  pass draws 6905 (66) and 7016 (51) into the HDR target `83090`. Before the fix no draw covered it (section 11).
- The lit pass's pixel shader (133486, 23 bound resources) has three 256 x 256 BC7 material images bound, the lightmap images (primary BC4 4096 x 2048, secondary BC6
  4096 x 4096, secondunorm R8G8 4096 x 2048), the shadow depth, the occlusion target and the light grid volumes; none of the bound images is all-zero (statistics of
  the first mebibyte).
- **Slot 1 is NOT bound on the floor draws**: one vertex buffer (slot 0, stride 44: SV_POSITION, TEXCOORD0, NORMAL, TEXCOORD2). That floor material is plain, not layered,
  so no layer stream is expected. Over the capture's 912 opaque draws, 6 world-vertex draws (stride 44) bind a second buffer (slot 2, stride 8, 9 indices: not slot 1), and the 16
  draws with a slot 1 (stride 12) are a prop model (6,108 indices). **No world surface of this capture binds slot 1 or layer images**: "slot 1 bound, layer images bound" is
  NOT shown for a lifted world surface; it needs a view with a layered `*` surface and a pixel on it. The capture is also darker than the live shot (no studio vision).

### Ranking (section 9 updated in place)
Closing the foreign materials removed **3.22** of the mean distance (5.83 to 2.61) and all of the black. Closing the blend layers (`keep`) removed about 0.00 on this metric.
What remains of the 2.61 is named in the bands: the clean floor against stock's dirt, the missing graffiti and decals (decal draw classes: HOLD), the blue floor balance (probe
cube: HOLD), the ceiling and wall levels.
