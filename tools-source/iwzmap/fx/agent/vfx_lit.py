"""Classify effects by the lighting of their particle materials: lit (eq_effect_* without _em), emissive (_em),
unlit (effectunlit), distortion. usage: vfx_lit.py <out json> [name filter regex]"""
import json, os, re, sys, glob
R = os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')
P = [R + r'\iwz-map-ref-a\dump\cp_zmb\particlesystem', R + r'\iwz-stage2\fx\ztwork\dump\cp_disco\particlesystem']
M = [R + r'\iwz-stage2\kitimport\ztwork\dump\cp_disco\materials', R + r'\iwz-stage2\level\ztwork\dump\techsets_cp_disco\materials'] + glob.glob(R + r'\iwz-map-ref-a\dump\*\materials')
def strs(p): return sorted(set(m.decode() for m in re.findall(rb'[\x20-\x7e]{4,}', open(p, 'rb').read())))
def vfx_path(n):
    for r in P:
        p = os.path.join(r, n + '.iw7VFX')
        if os.path.isfile(p): return p
def mat(n):
    for r in M:
        p = os.path.join(r, n + '.json')
        if os.path.isfile(p): return json.load(open(p))
def cls(t):
    if 'unlit' in t: return 'unlit'
    if 'distortion' in t: return 'distortion'
    if t.endswith('_em') or '_em_' in t or 'emissive' in t: return 'emissive'
    return 'lit'
def walk(n, seen):
    p = vfx_path(n)
    if not p or n in seen: return []
    seen.add(n); out = []
    for s in strs(p):
        if s == n: continue
        if vfx_path(s): out += walk(s, seen)
        else:
            j = mat(s)
            if j and j.get('techniqueSet->name'):
                em = [c.get('literal') for c in (j.get('constantTable') or []) if c['name'] == 'emissivePara']
                out.append((s, j['techniqueSet->name'], cls(j['techniqueSet->name']), em[0][0] if em and em[0] else None))
    return out
flt = re.compile(sys.argv[2] if len(sys.argv) > 2 else '.')
res = {}
for r in P:
    for f in glob.glob(os.path.join(r, '**', '*.iw7VFX'), recursive=True):
        n = os.path.relpath(f, r)[:-7].replace(os.sep, '/')
        if not flt.search(n): continue
        ms = walk(n, set())
        if ms: res[n] = {'classes': sorted(set(m[2] for m in ms)), 'materials': ms}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
for n, v in sorted(res.items()): print(','.join(v['classes']).ljust(28), n)
