"""Station hardware graphics: stopped clock face, split-flap departure board, signal & evacuation diagram.

Exact text, drawn from fonts. Palette and type follow the existing Zero Line sign art (make_signs.py): Bahnschrift,
enamel navy (22, 40, 86), Zero green (60, 170, 90), red (200, 44, 36), yellow (250, 200, 30), off-white (244, 242, 236).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

from . import masks as M
from . import noise as N
from . import paper as P

NAVY = (22, 40, 86)
ZGREEN = (60, 170, 90)
RED = (200, 44, 36)
YELLOW = (250, 200, 30)
WHITE = (244, 242, 236)
INCIDENT = '23:47'


def _f(c):
    return np.array(c, np.float32) / 255.0


def zero_badge(d, cx, cy, r, ring=WHITE, fill=ZGREEN, ink=WHITE, width=None):
    """The Zero Line roundel: green disc, white ring, white Z (same as the station plates)."""
    width = width or max(1, int(r * 0.12))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=ring, width=width)
    d.text((cx, cy + r * 0.05), 'Z', font=P.font('arial_bold', int(r * 1.3)), fill=ink, anchor='mm')


def overlay(base_rgb, ov_rgba, strength=1.0):
    a = ov_rgba[..., 3:4] * strength
    return base_rgb * (1 - a) + ov_rgba[..., :3] * a


# ----------------------------------------------------------------------------------------------- clock face
def cracks(size, seed, cx, cy, radius, n_radial=11, rings=3, jitter=0.06):
    """Impact crack network on glass: jagged radial cracks from (cx, cy) plus partial concentric cracks.
    Returns (line mask, shard id field) at `size`."""
    r = np.random.default_rng(seed)
    S = 3
    W = size * S
    im = Image.new('L', (W, W), 0)
    d = ImageDraw.Draw(im)
    angles = np.sort(r.uniform(0, 2 * np.pi, n_radial))
    ends = []
    for a in angles:
        L = r.uniform(0.45, 1.0) * radius
        pts = [(cx * S, cy * S)]
        x, y, ang = cx, cy, a
        steps = int(L / 9)
        for i in range(steps):
            ang += r.normal(0, jitter)
            x += math.cos(ang) * 9
            y += math.sin(ang) * 9
            pts.append((x * S, y * S))
            if r.random() < 0.08:          # a forked branch
                bx, by, ba = x, y, ang + r.choice([-1, 1]) * r.uniform(0.3, 0.7)
                bpts = [(x * S, y * S)]
                for _ in range(r.integers(2, 7)):
                    ba += r.normal(0, 0.15)
                    bx += math.cos(ba) * 8
                    by += math.sin(ba) * 8
                    bpts.append((bx * S, by * S))
                d.line(bpts, fill=200, width=S)
        d.line(pts, fill=255, width=int(S * r.uniform(1.0, 1.6)))
        ends.append(pts)
    for k in range(rings):
        rr = radius * (0.12 + 0.17 * k) * r.uniform(0.85, 1.15)
        a0 = r.uniform(0, 2 * np.pi)
        span = r.uniform(1.5, 4.5)
        pts = []
        for t in np.linspace(0, span, int(span * rr / 8) + 2):
            rj = rr * (1 + r.normal(0, 0.03))
            pts.append(((cx + math.cos(a0 + t) * rj) * S, (cy + math.sin(a0 + t) * rj) * S))
        d.line(pts, fill=230, width=S)
    # crushed glass at the impact
    for _ in range(40):
        a, rr = r.uniform(0, 2 * np.pi), abs(r.normal(0, radius * 0.035))
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        d.line([(x * S, y * S), ((x + r.normal(0, 4)) * S, (y + r.normal(0, 4)) * S)], fill=255, width=S)
    return np.asarray(im.resize((size, size), Image.LANCZOS), np.float32) / 255


def clock_face_stopped(size=512, seed=2347, hhmm=INCIDENT, second=37):
    """Station clock, stopped at the incident time, cracked glass. RGBA, alpha 0 outside the bezel."""
    S = 4
    W = size * S
    c = W / 2
    R_out, R_dial = W * 0.492, W * 0.445
    base = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.ellipse([c - R_out, c - R_out, c + R_out, c + R_out], fill=(30, 31, 33, 255))           # black steel bezel
    d.ellipse([c - R_out * 0.965, c - R_out * 0.965, c + R_out * 0.965, c + R_out * 0.965], outline=(70, 72, 76, 255),
              width=int(S * 1.5))
    d.ellipse([c - R_dial, c - R_dial, c + R_dial, c + R_dial], fill=(236, 232, 220, 255))   # enamel dial
    # minute ticks and hour bars
    for i in range(60):
        a = math.radians(i * 6 - 90)
        hour = i % 5 == 0
        r0 = R_dial * (0.76 if hour else 0.88)
        r1 = R_dial * 0.955
        wdt = S * (11 if hour else 3.2)
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * r1, c + math.sin(a) * r1)],
               fill=(18, 18, 20, 255), width=int(wdt))
    # 24-hour inner ring (13..24) in red: railway practice, and it makes 23:47 read unambiguously
    f24 = P.font('din', int(R_dial * 0.085), 'SemiBold')
    for hnum in range(1, 13):
        a = math.radians(hnum * 30 - 90)
        rr = R_dial * 0.64
        d.text((c + math.cos(a) * rr, c + math.sin(a) * rr), str(hnum + 12), font=f24, fill=RED + (255,), anchor='mm')
    # branding
    # branding in the lower half, clear of the stopped hands (hour ~12, minute ~9:24, second ~7:30)
    zero_badge(d, c + R_dial * 0.02, c + R_dial * 0.24, R_dial * 0.085, ring=(236, 232, 220), width=S * 2)
    d.text((c + R_dial * 0.02, c + R_dial * 0.385), 'ZERO LINE', font=P.font('din', int(R_dial * 0.07), 'Bold'),
           fill=(18, 18, 20, 255), anchor='mm')
    hh, mm = (int(v) for v in hhmm.split(':'))
    a_h = math.radians(((hh % 12) + mm / 60) * 30 - 90)
    a_m = math.radians(mm * 6 - 90)
    a_s = math.radians(second * 6 - 90)

    def bar(ang, back, front, w_back, w_front, colour):
        pts = [(c - math.cos(ang) * back - math.sin(ang) * w_back / 2, c - math.sin(ang) * back + math.cos(ang) * w_back / 2),
               (c - math.cos(ang) * back + math.sin(ang) * w_back / 2, c - math.sin(ang) * back - math.cos(ang) * w_back / 2),
               (c + math.cos(ang) * front + math.sin(ang) * w_front / 2, c + math.sin(ang) * front - math.cos(ang) * w_front / 2),
               (c + math.cos(ang) * front - math.sin(ang) * w_front / 2, c + math.sin(ang) * front + math.cos(ang) * w_front / 2)]
        return pts, colour

    hands = [bar(a_h, R_dial * 0.16, R_dial * 0.55, S * 15, S * 11, (16, 16, 18, 255)),
             bar(a_m, R_dial * 0.16, R_dial * 0.87, S * 12, S * 8, (16, 16, 18, 255))]
    # hand shadows on the dial (light from above): offset, blurred
    shadow = Image.new('L', (W, W), 0)
    sd = ImageDraw.Draw(shadow)
    off = (S * 3, S * 6)
    for pts, _ in hands:
        sd.polygon([(x + off[0], y + off[1]) for x, y in pts], fill=120)
    sd.line([(c - math.cos(a_s) * R_dial * 0.22 + off[0], c - math.sin(a_s) * R_dial * 0.22 + off[1]),
             (c + math.cos(a_s) * R_dial * 0.8 + off[0], c + math.sin(a_s) * R_dial * 0.8 + off[1])], fill=90, width=S * 3)
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 3))
    dial_mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(dial_mask).ellipse([c - R_dial, c - R_dial, c + R_dial, c + R_dial], fill=255)
    shadow = Image.fromarray((np.asarray(shadow, np.float32) * np.asarray(dial_mask, np.float32) / 255).astype(np.uint8))
    base = Image.composite(Image.new('RGBA', (W, W), (40, 36, 30, 255)), base, shadow)
    d = ImageDraw.Draw(base)
    for pts, col in hands:
        d.polygon(pts, fill=col)
    # second hand: red, with the lollipop disc
    sx, sy = c + math.cos(a_s) * R_dial * 0.8, c + math.sin(a_s) * R_dial * 0.8
    d.line([(c - math.cos(a_s) * R_dial * 0.22, c - math.sin(a_s) * R_dial * 0.22), (sx, sy)], fill=RED + (255,), width=S * 3)
    lr = R_dial * 0.06
    lx, ly = c + math.cos(a_s) * R_dial * 0.62, c + math.sin(a_s) * R_dial * 0.62
    d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=RED + (255,))
    d.ellipse([c - S * 9, c - S * 9, c + S * 9, c + S * 9], fill=(20, 20, 22, 255))
    d.ellipse([c - S * 4, c - S * 4, c + S * 4, c + S * 4], fill=RED + (255,))
    im = np.asarray(base.resize((size, size), Image.LANCZOS), np.float32) / 255
    rgb, alpha = im[..., :3], im[..., 3]
    # dial ageing: yellowed enamel, a water stain from the top, foxing
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    rd = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / size
    on_dial = (rd < 0.445).astype(np.float32)[..., None]
    aged = P.yellow(rgb, seed, 0.18, 0.15)
    aged = P.water_stain(aged, seed + 1, 0.38, 0.22, 0.16, 0.18)
    aged = P.foxing(aged, seed + 2, 14, 2.0, 0.18)
    rgb = rgb * (1 - on_dial) + aged * on_dial
    # bezel wear: scuffs showing lighter steel
    scuff = N.smoothstep(0.75, 0.95, N.spectral((size, size), 1.0, seed + 3)) * (1 - on_dial[..., 0]) * (rd < 0.49)
    rgb = rgb + scuff[..., None] * 0.12
    # glass: dust film heavier toward the bottom, a soft glare arc, cracks from an impact upper right
    dust = (0.10 + 0.10 * N.fbm((size, size), seed + 4, 5, base=0.01)) * (0.6 + 0.6 * yy / size)
    rgb = rgb * (1 - dust[..., None] * on_dial) + np.array([0.55, 0.50, 0.42]) * dust[..., None] * on_dial
    glare = np.exp(-((rd - 0.33) / 0.03) ** 2) * N.smoothstep(-0.2, 0.6, (size / 2 - yy) / size * 2 - (xx - size / 2) / size)
    rgb = rgb + glare[..., None] * 0.10 * on_dial
    ix, iy = size * 0.66, size * 0.36
    cr = cracks(size, seed + 5, ix, iy, size * 0.42)
    cr = cr * on_dial[..., 0]
    shadow_side = ndimage.shift(cr, (1.2, 1.2), order=1)
    rgb = rgb * (1 - shadow_side[..., None] * 0.45)
    rgb = rgb * (1 - cr[..., None] * 0.6) + cr[..., None] * 0.6 * np.array([0.97, 0.97, 0.95])
    crush = np.exp(-(((xx - ix) ** 2 + (yy - iy) ** 2) / (size * 0.03) ** 2))
    rgb = rgb * (1 - crush[..., None] * 0.35) + crush[..., None] * 0.35 * 0.85
    return np.dstack([np.clip(rgb, 0, 1), alpha]).astype(np.float32)


# ----------------------------------------------------------------------------------- split-flap departure board
BOARD_ROWS = [
    ('23:47', 'COSMIC HEIGHTS', 'A', 'SERVICE SUSPENDED'),
    ('23:52', 'REDWOODS', 'A', 'SERVICE SUSPENDED'),
    ('23:58', 'ARCADIA', 'A', 'SERVICE SUSPENDED'),
    ('00:05', 'POLAR PEAK', 'A', 'SERVICE SUSPENDED'),
]


def departure_board_suspended(w=1024, h=256, seed=4752, rows=BOARD_ROWS, clock=INCIDENT):
    """Split-flap departures board: header with the Zero Line badge, DEPARTURES and the stopped clock; every row
    SERVICE SUSPENDED. One flap stuck mid-turn, one missing, dust on the cover glass. RGB."""
    S = 3
    W, H = w * S, h * S
    im = Image.new('RGB', (W, H), (34, 35, 38))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    pad = 8 * S
    d.rectangle([0, 0, W - 1, H - 1], fill=(48, 50, 54))
    d.rectangle([pad, pad, W - pad, H - pad], fill=(14, 14, 16))
    head_h = 44 * S
    d.rectangle([pad, pad, W - pad, pad + head_h], fill=NAVY)
    d.rectangle([pad, pad + head_h, W - pad, pad + head_h + 3 * S], fill=YELLOW)
    zero_badge(d, pad + 26 * S, pad + head_h / 2, 16 * S, width=2 * S)
    d.text((pad + 50 * S, pad + head_h / 2), 'ZERO LINE', font=P.font('din', 24 * S, 'Bold'), fill=WHITE, anchor='lm')
    d.text((W / 2, pad + head_h / 2), 'DEPARTURES', font=P.font('din', 26 * S, 'Bold'), fill=WHITE, anchor='mm')
    # column labels
    cols = [('TIME', 5), ('DESTINATION', 14), ('PLAT', 1), ('REMARKS', 17)]
    cell_w, cell_h, gap = 22.5 * S, 36 * S, 2 * S
    col_gap = 14 * S
    x0 = pad + 12 * S
    y_lab = pad + head_h + 6 * S
    lab_font = P.font('din', 11 * S, 'Bold')
    xs = []
    x = x0
    for name, n in cols:
        xs.append(x)
        d.text((x, y_lab), name, font=lab_font, fill=YELLOW, anchor='la')
        x += n * (cell_w + gap) + col_gap
    # the stopped clock: four flaps on the right of the header
    flap_font = P.font('din', int(cell_h * 0.78), 'Bold Condensed')

    def flap(x, y, ch, cw=cell_w, chh=cell_h, state='ok'):
        top = (40, 40, 44)
        bot = (28, 28, 31)
        d.rectangle([x, y, x + cw, y + chh / 2], fill=top)
        d.rectangle([x, y + chh / 2, x + cw, y + chh], fill=bot)
        if state == 'missing':
            d.rectangle([x, y, x + cw, y + chh], fill=(8, 8, 9))
            d.line([(x + cw * 0.15, y + chh / 2), (x + cw * 0.85, y + chh / 2)], fill=(70, 70, 70), width=S)
            return
        if ch.strip():
            layer = Image.new('L', (int(cw), int(chh)), 0)
            ImageDraw.Draw(layer).text((cw / 2, chh / 2 + S), ch, font=flap_font, fill=255, anchor='mm')
            col = (238, 232, 214)
            if state == 'stuck':     # upper half shows the next card turning: squashed and darker
                upper = layer.crop((0, 0, int(cw), int(chh / 2))).resize((int(cw), int(chh * 0.22)))
                lower = layer.crop((0, int(chh / 2), int(cw), int(chh)))
                layer = Image.new('L', (int(cw), int(chh)), 0)
                layer.paste(lower, (0, int(chh / 2)))
                layer.paste(upper, (0, int(chh / 2 - chh * 0.22)))
                d.rectangle([x, y, x + cw, y + chh / 2 - chh * 0.22], fill=(10, 10, 11))
                col = (200, 196, 182)
            im.paste(Image.new('RGB', layer.size, col), (int(x), int(y)), layer)
        d.line([(x, y + chh / 2), (x + cw, y + chh / 2)], fill=(6, 6, 7), width=int(1.6 * S))
        d.rectangle([x, y, x + cw, y + chh], outline=(10, 10, 12), width=S)

    cx = W - pad - 4 * (24 * S) - 22 * S
    for i, ch in enumerate(clock):
        if ch == ':':
            d.text((cx + i * 24 * S + 7 * S, pad + head_h / 2), ':', font=P.font('din', 26 * S, 'Bold'), fill=WHITE,
                   anchor='mm')
            continue
        flap(cx + i * 24 * S, pad + 5 * S, ch, cw=22 * S, chh=head_h - 10 * S)
    y = y_lab + 16 * S
    stuck = (1, 3, 9)          # row, column group, char index
    missing = (2, 1, 11)
    for ri, row in enumerate(rows):
        for ci, ((name, n), text) in enumerate(zip(cols, row)):
            t = text.ljust(n)[:n]
            for k, ch in enumerate(t):
                state = 'stuck' if (ri, ci, k) == stuck else 'missing' if (ri, ci, k) == missing else 'ok'
                flap(xs[ci] + k * (cell_w + gap), y, ch, state=state)
        y += cell_h + 5 * S
    small = im.resize((w, h), Image.LANCZOS)
    rgb = np.asarray(small, np.float32) / 255
    # housing wear and the cover glass: dust, grime at the edges, a fingerprint-y smear, faint reflection
    ov = M.sign_grime_overlay(w, h, seed + 1)
    rgb = overlay(rgb, ov, 0.55)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    refl = N.smoothstep(0.0, 1.0, 1 - np.abs((xx / w - yy / h * 0.6) - 0.45) / 0.12) * 0.05
    rgb = np.clip(rgb + refl[..., None], 0, 1)
    return rgb.astype(np.float32)


# ------------------------------------------------------------------------- signal & evacuation diagram
def evac_signal_diagram(w=1024, h=512, seed=4753):
    """Station Zero signal and evacuation diagram (control room wall): station plan from the level layout, the Zero
    Line track with its signals all lit red, the held train 047 at Platform A, green evacuation routes, legend. RGB."""
    S = 3
    W, H = w * S, h * S
    PANEL = (34, 46, 44)
    LINE = (226, 222, 206)
    im = Image.new('RGB', (W, H), PANEL)
    d = ImageDraw.Draw(im)
    title_h = 40 * S
    d.rectangle([0, 0, W, title_h], fill=NAVY)
    d.rectangle([0, title_h, W, title_h + 3 * S], fill=YELLOW)
    zero_badge(d, 24 * S, title_h / 2, 14 * S, width=2 * S)
    d.text((46 * S, title_h / 2), 'ZERO LINE  ·  STATION ZERO', font=P.font('din', 20 * S, 'Bold'), fill=WHITE,
           anchor='lm')
    d.text((W - 16 * S, title_h / 2), 'SIGNAL & EMERGENCY EVACUATION DIAGRAM', font=P.font('din', 17 * S, 'SemiBold'),
           fill=WHITE, anchor='rm')
    # level coordinates -> panel (north up). Map box x -3800..4000, y 1000..4600 into the plan area
    px0, py0, px1, py1 = 18 * S, title_h + 16 * S, W - 250 * S, H - 18 * S

    def P2(x, y):
        return (px0 + (x + 3800) / 7800 * (px1 - px0), py1 - (y - 1000) / 3600 * (py1 - py0))

    def room(x0, y0, x1, y1, label, fill=(44, 58, 56), hatch=False, lab_col=LINE, size=10, at=None):
        a, b = P2(x0, y1), P2(x1, y0)
        d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=LINE, width=int(1.5 * S))
        if hatch:
            for k in range(int(a[0] - (b[1] - a[1])), int(b[0]), 9 * S):
                d.line([(max(k, a[0]), a[1] + max(0, a[0] - k)), (min(k + (b[1] - a[1]), b[0]), b[1] - max(0, k + (b[1] - a[1]) - b[0]))],
                       fill=(70, 84, 80), width=S)
        if label:
            lines = label.split('\n')
            fz = P.font('din', size * S, 'SemiBold')
            lx, ly = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) if at is None else P2(*at)
            cy = ly - (len(lines) - 1) * size * S * 0.6
            for i, ln in enumerate(lines):
                d.text((lx, cy + i * size * S * 1.2), ln, font=fz, fill=lab_col, anchor='mm')

    room(-1200, 3200, 400, 4400, 'TICKET HALL')
    room(-800, 2400, -400, 3200, 'STAIR\nA', size=9, at=(-500, 2950))
    room(-1600, 3240, -1200, 3560, 'STAIR B', size=7, at=(-1400, 3490))
    room(-2400, 1600, 2400, 2400, 'PLATFORM A', at=(1100, 2200))
    room(2400, 1680, 3200, 1920, 'MAINT.', size=8)
    room(2960, 1920, 3200, 2400, '', size=8)
    room(2600, 2400, 3800, 3200, 'GENERATOR\nROOM')
    room(2600, 3200, 3600, 4000, 'SIGNAL\nCONTROL', fill=(58, 52, 40), lab_col=(255, 214, 120))
    room(-3600, 2600, -1600, 3400, 'OLD STATION\nCLOSED', hatch=True)
    room(-3600, 1600, -3200, 2600, '', hatch=False)
    # track: platform A road through the pit, west into the service tunnel to the buffer stop, east into the tunnel
    ty = 1488
    a, b = P2(-3600, ty), P2(3990, ty)
    d.rectangle([a[0], a[1] - 2.5 * S, b[0], a[1] + 2.5 * S], fill=LINE)
    tun_a, tun_b = P2(-3600, 1200), P2(-2400, 1600)
    d.rectangle([tun_a[0], tun_b[1], tun_b[0], tun_a[1]], outline=LINE, width=int(1.5 * S))
    d.text((P2(-3000, 1300)), 'SERVICE TUNNEL', font=P.font('din', 9 * S, 'SemiBold'), fill=LINE, anchor='mm')
    bs = P2(-3600, ty)
    d.rectangle([bs[0] - 2 * S, bs[1] - 9 * S, bs[0] + 3 * S, bs[1] + 9 * S], fill=RED)          # buffer stop
    # the old station's disused road (dashed)
    ob0, ob1 = P2(-3600, 2700), P2(-1600, 2700)
    for k in np.arange(ob0[0], ob1[0], 14 * S):
        d.line([(k, ob0[1]), (min(k + 8 * S, ob1[0]), ob0[1])], fill=(150, 150, 140), width=int(2 * S))
    # track circuits: insulated joints (ticks) and section names
    for i, x in enumerate((-2400, -1200, 0, 1200, 2400, 3400)):
        p = P2(x, ty)
        d.line([(p[0], p[1] - 6 * S), (p[0], p[1] + 6 * S)], fill=(14, 18, 18), width=int(2 * S))
    for i, x in enumerate((-3000, -1800, -600, 600, 1800, 2900, 3700)):
        p = P2(x, ty)
        d.text((p[0], p[1] + 12 * S), 'Z%d' % (10 + i), font=P.font('din', 8 * S, 'SemiBold'), fill=(180, 186, 176), anchor='mm')
    # train 047 held at platform A: amber occupied section lamps and a train describer box
    for x in np.arange(-1150, 1150, 140):
        p = P2(x, ty)
        d.ellipse([p[0] - 3.2 * S, p[1] - 3.2 * S, p[0] + 3.2 * S, p[1] + 3.2 * S], fill=(255, 176, 40))
    tb = P2(-160, 1300)
    d.rectangle([tb[0] - 30 * S, tb[1] - 9 * S, tb[0] + 30 * S, tb[1] + 9 * S], fill=(12, 12, 12), outline=LINE, width=S)
    d.text(tb, '0 4 7', font=P.font('din', 13 * S, 'Bold'), fill=(255, 176, 40), anchor='mm')
    # signals: post + lamp, every one lit red
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for i, (x, side) in enumerate(((-3300, -1), (-2300, -1), (-1150, 1), (1250, -1), (2350, 1), (3500, 1))):
        p = P2(x, ty)
        sy = p[1] + side * 18 * S
        d.line([(p[0], p[1] + side * 3 * S), (p[0], sy)], fill=LINE, width=int(1.5 * S))
        d.line([(p[0], sy), (p[0] + 10 * S, sy)], fill=LINE, width=int(1.5 * S))
        lx = p[0] + 16 * S
        d.ellipse([lx - 6 * S, sy - 6 * S, lx + 6 * S, sy + 6 * S], fill=(255, 40, 30), outline=(20, 10, 10), width=S)
        gd.ellipse([lx - 12 * S, sy - 12 * S, lx + 12 * S, sy + 12 * S], fill=200)
        d.text((lx, sy + side * 13 * S), 'S%d' % (i + 1), font=P.font('din', 8 * S, 'Bold'), fill=(230, 210, 200), anchor='mm')
    # evacuation routes: green arrows toward the street exits from the ticket hall
    G = (70, 200, 100)

    def arrow(pts, col=G):
        d.line(pts, fill=col, width=int(3 * S), joint='curve')
        (xa, ya), (xb, yb) = pts[-2], pts[-1]
        ang = math.atan2(yb - ya, xb - xa)
        L = 9 * S
        d.polygon([(xb + math.cos(ang) * L * 0.6, yb + math.sin(ang) * L * 0.6),
                   (xb + math.cos(ang + 2.4) * L, yb + math.sin(ang + 2.4) * L),
                   (xb + math.cos(ang - 2.4) * L, yb + math.sin(ang - 2.4) * L)], fill=col)

    arrow([P2(400, 1900), P2(-700, 1900), P2(-700, 2900), P2(-700, 3550)])
    arrow([P2(-2200, 3000), P2(-1450, 3000), P2(-1450, 3330), P2(-1150, 3330)])
    arrow([P2(3100, 3600), P2(3100, 3250)])
    arrow([P2(3500, 2560), P2(3080, 2560), P2(3080, 2050), P2(2300, 1800), P2(500, 1800)])
    arrow([P2(-400, 4000), P2(-400, 4520)])
    ex = P2(-400, 4560)
    d.rectangle([ex[0] - 22 * S, ex[1] - 6 * S, ex[0] + 22 * S, ex[1] + 7 * S], fill=G)
    d.text(ex, 'EXIT', font=P.font('din', 10 * S, 'Bold'), fill=(10, 30, 14), anchor='mm')
    yah = P2(3350, 3800)
    d.ellipse([yah[0] - 5 * S, yah[1] - 5 * S, yah[0] + 5 * S, yah[1] + 5 * S], fill=RED, outline=WHITE, width=S)
    d.text((yah[0] - 8 * S, yah[1]), 'YOU ARE HERE', font=P.font('din', 8 * S, 'Bold'), fill=(255, 214, 120), anchor='rm')
    # legend panel
    lx0 = W - 236 * S
    d.rectangle([lx0, title_h + 16 * S, W - 14 * S, H - 18 * S], fill=(26, 34, 33), outline=LINE, width=S)
    lf = P.font('din', 11 * S, 'SemiBold')
    hf = P.font('din', 12 * S, 'Bold')
    y = title_h + 30 * S
    d.text((lx0 + 12 * S, y), 'KEY', font=hf, fill=YELLOW, anchor='lm')
    y += 22 * S
    items = [('lamp', 'SIGNAL AT DANGER'), ('amber', 'TRACK SECTION OCCUPIED'), ('track', 'ZERO LINE RUNNING ROAD'),
             ('dash', 'DISUSED ROAD (OLD STATION)'), ('arrow', 'EVACUATION ROUTE'), ('hatch', 'CLOSED TO PASSENGERS')]
    for kind, text in items:
        ix = lx0 + 20 * S
        if kind == 'lamp':
            d.ellipse([ix - 6 * S, y - 6 * S, ix + 6 * S, y + 6 * S], fill=(255, 40, 30))
        elif kind == 'amber':
            d.ellipse([ix - 4 * S, y - 4 * S, ix + 4 * S, y + 4 * S], fill=(255, 176, 40))
        elif kind == 'track':
            d.rectangle([ix - 10 * S, y - 2 * S, ix + 10 * S, y + 2 * S], fill=LINE)
        elif kind == 'dash':
            d.line([(ix - 10 * S, y), (ix - 2 * S, y)], fill=(150, 150, 140), width=2 * S)
            d.line([(ix + 3 * S, y), (ix + 10 * S, y)], fill=(150, 150, 140), width=2 * S)
        elif kind == 'arrow':
            d.line([(ix - 10 * S, y), (ix + 6 * S, y)], fill=G, width=3 * S)
            d.polygon([(ix + 11 * S, y), (ix + 4 * S, y - 5 * S), (ix + 4 * S, y + 5 * S)], fill=G)
        elif kind == 'hatch':
            d.rectangle([ix - 10 * S, y - 6 * S, ix + 10 * S, y + 6 * S], fill=(44, 58, 56), outline=LINE, width=S)
            for k in range(-10, 10, 5):
                d.line([(ix + k * S, y + 6 * S), (ix + (k + 6) * S, y - 6 * S)], fill=(90, 104, 100), width=S)
        d.text((ix + 20 * S, y), text, font=lf, fill=LINE, anchor='lm')
        y += 24 * S
    y += 6 * S
    notes = ['IN AN EMERGENCY ALL SIGNALS', 'RETURN TO DANGER.', 'DO NOT CLEAR A SIGNAL WITHOUT', 'THE AUTHORITY OF CONTROL.']
    nf = P.font('din', 9 * S, 'SemiBold')
    for n in notes:
        d.text((lx0 + 12 * S, y), n, font=nf, fill=(200, 196, 182), anchor='lm')
        y += 13 * S
    d.text((lx0 + 12 * S, H - 30 * S), 'DIAGRAM SZ-02  REV. 4', font=P.font('din', 9 * S, 'Bold'), fill=(160, 160, 150),
           anchor='lm')
    glow = glow.filter(ImageFilter.GaussianBlur(8 * S))
    im = Image.composite(Image.new('RGB', (W, H), (255, 70, 50)), im,
                         Image.fromarray((np.asarray(glow, np.float32) * 0.35).astype(np.uint8)))
    rgb = np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255
    # enamel panel ageing: grime overlay, a few chips, faint fading toward the bottom right
    rgb = overlay(rgb, M.sign_grime_overlay(w, h, seed + 1), 0.6)
    r = np.random.default_rng(seed + 2)
    chip = Image.new('L', (w, h), 0)
    cd = ImageDraw.Draw(chip)
    for _ in range(14):
        side = r.integers(4)
        x = r.uniform(0, w) if side < 2 else (r.uniform(2, 14) if side == 2 else w - r.uniform(2, 14))
        y = r.uniform(0, h) if side >= 2 else (r.uniform(2, 14) if side == 0 else h - r.uniform(2, 14))
        rr = r.uniform(1.5, 4.0)
        cd.polygon([(x + math.cos(a) * rr * r.uniform(0.6, 1.4), y + math.sin(a) * rr * r.uniform(0.6, 1.4))
                    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)], fill=255)
    cm = np.asarray(chip, np.float32)[..., None] / 255
    rgb = rgb * (1 - cm) + np.array([0.20, 0.20, 0.22]) * cm
    return np.clip(rgb, 0, 1).astype(np.float32)
