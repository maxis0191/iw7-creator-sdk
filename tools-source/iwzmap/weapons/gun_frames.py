"""Frame facts for a gun held in first person: which pixels are the gun (by the engine's depth, iw7_see), what colours
they hold against a camo's palette roles, and how much of the gun's surface changed between frames of the same view.

usage: gun_frames.py <run dir> --views p_ec_carrier,p_ec_mercury,... [--spec camos.json] [--near 48] [--json out.json]
       Each view is three captures of a gamelab plan: <view>_a, _b (1 s later), _c (3 s later), with depth.

Per view: gun share of the frame, the share of gun pixels near each palette colour of each camo in camos.json (a
colour counts when its Lab-like distance to the pixel is under a threshold and the pixel is not darker than the
colour's own floor), the dominant hues, and the motion: the mean absolute change of gun pixels between a/b and a/c
over the pixels that are gun in both frames, against the change of the background (sway and the camo both move the
gun's pixels; a static camo on a swaying gun changes edges, a moving camo changes the inside: the 'interior' measure
erodes the mask by 6 pixels). The numbers are facts for the reviewers' brief, not a verdict on the look.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "worldkit"))
import iw7_see  # noqa: E402


def read_bmp(path):
    with open(path, "rb") as f:
        b = f.read()
    off = int.from_bytes(b[10:14], "little")
    w = int.from_bytes(b[18:22], "little", signed=True)
    h = int.from_bytes(b[22:26], "little", signed=True)
    bpp = int.from_bytes(b[28:30], "little")
    step = bpp // 8
    row = (w * step + 3) & ~3
    a = np.frombuffer(b, dtype=np.uint8, count=row * abs(h), offset=off).reshape(abs(h), row)[:, :w * step]
    a = a.reshape(abs(h), w, step)[:, :, :3][:, :, ::-1]
    if h > 0:
        a = a[::-1]
    return a.astype(np.float64) / 255.0


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def erode(m, k):
    out = m.copy()
    for _ in range(k):
        o = out.copy()
        o[1:, :] &= out[:-1, :]
        o[:-1, :] &= out[1:, :]
        o[:, 1:] &= out[:, :-1]
        o[:, :-1] &= out[:, 1:]
        out = o
    return out


def gun_mask(frame_path, near):
    fr = iw7_see.Frame(frame_path)
    z = fr.z_buffer()
    if z is None:
        raise SystemExit("%s: no depth beside the capture" % frame_path)
    rgb = read_bmp(frame_path)
    m = z < near
    if m.shape != rgb.shape[:2]:
        ys = (np.arange(rgb.shape[0]) * m.shape[0] // rgb.shape[0])
        xs = (np.arange(rgb.shape[1]) * m.shape[1] // rgb.shape[1])
        m = m[ys][:, xs]
    return rgb, m


def hue(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0)
    return h, s, mx


def palette_shares(px, spec):
    out = {}
    h, s, v = hue(px)
    for key, cfg in spec["camos"].items():
        roles = {}
        for role, c in cfg["palette"].items():
            col = hexrgb(c["hex"])
            ch, cs, cv = hue(col[None, :])
            if cs[0] > 0.35:      # a saturated colour: match by hue and saturation, any brightness above a floor
                dh = np.minimum(abs(h - ch[0]), 360 - abs(h - ch[0]))
                hit = (dh < 18) & (s > 0.45) & (v > 0.12)
            else:                 # a neutral: match by brightness band
                hit = (s < 0.25) & (abs(v - cv[0]) < 0.08)
            roles[role] = round(float(hit.mean()), 4) if px.size else 0.0
        out[key] = roles
    bins = np.histogram(h[(s > 0.45) & (v > 0.12)], bins=12, range=(0, 360))[0]
    out["saturated_share"] = round(float(((s > 0.45) & (v > 0.12)).mean()), 4)
    out["hue_bins_30deg"] = [int(b) for b in bins]
    out["mean_rgb"] = [round(float(x), 4) for x in px.mean(0)] if len(px) else []
    return out


def view_facts(run, view, spec, near):
    caps = []
    for suf in ("a", "b", "c"):
        p = os.path.join(run, "iwz_%s_%s.bmp" % (view, suf))
        if not os.path.exists(p):
            return {"view": view, "missing": p}
        caps.append(gun_mask(p, near))
    (a, ma), (b, mb), (c, mc) = caps
    facts = {"view": view, "gun_share": round(float(ma.mean()), 4)}
    facts["palette"] = palette_shares(a[ma], spec)
    for name, (x, mx) in (("ab", (b, mb)), ("ac", (c, mc))):
        both = ma & mx
        inner = erode(both, 6)
        bg = ~(ma | mx)
        facts["motion_" + name] = {
            "gun_mean_abs": round(float(np.abs(a - x)[both].mean()), 4) if both.any() else None,
            "gun_interior_mean_abs": round(float(np.abs(a - x)[inner].mean()), 4) if inner.any() else None,
            "background_mean_abs": round(float(np.abs(a - x)[bg].mean()), 4) if bg.any() else None,
            "mask_iou": round(float(both.sum() / max(1, (ma | mx).sum())), 4)}
    return facts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run")
    ap.add_argument("--views", required=True)
    ap.add_argument("--spec", default=os.path.join(HERE, "camos.json"))
    ap.add_argument("--near", type=float, default=48.0, help="gun pixels: forward distance under this (units)")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    res = [view_facts(a.run, v, spec, a.near) for v in a.views.split(",")]
    for f in res:
        if "missing" in f:
            print("%-16s missing %s" % (f["view"], f["missing"]))
            continue
        p = f["palette"]
        print("%-16s gun %.3f  carrier route %.3f lamp %.3f enamel %.3f | mercury skin %.3f arc_body %.3f core %.3f | sat %.3f"
              % (f["view"], f["gun_share"], p["carrier"].get("route", 0), p["carrier"].get("lamp", 0),
                 p["carrier"].get("enamel", 0), p["mercury"].get("skin", 0), p["mercury"].get("body", 0),
                 p["mercury"].get("core", 0), p["saturated_share"]))
        for k in ("ab", "ac"):
            m = f["motion_" + k]
            print("%16s motion %s: gun %.4s interior %s background %s iou %s" % (
                "", k, m["gun_mean_abs"], m["gun_interior_mean_abs"], m["background_mean_abs"], m["mask_iou"]))
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
