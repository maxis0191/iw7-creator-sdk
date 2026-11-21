"""Per-zone light contrast of a bake, offline (no game): the numbers behind "flat and evenly lit".

usage: bake_zone_contrast.py <baked dir (bake.npz)> <source dir with layout.json> [--ref <earlier report.json>]
                             [--json out.json]

Every texel of the bake (bake.npz: tx_pos, tx_n, Edir, Eind) is given to the zone whose layout box holds it and to a
surface family: floor (normal z > 0.7), ceiling (normal z < -0.7), lower wall (vertical, under floor + 110) and upper
wall (vertical, above). The irradiance E = Edir + Eind is read as luma. Per zone it prints:

  floor        median floor E (the light a player stands in)
  ceil/floor   median ceiling E over median floor E: 1 means the ceiling is as lit as the floor (a showroom); a
               station lit by downward fittings sits well under it
  upwall/floor median upper-wall E over median floor E (the same, for the walls above head height)
  pool p90/p50 floor E 90th percentile over the median: how much brighter the pools are than the typical floor
  dark share   share of the floor under a quarter of the median floor E: real darkness between the pools
  ind share    indirect share of the floor E (bounce fill; the even part of the light)
  cast         max / min of the zone's mean E channels (1.0 neutral; the colour washes of the reviews show here)

With --ref, each value is printed with the reference beside it. The bake's irradiance is not the frame: the engine
multiplies it by the albedo and tone maps it. The frames of a built map remain the proof of how it looks; this says
in seconds which way a light change moved the light before anything is built.
"""
import argparse, json, os
import numpy as np


def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def measure(baked, src):
    z = np.load(os.path.join(baked, 'bake.npz'))
    pos, n = z['tx_pos'], z['tx_n']
    if pos.ndim != 2:       # bakes before the lmbake.py fix of 21 Nov 2026 saved a file path here
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import lmbake
        pos = lmbake.texel_positions(baked, z)
    E = z['Edir'] + z['Eind']
    Y, Yi = luma(E), luma(z['Eind'])
    zones = json.load(open(os.path.join(src, 'layout.json')))['zones']
    out = {}
    for zn, zd in zones.items():
        x0, y0, z0, x1, y1, z1 = zd['box']
        m = (pos[:, 0] >= x0 - 16) & (pos[:, 0] <= x1 + 16) & (pos[:, 1] >= y0 - 16) & (pos[:, 1] <= y1 + 16) & \
            (pos[:, 2] >= z0 - 16) & (pos[:, 2] <= z1 + 16)
        if not m.any():
            continue
        fl = m & (n[:, 2] > 0.7)
        ce = m & (n[:, 2] < -0.7)
        wa = m & (np.abs(n[:, 2]) < 0.3)
        fz = np.median(pos[fl, 2]) if fl.any() else z0
        wl, wu = wa & (pos[:, 2] < fz + 110), wa & (pos[:, 2] >= fz + 110)
        med = lambda k: float(np.median(Y[k])) if k.any() else float('nan')
        f = med(fl)
        rec = {'texels': int(m.sum()), 'floor': round(f, 4),
               'ceil_floor': round(med(ce) / f, 3) if f > 0 else None,
               'upwall_floor': round(med(wu) / f, 3) if f > 0 else None,
               'lowwall_floor': round(med(wl) / f, 3) if f > 0 else None,
               'pool_p90_p50': round(float(np.percentile(Y[fl], 90) / max(f, 1e-6)), 2) if fl.any() else None,
               'dark_share': round(float((Y[fl] < 0.25 * f).mean()), 3) if fl.any() else None,
               'ind_share': round(float(Yi[fl].sum() / max(Y[fl].sum(), 1e-6)), 3) if fl.any() else None}
        c = E[m].mean(0)
        rec['cast'] = round(float(c.max() / max(c.min(), 1e-6)), 3)
        out[zn] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('baked'); ap.add_argument('src')
    ap.add_argument('--ref'); ap.add_argument('--json')
    a = ap.parse_args()
    rep = measure(a.baked, a.src)
    ref = json.load(open(a.ref))['zones'] if a.ref else {}
    keys = ('floor', 'ceil_floor', 'upwall_floor', 'pool_p90_p50', 'dark_share', 'ind_share', 'cast')
    print('%-15s' % 'zone' + ''.join('%21s' % k for k in keys))
    for zn, r in rep.items():
        cells = []
        for k in keys:
            v, w = r.get(k), ref.get(zn, {}).get(k)
            cells.append('%21s' % (('%s (was %s)' % (v, w)) if w is not None else str(v)))
        print('%-15s' % zn + ''.join(cells))
    if a.json:
        json.dump({'schema': 'iwzmap.bake-zone-contrast/1', 'baked': a.baked, 'zones': rep}, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
