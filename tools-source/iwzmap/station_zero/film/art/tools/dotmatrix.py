"""One dot-matrix hand for every printed piece of the Terminus: a 5x7 glyph table drawn as round ink dots.

draw_text(img_rgba, text, x, y, pitch, radius, ink, wrap=None, jitter=0.0, dropout=0.0, rng=None, scale_y=1.0)
  draws onto a PIL RGBA image (supersample it yourself for smooth dots); wrap=(W,H) wraps dots modulo the size
  so a texture stays seamless. Returns the width drawn in pixels.
"""
import random
from PIL import ImageDraw

G = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "·": ["00000", "00000", "00000", "01100", "01100", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00000", "00001", "00010", "00100", "01000", "10000", "00000"],
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "10001", "01010", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def text_width(text, pitch):
    return len(text) * 6 * pitch - pitch


def glyph_dots(text):
    """Yield (col, row) dot positions in dot units for a line of text (6 columns a character)."""
    for i, ch in enumerate(text):
        rows = G[ch]
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    yield i * 6 + c, r


def draw_text(img, text, x, y, pitch, radius, ink, wrap=None, jitter=0.0, dropout=0.0, rng=None, scale_y=1.0):
    rng = rng or random.Random(0)
    d = ImageDraw.Draw(img)
    for c, r in glyph_dots(text):
        if dropout and rng.random() < dropout:
            continue
        cx = x + c * pitch + rng.uniform(-jitter, jitter)
        cy = y + r * pitch * scale_y + rng.uniform(-jitter, jitter)
        rr = radius * rng.uniform(0.9, 1.08)
        a = ink[3] if len(ink) == 4 else 255
        col = (ink[0], ink[1], ink[2], max(0, min(255, int(a * rng.uniform(0.82, 1.0)))))
        offs = [(0, 0)]
        if wrap:
            W, H = wrap
            cx %= W; cy %= H
            offs = [(dx, dy) for dx in (-W, 0, W) for dy in (-H, 0, H)]
        for dx, dy in offs:
            X, Y = cx + dx, cy + dy
            d.ellipse([X - rr, Y - rr, X + rr, Y + rr], fill=col)
    return text_width(text, pitch)


def draw_big_glyph(img, ch, x, y, cell, radius, ink, rng=None, dropout=0.0):
    """A single large glyph as a dot field: each glyph pixel is a cell of 2x2 dots (finer dot-matrix look)."""
    rng = rng or random.Random(1)
    d = ImageDraw.Draw(img)
    rows = G[ch]
    sub = cell / 2
    for r, row in enumerate(rows):
        for c, bit in enumerate(row):
            if bit != "1":
                continue
            for i in range(2):
                for j in range(2):
                    if dropout and rng.random() < dropout:
                        continue
                    cx = x + c * cell + (i + 0.5) * sub
                    cy = y + r * cell + (j + 0.5) * sub
                    rr = radius * rng.uniform(0.88, 1.06)
                    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=ink)
