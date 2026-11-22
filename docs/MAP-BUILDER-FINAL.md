# Map builder, final product: acceptance and state

Owner, 22 Nov 2026 (evening): the Blender map builder is a prototype until it is proven on real content. "Make it perfect.
Prove it by building a whole new section, remaking sections that feel too generic and have too little ambition (most of the
screenshots are blank areas with a few props). Not a prototype." This page is the acceptance list and its state; the plan of the
pipeline itself is [BLENDER-MAP-PIPELINE](BLENDER-MAP-PIPELINE.md). Nothing here is "done" until its line says measured.

## Design decisions (lead, 22 Nov 2026)

1. **Sections on a base.** Station Zero stays generated (`station_zero2.py`, `build-g.ps1`); Blender replaces or adds whole
   sections on top of that base emit. Untouched zones pass through byte-identical. A full import and re-export loses content
   today (193 of 518 entities, 0 of 4 stairs), so it is not the route.
2. **Navigation.** Remade sections keep the base navigation (the floor plan stays; new solid collision removes the cells it
   blocks). A new section gets `navgen` quads on the same 32-unit lattice, stitched to the base cells. Walkable edges stay on the
   16/32 grid until polygon areas are proven in game; the richness goes into render geometry, props and clip.
3. **Content.** Dense, layered dressing from the stock game's own models (every dumped zone, imported by `kit_import.py`), world
   materials, decals, signs, FX and baked lights, authored in Blender with the real meshes and textures in the viewport.
4. **Proof sections.** New: the Underpass Arcade of the bible (`docs/station-zero/02-WORLD.md`, zone 4: x -3000..-1200,
   y 3500..4300 plus five shop bays, door D4 from the Fare Hall). Remade: the Fare Hall (`ticket_hall`) and Platform A.
5. **One compiler** for every map build: the one of the current Station Zero release (`zonetool-lightvol-ea60b19.exe`), named in
   one place.

## Acceptance

| # | Line | Measure | State |
|---|---|---|---|
| A1 | Station Zero through the builder with no section is the same map | emit files byte-identical to the base emit | open |
| A2 | The RC4 gameplay suite still passes on the map with the sections | doors 70/70, economy 76/76, wells 9/9, stairs 9/9, post routes 128/128, start closed 20/20 | open |
| A3 | The new section plays | door D4 buys and opens; zombies spawn in the Arcade and reach the player; rounds run with the player there; perk, wall buys | open |
| A4 | Density at the stock level | per 1000 x 1000 of floor: at least 500 props, 110 distinct models, 100 world materials, 20 lights (stock cp_zmb, five densest covered 1000 x 1000 areas: 512 to 840 props, 116 to 162 models, 100 to 189 materials, 22 to 38 lights; Station Zero zones today: 26 to 160 props, 4 to 38 models a zone; method and table in [ASSET-LIBRARY](ASSET-LIBRARY.md)) | open (target measured 22 Nov) |
| A5 | Look | three independent reviewers, in-game frames at fixed cameras, stock frames as reference: 7.5 or more of 10 for each of the three sections (RC4: 6.5 lit, about 5 dark) | open |
| A6 | Loop | a geometry-only change of a section to a playable map: measured before (403 s build + 154 s bake) and after | open |
| A7 | A map of its own | a generic Blender map with its own name, arena, title and browser art; two installed side by side | open |
| A8 | Stairs | a second flight (rotated, both sides open) passes climb and descent over several uncached runs | open |
| A9 | Landed | everything on main, checks on the exact head, author guide, DEVKIT row | open |

The preview (`tools-source/iwzmap/preview/`) serves composition only: its lit state is not matched to the engine yet.

## State

- 22 Nov 2026: acceptance written; work started.
- 22 Nov 2026: A4 target measured (asset library: stock density, caps of the compiler, contact sheets of the stock models): [ASSET-LIBRARY](ASSET-LIBRARY.md).
