"""Runtime ("primary") lights of the Station Zero preview: the lit state.

The emit's lightmap holds only the 56 emergency lights (the darkness bake); the 72 named lights (`lights.txt`, group power / flicker) are switched on at
runtime by the level script. The engine adds them per pixel in the world shader (ENGINE-SHADERS.md section 2). Blender's own falloff cannot be that
function, so the preview adds them in numpy per pixel from three Blender passes: the radiance (lightmap, props, emission), the world position and
normal (material override) and the albedo (`--albedo-pass`).

    python iwz_preview_render.py lights --src <emit src> --plan <plan> --frames <engine frames> --out <dir>
"""
import json
import os
import shutil

import numpy as np

import iwz_calib as C
import iwz_tonemap as TM


def parse_lights(src):
    """The named runtime lights (`lights.txt`: omni x y z r g b intensity radius shadowed name= group=bank|zone|intensity|fixture)."""
    out = []
    for ln in open(os.path.join(src, 'lights.txt'), encoding='utf-8'):
        if 'name=' not in ln:
            continue
        p = ln.split()
        grp = ln.split('group=')[1].split()[0].split('|')
        out.append({'pos': np.array([float(v) for v in p[1:4]], np.float32), 'rgb': np.array([float(v) for v in p[4:7]], np.float32),
                    'intensity': float(p[7]), 'radius': float(p[8]), 'shadowed': int(p[9]), 'bank': int(grp[0]), 'zone': grp[1],
                    'fixture': grp[3] if len(grp) > 3 else ''})
    return out


def light_term(pos, nrm, alb, lights, k=1.0, zones=None):
    """Per pixel diffuse of the runtime lights per unit of the light colour scale.
    Engine falloff (ENGINE-SHADERS.md section 2, lines 405-410): a = saturate(k (1 - d / R)); a = a^2 (3 - 2a);
    diffuse = albedo * colour * intensity * a * saturate(N.L). No shadows (63 of the 72 lights are unshadowed in the engine, the 9 shadowed ones are
    drawn unshadowed here), no specular, no sphere size. `zones`: only lights of these zones (None: all)."""
    # passes as written by iwz_preview.geometry_override: position + 100 m (scene in metres, S = 0.0254 per engine unit), normal * 0.5 + 0.5; background = 0
    hit = pos[..., 0] > 50.0
    pos = (pos - 100.0) / 0.0254
    nrm = nrm * 2.0 - 1.0
    h, w = pos.shape[:2]
    valid = hit.reshape(-1)
    fp, fn, fa = pos.reshape(-1, 3), nrm.reshape(-1, 3), alb.reshape(-1, 3)
    acc = np.zeros((h * w, 3), np.float32)
    for L in lights:
        if zones is not None and L['zone'] not in zones:
            continue
        d = fp - L['pos']
        dist = np.linalg.norm(d, axis=1)
        idx = np.nonzero(valid & (dist < L['radius']))[0]
        if not len(idx):
            continue
        di = dist[idx]
        a = np.clip(k * (1.0 - di / L['radius']), 0, 1)
        a = a * a * (3 - 2 * a)
        ndl = np.clip((-d[idx] * fn[idx]).sum(1) / np.maximum(di, 1e-3), 0, 1)
        acc[idx] += fa[idx] * (L['rgb'] * L['intensity'])[None, :] * (a * ndl)[:, None]
    return acc.reshape(h, w, 3)


def run(a, load_calib, run_blender, engine_frames, save_png):
    cal = load_calib(a.calib)
    mask = C.mask_1280x720()
    plan = json.load(open(a.plan))
    names = []
    for st in plan['steps']:
        if st.get('do') == 'tour':
            names += [v['name'] for v in st['views'] if v['name'].startswith('lit_')]
    eng = engine_frames(a.frames, names)
    out = a.out
    os.makedirs(out, exist_ok=True)
    rd, ad = os.path.join(out, '_raw'), os.path.join(out, '_alb')
    if not (a.reuse_raw and os.path.isdir(rd) and os.path.isdir(ad)):
        shutil.rmtree(rd, ignore_errors=True)
        shutil.rmtree(ad, ignore_errors=True)
        base = ['load', a.src, '--plan', a.plan, '--views', 'plan_lit_*', '--eye', str(cal['eye']), '--fov', str(cal['fov']), '--power', 'on',
                '--prop-gain', str(a.prop_gain)]
        run_blender(base + ['--out', rd, '--aux'])
        run_blender(base + ['--out', ad, '--albedo-pass'])
    lights = parse_lights(a.src)
    lut = TM.load_lut()
    data = {}
    for n in eng:
        data[n] = {'lm': np.load(os.path.join(rd, 'plan_' + n + '.npy')),
                   'lt': light_term(np.load(os.path.join(rd, 'plan_' + n + '__pos.npy')), np.load(os.path.join(rd, 'plan_' + n + '__nrm.npy')),
                                    np.load(os.path.join(ad, 'plan_' + n + '.npy')), lights)}
    msk = C.mask_1280x720()

    def blocks(a):
        h, w = a.shape[:2]
        return a[:h // 4 * 4, :w // 4 * 4].reshape(h // 4, 4, w // 4, 4, *a.shape[2:]).mean((1, 3))
    mlow = blocks(msk.astype(np.float32)) > 0.99
    elow = {n: np.maximum(blocks(C.lum(C.srgb_to_lin(eng[n]))), 1e-4) for n in eng}

    def preview_low(n, unit, gain):
        x = (data[n]['lm'] + unit * data[n]['lt'])
        x = blocks(x)
        return np.maximum(C.lum(C.srgb_to_lin(TM.display_frame(x, gain, lut))), 1e-4)

    def fit_exposure(n, unit):
        """The exposure of this frame (auto exposure: not modelled): the gain that makes the median luminance of the preview equal the engine's. -> gain, rms log error of the spatial pattern."""
        lo, hi = 1e-4, 1e2
        em = float(np.median(elow[n][mlow]))
        for _ in range(14):
            g = float(np.sqrt(lo * hi))
            lo, hi = (g, hi) if float(np.median(preview_low(n, unit, g)[mlow])) < em else (lo, g)
        p = preview_low(n, unit, g)
        return g, float(np.sqrt(np.mean((np.log(p[mlow]) - np.log(elow[n][mlow])) ** 2)))

    vision = TM.parse_vision(a.vision)
    if a.lit_adjust is not None:
        vision['tonemapAutoExposureAdjust'] = a.lit_adjust

    def model_exposure(n, unit):
        """Steady state auto exposure of the engine from the frame's own log average luminance and the vision (iwz_tonemap.exposure_gain). No per frame parameter.
        -> gain, rms log error of the spatial pattern."""
        x = data[n]['lm'] + unit * data[n]['lt']
        g = TM.exposure_gain(TM.log_average(x), vision, a.ae_factor)
        p = preview_low(n, unit, g)
        return g, float(np.sqrt(np.mean((np.log(p[mlow]) - np.log(elow[n][mlow])) ** 2)))

    exposure = fit_exposure if a.fit_exposure else model_exposure
    units = [0.0] + list(10 ** np.linspace(-5.5, -1.5, 9))
    errs = {}
    for u in units:
        errs[u] = float(np.mean([exposure(n, u)[1] for n in eng]))
        print('unit %.3g: mean spatial rms log error %.4f' % (u, errs[u]), flush=True)
    ubest = min(units, key=lambda u: errs[u])
    sbs = os.path.join(out, 'sidebyside')
    os.makedirs(sbs, exist_ok=True)
    rows = []
    for n in eng:
        eedge = C.engine_edges(eng[n], mask)
        res = {}
        for tag, unit in (('before', 0.0), ('after', ubest)):
            g, e = exposure(n, unit)
            gf, _ = fit_exposure(n, unit)
            res[tag + '_evfit'] = float(np.log2(gf))
            x = data[n]['lm'] + unit * data[n]['lt']
            img = TM.display_frame(x, g, lut)
            res[tag] = img
            res[tag + '_edge'] = C.edge_score(eng[n], C.srgb_to_lin(img), mask, eedge)
            res[tag + '_err'] = e
            res[tag + '_ev'] = float(np.log2(g))
        rows.append({'frame': n, **{k: round(float(v), 3) for k, v in res.items() if not isinstance(v, np.ndarray)}})
        save_png(np.concatenate([res['before'], res['after'], eng[n]], 1), os.path.join(sbs, n + '_before_after_engine.png'))
    keys = ('before_edge', 'after_edge', 'before_err', 'after_err', 'before_ev', 'before_evfit', 'after_ev', 'after_evfit')
    lines = ['| frame | edge IoU before | edge IoU after | pattern rms log err before | pattern rms log err after | EV used before | EV fitted before | EV used after | EV fitted after |',
             '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | ' % r['frame'] + ' | '.join('%.3f' % r[k] for k in keys) + ' |')
    lines.append('| mean | ' + ' | '.join('%.3f' % np.mean([r[k] for r in rows]) for k in keys) + ' |')
    open(os.path.join(out, 'table_lit.md'), 'w').write(chr(10).join(lines) + chr(10))
    json.dump({'rows': rows, 'unit_errors': {str(k): v for k, v in errs.items()}, 'unit': ubest}, open(os.path.join(out, 'table_lit.json'), 'w'), indent=1)
    print(chr(10).join(lines))
    print('lit: UNIT %.3g (0 = no runtime lights)' % ubest)


def region_report(pos, nrm, lights, region, min_share=0.01):
    """Which runtime lights reach the pixels of a region (row slice, column slice) of a view and how much: (zone, position, radius, shadowed, share of the
    region's pixels inside the radius with N.L > 0, mean of a * N.L). Also the largest number of lights whose radius covers one pixel of the whole view
    (to compare with the engine's per pixel limits, ENGINE-SHADERS.md section 4)."""
    hit = pos[..., 0] > 50.0
    P = ((pos - 100.0) / 0.0254)
    N = nrm * 2.0 - 1.0
    sel = hit[region]
    p, n = P[region][sel], N[region][sel]
    rows = []
    for l in lights:
        d = p - l['pos']
        dist = np.linalg.norm(d, axis=1)
        a = np.clip(1 - dist / l['radius'], 0, 1)
        a = a * a * (3 - 2 * a)
        w = a * np.clip((-d * n).sum(1) / np.maximum(dist, 1e-3), 0, 1)
        if (w > 0).mean() > min_share:
            rows.append((l['zone'], l['pos'].tolist(), l['radius'], l['shadowed'], round(float((w > 0).mean()), 3), round(float(w.mean()), 4)))
    cnt = np.zeros(int(hit.sum()), int)
    fp = P[hit]
    for l in lights:
        cnt += np.linalg.norm(fp - l['pos'], axis=1) < l['radius']
    return sorted(rows, key=lambda r: -r[5]), int(cnt.max()), float(cnt.mean())
