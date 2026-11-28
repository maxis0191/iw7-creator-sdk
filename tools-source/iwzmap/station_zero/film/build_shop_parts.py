r"""build_shop_parts: shop_parts.json from the `store show` sheets' json of the AC2 fit run (bounds in the model frame, the back and the yaws that put it to a wall).

    python build_shop_parts.py [fit folder]   (default C:\studio-data\sz\film\station\ac2\fit)
Keys as parts_final.json (mins, maxs, size, tris, back, front, against_wall, zones, materials).
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(fit=r'C:\studio-data\sz\film\station\ac2\fit'):
    out = {}
    for f in sorted(glob.glob(os.path.join(fit, '*.v1.json'))):
        d = json.load(open(f, encoding='utf-8'))
        if not d.get('ok'):
            continue
        sd = d.get('sides') or {}
        out[d['model']] = {'size': d['size'], 'mins': d['bounds']['mins'], 'maxs': d['bounds']['maxs'], 'tris': d['tris'], 'back': d.get('back'), 'front': d.get('front'),
                           'against_wall': d.get('against_wall'), 'kind': sd.get('kind'), 'zones': d.get('zones'), 'materials': d.get('materials')}
    json.dump(out, open(os.path.join(HERE, 'shop_parts.json'), 'w', encoding='utf-8'), indent=0)
    print(len(out), 'models')


if __name__ == '__main__':
    main(*sys.argv[1:])
