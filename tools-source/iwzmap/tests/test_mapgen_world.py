"""mapgen.write_world: world.bin version 1 is unchanged byte for byte; version 2 (per-surface layer stream, docs/station-zero/redesign/BLEND-LAYERS.md 4.1)."""
import hashlib
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import iwz_wind  # noqa: E402
import mapgen  # noqa: E402

# sha256 of the world.bin the writer of 27 Nov 2026 (before layers) wrote for plain_mesh(); version 1 must stay identical
V1_SHA = '00a33e5e0e6fae57c4d9289814bb54338e6c0bbef6694a7cece6816385736b7a'
V1_SIZE = 717


def plain_mesh():
    m = mapgen.Mesh()
    m.quad('w/floor', (0, 0, 0), (128, 0, 0), (128, 128, 0), (0, 128, 0), (0, 0, 1), (1, 0, 0), (0.25, 0.5))
    m.quad('w/wall|a', (0, 0, 0), (0, 0, 64), (128, 0, 64), (128, 0, 0), (0, -1, 0), (1, 0, 0), (0.5, 0.5))
    m.quad_uv('w/floor', [(200, 0, 0), (300, 0, 0), (300, 100, 0), (200, 100, 0)], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, 1), (1, 0, 0), (0.1, 0.2))
    return m


def read_world(path):
    with open(path, 'rb') as f:
        return read_world_bytes(f.read())


def read_world_bytes(b):
    p = [0]

    def take(fmt):
        v = struct.unpack_from(fmt, b, p[0]); p[0] += struct.calcsize(fmt); return v
    magic, ver = take('<II')
    assert magic == 0x575A5749
    mats = []
    for _ in range(take('<I')[0]):
        n, = take('<H'); mats.append(b[p[0]:p[0] + n].decode()); p[0] += n
    nv, = take('<I'); vo = p[0]; p[0] += nv * 44
    verts = [struct.unpack_from('<3ff4B2f2fII', b, vo + 44 * i) for i in range(nv)]
    ni, = take('<I'); p[0] += ni * 2
    ns, = take('<I'); surfs = []
    for _ in range(ns):
        s = take('<5I6f')
        extra = take('<II') if ver == 2 else (0, 0)
        surfs.append(s + extra)
    blob = b''
    if ver == 2:
        n, = take('<I'); blob = b[p[0]:p[0] + n]; p[0] += n
    bounds = take('<6f')
    assert p[0] == len(b), (p[0], len(b))
    return ver, mats, verts, surfs, blob, bounds


def layered_mesh():
    """a layered wall (stride 28, every vertex its own 28 bytes), a layered floor (stride 12), a plain tile"""
    m = mapgen.Mesh()
    for name, stride, y in (('*622n_89_91_282n', 28, 0), ('*622n_274n', 12, 300)):
        verts, idx = m.mat(name)
        pts = [(0, y, 0), (128, y, 0), (128, y, 64), (0, y, 64)]
        for k, p in enumerate(pts):
            rec = bytes((k * 16 + j + stride) & 255 for j in range(stride))
            verts.append((p, 0.0, 0.0, (0.5, 0.5), 0, 0, (255, 10 * (k + 1), 20 * (k + 1), 30 * (k + 1)), rec))
        idx += [0, 1, 2, 0, 2, 3]
    m.quad('w/plain', (0, 0, 0), (128, 0, 0), (128, 128, 0), (0, 128, 0), (0, 0, 1), (1, 0, 0), (0.25, 0.5))
    return m


class WriteWorld(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'world.bin')

    def tearDown(self):
        self.tmp.cleanup()

    def test_version_1_is_byte_identical_without_layers(self):
        mapgen.write_world(plain_mesh(), self.path)
        data = open(self.path, 'rb').read()
        self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (V1_SHA, V1_SIZE))
        ver, mats, verts, surfs, blob, _ = read_world(self.path)
        self.assertEqual((ver, blob), (1, b''))
        self.assertTrue(all(v[4:8] == (255, 255, 255, 255) for v in verts))

    def test_explicit_colour_without_layers_stays_version_1(self):
        m = mapgen.Mesh()
        verts, idx = m.mat('w/x')
        for k, p in enumerate([(0, 0, 0), (10, 0, 0), (0, 10, 0)]):
            verts.append((p, 0.0, 0.0, (0.5, 0.5), 0, 0, (255, 0, 128, 255), None))
        idx += [0, 1, 2]
        mapgen.write_world(m, self.path)
        ver, _, v, _, _, _ = read_world(self.path)
        self.assertEqual(ver, 1)
        self.assertEqual([x[4:8] for x in v], [(255, 0, 128, 255)] * 3)

    def test_six_tuples_and_eight_tuples_mix_in_one_mesh(self):
        m = plain_mesh()
        mapgen.write_world(m, self.path)
        ref = open(self.path, 'rb').read()
        verts, _ = m.by_mat['w/floor']
        verts[:] = [v + ((255, 255, 255, 255), None) for v in verts]        # the same vertices written with explicit defaults
        mapgen.write_world(m, self.path)
        self.assertEqual(open(self.path, 'rb').read(), ref)

    def test_version_2_roundtrip(self):
        m = layered_mesh()
        nv, ni, ns, _ = mapgen.write_world(m, self.path)
        ver, mats, verts, surfs, blob, bounds = read_world(self.path)
        self.assertEqual(ver, 2)
        self.assertEqual((nv, ns), (len(verts), len(surfs)))
        by_mat = {mats[s[0]]: s for s in surfs}
        wall, floor, plain = by_mat['*622n_89_91_282n'], by_mat['*622n_274n'], by_mat['w/plain']
        self.assertEqual((wall[12], floor[12], plain[12]), (28, 12, 0))                 # strides
        self.assertEqual(wall[11] % 4, 0)
        self.assertEqual(floor[11] % 4, 0)
        self.assertEqual(plain[11], 0)
        self.assertEqual(len(blob), 4 * 28 + 4 * 12)
        # the record of vertex j of a surface is at offset + j * stride and equals what the vertex carried
        for s, stride, key in ((wall, 28, 28), (floor, 12, 12)):
            for j in range(4):
                want = bytes((j * 16 + i + key) & 255 for i in range(stride))
                self.assertEqual(blob[s[11] + j * stride:s[11] + (j + 1) * stride], want)
            self.assertEqual([v[4:8] for v in verts[s[1]:s[1] + s[2]]], [(255, 10 * (k + 1), 20 * (k + 1), 30 * (k + 1)) for k in range(4)])
        self.assertEqual(sorted(s[11] for s in (wall, floor)), [0, 112])
        self.assertTrue(all(v[4:8] == (255, 255, 255, 255) for v in verts[plain[1]:plain[1] + plain[2]]))
        self.assertEqual(len(bounds), 6)

    def test_surfaces_of_a_split_material_keep_their_own_records(self):
        # two surfaces of one material (more than 30,000 triangles) take consecutive aligned slices of the blob
        m = mapgen.Mesh()
        verts, idx = m.mat('*622n_274n')
        n = 30001                                                   # triangles of a strip: vertex i is (i, 0, 0)
        for i in range(n + 2):
            verts.append(((float(i), 0.0, 0.0), 0.0, 0.0, (0.5, 0.5), 0, 0, None, struct.pack('<3I', i, i + 1, i + 2)))
        for t in range(n):
            idx += [t, t + 1, t + 2]
        mapgen.write_world(m, self.path)
        ver, mats, _, surfs, blob, _ = read_world(self.path)
        self.assertEqual((ver, len(surfs)), (2, 2))
        self.assertEqual((surfs[0][2], surfs[1][2]), (30002, 3))
        self.assertEqual((surfs[0][11], surfs[1][11]), (0, 30002 * 12))
        self.assertEqual(len(blob), (30002 + 3) * 12)
        self.assertEqual(struct.unpack_from('<3I', blob, surfs[1][11]), (30000, 30001, 30002))

    def test_iwz_wind_reverses_a_version_2_world_and_leaves_the_layers_alone(self):
        mapgen.write_world(layered_mesh(), self.path)
        before = open(self.path, 'rb').read()
        r = iwz_wind.reverse(self.tmp.name)
        self.assertEqual((r['already'], r['reversed']), (False, 2 + 2 + 2))
        after = open(self.path, 'rb').read()
        self.assertEqual(len(after), len(before))
        ver, _, _, surfs, blob, _ = read_world(self.path)
        ver0, _, _, surfs0, blob0, _ = read_world_bytes(before)
        self.assertEqual((ver, surfs, blob), (ver0, surfs0, blob0))
        self.assertNotEqual(after, before)

    def test_mixed_or_unaligned_records_are_refused(self):
        m = mapgen.Mesh()
        verts, idx = m.mat('*622n_274n')
        for k, p in enumerate([(0, 0, 0), (10, 0, 0), (0, 10, 0)]):
            verts.append((p, 0.0, 0.0, (0.5, 0.5), 0, 0, None, bytes(12) if k else None))
        idx += [0, 1, 2]
        with self.assertRaises(ValueError):
            mapgen.write_world(m, self.path)
        m = mapgen.Mesh()
        verts, idx = m.mat('*622n_274n')
        for p in [(0, 0, 0), (10, 0, 0), (0, 10, 0)]:
            verts.append((p, 0.0, 0.0, (0.5, 0.5), 0, 0, None, bytes(10)))
        idx += [0, 1, 2]
        with self.assertRaises(ValueError):
            mapgen.write_world(m, self.path)


if __name__ == '__main__':
    unittest.main()
