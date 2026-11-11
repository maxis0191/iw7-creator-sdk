"""Entity and template-pool ledger of a generated IW7 map source (TF8). Seconds, no game, no build.

  python -I iwz_ledger.py count <src> [--template <stock cp_zmb dump>] [--json <out>]
  python -I iwz_ledger.py check <src> --template <stock cp_zmb dump> [--ceiling 1800] [--live <run log>] [--json <out>]
  python -I iwz_ledger.py compiled <compile log> [--json <out>]

<src> is a generator output folder (ents.txt, triggers.txt, lights.txt, probes.txt, smodels.txt, scriptables.txt).

Entities. The engine has 2,048 entity slots; the project's ceiling is 1,800. A map pays for the entities of its
entity list (every entry of ents.txt that is not a struct: script_struct and script_struct_mini become script structs,
not entities) and, while it runs, for players, zombies, script models, triggers and effects that scripts spawn. That
runtime share cannot be read from files, so every package writes its worst case in <src>/entity_budget.json:
  {"rows": [{"package": "E1", "entities": 120, "why": "78 crowd bodies + 42 hit volumes"}, ...]}
`check` refuses (exit 1) when entity list + runtime rows > ceiling. The live count of a running map is the `ents`
step of a gamelab plan (counts every entity the game holds); the soak's script counter does the same in a soak.

Template pools. The compiler (x64-zt iwzmap) builds the new map inside the template map (stock cp_zmb) and reuses
the template's slots; a source that needs more than the template has fails late in the compiler, or not at all:
  trigger_shapes   generated trigger models (triggers.txt rows) each take the box entity shape of an unused
                   template trigger model (info_volume, trigger_multiple, trigger_use, trigger_damage, trigger_hurt).
                   Capacity = those template models that the source's entity list does not itself use. An upper
                   bound: the compiler also needs a single box hull (`compiled` reads what it really did).
  light_static     unnamed lights.txt rows take static spot/omni slots between the last sun and the scriptable range
  light_named      named lights.txt rows (switchable) take the scriptable range; the compiler can extend that range
                   over static slots, so named + unnamed together must fit in static + scriptable
  probes           probes.txt rooms each take one reflection cube of the template's probe array
  door_blockers    script_brushmodel entries of the entity list: copies of template brush models; capacity is the
                   number of entities, not a template count (reported, not limited)
  static_models    smodels.txt rows: at most 65,535 (compiler limit)
`check` refuses (exit 1) when any limited pool is over its capacity.
"""
import argparse, json, os, re, sys

STRUCTS = {'script_struct', 'script_struct_mini'}
TRIGGER_CLASSES = {'info_volume', 'trigger_multiple', 'trigger_use', 'trigger_damage', 'trigger_hurt'}
ENGINE_SLOTS = 2048
PROBES_IN_TEMPLATE = 160      # cp_zmb reflection probe array (compile log: "160 probes")


def parse_ents(path):
    ents, cur = [], None
    for line in open(path, encoding='latin-1'):
        line = line.strip()
        if line == '{':
            cur = {}
        elif line == '}':
            if cur is not None:
                ents.append(cur)
            cur = None
        elif cur is not None:
            m = re.match(r'(\S+) "(.*)"$', line)
            if m:
                cur[m.group(1)] = m.group(2)
    return ents


def rows(path):
    if not os.path.isfile(path):
        return []
    return [ln.split() for ln in open(path, encoding='utf-8', errors='replace') if ln.strip() and not ln.lstrip().startswith(('#', '//'))]


def entity_table(ents):
    by = {}
    for e in ents:
        c = e.get('157', '?')
        by[c] = by.get(c, 0) + 1
    entities = sum(n for c, n in by.items() if c not in STRUCTS)
    structs = sum(n for c, n in by.items() if c in STRUCTS)
    return entities, structs, dict(sorted(by.items(), key=lambda kv: -kv[1]))


def template_caps(tdump):
    maps = os.path.join(tdump, 'maps', 'cp')
    ents = parse_ents(os.path.join(maps, 'cp_zmb.d3dbsp.ents'))
    trig = sorted({e['497'] for e in ents if e.get('157') in TRIGGER_CLASSES and e.get('497', '').startswith('?')})
    com = json.load(open(os.path.join(maps, 'cp_zmb.d3dbsp.commap.json')))
    pl = com['primaryLight']
    first = int(com['firstScriptablePrimaryLight']); nscr = int(com['scriptablePrimaryLightCount'])
    last_sun = max(i for i, l in enumerate(pl) if l['type'] == 1)
    end = first if nscr else len(pl)
    static = sum(1 for l in pl[last_sun + 1:end] if l['type'] in (2, 3))
    scriptable = sum(1 for l in pl[end:] if l['type'] in (2, 3))
    return {'trigger_models': trig, 'light_static': static, 'light_scriptable': scriptable, 'probes': PROBES_IN_TEMPLATE,
            'template_entities': entity_table(ents)[0]}


def ledger(src, tdump=None, ceiling=1800):
    ents = parse_ents(os.path.join(src, 'ents.txt'))
    entities, structs, by = entity_table(ents)
    budget_path = os.path.join(src, 'entity_budget.json')
    budget = json.load(open(budget_path)).get('rows', []) if os.path.isfile(budget_path) else []
    runtime = sum(int(r.get('entities', 0)) for r in budget)
    lights = rows(os.path.join(src, 'lights.txt'))
    named = sum(1 for r in lights if any(t.startswith('name=') for t in r))   # "... [shadow] [name=<targetname>] [group=..]"
    out = {'schema': 'iwz.ledger/1', 'src': os.path.abspath(src),
           'entities': {'entity_list': entities, 'structs': structs, 'by_class': by, 'runtime_rows': budget,
                        'runtime': runtime, 'total': entities + runtime, 'ceiling': ceiling, 'engine': ENGINE_SLOTS},
           'pools': {}, 'refusals': []}
    used_trig = sorted({e['497'] for e in ents if e.get('157') in TRIGGER_CLASSES and e.get('497', '').startswith('?')})
    pools = {
        'trigger_shapes': {'used': len(rows(os.path.join(src, 'triggers.txt')))},
        'light_static': {'used': len(lights) - named},
        'light_named': {'used': named},
        'probes': {'used': sum(1 for r in rows(os.path.join(src, 'probes.txt')) if r[0] == 'room')},
        'door_blockers': {'used': by.get('script_brushmodel', 0), 'capacity': None},
        'static_models': {'used': len(rows(os.path.join(src, 'smodels.txt'))), 'capacity': 65535},
        'scriptables': {'used': len(rows(os.path.join(src, 'scriptables.txt'))), 'capacity': None},
    }
    if tdump:
        caps = template_caps(tdump)
        # template trigger models the source still names itself are not free to give their shape
        free = [m for m in caps['trigger_models'] if m not in used_trig]
        pools['trigger_shapes']['capacity'] = len(free)
        pools['trigger_shapes']['note'] = 'upper bound: the compiler also needs a single box hull'
        pools['light_static']['capacity'] = caps['light_static']
        pools['light_named']['capacity'] = caps['light_scriptable']
        pools['light_named']['note'] = 'the compiler extends the named range over static slots: named + static <= %d' % (caps['light_static'] + caps['light_scriptable'])
        pools['probes']['capacity'] = caps['probes']
        out['template'] = {k: v for k, v in caps.items() if k != 'trigger_models'}
        out['template']['trigger_models'] = len(caps['trigger_models'])
        if pools['light_named']['used'] + pools['light_static']['used'] > caps['light_static'] + caps['light_scriptable']:
            out['refusals'].append('lights: %d named + %d static > %d template slots' % (
                pools['light_named']['used'], pools['light_static']['used'], caps['light_static'] + caps['light_scriptable']))
    for name, p in pools.items():
        if name == 'light_named':
            continue          # judged together with the static lights above
        if p.get('capacity') is not None and p['used'] > p['capacity']:
            out['refusals'].append('%s: %d used > %d in the template' % (name, p['used'], p['capacity']))
    if entities + runtime > ceiling:
        out['refusals'].append('entities: %d in the entity list + %d declared at runtime = %d > ceiling %d' % (
            entities, runtime, entities + runtime, ceiling))
    out['pools'] = pools
    return out


def live(log):
    """Entity census lines of a gamelab run (GL ENTS name=.. key=* .. n=..): what the running map really holds."""
    out = {}
    for m in re.finditer(r'GL ENTS i=\d+ name=(\S+) key=(\S+) value=(\S+) n=(\d+) ents=(\d+) structs=(\d+)', open(log, encoding='utf-8', errors='replace').read()):
        out[m.group(1)] = {'key': m.group(2), 'value': m.group(3), 'n': int(m.group(4)), 'ents': int(m.group(5)), 'structs': int(m.group(6))}
    return out


def compiled(log):
    """What the compiler really did with the pools (read from an iwzcompile log)."""
    text = open(log, encoding='utf-8', errors='replace').read()
    g = lambda rx: [m.groups() for m in re.finditer(rx, text)]
    out = {'schema': 'iwz.ledger-compiled/1', 'log': os.path.abspath(log)}
    t = g(r'(\d+) generated trigger models')
    out['trigger_models'] = int(t[-1][0]) if t else 0
    out['trigger_shaped'] = len(g(r'generated trigger \?\d+ takes the entity shape'))
    out['trigger_unshaped'] = len(g(r'generated trigger \?\d+ has \d+ hulls')) + sum(int(n) for (n,) in g(r'(\d+) generated trigger models (?:keep no|have no) entity shape'))
    out['light_slots'] = len(set(g(r'light (?:omni |spot )?slot (\d+)')))
    p = g(r'probes: neutral rooms (\d+) of (\d+) \(cubes (\d+)\)')
    if p:
        out['probe_rooms'], out['probe_cubes'] = int(p[-1][0]), int(p[-1][2])
    s = g(r'iwzmap: (\d+) static models')
    out['static_models'] = int(s[-1][0]) if s else 0
    out['errors'] = [m.group(0)[:200] for m in re.finditer(r'(?:no static template light slot left|no scriptable light slot left|not enough template light slots|more than 65535 static models)[^\n]*', text)]
    return out


def show(o):
    if o['schema'] == 'iwz.ledger/1':
        e = o['entities']
        print('entities: %d in the entity list (%d structs not counted), %d declared at runtime, total %d of ceiling %d (engine %d)' % (
            e['entity_list'], e['structs'], e['runtime'], e['total'], e['ceiling'], e['engine']))
        print('  by class: ' + ', '.join('%s %d' % kv for kv in e['by_class'].items() if kv[0] not in STRUCTS))
        if 'live_total' in e:
            print('  live census: %d entities in the running map, so %d come from scripts, players and the engine at that moment' % (
                e['live_total'], e['live_runtime_share']))
        for name, p in o['pools'].items():
            cap = p.get('capacity')
            print('pool %-15s used %5d of %s%s' % (name, p['used'], '-' if cap is None else cap, ('  (' + p['note'] + ')') if p.get('note') else ''))
        for r in o['refusals']:
            print('REFUSED ' + r)
        if not o['refusals']:
            print('ok')
    else:
        print(json.dumps(o, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for n in ('count', 'check'):
        p = sub.add_parser(n); p.add_argument('src'); p.add_argument('--template', required=(n == 'check'))
        p.add_argument('--ceiling', type=int, default=1800); p.add_argument('--json')
        p.add_argument('--live', help="a gamelab run's client.stdout.log with an `ents` step that counts every entity")
    c = sub.add_parser('compiled'); c.add_argument('log'); c.add_argument('--json')
    a = ap.parse_args()
    if a.cmd == 'compiled':
        o = compiled(a.log)
    else:
        o = ledger(a.src, a.template, a.ceiling)
        if a.live:
            census = live(a.live)
            whole = next((c for c in census.values() if c['key'] == '*'), None)
            o['entities']['live'] = census
            if whole:
                o['entities']['live_total'] = whole['ents']
                o['entities']['live_runtime_share'] = whole['ents'] - o['entities']['entity_list']
    if a.json:
        json.dump(o, open(a.json, 'w'), indent=1)
    show(o)
    if a.cmd == 'check' and o['refusals']:
        return 1
    if a.cmd == 'compiled' and o['errors']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
