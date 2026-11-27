"""Writes ../manifest.json: one record per delivered picture, measured from the file on disk.

usage: python manifest.py
Word sources: "canon" (01-LORE.md / the brief's canon list), "copy:<key path>" (arcade_copy_raw.txt), "PLACEHOLDER".
"""
import hashlib, json, pathlib
import numpy as np
from PIL import Image

ART = pathlib.Path("C:/studio-data/sz/film/art")
HERE = pathlib.Path(__file__).resolve().parent
COPYF = pathlib.Path("C:/studio-data/sz/film/copy/arcade_copy_raw.txt")
COPY = json.loads(COPYF.read_text(encoding="utf-8"))
PR = "tools-source/iwzmap/station_zero/film/art/prompts/"
TL = "tools-source/iwzmap/station_zero/film/art/tools/"


def W(text, src):
    return {"text": text, "source": src}


SHOPS = {"needle_drop": "NEEDLE DROP", "copy_stop": "COPY STOP", "hole_nine": "Hole Number Nine", "heel_key": "HEEL & KEY"}
items = []


def add(folder, file, units, brand, words, made, note, emissive=False, prompt=None):
    items.append(dict(folder=folder, file=file, units=units, brand=brand, words=words, made=made, prompt=prompt,
                      emissive=emissive, placement=note))


for s in SHOPS:
    add("arcade", f"logo_{s}.png", [None, None], s, [],
        "generator (transparent), alpha snapped, cropped and centred" if s != "copy_stop" else
        "drawn in PIL (two generator tries read as a computer file icon): build_marks.copy_stop_mark",
        "the mark alone: for any use at any size (bags, tags, decals, the directory); not a quad of its own size",
        prompt=PR + f"logo_{s}.prompt.txt" if s != "copy_stop" else None)

for s, name in SHOPS.items():
    if s == "copy_stop":
        continue
    add("arcade", f"fascia_{s}.png", [300, 68], s,
        [W(name, "canon"), W(COPY["fascia_tagline"][s], f"copy:fascia_tagline.{s}")],
        "PIL composition: painted field + accepted logo + generator wordmark (recoloured to the brand ink)",
        "hero sign: the fascia box over the front, 300 x 68, centre about +190 over the floor; lit from outside",
        prompt=PR + f"wordmark_{s}.prompt.txt")
add("arcade", "fascia_copy_stop.png", [310, 68], "copy_stop", [W("COPY STOP", "canon")],
    "PIL: Bahnschrift Bold Condensed slanted 12 degrees, second impression offset (the mark's idea)",
    "hero sign over the double front (U2+U3), 310 x 68, between the two side panels; lit from outside")
wc = COPY["window_cards"]["copy_stop"]
add("arcade", "fascia_copy_stop_left.png", [150, 68], "copy_stop",
    [W(wc[0][0], "copy:window_cards.copy_stop[0][0]"), W(wc[1][0], "copy:window_cards.copy_stop[1][0]")],
    "PIL: Bahnschrift Bold Condensed slanted", "left of fascia_copy_stop, same height and band")
add("arcade", "fascia_copy_stop_right.png", [150, 68], "copy_stop",
    [W(wc[2][0], "copy:window_cards.copy_stop[2][0]"), W(wc[3][0], "copy:window_cards.copy_stop[3][0]")],
    "PIL: Bahnschrift Bold Condensed slanted", "right of fascia_copy_stop, same height and band")

add("arcade", "directory_board.png", [120, 160], "HRT",
    [W(COPY["directory"]["header"], "copy:directory.header"), W(COPY["directory"]["subline"], "copy:directory.subline"),
     W("NEEDLE DROP / COPY STOP / HOLE NUMBER NINE / HEEL & KEY", "canon"), W("HALCYON RAPID TRANSIT", "canon")],
    "PIL: black enamel field, HRT disc, Bahnschrift (transit grotesque), the four accepted logos on white tiles",
    "south wall by entry D4, the hall's landmark (rule 25); enamel lit from outside, centre about +110")

for s in SHOPS:
    add("arcade", f"door_card_{s}.png", [10, 7], s,
        [W(" / ".join(COPY["door_card"][s]), f"copy:door_card.{s}")], "generator; spelling checked letter by letter",
        "taped inside the shop door's glass at eye level (+60); " + ("has alpha: clipped tag corners and eyelet hole" if s == "heel_key" else "opaque card"),
        prompt=PR + f"door_card_{s}.prompt.txt")

LB = {"orbit": ("Orbit Rink", 0), "lodestar": ("Lodestar", 1), "zero_line": ("Zero Line / HRT", 2),
      "channel9": ("Channel 9 Night Desk", 3)}
for n, (brand, i) in LB.items():
    ad = COPY["ad_lightboxes"][i]
    add("arcade", f"lightbox_{n}.png", [64, 96], brand,
        [W(ad["headline"], "canon" if n == "lodestar" else f"copy:ad_lightboxes[{i}].headline"),
         W(ad["line"], f"copy:ad_lightboxes[{i}].line")],
        "generator; text checked letter by letter on full-resolution crops",
        "south wall light box face, fully emissive (one radiance), in a box housing modelled by the 3D worker",
        emissive=True, prompt=PR + f"lightbox_{n}.prompt.txt")

for i, n in enumerate(COPY["arcade_notices"], 1):
    add("arcade", f"notice_{i}.png", [16, 22], "HRT",
        [W(n["title"], f"copy:arcade_notices[{i - 1}].title"),
         W(" / ".join(n["lines"]), f"copy:arcade_notices[{i - 1}].lines")],
        "PIL on generated blank paper: HRT disc in keyline, title Bahnschrift Bold Condensed, body Courier New Bold "
        "(courbd.ttf) with per-character typewriter jitter",
        "south wall notice frames or taped to tile, eye level", prompt=PR + "notice_paper.prompt.txt")

add("arcade", "banner_new_year.png", [320, 48], "arcade dressing", [W("HAPPY NEW YEAR 1985", "PLACEHOLDER (period stock words, not from the copy file)")],
    "generator (transparent), cropped", "hung across the hall under the ceiling, alpha blend", prompt=PR + "banner_new_year.prompt.txt")
add("arcade", "bunting_strip.png", [256, 24], "arcade dressing", [],
    "PIL: pennants in the four shop colours and cream, periodic paper grain; tiles horizontally every 1024 px",
    "tile along the hall under the ceiling; alpha blend; test: bunting_strip_tiletest.jpg")
add("arcade", "floor_polish_circle.png", [220, 220], "arcade dressing", [],
    "PIL: alpha from a generated grayscale swirl mask, warm white, soft edge",
    "floor decal under the polisher over the brown and orange tile; brightens, alpha blend")
add("arcade", "poster_station_zero.png", [64, 96], "the film",
    [W("A WILLARD WYLER PICTURE", "canon"), W("STATION ZERO", "canon"), W("NEXT STOP: NOWHERE.", "canon")],
    "concept/poster.png with only the clock region (794..987 x 333..530 of 1024x1536) taken from a generator edit; "
    "clock reads 11:47 (minute hand ~284 deg, hour hand ~351 deg)", "poster frame on the hall wall; lit from outside",
    prompt=PR + "poster_station_zero.prompt.txt")
for n in ("board_copy_stop", "menu_hole_nine", "today_hole_nine", "board_heel_key"):
    key = {"board_copy_stop": "copy_stop_board", "menu_hole_nine": "hole_nine_menu", "today_hole_nine": "hole_nine_menu.today",
           "board_heel_key": "heel_key_board"}[n]
    add("arcade", f"{n}.png", [60, 44], n.split("_", 1)[1] if n.startswith("board") else "hole_nine",
        [W("(title and every line)", f"copy:{key}")], "generator; every line checked letter by letter",
        "inside the shop on the back wall or over the counter, readable through the glass", prompt=PR + f"{n}.prompt.txt")
for s in SHOPS:
    add("arcade", f"window_cards_{s}.png", [40, 28], s, [W("(four cards)", f"copy:window_cards.{s}")],
        "generator (transparent) — PENDING quota", "inside the window glass, lower third", prompt=PR + f"window_cards_{s}.prompt.txt")
for i, sl in enumerate(COPY["needle_drop_sleeves"], 1):
    add("arcade", f"sleeve_{i}.png", [12, 12], "needle_drop",
        [W(f"{sl['artist']} / {sl['title']}", f"copy:needle_drop_sleeves[{i - 1}]")], "generator — PENDING quota",
        "Needle Drop sleeve wall and window", prompt=PR + f"sleeve_{i}.prompt.txt")
for i, r in enumerate(COPY["needle_drop_rental"], 1):
    add("arcade", f"rental_{i}.png", [5, 8], "needle_drop", [W(r["title"], f"copy:needle_drop_rental[{i - 1}].title")],
        "generator — PENDING quota", "rental tape shelf faces", prompt=PR + f"rental_{i}.prompt.txt")

# Terminus
T = "procedural (PIL): " + TL + "terminus_paper.py"
add("terminus", "paper_greenbar_tile.png", [None, None], "Terminus", [W("(digits only, as texture)", "none: random numbers")],
    T + "; 16 bars of 64 px, FFT-periodic fibre noise, faint wrapped dot-matrix digits",
    "tiling colour texture for every paper surface (walls, floor, ceiling, benches); scale so one bar is about 8 units; seamless (tiletest kept)")
add("terminus", "paper_greenbar_edge.png", [128, 16], "Terminus", [], T + "; holes alpha 0, hole pitch 64 px = bar height",
    "edge strips along platform edge and sheet borders; tiles horizontally; alpha test (holes)")
add("terminus", "paper_times_column.png", [48, 192], "Terminus", [W("23:47 (x32)", "canon")], T,
    "column faces; two lines a bar, bars match the tile")
add("terminus", "sign_terminus.png", [144, 28], "Terminus", [W("047 · TERMINUS", "canon")], T + " (one 5x7 dot glyph table)",
    "hanging sign over the platform")
add("terminus", "sign_fare_validation.png", [64, 16], "Terminus", [W("FARE VALIDATION", "canon")], T,
    "sign over the projector on the validator post")
for n in range(8, 1, -1):
    add("terminus", f"leader_{n}.png", [24, 24], "Terminus", [W(str(n), "film leader numeral (FILM-LAYER 6)")], T,
        "printed along the platform edge, 8 to 2 towards the screen, never 1; alpha blend decal")
add("terminus", "screen_second_platform.png", [384, 216], "Terminus", [],
    "generator, then multiplied by the paper tile's luminance (+-6 %) so the bars and faint digits show through",
    "the projected rectangle on the paper wall across the track; fully emissive", emissive=True,
    prompt=PR + "screen_second_platform.prompt.txt")
add("terminus", "footprints_printed.png", [96, 96], "Terminus", [], "generator (transparent), cropped",
    "floor decals, toes pointing away from the edge (up = facing the train); alpha blend", prompt=PR + "footprints_printed.prompt.txt")
add("terminus", "footprints_fresh.png", [24, 24], "Terminus", [], "generator (transparent), cropped",
    "one fresh pair at the platform edge; alpha blend", prompt=PR + "footprints_fresh.prompt.txt")
add("terminus", "pictogram_validate.png", [24, 24], "HRT", [], "generator (transparent), cropped",
    "overhead signs once the road is set; wordless (replaces any 'PaP' word)", prompt=PR + "pictogram_validate.prompt.txt")

out, missing = [], []
for it in items:
    p = ART / it["folder"] / it["file"]
    if not p.exists():
        missing.append(it["file"]); it["delivered"] = False; out.append(it); continue
    im = Image.open(p)
    a = np.array(im.convert("RGBA"))[..., 3]
    it.update(delivered=True, path=str(p).replace("\\", "/"), pixels=list(im.size), mode=im.mode,
              has_alpha=im.mode == "RGBA" and bool((a < 255).any()), transparent_share=round(float((a == 0).mean()), 3),
              sha1=hashlib.sha1(p.read_bytes()).hexdigest()[:12])
    if it["units"] == [None, None]:
        it["units"] = None
    out.append(it)
man = {"worker": "A1", "date": "2026-11-27", "copy_file": str(COPYF).replace("\\", "/"),
       "copy_sha256": hashlib.sha256(COPYF.read_bytes()).hexdigest(),
       "copy_writer_note": COPY.get("_writer"),
       "fonts": {"bahnschrift.ttf": "HRT directory, notices titles, Copy Stop lettering",
                 "courbd.ttf": "notice bodies (typewriter)", "dot-matrix": "own 5x7 glyph table, tools/dotmatrix.py"},
       "count_delivered": sum(1 for i in out if i["delivered"]), "missing": missing, "items": out}
(HERE.parent / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
print("delivered", man["count_delivered"], "missing", len(missing), missing)
