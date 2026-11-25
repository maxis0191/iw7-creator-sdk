"""A bake that starts from an earlier bake of nearly the same map (numpy only: no numba, importable by any Python).

`lmbake.bake(..., reuse={'baked': <a baked emit folder>, ['world': <the unbaked world.bin it was made from>], ['config': <its lights.json>]})`

The earlier bake (the SEED) is a folder the baker wrote: `bake.npz` (the float images and the texels), `bake.json` (the atlas and its chart list),
`bake_config.json` (the light list it was given) and `world_unbaked.bin` (the world it started from); a bake made before those two files were
written names them with `config` and `world`. The new map is the seed's map with something added, removed or changed: a room behind a doorway,
lights, an emissive sign.

What is kept and what is baked again, per lightmap chart (a planar group of triangles of one surface):

  carried   the chart is in both maps (the same triangles, material, texel grid) and nothing that lights it changed: its texels are the seed's,
            value for value, at the seed's place in the atlas
  baked     every other chart: new geometry, and a chart of both maps
              light      inside the radius of a light that was added, removed or changed
              shadow     inside the radius of a kept light whose rays to it pass a piece of geometry that was added or removed
              near       within `reach` of added or removed geometry (it receives or loses bounced light; twice `reach` when that geometry emits)
              material   its material's albedo or emission changed
              ambient    inside an ambient room that was added, removed or changed
              bounce     within `reach` of a chart baked again for light, shadow or material (the light it throws back changed)

A chart baked again gathers its bounced light from ALL texels: the carried ones give the radiance the seed computed for them. A carried chart does not
see the change at all: the error is the bounced light of the change at more than `reach` (default 256 units) from it, which the caller measures
against the grain of the bake (tests/test_lmbake_reuse.py).

The seed is refused (the bake is then a full one, and says why) when the two bakes would not be the same light: another texel size or number of
bounces, fewer rays in the seed than asked, another ambient, sky, sun or default albedo.
"""
import json
import os

import numpy as np

Q = 8.0                     # corner positions are compared to 1/8 unit (the baker's own corner key)
REACH = 256.0
REASONS = ('carried', 'new', 'light', 'shadow', 'near', 'material', 'ambient', 'bounce', 'texels')
GLOBAL_KEYS = ('sky', 'sun', 'sun_bounce', 'default_albedo')


class Refused(Exception):
    """the seed cannot be used: the message is the reason"""


# ------------------------------------------------------------------------------------------------ geometry helpers
def box_point_dist(mn, mx, o):
    """distance of the boxes (k, 3), (k, 3) from the point o (3,) -> (k,)"""
    d = np.maximum(np.maximum(mn - o, o - mx), 0.0)
    return np.sqrt((d * d).sum(-1))


def box_box_dist(mn, mx, gmn, gmx):
    """distance between every box of (k, 3) and every box of (g, 3) -> (k, g)"""
    d = np.maximum(np.maximum(mn[:, None, :] - gmx[None, :, :], gmn[None, :, :] - mx[:, None, :]), 0.0)
    return np.sqrt((d * d).sum(-1))


def lights_reaching(lights, mn, mx):
    """per light {origin, radius}: which boxes lie inside its radius -> (lights, boxes) bool. The rule of `light` above; a tool that says
    "this light reaches base surfaces" uses the same function, so its number is the bake's."""
    out = np.zeros((len(lights), len(mn)), bool)
    for k, l in enumerate(lights):
        out[k] = box_point_dist(mn, mx, np.array(l['origin'], float)) < float(l['radius'])
    return out


def shadowed(o, radius, mn, mx, gmn, gmx, chunk=256):
    """boxes (k) inside the radius of a light at `o` whose rays from the light can pass a changed box (g): bounding spheres, the changed box not
    farther from the light than the box's far side -> (k,) bool"""
    out = np.zeros(len(mn), bool)
    if not len(gmn) or not len(mn):
        return out
    gin = box_point_dist(gmn, gmx, o) < radius
    cin = box_point_dist(mn, mx, o) < radius
    if not gin.any() or not cin.any():
        return out
    gc, gr = (gmn[gin] + gmx[gin]) / 2 - o, np.linalg.norm(gmx[gin] - gmn[gin], axis=1) / 2
    gd = np.linalg.norm(gc, axis=1)
    ci = np.nonzero(cin)[0]
    cc, cr = (mn[ci] + mx[ci]) / 2 - o, np.linalg.norm(mx[ci] - mn[ci], axis=1) / 2
    cd = np.linalg.norm(cc, axis=1)
    ga = np.where(gd > gr, np.arcsin(np.clip(gr / np.maximum(gd, 1e-9), 0, 1)), np.pi)
    ca = np.where(cd > cr, np.arcsin(np.clip(cr / np.maximum(cd, 1e-9), 0, 1)), np.pi)
    gu = gc / np.maximum(gd, 1e-9)[:, None]
    cu = cc / np.maximum(cd, 1e-9)[:, None]
    hit = np.zeros(len(ci), bool)
    for g0 in range(0, len(gu), chunk):
        ang = np.arccos(np.clip(cu @ gu[g0:g0 + chunk].T, -1, 1))                    # (k, g)
        hit |= ((ang < ca[:, None] + ga[None, g0:g0 + chunk]) & (gd[None, g0:g0 + chunk] - gr[None, g0:g0 + chunk] < (cd + cr)[:, None])).any(1)
    out[ci] = hit
    return out


def near(mn, mx, gmn, gmx, reach, chunk=256):
    """boxes (k) within reach[j] of a changed box j -> (k,) bool"""
    out = np.zeros(len(mn), bool)
    if not len(gmn) or not len(mn):
        return out
    reach = np.broadcast_to(np.asarray(reach, float), (len(gmn),))
    lo, hi = (gmn - reach[:, None]).min(0), (gmx + reach[:, None]).max(0)
    cand = np.nonzero(np.all((mx >= lo) & (mn <= hi), axis=1))[0]
    if not len(cand):
        return out
    hit = np.zeros(len(cand), bool)
    for g0 in range(0, len(gmn), chunk):
        hit |= (box_box_dist(mn[cand], mx[cand], gmn[g0:g0 + chunk], gmx[g0:g0 + chunk]) < reach[None, g0:g0 + chunk]).any(1)
    out[cand] = hit
    return out


def classify(mn, mx, mat_changed, lights_changed, lights_kept, gmn, gmx, g_emits, rooms_changed, reach=REACH):
    """the rule, on boxes alone. mn, mx (k, 3): the charts that are in both maps; mat_changed (k,) bool; lights_*: [{origin, radius}];
    gmn, gmx (g, 3) and g_emits (g,) bool: the geometry added or removed; rooms_changed: [[x0, y0, z0, x1, y1, z1]] -> (k,) indices into REASONS"""
    k = len(mn)
    why = np.zeros(k, np.int8)

    def mark(sel, name):
        why[sel & (why == 0)] = REASONS.index(name)

    lit = np.zeros(k, bool)
    for l in lights_changed:
        lit |= box_point_dist(mn, mx, np.array(l['origin'], float)) < float(l['radius'])
    mark(lit, 'light')
    sh = np.zeros(k, bool)
    for l in lights_kept:
        sh |= shadowed(np.array(l['origin'], float), float(l['radius']), mn, mx, gmn, gmx)
    mark(sh, 'shadow')
    mark(np.asarray(mat_changed, bool), 'material')
    src = why != 0                                           # these throw back another light than before
    rg = np.where(np.asarray(g_emits, bool), 2.0 * reach, reach) if len(gmn) else np.zeros(0)
    mark(near(mn, mx, gmn, gmx, rg), 'near')
    amb = np.zeros(k, bool)
    for b in rooms_changed:
        b = np.array(b, float)
        amb |= np.all((mx >= b[:3]) & (mn <= b[3:]), axis=1)
    mark(amb, 'ambient')
    if src.any():
        mark(near(mn, mx, mn[src], mx[src], reach), 'bounce')
    return why


# ------------------------------------------------------------------------------------------------ charts of two worlds
def chart_key(c, pos, material):
    q = np.round(pos[np.array(c['tris'], np.int64)] * Q).astype(np.int64)            # (t, 3, 3)
    tris = tuple(sorted(tuple(sorted(map(tuple, t))) for t in q.tolist()))
    frame = tuple(np.round(np.concatenate([c['n'], c['t'], c['b']]) * 64).astype(np.int64).tolist())
    return (material, tris, frame, int(c['ns']), int(c['nr']), int(round(c['s0'] * Q)), int(round(c['r0'] * Q)))


def chart_box(c, pos):
    p = pos[np.array(c['verts'], np.int64)]
    return p.min(0), p.max(0)


def _multiset_delta(old, new):
    """-> (items of new that old has not, items of old that new has not), as multisets of their JSON text"""
    def bag(xs):
        d = {}
        for x in xs:
            s = json.dumps(x, sort_keys=True)
            d.setdefault(s, []).append(x)
        return d
    a, b = bag(old), bag(new)
    added = [x for s, xs in b.items() for x in xs[len(a.get(s, ())):]]
    removed = [x for s, xs in a.items() for x in xs[len(b.get(s, ())):]]
    return added, removed


def _occ_box(o):
    c = np.array(o['corners'] if 'corners' in o else [o['min'], o['max']], float)
    return c.min(0), c.max(0)


def _mat_values(cfg, name):
    return (list(cfg.get('albedo', {}).get(name, cfg.get('default_albedo', [0.5, 0.5, 0.5]))), list(cfg.get('emissive', {}).get(name, [0, 0, 0])))


class _Arrays:
    """the arrays of a bake.npz, each read once"""

    def __init__(self, path):
        self._z = np.load(path)
        self.files = list(self._z.files)
        self._c = {}

    def __getitem__(self, k):
        if k not in self._c:
            self._c[k] = self._z[k]
        return self._c[k]


def load_seed(reuse):
    """the seed's files -> dict (Refused when one is missing)"""
    baked = reuse['baked']
    cfgp = reuse.get('config') or os.path.join(baked, 'bake_config.json')
    worldp = reuse.get('world') or os.path.join(baked, 'world_unbaked.bin')
    for p, what in ((os.path.join(baked, 'bake.npz'), 'bake.npz (the texels of the bake)'), (os.path.join(baked, 'bake.json'), 'bake.json'),
                    (cfgp, 'the light list the bake was given (bake_config.json, or `config`)'), (worldp, 'the unbaked world the bake started from (world_unbaked.bin, or `world`)')):
        if not os.path.isfile(p):
            raise Refused('the seed %s has no %s' % (baked, what))
    z = _Arrays(os.path.join(baked, 'bake.npz'))
    with open(os.path.join(baked, 'bake.json'), encoding='utf-8') as f:
        bj = json.load(f)
    with open(cfgp, encoding='utf-8') as f:
        cfg = json.load(f)
    return {'baked': baked, 'npz': z, 'json': bj, 'cfg': cfg, 'world_path': worldp}


def check_settings(seed, cfg, texel, bounces, rays, pattern=None):
    """Refused when the seed and the bake asked for would not be the same light"""
    bj, old = seed['json'], seed['cfg']
    if pattern:
        raise Refused('a calibration pattern is baked: no reuse')
    if abs(float(bj['texel']) - float(texel)) > 1e-9:
        raise Refused('the seed has texel %s, texel %s is asked' % (bj['texel'], texel))
    ob = bj.get('bounces_used', bj.get('bounces'))
    if int(ob) != int(bounces):
        raise Refused('the seed has %s bounces, %s are asked' % (ob, bounces))
    if int(bj.get('rays_per_texel', 0)) < int(rays):
        raise Refused('the seed was baked with %s rays a texel, %s are asked (a seed is never coarser than the bake that carries it)' % (bj.get('rays_per_texel'), rays))
    for k in GLOBAL_KEYS:
        if json.dumps(old.get(k), sort_keys=True) != json.dumps(cfg.get(k), sort_keys=True):
            raise Refused('the bake setting `%s` changed (%s -> %s): every chart would differ' % (k, json.dumps(old.get(k)), json.dumps(cfg.get(k))))
    oa, na = dict(old.get('ambient') or {}), dict(cfg.get('ambient') or {})
    oa.pop('rooms', None)
    na.pop('rooms', None)
    if json.dumps(oa, sort_keys=True) != json.dumps(na, sort_keys=True):
        raise Refused('the ambient changed (%s -> %s): every chart would differ' % (json.dumps(oa), json.dumps(na)))


def plan(seed, old_charts, old_w, charts, w, cfg, reach=REACH):
    """seed: load_seed's dict; old_charts, old_w: the baker's charts of the seed's unbaked world (after the vertex split) and that world;
    charts, w: the same of the new world; cfg: the new light list.
    -> {'old': [old chart index | -1 per new chart], 'why': [index into REASONS per new chart], 'removed': n, 'counts': {reason: charts}, ...}"""
    bj, old_cfg, z = seed['json'], seed['cfg'], seed['npz']
    cl = bj['chart_list']
    if len(old_charts) != len(cl) or any([c['ns'], c['nr']] != list(e['texels']) for c, e in zip(old_charts, cl)):
        raise Refused('the unbaked world given for the seed is not the one its bake was made from (%d charts against %d in bake.json, or other chart sizes)' % (len(old_charts), len(cl)))
    opos, npos = old_w['verts']['pos'].astype(np.float64), w['verts']['pos'].astype(np.float64)
    omat, nmat = old_w['materials'], w['materials']
    have = {}
    for oi, c in enumerate(old_charts):
        have.setdefault(chart_key(c, opos, omat[c['mat']]), []).append(oi)
    n = len(charts)
    old_of = np.full(n, -1, np.int64)
    for ci, c in enumerate(charts):
        lst = have.get(chart_key(c, npos, nmat[c['mat']]))
        if lst:
            old_of[ci] = lst.pop(0)
    removed = sorted(oi for lst in have.values() for oi in lst)
    matched = np.nonzero(old_of >= 0)[0]
    fresh = np.nonzero(old_of < 0)[0]

    # what changed
    l_add, l_rem = _multiset_delta(old_cfg.get('lights') or [], cfg.get('lights') or [])
    l_changed = l_add + l_rem
    gone = {json.dumps(x, sort_keys=True) for x in l_rem}
    l_kept = [l for l in (cfg.get('lights') or []) if json.dumps(l, sort_keys=True) not in gone and l not in l_add]
    names = sorted(set(omat) & set(nmat))
    mats_changed = {m for m in names if _mat_values(old_cfg, m) != _mat_values(cfg, m)}
    o_add, o_rem = _multiset_delta(old_cfg.get('occluders') or [], cfg.get('occluders') or [])
    r_add, r_rem = _multiset_delta((old_cfg.get('ambient') or {}).get('rooms') or [], (cfg.get('ambient') or {}).get('rooms') or [])
    gb, ge = [], []
    for ci in fresh:
        gb.append(chart_box(charts[ci], npos))
        ge.append(max(_mat_values(cfg, nmat[charts[ci]['mat']])[1]) > 0)
    for oi in removed:
        gb.append(chart_box(old_charts[oi], opos))
        ge.append(max(_mat_values(old_cfg, omat[old_charts[oi]['mat']])[1]) > 0)
    for o in o_add + o_rem:
        gb.append(_occ_box(o))
        ge.append(bool(o.get('emissive')) and max(o['emissive']) > 0)
    gmn = np.array([b[0] for b in gb], float).reshape(-1, 3)
    gmx = np.array([b[1] for b in gb], float).reshape(-1, 3)
    boxes = [chart_box(charts[ci], npos) for ci in matched]
    mn = np.array([b[0] for b in boxes], float).reshape(-1, 3)
    mx = np.array([b[1] for b in boxes], float).reshape(-1, 3)
    mc = np.array([nmat[charts[ci]['mat']] in mats_changed for ci in matched], bool)
    why_m = classify(mn, mx, mc, l_changed, l_kept, gmn, gmx, np.array(ge, bool), [r['box'] for r in r_add + r_rem], reach)
    why = np.full(n, REASONS.index('new'), np.int8)
    why[matched] = why_m
    counts = {r: int((why == k).sum()) for k, r in enumerate(REASONS)}
    return {'old': old_of, 'why': why, 'removed': len(removed), 'counts': counts, 'reach': reach,
            'changes': {'lights_added': len(l_add), 'lights_removed': len(l_rem), 'materials': sorted(mats_changed), 'geometry_boxes': len(gb),
                        'occluders_added': len(o_add), 'occluders_removed': len(o_rem), 'ambient_rooms': len(r_add) + len(r_rem)}}


# ------------------------------------------------------------------------------------------------ the atlas
def pack_keep(charts, old_of, seed, pad):
    """every chart that the seed has keeps the seed's rectangle; the new ones go under the seed's last row (the atlas doubles when they do not fit:
    its height first, then its width, as the baker's own packer never makes it taller than wide). Rectangles of charts that are gone stay empty.
    -> (W, H, grown)"""
    cl = seed['json']['chart_list']
    W, H = seed['json']['atlas']
    a4 = lambda x: (x + 3) & ~3
    used = 0
    new = []
    for ci, c in enumerate(charts):
        c['w'] = a4(c['ns'] + 2 * pad)
        c['h'] = a4(c['nr'] + 2 * pad)
        oi = int(old_of[ci])
        if oi >= 0:
            x, y, w_, h_ = cl[oi]['rect']
            if (w_, h_) != (c['w'], c['h']):
                raise Refused('chart %d has another size than its rectangle in the seed' % ci)
            c['x'], c['y'] = x, y
        else:
            new.append(ci)
    for e in cl:                                         # the seed's whole layout is kept free of new charts, the holes of removed charts too
        used = max(used, e['rect'][1] + e['rect'][3])
    new.sort(key=lambda i: (-charts[i]['h'], -charts[i]['w']))
    W0, H0 = W, H
    while True:
        regions = [(0, used, W0, H)]                     # (x0, y0, x1, y1): under the seed's rows, then the strip a wider atlas adds
        if W > W0:
            regions.append((W0, 0, W, H))
        ok = True
        it = iter(regions)
        x0, y0, x1, y1 = next(it)
        x, y, shelf = x0, y0, 0
        for i in new:
            c = charts[i]
            while True:
                if c['w'] > x1 - x0:
                    fits = False
                else:
                    if x + c['w'] > x1:
                        x, y, shelf = x0, y + shelf, 0
                    fits = y + c['h'] <= y1
                if fits:
                    break
                nxt = next(it, None)
                if nxt is None:
                    ok = False
                    break
                x0, y0, x1, y1 = nxt
                x, y, shelf = x0, y0, 0
            if not ok:
                break
            c['x'], c['y'] = x, y
            x += c['w']
            shelf = max(shelf, c['h'])
        if ok:
            return W, H, (W, H) != (W0, H0)
        if H < W:
            H *= 2
        elif W < 4096:
            W *= 2
        else:
            raise SystemExit('atlas does not fit 4096 x 4096 with the seed\'s layout kept (bake without reuse, or increase --texel)')


def texel_map(plan_, charts, tx_chart, tx_pos, seed):
    """the carried charts' texels: new texel index -> seed texel index. A chart whose texels are not the seed's (count or place) is baked instead
    (reason `texels`). -> (new indices, seed indices), both (m,)"""
    z = seed['npz']
    o_chart, o_pos = z['tx_chart'], z['tx_pos']
    new_idx, old_idx = [], []
    for ci in np.nonzero(plan_['why'] == 0)[0]:
        oi = int(plan_['old'][ci])
        a0, a1 = np.searchsorted(tx_chart, [ci, ci + 1])
        b0, b1 = np.searchsorted(o_chart, [oi, oi + 1])
        if a1 - a0 != b1 - b0 or (a1 > a0 and np.abs(tx_pos[a0:a1] - o_pos[b0:b1]).max() > 0.02):
            plan_['why'][ci] = REASONS.index('texels')
            continue
        new_idx.append(np.arange(a0, a1))
        old_idx.append(np.arange(b0, b1))
    cat = lambda xs: np.concatenate(xs) if xs else np.zeros(0, np.int64)
    plan_['counts'] = {r: int((plan_['why'] == k).sum()) for k, r in enumerate(REASONS)}
    return cat(new_idx), cat(old_idx)


def grid_origin(seed, mn, cell):
    """the light grid's lower corner on the seed's lattice (a room that extends the world's bounds must not shift every cell) -> (3,)"""
    g = seed['npz']['grid'] if 'grid' in seed['npz'].files else None
    if g is None or not len(g):
        return np.array(mn, float)
    first = g[:, :3].min(0)                              # a cell centre of the seed
    mn = np.array(mn, float)
    off = np.array([cell / 2, cell / 2, min(cell / 2, 48)])
    base = first - off                                   # the seed's lower corner
    k = np.ceil((base - mn) / cell - 1e-9)
    return base - np.maximum(k, 0) * cell if np.all(np.isfinite(base)) else mn
