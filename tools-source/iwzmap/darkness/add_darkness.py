"""Add the darkness + flashlight modules to an assembled usermap zone (after assemble.py / sz2_assemble.py).

- copies cp_iwz_darkness.gsc and cp_iwz_flashlight.gsc to <asset root>/scripts/cp/maps/<map>/<map>_darkness.gsc /
  <map>_flashlight.gsc (rawfiles, called from the level script: generator IWZ_DARK=1 fills //@DARK@);
- inserts their `rawfile,...` rows once, right after the level script row of zone_source/<map>.csv.
The flashlight effects themselves (vfx/iwz/vfx_iwz_flashlight_*) are made by make_vfx_light.py and imported with
fx/fx_import.py (`--dump iwz=<make_vfx_light out root> --fx iwz:vfx/iwz/vfx_iwz_flashlight_world,...`).

usage: add_darkness.py <zone_source csv> <asset root (zonetool/<map>)> <map> [--dark-exposure 8] [--exposures 4,6]
"""
import os, re, shutil, sys

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
    # dark vision set: the map's own vision with auto exposure off and a fixed exposure, so the engine's eye
    # adaptation does not brighten the dark bake back to a lit look (engine run dk2-d2: with auto exposure the dark
    # hall rendered at median luma 0.26). Extra exposures for calibration runs: --exposures 4,6,8
    # The dark vision's keys: --dark "key=value;key=value" (default: auto exposure off). Calibration variants:
    # --variants "name:key=value;key=value|name2:..." -> vision/<map>_dark_<name>.vision. (Run dk3-d3: with
    # tonemapAuto 0, tonemapExposure 2..14 rendered the same image, so exposure is not that key alone.)
    vis = os.path.join(root, 'vision', '%s.vision' % m)
    exposures = [e for e in (argv[argv.index('--exposures') + 1].split(',') if '--exposures' in argv else []) if e]
    dark_ev = argv[argv.index('--dark-exposure') + 1] if '--dark-exposure' in argv else '8'
    dark_keys = argv[argv.index('--dark') + 1] if '--dark' in argv else 'tonemapAuto=0;tonemapExposure=%s' % dark_ev
    variants = [('%s_dark' % m, dark_keys)]
    variants += [('%s_dark_e%s' % (m, e.replace('.', 'p')), 'tonemapAuto=0;tonemapExposure=%s' % e) for e in exposures]
    if '--variants' in argv:
        for v in argv[argv.index('--variants') + 1].split('|'):
            if ':' in v:
                n, keys = v.split(':', 1)
                variants.append(('%s_dark_%s' % (m, n), keys))
    if os.path.exists(vis):
        base = open(vis, encoding='latin1').read()
        for name, keys in variants:
            txt = base
            for kv in keys.split(';'):
                if '=' not in kv:
                    continue
                k, v = kv.split('=', 1)
                if re.search(r'(?m)^%s ".*"$' % re.escape(k), txt):
                    txt = re.sub(r'(?m)^%s ".*"$' % re.escape(k), '%s "%s"' % (k, v), txt)
                else:
                    txt += '%s "%s"\n' % (k, v)
            rel = 'vision/%s.vision' % name
            open(os.path.join(root, *rel.split('/')), 'w', newline='\n', encoding='latin1').write(txt)
            rows.append('rawfile,' + rel)
    else:
        print('no %s: dark vision not made' % vis)
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
