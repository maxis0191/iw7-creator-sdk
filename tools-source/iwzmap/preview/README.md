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
| `iwz_calib.py` | the metrics (edge IoU, mean luminance, global tone fit) |
| `calibration.json` | the fitted global camera (eye height, horizontal fov) and tone (exposure `k`, gamma `p`) |

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

## What it cannot show

FX and particles; the engine's light grid lighting of models (direction, specular, SH order 1 bands) and
reflection probes; specular, normal maps and gloss (colour map only); the vision / tone mapping / bloom of the engine
(replaced by one fitted exposure and gamma); the first person weapon, hands and HUD; Umbra culling (everything in the
frustum is drawn, so a view can show things the engine culls); anything that happens in play (doors, power state beyond the
`lit_*` capture, zombies). Light fixtures that have an `on` variant show the single model the emit lists.

## Measured (see the table below)

Run of 22 Nov 2026 on the g27r emit (`level/src_g27r_lm`), the 15 `lit_*_1` engine frames of `finish/frames/rc4_g27r` and the plan
`finish/plans/szf_rc4_look.json` (1280 x 720, one fixed mask for weapon, hands, watermark and corner icon):

* **Camera**, fitted once for all frames (not per frame): eye height **60 units** above the `setorigin` origin and horizontal fov
  **80.8 degrees**. Edge IoU over the grid: fov at eye 60 peaks at 85 (coarse grid of 9), the eye x fov grid peaks at eye 60, the fine stage
  gives 78: 0.377, 79: 0.415, 80: 0.492, 80.8: 0.531, 81: 0.530, 82: 0.469. 80.8 degrees is exactly the horizontal fov that
  `cg_fov 65` (4:3 based) gives on 16:9, so the fit found the engine default, and 60 units is the standing eye height. The older
  `bake/lm_measure.py` grid (118 to 150 degrees) uses another fov convention and does not apply here.
* **Exposure**: one global pair, display = clip(k * radiance) ^ p with k = 0.169, p = 0.500 (p sits on the lower end of its [0.5, 1] grid).
  No single curve reconciles the frames: the engine's mean luminance varies much less between views than the lightmap predicts
  (auto exposure and lighting terms the preview does not have), so the per-frame luminance ratio keeps a spread of 0.42 to 3.4 after the
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

