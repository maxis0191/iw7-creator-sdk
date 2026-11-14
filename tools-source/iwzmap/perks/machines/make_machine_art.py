"""Texture art of the four new Station Zero perk machines (06-PERKS.md section 2), drawn from code (PIL + numpy).

    python -I -B make_machine_art.py <out dir>

Writes into <out dir>:
  <m>_atlas.png      1024 x 1024 albedo atlas per machine (signs, labels, dial, contents of the drum / globe, curtain...)
  <m>_glow_e.png     its emissive mask (lit sign and bulbs, black elsewhere): the same atlas drives the glow material
  <m>_rects.json     the atlas rectangles (pixels, top-left origin) the Blender builder maps faces to
  tiles: enamel_*.png (tileable painted enamel with chips and grime), walnut.png, kraft.png, metal_c.png (dark brushed
  base of metals), spec_chrome.png / spec_brass.png / spec_gilt.png (metal F0 colour maps), rubber.png
Nothing is taken from another game: every sign, mascot and emblem is drawn here.
Machines: bakers, voyage, grudge, double.
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = 'C:/Windows/Fonts/'
S = 1024                     # atlas size
SS = 2                       # supersampling of drawn art


def font(name, px):
    return ImageFont.truetype(FONTS + name, int(px))


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- tileable noise
def tnoise(n, scale, seed, aniso=(1.0, 1.0)):
    """Periodic smooth noise in 0..1 (FFT low-pass of white noise: tiles seamlessly)."""
    r = np.random.default_rng(seed)
    w = r.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None] * aniso[1]
    fx = np.fft.fftfreq(n)[None, :] * aniso[0]
    f = np.sqrt(fx * fx + fy * fy)
    g = np.exp(-(f * scale) ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def enamel(base, seed, n=512, chips=22, chip_col=(92, 60, 38), grime=0.2, mottle=0.03, runs=0.16):
    """Old painted enamel after a year sealed underground, tileable: soft mottling, dust, vertical grime runs, a few
    rust streaks under small chips worn through to rusty metal (dark rim, rust-brown core)."""
    b = np.array(base, np.float32)[None, None, :]
    mot = tnoise(n, 40, seed) - 0.5
    img = b * (1 + mottle * 2 * mot[..., None])
    gr = tnoise(n, 30, seed + 1) ** 2.0
    img = img * (1 - grime * gr[..., None])
    run = tnoise(n, 3, seed + 5, aniso=(1.0, 30.0)) ** 3
    img = img * (1 - runs * run[..., None]) + np.array([40, 34, 26]) * (runs * 0.4 * run[..., None])
    dust = tnoise(n, 0.8, seed + 6)
    img = img * 0.96 + np.array([120, 116, 108]) * 0.04 * dust[..., None]
    r = random.Random(seed)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    streaks = Image.new('L', (n, n), 0)
    sd = ImageDraw.Draw(streaks)
    d = ImageDraw.Draw(im)
    for k in range(chips):
        x, y, sz = r.randrange(n), r.randrange(n), r.uniform(1.5, 4.5)
        pts = [(x + sz * math.cos(a_) * r.uniform(0.5, 1.3), y + sz * math.sin(a_) * r.uniform(0.4, 1.0))
               for a_ in np.linspace(0, 2 * math.pi, 8)[:-1]]
        if k % 3 == 0:                                   # a rust streak running down from every third chip
            L = r.uniform(15, 60)
            for ox in (-n, 0, n):
                sd.line([(x + ox, y), (x + ox + r.uniform(-2, 2), y + L)], fill=150, width=int(max(1, sz * 0.8)))
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                pp = [(px + ox, py + oy) for px, py in pts]
                d.polygon(pp, fill=tuple(int(c * 0.45) for c in chip_col))
                cx_, cy_ = x + ox, y + oy
                d.polygon([(cx_ + (px - x) * 0.65, cy_ + (py - y) * 0.65) for px, py in pts], fill=chip_col)
    sm = np.asarray(streaks.filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255.0
    a2 = np.asarray(im, np.float32)
    a2 = a2 * (1 - 0.45 * sm) + np.array([110, 62, 30]) * 0.45 * sm
    return Image.fromarray(np.clip(a2, 0, 255).astype(np.uint8))


def walnut(n=512, seed=5):
    """Varnished walnut, grain running along v (vertical on the cabinet's faces): fine straight grain lines, soft
    figure, low contrast."""
    xx = np.arange(n)[None, :]
    warp = tnoise(n, 60, seed) * 25
    figure = np.sin((xx + warp) / n * 2 * math.pi * 3) * 0.5 + 0.5
    grain = tnoise(n, 2.0, seed + 2, aniso=(1.0, 40.0))
    lines = (tnoise(n, 1.0, seed + 3, aniso=(1.0, 60.0)) > 0.62).astype(np.float32)
    t = 0.25 * figure + 0.6 * grain - 0.25 * lines
    t = (t - t.min()) / (t.max() - t.min())
    dark, light = np.array([52, 29, 16]), np.array([98, 57, 31])
    img = dark + (light - dark) * t[..., None]
    img = img * (1 - 0.18 * tnoise(n, 30, seed + 9)[..., None] ** 2)            # a year of dust and handling
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def kraft(n=256, seed=9):
    t = tnoise(n, 3, seed, aniso=(0.3, 1.0)) * 0.6 + tnoise(n, 20, seed + 1) * 0.4
    img = np.array([168, 128, 82]) * (0.85 + 0.25 * t[..., None])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def metal_base(n=256, seed=11):
    t = tnoise(n, 1.2, seed, aniso=(0.02, 1.0))
    v = 14 + 10 * t
    return Image.fromarray(np.dstack([v, v, v]).astype(np.uint8))


def spec(colour, n=64, seed=13, var=0.06):
    t = tnoise(n, 6, seed)
    img = np.array(colour, np.float32) * (1 - var + 2 * var * t[..., None])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- drawing helpers (on a supersampled canvas)
class Canvas:
    def __init__(self, bg=(0, 0, 0)):
        self.im = Image.new('RGB', (S * SS, S * SS), bg)
        self.glow = Image.new('RGB', (S * SS, S * SS), (0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.g = ImageDraw.Draw(self.glow)
        self.rects = {}

    def rect(self, name, x, y, w, h):
        self.rects[name] = [x, y, w, h]
        return [v * SS for v in (x, y, w, h)]

    def paste(self, name, img, glow=None):
        x, y, w, h = self.rects[name]
        self.im.paste(img.resize((w * SS, h * SS), Image.Resampling.LANCZOS), (x * SS, y * SS))
        if glow is not None:
            self.glow.paste(glow.resize((w * SS, h * SS), Image.Resampling.LANCZOS), (x * SS, y * SS))

    def save(self, out, m):
        self.im.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(out, m + '_atlas.png'))
        self.glow.resize((S, S), Image.Resampling.LANCZOS).save(os.path.join(out, m + '_glow_e.png'))
        json.dump({'size': S, 'rects': self.rects}, open(os.path.join(out, m + '_rects.json'), 'w'), indent=1)


def panel(w, h, bg):
    return Image.new('RGB', (w * SS, h * SS), bg)


def text_center(d, cx, cy, s, f, fill, stroke=0, stroke_fill=None, spacing=0):
    if spacing:
        widths = [d.textlength(ch, font=f) for ch in s]
        total = sum(widths) + spacing * (len(s) - 1)
        x = cx - total / 2
        for ch, wch in zip(s, widths):
            d.text((x, cy), ch, font=f, fill=fill, anchor='lm', stroke_width=stroke, stroke_fill=stroke_fill)
            x += wch + spacing
        return
    d.text((cx, cy), s, font=f, fill=fill, anchor='mm', stroke_width=stroke, stroke_fill=stroke_fill)


def fit_font(d, s, name, max_w, max_px):
    px = max_px
    while px > 8:
        f = font(name, px)
        if d.textlength(s, font=f) <= max_w:
            return f
        px -= 2
    return font(name, 8)


def round_rect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def grime_overlay(img, seed, amount=0.25):
    a = np.asarray(img).astype(np.float32)
    n = tnoise(256, 10, seed)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize(img.size, Image.Resampling.BILINEAR)) / 255.0
    edge = np.ones(a.shape[:2])
    h, w = edge.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / max(8.0, 0.08 * min(h, w))
    edge = np.clip(dist, 0, 1)
    k = 1 - amount * (n ** 2) - 0.25 * (1 - edge)
    return Image.fromarray(np.clip(a * k[..., None], 0, 255).astype(np.uint8))


def candies(w, h, seed, colours, sugar=True, pucker=False, bg=(30, 18, 14), size=(16, 26), glass=True, shape='round'):
    """A packed layer of drops (front view of a glass drum or globe's contents), seamless in x.
    shape 'round': glossy drops; 'dome': sugared jelly drops (flat-bottomed domes, matte, crusted with sugar);
    pucker: sour drops with a crinkled star pucker and a dark centre."""
    r = random.Random(seed)
    im = panel(w, h, bg)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    rows = []
    y = -10 * SS
    while y < H + 40 * SS:
        rows.append(y)
        y += int(size[0] * SS * (0.95 if shape == 'dome' else 1.2))
    for row in rows:
        x = r.uniform(0, 20)
        while x < W:
            rad = r.uniform(*size) * SS / 2
            cx, cy = x, row + r.uniform(-5, 5) * SS
            col = r.choice(colours)
            shade = tuple(int(c * 0.5) for c in col)
            lite = tuple(min(255, int(c * 0.55 + 120)) for c in col)
            for ox in (-W, 0, W):
                X = cx + ox
                if shape == 'dome':
                    d.chord((X - rad, cy - rad, X + rad, cy + rad * 1.2), 180, 360, fill=shade)
                    d.rectangle((X - rad, cy + rad * 0.1 - 1, X + rad, cy + rad * 0.45), fill=shade)
                    d.chord((X - rad * 0.86, cy - rad * 0.86, X + rad * 0.82, cy + rad * 0.9), 180, 360, fill=col)
                    d.rectangle((X - rad * 0.86, cy, X + rad * 0.82, cy + rad * 0.3), fill=col)
                    d.ellipse((X - rad * 0.5, cy - rad * 0.7, X - rad * 0.05, cy - rad * 0.35), fill=lite)
                else:
                    d.ellipse((X - rad, cy - rad * 0.9, X + rad, cy + rad * 0.9), fill=shade)
                    d.ellipse((X - rad * 0.88, cy - rad * 0.82, X + rad * 0.8, cy + rad * 0.68), fill=col)
                    if pucker:
                        n = r.randint(6, 8)
                        a0 = r.uniform(0, 1)
                        for k in range(n):
                            a = a0 + 2 * math.pi * k / n
                            d.line([(X + rad * 0.12 * math.cos(a), cy + rad * 0.12 * math.sin(a)),
                                    (X + rad * 0.78 * math.cos(a + 0.25), cy + rad * 0.66 * math.sin(a + 0.25))],
                                   fill=shade, width=max(2, int(2.2 * SS)))
                        d.ellipse((X - rad * 0.16, cy - rad * 0.14, X + rad * 0.16, cy + rad * 0.14), fill=shade)
                    hl = (X - rad * 0.6, cy - rad * 0.62, X - rad * 0.12, cy - rad * 0.25)
                    d.ellipse(hl, fill=lite)
            x += rad * 2 * r.uniform(0.92, 1.05)
    if sugar:
        dens = 7 if shape == 'dome' else 9
        for _ in range(int(W * H / (SS * SS) / dens)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            v = r.randint(205, 255)
            d.rectangle((x, y, x + SS * 0.8, y + SS * 0.8), fill=(v, v, v - 8))
    if glass:      # glass: two vertical highlight streaks and a slight grey film
        a = np.asarray(im).astype(np.float32)
        xx = np.arange(W)[None, :] / W
        streak = np.exp(-((xx - 0.18) / 0.025) ** 2) * 0.6 + np.exp(-((xx - 0.23) / 0.008) ** 2) * 0.5 + \
            np.exp(-((xx - 0.68) / 0.012) ** 2) * 0.35
        a = a * 0.9 + np.array([30, 36, 40]) * 0.1
        a = a + streak[..., None] * 190
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return im


def bulb_art(w, h, col):
    """A lit bulb seen through warm glass: amber filament core, coloured glass, darker rim (no white blob)."""
    im = panel(w, h, (0, 0, 0))
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    rim = tuple(int(v * 0.45) for v in col)
    core = tuple(min(255, int(v * 1.0 + 30)) for v in col)
    for k in range(24, 0, -1):
        t = k / 24
        c = tuple(int(rv * t + cv * (1 - t)) for rv, cv in zip(rim, core))
        d.ellipse((W / 2 - W / 2 * t, H / 2 - H / 2 * t, W / 2 + W / 2 * t, H / 2 + H / 2 * t), fill=c)
    d.line([(W * 0.38, H * 0.55), (W * 0.45, H * 0.42), (W * 0.55, H * 0.58), (W * 0.62, H * 0.45)],
           fill=(255, 236, 190), width=max(1, int(W * 0.04)))
    return im


def drop_swatch(col, seed, kind):
    """One drop's skin for the 3D drops inside the glass: 'sour' crinkled and sugared, 'jelly' sugar-crusted matte,
    'hard' glossy boiled sweet. Tiles around a small sphere."""
    n = 64
    r = random.Random(seed)
    im = panel(n, n, col)
    d = ImageDraw.Draw(im)
    shade = tuple(int(c * 0.6) for c in col)
    if kind == 'sour':
        for k in range(10):
            x = r.uniform(0, n) * SS
            d.line([(x, 0), (x + r.uniform(-12, 12) * SS, n * SS)], fill=shade, width=2 * SS)
    if kind in ('sour', 'jelly'):
        for _ in range(500 if kind == 'jelly' else 220):
            x, y = r.uniform(0, n) * SS, r.uniform(0, n) * SS
            v = r.randint(215, 255)
            d.rectangle((x, y, x + SS, y + SS), fill=(v, v, v - 8))
    return im


def dim(img, k):
    return img.point(lambda v: int(v * k))


def spray(size, draw_fn, blur, seed, drips=0, drip_len=(10, 40)):
    """A spray-paint mask: shapes drawn by draw_fn on an L canvas, soft overspray halo, optional drips."""
    m = Image.new('L', size, 0)
    md = ImageDraw.Draw(m)
    draw_fn(md)
    halo = m.filter(ImageFilter.GaussianBlur(blur * 4)).point(lambda v: int(v * 0.35))
    core = m.filter(ImageFilter.GaussianBlur(blur))
    out = ImageChops_lighter(core, halo)
    if drips:
        r = random.Random(seed)
        od = ImageDraw.Draw(out)
        arr = np.asarray(m)
        ys, xs = np.nonzero(arr > 128)
        for _ in range(drips):
            if not len(xs):
                break
            i = r.randrange(len(xs))
            x, y = xs[i], ys[i]
            L = r.uniform(*drip_len) * SS
            wdt = r.uniform(1.5, 3.5) * SS
            od.line([(x, y), (x, y + L)], fill=230, width=int(wdt))
            od.ellipse((x - wdt * 0.8, y + L - wdt * 0.8, x + wdt * 0.8, y + L + wdt), fill=230)
    return out


def ImageChops_lighter(a, b):
    from PIL import ImageChops
    return ImageChops.lighter(a, b)


# ================================================================ BAKER'S DOZENS
def art_bakers(out):
    RED, CREAM, AMBER, CHOC = rgb('#B5222A'), rgb('#EFE4CC'), rgb('#FFB238'), rgb('#4A2716')
    c = Canvas(CREAM)
    # lit marquee: cream script on red, chrome-look border, "THIRTEEN TO THE BAG"
    c.rect('sign', 0, 0, 1024, 314)
    s = panel(1024, 314, RED)
    d = ImageDraw.Draw(s)
    W, H = 1024 * SS, 314 * SS
    round_rect(d, (10 * SS, 10 * SS, W - 10 * SS, H - 10 * SS), 40 * SS, outline=(225, 225, 230), width=10 * SS)
    round_rect(d, (26 * SS, 26 * SS, W - 26 * SS, H - 26 * SS), 30 * SS, outline=CREAM, width=3 * SS)
    f = fit_font(d, "Baker's Dozens", 'georgiaz.ttf', W - 120 * SS, 170 * SS)
    text_center(d, W / 2 + 4 * SS, 128 * SS + 5 * SS, "Baker's Dozens", f, (90, 10, 14))
    text_center(d, W / 2, 128 * SS, "Baker's Dozens", f, CREAM)
    f2 = font('georgiab.ttf', 40 * SS)
    text_center(d, W / 2, 250 * SS, 'THIRTEEN  TO  THE  BAG', f2, AMBER, spacing=6 * SS)
    for x in (110, 914):
        d.ellipse(((x - 14) * SS, 236 * SS, (x + 14) * SS, 264 * SS), fill=AMBER)
    c.paste('sign', s, s)
    # drum contents: sugared jelly drops (domes crusted with sugar), lit from inside the drum
    c.rect('drum', 0, 314, 1024, 260)
    dr = candies(1024, 260, 3, [(200, 30, 40), (240, 150, 30), (230, 90, 30), (90, 160, 50), (170, 40, 90), (240, 200, 60)],
                 size=(26, 34), shape='dome', bg=(60, 30, 20))
    c.paste('drum', dr, dim(dr, 0.45))
    # flip-digit counter face "13" (two black flaps per digit, split line, amber number)
    c.rect('counter', 0, 574, 400, 284)
    s = panel(400, 284, (18, 18, 20))
    d = ImageDraw.Draw(s)
    W, H = 400 * SS, 284 * SS
    fnum = font('arialbd.ttf', 200 * SS)
    for k, ch in enumerate('13'):
        x0 = 22 * SS + k * 184 * SS
        round_rect(d, (x0, 30 * SS, x0 + 172 * SS, 254 * SS), 12 * SS, fill=(36, 34, 34))
        text_center(d, x0 + 86 * SS, 142 * SS, ch, fnum, AMBER)
        d.line([(x0, 142 * SS), (x0 + 172 * SS, 142 * SS)], fill=(8, 8, 8), width=5 * SS)

    text_center(d, W / 2, 15 * SS, 'COUNT  TO  13', font('arialbd.ttf', 22 * SS), (220, 220, 220), spacing=3 * SS)
    text_center(d, W / 2, 270 * SS, 'BELL  ON  13', font('arialbd.ttf', 22 * SS), AMBER, spacing=3 * SS)
    c.paste('counter', s, dim(s, 0.5))
    # paper bag front: kraft, zigzag folded top, printed red "13" and one drop falling out (amber)
    c.rect('bag', 400, 574, 300, 284)
    s = kraft(256, 21).resize((300 * SS, 284 * SS))
    d = ImageDraw.Draw(s)
    W, H = 300 * SS, 284 * SS
    zig = [(0, 0)] + [(k * 25 * SS, (16 if k % 2 else 0) * SS + 6 * SS) for k in range(13)] + [(W, 0)]
    d.polygon(zig + [(W, 0)], fill=(60, 50, 40))
    d.ellipse((80 * SS, 50 * SS, 220 * SS, 190 * SS), outline=RED, width=9 * SS)
    text_center(d, W / 2, 122 * SS, '13', font('georgiab.ttf', 96 * SS), RED)
    text_center(d, W / 2, 238 * SS, "BAKER'S DOZENS", font('georgiab.ttf', 30 * SS), RED)
    d.ellipse((232 * SS, 180 * SS, 258 * SS, 210 * SS), fill=AMBER)
    c.paste('bag', grime_overlay(s, 4, 0.25))
    # lower front panel: cream field, red border, doughnut emblem (own drawing) with 13, product lines
    c.rect('front', 700, 574, 324, 450)
    s = panel(324, 450, CREAM)
    d = ImageDraw.Draw(s)
    W, H = 324 * SS, 450 * SS
    round_rect(d, (8 * SS, 8 * SS, W - 8 * SS, H - 8 * SS), 26 * SS, outline=RED, width=10 * SS)
    cx, cy, R = W / 2, 150 * SS, 105 * SS
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(196, 132, 70))
    d.ellipse((cx - R * 0.92, cy - R * 0.92, cx + R * 0.92, cy + R * 0.88), fill=(232, 120, 150))   # icing
    rr = random.Random(7)
    for _ in range(40):
        a, t = rr.uniform(0, 2 * math.pi), rr.uniform(0.45, 0.85)
        x, y = cx + R * t * math.cos(a), cy + R * t * math.sin(a)
        d.line([(x, y), (x + 8 * SS * math.cos(a + 1), y + 8 * SS * math.sin(a + 1))],
               fill=rr.choice([AMBER, (255, 255, 255), (90, 160, 50), RED]), width=4 * SS)
    d.ellipse((cx - R * 0.34, cy - R * 0.34, cx + R * 0.34, cy + R * 0.34), fill=CREAM)
    text_center(d, cx, cy, '13', font('georgiab.ttf', 56 * SS), RED)
    text_center(d, W / 2, 300 * SS, 'SUGARED', font('georgiab.ttf', 34 * SS), RED, spacing=2 * SS)
    text_center(d, W / 2, 344 * SS, 'JELLY DROPS', font('georgiab.ttf', 34 * SS), RED, spacing=1 * SS)
    text_center(d, W / 2, 400 * SS, '- one for luck -', font('georgiai.ttf', 30 * SS), CHOC)
    c.paste('front', grime_overlay(s, 5, 0.3))
    # tower stripes, awning stripes
    c.rect('tower', 0, 858, 350, 100)
    s = panel(350, 100, CREAM)
    d = ImageDraw.Draw(s)
    for k in range(0, 350, 50):
        d.rectangle((k * SS, 0, (k + 25) * SS, 100 * SS), fill=RED)
    c.paste('tower', grime_overlay(s, 6, 0.3))
    c.rect('awning', 350, 858, 350, 100)
    s = panel(350, 100, CREAM)
    d = ImageDraw.Draw(s)
    for k in range(0, 350, 50):
        d.rectangle((k * SS, 0, (k + 25) * SS, 100 * SS), fill=RED)
    c.paste('awning', grime_overlay(s, 8, 0.25))
    # marquee bulbs, and the coin plate: INSERT COIN / PUSH FOR 13
    c.rect('bulb', 0, 958, 66, 66)
    bl = bulb_art(66, 66, (255, 200, 110))
    c.paste('bulb', bl, bl)
    c.rect('coin', 66, 958, 260, 66)
    s = panel(260, 66, (176, 178, 184))
    d = ImageDraw.Draw(s)
    round_rect(d, (3 * SS, 3 * SS, 257 * SS, 63 * SS), 8 * SS, outline=(70, 70, 74), width=3 * SS)
    text_center(d, 130 * SS, 22 * SS, 'INSERT COIN', font('arialbd.ttf', 22 * SS), (30, 30, 34), spacing=2 * SS)
    text_center(d, 130 * SS, 46 * SS, 'PUSH FOR 13', font('arialbd.ttf', 20 * SS), RED, spacing=2 * SS)
    c.paste('coin', grime_overlay(s, 9, 0.3))
    for k, col in enumerate([(200, 30, 40), (240, 150, 30), (90, 160, 50), (170, 40, 90)]):
        c.rect('drop%d' % k, 330 + 66 * k, 958, 64, 64)
        c.paste('drop%d' % k, drop_swatch(col, 40 + k, 'jelly'))
    c.save(out, 'bakers')


# ================================================================ BON VOYAGES
def art_voyage(out):
    GILT, GILT_D, BOARD, GREEN, MAROON, NAVY = rgb('#E2B65A'), rgb('#8A6420'), rgb('#0E0B08'), rgb('#1F4A33'), rgb('#6B1E24'), rgb('#1C2A4E')
    c = Canvas((30, 20, 14))
    # crest sign: dark lacquer board, gilt serif BON VOYAGES with a dark shadow and a thin gilt rule
    c.rect('sign', 0, 0, 1024, 300)
    s = panel(1024, 300, BOARD)
    d = ImageDraw.Draw(s)
    W, H = 1024 * SS, 300 * SS
    d.rectangle((12 * SS, 12 * SS, W - 12 * SS, H - 12 * SS), outline=GILT, width=6 * SS)
    d.rectangle((26 * SS, 26 * SS, W - 26 * SS, H - 26 * SS), outline=GILT_D, width=2 * SS)
    f = fit_font(d, 'BON VOYAGES', 'palab.ttf', W - 140 * SS, 160 * SS)
    text_center(d, W / 2 + 5 * SS, 130 * SS + 5 * SS, 'BON VOYAGES', f, (0, 0, 0))
    m = Image.new('L', s.size, 0)
    ImageDraw.Draw(m).text((W / 2, 130 * SS), 'BON VOYAGES', font=f, fill=255, anchor='mm', stroke_width=2 * SS,
                           stroke_fill=255)
    yy = np.linspace(0, 1, H)[:, None, None]
    gold = np.clip(np.array([255, 226, 140]) * (1 - yy) + np.array([196, 140, 50]) * yy, 0, 255) * np.ones((1, W, 1))
    s = Image.composite(Image.fromarray(gold.astype(np.uint8)), s, m)
    d = ImageDraw.Draw(s)
    text_center(d, W / 2, 238 * SS, 'TRAVEL  SWEETS  FROM  THE  TIN', font('palab.ttf', 40 * SS), GILT, spacing=4 * SS)
    c.paste('sign', s, dim(s, 0.85))
    # FOR THE JOURNEY: gilt letters straight on the walnut rail
    c.rect('journey', 0, 300, 1024, 160)
    s = walnut(512, 7).resize((1024 * SS, 160 * SS))
    d = ImageDraw.Draw(s)
    W, H = 1024 * SS, 160 * SS
    f = fit_font(d, 'FOR THE JOURNEY', 'palab.ttf', W - 120 * SS, 120 * SS)
    text_center(d, W / 2 + 4 * SS, 80 * SS + 4 * SS, 'FOR THE JOURNEY', f, (10, 5, 2))
    text_center(d, W / 2, 80 * SS, 'FOR THE JOURNEY', f, GILT, stroke=2 * SS, stroke_fill=GILT_D)
    c.paste('journey', s, dim(s, 0.12))
    # destination dial: alternating cream and maroon sectors, six destinations in large type, numbered ring
    c.rect('dial', 0, 460, 512, 512)
    s = panel(512, 512, (30, 20, 14))
    d = ImageDraw.Draw(s)
    W = 512 * SS
    cx = cy = W / 2
    dests = ['PARLOUR', 'HARBOUR', 'PLAZA', 'CAR BARN', 'BELLOWS', 'TERMINUS']
    n = len(dests)
    for k in range(n):
        a0 = -90 - 180 / n + k * 360 / n
        d.pieslice((0, 0, W, W), a0, a0 + 360 / n, fill=((226, 210, 172) if k % 2 == 0 else (120, 34, 38)))
    fd = font('palab.ttf', 25 * SS)
    for k, name in enumerate(dests):
        a = -math.pi / 2 + k * 2 * math.pi / n
        txt = Image.new('RGBA', (320 * SS, 70 * SS), (0, 0, 0, 0))
        td = ImageDraw.Draw(txt)
        td.text((160 * SS, 35 * SS), name, font=fd, fill=((40, 26, 14) if k % 2 == 0 else (240, 225, 190)), anchor='mm')
        rot = txt
        px, py = cx + 0.66 * (W / 2) * math.cos(a), cy + 0.66 * (W / 2) * math.sin(a)
        s.paste(rot, (int(px - rot.width / 2), int(py - rot.height / 2)), rot)
    d.ellipse((cx - 0.40 * W / 2, cy - 0.40 * W / 2, cx + 0.40 * W / 2, cy + 0.40 * W / 2), fill=(226, 210, 172),
              outline=GILT_D, width=5 * SS)
    text_center(d, cx, cy - 26 * SS, 'DIAL', font('palab.ttf', 34 * SS), (60, 40, 20))
    text_center(d, cx, cy + 26 * SS, 'DESTINATION', font('palab.ttf', 24 * SS), (60, 40, 20))
    c.paste('dial', grime_overlay(s, 12, 0.2), dim(s, 0.18))
    # tins: three closed liveries and one open tin showing dusted sweets
    for k, (col, nm) in enumerate(((GREEN, 'PEPPERMINT'), (MAROON, 'ACID DROPS'), (NAVY, 'BARLEY'))):
        c.rect('tin%d' % k, 512 + (k % 2) * 256, 460 + (k // 2) * 256, 256, 256)
        s = panel(256, 256, (30, 20, 14))
        d = ImageDraw.Draw(s)
        W = 256 * SS
        d.ellipse((0, 0, W, W), fill=GILT_D)
        d.ellipse((10 * SS, 10 * SS, W - 10 * SS, W - 10 * SS), fill=col)
        d.ellipse((34 * SS, 34 * SS, W - 34 * SS, W - 34 * SS), outline=GILT, width=5 * SS)
        text_center(d, W / 2, 96 * SS, 'BON', font('palab.ttf', 40 * SS), GILT)
        text_center(d, W / 2, 136 * SS, 'VOYAGES', font('palab.ttf', 34 * SS), GILT)
        text_center(d, W / 2, 176 * SS, nm, font('palab.ttf', 20 * SS), (235, 225, 205))
        rr = random.Random(30 + k)
        for _ in range(900):
            x, y = rr.uniform(20, 236) * SS, rr.uniform(20, 236) * SS
            d.point((x, y), fill=(225, 220, 210))
        c.paste('tin%d' % k, s)
    c.rect('tin3', 768, 716, 256, 256)
    s = panel(256, 256, (30, 20, 14))
    d = ImageDraw.Draw(s)
    W = 256 * SS
    d.ellipse((0, 0, W, W), fill=GILT)
    d.ellipse((12 * SS, 12 * SS, W - 12 * SS, W - 12 * SS), fill=(90, 70, 50))
    rr = random.Random(77)
    for _ in range(70):
        a, t = rr.uniform(0, 2 * math.pi), math.sqrt(rr.uniform(0, 1)) * 100 * SS
        x, y, rad = W / 2 + t * math.cos(a), W / 2 + t * math.sin(a), rr.uniform(12, 18) * SS
        colr = rr.choice([(240, 200, 210), (210, 235, 210), (250, 240, 200), (220, 215, 245)])
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=tuple(int(v * 0.7) for v in colr))
        d.ellipse((x - rad * 0.85, y - rad * 0.9, x + rad * 0.8, y + rad * 0.75), fill=colr)
    for _ in range(4000):
        x, y = rr.uniform(14, 242) * SS, rr.uniform(14, 242) * SS
        if (x - W / 2) ** 2 + (y - W / 2) ** 2 < (114 * SS) ** 2:
            d.point((x, y), fill=(250, 248, 240))
    c.paste('tin3', s)
    # velvet back of the lit display window: deep green with a soft sheen; it glows warm (a lamp inside the case)
    c.rect('velvet', 52, 972, 256, 52)
    v = tnoise(256, 4, 40, aniso=(1.0, 0.1))[:52, :]
    a = np.array(rgb('#2A4A36'), np.float32) * (0.7 + 0.5 * v[..., None])
    vel = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    yy = np.linspace(1, 0.4, 52)[:, None, None]
    gl = Image.fromarray(np.clip(np.ones((52, 256, 3)) * np.array([255, 196, 120]) * 0.45 * yy, 0, 255).astype(np.uint8))
    c.paste('velvet', vel, gl)
    c.rect('bulb', 0, 972, 52, 52)
    bl = bulb_art(52, 52, (255, 190, 90))
    c.paste('bulb', bl, bl)
    # buying plate: brass, PENNY IN THE SLOT / PULL FOR YOUR TIN
    c.rect('buy', 308, 972, 204, 52)
    s = panel(204, 52, (176, 130, 56))
    d = ImageDraw.Draw(s)
    d.rectangle((2 * SS, 2 * SS, 202 * SS, 50 * SS), outline=(90, 60, 20), width=3 * SS)
    text_center(d, 102 * SS, 17 * SS, 'PENNY IN THE SLOT', font('palab.ttf', 18 * SS), (40, 24, 8))
    text_center(d, 102 * SS, 37 * SS, 'PULL FOR YOUR TIN', font('palab.ttf', 18 * SS), (40, 24, 8))
    c.paste('buy', s)
    c.save(out, 'voyage')


# ================================================================ SOUR GRUDGES
def art_grudge(out):
    GREEN, YELLOW, LIME, BLACK, PINK = rgb('#3F8A2A'), rgb('#E8C631'), rgb('#B8E04A'), (16, 16, 14), rgb('#D2307A')
    c = Canvas(GREEN)
    # lit sign: SOUR GRUDGES in heavy yellow letters with a black outline on green, each word tilted
    c.rect('sign', 0, 0, 1024, 300)
    s = panel(1024, 300, rgb('#24561A'))
    d = ImageDraw.Draw(s)
    W, H = 1024 * SS, 300 * SS
    d.rectangle((10 * SS, 10 * SS, W - 10 * SS, H - 10 * SS), outline=YELLOW, width=8 * SS)
    for word, cx, cy, rot, wmax in (('SOUR', 190, 146, 5, 290), ('GRUDGES', 665, 154, -4, 520)):
        f = fit_font(d, word, 'ariblk.ttf', wmax * SS, 130 * SS)
        layer = Image.new('RGBA', (700 * SS, 260 * SS), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text((350 * SS + 6 * SS, 130 * SS + 6 * SS), word, font=f, fill=(0, 0, 0, 255), anchor='mm')
        ld.text((350 * SS, 130 * SS), word, font=f, fill=YELLOW + (255,), anchor='mm', stroke_width=5 * SS,
                stroke_fill=BLACK + (255,))
        layer = layer.rotate(rot, resample=Image.Resampling.BICUBIC)
        s.paste(layer, (int(cx * SS - 350 * SS), int(cy * SS - 130 * SS)), layer)
    text_center(d, W / 2, 268 * SS, 'FOR  PEOPLE  WHO  DO  NOT  FORGIVE', font('ariblk.ttf', 26 * SS), LIME,
                spacing=3 * SS)
    # a sprayed crown tag in the corner of the sign (the Zero Kings got here too)
    m = spray(s.size, lambda md: md.polygon([(x * SS, y * SS) for x, y in
                                             [(880, 92), (880, 40), (905, 64), (925, 30), (945, 64), (970, 40), (970, 92)]],
                                            fill=255), 1.2 * SS, 5)
    s = Image.composite(Image.new('RGB', s.size, PINK), s, m)
    c.paste('sign', s, s)
    # globe contents: puckered sour drops, lit from inside the globe
    c.rect('globe', 0, 300, 1024, 360)
    gl = candies(1024, 360, 17, [(232, 205, 40), (180, 225, 70), (90, 170, 40), (240, 240, 200), (250, 230, 90)],
                 pucker=True, size=(30, 40), bg=(40, 50, 20))
    c.paste('globe', gl, dim(gl, 0.4))
    # face plate: the maker's hand-painted smiling mascot (enamel, crazed and chipped), and over it the Zero Kings'
    # rough aerosol scowl: wobbling strokes built from overspray dots, a heavier core, runs and drips
    c.rect('face', 0, 660, 364, 364)
    s = enamel(rgb('#2F6E22'), 27, n=182, chips=6).resize((364 * SS, 364 * SS))
    d = ImageDraw.Draw(s)
    W = 364 * SS
    d.ellipse((14 * SS, 14 * SS, W - 14 * SS, W - 14 * SS), fill=rgb('#E2BE34'), outline=(110, 80, 20), width=7 * SS)
    for x in (100, 264):
        d.ellipse(((x - 32) * SS, 200 * SS, (x + 32) * SS, 238 * SS), fill=(232, 140, 108))
    d.ellipse((120 * SS, 118 * SS, 150 * SS, 162 * SS), fill=(60, 38, 16))
    d.ellipse((214 * SS, 118 * SS, 244 * SS, 162 * SS), fill=(60, 38, 16))
    d.ellipse((128 * SS, 124 * SS, 138 * SS, 136 * SS), fill=(250, 240, 220))
    d.ellipse((222 * SS, 124 * SS, 232 * SS, 136 * SS), fill=(250, 240, 220))
    d.chord((92 * SS, 150 * SS, 272 * SS, 300 * SS), 15, 165, fill=(150, 40, 30))      # the painted grin
    d.chord((110 * SS, 172 * SS, 254 * SS, 262 * SS), 20, 160, fill=(250, 245, 230))   # its teeth
    s = grime_overlay(s, 28, 0.25)
    rr = random.Random(29)

    def wobble(p0, p1, n=24, amp=6):
        out = []
        for k in range(n + 1):
            t = k / n
            out.append((p0[0] + (p1[0] - p0[0]) * t + rr.uniform(-amp, amp) * SS * 0.3,
                        p0[1] + (p1[1] - p0[1]) * t + math.sin(t * 7 + rr.uniform(0, 1)) * amp * SS * 0.5))
        return out

    strokes = [wobble((70 * SS, 84 * SS), (172 * SS, 142 * SS)), wobble((294 * SS, 84 * SS), (192 * SS, 142 * SS)),
               [(96 * SS + 172 * SS * k / 24, 318 * SS - 70 * SS * math.sin(math.pi * k / 24) + rr.uniform(-3, 3) * SS)
                for k in range(25)],
               wobble((60 * SS, 236 * SS), (304 * SS, 222 * SS), amp=8)]
    paint = Image.new('L', s.size, 0)
    pd = ImageDraw.Draw(paint)
    for k, st in enumerate(strokes):
        w = (18 if k < 3 else 12) * SS
        for (x0, y0), (x1, y1) in zip(st, st[1:]):
            pd.line([(x0, y0), (x1, y1)], fill=235, width=int(w * rr.uniform(0.8, 1.2)))
        for _ in range(900):                                  # overspray: scattered dots round the stroke
            x0, y0 = rr.choice(st)
            a_, rad = rr.uniform(0, 2 * math.pi), abs(rr.gauss(0, w * 1.1))
            pd.point((x0 + rad * math.cos(a_), y0 + rad * math.sin(a_)), fill=rr.randint(120, 255))
        for _ in range(3):                                    # runs
            x0, y0 = rr.choice(st)
            L = rr.uniform(14, 50) * SS
            pd.line([(x0, y0), (x0 + rr.uniform(-2, 2) * SS, y0 + L)], fill=220, width=int(3 * SS))
            pd.ellipse((x0 - 3 * SS, y0 + L - 3 * SS, x0 + 3 * SS, y0 + L + 4 * SS), fill=220)
    paint = paint.filter(ImageFilter.GaussianBlur(0.8 * SS))
    s = Image.composite(Image.new('RGB', s.size, (14, 14, 12)), s, paint)
    c.paste('face', s)
    # crown stencil: sprayed black with stencil bridges, overspray and drips, on weathered green; a pink outline tag
    c.rect('crown', 364, 660, 330, 364)
    s = enamel(GREEN, 19, n=330 * SS // 2, chips=10).resize((330 * SS, 364 * SS))
    pts = [(55, 250), (55, 110), (110, 175), (165, 70), (220, 175), (275, 110), (275, 250)]

    def crown(md):
        md.polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        for x in (110, 165, 220):
            md.rectangle(((x - 5) * SS, 190 * SS, (x + 5) * SS, 252 * SS), fill=0)
        for x, y in ((55, 110), (165, 70), (275, 110)):
            md.ellipse(((x - 12) * SS, (y - 24) * SS, (x + 12) * SS, y * SS), fill=255)
        md.rectangle((55 * SS, 266 * SS, 275 * SS, 292 * SS), fill=255)
        md.text((165 * SS, 330 * SS), 'ZERO KINGS', font=font('ariblk.ttf', 30 * SS), fill=255, anchor='mm')
    m = spray(s.size, crown, 1.6 * SS, 23, drips=8, drip_len=(10, 34))
    s = Image.composite(Image.new('RGB', s.size, BLACK), s, m)
    c.paste('crown', s)
    # coin plate
    c.rect('coin', 694, 660, 330, 200)
    s = panel(330, 200, (150, 152, 156))
    d = ImageDraw.Draw(s)
    W, H = 330 * SS, 200 * SS
    round_rect(d, (6 * SS, 6 * SS, W - 6 * SS, H - 6 * SS), 16 * SS, outline=(70, 70, 74), width=5 * SS)
    text_center(d, W / 2, 46 * SS, 'TURN  FULLY', font('ariblk.ttf', 30 * SS), (40, 40, 44), spacing=2 * SS)
    d.rectangle((W / 2 - 60 * SS, 112 * SS, W / 2 + 60 * SS, 126 * SS), fill=(30, 30, 32))
    text_center(d, W / 2, 166 * SS, 'NO REFUNDS', font('ariblk.ttf', 28 * SS), rgb('#B5222A'), spacing=2 * SS)
    c.paste('coin', grime_overlay(s, 22, 0.35))
    c.rect('bulb', 694, 860, 64, 64)
    bl = bulb_art(64, 64, (200, 255, 120))
    c.paste('bulb', bl, bl)
    # graffiti panel for the plinth and body sides: pink and white tags with a crown over weathered green
    c.rect('tag', 758, 860, 266, 100)
    s = enamel(GREEN, 24, n=266 * SS // 2, chips=8).resize((266 * SS, 164 * SS))

    def tag(md):
        md.text((133 * SS, 92 * SS), 'ZK', font=font('ariblk.ttf', 96 * SS), fill=255, anchor='mm')
    m = spray(s.size, tag, 1.4 * SS, 25, drips=6)
    s = Image.composite(Image.new('RGB', s.size, PINK), s, m)

    def tag2(md):
        md.text((133 * SS, 140 * SS), 'NO FARE NO FAIR', font=font('Inkfree.ttf', 26 * SS), fill=255, anchor='mm')
        md.polygon([(x * SS, y * SS) for x, y in [(200, 40), (200, 14), (212, 26), (222, 8), (232, 26), (244, 14), (244, 40)]],
                   fill=255)
    m = spray(s.size, tag2, 0.8 * SS, 26)
    s = Image.composite(Image.new('RGB', s.size, (235, 235, 225)), s, m)
    c.paste('tag', s.resize((266 * SS, 100 * SS)))
    for k, col in enumerate([(232, 205, 40), (180, 225, 70), (90, 170, 40), (240, 240, 200)]):
        c.rect('drop%d' % k, 758 + 66 * k, 960, 64, 64)
        c.paste('drop%d' % k, drop_swatch(col, 50 + k, 'sour'))
    c.save(out, 'grudge')


# ================================================================ DOUBLE TAKES
def art_double(out):
    TURQ, TURQ_D, CORAL, CHROME, BONE = rgb('#21A69A'), rgb('#0F5F58'), rgb('#C8323A'), (200, 204, 210), rgb('#EEE7D7')
    c = Canvas(TURQ)
    # lit marquee: DOUBLE TAKES twice, the rear copy offset and outlined (the double take), on deep turquoise
    c.rect('sign', 0, 0, 1024, 300)
    s = panel(1024, 300, TURQ_D)
    d = ImageDraw.Draw(s)
    W, H = 1024 * SS, 300 * SS
    round_rect(d, (10 * SS, 10 * SS, W - 10 * SS, H - 10 * SS), 30 * SS, outline=CHROME, width=10 * SS)
    f = fit_font(d, 'DOUBLE TAKES', 'ariblk.ttf', W - 150 * SS, 140 * SS)
    text_center(d, W / 2 + 16 * SS, 122 * SS + 10 * SS, 'DOUBLE TAKES', f, TURQ_D, stroke=4 * SS, stroke_fill=(120, 230, 220))
    text_center(d, W / 2, 122 * SS, 'DOUBLE TAKES', f, BONE, stroke=3 * SS, stroke_fill=(30, 30, 30))
    text_center(d, W / 2, 248 * SS, 'SWEETS  ·  ONE FLASH  ·  TWO OF YOU', font('ariblk.ttf', 32 * SS), rgb('#FFB238'),
                spacing=3 * SS)
    c.paste('sign', s, s)
    # photo strip: four identical frames of the same sweet (a wrapped turquoise drop), white border
    c.rect('strip', 0, 300, 220, 724)
    s = panel(220, 724, (245, 242, 232))
    d = ImageDraw.Draw(s)
    for k in range(4):
        y0 = (20 + k * 172) * SS
        d.rectangle((18 * SS, y0, 202 * SS, y0 + 160 * SS), fill=(40, 40, 46))
        cx, cy = 110 * SS, y0 + 80 * SS
        d.polygon([(cx - 70 * SS, cy - 26 * SS), (cx - 42 * SS, cy), (cx - 70 * SS, cy + 26 * SS)], fill=CORAL)
        d.polygon([(cx + 70 * SS, cy - 26 * SS), (cx + 42 * SS, cy), (cx + 70 * SS, cy + 26 * SS)], fill=CORAL)
        d.ellipse((cx - 46 * SS, cy - 38 * SS, cx + 46 * SS, cy + 38 * SS), fill=TURQ)
        d.ellipse((cx - 30 * SS, cy - 26 * SS, cx - 6 * SS, cy - 8 * SS), fill=(200, 250, 245))
    c.paste('strip', s, dim(s, 0.3))
    # display card beside the strip: the sweet is what you buy
    c.rect('card', 220, 300, 400, 380)
    s = panel(400, 380, TURQ_D)
    d = ImageDraw.Draw(s)
    W, H = 400 * SS, 380 * SS
    round_rect(d, (8 * SS, 8 * SS, W - 8 * SS, H - 8 * SS), 20 * SS, outline=CHROME, width=6 * SS)
    text_center(d, W / 2, 64 * SS, 'SWEETS', font('ariblk.ttf', 68 * SS), BONE, spacing=4 * SS)
    text_center(d, W / 2, 150 * SS, '4 IN A STRIP', font('ariblk.ttf', 44 * SS), rgb('#FFB238'))
    text_center(d, W / 2, 214 * SS, '1 FLASH', font('ariblk.ttf', 44 * SS), rgb('#FFB238'))
    text_center(d, W / 2, 300 * SS, 'SIT · SMILE · WAIT', font('arialbd.ttf', 30 * SS), BONE, spacing=2 * SS)
    c.paste('card', grime_overlay(s, 31, 0.2), dim(s, 0.3))
    # curtain: coral velvet with vertical folds (tiles across the wavy curtain)
    c.rect('curtain', 620, 300, 404, 380)
    xx = np.linspace(0, 1, 404)[None, :]
    fold = 0.55 + 0.45 * np.sin(xx * 2 * math.pi * 6) ** 2
    nz = tnoise(512, 3, 32, aniso=(1.0, 0.05))[:380, :404]
    a = np.array(CORAL, np.float32) * (fold * (0.8 + 0.3 * nz))[..., None]
    yy = np.linspace(0, 1, 380)[:, None]
    a *= (0.75 + 0.25 * (1 - yy))[..., None]
    c.paste('curtain', Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    # slot plate
    c.rect('slot', 220, 680, 400, 160)
    s = panel(400, 160, (170, 174, 180))
    d = ImageDraw.Draw(s)
    W, H = 400 * SS, 160 * SS
    round_rect(d, (6 * SS, 6 * SS, W - 6 * SS, H - 6 * SS), 14 * SS, outline=(80, 80, 86), width=5 * SS)
    text_center(d, W / 2, 50 * SS, 'YOUR STRIP', font('ariblk.ttf', 36 * SS), (30, 30, 34), spacing=2 * SS)
    d.polygon([(W / 2 - 30 * SS, 92 * SS), (W / 2 + 30 * SS, 92 * SS), (W / 2, 130 * SS)], fill=CORAL)
    c.paste('slot', s)
    c.rect('inside', 620, 680, 404, 160)
    c.paste('inside', panel(404, 160, (18, 20, 22)))
    c.rect('bulb', 220, 840, 120, 120)
    bl = bulb_art(120, 120, (225, 245, 255))
    c.paste('bulb', bl, bl)
    # lit header over the candy hopper: SWEETS / 4 IN A STRIP
    c.rect('sweets', 620, 840, 404, 120)
    s = panel(404, 120, rgb('#C8323A'))
    d = ImageDraw.Draw(s)
    W, H = 404 * SS, 120 * SS
    round_rect(d, (5 * SS, 5 * SS, W - 5 * SS, H - 5 * SS), 14 * SS, outline=CHROME, width=5 * SS)
    text_center(d, W / 2, 50 * SS, 'SWEETS', font('ariblk.ttf', 64 * SS), BONE, spacing=6 * SS)
    text_center(d, W / 2, 98 * SS, '4 IN A STRIP  \u00b7  ONE FLASH', font('ariblk.ttf', 20 * SS), rgb('#FFB238'),
                spacing=2 * SS)
    c.paste('sweets', s, s)
    # FLASH plate on the flash unit: a bolt and the word
    c.rect('flashplate', 620, 960, 404, 64)
    s = panel(404, 64, (24, 24, 26))
    d = ImageDraw.Draw(s)
    d.polygon([(30 * SS, 6 * SS), (12 * SS, 36 * SS), (26 * SS, 36 * SS), (16 * SS, 60 * SS), (48 * SS, 26 * SS),
               (33 * SS, 26 * SS), (44 * SS, 6 * SS)], fill=rgb('#FFB238'))
    text_center(d, 222 * SS, 33 * SS, 'FLASH', font('ariblk.ttf', 44 * SS), BONE, spacing=8 * SS)
    c.paste('flashplate', s, dim(s, 0.6))
    # the hopper's packed core (seen between the 3D drops) and the drops' skins
    c.rect('core', 340, 904, 280, 120)
    core = candies(280, 120, 61, [(33, 166, 154), (200, 50, 58), (238, 231, 215), (255, 178, 56)], size=(14, 20), glass=False,
                   bg=(20, 30, 30))
    c.paste('core', core, dim(core, 0.3))
    for k, col in enumerate([(33, 166, 154), (200, 50, 58), (255, 178, 56)]):
        c.rect('drop%d' % k, 340 + 66 * k, 840, 64, 64)
        c.paste('drop%d' % k, drop_swatch(col, 60 + k, 'hard'))
    c.save(out, 'double')


def tiles(out):
    enamel(rgb('#B5222A'), 101).save(os.path.join(out, 'enamel_red.png'))
    enamel(rgb('#EFE4CC'), 102, chip_col=(120, 100, 80)).save(os.path.join(out, 'enamel_cream.png'))
    enamel(rgb('#3F8A2A'), 103).save(os.path.join(out, 'enamel_green.png'))
    enamel(rgb('#E8C631'), 104, chip_col=(90, 80, 60)).save(os.path.join(out, 'enamel_yellow.png'))
    enamel(rgb('#21A69A'), 105).save(os.path.join(out, 'enamel_turq.png'))
    enamel(rgb('#1C1A1A'), 106, chip_col=(60, 58, 56), grime=0.1).save(os.path.join(out, 'enamel_black.png'))
    walnut().save(os.path.join(out, 'walnut.png'))
    kraft().save(os.path.join(out, 'kraft.png'))
    metal_base().save(os.path.join(out, 'metal_c.png'))
    spec((196, 198, 204)).save(os.path.join(out, 'spec_chrome.png'))
    spec((214, 168, 82)).save(os.path.join(out, 'spec_brass.png'))
    spec((236, 196, 110)).save(os.path.join(out, 'spec_gilt.png'))
    Image.fromarray((np.dstack([tnoise(64, 4, 7)] * 3) * 20 + 14).astype(np.uint8)).save(os.path.join(out, 'rubber.png'))
    Image.new('RGB', (16, 16), (200, 206, 210)).save(os.path.join(out, 'glass_c.png'))   # stand-in, swapped for stock glass


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    tiles(out)
    art_bakers(out)
    art_voyage(out)
    art_grudge(out)
    art_double(out)
    print('art written to', out)


if __name__ == '__main__':
    main()
