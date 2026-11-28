"""Decals, glass and fences are baked (they get lightmap texels) but stop no light; shadow casters that draw nothing (stock caulk_shadow) are baker-only triangles.
Run with the bake environment's python: python -B tests/test_lmbake_decals.py   (a check without numpy skips)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'bake'))
try:
    import numpy as np
    import lmbake
    import layout_lights as LL
except ImportError as e:
    raise unittest.SkipTest('bake environment missing: %s' % e)


def scene():
    """three triangles: material 0 (wall), 1 (decal), 2 (fence)"""
    tri_v = [np.array([[0, 0, 0], [0, 0, 1], [0, 0, 2]], float), np.array([[1, 0, 0], [1, 0, 1], [1, 0, 2]], float), np.array([[0, 1, 0], [0, 1, 1], [0, 1, 2]], float)]
    tri_lm = [np.array([[0.1, 0.1], [0.2, 0.2], [0.3, 0.3]]), np.array([[0.4, 0.4], [0.5, 0.5], [0.6, 0.6]]), np.array([[0.7, 0.7], [0.8, 0.8], [0.9, 0.9]])]
    return tri_v, tri_lm, np.array([0, 1, 2])


class DropNonOccluders(unittest.TestCase):
    def test_nothing_listed_changes_nothing(self):
        v, lm, mat = scene()
        a, b, c, n = lmbake.drop_non_occluders(v, lm, mat, ['wall', 'decal', 'fence'], None)
        self.assertEqual(n, 0)
        self.assertIs(a, v)
        self.assertIs(c, mat)
        self.assertEqual(lmbake.drop_non_occluders(v, lm, mat, ['wall', 'decal', 'fence'], [])[3], 0)
        self.assertEqual(lmbake.drop_non_occluders(v, lm, mat, ['wall', 'decal', 'fence'], ['not_a_material'])[3], 0)

    def test_listed_materials_leave_the_scene_arrays_aligned(self):
        v, lm, mat = scene()
        a, b, c, n = lmbake.drop_non_occluders(v, lm, mat, ['wall', 'decal', 'fence'], ['decal', 'fence'])
        self.assertEqual(n, 2)
        self.assertEqual(list(c), [0])
        self.assertEqual(a[0].shape, (1, 3))
        self.assertTrue(np.allclose(b[0], lm[0][[0]]))
        self.assertTrue(np.allclose(a[1], v[1][[0]]))

    def test_everything_listed(self):
        v, lm, mat = scene()
        a, b, c, n = lmbake.drop_non_occluders(v, lm, mat, ['wall', 'decal', 'fence'], ['wall', 'decal', 'fence'])
        self.assertEqual((n, len(c)), (3, 0))


class ShadowTriangles(unittest.TestCase):
    def test_none_without_triangles(self):
        self.assertIsNone(lmbake.occluder_triangles({}))
        self.assertIsNone(lmbake.occluder_triangles({'occluder_tris': []}))

    def test_corners(self):
        t = lmbake.occluder_triangles({'occluder_tris': [[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[0, 0, 5], [1, 0, 5], [0, 1, 5]]]})
        self.assertEqual([x.shape for x in t], [(2, 3)] * 3)
        self.assertEqual(list(t[1][0]), [1, 0, 0])
        self.assertEqual(list(t[2][1]), [0, 1, 5])


class Inputs(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(LL.draw_class_inputs(d), ([], [], {}))
            open(os.path.join(d, 'draw_classes.txt'), 'w').write('# c\nw/graffiti\t15\nwc/glass\t25\nw/emitter\t38\nw/odd\tx\n')
            json.dump({'triangles': [[[0, 0, 0], [1, 0, 0], [0, 1, 0]]]}, open(os.path.join(d, 'shadow_occluders.json'), 'w'))
            names, tris, rep = LL.draw_class_inputs(d)
            self.assertEqual(names, ['w/graffiti', 'wc/glass'])           # decal and trans bands only: emissive (38) stays an occluder
            self.assertEqual(len(tris), 1)
            self.assertEqual(rep, {'non_occluding_materials': 2, 'shadow_occluder_triangles': 1})


if __name__ == '__main__':
    unittest.main()
