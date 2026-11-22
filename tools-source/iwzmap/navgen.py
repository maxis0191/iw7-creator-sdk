#!/usr/bin/env python3
"""Navmesh from collision triangles, with any number of floors, in the engine's own graph format (navfmt.py).

    from navgen import generate
    data, report = generate(tris, cell=32, agent_height=72, agent_radius=15, step=18, max_slope_deg=45, seeds=[...])

`tris` is anything numpy reads as (N, 3, 3) game units (collision triangles: a floor faces up, a ceiling down; the
soup does not have to be closed). `data` is a bare navgraph.bin (the resource the map compiler reads). `report` is a
dict of counts (see below); a seed with no navigation near it is reported in `report['seed_problems']`, never
silently dropped.

How it works (a Recast-style heightfield written for this format, no Recast code):
  1. every triangle is sampled with points on a lattice (4 units on walls, 5.6 on floors); the points are binned into
     columns of `res` units (8 by default) on a grid aligned to `cell`;
  2. in each column the points are merged into solid spans (gap <= res); a span is a floor when its top is an
     up-facing triangle whose slope is under `max_slope_deg`, and when the next span above is at least
     `agent_height` higher (headroom);
  3. floors of neighbouring columns are linked when they differ by at most `step`, with the headroom of both kept;
     floors within `agent_radius` of a wall, a drop or a missing link are eroded (distance measured on the links);
  4. what is left is grouped in connected floor layers; each `cell` x `cell` square holds at most one area per layer
     (a quad) when at least `min_cover` of its columns are floor, so a floor can lie over another floor;
  5. the corner heights of a quad come from a least-squares plane through its columns, then every corner is
     averaged with the corners of the same layer within one `step` at the same point, so linked quads share their
     edge exactly (the engine climbs only along such edges); links are the pairs of quads joined by linked columns;
  6. areas not connected to any seed are dropped (when seeds are given), the kd tree is built by the stock rule.

report keys: tris, tris_skipped, columns, spans, floor_spans, eroded, areas, cells, stacked_cells (squares with more
than one area), components, layers_z (rounded floor heights with their area counts), links, dropped_unreachable,
seed_problems, params. With detail=True also 'cells': one dict per area (i, j, z, corners, links).
"""
import argparse
import collections
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
        pend_p.append(p)
        pend_w.append(np.full(len(p), walk[ti]))
        count += len(p)
        if count >= chunk:
            yield np.concatenate(pend_p), np.concatenate(pend_w)
            pend_p, pend_w, count = [], [], 0
    if pend_p:
        yield np.concatenate(pend_p), np.concatenate(pend_w)
    return


def generate(tris, *, cell=32, agent_height=72, agent_radius=15, step=18, max_slope_deg=45, seeds=None,
             res=8, min_cover=0.2, detail=False, _debug=None):
    tris = np.asarray(tris, dtype=np.float64).reshape(-1, 3, 3)
    cell = float(cell)
    q = max(1, int(round(cell / float(res))))
    res = cell / q
    cos_slope = math.cos(math.radians(max_slope_deg))
    report = {'tris': int(len(tris)), 'params': {'cell': cell, 'res': res, 'agent_height': agent_height,
                                                 'agent_radius': agent_radius, 'step': step,
                                                 'max_slope_deg': max_slope_deg, 'min_cover': min_cover}}
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
    degenerate = 0
    for pts, wk in _sample(tris, res * 0.7, res * 0.5, cos_slope):
        cx = np.floor((pts[:, 0] - ox) / res).astype(np.int64)
        cy = np.floor((pts[:, 1] - oy) / res).astype(np.int64)
        keys.append(cy * W + cx)
        zs.append(pts[:, 2])
        ws.append(wk)
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    degenerate = int((np.linalg.norm(np.cross(e1, e2), axis=1) <= 1e-6).sum())
    report['tris_skipped'] = degenerate
    key = np.concatenate(keys)
    z = np.concatenate(zs)
    w = np.concatenate(ws)
    del keys, zs, ws
    order = np.lexsort((z, key))
    key, z, w = key[order], z[order], w[order]

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
    report['columns'] = int(len(np.unique(skey)))
    report['spans'] = ns
    report['floor_spans'] = int(floor.sum())

    colspans = collections.defaultdict(list)
    for i in np.flatnonzero(floor):
        colspans[int(skey[i])].append(int(i))
    fzl, zmaxl, ceill = fz.tolist(), zmax.tolist(), ceil.tolist()

    def qualifying(i, nk):
        out = []
        for j in colspans.get(nk, ()):
            if abs(fzl[i] - fzl[j]) <= step and min(ceill[i], ceill[j]) - max(zmaxl[i], zmaxl[j]) >= agent_height:
                out.append(j)
        return out

    # -------- 3. links, erosion
    alive = {int(i) for i in np.flatnonzero(floor)}
    nb8 = {}
    nb4 = {}
    boundary = []
    for i in alive:
        k = int(skey[i])
        cx, cy = k % W, k // W
        l8, l4, bnd = [], [], False
        for d, (dx, dy) in enumerate(N8):
            xx, yy = cx + dx, cy + dy
            if xx < 0 or yy < 0 or xx >= W or yy >= Hh:
                bnd = True
                continue
            js = qualifying(i, yy * W + xx)
            if js:
                l8 += js
                if d < 4:
                    l4 += js
            else:
                bnd = True
        nb8[i], nb4[i] = l8, l4
        if bnd:
            boundary.append(i)
    dist = {i: 0 for i in boundary}
    dq = collections.deque(boundary)
    while dq:
        i = dq.popleft()
        for j in nb8[i]:
            if j not in dist:
                dist[j] = dist[i] + 1
                dq.append(j)
    keep = {i for i in alive if (dist.get(i, 1 << 30) + 0.5) * res >= agent_radius}
    report['eroded'] = len(alive) - len(keep)
    if _debug is not None:
        _debug.update(dict(skey=skey, fz=fz, zmax=zmax, zmin=zmin, ceil=ceil, floor=floor, swalk=swalk, keep=keep, dist=dist, W=W, ox=ox, oy=oy, res=res))

    # -------- 4. floor layers (components), cells
    comp = {}
    ncomp = 0
    for i in sorted(keep):
        if i in comp:
            continue
        comp[i] = ncomp
        st = [i]
        while st:
            c = st.pop()
            for j in nb4[c]:
                if j in keep and j not in comp:
                    comp[j] = ncomp
                    st.append(j)
        ncomp += 1
    report['components'] = ncomp
    percell = collections.defaultdict(list)
    for i in keep:
        k = int(skey[i])
        cx, cy = k % W, k // W
        percell[(cx // q, cy // q, comp[i])].append(i)
    need = max(1, math.ceil(min_cover * q * q - 1e-9))
    nodes = []          # dicts
    span_node = {}
    for (ci, cj, cp), lst in sorted(percell.items()):
        lst.sort(key=lambda i: fzl[i])
        groups, cur = [], [lst[0]]
        for i in lst[1:]:
            if fzl[i] - fzl[cur[-1]] > 2 * step:
                groups.append(cur)
                cur = [i]
            else:
                cur.append(i)
        groups.append(cur)
        for g in groups:
            if len(g) < need:
                continue
            xy = np.array([[((int(skey[i]) % W) + 0.5) * res + ox, ((int(skey[i]) // W) + 0.5) * res + oy] for i in g])
            zz = np.array([fzl[i] for i in g])
            cxm, cym = ox + (ci + 0.5) * cell, oy + (cj + 0.5) * cell
            Amat = np.column_stack([np.ones(len(g)), xy[:, 0] - cxm, xy[:, 1] - cym])
            if len(g) >= 3 and np.linalg.matrix_rank(Amat) == 3:
                coef = np.linalg.lstsq(Amat, zz, rcond=None)[0]
            else:
                coef = np.array([zz.mean(), 0.0, 0.0])
            est = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v = coef[0] + coef[1] * sx * cell / 2 + coef[2] * sy * cell / 2
                est.append(float(min(max(v, zz.min() - res), zz.max() + res)))
            node = {'i': ci, 'j': cj, 'comp': cp, 'est': est, 'zmean': float(zz.mean()), 'n': len(g)}
            for i in g:
                span_node[i] = len(nodes)
            nodes.append(node)
    if not nodes:
        raise ValueError('no walkable area found (%d floor spans, %d after erosion)' % (len(alive), len(keep)))

    # -------- 5. shared corner heights
    vert = collections.defaultdict(list)
    for ni, nd in enumerate(nodes):
        i, j = nd['i'], nd['j']
        for c, (vi, vj) in enumerate(((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
            vert[(vi, vj, nd['comp'])].append((nd['est'][c], ni, c))
    for lst in vert.values():
        lst.sort()
        cur = [lst[0]]
        groups = []
        for item in lst[1:]:
            if item[0] - cur[-1][0] <= step:
                cur.append(item)
            else:
                groups.append(cur)
                cur = [item]
        groups.append(cur)
        for g in groups:
            m = sum(e for e, _n, _c in g) / len(g)
            for _e, ni, c in g:
                nodes[ni].setdefault('z', [None] * 4)[c] = m

    # -------- links between nodes (fine links across a cell boundary, shared edge heights equal)
    pairs = set()
    for i in keep:
        a = span_node.get(i)
        if a is None:
            continue
        for j in nb4[i]:
            b = span_node.get(j)
            if b is not None and b != a and nodes[a]['comp'] == nodes[b]['comp']:
                pairs.add((a, b))
    bycell = collections.defaultdict(list)
    for ni, nd in enumerate(nodes):
        bycell[(nd['i'], nd['j'])].append(ni)
    links = {ni: [None] * 4 for ni in range(len(nodes))}
    for a, b in pairs:
        A, B = nodes[a], nodes[b]
        off = (B['i'] - A['i'], B['j'] - A['j'])
        if off not in NBR:
            continue
        e = NBR.index(off)
        za, zb = A['z'], B['z']
        if abs(za[e] - zb[(e + 3) % 4]) <= 0.05 and abs(za[(e + 1) % 4] - zb[(e + 2) % 4]) <= 0.05:
            links[a][e] = b

    # -------- 6. seeds
    seed_problems = []
    dropped = 0
    order_nodes = sorted(range(len(nodes)), key=lambda n: (nodes[n]['i'], nodes[n]['j'], nodes[n]['zmean']))
    if seeds:
        und = collections.defaultdict(set)
        for a in range(len(nodes)):
            for b in links[a]:
                if b is not None:
                    und[a].add(b)
                    und[b].add(a)
        start = set()
        for sd in seeds:
            sx, sy, sz = (float(c) for c in sd)
            ci, cj = int(math.floor((sx - ox) / cell)), int(math.floor((sy - oy) / cell))
            best = None
            for di in (0, -1, 1):
                for dj in (0, -1, 1):
                    for ni in bycell.get((ci + di, cj + dj), ()):
                        nd = nodes[ni]
                        d = abs(nd['zmean'] - sz)
                        if d <= 48.0 and (best is None or (di == 0 and dj == 0, -d) > best[0]):
                            best = ((di == 0 and dj == 0, -d), ni)
            if best is None:
                seed_problems.append({'seed': [sx, sy, sz], 'problem': 'no navigation within one cell and 48 units'})
            else:
                start.add(best[1])
        reach = set(start)
        st = list(start)
        while st:
            c = st.pop()
            for d in und[c]:
                if d not in reach:
                    reach.add(d)
                    st.append(d)
        if not start:
            raise ValueError('none of the %d seeds is on navigation: %s' % (len(seeds), seed_problems))
        dropped = len(nodes) - len(reach)
        order_nodes = [n for n in order_nodes if n in reach]
    report['dropped_unreachable'] = dropped
    report['seed_problems'] = seed_problems

    # -------- 7. areas
    idx_of = {n: k for k, n in enumerate(order_nodes)}
    areas = []
    for n in order_nodes:
        nd = nodes[n]
        i, j = nd['i'], nd['j']
        x0, y0 = ox + i * cell, oy + j * cell
        cz = nd['z']
        corners = [(x0, y0, cz[0]), (x0 + cell, y0, cz[1]), (x0 + cell, y0 + cell, cz[2]), (x0, y0 + cell, cz[3])]
        c = (x0 + cell / 2, y0 + cell / 2, sum(cz) / 4)
        r = max(math.dist(c, p) for p in corners)
        edges = [navfmt.Edge(0, corners[e]) for e in range(4)]
        areas.append(navfmt.Area(c, r, edges))
    navfmt.layout_offsets(areas)
    nlinks = 0
    for n in order_nodes:
        a = areas[idx_of[n]]
        for e in range(4):
            b = links[n][e]
            if b is not None and b in idx_of:
                tgt = areas[idx_of[b]]
                a.edges[e].nbr = tgt.off
                a.edges[e].cost = int(math.ceil(math.dist(a.centre, tgt.centre) * 1000.0 / 72.0))
                nlinks += 1
    gr = navfmt.new_graph(areas)
    data = navfmt.wrap_resource(navfmt.write_graph(gr))
    perc = collections.Counter((nodes[n]['i'], nodes[n]['j']) for n in order_nodes)
    zc = collections.Counter(round(nodes[n]['zmean'] / 8.0) * 8 for n in order_nodes)
    report.update({'areas': len(areas), 'cells': len(perc), 'stacked_cells': sum(1 for v in perc.values() if v > 1),
                   'max_layers_in_a_cell': max(perc.values()), 'links': nlinks,
                   'layers_z': dict(sorted(zc.items())), 'bytes': len(data)})
    if detail:
        report['cells_detail'] = [{'i': nodes[n]['i'], 'j': nodes[n]['j'], 'comp': nodes[n]['comp'],
                                   'z': [round(v, 2) for v in nodes[n]['z']],
                                   'links': [None if b is None or b not in idx_of else idx_of[b] for b in links[n]]}
                                  for n in order_nodes]
    return data, report


# ------------------------------------------------------------------------------ tools
def load_triangles(path):
    if os.path.isdir(path):
        path = os.path.join(path, 'colmap.hkx')
    if path.endswith('.npy'):
        return np.load(path)
    import iwz_emitcheck
    return np.array(iwz_emitcheck.load_tris(path), dtype=np.float64)


def cells_of(path, cell=32.0):
    """{(i, j, k): z} for a navgraph (k numbers the areas of one column from the lowest)."""
    gr = navfmt.read_file(path)
    col = collections.defaultdict(list)
    for a in gr.areas:
        col[(int(math.floor(a.centre[0] / cell)), int(math.floor(a.centre[1] / cell)))].append(a.centre[2])
    return {k: sorted(v) for k, v in col.items()}


def compare(a_path, b_path, cell=32.0, zones=None, tol=24.0):
    """Cells in a and not in b (same column, no area within `tol` in z) and the reverse; by zone when given."""
    A, B = cells_of(a_path, cell), cells_of(b_path, cell)

    def only(X, Y):
        out = []
        for k, zs in X.items():
            for z in zs:
                if not any(abs(z - y) <= tol for y in Y.get(k, ())):
                    out.append((k, z))
        return out
    oa, ob = only(A, B), only(B, A)
    res = {'a_areas': sum(len(v) for v in A.values()), 'b_areas': sum(len(v) for v in B.values()),
           'only_in_a': len(oa), 'only_in_b': len(ob)}
    if zones:
        def where(k, z):
            x, y = (k[0] + 0.5) * cell, (k[1] + 0.5) * cell
            best = None
            for name, zn in zones.items():
                b = zn.get('box')
                if b and b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] - 8 <= z <= b[5] + 8:
                    vol = (b[3] - b[0]) * (b[4] - b[1])
                    if best is None or vol < best[0]:
                        best = (vol, name)
            return best[1] if best else 'outside'
        res['only_in_a_by_zone'] = dict(collections.Counter(where(k, z) for k, z in oa))
        res['only_in_b_by_zone'] = dict(collections.Counter(where(k, z) for k, z in ob))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('gen', help='triangles (colmap.hkx, an emit folder or .npy) -> navgraph.bin')
    p.add_argument('src')
    p.add_argument('-o', '--out', required=True)
    p.add_argument('--seed', action='append', default=[], help='x,y,z (repeatable)')
    p.add_argument('--cell', type=float, default=32.0)
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
