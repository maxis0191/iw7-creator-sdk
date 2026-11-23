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

    def test_sky_name_is_replaced_in_the_stream(self):
        buf = b'abc' + S.SKY_TAG + b'sky_cp_zmb_night_01\0' + b'tail'
        self.assertEqual(S.sky_name(buf), 'sky_cp_zmb_night_01')
        new = S.set_sky_name(buf, 'sky_cp_town')
        self.assertEqual(new, b'abc' + S.SKY_TAG + b'sky_cp_town\0tail')

    def test_always_loaded_sky_takes_the_template_skys_places(self):
        img = lambda n: S.SKY_TAG + n + b'\0'          # noqa: E731
        buf = img(b'aaa_c') + img(b'sky_cp_zmb_night_01') + img(b'zmb_arcade_sky_card_01_c') + b'\x08\x01flags' + img(b'w/sky_cp_zmb') + img(b'w/zmb_arcade_sky_card_01') + b'end'
        new, rep = S.set_streamed_sky(buf, 'sky_cp_town', 'w/sky_cp_town')
        self.assertEqual(new, img(b'aaa_c') + img(b'sky_cp_town') + img(b'zmb_arcade_sky_card_01_c') + b'\x08\x01flags' + img(b'w/sky_cp_town') + img(b'w/zmb_arcade_sky_card_01') + b'end')
        self.assertEqual(rep, {'image': ['sky_cp_zmb_night_01', 'sky_cp_town'], 'material': ['w/sky_cp_zmb', 'w/sky_cp_town']})
        again, rep2 = S.set_streamed_sky(new, 'sky_mp_paris', 'w/sky_mp_paris')          # a kept assembly already carries the last sky: the place is found by the prefix
        self.assertIn(img(b'sky_mp_paris'), again)
        self.assertNotIn(b'sky_cp_town', again)
        same, _ = S.set_streamed_sky(new, 'sky_cp_town', 'w/sky_cp_town')
        self.assertEqual(same, new)

    def test_always_loaded_list_without_one_sky_is_left_alone(self):
        buf = S.SKY_TAG + b'sky_a\0' + S.SKY_TAG + b'sky_b\0'
        new, rep = S.set_streamed_sky(buf, 'sky_cp_town', 'w/sky_cp_town')
        self.assertEqual(new, buf)
        self.assertIn('not changed', rep['image'])
        self.assertIn('not changed', rep['material'])


if __name__ == '__main__':
    unittest.main()
