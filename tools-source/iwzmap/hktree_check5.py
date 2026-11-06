import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hkpack import Packfile
C = 226.0
def dec(byte, mn, mx):
    s = mx - mn; lo, hi = byte >> 4, byte & 15
    return mn + lo * lo / C * s, mx - hi * hi / C * s
def walk4(nodes, i, mn, mx, out):
    x = nodes[i]; box = [dec(x[a], mn[a], mx[a]) for a in range(3)]
    cmn = [b[0] for b in box]; cmx = [b[1] for b in box]
    d = x[3]
    if d & 1:
        walk4(nodes, i + 1, cmn, cmx, out); walk4(nodes, i + (d & 0xFE), cmn, cmx, out)
    else: out.append((d >> 1, cmn, cmx))
def walk5(nodes, i, mn, mx, out, root=False):
    x = nodes[i]
    if root: cmn, cmx = mn, mx
    else:
        box = [dec(x[a], mn[a], mx[a]) for a in range(3)]; cmn = [b[0] for b in box]; cmx = [b[1] for b in box]
    data = (x[3] << 8) | x[4]
    if x[3] & 0x80:
        walk5(nodes, i + 1, cmn, cmx, out); walk5(nodes, i + 2 * (data & 0x7FFF), cmn, cmx, out)
    else: out.append((data, cmn, cmx))
pf = Packfile(open(sys.argv[1], 'rb').read()); b = pf.data_sec.body
d = [a for a, n, _ in pf.objects if n == 'hknpCompressedMeshShapeData'][0]
tp, tn, _ = pf.array(d + 0x10)
top = [b[tp + 5*i: tp + 5*i + 5] for i in range(tn)]
dmn = struct.unpack_from('<3f', b, d + 0x20); dmx = struct.unpack_from('<3f', b, d + 0x30)
leaves = []; walk5(top, 0, dmn, dmx, leaves, True)
sec_p, nsec, _ = pf.array(d + 0x50)
print('top nodes', tn, 'leaves', len(leaves), 'sections', nsec, 'leaf ids sorted ok', sorted(l[0] for l in leaves) == list(range(nsec)))
bad = 0
for sid, lmn, lmx in leaves:
    so = sec_p + 96 * sid
    smn = struct.unpack_from('<3f', b, so + 16); smx = struct.unpack_from('<3f', b, so + 32)
    if any(smn[a] < lmn[a] - 1e-3 or smx[a] > lmx[a] + 1e-3 for a in range(3)): bad += 1
print('section boxes outside top leaf', bad)
# section trees vs primitive vertex positions
from hkcm import decode_cm_data
sv_p, _, _ = pf.array(d + 0x90); svi_p, _, _ = pf.array(d + 0x70); prim_p, _, _ = pf.array(d + 0x60)
span = [dmx[k] - dmn[k] for k in range(3)]
def shared(i):
    v = struct.unpack_from('<Q', b, sv_p + 8 * i)[0]
    q = (v & 0x1FFFFF, (v >> 21) & 0x1FFFFF, (v >> 42) & 0x3FFFFF)
    return [dmn[k] + q[k] * span[k] / (0x1FFFFF if k < 2 else 0x3FFFFF) for k in range(3)]
badp = tot = 0
for sid in range(min(nsec, 400)):
    so = sec_p + 96 * sid
    np_, _ = struct.unpack_from('<qi', b, so)[0], 0
    nptr = pf.ptr.get(so); nn = struct.unpack_from('<i', b, so + 8)[0]
    smn = struct.unpack_from('<3f', b, so + 16); smx = struct.unpack_from('<3f', b, so + 32)
    nodes = [b[nptr + 4*i: nptr + 4*i + 4] for i in range(nn)] if nn else []
    out = []
    if nn: walk4(nodes, 0, smn, smx, out)
    shv, prims = struct.unpack_from('<II', b, so + 76); nsh = b[so + 89]
    page = b[so + 92]
    verts = [shared((page << 16) | struct.unpack_from('<H', b, svi_p + 2 * ((shv >> 8) + j))[0]) for j in range(nsh)]
    for pidx, lmn, lmx in out:
        idx = b[prim_p + 4 * ((prims >> 8) + pidx): prim_p + 4 * ((prims >> 8) + pidx) + 4]
        if len(set(idx[:3])) < 3 or max(idx) >= len(verts): continue
        for k in set(idx):
            if k >= len(verts): continue
            tot += 1
            v = verts[k]
            if any(v[a] < lmn[a] - 0.01 * (smx[a]-smn[a]) - 0.05 or v[a] > lmx[a] + 0.01 * (smx[a]-smn[a]) + 0.05 for a in range(3)): badp += 1
print('section vertex checks', tot, 'outside leaf', badp)
