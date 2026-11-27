r"""make_goods_pictures: the pictures of the goods of Needle Drop and Heel & Key (worker A3a), drawn with PIL.

    python make_goods_pictures.py [out folder]        default C:\studio-data\sz\film\art\arcade\goods_a

Words: every title, artist, genre, card line and claim tag is read from C:\studio-data\sz\film\copy\arcade_copy.json at run time
(needle_drop_sleeves, needle_drop_rental, window_cards, heel_key_board.claim_tags), never typed here. Two exceptions, decisions of the worker:
the party tape's J-card says PARTY TAPE and CAR 6 (words of the Needle Drop door card, recomposed), and the "0" of the quest tag (canon).
Art: procedural graphic design in the manner of each year's sleeves (1978 to 1984). The image tool was out of quota on 27 Nov 2026; the
prompts are in prompts/ and gen_raw.sh makes wordless painted art into ...\goods_a\raw: when raw/<prompt>.png exists it replaces the
aw: when raw/<prompt>.png exists it replaces the
procedural art under the same words. Deterministic: every noise is seeded, so a rerun writes the same files (Studio names a picture's
material by the file's hash). In the game a picture gets 8 pixels a unit (an LP sleeve 12.4 units = 100 px).
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\studio-data\sz\film\art\arcade\goods_a'
COPY = r'C:\studio-data\sz\film\copy\arcade_copy.json'
ART = r'C:\studio-data\sz\film\art\arcade'
F = r'C:\Windows\Fonts'
S = 512                    # sleeve master (12.4 units -> 100 px in game)


def font(name, px, var=None):
    f = ImageFont.truetype(os.path.join(F, name), px)
    if var:
        f.set_variation_by_name(var)
    return f


def grain(im, amount=10, seed=1):
    rnd = random.Random(seed * 7919 + 17)
    n = Image.new('L', im.size)
    n.putdata([max(0, min(255, int(rnd.gauss(128, 64)))) for _ in range(im.size[0] * im.size[1])])
    n = n.point(lambda v: 128 + (v - 128) * amount // 32)
    base = im.convert('RGB')
    return ImageChops.overlay(base, Image.merge('RGB', (n, n, n)))


def ringwear(im, strength=26):
    """the pale ring an LP leaves on its sleeve"""
    w, h = im.size
    m = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(m)
    r = w * 0.46
    d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], outline=strength, width=max(2, w // 60))
    m = m.filter(ImageFilter.GaussianBlur(w / 90))
    white = Image.new('RGB', im.size, (235, 230, 220))
    return Image.composite(white, im.convert('RGB'), m)


def vgrad(size, top, bot):
    w, h = size
    im = Image.new('RGB', size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return im


def text_fit(d, xy, s, fnt_name, max_w, px, var=None, fill=(255, 255, 255), anchor='mm', stroke=0, stroke_fill=None):
    while px > 6:
        f = font(fnt_name, px, var)
        bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
        if bb[2] - bb[0] <= max_w:
            break
        px -= 2
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)
    return f


def gradient_text(size, xy, s, fnt, top, bot, anchor='mm', stroke=0, stroke_fill=(0, 0, 0)):
    """letters filled with a vertical gradient (chrome, gold), on a transparent layer"""
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).text(xy, s, font=fnt, fill=255, anchor=anchor)
    bb = mask.getbbox() or (0, 0, size[0], size[1])
    g = Image.new('RGB', size, top)
    gh = vgrad((size[0], bb[3] - bb[1] + 1), top, bot)
    g.paste(gh, (0, bb[1]))
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    if stroke:
        sm = Image.new('L', size, 0)
        ImageDraw.Draw(sm).text(xy, s, font=fnt, fill=255, anchor=anchor, stroke_width=stroke, stroke_fill=255)
        layer.paste(Image.new('RGBA', size, stroke_fill + (255,)), (0, 0), sm)
    layer.paste(g.convert('RGBA'), (0, 0), mask)
    return layer


# ------------------------------------------------------------------------------------------------ the eight sleeves
def sleeve_1(a, t):      # PLASTIC TONE, NO STATIC TONITE, LP 1981: new wave, Memphis shapes
    im = Image.new('RGB', (S, S), (18, 18, 20))
    d = ImageDraw.Draw(im)
    for i in range(8):
        for j in range(8):
            d.ellipse([28 + i * 30, 300 + j * 26, 36 + i * 30, 308 + j * 26], fill=(250, 222, 40))
    d.polygon([(250, 470), (470, 470), (360, 240)], fill=(255, 64, 160))
    pts = [(40 + x, 220 + 26 * math.sin(x / 26.0)) for x in range(0, 440, 4)]
    d.line(pts, fill=(30, 200, 190), width=16, joint='curve')
    for k in range(16):
        d.rectangle([k * 32, 486, k * 32 + 16, 502], fill=(240, 240, 240))
        d.rectangle([k * 32 + 16, 486, k * 32 + 32, 502], fill=(18, 18, 20))
    rnd = random.Random(81)
    tv = Image.new('L', (130, 90))
    tv.putdata([rnd.randrange(40, 255) for _ in range(130 * 90)])
    im.paste(Image.merge('RGB', (tv, tv, tv)), (330, 330))
    d.rectangle([326, 326, 464, 424], outline=(30, 200, 190), width=4)
    d.rectangle([0, 0, S, 150], fill=(18, 18, 20))
    text_fit(d, (S // 2, 66), a, 'ariblk.ttf', 460, 86, fill=(255, 64, 160))
    text_fit(d, (S // 2, 130), t, 'bahnschrift.ttf', 420, 40, var='Bold', fill=(250, 222, 40))
    return ringwear(grain(im, 8, 1))


def sleeve_2(a, t):      # MARA SOL, MIDNIGHT METER, 12-INCH 1979: disco airbrush, a glowing meter dial, gold script
    im = vgrad((S, S), (40, 8, 70), (200, 30, 140))
    d = ImageDraw.Draw(im)
    for k in range(8):
        y = 300 + k * 26
        d.rectangle([0, y, S, y + 10], fill=(60 + k * 12, 10, 90 + k * 8))
    glow = Image.new('L', (S, S), 0)
    ImageDraw.Draw(glow).ellipse([136, 170, 376, 410], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    im = Image.composite(Image.new('RGB', (S, S), (255, 200, 120)), im, glow.point(lambda v: v * 7 // 10))
    d = ImageDraw.Draw(im)
    cx, cy, r = 256, 290, 110
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(230, 230, 240), width=8)
    for k in range(13):
        ang = math.radians(210 - k * 20)
        d.line([(cx + (r - 22) * math.cos(ang), cy - (r - 22) * math.sin(ang)), (cx + (r - 6) * math.cos(ang), cy - (r - 6) * math.sin(ang))], fill=(240, 220, 150), width=5)
    ang = math.radians(60)
    d.line([(cx, cy), (cx + 90 * math.cos(ang), cy - 90 * math.sin(ang))], fill=(255, 60, 120), width=8)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(240, 220, 150))
    rnd = random.Random(79)
    for _ in range(22):
        x, y, s = rnd.randrange(20, 490), rnd.randrange(160, 500), rnd.randrange(4, 16)
        d.polygon([(x, y - s), (x + s / 4, y), (x, y + s), (x - s / 4, y)], fill=(255, 250, 220))
        d.polygon([(x - s, y), (x, y - s / 4), (x + s, y), (x, y + s / 4)], fill=(255, 250, 220))
    lay = gradient_text((S, S), (S // 2, 70), a, font('georgiaz.ttf', 78), (255, 236, 160), (190, 120, 30), stroke=3, stroke_fill=(60, 10, 60))
    im = Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')
    d = ImageDraw.Draw(im)
    text_fit(d, (S // 2, 140), t, 'georgiai.ttf', 420, 40, fill=(255, 230, 250))
    return ringwear(grain(im, 6, 2))


def sleeve_3(a, t):      # IRON QUARRY, SHIFT WHISTLE, LP 1980: hard rock, a foundry on a quarry cliff, steam, chrome letters
    im = vgrad((S, S), (20, 6, 6), (120, 30, 10))
    d = ImageDraw.Draw(im)
    glow = Image.new('L', (S, S), 0)
    ImageDraw.Draw(glow).ellipse([60, 360, 460, 640], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    im = Image.composite(Image.new('RGB', (S, S), (255, 120, 20)), im, glow)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 512), (0, 400), (120, 380), (200, 430), (300, 390), (400, 420), (512, 380), (512, 512)], fill=(30, 18, 14))
    for x, w, h in ((150, 70, 120), (240, 90, 160), (350, 60, 100)):
        d.rectangle([x, 400 - h, x + w, 410], fill=(14, 10, 10))
        d.rectangle([x + w // 3, 400 - h - 90, x + w // 3 + 14, 400 - h], fill=(14, 10, 10))
        for k in range(3):
            d.rectangle([x + 10 + k * 18, 330 - h // 3, x + 20 + k * 18, 344 - h // 3], fill=(255, 150, 40))
    d.line([(290, 300), (330, 470)], fill=(255, 190, 60), width=10)
    steam = Image.new('L', (S, S), 0)
    sd = ImageDraw.Draw(steam)
    rnd = random.Random(80)
    for k in range(26):
        y = 140 - k * 4 + rnd.randrange(-6, 6)
        r = 20 + k * 3
        x = 286 + rnd.randrange(-10, 30) + k * 2
        sd.ellipse([x - r, y + 140 - r // 2 + k * 2, x + r, y + 140 + r // 2 + k * 2], fill=180)
    steam = steam.filter(ImageFilter.GaussianBlur(10))
    im = Image.composite(Image.new('RGB', (S, S), (235, 230, 225)), im, steam)
    lay = gradient_text((S, S), (S // 2, 66), a, font('impact.ttf', 96), (250, 250, 255), (90, 95, 110), stroke=5, stroke_fill=(10, 0, 0))
    im = Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')
    d = ImageDraw.Draw(im)
    text_fit(d, (S // 2, 138), t, 'impact.ttf', 300, 44, fill=(255, 170, 40), stroke=3, stroke_fill=(10, 0, 0))
    return ringwear(grain(im, 9, 3))


def sleeve_4(a, t):      # SILO NINE, COLD CORRIDOR, CASSETTE 1983: post-punk, a grainy one-colour corridor, small type
    im = Image.new('RGB', (S, S), (232, 230, 224))
    ph = Image.new('L', (380, 300), 10)
    d = ImageDraw.Draw(ph)
    for k in range(9):
        f = 0.9 ** (k * 2)
        w, h = 380 * f, 300 * f
        x0, y0 = 190 - w / 2, 150 - h / 2
        d.rectangle([x0, y0, x0 + w, y0 + h], outline=20 + k * 22, width=3)
    d.rectangle([170, 40, 210, 48], fill=255)
    d.polygon([(0, 300), (95, 225), (285, 225), (380, 300)], fill=60)
    ph = ph.filter(ImageFilter.GaussianBlur(1.2))
    rnd = random.Random(83)
    noise = Image.new('L', ph.size)
    noise.putdata([rnd.randrange(0, 90) for _ in range(ph.size[0] * ph.size[1])])
    ph = ImageChops.add(ph, noise, 1.0, -40)
    im.paste(ImageOps.colorize(ph, (12, 12, 14), (225, 225, 225)), (66, 120))
    d = ImageDraw.Draw(im)
    d.line([(0, 450), (512, 360)], fill=(120, 190, 235), width=5)
    text_fit(d, (66, 70), a, 'bahnschrift.ttf', 300, 42, var='Light', fill=(15, 15, 15), anchor='lm')
    text_fit(d, (66, 460), t, 'bahnschrift.ttf', 300, 30, var='Light Condensed', fill=(15, 15, 15), anchor='lm')
    return ringwear(grain(im, 6, 4), 18)


def sleeve_5(a, t):      # PIER SEVEN, SAIL TO SUNSET, LP 1978: soft rock, a banded sun and a sail, pastel airbrush
    im = vgrad((S, S), (250, 196, 170), (170, 140, 200))
    d = ImageDraw.Draw(im)
    cx, cy, r = 256, 330, 150
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 210, 90))
    for k in range(6):
        y = cy + 10 + k * 22
        d.rectangle([0, y, S, y + 6 + k * 2], fill=(250, 170 - k * 8, 150 + k * 6))
    sea = vgrad((S, 140), (120, 150, 200), (60, 90, 150))
    im.paste(sea, (0, 372))
    d = ImageDraw.Draw(im)
    for k in range(9):
        d.line([(120 + k * 6, 380 + k * 12), (390 - k * 6, 380 + k * 12)], fill=(255, 200, 120), width=3)
    d.polygon([(250, 250), (250, 390), (190, 390)], fill=(250, 250, 245))
    d.polygon([(258, 270), (258, 390), (300, 390)], fill=(235, 235, 230))
    d.polygon([(180, 392), (320, 392), (300, 408), (196, 408)], fill=(40, 40, 60))
    d.line([(470, 512), (440, 280)], fill=(40, 30, 50), width=10)
    for ang in (200, 230, 260, 300, 330):
        a_ = math.radians(ang)
        d.line([(440, 280), (440 + 80 * math.cos(a_), 280 - 40 * math.sin(a_) + 20)], fill=(40, 30, 50), width=8)
    text_fit(d, (S // 2, 64), a, 'georgiaz.ttf', 420, 64, fill=(255, 255, 255), stroke=2, stroke_fill=(200, 110, 110))
    text_fit(d, (S // 2, 128), t, 'georgiai.ttf', 360, 40, fill=(120, 60, 110))
    return ringwear(grain(im, 6, 5))


def sleeve_6(a, t):      # DUB SWITCH, NORTH PIER ECHO, LP 1982: dub, linocut rings and a speaker stack on a pier
    im = Image.new('RGB', (S, S), (16, 14, 12))
    d = ImageDraw.Draw(im)
    for k, c in enumerate([(200, 30, 30), (230, 180, 30), (30, 150, 60)] * 4):
        r = 60 + k * 34
        d.ellipse([256 - r, 380 - r * 0.45, 256 + r, 380 + r * 0.45], outline=c, width=12)
    for row in range(3):
        for col in range(2 - (row == 2)):
            x, y = 190 + col * 66 + (row == 2) * 33, 372 - row * 66
            d.rectangle([x, y - 64, x + 62, y], fill=(235, 228, 205), outline=(16, 14, 12), width=4)
            d.ellipse([x + 9, y - 56, x + 53, y - 12], fill=(16, 14, 12))
            d.ellipse([x + 22, y - 43, x + 40, y - 25], fill=(235, 228, 205))
    d.rectangle([90, 374, 422, 386], fill=(235, 228, 205))
    for k in range(6):
        d.rectangle([110 + k * 56, 386, 120 + k * 56, 460], fill=(235, 228, 205))
    rnd = random.Random(82)
    for _ in range(500):
        x, y = rnd.randrange(S), rnd.randrange(S)
        d.line([(x, y), (x + rnd.randrange(3, 14), y + rnd.randrange(-2, 2))], fill=(16, 14, 12), width=1)
    text_fit(d, (S // 2, 64), a, 'ariblk.ttf', 440, 80, fill=(235, 228, 205))
    text_fit(d, (S // 2, 132), t, 'ariblk.ttf', 400, 40, fill=(230, 180, 30))
    return ringwear(grain(im, 12, 6))


def sleeve_7(a, t):      # RAYMOND DEAN, TRUCK STOP RAIN, 8-TRACK 1979: country, a faded photograph of a diner in the rain, framed
    im = Image.new('RGB', (S, S), (238, 232, 214))
    ph = vgrad((440, 330), (60, 90, 100), (120, 110, 90))
    d = ImageDraw.Draw(ph)
    d.rectangle([40, 120, 330, 230], fill=(70, 60, 55))
    d.rectangle([30, 110, 340, 124], fill=(150, 40, 40))
    for k in range(6):
        d.rectangle([56 + k * 46, 150, 90 + k * 46, 190], fill=(250, 200, 110))
    d.line([(60, 104), (300, 104)], fill=(255, 70, 70), width=5)
    d.rectangle([330, 150, 440, 230], fill=(140, 130, 120))
    d.rectangle([340, 120, 400, 160], fill=(150, 140, 130))
    for x in (350, 380, 420):
        d.ellipse([x - 12, 220, x + 12, 244], fill=(20, 20, 20))
    d.rectangle([200, 175, 214, 230], fill=(25, 20, 20))
    d.polygon([(194, 176), (220, 176), (215, 168), (199, 168)], fill=(25, 20, 20))
    d.rectangle([0, 232, 440, 330], fill=(45, 50, 55))
    refl = ph.crop((0, 120, 440, 232)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(3)).resize((440, 98))
    ph.paste(Image.blend(ph.crop((0, 232, 440, 330)), refl, 0.5), (0, 232))
    d = ImageDraw.Draw(ph)
    rnd = random.Random(79)
    for _ in range(260):
        x, y = rnd.randrange(440), rnd.randrange(330)
        d.line([(x, y), (x - 6, y + 22)], fill=(190, 200, 205), width=1)
    ph = Image.blend(ph, Image.new('RGB', ph.size, (200, 170, 120)), 0.18)
    im.paste(ph, (36, 36))
    d = ImageDraw.Draw(im)
    text_fit(d, (S // 2, 410), a, 'georgiab.ttf', 440, 60, fill=(120, 30, 30))
    text_fit(d, (S // 2, 468), t, 'georgia.ttf', 380, 36, fill=(40, 40, 40))
    return ringwear(grain(im, 7, 7))


def sleeve_8(a, t):      # TONE WHEEL, TWO STEP TEST, 45 RPM 1984: synth-pop, chrome over a laser grid
    im = vgrad((S, S), (10, 12, 50), (110, 20, 110))
    d = ImageDraw.Draw(im)
    cx, cy, r = 256, 300, 120
    for k in range(10):
        y0 = cy - r + k * 24
        d.chord([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=None)
    sun = Image.new('L', (S, S), 0)
    ImageDraw.Draw(sun).pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=255)
    for k in range(6):
        ImageDraw.Draw(sun).rectangle([0, cy - 60 + k * 12, S, cy - 56 + k * 12], fill=0)
    im = Image.composite(vgrad((S, S), (255, 230, 60), (255, 60, 120)), im, sun)
    d = ImageDraw.Draw(im)
    d.rectangle([0, cy, S, S], fill=(14, 6, 30))
    for k in range(-12, 13):
        d.line([(cx + k * 12, cy), (cx + k * 70, S)], fill=(255, 40, 200), width=2)
    for k in range(9):
        y = cy + (S - cy) * (k / 8.0) ** 1.8
        d.line([(0, y), (S, y)], fill=(255, 40, 200), width=2)
    ring = Image.new('L', (S, S), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse([176, 200, 336, 360], fill=255)
    rd.ellipse([206, 230, 306, 330], fill=0)
    for ang in range(0, 360, 45):
        a_ = math.radians(ang)
        rd.line([(256, 280), (256 + 60 * math.cos(a_), 280 + 60 * math.sin(a_))], fill=255, width=8)
    im = Image.composite(vgrad((S, S), (250, 250, 255), (70, 90, 130)), im, ring)
    lay = gradient_text((S, S), (S // 2, 70), a, font('impact.ttf', 90), (240, 250, 255), (80, 200, 240), stroke=3, stroke_fill=(20, 0, 60))
    lay = lay.transform(lay.size, Image.AFFINE, (1, 0.25, -18, 0, 1, 0))
    im = Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')
    d = ImageDraw.Draw(im)
    text_fit(d, (S // 2, 140), t, 'bahnschrift.ttf', 380, 38, var='SemiBold SemiCondensed', fill=(120, 240, 255))
    return ringwear(grain(im, 5, 8))


SLEEVES = [sleeve_1, sleeve_2, sleeve_3, sleeve_4, sleeve_5, sleeve_6, sleeve_7, sleeve_8]


# ------------------------------------------------------------------------------------------------ the six rental boxes and the film's own
TW, TH = 300, 540          # a VHS box front, 4.1 x 7.4 (in game 7.5 x 13.5 units -> 60 x 108 px)


def tape_frame(art, title, genre, title_font='impact.ttf', tcol=(255, 255, 255), stroke=(0, 0, 0), logo=None):
    im = Image.new('RGB', (TW, TH), (10, 10, 12))
    im.paste(art.resize((TW - 16, TH - 90)), (8, 8))
    d = ImageDraw.Draw(im)
    words = title.split()
    lines = [title] if len(title) <= 12 else [' '.join(words[:len(words) // 2 + (len(words) % 2)]), ' '.join(words[len(words) // 2 + (len(words) % 2):])]
    y = 46 if len(lines) == 1 else 34
    for ln in lines:
        text_fit(d, (TW // 2, y), ln, title_font, TW - 30, 56, fill=tcol, stroke=3, stroke_fill=stroke)
        y += 52
    d.rectangle([0, TH - 82, TW, TH], fill=(10, 10, 12))
    text_fit(d, (TW // 2, TH - 52), genre, 'bahnschrift.ttf', TW - 40, 26, var='Bold Condensed', fill=(230, 230, 230))
    if logo is not None:                               # the shop's rental sticker: its own logo, canon
        lg = logo.resize((58, 58))
        im.paste(lg, (TW - 70, TH - 140), lg)
    return grain(im, 5, sum(map(ord, title)) & 0xff)


def art_steel_harbor():
    im = vgrad((284, 450), (20, 30, 60), (60, 70, 90))
    d = ImageDraw.Draw(im)
    g = Image.new('L', im.size, 0)
    ImageDraw.Draw(g).ellipse([150, 120, 270, 240], fill=255)
    im = Image.composite(Image.new('RGB', im.size, (255, 150, 50)), im, g.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(im)
    d.line([(210, 180), (210, 450)], fill=(15, 15, 20), width=6)
    d.ellipse([200, 172, 220, 186], fill=(255, 210, 120))
    for x in (20, 90):
        d.line([(x, 450), (x + 20, 120)], fill=(15, 15, 25), width=6)
        d.line([(x + 20, 120), (x + 120, 140)], fill=(15, 15, 25), width=5)
    d.rectangle([0, 330, 284, 370], fill=(25, 25, 35))
    d.polygon([(100, 450), (110, 300), (125, 280), (150, 280), (162, 300), (170, 450)], fill=(10, 10, 12))
    d.ellipse([122, 248, 152, 280], fill=(10, 10, 12))
    d.polygon([(112, 256), (162, 256), (152, 244), (122, 244)], fill=(10, 10, 12))
    fog = Image.new('L', im.size, 0)
    ImageDraw.Draw(fog).rectangle([0, 360, 284, 450], fill=120)
    return Image.composite(Image.new('RGB', im.size, (120, 130, 150)), im, fog.filter(ImageFilter.GaussianBlur(25)))


def art_night_freight():
    im = vgrad((284, 450), (8, 10, 40), (60, 40, 50))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 300, 284, 450], fill=(70, 45, 30))
    for k in (-1, 1):
        d.line([(142 + k * 10, 300), (142 + k * 160, 450)], fill=(160, 160, 170), width=4)
    d.polygon([(92, 300), (192, 300), (200, 160), (84, 160)], fill=(25, 25, 30))
    d.rectangle([110, 175, 174, 215], fill=(70, 80, 90))
    g = Image.new('L', im.size, 0)
    ImageDraw.Draw(g).ellipse([102, 205, 182, 285], fill=255)
    im = Image.composite(Image.new('RGB', im.size, (255, 250, 220)), im, g.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.line([(200, 190), (240, 260)], fill=(10, 10, 10), width=8)
    d.ellipse([228, 170, 246, 188], fill=(10, 10, 10))
    for x in (30, 60):
        d.ellipse([x, 390, x + 12, 398], fill=(255, 240, 180))
    return grain(im, 8, 22)


def art_star_sector():
    im = vgrad((284, 450), (6, 6, 30), (40, 10, 60))
    rnd = random.Random(33)
    d = ImageDraw.Draw(im)
    for _ in range(160):
        x, y = rnd.randrange(284), rnd.randrange(450)
        d.point((x, y), fill=(255, 255, 255))
    neb = Image.new('L', im.size, 0)
    nd = ImageDraw.Draw(neb)
    for _ in range(12):
        x, y, r = rnd.randrange(0, 284), rnd.randrange(60, 300), rnd.randrange(30, 80)
        nd.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randrange(60, 140))
    im = Image.composite(Image.new('RGB', im.size, (220, 50, 180)), im, neb.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(im)
    d.ellipse([150, 60, 270, 180], fill=(200, 140, 70))
    d.ellipse([120, 105, 300, 135], outline=(240, 210, 150), width=5)
    d.polygon([(40, 330), (200, 270), (210, 290)], fill=(230, 230, 240))
    d.polygon([(120, 300), (150, 340), (160, 300)], fill=(180, 180, 200))
    for k in range(3):
        d.line([(40, 330 + k * 4), (0, 345 + k * 6)], fill=(120, 220, 255), width=2)
    d.line([(220, 200), (284, 160)], fill=(255, 60, 60), width=3)
    return grain(im, 6, 33)


def art_fist_foundry():
    im = vgrad((284, 450), (40, 5, 0), (240, 110, 20))
    d = ImageDraw.Draw(im)
    rnd = random.Random(44)
    for _ in range(140):
        x, y = rnd.randrange(284), rnd.randrange(450)
        d.line([(x, y), (x + rnd.randrange(-4, 4), y - rnd.randrange(4, 14))], fill=(255, 230, 120), width=2)
    c = (10, 5, 5)
    d.ellipse([150, 100, 182, 132], fill=c)
    d.line([(160, 130), (130, 230)], fill=c, width=22)
    d.line([(150, 150), (230, 120)], fill=c, width=12)
    d.line([(145, 160), (90, 190)], fill=c, width=12)
    d.line([(130, 225), (250, 200)], fill=c, width=16)
    d.line([(130, 225), (90, 300)], fill=c, width=16)
    d.line([(90, 300), (110, 340)], fill=c, width=14)
    for x in range(0, 284, 40):
        d.polygon([(x, 450), (x + 14, 380 + (x % 3) * 10), (x + 28, 450)], fill=c)
    return im


def art_two_dogs():
    im = vgrad((284, 450), (110, 190, 255), (200, 230, 255))
    d = ImageDraw.Draw(im)
    d.ellipse([200, 30, 260, 90], fill=(255, 220, 60))
    d.rectangle([0, 320, 284, 450], fill=(40, 110, 190))
    for k in range(8):
        d.arc([k * 40 - 10, 316, k * 40 + 30, 336], 180, 360, fill=(230, 240, 255), width=3)
    d.polygon([(30, 300), (250, 300), (220, 360), (60, 360)], fill=(200, 40, 40))
    d.rectangle([30, 292, 250, 302], fill=(250, 250, 250))
    for x, col in ((90, (200, 150, 90)), (180, (240, 235, 220))):
        d.ellipse([x - 32, 210, x + 32, 274], fill=col)
        d.ellipse([x - 40, 214, x - 22, 250], fill=(120, 80, 40))
        d.ellipse([x + 22, 214, x + 40, 250], fill=(120, 80, 40))
        d.ellipse([x - 14, 232, x - 6, 240], fill=(0, 0, 0))
        d.ellipse([x + 6, 232, x + 14, 240], fill=(0, 0, 0))
        d.ellipse([x - 8, 248, x + 8, 260], fill=(30, 20, 20))
        d.rectangle([x - 30, 196, x + 30, 212], fill=(250, 250, 250))
        d.rectangle([x - 34, 208, x + 34, 214], fill=(20, 30, 80))
        d.rectangle([x - 30, 274, x + 30, 300], fill=col)
    d.polygon([(210, 140), (250, 120), (240, 150)], fill=(250, 250, 250))
    return im


def art_summer_pier():
    im = vgrad((284, 450), (250, 150, 170), (150, 120, 200))
    d = ImageDraw.Draw(im)
    d.ellipse([100, 200, 190, 290], fill=(255, 200, 120))
    cx, cy, r = 200, 170, 90
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(60, 30, 70), width=5)
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        d.line([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))], fill=(60, 30, 70), width=3)
        d.ellipse([cx + r * math.cos(a) - 6, cy + r * math.sin(a) - 6, cx + r * math.cos(a) + 6, cy + r * math.sin(a) + 6], fill=(255, 240, 120))
    d.polygon([(cx, cy), (cx - 50, 330), (cx + 50, 330)], outline=(60, 30, 70), width=4)
    d.rectangle([0, 330, 284, 450], fill=(70, 160, 180))
    d.rectangle([0, 318, 284, 326], fill=(50, 25, 50))
    for x in range(0, 284, 22):
        d.rectangle([x, 326, x + 4, 360], fill=(50, 25, 50))
    for x, h in ((80, 58), (112, 64)):
        d.ellipse([x - 9, 318 - h, x + 9, 318 - h + 18], fill=(40, 20, 40))
        d.rectangle([x - 10, 318 - h + 16, x + 10, 320], fill=(40, 20, 40))
    d.rectangle([60, 330, 72, 348], fill=(255, 255, 255))
    return im


TAPES = [art_steel_harbor, art_night_freight, art_star_sector, art_fist_foundry, art_two_dogs, art_summer_pier]
TAPE_STYLE = [dict(tcol=(255, 255, 255), stroke=(200, 90, 20)), dict(tcol=(255, 230, 60), stroke=(0, 0, 0)), dict(title_font='ariblk.ttf', tcol=(255, 230, 120), stroke=(60, 0, 80)),
              dict(tcol=(255, 40, 30), stroke=(255, 230, 60)), dict(title_font='ariblk.ttf', tcol=(255, 230, 40), stroke=(20, 60, 160)), dict(title_font='segoescb.ttf', tcol=(255, 255, 255), stroke=(200, 60, 140))]


# ------------------------------------------------------------------------------------------------ cards, tags, sheets
def card(lines, ink, paper=(245, 240, 225), size=(540, 360), seed=0, tape=True):
    """a hand-lettered card taped up: marker letters (Ink Free bold by stroke), two strips of tape"""
    rnd = random.Random(seed)
    im = Image.new('RGB', size, paper)
    d = ImageDraw.Draw(im)
    w, h = size
    y = h * 0.34
    for k, ln in enumerate(lines):
        px = 76 if k == 0 else 58
        text_fit(d, (w // 2 + rnd.randrange(-6, 6), y), ln, 'Inkfree.ttf', w - 50, px, fill=ink, stroke=2, stroke_fill=ink)
        y += h * 0.36
    if tape:
        for x in (36, w - 96):
            d.polygon([(x, 0), (x + 70, 0), (x + 64, 30), (x - 4, 26)], fill=(225, 215, 170))
    im = grain(im, 6, seed)
    return im


def claim_tag(text, seed, big=False):
    """a manila claim tag with an eyelet and a string, typed text (Courier)"""
    w, h = 160, 280
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(10, 40), (40, 10), (120, 10), (150, 40), (150, 270), (10, 270)], fill=(214, 186, 128, 255), outline=(150, 120, 70, 255))
    d.ellipse([66, 26, 94, 54], fill=(150, 120, 70, 255))
    d.ellipse([72, 32, 88, 48], fill=(0, 0, 0, 0))
    if big:
        text_fit(d, (80, 170), text, 'courbd.ttf', 120, 150, fill=(40, 30, 25, 255))
    else:
        name, date = text.split()[0], ' '.join(text.split()[1:])
        if name == 'TAN' or name == 'RED':                 # TAN BOOT, RED PUMP: the article, then the date
            name, date = ' '.join(text.split()[:2]), ' '.join(text.split()[2:])
        y = 104
        for ln in name.split():
            text_fit(d, (80, y), ln, 'arialbd.ttf', 132, 46, fill=(30, 25, 70, 255))
            y += 50
        text_fit(d, (80, 246), date, 'arialbd.ttf', 120, 36, fill=(150, 20, 20, 255))
    rnd = random.Random(seed)
    for _ in range(40):
        x, y = rnd.randrange(14, 146), rnd.randrange(60, 266)
        d.point((x, y), fill=(160, 130, 90, 255))
    return im


def key_board():
    """the board of key blanks: rows of nickel and brass blanks on hooks on a dark board, one hook empty and tagged (the tag is its own picture)"""
    w, h = 640, 400
    im = Image.new('RGB', (w, h), (40, 34, 30))
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for r in range(5):
        for c in range(14):
            x, y = 30 + c * 44, 30 + r * 74
            d.ellipse([x + 14, y, x + 22, y + 8], fill=(120, 110, 100))
            if (r, c) == (2, 7):
                continue                                   # the empty hook: the "0" tag hangs here
            col = (200, 165, 70) if (r + c) % 3 else (190, 195, 200)
            d.ellipse([x + 6, y + 6, x + 30, y + 30], fill=col)
            d.ellipse([x + 14, y + 12, x + 22, y + 20], fill=(40, 34, 30))
            d.rectangle([x + 14, y + 30, x + 22, y + 62], fill=col)
            for k in range(rnd.randrange(3, 5)):
                d.rectangle([x + 22, y + 36 + k * 6, x + 25, y + 39 + k * 6], fill=col)
    return grain(im, 6, 9)


def laces_card():
    w, h = 240, 360
    im = Image.new('RGB', (w, h), (235, 228, 210))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 40], fill=(110, 20, 30))
    d.ellipse([w / 2 - 10, 10, w / 2 + 10, 30], fill=(235, 228, 210))
    cols = [(20, 20, 20), (90, 55, 30), (150, 110, 70), (240, 240, 235), (20, 20, 20), (90, 55, 30)]
    for k, c in enumerate(cols):
        x = 24 + k * 34
        d.line([(x, 60), (x + 8, 330)], fill=c, width=8)
        d.line([(x + 12, 60), (x + 4, 330)], fill=c, width=8)
        d.rectangle([x - 2, 330, x + 14, 350], fill=(200, 200, 200))
    return grain(im, 5, 11)


def sleeve_sheet(sleeves, order, gaps=(), board=(28, 22, 20)):
    """a rail of face-out sleeves: four sleeves 12.4 wide with 1.1 gaps on a 56 x 13 board (4.8 px a unit here: 269 x 62 -> drawn at 4x)"""
    k = 20.0                                              # px per unit for the master
    W, H = int(56 * k), int(13 * k)
    im = Image.new('RGB', (W, H), board)
    d = ImageDraw.Draw(im)
    s = int(12.4 * k)
    for i, idx in enumerate(order):
        x = int((1.1 + i * 13.5) * k)
        if i in gaps:
            d.rectangle([x, int(0.5 * k), x + s, int(12.9 * k)], fill=tuple(c + 10 for c in board))
            continue
        sl = sleeves[idx].resize((s, s))
        im.paste(sl, (x, int(0.3 * k)))
        d.line([(x + s, int(0.3 * k)), (x + s, int(0.3 * k) + s)], fill=(0, 0, 0), width=3)
    return im


def bin_tops(seed):
    """the tops of LPs standing tight in a bin, seen from above: 28 units of edges (rows of 0.25 units), 12.4 wide"""
    k = 16
    W, H = int(12.4 * k), int(28 * k)
    im = Image.new('RGB', (W, H), (10, 10, 10))
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    y = 0
    pal = [(30, 30, 30), (200, 60, 40), (230, 220, 200), (40, 70, 140), (250, 200, 40), (20, 20, 20), (120, 40, 120), (60, 140, 90), (240, 120, 30)]
    while y < H:
        t = rnd.choice((3, 4, 4, 5))
        c = rnd.choice(pal)
        d.rectangle([0, y, W, y + t - 1], fill=c)
        d.line([(0, y + t - 1), (W, y + t - 1)], fill=(0, 0, 0))
        y += t
    return grain(im, 8, seed)


def spines(seed):
    """LPs filed spine-out on a shelf: 28 units of spines (0.25 to 0.4 a sleeve), 12.4 high, seen from the front"""
    k = 16
    W, H = int(28 * k), int(12.4 * k)
    im = Image.new('RGB', (W, H), (12, 12, 12))
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    x = 0
    pal = [(30, 30, 30), (200, 60, 40), (230, 220, 200), (40, 70, 140), (250, 200, 40), (20, 20, 20), (120, 40, 120), (60, 140, 90), (240, 120, 30), (200, 200, 205)]
    while x < W:
        t = rnd.choice((4, 5, 5, 6))
        c = rnd.choice(pal)
        d.rectangle([x, rnd.randrange(0, 6), x + t - 1, H], fill=c)
        d.line([(x + t - 1, 0), (x + t - 1, H)], fill=(0, 0, 0))
        if rnd.random() < 0.5:
            d.rectangle([x + 1, H // 3, x + t - 2, H // 3 + rnd.randrange(20, 60)], fill=tuple(255 - v for v in c))
        x += t
    return grain(im, 8, seed)


RAW = os.path.join(OUT, 'raw')
RAW_SLEEVE = ['sleeve_1_plastic_tone', 'sleeve_2_mara_sol', 'sleeve_3_iron_quarry', 'sleeve_4_silo_nine', 'sleeve_5_pier_seven',
              'sleeve_6_dub_switch', 'sleeve_7_raymond_dean', 'sleeve_8_tone_wheel']
RAW_TAPE = ['tape_1_steel_harbor', 'tape_2_night_freight', 'tape_3_star_sector', 'tape_4_fist_foundry', 'tape_5_two_dogs', 'tape_6_summer_pier']
RAW_TITLE = [('ariblk.ttf', (255, 64, 160)), ('georgiaz.ttf', (255, 230, 150)), ('impact.ttf', (235, 235, 245)), ('bahnschrift.ttf', (15, 15, 15)),
             ('georgiaz.ttf', (255, 255, 255)), ('ariblk.ttf', (235, 228, 205)), ('georgiab.ttf', (250, 240, 220)), ('impact.ttf', (240, 250, 255))]


def raw_art(name):
    p = os.path.join(RAW, name + '.png')
    return Image.open(p).convert('RGB') if os.path.isfile(p) else None


def raw_sleeve(raw, k, a, t):
    """painted art of the image tool under the same words"""
    im = raw.resize((S, S))
    band = Image.new('L', (S, S), 0)
    ImageDraw.Draw(band).rectangle([0, 0, S, 160], fill=150)
    im = Image.composite(Image.new('RGB', (S, S), (10, 10, 12)), im, band.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(im)
    fn, col = RAW_TITLE[k]
    text_fit(d, (S // 2, 64), a, fn, 460, 84, fill=col, stroke=3, stroke_fill=(0, 0, 0))
    text_fit(d, (S // 2, 132), t, fn, 400, 40, fill=(240, 240, 240), stroke=2, stroke_fill=(0, 0, 0))
    return ringwear(grain(im, 6, 100 + k))


def cassette_rack(sleeves):
    """the face of a wall cassette rack: 5 rows of 6 cassettes face out (the eight albums' cassette editions), clear cases, a black rack"""
    k = 20.0
    W, H = int(24 * k), int(30 * k)
    im = Image.new('RGB', (W, H), (16, 16, 16))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for r in range(5):
        d.rectangle([0, int((r + 1) * 6 * k) - 8, W, int((r + 1) * 6 * k)], fill=(60, 60, 60))
        for c in range(6):
            if rnd.random() < 0.12:
                continue
            x, y = int((0.25 + c * 3.95) * k), int((0.5 + r * 6) * k)
            cw, ch = int(3.7 * k), int(5.0 * k)
            d.rectangle([x, y, x + cw, y + ch], fill=(200, 205, 210))
            art = sleeves[rnd.randrange(8)].resize((cw - 6, cw - 6))
            im.paste(art, (x + 3, y + 3))
            d.rectangle([x + 3, y + cw - 1, x + cw - 3, y + ch - 3], fill=(240, 235, 220))
    return grain(im, 4, 5)


def party_jcard():
    """the J-card of the party tape's empty case: hand lettered in the keeper's marker. Words: PARTY TAPE, CAR 6 (the door card's copy)"""
    w, h = 400, 260
    im = Image.new('RGB', (w, h), (250, 246, 236))
    d = ImageDraw.Draw(im)
    for y in range(80, h, 26):
        d.line([(20, y), (w - 20, y)], fill=(170, 190, 220), width=2)
    d.rectangle([0, 0, w, 50], fill=(240, 100, 20))
    text_fit(d, (w // 2, 120), 'PARTY TAPE', 'Inkfree.ttf', w - 60, 70, fill=(20, 20, 30), stroke=2, stroke_fill=(20, 20, 30))
    text_fit(d, (w // 2, 200), 'CAR 6', 'Inkfree.ttf', w - 160, 60, fill=(200, 40, 20), stroke=2, stroke_fill=(200, 40, 20))
    return grain(im, 4, 12)


def film_tape(logo):
    """the film's own rental box (FILM-LAYER item 7): the painted one-sheet on a black box front, the shop's sticker"""
    poster = Image.open(os.path.join(ART, 'poster_station_zero.png')).convert('RGB')
    im = Image.new('RGB', (TW, TH), (8, 8, 10))
    p = poster.resize((TW - 12, int((TW - 12) * 1024 / 683)))
    im.paste(p, (6, 6))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 6 + p.size[1] + 6, TW, TH], fill=(150, 20, 20))
    lg = logo.resize((58, 58))
    im.paste(lg, (TW - 70, TH - 70), lg)
    return grain(im, 4, 13)


# ------------------------------------------------------------------------------------------------ words, checked against the copy file
def words():
    c = json.load(open(COPY, encoding='utf-8'))
    return c


def main():
    os.makedirs(OUT, exist_ok=True)
    c = words()
    sl = c['needle_drop_sleeves']
    made = {}

    def save(name, im):
        p = os.path.join(OUT, name)
        im.save(p)
        made[name] = list(im.size)
    sleeves = []
    for k, fn in enumerate(SLEEVES):
        raw = raw_art(RAW_SLEEVE[k])
        im = raw_sleeve(raw, k, sl[k]['artist'], sl[k]['title']) if raw is not None else fn(sl[k]['artist'], sl[k]['title'])
        sleeves.append(im)
        save('nd_sleeve_%d.png' % (k + 1), im)
    logo = Image.open(os.path.join(ART, 'logo_needle_drop.png')).convert('RGBA')
    for k, fn in enumerate(TAPES):
        r = c['needle_drop_rental'][k]
        raw = raw_art(RAW_TAPE[k])
        save('nd_tape_%d.png' % (k + 1), tape_frame(raw if raw is not None else fn(), r['title'], r['genre'], logo=logo, **TAPE_STYLE[k]))
    save('nd_tape_station_zero.png', film_tape(logo))
    for k, (a, b) in enumerate(c['window_cards']['needle_drop']):
        save('nd_card_%d.png' % (k + 1), card([a, b], ink=[(20, 20, 20), (230, 80, 10)][k % 2], seed=20 + k))
    save('nd_rail_a.png', sleeve_sheet(sleeves, [0, 4, 2, 6]))
    save('nd_rail_b.png', sleeve_sheet(sleeves, [7, 1, 5, 3]))
    save('nd_rail_c.png', sleeve_sheet(sleeves, [3, 6, 0, 1], gaps=(2,)))
    save('nd_bin_tops.png', bin_tops(31))
    save('nd_spines.png', spines(37))
    save('nd_cassette_rack.png', cassette_rack(sleeves))
    save('nd_party_jcard.png', party_jcard())
    hk = c['heel_key_board']
    for k, t in enumerate(hk['claim_tags']):
        save('hk_tag_%d.png' % (k + 1), claim_tag(' '.join(t.split()), 40 + k))
    save('hk_tag_zero.png', claim_tag('0', 50, big=True))
    for k, (a, b) in enumerate(c['window_cards']['heel_key']):
        save('hk_card_%d.png' % (k + 1), card([a, b], ink=[(110, 20, 30), (30, 30, 30)][k % 2], paper=(240, 230, 205), seed=60 + k))
    save('hk_key_board.png', key_board())
    save('hk_laces_card.png', laces_card())
    json.dump({'made': made, 'words_from': COPY, 'raw_used': sorted(n for n in RAW_SLEEVE + RAW_TAPE if raw_art(n) is not None),
               'note': 'procedural (PIL) where raw_used does not name the art; image tool out of quota 27 Nov 2026'}, open(os.path.join(OUT, 'manifest_goods_a.json'), 'w'), indent=1)
    # contact sheet for the eye
    names = sorted(made)
    tw = 220
    rows = (len(names) + 5) // 6
    sheet = Image.new('RGB', (6 * tw, rows * (tw + 18)), (90, 90, 90))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(OUT, n)).convert('RGBA')
        im.thumbnail((tw - 8, tw - 8))
        x, y = (i % 6) * tw, (i // 6) * (tw + 18)
        sheet.paste(im, (x + 4, y + 16), im)
        d.text((x + 4, y + 2), n, fill=(255, 255, 0))
    sheet.save(os.path.join(OUT, 'contact_goods_a.jpg'), quality=88)
    print(json.dumps({'out': OUT, 'pictures': len(made)}, indent=1))


if __name__ == '__main__':
    main()
