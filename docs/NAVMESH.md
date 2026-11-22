# NavGraph format and the navmesh generator

The navigation of an IW7 zombies map is one bfx NavGraph (graph version 0x2B, the zone's `navmesh` asset). This page is
the format as measured on the stock `cp_zmb` navmesh (ZoneTool dump, 2,865 areas) and the generator that writes it from
collision triangles. Code: `tools-source/iwzmap/navfmt.py` (reader, writer, kd builder), `navgen.py` (generator),
`test_navgen.py`, fixtures `fixtures/twostorey/` and `fixtures/freeform/`.

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

## Generator: `navgen.generate` (round 2, 22 Nov 2026)

```
generate(tris, *, cell=16, agent_height=72, agent_radius=15, step=18, max_slope_deg=45, seeds=None,
         max_edges=14, plane_tol=1.5, edge_margin=8.0, solid_check=True) -> (navgraph.bin bytes, report dict)
```

`tris` is (N, 3, 3) in game units; floors face up, ceilings down, solids closed. No grid is assumed: walls and stairs at
any angle, edges anywhere. Steps:

1. Every triangle is sampled on a lattice (5.6 units on floors, which are pulled 0.6 inside their triangle so that the
   row of points on a border does not put a floor column on the far side of the edge; 4 on walls) and binned in columns
   of `cell / 2` (8) units.
2. Per column the points are merged into spans. A span is a floor when its highest walkable point is within `step` of the
   span top, the slope is at most `max_slope_deg`, the next span above is `agent_height` higher, and (`solid_check`) the
   next surface above is not an up-facing face: a floor inside a closed solid (under a pillar, inside a crate) is not
   walkable (`report['inside_solid']`).
3. Floors of neighbouring columns link when their heights differ by at most `step` and the headroom stays. Every floor
   span gets its distance to the edge of its surface: a floor with a missing neighbour is a border span, its distance is
   measured to the real wall points of the neighbouring columns (the wall is somewhere inside its column), or half a column
   at a drop; the distance is carried inward along the links (chamfer metric 1, 1.41, in 8-unit steps).
4. Lattice vertices every `cell` (16) units. A vertex collects the floor spans of the four columns around it and has
   one node per floor level (spans within `step` of each other), with the mean height and the mean distance to the edge
   (a missing column counts -4). Per lattice cell and floor level, marching squares at the level `edge_margin` (8)
   cuts the cell: corners over the level are kept, and the crossing on a cell edge is placed by linear interpolation of
   the two vertex distances. The result is a convex polygon of 3 to 6 corners that does not overhang the real edge
   (the crossing depends only on the two vertex nodes of the shared lattice edge, so both cells compute the same point).
5. Convex merge: neighbouring polygons are joined along their shared edges while the result stays one simple convex
   polygon, planar within `plane_tol` units, with at most `max_edges` (14, stock range 3 to 14) corners; a vertex in the
   middle of an edge with the same neighbour on both sides is not a corner.
6. Slope rule (round 3): a link between two areas whose slopes differ by more than 10 degrees (a ramp or stair next to a
   flat floor) is kept only across the sloped area's foot or top edge, within 30 degrees of perpendicular to its gradient;
   a side edge gets no link, because the body cannot step onto a ramp from the side (found in game on the Blender test
   map). `report['slope_side_links_cut']` counts them.
7. Links: the neighbour of an edge is the polygon that owns the same two vertices reversed. Every link therefore is one
   exactly shared edge with equal corner heights (the rule measured on stock). Areas not connected to any seed are dropped
   and counted (`dropped_unreachable`); a seed with no navigation at it within 48 units goes in `seed_problems` (all seeds
   bad: `ValueError`). The kd tree is the stock rule (`navfmt.build_kd`).

`report` has counts (`polygons_before_merge`, `areas`, `links`, `edge_count_hist`, `inside_solid`, `eroded`, `layers_z`).
`navgen.boundary_gap(tris, data)` measures how far the nav edge stays from the collision wall (outward ray from every
unlinked edge, first wall point within 3 units of the ray): mean, 95th percentile, max, the samples that face a drop.

CLI: `python navgen.py gen <colmap.hkx|emit folder|tris.npy> -o navgraph.bin --seed=x,y,z --json report.json`;
`python navgen.py compare a.bin b.bin --layout layout.json` (floor area of one graph the other does not cover, by zone).
Needs numpy (no scipy); the test skips without it (`python -I` does not see the user-site numpy, `python -B` does).

`iwz_emitcheck` now reads N-gon graphs (through `navfmt`): `load_nav` takes any edge count, `z_at` and `columns` work on
polygons, and `check_links` judges a link between polygon areas centre to the middle of the shared edge to the centre
(heights on the shared edge) instead of centre to centre, which is meaningless for big ramp polygons. Axis-aligned flat
quads of at most 64 units are still judged as before.

### What it does not do

- The merge is greedy and local: 3,871 areas for g27r where stock cp_zmb has 2,865 for a bigger map; a flat 512 x 512
  floor gives 88 polygons.
- Doors, jump links, flags `0xFFFF8000`, the `n << 24` field and the 128-byte stock block are not generated.
- Closed solids are assumed: a single-sided floor over another floor turns the lower floor into "inside a solid"
  (`solid_check=False` switches that off).
- The edge sits `edge_margin` (8) units from the wall, not `agent_radius`: with 15 the stair feet next to a pit wall lose
  their last samples (`STAIR_NAV_GAP`), with 6 or less the quads reach over drops (`NAV_FLOATING`).
- Memory is about 24 bytes per sample point: a very large floor needs `cell` raised.

## Measured (22 Nov 2026, offline, no game)

Round 1 (quads on a 32-unit grid) against round 2 (polygons from the contour), same inputs:

| | round 1 | round 2 |
| --- | --- | --- |
| g27r areas (shipped 10,262; stock cp_zmb 2,865) | 10,832 | 3,871 (49,388 lattice polygons before the merge) |
| g27r `iwz_emitcheck check` errors (shipped: 0) | 1 | 3: 1 `NAV_FLOATING` (generator_room, 12 units), 2 `STAIR_NAV_GAP` (one sample each at the foot of well_e and well_w, 8 units from the pit wall) |
| g27r floor area the shipped graph has and ours misses | 44 cells of 32 x 32 (45,000) | 115,000 sq units (1.1% of 10.5 M) |
| g27r floor area ours has and the shipped graph misses | 614 cells (630,000) | 819,000 (walls, tunnel, platform margins) |
| g27r `reach --all-spawners` | not run | 51 sources, 0 without a route |
| g27r time | 5 s | 15 s |
| two-storey fixture areas | 1,882 | 610 |
| two-storey `check` | 0 errors, 1 warning | 0 errors, 1 warning (open stair sides, by design) |
| two-storey `route` start to top floor | 1,403 units | 1,328 units |

Edge distance to the wall (`boundary_gap`, outward ray): g27r mean 9.0, 95th percentile 12.6, max 44 (78 of 19,489 samples
beyond 20, at open stair sides and wells facing a far wall); free-form fixture mean 9.5, p95 11.2, max 47 (24 of 3,557
beyond 20, all at the open side of the stair top); two-storey mean 9.5, p95 9.7. `edge_margin` is 8, so the expected
distance is 8 plus the thickness of the sampling.

Free-form fixture (`fixtures/freeform`: the two-storey level rotated 30 degrees, plus a room with a 45-degree wall and a
16-sided pillar of radius 48 at x 1620, y 230): 1,100 areas, edge counts 3 to 14, every one of 5,052 links one exactly
shared edge, every area convex, `iwz_emitcheck check` 0 errors and 1 warning (the room is an island: it has its own seed),
the bottom seed reaches the whole top floor, no corner within 47 of the pillar axis or within 7 of the wall. Without `solid_check` the interior of the pillar was walkable.
Round-1 data (quads at 32 units) is kept in the git history of this page.

Round 3 (slope rule), offline: testmap1 collision (362 triangles): 28 of 44 slope-changing links were side links, all cut,
0 remain, the upper floor (z 136, 70 areas) is still reached from the ground start, `check` 0 errors; twostorey 28 cut, 0
side links, 0 errors, route 1,510 units; freeform 158 cut, 0 side links, 0 errors; g27r 236 cut (186 side links before
the rule, 0 after), 3,868 areas (round 2: 3,871), `check` the same 3 errors, `reach` 51 of 51 with a route.

## Round 4: stock rules measured against ours, and the `areas` modes (22 Nov 2026)

Trigger: on the Blender test map the engine paths on the round-3 polygon graph but zombies hover 70 to 160 units from
their goals inside one big area, while the 32-unit quad graph of the same map works. Measured on stock cp_zmb (2,865
areas) and on the testmap1 `emit_poly4` graph (211 areas); no cause of the hovering is proven by this table, these are
the differences:

| Property | stock cp_zmb | ours (polygons, testmap1 emit_poly4) | `areas='stock'` | `areas='quads'` |
| --- | --- | --- | --- | --- |
| corners on a straight line between neighbours (xy, 0.05) | 86 corners in 79 areas (2.8%) | 157 corners in 85 of 211 areas (40%) | 0 | 0 |
| centre x, y | area centroid, error 0.00 on 2,865 | centroid, same | same | same |
| centre z | plane through the corners at the centroid (0.00) | same (clamped to the corner range) | same | same |
| radius | longest 3D distance centre to corner, 2,865 of 2,865 | same | same, and the diameter of a merged area is capped at 230 | same |
| edge cost | `ceil(centre to centre distance * 1000 / 72)`, 5,804 of 5,804 (via the edge midpoint only 504) | same | same | same |
| radius p5 / p50 / p95 / max | 21.6 / 87.3 / 230 / 949 | 8.9 / 44 / 82 / 232 | 11 / 48 / 100 / 107 | 19 / 23 / 23 / 24 |
| longest edge of an area p50 / p95 | 140 / 366 | 86 / 160 | 86 / 157 | 32 / 35 |
| area size p5 / p50 / p95 (sq units) | 238 / 4,969 / 44,248 | 128 / 1,968 / 5,248 | 128 / 896 / 4,864 | 410 / 1,024 / 1,024 |
| first corner of an area | no rule (lowest y 27%, lowest x 27%) | lattice order | same | same |
| order of the areas in the file | not sorted by position | sorted by centre | same | same |
| `n << 24` word at +60, edge flag `0xFFFF8000` | 2 to 7, 214 edges | 2, never | same | same |

So the definitions of centre, radius and cost were already stock's; what differs is the share of areas with a corner on a
straight line (stock mostly has a full shared edge on every side), the size of the areas (stock median radius 87), and
the order of the corners and areas, which stock does not sort.

`generate(..., areas='polygons' | 'stock' | 'quads', max_radius=None)`:
- `polygons` (default): as round 3.
- `stock`: merge as in `polygons` with the diameter capped at 230 (stock p95 radius, so no radius above it), then every
  polygon whose side meets two different neighbours (a corner on a straight line, 0.1 xy) is cut by a diagonal from that
  corner, so each side has one neighbour; open-boundary corners within 0.3 of a line are removed. Result: no corner on a
  straight line, every link one exactly shared edge, the round-3 slope rule kept. More areas than `polygons`.
- `quads` (use `cell=32`): axis-aligned rectangles from the lattice, merged only when the result is still a rectangle of at
  most 64 x 64 with one neighbour per side, plus the clipped polygons where the walkable edge is not axis-aligned; no corner
  on a straight line; the slope rule kept. Closest to the graph shape proven in game.

testmap1 (`emit_poly4` collision, seeds from its layout), written into copies of the emit folder with only `navgraph.bin`
replaced: `IW7-Runtime\iwz-blend	estmap1\emit_nav_stock` (366 areas, 1,100 links, 0 straight-line corners, radius max
107) and `emit_nav_quads` (520 areas, 1,894 links, 493 rectangles). Both: every link one exactly shared edge, no sideways
ramp link, `iwz_emitcheck check` 0 errors, `reach --all-spawners` 6 sources, 0 without a route.

g27r (not the test target): `stock` 7,455 areas, 5 `check` errors (the 3 of round 3 plus a `LINK_STEEP` and a
`STAIR_NAV_OFF_SURFACE` on stair_a), `reach` 51 sources, 7 routes over 6,000 units (detours, no source without a route);
`quads` (cell 32) 11,676 areas, 10 `check` errors (floating cells where walls are off the 32 grid), `reach` 51 of 51.
`stock` mode costs time on a big map (16 s for g27r).
