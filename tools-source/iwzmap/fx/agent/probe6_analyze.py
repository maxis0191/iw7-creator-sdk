"""fxprobe6/7 frames: per effect and flashlight pass, change in the effect region (FX on vs the off frame of the same
camera, flashlight state and time), coverage (blurred luma, |d| > 0.03) and strong pixels (unblurred, |d| > 0.1),
plus the region's mean luma (how much light reaches it). usage: probe6_analyze.py <run> <out> [prefix iwzd]"""
import importlib.util, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
spec = importlib.util.spec_from_file_location('fxp', r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-iwzmap-fx\tools-source\iwzmap\fx\fx_proof.py')
fxp = importlib.util.module_from_spec(spec); sys.argv_saved = sys.argv; spec.loader.exec_module(fxp)
run, out = sys.argv[1], sys.argv[2]
pre = sys.argv[3] if len(sys.argv) > 3 else 'iwzd'
os.makedirs(out, exist_ok=True)
log = open(os.path.join(run, 'client.stdout.log'), errors='replace').read()
R = 48.0
rows, tiles = [], []
for m in re.finditer(r'FXPROBE[678] s=(\d+) name=(\w+) fl=(\d) origin=\(([^)]*)\) cam=\(([^)]*)\) angles=\(([^)]*)\) flon=(\S+)', log):
    s, name, fl = int(m.group(1)), m.group(2), int(m.group(3))
    o, cam, ang = fxp.vec(m.group(4)), fxp.vec(m.group(5)), fxp.vec(m.group(6))
    tag = '%s_s%d_%s_%s' % (pre, s, name, 'fl' if fl else 'nofl')
    off = fxp.load(run, tag + '_off'); ons = [fxp.load(run, tag + '_on%d' % i) for i in range(3)]
    if off is None or any(x is None for x in ons):
        rows.append({'tag': tag, 'result': 'NO_FRAME'}); continue
    h, w = off.shape[:2]
    eye = (cam[0], cam[1], cam[2] + 60)
    pts = [fxp.project((o[0] + dx, o[1] + dy, o[2] + dz), eye, ang[1], ang[0], w, h, 80.7) for dx in (-R, R) for dy in (-R, R) for dz in (-R, R)]
    pts = [p for p in pts if p]
    x0, x1 = max(0, int(min(p[0] for p in pts))), min(w, int(max(p[0] for p in pts)))
    y0, y1 = max(0, int(min(p[1] for p in pts))), min(h, int(max(p[1] for p in pts)))
    reg = np.zeros((h, w), bool); reg[y0:y1, x0:x1] = True
    B0 = fxp.luma(off, 3); Bs = [fxp.luma(x, 3) for x in ons]
    U0 = fxp.luma(off, 0); Us = [fxp.luma(x, 0) for x in ons]
    cov = [float((np.abs(b - B0) > 0.03)[reg].mean()) for b in Bs]
    covo = [float((np.abs(b - B0) > 0.03)[~reg].mean()) for b in Bs]
    strong = [int(((np.abs(u - U0) > 0.1) & reg).sum()) for u in Us]
    dl = [float((b - B0)[reg].mean()) for b in Bs]
    i = int(np.argmax(cov))
    off1 = fxp.load(run, tag + '_off1')
    n_cov, n_strong = 0.0, 0
    if off1 is not None:
        n_cov = float((np.abs(fxp.luma(off1, 3) - B0) > 0.03)[reg].mean())
        n_strong = int(((np.abs(fxp.luma(off1, 0) - U0) > 0.1) & reg).sum())
    reads = (cov[i] >= 0.004 and cov[i] >= 3 * covo[i] and cov[i] >= 4 * n_cov + 0.002) or (max(strong) >= 20 and max(strong) >= 5 * (n_strong + 2))
    r = {'tag': tag, 'set': s, 'name': name, 'flashlight': fl, 'region_px': [x0, y0, x1, y1],
         'region_luma_off': round(float(B0[reg].mean()), 4), 'coverage_in': [round(v, 4) for v in cov],
         'coverage_out': [round(v, 4) for v in covo], 'noise_cov': round(n_cov, 4), 'noise_strong': n_strong, 'strong_in': strong, 'mean_luma_delta_in': [round(v, 4) for v in dl],
         'result': 'READS' if reads else 'NOT_SEEN'}
    rows.append(r)
    mx, my = 60, 60
    cx0, cy0, cx1, cy1 = max(0, x0 - mx), max(0, y0 - my), min(w, x1 + mx), min(h, y1 + my)
    a = Image.fromarray((off[cy0:cy1, cx0:cx1] * 255).astype(np.uint8)); b = Image.fromarray((ons[i][cy0:cy1, cx0:cx1] * 255).astype(np.uint8))
    d = np.clip(np.abs(Bs[i] - B0)[cy0:cy1, cx0:cx1] * 8, 0, 1)
    c = Image.fromarray((d * 255).astype(np.uint8)).convert('RGB')
    t = Image.new('RGB', (a.width * 3 + 8, a.height + 16), (10, 10, 10))
    t.paste(a, (0, 16)); t.paste(b, (a.width + 4, 16)); t.paste(c, (2 * a.width + 8, 16))
    ImageDraw.Draw(t).text((3, 2), '%s  cov %.4f out %.4f strong %d  %s' % (tag, cov[i], covo[i], max(strong), r['result']), fill=(255, 255, 0))
    t.save(os.path.join(out, tag + '.jpg'), quality=88)
    tiles.append(t)
json.dump(rows, open(os.path.join(out, 'probe.json'), 'w'), indent=1)
for r in rows:
    print('%-34s %-8s off_luma=%s cov=%s out=%s noise=%s/%s strong=%s dl=%s' % (r['tag'], r.get('result'), r.get('region_luma_off'), r.get('coverage_in'), r.get('coverage_out'), r.get('noise_cov'), r.get('noise_strong'), r.get('strong_in'), r.get('mean_luma_delta_in')))
if tiles:
    W = 1100
    rs = [t.resize((W, max(1, int(t.height * W / t.width)))) for t in tiles]
    for k in range(0, len(rs), 8):
        g = rs[k:k + 8]
        sh = Image.new('RGB', (W, sum(t.height for t in g)))
        y = 0
        for t in g:
            sh.paste(t, (0, y)); y += t.height
        sh.save(os.path.join(out, 'sheet_%d.jpg' % (k // 8)), quality=82)
