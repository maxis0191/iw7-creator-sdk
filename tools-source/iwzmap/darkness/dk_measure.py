"""Darkness / flashlight measurements on runner frames (capture_frame BMPs) and fxperf frame times.

Per frame (luma = Rec.709 of the sRGB pixel values / 255, after a 7x7 box blur that removes IW7 film grain):
  - median / mean / p95 luma of the frame, with the first-person weapon area masked (lower right, --weapon-mask);
  - the flashlight pool: pixels brighter than max(3 x outside median, outside median + 0.04); pool area fraction,
    pool mean luma, pool centroid offset from the image centre (does the light follow the view?);
  - "outside" = the frame minus the pool and the weapon mask: median and p10 / p90 luma (target 0.02 .. 0.05);
  - contrast = pool mean / outside median.
Pairs (--pair a:b) report the per-pixel mean luma change and the fraction of pixels that changed by > 0.03 between
two frames (dark vs lit, power transition steps, other players' lights on vs off).
fxperf (--perf <file> --phases "1=lit,2=dark,...") adds mean / p95 / p99 frame time per phase.

usage: dk_measure.py <run dir> [--frames 'dk_*'] [--pair a:b ...] [--perf f --phases ...] [--json out] [--sheet out.jpg]
"""
import argparse, fnmatch, glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw


def luma_of(path):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    y = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    # 7x7 box blur (separable cumulative sums)
    k = 3
    p = np.pad(y, k, mode='edge')
    c = np.cumsum(np.cumsum(p, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * k + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s / (n * n)


def weapon_mask(h, w, spec):
    m = np.zeros((h, w), bool)
    if spec:
        x0, y0 = (float(v) for v in spec.split(','))
        m[int(h * y0):, int(w * x0):] = True
    return m


def measure(path, wm_spec):
    y = luma_of(path)
    h, w = y.shape
    wm = weapon_mask(h, w, wm_spec)
    valid = ~wm
    med0 = float(np.median(y[valid]))
    thr = max(3.0 * med0, med0 + 0.04)
    pool = (y > thr) & valid
    out = valid & ~pool
    r = {'frame': os.path.basename(path), 'w': w, 'h': h,
         'median': round(med0, 4), 'mean': round(float(y[valid].mean()), 4), 'p95': round(float(np.percentile(y[valid], 95)), 4),
         'pool_frac': round(float(pool.sum()) / valid.sum(), 4), 'threshold': round(thr, 4)}
    if pool.sum() > 50:
        ys, xs = np.nonzero(pool)
        r.update(pool_clip=round(float((y[pool] > 0.98).mean()), 4), pool_median=round(float(np.median(y[pool])), 4))
        r.update(pool_mean=round(float(y[pool].mean()), 4), pool_p90=round(float(np.percentile(y[pool], 90)), 4),
                 pool_cx=round(float(xs.mean()) / w - 0.5, 3), pool_cy=round(float(ys.mean()) / h - 0.5, 3))
    # haze: a fog veil lifts the dark end and flattens local contrast (upper two thirds: no weapon, no floor at feet)
    top = y[: int(h * 2 / 3)]
    bs = 16
    hh, ww = (top.shape[0] // bs) * bs, (top.shape[1] // bs) * bs
    blocks = top[:hh, :ww].reshape(hh // bs, bs, ww // bs, bs).swapaxes(1, 2).reshape(-1, bs * bs)
    r['veil_p5'] = round(float(np.percentile(top, 5)), 4)
    r['local_contrast'] = round(float(blocks.std(axis=1).mean()), 4)
    r['clip_frac'] = round(float((y[valid] > 0.98).mean()), 5)
    if out.sum():
        o = y[out]
        r.update(out_median=round(float(np.median(o)), 4), out_p10=round(float(np.percentile(o, 10)), 4),
                 out_p90=round(float(np.percentile(o, 90)), 4), out_black_frac=round(float((o < 0.005).mean()), 4))
        if 'pool_mean' in r and r['out_median'] > 0:
            r['contrast'] = round(r['pool_mean'] / r['out_median'], 2)
    return r, y


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--frames', default='*')
    ap.add_argument('--weapon-mask', default='0.55,0.55', help="x0,y0 fractions of the masked lower-right weapon box ('' = none)")
    ap.add_argument('--pair', action='append', default=[])
    ap.add_argument('--perf', default=''); ap.add_argument('--phases', default='')
    ap.add_argument('--json', default=''); ap.add_argument('--sheet', default='')
    a = ap.parse_args(argv)
    files = sorted(f for f in glob.glob(os.path.join(a.run, '*.bmp')) if fnmatch.fnmatch(os.path.basename(f)[:-4], a.frames))
    res, lum = [], {}
    for f in files:
        r, y = measure(f, a.weapon_mask)
        res.append(r); lum[os.path.basename(f)[:-4]] = y
        print('%-36s med %.3f pool %.3f@%.3f clip %s out %s contrast %s cx %s veil %.3f lc %.4f' % (r['frame'], r['median'], r['pool_frac'],
              r.get('pool_mean', 0), r.get('pool_clip', '-'), r.get('out_median', '-'), r.get('contrast', '-'), r.get('pool_cx', '-'),
              r['veil_p5'], r['local_contrast']))
    pairs = []
    for p in a.pair:
        x, z = p.split(':')
        if x in lum and z in lum and lum[x].shape == lum[z].shape:
            d = lum[z] - lum[x]
            pairs.append({'a': x, 'b': z, 'mean_delta': round(float(d.mean()), 4), 'changed_frac': round(float((np.abs(d) > 0.03).mean()), 4),
                          'brighter_frac': round(float((d > 0.03).mean()), 4)})
            print('PAIR %s -> %s mean %+.4f changed %.3f' % (x, z, pairs[-1]['mean_delta'], pairs[-1]['changed_frac']))
    perf = []
    if a.perf and os.path.exists(a.perf):
        names = dict(kv.split('=') for kv in a.phases.split(',') if kv)
        for line in open(a.perf):
            t = line.split()
            if len(t) >= 14 and t[0] == 'phase':
                perf.append({'phase': int(t[1]), 'name': names.get(t[1], t[1]), 'frames': int(t[3]), 'mean_ms': float(t[5]),
                             'p50_ms': float(t[7]), 'p95_ms': float(t[9]), 'p99_ms': float(t[11]), 'max_ms': float(t[13])})
        for p in perf:
            print('PERF %-12s frames %6d mean %.3f p95 %.3f p99 %.3f' % (p['name'], p['frames'], p['mean_ms'], p['p95_ms'], p['p99_ms']))
    if a.json:
        json.dump({'frames': res, 'pairs': pairs, 'perf': perf}, open(a.json, 'w'), indent=1)
    if a.sheet and files:
        tw, th = 384, 216
        cols = 4
        rows = (len(files) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * tw, rows * (th + 16)), (32, 32, 32))
        dr = ImageDraw.Draw(sheet)
        for k, f in enumerate(files):
            im = Image.open(f).convert('RGB').resize((tw, th))
            x, yv = (k % cols) * tw, (k // cols) * (th + 16)
            sheet.paste(im, (x, yv + 16))
            r = res[k]
            dr.text((x + 2, yv + 2), '%s out %.3f pool %.3f' % (r['frame'][:28], r.get('out_median', 0), r.get('pool_mean', 0)), fill=(255, 255, 0))
        sheet.save(a.sheet, quality=90)


if __name__ == '__main__':
    main()
