"""Tests for dxbc.py and shader_read.py on stock IW7 shaders (python -m unittest test_shader_read).

Needs the stock techsets dump (IWZ_TECHSETS_DUMP, default the reference copy's techsets_global_cp dump); the tests
that need it are skipped when it is absent. The D3D11 checks use a WARP (software) device: no game, no GPU."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxbc  # noqa: E402
import shader_read  # noqa: E402
from shader_read import _read  # noqa: E402

DUMP = os.environ.get('IWZ_TECHSETS_DUMP',
                      r'C:\Users\ezvalo\Documents\IW7-Runtime\iwz-map-ref-a\dump\techsets_global_cp\techsets')
CAMO_PS = '6ff80a5207557f38'        # pixel shader of the 2-UV weapon lit technique (weapon_1887_camo)
CAMO_VS = 'eaaca8ffa5a53c35'
TECH = 'lprobe_specenv_g0[0]_ng0[0]_c0_r0_n0_s0_om0_p0_pa0_part0_g1[1]_ng1[1]_c1_b1_n1_s1_om1_e1_na1_evc1_sm_' \
       '.f09012b27e31092f.tech.technique'
CBT = os.path.join('constantbuffer', 'm2o_l_sm_replace_i0c0s0o0n0pa0_b1c1s1o1na1ec1_svp_2uvt_bafsp_scred_vm', 'm2o',
                   'weapon_1887_camo.cbt')


def cso(stage, h):
    return _read(os.path.join(DUMP, stage, h + '.cso'))


class ChecksumWithoutDump(unittest.TestCase):
    def test_tiny_container_round_trip(self):
        c = dxbc.Container(b'', 1, [['SHEX', b'\x50\x00\x05\x00' + b'\0' * 4], ['STAT', b'\0' * 60]])
        raw = c.build()
        again = dxbc.Container.parse(raw)
        self.assertEqual(again.stored_checksum, dxbc.checksum(raw))
        self.assertEqual(again.build(), raw)

    def test_checksum_covers_both_final_block_shapes(self):
        for n in (0, 1, 55, 56, 63, 64, 119, 120):      # tail < 56 and >= 56 bytes take different final blocks
            raw = b'DXBC' + b'\0' * 16 + b'\x01' * n
            self.assertEqual(len(dxbc.checksum(raw)), 16)
        self.assertNotEqual(dxbc.checksum(b'DXBC' + b'\0' * 16 + b'a'), dxbc.checksum(b'DXBC' + b'\0' * 16 + b'b'))


@unittest.skipUnless(os.path.isdir(DUMP), 'stock techsets dump not present')
class StockShaders(unittest.TestCase):
    def test_every_stock_shader_checksum_matches(self):
        n = 0
        for stage in ('vs', 'ps'):
            for f in sorted(os.listdir(os.path.join(DUMP, stage)))[:150]:
                raw = _read(os.path.join(DUMP, stage, f))
                self.assertEqual(dxbc.checksum(raw), raw[4:20], f)
                n += 1
        self.assertGreater(n, 100)

    def test_round_trip_is_byte_identical_and_accepted(self):
        for stage, h in (('ps', CAMO_PS), ('vs', CAMO_VS)):
            raw = cso(stage, h)
            c = dxbc.Container.parse(raw)
            self.assertEqual(c.build(), raw)
            self.assertTrue(shader_read.runtime_accepts(raw, stage))
            self.assertIn('%s_5_0' % stage, shader_read.disassemble(raw))

    def test_edited_shader_needs_the_new_checksum(self):
        raw = cso('ps', CAMO_PS)
        c = dxbc.Container.parse(raw)
        shex = bytearray(c.chunk('SHEX'))
        # the l(1.000000) literal of the first instruction (movc r0.x, v10.x, l(1.0), l(-1.0)) becomes 0.5
        at = shex.find(b'\x00\x00\x80\x3f')
        self.assertGreater(at, 0)
        shex[at:at + 4] = b'\x00\x00\x00\x3f'
        c.set_chunk('SHEX', shex)
        good = c.build()
        bad = bytearray(good); bad[4:20] = raw[4:20]    # same edit, stale checksum
        self.assertTrue(shader_read.runtime_accepts(good, 'ps'))
        self.assertFalse(shader_read.runtime_accepts(bytes(bad), 'ps'))
        self.assertIn('l(0.500000)', shader_read.disassemble(good).split('movc r0.x', 1)[1].split('\n', 1)[0])

    def test_technique_binding_table(self):
        t = shader_read.technique_refs(os.path.join(DUMP, TECH))
        self.assertEqual(t['shaders'], [CAMO_VS, CAMO_PS])
        consts = {(a['stage'], a['slot']): a['value'] for a in t['args'] if a['kind'] == 'material-constant'}
        self.assertEqual(consts[('vs', 0)], 4044143062)     # layer-1 UV scale.xy, scroll.zw
        self.assertEqual(consts[('vs', 1)], 28846999)       # layer-1 angle, angular speed, offset.zw
        texs = {a['value']: a['slot'] for a in t['args'] if a['kind'] == 'material-texture'}
        self.assertEqual([texs[h] for h in (3054311504, 2486480606, 3532022562, 3230247958, 1253113093)],
                         [5, 4, 6, 8, 7])                    # layer-1 _c _n _sg _e _o -> t5 t4 t6 t8 t7

    def test_cbt_literals(self):
        cb = shader_read.read_cbt(os.path.join(DUMP, CBT))
        self.assertEqual(cb[1]['vs'][0], [1.0, 1.0, 0.0, 0.0])
        self.assertEqual(cb[1]['vs'][2], [64.0, 64.0, 64.0, 64.0])
        self.assertEqual(cb[1]['ps'][2][0], 1000.0)          # emissivePara
        self.assertEqual(cb[1]['vsOffsets'], [16, 65535, 32, 65535, 48, 65535, 65535, 65535, 0])


if __name__ == '__main__':
    unittest.main()
