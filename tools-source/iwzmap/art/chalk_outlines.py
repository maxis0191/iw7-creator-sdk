"""Wall-buy chalk outlines (review g27 item 20: wall buys showed only the small cyan weapon outline), procedural (PIL).

usage: python -I chalk_outlines.py <art dir>   -> <art dir>/chalk/chalk_<class>.png and chalk_<class>_c.tga (RGBA, alpha =
chalk). Classes: pistol, smg, rifle, shotgun. Each is a hand-drawn weapon silhouette in rough chalk strokes with a chalk
frame and a blank price line (prices come from the live interaction table, not drawn here). The level places the decal
on the wall behind each wall-buy struct, only when its TGA exists.
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 512, 256
SHAPES = {   # silhouettes in a 100 x 50 box: lists of polylines (closed unless the first point repeats)
    'pistol': [[(18, 18), (70, 18), (74, 22), (74, 27), (40, 27), (38, 32), (34, 44), (24, 44), (27, 30), (18, 27)],
               [(36, 27), (38, 34), (44, 34), (44, 27)]],
    'smg': [[(8, 20), (62, 20), (66, 16), (84, 16), (84, 24), (92, 24), (92, 28), (66, 28), (62, 36), (56, 36), (52, 28),
             (40, 28), (36, 44), (28, 44), (30, 28), (16, 28), (8, 34)], [(44, 28), (46, 40), (52, 40), (50, 28)]],
    'rifle': [[(4, 22), (24, 18), (30, 18), (34, 15), (70, 15), (74, 18), (96, 18), (96, 22), (74, 22), (70, 26), (52, 26),
               (50, 38), (44, 38), (44, 26), (34, 26), (30, 32), (24, 32), (4, 30)], [(56, 26), (60, 40), (66, 40), (62, 26)],
              [(38, 15), (40, 10), (60, 10), (62, 15)]],
    'shotgun': [[(4, 24), (22, 20), (30, 20), (34, 18), (96, 18), (96, 23), (60, 23), (60, 27), (34, 27), (30, 31),
                 (24, 31), (4, 32)], [(62, 23), (62, 28), (84, 28), (84, 23)]],
}


def chalk_line(d, a, b, rnd, width=5):
    n = max(2, int(math.dist(a, b) / 6))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        p0 = (a[0] + (b[0] - a[0]) * t0 + rnd.uniform(-1.2, 1.2), a[1] + (b[1] - a[1]) * t0 + rnd.uniform(-1.2, 1.2))
        p1 = (a[0] + (b[0] - a[0]) * t1 + rnd.uniform(-1.2, 1.2), a[1] + (b[1] - a[1]) * t1 + rnd.uniform(-1.2, 1.2))
        d.line([p0, p1], fill=int(rnd.uniform(150, 235)), width=max(2, int(width + rnd.uniform(-1.5, 1.5))))


PRICES = {'pistol': (500,), 'smg': (1250,), 'rifle': (500, 1500), 'shotgun': (750,)}   # live costs (g27d capture COST lines)


def make(cls, seed, price=None):
    rnd = random.Random(seed)
    a = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(a)
    sx, sy, ox, oy = 4.4, 3.4, 36, 24
    for poly in SHAPES[cls]:
        pts = [(ox + x * sx, oy + y * sy) for x, y in poly]
        for p, q in zip(pts, pts[1:] + pts[:1]):
            chalk_line(d, p, q, rnd)
    for p, q in (((14, 10), (W - 14, 10)), ((W - 14, 10), (W - 14, H - 14)), ((W - 14, H - 14), (14, H - 14)), ((14, H - 14), (14, 10))):
        chalk_line(d, p, q, rnd, width=4)                     # chalk frame
    chalk_line(d, (W / 2 - 70, H - 46), (W / 2 + 70, H - 46), rnd, width=3)     # price line
    if price:
        f = ImageFont.truetype(os.path.join(r'C:\Windows\Fonts', 'segoepr.ttf' if os.path.exists(r'C:\Windows\Fonts\segoepr.ttf') else 'arialbd.ttf'), 40)
        t = str(price)
        l, tp, r, b = d.textbbox((0, 0), t, font=f)
        d.text((W / 2 - (r - l) / 2 - l, H - 92 - tp), t, font=f, fill=225)
    grain = Image.effect_noise((W, H), 70).point(lambda v: 255 if v > 110 else 0)
    a = Image.composite(a, Image.new('L', (W, H), 0), grain).filter(ImageFilter.GaussianBlur(0.8))
    rgba = Image.merge('RGBA', (Image.new('L', (W, H), 236), Image.new('L', (W, H), 234), Image.new('L', (W, H), 226), a))
    return rgba


def main():
    out = os.path.join(sys.argv[1], 'chalk')
    os.makedirs(out, exist_ok=True)
    for k, cls in enumerate(SHAPES):
        im = make(cls, 470 + k)
        im.save(os.path.join(out, 'chalk_%s.png' % cls))
        im.save(os.path.join(out, 'chalk_%s_c.tga' % cls))
        print('chalk', cls, im.size)
        for pr in PRICES.get(cls, ()):
            im = make(cls, 470 + k, pr)
            im.save(os.path.join(out, 'chalk_%s_%d.png' % (cls, pr)))
            im.save(os.path.join(out, 'chalk_%s_%d_c.tga' % (cls, pr)))
            print('chalk', cls, pr)


if __name__ == '__main__':
    main()
