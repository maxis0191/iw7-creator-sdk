r"""bake_probe: what a bake stored on the floor of a region, from its bake.npz (the SDK baker's per-texel record) (worker C1, 28 Nov 2026).

    python bake_probe.py <out.json> --box x0,y0,z0,x1,y1,z1 [--wall x=-2160|y=4300 ...] [--feet <smodels.txt>] <baked dir> [<baked dir> ...]

<baked dir> = a `studio bake --keep` folder (holds bake.npz). Floor texels = texels in the box whose normal points up (n.z > 0.7).
  floor     count, texel size, mean and 10th percentile of the stored irradiance E = Edir + Eind (luminance, baker units), mean ao
  wall      per --wall plane: the floor's mean E in bands of distance from the plane (0-4, 4-8, 8-16, 16-32, 32-64, 64-128 units) and the ratio
            of the first band to the 64-128 band (a contact shadow at the wall's foot makes it < 1)
  feet      per --feet smodels.txt: the floor texels within 6 units of a static model's origin footprint (models standing in the box) against the
            texels 24 to 48 units away: the ratio (a prop that throws a baked shadow makes it < 1)
"""
import json
import math
import os
import sys

import numpy as np

W = np.array([0.2126, 0.7152, 0.0722])


def load(d):
    z = np.load(os.path.join(d, 'bake.npz'))
    E = z['Edir'] + z['Eind']
    E = E @ W if E.ndim == 2 else E
    return {'pos': z['tx_pos'], 'n': z['tx_n'], 'E': E, 'ao': z['ao'] if 'ao' in z.files else None}


def floor_sel(b, box):
    p, n = b['pos'], b['n']
    return (p[:, 0] >= box[0]) & (p[:, 0] <= box[3]) & (p[:, 1] >= box[1]) & (p[:, 1] <= box[4]) & (p[:, 2] >= box[2]) & (p[:, 2] <= box[5]) & (n[:, 2] > 0.7)


def spacing(p):
    if len(p) < 3:
        return None
    q = p[np.random.default_rng(0).choice(len(p), min(400, len(p)), replace=False)]
    d = np.sqrt(((q[:, None, :2] - p[None, :, :2]) ** 2).sum(-1))
    d[d < 1e-6] = np.inf
    return round(float(np.median(d.min(1))), 2)


def probe(d, box, walls, feet):
    b = load(d)
    s = floor_sel(b, box)
    p, E = b['pos'][s], b['E'][s]
    out = {'dir': d, 'floor_texels': int(s.sum()), 'texel_spacing': spacing(p), 'E_mean': round(float(E.mean()), 4) if len(E) else None,
           'E_p10': round(float(np.percentile(E, 10)), 4) if len(E) else None}
    if b['ao'] is not None and len(E):
        out['ao_mean'] = round(float(b['ao'][s].mean()), 4)
    for w in walls:
        ax, v = w.split('=')
        k = 0 if ax == 'x' else 1
        dist = np.abs(p[:, k] - float(v))
        bands = [(0, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128)]
        row = {}
        for a, c in bands:
            m = (dist >= a) & (dist < c)
            row['%d-%d' % (a, c)] = [int(m.sum()), round(float(E[m].mean()), 4) if m.any() else None]
        if row['0-4'][1] is not None and row['64-128'][1]:
            row['foot_to_open'] = round(row['0-4'][1] / row['64-128'][1], 3)
        elif row['4-8'][1] is not None and row['64-128'][1]:
            row['foot_to_open'] = round(row['4-8'][1] / row['64-128'][1], 3)
        out['wall_' + w] = row
    if feet:
        near_all, far_all, n_props = [], [], 0
        for ln in open(feet, encoding='utf-8'):
            t = ln.split()
            if len(t) < 8:
                continue
            o = [float(x) for x in t[1:4]]
            if not (box[0] <= o[0] <= box[3] and box[1] <= o[1] <= box[4] and box[2] <= o[2] <= box[5]):
                continue
            dd = np.hypot(p[:, 0] - o[0], p[:, 1] - o[1])
            near, far = E[dd < 6.0], E[(dd >= 24.0) & (dd < 48.0)]
            if len(near) and len(far):
                n_props += 1
                near_all.append(near.mean())
                far_all.append(far.mean())
        if n_props:
            out['feet'] = {'props': n_props, 'E_near_mean': round(float(np.mean(near_all)), 4), 'E_24_48_mean': round(float(np.mean(far_all)), 4),
                           'near_to_far': round(float(np.mean(near_all) / max(np.mean(far_all), 1e-9)), 3)}
    return out


def main(argv):
    out = argv[0]
    i = 1
    box, walls, feet, dirs = None, [], None, []
    while i < len(argv):
        if argv[i] == '--box':
            box = [float(v) for v in argv[i + 1].split(',')]
            i += 2
        elif argv[i] == '--wall':
            walls.append(argv[i + 1])
            i += 2
        elif argv[i] == '--feet':
            feet = argv[i + 1]
            i += 2
        else:
            dirs.append(argv[i])
            i += 1
    res = [probe(d, box, walls, feet) for d in dirs]
    json.dump({'box': box, 'walls': walls, 'feet': feet, 'bakes': res}, open(out, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
