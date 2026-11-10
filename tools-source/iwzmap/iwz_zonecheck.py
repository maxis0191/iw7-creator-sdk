#!/usr/bin/env python3
"""Map zone check: is everything that was built really listed and really present, and is the compiled file
newer than what it was built from?

The map pipeline goes: generator -> emitted files -> compile step -> source list (csv) + source tree -> ZoneTool ->
<zone>.ff.  iwz_emitcheck.py opens three emitted files; nothing checked the stretch between "emitted" and "packed".
This tool reads that stretch from files only.  It never judges how the map looks.

Work folder (a ZoneTool work directory):
    zone_source/<zone>.csv        the source list: one `type,name` row per asset (`type,,name` = reference to a
                                  required zone, nothing to pack from the tree)
    zonetool/<zone>/              the source tree: one folder per asset type
    zone/<zone>.ff                the compiled file

Report shape (schema iw7.content-audit/1) is the one the other content audits write, so one reader handles all of
them.  Severity: error = the files prove it is broken; warn = somebody must look; info = counts and what was not
checked.  Exit code 1 with errors; with --strict 2 while a warning stands.  Standard library only.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

TOOL = 'map-zone-check'
SCHEMA = 'iw7.content-audit/1'
SEVERITIES = ('error', 'warn', 'info')
PROOFS = ('data', 'engine')
ORDER = {s: i for i, s in enumerate(SEVERITIES)}
QUESTION_KINDS = ('see', 'hear', 'time', 'load')
SHOW = 10                      # how many names a finding lists before saying "and N more"

# Rows that steer the build and are not assets (ZoneTool parse_csv_file).
DIRECTIVES = ('require', 'include', 'ignore', 'reference', 'iterate', 'addpath', 'addpaths')

# ---------------------------------------------------------------------------------------------------------------
# FORMAT FACTS.  Each line was established twice: the file names ZoneTool builds from the row name (its
# assets/*.cpp `name + ".ext"` lines) and the real tree against the real csv (every row of the kind found its file
# under exactly this rule on the working cp_iwz work folder).  {n} is the row name with '/' separators.
#
# kind -> (required templates, optional companions).  Required absent = the row cannot be built.
# ---------------------------------------------------------------------------------------------------------------
MAP_KINDS = collections.OrderedDict([
    ('gfx_map', (('{n}.gfxmap',), ())),
    ('gfx_map_trzone', (('transient_zones/{n}.gfxmap_tr',), ())),
    ('col_map', (('{n}.colmap', '{n}.colmap.hkx'), ())),
    ('com_map', (('{n}.commap.json',), ())),
    ('fx_map', (('{n}.fxmap',), ())),
    ('glass_map', (('{n}.glassmap',), ())),
    ('navmesh', (('{n}.navmesh',), ())),
    ('map_ents', (('{n}.ents', '{n}.ents.data'),
                  ('{n}.ents.data.hkx', '{n}.ents.spawnList.json', '{n}.ents.spawners'))),
    ('aipaths', (('{n}.aipaths',), ())),
    ('gfxlightmap', (('lightmaps/{c}.json',), ())),     # {c}: '*' becomes '_' (gfxlightmap.cpp clean_name)
])
REQUIRED_KINDS = ('gfx_map', 'col_map', 'com_map', 'map_ents')

# Suffixes of files `<zone>.d3dbsp<suffix>` under maps/ and what kind they belong to.
MAP_SUFFIX = {
    '.gfxmap': 'gfx_map', '.colmap': 'col_map', '.colmap.hkx': 'col_map', '.commap.json': 'com_map',
    '.fxmap': 'fx_map', '.glassmap': 'glass_map', '.navmesh': 'navmesh', '.ents': 'map_ents',
    '.ents.data': 'map_ents', '.ents.data.hkx': 'map_ents', '.ents.spawnList.json': 'map_ents',
    '.ents.spawners': 'map_ents', '.aipaths': 'aipaths',
}

# Other asset types: type -> templates (any one present is enough).  Established the same way (all rows of the type
# on the real work folder resolved), with the engine's folder names.
TYPE_RULES = {
    'animclass': ('animclass/{n}',), 'animpkg': ('animpkg/{n}.json',), 'attachment': ('attachments/{n}.json',),
    'behaviortree': ('behaviortree/{n}.json',), 'gesture': ('gesture/{n}.json',),
    'image': ('images/{n}.iw7Image', 'images/{n}.dds', 'images/{n}.tga'),
    'impactfx': ('impactfx/{n}.json',), 'laser': ('laser/{n}.json',), 'lightdef': ('lights/{n}.json',),
    'material': ('materials/{n}.json',), 'netconststrings': ('netconststrings/{n}.json',),
    'particlesimanimation': ('particlesimanimation/{n}.psa',), 'physicsasset': ('physicsasset/{n}',),
    'physicsfxpipeline': ('physicsfxpipeline/{n}',), 'physicsfxshape': ('physicsfxshape/{n}',),
    'rawfile': ('{n}',), 'reticle': ('reticle/{n}.json',), 'rumble': ('rumble/{n}.json',),
    'rumblegraph': ('rumble_graph/{n}.json',), 'scriptable': ('scriptable/{n}',),
    'scriptfile': ('{n}.gscbin', '{n}.gsc'), 'sfxpkg': ('sfxpkg/{n}.json',),
    'soundbank': ('sound/{n}.aliases.csv', 'soundbank/{n}.json'), 'streaminginfo': ('streaming_info/{n}',),
    'stringtable': ('{n}',), 'techset': ('techsets/{n}.techset',), 'tracer': ('tracer/{n}.json',),
    'vfx': ('particlesystem/{n}.iw7VFX',), 'vfxpkg': ('vfxpkg/{n}.json',), 'weapon': ('weapons/{n}.json',),
    'xanim': ('xanim/{n}.xab',), 'xmodel': ('xmodel/{n}.xmb',), 'xmodelsurfs': ('xsurface/{n}.xsb',),
    'pixelshader': ('techsets/ps/{n}.cso',), 'vertexshader': ('techsets/vs/{n}.cso',),
}
GENERATED_PREFIX = '*'          # image names the engine makes itself (lightmap atlases): no source file exists

# Emitted file -> tree file that must carry the same bytes.  Only colmap.hkx is byte-identical after the compile
# step (compared on a real emit folder and the real tree: every other emitted file is converted).
EMIT_SAME = (('colmap.hkx', 'col_map', '{n}.colmap.hkx'),)


# ------------------------------------------------------------------ report (same shape as the other audits)
class Report:
    """Findings and engine questions of one run."""

    def __init__(self, tool, target):
        self.tool, self.target = tool, target
        self.findings, self.questions, self.facts = [], [], {}

    def add(self, severity, code, asset, message, notice=None, proof='data', source=None, **evidence):
        if severity not in SEVERITIES or proof not in PROOFS:
            raise ValueError('bad severity or proof: %r %r' % (severity, proof))
        finding = {'severity': severity, 'code': code, 'asset': asset, 'message': message, 'proof': proof}
        if notice:
            finding['notice'] = notice
        if source:
            finding['source'] = source
        if evidence:
            finding['evidence'] = evidence
        self.findings.append(finding)
        return finding

    def ask(self, kind, asset, question, why, **how):
        if kind not in QUESTION_KINDS:
            raise ValueError('bad question kind: %r' % kind)
        entry = {'kind': kind, 'asset': asset, 'question': question, 'why': why}
        if how:
            entry['how'] = how
        if entry not in self.questions:
            self.questions.append(entry)

    def counts(self):
        return {s: sum(1 for f in self.findings if f['severity'] == s) for s in SEVERITIES}

    def sorted_findings(self):
        return sorted(self.findings, key=lambda f: (ORDER[f['severity']], f['code'], f['asset']))

    def as_dict(self):
        return {'schema': SCHEMA, 'tool': self.tool, 'target': self.target, 'counts': self.counts(),
                'findings': self.sorted_findings(), 'engine_questions': self.questions, 'facts': self.facts}

    def write_text(self, stream=None):
        stream = stream or sys.stdout
        counts = self.counts()
        for f in self.sorted_findings():
            tail = '  [only the engine can confirm]' if f['proof'] == 'engine' else ''
            also = (f.get('evidence') or {}).get('also') or ()
            asset = f['asset'] + (' (+%d: %s)' % (len(also), ', '.join(also)) if also else '')
            stream.write('  %-5s %s  %s: %s%s\n' % (f['severity'].upper(), f['code'], asset, f['message'], tail))
            if f.get('notice'):
                stream.write('        player: %s\n' % f['notice'])
            if f.get('answered'):
                stream.write('        answered: %s\n' % f['answered'])
        stream.write('%s %s: errors %d, warnings %d, notes %d, engine questions %d\n' % (
            self.tool, self.target, counts['error'], counts['warn'], counts['info'], len(self.questions)))

    def exit_code(self, strict=False):
        counts = self.counts()
        return 1 if counts['error'] else (2 if strict and counts['warn'] else 0)


def finish(report, args, stream=None):
    report.write_text(stream)
    if getattr(args, 'json', None):
        with open(args.json, 'w', encoding='utf-8') as handle:
            json.dump(report.as_dict(), handle, indent=1, sort_keys=True)
    return report.exit_code(getattr(args, 'strict', False))


# ------------------------------------------------------------------ helpers
def first(items, limit=SHOW):
    items = list(items)
    text = ', '.join(items[:limit])
    return text + (' and %d more' % (len(items) - limit) if len(items) > limit else '')


def norm(name):
    return name.replace('\\', '/')


def fill(template, name):
    """Template with {n} (row name) and {c} (row name with '*' as '_')."""
    return template.replace('{n}', name).replace('{c}', name.replace('*', '_'))


def stamp(seconds):
    import time
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))


def index_tree(base):
    """{lowercase relative path: real relative path} of every file below base (one walk; no per row stat)."""
    out = {}
    stack = [(base, '')]
    while stack:
        here, rel = stack.pop()
        try:
            with os.scandir(here) as it:
                for entry in it:
                    path = rel + entry.name
                    if entry.is_dir(follow_symlinks=False):
                        stack.append((entry.path, path + '/'))
                    else:
                        out[path.lower()] = path
        except OSError:
            continue
    return out


def read_rows(csv_path):
    """([(type, name, is_reference)], {directive: count}, comment_or_blank_count) as ZoneTool reads the list."""
    rows, directives, referencing = [], collections.Counter(), False
    with open(csv_path, encoding='utf-8', errors='replace') as handle:
        for line in handle:
            fields = line.rstrip('\r\n').split(',')
            head = fields[0]
            if not head or head[0] == '#' or head.startswith('//'):
                continue
            if head in DIRECTIVES:
                directives[head] += 1
                if head == 'reference' and len(fields) >= 2:
                    referencing = fields[1] == 'true'
                continue
            if len(fields) < 2:
                continue
            if not fields[1] and len(fields) > 2 and fields[2]:
                rows.append((head, norm(fields[2]), True))      # `type,,name`: reference to a required zone
            elif fields[1]:
                rows.append((head, norm(fields[1]), referencing))
    return rows, directives


def stock_indexes(paths):
    """[(zone name, {lowercase path: real}, {(type, name)})] for dump zone folders; a folder of zone folders is
    expanded.  The set is read from the dump's own <zone>.csv, which lists assets the dump writes no file for."""
    known = set(f.split('/')[0] for t in TYPE_RULES.values() for f in t if '/' in f) | {'maps'}
    zones = []
    for path in paths:
        if not os.path.isdir(path):
            continue
        children = [e for e in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, e))]
        own = os.path.join(path, os.path.basename(os.path.normpath(path)) + '.csv')
        if any(c in known for c in children) or os.path.isfile(own):
            zones.append((os.path.basename(os.path.normpath(path)), path))
        else:
            zones.extend((c, os.path.join(path, c)) for c in children)
    out = []
    for name, path in zones:
        listed = set()
        csv_file = os.path.join(path, name + '.csv')
        if os.path.isfile(csv_file):
            rows, _d = read_rows(csv_file)
            listed = {(k, n.lower()) for k, n, _r in rows}
        out.append((name, index_tree(path), listed))
    return out


def has_file(index, templates, name):
    return any(fill(t, name).lower() in index for t in templates)


# ------------------------------------------------------------------ entity file
ENT_PAIR = re.compile(r'^(\S+)\s+"(.*)"$')
CLASSNAME_KEYS = ('classname', '157')    # 157 is the key the compile step writes for classname (every block of the
                                         # real tree and of the stock cp_zmb entity file carries it)


def read_entities(path):
    """(count, Counter of classnames) of a plain text entity file, or (None, reason)."""
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            text = handle.read().replace('\x00', '')
    except OSError as exc:
        return None, str(exc)
    count, classes, current, missing = 0, collections.Counter(), None, 0
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line == '{':
            if current is not None:
                return None, 'line %d: block inside a block' % number
            current = {}
        elif line == '}':
            if current is None:
                return None, 'line %d: closing brace without a block' % number
            count += 1
            name = next((current[k] for k in CLASSNAME_KEYS if k in current), None)
            if name is None:
                missing += 1
            else:
                classes[name] += 1
            current = None
        else:
            pair = ENT_PAIR.match(line)
            if current is None or not pair:
                return None, 'line %d: not a key "value" pair inside a block' % number
            current[pair.group(1)] = pair.group(2)
    if current is not None:
        return None, 'the last block is never closed'
    if count == 0:
        return None, 'no entity block found'
    if missing:
        classes['(no classname key)'] = missing
    return count, classes


# ------------------------------------------------------------------ collision reuse
def collision_loader(path):
    """Decode a colmap.hkx with the reader of iwz_emitcheck.py: returns the triangle count, raises on failure."""
    import iwz_emitcheck as emitcheck
    tris = emitcheck.load_tris(path)
    if not tris:
        raise ValueError('the collision decodes to no triangles')
    return len(tris)


# ------------------------------------------------------------------ the audit
def audit(work, zone, emit=None, stock=None):
    """Return a Report for a ZoneTool work folder and zone name. No printing, no exit."""
    work = os.path.abspath(work)
    report = Report(TOOL, '%s (%s)' % (zone, work))
    csv_path = os.path.join(work, 'zone_source', zone + '.csv')
    tree = os.path.join(work, 'zonetool', zone)
    ff_path = os.path.join(work, 'zone', zone + '.ff')
    report.facts['paths'] = {'source_list': csv_path, 'tree': tree, 'compiled': ff_path}
    ok = True
    if not os.path.isfile(csv_path):
        report.add('error', 'MAP-LIST-MISSING', zone, 'the source list %s does not exist' % csv_path,
                   notice='there is nothing to build the map from')
        ok = False
    if not os.path.isdir(tree):
        report.add('error', 'MAP-TREE-MISSING', zone, 'the source tree %s does not exist' % tree,
                   notice='there is nothing to build the map from')
        ok = False
    if not ok:
        return report

    rows, directives = read_rows(csv_path)
    report.facts['rows'] = {'assets': len(rows), 'directives': dict(directives)}
    index = index_tree(tree)
    report.facts['tree_files'] = len(index)

    map_rows = collections.defaultdict(list)          # kind -> [name]
    for kind, name, ref in rows:
        if kind in MAP_KINDS and not ref:
            map_rows[kind].append(name)

    expected = {}                                     # lowercase path -> (kind, row name) of every built file
    kinds_table = {}
    present_map_files = {}                            # lowercase path -> real path (files that exist and belong)
    # ---- M2 required kinds, M1 listed but absent
    for kind, (required, optional) in MAP_KINDS.items():
        names = map_rows.get(kind, [])
        entry = kinds_table[kind] = {'rows': len(names), 'required': list(required), 'optional': list(optional),
                                     'missing': []}
        if not names:
            if kind in REQUIRED_KINDS:
                report.add('error', 'MAP-KIND-MISSING', kind,
                           'no row of kind %s in %s: the compiled map has no %s' % (kind, os.path.basename(csv_path), kind),
                           notice='the map lacks a part it cannot run without',
                           csv=csv_path)
            else:
                report.add('info', 'MAP-KIND-MISSING', kind,
                           'no row of kind %s: the compiled map has none (this tool treats the kind as optional)' % kind)
            continue
        for name in names:
            for template in required + optional:
                path = fill(template, name)
                expected[path.lower()] = (kind, name, template in optional)
                if path.lower() in index:
                    present_map_files[path.lower()] = index[path.lower()]
            lost = [fill(t, name) for t in required if fill(t, name).lower() not in index]
            if lost:
                entry['missing'].extend(lost)
                report.add('error', 'MAP-ROW-NO-FILE', '%s %s' % (kind, name),
                           'listed as %s %s but %s not in the tree' % (
                               kind, name, ', '.join(lost) + (' is' if len(lost) == 1 else ' are')),
                           notice='the map lists a part that was never built: the build fails or the game loads a broken map',
                           missing=lost)
    report.facts['kinds'] = kinds_table

    unknown_kinds = sorted({k for k, _n, _r in rows if (k.endswith('_map') or k.endswith('_trzone'))
                            and k not in MAP_KINDS})
    for kind in unknown_kinds:
        report.add('info', 'MAP-KIND-NOT-CHECKED', kind,
                   'rows of kind %s exist but this tool does not know which files they need' % kind)

    # ---- M1b built but not listed; files that belong to no kind
    lowzone = zone.lower()
    packed_prefix = lowzone + '.d3dbsp'
    not_packed, unknown_files, other_zone = [], [], []
    for lower, real in index.items():
        top = lower.split('/')[0]
        base = lower.rsplit('/', 1)[-1]
        if top == 'maps':
            if not base.startswith(packed_prefix + '.'):
                if '.d3dbsp.' in base:
                    other_zone.append(real)
                continue
            suffix = base[len(packed_prefix):]
            kind = next((k for s, k in MAP_SUFFIX.items() if s.lower() == suffix), None)
            if kind is None:
                unknown_files.append(real)
            elif lower not in expected:
                not_packed.append((kind, real))
        elif top == 'transient_zones':
            if base == lowzone + '.gfxmap_tr' and lower not in expected:
                not_packed.append(('gfx_map_trzone', real))
        elif top == 'lightmaps' and base.endswith('.json') and lower not in expected:
            not_packed.append(('gfxlightmap', real))
    for kind, real in sorted(not_packed):
        report.add('error', 'MAP-FILE-NOT-PACKED', real,
                   'map file %s (kind %s) is in the tree but no %s row names it' % (real, kind, kind),
                   notice='a part of the map was built but is left out of the compiled file')
    if unknown_files:
        report.add('info', 'MAP-FILE-UNKNOWN', 'maps',
                   '%d file(s) of this zone in the map folder belong to no kind this tool knows: %s' % (
                       len(unknown_files), first(sorted(unknown_files))), files=sorted(unknown_files))
    if other_zone:
        report.add('info', 'MAP-FILE-OTHER-ZONE', 'maps',
                   '%d map file(s) of another zone sit in the tree and are not part of %s (left from the template): %s' % (
                       len(other_zone), zone, first(sorted(other_zone))), count=len(other_zone))
    report.facts['map_files'] = sorted(present_map_files.values())

    # ---- M3 empty or unreadable, entity count
    ents_path = None
    for lower, real in sorted(present_map_files.items()):
        full = os.path.join(tree, real.replace('/', os.sep))
        try:
            size = os.path.getsize(full)
        except OSError:
            continue
        if size == 0:
            report.add('error', 'MAP-FILE-EMPTY', real, '%s has size 0' % real,
                       notice='a part of the map is an empty file: the build fails or the part is missing in game')
            continue
        if lower.endswith('.json'):
            try:
                with open(full, encoding='utf-8') as handle:
                    json.load(handle)
            except (ValueError, OSError) as exc:
                report.add('error', 'MAP-FILE-UNREADABLE', real, '%s is not valid JSON: %s' % (real, exc),
                           notice='a part of the map cannot be read: the build fails or the part is missing in game')
        if lower.endswith('.ents') and expected[lower][0] == 'map_ents' and ents_path is None:
            ents_path = full
    if ents_path:
        count, detail = read_entities(ents_path)
        if count is None:
            report.add('info', 'MAP-ENTS-NOT-READ', os.path.basename(ents_path),
                       'the entity file is not the plain text format this tool reads (%s)' % detail)
        else:
            top = detail.most_common(20)
            report.facts['entities'] = {'count': count, 'classnames': len(detail),
                                        'top20': [[k, v] for k, v in top]}

    # ---- M4 duplicate rows
    seen, dupes = collections.Counter(), []
    for kind, name, ref in rows:
        seen[(kind, name, ref)] += 1
    dupes = ['%s,%s%s (x%d)' % (k, '' if not r else ',', n, c) for (k, n, r), c in seen.items() if c > 1]
    if dupes:
        report.add('warn', 'MAP-ROW-DUPLICATE', os.path.basename(csv_path),
                   '%d row(s) appear more than once: %s' % (len(dupes), first(dupes)),
                   notice='the same part is packed twice: the compiled file is larger than it needs to be',
                   count=len(dupes), first=dupes[:SHOW])

    # ---- M5 other asset types
    types = collections.OrderedDict()
    missing_by = collections.defaultdict(list)
    ref_by = collections.defaultdict(list)
    untouched = collections.Counter()
    for kind, name, ref in rows:
        if kind in MAP_KINDS:
            continue
        rule = TYPE_RULES.get(kind)
        if rule is None:
            untouched[kind] += 1
            continue
        entry = types.setdefault(kind, {'rows': 0, 'with_file': 0, 'without_file': 0, 'reference': 0, 'generated': 0})
        entry['rows'] += 1
        if kind == 'image' and name.startswith(GENERATED_PREFIX):
            entry['generated'] += 1
        elif ref:
            entry['reference'] += 1
            ref_by[kind].append(name)
        elif has_file(index, rule, name):
            entry['with_file'] += 1
        else:
            entry['without_file'] += 1
            missing_by[kind].append(name)
    stock_zones = stock_indexes(stock or [])
    if stock_zones:
        report.facts['stock_zones'] = [z[0] for z in stock_zones]
    elif missing_by or ref_by:
        report.add('info', 'MAP-NO-STOCK', zone,
                   'no --stock given: %d row(s) without a file in the tree and %d reference row(s) were not looked up '
                   'in stock' % (sum(len(v) for v in missing_by.values()), sum(len(v) for v in ref_by.values())))
    for kind in list(types):
        entry = types[kind]
        for label, names in (('', missing_by.get(kind, [])), (' (reference)', ref_by.get(kind, []))):
            if not names or not stock_zones:
                continue
            found = [n for n in names if any(has_file(i, TYPE_RULES[kind], n) or (kind, n.lower()) in listed
                                             for _z, i, listed in stock_zones)]
            nowhere = [n for n in names if n not in set(found)]
            entry['found_in_stock' + ('_reference' if label else '')] = len(found)
            entry['not_found' + ('_reference' if label else '')] = len(nowhere)
            if nowhere:
                report.add('info', 'MAP-ROW-NOT-FOUND', kind + label,
                           '%d %s row(s) have no file in the tree%s and none in the stock dump (the dump is partial, '
                           'the build log is the proof): %s' % (
                               len(nowhere), kind, ' (they only reference a required zone)' if label else '',
                               first(nowhere)),
                           count=len(nowhere), first=nowhere[:SHOW])
    for kind, count in sorted(untouched.items()):
        types.setdefault(kind, {'rows': 0})['rows'] = count
    if untouched:
        report.add('info', 'MAP-TYPE-NOT-CHECKED', 'types',
                   'no file rule for %d asset type(s), their %d row(s) were not checked: %s' % (
                       len(untouched), sum(untouched.values()),
                       ', '.join('%s (%d)' % kv for kv in sorted(untouched.items()))))
    report.facts['types'] = types

    # ---- M6 freshness
    if not os.path.isfile(ff_path):
        report.add('info', 'MAP-FF-MISSING', zone, 'there is no compiled file %s' % ff_path)
    else:
        ff_time = os.path.getmtime(ff_path)
        newer = []
        sources = [('source list', csv_path)] + [
            (real, os.path.join(tree, real.replace('/', os.sep))) for real in sorted(present_map_files.values())]
        for label, path in sources:
            try:
                seconds = os.path.getmtime(path)
            except OSError:
                continue
            if seconds > ff_time:
                newer.append('%s (%s)' % (label, stamp(seconds)))
        report.facts['compiled_time'] = stamp(ff_time)
        if newer:
            report.add('warn', 'MAP-FF-OLDER-THAN-SOURCE', os.path.basename(ff_path),
                       'compiled %s is older than %d source(s): %s' % (stamp(ff_time), len(newer), first(newer)),
                       notice='the compiled map is older than its sources: the game is not running what was last built',
                       newer=newer)

    # ---- M7 emitted against packed
    if emit:
        emit = os.path.abspath(emit)
        files = sorted(e for e in os.listdir(emit) if os.path.isfile(os.path.join(emit, e))) if os.path.isdir(emit) else []
        related = set()
        for emitted, kind, template in EMIT_SAME:
            if emitted not in files:
                continue
            related.add(emitted)
            for name in map_rows.get(kind, []):
                real = index.get(fill(template, name).lower())
                if real is None:
                    continue        # a missing tree file is already MAP-ROW-NO-FILE
                if not same_bytes(os.path.join(emit, emitted), os.path.join(tree, real.replace('/', os.sep))):
                    report.add('error', 'MAP-EMIT-NOT-PACKED', real,
                               '%s differs from the emitted %s in %s' % (real, emitted, emit),
                               notice='the collision in the tree is not the one last emitted',
                               emitted=os.path.join(emit, emitted))
        rest = [f for f in files if f not in related]
        if rest:
            report.add('info', 'MAP-EMIT-NOT-RELATED', os.path.basename(emit),
                       '%d emitted file(s) are converted by the compile step, so no tree file can be compared byte '
                       'for byte: %s' % (len(rest), first(rest)), files=rest)
        if not files:
            report.add('info', 'MAP-EMIT-NOT-RELATED', os.path.basename(emit), 'the emit folder holds no files')

    # ---- M8 collision through the existing reader
    for name in map_rows.get('col_map', []):
        real = index.get(fill('{n}.colmap.hkx', name).lower())
        if real is None:
            continue
        path = os.path.join(tree, real.replace('/', os.sep))
        if os.path.getsize(path) == 0:
            continue                # already MAP-FILE-EMPTY
        try:
            count = collision_loader(path)
        except ImportError as exc:
            report.add('info', 'MAP-COLLISION-NOT-CHECKED', real,
                       'the reader iwz_emitcheck.py could not be loaded (%s)' % exc)
        except Exception as exc:        # the reader raises whatever the packfile decoder raises
            report.add('error', 'MAP-COLLISION-INVALID', real, '%s: %s' % (type(exc).__name__, exc),
                       notice='the collision of the map cannot be read: players fall through or the build fails')
        else:
            report.facts.setdefault('collision', {})[real] = {'triangles': count}
    return report


def same_bytes(a, b, block=1 << 20):
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, 'rb') as fa, open(b, 'rb') as fb:
        while True:
            x, y = fa.read(block), fb.read(block)
            if x != y:
                return False
            if not x:
                return True


def kind_table(report):
    """Plain text table of the map kinds for the console."""
    lines = ['  %-15s %5s  %s' % ('kind', 'rows', 'files it needs (required | optional)')]
    for kind, entry in report.facts.get('kinds', {}).items():
        lines.append('  %-15s %5d  %s | %s%s' % (kind, entry['rows'], ' '.join(entry['required']),
                                                  ' '.join(entry['optional']) or '-',
                                                  '   MISSING: ' + ' '.join(entry['missing']) if entry['missing'] else ''))
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Check that everything built for a map is listed, present and fresh.')
    ap.add_argument('work', help='ZoneTool work folder (holds zone_source/, zonetool/ and zone/)')
    ap.add_argument('--zone', required=True, help='zone name, e.g. cp_iwz')
    ap.add_argument('--emit', metavar='DIR', help='emitted level folder to compare with the tree')
    ap.add_argument('--stock', action='append', default=[], metavar='DIR',
                    help='dumped stock zone folder, or a folder holding several (repeatable)')
    ap.add_argument('--json', metavar='FILE', help='write the full result here')
    ap.add_argument('--strict', action='store_true',
                    help='release gate: also fail (exit 2) while a warning stands')
    ap.add_argument('--table', action='store_true', help='print the per-kind table before the findings')
    args = ap.parse_args(argv)
    report = audit(args.work, args.zone, emit=args.emit, stock=args.stock or None)
    if args.table:
        print(kind_table(report))
    return finish(report, args)


if __name__ == '__main__':
    sys.exit(main())
