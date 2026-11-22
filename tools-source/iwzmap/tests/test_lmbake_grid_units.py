"""The light grid's two terms are one convention (measured 22 Nov 2026 on the Arcade, where they looked inconsistent: c0 = 3.545 x radiance against 0.886 x e).

lighting.txt c0 = sqrt(4 pi) x (mean over all normals of the irradiance a surface would receive, baker units, in which a lit surface shows albedo x E):
  * indirect: radiance L seen from every direction -> E(n) = L for every n -> c0 = 4 pi Y00 L = 3.545 L          (lmbake.light_grid: rad.mean * 4 pi Y00)
  * delta light of irradiance e (E(n) = e max(0, n.l)) -> mean over the sphere e / 4 -> c0 = 3.545 e / 4 = 0.886 e (lmbake.light_grid: pi e Y00)
so the same room lit by either reads the same c0 per unit mean irradiance. Run with the bake environment's python: python -B tests/test_lmbake_grid_units.py
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bake'))
import lmbake  # noqa: E402


class GridUnits(unittest.TestCase):
    def sphere(self, n=200000):
        rng = np.random.default_rng(1)
        v = rng.normal(size=(n, 3))
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    def test_constants(self):
        self.assertAlmostEqual(lmbake.Y00, 1 / (2 * math.sqrt(math.pi)), 5)
        self.assertAlmostEqual(4 * math.pi * lmbake.Y00, math.sqrt(4 * math.pi), 5)

    def test_delta_light_equals_uniform_of_same_mean_irradiance(self):
        n = self.sphere()
        l = np.array([0.3, -0.2, 0.9]); l /= np.linalg.norm(l)
        e = 2.0
        mean_E = (e * np.maximum(0, n @ l)).mean()                 # mean over normals of the irradiance
        c0_code = math.pi * e * lmbake.Y00                        # the code's direct term
        self.assertAlmostEqual(c0_code, math.sqrt(4 * math.pi) * mean_E, delta=0.01 * c0_code)
        L = mean_E                                                # a uniform environment with the same mean irradiance
        self.assertAlmostEqual(L * 4 * math.pi * lmbake.Y00, c0_code, delta=0.01 * c0_code)   # the code's indirect term gives the same c0


if __name__ == '__main__':
    unittest.main()
