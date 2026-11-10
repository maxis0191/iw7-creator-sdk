"""Age existing sign/poster textures with the procedural grime overlay (review B: "signs look newly installed").

usage: python -m art.age <in dir with *_c.tga> <out dir> [strength 0..1]

The overlay is synthesized at each sign's own size (masks.sign_grime_overlay), so the top-edge runs keep their shape
on 4:1 signs instead of being squashed from a square overlay. Seeds derive from the file name: re-running gives the
same bytes, and no two signs share the same grime.
"""
import os
import sys
import zlib

import numpy as np
from PIL import Image

from . import masks as M
from . import texio as T


def apply_overlay(rgb, seed, strength=0.8):
    """rgb float [0,1] HxWx3 -> aged rgb."""
    h, w = rgb.shape[:2]
    ov = M.sign_grime_overlay(w, h, seed)
    a = ov[..., 3:4] * strength
    return np.clip(rgb * (1 - a) + ov[..., :3] * a, 0, 1)


def age_dir(src, dst, strength=0.8):
    os.makedirs(dst, exist_ok=True)
    done = []
    for f in sorted(os.listdir(src)):
        if not f.endswith('_c.tga'):
            continue
        name = f[:-6]
        rgb = np.asarray(Image.open(os.path.join(src, f)).convert('RGB'), np.float32) / 255
        aged = apply_overlay(rgb, zlib.crc32(name.encode()) & 0xFFFF, strength)
        done.append(T.save_all(aged, dst, name))
    return done


if __name__ == '__main__':
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    for r in age_dir(sys.argv[1], sys.argv[2], s):
        print(r)
