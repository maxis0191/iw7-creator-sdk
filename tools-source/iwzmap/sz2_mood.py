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
"""
import argparse, glob, json, os
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
    a = ap.parse_args()
    ref = json.load(open(a.ref))['zones'] if a.ref else {}
    zones, inter = {}, []
    for f in sorted(glob.glob(os.path.join(a.run, 'iwzv_*.bmp'))):
        name = os.path.basename(f)[5:-4]
        zone = name.rsplit('_', 1)[0]
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
        blocks = l[:bh * 48, :bw * 48].reshape(bh, 48, bw, 48).mean(axis=(1, 3)).ravel()
        zones.setdefault(zone, []).append((l.ravel()[::7], blocks))
    rep = {'zones': {}, 'interact': inter, 'fails': []}
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


if __name__ == '__main__':
    main()
