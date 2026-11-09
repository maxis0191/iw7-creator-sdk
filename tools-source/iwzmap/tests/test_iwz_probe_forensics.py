"""Probe forensics: every recorded log format and every trajectory class."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import iwz_probe_forensics as pf  # noqa: E402

P = '[IWZ local] '


def trail(case, points, n=None, dist=None, off=None):
    out = []
    for i, p in enumerate(points):
        d = dist[i] if dist else 300
        o = off[i] if off else 0
        out.append('%sSP_T case=%s %st=%d pos=(%s, %s, %s) speed=0 dist=%s nav=(%s, %s, %s) nav_off=%s\t' % (
            P, case, '' if n is None else 'n=%d ' % n, 250 * (i + 1), p[0], p[1], p[2], d,
            p[0], p[1], p[2] - o, o))
    return out


def one(lines):
    cases = pf.parse_log(lines)
    return pf.analyse_case(cases[0])


class ParseTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(pf.parse_value('(1, 2.5, -3)'), (1.0, 2.5, -3.0))
        self.assertEqual(pf.parse_value('(1, 2, 3)|door'), (1.0, 2.0, 3.0))
        self.assertEqual(pf.parse_value('12.5'), 12.5)
        self.assertEqual(pf.parse_value('0/6'), '0/6')

    def test_lines_without_a_case_are_ignored(self):
        self.assertEqual(pf.parse_log(['hello', P + 'SPAWNED; origin=(0, 0, 0)', P + 'SP_T t=1']), [])

    def test_old_format_without_zombie_index(self):
        lines = trail('east_up', [(0, 0, 0), (100, 0, 30), (200, 0, 64)]) + [
            P + 'SP_END case=east_up result=reached ms=10750 spawner=(2250, 2000, -319)\t']
        c = one(lines)
        self.assertEqual((c['verdict'], c['reached'], c['total']), ('pass', 1, 1))


class ClassTests(unittest.TestCase):
    def end(self, case, result, ms=45000, placed=1):
        return [P + 'SP_END case=%s result=%s reached died=0 ms=%d spawner=(0, 0, 0) placed=%d\t' % (
            case, result, ms, placed)]

    def test_sunk_body_is_a_geometry_suspect(self):
        pts = [(i * 20, 0, 0) for i in range(12)]
        off = [0, 0, -5, -20, -30, -30, -30, -30, -30, -30, -30, -30]
        c = one(trail('up', pts, n=0, off=off) + self.end('up', '0/1'))
        self.assertEqual(c['classes'], ['sub_surface'])
        self.assertEqual(c['verdict'], 'geometry_suspect')
        self.assertEqual(c['zombies'][0]['min_nav_off'], -30.0)

    def test_fall_out_of_world_keeps_the_place_it_left_the_floor(self):
        pts = [(0, 0, 0), (40, 0, 0), (80, 0, 0), (80, 0, -900), (80, 0, -454641)]
        off = [0, 0, 0, -900, -454641]
        lines = trail('far', pts, n=0, off=off) + [
            P + 'SP_GONE case=far n=0 t=1250 last=(80, 0, -454641)\t'] + self.end('far', '0/1')
        c = one(lines)
        self.assertEqual(c['classes'], ['fell_out_of_world'])
        self.assertEqual(c['zombies'][0]['last_sane'], (80.0, 0.0, 0.0))

    def test_zombie_that_changed_floor_is_not_a_map_failure(self):
        pts = [(i * 60, 0, min(63, i * 8)) for i in range(16)]
        c = one(trail('far3', pts, n=0) + self.end('far3', '0/1', ms=33500))
        self.assertEqual(c['classes'], ['crossed_level'])
        self.assertEqual(c['verdict'], 'probe_artifact')
        self.assertIn('changed_floor_not_counted', c['flags'])

    def test_case_that_ends_too_soon_proves_nothing(self):
        pts = [(i * 10, 0, 0) for i in range(8)]
        dist = [400 - i * 10 for i in range(8)]
        c = one(trail('down6', pts, n=0, dist=dist) + self.end('down6', '0/6', ms=5250, placed=0))
        self.assertEqual(c['verdict'], 'probe_artifact')
        self.assertIn('ended_early', c['flags'])
        self.assertIn('ended_while_walking', c['flags'])

    def test_reach_lines_count_per_zombie(self):
        lines = trail('up6', [(0, 0, 0), (50, 0, 20), (90, 0, 40)], n=0) + \
            trail('up6', [(0, 0, 0), (2, 0, 0), (3, 0, 0)], n=1) + [
                P + 'SP_REACH case=up6 n=0 t=7000\t'] + self.end('up6', '1/2')
        c = one(lines)
        self.assertEqual(c['classes'], ['reached', 'never_moved'])
        self.assertEqual(c['verdict'], 'partial')

    def test_stuck_means_no_movement_at_the_end(self):
        pts = [(i * 30, 0, 0) for i in range(5)] + [(120, 0, 0)] * 12
        c = one(trail('s', pts, n=0) + self.end('s', '0/1'))
        self.assertEqual(c['classes'], ['stuck'])
        self.assertEqual(c['verdict'], 'geometry_suspect')


class CohortTests(unittest.TestCase):
    def test_same_case_with_two_outcomes(self):
        ok = pf.analyse_case(pf.parse_log(trail('w', [(0, 0, 0), (90, 0, 60)]) + [
            P + 'SP_END case=w result=reached ms=9000'])[0])
        bad = pf.analyse_case(pf.parse_log(trail('w', [(0, 0, 0)] * 20) + [
            P + 'SP_END case=w result=died ms=14250'])[0])
        self.assertEqual(ok['verdict'], 'pass')
        self.assertNotEqual(bad['verdict'], 'pass')


if __name__ == '__main__':
    unittest.main()
