"""Measure a small model in a native game frame: is it drawn textured, and at what scale (numpy + PIL).

    python model_frame.py --frame iwzbear0.bmp [--pair] [--albedo 155,98,64] [--out frame.json] [--mask mask.png]

The fixture frames a model on a plain floor: `--pair` when a stock reference model of known height stands
beside it (left and right halves of the view). In the central region (HUD rows excluded) the tool keeps the
pixels whose colour is warm and saturated like the model's albedo (hue within 25 degrees of it, saturation
above a third of the albedo's), takes the connected blob (>= 40 pixels) nearest to the centre of each half
(the fixture aims at the model; hands and HUD lie off centre), and reports its bounding box,
pixel count, mean colour and hue. A model drawn black (lost normals, missing textures, lighting from below
the floor) has no such blob; the darkest blob is reported instead. With `--pair`, height_ratio = left blob
height / right blob height (same camera distance: the ratio of the two models' heights).
"""
import argparse
import colorsys
import json

import numpy as np
from PIL import Image


def hue_deg(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
    return h * 360.0, s, v


def blobs(mask):
    """Connected components (4-neighbour) of a boolean mask: list of (count, ys, xs)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack, ys, xs = [(y0, x0)], [], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            ys.append(y)
            xs.append(x)
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append((len(ys), np.array(ys), np.array(xs)))
    out.sort(key=lambda b: -b[0])
    return out


def describe(img, blob, y_off, x_off):
    n, ys, xs = blob
    px = img[ys, xs].astype(float)
    mean = px.mean(axis=0)
    h, s, v = hue_deg(mean)
    return {'pixels': int(n), 'bbox': [int(xs.min() + x_off), int(ys.min() + y_off), int(xs.max() + x_off), int(ys.max() + y_off)],
            'height_px': int(ys.max() - ys.min() + 1), 'width_px': int(xs.max() - xs.min() + 1),
            'mean_rgb': [round(float(c), 1) for c in mean], 'hue_deg': round(h, 1), 'saturation': round(s, 3), 'value': round(v, 3)}


def measure(frame, albedo, pair=False, top=0.08, bottom=0.82, min_pixels=40):
    img = np.asarray(Image.open(frame).convert('RGB'))
    H, W, _ = img.shape
    y0, y1 = int(H * top), int(H * bottom)
    roi = img[y0:y1].astype(float) / 255.0
    mx, mn = roi.max(axis=2), roi.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    hue = (np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) + 360) % 360
    ah, asat, _ = hue_deg(albedo)
    dh = np.minimum(np.abs(hue - ah), 360 - np.abs(hue - ah))
    warm = (dh < 25) & (sat > asat / 3) & (mx > 0.15)   # near-black (value < 0.15) is not "drawn textured"
    dark = mx < 0.12
    halves = [('left', 0, W // 2), ('right', W // 2, W)] if pair else [('view', 0, W)]
    result = {'frame': frame, 'size': [W, H], 'albedo_rgb': list(albedo), 'albedo_hue_deg': round(ah, 1), 'parts': {}}
    cy = H / 2 - y0
    for name, a, b in halves:
        part = {}
        cx = (b - a) / 2

        def nearest(found):
            return min(found, key=lambda bl: (bl[1].mean() - cy) ** 2 + (bl[2].mean() - cx) ** 2)
        found = [bl for bl in blobs(warm[:, a:b]) if bl[0] >= min_pixels]
        if found:
            part['textured'] = describe(img[y0:y1, a:b], nearest(found), y0, a)
        darks = [bl for bl in blobs(dark[:, a:b]) if bl[0] >= min_pixels]
        if darks:
            part['darkest_blob'] = describe(img[y0:y1, a:b], nearest(darks), y0, a)
        result['parts'][name] = part
    if pair:
        l, r_ = result['parts']['left'].get('textured'), result['parts']['right'].get('textured')
        if l and r_:
            result['height_ratio_left_over_right'] = round(l['height_px'] / r_['height_px'], 3)
    return result, (warm, y0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--frame', required=True)
    ap.add_argument('--albedo', default='155,98,64', help='mean albedo of the model texture (R,G,B 0..255)')
    ap.add_argument('--pair', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--mask', help='PNG of the kept pixels, for review')
    args = ap.parse_args(argv)
    albedo = tuple(int(v) for v in args.albedo.split(','))
    result, (warm, y0) = measure(args.frame, albedo, args.pair)
    if args.mask:
        img = np.asarray(Image.open(args.frame).convert('RGB')).copy()
        view = img[y0:y0 + warm.shape[0]]
        view[warm] = (255, 0, 255)
        Image.fromarray(img).save(args.mask)
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
