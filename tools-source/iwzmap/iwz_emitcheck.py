#!/usr/bin/env python3
"""Offline gate for an emitted IWZ level directory (colmap.hkx + navgraph.bin + layout.json).

Answers, in seconds and without building a fastfile or starting the game, the
questions that used to cost one zone build plus one game launch each:

  check   every nav cell rests on collision, every nav link is walkable, every
          spawner can path to a player start, and a walk simulation from the
          player starts finds leaks, traps, hollow spaces under nav surfaces and
          walkable regions the AI cannot reach.
  stairs  a side-by-side profile of every stair (nav surface, collision layers,
          side openness, hollows) so a failing stair can be compared to a
          passing one.
  diff    what changed between two emits, which zones/stairs/doors that touches,
          and therefore which in-game probes are worth re-running (and which
          earlier verdicts still stand).
  at      what the emit says about a recorded position (on a floor, in the air,
          inside solid geometry), to read a stuck or sunk agent without a launch.
  route   nav path length and walking time between two points, to size a probe
          timeout before spending a launch on it.

The walk simulation is a model, not the engine: 16-unit columns, an 18-unit
step, a centre-line wall test.  A clean report removes whole defect classes
before a launch; it does not replace the in-game probe of what it flags.
"""
import argparse
import collections
import heapq
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STEP = 18.0          # tallest rise an agent walks up without jumping
AGENT_H = 72.0       # standing agent height
MIN_CLEAR = 40.0     # lowest headroom an agent can still be pushed into
EX, EY = 0.37, 0.29  # sample offset: keeps probes off triangle edges
NAV_TOL = 24.0       # vertical tolerance when matching a position to a nav cell
HS, AREA, EDGE = 336, 72, 32


# --------------------------------------------------------------------------- loading
def load_tris(path):
    from hkpack import Packfile
    import hkcm
    pf = Packfile(open(path, 'rb').read())
    for addr, name, _size in pf.objects:
        if name == 'hknpCompressedMeshShapeData':
            data = hkcm.decode_cm_data(pf, addr)
            return [tuple(tuple(c * 32.0 for c in v) for v in t) for t in data['tris']]
    raise ValueError('no hknpCompressedMeshShapeData in ' + path)


def load_nav(path):
    g = open(path, 'rb').read()[48:]
    _ver, _pad, area_bytes, _kd = struct.unpack_from('<IIII', g, 0)
    areas = {}
    off = HS
    while off < HS + area_bytes:
        centre = struct.unpack_from('<3f', g, off + 32)
        corners, nbrs = [], []
        for e in range(4):
            eo = off + AREA + EDGE * e
            nb = struct.unpack_from('<Q', g, eo)[0]
            x, y, z, _flags, cost, _ = struct.unpack_from('<3fIII', g, eo + 8)
            corners.append((x, y, z))
            nbrs.append(nb if cost else 0)
        areas[off] = {'c': centre, 'corners': corners, 'nbrs': nbrs}
        off += AREA + EDGE * 4
    return areas


class NotAnEmit(Exception):
    """The directory lacks the collision or navigation output."""


class Emit:
    def __init__(self, tris, areas, layout, name=''):
        self.tris, self.areas, self.layout, self.name = tris, areas, layout or {}, name
        self.col = Collision(tris)
        self.nav = Nav(areas)

    @classmethod
    def load(cls, src):
        layout = {}
        lp = os.path.join(src, 'layout.json')
        if os.path.exists(lp):
            layout = json.load(open(lp, encoding='utf-8'))
        missing = [n for n in ('colmap.hkx', 'navgraph.bin')
                   if not os.path.isfile(os.path.join(src, n))]
        if missing:
            raise NotAnEmit('%s is not a full emit: missing %s' % (src, ', '.join(missing)))
        return cls(load_tris(os.path.join(src, 'colmap.hkx')), load_nav(os.path.join(src, 'navgraph.bin')),
                   layout, os.path.basename(os.path.normpath(src)))

    # ---- labels
    def stair_boxes(self):
        out = []
        for s in self.layout.get('stairs', []):
            a0, a1 = sorted(s['span'])
            c0, c1 = sorted(s['c'])
            z0, z1 = sorted(s['z'])
            box = (a0, c0, z0, a1, c1, z1) if s['axis'] == 'x' else (c0, a0, z0, c1, a1, z1)
            out.append((s.get('space') or s.get('zone'), box, s))
        return out

    def where(self, x, y, z):
        for name, b, _s in self.stair_boxes():
            if b[0] - 48 <= x <= b[3] + 48 and b[1] - 16 <= y <= b[4] + 16 and b[2] - 48 <= z <= b[5] + 48:
                return 'stair:' + name
        best = None
        for name, zn in self.layout.get('zones', {}).items():
            b = zn.get('box')
            if b and b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] - 8 <= z <= b[5] + 8:
                vol = (b[3] - b[0]) * (b[4] - b[1])
                if best is None or vol < best[0]:
                    best = (vol, name)
        return 'zone:' + best[1] if best else 'outside'


# --------------------------------------------------------------------------- collision
class Collision:
    def __init__(self, tris, g=32.0):
        self.t, self.g = tris, g
        self.bb, self.nz = [], []
        self.flat = collections.defaultdict(list)
        self.all = collections.defaultdict(list)
        for i, (a, b, c) in enumerate(tris):
            bb = (min(a[0], b[0], c[0]), max(a[0], b[0], c[0]), min(a[1], b[1], c[1]), max(a[1], b[1], c[1]),
                  min(a[2], b[2], c[2]), max(a[2], b[2], c[2]))
            e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) or 1.0
            nz = n[2] / ln
            self.bb.append(bb)
            self.nz.append(nz)
            flat = abs(nz) > 0.05
            for ix in range(int(math.floor(bb[0] / g)), int(math.floor(bb[1] / g)) + 1):
                for iy in range(int(math.floor(bb[2] / g)), int(math.floor(bb[3] / g)) + 1):
                    self.all[(ix, iy)].append(i)
                    if flat:
                        self.flat[(ix, iy)].append(i)

    def column(self, x, y):
        """Every (z, nz) where the vertical line through (x, y) meets a surface, lowest first."""
        out = []
        for i in self.flat.get((int(math.floor(x / self.g)), int(math.floor(y / self.g))), ()):
            bb = self.bb[i]
            if x < bb[0] or x > bb[1] or y < bb[2] or y > bb[3]:
                continue
            a, b, c = self.t[i]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            u = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
            v = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
            w = 1.0 - u - v
            if u < -1e-6 or v < -1e-6 or w < -1e-6:
                continue
            out.append((u * a[2] + v * b[2] + w * c[2], self.nz[i]))
        out.sort()
        return out

    def floors(self, x, y, min_clear=0.0):
        """Walkable layers (z, headroom) in a column."""
        hits = self.column(x, y)
        out = []
        for k, (z, nz) in enumerate(hits):
            if nz < 0.7:
                continue
            clear = 9999.0
            for z2, _n in hits[k + 1:]:
                if z2 > z + 1.0:
                    clear = z2 - z
                    break
            if clear >= min_clear and not (out and abs(out[-1][0] - z) < 0.5):
                out.append((z, clear))
        return out

    def blocked(self, p, q):
        """True when the segment p-q crosses any collision triangle."""
        g = self.g
        x0, x1 = (p[0], q[0]) if p[0] <= q[0] else (q[0], p[0])
        y0, y1 = (p[1], q[1]) if p[1] <= q[1] else (q[1], p[1])
        z0, z1 = (p[2], q[2]) if p[2] <= q[2] else (q[2], p[2])
        d = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
        seen = set()
        for ix in range(int(math.floor(x0 / g)), int(math.floor(x1 / g)) + 1):
            for iy in range(int(math.floor(y0 / g)), int(math.floor(y1 / g)) + 1):
                for i in self.all.get((ix, iy), ()):
                    bb = self.bb[i]
                    if bb[0] > x1 or bb[1] < x0 or bb[2] > y1 or bb[3] < y0 or bb[4] > z1 or bb[5] < z0 or i in seen:
                        continue
                    seen.add(i)
                    a, b, c = self.t[i]
                    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                    h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
                    det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
                    if -1e-9 < det < 1e-9:
                        continue
                    f = 1.0 / det
                    s = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
                    u = f * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
                    if u < 0.0 or u > 1.0:
                        continue
                    qv = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
                    v = f * (d[0] * qv[0] + d[1] * qv[1] + d[2] * qv[2])
                    if v < 0.0 or u + v > 1.0:
                        continue
                    t = f * (e2[0] * qv[0] + e2[1] * qv[1] + e2[2] * qv[2])
                    if 0.0 <= t <= 1.0:
                        return True
        return False

    def passable(self, x0, y0, x1, y1, z):
        """Centre-line test at shin and chest height above a foot level."""
        return not (self.blocked((x0, y0, z + 20.0), (x1, y1, z + 20.0)) or
                    self.blocked((x0, y0, z + 48.0), (x1, y1, z + 48.0)))


# --------------------------------------------------------------------------- nav graph
class Nav:
    def __init__(self, areas, g=32.0):
        self.a, self.g = areas, g
        self.grid = collections.defaultdict(list)
        for k, ar in areas.items():
            xs = [c[0] for c in ar['corners']]
            ys = [c[1] for c in ar['corners']]
            ar['bb'] = (min(xs), max(xs), min(ys), max(ys))
            for ix in range(int(math.floor(min(xs) / g)), int(math.floor((max(xs) - 1e-3) / g)) + 1):
                for iy in range(int(math.floor(min(ys) / g)), int(math.floor((max(ys) - 1e-3) / g)) + 1):
                    self.grid[(ix, iy)].append(k)
        self._comp = None

    def z_at(self, k, x, y):
        ar = self.a[k]
        x0, x1, y0, y1 = ar['bb']
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6:
            return ar['c'][2]
        u = min(1.0, max(0.0, (x - x0) / (x1 - x0)))
        v = min(1.0, max(0.0, (y - y0) / (y1 - y0)))
        z = 0.0
        for cx, cy, cz in ar['corners']:
            wu = u if abs(cx - x1) < abs(cx - x0) else 1.0 - u
            wv = v if abs(cy - y1) < abs(cy - y0) else 1.0 - v
            z += wu * wv * cz
        return z

    def columns(self, x, y):
        out = []
        for k in self.grid.get((int(math.floor(x / self.g)), int(math.floor(y / self.g))), ()):
            bb = self.a[k]['bb']
            if bb[0] - 1e-3 <= x <= bb[1] + 1e-3 and bb[2] - 1e-3 <= y <= bb[3] + 1e-3:
                out.append((self.z_at(k, x, y), k))
        return out

    def at(self, x, y, z, tol=NAV_TOL):
        best = None
        for nz, k in self.columns(x, y):
            if abs(nz - z) <= tol and (best is None or abs(nz - z) < abs(best[0] - z)):
                best = (nz, k)
        return best[1] if best else None

    def nearest(self, x, y, z, reach=160.0):
        k = self.at(x, y, z, 48.0)
        if k is not None:
            return k
        best = None
        r = int(reach // self.g) + 1
        ix0, iy0 = int(math.floor(x / self.g)), int(math.floor(y / self.g))
        for ix in range(ix0 - r, ix0 + r + 1):
            for iy in range(iy0 - r, iy0 + r + 1):
                for kk in self.grid.get((ix, iy), ()):
                    c = self.a[kk]['c']
                    d = math.dist((x, y, z), c)
                    if d <= reach and (best is None or d < best[0]):
                        best = (d, kk)
        return best[1] if best else None

    def below(self, x, y, z, reach=160.0):
        """Nav cell an agent released at (x, y, z) lands on: ceiling and wall spawners."""
        best = None
        r = int(reach // self.g) + 1
        ix0, iy0 = int(math.floor(x / self.g)), int(math.floor(y / self.g))
        for ix in range(ix0 - r, ix0 + r + 1):
            for iy in range(iy0 - r, iy0 + r + 1):
                for kk in self.grid.get((ix, iy), ()):
                    c = self.a[kk]['c']
                    d = math.hypot(c[0] - x, c[1] - y)
                    if c[2] <= z + NAV_TOL and d <= reach and (best is None or (d, -c[2]) < best[0]):
                        best = ((d, -c[2]), kk)
        return best[1] if best else None

    def components(self):
        if self._comp is None:
            und = collections.defaultdict(set)
            for k, ar in self.a.items():
                for nb in ar['nbrs']:
                    if nb in self.a:
                        und[k].add(nb)
                        und[nb].add(k)
            comp, cid = {}, 0
            for k in self.a:
                if k in comp:
                    continue
                stack = [k]
                comp[k] = cid
                while stack:
                    cur = stack.pop()
                    for nb in und[cur]:
                        if nb not in comp:
                            comp[nb] = cid
                            stack.append(nb)
                cid += 1
            self._comp = comp
        return self._comp

    def route(self, a, b):
        """A* over directed links.  Returns (length, [area ids]) or (None, [])."""
        if a is None or b is None:
            return None, []
        goal = self.a[b]['c']
        dist = {a: 0.0}
        prev = {}
        heap = [(math.dist(self.a[a]['c'], goal), a)]
        done = set()
        while heap:
            _f, cur = heapq.heappop(heap)
            if cur in done:
                continue
            done.add(cur)
            if cur == b:
                path = [b]
                while path[-1] in prev:
                    path.append(prev[path[-1]])
                return dist[b], path[::-1]
            cc = self.a[cur]['c']
            for nb in self.a[cur]['nbrs']:
                if nb not in self.a:
                    continue
                nd = dist[cur] + math.dist(cc, self.a[nb]['c'])
                if nd < dist.get(nb, 1e18):
                    dist[nb] = nd
                    prev[nb] = cur
                    heapq.heappush(heap, (nd + math.dist(self.a[nb]['c'], goal), nb))
        return None, []


# --------------------------------------------------------------------------- walk simulation
class Walk:
    """Flood of where a walking agent can get from the player starts."""

    def __init__(self, emit, cell=16.0, max_cells=400000):
        self.e, self.cell, self.max = emit, cell, max_cells
        self.cache = {}
        self.adj = collections.defaultdict(list)
        self.walk, self.drop_only = set(), set()
        self.voids, self.drops = [], []

    def xy(self, ix, iy):
        return ix * self.cell + self.cell / 2 + EX, iy * self.cell + self.cell / 2 + EY

    def layers(self, ix, iy):
        key = (ix, iy)
        if key not in self.cache:
            x, y = self.xy(ix, iy)
            self.cache[key] = self.e.col.floors(x, y, MIN_CLEAR)
        return self.cache[key]

    def seed(self, p):
        ix, iy = int(math.floor(p[0] / self.cell)), int(math.floor(p[1] / self.cell))
        ls = self.layers(ix, iy)
        if not ls:
            return None
        z = min(ls, key=lambda l: abs(l[0] - p[2]))[0]
        return (ix, iy, z)

    def _expand(self, st, allow_drop):
        ix, iy, z = st
        x, y = self.xy(ix, iy)
        out = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = ix + dx, iy + dy
            cands = [l for l in self.layers(nx, ny) if l[0] <= z + STEP]
            x2, y2 = self.xy(nx, ny)
            if not cands:
                if not self.layers(nx, ny) and self.e.col.passable(x, y, x2, y2, z):
                    self.voids.append((st, (nx, ny)))
                continue
            z2 = max(c[0] for c in cands)
            if z2 >= z - STEP:
                if self.e.col.passable(x, y, x2, y2, max(z, z2)):
                    out.append((nx, ny, z2))
            elif self.e.col.passable(x, y, x2, y2, z):
                self.drops.append((st, (nx, ny, z2)))
                if allow_drop:
                    out.append((nx, ny, z2))
        return out

    def run(self, seeds):
        todo = collections.deque(s for s in seeds if s)
        self.walk = set(todo)
        while todo and len(self.walk) < self.max:
            st = todo.popleft()
            for nb in self._expand(st, False):
                self.adj[st].append(nb)
                if nb not in self.walk:
                    self.walk.add(nb)
                    todo.append(nb)
        landing = [d[1] for d in self.drops if d[1] not in self.walk]
        todo = collections.deque(dict.fromkeys(landing))
        self.drop_only = set(todo)
        while todo and len(self.walk) + len(self.drop_only) < self.max:
            st = todo.popleft()
            for nb in self._expand(st, True):
                self.adj[st].append(nb)
                if nb not in self.walk and nb not in self.drop_only:
                    self.drop_only.add(nb)
                    todo.append(nb)
        return self


def clusters(cells, adj=None):
    """Group (ix, iy, z) states into 8-connected clusters (z within one step)."""
    by = collections.defaultdict(list)
    for c in cells:
        by[(c[0], c[1])].append(c)
    seen, out = set(), []
    for c in cells:
        if c in seen:
            continue
        seen.add(c)
        grp, stack = [], [c]
        while stack:
            cur = stack.pop()
            grp.append(cur)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for nb in by.get((cur[0] + dx, cur[1] + dy), ()):
                        if nb not in seen and abs(nb[2] - cur[2]) <= STEP * 2:
                            seen.add(nb)
                            stack.append(nb)
        out.append(grp)
    return out


# --------------------------------------------------------------------------- findings
def finding(code, sev, label, cells, cell, detail, **extra):
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    zs = [c[2] for c in cells]
    f = {'code': code, 'severity': sev, 'where': label, 'count': len(cells),
         'bbox': [round(min(xs) * cell), round(min(ys) * cell), round(min(zs)),
                  round((max(xs) + 1) * cell), round((max(ys) + 1) * cell), round(max(zs))],
         'detail': detail}
    f.update(extra)
    return f


def majority(emit, cells, cell):
    cnt = collections.Counter(emit.where((c[0] + 0.5) * cell, (c[1] + 0.5) * cell, c[2]) for c in cells)
    return cnt.most_common(1)[0][0]


def check_degenerate(emit):
    """collision triangles with two equal corners: the engine reads them as a custom primitive with no shape and a query
    that touches one crashes the server (hkcdStaticMeshTree, sub_1410AD7F0+0x11B)"""
    bad = []
    for t in emit.tris:
        a, b, c = t
        u = [b[k] - a[k] for k in range(3)]; v = [c[k] - a[k] for k in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        if a == b or b == c or a == c or n[0] * n[0] + n[1] * n[1] + n[2] * n[2] < 1e-6:
            bad.append(t)
    if not bad:
        return []
    xs = [p[0] for t in bad for p in t]; ys = [p[1] for t in bad for p in t]; zs = [p[2] for t in bad for p in t]
    return [{'code': 'DEGENERATE_COLLISION', 'severity': 'error', 'where': 'map', 'count': len(bad),
             'bbox': [round(min(xs)), round(min(ys)), round(min(zs)), round(max(xs)), round(max(ys)), round(max(zs))],
             'detail': 'collision triangles with two equal corners or no area: the engine reads them as a custom primitive '
                       'with no shape and crashes the server when a query touches one'}]


def check_nav_support(emit):
    """Every nav cell centre should sit on a collision floor."""
    bad = collections.defaultdict(list)
    for k, ar in emit.areas.items():
        x, y, z = ar['c']
        floors = [f[0] for f in emit.col.floors(x + EX, y + EY)]
        if not floors:
            bad['NAV_NO_FLOOR'].append((int(x // 32), int(y // 32), z, 0.0))
            continue
        near = min(floors, key=lambda f: abs(f - z))
        if abs(near - z) <= 12.0:
            continue
        code = 'NAV_FLOATING' if near < z else 'NAV_BURIED'
        bad[code].append((int(x // 32), int(y // 32), z, z - near))
    out = []
    text = {'NAV_NO_FLOOR': 'nav cells with no collision floor in their column',
            'NAV_FLOATING': 'nav cells above the nearest collision floor: agents path through air and sink',
            'NAV_BURIED': 'nav cells below the nearest collision floor: agents path inside solid geometry'}
    for code, cells in bad.items():
        for grp in clusters(cells):
            offs = [c[3] for c in grp]
            out.append(finding(code, 'error', majority(emit, grp, 32.0), grp, 32.0,
                               text[code] + ' (offset %.0f..%.0f)' % (min(offs), max(offs))))
    return out


def check_links(emit):
    """Nav links must be walkable: no wall across them, no cliff along them."""
    out_blocked, out_steep, oneway = [], [], 0
    for k, ar in emit.areas.items():
        a = ar['c']
        for nb in ar['nbrs']:
            if nb not in emit.areas:
                continue
            other = emit.areas[nb]
            b = other['c']
            if k not in other['nbrs']:
                oneway += 1
            if k > nb and k in other['nbrs']:
                continue
            if abs(a[2] - b[2]) > STEP + 6.0:
                out_steep.append((int(a[0] // 32), int(a[1] // 32), a[2]))
            base = max(a[2], b[2])
            if emit.col.blocked((a[0] + EX, a[1] + EY, base + 20.0), (b[0] + EX, b[1] + EY, base + 20.0)) or \
               emit.col.blocked((a[0] + EX, a[1] + EY, base + 48.0), (b[0] + EX, b[1] + EY, base + 48.0)):
                out_blocked.append((int(a[0] // 32), int(a[1] // 32), a[2]))
    out = []
    for grp in clusters(out_blocked):
        out.append(finding('LINK_BLOCKED', 'error', majority(emit, grp, 32.0), grp, 32.0,
                           'nav links that cross collision: agents are told to walk through a wall, rail or riser'))
    for grp in clusters(out_steep):
        out.append(finding('LINK_STEEP', 'error', majority(emit, grp, 32.0), grp, 32.0,
                           'nav links whose ends differ by more than one step'))
    return out, oneway


def check_graph(emit):
    """Spawners and zones must reach the player starts over the nav graph."""
    out = []
    comp = emit.nav.components()
    starts = emit.layout.get('starts', [])
    start_areas = [emit.nav.nearest(*s) for s in starts]
    for s, k in zip(starts, start_areas):
        if k is None:
            out.append({'code': 'START_OFF_NAV', 'severity': 'error', 'where': emit.where(*s), 'count': 1,
                        'bbox': list(s) + list(s), 'detail': 'player start has no nav cell within 160 units'})
    home = collections.Counter(comp[k] for k in start_areas if k is not None).most_common(1)
    home = home[0][0] if home else None
    sizes = collections.Counter(comp.values())
    goal = next((k for k in start_areas if k is not None), None)
    lost = []
    for sp in emit.layout.get('spawners', []):
        o = sp['origin']
        k = emit.nav.nearest(*o) if sp.get('kind', 'ground') == 'ground' else emit.nav.below(*o)
        if k is None or (home is not None and comp[k] != home):
            lost.append((sp, 'no nav cell within 160 units' if k is None else 'nav island'))
        elif goal is not None and emit.nav.route(k, goal)[0] is None:
            lost.append((sp, 'no directed route to the start'))
    for sp, why in lost:
        o = sp['origin']
        out.append({'code': 'SPAWNER_CANNOT_REACH', 'severity': 'error', 'where': 'zone:' + str(sp.get('zone')),
                    'count': 1, 'bbox': list(o) + list(o), 'detail': 'spawner cannot path to a player start: ' + why})
    islands = [(n, c) for c, n in sizes.items() if c != home]
    if islands:
        # where each island is (the warning used to say only how many): the box of its cells' centres
        boxes = []
        for n, c in sorted(islands):
            pts = [emit.nav.a[k].get('c') or emit.nav.a[k].get('center') for k in emit.nav.a if comp.get(k) == c]
            pts = [p for p in pts if p]
            if pts:
                boxes.append('%d cells at %s' % (n, [round(min(p[0] for p in pts)), round(min(p[1] for p in pts)), round(min(p[2] for p in pts)),
                                                     round(max(p[0] for p in pts)), round(max(p[1] for p in pts))]))
        out.append({'code': 'NAV_ISLANDS', 'severity': 'warn', 'where': 'map', 'count': len(islands),
                    'bbox': [], 'detail': '%d nav islands not connected to the start island (%d cells in total)%s'
                    % (len(islands), sum(n for n, _c in islands), (': ' + '; '.join(boxes)) if boxes else '')})
    return out


def check_walk(emit, cell=16.0):
    """Walk simulation from the player starts."""
    w = Walk(emit, cell)
    starts = emit.layout.get('starts', [])
    w.run([w.seed(s) for s in starts])
    out = []
    reach = w.walk | w.drop_only
    covered = {}
    for st in reach:
        x, y = w.xy(st[0], st[1])
        covered[st] = emit.nav.at(x, y, st[2]) is not None
    # hollow: reachable floor that sits under a nav surface but has no nav of its own
    hollow = []
    for st in reach:
        if covered[st]:
            continue
        x, y = w.xy(st[0], st[1])
        above = [nz for nz, _k in emit.nav.columns(x, y) if STEP < nz - st[2] <= 160.0]
        if above:
            hollow.append(st)
    for grp in clusters(hollow):
        if len(grp) * cell * cell < 512:
            continue
        how = 'walk' if any(c in w.walk for c in grp) else 'drop'
        out.append(finding('HOLLOW_UNDER_NAV', 'warn', majority(emit, grp, cell), grp, cell,
                           'agents can get under a nav surface here (reached by %s); the nav graph only knows the '
                           'surface above, so an agent pushed or dropped in has no path out' % how, reached=how))
    # traps: reached only by dropping in
    for grp in clusters(list(w.drop_only)):
        if len(grp) * cell * cell < 1024:
            continue
        nav_cov = sum(1 for c in grp if covered[c])
        depth = min((d[0][2] - d[1][2]) for d in w.drops if d[1] in set(grp)) if grp else 0
        sev = 'error' if depth > 40 else 'warn'
        out.append(finding('DROP_ONLY_REGION', sev, majority(emit, grp, cell), grp, cell,
                           'floor you can drop into but not walk out of (shallowest drop %.0f); %d%% has nav'
                           % (depth, 100 * nav_cov // len(grp)), drop=round(depth)))
    # leaks into the void
    leaks = [v[0] for v in w.voids]
    for grp in clusters(leaks):
        if len(grp) < 2:
            continue
        out.append(finding('OPEN_EDGE_TO_VOID', 'error', majority(emit, grp, cell), grp, cell,
                           'walkable floor edge with no wall and nothing below: players and agents can leave the map'))
    # deep off-nav: walkable places the AI cannot path to
    dist = {st: 0 for st in reach if covered[st]}
    todo = collections.deque(dist)
    while todo:
        cur = todo.popleft()
        for nb in w.adj.get(cur, ()):
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                todo.append(nb)
    deep = [st for st in w.walk if not covered[st] and dist.get(st, 99) * cell > 48.0 and st not in set(hollow)]
    for grp in clusters(deep):
        if len(grp) * cell * cell < 4096:
            continue
        out.append(finding('WALKABLE_OFF_NAV', 'warn', majority(emit, grp, cell), grp, cell,
                           'players can stand here but no nav cell is within 48 units: zombies cannot reach them'))
    # nav the player side never reaches
    unreached = 0
    for k, ar in emit.areas.items():
        x, y, z = ar['c']
        ix, iy = int(math.floor(x / cell)), int(math.floor(y / cell))
        if not any((ix, iy, l[0]) in reach for l in w.layers(ix, iy) if abs(l[0] - z) <= NAV_TOL):
            unreached += 1
    stats = {'walk_cells': len(w.walk), 'drop_only_cells': len(w.drop_only), 'void_edges': len(w.voids),
             'nav_cells': len(emit.areas), 'nav_cells_not_walk_reached': unreached,
             'walk_cells_without_nav': sum(1 for st in w.walk if not covered[st])}
    return out, stats, w


# --------------------------------------------------------------------------- stairs
def stair_profile(emit, stair, step=8.0):
    """Sample a stair along its axis: nav surface, collision layers, sides."""
    ax = stair['axis']
    a0, a1 = sorted(stair['span'])
    c0, c1 = sorted(stair['c'])
    z0, z1 = sorted(stair['z'])
    mid = (c0 + c1) / 2.0

    def pt(s, c):
        return (s + EX, c + EY) if ax == 'x' else (c + EX, s + EY)

    rows = []
    s = a0 - 64.0
    while s <= a1 + 64.0:
        x, y = pt(s, mid)
        navs = sorted(nz for nz, _k in emit.nav.columns(x, y) if z0 - 64 <= nz <= z1 + 64)
        hits = [(round(z, 1), round(n, 2)) for z, n in emit.col.column(x, y) if z0 - 64 <= z <= z1 + 80]
        floors = [h[0] for h in hits if h[1] >= 0.7]
        top = max(floors) if floors else None
        nav = max(navs) if navs else None
        sides = []
        for c_in, c_out in ((c0 + 12.0, c0 - 20.0), (c1 - 12.0, c1 + 20.0)):
            if top is None:
                sides.append('?')
                continue
            xi, yi = pt(s, c_in)
            xo, yo = pt(s, c_out)
            if not emit.col.passable(xi, yi, xo, yo, top):
                sides.append('wall')
                continue
            outside = [f[0] for f in emit.col.floors(xo, yo) if f[0] <= top + STEP]
            if not outside:
                sides.append('void')
            else:
                d = top - max(outside)
                sides.append('level' if abs(d) <= STEP else 'drop%d' % round(d))
        rows.append({'s': s, 'nav': nav, 'top': top, 'layers': hits, 'left': sides[0], 'right': sides[1],
                     'navs': [round(n, 1) for n in navs]})
        s += step
    return rows


def check_stairs(emit):
    out, tables = [], {}
    for name, box, st in emit.stair_boxes():
        rows = stair_profile(emit, st)
        tables[name] = rows
        inside = [r for r in rows if min(st['span']) < r['s'] < max(st['span'])]
        gaps = [r for r in inside if r['nav'] is not None and r['top'] is not None and abs(r['nav'] - r['top']) > 12.0]
        nonav = [r for r in inside if r['nav'] is None]
        risers = []
        prev = None
        for r in inside:
            if prev is not None and r['top'] is not None and prev['top'] is not None and abs(r['top'] - prev['top']) > STEP:
                risers.append(r)
            prev = r
        opens = [r for r in inside if any(side.startswith('drop') or side == 'void' for side in (r['left'], r['right']))]
        label = 'stair:' + name

        def f(code, sev, rs, detail):
            ss = [r['s'] for r in rs]
            out.append({'code': code, 'severity': sev, 'where': label, 'count': len(rs),
                        'bbox': [min(ss), max(ss)], 'detail': detail})
        if gaps:
            worst = max(gaps, key=lambda r: abs(r['nav'] - r['top']))
            f('STAIR_NAV_OFF_SURFACE', 'error', gaps, 'nav and collision surface disagree along the stair (worst %.0f at s=%.0f)'
              % (worst['nav'] - worst['top'], worst['s']))
        if nonav:
            f('STAIR_NAV_GAP', 'error', nonav, 'no nav on the stair centre line at %d samples' % len(nonav))
        if risers:
            f('STAIR_RISER', 'error', risers, 'collision rises more than one step between samples 8 units apart')
        if len(opens) >= 3:
            f('STAIR_OPEN_SIDE', 'warn', opens, 'stair side is open to a lower floor or void: agents can leave the stair '
              'sideways (sides %s)' % sorted({side for r in opens for side in (r['left'], r['right']) if side not in ('wall', 'level')}))
    return out, tables


def print_stairs(tables, only=None):
    for name, rows in tables.items():
        if only and name != only:
            continue
        print('== stair %s' % name)
        print('%8s %8s %8s %6s  %-8s %-8s %s' % ('s', 'nav', 'col_top', 'd', 'left', 'right', 'collision layers (z, nz)'))
        for r in rows:
            d = '' if r['nav'] is None or r['top'] is None else '%.0f' % (r['nav'] - r['top'])
            print('%8.0f %8s %8s %6s  %-8s %-8s %s' % (
                r['s'], '-' if r['nav'] is None else '%.1f' % r['nav'], '-' if r['top'] is None else '%.1f' % r['top'],
                d, r['left'], r['right'], r['layers']))


# --------------------------------------------------------------------------- reports
def run_check(emit, cell=16.0):
    findings = []
    findings += check_degenerate(emit)
    findings += check_nav_support(emit)
    link_findings, oneway = check_links(emit)
    findings += link_findings
    findings += check_graph(emit)
    walk_findings, stats, _w = check_walk(emit, cell)
    findings += walk_findings
    stair_findings, tables = check_stairs(emit)
    findings += stair_findings
    stats['oneway_links'] = oneway
    stats['tris'] = len(emit.tris)
    order = {'error': 0, 'warn': 1, 'info': 2}
    findings.sort(key=lambda f: (order[f['severity']], f['code'], f['where']))
    return {'schema': 'iw7.iwz-emitcheck/1', 'emit': emit.name, 'stats': stats, 'findings': findings,
            'errors': sum(1 for f in findings if f['severity'] == 'error'),
            'warnings': sum(1 for f in findings if f['severity'] == 'warn')}, tables


def fkey(f):
    return (f['code'], f['where'])


def print_report(rep):
    print('emit %s: %d errors, %d warnings; %s' % (rep['emit'], rep['errors'], rep['warnings'],
                                                   ' '.join('%s=%s' % kv for kv in sorted(rep['stats'].items()))))
    for f in rep['findings']:
        print('  %-5s %-22s %-22s n=%-5d %s  %s' % (f['severity'].upper(), f['code'], f['where'], f['count'], f['bbox'], f['detail']))


def tri_key(t):
    return tuple(sorted(tuple(round(c, 1) for c in v) for v in t))


def diff_emits(a, b):
    """Spatial difference between two emits and what it means for re-testing."""
    ka = collections.Counter(tri_key(t) for t in a.tris)
    kb = collections.Counter(tri_key(t) for t in b.tris)
    changed = list((ka - kb).elements()) + list((kb - ka).elements())
    na = {(round(v['c'][0]), round(v['c'][1]), round(v['c'][2])): tuple(sorted(
        (round(a.areas[n]['c'][0]), round(a.areas[n]['c'][1]), round(a.areas[n]['c'][2])) for n in v['nbrs'] if n in a.areas))
        for v in a.areas.values()}
    nb = {(round(v['c'][0]), round(v['c'][1]), round(v['c'][2])): tuple(sorted(
        (round(b.areas[n]['c'][0]), round(b.areas[n]['c'][1]), round(b.areas[n]['c'][2])) for n in v['nbrs'] if n in b.areas))
        for v in b.areas.values()}
    nav_changed = [k for k in set(na) | set(nb) if na.get(k) != nb.get(k)]
    touched = collections.Counter()
    for t in changed:
        cx = sum(v[0] for v in t) / 3.0
        cy = sum(v[1] for v in t) / 3.0
        cz = sum(v[2] for v in t) / 3.0
        touched[b.where(cx, cy, cz)] += 1
    nav_touched = collections.Counter(b.where(*k) for k in nav_changed)
    layout_changed = sorted(k for k in set(a.layout) | set(b.layout) if a.layout.get(k) != b.layout.get(k))
    labels = sorted(set(touched) | set(nav_touched))
    all_labels = sorted({'stair:' + n for n, _b, _s in b.stair_boxes()} | {'zone:' + z for z in b.layout.get('zones', {})})
    ra, _ta = run_check(a)
    rb, _tb = run_check(b)
    fa = collections.Counter(fkey(f) for f in ra['findings'])
    fb = collections.Counter(fkey(f) for f in rb['findings'])
    return {'schema': 'iw7.iwz-emitdiff/1', 'a': a.name, 'b': b.name,
            'collision_tris_changed': len(changed), 'nav_cells_changed': len(nav_changed),
            'layout_keys_changed': layout_changed,
            'touched': {l: {'tris': touched.get(l, 0), 'nav': nav_touched.get(l, 0)} for l in labels},
            'retest': [l for l in labels if l != 'outside'],
            'carry_over': [l for l in all_labels if l not in labels],
            'fixed': sorted('%s @ %s' % k for k in fa if k not in fb),
            'introduced': sorted('%s @ %s' % k for k in fb if k not in fa),
            'remaining': sorted('%s @ %s' % k for k in fb if k in fa),
            'errors_a': ra['errors'], 'errors_b': rb['errors']}


def explain(emit, x, y, z):
    """What the emit says about one world position (for a recorded stuck or sunk agent)."""
    col = [(round(cz, 1), round(n, 2)) for cz, n in emit.col.column(x + EX, y + EY)]
    floors = [f for f in emit.col.floors(x + EX, y + EY)]
    navs = sorted(round(nz, 1) for nz, _k in emit.nav.columns(x, y))
    out = {'point': [x, y, z], 'where': emit.where(x, y, z), 'collision': col, 'nav': navs}
    below = [f[0] for f in floors if f[0] <= z + 2.0]
    above = [f[0] for f in floors if f[0] > z + 2.0]
    if below and z - max(below) <= 4.0:
        out['verdict'] = 'on_floor'
    elif above and (not below or z - max(below) > STEP) and min(above) - z < AGENT_H:
        out['verdict'] = 'inside_solid'
        out['note'] = ('%.0f under the walkable surface with no floor at this height: the emitted collision says an '
                       'agent cannot be here, so the game is not colliding the agent with that surface' % (min(above) - z))
    elif below:
        out['verdict'] = 'in_air'
        out['note'] = '%.0f above the floor below' % (z - max(below))
    else:
        out['verdict'] = 'no_floor'
    near = min(navs, key=lambda n: abs(n - z)) if navs else None
    out['nav_offset'] = None if near is None else round(z - near, 1)
    return out


def parse_point(text):
    p = [float(v) for v in text.replace('(', '').replace(')', '').split(',')]
    if len(p) != 3:
        raise argparse.ArgumentTypeError('point must be x,y,z')
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('check')
    p.add_argument('src')
    p.add_argument('--json')
    p.add_argument('--cell', type=float, default=16.0)
    p.add_argument('--baseline', help='earlier report JSON: only findings absent from it fail the gate')
    p = sub.add_parser('stairs')
    p.add_argument('src')
    p.add_argument('--name')
    p = sub.add_parser('diff')
    p.add_argument('a')
    p.add_argument('b')
    p.add_argument('--json')
    p = sub.add_parser('at')
    p.add_argument('src')
    p.add_argument('points', type=parse_point, nargs='+')
    p = sub.add_parser('route')
    p.add_argument('src')
    p.add_argument('start', type=parse_point)
    p.add_argument('goal', type=parse_point)
    p.add_argument('--speed', type=float, default=35.0, help='units per second (a walking zombie is about 35)')
    args = ap.parse_args(argv)

    if args.cmd == 'check':
        rep, _tables = run_check(Emit.load(args.src), args.cell)
        print_report(rep)
        if args.json:
            json.dump(rep, open(args.json, 'w', encoding='utf-8'), indent=1)
        if args.baseline:
            old = {fkey(f) for f in json.load(open(args.baseline, encoding='utf-8'))['findings']}
            new = [f for f in rep['findings'] if f['severity'] == 'error' and fkey(f) not in old]
            print('new errors versus baseline: %d' % len(new))
            return 1 if new else 0
        return 1 if rep['errors'] else 0
    if args.cmd == 'stairs':
        emit = Emit.load(args.src)
        findings, tables = check_stairs(emit)
        print_stairs(tables, args.name)
        for f in findings:
            if not args.name or f['where'] == 'stair:' + args.name:
                print('  %-5s %-22s %-18s n=%-4d %s  %s' % (f['severity'].upper(), f['code'], f['where'], f['count'], f['bbox'], f['detail']))
        return 0
    if args.cmd == 'diff':
        d = diff_emits(Emit.load(args.a), Emit.load(args.b))
        if args.json:
            json.dump(d, open(args.json, 'w', encoding='utf-8'), indent=1)
        print('%s -> %s: %d collision triangles and %d nav cells changed; layout keys changed: %s' % (
            d['a'], d['b'], d['collision_tris_changed'], d['nav_cells_changed'], ', '.join(d['layout_keys_changed']) or 'none'))
        for l, v in d['touched'].items():
            print('  touched %-24s tris=%-5d nav=%d' % (l, v['tris'], v['nav']))
        print('  re-test in game : %s' % (', '.join(d['retest']) or 'nothing'))
        print('  verdicts carry  : %s' % (', '.join(d['carry_over']) or 'none'))
        print('  errors %d -> %d' % (d['errors_a'], d['errors_b']))
        for k in ('fixed', 'introduced', 'remaining'):
            for item in d[k]:
                print('  %-10s %s' % (k, item))
        return 0
    if args.cmd == 'at':
        emit = Emit.load(args.src)
        for pt in args.points:
            print(json.dumps(explain(emit, *pt)))
        return 0
    if args.cmd == 'route':
        emit = Emit.load(args.src)
        a = emit.nav.nearest(*args.start) or emit.nav.below(*args.start)
        b = emit.nav.nearest(*args.goal) or emit.nav.below(*args.goal)
        length, path = emit.nav.route(a, b)
        if length is None:
            print('no route (start cell %s, goal cell %s)' % (a, b))
            return 1
        zs = [emit.areas[k]['c'][2] for k in path]
        print('route %.0f units over %d cells, z %.0f..%.0f, about %.0f s at %.0f u/s' % (
            length, len(path), min(zs), max(zs), length / args.speed, args.speed))
        return 0
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except NotAnEmit as exc:
        print('error: %s' % exc, file=sys.stderr)
        sys.exit(2)
