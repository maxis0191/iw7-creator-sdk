# World kit: a studio-made map as data

`tools-source/worldkit/` reads the dump of one of the game's own maps (made by the project's asset tool, a
ZoneTool fork, from the owner's own game files) into a queryable scene: every placed prop with its position and
orientation, every piece of world geometry with its material, every light, every entity. An agent can find a
room in that data, and lift its contents out as a reusable piece, a **prefab**.

What it is for:

* seeing a studio-made map as data, without launching the game or looking at screenshots;
* lifting rooms out as prefabs (props, lights, entities, surface meshes), placed anywhere with a turn about the
  vertical axis;
* the base for editing stock maps and for dressing new maps with studio-quality detail.

It reads dumps; it never runs the asset tool or the game. Python standard library only (`numpy` is used when
importable, `IW7_WORLD_NO_NUMPY=1` turns it off; both paths give identical databases).

Files: `iw7_dump.py` (the byte-level reader: format, layouts, loud failures), `iw7_world.py` (database, queries,
prefabs, command line), `tests/` (synthetic world and tests).

## Commands

```
python -B tools-source/worldkit/iw7_world.py build --dump <map dump folder> --db <out.sqlite> [--catalog <models catalog json>]
python -B tools-source/worldkit/iw7_world.py <command> --db <out.sqlite> ... [--json] [--limit N]
```

Text output is compact; `--json` prints the same data for machines; `--limit` (default 10, 0 = all) caps the rows
listed per section. Totals are always complete. Every command fails with exit code 2 and a message on stderr.
Examples below are from the Spaceland dump (counts only).

| Command | What it does | Example result (Spaceland) |
| --- | --- | --- |
| `build` | reads `maps/**/*.gfxmap`, `*.commap.json` (or binary `.commap`), `*.ents`, and `transient_zones/*.gfxmap_tr` into the database; the vertex and index buffers go to the side file `<db>.mesh` | `surfaces 10760, smodels 17010, primaryLights 1039, probes 160`, 3 to 5 s |
| `stats` | counts next to the numbers the file header declares and the independent ground truth, bounding boxes, the 20 most placed models, the 20 materials with most triangles | all three columns agree on every count |
| `box X1 Y1 Z1 X2 Y2 Z2` | props, lights, entities inside an axis-aligned box; surfaces touching it and the triangles whose centroid is inside | box over the player start: 483 props, 36 lights, 69 entities, 11460 triangles |
| `near X Y Z --radius R [--kind props\|lights\|ents\|surfaces]` | the same around a point, nearest first | radius 600 around the player start: 407 props, 30 lights, 64 entities |
| `find-model TEXT` | models whose name contains TEXT: instance count and centroid | `arcade`: 36 models |
| `where-model NAME` | every placement of a model | `zmb_arcade_toy_astronaut_white`: 104 |
| `rooms --cell 512` | a grid over x, y: props, lights, entities, triangles per non-empty cell, most props first | 1861 non-empty cells |
| `check [--dump DIR]` | sanity checks against the dump folder: model files, material files, outliers, orientation | see the measured table |
| `compare-smodels --csv FILE` | compares the static models with a table the map compiler's own reader wrote | 17010 of 17010 rows equal |
| `extract --box X1 Y1 Z1 X2 Y2 Z2 --name N --out DIR` | writes a prefab folder | `spawn_plaza`: 483 props, 36 lights, 69 entities, 437 surfaces, 11460 triangles |
| `place --prefab DIR --at X Y Z [--yaw DEG] --out DIR2` | the prefab moved to a point and turned about the vertical axis | yaw 90 is exact; pairwise prop distances unchanged |

Python use: `iw7_world.World(db)` gives `q(sql)`, `surface_mesh(i)`, `box`, `near`, `rooms`, `stats`, `check`;
`iw7_world.extract(world, box, name, out)` and `iw7_world.place(prefab, at, yaw, out)`.

### Database

`smodels` (one row per placed static model; field names from the asset tool's `structs.hpp`, raw values kept:
`cullDist`, `flags`, `lightingHandle`, `unk0`..`unk21`, `primaryLightEnvIndex`, `reflectionProbeIndex`,
`firstMtlSkinIndex`, `sunShadowFlags`, `transientZone`, lightmap offset/scale/index, vertex-lighting count; plus
the stored bounds and lighting origin, the draw order slots `lod_slot` and `sorted_pos`), `surfaces`,
`tris` (one centroid per triangle), `lights`, `probes`, `probe_instances`, `assets` (names of lightmaps,
probe images, sky image, transient zones and the like), `brush_models`, `ents` and `ent_kv`, `models` (instance
count; with `--catalog`: lod 0 triangles, bounds, category), `mesh_zones`, `meta` (dump path, file names, sizes,
SHA-256, whether each file parsed to its exact end, counts, reader version).

`surface_mesh(i)` returns positions, normals, texture coordinates, lightmap coordinates and triangle indices of
one surface, read from the side file. Only the vertices the triangles use are returned, indices remapped.
Normals are 10:10:10:2 packed unit vectors, decoded as `bits / 511.5 - 1` per axis (the project's generator packs
them the same way; decoded lengths measured 0.9986 to 1.0014).

Entity keys in `.ents` are numeric field ids. The ones the project's generator already uses are named in
`ent_kv.key_name` (157 classname, 822 targetname, 543 origin, 65 angles, 638 script_noteworthy, 820 target,
497 model, ...); the others stay numeric. `classname`, `targetname`, `origin` in `ents` come from those ids.

### Orientation

A static model's 3x3 axis is stored as rows: forward, left, up (world vectors of the model's x, y, z axes), scale
separate. `pitch yaw roll` in degrees are derived with the Quake style angle vectors (forward =
(cos p cos y, cos p sin y, -sin p), left = -right), the same routine the map compiler uses to turn `smodels.txt`
angles into an axis. The derived angles rebuild the stored matrix to within 2e-5 for all 17010 models (checked
at build time and recorded in `meta`). At pitch +-90 roll is set to 0.

### Prefab format (`iw7.prefab/1`)

A folder with:

* `prefab.json`: `schema`, `name`, `source` (map, reader version), `box`, `origin` (the centre of the box floor),
  `space` (`relative`: positions are relative to `origin`; `world`: written by `place`, absolute), `yaw`, `counts`,
  `props` (`model`, `pos`, `pitch`, `yaw`, `roll`, `scale`, `flags`, `cullDist`), `lights` (`pos`, direction, up,
  colour, radius, cone cosines, intensities, shadow flags, `defName`, `entityId`, all light fields), `ents`
  (`origin`, `kv` as key/value pairs; origin and angles keys are rewritten by `place`), `surfaces` (`material`,
  source surface, vertex and triangle counts, offset into the mesh file).
* `surfaces.bin`: per surface, little endian, origin-relative: positions `f32x3`, normals `f32x3`, texture
  coordinates `f32x2`, lightmap coordinates `f32x2` for each vertex (in that order), then triangles `u32x3`. Only
  triangles whose centroid is inside the box are kept. `read_prefab_surface(dir, prefab, k)` reads one.
* `smodels.txt`: one line per prop, `<xmodel> x y z pitch yaw roll scale`, the format the map compiler's
  `smodels.txt` reader takes (`#` comments allowed). The angles use the compiler's own convention (see above),
  so no conversion is needed. After `extract` the positions are prefab-relative; after `place` they are world
  positions, ready to be used as the compiler's input. The compiler's optional `noshadow` / `cull=` flags are not
  written; `flags` and `cullDist` are in `prefab.json`.

`place` rotates positions, orientations, light directions, entity origins and angles, and mesh positions and normals
about the vertical axis through the prefab origin, then moves the origin to `--at`. Multiples of 90 degrees use
exact cosine and sine, so they are exact. A world-space prefab can be placed again.

## Measured on Spaceland

Dump read: `cp_zmb` (the game's own map; 100,110,337 byte `.gfxmap`, 24,906,133 byte transient zone, 1.8 MB light
JSON, 450 KB entity text). Both binary files parse to their exact last byte. Counts agree with the header and with
the map compiler's printout (surfaces 10760, static models 17010, primary lights 1039, reflection probes 160, brush
models 94). The static model table agrees with the compiler's own table on all 17010 rows (model, position, scale,
flags, cull distance, lod slot, sort position, lighting handle, transient zone, lightmap index). Total 403,042
triangles, 514,927 vertices, 1,209,126 indices, 3695 entities, 916 distinct models. Database 37 MB plus a 25 MB
mesh side file; about 3 s to build with numpy, 7 s without. Every model name has a model file in the dump
folders, every surface material has a material file; the 17 props and 13 surfaces outside +-20000 are the
distant vista (trees, terrain). The test suite uses a synthetic world only and runs in seconds.

## What it does not do yet

* Collision and navigation of a prefab are not extracted (no Havok mesh, no nav mesh, no path nodes).
* Lightmap texels are referenced, not copied: a prefab carries lightmap coordinates and the lightmap index, not
  the lighting. Light grid, reflection probe contents and umbra visibility data are not read (their sections are
  walked over and counted, not decoded).
* Nothing here builds a map. A prefab's `smodels.txt` and surface meshes are inputs for the map generator, which
  must still learn to take them (the compiler already takes `smodels.txt`; surface meshes have no consumer yet).
* Surface fields without a known meaning (`unk1`..`unk4`, `sortKey`, vertex layer data) are kept raw; this dump
  version has no per-surface reflection probe or primary light index, so none is reported.
* The binary `.ents.data` (triggers, splines, dynamic entities, clip data) is listed in `meta`, not read; the
  plain `.ents` text is the entity source. The binary `.commap` reader exists and is tested on a synthetic file,
  but the real dump holds the JSON form.
* The dump holds a single world per folder; several transient zones are supported but only one was seen.
* Other maps: only Spaceland has world files on this machine (the Rave dump holds none), so the reader is proven
  on one real file plus the synthetic world.

## Failing loudly

A file must parse to its exact end: every array count must equal what the owning structure declares, every
offset is bounds checked, a repeat record must point at an earlier entry, the light count of the light file must
equal the gfx world's, an unbalanced entity block is an error. The messages name the file and the byte offset.
A database built by another major reader version is refused.
