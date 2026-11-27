r"""arcade_doc: the Underpass Arcade's document = the shell (arcade_shell.py) + the goods of each shop (goods_<shop>.py).

    set STUDIO_ROOT=C:\studio
    python arcade_doc.py <folder> [--only needle_drop,heel_key]

A goods module is `goods_<shop>.py` beside this file with one function `add(m, anchors)`: `m` is the Studio Map the shell has
already filled, `anchors` a dict name -> anchor (box, facing, for) as the shell declares them. It adds ONE layer named
`goods_<shop>` and puts every object of the shop's goods in it, ids prefixed `<shop>_`. It changes nothing of the shell's layers.
Shops: needle_drop, copy_stop, hole_nine, heel_key. A module that does not exist yet is skipped and named in the printed report.
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade_shell as SHELL  # noqa: E402
from studio import fixtures as FX  # noqa: E402

SHOPS = ('needle_drop', 'copy_stop', 'hole_nine', 'heel_key')


def build(only=None, name='sz_arcade'):
    m = SHELL.build(name)
    anchors = {a['name']: a for a in SHELL.ANCHORS}
    done, missing = [], []
    for shop in SHOPS:
        if only and shop not in only:
            continue
        if not os.path.isfile(os.path.join(HERE, 'goods_%s.py' % shop)):
            missing.append(shop)
            continue
        mod = importlib.import_module('goods_%s' % shop)
        m.add_layer('goods_%s' % shop)
        mod.add(m, anchors)
        done.append(shop)
    FX.use_kit(m)                                                  # the kit list again: the goods' models
    return m, done, missing


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    only = None
    if '--only' in argv:
        i = argv.index('--only')
        only = [s for s in argv[i + 1].split(',') if s]
        del argv[i:i + 2]
    folder = argv[0]
    m, done, missing = build(only)
    m.save(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'goods': done, 'no_module_yet': missing}, indent=1, default=str))


if __name__ == '__main__':
    main()
