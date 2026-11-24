"""Tests of sz2_recipe.py: the build recipe the generator writes from its own switches (no machine paths, no game data)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import sz2_recipe  # noqa: E402

# the environment of the release build g27r (info.generator.env of its recipe) + the switches build-g now hands over
G27R_ENV = {
    'PYTHONHASHSEED': '0', 'IWZ_LIGHTS': '1', 'IWZ_SMODELS': '1', 'IWZ_KIT': '1',
    'IWZ_KIT_MATERIAL_MAP': 'mopw/glass_opaque_02=m/clk_glass_grunge_mild', 'IWZ_DOUBLE_SIDED': '1', 'IWZ_STAIR_STYLE': 'g27',
    'IWZ_TRAIN': '1', 'IWZ_TRAIN_CARS': '3', 'IWZ_TRAIN_CONSIST_END_X': '1800', 'IWZ_TRAIN_TRACK_EAST_X': '2848',
    'IWZ_TRAIN_CAR_BOXES': '{runtime}/iwz-stage2/train/port/banzai_v5/collision/iwz_t7e_subway_car_a.json',
    'IWZ_TRAIN_PROPS': '{runtime}/iwz-stage2/level/props_g27d.json', 'IWZ_PROBES': 'neutral', 'IWZ_AUDIO': '1',
    'IWZ_FX_TXT': '{sdk}/fx/station_zero_fx_dark.txt', 'IWZ_DARK': '1',
    'IWZ_TRAIN_SET': 'g27e', 'IWZ_DARK_ZONE_FILL': '1', 'IWZ_NAV_OBSTACLES': '1', 'IWZ_P1': '1'}


class Sz2RecipeTest(unittest.TestCase):
    def test_g27r_switches_give_the_g27r_recipe(self):
        want = json.load(open(os.path.join(HERE, 'fixtures_sz2_recipe_g27r.json'), encoding='utf-8'))
        got = sz2_recipe.recipe(G27R_ENV, 'unused')
        info = got.pop('info')
        self.assertEqual(got, want)
        self.assertEqual(info['generator']['env']['IWZ_TRAIN_SET'], 'g27e')
        self.assertEqual(info['written_by'], 'sz2_recipe.py')
        self.assertNotIn('keep_winding', got['compiler'])

    def test_train_set_default_follows_the_car_boxes_path(self):
        env = dict(G27R_ENV)
        del env['IWZ_TRAIN_SET']
        self.assertEqual(sz2_recipe.recipe(env, 'x')['kit']['dumps']['train'][1], '{runtime}/iwz-stage2/train/port/kit_v6')
        env['IWZ_TRAIN_SET'] = 'g27d'
        with self.assertRaises(ValueError):
            sz2_recipe.recipe(env, 'x')       # banzai_v5 is not the folder of g27d

    def test_no_switch_no_section(self):
        r = sz2_recipe.recipe({'IWZ_RUNTIME': 'R:/rt'}, 'x')
        for k in ('kit', 'fx', 'audio', 'darkness'):
            self.assertNotIn(k, r)
        self.assertEqual(r['bake']['lights'], 'document')
        self.assertFalse(r['perks']['p1'])
        self.assertFalse(r['submodels']['nav_obstacles'])
        self.assertNotIn('env', r['compiler'])

    def test_zone_fill_spec_and_real_paths_are_rooted(self):
        bs = chr(92)
        env = {'IWZ_RUNTIME': 'R:' + bs + 'rt', 'IWZ_DARK': '1', 'IWZ_DARK_ZONE_FILL': 'a:1:2:3',
               'IWZ_FX_TXT': bs.join(['R:', 'rt', 'fx', 'x.txt']), 'IWZ_KIT': '1', 'IWZ_TRAIN': '1', 'IWZ_TRAIN_SET': 'g27',
               'IWZ_TRAIN_CAR_BOXES': bs.join(['R:', 'rt', 'iwz-stage2', 'train', 'port', 'banzai_v3', 'collision', 'c.json'])}
        r = sz2_recipe.recipe(env, 'x')
        self.assertEqual(r['darkness']['lights']['zone_fill'], 'a:1:2:3')
        self.assertEqual(r['fx']['place'], '{runtime}/fx/x.txt')
        self.assertEqual(r['kit']['dumps']['train'][0], '{runtime}/iwz-stage2/train/port/banzai_v3')
        self.assertEqual(r['info']['generator']['env']['IWZ_FX_TXT'], '{runtime}/fx/x.txt')

    def test_write_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            p1 = sz2_recipe.write(G27R_ENV, d1)
            p2 = sz2_recipe.write(G27R_ENV, d2)
            b1, b2 = open(p1, 'rb').read(), open(p2, 'rb').read()
            self.assertEqual(b1, b2)
            self.assertEqual(os.path.basename(p1), 'build.json')
            self.assertNotIn(b'\r', b1)
            self.assertTrue(b1.endswith(b'\n'))
            self.assertEqual(json.loads(b1)['version'], 1)


if __name__ == '__main__':
    unittest.main()
