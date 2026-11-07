"""Import stock IW7 xmodels from other zones (cp_disco, cp_final, ...) into an assembled usermap zone.

Run after assemble.py / sz2_assemble.py and before `-buildzone`. For each model it links (hardlinks, never modifies)
from per-zone dumps into zonetool/<map>/:
  xmodel/<name>.xmb (+ its <name>_lod*.hkx physics LOD data), the xsurface files, physicsasset / physicsfxshape files,
  and for every material the zone does not already carry: materials/<m>.json, its techset state and constant buffer
  files (techsets/state/<techset>/<m>.*, techsets/constantbuffer/<techset>/<m>.*) and the image headers
  (images/<img>.iw7Image; the pixels stay in the base game's imagefile*.pak and stream from there).
It then adds `xmodel,<name>` rows before the world rows of zone_source/<map>.csv (ZoneTool pulls materials, surfaces,
images and techsets as dependencies).

Techsets: a material's techset that the template zone csv already names is shared (provided at runtime). Another one
is embedded from disk: techsets/<t>.techset, its techsets/<technique>.technique files, vertex declarations
(techsets/<decl>.vertexdecl) and shader bytecode (techsets/{vs,ps,hs,ds}/<hash>.cso) from a dump of techsets_<zone>
(`zonetool -dumpzone techsets_<zone>`). A shader (or techset) that a runtime techset zone already defines
(--runtime-csv: dump csvs of the zones the template map loads, e.g. techsets_cp_zmb.csv, techsets_global_core_mp.csv)
gets a `<type>,,<name>` reference row instead of a second copy. Loading techsets_cp_disco + techsets_cp_final with
`require` next to the template's nine techset zones hung ZoneTool (2026-11-07), so `require` is only the fallback for a
techset with no dump (--allow-require).

Dumps: one root per source zone made by the kit-import ZoneTool (x64-zt codex/iwzmap-kit-import):
  zonetool -dumpzonetypes <zone> xmodel,xmodelsurfs,material,image,physicsasset,physicsfxshape
That command now also writes the zone's materials (a map zone only references them; their definitions are in
techsets_<zone>, which it loads first).

A material, image or techset already present in the zone csv (full or `,name` reference) is shared: the template map's
zones provide it at runtime and nothing is linked for it.

usage: kit_import.py <work dir> <map> --dump <zone>=<dump root>[;<root>...] [--dump ...] (--models a,b,c | --kit kit_final.json
       [--tier core] [--zones cp_disco,cp_final]) [--runtime-csv <csv> ...] [--allow-require] [--report report.json]
       [--dry-run]
       dump roots of a zone: the -dumpzonetypes dump of <zone> and the -dumpzone dump of techsets_<zone>
Exit 1 when a model, surface, material, state file or image is missing (nothing is written to the csv then).
"""
import argparse, json, os, re, sys

WORLD_FIRST = 'com_map,'
HEX16 = re.compile(r'^[0-9a-f]{16}$')
BADPATH = set(':*?"<>|\\')                     # strings of the .xmb that cannot be asset file names


def strings_of(path, minlen=3):
    data = open(path, 'rb').read()
    return [m.decode('ascii') for m in re.findall(rb'[\x20-\x7e]{%d,}' % minlen, data)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('work'); ap.add_argument('map')
    ap.add_argument('--dump', action='append', default=[], help='<zone>=<dump root of that zone>')
    ap.add_argument('--models', default='')
    ap.add_argument('--kit', default='')
    ap.add_argument('--tier', default='')
    ap.add_argument('--zones', default='')
    ap.add_argument('--report', default='')
    ap.add_argument('--runtime-csv', action='append', default=[], help='dump csv of a zone loaded at runtime (shared techsets/shaders)')
    ap.add_argument('--allow-require', action='store_true', help='techset without a dump: require,techsets_<zone> (ZoneTool loads it)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)

    dumps = {}                                  # zone -> [dump roots], searched in order
    for d in a.dump:
        z, roots = d.split('=', 1)
        dumps.setdefault(z, []).extend(r for r in roots.split(';') if r)

    def find(zone, rel):
        for r in dumps.get(zone or '', []):
            p = os.path.join(r, rel)
            if os.path.isfile(p):
                return p
        return None

    listing = {}

    def find_all(zone, sub, stem):
        """files <sub>/<stem> and <sub>/<stem>.<ext> of the first root that has any"""
        for r in dumps.get(zone or '', []):
            d = os.path.join(r, sub, os.path.dirname(stem))
            if d not in listing:
                listing[d] = os.listdir(d) if os.path.isdir(d) else []
            b = os.path.basename(stem)
            hit = [f for f in listing[d] if f == b or f.startswith(b + '.')]
            if hit:
                return [(os.path.join(d, f), os.path.join(sub, os.path.dirname(stem), f)) for f in hit]
        return []

    dst =os.path.join(a.work, 'zonetool', a.map)
    csvp = os.path.join(a.work, 'zone_source', a.map + '.csv')
    lines = open(csvp).read().splitlines()
    have = {}                                   # (type, name) -> 'full' | 'ref'
    for ln in lines:
        q = ln.split(',')
        if len(q) == 2 and q[1]:
            have.setdefault((q[0], q[1]), 'full')
        elif len(q) == 3 and q[1] == '' and q[2]:
            have.setdefault((q[0], q[2]), 'ref')

    runtime = set()                             # (type, name) defined by a zone loaded at runtime
    for c in a.runtime_csv:
        for ln in open(c, errors='replace'):
            q = ln.strip().split(',')
            if len(q) == 2 and q[1]:
                runtime.add((q[0], q[1]))
    ref_rows = []

    def ref(t, n):
        if (t, n) not in have:
            have[(t, n)] = 'ref'; ref_rows.append('%s,,%s' % (t, n))

    SHADERS = (('vs', 'vertexshader'), ('ps', 'pixelshader'), ('hs', 'hullshader'), ('ds', 'domainshader'))

    def embed_techset(zone, tech):
        """link techset + techniques + vertex decls + shaders from the techsets dump; False when not on disk"""
        tp = find(zone, os.path.join('techsets', tech + '.techset'))
        if not tp:
            return False
        add(tp, os.path.join('techsets', tech + '.techset'))
        info = {'zone': zone, 'techniques': 0, 'shaders': 0, 'sharedShaders': 0, 'decls': 0}
        for t in set(strings_of(tp)):
            tq = find(zone, os.path.join('techsets', t + '.technique')) if not set(t) & BADPATH else None
            if not tq:
                continue
            add(tq, os.path.join('techsets', t + '.technique')); info['techniques'] += 1
            for x in set(strings_of(tq)):
                if set(x) & BADPATH:
                    continue
                vd = find(zone, os.path.join('techsets', x + '.vertexdecl'))
                if vd:
                    add(vd, os.path.join('techsets', x + '.vertexdecl')); info['decls'] += 1
                if not HEX16.match(x):
                    continue
                for ab, ty in SHADERS:
                    if (ty, x) in runtime or (ty, x) in have:
                        ref(ty, x); info['sharedShaders'] += 1; break
                    sp = find(zone, os.path.join('techsets', ab, x + '.cso'))
                    if sp:
                        add(sp, os.path.join('techsets', ab, x + '.cso')); info['shaders'] += 1; break
                else:
                    # in a runtime zone without a dump csv (techsets_common): ZoneTool takes the loaded copy
                    info.setdefault('unresolvedShaders', []).append(x)
        rep['techsets']['embedded'][tech] = info
        return True

    # model list: name -> zone
    models = {}
    if a.kit:
        zones = set(z for z in a.zones.split(',') if z)
        for m in json.load(open(a.kit))['models']:
            z = m.get('source') or m.get('zone')
            if (not zones or z in zones) and (not a.tier or m.get('tier') == a.tier):
                models[m['name']] = z
    for n in [n for n in a.models.split(',') if n]:
        if ':' in n:
            z, n = n.split(':', 1); models[n] = z
        elif n not in models:
            hit = [z for z in dumps if find(z, os.path.join('xmodel', n + '.xmb'))]
            models[n] = hit[0] if hit else None

    plan = []                                   # (src, dst) links
    missing, rows, req_zones = [], [], set()
    rep = {'models': {}, 'materials': {'new': [], 'shared': []}, 'images': {'new': 0, 'shared': 0, 'bytes': 0},
           'techsets': {'embedded': {}, 'required': {}, 'shared': []}, 'linkedBytes': 0, 'surfaceBytes': 0}
    seen_mat, seen_img = set(), set()

    def add(src, rel):
        plan.append((src, os.path.join(dst, rel)))

    for name, zone in sorted(models.items()):
        if not dumps.get(zone or ''):
            missing.append('zone dump for %s (%s)' % (name, zone)); continue
        if ('xmodel', name) in have:
            rep['models'][name] = {'zone': zone, 'status': 'already in zone (%s)' % have[('xmodel', name)]}
            continue
        xm = find(zone, os.path.join('xmodel', name + '.xmb'))
        if not xm:
            missing.append('xmodel:' + name); continue
        info = {'zone': zone, 'surfaces': [], 'materials': [], 'physics': []}
        xdir = os.path.dirname(xm)
        for f in os.listdir(xdir):
            if f == name + '.xmb' or (f.startswith(name + '_lod') and f.endswith('.hkx')):
                add(os.path.join(xdir, f), os.path.join('xmodel', f))
        strs = set(strings_of(xm))
        for s in sorted(strs):
            xs = find(zone, os.path.join('xsurface', s + '.xsb'))
            if xs:
                add(xs, os.path.join('xsurface', s + '.xsb')); info['surfaces'].append(s)
                rep['surfaceBytes'] += os.path.getsize(xs)
            for sub in ('physicsasset', 'physicsfxshape', 'proceduralbones'):
                for pp, rel in (find_all(zone, sub, s) if s and not set(s) & BADPATH else []):
                    add(pp, rel); info['physics'].append(rel.replace(os.sep, '/'))
            if find(zone, os.path.join('materials', s + '.json')):
                info['materials'].append(s)
        if not info['surfaces']:
            missing.append('xsurface:' + name)
        for mat in info['materials']:
            if mat in seen_mat:
                continue
            seen_mat.add(mat)
            if ('material', mat) in have:
                rep['materials']['shared'].append(mat); continue
            mj = find(zone, os.path.join('materials', mat + '.json'))
            md = json.load(open(mj))
            add(mj, os.path.join('materials', mat + '.json'))
            rep['materials']['new'].append(mat)
            tech = md.get('techniqueSet->name') or ''
            if tech:
                for sub, exts, need in (('state', ('.stateinfo', '.statebits', '.statebitsmap'), ('.statebits', '.statebitsmap')),
                                        ('constantbuffer', ('.cbi', '.cbt'), ())):
                    for ext in exts:
                        p = find(zone, os.path.join('techsets', sub, tech, mat + ext))
                        if p:
                            add(p, os.path.join('techsets', sub, tech, mat + ext))
                        elif ext in need or (sub == 'constantbuffer' and md.get('constantTable')):
                            missing.append('%s %s/%s%s' % (sub, tech, mat, ext))
                if ('techset', tech) in have or ('techset', tech) in runtime:
                    ref('techset', tech)
                    if tech not in rep['techsets']['shared']:
                        rep['techsets']['shared'].append(tech)
                elif tech not in rep['techsets']['embedded'] and tech not in rep['techsets']['required']:
                    if not embed_techset(zone, tech):
                        if a.allow_require:
                            rep['techsets']['required'][tech] = zone; req_zones.add(zone)
                        else:
                            missing.append('techset:%s (no techsets_%s dump)' % (tech, zone))
            for t in md.get('textureTable', []):
                img = t.get('image')
                if not img or img in seen_img:
                    continue
                seen_img.add(img)
                if ('image', img) in have:
                    rep['images']['shared'] += 1; continue
                ip = find(zone, os.path.join('images', img + '.iw7Image'))
                if not ip:
                    missing.append('image:' + img); continue
                add(ip, os.path.join('images', img + '.iw7Image'))
                rep['images']['new'] += 1; rep['images']['bytes'] += os.path.getsize(ip)
        rep['models'][name] = info
        rows.append('xmodel,' + name)

    rep['missing'] = missing
    rep['rows'] = rows
    rep['refRows'] = ref_rows
    rep['require'] = ['techsets_' + z for z in sorted(req_zones)]
    linked = 0
    if not missing and not a.dry_run:
        for src, d in plan:
            if os.path.exists(d):
                continue                       # stock file of the same name already there: keep it
            os.makedirs(os.path.dirname(d), exist_ok=True)
            os.link(src, d); linked += 1
            rep['linkedBytes'] += os.path.getsize(src)
        req = [r for r in ('require,' + z for z in rep['require']) if r not in lines]
        last_req = max([i for i, l in enumerate(lines) if l.startswith('require,')], default=0)
        lines[last_req + 1:last_req + 1] = req
        at = next(i for i, l in enumerate(lines) if l.startswith(WORLD_FIRST))
        lines[at:at] = [r for r in ref_rows + rows if r not in lines]
        open(csvp, 'w', newline='\n').write('\n'.join(lines) + '\n')
    rep['linked'] = linked
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1)
    print('kit import: %d models, %d new materials (%d shared), %d new image headers (%d shared), '
          '%d techsets embedded %s, %d shared, surfaces %.1f MB, linked %d files; missing %s'
          % (len(rows), len(rep['materials']['new']), len(rep['materials']['shared']), rep['images']['new'],
             rep['images']['shared'], len(rep['techsets']['embedded']), rep['require'], len(rep['techsets']['shared']),
             rep['surfaceBytes'] / 1e6, linked, missing[:12]))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
