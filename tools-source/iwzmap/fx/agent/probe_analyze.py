"""fxprobe1 frames: off vs on0..2 per probe, change mask in a +-R box around the FX origin (from FXPROBE lines)."""
import json, math, os, re, sys
import numpy as np
from PIL import Image
run, out = sys.argv[1], sys.argv[2]
R = float(sys.argv[3]) if len(sys.argv) > 3 else 80
os.makedirs(out, exist_ok=True)
log = open(os.path.join(run, 'client.stdout.log'), errors='replace').read()
def vec(s): return [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', s)][:3]
def project(p, cam, yaw, pitch, w, h, hfov=80.7):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 4: return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(hfov) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z)
def L(im, r=3):
    l = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    c = np.pad(l, ((r + 1, r), (r + 1, r)), mode='edge').cumsum(0).cumsum(1); k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
def load(n):
    p = os.path.join(run, n + '.bmp')
    return np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255 if os.path.isfile(p) else None
res = []
for m in re.finditer(r'FXPROBE s=(\d+) name=(\w+) id=(\S+) origin=\(([^)]*)\) cam=\(([^)]*)\) yaw=(\S+)', log):
    s, name, fid, o, cam, yaw = int(m.group(1)), m.group(2), m.group(3), vec(m.group(4)), vec(m.group(5)), float(m.group(6))
    tag = 'iwzp_s%d_%s' % (s, name)
    off = load(tag + '_off'); ons = [load(tag + '_on%d' % i) for i in range(3)]
    if off is None or any(x is None for x in ons):
        res.append({'s': s, 'name': name, 'result': 'NO_FRAME'}); continue
    h, w = off.shape[:2]
    eye = (cam[0], cam[1], cam[2] + 60)
    pts = [project((o[0] + dx, o[1] + dy, o[2] + dz), eye, yaw, 0, w, h) for dx in (-R, R) for dy in (-R, R) for dz in (-R, R)]
    pts = [p for p in pts if p]
    x0, x1 = max(0, int(min(p[0] for p in pts))), min(w, int(max(p[0] for p in pts)))
    y0, y1 = max(0, int(min(p[1] for p in pts))), min(h, int(max(p[1] for p in pts)))
    reg = np.zeros((h, w), bool); reg[y0:y1, x0:x1] = True
    l0 = L(off); ch = [np.abs(L(x) - l0) > 0.03 for x in ons]
    tin = [float(c[reg].mean()) for c in ch]; tout = [float(c[~reg].mean()) for c in ch]
    temporal = float(np.mean([(np.abs(L(ons[i + 1]) - L(ons[i])) > 0.03)[reg].mean() for i in range(2)]))
    dmean = float((L(ons[1]) - l0)[reg].mean())
    res.append({'s': s, 'name': name, 'id': fid, 'in': [round(v, 4) for v in tin], 'out': [round(v, 4) for v in tout],
                'temporal': round(temporal, 4), 'dluma': round(dmean, 4), 'box': [x0, y0, x1, y1]})
    best = int(np.argmax(tin))
    crop = lambda im: Image.fromarray((im[max(0, y0 - 60):y1 + 60, max(0, x0 - 60):x1 + 60] * 255).astype(np.uint8))
    a, b = crop(off), crop(ons[best])
    im = Image.new('RGB', (a.width * 2 + 6, a.height)); im.paste(a, (0, 0)); im.paste(b, (a.width + 6, 0))
    im.save(os.path.join(out, '%s.jpg' % tag), quality=85)
json.dump(res, open(os.path.join(out, 'probe.json'), 'w'), indent=1)
for r in res: print(r)
