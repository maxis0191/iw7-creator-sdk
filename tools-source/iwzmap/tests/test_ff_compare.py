"""ff_compare: synthetic zones (an IWC stream of LZ4 blocks) with pointer residue and with a content change."""
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import lz4.block  # noqa: F401
    HAVE_LZ4 = True
except ImportError:
    HAVE_LZ4 = False


def zone(payload):
    import lz4.block
    blocks = b''
    for i in range(0, len(payload), 0x10000):
        raw = payload[i:i + 0x10000]
        c = lz4.block.compress(raw, store_size=False)
        blocks += struct.pack('<III', len(c), len(raw), 0) + c + b'\0' * (((len(c) + 3) & ~3) - len(c))
    return b'IWffu100' + b'\0' * 32 + b'IWC' + struct.pack('<QI', len(payload), 0x04010000) + blocks


@unittest.skipUnless(HAVE_LZ4, 'needs the lz4 package')
class FfCompareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = bytearray(os.urandom(200000))
        struct.pack_into('<Q', base, 70001, 0x13244BA1C7)       # an unaligned leftover address
        self.base = bytes(base)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, payload):
        p = os.path.join(self.tmp.name, name)
        open(p, 'wb').write(zone(payload))
        return p

    def test_identical_and_residue_and_content(self):
        import ff_compare as fc
        a = self.write('a.ff', self.base)
        self.assertEqual(fc.compare(a, self.write('b.ff', self.base))['verdict'], 'identical')
        moved = bytearray(self.base); struct.pack_into('<Q', moved, 70001, 0x13244B71C7)
        r = fc.compare(a, self.write('c.ff', bytes(moved)))
        self.assertEqual((r['verdict'], r['content_bytes']), ('same_content', 0))
        changed = bytearray(self.base); changed[150000] ^= 0xFF
        r = fc.compare(a, self.write('d.ff', bytes(changed)))
        self.assertEqual((r['verdict'], r['content_bytes']), ('different', 1))


if __name__ == '__main__':
    unittest.main()
