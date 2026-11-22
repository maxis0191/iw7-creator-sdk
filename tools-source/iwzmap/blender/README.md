# Author an IW7 zombies map in Blender (add-on + exporter)

Written 22 Nov 2026 (workstream E of [../../../docs/BLENDER-MAP-PIPELINE.md](../../../docs/BLENDER-MAP-PIPELINE.md)). The files the
exporter writes are specified in [../../../docs/IWZ-EMIT-CONTRACT.md](../../../docs/IWZ-EMIT-CONTRACT.md).

| File | Role |
| --- | --- |
| `iwz_addon/` | the Blender add-on: sidebar panel (N key, tab **IW7**): material and prop pickers, entity buttons, Validate, Export emit, Preview looks |
| `blend2iwz.py` | inside Blender (interactive or `-b`): reads the scene into a plain dict (`collect_scene`) and calls the exporter; CLI `export` / `validate` |
| `blend_core.py` | pure Python (no bpy): `validate`, `export_scene` (a subclass of `scenegen.Emitter`), `nav_single_layer`, `WorldBuilder` |
| `iwz2blend.py` | the reverse: an emit folder (world, collision, entities, lights, props) into Blender |
| `make_testmap1.py` | authors the two-floor test map by script, as a map author would, saves the .blend and exports |
| `roundtrip_diff.py` | compares two emit folders (original and round trip) |
| `addon_headless_test.py`, `tests/test_blend_core.py` | proofs: add-on registers and every operator runs; the pure part (16 tests) |
| `../build-blend.ps1` | the generic zone build from an emit folder |

## Install and open

1. Blender 4.2 or later (tested on 5.2). Edit > Preferences > Add-ons > Install from Disk, on a zip of the folder `iwz_addon`;
   or from the command line `blender --python-expr "import sys; sys.path.insert(0, r'<repo>/tools-source/iwzmap/blender'); import iwz_addon; iwz_addon.register()"`.
   The add-on finds `blend2iwz.py` next to its folder, or in `IWZ_BLENDER_TOOLS`.
2. The stock catalogue (1,179 world materials, 7,394 models) and the textures come from the dumps (`IWZ_RUNTIME`, see
   `preview/README.md`): press **Load stock catalog** once. Without dumps the add-on still works, materials are plain grey and a box
   stands in for a model; only the names matter for the export.
3. Exporting needs no add-on: `blender -b map.blend --python blend2iwz.py -- export --out <emit>`.

## Units, axes, collections

* **1 Blender unit = 1 metre = 39.37 IW7 inches** (the preview uses the same factor). IW7 axes are Blender's (x east, y north, z up),
  nothing is swapped. Yaw is rotation about Z in degrees (0 = +x). Sizes worth knowing in inches: player 72 high (1.83 m), eye
  60, doorway at least 48 wide x 84 high (1.22 x 2.13 m), step riser 8 (0.20 m), stair tread 14.5 to 20 (0.37 to 0.51 m),
  headroom at least 72.
* **IWZ_World**: every mesh in it (children included) is level geometry. A mesh needs a **material slot named after the IW7 world
  material** (`w/concrete_tiles_01`). Per object custom properties: `iwz_mode` = `both` (default) | `render` | `collision`
  (collision only = an invisible solid brush; drawn as wire); `iwz_uv` = `auto` (default: world aligned mapping at the real texture
  scale of the material) | `authored` (the mesh's uv map, v flipped for DDS); `iwz_tag` (expert: raw collision surface tag).
  Modifiers are applied, negative scales are handled. Use flat shaded faces: the exporter writes the face normal (the lightmap
  baker needs a planar shading frame per face).
* **IWZ_Entities / IWZ_Zones**: any object with the custom property `iwz_kind` is an entity (the buttons create them in these
  collections, but the collection does not matter). **IWZ_Props**: any object with `iwz_model` = a stock xmodel name; location,
  rotation (x roll, y pitch, z yaw) and uniform scale are exported to `smodels.txt`.

## Entities

| `iwz_kind` | Object | Properties |
| --- | --- | --- |
| `zone` | a box mesh (wire) | `iwz_name` (lower case, digits, `_`). The **world bounding box** is one spawn volume and one lighting room. Zones must not overlap in 3D: stacked floors need boxes that split at the slab (see testmap1). Zones facing each other across a wall gap of up to 16 inches are padded by half the gap each |
| `door` | a thin box in the doorway (one horizontal side at most 48 inches) | `iwz_cost` 750, 1000, 1250 or 1500; `iwz_zones` `a,b` or empty (detected from the zones on both sides). The doorway itself is left **open** in the render and collision meshes: the closed door's collision is the template debris sub-model (tiled over the box) that the purchase removes |
| `start` | empty | up to 4 (padded to 4 on neighbouring columns) |
| `spawner` | empty | `iwz_spawn` ground, wall (vent, built for you) or ceiling; yaw = the way the zombie faces; `iwz_vent` 0 to skip the vent geometry |
| `power` | empty on the floor | the power switch |
| `perk` | empty on the floor | `iwz_perk` revive, tough, run, rat_a_tat, flash, zap, boom, more, smack, fwoosh; `iwz_powered` 1 = on from the start; at most 6 |
| `wall_buy` | empty on the floor, yaw facing out of the wall | `iwz_weapon_class` pistol, revolver, carbine, smg, rifle, shotgun, marksman, lmg, heavy_shotgun, heavy, or `iwz_weapon` a stock weapon name; `iwz_cost` |
| `pap`, `wheel` | empty | Pack-a-Punch (one), mystery box (up to 9) |
| `marker` | empty | `iwz_marker` kind, `iwz_name` id: a position kept in `layout.json` for game script modules |
| light objects | Blender point or spot light | colour; `iwz_radius` (inches, default the light's custom distance or 420), `iwz_intensity` (2.0), `iwz_group`, `iwz_name`, `iwz_runtime` 1 = also a script switchable light in `lights.txt` |
| camera | any camera | `iwz_zone`: becomes a preview view in `layout.json` (`views`) |

The text datablock `iwz_layout_extra` (JSON) is merged into `layout.json` (keys of a map made elsewhere that the add-on does not
model); scene properties `iwz_map` (map name, default `cp_iwz`) and `iwz_ambient` (r, g, b, up).

## Export and build

```powershell
blender -b map.blend --python tools-source/iwzmap/blender/blend2iwz.py -- validate
blender -b map.blend --python tools-source/iwzmap/blender/blend2iwz.py -- export --out <runtime>\iwz-blend\<name>\emit     # seconds
python -I -B tools-source/iwzmap/iwz_emitcheck.py check <emit>            # the offline gates
pwsh tools-source/iwzmap/build-blend.ps1 -Src <emit> -UmOut <usermaps\cp_iwz> [-Bake]    # the lead's build; the header lists the steps
```

`build-blend.ps1` needs a ZoneTool work folder of its own (`new-work-from-stock.ps1`, default `<runtime>\iwz-blend\ztwork`).

**Validation refuses**: no player start or zone, an overlapping or badly named zone, a door whose cost is not a stock price or that
is not thin, a perk or weapon class that does not exist, a perk placed twice, a mesh material that is not `w/...`. It warns for
a material found in neither the stock table nor the dumps.

## Known limits (what the exporter cannot do yet)

* **Two floors need `navgen.py`** (workstream N, branch `claude/iwz-navgen`, not on main when this was written). The exporter calls
  `navgen.generate(tris, seeds=starts, detail=True)` when it imports (`IWZ_NAVGEN_DIR` names the folder holding `navgen.py` and
  `navfmt.py`). Without it, a single layer height field is written (`nav_single_layer`: the floor reachable from a player start by
  18 unit steps, the lowest in a column with two); every dropped floor is listed in `scene_report.json` and as `PROBLEM` / `WARN`
  lines (a spawner on a floor without navigation is a problem). Measured on testmap1: fallback 260 cells, 2 problems (the two
  upper floor spawners), `iwz_emitcheck check` 0 errors, `sz2_navconn` 11 fails (the stair seams); with navgen 496 cells over both
  floors, 0 problems, `iwz_emitcheck check` 0 errors 0 warnings. **Neither is proven in the game.**
* **Collision tags**: only solid (382) is generated; the contents flags of the template surface table are not decoded, so there is no
  player-only or monster-only clip (a collision-only mesh blocks everything). The stair tags 387, 402 and 411 are preserved on import.
* **Lightmaps**: the exporter writes the neutral placeholder texel; `-Bake` (lmbake) makes the real one. lmbake makes one chart per
  planar facet: measured on a synthetic cylinder, 8, 16 and 32 segments give 8, 16, 32 charts (one a facet), 64 segments give 104
  charts for 128 triangles. Curved meshes cost charts, atlas area and bake time in proportion to their facets.
* **Doors** are axis aligned (the door box is read as its world bounding box). Costs are the four stock debris prices.
* No Station Zero systems (quest, post, darkness, audio, FX) are emitted; the Third Rail trap and door dressing are absent.
* The panel was built headless and its operators run (`addon_headless_test.py`); its drawing was **not looked at**. The preview
  button needs a baked emit (the preview reads `bake.npz`).

## Round trip, measured (22 Nov 2026)

Station Zero g27r (`level/src_g27r_lm`) imported with `iwz2blend.py` and exported again (`roundtrip_diff.py`): see
[../../../docs/BLENDER-MAP-PIPELINE.md](../../../docs/BLENDER-MAP-PIPELINE.md) section E for the table.
