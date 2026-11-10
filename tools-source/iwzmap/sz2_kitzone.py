"""Add kit models from other CP zones (cp_disco, cp_final) to an assembled map zone (after assemble.py / sz2_assemble.py,
before buildzone): link their xmodel, xsurface, material and image dump files into zonetool/<map>/ and add the zone
csv rows (require,techsets_<zone> and xmodel,<name> before the world rows).

usage: sz2_kitzone.py <work dir> <map> <kit_final.json> <model name>[,<model name>...]
       --models-root <dir with <zone>/{xmodel,xsurface,images}> --materials-root <dir with <zone>/materials>

Stock files are hardlinked (never modified); a name already present in the target is kept. Prints what was linked
and the rows added; exits 1 when a model, xsurface or material file is missing.
"""
import json, os, re, sys

work, mapname, kitf, names = sys.argv[1:5]
models_root = sys.argv[sys.argv.index('--models-root') + 1]
mats_root = sys.argv[sys.argv.index('--materials-root') + 1]
dst = os.path.join(work, 'zonetool', mapname)
kit = {m['name']: m for m in json.load(open(kitf))['models']}
names = [n for n in names.split(',') if n]
linked, missing, zones = 0, [], set()


def link(src, d):
    global linked
    if os.path.exists(d):
        return
    os.makedirs(os.path.dirname(d), exist_ok=True)
    os.link(src, d)
    linked += 1


rows = []
for n in names:
    m = kit.get(n)
    if not m:
        missing.append('kit:' + n); continue
    z = m['source']
    zones.add(z)
    mr = os.path.join(models_root, z)
    for f in os.listdir(os.path.join(mr, 'xmodel')):
        if f.startswith(n + '.') or f.startswith(n + '_lod'):
            link(os.path.join(mr, 'xmodel', f), os.path.join(dst, 'xmodel', f))
    if not os.path.exists(os.path.join(dst, 'xmodel', n + '.xmb')):
        missing.append('xmodel:' + n)
    # xsurfaces named after the model (lod surfaces)
    for f in os.listdir(os.path.join(mr, 'xsurface')):
        if f.startswith(n) or f.startswith(n.replace('_bsp2xmodel', '')):
            link(os.path.join(mr, 'xsurface', f), os.path.join(dst, 'xsurface', f))
    for mat in m.get('materials', []):
        mj = os.path.join(mats_root, z, 'materials', mat + '.json')
        if not os.path.isfile(mj):
            missing.append('material:' + mat); continue
        link(mj, os.path.join(dst, 'materials', mat + '.json'))
        try:
            md = json.load(open(mj))
        except Exception:
            continue
        for t in md.get('textureTable', []):
            img = t.get('image')
            if not img:
                continue
            for root in (os.path.join(mr, 'images'), os.path.join(mats_root, z, 'images')):
                p = os.path.join(root, img + '.iw7Image')
                if os.path.isfile(p):
                    link(p, os.path.join(dst, 'images', img + '.iw7Image'))
                    break
    rows.append('xmodel,' + n)
csv = os.path.join(work, 'zone_source', mapname + '.csv')
lines = open(csv).read().splitlines()
req = ['require,techsets_' + z for z in sorted(zones)]
first_req = next((i for i, l in enumerate(lines) if l.startswith('require,')), 1)
lines[first_req:first_req] = [r for r in req if r not in lines]
at = next(i for i, l in enumerate(lines) if l.startswith('com_map,'))
lines[at:at] = [r for r in rows if r not in lines]
open(csv, 'w', newline='\n').write('\n'.join(lines) + '\n')
print('kit zone: linked %d files, rows %s %s, missing %s' % (linked, req, rows, missing[:20]))
sys.exit(1 if missing else 0)
