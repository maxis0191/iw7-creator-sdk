"""Tests of audio_layout.py (stdlib unittest): python -m unittest test_audio_layout.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_layout  # noqa: E402

LAYOUT = {
    'zones': {'hall': {'box': [0, 0, -16, 1000, 1000, 320]}, 'pit': {'box': [0, 1000, -400, 1000, 1400, -80]}},
    'lights': [{'zone': 'hall', 'origin': [500, 500, 300]}],
    'decor': [{'zone': 'pit', 'model': 'gen', 'origin': [100, 1100, -384]}],
    'quest': {'teddy_bear': {'origin': [200, 1200, -213], 'yaw': 90}},
    'interactions': [{'kind': 'generator', 'origin': [900, 900, 0], 'area': 'hall'}],
}
BANK = {'bed_a', 'bed_b', 'hum', 'creak'}


def spec(**kw):
    s = {'default_bed': 'bed_a', 'zones': {'pit': {'bed': 'bed_b'}, 'hall': {'bed': 'bed_a'}},
         'emitters': [{'zone': 'hall', 'alias': 'hum', 'at': 'light:hall:0', 'offset': [0, 0, -12]},
                      {'zone': 'pit', 'alias': 'hum', 'at': 'decor:gen@pit', 'offset': [0, 0, 40]},
                      {'zone': 'hall', 'alias': 'creak', 'at': 'zone:0.5,0.25,100', 'random': [5, 9]},
                      {'zone': 'hall', 'alias': 'hum', 'at': 'interaction:generator'}],
         'song_ee': {'at': 'quest:teddy_bear', 'zone': 'pit'}}
    s.update(kw)
    return s


class LayoutTest(unittest.TestCase):
    def test_anchors_and_gsc(self):
        r = audio_layout.plan(LAYOUT, spec(), BANK)
        self.assertEqual(r['errors'], [])
        self.assertEqual([e['origin'] for e in r['emitters']],
                         [[500, 500, 288], [100, 1100, -344], [500, 250, 100], [900, 900, 0]])
        self.assertEqual(r['song_ee'], {'origin': [200, 1200, -213], 'yaw': 90.0, 'zone': 'pit'})
        self.assertEqual(r['loops'], {'hall': 2, 'pit': 1})
        text = audio_layout.gsc(r, 'cp_x', 'layout.json')
        self.assertIn('ambience_zone( "pit", ( 0, 1000, -400 ), ( 1000, 1400, -80 ), "bed_b" );', text)
        self.assertIn('scripts\\cp\\maps\\cp_x\\cp_x_audio::ambience_emitter( "creak", ( 500, 250, 100 ), 1, 5, 9 );', text)
        self.assertIn('song_ee_init( ( 200, 1200, -213 ), ( 0, 90, 0 ) );', text)
        self.assertIn('ambience_init( emitters, "bed_a", zones );', text)

    def test_errors(self):
        bad = spec(emitters=[{'zone': 'hall', 'alias': 'nope', 'at': [10, 10, 10]},
                             {'zone': 'hall', 'alias': 'hum', 'at': [10, 10, 900]},
                             {'zone': 'hall', 'alias': 'creak', 'at': [10, 10, 10], 'random': [9, 5]},
                             {'zone': 'hall', 'alias': 'hum', 'at': 'light:hall:3'}],
                   zones={'attic': {'bed': 'bed_a'}, 'hall': {'bed': 'missing'}})
        errors = audio_layout.plan(LAYOUT, bad, BANK)['errors']
        joined = '\n'.join(errors)
        for needle in ('zone attic is not in the layout', 'bed missing is not in the bank', 'nope: alias is not in the bank',
                       'outside zone hall', 'random wait needs', 'zone hall has 1 lights'):
            self.assertIn(needle, joined)

    def test_loop_limits(self):
        many = [{'zone': 'hall', 'alias': 'hum', 'at': [10 * i, 10, 10]} for i in range(5)]
        errors = audio_layout.plan(LAYOUT, spec(emitters=many, max_loops_per_zone=4, max_loops_total=3), BANK)['errors']
        self.assertTrue(any('5 looping emitters (limit 4)' in e for e in errors))
        self.assertTrue(any('5 looping emitters in total (limit 3)' in e for e in errors))

    def test_rc1_rooms(self):
        layout = {'rooms': {'arrival': {'box': [0, 4800, 1024, 5824], 'height': 288}}}
        r = audio_layout.plan(layout, {'zones': {'arrival': {'bed': 'bed_a'}},
                                       'emitters': [{'zone': 'arrival', 'alias': 'hum', 'at': 'zone:0.5,0.5,40'}],
                                       'song_ee': {'at': [40, 5100, 0], 'yaw': 45, 'zone': 'arrival'}}, BANK)
        self.assertEqual(r['errors'], [])
        self.assertEqual(r['zones'][0]['mins'], [0, 4800, -16])
        self.assertEqual(r['emitters'][0]['origin'], [512, 5312, 40])


if __name__ == '__main__':
    unittest.main()
