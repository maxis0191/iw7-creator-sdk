"""Unit tests of scenes/kit_lists.py on a tiny synthetic catalogue (no machine paths, no game data)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scenes'))
import kit_lists  # noqa: E402


def model(name, zones, size=(10, 20, 30), mats=()):
    return {'name': name, 'zones': list(zones), 'category': 'prop', 'size': list(size),
            'materials': [{'name': m} for m in mats] + [{'name': 'mopw/missing_one', 'missing': True}]}


class KitListsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.cat = os.path.join(self.d, 'catalog.json')
        json.dump({'zones': [], 'models': [
            model('bench_a', ['cp_zmb', 'cp_town'], (100, 40, 45), ['mopw/tile_a']),
            model('booth_b', ['cp_disco']),
            model('lamp_c', ['cp_final'], (5, 5, 20)),
            model('mp_only_d', ['mp_riot']),
        ]}, open(self.cat, 'w'))
        self.ported = os.path.join(self.d, 'ported.json')
        json.dump({'models': [model('piano_p', ['zm_castle'], (30, 70, 58))]}, open(self.ported, 'w'))
        self.smodels = os.path.join(self.d, 'smodels.csv')
        with open(self.smodels, 'w') as f:
            f.write('i,model,x\n0,bench_a,1\n1,bench_a,2\n2,other,3\n')
        self.fxcsv = os.path.join(self.d, 'z.csv')
        with open(self.fxcsv, 'w') as f:
            f.write('vfx,vfx/a/dust\nmaterial,mopw/tile_a\n')
        self.out = os.path.join(self.d, 'kits.json')
        self.md = os.path.join(self.d, 'kits.md')

    def tearDown(self):
        self.tmp.cleanup()

    def select(self, zones):
        p = os.path.join(self.d, 'select.json')
        with open(p, 'w') as f:
            json.dump({'zones': zones}, f)
        return p

    def run_main(self, zones, extra=()):
        argv = ['--select', self.select(zones), '--catalog', self.cat, '--ported-catalog', self.ported,
                '--smodels-csv', self.smodels, '--fx-csv', 'cp_zmb=' + self.fxcsv, '--out-json', self.out,
                '--out-md', self.md, '--min-total', '3', '--min-zone', '2', '--min-small', '1'] + list(extra)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = kit_lists.main(argv)
        return code, out.getvalue(), err.getvalue()

    def good(self):
        return {'hall': {
            'models': [{'name': 'bench_a', 'role': 'bench'}, {'name': 'booth_b', 'role': 'booth'}],
            'ported': [{'name': 'piano_p', 'role': 'piano'}],
            'effects': [{'name': 'vfx/a/dust', 'role': 'dust'}],
            'materials': [{'name': 'mopw/tile_a', 'role': 'floor'}],
            'gaps': [{'object': 'turnstile', 'size': [60, 30, 100], 'note': 'author'}]},
            'terminus': {'models': [{'name': 'lamp_c', 'role': 'lamp'}], 'gaps': []}}

    def test_good_selection(self):
        code, out, err = self.run_main(self.good())
        self.assertEqual(code, 0, err)
        data = json.load(open(self.out))
        self.assertEqual(data['totals']['distinct_models'], 3)
        self.assertEqual(data['totals']['template_donor_models'], 1)
        self.assertEqual(data['totals']['gaps'], 1)
        b = data['zones']['hall']['models'][0]
        self.assertEqual((b['name'], b['size'], b['template_donor'], b['uses_spaceland']), ('bench_a', [100, 40, 45], True, 2))
        self.assertEqual(data['zones']['hall']['models'][1]['template_donor'], False)
        self.assertIn('| `bench_a` | bench | 100x40x45 | zmb town | 2 | yes |', open(self.md).read())
        self.assertIn('distinct models over the map: 3', out)

    def test_missing_model_exits_1(self):
        z = self.good()
        z['hall']['models'].append({'name': 'no_such_model', 'role': 'x'})
        code, _, err = self.run_main(z)
        self.assertEqual(code, 1)
        self.assertIn('no_such_model', err)

    def test_model_of_other_maps_is_not_stock(self):
        z = self.good()
        z['hall']['models'].append({'name': 'mp_only_d', 'role': 'x'})
        code, _, err = self.run_main(z)
        self.assertEqual(code, 1)
        self.assertIn('mp_only_d', err)

    def test_missing_effect_material_and_ported(self):
        z = self.good()
        z['hall']['effects'].append({'name': 'vfx/none', 'role': 'x'})
        z['hall']['materials'].append({'name': 'mopw/missing_one', 'role': 'x'})
        z['hall']['ported'].append({'name': 'nothing', 'role': 'x'})
        code, _, err = self.run_main(z)
        self.assertEqual(code, 1)
        for n in ('vfx/none', 'mopw/missing_one', 'nothing'):
            self.assertIn(n, err)

    def test_size_rules(self):
        z = self.good()
        code, _, err = self.run_main(z, ['--min-total', '10'])
        self.assertEqual(code, 1)
        self.assertIn('distinct models over the map', err)
        code, _, err = self.run_main(z, ['--min-zone', '5'])
        self.assertEqual(code, 1)
        self.assertIn('zone hall', err)

    def test_dump_check(self):
        dump = os.path.join(self.d, 'dump', 'cp_zmb')
        os.makedirs(os.path.join(dump, 'xmodel'))
        open(os.path.join(dump, 'xmodel', 'bench_a.xmb'), 'w').close()
        json.dump({'zones': [{'name': 'cp_zmb', 'dirs': [dump]}, {'name': 'cp_disco', 'dirs': [dump]}], 'models': [
            model('bench_a', ['cp_zmb']), model('booth_b', ['cp_disco']), model('lamp_c', ['cp_final'])]}, open(self.cat, 'w'))
        z = {'hall': {'models': [{'name': 'bench_a', 'role': 'bench'}, {'name': 'booth_b', 'role': 'booth'}]}}
        code, _, err = self.run_main(z)
        self.assertEqual(code, 1)
        self.assertIn('booth_b has no xmodel file', err)


if __name__ == '__main__':
    unittest.main()
