"""Check engine preview frames of iwzmap_preview.gsc against the asset catalog and build a contact sheet.

usage: python -I preview_analyze.py --run <runner output dir> [--run ...] --catalog catalog.json
                                    --dump <zone>=<dump dir>[;dir] ... --out <dir> [--hfov-scale 1.0]

For every "[IWZ local] PV" line of result.local.json:
  engine bounds : getpointinbounds(-1,-1,-1)/(1,1,1) of the spawned script_model versus the catalog header bounds
                  rotated by the entity angles and moved to its origin (max abs difference, game units);
  silhouette    : pixels that differ from the background frames (iwzbg<k>, taken before/after) -> mask bbox;
  projection    : LOD0 vertices (from the dump's .xsb) projected with the logged eye/angles -> bbox;
                  IoU(mask bbox, projected bbox) measures whether bounds and pose match the render;
  texture       : mean luma, luma std, near-black fraction and a two-tone checkerboard score inside the mask.
Writes previews.json (one row per frame with PASS/FAIL per check), crops/<model>.png and contact sheets.
"""
import argparse
import json
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ztdump  # noqa: E402

VEC = r'\(([-\d.e]+), ([-\d.e]+), ([-\d.e]+)\)'


def vec(s):
    m = re.search(VEC, s)
    return tuple(float(m.group(i)) for i in (1, 2, 3))


def parse_lines(lines):
    cams, pvs, bgs = {}, [], []
    cur = None
    for ln in lines:
        if '[IWZ local] PREVIEW CAM' in ln:
            ci = int(re.search(r'ci=(\d+)', ln).group(1))
            eye = vec(ln.split('eye=')[1])
            ang = vec(ln.split('angles=')[1])
            fov = float(re.search(r'fov=([-\d.]+)', ln).group(1))
            fs = float(re.search(r'fovscale=([-\d.]+)', ln).group(1))
            cams[ci] = {'eye': eye, 'angles': ang, 'fov': fov, 'fovscale': fs}
            cur = ci
        elif '[IWZ local] PV ' in ln:
            d = {'n': int(re.search(r'n=(\d+)', ln).group(1)), 'model': re.search(r'model=([^;]+)', ln).group(1),
                 'origin': vec(ln.split('origin=')[1]), 'angles': vec(ln.split('angles=')[1]),
                 'lo': vec(ln.split('lo=')[1]), 'hi': vec(ln.split('hi=')[1]), 'eye': vec(ln.split('eye=')[1]),
                 'bg': int(re.search(r'bg=(\d+)', ln).group(1)), 'cam': cur}
            pvs.append(d)
        elif '[IWZ local] BG ' in ln:
            bgs.append((int(re.search(r'k=(\d+)', ln).group(1)), cur))
    return cams, pvs, bgs


def rot_yaw(p, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_angles(p, ang):
    """IW angles (pitch, yaw, roll) applied as AnglesToAxis: world = x*fwd + y*left + z*up."""
    f, r, u = basis(ang)
    left = (-r[0], -r[1], -r[2])
    return tuple(p[0] * f[i] + p[1] * left[i] + p[2] * u[i] for i in range(3))


def basis(ang):
    p, y, r = (math.radians(a) for a in ang)
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(r), math.cos(r)
    fwd = (cp * cy, cp * sy, -sp)
    right = (-sr * sp * cy + cr * sy, -sr * sp * sy - cr * cy, -sr * cp)
    up = (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp)
    return fwd, right, up


def projector(eye, ang, w, h, fov, fovscale, hscale):
    fwd, right, up = basis(ang)
    # IW7: cg_fov is the 4:3 horizontal fov; wider aspect ratios widen it (hor+)
    t43 = math.tan(math.radians(fov * (fovscale or 1.0)) / 2)
    tx = t43 * (w / h) / (4 / 3) * hscale
    ty = tx * h / w

    def proj(p):
        v = (p[0] - eye[0], p[1] - eye[1], p[2] - eye[2])
        z = v[0] * fwd[0] + v[1] * fwd[1] + v[2] * fwd[2]
        if z <= 1:
            return None
        x = v[0] * right[0] + v[1] * right[1] + v[2] * right[2]
        yv = v[0] * up[0] + v[1] * up[1] + v[2] * up[2]
        return (w / 2 + x / z * (w / 2) / tx, h / 2 - yv / z * (h / 2) / ty)
    return proj


def bbox_of(points):
    pts = [p for p in points if p]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def iou(a, b):
    if not a or not b:
        return 0.0
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def diff_mask(frame, bgs, static_mask, thr):
    best = None
    for bg in bgs:
        d = ImageChops.difference(frame, bg).convert('L')
        best = d if best is None else ImageChops.darker(best, d)
    m = best.point(lambda v: 255 if v > thr else 0)
    if static_mask is not None:
        m = ImageChops.multiply(m, static_mask)
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    return m


def keep_components_near(mask, box, grow):
    """Drop changed regions that do not touch the projected box grown by `grow` (moving cars, beams, flicker
    elsewhere in the background). A component that touches it is kept whole, so a model larger than its
    bounds still shows as a low IoU."""
    import numpy as np
    from scipy import ndimage
    m = np.array(mask) > 0
    lab, n = ndimage.label(m)
    w, h = mask.size
    gx = (box[2] - box[0]) * grow
    gy = (box[3] - box[1]) * grow
    x0, y0 = max(0, int(box[0] - gx)), max(0, int(box[1] - gy))
    x1, y1 = min(w, int(box[2] + gx) + 1), min(h, int(box[3] + gy) + 1)
    keep = set(np.unique(lab[y0:y1, x0:x1])) - {0}
    out = np.isin(lab, list(keep)) if keep else np.zeros_like(m)
    return Image.fromarray((out * 255).astype('uint8')), int(m.sum() - out.sum())


def texture_stats(frame, mask):
    g = frame.convert('L')
    vals = [v for v, k in zip(g.get_flattened_data() if hasattr(g, 'get_flattened_data') else g.getdata(), mask.get_flattened_data() if hasattr(mask, 'get_flattened_data') else mask.getdata()) if k]
    if len(vals) < 50:
        return {'pixels': len(vals)}
    n = len(vals)
    mean = sum(vals) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
    black = sum(v < 12 for v in vals) / n
    # checkerboard score: share of variance explained by a 2-level (Otsu) split; a flat two-tone
    # default checker is ~1.0, real textures are lower
    hist = [0] * 256
    for v in vals:
        hist[v] += 1
    total = sum(i * hist[i] for i in range(256))
    best, wb, sb = 0, 0, 0
    var_t = std * std
    for t in range(256):
        wb += hist[t]
        if wb == 0 or wb == n:
            continue
        sb += t * hist[t]
        mb = sb / wb
        mf = (total - sb) / (n - wb)
        between = wb * (n - wb) * (mb - mf) ** 2 / (n * n)
        best = max(best, between)
    two_tone = best / var_t if var_t > 0 else 1.0
    return {'pixels': n, 'meanLuma': round(mean, 1), 'stdLuma': round(std, 1), 'blackFrac': round(black, 3),
            'twoTone': round(two_tone, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='append', required=True)
    ap.add_argument('--catalog', required=True)
    ap.add_argument('--dump', action='append', default=[])
    ap.add_argument('--out', required=True)
    ap.add_argument('--hfov-scale', type=float, default=1.0)
    ap.add_argument('--thr', type=int, default=14)
    ap.add_argument('--roi', type=float, default=0.05)
    ap.add_argument('--static-thr', type=int, default=20)  # background-to-background change marking HUD/flicker pixels
    ap.add_argument('--min-luma', type=float, default=14.0)  # night maps (cp_disco) light props dimly
    ap.add_argument('--tile', type=int, default=240)
    ap.add_argument('--cols', type=int, default=8)
    a = ap.parse_args()
    cat = {r['name']: r for r in json.load(open(a.catalog))['models']}
    dumps = {}
    for z in a.dump:
        n, _, d = z.partition('=')
        dumps[n] = [x for x in d.split(';') if x]
    os.makedirs(os.path.join(a.out, 'crops'), exist_ok=True)
    rows = []
    for run in a.run:
        res = json.load(open(os.path.join(run, 'result.local.json'), encoding='utf-8-sig'))
        cams, pvs, bgk = parse_lines(res.get('Lines') or [])
        bg_imgs, bg_cam = {}, {}
        for k, ci in bgk:
            p = os.path.join(run, 'iwzbg%d.bmp' % k)
            if os.path.exists(p):
                bg_imgs[k] = Image.open(p).convert('RGB')
                bg_cam[k] = ci
        # pixels that change between background frames of the same camera (HUD counters, flicker) are not
        # trusted; frames of different cameras show different views and are never compared
        statics = {}
        for ci in set(bg_cam.values()):
            ks = sorted(k for k in bg_imgs if bg_cam[k] == ci)
            if len(ks) < 2:
                continue
            acc = None
            for i in range(1, len(ks)):
                d = ImageChops.difference(bg_imgs[ks[i]], bg_imgs[ks[0]]).convert('L').point(lambda v: 255 if v > a.static_thr else 0)
                acc = d if acc is None else ImageChops.lighter(acc, d)
            statics[ci] = ImageChops.invert(acc.filter(ImageFilter.MaxFilter(9)))
        for pv in pvs:
            fp = os.path.join(run, 'iwzpv%d.bmp' % pv['n'])
            row = {'run': os.path.basename(run.rstrip('/\\')), 'n': pv['n'], 'model': pv['model'], 'frame': fp}
            c = cat.get(pv['model'])
            if not c:
                row['error'] = 'not in catalog'
                rows.append(row)
                continue
            row['zones'] = c['zones']
            row['category'] = c['category']
            # 1. engine bounds vs header bounds
            mins, maxs = c['bounds']['mins'], c['bounds']['maxs']
            exp_lo = tuple(pv['origin'][i] + rot_angles(mins, pv['angles'])[i] for i in range(3))
            exp_hi = tuple(pv['origin'][i] + rot_angles(maxs, pv['angles'])[i] for i in range(3))
            ediff = max(max(abs(exp_lo[i] - pv['lo'][i]), abs(exp_hi[i] - pv['hi'][i])) for i in range(3))
            # alternative semantics: world axis-aligned box of the rotated corners (absmin/absmax)
            wc = [tuple(pv['origin'][i] + rot_angles((x, y, z), pv['angles'])[i] for i in range(3))
                  for x in (mins[0], maxs[0]) for y in (mins[1], maxs[1]) for z in (mins[2], maxs[2])]
            alo = tuple(min(p[i] for p in wc) for i in range(3))
            ahi = tuple(max(p[i] for p in wc) for i in range(3))
            adiff = max(max(abs(alo[i] - pv['lo'][i]), abs(ahi[i] - pv['hi'][i])) for i in range(3))
            row['engineBoundsDiff'] = round(min(ediff, adiff), 3)
            row['engineBoundsSemantics'] = 'oriented' if ediff <= adiff else 'world-aabb'
            row['engineBounds'] = 'PASS' if min(ediff, adiff) <= 0.6 else 'FAIL'
            if pv['lo'] == pv['hi']:
                # getpointinbounds returns the origin for a script_model (no absmin/absmax): not a measurement
                row['engineBounds'] = 'N/A'
            if not os.path.exists(fp):
                row['error'] = 'frame missing'
                rows.append(row)
                continue
            frame = Image.open(fp).convert('RGB')
            w, h = frame.size
            cam = cams.get(pv['cam'], {})
            ang = cam.get('angles', (0, 0, 0))
            proj = projector(pv['eye'], ang, w, h, cam.get('fov', 65), cam.get('fovscale', 1), a.hfov_scale)
            # 2. projected LOD0 vertices
            l0 = c['lods'][0]['surfs'] if c['lods'] else None
            pts = []
            zone_dirs = []
            for z in c['zones']:
                zone_dirs += dumps.get(z, [])
            for d in zone_dirs:
                p = os.path.join(d, 'xsurface', (l0 or '') + '.xsb')
                if l0 and os.path.exists(p):
                    s = ztdump.read_xsurfs(p, want_verts=True)
                    for vl in s['vertexLists']:
                        step = max(1, len(vl) // 4000)
                        for v in vl[::step]:
                            wv = rot_angles(v, pv['angles'])
                            pts.append(proj((pv['origin'][0] + wv[0], pv['origin'][1] + wv[1], pv['origin'][2] + wv[2])))
                    break
            corners = []
            for cx in (mins[0], maxs[0]):
                for cy in (mins[1], maxs[1]):
                    for cz in (mins[2], maxs[2]):
                        wv = rot_angles((cx, cy, cz), pv['angles'])
                        corners.append(proj(tuple(pv['origin'][i] + wv[i] for i in range(3))))
            pbox = bbox_of(pts)
            cbox = bbox_of(corners)
            # 3. silhouette from background difference
            near = [bg_imgs[k] for k in (pv['bg'] - 1, pv['bg']) if k in bg_imgs and bg_cam[k] == pv['cam']]
            mask = diff_mask(frame, near, statics.get(pv['cam']), a.thr) if near else None
            if mask is not None and pbox:
                mask, row['discardedPixels'] = keep_components_near(mask, pbox, a.roi)
            mbox = mask.getbbox() if mask else None
            row['projBox'] = [round(x, 1) for x in pbox] if pbox else None
            row['boundsBox'] = [round(x, 1) for x in cbox] if cbox else None
            row['maskBox'] = list(mbox) if mbox else None
            row['iou'] = round(iou(pbox, mbox), 3)
            row['silhouette'] = 'PASS' if row['iou'] >= 0.7 else 'FAIL'
            if mask is not None and mbox:
                st = texture_stats(frame, mask)
                row['texture'] = st
                ok = st.get('pixels', 0) >= 200 and st.get('meanLuma', 0) >= a.min_luma and st.get('blackFrac', 1) <= 0.5 \
                    and st.get('stdLuma', 0) >= 4 and st.get('twoTone', 1) <= 0.97
                row['textured'] = 'PASS' if ok else 'FAIL'
            else:
                row['textured'] = 'FAIL'
            # crop for the sheet: projected bounds box with margin
            box = cbox or mbox or (0, 0, w, h)
            mx = (box[2] - box[0]) * 0.12 + 8
            my = (box[3] - box[1]) * 0.12 + 8
            crop = frame.crop((int(max(0, box[0] - mx)), int(max(0, box[1] - my)),
                               int(min(w, box[2] + mx)), int(min(h, box[3] + my))))
            ov = crop.copy()
            dr = ImageDraw.Draw(ov)
            ox, oy = max(0, box[0] - mx), max(0, box[1] - my)
            if pbox:
                dr.rectangle((pbox[0] - ox, pbox[1] - oy, pbox[2] - ox, pbox[3] - oy), outline=(0, 255, 0))
            if mbox:
                dr.rectangle((mbox[0] - ox, mbox[1] - oy, mbox[2] - ox, mbox[3] - oy), outline=(255, 0, 255))
            # one crop per frame: a model previewed from several cameras keeps every view
            safe = re.sub(r'[^A-Za-z0-9_.-]', '_', pv['model']) + '_n%d' % pv['n']
            cp = os.path.join(a.out, 'crops', safe + '.png')
            crop.save(cp)
            ov.save(os.path.join(a.out, 'crops', safe + '.check.png'))
            row['crop'] = cp
            row['pass'] = row['engineBounds'] != 'FAIL' and row['silhouette'] == 'PASS' and row['textured'] == 'PASS'
            rows.append(row)
    json.dump({'schema': 'iwz.asset-previews/1', 'hfovScale': a.hfov_scale, 'rows': rows},
              open(os.path.join(a.out, 'previews.json'), 'w'), indent=1)
    sheet(rows, cat, a.out, a.tile, a.cols)
    npass = sum(1 for r in rows if r.get('pass'))
    print('previews: %d frames, %d pass all checks -> %s' % (len(rows), npass, a.out))


def sheet(rows, cat, out, tile, cols, name='contact_sheet'):
    rows = [r for r in rows if r.get('crop')]
    if not rows:
        return
    lab = 46
    per = cols * 6
    try:
        font = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        font = ImageFont.load_default()
    for page in range(0, len(rows), per):
        chunk = rows[page:page + per]
        nr = (len(chunk) + cols - 1) // cols
        img = Image.new('RGB', (cols * tile, nr * (tile + lab)), (24, 24, 24))
        dr = ImageDraw.Draw(img)
        for i, r in enumerate(chunk):
            x, y = (i % cols) * tile, (i // cols) * (tile + lab)
            im = Image.open(r['crop'])
            im.thumbnail((tile, tile))
            img.paste(im, (x + (tile - im.width) // 2, y + (tile - im.height) // 2))
            c = cat[r['model']]
            col = (120, 230, 120) if r.get('pass') else (240, 110, 110)
            dr.text((x + 3, y + tile + 1), r['model'][:38], fill=(235, 235, 235), font=font)
            dr.text((x + 3, y + tile + 15), '%s %s' % (','.join(c['zones'])[:16], 'x'.join('%g' % round(s) for s in c['size'])),
                    fill=(200, 200, 200), font=font)
            eb = 'n/a' if r.get('engineBounds') == 'N/A' else '%.2f' % r.get('engineBoundsDiff', -1)
            dr.text((x + 3, y + tile + 29), 'iou %.2f tex %s eb %s %s' % (
                r.get('iou', 0), (r.get('texture') or {}).get('meanLuma', '-'), eb, 'PASS' if r.get('pass') else 'FAIL'),
                fill=col, font=font)
        img.save(os.path.join(out, '%s_%02d.png' % (name, page // per)))


if __name__ == '__main__':
    main()
