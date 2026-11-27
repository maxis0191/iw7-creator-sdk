"""Logos (finished from generator output, Copy Stop drawn here), poster clock paste, projected screen, polish decal.

usage: python build_marks.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from artlib import RAW, ARCADE, TERMINUS, snap_alpha, bbox_crop, contain, cover

BLUE = (0, 133, 202, 255)
WHITE = (255, 255, 255, 255)


def logo_from_raw(raw, out):
    im = snap_alpha(Image.open(RAW / raw))
    im = contain(bbox_crop(im), (1024, 1024), margin=72)
    im.save(ARCADE / out)


def page_poly(x0, y0, w, h, f):
    return [(x0, y0), (x0 + w - f, y0), (x0 + w, y0 + f), (x0 + w, y0 + h), (x0, y0 + h)]


def copy_stop_mark():
    """A page printed twice out of register: impression A solid blue, impression B its ghost shifted up-right.
    Where B's strokes cross A they knock out to white (two colours only: process blue and white)."""
    S = 4
    N = 1024 * S
    w, h, f, st = 500 * S, 660 * S, 150 * S, 30 * S
    dx, dy = 110 * S, -60 * S
    x0 = (N - (w + dx)) // 2
    y0 = (N - (h - dy)) // 2 - dy
    bx, by = x0 + dx, y0 + dy

    def mask(draw_fn):
        m = Image.new("L", (N, N), 0); draw_fn(ImageDraw.Draw(m)); return np.array(m) > 127

    A = mask(lambda d: d.polygon(page_poly(x0, y0, w, h, f), fill=255))
    foldA = mask(lambda d: d.polygon([(x0 + w - f, y0), (x0 + w - f, y0 + f), (x0 + w, y0 + f)], fill=255))
    lines = [0.40, 0.58, 0.76]

    def line_rects(px, py, d, col=255):
        for k, t in enumerate(lines):
            ly = py + int(h * t)
            xe = px + w - 80 * S - (120 * S if k == 2 else 0)
            d.rectangle([px + 80 * S, ly, xe, ly + 40 * S], fill=col)

    linesA = mask(lambda d: line_rects(x0, y0, d))
    Bpoly = mask(lambda d: d.polygon(page_poly(bx, by, w, h, f), fill=255))

    def b_strokes(d):
        d.line(page_poly(bx, by, w, h, f) + [(bx, by)], fill=255, width=st, joint="curve")
        d.line([(bx + w - f, by), (bx + w - f, by + f), (bx + w, by + f)], fill=255, width=st, joint="curve")

    inkB = mask(b_strokes)
    inkA = A & ~linesA & ~foldA
    blue = inkA ^ inkB
    white = (A | Bpoly) & ~blue
    out = np.zeros((N, N, 4), np.uint8)
    out[blue] = BLUE
    out[white] = WHITE
    im = Image.fromarray(out, "RGBA").resize((1024, 1024), Image.LANCZOS)
    im.save(ARCADE / "logo_copy_stop.png")


def poster():
    """Paste only the edited clock back onto the concept one-sheet (feathered), then deliver 683x1024."""
    a = Image.open("C:/studio-data/sz/film/concept/poster.png").convert("RGB")
    b = Image.open(RAW / "poster_station_zero.png").convert("RGB").resize(a.size, Image.LANCZOS)
    m = Image.new("L", a.size, 0)
    ImageDraw.Draw(m).rectangle([805, 345, 975, 520], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(6))
    full = Image.composite(b, a, m)
    full.save(RAW / "poster_station_zero_composited_1024x1536.png")
    d = np.abs(np.array(full, int) - np.array(a, int)).max(2)
    ys, xs = np.where(d > 0)
    print("poster: changed pixels bbox", xs.min(), ys.min(), xs.max(), ys.max())
    full.resize((683, 1024), Image.LANCZOS).save(ARCADE / "poster_station_zero.png")


def screen():
    """Projected film frame on the paper wall: 1024x576, paper bars from our own tile multiplied through it."""
    im = cover(Image.open(RAW / "screen_second_platform.png").convert("RGB"), (1024, 576))
    paper = Image.open(TERMINUS / "paper_greenbar_tile.png").convert("RGB").crop((0, 0, 1024, 576))
    lum = np.array(paper.convert("L"), float)
    p = (1 + 1.2 * (lum / lum.mean() - 1))[..., None]  # the paper's bars and fibre: about +-6 % of the light
    out = np.clip(np.array(im, float) * p, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(TERMINUS / "screen_second_platform.png")


def polish():
    """Decal: warm white brightening; alpha = swirl luminance plus a soft clean disc, soft outer edge."""
    g = np.array(cover(Image.open(RAW / "floor_polish_swirl.png").convert("L"), (1024, 1024)), float) / 255
    yy, xx = np.mgrid[0:1024, 0:1024]
    r = np.hypot(xx - 511.5, yy - 511.5) / 512
    disc = np.clip((0.86 - r) / 0.16, 0, 1) ** 1.5  # soft edge from r .70 to .86
    a = np.clip(0.10 * disc + 0.62 * g, 0, 1) * np.clip((0.98 - r) / 0.1, 0, 1)
    rgb = np.empty((1024, 1024, 3)); rgb[...] = (255, 246, 228)
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(ARCADE / "floor_polish_circle.png")


if __name__ == "__main__":
    logo_from_raw("logo_needle_drop.png", "logo_needle_drop.png")
    logo_from_raw("logo_hole_nine.png", "logo_hole_nine.png")
    logo_from_raw("logo_heel_key.png", "logo_heel_key.png")
    copy_stop_mark()
    poster()
    screen()
    polish()
    print("ok")
