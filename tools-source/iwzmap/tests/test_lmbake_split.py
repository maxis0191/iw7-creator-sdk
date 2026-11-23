"""R7 baker bug: a vertex shared by two lightmap charts kept only the last chart's lightmap coordinate (stretched, striped lighting
on walls: 542 of 15,882 triangles of the Arcade). split_shared_vertices gives every chart its own copy.
Run with the bake environment's python: python -B tests/test_lmbake_split.py   (a check without numba skips)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy as np
    import synth_world as SW
    import lmbake
    import lm_stretch
except ImportError as e:
    raise unittest.SkipTest('bake environment missing: %s' % e)

ARCADE = os.environ.get('IWZ_ARCADE_EMIT', 'C:/studio-data/rooms/maps/arcade_emit5')


def two_charts_one_vertex():
    """one surface, 5 vertices, triangles (0,1,2) and (0,3,4): vertex 0 is shared; the reversed twin of the first is (0,2,1)"""
    w = SW.make_world([SW.floor_quad(0, 0, 0, 64, 64)], ['m'])
    v = np.zeros(5, lmbake.VD)
    P = [(0, 0, 0), (64, 0, 0), (0, 64, 0), (0, -64, 0), (-64, 0, 0)]
    for i, p in enumerate(P):
        v['pos'][i] = p; v['n'][i] = SW.pack_unit((0, 0, 1)); v['t'][i] = SW.pack_unit((1, 0, 0))
    w['verts'] = v
    w['indices'] = np.array([0, 1, 2, 0, 3, 4, 0, 2, 1], '<u2')
    w['surfaces']['vc'] = 5; w['surfaces']['tc'] = 3
    def chart(tris, vs, s0, r0):
        e = np.array
        return {'surface': 0, 'tris': tris, 'verts': vs, 'n': e([0, 0, 1.]), 't': e([1., 0, 0]), 'b': e([0, 1., 0]), 'd': 0.0,
                'sn': e([0, 0, 1.]), 'st': e([1., 0, 0]), 'sb': e([0, 1., 0]), 's0': s0, 'r0': r0, 'ns': 8, 'nr': 8, 'ts': 8.0, 'tr': 8.0, 'mat': 0}
    charts = [chart([(0, 1, 2)], [0, 1, 2], 0, 0), chart([(0, 3, 4)], [0, 3, 4], -64, -64)]
    return w, charts


class Split(unittest.TestCase):
    def test_shared_vertex_is_copied_once(self):
        w, charts = two_charts_one_vertex()
        pos0 = w['verts']['pos'].copy()
        r = lmbake.split_shared_vertices(w, charts)
        self.assertEqual(r['added'], 1)
        self.assertEqual(len(w['verts']), 6)
        a, b = set(charts[0]['verts']), set(charts[1]['verts'])
        self.assertFalse(a & b, 'the charts still share a vertex')
        self.assertEqual(sorted(a | b), [0, 1, 2, 3, 4, 5])
        # the geometry is unchanged: every triangle keeps its corner positions
        pos = w['verts']['pos']
        self.assertTrue(np.allclose(pos[list(charts[0]['tris'][0])], pos0[[0, 1, 2]]))
        self.assertTrue(np.allclose(pos[list(charts[1]['tris'][0])], pos0[[0, 3, 4]]))
        # the index buffer follows the charts; the reversed twin (0,2,1) follows the chart of its twin (0,1,2)
        idx = w['indices'].astype(int) + int(w['surfaces']['first'][0])
        self.assertEqual(sorted(idx[0:3]), sorted(charts[0]['tris'][0]))
        self.assertEqual(sorted(idx[3:6]), sorted(charts[1]['tris'][0]))
        self.assertEqual(sorted(idx[6:9]), sorted(charts[0]['tris'][0]))
        self.assertEqual(int(w['surfaces']['vc'][0]), 6)

    def test_lightmap_coordinates_do_not_collide(self):
        w, charts = two_charts_one_vertex()
        lmbake.split_shared_vertices(w, charts)
        W, H = lmbake.pack(charts)
        lmbake.chart_texels(charts, w, W, H)
        lm = w['verts']['lm']
        v_a, v_b = charts[0]['tris'][0][0], charts[1]['tris'][0][0]    # the two copies of the shared corner
        self.assertNotEqual(v_a, v_b)
        self.assertFalse(np.allclose(lm[v_a], lm[v_b]))

    def test_u16_limit(self):
        w, charts = two_charts_one_vertex()
        w['surfaces']['vc'][0] = 65535
        w['verts'] = np.concatenate([w['verts'], np.zeros(65530, lmbake.VD)])
        with self.assertRaises(SystemExit):
            lmbake.split_shared_vertices(w, charts)


class ArcadeStretch(unittest.TestCase):
    @unittest.skipUnless(os.path.isfile(os.path.join(ARCADE, 'world.bin')), 'Arcade emit not on this machine')
    def test_arcade_has_no_stretched_triangle(self):
        w0, W0, H0, _ = lm_stretch.plan(ARCADE, 8.0, split=False)
        rows0, bad0 = lm_stretch.stretched(w0, W0, H0, 8.0)
        w1, W1, H1, added = lm_stretch.plan(ARCADE, 8.0, split=True)
        rows1, bad1 = lm_stretch.stretched(w1, W1, H1, 8.0)
        print('Arcade: stretched %d -> %d of %d triangles, vertices %d -> %d (+%d), atlas %dx%d -> %dx%d' %
              (len(bad0), len(bad1), len(rows1), len(w0['verts']), len(w1['verts']), added, W0, H0, W1, H1))
        self.assertGreater(len(bad0), 100)
        self.assertEqual(len(bad1), 0)
        self.assertEqual((W0, H0), (W1, H1))             # the atlas does not change: same charts

        def tri_lm(w):
            out = []
            for sf in w['surfaces']:
                t = w['indices'][sf['base']:sf['base'] + sf['tc'] * 3].reshape(-1, 3).astype(int) + sf['first']
                out.append(w['verts']['lm'][t])
            return np.concatenate(out)
        a, b = tri_lm(w0), tri_lm(w1)
        same = np.all(np.abs(a - b) < 1e-6, axis=(1, 2))
        print('Arcade: %d of %d triangles keep their lightmap coordinates exactly, %d change (they read another chart before)' %
              (same.sum(), len(a), (~same).sum()))
        self.assertGreater(same.mean(), 0.88)
        self.assertGreaterEqual((~same).sum(), len(bad0))   # every stretched triangle was among the changed ones


if __name__ == '__main__':
    unittest.main()
