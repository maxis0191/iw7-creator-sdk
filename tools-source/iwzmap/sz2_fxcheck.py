"""Check in engine frames that the ambient FX render and that decal quads blend (not opaque squares).

usage: sz2_fxcheck.py <run dir> <generated source dir (layout.json)> <out dir> [hfov]

FX: the views run captures every FX view twice, with the FX held (iwzv_fx_<k>_off, level dvar paris_iwz_fxhold 1)
and running (iwzv_fx_<k>_on). The FX origin +-64 units is projected with the capture camera model; PASS when the mean
absolute pixel difference of that crop between the two captures is >= 0.012 (0..1 scale; camera, lighting and
static scene identical), and the rest of the frame changed less than the crop (difference ratio >= 2).
Decals: every decal quad of layout 'decals' is projected into the zone views where it is fully visible and at least
40 px wide; FAIL when the decal crop is flat (luma std < 0.012) and differs from the surrounding ring by more than
0.08 (an opaque square), PASS otherwise.
Writes <out>/fxcheck.json, fx_<k>.jpg (off | on).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

run, src, out = sys.argv[1:4]
HFOV = float(sys.argv[4]) if len(sys.argv) > 4 else 80.7
EYE = 60.0
os.makedirs(out, exist_ok=True)
lay = json.load(open(os.path.join(src, 'layout.json')))


def project(p, cam, yaw, pitch, w, h):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 8:
        return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(HFOV) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z)


def load(name):
    fn = os.path.join(run, 'iwzv_%s.bmp' % name)
    return np.asarray(Image.open(fn).convert('RGB')).astype(np.float32) / 255.0 if os.path.isfile(fn) else None


def box_px(corners, cam, yaw, pitch, w, h):
    pts = [project(c, cam, yaw, pitch, w, h) for c in corners]
    if any(p is None for p in pts):
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(0, int(min(xs))), max(0, int(min(ys))), min(w, int(max(xs))), min(h, int(max(ys)))


res = {'fx': [], 'decals': [], 'flicker': []}
for li, (vx, vy, vz, yaw, pitch) in lay.get('flicker_views', []):
    f = lay['flicker'][li]
    a, b = load('flk_%d_on' % li), load('flk_%d_off' % li)
    if a is None or b is None:
        res['flicker'].append({'zone': f['zone'], 'result': 'NO_FRAME'}); continue
    h, w = a.shape[:2]
    o = f['origin']
    corners = [(o[0] + dx, o[1] + dy, o[2] + dz) for dx in (-40, 40) for dy in (-40, 40) for dz in (-24, 8)]
    bx = box_px(corners, (vx, vy, vz + EYE), yaw, pitch, w, h)
    if not bx or bx[2] - bx[0] < 8 or bx[3] - bx[1] < 8:
        res['flicker'].append({'zone': f['zone'], 'result': 'OFF_FRAME'}); continue
    x0, y0, x1, y1 = bx
    d = np.abs(b - a).mean(axis=2)
    inside = float(d[y0:y1, x0:x1].mean())
    mask = np.ones_like(d, bool); mask[y0:y1, x0:x1] = False
    outside = float(d[mask].mean()) if mask.any() else 0.0
    la = float((0.2126 * a[y0:y1, x0:x1, 0] + 0.7152 * a[y0:y1, x0:x1, 1] + 0.0722 * a[y0:y1, x0:x1, 2]).mean())
    lb = float((0.2126 * b[y0:y1, x0:x1, 0] + 0.7152 * b[y0:y1, x0:x1, 1] + 0.0722 * b[y0:y1, x0:x1, 2]).mean())
    ok = inside >= 0.02 and inside >= 2 * outside and la > lb
    res['flicker'].append({'zone': f['zone'], 'origin': o, 'diff_in': round(inside, 4), 'diff_out': round(outside, 4),
                           'luma_on': round(la, 3), 'luma_off': round(lb, 3), 'result': 'PASS' if ok else 'FAIL'})
for fi, (vx, vy, vz, yaw, pitch) in lay.get('fx_views', []):
    f = lay['fx'][fi]
    a, b = load('fx_%d_off' % fi), load('fx_%d_on' % fi)
    if a is None or b is None:
        res['fx'].append({'fx': f['fx'], 'zone': f['zone'], 'result': 'NO_FRAME'}); continue
    h, w = a.shape[:2]
    o = f['origin']
    corners = [(o[0] + dx, o[1] + dy, o[2] + dz) for dx in (-64, 64) for dy in (-64, 64) for dz in (-64, 64)]
    bx = box_px(corners, (vx, vy, vz + EYE), yaw, pitch, w, h)
    if not bx or bx[2] - bx[0] < 8 or bx[3] - bx[1] < 8:
        res['fx'].append({'fx': f['fx'], 'zone': f['zone'], 'result': 'OFF_FRAME'}); continue
    x0, y0, x1, y1 = bx
    d = np.abs(b - a).mean(axis=2)
    inside = float(d[y0:y1, x0:x1].mean())
    mask = np.ones_like(d, bool); mask[y0:y1, x0:x1] = False
    outside = float(d[mask].mean()) if mask.any() else 0.0
    ok = inside >= 0.012 and inside >= 2 * outside
    side = Image.new('RGB', (2 * (x1 - x0) + 8, y1 - y0))
    side.paste(Image.fromarray((a[y0:y1, x0:x1] * 255).astype(np.uint8)), (0, 0))
    side.paste(Image.fromarray((b[y0:y1, x0:x1] * 255).astype(np.uint8)), (x1 - x0 + 8, 0))
    side.save(os.path.join(out, 'fx_%d.jpg' % fi), quality=85)
    res['fx'].append({'fx': f['fx'], 'zone': f['zone'], 'origin': o, 'diff_in': round(inside, 4), 'diff_out': round(outside, 4),
                      'result': 'PASS' if ok else 'FAIL'})

views = [('%s_%d' % (z, k), v) for z, vs in lay.get('views', {}).items() for k, v in enumerate(vs)]
for dc in lay.get('decals', []):
    if dc['axis'] == 'x':
        y = dc['fixed'] + dc['facing'] * 0.4
        corners = [(dc['s'] + sx * dc['w'] / 2, y, dc['zc'] + sz * dc['h'] / 2) for sx in (-1, 1) for sz in (-1, 1)]
    else:
        x = dc['fixed'] + dc['facing'] * 0.4
        corners = [(x, dc['s'] + sx * dc['w'] / 2, dc['zc'] + sz * dc['h'] / 2) for sx in (-1, 1) for sz in (-1, 1)]
    best = None
    for name, (vx, vy, vz, yaw, pitch) in views:
        if not name.startswith(dc['zone']):
            continue
        a = load(name)
        if a is None:
            continue
        h, w = a.shape[:2]
        bx = box_px(corners, (vx, vy, vz + EYE), yaw, pitch, w, h)
        if not bx:
            continue
        x0, y0, x1, y1 = bx
        if x1 - x0 < 40 or y1 - y0 < 20 or x0 <= 0 or y0 <= 0 or x1 >= w or y1 >= h:
            continue
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        ix0, ix1 = x0 + (x1 - x0) // 5, x1 - (x1 - x0) // 5
        iy0, iy1 = y0 + (y1 - y0) // 5, y1 - (y1 - y0) // 5
        crop = lum[iy0:iy1, ix0:ix1]
        pad = max(6, (x1 - x0) // 4)
        ring = np.concatenate([lum[max(0, y0 - pad):y0, x0:x1].ravel(), lum[y1:y1 + pad, x0:x1].ravel(),
                               lum[y0:y1, max(0, x0 - pad):x0].ravel(), lum[y0:y1, x1:x1 + pad].ravel()])
        rec = {'mat': dc['mat'], 'zone': dc['zone'], 'view': name, 'std': round(float(crop.std()), 4),
               'mean': round(float(crop.mean()), 3), 'ring': round(float(ring.mean()), 3) if ring.size else None, 'width_px': x1 - x0}
        if best is None or rec['width_px'] > best['width_px']:
            best = rec
    if best is None:
        res['decals'].append({'mat': dc['mat'], 'zone': dc['zone'], 'result': 'NOT_SEEN'}); continue
    opaque = best['std'] < 0.012 and best['ring'] is not None and abs(best['mean'] - best['ring']) > 0.08
    best['result'] = 'FAIL' if opaque else 'PASS'
    res['decals'].append(best)
json.dump(res, open(os.path.join(out, 'fxcheck.json'), 'w'), indent=1)
for r in res['fx']:
    print('FX    %-62s %-15s %s %s' % (r['fx'], r['zone'], r['result'], r.get('diff_in', '')))
for r in res['decals']:
    print('DECAL %-20s %-15s %s %s' % (r['mat'], r['zone'], r['result'], {k: r[k] for k in ('std', 'mean', 'ring') if k in r}))
for r in res['flicker']:
    print('FLICK %-15s %s %s' % (r['zone'], r['result'], {k: r[k] for k in ('diff_in', 'diff_out', 'luma_on', 'luma_off') if k in r}))
print('flicker PASS %d/%d' % (sum(r['result'] == 'PASS' for r in res['flicker']), len(res['flicker'])))
print('fx PASS %d/%d, decals PASS %d/%d (seen %d)' % (sum(r['result'] == 'PASS' for r in res['fx']), len(res['fx']),
      sum(r['result'] == 'PASS' for r in res['decals']), len(res['decals']), sum(r['result'] != 'NOT_SEEN' for r in res['decals'])))
