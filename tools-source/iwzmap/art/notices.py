"""Paper notices and printed posters of Station Zero: torn layered CLOSED notices, the evacuation/quarantine order,
the generator lock-out notice with the night-shift roster, missing-person flyers, the cracked lit ad panel and the
second film poster. Every word is typeset from a font (exact spelling); photos/illustrations come from reviewed
image files passed in by the caller (art/imagegen in the stage folder).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

from . import boards as B
from . import masks as M
from . import noise as N
from . import paper as P

INK = (0.10, 0.10, 0.11)
RED_INK = (0.74, 0.12, 0.10)
NAVY_INK = (0.12, 0.18, 0.36)
STAMP_RED = (0.70, 0.10, 0.12)


def _rgb(c):
    return tuple(np.array(c, np.float32))


def scribble(doc, x, y, w, seed, colour=(0.12, 0.14, 0.32), h=12):
    """A ballpoint signature: a big looped initial, then a smoothed random walk of letter-like humps with varying
    height and slant, and a trailing underline flick."""
    r = np.random.default_rng(seed)
    ctrl = [(x, y + h * 0.6), (x + h * 0.2, y - h * 0.9), (x + h * 0.55, y - h * 0.2), (x + h * 0.1, y + h * 0.5)]
    cx = x + h * 0.5
    while cx < x + w:
        cx += r.uniform(0.25, 0.7) * h
        ctrl.append((cx, y + r.uniform(-0.9, 0.5) * h * (0.4 if r.random() < 0.6 else 1.0)))
    pts = []
    for i in range(1, len(ctrl) - 2):                      # Catmull-Rom through the control points
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2]
        for t in np.linspace(0, 1, 8, endpoint=False):
            t2, t3 = t * t, t * t * t
            pts.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                    (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    slant = 0.25
    pts = [(px + (y - py) * slant, py) for px, py in pts]
    doc.line(pts, colour, width=0.9)
    doc.line([(x + w * 0.05, y + h * 0.9), (x + w * 0.6, y + h * 0.75), (x + w * 0.95, y + h * 0.95)], colour, width=0.8)


def stamp_masks(seed, text, size, angle_deg, box=True, sub=None):
    """Rubber-stamp ink coverage, split so the distressing never breaks a letterform: the frame gets full
    'did not touch' gaps; the letters keep a solid core (ink density never below 0.8) and are distressed only on a
    thin band along their edges. Returns (ink, clean_text) at final scale, clean_text being the undistressed glyphs
    (used by the legibility test)."""
    S = 3
    f = P.font('din', int(size * S), 'Bold')          # full width: condensed letters (R/P/B) close up at 2 m
    tw = f.getlength(text)
    pad = size * S * 0.35
    W2 = int(tw + pad * 2)
    H2 = int(size * S * (1.6 if sub else 1.35))
    txt = Image.new('L', (W2, H2), 0)
    frm = Image.new('L', (W2, H2), 0)
    ImageDraw.Draw(txt).text((W2 / 2, H2 * (0.42 if sub else 0.5)), text, font=f, fill=255, anchor='mm')
    if box:
        ImageDraw.Draw(frm).rectangle([2, 2, W2 - 3, H2 - 3], outline=255, width=int(size * S * 0.09))
    if sub:
        ImageDraw.Draw(txt).text((W2 / 2, H2 * 0.82), sub, font=P.font('din', int(size * S * 0.4), 'Bold'), fill=255,
                                 anchor='mm')

    def final(im):
        im = im.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
        return np.asarray(im.resize((max(1, im.width // S), max(1, im.height // S)), Image.LANCZOS), np.float32) / 255

    t, fr = final(txt), final(frm)
    sh = t.shape
    # frame: heavy, patchy contact
    touch = N.smoothstep(0.25, 0.6, N.fbm(sh, seed, 4, base=0.03)) * (0.7 + 0.3 * N.spectral(sh, 0.8, seed + 1))
    fr = fr * np.clip(touch * 1.3, 0, 1)
    # letters: solid core, uneven ink density 0.8..1, ragged only on a 1 px edge band
    core = ndimage.grey_erosion(t, size=(3, 3))
    edge = np.clip(t - core, 0, 1)
    rough = N.smoothstep(0.35, 0.65, N.spectral(sh, 0.6, seed + 2))
    density = 0.8 + 0.2 * N.fbm(sh, seed + 3, 3, base=0.05)
    near = ndimage.grey_dilation(core, size=(3, 3)) > 0.5          # strokes thick enough to have a core
    letters = np.where(near, core + edge * rough, t) * density   # thin strokes (sub-line) stay whole
    return np.clip(np.maximum(letters, fr), 0, 1), t


def stamp(rgb, seed, text, cx, cy, size, angle_deg, colour=STAMP_RED, strength=0.85, box=True, sub=None):
    """Rubber stamp composited with multiply ink (see stamp_masks); rotated."""
    h, w = rgb.shape[:2]
    m, _ = stamp_masks(seed, text, size, angle_deg, box, sub)
    m = m * strength
    mh, mw = m.shape
    out = rgb.copy()
    x0, y0 = int(cx - mw / 2), int(cy - mh / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(w, x0 + mw), min(h, y0 + mh)
    sub_m = m[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - sub_m * (1 - np.array(colour, np.float32)))
    return out


def drop_shadow(alpha, offset=(3, 5), blur=4.0, strength=0.45):
    sh = ndimage.shift(alpha, (offset[1], offset[0]), order=1)
    return ndimage.gaussian_filter(sh, blur) * strength


# --------------------------------------------------------------------------------- layered CLOSED notices
def _sheet(w, h, seed, draw, paper_col, age, torn='tblr', corner_cut=None, rot=0.0):
    doc = P.Doc(w, h)
    draw(doc)
    pap = P.paper(w, h, seed, paper_col)
    rgb = doc.render(pap, seed, fade=age.get('fade', 0.0))
    rgb = P.yellow(rgb, seed + 1, age.get('yellow', 0.2), age.get('edge', 0.25))
    for k, (cx, cy, rr) in enumerate(age.get('stains', [])):
        rgb = P.water_stain(rgb, seed + 10 + k, cx, cy, rr, 0.25)
    if age.get('fox'):
        rgb = P.foxing(rgb, seed + 3, age['fox'], 2.2, 0.22)
    rgb = P.grime(rgb, seed + 4, age.get('grime', 0.12))
    for k, (pos, horiz) in enumerate(age.get('folds', [])):
        rgb = P.fold(rgb, seed + 20 + k, pos, horiz)
    alpha, rim = P.torn_alpha(w, h, seed + 5, inset=6, rough=5.0, torn_sides=torn, corner_cut=corner_cut)
    rgb = rgb * (1 - rim[..., None] * 0.6) + np.array([0.95, 0.93, 0.88]) * rim[..., None] * 0.6
    im = np.dstack([np.clip(rgb, 0, 1), alpha]).astype(np.float32)
    if rot:
        pil = Image.fromarray((im * 255).astype(np.uint8), 'RGBA').rotate(rot, resample=Image.BICUBIC, expand=True)
        im = np.asarray(pil, np.float32) / 255
    return im


def _paste(canvas, sheet, x, y, shadow=True):
    h, w = sheet.shape[:2]
    H, W = canvas.shape[:2]
    full = np.zeros((H, W, 4), np.float32)
    xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    full[ya:yb, xa:xb] = sheet[ya - y:yb - y, xa - x:xb - x]
    a = full[..., 3:4]
    if shadow:
        sh = drop_shadow(full[..., 3])[..., None]
        canvas[..., :3] = canvas[..., :3] * (1 - sh * canvas[..., 3:4])
    canvas[..., :3] = full[..., :3] * a + canvas[..., :3] * (1 - a)
    canvas[..., 3:4] = a + canvas[..., 3:4] * (1 - a)
    return canvas


def notice_closed_layers(size=512, seed=1984):
    """Three layered, torn notices from three different eras of the old station's closure. RGBA."""
    canvas = np.zeros((size, size, 4), np.float32)

    def oldest(doc):            # 1984: the transit authority's printed closure notice, serif, navy
        w = doc.w
        doc.text((w / 2, 34), 'ZERO LINE TRANSIT AUTHORITY', P.font('serif_bold', 17), NAVY_INK, anchor='mm', tracking=1.5)
        doc.line([(40, 50), (w - 40, 50)], NAVY_INK, 1.2)
        doc.text((w / 2, 98), 'STATION', P.font('serif_bold', 62), INK, anchor='mm')
        doc.text((w / 2, 158), 'CLOSED', P.font('serif_bold', 62), INK, anchor='mm')
        y = doc.para(46, 200, 'This station is closed to passengers. Trains will not stop here. Passengers should use '
                     'STATION ZERO, Platform A, by the subway on the right.', P.font('serif', 17), INK, w - 92, 1.3,
                     align='center')
        doc.text((w / 2, y + 26), 'By order of the General Manager', P.font('serif_italic', 15), INK, anchor='mm')
        doc.text((w / 2, y + 50), '2nd July 1984', P.font('serif_italic', 15), INK, anchor='mm')

    def middle(doc):            # later: engineering notice, red header bar, DIN
        w = doc.w
        doc.rect((0, 0, w, 58), RED_INK)
        doc.text((w / 2, 30), 'NOTICE', P.font('din', 38, 'Bold'), (1, 1, 1), anchor='mm', knock=RED_INK)
        doc.text((w / 2, 92), 'CLOSED UNTIL', P.font('din', 40, 'Bold Condensed'), INK, anchor='mm')
        doc.text((w / 2, 134), 'FURTHER NOTICE', P.font('din', 40, 'Bold Condensed'), INK, anchor='mm')
        doc.para(28, 168, 'Structural survey in progress. No entry beyond this point. Unauthorised persons will be '
                 'removed.', P.font('din', 16, 'SemiBold'), INK, w - 56, 1.3, align='center')
        doc.text((w / 2, 252), 'ENGINEERING DEPARTMENT  ·  ZERO LINE', P.font('din', 12, 'Bold'), RED_INK, anchor='mm')

    def newest(doc):            # the night of the incident: a hurried printed slip
        w = doc.w
        doc.rect((6, 6, w - 6, 112), INK, width=3)
        doc.text((w / 2, 46), 'STATION CLOSED', P.fit_font('impact', 'STATION CLOSED', w - 44, 40), INK, anchor='mm')
        doc.text((w / 2, 88), 'DO NOT ENTER  ·  BY ORDER', P.fit_font('din', 'DO NOT ENTER  ·  BY ORDER', w - 50, 18, 'Bold'), INK,
                 anchor='mm')

    s1 = _sheet(330, 420, seed, oldest, (0.93, 0.89, 0.78),
                {'yellow': 0.45, 'edge': 0.4, 'fade': 0.25, 'fox': 30, 'grime': 0.2, 'stains': [(0.25, 0.85, 0.28)],
                 'folds': [(0.5, True)]}, torn='tbr', corner_cut=[(1.0, 0.0, 0.25)], rot=-2.5)
    s2 = _sheet(300, 280, seed + 100, middle, (0.95, 0.94, 0.90),
                {'yellow': 0.25, 'edge': 0.25, 'fade': 0.1, 'grime': 0.12, 'fox': 8}, torn='blr',
                corner_cut=[(0.0, 1.0, 0.3)], rot=3.5)
    s3 = _sheet(270, 124, seed + 200, newest, (0.97, 0.97, 0.95),
                {'yellow': 0.08, 'edge': 0.1, 'grime': 0.06}, torn='lr', rot=-5.0)
    canvas = _paste(canvas, s1, 18, 8, shadow=False)
    canvas = _paste(canvas, s2, 190, 205)
    canvas = _paste(canvas, s3, 120, 320)
    # tape on the newest slip's ends and staples on the middle sheet
    canvas = P.tape(canvas, seed + 7, (118, 352, 168, 372), angle=-0.15)
    canvas = P.tape(canvas, seed + 8, (356, 330, 404, 350), angle=-0.05)
    rgb = canvas[..., :3]
    rgb = P.staple(rgb, 214, 230, 0.5)
    rgb = P.staple(rgb, 448, 246, -0.1)
    rgb = P.staple(rgb, 70, 30, 0.1)
    canvas[..., :3] = rgb
    # nothing may touch the image border (feathered edge for the decal)
    canvas[..., 3] *= N.border_falloff((size, size), 4)
    return canvas


# ----------------------------------------------------------------------------- evacuation / quarantine order
def notice_quarantine(w=512, h=768, seed=2348):
    doc = P.Doc(w, h)
    doc.rect((0, 0, w, 74), RED_INK)
    doc.text((w / 2, 38), 'EMERGENCY NOTICE', P.font('din', 44, 'Bold'), (1, 1, 1), anchor='mm', knock=RED_INK)
    doc.text((w / 2, 104), 'ZERO LINE TRANSIT AUTHORITY  ·  OFFICE OF CIVIL DEFENSE', P.font('din', 13, 'Bold'),
             INK, anchor='mm')
    doc.line([(30, 120), (w - 30, 120)], INK, 1.5)
    doc.text((w / 2, 168), 'EVACUATION ORDER', P.font('din', 50, 'Bold Condensed'), INK, anchor='mm')
    doc.text((w / 2, 214), 'AND QUARANTINE', P.font('din', 34, 'Bold Condensed'), RED_INK, anchor='mm')
    doc.text((w / 2, 252), 'STATION ZERO  ·  ALL PLATFORMS  ·  EFFECTIVE 23:47', P.font('din', 15, 'Bold'), INK,
             anchor='mm')
    body = P.font('din', 15, 'SemiBold')
    y = doc.para(36, 282, 'Following an incident on Platform A, this station is closed and placed under quarantine. '
                 'All passengers and staff must leave immediately by the nearest marked exit.', body, INK, w - 72, 1.3)
    y += 10
    rules = ['Do not use the lifts.',
             'Do not return for luggage or belongings.',
             'Do not approach persons who appear unwell, confused or aggressive.',
             'Report any bite or scratch to the first-aid post in the ticket hall.',
             'Do not re-enter until the all-clear is given by Control.']
    nf = P.font('din', 15, 'Bold')
    for i, rtext in enumerate(rules):
        doc.text((40, y), '%d.' % (i + 1), nf, RED_INK)
        y = doc.para(66, y, rtext, body, INK, w - 106, 1.25) + 6
    y += 6
    doc.rect((30, y, w - 30, y + 64), INK, width=2)
    doc.text((w / 2, y + 22), 'SERVICE SUSPENDED UNTIL FURTHER NOTICE', P.font('din', 17, 'Bold'), INK, anchor='mm')
    doc.text((w / 2, y + 46), 'Trains will not stop at this station.', body, INK, anchor='mm')
    yb = h - 96
    doc.line([(36, yb), (230, yb)], INK, 1)
    doc.text((36, yb + 6), 'Station Supervisor', P.font('din', 12, 'SemiBold'), INK)
    scribble(doc, 50, yb - 14, 140, seed + 1)
    doc.text((w - 36, yb + 6), 'ORDER No. Z-2347', P.font('din', 12, 'Bold'), INK, anchor='ra')
    doc.text((w / 2, h - 40), 'ZERO LINE  ·  EVERY STATION, ALL NIGHT', P.font('din', 11, 'Bold'), (0.4, 0.4, 0.42),
             anchor='mm')
    pap = P.paper(w, h, seed, (0.95, 0.94, 0.90))
    rgb = doc.render(pap, seed, uneven=0.1)
    rgb = stamp(rgb, seed + 2, 'QUARANTINE', 350, 636, 32, 10, strength=0.85, sub='ZONE A  ·  23:47')
    rgb = P.yellow(rgb, seed + 3, 0.22, 0.3)
    rgb = P.fold(rgb, seed + 4, 0.5, True, 0.2)
    rgb = P.fold(rgb, seed + 5, 0.33, True, 0.12)
    rgb = P.water_stain(rgb, seed + 6, 0.2, 0.92, 0.2, 0.28)
    rgb = P.grime(rgb, seed + 7, 0.07)
    rgb = P.handling(rgb, seed + 8, 0.18)
    rgba = np.dstack([rgb, np.ones((h, w), np.float32)])
    rgba = P.tape(rgba, seed + 10, (30, -4, 104, 22), angle=0.6)
    rgba = P.tape(rgba, seed + 11, (w - 104, -4, w - 30, 22), angle=-0.6)
    return np.clip(rgba[..., :3], 0, 1)


# ------------------------------------------------------------------ generator lock-out notice + night roster
ROSTER = [
    ('D. MALONE', 'SIGNAL TECH.', '22:00-06:00', '21:52', ''),
    ('R. OKAFOR', 'SUPERVISOR', '22:00-06:00', '21:47', ''),
    ('T. BECKER', 'ELECTRICIAN', '22:00-06:00', '21:58', ''),
    ('J. ALVAREZ', 'TRACK GANG', '22:00-06:00', '22:03', ''),
    ('M. KOWALSKI', 'TRACK GANG', '22:00-06:00', '22:01', ''),
    ('S. PRICE', 'STATION ASST.', '14:00-22:00', '13:55', '22:06'),
]


def notice_do_not_restart(w=512, h=768, seed=4747):
    doc = P.Doc(w, h)
    # 1980s safety-sign header: black panel, red oval with DANGER knocked out
    doc.rect((14, 14, w - 14, 98), INK)
    doc.ellipse((w / 2 - 128, 24, w / 2 + 128, 88), RED_INK, knock=INK)
    doc.text((w / 2, 56), 'DANGER', P.font('din', 46, 'Bold'), (1, 1, 1), anchor='mm', knock=[RED_INK, INK])
    doc.text((w / 2, 140), 'DO NOT RESTART', P.font('din', 50, 'Bold Condensed'), INK, anchor='mm')
    doc.text((w / 2, 190), 'GENERATOR', P.font('din', 50, 'Bold Condensed'), INK, anchor='mm')
    body = P.font('din', 14, 'SemiBold')
    y = doc.para(32, 222, 'Generator G-2 tripped at 23:47. Fault under investigation. Restarting will re-energise the '
                 'third rail on Platform A.', body, INK, w - 64, 1.3, align='center')
    doc.rect((32, y + 8, w - 32, y + 44), RED_INK, width=2)
    doc.text((w / 2, y + 26), 'LOCKED OUT  ·  TAG No. 0447  ·  SEE SUPERVISOR', P.font('din', 14, 'Bold'), RED_INK,
             anchor='mm')
    # roster
    y = y + 70
    doc.line([(20, y), (w - 20, y)], INK, 1.5)
    doc.text((w / 2, y + 20), 'NIGHT SHIFT ROSTER  ·  STATION ZERO  ·  WEEK 44', P.font('typewriter_bold', 15), INK,
             anchor='mm')
    y += 40
    cols = [(24, 'NAME'), (150, 'DUTY'), (268, 'SHIFT'), (372, 'IN'), (432, 'OUT')]
    tf = P.font('typewriter_bold', 13)
    for x, t in cols:
        doc.text((x, y), t, tf, INK)
    y += 20
    doc.line([(20, y - 3), (w - 20, y - 3)], INK, 1)
    rf = P.font('typewriter', 13)
    pen = (0.12, 0.14, 0.32)
    r = np.random.default_rng(seed)
    for i, row in enumerate(ROSTER):
        for (x, _), t in zip(cols, row):
            if t:
                colr = pen if x >= 372 else INK
                doc.text((x + (r.normal(0, 0.6) if x >= 372 else 0), y + (r.normal(0, 0.6) if x >= 372 else 0)), t,
                         P.font('typewriter_bold', 13) if x >= 372 else rf, colr)
        doc.line([(20, y + 19), (w - 20, y + 19)], (0.55, 0.55, 0.58), 0.6)
        y += 26
    # the OUT column stays empty for the night shift: ruled empty boxes, the supervisor's question in pen
    doc.text((24, y + 10), 'OUT not signed - night shift. Control informed 23:55.', P.font('typewriter', 12), INK)
    y += 34
    doc.text((24, y), 'Supervisor:', P.font('typewriter', 12), INK)
    scribble(doc, 120, y - 2, 110, seed + 3)
    doc.text((w - 24, h - 30), 'FORM ZL-114', P.font('din', 10, 'Bold'), (0.4, 0.4, 0.42), anchor='ra')
    pap = P.paper(w, h, seed, (0.94, 0.93, 0.88))
    rgb = doc.render(pap, seed, uneven=0.1)
    rgb = P.yellow(rgb, seed + 4, 0.28, 0.35)
    rgb = P.grime(rgb, seed + 5, 0.08)
    rgb = P.water_stain(rgb, seed + 6, 0.15, 0.08, 0.2, 0.25)
    rgb = P.foxing(rgb, seed + 7, 20, 2.0, 0.2)
    rgb = P.handling(rgb, seed + 8, 0.25)
    rgb = P.staple(rgb, 40, 10, 0.2)
    rgb = P.staple(rgb, w - 40, 10, -0.2)
    return np.clip(rgb, 0, 1)


# ------------------------------------------------------------------------------------ missing-person posters
def _photo(path, box_w, box_h, focus=0.42):
    im = Image.open(path).convert('RGB')
    # cover-crop to the box aspect around the face (upper middle)
    tw, th = im.size
    ar = box_w / box_h
    if tw / th > ar:
        nw = int(th * ar)
        x0 = (tw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, th))
    else:
        nh = int(tw / ar)
        y0 = int((th - nh) * focus)
        im = im.crop((0, y0, tw, y0 + nh))
    return im


def poster_missing(variant, photo_path, w=512, h=768, seed=None):
    """variant 'a' photocopied flyer (signal technician), 'b' family flyer with a real colour print stapled on,
    'c' old rain-faded flyer (elderly commuter)."""
    seed = seed if seed is not None else {'a': 7001, 'b': 7002, 'c': 7003}[variant]
    doc = P.Doc(w, h)
    if variant == 'a':
        doc.text((w / 2, 66), 'MISSING', P.font('impact', 96), INK, anchor='mm')
        pw, ph = 300, 360
        px, py = (w - pw) // 2, 124
        im = _photo(photo_path, pw * 2, ph * 2)
        g = np.asarray(im.convert('L').resize((pw, ph), Image.LANCZOS), np.float32) / 255
        g = P.photocopy(g, seed + 1, 1.8, 0.05)
        doc.image(Image.fromarray((g * 255).astype(np.uint8)), (px, py, px + pw, py + ph))
        doc.rect((px, py, px + pw, py + ph), INK, width=2)
        doc.text((w / 2, 522), 'DANIEL MALONE', P.font('din', 40, 'Bold'), INK, anchor='mm')
        doc.text((w / 2, 556), 'AGE 46  ·  5\'10"  ·  BROWN EYES  ·  MOUSTACHE', P.font('din', 16, 'Bold'), INK,
                 anchor='mm')
        y = doc.para(40, 576, 'Signal technician, Zero Line. Last seen on the night shift at STATION ZERO, about 23:40. '
                     'Wearing a navy work jacket.', P.font('din', 16, 'SemiBold'), INK, w - 80, 1.3, align='center')
        doc.text((w / 2, y + 22), 'PLEASE CALL 555-0147', P.font('din', 28, 'Bold'), INK, anchor='mm')
        doc.text((w / 2, y + 54), 'ANY INFORMATION  ·  DAY OR NIGHT', P.font('din', 14, 'Bold'), INK, anchor='mm')
        pap = P.paper(w, h, seed, (0.95, 0.95, 0.93), grain=0.02)
        rgb = doc.render(pap, seed, bleed=0.6, uneven=0.18)
        g2 = P.photocopy(rgb.mean(-1), seed + 2, 1.15, 0.03)       # the whole sheet is a copy of a copy
        rgb = np.dstack([g2] * 3) * np.array([1.0, 0.99, 0.96])
        rgb = P.yellow(rgb, seed + 3, 0.12, 0.2)
        rgb = P.fold(rgb, seed + 4, 0.5, False, 0.12)
        rgb = P.grime(rgb, seed + 5, 0.1)
        rgba = P.tape(np.dstack([rgb, np.ones((h, w))]).astype(np.float32), seed + 6, (w / 2 - 50, -4, w / 2 + 50, 20))
        return np.clip(rgba[..., :3], 0, 1)
    if variant == 'b':
        doc.text((w / 2, 52), 'HAVE YOU SEEN', P.font('din', 46, 'Bold Condensed'), RED_INK, anchor='mm')
        doc.text((w / 2, 102), 'OUR DAUGHTER?', P.font('din', 46, 'Bold Condensed'), RED_INK, anchor='mm')
        doc.text((w / 2, 532), 'LINDA PRESCOTT', P.font('din', 38, 'Bold'), INK, anchor='mm')
        doc.text((w / 2, 566), 'AGE 28  ·  5\'5"  ·  LIGHT BROWN HAIR', P.font('din', 16, 'Bold'), INK, anchor='mm')
        y = doc.para(40, 586, 'Linda took the last train home from STATION ZERO on the night of the incident and never '
                     'arrived. Denim jacket, striped top, gold hoop earrings.', P.font('din', 15, 'SemiBold'), INK,
                     w - 80, 1.3, align='center')
        doc.text((w / 2, y + 24), 'CALL 555-0183', P.font('din', 30, 'Bold'), RED_INK, anchor='mm')
        doc.text((w / 2, y + 54), 'WE LOVE YOU, LINDA. PLEASE COME HOME.', P.font('din', 14, 'Bold'), INK, anchor='mm')
        pap = P.paper(w, h, seed, (0.97, 0.93, 0.74), grain=0.03)      # canary yellow copier paper
        rgb = doc.render(pap, seed, uneven=0.12)
        # the real photo print, stapled on with a white border and a slight tilt
        pw, ph = 270, 340
        im = _photo(photo_path, pw, ph, 0.35).resize((pw, ph), Image.LANCZOS)
        bordered = Image.new('RGB', (pw + 24, ph + 24), (240, 236, 226))
        bordered.paste(im, (12, 12))
        arr = np.asarray(bordered, np.float32) / 255
        arr = P.yellow(arr, seed + 1, 0.15, 0.15) * 0.97 + 0.02           # faded print
        pil = Image.fromarray((arr * 255).astype(np.uint8)).convert('RGBA').rotate(-2.2, resample=Image.BICUBIC,
                                                                                   expand=True)
        a = np.asarray(pil, np.float32) / 255
        ph2, pw2 = a.shape[:2]
        x0, y0 = (w - pw2) // 2, 128
        canvas = np.dstack([rgb, np.ones((h, w))]).astype(np.float32)
        sub = np.zeros((h, w, 4), np.float32)
        sub[y0:y0 + ph2, x0:x0 + pw2] = a
        shadow = drop_shadow(sub[..., 3], (2, 4), 3.0, 0.4)[..., None]
        canvas[..., :3] *= (1 - shadow)
        canvas[..., :3] = sub[..., :3] * sub[..., 3:4] + canvas[..., :3] * (1 - sub[..., 3:4])
        rgb = canvas[..., :3]
        rgb = P.staple(rgb, w / 2 - 110, 134, 0.1)
        rgb = P.staple(rgb, w / 2 + 110, 132, -0.05)
        rgb = P.yellow(rgb, seed + 2, 0.1, 0.25)
        rgb = P.water_stain(rgb, seed + 3, 0.2, 0.75, 0.2, 0.2)
        rgb = P.grime(rgb, seed + 4, 0.1)
        rgb = P.handling(rgb, seed + 5, 0.15)
        return np.clip(rgb, 0, 1)
    if variant == 'c':
        doc.rect((0, 0, w, 96), INK)
        doc.text((w / 2, 50), 'MISSING', P.font('din', 70, 'Bold'), (1, 1, 1), anchor='mm', knock=INK)
        pw, ph = 280, 340
        px, py = (w - pw) // 2, 122
        im = _photo(photo_path, pw * 2, ph * 2, 0.35)
        g = np.asarray(im.convert('L').resize((pw, ph), Image.LANCZOS), np.float32) / 255
        g = P.photocopy(g, seed + 1, 1.5, 0.04)
        doc.image(Image.fromarray((g * 255).astype(np.uint8)), (px, py, px + pw, py + ph))
        doc.text((w / 2, 500), 'WALTER HUGHES', P.font('din', 38, 'Bold'), INK, anchor='mm')
        doc.text((w / 2, 532), 'AGE 67  ·  GLASSES  ·  GREY CARDIGAN', P.font('din', 16, 'Bold'), INK, anchor='mm')
        y = doc.para(40, 552, 'Walter rides the Zero Line every evening. He was last seen waiting on Platform A at '
                     'STATION ZERO. He may be confused and need help.', P.font('din', 15, 'SemiBold'), INK, w - 80,
                     1.3, align='center')
        doc.text((w / 2, y + 24), 'PHONE 555-0129', P.font('din', 28, 'Bold'), INK, anchor='mm')
        pap = P.paper(w, h, seed, (0.94, 0.94, 0.92))
        rgb = doc.render(pap, seed, bleed=0.6, uneven=0.2, fade=0.28)      # rain-faded
        rgb = P.yellow(rgb, seed + 2, 0.35, 0.4)
        rgb = P.water_stain(rgb, seed + 3, 0.6, 0.15, 0.35, 0.35)
        rgb = P.water_stain(rgb, seed + 4, 0.25, 0.8, 0.3, 0.3)
        # rain runs: ink washed downward from the photo and the name
        runs = N.streaks((h, w), seed + 5, 18, length=(0.1, 0.35), width=(2, 6), x_range=(0.2, 0.8),
                         y0_range=(0.15, 0.7), wobble=1.0, wrap_x=False)
        rgb = rgb * (1 - runs[..., None] * 0.18)
        rgb = P.fold(rgb, seed + 6, 0.5, True, 0.18)
        rgb = P.fold(rgb, seed + 7, 0.5, False, 0.14)
        rgb = P.grime(rgb, seed + 8, 0.2)
        rgb = P.foxing(rgb, seed + 9, 30, 2.4, 0.22)
        return np.clip(rgb, 0, 1)
    raise ValueError(variant)


# ------------------------------------------------------------------------------------- cracked lit ad panel
def ad_panel_broken(illustration_path, w=1024, h=512, seed=6060):
    """Backlit 1980s ad light box: the beach illustration with typeset copy, aluminium frame, uneven tube backlight
    (one tube dead), a cracked acrylic front with an impact and a missing shard, dust. RGB."""
    S = 2
    W, H = w * S, h * S
    frame = 16
    src = Image.open(illustration_path).convert('RGB')
    art = src.resize((W - 2 * frame * S, int(src.height * (W - 2 * frame * S) / src.width)), Image.LANCZOS)
    art = art.crop((0, 0, art.width, H - 2 * frame * S)) if art.height >= H - 2 * frame * S else \
        art.resize((W - 2 * frame * S, H - 2 * frame * S), Image.LANCZOS)
    im = Image.new('RGB', (W, H), (150, 152, 156))
    im.paste(art, (frame * S, frame * S))
    d = ImageDraw.Draw(im)
    # copy (right side, over the open sea/sky)
    tx = int(W * 0.60)
    h1 = P.font('din', 58 * S, 'Bold Condensed')
    h2 = P.font('din', 26 * S, 'SemiBold')

    def shadowed(xy, text, f, fill, sh=(14, 40, 86)):
        d.text((xy[0] + 3 * S, xy[1] + 3 * S), text, font=f, fill=sh, anchor='la')
        d.text(xy, text, font=f, fill=fill, anchor='la')

    shadowed((tx, 70 * S), 'THE BEACH IS', h1, (18, 40, 86), sh=(255, 255, 255))
    shadowed((tx, 128 * S), '40 MINUTES', h1, (18, 40, 86), sh=(255, 255, 255))
    shadowed((tx, 186 * S), 'AWAY', h1, (214, 56, 36), sh=(255, 255, 255))
    sub = 'Radioactive Beach, every 12 minutes.'
    h2 = P.fit_font('din', sub, W - frame * S - 24 * S - tx, 26 * S, 'SemiBold')
    d.text((tx, 262 * S), 'Zero Line summer service to', font=h2, fill=(18, 40, 86), anchor='la')
    d.text((tx, 294 * S), sub, font=h2, fill=(18, 40, 86), anchor='la')
    bx, by = W - 70 * S, H - 74 * S
    B.zero_badge(d, bx, by, 28 * S, width=3 * S)
    d.text((bx - 40 * S, by), 'ZERO LINE', font=P.font('din', 30 * S, 'Bold'), fill=(18, 40, 86), anchor='rm')
    # aluminium frame with screws
    d.rectangle([0, 0, W - 1, H - 1], outline=(110, 112, 116), width=frame * S)
    d.rectangle([frame * S - 2 * S, frame * S - 2 * S, W - frame * S + 2 * S, H - frame * S + 2 * S], outline=(60, 62, 66),
                width=2 * S)
    for sx, sy in ((frame * S // 2, frame * S // 2), (W - frame * S // 2, frame * S // 2), (frame * S // 2, H - frame * S // 2),
                   (W - frame * S // 2, H - frame * S // 2)):
        d.ellipse([sx - 4 * S, sy - 4 * S, sx + 4 * S, sy + 4 * S], fill=(70, 70, 74))
    rgb = np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    inner = ((xx > frame) & (xx < w - frame) & (yy > frame) & (yy < h - frame)).astype(np.float32)
    # backlight: three horizontal tubes; the bottom one is dead; hot bands over live tubes, a little vignetting
    light = np.full((h, w), 0.70, np.float32)
    for ty, on in ((0.2, 1.0), (0.52, 1.0), (0.84, 0.0)):
        light += on * 0.32 * np.exp(-((yy / h - ty) / 0.16) ** 2)
    light *= 1 - 0.18 * ((xx / w - 0.5) * 2) ** 2
    light = ndimage.gaussian_filter(light, 4)
    lit = rgb * (light[..., None] * 1.12)
    lit = lit + 0.06 * light[..., None]                      # lifted blacks of a transparency
    rgb = rgb * (1 - inner[..., None]) + np.clip(lit, 0, 1) * inner[..., None]
    # cracked acrylic: impact left of centre-bottom, a missing shard (dark box interior, a bare tube end visible)
    ix, iy = w * 0.36, h * 0.66
    cr = B.cracks(max(w, h), seed + 1, ix, iy, w * 0.40, n_radial=9, rings=2, jitter=0.05)[:h, :w] * inner
    shard = np.zeros((h, w), np.float32)
    # the missing shard: the transparency is torn there, so the bright white box interior shows, with the tube
    pil = Image.new('L', (w, h), 0)
    ImageDraw.Draw(pil).polygon([(ix - 3, iy - 2), (ix + 20, iy - 13), (ix + 30, iy + 3), (ix + 12, iy + 17), (ix - 8, iy + 10)],
                                fill=255)
    shard = ndimage.gaussian_filter(np.asarray(pil, np.float32) / 255, 0.6)
    tube = np.exp(-((yy - (iy + 2)) / 3.0) ** 2)[..., None]
    interior = np.array([0.86, 0.87, 0.86]) * (1 - tube) + np.array([1.0, 1.0, 0.97]) * tube
    rim = np.clip(ndimage.gaussian_gradient_magnitude(shard, 0.8) * 3, 0, 1)
    rgb = rgb * (1 - shard[..., None]) + interior * shard[..., None]
    rgb = rgb * (1 - rim[..., None] * 0.6)
    shadow_side = ndimage.shift(cr, (1.0, 1.0), order=1)
    rgb = rgb * (1 - shadow_side[..., None] * 0.35)
    rgb = rgb * (1 - cr[..., None] * 0.55) + cr[..., None] * 0.55 * np.array([1.0, 1.0, 0.98])
    # dust and grime on the front, heavier at the bottom edge and corners
    rgb = B.overlay(rgb, M.sign_grime_overlay(w, h, seed + 2), 0.75)
    return np.clip(rgb, 0, 1).astype(np.float32)


# -------------------------------------------------------------------------------- second film poster
def paint_roundel_z(img, box=(0.25, 0.12, 0.75, 0.45)):
    """Find the blank dark-green enamel disc above the stairwell (largest dark-green blob inside `box`, fractions) and
    paint the Zero Line 'Z' on it, keeping the painting's light and rain: the letter colour is modulated by the disc's
    own luminance and the illustration's fine detail is added back on top. Returns img unchanged if no disc is found."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    sub = img[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    green = (g > r * 1.25) & (g > b * 1.05) & (g < 0.45)
    lab, n = ndimage.label(ndimage.binary_opening(green, iterations=2))
    if n == 0:
        return img
    sizes = ndimage.sum(green, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    ys, xs = np.nonzero(lab == k)
    if len(xs) < 2000:
        return img
    cx, cy = xs.mean() + x0, ys.mean() + y0
    rad = math.sqrt(len(xs) / math.pi)
    S = 4
    m = Image.new('L', (w * S, h * S), 0)
    ImageDraw.Draw(m).text((cx * S, cy * S + rad * S * 0.04), 'Z', font=P.font('arial_bold', int(rad * 1.25 * S)),
                           fill=255, anchor='mm')
    a = np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255
    a = ndimage.gaussian_filter(a, 0.8) * 0.92
    lum = img.mean(axis=2)
    disc_lum = ndimage.gaussian_filter(lum, rad * 0.25)
    shade = np.clip(disc_lum / max(float(lum[int(cy), int(cx)]), 1e-3), 0.6, 1.5)[..., None]
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    toplit = np.clip(1.08 - 0.25 * (yy - (cy - rad)) / (2 * rad), 0.8, 1.1)[..., None]   # lamp light from above
    wear = (0.9 + 0.1 * N.fbm((h, w), 77, 4, base=0.05))[..., None]
    letter = np.array([0.93, 0.90, 0.80], np.float32)[None, None, :] * shade * toplit * wear
    detail = img - ndimage.gaussian_filter(img, (1.5, 1.5, 0))
    out = img * (1 - a[..., None]) + np.clip(letter + detail * 2.0, 0, 1) * a[..., None]
    return np.clip(out, 0, 1).astype(np.float32)


def poster_station_zero_v2(illustration_path, w=1024, h=1536, seed=6161):
    """Film poster on the stairwell illustration: STATION ZERO title (same treatment as the first poster), a new
    tagline and a diegetic credit line. Returns (poster RGB at w x h, the text-free illustration at w x h)."""
    base = Image.open(illustration_path).convert('RGB').resize((w, h), Image.LANCZOS)
    plain = np.asarray(base, np.float32) / 255
    plain = paint_roundel_z(plain)
    p = Image.fromarray((plain * 255 + 0.5).astype(np.uint8)).convert('RGBA')
    glow = Image.new('RGBA', p.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    t1, t2 = P.font('impact', int(h * 0.082)), P.font('impact', int(h * 0.128))
    y1, y2 = h * 0.06, h * 0.152
    gd.text((w / 2, y1), 'STATION', font=t1, fill=(120, 255, 90, 255), anchor='mm')
    gd.text((w / 2, y2), 'ZERO', font=t2, fill=(120, 255, 90, 255), anchor='mm')
    glow = glow.filter(ImageFilter.GaussianBlur(w / 64))
    p.alpha_composite(glow)
    p.alpha_composite(glow)
    d = ImageDraw.Draw(p)
    d.text((w / 2, y1), 'STATION', font=t1, fill=(230, 255, 220, 255), anchor='mm', stroke_width=3,
           stroke_fill=(10, 30, 10, 255))
    d.text((w / 2, y2), 'ZERO', font=t2, fill=(150, 255, 120, 255), anchor='mm', stroke_width=4,
           stroke_fill=(10, 30, 10, 255))
    tag = 'THE CITY ABOVE IS NEXT'
    d.text((w / 2, h * 0.919), tag, font=P.fit_font('din', tag, w * 0.84, int(h * 0.036), 'Regular'),
           fill=(255, 120, 205, 255), anchor='mm')
    cred = 'WILLARD WYLER PRESENTS  •  A ZERO LINE PICTURE  •  NOW SHOWING'
    d.text((w / 2, h * 0.958), cred, font=P.fit_font('din', cred, w * 0.86, int(h * 0.0185), 'Regular'),
           fill=(205, 205, 215, 255), anchor='mm')
    return np.asarray(p.convert('RGB'), np.float32) / 255, plain
