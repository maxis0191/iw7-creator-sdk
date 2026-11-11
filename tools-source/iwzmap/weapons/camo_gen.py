"""Station Zero Pack-a-Punch camo textures, procedural and seeded (docs 08-CAMOS.md).

    python -B camo_gen.py camos.json --out <dir> --texconv <texconv.exe> [--materials <stock camo_01.json>]
           [--only carrier] [--size 1024] [--no-dds] [--material-name carrier=camo_01] [--image-name carrier=...]

Writes, per camo, into <dir>/images: <img>_c.dds (BC1_UNORM), <img>_n.dds (BC7_UNORM), <img>_sg.dds (BC3_UNORM),
<img>_e.dds (BC1_UNORM), <img>_o.dds (BC4_UNORM), all with full mip chains, and the layer-M masks
(<img>_m.dds, <img>_m1.dds, <img>_m2.dds, BC1_UNORM); into <dir>/preview: PNG previews (each map, the palette
roles, a rough lit view, a 2x2 tiling check) and a motion preview (GIF and strip); into <dir>/materials (with
--materials): material JSONs cloned from the stock camo_01 with the layer-1 slots pointing at the images; and
<dir>/camo_report.json with the measured role shares, seam metrics and DDS headers. Exit code 2 when a
measured share leaves its band in the spec.

Encoding (stock facts read 2026-11-11 from the GfxImage headers of 485 stock camo .iw7Image dumps, format u32 at
struct offset 0x18; the pixels themselves are streamed and not in the dumps):
* stock camo images use BC1_UNORM (_c 190 of 210, _e 36 of 45), BC7_UNORM (_n), BC3_UNORM (_sg), BC4_UNORM (_o);
  no sRGB formats. Sizes 512 (camo_01) to 2048 (camo_211.._215), full mip chains.
* Channel use READ FROM THE SHADER (2026-11-11, pixel shader 6ff80a5207557f38 of the 2-UV weapon lit technique,
  see shader_read.py and notes engine-camo-shading.md): layer 1 is sampled at one UV for all five maps.
  _c (t5): RGB squared = linear albedo x colorTint1; A = camo coverage mask (x the gun's own _packed_a mask).
  _n (t4): G and A only, 2v - 1, 45-degree octahedral pair (x = (G+A)/2, y = (G-A)/2, z = 1 - |x| - |y|), rotated
  into the base frame by TEXCOORD11 and ADDED to the base pair x mask; R and B are not read.
  _sg (t6): RGB squared = specular F0 colour; A = gloss, linear, power 2^(20 (1 - sqrt(1 - A))) + 2.
  _o (t7): R only, squared on read (stored here as sqrt(occlusion)); feeds the specular-occlusion lookup.
  _e (t8): RGB squared x emissivePara 1323547990 .x x a code exposure constant x mask.
* material: camo_01 clone; emissivePara 1323547990 = emissive scale (stock camos use 1 to 1000). Layer-1 UV, read
  from vertex shader eaaca8ffa5a53c35: uv1 = S * (R(a + w t) (uv2 + O) + V t), t = game time in seconds;
  secondarySam 4044143062 = [S.u, S.v, V.u, V.v] (V in pre-scale units: the texture moves S*V tiles a second),
  secondarySam 28846999 = [a radians, w radians/s, O.u, O.v]. Stock camo_02 scrolls [1, 1, 0.1, 0.1], camo_242
  rotates [0, 1, 0, 0]. The whole layer (all five maps) moves together; a separately moving layer-M is not in the
  stock shader.
Geometry is in millimetres on a tile of tile_mm; every primitive is drawn with wrap-around, so each image tiles.
"""
import argparse
import copy
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import time

import numpy as np

# ------------------------------------------------------------------ helpers

def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def srgb_to_linear(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((np.maximum(c, 0) + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055).astype(np.float32)


def gloss_from_roughness(r):
    """Gloss (0..1) whose decoded specular power 2^(20 (1 - sqrt(1 - g))) + 2 equals the Blinn power of a
    GGX roughness r (alpha = r^2, power = 2 / alpha^2 - 2)."""
    r = np.asarray(r, np.float64)
    alpha = np.maximum(r * r, 1e-4)
    power = np.maximum(2.0 / (alpha * alpha) - 2.0, 2.0 + 1e-6)
    e = np.clip(np.log2(power - 2.0) / 20.0, 0.0, 1.0)
    return (1.0 - (1.0 - e) ** 2).astype(np.float32)


def fft_noise(rng, n, lo_mm, hi_mm, px_mm, stretch_u=1.0):
    """Periodic noise with a smooth band of wavelengths lo..hi mm; zero mean, unit std. stretch_u > 1 makes
    the features longer along U (the barrel axis) by that factor."""
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n) * px_mm          # cycles per mm
    fx, fy = np.meshgrid(f, f)
    fr = np.hypot(fx * stretch_u, fy)
    lf = np.log(np.maximum(fr, 1e-9))
    c = 0.5 * (math.log(1.0 / hi_mm) + math.log(1.0 / lo_mm))
    half = max(0.5 * (math.log(1.0 / lo_mm) - math.log(1.0 / hi_mm)), 0.15)
    g = np.exp(-0.5 * ((lf - c) / half) ** 2)
    g[0, 0] = 0.0
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    out -= out.mean()
    return (out / (out.std() + 1e-12)).astype(np.float32)


def blur(img, sigma_px):
    """Periodic gaussian blur (FFT)."""
    if img.ndim == 3:
        return np.stack([blur(img[..., c], sigma_px) for c in range(img.shape[2])], -1)
    n = img.shape[0]
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    g = np.exp(-2.0 * (math.pi * sigma_px) ** 2 * (fx * fx + fy * fy))
    return np.real(np.fft.ifft2(np.fft.fft2(img) * g)).astype(np.float32)


class Canvas:
    """A periodic n x n raster of a tile_mm square; primitives in mm, drawn with wrap-around."""

    def __init__(self, n, tile_mm):
        self.n, self.t = n, tile_mm
        self.s = n / tile_mm            # px per mm

    def field(self, fill=1e9):
        return np.full((self.n, self.n), fill, np.float32)

    def _window(self, x0, y0, x1, y1):
        s = self.s
        c0, c1 = int(math.floor(x0 * s)), int(math.ceil(x1 * s)) + 1
        r0, r1 = int(math.floor(y0 * s)), int(math.ceil(y1 * s)) + 1
        cols, rows = np.arange(c0, c1), np.arange(r0, r1)
        return rows, cols, (rows + 0.5) / s, (cols + 0.5) / s

    def capsules(self, sd, segs, pad=1.0):
        """sd = min(sd, distance - radius) for tapered capsules (x0, y0, x1, y1, r0, r1) in mm."""
        n, lim = self.n, self.t / 4.0
        for (x0, y0, x1, y1, r0, r1) in segs:
            L = math.hypot(x1 - x0, y1 - y0)
            k = max(1, int(math.ceil(L / lim)))      # windows narrower than the tile: each pixel once
            for j in range(k):
                a, b = j / k, (j + 1) / k
                self._capsule(sd, x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b,
                              y0 + (y1 - y0) * b, r0 + (r1 - r0) * a, r0 + (r1 - r0) * b, pad)
        return sd

    def _capsule(self, sd, x0, y0, x1, y1, r0, r1, pad):
        n = self.n
        m = max(r0, r1) + pad
        rows, cols, ym, xm = self._window(min(x0, x1) - m, min(y0, y1) - m, max(x0, x1) + m, max(y0, y1) + m)
        X, Y = np.meshgrid(xm, ym)
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / ll, 0.0, 1.0) if ll > 1e-12 else np.zeros_like(X)
        d = np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)) - (r0 + (r1 - r0) * t)
        ix = np.ix_(rows % n, cols % n)
        sd[ix] = np.minimum(sd[ix], d)

    def disc(self, sd, x, y, r, pad=1.0):
        return self.capsules(sd, [(x, y, x, y, r, r)], pad)

    def coverage(self, sd):
        """Anti-aliased inside coverage from a signed distance in mm."""
        return np.clip(0.5 - sd * self.s, 0.0, 1.0).astype(np.float32)

    def stamp(self, mask, x, y, rows_bits, cell):
        """Paint a bitmap (list of strings, '#' = on) with its top-left at (x, y) mm, cell mm per bit."""
        n = self.n
        h, w = len(rows_bits), len(rows_bits[0])
        rows, cols, ym, xm = self._window(x, y, x + w * cell, y + h * cell)
        X, Y = np.meshgrid(xm, ym)
        bx = np.floor((X - x) / cell).astype(int)
        by = np.floor((Y - y) / cell).astype(int)
        inside = (bx >= 0) & (bx < w) & (by >= 0) & (by < h)
        bits = np.array([[c == "#" for c in r] for r in rows_bits], bool)
        on = np.zeros_like(inside)
        on[inside] = bits[by[inside], bx[inside]]
        ix = np.ix_(rows % n, cols % n)
        sub = mask[ix]
        sub[on] = 1.0
        mask[ix] = sub


def fillet(points, radius, arc_steps=8):
    """Round the corners of a polyline with arcs of the given radius."""
    p = [np.asarray(q, np.float64) for q in points]
    out = [p[0]]
    for i in range(1, len(p) - 1):
        a, b, c = p[i - 1], p[i], p[i + 1]
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-9 or lv < 1e-9:
            continue
        u, v = u / lu, v / lv
        theta = math.acos(float(np.clip(np.dot(u, v), -1.0, 1.0)))   # interior angle
        if abs(math.pi - theta) < 1e-3:
            out.append(b)
            continue
        t = min(radius / math.tan(theta / 2.0), 0.5 * lu, 0.5 * lv)
        p0, p1 = b + u * t, b + v * t
        nrm = u + v
        nrm /= np.linalg.norm(nrm)
        r_eff = t * math.tan(theta / 2.0)               # the radius actually fitting the clamped cut-back
        centre = b + nrm * (r_eff / math.sin(theta / 2.0))
        rr = np.linalg.norm(p0 - centre)
        a0 = math.atan2(p0[1] - centre[1], p0[0] - centre[0])
        a1 = math.atan2(p1[1] - centre[1], p1[0] - centre[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(arc_steps + 1):
            ang = a0 + da * j / arc_steps
            out.append(centre + rr * np.array([math.cos(ang), math.sin(ang)]))
    out.append(p[-1])
    return out


def polyline_segs(points, r):
    return [(a[0], a[1], b[0], b[1], r, r) for a, b in zip(points[:-1], points[1:])]


FONT = {   # 3 x 5 engraving font
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
    "A": [".#.", "#.#", "###", "#.#", "#.#"], ".": ["...", "...", "...", "...", ".#."],
}


def text_bits(txt):
    rows = ["" for _ in range(5)]
    for i, ch in enumerate(txt):
        for r in range(5):
            rows[r] += FONT[ch][r] + ("." if i < len(txt) - 1 else "")
    return rows


def normal_from_height(h_mm, px_mm, y_down=True):
    gx = (np.roll(h_mm, -1, 1) - np.roll(h_mm, 1, 1)) * 0.5 * px_mm
    gy = (np.roll(h_mm, -1, 0) - np.roll(h_mm, 1, 0)) * 0.5 * px_mm
    n = np.stack([-gx, gy if y_down else -gy, np.ones_like(gx)], -1)
    return (n / np.linalg.norm(n, axis=-1, keepdims=True)).astype(np.float32)


def encode_normal(nrm, mode):
    x, y, z = nrm[..., 0], nrm[..., 1], nrm[..., 2]
    norm = np.abs(x) + np.abs(y) + np.abs(z)
    px, py = x / norm, y / norm
    g_oct, a_oct = (px + py + 1) / 2, (px - py + 1) / 2
    one = np.ones_like(x)
    if mode == "rgb":
        return np.stack([(x + 1) / 2, (y + 1) / 2, (z + 1) / 2, one], -1)
    if mode == "octa":
        return np.stack([one, g_oct, one, a_oct], -1)
    return np.stack([(x + 1) / 2, g_oct, (z + 1) / 2, a_oct], -1)        # hybrid


def seam_metric(img):
    """Wrap-around step against the interior steps. Per axis, the mean |difference| of every adjacent pair of
    lines is taken; the wrap pair (last line, first line) is compared with the largest interior pair.
    Returns (wrap mean |diff|, ratio); ratio <= 1 means the seam is no stronger than an existing line step."""
    a = np.asarray(img, np.float32)
    if a.ndim == 2:
        a = a[..., None]
    out_edge, out_ratio = [], []
    for ax in (0, 1):
        d = np.abs(np.diff(a, axis=ax)).mean(axis=tuple(i for i in range(3) if i != ax))
        w = np.abs(np.take(a, 0, ax) - np.take(a, -1, ax)).mean()
        ref = max(float(d.max()), 1e-6)
        out_edge.append(float(w))
        out_ratio.append(float(w / ref))
    return max(out_edge), max(out_ratio)


# ------------------------------------------------------------------ CARRIER

def build_carrier(spec, cfg, n, rng):
    T = float(spec["tile_mm"])
    cv = Canvas(n, T)
    s = cv.s
    P, pal = cfg["pattern"], cfg["palette"]
    lw = P["line_width_mm"] / 2.0
    sp = P["route_spacing_mm"]
    R = P["bend_radius_mm"]
    nb = P["bundles"]

    route_sd, stud_sd, lamp_sd = cv.field(), cv.field(), cv.field()
    red_sd, green_sd, roundel_black = cv.field(), cv.field(), cv.field()
    letters = np.zeros((n, n), np.float32)
    lanes_y, junctions, bundles = [], [], []
    keep_out = []          # (x, y, r) places taken, for lamps, labels and signals

    def free(x, y, r):
        for (a, b, rr) in keep_out:
            dx = (x - a + T / 2) % T - T / 2
            dy = (y - b + T / 2) % T - T / 2
            if math.hypot(dx, dy) < r + rr:
                return False
        return True

    roundel = None
    for b in range(nb):
        nr = P["routes_per_bundle"][b % len(P["routes_per_bundle"])]
        y0 = T * (b + 0.5) / nb - sp * (nr - 1) / 2.0 + rng.uniform(-3.0, 3.0)
        lane = [y0 + i * sp for i in range(nr)]
        lanes_y += lane
        # merge/split: a route leaves its lane on a 45-degree diagonal, runs on the neighbour's lane (the lines
        # merge at a stud), then splits back (stud). Events stay off the tile border so lanes meet at the wrap.
        events = {i: [] for i in range(nr)}
        busy = []
        tries = 0
        while sum(len(v) for v in events.values()) < P["merge_events_per_bundle"] and tries < 40:
            tries += 1
            length = float(rng.uniform(*P["merge_length_mm"]))
            xa = float(rng.uniform(12.0, T - 12.0 - length - 2 * sp))
            src = int(rng.integers(0, nr))
            dst = src + (1 if src == 0 else -1 if src == nr - 1 else int(rng.choice([-1, 1])))
            span = (xa - 8.0, xa + length + 2 * sp + 8.0)
            if any(not (span[1] < u0 or span[0] > u1) for u0, u1 in busy):
                continue
            busy.append(span)
            events[src].append((xa, lane[dst] - lane[src], length))
        spans = {}
        for i in range(nr):
            pts = [(-2.0 * R, lane[i])]
            sp_i = []
            for (xa, dy, length) in sorted(events[i]):
                d = abs(dy)
                pts += [(xa, lane[i]), (xa + d, lane[i] + dy), (xa + d + length, lane[i] + dy),
                        (xa + 2 * d + length, lane[i])]
                junctions += [(xa + d, lane[i] + dy), (xa + d + length, lane[i] + dy)]
                sp_i.append((xa - 2.0, xa + 2 * d + length + 2.0))
            pts.append((T + 2.0 * R, lane[i]))
            cv.capsules(route_sd, polyline_segs(fillet(pts, R), lw))
            spans[i] = sp_i
        bundles.append({"lane": lane, "busy": busy, "spans": spans})
        if b == nb // 2:   # the Zero roundel: a spur from the outer route of the middle bundle ends in the disc
            yb = lane[-1]
            xr = float(rng.uniform(0.40 * T, 0.6 * T))
            for (u0, u1) in busy:
                if u0 - 16 < xr < u1 + 4:
                    xr = (u1 + 22.0) % T
            jx = xr - 9.0
            ry = yb + 6.0 + 4.0 + P["roundel_outer_mm"] - 1.0
            pts = fillet([(jx, yb), (jx + 6.0, yb + 6.0), (xr, ry)], R)
            cv.capsules(route_sd, polyline_segs(pts, lw))
            cv.disc(route_sd, xr, ry, P["roundel_outer_mm"])
            cv.disc(roundel_black, xr, ry, P["roundel_inner_mm"])
            junctions.append((jx, yb))
            roundel = (xr, ry)
            keep_out.append((xr, ry, P["roundel_outer_mm"] + 4.0))
    for (x, y) in junctions:
        cv.disc(stud_sd, x, y, P["junction_stud_radius_mm"])
        keep_out.append((x, y, P["junction_stud_radius_mm"] + 2.0))

    # station ticks every T / k on the outer lanes (outward, short, perpendicular), each with an inline lamp
    k = P["station_ticks_per_tile"]
    labels = P["labels"]
    cell = P["glyph_height_mm"] / 5.0
    tick_pts = []
    for bi, B in enumerate(bundles):
        lane = B["lane"]
        for i, side in ((0, -1), (len(lane) - 1, 1)):
            phase = rng.uniform(0.0, T / k)
            for j in range(k):
                x = (phase + j * T / k) % T
                y = lane[i]
                if any(u0 - 5.0 <= x <= u1 + 5.0 for u0, u1 in B["spans"][i]):
                    continue
                if not free(x, y, 3.0):
                    continue
                y1 = y + side * (lw + P["tick_length_mm"])
                cv.capsules(route_sd, [(x, y, x, y1, P["tick_width_mm"] / 2, P["tick_width_mm"] / 2)])
                cv.disc(lamp_sd, x, y, P["station_lamp_radius_mm"])
                keep_out.append((x, y1, 3.0))
                keep_out.append((x, y, P["station_lamp_radius_mm"] + 1.0))
                tick_pts.append((x, y1, side))
                txt = labels[len(tick_pts) % len(labels)]
                bits = text_bits(txt)
                ty = y1 + (1.0 if side > 0 else -1.0 - 5 * cell)
                cv.stamp(letters, x - len(bits[0]) * cell / 2.0, ty, bits, cell)

    # one parked lamp per route, spaced along U (the static frame of the travelling lamps)
    for j, y in enumerate(lanes_y):
        x = float((j * 0.381966 + 0.13) % 1.0) * T
        for _ in range(8):
            if free(x, y, P["parked_lamp_radius_mm"] + 1.0):
                break
            x = (x + 11.0) % T
        cv.disc(lamp_sd, x, y, P["parked_lamp_radius_mm"])
        keep_out.append((x, y, P["parked_lamp_radius_mm"] + 1.0))

    # route labels between lanes (engraved, tiny)
    for B in bundles:
        lane = B["lane"]
        for i in range(len(lane) - 1):
            ym = 0.5 * (lane[i] + lane[i + 1]) - 2.5 * cell
            for j in range(P["route_labels_per_gap"]):
                x = (j + rng.uniform(0.2, 0.8)) * T / P["route_labels_per_gap"]
                near = B["spans"][i] + B["spans"][i + 1]
                if any(u0 - 4 <= x <= u1 + 4 for u0, u1 in near) or not free(x, ym, 3.0):
                    continue
                txt = labels[int(rng.integers(0, len(labels)))]
                cv.stamp(letters, x, ym, text_bits(txt), cell)

    # gaps between bundles: chainage scale with numbers, panel screws, signal lamps
    gaps = []
    for b in range(nb):
        top = bundles[b]["lane"][-1]
        nxt = bundles[(b + 1) % nb]["lane"][0] + (T if b == nb - 1 else 0.0)
        gaps.append(((top + nxt) / 2.0) % T)
    mw, ml = P["chainage_mark_mm"]
    step = P["chainage_mark_step_mm"]
    marks = []
    for gy in gaps:
        base = gy + 1.0
        for j in range(int(round(T / step))):
            x = j * step
            long_ = (j % 4 == 0)
            l = ml * (1.9 if long_ else 1.0)
            marks.append((x, base, x, base + l, mw / 2, mw / 2))
            if j % 8 == 0:
                cv.stamp(letters, x + 0.8, base + l - 5 * cell, text_bits("%d" % ((j * step) % 1000)), cell)
        for j in range(int(round(T / step))):
            keep_out.append((j * step, base + ml, ml))
    mk = cv.field()
    cv.capsules(mk, marks, pad=0.5)
    letters = np.maximum(letters, cv.coverage(mk))
    screws = []
    per_gap = max(1, P["panel_screws"] // len(gaps))
    for gi, gy in enumerate(gaps):
        for j in range(per_gap):
            gx = (j + 0.5 + rng.uniform(-0.15, 0.15)) * T / per_gap + gi * 17.0
            sy = gy - 6.5
            for _ in range(12):
                if free(gx % T, sy, P["panel_screw_radius_mm"] + 1.5):
                    break
                gx += 9.0
            screws.append((gx % T, sy))
            cv.disc(stud_sd, gx % T, sy, P["panel_screw_radius_mm"])
            keep_out.append((gx % T, sy, P["panel_screw_radius_mm"] + 2.0))

    def signal(sd, count):
        placed = 0
        for _ in range(200):
            if placed >= count:
                break
            B = bundles[int(rng.integers(0, len(bundles)))]
            out = int(rng.integers(0, 2))
            x = float(rng.uniform(0, T))
            y = B["lane"][-1] + 6.0 if out else B["lane"][0] - 6.0
            if free(x, y, P["signal_lamp_radius_mm"] + 0.8) and route_sd[int(y * s) % n, int(x * s) % n] > 1.0:
                cv.disc(sd, x, y, P["signal_lamp_radius_mm"])
                keep_out.append((x, y, P["signal_lamp_radius_mm"] + 1.0))
                placed += 1
    signal(red_sd, P["red_lamps_per_tile"])
    signal(green_sd, P["green_lamps_per_tile"])

    # --- coverages and roles (priority: signal lamps, lamps, studs, routes, letters, wear, enamel)
    cov = {k_: cv.coverage(v) for k_, v in (("route", route_sd), ("stud", stud_sd), ("lamp", lamp_sd),
                                            ("red", red_sd), ("green", green_sd), ("black", roundel_black))}
    route_c = cov["route"] * (1.0 - cov["black"])
    # enamel wear: polished rims around the engraving and the studs, broken by noise (edge highlights)
    rim = np.exp(-np.maximum(route_sd, 0.0) / 0.9) * (route_sd > 0) + \
        0.8 * np.exp(-np.maximum(stud_sd, 0.0) / 0.9) * (stud_sd > 0)
    wear_field = 1.4 * rim + 0.55 * fft_noise(rng, n, 1.0, 6.0, s) + 0.35 * fft_noise(rng, n, 10.0, 40.0, s)
    plain = (route_sd > 0) & (stud_sd > 0) & (lamp_sd > 0) & (letters < 0.5)
    q = float(np.clip(1.0 - P["wear_share"] / max(plain.mean(), 1e-6), 0, 1))
    thr = float(np.quantile(wear_field[plain], q))
    wear_c = np.clip((wear_field - thr) * 3.0 + 0.5, 0.0, 1.0) * plain

    names = ["enamel", "wear", "route", "lamp", "red", "green", "brass", "lettering"]
    roles = np.zeros((n, n), np.uint8)
    roles[wear_c >= 0.5] = 1
    roles[letters >= 0.5] = 7
    roles[route_c >= 0.5] = 2
    roles[cov["stud"] >= 0.5] = 6
    roles[cov["lamp"] >= 0.5] = 3
    roles[cov["red"] >= 0.5] = 4
    roles[cov["green"] >= 0.5] = 5

    E = float(cfg["emissive_max_strength"])
    layers = [(wear_c, "wear"), (letters, "lettering"), (route_c, "route"), (cov["stud"], "brass"),
              (cov["lamp"], "lamp"), (cov["red"], "red"), (cov["green"], "green")]
    albedo = np.broadcast_to(hex_rgb(pal["enamel"]["hex"]), (n, n, 3)).astype(np.float32).copy()
    emis = np.zeros((n, n, 3), np.float32)            # linear, 1.0 = emissive_max_strength
    rough = np.full((n, n), pal["enamel"]["roughness"], np.float32)
    metal = np.zeros((n, n), np.float32)
    for c, role in layers:
        c3 = c[..., None]
        p = pal[role]
        albedo = albedo * (1 - c3) + hex_rgb(p["hex"]) * p.get("albedo_scale", 1.0) * c3
        e = srgb_to_linear(hex_rgb(p["hex"])) * (p.get("emissive", 0.0) / E)
        emis = emis * (1 - c3) + e * c3
        rough = rough * (1 - c) + p.get("roughness", 0.5) * c
        metal = metal * (1 - c) + p.get("metal", 0.0) * c
    # dust in the engraving: the line rims are darker in albedo and occlusion; light grime on the enamel
    rim_in = np.clip(1.0 - np.abs(route_sd + 0.3) / 0.4, 0.0, 1.0) * (route_c > 0.02)
    albedo *= (1.0 - 0.4 * rim_in)[..., None]
    emis *= (1.0 - 0.5 * rim_in)[..., None]
    grime = np.clip(0.5 + 0.5 * fft_noise(rng, n, 0.5, 4.0, s), 0, 1)
    albedo *= (0.92 + 0.08 * grime)[..., None]

    # --- height (mm): orange peel, engraved lines, domed studs and lamps, screw slots, shallow lettering
    h = P["orange_peel_height_mm"] * fft_noise(rng, n, *P["orange_peel_mm"], s)
    h -= P["engrave_depth_mm"] * np.clip(-route_sd / 0.15 + 0.5, 0.0, 1.0) * (1.0 - cov["black"])
    for sd, rr, hh in ((stud_sd, P["junction_stud_radius_mm"], 0.35), (lamp_sd, P["parked_lamp_radius_mm"], 0.15),
                       (red_sd, P["signal_lamp_radius_mm"], 0.3), (green_sd, P["signal_lamp_radius_mm"], 0.3)):
        inside = np.clip(-sd / rr, 0.0, 1.0)
        h += hh * np.sqrt(np.clip(1.0 - (1.0 - inside) ** 2, 0.0, 1.0)) * (sd < 0)
    for (gx, gy) in screws:
        sl = cv.field()
        a = rng.uniform(0, math.pi)
        r = P["panel_screw_radius_mm"] * 0.72
        cv.capsules(sl, [(gx - r * math.cos(a), gy - r * math.sin(a), gx + r * math.cos(a), gy + r * math.sin(a),
                          0.45, 0.45)], pad=0.5)
        sc = cv.coverage(sl)
        h -= 0.3 * sc
        albedo *= (1.0 - 0.5 * sc)[..., None]
    h -= 0.04 * letters
    occl = np.clip(1.0 - 0.45 * rim_in - 0.25 * np.exp(-np.maximum(stud_sd, 0) / 0.5) * (stud_sd > 0), 0, 1)

    # --- motion: travelling lamps, one dot per route, laid straight along U on the route's lane
    M = cfg["motion"]
    mot = cv.field()
    segs = []
    for j, y in enumerate(lanes_y):
        x = float((j * 0.381966 + 0.13) % 1.0) * T
        L = M["lamp_length_mm"]
        segs.append((x - L / 2, y, x + L / 2, y, lw, lw))
    cv.capsules(mot, segs)
    m = np.clip(blur(cv.coverage(mot), 0.4 * s), 0, 1)
    motion = {"m": m[..., None] * srgb_to_linear(hex_rgb(pal["lamp"]["hex"]))}

    return dict(albedo=albedo, emissive=emis, rough=rough, metal=metal, height=h, occlusion=occl,
                roles=roles, role_names=names, motion=motion,
                extra={"lanes_y_mm": [round(y, 2) for y in lanes_y], "junctions": len(junctions),
                       "station_ticks": len(tick_pts), "roundel_mm": [round(v, 1) for v in roundel],
                       "lamp_scroll_uv_s": round(M["lamp_speed_mm_s"] / T, 4)})


# ------------------------------------------------------------------ MERCURY ARC

def grow_filament(rng, P, x0, y0, heading):
    """A Lichtenberg-like filament as tapered capsules: a trunk, 3..6 branches fanning forward, sub-branches
    and hair-thin twigs. Directions wander around their own heading (mean-reverting), so lines kink
    slightly at every step but never curl or zigzag."""
    segs = []
    step = P["step_mm"]
    wander = P["wander_rad"]

    def walk(x, y, head, length, r0, r1):
        nst = max(2, int(length / step))
        off = 0.0
        pts = [(x, y)]
        for _ in range(nst):
            off = 0.75 * off + rng.normal(0, wander)
            a = head + off
            x, y = x + step * math.cos(a), y + step * math.sin(a)
            pts.append((x, y))
        for i in range(nst):
            t0, t1 = i / nst, (i + 1) / nst
            segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                         r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1))
        return pts

    nb = int(rng.integers(P["branches"][0], P["branches"][1] + 1))
    L = float(rng.uniform(*P["trunk_length_mm"]))
    r_root, r_tip = P["root_radius_mm"], P["tip_radius_mm"]
    trunk = walk(x0, y0, heading, L, r_root, r_tip)
    nt = len(trunk) - 1
    at = np.sort(rng.uniform(0.1, 0.7, nb))
    for j, f in enumerate(at):
        i = int(f * nt)
        bx, by = trunk[i]
        side = 1 if j % 2 == 0 else -1
        a = heading + side * rng.uniform(0.35, 0.8)
        rb = (r_root + (r_tip - r_root) * f) * 0.7
        bl = L * (1 - f) * rng.uniform(0.5, 0.85)
        pts = walk(bx, by, a, bl, rb, r_tip * 0.8)
        if bl > 16.0:
            k = int(len(pts) * rng.uniform(0.3, 0.6))
            sx, sy = pts[k]
            walk(sx, sy, a + side * rng.uniform(0.35, 0.7), bl * 0.45, rb * 0.55, r_tip * 0.7)
    for _ in range(P["twigs_per_filament"]):
        i = int(rng.uniform(0.15, 0.95) * nt)
        bx, by = trunk[i]
        a = heading + rng.choice([-1, 1]) * rng.uniform(0.5, 1.2)
        walk(bx, by, a, rng.uniform(2.0, 5.0), r_tip * 0.8, r_tip * 0.5)
    return segs


def filament_field(cv, rng, P, count, angle_spread=0.35):
    T = cv.t
    sd, core = cv.field(), cv.field()
    roots = []
    for k in range(count):
        x0 = (k + rng.uniform(0.2, 0.8)) * T / count
        y0 = (k * 0.618034 + rng.uniform(-0.08, 0.08)) % 1.0 * T
        heading = rng.choice([0.0, math.pi]) + rng.normal(0, angle_spread)
        segs = grow_filament(rng, P, x0, y0, heading)
        cv.capsules(sd, segs, pad=P["teal_fringe_mm"] + 0.6)
        cf, cm = P["core_fraction"], P["core_min_radius_mm"]
        cv.capsules(core, [(a, b, c, d, max(r0 * cf - cm, 0.0), max(r1 * cf - cm, 0.0))
                           for (a, b, c, d, r0, r1) in segs if r0 * cf > cm], pad=0.5)
        roots.append((x0, y0))
    return sd, core, roots


def build_mercury(spec, cfg, n, rng):
    T = float(spec["tile_mm"])
    cv = Canvas(n, T)
    s = cv.s
    P, pal = cfg["pattern"], cfg["palette"]
    E = float(cfg["emissive_max_strength"])

    # --- slow liquid ripple; sparse beads
    lo, hi = P["ripple_wavelength_mm"]
    rip = fft_noise(rng, n, lo, hi, s, P.get("ripple_stretch_u", 1.0))
    h = 0.5 * P["ripple_height_mm"] * rip
    for _ in range(P["beads_per_tile"]):
        d = rng.uniform(*P["bead_diameter_mm"])
        x, y = rng.uniform(0, T), rng.uniform(0, T)
        sd1 = cv.field()
        cv.disc(sd1, x, y, d / 2, pad=0.3)
        inside = np.clip(-sd1 / (d / 2), 0, 1)
        h += (d / 2) * 0.7 * np.sqrt(np.clip(1 - (1 - inside) ** 2, 0, 1)) * (sd1 < 0)
    nrm = normal_from_height(h, s, spec.get("normal_y_down", True))

    # --- shadow tint in the troughs (occluded folds), soft
    # folds: concave places of the skin (local mean above the point), soft-edged, P["shadow_share"] of the tile
    fold = blur(rip, P["fold_radius_mm"] * s) - rip
    fold /= fold.std() + 1e-9
    q = float(np.quantile(fold, 1.0 - P["shadow_share"]))
    shadow_c = np.clip((fold - q) * P["shadow_softness"] + 0.5, 0, 1)

    # --- faint baked environment: blurred lamps looked up by the ripple normal
    env = np.zeros((n, n, 3), np.float32)
    for lamp in P["env_lamps"]:
        ax, ay = lamp["at"]
        d2 = (nrm[..., 0] * P["env_normal_gain"] - ax) ** 2 + (nrm[..., 1] * P["env_normal_gain"] - ay) ** 2
        env += lamp["gain"] * np.exp(-d2 / (2 * lamp["spread"] ** 2))[..., None] * hex_rgb(lamp["hex"])
    env = blur(env, 1.0 * s)
    skin, shad = hex_rgb(pal["skin"]["hex"]), hex_rgb(pal["shadow"]["hex"])
    base = skin * (0.94 + 0.06 * np.tanh(rip)[..., None])
    albedo = base * (1 - shadow_c[..., None]) + shad * shadow_c[..., None]
    k = P["env_strength"]
    albedo = np.clip(albedo * (1 - k * 0.6) + k * env * (1 - 0.7 * shadow_c[..., None]), 0, 1)

    # --- arc filament (static frame): violet body, white core, hair-thin teal fringe; soft UV glow
    sd, core_sd, roots = filament_field(cv, rng, P, P["filaments_per_tile"])
    body_c, core_c = cv.coverage(sd), cv.coverage(core_sd)
    fr = P["teal_fringe_mm"]
    teal_c = np.clip(cv.coverage(sd - fr) - body_c, 0, 1)
    halo = blur(body_c, P["glow_radius_mm"] * s)
    halo = np.clip(halo / (np.quantile(halo, 0.995) + 1e-9), 0, 1)
    glow_f = np.clip(halo ** 0.6 + P["glow_trough_gain"] * shadow_c * np.clip(halo * 3.0, 0, 1), 0, 1)

    def ce(k_):
        return srgb_to_linear(hex_rgb(pal[k_]["hex"])) * (pal[k_]["emissive"] / E)
    emis = glow_f[..., None] * ce("glow")
    emis = emis * (1 - teal_c[..., None]) + ce("teal") * teal_c[..., None]
    emis = emis * (1 - body_c[..., None]) + ce("body") * body_c[..., None]
    emis = emis * (1 - core_c[..., None]) + ce("core") * core_c[..., None]
    albedo = albedo * (1 - 0.2 * body_c[..., None]) + 0.2 * body_c[..., None] * hex_rgb(pal["body"]["hex"])

    names = ["skin", "shadow", "glow", "teal", "body", "core"]
    roles = np.zeros((n, n), np.uint8)
    roles[shadow_c >= 0.5] = 1
    roles[glow_f >= P["glow_role_level"]] = 2
    roles[teal_c >= 0.5] = 3
    roles[body_c >= 0.5] = 4
    roles[core_c >= 0.5] = 5

    rough = (pal["skin"]["roughness"] * (1 - shadow_c) + pal["shadow"]["roughness"] * shadow_c).astype(np.float32)
    metal = np.ones((n, n), np.float32)
    occl = np.clip(1.0 - 0.3 * shadow_c, 0, 1).astype(np.float32)

    # --- motion: arc mask A (filaments, coloured) and reveal mask B (soft blobs); visible arc = A x B
    Mo = cfg["motion"]
    sdA, coreA, _ = filament_field(cv, rng, P, Mo["filaments_a"], angle_spread=0.6)
    bA, cA = cv.coverage(sdA), cv.coverage(coreA)
    tA = np.clip(cv.coverage(sdA - fr) - bA, 0, 1)
    lin = lambda k_: srgb_to_linear(hex_rgb(pal[k_]["hex"]))
    maskA = tA[..., None] * lin("teal") * 0.5
    maskA = maskA * (1 - bA[..., None]) + bA[..., None] * lin("body")
    maskA = maskA * (1 - cA[..., None]) + cA[..., None] * lin("core")
    blobs = fft_noise(rng, n, Mo["reveal_wavelength_mm"][0], Mo["reveal_wavelength_mm"][1], s)
    thrB = float(np.quantile(blobs, 1.0 - Mo["reveal_share"]))
    maskB = np.clip((blobs - thrB) / 0.5 + 0.5, 0, 1)
    motion = {"m1": np.clip(maskA, 0, 1).astype(np.float32), "m2": np.repeat(maskB[..., None], 3, -1).astype(np.float32)}

    return dict(albedo=albedo.astype(np.float32), emissive=emis.astype(np.float32), rough=rough, metal=metal,
                normal=nrm, height=h, occlusion=occl, roles=roles, role_names=names, motion=motion,
                extra={"filament_roots_mm": [[round(a, 1), round(b, 1)] for a, b in roots],
                       "mask_a_share": round(float((bA >= 0.5).mean()), 4),
                       "mask_b_share": round(float((maskB >= 0.5).mean()), 4)})


# ------------------------------------------------------------------ packing and writing

def pack(spec, cfg, L):
    """Stored texel values (0..1) for each image, as the game would sample them (see module doc)."""
    n = L["albedo"].shape[0]
    px_mm = n / float(spec["tile_mm"])
    nrm = L.get("normal")
    if nrm is None:
        nrm = normal_from_height(L["height"], px_mm, spec.get("normal_y_down", True))
    lin = srgb_to_linear(L["albedo"])
    metal = L["metal"][..., None]
    f0 = 0.04 * (1 - metal) + lin * metal
    diffuse = lin * (1 - metal * (1.0 - cfg.get("metal_diffuse_scale", 1.0)))
    sg = np.concatenate([np.sqrt(f0), gloss_from_roughness(L["rough"])[..., None]], -1)
    return {
        "c": np.clip(np.sqrt(diffuse), 0, 1),
        "n": np.clip(encode_normal(nrm, spec.get("normal_encoding", "hybrid")), 0, 1),
        "sg": np.clip(sg, 0, 1),
        "e": np.clip(np.sqrt(np.clip(L["emissive"], 0, 1)), 0, 1),
        "o": np.sqrt(np.clip(L["occlusion"], 0, 1))[..., None].repeat(3, -1),     # the shader squares R
        "_normal": nrm,
    }


FORMATS = {"c": "BC1_UNORM", "n": "BC7_UNORM", "sg": "BC3_UNORM", "e": "BC1_UNORM", "o": "BC4_UNORM",
           "m": "BC1_UNORM", "m1": "BC1_UNORM", "m2": "BC1_UNORM"}
DXGI_CODE = {"BC1_UNORM": 71, "BC3_UNORM": 77, "BC4_UNORM": 80, "BC7_UNORM": 98}


def to_u8(img):
    a = np.clip(np.round(np.asarray(img, np.float32) * 255.0), 0, 255).astype(np.uint8)
    if a.ndim == 2:
        a = a[..., None]
    if a.shape[2] == 1:
        a = np.repeat(a, 3, 2)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full(a.shape[:2] + (1,), 255, np.uint8)], 2)
    return a


def write_rgba_dds(path, rgba_u8):
    """Uncompressed R8G8B8A8_UNORM DDS (DX10 header): texconv input with no colour-space metadata."""
    h, w = rgba_u8.shape[:2]
    hdr = bytearray(124)
    struct.pack_into("<IIIIIII", hdr, 0, 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, w, w * 4, 0, 1)
    struct.pack_into("<II4s", hdr, 72, 32, 0x4, b"DX10")
    struct.pack_into("<I", hdr, 104, 0x1000)
    dx10 = struct.pack("<IIIII", 28, 3, 0, 1, 0)
    with open(path, "wb") as f:
        f.write(b"DDS " + bytes(hdr) + dx10 + np.ascontiguousarray(rgba_u8).tobytes())


def read_dds_header(path):
    with open(path, "rb") as f:
        b = f.read(148)
    if b[:4] != b"DDS ":
        raise ValueError("not a DDS: %s" % path)
    h, w = struct.unpack_from("<II", b, 12)
    mips = struct.unpack_from("<I", b, 28)[0] or 1
    fourcc = b[84:88]
    fmt = struct.unpack_from("<I", b, 128)[0] if fourcc == b"DX10" else \
        {b"DXT1": 71, b"DXT5": 77, b"ATI1": 80, b"BC4U": 80}.get(fourcc)
    return {"width": w, "height": h, "mips": mips, "dxgi": fmt}


def texconv_encode(texconv, rgba_u8, out_path, fmt):
    tmp = tempfile.mkdtemp(prefix="camo_")
    base = os.path.splitext(os.path.basename(out_path))[0]
    src = os.path.join(tmp, base + ".dds")
    write_rgba_dds(src, rgba_u8)
    od = os.path.join(tmp, "out")
    os.makedirs(od)
    cmd = [texconv, "-nologo", "-y", "-dx10", "-m", "0", "-f", fmt, "-o", od, "--", src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    res = os.path.join(od, base + ".dds")
    if r.returncode != 0 or not os.path.isfile(res):
        raise RuntimeError("texconv %s failed: %s %s" % (fmt, r.stdout[-600:], r.stderr[-600:]))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    os.replace(res, out_path)
    for f in os.listdir(od):
        os.remove(os.path.join(od, f))
    os.rmdir(od)
    os.remove(src)
    os.rmdir(tmp)
    return read_dds_header(out_path)


def save_png(path, img):
    from PIL import Image
    Image.fromarray(to_u8(img)[..., :3]).save(path)


def role_preview(roles, names, cfg):
    out = np.zeros(roles.shape + (3,), np.float32)
    for i, nm in enumerate(names):
        c = hex_rgb(cfg["palette"][nm]["hex"])
        if nm == "enamel":
            c = np.array([0.16, 0.16, 0.18], np.float32)
        out[roles == i] = c
    return out


def lit_preview(L, packed, light=(0.35, -0.45, 0.82)):
    """A rough look for iteration (not the game's shading): diffuse x lambert + spec glint + emissive x 1.5."""
    l = np.array(light, np.float32)
    l /= np.linalg.norm(l)
    nrm = packed["_normal"]
    lam = np.clip((nrm * l).sum(-1), 0, 1)[..., None]
    hv = l + np.array([0, 0, 1], np.float32)
    hv /= np.linalg.norm(hv)
    g = packed["sg"][..., 3:4]
    pw = 2 ** (20 * (1 - np.sqrt(1 - np.clip(g, 0, 0.999)))) + 2
    spc = np.clip((nrm * hv).sum(-1, keepdims=True), 0, 1) ** pw * packed["sg"][..., :3] ** 2 * 2.0
    diffuse = packed["c"] ** 2
    lin = diffuse * (0.15 + 0.85 * lam) + spc + np.clip(L["emissive"], 0, 1) * 1.5
    return linear_to_srgb(lin)


def measure(L, cfg):
    roles, names = L["roles"], L["role_names"]
    shares = {nm: float((roles == i).mean()) for i, nm in enumerate(names)}
    checks = {}
    for nm, v in shares.items():
        band = cfg["palette"].get(nm, {}).get("band")
        if band:
            checks[nm] = {"share": round(v, 4), "band": band, "ok": band[0] <= v <= band[1]}
    return shares, checks


def motion_frames(L, cfg, spec, t):
    """The layer-M emissive at time t (seconds), scrolled in numpy as the material would scroll it."""
    n = L["albedo"].shape[0]
    T = float(spec["tile_mm"])
    if "m" in L["motion"]:
        sh = cfg["motion"]["lamp_speed_mm_s"] / T * t * n
        return np.roll(L["motion"]["m"], int(round(sh)), axis=1)
    Mo = cfg["motion"]

    def shift(img, speed, deg):
        dx = speed * t * n * math.cos(math.radians(deg))
        dy = -speed * t * n * math.sin(math.radians(deg))
        return np.roll(np.roll(img, int(round(dy)), 0), int(round(dx)), 1)
    return shift(L["motion"]["m1"], Mo["speed_a_uv_s"], Mo["dir_a_deg"]) * \
        shift(L["motion"]["m2"], Mo["speed_b_uv_s"], Mo["dir_b_deg"])[..., :1]


def motion_preview(name, L, packed, cfg, spec, outdir, frames=48, fps=12, size=384):
    from PIL import Image
    diffuse = packed["c"] ** 2
    imgs, stats = [], []
    for f in range(frames):
        m = motion_frames(L, cfg, spec, f / fps)
        if "m" in L["motion"]:
            on_route = (L["roles"] == 2)[..., None]
            lin = diffuse * 0.5 + np.clip(L["emissive"], 0, 1) * 1.2 + m * 2.0 * (0.3 + 0.7 * on_route)
        else:
            lin = diffuse * 0.5 + m * 2.0
        stats.append(float((m.max(-1) > 0.15).mean()))
        imgs.append(Image.fromarray(to_u8(linear_to_srgb(lin))[..., :3]).resize((size, size), Image.LANCZOS))
    gif = os.path.join(outdir, name + "_motion.gif")
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0)
    w = size // 2
    strip = Image.new("RGB", (w * 8, w))
    for i in range(8):
        strip.paste(imgs[i * frames // 8].resize((w, w), Image.LANCZOS), (i * w, 0))
    strip.save(os.path.join(outdir, name + "_motion_strip.png"))
    return {"gif": os.path.basename(gif), "frames": frames, "fps": fps,
            "visible_share_max": round(max(stats), 4), "visible_share_mean": round(float(np.mean(stats)), 4)}


def build_material(stock, img, uv_scale, emissive_scale, scroll_uv_s=(0.0, 0.0), rotation=(0.0, 0.0)):
    """camo_01 clone on our images. scroll_uv_s: texture tiles per second along U, V (on the gun); rotation:
    (start angle rad, rad/s). Both land in the layer-1 UV transform of the weapon vertex shader."""
    m = copy.deepcopy(stock)
    slots = {3054311504: img + "_c", 2486480606: img + "_n", 3532022562: img + "_sg", 3230247958: img + "_e",
             1253113093: img + "_o"}
    for t in m["textureTable"]:
        if t.get("lastCharacter") == 49 and t["typeHash"] in slots:
            t["image"] = slots[t["typeHash"]]
    for c in m["constantTable"]:
        if c["name"] == "emissivePara" and c["nameHash"] == 1323547990:
            c["literal"] = [float(emissive_scale), 0.0, 0.0, 0.0]
        if c["name"] == "secondarySam" and c["nameHash"] == 4044143062:
            c["literal"] = [float(uv_scale), float(uv_scale), float(scroll_uv_s[0]) / float(uv_scale),
                            float(scroll_uv_s[1]) / float(uv_scale)]
        if c["name"] == "secondarySam" and c["nameHash"] == 28846999:
            c["literal"] = [float(rotation[0]), float(rotation[1]), c["literal"][2], c["literal"][3]]
        if c["name"] == "colorTint1":
            c["literal"] = [1.0, 1.0, 1.0, 1.0]
    return m


def generate(spec, key, size=None, seed=None):
    cfg = spec["camos"][key]
    n = int(size or spec["size"])
    sd = int(spec["seed"] if seed is None else seed)
    rng = np.random.default_rng([sd, sum(map(ord, key))])
    L = (build_carrier if cfg["kind"] == "carrier" else build_mercury)(spec, cfg, n, rng)
    return cfg, L, pack(spec, cfg, L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--texconv", help="texconv.exe (DirectXTex); without it only PNGs are written")
    ap.add_argument("--materials", help="stock camo_01.json to clone into material JSONs")
    ap.add_argument("--only", action="append", help="camo key(s) to build")
    ap.add_argument("--size", type=int)
    ap.add_argument("--material-name", action="append", default=[], help="key=name (default from the spec)")
    ap.add_argument("--image-name", action="append", default=[], help="key=prefix (default from the spec)")
    ap.add_argument("--no-dds", action="store_true")
    ap.add_argument("--no-motion-preview", action="store_true")
    args = ap.parse_args(argv)

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    mat_names = dict(a.split("=", 1) for a in args.material_name)
    img_names = dict(a.split("=", 1) for a in args.image_name)
    img_dir, prev_dir, mat_dir = (os.path.join(args.out, d) for d in ("images", "preview", "materials"))
    os.makedirs(prev_dir, exist_ok=True)
    stock = None
    if args.materials:
        with open(args.materials, encoding="utf-8") as f:
            stock = json.load(f)
    report = {"spec": os.path.abspath(args.spec), "camos": {}}
    ok_all = True
    for key in (args.only or list(spec["camos"])):
        t0 = time.time()
        cfg, L, packed = generate(spec, key, args.size)
        t_gen = time.time() - t0
        img = img_names.get(key, cfg["images"])
        mat = mat_names.get(key, cfg["material"])
        shares, checks = measure(L, cfg)
        images = {k: v for k, v in packed.items() if not k.startswith("_")}
        images.update({k: np.sqrt(np.clip(v, 0, 1)) for k, v in L["motion"].items()})
        seams = {k: seam_metric(v) for k, v in images.items()}
        rec = {"image_prefix": img, "material": mat, "size": int(packed["c"].shape[0]), "generate_s": round(t_gen, 2),
               "shares": {k: round(v, 4) for k, v in shares.items()}, "share_checks": checks,
               "seam": {k: {"wrap_mean_abs_diff": round(a, 5), "ratio_to_interior_max": round(b, 3)}
                        for k, (a, b) in seams.items()},
               "seam_ok": all(b <= spec.get("seam_ratio_max", 1.0) for (_, b) in seams.values()),
               "extra": L["extra"]}
        ok_all &= rec["seam_ok"]
        if cfg["kind"] == "mercury":
            arc = shares["core"] + shares["body"] + shares["teal"]
            rec["arc_share"] = round(arc, 4)
            rec["arc_ok"] = arc <= cfg["arc_max_share"]
            ok_all &= rec["arc_ok"]
        ok_all &= all(c["ok"] for c in checks.values())
        for k, v in images.items():
            save_png(os.path.join(prev_dir, "%s_%s.png" % (img, k)), v[..., :3])
        save_png(os.path.join(prev_dir, "%s_sg_gloss.png" % img), packed["sg"][..., 3])
        save_png(os.path.join(prev_dir, "%s_normal_xyz.png" % img), 0.5 + 0.5 * packed["_normal"])
        save_png(os.path.join(prev_dir, "%s_roles.png" % img), role_preview(L["roles"], L["role_names"], cfg))
        lit = lit_preview(L, packed)
        save_png(os.path.join(prev_dir, "%s_lit.png" % img), lit)
        save_png(os.path.join(prev_dir, "%s_lit_tiled2x2.png" % img), np.tile(lit, (2, 2, 1))[::2, ::2])
        if not args.no_motion_preview:
            rec["motion_preview"] = motion_preview(img, L, packed, cfg, spec, prev_dir)
        if args.texconv and not args.no_dds:
            os.makedirs(img_dir, exist_ok=True)
            t1 = time.time()
            rec["dds"] = {}
            for k, v in images.items():
                fmt = FORMATS[k]
                path = os.path.join(img_dir, "%s_%s.dds" % (img, k))
                hdr = texconv_encode(args.texconv, to_u8(v), path, fmt)
                hdr["format"] = fmt
                rec["dds"][os.path.basename(path)] = hdr
            rec["encode_s"] = round(time.time() - t1, 2)
        if stock is not None:
            os.makedirs(mat_dir, exist_ok=True)
            uv_scale = round(float(spec["camo_uv_mm_per_unit"]) / float(spec["tile_mm"]), 4)
            mm = cfg.get("material_motion", {})
            m = build_material(stock, img, uv_scale, cfg["emissive_max_strength"], mm.get("scroll_uv_s", (0.0, 0.0)),
                               mm.get("rotation", (0.0, 0.0)))
            mp = os.path.join(mat_dir, mat + ".json")
            with open(mp, "w", encoding="utf-8") as f:
                json.dump(m, f, indent=4)
            rec["material_json"] = os.path.basename(mp)
            rec["uv_scale"] = uv_scale
        report["camos"][key] = rec
        print("%s: generated %dpx in %.1fs" % (key, rec["size"], t_gen))
        for nm, c in checks.items():
            print("   %-10s %.4f  band %-14s %s" % (nm, c["share"], c["band"], "ok" if c["ok"] else "OUT"))
        if "arc_share" in rec:
            print("   arc total  %.4f  max %.2f  %s" % (rec["arc_share"], cfg["arc_max_share"], "ok" if rec["arc_ok"] else "OUT"))
        print("   seam ratio (wrap / interior max): " + ", ".join("%s %.2f" % (k, v[1]) for k, v in seams.items()))
        if "motion_preview" in rec:
            mp_ = rec["motion_preview"]
            print("   motion: visible share max %.4f mean %.4f" % (mp_["visible_share_max"], mp_["visible_share_mean"]))
        if "encode_s" in rec:
            print("   dds: %d files in %.1fs" % (len(rec["dds"]), rec["encode_s"]))
    report["all_ok"] = bool(ok_all)
    with open(os.path.join(args.out, "camo_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("all checks ok:", ok_all)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
