"""crowd_seen.py on a synthetic frame: a camera looking along +x, a depth buffer painted by hand."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
try:
    import numpy as np
except ImportError:          # pragma: no cover
    np = None

W, H = 320, 180


@unittest.skipIf(np is None, 'needs numpy')
class CrowdSeenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import iw7_see as S
        import crowd_seen as C
        cls.S, cls.C = S, C
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.tmp.name
        cam = {'schema': 'iw7.see-camera/1', 'name': 'v', 'frame': {'file': 'v.bmp', 'width': W, 'height': H},
               'camera': {'tan_half_fov': [1.0, 0.5625], 'origin': [0.0, 0.0, 60.0], 'axis': [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 'z_near': 4.0},
               'depth': [{'file': 'v__z.bmp'}]}
        cls.cam = os.path.join(d, 'see-v.json')
        json.dump(cam, open(cls.cam, 'w'))
        # a depth buffer: the far wall at 2000 everywhere; body A at x=400, y=0 drawn (its surface 8 nearer than its axis);
        # body B at x=600 y=0 is behind A (A's pixels hide it); body C at x=500, y=-150 is NOT drawn (wall depth there)
        z = np.full((H, W), 2000.0)
        cls.z = z
        frame = cls._frame_without_depth()
        for (bx, by, surf) in ((400.0, 0.0, 392.0),):
            for h in range(0, 75, 2):
                for dy in range(-14, 15, 2):
                    px, py, pz = frame.project(np.array([surf, by + dy, h], dtype=np.float64))
                    xi, yi = int(px), int(py)
                    for ox in (-1, 0, 1):
                        for oy in (-1, 0, 1):
                            if 0 <= xi + ox < W and 0 <= yi + oy < H:
                                z[yi + oy, xi + ox] = min(z[yi + oy, xi + ox], float(pz))
        S.write_float_bmp(os.path.join(d, 'v__z.bmp'), S.z_to_device(z, {'a': 0.0, 'b': 4.0}).astype(np.float32))
        cls.log = os.path.join(d, 'client.stdout.log')
        open(cls.log, 'w').write('\n'.join([
            '[IWZ local] GL CRPOS name=pre kind=crowd id=1 x=400 y=0 z=0 yaw=180',
            '[IWZ local] GL CRPOS name=pre kind=crowd id=2 x=600 y=0 z=0 yaw=180',
            '[IWZ local] GL CRPOS name=pre kind=crowd id=3 x=500 y=-150 z=0 yaw=180',
            '[IWZ local] GL CRPOS name=pre kind=agent id=40 x=-300 y=0 z=0 yaw=0',
            '[IWZ local] GL CRPOS name=post kind=crowd id=1 x=401 y=0 z=0 yaw=180',
        ]) + '\n')

    @classmethod
    def _frame_without_depth(cls):
        doc = json.load(open(cls.cam))
        doc['depth'] = []
        p = os.path.join(cls.tmp.name, 'see-nodepth.json')
        doc['name'] = 'nodepth'
        json.dump(doc, open(p, 'w'))
        return cls.S.Frame(p)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_states(self):
        frame = self.S.Frame(self.cam)
        pos = self.C.read_positions(open(self.log).read())
        r = self.C.judge([(frame, 'pre', 'post')], pos)
        state = {(b['kind'], b['id']): b['state'] for b in r['bodies']}
        self.assertEqual(state[('crowd', 1)], 'drawn')
        self.assertEqual(state[('crowd', 2)], 'occluded')
        self.assertEqual(state[('crowd', 3)], 'absent')
        self.assertEqual(state[('agent', 40)], 'outside')
        self.assertEqual(r['total'], {'listed': 4, 'drawn': 1, 'occluded': 1, 'absent': 1, 'outside': 1})

    def test_command_line(self):
        out = os.path.join(self.tmp.name, 'v.bmp')
        code = self.C.main(['--log', self.log, '--view', out + ':pre:post', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(self.C.main(['--log', self.log, '--view', out + ':nosuchset']), 2)


if __name__ == '__main__':
    unittest.main()
