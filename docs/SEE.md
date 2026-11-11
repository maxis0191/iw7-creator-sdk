# Frame facts: what a captured frame shows, as data

Status: built and measured live on 10 and 11 Nov 2026 on Spaceland (`cp_zmb`), lab client, private sessions. Nothing here is
deployed. The tool is `tools-source/worldkit/iw7_see.py`; the camera and the depth come from the lab client
(iw7-mod-components `src/native/paris_see.cpp`, and its page `docs/SEE.md` there).

## What it is for

An agent judges a picture badly and a number well. For any frame taken in a test session, this answers from data:

| Question | Command |
|---|---|
| What object is at pixel (x, y)? Where is it in the world, how far? | `at <frame> <x> <y>` |
| Where does a world point fall in the frame, and is it hidden? | `project <frame> <x,y,z>` |
| Is prop X (or every prop of a model) visible, on how many pixels, how much is hidden? | `visible <frame> --prop <index>` / `--model <text>` / `--point <x,y,z>` |
| What does the frame show? What is in it that is not part of the map? What should be there and is not? | `objects <frame>` |
| Is a thing floating above the floor or sunk into it? | `floor <frame> --point <x,y,z>` / `--pixel <x,y>` |
| What appeared or disappeared between two frames? | `compare <frame a> <frame b>` |

Every command takes `--db <world database>` (built by `iw7_world.py build`, docs/WORLDKIT.md) and `--json`.
`<frame>` is the frame file (`iwz_<name>.bmp` in a gamelab run folder) or its camera file (`perf/see-iwz_<name>.json`).

```
python -B tools-source/worldkit/iw7_see.py index --db <db> --dump <map dump folder>      # once per database
python -B tools-source/worldkit/iw7_see.py objects <run>/iwz_view.bmp --db <db>
python -B tools-source/worldkit/iw7_see.py at <run>/iwz_view.bmp 640 360 --db <db>
python -B tools-source/worldkit/iw7_see.py visible <run>/iwz_view.bmp --model trash_can --db <db>
python -B tools-source/worldkit/iw7_see.py floor <run>/iwz_view.bmp --point 467,3477,40 --db <db>
python -B tools-source/worldkit/iw7_see.py compare <run>/iwz_before.bmp <run>/iwz_hidden.bmp --db <db>
python -B tools-source/worldkit/iw7_see.py camera <run>/iwz_view.bmp
```

Needs `numpy`. Exit code 2 with one sentence on stderr for every refusal (no camera file, no depth when a command
needs it, a pixel outside the frame, a file that is not a camera).

## Getting a frame with its camera and depth

In a gamelab plan (server repository, docs/GAMELAB.md), with a lab client built from current components:

```json
{"do":"capture","name":"view","depth":true,"pause":0.5}
```

The run folder then holds `iwz_view.bmp` (the picture), `perf/see-iwz_view.json` (the camera, always written) and
`iwz_view__z.bmp` (the depth, only with `"depth": true`). The step returns when the frame has really been taken.
From the console: `paris_see_depth`, then `capture_frame <name>`.

Hide the weapon and the HUD before a frame that is to be measured (`{"do":"dvar","name":"cg_drawGun","value":"0"}`,
the same for `cg_draw2D`): the weapon is drawn into the depth buffer, right in front of the camera.

## The three sources and how they are used

1. **The exact camera of the frame.** The client records the engine's own projection of a few hundred world points
   when the capture is asked and again right after the frame was taken; the tool solves the camera from them
   (position, the three axes, focal lengths, centre). With it, the world database is drawn offline from the frame's
   own point of view: every world surface triangle and every prop's triangles (the highest-detail mesh of its model,
   read from the dump by `index`). That gives, for each pixel, the static thing that should be there and its distance.
   It costs no graphics work and is blind to everything that is not the static map.
2. **The engine's own depth buffer** of the same present. It is the truth of what was drawn, dynamic things included,
   and the only proof of visibility. It gives a distance, not a name.
3. **The game's own ray casts** (gamelab `trace` steps: fraction, position, and the entity that was hit). Used here to
   check the tool; not needed to use it.

The answers come from the agreement of 1 and 2. At a pixel, the depth gives the world point that was drawn. If a
database triangle lies on the pixel's ray at that distance, the pixel is that prop or surface. If the depth is nearer
than every database triangle, something that is not in the static map was drawn there: "dynamic or unknown", with its
position, its distance and the nearest map entity. If a database triangle is in front of what was drawn, that thing
was not drawn: it is reported (hidden by the live editor, not drawn at that distance, transparent, or absent).

## Conventions

- World units. The camera axes are forward, left, up.
- A pixel `(x, y)`: x to the right, y down, the centre of the pixel at `(x + 0.5, y + 0.5)`. Pixels given to the
  commands are pixels of the picture. Pixel counts in the answers are depth-buffer pixels (the answer says the size).
- `z` is the distance along the camera's forward axis; `distance` is the straight line from the camera.
- Projection: `x = cx - fx * left / z`, `y = cy - fy * up / z`, with `fx = width / (2 * tan_half_fov_x)` and the centre
  `(cx, cy)` solved with the camera (it is the middle of the frame to within 0.0001 pixel).
- Depth file: a 32-bit BMP, top row first, whose 4 bytes per pixel are one little-endian float: the raw device depth.
  Measured: device depth = 3.9375 / z; 0 where nothing was drawn; larger is nearer.
- Two distances agree when they differ by at most 2 units, or 1.5 % of the distance when that is more. A pixel also
  agrees when the depth lies between the static distances of its 3 by 3 neighbours (edges fall one pixel either way).
- The sky is a surface of the map that writes no depth; it is left out, and a pixel of sky answers `nothing drawn`.

## What the commands print

`at`: the object (`prop <index> <model>` or `surface <index> <material>`), the world position, `z` and `distance`,
and where the answer comes from. `dynamic or unknown` adds the static thing behind it and the nearest map entity
within 96 units. `not_drawn_in_front` lists database things on the ray that were not drawn. A surface of one of the
map's brush models (a door or another part a script can move) carries `movable_brush_model`. Without a depth file the
answer is the database's first hit and says so.

`project`: the pixel, `z`, and one of `visible, a surface is drawn there`, `visible, nothing drawn there` (the depth
is farther: free space, or the thing is missing), `occluded` (with what hides it), `outside the frame`,
`behind the camera`.

`visible`: per prop, `projected` (pixels its triangles cover, alone), `visible` (the depth is that prop), `occluded`
(something nearer was drawn, the floor included when the prop is sunk into it) and `absent` (the depth is farther: the
prop was not drawn there). Totals, the hidden fraction, the fraction of the frame, a pixel box.

`objects`: the summary (pixels that are the static world, nearer, farther, nothing drawn), the objects by pixels seen
(with the pixels expected and the nearest `z`), the things that are not in the map (connected groups of nearer
pixels: size, box, centre, distance, how far in front of the static world, height of the lowest seen point above the
floor, seen height), and the missing objects (expected on 40 pixels or more, seen on less than 30 % of them, the depth
farther on more than 60 %).

`floor`: the nearest level surface on the vertical line through the point (within 400 units above or below) and the
height of the point above it: positive = floating, negative = sunk. With `--pixel` the point is what the depth shows
at that pixel, so the reading comes from the frame alone.

`compare`: objects seen in A and no longer in B (less than 30 % of their pixels left), the reverse, the things that are
not in the map and came or went (groups of pixels whose depth moved, with the height of their lowest seen point above
the floor), the count of pixels whose depth changed, and whether the two cameras are the same.

`camera`: position, axes, yaw, pitch, fields of view, sizes, how well the solved camera reproduces the engine's
projection, how much the camera moved between the request and just after the frame, and the capture times.
`fit`: the depth convention measured on a frame.

## Measured on Spaceland (10 and 11 Nov 2026)

One private session (lab client built from the components change, loopback, 136 plan steps, 21 captures, PASS in
92.5 s), player frozen at the spawn (467, 3677, 0), weapon and HUD hidden, three views: A yaw 0, B yaw 270, C yaw 300
pitch 5. Frames 1280 by 720; depth 1280 by 720. A second session measured the cost.

**Models.** `index` reads 916 of the 916 models the map places (1,595,875 vertices, 1,715,622 triangles) in 2 s; the
largest difference between a mesh's box and the box the model catalogue stores is 0.00 units.

**Camera.** The camera solved from the client's record reproduces the engine's own projection of 320 points to a
median of 0.00005 pixel (worst 0.013 over the three views); the centre of projection is the middle of the frame to
0.0001 pixel; the camera did not move between the request and the frame (0.0). For the player's origin
(467, 3677.05, 0.10) at yaw 0 it gives the eye at (466.894, 3677.050, 60.102), tangents 0.849427 and 0.477803.

**Depth.** `fit` on the three views: device depth = 3.9375 / z (3.937495, 3.937499, 3.937493; offset below 5e-8).
That is the tool's default; `--depth-model a,b` overrides it.

**The whole frame against the database.** Pixels where the engine's depth is the static thing the database predicts,
plus sky pixels where it predicts nothing: view A 916,490 of 921,600 (99.4 %), B 861,672 (93.5 %), C 859,818
(93.3 %). The rest is nearer than the static world (A 0.2 %, B 6.4 %, C 6.4 %: things that are not in the map, such
as a bunch of balloons, turning planets, signs) or farther (0.31 %, 0.13 %, 0.26 %).

**P1, camera truth, 20 props over the three views.** A prop's position in the picture is the pixel of its own drawn
shape nearest to the centre of that shape. For 11 props the depth there unprojects to a point inside the prop's
stored bounds; depth minus database is 0.000 to 0.16 units for solid props (at distances of 113 to 1,304 units) and
up to 2.6 units for bushes (leaf cards). For 8 props the pixel is hidden, and the tool names what hides it (a wall,
a bush, another prop). 1 prop is not drawn there (`brokenglass_window01`: glass writes no depth). Shifting a solid
prop's shape by one or two pixels in any direction never improved the agreement (5 solid props tested): the pixel
error is below one pixel. (A bush gained 96 of 2,920 pixels at a shift of two.)

**P2, naming, 30 pixels.** Ten random pixels in each view (one in each cell of a 5 by 2 grid, not chosen by what is
there). `at` named 10 props, 16 surfaces, 2 sky pixels and 2 things that are not in the map.

| Named as | Check | Result |
|---|---|---|
| prop (10) | hide exactly that prop with the live editor (`paris_world_hide_model <model> <origin> 0.5`, `matched=1` every time), capture again, compare the depth at the pixel; the 8 or 9 other pixels of the view must not move | 10 of 10: the depth changed at the pixel every time, and 0 other pixels moved (9 in the proof session; the tenth, a gate 3,355 units away, in a later session: its depth went to 3,421.8, the gate behind it, and the tool lists the hidden gate as not drawn in front) |
| surface (16) | the game's own collision trace from the camera through the pixel | 15 hit within 0.1 unit of the tool's point. 1 differs: the collision trace stops 25.7 units short on a collision shape (`plastic`) that is not drawn at that pixel; the depth and the database agree on the floor |
| nothing drawn (2) | the depth is 0 and the database has the sky there | 2 of 2 |
| not in the map (2) | the game's trace | 1 confirmed: the trace hits a `scriptable` entity 0.8 units from the tool's point (the balloons). 1 not confirmed: the trace passes through it and hits the wall the tool reports 32.8 units behind it |

So 28 of 30 are confirmed by an independent check (10 props, 15 surfaces, 2 sky pixels, 1 thing that is not in the map), none is shown wrong, and 2 are not confirmed: the surface where collision and picture differ, and one thing that is not in the map.

**P3, dynamic things.** A script model placed by the plan (`zmb_target_01` at (467, 3477, 40)): `at` on its pixel
says `dynamic or unknown`, distance 199.22; the game's trace through the same pixel hits
`script_model zmb_target_01` at 199.16. `compare` of the view before and after lists it as "appeared, not in the map"
(8,204 pixels, centre (466.9, 3477.9, 64.7)). A spawned zombie whose script origin was (511.9, 3391.1, 0.1): listed
as appeared, not in the map, 5,011 pixels, distance 291.6 (script: 290.3 to its chest), lowest point 1.7 above the
floor, seen height 68.9. Its drawn centre is 9 units from the script origin of the same moment (it was walking; the
script reads the server's position).

**P4, a defect found by numbers.** Three copies of the same model: one on the floor, one placed 40 units above it,
one sunk 20 units into it.

| Thing | `floor --point <script origin>` | From the frame alone |
|---|---|---|
| on the floor | on the surface (0.0) | lowest seen point 1.2 above the floor, seen height 35.6 |
| 40 above | above the surface by 40.0 | lowest seen point 40.04 above the floor (`compare`); `floor --pixel` just above its base reads 41.37 (the point is at 41.5) |
| sunk 20 | below the surface by 20.0 | seen height 17.3 instead of 35.6; `floor --pixel` near its top reads 16.87 (the point is at 16.8); at its base the frame shows the floor |

The hidden plaza (the live editor hid the 792 props of a box around the view): `compare` lists 28 props as
disappeared. They are exactly the 28 props of the box that were seen on 40 pixels or more before; none of the 20 seen
props outside the box is listed. After the restore: 0 disappeared (one surface listed as appeared, 8 to 80 pixels, next to a moving thing). Two frames of the unchanged view: 0 disappeared,
0 appeared, 159 pixels of 921,600 with another depth.

**P5, cost.** In the game: a capture without depth is the picture copy the game's own capture already cost (median 14.4 ms in the renderer); the depth adds a median of 9.6 ms, so a capture with depth is one long frame of about 25 ms (the first one of a session 0.2 to 0.6 s: the depth target is looked up once). With no capture pending the frame time is unchanged within the noise (listener on, off, on, off: medians 7.41, 7.88, 7.80, 7.26 ms in one session and 6.35, 6.53, 5.51, 6.12 ms in another). Files per frame: picture 3.7 MB, depth 3.7 MB, camera 33 KB. Details: components `docs/SEE.md`. The tool: `objects` 7.9 s the first time for a view (the database is drawn once and kept in
the cache folder), 2.3 s after; `at` 0.7 s; `visible --model` 1.5 s for 99 props; `floor` 0.8 s.

## What is not covered

- **Transparent things, effects, decals.** They write no depth, so a frame's depth shows what is behind them: glass
  (`brokenglass_window01` above), smoke, fire and most effects are invisible to this tool. A decal surface of the map
  (`..._dec`) counts as seen where the thing under it is within the tolerance. To see them the colour frame is needed,
  or a second capture of the engine's own masks; neither is done.
- **The sky and far vista.** The sky is "nothing drawn". The distant mountains are props of the database and are named.
- **The HUD, the weapon, text drawn over the frame.** The weapon is in the depth with values that are not its distance
  (hide it). The HUD and the build text are in the picture and not in the depth: the tool never sees them.
- **What a dynamic thing is.** A thing that is not in the map is reported with its pixels, position, distance and
  height above the floor, and the nearest map entity as a hint. Its name (which script model, which zombie) is not in
  the frame; a gamelab `trace` step through the pixel gives it when the thing has collision. The exact shape of a
  skinned character is the depth's; nothing here compares it with the character's model.
- **Thin things flush on a surface.** A prop less than the tolerance in front of what is behind it (a door frame on a
  wall: 2 units, or 1.5 % of the distance) cannot be told from that wall in one frame. `compare` with one camera does
  see it go (the depth repeats bit for bit, so 0.25 units are enough).
- **Leaves.** A bush or a tree is drawn as cards with holes; its triangles cover more pixels than its leaves (a bush
  in the proof: the depth agrees on 63 to 84 % of its triangles' pixels, up to 2.6 units off).
- **Lower detail far away.** The tool draws the highest-detail mesh of every model and honours the stored cull
  distance; the engine's switch to simpler meshes with distance is not modelled (no error above the tolerance was seen
  up to 6,200 units).
- **Collision.** The tool reads what is drawn. Collision can differ (one of 15 surface checks above).
- **Moving camera.** Exact only when the camera is the same at the request and after the frame; the tool prints the
  difference and does not correct for it.
- **Other maps, other sizes.** Only Spaceland has a world database on this machine. One window size (1280 by 720),
  scene scale 1. A map without a database has no `objects`, `at` by name or `compare`; the camera and the depth (world
  position and distance of any pixel) still work with any database of the right map.
- **Brush models a script moved.** The database holds them where the map file puts them; a door that a script opened
  is reported as missing there and as "not in the map" where it now stands (`movable_brush_model` marks such surfaces).

## Files

| File | Role |
|---|---|
| `tools-source/worldkit/iw7_see.py` | the tool |
| `tools-source/worldkit/tests/test_see.py` | 22 tests on the synthetic world: a made-up camera, a depth image drawn by the tool and then changed |
| `<db>.models.npz` | written by `index` beside the database: the props' triangles (machine-local, never committed) |
