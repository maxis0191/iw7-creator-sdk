r"""goods_kit_a: helpers of the goods of Needle Drop and Heel & Key (worker A3a).

Every object of a shop's goods has an id `<shop>_<cls>__<item>__<n>[__<part>]`, so that film/goods_score_a.py can count ITEMS (one item =
one object a player would name: a sleeve, a register, a pair of shoes) from the layer alone. cls:
  T  the trade's own object (goods it sells or services, its machines and tools)
  S  the trade's own object that is shelf goods (sleeves, tapes, keys on a board): QUALITY-BAR rule 7 leaves these out of the variety count
  F  furniture and fittings of the dressing (a riser, a shelf board, a bracket, a rail)
  X  filler (box, crate, pallet, trash: rule 6)
  P  a picture alone (a card, a poster): not a prop, not counted
Pictures: C:\studio-data\sz\film\art\arcade\goods_a (drawn by art_goods_a/make_goods_pictures.py). Each picture is used at ONE size (Studio's
material of a picture is a hash of its file and its pixel size: a second size would be a second material).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import build as B  # noqa: E402
import shellgeo as G  # noqa: E402
import shellparts as P  # noqa: E402

PIC = r'C:\studio-data\sz\film\art\arcade\goods_a'
ART = r'C:\studio-data\sz\film\art\arcade'

# one size per picture (units, w x h)
SIZE = {
    'sleeve': (12.4, 12.4), 'rail': (56.0, 13.0), 'bin_tops': (12.4, 28.0), 'spines': (28.0, 12.4), 'tape': (7.5, 13.5),
    'card': (18.0, 12.0), 'cassette_rack': (24.0, 30.0), 'jcard': (4.2, 2.7), 'poster': (26.0, 39.0),
    'tag': (4.8, 8.4), 'key_board': (40.0, 25.0), 'laces': (8.0, 12.0), 'price_board': (30.0, 22.0),
}

MAT = {
    'black': 'w/metal_painted_02_dark', 'white': 'w/metal_panel_painted_01_white', 'alu': 'w/metal_aluminum_brushed_clearcoat',
    'chrome': 'w/metal_chrome_trim_03', 'wood': 'w/wood_antique_panel_trim_01', 'orange': 'w/ceramic_tile_01_orange',
    'glass': 'w/glass_clear_generic_01', 'rubber': 'w/rubber_trim_black', 'plaster': 'w/plaster_wall_04_white',
    'grey': 'w/metal_painted_wall_panel_04', 'beige': 'w/plastic_wall_frp_01_beige', 'red': 'w/plastic_wall_plain_red_01',
    'cream': 'w/plaster_wall_04_beige', 'card': 'w/plaster_wall_01_beige', 'brass': 'w/metal_painted_scratched_yellow',
    'blue': 'w/zmb_brushed_metal_01_blue',
}

NORMAL = {'s': (0.0, -1.0, 0.0), 'n': (0.0, 1.0, 0.0), 'e': (1.0, 0.0, 0.0), 'w': (-1.0, 0.0, 0.0), 'up': (0.0, 0.0, 1.0)}
PICS_USED = {}          # picture file -> size: the one-size rule, checked as we go


class Shop:
    """the id factory of one shop's layer"""

    def __init__(self, m, shop):
        self.m, self.shop, self.n = m, shop, {}
        self.layer = 'goods_%s' % shop
        m.use(self.layer)

    def item(self, cls, name):
        k = self.n.get(name, 0) + 1
        self.n[name] = k
        return '%s_%s__%s__%d' % (self.shop, cls, name, k)

    # -------------------------------------------------------------------------------------------- geometry of an item (pass the item id)
    def box(self, iid, part, b, mat, mode='render'):
        """AC2: a render-only solid is an authored bevelled mesh (edges cut at 45 degrees, a third of its thinnest side at most 0.6), a hairline (under 2.4) a plain solid;
        the id is the box's, so the goods score still counts the item"""
        b = [round(v, 3) for v in b]
        if mode != 'render':
            return B.box(self.m, b, MAT.get(mat, mat), mode=mode, layer=self.layer, id='%s__%s' % (iid, part))
        t = min(b[3] - b[0], b[4] - b[1], b[5] - b[2])
        tris = P.box(*b) if t < 2.4 else P.bevel_box(*b, c=min(0.6, t / 3.0), top=min(0.6, t / 3.0))
        return B.mesh(self.m, MAT.get(mat, mat), tris=tris, mode='render', layer=self.layer, id='%s__%s' % (iid, part))

    def clip(self, iid, b):
        return B.clip(self.m, [round(v, 3) for v in b], layer=self.layer, id='%s__clip' % iid)

    def pic(self, iid, part, name, at, facing, kind, folder=PIC, glow=None):
        """a picture on a surface (decal, 0.4 in front). glow: a picture that must read where no lamp reaches (a poster taped inside a
        window, lit from behind the glass only): an emissive sign of that strength set 0.4 in front, no light added"""
        path = name if os.path.isabs(name) else os.path.join(folder, name)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        size = SIZE[kind]
        if PICS_USED.setdefault(path, size) != size:
            raise ValueError('%s used at two sizes: %s and %s' % (path, PICS_USED[path], size))
        if glow:
            oid = B.sign(self.m, image=path, at=[round(v, 3) for v in at], normal=NORMAL[facing], size=list(size), emissive=glow, layer=self.layer,
                         id='%s__%s' % (iid, part))
            self.m.update(oid, off=0.4)
            return oid
        return B.decal(self.m, image=path, at=[round(v, 3) for v in at], normal=NORMAL[facing], size=list(size), layer=self.layer,
                       id='%s__%s' % (iid, part))

    def prop(self, iid, model, origin, yaw=0.0, angles=None, scale=1.0, clip=None, part='m'):
        return B.prop(self.m, model, [round(v, 3) for v in origin], yaw=yaw, angles=angles, scale=scale, clip=clip, layer=self.layer,
                      id='%s__%s' % (iid, part))

    def mesh(self, iid, part, mat, parts):
        tris, uvs = parts
        return B.mesh(self.m, MAT.get(mat, mat), tris=tris, uvs=uvs, mode='render', layer=self.layer, id='%s__%s' % (iid, part))

    # -------------------------------------------------------------------------------------------- composite goods
    def flat(self, cls, name, picture, kind, centre, facing, thick=0.3, mat='card', back=None):
        """a flat thing with a picture on its face (an LP sleeve, a tape box, a card on a backing): a thin box behind the face, the
        picture on the face. `centre` is the centre of the FACE; facing s/n/e/w"""
        iid = self.item(cls, name)
        w, h = SIZE[kind]
        x, y, z = centre
        n = NORMAL[facing]
        if facing in ('s', 'n'):
            y0, y1 = (y, y + thick) if facing == 's' else (y - thick, y)
            b = [x - w / 2, y0, z - h / 2, x + w / 2, y1, z + h / 2]
        else:
            x0, x1 = (x, x + thick) if facing == 'w' else (x - thick, x)
            b = [x0, y - w / 2, z - h / 2, x1, y + w / 2, z + h / 2]
        self.box(iid, 'body', b, mat)
        self.pic(iid, 'face', picture, centre, facing, kind)
        if back:
            opp = {'s': 'n', 'n': 's', 'e': 'w', 'w': 'e'}[facing]
            bc = [x - n[0] * thick, y - n[1] * thick, z]
            self.pic(iid, 'back', back, bc, opp, kind)
        return iid


# ------------------------------------------------------------------------------------------------ authored meshes (simple, said so in the note)
def boxtris(b):
    """a closed box as (tris, uvs) for a mesh (so that a few boxes can share one mesh record)"""
    x0, y0, z0, x1, y1, z1 = b
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    tris, uvs = [], []
    for a, b_, c, d in faces:
        q = [list(P[i]) for i in (a, b_, c, d)]
        tris += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
        uvs += [[[0, 0], [1, 0], [1, 1]], [[0, 0], [1, 1], [0, 1]]]
    return tris, uvs


def loft(sections, segs=12):
    """a closed solid through elliptical sections [(x, w, h, zc)] along x (half widths w in y, half heights h in z, centre height zc)"""
    tris, uvs = [], []
    rings = []
    for x, w, h, zc in sections:
        rings.append([(x, w * math.cos(2 * math.pi * k / segs), zc + h * math.sin(2 * math.pi * k / segs)) for k in range(segs)])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            tris += [[list(a[k]), list(b[k2]), list(b[k])], [list(a[k]), list(a[k2]), list(b[k2])]]      # outward (axial x tangent faced in)
            uvs += [[[0, 0], [1, 0], [1, 1]], [[0, 0], [1, 1], [0, 1]]]
    for ring, sgn in ((rings[0], -1), (rings[-1], 1)):
        c = [ring[0][0], 0.0, sum(p[2] for p in ring) / segs]
        for k in range(segs):
            k2 = (k + 1) % segs
            t = [c, list(ring[k]), list(ring[k2])] if sgn > 0 else [c, list(ring[k2]), list(ring[k])]
            tris.append(t)
            uvs.append([[0.5, 0.5], [1, 0], [1, 1]])
    return tris, uvs


def place(parts, origin, yaw):
    tris, uvs = parts
    return G.yaw_points(tris, origin, yaw), uvs


def last_shape():
    """a wooden shoe last, toe along +x, 10.5 long, standing on z 0: a lofted foot form with a raised cone (the instep) at the heel end"""
    secs = [(-5.2, 0.6, 1.0, 1.8), (-4.8, 1.4, 1.9, 2.0), (-3.6, 1.6, 2.2, 2.2), (-1.8, 1.5, 2.0, 2.1), (0.4, 1.7, 1.6, 1.7), (2.6, 1.9, 1.3, 1.4),
            (4.2, 1.6, 1.0, 1.1), (5.0, 1.0, 0.7, 0.8), (5.3, 0.4, 0.4, 0.6)]
    foot = loft(secs, 10)
    cone = G.cylinder((-3.4, 0.0, 3.6), (-3.0, 0.0, 6.6), 1.1, 10)          # the leg cone with its thimble
    return G.merge(foot, cone)


def key_machine(origin, yaw):
    """a key duplicating machine (1970s bench type), about 15 x 10 x 12: base, carriage with two vices, the cutter wheel under its guard,
    the tracer, the lever. -> {material: parts}"""
    body = G.merge(boxtris([-7.5, -5.0, 0.0, 7.5, 5.0, 4.0]), boxtris([-6.0, -4.0, 4.0, 6.0, 4.0, 5.0]), boxtris([-1.0, 2.0, 5.0, 1.0, 4.5, 11.0]),
                   boxtris([-5.5, 1.8, 9.5, 5.5, 4.6, 12.0]))
    steel = G.merge(boxtris([-5.0, -3.0, 5.0, -2.0, 0.6, 7.2]), boxtris([2.0, -3.0, 5.0, 5.0, 0.6, 7.2]),
                    G.cylinder((-3.5, 1.6, 8.0), (-3.5, 0.6, 8.0), 2.0, 16), G.cylinder((3.5, 1.6, 8.0), (3.5, 0.6, 8.0), 0.5, 8),
                    G.cylinder((6.0, -1.0, 6.0), (10.0, -5.0, 6.5), 0.4, 8))
    knob = G.cylinder((10.0, -5.0, 6.5), (10.8, -5.8, 6.6), 0.9, 8)
    return {'beige': place(body, origin, yaw), 'chrome': place(steel, origin, yaw), 'black': place(knob, origin, yaw)}


def grinder(origin, yaw):
    """a bench grinder with two wheels and their guards on a motor, about 16 x 6 x 10"""
    motor = G.merge(G.cylinder((-3.5, 0, 5.0), (3.5, 0, 5.0), 3.0, 16), boxtris([-3.0, -3.0, 0.0, 3.0, 3.0, 2.5]))
    wheels = G.merge(G.cylinder((-6.6, 0, 5.0), (-5.0, 0, 5.0), 3.6, 18), G.cylinder((5.0, 0, 5.0), (6.6, 0, 5.0), 3.6, 18))
    guards = G.merge(boxtris([-7.2, -2.6, 8.2, -4.4, 2.6, 9.0]), boxtris([4.4, -2.6, 8.2, 7.2, 2.6, 9.0]),
                     boxtris([-7.2, 2.6, 2.0, -4.4, 3.2, 9.0]), boxtris([4.4, 2.6, 2.0, 7.2, 3.2, 9.0]))
    shaft = G.cylinder((-7.4, 0, 5.0), (7.4, 0, 5.0), 0.5, 8)
    return {'grey': place(G.merge(motor, guards), origin, yaw), 'rubber': place(wheels, origin, yaw), 'chrome': place(shaft, origin, yaw)}


def mould(origin, yaw):
    """the plaster mould of the Dead-Man's Handle, two halves: the lower half lies open (its cavity: a grip channel 9 long with a round
    knob pocket and the boss at the pivot end, made as a recess by building the block around it), the upper half lies beside it turned
    over. 12 x 5 x 2.2 a half. -> {material: parts}"""
    L, W, H = 12.0, 5.0, 2.2
    lo = []
    # the block around a channel along x: y -0.8..0.8, from x -4.5 to 4.5, depth 1.0; a pocket at x 4.5..6 (knob) wider; boss pocket at x -6..-4.5
    d = H - 1.0
    lo.append(boxtris([-L / 2, -W / 2, 0.0, L / 2, W / 2, d]))                               # floor of the cavity and below
    lo.append(boxtris([-L / 2, -W / 2, d, L / 2, -1.4, H]))                                  # south rim
    lo.append(boxtris([-L / 2, 1.4, d, L / 2, W / 2, H]))                                     # north rim
    lo.append(boxtris([-L / 2, -1.4, d, -4.6, -0.8, H]))                                      # boss shoulders
    lo.append(boxtris([-L / 2, 0.8, d, -4.6, 1.4, H]))
    lo.append(boxtris([-4.6, -1.4, d, 3.8, -0.6, H]))                                         # grip channel shoulders (narrower)
    lo.append(boxtris([-4.6, 0.6, d, 3.8, 1.4, H]))
    lo.append(boxtris([5.6, -1.4, d, L / 2, 1.4, H]))                                         # end wall past the knob pocket
    lo.append(boxtris([-L / 2, -0.8, d, -5.4, 0.8, H]))                                       # end wall past the boss
    lower = G.merge(*lo)
    upper = boxtris([-L / 2, W / 2 + 0.8, 0.0, L / 2, W / 2 + 0.8 + W, H])
    sprue = G.cylinder((0.0, W + 3.3 - 2.5, H), (0.0, W + 3.3 - 2.5, H + 0.05), 0.7, 10, caps=True)
    stain = G.merge(boxtris([-5.4, -0.8, d - 0.02, -4.6, 0.8, d + 0.02]), boxtris([-4.6, -0.6, d - 0.02, 3.8, 0.6, d + 0.02]),
                    boxtris([3.8, -1.4, d - 0.02, 5.6, 1.4, d + 0.02]))
    return {'plaster': place(G.merge(lower, upper), origin, yaw), 'brass': place(stain, origin, yaw), 'black': place(sprue, origin, yaw)}


def carousel(origin, tiers=3, r=6.0, h=30.0):
    """a counter key carousel: base disc, a post, `tiers` rings of hooks (returns meshes and the hook points for keys)"""
    x, y, z = origin
    parts = [G.cylinder((x, y, z), (x, y, z + 1.0), 4.5, 16), G.cylinder((x, y, z + 1.0), (x, y, z + h), 0.5, 8)]
    hooks = []
    for t in range(tiers):
        zt = z + 8.0 + t * (h - 10.0) / max(1, tiers - 1)
        parts.append(G.cylinder((x, y, zt), (x, y, zt + 0.5), r, 18))
        for k in range(8):
            a = 2 * math.pi * k / 8 + t * 0.4
            hx, hy = x + r * math.cos(a), y + r * math.sin(a)
            parts.append(G.cylinder((hx, hy, zt + 0.2), (x + (r + 2.0) * math.cos(a), y + (r + 2.0) * math.sin(a), zt + 0.2), 0.15, 4))
            hooks.append((x + (r + 1.6) * math.cos(a), y + (r + 1.6) * math.sin(a), zt - 0.3, math.degrees(a)))
    return G.merge(*parts), hooks
