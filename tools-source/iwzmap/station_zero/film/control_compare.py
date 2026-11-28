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


# ------------------------------------------------------------------ metric (worker R2): one table, stock against ours, per region
BANDS = {'ceiling': (0.00, 0.30), 'wall': (0.30, 0.70), 'floor': (0.70, 0.97)}   # rows of the frame; floor = LIGHTING-GAP's floor band
Y709 = np.array([0.2126, 0.7152, 0.0722])


def _local_contrast(y):
    """mean absolute difference of log luminance between a pixel and its 9 x 9 box mean (texture, grime, shading detail)"""
    ly = np.log2(np.maximum(y, 1e-4))
    k = 9
    pad = np.pad(ly, k // 2, mode='edge')
    c = np.cumsum(np.cumsum(pad, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    h, w = ly.shape
    box = (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)
    return np.abs(ly - box)


def region_numbers(a):
    """per band of a frame (display-encoded 0..1 RGB): mean linear luminance, mean linear chromaticity (r, g, b sum to 1),
    local contrast (mean |log2 lum - log2 box mean|), share of pixels under 1/255 display (black); plus a 16 x 9 tile grid of log2 luminance"""
    lin = LM._lin(a)
    y = lin @ Y709
    lc = _local_contrast(y)
    h, w = y.shape
    out = {}
    for k, (r0, r1) in BANDS.items():
        sl = slice(int(r0 * h), int(r1 * h))
        m = lin[sl].reshape(-1, 3).mean(0)
        out[k] = {'lum': float(y[sl].mean()), 'chroma': [float(v) for v in m / max(m.sum(), 1e-9)],
                  'contrast': float(lc[sl].mean()), 'black': float((a[sl].max(2) <= 1.5 / 255).mean())}
    tiles = np.log2(np.maximum(y[:h // 9 * 9, :w // 16 * 16].reshape(9, h // 9, 16, w // 16).mean((1, 3)), 1e-4))
    return out, tiles


def distance(s, o, ts, to):
    """one number, 0 = the same frame statistics. Per band: |log2 luminance ratio| + 10 x chromaticity distance + |log2 contrast ratio| +
    2 x |black share difference|; averaged over the three bands; plus the mean |log2| difference of the 16 x 9 tile grid after removing the
    frames' mean level (where light falls, independent of exposure). Each term is about 1 for a clearly visible difference."""
    terms = {}
    for k in BANDS:
        a, b = s[k], o[k]
        terms[k] = (abs(np.log2(max(b['lum'], 1e-5) / max(a['lum'], 1e-5))) + 10 * float(np.linalg.norm(np.subtract(a['chroma'], b['chroma'])))
                    + abs(np.log2(max(b['contrast'], 1e-5) / max(a['contrast'], 1e-5))) + 2 * abs(b['black'] - a['black']))
    tile = float(np.abs((to - to.mean()) - (ts - ts.mean())).mean())
    d = float(np.mean(list(terms.values()))) + tile
    return d, {**{k: round(v, 3) for k, v in terms.items()}, 'tiles': round(tile, 3)}


def metric(stock, variants, names, out=None):
    """variants: [(label, dir)]. Registration is reported (shift and edge match) and flagged when the shift exceeds 8 px or the edge match is
    under 0.25: the bands assume the same eye, and a frame a quarter black registers poorly."""
    res = {}
    for name in names:
        sp = find(stock, name)
        if not sp:
            res[name] = {'missing': 'stock'}
            continue
        s = load(sp)
        sn, st = region_numbers(s)
        row = {'stock': {'file': sp, 'regions': sn}}
        for label, d in variants:
            op = find(d, name)
            if not op:
                row[label] = {'missing': d}
                continue
            o = load(op)
            if o.shape != s.shape:
                o = np.asarray(Image.open(op).convert('RGB').resize((s.shape[1], s.shape[0])), dtype=np.float64) / 255.0
            on, ot = region_numbers(o)
            dist, terms = distance(sn, on, st, ot)
            reg = register(s, o)
            reg['flag'] = bool(abs(reg['dx']) > 8 or abs(reg['dy']) > 8 or reg['stock_edges_matched_2px'] < 0.25)
            row[label] = {'file': op, 'regions': on, 'distance': round(dist, 3), 'terms': terms, 'register': reg}
        res[name] = row
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
    return res


def table(res):
    """markdown table: one row per pose and frame source"""
    L = ['| pose | frame | ceiling lum | wall lum | floor lum | floor b/r | floor contrast | black % | distance | reg dx,dy / match |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for name, row in res.items():
        for label, v in row.items():
            if not isinstance(v, dict) or 'regions' not in v:
                continue
            r = v['regions']
            bl = np.mean([r[k]['black'] for k in BANDS]) * 100
            fl = r['floor']
            reg = v.get('register')
            L.append('| %s | %s | %.4f | %.4f | %.4f | %.2f | %.3f | %.1f | %s | %s |' % (
                name, label, r['ceiling']['lum'], r['wall']['lum'], fl['lum'], fl['chroma'][2] / max(fl['chroma'][0], 1e-9), fl['contrast'], bl,
                '%.2f' % v['distance'] if 'distance' in v else '-',
                '%d,%d / %.2f%s' % (reg['dx'], reg['dy'], reg['stock_edges_matched_2px'], ' FLAG' if reg['flag'] else '') if reg else '-'))
    summ = {}
    for row in res.values():
        for label, v in row.items():
            if isinstance(v, dict) and 'distance' in v:
                summ.setdefault(label, []).append(v['distance'])
    L.append('')
    L.append('mean distance over the poses: ' + ', '.join('%s %.2f' % (k, np.mean(v)) for k, v in summ.items()))
    return '\n'.join(L)


def main(argv):
    if argv[0] == 'metric':
        # metric <out.json> <stock dir> label=dir[,label=dir...] [--names a,b,c]
        out, stock = argv[1], argv[2]
        variants = [tuple(x.split('=', 1)) for x in argv[3].split(',')]
        opt = dict(zip(argv[4::2], argv[5::2]))
        names = opt.get('--names', 'subway_east_1,subway_east_2,subway_east_5').split(',')
        res = metric(stock, variants, names, out)
        t = table(res)
        open(os.path.splitext(out)[0] + '.md', 'w', encoding='utf-8').write(t + '\n')
        print(t)
        return
    if argv[0] == 'pairs':
        out, stock, ours = argv[1], argv[2], argv[3].split(',')
        opt = dict(zip(argv[4::2], argv[5::2]))
        names = opt.get('--names', ','.join('subway_east_%d' % k for k in range(1, 9))).split(',')
        patches = json.load(open(opt['--patches'])) if '--patches' in opt else None
        pairs(out, stock, ours, names, patches)


if __name__ == '__main__':
    main(sys.argv[1:])
