"""Drawn / textured / lit check of the train kit from A/B frames (iwzt_<view>.bmp with the kit, iwzt_<view>_off.bmp
without), in the spirit of SDK kit_proof.py.

usage: train_proof.py <run dir> [--json out.json]
Per view: the kit mask = pixels that change by more than 30 (RGB sum) between the two frames, cleaned of isolated
pixels; drawn = mask share; textured = luma standard deviation inside the mask (a flat or missing texture gives a
low value); lit = mean luma inside the mask and the share of near-black pixels (< 12/255). Verdicts: drawn >= 0.02,
textured std >= 6, lit mean >= 28 and black share <= 0.35.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)


def main():
    run = sys.argv[1]
    out = []
    for on in sorted(glob.glob(os.path.join(run, 'iwzt_*.bmp'))):
        if on.endswith('_off.bmp'):
            continue
        off = on[:-4] + '_off.bmp'
        if not os.path.exists(off):
            continue
        a, b = load(on), load(off)
        m = np.abs(a - b).sum(2) > 30
        # drop isolated changed pixels (zombies / particles still differ): 3x3 majority
        k = sum(np.roll(np.roll(m, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) >= 6
        luma = a @ np.array([0.299, 0.587, 0.114], np.float32)
        sel = luma[k]
        r = {'view': os.path.basename(on)[5:-4], 'drawn': round(float(k.mean()), 3)}
        if sel.size:
            r.update(textured_std=round(float(sel.std()), 1), lit_mean=round(float(sel.mean()), 1),
                     black_share=round(float((sel < 12).mean()), 3))
        r['pass'] = bool(sel.size and r['drawn'] >= 0.02 and r['textured_std'] >= 6 and r['lit_mean'] >= 28 and r['black_share'] <= 0.35)
        out.append(r)
        print('%-22s drawn %.3f  std %s  mean %s  black %s  %s' % (r['view'], r['drawn'], r.get('textured_std'), r.get('lit_mean'),
                                                                r.get('black_share'), 'PASS' if r['pass'] else 'FAIL'))
    if '--json' in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
