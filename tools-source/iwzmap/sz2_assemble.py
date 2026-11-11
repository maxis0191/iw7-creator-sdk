"""After assemble.py: add the generator's custom world materials (cloned stock world materials with a custom colour
image and/or colour constants) and their TGA images to zonetool/<map>/, and their rows to zone_source/<map>.csv
(before the world assets, which reference them).

usage: sz2_assemble.py <work dir> <map> <generated source dir (custom_materials.json)>
Stock files in zonetool/<map>/ are hardlinks into the stock dumps: they are never modified, only new files are written.
"""
import copy, json, os, shutil, sys

work, mapname, src = sys.argv[1:4]
dst = os.path.join(work, 'zonetool', mapname)
spec = json.load(open(os.path.join(src, 'custom_materials.json')))['custom']
rows = []
for key, c in spec.items():
    base = json.load(open(os.path.join(dst, 'materials', 'w', c['base'] + '.json')))
    m = copy.deepcopy(base)
    for const in m.get('constantTable', []):
        if const['name'] == 'colorTint' and c.get('tint'):
            const['literal'] = [float(v) for v in c['tint']]
        if const['name'] == 'emissivePara' and c.get('emissive'):
            const['literal'] = [float(v) for v in c['emissive']]
        if const['name'] in (c.get('consts') or {}):      # any other named constant (e.g. reflectionRa, SSR)
            const['literal'] = [float(v) for v in c['consts'][const['name']]]
    if c.get('image'):
        colour = [t for t in m['textureTable'] if t['semantic'] == 2]
        assert len(colour) == 1, (key, 'expected one colour texture in', c['base'])
        colour[0]['image'] = c['image']
        os.makedirs(os.path.join(dst, 'images'), exist_ok=True)
        out_img = os.path.join(dst, 'images', c['image'] + '.tga')
        if os.path.exists(out_img):
            os.remove(out_img)
        shutil.copyfile(c['tga'], out_img)
    name = c['path'].split('/', 1)[1]
    out = os.path.join(dst, 'materials', 'w', name + '.json')
    if os.path.exists(out):
        os.remove(out)        # never write through a hardlink
    json.dump(m, open(out, 'w'), indent=4)
    rows.append('material,' + c['path'])
csv = os.path.join(work, 'zone_source', mapname + '.csv')
lines = open(csv).read().splitlines()
at = next(i for i, l in enumerate(lines) if l.startswith('com_map,'))
lines[at:at] = [r for r in rows if r not in lines]
# game-script modules of the emit (<src>/modules/<map>_<name>.gsc, sz_modules.py): rawfiles right after the level script
mods = sorted(f for f in os.listdir(os.path.join(src, 'modules')) if f.endswith('.gsc')) if os.path.isdir(os.path.join(src, 'modules')) else []
mrows = []
for f in mods:
    rel = 'scripts/cp/maps/%s/%s' % (mapname, f)
    out = os.path.join(dst, *rel.split('/'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    shutil.copyfile(os.path.join(src, 'modules', f), out)
    mrows.append('rawfile,' + rel)
if mrows:
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (mapname, mapname)
    at = lines.index(level_row) + 1
    lines[at:at] = [r for r in mrows if r not in lines]
open(csv, 'w', newline='\n').write('\n'.join(lines) + '\n')
print('custom materials', len(rows), 'modules', len(mrows))
