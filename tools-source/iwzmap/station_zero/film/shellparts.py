"""shellparts: the authoring library of the Arcade's architecture (worker AC1, 28 Nov 2026; K1-CONSTRUCTION section 4.1).

Convex solids with bevels and chamfers as triangle soups per material, no hand-placed texture coordinates: the world exporter projects an uncoordinated
triangle by the material's size (blend_core.WorldBuilder.add), which is how a stock wall is textured. Units are inches, z up.

    s = Soup()
    s.add(MAT, column_shaft(x, y, 12, 80))
    s.flush(A, m, 'cols')            # one render-only mesh object per material

Every solid is oriented outward by its own centroid (all of them are convex), so no function here depends on a winding convention.
"""
import math
from collections import defaultdict

from studio import build as B


# ------------------------------------------------------------------------------------------------ plan polygons
def rect_poly(cx, cy, w, d, c=0.0):
    """a rectangle w x d centred on (cx, cy), the corners cut by c (an octagon when c > 0), counter-clockwise from above"""
    hx, hy = w / 2.0, d / 2.0
    if c <= 0.0:
        return [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)]
    return [(cx - hx + c, cy - hy), (cx + hx - c, cy - hy), (cx + hx, cy - hy + c), (cx + hx, cy + hy - c),
            (cx + hx - c, cy + hy), (cx - hx + c, cy + hy), (cx - hx, cy + hy - c), (cx - hx, cy - hy + c)]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _outward(tris, centre):
    """flip every triangle whose normal looks at the solid's centre"""
    out = []
    for t in tris:
        n = _cross(_sub(t[1], t[0]), _sub(t[2], t[0]))
        c = [(t[0][i] + t[1][i] + t[2][i]) / 3.0 - centre[i] for i in range(3)]
        if _dot(n, c) < 0.0:
            t = [t[0], t[2], t[1]]
        out.append([[round(v, 3) for v in p] for p in t])
    return out


def _centroid(pts):
    n = float(len(pts))
    return [sum(p[i] for p in pts) / n for i in range(3)]


def loft(rings, cap_bottom=True, cap_top=True):
    """rings [(z, polygon)], each polygon the same number of (x, y) points: the side quads between consecutive rings and fan caps"""
    tris, pts = [], []
    for k in range(len(rings) - 1):
        (z0, p0), (z1, p1) = rings[k], rings[k + 1]
        n = len(p0)
        for i in range(n):
            j = (i + 1) % n
            a, b, c, d = (p0[i][0], p0[i][1], z0), (p0[j][0], p0[j][1], z0), (p1[j][0], p1[j][1], z1), (p1[i][0], p1[i][1], z1)
            tris += [[a, b, c], [a, c, d]]
    for z, p in rings:
        pts += [(q[0], q[1], z) for q in p]
    for cap, (z, p) in ((cap_bottom, rings[0]), (cap_top, rings[-1])):
        if cap:
            c = (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p), z)
            for i in range(len(p)):
                tris.append([c, (p[i][0], p[i][1], z), (p[(i + 1) % len(p)][0], p[(i + 1) % len(p)][1], z)])
    return _outward(tris, _centroid(pts))


def box(x0, y0, z0, x1, y1, z1, skip=()):
    """a plain box; skip names faces left out: 'x0' 'x1' 'y0' 'y1' 'z0' 'z1'"""
    p = lambda x, y, z: (x, y, z)
    c = {'x0': [p(x0, y0, z0), p(x0, y1, z0), p(x0, y1, z1), p(x0, y0, z1)], 'x1': [p(x1, y0, z0), p(x1, y1, z0), p(x1, y1, z1), p(x1, y0, z1)],
         'y0': [p(x0, y0, z0), p(x1, y0, z0), p(x1, y0, z1), p(x0, y0, z1)], 'y1': [p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1)],
         'z0': [p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0)], 'z1': [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]}
    tris = []
    for k, q in c.items():
        if k not in skip:
            tris += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    return _outward(tris, ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0))


def bevel_box(x0, y0, z0, x1, y1, z1, c=1.0, top=None, bottom=0.0):
    """a box with its four vertical edges cut by c, the top rim bevelled by `top` (default c) and the bottom rim by `bottom`"""
    t = c if top is None else top
    w, d, cx, cy = x1 - x0, y1 - y0, (x0 + x1) / 2.0, (y0 + y1) / 2.0
    c = min(c, w / 2.0 - 0.01, d / 2.0 - 0.01)
    rings = []
    if bottom > 0:
        rings.append((z0, rect_poly(cx, cy, w - 2 * bottom, d - 2 * bottom, max(0.001, c - bottom))))
        rings.append((z0 + bottom, rect_poly(cx, cy, w, d, c)))
    else:
        rings.append((z0, rect_poly(cx, cy, w, d, c)))
    if t > 0:
        rings.append((z1 - t, rect_poly(cx, cy, w, d, c)))
        rings.append((z1, rect_poly(cx, cy, w - 2 * t, d - 2 * t, max(0.001, c - t))))
    else:
        rings.append((z1, rect_poly(cx, cy, w, d, c)))
    return loft(rings)


def strip(a, b, profile, skip_caps=False):
    """a convex profile [(d, z)] extruded along the plan segment a -> b; d is the offset along the left normal of the direction (so that a wall run from west
    to east with the room on its left has d positive into the room)"""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay) or 1.0
    nx, ny = -(by - ay) / L, (bx - ax) / L
    pts = [((ax + nx * d, ay + ny * d, z), (bx + nx * d, by + ny * d, z)) for d, z in profile]
    tris = []
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        tris += [[pts[i][0], pts[j][0], pts[j][1]], [pts[i][0], pts[j][1], pts[i][1]]]
    if not skip_caps:
        for k in (0, 1):
            ring = [p[k] for p in pts]
            c = _centroid(ring)
            for i in range(n):
                tris.append([c, ring[i], ring[(i + 1) % n]])
    allp = [q for p in pts for q in p]
    return _outward(tris, _centroid(allp))


def quad(p0, p1, p2, p3):
    """one flat quad as two triangles, the normal as the points wind (p0 p1 p2)"""
    return [[list(p0), list(p1), list(p2)], [list(p0), list(p2), list(p3)]]


def wall_rects(a0, a1, z0, z1, openings=()):
    """a wall face as rectangles [(a0, z0, a1, z1)] without the openings [(o0, o1, oz0, oz1)]"""
    cuts = sorted({a0, a1} | {o[0] for o in openings if a0 < o[0] < a1} | {o[1] for o in openings if a0 < o[1] < a1})
    out = []
    for s0, s1 in zip(cuts, cuts[1:]):
        mid = (s0 + s1) / 2.0
        covering = [o for o in openings if o[0] < mid < o[1]]
        if not covering:
            out.append((s0, z0, s1, z1))
            continue
        lo = max(min(o[2] for o in covering), z0)
        hi = min(max(o[3] for o in covering), z1)
        if lo > z0:
            out.append((s0, z0, s1, lo))
        if hi < z1:
            out.append((s0, hi, s1, z1))
    return out


def wall_face(axis, plane, a0, a1, z0, z1, facing, openings=()):
    """the face of a wall as triangles: axis 'x' = a wall running along x at y = plane, 'y' = running along y at x = plane; facing +1 / -1 = the side the face looks to"""
    tris = []
    for r0, rz0, r1, rz1 in wall_rects(a0, a1, z0, z1, openings):
        if axis == 'x':
            q = [(r0, plane, rz0), (r1, plane, rz0), (r1, plane, rz1), (r0, plane, rz1)]
            n = 1 if facing > 0 else -1
            tris += quad(*q) if n < 0 else quad(q[1], q[0], q[3], q[2])
        else:
            q = [(plane, r0, rz0), (plane, r1, rz0), (plane, r1, rz1), (plane, r0, rz1)]
            tris += quad(*q) if facing > 0 else quad(q[1], q[0], q[3], q[2])
    return tris


# ------------------------------------------------------------------------------------------------ the parts
def column_parts(x, y, rows=(), dmg=False):
    """the stock column of K1 section 2.4 (34 x 34 base 12 high; shaft 32 x 32 with 3-unit chamfers; a band 11 high; a collar 24 high; the cap up to the grid):
    -> {role: tris} with the roles base, shaft, band, upper, collar, cap"""
    c = 3.0
    out = {}
    out['base'] = loft([(0.0, rect_poly(x, y, 34.0, 34.0, c)), (10.0, rect_poly(x, y, 34.0, 34.0, c)), (12.0, rect_poly(x, y, 32.0, 32.0, c))])
    out['shaft'] = loft([(12.0, rect_poly(x, y, 32.0, 32.0, c)), (80.0, rect_poly(x, y, 32.0, 32.0, c))], cap_bottom=False, cap_top=False)
    out['band'] = loft([(80.0, rect_poly(x, y, 32.8, 32.8, c)), (80.8, rect_poly(x, y, 33.6, 33.6, c)), (90.2, rect_poly(x, y, 33.6, 33.6, c)),
                        (91.0, rect_poly(x, y, 32.8, 32.8, c))], cap_bottom=False, cap_top=False)
    out['upper'] = loft([(91.0, rect_poly(x, y, 32.0, 32.0, c)), (127.0, rect_poly(x, y, 32.0, 32.0, c))], cap_bottom=False, cap_top=False)
    out['collar'] = loft([(127.0, rect_poly(x, y, 32.0, 32.0, c)), (128.5, rect_poly(x, y, 35.0, 35.0, c)), (150.0, rect_poly(x, y, 35.0, 35.0, c)),
                          (151.5, rect_poly(x, y, 32.0, 32.0, c))], cap_bottom=False, cap_top=False)
    out['cap'] = loft([(151.5, rect_poly(x, y, 32.0, 32.0, c)), (243.8, rect_poly(x, y, 32.0, 32.0, c))], cap_bottom=False, cap_top=False)
    return out


def ibeam(a, b, z0, z1, flange=28.0, ft=3.0, web=4.0):
    """a girder along the plan segment a -> b between z0 (underside) and z1 (top): two flanges and a web, as three convex solids, + end plates left to the caller
    -> {'flange': tris, 'web': tris}"""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay) or 1.0
    t = ((bx - ax) / L, (by - ay) / L)
    n = (-t[1], t[0])
    flanges, webs = [], []

    def solid(d0, d1, zz0, zz1):
        prof = [(d0, zz0), (d1, zz0), (d1, zz1), (d0, zz1)]
        return strip(a, b, prof)
    h = flange / 2.0
    flanges += solid(-h, h, z0, z0 + ft)
    flanges += solid(-h, h, z1 - ft, z1)
    webs += solid(-web / 2.0, web / 2.0, z0 + ft, z1 - ft)
    return {'flange': flanges, 'web': webs}


class Soup:
    """triangles per material, flushed as render-only mesh objects"""

    def __init__(self):
        self.t = defaultdict(list)

    def add(self, mat, tris):
        self.t[mat] += tris

    def count(self):
        return sum(len(v) for v in self.t.values())

    def flush(self, m, prefix, layer='shell', mode='render', cap=20000):
        """-> number of mesh objects written"""
        n = 0
        for mat, tris in sorted(self.t.items()):
            tag = mat.replace('w/', '').replace('*', 's')
            for k in range(0, len(tris), cap):
                B.mesh(m, mat, tris=tris[k:k + cap], mode=mode, layer=layer, id='%s_%s%s' % (prefix, tag, '' if k == 0 else '_%d' % (k // cap)))
                n += 1
        return n
