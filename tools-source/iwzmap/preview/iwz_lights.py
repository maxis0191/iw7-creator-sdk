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
    h, w = pos.shape[:2]
    valid = (np.linalg.norm(nrm, axis=-1) > 0.5).reshape(-1)
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
    S = 4
    data = {}
    for n in eng:
        data[n] = {'lm': np.load(os.path.join(rd, 'plan_' + n + '.npy')),
                   'lt': light_term(np.load(os.path.join(rd, 'plan_' + n + '__pos.npy')), np.load(os.path.join(rd, 'plan_' + n + '__nrm.npy')),
                                    np.load(os.path.join(ad, 'plan_' + n + '.npy')), lights)}
    up = (slice(60, 330), slice(None))

    def lav(x):
        return float(np.exp(np.log(np.maximum(C.lum(x), 1e-5)).mean()))

    def frame(n, unit, kg, full=False):
        x = data[n]['lm'] + unit * data[n]['lt']
        x = x if full else x[::S, ::S]
        g = min(1.0, kg / lav(x))
        return TM.display_frame(x, g, lut), g

    emed = {n: float(np.median(C.lum(C.srgb_to_lin(eng[n][up])))) for n in eng}

    def med_up(img):
        return float(np.median(C.lum(C.srgb_to_lin(img[60 // S:330 // S, :]))))

    def err(unit, kg):
        return float(np.sqrt(np.mean([np.log(max(med_up(frame(n, unit, kg)[0]), 1e-6) / emed[n]) ** 2 for n in eng])))
    units = 10 ** np.linspace(-6, -1, 21)
    kgs = 10 ** np.linspace(-3, 0, 25)
    best0 = min((err(0.0, kg), kg) for kg in kgs)
    best1 = min((err(u, kg), u, kg) for u in units for kg in kgs)
    sbs = os.path.join(out, 'sidebyside')
    os.makedirs(sbs, exist_ok=True)
    rows = []
    for n in eng:
        eedge = C.engine_edges(eng[n], mask)
        res = {}
        for tag, unit, kg in (('before', 0.0, best0[1]), ('after', best1[1], best1[2])):
            img, g = frame(n, unit, kg, full=True)
            res[tag] = img
            res[tag + '_edge'] = C.edge_score(eng[n], C.srgb_to_lin(img), mask, eedge)
            res[tag + '_mean'] = C.mean_lum(C.srgb_to_lin(img), mask) / C.mean_lum(C.srgb_to_lin(eng[n]), mask)
            res[tag + '_med'] = float(np.median(C.lum(C.srgb_to_lin(img[up])))) / emed[n]
            res[tag + '_gain'] = g
        rows.append({'frame': n, **{k: round(float(v), 3) for k, v in res.items() if not isinstance(v, np.ndarray)}})
        save_png(np.concatenate([res['before'], res['after'], eng[n]], 1), os.path.join(sbs, n + '_before_after_engine.png'))
    keys = ('before_edge', 'after_edge', 'before_med', 'after_med', 'before_mean', 'after_mean', 'after_gain')
    lines = ['| frame | edge IoU before | edge IoU after | median ratio before | median ratio after | mean ratio before | mean ratio after | auto gain after |',
             '|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | ' % r['frame'] + ' | '.join('%.3f' % r[k] for k in keys) + ' |')
    lines.append('| mean | ' + ' | '.join('%.3f' % np.mean([r[k] for r in rows]) for k in keys) + ' |')
    open(os.path.join(out, 'table_lit.md'), 'w').write(chr(10).join(lines) + chr(10))
    json.dump({'rows': rows, 'before': best0, 'after': best1}, open(os.path.join(out, 'table_lit.json'), 'w'), indent=1)
    print(chr(10).join(lines))
    print('lit: before rms log median error %.3f (KG %.4f); after %.3f (UNIT %.3g, KG %.4f)' % (best0[0], best0[1], best1[0], best1[1], best1[2]))
