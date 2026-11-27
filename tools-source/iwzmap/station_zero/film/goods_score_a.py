r"""goods_score_a: QUALITY-BAR rules 5, 6 and 7 for the goods of Needle Drop and Heel & Key, from their layers alone (worker A3a).

    python goods_score_a.py [doc folder] [--md]

Two counts, both printed:
  props  stock models only (`kind == prop`), as QUALITY-BAR part A measured the stock shops;
  items  every object a player would name, authored ones included: the objects of one item share the id `<shop>_<cls>__<item>__<n>`
         (goods_kit_a.py); an authored item counts as the model `authored:<item>`. Pictures alone (cards, posters, tags: cls P) are not props.
Rule 5: trade objects (cls T and S) / all props behind the glass, 45 % or more.
Rule 6: filler (cls X, or a model named cardboard box, crate, pallet, carton, trash) under 8.8 % and not the most copied model.
Rule 7: distinct models per 100 props, shelf goods (cls S) left out, 19 or more.
"""
import json
import os
import sys
from collections import Counter

DOC = r'C:\studio-data\sz\film\arcade\goods_a\doc'
SHOPS = ('needle_drop', 'heel_key')
FILLER_WORDS = ('box_cardboard', 'cardboard', 'crate', 'pallet', 'carton', 'trash')      # a VHS box or a toolbox is not filler


def load(folder):
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import Map
    m = Map.load(folder)
    return {shop: [dict(o) for o in m.objects('goods_%s' % shop)] for shop in SHOPS}


def parse(shop, oid):
    rest = oid[len(shop) + 1:]
    parts = rest.split('__')
    return parts[0], parts[1], parts[2]                  # cls, item, n


def rows_of(shop, objs):
    items = {}
    for o in objs:
        cls, item, n = parse(shop, o['id'])
        if o['kind'] in ('light', 'camera'):
            continue
        it = items.setdefault((cls, item, n), {'cls': cls, 'item': item, 'models': set()})
        if o['kind'] == 'prop':
            it['models'].add(o['model'])
    out = []
    for it in items.values():
        if it['cls'] == 'P':
            continue
        model = sorted(it['models'])[0] if it['models'] and len(it['models']) == 1 and it['item'] not in ('key_carousel',) else 'authored:' + it['item']
        stock = bool(it['models']) and not model.startswith('authored:')
        out.append({'cls': it['cls'], 'item': it['item'], 'model': model, 'stock': stock})
    return out


def rules(rows):
    n = len(rows)
    trade = sum(1 for r in rows if r['cls'] in ('T', 'S'))
    filler = [r for r in rows if r['cls'] == 'X' or any(w in r['model'].lower() for w in FILLER_WORDS)]
    cnt = Counter(r['model'] for r in rows)
    top = cnt.most_common(1)[0] if cnt else ('-', 0)
    top_is_filler = any(w in top[0].lower() for w in FILLER_WORDS) or any(r['cls'] == 'X' and r['model'] == top[0] for r in rows)
    nos = [r for r in rows if r['cls'] != 'S']
    distinct = len({r['model'] for r in nos})
    r5 = 100.0 * trade / max(1, n)
    r6 = 100.0 * len(filler) / max(1, n)
    r7 = 100.0 * distinct / max(1, len(nos))
    return {'props': n, 'rule5_trade_pct': round(r5, 1), 'rule5_pass': r5 >= 45.0,
            'rule6_filler_pct': round(r6, 1), 'rule6_most_copied': '%s x%d' % top, 'rule6_pass': r6 < 8.8 and not top_is_filler,
            'rule7_distinct_per_100': round(r7, 1), 'rule7_basis': '%d models / %d props (shelf goods out)' % (distinct, len(nos)), 'rule7_pass': r7 >= 19.0}


def score(folder):
    lay = load(folder)
    out = {}
    for shop, objs in lay.items():
        rows = rows_of(shop, objs)
        out[shop] = {'items': rules(rows), 'props': rules([r for r in rows if r['stock']]),
                     'counts': {'objects': len(objs), 'items': len(rows), 'stock_props': sum(1 for o in objs if o['kind'] == 'prop'),
                                'distinct_stock_models': len({o['model'] for o in objs if o['kind'] == 'prop'}),
                                'pictures': len({o.get('image') for o in objs if o['kind'] in ('decal', 'sign') and o.get('image')}),
                                'by_class': dict(Counter(r['cls'] for r in rows))}}
    return out


def md(res):
    L = ['| Shop | Count | Props | Rule 5 trade % (45+) | Rule 6 filler % (<8.8), most copied | Rule 7 distinct / 100 (19+) |', '|---|---|---|---|---|---|']
    for shop, r in res.items():
        for basis in ('items', 'props'):
            x = r[basis]
            L.append('| %s | %s | %d | %.1f %s | %.1f, %s %s | %.1f (%s) %s |' % (
                shop, basis, x['props'], x['rule5_trade_pct'], 'pass' if x['rule5_pass'] else '**fail**', x['rule6_filler_pct'], x['rule6_most_copied'],
                'pass' if x['rule6_pass'] else '**fail**', x['rule7_distinct_per_100'], x['rule7_basis'], 'pass' if x['rule7_pass'] else '**fail**'))
    return '\n'.join(L)


if __name__ == '__main__':
    a = sys.argv[1:]
    folder = a[0] if a and not a[0].startswith('--') else DOC
    res = score(folder)
    print(md(res) if '--md' in a else json.dumps(res, indent=1, default=str))
