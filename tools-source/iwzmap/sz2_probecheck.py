"""Reflection probe check of a Station Zero build (pale Spaceland glyphs on the g24 ceilings came from the template's
reflection probes; the compiler's IWZ_PROBES=neutral gives every lighting room a constant cube of its own colour).

usage: sz2_probecheck.py <compile or build log> <src dir (layout.json, lighting.txt)> <views run dir> [--json out.json]
                         [--chroma 0.2] [--max-luma-ratio 1.0]

From the log: the "iwzmap: probes: room k box ... rgb r g b" lines and the summary line ("template overlapping the
world N"). From the frames: for every hand view (iwzv_<zone>_<n>.bmp) whose camera lies inside a probe room box, the
mean linear colour of the frame. Per room: the chroma of the probe colour (r, g, b divided by their sum) must lie
within --chroma (L1) of the chroma of its frames, and the probe luminance must not exceed --max-luma-ratio times the
frames' mean luminance (a dim environment, never brighter than the room). Fails also when no neutral probe line is
found (the build did not neutralise) or a template instance still overlaps the generated world.
"""
import argparse, glob, json, os, re, sys

import numpy as np
from PIL import Image


def lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def chroma(rgb):
    s = sum(rgb) or 1e-6
    return [c / s for c in rgb]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log'); ap.add_argument('src'); ap.add_argument('run'); ap.add_argument('--json')
    ap.add_argument('--chroma', type=float, default=0.2); ap.add_argument('--max-luma-ratio', type=float, default=1.0)
    a = ap.parse_args()
    text = open(a.log, encoding='utf-8', errors='replace').read()
    rooms = []
    for m in re.finditer(r'iwzmap: probes: room (\d+) box (\S+) (\S+) (\S+) \.\. (\S+) (\S+) (\S+) -> cube \d+ rgb (\S+) (\S+) (\S+)', text):
        v = [float(x) for x in m.groups()[1:]]
        rooms.append({'k': int(m.group(1)), 'mins': v[0:3], 'maxs': v[3:6], 'rgb': v[6:9]})
    summ = re.search(r'template overlapping the world (\d+)', text)
    fails = []
    if not rooms:
        fails.append('no neutral probe rooms in the log (build without IWZ_PROBES=neutral?)')
    if summ and int(summ.group(1)) > 0:
        fails.append('%s template probe instances still overlap the generated world' % summ.group(1))
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    stats = {r['k']: [] for r in rooms}
    for zone, vs in lay.get('views', {}).items():
        for n, v in enumerate(vs):
            x, y, z = v[0], v[1], v[2] + 60
            f = os.path.join(a.run, 'iwzv_%s_%d.bmp' % (zone, n))
            if not os.path.exists(f):
                continue
            inside = [r for r in rooms if all(r['mins'][i] <= p <= r['maxs'][i] for i, p in enumerate((x, y, z)))]
            if not inside:
                continue
            r = min(inside, key=lambda r: np.prod([r['maxs'][i] - r['mins'][i] for i in range(3)]))
            img = lin(np.asarray(Image.open(f).convert('RGB')).astype(np.float32)[::4, ::4])
            stats[r['k']].append([float(c) for c in img.reshape(-1, 3).mean(axis=0)])
    report = []
    for r in rooms:
        fs = stats[r['k']]
        if not fs:
            report.append({'room': r['k'], 'frames': 0})
            continue
        fm = [sum(c[i] for c in fs) / len(fs) for i in range(3)]
        d = sum(abs(p - q) for p, q in zip(chroma(r['rgb']), chroma(fm)))
        pl = 0.2126 * r['rgb'][0] + 0.7152 * r['rgb'][1] + 0.0722 * r['rgb'][2]
        fl = 0.2126 * fm[0] + 0.7152 * fm[1] + 0.0722 * fm[2]
        ok = d <= a.chroma and pl <= a.max_luma_ratio * fl
        report.append({'room': r['k'], 'frames': len(fs), 'probe_rgb': r['rgb'], 'frame_rgb': [round(c, 4) for c in fm],
                       'chroma_l1': round(d, 3), 'probe_luma': round(pl, 4), 'frame_luma': round(fl, 4), 'ok': ok})
        if not ok:
            fails.append('room %d: probe chroma off by %.3f or brighter (probe %.4f, frames %.4f)' % (r['k'], d, pl, fl))
    for x in report:
        print('PROBE', x)
    print('probecheck: rooms %d, fails %d%s' % (len(rooms), len(fails), ''.join('\n  FAIL ' + f for f in fails)))
    if a.json:
        json.dump({'rooms': report, 'fails': fails}, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
