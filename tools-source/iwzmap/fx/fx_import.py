"""Import stock IW7 effects (vfx) from other zones (cp_disco, cp_final, ...) into an assembled usermap zone, and make
them registrable at runtime.

Run after assemble.py / sz2_assemble.py (and kit_import.py), before `-buildzone`. Two things are needed for a foreign
effect to play in the usermap:
  1. the ParticleSystemDef and everything it references must be in the FF: the effect itself, its child effects
     (spawn-on-death / runner / impact children, named inside the .iw7VFX), materials (definition json, techset
     state + constant buffer files, the techset itself when the template's runtime techset zones do not define it),
     image headers, models, particle sim animations;
  2. its name must be in the level NetConstStrings effect list (`netconststrings/ncs_efx_level.json`, string type 5):
     IW7 resolves loadfx / playfx / spawnfx effects through that list, so a name outside it cannot be registered.
This tool links (hardlinks, never modifies) the dump files into zonetool/<map>/, writes a NEW ncs_efx_level.json (the
assembled one is a hardlink into the stock dump: it is removed first, never written through) with the imported names
appended, adds `vfx,<name>` rows before the world rows of zone_source/<map>.csv, and writes the merged list to
--ncs-out for fx_place.py --ncs.

Dumps: the -dumpzonetypes dump of the source zone with the vfx types (x64-zt codex/iwzmap-kit-import or later):
  zonetool -dumpzonetypes cp_disco vfx,particlesimanimation,netconststrings
plus the kit-import dumps of the same zone for materials / images / models / techsets
  (zonetool -dumpzonetypes cp_disco xmodel,xmodelsurfs,material,image,physicsasset,physicsfxshape; -dumpzone techsets_cp_disco)

usage: fx_import.py <work dir> <map> --dump <zone>=<root>[;<root>...] --fx <zone>:<vfx path>[,...]
       [--runtime-csv <csv> ...] [--ncs-out <json>] [--report <json>] [--dry-run]
Models referenced by an effect (debris chunks) are not linked here: --dry-run lists them as kitModels
('<zone>:<model>'); add them to kit_import.py's model list (build-sz2.ps1 -KitModels), which runs first.
Exit 1 when something referenced is missing (nothing is written then).
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit_import import strings_of, HEX16, BADPATH      # noqa: E402  (same dump-string conventions)

WORLD_FIRST = 'com_map,'
NCS = os.path.join('netconststrings', 'ncs_efx_level.json')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('work'); ap.add_argument('map')
    ap.add_argument('--dump', action='append', default=[])
    ap.add_argument('--fx', action='append', default=[], help='<zone>:<vfx path> (comma separated list allowed)')
    ap.add_argument('--runtime-csv', action='append', default=[])
    ap.add_argument('--ncs-out', default='')
    ap.add_argument('--ncs-skip', default='', help='comma list of imported effects NOT appended to the level list (experiment: is the list needed)')
    ap.add_argument('--report', default='')
    ap.add_argument('--no-ncs', action='store_true',
                    help='a mod zone: write no level effect list (an effect named by a scriptable event is a pointer of '
                         'that scriptable, not a loadfx name); rows go at the end of a zone with no world rows')
    ap.add_argument('--share-runtime', action='store_true',
                    help='a material or image that a --runtime-csv zone defines gets a `<type>,,<name>` reference row')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)

    dumps = {}
    for d in a.dump:
        z, roots = d.split('=', 1)
        dumps.setdefault(z, []).extend(r for r in roots.split(';') if r)

    def find(zone, rel):
        for r in dumps.get(zone or '', []):
            p = os.path.join(r, rel)
            if os.path.isfile(p):
                return p
        return None

    dst = os.path.join(a.work, 'zonetool', a.map)
    csvp = os.path.join(a.work, 'zone_source', a.map + '.csv')
    lines = open(csvp).read().splitlines()
    have = {}
    for ln in lines:
        q = ln.split(',')
        if len(q) == 2 and q[1]:
            have.setdefault((q[0], q[1]), 'full')
        elif len(q) == 3 and q[1] == '' and q[2]:
            have.setdefault((q[0], q[2]), 'ref')
    runtime = set()
    for c in a.runtime_csv:
        for ln in open(c, errors='replace'):
            q = ln.strip().split(',')
            if len(q) == 2 and q[1]:
                runtime.add((q[0], q[1]))

    plan, rows, ref_rows, missing = [], [], [], []
    rep = {'fx': {}, 'materials': {'new': [], 'shared': []}, 'images': {'new': 0, 'shared': 0}, 'techsets': {'embedded': [], 'shared': []},
           'models': [], 'ncs_added': [], 'kitModels': []}

    def add(src, rel):
        plan.append((src, os.path.join(dst, rel)))

    def ref(t, n):
        if (t, n) not in have:
            have[(t, n)] = 'ref'; ref_rows.append('%s,,%s' % (t, n))

    SHADERS = (('vs', 'vertexshader'), ('ps', 'pixelshader'), ('hs', 'hullshader'), ('ds', 'domainshader'))
    seen_tech = set()

    def embed_techset(zone, tech):
        tp = find(zone, os.path.join('techsets', tech + '.techset'))
        if not tp:
            return False
        add(tp, os.path.join('techsets', tech + '.techset'))
        for t in set(strings_of(tp)):
            tq = find(zone, os.path.join('techsets', t + '.technique')) if not set(t) & BADPATH else None
            if not tq:
                continue
            add(tq, os.path.join('techsets', t + '.technique'))
            for x in set(strings_of(tq)):
                if set(x) & BADPATH:
                    continue
                vd = find(zone, os.path.join('techsets', x + '.vertexdecl'))
                if vd:
                    add(vd, os.path.join('techsets', x + '.vertexdecl'))
                if not HEX16.match(x):
                    continue
                for ab, ty in SHADERS:
                    if (ty, x) in runtime or (ty, x) in have:
                        ref(ty, x); break
                    sp = find(zone, os.path.join('techsets', ab, x + '.cso'))
                    if sp:
                        add(sp, os.path.join('techsets', ab, x + '.cso')); break
        rep['techsets']['embedded'].append(tech)
        return True

    seen_mat, seen_img = set(), set()

    def material(zone, mat):
        if mat in seen_mat:
            return
        seen_mat.add(mat)
        if ('material', mat) in have:
            rep['materials']['shared'].append(mat); return
        if a.share_runtime and ('material', mat) in runtime:
            ref('material', mat); rep['materials']['shared'].append(mat); return
        mj = find(zone, os.path.join('materials', mat + '.json'))
        if not mj:
            missing.append('material:' + mat); return
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
            if tech not in seen_tech:
                seen_tech.add(tech)
                if ('techset', tech) in have or ('techset', tech) in runtime:
                    ref('techset', tech); rep['techsets']['shared'].append(tech)
                elif not embed_techset(zone, tech):
                    missing.append('techset:%s (no techsets_%s dump)' % (tech, zone))
        for t in md.get('textureTable', []):
            img = t.get('image')
            if not img or img in seen_img:
                continue
            seen_img.add(img)
            if ('image', img) in have:
                rep['images']['shared'] += 1; continue
            if a.share_runtime and ('image', img) in runtime:
                ref('image', img); rep['images']['shared'] += 1; continue
            ip = find(zone, os.path.join('images', img + '.iw7Image'))
            if not ip:
                missing.append('image:' + img); continue
            add(ip, os.path.join('images', img + '.iw7Image')); rep['images']['new'] += 1

    want = []
    for spec in a.fx:
        for item in spec.split(','):
            z, n = item.split(':', 1)
            want.append((z, n[:-4] if n.endswith('.vfx') else n))
    todo, done = list(want), set()
    while todo:
        zone, name = todo.pop(0)
        if name in done:
            continue
        done.add(name)
        if ('vfx', name) in have:
            rep['fx'][name] = {'zone': zone, 'status': 'already in zone (%s)' % have[('vfx', name)]}
            continue
        vp = find(zone, os.path.join('particlesystem', name + '.iw7VFX'))
        if not vp:
            missing.append('vfx:' + name); continue
        add(vp, os.path.join('particlesystem', name + '.iw7VFX'))
        info = {'zone': zone, 'children': [], 'materials': [], 'models': [], 'other': []}
        for s in sorted(set(strings_of(vp, 4)) - {name}):
            if set(s) & BADPATH:
                continue
            if find(zone, os.path.join('particlesystem', s + '.iw7VFX')) or ('vfx', s) in have:
                info['children'].append(s); todo.append((zone, s)); continue
            if find(zone, os.path.join('materials', s + '.json')) or ('material', s) in have:
                info['materials'].append(s); material(zone, s); continue
            if find(zone, os.path.join('xmodel', s + '.xmb')) or ('xmodel', s) in have:
                info['models'].append(s)
                if ('xmodel', s) not in have:
                    # models (debris chunks) come in through kit_import.py (-KitModels), which runs first
                    rep['kitModels'].append('%s:%s' % (zone, s))
                    if not a.dry_run:
                        missing.append('xmodel %s (add %s:%s to the kit models)' % (s, zone, s))
                continue
            if find(zone, os.path.join('particlesimanimation', s + '.iw7psa')) or any(
                    os.path.isfile(os.path.join(r, 'particlesimanimation', s)) for r in dumps.get(zone, [])):
                info['other'].append('particlesimanimation/' + s); missing.append('particlesimanimation %s (not handled yet)' % s)
        rep['fx'][name] = info
        rows.append('vfx,' + name)

    # the level effect list: assembled copy (hardlink into the stock dump) + the imported top-level names
    ncs_p = os.path.join(dst, NCS)
    ncs = json.load(open(ncs_p)) if os.path.isfile(ncs_p) else {'stringType': 5, 'sourceType': 0, 'stringList': []}
    lst = list(ncs.get('stringList') or [])
    skip = set(x[:-4] if x.endswith('.vfx') else x for x in a.ncs_skip.split(',') if x)
    for z, n in want:
        if n not in lst and n not in skip:
            lst.append(n); rep['ncs_added'].append(n)
    ncs['stringList'] = lst
    rep['missing'] = missing; rep['rows'] = rows; rep['refRows'] = ref_rows
    if not missing and not a.dry_run:
        for src, d in plan:
            if os.path.exists(d):
                continue
            os.makedirs(os.path.dirname(d), exist_ok=True)
            os.link(src, d)
        if not a.no_ncs:
            if os.path.exists(ncs_p):
                os.remove(ncs_p)               # hardlink into the stock dump: never write through it
            os.makedirs(os.path.dirname(ncs_p), exist_ok=True)
            with open(ncs_p, 'w') as f:
                json.dump(ncs, f, indent=4)
        else:
            rep['ncs_added'] = []
        at = next((i for i, l in enumerate(lines) if l.startswith(WORLD_FIRST)), None)
        if at is not None:
            lines[at:at] = [r for r in ref_rows + rows if r not in lines]
        else:
            # a zone with no world (a mod zone): references right after the require rows, before every asset row,
            # since a model met earlier can pull them first (Pam's model -> its scriptable -> the effect's materials
            # -> their images: a reference listed after that was too late, and ZoneTool wrote an empty image)
            top = max([i + 1 for i, l in enumerate(lines) if l.startswith('require,')], default=0)
            lines[top:top] = [r for r in ref_rows if r not in lines]
            lines += [r for r in rows if r not in lines]
        open(csvp, 'w', newline='\n').write('\n'.join(lines) + '\n')
    if a.ncs_out:
        json.dump({'stringType': 5, 'stringList': lst}, open(a.ncs_out, 'w'), indent=1)
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1)
    print('fx import: %d vfx (%d requested), %d new materials (%d shared), %d new image headers, techsets embedded %d, '
          'ncs +%d (%d names), linked %d files; missing %s'
          % (len(rows), len(want), len(rep['materials']['new']), len(rep['materials']['shared']), rep['images']['new'],
             len(rep['techsets']['embedded']), len(rep['ncs_added']), len(lst), 0 if missing or a.dry_run else len(plan), missing[:12]))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
