r"""light_design: the light DESIGN numbers of a document and of frames, ours beside stock (worker L2, 28 Nov 2026).

    python light_design.py lights <doc folder | prefab.json> [--area <sq units>] [--region x0,y0,x1,y1]
    python light_design.py frames <out.json> label=<folder|png> [label=...]

lights   the light records of a Studio document (or of the control room's stock prefab, `ctl_subway_east_lay`): count, spots / omnis, share with
         shadows, share that are engine lights (runtime / bounce), the engine row of each (document intensity x 27,000 for a bounce light,
         x 1,000 for a plain runtime one; baked lights are in baker units = the document intensity and are shown as such), the radius and the cone
         (outer angle), and sources per million square units of floor (1,000 x 1,000 units) when the floor area is given or implied.
frames   per set of frames, medians over its frames, on LINEAR luminance (sRGB decoded): lum (mean), floor_ps = 90th / 10th percentile of the
         floor band (rows 70 to 97 %: the pool to shadow ratio on the floor), all_ps = 95th / 5th over the frame, contrast = the local contrast of
         control_compare (mean |log2 lum - log2 9 x 9 box mean|) of the floor band and of the whole frame, tile_sd = standard deviation of the
         16 x 9 tile grid's log2 luminance (how unevenly light falls over the frame), dark = share under 0.03 display.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

Y709 = np.array([0.2126, 0.7152, 0.0722])
BOUNCE_ROW = 27000.0
RUNTIME_ROW = 1000.0


def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _local_contrast(y):
    ly = np.log2(np.maximum(y, 1e-4))
    k = 9
    pad = np.pad(ly, k // 2, mode='edge')
    c = np.pad(np.cumsum(np.cumsum(pad, 0), 1), ((1, 0), (1, 0)))
    h, w = ly.shape
    box = (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)
    return np.abs(ly - box)


def _box_blur(y, k):
    pad = np.pad(y, k // 2, mode='edge')
    c = np.pad(np.cumsum(np.cumsum(pad, 0), 1), ((1, 0), (1, 0)))
    h, w = y.shape
    return (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)


def frame_numbers(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float64) / 255.0
    y = _lin(a) @ Y709
    h, w = y.shape
    fl = y[int(.70 * h):int(.97 * h)]
    lc = _local_contrast(y)
    tiles = np.log2(np.maximum(y[:h // 9 * 9, :w // 16 * 16].reshape(9, h // 9, 16, w // 16).mean((1, 3)), 1e-4))
    flp = _box_blur(y, 41)[int(.70 * h):int(.97 * h)]        # the floor band with texture, litter and joints blurred away: light only
    p = lambda v, q: float(np.percentile(v, q))     # noqa: E731
    return {'lum': float(y.mean()), 'ceil_lum': float(y[:int(.30 * h)].mean()), 'wall_lum': float(y[int(.30 * h):int(.70 * h)].mean()), 'floor_lum': float(fl.mean()),
            'floor_hi_share': float((fl > 4 * np.median(fl)).mean()), 'clip': float((a.max(2) >= 0.98).mean()),
            'floor_ps': p(fl, 90) / max(p(fl, 10), 1e-4), 'floor_lp_ps': p(flp, 90) / max(p(flp, 10), 1e-4),
            'ceil_over_floor': float(y[:int(.30 * h)].mean() / max(fl.mean(), 1e-6)), 'all_ps': p(y, 95) / max(p(y, 5), 1e-4),
            'floor_contrast': float(lc[int(.70 * h):int(.97 * h)].mean()), 'contrast': float(lc.mean()),
            'tile_sd': float(tiles.std()), 'dark': float((a @ Y709 < 0.03).mean())}


def frames(out, args):
    res = {}
    for arg in args:
        label, _, src = arg.partition('=')
        if os.path.isdir(src):
            files = sorted(os.path.join(src, f) for f in os.listdir(src) if f.endswith('.png') and not f.startswith(('sheet', 'diff')))
        else:
            files = [src]
        nums = {os.path.basename(f): frame_numbers(f) for f in files}
        med = {k: round(float(np.median([v[k] for v in nums.values()])), 4) for k in next(iter(nums.values()))}
        res[label] = {'n': len(nums), 'median': med, 'frames': {k: {a: round(b, 4) for a, b in v.items()} for k, v in nums.items()}}
        print(label, res[label]['n'], json.dumps(med))
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
    return res


def _doc_lights(path):
    """the light records of a document folder: (layer, record) pairs; or a prefab.json's stock lights"""
    if os.path.isfile(path):
        pre = json.load(open(path, encoding='utf-8'))
        out = []
        for L in pre['lights']:
            peak = max(L['color'])
            out.append({'src': 'stock', 'type': 'spot' if L['type'] == 2 else 'omni', 'row': peak, 'radius': L['radius'],
                        'outer': float(np.degrees(np.arccos(max(-1.0, min(1.0, L['cosHalfFovOuter']))))) if L['type'] == 2 else 180.0,
                        'shadows': bool(L.get('canUseShadowMap')), 'engine': True, 'pos': L['pos']})
        return out
    out = []
    ld = os.path.join(path, 'layers')
    for f in sorted(os.listdir(ld)):
        d = json.load(open(os.path.join(ld, f), encoding='utf-8'))
        L = d if isinstance(d, list) else d.get('objects', d)
        if isinstance(L, dict):
            L = list(L.values())
        for o in L:
            if isinstance(o, dict) and o.get('kind') == 'light' and not f.startswith('terminus'):
                bake = o.get('bake', 'baked' if not o.get('runtime') else 'runtime')
                engine = bool(o.get('runtime')) or bake in ('bounce', 'both', 'runtime')
                row = o.get('intensity', 1.0) * (BOUNCE_ROW if bake == 'bounce' else RUNTIME_ROW if engine else 1.0)
                out.append({'src': f[:-5], 'id': o.get('id'), 'type': o.get('type', 'omni'), 'row': row, 'radius': o.get('radius', 0.0),
                            'outer': float(o.get('outer', 180.0)), 'shadows': bool(o.get('shadows')), 'engine': engine, 'bake': bake,
                            'intensity': o.get('intensity', 1.0), 'pos': o.get('origin')})
    return out


def lights(path, area=None, region=None):
    L = _doc_lights(path)
    if region:
        x0, y0, x1, y1 = region
        L = [l for l in L if l.get('pos') and x0 <= l['pos'][0] <= x1 and y0 <= l['pos'][1] <= y1]
    n = len(L)
    eng = [l for l in L if l['engine']]
    q = lambda v: [round(float(np.percentile(v, p)), 3) for p in (10, 50, 90)] if v else None     # noqa: E731
    r = {'count': n, 'spots': sum(l['type'] == 'spot' for l in L), 'shadowed': sum(l['shadows'] for l in L), 'engine': len(eng),
         'radius_p10_50_90': q([l['radius'] for l in L]), 'cone_outer_p10_50_90': q([l['outer'] for l in L if l['type'] == 'spot']),
         'engine_row_p10_50_90': q([l['row'] for l in eng])}
    if path.endswith('.json'):
        r['intensity_baker_units_p10_50_90'] = q([l['row'] / BOUNCE_ROW for l in L])
    else:
        r['intensity_doc_p10_50_90'] = q([l['intensity'] for l in L])
    if area:
        r['per_million_sq'] = round(n / area * 1e6, 2)
        r['shadowed_per_million_sq'] = round(r['shadowed'] / area * 1e6, 2)
    return r


def main(argv):
    if len(argv) >= 2 and argv[0] == 'lights':
        area = region = None
        if '--area' in argv:
            area = float(argv[argv.index('--area') + 1])
        if '--region' in argv:
            region = [float(v) for v in argv[argv.index('--region') + 1].split(',')]
        print(json.dumps(lights(argv[1], area, region), indent=1))
    elif len(argv) >= 3 and argv[0] == 'frames':
        frames(argv[1], argv[2:])
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
