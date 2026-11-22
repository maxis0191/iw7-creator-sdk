# Map builder, final product: acceptance and state

Owner, 22 Nov 2026 (evening): the Blender map builder is a prototype until it is proven on real content. "Make it perfect.
Prove it by building a whole new section, remaking sections that feel too generic and have too little ambition (most of the
screenshots are blank areas with a few props). Not a prototype." This page is the acceptance list and its state; the plan of the
pipeline itself is [BLENDER-MAP-PIPELINE](BLENDER-MAP-PIPELINE.md). Nothing here is "done" until its line says measured.

## The product (owner, 22 Nov 2026, late: "make the tools perfect; build fast; it works in the game as soon as you build it; any tool, or our own")

The tool comes first; the sections further down are its demonstration, not the goal. The map builder is four parts:

1. **Live link: the game is the viewport.** A game session stays up on the map being made. A prop, a light or an entity placed,
   moved or deleted in any front end appears in the running game within a second, and a frame comes back on request. The same
   link is an editor inside the game: fly, pick a model, place, turn, snap, delete, save. Found 22 Nov: Forge client cells already
   take console commands (the game's stdin, `forge/winproc.py command`) and server cells take rcon; a script that reads a dvar
   every server frame can spawn and move models. What is missing is the session that stays open (`forge live`) and the script.
2. **Fast compiler.** Geometry is the one thing that needs a build. Target: saved change to playable map in 20 s or less
   (measured today: 403 s build + 154 s bake for Station Zero, 164 to 198 s for a 360-triangle map, nearly all of it stock content
   copied again into every map). Means: the stock-derived content built once into a base zone, incremental stages, a warm game
   that reloads the map and puts the camera back.
3. **One map document, three front ends.** A text document (geometry meshes, kit pieces, entities, lights, layers) that the Python
   API (`iwz_author`), the Blender add-on and the in-game editor all read and write; layers let authored sections sit on a generated
   base. Every stock model of every dumped zone is placeable; the build imports what a map uses.
4. **Proof and delivery by construction.** The gates and the in-game test plans are generated from the document (reach, doors,
   power, perks, rounds); one command gives the map its own name, browser entry and package.

| # | Tool line | Measure | State |
|---|---|---|---|
| T1 | Live edit | prop or light change visible in the running game in under 1 s; a frame back in under 2 s; 50 edits in a row without a restart | open |
| T2 | Geometry to game | a geometry change playable in 20 s or less, camera back at the same spot (before: 403 s + 154 s) | open |
| T3 | In-game editor | place, move, turn, delete, save with keys in the game; the saved document rebuilds to the same placement (positions within 0.1) | open |
| T4 | One document | the same map written by the Python API, Blender and the in-game editor round-trips with no loss | open |
| T5 | Any stock model | a model of any dumped zone placed live and in a build with no hand step | open |
| T6 | Gameplay kit and tests | doors, power, perks, wall buys, wheel, Pack-a-Punch, spawn zones placed as objects; the test plan generated from the document passes | open |
| T7 | Delivery | one command: own name, browser entry, package; two maps side by side | open |

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

## Acceptance of the demonstration (after the tool lines above)

| # | Line | Measure | State |
|---|---|---|---|
| A1 | Station Zero through the builder with no section is the same map | emit files byte-identical to the base emit | open |
| A2 | The RC4 gameplay suite still passes on the map with the sections | doors 70/70, economy 76/76, wells 9/9, stairs 9/9, post routes 128/128, start closed 20/20 | open |
| A3 | The new section plays | door D4 buys and opens; zombies spawn in the Arcade and reach the player; rounds run with the player there; perk, wall buys | open |
| A4 | Density at the stock level | props, distinct models and materials per 1000 x 1000 of floor against a measured stock reference (numbers below once measured) | open |
| A5 | Look | three independent reviewers, in-game frames at fixed cameras, stock frames as reference: 7.5 or more of 10 for each of the three sections (RC4: 6.5 lit, about 5 dark) | open |
| A6 | Loop | a geometry-only change of a section to a playable map: measured before (403 s build + 154 s bake) and after | open |
| A7 | A map of its own | a generic Blender map with its own name, arena, title and browser art; two installed side by side | open |
| A8 | Stairs | a second flight (rotated, both sides open) passes climb and descent over several uncached runs | open |
| A9 | Landed | everything on main, checks on the exact head, author guide, DEVKIT row | open |

The preview (`tools-source/iwzmap/preview/`) serves composition only: its lit state is not matched to the engine yet.

## State

- 22 Nov 2026: acceptance written; work started.
