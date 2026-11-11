"""DXBC container: parse, rebuild, checksum (the D3D runtime refuses a shader whose stored checksum is wrong).

Container layout: 'DXBC', 16-byte checksum, u32 version (1), u32 total size, u32 chunk count, u32 chunk offsets[],
then chunks (4-char FourCC, u32 size, body). The checksum is MD5 over bytes [20:] with a non-standard final block:
the bit length is stored as the first u32 of the last block and (bits >> 2) | 1 as its last u32.
"""
import struct

_S = [7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 + [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4
_K = [int(abs(__import__('math').sin(i + 1)) * 2 ** 32) & 0xffffffff for i in range(64)]


def _rotl(x, c):
    return ((x << c) | (x >> (32 - c))) & 0xffffffff


def _md5_block(st, block):
    m = struct.unpack('<16I', block)
    a, b, c, d = st
    for i in range(64):
        if i < 16:
            f, g = (b & c) | (~b & d), i
        elif i < 32:
            f, g = (d & b) | (~d & c), (5 * i + 1) % 16
        elif i < 48:
            f, g = b ^ c ^ d, (3 * i + 5) % 16
        else:
            f, g = c ^ (b | (~d & 0xffffffff)), (7 * i) % 16
        f = (f + a + _K[i] + m[g]) & 0xffffffff
        a, d, c = d, c, b
        b = (b + _rotl(f, _S[i])) & 0xffffffff
    return [(x + y) & 0xffffffff for x, y in zip(st, (a, b, c, d))]


def checksum(raw):
    """16-byte DXBC checksum of a whole container (the stored checksum field is not part of the input)"""
    data = bytes(raw[20:])
    n = len(data)
    bits = n * 8
    st = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]
    full = n // 64
    for i in range(full):
        st = _md5_block(st, data[i * 64:(i + 1) * 64])
    last = data[full * 64:]
    pad = b'\x80' + b'\0' * 63
    if len(last) >= 56:
        st = _md5_block(st, last + pad[:64 - len(last)])
        st = _md5_block(st, struct.pack('<I', bits) + b'\0' * 56 + struct.pack('<I', (bits >> 2) | 1))
    else:
        blk = struct.pack('<I', bits) + last + pad[:64 - 8 - len(last)] + struct.pack('<I', (bits >> 2) | 1)
        st = _md5_block(st, blk)
    return struct.pack('<4I', *st)


class Container:
    def __init__(self, raw, version, chunks):
        self.raw = raw
        self.version = version
        self.chunks = chunks  # list of [fourcc str, bytes body]

    @property
    def stored_checksum(self):
        return self.raw[4:20]

    @classmethod
    def parse(cls, raw):
        raw = bytes(raw)
        if raw[:4] != b'DXBC':
            raise ValueError('not a DXBC container')
        version, total, count = struct.unpack_from('<3I', raw, 20)
        if total != len(raw):
            raise ValueError('size field %d != file %d' % (total, len(raw)))
        offs = struct.unpack_from('<%dI' % count, raw, 32)
        chunks = []
        for o in offs:
            fourcc = raw[o:o + 4].decode('latin-1')
            size = struct.unpack_from('<I', raw, o + 4)[0]
            chunks.append([fourcc, raw[o + 8:o + 8 + size]])
        return cls(raw, version, chunks)

    def chunk(self, fourcc):
        for c in self.chunks:
            if c[0] == fourcc:
                return c[1]
        return None

    def set_chunk(self, fourcc, body):
        for c in self.chunks:
            if c[0] == fourcc:
                c[1] = bytes(body)
                return
        raise KeyError(fourcc)

    def build(self):
        """serialise the chunks in their original order and write a fresh checksum"""
        head = 32 + 4 * len(self.chunks)
        offs, body, pos = [], b'', head
        for fourcc, data in self.chunks:
            offs.append(pos)
            piece = fourcc.encode('latin-1') + struct.pack('<I', len(data)) + data
            body += piece
            pos += len(piece)
        out = bytearray(b'DXBC' + b'\0' * 16 + struct.pack('<3I', self.version, pos, len(self.chunks))
                        + struct.pack('<%dI' % len(offs), *offs) + body)
        out[4:20] = checksum(out)
        self.raw = bytes(out)
        return self.raw
