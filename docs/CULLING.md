# Culling on a generated map: what decides which props are drawn

Status: built and measured 11 Nov 2026 on Station Zero's 19-zone blockout with ST1's stress props (2,000 and 6,000
stock static props), private loopback benches, lab client with the performance recorder. Package TF5 (= N5).
Nothing here judges looks.

## How the game decides (read from the shipped map's data and the game's own code, no build)

- The renderer draws the static models (props) that the visibility query returns. It has **no frustum or distance
  test of its own** for props: the live editor's earlier proof showed that changing a prop's `cullDist` or its
  `GfxStaticModelInst` bounds on Spaceland changes nothing on screen.
- The query reads the world's **tome** (format 20). Spaceland's (6.3 MB): 24,053 objects, 1,408 leaf tiles, 3,712 cells,
  27 gates. Per object it stores its **own bounds** (median largest extent 60 units; prop boxes equal
  `GfxStaticModelInst` bounds to 0.001 unit) and a **distance box**: the same bounds, 0, the same bounds, **cullDist
  squared** (8,205 exact, 7,486 within float rounding; objects never distance culled: about 1e12 or FLT_MAX). A prop's
  user id is class 1 (bits 28-31) with value v, and the prop is `lodData[v]` (16,693 of 16,693 matched by bounds).
- The query (results read in the game: 0 done, 2 out of memory, 5 camera outside the view volume, 7 failed) finds the
  camera's cell first. When it cannot (result 5, "camera outside umbra view volume") the renderer marks **every** prop
  visible (the fallback sets all visibility bits).
- The cell lookup reads the tile's cell count from the high half of tile `+0x34` and the camera cell's global index
  from the cell record `+0x10` (Spaceland: `0x00010001`, the cell's index).
- The game has a screen-size cull of its own: `r_umbraMinObjectContribution` (default 20 "pixels"). Setting it to 0
  changed nothing in the measured view. Models also have their own level-of-detail distances (for example
  `com_emergency_alarm_speaker` 200 / 500 / 4,500); far levels can be mostly transparent, which the frame check counts
  as drawn-but-different, not culled (see below).

## What the compiler wrote before, and now

| | before (x64-zt main 3e37290) | now (x64-zt `claude/iwzmap-tome-culling`) |
|---|---|---|
| Object bounds | the whole scene for every object | its own: props from `GfxStaticModelInst`, world surfaces from their triangles; lights and probe instances stay scene sized |
| Distance | +infinity for every object | prop `cullDist` squared (0 = never); world surfaces never |
| Camera cell | tile `+0x34` = 1, cell `+0x10` = -1 | tile `+0x34` = `0x00010001`, cell `+0x10` = 0, `+0x14` = `0x80000001` |
| A/B switches | | `IWZ_TOME=conservative` (scene boxes, no distance), `IWZ_TOME_LEGACY_CELL` (old cell record), `IWZ_TOME_TILE34/CELL10/CELL14` (hex) |

Props get their cull distance from the generator side (`tome_cull.py cull-distances`, below): the distance beyond which
the prop's bounding sphere covers fewer than 30 pixels of a 1920 x 1080 frame (`1130 x radius x sqrt(pi / 30)`, about
366 x radius). Spaceland's own props cull at a median 174 x radius (about 130 pixels), so this rule is stricter than the
shipped map: what disappears at its cull distance is smaller than 30 pixels.

## The tool: `tools-source/iwzmap/tome_cull.py`

```
python -B tome_cull.py cull-distances <src>/smodels.txt --models <worldkit cp_zmb.sqlite> --out <src2>/smodels.txt
python -B tome_cull.py read   <work>/dump/cp_iwz/maps/cp/cp_iwz.d3dbsp.gfxmap
python -B tome_cull.py check  <gfxmap> --db <db of this compile> --layout <src>/layout.json [--json out]
python -B tome_cull.py views  --layout <src>/layout.json --out plans/door_views.json --back 200 --limit 24
python -B tome_cull.py frames <run folder> --db <db> --gfxmap <gfxmap> [--json out]
python -B tome_cull.py model  <gfxmap> --log <perfzones client.stdout.log>
```

The database of a compile: `worldkit/iw7_world.py build --dump <work>/dump/cp_iwz --db X`, then
`iw7_see.py index --db X --dump <template dump>` for the meshes (about 2 s together).

- **check** (before the zone step; the compile alone takes 10 s): the tome's size and CRC32C; every prop has exactly one
  object; its box equals its static model bounds; its mesh lies inside its box; its distance equals `cullDist`
  squared; no scene-sized prop boxes. Then every door sightline: cameras on both sides of every opening of
  `layout.json` (96 and 320 units back, straight and 20 degrees either way: 276 views on Station Zero), the world drawn
  offline from each; every prop seen on 2 or more pixels must pass the tome's frustum test, and a prop that the tome's
  distance drops must cover fewer than 30 pixels of 1080p, measured at 1920 x 1080 for that prop (otherwise it pops). 123 s for the 2,000-prop map, 273 s for 6,000.
- **views** writes a client plan that stands at door views and captures each with the engine's depth.
- **frames** reads those captures: the world drawn offline from each frame's exact camera; each prop the offline
  raster sees on 30 pixels or more and the tome keeps must show its own depth on the frame. The game keeps or drops a
  whole object, so a culled prop shows none of its depth; a prop showing a part of it is drawn (a far level of detail).
  Props the camera stands in are skipped.

## Measured (11 Nov 2026, 1920 x 1080, perfzones, three sessions a point)

Spaceland the same afternoon on the same bench: median zone fps 419.6 / 428.1 / 421.1 (mean 422.9; parity line 85 % =
359.5). "Before" is ST1's builds (conservative tome) re-measured the same afternoon plus ST1's own morning session;
"after" is the culling tome (per-object bounds, size-rule cull distances, cell record as Spaceland's).

| Props | before: median zone fps | share | after: median zone fps | share | after: worst zone |
|---|---|---|---|---|---|
| 2,000 | 272.3 (morning) / 331.5 / 326.4 | 77.7 % (afternoon mean) | 465.6 / 515.4 / 500.7 | **116.8 %** | terminus 318, arcade_2 424, parlour 399 |
| 6,000 | 223.4 (morning) / 249.4 / 248.6 | 58.9 % | 321.8 / 331.5 / 343.8 | **78.6 %** | arcade_2 225 / 234, arcade 254 (Spaceland's own worst: moon 248-261) |

- Bounds and distances alone (old cell record, 6,000): 272.0 / 354.8 / 336.1. The cell-record change made no measured
  difference; the gain is the per-object bounds and distances.
- "too many visible static models" no longer appears while a view is held; it still appears for a frame on a
  teleport, together with "camera outside umbra view volume" (the renderer then draws everything for that frame; the
  same lines appear on the conservative builds). Not seen in a walk: not measured.
- Offline check before the zone step (276 door views): 2,000 props 0 frustum errors, 0 pops of 30+ pixels (6 culled
  props cover fewer than 30 pixels at 1080p), median 232 props kept a view, max 1,269; 123 s. 6,000 props: 13,583 sightings, 0 frustum errors, 0 pops (6 culled props under 30 pixels), median 678 kept, max 3,711; 273 s. Both pass. The conservative tome fails the same check (2,039 scene-sized boxes).
- Game frames (24 door views, 6,000 props, depth): 1,763 props expected, 1,737 show their own depth, 26 do not. A/B on
  the view with 21 of them (signal cabin): with the tome's old cell record the same props are missing too (missing only
  with the culling tome: 0), and `r_umbraMinObjectContribution 0` changes nothing: they are far levels of detail of
  their models (for example the alarm speaker, missing beyond about 1,050 units, whose model has level distances 200,
  500 and 4,500), not culling.
- Kept props a view (`model`, 6,000): median 877, max 3,013. The worst views look down a long room or along the
  platforms: frustum and distance cannot remove what stands in view behind a wall. That is what occlusion (cells and
  portals in the tome) would remove; not built (below).

## Budget

Frame time from the medians: 1.53 ms + 0.246 microseconds a prop (2,000: 2.02 ms; 6,000: 3.01 ms; same spread as ST1).
Parity (2.78 ms) holds up to about **5,000 static props map-wide** (about 270 a zone by floor area), against 1,000
before. With no margin yet measured for four players and 78 zombies, the recommendation is **4,000 map-wide, a
zone's own share by floor area (about 210 on average), and no view keeping more than about 700 props**
(`tome_cull.py model` on the compile, 10 s, no build). The design aim of 640 to 720 props in a full zone (12,000+ in all)
needs occlusion.

## Not built: occlusion (cells and portals)

Read from Spaceland's tome and the game's query: the camera's tile comes from a tile tree, the leaf within the tile from
a second tree at tile `+0x1C` (`+0x18` is its bit count, 32 or more), the leaf's cells, then the cell record (36 bytes at
tile `+0x38`, the global index at `+0x10`). Spaceland's cell records carry quantized 16-bit rectangles and links
(portals); their layout is not decoded yet. The next package writes zones as cells and doors as portals in that layout,
with the same checks.