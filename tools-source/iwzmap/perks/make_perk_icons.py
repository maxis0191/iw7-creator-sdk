"""Draws the five perk HUD icons (128x128 RGBA TGA + PNG) and a review sheet.

Usage: python -I -B make_perk_icons.py <out dir>   (default: <script folder>\\icons)
Only Pillow and the standard library are used. Drawing happens at 4x and is
downsampled with LANCZOS.
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw

S = 4                      # supersampling factor
N = 128 * S                # work canvas
SW = 6                     # stroke width at 128 size

DISC = (0x0D, 0x12, 0x18, int(round(255 * 0.94)))
RING = (0x22, 0x30, 0x3D, 255)
BONE = (0xEE, 0xE7, 0xD7)
AMBER = (0xFF, 0xB2, 0x38)
GREEN = (0x6B, 0xE6, 0x75)
GREY = (0x8E, 0x94, 0x9C)


def sc(p):
    return (p[0] * S, p[1] * S)


def new_mask():
    m = Image.new("L", (N, N), 0)
    return m, ImageDraw.Draw(m)


def stroke(d, pts, w=SW, closed=False):
    pts = [sc(p) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    r = w * S / 2.0
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=int(round(w * S)))
    for p in pts:
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)


def arc_pts(cx, cy, rx, ry, a0, a1, n=72):
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return out


def circle_pts(cx, cy, r, n=120):
    return arc_pts(cx, cy, r, r, 0, 360, n)[:-1]


def dashed(d, pts, closed=True, on=2.0, period=11.0, w=SW):
    pts = list(pts)
    if closed:
        pts = pts + [pts[0]]
    segs = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((total, ln, a, b))
        total += ln

    def at(t):
        t = min(max(t, 0.0), total)
        for s0, ln, a, b in segs:
            if t <= s0 + ln or (s0, ln) == (segs[-1][0], segs[-1][1]):
                f = 0 if ln == 0 else (t - s0) / ln
                return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        return pts[-1]

    n_dash = max(1, int(round(total / period)))
    per = total / n_dash
    for i in range(n_dash):
        s = i * per + (per - on) / 2.0
        k = max(2, int(on / 0.5) + 1)
        seg = [at(s + on * j / (k - 1)) for j in range(k)]
        stroke(d, seg, w)


def fill_poly(d, pts):
    d.polygon([sc(p) for p in pts], fill=255)


def fill_circle(d, c, r):
    x, y = sc(c)
    rr = r * S
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)


def base_badge():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = N // 2
    ro = 60 * S
    ri = 56 * S
    d.ellipse([c - ro, c - ro, c + ro, c + ro], fill=RING)
    d.ellipse([c - ri, c - ri, c + ri, c + ri], fill=DISC)
    return img


# ---------------------------------------------------------------- icons
def icon_bakers():
    bone, bd = new_mask()
    acc, ad = new_mask()
    # bag body: tapering, zig-zag top
    zig = [(42, 46), (53, 40), (64, 46), (75, 40), (86, 46)]
    body = [(38, 92)] + zig + [(90, 92)]
    stroke(bd, body, closed=True)
    # digits "13"
    stroke(bd, [(46, 62), (52, 56), (52, 82)])          # 1
    stroke(bd, arc_pts(71, 62, 6.5, 6.5, 200, 450, 40))  # 3 upper bowl
    stroke(bd, arc_pts(71, 75, 6.5, 6.5, 270, 520, 40))  # 3 lower bowl
    # amber drop with a point on top
    fill_circle(ad, (92, 33), 6.5)
    fill_poly(ad, [(92, 20), (97.6, 29.5), (86.4, 29.5)])
    return bone, acc


def icon_voyage():
    bone, bd = new_mask()
    acc, ad = new_mask()
    stroke(bd, circle_pts(64, 64, 36), closed=True)
    stroke(bd, circle_pts(64, 64, 22), closed=True)
    ang = math.radians(60)  # 2 o'clock, clockwise from 12
    tip = (64 + 14 * math.sin(ang), 64 - 14 * math.cos(ang))
    stroke(ad, [(64, 64), tip])
    fill_circle(ad, (64, 64), 5.5)
    return bone, acc


def icon_grudge():
    bone, bd = new_mask()
    acc, ad = new_mask()
    fx, fy = 56, 71
    stroke(bd, circle_pts(fx, fy, 27), closed=True)
    for ex in (fx - 10, fx + 10):
        ey = fy - 8
        stroke(bd, [(ex - 4.5, ey - 4.5), (ex + 4.5, ey + 4.5)])
        stroke(bd, [(ex - 4.5, ey + 4.5), (ex + 4.5, ey - 4.5)])
    mouth = []
    for i in range(41):
        t = i / 40.0
        x = fx - 8 + 16 * t
        y = fy + 12 + 2.6 * math.sin(t * math.pi * 3)
        mouth.append((x, y))
    stroke(bd, mouth)
    # cloud (three bumps on a flat base), green accent
    fill_circle(ad, (83, 41), 5.5)
    fill_circle(ad, (91, 35), 8)
    fill_circle(ad, (99, 41), 5.5)
    fill_poly(ad, [(83, 35.5), (99, 35.5), (99, 46.5), (83, 46.5)])
    return bone, acc


def person(cx, cy):
    head = circle_pts(cx, cy, 8)
    sh = arc_pts(cx, cy + 36, 20, 16, 180, 360, 60)
    return head, sh


def icon_double(parts=False):
    bone, bd = new_mask()
    acc, ad = new_mask()
    # rear person (dashed), offset up and right
    rear, rd = new_mask()
    h, sh = person(68, 36)
    dashed(rd, h, closed=True)
    dashed(rd, sh, closed=True)
    # front person (solid), lower left
    fh, fsh = person(44, 54)
    # knock the rear outlines out of the front person's area (+ margin)
    ko, kd = new_mask()
    stroke(kd, fh, w=SW + 4, closed=True)
    fill_poly(kd, fh)
    stroke(kd, fsh, w=SW + 4, closed=True)
    fill_poly(kd, fsh)
    rear = ImageChops.subtract(rear, ko)
    bone = ImageChops.lighter(bone, rear)
    stroke(bd, fh, closed=True)
    stroke(bd, fsh, closed=True)
    bone = ImageChops.lighter(bone, bd._image if hasattr(bd, "_image") else bone)
    # flash star: 4 rays
    cx, cy, R, r = 92, 31, 9.5, 3.2
    star = []
    for i in range(8):
        a = math.radians(-90 + 45 * i)
        rad = R if i % 2 == 0 else r
        star.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    fill_poly(ad, star)
    return bone, acc


def compose(bone, acc, bone_col, acc_col, alpha_mul=1.0):
    img = base_badge()
    img.paste(bone_col + (255,), mask=bone)
    img.paste(acc_col + (255,), mask=acc)
    out = img.resize((128, 128), Image.LANCZOS)
    if alpha_mul != 1.0:
        r, g, b, a = out.split()
        a = a.point(lambda v: int(round(v * alpha_mul)))
        out = Image.merge("RGBA", (r, g, b, a))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "icons")
    os.makedirs(out, exist_ok=True)

    icons = {}
    b, a = icon_bakers()
    icons["iwz_perk_icon_bakers"] = compose(b, a, BONE, AMBER)
    b, a = icon_voyage()
    icons["iwz_perk_icon_voyage"] = compose(b, a, BONE, AMBER)
    b, a = icon_grudge()
    icons["iwz_perk_icon_grudge"] = compose(b, a, BONE, GREEN)
    b, a = icon_double()
    icons["iwz_perk_icon_double"] = compose(b, a, BONE, AMBER)
    icons["iwz_perk_icon_double_cd"] = compose(b, a, GREY, GREY, 0.6)

    for name, im in icons.items():
        im.save(os.path.join(out, name + ".tga"), format="TGA")
        im.save(os.path.join(out, name + ".png"), format="PNG")

    pad = 24
    names = list(icons)
    W = len(names) * 256 + (len(names) + 1) * pad
    H = pad + 256 + pad + 32 + pad
    sheet = Image.new("RGBA", (W, H), (0x3A, 0x3F, 0x46, 255))
    for i, name in enumerate(names):
        x = pad + i * (256 + pad)
        big = icons[name].resize((256, 256), Image.LANCZOS)
        sheet.alpha_composite(big, (x, pad))
        small = icons[name].resize((32, 32), Image.LANCZOS)
        sheet.alpha_composite(small, (x + 112, pad + 256 + pad))
    sheet.save(os.path.join(out, "icons_sheet.png"), format="PNG")

    for name in names:
        t = Image.open(os.path.join(out, name + ".tga"))
        t.load()
        corners = [t.getpixel(p)[3] for p in ((0, 0), (127, 0), (0, 127), (127, 127))]
        print(name, t.size, t.mode, "corner alpha", corners,
              "tga bytes", os.path.getsize(os.path.join(out, name + ".tga")),
              "png bytes", os.path.getsize(os.path.join(out, name + ".png")))
    print("sheet bytes", os.path.getsize(os.path.join(out, "icons_sheet.png")))


if __name__ == "__main__":
    main()
