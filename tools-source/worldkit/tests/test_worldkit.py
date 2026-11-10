"""worldkit tests on a synthetic world (3 surfaces, 4 props, 2 lights, 3 entities) written with the dump conventions."""
import contextlib
import io
import itertools
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import iw7_dump as D  # noqa: E402
import iw7_world as W  # noqa: E402
import synthetic as S  # noqa: E402

QUIET = lambda *a: None  # noqa: E731


def build_world(root, **kw):
    S.write_world(root, **kw)
    db = os.path.join(root, 'world.sqlite')
    W.build(root, db, log=QUIET)
    return db


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='worldkit-test-')
        cls.root = os.path.join(cls.tmp, 'dump')
        cls.db = build_world(cls.root)
        cls.w = W.World(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.w.con.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)


class BuildTests(Base):
    def test_every_table_and_count(self):
        c = self.w.meta['counts']
        self.assertEqual((c['surfaces'], c['smodels'], c['primaryLights'], c['probes'], c['models'], c['entities']), (3, 4, 2, 1, 1, 3))
        self.assertEqual(self.w.meta['declared_counts'], {'surfaces': 3, 'smodels': 4, 'primaryLights': 2, 'probes': 1, 'models': 1})
        self.assertEqual(c['triangles'], 6)
        self.assertEqual(c['vertices'], 12)
        q = lambda t: self.w.q('SELECT count(*) n FROM %s' % t)[0]['n']  # noqa: E731
        self.assertEqual([q(t) for t in ('smodels', 'surfaces', 'lights', 'probes', 'ents', 'brush_models', 'tris')], [4, 3, 2, 1, 3, 1, 6])
        self.assertEqual(q('ent_kv'), 2 + 4 + 4)
        self.assertEqual(self.w.q('SELECT count(*) n FROM ent_kv WHERE i=1')[0]['n'], 4)

    def test_meta_records_files_parse_end_and_hashes(self):
        files = {f['kind']: f for f in self.w.meta['files']}
        self.assertTrue(files['gfxmap']['parsed_to_end'])
        self.assertEqual(files['gfxmap']['parsed_bytes'], files['gfxmap']['bytes'])
        self.assertTrue(files['gfxmap_tr']['parsed_to_end'])
        self.assertEqual(len(files['gfxmap']['sha256']), 64)
        self.assertIn('navmesh (listed, not read)', files)
        self.assertEqual(self.w.meta['reader_version'], W.READER_VERSION)

    def test_repeated_names_resolve_through_repeat_records(self):
        # model_a and mat_floor are written twice or more: the second record is a type 9 repeat
        self.assertEqual([r['model'] for r in self.w.q('SELECT model FROM smodels ORDER BY i')], ['model_a', 'model_a', 'model_b', 'model_a'])
        self.assertEqual([r['material'] for r in self.w.q('SELECT material FROM surfaces ORDER BY i')], ['mat_floor', 'mat_wall', 'mat_floor'])

    def test_props_columns(self):
        r = self.w.q('SELECT * FROM smodels WHERE i=2')[0]
        self.assertEqual((r['x'], r['y'], r['z'], r['scale'], r['cullDist'], r['flags'], r['lmIndex']), (90, 90, 10, 2.0, 4000, 0x66, -1))
        ax = S.axis_for(30, 45, 20)
        for a in range(3):
            for b in range(3):
                self.assertAlmostEqual(r['a%d%d' % (a, b)], ax[a][b], places=6)
        self.assertEqual((r['bmid_x'], r['bhalf_x']), (90, 5))

    def test_angles_round_trip_to_the_same_matrix(self):
        for r in self.w.q('SELECT * FROM smodels'):
            m = [[r['a%d%d' % (a, b)] for b in range(3)] for a in range(3)]
            back = W.angles_to_axis(r['pitch'], r['yaw'], r['roll'])
            self.assertLess(W.max_matrix_diff(m, back), 1e-4)
        self.assertLess(self.w.meta['worst_angle_roundtrip'], 1e-4)
        self.assertLess(self.w.meta['worst_orthonormality'], 1e-3)

    def test_surfaces_bounds_from_vertices_in_use(self):
        r = {s['i']: s for s in self.w.q('SELECT * FROM surfaces')}
        self.assertEqual((r[0]['minx'], r[0]['maxx'], r[0]['miny'], r[0]['maxy'], r[0]['minz'], r[0]['maxz']), (0, 100, 0, 100, 0, 0))
        self.assertEqual((r[1]['miny'], r[1]['maxy'], r[1]['minz'], r[1]['maxz']), (0, 0, 0, 100))
        self.assertEqual((r[1]['vertex_count'], r[1]['used_vertices'], r[1]['tri_count'], r[1]['first_vertex']), (8, 4, 2, 0))
        self.assertEqual((r[2]['minx'], r[2]['maxx']), (1000, 1100))
        self.assertEqual((r[0]['sb_minx'], r[0]['sb_maxx']), (0, 100))

    def test_lights_entities_probes_and_assets(self):
        a, b = self.w.q('SELECT * FROM lights ORDER BY i')
        self.assertEqual((a['type_name'], a['x'], a['y'], a['z'], a['radius'], a['defName'], a['placed']), ('omni', 20, 20, 50, 300, 'light_omni', 1))
        self.assertEqual((a['color_r'], a['color_g'], a['color_b'], a['dir_z'], a['entityId']), (1.0, 0.5, 0.25, -1.0, 100))
        self.assertAlmostEqual(a['outer_deg'], 120.0, places=4)
        self.assertEqual(b['type_name'], 'spot')
        e = self.w.q('SELECT * FROM ents ORDER BY i')
        self.assertEqual([x['classname'] for x in e], ['worldspawn', 'script_struct', 'script_model'])
        self.assertEqual((e[1]['targetname'], e[1]['origin_x'], e[1]['origin_y']), ('spawn', 50, 50))
        self.assertIsNone(e[0]['origin_x'])
        self.assertEqual(e[2]['model'], 'model_a')
        kv = self.w.q("SELECT key, key_name, value FROM ent_kv WHERE i=1 AND key_name='origin'")
        self.assertEqual(kv, [{'key': '543', 'key_name': 'origin', 'value': '50 50 0'}])
        self.assertEqual(self.w.q('SELECT livePath, x, y, z FROM probes')[0], {'livePath': 'probe_a', 'x': 1.0, 'y': 2.0, 'z': 3.0})
        kinds = {r['kind']: r['name'] for r in self.w.q('SELECT kind, name FROM assets')}
        self.assertEqual((kinds['lightmap'], kinds['transient_zone']), ('*lightmap0', 'synth'))
        self.assertEqual(self.w.q('SELECT surfaceCount FROM brush_models')[0]['surfaceCount'], 2)

    def test_models_table_and_catalog_join(self):
        cat = os.path.join(self.tmp, 'catalog.json')
        with open(cat, 'w') as f:
            json.dump({'models': [{'name': 'model_a', 'category': 'prop', 'numLods': 3, 'radius': 9.5,
                               'bounds': {'mins': [-1, -2, -3], 'maxs': [1, 2, 3]}, 'lods': [{'lod': 0, 'tris': 77}]}]}, f)
        db = os.path.join(self.tmp, 'cat.sqlite')
        W.build(self.root, db, catalog=cat, log=QUIET)
        w = W.World(db)
        rows = {r['name']: r for r in w.q('SELECT * FROM models')}
        self.assertEqual((rows['model_a']['instances'], rows['model_a']['in_catalog'], rows['model_a']['lod0_tris'], rows['model_a']['bmax_z']), (3, 1, 77, 3))
        self.assertEqual((rows['model_b']['instances'], rows['model_b']['in_catalog'], rows['model_b']['lod0_tris']), (1, 0, None))
        w.con.close()


class MeshTests(Base):
    def test_surface_mesh_decodes_and_remaps(self):
        m = self.w.surface_mesh(1)
        self.assertEqual(m['material'], 'mat_wall')
        self.assertEqual(m['positions'], [(0, 0, 0), (100, 0, 0), (100, 0, 100), (0, 0, 100)])
        self.assertEqual(m['tris'], [(0, 1, 2), (0, 2, 3)])
        self.assertEqual(m['uvs'][1], (1.0, 0.0))
        self.assertEqual(m['lmuvs'][2], (1.0, 1.0))
        for n in m['normals']:
            self.assertAlmostEqual(n[1], -1.0, delta=2e-3)
            self.assertAlmostEqual(math.sqrt(sum(c * c for c in n)), 1.0, delta=3e-3)
        far = self.w.surface_mesh(2)
        self.assertEqual(far['positions'][0], (1000, 1000, 0))
        self.assertEqual(far['normals'][0][2] < 0.01, True)

    def test_unknown_surface_is_an_error(self):
        with self.assertRaises(W.WorldError):
            self.w.surface_mesh(99)


class QueryTests(Base):
    BOX_A = (-10, -10, -10, 70, 40, 60)

    def test_box(self):
        r = self.w.box(self.BOX_A)
        self.assertEqual([p['i'] for p in r['props']], [0, 1])
        self.assertEqual([l['i'] for l in r['lights']], [0])
        self.assertEqual(r['ents'], [])
        self.assertEqual(len(r['surfaces_touching']), 2)
        self.assertEqual(r['triangles'], 2)   # centroid rule: one triangle of the floor, one of the wall
        r = self.w.box((-10, -10, -10, 200, 200, 200))
        self.assertEqual((len(r['props']), len(r['lights']), len(r['ents']), r['triangles']), (3, 1, 1, 4))
        # corners given in any order
        self.assertEqual(self.w.box((200, 200, 200, -10, -10, -10))['triangles'], 4)

    def test_near(self):
        r = self.w.near((10, 10, 0), 50, ('props',))
        self.assertEqual([p['i'] for p in r['props']], [0, 1])
        self.assertAlmostEqual(r['props'][1]['dist'], math.sqrt(40 ** 2 + 10 ** 2), places=6)
        self.assertEqual(self.w.near((10, 10, 0), 60, ('lights',))['lights'][0]['i'], 0)
        self.assertEqual(self.w.near((10, 10, 0), 50, ('lights',))['lights'], [])
        self.assertNotIn('props', self.w.near((10, 10, 0), 50, ('lights',)))
        self.assertEqual(self.w.near((1000, 1000, 0), 20, ('ents',))['ents'][0]['classname'], 'script_model')
        s = self.w.near((50, 50, 0), 5, ('surfaces',))['surfaces']
        self.assertEqual(s, [])

    def test_find_and_where_model(self):
        rows = self.w.find_model('model_')
        self.assertEqual([(r['model'], r['n']) for r in rows], [('model_a', 3), ('model_b', 1)])
        self.assertAlmostEqual(rows[0]['cx'], (10 + 50 + 1000) / 3.0, places=6)
        self.assertEqual(self.w.find_model('100%'), [])
        self.assertEqual([r['i'] for r in self.w.where_model('model_a')], [0, 1, 3])

    def test_rooms(self):
        r = self.w.rooms(100)
        self.assertEqual(r['cells'][0]['cell'], [0, 0])
        self.assertEqual({k: r['cells'][0][k] for k in ('props', 'lights', 'ents', 'triangles')}, {'props': 3, 'lights': 1, 'ents': 1, 'triangles': 4})
        self.assertEqual({k: r['cells'][1][k] for k in ('props', 'lights', 'ents', 'triangles')}, {'props': 1, 'lights': 1, 'ents': 1, 'triangles': 2})
        self.assertEqual(len(r['cells']), 2)
        with self.assertRaises(W.WorldError):
            self.w.rooms(0)

    def test_check_reports_files_and_outliers(self):
        c = self.w.check()
        self.assertEqual((c['props']['models_with_file'], c['props']['models_without_file'], c['props']['bad_names']), (2, 0, 0))
        self.assertEqual((c['materials']['with_file'], c['materials']['without_file']), (2, 0))
        self.assertEqual((c['outliers']['props_outside'], c['outliers']['surfaces_outside']), (0, 0))
        os.remove(os.path.join(self.root, 'xmodel', 'model_b.xmb'))
        try:
            c = self.w.check()
            self.assertEqual((c['props']['models_without_file'], c['props']['missing_examples']), (1, ['model_b']))
        finally:
            S.put(os.path.join(self.root, 'xmodel', 'model_b.xmb'), b'x')

    def test_cli_text_and_json(self):
        def run(*argv):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = W.main(list(argv))
            return code, out.getvalue()
        code, text = run('stats', '--db', self.db)
        self.assertEqual(code, 0)
        self.assertIn('surfaces', text)
        self.assertIn('n/a', text)   # no independent ground truth for a synthetic map
        code, text = run('stats', '--db', self.db, '--json')
        s = json.loads(text)
        self.assertEqual([c['read'] for c in s['counts']], [3, 4, 2, 1, 1])
        self.assertEqual(s['props_bbox']['x1'], 1000)
        code, text = run('box', '--db', self.db, *map(str, self.BOX_A), '--json')
        self.assertEqual(json.loads(text)['triangles'], 2)
        code, text = run('near', '--db', self.db, '10', '10', '0', '--radius', '50', '--kind', 'props')
        self.assertIn('model_a', text)
        code, text = run('rooms', '--db', self.db, '--cell', '512', '--limit', '3')
        self.assertIn('props', text)
        code, text = run('find-model', '--db', self.db, 'model_b')
        self.assertIn('model_b', text)
        code, text = run('where-model', '--db', self.db, 'model_a', '--json')
        self.assertEqual(len(json.loads(text)), 3)


class PrefabTests(Base):
    BOX_A = (-10, -10, -10, 70, 40, 60)

    def extract(self, name='room', box=None):
        out = os.path.join(self.tmp, name)
        shutil.rmtree(out, ignore_errors=True)
        return out, W.extract(self.w, box or self.BOX_A, name, out)

    def test_extract_counts_origin_and_relative_coordinates(self):
        out, p = self.extract()
        self.assertEqual(p['schema'], 'iw7.prefab/1')
        self.assertEqual(p['counts'], {'props': 2, 'lights': 1, 'ents': 0, 'surfaces': 2, 'triangles': 2, 'vertices': 6})
        self.assertEqual(p['origin'], [30.0, 15.0, -10.0])    # centre of the box floor
        self.assertEqual(p['props'][0]['pos'], [-20.0, -5.0, 10.0])
        self.assertEqual(p['lights'][0]['pos'], [-10.0, 5.0, 60.0])
        self.assertEqual((p['lights'][0]['defName'], p['lights'][0]['color']), ('light_omni', [1.0, 0.5, 0.25]))
        loaded = W.load_prefab(out)
        self.assertEqual(loaded['counts'], p['counts'])
        m = W.read_prefab_surface(out, loaded, 0)
        self.assertEqual(len(m['tris']), 1)
        self.assertEqual(sorted(m['positions']), sorted([(-30.0, -15.0, 10.0), (70.0, -15.0, 10.0), (70.0, 85.0, 10.0)]))
        self.assertEqual(len(m['normals']), 3)
        self.assertEqual(len(m['lmuvs']), 3)

    def test_extract_triangle_centroid_rule(self):
        out, p = self.extract('wide', (-10, -10, -10, 200, 200, 200))
        self.assertEqual(p['counts']['triangles'], 4)
        self.assertEqual(p['counts']['ents'], 1)
        self.assertEqual(p['ents'][0]['origin'], [50 - 95.0, 50 - 95.0, 10.0])
        self.assertIn(['543', '-45 -45 10'], p['ents'][0]['kv'])
        out, p = self.extract('narrow', (60, 0, -10, 70, 10, 5))   # only the first floor triangle has its centroid here
        self.assertEqual((p['counts']['triangles'], p['counts']['surfaces']), (0, 0))
        out, p = self.extract('floor', (60, 30, -10, 70, 36, 5))
        self.assertEqual((p['counts']['triangles'], p['counts']['surfaces']), (1, 1))

    def test_smodels_txt_is_the_generator_format(self):
        out, p = self.extract()
        lines = S.get(os.path.join(out, 'smodels.txt'), 'r').splitlines()
        self.assertEqual(lines[0], 'model_a -20 -5 10 0 0 0 1')
        self.assertEqual(lines[1], 'model_a 20 5 10 0 90 0 1')
        for ln in lines:
            f = ln.split()
            self.assertEqual(len(f), 8)
            [float(x) for x in f[1:]]

    def test_the_angles_in_smodels_txt_rebuild_the_stored_axis(self):
        # the map compiler turns "pitch yaw roll" into the axis with its own routine; prove the same matrix comes back
        for r in self.w.q('SELECT * FROM smodels'):
            m = [[r['a%d%d' % (a, b)] for b in range(3)] for a in range(3)]
            line = '%s %s %s %s' % (W.fmt(r['pitch']), W.fmt(r['yaw']), W.fmt(r['roll']), r['model'])
            p, y, ro = (float(v) for v in line.split()[:3])
            self.assertLess(W.max_matrix_diff(m, W.angles_to_axis(p, y, ro)), 1e-4)

    def test_place_yaw_90_is_exact(self):
        out, p = self.extract()
        out2 = os.path.join(self.tmp, 'placed90')
        q = W.place(out, (0, 0, 0), 90, out2)
        self.assertEqual(q['props'][0]['pos'], [5.0, -20.0, 10.0])
        self.assertEqual(q['lights'][0]['pos'], [-5.0, -10.0, 60.0])
        self.assertAlmostEqual(q['props'][0]['yaw'], 90.0, places=4)
        self.assertAlmostEqual(q['props'][1]['yaw'], 180.0, places=3)
        self.assertEqual(q['lights'][0]['dir'], [0.0, 0.0, -1.0])
        m = W.read_prefab_surface(out2, W.load_prefab(out2), 0)
        self.assertIn((15.0, -30.0, 10.0), m['positions'])
        self.assertTrue(os.path.isfile(os.path.join(out2, 'smodels.txt')))
        self.assertEqual(S.get(os.path.join(out2, 'smodels.txt'), 'r').splitlines()[0], 'model_a 5 -20 10 0 90 0 1')

    def test_place_preserves_distances_and_round_trips(self):
        out, p = self.extract('wide2', (-10, -10, -10, 200, 200, 200))
        for yaw in (37.5, -123.0, 180.0, 270.0):
            out2 = os.path.join(self.tmp, 'placed')
            q = W.place(out, (100, 200, 5), yaw, out2)
            self.assertEqual(q['origin'], [100.0, 200.0, 5.0])
            for a, b in itertools.combinations(range(len(p['props'])), 2):
                d0, d1 = math.dist(p['props'][a]['pos'], p['props'][b]['pos']), math.dist(q['props'][a]['pos'], q['props'][b]['pos'])
                self.assertAlmostEqual(d0, d1, places=9)
            # orientation: yaw is added to the prop's yaw (about the vertical axis)
            for a, b in zip(p['props'], q['props']):
                diff = (b['yaw'] - a['yaw'] - yaw + 180) % 360 - 180
                if abs(a['pitch']) < 89:
                    self.assertAlmostEqual(diff, 0.0, places=3)
            back = os.path.join(self.tmp, 'back')
            r = W.place(out2, (0, 0, 0), -yaw, back)
            for a, b in zip(p['props'], r['props']):
                for k in range(3):
                    self.assertAlmostEqual(a['pos'][k], b['pos'][k], places=9)
            ma = W.read_prefab_surface(out, p, 0)
            mb = W.read_prefab_surface(out2, W.load_prefab(out2), 0)
            for i, j in itertools.combinations(range(len(ma['positions'])), 2):
                self.assertAlmostEqual(math.dist(ma['positions'][i], ma['positions'][j]), math.dist(mb['positions'][i], mb['positions'][j]), places=3)
            # entity angles turn with the prefab
            self.assertEqual(len(q['ents']), 1)
        e = W.place(out, (0, 0, 0), 90, os.path.join(self.tmp, 'e90'))['ents'][0]
        self.assertIn(['65', '0 90 0'], e['kv'])

    def test_place_puts_the_prefab_in_world_coordinates(self):
        out, p = self.extract()
        q = W.place(out, (100, 200, 5), 180, os.path.join(self.tmp, 'world180'))
        self.assertEqual(q['space'], 'world')
        self.assertEqual(q['props'][0]['pos'], [120.0, 205.0, 15.0])     # (-20, -5, 10) turned half a way round, then moved
        self.assertEqual(S.get(os.path.join(self.tmp, 'world180', 'smodels.txt'), 'r').splitlines()[0].split()[1:4], ['120', '205', '15'])
        # a world-space prefab can be placed again: back to the first position
        r = W.place(os.path.join(self.tmp, 'world180'), (100, 200, 5), 180, os.path.join(self.tmp, 'world0'))
        self.assertEqual(r['props'][0]['pos'], [80.0, 195.0, 15.0])

    def test_place_rejects_a_foreign_folder(self):
        os.makedirs(os.path.join(self.tmp, 'empty'), exist_ok=True)
        with self.assertRaises(W.WorldError):
            W.place(os.path.join(self.tmp, 'empty'), (0, 0, 0), 0, os.path.join(self.tmp, 'nope'))

    def test_cli_extract_and_place(self):
        out = os.path.join(self.tmp, 'cli_room')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(W.main(['extract', '--db', self.db, '--box', *map(str, self.BOX_A), '--name', 'cli_room', '--out', out]), 0)
            self.assertEqual(W.main(['place', '--prefab', out, '--at', '1', '2', '3', '--yaw', '90', '--out', out + '_p']), 0)
        self.assertIn('props 2', buf.getvalue())
        self.assertEqual(W.load_prefab(out + '_p')['origin'], [1.0, 2.0, 3.0])


class AngleTests(unittest.TestCase):
    def test_round_trip_random_and_special_angles(self):
        rnd = random.Random(7)
        cases = [(0, 0, 0), (90, 0, 0), (-90, 33, 0), (45, 45, 45), (0, 180, 0), (0, -180, 0), (89.999, 10, 20), (30, 270, -170)]
        cases += [(rnd.uniform(-90, 90), rnd.uniform(-180, 180), rnd.uniform(-180, 180)) for _ in range(500)]
        worst = 0.0
        for c in cases:
            ax = W.angles_to_axis(*c)
            worst = max(worst, W.max_matrix_diff(ax, W.angles_to_axis(*W.axis_to_angles(ax))))
        self.assertLess(worst, 1e-9)

    def test_yaw_90_rotates_forward_to_left_of_x(self):
        f, left, up = W.angles_to_axis(0, 90, 0)
        self.assertLess(abs(f[0]) + abs(f[1] - 1) + abs(f[2]), 1e-12)
        self.assertLess(abs(left[0] + 1) + abs(left[1]) + abs(left[2]), 1e-12)
        self.assertLess(abs(up[2] - 1), 1e-12)

    def test_exact_cos_sin_for_quarter_turns(self):
        self.assertEqual([W._cos_sin(a) for a in (0, 90, 180, 270, -90, 360)],
                         [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0), (0.0, -1.0), (1.0, 0.0)])


class FailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='worldkit-fail-')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, **kw):
        root = os.path.join(self.tmp, 'd')
        shutil.rmtree(root, ignore_errors=True)
        S.write_world(root, **kw)
        return root

    def gfx(self, root):
        return os.path.join(root, 'maps', 'x', 'synth.d3dbsp.gfxmap')

    def expect(self, root, *needles):
        with self.assertRaises(W.WorldError) as cm:
            W.build(root, os.path.join(self.tmp, 'o.sqlite'), log=QUIET)
        msg = str(cm.exception)
        for n in needles:
            self.assertIn(n, msg)
        return msg

    def test_truncated_gfxmap_names_the_offset(self):
        root = self.build()
        data = S.get(self.gfx(root))
        S.put(self.gfx(root), data[:-100])
        msg = self.expect(root, 'offset')
        self.assertRegex(msg, r'offset \d+ \(0x[0-9a-f]+\)')

    def test_trailing_bytes_are_an_error(self):
        root = self.build()
        S.put(self.gfx(root), S.get(self.gfx(root)) + bytes(5))
        self.expect(root, 'trailing bytes', 'offset')

    def test_count_that_overruns_the_file(self):
        root = self.build(index_count=1000)
        self.expect(root, 'draw.indices', 'file holds 18 elements but the structure declares 1000')

    def test_implausible_counts(self):
        self.expect(self.build(surface_count=10 ** 9), 'not plausible')
        self.expect(self.build(index_count=10 ** 9 + 7), 'not plausible')

    def test_surface_count_that_disagrees_with_the_array(self):
        self.expect(self.build(surface_count=5), 'dpvs.surfaces', 'declares 5')

    def test_truncated_zone_file(self):
        root = self.build()
        zp = os.path.join(root, 'transient_zones', 'synth.gfxmap_tr')
        data = S.get(zp)
        S.put(zp, data[:-10])
        self.expect(root, 'gfxmap_tr', 'offset')

    def test_missing_zone_file(self):
        root = self.build()
        os.remove(os.path.join(root, 'transient_zones', 'synth.gfxmap_tr'))
        self.expect(root, 'transient zone')

    def test_light_count_disagreement_between_files(self):
        root = self.build()
        p = os.path.join(root, 'maps', 'x', 'synth.d3dbsp.commap.json')
        j = json.loads(S.get(p, 'r'))
        j['primaryLight'].append(dict(j['primaryLight'][0], primaryLightIndex=2))
        S.put(p, json.dumps(j), 'w')
        self.expect(root, 'primary lights')

    def test_malformed_entities(self):
        root = self.build()
        p = os.path.join(root, 'maps', 'x', 'synth.d3dbsp.ents')
        S.put(p, '{' + chr(10) + '157 "a"' + chr(10), 'w')
        self.expect(root, 'ents', 'not closed')
        S.put(p, '157 "a"' + chr(10), 'w')
        self.expect(root, 'outside a block')
        S.put(p, chr(10).join(['{', '157 a', '}', '']), 'w')
        self.expect(root, 'key "value"')

    def test_missing_gfxmap(self):
        os.makedirs(os.path.join(self.tmp, 'empty', 'maps'))
        with self.assertRaises(W.WorldError):
            W.build(os.path.join(self.tmp, 'empty'), os.path.join(self.tmp, 'o.sqlite'), log=QUIET)

    def test_bad_repeat_record_is_caught(self):
        s = D.Stream(bytes([9]) + (99).to_bytes(4, 'little') + (0).to_bytes(4, 'little'), 'x')
        with self.assertRaises(D.WorldError):
            s.string()
        s = D.Stream(bytes([2, 0]), 'x')
        with self.assertRaises(D.WorldError) as cm:
            s.array(4, 1, 'thing')
        self.assertIn('found 2', str(cm.exception))

    def test_cli_exits_non_zero_with_a_message(self):
        root = self.build()
        S.put(self.gfx(root), S.get(self.gfx(root)) + bytes(1))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = W.main(['build', '--dump', root, '--db', os.path.join(self.tmp, 'o.sqlite')])
        self.assertEqual(code, 2)
        self.assertIn('trailing bytes', err.getvalue())
        proc = subprocess.run([sys.executable, '-B', os.path.join(os.path.dirname(HERE), 'iw7_world.py'), 'stats', '--db',
                               os.path.join(self.tmp, 'missing.sqlite')], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('database not found', proc.stderr)

    def test_a_database_from_another_reader_version_is_refused(self):
        root = self.build()
        db = os.path.join(self.tmp, 'o.sqlite')
        W.build(root, db, log=QUIET)
        import sqlite3
        con = sqlite3.connect(db)
        con.execute("UPDATE meta SET value='\"0.1.0\"' WHERE key='reader_version'")
        con.commit()
        con.close()
        with self.assertRaises(W.WorldError):
            W.World(db)


class LayoutTests(unittest.TestCase):
    def test_structure_sizes_match_the_asset_tools_asserts(self):
        # these are asserted at import; the test documents them
        self.assertEqual(D.layout('GfxWorld').size, 0x11A8)
        self.assertEqual(D.layout('GfxStaticModelDrawInst').size, 184)
        self.assertEqual(D.layout('GfxSurface').size, 48)
        self.assertEqual(D.layout('GfxWorldVertex').size, 44)
        self.assertEqual(D.layout('ComPrimaryLight').size, 144)
        self.assertEqual(D.layout('GfxWorld').off('dpvs.smodelCount'), 2976)

    def test_pure_python_and_numpy_builds_agree(self):
        tmp = tempfile.mkdtemp(prefix='worldkit-np-')
        try:
            root = os.path.join(tmp, 'd')
            S.write_world(root)
            script = os.path.join(os.path.dirname(HERE), 'iw7_world.py')
            dbs = []
            for flag in ('', '1'):
                env = dict(os.environ)
                env.pop('IW7_WORLD_NO_NUMPY', None)
                if flag:
                    env['IW7_WORLD_NO_NUMPY'] = flag
                db = os.path.join(tmp, 'w%s.sqlite' % flag)
                proc = subprocess.run([sys.executable, '-B', script, 'build', '--dump', root, '--db', db], capture_output=True, text=True, env=env)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                dbs.append(db)
            import sqlite3
            rows = []
            for db in dbs:
                con = sqlite3.connect(db)
                rows.append([con.execute('SELECT * FROM %s ORDER BY 1, 2' % t).fetchall() for t in ('surfaces', 'smodels', 'tris', 'lights')])
                con.close()
            self.assertEqual(rows[0], rows[1])
            self.assertEqual(S.get(dbs[0] + '.mesh'), S.get(dbs[1] + '.mesh'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class BinaryComWorldTests(unittest.TestCase):
    def test_binary_commap_parses_to_its_end(self):
        L = D.layout('ComPrimaryLight')
        d = S.Dumper()
        d.array(None, S.set_fields('ComWorld', primaryLightCount=1, numUmbraGates=1, primaryLightEnvCount=0, bakeQuality=3), 1, D.layout('ComWorld').size)
        d.string('cw')
        d.array(None, S.set_fields('ComPrimaryLight', type=3, origin__0=1.0, origin__1=2.0, origin__2=3.0, radius=9.0, cosHalfFovOuter=0.5), 1, L.size)
        d.string('light_def')
        d.absent()
        d.string(None)
        d.string('gate0')
        data = bytes(d.out)
        r = D.parse_commap_binary(data)
        self.assertEqual((r['primaryLight'][0]['type'], r['primaryLight'][0]['origin'], r['primaryLight'][0]['defName']), (3, [1.0, 2.0, 3.0], 'light_def'))
        self.assertEqual(r['umbraGateNames'], ['gate0'])
        with self.assertRaises(D.WorldError):
            D.parse_commap_binary(data + b'\0')
        with self.assertRaises(D.WorldError):
            D.parse_commap_binary(data[:-3])


if __name__ == '__main__':
    unittest.main()
