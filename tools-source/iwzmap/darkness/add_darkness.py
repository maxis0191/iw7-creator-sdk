"""Add the darkness + flashlight modules to an assembled usermap zone (after assemble.py / sz2_assemble.py).

- copies cp_iwz_darkness.gsc and cp_iwz_flashlight.gsc to <asset root>/scripts/cp/maps/<map>/<map>_darkness.gsc /
  <map>_flashlight.gsc (rawfiles, called from the level script: generator IWZ_DARK=1 fills //@DARK@);
- inserts their `rawfile,...` rows once, right after the level script row of zone_source/<map>.csv.
The flashlight effects themselves (vfx/iwz/vfx_iwz_flashlight_*) are made by make_vfx_light.py and imported with
fx/fx_import.py (`--dump iwz=<make_vfx_light out root> --fx iwz:vfx/iwz/vfx_iwz_flashlight_world,...`).

usage: add_darkness.py <zone_source csv> <asset root (zonetool/<map>)> <map>
"""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    csvp, root, m = argv[:3]
    rows = []
    for mod in ('darkness', 'flashlight'):
        rel = 'scripts/cp/maps/%s/%s_%s.gsc' % (m, m, mod)
        dst = os.path.join(root, *rel.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        src = open(os.path.join(HERE, 'cp_iwz_%s.gsc' % mod), encoding='utf-8').read()
        # the modules call each other through scripts\cp\maps\cp_iwz\...: rename for another map
        src = src.replace('scripts\\cp\\maps\\cp_iwz\\cp_iwz_', 'scripts\\cp\\maps\\%s\\%s_' % (m, m))
        open(dst, 'w', newline='\n', encoding='utf-8').write(src)
        rows.append('rawfile,' + rel)
    lines = open(csvp).read().splitlines()
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (m, m)
    if level_row not in lines:
        raise SystemExit('level script row %s not in %s' % (level_row, csvp))
    at = lines.index(level_row) + 1
    new = [r for r in rows if r not in lines]
    lines[at:at] = new
    open(csvp, 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('darkness modules: %d rows added after %s' % (len(new), level_row))


if __name__ == '__main__':
    main()
