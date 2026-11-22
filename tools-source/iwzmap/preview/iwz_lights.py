"""Runtime lights and exposure of the Station Zero preview (dark and lit state).

The emit's lightmap holds only the 56 emergency lights (the darkness bake). The 72 named lights (`lights.txt`) are runtime lights the level script switches on, and
the darkness module attaches a flashlight (a particle spot light) to every player. The engine adds them per pixel in the world shader (ENGINE-SHADERS.md section 2).
Blender's own falloff cannot be that function, so the preview adds them in numpy per pixel from three Blender passes: the radiance (lightmap, props, emission),
the world position and normal (material override) and the albedo (`--albedo-pass`).

    python iwz_preview_render.py lights --state lit  --src <emit src> --plan <plan> --frames <engine frames> --out <dir> [--flu <flashlight unit>]
    python iwz_preview_render.py lights --state dark --src <emit src> --plan <plan> --frames <engine frames> --out <dir>      (fits the flashlight unit)
"""
import json
import math
import os
import shutil

import numpy as np

import iwz_calib as C
import iwz_tonemap as TM

# The flashlight of the darkness module (a85/sdkhead/tools-source/iwzmap/darkness: README.md, build-g-dark.ps1 d16 line 2, make_vfx_light.py, cp_iwz_flashlight.gsc):
# a particle spot light on a carrier at eye + (24 forward, 4 right, 6 down) following the view angles; world copy: full cone 40 deg, inner 2 deg, radius 900,
# colour (1, 0.92, 0.80), brightness 3.5, shadow on; lit copy (after power) brightness 3.5 * 0.3; halo: full cone 64, inner 0, radius 700, brightness
# 3.5 * 0.25 (* 0.3 lit), no shadow. `brightness` goes into a record colour with an unknown unit (FLU, fitted on the dark frames).
FLASH = {'offset': (24.0, 4.0, -6.0), 'color': np.array([1.0, 0.92, 0.80], np.float32),
         'main': {'fov': 40.0, 'inner': 2.0, 'radius': 900.0, 'dark': 3.5, 'lit': 1.05},
         'halo': {'fov': 64.0, 'inner': 0.0, 'radius': 700.0, 'dark': 0.875, 'lit': 0.26}}


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


def decode_passes(pos, nrm):
    """Passes as written by iwz_preview.geometry_override: position + 100 m (the scene is in metres, S = 0.0254 per engine unit), normal * 0.5 + 0.5; background = 0."""
    hit = pos[..., 0] > 50.0
    return (pos - 100.0) / 0.0254, nrm * 2.0 - 1.0, hit


def light_term(pos, nrm, alb, lights, k=1.0, zones=None):
    """Per pixel diffuse of the runtime lights per unit of the light colour scale.
    Engine falloff (ENGINE-SHADERS.md section 2, lines 405-410): a = saturate(k (1 - d / R)); a = a^2 (3 - 2a);
    diffuse = albedo * colour * intensity * a * saturate(N.L). No shadows (63 of the 72 lights are unshadowed in the engine, the 9 shadowed ones are
    drawn unshadowed here), no specular, no sphere size. `zones`: only lights of these zones (None: all)."""
    pos, nrm, hit = decode_passes(pos, nrm)
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


def camera_basis(x, y, z, yaw, pitch, eye=60.0):
    """Eye position, forward, right, up of a plan view (gl_tp: setorigin + setplayerangles((pitch, yaw, 0)); pitch positive looks down)."""
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    fwd = np.array([cp * cy, cp * sy, -sp], np.float32)
    right = np.array([sy, -cy, 0.0], np.float32)
    up = np.cross(right, fwd).astype(np.float32)
    return np.array([x, y, z + eye], np.float32), fwd, right, up


def flash_term(pos, nrm, alb, view, state, eye=60.0):
    """Per pixel diffuse of the flashlight (main spot and halo) per unit of FLU. Spot form of the engine falloff (ENGINE-SHADERS.md section 2: cone
    = saturate(cos * scale + bias) between the outer and the inner half angle, radial smoothstep of saturate(1 - d / R)); no shadow."""
    pos, nrm, hit = decode_passes(pos, nrm)
    e, fwd, right, up = camera_basis(*view, eye=eye)
    off = FLASH['offset']
    src = e + fwd * off[0] + right * off[1] + up * off[2]
    h, w = pos.shape[:2]
    fp, fn, fa = pos.reshape(-1, 3), nrm.reshape(-1, 3), alb.reshape(-1, 3)
    valid = hit.reshape(-1)
    acc = np.zeros((h * w, 3), np.float32)
    d = fp - src
    dist = np.linalg.norm(d, axis=1)
    for part in ('main', 'halo'):
        s = FLASH[part]
        cos_o, cos_i = math.cos(math.radians(s['fov'] / 2)), math.cos(math.radians(max(s['inner'] / 2, 0.0)))
        idx = np.nonzero(valid & (dist < s['radius']))[0]
        if not len(idx):
            continue
        di = np.maximum(dist[idx], 1e-3)
        c = (d[idx] * fwd).sum(1) / di
        cone = np.clip((c - cos_o) / (cos_i - cos_o), 0, 1)
        a = np.clip(1.0 - di / s['radius'], 0, 1)
        a = a * a * (3 - 2 * a)
        ndl = np.clip((-d[idx] * fn[idx]).sum(1) / di, 0, 1)
        acc[idx] += fa[idx] * FLASH['color'][None, :] * (s[state] * a * cone * ndl)[:, None]
    return acc.reshape(h, w, 3)


def region_report(pos, nrm, lights, region, min_share=0.01):
    """Which runtime lights reach the pixels of a region (row slice, column slice) of a view and how much: (zone, position, radius, shadowed, share of the
    region's pixels inside the radius with N.L > 0, mean of a * N.L). Also the largest number of lights whose radius covers one pixel of the whole view
    (to compare with the engine's per pixel limits, ENGINE-SHADERS.md section 4)."""
    P, N, hit = decode_passes(pos, nrm)
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


def run(a, load_calib, run_blender, engine_frames, save_png):
    state = a.state
    cal = load_calib(a.calib)
    mask = C.mask_1280x720()
    plan = json.load(open(a.plan))
    names, views = [], {}
    for st in plan['steps']:
        if st.get('do') == 'tour':
            for v in st['views']:
                views[v['name']] = (v['at'][0], v['at'][1], v['at'][2], v.get('yaw', 0), v.get('pitch', 0))
                if v['name'].startswith(state + '_'):
                    names.append(v['name'])
    eng = engine_frames(a.frames, names)
    out = a.out
    os.makedirs(out, exist_ok=True)
    rd, ad = os.path.join(out, '_raw'), os.path.join(out, '_alb')
    if not (a.reuse_raw and os.path.isdir(rd) and os.path.isdir(ad)):
        shutil.rmtree(rd, ignore_errors=True)
        shutil.rmtree(ad, ignore_errors=True)
        base = ['load', a.src, '--plan', a.plan, '--views', 'plan_%s_*' % state, '--eye', str(cal['eye']), '--fov', str(cal['fov']),
                '--power', 'on' if state == 'lit' else 'off', '--prop-gain', str(a.prop_gain)]
        run_blender(base + ['--out', rd, '--aux'])
        run_blender(base + ['--out', ad, '--albedo-pass'])
    lights = parse_lights(a.src) if state == 'lit' else []
    lut = TM.load_lut()
    data = {}
    for n in eng:
        pos = np.load(os.path.join(rd, 'plan_' + n + '__pos.npy'))
        nrm = np.load(os.path.join(rd, 'plan_' + n + '__nrm.npy'))
        alb = np.load(os.path.join(ad, 'plan_' + n + '.npy'))
        data[n] = {'lm': np.load(os.path.join(rd, 'plan_' + n + '.npy')),
                   'lt': light_term(pos, nrm, alb, lights) if lights else 0.0,
                   'fl': flash_term(pos, nrm, alb, views[n], state, cal['eye']) if a.flashlight else 0.0}

    def blocks(x):
        h, w = x.shape[:2]
        return x[:h // 4 * 4, :w // 4 * 4].reshape(h // 4, 4, w // 4, 4, *x.shape[2:]).mean((1, 3))
    mlow = blocks(mask.astype(np.float32)) > 0.99
    elow = {n: np.maximum(blocks(C.lum(C.srgb_to_lin(eng[n]))), 1e-4) for n in eng}

    vision = TM.parse_vision(a.vision)
    if state == 'dark':
        vision.update({'tonemapAuto': 0.0, 'tonemapAdaptSpeed': 1.0, 'tonemapExposureAdjust': -3.0})   # the module's dark vision (build-g-dark.ps1 DarkArgs)
    elif a.lit_adjust is not None:
        vision['tonemapAutoExposureAdjust'] = a.lit_adjust

    def hdr(n, unit, flu):
        return data[n]['lm'] + unit * data[n]['lt'] + flu * data[n]['fl']

    def gain_model(x):
        return TM.exposure_gain(TM.log_average(x), vision, a.ae_factor)

    def low_err(n, x, g):
        p = np.maximum(C.lum(C.srgb_to_lin(TM.display_frame(blocks(x), g, lut))), 1e-4)
        return float(np.sqrt(np.mean((np.log(p[mlow]) - np.log(elow[n][mlow])) ** 2)))

    def fit_gain(n, x):
        """Information only: the gain that matches the median luminance of the engine frame (the exposure a per frame fit would pick)."""
        lo, hi = 1e-4, 1e2
        em = float(np.median(elow[n][mlow]))
        for _ in range(14):
            g = float(np.sqrt(lo * hi))
            p = np.maximum(C.lum(C.srgb_to_lin(TM.display_frame(blocks(x), g, lut))), 1e-4)
            lo, hi = (g, hi) if float(np.median(p[mlow])) < em else (lo, g)
        return g

    def mean_err(unit, flu):
        return float(np.mean([low_err(n, hdr(n, unit, flu), gain_model(hdr(n, unit, flu))) for n in eng]))

    unit0 = a.unit
    flu0 = a.flu if a.flu is not None else 0.0
    fit = {}
    if state == 'dark' and a.flashlight and a.flu is None:
        grid = [0.0] + list(10 ** np.linspace(-2.5, 1.5, 9))
        errs = {}
        for f in grid:
            errs[f] = mean_err(0.0, f)
            print('FLU %.3g: mean spatial rms log error %.4f' % (f, errs[f]), flush=True)
        flu0 = min(grid, key=lambda f: errs[f])
        fit['flu_errors'] = {str(k): v for k, v in errs.items()}
    if state == 'lit' and lights and unit0 is None:
        grid = [0.0] + list(10 ** np.linspace(-5.5, -1.5, 9))
        errs = {}
        for u in grid:
            errs[u] = mean_err(u, flu0)
            print('UNIT %.3g (FLU %.3g): mean spatial rms log error %.4f' % (u, flu0, errs[u]), flush=True)
        unit0 = min(grid, key=lambda u: errs[u])
        fit['unit_errors'] = {str(k): v for k, v in errs.items()}
    unit0 = unit0 or 0.0
    sbs = os.path.join(out, 'sidebyside')
    os.makedirs(sbs, exist_ok=True)
    rows = []
    for n in eng:
        eedge = C.engine_edges(eng[n], mask)
        res = {}
        for tag, unit, flu in (('before', 0.0, 0.0), ('after', unit0, flu0)):
            x = hdr(n, unit, flu)
            g = gain_model(x)
            img = TM.display_frame(x, g, lut)
            res[tag] = img
            res[tag + '_edge'] = C.edge_score(eng[n], C.srgb_to_lin(img), mask, eedge)
            res[tag + '_err'] = low_err(n, x, g)
            res[tag + '_ev'] = float(np.log2(g))
            res[tag + '_evfit'] = float(np.log2(fit_gain(n, x)))
            res[tag + '_med'] = float(np.median(C.lum(C.srgb_to_lin(img[60:330])))) / float(np.median(C.lum(C.srgb_to_lin(eng[n][60:330]))))
        rows.append({'frame': n, **{k: round(float(v), 3) for k, v in res.items() if not isinstance(v, np.ndarray)}})
        save_png(np.concatenate([res['before'], res['after'], eng[n]], 1), os.path.join(sbs, n + '_before_after_engine.png'))
    keys = ('before_edge', 'after_edge', 'before_err', 'after_err', 'before_med', 'after_med', 'before_ev', 'before_evfit', 'after_ev', 'after_evfit')
    lines = ['| frame | edge IoU before | edge IoU after | pattern err before | pattern err after | median ratio before | median ratio after | EV model before | EV fitted before | EV model after | EV fitted after |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | ' % r['frame'] + ' | '.join('%.3f' % r[k] for k in keys) + ' |')
    lines.append('| mean | ' + ' | '.join('%.3f' % np.mean([r[k] for r in rows]) for k in keys) + ' |')
    open(os.path.join(out, 'table_%s.md' % state), 'w').write(chr(10).join(lines) + chr(10))
    fit.update({'state': state, 'unit': unit0, 'flu': flu0, 'flashlight': bool(a.flashlight), 'ae_factor': a.ae_factor, 'vision': a.vision})
    json.dump({'rows': rows, 'fit': fit}, open(os.path.join(out, 'table_%s.json' % state), 'w'), indent=1)
    print(chr(10).join(lines))
    print('%s: UNIT %.3g, FLU %.3g' % (state, unit0, flu0))
