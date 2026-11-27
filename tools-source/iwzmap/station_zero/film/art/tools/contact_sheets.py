"""Contact sheets at relative in-game sizes (units x scale) on mid-grey, one per brand plus the hall and the Terminus.

usage: python contact_sheets.py [px_per_unit=3]
"""
import pathlib, sys
from PIL import Image, ImageDraw
from artlib import ARCADE, TERMINUS

OUT = pathlib.Path("C:/studio-data/sz/film/art/_sheets")
K = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0

SETS = {
    "needle_drop": [("logo_needle_drop", 24, 24), ("fascia_needle_drop", 300, 68), ("door_card_needle_drop", 10, 7)],
    "copy_stop": [("logo_copy_stop", 24, 24), ("fascia_copy_stop_left", 150, 68), ("fascia_copy_stop", 310, 68),
                  ("fascia_copy_stop_right", 150, 68), ("door_card_copy_stop", 10, 7), ("board_copy_stop", 60, 44)],
    "hole_nine": [("logo_hole_nine", 24, 24), ("fascia_hole_nine", 300, 68), ("door_card_hole_nine", 10, 7),
                  ("menu_hole_nine", 60, 44), ("today_hole_nine", 60, 44)],
    "heel_key": [("logo_heel_key", 24, 24), ("fascia_heel_key", 300, 68), ("door_card_heel_key", 10, 7),
                 ("board_heel_key", 60, 44)],
    "hall": [("directory_board", 120, 160), ("lightbox_orbit", 64, 96), ("lightbox_lodestar", 64, 96),
             ("lightbox_zero_line", 64, 96), ("lightbox_channel9", 64, 96), ("poster_station_zero", 64, 96),
             ("notice_1", 16, 22), ("notice_2", 16, 22), ("notice_3", 16, 22), ("notice_4", 16, 22),
             ("banner_new_year", 320, 48), ("bunting_strip", 256, 24), ("floor_polish_circle", 220, 220)],
    "terminus": [("sign_terminus", 144, 28), ("sign_fare_validation", 64, 16), ("paper_times_column", 48, 192),
                 ("screen_second_platform", 384, 216), ("pictogram_validate", 24, 24), ("footprints_printed", 96, 96),
                 ("footprints_fresh", 24, 24)] + [(f"leader_{n}", 24, 24) for n in range(8, 1, -1)]
                + [("paper_greenbar_tile", 128, 128), ("paper_greenbar_edge", 128, 16)],
}


def find(name):
    for d in (ARCADE, TERMINUS):
        p = d / f"{name}.png"
        if p.exists():
            return p


def sheet(key, items, maxw=1900):
    tiles = []
    for name, uw, uh in items:
        p = find(name)
        if not p:
            continue
        im = Image.open(p).convert("RGBA").resize((max(1, int(uw * K)), max(1, int(uh * K))), Image.LANCZOS)
        tiles.append((name, im))
    rows, row, w = [], [], 0
    for t in tiles:
        if row and w + t[1].width + 24 > maxw:
            rows.append(row); row, w = [], 0
        row.append(t); w += t[1].width + 24
    rows.append(row)
    H = sum(max(t[1].height for t in r) + 40 for r in rows) + 20
    W = min(maxw, max(sum(t[1].width + 24 for t in r) for r in rows) + 24)
    s = Image.new("RGB", (W, H), (128, 128, 128))
    d = ImageDraw.Draw(s)
    y = 20
    for r in rows:
        x = 24
        for name, im in r:
            s.paste(im, (x, y + 16), im)
            d.text((x, y), name, fill=(255, 255, 255))
            x += im.width + 24
        y += max(t[1].height for t in r) + 40
    s.save(OUT / f"sheet_{key}.jpg", quality=92)
    print(OUT / f"sheet_{key}.jpg", s.size, len(tiles), "pieces")


if __name__ == "__main__":
    for k, v in SETS.items():
        sheet(k, v)
