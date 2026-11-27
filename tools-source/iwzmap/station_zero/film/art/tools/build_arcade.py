"""Arcade compositions: fascias, side panels, directory board, bunting, finishing of generated pieces.

usage: python build_arcade.py [step ...]   (no step = all steps whose inputs exist)
Fonts used (C:/Windows/Fonts): bahnschrift.ttf (variable; 'Bold Condensed', 'SemiBold Condensed', 'Bold').
"""
import json, math, pathlib, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from artlib import RAW, ARCADE, snap_alpha, bbox_crop, contain, cover
from terminus_paper import periodic_noise

COPY = json.loads(pathlib.Path("C:/studio-data/sz/film/copy/arcade_copy_raw.txt").read_text(encoding="utf-8"))
BAHN = "C:/Windows/Fonts/bahnschrift.ttf"

C = {
    "needle_drop": {"field": (17, 17, 17), "ink": (255, 90, 20)},
    "copy_stop": {"field": (0, 133, 202), "ink": (255, 255, 255)},
    "hole_nine": {"field": (244, 143, 177), "ink": (78, 42, 30)},
    "heel_key": {"field": (107, 30, 35), "ink": (242, 230, 201)},
}


def bahn(size, var="Bold Condensed"):
    f = ImageFont.truetype(BAHN, size)
    f.set_variation_by_name(var)
    return f


def painted_field(size, rgb, seed, strength=4.0):
    """A screen-printed / painted panel: flat colour, faint brush and grain, slightly worn edges. No light gradient."""
    W, H = size
    n = 0.6 * periodic_noise(H, W, 30.0, 3.0, seed) + 0.4 * periodic_noise(H, W, 400.0, 400.0, seed + 1)
    arr = np.array(rgb, float)[None, None, :] + strength * n[..., None]
    rng = np.random.default_rng(seed)
    edge = np.zeros((H, W))
    for _ in range(int((W + H) / 40)):  # small chips along the border
        side = rng.integers(4)
        r = rng.uniform(1.5, 5.0)
        x = rng.uniform(0, W) if side < 2 else (rng.uniform(0, 4) if side == 2 else W - rng.uniform(0, 4))
        y = rng.uniform(0, H) if side >= 2 else (rng.uniform(0, 4) if side == 0 else H - rng.uniform(0, 4))
        yy, xx = np.ogrid[:H, :W]
        edge = np.maximum(edge, ((xx - x) ** 2 + (yy - y) ** 2 < r * r).astype(float))
    arr = arr * (1 - 0.25 * edge[..., None]) + 0.25 * edge[..., None] * np.array([90, 88, 84])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def text_layer(text, font, fill, pad=20):
    l, t, r, b = font.getbbox(text)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=font, fill=fill)
    return im


def oblique(im, k=0.2):
    W, H = im.size
    out = im.transform((W + int(k * H) + 2, H), Image.AFFINE, (1, k, -k * H, 0, 1, 0), Image.BICUBIC)
    return out


def logo(shop, px):
    im = Image.open(ARCADE / f"logo_{shop}.png").convert("RGBA")
    return im.resize((px, px), Image.LANCZOS)


# ---------------------------------------------------------------- Copy Stop
def fascia_copy_stop():
    W, H = 1024, 225  # 310 x 68 units
    f = painted_field((W, H), C["copy_stop"]["field"], 31)
    d = ImageDraw.Draw(f)
    tile = 185
    d.rounded_rectangle([20, 20, 20 + tile, 20 + tile], 14, fill=(255, 255, 255, 255))
    f.alpha_composite(logo("copy_stop", tile - 24), (32, 32))
    word = oblique(text_layer("COPY STOP", bahn(190), (255, 255, 255, 255)), 0.21)
    word = word.resize((int(word.width * 168 / word.height), 168), Image.LANCZOS) if word.height > 168 else word
    ghost = word.copy()
    ga = np.array(ghost); ga[..., 3] = (ga[..., 3] * 0.33).astype(np.uint8); ghost = Image.fromarray(ga)
    x = 20 + tile + 34 + max(0, (W - 20 - tile - 34 - 24 - word.width) // 2)
    y = (H - word.height) // 2 + 6
    f.alpha_composite(ghost, (x + 10, y - 7))  # the second impression, out of register like the mark
    f.alpha_composite(word, (x, y))
    f.convert("RGB").save(ARCADE / "fascia_copy_stop.png")
    return word.width


def side_panel(lines, name, seed):
    W, H = 1024, 464  # 150 x 68 units
    f = painted_field((W, H), C["copy_stop"]["field"], seed)
    d = ImageDraw.Draw(f)
    d.rectangle([28, 28, W - 28, H - 28], outline=(255, 255, 255, 255), width=8)
    ys = [70, 262]
    for (l1, y) in zip(lines, ys):
        t = oblique(text_layer(l1, bahn(130), (255, 255, 255, 255)), 0.21)
        if t.width > W - 120:
            t = t.resize((W - 120, int(t.height * (W - 120) / t.width)), Image.LANCZOS)
        f.alpha_composite(t, ((W - t.width) // 2, y + (130 - t.height) // 2 + 20))
    d.line([(120, H // 2), (W - 120, H // 2)], fill=(255, 255, 255, 255), width=5)
    f.convert("RGB").save(ARCADE / name)


def copy_stop_panels():
    wc = COPY["window_cards"]["copy_stop"]
    # words: the copy file's window card headings (copy key window_cards.copy_stop[i][0])
    side_panel([wc[0][0], wc[1][0]], "fascia_copy_stop_left.png", 41)
    side_panel([wc[2][0], wc[3][0]], "fascia_copy_stop_right.png", 42)


# ---------------------------------------------------------------- the three generated wordmarks
def fascia_from_wordmark(shop, raw, W=1024, H=232, tile_bg=None, seed=50):
    f = painted_field((W, H), C[shop]["field"], seed)
    mark_px = H - 36
    m = logo(shop, mark_px)
    if tile_bg is not None:
        d = ImageDraw.Draw(f)
        d.ellipse([14, 14, 14 + mark_px + 8, 14 + mark_px + 8], fill=tile_bg + (255,))
        f.alpha_composite(m, (18, 18))
    else:
        f.alpha_composite(m, (18, 18))
    wm = bbox_crop(snap_alpha(Image.open(RAW / raw)))
    # recolour to the brand ink exactly (the generator's flat colour drifts a little)
    a = np.array(wm); a[..., :3] = C[shop]["ink"]; wm = Image.fromarray(a)
    avail_w, avail_h = W - mark_px - 18 - 60, H - 40
    s = min(avail_w / wm.width, avail_h / wm.height)
    wm = wm.resize((int(wm.width * s), int(wm.height * s)), Image.LANCZOS)
    x = mark_px + 18 + 30 + (avail_w - wm.width) // 2
    f.alpha_composite(wm, (x, (H - wm.height) // 2))
    f.convert("RGB").save(ARCADE / f"fascia_{shop}.png")


# ---------------------------------------------------------------- directory (HRT style)
def hrt_disc(px, bar=(0, 0, 0)):
    S = 4
    im = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, px * S - 1, px * S - 1], fill=(255, 255, 255, 255))
    bw, bh = px * S * 0.70, px * S * 0.16  # the held breath: a bar that does not reach the edges
    c = px * S / 2
    d.rectangle([c - bw / 2, c - bh / 2, c + bw / 2, c + bh / 2], fill=bar + (255,))
    return im.resize((px, px), Image.LANCZOS)


def directory():
    W, H = 768, 1024  # 120 x 160 units
    f = painted_field((W, H), (22, 23, 25), 61, strength=3.0)
    d = ImageDraw.Draw(f)
    f.alpha_composite(hrt_disc(92), (48, 52))
    hdr = COPY["directory"]["header"]
    sub = COPY["directory"]["subline"]
    t = text_layer(hdr, bahn(60, "Bold Condensed"), (255, 255, 255, 255), pad=0)
    if t.width > W - 210:
        t = t.resize((W - 210, int(t.height * (W - 210) / t.width)), Image.LANCZOS)
    f.alpha_composite(t, (162, 58))
    s = text_layer(sub, bahn(30, "SemiBold Condensed"), (205, 205, 200, 255), pad=0)
    if s.width > W - 210:
        s = s.resize((W - 210, int(s.height * (W - 210) / s.width)), Image.LANCZOS)
    f.alpha_composite(s, (164, 58 + t.height + 16))
    d.rectangle([48, 182, W - 48, 188], fill=(255, 255, 255, 255))
    shops = [("needle_drop", "NEEDLE DROP"), ("copy_stop", "COPY STOP"), ("hole_nine", "HOLE NUMBER NINE"),
             ("heel_key", "HEEL & KEY")]
    row_h, y0, tile = 180, 214, 148
    for i, (shop, name) in enumerate(shops):
        y = y0 + i * row_h
        d.rectangle([48, y, 48 + tile, y + tile], fill=(244, 242, 236, 255))
        f.alpha_composite(logo(shop, tile - 22), (59, y + 11))
        nm = text_layer(name, bahn(70, "SemiBold Condensed"), (255, 255, 255, 255), pad=0)
        if nm.width > W - 48 - tile - 40 - 48:
            nm = nm.resize((W - 48 - tile - 40 - 48, int(nm.height * (W - 48 - tile - 40 - 48) / nm.width)),
                           Image.LANCZOS)
        f.alpha_composite(nm, (48 + tile + 36, y + (tile - nm.height) // 2))
        if i < 3:
            d.rectangle([48, y + tile + 15, W - 48, y + tile + 17], fill=(110, 110, 108, 255))
    foot = text_layer("HALCYON RAPID TRANSIT", bahn(30, "Bold"), (205, 205, 200, 255), pad=0)
    f.alpha_composite(hrt_disc(34), (48, H - 66))
    f.alpha_composite(foot, (94, H - 66 + (34 - foot.height) // 2))
    for (x, y) in ((22, 22), (W - 22, 22), (22, H - 22), (W - 22, H - 22)):  # enamel fixing points
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(150, 150, 146, 255))
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(70, 70, 68, 255))
    f.convert("RGB").save(ARCADE / "directory_board.png")


# ---------------------------------------------------------------- bunting (tiles horizontally, period 1024)
def bunting():
    W, H, S = 1024, 96, 4
    cols = [(255, 90, 20), (242, 230, 201), (0, 133, 202), (244, 143, 177), (107, 30, 35), (242, 230, 201),
            (255, 90, 20), (0, 133, 202)]
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = random.Random(7)

    def sag(x):  # string: a scallop between hanging points every 128 px
        return (10 + 7 * math.sin(math.pi * ((x / S) % 128) / 128)) * S

    pts = [(x, sag(x)) for x in range(0, W * S + 1, 8)]
    for k, col in enumerate(cols):
        cx = (64 + 128 * k) * S
        top = sag(cx)
        hw, h = 50 * S, 76 * S
        sway = rng.uniform(-4, 4) * S
        d.polygon([(cx - hw, top), (cx + hw, top), (cx + sway, top + h)], fill=col + (255,))
    d.line(pts, fill=(235, 232, 222, 255), width=3 * S)
    out = im.resize((W, H), Image.LANCZOS)
    a = np.array(out).astype(float)
    n = periodic_noise(H, W, 8.0, 8.0, 3)  # paper grain, periodic so the tile still closes
    a[..., :3] = np.clip(a[..., :3] + 6 * n[..., None], 0, 255)
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    out.save(ARCADE / "bunting_strip.png")
    t = Image.new("RGBA", (W * 3, H), (128, 128, 128, 255))
    for i in range(3):
        t.alpha_composite(out, (i * W, 0))
    t.convert("RGB").save(ARCADE / "bunting_strip_tiletest.jpg", quality=92)


# ---------------------------------------------------------------- finishing of generated pieces
def finish_generated():
    for n in ("orbit", "lodestar", "zero_line", "channel9"):
        p = RAW / f"lightbox_{n}.png"
        if p.exists():
            cover(Image.open(p).convert("RGB"), (683, 1024)).save(ARCADE / f"lightbox_{n}.png")
    if (RAW / "banner_new_year.png").exists():
        b = bbox_crop(snap_alpha(Image.open(RAW / "banner_new_year.png")), pad=4)
        contain(b, (1024, 154)).save(ARCADE / "banner_new_year.png")
    if (RAW / "pictogram_validate.png").exists():
        p = bbox_crop(snap_alpha(Image.open(RAW / "pictogram_validate.png")), pad=2)
        contain(p, (192, 192), margin=2).save(pathlib.Path("C:/studio-data/sz/film/art/terminus/pictogram_validate.png"))
    for n, px in (("footprints_printed", 768), ("footprints_fresh", 192)):
        if (RAW / f"{n}.png").exists():
            p = bbox_crop(snap_alpha(Image.open(RAW / f"{n}.png")), pad=6)
            contain(p, (px, px), margin=4).save(pathlib.Path(f"C:/studio-data/sz/film/art/terminus/{n}.png"))


# ---------------------------------------------------------------- HRT notices (jobbing printer header, typewritten body)
def ink_on(paper, layer, seed):
    """Multiply a black ink layer onto paper with uneven density (letterpress / ribbon)."""
    p = np.array(paper.convert("RGB"), float)
    a = np.array(layer)[..., 3].astype(float) / 255
    H, W = a.shape
    dens = 0.88 + 0.12 * np.clip(periodic_noise(H, W, 120.0, 120.0, seed) * 0.5 + 0.5, 0, 1)
    speck = periodic_noise(H, W, 1.5, 1.5, seed + 5) > 2.2  # tiny ink-starved specks (fine-grain noise)
    a = a * dens * np.where(speck, 0.45, 1.0)
    ink = np.array([24, 22, 26], float)
    out = p * (1 - a[..., None]) + (p * ink / 255)[..., :] * a[..., None] * 0 + ink * a[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def notices():
    src = Image.open(RAW / "notice_paper.png").convert("RGB")
    W, H = 744, 1024  # composed at 2x, delivered 372 x 512 (16 x 22 units)
    cour = ImageFont.truetype("C:/Windows/Fonts/courbd.ttf", 40)
    for i, n in enumerate(COPY["arcade_notices"], 1):
        paper = src.transpose(Image.FLIP_LEFT_RIGHT) if i % 2 == 0 else src
        paper = paper.transpose(Image.FLIP_TOP_BOTTOM) if i > 2 else paper
        paper = cover(paper, (W, H), anchor=(0.5, 0.5))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        # the HRT mark in one-colour print: the white disc is the paper, held by a black keyline; the bar is black
        S4 = 4; D = 110 * S4
        mk = Image.new("RGBA", (D, D), (0, 0, 0, 0))
        md = ImageDraw.Draw(mk)
        md.ellipse([0, 0, D - 1, D - 1], outline=(0, 0, 0, 255), width=int(D * 0.07))
        bw, bh = D * 0.70, D * 0.16
        md.rectangle([D / 2 - bw / 2, D / 2 - bh / 2, D / 2 + bw / 2, D / 2 + bh / 2], fill=(0, 0, 0, 255))
        layer.alpha_composite(mk.resize((110, 110), Image.LANCZOS), (70, 80))
        d.rectangle([70 + 110 + 24, 112, W - 70, 124], fill=(0, 0, 0, 255))
        t = text_layer(n["title"], bahn(108, "Bold Condensed"), (0, 0, 0, 255), pad=0)
        if t.width > W - 140:
            t = t.resize((W - 140, int(t.height * (W - 140) / t.width)), Image.LANCZOS)
        layer.alpha_composite(t, (70, 240))
        d.rectangle([70, 240 + t.height + 34, W - 70, 240 + t.height + 40], fill=(0, 0, 0, 255))
        rng = random.Random(100 + i)
        y = 240 + t.height + 110
        for line in n["lines"]:
            x = 70
            for ch in line:
                if ch != " ":
                    g = Image.new("RGBA", (48, 60), (0, 0, 0, 0))
                    ImageDraw.Draw(g).text((4, 4), ch, font=cour, fill=(0, 0, 0, int(255 * rng.uniform(0.78, 1.0))))
                    layer.alpha_composite(g, (int(x) - 4, int(y + rng.uniform(-1.6, 1.6)) - 4))
                x += cour.getlength("M")
            y += 84
        out = ink_on(paper, layer, 70 + i).resize((372, 512), Image.LANCZOS)
        out.save(ARCADE / f"notice_{i}.png")


def door_cards():
    for shop in ("needle_drop", "copy_stop", "hole_nine", "heel_key"):
        im = Image.open(RAW / f"door_card_{shop}.png").convert("RGBA")
        if shop == "heel_key":
            # the tag's clipped corners and its eyelet hole came back as white background: key them out
            S = im.copy()
            for seed in ((2, 2), (2, im.height - 3), (im.width - 3, 2), (im.width - 3, im.height - 3)):
                ImageDraw.floodfill(S, seed, (255, 0, 255, 0), thresh=40)
            a = np.array(S)
            mask = (a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255)
            arr = np.array(im)
            rgb = arr[..., :3].astype(int)
            bright = (rgb.min(2) > 170) & ((rgb.max(2) - rgb.min(2)) < 32)  # grey, unlike the orange tag
            # the eyelet hole: bright pixels within the eyelet's box at the left middle
            hy, hx = int(im.height * 0.52), int(im.width * 0.045)
            yy, xx = np.ogrid[:im.height, :im.width]
            near = (np.abs(yy - hy) < im.height * 0.06) & (np.abs(xx - hx) < im.width * 0.04)
            arr[..., 3] = np.where(mask | (bright & near), 0, 255)
            im = Image.fromarray(arr)
        out = cover(im, (512, 358))
        (out if shop == "heel_key" else out.convert("RGB")).save(ARCADE / f"door_card_{shop}.png")


def boards():
    for n in ("board_copy_stop", "menu_hole_nine", "today_hole_nine", "board_heel_key"):
        cover(Image.open(RAW / f"{n}.png").convert("RGB"), (1024, 751)).save(ARCADE / f"{n}.png")


def fascias():
    # the record is black: on the black field it needs the orange disc behind it to exist
    fascia_from_wordmark("needle_drop", "wordmark_needle_drop-1.png", seed=51, tile_bg=(255, 90, 20))
    fascia_from_wordmark("hole_nine", "wordmark_hole_nine.png", seed=52, tile_bg=(250, 238, 228))
    fascia_from_wordmark("heel_key", "wordmark_heel_key.png", seed=53, tile_bg=(242, 230, 201))


def late():
    """Pieces whose generation waits for the generator quota (batch _raw/b05.json). Skips what is not there yet."""
    for shop in ("needle_drop", "copy_stop", "hole_nine", "heel_key"):
        p = RAW / f"window_cards_{shop}.png"
        if p.exists():
            contain(bbox_crop(snap_alpha(Image.open(p)), pad=4), (1024, 717)).save(ARCADE / f"window_cards_{shop}.png")
    for i in range(1, 9):
        p = RAW / f"sleeve_{i}.png"
        if p.exists():
            cover(Image.open(p).convert("RGB"), (256, 256)).save(ARCADE / f"sleeve_{i}.png")
    for i in range(1, 7):
        p = RAW / f"rental_{i}.png"
        if p.exists():
            cover(Image.open(p).convert("RGB"), (160, 256)).save(ARCADE / f"rental_{i}.png")


STEPS = {"copy_stop": lambda: (fascia_copy_stop(), copy_stop_panels()), "directory": directory, "bunting": bunting,
         "finish": finish_generated, "notices": notices, "door_cards": door_cards, "boards": boards,
         "fascias": fascias, "late": late}

if __name__ == "__main__":
    for s in (sys.argv[1:] or STEPS):
        STEPS[s]()
        print("done", s)
