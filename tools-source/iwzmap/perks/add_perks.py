"""Add the perk module of Station Zero (package P1) to an assembled usermap zone (after assemble.py / sz2_assemble.py).

- the scripts: cp_iwz_perks.gsc and the four new perks' files go to <asset root>/scripts/cp/maps/<map>/ as rawfiles
  (the level script calls scripts\\cp\\maps\\<map>\\cp_iwz_perks::init and ::register), their rows right after the level
  script row of zone_source/<map>.csv;
- the HUD icons: one 2D material per new perk (a copy of the stock perk icon material cp_zmb_perk_icon_tough with its
  own image; the images are the TGAs of make_perk_icons.py, drawn at build time), and Deadeye Dewdrops' stock icon material, whose image
  comes from the cp_disco dump (the template map's zone has no Deadeye icon);
- the stock perk bit table (stringtable cp/zombies/zombie_perks_bit_mask_table.csv, already in the zone from the
  template's patch zone) gets one row per new perk: the stock HUD draws the icon of every bit the server sets in the
  omnvar zm_active_perks, reading the icon name from this table (ui/utils/cp/ingamecoopdatasources.lua).

usage: add_perks.py <zone_source csv> <asset root (zonetool/<map>)> <map> --template-dump <dump root (holds
       techsets_cp_zmb)> [--deadeye-image <cp_disco dump>/images/cp_zmb_perk_icon_deadeye.iw7Image] [--icons <dir>]
Stock files in the asset root may be hardlinks into the dumps: a file is always removed before it is written.
"""
import argparse, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = ['cp_iwz_perks', 'cp_iwz_perk_bakers', 'cp_iwz_perk_voyages', 'cp_iwz_perk_grudges', 'cp_iwz_perk_doubletakes']
# bit (1-based, the table's first column), perk, icon material. 1..17 are the stock rows.
NEW_ROWS = [(18, 'perk_machine_bakers', 'iwz_perk_icon_bakers'), (19, 'perk_machine_voyage', 'iwz_perk_icon_voyage'),
            (20, 'perk_machine_grudge', 'iwz_perk_icon_grudge'), (21, 'perk_machine_double', 'iwz_perk_icon_double'),
            (22, 'perk_machine_double_cd', 'iwz_perk_icon_double_cd')]
ICON_BASE = 'cp_zmb_perk_icon_tough'
TABLE = 'cp/zombies/zombie_perks_bit_mask_table.csv'


def write_new(path, data, mode='w'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)            # never write through a hardlink into a dump
    if mode == 'wb':
        open(path, 'wb').write(data)
    else:
        open(path, 'w', newline='\n', encoding='utf-8').write(data)


def copy_new(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copyfile(src, dst)


def icon_material(root, tdump, name, image):
    """a 2D material named <name> showing <image>: the stock icon material's json and its 2d techset state files"""
    base = json.load(open(os.path.join(tdump, 'materials', ICON_BASE + '.json')))
    base['textureTable'][0]['image'] = image
    write_new(os.path.join(root, 'materials', name + '.json'), json.dumps(base, indent=4))
    for sub, exts in (('state', ('.stateinfo', '.statebits', '.statebitsmap')), ('constantbuffer', ('.cbi', '.cbt'))):
        for ext in exts:
            src = os.path.join(tdump, 'techsets', sub, '2d', ICON_BASE + ext)
            if os.path.exists(src):
                copy_new(src, os.path.join(root, 'techsets', sub, '2d', name + ext))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('root')
    ap.add_argument('map')
    ap.add_argument('--template-dump', required=True)
    ap.add_argument('--deadeye-image', default='')
    ap.add_argument('--icons', default='')        # default: <asset root>/../perk_icons, drawn by make_perk_icons.py when missing
    a = ap.parse_args(argv)
    m, root = a.map, a.root
    tdump = os.path.join(a.template_dump, 'techsets_cp_zmb')
    rows = []
    for mod in MODULES:
        rel = 'scripts/cp/maps/%s/%s.gsc' % (m, mod)
        src = open(os.path.join(HERE, mod + '.gsc'), encoding='utf-8').read()
        src = src.replace('scripts\\cp\\maps\\cp_iwz\\', 'scripts\\cp\\maps\\%s\\' % m)
        write_new(os.path.join(root, *rel.split('/')), src)
        rows.append('rawfile,' + rel)
    mats = []
    icons = a.icons or os.path.join(os.path.dirname(os.path.abspath(root)), 'perk_icons')
    if not all(os.path.exists(os.path.join(icons, r[2] + '.tga')) for r in NEW_ROWS):
        subprocess.check_call([sys.executable, '-I', '-B', os.path.join(HERE, 'make_perk_icons.py'), icons])
    for bit, perk, mat in NEW_ROWS:
        tga = os.path.join(icons, mat + '.tga')
        if not os.path.exists(tga):
            raise SystemExit('missing icon %s (make_perk_icons.py)' % tga)
        copy_new(tga, os.path.join(root, 'images', mat + '.tga'))
        icon_material(root, tdump, mat, mat)
        mats.append(mat)
    if a.deadeye_image:
        copy_new(a.deadeye_image, os.path.join(root, 'images', 'cp_zmb_perk_icon_deadeye.iw7Image'))
        icon_material(root, tdump, 'cp_zmb_perk_icon_deadeye', 'cp_zmb_perk_icon_deadeye')
        mats.append('cp_zmb_perk_icon_deadeye')
    # the bit table: the zone's own copy (from the template's patch zone) plus the new rows
    tp = os.path.join(root, *TABLE.split('/'))
    if not os.path.exists(tp):
        tp_src = os.path.join(a.template_dump, 'patch_cp_zmb', *TABLE.split('/'))
        lines = open(tp_src).read().splitlines()
    else:
        lines = open(tp).read().splitlines()
    have = {l.split(',')[1] for l in lines[1:] if l.count(',') >= 2}
    lines += ['%d,%s,%s' % r for r in NEW_ROWS if r[1] not in have]
    write_new(tp, '\n'.join(lines) + '\n')
    csvl = open(a.csv).read().splitlines()
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (m, m)
    if level_row not in csvl:
        raise SystemExit('level script row %s not in %s' % (level_row, a.csv))
    at = csvl.index(level_row) + 1
    new = [r for r in rows if r not in csvl]
    csvl[at:at] = new
    # materials before the world (they are referenced by name only, from script and from the stock HUD)
    first = next(i for i, l in enumerate(csvl) if l.startswith('com_map,'))
    mrows = ['material,' + x for x in mats if 'material,' + x not in csvl]
    csvl[first:first] = mrows
    if 'stringtable,' + TABLE not in csvl:
        csvl.insert(first, 'stringtable,' + TABLE)
    open(a.csv, 'w', newline='\n').write('\n'.join(csvl) + '\n')
    print('perks module: %d script rows, %d icon materials, bit table %d rows (%s)' % (len(new), len(mrows), len(lines) - 1, tp))


if __name__ == '__main__':
    main()
