#!/usr/bin/env python3
"""Reader and writer for the IW7 bfx NavGraph (graph version 0x2B), the payload of the zone's navmesh asset.

Layout (all little endian, offsets measured on the stock cp_zmb navmesh, see docs/NAVMESH.md):

  header   336 bytes   ver 0x2B, area_bytes@8, kd_bytes@12, 0x38@24, graph_bytes@32, params@36 (5 floats),
                       bounds@56 (6 floats: min xyz, max xyz), 2@80, 128 bytes of stock-only data @208
  areas    area_bytes  each: 72-byte header + 32 bytes per edge; low 7 bits of the word @56 = edge count
  kd tree  kd_bytes    28-byte header (bounds 6 floats + payload size u32) then nodes: internal = 12 bytes
                       (axis<<28 | offset to the right child, left_max, right_min), leaf = 4 bytes
                       (0x80000000 | area offset)

A navmesh file is either a bare resource (our navgraph.bin: 48 bytes then the graph) or a ZoneTool dump (340
bytes then the graph, then trailing tables). Both are located by the marker 2B 01 2B that precedes the graph.

CLI:  navfmt.py read <file> [--json]     decode and print the statistics
      navfmt.py roundtrip <file>         read then write, compare bytes
"""
import collections
import json
import math
import os
import struct
import sys

HS, AREA, EDGE = 336, 72, 32
MARKER = bytes.fromhex('2b000000010000002b000000')
EDGE_COST_NONE = 0


class Edge:
    __slots__ = ('nbr', 'corner', 'flags', 'cost', 'tail')

    def __init__(self, nbr=0, corner=(0.0, 0.0, 0.0), flags=0xFFFF0000, cost=0, tail=0):
        self.nbr, self.corner, self.flags, self.cost, self.tail = nbr, tuple(corner), flags, cost, tail


class Area:
    __slots__ = ('off', 'pre', 'centre', 'radius', 'w48', 'w52', 'flags', 'w60', 'w64', 'w68', 'edges')

    def __init__(self, centre, radius, edges, off=0, pre=bytes(32), w48=0xFFFFFFFF, w52=0, w60=0x02110000, w64=0, w68=0,
                 flags=None):
        self.off, self.pre, self.centre, self.radius = off, pre, tuple(centre), radius
        self.w48, self.w52, self.w60, self.w64, self.w68 = w48, w52, w60, w64, w68
        self.edges = edges
        self.flags = (0x3FFFF << 7 | len(edges)) if flags is None else flags

    @property
    def size(self):
        return AREA + EDGE * len(self.edges)

    def polygon(self):
        return [e.corner for e in self.edges]


class KdNode:
    __slots__ = ('word', 'lo', 'hi')

    def __init__(self, word, lo=None, hi=None):
        self.word, self.lo, self.hi = word, lo, hi

    @property
    def is_leaf(self):
        return self.lo is None


class Graph:
    def __init__(self):
        self.header = bytearray(HS)
        self.areas = []
        self.kd_head = bytes(28)
        self.kd = []           # flat nodes in stream order
        self.prefix = b''
        self.suffix = b''

    # header views
    @property
    def params(self):
        return struct.unpack_from('<5f', self.header, 36)

    @property
    def bounds(self):
        return struct.unpack_from('<6f', self.header, 56)

    def by_off(self):
        return {a.off: a for a in self.areas}


def find_graph(data):
    i = data.find(MARKER)
    if i < 0:
        raise ValueError('no NavGraph marker (2B 01 2B) in the file')
    return i + 8


def parse_graph(g):
    gr = Graph()
    ver, _pad, area_bytes, kd_bytes = struct.unpack_from('<IIII', g, 0)
    if ver != 0x2B:
        raise ValueError('graph version %#x, expected 0x2B' % ver)
    gr.header = bytearray(g[:HS])
    off = HS
    end = HS + area_bytes
    while off < end:
        pre = bytes(g[off:off + 32])
        c = struct.unpack_from('<3f', g, off + 32)
        r = struct.unpack_from('<f', g, off + 44)[0]
        w48, w52, flags, w60, w64, w68 = struct.unpack_from('<6I', g, off + 48)
        n = flags & 0x7F
        edges = []
        for e in range(n):
            eo = off + AREA + EDGE * e
            nbr = struct.unpack_from('<Q', g, eo)[0]
            x, y, z, ef, cost, tail = struct.unpack_from('<3fIII', g, eo + 8)
            edges.append(Edge(nbr, (x, y, z), ef, cost, tail))
        gr.areas.append(Area(c, r, edges, off, pre, w48, w52, w60, w64, w68, flags))
        off += AREA + EDGE * n
    if off != end:
        raise ValueError('areas end at %d, header says %d' % (off, end))
    kd = g[end:end + kd_bytes]
    gr.kd_head = bytes(kd[:28])
    pos = 28
    stack = 0
    while pos < len(kd):
        w = struct.unpack_from('<I', kd, pos)[0]
        if w & 0x80000000:
            gr.kd.append(KdNode(w))
            pos += 4
        else:
            lo, hi = struct.unpack_from('<2f', kd, pos + 4)
            gr.kd.append(KdNode(w, lo, hi))
            pos += 12
    if pos != len(kd):
        raise ValueError('kd tree overruns its section (%d vs %d)' % (pos, len(kd)))
    return gr, HS + area_bytes + kd_bytes


def write_graph(gr):
    """Serialise the graph; areas are laid out in list order and offsets (`off`, kd leaves, edge links) are the
    caller's: use `relayout` first when areas were added or edge counts changed."""
    h = bytearray(gr.header)
    area_bytes = sum(a.size for a in gr.areas)
    kd = bytearray(gr.kd_head)
    for n in gr.kd:
        if n.is_leaf:
            kd += struct.pack('<I', n.word)
        else:
            kd += struct.pack('<Iff', n.word, n.lo, n.hi)
    struct.pack_into('<I', kd, 24, len(kd) - 28)
    struct.pack_into('<II', h, 8, area_bytes, len(kd))
    struct.pack_into('<I', h, 32, HS + area_bytes + len(kd))
    out = bytearray(h)
    for a in gr.areas:
        out += a.pre
        out += struct.pack('<4f', *a.centre, a.radius)
        out += struct.pack('<6I', a.w48, a.w52, a.flags, a.w60, a.w64, a.w68)
        for e in a.edges:
            out += struct.pack('<Q3fIII', e.nbr, *e.corner, e.flags, e.cost, e.tail)
    out += kd
    return bytes(out)


def read_file(path):
    data = open(path, 'rb').read()
    gs = find_graph(data)
    gr, glen = parse_graph(data[gs:])
    gr.prefix = data[:gs]
    gr.suffix = data[gs + glen:]
    return gr


def write_file(gr):
    return gr.prefix + write_graph(gr) + gr.suffix


def wrap_resource(graph):
    """The bare resource our compiler reads (24-byte resource header, 12-byte graph header, 12 bytes of
    inner header, then the graph); the same wrapper mapgen.nav_graph emits."""
    body = 12 + 12 + len(graph)
    res = bytearray(24 + body)
    struct.pack_into('<III', res, 4, 2, body, 0)
    struct.pack_into('<IIII', res, 20, 0x1000001, 0x10000, 12 + len(graph), 1)
    struct.pack_into('<II', res, 40, 0x2B, 1)
    res[48:] = graph
    chk = sum(struct.unpack_from('<%dI' % ((len(res) - 24) // 4), res, 24)) & 0xFFFFFFFF
    struct.pack_into('<I', res, 12, chk)
    return bytes(res)


def relayout(gr):
    """Recompute `off` of every area. Edge `nbr` values are offsets; callers that build graphs use
    `link_by_index` below instead of touching offsets."""
    off = HS
    for a in gr.areas:
        a.off = off
        off += a.size


# ------------------------------------------------------------------------------ analysis
def kd_walk(gr):
    """Yield (depth, node) along the stream; returns leaf area offsets and axes used."""
    axes = collections.Counter()
    leaves = []
    depths = []
    pos = 28
    sizes = []
    for n in gr.kd:
        sizes.append(4 if n.is_leaf else 12)
    starts = []
    p = 28
    for s in sizes:
        starts.append(p)
        p += s
    idx_of = {s: i for i, s in enumerate(starts)}

    def rec(i, d):
        n = gr.kd[i]
        if n.is_leaf:
            leaves.append(n.word & 0x7FFFFFFF)
            depths.append(d)
            return
        axes[n.word >> 28] += 1
        rec(i + 1, d + 1)
        rec(idx_of[starts[i] + (n.word & 0x0FFFFFFF)], d + 1)
    rec(0, 0)
    return axes, leaves, depths


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i][0], poly[i][1]
        x1, y1 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


def stats(gr, examples=3):
    by = gr.by_off()
    out = {'version': hex(struct.unpack_from('<I', gr.header, 0)[0]), 'params': list(gr.params),
           'bounds': list(gr.bounds), 'areas': len(gr.areas)}
    out['edge_count_hist'] = dict(sorted(collections.Counter(len(a.edges) for a in gr.areas).items()))
    out['edge_flags'] = {hex(k): v for k, v in collections.Counter(e.flags for a in gr.areas for e in a.edges).items()}
    out['area_w48'] = {hex(k): v for k, v in collections.Counter(a.w48 for a in gr.areas).items()}
    out['area_w52'] = {hex(k): v for k, v in collections.Counter(a.w52 for a in gr.areas).items()}
    out['area_flags_high'] = {hex(k): v for k, v in collections.Counter(a.flags >> 7 for a in gr.areas).items()}
    out['area_w60'] = {hex(k): v for k, v in collections.Counter(a.w60 for a in gr.areas).most_common(12)}
    out['area_w64_w68'] = {'%x,%x' % k: v for k, v in collections.Counter((a.w64, a.w68) for a in gr.areas).most_common(8)}
    out['area_pre_nonzero'] = sum(1 for a in gr.areas if any(a.pre))
    out['edge_tail'] = {hex(k): v for k, v in collections.Counter(e.tail for a in gr.areas for e in a.edges).most_common(8)}
    links = [e for a in gr.areas for e in a.edges if e.cost]
    out['edges_total'] = sum(len(a.edges) for a in gr.areas)
    out['edges_linked'] = len(links)
    out['links_to_unknown_area'] = sum(1 for e in links if e.nbr not in by)
    out['link_nbr_nonzero_with_cost0'] = sum(1 for a in gr.areas for e in a.edges if not e.cost and e.nbr)
    # symmetry
    sym = 0
    for a in gr.areas:
        for e in a.edges:
            if e.cost and e.nbr in by and any(f.cost and f.nbr == a.off for f in by[e.nbr].edges):
                sym += 1
    out['links_symmetric'] = sym
    dz = [abs(by[e.nbr].centre[2] - a.centre[2]) for a in gr.areas for e in a.edges if e.cost and e.nbr in by]
    out['link_dz_max'] = round(max(dz), 2) if dz else 0
    out['link_dz_gt18'] = sum(1 for v in dz if v > 18.5)
    # kd
    axes, leaves, depths = kd_walk(gr)
    out['kd'] = {'nodes': len(gr.kd), 'internal': sum(1 for n in gr.kd if not n.is_leaf), 'leaves': len(leaves),
                 'axis_use': dict(axes), 'max_depth': max(depths) if depths else 0,
                 'leaf_areas_unique': len(set(leaves)), 'leaves_match_areas': sorted(leaves) == sorted(by)}
    # stacked floors: areas whose xy footprint overlaps another area's at a z more than the agent height apart
    G = 128.0
    cell = collections.defaultdict(list)
    bbs = {}
    for i, a in enumerate(gr.areas):
        xs = [c[0] for c in a.polygon()] or [a.centre[0]]
        ys = [c[1] for c in a.polygon()] or [a.centre[1]]
        bbs[i] = (min(xs), max(xs), min(ys), max(ys))
        for ix in range(int(math.floor(min(xs) / G)), int(math.floor(max(xs) / G)) + 1):
            for iy in range(int(math.floor(min(ys) / G)), int(math.floor(max(ys) / G)) + 1):
                cell[(ix, iy)].append(i)
    stacked = set()
    pairs = []
    seen = set()
    for lst in cell.values():
        for ai in range(len(lst)):
            for bi in range(ai + 1, len(lst)):
                i, j = lst[ai], lst[bi]
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                a, b = gr.areas[i], gr.areas[j]
                if abs(a.centre[2] - b.centre[2]) < 72.0:
                    continue
                if point_in_poly(a.centre[0], a.centre[1], b.polygon()) or point_in_poly(b.centre[0], b.centre[1], a.polygon()):
                    stacked.add(i); stacked.add(j)
                    pairs.append((i, j))
    out['stacked_areas'] = len(stacked)
    out['stacked_pairs'] = len(pairs)
    pairs.sort(key=lambda p: -abs(gr.areas[p[0]].centre[2] - gr.areas[p[1]].centre[2]))
    out['stacked_examples'] = [{'xy': [round(gr.areas[i].centre[0], 1), round(gr.areas[i].centre[1], 1)],
                                'z': [round(gr.areas[i].centre[2], 1), round(gr.areas[j].centre[2], 1)]}
                               for i, j in pairs[:examples]]
    zs = [a.centre[2] for a in gr.areas]
    out['z_range'] = [round(min(zs), 1), round(max(zs), 1)]
    out['suffix_bytes'] = len(gr.suffix)
    out['prefix_bytes'] = len(gr.prefix)
    out['header_stock_data_nonzero_words'] = sum(1 for o in range(208, HS, 4) if struct.unpack_from('<I', gr.header, o)[0])
    return out


def main(argv):
    if len(argv) < 3 or argv[1] not in ('read', 'roundtrip'):
        print(__doc__)
        return 2
    path = argv[2]
    if argv[1] == 'read':
        gr = read_file(path)
        print(json.dumps(stats(gr), indent=1))
        return 0
    data = open(path, 'rb').read()
    gr = read_file(path)
    back = write_file(gr)
    ok = back == data
    print('%s: %d bytes, round trip %s' % (os.path.basename(path), len(data), 'IDENTICAL' if ok else 'DIFFERENT'))
    if not ok:
        for i, (x, y) in enumerate(zip(data, back)):
            if x != y:
                print('first difference at', i)
                break
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
