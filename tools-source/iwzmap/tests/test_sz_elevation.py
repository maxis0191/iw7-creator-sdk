"""Unit tests of the Station Zero AAA elevation wave 1 (docs/STATION-ZERO-AAA-W1.md): the bake occluders
(bake/occluders.py), the lighting design pass (sz2_lightdesign.py) and the voice script checker
(audio/voice_script_check.py) on synthetic data and on the committed script. No machine paths, no game data."""
import copy
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bake'))
import occluders  # noqa: E402
import sz2_lightdesign as LD  # noqa: E402


class OccluderTest(unittest.TestCase):
    def lay(self):
        return {'decor': [
            {'model': 'crate', 'origin': [0, 0, 0], 'yaw': 0, 'clip': None},                       # bounds below
            {'model': 'crate', 'origin': [500, 0, 0], 'yaw': 90, 'clip': None},                    # turned
            {'model': 'paper', 'origin': [100, 0, 0], 'yaw': 0, 'clip': None},                     # too thin
            {'model': 'iwz_platform_edge_128', 'origin': [0, 300, 0], 'yaw': 0, 'boxes': [[0, 0, 0, 128, 40, 30]]},
            {'model': 'iwz_vending', 'origin': [900, 0, 0], 'yaw': 0, 'boxes': [[880, -20, 0, 920, 20, 80]]},
            {'model': 'lamp_box', 'origin': [0, 900, 0], 'yaw': 0, 'clip': (20, 20, 20)},           # holds a light
            {'model': 'iwz_t7e_subway_car_a', 'origin': [0, -900, 0], 'yaw': 0},
        ],
            'train_spec': {'cars': [{'origin': [0, -900, -356], 'nav_half': [268, 66.5, 95], 'floor_z': -323}]},
            'genset': {'model': 'iwz_vending', 'footprint': [[880, -20], [920, 20]], 'origin': [900, 0, 0]}}

    def test_boxes(self):
        bounds = {'crate': {'mins': [-20, -10, 0], 'maxs': [20, 10, 40]}, 'paper': {'mins': [-30, -20, 0], 'maxs': [30, 20, 2]}}
        boxes, sk = occluders.occluder_boxes(self.lay(), bounds, [(0, 900, 20)])
        names = [b['model'] for b in boxes]
        self.assertEqual(names.count('crate'), 2)
        self.assertNotIn('paper', names)                              # thin: a black square on the floor otherwise
        self.assertNotIn('iwz_platform_edge_128', names)              # walkable surface model
        self.assertNotIn('lamp_box', names)                           # the lamp would black itself out
        self.assertEqual(names.count('iwz_vending'), 1)               # port box; the genset footprint is not doubled
        self.assertEqual(names.count('train_underframe'), 1)
        self.assertEqual(names.count('train_roof'), 1)
        self.assertEqual(sk, {'small': 1, 'holds_light': 1})
        c = next(b for b in boxes if b['model'] == 'crate' and b['min'][0] > 400)
        self.assertLess(c['max'][0] - c['min'][0], c['max'][1] - c['min'][1])      # yaw 90 turns the long side
        a = next(b for b in boxes if b['model'] == 'crate' and b['min'][0] < 400)
        self.assertAlmostEqual(a['max'][0] - a['min'][0], 40 * 0.88, places=2)      # 12 % inset


class LightDesignTest(unittest.TestCase):
    def lights(self):
        return [
            {'zone': 'ticket_hall', 'origin': (0, 0, 300), 'color': (0.85, 0.93, 1.0), 'radius': 288, 'intensity': 1.0, 'fixture': 'lamp_cool', 'mount': 'ceiling'},
            {'zone': 'ticket_hall', 'origin': (0, 0, 300), 'color': (0.85, 0.93, 1.0), 'radius': 384, 'intensity': 0.0, 'fixture': 'lamp_cool', 'mount': 'ceiling', 'dead': True},
            {'zone': 'control_room', 'origin': (0, 0, 100), 'color': (1.0, 0.06, 0.04), 'radius': 96, 'intensity': 0.3, 'fixture': 'lamp_red', 'mount': 'wall', 'wall_axis': 'y', 'wall_facing': -1},
            {'zone': 'control_room', 'origin': (0, 0, 40), 'color': (1.0, 0.55, 0.2), 'radius': 72, 'intensity': 0.25, 'fixture': 'hint_glow'},
            {'zone': 'platform_a', 'origin': (0, 0, 40), 'color': (1, 1, 1), 'radius': 170, 'intensity': 1.0, 'fixture': 'train_interior'},
        ]

    def test_pass(self):
        L = self.lights()
        before = copy.deepcopy(L)
        signs = [{'zone': 'ticket_hall', 'image': 'art_departure_board_suspended', 'center': [400, 3648, 200], 'axis': 'y', 'facing': -1}]
        decor = [{'zone': 'control_room', 'model': 'com_tv2_testpattern', 'origin': [3460, 3592, -250]}]
        rep = LD.apply(L, signs, decor)
        self.assertEqual(len(L), len(before) + 2)                     # accents appended, nothing removed
        for a, b in zip(before, L):                                   # runtime fields untouched, order kept
            for k in ('zone', 'origin', 'color', 'radius', 'intensity', 'fixture'):
                self.assertEqual(a[k], b[k])
        self.assertEqual(L[0]['bake']['type'], 'spot')
        self.assertEqual(L[0]['bake']['dir'], [0.0, 0.0, -1.0])
        self.assertAlmostEqual(L[0]['bake']['power_scale'], 1.6 * 1.5)   # lobe x the ticket hall key gain
        self.assertNotIn('bake', L[1])                                # dead fitting
        self.assertLess(L[2]['bake']['dir'][0], 0)                    # wall lamp faces -x and down
        self.assertLess(L[2]['bake']['dir'][2], 0)
        self.assertEqual(L[2]['bake']['radius_scale'], LD.ACCENT_RADIUS_SCALE)
        self.assertEqual(L[3]['bake'], {'radius_scale': LD.CUE_RADIUS_SCALE})
        self.assertNotIn('bake', L[4])                                # the train's interior light stays omni
        self.assertEqual(L[-2]['fixture'], 'board_glow')
        self.assertEqual(L[-2]['origin'][0], 364)                     # 36 out from the board's wall
        self.assertEqual(L[-1]['fixture'], 'screen_glow')
        self.assertEqual(len(rep['accents']), 2)


class VoiceScriptTest(unittest.TestCase):
    def test_committed_script_passes(self):
        script = os.path.join(ROOT, '..', '..', 'docs', 'station-zero', 'STATION-ZERO-VOICE-SCRIPT.json')
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(ROOT, 'audio', 'voice_script_check.py'), script],
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('voice script: PASS', r.stdout)


if __name__ == '__main__':
    unittest.main()
