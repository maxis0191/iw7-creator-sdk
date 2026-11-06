import os
"""Generate iwzcompile sources (world.bin, colmap.hkx, navgraph.bin, ents.txt) from a box-based map description."""
import json, math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hkcm_write

HAVOK_SCALE = 1.0 / 32.0


def pack_unit(v, w=3):
    q = [max(0, min(1023, int(round((c + 1.0) * 511.5)))) for c in v]
    return q[0] | q[1] << 10 | q[2] << 20 | w << 30


class Mesh:
    def __init__(self):
        self.materials = []
        self.by_mat = {}      # material -> (verts, indices)
        self.col = []         # collision triangles (game units)

    def mat(self, name):
        if name not in self.by_mat:
            self.materials.append(name); self.by_mat[name] = ([], [])
        return self.by_mat[name]

    def quad(self, material, p0, p1, p2, p3, normal, tangent, lm, uv_scale=128.0, collide=True):
        """p0..p3 counter-clockwise seen from the normal side."""
        verts, idx = self.mat(material)
        base = len(verts)
        bit = [n * 0 for n in normal]
        b = [normal[1] * tangent[2] - normal[2] * tangent[1], normal[2] * tangent[0] - normal[0] * tangent[2],
             normal[0] * tangent[1] - normal[1] * tangent[0]]
        for p in (p0, p1, p2, p3):
            u = sum(p[a] * tangent[a] for a in range(3)) / uv_scale
            v = -sum(p[a] * b[a] for a in range(3)) / uv_scale
            verts.append((p, u, v, lm, pack_unit(normal), pack_unit(tangent)))
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
        if os.environ.get('IWZ_DOUBLE_SIDED') == '1':
            idx += [base, base + 2, base + 1, base, base + 3, base + 2]
        if collide:
            self.col += [(p0, p1, p2), (p0, p2, p3)]

    def quad_uv(self, material, pts, uvs, normal, tangent, lm, collide=True, double_sided=None):
        """Quad with explicit texture coordinates (pts counter-clockwise seen from the normal side)."""
        verts, idx = self.mat(material)
        base = len(verts)
        for p, (u, v) in zip(pts, uvs):
            verts.append((tuple(float(c) for c in p), u, v, lm, pack_unit(normal), pack_unit(tangent)))
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
        if double_sided is None:
            double_sided = os.environ.get('IWZ_DOUBLE_SIDED') == '1'
        if double_sided:
            idx += [base, base + 2, base + 1, base, base + 3, base + 2]
        if collide:
            p0, p1, p2, p3 = pts
            self.col += [(p0, p1, p2), (p0, p2, p3)]


def box_faces(mesh, mn, mx, mats, lm, inward=False, skip=()):
    """Six faces of an axis-aligned box. mats: dict face->material ('floor','ceiling','wall')."""
    x0, y0, z0 = mn; x1, y1, z1 = mx
    s = -1 if inward else 1
    faces = {
        'top':    ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1), (1, 0, 0)),
        'bottom': ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1), (1, 0, 0)),
        'south':  ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0), (1, 0, 0)),
        'north':  ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0), (-1, 0, 0)),
        'west':   ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0), (0, -1, 0)),
        'east':   ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0), (0, 1, 0)),
    }
    for name, (pts, n, t) in faces.items():
        if name in skip: continue
        if inward:
            pts = pts[::-1]; n = tuple(-c for c in n); t = tuple(-c for c in t)
        m = mats['floor'] if (name == 'bottom') ^ (not inward) and name in ('top', 'bottom') else None
        if name in ('top', 'bottom'):
            m = mats['floor'] if (inward and name == 'bottom') or (not inward and name == 'top') else mats['ceiling']
        else:
            m = mats['wall']
        mesh.quad(m, *pts, normal=n, tangent=t, lm=lm)


def write_world(mesh, path):
    surfaces = []; verts = []; indices = []
    allp = []
    for mi, m in enumerate(mesh.materials):
        v, idx = mesh.by_mat[m]
        # split into surfaces of <= 65535 vertices (u16 indices are relative to firstVertex)
        start = 0
        while start < len(idx):
            end = min(len(idx), start + 30000 * 3)
            sub = idx[start:end]
            lo = min(sub); hi = max(sub)
            first = len(verts)
            vmap = {}
            for i in range(lo, hi + 1):
                vmap[i] = len(verts) - first; verts.append(v[i])
            base = len(indices)
            indices += [vmap[i] for i in sub]
            pts = [v[i][0] for i in range(lo, hi + 1)]
            allp += pts
            mn = [min(p[a] for p in pts) for a in range(3)]; mx = [max(p[a] for p in pts) for a in range(3)]
            surfaces.append((mi, first, hi - lo + 1, base, len(sub) // 3, mn, mx))
            start = end
    names = []
    for m in mesh.materials:
        base = m.split('|')[0]
        if base not in names: names.append(base)
    surfaces = [(names.index(mesh.materials[mi].split('|')[0]),) + tuple(rest) for (mi, *rest) in surfaces]
    out = bytearray(struct.pack('<II', 0x575A5749, 1))
    out += struct.pack('<I', len(names))
    for m in names:
        e = m.encode(); out += struct.pack('<H', len(e)) + e
    out += struct.pack('<I', len(verts))
    for (p, u, vv, lm, n, t) in verts:
        out += struct.pack('<3ff4B2f2fII', *p, 0.0078125, 255, 255, 255, 255, u, vv, lm[0], lm[1], n, t)
    out += struct.pack('<I', len(indices)) + struct.pack('<%dH' % len(indices), *indices)
    out += struct.pack('<I', len(surfaces))
    for (mi, first, vc, base, tc, mn, mx) in surfaces:
        out += struct.pack('<5I6f', mi, first, vc, base, tc, *mn, *mx)
    wmn = [min(p[a] for p in allp) for a in range(3)]; wmx = [max(p[a] for p in allp) for a in range(3)]
    out += struct.pack('<6f', *wmn, *wmx)
    open(path, 'wb').write(out)
    return len(verts), len(indices), len(surfaces), (wmn, wmx)


# ---------------------------------------------------------------- nav graph (bfx, IW7 graph version 0x2B)
def nav_graph(cells, cell, link=None):
    """cells: dict (i, j) -> z (walkable grid cells of size `cell`, floor height z). One quad area per cell."""
    keys = sorted(cells)
    HS, AREA, EDGE = 336, 72, 32
    offs = {}
    off = HS
    for k in keys:
        offs[k] = off; off += AREA + EDGE * 4
    area_bytes = off - HS
    gmn = [min(i for i, j in keys) * cell, min(j for i, j in keys) * cell, min(cells.values())]
    gmx = [(max(i for i, j in keys) + 1) * cell, (max(j for i, j in keys) + 1) * cell, max(cells.values()) + 72]
    def center(k):
        i, j = k; return ((i + 0.5) * cell, (j + 0.5) * cell, cells[k])
    # kd tree over area centers
    kd = bytearray(struct.pack('<6f', *gmn, *gmx)) + bytearray(4)
    def kd_rec(items):
        if len(items) == 1:
            kd.extend(struct.pack('<I', 0x80000000 | offs[items[0]])); return
        cs = [center(k) for k in items]
        ax = max(range(2), key=lambda a: max(c[a] for c in cs) - min(c[a] for c in cs))
        items = sorted(items, key=lambda k: center(k)[ax])
        h = len(items) // 2
        left_max = max(center(k)[ax] + cell / 2 for k in items[:h])
        right_min = min(center(k)[ax] - cell / 2 for k in items[h:])
        node = len(kd); kd.extend(struct.pack('<Iff', 0, left_max, right_min))
        kd_rec(items[:h])
        struct.pack_into('<I', kd, node, ax << 28 | (len(kd) - node))
        kd_rec(items[h:])
    kd_rec(keys)
    struct.pack_into('<I', kd, 24, len(kd) - 28)
    graph = bytearray(HS + area_bytes)
    graph_bytes = HS + area_bytes + len(kd)
    struct.pack_into('<IIII', graph, 0, 0x2B, 0, area_bytes, len(kd))
    struct.pack_into('<I', graph, 24, 56)
    struct.pack_into('<I', graph, 32, graph_bytes)
    struct.pack_into('<5f', graph, 36, 72.0, 5.0, 15.0, 10.0, 72.0)
    struct.pack_into('<6f', graph, 56, *gmn, *gmx)
    struct.pack_into('<I', graph, 80, 2)
    for k in keys:
        i, j = k; z = cells[k]; base = offs[k]
        c = center(k)
        corners = [(i * cell, j * cell, z), ((i + 1) * cell, j * cell, z), ((i + 1) * cell, (j + 1) * cell, z), (i * cell, (j + 1) * cell, z)]
        nbrs = [(i, j - 1), (i + 1, j), (i, j + 1), (i - 1, j)]   # edge e goes corner e -> e+1
        struct.pack_into('<3ff', graph, base + 32, *c, math.sqrt(2) * cell / 2)
        struct.pack_into('<III', graph, base + 48, 0xFFFFFFFF, 0, 0x3FFFF << 7 | 4)
        struct.pack_into('<II', graph, base + 60, 2 << 24 | 0x110000, 0)
        for e in range(4):
            eo = base + AREA + EDGE * e
            nb = nbrs[e]
            if nb in cells and abs(cells[nb] - z) <= 18 and (link is None or link(k, nb)):
                nc = center(nb)
                cost = int(math.ceil(math.dist(c, nc) * 1000.0 / 72.0))
                struct.pack_into('<Q', graph, eo, offs[nb])
            else:
                cost = 0
            struct.pack_into('<3fIII', graph, eo + 8, *corners[e], 0xFFFF0000, cost, 0)
    g = bytes(graph) + bytes(kd)
    body = 12 + 12 + len(g)
    res = bytearray(24 + body)
    struct.pack_into('<III', res, 4, 2, body, 0)
    struct.pack_into('<IIII', res, 20, 0x1000001, 0x10000, 12 + len(g), 1)
    struct.pack_into('<II', res, 40, 0x2B, 1)
    res[48:] = g
    chk = sum(struct.unpack_from('<%dI' % ((len(res) - 24) // 4), res, 24)) & 0xFFFFFFFF
    struct.pack_into('<I', res, 12, chk)
    return bytes(res), len(keys)


def ents_text(worldspawn, ents):
    out = []
    for e in [worldspawn] + ents:
        out.append('{')
        for k, v in e:
            out.append('%s "%s"' % (k, v))
        out.append('}')
    return '\n'.join(out) + '\n'


def stock_worldspawn(ents_path):
    txt = open(ents_path, 'rb').read().decode('latin-1')
    block = txt[txt.index('{') + 1: txt.index('}')]
    rows = []
    for ln in block.strip().splitlines():
        k, v = ln.split(' ', 1)
        rows.append((k, v.strip().strip('"')))
    return rows
