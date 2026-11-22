"""Render Station Zero views with Blender in the background and compare them with engine frames.

    python iwz_preview_render.py render    --src <emit src> --out <dir> [--views a,b|all|prefix*] [--plan PLAN.json]
    python iwz_preview_render.py calibrate --src <emit src> --plan PLAN.json --frames <dir of lit_*_1.png> --out <dir>
    python iwz_preview_render.py props     --src <emit src> --plan PLAN.json --frames <dir> --out <dir>      (fits prop_gain)

render     loads the scene once (Blender -b), renders the views, tone maps with calibration.json (next to this file
           or --calib) and writes PNGs. Prints seconds per stage.
calibrate  the acceptance test: renders the plan's engine camera views, fits ONE global (eye height, horizontal fov)
           by edge IoU against the engine frames, then ONE global exposure / gamma by the mean luminance of all frames,
           writes calibration.json, side-by-side PNGs and the before / after table (table.md, table.json).
Environment: IWZ_BLENDER (blender.exe), IWZ_RUNTIME, IWZ_GAME_ROOT (imagefile*.pak), IWZ_TEXCONV; see iwz_assets.py.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iwz_calib as C  # noqa: E402
import iwz_tonemap as TM  # noqa: E402

CALIB = os.path.join(HERE, 'calibration.json')


def blender_exe():
    e = os.environ.get('IWZ_BLENDER')
    if e:
        return e
    for c in (r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe', r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe',
              r'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'):
        if os.path.isfile(c):
            return c
    raise SystemExit('Blender not found: set IWZ_BLENDER')


def run_blender(args, quiet=True):
    t = time.time()
    cmd = [blender_exe(), '-b', '--factory-startup', '--python', os.path.join(HERE, 'iwz_preview.py'), '--'] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith('IWZ_PREVIEW')]
    if r.returncode != 0 or not lines:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
        raise SystemExit('blender failed (%d)' % r.returncode)
    return lines, round(time.time() - t, 2)


def load_calib(path=None):
    p = path or CALIB
    if os.path.isfile(p):
        return json.load(open(p))
    return {'eye': 60.0, 'fov': 90.0, 'k': 1.0, 'p': 1.0}


def save_png(arr_srgb, path):
    Image.fromarray((np.clip(arr_srgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def display(raw, k, p):
    return C.lin_to_srgb(C.tonemap(raw, k, p))


def cmd_render(a):
    cal = load_calib(a.calib)
    os.makedirs(a.out, exist_ok=True)
    raw_dir = os.path.join(a.out, '_raw')
    args = ['load', a.src, '--out', raw_dir, '--views', a.views, '--eye', str(a.eye or cal['eye']), '--fov', str(a.fov or cal['fov'])]
    if a.plan:
        args += ['--plan', a.plan]
    if a.overlays:
        args += ['--overlays']
    lines, wall = run_blender(args)
    for ln in lines:
        print(ln)
    t = time.time()
    n = 0
    zone_lum = {}
    mask = C.mask_1280x720()
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.npy'))):
        raw = np.load(f)
        nm = os.path.basename(f)[:-4]
        save_png(display(raw, cal['k'], cal['p']), os.path.join(a.out, nm + '.png'))
        if not nm.startswith('plan_'):
            zone_lum.setdefault(nm.rsplit('_', 1)[0], []).append(C.mean_lum(raw, np.ones_like(mask)))
        n += 1
    if zone_lum:
        zl = {z: {'views': len(v), 'mean_radiance_luminance': round(float(np.mean(v)), 5)} for z, v in zone_lum.items()}
        json.dump(zl, open(os.path.join(a.out, 'zone_luminance.json'), 'w'), indent=1)
        print('mean luminance per zone (linear radiance of the render, all pixels): ' +
              ', '.join('%s %.4f' % (z, v['mean_radiance_luminance']) for z, v in zl.items()))
    if os.path.isfile(os.path.join(raw_dir, 'report.json')):
        shutil.move(os.path.join(raw_dir, 'report.json'), os.path.join(a.out, 'report.json'))
    shutil.rmtree(raw_dir, ignore_errors=True)
    print('render: blender wall %.2f s, tonemap+png %.2f s, %d frames -> %s' % (wall, time.time() - t, n, a.out))


def engine_frames(frames_dir, names):
    out = {}
    for n in names:
        p = os.path.join(frames_dir, n + '.png')
        if os.path.isfile(p):
            out[n] = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255.0
    return out


_ENG_EDGES = {}


def score_dir(d, eng, mask, k=30.0, p=1.0):
    sc = {}
    for n, e in eng.items():
        if n not in _ENG_EDGES:
            _ENG_EDGES[n] = C.engine_edges(e, mask)
        raw = np.load(os.path.join(d, 'plan_' + n + '.npy'))
        sc[n] = C.edge_score(e, C.tonemap(raw, k, p), mask, _ENG_EDGES[n])
    return sc


def sweep(a, eng, mask, eyes, fovs, tag):
    out = os.path.join(a.out, '_sweep_' + tag)
    shutil.rmtree(out, ignore_errors=True)
    args = ['load', a.src, '--plan', a.plan, '--out', out, '--views', 'plan_lit_*', '--eye-list', ','.join(map(str, eyes)),
            '--fov-list', ','.join(map(str, fovs))]
    lines, wall = run_blender(args)
    res = {}
    for eye in eyes:
        for fov in fovs:
            d = os.path.join(out, 'e%g_f%g' % (eye, fov)) if (len(eyes) * len(fovs) > 1) else out
            s = score_dir(d, eng, mask)
            res[(eye, fov)] = {'mean': float(np.mean(list(s.values()))), 'per': s}
    return res, wall, out


def camera_search(a, eng, mask):
    """Edge IoU sweeps: fov at eye 60, then eye x fov around the best, then a fine fov (with 80.8 = cg_fov 65 at 16:9)."""
    fovs1 = [65.0, 75.0, 85.0, 95.0, 105.0, 115.0, 125.0, 135.0, 145.0]
    sw1, w1, d1 = sweep(a, eng, mask, [60.0], fovs1, 'fov')
    best_fov = max(fovs1, key=lambda f: sw1[(60.0, f)]['mean'])
    print('stage fov: best %g (%.1f s) %s' % (best_fov, w1, {f: round(sw1[(60.0, f)]['mean'], 3) for f in fovs1}), flush=True)
    shutil.rmtree(d1, ignore_errors=True)
    fine = sorted({round(best_fov + d, 1) for d in (-5, -2.5, 0, 2.5, 5)})
    eyes = [52.0, 56.0, 60.0, 64.0, 68.0]
    sw2, w2, d2 = sweep(a, eng, mask, eyes, fine, 'eye')
    (best_eye, best_fov2) = max(sw2, key=lambda ef: sw2[ef]['mean'])
    shutil.rmtree(d2, ignore_errors=True)
    fine3 = sorted({round(best_fov2 + d, 1) for d in (-2, -1, 0, 1, 2)} | {80.8})
    sw3, w3, d3 = sweep(a, eng, mask, [best_eye], fine3, 'fine')
    shutil.rmtree(d3, ignore_errors=True)
    best3 = max(fine3, key=lambda f: sw3[(best_eye, f)]['mean'])
    print('stage fine: best %g at eye %g %s' % (best3, best_eye, {f: round(sw3[(best_eye, f)]['mean'], 4) for f in fine3}), flush=True)
    if sw3[(best_eye, best3)]['mean'] >= sw2[(best_eye, best_fov2)]['mean']:
        best_fov2 = best3
    return {'eye': best_eye, 'fov': best_fov2,
            'grid_fov_stage': {str(f): round(sw1[(60.0, f)]['mean'], 4) for f in fovs1},
            'grid_eye_fov_stage': {'%g/%g' % ef: round(v['mean'], 4) for ef, v in sw2.items()},
            'grid_fine_fov_stage': {str(f): round(sw3[(best_eye, f)]['mean'], 4) for f in fine3}}


def cmd_calibrate(a):
    t_all = time.time()
    os.makedirs(a.out, exist_ok=True)
    mask = C.mask_1280x720()
    plan_views = json.load(open(a.plan))
    names = []
    for st in plan_views['steps']:
        if st.get('do') == 'tour':
            names += [v['name'] for v in st['views'] if v['name'].startswith('lit_')]
    eng = engine_frames(a.frames, names)
    if not eng:
        raise SystemExit('no engine frames found in %s' % a.frames)
    calp = a.calib or CALIB
    if a.tone_only and os.path.isfile(calp):
        cam = {k: v for k, v in json.load(open(calp)).items() if k in ('eye', 'fov') or k.startswith('grid_')}
        print('tone only: camera from %s (eye %g, fov %g)' % (calp, cam['eye'], cam['fov']), flush=True)
    else:
        cam = camera_search(a, eng, mask)
    best_eye, best_fov = cam['eye'], cam['fov']
    # BEFORE: the first probe guesses (eye +64, 18 mm lens on a 36 mm sensor = 90 deg horizontal, exposure 1)
    sw0, w0, d0 = sweep(a, eng, mask, [64.0], [90.0], 'before')
    before_raws = {n: np.load(os.path.join(d0, 'plan_' + n + '.npy')) for n in eng}
    before_scores = sw0[(64.0, 90.0)]['per']
    sw1, w1, d1 = sweep(a, eng, mask, [best_eye], [best_fov], 'after')
    raws = {n: np.load(os.path.join(d1, 'plan_' + n + '.npy')) for n in eng}
    # exposure / gamma: ONE global pair over all frames (grid on gamma, bisection on exposure)
    k, p, err = C.fit_tonemap([raws[n] for n in eng], [eng[n] for n in eng], mask)
    after_scores = {n: C.edge_score(eng[n], C.tonemap(raws[n], k, p), mask, _ENG_EDGES[n]) for n in eng}
    rows = []
    sbs_dir = os.path.join(a.out, 'sidebyside')
    os.makedirs(sbs_dir, exist_ok=True)
    for n in eng:
        e_lum = C.mean_lum(C.srgb_to_lin(eng[n]), mask)
        b_lum = C.mean_lum(before_raws[n], mask)
        a_lum = C.mean_lum(C.tonemap(raws[n], k, p), mask)
        rows.append({'frame': n, 'edge_before': round(before_scores[n], 3), 'lum_ratio_before': round(b_lum / e_lum, 3),
                     'edge_after': round(after_scores[n], 3), 'lum_ratio_after': round(a_lum / e_lum, 3),
                     'engine_lum': round(e_lum, 4), 'raw_lum': round(C.mean_lum(raws[n], mask), 5)})
        save_png(np.concatenate([display(raws[n], k, p), eng[n]], 1), os.path.join(sbs_dir, n + '_preview_vs_engine.png'))
    lr = np.log([r['lum_ratio_after'] for r in rows])
    lrb = np.log([r['lum_ratio_before'] for r in rows])
    cal = dict(cam, k=k, p=p,
               fit='camera: edge IoU over %d frames; tone: grid on p in [0.5, 1], k by bisection, least squares of log(luminance ratio)' % len(eng),
               edge_mean_before=float(np.mean(list(before_scores.values()))), edge_mean_after=float(np.mean(list(after_scores.values()))),
               lum_ratio_log_rms_before=float(np.sqrt(np.mean(lrb ** 2))), lum_ratio_log_rms_after=float(np.sqrt(np.mean(lr ** 2))))
    if os.path.isfile(calp):
        prev = json.load(open(calp))
        if 'prop_gain' in prev:
            cal['prop_gain'] = prev['prop_gain']        # fitted by the props command, kept
    json.dump(cal, open(calp, 'w'), indent=1)
    json.dump({'rows': rows, 'calibration': cal}, open(os.path.join(a.out, 'table.json'), 'w'), indent=1)
    lines = ['| frame | edge IoU before | lum ratio before | edge IoU after | lum ratio after |', '|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | %.3f | %.3f | %.3f | %.3f |' % (r['frame'], r['edge_before'], r['lum_ratio_before'], r['edge_after'], r['lum_ratio_after']))
    lines.append('| mean | %.3f | %.3f | %.3f | %.3f |' % (np.mean([r['edge_before'] for r in rows]), np.mean([r['lum_ratio_before'] for r in rows]),
                                                         np.mean([r['edge_after'] for r in rows]), np.mean([r['lum_ratio_after'] for r in rows])))
    open(os.path.join(a.out, 'table.md'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print('fit: eye %g in, hfov %g deg, k %.3f, p %.3f; luminance ratio log-rms %.3f before, %.3f after; total %.1f s' % (
        best_eye, best_fov, k, p, cal['lum_ratio_log_rms_before'], cal['lum_ratio_log_rms_after'], time.time() - t_all))
    for d in (d0, d1):
        shutil.rmtree(d, ignore_errors=True)


def cmd_props(a):
    """Fit the scale of the light grid value of props (calibration.json prop_gain) on the prop pixels of the 15 engine frames:
    props rendered alone (RGBA, world holdout) at gain 1, display = clip(k * gain * radiance) ^ p with the tone of calibration.json,
    least squares of log(preview mean luminance / engine mean luminance) over the frames that show props."""
    cal = load_calib(a.calib)
    mask = C.mask_1280x720()
    plan_views = json.load(open(a.plan))
    names = []
    for st in plan_views['steps']:
        if st.get('do') == 'tour':
            names += [v['name'] for v in st['views'] if v['name'].startswith('lit_')]
    eng = engine_frames(a.frames, names)
    out = os.path.join(a.out, '_props')
    shutil.rmtree(out, ignore_errors=True)
    args = ['load', a.src, '--plan', a.plan, '--out', out, '--views', 'plan_lit_*', '--eye', str(cal['eye']), '--fov', str(cal['fov']),
            '--prop-gain', '1', '--prop-pass']
    lines, wall = run_blender(args)
    data = []
    for n, e in eng.items():
        arr = np.load(os.path.join(out, 'plan_' + n + '.npy'))
        sel = (arr[..., 3] > 0.99) & mask
        if sel.sum() >= 500:
            data.append((n, int(sel.sum()), arr[..., :3][sel], C.lum(C.srgb_to_lin(e))[sel].mean()))
    gains = np.exp(np.linspace(np.log(0.01), np.log(2.0), 80))

    def logs(g):
        return np.array([np.log(C.lum(np.clip(pr * g * cal['k'], 0, 1) ** cal['p']).mean() / el) for _, _, pr, el in data])
    errs = [float(np.sqrt(np.mean(logs(g) ** 2))) for g in gains]
    g = float(gains[int(np.argmin(errs))])
    cal['prop_gain'] = g
    json.dump(cal, open(a.calib or CALIB, 'w'), indent=1)
    l1, lg = logs(1.0), logs(g)
    print('prop gain %.3f (rms log error %.3f, was %.3f at gain 1) over %d frames with props (%.1f s)' % (
        g, float(np.sqrt(np.mean(lg ** 2))), float(np.sqrt(np.mean(l1 ** 2))), len(data), wall))
    for (n, c, _, el), x1, xg in zip(data, l1, lg):
        print('  %-24s %7d px  engine lum %.4f  log ratio %+.2f -> %+.2f' % (n, c, el, x1, xg))
    shutil.rmtree(out, ignore_errors=True)


def cmd_light(a):
    """Render the plan's `<prefix>_*` views in one power state, tone map them with the ENGINE curve (iwz_tonemap) at a stated exposure (`--ev`, the
    vision's fixed exposure; nothing is fitted) and compare with the engine frames: edge IoU, mean luminance ratio and median luminance ratio of the
    upper rows (no weapon, no flashlight pool). Side by sides go to <out>/sidebyside (preview left, engine right)."""
    cal = load_calib(a.calib)
    mask = C.mask_1280x720()
    plan_views = json.load(open(a.plan))
    names = []
    for st in plan_views['steps']:
        if st.get('do') == 'tour':
            names += [v['name'] for v in st['views'] if v['name'].startswith(a.prefix + '_')]
    eng = engine_frames(a.frames, names)
    if not eng:
        raise SystemExit('no engine frames found in %s' % a.frames)
    raw_dir = os.path.join(a.out, '_raw')
    reuse = a.reuse_raw and os.path.isdir(raw_dir)
    if not reuse:
        shutil.rmtree(raw_dir, ignore_errors=True)
    args = ['load', a.src, '--plan', a.plan, '--out', raw_dir, '--views', 'plan_%s_*' % a.prefix, '--eye', str(cal['eye']),
            '--fov', str(cal['fov']), '--power', a.power, '--prop-gain', str(a.prop_gain)]
    lines, wall = ([], 0.0) if reuse else run_blender(args)
    lut = TM.load_lut()
    rows, sbs = [], os.path.join(a.out, 'sidebyside')
    os.makedirs(sbs, exist_ok=True)
    raws = {n: np.load(os.path.join(raw_dir, 'plan_' + n + '.npy')) for n in eng}
    e_lum = {n: C.mean_lum(C.srgb_to_lin(eng[n]), mask) for n in eng}

    gain = 2.0 ** a.ev
    up = (slice(60, 330), slice(None))

    def med(img):
        return float(np.median(C.lum(C.srgb_to_lin(img[up]))))
    for n in eng:
        d1 = TM.display_frame(raws[n], gain, lut)
        eedge = C.engine_edges(eng[n], mask)
        rows.append({'frame': n, 'edge_iou': round(C.edge_score(eng[n], C.srgb_to_lin(d1), mask, eedge), 3),
                     'lum_ratio_mean': round(C.mean_lum(C.srgb_to_lin(d1), mask) / e_lum[n], 3),
                     'lum_ratio_median_upper': round(med(d1) / max(med(eng[n]), 1e-6), 3), 'engine_lum': round(e_lum[n], 4)})
        save_png(np.concatenate([d1, eng[n]], 1), os.path.join(sbs, n + '_preview_vs_engine.png'))
    out = ['| frame (exposure %+g EV) | edge IoU | lum ratio, mean | lum ratio, median upper rows |' % a.ev, '|---|---|---|---|']
    for r in rows:
        out.append('| %s | %.3f | %.3f | %.3f |' % (r['frame'], r['edge_iou'], r['lum_ratio_mean'], r['lum_ratio_median_upper']))
    out.append('| mean | %.3f | %.3f | %.3f |' % tuple(np.mean([r[k] for r in rows]) for k in ('edge_iou', 'lum_ratio_mean', 'lum_ratio_median_upper')))
    open(os.path.join(a.out, 'table_%s.md' % a.prefix), 'w').write(chr(10).join(out) + chr(10))
    json.dump({'rows': rows, 'exposure_ev': a.ev, 'power': a.power, 'prop_gain': a.prop_gain}, open(os.path.join(a.out, 'table_%s.json' % a.prefix), 'w'), indent=1)
    print(chr(10).join(out))
    print('light: power %s, engine tone map, blender %.1f s; exposure %+g EV (gain %.4f)' % (a.power, wall, a.ev, gain))
    if not a.keep_raw:
        shutil.rmtree(raw_dir, ignore_errors=True)


def cmd_lights(a):
    import iwz_lights
    iwz_lights.run(a, load_calib, run_blender, engine_frames, save_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['render', 'calibrate', 'props', 'light', 'lights'])
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--views', default='all')
    ap.add_argument('--plan', default='')
    ap.add_argument('--frames', default='')
    ap.add_argument('--calib', default='')
    ap.add_argument('--eye', type=float, default=0)
    ap.add_argument('--fov', type=float, default=0)
    ap.add_argument('--overlays', action='store_true')
    ap.add_argument('--tone-only', action='store_true', help='calibrate: keep the camera of calibration.json, refit exposure only')
    ap.add_argument('--prefix', default='dark', help='light: engine frame / plan view prefix (dark = power off, lit = power on)')
    ap.add_argument('--ev', type=float, default=-3.0, help='light: exposure in EV (display gain 2**ev); -3 = tonemapAuto 0 + tonemapMaxExposure -3 of the dark vision')
    ap.add_argument('--reuse-raw', action='store_true')
    ap.add_argument('--keep-raw', action='store_true')
    ap.add_argument('--power', choices=['on', 'off'], default='off')
    ap.add_argument('--prop-gain', type=float, default=1.0)
    a = ap.parse_args()
    {'render': cmd_render, 'calibrate': cmd_calibrate, 'props': cmd_props, 'light': cmd_light, 'lights': cmd_lights}[a.cmd](a)


if __name__ == '__main__':
    main()
