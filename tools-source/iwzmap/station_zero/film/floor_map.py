r"""floor_map: the direct light of a document on its floor and its ceiling, by the baker's own formula, offline (worker L2, 28 Nov 2026).

    set STUDIO_ROOT=C:\studio  (and STUDIO_CONFIG, IWZ_SDK as the document's env.sh)
    python floor_map.py <doc folder> --region x0,y0,x1,y1 [--n 60000] [--out m.json] [--emit <emit folder>]

The design loop of the lighting lot: no game, no bake. Uses Studio's `lightwhy` (the lights of the emit as the build makes them, the triangles of its
world.bin, rays for shadows) and samples the surfaces inside the region by area. Per point the summed direct irradiance E of every light of the `on` state
(baked lights and engine lights; a baked light and a shadow-flag engine light are ray traced). It has NO albedo and no bounce: it measures the LIGHT
DISTRIBUTION, which a frame's luminance mixes with the materials.
Reported:
  floor    p10 / p50 / p90 of E on floor points, pool = p90 / p10, `pool_share` = share of floor above 2.5 x the median, `dark_share` = share under 0.35 x median,
           `cv` = std / mean (how unevenly the floor is lit)
  ceiling  mean E on ceiling points over mean E on floor points (a flat even fill lights the ceiling as much as the floor; stock's lamps light the floor)
  wall     the same for walls
  lights   the number of lights with any energy in the region, and the floor share of the five strongest
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import lightwhy as LW  # noqa: E402
from studio import Map  # noqa: E402


def measure(folder, region, n=60000, emit=None, seed=7):
    import time
    t0 = time.time()
    log = lambda *a: print('[%5.1fs]' % (time.time() - t0), *a, file=sys.stderr, flush=True)     # noqa: E731
    m = Map.load(folder)
    log('loaded')
    emit_dir, _ = LW.emit_for(m, emit)
    log('emit', emit_dir)
    lt = LW.build_lights(emit_dir, m)
    log('lights', len(lt['baked']), len(lt['runtime']))
    from studio import bake as BK
    dump = BK.template_dump()
    sc = LW.Scene(emit_dir, m, [dump] if dump else [])
    x0, y0, x1, y1 = region
    sc.zones['_region'] = [x0, y0, -2000.0, x1, y1, 2000.0]      # sample only the region: the world's other 500,000 triangles would each cost a cover ray
    log('scene', sc.world_n, 'tris')
    P, N, cls, _ = sc.sample(n, seed, '_region')
    log('sampled', len(P))
    cls = np.array(cls)
    E = np.zeros(len(P))
    per = []
    for L in lt['baked'] + lt['runtime']:
        e, parts = LW.irradiance(L, P, N)
        live = parts['inrange'] & (e > 0)
        if not live.any():
            continue
        idx = np.nonzero(live)[0]
        b, _, _ = LW._shadowed(sc, L, P[idx], N[idx])
        e = e.copy()
        e[idx[b]] = 0.0           # every light of the model is traced here (the engine's shadow flag is a build fact, reported apart)
        E += e
        per.append({'id': L.get('id'), 'state': L.get('state'), 'shadow_flag': int(bool(L.get('shadow'))),
                    'floor': float(e[cls == 'floor'].sum()), 'ceiling': float(e[cls == 'ceiling'].sum()), 'wall': float(e[cls == 'wall'].sum())})
    fl = E[(cls == 'floor') & (N[:, 2] > 0.9)]
    ce = E[cls == 'ceiling']
    wa = E[cls == 'wall']
    q = lambda v, p: float(np.percentile(v, p)) if len(v) else 0.0     # noqa: E731
    med = q(fl, 50)
    out = {'points': int(len(P)), 'floor_points': int(len(fl)),
           'floor': {'p10': round(q(fl, 10), 4), 'p50': round(med, 4), 'p90': round(q(fl, 90), 4),
                     'pool': round(q(fl, 90) / max(q(fl, 10), 1e-4), 2), 'pool_share': round(float((fl > 2.5 * med).mean()), 4) if len(fl) else 0,
                     'dark_share': round(float((fl < 0.35 * med).mean()), 4) if len(fl) else 0, 'cv': round(float(fl.std() / max(fl.mean(), 1e-6)), 3)},
           'ceiling_to_floor': round(float(ce.mean() / max(fl.mean(), 1e-6)), 3) if len(ce) else None,
           'wall_to_floor': round(float(wa.mean() / max(fl.mean(), 1e-6)), 3) if len(wa) else None,
           'lights_in_region': len(per), 'lights_total': len(lt['baked']) + len(lt['runtime']),
           'top': sorted(per, key=lambda r: -r['floor'])[:6]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('folder')
    ap.add_argument('--region', required=True)
    ap.add_argument('--n', type=int, default=9000)
    ap.add_argument('--out')
    ap.add_argument('--emit')
    a = ap.parse_args(argv)
    r = measure(a.folder, [float(v) for v in a.region.split(',')], a.n, a.emit)
    if a.out:
        json.dump(r, open(a.out, 'w'), indent=1)
    print(json.dumps(r, indent=1))


if __name__ == '__main__':
    main()
