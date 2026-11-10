"""Measure in engine frames that placed FX render: same camera, FX off vs FX on, pixel-change mask restricted to the FX
region, temporal change across the on frames, and the frame-time cost (fxperf DLL phases).

usage: fx_proof.py <run dir> <fx manifest json> <out dir> [--perf <fxperf summary>] [--hfov 80.7] [--thr 0.03] [--blur 3]

Frames (fx_proof_fixture.gsc): iwzf_<k>_off0, iwzf_<k>_off1 (FX k held), iwzf_<k>_on0..on4 (+0.4/1.0/1.8/2.8/4.0 s after
FX k started). Camera of FX k: the fixture's "[IWZ local] FXPROOF k=..; feet=..; angles=.." line (eye = feet + 60).
Region: box of +-region units (z: +-region/2 around target) projected with the capture camera (cg_fov 65 at 16:9 ->
horizontal fov 80.7).
Per FX:
  noise_in / noise_out   fraction of pixels whose blurred luma (7x7 box, film grain) changed > thr between off0 and off1 (inside / outside region)
  change_in / change_out max over on frames of the fraction changed > thr against off0
  temporal_in            mean fraction changed > thr between consecutive on frames inside the region
  RENDERS  coverage test: change_in >= 0.004, change_in >= 4 x noise_in + 0.002, change_in >= 3 x change_out
           or sparse test (embers, sparks, drips): unblurred |diff| > 0.1 pixels in the region >= 20, >= 5 x (off/off
           count + 2), and their density inside >= 3 x the density outside
  region_frac: share of the frame the region covers (near 1: the outside comparison carries little weight)
  ANIMATED temporal_in >= 3 x noise_in + 0.002 (moving particles; a static glow / decal-like FX can render without it)
Frame time: phases 2k+1 (FX off) / 2k+2 (FX on) of the fxperf summary; 200 / 201 = every FX off / on at the zone views.
Writes <out>/fxproof.json, <out>/fx_<k>_<name>.jpg (off | on | mask: red = changed in region, blue = changed outside),
<out>/sheet.jpg.
"""
import argparse, json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

EYE = 60.0


def project(p, cam, yaw, pitch, w, h, hfov):
    yr, pr = math.radians(yaw), math.radians(pitch)
    f = (math.cos(pr) * math.cos(yr), math.cos(pr) * math.sin(yr), -math.sin(pr))
    r = (math.sin(yr), -math.cos(yr), 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 4:
        return None
    x = sum(d[i] * r[i] for i in range(3)); y = sum(d[i] * u[i] for i in range(3))
    fx = (w / 2) / math.tan(math.radians(hfov) / 2)
    return (w / 2 + fx * x / z, h / 2 - fx * y / z)


def vec(s):
    return [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', s)][:3]


def luma(im, r=3):
    """luma, box-blurred over (2r+1)^2 pixels: IW7 film grain changes single pixels between any two frames"""
    l = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    if r <= 0:
        return l
    c = np.pad(l, ((r + 1, r), (r + 1, r)), mode='edge').cumsum(0).cumsum(1)
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def load(run, name):
    p = os.path.join(run, name + '.bmp')
    return np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255.0 if os.path.isfile(p) else None


def read_perf(path):
    out = {}
    if path and os.path.isfile(path):
        for ln in open(path):
            q = ln.split()
            if len(q) >= 14 and q[0] == 'phase':
                out[int(q[1])] = {'frames': int(q[3]), 'mean_ms': float(q[5]), 'p50_ms': float(q[7]), 'p95_ms': float(q[9]),
                                  'p99_ms': float(q[11]), 'max_ms': float(q[13])}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('run'); ap.add_argument('manifest'); ap.add_argument('out')
    ap.add_argument('--perf', default='')
    ap.add_argument('--hfov', type=float, default=80.7)
    ap.add_argument('--thr', type=float, default=0.03)
    ap.add_argument('--blur', type=int, default=3)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    man = json.load(open(a.manifest))
    log = ''
    for f in ('client.stdout.log',):
        p = os.path.join(a.run, f)
        if os.path.isfile(p):
            log = open(p, errors='replace').read()
    cams = {}
    for m in re.finditer(r'\[IWZ local\] FXPROOF k=(\d+); feet=\(([^)]*)\); angles=\(([^)]*)\); los=(\d+)', log):
        cams[int(m.group(1))] = {'feet': vec(m.group(2)), 'angles': vec(m.group(3)), 'los': int(m.group(4))}
    perf = read_perf(a.perf)
    res = {'run': os.path.abspath(a.run), 'thr': a.thr, 'fx': [], 'perf_all': {}}
    tiles = []
    for k, e in enumerate(man['fx']):
        r = {'k': k, 'name': e['name'], 'fx': e['fx'], 'mode': e['mode'], 'zone': e['zone'], 'origin': e['origin']}
        res['fx'].append(r)
        cam = cams.get(k)
        off0, off1 = load(a.run, 'iwzf_%d_off0' % k), load(a.run, 'iwzf_%d_off1' % k)
        ons = [x for x in (load(a.run, 'iwzf_%d_on%d' % (k, i)) for i in range(5)) if x is not None]
        if cam is None or off0 is None or off1 is None or not ons:
            r['result'] = 'NO_FRAME'; continue
        r['camera'] = cam
        h, w = off0.shape[:2]
        eye = (cam['feet'][0], cam['feet'][1], cam['feet'][2] + EYE)
        t = (e['origin'][0], e['origin'][1], e['origin'][2] + e.get('region_dz', 0))
        R = float(e.get('region', 64))
        corners = [(t[0] + dx, t[1] + dy, t[2] + dz) for dx in (-R, R) for dy in (-R, R) for dz in (-R / 2, R / 2)]
        pts = [project(c, eye, cam['angles'][1], cam['angles'][0], w, h, a.hfov) for c in corners]
        pts = [p for p in pts if p]
        if len(pts) < 2:
            r['result'] = 'OFF_FRAME'; continue
        x0, x1 = max(0, int(min(p[0] for p in pts))), min(w, int(max(p[0] for p in pts)))
        y0, y1 = max(0, int(min(p[1] for p in pts))), min(h, int(max(p[1] for p in pts)))
        if x1 - x0 < 8 or y1 - y0 < 8:
            r['result'] = 'OFF_FRAME'; continue
        region = np.zeros((h, w), bool); region[y0:y1, x0:x1] = True
        L0, L1 = luma(off0, a.blur), luma(off1, a.blur)
        Ls = [luma(x, a.blur) for x in ons]
        frac = lambda m, sel: float(m[sel].mean()) if sel.any() else 0.0
        noise = np.abs(L1 - L0) > a.thr
        changes = [np.abs(L - L0) > a.thr for L in Ls]
        ch_in = [frac(c, region) for c in changes]
        ch_out = [frac(c, ~region) for c in changes]
        best = int(np.argmax(ch_in))
        temporal = [frac(np.abs(Ls[i + 1] - Ls[i]) > a.thr, region) for i in range(len(Ls) - 1)]
        n_in, n_out = frac(noise, region), frac(noise, ~region)
        c_in, c_out = ch_in[best], ch_out[best]
        t_in = float(np.mean(temporal)) if temporal else 0.0
        cover = c_in >= 0.004 and c_in >= 4 * n_in + 0.002 and c_in >= 3 * c_out
        # sparse particles (embers, sparks, drips, thin beams): few pixels, but each changes strongly. Unblurred luma,
        # |diff| > 0.1: count in the region on the on frames vs the off0/off1 pair, density inside vs outside
        R0, R1 = luma(off0, 0), luma(off1, 0)
        s_noise = int(((np.abs(R1 - R0) > 0.1) & region).sum())
        s_on = [int(((np.abs(luma(x, 0) - R0) > 0.1) & region).sum()) for x in ons]
        s_out = [int(((np.abs(luma(x, 0) - R0) > 0.1) & ~region).sum()) for x in ons]
        area_in, area_out = max(1, int(region.sum())), max(1, int((~region).sum()))
        # any on frame (a spark burst or a passing drip is in some frames only; other effects' lingering particles
        # outside the region can spoil a single frame)
        sparse = any(s_on[i] >= 20 and s_on[i] >= 5 * (s_noise + 2) and s_on[i] / area_in >= 3 * s_out[i] / area_out
                     for i in range(len(s_on)))
        renders = cover or sparse
        animated = t_in >= 3 * n_in + 0.002
        dl = float((Ls[best] - L0)[region].mean())
        r.update({'region_frac': round(area_in / float(h * w), 3), 'test': 'coverage' if cover else ('sparse' if sparse else ''),
                  'strong_noise_in': s_noise, 'strong_on_in': s_on, 'strong_on_out': s_out,
                  'region_px': [x0, y0, x1, y1], 'noise_in': round(n_in, 5), 'noise_out': round(n_out, 5),
                  'change_in': round(c_in, 5), 'change_out': round(c_out, 5), 'change_in_frames': [round(v, 5) for v in ch_in],
                  'temporal_in': round(t_in, 5), 'mean_luma_delta_in': round(dl, 4), 'best_on': best,
                  'renders': bool(renders), 'animated': bool(animated),
                  'result': 'PASS' if renders else 'FAIL'})
        p_off, p_on = perf.get(2 * k + 1), perf.get(2 * k + 2)
        if p_off and p_on:
            r['frame_ms'] = {'off': p_off, 'on': p_on, 'delta_mean_ms': round(p_on['mean_ms'] - p_off['mean_ms'], 3),
                             'delta_p95_ms': round(p_on['p95_ms'] - p_off['p95_ms'], 3)}
        # evidence image: crop around the region (margin) - off | on | mask
        mx, my = max(40, (x1 - x0) // 2), max(40, (y1 - y0) // 2)
        cx0, cy0, cx1, cy1 = max(0, x0 - mx), max(0, y0 - my), min(w, x1 + mx), min(h, y1 + my)
        mask = np.zeros((h, w, 3), np.float32)
        cb = changes[best]
        mask[cb & region] = (1, 0.1, 0.1); mask[cb & ~region] = (0.2, 0.4, 1)
        over = np.clip(ons[best] * 0.45 + mask * 0.75, 0, 1)
        parts = [off0, ons[best], over]
        cw, chh = cx1 - cx0, cy1 - cy0
        img = Image.new('RGB', (3 * cw + 16, chh + 22), (20, 20, 20))
        for i, pimg in enumerate(parts):
            img.paste(Image.fromarray((pimg[cy0:cy1, cx0:cx1] * 255).astype(np.uint8)), (i * (cw + 8), 22))
        d = ImageDraw.Draw(img)
        d.rectangle([2 * (cw + 8) + x0 - cx0, 22 + y0 - cy0, 2 * (cw + 8) + x1 - cx0, 22 + y1 - cy0], outline=(255, 255, 0))
        d.text((4, 4), '%d %s %s  in %.4f (noise %.4f) out %.4f temporal %.4f  %s' % (k, e['name'], e['fx'].split('/')[-1], c_in, n_in, c_out, t_in, r['result']), fill=(255, 255, 255))
        fn = os.path.join(a.out, 'fx_%d_%s.jpg' % (k, e['name']))
        img.save(fn, quality=88); r['image'] = fn
        tiles.append(img)
    if 200 in perf and 201 in perf:
        res['perf_all'] = {'off': perf[200], 'on': perf[201], 'delta_mean_ms': round(perf[201]['mean_ms'] - perf[200]['mean_ms'], 3),
                           'delta_p95_ms': round(perf[201]['p95_ms'] - perf[200]['p95_ms'], 3)}
    if tiles:
        tw = 900
        rows = [t.resize((tw, max(1, int(t.height * tw / t.width)))) for t in tiles]
        sheet = Image.new('RGB', (tw, sum(t.height for t in rows) + 4 * len(rows)), (0, 0, 0))
        y = 0
        for t in rows:
            sheet.paste(t, (0, y)); y += t.height + 4
        sheet.save(os.path.join(a.out, 'sheet.jpg'), quality=82)
    json.dump(res, open(os.path.join(a.out, 'fxproof.json'), 'w'), indent=1)
    n = sum(1 for r in res['fx'] if r.get('result') == 'PASS')
    for r in res['fx']:
        fm = r.get('frame_ms', {})
        print('%2d %-16s %-36s %-5s %-8s in=%s noise=%s out=%s strong=%s/%s anim=%s regfrac=%s dms=%s' % (
            r['k'], r['name'], r['fx'].split('/')[-1], r['result'], r.get('test'), r.get('change_in'), r.get('noise_in'), r.get('change_out'),
            max(r.get('strong_on_in') or [0]), r.get('strong_noise_in'), r.get('animated'), r.get('region_frac'), fm.get('delta_mean_ms')))
    print('FXPROOF %d/%d render; all-FX frame time %s' % (n, len(res['fx']), res['perf_all'] or 'n/a'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
