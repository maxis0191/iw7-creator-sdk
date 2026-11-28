"""lmbake carries world.bin version 2 (layer records, vertex colours) through read -> split_shared_vertices -> write.
A split only copies an existing vertex of the same surface: colour and layer record (any stride, uv floats and rotation bytes alike) are copied byte for byte."""
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy as np
    import synth_world as SW
    import lmbake
except ImportError as e:
    raise unittest.SkipTest('bake environment missing: %s' % e)


def chart(surface, tris, vs, s0, r0):
    e = np.array
    return {'surface': surface, 'tris': tris, 'verts': vs, 'n': e([0, 0, 1.]), 't': e([1., 0, 0]), 'b': e([0, 1., 0]), 'd': 0.0,
            'sn': e([0, 0, 1.]), 'st': e([1., 0, 0]), 'sb': e([0, 1., 0]), 's0': s0, 'r0': r0, 'ns': 8, 'nr': 8, 'ts': 8.0, 'tr': 8.0, 'mat': 0}


def world_bytes(v2=True):
    """3 surfaces of 5 vertices (two triangles sharing vertex 0): strides 28, 36 and a plain one"""
    P = [(0, 0, 0), (64, 0, 0), (0, 64, 0), (0, -64, 0), (-64, 0, 0)]
    verts = np.zeros(15, lmbake.VD)
    for i in range(15):
        verts['pos'][i] = P[i % 5]; verts['n'][i] = SW.pack_unit((0, 0, 1)); verts['t'][i] = SW.pack_unit((1, 0, 0))
        verts['col'][i] = (255, i * 10, 255 - i, i)
    surfs = np.zeros(3, lmbake.SD)
    for k in range(3):
        surfs['mat'][k] = k; surfs['first'][k] = 5 * k; surfs['vc'][k] = 5; surfs['base'][k] = 6 * k; surfs['tc'][k] = 2
    idx = np.array([0, 1, 2, 0, 3, 4] * 3, '<u2')
    strides = [28, 36, 0]
    blob, offs = bytearray(), []
    for k, st in enumerate(strides):
        offs.append(len(blob))
        blob += bytes((k * 50 + i * 7 + j) & 255 for i in range(5) for j in range(st))
    w = {'materials': ['*a', '*b', 'w/plain'], 'verts': verts, 'indices': idx, 'surfaces': surfs, 'bounds': (-64., -64., 0., 64., 64., 0.),
         'ver': 2 if v2 else 1, 'layer': bytes(blob), 'layer_off': np.array(offs, '<u4'), 'layer_stride': np.array(strides, '<u4')}
    return w


class V2(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.p = os.path.join(self.d.name, 'world.bin')

    def tearDown(self):
        self.d.cleanup()

    def test_roundtrip_is_byte_identical_for_both_versions(self):
        for v2 in (False, True):
            lmbake.write_world(world_bytes(v2), self.p)
            a = open(self.p, 'rb').read()
            self.assertEqual(struct.unpack_from('<II', a)[1], 2 if v2 else 1)
            lmbake.write_world(lmbake.read_world(self.p), self.p)
            self.assertEqual(open(self.p, 'rb').read(), a)

    def test_split_copies_colour_and_layer_records(self):
        lmbake.write_world(world_bytes(), self.p)
        w = lmbake.read_world(self.p)
        old_v, old_blob = w['verts'].copy(), w['layer']
        old_off, old_st = w['layer_off'].copy(), w['layer_stride'].copy()
        charts = []
        for k in range(3):
            f = 5 * k
            charts.append(chart(k, [(f, f + 1, f + 2)], [f, f + 1, f + 2], 0, 0))
            charts.append(chart(k, [(f, f + 3, f + 4)], [f, f + 3, f + 4], -64, -64))
        sp = lmbake.split_shared_vertices(w, charts)
        self.assertEqual((sp['added'], sp['surfaces_split']), (3, 3))
        lmbake.write_world(w, self.p)
        r = lmbake.read_world(self.p)
        self.assertEqual(r['ver'], 2)
        self.assertEqual(list(r['layer_stride']), [28, 36, 0])
        self.assertEqual(len(r['layer']), 6 * 28 + 6 * 36)
        for k in range(3):
            s = r['surfaces'][k]
            f, vc = int(s['first']), int(s['vc'])
            self.assertEqual(vc, 6)
            # original vertices: colour and records unchanged; the new vertex (last of the range) equals vertex 0 of its surface
            for j in range(6):
                src = j if j < 5 else 0
                self.assertEqual(r['verts']['col'][f + j].tolist(), old_v['col'][5 * k + src].tolist())
                st = int(old_st[k])
                if st:
                    o, oo = int(r['layer_off'][k]), int(old_off[k])
                    self.assertEqual(r['layer'][o + j * st:o + (j + 1) * st], old_blob[oo + src * st:oo + (src + 1) * st])
            self.assertEqual(int(r['layer_off'][k]) % 4, 0)
        self.assertEqual((int(r['layer_off'][0]), int(r['layer_off'][1]), int(r['layer_off'][2])), (0, 6 * 28, 0))      # re-laid out; the plain surface has none


if __name__ == '__main__':
    unittest.main()
