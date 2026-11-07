"""Offline checks of a generated Station Zero v2 source dir: plan image + nav/data consistency report.

usage: sz2_plan.py <source dir> [out png]
Checks (exit code 1 on failure):
  - every zone has nav cells and is reachable from the player starts over nav links (doors count as open)
  - spawners, starts, walk waypoints, dog spawners lie on nav cells of the right zone (within one cell)
  - consecutive walk waypoints are connected over nav links
  - nav links never rise more than 18 units
Writes a top-down plan (cells coloured by height, blockers, openings, spawners, interactions, walk path).
"""
import collections, json, math, os, sys
from PIL import Image, ImageDraw

src = sys.argv[1]
out_png = sys.argv[2] if len(sys.argv) > 2 else os.path.join(src, 'plan.png')
plan = json.load(open(os.path.join(src, 'plan.json')))
layout = json.load(open(os.path.join(src, 'layout.json')))
CELL = 32
cells = {(i, j): (z, o) for i, j, z, o in plan['cells']}
adj = {frozenset(a) for a in plan['adj']}
zone_of = {r['name']: r['zone'] for r in plan['regions']}


def linked(a, b):
    za, oa = cells[a]; zb, ob = cells[b]
    return abs(za - zb) <= 18 and (oa == ob or frozenset((oa, ob)) in adj)


nbr = collections.defaultdict(list)
for (i, j) in cells:
    for di, dj in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        k = (i + di, j + dj)
        if k in cells and linked((i, j), k):
            nbr[(i, j)].append(k)


def cell_at(x, y, z=None, zone=None):
    best = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            k = (int(math.floor(x / CELL)) + di, int(math.floor(y / CELL)) + dj)
            if k in cells:
                cz, o = cells[k]
                if z is not None and abs(cz - z) > 40:
                    continue
                if zone and zone_of[o] != zone:
                    continue
                d = abs(di) + abs(dj)
                if best is None or d < best[0]:
                    best = (d, k)
    return best[1] if best else None


def bfs(start):
    seen = {start}; q = collections.deque([start])
    while q:
        c = q.popleft()
        for n in nbr[c]:
            if n not in seen:
                seen.add(n); q.append(n)
    return seen


fails, notes = [], []
starts = layout['starts']
s0 = cell_at(starts[0][0], starts[0][1], starts[0][2])
if s0 is None:
    fails.append('start 0 not on nav')
reach = bfs(s0) if s0 else set()
by_zone = collections.Counter(zone_of[o] for (z, o) in cells.values())
reach_zone = collections.Counter(zone_of[cells[c][1]] for c in reach)
for zone in layout['zones']:
    notes.append('zone %-15s cells %5d reachable %5d' % (zone, by_zone[zone], reach_zone[zone]))
    if by_zone[zone] == 0:
        fails.append('zone %s has no nav cells' % zone)
    elif reach_zone[zone] < by_zone[zone] * 0.9:
        fails.append('zone %s: only %d/%d cells reachable from the start' % (zone, reach_zone[zone], by_zone[zone]))
for k, st in enumerate(starts):
    if cell_at(st[0], st[1], st[2], 'ticket_hall') is None:
        fails.append('start %d off nav' % k)
for s in layout['spawners']:
    x, y, z = s['origin']
    if s['kind'] == 'ceiling':
        c = cell_at(x, y, None, s['zone'])
    else:
        c = cell_at(x, y, z, s['zone'])
    if c is None:
        fails.append('spawner %s %s (%g %g %g) off nav' % (s['zone'], s['kind'], x, y, z))
    elif c not in reach:
        fails.append('spawner %s (%g %g) unreachable' % (s['zone'], x, y))
    # a spawner inside (or within 24 of) a decor clip box: its zombie spawns into the prop (QA g18: platform_a vents)
    if s['kind'] != 'ceiling':
        for d in layout.get('decor', []):
            cl = d.get('clip')
            if not cl:
                continue
            dx_, dy_, dz_ = d['origin']
            if abs(x - dx_) < cl[0] + 24 and abs(y - dy_) < cl[1] + 24 and abs(z - dz_) < 2 * cl[2] + 40:
                fails.append('spawner %s (%g %g) inside the clip of %s at (%g %g)' % (s['zone'], x, y, d['model'], dx_, dy_))
for it in layout['interactions']:
    x, y, z = it['origin']
    if cell_at(x, y, None) is None:
        notes.append('interaction %s at (%g %g %g): no nav cell within 1 cell (wall mounted?)' % (it['kind'], x, y, z))
walk = layout['walk']
prev = None
for k, p in enumerate(walk):
    c = cell_at(p[0], p[1], p[2])
    if c is None:
        fails.append('walk %d (%g %g %g) off nav' % (k, *p)); prev = None; continue
    if prev is not None:
        seen = bfs(prev)
        if c not in seen:
            fails.append('walk %d -> %d not connected' % (k - 1, k))
    prev = c

# plan image
x0, y0 = -3800, 0
W, H = 7800, 4800
S = 0.2
img = Image.new('RGB', (int(W * S), int(H * S)), (20, 20, 24))
d = ImageDraw.Draw(img)


def P(x, y):
    return ((x - x0) * S, (H - (y - y0)) * S)


ZC = {}
palette = [(230, 230, 240), (120, 200, 255), (90, 160, 230), (255, 170, 80), (255, 130, 40), (230, 60, 60), (160, 140, 110),
           (140, 220, 140), (200, 200, 120), (180, 180, 180)]
for k, z in enumerate(list(layout['zones']) + ['gallery']):
    ZC[z] = palette[k % len(palette)]
for (i, j), (z, o) in cells.items():
    c = ZC.get(zone_of[o], (255, 255, 255))
    t = max(0.35, min(1.0, 0.55 + (z + 384) / 800))
    col = tuple(int(v * t) for v in c)
    if (i, j) not in reach:
        col = (255, 0, 255)
    a, b = P(i * CELL, (j + 1) * CELL); e, f = P((i + 1) * CELL, j * CELL)
    d.rectangle([a, b, e - 1, f - 1], fill=col)
for bx0, by0, bx1, by1, bz0, bz1 in plan['blockers']:
    d.rectangle([*P(bx0, by1), *P(bx1, by0)], outline=(255, 60, 60))
for s in layout['spawners']:
    x, y, _ = s['origin']; cx, cy = P(x, y)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill={'ground': (255, 0, 0), 'wall': (255, 128, 0), 'ceiling': (255, 255, 0)}[s['kind']])
for it in layout['interactions']:
    x, y, _ = it['origin']; cx, cy = P(x, y)
    d.rectangle([cx - 4, cy - 4, cx + 4, cy + 4], fill=(0, 255, 255))
for st in starts:
    cx, cy = P(st[0], st[1]); d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(0, 255, 0))
pts = [P(p[0], p[1]) for p in walk]
d.line(pts, fill=(255, 255, 0), width=2)
for dr in layout['doors']:
    if dr['axis'] == 1:
        d.line([P(dr['lo'], dr['plane']), P(dr['hi'], dr['plane'])], fill=(255, 0, 0), width=4)
    else:
        d.line([P(dr['plane'], dr['lo']), P(dr['plane'], dr['hi'])], fill=(255, 0, 0), width=4)
img.save(out_png)
report = {'fails': fails, 'notes': notes, 'cells': len(cells), 'reachable': len(reach)}
json.dump(report, open(os.path.join(src, 'plan_check.json'), 'w'), indent=1)
for n in notes: print(n)
for f in fails: print('FAIL', f)
print('plan', out_png, 'cells', len(cells), 'reachable', len(reach), 'fails', len(fails))
sys.exit(1 if fails else 0)
