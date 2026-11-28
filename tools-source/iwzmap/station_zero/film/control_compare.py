r"""control_compare: stock frame against our frame of the same eye (worker C1, 28 Nov 2026).

    python control_compare.py pairs <out dir> <stock dir> <ours dir>[,<ours dir 2>] [--names subway_east_1,...] [--patches patches.json]

For every name: <stock dir>/<name>.png and <ours dir>/ctl_<name>.png (or <name>.png).
  pairs    <out>/<name>.jpg: stock left, ours right (a third panel per extra ours dir), labelled, 1280 x 720 each
  numbers  light_measure.numbers of each frame (p5, p50, p95, p99, dark, clip, floor band)
  register the shift (dx, dy in pixels) of our frame against stock by phase correlation of the two edge maps, and the share of stock's strong
           edges that have an edge of ours within 2 pixels: the same eye and the same field of view give a shift near 0 and a high share
  patches  {name: {label: [x0, y0, x1, y1] (fractions of the frame)}}: linear mean luminance of each box on both frames and the ratio of a box to
           the box named `ref` (an exposure cannot move a ratio of two boxes of the same frame: the ratios compare shadow and contrast, not level)
Writes <out>/compare.json.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import light_measure as LM  # noqa: E402


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.float64) / 255.0


def lum(a):
    return a @ np.array([0.2126, 0.7152, 0.0722])


def edges(y):
    gx = np.zeros_like(y)
    gy = np.zeros_like(y)
    gx[:, 1:-1] = y[:, 2:] - y[:, :-2]
    gy[1:-1, :] = y[2:, :] - y[:-2, :]
    return np.hypot(gx, gy)


def phase_shift(a, b):
    """shift of b against a (pixels): the peak of the normalised cross power spectrum"""
    A = np.fft.fft2(a - a.mean())
    Bf = np.fft.fft2(b - b.mean())
    R = A * np.conj(Bf)
    R /= np.maximum(np.abs(R), 1e-12)
    r = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    h, w = r.shape
    dy = iy if iy <= h // 2 else iy - h
    dx = ix if ix <= w // 2 else ix - w
    return int(-dx), int(-dy), float(r.max())


def register(stock, ours):
    es, eo = edges(lum(stock)), edges(lum(ours))
    dx, dy, peak = phase_shift(es, eo)
    ts = np.percentile(es, 95)
    to = np.percentile(eo, 90)
    strong = es >= ts
    near = eo >= to
    # dilate ours' edges by 2 pixels
    d = near.copy()
    for sy in range(-2, 3):
        for sx in range(-2, 3):
            d |= np.roll(np.roll(near, sy, 0), sx, 1)
    share = float((strong & d).sum() / max(strong.sum(), 1))
    return {'dx': dx, 'dy': dy, 'peak': round(peak, 4), 'stock_edges_matched_2px': round(share, 3)}


def patch_means(a, boxes):
    lin = LM._lin(a)
    h, w, _ = a.shape
    out = {}
    for k, (x0, y0, x1, y1) in boxes.items():
        p = lin[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].reshape(-1, 3).mean(0)
        out[k] = {'lum': round(float(p @ np.array([0.2126, 0.7152, 0.0722])), 5), 'b_r': round(float(p[2] / max(p[0], 1e-6)), 3)}
    if 'ref' in out:
        for k in out:
            out[k]['to_ref'] = round(out[k]['lum'] / max(out['ref']['lum'], 1e-6), 3)
    return out


def panel(paths, labels, out, boxes=None):
    ims = [Image.open(p).convert('RGB').resize((1280, 720)) for p in paths]
    W = Image.new('RGB', (1280 * len(ims), 720 + 36), (16, 16, 16))
    dr = ImageDraw.Draw(W)
    try:
        f = ImageFont.truetype('consola.ttf', 22)
    except OSError:
        f = ImageFont.load_default()
    for i, (im, lb) in enumerate(zip(ims, labels)):
        W.paste(im, (1280 * i, 36))
        dr.text((1280 * i + 8, 6), lb, fill=(255, 230, 80), font=f)
        for k, (x0, y0, x1, y1) in (boxes or {}).items():
            dr.rectangle([1280 * i + x0 * 1280, 36 + y0 * 720, 1280 * i + x1 * 1280, 36 + y1 * 720], outline=(0, 255, 255), width=2)
            dr.text((1280 * i + x0 * 1280 + 3, 36 + y0 * 720 + 2), k, fill=(0, 255, 255), font=f)
    W.save(out, quality=92)


def find(d, name):
    for n in ('ctl_' + name + '.png', name + '.png'):
        p = os.path.join(d, n)
        if os.path.isfile(p):
            return p
    return None


def pairs(out, stock, ours_dirs, names, patches):
    os.makedirs(out, exist_ok=True)
    res = {}
    for name in names:
        sp = find(stock, name)
        ops = [find(d, name) for d in ours_dirs]
        if not sp or not all(ops):
            res[name] = {'missing': [p for p in [sp] + ops if not p]}
            continue
        s = load(sp)
        row = {'stock': {'file': sp, **LM.numbers(sp, front=False)}}
        boxes = (patches or {}).get(name)
        if boxes:
            row['stock']['patches'] = patch_means(s, boxes)
        for d, op in zip(ours_dirs, ops):
            key = os.path.basename(os.path.dirname(op)) if os.path.basename(os.path.dirname(op)) not in ('on', 'base') else os.path.basename(os.path.dirname(os.path.dirname(op)))
            o = load(op)
            row[key] = {'file': op, **LM.numbers(op, front=False), 'register': register(s, o)}
            if boxes:
                row[key]['patches'] = patch_means(o, boxes)
        labels = ['STOCK cp_disco %s' % name] + ['OURS %s' % os.path.relpath(p, os.path.dirname(os.path.dirname(os.path.dirname(p)))) for p in ops]
        panel([sp] + ops, labels, os.path.join(out, name + '.jpg'), boxes)
        res[name] = row
    json.dump(res, open(os.path.join(out, 'compare.json'), 'w', encoding='utf-8'), indent=1)
    for name, row in res.items():
        print(name)
        for k, v in row.items():
            if isinstance(v, dict) and 'p50' in v:
                print('  %-12s p5 %.3f p50 %.3f p99 %.3f floor %.3f dark %.3f %s' % (k, v['p5'], v['p50'], v['p99'], v['floor'], v['dark'],
                                                                              v.get('register', '')))
    return res


def main(argv):
    if argv[0] == 'pairs':
        out, stock, ours = argv[1], argv[2], argv[3].split(',')
        opt = dict(zip(argv[4::2], argv[5::2]))
        names = opt.get('--names', ','.join('subway_east_%d' % k for k in range(1, 9))).split(',')
        patches = json.load(open(opt['--patches'])) if '--patches' in opt else None
        pairs(out, stock, ours, names, patches)


if __name__ == '__main__':
    main(sys.argv[1:])
