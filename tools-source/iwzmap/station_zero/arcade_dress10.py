r"""arcade_dress10: round 10 of the Underpass Arcade's dressing: Studio's own dresser (`studio.placer.Placer`) instead of the SDK `Dresser`, the five shops dressed by
`dress_like(..., keep_clear=, resupport=True)` with the gameplay clearances, and their back walls by `strip=` wall runs. Nothing else of rounds 4 to 9 changes.

`install()` swaps the pieces in place (the older rounds' files stay as they were; only a builder that calls `install()` gets round 10):
  arcade_dress2.D2            -> PlacerDresser (a Placer with the SDK Dresser's surface: put / on / wall / ceil, rooms, keep, boxes, tops, skipped, failed, foreign, rng)
  arcade_dress.setup_rooms    -> the same rooms and keep-outs, each keep named (the refusals name them)
  arcade_dress4.dress_shop    -> dress_like with keep_clear = the gameplay clearance rows + the named keep-outs of the bay, resupport=True
  arcade_dress4.shop          -> its tall back-wall units (R2.Shelf + stock) become `strip=` wall runs
  arcade_dress6.shop6         -> round 5/6's header boards, dividers and second rows (tied to the tall units) are not made; the back room's stock is kept
"""
import inspect
import math
import random
import sys

import arcade_dress as R1
import arcade_dress2 as R2
import arcade_dress4 as D4
import arcade_dress5 as D5
import arcade_dress6 as D6
from studio import answers, placer, prefab
from studio import build as B

M = D4.M
SHELF = 'com_restaurantstainlessteelshelf_02'          # `store show`: 18.9 deep, 54.3 wide, 71 tall, symmetric (no back side), boards measured from the mesh
STRIP_DEPTH = 30.0
REPORT = {}


class _Pairs(list):
    """a list of (box, name) pairs that also takes the SDK's plain 4-tuples (named `<what>_<n>`)"""
    what = 'keep'

    def append(self, b):
        if len(b) == 4 and not isinstance(b[0], (list, tuple)):
            b = (tuple(b), '%s_%d' % (self.what, len(self) + 1))
        super().append(b)


class _Boxes(_Pairs):
    what = 'reserved'


class _Tops(dict):
    """the SDK's tops are 6-tuples (x, y, top, w, d, yaw); the Placer adds the prop id as a seventh"""

    def __setitem__(self, k, v):
        super().__setitem__(k, tuple(v)[:6])


class PlacerDresser(placer.Placer):
    def __init__(self, A, m):
        super().__init__(m, layer='dressing', zone='arcade', prefix='p', cap=R1.PROP_CAP, zones_of=R1.zones_of, subst=R1.SUBST)
        self.A = A
        self.keep, self.boxes, self.tops = _Pairs(), _Boxes(), _Tops()
        self.foreign = {}
        self.failed = []
        self.rng = random.Random(1978)

    def bounds(self, model):
        return self.bounds_of(model)

    def _put(self, model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone):
        rec, why = super()._put(model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone)
        if rec:
            zs = R1.zones_of(rec['model'])
            if 'cp_zmb' not in zs:
                self.foreign[rec['model']] = sorted(zs)
        return rec, why

    def put(self, model, x, y, yaw=0.0, z=0.0, tag=None, scale=1.0, emissive=None, alt=None, clip='auto', on=None, margin=1.0, ignore_keep=False, zone='arcade', slide=None, reach=48.0):
        rec = super().put(model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone, slide, reach)
        if rec is None:
            self.failed.append((tag or model, self._last_reason(tag or model), [round(x), round(y)]))
        return rec

    def _last_reason(self, key):
        row = self.ledger._t.get(str(key), {})
        rs = row.get('reasons') or {}
        return list(rs)[-1] if rs else 'refused'

    @property
    def skipped(self):
        out = {'room': 0, 'keep': 0, 'overlap': 0, 'zone': 0}
        for row in self.ledger._t.values():
            for reason, by in row['reasons'].items():
                out[reason] = out.get(reason, 0) + sum(by.values())
        return out

    def ceil(self, model, x, y, yaw, zc):
        """a ceiling prop by the centre of its bounds at height zc (the SDK Dresser's, counted in the ledger)"""
        model = R1.SUBST.get(model, model)
        self.ledger.ask('ceil')
        if self.n >= R1.PROP_CAP or not model or not R1.zones_of(model):
            self.ledger.refuse('ceil', 'zone' if model else 'cap', model)
            return None
        mn, mx = self.bounds_of(model)
        c = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, (mn[2] + mx[2]) / 2.0)
        a = math.radians(yaw)
        ox = x - (c[0] * math.cos(a) - c[1] * math.sin(a))
        oy = y - (c[0] * math.sin(a) + c[1] * math.cos(a))
        self.ids += 1
        self.m.use('dressing')
        B.prop(self.m, model, (round(ox, 2), round(oy, 2), round(zc - c[2], 2)), yaw=yaw, zone='arcade', id='c%03d_%s' % (self.ids, model[:16]))
        self.n += 1
        self.ledger.ok('ceil')
        return True

    # the SDK Dresser.wall (Placer has no wall helper): it only calls self.put, self.bounds and self.A
    wall = R1.Dresser.wall


def setup_rooms(A, D):
    D.rooms.append((A.X0 + A.WT, A.Y0 + A.WT, A.X1 - A.WT, A.Y1 - A.WT))
    for i in range(5):
        s = A.BAY_X[i]
        D.rooms.append((s + A.WT, A.Y1 + A.WT, s + A.BAY_W - A.WT, A.BACK_Y))
        D.rooms.append((s + A.WT, A.BACK_Y + 12.0, s + A.BAY_W - A.WT, A.Y1 + A.BAY_D - A.WT))
    D.rooms.append((A.X1 + A.WT, 3796.0, A.X1 + 200.0 - A.WT, 4004.0))
    D.add_keep((A.X0, 3590.0, A.X1, 3700.0), 'lane_south')
    D.add_keep((A.X0, 4130.0, A.X1, 4240.0), 'lane_north')
    for i in range(5):
        a0, a1 = A.aperture(i)
        s = A.BAY_X[i]
        D.add_keep((a0, 4240.0, a1, A.Y1 + 20.0), 'front_bay%d' % (i + 1))
        D.add_keep((s + 120.0, A.Y1, s + 200.0, A.BACK_Y + 30.0), 'path_bay%d' % (i + 1))
    D.add_keep((A.X1 - 200.0, 3780.0, A.X1 - 16.0, 4020.0), 'approach_D4')
    D.add_keep((A.X0, 3780.0, A.X0 + 80.0, 4020.0), 'approach_D7')
    for r in answers.clearance_rows(D.m):
        b = r['box']
        D.add_keep((b[0] - 4.0, b[1] - 4.0, b[3] + 4.0, b[4] + 4.0), '%s %s' % (r['kind'], r['id']))
    for c in D.m.flat().cameras:
        x, y = c['origin'][0], c['origin'][1]
        D.add_keep((x - 52.0, y - 52.0, x + 52.0, y + 52.0), 'camera %s' % c.get('id', c.get('name', '?')))


def _overlaps(b, k):
    return b[0] < k[2] and b[2] > k[0] and b[1] < k[3] and b[3] > k[1]


def dress_shop(A, m, D, i, report):
    """dress_like into the shop's front room, with the gameplay clearances and the named keep-outs that touch the bay; what it could not place is named in the answer"""
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    left, right = s + A.WT, s + A.BAY_W - A.WT
    y0, y1 = A.Y1 + A.WT, A.BACK_Y - 34.0
    room, seed = D4.SHOP_SRC[kind]
    box = [left, y0, right, y1]
    keep = answers.clearance_rows(m) + [(k, n) for (k, n) in D.keep if _overlaps(box, k) and n.startswith(('camera', 'front_bay', 'path_bay'))]
    m.use('dressing')
    rep = prefab.dress_like(m, room, box, front='s', density=1.0, seed=seed, z=0.0, prefix='dl%d_' % (i + 1), keep_clear=keep, resupport=True)
    D.n += rep['placed']
    for pid in rep['ids']:
        o = m.get(pid)
        if o is not None and o.get('kind') == 'prop' and o['origin'][2] < 72.0:
            bx = D.box_of(o['model'], o['origin'][0], o['origin'][1], (o.get('angles') or [0, 0, 0])[1], o.get('scale') or 1.0)
            D.boxes.append((tuple(bx), pid))
    report.setdefault('dress_like', {})[kind] = {'room': room, 'placed': rep['placed'], 'dropped': rep['dropped_by_reason'], 'models': rep['models_needed'],
                                                'density_per_1000': rep['density_per_1000'], 'coverage': rep['coverage']['dressed'], 'resupported': rep.get('resupported'),
                                                'refusal_lines': rep.get('refusal_lines')}
    REPORT.setdefault('dress_like', {})[kind] = {'placed': rep['placed'], 'refusal_lines': rep.get('refusal_lines'), 'resupported': rep.get('resupported')}


def back_strips(A, m, D, i, kind, items, brd):
    """the partition's face (the back wall of the front room): two wall runs of shelf units with their stock, either side of the doorway (u 18..116 and 204..302)"""
    s, yp = A.BAY_X[i], A.BACK_Y
    stock = []
    for k in list(items[0]) + list(items[1]):
        if k in M and M[k] not in stock:
            stock.append(M[k])
    n = 0
    rows = REPORT.setdefault('strips', {}).setdefault(kind, [])
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        rep = prefab.dress_like(m, None, [s + u0, yp - STRIP_DEPTH, s + u1, yp], front='s', seed=10 * i + side, prefix='st%d_%d_' % (i + 1, side), keep_clear=answers.clearance_rows(m),
                                strip={'wall': 'back', 'depth': STRIP_DEPTH, 'shelf': SHELF, 'stock': stock, 'fill': 0.9})
        n += rep.get('stock', 0) or 0
        rows.append({'side': side, 'shelves': rep.get('shelves'), 'stock': rep.get('stock'), 'levels': rep.get('levels'), 'distinct_models': rep.get('distinct_models'),
                     'wall_cover': rep.get('wall_cover'), 'refusal_lines': rep.get('refusal_lines')})
        D.n += (rep.get('shelves') or 0) + (rep.get('stock') or 0)
    return n


_BLOCK = """    n_stock = 0
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        sh = R2.Shelf(m, 'shelf_p%d_%d' % (side, i), (U(u0), yp - 32.0, U(u1), yp), 's', lv, board=brd, top=172.0)
        n_stock += R2.stock(D, sh, items[side], step * 1.5, yaw=270.0, jitter=14.0, skip=0.04, scale=1.5)
"""


def _patched_shop():
    src = inspect.getsource(D4.shop)
    assert _BLOCK in src, 'arcade_dress4.shop changed: the tall unit block was not found'
    src = src.replace(_BLOCK, "    n_stock = DRESS10.back_strips(A, m, D, i, kind, items, brd)\n")
    ns = D4.__dict__
    ns['DRESS10'] = sys.modules[__name__]
    exec(compile(src, '<arcade_dress10 shop>', 'exec'), ns)
    return ns['shop']


def shop10(A, m, D, i, report):
    """round 4's shop (with strips), then from rounds 5 and 6 only what does not belong to the tall units: the back room's continuous stock, the hanging lamps, the barrel and crate
    moved out of the back shelf, the back room's middle unit"""
    n = D4.shop(A, m, D, i, report)
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    wallb = A.Y1 + A.BAY_D - A.WT
    brd = D4.R3.BOARD[kind]
    U = lambda u: s + u
    m.use('dressing')
    sh = R2.Shelf(m, 'bsm_%d' % i, (U(116.0), wallb - 24.0, U(204.0), wallb), 's', (22.0, 50.0, 78.0, 106.0), board=brd, top=116.0, clip=False)
    R2.stock(D, sh, ['boxc', 'crate2', 'boxa', 'crate2', 'bag', 'boxc'], 24.0, yaw=270.0, jitter=12.0, skip=0.0, scale=1.2)
    for k, u in enumerate((60.0, 160.0, 260.0)):
        D.put(M['hang'], U(u), A.BACK_Y + 56.0, 0.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)
    for pid in [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and ('bk_barrel_%d' % i in o['id'] or 'bk_crate_%d' % i in o['id'])]:
        m.remove(pid)
    D.put(M['barrel'], U(30.0), A.BACK_Y + 36.0, 0.0, margin=1.0, clip=False)
    D.put(M['crate3'], U(290.0), A.BACK_Y + 36.0, 8.0, margin=1.0, clip=False)
    rng = random.Random(40 + i)
    placed = 0
    for z in (22.0, 50.0, 78.0, 106.0):
        t = U(122.0)
        while t < U(198.0):
            if D.put(rng.choice([M['boxc'], M['boxa'], M['crate2'], M['bag']]), t, wallb - 12.0, 270.0 + rng.uniform(-10.0, 10.0), z=z, ignore_keep=True, margin=0.0, clip=False):
                placed += 1
            t += rng.uniform(20.0, 30.0)
    return n + 1 + placed


def install():
    R2.D2 = PlacerDresser
    R1.setup_rooms = setup_rooms
    D4.dress_shop = dress_shop
    D4.shop = _patched_shop()
    D6.shop6 = shop10
    REPORT.clear()
