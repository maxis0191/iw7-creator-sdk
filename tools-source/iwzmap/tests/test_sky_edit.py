"""sky_edit.py: the sun lights of a commap and the sky image name of a gfxmap stream (synthetic, no game)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import sky_edit as S  # noqa: E402


class SkyEditTest(unittest.TestCase):
    def test_sun_lights_only(self):
        com = {'primaryLight': [{'type': 0}, {'type': 1, 'color': [0, 0, 1], 'dir': [0, 0, 1]}, {'type': 2, 'color': [1, 1, 1], 'dir': [0, 0, 1]}, {'type': 1, 'color': [0, 0, 1], 'dir': [0, 0, 1]}]}
        n = S.set_sun(com, [0.0, 0.0, -1.0], [1.0, 0.5, 0.25], 2.0)
        self.assertEqual(n, 2)
        self.assertEqual(com['primaryLight'][1]['color'], [2.0, 1.0, 0.5])
        self.assertEqual(com['primaryLight'][1]['dir'], [0.0, 0.0, 1.0] if False else [-0.0, -0.0, 1.0])     # the file stores the way to the sun
        self.assertEqual(com['primaryLight'][2]['color'], [1, 1, 1])

    def test_sun_flare_numbers_are_written_in_place(self):
        W = S._worldkit().layout('GfxWorld')
        buf = bytes(6 + W.size + 40)
        new = S.set_sun_flare(buf, {'spriteSize': 16.0, 'flareFadeInTime': 700, 'glareMaxLighten': 0.3})
        self.assertEqual(len(new), len(buf))
        got = S.sun_flare(new)
        self.assertEqual((got['spriteSize'], got['flareFadeInTime']), (16.0, 700))
        self.assertAlmostEqual(got['glareMaxLighten'], 0.3, places=6)
        self.assertEqual(got['flareMaxSize'], 0.0)
        changed = [i for i in range(len(buf)) if buf[i] != new[i]]
        lo, hi = 6 + W.off('sun.spriteSize'), 6 + W.off('sun.sunFxPosition[0]')
        self.assertTrue(all(lo <= i < hi for i in changed), changed)      # nothing outside the sun's numbers moves
        with self.assertRaises(ValueError):
            S.set_sun_flare(buf, {'spriteMaterial': 1})

    def test_sky_name_is_replaced_in_the_stream(self):
        buf = b'abc' + S.SKY_TAG + b'sky_cp_zmb_night_01\0' + b'tail'
        self.assertEqual(S.sky_name(buf), 'sky_cp_zmb_night_01')
        new = S.set_sky_name(buf, 'sky_cp_town')
        self.assertEqual(new, b'abc' + S.SKY_TAG + b'sky_cp_town\0tail')


if __name__ == '__main__':
    unittest.main()
