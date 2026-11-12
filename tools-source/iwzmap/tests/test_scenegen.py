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

    def test_a_walk_path_keeps_its_corners_and_drops_straight_runs(self):
        pts = [[x, 0, 0] for x in range(0, 500, 48)] + [[480, y, 0] for y in range(48, 500, 48)]
        s = sg.simplify(pts, 12.0)
        self.assertEqual(s[0], pts[0])
        self.assertEqual(s[-1], pts[-1])
        self.assertEqual(len(s), 3)
        self.assertEqual(s[1][:2], [480, 0])

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

    def test_props_come_over_from_an_old_layout_only_where_they_stand(self):
        tmp = tempfile.mkdtemp()
        sp, lp = os.path.join(tmp, 's.json'), os.path.join(tmp, 'old.json')
        json.dump(BASE, open(sp, 'w'))
        decor = [{'zone': 'old', 'model': 'bench', 'origin': [200, 200, 0], 'yaw': 90, 'static': True},        # kept
                 {'zone': 'old', 'model': 'rubble_pile', 'origin': [300, 300, 0], 'static': True},          # excluded name
                 {'zone': 'old', 'model': 'crate', 'origin': [480, 700, 0], 'static': True},                # in front of D1
                 {'zone': 'old', 'model': 'kit', 'origin': [250, 250, 0], 'static': False},                 # not static
                 {'zone': 'old', 'model': 'lamp', 'origin': [5000, 5000, 0], 'static': True}]              # off the zone
        json.dump({'decor': decor}, open(lp, 'w'))
        props, rep = sg.import_props(sp, lp, ['old=hall'])
        self.assertEqual([p['model'] for p in props['hall']], ['bench'])
        self.assertEqual(rep['kept'], 1)

    def test_headroom_is_checked(self):
        def mut(d):
            d['zones'][0]['ceiling'] = 60
        self.assertTrue(any('ceiling' in m for m in errors(scene(mut))))


def write_scene(tmp, d, files):
    for name, data in files.items():
        json.dump(data, open(os.path.join(tmp, name), 'w'))
    sp = os.path.join(tmp, 'scene.json')
    json.dump(d, open(sp, 'w'))
    return sg.Scene.load(sp)


class DressAndLightTests(unittest.TestCase):
    def test_dress_files_append_props_lights_and_solids_after_the_props_files(self):
        tmp = tempfile.mkdtemp()
        d = copy.deepcopy(BASE)
        d['zones'][0]['props'] = [{'model': 'own', 'at': [100, 100]}]
        d['zones'][0]['lights'] = [{'at': [200, 200], 'h': 200}]
        d['zones'][0]['solids'] = [{'rect': [10, 10, 40, 40], 'z0': 0, 'z1': 64}]
        d['props_files'] = ['p.json']
        d['dress_files'] = ['a.json', 'b.json']
        sc = write_scene(tmp, d, {
            'p.json': {'hall': [{'model': 'kept', 'at': [120, 120]}]},
            'a.json': {'hall': {'props': [{'model': 'dress_a', 'at': [140, 140]}],
                                'lights': [{'at': [500, 400], 'z': 240, 'type': 'spot', 'dir': [0, 0, -1], 'inner': 20, 'outer': 40}],
                                'solids': [{'rect': [900, 600, 1000, 700], 'z0': 0, 'z1': 96, 'mat': 'conc_dark'}]},
                       'side': {'lights': [{'at': [1400, 1100]}]}},
            'b.json': {'hall': {'props': [{'model': 'dress_b', 'at': [160, 160]}]}}})
        hall = sc.zones['hall']
        self.assertEqual([p['model'] for p in hall.props], ['own', 'kept', 'dress_a', 'dress_b'])
        self.assertEqual(len(hall.lights), 2)
        self.assertEqual([s['rect'] for s in hall.solids], [(10, 10, 40, 40), (900, 600, 1000, 700)])
        self.assertEqual(hall.solids[1]['mat'], 'conc_dark')
        self.assertEqual(len(sc.zones['side'].lights), 1)
        self.assertEqual(sc.zones['low'].lights, [])
        self.assertEqual(errors(sc), [])
        recs = hall.light_records()
        self.assertEqual(recs[0]['origin'], [200.0, 200.0, 200.0])           # h above the floor at that point
        self.assertEqual(recs[1]['type'], 'spot')
        self.assertEqual((recs[1]['inner'], recs[1]['outer']), (20.0, 40.0))
        self.assertEqual(sc.zones['side'].light_records()[0]['origin'][2], 192 - 16)   # default: 16 under the ceiling

    def test_a_dress_file_naming_an_unknown_zone_or_key_is_refused(self):
        tmp = tempfile.mkdtemp()
        d = copy.deepcopy(BASE)
        d['dress_files'] = ['a.json']
        sc = write_scene(tmp, d, {'a.json': {'nowhere': {'lights': []}}})
        self.assertTrue(any('unknown zone nowhere' in m for m in errors(sc)))
        with self.assertRaises(sg.SceneError):
            write_scene(tmp, d, {'a.json': {'hall': {'lamps': []}}})

    def test_bad_lights_are_refused(self):
        for light, word in (({'at': [5000, 5000]}, 'outside the zone'), ({'at': [100, 100], 'z': 400}, 'ceiling'),
                            ({'at': [100, 100], 'type': 'area'}, 'omni or spot'),
                            ({'at': [100, 100], 'type': 'spot', 'inner': 70, 'outer': 40}, 'cone')):
            def mut(d, light=light):
                d['zones'][0]['lights'] = [light]
            e = errors(scene(mut))
            self.assertTrue(any(word in m for m in e), (light, e))

    def test_a_zone_without_lights_gets_a_fill_grid_aimed_at_the_flat_texel(self):
        sc = scene()
        hall = sc.zones['hall']
        self.assertTrue(hall.wants_fill())
        fill = hall.fill_lights()
        self.assertEqual(len(fill), 4 * 3)                  # 1024 x 768 at a spacing of 256 (the 256 headroom)
        self.assertTrue(all(f['fill'] and f['type'] == 'omni' and f['origin'][2] == 128 for f in fill))
        inten = fill[0]['intensity']
        self.assertGreater(inten, 0)
        # the estimate the intensity was chosen with meets the flat texel's luminance (ambient included)
        est = hall.direct_estimate(fill) * inten * sg.FILL_BOUNCE + sg.BAKE_AMBIENT * 0.8
        self.assertAlmostEqual(est, sg.FLAT_LUMA, delta=0.002)

        def lit(d):
            d['zones'][0]['lights'] = [{'at': [500, 400]}]
        self.assertFalse(scene(lit).zones['hall'].wants_fill())

        def forced(d):
            d['zones'][0]['lights'] = [{'at': [500, 400]}]
            d['zones'][0]['fill'] = True
        self.assertTrue(scene(forced).zones['hall'].wants_fill())


@unittest.skipUnless(HAVE_TEMPLATE, 'stock cp_zmb dump not present (set IWZ_TEMPLATE_DUMP_CP)')
class EmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = os.path.join(cls.tmp.name, 'src')
        path = os.path.join(cls.tmp.name, 'scene.json')
        base = copy.deepcopy(BASE)
        base['interactions'][0]['powered'] = True
        base['interactions'] += [{'kind': 'perk', 'perk': 'tough', 'zone': 'side', 'wall': 'east', 't': 0.5},
                                 {'kind': 'wall_buy', 'class': 'smg', 'price': 1250, 'zone': 'hall', 'wall': 'south', 's': 300},
                                 {'kind': 'wall_buy', 'class': 'smg', 'price': 1500, 'zone': 'side', 'wall': 'north', 's': 1500},
                                 {'kind': 'power', 'zone': 'low', 'wall': 'west', 't': 0.5}]
        base['dress_files'] = ['dress.json']
        json.dump({'hall': {'lights': [{'at': [500, 400], 'h': 240, 'type': 'spot', 'dir': [0, 0, -1], 'inner': 20, 'outer': 45,
                                        'color': [1, 0.7, 0.4], 'radius': 300, 'intensity': 1.2, 'fixture': 'lamp_model',
                                        'fixture_z': 252}]}},
                  open(os.path.join(cls.tmp.name, 'dress.json'), 'w'))
        json.dump(base, open(path, 'w'))
        cls.report = sg.emit(path, TEMPLATE, cls.out, log=lambda *_: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_output_is_written(self):
        for n in ('world.bin', 'colmap.hkx', 'navgraph.bin', 'ents.txt', 'triggers.txt', 'layout.json', 'plan.json', 'cp_iwz.gsc'):
            self.assertTrue(os.path.isfile(os.path.join(self.out, n)), n)
        self.assertEqual(self.report['problems'], [])
        self.assertEqual(self.report['spawners'], 10)

    def test_layout_lights_carry_the_dressing_and_fill_the_rest(self):
        lay = json.load(open(os.path.join(self.out, 'layout.json')))
        own = [l for l in lay['lights'] if not l.get('fill')]
        self.assertEqual(len(own), 1)
        l = own[0]
        self.assertEqual((l['zone'], l['origin'], l['type'], l['color'], l['radius'], l['intensity']),
                         ('hall', [500.0, 400.0, 240.0], 'spot', [1.0, 0.7, 0.4], 300.0, 1.2))
        self.assertEqual((l['dir'], l['inner'], l['outer'], l['fixture']), ([0.0, 0.0, -1.0], 20.0, 45.0, 'lamp_model'))
        filled = {f['zone'] for f in lay['lights'] if f.get('fill')}
        self.assertEqual(filled, {'low', 'side'})          # the hall has its own light: no fill there
        self.assertIn('lamp_model 500 400 252 0 0 0 1', open(os.path.join(self.out, 'smodels.txt')).read())
        self.assertEqual(self.report['lights']['own'], 1)

    def test_the_baker_reads_the_layout_lights(self):
        bake_dir = os.path.join(HERE, 'bake')
        try:
            sys.path.insert(0, bake_dir)
            import layout_lights  # noqa: F401  (needs numpy: the bake python)
        except ImportError:
            self.skipTest('numpy not present (run with the bake python)')
        finally:
            sys.path.remove(bake_dir)
        import subprocess
        out = os.path.join(self.tmp.name, 'lights.json')
        r = subprocess.run([sys.executable, '-I', os.path.join(bake_dir, 'layout_lights.py'), self.out, out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        cfg = json.load(open(out))
        lay = json.load(open(os.path.join(self.out, 'layout.json')))
        self.assertEqual(len(cfg['lights']), len(lay['lights']))
        spot = next(x for x in cfg['lights'] if x['type'] == 'spot')
        self.assertEqual((spot['origin'], spot['inner'], spot['outer'], spot['room']), ([500.0, 400.0, 240.0], 20.0, 45.0, 'hall'))
        self.assertAlmostEqual(spot['intensity'], 1.2 * 3.0)
        self.assertAlmostEqual(spot['radius'], 300 * 2.5)

    def test_the_collision_holds_no_degenerate_triangle(self):
        import iwz_emitcheck as ec
        self.assertEqual(ec.check_degenerate(ec.Emit.load(self.out)), [])

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

    def test_lab_plans_cover_every_case_with_an_expectation(self):
        plans = sg.lab_plans(self.out, per_plan=3)
        self.assertEqual(plans[0]['name'], 'cp_test_w1a_survey')
        expects = [st for pl in plans for st in pl['steps'] if st['do'] == 'expect']
        self.assertEqual(len(expects), 4 * 3)      # per case: zombies arrive, the player walks forward and back
        tags = [st['tag'] for pl in plans for st in pl['steps'] if st['do'] == 'spawn']
        self.assertTrue(all(t.replace('_', '').isalnum() and t == t.lower() for t in tags), tags)

    def test_the_level_script_carries_the_doors(self):
        gsc = open(os.path.join(self.out, 'cp_iwz.gsc')).read()
        self.assertIn('iwz_door( "D1", "iwz_door_D1"', gsc)
        self.assertNotIn('//@DOORS@', gsc)

    def test_each_wall_weapon_place_keeps_its_own_price(self):
        gsc = open(os.path.join(self.out, 'cp_iwz.gsc')).read()
        self.assertNotIn('//@PRICES@', gsc)
        self.assertIn('"iw7_ump45_zml", 1250 );', gsc)
        self.assertIn('"iw7_ump45_zml", 1500 );', gsc)

    def test_system_plans_use_every_thing_and_judge_the_game_state(self):
        plans = {p['name']: p for p in sg.w1b_plans(self.out)}
        self.assertEqual(sorted(plans), ['cp_test_w1b_powered_client', 'cp_test_w1b_rounds', 'cp_test_w1b_systems', 'cp_test_w1b_walls'])
        sysp = plans['cp_test_w1b_systems']['steps']
        uses = [s['name'] for s in sysp if s['do'] == 'use']
        # the powered perk first, the unpowered one refused, the switch, then the unpowered one bought
        self.assertEqual(uses, ['pk_revive_prepower', 'pk_tough_nopower', 'power', 'pk_tough'])
        walls = plans['cp_test_w1b_walls']['steps']
        spent = sorted(s['eq'] for s in walls if s['do'] == 'expect' and s['that'].endswith('.spent'))
        self.assertEqual(spent, [1250, 1500])
        self.assertEqual(sum(1 for s in walls if s['do'] == 'take'), 2)

    def test_the_walk_plan_walks_each_route_with_the_forward_key(self):
        pl = sg.walk_plan(self.out, pairs=[('hall', 'side')])
        walks = [s for s in pl['steps'] if s['do'] == 'walk']
        self.assertEqual(len(walks), 1)
        self.assertTrue(2 <= len(walks[0]['path']) <= 40)
        self.assertEqual(walks[0]['name'], 'walk_hall_side')


if __name__ == '__main__':
    unittest.main()
