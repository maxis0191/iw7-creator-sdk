"""Review previews: composite RGBA assets over representative surfaces so they are judged as they will be seen.

usage: python -m art.preview <asset.png> <out.png> [surface: tile|concrete|plate|cream|checker] [tile N]
"""
import sys

import numpy as np
from PIL import Image

from . import noise as N

SURFACES = {
    'tile': (0.86, 0.87, 0.84),      # white ceramic metro tile
    'concrete': (0.52, 0.51, 0.49),
    'plate': (0.42, 0.43, 0.44),     # diamond plate steel
    'cream': (0.90, 0.85, 0.72),
}


def surface(kind, w, h, seed=1):
    if kind == 'checker':
        yy, xx = np.mgrid[0:h, 0:w]
        c = (((xx // 32) + (yy // 32)) % 2) * 0.25 + 0.5
        return np.dstack([c, c, c]).astype(np.float32)
    base = np.array(SURFACES[kind], np.float32)
    var = (N.fbm((h, w), seed, 4, base=0.01) - 0.5) * 0.06
    s = np.clip(base[None, None, :] + var[..., None], 0, 1)
    if kind == 'tile':                # grout lines every 64 px
        yy, xx = np.mgrid[0:h, 0:w]
        grout = ((xx % 64) < 2) | ((yy % 32) < 2)
        s[grout] *= 0.7
    return s


def composite(rgba, kind='tile'):
    a = np.asarray(rgba, np.float32)
    if a.max() > 1.5:
        a = a / 255.0
    h, w = a.shape[:2]
    if a.shape[2] == 3:
        return a
    bg = surface(kind, w, h)
    return a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4])


def multiply(rgb_mask, kind='plate'):
    a = np.asarray(rgb_mask, np.float32)
    if a.max() > 1.5:
        a = a / 255.0
    h, w = a.shape[:2]
    return surface(kind, w, h) * a[..., :3]


if __name__ == '__main__':
    src, dst = sys.argv[1:3]
    kind = sys.argv[3] if len(sys.argv) > 3 else 'tile'
    tiles = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    im = np.asarray(Image.open(src).convert('RGBA'), np.float32) / 255
    if tiles > 1:
        im = np.tile(im, (tiles, tiles, 1))
    out = multiply(im, kind) if kind == 'plate' else composite(im, kind)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(dst)
