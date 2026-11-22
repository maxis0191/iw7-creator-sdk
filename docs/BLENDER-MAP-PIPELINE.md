# Blender map pipeline: author an IW7 zombies map in Blender, play it in IW7

Owner request, 22 Nov 2026: stop building maps blind (code, full build, in-game screenshot). Author in a tool where the
result is visible in real time, and give the dev kit what it needs so that a map made there reaches IW7 Zombies with no
manual step. Decided by the lead the same day; this page is the plan and its state. Update it in the same change as the
work.

## Why Blender

- It is already driven by the agents (the `blender` MCP server on the owner's machine; `blender -b --python` for workers).
- The preview tool (`tools-source/iwzmap/preview/`) already loads IW7 geometry, stock models, materials and baked lightmaps
  into it: the editor and the viewer are the same program.
- Free, scriptable in Python (the same language as the map compiler), handles meshes, UVs, lights, cameras and custom
  properties. A brush editor (Radiant, TrenchBroom) would give brushes only, a second viewer and no agent control.

## The chain

```
Blender scene (iwz add-on)  ->  blend2iwz export  ->  emit source folder  ->  lmbake  ->  zone build  ->  usermap  ->  Forge plans
  meshes + IW7 materials         world.bin, colmap.hkx, navgraph.bin, ents.txt, triggers.txt, scriptables.txt,
  stock props (linked)           lighting.txt, probes.txt, layout.json, plan.json, cp_iwz.gsc, custom_materials.json
  entities (empties + props)
  lights (power groups)
```

What already takes free-form triangles: `world.bin` (`mapgen.write_world`), collision (`hkcm_write.encode`: a triangle
soup; degenerate triangles are dropped because they crash the server), the lightmap baker (`bake/lmbake.py` on world.bin),
the conservative Umbra tome (`-iwzcompile`).

What does not:
- **Navigation**: `mapgen.nav_graph` writes one quad area per 32-unit grid column (one floor height per column), so a
  floor over another floor is impossible. Workstream N replaces it.
- **Build scripts**: `build-sz2.ps1` / `build-g.ps1` carry Station Zero specifics (portal names for `volume_check`,
  `sz2_assemble`, door blockers as brush sub-models `*N` from `sz2_submodels.json`, audio layout, perk kit). Workstream E
  writes the contract and a generic build entry.
- Limits to check on free-form meshes: u16 indices per surface (split surfaces), one lightmap chart per planar group in
  `lmbake` (curved meshes), axis-aligned zone boxes for the light grid and spawn volumes.

## Workstreams

| | Owner | Output | Done when |
|---|---|---|---|
| L: preview lighting | worker (Sonnet) | preview matches the engine in both power states | see below |
| N: navigation | worker (Sonnet), engine proof by the lead | `navgen.py`: navmesh from collision triangles, any number of floors | the decoded stock format is documented; a two-storey graph passes `iwz_emitcheck`; zombies cross both floors in game (lead, Forge) |
| E: Blender add-on and exporter | worker (Sonnet) | `tools-source/iwzmap/blender/` add-on + `blend2iwz.py` + generic build entry | g27r emit round-trips through Blender with no `iwz_emitcheck` difference that matters; a new map authored in Blender builds and plays |
| P: proof map | lead | a new two-floor map authored in Blender: door, power, a perk, a wall buy, spawners | built once, Forge plans: spawn, walk both floors, zombies chase across floors, door buy, power, perk |

### L: state (22 Nov 2026)

The g27r bake is a darkness bake: the lightmap holds the 56 emergency lights only; the 72 named lights of the power banks are runtime lights switched on by the level script.
The capture plan `szf_rc4_look.json` shoots `dark_*` with the power off and `lit_*` 15 s after `sz_power_direct power 20`. The first preview calibration fitted a lightmap-only render against the
`lit_*` frames (wrong state) and is withdrawn, with its "reflections / auto exposure" explanation.

Done, with evidence in `tools-source/iwzmap/preview/` (`README.md` "State of the lighting", `ENGINE-SHADERS.md`):

* Engine tone map read from the shader of a stock RenderDoc capture (offline, `rdoc_inspect.py`): reproduces the engine's post pass to 0.25 of an 8 bit level (mean), 0.61 max. Exposure is a scale on the
  curve constants written by the exposure compute pass; dark frames fit 2^-3.01, the dark vision's `tonemapMaxExposure -3`.
* Lightmapped world shader and runtime light falloff documented with instruction lines (smoothstep of `saturate(k (1 - d / R))`, radius R).
* Dark state: 15 `dark_*` frames, mean edge IoU 0.556, median luminance ratio 1.13, no fitted parameter. Lit state: runtime lights added per pixel (`iwz_lights.py`), mean edge IoU 0.528 -> 0.557,
  pattern error 1.81 -> 1.66, one fitted light unit (1e-3), exposure per frame fitted (auto exposure not modelled).
* Control room dark through the generator room door: not an engine limit (at most 7 lights cover a pixel against a limit of 64; 256 light records per view).

Round 2 (22 Nov 2026): albedo `rgb^2`, nog R as gloss (no occlusion); the engine's exposure pass as a steady state model (saturates at the maximum exposure for 10 of 15 lit frames, the engine wants about 1 stop less: open);
the module's flashlight added (FLU fitted on the dark frames: dark pattern error 1.56 -> 1.24; the lit state is still not matched); specular from reflection probes not done (missing pieces listed); barrels: preview light grid
nearest cell too hot (established); control room doorway: lights, exposure, props, lightmap data and techset excluded, cause open until a capture of that view.

Open: the unit of a light record (CPU side), auto exposure of the lit vision, the lit vision's colour grade and curve constants (no capture of the generated map in the lit vision), specular and reflection
probes, shadows of the 9 shadowed lights, the flashlight.

## State

- 22 Nov 2026: plan written; L, N, E started.
- 22 Nov 2026: L: tone map and lighting read from the engine, dark and lit states measured (see L).
