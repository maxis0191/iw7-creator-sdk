"""Tiny synthetic worlds for the baker tests (no game, no files of the machine except where a test says so).

make_world(quads, materials) -> the dict lmbake.read_world returns; write_emit(dir, world, layout) writes world.bin and layout.json.
A quad is (material index, [p0, p1, p2, p3] counter clockwise seen from its front, normal): two triangles, its own four vertices.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bake'))


def pack_unit(v):
    q = [max(0, min(1023, int(round((c + 1.0) * 511.5)))) for c in v]
    return q[0] | q[1] << 10 | q[2] << 20 | 3 << 30


def tangent_for(n):
    n = np.array(n, float)
    t = np.cross(n, [0, 0, 1] if abs(n[2]) < 0.9 else [1, 0, 0])
    return t / np.linalg.norm(t)


def make_world(quads, materials):
    import lmbake
    verts, idx, surfs = [], [], []
    for m, pts, n in quads:
        first = len(verts)
        t = tangent_for(n)
        for p in pts:
            v = np.zeros(1, lmbake.VD)
            v['pos'] = p; v['bs'] = 0.0078125; v['col'] = 255; v['uv'] = (0, 0); v['lm'] = (0, 0)
            v['n'] = pack_unit(n); v['t'] = pack_unit(t)
            verts.append(v[0])
        base = len(idx)
        idx += [0, 1, 2, 0, 2, 3]
        s = np.zeros(1, lmbake.SD)
        s['mat'] = m; s['first'] = first; s['vc'] = 4; s['base'] = base; s['tc'] = 2
        P = np.array(pts, float)
        s['mn'] = P.min(0); s['mx'] = P.max(0)
        surfs.append(s[0])
    allp = np.array([v['pos'] for v in verts], float)
    return {'materials': list(materials), 'verts': np.array(verts, lmbake.VD), 'indices': np.array(idx, '<u2'),
            'surfaces': np.array(surfs, lmbake.SD), 'bounds': tuple(allp.min(0)) + tuple(allp.max(0))}


def floor_quad(mat, x0, y0, x1, y1, z=0.0):
    return (mat, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, 1))


def wall_quad_x(mat, x, y0, y1, z0, z1, facing=1):
    """a wall standing at x, facing +x (facing 1) or -x (-1)"""
    if facing > 0:
        return (mat, [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], (1, 0, 0))
    return (mat, [(x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1)], (-1, 0, 0))


def write_emit(path, world, layout=None, smodels=None, extra=None):
    import lmbake
    os.makedirs(path, exist_ok=True)
    lmbake.write_world(world, os.path.join(path, 'world.bin'))
    json.dump(layout or {'lights': []}, open(os.path.join(path, 'layout.json'), 'w'))
    if smodels:
        open(os.path.join(path, 'smodels.txt'), 'w', newline='\n').write('\n'.join(smodels) + '\n')
    for name, data in (extra or {}).items():
        json.dump(data, open(os.path.join(path, name), 'w'))
