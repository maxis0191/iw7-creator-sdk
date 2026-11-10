"""Baker light list (lights.json) from a generator layout.json (the level generator's `lights` list).

usage: layout_lights.py <source dir> <out lights.json> [--power 3.0] [--radius-scale 2.5] [--texel 8]
                        [--ambient 0.02] [--emissive 1.5]

<source dir> has layout.json (lights: [{origin, type omni|spot, color, radius, intensity, fixture, dir?}]) and
world.bin (material names). The layout radius is the runtime/light-grid falloff radius; the bake uses a longer
physical falloff (radius * radius-scale) and intensity * power in the baker's units (E = I * (100 / d)^2 * cos).
Albedo per material is guessed from the material name (override with an "albedo" block merged from --extra).
Lamp materials (*lamp*, *light*_on) are emissive with the colour of the nearest layout light of that fixture.
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lmbake

ALBEDO_RULES = [            # first match wins (name regex, linear albedo)
    (r'black|dark|rubber|com_black', 0.06),
    (r'white|cream|ceiling|plaster|ceramic', 0.62),
    (r'chrome|silver|steel|brushed', 0.45),
    (r'glass', 0.2),
    (r'red', 0.25),
    (r'yellow', 0.45),
    (r'green|blue', 0.3),
    (r'wood|plank', 0.3),
    (r'brick', 0.38),
    (r'concrete|stone|tile|marble|floor', 0.4),
    (r'metal|ibeam|grate|corrugated|door', 0.32),
    (r'sign|poster|map|decal|stain|dec$', 0.45),
]
TINT = {'red': (1.0, 0.45, 0.4), 'green': (0.75, 1.0, 0.8), 'blue': (0.75, 0.85, 1.0), 'yellow': (1.0, 0.9, 0.55),
        'cream': (1.0, 0.95, 0.85), 'wood': (1.0, 0.8, 0.6)}


def albedo_for(name):
    n = name.lower()
    a = 0.45
    for rx, v in ALBEDO_RULES:
        if re.search(rx, n):
            a = v; break
    tint = (1.0, 1.0, 1.0)
    for k, t in TINT.items():
        if k in n:
            tint = t; break
    return [round(a * c, 3) for c in tint]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--power', type=float, default=3.0); ap.add_argument('--radius-scale', type=float, default=2.5)
    ap.add_argument('--texel', type=float, default=8); ap.add_argument('--ambient', type=float, default=0.02)
    ap.add_argument('--emissive', type=float, default=1.5)
    ap.add_argument('--extra', help='json merged over the result (albedo/emissive/sun/sky overrides)')
    a = ap.parse_args()
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    w = lmbake.read_world(os.path.join(a.src, 'world.bin'))
    lights, fixture_col = [], {}
    for l in lay.get('lights', []):
        col = [float(c) for c in l.get('color', [1, 1, 1])]
        mx = max(col) or 1.0
        col = [c / mx for c in col]
        fixture_col.setdefault(l.get('fixture', ''), col)
        rec = {'type': 'spot' if l.get('type') == 'spot' else 'point', 'origin': [float(c) for c in l['origin']],
               'color': col, 'intensity': float(l.get('intensity', 1.0)) * mx * a.power,
               'radius': float(l.get('radius', 384)) * a.radius_scale, 'size': 6.0, 'room': l.get('zone', '')}
        if rec['type'] == 'spot':
            rec.update({'dir': l.get('dir', [0, 0, -1]), 'inner': l.get('inner', 25), 'outer': l.get('outer', 60)})
        lights.append(rec)
    albedo, emissive = {}, {}
    for m in w['materials']:
        albedo[m] = albedo_for(m)
        ml = m.lower()
        if 'lamp' in ml or ml.endswith('light_02_on') or ml.endswith('_on'):
            key = next((f for f in fixture_col if f and f.split('_')[-1] in ml), None)
            col = fixture_col.get(key, [1.0, 0.95, 0.85])
            emissive[m] = [round(c * a.emissive, 3) for c in col]
    cfg = {'texel': a.texel, 'probe_cell': 128, 'albedo': albedo, 'default_albedo': [0.45, 0.45, 0.45], 'emissive': emissive,
           'sky': [0, 0, 0], 'ambient': {'color': [a.ambient, a.ambient, a.ambient * 1.1], 'ao_radius': 96}, 'lights': lights}
    if a.extra:
        ex = json.load(open(a.extra))
        for k, v in ex.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict): cfg[k].update(v)
            else: cfg[k] = v
    json.dump(cfg, open(a.out, 'w'), indent=1)
    print('%d lights, %d materials (%d emissive) -> %s' % (len(lights), len(albedo), len(emissive), a.out))


if __name__ == '__main__':
    main()
