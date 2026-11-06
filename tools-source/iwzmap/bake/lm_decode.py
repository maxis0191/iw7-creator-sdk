"""Decode an IW7 lightmap set (HDR) and query texels.

usage: lm_decode.py <images dir> <out dir> [--prefix _lightmap0] [u v ...]

Reads <prefix>_primary / _secondary / _secondunorm .iw7Image, decodes them to float (texconv), writes
<out>/{A,B,D,S}.npy and PNG previews, prints statistics and, per (u, v) lightmap coordinate, the decoded terms:
  A  secondary top half    (u, v/2)        non-directional irradiance (linear RGB, radiance units)
  B  secondary bottom half (u, v/2 + 1/2)  directional irradiance colour along D
  D  secondunorm R8G8      (u, v)          dominant direction, rotated octahedral, tangent space
  S  primary BC4           (u, v)          sun visibility (0.5 = shadow edge)
Diffuse irradiance the world shader uses (lit-surface pixel shader, see bake/README):
  E = A + ssao * B * saturate(dot(N, D_world)),  outgoing diffuse ~= albedo * E.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iw7image


def oct_decode(rg):
    a = rg[..., 0] * 2 - 1; b = rg[..., 1] * 2 - 1
    x = (a + b) * 0.5; y = (a - b) * 0.5
    z = 1 - np.abs(x) - np.abs(y)
    v = np.stack([x, y, z], -1)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-8)


def load_set(src, prefix='_lightmap0', work=None):
    out = {}
    for kind in ('primary', 'secondary', 'secondunorm'):
        im = iw7image.read_iw7image(os.path.join(src, '%s_%s.iw7Image' % (prefix, kind)))
        out[kind] = (im, iw7image.decode(im['format'], im['width'], im['height'], im['data'], work))
    sec = out['secondary'][1]
    h = sec.shape[0] // 2
    return {'A': sec[:h, :, :3], 'B': sec[h:, :, :3], 'D': oct_decode(out['secondunorm'][1]),
            'S': out['primary'][1][..., 0], 'images': {k: v[0] for k, v in out.items()}}


def texel(arr, u, v):
    h, w = arr.shape[:2]
    return arr[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w)))]


def preview(path, rgb, scale=1.0):
    from PIL import Image
    x = np.clip(rgb * scale, 0, None)
    x = x / (1 + x)                                  # Reinhard for viewing
    x = (np.power(x, 1 / 2.2) * 255).astype(np.uint8)
    im = Image.fromarray(x)
    if im.width > 2048: im = im.resize((im.width // 4, im.height // 4))
    im.save(path)


if __name__ == '__main__':
    args = sys.argv[1:]
    prefix = '_lightmap0'
    if '--prefix' in args:
        i = args.index('--prefix'); prefix = args[i + 1]; del args[i:i + 2]
    src, out = args[:2]
    coords = [float(c) for c in args[2:]]
    os.makedirs(out, exist_ok=True)
    s = load_set(src, prefix, os.path.join(out, 'tmp'))
    for k in 'ABDS':
        np.save(os.path.join(out, k + '.npy'), s[k].astype(np.float32))
    for k, im in s['images'].items():
        print('%s: %s fmt %d %dx%d' % (k, im['name'], im['format'], im['width'], im['height']))
    for k in 'AB':
        a = s[k].reshape(-1, 3)
        print('%s mean %s p50 %s p99 %s max %s' % (k, a.mean(0).round(4), np.percentile(a, 50, 0).round(4),
                                                  np.percentile(a, 99, 0).round(4), a.max(0).round(3)))
        preview(os.path.join(out, k + '.png'), s[k])
    d = s['D'].reshape(-1, 3)
    print('D mean z %.3f, share z>0.9 %.3f' % (d[:, 2].mean(), (d[:, 2] > 0.9).mean()))
    preview(os.path.join(out, 'D.png'), s['D'] * 0.5 + 0.5, 1.0)
    print('S mean %.3f share >0.5 %.3f' % (s['S'].mean(), (s['S'] > 0.5).mean()))
    for i in range(0, len(coords) - 1, 2):
        u, v = coords[i], coords[i + 1]
        print('uv %.4f %.4f  A %s  B %s  D %s  S %.3f' % (u, v, texel(s['A'], u, v).round(4), texel(s['B'], u, v).round(4),
                                                          texel(s['D'], u, v).round(3), texel(s['S'], u, v)))
