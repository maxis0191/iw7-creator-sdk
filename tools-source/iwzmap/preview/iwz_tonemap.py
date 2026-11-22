"""The engine's tone mapping, read from the shaders of a stock cp_zmb RenderDoc capture (numpy only).

Source: pixel shader 8881bdf370aa (post pass, event 10875 of tf9/gpu-pass-base-L1/run1/frame_frame26095.rdc), DXBC read with
rdoc_inspect.py. Per pixel, with the scene already exposed in the HDR target (there is no exposure multiply in the pass):

    c  = w_scene * scene + w_bloom * bloom            cb2[4].y, cb2[4].x   (0.9, 0.1 in the capture)
    t  = clamp((A*c + B) / (C*c + D), 0, 1)           per channel; (A, C, B, D) = cb13[1].xy, cb13[1].z, cb13[1].w when c >= cb13[0].x
                                                       (shoulder), else cb13[2].xy, cb13[2].z, cb13[2].w (toe)
    m  = clamp(M . t, 0, 1)                           M = cb2[1..3] rows (identity in the capture)
    s  = max(1.055 * m ** (1 / 2.4) - 0.055, 0)       the sRGB curve without its linear segment
    d  = LUT3D(s * 31/32 + 1/64)                      32 x 32 x 32 R8G8B8A8 colour grade, trilinear (texture t2)
    out = d (8 bit, already display encoded); alpha = luma(d) for the anti aliasing pass that follows (FXAA + a noise of cb2[2].y)
"""
import numpy as np

TONE_CAPTURE = {  # the constants of the stock capture (cp_zmb, 1280 x 720)
    'w_bloom': 0.1, 'w_scene': 0.9, 'thresh': 0.071506,
    'shoulder': (27.888254, 27.613163, -0.5121, 4.523621),   # A, C, B, D
    'toe': (6.124092, -1.118782, -0.0, 2.0),
}


def decode_r11g11b10(raw, w, h):
    u = np.frombuffer(raw, '<u4').reshape(h, w)

    def f(bits, ebits, mbits):
        e = (bits >> mbits) & ((1 << ebits) - 1)
        m = bits & ((1 << mbits) - 1)
        e = e.astype(np.int32)
        val = np.where(e == 0, m / (1 << mbits) * 2.0 ** -14, (1 + m / (1 << mbits)) * 2.0 ** (e - 15.0))
        return np.where(e == 31, 65504.0, val).astype(np.float32)
    return np.stack([f(u & 0x7FF, 5, 6), f((u >> 11) & 0x7FF, 5, 6), f((u >> 22) & 0x3FF, 5, 5)], -1)


def bilinear_up(img, h, w):
    """Texture sample at pixel centres (clamp to edge) of img (h0, w0, c) to (h, w)."""
    h0, w0 = img.shape[:2]
    ys = (np.arange(h) + 0.5) * h0 / h - 0.5
    xs = (np.arange(w) + 0.5) * w0 / w - 0.5
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None, None]
    fx = (xs - x0)[None, :, None]
    y0c, y1c = np.clip(y0, 0, h0 - 1), np.clip(y0 + 1, 0, h0 - 1)
    x0c, x1c = np.clip(x0, 0, w0 - 1), np.clip(x0 + 1, 0, w0 - 1)
    top = img[y0c][:, x0c] * (1 - fx) + img[y0c][:, x1c] * fx
    bot = img[y1c][:, x0c] * (1 - fx) + img[y1c][:, x1c] * fx
    return top * (1 - fy) + bot * fy


def curve(c, p=TONE_CAPTURE):
    a, cc, b, d = p['shoulder']
    ta, tc, tb, td = p['toe']
    use_toe = c < p['thresh']
    A = np.where(use_toe, ta, a)
    B = np.where(use_toe, tb, b)
    C = np.where(use_toe, tc, cc)
    D = np.where(use_toe, td, d)
    return np.clip((A * c + B) / (C * c + D), 0, 1)


def lut_sample(lut, rgb):
    """lut (32, 32, 32, 4) indexed [b][g][r]; rgb in 0..1 -> trilinear, clamp."""
    n = lut.shape[0]
    p = np.clip(rgb * n - 0.5, 0, n - 1)
    i0 = np.floor(p).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    f = p - i0
    out = 0
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                ix = (i1 if dx else i0)[..., 0]
                iy = (i1 if dy else i0)[..., 1]
                iz = (i1 if dz else i0)[..., 2]
                wgt = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + lut[iz, iy, ix, :3].astype(np.float32) * wgt[..., None]
    return out / 255.0


def tonemap(scene, bloom, lut, p=TONE_CAPTURE, matrix=None):
    """scene (h, w, 3) linear HDR; bloom (h, w, 3) or None; lut (32,32,32,4) uint8 -> display 0..1 (h, w, 3)."""
    c = p['w_scene'] * scene + (p['w_bloom'] * bloom if bloom is not None else 0)
    t = curve(c, p)
    if matrix is not None:
        t = np.clip(t @ np.asarray(matrix, np.float32).T, 0, 1)
    s = np.maximum(1.055 * np.power(np.clip(t, 0, 1), 1 / 2.4) - 0.055, 0)
    return lut_sample(lut, s * 0.96875 + 0.015625)


def load_lut(path=None):
    import os
    p = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engine_tonemap_lut32.hex')
    if p.endswith('.hex'):                     # text in the product (the source workspace refuses binary payloads)
        raw = bytes.fromhex(''.join(l.strip() for l in open(p, encoding='ascii') if not l.startswith('#')))
    else:
        raw = open(p, 'rb').read()
    return np.frombuffer(raw, np.uint8).reshape(32, 32, 32, 4)


def bloom_approx(scene):
    """The engine's bloom is a 5 level blurred pyramid of the HDR frame ending at 320 x 180 (post chain in ENGINE-SHADERS.md).
    Approximation: 4 x 4 box average (320 x 180) sampled back bilinearly. Weight 0.1 of the output, so its error is second order."""
    h, w = scene.shape[:2]
    if h % 4 or w % 4:
        return scene
    small = scene.reshape(h // 4, 4, w // 4, 4, 3).mean((1, 3))
    return bilinear_up(small, h, w)


def display_frame(raw, gain=1.0, lut=None):
    """Preview linear radiance (h, w, 3), multiplied by `gain` (1.0 = the engine's own scale) -> display sRGB 0..1 (h, w, 3)
    through the engine tone map of the stock vision."""
    lut = load_lut() if lut is None else lut
    scene = np.maximum(raw[..., :3] * gain, 0).astype(np.float32)
    return tonemap(scene, bloom_approx(scene), lut)


# ---- exposure: the engine's exposure compute pass as a steady state model ------------------------------------------------------------------
# Shaders: c672eba77dc0 (sum of log luminance of the 160 x 90 blurred HDR, optional vignette weight; unweighted here) and 974052551c85 lines 28-120
# (ENGINE-SHADERS.md section 1b). The tone curve constants of the pass are the base constants times s, s = 5.5555 * exposure; the world is
# multiplied by nothing else. Stock vision values: the numbers of the cp_zmb / cp_iwz vision files.
import math
import re

STOCK_CAP = 5.0345    # exposure of the stock capture (cb13[3].x) = 0.18 / Lmax with tonemapMaxExposure 8


def parse_vision(path):
    out = {}
    for ln in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'\s*(\w+)\s+"([^"]*)"', ln)
        if m:
            try:
                out[m.group(1)] = float(m.group(2).split()[0])
            except ValueError:
                pass
    return out


def log_average(scene, block=8):
    """Geometric mean of the luminance of the scene reduced to 1 / block (160 x 90 for 1280 x 720), floor 0.000061 as in the shader (line 24-25 of c672)."""
    h, w = scene.shape[:2]
    h8, w8 = h // block * block, w // block * block
    lum = scene[:h8, :w8, 0] * 0.2126 + scene[:h8, :w8, 1] * 0.7152 + scene[:h8, :w8, 2] * 0.0722
    low = lum.reshape(h8 // block, block, w8 // block, block).mean((1, 3))
    return float(math.exp(np.mean(np.log(np.clip(low, 0.000061, 65504.0)))))


def auto_key(lavg, v):
    """The target luminance the frame is exposed to (974052551c85 lines 38-66): a power curve through the vision's Dark / Mid / Light EV points and their exposure adjustments,
    evaluated in the gamma 2.2 domain, clamped to 0.18 * 2^(min adjust) .. 0.18 * 2^(max adjust)."""
    dark, mid, light = v['tonemapDarkEv'], v['tonemapMidEv'], v['tonemapLightEv']
    ga = [(0.18 * 2.0 ** v[k]) ** (1 / 2.2) for k in ('tonemapDarkExposureAdjust', 'tonemapMidExposureAdjust', 'tonemapLightExposureAdjust')]
    ln2 = math.log(2.0)
    span = (light - dark) * ln2
    ratio_ev = (mid - dark) * ln2 / span
    ratio_adj = (ga[1] - ga[0]) / (ga[2] - ga[0])
    p = math.log(ratio_adj) / math.log(ratio_ev)
    scaled = max(lavg / 0.001, 6.1e-5)               # scene luminance in the units of the Ev table (line 34-37)
    tt = max((math.log(scaled) - 0.0) / span, 0.0)   # (Dark - 2.84) = 0 for the stock Dark Ev
    y = max(tt ** p * (ga[2] - ga[0]) + ga[0], 0.0)
    key = y ** 2.2
    return min(max(key, 0.18 * 2.0 ** v['tonemapMinExposureAdjust']), 0.18 * 2.0 ** v['tonemapMaxExposureAdjust'])


def exposure_gain(lavg, v, factor=1.0):
    """Gain on the scene relative to the stock capture's curve constants (s = 27.97 at exposure 5.0345).
    auto (tonemapAuto 1): e = factor * key / Lavg, exposure = min(0.18 / Lmax, e * 2^tonemapAutoExposureAdjust) (lines 80, 108-109);
    fixed (tonemapAuto 0): exposure = min(0.18 / Lmax, 5.0345 * 2^tonemapExposureAdjust) (the stock capture's value times the bias; 2^-3 for the dark vision)."""
    lmax = 0.001 * 2.0 ** (v['tonemapMaxExposure'] - 2.84)
    cap = 0.18 / lmax
    if v.get('tonemapAuto', 1.0) > 0:
        e = factor * auto_key(lavg, v) / max(lavg, 1e-9)
        exp = min(cap, e * 2.0 ** v.get('tonemapAutoExposureAdjust', 0.0))
    else:
        exp = min(cap, STOCK_CAP * 2.0 ** v.get('tonemapExposureAdjust', 0.0))
    return exp / STOCK_CAP
