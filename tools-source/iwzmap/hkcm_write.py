"""Encode a triangle soup as an IW7 world collision packfile (hknpCompressedMeshShape).

Format facts were measured on the stock cp_zmb colmap (see hkcm.py / hktree_check.py / simd_check.py):
  key = section << 8 | prim << 1 | tri ; sections <= 127 primitives ; shared vertex index = page << 16 | u16
  top tree Codec3Axis5 (leaf = section), section tree Codec3Axis4 (leaf = prim << 1, internal = offset | 1)
  simd tree: node 0 empty, root 1, data even = child node << 1, odd = key << 1 | 1.
The HavokPhysicsShapeList root (surface table, names) is reused from the stock template; only its domain changes.
"""
import math, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hkpack import Packfile

FLT_MAX = struct.unpack('<f', struct.pack('<I', 0x7F7FFFEE))[0]
CURVE = 226.0


def q_axis(mn, mx, pmn, pmx):
    span = pmx - pmn
    if span <= 0: return 0
    lo = int(math.floor(math.sqrt(max((mn - pmn) * CURVE / span, 0.0))))
    hi = int(math.floor(math.sqrt(max((pmx - mx) * CURVE / span, 0.0))))
    return (min(15, lo) << 4) | min(15, hi)


def dq_axis(byte, pmn, pmx):
    s = pmx - pmn
    return pmn + (byte >> 4) ** 2 / CURVE * s, pmx - (byte & 15) ** 2 / CURVE * s


def bounds(boxes):
    return ([min(b[0][a] for b in boxes) for a in range(3)], [max(b[1][a] for b in boxes) for a in range(3)])


class Node:
    __slots__ = ('mn', 'mx', 'leaf', 'kids')
    def __init__(self, mn, mx, leaf=None, kids=None):
        self.mn, self.mx, self.leaf, self.kids = mn, mx, leaf, kids


def bvh(items):
    """items: [(id, mn, mx)] -> binary Node tree (median split on longest axis)."""
    mn, mx = bounds([(i[1], i[2]) for i in items])
    if len(items) == 1:
        return Node(mn, mx, leaf=items[0][0])
    ax = max(range(3), key=lambda a: mx[a] - mn[a])
    items = sorted(items, key=lambda i: i[1][ax] + i[2][ax])
    h = len(items) // 2
    return Node(mn, mx, kids=[bvh(items[:h]), bvh(items[h:])])


def emit_axis4(root, dmn, dmx):
    out = []
    def rec(n, pmn, pmx):
        i = len(out)
        xyz = [q_axis(n.mn[a], n.mx[a], pmn[a], pmx[a]) for a in range(3)]
        out.append(xyz + [0])
        d = [dq_axis(xyz[a], pmn[a], pmx[a]) for a in range(3)]
        cmn, cmx = [x[0] for x in d], [x[1] for x in d]
        if n.leaf is not None:
            assert n.leaf < 128
            out[i][3] = n.leaf << 1
        else:
            rec(n.kids[0], cmn, cmx)
            off = len(out) - i
            assert off <= 0xFE and off % 2 == 0
            out[i][3] = off | 1
            rec(n.kids[1], cmn, cmx)
    rec(root, dmn, dmx)
    return b''.join(bytes(x) for x in out)


def emit_axis5(root, dmn, dmx):
    out = []; leaf_node = {}
    def rec(n, pmn, pmx, is_root=False):
        i = len(out)
        if is_root:
            xyz = [0, 0, 0]; cmn, cmx = pmn, pmx
        else:
            xyz = [q_axis(n.mn[a], n.mx[a], pmn[a], pmx[a]) for a in range(3)]
            d = [dq_axis(xyz[a], pmn[a], pmx[a]) for a in range(3)]
            cmn, cmx = [x[0] for x in d], [x[1] for x in d]
        out.append(xyz + [0, 0])
        if n.leaf is not None:
            out[i][3], out[i][4] = (n.leaf >> 8) & 0x7F, n.leaf & 0xFF
            leaf_node[n.leaf] = i
        else:
            rec(n.kids[0], cmn, cmx)
            data = (len(out) - i) // 2
            assert (len(out) - i) % 2 == 0 and data < 0x8000
            out[i][3], out[i][4] = 0x80 | ((data >> 8) & 0x7F), data & 0xFF
            rec(n.kids[1], cmn, cmx)
    rec(root, dmn, dmx, True)
    return b''.join(bytes(x) for x in out), leaf_node


def emit_simd(root):
    """4-wide tree: node 0 empty, root at 1."""
    empty = struct.pack('<4f', FLT_MAX, FLT_MAX, FLT_MAX, FLT_MAX) + struct.pack('<4f', -FLT_MAX, -FLT_MAX, -FLT_MAX, -FLT_MAX)
    empty_node = empty * 3 + struct.pack('<4I', 0, 0, 0, 0)
    nodes = [empty_node]
    def kids4(n):
        ks = [n] if n.leaf is not None else list(n.kids)
        while len(ks) < 4:
            j = next((k for k in range(len(ks)) if ks[k].leaf is None), None)
            if j is None: break
            k = ks.pop(j); ks[j:j] = k.kids
        return ks
    def rec(n):
        i = len(nodes); nodes.append(None)
        ks = kids4(n)
        lo = [[FLT_MAX] * 4 for _ in range(3)]; hi = [[-FLT_MAX] * 4 for _ in range(3)]; data = [0, 0, 0, 0]
        for j, k in enumerate(ks):
            for a in range(3): lo[a][j], hi[a][j] = k.mn[a], k.mx[a]
            data[j] = (k.leaf << 1 | 1) if k.leaf is not None else (rec(k) << 1)
        nodes[i] = b''.join(struct.pack('<4f', *lo[a]) + struct.pack('<4f', *hi[a]) for a in range(3)) + struct.pack('<4I', *data)
        return i
    rec(root)
    return b''.join(nodes), len(nodes)


def tri_box(t):
    return [min(v[a] for v in t) for a in range(3)], [max(v[a] for v in t) for a in range(3)]


def split_sections(tris, ids, max_tris=127):
    """Recursive split: <=127 triangles and <=255 unique vertices per section."""
    verts = {v for i in ids for v in tris[i]}
    if len(ids) <= max_tris and len(verts) <= 255:
        return [ids]
    mn, mx = bounds([tri_box(tris[i]) for i in ids])
    ax = max(range(3), key=lambda a: mx[a] - mn[a])
    s = sorted(ids, key=lambda i: sum(v[ax] for v in tris[i]))
    h = len(s) // 2
    return split_sections(tris, s[:h], max_tris) + split_sections(tris, s[h:], max_tris)


class Writer:
    def __init__(self):
        self.b = bytearray(); self.local = []; self.glob = []
    def align(self, n=16):
        while len(self.b) % n: self.b.append(0)
    def put(self, data):
        self.align(); o = len(self.b); self.b += data; return o
    def arr(self, at, target, count, flags=0x80000000):
        struct.pack_into('<QiI', self.b, at, 0, count, count | flags)
        if count: self.local.append((at, target))


def encode(tris, template_path, tag=0, max_tris=127):
    tris = [tuple(tuple(float(c) for c in v) for v in t) for t in tris]
    tpl = Packfile(open(template_path, 'rb').read())
    tb = tpl.data_sec.body
    root_end = [a for a, n, _ in tpl.objects if n == 'hknpCompressedMeshShape'][0]
    pts = [v for t in tris for v in t]
    dmn = [min(p[a] for p in pts) - 1.0 for a in range(3)]
    dmx = [max(p[a] for p in pts) + 1.0 for a in range(3)]
    span = [dmx[a] - dmn[a] for a in range(3)]
    def qv(p):
        q = [int(round((p[a] - dmn[a]) / span[a] * (0x1FFFFF if a < 2 else 0x3FFFFF))) for a in range(3)]
        return q[0] | q[1] << 21 | q[2] << 42
    shared = []
    sections = split_sections(tris, list(range(len(tris))), max_tris)
    sec_boxes = [bounds([tri_box(tris[i]) for i in s]) for s in sections]
    top_root = bvh([(k, sec_boxes[k][0], sec_boxes[k][1]) for k in range(len(sections))])
    top_bytes, leaf_node = emit_axis5(top_root, dmn, dmx)
    prims = bytearray(); svi = bytearray(); runs = bytearray(); sec_recs = []; sec_trees = []
    simd_items = []
    for k, s in enumerate(sections):
        local = []; lmap = {}
        for i in s:
            for v in tris[i]:
                if v not in lmap:
                    lmap[v] = len(local); local.append(v)
        # one shared-vertex page per section: start a new page when the section would straddle one
        if (len(shared) >> 16) != ((len(shared) + len(local) - 1) >> 16):
            shared += [shared[-1]] * (((len(shared) >> 16) + 1 << 16) - len(shared))
        base = len(shared)
        shared += [qv(v) for v in local]
        page = base >> 16
        local = list(range(base, base + len(local)))
        sh_off = len(svi) // 2
        for g in local: svi += struct.pack('<H', g & 0xFFFF)
        p_off = len(prims) // 4
        for j, i in enumerate(s):
            a, b_, c = (lmap[v] for v in tris[i])
            prims += bytes([a, b_, c, c])
            mn, mx = tri_box(tris[i])
            simd_items.append(((k << 8) | (j << 1), mn, mx))
        r_off = len(runs) // 4
        runs += struct.pack('<HBB', tag, 0, len(s))
        smn, smx = sec_boxes[k]
        sroot = bvh([(j, *tri_box(tris[i])) for j, i in enumerate(s)])
        sec_trees.append(emit_axis4(sroot, smn, smx))
        sec_recs.append((smn, smx, sh_off, len(local), p_off, len(s), r_off, page, leaf_node[k]))
    simd_root = bvh(simd_items)
    simd_bytes, simd_n = emit_simd(simd_root)
    nsec = len(sections)
    maxkey = ((nsec - 1) << 8) | ((len(sections[-1]) - 1) << 1)
    # keys keep 8 low bits for prim << 1 | tri; stock: 8 + bits(section count) (2011 sections -> 19)
    bits = 8 + max(1, (nsec - 1).bit_length())
    nkeys = len(tris)
    # ---- data section
    w = Writer()
    w.b += tb[:root_end]                                   # stock HavokPhysicsShapeList root (+ its arrays)
    w.local += [(a, t) for a, t in tpl.data_sec.locals if a < root_end]
    struct.pack_into('<4f', w.b, 0x100, *dmn, 0.0)
    struct.pack_into('<4f', w.b, 0x110, *dmx, 0.0)
    shape = w.put(bytes(tb[root_end:root_end + 0xA0]))
    assert shape == root_end
    w.glob.append((0xA0, shape))                            # shapes[0] -> CM shape
    struct.pack_into('<BB', w.b, shape + 0x12, bits, 0x02)
    qwords = (((maxkey + 2) // 2) + 31) // 32
    twords = ((maxkey + 1) + 31) // 32
    qf = w.put(bytes(4 * qwords)); w.arr(shape + 0x68, qf, qwords); struct.pack_into('<I', w.b, shape + 0x78, (maxkey + 2) // 2)
    tf = w.put(bytes(4 * twords)); w.arr(shape + 0x80, tf, twords); struct.pack_into('<I', w.b, shape + 0x90, maxkey + 1)
    # IW7's hknpCompressedMeshShapeData is 0x100 bytes: after simdTree come three empty hkArrays
    # (+0xC8, +0xD8, +0xE8, DONT_DEALLOCATE) that the engine destroys when the zone unloads
    data = w.put(bytes(0x100))
    for off in (0xC8, 0xD8, 0xE8):
        struct.pack_into('<QiI', w.b, data + off, 0, 0, 0x80000000)
    w.b[data:data + 0x10] = tb[[a for a, n, _ in tpl.objects if n == 'hknpCompressedMeshShapeData'][0]:][:0x10]
    w.glob.append((shape + 0x60, data))
    struct.pack_into('<4f', w.b, data + 0x20, *dmn, 0.0)
    struct.pack_into('<4f', w.b, data + 0x30, *dmx, 0.0)
    struct.pack_into('<iiI', w.b, data + 0x40, nkeys, bits, maxkey)
    o = w.put(top_bytes); w.arr(data + 0x10, o, len(top_bytes) // 5)
    secs = w.put(bytes(96 * nsec)); w.arr(data + 0x50, secs, nsec)
    for k, (smn, smx, sh_off, nsh, p_off, np_, r_off, page, leaf) in enumerate(sec_recs):
        so = secs + 96 * k
        struct.pack_into('<4f4f', w.b, so + 16, *smn, 0.0, *smx, 0.0)
        struct.pack_into('<3f3f', w.b, so + 48, FLT_MAX, FLT_MAX, FLT_MAX, -math.inf, -math.inf, -math.inf)
        struct.pack_into('<IIII', w.b, so + 72, 0, sh_off << 8, p_off << 8 | np_, r_off << 8 | 1)
        struct.pack_into('<BBHBBBB', w.b, so + 88, 0, nsh, leaf, page, 0, 0, 0)
    for k, t in enumerate(sec_trees):
        o = w.put(t); w.arr(secs + 96 * k, o, len(t) // 4)
    o = w.put(bytes(prims)); w.arr(data + 0x60, o, len(prims) // 4)
    o = w.put(bytes(svi)); w.arr(data + 0x70, o, len(svi) // 2)
    w.arr(data + 0x80, 0, 0)
    o = w.put(b''.join(struct.pack('<Q', v) for v in shared)); w.arr(data + 0x90, o, len(shared))
    o = w.put(bytes(runs)); w.arr(data + 0xA0, o, len(runs) // 4)
    o = w.put(simd_bytes); w.arr(data + 0xB8, o, simd_n)
    w.align()
    objs = [(0, 'HavokPhysicsShapeList'), (shape, 'hknpCompressedMeshShape'), (data, 'hknpCompressedMeshShapeData')]
    return pack(tpl, w, objs), dict(sections=nsec, shared=len(shared), maxkey=maxkey, bits=bits, simd=simd_n)


def pad(buf, fill=0xFF):
    while len(buf) % 16: buf.append(fill)


def pack(tpl, w, objs):
    raw = tpl.data
    cn_sec = tpl.sections[0]
    name_off = {v[1]: k for k, v in tpl.classnames.items()}
    out = bytearray(raw[:tpl.header_size + 0x40 * tpl.num_sections])
    cn_start = len(out)
    out += cn_sec.body; pad(out)
    data_start = len(out)
    body = bytes(w.b)
    out += body
    loc = bytearray()
    for a, t in sorted(w.local): loc += struct.pack('<ii', a, t)
    pad(loc)
    glo = bytearray()
    for a, t in w.glob: glo += struct.pack('<iii', a, 2, t)
    pad(glo)
    vir = bytearray()
    for a, n in objs: vir += struct.pack('<iii', a, 0, name_off[n])
    pad(vir)
    out += loc + glo + vir
    rel_loc = len(body); rel_glo = rel_loc + len(loc); rel_vir = rel_glo + len(glo); rel_end = rel_vir + len(vir)
    def sec_hdr(i, start, l, g, v, e):
        o = tpl.header_size + 0x40 * i
        struct.pack_into('<7I', out, o + 20, start, l, g, v, e, e, e)
    sec_hdr(0, cn_start, len(cn_sec.body), len(cn_sec.body), len(cn_sec.body), len(cn_sec.body))
    sec_hdr(1, data_start, 0, 0, 0, 0)
    sec_hdr(2, data_start, rel_loc, rel_glo, rel_vir, rel_end)
    return bytes(out)


if __name__ == '__main__':
    # self-test: a 512x512 floor plus four 256-high walls; decode back and compare triangle sets
    from hkcm import decode_cm_data
    def quad(a, b_, c, d): return [(a, b_, c), (a, c, d)]
    T = []
    n = 8
    for i in range(n):
        for j in range(n):
            x0, y0, s = -256 + 64 * i, -256 + 64 * j, 64
            T += quad((x0, y0, 0), (x0 + s, y0, 0), (x0 + s, y0 + s, 0), (x0, y0 + s, 0))
    for (ax, ay, bx, by) in [(-256, -256, 256, -256), (256, -256, 256, 256), (256, 256, -256, 256), (-256, 256, -256, -256)]:
        T += quad((ax, ay, 0), (bx, by, 0), (bx, by, 256), (ax, ay, 256))
    blob, info = encode(T, sys.argv[1])
    open(sys.argv[2], 'wb').write(blob)
    pf = Packfile(blob)
    d = [a for a, n_, _ in pf.objects if n_ == 'hknpCompressedMeshShapeData'][0]
    r = decode_cm_data(pf, d)
    got = sorted(tuple(sorted(tuple(round(c) for c in v) for v in t)) for t in r['tris'])
    want = sorted(tuple(sorted(tuple(round(c) for c in v) for v in t)) for t in T)
    print(info, 'decoded', len(r['tris']), 'match', got == want)
