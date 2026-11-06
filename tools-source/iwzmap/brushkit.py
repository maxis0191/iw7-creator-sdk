"""Brush library for generated IW7 worlds: textured quads, boxes, wedges, banded walls with openings, stairs.

Everything is axis aligned in plan (x east, y north, z up). A Builder owns one mapgen.Mesh (render surfaces and
collision triangles) plus the solid footprints the nav generator must avoid. Materials are looked up in a material
table (sz2_materials.MATERIALS): each entry gives the material asset and its texture world size (units covered by
one repeat of the texture in u and v), so every surface is mapped at real scale and aligned to world planes.

Surfaces are grouped per material and zone (render surface key "<material>|<zone>"); each quad points at one
lightmap texel picked by (zone, tone) through the builder's lm() callback.
"""
import math
import mapgen

UP = (0.0, 0.0, 1.0)


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    l = math.sqrt(dot(a, a))
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-9 else (0.0, 0.0, 1.0)


def face_tangent(n):
    """u direction of a face: viewer-right for walls (texture upright), +x for floors and ceilings."""
    if abs(n[2]) > 0.7:
        t = (1.0, 0.0, 0.0)
        t = sub(t, mul(n, dot(t, n)))
        return norm(t)
    h = norm((n[0], n[1], 0.0))
    return norm(cross((-h[0], -h[1], 0.0), UP))


class Builder:
    def __init__(self, materials, lm):
        self.materials = materials        # key -> dict(path, su, sv, ...)
        self.lm = lm                      # (zone, tone) -> (u, v) lightmap texel
        self.mesh = mapgen.Mesh()
        self.blockers = []                # (x0, y0, x1, y1, z0, z1): solid footprints for the nav generator
        self.used = {}                    # material key -> quads
        self.quads = 0

    # ------------------------------------------------------------------ primitives
    def quad(self, mat, zone, pts, n=None, t=None, uvs=None, collide=True, tone='mid', uvoff=(0.0, 0.0), uvscale=1.0):
        """pts: 4 points counter-clockwise seen from the front (normal) side. uvs: explicit per-point (u, v);
        otherwise world aligned with the material's texture world size (su, sv) and offsets in repeats."""
        if n is None:
            n = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
        if t is None:
            t = face_tangent(n)
        spec = self.materials[mat]
        if uvs is None:
            b = cross(n, t)
            su, sv = spec['su'] * uvscale, spec['sv'] * uvscale
            uvs = [(dot(p, t) / su + uvoff[0], -dot(p, b) / sv + uvoff[1]) for p in pts]
        key = '%s|%s' % (spec['path'], zone)
        self.mesh.quad_uv(key, pts, uvs, n, t, self.lm(zone, spec.get('tone', tone) if tone == 'mid' else tone),
                          collide=collide and spec.get('collide', True))
        self.used[mat] = self.used.get(mat, 0) + 1
        self.quads += 1

    def collision_quad(self, pts):
        p0, p1, p2, p3 = pts
        self.mesh.col += [(p0, p1, p2), (p0, p2, p3)]

    def collision_box(self, mn, mx, nav=True):
        (x0, y0, z0), (x1, y1, z1) = mn, mx
        c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for k in range(4):
            (ax, ay), (bx, by) = c[k], c[(k + 1) % 4]
            self.collision_quad([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
        self.collision_quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        if nav:
            self.blockers.append((x0, y0, x1, y1, z0, z1))

    def box(self, mn, mx, mat, zone, collide=True, skip=(), nav=None, tone='mid', uvoff=(0.0, 0.0), uvscale=1.0):
        """Solid axis-aligned box seen from outside. mat: material key or dict face -> key
        (faces: top bottom north south east west, 'side' for the four walls). nav: block nav cells
        (default: solid boxes taller than a step block)."""
        (x0, y0, z0), (x1, y1, z1) = mn, mx
        if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
            return
        faces = {
            'top':    ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
            'bottom': ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)),
            'south':  ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
            'north':  ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),
            'west':   ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),
            'east':   ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
        }
        for name, (pts, n) in faces.items():
            if name in skip:
                continue
            m = mat
            if isinstance(mat, dict):
                m = mat.get(name) or (mat.get('side') if name not in ('top', 'bottom') else None) or mat.get('all')
                if m is None:
                    continue
            # side faces: the quad winding above is counter-clockwise from outside
            self.quad(m, zone, pts, n=tuple(float(c) for c in n), collide=False, tone=tone, uvoff=uvoff, uvscale=uvscale)
        if collide:
            self.collision_box(mn, mx, nav=False)
        if nav is None:
            nav = collide and (z1 - z0) > 18
        if nav:
            self.blockers.append((x0, y0, x1, y1, z0, z1))

    def slab_x(self, x0, x1, y, z0, z1, depth, mat, zone, facing, **kw):
        """Thin box protruding `depth` from the plane y in direction facing (+1 / -1), along x."""
        ya, yb = (y, y + depth) if facing > 0 else (y - depth, y)
        self.box((x0, ya, z0), (x1, yb, z1), mat, zone, **kw)

    def slab_y(self, y0, y1, x, z0, z1, depth, mat, zone, facing, **kw):
        xa, xb = (x, x + depth) if facing > 0 else (x - depth, x)
        self.box((xa, y0, z0), (xb, y1, z1), mat, zone, **kw)

    # ------------------------------------------------------------------ walls
    def wall_plane(self, zone, axis, fixed, facing, s0, s1, z0, z1, mat, collide=True, tone='mid', vtop=None):
        """One vertical rectangle. axis 'x': runs along x at y=fixed; 'y': along y at x=fixed. facing: the
        normal's sign along the other axis. vtop: world z at which the texture's top row sits (tile alignment)."""
        if s1 - s0 <= 0.01 or z1 - z0 <= 0.01:
            return
        if axis == 'x':
            n = (0.0, float(facing), 0.0)
            a, b = (s1, s0) if facing > 0 else (s0, s1)
            pts = [(a, fixed, z0), (b, fixed, z0), (b, fixed, z1), (a, fixed, z1)]
        else:
            n = (float(facing), 0.0, 0.0)
            a, b = (s0, s1) if facing > 0 else (s1, s0)
            pts = [(fixed, a, z0), (fixed, b, z0), (fixed, b, z1), (fixed, a, z1)]
        spec = self.materials[mat]
        voff = (vtop / spec['sv']) if vtop is not None else 0.0
        self.quad(mat, zone, pts, n=n, collide=collide, tone=tone, uvoff=(0.0, voff))

    def wall_sloped(self, zone, axis, fixed, facing, s0, s1, za0, za1, zb0, zb1, mat, collide=True, tone='mid'):
        """Vertical quad whose bottom runs za0 -> za1 and top zb0 -> zb1 from s0 to s1 (stair walls)."""
        if axis == 'x':
            n = (0.0, float(facing), 0.0)
            P = lambda s, z: (s, fixed, z)
        else:
            n = (float(facing), 0.0, 0.0)
            P = lambda s, z: (fixed, s, z)
        pts = [P(s0, za0), P(s1, za1), P(s1, zb1), P(s0, zb0)]
        # make it counter-clockwise seen from the normal side
        if dot(cross(sub(pts[1], pts[0]), sub(pts[3], pts[0])), n) < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        self.quad(mat, zone, pts, n=n, collide=collide, tone=tone)


def spans_minus(s0, s1, holes):
    """[s0, s1] minus the given (a, b) intervals -> list of (a, b)."""
    out, cur = [], s0
    for a, b in sorted(holes):
        a, b = max(a, s0), min(b, s1)
        if b <= a:
            continue
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if cur < s1:
        out.append((cur, s1))
    return out
