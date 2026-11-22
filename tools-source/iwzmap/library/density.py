"""Density of a stock map and of Station Zero, measured the same way: props, distinct models, world materials, lights.

  python -B density.py stock  --db <worldkit cp_zmb.sqlite> [--window 1000] [--areas 5] [--json out.json]
  python -B density.py zones  --src <emit src of Station Zero> [--json out.json]
  python -B density.py report --db ... --src ...      (both, as a markdown table, the numbers of docs/ASSET-LIBRARY.md)

Stock data: the world kit database (tools-source/worldkit/iw7_world.py build) of the cp_zmb dump, which was parsed from
`maps/cp/cp_zmb.d3dbsp.gfxmap` (static model instances `smodels`, world surfaces `surfaces` with their material and bounds,
primary lights `lights`) and `cp_zmb.d3dbsp.ents` (`ents`: script_model entities). Nothing else is read.
Station Zero: the emitted compiler source (layout.json decor + models, smodels.txt, surfaces.json quads, lights.txt).

A prop is a static model instance or a script model. A world material is a distinct material name of the world surfaces
whose bounds centre lies in the area. Areas of the stock map are 1000 x 1000 windows (stride 250) inside the playable box,
ranked by props, restricted to covered (indoor) ones: the share of the window under a horizontal surface 100..700 units
above the floor (the 20th percentile of the prop heights) is at least 0.6; chosen greedily with at most 25 % overlap.
"""
import argparse
import json
import os
import sqlite3
import sys

import numpy as np

# playable box of cp_zmb: union of its 13 gameplay spawn volumes (docs/station-zero/research/E-shipped-map-numbers.md)
PLAYABLE = (-3272.0, -3568.0, 4952.0, 3824.0)
SKIP_MATERIAL = ('sky', 'caulk', 'clip', 'trigger', 'nodraw', 'skip', 'hint')


def load_stock(db):
    c = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
    sm = np.array(c.execute('select x, y, z from smodels').fetchall(), np.float64)
    sm_model = [r[0] for r in c.execute('select model from smodels')]
    ent = c.execute("select origin_x, origin_y, origin_z, model from ents where classname='script_model' and model is not null").fetchall()
    surf = c.execute('select material, minx, miny, minz, maxx, maxy, maxz, tri_count from surfaces').fetchall()
    lights = np.array(c.execute('select x, y, z from lights').fetchall(), np.float64)
    return {'sm': sm, 'sm_model': sm_model, 'ent': ent, 'surf': surf, 'lights': lights}


def measure_box(S, box):
    """box = (x0, y0, x1, y1) -> props, distinct models, materials, lights, triangles, ceiling coverage."""
    x0, y0, x1, y1 = box
    sm = S['sm']
    in_sm = (sm[:, 0] >= x0) & (sm[:, 0] < x1) & (sm[:, 1] >= y0) & (sm[:, 1] < y1)
    models = {S['sm_model'][i] for i in np.nonzero(in_sm)[0]}
    ents = [e for e in S['ent'] if x0 <= e[0] < x1 and y0 <= e[1] < y1]
    models.update(e[3] for e in ents)
    mats, tris, roof = set(), 0, []
    for m, a, b, c, d, e, f, t in S['surf']:
        cx, cy = (a + d) / 2, (b + e) / 2
        if not (x0 <= cx < x1 and y0 <= cy < y1) or any(k in m.lower() for k in SKIP_MATERIAL):
            continue
        mats.add(m)
        tris += t
        if (d - a) >= 32 and (e - b) >= 32 and (f - c) <= 24:
            roof.append((a, b, d, e, c))
    L = S['lights']
    in_l = (L[:, 0] >= x0) & (L[:, 0] < x1) & (L[:, 1] >= y0) & (L[:, 1] < y1)
    floor = float(np.percentile(sm[in_sm][:, 2], 20)) if in_sm.any() else 0.0
    cell = 50.0
    nx, ny = int((x1 - x0) / cell), int((y1 - y0) / cell)
    cov = np.zeros((nx, ny), bool)
    for a, b, d, e, z in roof:
        if floor + 100 <= z <= floor + 700:
            i0, i1 = max(int((a - x0) / cell), 0), min(int(np.ceil((d - x0) / cell)), nx)
            j0, j1 = max(int((b - y0) / cell), 0), min(int(np.ceil((e - y0) / cell)), ny)
            cov[i0:i1, j0:j1] = True
    return {'box': [x0, y0, x1, y1], 'props': int(in_sm.sum()) + len(ents), 'static_models': int(in_sm.sum()),
            'script_models': len(ents), 'distinct_models': len(models), 'materials': len(mats), 'lights': int(in_l.sum()),
            'triangles': tris, 'covered': round(float(cov.mean()), 2) if cov.size else 0.0, 'floor_z': round(floor)}


def stock_areas(S, window=1000.0, stride=250.0, n=5, min_cover=0.6, max_overlap=0.25):
    x0, y0, x1, y1 = PLAYABLE
    cand = []
    for x in np.arange(x0, x1 - window + 1, stride):
        for y in np.arange(y0, y1 - window + 1, stride):
            sm = S['sm']
            cnt = int(((sm[:, 0] >= x) & (sm[:, 0] < x + window) & (sm[:, 1] >= y) & (sm[:, 1] < y + window)).sum())
            cand.append((cnt, float(x), float(y)))
    cand.sort(reverse=True)
    chosen, rows = [], []
    for cnt, x, y in cand:
        if len(rows) >= n or cnt < 50:
            break
        if any(max(0.0, min(x + window, cx + window) - max(x, cx)) * max(0.0, min(y + window, cy + window) - max(y, cy)) > max_overlap * window * window
               for cx, cy in chosen):
            continue
        r = measure_box(S, (x, y, x + window, y + window))
        if r['covered'] < min_cover:
            continue
        chosen.append((x, y))
        rows.append(r)
    return rows


def stock_zones(S, zones):
    """zones: {name: (x0, y0, x1, y1)} -> rows (used for the spawn volumes of the research page, E-shipped-map-numbers)."""
    return {k: measure_box(S, v) for k, v in zones.items()}


def parse_lines(path):
    out = []
    if os.path.isfile(path):
        for ln in open(path, encoding='utf-8', errors='replace'):
            ln = ln.strip()
            if ln and not ln.startswith(('#', '//')):
                out.append(ln.split())
    return out


def station_zones(src):
    lay = json.load(open(os.path.join(src, 'layout.json')))
    quads = json.load(open(os.path.join(src, 'surfaces.json')))['quads']
    sm = parse_lines(os.path.join(src, 'smodels.txt'))
    lt = parse_lines(os.path.join(src, 'lights.txt'))
    rows = {}
    for name, z in lay['zones'].items():
        b = z['box']
        x0, y0, x1, y1 = b[0], b[1], b[3], b[4]

        def inside(p):
            return x0 <= p[0] < x1 and y0 <= p[1] < y1
        static = [r for r in sm if inside((float(r[1]), float(r[2])))]
        script = [m for m in lay['models'] if m.get('zone') == name or (m.get('zone') is None and inside(m['origin']))]
        decor_dyn = [d for d in lay['decor'] if d['zone'] == name and not d.get('static')]
        models = {r[0] for r in static} | {m['model'] for m in script} | {d['model'] for d in decor_dyn}
        mats = {q[1] for q in quads if q[0] == name}
        tris = sum(2 for q in quads if q[0] == name)
        lights = [r for r in lt if inside((float(r[1]), float(r[2])))]
        authored = [x for x in lay['lights'] if x['zone'] == name]
        area = (x1 - x0) * (y1 - y0)
        rows[name] = {'box': [x0, y0, x1, y1], 'area': area, 'props': len(static) + len(script) + len(decor_dyn),
                      'static_models': len(static), 'script_models': len(script) + len(decor_dyn),
                      'geo_props': sum(1 for g in lay['geo_props'] if g['zone'] == name),
                      'distinct_models': len(models), 'materials': len(mats), 'lights': len(lights),
                      'authored_lights': len(authored), 'triangles': tris}
    return rows


def per_million(r, area):
    k = 1e6 / area
    return {m: round(r[m] * k, 1) for m in ('props', 'distinct_models', 'materials', 'lights')}


def report(S, src, window=1000.0, n=5):
    out = {'stock_areas': [], 'station_zero': {}}
    for r in stock_areas(S, window, n=n):
        r['per_million'] = per_million(r, window * window)
        out['stock_areas'].append(r)
    for name, r in station_zones(src).items():
        r['per_million'] = per_million(r, r['area'])
        out['station_zero'][name] = r
    return out


def markdown(rep):
    lines = ['| area | box (x0 y0 x1 y1) | covered | props | distinct models | materials | lights | props / 1000x1000 |',
             '|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(rep['stock_areas']):
        b = r['box']
        lines.append('| cp_zmb area %d | %d %d %d %d | %.2f | %d | %d | %d | %d | %d |' % (
            i + 1, b[0], b[1], b[2], b[3], r['covered'], r['props'], r['distinct_models'], r['materials'], r['lights'], r['props']))
    for name, r in rep['station_zero'].items():
        b = r['box']
        pm = r['per_million']
        lines.append('| SZ %s | %d %d %d %d | - | %d | %d | %d | %d | %d |' % (
            name, b[0], b[1], b[2], b[3], r['props'], r['distinct_models'], r['materials'], r['lights'], pm['props']))
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['stock', 'zones', 'report'])
    ap.add_argument('--db')
    ap.add_argument('--src')
    ap.add_argument('--window', type=float, default=1000.0)
    ap.add_argument('--areas', type=int, default=5)
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    if a.cmd == 'stock':
        rep = {'stock_areas': stock_areas(load_stock(a.db), a.window, n=a.areas)}
    elif a.cmd == 'zones':
        rep = {'station_zero': station_zones(a.src)}
    else:
        rep = report(load_stock(a.db), a.src, a.window, a.areas)
        print(markdown(rep))
    if a.json:
        json.dump(rep, open(a.json, 'w'), indent=1)
    if a.cmd != 'report':
        print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
