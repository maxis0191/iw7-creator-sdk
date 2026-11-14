"""Put every localized string the map zone uses into the map zone itself (after assemble.py / add_perks.py).

A stock map gets its strings from its language zone (eng_cp_zmb.ff for Spaceland); a usermap built from the template
does not load that zone, so the stock interaction code shows raw keys (COOP_PERK_MACHINES_REMOVE_PERK). This tool
collects the keys the zone's own content references and writes them as one ZoneTool localize file.

ZoneTool for IW7 (x64-zt, src/zonetool/zonetool/iw7/zonetool.cpp, the zone csv loop; shared/assets/localize.hpp):
a row `localize,<name>` whose file <asset root>/localizedstrings/<name>.str exists is read by parse_localizedstrings_file,
else <name>.json by parse_localizedstrings_json, which adds one localize asset (LocalizeEntry name/value) per key of a
JSON object {"KEY": "text"}; the .str check runs first. JSON is used here because the .str parser cannot carry a '"'
inside a value (the perk hints quote their slogans). IW7 writes the entry name lower-cased (localize::write).

Keys are taken from the zone csv's own rows, each looked up in the strings sources (--strings, repeatable, a later one
wins: a {"KEY": "text"} JSON such as iw7-dump-lui/localize.json, or a directory of ZoneTool-dumped localize assets,
e.g. the localizedstrings folder of a dump of eng_cp_zmb):
- rawfile rows ending .gsc: every &"KEY" (a key not in the source is reported as missing);
- scriptfile rows: the compiled <asset root>/<name>.gscbin (zlib buffer), every string that is a source key;
- stringtable rows: every cell that is a source key;
- weapon / attachment rows: every JSON string value that is a source key (szDisplayName ...);
- --scripts DIR (repeatable): every &"KEY" in the .gsc files under DIR (e.g. the decompiled stock scripts);
- --extra FILE: a {"KEY": "text"} JSON of new strings, added as is (and overriding the source).

usage: add_localize.py <zone_source csv> <asset root (zonetool/<map>)> --strings <localize.json | dumped dir> ...
       [--name <map>] [--scripts DIR ...] [--extra new_strings.json] [--report keys.tsv]
The report lists written keys, &"KEY"s with no text (missing) and key-like strings of compiled scripts with no text
(suspect: the text exists only in a language zone not in the sources).
Stock files in the asset root may be hardlinks into the dumps: a file is always removed before it is written.
Running it again replaces its own file and row.
"""
import argparse, csv, io, json, os, re, struct, sys, zlib

ISTR = re.compile(r'&"([^"\\\r\n]+)"')
TOKEN = re.compile(rb'[A-Za-z][A-Za-z0-9_]{3,}')
SUSPECT = re.compile(r'^[A-Z][A-Z0-9]*_[A-Z0-9_]+$')
KEY = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')


def write_new(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)            # never write through a hardlink into a dump
    with open(path, 'w', newline='\n', encoding='utf-8') as f:
        f.write(data)


def gscbin_buffer(path):
    """the decompressed source/string buffer of a ZoneTool IW7 .gscbin (name\\0, three u32, zlib data)"""
    b = open(path, 'rb').read()
    z = b.find(b'\0') + 1 + 12
    for off in [z] + [m.start() for m in re.finditer(rb'\x78[\x01\x5e\x9c\xda]', b)]:
        try:
            return zlib.decompress(b[off:])
        except zlib.error:
            continue
    return b''


def load_strings(path):
    """{"KEY": "text"} from a JSON object, or from a directory of ZoneTool-dumped localize assets
    (localize::dump writes localizedstrings/<name> holding the raw value)"""
    if os.path.isdir(path):
        out = {}
        for f in os.listdir(path):
            p = os.path.join(path, f)
            if os.path.isfile(p) and '.' not in f:
                out[f] = open(p, 'rb').read().decode('utf-8', errors='replace')
        return out
    return json.load(open(path, encoding='utf-8'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('csv')
    ap.add_argument('root')
    ap.add_argument('--strings', action='append', required=True)   # repeatable; a later source wins
    ap.add_argument('--name', default='')          # default: the csv's base name (cp_iwz)
    ap.add_argument('--scripts', action='append', default=[])
    ap.add_argument('--extra', default='')
    ap.add_argument('--report', default='')
    a = ap.parse_args(argv)
    name = a.name or os.path.splitext(os.path.basename(a.csv))[0]
    source = {}
    for s in a.strings:
        source.update(load_strings(s))
    source = {k: v for k, v in source.items() if KEY.match(k)}       # the dump also holds junk names ('', '*95N_11')
    # iw7-dump-lui/localize.json was read from memory: some entries hold a stale pointer's bytes ('8�mC\x01');
    # such a key is treated as having no text (reported 'corrupt', not written)
    corrupt_src = {k for k, v in source.items() if '�' in v or any(ord(c) < 9 for c in v)}
    upper = {k.upper(): k for k in source}
    prefixes = {k.split('_', 1)[0].upper() for k in source if '_' in k}
    lines = open(a.csv, encoding='utf-8').read().splitlines()

    found, missing, origin, suspects, corrupt = {}, set(), {}, set(), set()

    def take(token, where, strict):
        # a compiled script or a table also holds plain strings: there only an exact upper-case KEY_WORD counts
        key = upper.get(token.upper()) if strict else (upper.get(token) if SUSPECT.match(token) else None)
        if key in corrupt_src:
            corrupt.add((key, where))
        elif key is not None:
            found.setdefault(key, source[key])
            origin.setdefault(key, where)
        elif strict:
            missing.add((token, where))
        elif SUSPECT.match(token) and token.split('_', 1)[0] in prefixes:
            suspects.add((token, where))     # looks like a key of a source family, but no source has it

    def scan_text_gsc(path, where):
        for k in ISTR.findall(open(path, encoding='utf-8', errors='replace').read()):
            take(k, where, True)

    unread = []
    for line in lines:
        kind, _, rest = line.partition(',')
        rest = rest.strip().lstrip(',')     # ",name" is ZoneTool's referenced-asset form
        if not rest:
            continue
        p = os.path.join(a.root, *rest.split('/'))
        if kind == 'rawfile' and rest.endswith('.gsc'):
            if os.path.exists(p):
                scan_text_gsc(p, rest)
            else:
                unread.append(rest)
        elif kind == 'scriptfile':
            if os.path.exists(p + '.gscbin'):
                for t in TOKEN.findall(gscbin_buffer(p + '.gscbin')):
                    take(t.decode('ascii'), 'scriptfile ' + rest, False)
            else:
                unread.append(rest)
        elif kind == 'stringtable':
            if os.path.exists(p):
                for row in csv.reader(io.StringIO(open(p, encoding='utf-8', errors='replace').read())):
                    for cell in row:
                        take(cell.strip(), rest, False)
            else:
                unread.append(rest)
        elif kind in ('weapon', 'attachment'):
            j = os.path.join(a.root, kind + 's', rest + '.json')
            if os.path.exists(j):
                for t in re.findall(r'"([A-Z][A-Z0-9_]{3,})"', open(j, encoding='utf-8', errors='replace').read()):
                    take(t, kind + ' ' + rest, False)
            else:
                unread.append(kind + ' ' + rest)
    for d in a.scripts:
        for base, _, files in os.walk(d):
            for f in files:
                if f.endswith('.gsc'):
                    scan_text_gsc(os.path.join(base, f), os.path.relpath(os.path.join(base, f), d))
    if a.extra:
        extra = json.load(open(a.extra, encoding='utf-8'))
        for k, v in extra.items():
            found[k] = v
            origin[k] = 'extra'
        missing = {m for m in missing if m[0] not in extra}

    out = os.path.join(a.root, 'localizedstrings', name + '.json')
    stale = os.path.join(a.root, 'localizedstrings', name + '.str')
    if os.path.exists(stale):
        os.remove(stale)           # ZoneTool reads <name>.str before <name>.json
    write_new(out, json.dumps(dict(sorted(found.items())), indent=1, ensure_ascii=True) + '\n')

    row = 'localize,' + name
    lines = [l for l in lines if l.strip() != row]
    lines.append(row)
    if os.path.exists(a.csv):
        os.remove(a.csv)
    with open(a.csv, 'w', newline='\n', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    suspects = {s for s in suspects if s[0] not in found}
    if a.report:
        write_new(a.report, ''.join('written\t%s\t%s\n' % (k, origin[k]) for k in sorted(found)) +
                  ''.join('missing\t%s\t%s\n' % m for m in sorted(missing)) +
                  ''.join('corrupt\t%s\t%s\n' % m for m in sorted(corrupt)) +
                  ''.join('suspect\t%s\t%s\n' % s for s in sorted(suspects)))
    print('add_localize: %d keys -> %s, row "%s"' % (len(found), out, row))
    for k, where in sorted(missing):
        print('  missing in strings source: %s (%s)' % (k, where))
    for k in sorted({c[0] for c in corrupt}):
        print('  corrupt text in strings source, not written: %s' % k)
    if suspects:
        print('  %d key-like strings in compiled scripts have no text in the sources (likely keys of the map\'s language '
              'zone, e.g. %s); --report lists them' % (len({s[0] for s in suspects}), sorted(suspects)[0][0]))
    if unread:
        print('  %d rows not in the asset root, not scanned (first: %s)' % (len(unread), ', '.join(unread[:5])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
