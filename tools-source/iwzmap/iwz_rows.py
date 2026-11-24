"""The rows of the generated tables of an emit, one function per row: the level script (`cp_iwz.gsc`: doors, zone links, wall prices, the
initial volume), the Station Zero test fixture (`iwzmap_sz2_local.gsc`: doors, probes) and `triggers.txt`.

Every writer of these tables calls them: `scenegen.Emitter.level_script` (a scene, a Blender or Studio document), `station_zero2.py`
(the Station Zero generator) and Studio's merge of a layer into a base emit (`studio/basegame.py`), which parses a base's table, checks
that these functions give its rows back byte for byte, and appends rows made by the same functions. `table()` and `rows_of()` are the
two directions of one table block between the line a template's `//@NAME@` marker stood on and the rest of the script.
"""
import re


def door_row(d):
    """level script //@DOORS@: a door of layout.json `doors` {name, target, axis (0: plane x, 1: plane y), plane, lo, hi, z0, z1}"""
    return '    doors[doors.size] = iwz_door( "%s", "%s", %d, %g, %g, %g, %g, %g );' % (
        d['name'], d['target'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1'])


def link_row(pair):
    """level script //@LINKS@: two spawn volumes joined without a door"""
    return '    links[links.size] = [ "%s", "%s" ];' % tuple(pair)


def price_row(origin, weapon, price):
    """level script //@PRICES@ (cp_iwz3.gsc): the price of a wall weapon at one place"""
    return '    table[table.size] = iwz_price( ( %g, %g, %g ), "%s", %d );' % (float(origin[0]), float(origin[1]), float(origin[2]), weapon, int(price))


def initial_row(names):
    """level script //@INITIAL@: the volumes active at the start"""
    return 'level.initial_active_volumes = [ %s ];' % ', '.join('"%s"' % z for z in names)


def fixture_door_row(d):
    """iwzmap_sz2_local.gsc //@DOORS@: a door for the fixture's door probes (no target)"""
    return '    doors[doors.size] = iwz_door( "%s", %d, %g, %g, %g, %g, %g );' % (d['name'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1'])


def fixture_probe_row(zone, x, y, z):
    """iwzmap_sz2_local.gsc //@PROBES@: a point of a navigation region, 40 above its floor"""
    return '    probes[probes.size] = iwz_probe( "%s", %g, %g, %g );' % (zone, x, y, z)


def trigger_row(box):
    """triggers.txt: the half extents of a volume box [x0, y0, z0, x1, y1, z1] (line k is the trigger model ?IWZ<k>)"""
    x0, y0, z0, x1, y1, z1 = box
    return '28000001 %g %g %g' % ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)


def table(rows, strip=False):
    """the text a `//@NAME@` marker is replaced with (the marker stands after four spaces; `strip` for the markers whose writer strips the
    first row's indent)"""
    t = '\n'.join(rows)
    return t.lstrip() if strip else t


ROW = {
    'doors': re.compile(r'^\s*doors\[doors\.size\] = iwz_door\('),
    'links': re.compile(r'^\s*links\[links\.size\] = \['),
    'prices': re.compile(r'^\s*table\[table\.size\] = iwz_price\('),
    'probes': re.compile(r'^\s*probes\[probes\.size\] = iwz_probe\('),
}
INITIAL = re.compile(r'^(\s*)level\.initial_active_volumes = \[ (.*) \];$')


def rows_of(text, kind):
    """(first line index, last line index + 1, rows) of the table `kind` in a generated script: its consecutive row lines, each as the row
    functions write it (four spaces of indent, whatever the first line carries). No row: (None, None, [])"""
    lines = text.split('\n')
    rx = ROW[kind]
    idx = [i for i, l in enumerate(lines) if rx.match(l)]
    if not idx:
        return None, None, []
    if idx != list(range(idx[0], idx[-1] + 1)):
        raise ValueError('the %s rows of the script are not one block (lines %d to %d)' % (kind, idx[0] + 1, idx[-1] + 1))
    return idx[0], idx[-1] + 1, ['    ' + lines[i].strip() for i in idx]


def with_rows(text, kind, rows, anchor=None, strip=False):
    """the script with the table `kind` holding `rows`. A script whose table is empty gets them on the blank line that follows `anchor`
    (the line before the marker in the template, e.g. '    doors = [];')"""
    lines = text.split('\n')
    a, b, old = rows_of(text, kind)
    if a is None:
        if not rows:
            return text
        if anchor is None or anchor not in lines:
            raise ValueError('the script has no %s table (no row, and no line %r)' % (kind, anchor))
        a = lines.index(anchor) + 1
        if lines[a].strip():
            raise ValueError('the script has no empty %s table after %r' % (kind, anchor))
        b = a + 1
        lead = lines[a]
    else:
        n = len(lines[a]) - len(lines[a].lstrip())
        lead = lines[a][:n if strip else n - 4]
    block = (lead + table(rows, strip)).split('\n') if rows else [lead]
    return '\n'.join(lines[:a] + block + lines[b:])
