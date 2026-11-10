"""Blood decals, four physically different patterns (coordinator review g25: one blob silhouette read as a map outline).

Each builder returns a 512x512 (by default) straight-alpha RGBA float array, feathered to alpha 0 on every border.
Reference behaviour, written down before building:
  hand smear  - a hand pressed on a wall then slid down: a dense palm/finger contact print at the top, then four
                parallel finger streaks (and a short thumb streak) pulled downward. In each streak the blood is pushed
                to the edges (darker ridges, thinner lighter middle); the streaks thin and break up where the hand
                lifted off.
  body drag   - a wide band (shoulder width) that narrows and fades along the drag. Long parallel striations from
                cloth run in the drag direction; edges are ragged; there are skips where the body lifted, denser blood
                at the start and only streak remnants at the end.
  spatter     - an impact stain with satellite drops. Drop size falls off with distance and drops elongate the further
                they flew, with the narrow tail pointing AWAY from the source (direction of travel); fine mist dots.
  dried pool  - a lobed, surface-tension outline. Blood coagulates at the margin (a dark rim, coffee-ring effect); the
                interior dries lighter and translucent with shrinkage cracks; a pale serum halo sits just outside the
                edge.
Colours stay oxidised (maroon to brown), never cartoon red. The material is a lit alpha blend (base wall_stain_01_dec).
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from . import noise as N

FRESH = np.array([0.26, 0.025, 0.02], np.float32)     # thick, still glossy-dark
DRIED = np.array([0.17, 0.05, 0.035], np.float32)     # thin, oxidised brown
CLOT = np.array([0.09, 0.015, 0.012], np.float32)     # coagulated margin
SERUM = np.array([0.50, 0.33, 0.20], np.float32)      # pale serum halo


def _finish(thick, seed, size, extra_rim=0.0, halo=None):
    """thickness field -> RGBA. Thin = brown and translucent; thick = dark; edges of thick areas darker (rim)."""
    thick = np.clip(ndimage.gaussian_filter(thick, 0.7), 0, 1)
    body = ndimage.gaussian_filter(thick, size * 0.008)
    rim = np.clip((thick - body) * 2.2, 0, 1) * N.smoothstep(0.15, 0.5, thick)
    tone = np.clip(thick * 1.15, 0, 1) * (0.8 + 0.2 * N.fbm(thick.shape, seed, 3, base=0.015))
    rgb = DRIED * (1 - tone[..., None]) + FRESH * tone[..., None]
    k = np.clip(rim * 0.6 + extra_rim, 0, 1)[..., None]
    rgb = rgb * (1 - k) + CLOT * k
    a = N.smoothstep(0.03, 0.5, thick) * 0.93
    if halo is not None:
        hk = np.clip(halo, 0, 1)
        rgb = rgb * (1 - (hk * (1 - a))[..., None]) + SERUM * (hk * (1 - a))[..., None]
        a = np.maximum(a, hk * 0.28)
    a = a * N.border_falloff(thick.shape, size * 0.05, seed + 1, wobble=size * 0.015)
    return np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)]).astype(np.float32)


def _ridge_profile(lat):
    """Across a smear: blood pushed to the sides. lat in [-1, 1] -> thickness factor (edges ~1, middle ~0.45)."""
    u = np.abs(lat)
    return 0.45 + 0.55 * u ** 3


def _print_texture(sh, seed):
    """Partial transfer of a contact print: skin ridges and voids."""
    ridges = 0.5 + 0.5 * np.sin(N.warp(N.spectral(sh, 2.0, seed, aniso=(1.0, 3.0)) * 60.0, seed + 1, 6, 0.02))
    voids = N.smoothstep(0.3, 0.55, N.fbm(sh, seed + 2, 4, base=0.03))
    return np.clip((0.55 + 0.45 * ridges) * (0.35 + 0.65 * voids), 0, 1)


def blood_hand_smear(size=512, seed=4811):
    sh = (size, size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    edge_n = (N.fbm(sh, seed, 4, base=0.02) - 0.5)
    tex = _print_texture(sh, seed + 7)
    thick = np.zeros(sh, np.float32)
    # contact print: palm heel (lower) and four finger pads (upper), the hand rested fingers-up then slid down
    fingers = [(-0.105, 0.030, 0.58), (-0.035, 0.034, 0.66), (0.035, 0.033, 0.64), (0.10, 0.028, 0.54)]
    pads = [(0.5 + off, 0.13 + 0.012 * abs(i - 1.5), hw * 1.05, 0.05) for i, (off, hw, _) in enumerate(fingers)]
    pads.append((0.50, 0.25, 0.15, 0.085))                       # palm
    pads.append((0.69, 0.27, 0.032, 0.06))                       # thumb
    for px, py, rx, ry in pads:
        dd = np.sqrt(((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2) + edge_n * 0.3
        thick = np.maximum(thick, N.smoothstep(1.0, 0.8, dd) * tex * 0.95)
    fib = N.spectral(sh, 1.8, seed + 2, aniso=(24.0, 1.0))
    streaks = [(off, hw, ln, 0.15) for off, hw, ln in fingers] + [(0.19, 0.028, 0.26, 0.28)]
    for i, (off, half_w, length, y0) in enumerate(streaks):
        t = np.clip((yy - y0) / length, 0, 1)
        cx = 0.5 + off + 0.04 * t * t + 0.006 * np.sin(t * 9 + i)
        w = half_w * (1 - 0.45 * t) * (0.9 + 0.2 * N.fbm((size, 1), seed + 10 + i, 3, base=0.02)[:, 0][:, None])
        lat = (xx - cx) / w
        inside = N.smoothstep(1.0, 0.8, np.abs(lat) + edge_n * 0.25) * N.smoothstep(y0 - 0.01, y0 + 0.04, yy)
        lift = N.smoothstep(1.0, 0.75, t + (fib - 0.5) * 0.35)
        streak = inside * _ridge_profile(np.clip(lat, -1, 1)) * lift * (0.35 + 0.65 * fib) * (1 - 0.4 * t)
        thick = np.maximum(thick, streak)
    return _finish(thick, seed + 3, size)


def blood_drag_trail(size=512, seed=4812):
    sh = (size, size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    ang = math.radians(-38)
    u = (xx - 0.5) * math.cos(ang) - (yy - 0.5) * math.sin(ang)
    v = (xx - 0.5) * math.sin(ang) + (yy - 0.5) * math.cos(ang)
    t = np.clip((u + 0.46) / 0.9, 0, 1)
    k = 1024
    meander = N.fbm((1, k), seed + 9, 2, base=0.8 / k)[0]                 # one or two slow bends along the drag
    vc = (meander[(t * (k - 1)).astype(np.int64)] - 0.5) * 0.06
    half_w = (0.14 * (1 - 0.6 * t ** 0.9) + 0.014) * (0.85 + 0.3 * N.fbm(sh, seed, 3, base=0.006))
    lat = (v - vc) / half_w
    ragged = (N.fbm(sh, seed + 1, 5, base=0.025) - 0.5) * 0.45
    band = N.smoothstep(1.0, 0.82, np.abs(lat) + ragged) * N.smoothstep(0.0, 0.06, t + ragged * 0.05) \
        * N.smoothstep(1.0, 0.9, t)
    stri1d = N.spectral((1, k), 1.3, seed + 2)[0]
    wav = 0.0025 * np.sin(u * 9 + 1.0)                                  # gentle sway of the striations
    idx = ((v - vc + 0.5 + wav) * k * 0.9).astype(np.int64) % k
    stri = stri1d[idx]
    keep = N.smoothstep(0.2 + 0.45 * t, 0.42 + 0.45 * t, stri)
    skips = N.smoothstep(0.2, 0.45, N.fbm((1, k), seed + 3, 3, base=6.0 / k)[0][(t * (k - 1)).astype(np.int64)])
    thick = band * (0.35 + 0.65 * keep) * (1 - 0.5 * t) * (0.5 + 0.5 * skips)
    # where the body lay: denser but uneven (cloth pattern, voids), blending into the trail rather than a lump
    start = np.sqrt(((u + 0.38) / 0.10) ** 2 + ((v - vc) / 0.14) ** 2) + ragged * 0.7
    lay = N.smoothstep(1.0, 0.75, start) * (0.45 + 0.55 * N.smoothstep(0.3, 0.6, N.fbm(sh, seed + 4, 4, base=0.025)))
    thick = np.maximum(thick, lay * 0.9)
    return _finish(thick, seed + 5, size)


def blood_spatter(size=512, seed=4813):
    """Impact spatter on a surface. Central stain with short spines (the crown), satellites round near the source and
    progressively oval with a short blunt tail further out (tail = direction of travel), detached daughter drops, mist."""
    sh = (size, size)
    r = np.random.default_rng(seed)
    S = 3
    W = size * S
    sx, sy = 0.42 * W, 0.56 * W
    im = Image.new('F', (W, W), 0.0)
    d = ImageDraw.Draw(im)
    main_dir = math.radians(-30)
    # central stain: irregular outline with spines
    pts = []
    base_r = 0.065 * W
    n = 120
    spikes = r.uniform(0.0, 1.0, n)
    wob = N.fbm((1, n), seed + 7, 3, base=0.05)[0]
    for i, q in enumerate(np.linspace(0, 2 * math.pi, n, endpoint=False)):
        bias = 1.0 + 0.25 * max(0.0, math.cos(q - main_dir))
        spine = (0.22 + 0.25 * max(0.0, math.cos(q - main_dir))) * spikes[i] if i % 3 == 0 and spikes[i] > 0.45 else 0
        rr = base_r * bias * (0.85 + 0.2 * (wob[i] - 0.5) + spine)
        pts.append((sx + math.cos(q) * rr, sy + math.sin(q) * rr))
    d.polygon(pts, fill=1.0)

    def drop(px, py, a, rad, elong, val):
        ca, sa = math.cos(a), math.sin(a)
        poly = []
        for q in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            # an ellipse elongated along the travel direction, with the far end slightly pointed (blunt tail)
            ex = math.cos(q) * rad * elong
            ey = math.sin(q) * rad
            if ex > 0:
                ey *= 1 - 0.35 * (ex / (rad * elong))
            poly.append((px + ex * ca - ey * sa, py + ex * sa + ey * ca))
        d.polygon(poly, fill=val)

    for _ in range(70):
        a = main_dir + r.normal(0, 0.7)
        dist = (0.10 + r.exponential(0.11)) * W
        if dist > 0.42 * W:
            continue
        rel = dist / W
        rad = max(1.4 * S, (0.017 - 0.03 * rel) * W * r.uniform(0.5, 1.3))
        elong = 1.0 + 2.2 * max(0.0, rel - 0.08) * r.uniform(0.6, 1.4)
        px, py = sx + math.cos(a) * dist, sy + math.sin(a) * dist
        drop(px, py, a, rad, elong, float(r.uniform(0.7, 1.0)))
        if elong > 1.4 and r.random() < 0.35:            # daughter droplet thrown off the tail
            q = rad * elong + r.uniform(3, 8) * S
            drop(px + math.cos(a) * q, py + math.sin(a) * q, a, rad * 0.3, 1.2, 0.75)
    for _ in range(220):
        a = main_dir + r.normal(0, 0.9)
        dist = (0.08 + r.exponential(0.15)) * W
        if dist > 0.44 * W:
            continue
        rr = r.uniform(0.4, 1.2) * S
        px, py = sx + math.cos(a) * dist, sy + math.sin(a) * dist
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=float(r.uniform(0.35, 0.7)))
    f = np.asarray(im, np.float32).reshape(size, S, size, S).mean(axis=(1, 3))
    f = f * (0.8 + 0.35 * N.fbm(sh, seed + 1, 4, base=0.05))
    return _finish(np.clip(f, 0, 1), seed + 2, size)


def _crack_network(sh, seed, cells=70):
    """Shrinkage cracks: edges of a jittered Voronoi tessellation (distance to 2nd nearest - nearest site)."""
    from scipy.spatial import cKDTree
    h, w = sh
    r = np.random.default_rng(seed)
    pts = r.uniform(0, 1, (cells, 2)) * [w, h]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = xx + (N.fbm(sh, seed + 1, 3, base=0.02) - 0.5) * 18
    wy = yy + (N.fbm(sh, seed + 2, 3, base=0.02) - 0.5) * 18
    dist, _ = cKDTree(pts).query(np.stack([wx.ravel(), wy.ravel()], 1), k=2)
    gap = (dist[:, 1] - dist[:, 0]).reshape(h, w)
    width = 0.55 + 0.35 * N.fbm(sh, seed + 3, 3, base=0.03)
    return N.smoothstep(width * 1.5, width * 0.3, gap) * 0.9


def blood_dried_pool(size=512, seed=4814):
    sh = (size, size)
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    dx, dy = xx - 0.5, yy - 0.52
    th = np.arctan2(dy, dx)
    rad = 0.30
    lobes = sum(r.uniform(0.03, 0.08) * np.sin(k * th + r.uniform(0, 6.28)) for k in (2, 3, 5, 7))
    outline = rad * (1 + lobes) * (0.97 + 0.06 * N.fbm(sh, seed, 3, base=0.03))
    dn = np.sqrt(dx * dx + (dy * 1.15) ** 2) / outline
    inside = N.smoothstep(1.0, 0.985, dn)
    interior = 0.42 + 0.18 * N.fbm(sh, seed + 1, 4, base=0.02)
    rim = np.exp(-((dn - 0.955) / 0.03) ** 2)
    cracks = _crack_network(sh, seed + 2) * N.smoothstep(0.92, 0.6, dn)    # cracks in the thin dried interior only
    thick = inside * np.clip(interior + rim * 0.55, 0, 1) * (1 - 0.8 * cracks)
    drops = N.blobs(sh, seed + 3, 9, size * 0.006, size * 0.016, irregular=0.2, wrap=False, rough_base=0.05)
    ring = N.smoothstep(1.05, 1.15, dn) * N.smoothstep(1.6, 1.3, dn)
    thick = np.maximum(thick, (drops > 0.5) * ring * 0.8)
    halo = np.exp(-((dn - 1.035) / 0.03) ** 2) * (1 - inside) * 0.9 * (0.6 + 0.4 * N.fbm(sh, seed + 4, 3, base=0.03))
    return _finish(thick, seed + 5, size, extra_rim=rim * inside * 0.55, halo=halo)


VARIANTS = {'hand': blood_hand_smear, 'drag': blood_drag_trail, 'spatter': blood_spatter, 'pool': blood_dried_pool}
