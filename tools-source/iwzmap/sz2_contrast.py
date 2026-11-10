"""Surface-family contrast on the capture frames (lead g24 review: floor, walls and ceiling read as one ochre tone).

usage: sz2_contrast.py <views run dir> <src dir (layout.json, surfaces.json)> <out.json> [--min 0.05] [--hfov 80.7]

For every zone view (iwzv_<zone>_<n>.bmp) the zone's render quads (surfaces.json) are projected with the capture camera
(eye 60 above the view origin, as sz2_propcheck / kit_proof), clipped at the near plane and painted far to near into a
label image by family: floor (normal up), ceiling (normal down), lower wall (top below floor + 110), upper wall (the
rest of the vertical quads). Per zone, the mean sRGB luma of each family over its views is compared for the adjacent
pairs floor / lower wall, lower wall / upper wall, upper wall / ceiling: each pair must differ by >= --min (luma) or by
>= 20 degrees of hue. Decor models are not in surfaces.json (they paint over nothing: their pixels count for the
quad behind them, an accepted approximation).
"""
import argparse, colorsys, json, math, os
import numpy as np
from PIL import Image, ImageDraw

EYE = 60.0
FAM = {1: 'floor', 2: 'wall_low', 3: 'wall_up', 4: 'ceiling'}
PAIRS = [('floor', 'wall_low'), ('wall_low', 'wall_up'), ('wall_up', 'ceiling')]


def cam_basis(yaw, pitch):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = np.array([math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr)])
    r = np.array([math.sin(yr), -math.cos(yr), 0.0])
    u = np.cross(r, f)
    return f, r, u


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--min', type=float, default=0.05); ap.add_argument('--hfov', type=float, default=80.7)
    a = ap.parse_args()
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    quads = json.load(open(os.path.join(a.src, 'surfaces.json')))['quads']
    by_zone = {}
    for z, mat, pts, n in quads:
        by_zone.setdefault(z, []).append((mat, np.array(pts, float), np.array(n, float)))
    rep, fails = {}, []
    for zone, vs in lay['views'].items():
        if zone not in lay['zones']:
            continue
        zf = lay['zones'][zone]['box'][2] + 16
        acc = {f: [] for f in FAM.values()}
        for k, (vx, vy, vz, yaw, pitch) in enumerate(vs):
            path = os.path.join(a.run, 'iwzv_%s_%d.bmp' % (zone, k))
            if not os.path.isfile(path):
                continue
            img = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0
            H, W = img.shape[:2]
            fx = (W / 2) / math.tan(math.radians(a.hfov) / 2)
            o = np.array([vx, vy, vz + EYE]); f, r, u = cam_basis(yaw, pitch)
            polys = []
            for mat, P, n in by_zone.get(zone, []):
                if (o - P[0]) @ n <= 0:
                    continue                                   # back face
                d = P - o
                zc = d @ f
                # near-plane clip (z >= 4) of the polygon
                out, m = [], len(P)
                for i in range(m):
                    p0, p1, z0, z1 = d[i], d[(i + 1) % m], zc[i], zc[(i + 1) % m]
                    if z0 >= 4: out.append(p0)
                    if (z0 >= 4) != (z1 >= 4):
                        t = (4 - z0) / (z1 - z0); out.append(p0 + t * (p1 - p0))
                if len(out) < 3:
                    continue
                out = np.array(out)
                zz = out @ f
                xy = [(W / 2 + fx * (q @ r) / z_, H / 2 - fx * (q @ u) / z_) for q, z_ in zip(out, zz)]
                if n[2] > 0.7: fam = 1
                elif n[2] < -0.7: fam = 4
                elif P[:, 2].max() <= zf + 110: fam = 2
                else: fam = 3
                polys.append((float(np.mean(zz)), fam, xy))
            lab = Image.new('L', (W, H), 0)
            dr = ImageDraw.Draw(lab)
            for _, fam, xy in sorted(polys, key=lambda t: -t[0]):
                dr.polygon(xy, fill=fam)
            L = np.asarray(lab)
            for fam, name in FAM.items():
                msk = L == fam
                if msk.sum() > 2000:
                    acc[name].append(img[msk].mean(0))
        res = {}
        for name, cols in acc.items():
            if cols:
                c = [float(v) for v in np.mean(cols, 0)]
                res[name] = {'luma': round(float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]), 3),
                             'hue': round(colorsys.rgb_to_hsv(*c)[0] * 360, 1), 'sat': round(colorsys.rgb_to_hsv(*c)[1], 3)}
        checks = []
        for p, q in PAIRS:
            if p in res and q in res:
                dl = abs(res[p]['luma'] - res[q]['luma'])
                dh = abs(res[p]['hue'] - res[q]['hue']); dh = min(dh, 360 - dh)
                hue_counts = res[p]['sat'] > 0.12 and res[q]['sat'] > 0.12
                ok = dl >= a.min or (hue_counts and dh >= 20)
                checks.append({'pair': '%s/%s' % (p, q), 'dluma': round(dl, 3), 'dhue': round(dh, 1), 'ok': bool(ok)})
                if not ok:
                    fails.append('%s %s/%s dluma %.3f dhue %.0f' % (zone, p, q, dl, dh))
        rep[zone] = {'families': res, 'checks': checks}
        print('%-15s %s | %s' % (zone, ' '.join('%s %.2f' % (n, v['luma']) for n, v in res.items()),
                                 ' '.join('%s %s%.2f' % (c['pair'], '' if c['ok'] else 'FAIL ', c['dluma']) for c in checks)))
    json.dump({'zones': rep, 'fails': fails, 'min': a.min}, open(a.out, 'w'), indent=1)
    print('contrast fails: %s' % ('none' if not fails else '; '.join(fails)))


if __name__ == '__main__':
    main()
