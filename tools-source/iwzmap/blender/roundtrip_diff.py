"""Compare two emit folders (an original and its Blender round trip): world triangles, collision, entities, layout, navigation.

    python -B roundtrip_diff.py <original emit> <round trip emit> [--json out.json]

Plain Python and numpy, no Blender. Triangles are compared as multisets with a tolerance (the collision is quantised by
hkcm_write: 21 bits over the map extent, about 0.004 units, so corners are rounded to 0.05 first).
"""
import collections
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IWZ = os.path.dirname(HERE)
for p in (IWZ, os.path.join(IWZ, 'preview')):
    sys.path.insert(0, p)


def area(t):
    a, b, c = t
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    x = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return 0.5 * math.sqrt(x[0] ** 2 + x[1] ** 2 + x[2] ** 2)


def tkey(t, q=0.05):
    pts = [tuple(round(c / q) for c in p) for p in t]
    k = pts.index(min(pts))
    return tuple(pts[k:] + pts[:k])


def world_tris(src):
    import iwz_assets as A
    import numpy as np
    w = A.read_world(os.path.join(src, 'world.bin'))
    v, idx = w['verts'], w['indices']
    out = collections.defaultdict(list)
    for s in w['surfaces']:
        t = idx[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + int(s['first'])
        for tri in t:
            out[w['materials'][int(s['mat'])].split('|')[0]].append([tuple(map(float, v['pos'][i])) for i in tri])
    return out, w


def col_tris(src):
    from hkpack import Packfile
    import hkcm
    pf = Packfile(open(os.path.join(src, 'colmap.hkx'), 'rb').read())
    for addr, name, _ in pf.objects:
        if name == 'hknpCompressedMeshShapeData':
            d = hkcm.decode_cm_data(pf, addr)
            return [tuple(tuple(c * 32.0 for c in p) for p in t) for t in d['tris']], d['tags']


def ents(src):
    rows, cur = [], None
    for ln in open(os.path.join(src, 'ents.txt'), encoding='latin-1'):
        ln = ln.strip()
        if ln == '{':
            cur = {}
        elif ln == '}':
            rows.append(cur)
        elif ln and cur is not None:
            k, v = ln.split(' ', 1)
            cur[k] = v.strip('"')
    return rows


def multiset_diff(a, b, key):
    ca, cb = collections.Counter(key(t) for t in a), collections.Counter(key(t) for t in b)
    only_a = sum((ca - cb).values()); only_b = sum((cb - ca).values())
    return {'original': len(a), 'round_trip': len(b), 'only_in_original': only_a, 'only_in_round_trip': only_b,
            'matched': len(a) - only_a}


def emitcheck(src):
    r = subprocess.run([sys.executable, '-B', os.path.join(IWZ, 'iwz_emitcheck.py'), 'check', src], capture_output=True, text=True)
    lines = (r.stdout or '').strip().splitlines()
    return {'exit': r.returncode, 'summary': lines[0] if lines else '', 'findings': [l.strip() for l in lines[1:6]]}


def main(argv):
    a, b = argv[0], argv[1]
    rep = {}
    wa, W1 = world_tris(a); wb, W2 = world_tris(b)
    ta = [t for m in wa.values() for t in m]; tb = [t for m in wb.values() for t in m]
    rep['world'] = multiset_diff(ta, tb, tkey)
    rep['world']['area_original'] = round(sum(area(t) for t in ta)); rep['world']['area_round_trip'] = round(sum(area(t) for t in tb))
    rep['world']['materials'] = {m: [len(wa.get(m, [])), len(wb.get(m, []))] for m in sorted(set(wa) | set(wb)) if len(wa.get(m, [])) != len(wb.get(m, []))}
    rep['world']['surfaces'] = [len(W1['surfaces']), len(W2['surfaces'])]
    def lmset(W):
        v = W['verts']
        return collections.Counter((tuple(round(float(c), 1) for c in p), round(float(l[0]), 4), round(float(l[1]), 4)) for p, l in zip(v['pos'], v['lm']))
    la_, lb_ = lmset(W1), lmset(W2)
    rep['world']['vertices_with_same_position_and_lightmap_uv'] = [sum(min(la_[k], lb_[k]) for k in la_), sum(la_.values()), sum(lb_.values())]
    ca, ga = col_tris(a); cb, gb = col_tris(b)
    rep['collision'] = multiset_diff(ca, cb, tkey)
    rep['collision']['area_original'] = round(sum(area(t) for t in ca)); rep['collision']['area_round_trip'] = round(sum(area(t) for t in cb))
    rep['collision']['tags'] = [dict(collections.Counter(ga)), dict(collections.Counter(gb))]
    ea, eb = ents(a), ents(b)
    def census(es):
        c = collections.Counter()
        for e in es:
            c[(e.get('157', '?'), e.get('822', '') or e.get('638', ''))] += 1
        return c
    A_, B_ = census(ea), census(eb)
    keys = sorted(set(A_) | set(B_))
    rep['entities'] = {'original': len(ea), 'round_trip': len(eb),
                       'same': {'%s %s' % k: A_[k] for k in keys if A_[k] == B_[k]},
                       'differ': {'%s %s' % k: [A_[k], B_[k]] for k in keys if A_[k] != B_[k]}}
    la = json.load(open(os.path.join(a, 'layout.json'), encoding='utf-8')); lb = json.load(open(os.path.join(b, 'layout.json'), encoding='utf-8'))
    size = lambda v: len(v) if hasattr(v, '__len__') else v
    common = sorted(set(la) & set(lb))
    rep['layout'] = {'keys_only_in_original': sorted(set(la) - set(lb)), 'keys_only_in_round_trip': sorted(set(lb) - set(la)),
                     'same_size': [k for k in common if size(la[k]) == size(lb[k])],
                     'different_size': {k: [size(la[k]), size(lb[k])] for k in common if size(la[k]) != size(lb[k])}}
    rep['emitcheck'] = {'original': emitcheck(a), 'round_trip': emitcheck(b)}
    na = os.path.getsize(os.path.join(a, 'navgraph.bin')); nb = os.path.getsize(os.path.join(b, 'navgraph.bin'))
    rep['navgraph_bytes'] = [na, nb]
    if '--json' in argv:
        json.dump(rep, open(argv[argv.index('--json') + 1], 'w'), indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
