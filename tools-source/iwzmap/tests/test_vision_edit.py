"""The map vision from layout.json `lighting` (vision_edit.py): keys replaced in place, unknown keys refused, the stock file never written through."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import vision_edit as V  # noqa: E402

STOCK = 'fogDensity "300"\nfogColor "0.1137255 0.1529412 0.1803922"\nfogMaxOpacity "1"\ntonemapAuto "1"\ntonemapExposure "9"\nr_ssaoStrength "2"\n'
DUMP = os.path.join(os.environ.get('IWZ_TEMPLATE_DUMP') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime', 'iwz-map-ref-a', 'dump'),
                    'cp_zmb', 'vision', 'cp_zmb.vision')


class Vision(unittest.TestCase):
    def test_convenience_keys_and_raw_keys(self):
        e = V.edits_of({'fog': {'color': [0.2, 0.1, 0.05], 'density': 120, 'max_opacity': 0.4}, 'exposure': {'auto': False, 'value': 6},
                        'vision': {'r_ssaoStrength': 3, 'fogDensity': 100}})
        self.assertEqual(e['fogColor'], '0.2 0.1 0.05'); self.assertEqual(e['tonemapAuto'], '0'); self.assertEqual(e['fogDensity'], '100')   # raw wins
        new, rep = V.apply(STOCK, e, V.keys_of(STOCK))
        self.assertIn('fogColor "0.2 0.1 0.05"', new); self.assertIn('tonemapExposure "6"', new); self.assertIn('r_ssaoStrength "3"', new)
        self.assertIn('fogMaxOpacity "0.4"', new)
        self.assertEqual(rep['changed']['fogDensity'], ['300', '100']); self.assertEqual(rep['added'], [])
        self.assertEqual(len(new.splitlines()), len(STOCK.splitlines()))            # same lines, same order

    def test_unknown_key_is_refused_with_the_nearest(self):
        with self.assertRaises(ValueError) as c:
            V.apply(STOCK, {'fogDensty': '1'}, set(V.keys_of(STOCK)))
        self.assertIn('fogDensity', str(c.exception))
        with self.assertRaises(ValueError):
            V.edits_of({'fog': {'colour': [1, 1, 1]}})

    def test_zone_file_is_replaced_not_written_through(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, 'zone', 'vision')); os.makedirs(os.path.join(d, 'dump'))
            stock = os.path.join(d, 'dump', 'cp_zmb.vision')
            open(stock, 'w', newline='\n').write(STOCK)
            link = os.path.join(d, 'zone', 'vision', 'cp_iwz.vision')
            os.link(stock, link)
            rep = V.apply_to_zone(os.path.join(d, 'zone'), 'cp_iwz', {'fog': {'density': 50}})
            self.assertEqual(rep['changed']['fogDensity'], ['300', '50'])
            self.assertIn('fogDensity "300"', open(stock).read())                    # the stock dump is untouched
            self.assertIn('fogDensity "50"', open(link).read())
            self.assertIsNone(V.apply_to_zone(os.path.join(d, 'zone'), 'cp_iwz', {}))

    @unittest.skipUnless(os.path.isfile(DUMP), 'stock dump not on this machine')
    def test_real_stock_vision_takes_the_keys(self):
        text = open(DUMP, encoding='latin1').read()
        e = V.edits_of({'fog': {'color': [0.3, 0.1, 0.1], 'density': 150, 'max_opacity': 0.5, 'intensity': 1.0}, 'exposure': {'auto': False, 'value': 8, 'adjust': -1}})
        new, rep = V.apply(text, e, V.keys_of(text))
        self.assertEqual(sorted(rep['changed']), sorted(e)); self.assertEqual(rep['added'], [])
        self.assertEqual(len(new.splitlines()), len(text.splitlines()))


if __name__ == '__main__':
    unittest.main()
