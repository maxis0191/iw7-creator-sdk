"""pick2: every Nth pixel of a frame ray-picked into world.bin; per surface: pixels, share black, material, size.
usage: pick2.py <world.bin> <frame png> <eye x,y,z> <yaw> <pitch> [hfov] [step]"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wb import read_world
from PIL import Image
wbp, png, eye = sys.argv[1], sys.argv[2], np.array([float(v) for v in sys.argv[3].split(',')])
yaw, pitch = float(sys.argv[4]), float(sys.argv[5])
hfov = float(sys.argv[6]) if len(sys.argv) > 6 else 80.69
step = int(sys.argv[7]) if len(sys.argv) > 7 else 12
img = np.asarray(Image.open(png).convert('RGB')).astype(int); H, W = img.shape[:2]
w = read_world(wbp); V = w['verts']; S = w['surfaces']; I = w['indices']; p = V['pos'].astype(np.float64)
tri, sid = [], []
for si, s in enumerate(S):
    t = I[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + s['first']; tri.append(t); sid.append(np.full(len(t), si))
tri = np.concatenate(tri); sid = np.concatenate(sid)
A, B, C = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
near = np.linalg.norm((A + B + C) / 3 - eye, axis=1) < 3500
A, B, C, sid = A[near], B[near], C[near], sid[near]
e1, e2 = B - A, C - A
y, pz = np.radians(yaw), np.radians(-pitch)
fwd = np.array([np.cos(pz) * np.cos(y), np.cos(pz) * np.sin(y), np.sin(pz)])
right = np.array([np.sin(y), -np.cos(y), 0.0]); up = np.cross(right, fwd)
tx = np.tan(np.radians(hfov) / 2); ty = tx * H / W
stat = {}
for yy in range(step // 2, H, step):
    for xx in range(step // 2, W, step):
        u = (2 * (xx + 0.5) / W - 1) * tx; v = (1 - 2 * (yy + 0.5) / H) * ty
        d = fwd + u * right + v * up; d /= np.linalg.norm(d)
        pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        tv = eye - A; uu = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); vv = (qv @ d) * inv; tt = (qv * e2).sum(1) * inv
        m = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 1)
        si = int(sid[np.where(m)[0][np.argmin(tt[m])]]) if m.any() else -1
        b = img[yy, xx].max() <= 2
        st = stat.setdefault(si, [0, 0]); st[0] += 1; st[1] += b
rows = []
for si, (n, nb) in stat.items():
    if si < 0:
        rows.append({'surf': -1, 'mat': '(nothing)', 'px': n, 'black': nb}); continue
    s = S[si]; ext = (s['mx'] - s['mn']).tolist()
    rows.append({'surf': si, 'mat': w['materials'][s['mat']], 'px': n, 'black': nb, 'tc': int(s['tc']), 'vc': int(s['vc']), 'ext': [round(e) for e in ext]})
rows.sort(key=lambda r: -r['px'])
for r in rows[:45]:
    print('%5d px %5.0f%% black  surf %5d  tc %4s  ext %-18s %s' % (r['px'], 100 * r['black'] / r['px'], r['surf'], r.get('tc', ''), r.get('ext', ''), r['mat']))
json.dump(rows, open(os.path.basename(os.path.splitext(png)[0]) + '_pick2.json', 'w'), indent=0)
