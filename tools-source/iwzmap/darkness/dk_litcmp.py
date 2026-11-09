"""Lit-state comparison against a reference capture (the level builder's lit views, e.g. vision\\g27\\frames).

For every view captured by probe 8 under a prefix (lit2_, lre_, ls_<vision>_, lsc60_ ...) and present in the
reference: median luma (target |delta| <= 0.05), clipped pixels > 0.98 over the frame, and the same with the light
fixtures themselves excluded (connected clipped blobs smaller than --fixture-area of the frame: lamp lenses, tubes).
Frames are compared at the reference size. Prints one line per view and a summary per prefix; --json writes all.

usage: dk_litcmp.py <run dir> <reference dir> [--prefix lit2_ --prefix lre_ ...] [--fixture-area 0.004] [--json out]
"""
import argparse, glob, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage


def luma(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def metrics(y, fixture_area):
    clip = y > 0.98
    lab, n = ndimage.label(clip)
    big = np.zeros_like(clip)
    if n:
        sizes = ndimage.sum(clip, lab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= fixture_area * y.size]
        if keep:
            big = np.isin(lab, keep)
    return {'median': round(float(np.median(y)), 4), 'clip': round(float(clip.mean()), 4),
            'clip_ex_fixtures': round(float(big.mean()), 4)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('ref')
    ap.add_argument('--prefix', action='append', default=[])
    ap.add_argument('--fixture-area', type=float, default=0.004)
    ap.add_argument('--json', default='')
    a = ap.parse_args(argv)
    prefixes = a.prefix or ['lit2_']
    out = {'ref': a.ref, 'run': a.run, 'fixture_area': a.fixture_area, 'sets': {}}
    for pre in prefixes:
        rows = []
        for f in sorted(glob.glob(os.path.join(a.run, 'iwzdk_' + pre + '*.bmp'))):
            name = os.path.basename(f)[len('iwzdk_' + pre):-4]
            rp = os.path.join(a.ref, name + '.png')
            if not os.path.exists(rp):
                continue
            ref = Image.open(rp)
            img = Image.open(f).resize(ref.size, Image.BILINEAR)
            r = metrics(luma(ref), a.fixture_area); m = metrics(luma(img), a.fixture_area)
            row = {'view': name, 'ref': r, 'run': m, 'delta_median': round(m['median'] - r['median'], 4)}
            rows.append(row)
            print('%-6s %-18s median %.3f (ref %.3f, d %+.3f)  clip %.4f  clip ex fixtures %.4f (ref %.4f)' % (
                pre, name, m['median'], r['median'], row['delta_median'], m['clip'], m['clip_ex_fixtures'], r['clip_ex_fixtures']))
        if rows:
            d = np.array([abs(x['delta_median']) for x in rows]); c = np.array([x['run']['clip_ex_fixtures'] for x in rows])
            s = {'views': len(rows), 'mean_abs_delta': round(float(d.mean()), 4), 'within_005': int((d <= 0.05).sum()),
                 'mean_delta': round(float(np.mean([x['delta_median'] for x in rows])), 4),
                 'clip_ex_mean': round(float(c.mean()), 4), 'clip_ex_max': round(float(c.max()), 4), 'clip_ex_under_1pct': int((c < 0.01).sum())}
            out['sets'][pre] = {'summary': s, 'rows': rows}
            print('SUMMARY %-22s views %d  |d| mean %.3f  within 0.05: %d  mean d %+.3f  clip ex fixtures mean %.4f max %.4f  <1%%: %d' % (
                pre, s['views'], s['mean_abs_delta'], s['within_005'], s['mean_delta'], s['clip_ex_mean'], s['clip_ex_max'], s['clip_ex_under_1pct']))
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
