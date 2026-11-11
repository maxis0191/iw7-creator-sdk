"""Crowd module (E2): the model copy without a scriptable, the zone rows, the level script call, the module text."""
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CROWD = os.path.join(os.path.dirname(HERE), 'crowd')
sys.path.insert(0, CROWD)
import add_crowd  # noqa: E402
import crowd_model  # noqa: E402


def fake_xmb(name, scriptable):
    """A file shaped like ZoneTool's xmodel dump around the records the tool touches."""
    raw = bytes(range(40))                                         # the raw struct
    out = raw + b'\x06\x01' + name.encode() + b'\x00'               # the model's name
    out += b'\x07\x01mtl/a\x00\x07\x01' + name.encode() + b'_lod0\x00'   # a material, a surface (names contain the name)
    out += b'\x07\x01ragdoll_human_male\x00\x07\x00'                 # physics asset, no physics fx shape
    out += (b'\x07\x01' + scriptable.encode() + b'\x00') if scriptable else b'\x07\x00'
    out += b'\x07\x01procedural_bones\x00\x00\x01\x02'
    return out


class CrowdModelTest(unittest.TestCase):
    def test_strip_renames_and_removes_the_scriptable(self):
        data = fake_xmb('police_officer_zombie', 'zombie_cop_scriptable')
        self.assertEqual(crowd_model.check(data), 'zombie_cop_scriptable')
        out, removed = crowd_model.strip(data, 'police_officer_zombie', 'iwz_crowd_cop')
        self.assertEqual(removed, 'zombie_cop_scriptable')
        self.assertIsNone(crowd_model.check(out))
        self.assertIn(b'\x06\x01iwz_crowd_cop\x00', out)
        self.assertNotIn(b'\x06\x01police_officer_zombie\x00', out)
        # the shared assets keep their stock names
        self.assertIn(b'\x07\x01police_officer_zombie_lod0\x00', out)
        self.assertIn(b'\x07\x01ragdoll_human_male\x00', out)
        self.assertEqual(out[:40], data[:40])
        self.assertTrue(out.endswith(b'\x07\x01procedural_bones\x00\x00\x01\x02'))

    def test_a_model_without_scriptable_is_refused(self):
        with self.assertRaises(ValueError):
            crowd_model.strip(fake_xmb('m', None), 'm', 'n')

    def test_two_scriptables_are_refused(self):
        data = fake_xmb('m', 'a_scriptable') + b'\x07\x01b_scriptable\x00'
        with self.assertRaises(ValueError):
            crowd_model.check(data)


class AddCrowdTest(unittest.TestCase):
    def test_marker_becomes_the_call(self):
        text = 'main()\n{\n    level thread iwz_report();\n    //@CROWD@\n    //@AUDIO@\n}\n'
        out = add_crowd.patch_level(text, 'cp_iwz')
        self.assertIn('scripts\\cp\\maps\\cp_iwz\\cp_iwz_crowd::init();', out)
        self.assertNotIn('//@CROWD@', out)
        self.assertIn('//@AUDIO@', out)
        self.assertEqual(add_crowd.patch_level(out, 'cp_iwz'), out)       # once

    def test_older_level_script_gets_the_call_before_audio(self):
        text = 'main()\n{\n    //@AUDIO@\n}\n'
        out = add_crowd.patch_level(text, 'cp_iwz').split('\n')
        i = [k for k, l in enumerate(out) if 'cp_iwz_crowd::init' in l][0]
        self.assertEqual(out[i + 1].strip(), '//@AUDIO@')

    def test_no_place_is_an_error(self):
        with self.assertRaises(ValueError):
            add_crowd.patch_level('main()\n{\n}\n', 'cp_iwz')

    def test_rows_after_the_level_script_once(self):
        lines = ['>,x', 'rawfile,scripts/cp/maps/cp_iwz/cp_iwz.gsc', 'xmodel,other']
        rows = ['rawfile,scripts/cp/maps/cp_iwz/cp_iwz_crowd.gsc', 'xmodel,iwz_crowd_cop']
        out = add_crowd.add_rows(lines, 'cp_iwz', rows)
        self.assertEqual(out[2:4], rows)
        self.assertEqual(add_crowd.add_rows(out, 'cp_iwz', rows), out)

    def test_whole_module_on_a_tree(self):
        with tempfile.TemporaryDirectory() as t:
            stock = os.path.join(t, 'stock')
            os.makedirs(stock)
            open(os.path.join(stock, 'police_officer_zombie.xmb'), 'wb').write(fake_xmb('police_officer_zombie', 'zombie_cop_scriptable'))
            root = os.path.join(t, 'zonetool', 'cp_iwz')
            lvl = os.path.join(root, 'scripts', 'cp', 'maps', 'cp_iwz')
            os.makedirs(lvl)
            open(os.path.join(lvl, 'cp_iwz.gsc'), 'w').write('main()\n{\n    //@CROWD@\n}\n')
            csv = os.path.join(t, 'cp_iwz.csv')
            open(csv, 'w').write('rawfile,scripts/cp/maps/cp_iwz/cp_iwz.gsc\n')
            self.assertEqual(add_crowd.main([csv, root, 'cp_iwz', '--stock-xmodel', stock]), 0)
            self.assertIsNone(crowd_model.check(open(os.path.join(root, 'xmodel', 'iwz_crowd_cop.xmb'), 'rb').read()))
            self.assertTrue(os.path.isfile(os.path.join(lvl, 'cp_iwz_crowd.gsc')))
            self.assertIn('xmodel,iwz_crowd_cop', open(csv).read())
            self.assertIn('cp_iwz_crowd::init', open(os.path.join(lvl, 'cp_iwz.gsc')).read())


class ModuleTextTest(unittest.TestCase):
    def setUp(self):
        self.gsc = open(os.path.join(CROWD, 'cp_iwz_crowd.gsc'), encoding='utf-8').read()

    def test_no_lab_only_builtin(self):
        # the production server lacks the lab's builtins: a call stops the map load (docs/NETLAB.md of the server)
        for name in ('paris_debug_begin', 'paris_debug_end', 'paris_get_connection_id', 'executecommand'):
            self.assertNotIn(name + '(', self.gsc)

    def test_cap_table_is_the_bible_table(self):
        rows = re.findall(r'table\[(\d)\] = \[ ([\d, ]+) \];', self.gsc)
        self.assertEqual([r[1] for r in rows], ['24, 24, 24, 24', '24, 28, 32, 36', '30, 36, 44, 48', '38, 46, 56, 62', '47, 58, 70, 78'])

    def test_registers_in_the_stock_list_of_enemies(self):
        self.assertIn('level.dlc_get_non_agent_enemies = ::iwz_crowd_alive;', self.gsc)


if __name__ == '__main__':
    unittest.main()
