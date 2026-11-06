"""Analyse a Station Zero v2 capture run: contact sheets, luma per frame/zone, gallery panel sampling.

usage: sz2_frames.py <run dir (frames iwzv_*.bmp)> <generated source dir (layout.json)> <out dir> [hfov]
Writes <out>/sheet_<zone>.jpg (5 views per zone), sheet_all.jpg, frames.json (mean luma, mean rgb, dark/bright
fractions per frame; per zone mean), and for gallery frames gallery.json (projected panel centres sampled:
material panels and lightmap texel panels) with annotated images gallery_<k>.jpg for checking the projection.
Luma is Rec.709 on sRGB values / 255.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

run, src, out = sys.argv[1:4]
HFOV = float(sys.argv[4]) if len(sys.argv) > 4 else 80.7
EYE = 60.0
os.makedirs(out, exist_ok=True)
layout = json.load(open(os.path.join(src, 'layout.json')))
frames = sorted(f for f in os.listdir(run) if f.startswith('iwzv_') and f.endswith('.bmp'))


def luma(a):
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255.0


stats, by_zone = {}, {}
for f in frames:
    name = f[5:-4]
    a = np.asarray(Image.open(os.path.join(run, f)).convert('RGB')).astype(np.float32)
    l = luma(a)
    zone = name.rsplit('_', 1)[0]
    st = {'mean_luma': round(float(l.mean()), 3), 'rgb': [round(float(c), 1) for c in a.reshape(-1, 3).mean(0)],
          'dark_frac': round(float((l < 0.04).mean()), 3), 'clip_frac': round(float((l > 0.98).mean()), 3),
          'size': list(a.shape[1::-1])}
    stats[name] = st
    by_zone.setdefault(zone, []).append((name, st))
summary = {z: {'mean_luma': round(float(np.mean([s['mean_luma'] for _, s in v])), 3),
               'rgb': [round(float(np.mean([s['rgb'][c] for _, s in v])), 1) for c in range(3)], 'frames': len(v)}
           for z, v in by_zone.items()}
json.dump({'frames': stats, 'zones': summary, 'target_luma': [0.30, 0.50]}, open(os.path.join(out, 'frames.json'), 'w'), indent=1)


def sheet(names, path, cols=5, tw=384):
    ims = [Image.open(os.path.join(run, 'iwzv_' + n + '.bmp')).convert('RGB') for n in names]
    if not ims:
        return
    th = int(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, rows * (th + 18)), (16, 16, 16))
    d = ImageDraw.Draw(sh)
    for k, (n, im) in enumerate(zip(names, ims)):
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        sh.paste(im.resize((tw, th)), (x, y + 18))
        d.text((x + 4, y + 2), '%s  luma %.2f' % (n, stats[n]['mean_luma']), fill=(255, 255, 0))
    sh.save(path, quality=88)


allnames = []
for zone, v in by_zone.items():
    names = [n for n, _ in v]
    allnames += names
    sheet(names, os.path.join(out, 'sheet_%s.jpg' % zone))
sheet([n for n in allnames if not n.startswith('gallery')], os.path.join(out, 'sheet_all.jpg'), cols=5, tw=320)

# gallery projection
gal = layout.get('gallery') or {}
gviews = gal.get('views') or []


def project(p, cam, yaw, pitch, w, h):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 1:
        return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(HFOV) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z, fx / z)


samples = {'materials': {}, 'texels': {}}
for k, (vx, vy, vz, yaw, pitch) in enumerate(gviews):
    fn = os.path.join(run, 'iwzv_gallery_%d.bmp' % k)
    if not os.path.isfile(fn):
        continue
    im = Image.open(fn).convert('RGB'); a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    d = ImageDraw.Draw(im)
    cam = (vx, vy, vz + EYE)
    for kind in ('materials', 'texels'):
        for it in gal.get(kind, []):
            pr = project(it['center'], cam, yaw, pitch, w, h)
            if not pr:
                continue
            px, py, s = pr
            half = it['size'] * s * 0.3
            if half < 3 or px - half < 0 or py - half < 0 or px + half >= w or py + half >= h:
                continue
            x0, y0, x1, y1 = int(px - half), int(py - half), int(px + half), int(py + half)
            patch = a[y0:y1, x0:x1].reshape(-1, 3)
            key = it.get('key') or ('%.4f,%.4f' % tuple(it['uv']))
            rec = {'rgb': [round(float(c), 1) for c in patch.mean(0)], 'luma': round(float(luma(patch).mean()), 3),
                   'std': round(float(luma(patch).std()), 3), 'view': k, 'px': int(px), 'py': int(py)}
            prev = samples[kind].get(key)
            if prev is None or abs(px - w / 2) < abs(prev['px'] - w / 2):
                samples[kind][key] = rec
            d.rectangle([x0, y0, x1, y1], outline=(255, 0, 255) if kind == 'materials' else (0, 255, 0))
            d.text((x0 + 2, y0 + 2), key[:18], fill=(255, 255, 0))
    im.save(os.path.join(out, 'gallery_%d.jpg' % k), quality=85)
json.dump(samples, open(os.path.join(out, 'gallery.json'), 'w'), indent=1)
for z, s in summary.items():
    print('%-16s luma %.3f rgb %s frames %d' % (z, s['mean_luma'], s['rgb'], s['frames']))
print('gallery samples: materials %d texels %d' % (len(samples['materials']), len(samples['texels'])))
