"""The new perks' HUD icons in the stock perk-tile system (128x128 RGBA TGA + PNG, a review sheet).

Usage: python -I -B perk_icons.py <out dir> [--stock-dir <dir with stock_revive.png, stock_deadeye.png>]
Output names are the ones add_perks.py wires (iwz_perk_icon_bakers/voyage/grudge/double/double_cd).

Tile: stock_tile_alpha.png (kept OUT of the repository: extracted game content stays on the PC; path from IWZ_PERK_TILE, default C:\studio-data\sz\perk_stock\stock_tile_alpha.png) is the alpha channel of the stock cp_zmb_perk_icon_revive image (the skewed
parallelogram: a 3 px rim at alpha ~117, the body at ~168, the same alpha the stock tiles use). The rim is
white like the stock rim, the body is one flat colour per perk with a light top-to-bottom shade, the glyph is
white with a thin dark outline of the body colour. Glyphs are simple filled shapes drawn at 4x and
downsampled; they are sized to read at 25 px.
Pillow only for drawing (add_perks.py runs this with python -I when the images are missing); numpy only for --stock-dir measurements.
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 4
N = 128 * S
HERE = os.path.dirname(os.path.abspath(__file__))
TILE = os.environ.get("IWZ_PERK_TILE") or r"C:\studio-data\sz\perk_stock\stock_tile_alpha.png"   # extracted game content: never in the repository

# body colours; the stock tiles in the HUD row are revive (cyan, hue 195) and deadeye (green, hue 120)
BODY = {
    "bakers": (232, 128, 24),    # orange   hue ~ 31
    "voyage": (126, 82, 208),    # violet   hue ~ 261
    "grudge": (196, 36, 52),     # crimson  hue ~ 353
    "double": (222, 70, 160),    # magenta  hue ~ 326
}


def sc(p):
    return (p[0] * S, p[1] * S)


def mask():
    m = Image.new("L", (N, N), 0)
    return m, ImageDraw.Draw(m)


def stroke(d, pts, w, closed=False):
    pts = [sc(p) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    r = w * S / 2.0
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=int(round(w * S)))
    for p in pts:
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)


def arc(cx, cy, r, a0, a1, n=48):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def disc(d, c, r, fill=255):
    x, y = sc(c)
    d.ellipse([x - r * S, y - r * S, x + r * S, y + r * S], fill=fill)


def poly(d, pts, fill=255):
    d.polygon([sc(p) for p in pts], fill=fill)


def star4(d, c, r, k=0.28, fill=255):
    pts = []
    for i in range(8):
        a = math.radians(-90 + 45 * i)
        rr = r if i % 2 == 0 else r * k
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    poly(d, pts, fill)


# glyphs: (white mask, knockout mask). Centre of the tile body is about (62, 65); room is about 58 x 52.
def glyph_bakers():
    w, wd = mask()
    k, kd = mask()
    stroke(wd, [(37, 56), (47, 49), (47, 82)], 10)          # 1 with a flag
    stroke(wd, arc(71, 57, 9.5, 200, 450), 9.5)              # 3, upper bowl
    stroke(wd, arc(71, 74, 11, 270, 520), 9.5)               # 3, lower bowl
    return w, k


def glyph_voyage():
    w, wd = mask()
    k, kd = mask()
    stroke(wd, arc(62, 65, 26, 0, 360, 96), 8)               # dial ring
    stroke(wd, [(62, 65), (62, 44)], 8)                       # long hand
    stroke(wd, [(62, 65), (79, 74)], 8)                       # short hand
    disc(wd, (62, 65), 6)
    return w, k


def glyph_grudge():
    w, wd = mask()
    k, kd = mask()
    disc(wd, (62, 65), 28)                                    # face, with X eyes and a flat mouth knocked out
    for ex in (51, 73):
        stroke(kd, [(ex - 6, 53), (ex + 6, 65)], 5.5)
        stroke(kd, [(ex - 6, 65), (ex + 6, 53)], 5.5)
    stroke(kd, [(50, 79), (74, 79)], 5.5)
    return w, k


def glyph_double():
    w, wd = mask()
    k, kd = mask()
    disc(wd, (50, 52), 10.5)                                  # person: head and shoulders
    poly(wd, [(30, 90), (32, 74), (40, 67), (60, 67), (68, 74), (70, 90)])
    star4(wd, (85, 48), 15, 0.3)                              # two sparkles
    star4(wd, (86, 80), 9, 0.3)
    return w, k


GLYPHS = {"bakers": glyph_bakers, "voyage": glyph_voyage, "grudge": glyph_grudge, "double": glyph_double}


def down(m):
    return m.resize((128, 128), Image.LANCZOS)


def compose(key, body_rgb, tile_alpha, grey=False):
    w, k = GLYPHS[key]()
    glyph = ImageChops.subtract(down(w), down(k))
    ol = down(w.filter(ImageFilter.MaxFilter(2 * S + 1)))
    rim = tile_alpha.point(lambda v: 255 if 30 < v < 140 else 0).filter(ImageFilter.GaussianBlur(0.4))
    body = ImageChops.multiply(tile_alpha.point(lambda v: max(0, min(255, int((v - 30) / 120.0 * 255)))), ImageChops.invert(rim))
    t = Image.linear_gradient("L").resize((128, 128))                   # 0 at the top, 255 at the bottom
    col = Image.merge("RGB", [t.point(lambda v, c=c: max(0, min(255, int(c * (1.12 - 0.28 * v / 255.0)))))
                              for c in body_rgb])
    white = Image.new("RGB", (128, 128), (255, 255, 255))
    img = Image.composite(col, Image.new("RGB", (128, 128), (0, 0, 0)), body)
    img = Image.composite(white, img, rim)                                # white rim like the stock one
    om = ImageChops.multiply(ol, body).point(lambda v: int(v * 0.9))
    img = Image.composite(col.point(lambda v: int(v * 0.45)), img, om)   # thin dark outline on the body only
    img = Image.composite(white, img, glyph)
    alpha = tile_alpha
    if grey:
        img = img.convert("L").point(lambda v: int(v * 0.55 + 40)).convert("RGB")
        alpha = alpha.point(lambda v: int(v * 0.6))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def metrics(path, stock):
    """alpha coverage, tile IoU and a 4x4x4 colour histogram distance of an icon to the stock tile"""
    import numpy as np                      # measuring only (not needed by the build)
    im = np.asarray(Image.open(path).convert("RGBA"))
    st = np.asarray(Image.open(stock).convert("RGBA"))

    def hist(x):
        m = x[..., 3] > 127
        h, _ = np.histogramdd(x[m][:, :3].astype(float), bins=(4, 4, 4), range=((0, 256),) * 3)
        return h / max(h.sum(), 1)
    sa, ia = st[..., 3] > 127, im[..., 3] > 127
    return (float(ia.mean()), float((sa & ia).sum() / max((sa | ia).sum(), 1)),
            float(0.5 * np.abs(hist(im) - hist(st)).sum()))


def main():
    args = sys.argv[1:]
    stock_dir = ""
    if "--stock-dir" in args:
        i = args.index("--stock-dir")
        stock_dir = args[i + 1]
        del args[i:i + 2]
    out = args[0] if args else os.path.join(HERE, "icons")
    os.makedirs(out, exist_ok=True)
    if not os.path.isfile(TILE):
        raise SystemExit("perk_icons: the stock tile mask is not on this PC: %s (save the alpha channel of the stock cp_zmb_perk_icon_revive image there, 128x128 L, or set IWZ_PERK_TILE)" % TILE)
    tile = Image.open(TILE).convert("L")
    assert tile.size == (128, 128)
    icons = {"iwz_perk_icon_" + k: compose(k, rgb, tile) for k, rgb in BODY.items()}
    icons["iwz_perk_icon_double_cd"] = compose("double", BODY["double"], tile, grey=True)
    for name, im in icons.items():
        im.save(os.path.join(out, name + ".tga"), format="TGA")
        im.save(os.path.join(out, name + ".png"), format="PNG")
        t = Image.open(os.path.join(out, name + ".tga"))
        t.load()
        print(name, t.size, t.mode, "tga bytes", os.path.getsize(os.path.join(out, name + ".tga")))
    pics = []
    if stock_dir:
        pics += [Image.open(os.path.join(stock_dir, s + ".png")).convert("RGBA") for s in ("stock_revive", "stock_deadeye")]
    pics += list(icons.values())
    pad = 16
    sheet = Image.new("RGBA", (pad + len(pics) * (192 + pad), pad * 3 + 192 + 64), (34, 38, 44, 255))
    for i, p in enumerate(pics):
        x = pad + i * (192 + pad)
        sheet.alpha_composite(p.resize((192, 192), Image.LANCZOS), (x, pad))
        sheet.alpha_composite(p.resize((25, 25), Image.LANCZOS), (x + 40, pad * 2 + 192))
        sheet.alpha_composite(p.resize((50, 50), Image.LANCZOS), (x + 100, pad * 2 + 192))
    sheet.save(os.path.join(out, "icons_sheet.png"))
    if stock_dir:
        ref = os.path.join(stock_dir, "stock_revive.png")
        for name in icons:
            print("%s: alpha>127 coverage %.3f, tile IoU vs stock revive %.3f, colour histogram distance %.3f"
                  % ((name,) + metrics(os.path.join(out, name + ".png"), ref)))
        print("stock deadeye vs stock revive: coverage %.3f IoU %.3f histogram distance %.3f"
              % metrics(os.path.join(stock_dir, "stock_deadeye.png"), ref))


if __name__ == "__main__":
    main()
