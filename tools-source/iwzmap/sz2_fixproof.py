"""Fix-proof crop pairs for a Station Zero v2 build (consolidated review protocol, 2026-11-09).

usage: python -I sz2_fixproof.py <spec.json> <before vision dir> <after vision dir> <out dir>
       --before-runs <run dir>[;...] --after-runs <run dir>[=suffix][;...] [--verdicts verdicts.json]

spec.json: {"build": "g27c", "before": "g27", "items": [{"id": "B1", "title": "...", "frames": ["stair_a_2", ...],
            "crop": {"stair_a_2": [x0, y0, x1, y1]}}]}   (crop in native pixels; default: the whole frame)
A defect is only proven at the SAME camera: every frame's pose (origin + angles from the runs' [IWZ local] VIEW / WC
lines) must match between the two builds; a moved camera is reported, never paired silently. An "after-runs" entry
with "=suffix" maps its frames to <name><suffix> in the after vision dir (vision_prep of renamed copies), and that run
is preferred for the pair (e.g. the closed-door views, the door state of the before build's views).
Writes <out>/<id>_<frame>_{before,after,pair}.png, <out>/<id>_{before,after}.png (first frame) and <out>/fixproof.md
(one line per pair: camera check, verdict from --verdicts {"<id>/<frame>": "FIXED|NOT FIXED|... text"}).
"""
import json, os, re, sys
from PIL import Image, ImageDraw

POSE = re.compile(r'\[IWZ local\] (?:VIEW|WC) name=([^;]+); origin=\(([^)]*)\);.*?(?:angles=\(([^)]*)\))?\s*$')


def poses(run):
    out = {}
    for fn in ('client.stdout.log',):
        p = os.path.join(run, fn)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding='utf-8', errors='replace'):
            m = POSE.search(line.rstrip())
            if m:
                o = tuple(round(float(c)) for c in m.group(2).split(','))
                a = tuple(round(float(c)) for c in m.group(3).split(',')) if m.group(3) else None
                out[m.group(1)] = (o, a)
    return out


def main():
    a = sys.argv[1:]
    opt = {}
    for k in ('--before-runs', '--after-runs', '--verdicts'):
        if k in a:
            i = a.index(k); opt[k] = a[i + 1]; del a[i:i + 2]
    spec_p, bdir, adir, out = a
    spec = json.load(open(spec_p))
    verdicts = json.load(open(opt['--verdicts'])) if '--verdicts' in opt else {}
    os.makedirs(out, exist_ok=True)
    bpose = {}
    for r in opt.get('--before-runs', '').split(';'):
        if r:
            bpose.update(poses(r))
    apose = []        # (suffix, poses) in preference order: suffixed runs first
    for r in opt.get('--after-runs', '').split(';'):
        if not r:
            continue
        r, _, suf = r.partition('=')
        apose.append((suf, poses(r)))
    apose.sort(key=lambda t: t[0] == '')
    lines = ['# Fix proof %s (before: %s)' % (spec['build'], spec['before']), '',
             'Same camera = identical origin and angles in both builds\' run logs. Crops at native resolution.', '',
             '| id | frame | after frame | camera | verdict |', '|---|---|---|---|---|']
    missing = 0
    for it in spec['items']:
        first = True
        for fr in it['frames']:
            bp = bpose.get(fr)
            after, cam = None, 'no pose'
            for suf, ps in apose:
                if fr in ps and os.path.exists(os.path.join(adir, 'frames', fr + suf + '.png')):
                    after = fr + suf
                    q_ = ps[fr]
                    close_ = bp and all(abs(a_ - b_) <= 2 for a_, b_ in zip(q_[0], bp[0])) and (q_[1] == bp[1] or (q_[1] and bp[1] and all(abs(a_ - b_) <= 1 for a_, b_ in zip(q_[1], bp[1]))))
                    cam = 'same' if close_ else 'MOVED %s -> %s' % (bp, q_)
                    break
            if bp and cam != 'same':
                # a renumbered view list or a fixed fp_* camera: any after frame at exactly the before pose
                # (origin within 2 units, angles within 1 degree) is the same camera
                for suf, ps in apose:
                    hit = next((n_ for n_, q_ in ps.items() if q_[1] and bp[1] and all(abs(a_ - b_) <= 2 for a_, b_ in zip(q_[0], bp[0]))
                                and all(abs(a_ - b_) <= 1 for a_, b_ in zip(q_[1], bp[1]))
                                and os.path.exists(os.path.join(adir, 'frames', n_ + suf + '.png'))), None)
                    if hit:
                        after, cam = hit + suf, 'same pose (%s)' % hit
                        break
            bpng = os.path.join(bdir, 'frames', fr + '.png')
            if after is None or not os.path.exists(bpng):
                missing += 1
                lines.append('| %s | %s | - | MISSING (%s) | - |' % (it['id'], fr, 'before' if not os.path.exists(bpng) else 'after'))
                continue
            box = it.get('crop', {}).get(fr)
            ib = Image.open(bpng).convert('RGB'); ia = Image.open(os.path.join(adir, 'frames', after + '.png')).convert('RGB')
            if box:
                ib, ia = ib.crop(tuple(box)), ia.crop(tuple(box))
            stem = os.path.join(out, '%s_%s' % (it['id'], fr))
            ib.save(stem + '_before.png'); ia.save(stem + '_after.png')
            w, h = ib.size
            pair = Image.new('RGB', (w * 2 + 8, h + 28), (20, 20, 20))
            pair.paste(ib, (0, 28)); pair.paste(ia, (w + 8, 28))
            d = ImageDraw.Draw(pair)
            d.text((6, 6), '%s %s  BEFORE %s' % (it['id'], fr, spec['before']), fill=(255, 255, 255))
            d.text((w + 14, 6), 'AFTER %s (%s)  camera %s' % (spec['build'], after, cam.split(' ')[0]), fill=(255, 255, 255))
            pair.save(stem + '_pair.png')
            if first:
                ib.save(os.path.join(out, it['id'] + '_before.png')); ia.save(os.path.join(out, it['id'] + '_after.png'))
                first = False
            v = verdicts.get('%s/%s' % (it['id'], fr), 'not reviewed')
            lines.append('| %s | %s | %s | %s | %s |' % (it['id'], fr, after, cam, v))
    open(os.path.join(out, 'fixproof.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('fixproof pairs: %d lines, %d missing -> %s' % (len(lines) - 6, missing, out))


if __name__ == '__main__':
    main()
