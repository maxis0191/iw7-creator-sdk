"""Texture output for the iwzmap pipeline.

The map zone ingests custom images through ZoneTool (x64-zt iw7 gfximage.cpp, directxtex::load_image): it looks for
images/<name>.dds first, then images/<name>.tga, and stores the pixels as loaded (TGA -> R8G8B8A8_UNORM, ONE mip
level). Mip-less textures shimmer and alias at distance (text, grime speckle), so every asset is written as:

  <name>.png        lossless master (RGB or RGBA)
  <name>_c.tga      32-bit uncompressed TGA, the format the generator already ships (proven path: the sign art)
  <name>_c.dds      R8G8B8A8_UNORM DDS with a full mip chain (gamma-aware, premultiplied-alpha box filter).
                    ZoneTool loads it before the TGA when both sit in images/ (NOT_PROVEN in engine yet).
"""
import os
import struct

import numpy as np
from PIL import Image


def to_u8(a):
    a = np.asarray(a)
    if a.dtype == np.uint8:
        return a
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def as_image(a):
    if isinstance(a, Image.Image):
        return a
    a = to_u8(a)
    if a.ndim == 2:
        return Image.fromarray(a, 'L')
    return Image.fromarray(a, 'RGBA' if a.shape[2] == 4 else 'RGB')


def _mips(rgba):
    """Full mip chain of an RGBA uint8 array: average in linear light with premultiplied alpha."""
    levels = [rgba]
    cur = rgba.astype(np.float32) / 255.0
    lin = cur.copy()
    lin[..., :3] = lin[..., :3] ** 2.2
    lin[..., :3] *= lin[..., 3:4]
    while lin.shape[0] > 1 or lin.shape[1] > 1:
        h, w = lin.shape[:2]
        h2, w2 = max(1, h // 2), max(1, w // 2)
        if h > 1 and w > 1:
            lin = lin[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 4).mean(axis=(1, 3))
        elif h > 1:
            lin = lin[:h2 * 2].reshape(h2, 2, w, 4).mean(axis=1)
        else:
            lin = lin[:, :w2 * 2].reshape(h, w2, 2, 4).mean(axis=2)
        out = lin.copy()
        a = np.maximum(out[..., 3:4], 1e-6)
        out[..., :3] = np.clip(out[..., :3] / a, 0, 1) ** (1 / 2.2)
        out[..., :3] = np.where(lin[..., 3:4] > 1e-6, out[..., :3], 0)
        levels.append(to_u8(out))
    return levels


def write_dds(path, rgba):
    """Legacy-header DDS, 32-bit RGBA (masks R=0xff, G=0xff00, B=0xff0000, A=0xff000000 = DXGI R8G8B8A8_UNORM)."""
    rgba = to_u8(rgba)
    h, w = rgba.shape[:2]
    levels = _mips(rgba)
    DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PITCH, DDSD_PIXELFORMAT, DDSD_MIPMAPCOUNT = 1, 2, 4, 8, 0x1000, 0x20000
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PITCH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT
    pf = struct.pack('<II4sIIIII', 32, 0x41, b'\0\0\0\0', 32, 0xFF, 0xFF00, 0xFF0000, 0xFF000000)
    caps = 0x1000 | 0x400000 | 0x8          # TEXTURE | MIPMAP | COMPLEX
    header = struct.pack('<IIIIIII', 124, flags, h, w, w * 4, 0, len(levels)) + b'\0' * 44 + pf + \
        struct.pack('<IIIII', caps, 0, 0, 0, 0)
    assert len(header) == 124
    with open(path, 'wb') as f:
        f.write(b'DDS ' + header)
        for lv in levels:
            f.write(np.ascontiguousarray(lv).tobytes())
    return len(levels)


def read_dds_info(path):
    d = open(path, 'rb').read(128)
    assert d[:4] == b'DDS '
    size, flags, h, w, pitch, depth, mips = struct.unpack('<IIIIIII', d[4:32])
    return {'width': w, 'height': h, 'mips': mips, 'bytes': os.path.getsize(path)}


def save_all(a, out_dir, name, alpha=None):
    """Write <name>.png, <name>_c.tga and <name>_c.dds. `alpha` forces RGBA (True) or RGB (False) for the PNG;
    the TGA/DDS are always 32-bit RGBA (opaque alpha 255 when the asset has none), as the shipped signs are."""
    os.makedirs(out_dir, exist_ok=True)
    im = as_image(a)
    if im.mode == 'L':
        im = im.convert('RGB')
    if alpha is True:
        im = im.convert('RGBA')
    elif alpha is False:
        im = im.convert('RGB')
    w, h = im.size
    # The art list fixes the sizes; 512x768 posters are not power-of-two (as the shipped posters), so require only
    # multiples of 4 (block-compression friendly) and report the power-of-two state in the result.
    assert w % 4 == 0 and h % 4 == 0, (name, im.size, 'not a multiple of 4')
    png = os.path.join(out_dir, name + '.png')
    im.save(png, optimize=True)
    rgba = im.convert('RGBA')
    rgba.save(os.path.join(out_dir, name + '_c.tga'))
    n = write_dds(os.path.join(out_dir, name + '_c.dds'), np.asarray(rgba))
    return {'name': name, 'size': [w, h], 'mode': im.mode, 'mips': n,
            'pow2': bool(w & (w - 1) == 0 and h & (h - 1) == 0)}
