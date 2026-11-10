"""Make a self-lit ("dark") variant of a lit stock effect: the same particles with their lit blend materials swapped to
the unlit counterpart techset and a faint colour, so the effect reads in a pitch-dark map without any light.

Why: IW7 lit particle materials (techsets eq_effect_*_blend_*) are lit by the baked light grid (fx\\NOTES.md, probe6:
pipe steam reads next to a baked emergency lamp, nothing in an unlit tunnel). In a dark bake they disappear. The stock
unlit counterparts (eq_effectunlit_*) take exactly the same constants (textureAtlas, featherParms, atlasBlendPa,
colorTint, falloff*), so a clone with the unlit techset, the donor's state / constant-buffer layout and a scaled
colorTint is a faint self-lit version of the same sprite.

usage: fx_variant.py --dump <root>[;<root>...] (vfx, material, techset dumps; searched in order)
                     --fx <vfx path>[,...] --out <variant dump root> [--suffix _dark] [--tint 0.15] [--prefix vfx/iwz/amb/]
                     [--techsets <techsets_all.txt>] [--report <json>]
Output (a dump root for fx_import.py --dump iwz=<out>;<the same roots>):
  particlesystem/<prefix><base><suffix>.iw7VFX   effect (and its children) renamed, material tokens remapped
  materials/<dir>/iwz_<base><suffix>.json        unlit clone; techsets/state|constantbuffer/<unlit techset>/... copied
                                                 from a stock material that uses that techset (same constant order)
Distortion / unlit / emissive materials are kept. A lit material without an unlit counterpart is kept and reported.
"""
import argparse, glob, json, os, re, shutil, sys

TOK_ASSET, TOK_STR = b'\x07\x01', b'\x06\x01'


def strs(data, n=4):
    return sorted(set(m.decode() for m in re.findall(rb'[\x20-\x7e]{%d,}' % n, data)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dump', action='append', default=[])
    ap.add_argument('--fx', action='append', default=[])
    ap.add_argument('--out', required=True)
    ap.add_argument('--suffix', default='_dark')
    ap.add_argument('--tint', type=float, default=0.15)
    ap.add_argument('--prefix', default='vfx/iwz/amb/')
    ap.add_argument('--techsets', default='')
    ap.add_argument('--report', default='')
    a = ap.parse_args(argv)
    roots = [r for d in a.dump for r in d.split(';') if r]

    def find(rel):
        for r in roots:
            p = os.path.join(r, rel)
            if os.path.isfile(p):
                return p
        return None

    known_tech = set(open(a.techsets).read().split()) if a.techsets else None
    donors = {}

    def donor_for(tech):
        """(state dir, cbuffer dir, stem) of a stock material that uses `tech` and has all its files"""
        if tech in donors:
            return donors[tech]
        donors[tech] = None
        for r in roots:
            sd = os.path.join(r, 'techsets', 'state', tech)
            cd = os.path.join(r, 'techsets', 'constantbuffer', tech)
            for f in sorted(glob.glob(os.path.join(sd, '**', '*.statebits'), recursive=True)):
                stem = os.path.relpath(f, sd)[:-len('.statebits')]
                if all(os.path.isfile(os.path.join(sd, stem + e)) for e in ('.statebitsmap', '.stateinfo')) and \
                        all(os.path.isfile(os.path.join(cd, stem + e)) for e in ('.cbi', '.cbt')):
                    mj = find(os.path.join('materials', stem + '.json'))
                    if mj:
                        donors[tech] = (sd, cd, stem, json.load(open(mj)))
                        return donors[tech]
        return None

    def unlit_of(tech):
        if 'unlit' in tech or 'distortion' in tech or tech.endswith('_em') or '_em_' in tech:
            return None
        t = tech.replace('_effect_', '_effectunlit_', 1)
        for drop in ('_shl', '_norm_spec', '_spec', '_norm'):
            t = t.replace(drop, '')
        if known_tech is not None and t not in known_tech:
            t2 = t.replace('_nofog', '')
            return t2 if t2 in known_tech else None
        return t

    rep = {'fx': {}, 'materials': {}, 'kept': []}
    os.makedirs(a.out, exist_ok=True)
    newname = lambda n: a.prefix + n.split('/')[-1] + a.suffix
    todo, done = [n[:-4] if n.endswith('.vfx') else n for f in a.fx for n in f.split(',') if n], set()
    mat_map = {}
    while todo:
        name = todo.pop(0)
        if name in done:
            continue
        done.add(name)
        vp = find(os.path.join('particlesystem', name + '.iw7VFX'))
        if not vp:
            raise SystemExit('no dump of ' + name)
        data = open(vp, 'rb').read()
        children, mats = [], []
        for s in strs(data):
            if s == name:
                continue
            if find(os.path.join('particlesystem', s + '.iw7VFX')) and (TOK_ASSET + s.encode() + b'\x00') in data:
                children.append(s); todo.append(s)
            elif find(os.path.join('materials', s + '.json')) and (TOK_ASSET + s.encode() + b'\x00') in data:
                mats.append(s)
        for m in mats:
            if m in mat_map or m in rep['kept']:
                continue
            mj = json.load(open(find(os.path.join('materials', m + '.json'))))
            tech = mj.get('techniqueSet->name') or ''
            ut = unlit_of(tech)
            dn = donor_for(ut) if ut else None
            if not dn:
                rep['kept'].append(m); continue
            sd, cd, stem, dj = dn
            names = [c['name'] for c in (mj.get('constantTable') or [])]
            dnames = [c['name'] for c in (dj.get('constantTable') or [])]
            if sorted(names) != sorted(dnames):
                rep['kept'].append(m); rep['materials'][m] = {'skip': 'constants %s vs donor %s' % (names, dnames)}; continue
            nm = os.path.dirname(m) + '/iwz_' + os.path.basename(m) + a.suffix
            out = dict(mj)
            for k in ('materialType', 'stateFlags', 'renderFlags', 'cameraRegion'):
                if k in dj:
                    out[k] = dj[k]
            out['techniqueSet->name'] = ut
            byname = {c['name']: c for c in mj['constantTable']}
            ct = []
            for c in dj['constantTable']:                      # donor order = constant buffer layout order
                cc = json.loads(json.dumps(byname[c['name']]))
                if cc['name'] == 'colorTint':
                    cc['literal'] = [cc['literal'][0] * a.tint, cc['literal'][1] * a.tint, cc['literal'][2] * a.tint, cc['literal'][3]]
                ct.append(cc)
            out['constantTable'] = ct
            p = os.path.join(a.out, 'materials', nm + '.json')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump(out, open(p, 'w'), indent=4)
            for e in ('.statebits', '.statebitsmap', '.stateinfo'):
                q = os.path.join(a.out, 'techsets', 'state', ut, nm + e)
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copyfile(os.path.join(sd, stem + e), q)
            for e in ('.cbi', '.cbt'):
                q = os.path.join(a.out, 'techsets', 'constantbuffer', ut, nm + e)
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copyfile(os.path.join(cd, stem + e), q)
            mat_map[m] = nm
            rep['materials'][m] = {'new': nm, 'techset': tech + ' -> ' + ut, 'donor': stem, 'tint': a.tint}
        for m in mats:
            if m in mat_map:
                data = data.replace(TOK_ASSET + m.encode() + b'\x00', TOK_ASSET + mat_map[m].encode() + b'\x00')
        for c in children:
            data = data.replace(TOK_ASSET + c.encode() + b'\x00', TOK_ASSET + newname(c).encode() + b'\x00')
        own = TOK_STR + name.encode() + b'\x00'
        if own not in data:
            raise SystemExit('%s: own name token not found' % name)
        data = data.replace(own, TOK_STR + newname(name).encode() + b'\x00', 1)
        q = os.path.join(a.out, 'particlesystem', newname(name) + '.iw7VFX')
        os.makedirs(os.path.dirname(q), exist_ok=True)
        open(q, 'wb').write(data)
        rep['fx'][name] = {'new': newname(name), 'children': [newname(c) for c in children], 'materials': mats}
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1)
    for n, v in rep['fx'].items():
        print('%s -> %s (materials %s)' % (n, v['new'], ', '.join(mat_map.get(m, m + ' [kept]') for m in v['materials'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
