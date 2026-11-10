"""Station Zero story plates at eye level (review g27 item 16), procedural (PIL, no AI).

usage: python -I story_plates.py <art dir>     -> <art dir>/story/<name>.png (preview) and <name>_c.tga (texture)
  story_run_047        cab run-number plate: white 047 on black enamel (hero car west cab, below the left window)
  story_headsign_2347  destination blind: "23:47  STATION ZERO" amber dot-matrix on black (hero car header)
  story_danger_g2      DANGER placard for the G-2 cordon: "DANGER / G-2 LOCKED OUT / DO NOT RESTART / 23:47"
  story_lockout_tag    red DO NOT OPERATE lockout tag with a hasp hole
  story_clock_big      a large stopped station clock face at 23:47 (over the Platform A stair arch)
Images are power-of-two RGBA; the level registers each one only when its TGA exists (build unchanged otherwise).
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

F = r'C:\Windows\Fonts'
bahn = lambda s: ImageFont.truetype(os.path.join(F, 'bahnschrift.ttf'), s)
arialb = lambda s: ImageFont.truetype(os.path.join(F, 'arialbd.ttf'), s)
random.seed(2347)


def grime(im, amount=0.12, specks=300):
    w, h = im.size
    g = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(g)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=int(255 * amount * (0.3 + 0.7 * y / h)))
    for _ in range(specks):
        x, y = random.randrange(w), random.randrange(h)
        r = random.uniform(0.5, 2.5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=random.randrange(40, 140))
    g = g.filter(ImageFilter.GaussianBlur(1.2))
    return Image.composite(Image.new('RGB', (w, h), (34, 28, 20)), im.convert('RGB'), g)


def centred(d, box, text, font, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    d.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), text, font=font, fill=fill)


def run_plate():
    im = Image.new('RGB', (256, 128), (16, 16, 18))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, 251, 123], outline=(150, 150, 150), width=4)
    centred(d, (0, 0, 256, 128), '047', bahn(96), (236, 234, 226))
    for x, y in ((14, 14), (241, 14), (14, 113), (241, 113)):
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(90, 90, 92))
    return grime(im, 0.18)


def headsign():
    w, h = 512, 64
    im = Image.new('RGB', (w, h), (6, 6, 6))
    txt = Image.new('L', (w, h), 0)
    centred(ImageDraw.Draw(txt), (0, 0, w, h), '23:47   STATION ZERO', bahn(44), 255)
    d = ImageDraw.Draw(im)
    for y in range(2, h, 4):          # dot matrix: lit dots where the text is, dim dots elsewhere
        for x in range(2, w, 4):
            on = txt.getpixel((x, y)) > 110
            c = (255, 168, 40) if on else (28, 20, 8)
            d.ellipse([x - 1.4, y - 1.4, x + 1.4, y + 1.4], fill=c)
    return grime(im, 0.10, 80)


def danger():
    w, h = 256, 256
    im = Image.new('RGB', (w, h), (240, 236, 224))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, 70], fill=(200, 30, 28))
    d.ellipse([18, 12, 62, 58], fill=(240, 236, 224))
    centred(d, (18, 12, 62, 58), '!', arialb(40), (200, 30, 28))
    centred(d, (64, 0, w - 6, 70), 'DANGER', arialb(40), (250, 248, 240))
    centred(d, (0, 80, w, 122), 'G-2 LOCKED OUT', arialb(24), (20, 20, 20))
    centred(d, (0, 122, w, 160), 'DO NOT RESTART', arialb(24), (20, 20, 20))
    d.line([(24, 172), (w - 24, 172)], fill=(60, 60, 60), width=2)
    centred(d, (0, 180, w, 212), 'TRIPPED 23:47', bahn(28), (40, 40, 40))
    centred(d, (0, 214, w, 246), 'BY ORDER OF THE ENGINEER', bahn(18), (60, 60, 60))
    d.rectangle([2, 2, w - 3, h - 3], outline=(30, 30, 30), width=3)
    return grime(im, 0.22)


def lockout():
    w, h = 128, 256
    im = Image.new('RGB', (w, h), (190, 28, 24))
    d = ImageDraw.Draw(im)
    d.ellipse([w / 2 - 16, 14, w / 2 + 16, 46], fill=(20, 20, 20), outline=(220, 220, 220), width=4)
    centred(d, (0, 60, w, 120), 'DO NOT', arialb(30), (250, 248, 240))
    centred(d, (0, 112, w, 160), 'OPERATE', arialb(26), (250, 248, 240))
    d.rectangle([12, 172, w - 12, 236], fill=(240, 236, 224))
    centred(d, (12, 172, w - 12, 204), 'R. HALE', bahn(20), (30, 30, 30))
    centred(d, (12, 204, w - 12, 236), '23:47', bahn(22), (30, 30, 30))
    return grime(im, 0.2)


def clock_big():
    s = 512
    im = Image.new('RGB', (s, s), (14, 14, 16))
    d = ImageDraw.Draw(im)
    c, r = s / 2, s / 2 - 10
    d.ellipse([c - r, c - r, c + r, c + r], fill=(232, 228, 214), outline=(40, 40, 40), width=14)
    for k in range(60):
        a = math.radians(k * 6)
        r0 = r - (46 if k % 5 == 0 else 26)
        d.line([(c + math.sin(a) * r0, c - math.cos(a) * r0), (c + math.sin(a) * (r - 16), c - math.cos(a) * (r - 16))],
               fill=(24, 24, 24), width=10 if k % 5 == 0 else 3)
    def hand(deg, length, width):
        a = math.radians(deg)
        d.line([(c - math.sin(a) * 30, c + math.cos(a) * 30), (c + math.sin(a) * length, c - math.cos(a) * length)],
               fill=(18, 18, 18), width=width)
    hand((23 % 12 + 47 / 60) * 30, r * 0.55, 18)      # 23:47
    hand(47 * 6, r * 0.82, 11)
    d.ellipse([c - 14, c - 14, c + 14, c + 14], fill=(18, 18, 18))
    centred(d, (0, c + 70, s, c + 120), 'STATION ZERO', bahn(34), (60, 60, 60))
    return grime(im, 0.16, 400)


def main():
    out = os.path.join(sys.argv[1], 'story')
    os.makedirs(out, exist_ok=True)
    for name, fn in (('story_run_047', run_plate), ('story_headsign_2347', headsign), ('story_danger_g2', danger),
                     ('story_lockout_tag', lockout), ('story_clock_big', clock_big)):
        im = fn()
        im.save(os.path.join(out, name + '.png'))
        im.convert('RGBA').save(os.path.join(out, name + '_c.tga'))
        print(name, im.size)


if __name__ == '__main__':
    main()
