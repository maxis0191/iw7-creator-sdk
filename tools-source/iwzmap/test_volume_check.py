"""Unit tests of volume_check.py: entity box shapes as the engine point-tests them (Havok point query, units / 32).

A synthetic hknpDynamicCompoundShape -> hknpConvexPolytopeShape box is laid out exactly like the stock cp_zmb ones
(compound AABB +0x80/+0x90, instance array +0x60, tree +0xc0; polytope vertices +0x30, planes +0x40). The g8 case
reproduces the partial resize of the IWZ_TRIGGER_SHAPES compiler patch (only the positive half extents rewritten).
When IWZ_STOCK_DUMP_CP names a stock dump, it is checked too.
"""
import os
import struct
import unittest

import volume_check as vc

# Optional extra case on a real stock dump: set IWZ_STOCK_DUMP_CP to <dump>/cp_zmb/maps/cp. Unset, that case is
# skipped and the verdict depends on the synthetic cases only.
STOCK = os.environ.get('IWZ_STOCK_DUMP_CP', '')


class FakePack(vc.Pack):
    def __init__(self):    # no packfile: body and fixups are built by box()
        self.body = bytearray(0x400)
        self.local, self.glob, self.cls = {}, {}, {}
        self.contents = None

    def put(self, o, *f):
        struct.pack_into('<%df' % len(f), self.body, o, *f)


def box(donor, new=None, partial=False):
    """Box shape of half extents `donor` (game units), optionally resized to `new` completely or, with partial=True,
    only where (+hx, +hy, +hz) appears (the g8 defect)."""
    pk = FakePack()
    s = [x / vc.SCALE for x in donor]
    comp, inst, poly, data, nodes = 0x000, 0x100, 0x180, 0x300, 0x340
    pk.cls.update({comp: 'hknpDynamicCompoundShape', poly: 'hknpConvexPolytopeShape', data: 'hknpDynamicCompoundShapeData'})
    pk.local[comp + 0x60] = inst
    struct.pack_into('<I', pk.body, comp + 0x68, 1)
    pk.put(comp + 0x80, -s[0], -s[1], -s[2], 0.5)
    pk.put(comp + 0x90, s[0], s[1], s[2], 0.0)
    pk.glob[comp + 0xc0] = data
    pk.put(inst, 1, 0, 0, 0)
    pk.put(inst + 0x10, 0, 1, 0, 0)
    pk.put(inst + 0x20, 0, 0, 1, 0)
    pk.put(inst + 0x40, 1, 1, 1, 1)
    pk.glob[inst + 0x50] = poly
    struct.pack_into('<HH', pk.body, poly + 0x30, 8, 0x30)          # vertices at poly + 0x60
    struct.pack_into('<HH', pk.body, poly + 0x40, 6, 0xa0)          # planes at poly + 0xe0
    signs = [(1, 1, 1), (1, -1, 1), (1, 1, -1), (-1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)]
    for i, sg in enumerate(signs):
        pk.put(poly + 0x60 + 16 * i, sg[0] * s[0], sg[1] * s[1], sg[2] * s[2], 0.5)
    for i, (a, sgn) in enumerate([(2, 1), (2, -1), (1, -1), (1, 1), (0, -1), (0, 1)]):
        n = [0.0, 0.0, 0.0]
        n[a] = float(sgn)
        pk.put(poly + 0xe0 + 16 * i, n[0], n[1], n[2], -s[a])
    pk.local[data + 0x10] = nodes
    struct.pack_into('<I', pk.body, data + 0x18, 1)
    pk.put(nodes, -s[0], -s[1], -s[2], 0.5)
    pk.put(nodes + 16, s[0], s[1], s[2], 0.0)
    if new:
        t = [x / vc.SCALE for x in new]
        body = pk.body
        if partial:
            old = struct.pack('<3f', *s)
            at = body.find(old)
            while at >= 0:
                struct.pack_into('<3f', body, at, *t)
                at = body.find(old, at + 4)
        else:
            for i, sg in enumerate(signs):
                pk.put(poly + 0x60 + 16 * i, sg[0] * t[0], sg[1] * t[1], sg[2] * t[2])
            for i, (a, sgn) in enumerate([(2, 1), (2, -1), (1, -1), (1, 1), (0, -1), (0, 1)]):
                struct.pack_into('<f', body, poly + 0xe0 + 16 * i + 12, -t[a])
            for o in (comp + 0x80, nodes):
                pk.put(o, -t[0], -t[1], -t[2])
                pk.put(o + 16, t[0], t[1], t[2])
    return pk, comp


class VolumeShapeTest(unittest.TestCase):
    def test_stock_box(self):
        pk, comp = box((862, 588, 424))
        g = vc.shape_geom(pk, comp)
        self.assertTrue(g['ok'], g['why'])
        self.assertEqual(vc._r(g['maxs']), (862, 588, 424))
        self.assertTrue(vc.point_in_shape(g, (861, 0, 0)))
        self.assertFalse(vc.point_in_shape(g, (863, 0, 0)))

    def test_full_resize(self):
        pk, comp = box((862, 588, 424), (2500, 600, 208))
        g = vc.shape_geom(pk, comp)
        self.assertTrue(g['ok'], g['why'])
        for p, inside in (((2499, 0, 0), True), ((-2499, 599, -207), True), ((2501, 0, 0), False), ((0, 0, -209), False)):
            self.assertEqual(vc.point_in_shape(g, p), inside, p)

    def test_partial_resize_g8_is_caught(self):
        # g8: only (+hx, +hy, +hz) rewritten -> planes keep 862: the engine says |dx| > 862 is outside
        pk, comp = box((862, 588, 424), (2500, 600, 208), partial=True)
        g = vc.shape_geom(pk, comp)
        self.assertFalse(g['ok'])
        self.assertIn('outside plane', g['why'])

    def test_partial_shrink_is_caught(self):
        # a smaller target: vertex 0 shrinks, the planes and minimum bounds keep the donor (over-permissive volume)
        pk, comp = box((871, 897, 320), (800, 700, 176), partial=True)
        g = vc.shape_geom(pk, comp)
        self.assertFalse(g['ok'])

    def test_no_shape(self):
        self.assertFalse(vc.shape_geom(FakePack(), None)['ok'])


@unittest.skipUnless(STOCK and os.path.exists(os.path.join(STOCK, 'cp_zmb.d3dbsp.ents.data.hkx')), 'stock cp_zmb dump not present')
class StockDumpTest(unittest.TestCase):
    def test_stock_volumes_pass(self):
        r = vc.check(STOCK, 'cp_zmb')
        self.assertEqual(r['fails'], 0, [x for x in r['rows'] if not x['ok']][:3])
        self.assertGreater(r['checked'], 100)


if __name__ == '__main__':
    unittest.main()
