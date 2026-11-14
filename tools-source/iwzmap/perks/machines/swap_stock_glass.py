"""Point the perk machines' glass at the stock clear model glass, after t7_env_port.py.

    python -B swap_stock_glass.py <port dir> [--env-model <x64-zt-extensions>/tools-source/asset-bridge/env-model]

The machines author their glass as iwz_pk_zz_glass. The port bakes it on its own glass template, which glowed lavender in
g27. This step rewrites every model in <port>/xmodel so that the surface uses mo/glass_clear_model_no_imp instead. That
is the stock clear glass of cp_zmb (stock p7_cup_glass_tumbler uses it). The Station Zero zone csv already carries it
as a reference row (`material,,mo/glass_clear_model_no_imp`), so the kit import shares it and copies nothing. The
stand-in's material file, techset state files and the images that only it uses are deleted. A copy of the stock
material's definition is put in their place (<port>/materials/mo/glass_clear_model_no_imp.json, from the template
dump): kit_import.py only recognises a model's material through that file, then finds the zone csv's reference row
and shares it instead of copying it. Writes
<port>/glass_swap.json and exits 1 when nothing was swapped.
"""
import argparse
import glob
import json
import os
import sys

SRC = 'mo/t7e_iwz_pk_zz_glass'
STOCK = 'mo/glass_clear_model_no_imp'
DEFAULT_ENV = os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Products', 'x64-zt-extensions', 'tools-source',
                           'asset-bridge', 'env-model')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('port')
    ap.add_argument('--env-model', default=DEFAULT_ENV)
    ap.add_argument('--template-materials', default=os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime',
                    'iwz-map-ref-a', 'dump', 'techsets_cp_zmb', 'materials'),
                    help='materials/ of the template dump that defines the stock glass')
    a = ap.parse_args(argv)
    sys.path.insert(0, a.env_model)
    import iw7_xmodel_io as io
    rep = {'swapped': {}, 'deleted': []}
    for f in sorted(glob.glob(os.path.join(a.port, 'xmodel', '*.xmb'))):
        data = open(f, 'rb').read()
        m = io.parse_xmodel(data)
        n = sum(1 for x in m['materials'] if x == SRC)
        if not n:
            continue
        m['materials'] = [STOCK if x == SRC else x for x in m['materials']]
        out = io.write_xmodel(m)
        if io.parse_xmodel(out)['materials'] != m['materials']:
            raise SystemExit('%s: read-back after the swap differs' % f)
        open(f, 'wb').write(out)
        rep['swapped'][os.path.basename(f)] = n
    stem = SRC.replace('/', '_')
    mat = os.path.join(a.port, 'materials', SRC + '.json')
    used_elsewhere = set()
    for mj in glob.glob(os.path.join(a.port, 'materials', '**', '*.json'), recursive=True):
        if os.path.normpath(mj) == os.path.normpath(mat):
            continue
        for t in json.load(open(mj)).get('textureTable', []):
            used_elsewhere.add(t['image'])
    own = []
    if os.path.exists(mat):
        own = [t['image'] for t in json.load(open(mat)).get('textureTable', [])]
        os.remove(mat)
        rep['deleted'].append(mat)
    for img in own:
        p = os.path.join(a.port, 'images', img + '.dds')
        if img not in used_elsewhere and os.path.exists(p):
            os.remove(p)
            rep['deleted'].append(p)
    state = set(glob.glob(os.path.join(a.port, 'techsets', '**', 't7e_iwz_pk_zz_glass.*'), recursive=True))
    for p in sorted(state):
        os.remove(p)
        rep['deleted'].append(p)
    src = os.path.join(a.template_materials, STOCK + '.json')
    if not os.path.exists(src):
        raise SystemExit('stock material definition not found: %s' % src)
    dst = os.path.join(a.port, 'materials', STOCK + '.json')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(open(src, 'rb').read())
    rep['stock_definition'] = dst
    rep['stock'] = STOCK
    json.dump(rep, open(os.path.join(a.port, 'glass_swap.json'), 'w'), indent=1)
    print('glass swap:', rep['swapped'], '; deleted', len(rep['deleted']), 'files')
    return 0 if rep['swapped'] else 1


if __name__ == '__main__':
    sys.exit(main())
