"""Counts of the catalogue: models per zone and group (the table of docs/ASSET-LIBRARY.md).

  python -B report.py [--catalog catalog.json] [--md] [--json out.json]

A model counts under every zone it ships in ("in zone") and once under its home zone (first of its zones in build order,
where its sheets are filed). `lod0` = has LOD0 triangles, `resolves` = every texture of its materials has a file in a dump
(engine placeholder images aside). Excluded groups (weapon, character, vfx, attachment) are counted but get no sheets.
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def counts(models):
    zones = sorted({z for m in models for z in m['zones']})
    groups = sorted({m['group'] for m in models})
    inzone = collections.defaultdict(lambda: collections.Counter())
    home = collections.defaultdict(lambda: collections.Counter())
    for m in models:
        for z in m['zones']:
            inzone[z][m['group']] += 1
            inzone[z]['_models'] += 1
            inzone[z]['_lod0'] += bool(m.get('lod0Tris'))
            inzone[z]['_resolves'] += bool(m['resolves'])
        home[C.home_zone(m)][m['group']] += 1
    return zones, groups, inzone, home


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--catalog')
    ap.add_argument('--md', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    models = C.load_catalog(a.catalog)['models']
    zones, groups, inzone, home = counts(models)
    lib = [m for m in models if m['group'] not in C.EXCLUDED_GROUPS]
    out = {'models': len(models), 'library_models': len(lib), 'library_resolving': sum(m['resolves'] for m in lib),
           'in_zone': {z: dict(inzone[z]) for z in zones}, 'home_zone': {z: dict(home[z]) for z in zones}}
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1)
    head = ['zone', 'models', 'LOD0', 'resolves'] + groups
    if a.md:
        print('| ' + ' | '.join(head) + ' |')
        print('|' + '---|' * len(head))
    else:
        print('\t'.join(head))
    for z in zones:
        c = inzone[z]
        row = [z, c['_models'], c['_lod0'], c['_resolves']] + [c[g] for g in groups]
        print(('| ' + ' | '.join(str(x) for x in row) + ' |') if a.md else '\t'.join(str(x) for x in row))
    print('%d models, %d in the library (not weapon / character / vfx / attachment), %d of those resolve' % (
        len(models), len(lib), out['library_resolving']))


if __name__ == '__main__':
    main()
