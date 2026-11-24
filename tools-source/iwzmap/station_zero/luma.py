"""luma: p5 / p50 / p95 of the displayed frames, the way C:\\studio\\rooms\\lightstats.py defines them (top 88 % of the picture, Rec. 709 luma of the 0..1 pixel values).

    python luma.py <frames folder> [out.json]
"""
import json
import os
import sys

import numpy as np
from PIL import Image


def stats(path, top=0.88):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0
    im = im[:int(im.shape[0] * top)]
    luma = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    p5, p50, p95 = np.percentile(luma, [5, 50, 95])
    return {'p5': round(float(p5), 3), 'p50': round(float(p50), 3), 'p95': round(float(p95), 3), 'under_008': round(float((luma < 0.08).mean()), 3),
            'over_085': round(float((luma > 0.85).mean()), 3), 'size': [im.shape[1], int(im.shape[0] / top)]}


def main():
    folder = sys.argv[1]
    out = {}
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith('.png'):
            out[f[:-4]] = stats(os.path.join(folder, f))
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
