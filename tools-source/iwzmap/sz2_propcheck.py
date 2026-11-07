"""Find props that render as flat black or untextured slabs in the engine capture frames.

usage: sz2_propcheck.py <run dir (iwzv_*.bmp)> <generated source dir (layout.json)> <asset catalog.json> <out dir>
                       [kit_final.json] [hfov]

Props: every placed model of layout.json ('decor' and 'models': model name, origin, yaw; bounds from the asset
catalog) and every world-geometry prop box ('geo_props': name, mins, maxs). For each capture view (layout 'views',
'sign_view_list') the prop's bounding box is projected with the capture camera model (same as sz2_frames.py); props
behind the camera, smaller than 24x24 px or less than half inside the frame are skipped. A crop is FLAGGED when
more than 45 % of its pixels have luma < 0.05 (flat black), or when its luma spread (p90 - p10) is < 0.03 with mean
luma < 0.2 (untextured dark slab). The crop is the projected box, so background can lower the dark fraction: the
check errs towards passing partially visible props; a prop is flagged if it is flagged in any view where it fills
at least 1 % of the frame. The decision uses the central 40 % of the box (the prop itself): median luma < 0.08, or,
with the kit preview's measured texture luma (kit_final.json check.texture.meanLuma, engine preview), a median below
35 % of it and below 0.15. Writes <out>/propcheck.json and <out>/prop_<name>_<view>.jpg for flagged crops.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

run, src, catalog, out = sys.argv[1:5]
KIT = {}
if len(sys.argv) > 5 and sys.argv[5].endswith('.json'):
    KIT = {m['name']: m for m in json.load(open(sys.argv[5]))['models']}
HFOV = float(sys.argv[6]) if len(sys.argv) > 6 else 80.7
EYE = 60.0
os.makedirs(out, exist_ok=True)
layout = json.load(open(os.path.join(src, 'layout.json')))
cat = {m['name']: m for m in json.load(open(catalog))['models']}


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


props = []
for d in list(layout.get('decor', [])) + list(layout.get('models', [])):
    m = cat.get(d['model'])
    if not m:
        props.append({'name': d['model'], 'zone': d.get('zone'), 'corners': None, 'note': 'not in catalog'})
        continue
    mn, mx = m['bounds']['mins'], m['bounds']['maxs']
    yr = math.radians(d.get('yaw', 0))
    o = d['origin']
    cs = []
    for x in (mn[0], mx[0]):
        for y in (mn[1], mx[1]):
            for z in (mn[2], mx[2]):
                cs.append((o[0] + x * math.cos(yr) - y * math.sin(yr), o[1] + x * math.sin(yr) + y * math.cos(yr), o[2] + z))
    props.append({'name': d['model'], 'zone': d.get('zone'), 'corners': cs, 'origin': o})
for g in layout.get('geo_props', []):
    (x0, y0, z0), (x1, y1, z1) = g['mins'], g['maxs']
    props.append({'name': 'geo:' + g['name'], 'zone': g.get('zone'), 'origin': [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2],
                  'corners': [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]})

views = []
for zone, vs in layout.get('views', {}).items():
    for k, v in enumerate(vs):
        views.append(('%s_%d' % (zone, k), v))
for k, v in enumerate(layout.get('sign_view_list', [])):
    views.append(('sign_%d' % k, v))

frames = {}
results = {}
for name, (vx, vy, vz, yaw, pitch) in views:
    fn = os.path.join(run, 'iwzv_%s.bmp' % name)
    if not os.path.isfile(fn):
        continue
    if name not in frames:
        frames[name] = np.asarray(Image.open(fn).convert('RGB')).astype(np.float32) / 255.0
    a = frames[name]
    h, w = a.shape[:2]
    cam = (vx, vy, vz + EYE)
    for pi, p in enumerate(props):
        if not p['corners']:
            continue
        if math.dist(cam, p['origin']) > 1600:
            continue
        pts = [project(c, cam, yaw, pitch, w, h) for c in p['corners']]
        if any(q is None for q in pts):
            continue
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        area = (bx1 - bx0) * (by1 - by0)
        cx0, cx1, cy0, cy1 = max(0, int(bx0)), min(w, int(bx1)), max(0, int(by0)), min(h, int(by1))
        if cx1 - cx0 < 24 or cy1 - cy0 < 24 or area <= 0 or (cx1 - cx0) * (cy1 - cy0) < 0.5 * area:
            continue
        crop = a[cy0:cy1, cx0:cx1]
        ix0, ix1 = int(bx0 + 0.3 * (bx1 - bx0)), int(bx1 - 0.3 * (bx1 - bx0))
        iy0, iy1 = int(by0 + 0.3 * (by1 - by0)), int(by1 - 0.3 * (by1 - by0))
        ix0, ix1, iy0, iy1 = max(0, ix0), min(w, max(ix1, ix0 + 2)), max(0, iy0), min(h, max(iy1, iy0 + 2))
        inner = a[iy0:iy1, ix0:ix1]
        lum = 0.2126 * inner[..., 0] + 0.7152 * inner[..., 1] + 0.0722 * inner[..., 2]
        med = float(np.median(lum))
        dark = float((lum < 0.05).mean())
        p10, p90 = np.percentile(lum, [10, 90])
        fill = (cx1 - cx0) * (cy1 - cy0) / float(w * h)
        ref = None
        km = KIT.get(p['name'])
        if km and km.get('check', {}).get('texture'):
            ref = km['check']['texture']['meanLuma'] / 255.0
        flag = fill >= 0.01 and (med < 0.08 or dark > 0.45 or (ref is not None and med < 0.35 * ref and med < 0.15))
        rec = {'view': name, 'median': round(med, 3), 'dark_frac': round(dark, 3), 'spread': round(float(p90 - p10), 3),
               'preview': None if ref is None else round(ref, 3), 'fill': round(fill, 4), 'flag': bool(flag)}
        key = '%d:%s' % (pi, p['name'])
        results.setdefault(key, {'name': p['name'], 'zone': p['zone'], 'origin': p['origin'], 'views': []})['views'].append(rec)
        if flag:
            Image.fromarray((crop * 255).astype(np.uint8)).save(os.path.join(out, 'prop_%s_%s.jpg' % (p['name'].replace(':', '_'), name)), quality=85)
seen = [r for r in results.values()]
flagged = [r for r in seen if any(v['flag'] for v in r['views'])]
missing = [p['name'] for p in props if not p['corners']]
json.dump({'props': len(props), 'seen': len(seen), 'flagged': flagged, 'not_in_catalog': missing,
           'all': seen}, open(os.path.join(out, 'propcheck.json'), 'w'), indent=1)
for r in flagged:
    worst = min(r['views'], key=lambda v: v['median'])
    print('FLAG %-40s %-15s median %.3f dark %.2f preview %s view %s' % (r['name'], r['zone'], worst['median'], worst['dark_frac'], worst['preview'], worst['view']))
print('props %d, seen in frames %d, flagged %d, not in catalog %d' % (len(props), len(seen), len(flagged), len(missing)))
