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

    def test_audio_zones(self):
        s = spec(zones={'pit': {'audio_zone': 'z_pit'}, 'hall': {'audio_zone': 'z_missing'}})
        r = audio_layout.plan(LAYOUT, s, BANK, {'z_pit'})
        self.assertEqual(r['errors'], ['zone hall: audio zone z_missing is not a sound zone of the bank'])
        text = audio_layout.gsc(r, 'cp_x', 'layout.json')
        self.assertIn('ambience_audio_zone( "pit", ( 0, 1000, -400 ), ( 1000, 1400, -80 ), "z_pit" );', text)

    def test_audio_zone_bed_from_bank(self):
        # the engine's zone bed is silent in a usermap: the module plays the sound zone's ambience alias itself
        s = spec(zones={'pit': {'audio_zone': 'z_pit'}})
        r = audio_layout.plan(LAYOUT, s, BANK, {'z_pit': {'name': 'z_pit', 'ambience': 'amb_bed'}})
        self.assertEqual(r['zones'][0]['bed'], 'amb_bed')
        self.assertIn('"z_pit", "amb_bed" );', audio_layout.gsc(r, 'cp_test', 'layout.json'))

    def test_rc1_rooms(self):
        layout = {'rooms': {'arrival': {'box': [0, 4800, 1024, 5824], 'height': 288}}}
        r = audio_layout.plan(layout, {'zones': {'arrival': {'bed': 'bed_a'}},
                                       'emitters': [{'zone': 'arrival', 'alias': 'hum', 'at': 'zone:0.5,0.5,40'}],
                                       'song_ee': {'at': [40, 5100, 0], 'yaw': 45, 'zone': 'arrival'}}, BANK)
        self.assertEqual(r['errors'], [])
        self.assertEqual(r['zones'][0]['mins'], [0, 4800, -16])
        self.assertEqual(r['emitters'][0]['origin'], [512, 5312, 40])

class SoundscapeTest(unittest.TestCase):
    def test_calls_far_points_and_checks(self):
        sc = {'scatter': [{'alias': 'creak', 'zones': ['hall', 'pit'], 'wait': [5, 9], 'dist': [100, 400]}],
              'far': [{'alias': 'creak', 'at': [-3000, 0, 0], 'wait': [60, 90]}],
              'loops': [{'alias': 'hum', 'at': 'decor:gen@pit', 'zone': 'pit', 'offset': [0, 0, 20]}],
              'phone': {'ring': 'creak', 'hangup': 'hum', 'at': 'light:hall:0', 'zone': 'hall', 'wait': [30, 60], 'radius': 150},
              'intro': {'alias': 'bed_a'}}
        r = audio_layout.soundscape(spec(soundscape=sc), LAYOUT, audio_layout.zones_of(LAYOUT), BANK)
        self.assertEqual(r['errors'], [])
        self.assertEqual(r['far'][0]['origin'], [-3000.0, 0.0, 0.0])          # outside every zone: allowed for far
        text = '\n'.join(audio_layout.gsc_calls(r['calls'], 'm'))
        self.assertIn('m::soundscape_scatter( "creak", [ ( 0, 0, -16 ), ( 0, 1000, -400 ) ], [ ( 1000, 1000, 320 ), ( 1000, 1400, -80 ) ], 5, 9, 100, 400, 0 );', text)
        self.assertIn('m::soundscape_loop( "hum", ( 100, 1100, -364 ) );', text)
        self.assertIn('m::soundscape_phone( ( 500, 500, 300 ), "creak", "hum", 30, 60, 150 );', text)
        self.assertIn('m::soundscape_intro( "bed_a" );', text)
        sc['scatter'][0]['alias'] = 'nope'
        sc['loops'][0]['at'] = [5000, 5000, 0]
        errors = '\n'.join(audio_layout.soundscape(spec(soundscape=sc), LAYOUT, audio_layout.zones_of(LAYOUT), BANK)['errors'])
        self.assertIn('alias nope is not in the bank', errors)
        self.assertIn('lies outside zone pit', errors)



if __name__ == '__main__':
    unittest.main()
