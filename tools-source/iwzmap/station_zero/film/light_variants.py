r"""light_variants: variant documents of the Arcade for the lighting experiments (worker L1, 28 Nov 2026; LIGHTING-GAP E1, W2).

    python light_variants.py <folder> [--floor w/<material>] [--pools baked|runtime|bounce] [--lit "key=v;key=v"]

--floor   the hall floor's material instead of the shell's (E1 A: w/concrete_floor_polished_01_ssr, the stock _sref0 floor, its own pictures)
--pools   the four shop pool spots (`light_pool_<shop>`): as built, pure runtime (always-on engine light, not baked: E1 B) or bounce
--pool-k  a factor on those spots' intensity (with --pools runtime|bounce; E1 B brackets 0.3, 1, 3)
--lit     key=value pairs set over the `--lit` vision of the recipe (W2 sweep); the dark vision is not touched
The builder is arcade_doc.build: nothing of the shell's files changes; the overrides are applied around it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade_doc  # noqa: E402
import arcade_shell as SHELL  # noqa: E402


def set_lit(folder, pairs):
    p = os.path.join(folder, 'map.json')
    d = json.load(open(p, encoding='utf-8'))
    args = d['settings']['build']['darkness']['args']
    i = args.index('--lit') + 1
    kv = dict(x.split('=', 1) for x in args[i].split(';') if x)
    for x in pairs.split(';'):
        if x:
            k, v = x.split('=', 1)
            kv[k.strip()] = v.strip()
    args[i] = ';'.join('%s=%s' % (k, v) for k, v in kv.items())
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=1)
    return args[i]


def main(argv):
    folder = argv[0]
    opt = dict(zip(argv[1::2], argv[2::2]))
    if '--floor' in opt:
        SHELL.MAT['floor'] = opt['--floor']
    pools = opt.get('--pools', 'baked')
    if pools != 'baked':
        lamp0 = SHELL.lamp

        pk = float(opt.get('--pool-k', '1'))

        def lamp(m, id, origin, role, **kw):
            if id.startswith('light_pool_'):
                kw['intensity'] = kw.get('intensity', 1.0) * pk
                kw.update(runtime=True, bake=False) if pools == 'runtime' else kw.update(runtime=True, bake='bounce')
            return lamp0(m, id, origin, role, **kw)
        SHELL.lamp = lamp
    m, done, missing = arcade_doc.build()
    m.save(folder)
    out = {'folder': folder, 'floor': SHELL.MAT['floor'], 'pools': pools, 'goods': done, 'no_module_yet': missing}
    if '--lit' in opt:
        out['lit'] = set_lit(folder, opt['--lit'])
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
