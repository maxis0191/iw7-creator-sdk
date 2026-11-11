"""The culling data checks: tome reading, the frustum and distance test, the door views."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tome_cull as tc  # noqa: E402

BIG = tc.FLT_MAX


class TomeTests(unittest.TestCase):
    def setUp(self):
        self.objs = [(0, (0, 0, 0, 100, 100, 10), BIG),                      # a floor surface
                     (0x10000000, (500, -10, 0, 520, 10, 40), 1000.0 ** 2),   # prop 0, cull 1000
                     (0x10000001, (-520, -10, 0, -500, 10, 40), BIG),         # prop 1 behind, never distance culled
                     (0x10000002, (3000, -10, 0, 3020, 10, 40), 1500.0 ** 2)]  # prop 2, far ahead
        self.data = tc.write_tome(self.objs, (-4000, -4000, -100), (4000, 4000, 500))
        self.tome = tc.Tome(self.data)

    def test_reads_what_was_written(self):
        t = self.tome
        self.assertTrue(t.size_ok)
        self.assertTrue(t.crc_ok)
        self.assertEqual(t.count, 4)
        self.assertEqual(t.by_class(1), {0: 1, 1: 2, 2: 3})
        self.assertEqual(t.bounds[1], (500, -10, 0, 520, 10, 40))
        self.assertEqual(t.far_sq[1], 1000.0 ** 2)

    def test_a_changed_byte_breaks_the_checksum(self):
        bad = bytearray(self.data)
        bad[0x200] ^= 1
        self.assertFalse(tc.Tome(bytes(bad)).crc_ok)

    def test_not_a_tome_is_refused(self):
        with self.assertRaises(ValueError):
            tc.Tome(b'\0' * 0x200)

    def test_frustum_and_distance(self):
        view = tc.View.from_yaw_pitch((0.0, 0.0, 20.0), 0.0, 0.0)       # looking along +x
        self.assertEqual(tc.tome_keeps(self.tome, 1, view), (True, True))     # 500 ahead, cull 1000
        self.assertEqual(tc.tome_keeps(self.tome, 2, view)[0], False)        # behind the camera
        self.assertEqual(tc.tome_keeps(self.tome, 3, view), (True, False))    # 3000 ahead, cull 1500
        back = tc.View.from_yaw_pitch((0.0, 0.0, 20.0), 180.0, 0.0)
        self.assertEqual(tc.tome_keeps(self.tome, 2, back), (True, True))

    def test_a_box_beside_the_view_is_outside(self):
        view = tc.View.from_yaw_pitch((0.0, 0.0, 20.0), 0.0, 0.0)
        # 500 ahead, 1000 to the left: tan of the half view is 0.85, so 425 would be the edge
        self.assertFalse(view.box_in((490, 990, 0, 510, 1010, 40)))
        self.assertTrue(view.box_in((490, 400, 0, 510, 420, 40)))

    def test_distance_is_to_the_nearest_point_of_the_box(self):
        self.assertEqual(tc.box_nearest_sq((10, 0, 0, 20, 5, 5), (0, 0, 0)), 100.0)
        self.assertEqual(tc.box_nearest_sq((-1, -1, -1, 1, 1, 1), (0, 0, 0)), 0.0)


class SizeCullTests(unittest.TestCase):
    def test_a_sphere_at_its_cull_distance_covers_the_pop_pixels(self):
        d = tc.size_cull(20.0, 30)
        f = 1920 * 0.5 / tc.TAN_HALF[0]
        self.assertAlmostEqual(3.141592653589793 * (f * 20.0 / d) ** 2, 30.0, delta=0.1)
        self.assertGreater(tc.size_cull(20.0, 10), d)          # a stricter rule keeps props longer


class DoorViewTests(unittest.TestCase):
    def test_two_sides_looking_through_the_opening(self):
        layout = {'zones': {'a': {'box': [0, 0, 0, 1000, 1000, 300], 'floor': 0},
                            'b': {'box': [0, 1000, 0, 1000, 2000, 300], 'floor': 0}},
                  'openings': [{'name': 'D1', 'kind': 'door', 'axis': 'x', 'zones': ['a', 'b'], 'walls': {'a': 1000, 'b': 1000},
                                'a': 400, 'b': 600, 'z0': 0, 'z1': 200}]}
        views = tc.door_views(layout, back=(100.0,), turns=(0.0,))
        self.assertEqual(len(views), 2)
        va = [v for v in views if v['from'] == 'a'][0]
        vb = [v for v in views if v['from'] == 'b'][0]
        self.assertEqual(va['origin'][:2], (500.0, 900.0))
        self.assertEqual(va['yaw'], 90.0)          # zone a lies below y 1000: look +y
        self.assertEqual(vb['origin'][:2], (500.0, 1100.0))
        self.assertEqual(vb['yaw'], -90.0)
        view = tc.View.from_yaw_pitch(va['origin'], va['yaw'], va['pitch'])
        self.assertTrue(view.box_in((450, 1400, 0, 550, 1500, 100)))   # straight through the door


if __name__ == '__main__':
    unittest.main()
