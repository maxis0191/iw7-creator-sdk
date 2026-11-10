"""Flashlight pool metrics from on / off frame pairs (probe 8 flv_* frames).

For each pair: the light's own contribution d = luma(on) - luma(off) (weapon box excluded), its peak (p99.5),
pool = pixels with d > 0.25 x peak: pool area, median and p90 luma of the ON frame in the pool (target 0.35 .. 0.55),
clipped fraction (> 0.98) in the pool, and edge softness = area(d > 0.1 peak) / area(d > 0.5 peak) (a hard-rimmed disc
is close to 1, a soft falloff with a hot centre is clearly larger).

usage: dk_flpool.py <run dir> on:off [on:off ...] [--weapon-box 0.55,0.55]
"""
import argparse, os
import numpy as np
from PIL import Image


def luma(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('pairs', nargs='+')
    ap.add_argument('--weapon-box', default='0.55,0.55')
    a = ap.parse_args(argv)
    wx, wy = [float(v) for v in a.weapon_box.split(',')]
    for pr in a.pairs:
        on, off = pr.split(':')
        y1 = luma(os.path.join(a.run, 'iwzdk_%s.bmp' % on)); y0 = luma(os.path.join(a.run, 'iwzdk_%s.bmp' % off))
        h, w = y1.shape
        valid = np.ones_like(y1, bool); valid[int(h * wy):, int(w * wx):] = False
        d = np.where(valid, y1 - y0, 0)
        peak = float(np.percentile(d[valid], 99.5))
        if peak <= 0.02:
            print('%-16s no light (peak %.3f)' % (on, peak)); continue
        pool = d > 0.25 * peak
        a10 = int((d > 0.1 * peak).sum()); a50 = max(1, int((d > 0.5 * peak).sum()))
        print('%-16s peak +%.3f  pool %.3f of frame  median %.3f  p90 %.3f  clip %.4f  softness %.2f' % (
            on, peak, pool.mean(), np.median(y1[pool]), np.percentile(y1[pool], 90), (y1[pool] > 0.98).mean(), a10 / a50))


if __name__ == '__main__':
    main()
