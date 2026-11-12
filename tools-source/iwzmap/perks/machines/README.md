# Perk machine models (package P2)

The four new perk machines of `docs/station-zero/06-PERKS.md` section 2, made from code: Baker's Dozens, Bon Voyages,
Sour Grudges and Double Takes. They are rigid script models (`iwz_perk_machine_bakers`, `_voyage`, `_grudge` and
`_double`). The front faces +X, the origin is at the floor centre, and the units are inches. All art is drawn here; nothing
is taken from another game.

| File | What it does |
|---|---|
| `make_machine_art.py` | Draws the textures with PIL: one 1024 atlas per machine (signs, labels, dial, drum and globe contents, curtain), its emissive mask, the atlas rectangles, and the tileable enamel, walnut, kraft and metal maps. |
| `swap_stock_glass.py` | Runs after the port. It points the glass surfaces (the drum, the globe, the hopper) at the stock clear glass `mo/glass_clear_model_no_imp`, which the Station Zero zone csv references. It also drops the baked stand-in and puts the stock material definition in its place, so `kit_import.py` shares the material instead of copying it. |
| `perk_machines.py` | Headless Blender script. It builds the geometry onto those rectangles, writes one `.glb` plus one `.materials.json` per machine for env-model, and makes review renders (3/4 view at about 3 m, and a dim view at about 4.5 m). `--roundtrip <port>` renders the models read back from the game dump instead. |

## Commands (no game, no ZoneTool)

```powershell
$M = 'C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\level\p1\machines'
$E = '<x64-zt-extensions>\tools-source\asset-bridge\env-model'
python -B make_machine_art.py "$M\art"
blender -b --factory-startup -P perk_machines.py -- --art "$M\art" --out "$M\authored" --renders "$M\renders"
python -B "$E\t7_env_port.py" --manifest "$M\port.json" --out "$M\port"        # zone-ready dump root
python -B swap_stock_glass.py "$M\port"                                         # glass -> stock clear glass
python -B "$E\iw7_model_to_glb.py" "$M\port" iwz_perk_machine_bakers "$M\port\readback\iwz_perk_machine_bakers.glb"
blender -b --factory-startup -P perk_machines.py -- --art "$M\art" --out "$M\authored" --renders "$M\renders\readback" --roundtrip "$M\port"
```

`port.json` lists one model per machine, with the part `{"glb": "<authored>\iwz_perk_machine_<m>.glb"}` and
`collision {"voxel": 4, "exclude": ["glow"]}`. It also sets `templates` (the `techsets_cp_zmb` dump of
`iwz-map-ref-a`), `texconv`, `prefix "mo/t7e_"` and `texture_size 1024`. Its `export_dir` must point at an existing
folder that has a `models` subfolder (an empty one is enough). Without it, `t7_env_port.py` asks for a GrayWolf export,
even when every part is an authored glb.

## Into the map zone

A script model does not need the static-model route (TF10): no `smodels.txt` row, no `kit_import.py --stage-xmodels`,
and no light-grid draw instance. Two things are needed:

1. The kit import puts each model into the zone csv as an `xmodel,<name>` row. Pass these to `build-sz2.ps1`:
   `-KitModels 'perks:iwz_perk_machine_bakers,perks:iwz_perk_machine_voyage,perks:iwz_perk_machine_grudge,perks:iwz_perk_machine_double'`
   and `-KitDumps 'perks=<M>\port'`.
2. `scenegen.py` gives the `script_model` entity the model name. `PERK_NEW` gets the four new model names in place
   of the stock placeholder bodies.

Material limits of the route:
- Opaque materials use the `mo/barrier_handrail` template. Emissive materials use `mo/signage_exit_sign_emergency_on`,
  with `emissivePara` 3.0 as on the stock exit sign. Both techsets are shared from the template map's
  `techsets_cp_zmb` at runtime.
- Glass is never baked: the env-model glass template glowed lavender in g27. The drum, the globe and the hopper use
  the stock `mo/glass_clear_model_no_imp` (additive clear glass) over real 3D sweets (24 triangles each) and a packed,
  lit core.
- Images are BC7 and their pixels are embedded in the zone.
- Each material bakes at the size of its largest map, up to `texture_size`. Non-square maps are squared, and constant
  maps drop to 16 px.
