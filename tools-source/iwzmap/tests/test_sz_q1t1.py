"""Station Zero Q1/T1: the game-script module tables (sz_modules.py), the ring arithmetic and the plans and report of
sz_q1t1.py, on a synthetic layout (no game, no dump)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import sz_modules  # noqa: E402
import sz_q1t1  # noqa: E402

MARKERS = [
    {'kind': 'hatch', 'id': 'PLAZA', 'zone': 'cordon', 'origin': [1900, 5500, 192], 'yaw': 0},
    {'kind': 'hatch', 'id': 'EXCHANGE', 'zone': 'exchange', 'origin': [4160, 3900, -320], 'yaw': 180},
    {'kind': 'hatch', 'id': 'BARN', 'zone': 'car_barn', 'origin': [4200, 1200, -320], 'yaw': 0},
    {'kind': 'hatch', 'id': 'PARLOUR', 'zone': 'parlour', 'origin': [-3760, 2800, -384], 'yaw': 0},
    {'kind': 'quest_clock', 'id': 'clock_1', 'zone': 'fare_hall', 'origin': [600, 3240, 0], 'yaw': 90},
    {'kind': 'quest_clock', 'id': 'clock_2', 'zone': 'platform_west', 'origin': [-1200, 2000, -320], 'yaw': 0},
    {'kind': 'quest_clock', 'id': 'clock_3', 'zone': 'car_barn', 'origin': [5100, 840, -320], 'yaw': 90},
    {'kind': 'quest_clock', 'id': 'clock_4', 'zone': 'parlour', 'origin': [-3200, 3360, -384], 'yaw': 270},
    {'kind': 'quest_cab', 'id': 'car1', 'zone': 'platform_east', 'origin': [300, 1517, -320], 'yaw': 0,
     'area': [264, 1450, -330, 798, 1584, -200]},
    {'kind': 'terminus_arrival', 'id': 'arrival', 'zone': 'terminus', 'origin': [8300, 8450, 0], 'yaw': 0,
     'area': [7992, 7992, -16, 9408, 8908, 272]},
    {'kind': 'post_lever', 'id': 'bellows_lever', 'zone': 'bellows', 'origin': [-4400, 3568, -384], 'yaw': 270},
    {'kind': 'trap', 'id': 'unplaced', 'zone': 'cordon', 'origin': None, 'yaw': None},
]
VOLS = [{'name': 'cordon', 'zone': 'cordon', 'box': [-1408, 4600, -16, 2208, 5808, 636]},
        {'name': 'platform_east_2', 'zone': 'platform_east', 'box': [2400, 1208, -400, 3500, 1592, 16]}]


class ModuleTables(unittest.TestCase):
    def test_marker_lines(self):
        lines = sz_modules.marker_lines(MARKERS)
        self.assertEqual(len(lines), len(MARKERS) - 1)          # an unplaced marker is left out
        self.assertIn('[ "hatch", "PLAZA", "cordon", ( 1900, 5500, 192 ), 0 ];', lines[0])
        car = [ln for ln in lines if '"quest_cab"' in ln][0]
        self.assertIn('( 264, 1450, -330 ), ( 798, 1584, -200 )', car)

    def test_volume_lines(self):
        self.assertEqual(sz_modules.volume_lines(VOLS)[1],
                         '    v[v.size] = [ "platform_east_2", "platform_east", ( 2400, 1208, -400 ), ( 3500, 1592, 16 ) ];')

    def test_emit_fills_every_module(self):
        with tempfile.TemporaryDirectory() as d:
            mods = sz_modules.emit(d, MARKERS, VOLS, 'cp_iwz')
            self.assertEqual(mods, ['cap', 'post', 'quest'])
            for n in mods:
                with open(os.path.join(d, 'cp_iwz_%s.gsc' % n), encoding='utf-8') as f:
                    src = f.read()
                self.assertNotIn('//@MARKERS@', src)
                self.assertNotIn('//@VOLUMES@', src)
                if n != 'cap':                                    # the cap module places nothing: no tables
                    self.assertIn('"terminus_arrival"', src)
                # self-contained: no call into another module or the level script by path
                self.assertNotIn('scripts\\cp\\maps\\', src)
            self.assertEqual(sz_modules.calls(mods, 'cp_iwz')[2], '    level thread scripts\\cp\\maps\\cp_iwz\\cp_iwz_quest::init();')


class Ring(unittest.TestCase):
    def test_segments_and_prices(self):
        # 03-TRANSPORT.md: from PLAZA on BLOW, EXCHANGE 1, BARN 2, PARLOUR 3; DRAW swaps near and far
        self.assertEqual([sz_q1t1.segs('PLAZA', b, 'BLOW') for b in ('EXCHANGE', 'BARN', 'PARLOUR')], [1, 2, 3])
        self.assertEqual([sz_q1t1.segs('PLAZA', b, 'DRAW') for b in ('EXCHANGE', 'BARN', 'PARLOUR')], [3, 2, 1])
        for a in sz_q1t1.RING:
            near = [b for b in sz_q1t1.RING if b != a and sz_q1t1.segs(a, b, 'BLOW') == 1]
            self.assertEqual(len(near), 1)
        self.assertEqual(sz_q1t1.PRICE, {1: 250, 2: 400, 3: 550})

    def test_module_matches_the_ring(self):
        with open(os.path.join(HERE, 'modules', 'post.gsc'), encoding='utf-8') as f:
            src = f.read()
        self.assertIn('s.ring = [ "PLAZA", "EXCHANGE", "BARN", "PARLOUR" ];', src)
        self.assertIn('s.price = [ 0, 250, 400, 550 ];', src)


class Plans(unittest.TestCase):
    def layout(self, d):
        lay = {'map': 'cp_iwz', 'markers': MARKERS, 'volumes': VOLS, 'zone_points': {},
               'interactions': [{'kind': 'generator', 'origin': [3900, 2976, -270]}, {'kind': 'weapon_upgrade', 'origin': [8700, 8450, 0]}]}
        json.dump(lay, open(os.path.join(d, 'layout.json'), 'w'))
        return sz_q1t1.Lay(d)

    def test_plans_without_navigation(self):
        with tempfile.TemporaryDirectory() as d:
            L = self.layout(d)
            pls = [sz_q1t1.q1_steps(L), sz_q1t1.q1_order_coop(L), sz_q1t1.q1_late_round(L), sz_q1t1.t1_routes(L), sz_q1t1.t1_rules(L)]
            names = [p['name'] for p in pls]
            self.assertEqual(names, ['cp_iwz_q1_steps', 'cp_iwz_q1_order_coop', 'cp_iwz_q1_late_round', 'cp_iwz_t1_routes', 'cp_iwz_t1_rules'])
            for p in pls:
                self.assertEqual(p['libraries'], ['szq'])
                for st in p['steps']:
                    if st.get('do') == 'use' and 'ent' in st:
                        self.assertRegex(st['ent'], r'^[a-z0-9_]{1,63}$')       # gamelab's targetname rule
                    if st.get('do') == 'expect':
                        self.assertRegex(st['that'].split(':')[-1].split('.')[-1], r'^[a-z0-9_]+$')
            routes = pls[3]
            rides = [s for s in routes['steps'] if s.get('fn') == 'szq_ride']
            self.assertEqual(len(rides), 24)                                      # 12 routes on each lever setting

    def test_report_flags_a_ride_out_of_its_zone(self):
        with tempfile.TemporaryDirectory() as d:
            run = os.path.join(d, 'run1')
            os.makedirs(run)
            with open(os.path.join(run, 'client.stdout.log'), 'w') as f:
                f.write('[IWZ level] T1 LAUNCH from=PLAZA to=BARN segs=2 price=400 s=4.5 dir=BLOW capsule=0 by=x blowback=0 ride=1 t=1\n')
                f.write('[IWZ level] T1 RIDE_S ride=1 ms=0 origin=(4200, 1240, -320) zone=car_barn volume=car_barn t=2\n')
                f.write('[IWZ level] T1 RIDE_S ride=1 ms=250 origin=(1, 2, 3) zone=cordon volume=cordon t=3\n')
                f.write('[IWZ level] T1 ARRIVE to=BARN by=x ms=4600 t=4\n')
            r = sz_q1t1.report([d])
            self.assertEqual(r['rides'], 1)
            self.assertEqual(r['rides_left_zone'], [{'ride': '1', 'to': 'BARN', 'off': 1, 'samples': 2}])


if __name__ == '__main__':
    unittest.main()
