"""Layered (`*`) surfaces in the pure part of the Blender exporter: vertex colour weights and per-vertex layer-stream records (blend_core.WorldBuilder.add, layer_record),
reproduction of a stock vertex of `*622n_89_91_282n`, world.bin version 2 out of the builder. No game, no dump."""
import json
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '..'))

import blend_core as C  # noqa: E402
import mapgen  # noqa: E402
from layerstream import extract_layouts as LS  # noqa: E402

FIXTURE = os.path.join(HERE, 'fixture_layer_622n_89_91_282n.json')     # 45 vertices of a stock surface of cp_disco: position, colour, normal, tangent, 28 byte layer record
MAT = '*622n_89_91_282n'
MAT36 = '*387n_86n_354n_362n'
MAT12 = '*622n_274n'


def unsupported_material():
    t = LS.load_table()
    for name, ts in sorted(t['materials']['cp_disco'].items()):
        if not t['techsets'][ts]['supported']:
            return name
    raise AssertionError('no unsupported material in the table')


def builder():
    return C.WorldBuilder(mapgen.Mesh(), (0.8, 0.5), {})


def quad_tris(x0, x1, y=0.0, z0=0.0, z1=64.0):
    """a wall in the xz plane facing -y (counter-clockwise seen from the front)"""
    a, b, c, d = (x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)
    return [[a, b, c], [a, c, d]]


class StockVertex(unittest.TestCase):
    def test_layer_record_reproduces_the_stock_vertices(self):
        fx = json.load(open(FIXTURE))
        lay = LS.material_layout(fx['material'], fx['zone'])
        self.assertEqual(lay['stride'], 28)
        diffs = []
        for v in fx['vertices']:
            ours = C.layer_record(lay, tuple(v['p']), tuple(v['n']))
            stock = bytes.fromhex(v['layer'])
            self.assertEqual(len(ours), len(stock))
            fo = struct.unpack('<6f', ours[:24])
            fs = struct.unpack('<6f', stock[:24])
            diffs.append([a - b for a, b in zip(fo, fs)])
            # rotation: one byte of difference at most (stock writes 126 or 127 for 0, 253 or 254 for +1)
            self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(ours[24:], stock[24:])), (ours[24:].hex(), stock[24:].hex()))
            self.assertEqual(v['col'][0], 255)
        # the planar rule reproduces uv up to the surface's own constant offset (stock: u = -y/128 + 21.186, v = -x/128 + 2.34375), the same for the three layers (scale 1).
        # Vertices 0..22 are one planar patch: the offset is the same for all. Vertices 23..44 are another patch of the chunk: the same u slope (offset differs by a whole tile)
        # and a MIRRORED v (the stock v runs +x there), which the single planar rule does not make: measured here, left to the in-game proof of BLEND-LAYERS.md section 5.
        a = diffs[:23]
        for k in range(6):
            col = [d[k] for d in a]
            self.assertLess(max(col) - min(col), 1e-3, k)
        for k in (0, 2, 4):
            self.assertLess(abs(a[0][k] - a[0][0]), 1e-3)
            self.assertLess(abs(((diffs[30][k] - a[0][k]) + 0.5) % 1.0 - 0.5), 2e-3)           # a whole number of tiles
        self.assertGreater(max(d[1] for d in diffs[23:]) - min(d[1] for d in diffs[23:]), 1.0)
        # with the patch's offset given, its records equal the stock records to 1e-3
        off = [(-a[0][0], -a[0][1])] * 3
        for v in fx['vertices'][:23]:
            ours = C.layer_record(lay, tuple(v['p']), tuple(v['n']), offsets=off)
            self.assertTrue(all(abs(x - y) < 1e-3 for x, y in zip(struct.unpack('<6f', ours[:24]), struct.unpack('<6f', bytes.fromhex(v['layer'])[:24]))))

    def test_other_strides_follow_the_table(self):
        for name, stride in ((MAT36, 36), (MAT12, 12)):
            lay = LS.material_layout(name, 'cp_disco')
            rec = C.layer_record(lay, (10.0, 20.0, 30.0), (0.0, -1.0, 0.0))
            self.assertEqual(len(rec), stride, name)
        # 36: three uv pairs then three rotations (TEXCOORD5, 6, 9)
        lay = LS.material_layout(MAT36, 'cp_disco')
        rec = C.layer_record(lay, (10.0, 20.0, 30.0), (0.0, 0.0, 1.0), scales=[1, 2, 2])
        f = struct.unpack('<6f', rec[:24])
        self.assertAlmostEqual(f[2], f[0] * 2, places=5)
        self.assertEqual(rec[24:28], rec[28:32])
        self.assertEqual(rec[28:32], rec[32:36])

    def test_tangent_mapping_is_the_identity_rotation(self):
        lay = LS.material_layout(MAT, 'cp_disco')
        rec = C.layer_record(lay, (128.0, 0.0, 0.0), (0.0, 0.0, 1.0), mapping='tangent')
        self.assertEqual(rec[24:], bytes([254, 127, 127, 254]))
        u, v = struct.unpack('<2f', rec[:8])
        self.assertAlmostEqual(u, 1.0, places=5)          # u = p . t / 128 with t = +x
        self.assertAlmostEqual(v, 0.0, places=5)

    def test_scales_are_required_per_layer(self):
        lay = LS.material_layout(MAT, 'cp_disco')
        with self.assertRaises(ValueError):
            C.layer_record(lay, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), scales=[1.0])


class Builder(unittest.TestCase):
    def test_weights_become_vertex_colour_and_records(self):
        wb = builder()
        wb.add({'name': 'w', 'material': MAT, 'tris': quad_tris(0, 128), 'blend': {'zone': 'cp_disco', 'weights': [lambda p, n: p[0] / 128.0, 0.5, 0.0], 'scales': [1, 1, 2]}})
        verts, idx = wb.mesh.by_mat['%s|w' % MAT]
        self.assertEqual((len(verts), len(idx), wb.layer_tris), (4, 6, 2))
        lay = LS.material_layout(MAT, 'cp_disco')
        by_x = {v[0][0]: v for v in verts}
        self.assertEqual(by_x[0.0][6], (255, 0, 128, 0))
        self.assertEqual(by_x[128.0][6], (255, 255, 128, 0))
        for v in verts:
            self.assertEqual(len(v[7]), lay['stride'])
            self.assertEqual(v[7], C.layer_record(lay, v[0], (0.0, -1.0, 0.0), [1, 1, 2]))

    def test_painted_vertices_do_not_weld_with_clean_ones(self):
        def run(weights):
            wb = builder()
            wb.add({'name': 'a', 'material': MAT, 'tris': quad_tris(0, 128), 'blend': {'zone': 'cp_disco', 'weights': weights[0]}})
            wb.add({'name': 'a', 'material': MAT, 'tris': quad_tris(128, 256), 'blend': {'zone': 'cp_disco', 'weights': weights[1]}})
            return len(wb.mesh.by_mat['%s|a' % MAT][0])
        self.assertEqual(run([[1.0], [1.0]]), 6)               # one weight: the shared edge welds (the layer records agree there)
        self.assertEqual(run([[1.0], [0.0]]), 8)               # two weights: the two shared corners split

    def test_table_weights_per_triangle_corner(self):
        wb = builder()
        table = [[0.0, 1.0, 1.0], [0.0, 1.0, 0.0]]
        wb.add({'name': 'w', 'material': MAT, 'tris': quad_tris(0, 128), 'blend': {'zone': 'cp_disco', 'weights': [table]}})
        verts, _ = wb.mesh.by_mat['%s|w' % MAT]
        self.assertEqual(len(verts), 4)                       # the two shared corners agree in both triangles: welded
        self.assertEqual(sorted(v[6][1] for v in verts), [0, 0, 255, 255])
        self.assertEqual({v[6][0] for v in verts}, {255})

    def test_explicit_cols_and_layers(self):
        wb = builder()
        tris = quad_tris(0, 128)[:1]
        cols = [[(255, 1, 2, 3), (255, 4, 5, 6), (255, 7, 8, 9)]]
        layers = [[bytes([k] * 12).hex() for k in (1, 2, 3)]]
        wb.add({'name': 'e', 'material': MAT12, 'tris': tris, 'cols': cols, 'layers': layers})
        verts, _ = wb.mesh.by_mat['%s|e' % MAT12]
        self.assertEqual([v[6] for v in verts], cols[0])
        self.assertEqual([v[7] for v in verts], [bytes([k] * 12) for k in (1, 2, 3)])
        with self.assertRaises(ValueError):
            builder().add({'name': 'e', 'material': MAT12, 'tris': tris, 'layers': [[b'\x00' * 10] * 3]})

    def test_plain_material_vertices_are_unchanged(self):
        wb = builder()
        wb.add({'name': 'p', 'material': 'w/concrete_tiles_01', 'tris': quad_tris(0, 128)})
        verts, _ = wb.mesh.by_mat['w/concrete_tiles_01|p']
        self.assertTrue(all(len(v) == 6 for v in verts))
        self.assertEqual(wb.layer_tris, 0)

    def test_unsupported_and_unknown_materials_are_refused(self):
        bad = unsupported_material()
        for name, text in ((bad, 'not decoded'), ('*no_such_material', 'not in the layer layout table')):
            with self.assertRaises(ValueError) as cm:
                builder().add({'name': 'x', 'material': name, 'tris': quad_tris(0, 128), 'blend': {'zone': 'cp_disco'}})
            self.assertIn(text, str(cm.exception))

    def test_validate_accepts_layered_materials_with_a_blend_and_names_the_refusals(self):
        def mesh(material, **kw):
            return dict({'name': 'm', 'material': material, 'tris': quad_tris(0, 128)}, **kw)
        base = {'map': 'cp_iwz', 'zones': [{'name': 'a', 'box': [0, 0, 0, 100, 100, 100]}]}
        errs = lambda m: [msg for sev, msg in C.validate(dict(base, meshes=[m])) if sev == 'ERROR' and 'mesh m' in msg]
        self.assertEqual(errs(mesh(MAT, blend={'zone': 'cp_disco'})), [])
        self.assertEqual(len(errs(mesh(MAT))), 1)                                         # a `*` material without a blend is still refused
        self.assertEqual(len(errs(mesh(unsupported_material(), blend={'zone': 'cp_disco'}))), 1)
        self.assertEqual(errs(mesh('w/concrete_tiles_01')), [])

    def test_world_bin_version_2_from_the_builder(self):
        wb = builder()
        wb.add({'name': 'wall', 'material': MAT, 'tris': quad_tris(0, 128), 'blend': {'zone': 'cp_disco', 'weights': [1.0, 0.0, 0.0]}})
        wb.add({'name': 'wall2', 'material': MAT36, 'tris': quad_tris(300, 428), 'blend': {'zone': 'cp_disco', 'weights': [0.5, 0.5, 0.5], 'scales': [1, 2, 2]}})
        wb.add({'name': 'plain', 'material': 'w/concrete_tiles_01', 'tris': quad_tris(600, 728)})
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'world.bin')
            mapgen.write_world(wb.mesh, p)
            b = open(p, 'rb').read()
        magic, ver = struct.unpack_from('<II', b, 0)
        self.assertEqual((magic, ver), (0x575A5749, 2))
        o = 8
        nm, = struct.unpack_from('<I', b, o); o += 4
        mats = []
        for _ in range(nm):
            n, = struct.unpack_from('<H', b, o); o += 2; mats.append(b[o:o + n].decode()); o += n
        nv, = struct.unpack_from('<I', b, o); o += 4 + 44 * nv
        ni, = struct.unpack_from('<I', b, o); o += 4 + 2 * ni
        ns, = struct.unpack_from('<I', b, o); o += 4
        surf = {}
        for k in range(ns):
            f = struct.unpack_from('<5I6fII', b, o + 52 * k)
            surf[mats[f[0]]] = f
        o += 52 * ns
        size, = struct.unpack_from('<I', b, o)
        self.assertEqual(size, 4 * 28 + 4 * 36)
        self.assertEqual((surf[MAT][12], surf[MAT36][12], surf['w/concrete_tiles_01'][12]), (28, 36, 0))
        self.assertEqual(surf[MAT][11] % 4, 0)
        self.assertEqual(surf[MAT36][11] % 4, 0)


if __name__ == '__main__':
    unittest.main()
