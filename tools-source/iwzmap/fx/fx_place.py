"""Place stock IW7 ambient FX in a generated usermap: fx.txt -> level script module + proof fixture + manifest.

usage: fx_place.py <fx.txt> <generated source dir> [--ncs <ncs_efx_level.json> ...] [--catalog fx_catalog.json]
                   [--fixture-out <gsc>] [--manifest-out <json>] [--dry-run]

The source dir is a station_zero2.py output (cp_iwz.gsc, layout.json). cp_iwz.gsc is patched in place:
  - the generator's old `level thread iwz_ambient_fx();` call (if any) is replaced by `level thread iwz_fx_main();`,
  - every FX id is registered in main() with loadfx (main() runs at map load, before the first frame),
  - the iwz_fx_* module (tools-source/iwzmap/fx/iwz_fx.gsc) is appended with the generated table.
A second run replaces the previous generated block (markers //@IWZFX-BEGIN@ .. //@IWZFX-END@).

fx.txt: one effect per line, '#' starts a comment, fields separated by blanks:
  <name> <fx> <x> <y> <z> [key=value ...]
  <fx>       an alias of fx_catalog.json (dust_motes, drips, fog_low, ...) or a vfx path (vfx/iw7/...)
  angles=p,y,r   orientation (default from the catalog, else 0,0,0): forward = anglestoforward, up = anglestoup
  mode=loop                  spawnfx + triggerfx once (a looping vfx asset keeps emitting; stock createfx route)
  mode=retrigger:<s>         spawnfx once, triggerfx again every <s> seconds (non-looping assets as ambience)
  mode=interval:<a>-<b>      playfx every random a..b seconds (sparks, debris dust, flicker bursts)
  mode=oneshot               playfx once at start
  delay=<s>                  loop: triggerfx time offset (stock createfx uses -4: the emitter starts pre-rolled);
                             interval/oneshot: wait before the first play
  view=x,y,z,yaw,pitch       proof camera (player origin = feet); default: candidates computed from the layout zone
  region=<r>                 proof region half size in units (default from the catalog, else 64)
  zone=<zone>                layout zone (default: the zone box containing the origin)

Only effects of the level NetConstStrings list (`ncs_efx_level`, plus lists given with --ncs, e.g. one written by
fx_import.py) can be registered: IW7 resolves loadfx/playfx through that list. A name outside it is an error here.

Proof: the module obeys two dvars only when `paris_iwz_fxproof` is set (private fixture runs): paris_iwz_fxonly
(-1 every FX, -2 none, k only FX k) and paris_iwz_fxphase (frame-time phase, read by the fxperf diagnostic DLL).
Without paris_iwz_fxproof the module starts every FX once and exits (no polling cost in a real match).
"""
import argparse, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BEGIN, END = '//@IWZFX-BEGIN@', '//@IWZFX-END@'


def parse_fx_txt(path, catalog):
    out = []
    for no, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        q = line.split()
        if len(q) < 5:
            raise SystemExit('%s:%d: need <name> <fx> <x> <y> <z>' % (path, no))
        name, fx = q[0], q[1]
        if not re.match(r'^[A-Za-z0-9_]+$', name):
            raise SystemExit('%s:%d: bad name %r' % (path, no, name))
        cat = catalog.get(fx, {})
        e = {'name': name, 'alias': fx if cat else None, 'fx': cat.get('fx', fx), 'origin': [float(v) for v in q[2:5]],
             'angles': cat.get('angles', [0, 0, 0]), 'mode': cat.get('mode', 'loop'), 'delay': cat.get('delay', -4 if cat.get('mode', 'loop') == 'loop' else 0),
             'region': cat.get('region', 64), 'settle': cat.get('settle', 2.5), 'view': None, 'zone': None, 'line': no,
             'kind': cat.get('kind', ''), 'region_dz': cat.get('region_dz', 0)}
        for kv in q[5:]:
            if '=' not in kv:
                raise SystemExit('%s:%d: expected key=value, got %r' % (path, no, kv))
            k, v = kv.split('=', 1)
            if k == 'angles':
                e['angles'] = [float(x) for x in v.split(',')]
            elif k == 'mode':
                e['mode'] = v
            elif k == 'delay':
                e['delay'] = float(v)
            elif k == 'view':
                e['view'] = [float(x) for x in v.split(',')]
            elif k == 'region':
                e['region'] = float(v)
            elif k == 'zone':
                e['zone'] = v
            elif k == 'settle':
                e['settle'] = float(v)
            else:
                raise SystemExit('%s:%d: unknown key %r' % (path, no, k))
        m = e['mode']
        if m.startswith('interval:'):
            a, b = m.split(':', 1)[1].split('-')
            e['mode'], e['min'], e['max'] = 'interval', float(a), float(b)
        elif m.startswith('retrigger:'):
            e['mode'], e['min'] = 'retrigger', float(m.split(':', 1)[1]); e['max'] = e['min']
        elif m in ('loop', 'oneshot'):
            e['min'] = e['max'] = 0.0
        else:
            raise SystemExit('%s:%d: unknown mode %r' % (path, no, m))
        e['fx'] = e['fx'][:-4] if e['fx'].endswith('.vfx') else e['fx']
        out.append(e)
    names = [e['name'] for e in out]
    dup = sorted(set(n for n in names if names.count(n) > 1))
    if dup:
        raise SystemExit('duplicate names: %s' % dup)
    return out


def vec_fwd_up(angles):
    p, y, r = [math.radians(a) for a in angles]
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(r), math.cos(r)
    fwd = (cp * cy, cp * sy, -sp)
    up = (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp)
    return fwd, up


def zone_of(p, zones):
    for z, d in zones.items():
        b = d['box']
        if b[0] <= p[0] <= b[3] and b[1] <= p[1] <= b[4] and b[2] - 8 <= p[2] <= b[5]:
            return z
    return None


def candidate_views(e, zones):
    """up to 6 cameras in the FX zone box, 200..340 units away, eye looking at the region centre"""
    z = e['zone']
    b = zones[z]['box'] if z in zones else None
    o = e['origin']
    c = (o[0], o[1], o[2] + e['region_dz'])
    floor = b[2] + 16 if b else o[2] - 60
    outv = []
    for dist in (240, 320, 200):
        for k in range(8):
            yaw = k * 45.0
            cx, cy = c[0] - dist * math.cos(math.radians(yaw)), c[1] - dist * math.sin(math.radians(yaw))
            if b and not (b[0] + 48 <= cx <= b[3] - 48 and b[1] + 48 <= cy <= b[4] - 48):
                continue
            eye = floor + 60
            pitch = -math.degrees(math.atan2(c[2] - eye, dist))
            pitch = max(-45.0, min(45.0, pitch))
            outv.append([round(cx, 1), round(cy, 1), round(floor, 1), yaw, round(pitch, 2)])
        if len(outv) >= 6:
            break
    return outv[:6]


def gsc_vec(v):
    return '( %s )' % ', '.join('%g' % round(x, 4) for x in v)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('fx_txt'); ap.add_argument('src')
    ap.add_argument('--ncs', action='append', default=[], help='ncs_efx json (stringList) of registrable effects')
    ap.add_argument('--catalog', default=os.path.join(HERE, 'fx_catalog.json'))
    ap.add_argument('--fixture-out', default='')
    ap.add_argument('--manifest-out', default='')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)

    catalog = json.load(open(a.catalog))['fx'] if os.path.isfile(a.catalog) else {}
    fx = parse_fx_txt(a.fx_txt, catalog)
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    zones = lay.get('zones', {})
    ncs = set()
    for p in a.ncs:
        ncs |= set(json.load(open(p)).get('stringList') or [])
    bad = [e for e in fx if ncs and e['fx'] not in ncs]
    if bad:
        raise SystemExit('not in the level FX list (ncs_efx): %s' % ', '.join('%s=%s' % (e['name'], e['fx']) for e in bad))
    for e in fx:
        e['zone'] = e['zone'] or zone_of(e['origin'], zones)
        e['forward'], e['up'] = vec_fwd_up(e['angles'])
        e['views'] = [e['view']] if e['view'] else candidate_views(e, zones)
        if not e['views']:
            raise SystemExit('%s: no proof camera fits zone %s; give view=' % (e['name'], e['zone']))

    ids = sorted(set(e['fx'] for e in fx))
    key = {p: 'iwz_amb_%d' % i for i, p in enumerate(ids)}
    load = ['    level._effect["%s"] = loadfx( "%s" );' % (key[p], p) for p in ids]
    table = []
    for k, e in enumerate(fx):
        table.append('    level.iwz_fx[level.iwz_fx.size] = iwz_fx_def( "%s", "%s", %s, %s, %s, "%s", %g, %g, %g );'
                     % (e['name'], key[e['fx']], gsc_vec(e['origin']), gsc_vec(e['forward']), gsc_vec(e['up']), e['mode'],
                        e['delay'], e['min'], e['max']))
    module = open(os.path.join(HERE, 'iwz_fx.gsc')).read().replace('//@FXTABLE@', '\n'.join(table))

    gp = os.path.join(a.src, 'cp_iwz.gsc')
    g = open(gp).read()
    g = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?', '', g, flags=re.S)
    call_old, call_new = 'level thread iwz_ambient_fx();', 'level thread iwz_fx_main();'
    if call_old in g:
        g = g.replace('    ' + call_old, '    %s\n' % BEGIN + '\n'.join(load) + '\n    ' + call_new + '\n    %s' % END, 1)
    elif call_new not in g:
        at = g.index('main()\n{\n') + len('main()\n{\n')
        g = g[:at] + '    %s\n' % BEGIN + '\n'.join(load) + '\n    ' + call_new + '\n    %s\n' % END + g[at:]
    g = g.rstrip('\n') + '\n\n' + BEGIN + '\n' + module.rstrip('\n') + '\n' + END + '\n'
    if g.count(call_new) != 1:
        raise SystemExit('cp_iwz.gsc: expected exactly one iwz_fx_main call')

    man = {'schema': 'iwzmap.fx/1', 'src': os.path.abspath(a.src), 'fx': [
        {k: e[k] for k in ('name', 'alias', 'fx', 'origin', 'angles', 'forward', 'up', 'mode', 'delay', 'min', 'max', 'zone',
                           'views', 'region', 'region_dz', 'settle', 'kind')} for e in fx]}
    fixture = None
    if a.fixture_out:
        views = []
        for k, e in enumerate(fx):
            for v in e['views']:
                views.append('    fxv[fxv.size] = iwz_fxp_view( %d, %s, %g, %g, %s, %g );'
                             % (k, gsc_vec(v[:3]), v[3], v[4], gsc_vec([e['origin'][0], e['origin'][1], e['origin'][2] + e['region_dz']]), e['settle']))
        zv = []
        for z, vs in lay.get('views', {}).items():
            for v in vs[:1]:
                zv.append('    zv[zv.size] = iwz_fxp_view( -1, %s, %g, %g, ( 0, 0, 0 ), 0 );' % (gsc_vec(v[:3]), v[3], v[4]))
        fixture = open(os.path.join(HERE, 'fx_proof_fixture.gsc')).read().replace('//@FXVIEWS@', '\n'.join(views)).replace('//@ZONEVIEWS@', '\n'.join(zv))
    if a.dry_run:
        print(json.dumps(man, indent=1)[:4000]); return 0
    open(gp, 'w', newline='\n').write(g)
    if fixture:
        open(a.fixture_out, 'w', newline='\n').write(fixture)
    if a.manifest_out:
        json.dump(man, open(a.manifest_out, 'w'), indent=1)
    print('fx_place: %d FX (%d ids) -> %s%s' % (len(fx), len(ids), gp, (', fixture ' + a.fixture_out) if fixture else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
