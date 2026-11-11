"""Offline map gate: synthetic geometry with known defects."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import iwz_emitcheck as ec  # noqa: E402


def quad(x0, y0, x1, y1, z):
    """Two triangles wound counter-clockwise seen from above (a floor)."""
    a, b, c, d = (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)
    return [(a, b, c), (a, c, d)]


def cell(x0, y0, z, nbrs=(0, 0, 0, 0)):
    return {'c': (x0 + 16.0, y0 + 16.0, z),
            'corners': [(x0, y0, z), (x0 + 32.0, y0, z), (x0 + 32.0, y0 + 32.0, z), (x0, y0 + 32.0, z)],
            'nbrs': list(nbrs)}


def slab(extra_tris=(), areas=None, layout=None):
    tris = quad(0.0, 0.0, 128.0, 128.0, 0.0) + list(extra_tris)
    if areas is None:
        areas = {100: cell(32.0, 32.0, 0.0)}
    return ec.Emit(tris, areas, layout or {}, 'synthetic')


class DegenerateTests(unittest.TestCase):
    def test_a_triangle_with_two_equal_corners_is_an_error(self):
        emit = slab([((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0))])
        f = ec.check_degenerate(emit)
        self.assertEqual([(x['code'], x['severity'], x['count']) for x in f], [('DEGENERATE_COLLISION', 'error', 1)])
        self.assertEqual(ec.check_degenerate(slab()), [])


class CollisionTests(unittest.TestCase):
    def test_floor_is_found_where_it_exists(self):
        emit = slab()
        self.assertEqual([round(f[0]) for f in emit.col.floors(16.0, 16.0)], [0])
        self.assertEqual(emit.col.floors(500.0, 500.0), [])

    def test_explain_tells_floor_air_solid_and_void_apart(self):
        emit = slab()
        self.assertEqual(ec.explain(emit, 40.0, 40.0, 0.0)['verdict'], 'on_floor')
        self.assertEqual(ec.explain(emit, 40.0, 40.0, 30.0)['verdict'], 'in_air')
        self.assertEqual(ec.explain(emit, 40.0, 40.0, -30.0)['verdict'], 'inside_solid')
        self.assertEqual(ec.explain(emit, 500.0, 500.0, 0.0)['verdict'], 'no_floor')

    def test_explain_reports_distance_to_nav(self):
        emit = slab()
        self.assertEqual(ec.explain(emit, 48.0, 48.0, -30.0)['nav_offset'], -30.0)


class NavSupportTests(unittest.TestCase):
    def codes(self, emit):
        return sorted(f['code'] for f in ec.check_nav_support(emit))

    def test_supported_cell_is_clean(self):
        self.assertEqual(self.codes(slab()), [])

    def test_floating_buried_and_unsupported_cells_are_errors(self):
        self.assertEqual(self.codes(slab(areas={1: cell(32.0, 32.0, 60.0)})), ['NAV_FLOATING'])
        self.assertEqual(self.codes(slab(areas={1: cell(32.0, 32.0, -60.0)})), ['NAV_BURIED'])
        self.assertEqual(self.codes(slab(areas={1: cell(480.0, 480.0, 0.0)})), ['NAV_NO_FLOOR'])

    def test_findings_are_errors_with_a_place(self):
        f = ec.check_nav_support(slab(areas={1: cell(32.0, 32.0, 60.0)}))[0]
        self.assertEqual(f['severity'], 'error')
        self.assertEqual(f['count'], 1)
        self.assertEqual(len(f['bbox']), 6)


class RouteTests(unittest.TestCase):
    def test_route_follows_links_and_refuses_islands(self):
        areas = {1: cell(0.0, 0.0, 0.0, (2, 0, 0, 0)),
                 2: cell(32.0, 0.0, 0.0, (1, 3, 0, 0)),
                 3: cell(64.0, 0.0, 0.0, (2, 0, 0, 0)),
                 9: cell(96.0, 96.0, 0.0)}
        emit = slab(areas=areas)
        length, path = emit.nav.route(1, 3)
        self.assertEqual(path[0], 1)
        self.assertEqual(path[-1], 3)
        self.assertAlmostEqual(length, 64.0, delta=1.0)
        self.assertEqual(emit.nav.route(1, 9), (None, []))
        self.assertEqual(len(set(emit.nav.components().values())), 2)

    def test_point_lookup_projects_down_for_ceiling_spawners(self):
        emit = slab()
        self.assertEqual(emit.nav.at(48.0, 48.0, 2.0), 100)
        self.assertIsNone(emit.nav.at(48.0, 48.0, 120.0))
        self.assertEqual(emit.nav.below(48.0, 48.0, 120.0), 100)


class DiffTests(unittest.TestCase):
    def test_identical_emits_have_nothing_to_retest(self):
        d = ec.diff_emits(slab(), slab())
        self.assertEqual(d['collision_tris_changed'], 0)
        self.assertEqual(d['nav_cells_changed'], 0)
        self.assertEqual(d['retest'], [])

    def test_changed_geometry_is_counted(self):
        d = ec.diff_emits(slab(), slab(extra_tris=quad(0.0, 0.0, 32.0, 32.0, 64.0)))
        self.assertEqual(d['collision_tris_changed'], 2)
        self.assertEqual(d['nav_cells_changed'], 0)


class CliTests(unittest.TestCase):
    def test_points_parse(self):
        self.assertEqual(list(ec.parse_point('1,2,-3')), [1.0, 2.0, -3.0])

    def test_partial_emit_is_refused_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ec.NotAnEmit):
                ec.Emit.load(tmp)


if __name__ == '__main__':
    unittest.main()
