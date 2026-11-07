"""Set-dressing density per zone of a generated Station Zero source (offline, from layout.json + plan.json).

usage: sz2_density.py <generated source dir> [--min-per-100m2 4] [--max-bare-run 400]

Floor area = walkable nav cells (32 x 32 units; 1 m = 39.37 units). Dressing items = placed models (decor, models),
world-geometry props, signs/posters and light fixtures. Props per 100 m2 of floor = items / area * 100.
Wall dressing: the zone's boundary nav cells (a 4-neighbour missing) are 'dressed' when a dressing item lies within
160 units horizontally (and within 280 units vertically); the longest connected run of undressed boundary cells
(8-connected, length = cells x 32 units) is the zone's bare wall run. Exit 1 when a zone is below the minimum
density or above the maximum bare run.
"""
import json, math, os, sys

src = sys.argv[1]
MIN_DENS = float(sys.argv[sys.argv.index('--min-per-100m2') + 1]) if '--min-per-100m2' in sys.argv else 4.0
MAX_RUN = float(sys.argv[sys.argv.index('--max-bare-run') + 1]) if '--max-bare-run' in sys.argv else 400.0
lay = json.load(open(os.path.join(src, 'layout.json')))
plan = json.load(open(os.path.join(src, 'plan.json')))
CELL = 32
UNITS_PER_M = 39.37

items = []
for d in lay.get('decor', []) + lay.get('models', []):
    items.append(tuple(d['origin']))
for g in lay.get('geo_props', []):
    items.append(tuple((a + b) / 2 for a, b in zip(g['mins'], g['maxs'])))
for s in lay.get('signs', []):
    items.append(tuple(s['center']))
for l in lay.get('lights', []):
    items.append(tuple(l['origin']))

cells = {}
for i, j, z, owner in plan['cells']:
    cells[(i, j)] = z
zone_of_region = {r['name']: r['zone'] for r in plan['regions']}
by_zone = {}
for i, j, z, owner in plan['cells']:
    by_zone.setdefault(zone_of_region.get(owner, '?'), []).append((i, j, z))

report, fails = {}, []
for zone, cs in sorted(by_zone.items()):
    if zone in ('gallery', '?'):
        continue
    box = lay['zones'][zone]['box']
    inside = [p for p in items if box[0] - 32 <= p[0] <= box[3] + 32 and box[1] - 32 <= p[1] <= box[4] + 32 and box[2] - 64 <= p[2] <= box[5] + 64]
    area_m2 = len(cs) * CELL * CELL / (UNITS_PER_M ** 2)
    dens = len(inside) / area_m2 * 100 if area_m2 else 0
    own = {(i, j): z for i, j, z in cs}
    boundary = [(i, j) for (i, j) in own if any((i + di, j + dj) not in cells for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    bare = set()
    for (i, j) in boundary:
        cx, cy, cz = (i + 0.5) * CELL, (j + 0.5) * CELL, own[(i, j)]
        if not any(math.hypot(p[0] - cx, p[1] - cy) < 160 and abs(p[2] - cz) < 280 for p in inside):
            bare.add((i, j))
    best, seen = 0, set()
    for c in bare:
        if c in seen:
            continue
        stack, comp = [c], 0
        seen.add(c)
        while stack:
            a = stack.pop(); comp += 1
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    n = (a[0] + di, a[1] + dj)
                    if n in bare and n not in seen:
                        seen.add(n); stack.append(n)
        best = max(best, comp)
    run = best * CELL
    if '--debug' in sys.argv and run > MAX_RUN:
        # print bare boundary stretches (rows and columns of >= 5 cells) to place dressing
        segs = []
        for axis in (0, 1):
            lines = {}
            for c in bare:
                lines.setdefault(c[1 - axis], []).append(c[axis])
            for k, vs in lines.items():
                vs = sorted(vs); a = b = vs[0]
                for v in vs[1:] + [None]:
                    if v is not None and v == b + 1:
                        b = v; continue
                    if b - a >= 4:
                        segs.append(('%s=%d' % ('y' if axis == 0 else 'x', k * CELL + 16), a * CELL, (b + 1) * CELL))
                    if v is not None:
                        a = b = v
        print('   bare stretches:', segs[:16])
    ok = dens >= MIN_DENS and run <= MAX_RUN
    report[zone] = {'floor_m2': round(area_m2, 1), 'items': len(inside), 'per_100m2': round(dens, 2),
                    'boundary_cells': len(boundary), 'bare_cells': len(bare), 'max_bare_run': run, 'ok': ok}
    if not ok:
        fails.append(zone)
    print('%-15s floor %7.1f m2  items %3d  per100m2 %6.2f  bare %3d/%3d  max bare run %5d  %s' % (
        zone, area_m2, len(inside), dens, len(bare), len(boundary), run, 'OK' if ok else 'FAIL'))
json.dump({'min_per_100m2': MIN_DENS, 'max_bare_run': MAX_RUN, 'zones': report}, open(os.path.join(src, 'density.json'), 'w'), indent=1)
print('zones failing: %s' % (', '.join(fails) or 'none'))
sys.exit(1 if fails else 0)
