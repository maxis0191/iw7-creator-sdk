# Scene generator: a zombies map from a scene description

`tools-source/iwzmap/scenegen.py` builds a generated IW7 zombies map from one JSON file that says what the map is:
zones and their heights, doors, free links, flights of stairs, pits and raised floors, rooms inside rooms (train
cars, booths), solid blocks, spawner counts, interactions and markers. It replaces hand-written geometry code (the
3,400 lines of `station_zero2.py` for nine zones) with data, and it refuses a layout the game cannot carry before
anything is built.

The first scene is Station Zero's 19 zones from the bible: `tools-source/iwzmap/scenes/station_zero.json`
(`docs/station-zero/02-WORLD.md` sections 2 to 4 and 6).

## Commands

All of them run in seconds and touch nothing but their output folder.

```powershell
python -I -B scenegen.py check   scenes\station_zero.json                     # scene rules; exit 1 on an error
python -I -B scenegen.py emit    scenes\station_zero.json <cp_zmb dump> <src>  # check, then the compiler sources
python -I -B scenegen.py flights <src>                                         # navigation against the stair surface
python -I -B scenegen.py routes  <src> [--pairs a,b;c,d] [--md table.md]       # walking times between zones
python -I -B scenegen.py pools   <src> <cp_zmb dump>                           # template pools and entities used
python -I -B iwz_emitcheck.py check <src>                                      # the offline map gate
python -I -B sz2_navconn.py <src>                                              # navigation connectivity
python -B <server>\ops\iwzmap\iwzmap_ents_lint.py <src>\ents.txt --gsc <src>\cp_iwz.gsc   # stock zombies recipe
```

`<cp_zmb dump>` is the stock template dump (`IWZ_TEMPLATE_DUMP`, default `IW7-Runtime\iwz-map-ref-a\dump\cp_zmb`).
`emit` writes `world.bin`, `colmap.hkx`, `navgraph.bin`, `ents.txt`, `triggers.txt`, `scriptables.txt`,
`lighting.txt`, `probes.txt`, `layout.json`, `plan.json`, `cp_iwz.gsc` (from `cp_iwz3.gsc`), `custom_materials.json`
and `scene_report.json` (areas, counts, entity census, problems). The source then builds like any generated map
(`build-sz2.ps1 -Src <src>`).

## The scene file

```json
{
 "map": "cp_iwz",
 "start": {"zone": "cordon", "points": [[x, y, z, yaw], ...]},
 "zones": [{
   "id": "platform_west", "name": "PLATFORM A WEST",
   "boxes": [[x0, y0, x1, y1], ...],           // plan boxes; boxes of one zone may touch, never overlap
   "floor": -320, "ceiling": 0,                 // the zone floor and its flat ceiling
   "style": "metro", "floor_mat": "conc_tiles", "ceil_mat": "conc_painted", "area_mat": "conc_warm",
   "areas":   [{"id": "pit", "rect": [x0, y0, x1, y1], "z": -384}],                 // floors at another height
   "flights": [{"id": "f", "rect": [...], "up": "+y", "z_lo": -384, "z_hi": -320,  // stairs, stock construction
                "land_lo": 56, "land_hi": 32}],
   "solids":  [{"rect": [...], "z0": -384, "z1": 0, "mat": "conc_dark"}],          // solid blocks
   "enclosures": [{"id": "car1", "rect": [...], "z1": -216,                         // a room inside the zone
                   "openings": {"north": [[s0, s1, top], ...], "east": [...]}}],
   "volumes": [[x0, y0, x1, y1], ...],         // spawn volumes when one bounding box would overlap another zone
   "spawners": {"ground": 9, "wall": 3, "ceiling": 2, "points": [{"kind": "ground", "at": [x, y], "yaw": 0}]},
   "waiting": [[x, y], ...], "skate": [[x0, y0, x1, y1], ...],   // waiting places and the Rollers' skate mask
   "far": false, "plate": true }],
 "doors": [{"id": "D1", "zones": ["a", "b"], "price": 750, "span": [s0, s1], "sill": 0, "height": 224}],
 "links": [{"id": "L1", "zones": ["a", "b"], "kind": "open|arch", "openings": [{"span": [...], "sill": -320}]}],
 "interactions": [{"kind": "perk|wall_buy|wheel|power|pap|trap_third_rail", "zone": "...", "wall": "north", "s": 600, "off": 8}],
 "markers": [{"kind": "hatch", "id": "PLAZA", "zone": "cordon", "at": [x, y]}]
}
```

Units are inches (x east, y north, z up). A door's `span` runs along the shared wall; one door may have several
`openings` (one purchase opens all of them). A placement is `at: [x, y]` or `wall` + `s` (coordinate along the wall)
or `t` (0 to 1) + `off` (distance from the wall); `box` picks the box of a several-box zone. Wall weapons are given
by class (`pistol`, `carbine`, `smg`, `rifle`, `shotgun`, `marksman`, `lmg`, `heavy_shotgun`, `heavy`, `revolver`);
the generator takes the stock weapon of that class from Spaceland's wall-buy list, and marks a stand-in when the list
has none. Markers are positions kept in `layout.json` for later packages (new perks, hatches, clocks, traps that
need their own script).

## What `check` refuses

| Rule | Why |
| --- | --- |
| zones overlapping in plan | the navigation grid holds one height per 32-unit cell: levels are terraces side by side |
| a door or link between zones whose boxes do not face each other across a wall gap of 0 to 16 along the whole opening | a door into a wall |
| a sill that is not the floor height on both sides | a step the navigation cannot cross |
| a flight with risers far from 8 or treads outside 14.5 to 20, narrower than 96, or a low landing shorter than a tread | the stock stair construction; a 32-unit navigation cell on the slope then steps at most 17.7 |
| a flight end that lands on a floor of another height, runs into a wall with no opening, or meets an opening with less than 40 level units | the opening's navigation reaches 24 past the wall plane plus half a cell |
| headroom under 96 anywhere, an opening taller than a ceiling | |
| a zone that is not reachable from the start through doors and links (far boxes excepted) | |
| areas, flights, solids or enclosures outside their zone, areas and flights overlapping | |

`emit` adds what only the built geometry can say: a spawner kind that found no place (flat navigation at least 48
from a wall and 128 from an opening), spawn volumes that overlap.

## How the geometry is made

- Walls follow the outline of a zone's boxes (joins between its own boxes are left open), from the lowest floor of
  the zone to its ceiling, in banded styles, with door, arch and open cuts; a wall gap gets a reveal.
- Flights are the stock stair construction: render treads and risers of about 8; collision a player and monster
  clip sheet over the nosings (surface tag 411), solid risers (387) and bullet-only treads (402) under it; the
  navigation lies 2 above the sheet. A side that drops more than a step gets a guard rail (clip to 42 over the
  sheet); a side against a higher floor gets a trench wall.
- Navigation: 32-unit cells from the zone floors, areas and flights; 24 off walls, 16 off a flight's open sides; a
  flat cell is refused when any corner hangs over a floor of another height; each opening gets cells 24 past both wall
  planes. A seam pass keeps only real steps between cells that share an edge (inside a region up to 18, between
  regions within 3) and removes the lower cell otherwise.
- Doors are stock debris purchases: an interaction struct on each side, a `door_buy` trigger, and blocker brushes
  (copies of the kept template sub-model of `sz2_submodels.json`) as the door's target; the stock `clear_debris`
  makes them non-solid. No template debris scriptable is needed, so the 14 of the template do not limit the doors.
- Spawners are placed by a deterministic farthest-point sample over flat cells; every zone that is not far gets two
  brute / goon spots per spawn volume, two respawn points, an inspection plate on its first ground spawner, a
  standing point (`zone_points`, used by `routes`), waiting places and a skate mask.

## Proven so far

Offline (11 Nov 2026), on the Station Zero scene: `check` clean; `emit` 2.6 s; `iwz_emitcheck check` 0 errors (one
island: the Terminus, a far box, by design); `sz2_navconn` 0 failures; `flights` 14 of 14 within 2.6 of the sheet;
the ents lint finds no blocker. Unit tests: `tests/test_scenegen.py` (scene rules on synthetic layouts; an emitted
synthetic map read back by the gates when a stock dump is present). Nothing about this generator is proven in the
game until the first build of the blockout (package W1a).
