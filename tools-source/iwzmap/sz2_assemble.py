"""After assemble.py: add the generator's custom world materials (cloned stock world materials with a custom colour
image and/or colour constants, or the extended route: own packed normal and gloss images; each with the base's technique state files under its own name) and their TGA images to zonetool/<map>/, and their rows to zone_source/<map>.csv
(before the world assets, which reference them).

usage: sz2_assemble.py <work dir> <map> <generated source dir (custom_materials.json)>
Stock files in zonetool/<map>/ are hardlinks into the stock dumps: they are never modified, only new files are written.
"""
import copy, json, os, shutil, sys

work, mapname, src = sys.argv[1:4]
dst = os.path.join(work, 'zonetool', mapname)
spec = json.load(open(os.path.join(src, 'custom_materials.json')))['custom']
rows = []
STATE_FILES = (('state', ('.stateinfo', '.statebits', '.statebitsmap')), ('constantbuffer', ('.cbi', '.cbt')))


def clone_state_files(base_name, new_name, techset):
    """ZoneTool reads techsets/state/<techset>/<material>.{stateinfo,statebits,statebitsmap} and techsets/constantbuffer/<techset>/<material>.{cbi,cbt}
    (material name with its folder: w/<name>) and stops the build with 'statebits for techset ... are missing' when a custom material has none
    (the fallback picks a file of the techset's own folder, never one of a subfolder). The stock files sit under the base material's name:
    the clone gets copies under its own name (read through the root: a link of a full build, a stock dump through the reference build's overlay)."""
    n = 0
    for sub, exts in STATE_FILES:
        for ext in exts:
            s = os.path.join(dst, 'techsets', sub, techset, 'w', base_name + ext)
            if not os.path.isfile(s):
                continue
            out = os.path.join(dst, 'techsets', sub, techset, 'w', new_name + ext)
            if os.path.exists(out):
                os.remove(out)        # never write through a hardlink
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(s, 'rb') as f:
                data = f.read()
            with open(out, 'wb') as f:
                f.write(data)
            n += 1
    return n


def copy_image(tga, image):
    """the TGA as images/<image>.tga; a DDS with the full mip chain beside it (a TGA is one mip) as images/<image>.dds, which ZoneTool loads first"""
    os.makedirs(os.path.join(dst, 'images'), exist_ok=True)
    out_img = os.path.join(dst, 'images', image + '.tga')
    if os.path.exists(out_img):
        os.remove(out_img)
    shutil.copyfile(tga, out_img)
    dds = os.path.splitext(tga)[0] + '.dds'
    if os.path.isfile(dds):
        out_dds = os.path.join(dst, 'images', image + '.dds')
        if os.path.exists(out_dds):
            os.remove(out_dds)
        shutil.copyfile(dds, out_dds)


def copy_header(header, image):
    """a stock image of another zone: its dumped header as images/<image>.iw7Image. The pixels are not in the file: the header names the bytes of a stock
    imagefile<N>.pak, and the game streams them from there (as kit_import.py does for the images of an imported model). The name must be the stock one."""
    os.makedirs(os.path.join(dst, 'images'), exist_ok=True)
    out = os.path.join(dst, 'images', image + '.iw7Image')
    if os.path.exists(out):
        os.remove(out)        # never write through a hardlink
    shutil.copyfile(header, out)


n_state = 0
for key, c in spec.items():
    ext = c.get('ext')
    base_name = ext['base'] if ext else c['base']
    base = json.load(open(os.path.join(dst, 'materials', 'w', base_name + '.json')))
    m = copy.deepcopy(base)
    if ext:
        # the extended route: a base with a packed normal and gloss map (semantic 14 / 15 of the concrete_01 family); every texture of a listed semantic
        # points at our image. "ext": {"base": "concrete_01", "images": {"14": {"image": name, "tga": path}, "15": {...}}}
        # An image entry {"image": name, "header": path of a dumped .iw7Image} is a stock image of another zone (a sky: base "sky_cp_zmb", semantic 2).
        # "set": {field: value} writes fields of the material itself (a stock sky of another zone differs from the base in `gameFlags` at most).
        for t in m['textureTable']:
            im = ext['images'].get(str(t['semantic']))
            if im:
                t['image'] = im['image']
        missing = [s for s in ext['images'] if not any(str(t['semantic']) == s for t in m['textureTable'])]
        assert not missing, (key, 'base has no semantic', missing)
        for im in ext['images'].values():
            if im.get('header'):
                copy_header(im['header'] if os.path.isabs(im['header']) else os.path.join(src, im['header']), im['image'])      # a relative path is the emit folder's
            else:
                copy_image(im['tga'], im['image'])
        for field, value in (ext.get('set') or {}).items():
            assert field in m, (key, 'the base material has no field', field)
            m[field] = value
    else:
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
            copy_image(c['tga'], c['image'])
    name = c['path'].split('/', 1)[1]
    out = os.path.join(dst, 'materials', 'w', name + '.json')
    if os.path.exists(out):
        os.remove(out)        # never write through a hardlink
    json.dump(m, open(out, 'w'), indent=4)
    tech = base.get('techniqueSet->name')
    if tech:
        n_state += clone_state_files(base_name, name, tech)
    rows.append('material,' + c['path'])
csv = os.path.join(work, 'zone_source', mapname + '.csv')
lines = open(csv).read().splitlines()
at = next(i for i, l in enumerate(lines) if l.startswith('com_map,'))
lines[at:at] = [r for r in rows if r not in lines]
# models drawn by a relocated stock scriptable (src/scriptables.txt). The stock zone ships them only through the scriptable
# definition, so the full-stock rows of assemble.py list their surfaces but never the model: the relocated scriptable
# was placed and worked, but drew nothing (Station Zero RC4: no Pack-a-Punch machine in any frame since RC1; probe
# sz_pap_machine read part machine "on" at 3104 4110). Rows go before the world assets that reference the definition.
SCRIPTABLE_MODELS = {'pap_machine': ('zmb_pap_machine_animated', 'zmb_pap_machine_animated_blue')}
reloc = os.path.join(src, 'scriptables.txt')
moved = {l.split()[0] for l in open(reloc).read().splitlines() if l.strip()} if os.path.isfile(reloc) else set()
srows = ['xmodel,' + m for n in sorted(moved & set(SCRIPTABLE_MODELS)) for m in SCRIPTABLE_MODELS[n]
         if os.path.isfile(os.path.join(dst, 'xmodel', m + '.xmb'))]
at = next(i for i, l in enumerate(lines) if l.startswith('com_map,'))
lines[at:at] = [r for r in srows if r not in lines]
print('scriptable models', len(srows), ' '.join(srows))
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
# the level script of the nine-zone line starts the Capsule Post by path: a zone without that file fails to link (the map
# shuts down at load, as with the baked source that lost modules/), so the call goes when the module is not in the zone
lvl = os.path.join(dst, 'scripts', 'cp', 'maps', mapname, mapname + '.gsc')
post_call = '    level thread scripts\\cp\\maps\\%s\\%s_post::init();' % (mapname, mapname)
if os.path.isfile(lvl) and not any(f == '%s_post.gsc' % mapname for f in mods):
    text = open(lvl).read()
    if post_call in text:
        os.remove(lvl)      # never write through a hardlink
        open(lvl, 'w', newline='\n').write(text.replace(post_call, '    // (sz2_assemble: no modules/%s_post.gsc in the source, the Capsule Post call was dropped)' % mapname))
        print('WARNING: the level script starts the Capsule Post but %s/modules has no %s_post.gsc: the call was dropped from the zone copy' % (src, mapname))
if mrows:
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (mapname, mapname)
    at = lines.index(level_row) + 1
    lines[at:at] = [r for r in mrows if r not in lines]
open(csv, 'w', newline='\n').write('\n'.join(lines) + '\n')
# the map's own look (layout.json lighting: fog, exposure, vision keys): vision/<map>.vision, which assemble.py shipped (vision_edit.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vision_edit
_lay = os.path.join(src, 'layout.json')
_vis = vision_edit.apply_to_zone(dst, mapname, (json.load(open(_lay)).get('lighting') if os.path.isfile(_lay) else None))
if _vis:
    print('vision/%s.vision: %d keys changed, %d added (%s)' % (mapname, len(_vis['changed']), len(_vis['added']), ', '.join(sorted(list(_vis['changed']) + _vis['added']))))
import sky_edit
_sky = sky_edit.apply_to_zone(dst, mapname, (json.load(open(_lay)).get('lighting') if os.path.isfile(_lay) else None))
if _sky:
    print('sky and sun: %s' % json.dumps(_sky))
print('custom materials', len(rows), 'state files', n_state, 'modules', len(mrows))
