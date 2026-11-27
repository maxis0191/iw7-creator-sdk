r"""make_pictures_b: the pictures of the goods of COPY STOP and HOLE NUMBER NINE (worker A3b), drawn with PIL.

    python make_pictures_b.py [out folder]      (default C:\studio-data\sz\film\art\arcade\goods_b)

Words: only the copy file's (C:\studio-data\sz\film\copy\arcade_copy.json: window_cards, copy_stop_board notices, photo_booth) and canon
names. Two pictures carry words that are not copy yet: their file names hold PLACEHOLDER (the memo's stamp "COPY 1 OF 40", the bag ticket
"STRAND - TO COLLECT") and so does the toner label ("TONER", named by the brief). Marks are cropped from worker A1's light boxes, never redrawn.
`mat_*` pictures are world materials (B.material: sides a power of two); the others are sign or decal pictures.
The passport photographs of the booth are painted here (the image generator was out of quota on 27 Nov): four invented faces, no likeness.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ART = r'C:\studio-data\sz\film\art\arcade'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ART, 'goods_b')
COPY = json.load(open(r'C:\studio-data\sz\film\copy\arcade_copy.json', encoding='utf-8'))
FONTS = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')

PROCESS_BLUE = (0, 104, 180)
AMBER = (247, 168, 0)
PINK = (238, 150, 186)
CHOC = (84, 46, 30)
MADE = []


def font(name, px, variation=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), int(px))
    if variation:
        f.set_variation_by_name(variation)
    return f


def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p)
    MADE.append((name, im.size))
    return p


def paper(w, h, base=(244, 241, 230), grain=10, seed=1):
    rnd = random.Random(seed)
    im = Image.new('RGB', (w, h), base)
    px = im.load()
    for _ in range(w * h // 6):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d = rnd.randint(-grain, grain)
        r, g, b = px[x, y]
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    return im.filter(ImageFilter.GaussianBlur(0.6))


def tape(d, box, alpha_col=(236, 224, 170)):
    d.rectangle(box, fill=alpha_col)


def centred(d, text, cx, y, f, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def fit_font(d, text, name, max_w, start, variation=None):
    px = start
    while px > 8:
        f = font(name, px, variation)
        if d.textlength(text, font=f) <= max_w:
            return f
        px -= 2
    return font(name, 8, variation)


def jitter_text(im, text, cx, y, f, fill, seed, amp=1.5, rot=2.0):
    """hand lettering: each glyph drawn on its own with a small offset and tilt"""
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    total = d.textlength(text, font=f)
    x = cx - total / 2
    for ch in text:
        w = d.textlength(ch, font=f)
        if ch != ' ':
            g = Image.new('RGBA', (int(w + f.size), int(f.size * 1.6)), (0, 0, 0, 0))
            ImageDraw.Draw(g).text((f.size / 2, f.size * 0.2), ch, font=f, fill=fill + (255,))
            g = g.rotate(rnd.uniform(-rot, rot), resample=Image.BICUBIC)
            im.paste(g, (int(x - f.size / 2 + rnd.uniform(-amp, amp)), int(y - f.size * 0.2 + rnd.uniform(-amp, amp))), g)
        x += w


def typed_bars(d, x0, y0, x1, y1, line=11, ink=(70, 70, 76), seed=3, para=5):
    """typewriter texture: rows of short grey dashes of word lengths, no letters (unreadable at any distance)"""
    rnd = random.Random(seed)
    y = y0
    n = 0
    while y < y1:
        n += 1
        if n % para == 0:
            y += line
            continue
        x = x0 + (18 if n % para == 1 else 0)
        end = x1 - (rnd.uniform(0, (x1 - x0) * 0.5) if n % para == para - 1 else rnd.uniform(0, 12))
        while x < end:
            wl = rnd.randint(2, 9) * 5.2
            if x + wl > end:
                break
            dv = rnd.randint(-18, 18)
            shade = tuple(max(0, c + dv) for c in ink)
            d.rectangle([x, y + 2, x + wl, y + line * 0.55], fill=shade)
            x += wl + 5
        y += line


# ------------------------------------------------------------------------------------------------ marks cropped from A1's light boxes
def lodestar_mark():
    im = Image.open(os.path.join(ART, 'lightbox_lodestar.png')).convert('RGB').crop((77, 44, 597, 499))
    return im


def zero_roundel():
    """the roundel only: a circular cut of the light box's top (its words below are left out), outside filled with the amber"""
    im = Image.open(os.path.join(ART, 'lightbox_zero_line.png')).convert('RGB').crop((80, 26, 598, 605))
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 8, im.size[0] - 1, im.size[1] - 40], fill=255)
    return Image.composite(im, Image.new('RGB', im.size, AMBER), mask)


# ------------------------------------------------------------------------------------------------ COPY STOP
def cs_cards():
    """Ines Varga's window cards: draughtsman's upright capitals in process-blue felt pen on white card, taped to the glass"""
    for k, (a, b) in enumerate(COPY['window_cards']['copy_stop']):
        im = paper(512, 320, (250, 250, 246), 6, seed=10 + k)
        d = ImageDraw.Draw(im)
        d.rectangle([6, 6, 505, 313], outline=(210, 214, 222), width=2)
        for y in (128, 236):
            d.line([(40, y), (472, y)], fill=(196, 210, 232), width=2)       # the pencil guide lines she lettered on
        f1 = fit_font(d, a, 'bahnschrift.ttf', 440, 92, 'SemiBold Condensed')
        f2 = fit_font(d, b, 'bahnschrift.ttf', 440, 64, 'Condensed')
        jitter_text(im, a, 256, 128 - f1.size * 1.0, f1, PROCESS_BLUE, 20 + k, 1.2, 1.5)
        jitter_text(im, b, 256, 236 - f2.size * 1.0, f2, (30, 60, 120), 40 + k, 1.2, 1.5)
        d = ImageDraw.Draw(im)
        tape(d, [220, 0, 292, 22])
        save(im, 'cs_card_%d.png' % (k + 1))


def cs_notices():
    for key, nm in ((0, 'cs_notice_drafting.png'), (1, 'cs_notice_paper_tray.png')):
        n = COPY['copy_stop_board']['notices'][key]
        im = paper(384, 512, (246, 243, 232), 8, seed=60 + key)
        d = ImageDraw.Draw(im)
        ft = font('courbd.ttf', 40)
        centred(d, n['title'], 192, 70, ft, (25, 25, 30))
        d.line([(60, 124), (324, 124)], fill=(40, 40, 40), width=3)
        fl = fit_font(d, max(n['lines'], key=len), 'courbd.ttf', 300, 30)
        for i, line in enumerate(n['lines']):
            d.text((42, 160 + i * (fl.size + 18)), line, font=fl, fill=(30, 30, 36))
        d.ellipse([178, 14, 206, 42], fill=(200, 30, 30))                       # the push pin
        d.ellipse([186, 20, 196, 30], fill=(250, 120, 120))
        save(im, nm)


def cs_booth():
    band = Image.new('RGB', (1024, 192), (246, 248, 252))
    d = ImageDraw.Draw(band)
    t = COPY['photo_booth'][0]
    f = fit_font(d, t, 'bahnschrift.ttf', 960, 150, 'Bold Condensed')
    centred(d, t, 512, (192 - f.size) / 2 - 12, f, PROCESS_BLUE)
    save(band, 'cs_booth_band.png')
    plate = Image.new('RGB', (512, 160), PROCESS_BLUE)
    d = ImageDraw.Draw(plate)
    f1 = fit_font(d, COPY['photo_booth'][1], 'bahnschrift.ttf', 470, 64, 'Bold Condensed')
    f2 = fit_font(d, COPY['photo_booth'][2], 'bahnschrift.ttf', 400, 44, 'SemiBold Condensed')
    centred(d, COPY['photo_booth'][1], 256, 14, f1, (250, 250, 250))
    centred(d, COPY['photo_booth'][2], 236, 98, f2, (250, 250, 250))
    w2 = d.textlength(COPY['photo_booth'][2], font=f2)
    cx = 236 + w2 / 2 + 26
    d.ellipse([cx - 14, 104, cx + 14, 132], fill=(60, 220, 90), outline=(240, 240, 240), width=3)
    save(plate, 'cs_booth_plate.png')


FACES = [   # (skin, hair, hair style, clothing, glasses, backdrop)
    ((226, 186, 160), (178, 176, 172), 'perm', (120, 84, 110), False, (120, 132, 150)),
    ((214, 166, 132), (70, 46, 30), 'short_moustache', (122, 86, 52), False, (116, 128, 146)),
    ((222, 178, 146), (36, 28, 24), 'curly', (70, 96, 140), False, (124, 136, 152)),
    ((230, 190, 166), (138, 64, 36), 'shoulder', (236, 232, 220), True, (118, 130, 148)),
]


def face(spec, seed, s=256):
    """a painted photo-booth portrait: flat flash light, curtain backdrop, head and shoulders, soft focus"""
    skin, hair, style, cloth, glasses, back = spec
    rnd = random.Random(seed)
    im = Image.new('RGB', (s, s), back)
    d = ImageDraw.Draw(im)
    for x in range(0, s, 18):                                             # curtain folds
        d.rectangle([x, 0, x + 8, s], fill=tuple(c - 10 for c in back))
    cx = s / 2 + rnd.uniform(-6, 6)
    d.ellipse([cx - 112, 196, cx + 112, 330], fill=cloth)                  # shoulders
    if style == 'shoulder':
        d.polygon([(cx - 30, 206), (cx, 250), (cx + 30, 206)], fill=(214, 206, 192))   # blouse collar
    d.rectangle([cx - 22, 160, cx + 22, 214], fill=tuple(int(c * 0.9) for c in skin))   # neck
    if style in ('perm', 'curly', 'shoulder'):
        hb = {'perm': [cx - 70, 26, cx + 70, 150], 'curly': [cx - 66, 22, cx + 66, 140], 'shoulder': [cx - 72, 34, cx + 72, 214]}[style]
        d.ellipse(hb, fill=hair)
        if style in ('perm', 'curly'):
            for _ in range(60):
                a = rnd.uniform(math.pi * 0.95, math.pi * 2.05)
                r = rnd.uniform(52, 66)
                x, y = cx + r * math.cos(a), 92 + r * 0.95 * math.sin(a)
                d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=tuple(c + rnd.randint(-12, 12) for c in hair))
    d.ellipse([cx - 50, 52, cx + 50, 182], fill=skin)                      # face
    if style == 'short_moustache':
        d.chord([cx - 54, 40, cx + 54, 120], 180, 360, fill=hair)
        d.rectangle([cx - 54, 72, cx - 44, 104], fill=hair)
        d.rectangle([cx + 44, 72, cx + 54, 104], fill=hair)
        d.polygon([(cx - 22, 142), (cx + 22, 142), (cx + 16, 150), (cx - 16, 150)], fill=hair)
    if style == 'shoulder':
        d.chord([cx - 56, 44, cx + 56, 124], 180, 360, fill=hair)
    for ex in (-20, 20):                                                    # eyes, brows
        d.ellipse([cx + ex - 7, 104, cx + ex + 7, 113], fill=(250, 248, 244))
        d.ellipse([cx + ex - 4, 105, cx + ex + 4, 113], fill=(60, 48, 40))
        d.line([(cx + ex - 10, 96), (cx + ex + 10, 95)], fill=tuple(int(c * 0.7) for c in hair) if style != 'perm' else (120, 110, 100), width=3)
    if glasses:
        for ex in (-20, 20):
            d.rounded_rectangle([cx + ex - 17, 96, cx + ex + 17, 124], 6, outline=(60, 40, 30), width=3)
        d.line([(cx - 3, 108), (cx + 3, 108)], fill=(60, 40, 30), width=3)
    d.line([(cx, 112), (cx - 4, 134), (cx + 4, 136)], fill=tuple(int(c * 0.82) for c in skin), width=3)     # nose
    mouth = {'perm': 'smile', 'short_moustache': 'flat', 'curly': 'half', 'shoulder': 'flat'}[style]
    if mouth == 'smile':
        d.arc([cx - 16, 140, cx + 16, 158], 20, 160, fill=(150, 70, 70), width=3)
    elif mouth == 'half':
        d.line([(cx - 14, 152), (cx + 10, 150), (cx + 16, 146)], fill=(150, 76, 72), width=3)
    else:
        d.line([(cx - 13, 153), (cx + 13, 153)], fill=(150, 80, 76), width=3)
    im = im.filter(ImageFilter.GaussianBlur(2.2))                           # booth lens, chemical print
    warm = Image.new('RGB', im.size, (255, 226, 190))
    im = Image.blend(im, warm, 0.10)
    g = paper(s, s, (128, 128, 128), 22, seed=seed + 99)
    return Image.blend(im, g.convert('RGB'), 0.06)


def cs_strip():
    """the sample strip in its frame on the booth: one strip of four frames on a white card, the shop's mark at the head"""
    card = paper(512, 512, (240, 240, 236), 5, seed=77)
    d = ImageDraw.Draw(card)
    sx0, sw, fh = 186, 140, 102
    d.rectangle([sx0 - 8, 52, sx0 + sw + 8, 52 + 4 * (fh + 8) + 8], fill=(252, 252, 250))
    for k, spec in enumerate(FACES):
        f = face(spec, 500 + k).resize((sw, fh))
        card.paste(f, (sx0, 60 + k * (fh + 8)))
    logo = Image.open(os.path.join(ART, 'logo_copy_stop.png')).convert('RGBA').resize((56, 56))
    for k in range(2):
        card.paste(logo, (40 + k * 376, 40), logo)
    d.rectangle([2, 2, 509, 509], outline=(180, 186, 196), width=4)
    save(card, 'cs_booth_strip.png')


def cs_memo():
    """the top sheet of the forty-copy job (FILM-LAYER 5: Dr. Strand's 1983 memo). Its words are not ours: the body is typewriter
    texture only. Readable: the LODESTAR letterhead mark and a red rubber stamp COPY 1 OF 40 (PLACEHOLDER words)."""
    W, H = 680, 880                                                          # 8.5 x 11 at 80 px a unit, then squeezed to 512 x 512
    im = paper(W, H, (247, 246, 240), 7, seed=5)
    d = ImageDraw.Draw(im)
    mk = lodestar_mark().resize((118, 103))
    im.paste(mk, (52, 40))
    d.rectangle([190, 66, 620, 72], fill=(30, 40, 80))                       # letterhead rule
    d.rectangle([190, 84, 470, 92], fill=(150, 150, 160))
    d.rectangle([190, 100, 400, 107], fill=(150, 150, 160))
    for y in (180, 202, 224, 246):                                           # the memo heading block: bars, not words
        d.rectangle([70, y, 136, y + 10], fill=(60, 60, 66))
        d.rectangle([160, y, 160 + random.Random(y).randint(150, 330), y + 10], fill=(80, 80, 88))
    d.rectangle([60, 276, 620, 279], fill=(60, 60, 66))
    typed_bars(d, 70, 300, 610, 800, line=17, seed=8, para=6)
    st = Image.new('RGBA', (360, 120), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle([6, 6, 354, 114], outline=(196, 26, 34, 230), width=7)
    fs = fit_font(sd, 'COPY 1 OF 40', 'courbd.ttf', 320, 64)
    centred(sd, 'COPY 1 OF 40', 180, 28, fs, (196, 26, 34, 230))
    st = st.rotate(9, expand=True, resample=Image.BICUBIC)
    im.paste(st, (300, 600), st)
    im = im.resize((512, 512), Image.LANCZOS)
    save(im, 'mat_cs_memo_PLACEHOLDER.png')


def cs_programme():
    """the inauguration programme she printed: the Zero Line roundel (black 0 on signal amber) and 047 (canon). Face 6 x 9."""
    W, H = 600, 900
    im = Image.new('RGB', (W, H), AMBER)
    r = zero_roundel().resize((400, 446))
    im.paste(r, (100, 90))
    d = ImageDraw.Draw(im)
    f = font('bahnschrift.ttf', 230, 'Bold Condensed')
    centred(d, '047', 300, 560, f, (12, 10, 10))
    d.rectangle([0, 0, W - 1, H - 1], outline=(200, 130, 0), width=6)
    im = im.resize((512, 512), Image.LANCZOS)
    save(im, 'mat_cs_programme.png')


def cs_copy_page():
    im = paper(256, 330, (248, 248, 246), 5, seed=9)
    d = ImageDraw.Draw(im)
    d.rectangle([24, 24, 120, 34], fill=(70, 70, 74))
    typed_bars(d, 24, 52, 232, 300, line=9, seed=12, para=5)
    save(im, 'cs_copy_page.png')


def cs_blueprint():
    """a diazo print, white line on blue: a station cross-section (platform, track, vault, escalator), a grid and a title block without words"""
    W, H = 1024, 512
    im = Image.new('RGB', (W, H), (26, 64, 140))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 32):
        d.line([(x, 0), (x, H)], fill=(40, 82, 158))
    for y in range(0, H, 32):
        d.line([(0, y), (W, y)], fill=(40, 82, 158))
    ln = (226, 236, 250)
    d.arc([120, 60, 620, 520], 180, 360, fill=ln, width=4)                    # the vault of the platform hall
    d.line([(120, 290), (620, 290)], fill=ln, width=3)
    d.rectangle([160, 330, 300, 350], outline=ln, width=3)                     # platform edges
    d.rectangle([440, 330, 580, 350], outline=ln, width=3)
    d.line([(300, 380), (440, 380)], fill=ln, width=3)                         # track bed
    for x in range(305, 440, 14):
        d.line([(x, 376), (x, 386)], fill=ln, width=2)
    d.line([(620, 340), (860, 120)], fill=ln, width=4)                         # the escalator up to the hall
    d.line([(640, 360), (880, 140)], fill=ln, width=2)
    for k in range(10):
        t = k / 9
        d.line([(620 + 240 * t, 340 - 220 * t), (640 + 240 * t, 360 - 220 * t)], fill=ln, width=1)
    d.line([(860, 120), (1000, 120)], fill=ln, width=3)
    for x0 in (160, 440):                                                      # dimension lines
        d.line([(x0, 420), (x0 + 140, 420)], fill=ln, width=2)
        d.polygon([(x0, 420), (x0 + 10, 415), (x0 + 10, 425)], fill=ln)
        d.polygon([(x0 + 140, 420), (x0 + 130, 415), (x0 + 130, 425)], fill=ln)
    d.rectangle([760, 400, 1004, 496], outline=ln, width=3)                    # title block: boxes and ruled lines only
    for y in (424, 448, 472):
        d.line([(760, y), (1004, y)], fill=ln, width=1)
    d.line([(880, 400), (880, 496)], fill=ln, width=1)
    d.rectangle([8, 8, W - 9, H - 9], outline=ln, width=3)
    im = im.filter(ImageFilter.GaussianBlur(0.7))
    save(im, 'cs_blueprint_sheet.png')


def cs_vellum():
    """the drawing on her light table: pencil on vellum, the elevation of a row of four shopfronts (this underpass), unfinished"""
    W, H = 1024, 768
    im = paper(W, H, (236, 232, 214), 6, seed=31)
    d = ImageDraw.Draw(im)
    pen = (92, 92, 100)
    d.line([(60, 600), (964, 600)], fill=pen, width=3)
    for k in range(4):
        x0 = 80 + k * 220
        d.rectangle([x0, 280, x0 + 200, 600], outline=pen, width=2)            # a front
        d.rectangle([x0, 240, x0 + 200, 280], outline=pen, width=2)            # its fascia
        d.line([(x0 + 70, 300), (x0 + 70, 600)], fill=pen, width=1)
        if k < 3:
            d.rectangle([x0 + 90, 320, x0 + 190, 560], outline=(130, 130, 140), width=1)
    for x in range(80, 960, 22):                                               # floor tile hatching, half done
        if x < 600:
            d.line([(x, 600), (x + 30, 640)], fill=(150, 150, 156), width=1)
    d.line([(80, 200), (900, 200)], fill=(170, 170, 176), width=1)            # construction lines
    d.line([(80, 690), (900, 690)], fill=(170, 170, 176), width=1)
    d.rectangle([760, 660, 980, 740], outline=pen, width=2)
    d.rectangle([10, 10, W - 11, H - 11], outline=(200, 196, 176), width=4)
    save(im, 'cs_vellum_drawing.png')


def cs_tickets():
    for k, (col, ink) in enumerate((((252, 250, 240), (40, 60, 150)), ((250, 236, 150), (170, 30, 30)))):
        im = Image.new('RGB', (256, 160), col)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 255, 26], fill=PROCESS_BLUE)
        for y in (52, 82, 112, 142):
            d.line([(14, y), (242, y)], fill=(150, 160, 180), width=2)
        rnd = random.Random(70 + k)
        for y in (46, 76, 106):                                                # her scribbled job notes: strokes, no words
            x = 20
            while x < rnd.randint(140, 220):
                w = rnd.randint(10, 34)
                d.line([(x, y), (x + w * 0.3, y - 8), (x + w * 0.6, y), (x + w, y - 6)], fill=ink, width=3)
                x += w + 8
        d.ellipse([196, 4, 216, 22], fill=(250, 250, 250))
        save(im, 'cs_ticket_%s.png' % 'ab'[k])


def mat_ream():
    """a ream wrapper: white kraft with a process-blue band, no words (the faces of a ream box are fitted to this picture)"""
    im = paper(256, 256, (240, 238, 228), 10, seed=41)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 96, 255, 160], fill=(30, 90, 170))
    d.rectangle([0, 104, 255, 108], fill=(240, 238, 228))
    d.rectangle([0, 148, 255, 152], fill=(240, 238, 228))
    for x in (0, 254):
        d.line([(x, 0), (x, 255)], fill=(205, 200, 190), width=2)
    save(im, 'mat_cs_ream.png')


def mat_ream_colours():
    """reams of coloured paper (the pastel stock of a copy shop): the wrapper in the paper's colour, a white band, no words"""
    for nm, col in (('yellow', (246, 222, 110)), ('pink', (242, 170, 170)), ('green', (160, 214, 150))):
        im = paper(256, 256, col, 10, seed=len(nm) * 7 + col[0])
        d = ImageDraw.Draw(im)
        d.rectangle([0, 104, 255, 152], fill=(246, 244, 236))
        d.rectangle([0, 120, 255, 136], fill=tuple(int(c * 0.8) for c in col))
        save(im, 'mat_cs_ream_%s.png' % nm)


def mat_paper_edge():
    """the edge of a stack of paper: fine off-white lines, slightly uneven (tiles)"""
    rnd = random.Random(42)
    im = Image.new('RGB', (256, 256), (244, 243, 236))
    d = ImageDraw.Draw(im)
    for y in range(0, 256, 2):
        c = 236 - rnd.randint(0, 22)
        d.line([(0, y), (255, y)], fill=(c, c, c - 6))
    save(im.filter(ImageFilter.GaussianBlur(0.4)), 'mat_cs_paper_edge.png')


def mat_envelope():
    im = paper(256, 256, (214, 182, 120), 10, seed=43)                        # manila
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (128, 90), (256, 0)], outline=(170, 140, 90))
    d.line([(0, 0), (128, 90), (255, 0)], fill=(176, 146, 94), width=3)
    d.rectangle([150, 160, 236, 236], fill=(250, 248, 240))                    # the job ticket pasted on
    d.rectangle([150, 160, 236, 172], fill=PROCESS_BLUE)
    save(im, 'mat_cs_envelope.png')


def cs_toner():
    im = Image.new('RGB', (512, 128), (24, 24, 26))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 30, 511, 98], fill=(236, 236, 232))
    f = font('bahnschrift.ttf', 56, 'Bold')
    centred(d, 'TONER', 256, 34, f, (20, 20, 22))
    save(im, 'cs_toner_PLACEHOLDER.png')


# ------------------------------------------------------------------------------------------------ HOLE NUMBER NINE
def h9_cards():
    """Dolores Kemp's cards: red marker on pink ruled card, as her door card"""
    for k, (a, b) in enumerate(COPY['window_cards']['hole_nine']):
        im = paper(512, 320, (246, 196, 206), 8, seed=80 + k)
        d = ImageDraw.Draw(im)
        for y in range(70, 320, 40):
            d.line([(0, y), (511, y)], fill=(160, 170, 220), width=2)
        d.line([(60, 0), (60, 319)], fill=(220, 90, 90), width=2)
        f1 = fit_font(d, a, 'segoeprb.ttf', 430, 70)
        f2 = fit_font(d, b, 'segoeprb.ttf', 430, 56)
        jitter_text(im, a, 270, 60, f1, (200, 20, 40), 90 + k, 1.6, 2.5)
        jitter_text(im, b, 270, 170, f2, (200, 20, 40), 95 + k, 1.6, 2.5)
        d = ImageDraw.Draw(im)
        tape(d, [20, 0, 90, 20])
        tape(d, [420, 0, 492, 20])
        save(im, 'h9_card_%d.png' % (k + 1))


def mat_glaze(name, glaze, dough=(196, 140, 84), sprinkles=None, seed=0):
    """a doughnut's surface as the authored ring maps it: v 0..0.5 (the bottom half of the picture) is the top of the ring (the glaze),
    v 0.5..1 the underside (the fried dough); u goes four times round"""
    rnd = random.Random(seed)
    im = Image.new('RGB', (256, 256), dough)
    d = ImageDraw.Draw(im)
    for _ in range(400):
        x, y = rnd.randrange(256), rnd.randrange(0, 128)
        c = tuple(max(0, v + rnd.randint(-20, 10)) for v in dough)
        d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=c)
    d.rectangle([0, 128, 255, 255], fill=glaze)
    for x in range(0, 256, 4):                                                  # the drip line of the glaze
        d.rectangle([x, 120 + rnd.randint(0, 7), x + 4, 128], fill=glaze)
    for _ in range(300):
        x, y = rnd.randrange(256), rnd.randrange(130, 256)
        c = tuple(min(255, v + rnd.randint(0, 24)) for v in glaze)
        d.point((x, y), fill=c)
    if sprinkles:
        for _ in range(220):
            x, y = rnd.randrange(256), rnd.randrange(136, 250)
            a = rnd.uniform(0, math.pi)
            d.line([(x, y), (x + 5 * math.cos(a), y + 5 * math.sin(a))], fill=rnd.choice(sprinkles), width=2)
    save(im.filter(ImageFilter.GaussianBlur(0.5)), name)


def h9_tv():
    """Channel 9's card on the screen: the top of A1's light box, with scan lines and a dark curved edge"""
    im = Image.open(os.path.join(ART, 'lightbox_channel9.png')).convert('RGB').crop((0, 30, 683, 542)).resize((512, 384), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for y in range(0, 384, 3):
        d.line([(0, y), (511, y)], fill=(0, 0, 0), width=1)
    im = Image.blend(Image.open(os.path.join(ART, 'lightbox_channel9.png')).convert('RGB').crop((0, 30, 683, 542)).resize((512, 384)), im, 0.35)
    mask = Image.new('L', (512, 384), 0)
    ImageDraw.Draw(mask).rounded_rectangle([10, 8, 502, 376], 48, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(14))
    out = Image.composite(im, Image.new('RGB', (512, 384), (6, 8, 12)), mask)
    save(out, 'h9_tv_screen.png')


def mat_box():
    """a Hole Number Nine box: pink board, the 9 in a white roundel, brown edge lines (fitted to each face of a box)"""
    im = paper(256, 256, PINK, 8, seed=50)
    d = ImageDraw.Draw(im)
    d.ellipse([64, 64, 192, 192], fill=(250, 244, 236))
    logo = Image.open(os.path.join(ART, 'logo_hole_nine.png')).convert('RGBA').resize((112, 112))
    im.paste(logo, (72, 72), logo)
    d.rectangle([3, 3, 252, 252], outline=CHOC, width=5)
    save(im, 'mat_h9_box.png')


def mat_bag():
    """a kraft bag with the shop's sticker"""
    im = paper(256, 256, (178, 136, 92), 14, seed=51)
    d = ImageDraw.Draw(im)
    for x in range(0, 256, 38):
        d.line([(x, 0), (x, 255)], fill=(160, 120, 80), width=2)
    d.ellipse([70, 80, 186, 196], fill=PINK)
    logo = Image.open(os.path.join(ART, 'logo_hole_nine.png')).convert('RGBA').resize((96, 96))
    im.paste(logo, (80, 90), logo)
    save(im, 'mat_h9_bag.png')


def mat_ticket():
    """the order ticket on the bagged order: an order-pad slip, hand-written STRAND - TO COLLECT (PLACEHOLDER words). Face 4 x 6."""
    W, H = 400, 600
    im = paper(W, H, (252, 250, 238), 6, seed=52)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 60], fill=PINK)
    logo = Image.open(os.path.join(ART, 'logo_hole_nine.png')).convert('RGBA').resize((52, 52))
    im.paste(logo, (174, 4), logo)
    for y in range(120, H, 54):
        d.line([(16, y), (W - 16, y)], fill=(150, 170, 220), width=2)
    f = font('segoeprb.ttf', 66)
    jitter_text(im, 'STRAND', W / 2, 140, f, (30, 30, 120), 7, 1.5, 3)
    f2 = font('segoeprb.ttf', 40)
    jitter_text(im, '- TO COLLECT', W / 2, 250, f2, (30, 30, 120), 8, 1.5, 3)
    d = ImageDraw.Draw(im)
    d.line([(60, 360), (340, 352)], fill=(30, 30, 120), width=4)
    im = im.resize((256, 512), Image.LANCZOS)
    save(im, 'mat_h9_ticket_PLACEHOLDER.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    cs_cards()
    cs_notices()
    cs_booth()
    cs_strip()
    cs_memo()
    cs_programme()
    cs_copy_page()
    cs_blueprint()
    cs_vellum()
    cs_tickets()
    mat_ream()
    mat_paper_edge()
    mat_ream_colours()
    mat_envelope()
    cs_toner()
    h9_cards()
    mat_glaze('mat_h9_glaze_pink.png', (238, 128, 170), sprinkles=[(250, 250, 250), (90, 200, 220), (250, 220, 70), (120, 70, 40)], seed=1)
    mat_glaze('mat_h9_glaze_honey.png', (244, 214, 150), dough=(176, 112, 60), seed=2)
    h9_tv()
    mat_box()
    mat_bag()
    mat_ticket()
    man = [{'file': n, 'px': list(s), 'placeholder_words': 'PLACEHOLDER' in n or n == 'cs_toner_PLACEHOLDER.png'} for n, s in MADE]
    json.dump(man, open(os.path.join(OUT, 'manifest_goods_b.json'), 'w', encoding='utf-8'), indent=1)
    print(json.dumps({'out': OUT, 'pictures': len(MADE), 'copy_stop': sum(1 for n, _ in MADE if n.startswith(('cs_', 'mat_cs_'))),
                      'hole_nine': sum(1 for n, _ in MADE if n.startswith(('h9_', 'mat_h9_')))}))


if __name__ == '__main__':
    main()
