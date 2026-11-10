#!/usr/bin/env python3
"""Entity overlay for the game's own maps: export a map's entity list, patch it, write the file the loader reads.

The engine's entity list of a shipped map (spawn points, zombie spawners, triggers, placed models, interaction
points, doors) can be replaced at map load by a plain text file named <map asset name>.ents (docs/MAPENTS.md).
This tool turns that into four safe steps an agent can script: export, find/stats, patch, write.

Entity text (what the dump tool writes and what the loader reads):

    {
    157 "script_model"          <- key "value"; the key is a numeric token id or a quoted name
    543 "467 3677 40"
    }

Standard library only.
"""
import argparse
import collections
import difflib
import json
import math
import os
import re
import sys

SCHEMA = 'iw7.ents/1'
PATCH_SCHEMA = 'iw7.ents-patch/1'
LINE = re.compile(r'(.+) "(.*)"')            # the loader's own expression (component mapents.cpp)

# Numeric token id -> field name, for the keys the shipped maps use that the game's token list names (the
# Spaceland dump uses all of these). A key not listed stays a plain number everywhere in the tool.
KEYS = {
    '157': 'classname', '543': 'origin', '822': 'targetname', '65': 'angles', '497': 'model',
    '638': 'script_noteworthy', '820': 'target', '61049': 'script_parameters', '599': 'radius', '4524': '_color',
    '687': 'spawnflags', '502': 'name', '8098': 'animation', '34466': 'groupname', '72': 'animscript',
    '60661': 'script_animation', '60904': 'script_index', '61118': 'script_speed', '60859': 'script_fxid',
    '691': 'speed', '60666': 'script_area', '635': 'script_delay', '47400': 'modelscale', '636': 'script_linkname',
    '445': 'lookahead', '4435': '__smuid', '29508': 'fov_outer', '29507': 'fov_inner', '27146': 'exponent',
    '20434': 'def', '39397': 'intensity', '4434': '__smorigin', '4431': '__smangles', '4433': '__smname',
    '4432': '__smid', '60659': 'script_angles', '60932': 'script_location', '61056': 'script_personality',
    '60921': 'script_label', '61097': 'script_side', '61205': 'script_wait', '337': 'generatenavmesh',
    '66196': 'skycolor', '721': 'sunlight', '719': 'suncolor', '720': 'sundirection', '61010': 'script_namenumber',
    '245': 'dmg',
}
IDS = {v: k for k, v in KEYS.items()}
SELECTOR_KEYS = ('classname', 'targetname', 'script_noteworthy', 'model', 'target', 'key', 'value', 'box', 'index',
                 'near', 'radius')
TOKEN_LINE = re.compile(r'\s*\{\s*0x([0-9A-Fa-f]+),\s*"([^"]*)"\s*\}')


class MapEntsError(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------------------------------------------------

def load_tokens(path):
    """Extend the key table from a gsc-tool IW7 token list (source file with lines like { 0x009D, "classname" })."""
    n = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = TOKEN_LINE.match(line)
            if m and m.group(2):
                key = str(int(m.group(1), 16))
                if key not in KEYS:
                    KEYS[key] = m.group(2)
                IDS.setdefault(m.group(2), key)
                n += 1
    return n


def norm_key(key):
    """A key as the tool keeps it: the field name when known, else the number, else the name as written."""
    key = str(key).strip().lower()
    if key.startswith('"') and key.endswith('"') and len(key) >= 2:
        key = key[1:-1]
    if key.isdigit() and str(int(key)) == key:
        return KEYS.get(key, key)
    return key


def key_id(key):
    """The numeric id written to the loader for a key, or None when only the name is known."""
    if key.isdigit():
        return key
    return IDS.get(key)


# ---------------------------------------------------------------------------------------------------------------------
# text <-> entities
# ---------------------------------------------------------------------------------------------------------------------

def parse_text(text):
    """Entity text -> (entities, warnings). An entity is a list of [key, value] pairs, in file order, duplicates kept.
    Follows the loader: only a brace in column 0 opens or closes an entity, blank or malformed lines are skipped,
    a pair with an empty value is dropped, // lines and /* */ blocks are comments. Text after the first NUL is
    ignored (the dump's trailing NUL). A line the loader would mishandle is an error here."""
    text = text.split('\0', 1)[0]
    entities, warnings, cur = [], [], None
    in_comment = False
    for n, line in enumerate(text.split('\n'), 1):
        line = line.rstrip('\r')
        if line.startswith('/*'):
            if line.endswith('*/'):
                raise MapEntsError('line %d: a one-line /* */ comment: the loader would treat the rest of the file as a comment' % n)
            in_comment = True
            continue
        if line.endswith('*/'):
            in_comment = False
            continue
        if in_comment or line.startswith('//'):
            continue
        if line[:1] == '{':
            if cur is not None:
                raise MapEntsError("line %d: unexpected '{' inside an entity" % n)
            cur = []
            continue
        if line[:1] == '}':
            if cur is None:
                raise MapEntsError("line %d: unexpected '}' outside an entity" % n)
            entities.append(cur)
            cur = None
            continue
        m = LINE.search(line)
        if not m:
            if line:
                warnings.append('line %d: not a key "value" pair, the loader skips it: %s' % (n, line[:60]))
            continue
        if cur is None:
            raise MapEntsError('line %d: a pair outside an entity' % n)
        key = norm_key(m.group(1).lstrip())
        if not key:
            warnings.append('line %d: empty key, skipped' % n)
            continue
        if m.group(2) == '':
            warnings.append('line %d: empty value for %s, the loader drops the pair' % (n, key))
            continue
        cur.append([key, m.group(2)])
    if cur is not None:
        raise MapEntsError('the last entity is not closed')
    return entities, warnings


def fmt_value(v):
    if isinstance(v, bool):
        raise MapEntsError('a value cannot be true/false: %r' % v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return ('%g' % v) if abs(v) < 1e15 else repr(v)
    if isinstance(v, (list, tuple)):
        return ' '.join(fmt_value(x) for x in v)
    if isinstance(v, str):
        return v
    raise MapEntsError('unsupported value %r' % (v,))


def check_pair(key, value):
    if not isinstance(key, str) or not key or any(c in key for c in '"\n\r\0'):
        raise MapEntsError('bad key %r' % (key,))
    if value == '':
        raise MapEntsError('key %s has an empty value: the loader drops such a pair' % key)
    if any(c in value for c in '"\n\r\0'):
        raise MapEntsError('value of %s contains a quote or a line break: %r' % (key, value))


def to_text(entities, readable=False):
    """Entities -> (the text the loader reads, the keys written by name that the loader must resolve itself).
    Numeric form (default): the keys the tool knows are written as their token ids, exactly like the stock file;
    readable form: every known key is written as a quoted name, which the loader converts through the game's token
    list. A key the tool has no id for is always written as a quoted name."""
    out, by_name = [], set()
    for ent in entities:
        out.append('{')
        for key, value in ent:
            value = fmt_value(value)
            check_pair(key, value)
            kid = key if key.isdigit() else (None if readable else key_id(key))
            if kid is not None:
                out.append('%s "%s"' % (kid, value))
            else:
                by_name.add(key)
                out.append('"%s" "%s"' % (key, value))
        out.append('}')
    return '\n'.join(out) + '\n', sorted(by_name)


# ---------------------------------------------------------------------------------------------------------------------
# entity access
# ---------------------------------------------------------------------------------------------------------------------

def get(ent, key, default=None):
    key = norm_key(key)
    for k, v in ent:
        if k == key:
            return v
    return default


def origin_of(ent):
    v = get(ent, 'origin')
    if v is None:
        return None
    try:
        p = [float(x) for x in v.split()]
    except ValueError:
        return None
    return tuple(p) if len(p) == 3 else None


def build_index(entities):
    idx = {'classname': collections.OrderedDict(), 'targetname': collections.OrderedDict()}
    for i, ent in enumerate(entities):
        for key in idx:
            v = get(ent, key)
            if v is not None:
                idx[key].setdefault(v, []).append(i)
    return idx


def make_doc(entities, map_name=None, loader_name=None, source=None, extra=None):
    doc = collections.OrderedDict()
    doc['schema'] = SCHEMA
    doc['map'] = map_name
    doc['loader_name'] = loader_name
    doc['source'] = source
    doc['count'] = len(entities)
    if extra:
        doc.update(extra)
    doc['entities'] = entities
    doc['index'] = build_index(entities)
    return doc


def save_doc(doc, path):
    """JSON with one entity per line (diff-friendly, and 3,000 entities stay readable)."""
    head = collections.OrderedDict((k, v) for k, v in doc.items() if k not in ('entities', 'index'))
    parts = ['{']
    for k, v in head.items():
        parts.append('%s: %s,' % (json.dumps(k), json.dumps(v)))
    parts.append('"entities": [')
    ents = doc['entities']
    for i, e in enumerate(ents):
        parts.append(' ' + json.dumps(e) + (',' if i < len(ents) - 1 else ''))
    parts.append('],')
    parts.append('"index": ' + json.dumps(doc.get('index') or build_index(ents)))
    parts.append('}')
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(parts) + '\n')


def load_doc(path):
    try:
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise MapEntsError('cannot read %s: %s' % (path, e))
    if not isinstance(doc, dict) or doc.get('schema') != SCHEMA or not isinstance(doc.get('entities'), list):
        raise MapEntsError('%s is not an %s file' % (path, SCHEMA))
    ents = []
    for n, e in enumerate(doc['entities']):
        if not isinstance(e, list) or not all(isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) for p in e):
            raise MapEntsError('%s: entity %d is not a list of [key, value] pairs' % (path, n))
        ents.append([[norm_key(k), fmt_value(v)] for k, v in e])
    doc['entities'] = ents
    return doc


# ---------------------------------------------------------------------------------------------------------------------
# selectors
# ---------------------------------------------------------------------------------------------------------------------

def check_selector(sel, where):
    if not isinstance(sel, dict) or not sel:
        raise MapEntsError('%s: a selector is a non-empty object' % where)
    for k in sel:
        if k not in SELECTOR_KEYS:
            raise MapEntsError('%s: unknown selector field %r (allowed: %s)' % (where, k, ', '.join(SELECTOR_KEYS)))
    if 'value' in sel and 'key' not in sel:
        raise MapEntsError('%s: "value" needs "key"' % where)
    if 'radius' in sel and 'near' not in sel or 'near' in sel and 'radius' not in sel:
        raise MapEntsError('%s: "near" and "radius" go together' % where)
    for k in ('box', 'near'):
        if k in sel:
            n = 6 if k == 'box' else 3
            v = sel[k]
            if not isinstance(v, list) or len(v) != n or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                raise MapEntsError('%s: "%s" is a list of %d numbers' % (where, k, n))
    if 'index' in sel:
        v = sel['index']
        v = v if isinstance(v, list) else [v]
        if not all(isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in v):
            raise MapEntsError('%s: "index" is a whole number or a list of them' % where)


def matches(ent, i, sel):
    for k in ('classname', 'targetname', 'script_noteworthy', 'model', 'target'):
        if k in sel and get(ent, k) != str(sel[k]):
            return False
    if 'key' in sel:
        v = get(ent, sel['key'])
        if v is None or ('value' in sel and v != fmt_value(sel['value'])):
            return False
    if 'index' in sel:
        want = sel['index'] if isinstance(sel['index'], list) else [sel['index']]
        if i not in want:
            return False
    p = None
    if 'box' in sel or 'near' in sel:
        p = origin_of(ent)
        if p is None:
            return False
    if 'box' in sel:
        b = sel['box']
        lo = [min(b[a], b[a + 3]) for a in range(3)]
        hi = [max(b[a], b[a + 3]) for a in range(3)]
        if not all(lo[a] <= p[a] <= hi[a] for a in range(3)):
            return False
    if 'near' in sel and math.dist(p, sel['near']) > sel['radius']:
        return False
    return True


def select(entities, sel, alive=None):
    return [i for i, e in enumerate(entities) if (alive is None or i in alive) and matches(e, i, sel)]


# ---------------------------------------------------------------------------------------------------------------------
# patch
# ---------------------------------------------------------------------------------------------------------------------

def brief(ent):
    return {k: get(ent, k) for k in ('classname', 'targetname', 'script_noteworthy', 'model', 'origin') if get(ent, k) is not None}


def apply_patch(entities, patch):
    """-> (new entities, report). Selectors name entities of the INPUT list (indexes included); removals happen first,
    then changes (on what is left), then additions. A rule that matches nothing is an error unless optional."""
    if not isinstance(patch, dict) or patch.get('schema') != PATCH_SCHEMA:
        raise MapEntsError('a patch has "schema": "%s"' % PATCH_SCHEMA)
    for k in patch:
        if k not in ('schema', 'remove', 'set', 'add', 'note'):
            raise MapEntsError('unknown patch field %r' % k)
    report = {'remove': [], 'set': [], 'add': []}
    errors = []
    removed = set()
    for n, rule in enumerate(patch.get('remove', [])):
        where = 'remove[%d]' % n
        optional = False
        sel = rule
        if isinstance(rule, dict) and 'optional' in rule:
            sel = {k: v for k, v in rule.items() if k != 'optional'}
            optional = bool(rule['optional'])
        check_selector(sel, where)
        hit = select(entities, sel)
        report['remove'].append({'rule': n, 'selector': sel, 'matched': len(hit), 'indices': hit[:50],
                                 'examples': [brief(entities[i]) for i in hit[:3]], 'optional': optional})
        if not hit and not optional:
            errors.append('%s matched no entity: %s' % (where, json.dumps(sel)))
        removed.update(hit)
    alive = set(range(len(entities))) - removed
    changed = {}
    for n, rule in enumerate(patch.get('set', [])):
        where = 'set[%d]' % n
        if not isinstance(rule, dict) or 'where' not in rule or not isinstance(rule.get('values'), dict) or not rule['values']:
            raise MapEntsError('%s needs "where" and a non-empty "values" object' % where)
        for k in rule:
            if k not in ('where', 'values', 'optional'):
                raise MapEntsError('%s: unknown field %r' % (where, k))
        check_selector(rule['where'], where + '.where')
        hit = select(entities, rule['where'], alive)
        report['set'].append({'rule': n, 'selector': rule['where'], 'values': rule['values'], 'matched': len(hit), 'indices': hit[:50],
                              'examples': [brief(entities[i]) for i in hit[:3]], 'optional': bool(rule.get('optional'))})
        if not hit and not rule.get('optional'):
            errors.append('%s matched no entity that is left after the removals: %s' % (where, json.dumps(rule['where'])))
        for i in hit:
            changed.setdefault(i, []).append(rule['values'])
    if errors:
        raise MapEntsError('; '.join(errors))
    out = []
    for i, ent in enumerate(entities):
        if i in removed:
            continue
        ent = [list(p) for p in ent]
        for values in changed.get(i, []):
            for k, v in values.items():
                key = norm_key(k)
                if v is None:
                    ent = [p for p in ent if p[0] != key]
                    continue
                v = fmt_value(v)
                check_pair(key, v)
                first = next((j for j, p in enumerate(ent) if p[0] == key), None)
                if first is None:
                    ent.append([key, v])
                else:
                    ent[first][1] = v
                    ent[:] = [p for j, p in enumerate(ent) if p[0] != key or j == first]
        out.append(ent)
    for n, spec in enumerate(patch.get('add', [])):
        where = 'add[%d]' % n
        if not isinstance(spec, dict) or not spec:
            raise MapEntsError('%s is a non-empty object of key: value' % where)
        ent = []
        for k, v in spec.items():
            key = norm_key(k)
            v = fmt_value(v)
            check_pair(key, v)
            ent.append([key, v])
        if get(ent, 'classname') is None:
            raise MapEntsError('%s has no "classname"' % where)
        out.append(ent)
        report['add'].append({'rule': n, 'index': len(out) - 1, 'entity': brief(ent)})
    report['before'] = len(entities)
    report['after'] = len(out)
    report['removed'] = len(removed)
    report['changed'] = len(changed)
    report['added'] = len(report['add'])
    return out, report


# ---------------------------------------------------------------------------------------------------------------------
# stats / diff
# ---------------------------------------------------------------------------------------------------------------------

def stats(entities, top=30):
    cls = collections.Counter(get(e, 'classname', '(none)') for e in entities)
    tn = collections.Counter(v for v in (get(e, 'targetname') for e in entities) if v is not None)
    pts = [p for p in (origin_of(e) for e in entities) if p]
    box = None
    if pts:
        box = [[min(p[a] for p in pts) for a in range(3)], [max(p[a] for p in pts) for a in range(3)]]
    return {'entities': len(entities), 'classnames': len(cls), 'by_classname': cls.most_common(),
            'targetnames': len(tn), 'by_targetname': tn.most_common(top),
            'with_model': sum(1 for e in entities if get(e, 'model') is not None),
            'with_origin': len(pts), 'origin_box': box}


def ent_key(ent):
    return json.dumps(ent)


def diff(a, b):
    """-> {'removed': [(i, ent)], 'added': [(j, ent)], 'changed': [(i, j, ent_a, [(key, old, new)])]}"""
    sm = difflib.SequenceMatcher(None, [ent_key(e) for e in a], [ent_key(e) for e in b], autojunk=False)
    removed, added, changed = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'delete':
            removed += [(i, a[i]) for i in range(i1, i2)]
        elif tag == 'insert':
            added += [(j, b[j]) for j in range(j1, j2)]
        elif tag == 'replace':
            left = list(range(i1, i2))
            right = list(range(j1, j2))
            for i in left:
                best = None
                for j in right:
                    if get(a[i], 'classname') == get(b[j], 'classname') and (
                            get(a[i], 'origin') == get(b[j], 'origin') or get(a[i], 'targetname') == get(b[j], 'targetname')
                            and get(a[i], 'targetname') is not None):
                        best = j
                        break
                if best is None:
                    removed.append((i, a[i]))
                else:
                    right.remove(best)
                    keys = []
                    for k in dict.fromkeys([p[0] for p in a[i]] + [p[0] for p in b[best]]):
                        o, nv = get(a[i], k), get(b[best], k)
                        if o != nv:
                            keys.append((k, o, nv))
                    changed.append((i, best, a[i], keys))
            added += [(j, b[j]) for j in right]
    return {'removed': removed, 'added': added, 'changed': changed}


# ---------------------------------------------------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------------------------------------------------

def find_dump_ents(dump):
    base = os.path.join(dump, 'maps')
    hits = []
    for root, _, files in os.walk(base if os.path.isdir(base) else dump):
        for name in files:
            if name.endswith('.d3dbsp.ents'):
                hits.append(os.path.join(root, name))
    if not hits:
        raise MapEntsError('no *.d3dbsp.ents under %s (a ZoneTool map dump has it under maps/<prefix>/)' % dump)
    if len(hits) > 1:
        raise MapEntsError('several entity files under %s; pass --ents FILE: %s' % (dump, ', '.join(hits)))
    return hits[0]


def default_loader_name(map_name):
    prefix = map_name.split('_', 1)[0]
    return 'maps/%s/%s.d3dbsp.ents' % (prefix, map_name)


def cmd_export(a):
    path = a.ents or find_dump_ents(a.dump)
    with open(path, 'rb') as f:
        raw = f.read()
    ents, warns = parse_text(raw.decode('latin-1'))
    base = os.path.basename(path)
    map_name = base[:-len('.d3dbsp.ents')]
    loader = None
    if a.dump and not a.ents:
        rel = os.path.relpath(path, a.dump).replace(os.sep, '/')
        loader = rel if rel.startswith('maps/') else None
    loader = loader or default_loader_name(map_name)
    doc = make_doc(ents, map_name, loader, {'file': base, 'bytes': len(raw)}, {'warnings': warns} if warns else None)
    save_doc(doc, a.out)
    print('exported %d entities of %s to %s (loader file name %s)' % (len(ents), map_name, a.out, loader))
    for w in warns[:10]:
        print('warning: ' + w)
    return 0


def cmd_stats(a):
    s = stats(load_doc(a.file)['entities'])
    if a.json:
        print(json.dumps(s))
        return 0
    print('entities %d, with origin %d, with model %d' % (s['entities'], s['with_origin'], s['with_model']))
    if s['origin_box']:
        print('origin box: %s .. %s' % tuple(' '.join('%g' % c for c in p) for p in s['origin_box']))
    print('classnames (%d):' % s['classnames'])
    for k, n in s['by_classname'][:a.top]:
        print('  %6d  %s' % (n, k))
    print('targetnames (%d distinct), top %d:' % (s['targetnames'], len(s['by_targetname'])))
    for k, n in s['by_targetname']:
        print('  %6d  %s' % (n, k))
    return 0


def selector_from_args(a):
    sel = {}
    for k in ('classname', 'targetname', 'key', 'value'):
        if getattr(a, k, None) is not None:
            sel[k] = getattr(a, k)
    if a.box:
        sel['box'] = a.box
    if a.near:
        sel['near'] = a.near
        sel['radius'] = a.radius if a.radius is not None else 0
    if a.index is not None:
        sel['index'] = a.index
    return sel


def cmd_find(a):
    doc = load_doc(a.file)
    sel = selector_from_args(a)
    if not sel:
        raise MapEntsError('give at least one of --classname --targetname --key --box --near --index')
    check_selector(sel, 'find')
    hit = select(doc['entities'], sel)
    if a.json:
        print(json.dumps([{'index': i, 'entity': doc['entities'][i]} for i in hit[:a.limit]]))
        return 0
    print('%d matching entities' % len(hit))
    for i in hit[:a.limit]:
        e = doc['entities'][i]
        bits = ['%s=%s' % (k, get(e, k)) for k in ('classname', 'targetname', 'script_noteworthy', 'model', 'origin') if get(e, k) is not None]
        print('  #%d %s' % (i, ' '.join(bits)))
    if len(hit) > a.limit:
        print('  ... %d more (--limit)' % (len(hit) - a.limit))
    return 0


def cmd_patch(a):
    doc = load_doc(a.file)
    try:
        with open(a.patch, encoding='utf-8') as f:
            patch = json.load(f)
    except (OSError, ValueError) as e:
        raise MapEntsError('cannot read the patch %s: %s' % (a.patch, e))
    ents, report = apply_patch(doc['entities'], patch)
    out = make_doc(ents, doc.get('map'), doc.get('loader_name'), doc.get('source'), {'patched_from': os.path.basename(a.file), 'patch': report})
    save_doc(out, a.out)
    print('patched %s: %d -> %d entities (removed %d, changed %d, added %d); report in %s' % (
        doc.get('map'), report['before'], report['after'], report['removed'], report['changed'], report['added'], a.out))
    for kind in ('remove', 'set'):
        for r in report[kind]:
            print('  %s[%d]: %d matched%s' % (kind, r['rule'], r['matched'], ' (optional)' if r['optional'] and not r['matched'] else ''))
    for r in report['add']:
        print('  add[%d]: entity #%d %s' % (r['rule'], r['index'], json.dumps(r['entity'])))
    return 0


def cmd_write(a):
    doc = load_doc(a.file)
    ents = doc['entities']
    if not ents:
        raise MapEntsError('the list is empty: the loader would load an empty map')
    map_name = a.map or doc.get('map')
    if not map_name:
        raise MapEntsError('give --map <map name>')
    rel = a.loader_name or (doc.get('loader_name') if (not a.map or a.map == doc.get('map')) else None) or default_loader_name(map_name)
    if rel.startswith('/') or '..' in rel.split('/'):
        raise MapEntsError('the loader file name must be a relative path: %s' % rel)
    text, by_name = to_text(ents, readable=a.readable)
    dest = os.path.join(a.out_dir, *rel.split('/'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='ascii', errors='strict', newline='\n') as f:
        f.write(text)
    print('wrote %d entities to %s' % (len(ents), dest))
    print('install: copy it to <game folder>/iw7-mod/%s (the loader also searches the mod data folder and the engine search paths)' % rel)
    if by_name:
        shown = ', '.join(by_name[:8]) + (' ...' if len(by_name) > 8 else '')
        print('note: %d field names are written by name; the loader resolves them through the game token list and drops a name it does not know with a log warning: %s' % (len(by_name), shown))
    return 0


def cmd_diff(a):
    da, db = load_doc(a.a), load_doc(a.b)
    d = diff(da['entities'], db['entities'])
    if a.json:
        print(json.dumps({'removed': [{'index': i, 'entity': e} for i, e in d['removed']],
                          'added': [{'index': j, 'entity': e} for j, e in d['added']],
                          'changed': [{'from': i, 'to': j, 'keys': k} for i, j, _, k in d['changed']]}))
        return 0
    print('%d removed, %d added, %d changed' % (len(d['removed']), len(d['added']), len(d['changed'])))
    for i, e in d['removed'][:a.limit]:
        print('  - #%d %s' % (i, json.dumps(brief(e))))
    for j, e in d['added'][:a.limit]:
        print('  + #%d %s' % (j, json.dumps(brief(e))))
    for i, j, e, keys in d['changed'][:a.limit]:
        print('  ~ #%d -> #%d %s' % (i, j, ', '.join('%s: %s -> %s' % k for k in keys)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='iw7_mapents', description=__doc__.split('\n')[0])
    ap.add_argument('--tokens', help='a gsc-tool IW7 token list (iw7_token.cpp) to name more numeric keys')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('export', help='a map dump -> entities JSON')
    p.add_argument('--dump', help='the map dump folder (holds maps/<prefix>/<map>.d3dbsp.ents)')
    p.add_argument('--ents', help='an entity text file instead of a dump folder')
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_export)
    p = sub.add_parser('stats', help='counts and the origin box')
    p.add_argument('file')
    p.add_argument('--top', type=int, default=15)
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser('find', help='entities matching a selector')
    p.add_argument('file')
    p.add_argument('--classname')
    p.add_argument('--targetname')
    p.add_argument('--key')
    p.add_argument('--value')
    p.add_argument('--box', nargs=6, type=float, metavar=('X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2'))
    p.add_argument('--near', nargs=3, type=float, metavar=('X', 'Y', 'Z'))
    p.add_argument('--radius', type=float)
    p.add_argument('--index', type=int)
    p.add_argument('--limit', type=int, default=50)
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser('patch', help='apply a patch (remove, set, add)')
    p.add_argument('file')
    p.add_argument('--patch', required=True)
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_patch)
    p = sub.add_parser('write', help='write the file the loader reads')
    p.add_argument('file')
    p.add_argument('--map', help='map name (default: the one in the file)')
    p.add_argument('--out-dir', required=True)
    p.add_argument('--loader-name', help='relative file name the loader looks for (default maps/<prefix>/<map>.d3dbsp.ents)')
    p.add_argument('--readable', action='store_true', help='write quoted field names instead of token ids (the loader converts them)')
    p.set_defaults(fn=cmd_write)
    p = sub.add_parser('diff', help='what differs between two entity files')
    p.add_argument('a')
    p.add_argument('b')
    p.add_argument('--limit', type=int, default=50)
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_diff)
    a = ap.parse_args(argv)
    try:
        if a.tokens:
            load_tokens(a.tokens)
        if a.cmd == 'export' and not (a.dump or a.ents):
            raise MapEntsError('give --dump or --ents')
        return a.fn(a)
    except MapEntsError as e:
        print('ERROR: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
