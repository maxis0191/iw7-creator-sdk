"""for sampled pixels: all surfaces hit within 1 unit of the nearest hit (coplanar layers), black vs lit"""
import sys, os, csv, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wb import read_world
emit, csvp = sys.argv[1], sys.argv[2]; eye = np.array([float(v) for v in sys.argv[3].split(',')]); yaw, pitch = float(sys.argv[4]), float(sys.argv[5])
w = read_world(os.path.join(emit, 'world.bin')); V = w['verts']; S = w['surfaces']; I = w['indices']; p = V['pos'].astype(np.float64)
tri, sid = [], []
for si, s in enumerate(S):
    t = I[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + s['first']; tri.append(t); sid.append(np.full(len(t), si))
tri = np.concatenate(tri); sid = np.concatenate(sid)
A, B, C = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
near = np.linalg.norm((A + B + C) / 3 - eye, axis=1) < 3500
A, B, C, sid = A[near], B[near], C[near], sid[near]; e1, e2 = B - A, C - A
y, pz = np.radians(yaw), np.radians(-pitch)
fwd = np.array([np.cos(pz) * np.cos(y), np.cos(pz) * np.sin(y), np.sin(pz)]); right = np.array([np.sin(y), -np.cos(y), 0.0]); up = np.cross(right, fwd)
W, H = 1280, 720; tx = np.tan(np.radians(80.69) / 2); ty = tx * H / W
rows = list(csv.DictReader(open(csvp)))
rows = [r for r in rows if r['mat'] == 'w/concrete_bare_patches_clean_03']
rng = np.random.default_rng(1); rng.shuffle(rows)
from collections import Counter
cnt = {True: Counter(), False: Counter()}; n = {True: 0, False: 0}
for r in rows[:400]:
    xx, yy = int(r['x']), int(r['y']); blk = max(int(r['R']), int(r['G']), int(r['Bpx'])) <= 2
    u = (2 * (xx + 0.5) / W - 1) * tx; v = (1 - 2 * (yy + 0.5) / H) * ty
    d = fwd + u * right + v * up; d /= np.linalg.norm(d)
    pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = eye - A; uu = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); vv = (qv @ d) * inv; tt = (qv * e2).sum(1) * inv
    m = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 1)
    t0 = tt[m].min(); layer = sorted({w['materials'][S[sid[i]]['mat']] for i in np.where(m & (tt < t0 + 1.0))[0]})
    n[blk] += 1; cnt[blk][' + '.join(layer)] += 1
for b in (True, False):
    print('BLACK' if b else 'LIT', n[b])
    for k, c in cnt[b].most_common(8): print('   %4d  %s' % (c, k))
