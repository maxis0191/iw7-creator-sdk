"""Predict the views-run mood metrics (sz2_mood.py) of a NEW bake from an OLD bake and its engine frames, offline.

usage: sz2_mood_predict.py <old bake dir> <new bake dir> <old views run dir> <src dir with layout.json> <out.json>
                           [--eye 58.45] [--hfov 133.14] [--baker <dir of lmbake.py/rt.py/lm_measure.py>]
                           [--points <json list of [x,y,z]>] [--points-min 0.22]

For every zone view of the old run: the old bake's texels visible from the capture camera are projected (camera and
visibility as lm_measure.py), the frame's linear luma at those pixels is related to the old irradiance by a fitted tone
curve (log-linear, per run), and each texel's luma is scaled by (E_new / E_old)^gamma, E_new taken from the nearest
texel of the new bake within 12 units with a similar normal. Reports per zone the predicted median sRGB luma and the
block (48 px) p90 / p10 contrast, comparable to sz2_mood.py. --points: predicted sRGB luma at world points (mean of new
texels within 64 units, through the same tone curve) - doors, buys and quest parts must stay readable.
Engine frames of the new build remain the proof; this only steers the bake parameters without a game run.
"""
import argparse, json, math, os, sys
import numpy as np


def srgb(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('run'); ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--eye', type=float, default=58.45); ap.add_argument('--hfov', type=float, default=133.14)
    ap.add_argument('--baker', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bake'))
    ap.add_argument('--points'); ap.add_argument('--points-min', type=float, default=0.22)
    a = ap.parse_args()
    sys.path.insert(0, a.baker)
    import lmbake, rt, lm_measure
    from scipy.spatial import cKDTree

    def load(bdir):
        d = np.load(os.path.join(bdir, 'bake.npz'))
        x, y = d['tx_x'], d['tx_y']
        E = (d['A'][y, x] + d['B'][y, x] * lmbake.oct_decode(d['D'][y, x])[:, 2:3]).mean(1)
        return d['tx_pos'].astype(np.float64), d['tx_n'].astype(np.float64), E

    P0, N0, E0 = load(a.old)
    P1, N1, E1 = load(a.new)
    tree = cKDTree(P1)
    w = lmbake.read_world(os.path.join(a.old, 'world.bin'))
    _, front = lmbake.build_charts(w, json.load(open(os.path.join(a.old, 'bake.json')))['texel'])
    pos = w['verts']['pos'].astype(np.float64)
    F = np.array([(x, y, z) for x, y, z, _ in front])
    scene = rt.Scene(pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]])
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    # new irradiance at the old texels: nearest new texel with a similar normal
    dist, idx = tree.query(P0, k=4, distance_upper_bound=12.0)
    En = np.full(len(P0), np.nan)
    for j in range(4):
        ok = np.isfinite(dist[:, j]) & np.isnan(En)
        ii = np.minimum(idx[:, j], len(P1) - 1)
        ok &= (N0 * N1[ii]).sum(1) > 0.7
        En[ok] = E1[ii[ok]]
    samples, fitx, fity = {}, [], []
    for zone, vs in lay['views'].items():
        if zone in ('kit', 'sign'):
            continue
        for k, v in enumerate(vs):
            f = os.path.join(a.run, 'iwzv_%s_%d.bmp' % (zone, k))
            if not os.path.isfile(f):
                continue
            fr = lm_measure.load_frame(f)
            H, W = fr.shape
            cam = lm_measure.camera(v, a.eye, a.hfov, W, H)
            px, py, ok = lm_measure.project(P0, cam, W, H)
            ok &= ((cam[0][None] - P0) * N0).sum(1) > 0
            idx_ = np.nonzero(ok)[0]
            src = np.ascontiguousarray(np.repeat(cam[0][None], len(idx_), 0))
            vis = rt.visible(src, np.ascontiguousarray(P0[idx_] + N0[idx_] * 1.0), *scene.args())
            sel = idx_[vis]
            lum = fr[py[sel].astype(int), px[sel].astype(int)]
            g = (lum > 1e-4) & (E0[sel] > 1e-4) & np.isfinite(En[sel])
            sel, lum = sel[g], lum[g]
            samples.setdefault(zone, []).append((sel, lum, px[sel].astype(int) // 48, py[sel].astype(int) // 48, k))
            fitx.append(np.log(E0[sel])); fity.append(np.log(lum))
    gamma, logk = np.polyfit(np.concatenate(fitx), np.concatenate(fity), 1)
    print('tone fit: luma = %.3f * E^%.3f' % (math.exp(logk), gamma))
    rep = {'tone': {'k': math.exp(logk), 'gamma': gamma}, 'zones': {}, 'points': []}
    for zone, parts in sorted(samples.items()):
        old_l, new_l, b_old, b_new = [], [], [], []
        for sel, lum, bx, by, k in parts:
            nl = lum * (np.maximum(En[sel], 1e-5) / E0[sel]) ** gamma
            old_l.append(srgb(lum)); new_l.append(srgb(nl))
            key = bx * 1000 + by
            for arr, dst in ((srgb(lum), b_old), (srgb(nl), b_new)):
                u, inv = np.unique(key, return_inverse=True)
                sums = np.bincount(inv, arr); cnt = np.bincount(inv)
                dst.append(sums[cnt >= 20] / cnt[cnt >= 20])
        ol, nlv = np.concatenate(old_l), np.concatenate(new_l)
        bo, bn = np.concatenate(b_old), np.concatenate(b_new)
        r = {'median_old': round(float(np.median(ol)), 3), 'median_new': round(float(np.median(nlv)), 3),
             'contrast_old': round(float(np.percentile(bo, 90) / max(np.percentile(bo, 10), 0.01)), 2),
             'contrast_new': round(float(np.percentile(bn, 90) / max(np.percentile(bn, 10), 0.01)), 2)}
        rep['zones'][zone] = r
        print('%-15s median %.3f -> %.3f   contrast %.2f -> %.2f  (world texels only)' % (zone, r['median_old'], r['median_new'],
              r['contrast_old'], r['contrast_new']))
    if a.points:
        if a.points == 'layout':     # every interaction of the map (doors, buys, perks, wheel, power, PaP, quest, trap)
            pts = [{'name': '%s@%d,%d' % (it['kind'], it['origin'][0], it['origin'][1]), 'pos': list(it['origin'])}
                   for it in lay.get('interactions', [])]
            for k_, q in (lay.get('quest') or {}).items():
                if isinstance(q, dict) and 'origin' in q:
                    pts.append({'name': k_, 'pos': list(q['origin'])})
        else:
            pts = json.load(open(a.points))
        for p in pts:
            p_ = np.array(p['pos'], float)
            ii = tree.query_ball_point(p_, 64.0)
            if not ii:
                rep['points'].append({**p, 'luma': None, 'ok': False}); continue
            e = float(np.mean(E1[ii]))
            l = float(srgb(math.exp(logk) * max(e, 1e-5) ** gamma))
            rep['points'].append({**p, 'luma': round(l, 3), 'ok': l >= a.points_min})
        dark = [p for p in rep['points'] if not p['ok']]
        print('points %d, below %.2f: %d %s' % (len(pts), a.points_min, len(dark), [(p['name'], p['luma']) for p in dark][:12]))
    json.dump(rep, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
