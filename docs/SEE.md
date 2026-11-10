# Frame facts: what a captured frame shows, as data

Status: built and measured live on 10 Nov 2026 on Spaceland (`cp_zmb`), lab client, private sessions. Nothing here is
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
  `(cx, cy)` solved with the camera (it is the middle of the frame to within @@CENTRE@@ pixel).
- Depth file: a 32-bit BMP, top row first, whose 4 bytes per pixel are one little-endian float: the raw device depth.
  @@DEPTH-CONVENTION@@
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

@@MEASURED@@

## Files

| File | Role |
|---|---|
| `tools-source/worldkit/iw7_see.py` | the tool |
| `tools-source/worldkit/tests/test_see.py` | 22 tests on the synthetic world: a made-up camera, a depth image drawn by the tool and then changed |
| `<db>.models.npz` | written by `index` beside the database: the props' triangles (machine-local, never committed) |
