"""EXPERIMENT, not wired into any build script: split an assembled zone csv into a base zone and a small map zone.

usage: split_zone.py <work> <map> --base <base zone> --stock-csv <dump csv> [--stock-csv ...] [--junction]

Reads <work>/zone_source/<map>.csv (the csv build-sz2.ps1 / build-blend.ps1 leave after the assembly, before -buildzone) and writes
    <work>/zone_source/<base>.csv   header, the require rows, every row whose asset is stock content
    <work>/zone_source/<map>.csv    header, `ignore,<base>`, the require rows, everything else (the map's own rows, in the old order)
    <work>/zone_source/<map>.full.csv   the csv as it was (the monolithic build is one `zonetool -buildzone <map>` away again)
With --junction, <work>/zonetool/<base> is made a directory junction to <work>/zonetool/<map>: both zones read the same asset tree.

Why it can work with no change to ZoneTool: `ignore,<zone>` (zonetool.cpp parse_csv_file_ignore) puts every (type, name) row of that
zone's csv into ZoneTool's ignore set, and zone_interface::add_asset_of_type writes an asset of the set as a reference (`,name`)
instead of its data, also when a map asset pulls it in as a dependency (load_depending). That is how the stock patch zones
reference the zone they patch. What it needs at run time is the base zone loaded before the map zone: docs/MAP-BUILD-LOOP.md.

Stock content = a row whose (type, name) is a row of a stock dump csv, written in full (`type,name`) or as a reference (`type,,name`):
the dumps the assembly links (patch_cp_zmb, cp_zmb, techsets_cp_zmb, techsets_global_cp, techsets_global) and the kit dumps.
Map-owned = a world type, a name that holds the map's name, a level netconststrings list, the sound bank, the localized strings,
and everything not in a stock csv (custom materials and their images, the perk module's icons, kit models of a kit not given).
Rows of the form `type,,name` (references to a zone the game loads) go to both csvs.
"""
import os
import subprocess
import sys

MAP_TYPES = {'com_map', 'navmesh', 'fx_map', 'gfx_map', 'map_ents', 'glass_map', 'aipaths', 'col_map', 'gfx_map_trzone',
             'streaminginfo', 'impactfx', 'soundbank', 'netconststrings', 'localize', 'gfxlightmap'}


def read_stock(csvs):
    stock = set()
    for path in csvs:
        for ln in open(path, errors='replace'):
            q = ln.strip().split(',')
            if q[0] in ('require', 'include', 'ignore', 'addpath', 'addpaths', 'reference', 'iterate'):
                continue
            if len(q) == 2 and q[0] and q[1]:
                stock.add((q[0], q[1]))
            elif len(q) == 3 and q[0] and not q[1] and q[2]:       # type,,name: the dump's zone references it, the asset is a stock one
                stock.add((q[0], q[2]))
    return stock


def classify(lines, stock, map_name):
    """Returns (header and require lines, rows of the base zone, rows of the map zone), each in the old order.
    A reference row (`type,,name`) goes to both: it costs no data, and it is what makes an asset that either zone pulls in a reference."""
    common, base, own = [], [], []
    for ln in lines:
        q = ln.strip().split(',')
        if not ln.strip() or ln.lstrip().startswith(('//', '#')) or q[0] == 'require':
            common.append(ln)
        elif len(q) == 2:
            if q[0] in MAP_TYPES or map_name in q[1] or (q[0], q[1]) not in stock:
                own.append(ln)
            else:
                base.append(ln)
        else:
            base.append(ln)
            own.append(ln)
    return common, base, own


def split(work, map_name, base, stock_csvs):
    src = os.path.join(work, 'zone_source', map_name + '.csv')
    full = os.path.join(work, 'zone_source', map_name + '.full.csv')
    already = any(l.startswith('ignore,') for l in open(src, errors='replace').read().splitlines()[:4])
    if already and os.path.exists(full):
        pass                                # the csv is the result of an earlier split: start from the full copy again
    else:
        os.replace(src, full)               # a csv from a new assembly: it becomes the full copy
    lines = open(full, errors='replace').read().splitlines()
    common, base_rows, own_rows = classify(lines, read_stock(stock_csvs), map_name)
    write = lambda p, rows: open(p, 'w', newline='\n').write('\n'.join(rows) + '\n')
    head = [l for l in common if l.strip().startswith(('//', '#'))][:1]
    req = [l for l in common if l.strip().startswith('require,')]
    write(os.path.join(work, 'zone_source', base + '.csv'), head + req + base_rows)
    write(src, head + ['ignore,' + base] + req + own_rows)
    return len(base_rows), len(own_rows)


def junction(work, map_name, base):
    link, target = os.path.join(work, 'zonetool', base), os.path.join(work, 'zonetool', map_name)
    if os.path.lexists(link):
        return
    subprocess.run(['cmd', '/c', 'mklink', '/J', link, target], check=True, capture_output=True)


def main(argv):
    if len(argv) < 2 or '--base' not in argv:
        sys.stderr.write(__doc__)
        return 2
    work, map_name = argv[0], argv[1]
    base = argv[argv.index('--base') + 1]
    stock = [argv[i + 1] for i, a in enumerate(argv) if a == '--stock-csv']
    nb, nm = split(work, map_name, base, stock)
    if '--junction' in argv:
        junction(work, map_name, base)
    print('split_zone: %d rows to %s, %d rows stay in %s (ignore,%s first)' % (nb, base, nm, map_name, base))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
