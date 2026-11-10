"""Pick the door blocker sub-model from an iwzcompile log made with IWZ_KEEP_SUBMODELS=1.

usage: sz2_submodels.py <compile log> <out json (sz2_submodels.json)> [template ents]

Reads the 'iwzmap: sub-model *N mid x y z half x y z ...' lines, keeps the template script_brushmodels that the
stock scripts use as debris door collision (key 51961 ScriptBrushModelDummyFixed in the template ents, when given),
and chooses the wall-like one (thin axis <= 24 units, others >= 48) with the largest face: door blockers tile copies
of it over each opening (station_zero2.py door_blockers). All parsed sub-models are kept in 'all' for reference.
"""
import json, re, sys

log, out = sys.argv[1:3]
tpl = sys.argv[3] if len(sys.argv) > 3 else None
rx = re.compile(r'sub-model \*(\d+) mid (\S+) (\S+) (\S+) half (\S+) (\S+) (\S+) radius (\S+) shape (\d+) navobst (\d+)')
subs = []
for line in open(log, encoding='utf-8', errors='replace'):
    m = rx.search(line)
    if m:
        g = m.groups()
        subs.append({'model': '*' + g[0], 'mid': [float(v) for v in g[1:4]], 'half': [float(v) for v in g[4:7]],
                     'radius': float(g[7]), 'shape': int(g[8]), 'navobst': int(g[9])})
door_models = None
if tpl:
    door_models = {}
    cur = {}
    for line in open(tpl, encoding='latin-1'):
        line = line.strip()
        if line == '{':
            cur = {}
        elif line == '}':
            if cur.get('157') == 'script_brushmodel' and cur.get('51961', '').lower() == 'scriptbrushmodeldummyfixed':
                door_models[cur.get('497')] = cur.get('543')
        else:
            m = re.match(r'(\S+) "(.*)"$', line)
            if m:
                cur[m.group(1)] = m.group(2)
cands = []
for s in subs:
    if s['model'] == '*0' or (door_models is not None and s['model'] not in door_models):
        continue
    h = sorted(s['half'])
    if h[0] <= 12 and h[1] >= 24:
        cands.append((h[1] * h[2], s))
cands.sort(key=lambda t: -t[0])
chosen = [c[1] for c in cands[:1]]
json.dump({'_source': log, 'blockers': chosen, 'door_candidates': [c[1] for c in cands], 'all': subs}, open(out, 'w'), indent=1)
print('sub-models', len(subs), 'door candidates', len(cands), 'chosen', chosen)
