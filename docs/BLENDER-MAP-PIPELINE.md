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

### L: what was found (22 Nov 2026)

The g27r bake is a darkness bake: the lightmap holds the 56 emergency lights only (`bake.json` lights 56,
`darkness.json` baked_emergency 56); the 72 named lights of the power banks are runtime lights switched on by the level
script. The capture plan `szf_rc4_look.json` shoots `dark_*` with the power off and `lit_*` 15 s after
`sz_power_direct power 20`. The first preview calibration (exposure `k`, `prop_gain 0.086`, emissive gain 20) fitted the
lightmap-only render against the `lit_*` frames, so its constants and its "reflections / auto exposure" explanation are
not valid. Order of work: tonemap from the engine's own shader and constants (RenderDoc captures on disk), calibrate the
lightmap-only state against `dark_*`, then add the runtime lights with the engine's falloff and calibrate against
`lit_*`. Open: in `lit_generator_room_1` the control room behind the open door is black while its bank is on; candidate
causes are a per-view limit on runtime lights in the engine, or a bank that did not switch on.

## State

- 22 Nov 2026: plan written; L, N, E started.
- 22 Nov 2026, N: `navfmt.py` + `navgen.py` built and proven offline ([NAVMESH](NAVMESH.md)): the stock graph has N-gons and stacked floors, kd splits on z; the generator writes quads on any number of floors. g27r regenerated from its collision: 10,832 areas (shipped 10,262), emitcheck 1 error; two-storey fixture `tools-source/iwzmap/fixtures/twostorey` passes emitcheck, route bottom to top 1,403 units. Not yet proven in game (lead, Forge).
