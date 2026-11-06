"""Decode the template lightmap atlas (cp_zmb) to find texels for generated surfaces.

usage: lightmap_read.py <template images dir> <out dir> [u v ...]
Writes previews of the primary (BC4), secondary (BC6H) and secondunorm (R8G8) images, and prints the texel
values at the given lightmap coordinates.
"""
import os, sys
import numpy as np
import texture2ddecoder as t
from PIL import Image

src, out = sys.argv[1:3]
coords = [float(c) for c in sys.argv[3:]]
os.makedirs(out, exist_ok=True)


def load(name):
    b = open(os.path.join(src, name + '.iw7Image'), 'rb').read()
    fmt, length = int.from_bytes(b[30:34], 'little'), int.from_bytes(b[46:50], 'little')
    w, h = int.from_bytes(b[54:56], 'little'), int.from_bytes(b[56:58], 'little')
    return fmt, w, h, b[-length:]


images = {}
for name in ('_lightmap0_primary', '_lightmap0_secondary', '_lightmap0_secondunorm'):
    fmt, w, h, data = load(name)
    if fmt == 80:
        rgba = np.frombuffer(t.decode_bc4(data, w, h), np.uint8).reshape(h, w, 4)
    elif fmt == 95:
        rgba = np.frombuffer(t.decode_bc6(data, w, h), np.uint8).reshape(h, w, 4)
    elif fmt == 49:
        rg = np.frombuffer(data, np.uint8).reshape(h, w, 2)
        rgba = np.zeros((h, w, 4), np.uint8); rgba[..., 2] = rg[..., 0]; rgba[..., 1] = rg[..., 1]; rgba[..., 3] = 255
    else:
        raise SystemExit('format %d' % fmt)
    rgb = rgba[..., [2, 1, 0]]  # BGRA -> RGB
    images[name] = rgb
    Image.fromarray(rgb).resize((w // 4, h // 4)).save(os.path.join(out, name + '.png'))
    np.save(os.path.join(out, name + '.npy'), rgb)
    print(name, fmt, w, h, 'mean', rgb.reshape(-1, 3).mean(0).round(1))

for i in range(0, len(coords) - 1, 2):
    u, v = coords[i], coords[i + 1]
    for name, rgb in images.items():
        h, w = rgb.shape[:2]
        print('uv %.4f %.4f' % (u, v), name, rgb[min(h - 1, int(v * h)), min(w - 1, int(u * w))])
