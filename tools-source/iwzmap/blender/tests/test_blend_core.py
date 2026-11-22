"""Unit tests of the pure part of the Blender exporter (no bpy). The end to end test needs the stock template dump and is skipped without it."""
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import blend_core as C  # noqa: E402
import mapgen  # noqa: E402

try:
    import numpy  # noqa: F401
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

TEMPLATE = C.default_template()
HAVE_TEMPLATE = os.path.isfile(os.path.join(TEMPLATE, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx'))
F = lambda *a: [float(x) for x in a]


def room_scene(extra=None):
    tris = C.box_tris((0, 0, -8), (800, 400, 0)) + C.box_tris((0, 0, 120), (800, 400, 128))
    for mn, mx in [((0, -8, 0), (800, 0, 120)), ((0, 400, 0), (800, 408, 120)), ((-8, 0, 0), (0, 400, 120)), ((800, 0, 0), (808, 400, 120)),
                   ((396, 0, 0), (404, 150, 120)), ((396, 250, 0), (404, 400, 120))]:
        tris += C.box_tris(mn, mx)
    sc = {'map': 'cp_iwz', 'meshes': [{'name': 'w', 'material': 'w/concrete_tiles_01', 'tris': tris}],
          'zones': [{'name': 'a', 'box': F(0, 0, -16, 396, 400, 120)}, {'name': 'b', 'box': F(404, 0, -16, 800, 400, 120)}],
          'starts': [{'at': F(100, 200, 0), 'yaw': 0}], 'spawners': [{'kind': 'ground', 'at': F(600, 200, 0), 'yaw': 180}],
          'doors': [{'name': 'd1', 'cost': 750, 'box': F(396, 150, 0, 404, 250, 100)}],
          'power': [{'at': F(100, 50, 0), 'yaw': 90}], 'perks': [{'at': F(700, 50, 0), 'yaw': 90, 'perk': 'revive'}],
          'wall_buys': [{'at': F(500, 20, 0), 'yaw': 90, 'weapon_class': 'smg', 'cost': 1000}]}
    sc.update(extra or {})
    return sc


class Geometry(unittest.TestCase):
    def test_box_faces_point_outward(self):
        for t in C.box_tris((0, 0, 0), (2, 3, 4)):
            n, _ = C.tri_normal(*t)
            c = [sum(p[i] for p in t) / 3 - (1, 1.5, 2)[i] for i in range(3)]
            self.assertGreater(sum(n[i] * c[i] for i in range(3)), 0)

    def test_degenerate_triangles_are_dropped_from_render_and_collision(self):
        m = mapgen.Mesh()
        wb = C.WorldBuilder(m, (0.8, 0.5), {})
        good = [[(0, 0, 0), (10, 0, 0), (0, 10, 0)]]
        bad = [[(0, 0, 0), (0, 0, 0), (5, 5, 5)], [(0, 0, 0), (5, 0, 0), (10, 0, 0)]]
        wb.add({'name': 'x', 'material': 'w/m', 'tris': good + bad})
        self.assertEqual((wb.render_tris, wb.col_tris, wb.degenerate), (1, 1, 2))

    def test_unshared_triangles_never_overflow_u16(self):
        # 25,000 triangles of 3 own vertices (75,000 vertices): one surface would overflow u16 relative indices
        m = mapgen.Mesh()
        wb = C.WorldBuilder(m, (0.8, 0.5), {})
        tris = [[(i * 3.0, 0, 0), (i * 3.0 + 2, 0, 0), (i * 3.0, 2, 0)] for i in range(25000)]
        wb.add({'name': 'big', 'material': 'w/m', 'tris': tris, 'mode': 'render'})
        self.assertEqual(wb.render_tris, 25000)
        self.assertGreaterEqual(len(m.materials), 2)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'world.bin')
            mapgen.write_world(m, p)
            b = open(p, 'rb').read()
            off = 12
            (nm,) = struct.unpack_from('<I', b, 8)
            for _ in range(nm):
                (n,) = struct.unpack_from('<H', b, off); off += 2 + n
            (nv,) = struct.unpack_from('<I', b, off); off += 4 + nv * 44
            (ni,) = struct.unpack_from('<I', b, off); off += 4 + ni * 2
            (ns,) = struct.unpack_from('<I', b, off); off += 4
            for _ in range(ns):
                mi, first, vc, base, tc = struct.unpack_from('<5I', b, off); off += 44
                self.assertLessEqual(vc, 65535)

    def test_vertices_are_welded_inside_a_surface(self):
        m = mapgen.Mesh()
        wb = C.WorldBuilder(m, (0.8, 0.5), {})
        wb.add({'name': 'q', 'material': 'w/m', 'tris': [[(0, 0, 0), (10, 0, 0), (10, 10, 0)], [(0, 0, 0), (10, 10, 0), (0, 10, 0)]]})
        verts, idx = m.mat('w/m|q')
        self.assertEqual((len(verts), len(idx)), (4, 6))

    def test_collision_only_mesh_is_not_rendered_and_keeps_its_tag(self):
        m = mapgen.Mesh()
        wb = C.WorldBuilder(m, (0.8, 0.5), {})
        wb.add({'name': 'clip', 'material': '', 'mode': 'collision', 'tag': 411, 'tris': [[(0, 0, 0), (10, 0, 0), (0, 10, 0)]]})
        self.assertEqual((wb.render_tris, wb.col_tris, m.col_tag), (0, 1, {0: 411}))


class Validation(unittest.TestCase):
    def errors(self, sc):
        return [m for s, m in C.validate(sc) if s == 'ERROR']

    def test_good_scene_has_no_error(self):
        self.assertEqual(self.errors(room_scene()), [])

    def test_door_cost_must_be_a_stock_debris_price(self):
        sc = room_scene()
        sc['doors'][0]['cost'] = 800
        self.assertTrue(any('stock debris' in e for e in self.errors(sc)))

    def test_door_must_be_thin(self):
        sc = room_scene()
        sc['doors'][0]['box'] = F(396, 150, 0, 500, 250, 100)
        self.assertTrue(any('at most 48' in e for e in self.errors(sc)))

    def test_zones_may_not_overlap_but_stacked_zones_may_touch(self):
        sc = room_scene()
        sc['zones'].append({'name': 'c', 'box': F(100, 100, -16, 300, 300, 120)})
        self.assertTrue(any('overlap' in e for e in self.errors(sc)))
        sc = room_scene()
        sc['zones'].append({'name': 'up', 'box': F(0, 0, 120, 396, 400, 300)})
        self.assertEqual(self.errors(sc), [])

    def test_names_perks_and_classes(self):
        sc = room_scene()
        sc['zones'][0]['name'] = 'Room A'
        sc['perks'][0]['perk'] = 'bogus'
        sc['wall_buys'][0]['weapon_class'] = 'bogus'
        e = ' | '.join(self.errors(sc))
        self.assertIn('lower case', e)
        self.assertIn('not a stock machine', e)
        self.assertIn('class', e)

    def test_start_and_mesh_material_rules(self):
        sc = room_scene()
        sc['starts'] = []
        sc['meshes'][0]['material'] = 'concrete'
        e = ' | '.join(self.errors(sc))
        self.assertIn('no player start', e)
        self.assertIn('not an IW7 world material', e)

    def test_zone_padding_closes_a_wall_gap(self):
        z = C.pad_zone_boxes(room_scene()['zones'])
        self.assertEqual((z[0]['box'][3], z[1]['box'][0]), (400.0, 400.0))
        far = C.pad_zone_boxes([{'name': 'a', 'box': F(0, 0, 0, 10, 10, 10)}, {'name': 'b', 'box': F(100, 0, 0, 110, 10, 10)}])
        self.assertEqual(far[0]['box'][3], 10.0)

    def test_door_zones_found_from_the_two_sides(self):
        sc = room_scene()
        self.assertEqual(C.door_zones(sc['doors'][0], sc['zones']), ['a', 'b'])


@unittest.skipUnless(HAVE_NUMPY, 'numpy')
class Navigation(unittest.TestCase):
    def test_single_layer_walks_a_room_and_reports_a_dropped_second_floor(self):
        floor = [tuple(map(tuple, t)) for t in C.box_tris((0, 0, -8), (400, 400, 0))]
        up = [tuple(map(tuple, t)) for t in C.box_tris((0, 0, 128), (400, 400, 136))]
        walls = [tuple(map(tuple, t)) for mn, mx in [((0, -8, 0), (400, 0, 280)), ((0, 400, 0), (400, 408, 280)), ((-8, 0, 0), (0, 400, 280)),
                                                      ((400, 0, 0), (408, 400, 280))] for t in C.box_tris(mn, mx)]
        cells, info = C.nav_single_layer(floor + walls, [(200, 200, 0)])
        self.assertGreater(len(cells), 60)
        self.assertEqual(info['dropped_upper_floors'], 0)
        self.assertTrue(all(abs(z - C.NAV_LIFT) < 1e-6 for z in cells.values()))
        # a second floor over the whole room, reachable only through a stair, is not representable: the ground stays
        cells2, info2 = C.nav_single_layer(floor + up + walls, [(200, 200, 0)])
        self.assertEqual(len(cells2), len(cells))
        self.assertTrue(all(z < 10 for z in cells2.values()))



def stair_scene(marked):
    """a 17 step flight (riser 8, tread 17, 112 wide) from a ground floor up to a landing at 136, walled in, roofless"""
    tris = C.box_tris((-100, 0, -8), (700, 400, 0)) + C.box_tris((332, 0, 0), (700, 400, 136))
    steps = []
    for i in range(17):
        steps += C.box_tris((60 + 17 * i, 100, 0), (60 + 17 * (i + 1), 212, 8 * (i + 1)))
    walls = []
    for mn, mx in [((-100, -8, 0), (700, 0, 300)), ((-100, 400, 0), (700, 408, 300)), ((-108, 0, 0), (-100, 400, 300)), ((700, 0, 0), (708, 400, 300)),
                   ((40, 92, 0), (332, 100, 300)), ((40, 212, 0), (332, 220, 300))]:
        walls += C.box_tris(mn, mx)
    return {'map': 'cp_iwz', 'meshes': [{'name': 'shell', 'material': 'w/concrete_tiles_01', 'tris': tris + walls},
                                        {'name': 'steps', 'material': 'w/rubber_non_skid_stair_01', 'tris': steps, 'stair': 'flight_a' if marked else None}],
            'zones': [{'name': 'a', 'box': F(-100, 0, -16, 700, 400, 300)}], 'starts': [{'at': F(0, 150, 0), 'yaw': 0}]}


@unittest.skipUnless(HAVE_NUMPY, 'numpy')
class Stairs(unittest.TestCase):
    def test_ramp_goes_from_the_floor_before_the_first_riser_to_the_top_tread(self):
        recs, rows = C.stair_ramps(stair_scene(True)['meshes'])
        r = rows[0]
        self.assertEqual((r['axis'], r['steps'], r['triangles']), ('x', 17, 2))
        # the nosing line runs (43, 0) -> (332, 136); the sheet is that line lifted by 2 (8.5 along the run at slope 136/289)
        self.assertEqual((r['ramp_from'][0], r['ramp_from'][2], r['ramp_to'][0], r['ramp_to'][2]), (38.75, 0.0, 327.75, 136.0))
        # every tread's front top edge (nosing) lies under the sheet, never on it
        a, b = r['ramp_from'], r['ramp_to']
        k = (b[2] - a[2]) / (b[0] - a[0])
        for i in range(17):
            x, z = 60 + 17 * i, 8 * (i + 1)
            self.assertGreaterEqual(a[2] + k * (x - a[0]) - z, 1.9)
        self.assertAlmostEqual(r['slope_deg'], 25.2, 1)
        self.assertEqual((recs[0]['mode'], recs[0]['tag']), ('collision', None))
        for t in recs[0]['tris']:
            self.assertGreater(C.tri_normal(*t)[0][2], 0.5)

    def test_a_riser_over_18_is_reported_and_8_unit_risers_are_not(self):
        sc = stair_scene(False)
        self.assertEqual([m for s, m in C.validate(sc) if 'step over 18' in m], [])
        tall = C.box_tris((60, 100, 0), (77, 212, 8)) + C.box_tris((77, 100, 0), (94, 212, 30)) + C.box_tris((94, 100, 0), (332, 212, 36))
        sc['meshes'][1] = {'name': 'steps', 'material': 'w/rubber_non_skid_stair_01', 'tris': tall, 'stair': None}
        self.assertTrue(any('step over 18' in m for s, m in C.validate(sc)))

    def test_open_side_gets_a_clip_wall_and_a_wall_side_gets_none(self):
        sc = stair_scene(True)
        # remove the wall along y 92..100 (the stair's low side): that side is then open
        keep = []
        for t in sc['meshes'][0]['tris']:
            ys = [p[1] for p in t]
            xs = [p[0] for p in t]
            if min(ys) >= 92 - 1e-6 and max(ys) <= 100 + 1e-6 and min(xs) >= 40 - 1e-6 and max(xs) <= 332 + 1e-6:
                continue
            keep.append(t)
        sc['meshes'][0]['tris'] = keep
        recs, rows = C.stair_ramps(sc['meshes'])
        sides = {w['side']: w for w in rows[0]['side_walls']}
        self.assertEqual(sides['y-']['triangles'], 12)
        self.assertEqual(sides['y+']['triangles'], 0)
        self.assertGreater(sides['y+']['against_wall'], 0.9)
        self.assertEqual(len([r for r in recs if r['name'].startswith('stairclip_')]), 1)
        for r in recs:
            for t in r['tris']:
                self.assertGreater(C.tri_normal(*t)[1], 0)

    def test_foot_clearance_is_measured(self):
        _recs, rows = C.stair_ramps(stair_scene(True)['meshes'])
        self.assertGreaterEqual(rows[0]['foot_clear_depth'], 48)
        sc = stair_scene(True)
        sc['meshes'][0]['tris'] += C.box_tris((20, 90, 0), (30, 220, 100))       # a wall 13 units in front of the foot (43)
        _recs, rows = C.stair_ramps(sc['meshes'])
        self.assertLess(rows[0]['foot_clear_depth'], 48)
        self.assertTrue(any('clear approach' in m for s, m in C.validate(sc) if s == 'WARN'))


@unittest.skipUnless(HAVE_NUMPY and HAVE_TEMPLATE, 'numpy and the stock template dump')
class EndToEnd(unittest.TestCase):
    def test_emit_folder_has_every_file_the_compiler_reads(self):
        with tempfile.TemporaryDirectory() as d:
            rep = C.export_scene(room_scene(), d, log=lambda m: None)
            for f in ('world.bin', 'colmap.hkx', 'navgraph.bin', 'ents.txt', 'triggers.txt', 'scriptables.txt', 'lighting.txt', 'probes.txt',
                      'layout.json', 'plan.json', 'cp_iwz.gsc', 'custom_materials.json', 'scene_report.json'):
                self.assertTrue(os.path.isfile(os.path.join(d, f)), f)
            self.assertEqual(rep['problems'], [])
            self.assertFalse(os.path.isdir(os.path.join(d, 'modules')) and os.listdir(os.path.join(d, 'modules')), 'a generic map starts no Station Zero module')
            gsc = open(os.path.join(d, 'cp_iwz.gsc')).read()
            self.assertIn('iwz_door( "d1"', gsc)
            self.assertNotIn('//@DOORS@', gsc)
            ents = open(os.path.join(d, 'ents.txt'), encoding='latin-1').read()
            self.assertIn('debris_750', ents)
            self.assertIn('perk_machine_revive', ents)

    def test_refused_scene_writes_nothing_useful(self):
        sc = room_scene()
        sc['doors'][0]['cost'] = 1
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                C.export_scene(sc, d, log=lambda m: None)


if __name__ == '__main__':
    unittest.main()
