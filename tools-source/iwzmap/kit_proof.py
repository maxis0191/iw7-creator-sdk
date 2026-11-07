"""Engine proof for imported kit models: are they drawn, textured and lit in the capture frames?

usage: kit_proof.py <kit run dir> <baseline run dir> <generated source dir (layout.json)> <kit_final.json> <out dir>
                    [--zone kit] [--assets <dir holding the kit preview crops>] [--hfov 80.7]

Both runs capture the same views (layout['views'][zone] -> iwzv_<zone>_<n>.bmp); the baseline map is the same build
without the kit models. For every placed model of layout['decor'] with that zone and every view, the model's catalog
box (kit_final.json bounds, origin, yaw) is projected with the capture camera (sz2_propcheck.py camera model).
Inside the projected box:
  drawn     fraction of pixels that differ from the baseline frame (max channel diff > 0.08) -> the model was drawn
  textured  on the drawn pixels: luma spread p90-p10 >= 0.04 and edge density (mean |gradient| of luma) >= 0.01
            (a missing material / untextured slab is flat), not more than 45 % pixels with luma < 0.05 (black)
  lit       mean luma of the drawn pixels >= 0.25 x the kit preview's mean luma (engine preview of the stock model)
  colour    chroma correlation with the kit preview crop (mean normalised r/g/b; informative, lighting differs)
A model passes when one view where its box covers >= 1500 px has drawn >= 0.35 (or >= 3000 drawn pixels: thin
models) and is textured and lit.
Writes <out>/kit_proof.json and side-by-side crops <out>/kit_<model>_<view>.jpg (kit | baseline | preview).
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

EYE = 60.0


def project(p, cam, yaw, pitch, w, h, hfov):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 8:
        return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(hfov) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z)


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('base'); ap.add_argument('src'); ap.add_argument('kit'); ap.add_argument('out')
    ap.add_argument('--zone', default='kit'); ap.add_argument('--assets', default=''); ap.add_argument('--hfov', type=float, default=80.7)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    kit = {m['name']: m for m in json.load(open(a.kit))['models']}
    assets = a.assets or os.path.dirname(os.path.dirname(os.path.abspath(a.kit)))
    props = [d for d in lay['decor'] if d.get('zone') == a.zone]
    views = lay['views'].get(a.zone, [])
    res = {}
    for vi, (vx, vy, vz, yaw, pitch) in enumerate(views):
        name = 'iwzv_%s_%d.bmp' % (a.zone, vi)
        fk, fb = os.path.join(a.run, name), os.path.join(a.base, name)
        if not os.path.isfile(fk):
            print('missing frame', fk); continue
        K = np.asarray(Image.open(fk).convert('RGB'), dtype=np.float32) / 255
        B = np.asarray(Image.open(fb).convert('RGB'), dtype=np.float32) / 255 if os.path.isfile(fb) else None
        h, w = K.shape[:2]
        cam = (vx, vy, vz + EYE)
        # nearer props first: a farther prop's box pixels covered by a nearer one are not its own
        order = sorted(props, key=lambda d: -math.dist(cam, d['origin']))
        owner = np.full((h, w), -1, dtype=np.int32)
        boxes = {}
        for pi, d in enumerate(order):
            m = kit.get(d['model'])
            if not m:
                continue
            mn, mx = m['bounds']['mins'], m['bounds']['maxs']
            yr = math.radians(d.get('yaw', 0)); o = d['origin']
            pts = []
            for x in (mn[0], mx[0]):
                for y in (mn[1], mx[1]):
                    for z in (mn[2], mx[2]):
                        q = project((o[0] + x * math.cos(yr) - y * math.sin(yr), o[1] + x * math.sin(yr) + y * math.cos(yr), o[2] + z),
                                    cam, yaw, pitch, w, h, a.hfov)
                        if q:
                            pts.append(q)
            if len(pts) < 8:
                continue
            x0, x1 = max(0, int(min(p[0] for p in pts))), min(w, int(max(p[0] for p in pts)) + 1)
            y0, y1 = max(0, int(min(p[1] for p in pts))), min(h, int(max(p[1] for p in pts)) + 1)
            if x1 - x0 < 12 or y1 - y0 < 12:
                continue
            owner[y0:y1, x0:x1] = pi
            boxes[pi] = (d, (x0, y0, x1, y1))
        for pi, (d, (x0, y0, x1, y1)) in boxes.items():
            own = owner[y0:y1, x0:x1] == pi
            crop = K[y0:y1, x0:x1]
            rec = {'view': vi, 'box': [x0, y0, x1, y1], 'pixels': int(own.sum())}
            if B is not None:
                diff = np.abs(crop - B[y0:y1, x0:x1]).max(axis=2) > 0.08
                drawn = diff & own
                rec['drawn'] = round(float(drawn.sum()) / max(1, own.sum()), 3)
            else:
                drawn = own
                rec['drawn'] = None
            L = luma(crop)
            sel = L[drawn] if drawn.sum() > 50 else L[own]
            gy, gx = np.gradient(L)
            g = np.hypot(gx, gy)[drawn] if drawn.sum() > 50 else np.hypot(gx, gy)[own]
            rec['meanLuma'] = round(float(sel.mean()), 4) if sel.size else 0
            rec['spread'] = round(float(np.percentile(sel, 90) - np.percentile(sel, 10)), 4) if sel.size else 0
            rec['edges'] = round(float(g.mean()), 4) if g.size else 0
            rec['black'] = round(float((sel < 0.05).mean()), 3) if sel.size else 1
            rgb = crop[drawn] if drawn.sum() > 50 else crop[own]
            chroma = (rgb / np.maximum(rgb.sum(axis=1, keepdims=True), 1e-3)).mean(axis=0) if rgb.size else np.zeros(3)
            rec['chroma'] = [round(float(c), 4) for c in chroma]
            m = kit[d['model']]
            ref_luma = (m.get('check', {}).get('texture', {}).get('meanLuma') or 0) / 255.0
            rec['previewLuma'] = round(ref_luma, 4)
            pv = os.path.join(assets, m.get('preview', '').replace('\\', '/')) if m.get('preview') else ''
            P = None
            if pv and os.path.isfile(pv):
                P = np.asarray(Image.open(pv).convert('RGB'), dtype=np.float32) / 255
                pl = luma(P); pm = pl > 0.02
                pc = (P[pm] / np.maximum(P[pm].sum(axis=1, keepdims=True), 1e-3)).mean(axis=0) if pm.sum() else np.zeros(3)
                rec['previewChroma'] = [round(float(c), 4) for c in pc]
                rec['chromaDist'] = round(float(np.abs(pc - chroma).sum()), 4)
            rec['textured'] = bool(rec['spread'] >= 0.04 and rec['edges'] >= 0.01 and rec['black'] <= 0.45)
            rec['lit'] = bool(rec['meanLuma'] >= 0.25 * ref_luma) if ref_luma else bool(rec['meanLuma'] >= 0.08)
            rec['drawnPixels'] = int(drawn.sum()) if B is not None else None
            # thin or diagonal models (a plank) fill little of their box: enough drawn pixels also counts
            seen = rec['drawn'] is None or rec['drawn'] >= 0.35 or rec['drawnPixels'] >= 3000
            rec['pass'] = bool(rec['pixels'] >= 1500 and seen and rec['textured'] and rec['lit'])
            res.setdefault(d['model'], {'model': d['model'], 'origin': d['origin'], 'views': []})['views'].append(rec)
            tiles = [Image.fromarray((crop * 255).astype(np.uint8))]
            if B is not None:
                tiles.append(Image.fromarray((B[y0:y1, x0:x1] * 255).astype(np.uint8)))
            if P is not None:
                pi_ = Image.fromarray((P * 255).astype(np.uint8)); pi_.thumbnail((x1 - x0, y1 - y0)); tiles.append(pi_)
            th = max(t.size[1] for t in tiles); sheet = Image.new('RGB', (sum(t.size[0] for t in tiles) + 8 * len(tiles), th))
            xx = 0
            for t in tiles:
                sheet.paste(t, (xx, 0)); xx += t.size[0] + 8
            sheet.save(os.path.join(a.out, 'kit_%s_%d.jpg' % (d['model'], vi)), quality=88)
    for r in res.values():
        r['pass'] = any(v['pass'] for v in r['views'])
    missing = [d['model'] for d in props if d['model'] not in res]
    out = {'zone': a.zone, 'run': a.run, 'baseline': a.base, 'models': res, 'notInAnyView': missing,
           'passed': sum(1 for r in res.values() if r['pass']), 'checked': len(res)}
    json.dump(out, open(os.path.join(a.out, 'kit_proof.json'), 'w'), indent=1)
    for r in sorted(res.values(), key=lambda r: r['model']):
        best = max(r['views'], key=lambda v: (v['pass'], v['pixels']))
        print('%-4s %-42s view %d px %7d drawn %s luma %.3f (preview %.3f) spread %.3f edges %.3f black %.2f chromaDist %s'
              % ('PASS' if r['pass'] else 'FAIL', r['model'], best['view'], best['pixels'], best['drawn'], best['meanLuma'],
                 best['previewLuma'], best['spread'], best['edges'], best['black'], best.get('chromaDist')))
    if missing:
        print('not in any view:', missing)
    print('KITPROOF passed %d / %d' % (out['passed'], len(props)))
    return 0 if out['passed'] == len(props) else 1


if __name__ == '__main__':
    sys.exit(main())
