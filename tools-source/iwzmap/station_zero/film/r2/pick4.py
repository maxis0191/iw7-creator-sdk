"""pick3: per sampled pixel: hit surface, interpolated lightmap uv, decoded A/B there, pixel value. Writes csv; prints black share by B level
usage: pick3.py <emit> <decoded dir> <png> <eye> <yaw> <pitch> <out csv> [step]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wb import read_world
from PIL import Image
emit, dec, png, eye = sys.argv[1], sys.argv[2], sys.argv[3], np.array([float(v) for v in sys.argv[4].split(',')])
yaw, pitch, outp = float(sys.argv[5]), float(sys.argv[6]), sys.argv[7]
step = int(sys.argv[8]) if len(sys.argv) > 8 else 8
img = np.asarray(Image.open(png).convert('RGB')).astype(int); H, W = img.shape[:2]
w = read_world(os.path.join(emit, 'world.bin')); V = w['verts']; S = w['surfaces']; I = w['indices']; p = V['pos'].astype(np.float64)
sec = np.load(os.path.join(dec, 'secondary.npy')); hs = sec.shape[0] // 2; LA = sec[:hs, :, :3]; LB = sec[hs:, :, :3]
tri, sid = [], []
for si, s in enumerate(S):
    t = I[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + s['first']; tri.append(t); sid.append(np.full(len(t), si))
tri = np.concatenate(tri); sid = np.concatenate(sid)
A, B, C = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
near = np.linalg.norm((A + B + C) / 3 - eye, axis=1) < 3500
tri, A, B, C, sid = tri[near], A[near], B[near], C[near], sid[near]
e1, e2 = B - A, C - A
y, pz = np.radians(yaw), np.radians(-pitch)
fwd = np.array([np.cos(pz) * np.cos(y), np.cos(pz) * np.sin(y), np.sin(pz)]); right = np.array([np.sin(y), -np.cos(y), 0.0]); up = np.cross(right, fwd)
tx = np.tan(np.radians(80.69) / 2); ty = tx * H / W
rows = []
for yy in range(step // 2, H, step):
    for xx in range(step // 2, W, step):
        u = (2 * (xx + 0.5) / W - 1) * tx; v = (1 - 2 * (yy + 0.5) / H) * ty
        d = fwd + u * right + v * up; d /= np.linalg.norm(d)
        pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        tv = eye - A; uu = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); vv = (qv @ d) * inv; tt = (qv * e2).sum(1) * inv
        m = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 1)
        if not m.any(): continue
        i = np.where(m)[0][np.argmin(tt[m])]
        a, b, c = tri[i]; bu, bv = uu[i], vv[i]
        lm = (1 - bu - bv) * V['lm'][a] + bu * V['lm'][b] + bv * V['lm'][c]
        px = min(LA.shape[1] - 1, max(0, int(lm[0] * LA.shape[1]))); py = min(LA.shape[0] - 1, max(0, int(lm[1] * LA.shape[0])))
        P = eye + d * tt[i]
        rows.append((xx, yy, int(sid[i]), w['materials'][S[sid[i]]['mat']], float(lm[0]), float(lm[1]), *LA[py, px].tolist(), *LB[py, px].tolist(), *img[yy, xx].tolist(), float(tt[i]), float(P[2]), float(P[0]), float(P[1])))
import csv
with open(outp, 'w', newline='') as f:
    wr = csv.writer(f); wr.writerow(['x', 'y', 'surf', 'mat', 'lmu', 'lmv', 'Ar', 'Ag', 'Ab', 'Br', 'Bg', 'Bb', 'R', 'G', 'Bpx', 't', 'z', 'wx', 'wy'])
    wr.writerows(rows)
R = np.array([r[6:15] for r in rows]); Al = R[:, :3].mean(1); Bl = R[:, 3:6].mean(1); blk = R[:, 6:9].max(1) <= 2
print('pixels', len(rows), 'black', blk.mean().round(3))
for lo, hi in ((0, 0.01), (0.01, 0.05), (0.05, 0.2), (0.2, 0.5), (0.5, 100)):
    m = (Bl >= lo) & (Bl < hi)
    print('B %.2f..%.2f: %5d px, black %.2f, A mean %.3f' % (lo, hi, m.sum(), blk[m].mean() if m.any() else 0, Al[m].mean() if m.any() else 0))
