"""Tests of navfmt.py (graph reader/writer) and navgen.py (navmesh from collision triangles) on synthetic geometry:
no machine paths, no game data. Stock-file round trips run only when IWZ_STOCK_NAVMESH points at a navmesh file."""
import collections
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'fixtures', 'twostorey'))
try:
    import numpy as np
    import navgen
    import twostorey
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
    def test_flat_floor_matches_mapgen_header_and_areas(self):
        data, rep = navgen.generate(np.array(flat_floor()))
        ref, _n = mapgen.nav_graph({(i, j): 0.0 for i in range(16) for j in range(16)}, 32)
        self.assertEqual(rep['areas'], 256)
        a, b = read_bytes(data), read_bytes(ref)
        end = navfmt.HS + sum(x.size for x in b.areas)
        self.assertEqual(navfmt.write_graph(a)[:end], navfmt.write_graph(b)[:end])

    def test_kd_tree_covers_every_area_once(self):
        data, _rep = navgen.generate(np.array(flat_floor(8)))
        gr = read_bytes(data)
        axes, leaves, _d = navfmt.kd_walk(gr)
        self.assertEqual(sorted(leaves), sorted(a.off for a in gr.areas))

    def test_wall_cuts_links(self):
        tris = flat_floor(8)
        wall = [((128, 0, 0), (128, 256, 0), (128, 256, 200)), ((128, 0, 0), (128, 256, 200), (128, 0, 200))]
        data, rep = navgen.generate(np.array(tris + wall), seeds=[(40, 40, 0)])
        self.assertEqual(rep['components'], 2)
        self.assertGreater(rep['dropped_unreachable'], 0)     # the far side is not connected to the seed

    def test_low_ceiling_is_not_walkable(self):
        tris = flat_floor(8)
        roof = [((0, 0, 40), (0, 256, 40), (256, 256, 40)), ((0, 0, 40), (256, 256, 40), (256, 0, 40))]   # faces down
        with self.assertRaises(ValueError):
            navgen.generate(np.array(tris + roof))

    def test_seed_off_navigation_is_reported(self):
        data, rep = navgen.generate(np.array(flat_floor(8)), seeds=[(100, 100, 0), (5000, 5000, 0)])
        self.assertEqual(len(rep['seed_problems']), 1)
        with self.assertRaises(ValueError):
            navgen.generate(np.array(flat_floor(8)), seeds=[(5000, 5000, 0)])


@unittest.skipIf(np is None, 'numpy missing')
class TwoStoreyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.rep = navgen.generate(np.array(twostorey.triangles()), seeds=[twostorey.START])
        cls.gr = read_bytes(cls.data)

    def test_both_floors_and_the_stair(self):
        zs = collections.Counter(round(a.centre[2]) for a in self.gr.areas)
        self.assertGreater(zs[0], 800)
        self.assertGreater(zs[256], 800)
        stair = [z for z in zs if 8 <= z <= 248]
        self.assertGreaterEqual(len(stair), 14)       # a stair level every 16 units
        self.assertGreater(self.rep['stacked_cells'], 800)      # the upper floor lies over the lower one
        self.assertEqual(self.rep['dropped_unreachable'], 0)
        self.assertEqual(self.rep['seed_problems'], [])

    def test_top_floor_is_reachable_from_the_bottom_seed_over_directed_links(self):
        gr = self.gr
        idx = {a.off: i for i, a in enumerate(gr.areas)}
        start = min((i for i, a in enumerate(gr.areas) if abs(a.centre[2]) < 1), key=lambda i: (
            abs(gr.areas[i].centre[0] - twostorey.START[0]) + abs(gr.areas[i].centre[1] - twostorey.START[1])))
        seen = {start}
        st = [start]
        while st:
            for e in gr.areas[st.pop()].edges:
                if e.cost and e.nbr in idx and idx[e.nbr] not in seen:
                    seen.add(idx[e.nbr])
                    st.append(idx[e.nbr])
        top = [i for i, a in enumerate(gr.areas) if abs(a.centre[2] - 256) < 1]
        self.assertEqual(len([i for i in top if i in seen]), len(top))
        # and back down
        self.assertEqual(len(seen), len(gr.areas))

    def test_linked_areas_share_their_edge_heights(self):
        by = self.gr.by_off()
        for a in self.gr.areas[:: max(1, len(self.gr.areas) // 400)]:
            P = [e.corner for e in a.edges]
            for i, e in enumerate(a.edges):
                if not e.cost:
                    continue
                b = by[e.nbr]
                Q = [f.corner for f in b.edges]
                j = next(j for j, f in enumerate(b.edges) if f.nbr == a.off)
                self.assertAlmostEqual(P[i][2], Q[(j + 1) % 4][2], places=3)
                self.assertAlmostEqual(P[(i + 1) % 4][2], Q[j][2], places=3)

    def test_stair_rises_without_a_step_over_eighteen(self):
        by = self.gr.by_off()
        worst = 0.0
        for a in self.gr.areas:
            for e in a.edges:
                if e.cost:
                    worst = max(worst, abs(by[e.nbr].centre[2] - a.centre[2]))
        self.assertLessEqual(worst, 18.0)


if __name__ == '__main__':
    unittest.main()
