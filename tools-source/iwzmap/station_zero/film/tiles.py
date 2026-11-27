r"""tiles: the Arcade's own tiling pictures, drawn procedurally (seamless by construction: the pattern is a whole number of tiles a repeat).

    python tiles.py            writes C:\studio-data\sz\film\art\arcade\tiles\*.png and a 3 x 3 tile test of each

- floor_quarry: 1978 quarry tiles, 32 x 32 tiles a 1024 picture (tile=384 units -> one tile = 12 units), each tile one of a brown / burnt
  orange / rust / dark chocolate palette with a soft mottle, dark grout; gloss: tiles glossy, grout matte.
- pegboard: brown hardboard with a 1-inch grid of holes (16 holes a 512 picture, tile=32 units: a hole every 2 units).
Why ours (pass 2 frames): the stock `linoleum_floor_tiles_orange_01` read as large plain orange squares, the target's floor is small mottled
brown tiles; the stock perforated panel read cyan.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = r'C:\studio-data\sz\film\art\arcade\tiles'
PALETTE = [(112, 58, 34), (138, 72, 38), (160, 84, 40), (96, 48, 30), (124, 52, 30), (70, 40, 28), (150, 96, 56), (118, 66, 44)]


def floor(px=1024, n=32, seed=1978):
    rnd = random.Random(seed)
    t = px // n
    col = Image.new('RGB', (px, px), (40, 28, 22))
    gl = Image.new('L', (px, px), 50)
    noise = Image.effect_noise((px, px), 28).filter(ImageFilter.GaussianBlur(2.2))
    for j in range(n):
        for i in range(n):
            c = rnd.choice(PALETTE)
            k = rnd.uniform(0.86, 1.12)
            c = tuple(max(0, min(255, int(v * k))) for v in c)
            g = 2
            box = [i * t + g, j * t + g, (i + 1) * t - g, (j + 1) * t - g]
            tile = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), c)
            m = noise.crop(box).point(lambda v: int(v * 0.35))
            tile = Image.blend(tile, Image.merge('RGB', (m, m, m)), 0.12)
            col.paste(tile, box[:2])
            gl.paste(rnd.randint(150, 190), box)
    return col, gl


def pegboard(px=512, holes=16):
    col = Image.new('RGB', (px, px), (122, 86, 52))
    noise = Image.effect_noise((px, px), 16).filter(ImageFilter.GaussianBlur(1.5))
    col = Image.blend(col, Image.merge('RGB', (noise, noise, noise)), 0.08)
    d = ImageDraw.Draw(col)
    step = px // holes
    r = max(3, step // 7)
    for j in range(holes):
        for i in range(holes):
            cx, cy = i * step + step // 2, j * step + step // 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 18, 12))
    return col


def tiletest(im, path):
    w, h = im.size
    s = Image.new(im.mode, (w * 3, h * 3))
    for j in range(3):
        for i in range(3):
            s.paste(im, (i * w, j * h))
    s.resize((min(1536, w * 3), min(1536, h * 3))).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    c, g = floor()
    c.save(os.path.join(OUT, 'floor_quarry_c.png'))
    g.save(os.path.join(OUT, 'floor_quarry_g.png'))
    tiletest(c, os.path.join(OUT, 'floor_quarry_tiletest.jpg'))
    p = pegboard()
    p.save(os.path.join(OUT, 'pegboard_c.png'))
    tiletest(p, os.path.join(OUT, 'pegboard_tiletest.jpg'))
    print(OUT)


if __name__ == '__main__':
    main()
