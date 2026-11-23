"""Baker light list (lights.json) from a generator layout.json (the level generator's `lights` list).

usage: layout_lights.py <source dir> <out lights.json> [--power 3.0] [--radius-scale 2.5] [--texel 8]
                        [--ambient 0.02] [--emissive 1.5]

<source dir> has layout.json (lights: [{origin, type omni|spot, color, radius, intensity, fixture, dir?}], and an optional
"lighting" block, see build_config), world.bin (material names) and smodels.txt (static props: baked shadows). The layout radius is the runtime/light-grid falloff radius; the bake uses a longer
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


def _rgb(v, default=None):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return [float(v)] * 3
    return [float(c) for c in v[:3]]


def build_config(src, power=3.0, radius_scale=2.5, texel=8.0, ambient=0.02, emissive=1.5, dump_roots=(), extra=None, prop_shadows=None):
    """-> (lights.json dict, report) of an emit folder (layout.json lights and `lighting` block, world.bin, smodels.txt).

    layout.json "lighting" (all optional; what a map author sets in the document, see docs/IWZ-EMIT-CONTRACT.md):
      prop_shadows        true (default) | false     static models block light in the bake (bake/occluders.py)
      prop_shadow_max_extent  200                      boxes larger than this (units) are not occluders
      ambient             number | [r,g,b] | {color [r,g,b], level, ao_radius}   fill light (default grey 0.02, blue x 1.1)
      bounces             indirect bounces (default 3)
      sky                 [r,g,b] radiance of the sky seen by escaping rays (default 0: interiors)
      sun                 {dir [x,y,z], color [r,g,b]} baked sun visibility
      emissive            {material: {color [r,g,b], strength s} | [r,g,b,s]}   the material emits color x strength (radiance)
      emissive_props      [{model, origin [x,y,z], angles [p,y,r], scale, color, strength}]   a static model that emits (its bounds box)
    prop_shadows (argument) overrides the layout when not None.
    """
    lay = json.load(open(os.path.join(src, 'layout.json')))
    st = lay.get('lighting') or {}
    w = lmbake.read_world(os.path.join(src, 'world.bin'))
    lights, fixture_col = [], {}
    runtime_only = 0
    for l in lay.get('lights', []):
        if l.get('runtime') and l.get('bake') is False:       # a pure runtime light (lights.txt, the engine's dynamic light): not in the lightmap
            runtime_only += 1
            continue
        col = [float(c) for c in l.get('color', [1, 1, 1])]
        mx = max(col) or 1.0
        col = [c / mx for c in col]
        fixture_col.setdefault(l.get('fixture', ''), col)
        rec = {'type': 'spot' if l.get('type') == 'spot' else 'point', 'origin': [float(c) for c in l['origin']],
               'color': col, 'intensity': float(l.get('intensity', 1.0)) * mx * power,
               'radius': float(l.get('radius', 384)) * radius_scale, 'size': 6.0, 'room': l.get('zone', '')}
        if rec['type'] == 'spot':
            rec.update({'dir': l.get('dir', [0, 0, -1]), 'inner': l.get('inner', 25), 'outer': l.get('outer', 60)})
        lights.append(rec)
    albedo, emi = {}, {}
    for m in w['materials']:
        albedo[m] = albedo_for(m)
        ml = m.lower()
        if 'lamp' in ml or ml.endswith('light_02_on') or ml.endswith('_on'):
            key = next((f for f in fixture_col if f and f.split('_')[-1] in ml), None)
            col = fixture_col.get(key, [1.0, 0.95, 0.85])
            emi[m] = [round(c * emissive, 3) for c in col]
    rep = {'runtime_only_lights_not_baked': runtime_only}
    doc_emi = st.get('emissive') or {}
    unknown = []
    for m, v in doc_emi.items():                       # the document wins over the name rule
        if isinstance(v, dict):
            col, k = _rgb(v.get('color'), [1.0, 1.0, 1.0]), float(v.get('strength', 1.0))
        else:
            col, k = _rgb(v), (float(v[3]) if len(v) > 3 else 1.0)
        if m not in albedo:
            unknown.append(m); continue
        emi[m] = [round(c * k, 4) for c in col]
    rep['emissive_materials_from_document'] = len(doc_emi) - len(unknown)
    rep['emissive_materials_unknown'] = unknown
    amb = st.get('ambient', None)
    if amb is None:
        acol, ao = [ambient, ambient, ambient * 1.1], 96
    elif isinstance(amb, dict):
        base = _rgb(amb.get('color'), [1.0, 1.0, 1.0])
        lvl = float(amb.get('level', 1.0 if amb.get('color') else ambient))
        acol, ao = [c * lvl for c in base], float(amb.get('ao_radius', 96))
    else:
        acol, ao = _rgb(amb), 96
    cfg = {'texel': texel, 'probe_cell': 128, 'albedo': albedo, 'default_albedo': [0.45, 0.45, 0.45], 'emissive': emi,
           'sky': _rgb(st.get('sky'), [0, 0, 0]), 'ambient': {'color': [round(c, 5) for c in acol], 'ao_radius': ao},
           'bounces': int(st.get('bounces', 3)), 'lights': lights}
    if st.get('sun'):
        cfg['sun'] = st['sun']
    boxes = []
    use_shadows = st.get('prop_shadows', True) if prop_shadows is None else prop_shadows
    roots = list(dump_roots) + [src]
    if use_shadows and os.path.isfile(os.path.join(src, 'smodels.txt')):
        import occluders
        boxes, orep = occluders.occluders(src, roots, [l['origin'] for l in lights], max_extent=float(st.get('prop_shadow_max_extent', 200.0)))
        rep['prop_shadows'] = orep
    eprops = st.get('emissive_props') or []
    if eprops:
        import occluders
        bounds, unk = occluders.model_bounds([e['model'] for e in eprops], src, roots)
        n_ok = 0
        for e in eprops:
            b = bounds.get(e['model'])
            if not b:
                continue
            col, k = _rgb(e.get('color'), [1.0, 1.0, 1.0]), float(e.get('strength', 1.0))
            cs = occluders.oriented_corners(e['origin'], e.get('angles', [0, 0, 0]), float(e.get('scale', 1.0)), b[0], b[1])
            boxes.append({'model': e['model'], 'emissive': [round(c * k, 4) for c in col], 'corners': [[round(v, 3) for v in c] for c in cs]})
            n_ok += 1
        rep['emissive_props'] = {'declared': len(eprops), 'baked': n_ok, 'unknown_models': unk}
    if boxes:
        cfg['occluders'] = boxes
    if extra:
        ex = json.load(open(extra)) if isinstance(extra, str) else extra
        for k, v in ex.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict): cfg[k].update(v)
            else: cfg[k] = v
    rep['summary'] = {'lights': len(lights), 'materials': len(albedo), 'emissive': len(emi), 'occluders': len(boxes), 'bounces': cfg['bounces'],
                      'ambient': cfg['ambient']['color'], 'sky': cfg['sky']}
    return cfg, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--power', type=float, default=3.0); ap.add_argument('--radius-scale', type=float, default=2.5)
    ap.add_argument('--texel', type=float, default=8); ap.add_argument('--ambient', type=float, default=0.02)
    ap.add_argument('--emissive', type=float, default=1.5)
    ap.add_argument('--extra', help='json merged over the result (albedo/emissive/sun/sky overrides)')
    ap.add_argument('--dump', action='append', default=[], help='a dump root holding <zone>/xmodel/<name>.xmb (model bounds for prop shadows); repeatable')
    ap.add_argument('--no-prop-shadows', action='store_true', help='no baked prop shadows whatever layout.json says')
    a = ap.parse_args()
    roots = list(a.dump) or ([os.environ['IWZ_TEMPLATE_DUMP']] if os.environ.get('IWZ_TEMPLATE_DUMP') else [])
    cfg, rep = build_config(a.src, a.power, a.radius_scale, a.texel, a.ambient, a.emissive, roots, a.extra, False if a.no_prop_shadows else None)
    json.dump(cfg, open(a.out, 'w'), indent=1)
    s = rep['summary']
    print('%d lights, %d materials (%d emissive), %d occluder boxes, %d bounces -> %s' % (s['lights'], s['materials'], s['emissive'], s['occluders'], s['bounces'], a.out))
    for k in ('prop_shadows', 'emissive_props'):
        if k in rep:
            print('  %s: %s' % (k, json.dumps({kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in rep[k].items()})))
    if rep.get('emissive_materials_unknown'):
        print('  emissive materials not in the world: %s' % ', '.join(rep['emissive_materials_unknown']))


if __name__ == '__main__':
    main()
