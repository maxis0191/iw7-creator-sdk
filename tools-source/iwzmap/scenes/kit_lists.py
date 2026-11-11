"""Station Zero kit lists (package TF7).

Reads the hand-written selection (station_zero_kit_select.json: per zone, the stock models, ported models,
effects and materials chosen for its look, plus the gaps) and checks every name against the machine's data:

  * the model catalogue built by catalog/iwzcat.py (rows: name, zones, category, size, materials ...);
    a model counts as "stock" when it ships in one of the five zombies maps (cp_zmb, cp_disco, cp_town,
    cp_final, cp_rave); when dump folders are known the xmodel file must exist in one of them as well;
  * the static models of the template map (stock-smodels.csv, column "model"): has_template_donor;
  * the scene database of Spaceland (cp_zmb.sqlite, table models): uses in the shipped map;
  * the zone csv files of the dumps (lines "vfx,<name>") for effects, and the catalogue's material lists.

It writes station_zero_kits.json and docs/STATION-ZERO-KITS.md and prints totals. Exit code 1 when a chosen
name is not found or a size rule is missed (distinct models over the map, models per zone).
Nothing is copied from the game: names and numbers only.

    python -I kit_lists.py --catalog catalog.json --smodels-csv stock-smodels.csv --sqlite cp_zmb.sqlite \
        --fx-csv cp_disco=cp_disco.csv --out-json station_zero_kits.json --out-md ../../../docs/STATION-ZERO-KITS.md
"""
import argparse
import csv
import json
import os
import sqlite3
import sys

STOCK_ZONES = ('cp_zmb', 'cp_disco', 'cp_town', 'cp_final', 'cp_rave')
SHORT = {'cp_zmb': 'zmb', 'cp_disco': 'disco', 'cp_town': 'town', 'cp_final': 'final', 'cp_rave': 'rave'}
SMALL_ZONES = ('staff_stair', 'terminus')
HERE = os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_catalog(path, stock_zones):
    """name -> row, for rows that ship in at least one of the given zones; plus the material set and zone dirs."""
    cat = load_json(path)
    rows = {}
    mats = {}
    for r in cat.get('models', []):
        zs = [z for z in r.get('zones', []) if z in stock_zones]
        if not zs:
            continue
        rows[r['name']] = r
        for m in r.get('materials', []) or []:
            if isinstance(m, dict) and not m.get('missing') and m.get('name'):
                mats.setdefault(m['name'], set()).update(zs)
    dirs = {z['name']: z.get('dirs', []) for z in cat.get('zones', [])}
    return rows, mats, dirs


def load_template_donors(path):
    counts = {}
    with open(path, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            counts[row['model']] = counts.get(row['model'], 0) + 1
    return counts


def load_sqlite_uses(path):
    db = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'), uri=True)
    try:
        return {n: i for n, i in db.execute('select name, instances from models')}
    finally:
        db.close()


def load_fx_names(csv_paths):
    names = {}
    for zone, path in csv_paths.items():
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                kind, _, name = line.strip().partition(',')
                if kind == 'vfx' and name:
                    names.setdefault(name, set()).add(zone)
    return names


def dump_has_model(dirs, zones, name):
    """True when <dir>/xmodel/<name>.xmb exists in a dump of one of the zones; None when no dump is known."""
    known = False
    for z in zones:
        for d in dirs.get(z, []):
            if not os.path.isdir(d):
                continue
            known = True
            if os.path.exists(os.path.join(d, 'xmodel', name + '.xmb')) or os.path.exists(os.path.join(d, name + '.xmb')):
                return True
    return False if known else None


def size_of(row):
    return [int(round(v)) for v in row.get('size', [0, 0, 0])]


def build(select, catalog, ported_catalog, mats, donors, uses, fx_names, dirs, stock_zones):
    problems = []
    out_zones = {}
    verified_by_dump = 0
    for zone, z in select['zones'].items():
        entry = {'models': [], 'ported': [], 'effects': [], 'materials': [], 'gaps': z.get('gaps', [])}
        seen = set()
        for m in z.get('models', []):
            n = m['name']
            if n in seen:
                problems.append('%s: %s listed twice' % (zone, n))
                continue
            seen.add(n)
            row = catalog.get(n)
            if row is None:
                problems.append('%s: model %s is not a stock model of the five zombies maps' % (zone, n))
                continue
            szs = [x for x in row['zones'] if x in stock_zones]
            dump = dump_has_model(dirs, szs, n)
            if dump is False:
                problems.append('%s: model %s has no xmodel file in the dumps of %s' % (zone, n, ','.join(szs)))
                continue
            if dump:
                verified_by_dump += 1
            entry['models'].append({
                'name': n, 'role': m['role'], 'size': size_of(row), 'category': row.get('category', ''),
                'zones': [x for x in stock_zones if x in szs], 'uses_spaceland': (uses or {}).get(n, donors.get(n, 0)),
                'template_donor': n in donors, 'dump_checked': dump is True})
        for m in z.get('ported', []):
            row = (ported_catalog or {}).get(m['name'])
            if row is None:
                problems.append('%s: ported model %s is not in the ported catalogue' % (zone, m['name']))
                continue
            entry['ported'].append({'name': m['name'], 'role': m['role'], 'size': size_of(row), 'zones': sorted(row.get('zones', []))})
        for m in z.get('effects', []):
            if fx_names is None:
                problems.append('%s: effect %s cannot be checked (no --fx-csv given)' % (zone, m['name']))
                continue
            if m['name'] not in fx_names:
                problems.append('%s: effect %s is not in any zone csv' % (zone, m['name']))
                continue
            entry['effects'].append({'name': m['name'], 'role': m['role'], 'zones': [x for x in stock_zones if x in fx_names[m['name']]]})
        for m in z.get('materials', []):
            if m['name'] not in mats:
                problems.append('%s: material %s is not on any stock model of the five maps' % (zone, m['name']))
                continue
            entry['materials'].append({'name': m['name'], 'role': m['role'], 'zones': [x for x in stock_zones if x in mats[m['name']]]})
        out_zones[zone] = entry
    return out_zones, problems, verified_by_dump


def totals(zones):
    all_models = {}
    for z in zones.values():
        for m in z['models']:
            all_models.setdefault(m['name'], m)
    donors = sum(1 for m in all_models.values() if m['template_donor'])
    ported = set(m['name'] for z in zones.values() for m in z['ported'])
    return {
        'distinct_models': len(all_models),
        'template_donor_models': donors,
        'template_donor_share': round(donors / len(all_models), 3) if all_models else 0.0,
        'distinct_ported_models': len(ported),
        'distinct_effects': len(set(m['name'] for z in zones.values() for m in z['effects'])),
        'distinct_materials': len(set(m['name'] for z in zones.values() for m in z['materials'])),
        'gaps': sum(len(z['gaps']) for z in zones.values()),
        'per_zone': {k: len(v['models']) for k, v in zones.items()},
    }


def check_rules(zones, tot, min_total, min_zone, min_small):
    problems = []
    if tot['distinct_models'] < min_total:
        problems.append('only %d distinct models over the map (need %d)' % (tot['distinct_models'], min_total))
    for k, v in zones.items():
        need = min_small if k in SMALL_ZONES else min_zone
        if len(v['models']) < need:
            problems.append('zone %s has %d models (need %d)' % (k, len(v['models']), need))
    return problems


def fmt_size(s):
    return '%dx%dx%d' % tuple(s)


def render_md(zones, tot, stock_zones):
    L = []
    w = L.append
    w('# Station Zero kit lists')
    w('')
    w('Package TF7 of the Station Zero build plan: for each of the 19 zones, the stock models, materials and effects')
    w('of the five shipped zombies maps (%s) that fit its look, with sizes and where the shipped maps use them,' % ', '.join(SHORT[z] for z in stock_zones if z in SHORT))
    w('and the objects no stock model fits (GAPS, models to author). Generated by `tools-source/iwzmap/scenes/kit_lists.py`')
    w('from the hand-written `station_zero_kit_select.json`; the data is `station_zero_kits.json`.')
    w('')
    w('Regenerate: `python -I tools-source/iwzmap/scenes/kit_lists.py --catalog <catalog.json> --ported-catalog <catalog_bo3_converted.json> --smodels-csv <stock-smodels.csv> --sqlite <cp_zmb.sqlite> --fx-csv <zone>=<zone csv> ... --out-md docs/STATION-ZERO-KITS.md`; it exits 1 when a name is missing.')
    w('')
    w('Nothing here is placed or seen in the game: a name in a table means it exists in a dump and was chosen by')
    w('its name, category and size, not that it looks right in the station. Sizes are the model bounds in game units')
    w('(x by y by z, catalogue bounds). "Uses in Spaceland" is the number of static instances in the shipped map')
    w('(cp_zmb). "Donor" is yes when the model appears among the static models compiled in the template map cp_zmb,')
    w('which a generated map can reuse as a static model; a model without a donor counts as an entity until a later')
    w('package proves otherwise. "Zones" lists where the model ships (zmb, disco, town, final, rave).')
    w('')
    w('## Totals')
    w('')
    w('| Item | Count |')
    w('| --- | --- |')
    w('| Distinct stock models over the map | %d |' % tot['distinct_models'])
    w('| of them with a template donor | %d (%.0f %%) |' % (tot['template_donor_models'], 100 * tot['template_donor_share']))
    w('| Distinct ported (converted BO3) models, listed apart | %d |' % tot['distinct_ported_models'])
    w('| Distinct effects | %d |' % tot['distinct_effects'])
    w('| Distinct materials | %d |' % tot['distinct_materials'])
    w('| Gaps (models to author) | %d |' % tot['gaps'])
    w('')
    w('| Zone | Models | with donor | Ported | Effects | Materials | Gaps |')
    w('| --- | --- | --- | --- | --- | --- | --- |')
    for k, v in zones.items():
        d = sum(1 for m in v['models'] if m['template_donor'])
        w('| %s | %d | %d | %d | %d | %d | %d |' % (k, len(v['models']), d, len(v['ported']), len(v['effects']), len(v['materials']), len(v['gaps'])))
    for k, v in zones.items():
        w('')
        w('## %s' % k)
        w('')
        w('| Model | Role | Size | Zones | Uses in Spaceland | Donor |')
        w('| --- | --- | --- | --- | --- | --- |')
        for m in v['models']:
            w('| `%s` | %s | %s | %s | %d | %s |' % (m['name'], m['role'], fmt_size(m['size']),
                                                  ' '.join(SHORT.get(z, z) for z in m['zones']), m['uses_spaceland'],
                                                  'yes' if m['template_donor'] else 'no'))
        if v['ported']:
            w('')
            w('Ported (converted from another game, not stock; each is an entity until proven otherwise):')
            w('')
            w('| Model | Role | Size |')
            w('| --- | --- | --- |')
            for m in v['ported']:
                w('| `%s` | %s | %s |' % (m['name'], m['role'], fmt_size(m['size'])))
        if v['effects']:
            w('')
            w('Effects:')
            w('')
            w('| Effect | Role | Zones |')
            w('| --- | --- | --- |')
            for m in v['effects']:
                w('| `%s` | %s | %s |' % (m['name'], m['role'], ' '.join(SHORT.get(z, z) for z in m['zones'])))
        if v['materials']:
            w('')
            w('Materials:')
            w('')
            w('| Material | Role | Zones |')
            w('| --- | --- | --- |')
            for m in v['materials']:
                w('| `%s` | %s | %s |' % (m['name'], m['role'], ' '.join(SHORT.get(z, z) for z in m['zones'])))
        if v['gaps']:
            w('')
            w('GAPS (models to author):')
            w('')
            w('| Object | Approx. size | Note |')
            w('| --- | --- | --- |')
            for g in v['gaps']:
                w('| %s | %s | %s |' % (g['object'], fmt_size(g['size']), g['note']))
    w('')
    return '\n'.join(L)


def parse_pairs(items):
    out = {}
    for it in items or []:
        k, _, v = it.partition('=')
        out[k] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--select', default=os.path.join(HERE, 'station_zero_kit_select.json'))
    ap.add_argument('--catalog', required=True)
    ap.add_argument('--ported-catalog')
    ap.add_argument('--smodels-csv', required=True)
    ap.add_argument('--sqlite')
    ap.add_argument('--fx-csv', action='append', help='zone=path of a zone csv (lines "vfx,<name>")')
    ap.add_argument('--no-dump-check', action='store_true', help='do not look for xmodel files in the dump folders')
    ap.add_argument('--out-json', default=os.path.join(HERE, 'station_zero_kits.json'))
    ap.add_argument('--out-md')
    ap.add_argument('--min-total', type=int, default=350)
    ap.add_argument('--min-zone', type=int, default=12)
    ap.add_argument('--min-small', type=int, default=6)
    a = ap.parse_args(argv)

    select = load_json(a.select)
    catalog, mats, dirs = load_catalog(a.catalog, STOCK_ZONES)
    if a.no_dump_check:
        dirs = {}
    ported = None
    if a.ported_catalog:
        ported = {r['name']: r for r in load_json(a.ported_catalog).get('models', [])}
    donors = load_template_donors(a.smodels_csv)
    uses = load_sqlite_uses(a.sqlite) if a.sqlite else None
    fx = load_fx_names(parse_pairs(a.fx_csv)) if a.fx_csv else None

    zones, problems, by_dump = build(select, catalog, ported, mats, donors, uses, fx, dirs, STOCK_ZONES)
    tot = totals(zones)
    problems += check_rules(zones, tot, a.min_total, a.min_zone, a.min_small)

    data = {'schema': 'iwz.station-zero-kits/1', 'stock_zones': list(STOCK_ZONES), 'totals': tot, 'zones': zones}
    with open(a.out_json, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1)
        f.write('\n')
    if a.out_md:
        with open(a.out_md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(render_md(zones, tot, STOCK_ZONES))

    print('distinct models over the map: %d (checked against an xmodel file in a dump: %d)' % (tot['distinct_models'], by_dump))
    print('template donor share: %d of %d (%.1f %%)' % (tot['template_donor_models'], tot['distinct_models'], 100 * tot['template_donor_share']))
    print('ported models: %d, effects: %d, materials: %d, gaps: %d' % (tot['distinct_ported_models'], tot['distinct_effects'], tot['distinct_materials'], tot['gaps']))
    for k, n in tot['per_zone'].items():
        print('  %-16s %d' % (k, n))
    for p in problems:
        print('PROBLEM: ' + p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
