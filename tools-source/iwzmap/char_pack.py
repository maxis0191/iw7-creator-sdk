"""Character pack: the zone source of stock player characters (body, head, arms) of other zones, for a mod zone.

The four guest characters of IW7 Zombies live each in one map zone (the DJ in cp_zmb, Kevin in cp_rave, Pam in
cp_disco, Elvira in cp_town). A server mod zone loads on every map, so a pack of their models in it makes each
character a player character on all five maps. This writes, in a fresh folder, the layout the Paris mod build
accepts (`zone_source/<zone>.csv` + `zonetool/<zone>/...`):
  - the models through kit_import.py (geometry, materials, image headers that stream from the base game's paks,
    physics assets, the techsets the shared techset zones lack, embedded from the techsets dumps). A material or physics
    asset that a shared zone defines (SHARED_ZONES) becomes a reference row. Every procedural bone set (shoulder twist
    helpers) is dropped from a patched copy of the model: ZoneTool handles that asset type, even as a reference, only in
    enemy packs, and one of a map zone could not be referenced anyway (the mod zone outlives the map); the report names
    each drop;
  - a string table `<table>` (default paris/characters_5_8.csv): `key,body,head,arms`, one row a character, an empty
    head for a full body: the server script reads it to know what the pack carries;
  - `require` rows for the shared techset zones (ZoneTool loads them while building; they are loaded on every map).

usage: char_pack.py <out dir> --dump <zone>=<dump>;<techsets dump> [--dump ...] [--characters characters_5_8.json]
       [--zone mod] [--runtime-dir <stock dumps with techsets_*/<zone>.csv>] [--dry-run]
Exit 1 when kit_import reports a missing file (its report: <out>/charpack-report.json).
"""
import argparse, csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_import  # noqa: E402

# Techset zones loaded on every zombies map (the usermap template requires the same, without its map's own).
SHARED_TECHSET_ZONES = ('techsets_common', 'techsets_global', 'techsets_common_core_mp', 'techsets_global_core_mp',
                        'techsets_common_mp', 'techsets_global_mp', 'techsets_common_cp', 'techsets_global_cp')
# Zones loaded before the mod zone on every zombies map and kept across maps (the maps reference their assets, e.g. the
# ragdoll physics asset and the male procedural bones of global_core_mp): their assets become references. A map zone
# never does: the mod zone outlives a map, so a reference into one would point at freed memory on the next map.
SHARED_ZONES = SHARED_TECHSET_ZONES + ('common', 'global_core_mp', 'global_cp', 'global', 'startup')


EXTRA_TYPES = 'proceduralbones,scriptable,vfx,particlesimanimation'


def shared_csvs(a):
    """The asset list of each shared zone: --runtime-dir first, then each --runtime-extra folder."""
    out = []
    for z in SHARED_ZONES:
        for d in [a.runtime_dir] + list(a.runtime_extra):
            p = os.path.join(d, z, z + '.csv')
            if os.path.isfile(p):
                out.append(p); break
    return out


def needs(chars, dumps, runtime_csvs):
    """Source zones whose character models name a procedural bone set or a scriptable that no shared zone defines: those
    zones need a dump of EXTRA_TYPES. Read from the models' .xmb asset tokens and the zone's own dump csv."""
    shared = set()
    for c in runtime_csvs:
        with open(c, errors='replace') as f:
            for ln in f:
                q = ln.strip().split(',')
                if len(q) == 2 and q[1]:
                    shared.add((q[0], q[1]))
    out = {}
    for ch in chars:
        zone = ch['zone']
        roots = dumps.get(zone, [])
        types = {}
        for r in roots:
            c = os.path.join(r, os.path.basename(os.path.normpath(r)) + '.csv')
            if os.path.isfile(c):
                with open(c, errors='replace') as f:
                    for ln in f:
                        q = ln.strip().split(',')
                        if len(q) == 2 and q[1]:
                            types.setdefault(q[1], set()).add(q[0])
        for part in ('body', 'head', 'arms'):
            if not ch.get(part):
                continue
            xm = next((os.path.join(r, 'xmodel', ch[part] + '.xmb') for r in roots
                       if os.path.isfile(os.path.join(r, 'xmodel', ch[part] + '.xmb'))), None)
            if not xm:
                continue
            with open(xm, 'rb') as f:
                data = f.read()
            for tok in re.findall(rb'\x07\x01([^\x00]+)\x00', data):
                n = tok.decode('ascii', 'replace')
                for t in ('proceduralbones', 'scriptable'):
                    if t in types.get(n, ()) and (t, n) not in shared:
                        out.setdefault(zone, set()).add('%s %s' % (t, n))
    return out


STARTUP_KINDS = ('material', 'techset', 'image')


def startup_query(a, missing):
    """A missing material, techset or image may be one of the zones the game loads at start and keeps for every map
    (common, techsets_common): no -dumpzone can list a loaded zone, so the pack asks ZoneTool itself
    (-assetsloaded, x64-zt). Writes <out>/startup-query.csv ("type,name") and returns 3 when every missing item is of
    such a kind; build-charpack.ps1 then runs the query, writes the loaded ones as the shared list 'startup' and builds
    the pack again. Any other missing item: 1."""
    rows = []
    for m in missing:
        kind, _, rest = m.partition(':')
        name = rest.split(' (')[0]
        if kind not in STARTUP_KINDS or not name:
            return 1
        rows.append('%s,%s' % (kind, name))
    if not rows:
        return 1
    with open(os.path.join(a.out, 'startup-query.csv'), 'w', newline='\n') as f:
        f.write('\n'.join(sorted(set(rows))) + '\n')
    print('character pack: %d names to ask ZoneTool about (startup-query.csv)' % len(set(rows)))
    return 3


def scriptable_effects(a, rep, runtime, report):
    """The effects a kept scriptable plays (Pam's body: pam_grier, its teleport effect) come in through fx_import.py in
    its mod-zone mode, with their materials, images and techsets. Names of a scriptable that are no dumped asset (sound
    aliases, part and state names, bones) are listed in the report: a sound alias resolves from the sound banks the
    map loads, not from this zone."""
    sys.path.insert(0, os.path.join(HERE, 'fx'))
    import fx_import  # noqa: E402
    roots = {}
    for d in a.dump:
        z, r = d.split('=', 1)
        roots.setdefault(z, []).extend(x for x in r.split(';') if x)
    fx, other = [], {}
    for name, info in rep.get('models', {}).items():
        zone = info.get('zone')
        for rel in info.get('scriptable', []):
            path = next((os.path.join(r, rel) for r in roots.get(zone, []) if os.path.isfile(os.path.join(r, rel))), None)
            if not path:
                continue
            for s in sorted(set(kit_import.strings_of(path, 4))):
                stem = s[:-4] if s.endswith('.vfx') else s
                if any(os.path.isfile(os.path.join(r, 'particlesystem', stem + '.iw7VFX')) for r in roots.get(zone, [])):
                    if '%s:%s' % (zone, stem) not in fx:
                        fx.append('%s:%s' % (zone, stem))
                elif not s.endswith('.vfx'):
                    other.setdefault(rel.replace(os.sep, '/'), []).append(s)
    rep['scriptableNames'] = other
    rc = 0
    if fx:
        fx_report = os.path.join(a.out, 'fx-report.json')
        args = [a.out, a.zone, '--fx', ','.join(fx), '--no-ncs', '--share-runtime', '--report', fx_report] + runtime
        for d in a.dump:
            args += ['--dump', d]
        rc = fx_import.main(args)
        with open(fx_report) as f:
            rep['scriptableFx'] = json.load(f)
    else:
        rep['scriptableFx'] = None
    with open(report, 'w') as f:
        json.dump(rep, f, indent=1)
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--dump', action='append', default=[],
                    help='<zone>=<dump root>[;<techsets dump root>][;<patch zone dump root>]')
    ap.add_argument('--characters', default=os.path.join(HERE, 'characters_5_8.json'))
    ap.add_argument('--zone', default='mod')
    ap.add_argument('--runtime-dir', default=os.environ.get('IWZ_TEMPLATE_DUMP') or os.path.join(
        os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime'), 'iwz-map-ref-a', 'dump'))
    ap.add_argument('--runtime-extra', action='append', default=[],
                    help='another folder of <zone>/<zone>.csv lists of shared zones (build-charpack.ps1 dumps the lists of '
                         'common and techsets_common there: effect materials and images live in them)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--needs', action='store_true',
                    help='print "<zone> <types>" for each source zone that needs a dump of ' + EXTRA_TYPES + ', then stop')
    a = ap.parse_args(argv)
    if a.needs:
        with open(a.characters) as f:
            chars = json.load(f)['characters']
        roots = {}
        for d in a.dump:
            z, r = d.split('=', 1)
            roots.setdefault(z, []).extend(x for x in r.split(';') if x)
        csvs = shared_csvs(a)
        for zone, why in sorted(needs(chars, roots, csvs).items()):
            print('%s %s  # %s' % (zone, EXTRA_TYPES, '; '.join(sorted(why))))
        return 0

    with open(a.characters) as f:
        spec = json.load(f)
    table = spec['table']
    chars = spec['characters']
    models = []
    for c in chars:
        for part in ('body', 'head', 'arms'):
            if c.get(part):
                models.append('%s:%s' % (c['zone'], c[part]))

    if os.path.exists(os.path.join(a.out, 'zone_source', a.zone + '.csv')):
        sys.exit('not a fresh pack folder: ' + a.out)
    os.makedirs(os.path.join(a.out, 'zone_source'), exist_ok=True)
    os.makedirs(os.path.join(a.out, 'zonetool', a.zone), exist_ok=True)
    csvp = os.path.join(a.out, 'zone_source', a.zone + '.csv')
    with open(csvp, 'w', newline='\n') as f:
        f.write(''.join('require,%s\n' % z for z in SHARED_TECHSET_ZONES))

    runtime = []
    for p in shared_csvs(a):
        runtime += ['--runtime-csv', p]
    if not runtime:
        sys.exit('no shared zone csv under ' + a.runtime_dir)

    report = os.path.join(a.out, 'charpack-report.json')
    # The bodies are whole: procedural bones (x64-zt handles them in any zone since claude/procbones-any-zone) and the
    # scriptable a playable body names (Pam's) are kept, with the dependencies the dumps hold.
    args = [a.out, a.zone, '--models', ','.join(models), '--share-runtime', '--keep-scriptable',
            '--report', report] + runtime
    for d in a.dump:
        args += ['--dump', d]
    if a.dry_run:
        args.append('--dry-run')
    rc = kit_import.main(args)
    with open(report) as f:
        rep = json.load(f)

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['key', 'body', 'head', 'arms'])
    for c in chars:
        w.writerow([c['key'], c['body'], c.get('head') or '', c['arms']])
    rep['table'] = {'name': table, 'rows': len(chars)}
    rep['characters'] = [{'key': c['key'], 'zone': c['zone'],
                          'models': {p: (c[p], 'in pack' if c[p] in rep.get('rows', []) or ('xmodel,' + c[p]) in rep.get('rows', [])
                                         else 'missing') for p in ('body', 'head', 'arms') if c.get(p)}} for c in chars]
    with open(report, 'w') as f:
        json.dump(rep, f, indent=1)
    if rc or a.dry_run:
        return startup_query(a, rep.get('missing', [])) if rc else rc
    rc = scriptable_effects(a, rep, runtime, report)
    if rc:
        return startup_query(a, (rep.get('scriptableFx') or {}).get('missing', []))
    tp = os.path.join(a.out, 'zonetool', a.zone, *table.split('/'))
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    open(tp, 'w', newline='\n').write(buf.getvalue())
    with open(csvp, 'a', newline='\n') as f:
        f.write('stringtable,%s\n' % table)
    with open(csvp) as f:
        n = sum(1 for _ in f)
    print('character pack: %d characters, %d models, zone source %s (%d rows), table %s'
          % (len(chars), len(models), csvp, n, table))
    return 0


if __name__ == '__main__':
    sys.exit(main())
