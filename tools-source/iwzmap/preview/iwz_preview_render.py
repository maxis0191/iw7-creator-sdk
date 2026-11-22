"""Render Station Zero views with Blender in the background and compare them with engine frames.

    python iwz_preview_render.py render    --src <emit src> --out <dir> [--views a,b|all|prefix*] [--plan PLAN.json]
    python iwz_preview_render.py calibrate --src <emit src> --plan PLAN.json --frames <dir of lit_*_1.png> --out <dir>

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

CALIB = os.path.join(HERE, 'calibration.json')
BEFORE = {'eye': 64.0, 'fov': 2 * np.degrees(np.arctan(18 * 0.5 * 0 + 1)) if False else 90.0, 'k': 1.0, 'p': 1.0}


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
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.npy'))):
        raw = np.load(f)
        save_png(display(raw, cal['k'], cal['p']), os.path.join(a.out, os.path.basename(f)[:-4] + '.png'))
        n += 1
    shutil.rmtree(raw_dir, ignore_errors=True)
    print('render: blender wall %.2f s, tonemap+png %.2f s, %d frames -> %s' % (wall, time.time() - t, n, a.out))


def engine_frames(frames_dir, names):
    out = {}
    for n in names:
        p = os.path.join(frames_dir, n + '.png')
        if os.path.isfile(p):
            out[n] = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255.0
    return out


def score_dir(d, eng, mask, k=30.0, p=1.0):
    sc = {}
    for n, e in eng.items():
        f = os.path.join(d, 'plan_' + n + '.npy')
        raw = np.load(f)
        sc[n] = C.edge_score(e, C.tonemap(raw, k, p), mask)
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
    # BEFORE: the lead's probe guesses (eye +64, 90 deg horizontal here, exposure 1)
    sw0, w0, d0 = sweep(a, eng, mask, [64.0], [90.0], 'before')
    before_dir = d0
    before_raws = {n: np.load(os.path.join(d0, 'plan_' + n + '.npy')) for n in eng}
    before_scores = sw0[(64.0, 90.0)]['per']
    # stage 1: fov at eye 60; stage 2: eye at the best fov
    fovs1 = [65.0, 75.0, 85.0, 95.0, 105.0, 115.0, 125.0, 135.0, 145.0]
    sw1, w1, d1 = sweep(a, eng, mask, [60.0], fovs1, 'fov')
    best_fov = max(fovs1, key=lambda f: sw1[(60.0, f)]['mean'])
    print('stage fov: best %g (%.1f s) %s' % (best_fov, w1, {f: round(sw1[(60.0, f)]['mean'], 3) for f in fovs1}), flush=True)
    shutil.rmtree(d1, ignore_errors=True)
    fine = sorted({round(best_fov + d, 1) for d in (-5, -2.5, 0, 2.5, 5)})
    eyes = [52.0, 56.0, 60.0, 64.0, 68.0]
    sw2, w2, d2 = sweep(a, eng, mask, eyes, fine, 'eye')
    (best_eye, best_fov2) = max(sw2, key=lambda ef: sw2[ef]['mean'])
    print('stage eye/fov: best %g/%g (%.1f s)' % (best_eye, best_fov2, w2), flush=True)
    best_dir = os.path.join(d2, 'e%g_f%g' % (best_eye, best_fov2))
    raws = {n: np.load(os.path.join(best_dir, 'plan_' + n + '.npy')) for n in eng}
    # exposure / gamma: one global pair over all frames
    k, p = C.fit_tonemap([raws[n] for n in eng], [eng[n] for n in eng], mask)
    after_scores = {n: C.edge_score(eng[n], C.tonemap(raws[n], k, p), mask) for n in eng}
    rows = []
    sbs_dir = os.path.join(a.out, 'sidebyside')
    os.makedirs(sbs_dir, exist_ok=True)
    for n in eng:
        e_lum = C.mean_lum(C.srgb_to_lin(eng[n]), mask)
        b_lum = C.mean_lum(before_raws[n], mask)
        a_lum = C.mean_lum(C.tonemap(raws[n], k, p), mask)
        rows.append({'frame': n, 'edge_before': round(before_scores[n], 3), 'lum_ratio_before': round(b_lum / e_lum, 3),
                     'edge_after': round(after_scores[n], 3), 'lum_ratio_after': round(a_lum / e_lum, 3),
                     'engine_lum': round(e_lum, 4)})
        prev = display(raws[n], k, p)
        side = np.concatenate([prev, eng[n]], 1)
        save_png(side, os.path.join(sbs_dir, n + '_preview_vs_engine.png'))
    cal = {'eye': best_eye, 'fov': best_fov2, 'k': k, 'p': p, 'fit': 'edge IoU over %d frames; log mean luminance regression' % len(eng),
           'edge_mean_before': float(np.mean(list(before_scores.values()))), 'edge_mean_after': float(np.mean(list(after_scores.values()))),
           'grid_fov_stage': {str(f): round(sw1[(60.0, f)]['mean'], 4) for f in fovs1},
           'grid_eye_fov_stage': {'%g/%g' % ef: round(v['mean'], 4) for ef, v in sw2.items()}}
    json.dump(cal, open(a.calib or CALIB, 'w'), indent=1)
    json.dump({'rows': rows, 'calibration': cal}, open(os.path.join(a.out, 'table.json'), 'w'), indent=1)
    lines = ['| frame | edge IoU before | lum ratio before | edge IoU after | lum ratio after |', '|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | %.3f | %.3f | %.3f | %.3f |' % (r['frame'], r['edge_before'], r['lum_ratio_before'], r['edge_after'], r['lum_ratio_after']))
    lines.append('| mean | %.3f | %.3f | %.3f | %.3f |' % (np.mean([r['edge_before'] for r in rows]), np.mean([r['lum_ratio_before'] for r in rows]),
                                                         np.mean([r['edge_after'] for r in rows]), np.mean([r['lum_ratio_after'] for r in rows])))
    open(os.path.join(a.out, 'table.md'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print('fit: eye %g in, hfov %g deg, k %.3f, p %.3f; total %.1f s' % (best_eye, best_fov2, k, p, time.time() - t_all))
    for d in (before_dir, d2):
        shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['render', 'calibrate'])
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--views', default='all')
    ap.add_argument('--plan', default='')
    ap.add_argument('--frames', default='')
    ap.add_argument('--calib', default='')
    ap.add_argument('--eye', type=float, default=0)
    ap.add_argument('--fov', type=float, default=0)
    ap.add_argument('--overlays', action='store_true')
    a = ap.parse_args()
    (cmd_render if a.cmd == 'render' else cmd_calibrate)(a)


if __name__ == '__main__':
    main()
