# Lighting gap: Arcade (pass 8) against stock (rendering lead, 28 Nov 2026)

Research only: no repository edited, no build, no live session. One Forge request: two RenderDoc captures of stock
`cp_disco`, kept at `C:\studio-data\captures\lightgap_cp_disco` (1.16 GB; `cam1` subway east with power OFF, `cam2`
Lounge street: the capture tool has no power step). For the same reason our lit state could not be captured: what is
said about our frame comes from the build's files, the compiler source, shader bytecode and the pass-8 PNGs. Pass 8 is
a DRAFT bake (16 rays, texel 8). Line numbers: compiler = worktree `x64-zt-serve`; SDK = `sdk-film` (pass 8 was built
from `sdk-film-shell`). All five `sheet_on_*`, the four stock sheets and the compare strip were opened.

## 0. What was measured

PNG luminance (0..1, display encoded), medians over 15 of ours (`pass8\on\arc_*`), 8 stock subway, 13 stock shopfronts:

| | ours | subway | shopfronts |
|---|---|---|---|
| p5 / p50 | 0.005 / 0.113 | 0.070 / 0.170 | 0.055 / 0.178 |
| p95 / p99 | 0.42 / 0.57 | 0.50 / 0.73 | 0.58 / 0.86 |
| pixels under 0.03 | 12.4 % | 0 % | 0.5 % |
| floor band (rows 70 to 97 %) mean | 0.100 | 0.261 | 0.207 |

Ground patch before a lit front (rows 80 to 97 %, linear means):

| frame | luminance | blue / red | front above it |
|---|---|---|---|
| ours `arc_hole_nine_front` (pink shop) | 0.015 | 0.13 | 0.033, b/r 0.20 |
| ours `arc_copy_stop_front` (blue shop) | 0.013 | 0.33 (mid hall 0.28) | |
| stock `shopfronts_2` (Lounge) | 0.094 | 1.39 | 0.038, b/r 0.71 |
| stock `shopfronts_13` | 0.057 | 3.48 | |

Stock ground is 2.5 times brighter than the front above it and takes its colour; ours is half as bright as the shop
and keeps the tile's hue. Blacks are crushed and the top 5 % is missing.

## 1. Causes, ranked

Ranked by mechanism and the numbers above. The share of lightmap, probe and runtime light in the stock floor's HDR
radiance was NOT measured; experiment E1 measures the split on our own map.

**C1. The hall has no runtime light (difference 2, the highlights of 1, 4).** [verified]
- Ours: `cp_iwz.compile.log:452` "5 primary lights" (five red omnis, radius 44, elsewhere). The Arcade's 49 lights are all
  in the baker list; `python -m studio light` answers `baked 154, runtime 0`.
- Stock `cp_disco.sqlite` `lights`: 404 spots, 46 omnis; 343 spots shadow mapped, 259 volumetric. Within 800 units of
  each subway camera: 17 to 29 spots (median radius 300), 4 to 13 of a saturated colour; shopfront cameras 10 to 23
  (the two street ends 2 and 3).
- A baked light gives no highlight. Read in the lit shader of our floor's technique set (`w_l_sm_replace_i0c0s0n0p0`,
  shared by `concrete_01` and `concrete_trim_floor_01`; pixel shader `6fa1f54639dc4f0f`, listing =
  `view/v1/dxdis.py` on `C:\studio-data\template\arcade\blob\6fa1f54639dc4f0f.dxbc`): lines 124 to 147, the lightmap's
  direction image feeds only `E = A + saturate(N.D) * ssao * B`. Specular has three sources: the probe cube (149 to
  297), the sun, the runtime light loop (`t24`, from 419).
- Lit-first traded "runtime, no bounce" for "bounce, no runtime". Stock has both.

**C2. Nothing for the floor to mirror (difference 1).** [verified]
- `iwzmap.cpp:713-733` fills every block of a room's cube with one colour; `compile.log:475`: the Arcade is room 9, "cube 9
  rgb 0.2250 0.2250 0.2375". Gloss 236 to 252 only selects a sharper mip of a constant.
- The shader scales the cube by `clamp(lum(E toward the reflection) / SH(probe), 0, 3)` (lines 153 to 155, 260 to 279): a
  luminance. With a grey cube the reflection is grey under any lamp: one reason the doubled coloured spots did nothing
  (C4 is the other).
- Stock: 87 probes, 96 instances, captured cubes (128 x 128 BC6, 8 mips).
- Stock also has screen-space reflection on few surfaces: technique sets ending `_sref0` read a 640 x 360 blurred HDR
  copy of the scene (texture 83163, events 8975 to 9126 of `cam1`). At least 12 named world materials (3,494 of 565,796
  triangles: glass, `concrete_floor_polished_01_ssr`, the subway's `linoleum_floor_tiles_noline_01`); 137 of the dump's
  6,000 material files carry the suffix, the blend materials were not mapped to surfaces. The street's
  `cp_disco_asphalt_01_wet` is not one: its mirror is probes and light highlights. Our floor has no `_sref0`; nothing
  shows such a technique set has ever run on our map (the material FE9 names is in no dump here).

**C3. The lit vision: no fog, no bloom, 2.5 EV under (differences 3, 4).** [keys verified; shares not]
- Base `cp_zmb.vision`: `fogMaxOpacity 1`, `veilStrength 0.1`, `volumetricSpotBrightness 0.8`,
  `volumetricAmbientBrightness 0`, `tonemapAutoExposureAdjust 0`. Ours (`build.json` `--lit`): 0.03, 0, 0, 0, -2.5.
- Stock capture: tone map `79ad73eab1b8` lines 12 to 14, `0.96 scene + 0.04 bloom` (`cb2[7]`): cp_disco's veil is 0.04
  [verified]. World shader `cb2[2].y` 0.95 subway, 0.75 street [inferred: the fog's maximum opacity].
- The froxel volume is nearly empty in both stock captures: in-scatter `t12` mean 0.001 to 0.002 (max 0.005) in the
  subway, 0 on the street, transmittance `t13` 1.0. The street still has p5 0.055. So stock's lifted blacks are NOT
  shown to come from volumetrics: distance fog and exposure are the candidates, not split. (Subway power was off.)
- Why ours was switched off: `darkness\add_darkness.py:80-81` ("the power spots lit the vision fog into a white haze", run
  dk5), `build-g-dark.ps1:26-27` (veil = "white haze around the hot power spots"), `README.md:111-112`. The cause was 72 to
  167 wide runtime spots in cp_zmb's outdoor fog; with 0 runtime lights it is gone, and returns with C1's fix.
- Whether baked light can feed haze (`volumetricAmbientBrightness`) is not known [not verified]: it goes in the sweep.
- cp_disco's vision files are in no dump on this PC.

**C4. The floor's colour kills coloured light (difference 2).** [verified]
`w/sz_arcade_quarry` colour image mean sRGB 86 / 49 / 32; the shader squares it: albedo 0.115 / 0.037 / 0.016. Blue returns
7 times less than red, so a pool can only read through the specular path, which C1 and C2 leave empty. Alpha 10 gives
F0 0.039.

**C5. Even fill (difference 4).** [model] 12 identical ceiling spots on a 384 grid. `studio light --at`: floor direct light
3.59 at the pink pool's centre (the pool spot 1.66 of it), 2.02 mid hall: 1.8 to 1 before bounce.

**C6. No effect cards (difference 3).** `station_zero_fx_dark.txt`: 20 placements, none in the Arcade [verified]. Stock
draws 50 (subway) and 86 (street) translucent draws of `869efa42679c` [inferred: glow, smoke, motes].

## 2. Smallest correct change per cause

**C1: runtime key lights with their bounce baked.**
- Today a fixture is `baked`, `runtime` (no bounce) or `both` (direct twice): `fixtures.py:238-241`,
  `layout_lights.py:75`. Missing: direct at run time, bounce in the lightmap. `lmbake.py:484-495`: keep the light in `Edir`
  for the gather, leave it out of `B`. About 15 lines there, 5 in `layout_lights.py`, 20 in Studio.
- Network: an unnamed row takes a static template slot and no entity (`iwzmap.cpp:1497-1517`; entities only for named
  lights, `:1577`): 0 records, the map stays at 494. Under lit-first the dark state is an exposure, so always-on lights
  fit. A light the power must switch is 1 record (headroom 274).
- Caps: 256 light rows, 65,535 voxel entries (r19: 198 rows, 59,191 entries): radii near stock's 300, ours are 950 to
  1,050. Frame time: not measured.
- Proof: the ground patch before the pink shop at `arc_hole_nine_front`: luminance above the shop's, blue / red above
  0.3; Forge frame time before and after.

**C2: a reflection source.**

| route | needs | weakness |
|---|---|---|
| a. `_sref0` base for hero floors | one document line (`base` of `mat_sz_arcade_quarry` -> `concrete_floor_polished_01_ssr`; cp_disco's technique dumps are already in `kit.dumps`) | on-screen content only; pass cost unmeasured; target packs normal, occlusion and gloss (`_packed_nog`), ours is `_packed_ng`; never run here |
| b. cubes from Studio's renderer | 6 faces, HDR, per probe (1.2 to 1.8 s a view: 10 to 20 probes = 1.5 to 3 min, cacheable by bake key); prefiltered mips; BC6H (`bake\iw7image.py`); compiler mode reading a cube per room, about 50 lines beside `:713`; several probes per room | renderer is 84 to 93 % within 5 % of the game |
| d. template cubes left in place | skip the fill under a switch, 3 lines | wrong pictures: a probe, not a product |

Six game frames per probe (route c) needs RenderDoc captures for HDR (0.5 to 1 GB each) and a session per build: not a
build step. Unknown for b and d: the per-probe SH the shader divides by (`t33`) is built by the engine at load, rule
not derived (`renderer.md` round 13). First cheap probe: route d on one build. A picture in the floor at a sane
brightness means b is safe; black or blown means the `t33` rule (Ghidra) comes first.

**C3: an interior lit vision.** `settings.build.darkness.args` `--lit`: sweep `veilStrength` 0.04, `fogMaxOpacity` 0.3 to
0.95 with a lower `fogDensity`, `tonemapAutoExposureAdjust` -1 to -2, `volumetricAmbientBrightness` 0.2 with
`volumetricAirDensity` 0.02; after C1, `volumetricSpotBrightness` 0.15 and a `vol` token in `lights.txt` (the compiler
writes `isVolumetric = 0`, `:1542`, and avoids volumetric slots, `:1508`; about 8 lines; worth building only if the
sweep shows haze matters). No code for the sweep: `live sync` variants (FE60). Dump cp_disco's vision first
(Coordinator). Proof at five cameras: p5 at least 0.04, under 2 % of pixels below 0.03, p99 at least 0.7, clipping under 1 %.

**C4: floor art.** `floor_quarry_c.png`: saturation at most 0.35, no channel under 0.08 after squaring; alpha 15 to 25 in
wet patches (F0 0.06 to 0.1); gloss with dry and wet areas. One file.

**C5, C6: fixture rule.** Lower the ceiling fill until pool to hall is 4 to 1 in `studio light`; glow cards and motes
from `fx\fx_catalog.json`, placed by the fixture.

## 3. Work packages, in order

| | package | proof |
|---|---|---|
| E1 | the experiment below (no code) | three frames, ground patch numbers |
| W1 | baker "bounce only" + Studio fixture value; Arcade pool and sign lights use it | patch test; 494 records; frame time |
| W2 | C3 sweep; cp_disco vision dump; `vol` token if the sweep asks for it | the C3 numbers |
| W3 | floor art C4, fill ratio C5, FX cards C6 | patch blue / red; pool to hall 4 to 1 |
| W4 | probe route d (3 lines), then b; `t33` rule if d fails | mirror at `arc_east_long`, same camera |
| W5 | final bake, all sheets, independent reviewers | QUALITY-BAR part C |

**E1, first thing tomorrow.** Three variants of `docall`, cameras `arc_hole_nine_front` and `arc_east_long`, power on:
(A) floor base -> `concrete_floor_polished_01_ssr`; (B) the four shop pool spots as `bake: runtime`, `group: emergency`;
(C) both. A reuses the bake; B and C bake once (124 s draft). Before shooting B, read the emitted `lights.txt` rows: bake
intensities are 12 to 16.5, engine rows are in the thousands (`dark_build --scale 840`); a row left at 16 makes a null
result meaningless. Read the ground patch (now 0.015, b/r 0.13). It tells which of C1 and C2 moves the floor and whether
`_sref0` works here, before any tool is written.

## Not verified
Our lit frame pass by pass; pixel coverage of `_sref0` surfaces in stock; cp_disco's vision keys and fog volume count;
which of fog, exposure or volumetrics lifts stock's blacks; frame time of runtime, shadowed or volumetric lights here;
the `t33` rule; one record per named light (from INVENTORY: 167 lights, 167 records).
