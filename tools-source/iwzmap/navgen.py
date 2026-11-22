#!/usr/bin/env python3
"""Navmesh from collision triangles, with any number of floors and free-form geometry, in the engine's own graph format
(navfmt.py). Areas are convex polygons of 3 to 14 corners that follow the real edge of the walkable surface; every link is
one exactly shared edge with equal corner heights. Details and measurements: docs/NAVMESH.md.

    from navgen import generate
    data, report = generate(tris, cell=16, agent_height=72, step=18, max_slope_deg=45, edge_margin=8, seeds=[...])

`tris` is anything numpy reads as (N, 3, 3) game units (collision triangles: a floor faces up, a ceiling down, solids
closed). `data` is a bare navgraph.bin (the resource the map compiler reads). `report` is a dict of counts; a seed with no
navigation near it is reported in `report['seed_problems']`, never silently dropped. `boundary_gap(tris, data)` measures
the distance from the nav edge to the collision wall.

Pipeline: sample the triangles into 8-unit columns; spans, floors (slope, headroom, not inside a closed solid); distance of
every floor span to the edge of its surface along the links; lattice of `cell` units with one node per floor level;
marching squares at `edge_margin` per cell and level; greedy convex merge up to `max_edges` corners, planar within
`plane_tol`; links by shared vertices; seeds drop unreachable areas; kd tree by the stock rule.
"""
import argparse
import collections
import heapq
import json
import math
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import navfmt  # noqa: E402

NBR = ((0, -1), (1, 0), (0, 1), (-1, 0))     # edge e (corner e -> e + 1) faces this cell offset, as mapgen.nav_graph
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


# ------------------------------------------------------------------------------ sampling
def _sample(tris, h_floor, h_wall, cos_slope, chunk=1_500_000):
    """Yield (points (M, 3), walkable flags (M,)) for the triangles, a lattice of about h units on each."""
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    e3 = tris[:, 2] - tris[:, 1]
    n = np.cross(e1, e2)
    area2 = np.linalg.norm(n, axis=1)
    ok = area2 > 1e-6
    nz = np.where(ok, n[:, 2] / np.maximum(area2, 1e-12), 0.0)
    walk = nz >= cos_slope
    # class: 3 walkable up-facing, 2 up-facing too steep, 1 near vertical, 0 facing down
    cls_t = np.where(walk, 3, np.where(nz > 0.1, 2, np.where(nz >= -0.1, 1, 0))).astype(np.int8)
    # the longest edge is the base a -> b; c is the apex
    l = np.stack([np.linalg.norm(e1, axis=1), np.linalg.norm(e3, axis=1), np.linalg.norm(e2, axis=1)], 1)
    which = l.argmax(1)
    A = np.where((which == 0)[:, None], tris[:, 0], np.where((which == 1)[:, None], tris[:, 1], tris[:, 2]))
    B = np.where((which == 0)[:, None], tris[:, 1], np.where((which == 1)[:, None], tris[:, 2], tris[:, 0]))
    C = np.where((which == 0)[:, None], tris[:, 2], np.where((which == 1)[:, None], tris[:, 0], tris[:, 1]))
    base = l.max(1)
    hgt = np.where(base > 0, area2 / np.maximum(base, 1e-9), 0.0)
    hs = np.where(walk, h_floor, h_wall)
    ks = np.maximum(1, np.ceil(base / hs)).astype(np.int64)
    kt = np.maximum(1, np.ceil(hgt / hs)).astype(np.int64)
    cost = (ks + 1) * (kt + 1)
    order = np.argsort(cost)
    pend_p, pend_w, count = [], [], 0
    for ti in order:
        if not ok[ti]:
            continue
        s = np.arange(ks[ti] + 1) / ks[ti]
        t = np.arange(kt[ti] + 1) / kt[ti]
        S, T = np.meshgrid(s, t)
        u = (S * (1.0 - T)).ravel()
        v = T.ravel()
        p = A[ti] + u[:, None] * (B[ti] - A[ti]) + v[:, None] * (C[ti] - A[ti])
        if walk[ti]:
            # pull the points of a floor triangle 0.6 units inside it, so that the row of points on its border does not
            # put a floor column on the far side of the edge (the slab edge, a doorway, a ledge)
            cen = (A[ti] + B[ti] + C[ti]) / 3.0
            vec = p - cen
            dn = np.maximum(np.linalg.norm(vec, axis=1), 1e-9)
            p = cen + vec * np.maximum(0.0, 1.0 - 0.6 / dn)[:, None]
        pend_p.append(p)
        pend_w.append(np.full(len(p), cls_t[ti]))
        count += len(p)
        if count >= chunk:
            yield np.concatenate(pend_p), np.concatenate(pend_w)
            pend_p, pend_w, count = [], [], 0
    if pend_p:
        yield np.concatenate(pend_p), np.concatenate(pend_w)
    return


def _plane(pts):
    """Least squares z = a x + b y + c through (n, 3) points; returns (a, b, c, max residual)."""
    p = np.asarray(pts, dtype=np.float64)
    if len(p) < 3:
        return 0.0, 0.0, float(p[:, 2].mean()), 0.0
    x0, y0 = p[:, 0].mean(), p[:, 1].mean()
    A = np.column_stack([p[:, 0] - x0, p[:, 1] - y0, np.ones(len(p))])
    if np.linalg.matrix_rank(A, tol=1e-6) < 3:
        return 0.0, 0.0, float(p[:, 2].mean()), float(np.abs(p[:, 2] - p[:, 2].mean()).max())
    c = np.linalg.lstsq(A, p[:, 2], rcond=None)[0]
    res = float(np.abs(A @ c - p[:, 2]).max())
    return float(c[0]), float(c[1]), float(c[2] - c[0] * x0 - c[1] * y0), res


class _Mesh:
    """Convex polygons over shared vertices; directed edge (u, v) belongs to exactly one polygon, its neighbour is
    the owner of (v, u)."""

    def __init__(self):
        self.X, self.Y, self.Z = [], [], []
        self.vkey = {}
        self.poly = {}            # id -> vertex cycle (counter-clockwise)
        self.owner = {}           # directed atomic edge -> polygon id
        self.nid = 0

    def vertex(self, key, x, y, z):
        v = self.vkey.get(key)
        if v is None:
            v = self.vkey[key] = len(self.X)
            self.X.append(x)
            self.Y.append(y)
            self.Z.append(z)
        return v

    def add(self, cyc):
        pid = self.nid
        self.nid += 1
        self.poly[pid] = cyc
        n = len(cyc)
        for k in range(n):
            self.owner[(cyc[k], cyc[(k + 1) % n])] = pid
        return pid

    def area2(self, cyc):
        s = 0.0
        n = len(cyc)
        for k in range(n):
            a, b = cyc[k], cyc[(k + 1) % n]
            s += self.X[a] * self.Y[b] - self.X[b] * self.Y[a]
        return s

    def collinear(self, a, b, c, tol=0.6):
        """b lies on the segment a-c within tol units in xy and z (a vertex that adds no corner)."""
        ax, ay, az = self.X[a], self.Y[a], self.Z[a]
        cx, cy, cz = self.X[c], self.Y[c], self.Z[c]
        dx, dy = cx - ax, cy - ay
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            return True
        t = ((self.X[b] - ax) * dx + (self.Y[b] - ay) * dy) / (ln * ln)
        if t < -1e-6 or t > 1 + 1e-6:
            return False
        off = abs((self.X[b] - ax) * dy - (self.Y[b] - ay) * dx) / ln
        zc = az + (cz - az) * t
        return off <= tol and abs(self.Z[b] - zc) <= tol

    def corners(self, cyc, own=None):
        """The polygon without the vertices that sit in the middle of one edge: the edges before and after have the
        same neighbour and the three points are collinear. Returns (kept vertices, their indices in cyc)."""
        n = len(cyc)
        if own is None:
            own = lambda u, v: self.owner.get((v, u))     # noqa: E731
        nb = [own(cyc[k], cyc[(k + 1) % n]) for k in range(n)]
        keep = []
        for k in range(n):
            prev = (k - 1) % n
            # a vertex between two edges of the same neighbour is merged when it is 0.6 off the line (both sides of a
            # link decide alike); on an open boundary only when it is exactly on the line
            if nb[prev] == nb[k] and self.collinear(cyc[prev], cyc[k], cyc[(k + 1) % n],
                                                     0.6 if nb[k] is not None else 0.05):
                continue
            keep.append(k)
        if len(keep) < 3:
            return list(cyc), list(range(n))
        return [cyc[k] for k in keep], keep

    def convex(self, cyc, eps=1e-3):
        n = len(cyc)
        for k in range(n):
            a, b, c = cyc[k], cyc[(k + 1) % n], cyc[(k + 2) % n]
            cr = (self.X[b] - self.X[a]) * (self.Y[c] - self.Y[b]) - (self.Y[b] - self.Y[a]) * (self.X[c] - self.X[b])
            if cr < -eps:
                return False
        return True

    def try_merge(self, a, b, max_edges, plane_tol):
        """The cycle of a and b joined along their shared edges, or None when that is not one simple convex, planar
        polygon with at most max_edges corners. Returns (cycle, shared edges, corner count)."""
        A, B = self.poly[a], self.poly[b]
        n = len(A)
        sh = [self.owner.get((A[(k + 1) % n], A[k])) == b for k in range(n)]
        cnt = sum(sh)
        if cnt == 0 or cnt == n:
            return None
        starts = [k for k in range(n) if sh[k] and not sh[k - 1]]
        if len(starts) != 1:
            return None
        s = starts[0]
        vs, ve = A[s], A[(s + cnt) % n]
        m = len(B)
        if vs not in B or ve not in B:
            return None
        jb = B.index(vs)
        rest = []
        k = (jb + 1) % m
        guard = 0
        while B[k] != ve:
            rest.append(B[k])
            k = (k + 1) % m
            guard += 1
            if guard > m:
                return None
        path_a = [A[(s + cnt + t) % n] for t in range(n - cnt + 1)]      # ve ... vs along the free side of a
        cyc = path_a + rest
        if len(set(cyc)) != len(cyc) or not self.convex(cyc):
            return None
        if _plane([(self.X[v], self.Y[v], self.Z[v]) for v in cyc])[3] > plane_tol:
            return None
        shared = {(A[(s + t) % n], A[(s + t + 1) % n]) for t in range(cnt)}
        shared |= {(v, u) for (u, v) in shared}

        def own(u, v):
            if (u, v) in shared:
                return None
            return self.owner.get((v, u))
        corners, _ = self.corners(cyc, own=own)
        if len(corners) > max_edges:
            return None
        return cyc, shared, len(corners)

    def commit(self, a, b, cyc, shared):
        for e in shared:
            self.owner.pop(e, None)
        for k in range(len(cyc)):
            self.owner[(cyc[k], cyc[(k + 1) % len(cyc)])] = a
        self.poly[a] = cyc
        del self.poly[b]

    def merge_all(self, max_edges, plane_tol):
        merged = 0
        for pid in sorted(self.poly):
            while pid in self.poly:
                cyc = self.poly[pid]
                n = len(cyc)
                cand = {self.owner.get((cyc[(k + 1) % n], cyc[k])) for k in range(n)} - {None, pid}
                best = None
                for qd in sorted(cand):
                    r = self.try_merge(pid, qd, max_edges, plane_tol)
                    if r is None:
                        continue
                    score = (r[2], len(r[0]))
                    if best is None or score < best[0]:
                        best = (score, qd, r)
                if best is None:
                    break
                self.commit(pid, best[1], best[2][0], best[2][1])
                merged += 1
        return merged


def generate(tris, *, cell=16, agent_height=72, agent_radius=15, step=18, max_slope_deg=45, seeds=None,
             res=8, max_edges=14, plane_tol=1.5, edge_margin=8.0, solid_check=True, detail=False, _debug=None):
    tris = np.asarray(tris, dtype=np.float64).reshape(-1, 3, 3)
    cell = float(cell)
    res = cell / 2.0          # a lattice cell is two columns wide: every column touches one lattice vertex
    cos_slope = math.cos(math.radians(max_slope_deg))
    report = {'tris': int(len(tris)), 'params': {'cell': cell, 'res': res, 'agent_height': agent_height,
                                                 'agent_radius': agent_radius, 'step': step,
                                                 'max_slope_deg': max_slope_deg, 'max_edges': max_edges, 'edge_margin': edge_margin,
                                                 'plane_tol': plane_tol}}
    if len(tris) == 0:
        raise ValueError('no triangles')
    mn = tris.reshape(-1, 3).min(0)
    ox = math.floor(mn[0] / cell) * cell
    oy = math.floor(mn[1] / cell) * cell
    mxp = tris.reshape(-1, 3).max(0)
    W = int(math.floor((mxp[0] - ox) / res)) + 2
    Hh = int(math.floor((mxp[1] - oy) / res)) + 2

    # -------- 1. points to columns
    keys, zs, ws = [], [], []
    wall_k, wall_p = [], []
    for pts, cl in _sample(tris, res * 0.7, res * 0.5, cos_slope):
        wk = cl == 3
        cx = np.floor((pts[:, 0] - ox) / res).astype(np.int64)
        cy = np.floor((pts[:, 1] - oy) / res).astype(np.int64)
        keys.append(cy * W + cx)
        zs.append(pts[:, 2])
        ws.append(cl)
        wall_k.append((cy * W + cx)[~wk])
        wall_p.append(pts[~wk])
    wall_k = np.concatenate(wall_k)
    wall_p = np.concatenate(wall_p)
    wo = np.argsort(wall_k, kind='stable')
    wall_k, wall_p = wall_k[wo], wall_p[wo]
    wall_lo = {}
    if len(wall_k):
        ukeys, ustart = np.unique(wall_k, return_index=True)
        uend = np.append(ustart[1:], len(wall_k))
        wall_lo = {int(a): (int(b), int(c)) for a, b, c in zip(ukeys, ustart, uend)}
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    report['tris_skipped'] = int((np.linalg.norm(np.cross(e1, e2), axis=1) <= 1e-6).sum())
    key = np.concatenate(keys)
    z = np.concatenate(zs)
    w = np.concatenate(ws)
    del keys, zs, ws
    order = np.lexsort((z, key))
    key, z, cls = key[order], z[order], w[order]
    w = cls == 3

    # -------- 2. spans
    new = np.ones(len(key), bool)
    new[1:] = (key[1:] != key[:-1]) | (z[1:] - z[:-1] > res)
    sid = np.cumsum(new) - 1
    ns = int(sid[-1]) + 1
    first = np.flatnonzero(new)
    last = np.append(first[1:], len(key)) - 1
    skey = key[first]
    zmin = z[first]
    zmax = z[last]
    wz = np.where(w, z, -np.inf)
    wtop = np.maximum.reduceat(wz, first)          # highest walkable point of each span
    # walkable when the highest walkable point is within one step of the span top (a riser or a curb above a
    # tread does not make the column a wall); the surface height is the mean of the walkable points near that top
    swalk = wtop >= zmax - step
    grp = w & (z >= wtop[sid] - 0.5 * res)
    cnt = np.bincount(sid, weights=grp.astype(np.float64), minlength=ns)
    fz = np.where(cnt > 0, np.bincount(sid, weights=np.where(grp, z, 0.0), minlength=ns) / np.maximum(cnt, 1), zmax)
    zmax = np.where(swalk, wtop, zmax)             # headroom is counted from the walkable top
    nxt_same = np.zeros(ns, bool)
    nxt_same[:-1] = skey[1:] == skey[:-1]
    ceil = np.full(ns, np.inf)
    ceil[:-1] = np.where(nxt_same[:-1], zmin[1:], np.inf)
    floor = swalk & (ceil - zmax >= agent_height)
    if solid_check:
        # the next surface above must be seen from below (a ceiling or a wall): when it faces up, the floor lies
        # inside a closed solid (under a pillar, inside a crate) and is not walkable
        lowcls = cls[first]
        inside = np.zeros(ns, bool)
        inside[:-1] = nxt_same[:-1] & (lowcls[1:] >= 2)
        report['inside_solid'] = int((floor & inside).sum())
        floor &= ~inside
    report['columns'] = int(len(np.unique(skey)))
    report['spans'] = ns
    report['floor_spans'] = int(floor.sum())

    colspans = collections.defaultdict(list)
    for i in np.flatnonzero(floor):
        colspans[int(skey[i])].append(int(i))
    fzl, zmaxl, ceill = fz.tolist(), zmax.tolist(), ceil.tolist()

    def qualifying(i, nk):
        return [j for j in colspans.get(nk, ())
                if abs(fzl[i] - fzl[j]) <= step and min(ceill[i], ceill[j]) - max(zmaxl[i], zmaxl[j]) >= agent_height]

    # -------- 3. distance of every floor span to the edge of its walkable surface (chamfer metric on the links)
    alive = sorted(int(i) for i in np.flatnonzero(floor))
    D8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    nb8 = {}
    seedd = {}
    for i in alive:
        k = int(skey[i])
        cx, cy = k % W, k // W
        lst = []
        miss4 = miss8 = False
        for d, (dx, dy) in enumerate(D8):
            xx, yy = cx + dx, cy + dy
            js = qualifying(i, yy * W + xx) if 0 <= xx < W and 0 <= yy < Hh else []
            if js:
                lst += [(j, res if d < 4 else res * math.sqrt(2.0)) for j in js]
            elif d < 4:
                miss4 = True
            else:
                miss8 = True
        nb8[i] = lst
        if miss4 or miss8:
            # the edge of the surface: the true distance to the wall in the neighbouring columns when there is one
            # (a wall column holds the wall somewhere inside it), else the half column of an open drop
            best = 0.5 * res if miss4 else 0.5 * res * math.sqrt(2.0)
            px, py = ox + (cx + 0.5) * res, oy + (cy + 0.5) * res
            lo, hi = fzl[i] + step, fzl[i] + agent_height
            wd = None
            for dx, dy in D8 + ((0, 0),):
                rng = wall_lo.get((cy + dy) * W + cx + dx)
                if rng is None:
                    continue
                seg = wall_p[rng[0]:rng[1]]
                seg = seg[(seg[:, 2] >= lo) & (seg[:, 2] <= hi)]
                if len(seg):
                    d = float(np.sqrt(((seg[:, 0] - px) ** 2 + (seg[:, 1] - py) ** 2).min()))
                    wd = d if wd is None else min(wd, d)
            seedd[i] = wd if wd is not None else best
    dist = dict(seedd)
    heap = [(d, i) for i, d in seedd.items()]
    heapq.heapify(heap)
    reach_cap = edge_margin + 2 * res
    while heap:
        d, i = heapq.heappop(heap)
        if d > dist.get(i, 1e18) or d > reach_cap:
            continue
        for j, wgt in nb8[i]:
            nd = d + wgt
            if nd < dist.get(j, 1e18):
                dist[j] = nd
                heapq.heappush(heap, (nd, j))
    phi_span = {i: min(dist.get(i, reach_cap + res), reach_cap + res) for i in alive}

    # -------- 4. lattice vertices with one node per floor level; marching squares per cell and level
    # a column touches exactly one lattice vertex (the cell is two columns wide): the corner of its own cell
    vspans = collections.defaultdict(list)
    for i in alive:
        k = int(skey[i])
        cx, cy = k % W, k // W
        vspans[(cx // 2 + cx % 2, cy // 2 + cy % 2)].append(i)
    nid = [0]
    vnodes = collections.defaultdict(list)            # (I, J) -> [(z, phi, node id)]
    for (vi, vj), lst in vspans.items():
        lst.sort(key=lambda i: fzl[i])
        groups, cur = [], [lst[0]]
        for i in lst[1:]:
            if fzl[i] - fzl[cur[-1]] > step:
                groups.append(cur)
                cur = [i]
            else:
                cur.append(i)
        groups.append(cur)
        for g in groups:
            zz = sum(fzl[i] for i in g) / len(g)
            ph = (sum(phi_span[i] for i in g) + max(0, 4 - len(g)) * (-0.5 * res)) / 4.0
            nid[0] += 1
            vnodes[(vi, vj)].append((zz, ph, nid[0]))

    def node_at(vi, vj, zref):
        best = None
        for nd in vnodes.get((vi, vj), ()):
            dz = abs(nd[0] - zref)
            if dz <= step and (best is None or dz < best[0]):
                best = (dz, nd)
        return best[1] if best else None

    mesh = _Mesh()
    r = float(edge_margin)

    def vert(vi, vj, nd):
        return mesh.vertex(('v', vi, vj, nd[2]), ox + vi * cell, oy + vj * cell, nd[0])

    cells = set()
    for (vi, vj) in vnodes:
        for di in (0, -1):
            for dj in (0, -1):
                cells.add((vi + di, vj + dj))
    for (ci, cj) in sorted(cells):
        corners = [(ci, cj), (ci + 1, cj), (ci + 1, cj + 1), (ci, cj + 1)]
        cand = []
        for k, (vi, vj) in enumerate(corners):
            for nd in vnodes.get((vi, vj), ()):
                cand.append((nd[0], k, nd))
        if not cand:
            continue
        cand.sort(key=lambda t: t[0])
        levels, cur = [], [cand[0]]
        for t in cand[1:]:
            if t[0] - cur[-1][0] > step:
                levels.append(cur)
                cur = [t]
            else:
                cur.append(t)
        levels.append(cur)
        for lv in levels:
            at = {}
            for _z, k, nd in lv:
                if k not in at or nd[1] > at[k][1]:
                    at[k] = nd
            if not any(nd[1] >= r for nd in at.values()):
                continue
            zref = sum(nd[0] for nd in at.values()) / len(at)
            cyc = []
            for k in range(4):
                kb = (k + 1) % 4
                a, b = at.get(k), at.get(kb)
                ia = a is not None and a[1] >= r
                ib = b is not None and b[1] >= r
                if ia:
                    cyc.append(vert(corners[k][0], corners[k][1], a))
                if ia != ib:
                    inn, ink, out_v = (a, k, corners[kb]) if ia else (b, kb, corners[k])
                    inv = corners[ink]
                    outn = node_at(out_v[0], out_v[1], inn[0])
                    pb = outn[1] if outn is not None else -0.5 * res
                    pa = inn[1]
                    t = (pa - r) / (pa - pb) if pa != pb else 0.0
                    if t < 0.03:
                        cyc.append(vert(inv[0], inv[1], inn))
                    else:
                        ek = ('x', inn[2], out_v[0], out_v[1])
                        cyc.append(mesh.vertex(ek, ox + (inv[0] + (out_v[0] - inv[0]) * t) * cell,
                                               oy + (inv[1] + (out_v[1] - inv[1]) * t) * cell, inn[0]))
            dedup = [v for kk, v in enumerate(cyc) if v != cyc[kk - 1]]
            if len(dedup) < 3 or abs(mesh.area2(dedup)) < 8.0:
                continue
            mesh.add(dedup)
    report['polygons_before_merge'] = len(mesh.poly)
    if not mesh.poly:
        raise ValueError('no walkable area found (%d floor spans)' % len(alive))
    report['eroded'] = sum(1 for i in alive if phi_span[i] < r)

    # -------- 5. merge into convex polygons
    report['merges'] = mesh.merge_all(max_edges, plane_tol)

    # -------- 6. final polygons
    info = {}
    for pid, cyc in mesh.poly.items():
        corners, keep = mesh.corners(cyc)
        a2 = mesh.area2(corners)
        if abs(a2) < 1e-6:
            continue
        m = len(corners)
        cxm = cym = 0.0
        for k in range(m):
            a, b = corners[k], corners[(k + 1) % m]
            cr = mesh.X[a] * mesh.Y[b] - mesh.X[b] * mesh.Y[a]
            cxm += (mesh.X[a] + mesh.X[b]) * cr
            cym += (mesh.Y[a] + mesh.Y[b]) * cr
        cxm /= 3 * a2
        cym /= 3 * a2
        pl = _plane([(mesh.X[v], mesh.Y[v], mesh.Z[v]) for v in cyc])
        n = len(cyc)
        zs_ = [mesh.Z[v] for v in cyc]
        zc_ = min(max(pl[0] * cxm + pl[1] * cym + pl[2], min(zs_)), max(zs_))     # a thin polygon gives a wild plane
        info[pid] = {'pts': [(mesh.X[v], mesh.Y[v], mesh.Z[v]) for v in corners],
                     'c': (cxm, cym, zc_), 'plane': pl, 'zr': (min(zs_), max(zs_)),
                     'nbr': [mesh.owner.get((cyc[(kk + 1) % n], cyc[kk])) for kk in keep]}
    order = sorted(info, key=lambda p: (round(info[p]['c'][0], 3), round(info[p]['c'][1], 3), round(info[p]['c'][2], 3)))
    seed_problems = []
    dropped = 0
    if seeds:
        und = collections.defaultdict(set)
        for pid in info:
            for b in info[pid]['nbr']:
                if b is not None and b in info:
                    und[pid].add(b)
                    und[b].add(pid)
        grid = collections.defaultdict(list)
        for pid in info:
            xs = [p[0] for p in info[pid]['pts']]
            ys = [p[1] for p in info[pid]['pts']]
            for gx in range(int(min(xs) // 64), int(max(xs) // 64) + 1):
                for gy in range(int(min(ys) // 64), int(max(ys) // 64) + 1):
                    grid[(gx, gy)].append(pid)
        start = set()
        for sd in seeds:
            sx, sy, sz = (float(c) for c in sd)
            best = None
            for pid in grid.get((int(sx // 64), int(sy // 64)), ()):
                a, b, c = info[pid]['plane'][:3]
                if navfmt.point_in_poly(sx, sy, info[pid]['pts']):
                    dz = abs(min(max(a * sx + b * sy + c, info[pid]['zr'][0]), info[pid]['zr'][1]) - sz)
                    if dz <= 48.0 and (best is None or dz < best[0]):
                        best = (dz, pid)
            if best is None:
                seed_problems.append({'seed': [sx, sy, sz], 'problem': 'no navigation at the seed within 48 units'})
            else:
                start.add(best[1])
        if not start:
            raise ValueError('none of the %d seeds is on navigation: %s' % (len(seeds), seed_problems))
        reach = set(start)
        st = list(start)
        while st:
            c = st.pop()
            for d in und[c]:
                if d not in reach:
                    reach.add(d)
                    st.append(d)
        dropped = len([p for p in order if p not in reach])
        order = [p for p in order if p in reach]
    report['dropped_unreachable'] = dropped
    report['seed_problems'] = seed_problems

    # -------- 7. areas and links
    idx_of = {p: k for k, p in enumerate(order)}
    areas = []
    for p in order:
        pts = info[p]['pts']
        c = info[p]['c']
        areas.append(navfmt.Area(c, max(math.dist(c, pt) for pt in pts), [navfmt.Edge(0, pt) for pt in pts]))
    navfmt.layout_offsets(areas)
    nlinks = 0
    for p in order:
        a = areas[idx_of[p]]
        for e, b in enumerate(info[p]['nbr']):
            if b is not None and b in idx_of:
                tgt = areas[idx_of[b]]
                a.edges[e].nbr = tgt.off
                a.edges[e].cost = int(math.ceil(math.dist(a.centre, tgt.centre) * 1000.0 / 72.0))
                nlinks += 1
    gr = navfmt.new_graph(areas)
    data = navfmt.wrap_resource(navfmt.write_graph(gr))
    ec = collections.Counter(len(a.edges) for a in areas)
    zc = collections.Counter(round(a.centre[2] / 8.0) * 8 for a in areas)
    foot = collections.defaultdict(list)
    for a in areas:
        foot[(int(a.centre[0] // 32), int(a.centre[1] // 32))].append(a.centre[2])
    report.update({'areas': len(areas), 'links': nlinks, 'edge_count_hist': dict(sorted(ec.items())),
                   'stacked_squares_32': sum(1 for v in foot.values() if max(v) - min(v) >= agent_height),
                   'layers_z': dict(sorted(zc.items())), 'bytes': len(data)})
    if _debug is not None:
        _debug.update(dict(mesh=mesh, info=info, order=order, areas=areas, ox=ox, oy=oy, phi=phi_span, skey=skey, fz=fz, W=W, res=res, vnodes=vnodes))
    return data, report



# ------------------------------------------------------------------------------ measurements
def boundary_gap(tris, data, *, agent_height=72, step=18, max_slope_deg=45, reach=48.0, spacing=4.0):
    """How far the navigation edge stays from the collision wall: samples every `spacing` units along each area edge
    that has no neighbour, looks straight out from the edge (the outward normal) and measures the distance to the first
    wall point within 3 units of that line (a point of a triangle steeper than max_slope_deg whose height lies in the
    body of an agent standing there). Samples with no wall within `reach` are drops, not walls, and are only counted.
    Returns a dict: samples, near_wall, open, max, mean, p95."""
    tris = np.asarray(tris, dtype=np.float64).reshape(-1, 3, 3)
    cos_slope = math.cos(math.radians(max_slope_deg))
    wall = [pts[cl != 3] for pts, cl in _sample(tris, 4.0, 4.0, cos_slope)]
    wall = np.concatenate(wall) if wall else np.zeros((0, 3))
    g = 16.0
    cx_all = np.floor(wall[:, 0] / g).astype(np.int64)
    cy_all = np.floor(wall[:, 1] / g).astype(np.int64)
    order = np.lexsort((cy_all, cx_all))
    wall, cx_all, cy_all = wall[order], cx_all[order], cy_all[order]
    grid = {}
    if len(wall):
        ck = cx_all * 100003 + cy_all
        uk, us = np.unique(ck, return_index=True)
        ue = np.append(us[1:], len(ck))
        for k, s, e in zip(uk.tolist(), us.tolist(), ue.tolist()):
            grid[k] = wall[s:e]
    gs = navfmt.find_graph(data)
    gr, _n = navfmt.parse_graph(data[gs:])
    dists = []
    far = []
    open_n = 0
    rr = int(reach // g) + 1
    for a in gr.areas:
        n = len(a.edges)
        for e in range(n):
            if a.edges[e].cost:
                continue
            p, q = a.edges[e].corner, a.edges[(e + 1) % n].corner
            ln = math.dist(p[:2], q[:2])
            if ln < 1e-6:
                continue
            tx, ty = (q[0] - p[0]) / ln, (q[1] - p[1]) / ln
            nx, ny = ty, -tx                                   # outward for counter-clockwise corners
            k = max(1, int(ln // spacing))
            for s in range(k + 1):
                x, y, z = (p[i] + (q[i] - p[i]) * s / k for i in range(3))
                cx, cy = int(x // g), int(y // g)
                cand = [grid[kk] for kk in ((ix * 100003 + iy) for ix in range(cx - rr, cx + rr + 1)
                                            for iy in range(cy - rr, cy + rr + 1)) if kk in grid]
                best = None
                if cand:
                    w = np.concatenate(cand)
                    w = w[(w[:, 2] >= z + step) & (w[:, 2] <= z + agent_height)]
                    if len(w):
                        al = (w[:, 0] - x) * nx + (w[:, 1] - y) * ny
                        pe = np.abs((w[:, 0] - x) * tx + (w[:, 1] - y) * ty)
                        ok = (al >= 0.0) & (al <= reach) & (pe <= 3.0)
                        if ok.any():
                            best = float(al[ok].min())
                if best is None:
                    open_n += 1
                else:
                    dists.append(best)
                    if best > 20.0:
                        far.append((round(x, 1), round(y, 1), round(z, 1), round(best, 1)))
    d = np.array(dists) if dists else np.zeros(1)
    return {'samples': len(dists) + open_n, 'near_wall': len(dists), 'open': open_n, 'max': round(float(d.max()), 2),
            'mean': round(float(d.mean()), 2), 'p95': round(float(np.percentile(d, 95)), 2),
            'beyond_20': len(far), 'far_examples': far[:5]}


# ------------------------------------------------------------------------------ tools
def load_triangles(path):
    if os.path.isdir(path):
        path = os.path.join(path, 'colmap.hkx')
    if path.endswith('.npy'):
        return np.load(path)
    import iwz_emitcheck
    return np.array(iwz_emitcheck.load_tris(path), dtype=np.float64)


def compare(a_path, b_path, step=16.0, zones=None, tol=24.0):
    """Floor area of navgraph a that graph b does not cover and the reverse, in 16-unit samples (area = count * step^2),
    by zone when a layout's zones are given. A sample is covered when b has an area over the same x, y at a height
    within `tol`."""
    import iwz_emitcheck as ec
    A, B = ec.load_nav(a_path), ec.load_nav(b_path)
    NA, NB = ec.Nav(A), ec.Nav(B)

    def samples(areas, nav):
        for k, ar in areas.items():
            x0, x1, y0, y1 = ar['bb'] if 'bb' in ar else (None,) * 4
            xs = [c[0] for c in ar['corners']]
            ys = [c[1] for c in ar['corners']]
            gx0, gx1, gy0, gy1 = min(xs), max(xs), min(ys), max(ys)
            x = (math.floor(gx0 / step) + 0.5) * step
            while x < gx1:
                y = (math.floor(gy0 / step) + 0.5) * step
                while y < gy1:
                    if ec._inside(x, y, ar['corners']) if len(ar['corners']) != 4 else True:
                        if gx0 <= x <= gx1 and gy0 <= y <= gy1:
                            yield x, y, nav.z_at(k, x, y)
                    y += step
                x += step

    def only(src, srcnav, dst):
        out = []
        for x, y, z in samples(src, srcnav):
            if dst.at(x, y, z, tol) is None:
                out.append((x, y, z))
        return out
    oa, ob = only(A, NA, NB), only(B, NB, NA)
    res = {'a_areas': len(A), 'b_areas': len(B), 'a_only_area': int(len(oa) * step * step),
           'b_only_area': int(len(ob) * step * step),
           'a_total_area': int(sum(1 for _ in samples(A, NA)) * step * step)}
    if zones:
        def where(x, y, z):
            best = None
            for name, zn in zones.items():
                b = zn.get('box')
                if b and b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] - 8 <= z <= b[5] + 8:
                    vol = (b[3] - b[0]) * (b[4] - b[1])
                    if best is None or vol < best[0]:
                        best = (vol, name)
            return best[1] if best else 'outside'
        res['a_only_by_zone'] = {k: v * int(step * step) for k, v in collections.Counter(where(*p) for p in oa).items()}
        res['b_only_by_zone'] = {k: v * int(step * step) for k, v in collections.Counter(where(*p) for p in ob).items()}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('gen', help='triangles (colmap.hkx, an emit folder or .npy) -> navgraph.bin')
    p.add_argument('src')
    p.add_argument('-o', '--out', required=True)
    p.add_argument('--seed', action='append', default=[], help='x,y,z (repeatable)')
    p.add_argument('--cell', type=float, default=16.0)
    p.add_argument('--res', type=float, default=8.0)
    p.add_argument('--radius', type=float, default=15.0)
    p.add_argument('--json', help='write the report (with the cells) here')
    p = sub.add_parser('compare', help='cell coverage of two navgraphs')
    p.add_argument('a')
    p.add_argument('b')
    p.add_argument('--layout', help='layout.json for the zone names')
    args = ap.parse_args(argv)
    if args.cmd == 'gen':
        seeds = [tuple(float(c) for c in s.split(',')) for s in args.seed]
        data, rep = generate(load_triangles(args.src), cell=args.cell, res=args.res, agent_radius=args.radius,
                             seeds=seeds or None, detail=bool(args.json))
        open(args.out, 'wb').write(data)
        if args.json:
            json.dump(rep, open(args.json, 'w'), indent=1)
        rep.pop('cells_detail', None)
        print(json.dumps(rep, indent=1))
        return 0
    zones = json.load(open(args.layout, encoding='utf-8')).get('zones') if args.layout else None
    print(json.dumps(compare(args.a, args.b, zones=zones), indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
