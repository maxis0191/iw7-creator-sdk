r"""goods_score_b: QUALITY-BAR rules 5, 6 and 7 for the goods of Copy Stop and Hole Number Nine, read from the document's layers (no game).

    python goods_score_b.py [doc folder] [--json out.json]

Definitions (stated, because most goods are authored, not stock props):
- an ITEM is one thing a player would name: the objects whose id is `<shop>__<kind>__<nn>[__part]` (goods_kit_b) are grouped by
  `<shop>__<kind>__<nn>`. Items made only of clip boxes, materials and cameras are not items. Its MODEL is the stock model of a prop item,
  else `authored:<kind>`.
- behind the glass: every item of the two shops stands inside its unit (north of the front glass y 4306), so all items count.
- rule 5, trade share: items whose kind is in TRADE[shop] / all items. Signs and cards count in the denominator, never as trade.
  Also given: the same share over stock props only (the stock definition of QUALITY-BAR part A).
- rule 6, filler: a stock model whose name holds box, crate, pallet, trash, carton or debris, and the authored kinds named so (none);
  the shop's most copied model and its share. The bakery's own pink boxes are its trade goods, not filler: said separately.
- rule 7, distinct models per 100 items, shelf goods excepted (SHELF: the units sold or stocked in quantity: rings, reams, jobs, rolls).
"""
import collections
import json
import os
import sys

DOC = r'C:\studio-data\sz\film\arcade\goods_b\doc'
SHOPS = ('copy_stop', 'hole_nine')
TRADE = {
    'copy_stop': {'drawing_tube', 'blueprint_roll', 'light_table', 'ream', 'copies_stack', 'sample_book', 'sample_board', 'blueprint_machine',
                  'blueprint_print', 'copies_out', 'original_on_glass', 'opened_ream', 'toner_drum', 'guillotine', 'cut_sheets', 'spiral_binder',
                  'programmes', 'job_tray', 'job', 'stamp_tree', 'stapler', 'laminator', 'job_envelope', 'forty_copy_job', 'booth_sample_strip',
                  'strip_face_down', 'tube_rack', 'stock_shelf'},
    'hole_nine': {'cake_stand', 'napkin_dispenser', 'sugar_pourer', 'strand_order', 'cup_stack', 'saucer_stack', 'cup', 'gala_tray',
                  'gala_tray_rings', 'ring_tray', 'ring_choc', 'coffee_urn', 'coffee_pot', 'plate', 'ring_on_plate', 'boxes_flat', 'box_made_up',
                  'rack_tray', 'glass_rack', 'rail_rack'},
}
SIGNS = {'window_card', 'hanging_card', 'price_board', 'notice', 'booth_lettering', 'menu_board', 'today_board', 'tv_picture', 'gala_label'}
SHELF = {'ring_choc', 'ream', 'job_envelope', 'job', 'blueprint_roll', 'drawing_tube', 'programmes', 'ring_tray', 'rack_tray', 'box_made_up'}
FILLER_WORDS = ('box', 'crate', 'pallet', 'trash', 'carton', 'debris')


def load(folder):
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import Map
    return [dict(o) for o in Map.load(folder).objects()]


def items_of(objs, shop):
    groups = collections.OrderedDict()
    for o in objs:
        oid = str(o.get('id', ''))
        if not oid.startswith(shop + '__'):
            continue
        parts = oid.split('__')
        if len(parts) < 3 or parts[1] in ('mat', 'cam'):
            continue
        key = '__'.join(parts[:2] + [parts[2].split('_')[0]])        # a fixture's light ids end in _l1
        groups.setdefault(key, []).append(o)
    out = []
    for key, objs_ in groups.items():
        real = [o for o in objs_ if o['kind'] not in ('material', 'camera') and not (o['kind'] == 'box' and o.get('mode') == 'clip')]
        if not real:
            continue
        kind = key.split('__')[1]
        props = [o for o in real if o['kind'] == 'prop']
        model = props[0]['model'] if (len(real) == 1 and props) else 'authored:' + kind
        lights = [o for o in real if o['kind'] == 'light']
        out.append({'id': key, 'kind': kind, 'model': model, 'parts': len(real), 'stock': bool(props) and len(real) - len(lights) == 1})
    return out


def score(folder):
    objs = load(folder)
    table = {}
    for shop in SHOPS:
        its = items_of(objs, shop)
        n = len(its)
        trade = [i for i in its if i['kind'] in TRADE[shop]]
        signs = [i for i in its if i['kind'] in SIGNS]
        stock = [i for i in its if i['stock']]
        stock_trade = [i for i in stock if i['kind'] in TRADE[shop]]
        models = collections.Counter(i['model'] for i in its)
        top_model, top_n = models.most_common(1)[0]
        filler = [i for i in its if any(w in i['model'].lower() for w in FILLER_WORDS) and not i['model'].startswith('authored:')]
        nonshelf = [i for i in its if i['kind'] not in SHELF]
        ns_models = {i['model'] for i in nonshelf}
        table[shop] = {
            'items': n, 'stock_props': len(stock), 'authored_items': n - len(stock), 'signs_cards': len(signs),
            'distinct_models': len(models), 'kinds': len({i['kind'] for i in its}),
            'rule5_trade_share': round(100.0 * len(trade) / n, 1),
            'rule5_trade_share_stock_props_only': round(100.0 * len(stock_trade) / max(1, len(stock)), 1),
            'rule6_most_copied': '%s x%d (%.1f %%)' % (top_model, top_n, 100.0 * top_n / n),
            'rule6_filler_stock_models': len(filler),
            'rule6_pass': len(filler) == 0 or (100.0 * len(filler) / n < 8.8 and not any(w in top_model for w in FILLER_WORDS)),
            'rule7_distinct_per_100_all': round(100.0 * len(models) / n, 1),
            'rule7_distinct_per_100_shelf_excepted': round(100.0 * len(ns_models) / max(1, len(nonshelf)), 1),
            'rule7_nonshelf_items': len(nonshelf),
            'stock_models': sorted({i['model'] for i in stock}),
            'kinds_list': dict(collections.Counter(i['kind'] for i in its)),
        }
        t = table[shop]
        t['rule5_pass'] = t['rule5_trade_share'] >= 45.0
        t['rule7_pass'] = t['rule7_distinct_per_100_shelf_excepted'] >= 19.0
    return table


def main():
    argv = sys.argv[1:]
    out = None
    if '--json' in argv:
        i = argv.index('--json')
        out = argv[i + 1]
        del argv[i:i + 2]
    t = score(argv[0] if argv else DOC)
    print('| shop | items (stock / authored) | rule 5 trade share (stock only) | rule 6 most copied; filler stock models | rule 7 distinct per 100, shelf goods excepted (all) |')
    print('|---|---|---|---|---|')
    for s, r in t.items():
        print('| %s | %d (%d / %d) | %.1f %% %s (%.1f %%) | %s; %d %s | %.1f %s (%.1f) |' % (
            s, r['items'], r['stock_props'], r['authored_items'], r['rule5_trade_share'], 'pass' if r['rule5_pass'] else 'FAIL',
            r['rule5_trade_share_stock_props_only'], r['rule6_most_copied'], r['rule6_filler_stock_models'], 'pass' if r['rule6_pass'] else 'FAIL',
            r['rule7_distinct_per_100_shelf_excepted'], 'pass' if r['rule7_pass'] else 'FAIL', r['rule7_distinct_per_100_all']))
    if out:
        json.dump(t, open(out, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
