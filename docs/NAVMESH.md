# NavGraph format and the navmesh generator

The navigation of an IW7 zombies map is one bfx NavGraph (graph version 0x2B, the zone's `navmesh` asset). This page is
the format as measured on the stock `cp_zmb` navmesh (ZoneTool dump, 2,865 areas) and the generator that writes it from
collision triangles. Code: `tools-source/iwzmap/navfmt.py` (reader, writer, kd builder), `navgen.py` (generator),
`test_navgen.py`, fixture `fixtures/twostorey/`.

## Where the graph sits in a file

Both forms hold the marker `2B 00 00 00 | 01 00 00 00 | 2B 00 00 00` followed by the graph (`navfmt.find_graph`):

| File | Bytes before the graph | Bytes after |
| --- | --- | --- |
| our `navgraph.bin` (compiler input) | 48 (24-byte resource header with a u32 sum at 12, `0x1000001, 0x10000, size, 1`, then `2B, 1`) | 0 |
| ZoneTool dump `*.d3dbsp.navmesh` | 340 (asset header: counts 0x0F, 1, 0x26, 0x12, 0x6E, the name `maps/cp/cp_zmb.d3dbsp`) | 23,090 on cp_zmb (tables the zone loader builds, not ours) |

`navfmt.write_file` keeps both byte for byte; `navfmt.wrap_resource` builds the first form.

## Graph (little endian)

| Offset | Size | Field |
| --- | --- | --- |
| 0 | u32 | version `0x2B` |
| 8 | u32 | `area_bytes` |
| 12 | u32 | `kd_bytes` |
| 24 | u32 | `0x38` (offset of the bounds) |
| 32 | u32 | total graph bytes = 336 + area_bytes + kd_bytes |
| 36 | 5 x f32 | params `72, 5, 15, 10, 72` (agent height, ?, radius, ?, height) |
| 56 | 6 x f32 | bounds min xyz, max xyz |
| 80 | u32 | `2` |
| 208 | 128 bytes | stock only: 32 non-zero words (looks like a hash); zero in every graph we emitted, which the engine accepts |
| 336 | | areas, then the kd tree |

### Area: 72 bytes + 32 bytes per edge (N-gons exist)

| Offset | Field |
| --- | --- |
| 0..31 | zero in all 2,865 stock areas |
| 32 | centre x, y, z (f32); not the average of the corners |
| 44 | radius = longest 3D distance from the centre to a corner (400 of 400 sampled) |
| 48 | `0xFFFFFFFF` (all areas) |
| 52 | 0 |
| 56 | u32 flags: `0x3FFFF << 7 \| edge_count`; the low 7 bits are the edge count |
| 60 | u32 `n << 24 \| 0x110000`; n = 2 on 1,603 stock areas, up to 7. Not the edge count and not the link count. Meaning unknown: we write 2 as mapgen does (proven in game) |
| 64, 68 | 0 |
| 72 + 32 e | edge e |

Edge (32 bytes): `u64 neighbour offset` (offset of the neighbour area in the graph; 0 with cost 0 = no link), `3 x f32`
corner e (the polygon is the list of edge corners; edge e runs from corner e to corner e+1), `u32 flags`, `u32 cost`,
`u32 0`. Cost is `ceil(distance between centres * 1000 / 72)`. Flags are `0xFFFF0000` (11,581 edges) or `0xFFFF8000`
(214 edges, all linked, z continuous; meaning unknown, we never write it).

Measured on cp_zmb: edge counts 3: 919, 4: 1,129, 5: 514, 6: 213, 7: 57, 8: 27, 9: 5, 14: 1. 5,804 of 11,795 edges are
links, all symmetric, and every link lies on one exactly shared edge: the neighbour holds the same two corners reversed,
with the same heights (z difference at most 0.1 on 5,804 of 5,804). The engine therefore climbs only along shared edges
of equal height; a stair is a run of sloped areas, not steps.

### Stacked floors

Areas may lie over each other: 587 stock areas (425 pairs) have an overlapping footprint with another area at least 72
units apart in z (for example x -1770, y -3086: z 364.5 and 1588.9). Nothing in the format forbids it: each area has its
own corners and its own links.

### kd tree (after the areas)

28-byte header: the bounds again (6 x f32) and the payload size (u32 at 24). Nodes in depth-first order: internal node 12
bytes `u32 axis << 28 | byte offset to the right child (from this node)`, `f32 left_max`, `f32 right_min`; leaf 4 bytes
`0x80000000 | area offset`; one leaf per area (2,865 leaves, 2,864 internal nodes, depth 12). The tree splits on all three
axes (x 1,318, y 1,347, z 199 nodes). Rule measured on the stock tree and used by `navfmt.build_kd`: axis = longest
extent of the polygon corners over x, y, z; items sorted by the middle of their extent on that axis; left = first n // 2;
`left_max` / `right_min` = extreme polygon corners on the axis, pushed outwards by 0.0072. 5,230 of 5,729 nodes are
reproduced exactly; the rest are ties in the sort or in the axis choice.

`mapgen.nav_graph` splits on x and y only, with centre bounds; it cannot separate two areas that share an xy position,
which is why it cannot write stacked floors. `navgen` uses the stock rule.

## Generator: `navgen.generate`

```
generate(tris, *, cell=32, agent_height=72, agent_radius=15, step=18, max_slope_deg=45, seeds=None,
         res=8, min_cover=0.2, detail=False) -> (navgraph.bin bytes, report dict)
```

`tris` is (N, 3, 3) in game units; floors face up, ceilings down. Steps: triangles are sampled on a lattice and binned
in columns of `res` (8) units on a grid aligned to `cell`; per column the points are merged into spans; a span is a floor
when its highest walkable point is within `step` of the span top, the slope is at most `max_slope_deg` and the next span
above is `agent_height` higher; neighbouring floors link when their heights differ by at most `step` and the headroom
stays; floors within `agent_radius` of a wall, a drop or a missing link are removed (distance counted on the links); the
rest becomes layers (connected components); each `cell` square gets one quad per layer when at least `min_cover` of its
columns are floor; quad corner heights come from a least squares plane, averaged with the corners of the same layer
within one `step` at the same point, so linked quads share edges exactly; links are the quads joined by linked columns;
quads not connected to any seed are dropped and counted (`dropped_unreachable`); a seed with no navigation within one
cell and 48 units goes in `seed_problems` (all seeds bad: `ValueError`). `report` has counts, `layers_z`,
`stacked_cells`, `components`, `links`.

CLI: `python navgen.py gen <colmap.hkx|emit folder|tris.npy> -o navgraph.bin --seed=x,y,z --json report.json`;
`python navgen.py compare a.bin b.bin --layout layout.json` (cell coverage by zone). Needs numpy; the test skips
without it (`python -I` does not see the user-site numpy, `python -B` does).

### What it does not do

- Areas are quads on the `cell` grid (as `mapgen.nav_graph`); no merging into N-gons (stock merges: 3 to 14 edges). The
  grid must fit the level: a stair or corridor edge that is not a multiple of `cell` gets a quad that sticks out over the
  drop (`NAV_FLOATING` in emitcheck on that quad; seen with a stair edge at x 592). Author on a 32-unit grid.
- Doors, jump links, flags `0xFFFF8000`, the `n << 24` field and the 128-byte stock block are not generated.
- Memory is about 24 bytes per sample point: a very large floor needs `res` raised.

## Measured (22 Nov 2026, offline, no game)

- Stock cp_zmb: round trip byte identical (653,342 bytes); our g27r `navgraph.bin`: byte identical (2,216,992 bytes).
- g27r collision (34,036 triangles) regenerated in about 5 s with seeds at the three player starts: 10,832 areas against
  10,262 shipped; 44 shipped cells missing, 614 generated cells not shipped (wall margins, tunnel and platform edges);
  `iwz_emitcheck check`: 1 error (`NAV_FLOATING`, one cell, 12 units, ticket hall); the shipped graph has 0.
- Two-storey fixture (`fixtures/twostorey`, floors at z 0 and 256, 32-step stair): 925 lower, 866 upper areas,
  861 squares with two areas, one component, `route` from the bottom start to the top floor 1,403 units;
  `iwz_emitcheck check`: 0 errors, 1 warning (open stair sides, by design).
