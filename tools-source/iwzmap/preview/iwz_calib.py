"""Frame comparison metrics for the Station Zero preview (numpy + PIL, plain Python).

edge score  structure alignment: Sobel magnitude of the blurred log luminance, the strongest EDGE_FRAC of the unmasked
            pixels of each image are 'edges'; score = IoU of the two edge sets after a TOL pixel dilation of each
            (the dilation makes a 1-2 px registration error free, a real camera error is not).
luminance   mean linear luminance of the unmasked pixels (sRGB decoded), ratio = preview / engine.
One fixed MASK covers what the engine frame draws and the preview cannot: the first person weapon, hands, the build
string watermark and the corner HUD icon.
"""
import numpy as np

EDGE_FRAC = 0.06
TOL = 3
SIGMA = 1.6


def mask_1280x720():
    m = np.ones((720, 1280), bool)
    m[400:, 560:] = False       # first person weapon and hands (lower right)
    m[640:, :] = False          # build string watermark row
    m[:60, 1180:] = False       # corner icon
    return m


def srgb_to_lin(x):
    x = np.asarray(x, np.float32)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def lum(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def _blur(a, sigma):
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode='edge')
    h, w = a.shape
    t = sum(k[i] * p[:, i:i + w] for i in range(2 * r + 1))
    return sum(k[i] * t[i:i + h, :] for i in range(2 * r + 1))


def edges(lin_lum, mask):
    g = _blur(np.log(np.maximum(lin_lum, 1e-4)), SIGMA)
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = np.hypot(gx, gy)
    mag[~mask] = 0
    thr = np.quantile(mag[mask], 1 - EDGE_FRAC)
    return (mag >= thr) & mask


def _dilate(b, r):
    out = b.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(b, dy, 0), dx, 1)
    return out


def engine_edges(eng_srgb, mask):
    return edges(lum(srgb_to_lin(eng_srgb)), mask)


def edge_score(eng_srgb, prev_lin, mask, e1=None):
    """eng_srgb: HxWx3 in 0..1 (display values); prev_lin: HxWx3 display-linear. -> IoU in 0..1
    e1: the engine edge set when already computed (engine_edges)."""
    if e1 is None:
        e1 = engine_edges(eng_srgb, mask)
    e2 = edges(lum(prev_lin), mask)
    d1, d2 = _dilate(e1, TOL), _dilate(e2, TOL)
    inter = (e1 & d2).sum() + (e2 & d1).sum()
    union = e1.sum() + e2.sum()
    return float(inter / max(union, 1))


def mean_lum(lin, mask):
    return float(lum(lin)[mask].mean())


def tonemap(raw, k, p):
    """raw linear preview radiance -> display-linear: clip(k * raw) ** p"""
    return np.clip(raw * k, 0, 1) ** p


def fit_tonemap(raws, engines, mask):
    """One global (k, p): least squares of log(engine mean lum) = p * log(k * raw mean lum), over frames."""
    x = np.array([np.log(max(mean_lum(r, mask), 1e-7)) for r in raws])
    y = np.array([np.log(max(mean_lum(srgb_to_lin(e), mask), 1e-7)) for e in engines])
    p, b = np.polyfit(x, y, 1)
    p = float(np.clip(p, 0.2, 1.5))
    b = float(np.mean(y - p * x))
    k = float(np.exp(b / p))
    return k, p
