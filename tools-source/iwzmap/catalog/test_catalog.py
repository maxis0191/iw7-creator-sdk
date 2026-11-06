"""Unit tests for the dump readers and catalog (synthetic dumps; run: python -I test_catalog.py)."""
import json
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ztdump  # noqa: E402
import iwzcat  # noqa: E402
import preview_analyze as pa  # noqa: E402


def arr(data, count=1):
    return bytes([8, 1]) + struct.pack('<I', count) + data


def none_arr():
    return bytes([8, 0])


def s(text, t=6):
    return bytes([t, 1]) + text.encode() + b'\0'


def none_s(t=7):
    return bytes([t, 0])


def raw_none():
    return bytes([10, 0])


def make_xmodel(name, mid, half, materials, lod_surfs):
    h = bytearray(ztdump.XMODEL_SIZE)
    struct.pack_into('<?BBBBB', h, 9, True, 0, len(lod_surfs), 0, 0, 0)
    struct.pack_into('<BBB', h, 20, 1, 1, 0)
    struct.pack_into('<HH', h, 24, 0, len(materials))
    struct.pack_into('<f', h, 28, 1.0)
    struct.pack_into('<if', h, 36, 1, 10.0)
    struct.pack_into('<3f3f', h, 44, *mid, *half)
    for i, _ in enumerate(lod_surfs):
        struct.pack_into('<fHH', h, 224 + i * 64, 100.0 * (i + 1), len(materials), 0)
    b = arr(bytes(h)) + s(name) + s('tag_origin')
    b += none_arr() * 4  # parent, angles, positions (no non-root bones), partClassification
    b += arr(bytes(32))  # baseMat
    b += none_arr() * 3  # reactive parts, tweaks, collSurfs
    b += arr(bytes(28))  # boneInfo
    b += none_arr()      # invHighMipRadius
    b += arr(bytes(8 * len(materials)), len(materials))
    first = {}
    entry = 6  # header, name, bone name, baseMat, boneInfo, materialHandles come first in the entry list
    for m in materials:
        if m in first:
            b += bytes([9]) + struct.pack('<II', first[m], 0)
        else:
            first[m] = entry
            entry += 1
            b += s(m, 7)
    for i in range(6):
        b += s(lod_surfs[i], 7) if i < len(lod_surfs) else none_s()
    b += none_s() + none_s()
    return b


def make_xsurfs(name, verts, tris):
    h = bytearray(ztdump.XSURFS_SIZE)
    struct.pack_into('<H', h, 16, 1)
    sf = bytearray(ztdump.XSURFACE_SIZE)
    struct.pack_into('<HHHBB', sf, 0, 0x100, len(verts), len(tris), 0, 0)
    vb = b''.join(struct.pack('<3f', *v) + bytes(20) for v in verts)
    tb = b''.join(struct.pack('<3H', *t) for t in tris)
    b = arr(bytes(h)) + s(name) + arr(bytes(sf)) + arr(vb, len(verts)) + arr(tb, len(tris)) + none_arr()
    b += raw_none() * 4
    b += arr(bytes(8 * len(verts)), len(verts))  # shProbe data1 for flag 0x100
    return b


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        os.makedirs(os.path.join(d, 'xmodel'))
        os.makedirs(os.path.join(d, 'xsurface'))
        os.makedirs(os.path.join(d, 'materials', 'mc'))
        verts = [(-10, -5, 0), (10, -5, 0), (10, 5, 30), (-10, 5, 30)]
        open(os.path.join(d, 'xmodel', 'subway_bench_01.xmb'), 'wb').write(
            make_xmodel('subway_bench_01', (0, 0, 15), (10, 5, 15), ['mc/mtl_bench', 'mc/mtl_bench'], ['bench_lod0']))
        open(os.path.join(d, 'xsurface', 'bench_lod0.xsb'), 'wb').write(make_xsurfs('bench_lod0', verts, [(0, 1, 2), (0, 2, 3)]))
        json.dump({'techniqueSet->name': 'mopw_l_sm_replace', 'textureTable': [{'image': 'bench_c', 'semantic': 2}]},
                  open(os.path.join(d, 'materials', 'mc', 'mtl_bench.json'), 'w'))
        self.dir = d

    def tearDown(self):
        self.tmp.cleanup()

    def test_xmodel_header_and_offsets(self):
        m = ztdump.read_xmodel(os.path.join(self.dir, 'xmodel', 'subway_bench_01.xmb'))
        self.assertEqual(m['name'], 'subway_bench_01')
        self.assertEqual(m['bounds'], {'mins': [-10, -5, 0], 'maxs': [10, 5, 30]})
        self.assertEqual(m['materials'], ['mc/mtl_bench'])  # second handle is an OFFSET token
        self.assertEqual(m['lods'][0]['surfs'], 'bench_lod0')

    def test_xsurfs_counts_and_vertex_bounds(self):
        x = ztdump.read_xsurfs(os.path.join(self.dir, 'xsurface', 'bench_lod0.xsb'))
        self.assertEqual((x['verts'], x['tris']), (4, 2))
        self.assertEqual(x['vertBounds'], {'mins': [-10, -5, 0], 'maxs': [10, 5, 30]})

    def test_catalog_row(self):
        out = os.path.join(self.dir, 'cat.json')
        iwzcat.main(['build', '--zone', 'cp_test=' + self.dir, '--out', out])
        c = json.load(open(out))
        r = c['models'][0]
        self.assertEqual(r['category'], 'bench')
        self.assertEqual(r['boundsMaxDiff'], 0)
        self.assertEqual(r['lods'][0]['tris'], 2)
        self.assertEqual(r['materials'][0]['techset'], 'mopw_l_sm_replace')
        self.assertEqual(r['images'], ['bench_c'])
        self.assertEqual(r['cost']['missingImages'], ['bench_c'])

    def test_categories(self):
        for n, c in [('cp_disco_subway_car_doors_01', 'train'), ('cp_disco_subway_turnstyle_arm', 'turnstile'),
                     ('pipe_metal_painted_straight_128', 'pipe'), ('com_trashcan_metal', 'trash'),
                     ('vfx_debris_paper_torn_a_08', 'vfx_model'), ('light_interior_ceiling_living_room_01_on', 'light')]:
            self.assertEqual(iwzcat.guess_category(n), c, n)


class ProjectionTests(unittest.TestCase):
    def test_centre_projects_to_centre(self):
        p = pa.projector((0, 0, 0), (0, 0, 0), 1280, 720, 65, 1, 1.0)
        x, y = p((100, 0, 0))
        self.assertAlmostEqual(x, 640)
        self.assertAlmostEqual(y, 360)
        x, y = p((100, -10, 10))  # right and up
        self.assertGreater(x, 640)
        self.assertLess(y, 360)

    def test_yaw_rotation(self):
        v = pa.rot_angles((1, 0, 0), (0, 90, 0))
        self.assertAlmostEqual(v[0], 0, places=6)
        self.assertAlmostEqual(v[1], 1, places=6)


if __name__ == '__main__':
    unittest.main()
