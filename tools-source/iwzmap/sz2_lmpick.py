"""Pick per-zone lightmap texels for Station Zero v2 from engine measurements.

usage: sz2_lmpick.py <gallery.json> <atlas npy dir (lightmap_read.py output)> <out lm table json>

1. Calibration: the texel gallery (IWZ_GALLERY=1 build, sz2_frames.py gallery.json) renders the same white tile
   under 132 texels. Its measured colour correlates with the decoded secondary lightmap's lower half
   (row = 2048 + v * 2048; r = 0.83 on the first gallery), so a power law render = k * atlas^g is fitted per
   channel group on those samples.
2. Search: every 4th texel of the atlas whose 5x5 neighbourhood is uniform is a candidate; its predicted render
   colour is compared with each zone's targets (white-tile luma for bright / mid / dark and a tint direction).
The table maps zone -> tone -> [u, v]; station_zero2.py reads it (IWZ_LM_TABLE or sz2_lm_table.json).
"""
import json, math, os, sys
import numpy as np

gal = json.load(open(sys.argv[1]))['texels']
atlas = np.load(os.path.join(sys.argv[2], '_lightmap0_secondary.npy')).astype(np.float64)
out = sys.argv[3]
low = atlas[2048:]                    # lower half: baked colour
H, W = low.shape[:2]


def at(u, v):
    y, x = min(H - 1, int(v * H)), min(W - 1, int(u * W))
    return low[max(0, y - 2):y + 3, max(0, x - 2):x + 3].reshape(-1, 3).mean(0)


# calibration: log(render) = log(k) + g * log(atlas + 1)
xs, ys = [], []
for key, rec in gal.items():
    if rec['std'] > 0.08:
        continue
    u, v = (float(c) for c in key.split(','))
    a = at(u, v)
    for c in range(3):
        if rec['rgb'][c] > 3:
            xs.append(math.log(a[c] + 1.0)); ys.append(math.log(rec['rgb'][c] / 255.0))
g, logk = np.polyfit(xs, ys, 1)
pred_err = float(np.sqrt(np.mean((np.polyval([g, logk], xs) - ys) ** 2)))
print('calibration: render = %.4f * (atlas + 1)^%.3f   (rms log error %.3f, %d samples)' % (math.exp(logk), g, pred_err, len(xs)))


def render(a):
    return np.clip(np.exp(logk) * np.power(a + 1.0, g), 0, 1)


# candidates: uniform 5x5 blocks
step = 4
blk = low[:H - H % step, :W - W % step]
cands = []
for y in range(2, H - 3, step):
    row = low[y - 2:y + 3]
    for x in range(2, W - 3, step):
        p = row[:, x - 2:x + 3].reshape(-1, 3)
        m = p.mean(0)
        if m.sum() < 3 or p.std(0).max() > 1.5:
            continue
        cands.append(((x + 0.5) / W, (y + 0.5) / H, m))
print('uniform candidates', len(cands))
C = np.array([c[2] for c in cands])
R = render(C)
Lum = R @ np.array([0.2126, 0.7152, 0.0722])
Chroma = R / np.maximum(R.mean(1, keepdims=True), 1e-4)

TARGETS = {   # zone: tint (r, g, b), white-tile luma (bright, mid, dark)
    'ticket_hall':    ((0.97, 1.0, 1.06), (0.80, 0.66, 0.40)),
    'stair_a':        ((0.97, 1.0, 1.06), (0.74, 0.60, 0.36)),
    'platform_a':     ((0.94, 1.0, 1.08), (0.78, 0.64, 0.40)),
    'maint_corridor': ((1.22, 1.0, 0.72), (0.70, 0.56, 0.32)),
    'generator_room': ((1.25, 1.0, 0.66), (0.74, 0.60, 0.36)),
    'control_room':   ((1.80, 0.70, 0.50), (0.60, 0.46, 0.26)),
    'service_tunnel': ((1.12, 1.0, 0.82), (0.62, 0.48, 0.28)),
    'platform_b':     ((1.08, 1.02, 0.88), (0.72, 0.58, 0.34)),
    'stair_b':        ((1.04, 1.0, 0.94), (0.72, 0.58, 0.34)),
    'gallery':        ((1.0, 1.0, 1.0), (0.7, 0.55, 0.3)),
}
table, report = {}, {}
for zone, (tint, lums) in TARGETS.items():
    t = np.array(tint) / np.mean(tint)
    table[zone], report[zone] = {}, {}
    for tone, lum in zip(('bright', 'mid', 'dark'), lums):
        cost = np.abs(Lum - lum) * 3.0 + np.linalg.norm(Chroma - t, axis=1)
        k = int(np.argmin(cost))
        u, v = cands[k][0], cands[k][1]
        table[zone][tone] = [round(u, 5), round(v, 5)]
        report[zone][tone] = {'uv': table[zone][tone], 'pred_luma': round(float(Lum[k]), 3), 'pred_rgb': [round(float(c) * 255) for c in R[k]]}
json.dump(table, open(out, 'w'), indent=1)
print(json.dumps(report, indent=1))
