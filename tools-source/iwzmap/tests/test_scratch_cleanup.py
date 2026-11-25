"""iw7image.encode/decode remove the scratch folder they make, also when texconv fails (25 Nov 2026: leaked iwzlm_* folders held 16 GB of %TEMP%).
Run: python -B tests/test_scratch_cleanup.py"""
import glob
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bake'))
try:
    import numpy as np
    import iw7image  # noqa: E402
except ImportError as e:
    raise unittest.SkipTest('bake environment missing: %s' % e)


class ScratchCleanup(unittest.TestCase):
    def _leftovers(self):
        return set(glob.glob(os.path.join(tempfile.gettempdir(), 'iwzlm_*')))

    def test_failure_leaves_nothing(self):
        before = self._leftovers()
        old = iw7image.texconv
        iw7image.texconv = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom'))
        try:
            with self.assertRaises(RuntimeError):
                iw7image.encode(np.zeros((4, 4, 3), np.float32), 'BC6H_UF16')
            with self.assertRaises(RuntimeError):
                iw7image.decode(95, 4, 4, b'\0' * 16)
        finally:
            iw7image.texconv = old
        self.assertEqual(self._leftovers(), before)


if __name__ == '__main__':
    unittest.main()
