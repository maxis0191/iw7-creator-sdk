"""Tests of navfmt.py (graph reader/writer) and navgen.py (navmesh from collision triangles) on synthetic geometry:
no machine paths, no game data. Stock-file round trips run only when IWZ_STOCK_NAVMESH points at a navmesh file."""
import collections
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'fixtures', 'twostorey'))
sys.path.insert(0, os.path.join(HERE, 'fixtures', 'freeform'))
try:
    import numpy as np
    import navgen
    import twostorey
    import freeform
except ImportError:          # numpy is not installed for this interpreter
    np = None
import navfmt  # noqa: E402
import mapgen  # noqa: E402


def read_bytes(data):
    gs = navfmt.find_graph(data)
    gr, n = navfmt.parse_graph(data[gs:])
    gr.prefix, gr.suffix = data[:gs], data[gs + n:]
    return gr


def flat_floor(n=16, z=0.0):
    s = n * 32.0
    a, b, c, d = (0, 0, z), (s, 0, z), (s, s, z), (0, s, z)
    return [(a, b, c), (a, c, d)]


def shared_edge_problems(gr):
    """Every link must be one exactly shared edge (the neighbour holds the same corners reversed, same heights) and
    every area convex. Returns (bad links, non-convex areas)."""
    by = gr.by_off()
    bad = 0
    nonconvex = 0
    for a in gr.areas:
        P = [e.corner for e in a.edges]
        n = len(P)
        for k in range(n):
            p, q, r = P[k], P[(k + 1) % n], P[(k + 2) % n]
            if (q[0] - p[0]) * (r[1] - q[1]) - (q[1] - p[1]) * (r[0] - q[0]) < -1e-2:
                nonconvex += 1
                break
        for i, e in enumerate(a.edges):
            if not e.cost:
                continue
            b = by[e.nbr]
            Q = [f.corner for f in b.edges]
            m = len(Q)
            if not any(f.nbr == a.off and all(abs(P[i][c] - Q[(j + 1) % m][c]) < 1e-3 and
                                              abs(P[(i + 1) % n][c] - Q[j][c]) < 1e-3 for c in range(3))
                       for j, f in enumerate(b.edges)):
                bad += 1
    return bad, nonconvex


def flood(gr, start):
    idx = {a.off: i for i, a in enumerate(gr.areas)}
    seen = {start}
    st = [start]
    while st:
        for e in gr.areas[st.pop()].edges:
            if e.cost and e.nbr in idx and idx[e.nbr] not in seen:
                seen.add(idx[e.nbr])
                st.append(idx[e.nbr])
    return seen


def side_slope_links(gr):
    """Links between areas whose slopes differ by more than 10 degrees where the shared edge is within 60 degrees of
    parallel to the gradient of the steeper one (a ramp entered from the side)."""
    by = gr.by_off()
    n = 0
    for a in gr.areas:
        P = [e.corner for e in a.edges]
        for i, e in enumerate(a.edges):
            if not e.cost:
                continue
            ga = navgen._plane(P)[:2]
            Q = [f.corner for f in by[e.nbr].edges]
            gb = navgen._plane(Q)[:2]
            sa, sb = math.hypot(*ga), math.hypot(*gb)
            if sa > 1.73 or sb > 1.73 or abs(math.degrees(math.atan(sa) - math.atan(sb))) <= 10.0:
                continue
            g = ga if sa >= sb else gb
            ex, ey = P[(i + 1) % len(P)][0] - P[i][0], P[(i + 1) % len(P)][1] - P[i][1]
            if abs(ex * g[0] + ey * g[1]) / (math.hypot(ex, ey) * math.hypot(*g)) > 0.5:
                n += 1
    return n


@unittest.skipIf(np is None, 'numpy missing')
class RampSideTests(unittest.TestCase):
    def test_a_ramp_is_entered_by_its_foot_not_from_the_side(self):
        # flat floor x < 256, a ramp x 256..512 rising to z 128 along x, and a flat strip beside the ramp (y > 256)
        def quad(p0, p1, p2, p3):
            return [(p0, p1, p2), (p0, p2, p3)]
        tris = quad((0, 0, 0), (256, 0, 0), (256, 256, 0), (0, 256, 0))
        tris += quad((256, 0, 0), (512, 0, 128), (512, 256, 128), (256, 256, 0))
        tris += quad((256, 256, 0), (512, 256, 0), (512, 512, 0), (256, 512, 0))
        tris += quad((0, 256, 0), (256, 256, 0), (256, 512, 0), (0, 512, 0))
        data, rep = navgen.generate(np.array(tris), seeds=[(100, 100, 0)])
        gr = read_bytes(data)
        self.assertGreater(rep['slope_side_links_cut'], 0)
        self.assertEqual(side_slope_links(gr), 0)
        self.assertEqual(shared_edge_problems(gr), (0, 0))
        # the top of the ramp is still reachable from the floor, over the foot edge
        start = min(range(len(gr.areas)), key=lambda i: math.dist(gr.areas[i].centre, (100, 100, 0)))
        seen = flood(gr, start)
        self.assertTrue(any(gr.areas[i].centre[2] > 100 for i in seen))


@unittest.skipIf(np is None, 'numpy missing')
class FormatTests(unittest.TestCase):
    def test_mapgen_graph_round_trips_byte_identical(self):
        data, _n = mapgen.nav_graph({(i, j): 0.0 for i in range(6) for j in range(5)}, 32)
        gr = read_bytes(data)
        self.assertEqual(len(gr.areas), 30)
        self.assertEqual(navfmt.write_file(gr), data)

    def test_n_gon_areas_round_trip(self):
        data, _n = mapgen.nav_graph({(i, j): 0.0 for i in range(3) for j in range(3)}, 32)
        gr = read_bytes(data)
        a = gr.areas[0]
        a.edges.append(navfmt.Edge(0, (1.0, 2.0, 3.0)))
        a.flags = a.flags & ~0x7F | 5
        navfmt.relayout(gr)
        again = navfmt.parse_graph(navfmt.write_graph(gr))[0]
        self.assertEqual([len(x.edges) for x in again.areas], [5] + [4] * 8)

    def test_stock_file_when_given(self):
        p = os.environ.get('IWZ_STOCK_NAVMESH')
        if not p or not os.path.isfile(p):
            self.skipTest('IWZ_STOCK_NAVMESH not set')
        self.assertEqual(navfmt.write_file(navfmt.read_file(p)), open(p, 'rb').read())


@unittest.skipIf(np is None, 'numpy missing')
class GenerateTests(unittest.TestCase):
    def test_flat_floor_is_a_few_big_polygons(self):
        data, rep = navgen.generate(np.array(flat_floor(16)))
        gr = read_bytes(data)
        self.assertLess(rep["areas"], 120)             # 1,024 lattice cells before the merge
        self.assertEqual(shared_edge_problems(gr), (0, 0))
        self.assertEqual({round(e.corner[2], 3) for a in gr.areas for e in a.edges}, {0.0})
        xs = [e.corner[0] for a in gr.areas for e in a.edges]
        self.assertAlmostEqual(min(xs), 8.0, delta=6.0)          # the edge stays the margin (8) off the border

    def test_kd_tree_covers_every_area_once(self):
        data, _rep = navgen.generate(np.array(flat_floor(8)))
        gr = read_bytes(data)
        _axes, leaves, _d = navfmt.kd_walk(gr)
        self.assertEqual(sorted(leaves), sorted(a.off for a in gr.areas))

    def test_wall_cuts_links_and_seeds_drop_the_far_side(self):
        tris = flat_floor(8)
        wall = [((128, 0, 0), (128, 256, 0), (128, 256, 200)), ((128, 0, 0), (128, 256, 200), (128, 0, 200))]
        data, rep = navgen.generate(np.array(tris + wall), seeds=[(40, 40, 0)])
        self.assertGreater(rep['dropped_unreachable'], 0)
        gr = read_bytes(data)
        self.assertTrue(all(e.corner[0] < 128 for a in gr.areas for e in a.edges))

    def test_low_ceiling_is_not_walkable(self):
        tris = flat_floor(8)
        roof = [((0, 0, 40), (0, 256, 40), (256, 256, 40)), ((0, 0, 40), (256, 256, 40), (256, 0, 40))]   # faces down
        with self.assertRaises(ValueError):
            navgen.generate(np.array(tris + roof))

    def test_seed_off_navigation_is_reported(self):
        _data, rep = navgen.generate(np.array(flat_floor(8)), seeds=[(100, 100, 0), (5000, 5000, 0)])
        self.assertEqual(len(rep['seed_problems']), 1)
        with self.assertRaises(ValueError):
            navgen.generate(np.array(flat_floor(8)), seeds=[(5000, 5000, 0)])


@unittest.skipIf(np is None, 'numpy missing')
class TwoStoreyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tris = np.array(twostorey.triangles())
        cls.data, cls.rep = navgen.generate(cls.tris, seeds=[twostorey.START])
        cls.gr = read_bytes(cls.data)

    def test_both_floors_and_the_stair(self):
        zs = collections.Counter(round(a.centre[2]) for a in self.gr.areas)
        self.assertGreater(zs[0], 100)
        self.assertGreater(zs[256], 100)
        self.assertGreaterEqual(len([z for z in zs if 8 <= z <= 248]), 3)
        self.assertGreater(navfmt.stats(self.gr)['stacked_areas'], 100)       # the upper floor lies over the lower one
        self.assertLessEqual(self.rep['dropped_unreachable'], 2)      # slivers beside the stair that lost their side link
        self.assertEqual(self.rep['seed_problems'], [])
        self.assertLess(len(self.gr.areas), 700)

    def test_top_floor_is_reachable_from_the_bottom_seed_over_directed_links(self):
        gr = self.gr
        start = min((i for i, a in enumerate(gr.areas) if abs(a.centre[2]) < 1),
                    key=lambda i: abs(gr.areas[i].centre[0] - twostorey.START[0]) +
                    abs(gr.areas[i].centre[1] - twostorey.START[1]))
        seen = flood(gr, start)
        top = [i for i, a in enumerate(gr.areas) if abs(a.centre[2] - 256) < 1]
        self.assertEqual(len([i for i in top if i in seen]), len(top))
        self.assertEqual(len(seen), len(gr.areas))

    def test_every_link_is_one_exactly_shared_edge_and_areas_are_convex(self):
        self.assertEqual(shared_edge_problems(self.gr), (0, 0))

    def test_edge_counts_stay_in_the_stock_range(self):
        self.assertTrue(all(3 <= len(a.edges) <= 14 for a in self.gr.areas))

    def test_edge_stays_near_the_wall(self):
        g = navgen.boundary_gap(self.tris, self.data)
        self.assertLessEqual(g['mean'], 12.0)
        self.assertLessEqual(g['p95'], 15.0)


@unittest.skipIf(np is None, 'numpy missing')
class FreeformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tris = np.array(freeform.triangles())
        seeds = [freeform.rot(freeform.START_LOWER), freeform.rot(freeform.SEED_TOP), freeform.SEED_ROOM]
        cls.data, cls.rep = navgen.generate(cls.tris, seeds=seeds)
        cls.gr = read_bytes(cls.data)

    def test_rotated_levels_are_connected_bottom_to_top(self):
        gr = self.gr
        sx, sy, _ = freeform.rot(freeform.START_LOWER)
        start = min((i for i, a in enumerate(gr.areas) if abs(a.centre[2]) < 1),
                    key=lambda i: abs(gr.areas[i].centre[0] - sx) + abs(gr.areas[i].centre[1] - sy))
        seen = flood(gr, start)
        top = [i for i, a in enumerate(gr.areas) if abs(a.centre[2] - 256) < 1 and a.centre[0] < 1300]
        self.assertGreater(len(top), 50)
        self.assertEqual(len([i for i in top if i in seen]), len(top))
        self.assertEqual(self.rep['seed_problems'], [])

    def test_links_exact_and_convex(self):
        self.assertEqual(shared_edge_problems(self.gr), (0, 0))

    def test_no_area_overhangs_the_pillar_or_the_diagonal_wall(self):
        px, py, pr = freeform.PILLAR
        x0, y0, _x1, _y1 = freeform.ROOM
        a0, a1 = (x0 + 120, y0), (x0 + 420, y0 + 300)
        for a in self.gr.areas:
            if not (1400 <= a.centre[0] <= 1900 and a.centre[2] < 5):
                continue
            for e in a.edges:
                x, y, _z = e.corner
                self.assertGreaterEqual(math.hypot(x - px, y - py), pr - 1.0)
                dx, dy = a1[0] - a0[0], a1[1] - a0[1]
                t = max(0.0, min(1.0, ((x - a0[0]) * dx + (y - a0[1]) * dy) / (dx * dx + dy * dy)))
                self.assertGreaterEqual(math.hypot(x - a0[0] - t * dx, y - a0[1] - t * dy), 8.0 - 1.0)

    def test_edge_stays_near_the_wall(self):
        g = navgen.boundary_gap(self.tris, self.data)
        self.assertLessEqual(g['mean'], 12.0)
        self.assertLessEqual(g['p95'], 15.0)

    def test_closed_solid_interior_is_not_walkable(self):
        _data, rep = navgen.generate(self.tris)
        self.assertGreater(rep['inside_solid'], 0)


if __name__ == '__main__':
    unittest.main()
