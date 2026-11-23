"""Baked shadows of static props: the baker's `occluders` list from an emit's smodels.txt.

A static model blocks light in the bake as the oriented box of its xmodel bounds (the bounds the compiler writes to
smodels.bounds.json, placed with the compiler's own angles_to_axis, scale and origin). Limits, on purpose and stated:
  * the box is solid: the gap between the legs of a table is shadowed too, a lamp's open frame is a block;
  * a model whose box holds a light is dropped (a hanging lamp must not shadow its own light), so are boxes with an
    extent over `max_extent` (an arch or a stage piece would shadow a whole passage), boxes under `min_extent` on every
    axis (a bolt), and models flagged `noshadow` in smodels.txt;
  * a model that no dump root and no sidecar knows is skipped and counted (`unknown_models` of the report).
Bounds come from `<emit>/smodel_bounds.json` ({model: {"mins": [x,y,z], "maxs": [x,y,z]}}, written by an authoring tool that
knows its own models) first, else from the xmodel files (`xmodel/<name>.xmb`) under the dump roots, read with
catalog/ztdump.py.
"""
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'catalog'))


def angles_to_axis(a):
    """iwzmap.cpp angles_to_axis: rows forward, left, up (pitch, yaw, roll in degrees)"""
    r = math.pi / 180.0
    sp, cp, sy, cy, sr, cr = (math.sin(a[0] * r), math.cos(a[0] * r), math.sin(a[1] * r), math.cos(a[1] * r),
                              math.sin(a[2] * r), math.cos(a[2] * r))
    f = [cp * cy, cp * sy, -sp]
    rt = [-sr * sp * cy + cr * sy, -sr * sp * sy - cr * cy, -sr * cp]
    u = [cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp]
    return [f, [-v for v in rt], u]


def read_smodels(path):
    """[{model, origin, angles, scale, noshadow, nocollision}] of smodels.txt ([] when the file is absent)"""
    out = []
    if not os.path.isfile(path):
        return out
    for ln in open(path, encoding='utf-8'):
        t = ln.split()
        if len(t) < 8:
            continue
        out.append({'model': t[0], 'origin': [float(v) for v in t[1:4]], 'angles': [float(v) for v in t[4:7]], 'scale': float(t[7]),
                    'noshadow': 'noshadow' in t[8:], 'nocollision': 'nocollision' in t[8:]})
    return out


def model_bounds(names, emit=None, dump_roots=()):
    """{model: (mins, maxs)} for the names that are known; the second result lists the unknown names"""
    side = {}
    if emit and os.path.isfile(os.path.join(emit, 'smodel_bounds.json')):
        side = json.load(open(os.path.join(emit, 'smodel_bounds.json')))
    out, unknown = {}, []
    ztdump = None
    for n in sorted(set(names)):
        if n in side:
            out[n] = (list(side[n]['mins']), list(side[n]['maxs'])); continue
        p = None
        for root in dump_roots:
            hit = glob.glob(os.path.join(root, '*', 'xmodel', n + '.xmb')) + glob.glob(os.path.join(root, 'xmodel', n + '.xmb'))
            if hit:
                p = hit[0]; break
        if not p:
            unknown.append(n); continue
        if ztdump is None:
            import ztdump
        try:
            b = ztdump.read_xmodel(p)['bounds']
            out[n] = (list(b['mins']), list(b['maxs']))
        except Exception:
            unknown.append(n)
    return out, unknown


def oriented_corners(origin, angles, scale, mins, maxs):
    """the 8 world corners of a model's bounds box, in the baker's box order (z low face first, counter clockwise)"""
    ax = angles_to_axis(angles)
    lo, hi = mins, maxs
    local = [(lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]), (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
             (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])]
    return [[origin[k] + scale * sum(ax[j][k] * p[j] for j in range(3)) for k in range(3)] for p in local]


def _contains(corners, point, margin):
    """point inside the box (oriented) grown by margin: tested in the box's own axes"""
    c = corners
    o = c[0]
    ex = [c[1][k] - o[k] for k in range(3)]; ey = [c[3][k] - o[k] for k in range(3)]; ez = [c[4][k] - o[k] for k in range(3)]
    d = [point[k] - o[k] for k in range(3)]
    for e in (ex, ey, ez):
        l2 = sum(v * v for v in e)
        if l2 < 1e-12:
            return False
        t = sum(d[k] * e[k] for k in range(3)) / math.sqrt(l2)
        if t < -margin or t > math.sqrt(l2) + margin:
            return False
    return True


def occluders(emit, dump_roots=(), light_origins=(), min_extent=3.0, max_extent=200.0, light_margin=4.0):
    """-> (list of {'model', 'corners'}, report). Reads <emit>/smodels.txt."""
    sm = read_smodels(os.path.join(emit, 'smodels.txt'))
    bounds, unknown = model_bounds([s['model'] for s in sm], emit, dump_roots)
    out = []
    rep = {'props': len(sm), 'boxes': 0, 'noshadow': 0, 'unknown_models': sorted(set(unknown)), 'unknown_props': 0, 'too_small': 0,
           'too_big': 0, 'hold_a_light': 0, 'bounds_source': 'smodel_bounds.json' if os.path.isfile(os.path.join(emit, 'smodel_bounds.json')) else 'xmodel files'}
    for s in sm:
        if s['noshadow']:
            rep['noshadow'] += 1; continue
        b = bounds.get(s['model'])
        if not b:
            rep['unknown_props'] += 1; continue
        ext = [(b[1][k] - b[0][k]) * s['scale'] for k in range(3)]
        if max(ext) < min_extent:
            rep['too_small'] += 1; continue
        if max(ext) > max_extent:
            rep['too_big'] += 1; continue
        corners = oriented_corners(s['origin'], s['angles'], s['scale'], b[0], b[1])
        if any(_contains(corners, lo, light_margin) for lo in light_origins):
            rep['hold_a_light'] += 1; continue
        out.append({'model': s['model'], 'corners': [[round(v, 3) for v in c] for c in corners]})
    rep['boxes'] = len(out)
    return out, rep
