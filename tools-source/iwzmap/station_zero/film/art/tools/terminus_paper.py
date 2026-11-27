"""The Terminus paper set, procedural (exact tiling, exact spelling, one dot-matrix hand).

Writes to C:/studio-data/sz/film/art/terminus/:
  paper_greenbar_tile.png 1024x1024 (16 bars of 64 px: 8 green, 8 white; periodic fibre noise; faint digits)
  paper_greenbar_edge.png 1024x128 RGBA (tractor margin: holes transparent, pitch 64 = bar height; perforation)
  paper_times_column.png 256x1024 ("23:47" two lines a bar, sprocket margins drawn as shaded holes)
  leader_8..leader_2.png 192x192 RGBA, sign_terminus.png 1024x200, sign_fare_validation.png 512x128
  *_tiletest.jpg (3x3 tiling of the tile, 3x1 of the edge) for the seam check.
usage: python terminus_paper.py
"""
import pathlib, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import dotmatrix as dm

OUT = pathlib.Path("C:/studio-data/sz/film/art/terminus")
WHITE = np.array([241, 241, 233], float)
GREEN = np.array([207, 226, 199], float)
INK = (26, 27, 30)
SS = 2  # supersampling for dots


def periodic_noise(h, w, sx, sy, seed):
    """Gaussian-filtered white noise via FFT: periodic in both axes, so it tiles by construction."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h, w))
    ky = np.fft.fftfreq(h)[:, None]
    kx = np.fft.fftfreq(w)[None, :]
    f = np.exp(-((kx * sx) ** 2 + (ky * sy) ** 2))
    r = np.real(np.fft.ifft2(np.fft.fft2(n) * f))
    return r / (r.std() + 1e-9)


def paper_rgb(h, w, bars="h", bar=64, seed=1, phase=0):
    """Green-bar paper as float RGB; bars='h' horizontal bars, 'v' vertical bars (the paper turned 90 degrees)."""
    if bars == "h":
        idx = ((np.arange(h) + phase) // bar) % 2
        band = idx[:, None].repeat(w, 1)
    else:
        idx = ((np.arange(w) + phase) // bar) % 2
        band = idx[None, :].repeat(h, 0)
    base = np.where(band[..., None] == 0, GREEN, WHITE)
    # soft 1.5 px transition at band edges (printed ink, not a cut)
    img = Image.fromarray(base.astype("uint8")).filter(ImageFilter.GaussianBlur(0.8))
    base = np.array(img, float)
    if bars == "h":  # fibres run along the bars (long correlation in x: narrow pass band in kx)
        fib = 0.55 * periodic_noise(h, w, 40.0, 2.0, seed) + 0.35 * periodic_noise(h, w, 60.0, 40.0, seed + 1)
    else:
        fib = 0.55 * periodic_noise(h, w, 2.0, 40.0, seed) + 0.35 * periodic_noise(h, w, 40.0, 60.0, seed + 1)
    blot = periodic_noise(h, w, 400.0, 400.0, seed + 2)  # large soft unevenness of the sheet
    grain = periodic_noise(h, w, 900.0, 900.0, seed + 3)
    lum = fib * 2.2 + blot * 2.0 + grain * 1.6
    return np.clip(base + lum[..., None], 0, 255)


def faint_digits(size_w, size_h, bar, seed):
    """Very pale dot-matrix rows of numbers, three lines per bar, wrapped modulo the tile (seamless)."""
    rng = random.Random(seed)
    W, H = size_w * SS, size_h * SS
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pitch = 2.5 * SS
    line = bar * SS / 3
    for li in range(int(H / line)):
        y = li * line + (line - 7 * pitch) / 2
        x = rng.uniform(0, W)
        cols = []
        while sum(len(c) + 3 for c in cols) * 6 * pitch < W - 40 * pitch:
            kind = rng.random()
            if kind < 0.3:
                cols.append("%06d" % rng.randrange(10 ** 6))
            elif kind < 0.55:
                cols.append("%02d:%02d" % (rng.choice([23, 23, 22, 0]), rng.randrange(60)))
            elif kind < 0.8:
                cols.append("%04d" % rng.randrange(10 ** 4))
            else:
                cols.append("%d.%02d" % (rng.randrange(100), rng.randrange(100)))
        text = "   ".join(cols)
        if rng.random() < 0.12:
            continue  # a blank line now and then
        dm.draw_text(layer, text, x, y, pitch, 0.55 * SS, (40, 44, 40, 50), wrap=(W, H), jitter=0.2 * SS,
                     dropout=0.04, rng=rng)
    return layer.resize((size_w, size_h), Image.LANCZOS)


def tile():
    rgb = paper_rgb(1024, 1024, "h", 64, seed=11)
    im = Image.fromarray(rgb.astype("uint8")).convert("RGBA")
    im.alpha_composite(faint_digits(1024, 1024, 64, 5))
    im = im.convert("RGB")
    im.save(OUT / "paper_greenbar_tile.png")
    t = Image.new("RGB", (3072, 3072))
    for i in range(3):
        for j in range(3):
            t.paste(im, (i * 1024, j * 1024))
    t.resize((1536, 1536), Image.LANCZOS).save(OUT / "paper_greenbar_tile_tiletest.jpg", quality=90)
    t.crop((768, 768, 1280, 1280)).save(OUT / "paper_greenbar_tile_tiletest_seamzoom.jpg", quality=92)
    return im


def edge():
    W, H = 1024, 128
    rgb = paper_rgb(H, W, "v", 64, seed=21)
    a = np.full((H, W), 255.0)
    S = 4
    m = Image.new("L", (W * S, H * S), 0)  # hole mask, supersampled
    d = ImageDraw.Draw(m)
    hy, hr = 40, 13.5
    for k in range(W // 64):
        cx = 32 + 64 * k
        d.ellipse([(cx - hr) * S, (hy - hr) * S, (cx + hr) * S, (hy + hr) * S], fill=255)
    hole = np.array(m.resize((W, H), Image.LANCZOS), float) / 255
    rim = np.array(m.filter(ImageFilter.MaxFilter(9)).resize((W, H), Image.LANCZOS), float) / 255 - hole
    a = a * (1 - hole)
    rgb = rgb * (1 - 0.18 * np.clip(rim, 0, 1)[..., None])  # torn fibre rim slightly darker
    # perforation line at y=80: short slits (half see-through), a fold shadow either side
    py = 80
    for x in range(0, W, 8):
        a[py - 1:py + 1, x:x + 5] *= 0.25
        rgb[py - 1:py + 1, x:x + 5] *= 0.75
    rgb[py - 3:py - 1] *= 0.97
    rgb[py + 1:py + 3] *= 0.985
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 255)]).astype("uint8")
    im = Image.fromarray(out, "RGBA")
    im.save(OUT / "paper_greenbar_edge.png")
    t = Image.new("RGBA", (W * 3, H * 3), (60, 60, 60, 255))
    for i in range(3):
        for j in range(3):
            t.alpha_composite(im, (i * W, j * H))
    t.convert("RGB").save(OUT / "paper_greenbar_edge_tiletest.jpg", quality=90)
    return im


def times_column(tile_im):
    W, H = 256, 1024
    col = tile_im.crop((300, 0, 300 + W, H)).convert("RGBA")
    d = ImageDraw.Draw(col)
    # sprocket margins: shaded holes (the column is solid behind), perforation line
    for x0 in (14, W - 14):
        for k in range(H // 32):
            cy = 16 + 32 * k
            d.ellipse([x0 - 6, cy - 6, x0 + 6, cy + 6], fill=(150, 152, 145, 255))
            d.ellipse([x0 - 6, cy - 6, x0 + 6, cy - 1], fill=(122, 124, 118, 255))
        px = 32 if x0 < W / 2 else W - 32
        for y in range(0, H, 7):
            d.line([(px, y), (px, y + 3)], fill=(170, 172, 165, 255), width=1)
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    rng = random.Random(47)
    pitch = 3.3 * SS
    tw = dm.text_width("23:47", pitch)
    for b in range(16):
        for k in (0, 1):
            y = (b * 64 + 5 + k * 32) * SS
            dm.draw_text(big, "23:47", (W * SS - tw) / 2, y, pitch, 1.3 * SS, INK + (238,), jitter=0.2 * SS,
                         dropout=0.025, rng=rng)
    col.alpha_composite(big.resize((W, H), Image.LANCZOS))
    col.convert("RGB").save(OUT / "paper_times_column.png")


def leaders():
    N = 192
    for n in range(8, 1, -1):
        big = Image.new("RGBA", (N * SS, N * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        rng = random.Random(n)
        c, R = N * SS / 2, 84 * SS
        steps = 96
        for i in range(steps):
            t = 2 * np.pi * i / steps
            rr = 2.1 * SS * rng.uniform(0.9, 1.05)
            x, y = c + R * np.cos(t), c + R * np.sin(t)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=INK + (240,))
        cell = 14 * SS
        dm.draw_big_glyph(big, str(n), c - 2.5 * cell, c - 3.5 * cell, cell, 2.6 * SS, INK + (240,), rng=rng,
                          dropout=0.02)
        big.resize((N, N), Image.LANCZOS).save(OUT / f"leader_{n}.png")


def paper_sign(W, H, text, pitch, name, seed):
    bar = H - 24  # white paper behind the text, one green band along the bottom edge
    rgb = paper_rgb(H, W, "h", bar, seed=seed, phase=bar)
    im = Image.fromarray(rgb.astype("uint8")).convert("RGBA")
    d = ImageDraw.Draw(im)
    hr = max(4, H // 22)
    for x0 in (hr * 2 + 2, W - hr * 2 - 2):  # tractor holes at both ends, shaded (the sign has a backing)
        for k in range(int(H // (hr * 4))):
            cy = hr * 2 + k * hr * 4 + (H - int(H // (hr * 4)) * hr * 4) / 2
            d.ellipse([x0 - hr, cy - hr, x0 + hr, cy + hr], fill=(150, 152, 145, 255))
            d.ellipse([x0 - hr, cy - hr, x0 + hr, cy - hr * 0.2], fill=(118, 120, 114, 255))
        px = x0 + (hr * 2 + 3 if x0 < W / 2 else -hr * 2 - 3)
        for y in range(0, H, 7):
            d.line([(px, y), (px, y + 3)], fill=(168, 170, 163, 255), width=1)
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    p = pitch * SS
    tw = dm.text_width(text, p)
    dm.draw_text(big, text, (W * SS - tw) / 2, (H * SS - 6 * p) / 2 - p * 0.3, p, 0.36 * p, INK + (240,),
                 jitter=0.04 * p, dropout=0.015, rng=random.Random(seed))
    im.alpha_composite(big.resize((W, H), Image.LANCZOS))
    im.convert("RGB").save(OUT / name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t = tile()
    edge()
    times_column(t)
    leaders()
    paper_sign(1024, 200, "047 · TERMINUS", 10, "sign_terminus.png", 47)
    paper_sign(512, 128, "FARE VALIDATION", 4.6, "sign_fare_validation.png", 48)
    print("ok")
