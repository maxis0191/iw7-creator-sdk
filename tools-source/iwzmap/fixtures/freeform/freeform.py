#!/usr/bin/env python3
"""Free-form level for navgen: the two-storey fixture rotated 30 degrees about z, plus a room with a 45-degree wall
and a round pillar (16-sided cylinder, radius 48), none of it on a grid.

    python freeform.py [out_dir] [--template cp_zmb.d3dbsp.colmap.hkx]   triangles.json, layout.json, navgraph.bin,
                                                                         colmap.hkx (with the template)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'twostorey'))
import twostorey  # noqa: E402

ANGLE = math.radians(30.0)
CENTRE = (512.0, 512.0)
ROOM = (1400.0, 100.0, 1900.0, 600.0)          # x0, y0, x1, y1 of the room floor (not a multiple of any cell)
PILLAR = (1620.0, 230.0, 48.0)                  # x, y, radius
START_LOWER = (200.0, 200.0, 0.0)
SEED_TOP = (200.0, 900.0, 256.0)
SEED_ROOM = (1500.0, 200.0, 0.0)


def rot(p, ang=ANGLE, c=CENTRE):
    x, y, z = p
    dx, dy = x - c[0], y - c[1]
    return (c[0] + dx * math.cos(ang) - dy * math.sin(ang), c[1] + dx * math.sin(ang) + dy * math.cos(ang), z)


def prism(cx, cy, r, z0, z1, n=16):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    t = []
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        t += [((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1)), ((a[0], a[1], z0), (b[0], b[1], z1), (a[0], a[1], z1))]
        t += [((cx, cy, z1), (a[0], a[1], z1), (b[0], b[1], z1))]      # top, up
        t += [((cx, cy, z0), (b[0], b[1], z0), (a[0], a[1], z0))]      # bottom, down
    return t


def slab_box(mn, mx):
    return twostorey.box(mn, mx)


def wall_45(p0, p1, thick, z0, z1):
    """A wall along p0 -> p1 as a box turned to the segment direction."""
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ln = math.dist(p0, p1)
    base = twostorey.box((0.0, -thick / 2, z0), (ln, thick / 2, z1))
    out = []
    for tri in base:
        out.append(tuple((p0[0] + x * math.cos(ang) - y * math.sin(ang), p0[1] + x * math.sin(ang) + y * math.cos(ang), z)
                         for x, y, z in tri))
    return out


def triangles():
    tris = [tuple(rot(p) for p in tri) for tri in twostorey.triangles()]
    x0, y0, x1, y1 = ROOM
    tris += slab_box((x0, y0, -16), (x1, y1, 0))                                  # floor
    tris += slab_box((x0 - 16, y0 - 16, -16), (x1 + 16, y0, 256))                 # walls
    tris += slab_box((x0 - 16, y1, -16), (x1 + 16, y1 + 16, 256))
    tris += slab_box((x0 - 16, y0, -16), (x0, y1, 256))
    tris += slab_box((x1, y0, -16), (x1 + 16, y1, 256))
    tris += slab_box((x0, y0 + 8, 256), (x1, y1 - 8, 272))                        # ceiling
    tris += wall_45((x0 + 120, y0, 0), (x0 + 420, y0 + 300, 0), 16, 0, 256)       # 45-degree wall, passage at its end
    tris += prism(PILLAR[0], PILLAR[1], PILLAR[2], 0, 256)
    return tris


def layout():
    return {'zones': {'rotated': {'box': [-300, -300, -16, 1400, 1400, 512]}, 'room': {'box': [ROOM[0], ROOM[1], -16, ROOM[2], ROOM[3], 272]}},
            'starts': [list(START_LOWER)],
            'spawners': [{'zone': 'rotated', 'origin': list(SEED_TOP), 'kind': 'ground', 'yaw': 0, 'on_nav': True}]}


def main(argv):
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    import numpy as np
    import navgen
    out = argv[1] if len(argv) > 1 and not argv[1].startswith('--') else HERE
    tris = triangles()
    seeds = [rot(START_LOWER), rot(SEED_TOP), SEED_ROOM]
    data, rep = navgen.generate(np.array(tris), seeds=seeds)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'navgraph.bin'), 'wb').write(data)
    json.dump([[list(v) for v in tri] for tri in tris], open(os.path.join(out, 'triangles.json'), 'w'))
    lay = layout()
    lay['starts'] = [list(rot(START_LOWER)), list(SEED_ROOM)]
    lay['spawners'][0]['origin'] = list(rot(SEED_TOP))
    json.dump(lay, open(os.path.join(out, 'layout.json'), 'w'), indent=1)
    if '--template' in argv:
        sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
        import hkcm_write
        import mapgen
        col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in tris]
        blob, _info = hkcm_write.encode(col, argv[argv.index('--template') + 1], tag=382)
        open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('layers_z', 'params')}, indent=1))


if __name__ == '__main__':
    main(sys.argv)
