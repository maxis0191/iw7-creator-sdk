"""Mood / contrast metrics of a Station Zero v2 views run (lead review g24: luma 0.41-0.48 everywhere, flat).

usage: sz2_mood.py <run dir> <out.json> [--ref <earlier sz2_mood out.json>] [--median 0.30 0.40] [--spread-x 2.0]
                   [--interact-min 0.22]

Per zone (frames iwzv_<zone>_<n>.bmp, sRGB luma as sz2_frames.py): median luma over all pixels of the zone's views,
and the lighting spread: p90 - p10 of 48 x 48 pixel block means (texture detail averaged out, so the spread measures
light pools and dark corners rather than texture contrast; the per-pixel p10 / p90 are reported too), and the
lighting contrast block_p90 / block_p10 (a difference cannot double on a 0..1 scale once it is ~0.5; a ratio can, by
darker corners). Targets: median in [lo, hi]; with --ref, contrast >= spread-x * the reference contrast.
Interaction views (iwzv_interact_<n>.bmp, the fixture's views aimed at doors / buys / perks / quest parts, if present):
mean luma of the central 20 % window must reach --interact-min (paths and purchases stay readable in a darker map).
Walkthrough frames (iwzv_wc_<zone>_<x>_<y>_y<yaw>.bmp, fixture mode walkcap) count for their zone as well.
Flat black voids (reviews A3/B/C: black windows, panels, clock faces, plinths): 32 x 32 blocks darker than 0.3 x the
frame's median luma (relative: the engine's auto exposure lifts true black to ~0.07) with a standard deviation < 0.01
(no texture, unlike a dark but lit surface); a frame fails when more than --void-max of its blocks are such voids
(0.04; on g24 this flags stair_b_3, stair_a_4, platform_b_2/4, generator_room_1, platform_a_2/3, kit_6, the frames
the three reviews named).
Capture gate (lead g27 stair_a_2: the black panel in the stair A arch survived three builds as a list entry): with
--gate the run exits 2 when any frame has a flat black void over --void-max, or a connected region of 16 x 16 blocks
with mean luma < --black-abs (0.02) covering more than --black-px pixels (4096), unless the view matches a known dark
target in mood_dark_ok.json (regex -> reason; e.g. the dark tunnels by design).
"""
import argparse, glob, json, os, re, sys
import numpy as np
from PIL import Image


def luma(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run'); ap.add_argument('out')
    ap.add_argument('--ref'); ap.add_argument('--median', type=float, nargs=2, default=(0.30, 0.40))
    ap.add_argument('--spread-x', type=float, default=2.0); ap.add_argument('--interact-min', type=float, default=0.22)
    ap.add_argument('--void-max', type=float, default=0.04)
    ap.add_argument('--gate', action='store_true', help='exit 2 on any void / black region outside the known dark targets')
    ap.add_argument('--black-abs', type=float, default=0.02); ap.add_argument('--black-px', type=int, default=4096)
    a = ap.parse_args()
    dark_ok = [k_ for k_ in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mood_dark_ok.json'))) if not k_.startswith('_')]
    gate = []
    ref = json.load(open(a.ref))['zones'] if a.ref else {}
    zones, inter, voids = {}, [], []
    files = []
    for r_ in a.run.split(';'):
        files += sorted(glob.glob(os.path.join(r_, 'iwzv_*.bmp')))
    for f in files:
        name = os.path.basename(f)[5:-4]
        zone = name.rsplit('_', 1)[0]
        m_ = re.match(r'wc_(.+)_(-?\d+)_(-?\d+)_y(\d+)$', name)
        if m_:
            zone = m_.group(1)
        if zone.startswith(('sign', 'flk', 'fx', 'kit')) or name.endswith(('_on', '_off')):
            continue
        l = luma(f)
        if zone == 'interact':
            h, w = l.shape
            c = l[int(h * 0.4):int(h * 0.6), int(w * 0.4):int(w * 0.6)]
            inter.append({'view': name, 'center_luma': round(float(c.mean()), 3), 'ok': bool(c.mean() >= a.interact_min)})
            continue
        h, w = l.shape
        bh, bw = h // 48, w // 48
        bk_ = l[:bh * 48, :bw * 48].reshape(bh, 48, bw, 48)
        blocks = bk_.mean(axis=(1, 3)).ravel()
        vb_ = l[:h // 32 * 32, :w // 32 * 32].reshape(h // 32, 32, w // 32, 32)
        flat = float(((vb_.mean(axis=(1, 3)) < 0.3 * float(np.median(l))) & (vb_.std(axis=(1, 3)) < 0.01)).mean())
        if flat > a.void_max:
            voids.append({'view': name, 'flat_black': round(flat, 3)})
        # absolute black regions: 16 x 16 blocks under black_abs, 4-connected
        bb_ = l[:h // 16 * 16, :w // 16 * 16].reshape(h // 16, 16, w // 16, 16).mean(axis=(1, 3)) < a.black_abs
        big = 0
        seen = np.zeros_like(bb_, dtype=bool)
        for i0, j0 in zip(*np.nonzero(bb_)):
            if seen[i0, j0]:
                continue
            stack = [(i0, j0)]; seen[i0, j0] = True; n_ = 0
            while stack:
                i, j = stack.pop(); n_ += 1
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p, q = i + di, j + dj
                    if 0 <= p < bb_.shape[0] and 0 <= q < bb_.shape[1] and bb_[p, q] and not seen[p, q]:
                        seen[p, q] = True; stack.append((p, q))
            big = max(big, n_ * 256)
        ok_ = next((r_ for r_ in dark_ok if re.search(r_, name)), None)
        if (flat > a.void_max or big > a.black_px) and not ok_:
            gate.append('%s: flat void %.1f%%, largest black region %d px' % (name, 100 * flat, big))
        zones.setdefault(zone, []).append((l.ravel()[::7], blocks))
    rep = {'zones': {}, 'interact': inter, 'voids': voids, 'fails': []}
    for v_ in voids:
        rep['fails'].append('flat black void %.1f%% of view %s' % (100 * v_['flat_black'], v_['view']))
    print('flat black void frames: %d' % len(voids))
    for z, parts in sorted(zones.items()):
        v = np.concatenate([p[0] for p in parts]); bl = np.concatenate([p[1] for p in parts])
        p10, med, p90 = (float(np.percentile(v, q)) for q in (10, 50, 90))
        b10, b90 = float(np.percentile(bl, 10)), float(np.percentile(bl, 90))
        r = {'median': round(med, 3), 'p10': round(p10, 3), 'p90': round(p90, 3), 'block_p10': round(b10, 3),
             'block_p90': round(b90, 3), 'spread': round(b90 - b10, 3), 'contrast': round(b90 / max(b10, 0.01), 2)}
        if not a.median[0] <= med <= a.median[1]:
            rep['fails'].append('%s median %.3f outside %.2f..%.2f' % (z, med, a.median[0], a.median[1]))
        if z in ref and r['contrast'] < a.spread_x * ref[z]['contrast']:
            rep['fails'].append('%s contrast %.2f < %.1f x reference %.2f' % (z, r['contrast'], a.spread_x, ref[z]['contrast']))
        r['ref_contrast'] = ref.get(z, {}).get('contrast')
        rep['zones'][z] = r
        print('%-15s median %.3f block p10 %.3f p90 %.3f contrast %.2f%s' % (z, med, b10, b90, r['contrast'],
              '' if z not in ref else '  (ref %.2f)' % ref[z]['contrast']))
    for i in inter:
        if not i['ok']:
            rep['fails'].append('interaction view %s centre luma %.3f < %.2f' % (i['view'], i['center_luma'], a.interact_min))
    print('interaction views %d, dark %d' % (len(inter), sum(not i['ok'] for i in inter)))
    json.dump(rep, open(a.out, 'w'), indent=1)
    print('mood fails: %s' % ('none' if not rep['fails'] else '; '.join(rep['fails'])))
    rep['gate'] = gate
    json.dump(rep, open(a.out, 'w'), indent=1)
    for g_ in gate:
        print('CAPTURE GATE FAIL', g_)
    print('capture gate: %s' % ('FAIL %d frames' % len(gate) if gate else 'ok'))
    if a.gate and gate:
        sys.exit(2)


if __name__ == '__main__':
    main()
