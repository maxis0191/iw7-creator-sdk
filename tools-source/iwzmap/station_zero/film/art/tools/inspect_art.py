"""Measure and preview pictures: mode, size, alpha share, dominant colours; a sheet on mid-grey.

usage: python inspect_art.py <out_sheet.jpg> <png> [<png> ...] [--small 64]
Each picture is shown at up to 360 px and at --small px (its in-game reading size), on grey #808080.
"""
import sys, pathlib
import numpy as np
from PIL import Image, ImageDraw


def stats(p):
    im = Image.open(p)
    rgba = np.array(im.convert("RGBA"))
    a = rgba[..., 3]
    opaque = rgba[a > 128][:, :3]
    q = Image.fromarray(opaque.reshape(-1, 1, 3).astype("uint8")).quantize(4) if len(opaque) else None
    cols = []
    if q is not None:
        pal = q.getpalette()[:12]
        counts = sorted(q.getcolors(), reverse=True)
        tot = sum(c for c, _ in counts)
        cols = ["#%02x%02x%02x %d%%" % (*pal[i * 3:i * 3 + 3], round(100 * c / tot)) for c, i in counts]
    return f"{pathlib.Path(p).name} {im.mode} {im.size} transparent={(a == 0).mean():.3f} partial={((a > 0) & (a < 255)).mean():.3f} colours={cols}"


def main():
    args = sys.argv[1:]
    small = 64
    if "--small" in args:
        i = args.index("--small"); small = int(args[i + 1]); del args[i:i + 2]
    out, files = args[0], args[1:]
    tiles = []
    for f in files:
        print(stats(f))
        im = Image.open(f).convert("RGBA")
        big = im.copy(); big.thumbnail((360, 360))
        sm = im.copy(); sm.thumbnail((small, small), Image.LANCZOS)
        tiles.append((big, sm, pathlib.Path(f).stem))
    W = sum(max(b.width, s.width) + 20 for b, s, _ in tiles) + 20
    H = 360 + small + 70
    sheet = Image.new("RGB", (W, H), (128, 128, 128))
    d = ImageDraw.Draw(sheet)
    x = 20
    for b, s, n in tiles:
        sheet.paste(b, (x, 20), b)
        sheet.paste(s, (x, 400), s)
        d.text((x, 4), n, fill=(255, 255, 255))
        x += max(b.width, s.width) + 20
    sheet.save(out, quality=92)


if __name__ == "__main__":
    main()
