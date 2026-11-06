"""Place a generated map's audio from the level generator's layout (stdlib only).

    python audio_layout.py --layout <layout.json> --spec station_zero_audio_layout.json --bank station_zero_audio.json
                           --out <zone root>/scripts/cp/maps/<map>/<map>_audio_layout.gsc [--report positions.json]

The spec names, per zone, the 2D bed and the emitters by anchors in the layout, so positions follow the
level generator when rooms move:
  light:<zone>:<i>          i-th light of that zone        decor:<model>@<zone>    first matching decor
  quest:<name>              a quest point (teddy_bear ...)  interaction:<kind>      first interaction of that kind
  zone:<fx>,<fy>,<dz>       fraction of the zone box in x/y, dz units above its floor
  [x, y, z]                 an explicit origin
plus an optional "offset": [dx, dy, dz]. Two layout formats are read: stage-2 "zones" {name: {box: [x0, y0,
z0, x1, y1, z1]}} (floor = z0 + 16) and rc1 "rooms" {name: {box: [x0, y0, x1, y1], height}} (floor 0).

Checks (exit 1 on any): every alias is in the bank spec, every emitter lies inside its zone box, random
emitters have 0 < min_wait < max_wait, looping emitters per zone and in total stay under the limits, the
easter egg point lies in its zone. Writes one GSC rawfile whose init() starts the module's ambience (zone
beds + emitters) and the hidden-song bear; the level script calls it with one line:

    level thread scripts\\cp\\maps\\<map>\\<map>_audio_layout::init();
"""
import argparse
import json
import sys

FLOOR_MARGIN = 16


def zones_of(layout):
    """{name: (mins, maxs, floor)} from either layout format."""
    out = {}
    if 'zones' in layout:
        for name, z in layout['zones'].items():
            b = z['box']
            out[name] = ((b[0], b[1], b[2]), (b[3], b[4], b[5]), b[2] + FLOOR_MARGIN)
    elif 'rooms' in layout:
        for name, r in layout['rooms'].items():
            b = r['box']
            out[name] = ((b[0], b[1], -FLOOR_MARGIN), (b[2], b[3], r.get('height', 256) + FLOOR_MARGIN), 0)
    else:
        raise ValueError('layout has neither "zones" nor "rooms"')
    return out


def resolve(at, layout, zones):
    if isinstance(at, list):
        return [float(v) for v in at]
    kind, _, rest = at.partition(':')
    if kind == 'light':
        zone, _, index = rest.rpartition(':')
        lights = [l for l in layout.get('lights', []) if l.get('zone') == zone]
        if int(index) >= len(lights):
            raise ValueError('%s: zone %s has %d lights' % (at, zone, len(lights)))
        return [float(v) for v in lights[int(index)]['origin']]
    if kind == 'decor':
        model, _, zone = rest.partition('@')
        for d in layout.get('decor', []):
            if d.get('model') == model and (not zone or d.get('zone') == zone):
                return [float(v) for v in d['origin']]
        raise ValueError('%s: no such decor' % at)
    if kind == 'quest':
        q = layout.get('quest', {}).get(rest)
        if not q or 'origin' not in q:
            raise ValueError('%s: no such quest point' % at)
        return [float(v) for v in q['origin']]
    if kind == 'interaction':
        name, _, zone = rest.partition('@')
        for i in layout.get('interactions', []):
            if i.get('kind') == name and (not zone or i.get('zone', i.get('area')) == zone):
                return [float(v) for v in i['origin']]
        raise ValueError('%s: no such interaction' % at)
    if kind == 'zone':
        raise ValueError('%s: zone anchors take the emitter zone, write zone:<fx>,<fy>,<dz>' % at)
    raise ValueError('unknown anchor %r' % at)


def resolve_in_zone(at, zone_name, layout, zones):
    if isinstance(at, str) and at.startswith('zone:'):
        fx, fy, dz = (float(v) for v in at[5:].split(','))
        mins, maxs, floor = zones[zone_name]
        return [mins[0] + fx * (maxs[0] - mins[0]), mins[1] + fy * (maxs[1] - mins[1]), floor + dz]
    return resolve(at, layout, zones)


def inside(p, zone, margin=1.0):
    mins, maxs, _ = zone
    return all(mins[k] - margin <= p[k] <= maxs[k] + margin for k in range(3))


def vec(p):
    return '( %s )' % ', '.join(('%d' % round(v)) if abs(v - round(v)) < 1e-6 else ('%.1f' % v) for v in p)


def plan(layout, spec, bank_aliases):
    zones = zones_of(layout)
    errors, emitters, beds = [], [], []
    limit_zone = spec.get('max_loops_per_zone', 6)
    limit_total = spec.get('max_loops_total', 24)
    for name, z in spec.get('zones', {}).items():
        if name not in zones:
            errors.append('zone %s is not in the layout' % name)
            continue
        bed = z.get('bed')
        if bed and bed not in bank_aliases:
            errors.append('zone %s: bed %s is not in the bank' % (name, bed))
        beds.append({'zone': name, 'mins': list(zones[name][0]), 'maxs': list(zones[name][1]), 'bed': bed})
    default_bed = spec.get('default_bed')
    if default_bed and default_bed not in bank_aliases:
        errors.append('default bed %s is not in the bank' % default_bed)
    loops = {}
    for e in spec.get('emitters', []):
        zone = e['zone']
        if zone not in zones:
            errors.append('%s: zone %s is not in the layout' % (e['alias'], zone))
            continue
        if e['alias'] not in bank_aliases:
            errors.append('%s: alias is not in the bank' % e['alias'])
        try:
            p = resolve_in_zone(e['at'], zone, layout, zones)
        except (ValueError, KeyError) as exc:
            errors.append('%s in %s: %s' % (e['alias'], zone, exc))
            continue
        p = [p[k] + e.get('offset', [0, 0, 0])[k] for k in range(3)]
        if not inside(p, zones[zone]):
            errors.append('%s at %s lies outside zone %s %s..%s' % (e['alias'], vec(p), zone, zones[zone][0], zones[zone][1]))
        rnd = e.get('random')
        if rnd:
            if not (0 < rnd[0] < rnd[1]):
                errors.append('%s in %s: random wait needs 0 < min < max' % (e['alias'], zone))
        else:
            loops[zone] = loops.get(zone, 0) + 1
        emitters.append({'alias': e['alias'], 'zone': zone, 'origin': p, 'random': rnd, 'note': e.get('note', '')})
    for zone, n in loops.items():
        if n > limit_zone:
            errors.append('zone %s has %d looping emitters (limit %d)' % (zone, n, limit_zone))
    if sum(loops.values()) > limit_total:
        errors.append('%d looping emitters in total (limit %d)' % (sum(loops.values()), limit_total))
    ee = None
    if spec.get('song_ee'):
        s = spec['song_ee']
        try:
            p = resolve(s['at'], layout, zones)
            p = [p[k] + s.get('offset', [0, 0, 0])[k] for k in range(3)]
            yaw = s.get('yaw')
            if yaw is None and isinstance(s['at'], str) and s['at'].startswith('quest:'):
                yaw = layout['quest'][s['at'][6:]].get('yaw', 0)
            ee = {'origin': p, 'yaw': float(yaw or 0), 'zone': s.get('zone')}
            if s.get('zone') and not inside(p, zones[s['zone']]):
                errors.append('song easter egg at %s lies outside zone %s' % (vec(p), s['zone']))
        except (ValueError, KeyError) as exc:
            errors.append('song easter egg: %s' % exc)
    return {'zones': beds, 'default_bed': default_bed, 'emitters': emitters, 'song_ee': ee,
            'loops': loops, 'errors': errors}


def gsc(result, mapname, source):
    mod = 'scripts\\cp\\maps\\%s\\%s_audio' % (mapname, mapname)
    out = ['// Generated by iw7-creator-sdk tools-source/iwzmap/audio/audio_layout.py from %s; do not edit.' % source,
           '// %s ambience (zone beds, emitters) and hidden-song bear, positions from the level layout.' % mapname,
           'init()', '{', '    zones = [];']
    for z in result['zones']:
        bed = '"%s"' % z['bed'] if z['bed'] else 'undefined'
        out.append('    zones[zones.size] = %s::ambience_zone( "%s", %s, %s, %s );' % (mod, z['zone'], vec(z['mins']), vec(z['maxs']), bed))
    out.append('    emitters = [];')
    for e in result['emitters']:
        if e['random']:
            out.append('    emitters[emitters.size] = %s::ambience_emitter( "%s", %s, 1, %s, %s ); // %s' % (
                mod, e['alias'], vec(e['origin']), e['random'][0], e['random'][1], e['zone']))
        else:
            out.append('    emitters[emitters.size] = %s::ambience_emitter( "%s", %s ); // %s' % (mod, e['alias'], vec(e['origin']), e['zone']))
    bed = '"%s"' % result['default_bed'] if result['default_bed'] else 'undefined'
    out.append('    level thread %s::ambience_init( emitters, %s, zones );' % (mod, bed))
    if result['song_ee']:
        ee = result['song_ee']
        out.append('    level thread %s::song_ee_init( %s, ( 0, %s, 0 ) ); // %s' % (mod, vec(ee['origin']), ('%g' % ee['yaw']), ee.get('zone') or ''))
    out += ['}', '']
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--layout', required=True)
    ap.add_argument('--spec', required=True)
    ap.add_argument('--bank', required=True, help='bank spec (station_zero_audio.json): the alias names')
    ap.add_argument('--map', default=None)
    ap.add_argument('--out')
    ap.add_argument('--report')
    args = ap.parse_args(argv)
    with open(args.layout, encoding='utf-8') as f:
        layout = json.load(f)
    with open(args.spec, encoding='utf-8') as f:
        spec = json.load(f)
    with open(args.bank, encoding='utf-8') as f:
        bank = json.load(f)
    aliases = {a['name'] for a in bank['aliases']}
    result = plan(layout, spec, aliases)
    mapname = args.map or spec.get('map') or bank.get('zone')
    if args.report:
        with open(args.report, 'w') as f:
            json.dump(result, f, indent=1)
    if args.out and not result['errors']:
        with open(args.out, 'w', newline='\n') as f:
            f.write(gsc(result, mapname, args.layout.replace('\\', '/').split('/')[-1]))
    print(json.dumps({'zones': len(result['zones']), 'emitters': len(result['emitters']), 'loops': result['loops'],
                      'song_ee': result['song_ee'], 'errors': result['errors']}, indent=1))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
