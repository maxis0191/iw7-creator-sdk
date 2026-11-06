"""Map browser art of Station Zero from engine renders (no HUD, no weapon).

usage: make_art.py <hero frame> <second frame> <out dir> [map]
Writes (TGA, 32-bit):
  zmb_poster_<map>_c.tga   theater poster texture of the zombies map browser (portrait 512x768)
  zmb_poster_<map>_sg.tga  its flat specular/gloss map
  image_<map>.tga          map list image (the same poster, as the stock zombies rows use poster art)
  image_<map>_vote.tga     end-of-game map vote image (landscape 512x256)
and preview PNGs next to them.
"""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

hero, second, out = sys.argv[1:4]
mapname = sys.argv[4] if len(sys.argv) > 4 else 'cp_iwz'
os.makedirs(out, exist_ok=True)
FONTS = r'C:\Windows\Fonts'
title_font = lambda s: ImageFont.truetype(os.path.join(FONTS, 'impact.ttf'), s)
body_font = lambda s: ImageFont.truetype(os.path.join(FONTS, 'bahnschrift.ttf'), s)
NEON = (120, 255, 90)


def grade(im, shadows=(10, 24, 30), highlights=(255, 196, 120), contrast=1.35, brightness=1.15):
    """Teal shadows / amber highlights split tone with a little contrast (film poster look)."""
    im = ImageEnhance.Brightness(ImageEnhance.Contrast(im.convert('RGB')).enhance(contrast)).enhance(brightness)
    gray = ImageOps.grayscale(im)
    toned = ImageOps.colorize(gray, shadows, highlights)
    return Image.blend(im, toned, 0.55)


def glow_text(base, xy, text, font, fill, glow, radius=8, anchor='mm'):
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=glow + (255,), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(layer)
    base.alpha_composite(layer)
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill + (255,), anchor=anchor, stroke_width=2, stroke_fill=(10, 20, 10, 255))


def vignette(size, strength=0.85):
    w, h = size
    mask = Image.new('L', size, 0)
    d = ImageDraw.Draw(mask)
    for i in range(40):
        t = i / 40
        d.ellipse([-w * 0.35 + t * w * 0.25, -h * 0.25 + t * h * 0.18, w * 1.35 - t * w * 0.25, h * 1.25 - t * h * 0.18],
                  fill=int(255 * t))
    mask = mask.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new('RGBA', size, (0, 0, 0, int(255 * strength)))
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    out.paste(dark, (0, 0), ImageOps.invert(mask))
    return out


def cover(im, size):
    return ImageOps.fit(im.convert('RGB'), size, Image.LANCZOS, centering=(0.5, 0.45))


# poster 512x768
W, H = 512, 768
poster = Image.new('RGBA', (W, H), (6, 8, 10, 255))
art = grade(cover(Image.open(hero), (W, 560)))
poster.paste(art, (0, 110))
fade = Image.new('L', (W, 560), 0)
fd = ImageDraw.Draw(fade)
for y in range(560):
    a = 0
    if y < 90: a = int(255 * (1 - y / 90))
    if y > 380: a = int(255 * min(1, (y - 380) / 180))
    fd.line([(0, y), (W, y)], fill=a)
poster.paste(Image.new('RGBA', (W, 560), (6, 8, 10, 255)), (0, 110), fade)
poster.alpha_composite(vignette((W, H), 0.6))
glow_text(poster, (W // 2, 70), 'STATION', title_font(92), (235, 255, 225), NEON, 10)
glow_text(poster, (W // 2, 160), 'ZERO', title_font(118), NEON, NEON, 14)
d = ImageDraw.Draw(poster)
d.text((W // 2, 612), 'LAST TRAIN OUT.  NO RETURN TICKET.', font=body_font(22), fill=(230, 220, 200, 255), anchor='mm')
d.line([(70, 640), (W - 70, 640)], fill=(120, 255, 90, 200), width=2)
d.text((W // 2, 668), 'AN  ORIGINAL  INFINITE WARFARE ZOMBIES  CUSTOM MAP', font=body_font(14), fill=(170, 180, 170, 255), anchor='mm')
d.text((W // 2, 690), 'GENERATED  WORLD  \u2022  NAVMESH  \u2022  STOCK  ZOMBIES  SYSTEMS', font=body_font(12), fill=(130, 140, 130, 255), anchor='mm')
d.text((W // 2, 732), 'NOW  BOARDING', font=title_font(34), fill=(255, 70, 50, 255), anchor='mm')
d.rectangle([4, 4, W - 5, H - 5], outline=(40, 50, 40, 255), width=3)
poster_rgb = poster.convert('RGB')

# vote banner 512x256
VW, VH = 512, 256
vote = Image.new('RGBA', (VW, VH), (0, 0, 0, 255))
vote.paste(grade(cover(Image.open(second), (VW, VH))), (0, 0))
shade = Image.new('L', (VW, VH), 0)
sd = ImageDraw.Draw(shade)
for x in range(VW):
    sd.line([(x, 0), (x, VH)], fill=int(200 * max(0.0, 1 - x / (VW * 0.75))))
vote.paste(Image.new('RGBA', (VW, VH), (4, 6, 8, 255)), (0, 0), shade)
glow_text(vote, (24, 96), 'STATION ZERO', title_font(64), (235, 255, 225), NEON, 8, anchor='lm')
ImageDraw.Draw(vote).text((26, 150), 'Infinite Warfare Zombies custom map', font=body_font(20), fill=(220, 220, 210, 255), anchor='lm')
vote_rgb = vote.convert('RGB')


def tga(im, name):
    im.convert('RGBA').save(os.path.join(out, name + '.tga'))
    im.convert('RGB').save(os.path.join(out, name + '.preview.png'))


# the theater poster is a lit model in a dim cinema: its texture is brightened (the 2D list image is not)
tga(ImageEnhance.Brightness(poster_rgb).enhance(1.6), 'zmb_poster_%s_c' % mapname)
tga(poster_rgb, 'image_%s' % mapname)
tga(vote_rgb, 'image_%s_vote' % mapname)
sg = Image.new('RGBA', (64, 64), (14, 14, 14, 70))
sg.save(os.path.join(out, 'zmb_poster_%s_sg.tga' % mapname))
print('art written to', out)
