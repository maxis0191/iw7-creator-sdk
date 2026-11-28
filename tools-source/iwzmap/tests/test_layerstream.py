"""Layer stream layout table (layerstream/extract_layouts.py, data/layer_layouts.json): strides of the stock layered techsets without any dump,
and, when the stock dumps are present, a re-extraction that must equal the shipped table."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from layerstream import extract_layouts as X  # noqa: E402

FIXTURE = os.path.join(HERE, 'fixtures_layer_stride_by_techset.json')       # measured from 422 cp_disco chunks: [sub-materials, techset, [strides]]
DUMP_ROOT = X.DEFAULT_DUMP_ROOT
HAVE_DUMP = os.path.isdir(os.path.join(DUMP_ROOT, 'cp_disco', 'materials')) and os.path.isdir(os.path.join(DUMP_ROOT, 'techsets_cp_disco', 'techsets'))


class Table(unittest.TestCase):
    def test_reference_materials_strides(self):
        for name, stride in (('*622n_89_91_282n', 28), ('*387n_86n_354n_362n', 36), ('*622n_274n', 12)):
            lay = X.material_layout(name, 'cp_disco')
            self.assertIsNotNone(lay, name)
            self.assertEqual(lay['stride'], stride, name)
            self.assertTrue(lay['supported'], name)

    def test_reference_element_order(self):
        lay = X.material_layout('*622n_89_91_282n', 'cp_disco')
        self.assertEqual([(e['sem'], e['idx'], e['fmt'], e['bytes'], e['offset']) for e in lay['elements']],
                         [('TEXCOORD', 3, 'f32', 16, 0), ('TEXCOORD', 4, 'f32', 8, 16), ('TEXCOORD', 5, 'u8x4', 4, 24)])
        self.assertEqual(sum(e['bytes'] for e in lay['elements']), 28)
        offs = [e['offset'] for e in lay['elements']]
        self.assertEqual(offs, sorted(offs))
        self.assertEqual(lay['elements'][-1]['offset'] + lay['elements'][-1]['bytes'], lay['stride'])

    def test_stride_of_the_254_measured_techsets(self):
        fx = json.load(open(FIXTURE))
        self.assertEqual(len(fx), 254)
        for _ns, ts, strides in fx:
            lay = X.techset_layout(ts)
            self.assertIsNotNone(lay, ts)
            self.assertEqual([float(lay['stride'])], [float(s) for s in strides], ts)

    def test_supported_counts_and_strides_are_multiples_of_four(self):
        t = X.load_table()
        m = t['materials']['cp_disco']
        self.assertEqual(len(m), 1528)
        self.assertEqual(sum(1 for ts in m.values() if t['techsets'][ts]['supported']), 1493)
        for ts, lay in t['techsets'].items():
            self.assertEqual(lay['stride'] % 4, 0, ts)
            self.assertEqual(lay['supported'], X.technique_supported(lay['elements']), ts)

    def test_unsupported_when_an_undecoded_element_is_read(self):
        sig = [('TEXCOORD', 3, 1, 3), ('TEXCOORD', 5, 2, 15), ('TEXCOORD', 10, 3, 15), ('COLOR', 1, 4, 1)]
        els, stride = X.layout_from_signature('pp.fcc0.ft0t0.ft1t3.3x0t5.fx1ta.fx2c1.f', sig)
        self.assertEqual([(e['sem'], e['idx']) for e in els], [('TEXCOORD', 3), ('TEXCOORD', 5), ('TEXCOORD', 10), ('COLOR', 1)])
        self.assertEqual(stride, 8 + 4 + 4 + 4)
        self.assertFalse(X.technique_supported(els))
        self.assertTrue(X.technique_supported(els[:2]))

    def test_rotation_bytes(self):
        self.assertEqual(X.encode_rotation(1, 0, 0, 1), bytes([254, 127, 127, 254]))
        self.assertEqual(X.encode_rotation(0, -1, 1, 0), bytes([127, 0, 254, 127]))

    def test_name_is_map_local(self):
        self.assertIsNone(X.material_layout('*no_such_material'))
        self.assertIsNone(X.material_layout('*622n_89_91_282n', 'no_zone'))


@unittest.skipUnless(HAVE_DUMP, 'stock dumps not present (RESTORE)')
class ReExtract(unittest.TestCase):
    def test_cp_disco_reextraction_equals_the_table(self):
        mats, tss, unresolved = X.extract_zone(DUMP_ROOT, 'cp_disco')
        t = X.load_table()
        self.assertEqual(unresolved, [])
        self.assertEqual(len(tss), 597)
        self.assertEqual(mats, t['materials']['cp_disco'])
        diff = [ts for ts, lay in tss.items() if {k: v for k, v in lay.items() if k != 'technique'} != {k: v for k, v in t['techsets'][ts].items() if k != 'technique'}]
        self.assertEqual(diff, [])

    def test_cli_check_is_identical(self):
        self.assertEqual(X.main(['--check']), 0)


if __name__ == '__main__':
    unittest.main()
