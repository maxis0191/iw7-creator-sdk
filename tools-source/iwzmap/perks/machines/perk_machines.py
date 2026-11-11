"""The four new Station Zero perk machines (06-PERKS.md section 2) built in Blender (headless): geometry, UVs onto the
art of make_machine_art.py, one glb + materials.json per machine for env-model t7_env_port.py, and review renders.

  blender -b --factory-startup -P perk_machines.py -- --art <art dir> --out <authored dir> [--renders <dir>] [--only bakers,...]
         [--roundtrip <port dir>]   (render the game models read back from the port dump instead of the Blender meshes)

Model space in inches (Blender metres = inches * 0.0254; mesh_glb maps Blender axes 1:1 to game axes): origin at the floor
centre, front facing +X, width along Y, Z up. Footprint about 32..40 x 40, height 85..90 like the stock machines.
Models: iwz_perk_machine_bakers, _voyage, _grudge, _double. Every surface is opaque or emissive (no glass: the IW7
glass template glowed lavender in g27); the drum and globe show their contents painted with glass highlights.
"""
import argparse
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

INCH = 0.0254
MACHINES = ['bakers', 'voyage', 'grudge', 'double']

# ---------------------------------------------------------------- materials
# kind: paint (tileable albedo), metal (dark albedo + specular colour = F0), atlas (machine atlas), glow (atlas + emissive)
COMMON = {
    'iwz_pk_chrome': dict(kind='metal', spec='spec_chrome.png', rough=0.18, uv=16),
    'iwz_pk_brass': dict(kind='metal', spec='spec_brass.png', rough=0.32, uv=16),
    'iwz_pk_black': dict(kind='paint', albedo='enamel_black.png', rough=0.4, uv=24),
}
PER = {
    'bakers': {'iwz_pk_bak_red': dict(kind='paint', albedo='enamel_red.png', rough=0.26, uv=24),
               'iwz_pk_bak_cream': dict(kind='paint', albedo='enamel_cream.png', rough=0.32, uv=24),
               'iwz_pk_bak_kraft': dict(kind='paint', albedo='kraft.png', rough=0.8, uv=10)},
    'voyage': {'iwz_pk_voy_walnut': dict(kind='paint', albedo='walnut.png', rough=0.35, uv=20)},
    'grudge': {'iwz_pk_gru_green': dict(kind='paint', albedo='enamel_green.png', rough=0.35, uv=24),
               'iwz_pk_gru_yellow': dict(kind='paint', albedo='enamel_yellow.png', rough=0.35, uv=24)},
    'double': {'iwz_pk_dbl_turq': dict(kind='paint', albedo='enamel_turq.png', rough=0.3, uv=24)},
}
SHORT = {'bakers': 'bak', 'voyage': 'voy', 'grudge': 'gru', 'double': 'dbl'}


def mat_table(m):
    t = dict(COMMON)
    t.update(PER[m])
    s = SHORT[m]
    t['iwz_pk_%s_atlas' % s] = dict(kind='atlas', albedo='%s_atlas.png' % m, rough=0.45)
    t['iwz_pk_%s_glow' % s] = dict(kind='glow', albedo='%s_atlas.png' % m, emissive='%s_glow_e.png' % m, rough=0.15)
    return t


# ---------------------------------------------------------------- builder
class B:
    def __init__(self, m, art):
        self.m = m
        self.mats = mat_table(m)
        self.names = list(self.mats)
        self.idx = {n: i for i, n in enumerate(self.names)}
        r = json.load(open(os.path.join(art, m + '_rects.json')))
        self.S, self.rects = r['size'], r['rects']
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.verify()
        self.mapped = set()
        s = SHORT[m]
        self.A, self.G = 'iwz_pk_%s_atlas' % s, 'iwz_pk_%s_glow' % s

    def mat(self, n):
        return self.idx[n if n in self.idx else n]

    def uvrect(self, name):
        x, y, w, h = self.rects[name]
        S = self.S
        return (x / S, 1 - (y + h) / S, (x + w) / S, 1 - y / S)

    def mark(self):
        # a set, not an index: BMesh reuses the slots of vertices a bevel deleted, so new vertices are not all at the end
        return set(self.bm.verts)

    def since(self, n0):
        return [v for v in self.bm.verts if v not in n0]

    def xform(self, n0, mat):
        for v in self.since(n0):
            v.co = mat @ v.co

    def rot(self, n0, axis, deg, pivot):
        p = Vector(pivot) * INCH
        self.xform(n0, Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p))

    def box(self, mat, x0, x1, y0, y1, z0, z1, bevel=0.0):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r['verts']:
            v.co.x = (x0 if v.co.x < 0 else x1) * INCH
            v.co.y = (y0 if v.co.y < 0 else y1) * INCH
            v.co.z = (z0 if v.co.z < 0 else z1) * INCH
        faces = list({f for v in r['verts'] for f in v.link_faces})
        for f in faces:
            f.material_index = self.mat(mat)
            f.smooth = False
        if bevel:
            bmesh.ops.bevel(self.bm, geom=list({e for f in faces for e in f.edges}), offset=bevel * INCH, segments=1,
                            affect='EDGES', material=self.mat(mat))

    def quad(self, mat, corners, rect=None, uvs=None):
        """Textured face; corners counter-clockwise seen from the front: bottom-left, bottom-right, top-right, top-left."""
        vs = [self.bm.verts.new(tuple(c * INCH for c in p)) for p in corners]
        f = self.bm.faces.new(vs)
        f.material_index = self.mat(mat)
        f.smooth = False
        if rect:
            u0, v0, u1, v1 = self.uvrect(rect)
            uvs = uvs or ((0, 0), (1, 0), (1, 1), (0, 1))
            for loop, (a, b) in zip(f.loops, uvs):
                loop[self.uv].uv = (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
            self.mapped.add(f)
        return f

    def front(self, mat, rect, x, y0, y1, z0, z1):
        """Decal facing +X; y0 is the viewer's left."""
        return self.quad(mat, [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], rect)

    def side(self, mat, rect, y, x0, x1, z0, z1, sign=1):
        """Decal facing +Y (sign 1, left edge at x1) or -Y (sign -1, left edge at x0)."""
        if sign > 0:
            return self.quad(mat, [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)], rect)
        return self.quad(mat, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], rect)

    def lathe(self, mat, prof, seg, cx=0.0, cy=0.0, rect=None, closed=False, smooth=True, phase=0.0):
        """Surface of revolution about the vertical line (cx, cy): prof = [(r, z)] ordered so the outer surface runs
        counter-clockwise in the (r, z) plane (bottom to top outside). r = 0 ends become poles; closed joins the last
        point to the first (rings). rect maps u around (phase 0 = +X), v along the profile length."""
        n0 = self.mark()
        pts = list(prof) + ([prof[0]] if closed else [])
        L = [0.0]
        for a, b in zip(pts, pts[1:]):
            L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        rings = []
        for (r, z) in pts:
            if r < 1e-6:
                rings.append(None)
                continue
            ring = []
            for k in range(seg):
                a = phase + 2 * math.pi * k / seg
                ring.append(self.bm.verts.new(((cx + r * math.cos(a)) * INCH, (cy + r * math.sin(a)) * INCH, z * INCH)))
            rings.append(ring)
        poles = {}
        for i, (r, z) in enumerate(pts):
            if rings[i] is None:
                poles[i] = self.bm.verts.new((cx * INCH, cy * INCH, z * INCH))
        uvr = self.uvrect(rect) if rect else None
        mi = self.mat(mat)
        for i in range(len(pts) - 1):
            ra, rb = rings[i], rings[i + 1]
            va, vb = L[i] / L[-1], L[i + 1] / L[-1]
            for k in range(seg):
                k1 = (k + 1) % seg
                ua, ub = k / seg, (k + 1) / seg
                if ra is None and rb is None:
                    continue
                if ra is None:
                    vs, uv = [poles[i], rb[k1], rb[k]], [((ua + ub) / 2, va), (ub, vb), (ua, vb)]
                elif rb is None:
                    vs, uv = [ra[k], ra[k1], poles[i + 1]], [(ua, va), (ub, va), ((ua + ub) / 2, vb)]
                else:
                    vs, uv = [ra[k], ra[k1], rb[k1], rb[k]], [(ua, va), (ub, va), (ub, vb), (ua, vb)]
                try:
                    f = self.bm.faces.new(vs)
                except ValueError:
                    continue
                f.material_index = mi
                f.smooth = smooth
                if uvr:
                    for loop, (a, b) in zip(f.loops, uv):
                        loop[self.uv].uv = (uvr[0] + (uvr[2] - uvr[0]) * a, uvr[1] + (uvr[3] - uvr[1]) * b)
                    self.mapped.add(f)
        return n0

    def lathe_x(self, mat, prof, seg, at, rect=None, closed=False, smooth=True):
        """The same revolution with its axis along +X (prof z = distance along +X from at)."""
        n0 = self.lathe(mat, prof, seg, rect=rect, closed=closed, smooth=smooth)
        self.xform(n0, Matrix.Translation(Vector(at) * INCH) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
        return n0

    def disc_x(self, mat, x, cy, cz, r, seg, rect):
        """Flat disc facing +X with planar UVs from the rect (the image's left at -Y)."""
        u0, v0, u1, v1 = self.uvrect(rect)
        c = self.bm.verts.new((x * INCH, cy * INCH, cz * INCH))
        ring = [self.bm.verts.new((x * INCH, (cy + r * math.cos(2 * math.pi * k / seg)) * INCH,
                                   (cz + r * math.sin(2 * math.pi * k / seg)) * INCH)) for k in range(seg)]
        for k in range(seg):
            a, b = ring[k], ring[(k + 1) % seg]
            f = self.bm.faces.new([c, a, b])
            f.material_index = self.mat(mat)
            f.smooth = False
            for loop in f.loops:
                p = loop.vert.co / INCH
                loop[self.uv].uv = (u0 + (u1 - u0) * (p.y - cy + r) / (2 * r), v0 + (v1 - v0) * (p.z - cz + r) / (2 * r))
            self.mapped.add(f)

    def cyl(self, mat, p0, p1, r, seg=12):
        ax = Vector(p1) - Vector(p0)
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r * INCH,
                                    radius2=r * INCH, depth=ax.length * INCH)
        q = Vector((0, 0, 1)).rotation_difference(ax.normalized())
        mid = (Vector(p0) + Vector(p1)) / 2 * INCH
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(mid) @ q.to_matrix().to_4x4(), verts=res['verts'])
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.material_index = self.mat(mat)
            f.smooth = False

    def sphere(self, mat, c, r, seg=16, rings=8, rect=None):
        prof = [(r * math.sin(math.pi * i / rings), c[2] - r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
        return self.lathe(mat, prof, seg, c[0], c[1], rect=rect)

    def finish(self, name):
        bm = self.bm
        for f in bm.faces:
            if f in self.mapped:
                continue
            d = self.mats[self.names[f.material_index]].get('uv', 24.0)
            nx, ny, nz = (abs(v) for v in f.normal)
            for loop in f.loops:
                co = loop.vert.co / INCH
                u, v = ((co.y, co.z) if nx >= max(ny, nz) else (co.x, co.z) if ny >= nz else (co.x, co.y))
                loop[self.uv].uv = (u / d, v / d)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        for n in self.names:
            me.materials.append(bpy.data.materials.get(n) or bpy.data.materials.new(n))
        return ob


# ---------------------------------------------------------------- the machines
def bakers(b):
    A, G = b.A, b.G
    R, C, K = 'iwz_pk_bak_red', 'iwz_pk_bak_cream', 'iwz_pk_chrome'
    b.box(K, -14.5, 14.5, -18.5, 18.5, 0, 3, bevel=0.3)                      # chrome kick plate
    b.box(R, -14, 14, -18, 18, 3, 40, bevel=0.6)                             # red enamel counter body
    b.box(K, -14.25, 13.8, -18.25, 18.25, 30, 31)                            # chrome band round sides and back
    for y0, y1 in ((-17.2, -12.6), (12.6, 17.2)):                            # cream pilasters either side of the panel
        b.box(C, 13.6, 14.5, y0, y1, 3, 40, bevel=0.3)
    b.front(A, 'front', 14.03, -11, 11, 4.6, 35.4)                           # doughnut emblem panel
    for y in (-11.6, 11.6):                                                  # chrome frame of the panel
        b.box(K, 13.8, 14.3, y - 0.5, y + 0.5, 4, 36)
    for z in (4.0, 35.4):
        b.box(K, 13.8, 14.3, -12.1, 12.1, z - 0.4, z + 0.6)
    b.box(C, -15, 16.5, -19, 19, 40, 42.5, bevel=0.5)                        # counter top
    b.box(K, -15.2, 16.7, -19.2, 19.2, 39.5, 40.4)                           # its chrome edge
    b.box(C, -14, -3, -17, 17, 42.5, 72, bevel=0.4)                          # back tower
    b.front(A, 'tower', -2.97, -17, 17, 42.5, 72)                            # candy stripes
    b.box(R, -12, 2, -19.5, 19.5, 72, 85.5, bevel=0.6)                       # lit marquee box
    b.front(G, 'sign', 2.04, -18.3, 18.3, 73.0, 84.3)
    b.box(K, -12.3, 2.3, -19.8, 19.8, 85.5, 86.3)
    for k in range(9):                                                       # chaser bulbs along the marquee top
        b.sphere(G, (2.0, -17.0 + k * 34.0 / 8, 87.1), 0.8, 8, 4, rect='bulb')
    # striped awning over the drum: top and underside, valance face
    x0, z0, x1, z1 = -3.0, 71.6, 11.0, 65.6
    b.quad(R, [(x1, -19, z1), (x1, 19, z1), (x0, 19, z0), (x0, -19, z0)])
    b.quad(C, [(x0, -19, z0 - 0.5), (x0, 19, z0 - 0.5), (x1, 19, z1 - 0.5), (x1, -19, z1 - 0.5)])
    b.front(A, 'awning', x1 + 0.01, -19, 19, z1 - 2.5, z1)
    for y in (-18.6, 18.6):                                                   # awning arms
        b.cyl(K, (x0, y, z0 - 0.6), (x1 - 0.5, y, z1 - 0.8), 0.25, 6)
    # glass drum of sugared jelly drops (lit inside) on a chrome base, chrome cap and knob, crank on its side
    dx, dy = 4.0, -5.0
    b.lathe(K, [(0, 42.5), (9.8, 42.5), (9.8, 45.4), (9.0, 46.2), (0, 46.2)], 32, dx, dy)
    b.lathe(G, [(9.0, 46.0), (9.0, 61.2)], 32, dx, dy, rect='drum')
    b.lathe(K, [(0, 61.0), (9.6, 61.0), (9.6, 62.2), (7.0, 63.8), (2.2, 64.4), (1.2, 65.3), (1.7, 66.4), (0, 66.9)], 32, dx, dy)
    for z in (49.0, 58.0):                                                    # drum hoops
        b.lathe(K, [(9.05, z), (9.35, z), (9.35, z + 0.6), (9.05, z + 0.6)], 32, dx, dy, closed=True)
    b.cyl(K, (dx, dy + 9.0, 54), (dx, dy + 11.6, 54), 0.55, 8)
    b.cyl(K, (dx, dy + 11.6, 54), (dx, dy + 11.6, 58.5), 0.45, 8)
    b.cyl('iwz_pk_black', (dx - 1.0, dy + 11.6, 58.8), (dx + 1.0, dy + 11.6, 58.8), 0.85, 10)
    # chrome chute from the drum's foot down over the counter's edge into a paper bag clipped at its mouth
    b.lathe_x(K, [(0, 0), (3.0, 0), (3.0, 1.8), (2.4, 2.6), (0, 2.6)], 16, (dx + 8.4, dy, 47.6))   # outlet boss
    b.cyl(K, (dx + 9.0, dy, 47.5), (19.4, dy, 45.0), 2.0, 14)                                 # chute pipe
    b.lathe(K, [(2.0, 41.6), (2.9, 41.6), (2.9, 46.0), (2.0, 46.0)], 16, 19.4, dy, closed=True)   # its mouth
    b.box(K, 16.4, 23.2, -10.2, 0.2, 30.2, 31.0, bevel=0.2)                   # bag shelf bracket
    b.box(K, 16.4, 17.2, -10.2, 0.2, 26.0, 31.0)
    b.box('iwz_pk_bak_kraft', 17.0, 22.4, -9.6, -0.4, 31.0, 42.0)
    b.front(A, 'bag', 22.43, -9.6, -0.4, 31.0, 42.0)
    # coin box with INSERT COIN plate and the red push button
    b.box(K, 11.5, 15.5, 8.8, 16.6, 42.5, 47.8, bevel=0.3)
    b.front(A, 'coin', 15.53, 9.1, 16.3, 45.8, 47.6)
    b.lathe_x(R, [(0, 0), (1.0, 0), (1.0, 0.7), (0.7, 1.0), (0, 1.0)], 12, (15.5, 12.7, 44.0))
    # mechanical flip counter 01..13 (lit digits) with a brass bell that rings on 13
    b.box('iwz_pk_black', -3.0, 2.6, 6.0, 19.6, 50.0, 62.4, bevel=0.4)
    b.box(K, 2.4, 2.9, 6.0, 19.6, 49.6, 50.6)
    b.box(K, 2.4, 2.9, 6.0, 19.6, 61.8, 62.8)
    b.front(G, 'counter', 2.93, 6.1, 19.5, 51.2, 61.2)
    b.lathe('iwz_pk_brass', [(0, 47.8), (3.0, 47.8), (3.0, 48.4), (2.7, 49.2), (2.1, 50.6), (1.0, 51.4), (0.4, 51.5),
                             (0.4, 52.3), (0.7, 52.5), (0, 52.8)], 20, 13.2, 12.7)     # desk bell that rings on 13


def voyage(b):
    A, G = b.A, b.G
    W, Br = 'iwz_pk_voy_walnut', 'iwz_pk_brass'
    b.box(W, -15, 15.5, -20, 20, 0, 6, bevel=0.6)                             # plinth
    b.box(Br, -15.2, 15.7, -20.2, 20.2, 0, 1.2)                               # brass kick strip
    b.box(W, -13, 9.5, -18.5, 18.5, 6, 74, bevel=0.5)                         # cabinet
    b.box(W, 9.5, 13, -18.5, 18.5, 6, 33.4, bevel=0.4)                        # lower front
    b.box(W, 9.5, 13.4, -18.5, 18.5, 33.4, 39.2, bevel=0.3)                   # rail carrying FOR THE JOURNEY (gilt)
    b.front(A, 'journey', 13.43, -15.6, 15.6, 33.8, 38.8)
    b.box(W, 9.5, 13, -18.5, -15, 39.2, 70)                                   # window jambs
    b.box(W, 9.5, 13, 15, 18.5, 39.2, 70)
    b.box(W, 9.5, 13.4, -18.5, 18.5, 70, 74, bevel=0.3)                       # top rail
    b.front(G, 'velvet', 9.53, -15, 15, 39.2, 70)                             # lit velvet back of the display case
    b.box(W, 9.5, 12.6, -15, 15, 39.2, 40.3)                                  # shelves
    b.box(W, 9.5, 12.6, -15, 15, 54.4, 55.5)
    # round tins of dusted travel sweets, lids to the front; one open tin per shelf shows the sweets
    lids = [['tin0', 'tin3', 'tin1'], ['tin2', 'tin1', 'tin3']]
    for row, zc in enumerate((44.9, 60.1)):
        for col, yc in enumerate((-9.8, 0.0, 9.8)):
            n0 = b.lathe(Br, [(0, 0), (4.3, 0), (4.3, 2.4), (4.45, 2.6), (4.45, 2.9), (0, 2.9)], 24)
            b.xform(n0, Matrix.Translation(Vector((9.6, yc, zc)) * INCH) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
            b.disc_x(A, 12.53, yc, zc, 4.0, 24, lids[row][col])
    # brass grille in front of the tins
    y = -14.0
    while y <= 14.01:
        b.cyl(Br, (12.9, y, 39.3), (12.9, y, 69.9), 0.22, 6)
        y += 2.33
    for z in (47.2, 62.6):
        b.cyl(Br, (12.9, -15, z), (12.9, 15, z), 0.28, 6)
    # destination dial: brass bezel, face, pointer set to TERMINUS, hub
    zc = 22.0
    b.lathe_x(Br, [(8.8, 0.0), (10.3, 0.0), (10.5, 0.8), (10.0, 1.4), (8.8, 1.4)], 36, (13.0, 0, zc), closed=True)
    b.disc_x(A, 13.05, 0, zc, 8.9, 36, 'dial')
    n0 = b.mark()
    b.box(Br, 13.2, 13.55, -0.3, 0.3, zc, zc + 7.4)
    b.rot(n0, 'X', 60, (13.3, 0, zc))
    b.cyl(Br, (13.0, 0, zc), (14.1, 0, zc), 1.0, 12)
    b.box(Br, 13.0, 16.2, -4.5, 4.5, 7.4, 8.4, bevel=0.2)                    # delivery tray
    b.box(Br, 15.6, 16.2, -4.5, 4.5, 8.4, 10.2)
    b.box(Br, 13.0, 16.2, -4.5, -4.0, 8.4, 10.2)
    b.box(Br, 13.0, 16.2, 4.0, 4.5, 8.4, 10.2)
    # buying: brass plate PENNY IN THE SLOT / PULL FOR YOUR TIN, a coin slot and a pull handle right of the dial
    b.box(Br, 13.0, 13.3, 11.4, 16.8, 25.0, 31.6, bevel=0.1)
    b.front(A, 'buy', 13.33, 11.6, 16.6, 30.0, 31.3)
    b.box('iwz_pk_black' if 'iwz_pk_black' in b.idx else W, 13.3, 13.45, 13.7, 14.7, 26.6, 29.2)
    b.cyl(Br, (13.0, 14.2, 16.0), (16.0, 14.2, 16.0), 0.45, 8)
    b.lathe_x(Br, [(0, 0), (1.2, 0), (1.2, 1.8), (0, 1.8)], 12, (16.0, 14.2, 16.0))
    # pilasters with brass caps
    for ys in (-17.4, 17.4):
        b.lathe(W, [(0, 6), (1.5, 6), (1.5, 74), (0, 74)], 12, 12.6, ys)
        for z in (6.0, 71.6):
            b.lathe(Br, [(0, z), (1.9, z), (1.9, z + 2.4), (0, z + 2.4)], 12, 12.6, ys)
    # raised side panels
    for s in (-1, 1):
        y0, y1 = (18.5, 19.1) if s > 0 else (-19.1, -18.5)
        b.box(W, -10, 6, y0, y1, 12, 32, bevel=0.25)
        b.box(W, -10, 6, y0, y1, 40, 68, bevel=0.25)
        yb = (y1 + 0.15) if s > 0 else (y0 - 0.15)
        for z0_, z1_ in ((12, 32), (40, 68)):                                 # brass beading round each panel
            b.box(Br, -10.3, 6.3, min(yb, yb - s * 0.4), max(yb, yb - s * 0.4), z0_ - 0.3, z0_ + 0.2)
            b.box(Br, -10.3, 6.3, min(yb, yb - s * 0.4), max(yb, yb - s * 0.4), z1_ - 0.2, z1_ + 0.3)
            b.box(Br, -10.3, -9.8, min(yb, yb - s * 0.4), max(yb, yb - s * 0.4), z0_, z1_)
            b.box(Br, 5.8, 6.3, min(yb, yb - s * 0.4), max(yb, yb - s * 0.4), z0_, z1_)
    # cornice, brass strip, crest sign board with the lit gilt name, brass finials
    b.box(W, -14, 14.4, -19.8, 19.8, 74, 76.6, bevel=0.5)
    b.box(Br, -14.1, 14.5, -19.9, 19.9, 74.9, 75.5)
    b.box(W, -3, 3.5, -19.0, 19.0, 76.6, 88.0, bevel=0.4)
    b.front(G, 'sign', 3.53, -18.0, 18.0, 77.3, 87.3)
    for ys in (-18.2, 18.2):
        b.sphere(Br, (0.25, ys, 89.0), 1.0, 12, 6)


def grudge(b):
    A, G = b.A, b.G
    Gr, Y, K = 'iwz_pk_gru_green', 'iwz_pk_gru_yellow', 'iwz_pk_chrome'
    b.box(Gr, -17, 17, -18, 18, 0, 13, bevel=0.8)                             # plinth: lit name, crown stencils
    b.box('iwz_pk_black', 17.0, 17.6, -17.2, 17.2, 1.2, 12.0)
    b.front(G, 'sign', 17.63, -16.8, 16.8, 1.7, 11.5)
    b.side(A, 'crown', 18.03, -5.8, 5.8, 0.6, 12.8, 1)
    b.side(A, 'crown', -18.03, -5.8, 5.8, 0.6, 12.8, -1)
    b.quad(A, [(-17.03, 9.5, 1.0), (-17.03, -9.5, 1.0), (-17.03, -9.5, 12.6), (-17.03, 9.5, 12.6)], 'tag')
    b.box(Y, -15, 15, -15, 15, 13, 14.6, bevel=0.4)
    n_col = b.mark()
    b.lathe(Y, [(0, 14.6), (8.0, 14.6), (5.8, 17.0), (4.8, 19.0), (4.8, 30.4), (6.4, 32.2), (6.4, 33.2), (0, 33.2)], 20)
    b.rot(n_col, 'X', -4.0, (0, 0, 14.6))
    # the head, set crooked: collar, cast body with the sprayed-over face, coin plate, crank, chute; lit globe; cap
    n_head = b.mark()
    b.lathe(Gr, [(0, 33.0), (9.0, 33.0), (10.2, 34.4), (10.2, 35.2), (0, 35.2)], 24)
    b.box(Gr, -10, 10, -10, 10, 35.2, 56.0, bevel=1.2)
    b.box(Y, -10.3, 10.3, -10.3, 10.3, 35.2, 36.6)
    b.box(Y, -10.3, 10.3, -10.3, 10.3, 54.6, 56.0)
    b.disc_x(A, 10.06, 0, 48.6, 6.0, 28, 'face')
    b.lathe_x(Y, [(5.9, 0.0), (6.7, 0.0), (6.7, 0.4), (5.9, 0.4)], 28, (10.0, 0, 48.6), closed=True)
    b.front(A, 'coin', 10.06, -4.3, 4.3, 36.9, 41.9)
    b.side(A, 'tag', 10.06, -8, 8, 39.5, 49.4, 1)
    b.side(A, 'tag', -10.06, -8, 8, 39.5, 49.4, -1)
    b.lathe_x(K, [(0, 0), (2.1, 0), (2.1, 1.4), (1.7, 3.0), (0, 3.0)], 16, (10.0, -2.2, 39.4))      # crank
    b.box(K, 12.6, 13.5, -7.6, 3.2, 38.6, 40.2, bevel=0.25)
    b.lathe_x('iwz_pk_black', [(0, 0), (0.9, 0), (0.9, 2.2), (0, 2.2)], 10, (13.5, -6.8, 39.4))
    b.box(K, 10.0, 11.8, 5.2, 9.2, 37.0, 42.2, bevel=0.3)                    # chute flap
    b.lathe(K, [(0, 56.0), (10.6, 56.0), (11.1, 57.4), (10.3, 58.9), (0, 58.9)], 32)
    R, zc = 13.4, 70.6
    t0, t1 = math.acos((zc - 58.6) / R), math.acos((zc - 81.6) / R)
    prof = [(R * math.sin(t0 + (t1 - t0) * i / 10), zc - R * math.cos(t0 + (t1 - t0) * i / 10)) for i in range(11)]
    b.lathe(G, prof, 32, rect='globe')
    b.lathe(Y, [(7.4, 81.0), (8.4, 81.0), (8.4, 82.0), (7.4, 82.0)], 24, closed=True)
    b.lathe(Gr, [(0, 81.8), (8.0, 81.8), (8.2, 82.8), (7.4, 84.6), (5.0, 86.2), (2.2, 87.0), (0, 87.1)], 24)
    b.sphere(G, (0, 0, 88.3), 1.4, 12, 6, rect='bulb')
    b.xform(n_head, Matrix.Translation(Vector((0, 0, 33.0)) * INCH) @ Matrix.Scale(1.1, 4) @
            Matrix.Translation(Vector((0, 0, -33.0)) * INCH))
    b.rot(n_head, 'Z', 12.0, (0, 0, 0))
    b.rot(n_head, 'X', -11.0, (0, 0, 33.0))
    b.rot(n_head, 'Y', 3.0, (0, 0, 33.0))


def double(b):
    A, G = b.A, b.G
    T, K = 'iwz_pk_dbl_turq', 'iwz_pk_chrome'
    b.box(K, -16.3, 14.3, -20.3, 20.3, 0, 2)
    b.box(T, -16, 4, -20, 20, 2, 79, bevel=0.6)                               # booth back block (to the roof)
    b.box(T, 4, 14, 1, 20, 2, 68, bevel=0.5)                                  # right panel
    b.box(T, 4, 14, -20, -17.5, 2, 68)                                        # left jamb
    b.box(T, 4, 14, -17.5, 1, 2, 14, bevel=0.3)                               # sill under the opening
    b.front(A, 'inside', 4.03, -17.5, 1, 14, 68)
    b.lathe(K, [(0, 14), (0.6, 14), (0.6, 23.6), (4.6, 24.0), (4.6, 25.6), (0, 25.6)], 16, 8.0, -8.2)   # stool
    # coral curtain with folds on a chrome rod
    cols = 16
    y0, y1, zb, zt = -17.4, 0.9, 19.0, 67.0
    pts = [(11.6 + 0.7 * math.sin(i / cols * math.pi * 6), y0 + (y1 - y0) * i / cols) for i in range(cols + 1)]
    for i in range(cols):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        b.quad(A, [(xa, ya, zb), (xb, yb, zb), (xb, yb, zt), (xa, ya, zt)], 'curtain',
               uvs=((i / cols, 0), ((i + 1) / cols, 0), ((i + 1) / cols, 1), (i / cols, 1)))
    b.cyl(K, (12.2, -17.6, 67.4), (12.2, 1.2, 67.4), 0.35, 8)
    # marquee with the lit name, chrome frame and a flush roof
    b.box(T, 4, 15.5, -20.3, 20.3, 68, 79, bevel=0.6)
    b.front(G, 'sign', 15.53, -16.4, 16.4, 68.7, 78.3)
    for z0, z1 in ((67.6, 68.4), (78.6, 79.4)):
        b.box(K, 15.2, 15.9, -20.3, 20.3, z0, z1)
    for y in (-18.2, 18.2):
        b.box(K, 15.3, 15.9, y - 0.4, y + 0.4, 68.0, 79.0)
    b.box(T, -16.0, 15.5, -20.3, 20.3, 79, 80.2, bevel=0.4)
    # camera flash gun on the roof: post, arm, a big polished reflector facing the player, the bulb in it
    b.box(K, 0.0, 6.8, -3.2, 3.2, 80.2, 84.2, bevel=0.4)                     # flash unit housing
    b.cyl(K, (5.0, 0, 84.2), (7.0, 0, 86.0), 0.8, 10)
    n0 = b.lathe(K, [(1.2, 0.0), (5.6, 3.0), (6.0, 3.0), (6.0, 3.4), (5.5, 3.4), (1.0, 0.4)], 28, closed=True)
    b.xform(n0, Matrix.Translation(Vector((7.4, 0, 87.0)) * INCH) @ Matrix.Rotation(math.radians(98), 4, 'Y'))
    b.lathe_x(K, [(0, 0), (1.3, 0), (1.3, 1.2), (0, 1.2)], 12, (7.0, 0, 87.0))
    b.sphere(G, (9.4, 0, 86.9), 2.3, 16, 8, rect='bulb')
    # right panel: framed lit photo strip of four identical sweets, SWEETS card, coin box, slot with a strip in it
    b.box(K, 14.0, 14.5, 2.0, 11.0, 35.4, 64.6, bevel=0.15)
    b.front(G, 'strip', 14.53, 2.5, 10.5, 36.0, 64.0)
    b.box(K, 14.0, 14.3, 11.6, 19.6, 41.6, 50.8)
    b.front(G, 'card', 14.33, 11.9, 19.3, 42.0, 50.4)
    b.box(K, 14.0, 15.4, 13.4, 18.4, 32.0, 38.4, bevel=0.3)
    b.box('iwz_pk_black', 15.38, 15.45, 15.4, 16.4, 34.0, 36.6)
    b.front(A, 'slot', 14.03, 4.6, 16.4, 25.6, 30.4)
    b.box(K, 14.0, 16.2, 5.6, 15.4, 21.4, 24.8, bevel=0.3)
    b.box('iwz_pk_black', 16.1, 16.25, 6.4, 14.6, 22.0, 22.8)
    b.quad(A, [(16.4, 8.8, 13.4), (16.4, 11.4, 13.4), (16.4, 11.4, 22.4), (16.4, 8.8, 22.4)], 'strip')   # delivered strip
    for y in (-20.4, 20.0):                                                   # chrome corner strips
        b.box(K, 13.6, 14.4, y, y + 0.4, 2.0, 68.0)
    b.box(K, 13.6, 14.4, 0.6, 1.4, 14.0, 68.0)
    # chrome trim stripes round the sides and back
    for z in (30.0, 56.0):
        for s in (-1, 1):
            b.box(K, -16.25, 14.0, 20.0 if s > 0 else -20.3, 20.3 if s > 0 else -20.0, z, z + 1.0)
        b.box(K, -16.3, -16.0, -20.3, 20.3, z, z + 1.0)


BUILD = {'bakers': bakers, 'voyage': voyage, 'grudge': grudge, 'double': double}


# ---------------------------------------------------------------- materials for render and materials.json
def render_material(name, d, art):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(p.outputs[0], out.inputs[0])
    p.inputs['Roughness'].default_value = d['rough']

    def img(fn, colour=True):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(os.path.join(art, fn), check_existing=True)
        n.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        return n
    if d['kind'] == 'metal':
        nt.links.new(img(d['spec']).outputs[0], p.inputs['Base Color'])
        p.inputs['Metallic'].default_value = 1.0
    else:
        nt.links.new(img(d['albedo']).outputs[0], p.inputs['Base Color'])
    if d['kind'] == 'glow':
        nt.links.new(img(d['emissive']).outputs[0], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = 7.0
    return m


def materials_json(m, out, art):
    rel = os.path.relpath(art, out).replace(os.sep, '/')
    mats = []
    for n, d in mat_table(m).items():
        e = {'name': n, 'alpha': 'opaque', 'techset': 'authored', 'roughness_value': d['rough']}
        if d['kind'] == 'metal':
            e['albedo'] = {'path': rel + '/metal_c.png'}
            e['specular'] = {'path': rel + '/' + d['spec']}
        else:
            e['albedo'] = {'path': rel + '/' + d['albedo']}
        if d['kind'] == 'glow':
            e['emissive'] = {'path': rel + '/' + d['emissive']}
        mats.append(e)
    return {'adapter': 'authored', 'format': 'greyhound-materials', 'materials': mats}


# ---------------------------------------------------------------- render
def stage(ob, scale_dark=1.0):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dev in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dev
            prefs.get_devices()
            for d_ in prefs.devices:
                d_.use = True
            sc.cycles.device = 'GPU'
            break
        except Exception:
            continue
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('dark')
    w.use_nodes = True
    # dark to the camera; to reflections, a dim station ceiling with a brighter band overhead (the station's own
    # strip lights), so metals read as metal the way the game's reflection probes would show them
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs[0].default_value = (0.004, 0.0045, 0.005, 1)
    env = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 3.0
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 1.6
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs[2], pw.inputs[0])
    nt.links.new(pw.outputs[0], mul.inputs[0])
    env.inputs[0].default_value = (1.0, 0.92, 0.8, 1)
    nt.links.new(mul.outputs[0], env.inputs[1])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
    nt.links.new(env.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes['World Output'].inputs[0])
    sc.world = w
    # station floor (worn grey terrazzo) and a tiled back wall, both dim
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    fl = bpy.context.object
    fm = bpy.data.materials.new('floor')
    fm.use_nodes = True
    n = fm.node_tree.nodes
    pr = n['Principled BSDF']
    nz = n.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 60
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
    ramp.color_ramp.elements[1].color = (0.12, 0.115, 0.11, 1)
    fm.node_tree.links.new(nz.outputs[0], ramp.inputs[0])
    fm.node_tree.links.new(ramp.outputs[0], pr.inputs['Base Color'])
    pr.inputs['Roughness'].default_value = 0.55
    fl.data.materials.append(fm)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(-1.4, 0, 3), rotation=(0, math.radians(90), 0))
    wl = bpy.context.object
    wm = bpy.data.materials.new('wall')
    wm.use_nodes = True
    br = wm.node_tree.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (0.07, 0.075, 0.07, 1)
    br.inputs['Color2'].default_value = (0.05, 0.055, 0.05, 1)
    br.inputs['Mortar'].default_value = (0.03, 0.03, 0.03, 1)
    br.inputs['Scale'].default_value = 12
    wm.node_tree.links.new(br.outputs[0], wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    wl.data.materials.append(wm)

    def area(name, loc, energy, size, colour, target=(0, 0, 1.1)):
        L = bpy.data.lights.new(name, 'AREA')
        L.energy, L.size, L.color = energy * scale_dark, size, colour
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        d = Vector(target) - Vector(loc)
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    area('key', (2.2, 1.6, 3.0), 260, 1.2, (1.0, 0.86, 0.68))           # warm station lamp above-front
    area('fill', (2.6, -2.4, 1.4), 40, 2.0, (0.6, 0.75, 1.0))           # cool bounce
    area('rim', (-1.0, 2.2, 2.6), 90, 0.8, (1.0, 0.9, 0.8))
    return sc


def camera(sc, dist, az_deg, height=1.62, target_z=1.05, lens=38):
    cam = bpy.data.cameras.new('cam')
    cam.lens = lens
    o = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(o)
    a = math.radians(az_deg)
    o.location = (dist * math.cos(a), dist * math.sin(a), height)
    d = Vector((0, 0, target_z)) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = o
    return o


def triangles(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def roundtrip_object(m, port, name):
    """Import the game model read back from the port dump (iw7_model_to_glb.py output <port>/readback/<name>.glb)."""
    glb = os.path.join(port, 'readback', name + '.glb')
    bpy.ops.import_scene.gltf(filepath=glb)
    obs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    for o in obs:
        for slot in o.material_slots:
            nm = slot.material.name.split('.')[0] if slot.material else ''
            nm = nm.replace('mo/t7e_', '')
            if nm in bpy.data.materials:
                slot.material = bpy.data.materials[nm]
    return obs


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--art', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--renders', default='')
    ap.add_argument('--only', default='')
    ap.add_argument('--roundtrip', default='', help='port dump with readback/<model>.glb: render those instead')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    report = {}
    for m in (a.only.split(',') if a.only else MACHINES):
        name = 'iwz_perk_machine_' + m
        bpy.ops.wm.read_factory_settings(use_empty=True)
        for n, d in mat_table(m).items():
            render_material(n, d, a.art)
        b = B(m, a.art)
        BUILD[m](b)
        ob = b.finish(name)
        me = ob.data
        used = sorted({p.material_index for p in me.polygons})
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = [min(v[i] for v in bb) / INCH for i in range(3)]
        hi = [max(v[i] for v in bb) / INCH for i in range(3)]
        report[m] = {'model': name, 'triangles': triangles(ob), 'materials': [b.names[i] for i in used],
                     'bounds_in': [[round(x, 2) for x in lo], [round(x, 2) for x in hi]]}
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        if not a.roundtrip:
            path = os.path.join(a.out, name + '.glb')
            bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                                      export_materials='EXPORT', export_apply=True)
            mj = materials_json(m, a.out, a.art)
            mj['materials'] = [e for e in mj['materials'] if e['name'] in report[m]['materials']]
            json.dump(mj, open(os.path.join(a.out, name + '.materials.json'), 'w'), indent=1)
        else:
            bpy.data.objects.remove(ob)
            obs = roundtrip_object(m, a.roundtrip, name)
            report[m]['readback_triangles'] = sum(triangles(o) for o in obs)
        if a.renders:
            os.makedirs(a.renders, exist_ok=True)
            tag = '_readback' if a.roundtrip else ''
            sc = stage(ob)
            camera(sc, 2.9, 32)
            sc.render.filepath = os.path.join(a.renders, '%s%s_34.png' % (name, tag))
            bpy.ops.render.render(write_still=True)
            for L in ('key', 'fill', 'rim'):
                bpy.data.objects[L].data.energy *= 0.35
            camera(sc, 4.5, -24, height=1.65, target_z=1.0, lens=40)
            sc.render.filepath = os.path.join(a.renders, '%s%s_4m_dark.png' % (name, tag))
            bpy.ops.render.render(write_still=True)
        print('MACHINE', json.dumps(report[m]))
    json.dump(report, open(os.path.join(a.out, 'machines_report%s.json' % ('_readback' if a.roundtrip else '')), 'w'),
              indent=1)


if __name__ == '__main__':
    main()
