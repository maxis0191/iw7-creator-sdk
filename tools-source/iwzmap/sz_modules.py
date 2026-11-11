"""Game-script modules of a scene-generated map (Station Zero Q1 quest, T1 Capsule Post, and any later package).

Each file modules/<name>.gsc is a self-contained level module. The emit (scenegen.py emit) fills two tables in it:
  //@MARKERS@  one line per placed scene marker:  m[m.size] = [ kind, id, zone, origin, yaw ];  (+ lo, hi for an 'area' [x0,y0,z0,x1,y1,z1])
  //@VOLUMES@  one line per spawn volume:         v[v.size] = [ name, zone, lo, hi ];
and writes it to <src>/modules/<map>_<name>.gsc. The level script calls each module's init() (//@MODULES@ in
cp_iwz3.gsc) and sz2_assemble.py puts the files in the zone as scripts/cp/maps/<map>/<map>_<name>.gsc. The modules
call no function of each other or of the level script by path. A changed module is tested on an already built map by
installing the file at iw7-mod/scripts/cp/maps/<map>/<map>_<name>.gsc (read before the zone's rawfile; docs/DEVKIT.md).

usage: sz_modules.py <src>                 regenerate <src>/modules from <src>/layout.json (same output as the emit)
       sz_modules.py <src> --out <dir>     write them elsewhere (loose files for a test session)
"""
import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = os.path.join(HERE, 'modules')


def v3(p):
    return '( %g, %g, %g )' % tuple(round(float(c), 2) for c in p)


def marker_lines(markers):
    out = []
    for m in markers:
        if m.get('origin') is None:
            continue
        row = '"%s", "%s", "%s", %s, %g' % (m['kind'], m.get('id', ''), m['zone'], v3(m['origin']), float(m.get('yaw') or 0))
        b = m.get('area')
        if isinstance(b, list) and len(b) == 6:
            row += ', %s, %s' % (v3(b[:3]), v3(b[3:]))
        out.append('    m[m.size] = [ %s ];' % row)
    return out


def volume_lines(vols):
    out = []
    for v in vols:
        b = v['box']
        out.append('    v[v.size] = [ "%s", "%s", %s, %s ];' % (v['name'], v['zone'], v3(b[:3]), v3(b[3:])))
    return out


def names():
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(MODULES, '*.gsc')))


def emit(out_dir, markers, vols, mapname):
    """write every module with its tables filled; returns the module names"""
    os.makedirs(out_dir, exist_ok=True)
    ml, vl = '\n'.join(marker_lines(markers)), '\n'.join(volume_lines(vols))
    done = []
    for n in names():
        src = open(os.path.join(MODULES, n + '.gsc'), encoding='utf-8').read()
        src = src.replace('//@MARKERS@', ml.lstrip()).replace('//@VOLUMES@', vl.lstrip())
        with open(os.path.join(out_dir, '%s_%s.gsc' % (mapname, n)), 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        done.append(n)
    return done


def calls(mods, mapname):
    """the level script lines that start the modules"""
    return ['    level thread scripts\\cp\\maps\\%s\\%s_%s::init();' % (mapname, mapname, n) for n in mods]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('src')
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    mapname = lay.get('map', 'cp_iwz')
    out = a.out or os.path.join(a.src, 'modules')
    mods = emit(out, lay.get('markers', []), lay.get('volumes', []), mapname)
    print('modules: %s -> %s' % (', '.join(mods), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
