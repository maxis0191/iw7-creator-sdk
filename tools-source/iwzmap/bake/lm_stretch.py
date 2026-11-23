"""Stretched lightmap triangles of a world (the R7 baker bug's measure, ported from the Studio's rooms/lmstretch.py).

A triangle is stretched when its longest lightmap edge, in texels, is more than 3 times (its longest world edge in texels + 6 of
padding); only triangles of world area >= 4 count. A vertex shared by two charts used to keep one chart's coordinate, so the
triangles of the other chart read the atlas from far away (striped lighting on walls).

usage (bake python): lm_stretch.py <baked folder with world.bin and bake.json>      or     lm_stretch.py --plan <emit folder> [--texel 8] [--no-split]
  --plan lays the charts out without baking and measures the result (seconds), with or without the vertex split.
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lmbake


def stretched(w, W, H, texel, limit=3.0, min_area=4.0):
    """Per triangle with world area >= min_area: (surface, centre, area, reach). Returns (rows, indices of stretched rows)."""
    v, S, I = w['verts'], w['surfaces'], w['indices']
    pos, lm = v['pos'].astype(float), v['lm'].astype(float)
    rows = []
    for si, s in enumerate(S):
        tri = I[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(int) + s['first']
        P0, P1, P2 = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
        wa = np.linalg.norm(np.cross(P1 - P0, P2 - P0), axis=1) / 2.0
        U0, U1, U2 = lm[tri[:, 0]], lm[tri[:, 1]], lm[tri[:, 2]]
        el = np.maximum.reduce([np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1), np.linalg.norm(P0 - P2, axis=1)])
        lel = np.maximum.reduce([np.hypot((U1[:, 0] - U0[:, 0]) * W, (U1[:, 1] - U0[:, 1]) * H),
                                 np.hypot((U2[:, 0] - U1[:, 0]) * W, (U2[:, 1] - U1[:, 1]) * H),
                                 np.hypot((U0[:, 0] - U2[:, 0]) * W, (U0[:, 1] - U2[:, 1]) * H)])
        reach = lel / np.maximum(el / texel + 6.0, 1e-9)
        for k in np.nonzero(wa >= min_area)[0]:
            rows.append((si, (P0[k] + P1[k] + P2[k]) / 3.0, float(wa[k]), float(reach[k])))
    return rows, [i for i, r in enumerate(rows) if r[3] > limit]


def plan(emit, texel=8.0, split=True):
    """Chart layout of an emit's world.bin without the bake: returns (world with lightmap coordinates, W, H, vertices added)."""
    w = lmbake.read_world(os.path.join(emit, 'world.bin'))
    charts, _ = lmbake.build_charts(w, texel)
    added = lmbake.split_shared_vertices(w, charts)['added'] if split else 0
    W, H = lmbake.pack(charts)
    lmbake.chart_texels(charts, w, W, H)
    return w, W, H, added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder'); ap.add_argument('--plan', action='store_true')
    ap.add_argument('--texel', type=float, default=8.0); ap.add_argument('--no-split', action='store_true')
    a = ap.parse_args()
    if a.plan:
        w, W, H, added = plan(a.folder, a.texel, not a.no_split)
        texel = a.texel
    else:
        w = lmbake.read_world(os.path.join(a.folder, 'world.bin'))
        bk = json.load(open(os.path.join(a.folder, 'bake.json')))
        W, H = bk['atlas']; texel = float(bk['texel']); added = 0
    rows, bad = stretched(w, W, H, texel)
    print('vertices %d (added %d), atlas %d x %d, triangles %d (area >= 4), stretched %d (%.1f %%)' %
          (len(w['verts']), added, W, H, len(rows), len(bad), 100.0 * len(bad) / max(len(rows), 1)))


if __name__ == '__main__':
    main()
