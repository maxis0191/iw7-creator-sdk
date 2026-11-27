"""Writes the text-bearing prompt files from the copy file, so every word in a prompt is the copy writer's verbatim.

usage: python write_prompts.py   (reads C:/studio-data/sz/film/copy/arcade_copy_raw.txt)
"""
import json, pathlib

COPY = json.loads(pathlib.Path("C:/studio-data/sz/film/copy/arcade_copy_raw.txt").read_text(encoding="utf-8"))
P = pathlib.Path(__file__).resolve().parent.parent / "prompts"

FLAT = ("Constraints: flat artwork seen exactly straight on, full-bleed, no perspective, no frame drawn around it, "
        "no mock-up scene, no lighting gradient across it (the game lights it). Text exactly as given, spelled letter "
        "by letter, no other words, no extra letters.")


def spell(s):
    return " ".join("-".join(w) for w in s.split())


def write(name, body):
    (P / f"{name}.prompt.txt").write_text(body.strip() + "\n", encoding="utf-8")


WORDMARK = {
    "needle_drop": ("NEEDLE DROP", "fat, rounded, heavy 1970s display lettering (the soft bulbous serifless or soft-serif "
                    "faces of record shops and roller rinks of 1975 to 1980), tight letter spacing, all capitals",
                    "hot orange #FF5A14", "the black shop fascia it will sit on"),
    "hole_nine": ("Hole Number Nine", "a confident sign-painter's brush script, connected, slightly upward slanting, "
                  "with thick and thin brush strokes, as a 1978 neighbourhood doughnut shop sign; mixed case exactly as "
                  "written", "chocolate brown #4E2A1E", "the candy pink fascia it will sit on"),
    "heel_key": ("HEEL & KEY", "a sturdy slab-serif of the 1970s (square heavy serifs, like a cobbler's painted board "
                 "or a stamp), all capitals, with a traditional ampersand", "cream #F2E6C9",
                 "the oxblood fascia it will sit on"),
}

for shop, (name, face, colour, ground) in WORDMARK.items():
    tag = COPY["fascia_tagline"][shop]
    write(f"wordmark_{shop}", f"""
Use case: logo-brand
Asset type: the lettering lockup of a small shop sign of 1978 in a subway underpass; it will be composited onto {ground}.
Primary request: a wordmark lockup on two lines: the shop name "{name}" large, and under it, centred and much smaller, the tagline "{tag}".
Style/medium: the name in {face}; the tagline in simple letter-spaced capitals of the same period, the same colour.
Color palette: one flat colour only, {colour}. No outline, no shadow, no gradient, no texture.
Composition/framing: wide landscape 3:1 inside the canvas, lettering centred with a small margin, nothing cropped.
Background: transparent background.
Text (verbatim): "{name}" and "{tag}". Spelling: {spell(name)} / {spell(tag)}.
{FLAT}
Avoid: any symbol, logo, picture, border, background, other words.
""")

HANDS = {
    "needle_drop": "a record-shop owner in his thirties: fast black felt-tip marker capitals on the torn-off back flap "
                   "of a white record mailer card, slightly slanted, a small doodled musical note after the last line",
    "copy_stop": "a draughtswoman: very neat technical-lettering capitals drawn with a fine blue technical pen on a crisp "
                 "white index card with pale blue ruled lines",
    "hole_nine": "a cheerful bakery owner: round loopy capitals in thick red marker on a pink-tinted bakery order slip, "
                 "a little coffee ring stain in one corner",
    "heel_key": "an old cobbler: carefully printed capitals in soft pencil on a stiff buff manila shipping tag card "
                "with a reinforced punched hole at the left end, a few letters gone over twice",
}
for shop, hand in HANDS.items():
    lines = COPY["door_card"][shop]
    write(f"door_card_{shop}", f"""
Use case: photorealistic-natural
Asset type: the hand-written card a shopkeeper taped to the inside of his shop's glass door on 31 December 1984; it will be a texture on a flat 10 x 7 inch quad.
Primary request: a close, flat, straight-on scan of the card alone filling the whole frame edge to edge: {hand}. Two short strips of clear yellowed sticky tape across the top corners.
Text (verbatim, three lines, exactly this line breaking): "{lines[0]}" / "{lines[1]}" / "{lines[2]}".
Spelling: {" / ".join(spell(l) for l in lines)}.
Composition/framing: landscape 10:7, the card fills the canvas full-bleed, text large and legible, centred.
{FLAT}
Avoid: glass, door, reflections, hands, any other words, signatures, dates beyond the given text.
""")

write("notice_paper", """
Use case: photorealistic-natural
Asset type: blank paper stock for transit authority notices posted in a subway underpass in December 1984; text will be typeset onto it afterwards.
Primary request: a single blank sheet of slightly off-white 1984 bond paper, flat and straight on, filling the whole frame edge to edge: faint fold creases, slight yellowing towards the edges, a few soft grey scuffs, a tiny tear at one edge, the four corners held by small strips of yellowed clear tape cut at angles (tape only at the corners, inside the frame).
Composition/framing: portrait, about 3:4, the sheet fills the canvas full-bleed.
Constraints: completely blank: no text, no letters, no logo, no lines, no marks of writing. Flat, straight on, even light, no perspective, no wall, no shadow.
Avoid: any writing or printing, any symbol.
""")

# Boards (60 x 44 units). One shop each, each in its own trade's period sign craft.
cs = COPY["copy_stop_board"]
write("board_copy_stop", f"""
Use case: photorealistic-natural
Asset type: the price board on the wall of a 1978 copy shop; texture for a flat 60 x 44 inch quad.
Primary request: a black grooved felt changeable-letter board (the kind with white plastic push-in letters) in a thin aluminium edge, straight on, filling the frame. White plastic capitals set in neat rows, the title in larger letters:
Title: "{cs['title']}"
Lines (one per row, keep the spacing between item and price as a gap): {" | ".join(f'"{l}"' for l in cs['lines'])}
A slightly crooked letter here and there, one row a little uneven, like a real letter board.
Spelling: {spell(cs['title'])}; {" ; ".join(spell(l) for l in cs['lines'])}.
Composition/framing: landscape 60:44, the board full-bleed (the aluminium edge at the very borders is fine).
{FLAT}
Avoid: any other words, any logo, a wall around it.
""")

hm = COPY["hole_nine_menu"]
write("menu_hole_nine", f"""
Use case: photorealistic-natural
Asset type: the menu board over the counter of a 1978 doughnut shop; texture for a flat 60 x 44 inch quad.
Primary request: a hand-painted menu board by a sign writer, painted on a chocolate brown board with a pink painted border line: the title in pink brush script at the top, then the items in cream hand-lettered capitals on the left with their prices aligned on the right with dotted leaders.
Title: "{hm['title']}"
Lines: {" | ".join(f'"{l}"' for l in hm['lines'])}
Spelling: {spell(hm['title'])}; {" ; ".join(spell(l) for l in hm['lines'])}.
Composition/framing: landscape 60:44, the board full-bleed.
{FLAT}
Avoid: any other words, pictures of food, logos.
""")

write("today_hole_nine", f"""
Use case: photorealistic-natural
Asset type: the small "today" chalkboard beside the counter of a 1978 doughnut shop; texture for a flat 60 x 44 inch quad.
Primary request: a slate-black chalkboard in a plain wooden frame edge, straight on, filling the frame, written by hand in white and pink chalk capitals, with old smudged chalk ghosts behind: the heading "TODAY" in pink chalk, underlined, then four lines in white chalk:
Lines: {" | ".join(f'"{l}"' for l in hm['today'])}
Spelling: T-O-D-A-Y; {" ; ".join(spell(l) for l in hm['today'])}.
Composition/framing: landscape 60:44, the chalkboard full-bleed.
{FLAT}
Avoid: any other words, drawings, logos.
""")

hk = COPY["heel_key_board"]
write("board_heel_key", f"""
Use case: photorealistic-natural
Asset type: the price board of a 1978 shoe repair and key cutting stall; texture for a flat 60 x 44 inch quad.
Primary request: a cream enamel-painted wooden board, hand-lettered by a sign writer in oxblood slab-serif capitals, with a double oxblood rule under the title; item names on the left, prices aligned on the right, a little worn and finger-marked:
Title: "{hk['title']}"
Lines: {" | ".join(f'"{l}"' for l in hk['lines'])}
Spelling: {spell(hk['title'])}; {" ; ".join(spell(l) for l in hk['lines'])}.
Composition/framing: landscape 60:44, the board full-bleed.
{FLAT}
Avoid: any other words, logos, pictures.
""")

CARD_STYLE = {
    "needle_drop": "four fluorescent day-glo star-burst and rectangle price cards (orange, yellow, green, pink) hand-lettered in thick black marker, the kind record shops taped in windows",
    "copy_stop": "four white index cards hand-lettered in neat blue technical-pen capitals with a ruler-drawn blue underline",
    "hole_nine": "four pink and cream scalloped-edge cards hand-lettered in red and brown marker, round friendly capitals",
    "heel_key": "four buff manila shipping-tag cards with punched reinforced holes, hand-lettered in black pencil and oxblood crayon capitals",
}
for shop, style in CARD_STYLE.items():
    cards = COPY["window_cards"][shop]
    txt = " ; ".join(f'card {i + 1}: "{a}" / "{b}"' for i, (a, b) in enumerate(cards))
    sp = " ; ".join(f"{spell(a)} / {spell(b)}" for a, b in cards)
    write(f"window_cards_{shop}", f"""
Use case: photorealistic-natural
Asset type: hand-lettered price cards taped inside a 1984 shop window; one sheet holding four separate cards, a texture with transparent background on a flat 40 x 28 inch quad.
Primary request: {style}. The four cards laid out in a loose 2 x 2 grid, each slightly rotated a few degrees, not overlapping, each card two lines of large hand lettering:
Text (verbatim): {txt}.
Spelling: {sp}.
Composition/framing: landscape 40:28, the four cards fill the canvas with small gaps between them.
Background: transparent background around and between the cards.
{FLAT}
Avoid: any other words, glass, a window frame, shadows outside the cards.
""")
SLEEVE_STYLE = [
    "early-eighties new wave: flat Memphis-like geometric shapes (squiggle, triangles, a grid) in pastel turquoise, pink and black on white, small sans-serif type",
    "late-seventies disco twelve-inch: airbrushed chrome and neon on deep purple, a glittering mirror-ball horizon, flowing script title",
    "1980 heavy metal: a dark painted illustration of a steel mill furnace under a red sky, jagged metallic gothic logo lettering",
    "1983 post-punk: a stark grainy black-and-white photocopied photo of an empty concrete corridor, tiny typewriter-style type, lots of black",
    "1978 soft rock: a warm faded photograph of a harbour sunset with a sailing boat, rounded brown and orange seventies lettering",
    "1982 dub reggae: a bold red, gold and green woodcut print of a pier with echoing sound rings, chunky hand-cut letters",
    "1979 country: a photograph of a lonely truck stop diner at night in the rain with neon reflections, western slab lettering in cream",
    "1984 electro: a black sleeve with a neon grid floor going to the horizon, a chrome turntable, a bold italic computer-style title",
]
for i, (s, style) in enumerate(zip(COPY["needle_drop_sleeves"], SLEEVE_STYLE), 1):
    write(f"sleeve_{i}", f"""
Use case: illustration-story
Asset type: the front of a record sleeve ({s['format']}) in the sleeve wall of a 1984 record shop; texture for a flat 12 x 12 inch quad.
Primary request: an original record cover for the band "{s['artist']}", album "{s['title']}", in this style: {style}.
Text (verbatim): the artist "{s['artist']}" and the title "{s['title']}", nothing else. Spelling: {spell(s['artist'])} / {spell(s['title'])}.
Composition/framing: square 1:1, the cover art full-bleed to all four edges, flat and straight on.
Constraints: only those words; the cover alone: no vinyl disc showing, no shop, no wall, no shrink-wrap glare, no perspective, no frame drawn. Big bold shapes that still read when the cover is shown at 96 pixels.
Avoid: real band names or logos, real record labels, barcodes, any other text.
""")

RENTAL_STYLE = {
    "CRIME DRAMA": "a painted 1984 video cover: a rain-soaked harbour at night, a detective's silhouette under a dock lamp, cold blue and orange",
    "ACTION THRILLER": "a painted 1984 video cover: a diesel freight locomotive bursting through a desert night with headlight flare, explosive red and yellow",
    "SPACE ADVENTURE": "a painted 1984 video cover: a gleaming starship over a ringed planet, a lone hero in a white space suit, airbrushed star field",
    "MARTIAL ARTS": "a painted 1984 video cover: a fighter in a flying kick in front of a glowing steel foundry furnace, orange and black",
    "FAMILY COMEDY": "a bright 1984 video cover photograph: two shaggy dogs in sailor caps on a small rowing boat, sunny blue sky, cheerful yellow border",
    "TEEN ROMANCE": "a soft-focus 1984 video cover photograph: a teenage couple on a boardwalk pier at sunset, pastel pink and turquoise",
}
for i, r in enumerate(COPY["needle_drop_rental"], 1):
    write(f"rental_{i}", f"""
Use case: illustration-story
Asset type: the front of a 1984 rental videocassette box in a record shop; texture for a flat 5 x 8 inch quad (portrait).
Primary request: an original film cover for "{r['title']}", a {r['genre'].lower()}: {RENTAL_STYLE[r['genre']]}. The title in big bold period display lettering in the upper third.
Text (verbatim): "{r['title']}" and nothing else. Spelling: {spell(r['title'])}.
Composition/framing: portrait 5:8, the cover art full-bleed to all four edges, flat and straight on.
Constraints: only the title; the cover alone: no plastic case, no shelf, no glare, no perspective, no frame drawn. Big shapes that read at 40 pixels wide.
Avoid: real actors, real studio logos, ratings, barcodes, credits, any other text.
""")
print("written")
