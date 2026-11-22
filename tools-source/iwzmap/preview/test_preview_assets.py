"""Offline checks of the preview's asset readers (no Blender, no game files needed)."""
import os
import struct
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iwz_assets as A  # noqa: E402
import iwz_calib as C  # noqa: E402


def lz4_literals(data):
    """An LZ4 block holding only literals (valid: the last sequence has no match)."""
    n = len(data)
    out = bytearray()
    if n < 15:
        out.append(n << 4)
    else:
        out.append(0xF0)
        r = n - 15
        while r >= 255:
            out.append(255)
            r -= 255
        out.append(r)
    return bytes(out) + data


class AssetTests(unittest.TestCase):
    def test_lz4_with_match(self):
        # literals 'abcd', then a match of offset 4 length 8 (token 0x44 + minmatch), then the final literals 'x'
        blk = bytes([0x44]) + b'abcd' + struct.pack('<H', 4) + bytes([0x10]) + b'x'
        self.assertEqual(A.lz4_block(blk, 13), b'abcd' + b'abcdabcd' + b'x')

    def test_iwc_two_blocks_aligned_to_4(self):
        a, b = bytes(range(50)), bytes(range(60, 100))
        hdr = b'\x02IWC' + struct.pack('<QI', len(a) + len(b), (0x10000) | (4 << 24))
        body = b''
        for part in (a, b):
            blk = lz4_literals(part)
            body += struct.pack('<IQ', len(blk), len(part)) + blk
            body += b'\0' * (-len(blk) % 4)
        self.assertEqual(A.iwc_unpack(hdr + body), a + b)

    def test_mip_bytes(self):
        self.assertEqual(A.mip_bytes(98, 512, 512), 262144)        # BC7
        self.assertEqual(A.mip_bytes(71, 128, 128), 8192)          # BC1

    def test_unpack_uv_half(self):
        tc = np.array([[0x3C00, 0x3800]], np.uint16)               # 1.0, 0.5
        self.assertEqual(A.unpack_uv(tc).tolist(), [[1.0, 0.5]])

    def test_metrics_identical_images(self):
        rng = np.random.default_rng(1)
        img = np.clip(rng.random((720, 1280, 3)) * 0.5, 0, 1).astype(np.float32)
        m = C.mask_1280x720()
        self.assertAlmostEqual(C.edge_score(img, C.srgb_to_lin(img), m), 1.0, places=3)


if __name__ == '__main__':
    unittest.main()
