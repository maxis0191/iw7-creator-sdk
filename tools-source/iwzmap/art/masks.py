"""Procedural grime / water / blood masks and feathered decals (deterministic, seeded).

All builders return float32 RGBA arrays in [0, 1] (straight alpha). Colour is premixed for an alpha-blend decal
(stock base material `wall_stain_01_dec`, techset w_l_sm_ndw_blend_i0c0: colour image with alpha), or, for
grime_mask_floor, a multiply-ready colour (white = no change) with the mask strength copied into alpha.
"""
import numpy as np
from scipy import ndimage

from . import noise as N

GRIME = np.array([0.15, 0.125, 0.10], np.float32)       # soot / dust / skin oil
OIL = np.array([0.10, 0.085, 0.07], np.float32)         # engine oil on steel
RUST = np.array([0.42, 0.24, 0.12], np.float32)
MINERAL = np.array([0.80, 0.78, 0.71], np.float32)      # calcite / efflorescence
BLOOD_WET = np.array([0.24, 0.025, 0.02], np.float32)
BLOOD_DRY = np.array([0.15, 0.045, 0.035], np.float32)


def _rgba(rgb, a):
    return np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)]).astype(np.float32)


def _mix(c0, c1, t):
    t = np.asarray(t, np.float32)[..., None]
    return c0 * (1 - t) + c1 * t


def grime_mask_floor(size=2048, seed=4701):
    """Tileable multiply mask for the diamond-plate floor: broad dirt, soaked-in oil stains with darker rims, drips,
    trolley-wheel smears, rust bloom, grit. RGB multiply colour (1 = clean), A = darkening strength."""
    sh = (size, size)
    broad = N.warp(N.fbm(sh, seed, 6, base=3.0 / size), seed + 1, amount=size * 0.03, scale=6.0 / size)
    mid = N.warp(N.fbm(sh, seed + 2, 5, base=6.0 / size), seed + 3, amount=size * 0.015, scale=8.0 / size)
    dirt = N.smoothstep(0.35, 0.95, broad * 0.65 + mid * 0.35)                     # 0 clean .. 1 dirty
    pools = N.blobs(sh, seed + 10, 6, size * 0.03, size * 0.07, irregular=0.45, elong=1.5, rough_base=9.0 / size)
    spills = N.blobs(sh, seed + 11, 22, size * 0.006, size * 0.02, irregular=0.4, elong=1.3, rough_base=25.0 / size)
    drips = N.blobs(sh, seed + 12, 50, size * 0.0012, size * 0.0035, irregular=0.3, rough_base=0.05)
    oil = np.maximum(pools, np.maximum(spills * 0.85, drips * 0.6))
    oil = N.warp(ndimage.gaussian_filter(oil, size * 0.0006, mode='wrap'), seed + 15, size * 0.003, 20.0 / size)
    soak = ndimage.gaussian_filter(oil, size * 0.006, mode='wrap')                  # oil wicks outward, faint
    rim = np.clip(oil - ndimage.gaussian_filter(oil, size * 0.003, mode='wrap'), 0, 1) * 2.0
    variation = 0.55 + 0.45 * N.fbm(sh, seed + 14, 4, base=10.0 / size)
    oil_strength = np.clip(oil * variation * 0.6 + rim * 0.25 + soak * 0.35, 0, 1)
    smear = N.spectral(sh, 2.4, seed + 20, aniso=(14.0, 1.0))                       # long soft wheel grain
    smear = 0.6 * N.smoothstep(0.75, 0.95, smear) * N.smoothstep(0.45, 0.8, N.fbm(sh, seed + 21, 3, base=3.0 / size))
    grit = N.smoothstep(0.78, 1.0, N.spectral(sh, 0.8, seed + 30, fmin=0.05))
    rust = N.smoothstep(0.62, 0.9, N.warp(N.fbm(sh, seed + 40, 5, base=4.0 / size), seed + 41, size * 0.02, 6.0 / size))
    rgb = np.ones(sh + (3,), np.float32)
    rgb = rgb * (1 - 0.42 * dirt[..., None]) + 0.42 * dirt[..., None] * (GRIME * 3.4)
    rgb = _mix(rgb, np.clip(rgb * (RUST * 2.0), 0, 1), rust * 0.3)
    rgb = _mix(rgb, OIL * 2.6, oil_strength * 0.8)
    rgb = rgb * (1 - 0.16 * smear[..., None])
    rgb = rgb * (1 - 0.10 * grit[..., None])
    rgb = np.clip(rgb, 0, 1)
    a = 1.0 - rgb.mean(axis=2)
    return _rgba(rgb, N.normalize(a, 0, 100))


def junction_grime(w=1024, h=256, seed=4702):
    """Horizontally tileable grime strip. The junction is the BOTTOM edge (floor/wall); flip vertically for a
    ceiling/wall junction. Alpha highest at the junction, 0 on the top rows, with mop-splash / rising-damp vertical
    breakup and a faint tide line."""
    sh = (h, w)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]            # 0 top .. 1 bottom
    up = 1 - yy                                                      # distance from the junction, 0..1
    reach = 0.22 + 0.38 * N.fbm((1, w), seed, 4, base=4.0 / w)[0][None, :]
    fibres = N.spectral(sh, 2.8, seed + 1, aniso=(6.0, 1.0))        # soft vertical runs
    reach = reach * (0.82 + 0.36 * fibres)
    base = N.smoothstep(reach, reach * 0.1, up) ** 1.4
    tide_mask = N.smoothstep(0.45, 0.75, N.fbm(sh, seed + 2, 3, base=5.0 / w))
    tide = np.exp(-((up - reach * 0.9) / 0.03) ** 2) * 0.12 * tide_mask
    mottling = N.fbm(sh, seed + 3, 5, base=10.0 / w)
    a = np.clip(base * (0.6 + 0.4 * mottling) + tide, 0, 1)
    a = a * N.smoothstep(0.02, 0.12, yy)
    tint = _mix(GRIME, RUST * 0.6, N.fbm(sh, seed + 4, 3, base=2.0 / w) * 0.45)
    rgb = tint * (0.8 + 0.4 * mottling[..., None])
    return _rgba(rgb, a * 0.9)


def water_streak(w=256, h=1024, seed=4703):
    """Ceiling-crack water streak (top = crack). Wet dark runs with whitish mineral deposits along their edges, rust
    toward the bottom; a hairline crack with a damp halo. Alpha reaches 0 on every border."""
    from PIL import Image, ImageDraw
    sh = (h, w)
    r = np.random.default_rng(seed)
    crack_y = int(h * 0.04)
    flow = N.streaks(sh, seed, 8, length=(0.3, 0.92), width=(3, 10), x_range=(0.34, 0.66), y0_range=(0.035, 0.05),
                     wobble=4.0, wrap_x=False)
    core = N.streaks(sh, seed + 1, 2, length=(0.6, 0.85), width=(12, 20), x_range=(0.45, 0.55),
                     y0_range=(0.035, 0.045), wobble=2.5, beads=False, wrap_x=False)
    trail = np.clip(np.maximum(flow * 0.8, core * 0.75), 0, 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    bloom = np.exp(-(((xx - w * 0.5) / (w * 0.26)) ** 2 + ((yy - crack_y) / (h * 0.035)) ** 2))
    bloom = bloom * (0.45 + 0.55 * N.fbm(sh, seed + 2, 4, base=0.015))
    wet = np.clip(np.maximum(trail, bloom * 0.55), 0, 1)
    k = 4
    cimg = Image.new('L', (w * k, h * k), 0)
    d = ImageDraw.Draw(cimg)
    x, y = w * 0.16 * k, crack_y * k
    pts = [(x, y)]
    while x < w * 0.84 * k:
        x += r.uniform(5, 14) * k / 2
        y = float(np.clip(y + r.normal(0, 2.2) * k / 2, (crack_y - 6) * k, (crack_y + 6) * k))
        pts.append((x, y))
    for i, ((xa, ya), (xb, yb)) in enumerate(zip(pts, pts[1:])):
        t = i / len(pts)
        d.line([(xa, ya), (xb, yb)], fill=255, width=max(1, int(k * (0.6 + 1.2 * np.sin(np.pi * t)))))
        if r.random() < 0.12:                                        # short hairline branch
            bx, by = xa, ya
            for _ in range(3):
                nx, ny = bx + r.uniform(-6, 6) * k / 2, by + r.uniform(2, 7) * k / 2
                d.line([(bx, by), (nx, ny)], fill=170, width=max(1, k // 2))
                bx, by = nx, ny
    crack = np.asarray(cimg.resize((w, h), Image.LANCZOS), np.float32) / 255
    halo = np.clip(ndimage.gaussian_filter(crack, 3.0) * 3, 0, 1)
    edge = np.clip(ndimage.gaussian_gradient_magnitude(trail, 1.2) * 7, 0, 1)
    mineral = edge * N.smoothstep(0.4, 0.75, N.fbm(sh, seed + 3, 4, base=0.03)) * N.smoothstep(0.05, 0.3, yy / h)
    depth = yy / h
    rgb = _mix(GRIME * 1.25, RUST * 0.75, N.smoothstep(0.25, 1.0, depth) * 0.55)
    rgb = _mix(rgb, MINERAL, mineral * 0.7)
    rgb = _mix(rgb, np.array([0.09, 0.08, 0.07], np.float32), np.clip(crack, 0, 1))
    a = np.clip(wet * 0.7 + halo * 0.4 + mineral * 0.3 + crack * 0.8, 0, 1)
    a = a * N.border_falloff(sh, 12)
    return _rgba(rgb, a)


def sign_grime_overlay(w=1024, h=1024, seed=4704):
    """Ageing overlay for enamel/printed signs: a yellow-brown film, grime gathered at the edges and corners, a few
    soft runs from the top edge, dust smudges, fine abrasion scratches (lighter colour). Alpha-blend it over the sign
    (age.apply_overlay draws it at the sign's own size, so runs keep their shape on 4:1 signs)."""
    from PIL import Image, ImageDraw
    sh = (h, w)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    s = min(w, h)
    dx = np.minimum(xx, w - 1 - xx) / s
    dy = np.minimum(yy, h - 1 - yy) / s
    blot = N.warp(N.fbm(sh, seed, 6, base=3.0 / s), seed + 1, amount=s * 0.02, scale=4.0 / s)
    edge = np.exp(-np.minimum(dx, dy) / 0.03) * (0.3 + 0.9 * blot)
    corner = np.exp(-np.sqrt(dx * dx + dy * dy) / 0.07)
    edge_grime = np.clip(edge * 0.55 + corner * 0.5, 0, 1)
    runs = N.streaks(sh, seed + 2, max(4, int(12 * w / 1024)), length=(0.12, 0.6), width=(3, 10),
                     y0_range=(0.0, 0.02), wobble=1.5)
    film = 0.07 + 0.09 * N.smoothstep(0.2, 0.9, N.fbm(sh, seed + 3, 4, base=2.5 / s))
    specks = N.smoothstep(0.93, 1.0, N.spectral(sh, 0.7, seed + 4, fmin=0.05)) * 0.35
    dust = N.blobs(sh, seed + 5, max(3, int(8 * w * h / 1024 ** 2)), s * 0.02, s * 0.06, irregular=0.9, elong=1.6,
                   wrap=False, rough_base=0.006) * 0.09
    dark_a = np.clip(film + edge_grime * 0.7 + runs * 0.16 + specks + dust, 0, 1)
    r = np.random.default_rng(seed + 6)
    k = 2
    simg = Image.new('L', (w * k, h * k), 0)
    d = ImageDraw.Draw(simg)
    for _ in range(int(60 * w * h / 1024 ** 2)):
        x0, y0 = r.uniform(0, w * k), r.uniform(0, h * k)
        ang = r.normal(0.15, 0.5)
        L = r.uniform(s * 0.005, s * 0.035) * k
        bend = r.normal(0, 0.15)
        pts = [(x0 + np.cos(ang + bend * t) * L * t, y0 + np.sin(ang + bend * t) * L * t) for t in np.linspace(0, 1, 6)]
        d.line(pts, fill=int(r.uniform(60, 160)), width=1)
    scratch = np.asarray(simg.resize((w, h), Image.LANCZOS), np.float32) / 255
    tint = _mix(GRIME, np.array([0.34, 0.27, 0.15], np.float32), N.smoothstep(0.3, 0.8, blot) * 0.6)
    rgb = _mix(tint, np.array([0.80, 0.78, 0.74], np.float32), np.clip(scratch * 2.5, 0, 1))
    a = np.clip(np.maximum(dark_a, scratch * 0.45), 0, 1)
    return _rgba(rgb, a)


def decal_blood_feathered(size=512, seed=4705):
    """A drag smear running bottom -> top: a pooled stain at the bottom that is smeared upward, the trail made of
    thickness variations ALONG the drag (cloth/limb drag marks), thinning and going translucent toward its end; dried
    darker rims where it is thick, a few satellite drops. Not gory. Feathered alpha, 0 at every border."""
    sh = (size, size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    cx = 0.5 + 0.07 * np.sin((yy - 0.1) * 3.2) - 0.05 * (0.8 - yy)
    t = N.smoothstep(0.78, 0.1, yy)                  # 0 at the pool, 1 at the far end
    wv = N.fbm((size, 1), seed + 8, 4, base=6.0 / size)[:, 0][:, None]          # irregular width along the drag
    half_w = (0.12 * (1 - 0.55 * t) + 0.02) * (0.6 + 0.8 * wv)
    lateral = (xx - cx) / half_w
    edge_noise = (N.fbm(sh, seed + 2, 4, base=0.012) - 0.5) * 0.45
    trail_cover = N.smoothstep(1.0, 0.85, np.abs(lateral) + edge_noise)
    trail_cover = trail_cover * N.smoothstep(0.86, 0.74, yy)
    fibres = N.warp(N.spectral(sh, 2.0, seed, aniso=(18.0, 1.0)), seed + 1, amount=2, scale=0.01)
    # thickness: drag fibres, fading with t; the end feathers out by thickness, not by spikes
    thickness = trail_cover * (0.25 + 0.75 * fibres) * (1 - t) ** 0.8
    thickness = thickness * N.smoothstep(0.0, 0.25, 1 - t + edge_noise * 0.3)
    py, px = 0.78, 0.53
    pd = np.sqrt(((xx - px) / 0.15) ** 2 + ((yy - py) / 0.11) ** 2)
    pool_cover = N.smoothstep(1.0, 0.92, pd + (N.fbm(sh, seed + 3, 4, base=0.01) - 0.5) * 0.5)
    pool = pool_cover * (0.65 + 0.35 * N.fbm(sh, seed + 7, 4, base=0.02))
    drops = N.blobs(sh, seed + 4, 12, size * 0.003, size * 0.009, irregular=0.15, wrap=False, rough_base=0.05)
    drops = (drops > 0.5).astype(np.float32) * 0.8 * N.smoothstep(0.3, 0.15, np.abs(xx - 0.52)) * N.smoothstep(0.5, 0.7, yy)
    thick = np.clip(np.maximum(np.maximum(thickness, pool), drops), 0, 1)
    thick = ndimage.gaussian_filter(thick, 0.8)
    body = ndimage.gaussian_filter(thick, size * 0.01)
    rim = np.clip(thick - body, 0, 1) * 1.6 * N.smoothstep(0.3, 0.6, body)
    rgb = _mix(BLOOD_DRY, BLOOD_WET, np.clip(body * 1.2, 0, 1) * (0.7 + 0.3 * N.fbm(sh, seed + 6, 3, base=0.01)))
    rgb = rgb * (1 - 0.35 * np.clip(rim, 0, 1)[..., None])
    a = np.clip(N.smoothstep(0.02, 0.45, thick) * 0.92 + rim * 0.1, 0, 0.94)
    a = a * N.border_falloff(sh, size * 0.06, seed + 5, wobble=size * 0.02)
    return _rgba(rgb, a)


def decal_grime_feathered(size=512, seed=4706):
    """Floor grime patch: a dried dirty-water stain. Irregular outline with tide lines where the puddle dried, mottled
    interior with ground-in grit, a darker core and two boot-scuff arcs. Feathered alpha reaching 0 at the border."""
    sh = (size, size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    d = np.sqrt(((xx - 0.5) / 0.40) ** 2 + ((yy - 0.5) / 0.34) ** 2)
    shape = N.warp(N.fbm(sh, seed, 5, base=0.008), seed + 1, amount=size * 0.015, scale=0.008)
    level = d + (shape - 0.5) * 0.8
    cover = N.smoothstep(0.95, 0.8, level)
    tide = np.zeros(sh, np.float32)
    for lv, wgt in ((0.88, 0.55), (0.72, 0.3), (0.55, 0.22)):          # tide lines of successive drying
        tide = np.maximum(tide, np.exp(-((level - lv) / 0.012) ** 2) * wgt)
    tide = tide * N.smoothstep(0.35, 0.65, N.fbm(sh, seed + 4, 3, base=0.02))
    mottle = N.fbm(sh, seed + 2, 5, base=0.02)
    core = N.smoothstep(0.55, 0.15, level)
    grit = N.smoothstep(0.8, 1.0, N.spectral(sh, 0.9, seed + 3, fmin=0.05))
    scuff = np.zeros(sh, np.float32)
    ang = np.arctan2(yy - 0.5, xx - 0.5)
    rad = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    for k, (r0, a0, a1) in enumerate(((0.26, 0.3, 1.5), (0.17, -2.6, -1.5))):
        band = np.exp(-((rad - r0) / 0.01) ** 2) * N.smoothstep(a0, a0 + 0.3, ang) * N.smoothstep(a1, a1 - 0.3, ang)
        scuff = np.maximum(scuff, band * N.smoothstep(0.3, 0.7, N.spectral(sh, 1.5, seed + 10 + k)))
    a = cover * (0.28 + 0.25 * mottle + 0.2 * core) + tide * 0.4 + grit * cover * 0.2 + scuff * cover * 0.25
    a = np.clip(a, 0, 0.85) * N.border_falloff(sh, size * 0.08)
    rgb = _mix(GRIME * 1.3, OIL, np.clip(core + tide, 0, 1)) * (0.85 + 0.3 * mottle[..., None])
    return _rgba(rgb, a)
