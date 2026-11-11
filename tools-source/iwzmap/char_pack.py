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
import argparse, csv, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_import  # noqa: E402

# Techset zones loaded on every zombies map (the usermap template requires the same, without its map's own).
SHARED_TECHSET_ZONES = ('techsets_common', 'techsets_global', 'techsets_common_core_mp', 'techsets_global_core_mp',
                        'techsets_common_mp', 'techsets_global_mp', 'techsets_common_cp', 'techsets_global_cp')
# Zones loaded before the mod zone on every zombies map and kept across maps (the maps reference their assets, e.g. the
# ragdoll physics asset and the male procedural bones of global_core_mp): their assets become references. A map zone
# never does: the mod zone outlives a map, so a reference into one would point at freed memory on the next map.
SHARED_ZONES = SHARED_TECHSET_ZONES + ('global_core_mp', 'global_cp', 'global')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--dump', action='append', default=[],
                    help='<zone>=<dump root>[;<techsets dump root>][;<patch zone dump root>]')
    ap.add_argument('--characters', default=os.path.join(HERE, 'characters_5_8.json'))
    ap.add_argument('--zone', default='mod')
    ap.add_argument('--runtime-dir', default=os.environ.get('IWZ_TEMPLATE_DUMP') or os.path.join(
        os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime'), 'iwz-map-ref-a', 'dump'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)

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
    for z in SHARED_ZONES:
        p = os.path.join(a.runtime_dir, z, z + '.csv')
        if os.path.isfile(p):
            runtime += ['--runtime-csv', p]
    if not runtime:
        sys.exit('no shared zone csv under ' + a.runtime_dir)

    report = os.path.join(a.out, 'charpack-report.json')
    args = [a.out, a.zone, '--models', ','.join(models), '--share-runtime', '--drop-procedural-bones',
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
        return rc
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
