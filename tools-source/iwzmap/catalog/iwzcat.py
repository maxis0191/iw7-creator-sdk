"""IW7 asset catalog: one JSON row per XModel found in ZoneTool dumps.

usage:
  python -I iwzcat.py build  --zone cp_disco=<dump dir>[;<dump dir>...] [--zone ...] --out catalog.json
                             [--base-paks <game dir>] [--always-loaded cp_zmb,common_cp]
  python -I iwzcat.py query  catalog.json [--category pipe] [--name subway] [--zone cp_disco] [--max-radius 200]
  python -I iwzcat.py fx     --zone cp_disco=<dump dir> ...  (vfx names listed in the dump csv, with a category)
  python -I iwzcat.py previewlist catalog.json names.txt     (entries for iwzmap_preview.gsc / Run-Preview.ps1)

A dump dir is what `zonetool -dumpzonetypes <zone> xmodel,xmodelsurfs,material,image` writes
(xmodel/*.xmb, xsurface/*.xsb, materials/**/*.json, images/*.iw7Image, <zone>.csv). Several dirs may be given
for one zone (e.g. an old full dump plus a later material-only dump); the first one holding a file wins.

Per row: name, zones, header bounds and size, LOD0 vertex bounds and the max difference to the header,
per-LOD surfaces/verts/tris/materials, techsets and images of the materials, physics/collision presence,
category guess, and a size estimate for embedding the model in another zone (surfaces + embedded image
pixels; streamed image bytes are listed per imagefile pak, which the base game ships).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ztdump  # noqa: E402

SCHEMA = 'iwz.asset-catalog/1'

# ordered: first match wins; patterns are matched against "_"-delimited name tokens and substrings
CATEGORIES = [
    ('vfx_model', r'^vfx_|_vfx_|^fx_'),
    ('character', r'^body_|^head_|^fullbody|^viewhands|^viewmodel|zombie_body|_hair_|^c_|^zmb_.*(body|head)_'),
    ('weapon', r'^weapon_|^wpn_|^vm_|^wm_'),
    ('vehicle', r'^veh_|^vehicle_|_car_body|station_wagon|_truck|_bus_'),
    ('train', r'subway_car|subway_train|train|_tram|railcar|locomotive'),
    ('track', r'_rail_|_rails|railroad|_track_|tracks|rail_tie'),
    ('turnstile', r'turnstyle|turnstile|ticket_gate'),
    ('ticket', r'ticket|booth|token_'),
    ('sign', r'sign|poster|billboard|banner|placard|decal_|graffiti|_logo'),
    ('light', r'light|lamp|lantern|bulb|neon|fluorescent|_flare'),
    ('pipe', r'pipe|conduit|_duct|ducting|plumbing|valve'),
    ('cable', r'cable|wire|_cord|hose'),
    ('generator', r'generator|transformer|power_box|breaker|fusebox|fuse_box|electrical_box|elec_box|junction_box|_panel_box'),
    ('vent', r'vent|_fan_|exhaust|ac_unit|hvac'),
    ('stairs', r'stair|_steps|ladder|escalator'),
    ('door', r'door|gate|shutter|hatch'),
    ('window', r'window|glass'),
    ('column', r'column|pillar|_post|beam|girder|support|_strut'),
    ('arch', r'arch'),
    ('trim', r'trim|molding|moulding|_edge|_curb|_ledge|_cap_|baseboard|railing|handrail|_rail'),
    ('wall', r'wall|facade|partition|_tile|brick|panel'),
    ('floor', r'floor|ground|_slab|grate|_platform'),
    ('ceiling', r'ceiling|roof'),
    ('bench', r'bench|seat|chair|stool|couch|sofa'),
    ('table', r'table|desk|counter'),
    ('storage', r'locker|cabinet|shelf|shelves|rack|drawer'),
    ('trash', r'trash|garbage|debris|rubble|junk|paper|newspaper|litter|bag_|_bag|bottle|cup_'),
    ('container', r'crate|box|barrel|drum|bin_|_bin|bucket|can_|_can|container|pallet|tank'),
    ('barrier', r'barrier|barricade|fence|cone|sandbag|blockade|board'),
    ('machine', r'machine|vending|console|computer|monitor|_tv|television|arcade|jukebox|phone'),
    ('foliage', r'tree|bush|foliage|plant|grass|ivy|leaf|leaves|weed'),
    ('rock', r'rock|cliff|boulder|stone'),
]
CAT_RE = [(c, re.compile(p)) for c, p in CATEGORIES]


def guess_category(name):
    n = name.lower().replace('/', '_')
    for c, rx in CAT_RE:
        if rx.search(n):
            return c
    return 'prop'


def _first(dirs, *rel):
    for d in dirs:
        p = os.path.join(d, *rel)
        if os.path.exists(p):
            return p
    return None


class Zone:
    def __init__(self, name, dirs):
        self.name = name
        self.dirs = dirs
        self._mat = {}
        self._img = {}
        self._surf = {}

    def xmodels(self):
        seen = set()
        for d in self.dirs:
            x = os.path.join(d, 'xmodel')
            if not os.path.isdir(x):
                continue
            for root, _, files in os.walk(x):
                for f in files:
                    if f.endswith('.xmb'):
                        rel = os.path.relpath(os.path.join(root, f), x)
                        if rel not in seen:
                            seen.add(rel)
                            yield os.path.join(root, f)

    def surfs(self, name):
        if name not in self._surf:
            p = _first(self.dirs, 'xsurface', name + '.xsb')
            try:
                self._surf[name] = ztdump.read_xsurfs(p) if p else None
            except ztdump.DumpError as e:
                self._surf[name] = {'error': str(e)}
        return self._surf[name]

    def material(self, name):
        if name not in self._mat:
            p = _first(self.dirs, 'materials', *(name.replace('*', '_') + '.json').split('/'))
            self._mat[name] = ztdump.read_material(p) if p else None
        return self._mat[name]

    def image(self, name):
        if name not in self._img:
            p = _first(self.dirs, 'images', name.replace('*', '_') + '.iw7Image')
            try:
                self._img[name] = ztdump.read_image(p) if p else None
            except ztdump.DumpError as e:
                self._img[name] = {'error': str(e)}
        return self._img[name]

    def csv_names(self, asset_type):
        p = _first(self.dirs, self.name + '.csv')
        out = []
        if p:
            for line in open(p, encoding='latin-1'):
                t, _, n = line.strip().partition(',')
                if t == asset_type and n:
                    out.append(n)
        return out


def model_row(zone, path, pak_present):
    m = ztdump.read_xmodel(path)
    row = {
        'name': m['name'], 'zone': zone.name, 'category': guess_category(m['name']),
        'bounds': m['bounds'],
        'size': [round(m['bounds']['maxs'][i] - m['bounds']['mins'][i], 2) for i in range(3)],
        'radius': m['radius'], 'numLods': m['numLods'], 'numBones': m['numBones'],
        'animatedOrSkinned': m['numBones'] > 1,
        'contents': m['contents'],
        'collision': {'collSurfs': m['numCollSurfs'], 'physicsAsset': m['physicsAsset'],
                      'havokLodData': m['physicsLODDataSize'], 'havokFile': m['havokFile']},
        'lods': [],
    }
    mats = set()
    surf_bytes = 0
    for i, lod in enumerate(m['lods']):
        entry = {'lod': i, 'dist': lod['dist'], 'surfs': lod['surfs'], 'materials': lod['materials']}
        mats.update(x for x in lod['materials'] if x)
        s = zone.surfs(lod['surfs']) if lod['surfs'] else None
        if s and 'error' not in s:
            entry.update({'verts': s['verts'], 'tris': s['tris'], 'surfaces': s['numsurfs']})
            surf_bytes += s['bytes']
            if i == 0 and 'vertBounds' in s:
                vb = s['vertBounds']
                row['vertBounds'] = vb
                row['boundsMaxDiff'] = round(max(max(abs(vb['mins'][k] - m['bounds']['mins'][k]),
                                                     abs(vb['maxs'][k] - m['bounds']['maxs'][k])) for k in range(3)), 3)
                row['lightmapCoords'] = any(x['lightmapCoords'] for x in s['surfaces'])
        elif s:
            entry['error'] = s['error']
        else:
            entry['missing'] = True
        row['lods'].append(entry)
    row['materials'] = []
    images = {}
    for mn in sorted(mats):
        md = zone.material(mn)
        if md is None:
            row['materials'].append({'name': mn, 'missing': True})
            continue
        row['materials'].append({'name': mn, 'techset': md['techset'],
                                 'images': [t['image'] for t in md['images']]})
        for t in md['images']:
            if t['image'] and not t['image'].startswith('$'):
                images[t['image']] = zone.image(t['image'])
    embedded = 0
    streamed = {}
    missing_images = []
    for n, im in images.items():
        if not im or 'error' in im:
            missing_images.append(n)
            continue
        embedded += im['embeddedBytes']
        for s in im['streams']:
            k = 'imagefile%d.pak' % s['fileIndex']
            streamed[k] = streamed.get(k, 0) + s['bytes']
    row['images'] = sorted(images)
    row['cost'] = {
        'surfaceBytes': surf_bytes,
        'embeddedImageBytes': embedded,
        'streamedImageBytes': streamed,
        'streamPaksInBaseGame': {k: pak_present(k) for k in streamed},
        'missingImages': missing_images,
    }
    techs = sorted({x.get('techset') for x in row['materials'] if x.get('techset')})
    row['techsets'] = techs
    row['emissive'] = any(re.search(r'emissive|_em_|glow|_e\d', t or '') for t in techs) or \
        any(re.search(r'_em$|_emissive|_glow', i) for i in row['images'])
    return row


def build(args):
    zones = []
    for z in args.zone:
        name, _, dirs = z.partition('=')
        zones.append(Zone(name, [d for d in dirs.split(';') if d]))
    base = args.base_paks
    present = {}

    def pak_present(fname):
        if base is None:
            return None
        if fname not in present:
            present[fname] = os.path.exists(os.path.join(base, fname))
        return present[fname]

    always = set(x for x in (args.always_loaded or '').split(',') if x)
    rows = {}
    errors = []
    for z in zones:
        for p in z.xmodels():
            try:
                r = model_row(z, p, pak_present)
            except Exception as e:  # keep going: report the file
                errors.append({'zone': z.name, 'file': p, 'error': '%s: %s' % (type(e).__name__, e)})
                continue
            prev = rows.get(r['name'])
            if prev:
                prev['zones'].append(z.name)
                continue
            r['zones'] = [z.name]
            rows[r['name']] = r
    for r in rows.values():
        r['inAlwaysLoadedOrTemplate'] = bool(always.intersection(r['zones']))
        del r['zone']
    out = {'schema': SCHEMA, 'zones': [{'name': z.name, 'dirs': z.dirs} for z in zones],
           'count': len(rows), 'errors': errors, 'models': sorted(rows.values(), key=lambda r: r['name'])}
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=1)
    print('catalog: %d models, %d errors -> %s' % (len(rows), len(errors), args.out))


def query(args):
    cat = json.load(open(args.catalog))
    n = 0
    for r in cat['models']:
        if args.category and r['category'] != args.category:
            continue
        if args.name and not re.search(args.name, r['name']):
            continue
        if args.zone and args.zone not in r['zones']:
            continue
        if args.max_radius and r['radius'] > args.max_radius:
            continue
        n += 1
        l0 = r['lods'][0] if r['lods'] else {}
        print('%-60s %-10s %-28s size=%s tris0=%s' % (r['name'], r['category'], ','.join(r['zones']),
                                                     r['size'], l0.get('tris')))
    print('%d rows' % n)


FX_CATEGORIES = [('fire', r'fire|flame|burn|ember'), ('smoke', r'smoke|steam|vapor|fog|mist|haze'),
                 ('dust', r'dust|debris|dirt|particulate|motes'), ('sparks', r'spark|electric|elec|zap|arc'),
                 ('water', r'water|drip|leak|splash|rain|puddle'), ('light', r'light|glow|flare|godray|lens'),
                 ('blood', r'blood|gore'), ('impact', r'impact|hit_')]


def fx(args):
    for z in args.zone:
        name, _, dirs = z.partition('=')
        zone = Zone(name, [d for d in dirs.split(';') if d])
        names = zone.csv_names('vfx')
        for n in names:
            cat = next((c for c, p in FX_CATEGORIES if re.search(p, n)), 'other')
            if args.category and cat != args.category:
                continue
            print('%s\t%s\t%s' % (name, cat, n))


def previewlist(args):
    """Booth entries "model:midx:midy:midz:radius" (bounds centre in model space, half diagonal)."""
    cat = {r['name']: r for r in json.load(open(args.catalog))['models']}
    for n in open(args.names).read().split():
        r = cat[n]
        lo, hi = r['bounds']['mins'], r['bounds']['maxs']
        mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
        rad = max(1.0, sum((hi[i] - lo[i]) ** 2 for i in range(3)) ** 0.5 / 2)
        print('%s:%.2f:%.2f:%.2f:%.2f' % (n, mid[0], mid[1], mid[2], rad))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('build')
    b.add_argument('--zone', action='append', required=True)
    b.add_argument('--out', required=True)
    b.add_argument('--base-paks')
    b.add_argument('--always-loaded')
    q = sp.add_parser('query')
    q.add_argument('catalog')
    q.add_argument('--category')
    q.add_argument('--name')
    q.add_argument('--zone')
    q.add_argument('--max-radius', type=float)
    f = sp.add_parser('fx')
    f.add_argument('--zone', action='append', required=True)
    f.add_argument('--category')
    p = sp.add_parser('previewlist')
    p.add_argument('catalog')
    p.add_argument('names')
    a = ap.parse_args(argv)
    {'build': build, 'query': query, 'fx': fx, 'previewlist': previewlist}[a.cmd](a)


if __name__ == '__main__':
    main()
