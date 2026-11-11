"""scenegen: the scene rules on synthetic layouts, and (when a stock cp_zmb dump is present) a small emitted map read
back by the offline gates."""
import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import scenegen as sg  # noqa: E402

TEMPLATE = os.environ.get('IWZ_TEMPLATE_DUMP_CP') or os.path.join(
    os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime'), 'iwz-map-ref-a', 'dump', 'cp_zmb')
HAVE_TEMPLATE = os.path.isfile(os.path.join(TEMPLATE, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx'))

# three rooms: a hall at 0, a lower hall at -64 reached by a flight inside it, a pit room behind a door at -64
BASE = {
    'map': 'cp_test',
    'start': {'zone': 'hall'},
    'zones': [
        {'id': 'hall', 'boxes': [[0, 0, 1024, 768]], 'floor': 0, 'ceiling': 256, 'spawners': {'ground': 3}},
        {'id': 'low', 'boxes': [[0, 768, 1024, 1536]], 'floor': -64, 'ceiling': 256,
         'flights': [{'id': 'low_steps', 'rect': [384, 768, 576, 984], 'up': '-y', 'z_lo': -64, 'z_hi': 0}],
         'spawners': {'ground': 3, 'ceiling': 1}},
        {'id': 'side', 'boxes': [[1040, 768, 1808, 1536]], 'floor': -64, 'ceiling': 192, 'spawners': {'ground': 3}},
    ],
    'doors': [
        {'id': 'D1', 'zones': ['hall', 'low'], 'price': 750, 'span': [384, 576], 'sill': 0},
        {'id': 'D2', 'zones': ['low', 'side'], 'price': 1000, 'span': [1056, 1248], 'sill': -64},
    ],
    'links': [],
    'interactions': [{'kind': 'perk', 'perk': 'revive', 'zone': 'hall', 'wall': 'west', 't': 0.5}],
}


def scene(mut=None):
    d = copy.deepcopy(BASE)
    if mut:
        mut(d)
    return sg.Scene(d, 'synthetic.json')


def errors(sc):
    return [m for s, m in sg.check_scene(sc) if s == 'ERROR']


class GeometryTests(unittest.TestCase):
    def test_rect_minus_leaves_the_frame_round_a_hole(self):
        parts = sg.rect_minus((0, 0, 100, 100), [(25, 25, 75, 75)])
        self.assertAlmostEqual(sum(sg.rect_area(p) for p in parts), 100 * 100 - 50 * 50)
        self.assertEqual(sg.rect_minus((0, 0, 10, 10), [(-5, -5, 20, 20)]), [])

    def test_shared_edge_accepts_a_wall_gap_and_refuses_a_wider_one(self):
        self.assertEqual(sg.shared_edge((0, 0, 100, 100), (116, 50, 200, 150))[:1], ('y',))
        self.assertIsNone(sg.shared_edge((0, 0, 100, 100), (140, 50, 200, 150)))
        self.assertEqual(sg.shared_edge((0, 0, 100, 100), (20, 100, 60, 180))[0], 'x')

    def test_flight_sheet_runs_over_the_nosings(self):
        f = sg.Flight('z', {'id': 'f', 'rect': [0, 0, 192, 400], 'up': '+y', 'z_lo': 0, 'z_hi': 160})
        self.assertEqual(f.n, 20)
        self.assertAlmostEqual(f.run, (400 - 56 - 32) / 20.0)
        # the sheet meets the top of riser k at the riser's position
        for k in range(f.n):
            self.assertAlmostEqual(f.line(f.s_a + k * f.run), f.z_lo + (k + 1) * f.rise, places=6)
        self.assertEqual(f.z_at(10, 0), 0)
        self.assertEqual(f.z_at(10, 400), 160)


class SceneRuleTests(unittest.TestCase):
    def test_the_synthetic_scene_is_clean(self):
        self.assertEqual(errors(scene()), [])

    def test_a_door_between_rooms_that_do_not_touch_is_refused(self):
        def mut(d):
            d['zones'][2]['boxes'] = [[1200, 768, 1808, 1536]]
        e = errors(scene(mut))
        self.assertTrue(any('do not share an edge' in m for m in e), e)

    def test_zones_may_not_overlap_in_plan(self):
        def mut(d):
            d['zones'][2]['boxes'] = [[1000, 768, 1808, 1536]]
        self.assertTrue(any('overlap in plan' in m for m in errors(scene(mut))))

    def test_a_sill_that_is_not_the_floor_is_refused(self):
        def mut(d):
            d['doors'][1]['sill'] = 0
        self.assertTrue(any('sill 0 but the floor of' in m for m in errors(scene(mut))))

    def test_a_steep_flight_is_refused(self):
        def mut(d):
            d['zones'][1]['flights'][0]['rect'] = [384, 768, 576, 900]
        self.assertTrue(any('tread' in m for m in errors(scene(mut))))

    def test_a_flight_end_needs_a_level_floor_or_an_opening(self):
        def mut(d):
            d['doors'][0]['span'] = [700, 892]
        e = errors(scene(mut))
        self.assertTrue(any('runs into a wall with no opening' in m for m in e), e)

    def test_an_opening_at_a_short_landing_is_refused(self):
        def mut(d):
            d['zones'][1]['flights'][0]['land_hi'] = 16
            d['zones'][1]['flights'][0]['land_lo'] = 56
            d['zones'][1]['flights'][0]['rect'] = [384, 768, 576, 984]
        e = errors(scene(mut))
        self.assertTrue(any('flat part' in m for m in e), e)

    def test_an_unreachable_zone_is_reported_and_a_far_box_is_not(self):
        def mut(d):
            d['doors'].pop()
        self.assertTrue(any('not reachable' in m for m in errors(scene(mut))))

        def far(d):
            d['doors'].pop()
            d['zones'][2]['far'] = True
            d['zones'][2]['boxes'] = [[5000, 5000, 5600, 5600]]
        self.assertEqual(errors(scene(far)), [])

    def test_a_prop_outside_its_zone_is_refused(self):
        def mut(d):
            d['zones'][0]['props'] = [{'model': 'm', 'at': [5000, 5000]}]
        self.assertTrue(any('prop 0' in m for m in errors(scene(mut))))

    def test_headroom_is_checked(self):
        def mut(d):
            d['zones'][0]['ceiling'] = 60
        self.assertTrue(any('ceiling' in m for m in errors(scene(mut))))


@unittest.skipUnless(HAVE_TEMPLATE, 'stock cp_zmb dump not present (set IWZ_TEMPLATE_DUMP_CP)')
class EmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = os.path.join(cls.tmp.name, 'src')
        path = os.path.join(cls.tmp.name, 'scene.json')
        json.dump(BASE, open(path, 'w'))
        cls.report = sg.emit(path, TEMPLATE, cls.out, log=lambda *_: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_output_is_written(self):
        for n in ('world.bin', 'colmap.hkx', 'navgraph.bin', 'ents.txt', 'triggers.txt', 'layout.json', 'plan.json', 'cp_iwz.gsc'):
            self.assertTrue(os.path.isfile(os.path.join(self.out, n)), n)
        self.assertEqual(self.report['problems'], [])
        self.assertEqual(self.report['spawners'], 10)

    def test_navigation_lies_on_the_flight_sheet(self):
        r = sg.check_flights(self.out)
        self.assertEqual(list(r['flights']), ['low_steps'])
        self.assertEqual(r['failures'], [])

    def test_the_offline_gate_finds_no_error(self):
        import iwz_emitcheck as ec
        rep, _tables = ec.run_check(ec.Emit.load(self.out))
        errs = [f for f in rep['findings'] if f['severity'] == 'error']
        self.assertEqual(errs, [], errs)

    def test_every_zone_is_walkable_from_the_start(self):
        t = sg.routes(self.out)
        self.assertTrue(t and all(v is not None for v in t.values()), t)

    def test_playtest_cases_cover_every_flight_and_opening(self):
        r = sg.test_args(self.out)
        self.assertEqual((r['climb_cases'], r['route_cases']), (2, 2))
        self.assertIn('low_steps_up=', r['climbs'])
        self.assertTrue(r['routes'].startswith('D1='))

    def test_the_level_script_carries_the_doors(self):
        gsc = open(os.path.join(self.out, 'cp_iwz.gsc')).read()
        self.assertIn('iwz_door( "D1", "iwz_door_D1"', gsc)
        self.assertNotIn('//@DOORS@', gsc)


if __name__ == '__main__':
    unittest.main()
