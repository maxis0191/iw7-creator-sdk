r"""arcade_score: the Arcade shell document against QUALITY-BAR part C (the count rules that apply to a shell).

    python arcade_score.py [doc folder] [--json out.json]

Reads the document's layers only (no game). Rules scored: 1, 2, 9, 10, 11, 12, 13, 16, 17, 23, 24, 25 (sign families). Not applicable to a shell:
4 (closed fronts), 15 (perk lights: no perk in this section); 3, 5, 6, 7, 8, 14 belong to the goods (workers A3) or to a blind review.
Definitions are QUALITY-BAR's: fixture model = a model name holding light, lamp, fluo, sconce, bulb, lantern or neon; hue class of a light =
its colour scaled to its peak (white: all channels above 0.85). Dominant hue of a shop = the class with the largest summed intensity.
"""
import json
import math
import os
import statistics
import sys

DOC = r'C:\studio-data\sz\film\arcade\shell\doc'
HALL = (-3000.0, 3500.0, -1200.0, 4300.0)
UNITS = {'needle_drop': (-2960.0, -2640.0), 'copy_stop': (-2630.0, -1980.0), 'hole_nine': (-1970.0, -1650.0), 'heel_key': (-1640.0, -1320.0)}
ROW_Y = (4200.0, 4600.0)          # a shop's own lights: inside the unit, or at its front (fascia lamps) north of y 4200
FIXTURE_WORDS = ('light', 'lamp', 'fluo', 'sconce', 'bulb', 'lantern', 'neon')
KIT = {'wall': 'w/dt_tile_ceramic_white', 'damaged twin': 'w/dt_tile_ceramic_white_dmg', 'band': 'w/ceramic_tile_01_orange',
       'dark': 'w/fac_tile_black_01', 'floor': 'w/linoleum_floor_tiles_orange_01'}


def load(folder):
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import Map
    return [dict(o) for o in Map.load(folder).objects()]


def hue(c):
    r, g, b = c
    k = max(r, g, b) or 1.0
    r, g, b = r / k, g / k, b / k
    if min(r, g, b) > 0.85:
        return 'white'
    if g < 0.35 and b < 0.35:
        return 'red'
    if r > 0.75 and b > 0.5 and g < min(r, b) - 0.15:
        return 'magenta'
    if g >= r and g >= b:
        return 'green'
    if b >= r and b >= g:
        return 'cool' if r > 0.6 else 'blue'
    return 'warm'


def in_box(p, x0, y0, x1, y1):
    return x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def score(folder):
    objs = load(folder)
    lights = [o for o in objs if o['kind'] == 'light']
    props = [o for o in objs if o['kind'] == 'prop']
    signs = [o for o in objs if o['kind'] == 'sign']
    rows = []

    def rule(n, name, ok, number, note=''):
        rows.append({'rule': n, 'name': name, 'pass': ok, 'number': number, 'note': note})

    # 1 and 2: hero signs (150 or wider) on the fronts
    hero = [s for s in signs if s['size'][0] >= 150 and s['at'][1] > 4200 and s['at'][2] > 150]
    groups = {}
    for s in hero:
        groups.setdefault((round(s['size'][0]), round(s['size'][1]), os.path.basename(str(s.get('image')))), []).append(s['id'])
    by_size = {}
    for s in hero:
        by_size.setdefault((round(s['size'][0]), round(s['size'][1])), []).append(s['id'])
    per_shop = {nm: [s for s in hero if x0 <= s['at'][0] <= x1] for nm, (x0, x1) in UNITS.items()}
    rule(1, 'every shop told by a hero sign of its own', all(per_shop.values()) and all(len(v) == 1 for v in groups.values()),
         '%d hero signs, %d distinct pictures, every shop has one' % (len(hero), len(groups)),
         'grouped by size alone: %s (three fascias share 300 x 68 by the brief; their pictures differ)' % {('%dx%d' % k): len(v) for k, v in by_size.items()})
    faces = {nm: max([s['size'][0] * s['size'][1] for s in v] or [0]) for nm, v in per_shop.items()}
    rule(2, 'hero sign face 19,600 or more', all(f >= 19600 for f in faces.values()), faces)
    # 9: lights per 1,000 square units, the hall and each shop
    def lights_in(x0, y0, x1, y1):
        return [o for o in lights if in_box(o['origin'], x0, y0, x1, y1)]
    dens = {'hall': (len(lights_in(*HALL)), (HALL[2] - HALL[0]) * (HALL[3] - HALL[1]))}
    for nm, (x0, x1) in UNITS.items():
        dens[nm] = (len(lights_in(x0, 4300.0, x1, 4600.0)), (x1 - x0) * 300.0)
    d9 = {k: '%d lights, %.4f per 1,000' % (n, n / a * 1000.0) for k, (n, a) in dens.items()}
    rule(9, 'at most 0.049 lights per 1,000', all(n / a * 1000.0 <= 0.049 for n, a in dens.values()), d9,
         'and at most 70 in the hall (%d), 5 a shop' % dens['hall'][0])
    # 10: median radius
    med = statistics.median([o['radius'] for o in lights])
    rule(10, 'median light radius 175 or more', med >= 175, round(med, 1), '%d lights' % len(lights))
    # 11 and 12: per shop rows and hues
    shop_lights = {nm: [o for o in lights if x0 <= o['origin'][0] <= x1 and ROW_Y[0] <= o['origin'][1] <= ROW_Y[1]] for nm, (x0, x1) in UNITS.items()}
    rows_of = {nm: {(round(o['intensity'], 3), round(o['radius'], 1), round(o['origin'][2], 1)) for o in v} for nm, v in shop_lights.items()}
    shared = []
    names = list(UNITS)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for r in rows_of[names[i]] & rows_of[names[j]]:
                shared.append((names[i], names[j], r))
    rule(11, 'no two shops share a light row (strength, radius, height)', not shared, '%d shared' % len(shared), {k: sorted(v) for k, v in rows_of.items()})
    dom = {}
    for nm in names:
        acc = {}
        for o in [o for o in lights if in_box(o['origin'], UNITS[nm][0], 4300.0, UNITS[nm][1], 4600.0)]:
            acc[hue(o['color'])] = acc.get(hue(o['color']), 0.0) + float(o['intensity'])
        dom[nm] = (max(acc, key=acc.get) if acc else None, {k: round(v, 2) for k, v in acc.items()})
    nb = all(dom[names[i]][0] != dom[names[i + 1]][0] for i in range(len(names) - 1))
    hall_hues = sorted({hue(o['color']) for o in lights_in(*HALL)})
    room_hues = {nm: len(dom[nm][1]) for nm in names}
    rule(12, 'neighbouring shops differ in dominant hue; four hue classes at most a room', nb and len(hall_hues) <= 4 and max(room_hues.values()) <= 4,
         {nm: dom[nm][0] for nm in names}, 'hall classes %s; per shop %s' % (hall_hues, {nm: dom[nm][1] for nm in names}))
    # 13: fixture models within 96, tubes off
    fx = [p for p in props if any(w in (p.get('model') or '').lower() for w in FIXTURE_WORDS)]
    near = [o for o in lights if any(math.dist(o['origin'], p['origin']) <= 96.0 for p in fx)]
    tubes = [p for p in fx if 'fluorescent' in p['model'] or 'tube' in p['model']]
    off = [p for p in tubes if p['model'].endswith('_off') or 'dmg' in p['model'] or 'damaged' in p['model']]
    share, toff = len(near) / max(1, len(lights)), len(off) / max(1, len(tubes))
    rule(13, '65 % of lights within 96 of a fixture model; 40 % of tube fixtures off or damaged', share >= 0.65 and toff >= 0.40,
         '%d of %d lights (%.0f %%); %d of %d tubes off (%.0f %%)' % (len(near), len(lights), share * 100, len(off), len(tubes), toff * 100),
         'lights without a fixture model: %s' % sorted(o['id'] for o in lights if o not in near))
    # 16: perk spacing
    perks = [o for o in objs if o['kind'] == 'perk']
    close = [(a['id'], b['id']) for i, a in enumerate(perks) for b in perks[i + 1:] if math.dist(a['at'], b['at']) < 404]
    rule(16, 'no two perk machines within 404', not close, '%d perks in the section' % len(perks))
    # 17: pockets hosting gameplay
    gp = [o for o in objs if o['kind'] in ('wallbuy', 'wheel', 'perk', 'pap', 'power')]
    host = {nm: [o['id'] for o in gp if in_box(o['at'], x0, 4300.0, x1, 4600.0)] for nm, (x0, x1) in UNITS.items()}
    n17 = sum(1 for v in host.values() if v)
    rule(17, 'three of five pockets host a gameplay object (3 of 4 here)', n17 / len(UNITS) >= 0.6, '%d of %d' % (n17, len(UNITS)), host)
    # 23: columns
    cols = sorted([o for o in objs if o['kind'] == 'box' and str(o['id']).startswith('col_') and str(o['id']).count('_') == 1], key=lambda o: o['box'][0])
    xs = [(o['box'][0] + o['box'][3]) / 2 for o in cols]
    pitches = sorted({round(b - a, 1) for a, b in zip(xs, xs[1:])})
    mats = sorted({o['material'] for o in cols})
    foreign = [p['model'] for p in props if 'column' in (p.get('model') or '') or 'pillar' in (p.get('model') or '')]
    rule(23, 'one column pitch, columns in the hall tile, none from another theme', len(pitches) == 1 and mats == [KIT['wall']] and not foreign,
         'pitch %s, %d columns, material %s' % (pitches, len(cols), mats), 'column models of another theme: %s' % foreign)
    # 24: tile kit of five
    used = {o.get('material') for o in objs}
    used |= {o.get('wall_material') for o in objs} | {o.get('floor_material') for o in objs}
    have = {k: v in used for k, v in KIT.items()}
    rule(24, 'tile kit of five: wall, its damaged twin, band, dark, floor', all(have.values()), have)
    # 25: sign families in the hall
    hs = [s for s in signs if in_box(s['at'], *HALL)]
    fam = {}
    for s in hs:
        w, h = s['size']
        key = ('fascia' if h == 68 else 'panel 64x96' if (w, h) == (64, 96) else 'directory' if (w, h) == (120, 160)
               else 'notice' if (w, h) == (16, 22) else 'hanging' if str(s['id']).startswith(('banner', 'bunting')) else '%gx%g' % (w, h))
        f = fam.setdefault(key, {'n': 0, 'w': [], 'z': []})
        f['n'] += 1
        f['w'].append(w)
        f['z'].append(round(s['at'][2]))
    famrep = {k: {'signs': v['n'], 'width': [min(v['w']), max(v['w'])], 'z': [min(v['z']), max(v['z'])]} for k, v in fam.items()}
    rule(25, 'four sign families at most a hall (doc part; the landmark is a blind question)', len(fam) <= 4, '%d families' % len(fam), famrep)
    return rows


def table(rows):
    out = ['| # | Rule | Number | Pass |', '|---|---|---|---|']
    for r in rows:
        num = r['number'] if isinstance(r['number'], str) else json.dumps(r['number'])
        out.append('| %d | %s | %s | %s |' % (r['rule'], r['name'], num, 'pass' if r['pass'] else '**fail**'))
    return '\n'.join(out)


if __name__ == '__main__':
    a = sys.argv[1:]
    folder = a[0] if a and not a[0].startswith('--') else DOC
    rows = score(folder)
    if '--json' in a:
        json.dump(rows, open(a[a.index('--json') + 1], 'w', encoding='utf-8'), indent=1)
    print(table(rows))
    for r in rows:
        if r['note']:
            print('rule %d: %s' % (r['rule'], r['note'] if isinstance(r['note'], str) else json.dumps(r['note'])))
