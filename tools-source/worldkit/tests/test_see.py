"""iw7_see tests on the synthetic world: a made-up camera, a depth image drawn by the tool itself and then changed
(a thing added in front, a prop taken away). No game file, no frame of the game."""
import contextlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import iw7_see as S  # noqa: E402
import iw7_world as W  # noqa: E402
import synthetic as SY  # noqa: E402

np = S.np
if np is None:
    raise unittest.SkipTest('iw7_see needs numpy')
QUIET = lambda *a: None  # noqa: E731
WIDTH, HEIGHT = 320, 180


def box_mesh(lo, hi):
    c = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    quads = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
    tris = [(q[0], q[1], q[2]) for q in quads] + [(q[0], q[2], q[3]) for q in quads]
    return c, tris


def xsb_bytes(name, surfaces):
    """A model-surfaces file in the dump's stream form: counted arrays, with arrays of other widths after each surface."""
    outer = bytearray(56)
    struct.pack_into('<H', outer, 16, len(surfaces))
    out = b'\x08\x01' + struct.pack('<I', 1) + bytes(outer) + b'\x06\x01' + name.encode() + b'\0'
    heads = b''
    for verts, tris in surfaces:
        h = bytearray(256)
        struct.pack_into('<HHH', h, 0, 0x82, len(verts), len(tris))
        heads += bytes(h)
    out += b'\x08\x01' + struct.pack('<I', len(surfaces)) + heads
    for verts, tris in surfaces:
        out += b'\x08\x01' + struct.pack('<I', len(verts))
        for v in verts:
            out += struct.pack('<3f', *v) + bytes(20)
        out += b'\x08\x01' + struct.pack('<I', len(tris)) + b''.join(struct.pack('<3H', *t) for t in tris)
        out += b'\x08\x00' + b'\x0a\x01' + struct.pack('<I', 5) + b'\x01\x02\x03\x04\x05' + b'\x0a\x00'
    return out


def write_models(root):
    os.makedirs(os.path.join(root, 'xmodel'), exist_ok=True)
    os.makedirs(os.path.join(root, 'xsurface'), exist_ok=True)
    # model_a: a cube of 10 around its origin, written as two surfaces (the synthetic world stores that box for it);
    # model_b: a cube of 4 around its origin
    lower, upper = box_mesh((-5, -5, -5), (5, 5, 0)), box_mesh((-5, -5, 0), (5, 5, 5))
    for model, surfaces in (('model_a', [lower, upper]), ('model_b', [box_mesh((-2, -2, -2), (2, 2, 2))])):
        surf = model + '_lod0'
        SY.put(os.path.join(root, 'xmodel', model + '.xmb'), b'\x08\x01\x01\0\0\0' + bytes(40) + model.encode() + b'\0tag_origin\0mtl/x\0' + surf.encode() + b'\0')
        SY.put(os.path.join(root, 'xsurface', surf + '.xsb'), xsb_bytes(surf, surfaces))


def camera_doc(name, depth_file=None, origin=(50.0, 130.0, 40.0)):
    doc = {'schema': 'iw7.see-camera/1', 'name': name, 'frame': {'file': name + '.bmp', 'width': WIDTH * 2, 'height': HEIGHT * 2},
           'camera': {'tan_half_fov': [1.0, 0.5625], 'origin': list(origin), 'axis': [[0, -1, 0], [1, 0, 0], [0, 0, 1]], 'z_near': 4.0},
           'depth': [{'file': depth_file}] if depth_file else []}
    doc['camera_at_request'] = doc['camera']
    return doc


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='see-test-')
        cls.root = os.path.join(cls.tmp, 'dump')
        SY.write_world(cls.root)
        write_models(cls.root)
        cls.db = os.path.join(cls.tmp, 'world.sqlite')
        W.build(cls.root, cls.db, log=QUIET)
        cls.report = S.build_index(cls.db, cls.root, log=QUIET)
        cls.scene = S.Scene(cls.db)
        cls.rundir = os.path.join(cls.tmp, 'run')
        os.makedirs(os.path.join(cls.rundir, 'perf'))
        cls.cache = os.path.join(cls.tmp, 'cache')
        # frame "plain": the static world as the tool draws it. The depth buffer has half the size of the frame.
        cls.plain = cls.write_frame('plain')
        # frame "thing": the same, with a box that is not in the map: 20 x 20 x 20 floating 40 above the floor
        c, t = box_mesh((40, 40, 40), (60, 60, 60))
        cls.thing = cls.write_frame('thing', extra=np.array([[c[i] for i in tri] for tri in t], dtype=np.float64))
        # frame "hidden": prop 1 (the box in the middle of the view) is not drawn
        cls.hidden = cls.write_frame('hidden', skip=[S.prop_id(1)])

    @classmethod
    def write_frame(cls, name, extra=None, skip=()):
        bare = os.path.join(cls.rundir, 'perf', 'see-%s.json' % name)
        with open(bare, 'w') as f:
            json.dump(camera_doc(name), f)
        frame = S.Frame(bare)
        frame.set_size(WIDTH, HEIGHT)
        z, ids = cls.scene.render(frame, skip=skip)
        if extra is not None:
            zf, idf = z.ravel().copy(), ids.ravel().copy()
            S.raster(frame.view(extra), np.full(len(extra), 0, dtype=np.int32), zf, idf, frame)
            z = zf.reshape(z.shape)
        S.write_float_bmp(os.path.join(cls.rundir, name + '__z.bmp'), S.z_to_device(z, frame.depth_model))
        with open(bare, 'w') as f:
            json.dump(camera_doc(name, name + '__z.bmp'), f)
        return S.Frame(os.path.join(cls.rundir, name + '.bmp'))

    @classmethod
    def tearDownClass(cls):
        cls.scene.w.con.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = S.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class Models(Base):
    def test_index_reads_every_model_with_its_exact_box(self):
        self.assertEqual((self.report['models'], self.report['read'], self.report['failed']), (2, 2, []))
        v, t = self.scene.meshes['model_a']
        self.assertEqual((len(v), len(t)), (16, 24))                    # two surfaces of 8 vertices and 12 triangles
        self.assertEqual((v.min(0).tolist(), v.max(0).tolist()), ([-5, -5, -5], [5, 5, 5]))
        self.assertEqual(int(t.max()), 15)                              # the second surface's indices are shifted

    def test_a_truncated_surfaces_file_is_refused(self):
        data = xsb_bytes('m', [box_mesh((0, 0, 0), (1, 1, 1))])
        with self.assertRaises(S.SeeError):
            S.read_xsb(data[:-60], 'cut')
        with self.assertRaises(S.SeeError):
            S.model_mesh(self.root, 'no_such_model')

    def test_a_prop_is_placed_with_its_axis_and_scale(self):
        # prop 2: model_b (a cube of 4) at (90, 90, 10), turned on three axes, scale 2: every corner 2 * sqrt(12) away
        tri, ids = next(self.scene.prop_tris([2]))
        d = np.linalg.norm(tri.reshape(-1, 3) - np.array([90.0, 90.0, 10.0]), axis=1)
        self.assertTrue(np.allclose(d, 2 * 12 ** 0.5, atol=1e-4))
        self.assertEqual(set(ids.tolist()), {S.prop_id(2)})


class Camera(Base):
    def test_project_and_unproject_are_inverse(self):
        f = self.plain
        x, y, z = f.project(np.array([50.0, 20.0, 40.0]))               # straight ahead, 110 away
        self.assertAlmostEqual(float(x), WIDTH / 2)
        self.assertAlmostEqual(float(y), HEIGHT / 2)
        self.assertAlmostEqual(float(z), 110.0)
        p = np.array([63.0, 31.0, 12.0])
        x, y, z = f.project(p)
        self.assertTrue(np.allclose(f.unproject(float(x), float(y), float(z)), p))
        # left of the view is +x here, so a point with a larger x lands on a smaller pixel x; a lower point on a larger y
        self.assertLess(float(x), WIDTH / 2)
        self.assertGreater(float(y), HEIGHT / 2)

    def projections(self, origin, yaw, pitch, tanx, count=200, seed=3, centre=(0.0, 0.0)):
        """What the engine would record: world points and where a camera puts them, in frame pixels (float32 like the engine)."""
        import math
        import random
        y, p = math.radians(yaw), math.radians(pitch)
        fwd = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p)])
        left = np.array([-math.sin(y), math.cos(y), 0.0])
        up = np.cross(fwd, left)
        fw, fh = WIDTH * 2, HEIGHT * 2
        fx = fw * 0.5 / tanx
        rnd, rows = random.Random(seed), []
        while len(rows) < count:
            pt = np.array([rnd.uniform(-9000, 9000), rnd.uniform(-9000, 9000), rnd.uniform(-2000, 4000)])
            v = pt - np.array(origin)
            f = float(v @ fwd)
            if f < 20:
                continue
            sx = fw * 0.5 + centre[0] - fx * float(v @ left) / f
            sy = fh * 0.5 + centre[1] - fx * float(v @ up) / f
            if 0 <= sx <= fw and 0 <= sy <= fh:
                rows.append([float(np.float32(c)) for c in (pt[0], pt[1], pt[2], sx, sy)])
        return rows, fwd, left, up

    def test_the_camera_is_solved_from_the_engine_projection(self):
        origin = [467.25, 3677.5, 60.125]
        rows, fwd, left, up = self.projections(origin, 271.3, 7.5, 0.85)
        doc = {'schema': 'iw7.see-camera/2', 'name': 'solved', 'frame': {'width': WIDTH * 2, 'height': HEIGHT * 2},
               'projection_at_request': rows, 'projection_after': rows, 'depth': []}
        path = os.path.join(self.tmp, 'see-solved.json')
        with open(path, 'w') as f:
            json.dump(doc, f)
        frame = S.Frame(path)
        self.assertLess(float(np.abs(frame.origin - np.array(origin)).max()), 0.02)
        for got, want in ((frame.forward, fwd), (frame.left, left), (frame.up, up)):
            self.assertLess(float(np.abs(got - want).max()), 1e-5)
        self.assertLess(abs(frame.tanx - 0.85), 1e-5)
        self.assertLess(abs(frame.tany - 0.85 * 9 / 16), 1e-5)
        r = S.answer_camera(frame)
        self.assertEqual((r['yaw'], r['pitch']), (-88.7, 7.5))
        self.assertLess(r['solved_from']['worst_error_pixels'], 0.01)
        self.assertEqual(r['moved_between_request_and_after'], {'origin': 0.0, 'axis': 0.0})
        # the same point through the solved camera lands where the engine put it
        x, y, _ = frame.project(np.array(rows[0][:3]))
        self.assertLess(abs(float(x) - rows[0][3]) + abs(float(y) - rows[0][4]), 0.01)

    def test_a_moved_camera_and_wrong_points_are_seen(self):
        rows, _, _, _ = self.projections([100.0, 200.0, 60.0], 10.0, 0.0, 0.85, seed=5)
        later, _, _, _ = self.projections([100.0, 203.0, 60.0], 12.0, 0.0, 0.85, seed=5)
        spoiled = [list(r) for r in rows]
        for k in (3, 40, 77):                                           # points the engine clamped to the screen edge
            spoiled[k][3], spoiled[k][4] = 0.0, 0.0
        doc = {'schema': 'iw7.see-camera/2', 'name': 'moved', 'frame': {'width': WIDTH * 2, 'height': HEIGHT * 2},
               'projection_at_request': spoiled, 'projection_after': later, 'depth': []}
        path = os.path.join(self.tmp, 'see-moved.json')
        with open(path, 'w') as f:
            json.dump(doc, f)
        frame = S.Frame(path)
        self.assertEqual(frame.solved['used'], frame.solved['points'] - 3)
        self.assertLess(float(np.abs(frame.origin - np.array([100.0, 200.0, 60.0])).max()), 0.02)
        moved = frame.moved()
        self.assertLess(abs(moved['origin'] - 3.0), 0.05)
        self.assertGreater(moved['axis'], 0.03)
        doc['projection_at_request'] = rows[:5]
        with open(path, 'w') as f:
            json.dump(doc, f)
        with self.assertRaises(S.SeeError):
            S.Frame(path)

    def test_a_file_that_is_not_a_camera_is_refused(self):
        doc = camera_doc('bad')
        doc['camera']['axis'] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        path = os.path.join(self.tmp, 'see-bad.json')
        with open(path, 'w') as f:
            json.dump(doc, f)
        with self.assertRaises(S.SeeError):
            S.Frame(path)
        with self.assertRaises(S.SeeError):
            S.Frame(os.path.join(self.tmp, 'nothing.bmp'))

    def test_the_depth_file_keeps_every_float(self):
        a = np.array([[0.0, 1.5e-7, 0.25], [1.0, 3.0e38, 7.0]], dtype=np.float32)
        path = os.path.join(self.tmp, 'f.bmp')
        S.write_float_bmp(path, a)
        b, w, h = S.read_float_bmp(path)
        self.assertEqual((w, h), (3, 2))
        self.assertTrue((a == b).all())


class Raster(Base):
    def test_one_triangle_covers_the_pixels_whose_centres_are_inside(self):
        f = S.Frame(self.plain.json_path)
        f.set_size(8, 8)
        f.fx = f.fy = f.cx = f.cy = 4.0                                 # tangents of 1 on both axes
        # a view-space triangle (forward, left, up) at depth 10 covering the upper left quarter and a bit more
        tv = np.array([[[10.0, 10.0, 10.0], [10.0, -2.0, 10.0], [10.0, 10.0, -2.0]]])
        z, ids = np.full(64, S.FAR), np.zeros(64, dtype=np.int32)
        S.raster(tv, np.array([7], dtype=np.int32), z, ids, f)
        got = ids.reshape(8, 8) == 7
        want = np.array([[x + y + 1 <= 4.8 for x in range(8)] for y in range(8)])      # centre (x + .5, y + .5): x + y + 1 <= 4.8
        self.assertTrue((got == want).all())
        self.assertTrue(np.allclose(z[ids == 7], 10.0))

    def test_a_triangle_through_the_near_plane_is_cut_not_lost(self):
        f = S.Frame(self.plain.json_path)
        f.set_size(16, 16)
        tv = np.array([[[-50.0, 0.0, -5.0], [200.0, 60.0, -5.0], [200.0, -60.0, -5.0]]])    # a floor strip from behind the eye
        z, ids = np.full(256, S.FAR), np.zeros(256, dtype=np.int32)
        S.raster(tv, np.array([3], dtype=np.int32), z, ids, f)
        self.assertGreater(int((ids == 3).sum()), 20)
        self.assertGreaterEqual(float(z[ids == 3].min()), f.near_clip - 1e-6)

    def test_the_nearest_triangle_wins(self):
        z, ids = self.scene.render(self.plain)
        x, y, _ = self.plain.project(np.array([50.0, 25.0, 2.5]))       # the front face of prop 1
        self.assertEqual(int(ids[int(y), int(x)]), S.prop_id(1))
        self.assertAlmostEqual(float(z[int(y), int(x)]), 105.0, places=3)


class Answers(Base):
    def pixel_of(self, frame, point):
        x, y, _ = frame.project(np.array(point, dtype=np.float64))
        return int(float(x) * 2), int(float(y) * 2)                     # frame pixels: the frame is twice the depth buffer

    def test_at_names_a_prop_a_surface_and_a_thing_that_is_not_in_the_map(self):
        r = S.answer_at(self.scene, self.plain, *self.pixel_of(self.plain, (50, 25, 2.5)))
        self.assertEqual((r['kind'], r['prop'], r['model']), ('prop', 1, 'model_a'))
        self.assertLess(abs(r['z'] - 105.0), 0.5)
        self.assertLess(abs(r['position'][1] - 25.0), 0.5)
        r = S.answer_at(self.scene, self.plain, *self.pixel_of(self.plain, (20, 0, 60)))
        self.assertEqual((r['kind'], r['material']), ('surface', 'mat_wall'))
        r = S.answer_at(self.scene, self.thing, *self.pixel_of(self.thing, (50, 60, 50)))
        self.assertEqual(r['kind'], 'dynamic or unknown')
        self.assertLess(abs(r['z'] - 70.0), 0.5)                        # the box's front face is 70 from the camera
        self.assertIn('in_front_of', r)

    def test_at_says_when_a_database_prop_was_not_drawn(self):
        r = S.answer_at(self.scene, self.hidden, *self.pixel_of(self.hidden, (50, 25, 2.5)))
        self.assertEqual(r['kind'], 'surface')
        self.assertEqual(r['not_drawn_in_front'][0]['prop'], 1)

    def test_at_without_depth_answers_from_the_database_and_says_so(self):
        path = os.path.join(self.tmp, 'see-nodepth.json')
        with open(path, 'w') as f:
            json.dump(camera_doc('nodepth'), f)
        frame = S.Frame(path)
        r = S.answer_at(self.scene, frame, *self.pixel_of(self.plain, (50, 25, 2.5)))
        self.assertEqual((r['prop'], r['depth']), (1, 'not captured'))
        with self.assertRaises(S.SeeError):
            S.answer_visible(self.scene, frame, prop=1)

    def test_project_tells_hidden_from_seen(self):
        r = S.answer_project(self.scene, self.plain, [50, 12, 1])       # behind prop 1
        self.assertEqual((r['state'], r['occluder']['prop']), ('occluded', 1))
        self.assertEqual(S.answer_project(self.scene, self.plain, [50, 25, 2.5])['state'], 'visible, a surface is drawn there')
        self.assertEqual(S.answer_project(self.scene, self.plain, [50, 60, 50])['state'], 'visible, nothing drawn there')
        self.assertEqual(S.answer_project(self.scene, self.plain, [50, 200, 50])['state'], 'behind the camera')
        self.assertEqual(S.answer_project(self.scene, self.plain, [5000, 20, 50])['state'], 'outside the frame')

    def test_visible_counts_pixels_and_what_hides_them(self):
        r = S.answer_visible(self.scene, self.plain, prop=1)
        t = r['total']
        # the cube's lower half is under the floor: the floor hides it, and that is counted as hidden, not as missing
        self.assertGreater(t['visible'], 100)
        self.assertGreater(t['occluded'], 50)
        self.assertEqual((t['visible'] + t['occluded'], t['absent']), (t['projected'], 0))
        # taken away, the prop still "agrees" where it touched the floor (the floor right behind it is as far): a thin band
        hid = S.answer_visible(self.scene, self.hidden, prop=1)['total']
        self.assertLess(hid['visible'], 0.2 * hid['projected'])
        self.assertGreater(hid['absent'], 0.5 * hid['projected'])     # the rest is the half under the floor
        # a nearer thing in front of prop 1: a box 30 wide at y 40..45, from the floor to z 40
        c, tr = box_mesh((35, 40, 0), (65, 45, 40))
        extra = np.array([[c[i] for i in tri] for tri in tr], dtype=np.float64)
        covered = type(self).write_frame('covered', extra=extra)
        cov = S.answer_visible(self.scene, covered, prop=1)['total']
        self.assertEqual(cov['visible'], 0)
        self.assertEqual(cov['fraction_occluded'], 1.0)
        by_model = S.answer_visible(self.scene, self.plain, model='MODEL_A')
        self.assertEqual(by_model['props_seen'], 2)                     # props 0 and 1; prop 3 is far away, out of view

    def test_objects_lists_the_frame_the_thing_and_the_missing_prop(self):
        r = S.table(self.scene, self.plain, self.cache)
        names = {S._name(o) for o in r['objects']}
        self.assertTrue({'prop 0 model_a', 'prop 1 model_a', 'surface 0 mat_floor', 'surface 1 mat_wall'} <= names)
        self.assertEqual((r['dynamic'], r['missing'], r['summary']['nearer_than_static']), ([], [], 0))
        r = S.table(self.scene, self.thing, self.cache)
        self.assertEqual(len(r['dynamic']), 1)
        b = r['dynamic'][0]
        self.assertLess(abs(b['nearest_z'] - 70.0), 0.5)
        self.assertLess(abs(b['lowest_point_above_floor'] - 40.0), 2.5)   # the floating box: its lowest seen point is 40 up
        r = S.table(self.scene, self.hidden, self.cache)
        self.assertEqual([m['prop'] for m in r['missing']], [1])
        self.assertNotIn('prop 1 model_a', {S._name(o) for o in r['objects']})

    def test_floor_reads_above_and_below(self):
        self.assertEqual(S.answer_floor(self.scene, None, point=[30, 60, 40])['height'], 40.0)
        r = S.answer_floor(self.scene, None, point=[30, 60, -20])
        self.assertEqual((r['height'], r['reading'], r['floor']['material']), (-20.0, 'below the surface by 20.0', 'mat_floor'))
        self.assertEqual(S.answer_floor(self.scene, None, point=[10, 10, 11])['height'], 6.0)        # the top of prop 0 is at 5
        self.assertIsNone(S.answer_floor(self.scene, None, point=[5000, 5000, 0])['floor'])
        px = self.pixel_of(self.thing, (50, 60, 41))
        r = S.answer_floor(self.scene, self.thing, pixel=px)
        self.assertLess(abs(r['height'] - 41.0), 2.5)

    def test_compare_lists_what_went_away(self):
        r = S.answer_compare(self.scene, self.plain, self.hidden, self.cache)
        self.assertTrue(r['same_camera'])
        self.assertEqual([o['prop'] for o in r['disappeared']], [1])
        self.assertEqual((r['appeared'], r['missing_only_in_b'][0]['prop']), ([], 1))
        self.assertGreater(r['pixels_whose_depth_changed'], 100)
        back = S.answer_compare(self.scene, self.hidden, self.plain, self.cache)
        self.assertEqual([o['prop'] for o in back['appeared']], [1])
        # a thing that is not in the map came: one group, floating 40 above the floor, 20 tall
        came = S.answer_compare(self.scene, self.plain, self.thing, self.cache)
        self.assertEqual((len(came['appeared_not_in_map']), came['disappeared_not_in_map'], came['disappeared'], came['appeared']), (1, [], [], []))
        thing = came['appeared_not_in_map'][0]
        self.assertLess(abs(thing['lowest_point_above_floor'] - 40.0), 2.5)
        self.assertLess(abs(thing['seen_height'] - 20.0), 3.0)
        self.assertEqual(len(S.answer_compare(self.scene, self.thing, self.plain, self.cache)['disappeared_not_in_map']), 1)

    def test_the_fit_finds_the_depth_convention(self):
        r = S.answer_fit(self.scene, self.plain, self.cache)
        m = self.plain.depth_model
        self.assertLess(abs(r['a'] - m['a']), 1e-6)
        self.assertLess(abs(r['b'] - m['b']) / m['b'], 1e-4)

    def test_the_command_line(self):
        frame = os.path.join(self.rundir, 'plain.bmp')
        x, y = self.pixel_of(self.plain, (50, 25, 2.5))
        code, out, _ = self.cli('at', frame, str(x), str(y), '--db', self.db, '--json')
        self.assertEqual((code, json.loads(out)['prop']), (0, 1))
        code, out, _ = self.cli('objects', frame, '--db', self.db, '--cache', self.cache)
        self.assertEqual(code, 0)
        self.assertIn('prop 1 model_a', out)
        code, out, _ = self.cli('floor', frame, '--db', self.db, '--point', '30,60,40')
        self.assertIn('above the surface by 40.0', out)
        code, out, _ = self.cli('compare', frame, os.path.join(self.rundir, 'hidden.bmp'), '--db', self.db, '--cache', self.cache)
        self.assertIn('disappeared: prop 1 model_a', out)
        code, _, err = self.cli('at', frame, '99999', '0', '--db', self.db)
        self.assertEqual(code, 2)
        self.assertIn('outside', err)
        code, _, err = self.cli('at', os.path.join(self.rundir, 'nope.bmp'), '1', '1', '--db', self.db)
        self.assertEqual(code, 2)
        code, out, _ = self.cli('camera', frame, '--json')
        self.assertEqual(json.loads(out)['depth_size'], [WIDTH, HEIGHT])

    def test_without_the_model_index_props_are_their_boxes(self):
        scene = S.Scene(self.db, boxes=True)
        try:
            self.assertFalse(scene.have_meshes)
            r = S.answer_at(scene, self.plain, *self.pixel_of(self.plain, (50, 25, 2.5)))
            self.assertEqual((r['prop'], r['mesh']), (1, 'bounding box'))
        finally:
            scene.w.con.close()


if __name__ == '__main__':
    unittest.main()
