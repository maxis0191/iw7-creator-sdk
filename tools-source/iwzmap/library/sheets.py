"""Contact sheets of the library: every library model, 3/4 view with its textures, 256 px tiles, 48 a sheet.

  python -B sheets.py [--zones ...] [--groups ...] [--res 256] [--workers 4] [--limit N] [--out DIR]

Needs the prep stage first (python -B prep.py). Tiles are rendered by background Blender processes (blender_tiles.py),
composed with PIL into `<out>/sheets/<group>/<zone>_<n>.png` and listed in `<out>/sheets/index.json`
(sheet -> models with row, column and the model's numbers). A model that failed to load or whose texture did not
resolve gets a magenta tile (all magenta for a load failure) and is listed in `<out>/sheets/failures.json` with the reason.
"""
import argparse
import json
import os
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

COLS, ROWS = 8, 6
PER_SHEET = COLS * ROWS
LABEL_H = 40
HEADER_H = 22
BG = (38, 38, 40)


def blender_exe():
    return os.environ.get('IWZ_BLENDER') or os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                                                         'Blender Foundation', 'Blender 5.2', 'blender.exe')


def font(size):
    for name in ('segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def render_tiles(items, res, engine, workers, workdir, log=print):
    """items: [{'name', 'prep', 'out'}] -> {name: result}. Splits across `workers` Blender processes."""
    os.makedirs(workdir, exist_ok=True)
    chunks = [items[i::workers] for i in range(workers)]
    procs = []
    for k, ch in enumerate(chunks):
        if not ch:
            continue
        jp = os.path.join(workdir, 'job%d.json' % k)
        json.dump({'res': res, 'engine': engine, 'items': ch}, open(jp, 'w'))
        if os.path.isfile(jp + '.result.json'):
            os.remove(jp + '.result.json')
        procs.append((jp, subprocess.Popen([blender_exe(), '-b', '--factory-startup', '--python',
                                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blender_tiles.py'), '--', jp],
                                           stdout=open(jp + '.log', 'w'), stderr=subprocess.STDOUT)))
    results = {}
    for jp, p in procs:
        p.wait()
        rp = jp + '.result.json'
        if os.path.isfile(rp):
            results.update(json.load(open(rp))['results'])
        else:
            log('blender worker %s ended without a result (see %s.log)' % (jp, jp))
    return results


def tile_image(path, res, ok, reason):
    if ok and os.path.isfile(path):
        return Image.open(path).convert('RGB')
    im = Image.new('RGB', (res, res), (255, 0, 255))
    d = ImageDraw.Draw(im)
    f = font(11)
    words, line, y = (reason or 'no tile').split(), '', 8
    for w in words:
        if d.textlength(line + ' ' + w, font=f) > res - 16:
            d.text((8, y), line, fill=(0, 0, 0), font=f)
            y += 14
            line = w
        else:
            line = (line + ' ' + w).strip()
    d.text((8, y), line, fill=(0, 0, 0), font=f)
    return im


def fit(text, d, f, width):
    if d.textlength(text, font=f) <= width:
        return text
    while len(text) > 3 and d.textlength(text + '...', font=f) > width:
        text = text[:-1]
    return text + '...'


def compose(entries, out_png, title, res=256, cols=COLS):
    """entries: [{'name', 'tile': png, 'ok', 'reason', 'size': 'a x b x c', 'tris': int}] -> one sheet png."""
    rows = (len(entries) + cols - 1) // cols
    W, H = cols * res, HEADER_H + rows * (res + LABEL_H)
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((6, 4), title, fill=(220, 220, 220), font=font(13))
    f1, f2 = font(11), font(10)
    for k, e in enumerate(entries):
        r, c = divmod(k, cols)
        x, y = c * res, HEADER_H + r * (res + LABEL_H)
        sheet.paste(tile_image(e['tile'], res, e['ok'], e.get('reason')), (x, y))
        d.text((x + 3, y + res + 2), fit(e['name'], d, f1, res - 6), fill=(235, 235, 235), font=f1)
        d.text((x + 3, y + res + 15), '%s in   %s tris' % (e['size'], e.get('tris') if e.get('tris') is not None else '?'),
               fill=(170, 200, 170), font=f2)
        d.text((x + 3, y + res + 27), fit(e.get('sub', ''), d, f2, res - 6), fill=(150, 150, 170), font=f2)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    sheet.save(out_png)
    return out_png


def run(args):
    cat = C.load_catalog()
    zones = args.zones.split(',') if args.zones else None
    groups = args.groups.split(',') if args.groups else None
    rows = C.library_models(cat, zones, groups)
    if args.limit:
        rows = rows[:args.limit]
    out = args.out or C.library_root()
    prep = os.path.join(out, 'prep')
    tiles = os.path.join(out, 'tiles')
    os.makedirs(tiles, exist_ok=True)
    items = [{'name': m['name'], 'prep': os.path.join(prep, C.safe(m['name'])),
              'out': os.path.join(tiles, C.safe(m['name']) + '.png')} for m in rows
             if os.path.isfile(os.path.join(prep, C.safe(m['name']) + '.json'))]
    t0 = time.time()
    res = render_tiles(items, args.res, args.engine, args.workers, os.path.join(out, 'tilejobs'))
    t1 = time.time()
    by = {}
    for m in rows:
        by.setdefault((m['group'], C.home_zone(m)), []).append(m)
    index, failures = {}, []
    for (g, z), ms in sorted(by.items()):
        ms.sort(key=lambda m: (m['subcategory'], m['name']))
        for n in range(0, len(ms), PER_SHEET):
            part = ms[n:n + PER_SHEET]
            ents = []
            for m in part:
                r = res.get(m['name'], {'ok': False, 'reason': 'not prepared (no prep file)'})
                if not r['ok'] or r.get('unresolvedSurfaces'):
                    failures.append({'name': m['name'], 'zone': z, 'group': g, 'reason': r.get('reason'), 'loaded': r['ok']})
                ents.append({'name': m['name'], 'tile': os.path.join(tiles, C.safe(m['name']) + '.png'), 'ok': r['ok'],
                             'reason': r.get('reason'), 'size': C.size_text(m), 'tris': m.get('lod0Tris'),
                             'sub': '%s / %s' % (m['subcategory'], ','.join(m['zones']))})
            rel = '%s/%s_%d.png' % (g, z, n // PER_SHEET + 1)
            compose(ents, os.path.join(out, 'sheets', rel), '%s / %s  sheet %d  (%d models)' % (g, z, n // PER_SHEET + 1, len(part)), args.res)
            index[rel] = [{'name': m['name'], 'row': k // COLS, 'col': k % COLS, 'size': m['size'], 'tris': m.get('lod0Tris'),
                           'subcategory': m['subcategory']} for k, m in enumerate(part)]
    json.dump({'schema': 'iwz.library-sheets/1', 'tile': args.res, 'cols': COLS, 'rows': ROWS, 'sheets': index},
              open(os.path.join(out, 'sheets', 'index.json'), 'w'), indent=1)
    json.dump(failures, open(os.path.join(out, 'sheets', 'failures.json'), 'w'), indent=1)
    t2 = time.time()
    print('sheets: %d models, %d sheets, %d with a failure or unresolved surface; tiles %.0f s (%d workers), compose %.0f s' % (
        len(rows), len(index), len(failures), t1 - t0, args.workers, t2 - t1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--zones')
    ap.add_argument('--groups')
    ap.add_argument('--res', type=int, default=256)
    ap.add_argument('--engine', default='EEVEE', choices=['EEVEE', 'WORKBENCH'])
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--out')
    run(ap.parse_args())
