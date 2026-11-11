"""Add the crowd module (package E2: more than 24 zombies alive) to an assembled usermap zone (after assemble.py).

- writes the crowd body model: a copy of a stock full-body zombie model with no scriptable (crowd_model.py), as
  <asset root>/xmodel/<name>.xmb, and its `xmodel,<name>` row;
- copies cp_iwz_crowd.gsc to <asset root>/scripts/cp/maps/<map>/<map>_crowd.gsc and inserts its `rawfile,...` row once,
  right after the level script row of zone_source/<map>.csv;
- makes the level script call it: the marker //@CROWD@ of the level script (cp_iwz3.gsc) becomes the call; a level
  script emitted before the marker existed gets the call right before //@AUDIO@.

usage: add_crowd.py <zone_source csv> <asset root (zonetool/<map>)> <map> --stock-xmodel <stock dump xmodel dir>
                    [--model police_officer_zombie] [--name iwz_crowd_cop]
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crowd_model  # noqa: E402


def call_line(m):
    return '    scripts\\cp\\maps\\%s\\%s_crowd::init();     // crowd module (E2): zombies beyond the 24 agents' % (m, m)


def patch_level(text, m):
    """The level script with the crowd module's call; raises when it has no place for it."""
    line = call_line(m)
    if line in text:
        return text
    if '//@CROWD@' in text:
        out = []
        for ln in text.split('\n'):
            out.append(line if ln.strip() == '//@CROWD@' else ln)
        return '\n'.join(out)
    if '//@AUDIO@' in text:
        out = []
        for ln in text.split('\n'):
            if ln.strip() == '//@AUDIO@':
                out.append(line)
            out.append(ln)
        return '\n'.join(out)
    raise ValueError('the level script has neither //@CROWD@ nor //@AUDIO@: no place for the crowd call')


def add_rows(lines, m, rows):
    """lines of the zone csv with rows inserted once after the level script row."""
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (m, m)
    present = set(l.strip() for l in lines)
    new = [r for r in rows if r not in present]
    if not new:
        return lines
    for i, l in enumerate(lines):
        if l.strip() == level_row:
            return lines[:i + 1] + new + lines[i + 1:]
    raise ValueError('no level script row (%s) in the zone csv' % level_row)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('root')
    ap.add_argument('map')
    ap.add_argument('--stock-xmodel', required=True)
    ap.add_argument('--model', default='police_officer_zombie')
    ap.add_argument('--name', default='iwz_crowd_cop')
    a = ap.parse_args(argv)
    m = a.map
    # the model
    data = open(os.path.join(a.stock_xmodel, a.model + '.xmb'), 'rb').read()
    out, removed = crowd_model.strip(data, a.model, a.name)
    dst = os.path.join(a.root, 'xmodel', a.name + '.xmb')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)          # may be a hard link into the stock dump: never write through it
    open(dst, 'wb').write(out)
    # the script
    rel = 'scripts/cp/maps/%s/%s_crowd.gsc' % (m, m)
    sdst = os.path.join(a.root, *rel.split('/'))
    os.makedirs(os.path.dirname(sdst), exist_ok=True)
    if os.path.exists(sdst):
        os.remove(sdst)
    shutil.copyfile(os.path.join(HERE, 'cp_iwz_crowd.gsc'), sdst)
    # the level script's call
    lvl = os.path.join(a.root, 'scripts', 'cp', 'maps', m, m + '.gsc')
    text = open(lvl, encoding='utf-8').read()
    patched = patch_level(text, m)
    if patched != text:
        os.remove(lvl)
        open(lvl, 'w', newline='\n', encoding='utf-8').write(patched)
    # the zone rows
    lines = open(a.csv, encoding='utf-8').read().split('\n')
    lines = add_rows(lines, m, ['rawfile,' + rel, 'xmodel,' + a.name])
    open(a.csv, 'w', newline='\n', encoding='utf-8').write('\n'.join(lines))
    print('crowd module: %s (copy of %s without %s), script %s, level call added' % (a.name, a.model, removed, rel))
    return 0


if __name__ == '__main__':
    sys.exit(main())
