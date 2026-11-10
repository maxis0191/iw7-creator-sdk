import os, re, sys
import numpy as np
from PIL import Image, ImageDraw
run, out = sys.argv[1], sys.argv[2]
names = sorted(set(re.sub(r'_(off|on\d)\.bmp$', '', f) for f in os.listdir(run) if f.startswith('iwzp_') and f.endswith('.bmp')))
tiles = []
for n in names:
    off = np.asarray(Image.open(os.path.join(run, n + '_off.bmp')).convert('RGB')).astype(np.float32)
    on = np.asarray(Image.open(os.path.join(run, n + '_on1.bmp')).convert('RGB')).astype(np.float32)
    h, w = off.shape[:2]
    x0, x1, y0, y1 = int(w * 0.2), int(w * 0.8), int(h * 0.05), int(h * 0.6)
    d = np.clip(np.abs(on - off).mean(axis=2) * 4, 0, 255)
    a = Image.fromarray(off[y0:y1, x0:x1].astype(np.uint8)); b = Image.fromarray(on[y0:y1, x0:x1].astype(np.uint8))
    c = Image.fromarray(d[y0:y1, x0:x1].astype(np.uint8)).convert('RGB')
    t = Image.new('RGB', (a.width * 3 + 8, a.height + 18)); t.paste(a, (0, 18)); t.paste(b, (a.width + 4, 18)); t.paste(c, (2 * a.width + 8, 18))
    ImageDraw.Draw(t).text((4, 2), n, fill=(255, 255, 0)); tiles.append(t.resize((t.width // 2, t.height // 2)))
os.makedirs(out, exist_ok=True)
for i in range(0, len(tiles), 7):
    grp = tiles[i:i + 7]
    s = Image.new('RGB', (grp[0].width, sum(t.height for t in grp)))
    y = 0
    for t in grp: s.paste(t, (0, y)); y += t.height
    s.save(os.path.join(out, 'sheet_%d.jpg' % (i // 7)), quality=85)
print(len(tiles))
