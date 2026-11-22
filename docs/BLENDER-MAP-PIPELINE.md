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

### E: Blender add-on, exporter and generic build (22 Nov 2026, built; nothing of it built into a zone or played yet)

Contract of the emit folder: [IWZ-EMIT-CONTRACT.md](IWZ-EMIT-CONTRACT.md). Author guide: [tools-source/iwzmap/blender/README.md](../tools-source/iwzmap/blender/README.md).

- **Built**: `iwz_addon` (sidebar panel IW7: stock material and model pickers, entity buttons, Validate, Export, Preview),
  `blend2iwz.py` + `blend_core.py` (scene to emit folder; `BlendEmitter` subclasses `scenegen.Emitter`, so entities, door
  blockers, perk / wall weapon / wheel tables and the level script come from the same code as Station Zero), `iwz2blend.py` (emit
  to Blender), `build-blend.ps1` (generic zone build, header lists the steps; **not run**).
- **Round trip, no game** (Station Zero g27r, `level/src_g27r_lm` into Blender and back, `roundtrip_diff.py`): collision **34,036 of
  34,036 triangles identical** with the four surface tags (382, 387, 402, 411) preserved; world 27,464 of 27,608 triangles identical
  (areas equal to the unit, 116,651,662; the other 144 differ in corner order or are 24 degenerate triangles dropped on purpose);
  27,580 of 27,608 vertices keep position and baked lightmap uv; 263 surfaces both. Typed and regenerated by the exporter: zones
  (9 volumes), 5 doors (their 20 blocker brushes are regenerated under `iwz_door_*` target names, the original names them `pf7_auto*`), 4 starts, 51 spawners, 4 perks, power, 5 wall buys, Pack-a-Punch,
  3 wheels, 150 lights, props, level script. Carried through unchanged in `iwz_layout_extra` (37 layout keys: decor, signs, quest,
  walk, ...) but **not regenerated**: the round trip has 193 entities against 518 (missing: script models of the dressing,
  power fixtures, relays, flicker, perk bodies, door dressing, shutters, 172 anonymous props, the trap; and 5 `interaction` structs),
  layout `decor` 441 to 197, `openings` 14 to 5, `stairs` 4 to 0. `iwz_emitcheck check`: original 0 errors / 18 warnings; round trip
  1 error (one NAV_FLOATING cell at the top of a stair, single layer fallback) / 25 warnings. Navigation cells 10,262 original,
  9,602 single layer fallback, 10,822 with navgen (0 problems; `walk_cells_without_nav` 5,133 original, 7,777 fallback, 2,943 navgen).
- **testmap1** (two ground rooms, door 750, a 17 step flight to an upper room over room A, power, one perk, one wall buy, 6 spawners,
  2 starts, 5 lights): authored by `blender/make_testmap1.py`; with the single layer fallback the upper floor has no navigation (2
  problems, `sz2_navconn` 11 fails on the stair seams); with navgen (branch `claude/iwz-navgen`, `IWZ_NAVGEN_DIR`) 496 cells over both
  floors, 0 problems, `iwz_emitcheck` 0 errors 0 warnings.
- **Not done**: player-only and monster-only clip (the surface table contents are not decoded: only the tags 382, 387, 402, 411 are
  known); rotated doors; two storey navigation without navgen; the panel was not looked at (its operators run headless); the build
  script has not run; the navgen call path (`navgen.generate(..., seeds=, detail=True)`) was exercised only against the unmerged branch.

## State

- 22 Nov 2026: plan written; L, N, E started.
- 22 Nov 2026: E built (add-on, exporter, importer, generic build script, contract); round trip of g27r measured; testmap1 exported. Waits on: navgen merged (N), the lead's first zone build of testmap1 (P).
- 22 Nov 2026 (E, after the first build of testmap1): stairs need the stock clip ramp. `iwz_stair` on the step meshes makes `blend2iwz` add the nosing ramp sheet (testmap1: 2 triangles, 25.2 degrees, 43,288,0 to 332,288,136, 112 wide); an export with two linked navigation cells more than 18 apart is refused (without the ramp: 101.7 to 120.5 at (304, 304), the step `iwz_emitcheck reach` flagged).
- 22 Nov 2026 (E, round 3): `blend_core` adapted to the round-2 polygon navgen (`IWZ_NAVGEN_DIR`, navgraph.bin unchanged, lattice cells and area links derived from the polygons; the over-18 refusal judges the height difference at each shared edge). testmap1 `emit_poly`: 212 areas, 812 links, 544 plan cells, `iwz_emitcheck check` (navgen branch) 0 errors, `reach --all-spawners` 6 of 6.

