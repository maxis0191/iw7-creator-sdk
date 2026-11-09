"""Darkness build step: the dark (pre-power) bake and the scripted power lights, from the layout light groups.

A generated map declares, on every layout light (layout.json `lights[]`), a light group:
  emergency  stays on in the dark: baked into the lightmap / light grid (battery lamps, signal lamps, amber cues)
  power      comes on with the power switch: NOT baked; becomes a script-switchable primary light (lights.txt
             `name=iwz_power group=<bank>|<zone>|<on intensity>|<kind>`), turned on bank by bank by cp_iwz_darkness.gsc
  flicker    a power light that keeps flickering after power-on (same record, kind "flicker")
Dead fixtures (intensity 0) are skipped.

Inputs: the generator output directory (layout.json, lights.txt, lights_groups.json) and the baker light list of the
LIT map made by bake/layout_lights.py from the same layout (one baker light per layout light, same order).
Outputs:
  <out lights.json>        baker input of the dark state: emergency lights only, power-fixture materials not emissive,
                           ambient fill set by --ambient (the outside-the-flashlight floor)
  <src>/lights.txt         rewritten: the generator's emergency lines unchanged, its power lines and every power /
                           flicker layout light as named scriptable lights
  <src>/darkness.json      report (counts, banks, slots requested)

Bank order: zones sorted by distance from the power switch (layout interaction kind "generator"), the order the
audio sequence registers its banks in.

usage: dark_build.py <src> <lit lights.json> <out dark lights.json> [--ambient 0.03] [--scale 9000]
       [--radius-scale 2.2] [--ceiling-fov 150] [--shadow-per-zone 1] [--keep-emissive lamp_red,lamp_green]
"""
import argparse, json, math, os, sys

POWER_FIXTURE_MATS = {'lamp_cool': 'w/iwz_lamp_cool', 'lamp_warm': 'w/iwz_lamp_warm'}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('lit'); ap.add_argument('out')
    ap.add_argument('--ambient', type=float, default=0.03)
    ap.add_argument('--scale', type=float, default=9000.0, help='lights.txt intensity per layout intensity unit')
    ap.add_argument('--radius-scale', type=float, default=2.2)
    ap.add_argument('--ceiling-fov', type=float, default=150.0)
    ap.add_argument('--shadow-per-zone', type=int, default=1, help='brightest N power lights per zone cast shadows')
    ap.add_argument('--power-emissive', type=float, default=0.0, help='emissive of power fixture materials in the dark bake')
    ap.add_argument('--alt', default='', help='calibration light sets "b:dz=-24,rs=3.0,is=0.5|c:..." named iwz_power_<set>')
    ap.add_argument('--cue-scale', type=float, default=1.0,
                    help='intensity scale of the amber interaction cues in the dark bake (run dk9: 1.0 lit the door / perk '
                         'areas almost like a lamp under the dark exposure; 0.4 suggested, not engine-tested)')
    a = ap.parse_args(argv)

    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    lit = json.load(open(a.lit))
    L = lay['lights']
    if len(lit['lights']) != len(L):
        raise SystemExit('baker list has %d lights, layout %d: make it with layout_lights.py from this layout' % (len(lit['lights']), len(L)))
    if 'light_groups' not in lay:
        raise SystemExit('layout.json has no light groups (generator older than 03faead)')

    # ---- dark bake input
    dark = dict(lit)
    dark['lights'] = []
    for l, b in zip(L, lit['lights']):
        if l.get('group') == 'emergency' and float(l.get('intensity', 0)) > 0:
            if l.get('fixture') == 'hint_glow' and a.cue_scale != 1.0:
                b = dict(b, intensity=float(b['intensity']) * a.cue_scale)
            dark['lights'].append(b)
    dark['ambient'] = dict(lit.get('ambient', {}), color=[a.ambient, a.ambient, a.ambient * 1.1])
    em = dict(lit.get('emissive', {}))
    for m in list(em):
        if any(m.endswith(p.split('/')[-1]) or m == p for p in POWER_FIXTURE_MATS.values()):
            em[m] = [round(c * a.power_emissive, 4) for c in em[m]]
    dark['emissive'] = em
    json.dump(dark, open(a.out, 'w'), indent=1)

    # ---- bank order: distance of each zone's lights from the power switch
    gen = next((i['origin'] for i in lay.get('interactions', []) if i.get('kind') == 'generator'), None)
    zones = lay.get('zones', {})

    def zone_centre(z):
        b = zones.get(z, {}).get('box')
        return [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2] if b else None

    power = [l for l in L if l.get('group') in ('power', 'flicker') and float(l.get('intensity', 0)) > 0 and not l.get('dead')]
    zl = sorted({l.get('zone') or '' for l in power})
    def dist(z):
        c = zone_centre(z)
        if not c or not gen:
            return 1e9
        return math.dist(c[:2], gen[:2])
    order = sorted(zl, key=dist)
    bank = {z: k for k, z in enumerate(order)}

    # ---- lights.txt: keep the generator's emergency lines, rewrite its power lines as named lights
    lines = open(os.path.join(a.src, 'lights.txt')).read().split('\n') if os.path.exists(os.path.join(a.src, 'lights.txt')) else []
    lines = [x for x in lines if x.strip()]
    groups = {}
    gp = os.path.join(a.src, 'lights_groups.json')
    if os.path.exists(gp):
        groups = {g['line']: g['group'] for g in json.load(open(gp))['lines']}
    out_lines, named = [], []
    for k, t in enumerate(lines):
        if groups.get(k, 'emergency') == 'power':
            p = t.split()
            o = [float(v) for v in p[1:4]]
            z = min(order, key=lambda zz: math.dist(o[:2], zone_centre(zz)[:2]) if zone_centre(zz) else 1e9) if order else ''
            named.append({'line': t, 'zone': z, 'kind': 'extra'})
            out_lines.append('%s name=iwz_power group=%d|%s|%s|extra' % (t, bank.get(z, 0), z, p[7]))
        else:
            out_lines.append(t)
    by_zone = {}
    for l in power:
        by_zone.setdefault(l.get('zone') or '', []).append(l)
    shadow_ids = set()
    for z, ls in by_zone.items():
        for l in sorted(ls, key=lambda l: -float(l['intensity']) * float(l['radius']))[:a.shadow_per_zone]:
            shadow_ids.add(id(l))
    for l in power:
        x, y, zc = l['origin']
        r, g, b = l.get('color', (1, 1, 1))
        inten = float(l['intensity']) * a.scale
        rad = float(l['radius']) * a.radius_scale
        z = l.get('zone') or ''
        kind = 'flicker' if l.get('group') == 'flicker' else l.get('fixture', 'lamp')
        sh = 1 if id(l) in shadow_ids else 0
        tail = 'name=iwz_power group=%d|%s|%g|%s' % (bank.get(z, 0), z, inten, kind)
        if float(l['radius']) >= 380 and l.get('fixture') in ('lamp_cool', 'lamp_warm'):
            # ceiling strip: a wide downward spot (a diffuser lights the room below it, not the ceiling)
            out_lines.append('spot %g %g %g %.3f %.3f %.3f %g %g 90 0 %g %d %s' % (x, y, zc, r, g, b, inten, rad, a.ceiling_fov, sh, tail))
        else:
            out_lines.append('omni %g %g %g %.3f %.3f %.3f %g %g %d %s' % (x, y, zc, r, g, b, inten, rad, sh, tail))
        named.append({'zone': z, 'kind': kind, 'origin': [x, y, zc], 'intensity': inten, 'radius': rad, 'shadow': sh})
    # calibration only: alternative power-light sets named iwz_power_<set> (the module ignores them; a probe switches
    # them with setlightintensity). --alt "b:dz=-24,rs=3.0,is=0.5|c:dz=-24,rs=4.5,is=0.35": every power light as an
    # unshadowed omni, dz below the fitting, radius x rs (of the layout radius), intensity x is (of this build's).
    alt_n = 0
    for spec in [s for s in (a.alt or '').split('|') if s]:
        sname, _, kv = spec.partition(':')
        o = dict(p.split('=') for p in kv.split(',') if '=' in p)
        dz, rs, iscale = float(o.get('dz', 0)), float(o.get('rs', a.radius_scale)), float(o.get('is', 1))
        for l in power:
            x, y, zc = l['origin']
            r, g, b = l.get('color', (1, 1, 1))
            inten = float(l['intensity']) * a.scale * iscale
            z = l.get('zone') or ''
            kind = 'flicker' if l.get('group') == 'flicker' else l.get('fixture', 'lamp')
            out_lines.append('omni %g %g %g %.3f %.3f %.3f %g %g 0 name=iwz_power_%s group=%d|%s|%g|%s' % (
                x, y, zc + dz, r, g, b, inten, float(l['radius']) * rs, sname, bank.get(z, 0), z, inten, kind))
            alt_n += 1
    open(os.path.join(a.src, 'lights.txt'), 'w', newline='\n').write('\n'.join(out_lines) + '\n')
    rep = {'bank_order': order, 'generator': gen, 'baked_emergency': len(dark['lights']), 'named_lights': len(named),
           'shadowed': sum(1 for n in named if n.get('shadow')), 'ambient': a.ambient, 'scale': a.scale, 'alt_lights': alt_n,
           'per_zone': {z: len(v) for z, v in by_zone.items()}, 'emissive_zeroed': [m for m in em if em[m] != lit['emissive'].get(m)]}
    json.dump(rep, open(os.path.join(a.src, 'darkness.json'), 'w'), indent=1)
    print('dark bake: %d emergency lights (of %d); %d named power lights in %d banks %s; %d calibration lights' % (
        len(dark['lights']), len(L), len(named), len(order), ','.join(order), alt_n))


if __name__ == '__main__':
    main()
