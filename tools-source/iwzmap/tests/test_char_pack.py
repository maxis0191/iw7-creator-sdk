"""Unit tests of char_pack.py (and kit_import.py on a zone with no world rows) on synthetic dumps: no machine paths,
no game data."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import char_pack  # noqa: E402


def asset(name):
    return b'\x07\x01' + name.encode() + b'\x00'


class CharPackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.dump = os.path.join(d, 'dump', 'zone_a')
        for sub in ('xmodel', 'xsurface', 'materials', 'images', 'techsets/state/ts_new', 'techsets/state/ts_shared'):
            os.makedirs(os.path.join(self.dump, sub))

        def write(rel, data):
            with open(os.path.join(self.dump, rel), 'wb') as f:
                f.write(data if isinstance(data, bytes) else data.encode())
        # body: one surface, one own material (own techset) and one material a shared zone defines, the shared ragdoll
        # physics, a scriptable and the procedural bones of its map zone, then the model's trailing arrays; arms: own
        # material
        self.body_tail = (asset('ragdoll_shared') + b'\x07\x00' + asset('boss_scriptable') + asset('pb_female')
                          + b'\x08\x01\x02\x00\x00\x00\x07\x0e' + b'\x08\x00' + b'\x08\x00')
        write('xmodel/hero_body.xmb', b'XMB' + asset('hero_body_lod0') + asset('mtl_body') + asset('mtl_shared')
              + self.body_tail)
        write('zone_a.csv', 'xmodel,hero_body\nproceduralbones,pb_female\nscriptable,boss_scriptable\n')
        write('xmodel/hero_arms.xmb', b'XMB' + asset('hero_arms_lod0') + asset('mtl_body'))
        write('xsurface/hero_body_lod0.xsb', b'S' * 10)
        write('xsurface/hero_arms_lod0.xsb', b'S' * 4)
        write('materials/mtl_body.json', json.dumps({'techniqueSet->name': 'ts_shared', 'textureTable': [{'image': 'img_body'}]}))
        write('materials/mtl_shared.json', json.dumps({'techniqueSet->name': 'ts_shared', 'textureTable': [{'image': 'img_x'}]}))
        write('images/img_body.iw7Image', b'H')
        write('techsets/state/ts_shared/mtl_body.statebits', b'1')
        write('techsets/state/ts_shared/mtl_body.statebitsmap', b'1')
        self.runtime = os.path.join(d, 'runtime')
        os.makedirs(os.path.join(self.runtime, 'techsets_global'))
        with open(os.path.join(self.runtime, 'techsets_global', 'techsets_global.csv'), 'w') as f:
            f.write('techset,ts_shared\nmaterial,mtl_shared\n')
        os.makedirs(os.path.join(self.runtime, 'global_core_mp'))
        with open(os.path.join(self.runtime, 'global_core_mp', 'global_core_mp.csv'), 'w') as f:
            f.write('physicsasset,ragdoll_shared\n')
        self.spec = os.path.join(d, 'chars.json')
        with open(self.spec, 'w') as f:
            json.dump({'table': 'paris/chars.csv', 'characters': [
                {'key': 'hero', 'zone': 'zone_a', 'body': 'hero_body', 'head': '', 'arms': 'hero_arms'}]}, f)
        self.out = os.path.join(d, 'pack')

    def tearDown(self):
        self.tmp.cleanup()

    def run_pack(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = char_pack.main([self.out, '--dump', 'zone_a=' + self.dump, '--characters', self.spec,
                                   '--runtime-dir', self.runtime] + list(extra))
        return code, out.getvalue()

    def test_pack_rows_table_and_shared_material(self):
        code, out = self.run_pack()
        self.assertEqual(code, 0, out)
        rows = open(os.path.join(self.out, 'zone_source', 'mod.csv')).read().split()
        self.assertEqual(rows[0], 'require,techsets_common')
        self.assertIn('material,,mtl_shared', rows)          # defined by a shared zone: a reference
        self.assertIn('techset,,ts_shared', rows)
        self.assertNotIn('material,,mtl_body', rows)         # own material: copied
        self.assertEqual(rows[-3:], ['xmodel,hero_arms', 'xmodel,hero_body', 'stringtable,paris/chars.csv'])
        tree = os.path.join(self.out, 'zonetool', 'mod')
        self.assertTrue(os.path.isfile(os.path.join(tree, 'materials', 'mtl_body.json')))
        self.assertFalse(os.path.exists(os.path.join(tree, 'materials', 'mtl_shared.json')))
        self.assertTrue(os.path.isfile(os.path.join(tree, 'images', 'img_body.iw7Image')))
        with open(os.path.join(tree, 'paris', 'chars.csv')) as f:
            self.assertEqual(f.read(), 'key,body,head,arms\nhero,hero_body,,hero_arms\n')
        self.assertIn('physicsasset,,ragdoll_shared', rows)  # a shared zone's ragdoll: a reference
        with open(os.path.join(self.out, 'charpack-report.json')) as f:
            rep = json.load(f)
        self.assertEqual(rep['characters'][0]['models']['body'], ['hero_body', 'in pack'])
        body = rep['models']['hero_body']
        self.assertEqual((body['droppedScriptable'], body['droppedProceduralBones']), ('boss_scriptable', 'pb_female'))
        with open(os.path.join(tree, 'xmodel', 'hero_body.xmb'), 'rb') as f:   # a patched copy, not the dump's file
            self.assertTrue(f.read().endswith(asset('ragdoll_shared') + b'\x07\x00\x07\x00\x07\x00'
                                              + b'\x08\x01\x02\x00\x00\x00\x07\x0e\x08\x00\x08\x00'))
        with open(os.path.join(self.dump, 'xmodel', 'hero_body.xmb'), 'rb') as f:
            self.assertTrue(f.read().endswith(self.body_tail))

    def test_portraits_are_standalone_materials(self):
        # a HUD portrait: a 2d material of no model, its techset only referenced by a shared techsets zone
        with open(os.path.join(self.dump, 'materials', 'hud_hero.json'), 'w') as f:
            json.dump({'techniqueSet->name': '2d', 'textureTable': [{'image': 'hud_hero'}]}, f)
        with open(os.path.join(self.dump, 'images', 'hud_hero.iw7Image'), 'wb') as f:
            f.write(b'P')
        os.makedirs(os.path.join(self.dump, 'techsets', 'state', '2d'))
        for ext in ('.statebits', '.statebitsmap'):
            with open(os.path.join(self.dump, 'techsets', 'state', '2d', 'hud_hero' + ext), 'wb') as f:
                f.write(b'1')
        with open(os.path.join(self.runtime, 'techsets_global', 'techsets_global.csv'), 'a') as f:
            f.write('techset,,2d\n')
        with open(self.spec, 'w') as f:
            json.dump({'table': 'paris/chars.csv', 'characters': [
                {'key': 'hero', 'zone': 'zone_a', 'body': 'hero_body', 'head': '', 'arms': 'hero_arms',
                 'portraits': ['hud_hero']}]}, f)
        code, out = self.run_pack()
        self.assertEqual(code, 0, out)
        rows = open(os.path.join(self.out, 'zone_source', 'mod.csv')).read().split()
        self.assertIn('material,hud_hero', rows)
        self.assertIn('techset,,2d', rows)
        tree = os.path.join(self.out, 'zonetool', 'mod')
        self.assertTrue(os.path.isfile(os.path.join(tree, 'materials', 'hud_hero.json')))
        self.assertTrue(os.path.isfile(os.path.join(tree, 'images', 'hud_hero.iw7Image')))
        with open(os.path.join(self.out, 'charpack-report.json')) as f:
            self.assertEqual(json.load(f)['portraits'], {'hero': {'hud_hero': 'in pack'}})

    def test_missing_portrait_fails(self):
        with open(self.spec, 'w') as f:
            json.dump({'table': 'paris/chars.csv', 'characters': [
                {'key': 'hero', 'zone': 'zone_a', 'body': 'hero_body', 'head': '', 'arms': 'hero_arms',
                 'portraits': ['hud_none']}]}, f)
        code, out = self.run_pack()
        self.assertEqual(code, 1, out)
        self.assertIn('material:hud_none', out)

    def test_unknown_tail_layout_is_refused(self):
        with open(os.path.join(self.dump, 'xmodel', 'hero_body.xmb'), 'ab') as f:
            f.write(b'\x08\x00')                                # one array too many: the drop is not safe
        code, out = self.run_pack()
        self.assertEqual(code, 1)
        self.assertIn('pb_female of hero_body', out)

    def test_missing_model_writes_no_table(self):
        os.remove(os.path.join(self.dump, 'xmodel', 'hero_arms.xmb'))
        code, out = self.run_pack()
        self.assertEqual(code, 1)
        self.assertIn('xmodel:hero_arms', out)
        self.assertFalse(os.path.exists(os.path.join(self.out, 'zonetool', 'mod', 'paris', 'chars.csv')))

    def test_refuses_a_used_folder(self):
        self.assertEqual(self.run_pack()[0], 0)
        with self.assertRaises(SystemExit):
            self.run_pack()


if __name__ == '__main__':
    unittest.main()
