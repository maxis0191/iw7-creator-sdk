# Station Zero look preview (Blender, no map build, no game)

Loads an emitted compiler source (`level/src_*`: `world.bin`, `layout.json`, `bake.npz`, `smodels.txt`,
`custom_materials.json`, `plan.json`, `colmap.hkx`) into Blender and renders cameras in a fraction of a second, so a
change to `station_zero2.py` / `scenegen.py` can be judged in about 10 seconds from emit instead of a ~7 minute build,
a game run and screenshots.

| File | Role |
| --- | --- |
| `iwz_preview.py` | runs inside Blender (`-b` or interactive): `load(src)` builds the scene (collections world / props / overlays / views), renders linear frames |
| `iwz_preview_render.py` | plain Python wrapper: `render` (views to PNG, prints seconds per stage) and `calibrate` (the acceptance test against engine frames) |
| `iwz_assets.py` | numpy-only readers: world.bin, dump index, material -> colour image, image decode from `imagefile<N>.pak` (IWC LZ4 blocks) via texconv, xmodel LOD0 with uv |
| `iwz_audit.py` | per material audit of the colour image and its evidence (STRONG / MEDIUM / WEAK), `material_audit.md` / `.json` |
| `iwz_calib.py` | the metrics (edge IoU, mean luminance, global tone fit) |
| `calibration.json` | the fitted global camera (eye height, horizontal fov); its tone fit (`k`, `p`) and `prop_gain` are the OLD lit-frame fit, superseded, see "State of the lighting" |
| `iwz_tonemap.py`, `engine_tonemap_lut32.bin` | the engine's own tone map (shader `8881bdf370aa`, constants and colour grade LUT of a stock capture), numpy |
| `iwz_lights.py` | the 72 runtime lights added per pixel with the engine falloff (lit state) |
| `rdoc_inspect.py`, `rdoc_run.py` | offline RenderDoc replay of an existing .rdc: shader disassembly, constants, textures, targets (no game) |
| `ENGINE-SHADERS.md` | what the engine's post chain and lightmapped world shader do, with instruction lines |

```powershell
python -B iwz_preview_render.py render --src <emit src> --out <dir> --views ticket_hall_0,platform_a_0 [--overlays]
python -B iwz_preview_render.py render --src <emit src> --out <dir> --views all --plan <plan.json>    # plan tour views too
python -B iwz_preview_render.py calibrate --src <emit src> --plan <capture plan> --frames <engine frames dir> --out <dir>
```

Needs Blender 5.x (`IWZ_BLENDER`, default `C:\Program Files\Blender Foundation\Blender 5.2`), Python with numpy and
PIL, texconv (`IWZ_TEXCONV`), and for the textures the base game's `imagefile<N>.pak` (`IWZ_GAME_ROOT`, else the first
`<runtime>\bench\*` that has them). Dumps come from `IWZ_RUNTIME` / `IWZ_TEMPLATE_DUMP` (see `iwz_assets.dump_roots`).
Decoded textures are cached in `%LOCALAPPDATA%\iwz-preview-cache` (override `IWZ_PREVIEW_CACHE`).

## What it renders

* **World**: `world.bin` triangles, albedo on the `uv` layer, the baked lightmap on the `lightmap` layer. Shading is
  unlit (emission), no Blender light exists: the engine draws albedo * irradiance and so does the preview.
* **Irradiance** `E = A + B * saturate(D.z)` per texel from `bake.npz` (formula of `bake/lm_decode.py`; for a flat
  surface `dot(N, D) = D.z`; its mean over valid texels equals `bake.json` `mean.E` to 8 digits). The in-engine ssao
  factor on B is not modelled.
* **Albedo**: the material json colour image (semantic 2, else 14 `..._packed_cs`), found in the dumps, streamed top mip read
  from `imagefile<N>.pak` (`IWC` header, LZ4 blocks of 64 KB, each block start aligned to 4), BC1-7 decoded by texconv.
  Checked pixel-exact (mean difference 0.0) against GrayWolf's PNG of the same stock image. Custom materials come from
  `custom_materials.json`: a TGA (signs, posters, decals) or a stock base with a tint; emissive customs (lamps) are shown
  unlit. Alpha-test techsets (`_atest_`) clip, blend techsets and decal customs blend, `w_unlit_multiply` decals (grime masks) are
  approximated as a black overlay with alpha = 1 - luminance. The PNG alpha of lit colour maps is a data channel (gloss), so images
  are read channel packed: Blender would otherwise premultiply the colour with it and darken the world about ten times.
* **Props**: layout decor and models (door dressing left out: the capture plans open the doors) as real LOD0 meshes
  with their colour textures, one mesh per model, objects linked to it. Instances are lit with the **light grid**
  (`bake.npz` `grid`: order-1 SH constant term of the kept probe cells, nearest cell within 192 units, else the mean of the
  kept cells, `E = 0.886 * c0`), constant per instance through the object colour, no direction.
* **Overlays** (collection `overlays`, hidden from render; `--overlays` shows them): spawners (arrows), doors, door blockers,
  zone volumes, nav cells (`plan.json` cells, 32 unit cells), collision (`colmap.hkx` through `hkcm.py`, wireframe).
* **Views**: `layout.json` `views` as `<zone>_<n>` and, with `--plan`, every `tour` view of a capture plan as `plan_<name>`.
  Camera = player origin + eye height, yaw, pitch (`gl_tp` does `setorigin` + `setplayerangles((pitch, yaw, 0))`).

Models come from the stock dumps, the kit dumps and the built zone dump (`<runtime>/iwz-stage2/level/ztwork/zonetool/cp_iwz`, which
holds the map's own `iwz_*` models, materials and plain DDS images); a model that has no xmodel but an authored glb (`level/p1/machines/authored`, the perk machines before the zone build) is imported
through Blender's glTF importer (unused on g27r: all models resolve from the zone dump). Anything unresolved is **magenta** and listed with its reason in `report.json` (`materials.unresolved_list`,
`models.unresolved_list`); nothing is given a silent fake colour. A missing model is drawn as a 32 x 32 x 32 unit
magenta box at its origin.

## State of the lighting (22 Nov 2026, replaces the exposure and prop gain claims further down)

**The power state is the fact that mattered.** The g27r emit is a darkness bake: its lightmap (`bake.npz`, and the compiled `lightmap/secondary.dds`, which are equal:
median ratio 0.9998 on A) holds the 56 emergency lights only (`darkness.json` baked_emergency 56, ambient 0.025); the 72 named lights of the power banks
(`lights.txt`, 72 lines with `name=iwz_power`) are runtime lights switched on by the level script. The capture plan `szf_rc4_look.json` shoots `dark_*` with the
power off and `lit_*` 15 s after `sz_power_direct power 20`. The first calibration (round 1 and 2 below) fitted a lightmap-only render against the `lit_*` frames,
the wrong state: its exposure `k`, gamma `p`, `prop_gain` 0.086 and the "auto exposure / reflections" explanation are not valid and are kept only as history.
The earlier statement that the large per view brightness spread is caused by reflections or auto exposure was not verified and is withdrawn: the lit frames lack
the runtime lights in the preview, and their exposure is auto (see below).

* **Tone map**: the engine's, read from the shader (`ENGINE-SHADERS.md` section 1; `iwz_tonemap.py` reproduces the stock capture's post pass with a mean error of
  0.25 of an 8 bit level, maximum 0.61). No fitted curve.
* **Exposure** enters the engine only as a scale `s` on the curve constants (`cb13[1].xy`, `cb13[2].xy` = base constants * s, written by the exposure compute pass
  `974052551c85`, lines 90-119). With `tonemapAuto 0` it comes from the vision (`tonemapMaxExposure`), with auto it comes from the log average luminance of the frame
  (`c672eba77dc0`, a vignette weighted sum of log luminance) through the vision's Dark / Mid / Light EV table, adapted slowly (`tonemapAdaptSpeed 0.01`).
  Dark frames: the 15 `dark_*` frames fit a mean exposure of 2^-3.01 (per frame spread 0.75 stops) against the stock constants, which is the module's dark vision
  (`tonemapAuto 0`, `tonemapMaxExposure -3`, `darkness/NOTES.md`). The preview uses `--ev -3`.
* **Lit frames** have an auto exposure that depends on the frame: modelled in round 2 below (steady state, no per frame parameter).

```powershell
python -B iwz_preview_render.py light  --src <emit src> --plan <plan> --frames <engine frames> --out <dir> --prefix dark --power off --ev -3   # dark state
python -B iwz_preview_render.py lights --src <emit src> --plan <plan> --frames <engine frames> --out <dir>                                  # lit state, runtime lights
```


### Measured: dark state (`light --power off --ev -3`, lightmap + props, no fitted curve, prop_gain 1)

Edge IoU as before (Sobel of the blurred log luminance, 3 px). "median upper" = median luminance of rows 60-330 (no weapon, no flashlight pool), preview / engine.
The engine's dark frames contain the player's flashlight pool and weapon, which the preview has not, so the mean ratio is below 1 where the flashlight dominates.

| frame (exposure -3 EV) | edge IoU | lum ratio, mean | lum ratio, median upper rows |
|---|---|---|---|
| dark_ticket_hall_1 | 0.548 | 0.446 | 1.140 |
| dark_stair_a_1 | 0.610 | 1.895 | 2.175 |
| dark_platform_a_1 | 0.588 | 0.644 | 1.267 |
| dark_maint_corridor_1 | 0.657 | 0.391 | 0.638 |
| dark_generator_room_1 | 0.637 | 1.131 | 1.327 |
| dark_control_room_1 | 0.707 | 0.481 | 0.933 |
| dark_service_tunnel_1 | 0.650 | 2.242 | 1.479 |
| dark_platform_b_1 | 0.562 | 0.976 | 1.517 |
| dark_stair_b_1 | 0.569 | 0.296 | 0.500 |
| dark_pap_arch_1 | 0.662 | 0.214 | 0.650 |
| dark_well_w_1 | 0.468 | 0.366 | 0.594 |
| dark_well_e_1 | 0.542 | 0.124 | 0.746 |
| dark_hero_car_1 | 0.551 | 1.732 | 2.744 |
| dark_pap_alcove_1 | 0.343 | 0.099 | 0.607 |
| dark_pap_alcove_2 | 0.247 | 0.230 | 0.622 |
| mean | 0.556 | 0.751 | 1.129 |

Before this work the lightmap only render at gain 1 (no exposure at all) was 6.5 times too bright on the mean; with the engine tone map and the vision's fixed exposure
there is no fitted parameter and the median of the upper rows is within 13 % on average (frames range 0.5 to 2.7). Side by sides (preview left, engine right):
`IW7-Runtime/iwz-stage2/finish/preview/light/dark1/sidebyside/dark_{ticket_hall,generator_room,control_room}_1_preview_vs_engine.png`.

### Measured: lit state (`lights`, power on, 72 runtime lights with the engine falloff)

One global parameter, `UNIT` (the engine's light record colour is colour * intensity * UNIT, the CPU side of that unit is not in any shader): the grid minimum of the mean
pattern error over 10 values is UNIT = 1e-3. The exposure of each frame is AUTO in the engine and is not modelled: each frame gets the gain that matches the median luminance of
the engine frame (the column "exposure EV" is that gain in stops against the stock curve constants), before and after. "Pattern rms log err" is the rms of
log(preview / engine) over the masked pixels of 4 x 4 block means (large because the engine has black pixels the log amplifies); lower is better.
Dark and lit frames of the plan are the same views, so lights are the only difference of the two states.

| frame | edge IoU before | edge IoU after | pattern rms log err before | pattern rms log err after | exposure EV before | exposure EV after |
|---|---|---|---|---|---|---|
| lit_ticket_hall_1 | 0.680 | 0.644 | 2.033 | 1.397 | -0.732 | -1.184 |
| lit_stair_a_1 | 0.651 | 0.678 | 1.654 | 1.483 | -1.749 | -2.557 |
| lit_platform_a_1 | 0.457 | 0.594 | 2.398 | 2.300 | -0.369 | -0.851 |
| lit_maint_corridor_1 | 0.527 | 0.523 | 1.453 | 1.527 | 0.110 | -1.776 |
| lit_generator_room_1 | 0.600 | 0.618 | 1.644 | 1.619 | 0.665 | -0.632 |
| lit_control_room_1 | 0.639 | 0.687 | 2.117 | 1.913 | 0.657 | -0.518 |
| lit_service_tunnel_1 | 0.615 | 0.615 | 2.055 | 2.055 | -0.725 | -0.725 |
| lit_platform_b_1 | 0.681 | 0.680 | 1.617 | 1.632 | 0.497 | 0.446 |
| lit_stair_b_1 | 0.541 | 0.652 | 1.533 | 1.102 | 0.193 | -1.613 |
| lit_pap_arch_1 | 0.580 | 0.573 | 1.740 | 1.187 | 0.353 | -0.255 |
| lit_well_w_1 | 0.498 | 0.488 | 2.250 | 2.220 | -1.104 | -1.238 |
| lit_well_e_1 | 0.486 | 0.510 | 1.745 | 1.585 | -0.873 | -1.073 |
| lit_hero_car_1 | 0.375 | 0.509 | 1.994 | 2.023 | -2.936 | -3.413 |
| lit_pap_alcove_1 | 0.343 | 0.339 | 1.471 | 1.352 | -0.948 | -1.284 |
| lit_pap_alcove_2 | 0.252 | 0.252 | 1.423 | 1.423 | -2.712 | -2.720 |
| mean | 0.528 | 0.557 | 1.808 | 1.655 | -0.645 | -1.293 |

By eye, after (lightmap + lights) against the engine, one sentence per frame: ticket_hall: ceiling, stairs and the bright side wall now match in brightness, the engine floor is cool grey where the preview floor is warm brown;
stair_a: walls are far brighter than the engine's near black walls, the lamps' pools match; platform_a: ceiling and pillars now read like the engine, the preview floor is black where the engine shows pale tiles;
maint_corridor: layout and lamp pool match, the engine is cool and glossy with near black lower walls, the preview warm and flat; generator_room: lamps, machine and the dim doorway match,
the engine floor is brighter and cooler; control_room: props and layout match, the preview has a strong red wash from the baked emergency lights that the engine shows far weaker;
service_tunnel: brightness and shape match closely, the engine adds glossy walls and rails; platform_b: structure matches, the preview floor is near black and the fire is missing;
stair_b: green walls match well, the engine's far window is blown out where the preview's is dim; pap_arch: structure and brightness match, the engine is cooler and the floor glossy;
well_w and well_e: wall lamps and glow match, engine wall tiles are cooler and the platform edge material differs (salmon in the preview, pale grey in the engine);
hero_car: preview much darker (engine ceiling and floor lit, fire and debris), the blue car matches; pap_alcove_1: preview warm and solid where the engine shows chain link and a cool cast;
pap_alcove_2: the engine has a large projector prop the emit does not list, the walls match in structure. The engine frames are consistently cooler than the preview: the lit vision's colour grade
(its own LUT and curve constants) is not in any capture on disk, the stock LUT is used.

Side by sides (before | after | engine) for all 15: `IW7-Runtime/iwz-stage2/finish/preview/light/lit1/sidebyside/lit_*_before_after_engine.png`
(ticket_hall, generator_room, control_room among them).

### Black control room (`lit_generator_room_1`)

Not an engine limit. `ENGINE-SHADERS.md` section 4: per pixel limits 64 (primary omni / spot), 32 (dynamic), 256 light records per view; the largest number of lights covering one pixel of that view is 7.
The room is drawn and dim in the engine; only two control room lamps reach what is visible through the door, with a smoothstep weight of 0.027 and 0.010.

Open items found on the way (not changed): the world shader reads channel R of the `..._packed_nog` map as gloss, not occlusion (ENGINE-SHADERS.md section 2); the preview still multiplies R
into the lightmap term A (an inference of the earlier round, now contradicted by the shader) and decodes colour maps with the sRGB curve where the engine squares them (c^2). Specular, reflection
probes, shadows of the 9 shadowed lights, bloom (approximated), the lit vision's colour grade and the flashlight are not modelled.

## Round 2 (22 Nov 2026, offline, no game)

### 1. Decode fixes

Albedo is now the engine's `rgb^2` (colour maps read as raw values and squared) for lit world surfaces and models; the `nog` map's R channel is no longer used as occlusion (it is gloss).
The real occlusion sources in the world shader are only the lightmap itself and the screen space ssao on the B term (ENGINE-SHADERS.md section 2); there is no material occlusion map.
Dark state, exposure -3 EV (vision), nothing fitted (the old column set; "median upper" = median luminance of rows 60-330, preview / engine):

| frame (exposure -3 EV) | edge IoU | lum ratio, mean | lum ratio, median upper rows |
|---|---|---|---|
| dark_ticket_hall_1 | 0.564 | 0.576 | 1.407 |
| dark_stair_a_1 | 0.683 | 2.344 | 2.541 |
| dark_platform_a_1 | 0.619 | 0.751 | 1.323 |
| dark_maint_corridor_1 | 0.646 | 0.465 | 0.737 |
| dark_generator_room_1 | 0.604 | 1.308 | 1.540 |
| dark_control_room_1 | 0.702 | 0.547 | 1.064 |
| dark_service_tunnel_1 | 0.651 | 2.515 | 1.678 |
| dark_platform_b_1 | 0.547 | 1.071 | 1.622 |
| dark_stair_b_1 | 0.570 | 0.327 | 0.589 |
| dark_pap_arch_1 | 0.658 | 0.254 | 0.721 |
| dark_well_w_1 | 0.474 | 0.403 | 0.630 |
| dark_well_e_1 | 0.550 | 0.134 | 0.800 |
| dark_hero_car_1 | 0.572 | 1.975 | 2.923 |
| dark_pap_alcove_1 | 0.347 | 0.118 | 0.705 |
| dark_pap_alcove_2 | 0.247 | 0.262 | 0.691 |
| mean | 0.562 | 0.870 | 1.265 |

Lit state with the per frame fitted exposure of round 1 (kept for reference; UNIT 1e-3; EV = exposure gain in stops against the stock curve constants):

| frame | edge IoU before | edge IoU after | pattern rms log err before | pattern rms log err after | exposure EV before | exposure EV after |
|---|---|---|---|---|---|---|
| lit_ticket_hall_1 | 0.650 | 0.685 | 1.903 | 1.383 | -1.321 | -1.593 |
| lit_stair_a_1 | 0.669 | 0.671 | 1.428 | 1.310 | -2.476 | -2.754 |
| lit_platform_a_1 | 0.496 | 0.645 | 1.691 | 1.652 | -0.659 | -1.077 |
| lit_maint_corridor_1 | 0.551 | 0.539 | 1.434 | 1.515 | -0.099 | -1.975 |
| lit_generator_room_1 | 0.592 | 0.633 | 1.490 | 1.487 | 0.268 | -0.878 |
| lit_control_room_1 | 0.672 | 0.687 | 1.955 | 1.795 | 0.363 | -0.812 |
| lit_service_tunnel_1 | 0.611 | 0.611 | 2.043 | 2.043 | -0.883 | -0.883 |
| lit_platform_b_1 | 0.708 | 0.709 | 1.495 | 1.510 | 0.110 | 0.078 |
| lit_stair_b_1 | 0.545 | 0.650 | 1.403 | 1.091 | -0.214 | -1.851 |
| lit_pap_arch_1 | 0.564 | 0.574 | 1.613 | 1.115 | 0.166 | -0.622 |
| lit_well_w_1 | 0.502 | 0.492 | 2.248 | 2.221 | -1.216 | -1.355 |
| lit_well_e_1 | 0.501 | 0.516 | 1.713 | 1.559 | -0.987 | -1.192 |
| lit_hero_car_1 | 0.400 | 0.512 | 1.890 | 1.954 | -3.221 | -3.674 |
| lit_pap_alcove_1 | 0.339 | 0.344 | 1.427 | 1.331 | -1.148 | -1.481 |
| lit_pap_alcove_2 | 0.256 | 0.255 | 1.371 | 1.370 | -2.846 | -2.856 |
| mean | 0.537 | 0.568 | 1.674 | 1.556 | -0.944 | -1.528 |

### 2. Auto exposure as a model (no per frame parameter)

`iwz_tonemap.exposure_gain`: the log average luminance of the frame (160 x 90 reduction, floor 0.000061; shader `c672eba77dc0`) goes through the vision's Dark / Mid / Light EV table
(`cp_iwz.vision`: DarkEv 2.84, MidEv 7.823, LightEv 12.81, adjusts -3.17 / -0.651 / 1.47, min / max adjust -3.17 / 2.3) to a target key (`974052551c85` lines 38-66), e = key / Lavg
(line 80), exposure = min(0.18 / Lmax, e * 2^tonemapAutoExposureAdjust) with Lmax = 0.001 * 2^(tonemapMaxExposure - 2.84) (lines 103-109); the gain against the stock capture's curve constants
is exposure / 5.0345. The fixed vision (`tonemapAuto 0`) uses 5.0345 * 2^tonemapExposureAdjust (the dark vision's -3 gives the 2^-3.01 measured on the dark frames).
The lit vision is the map vision (`cp_iwz.vision`, `tonemapAuto 1`, no bias; the darkness build only changes fog, volumetrics and `tonemapAdaptSpeed 0.3`, `build-g-dark.ps1` LK), steady state (adaptation ignored).
The two open points of the shader reading are a factor 2 between the fixed exposure the formula gives (2.517) and the stock capture's constant (5.0345), and the missing view of cb0[2].w; they are
documented in the code. Lit table with the model, no flashlight, UNIT fitted (1e-4) on the pattern error, no per frame parameter ("EV fitted" is the per frame gain that would match the median, for information):

| frame | edge IoU before | edge IoU after | pattern rms log err before | pattern rms log err after | EV used before | EV fitted before | EV used after | EV fitted after |
|---|---|---|---|---|---|---|---|---|
| lit_ticket_hall_1 | 0.655 | 0.654 | 1.957 | 1.885 | 0.000 | -1.321 | 0.000 | -1.435 |
| lit_stair_a_1 | 0.686 | 0.689 | 2.204 | 2.217 | -0.351 | -2.476 | -0.396 | -2.520 |
| lit_platform_a_1 | 0.511 | 0.557 | 1.849 | 1.839 | 0.000 | -0.659 | 0.000 | -0.742 |
| lit_maint_corridor_1 | 0.551 | 0.545 | 1.452 | 1.544 | 0.000 | -0.099 | 0.000 | -0.411 |
| lit_generator_room_1 | 0.590 | 0.612 | 1.507 | 1.359 | 0.000 | 0.268 | 0.000 | -0.199 |
| lit_control_room_1 | 0.672 | 0.674 | 1.888 | 1.850 | 0.000 | 0.363 | 0.000 | 0.176 |
| lit_service_tunnel_1 | 0.609 | 0.609 | 2.145 | 2.145 | -0.183 | -0.883 | -0.183 | -0.883 |
| lit_platform_b_1 | 0.709 | 0.709 | 1.502 | 1.502 | 0.000 | 0.110 | 0.000 | 0.103 |
| lit_stair_b_1 | 0.543 | 0.563 | 1.434 | 1.432 | 0.000 | -0.214 | 0.000 | -0.498 |
| lit_pap_arch_1 | 0.564 | 0.565 | 1.589 | 1.507 | 0.000 | 0.166 | 0.000 | 0.013 |
| lit_well_w_1 | 0.516 | 0.516 | 2.421 | 2.420 | -0.080 | -1.216 | -0.094 | -1.275 |
| lit_well_e_1 | 0.492 | 0.501 | 1.769 | 1.735 | 0.000 | -0.987 | 0.000 | -1.012 |
| lit_hero_car_1 | 0.410 | 0.454 | 2.713 | 2.761 | -0.223 | -3.221 | -0.260 | -3.289 |
| lit_pap_alcove_1 | 0.346 | 0.347 | 1.735 | 1.738 | 0.000 | -1.148 | 0.000 | -1.189 |
| lit_pap_alcove_2 | 0.249 | 0.249 | 2.325 | 2.325 | -0.689 | -2.846 | -0.689 | -2.846 |
| mean | 0.540 | 0.550 | 1.899 | 1.884 | -0.102 | -0.944 | -0.108 | -1.067 |

Result: the model saturates at the vision's maximum exposure (EV 0) for 10 of the 15 frames, because the log average luminance of these dark frames is far below the Dark point; the engine frames
want about one stop less on average (fitted EV mean -0.94 before lights, which includes the effect of the missing flashlight and specular). The model is the shader's steady state; the gap is open.

### 3. Flashlight

From the darkness module (`a85/sdkhead/tools-source/iwzmap/darkness`: `cp_iwz_flashlight.gsc`, `build-g-dark.ps1` line 2 for the d16 values, `make_vfx_light.py` units): a spot at eye + (24 forward, 4 right, 6 down)
following the view angles, full cone 40 deg, inner 2 deg, radius 900, colour (1, 0.92, 0.80), brightness 3.5 (x0.3 after power), plus a halo spot (full cone 64, inner 0, radius 700, brightness 0.875, x0.3 lit),
the engine's spot form (cone = saturate between the outer and inner half angle cosine, radial smoothstep, N.L), no shadow. The unit of `brightness` (FLU) is the one fitted value: FLU = 1 on the 15 dark frames
(pattern error 1.56 -> 1.24). Dark table, vision exposure -3 EV, flashlight on ("before" = without):

| frame | edge IoU before | edge IoU after | pattern err before | pattern err after | median ratio before | median ratio after | EV model before | EV fitted before | EV model after | EV fitted after |
|---|---|---|---|---|---|---|---|---|---|---|
| dark_ticket_hall_1 | 0.564 | 0.610 | 1.155 | 0.810 | 1.407 | 1.527 | -3.000 | -3.223 | -3.000 | -3.491 |
| dark_stair_a_1 | 0.683 | 0.687 | 1.029 | 0.999 | 2.541 | 2.573 | -3.000 | -4.128 | -3.000 | -4.197 |
| dark_platform_a_1 | 0.619 | 0.618 | 1.003 | 1.088 | 1.323 | 1.376 | -3.000 | -3.017 | -3.000 | -3.372 |
| dark_maint_corridor_1 | 0.646 | 0.685 | 1.235 | 0.959 | 0.737 | 1.620 | -3.000 | -2.425 | -3.000 | -3.725 |
| dark_generator_room_1 | 0.604 | 0.601 | 1.314 | 0.937 | 1.540 | 1.541 | -3.000 | -2.751 | -3.000 | -3.065 |
| dark_control_room_1 | 0.702 | 0.734 | 1.251 | 0.942 | 1.064 | 1.091 | -3.000 | -2.622 | -3.000 | -3.201 |
| dark_service_tunnel_1 | 0.651 | 0.651 | 0.957 | 0.957 | 1.678 | 1.678 | -3.000 | -3.844 | -3.000 | -3.844 |
| dark_platform_b_1 | 0.547 | 0.547 | 1.163 | 1.163 | 1.622 | 1.622 | -3.000 | -2.815 | -3.000 | -2.815 |
| dark_stair_b_1 | 0.570 | 0.588 | 2.330 | 0.988 | 0.589 | 0.798 | -3.000 | -1.820 | -3.000 | -2.603 |
| dark_pap_arch_1 | 0.658 | 0.588 | 1.372 | 1.034 | 0.721 | 1.318 | -3.000 | -2.447 | -3.000 | -3.034 |
| dark_well_w_1 | 0.474 | 0.485 | 2.236 | 2.221 | 0.630 | 0.643 | -3.000 | -2.761 | -3.000 | -2.768 |
| dark_well_e_1 | 0.550 | 0.558 | 1.991 | 1.514 | 0.800 | 0.805 | -3.000 | -2.547 | -3.000 | -2.771 |
| dark_hero_car_1 | 0.572 | 0.606 | 2.403 | 2.446 | 2.923 | 2.955 | -3.000 | -5.785 | -3.000 | -5.836 |
| dark_pap_alcove_1 | 0.347 | 0.344 | 2.160 | 1.209 | 0.705 | 0.879 | -3.000 | -2.712 | -3.000 | -2.953 |
| dark_pap_alcove_2 | 0.247 | 0.297 | 1.796 | 1.333 | 0.691 | 1.170 | -3.000 | -2.948 | -3.000 | -3.328 |
| mean | 0.562 | 0.573 | 1.560 | 1.240 | 1.265 | 1.440 | -3.000 | -3.056 | -3.000 | -3.400 |

Lit table with the flashlight at its lit brightness (FLU 1 from the dark state), model exposure, UNIT 1e-4:

| frame | edge IoU before | edge IoU after | pattern err before | pattern err after | median ratio before | median ratio after | EV model before | EV fitted before | EV model after | EV fitted after |
|---|---|---|---|---|---|---|---|---|---|---|
| lit_ticket_hall_1 | 0.655 | 0.648 | 1.957 | 2.276 | 1.702 | 1.954 | 0.000 | -1.321 | -0.204 | -1.700 |
| lit_stair_a_1 | 0.686 | 0.689 | 2.204 | 2.227 | 8.583 | 8.851 | -0.351 | -2.476 | -0.410 | -2.562 |
| lit_platform_a_1 | 0.511 | 0.551 | 1.849 | 1.966 | 7.100 | 8.062 | 0.000 | -0.659 | 0.000 | -1.048 |
| lit_maint_corridor_1 | 0.551 | 0.535 | 1.452 | 1.973 | 0.937 | 1.803 | 0.000 | -0.099 | -0.148 | -1.075 |
| lit_generator_room_1 | 0.590 | 0.606 | 1.507 | 1.312 | 0.783 | 1.198 | 0.000 | 0.268 | 0.000 | -0.309 |
| lit_control_room_1 | 0.672 | 0.671 | 1.888 | 1.942 | 1.847 | 2.161 | 0.000 | 0.363 | 0.000 | -0.202 |
| lit_service_tunnel_1 | 0.609 | 0.609 | 2.145 | 2.145 | 1.155 | 1.155 | -0.183 | -0.883 | -0.183 | -0.883 |
| lit_platform_b_1 | 0.709 | 0.709 | 1.502 | 1.502 | 1.323 | 1.329 | 0.000 | 0.110 | 0.000 | 0.103 |
| lit_stair_b_1 | 0.543 | 0.610 | 1.434 | 1.797 | 1.052 | 1.796 | 0.000 | -0.214 | -0.011 | -0.956 |
| lit_pap_arch_1 | 0.564 | 0.586 | 1.589 | 2.054 | 2.031 | 4.540 | 0.000 | 0.166 | 0.000 | -0.355 |
| lit_well_w_1 | 0.516 | 0.518 | 2.421 | 2.426 | 2.171 | 2.270 | -0.080 | -1.216 | -0.098 | -1.277 |
| lit_well_e_1 | 0.492 | 0.494 | 1.769 | 1.862 | 2.008 | 2.104 | 0.000 | -0.987 | 0.000 | -1.153 |
| lit_hero_car_1 | 0.410 | 0.450 | 2.713 | 2.793 | 4.929 | 8.340 | -0.223 | -3.221 | -0.279 | -3.323 |
| lit_pap_alcove_1 | 0.346 | 0.348 | 1.735 | 1.852 | 2.694 | 2.904 | 0.000 | -1.148 | -0.112 | -1.328 |
| lit_pap_alcove_2 | 0.249 | 0.247 | 2.325 | 2.500 | 6.688 | 7.928 | -0.689 | -2.846 | -0.900 | -3.053 |
| mean | 0.540 | 0.551 | 1.899 | 2.042 | 3.000 | 3.760 | -0.102 | -0.944 | -0.156 | -1.275 |

The flashlight pool reproduces the engine's (ticket_hall: the pillar and the floor, `dark3/sidebyside/dark_ticket_hall_1_before_after_engine.png`); the engine's pool is softer and dimmer on the pillar (no shadow, no normal map).
In the lit state the model exposure is too high (see 2), so the lit pattern error with the flashlight is not better than without; the lit state is not matched.

### 4. Specular from reflection probes: not done

What exists: the emit lists 9 `room` probes (`probes.txt`: box, colour, intensity) and the zone holds `_reflection_probe_array.iw7Image` (21 MB, header `08 01 01 00 ...`); the shader's inputs and formula are in ENGINE-SHADERS.md section 2.
What is missing, in order: (1) a reader for the zone's `.iw7Image` cube array (the stock images are read from `imagefile<N>.pak`; this custom one is a different container) and the mip chain of the BC6 faces; (2) the probe records of the
zone (`t31`: box, parallax centre, SH `t33` coefficients) which the compiler writes into the world and `probes.txt` only summarises; (3) a per pixel gloss (nog R) and metalness (albedo alpha) pass from Blender, and the normal map
(the preview uses geometric normals, so a mirror like floor would reflect wrongly); (4) the environment BRDF lookup `t11` (64 x 64 BC5 of the capture, dumpable with `rdoc_inspect.py`); (5) the relight ratio `lum(E at the reflection direction) / SH`.
That is more than the two hours; none of it is blocked by missing data except (1), which needs the container layout.

### 5. The two mismatches of `lit_generator_room_1`

**White barrels right of the generator (engine: dark barrels and a dark box): cause established.** They are props (`com_barrel_tan_rust` at (3540, 2590, -321), `ammo_crate_01_dust` at (3740, 2460)), which the preview lights with
the nearest kept light grid cell, constant per instance. The kept cells around the barrel (`bake.npz grid`, 1891 kept cells): nearest at 103 units has E = (0.508, 0.284, 0.114), the next three 0.27, 0.12, 0.18, and one 198 units away
has E = 8.8 (inside a lamp); the inverse distance mean of the four nearest is 0.28, and the cells under the barrel (z = -376 layer) are not kept at all. The engine interpolates the grid trilinearly per pixel with spherical harmonics
(direction, shadowing), so one hot cell does not paint the whole prop. Measured in the preview: with `prop_gain` 0 the barrel region radiance is 0.005 to 0.05, with the grid at gain 1 it is 0.05 to 0.11 (3 to 5 times more).
This is also the origin of the old "props are 12 times too dark" fit (`prop_gain` 0.086), which only hid the problem.

**Control room through the doorway (preview pink and bright, engine near black): cause NOT established; excluded, with evidence.**
- Not the runtime lights or a limit (section 4 of ENGINE-SHADERS.md; the state is the same in the dark frame, where there are no runtime lights: the engine doorway is black in `dark_generator_room_1` too).
- Not exposure (same in the dark frame at the fixed -3 EV).
- Not props: with `prop_gain` 0 the doorway region keeps its colour (world lightmap value 0.012 / 0.005 / 0.005 per pixel mean, red 2.4 times green).
- Not the lightmap data: the compiled `lightmap/secondary.dds` equals `bake.npz` (A and B, median ratio 0.9995, 0 of 73,424 texels with A > 0.05 below 0.2 times the bake).
- Not the techset or the tint alone: the red custom materials of that room (`iwz_panel_wall_red`, `iwz_ceil_red`, `iwz_panel_dark_red`, colorTint (1, 0.42, 0.38) ..) use the same techset as their stock bases
  (`w_l_sm_replace_i0c0s0o0n0q0p0`), and a tint cannot make the room black.
What remains: the engine draws these surfaces with a lightmap term far below the file (the pixel is also near black from inside the room, `lit_control_room_1`, where the engine room is grey blue with no red wash). The deciding
measurement is one RenderDoc capture of that view (the draw of a control room wall: which lightmap texels `t3` / `t4`, `cb3[0]` tint, and its HDR output), which needs a game run and is therefore left to the lead.

## What it cannot show

FX and particles; the engine's light grid lighting of models (direction, specular, SH order 1 bands) and
reflection probes; specular, normal maps and gloss (colour map only); the vision / tone mapping / bloom of the engine
(the engine tone map is used since 22 Nov, see "State of the lighting"; bloom is approximated); the first person weapon, hands and HUD; Umbra culling (everything in the
frustum is drawn, so a view can show things the engine culls); anything that happens in play (doors, power state beyond the
`lit_*` capture, zombies). Light fixtures that have an `on` variant show the single model the emit lists.

## Measured (see the table below)

First round (22 Nov 2026, superseded by the table below), run on the g27r emit (`level/src_g27r_lm`), the 15 `lit_*_1` engine frames of `finish/frames/rc4_g27r` and the plan
`finish/plans/szf_rc4_look.json` (1280 x 720, one fixed mask for weapon, hands, watermark and corner icon):

* **Camera**, fitted once for all frames (not per frame): eye height **60 units** above the `setorigin` origin and horizontal fov
  **80.8 degrees**. Edge IoU over the grid: fov at eye 60 peaks at 85 (coarse grid of 9), the eye x fov grid peaks at eye 60, the fine stage
  gives 78: 0.377, 79: 0.415, 80: 0.492, 80.8: 0.531, 81: 0.530, 82: 0.469. 80.8 degrees is exactly the horizontal fov that
  `cg_fov 65` (4:3 based) gives on 16:9, so the fit found the engine default, and 60 units is the standing eye height. The older
  `bake/lm_measure.py` grid (118 to 150 degrees) uses another fov convention and does not apply here.
* **Exposure**: one global pair, display = clip(k * radiance) ^ p with k = 0.169, p = 0.500 (p sits on the lower end of its [0.5, 1] grid).
  No single curve reconciles the frames: the engine's mean luminance varies much less between views than the lightmap predicts
  (the runtime lights the preview did not have, and the engine's auto exposure; this explanation is from the withdrawn lit-frame fit), so the per-frame luminance ratio keeps a spread of 0.42 to 3.4 after the
  fit (log rms 0.572, was 1.144 with exposure 1). Use the luminance column as "how far is this view's brightness from the engine",
  never as a match.
* Edge IoU (Sobel of the blurred log luminance, strongest 6 % of the unmasked pixels, 3 px tolerance): mean 0.270 before, 0.547 after.
  It counts texture and prop edges too, so it is a relative measure for the camera fit, not a percentage of agreement. "Before" is the
  first probe: eye 64, fov 90 (18 mm lens), exposure 1.

| frame | edge IoU before | lum ratio before | edge IoU after | lum ratio after |
|---|---|---|---|---|
| lit_ticket_hall_1 | 0.309 | 0.147 | 0.647 | 0.423 |
| lit_stair_a_1 | 0.405 | 1.615 | 0.694 | 2.551 |
| lit_platform_a_1 | 0.218 | 0.347 | 0.502 | 1.260 |
| lit_maint_corridor_1 | 0.304 | 0.222 | 0.546 | 0.784 |
| lit_generator_room_1 | 0.256 | 0.284 | 0.616 | 0.866 |
| lit_control_room_1 | 0.213 | 0.265 | 0.681 | 0.873 |
| lit_service_tunnel_1 | 0.332 | 0.398 | 0.625 | 0.639 |
| lit_platform_b_1 | 0.218 | 0.154 | 0.722 | 0.522 |
| lit_stair_b_1 | 0.192 | 0.720 | 0.566 | 1.063 |
| lit_pap_arch_1 | 0.287 | 0.221 | 0.567 | 0.709 |
| lit_well_w_1 | 0.306 | 1.043 | 0.492 | 1.206 |
| lit_well_e_1 | 0.357 | 0.282 | 0.524 | 0.526 |
| lit_hero_car_1 | 0.206 | 0.723 | 0.412 | 1.357 |
| lit_pap_alcove_1 | 0.251 | 0.669 | 0.344 | 1.791 |
| lit_pap_alcove_2 | 0.190 | 1.882 | 0.260 | 3.422 |
| mean | 0.270 | 0.598 | 0.547 | 1.199 |

### Fidelity round 2 (after the first review)

Table of the 15 frames, old (commit 527ad09) next to new (this commit). "lum ratio" is preview / engine mean luminance after the global
exposure fit (k = 0.253, p = 0.500); edge IoU is at the fitted camera (eye 60, fov 80.8), which did not change.

| frame | edge IoU old | edge IoU new | lum ratio old | lum ratio new | what still differs, by eye |
|---|---|---|---|---|---|
| lit_ticket_hall_1 | 0.647 | 0.770 | 0.423 | 0.430 | Layout, floor grout, pillars and gates now match; the engine has glossy bright white upper tiles and dark ceilings where the preview is flat and warm. |
| lit_stair_a_1 | 0.694 | 0.661 | 2.551 | 2.761 | Same geometry; engine walls are near black with specular glints and bright fixture glare, the preview is a flat mid grey and brighter. |
| lit_platform_a_1 | 0.502 | 0.466 | 1.260 | 1.316 | Engine floor has large tile plates with seams and dark wall tiles with gloss; the preview floor is flat and lighter. |
| lit_maint_corridor_1 | 0.546 | 0.492 | 0.784 | 0.877 | Engine lower walls (metal_panel_dark_01) are near black and glossy, the preview shows them mid grey (unexplained, see audit); fixture glare is missing. |
| lit_generator_room_1 | 0.616 | 0.630 | 0.866 | 0.926 | Barrels, crate and lockers are now dark like the engine; the engine doorway on the left opens onto a black room where the preview shows a lit one, and its ceiling strips glow. |
| lit_control_room_1 | 0.681 | 0.613 | 0.873 | 0.836 | Engine is cool, dark and glossy with a bright red ceiling vent; the preview is warm and flat with a pink desk (the red tinted custom material). |
| lit_service_tunnel_1 | 0.625 | 0.602 | 0.639 | 0.763 | Engine lower walls near black with bright light cones and rail specular; the preview walls are pale grey and the rails flat. |
| lit_platform_b_1 | 0.722 | 0.701 | 0.522 | 0.562 | Engine shows a fire, debris and blue FX props and a darker brick floor; the preview has no FX and a lighter floor. |
| lit_stair_b_1 | 0.566 | 0.571 | 1.063 | 1.192 | Engine green tile walls are saturated and the far window glares white; the preview is desaturated and dim. |
| lit_pap_arch_1 | 0.567 | 0.537 | 0.709 | 0.759 | Engine shows the chain link fence mesh and cool grey walls; the preview draws the fence frames without the mesh (alpha) and warm walls. |
| lit_well_w_1 | 0.492 | 0.435 | 1.206 | 0.797 | Engine platform edge has specular glints and a darker tiled wall; the preview is flat. |
| lit_well_e_1 | 0.524 | 0.519 | 0.526 | 0.468 | Engine tile wall is darker with a strong orange lamp glow and glossy rails; the preview is flatter and paler. |
| lit_hero_car_1 | 0.412 | 0.415 | 1.357 | 0.911 | Car colour, window and fence match; the engine adds broken glass, a dark tunnel ceiling and a glossy tactile strip, the preview floor and ceiling are brighter. |
| lit_pap_alcove_1 | 0.344 | 0.368 | 1.791 | 1.801 | Engine shows the chain link mesh over the cages and a grate floor; the preview has solid frames and a flat floor. |
| lit_pap_alcove_2 | 0.260 | 0.288 | 3.422 | 4.104 | Engine has a large projector prop and a strong orange spot that the preview lacks (no such model in the emit lists), and a grate floor. |
| mean | 0.547 | 0.538 | 1.199 | 1.234 | |

Mean edge IoU went from 0.547 to 0.538 (6 frames up, 9 down, ticket hall 0.647 to 0.770): the new grout, occlusion and darker props add
structure the engine also has but shift the log luminance edges in other frames; the camera is unchanged, so read the edge column as noise of about 0.03.
The mean luminance ratio stays at 1.23 (log rms 0.60): fidelity of materials and props improved, the per view brightness spread did not.

**1. Ticket hall floor.** It is the right image. The floor surface is `w/stone_marble_tile_checker_01` (128 unit repeat);
the material json (template dump and built zone dump agree) has exactly one colour texture, semantic 14
`stone_marble_tile_checker_01_c_..._sg_packed_cs`, and our PNG of it equals GrayWolf's export (mean difference 0.0). The texture
scale is the same as in the engine: the autocorrelation period of the floor rows is 92 px in the preview and 91 px in the engine at the same row.
What differed was the data the engine also uses and the preview ignored: the semantic 15 `..._packed_nog` map carries the tile grout as a
strong dark line in its R channel (occlusion). The preview now multiplies that channel into the non directional lightmap term A
(`E = A * occlusion + B * saturate(D.z)`), which restores the octagon outlines on every material with a `nog` map. R = occlusion is
inferred from the picture (the channels G and A sit at 0.5, a normal; B is thin lines, gloss); weak evidence, flagged.
`iwz_audit.py` writes the per material audit (`material_audit.md` / `.json` next to the table): 94 world materials, 91 STRONG
(exactly one colour texture of semantic 14, or one of semantic 2 for custom / unlit), 0 MEDIUM, 3 WEAK: `iwz_lamp_cool`, `iwz_lamp_warm`,
`iwz_lamp_red` (the stock base `emissive_light_panel_pink` has two semantic 2 textures, `..._neutral_8bit_c` and `..._white_8bit_c`, nothing
tells them apart; the first is used, and the surface saturates anyway). One more material has strong evidence but a visible mismatch
that the data does not explain: `w/metal_panel_dark_01` (lower walls of the maintenance corridor and the service tunnel): its colour map is mid
grey (mean 0.54) while the engine draws near black and glossy, probably a metal material whose diffuse is suppressed by a channel
the dumps do not carry as a separate map.

**2. Props too bright.** The model and texture are right (a close-up of the barrels shows the stock tan rusty drum). The scale of the light
grid value was wrong: `bake.npz grid` values times 0.886 equal the lightmap irradiance on average per zone (hall 0.091 / 0.093, platform A
0.078 / 0.084), but the engine's props come out about 12 times darker than that. `iwz_preview_render.py props` renders only the props
(RGBA, the world is a holdout) and fits one gain on the prop pixels of the 15 frames: **prop_gain = 0.086** (rms log luminance error 1.37 at gain 1,
0.63 at the fit; a constant per zone instead of the nearest cell is worse, 0.73). The cause of the factor is not known (the grid values in
`probes.txt` / `lighting.txt` are in other units than the lightmap, or the engine applies a probe visibility term). Props near a lamp still come out
brighter than the engine's.

**3. Light fixtures.** Three defects in my first version: the emissive test looked for `em0` but stock techsets say `e0`
(`..._n0e0p0`), so the stock emissive materials (fluorescent bulbs, car lamps) were drawn as lit colour; the colour image of a material
with both semantic 14 and semantic 2 was taken as the semantic 2 one (the emissive map); and the ceiling fixtures were not in the scene at
all, because they are `power_fixtures` of the layout that the level script places when the power is switched on. Now: stock emissive
slots show `emissive map * emissivePara`, unlit techsets (`..unlit..`, `colorTint` = brightness) show colour * tint, power fixtures use their
`on` model (`--power off` for the `off` model), and all self lit surfaces are scaled by EMISSIVE_GAIN = 20 so they saturate like the engine
(the engine frames have thousands of pixels above 0.9; the exact HDR / bloom value is not in the data, so this number is an assumption).

**Specular from reflection probes: does not exist.** The reflection probe array (`_reflection_probe_array.iw7Image` in the zone dump) is
on disk, but using it needs the cube array decoded, a probe chosen per surface, and the specular / gloss data per material: the gloss lives in an
unconfirmed channel of the `nog` maps and the specular colour in the colour map alpha (0.05 on average: likely not it). That is more than
the hour allowed; the preview draws no specular, which is the largest remaining visible difference (glossy engine walls, floors and rails).

Side-by-side frames (preview left, engine right) are written to `<out>/sidebyside/`; this run's are in
`IW7-Runtime/iwz-stage2/finish/preview/g27r/sidebyside/`.

Resolution on this emit (`report.json`): world materials 94 resolved / 0 unresolved; model materials 246 resolved / 0 unresolved;
models 86 resolved / 0 unresolved (420 instances, door dressing left out). The custom `iwz_*` models and materials come from the built zone dump
(`level/ztwork/zonetool/cp_iwz`). A material or model missing from every dump is listed with its reason and drawn magenta.

Mean radiance luminance per zone in the preview (all 121 layout views, linear, before exposure): ticket_hall 0.0151, stair_a 0.0491,
platform_a 0.0138, maint_corridor 0.0144, generator_room 0.0150, control_room 0.0086, service_tunnel 0.0186, platform_b 0.0124,
stair_b 0.0381 (`zone_luminance.json` is written by `render`).

Time, warm cache, one Blender process: load 1.8 s (dump index 0.06, source 0.01, lightmap 0.49, world mesh and materials 0.21, props
0.89, overlays 0.09), then 0.38 s per rendered view (121 views in 45.7 s; the first view of a process is 1 to 2 s while EEVEE
compiles the materials). Tone mapping and PNG writing in Python add about 0.18 s per frame. The calibration run (camera sweep over
about 40 camera settings x 15 frames, edge scoring, exposure fit) takes about 7 minutes; `--tone-only` keeps the camera and takes
about 50 s. Cold cache, first run of the early version on this machine: dump index walk 22 s, texture decode 4.9 s (world) and 7.8 s (first 49 props), first render 22 s.

