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
  unlit. Alpha-test techsets (`_atest_`) clip, blend techsets and decal customs blend.
* **Props**: layout decor and models (door dressing left out: the capture plans open the doors) as real LOD0 meshes
  with their colour textures, one mesh per model, objects linked to it. Instances are lit with the **light grid**
  (`bake.npz` `grid`: order-1 SH constant term of the kept probe cells, nearest cell within 192 units, else the mean of the
  kept cells, `E = 0.886 * c0`), constant per instance through the object colour, no direction.
* **Overlays** (collection `overlays`, hidden from render; `--overlays` shows them): spawners (arrows), doors, door blockers,
  zone volumes, nav cells (`plan.json` cells, 32 unit cells), collision (`colmap.hkx` through `hkcm.py`, wireframe).
* **Views**: `layout.json` `views` as `<zone>_<n>` and, with `--plan`, every `tour` view of a capture plan as `plan_<name>`.
  Camera = player origin + eye height, yaw, pitch (`gl_tp` does `setorigin` + `setplayerangles((pitch, yaw, 0))`).

Anything unresolved is **magenta** and listed with its reason in `report.json` (`materials.unresolved_list`,
`models.unresolved_list`); nothing is given a silent fake colour. A missing model is drawn as a 32 x 32 x 32 unit
magenta box at its origin.

## What it cannot show

FX and particles; the engine's light grid lighting of models (direction, specular, SH order 1 bands) and
reflection probes; specular, normal maps and gloss (colour map only); the vision / tone mapping / bloom of the engine
(replaced by one fitted exposure and gamma); the first person weapon, hands and HUD; Umbra culling (everything in the
frustum is drawn, so a view can show things the engine culls); anything that happens in play (doors, power state beyond the
`lit_*` capture, zombies). Light fixtures that have an `on` variant show the single model the emit lists.

## Measured (see the table below)

<!-- RESULTS -->
