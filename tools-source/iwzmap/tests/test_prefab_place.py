"""Prefab placement in a generated map: synthetic prefabs only (no game data)."""
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
IWZMAP = os.path.dirname(HERE)
WORLDKIT = os.path.join(os.path.dirname(IWZMAP), 'worldkit')
sys.path.insert(0, IWZMAP)
sys.path.insert(0, WORLDKIT)
sys.path.insert(0, os.path.join(WORLDKIT, 'tests'))

import iw7_world as W  # noqa: E402
import synthetic as S  # noqa: E402
import prefab_place as PP  # noqa: E402
import prefab_proof  # noqa: E402
import prefab_room  # noqa: E402

QUIET = lambda *a: None  # noqa: E731


def forward(pitch, yaw):
    p, y = math.radians(pitch), math.radians(yaw)
    return (math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='prefab-place-test-')
        root = os.path.join(cls.tmp, 'dump')
        S.write_world(root)
        cls.db = os.path.join(root, 'world.sqlite')
        W.build(root, cls.db, log=QUIET)
        cls.w = W.World(cls.db)
        cls.rel = os.path.join(cls.tmp, 'room')
        W.extract(cls.w, (-10, -10, -10, 200, 200, 200), 'room', cls.rel)        # origin (95, 95, -10)
        cls.placed = os.path.join(cls.tmp, 'room_placed')
        W.place(cls.rel, (1095, 2095, 490), 0, cls.placed)                       # shift (1000, 2000, 500)
        cls.turned = os.path.join(cls.tmp, 'room_turned')
        W.place(cls.rel, (0, 0, 0), 90, cls.turned)

    @classmethod
    def tearDownClass(cls):
        cls.w.con.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)


class TransformTests(Base):
    def test_a_relative_prefab_is_refused(self):
        with self.assertRaises(PP.PrefabError):
            PP.load(self.rel)

    def test_source_and_placed_coordinates(self):
        p = PP.load(self.placed)
        self.assertEqual(PP.source_origin(p), (95.0, 95.0, -10.0))
        self.assertEqual(PP.to_placed(p, (10, 10, 0)), (1010.0, 2010.0, 500.0))
        self.assertEqual(PP.to_source(p, (1010, 2010, 500)), (10.0, 10.0, 0.0))
        self.assertEqual(PP.placed_box(p), (990.0, 1990.0, 490.0, 1200.0, 2200.0, 700.0))

    def test_a_quarter_turn_round_trips(self):
        p = PP.load(self.turned)
        q = PP.to_placed(p, (10, 10, 0))
        self.assertEqual(q, (85.0, -85.0, 10.0))                 # (-85, -85, 10) turned by 90 degrees
        self.assertEqual(PP.to_source(p, q), (10.0, 10.0, 0.0))
        # the placed prop sits where to_placed says its source position goes
        self.assertEqual(tuple(p['props'][0]['pos']), PP.to_placed(p, (10, 10, 0)))


class SurfaceTests(Base):
    def test_every_surface_and_triangle_goes_into_the_world_file(self):
        p = PP.load(self.placed)
        w = PP.WorldWriter()
        st = PP.add_surfaces(w, self.placed, p)
        self.assertEqual((st['prefab_surfaces'], st['surfaces_written'], st['triangles']), (2, 2, p['counts']['triangles']))
        self.assertEqual(st['with_tangents'], 2)
        r = PP.read_world(w.tobytes())
        self.assertEqual([s['material'] for s in r['surfaces']], ['mat_floor', 'mat_wall'])      # the shipped map's order
        self.assertEqual(sum(s['triangles'] for s in r['surfaces']), p['counts']['triangles'])
        self.assertEqual(r['vertices'], p['counts']['vertices'])
        self.assertEqual(list(r['bounds']), [1000.0, 2000.0, 500.0, 1100.0, 2100.0, 600.0])

    def test_vertices_keep_position_texture_lightmap_tangent_and_colour(self):
        p = PP.load(self.placed)
        w = PP.WorldWriter()
        PP.add_surfaces(w, self.placed, p)
        data = w.tobytes()
        r = PP.read_world(data)
        m = W.read_prefab_surface(self.placed, p, 0)
        got = [struct.unpack_from('<3ffI2f2fII', data, r['vertex_offset'] + 44 * k) for k in range(len(m['positions']))]
        for g, pos, uv, lm in zip(got, m['positions'], m['uvs'], m['lmuvs']):
            self.assertEqual(g[0:3], pos)
            self.assertEqual((g[3], g[4]), (1.0, 0xFFFFFFFF))
            self.assertEqual((g[5:7], g[7:9]), (uv, lm))
            self.assertEqual(g[9], PP.pack_unit((0, 0, 1)))
            self.assertEqual(g[10], PP.pack_unit((1, 0, 0)))

    def test_tangents_are_derived_when_a_prefab_has_none(self):
        mesh = {'positions': [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], 'normals': [(0, 0, 1)] * 4,
                'uvs': [(0, 0), (0, 1), (-1, 1), (-1, 0)], 'tris': [(0, 1, 2), (0, 2, 3)]}       # u grows along -y
        for t in PP.tangents_from_uvs(mesh):
            self.assertLess(max(abs(a - b) for a, b in zip(t, (0.0, -1.0, 0.0))), 1e-6)

    def test_a_large_mesh_is_split_under_the_surface_limits(self):
        w = PP.WorldWriter()
        w.MAX_VERTS = 8
        pos = [(float(k), 0.0, 0.0) for k in range(30)]
        tris = [(k, k + 1, k + 2) for k in range(0, 27, 3)]
        n = w.add('m', pos, [(0, 0, 1)] * 30, [(0, 0)] * 30, [(0, 0)] * 30, tris)
        r = PP.read_world(w.tobytes())
        self.assertEqual(n, len(r['surfaces']))
        self.assertGreater(n, 1)
        self.assertEqual(sum(s['triangles'] for s in r['surfaces']), 9)
        self.assertTrue(all(s['vertices'] <= 8 for s in r['surfaces']))

    def test_a_broken_world_file_is_refused(self):
        w = PP.WorldWriter()
        w.add_quad('m', [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], (0.0, 0.0, 1.0))
        with self.assertRaises(PP.PrefabError):
            PP.read_world(w.tobytes() + b'x')
        with self.assertRaises(PP.PrefabError):
            PP.read_world(b'\0' * 64)


class PropAndLightTests(Base):
    def test_prop_lines_carry_the_compiler_flags(self):
        p = PP.load(self.placed)
        p['props'][0]['flags'] = 0x256          # no-cast-shadow bit set
        p['props'][0]['cullDist'] = 1500
        lines = PP.smodel_lines(p)
        self.assertEqual(len(lines), len(p['props']))
        self.assertEqual(lines[0], 'model_a 1010 2010 500 0 0 0 1 noshadow cull=1500')
        self.assertNotIn('noshadow', lines[1])
        self.assertEqual(PP.smodel_lines(p, flags=False)[0], 'model_a 1010 2010 500 0 0 0 1')

    def test_light_lines_give_back_the_stored_direction_colour_and_cone(self):
        L = {'type': 2, 'pos': [1.0, 2.0, 3.0], 'color': [2000.0, 1000.0, 500.0], 'radius': 120.0, 'dir': [0.6, 0.0, 0.8],
             'cosHalfFovOuter': math.cos(math.radians(40.0))}
        O = {'type': 3, 'pos': [4.0, 5.0, 6.0], 'color': [10.0, 10.0, 5.0], 'radius': 50.0, 'dir': [0, 0, 1], 'cosHalfFovOuter': 0}
        sun = {'type': 1, 'pos': [0, 0, 0], 'color': [1, 1, 1], 'radius': 1.0, 'dir': [0, 0, 1], 'cosHalfFovOuter': 0}
        lines, skipped = PP.light_lines({'lights': [L, O, sun]})
        self.assertEqual(skipped, [1])
        f = lines[0].split()
        self.assertEqual((f[0], [float(v) for v in f[1:4]]), ('spot', [1.0, 2.0, 3.0]))
        self.assertEqual([float(v) for v in f[4:7]], [1.0, 0.5, 0.25])
        self.assertEqual((float(f[7]), float(f[8])), (2000.0, 120.0))
        d = forward(float(f[9]), float(f[10]))            # what the compiler stores for these angles
        self.assertLess(max(abs(a - b) for a, b in zip(d, (0.6, 0.0, 0.8))), 1e-4)
        self.assertAlmostEqual(float(f[11]), 80.0, places=3)
        self.assertEqual(lines[1], 'omni 4.000 5.000 6.000 1.00000 1.00000 0.50000 10.000 50.000')

    def test_the_synthetic_prefab_lights(self):
        lines, skipped = PP.light_lines(PP.load(self.placed))
        self.assertEqual((len(lines), skipped), (1, []))
        self.assertTrue(lines[0].startswith('omni 1020.000 2020.000 550.000'))


class CollisionTests(Base):
    def test_clip_keeps_the_part_inside_the_box_and_the_winding(self):
        tri = ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0))                # area 50, normal +z
        parts = PP.clip_triangle(tri, (0, 0, -1, 5, 5, 1))
        area = 0.0
        for a, b, c in parts:
            n = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            self.assertGreater(n, 0)
            area += n / 2
            for v in (a, b, c):
                self.assertTrue(0 <= v[0] <= 5 and 0 <= v[1] <= 5)
        self.assertAlmostEqual(area, 25.0)
        self.assertEqual(PP.clip_triangle(tri, (20, 20, -1, 30, 30, 1)), [])
        self.assertEqual(PP.clip_triangle(tri, (-5, -5, -1, 50, 50, 1)), [tri])

    def test_collision_file_round_trip_and_precedence(self):
        d = os.path.join(self.tmp, 'room_col')
        shutil.copytree(self.placed, d)
        p = PP.load(d)
        tris, tags, src = PP.prefab_collision(d, p)
        self.assertEqual((src, len(tris), set(tags)), ('render triangles', p['counts']['triangles'], {382}))
        one = [((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.5))]
        PP.write_collision(os.path.join(d, PP.COLLISION_FILE), one, [7])
        tris, tags, src = PP.prefab_collision(d, p)
        self.assertEqual((src, tags), ('prefab collision file', [7]))
        self.assertEqual(tris[0][2], (0.0, 1.0, 0.5))
        with open(os.path.join(d, PP.COLLISION_FILE), 'ab') as f:
            f.write(b'x')
        with self.assertRaises(PP.PrefabError):
            PP.read_collision(os.path.join(d, PP.COLLISION_FILE))


def floor(x0, y0, x1, y1, z):
    a, b, c, d = (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)
    return [(a, b, c), (a, c, d)]


def wall_x(x, y0, y1, z0, z1):
    a, b, c, d = (x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)
    return [(a, b, c), (a, c, d)]


class NavTests(unittest.TestCase):
    def test_cells_stand_on_floors_and_stop_at_walls(self):
        tris = floor(0, 0, 256, 128, 10.0) + wall_x(128.0, 0, 128, 10.0, 138.0)
        cells = PP.nav_cells(tris, (0, 0, 256, 128), 32)
        self.assertEqual(len(cells), 24)                             # the two columns that touch the wall are left out
        self.assertFalse(any(i in (3, 4) for i, _j in cells))
        self.assertEqual(set(cells.values()), {10.0})
        g = PP.TriGrid(tris)
        link = PP.nav_link(g, cells)
        self.assertTrue(link((0, 0), (1, 0)))
        reach = PP.largest_island(cells, [(0, 0)], link=link)
        self.assertEqual(len(reach), 12)
        self.assertTrue(all(i < 3 for i, _j in reach))
        both = {(3, 0): 10.0, (4, 0): 10.0, (5, 0): 40.0}
        link = PP.nav_link(g, both)
        self.assertFalse(link((3, 0), (4, 0)))                       # the wall at x = 128 runs between their centres
        self.assertFalse(link((4, 0), (5, 0)))                       # more than a step apart

    def test_no_cell_under_a_low_ceiling_or_on_a_box(self):
        tris = floor(0, 0, 128, 64, 0.0) + floor(64, 0, 128, 64, 40.0)             # a 40 unit shelf over half the floor
        cells = PP.nav_cells(tris, (0, 0, 128, 64), 32)
        self.assertEqual([cells[(i, 0)] for i in range(4)], [0.0, 0.0, 40.0, 40.0])     # never the floor under the shelf
        self.assertEqual(sorted(PP.largest_island(cells, [(0, 0)])), [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual(sorted(PP.nav_cells(tris, (0, 0, 128, 64), 32, min_z=20.0)), [(2, 0), (2, 1), (3, 0), (3, 1)])

    def test_the_largest_group_is_kept_without_a_seed(self):
        cells = {(0, 0): 0.0, (1, 0): 0.0, (5, 5): 0.0, (1, 1): 30.0}
        self.assertEqual(sorted(PP.largest_island(cells)), [(0, 0), (1, 0)])
        self.assertEqual(sorted(PP.largest_island(cells, [(5, 5)])), [(5, 5)])


class LiveCheckTests(Base):
    def live(self, p):
        return {'schema': 'iw7.world-live/1', 'props': [
            {'i': k, 'model': q['model'], 'origin': list(q['pos']), 'scale': q['scale'], 'cull': q.get('cullDist'),
             'axis': [c for row in W.angles_to_axis(q['pitch'], q['yaw'], q['roll']) for c in row]} for k, q in enumerate(p['props'])]}

    def test_identical_props_pass(self):
        p = PP.load(self.placed)
        r = PP.props_check(p, self.live(p))
        self.assertTrue(r['ok'])
        self.assertEqual((r['matched'], r['missing'], r['extra_live'], r['orientation_differs'], r['scale_differs']),
                         (len(p['props']), 0, 0, 0, 0))

    def test_a_moved_a_missing_and_an_extra_prop_are_found(self):
        p = PP.load(self.placed)
        live = self.live(p)
        live['props'][0]['origin'][0] += 0.5
        r = PP.props_check(p, live)
        self.assertFalse(r['ok'])
        self.assertEqual((r['missing'], r['extra_live']), (1, 1))
        self.assertAlmostEqual(r['missing_rows'][0]['nearest'], 0.5)
        live = self.live(p)
        live['props'].append({'model': 'other', 'origin': [0, 0, 0], 'scale': 1})
        self.assertEqual(PP.props_check(p, live)['extra_live'], 1)
        live = self.live(p)
        live['props'][1]['axis'][0] = 0.5
        live['props'][1]['scale'] = 3.0
        r = PP.props_check(p, live)
        self.assertEqual((r['orientation_differs'], r['scale_differs']), (1, 1))

    def test_cli_exit_codes(self):
        p = PP.load(self.placed)
        path = os.path.join(self.tmp, 'live.json')
        with open(path, 'w') as f:
            json.dump(self.live(p), f)
        self.assertEqual(PP.main(['props-check', self.placed, path]), 0)
        self.assertEqual(PP.main(['props-check', self.rel, path]), 2)
        self.assertEqual(PP.main(['info', self.placed]), 0)


class ProofTests(Base):
    SPEC = {'poses': [{'name': 'a', 'at': [10, 10, 0], 'yaw': 30}], 'stands': [{'name': 's', 'at': [20, 20, 0]}],
            'walks': [{'name': 'w', 'from': [10, 10, 0], 'to': [60, 10, 0]}], 'perf_seconds': 5}

    def test_the_two_plans_stand_in_the_same_spots(self):
        out = os.path.join(self.tmp, 'plans')
        a, b = prefab_proof.plans(self.placed, self.SPEC, out, 'cp_pfr', 'um')
        self.assertEqual((a['map'], a['usermap']), ('cp_pfr', 'um'))
        self.assertEqual(b['map'], PP.load(self.placed)['source']['map'])
        self.assertNotIn('usermap', b)
        tpa = [s for s in a['steps'] if s['do'] == 'tp']
        tpb = [s for s in b['steps'] if s['do'] == 'tp']
        self.assertEqual(len(tpa), 3)
        self.assertEqual((tpa[0]['at'], tpb[0]['at']), ([1010.0, 2010.0, 500.0], [10, 10, 0]))
        self.assertEqual([s['do'] for s in a['steps']], [s['do'] for s in b['steps']])
        wa = [s for s in a['steps'] if s['do'] == 'walk'][0]
        self.assertEqual(wa['to'], [1060.0, 2010.0, 500.0])
        self.assertTrue(os.path.isfile(os.path.join(out, 'placed.json')) and os.path.isfile(os.path.join(out, 'source.json')))

    def test_a_turned_prefab_turns_the_views(self):
        a, _b = prefab_proof.plans(self.turned, self.SPEC, os.path.join(self.tmp, 'plans90'))
        tp = [s for s in a['steps'] if s['do'] == 'tp'][0]
        self.assertEqual((tp['at'], tp['yaw']), ([85.0, -85.0, 10.0], 120.0))

    def test_compare_moves_the_generated_positions_back(self):
        ra, rb = os.path.join(self.tmp, 'run_a'), os.path.join(self.tmp, 'run_b')
        os.makedirs(ra); os.makedirs(rb)
        with open(os.path.join(ra, 'client.stdout.log'), 'w') as f:
            f.write('[Paris world] map=cp_pfr props=3 surfaces=3 lights=40 hidden=0\n'
                    '[IWZ local] GL MARK i=3 name=stand_s_b t=1 origin=(1020, 2020, 500.1) pitch=0 yaw=0 ground=1 weapon=x\n'
                    '[IWZ local] GL WALK i=9 seq=1 from=(1010, 2010, 500) to=(1040, 2010, 500) want=(1060, 2010, 500) moved=30 left=20 ms=5 ground=1\n')
        with open(os.path.join(rb, 'client.stdout.log'), 'w') as f:
            f.write('[Paris world] map=cp_zmb props=17010 surfaces=10760 lights=1039 hidden=0\n'
                    '[IWZ local] GL MARK i=3 name=stand_s_b t=1 origin=(20, 20, 0.1) pitch=0 yaw=0 ground=1 weapon=x\n'
                    '[IWZ local] GL WALK i=9 seq=1 from=(10, 10, 0) to=(41, 10, 0) want=(60, 10, 0) moved=31 left=19 ms=5 ground=1\n')
        rep = prefab_proof.compare(ra, rb, self.placed)
        self.assertEqual(rep['placed_stats']['props'], 3)
        self.assertEqual(rep['marks'][0]['placed'], [20.0, 20.0, 0.1])
        self.assertEqual(rep['marks'][0]['difference'], 0.0)
        self.assertEqual((rep['walks'][0]['placed_moved'], rep['walks'][0]['source_moved']), (30, 31))
        self.assertEqual(rep['walks'][0]['placed_end'], [40.0, 10.0, 0.0])


class RoomTests(Base):
    def test_the_room_generator_writes_a_complete_source(self):
        tpl = os.path.join(self.tmp, 'tpl')
        os.makedirs(os.path.join(tpl, 'maps', 'cp'))
        with open(os.path.join(tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'), 'w') as f:
            f.write('{\n157 "worldspawn"\n337 "1"\n}\n')
        seen = {}

        def fake_encode(tris, template, tag=0, max_tris=127, tags=None):
            seen.clear()
            seen.update(tris=list(tris), tags=list(tags))
            return b'HKX', {'sections': 1}
        real = prefab_room.hkcm_write.encode
        prefab_room.hkcm_write.encode = fake_encode
        try:
            out = os.path.join(self.tmp, 'src')
            rep = prefab_room.build(tpl, self.placed, out, collision='render', lot_margin=64, log=QUIET)
            first = dict(seen)
            dark = os.path.join(self.tmp, 'src_template_light')
            prefab_room.build(tpl, self.placed, dark, collision='none', lighting='template', lights=False, log=QUIET)
        finally:
            prefab_room.hkcm_write.encode = real
        for name in ('world.bin', 'colmap.hkx', 'navgraph.bin', 'ents.txt', 'smodels.txt', 'lights.txt', 'lighting.txt', 'layout.json',
                     'cp_pfr.gsc', 'cp_pfr.arena', 'prefab_report.json'):
            self.assertTrue(os.path.isfile(os.path.join(out, name)), name)
        self.assertFalse(os.path.exists(os.path.join(dark, 'lighting.txt')))
        self.assertFalse(os.path.exists(os.path.join(dark, 'lights.txt')))
        p = PP.load(self.placed)
        self.assertEqual((rep['surfaces']['written'], rep['surfaces']['triangles']), (2, p['counts']['triangles']))
        self.assertEqual(rep['world']['surfaces'], 3)                                 # the lot + the two prefab surfaces
        self.assertEqual((rep['props']['lines'], rep['lights']['lines'], rep['starts']), (len(p['props']), 1, 4))
        self.assertEqual(rep['collision']['from'], 'render triangles')
        # collision reaches the encoder in Havok units (1/32), lot and perimeter wall first
        n_lot = rep['collision']['lot_triangles']
        self.assertEqual(len(first['tris']), n_lot + p['counts']['triangles'])
        self.assertEqual(first['tags'][:n_lot], [prefab_room.LOT_TAG] * n_lot)
        zs = {round(v[2] * 32.0, 3) for t in first['tris'][:2] for v in t}
        self.assertEqual(zs, {rep['box'][2] - 1.0})
        with open(os.path.join(out, 'layout.json')) as f:
            lay = json.load(f)
        self.assertEqual(len(lay['starts']), 4)
        self.assertGreater(rep['nav']['reachable'], 0)
        with open(os.path.join(out, 'ents.txt')) as f:
            ents = f.read()
        self.assertEqual(ents.count('default_player_start'), 4)
        self.assertIn('worldspawn', ents)

    def test_cli_refuses_an_unplaced_prefab(self):
        self.assertEqual(prefab_room.main([self.tmp, self.rel, os.path.join(self.tmp, 'nope')]), 2)


if __name__ == '__main__':
    unittest.main()
