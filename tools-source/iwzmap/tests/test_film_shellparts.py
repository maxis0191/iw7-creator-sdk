"""station_zero/film/shellparts.py (AC1): the authoring library of the Arcade's architecture. Convex solids come out closed and facing outward (by their own centroid), the stock
column's numbers (K1-CONSTRUCTION 2.4) are in the parts, a strip is its profile along a segment, a wall face leaves its openings out."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'station_zero', 'film'))
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))

try:
    import shellparts as P
except ImportError:                                   # no Studio on this machine: the library imports its build module
    P = None


def volume6(tris):
    """six times the signed volume (positive when the triangles face outward)"""
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return v


@unittest.skipIf(P is None, 'Studio is not on this machine')
class Parts(unittest.TestCase):
    def test_bevel_box_is_closed_and_outward(self):
        t = P.bevel_box(0, 0, 0, 10, 20, 5, c=1.0, top=1.0)
        self.assertGreater(volume6(t), 0.0)
        self.assertAlmostEqual(volume6(t) / 6.0, 10 * 20 * 5, delta=10 * 20 * 5 * 0.06)       # a bevelled 10 x 20 x 5 loses a few percent at its edges
        xs = [p[0] for tri in t for p in tri]
        self.assertAlmostEqual(min(xs), 0.0, places=2)
        self.assertAlmostEqual(max(xs), 10.0, places=2)

    def test_plain_box_volume(self):
        t = P.box(0, 0, 0, 4, 6, 8)
        self.assertAlmostEqual(volume6(t) / 6.0, 4 * 6 * 8, places=3)
        self.assertEqual(len(t), 12)
        self.assertEqual(len(P.box(0, 0, 0, 4, 6, 8, skip=('z0',))), 10)

    def test_column_is_the_stock_column(self):
        parts = P.column_parts(100.0, 200.0)
        zs = {role: (min(p[2] for t in tris for p in t), max(p[2] for t in tris for p in t)) for role, tris in parts.items()}
        self.assertEqual(zs['base'], (0.0, 12.0))                                   # base 12 high
        self.assertEqual(zs['band'], (80.0, 91.0))                                  # blue band 11 high
        self.assertEqual(zs['collar'][0], 127.0)                                    # black collar from +127
        self.assertGreaterEqual(zs['collar'][1] - zs['collar'][0], 24.0)           # 24 high
        xs = [p[0] for t in parts['shaft'] for p in t]
        self.assertAlmostEqual(max(xs) - min(xs), 32.0, places=2)                   # shaft 32 x 32
        xs = [p[0] for t in parts['base'] for p in t]
        self.assertAlmostEqual(max(xs) - min(xs), 34.0, places=2)                   # base 34 x 34
        for role in ('shaft', 'band', 'upper', 'collar', 'cap'):
            self.assertEqual(len(parts[role]) % 8, 0, role)                         # octagonal sections (3-unit chamfers)

    def test_ibeam_underside_and_top(self):
        p = P.ibeam((0, 0), (254, 0), 161.0, 240.0)
        zs = [q[2] for t in p['flange'] + p['web'] for q in t]
        self.assertEqual((min(zs), max(zs)), (161.0, 240.0))

    def test_strip_follows_its_segment(self):
        t = P.strip((0, 0), (100, 0), [(0.0, 0.0), (2.0, 0.0), (2.0, 3.0), (0.0, 3.0)])
        ys = [p[1] for tri in t for p in tri]
        self.assertAlmostEqual(min(ys), 0.0, places=3)
        self.assertAlmostEqual(max(ys), 2.0, places=3)                              # d is the left normal of +x: +y
        self.assertAlmostEqual(volume6(t) / 6.0, 100 * 2 * 3, places=2)

    def test_wall_face_leaves_openings_out(self):
        full = P.wall_face('x', 0.0, 0.0, 100.0, 0.0, 50.0, +1)
        cut = P.wall_face('x', 0.0, 0.0, 100.0, 0.0, 50.0, +1, openings=[(40.0, 60.0, 0.0, 30.0)])
        area = lambda tris: sum(abs((b[0] - a[0]) * (c[2] - a[2]) - (c[0] - a[0]) * (b[2] - a[2])) / 2.0 for a, b, c in tris)
        self.assertAlmostEqual(area(full), 100 * 50, places=2)
        self.assertAlmostEqual(area(cut), 100 * 50 - 20 * 30, places=2)

    def test_wall_face_faces_the_room(self):
        up = P.wall_face('x', 0.0, 0.0, 10.0, 0.0, 10.0, +1)[0]
        ny = (up[1][2] - up[0][2]) * (up[2][0] - up[0][0]) - (up[1][0] - up[0][0]) * (up[2][2] - up[0][2])
        self.assertGreater(ny, 0.0)                                                 # +y normal


if __name__ == '__main__':
    unittest.main()
