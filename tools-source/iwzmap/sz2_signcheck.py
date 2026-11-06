"""Check that the custom sign / poster images read correctly in engine frames (not mirrored, not flipped, legible).

usage: sz2_signcheck.py <run dir (iwzv_sign_<k>.bmp frames)> <generated source dir (layout.json)> <art dir> <out dir> [hfov]

For every sign view of layout.json ('sign_views': view index -> sign index), the sign quad corners are projected into
the frame with the capture camera model (same as sz2_frames.py), the quad is rectified to the image aspect, and the
rectified crop is compared (normalised cross-correlation of the grey gradients, 256 px wide) with the source image as
authored and with its mirrored / flipped / rotated variants. PASS when the authored orientation scores best and above
0.35. Writes <out>/signcheck.json and <out>/sign_<k>.jpg (crop | source side by side).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

run, src, art, out = sys.argv[1:5]
HFOV = float(sys.argv[5]) if len(sys.argv) > 5 else 80.7
EYE = 60.0
os.makedirs(out, exist_ok=True)
layout = json.load(open(os.path.join(src, 'layout.json')))
signs = layout['signs']


def project(p, cam, yaw, pitch, w, h):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 1:
        return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(HFOV) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z)


def corners(sg):
    """World corners of the image: top-left, top-right, bottom-right, bottom-left (as the viewer reads it)."""
    (cx, cy, zc), (w, h) = sg['center'], sg['size']
    ax, fc, off = sg['axis'], sg['facing'], sg.get('off', 2.0)
    z0, z1 = zc - h / 2, zc + h / 2
    if ax == 'x':
        y = cy + fc * off
        left, right = (cx + w / 2, cx - w / 2) if fc > 0 else (cx - w / 2, cx + w / 2)
        return [(left, y, z1), (right, y, z1), (right, y, z0), (left, y, z0)]
    x = cx + fc * off
    left, right = (cy - w / 2, cy + w / 2) if fc > 0 else (cy + w / 2, cy - w / 2)
    return [(x, left, z1), (x, right, z1), (x, right, z0), (x, left, z0)]


def persp_coeffs(dst, srcpts):
    # PIL PERSPECTIVE maps output (x, y) -> input; solve the 8 coefficients from 4 point pairs
    A, B = [], []
    for (x, y), (u, v) in zip(dst, srcpts):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def feat(im, W, H):
    a = np.asarray(im.convert('L').resize((W, H), Image.BILINEAR)).astype(np.float32)
    gx = np.zeros_like(a); gy = np.zeros_like(a)
    gx[:, 1:-1] = a[:, 2:] - a[:, :-2]; gy[1:-1, :] = a[2:, :] - a[:-2, :]
    g = np.hypot(gx, gy)
    g -= g.mean()
    return g / (np.linalg.norm(g) + 1e-6)


results = []
for vk, si in sorted(layout.get('sign_views', {}).items(), key=lambda t: int(t[0])):
    vk = int(vk)
    sg = signs[si]
    view = layout['sign_view_list'][vk]
    fn = os.path.join(run, 'iwzv_sign_%d.bmp' % vk)
    if not os.path.isfile(fn):
        results.append({'view': vk, 'image': sg['image'], 'result': 'NO_FRAME'})
        continue
    fr = Image.open(fn).convert('RGB')
    W0, H0 = fr.size
    vx, vy, vz, yaw, pitch = view
    cam = (vx, vy, vz + EYE)
    pts = [project(c, cam, yaw, pitch, W0, H0) for c in corners(sg)]
    if any(p is None for p in pts) or any(not (-5 <= p[0] <= W0 + 5 and -5 <= p[1] <= H0 + 5) for p in pts):
        results.append({'view': vk, 'image': sg['image'], 'result': 'OFF_FRAME', 'pts': pts})
        continue
    ow = 512
    oh = max(16, int(round(ow * sg['size'][1] / sg['size'][0])))
    co = persp_coeffs([(0, 0), (ow, 0), (ow, oh), (0, oh)], pts)
    crop = fr.transform((ow, oh), Image.PERSPECTIVE, co, Image.BILINEAR)
    name = sg['image']
    srcfile = None
    for sub in ('signs', 'out'):
        for ext in ('.png', '_c.tga'):
            p = os.path.join(art, sub, name + ext)
            if os.path.isfile(p) and srcfile is None:
                srcfile = p
    if srcfile is None:
        results.append({'view': vk, 'image': name, 'result': 'NO_SOURCE'})
        continue
    ref = Image.open(srcfile).convert('RGB')
    FW, FH = 256, max(8, int(round(256 * oh / ow)))
    fc = feat(crop, FW, FH)
    variants = {'as_authored': ref, 'mirrored': ref.transpose(Image.FLIP_LEFT_RIGHT), 'flipped': ref.transpose(Image.FLIP_TOP_BOTTOM),
                'rotated180': ref.transpose(Image.ROTATE_180)}
    scores = {k: round(float((fc * feat(v, FW, FH)).sum()), 3) for k, v in variants.items()}
    best = max(scores, key=scores.get)
    ok = best == 'as_authored' and scores['as_authored'] >= 0.35
    side = Image.new('RGB', (ow * 2 + 8, oh), (0, 0, 0))
    side.paste(crop, (0, 0)); side.paste(ref.resize((ow, oh)), (ow + 8, 0))
    side.save(os.path.join(out, 'sign_%d.jpg' % vk), quality=88)
    px = [round(p[0]) for p in pts]
    results.append({'view': vk, 'image': name, 'zone': sg['zone'], 'scores': scores, 'best': best,
                    'width_px': round(max(px) - min(px)), 'result': 'PASS' if ok else 'FAIL'})
json.dump(results, open(os.path.join(out, 'signcheck.json'), 'w'), indent=1)
for r in results:
    print('%-26s view %2d %-9s %s' % (r['image'], r['view'], r['result'], r.get('scores', '')))
print('signs PASS %d / %d' % (sum(r['result'] == 'PASS' for r in results), len(results)))
