"""Reverse the winding of every render triangle of a world.bin for the engine (indices only).

    python -I iwz_wind.py <folder>          rewrites <folder>/world.bin in place; prints one line

The emit contract (docs/IWZ-EMIT-CONTRACT.md) is counter clockwise seen from the front, the vertex normal agreeing with the
cross product; the baker, the checks and the previews read it that way. The engine's front is clockwise (shipped geometry has its
stored normal opposing the cross product) and the map compiler copies the indices as they are, so an emit compiled unchanged shows
the far side of every solid: a room looks closed, but each wall and floor is the inside of its back face, lit as a face turned
away, and a thin sheet shows from behind only. Measured in the game on 22 Nov 2026 (iw7-studio port/README.md).

The build scripts call this on their private copy of the emit, after the bake and right before the compile. The emit itself
stays in the contract. A folder that holds the marker `world.bin.cw` was reversed already (by this file or by a caller's own step)
and is left alone, so the step is safe to repeat.
"""
import os
import struct
import sys

MAGIC = 0x575A5749
VSIZE = 44
MARK = 'world.bin.cw'


def reverse(folder):
    p = os.path.join(folder, 'world.bin')
    mark = os.path.join(folder, MARK)
    if os.path.isfile(mark):
        return {'reversed': 0, 'already': True}
    b = bytearray(open(p, 'rb').read())
    magic, ver = struct.unpack_from('<II', b, 0)
    if magic != MAGIC or ver != 1:
        raise ValueError('%s: not a world.bin' % p)
    o = 8
    nm, = struct.unpack_from('<I', b, o); o += 4
    for _ in range(nm):
        ln, = struct.unpack_from('<H', b, o); o += 2 + ln
    nv, = struct.unpack_from('<I', b, o); o += 4 + VSIZE * nv
    ni, = struct.unpack_from('<I', b, o); o += 4
    idx = o
    o += 2 * ni
    ns, = struct.unpack_from('<I', b, o); o += 4
    n = 0
    for s in range(ns):
        _mat, _fv, _vc, fi, tc = struct.unpack_from('<5I', b, o + s * (20 + 24))
        if fi + 3 * tc > ni:
            raise ValueError('%s: surface %d runs past the index list' % (p, s))
        for t in range(tc):
            a = idx + 2 * (fi + 3 * t + 1)
            b[a:a + 2], b[a + 2:a + 4] = b[a + 2:a + 4], b[a:a + 2]
            n += 1
    tmp = p + '.tmp'
    open(tmp, 'wb').write(b)
    os.replace(tmp, p)
    open(mark, 'w').write('indices reversed for the engine by iwz_wind.py\n')
    return {'reversed': n, 'already': False}


if __name__ == '__main__':
    r = reverse(sys.argv[1])
    print('iwz_wind: %s' % ('already reversed, left alone' if r['already'] else '%d triangles reversed for the engine' % r['reversed']))
