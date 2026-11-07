"""Flatness of a generated Station Zero source: the largest undetailed wall, floor and ceiling area per zone.

usage: sz2_flatness.py <generated source dir (surfaces.json, layout.json)> [--floor 360000] [--ceiling 360000]
                       [--wall 160000] [--json out.json]

Surfaces: every axis-aligned quad of surfaces.json (written by station_zero2.py from the brush builder) with an area of
at least 64 x 64 units; walls are vertical, floors face up, ceilings down. Coplanar surfaces of a zone are rasterised
on a 32-unit grid of their plane (cell -> material of the quad covering its centre). Detail = anything within 24 units
in front of that plane (or touching it): every other quad (trims, frames, beams, columns, stains, signs, steps) by its
bounding box, and the placed models, signs and light fixtures of layout.json (+-24 units around their origin). The
largest 4-connected run of undetailed cells of one material is the undetailed area (units^2; 1 m^2 = 1550 units^2).
Thresholds (defaults: floor and ceiling 600 x 600, wall 400 x 400); exit 1 when a zone exceeds one.
"""
import json, math, os, sys
from collections import defaultdict

src = sys.argv[1]
arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
LIM = {'floor': arg('--floor', 360000.0), 'ceiling': arg('--ceiling', 360000.0), 'wall': arg('--wall', 160000.0)}
CELL, NEAR = 32.0, 24.0
quads = json.load(open(os.path.join(src, 'surfaces.json')))['quads']
lay = json.load(open(os.path.join(src, 'layout.json')))
points = [tuple(d['origin']) for d in lay.get('decor', []) + lay.get('models', [])]
points += [tuple(s['center']) for s in lay.get('signs', [])] + [tuple(l['origin']) for l in lay.get('lights', [])]


def axis_of(n):
    a = max(range(3), key=lambda i: abs(n[i]))
    return a if abs(n[a]) > 0.99 else None


planes = defaultdict(list)
for zone, mat, pts, n in quads:
    a = axis_of(n)
    if a is None:
        continue
    ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    o = [i for i in range(3) if i != a]
    area = ext[o[0]] * ext[o[1]]
    if area < 64 * 64 or mat in ('black',):
        continue
    planes[(zone, a, round(pts[0][a]), 1 if n[a] > 0 else -1)].append((mat, pts, o))

results = defaultdict(dict)
for (zone, a, coord, sg), surfs in planes.items():
    cat = 'wall' if a != 2 else ('floor' if sg > 0 else 'ceiling')
    o = surfs[0][2]
    cells = {}
    for mat, pts, _ in surfs:
        u0, u1 = min(p[o[0]] for p in pts), max(p[o[0]] for p in pts)
        v0, v1 = min(p[o[1]] for p in pts), max(p[o[1]] for p in pts)
        for i in range(int(math.floor(u0 / CELL)), int(math.ceil(u1 / CELL))):
            for j in range(int(math.floor(v0 / CELL)), int(math.ceil(v1 / CELL))):
                cu, cv = (i + 0.5) * CELL, (j + 0.5) * CELL
                if u0 <= cu <= u1 and v0 <= cv <= v1:
                    cells[(i, j)] = mat
    if not cells:
        continue
    detail = set()

    def mark(b0, b1, c0, c1):
        for i in range(int(math.floor(b0 / CELL)), int(math.ceil(b1 / CELL)) + 1):
            for j in range(int(math.floor(c0 / CELL)), int(math.ceil(c1 / CELL)) + 1):
                detail.add((i, j))
    for z2, mat2, pts2, n2 in quads:
        if z2 != zone:
            continue
        d = [(p[a] - coord) * sg for p in pts2]
        if max(d) < -1 or min(d) > NEAR or (max(d) - min(d) < 0.01 and abs(d[0]) < 0.01 and mat2 in [m for m, _, _ in surfs]):
            continue    # behind, too far, or one of the plane's own surfaces
        if abs(min(d)) < 0.01 and abs(max(d)) < 0.01 and axis_of(n2) == a:
            # coplanar surface of another material: a material border, not detail
            continue
        mark(min(p[o[0]] for p in pts2) - 8, max(p[o[0]] for p in pts2) + 8, min(p[o[1]] for p in pts2) - 8, max(p[o[1]] for p in pts2) + 8)
    for p in points:
        if -1 <= (p[a] - coord) * sg <= NEAR + 40:
            mark(p[o[0]] - 24, p[o[0]] + 24, p[o[1]] - 24, p[o[1]] + 24)
    seen, best, best_at = set(), 0, None
    for c, m in cells.items():
        if c in seen or c in detail:
            continue
        stack, comp = [c], []
        seen.add(c)
        while stack:
            q = stack.pop(); comp.append(q)
            for dq in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                r = (q[0] + dq[0], q[1] + dq[1])
                if r in cells and r not in seen and r not in detail and cells[r] == m:
                    seen.add(r); stack.append(r)
        if len(comp) > best:
            best = len(comp)
            us = [x[0] for x in comp]; vs = [x[1] for x in comp]
            best_at = {'material': m, 'plane': '%s=%d' % ('xyz'[a], coord), 'u': [min(us) * CELL, (max(us) + 1) * CELL],
                       'v': [min(vs) * CELL, (max(vs) + 1) * CELL]}
    area = best * CELL * CELL
    cur = results[zone].get(cat)
    if cur is None or area > cur['area']:
        results[zone][cat] = {'area': area, 'm2': round(area / 1550.0, 1), 'where': best_at}

fails = []
for zone in sorted(results):
    row = []
    for cat in ('wall', 'floor', 'ceiling'):
        r = results[zone].get(cat)
        if not r:
            continue
        ok = r['area'] <= LIM[cat]
        r['ok'] = ok
        if not ok:
            fails.append('%s/%s' % (zone, cat))
        row.append('%s %7d (%5.1f m2)%s' % (cat, r['area'], r['m2'], '' if ok else ' FAIL'))
    print('%-15s %s' % (zone, '  '.join(row)))
out = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else os.path.join(src, 'flatness.json')
json.dump({'limits': LIM, 'zones': results, 'fails': fails}, open(out, 'w'), indent=1)
print('flatness fails: %s' % (', '.join(fails) or 'none'))
sys.exit(1 if fails else 0)
