"""Machine inventory: IW7 fastfiles of the retained game folder and the ZoneTool dumps on disk.

  python -B inventory.py [--game <folder with *.ff>] [--runtime <IW7-Runtime>] [--json out.json]

Groups every *.ff (cp_*, mp_*, patch_*, techsets_*, common/global, sp/campaign, others) with counts and sizes, then walks
the runtime folder (without entering asset subfolders) for dump folders: a folder `<zone>` holding `<zone>.csv`. Per dump
it counts xmodel / xsurface / images / materials, so "has a dump" can be told apart from "has a dump with models that can
be rendered" (xsurface present). Reads names only; exports nothing.
"""
import argparse
import json
import os
import re
import sys

ASSET_DIRS = {'xmodel', 'xsurface', 'images', 'materials', 'xanim', 'sound', 'techsets', 'scripts', 'weapons', 'lightmaps',
              'maps', 'transient_zones', 'streaming_info', 'xmodelsurfs', '.git', 'node_modules', '__pycache__'}


def group_of(name):
    if name.startswith('patch_'):
        return 'patch'
    if name.startswith('techsets_'):
        return 'techsets'
    if name.startswith('cp_'):
        return 'cp'
    if name.startswith('mp_'):
        return 'mp'
    if name.startswith(('sp_', 'campaign')):
        return 'sp'
    if re.match(r'(common|global)', name):
        return 'common'
    return 'other'


def list_ff(game):
    rows = []
    for f in sorted(os.listdir(game)):
        if f.endswith('.ff'):
            rows.append({'name': f[:-3], 'bytes': os.path.getsize(os.path.join(game, f)), 'group': group_of(f[:-3])})
    return rows


def count(p):
    return sum(len(fs) for _, _, fs in os.walk(p)) if os.path.isdir(p) else 0


def find_dumps(runtime, max_depth=9):
    out = {}
    base_depth = runtime.rstrip('\\/').count(os.sep)
    for root, dirs, files in os.walk(runtime):
        if root.count(os.sep) - base_depth >= max_depth:
            dirs[:] = []
        leaf = os.path.basename(root)
        if leaf + '.csv' in files:
            out.setdefault(leaf, []).append({
                'path': root, 'xmodel': count(os.path.join(root, 'xmodel')), 'xsurface': count(os.path.join(root, 'xsurface')),
                'images': count(os.path.join(root, 'images')), 'materials': count(os.path.join(root, 'materials'))})
        dirs[:] = [d for d in dirs if d not in ASSET_DIRS]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game')
    ap.add_argument('--runtime')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    rt = a.runtime or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')
    game = a.game or os.path.join(rt, 'private-test-server')
    ffs = list_ff(game)
    dumps = find_dumps(rt)
    groups = {}
    for f in ffs:
        g = groups.setdefault(f['group'], {'count': 0, 'bytes': 0, 'dumped': 0, 'renderable': 0})
        g['count'] += 1
        g['bytes'] += f['bytes']
        d = dumps.get(f['name'])
        f['dump'] = bool(d)
        f['renderable_models'] = max([x['xmodel'] for x in d if x['xsurface']] or [0]) if d else 0
        g['dumped'] += bool(d)
        g['renderable'] += f['renderable_models'] > 0
    res = {'game': game, 'fastfiles': ffs, 'groups': groups, 'dumps': dumps}
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
    for g, v in sorted(groups.items()):
        print('%-9s %4d ff  %9.1f MB  dumped %3d  with renderable models %3d' % (g, v['count'], v['bytes'] / 1e6, v['dumped'], v['renderable']))


if __name__ == '__main__':
    main()
