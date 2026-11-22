"""Pick models from the library for a script or a section author.

  python -B pick.py query [--group retail] [--sub shelf] [--size-max 96] [--size-min 8] [--zone cp_disco] [--text shelf]
                          [--tris-max 3000] [--resolving] [--limit 50] [--json]
  python -B pick.py show <model> [<model> ...] [--res 512] [--out picks.png]

`query` filters the catalogue (size-max / size-min compare the largest bounds side in inches) and prints the model, group,
subcategory, size, LOD0 triangles, zones, cp_zmb placements and its contact sheet tile (sheet file, row, column) from
<library>/sheets/index.json. `show` prepares the chosen models (prep.py) and renders them larger into one PNG.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def sheet_positions(root):
    p = os.path.join(root, 'sheets', 'index.json')
    pos = {}
    if os.path.isfile(p):
        for sheet, ms in json.load(open(p))['sheets'].items():
            for m in ms:
                pos[m['name']] = (sheet, m['row'], m['col'])
    return pos


def select(models, group=None, sub=None, size_max=None, size_min=None, zone=None, text=None, tris_max=None,
           resolving=False, include_excluded=False):
    """Pure filter over catalogue rows."""
    rx = re.compile(text, re.I) if text else None
    out = []
    for m in models:
        if not include_excluded and m['group'] in C.EXCLUDED_GROUPS:
            continue
        if group and m['group'] != group:
            continue
        if sub and m['subcategory'] != sub:
            continue
        side = max(m['size'])
        if size_max is not None and side > size_max:
            continue
        if size_min is not None and side < size_min:
            continue
        if zone and zone not in m['zones']:
            continue
        if rx and not rx.search(m['name']):
            continue
        if tris_max is not None and (m.get('lod0Tris') or 0) > tris_max:
            continue
        if resolving and not m['resolves']:
            continue
        out.append(m)
    return out


def cmd_query(a):
    cat = C.load_catalog()
    rows = select(cat['models'], a.group, a.sub, a.size_max, a.size_min, a.zone, a.text, a.tris_max, a.resolving, a.all)
    pos = sheet_positions(C.library_root())
    out = []
    for m in rows[:a.limit]:
        sp = pos.get(m['name'])
        out.append({'name': m['name'], 'group': m['group'], 'subcategory': m['subcategory'], 'size': m['size'],
                    'bounds': m['bounds'], 'tris': m.get('lod0Tris'), 'zones': m['zones'], 'resolves': m['resolves'],
                    'cp_zmb_placements': m.get('placements', {}).get('cp_zmb'),
                    'sheet': {'file': sp[0], 'row': sp[1], 'col': sp[2]} if sp else None})
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        for o in out:
            print('%-52s %-12s %-10s %-22s tris=%-6s %-18s %s' % (
                o['name'], o['group'], o['subcategory'], ' x '.join('%d' % round(v) for v in o['size']), o['tris'],
                ','.join(o['zones'][:3]), ('%s r%d c%d' % (o['sheet']['file'], o['sheet']['row'], o['sheet']['col'])) if o['sheet'] else '-'))
    print('%d match, %d shown' % (len(rows), len(out)), file=sys.stderr)


def cmd_show(a):
    import prep
    import sheets
    cat = {m['name']: m for m in C.load_catalog()['models']}
    bad = [n for n in a.models if n not in cat]
    if bad:
        sys.exit('not in the catalogue: ' + ', '.join(bad))
    root = C.library_root()
    work = os.path.join(root, 'pick')
    os.makedirs(work, exist_ok=True)
    index = C.dump_index()
    infos = [prep.prep_model(n, work, index) for n in a.models]
    imgs, _ = prep.decode_images(infos, index, C.A.game_root(), 4)
    prep.finish(infos, imgs, work)
    items = [{'name': n, 'prep': os.path.join(work, C.safe(n)), 'out': os.path.join(work, C.safe(n) + '.png')} for n in a.models]
    res = sheets.render_tiles(items, a.res, 'EEVEE', 1, os.path.join(work, 'jobs'))
    ents = [{'name': n, 'tile': i['out'], 'ok': res.get(n, {}).get('ok', False), 'reason': res.get(n, {}).get('reason'),
             'size': C.size_text(cat[n]), 'tris': cat[n].get('lod0Tris'), 'sub': '%s / %s' % (cat[n]['subcategory'], ','.join(cat[n]['zones']))}
            for n, i in zip(a.models, items)]
    out = a.out or os.path.join(work, 'picks.png')
    sheets.compose(ents, out, 'picked models', a.res, cols=min(4, len(ents)))
    print(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('query')
    q.add_argument('--group')
    q.add_argument('--category', dest='group', help='alias of --group')
    q.add_argument('--sub')
    q.add_argument('--size-max', type=float)
    q.add_argument('--size-min', type=float)
    q.add_argument('--zone')
    q.add_argument('--text')
    q.add_argument('--tris-max', type=int)
    q.add_argument('--resolving', action='store_true')
    q.add_argument('--all', action='store_true', help='include weapon, character, vfx and attachment models')
    q.add_argument('--limit', type=int, default=50)
    q.add_argument('--json', action='store_true')
    s = sp.add_parser('show')
    s.add_argument('models', nargs='+')
    s.add_argument('--res', type=int, default=512)
    s.add_argument('--out')
    a = ap.parse_args(argv)
    {'query': cmd_query, 'show': cmd_show}[a.cmd](a)


if __name__ == '__main__':
    main()
