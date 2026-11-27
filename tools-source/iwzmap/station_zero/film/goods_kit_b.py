r"""goods_kit_b: the helpers of the goods of Copy Stop and Hole Number Nine (worker A3b).

Every object goes into the shop's own layer `goods_<shop>` with an id `<shop>__<kind>__<nn>[__<part>]`: one ITEM is one thing a player
would name (a ream, a tray of rings, the till), made of one stock model or of several authored parts. `goods_score_b.py` reads these ids
back from the document and scores the items by their kind (QUALITY-BAR rules 5, 6, 7).
Authored parts are render-only; furniture that stands on the floor gets one clip box (the shell's rule `solid`). Pictures are in
ART_B (drawn by art_goods_b/make_pictures_b.py); `mat_*` pictures are world materials of our own (B.material), the others sign or decal pictures.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import build as B  # noqa: E402
import shellgeo as G  # noqa: E402

ART = r'C:\studio-data\sz\film\art\arcade'
ART_B = os.path.join(ART, 'goods_b')
SIGN_OFF = 3.6        # a B.sign quad stands this far in front of its `at`
DECAL_OFF = 0.4       # a B.decal quad stands this far in front of its `at`

# stock materials used by the authored parts
M = {
    'white': 'w/metal_panel_painted_01_white',
    'chrome': 'w/metal_chrome_trim_03',
    'alu': 'w/metal_aluminum_brushed_clearcoat',
    'black': 'w/metal_painted_01_black',
    'rubber': 'w/rubber_trim_black',
    'glass': 'w/glass_clear_generic_01',
    'wood': 'w/wood_antique_panel_trim_01',
    'blue': 'w/zmb_brushed_metal_01_blue',
    'beige': 'w/plastic_wall_frp_01_beige',
    'grey': 'w/metal_painted_wall_panel_04',
    'red': 'w/plastic_wall_plain_red_01',
    'green_glow': 'w/emissive_light_panel_green',
    'white_glow': 'w/emissive_light_panel_white',
    'pink': 'w/paint_pink_wall_semigloss',
}


def art(name):
    return os.path.join(ART, name)


def art_b(name):
    p = os.path.join(ART_B, name)
    if not os.path.isfile(p):
        raise FileNotFoundError('%s: run art_goods_b/make_pictures_b.py first' % p)
    return p


# ------------------------------------------------------------------------------------------------ meshes
def quad(p0, p1, p2, p3, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    """a quad p0..p3 counter clockwise seen from its front; uv in repeats (v up)"""
    return [[list(p0), list(p1), list(p2)], [list(p0), list(p2), list(p3)]], [[list(uv[0]), list(uv[1]), list(uv[2])], [list(uv[0]), list(uv[2]), list(uv[3])]]


def obox(c, size, yaw=0.0, faces='tnsewb', fit=True, tile=8.0):
    """a box of size (w along local x, d along local y, h) standing on c = (x, y, z bottom centre), turned by yaw: its faces as a mesh.
    fit=True: every face carries the whole picture once (top: picture top to local +y; sides upright); else the picture repeats every `tile` units"""
    w, d, h = size
    cs, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def P(x, y, z):
        return (round(c[0] + x * cs - y * sn, 3), round(c[1] + x * sn + y * cs, 3), round(c[2] + z, 3))
    x0, x1, y0, y1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2, 0.0, h

    tu, tv = (tile, tile) if isinstance(tile, (int, float)) else tile

    def uvs(a, b):
        return ((0, 0), (1, 0), (1, 1), (0, 1)) if fit else ((0, 0), (a / tu, 0), (a / tu, b / tv), (0, b / tv))
    F = {
        't': (P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), uvs(w, d)),
        'b': (P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0), uvs(w, d)),
        's': (P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1), uvs(w, h)),
        'n': (P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), uvs(w, h)),
        'e': (P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1), uvs(d, h)),
        'w': (P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), uvs(d, h)),
    }
    tris, uv = [], []
    for f in faces:
        a, b_, c_, d_, u = F[f]
        t, q = quad(a, b_, c_, d_, u)
        tris += t
        uv += q
    return tris, uv


def prism(c, r, h, sides=8, yaw=0.0):
    """an upright n-sided prism (a tube, a drum) standing on c"""
    return G.cylinder((c[0], c[1], c[2]), (c[0], c[1], c[2] + h), r, sides)


def tilt(parts, origin, pitch):
    """turn mesh parts about the x axis through origin by pitch degrees (a tilted light table, a sheet hanging over an edge)"""
    tris, uvs = parts
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    out = []
    for t in tris:
        q = []
        for p in t:
            y, z = p[1] - origin[1], p[2] - origin[2]
            q.append([p[0], round(origin[1] + y * cp - z * sp, 3), round(origin[2] + y * sp + z * cp, 3)])
        out.append(q)
    return out, uvs


# ------------------------------------------------------------------------------------------------ the kit of one shop
class Kit:
    def __init__(self, m, shop):
        self.m, self.shop, self.layer = m, shop, 'goods_' + shop
        self.count = {}
        self.mats = {}
        self.items = []        # (item id, kind)

    def item(self, kind):
        n = self.count[kind] = self.count.get(kind, 0) + 1
        iid = '%s__%s__%02d' % (self.shop, kind, n)
        self.items.append((iid, kind))
        return iid

    # materials of our own: one per picture, named by the shop
    def mat(self, picture, tile=8.0, gloss=0.15):
        if picture not in self.mats:
            nm = 'sz_' + os.path.splitext(picture)[0].replace('mat_', '').replace('PLACEHOLDER', 'ph').lower()
            self.mats[picture] = B.material(self.m, nm, color=art_b(picture), gloss=gloss, tile=tile, layer=self.layer, id='%s__mat__%s' % (self.shop, nm))
        return self.mats[picture]

    # parts of an item
    def box(self, iid, part, box, mat, uv=None):
        return B.box(self.m, box, mat, mode='render', layer=self.layer, id='%s__%s' % (iid, part), uv=uv)

    def clip(self, iid, box, part='clip'):
        return B.clip(self.m, box, layer=self.layer, id='%s__%s' % (iid, part))

    def mesh(self, iid, part, mat, parts):
        tris, uvs = parts
        return B.mesh(self.m, mat, tris=tris, uvs=uvs, mode='render', layer=self.layer, id='%s__%s' % (iid, part))

    def decal(self, iid, part, picture, at, normal, size, rot=0.0, lift=0.05):
        """a picture lying on a surface: `at` on the surface, the quad `lift` in front of it"""
        a = [at[i] - normal[i] * (DECAL_OFF - lift) for i in range(3)]
        return B.decal(self.m, image=picture, at=a, normal=list(normal), size=list(size), rot=rot or 0.0, layer=self.layer, id='%s__%s' % (iid, part))

    def sign(self, iid, part, picture, at, normal, size, emissive=None, rot=0.0, lift=0.15):
        """a picture card standing `lift` in front of `at` (B.sign puts its quad 3.6 out: compensated)"""
        a = [at[i] - normal[i] * (SIGN_OFF - lift) for i in range(3)]
        return B.sign(self.m, image=picture, at=a, normal=list(normal), size=list(size), rot=rot or 0.0, emissive=emissive, layer=self.layer, id='%s__%s' % (iid, part))

    # whole items
    def prop(self, kind, model, origin, yaw=0.0, scale=1.0, clip=None, angles=None):
        iid = self.item(kind)
        B.prop(self.m, model, origin, yaw=yaw, scale=scale, angles=angles, clip=clip, layer=self.layer, id=iid)
        return iid

    def fixture(self, kind, fx_kind, at, facing=0.0, **kw):
        iid = self.item(kind)
        return B.fixture(self.m, fx_kind, at, facing, group='emergency', bake='baked', layer=self.layer, id=iid, **kw)


# ------------------------------------------------------------------------------------------------ shared builders
def paper_stack(K, kind, c, size, yaw=0.0, top=None, top_mat=None, edge_mat=None):
    """a stack of paper (copies, a job, blank sheets): sides in the paper edge material, a printed top sheet as a decal or a material face"""
    iid = K.item(kind)
    w, d, h = size
    edge = edge_mat or K.mat('mat_cs_paper_edge.png', tile=8.0)
    K.mesh(iid, 'body', edge, obox(c, size, yaw, faces='nsew', fit=False, tile=8.0))
    if top_mat:
        K.mesh(iid, 'top', top_mat, obox(c, (w, d, h + 0.02), yaw, faces='t', fit=True))
    else:
        K.mesh(iid, 'top', M['white'], obox(c, (w, d, h), yaw, faces='t', fit=True))
        if top:
            K.decal(iid, 'sheet', art_b(top), (c[0], c[1], c[2] + h), (0.0, 0.0, 1.0), (w * 0.98, d * 0.98), rot=yaw)
    return iid


def ream(K, c, yaw=0.0, kind='ream', colour=None):
    """a wrapped ream of letter paper, 8.5 x 11 x 2; colour 'yellow' | 'pink' | 'green' for the pastel stock"""
    iid = K.item(kind)
    K.mesh(iid, 'body', K.mat('mat_cs_ream_%s.png' % colour if colour else 'mat_cs_ream.png'), obox(c, (11.0, 8.5, 2.1), yaw, fit=True))
    return iid


def ream_stack(K, c, n, yaw=0.0, colour=None, kind='ream_stack'):
    """n wrapped reams stacked (one item): every ream shows its own wrapper band (the picture repeats every 2.1 up, every 11 across)"""
    iid = K.item(kind)
    pic = 'mat_cs_ream_%s.png' % colour if colour else 'mat_cs_ream.png'
    K.mesh(iid, 'body', K.mat(pic), obox(c, (11.0, 8.5, 2.1 * n), yaw, faces='tnsew', fit=False, tile=(11.0, 2.1)))
    return iid


def rings(c0, cols, rows, pitch, R=1.35, r=0.62, segs=12, tube=6, jitter=0.0, seed=0, skip=()):
    """rows of doughnut rings lying flat from corner c0 (x, y, z of the tray surface): one merged mesh"""
    import random
    rnd = random.Random(seed)
    parts = []
    for i in range(cols):
        for j in range(rows):
            if (i, j) in skip:
                continue
            x = c0[0] + i * pitch + rnd.uniform(-jitter, jitter)
            y = c0[1] + j * pitch + rnd.uniform(-jitter, jitter)
            parts.append(G.torus((x, y, c0[2] + r), (0.0, 0.0, 1.0), R, r, segs, tube))
    return G.merge(*parts)
