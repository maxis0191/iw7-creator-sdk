"""Shared helpers: fitting raw generator output to the delivered pixel size, alpha snapping, fonts."""
import pathlib
import numpy as np
from PIL import Image, ImageFont

RAW = pathlib.Path("C:/studio-data/sz/film/art/_raw")
ARCADE = pathlib.Path("C:/studio-data/sz/film/art/arcade")
TERMINUS = pathlib.Path("C:/studio-data/sz/film/art/terminus")
FONTS = pathlib.Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def snap_alpha(im, hi=245, lo=6):
    """The generator returns opaque pixels at alpha 250..254; make them 255, and dust under lo 0."""
    im = im.convert("RGBA")
    a = np.array(im)
    al = a[..., 3]
    al[al >= hi] = 255
    al[al <= lo] = 0
    return Image.fromarray(a, "RGBA")


def bbox_crop(im, pad=0):
    a = np.array(im.convert("RGBA"))[..., 3]
    ys, xs = np.where(a > 8)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def cover(im, size, anchor=(0.5, 0.5)):
    """Scale uniformly to cover size, then crop (no stretching)."""
    W, H = size
    s = max(W / im.width, H / im.height)
    r = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), Image.LANCZOS)
    x = round((r.width - W) * anchor[0]); y = round((r.height - H) * anchor[1])
    return r.crop((x, y, x + W, y + H))


def contain(im, size, margin=0, bg=(0, 0, 0, 0)):
    """Scale uniformly to fit inside size minus margin, centred on a transparent (or bg) canvas."""
    W, H = size
    s = min((W - 2 * margin) / im.width, (H - 2 * margin) / im.height)
    r = im.convert("RGBA").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    c = Image.new("RGBA", size, bg)
    c.alpha_composite(r, ((W - r.width) // 2, (H - r.height) // 2))
    return c


def alpha_share(im):
    a = np.array(im.convert("RGBA"))[..., 3]
    return round(float((a == 0).mean()), 3)
