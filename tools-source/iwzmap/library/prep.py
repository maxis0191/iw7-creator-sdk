"""Stage 1 of the contact sheets and the .blend libraries: models -> numpy files + decoded PNG textures (no Blender).

  python -B prep.py [--catalog catalog.json] [--zones cp_zmb,...] [--groups ...] [--limit N] [--threads 8] [--out DIR]

Per model one `<out>/<safe name>.npz` holds LOD0 as one array set (pos, uv, tris, surface ids) and a `.json` holds the
materials of its surfaces: colour image path (decoded PNG in the preview cache), tint, techset, alpha mode, and the
reason string of everything that did not resolve. Nothing is faked: a model that cannot load has a `.json` with
`error` and is drawn as a magenta tile by the sheets. Images are decoded once (preview cache) by a thread pool.
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
A = C.A

ALPHA_TECHSET = ('atest', 'blend', 'alpha', 'trans')


def prep_model(name, outdir, index):
    base = os.path.join(outdir, C.safe(name))
    info = {'name': name, 'surfaces': [], 'error': None}
    mod, why = A.read_model(index, name)
    if mod is None:
        info['error'] = why
        json.dump(info, open(base + '.json', 'w'))
        return info
    pos, uv, tris, sid = [], [], [], []
    off = 0
    mats = {}
    for s in mod['surfs']:
        n = len(s['pos'])
        if not n or not len(s['tris']):
            continue
        pos.append(s['pos'])
        uv.append(s['uv'])
        tris.append(s['tris'] + off)
        sid.append(np.full(len(s['tris']), len(info['surfaces']), np.int32))
        off += n
        mname = s['material']
        if mname not in mats:
            mi, mwhy = A.material_info(index, mname) if mname else (None, 'surface without a material name')
            rec = {'material': mname, 'image': None, 'png': None, 'tint': [1, 1, 1, 1], 'techset': None, 'alpha': False,
                   'reason': None}
            if mi is None:
                rec['reason'] = mwhy
            else:
                rec['techset'] = mi['techset']
                rec['tint'] = mi['tint']
                rec['how'] = mi['how']
                rec['alpha'] = any(k in (mi['techset'] or '') for k in ALPHA_TECHSET)
                rec['image'] = mi['image']
                if mi['image']:
                    rec['pending'] = True
                else:
                    rec['reason'] = 'material has no colour image'
            mats[mname] = rec
        info['surfaces'].append(mname)
    info['materials'] = mats
    if not pos:
        info['error'] = 'no triangles in LOD0'
        json.dump(info, open(base + '.json', 'w'))
        return info
    np.savez(base + '.npz', pos=np.concatenate(pos).astype(np.float32), uv=np.concatenate(uv).astype(np.float32),
             tris=np.concatenate(tris).astype(np.int32), sid=np.concatenate(sid), bmin=np.array(mod['bounds'][0], np.float32),
             bmax=np.array(mod['bounds'][1], np.float32))
    return info


def decode_images(infos, index, game, threads):
    """Decode every distinct colour image once (texconv is a subprocess: threads)."""
    names = sorted({m['image'] for i in infos for m in i.get('materials', {}).values() if m.get('pending')})
    res = {}

    def one(n):
        return n, A.image_png(index, n, game)

    t = time.time()
    with cf.ThreadPoolExecutor(threads) as ex:
        for n, (png, why) in ex.map(one, names):
            res[n] = (png, why)
    return res, round(time.time() - t, 1)


def finish(infos, imgs, outdir):
    """Write the decoded PNG paths into the per model json files."""
    for i in infos:
        for m in i.get('materials', {}).values():
            if m.pop('pending', None):
                png, why = imgs[m['image']]
                m['png'], m['reason'] = png, why
        json.dump(i, open(os.path.join(outdir, C.safe(i['name']) + '.json'), 'w'))


def run(args):
    cat = C.load_catalog(args.catalog)
    zones = args.zones.split(',') if args.zones else None
    groups = args.groups.split(',') if args.groups else None
    rows = C.library_models(cat, zones, groups, only_resolving=False)
    if args.names:
        want = set(open(args.names).read().split())
        rows = [r for r in rows if r['name'] in want]
    if args.limit:
        rows = rows[:args.limit]
    out = args.out or os.path.join(C.library_root(), 'prep')
    os.makedirs(out, exist_ok=True)
    index = C.dump_index()
    game = A.game_root()
    t0 = time.time()
    with cf.ThreadPoolExecutor(args.threads) as ex:
        infos = list(ex.map(lambda r: prep_model(r['name'], out, index), rows))
    t1 = time.time()
    imgs, dt = decode_images(infos, index, game, args.threads)
    finish(infos, imgs, out)
    errs = [i for i in infos if i.get('error')]
    print('prep: %d models (%d failed to load), %d images decoded (%d failed); models %.1f s, images %.1f s' % (
        len(infos), len(errs), len(imgs), sum(1 for p, w in imgs.values() if not p), t1 - t0, dt))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--catalog')
    ap.add_argument('--zones')
    ap.add_argument('--groups')
    ap.add_argument('--names', help='file of model names')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--out')
    run(ap.parse_args())
