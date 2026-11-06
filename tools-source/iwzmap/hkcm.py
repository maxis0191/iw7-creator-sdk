"""Decode hknpCompressedMeshShape(Data) from an IW7 packfile into triangles."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hkpack import Packfile

def arr(pf, o, item):
    p, n, cap = pf.array(o)
    return p, n

def decode_cm_data(pf, d):
    b = pf.data_sec.body
    dom_min = struct.unpack_from('<3f', b, d + 0x20)
    dom_max = struct.unpack_from('<3f', b, d + 0x30)
    nkeys, bits, maxkey = struct.unpack_from('<iiI', b, d + 0x40)
    sec_p, nsec = arr(pf, d + 0x50, 96)
    prim_p, nprim = arr(pf, d + 0x60, 4)
    svi_p, nsvi = arr(pf, d + 0x70, 2)
    pv_p, npv = arr(pf, d + 0x80, 4)
    sv_p, nsv = arr(pf, d + 0x90, 8)
    dr_p, ndr = arr(pf, d + 0xA0, 8)
    span = [dom_max[i] - dom_min[i] for i in range(3)]
    def shared(i):
        v = struct.unpack_from('<Q', b, sv_p + 8 * i)[0]
        q = (v & 0x1FFFFF, (v >> 21) & 0x1FFFFF, (v >> 42) & 0x3FFFFF)
        return tuple(dom_min[k] + q[k] * span[k] / (0x1FFFFF if k < 2 else 0x3FFFFF) for k in range(3))
    tris = []; tags = []; skipped = []
    for s in range(nsec):
        so = sec_p + 96 * s
        par = struct.unpack_from('<6f', b, so + 48)
        first_pv, shv, prims, runs = struct.unpack_from('<4I', b, so + 72)
        npack, nshared = b[so + 88], b[so + 89]
        verts = []
        for i in range(npack):
            v = struct.unpack_from('<I', b, pv_p + 4 * (first_pv + i))[0]
            q = (v & 0x7FF, (v >> 11) & 0x7FF, (v >> 22) & 0x3FF)
            verts.append(tuple(par[k] + q[k] * par[3 + k] for k in range(3)))
        sh_off, sh_n = shv >> 8, nshared
        for j in range(sh_n):
            idx = (b[so + 92] << 16) | struct.unpack_from("<H", b, svi_p + 2 * (sh_off + j))[0]
            verts.append(shared(idx))
        p_off, p_n = prims >> 8, prims & 0xFF
        r_off, r_n = runs >> 8, runs & 0xFF
        ptag = [0] * p_n
        for r in range(r_n):
            val, idx, cnt = struct.unpack_from('<HBB', b, dr_p + 4 * (r_off + r))
            for k in range(idx, idx + cnt):
                if k < p_n: ptag[k] = val
        for p in range(p_n):
            a, c, e, f = b[prim_p + 4 * (p_off + p): prim_p + 4 * (p_off + p) + 4]
            if max(a, c, e, f) >= len(verts) or a == c:
                skipped.append((a, c, e, f)); continue
            tris.append((verts[a], verts[c], verts[e])); tags.append(ptag[p])
            if e != f:
                tris.append((verts[a], verts[e], verts[f])); tags.append(ptag[p])
    return dict(domain=(dom_min, dom_max), nkeys=nkeys, bits=bits, maxkey=maxkey, nsec=nsec, nprim=nprim,
                npacked=npv, nshared=nsv, nruns=ndr, tris=tris, tags=tags, skipped=len(skipped))

if __name__ == '__main__':
    pf = Packfile(open(sys.argv[1], 'rb').read())
    from collections import Counter
    for a, n, sz in pf.objects:
        if n == 'hknpCompressedMeshShapeData':
            r = decode_cm_data(pf, a)
            print({k: v for k, v in r.items() if k not in ('tris', 'tags')}, 'tris', len(r['tris']))
            print('tags', Counter(r['tags']).most_common(12))
            if len(sys.argv) > 2:
                with open(sys.argv[2], 'w') as f:
                    for t in r['tris']:
                        for v in t: f.write('v %.2f %.2f %.2f\n' % v)
                    for i in range(len(r['tris'])): f.write('f %d %d %d\n' % (3*i+1, 3*i+2, 3*i+3))
            break
