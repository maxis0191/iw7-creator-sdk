"""Measure engine frames of a generated world against its bake (no screenshots read by eye).

usage: lm_measure.py <bake dir> <views "x,y,z,yaw,pitch;..."> <frame dir> <out.json> [--prefix iwzview]
                     [--pattern pattern.json] [--frames-flat <dir of a flat-lit run with the same views>]

For each view i (frame <prefix><i>.bmp, 1280x720 back buffer of capture_frame) every baked texel is projected with
a pinhole camera at the player's eye (origin + eye height, yaw, pitch; IW axes x forward, y left, z up) and tested
for visibility against the world geometry (ray traced: decor models are not part of the scene). The horizontal
field of view and the eye height are fitted per run (grid search, maximum correlation of log luma with log baked E).
Per view it reports:
  walls:    per chart (wall/floor/ceiling) visible texels, luma mean and coefficient of variation (std/mean)
  samples:  correlation of frame luma (linearised sRGB) with the baked flat-normal irradiance E = A + B*Dz,
            a fitted power tone curve luma = k * E^g and the residual
  pattern:  mean luma per calibration patch (lm_measure on the patch texels)
--frames-flat measures a second run at the same views (e.g. the template-texel build) on the same texels.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lmbake, rt


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def load_frame(path):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
    lin = srgb_to_linear(im)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def camera(view, eye, hfov, w, h):
    x, y, z, yaw, pitch = view
    yw, pt = math.radians(yaw), math.radians(pitch)
    f = np.array([math.cos(pt) * math.cos(yw), math.cos(pt) * math.sin(yw), -math.sin(pt)])
    r = np.array([math.sin(yw), -math.cos(yw), 0.0])
    u = np.cross(r, f)
    o = np.array([x, y, z + eye])
    k = (w / 2) / math.tan(math.radians(hfov) / 2)
    return o, f, r, u, k


def project(P, cam, w, h):
    o, f, r, u, k = cam
    d = P - o
    zf = d @ f
    px = w / 2 + (d @ r) / np.maximum(zf, 1e-6) * k
    py = h / 2 - (d @ u) / np.maximum(zf, 1e-6) * k
    ok = (zf > 4) & (px >= 1) & (px < w - 1) & (py >= 1) & (py < h - 1)
    return px, py, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bake'); ap.add_argument('views'); ap.add_argument('frames'); ap.add_argument('out')
    ap.add_argument('--prefix', default='iwzview'); ap.add_argument('--pattern'); ap.add_argument('--frames-flat')
    ap.add_argument('--eye', type=float); ap.add_argument('--fov', type=float)
    a = ap.parse_args()
    d = np.load(os.path.join(a.bake, 'bake.npz'))
    w = lmbake.read_world(os.path.join(a.bake, 'world.bin'))
    _, front = lmbake.build_charts(w, json.load(open(os.path.join(a.bake, 'bake.json')))['texel'])
    pos = w['verts']['pos'].astype(np.float64)
    F = np.array([(x, y, z) for x, y, z, _ in front])
    scene = rt.Scene(pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]])
    P, N = d['tx_pos'], d['tx_n']
    x, y = d['tx_x'], d['tx_y']
    A, B, D = d['A'][y, x], d['B'][y, x], d['D'][y, x]
    E = (A + B * lmbake.oct_decode(D)[:, 2:3]).mean(1)
    chart = d['tx_chart']
    views = [tuple(float(c) for c in v.split(',')) for v in a.views.split(';') if v]
    frames = [load_frame(os.path.join(a.frames, '%s%d.bmp' % (a.prefix, i))) for i in range(len(views))]
    flat = [load_frame(os.path.join(a.frames_flat, '%s%d.bmp' % (a.prefix, i))) for i in range(len(views))] if a.frames_flat else None
    H, W = frames[0].shape

    vis_cache = {}

    def samples(i, eye, fov):
        cam = camera(views[i], eye, fov, W, H)
        px, py, ok = project(P, cam, W, H)
        facing = ((cam[0][None] - P) * N).sum(1) > 0
        ok &= facing
        key = (i, eye)
        if key not in vis_cache:
            vis = np.zeros(len(P), bool)
            idx = np.nonzero(facing)[0]
            src = np.ascontiguousarray(np.repeat(cam[0][None], len(idx), 0))
            vis[idx] = rt.visible(src, np.ascontiguousarray(P[idx] + N[idx] * 1.0), *scene.args())
            vis_cache[key] = vis
        ok &= vis_cache[key]
        return px, py, ok

    def score(eye, fov):
        tot = 0.0
        for i in range(len(views)):
            px, py, ok = samples(i, eye, fov)
            if ok.sum() < 200: continue
            lum = frames[i][py[ok].astype(int), px[ok].astype(int)]
            g = (lum > 1e-4) & (E[ok] > 1e-4)
            if g.sum() < 200: continue
            tot += np.corrcoef(np.log(lum[g]), np.log(E[ok][g]))[0, 1] * g.sum()
        return tot

    if a.eye and a.fov:
        eye, fov = a.eye, a.fov
    else:
        best = None
        for eye in (50, 53, 56, 58, 60, 62, 64, 67, 70):
            for fov in np.arange(118, 150, 1.0):
                s = score(eye, fov)
                if best is None or s > best[0]: best = (s, eye, fov)
        _, eye, fov = best
        for fov2 in np.arange(fov - 1, fov + 1.01, 0.25):
            s = score(eye, fov2)
            if s > best[0]: best = (s, eye, fov2)
        _, eye, fov = best
    print('camera fit: eye height %.1f, horizontal fov %.2f' % (eye, fov))

    pattern = json.load(open(a.pattern)) if a.pattern else []
    rep = {'eye_height': eye, 'hfov': float(fov), 'views': []}
    for i, v in enumerate(views):
        px, py, ok = samples(i, eye, fov)
        ix, iy = px.astype(int), py.astype(int)
        lum = np.full(len(P), np.nan); lum[ok] = frames[i][iy[ok], ix[ok]]
        lf = None
        if flat:
            lf = np.full(len(P), np.nan); lf[ok] = flat[i][iy[ok], ix[ok]]
        vr = {'view': v, 'visible_texels': int(ok.sum()), 'walls': []}
        g = ok & (lum > 1e-4) & (E > 1e-4)
        if g.sum() > 50:
            le, ll = np.log(E[g]), np.log(lum[g])
            gamma, logk = np.polyfit(le, ll, 1)
            pred = logk + gamma * le
            vr['samples'] = {'n': int(g.sum()), 'pearson_log': float(np.corrcoef(le, ll)[0, 1]),
                             'pearson_linear': float(np.corrcoef(E[g], lum[g])[0, 1]),
                             'tone_fit': {'k': float(np.exp(logk)), 'gamma': float(gamma)},
                             'residual_log_rms': float(np.sqrt(np.mean((ll - pred) ** 2))),
                             'residual_rel_median': float(np.median(np.abs(np.exp(ll - pred) - 1)))}
            # a few explicit sample points (texel, world position, baked E, frame luma, predicted luma)
            pick = np.nonzero(g)[0][np.linspace(0, g.sum() - 1, 8).astype(int)]
            vr['sample_points'] = [{'pos': [round(float(c), 1) for c in P[j]], 'pixel': [int(ix[j]), int(iy[j])],
                                    'E_baked': round(float(E[j]), 4), 'luma': round(float(lum[j]), 4),
                                    'luma_pred': round(float(np.exp(logk) * E[j] ** gamma), 4)} for j in pick]
        if lf is not None:
            # same pixels of a run with the template-texel lighting: luma ratio cancels the material texture;
            # within a room the flat run's irradiance is constant, so the ratio follows the baked E alone
            gr = g & (lf > 1e-4)
            if gr.sum() > 50:
                lr = np.log(lum[gr] / lf[gr]); le = np.log(E[gr])
                per = []
                for c in np.unique(chart[gr]):
                    m = chart[gr] == c
                    if m.sum() > 60 and np.std(le[m]) > 0.05:
                        per.append(float(np.corrcoef(lr[m], le[m])[0, 1]))
                vr['ratio_vs_flat'] = {'n': int(gr.sum()), 'pearson_log_all': float(np.corrcoef(lr, le)[0, 1]),
                                       'pearson_log_per_wall_median': float(np.median(per)) if per else None,
                                       'walls_tested': len(per)}
        for c in np.unique(chart[ok]):
            m = ok & (chart == c)
            if m.sum() < 60: continue
            row = {'chart': int(c), 'normal': [round(float(t), 2) for t in N[m][0]], 'texels': int(m.sum()),
                   'luma_mean': float(np.mean(lum[m])), 'luma_cv': float(np.std(lum[m]) / max(np.mean(lum[m]), 1e-6)),
                   'baked_E_cv': float(np.std(E[m]) / max(np.mean(E[m]), 1e-6))}
            if lf is not None:
                row['flat_luma_mean'] = float(np.nanmean(lf[m])); row['flat_luma_cv'] = float(np.nanstd(lf[m]) / max(np.nanmean(lf[m]), 1e-6))
            vr['walls'].append(row)
        pr = []
        for pt in pattern:
            lo, hi = np.array(pt['box'][:3]), np.array(pt['box'][3:])
            m = ok & np.all((P >= lo) & (P <= hi), 1) & ((N @ np.array(pt.get('normal', [0, 0, 1]), float)) > 0.99)
            # keep texels away from the patch border (bilinear filtering and BC blocks mix neighbours)
            inner = m & np.all((P >= lo + [12, 12, -1]) & (P <= hi - [12, 12, -1]), 1)
            if inner.sum() >= 10:
                pr.append({'name': pt.get('name'), 'texels': int(inner.sum()), 'luma_mean': float(np.mean(lum[inner])),
                           'luma_std': float(np.std(lum[inner])), 'E_set': float(np.mean(E[inner]))})
        if pr: vr['pattern'] = pr
        # rendered vs baked on the calibration material: the A-only patches give the engine response luma = f(E)
        # (tone mapping and the material albedo included); predict the other texels of that material from their baked E
        cal = [q for q in pr if q['name'] and q['name'].startswith('A')]
        if len(cal) >= 4:
            ce = np.log([q['E_set'] for q in cal]); cl = np.log([q['luma_mean'] for q in cal])
            o = np.argsort(ce); ce, cl = ce[o], cl[o]
            inpat = np.zeros(len(P), bool)
            for pt in pattern:
                lo, hi = np.array(pt['box'][:3]), np.array(pt['box'][3:])
                inpat |= np.all((P >= lo - [16, 16, 0]) & (P <= hi + [16, 16, 0]), 1)
            pmat = d['tx_mat'][np.all((P >= np.array(pattern[0]['box'][:3])) & (P <= np.array(pattern[0]['box'][3:])), 1)]
            m = g & ~inpat & (d['tx_mat'] == np.bincount(pmat).argmax()) & (N[:, 2] > 0.9) & (E >= np.exp(ce[0])) & (E <= np.exp(ce[-1]))
            if m.sum() > 50:
                pred = np.exp(np.interp(np.log(E[m]), ce, cl))
                rel = lum[m] / pred - 1
                vr['calibrated_prediction'] = {'material_texels': int(m.sum()), 'pearson_log': float(np.corrcoef(np.log(pred), np.log(lum[m]))[0, 1]),
                                               'rel_err_median': float(np.median(np.abs(rel))), 'rel_bias_median': float(np.median(rel)),
                                               'rel_err_p90': float(np.percentile(np.abs(rel), 90))}
        rep['views'].append(vr)
        s = vr.get('samples', {})
        print('view %d: visible %d, r_log %.3f, walls %d, mean luma CV %.3f%s' % (
            i, ok.sum(), s.get('pearson_log', float('nan')), len(vr['walls']),
            np.mean([x['luma_cv'] for x in vr['walls']]) if vr['walls'] else float('nan'),
            (', flat CV %.3f' % np.mean([x['flat_luma_cv'] for x in vr['walls']])) if flat and vr['walls'] else ''))
        for q in pr:
            print('   %-10s E %.3f luma %.4f +- %.4f' % (q['name'], q['E_set'], q['luma_mean'], q['luma_std']))
    json.dump(rep, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
