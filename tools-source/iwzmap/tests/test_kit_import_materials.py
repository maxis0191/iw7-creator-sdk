"""Unit tests of kit_import.py --materials (stock world materials brought without a model) on synthetic files (no game data)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import kit_import  # noqa: E402


def put(root, rel, data=b'x'):
    p = os.path.join(root, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(data)


class BringMaterialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.work = os.path.join(d, 'work')
        self.dump = os.path.join(d, 'dump')
        os.makedirs(os.path.join(self.work, 'zone_source'))
        os.makedirs(os.path.join(self.work, 'zonetool', 'm'))
        with open(os.path.join(self.work, 'zone_source', 'm.csv'), 'w') as f:
            f.write('require,techsets_cp_zmb\nmaterial,,w/held\ncom_map,m\n')
        for mat, ts in (('w/tile_a', 'ts_base'), ('w/tile_b', 'ts_new'), ('w/held', 'ts_base')):
            put(self.dump, 'materials/%s.json' % mat, json.dumps({'techniqueSet->name': ts, 'textureTable': [{'semantic': 2, 'image': mat[2:] + '_c'},
                                                                                               {'semantic': 5, 'image': '$identitynormalmap'}]}).encode())
            for sub, exts in (('state', ('.stateinfo', '.statebits', '.statebitsmap')), ('constantbuffer', ('.cbi', '.cbt'))):
                for e in exts:
                    put(self.dump, 'techsets/%s/%s/%s%s' % (sub, ts, mat, e))
            put(self.dump, 'images/%s_c.iw7Image' % mat[2:])
        put(self.dump, 'techsets/ts_new.techset', b'\x00ts_new.tech\x00')
        put(self.dump, 'techsets/ts_new.tech.technique', b'\x00pp.7\x000123456789abcdef\x00')
        put(self.dump, 'techsets/pp.7.vertexdecl')
        put(self.dump, 'techsets/ps/0123456789abcdef.cso')
        self.rt = os.path.join(d, 'rt.csv')
        with open(self.rt, 'w') as f:
            f.write('techset,ts_base\n')

    def tearDown(self):
        self.tmp.cleanup()

    def run_kit(self, mats):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kit_import.main([self.work, 'm', '--dump', 'wm=' + self.dump, '--materials', mats, '--runtime-csv', self.rt, '--report', os.path.join(self.work, 'r.json')])
        return code, json.load(open(os.path.join(self.work, 'r.json'))), open(os.path.join(self.work, 'zone_source', 'm.csv')).read()

    def exists(self, rel):
        return os.path.isfile(os.path.join(self.work, 'zonetool', 'm', *rel.split('/')))

    def test_material_with_techset_in_base_brings_files_and_row(self):
        code, rep, csv = self.run_kit('wm:w/tile_a')
        self.assertEqual(code, 0)
        self.assertEqual(rep['materials']['new'], ['w/tile_a'])
        for rel in ('materials/w/tile_a.json', 'techsets/state/ts_base/w/tile_a.statebits', 'techsets/constantbuffer/ts_base/w/tile_a.cbt', 'images/tile_a_c.iw7Image'):
            self.assertTrue(self.exists(rel), rel)
        self.assertIn('material,w/tile_a', csv.splitlines())
        self.assertIn('techset,,ts_base', csv.splitlines())                       # shared with the runtime zone: a reference row, nothing embedded
        self.assertLess(csv.index('material,w/tile_a'), csv.index('com_map,m'))
        self.assertFalse(self.exists('techsets/ts_base.techset'))

    def test_star_material_files_are_named_with_underscore(self):
        # ZoneTool clean_name: the asset is `*387n_86n`, every file of it is `_387n_86n.*`
        put(self.dump, 'materials/_387n_86n.json', json.dumps({'techniqueSet->name': 'ts_base', 'textureTable': []}).encode())
        for sub, exts in (('state', ('.stateinfo', '.statebits', '.statebitsmap')), ('constantbuffer', ('.cbi', '.cbt'))):
            for e in exts:
                put(self.dump, 'techsets/%s/ts_base/_387n_86n%s' % (sub, e))
        code, rep, csv = self.run_kit('wm:*387n_86n')
        self.assertEqual(code, 0)
        self.assertEqual(rep['materials']['new'], ['*387n_86n'])
        self.assertEqual(rep['missing'] if 'missing' in rep else [], [])
        for rel in ('materials/_387n_86n.json', 'techsets/state/ts_base/_387n_86n.statebits', 'techsets/state/ts_base/_387n_86n.statebitsmap',
                    'techsets/state/ts_base/_387n_86n.stateinfo', 'techsets/constantbuffer/ts_base/_387n_86n.cbi', 'techsets/constantbuffer/ts_base/_387n_86n.cbt'):
            self.assertTrue(self.exists(rel), rel)
        self.assertIn('material,*387n_86n', csv.splitlines())                  # the reference keeps the `*`

    def test_material_with_new_techset_embeds_it_with_shader(self):
        code, rep, csv = self.run_kit('wm:w/tile_b')
        self.assertEqual(code, 0)
        self.assertIn('ts_new', rep['techsets']['embedded'])
        for rel in ('techsets/ts_new.techset', 'techsets/ts_new.tech.technique', 'techsets/pp.7.vertexdecl', 'techsets/ps/0123456789abcdef.cso'):
            self.assertTrue(self.exists(rel), rel)

    def test_material_the_csv_holds_is_shared_and_gets_no_row(self):
        code, rep, csv = self.run_kit('wm:w/held')
        self.assertEqual(code, 0)
        self.assertEqual(rep['materials']['shared'], ['w/held'])
        self.assertNotIn('material,w/held', csv.splitlines())

    def test_missing_material_fails_and_writes_nothing(self):
        code, rep, csv = self.run_kit('wm:w/tile_a,wm:w/nope')
        self.assertEqual(code, 1)
        self.assertIn('material:w/nope (wm)', rep['missing'])
        self.assertNotIn('material,w/tile_a', csv.splitlines())


if __name__ == '__main__':
    unittest.main()
