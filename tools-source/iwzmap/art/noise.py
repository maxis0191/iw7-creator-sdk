"""Deterministic, tileable noise synthesis for map textures (numpy + scipy only).

Every function takes an explicit seed and returns float32 arrays in [0, 1] unless stated otherwise. Spectral noise is
periodic by construction (FFT synthesis), so anything built from it with wrap-mode sampling tiles seamlessly.

  spectral(shape, beta, seed)     1/f^beta noise (beta 1 = pink/rough, 2 = brown/cloudy, 3 = very smooth)
  fbm(shape, seed, ...)           band-sum of spectral octaves with persistence
  warp(field, seed, amount, ...)  domain warp (two independent spectral displacement fields), wrap mode
  streaks(shape, seed, ...)       gravity flow streaks (water/rust/grime runs) with drip beads, alpha-like field
  blobs(shape, seed, ...)         soft irregular spots (oil drops, stains), wrap-aware
  border_falloff(shape, margin)   0 at the image border, 1 inside (feathered decals must reach 0 at the edge)
"""
import numpy as np
from scipy import ndimage


def _rng(seed):
    return np.random.default_rng(int(seed) & 0xFFFFFFFF)


def normalize(a, lo_pct=0.5, hi_pct=99.5):
    """Map to [0, 1] with percentile clipping (robust against a few extreme samples)."""
    lo, hi = np.percentile(a, [lo_pct, hi_pct])
    return np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1).astype(np.float32)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return (t * t * (3 - 2 * t)).astype(np.float32)


def spectral(shape, beta=2.0, seed=0, fmin=None, fmax=None, aniso=(1.0, 1.0)):
    """Periodic 1/f^beta noise. fmin/fmax (cycles per pixel, 0..0.5) band-limit it. aniso=(ky, kx) weights the
    frequency per axis: features become k times LONGER along an axis whose k > 1 (aniso=(8, 1): vertical fibres,
    aniso=(1, 8): horizontal grain)."""
    h, w = shape
    white = _rng(seed).standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * aniso[0]
    fx = np.fft.fftfreq(w)[None, :] * aniso[1]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    amp = f ** (-beta / 2.0)
    if fmin:
        amp *= 1.0 / (1.0 + np.exp(-(f - fmin) / (fmin * 0.3)))
    if fmax:
        amp *= np.exp(-(f / fmax) ** 2)
    amp[0, 0] = 0.0
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * amp))
    return normalize(out)


def fbm(shape, seed=0, octaves=6, base=0.004, lacunarity=2.0, persistence=0.55, beta=1.0):
    """Sum of band-limited octaves from `base` cycles/pixel upward."""
    acc = np.zeros(shape, np.float64)
    amp, f, total = 1.0, base, 0.0
    for o in range(octaves):
        band = spectral(shape, beta, seed * 131 + o, fmin=f * 0.5, fmax=f * 1.6)
        acc += (band - 0.5) * amp
        total += amp
        amp *= persistence
        f *= lacunarity
        if f > 0.5:
            break
    return normalize(acc / total)


def warp(field, seed=0, amount=40.0, scale=0.006, octaves=3):
    """Domain warp in pixels; wrap mode keeps tileability."""
    h, w = field.shape
    dx = (fbm((h, w), seed * 7 + 1, octaves, base=scale) - 0.5) * 2 * amount
    dy = (fbm((h, w), seed * 7 + 2, octaves, base=scale) - 0.5) * 2 * amount
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return ndimage.map_coordinates(field, [yy + dy, xx + dx], order=1, mode='grid-wrap').astype(np.float32)


def border_falloff(shape, margin, seed=None, wobble=0.0):
    """1 inside, smoothly 0 at the border over `margin` pixels; optional noisy wobble of the boundary."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    if seed is not None and wobble:
        d = d + (fbm(shape, seed, 4, base=0.01) - 0.5) * 2 * wobble
    return smoothstep(0, margin, d)


def blobs(shape, seed, count, rmin, rmax, irregular=0.5, wrap=True, elong=1.0, angle=None, rough_base=0.02):
    """Soft irregular spots as a [0,1] coverage field. Each blob is a gaussian distorted by noise."""
    h, w = shape
    r = _rng(seed)
    acc = np.zeros(shape, np.float32)
    rough = fbm(shape, seed + 99, 4, base=rough_base)
    for _ in range(count):
        cx, cy = r.uniform(0, w), r.uniform(0, h)
        rad = r.uniform(rmin, rmax)
        a = r.uniform(0, np.pi) if angle is None else angle
        gain = r.uniform(0.5, 1.0)
        ext = int(rad * max(elong, 1.0) * (1.6 + irregular)) + 2
        xs = np.arange(int(cx) - ext, int(cx) + ext + 1)
        ys = np.arange(int(cy) - ext, int(cy) + ext + 1)
        if wrap:
            xi, yi = xs % w, ys % h
        else:
            xs, ys = xs[(xs >= 0) & (xs < w)], ys[(ys >= 0) & (ys < h)]
            xi, yi = xs, ys
        ddx = (xs - cx)[None, :].astype(np.float32)
        ddy = (ys - cy)[:, None].astype(np.float32)
        u = ddx * np.cos(a) + ddy * np.sin(a)
        v = -ddx * np.sin(a) + ddy * np.cos(a)
        dist = np.sqrt((u / elong) ** 2 + v ** 2) / rad
        dist = dist + (rough[np.ix_(yi, xi)] - 0.5) * irregular * 2
        sub = acc[np.ix_(yi, xi)]
        acc[np.ix_(yi, xi)] = np.maximum(sub, gain * smoothstep(1.0, 0.55, dist))
    return acc


def streaks(shape, seed, count, length=(0.3, 0.9), width=(2.0, 8.0), x_range=(0.0, 1.0), y0_range=(0.0, 0.1),
            wobble=6.0, beads=True, wrap_x=True, ss=2):
    """Gravity flow streaks, top to bottom. Returns a [0,1] field: dense near the source, fading and thinning
    with distance, broken by noise, with occasional drip beads at the ends. Drawn supersampled then reduced."""
    from PIL import Image, ImageDraw
    h, w = shape
    H, W = h * ss, w * ss
    r = _rng(seed)
    acc = np.zeros((H, W), np.float32)
    for _ in range(count):
        img = Image.new('F', (W, H), 0.0)
        d = ImageDraw.Draw(img)
        x0 = r.uniform(*x_range) * W
        y0 = r.uniform(*y0_range) * H
        L = r.uniform(*length) * H
        wid = r.uniform(*width) * ss
        strength = r.uniform(0.35, 1.0)
        n = int(max(8, L / (2 * ss)))
        phase = r.uniform(0, 100)
        freq = r.uniform(0.004, 0.012) / ss
        # opacity and width vary along the run (1D smooth noise), the run thins and fades toward its end
        knots = r.uniform(0.55, 1.0, 9)
        wknots = r.uniform(0.6, 1.25, 7)
        pts = []
        for i in range(n + 1):
            t = i / n
            y = y0 + t * L
            x = x0 + wobble * ss * (np.sin(phase + y * freq) * 0.6 + np.sin(phase * 1.7 + y * freq * 2.9) * 0.4)
            pts.append((x, y, t))
        for (xa, ya, ta), (xb, yb, tb) in zip(pts, pts[1:]):
            fade = (1 - ta) ** 1.6
            op = np.interp(ta, np.linspace(0, 1, len(knots)), knots)
            wv = np.interp(ta, np.linspace(0, 1, len(wknots)), wknots)
            ww = max(1.0, wid * wv * (0.3 + 0.7 * (1 - ta) ** 0.7))
            val = float(strength * op * (0.15 + 0.85 * fade))
            for off in ((0,) if not wrap_x else (0, -W, W)):
                d.line([(xa + off, ya), (xb + off, yb)], fill=val, width=int(round(ww)))
        if beads and r.random() < 0.35:
            # a faint teardrop where the run stopped (not a hard dot)
            xe, ye, _ = pts[-1]
            br = max(1.5, wid * 0.35)
            for off in ((0,) if not wrap_x else (0, -W, W)):
                d.ellipse([xe + off - br, ye - br * 2.0, xe + off + br, ye + br], fill=float(strength * 0.22))
        acc = np.maximum(acc, np.asarray(img, np.float32))
    a = ndimage.gaussian_filter(acc, (ss * 2.0, ss * 1.4), mode=('nearest', 'wrap' if wrap_x else 'nearest'))
    a = a.reshape(h, ss, w, ss).mean(axis=(1, 3))
    # break the runs up along their length with long, soft variations (no hatching)
    breakup = spectral(shape, 2.2, seed + 5, aniso=(3.0, 1.0))
    a = a * (0.45 + 0.55 * smoothstep(0.15, 0.7, breakup))
    return np.clip(a / max(a.max(), 1e-6), 0, 1).astype(np.float32)


def tile_seam_error(a):
    """Mean absolute step across the wrap seams relative to the mean interior step (1.0 = seamless)."""
    a = np.asarray(a, np.float32)
    if a.ndim == 3:
        a = a.mean(axis=2)
    inner_x = np.abs(np.diff(a, axis=1)).mean()
    inner_y = np.abs(np.diff(a, axis=0)).mean()
    seam_x = np.abs(a[:, 0] - a[:, -1]).mean()
    seam_y = np.abs(a[0, :] - a[-1, :]).mean()
    return float(seam_x / max(inner_x, 1e-9)), float(seam_y / max(inner_y, 1e-9))
