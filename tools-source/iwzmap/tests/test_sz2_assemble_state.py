"""sz2_assemble.py: a custom material (colour route and extended route) gets the base material's technique state files under its own name
(ZoneTool stops a build with 'statebits for techset ... are missing' otherwise). Synthetic work tree, no ZoneTool."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TECH = 'w_l_sm_replace_i0c0n0'
TECH_EXT = 'w_l_sm_replace_i0c0s0n0p0'


def put(path, data=b'x'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def stock(root, tech, base, texture_semantics):
    mat = {'techniqueSet->name': tech, 'constantTable': [{'name': 'colorTint', 'literal': [1, 1, 1, 1]}],
           'textureTable': [{'semantic': s, 'image': 'stock_%d' % s} for s in texture_semantics]}
    put(os.path.join(root, 'materials', 'w', base + '.json'), json.dumps(mat).encode())
    for ext in ('.stateinfo', '.statebits', '.statebitsmap'):
        put(os.path.join(root, 'techsets', 'state', tech, 'w', base + ext), (base + ext).encode())
    for ext in ('.cbi', '.cbt'):
        put(os.path.join(root, 'techsets', 'constantbuffer', tech, 'w', base + ext), (base + ext).encode())


class StateFiles(unittest.TestCase):
    def build(self, overlay=False):
        t = tempfile.mkdtemp(prefix='sz2state_')
        self.addCleanup(__import__('shutil').rmtree, t, True)
        work, src, dumps = os.path.join(t, 'work'), os.path.join(t, 'src'), os.path.join(t, 'dump')
        tree = os.path.join(work, 'zonetool', 'cp_t')
        stock(dumps if overlay else tree, TECH, 'base_a', [2])
        stock(dumps if overlay else tree, TECH_EXT, 'base_b', [2, 14, 15])
        put(os.path.join(work, 'zone_source', 'cp_t.csv'), b'// x\ncom_map,cp_t\n')
        os.makedirs(tree, exist_ok=True)
        for n in ('red', 'n1', 'g1'):
            put(os.path.join(t, n + '.tga'))
        put(os.path.join(t, 'n1.dds'))
        spec = {'custom': {
            'a': {'path': 'w/iwz_a', 'base': 'base_a', 'image': 'red', 'tga': os.path.join(t, 'red.tga'), 'tint': [1, 0, 0, 1]},
            'b': {'path': 'w/iwz_b', 'base': 'base_a', 'ext': {'base': 'base_b', 'images': {
                '14': {'image': 'red', 'tga': os.path.join(t, 'red.tga')}, '15': {'image': 'n1', 'tga': os.path.join(t, 'n1.tga')}}}}}}
        put(os.path.join(src, 'custom_materials.json'), json.dumps(spec).encode())
        script = os.path.join(HERE, 'sz2_assemble.py')
        if overlay:
            ov = os.environ.get('STUDIO_OVERLAY')
            if not (ov and os.path.isfile(ov)):
                self.skipTest('STUDIO_OVERLAY (Studio compile/overlay.py) not set')
            cmd = [sys.executable, '-B', ov, tree, dumps, '--', script, work, 'cp_t', src]
        else:
            cmd = [sys.executable, '-B', script, work, 'cp_t', src]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return tree, dumps

    def check(self, tree, dumps):
        def rd(sub, tech, name, ext):
            with open(os.path.join(tree, 'techsets', sub, tech, 'w', name + ext), 'rb') as f:
                return f.read().decode()
        for sub, exts in (('state', ('.stateinfo', '.statebits', '.statebitsmap')), ('constantbuffer', ('.cbi', '.cbt'))):
            for ext in exts:
                self.assertEqual(rd(sub, TECH, 'iwz_a', ext), 'base_a' + ext)         # the colour route clones its base's files
                self.assertEqual(rd(sub, TECH_EXT, 'iwz_b', ext), 'base_b' + ext)     # the extended route clones the files of its ext base
        self.assertTrue(os.path.isfile(os.path.join(tree, 'images', 'n1.dds')))       # a DDS beside the TGA goes with it
        mat = json.load(open(os.path.join(tree, 'materials', 'w', 'iwz_b.json')))
        self.assertEqual({t['semantic']: t['image'] for t in mat['textureTable']}, {2: 'stock_2', 14: 'red', 15: 'n1'})
        if dumps:      # a dump is never written
            self.assertFalse(os.path.exists(os.path.join(dumps, 'techsets', 'state', TECH, 'w', 'iwz_a.statebits')))

    def test_full_tree(self):
        self.check(*self.build())

    def test_overlay_of_dumps(self):
        self.check(*self.build(overlay=True))


if __name__ == '__main__':
    unittest.main()
