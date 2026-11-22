"""Unit tests of the pure parts of the asset library (no game data, no Blender): python -B -m unittest test_library"""
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import density  # noqa: E402
import inventory  # noqa: E402
import iwzgroups  # noqa: E402,F401
import pick  # noqa: E402
import sheets  # noqa: E402


def row(name, group, sub, size, zones=('cp_zmb',), tris=100, resolves=True):
    return {'name': name, 'group': group, 'subcategory': sub, 'size': list(size), 'zones': list(zones),
            'lod0Tris': tris, 'resolves': resolves, 'bounds': {}}


class Groups(unittest.TestCase):
    def test_groups(self):
        g = iwzgroups.group_of
        self.assertEqual(g('cp_disco_subway_turnstyle_animated', 'turnstile')[0], 'transit')
        self.assertEqual(g('park_soda_machine')[0], 'retail')
        self.assertEqual(g('weapon_ak47_vm')[0] in iwzgroups.EXCLUDED, True)
        self.assertEqual(g('vfx_smoke_a')[0], 'vfx')
        self.assertEqual(g('com_trashcan_01')[0], 'debris')
        self.assertEqual(g('zzz_unknown_thing')[0], 'misc')
        self.assertEqual(g('zzz_unknown_thing', 'pipe')[0], 'utilities')   # fine category fallback


class Pick(unittest.TestCase):
    def test_select(self):
        ms = [row('shelf_a', 'retail', 'shelf', (30, 90, 80)), row('shelf_big', 'retail', 'shelf', (30, 300, 80)),
              row('pipe_a', 'utilities', 'pipe', (4, 4, 60), ('cp_disco',)), row('gun', 'weapon', 'weapon', (1, 1, 1)),
              row('broken_shelf', 'retail', 'shelf', (5, 5, 5), resolves=False)]
        names = lambda r: [m['name'] for m in r]  # noqa: E731
        self.assertEqual(names(pick.select(ms, group='retail', size_max=96)), ['shelf_a', 'broken_shelf'])
        self.assertEqual(names(pick.select(ms, zone='cp_disco')), ['pipe_a'])
        self.assertEqual(names(pick.select(ms, text='SHELF', resolving=True)), ['shelf_a', 'shelf_big'])
        self.assertEqual(names(pick.select(ms, group='weapon')), [])
        self.assertEqual(names(pick.select(ms, group='weapon', include_excluded=True)), ['gun'])
        self.assertEqual(names(pick.select(ms, size_min=50)), ['shelf_a', 'shelf_big', 'pipe_a'])


class Density(unittest.TestCase):
    def test_measure_box(self):
        S = {'sm': np.array([[10, 10, 0], [20, 20, 5], [5000, 5000, 0]], float), 'sm_model': ['a', 'b', 'a'],
             'ent': [(30, 30, 0, 'c'), (9000, 0, 0, 'd')],
             'surf': [('w/brick', 0, 0, 0, 100, 100, 0, 8), ('w/sky', 0, 0, 0, 100, 100, 0, 2),
                      ('w/ceil', 0, 0, 200, 400, 400, 200, 4)],
             'lights': np.array([[50, 50, 100], [3000, 3000, 0]], float)}
        r = density.measure_box(S, (0, 0, 400, 400))
        self.assertEqual((r['props'], r['static_models'], r['script_models']), (3, 2, 1))
        self.assertEqual(r['distinct_models'], 3)
        self.assertEqual(r['materials'], 2)            # sky is skipped
        self.assertEqual(r['lights'], 1)
        self.assertEqual(r['triangles'], 12)
        self.assertGreater(r['covered'], 0.9)          # the 400 x 400 roof 200 above the floor covers the box

    def test_per_million(self):
        self.assertEqual(density.per_million({'props': 50, 'distinct_models': 5, 'materials': 10, 'lights': 2}, 2e6)['props'], 25.0)


class Sheets(unittest.TestCase):
    def test_compose_and_magenta_tile(self):
        with tempfile.TemporaryDirectory() as d:
            ents = [{'name': 'a_model', 'tile': os.path.join(d, 'none.png'), 'ok': False, 'reason': 'xmodel x not in any dump',
                     'size': '10 x 10 x 10', 'tris': 12, 'sub': 'x / cp_zmb'}]
            out = sheets.compose(ents, os.path.join(d, 's', 'a.png'), 'test', 64, cols=2)
            from PIL import Image
            im = Image.open(out)
            self.assertEqual(im.size[0], 128)
            self.assertEqual(im.getpixel((2, sheets.HEADER_H + 2))[:3], (255, 0, 255))   # a failed load is magenta

    def test_per_sheet(self):
        self.assertEqual(sheets.PER_SHEET, 48)


class Inventory(unittest.TestCase):
    def test_group_and_dumps(self):
        self.assertEqual([inventory.group_of(n) for n in ('cp_zmb', 'mp_rivet', 'patch_cp_zmb', 'techsets_cp_zmb', 'common_cp', 'sp_x', 'ui')],
                         ['cp', 'mp', 'patch', 'techsets', 'common', 'sp', 'other'])
        with tempfile.TemporaryDirectory() as d:
            z = os.path.join(d, 'a', 'cp_x')
            os.makedirs(os.path.join(z, 'xmodel'))
            open(os.path.join(z, 'cp_x.csv'), 'w').close()
            open(os.path.join(z, 'xmodel', 'm.xmb'), 'w').close()
            r = inventory.find_dumps(d)
            self.assertEqual(r['cp_x'][0]['xmodel'], 1)
            self.assertEqual(r['cp_x'][0]['xsurface'], 0)


if __name__ == '__main__':
    unittest.main()
