"""Soot bloom decal for the G-2 (review g27d item 15: the scorch was not visible).

usage (from tools-source/iwzmap): python -I -m art.soot <art dir>  -> <art dir>/story/decal_soot_bloom.png + _c.tga
A burn mark on a wall / cabinet face above a hot or shorted part: a dense black core low down, rising and widening
like smoke deposit (heat carries the soot upward), feathered fbm edges, fine streaks where the smoke licked up, the
alpha falling to 0 on every border. Colour near-black brown; straight alpha. Material: the lit alpha blend decal
(base wall_stain_01_dec, the route the blood smears use on walls).
"""
import os, sys

import numpy as np
from PIL import Image

from . import noise as N


def soot_bloom(w=512, h=768, seed=5101):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx - w / 2) / (w / 2)                 # -1..1 across
    v = 1.0 - yy / h                           # 0 at the bottom, 1 at the top
    # plume: narrow and dense at the source (v ~ 0.15), widening and thinning upward
    width = 0.25 + 0.75 * np.clip(v, 0, 1) ** 0.8
    core = np.exp(-(u / width) ** 2 * 2.2) * np.clip((v - 0.06) / 0.12, 0, 1) * (1.0 - 0.55 * np.clip(v, 0, 1))
    f = N.warp(N.fbm((h, w), seed=seed, octaves=6, base=0.006), seed=seed + 1, amount=30.0)
    f = N.normalize(f)
    a = np.clip(core * (0.55 + 0.75 * f) - 0.12, 0, 1)
    st = N.streaks((h, w), seed + 2, 26, length=(0.25, 0.7), width=(2.0, 6.0), x_range=(0.3, 0.7), y0_range=(0.55, 0.8))
    st = np.asarray(st, np.float32)
    if st.shape == a.shape:
        a = np.clip(a + 0.25 * st * np.clip(v - 0.1, 0, 1) * (np.abs(u) < width), 0, 1)
    a *= N.border_falloff((h, w), 40, seed=seed + 3, wobble=0.3)
    a = np.clip(a * 1.15, 0, 0.95)
    col = np.zeros((h, w, 3), np.float32)
    col[...] = np.array([0.045, 0.035, 0.028], np.float32)
    col += (f[..., None] - 0.5) * 0.03
    rgba = np.concatenate([np.clip(col, 0, 1), a[..., None]], -1)
    return (rgba * 255 + 0.5).astype(np.uint8)


def main():
    out = os.path.join(sys.argv[1], 'story')
    os.makedirs(out, exist_ok=True)
    im = Image.fromarray(soot_bloom(), 'RGBA')
    im.save(os.path.join(out, 'decal_soot_bloom.png'))
    im.save(os.path.join(out, 'decal_soot_bloom_c.tga'))
    print('soot', im.size)


if __name__ == '__main__':
    main()
