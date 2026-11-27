"""standins: the picture slots of the Arcade shell and their stand-ins.

A slot names a file of worker A1 under ART. When the file is there it is used as it is; when it is not, a plain stand-in of the same
pixel ratio (flat brand colour, the file name in small type) is drawn into STANDIN and used instead, and the slot is listed as a stand-in.
The swap to the real art is automatic at the next build. A stand-in is never the art.
"""
import os

ART = r'C:\studio-data\sz\film\art\arcade'
STANDIN = r'C:\studio-data\sz\film\arcade\shell\standin'

# file -> (width, height in units, background rgb, ink rgb, alpha)
SLOTS = {
    'fascia_needle_drop.png': (300, 68, (18, 16, 16), (255, 110, 20), 255),
    'fascia_copy_stop.png': (310, 68, (0, 104, 180), (245, 245, 245), 255),
    'fascia_copy_stop_left.png': (150, 68, (0, 104, 180), (245, 245, 245), 255),
    'fascia_copy_stop_right.png': (150, 68, (0, 104, 180), (245, 245, 245), 255),
    'fascia_hole_nine.png': (300, 68, (236, 140, 178), (92, 52, 30), 255),
    'fascia_heel_key.png': (300, 68, (110, 22, 30), (240, 228, 200), 255),
    'directory_board.png': (120, 160, (236, 228, 206), (40, 36, 32), 255),
    'lightbox_orbit.png': (64, 96, (120, 60, 170), (250, 240, 120), 255),
    'lightbox_lodestar.png': (64, 96, (20, 34, 80), (230, 190, 80), 255),
    'lightbox_zero_line.png': (64, 96, (200, 40, 36), (250, 250, 250), 255),
    'lightbox_channel9.png': (64, 96, (20, 140, 150), (250, 250, 250), 255),
    'door_card_needle_drop.png': (10, 7, (250, 248, 240), (30, 30, 30), 255),
    'door_card_copy_stop.png': (10, 7, (250, 248, 240), (30, 30, 30), 255),
    'door_card_hole_nine.png': (10, 7, (250, 248, 240), (30, 30, 30), 255),
    'door_card_heel_key.png': (10, 7, (250, 248, 240), (30, 30, 30), 255),
    'notice_1.png': (16, 22, (240, 236, 220), (40, 40, 40), 255),
    'notice_2.png': (16, 22, (250, 240, 200), (40, 40, 40), 255),
    'notice_3.png': (16, 22, (230, 236, 240), (40, 40, 40), 255),
    'notice_4.png': (16, 22, (245, 225, 215), (40, 40, 40), 255),
    'banner_new_year.png': (320, 48, (240, 232, 210), (190, 40, 50), 255),
    'bunting_strip.png': (256, 24, (210, 60, 60), (40, 70, 160), 255),
    'floor_polish_circle.png': (220, 220, (120, 80, 50), (60, 40, 25), 90),
    'poster_station_zero.png': (64, 96, (30, 30, 40), (220, 200, 160), 255),
}


def _draw(path, name, w, h, bg, ink, alpha):
    from PIL import Image, ImageDraw, ImageFont
    k = 1024.0 / max(w, h) if max(w, h) * 8 > 1024 else 8.0
    pw, ph = max(16, int(round(w * k))), max(16, int(round(h * k)))
    im = Image.new('RGBA', (pw, ph), bg + (alpha,))
    d = ImageDraw.Draw(im)
    if name == 'floor_polish_circle.png':             # a soft disc: the stand-in of a floor decal is round, its corners clear
        im = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([4, 4, pw - 4, ph - 4], fill=bg + (alpha,))
    try:
        f = ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'consola.ttf'), max(8, ph // 10))
    except OSError:
        f = ImageFont.load_default()
    d.text((max(2, pw // 40), max(2, ph // 40)), 'STAND-IN ' + name, fill=ink + (255,), font=f)
    d.rectangle([0, 0, pw - 1, ph - 1], outline=ink + (255,), width=max(1, ph // 60))
    im.save(path)


def slot(name):
    """-> (path, is_standin) for the file `name` of a slot"""
    real = os.path.join(ART, name)
    if os.path.isfile(real):
        return real, False
    w, h, bg, ink, alpha = SLOTS[name]
    os.makedirs(STANDIN, exist_ok=True)
    p = os.path.join(STANDIN, name)
    if not os.path.isfile(p):
        _draw(p, name, w, h, bg, ink, alpha)
    return p, True
