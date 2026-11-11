"""Unit tests of kit_import.py --stage-xmodels (the .xmb files the map compiler reads for kit models placed as
static models) on synthetic files (no machine paths, no game data)."""
import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import kit_import  # noqa: E402


class StageXmodelsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.disco = os.path.join(d, 'disco')
        self.port = os.path.join(d, 'port')
        for root, files in ((self.disco, ('bench.xmb', 'bench_lod0.hkx', 'bench_lod1.hkx', 'benchmark.xmb')),
                            (self.port, ('cabinet.xmb',))):
            os.makedirs(os.path.join(root, 'xmodel'))
            for f in files:
                with open(os.path.join(root, 'xmodel', f), 'wb') as o:
                    o.write(f.encode())
        self.src = os.path.join(d, 'src')
        os.makedirs(self.src)

    def tearDown(self):
        self.tmp.cleanup()

    def run_stage(self, models):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kit_import.main(['unused_work', 'unused_map', '--dump', 'cp_disco=' + self.disco,
                                    '--dump', 'train=' + self.port, '--models', models, '--stage-xmodels', self.src])
        return code, out.getvalue()

    def test_stages_xmb_and_its_physics_lods_only(self):
        code, out = self.run_stage('bench,train:cabinet')
        self.assertEqual(code, 0, out)
        staged = sorted(os.listdir(os.path.join(self.src, 'xmodel')))
        self.assertEqual(staged, ['bench.xmb', 'bench_lod0.hkx', 'bench_lod1.hkx', 'cabinet.xmb'])
        with open(os.path.join(self.src, 'xmodel', 'cabinet.xmb'), 'rb') as f:
            self.assertEqual(f.read(), b'cabinet.xmb')
        self.assertIn('staged 2 xmodel(s)', out)

    def test_missing_model_fails(self):
        code, out = self.run_stage('bench,nowhere')
        self.assertEqual(code, 1)
        self.assertIn('missing: nowhere', out)

    def test_zone_prefix_limits_the_search(self):
        code, _ = self.run_stage('train:bench')
        self.assertEqual(code, 1)

    def test_restaging_replaces_files(self):
        self.assertEqual(self.run_stage('bench')[0], 0)
        self.assertEqual(self.run_stage('bench')[0], 0)
        self.assertEqual(len(os.listdir(os.path.join(self.src, 'xmodel'))), 3)


if __name__ == '__main__':
    unittest.main()
