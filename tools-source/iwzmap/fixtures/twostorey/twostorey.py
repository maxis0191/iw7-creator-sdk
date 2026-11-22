#!/usr/bin/env python3
"""Synthetic two-storey level for navgen: two 1024 x 1024 floors (tops at z 0 and z 256) joined by one straight stair
(32 steps, riser 8, tread 16, 160 wide, solid underneath), closed boxes, perimeter walls, a stairwell opening in the
upper slab so the stair has headroom. The upper floor lies over the lower one.

    python twostorey.py [out_dir]      writes triangles.json, layout.json and navgraph.bin (and colmap.hkx when the
                                       stock colmap template is given with --template)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAIR_X = (416.0, 576.0)
STAIR_Y0, TREAD, RISER, STEPS = 128.0, 16.0, 8.0, 32
START = (200.0, 200.0, 0.0)
TOP_SEED = (200.0, 900.0, 256.0)


def box(mn, mx):
    """Twelve triangles, outward normals (counter-clockwise seen from outside)."""
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    q = [
        ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),   # +z
        ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)),   # -z
        ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),   # -y
        ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),   # +y
        ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),   # -x
        ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),   # +x
    ]
    out = []
    for a, b, c, d in q:
        out += [(a, b, c), (a, c, d)]
    return out


def triangles():
    t = []
    t += box((0, 0, -16), (1024, 1024, 0))                       # lower floor
    t += box((0, 0, 240), (400, 640, 256))                       # upper floor, around the stairwell
    t += box((624, 0, 240), (1024, 640, 256))
    t += box((0, 640, 240), (1024, 1024, 256))
    for k in range(STEPS):                                       # stair, solid from the floor up
        y = STAIR_Y0 + TREAD * k
        t += box((STAIR_X[0], y, 0), (STAIR_X[1], y + TREAD, RISER * (k + 1)))
    t += box((-16, -16, -16), (1040, 0, 512))                    # perimeter walls
    t += box((-16, 1024, -16), (1040, 1040, 512))
    t += box((-16, 0, -16), (0, 1024, 512))
    t += box((1024, 0, -16), (1040, 1024, 512))
    return t


def layout():
    return {
        'zones': {'lower': {'box': [0, 0, -16, 1024, 1024, 240]}, 'upper': {'box': [0, 0, 240, 1024, 1024, 512]}},
        'starts': [list(START)],
        'spawners': [{'zone': 'upper', 'origin': list(TOP_SEED), 'kind': 'ground', 'yaw': 0, 'on_nav': True}],
        'stairs': [{'zone': 'lower', 'space': 'stair_main', 'axis': 'y', 'span': [STAIR_Y0, STAIR_Y0 + TREAD * STEPS],
                    'c': list(STAIR_X), 'z': [0, 256], 'steps': STEPS, 'side_walls': False, 'stringers': []}],
    }


def main(argv):
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    import numpy as np
    import navgen
    out = argv[1] if len(argv) > 1 and not argv[1].startswith('--') else HERE
    tris = triangles()
    data, rep = navgen.generate(np.array(tris), seeds=[START])
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'navgraph.bin'), 'wb').write(data)
    json.dump([[list(v) for v in tri] for tri in tris], open(os.path.join(out, 'triangles.json'), 'w'))
    json.dump(layout(), open(os.path.join(out, 'layout.json'), 'w'), indent=1)
    if '--template' in argv:
        import hkcm_write
        import mapgen
        col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in tris]
        blob, _info = hkcm_write.encode(col, argv[argv.index('--template') + 1], tag=382)
        open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)
    print(json.dumps({k: v for k, v in rep.items() if k != 'cells_detail'}, indent=1))


if __name__ == '__main__':
    main(sys.argv)
