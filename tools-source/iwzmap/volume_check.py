"""Offline check of the trigger volumes of a compiled IW7 map: does every brush-model trigger entity (info_volume,
trigger_*) have an entity physics shape that the engine can point-test, of the size of its trigger model, and do the
spawn volumes contain their spawners and the walkable cells of their zone?

Why: IW7 `ispointinvolume` (GScr 0x140B374B0) does not use the TriggerHull bounds. It takes the entity's Havok body id
(-1 -> false), scales the point by 1/32 and runs a Havok point query against the body, built from
MapEnts.havokEntsShapeData (hk_2014 HavokPhysicsShapeList) through TriggerModel.physicsAsset +
physicsShapeOverrideIdx. A generated trigger model without a shape is never "inside" (Station Zero g5), and a box
shape whose planes or minimum bounds keep another size clips the volume to that size (g8).

Inputs: the map asset dump that `zonetool -iwzcompile` writes (<work>/dump/<map>/maps/cp) or that
`-dumpzonetypes <zone> mapents` writes: <map>.d3dbsp.ents, .ents.data, .ents.data.hkx.

    python -I volume_check.py <maps/cp dir> <map> [--plan <src>/plan.json] [--require-spawners] [--json out.json]

--plan checks every nav cell centre of the generator plan (+8 or +40 units, the gameplay harness convention) against
the spawn volume of its zone (info_volume script_noteworthy); --gap-regions lists plan regions allowed outside.
Exit code 0 when everything checked passes, 1 otherwise. Stock cp_zmb passes without --require-spawners (its
window/gate spawners are outside their volumes by design).
"""
import argparse
import json
import math
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hkpack import Packfile  # noqa: E402

SCALE = 32.0          # Havok entity shapes are stored in units / 32
TOL = 1e-3 * SCALE    # 1/1000 shape unit, in game units
PROBE_HEIGHTS = (8.0, 40.0)


class Pack:
    """Data section view of an entity shape packfile: pointer fixups, object classes, typed reads."""

    def __init__(self, data):
        pf = Packfile(data)
        d = pf.data_sec
        self.body = d.body
        self.local = {a: b for a, b in d.locals}
        self.glob = {a: b for a, sec, b in d.globals if sec == pf.contents_sec}
        self.cls = {a: n for a, n, _ in pf.objects}
        self.contents = pf.contents_off

    def u16(self, o):
        return struct.unpack_from('<H', self.body, o)[0]

    def u32(self, o):
        return struct.unpack_from('<I', self.body, o)[0]

    def vec(self, o, n=3):
        return struct.unpack_from('<%df' % n, self.body, o)

    def shapes(self):
        if self.cls.get(self.contents) != 'HavokPhysicsShapeList':
            raise ValueError('contents is %s, not HavokPhysicsShapeList' % self.cls.get(self.contents))
        arr, n = self.local.get(self.contents), self.u32(self.contents + 8)
        return [self.glob.get(arr + 8 * i) for i in range(n)]


def _r(v):
    return tuple(round(x, 1) for x in v)


def shape_geom(pk, comp):
    """Decode an entity shape (hknpDynamicCompoundShape of hknpConvexPolytopeShape instances) into game-unit convex
    pieces and check that it is one consistent solid: every vertex inside every plane, every plane touching >= 3
    vertices, the compound AABB equal to the vertex bounds, the tree root containing them."""
    r = dict(ok=False, why='', pieces=[], aabbs=[], mins=None, maxs=None)
    if comp is None or pk.cls.get(comp) != 'hknpDynamicCompoundShape':
        r['why'] = 'shape is %s' % (pk.cls.get(comp) if comp is not None else 'null')
        return r
    inst, ninst = pk.local.get(comp + 0x60), pk.u32(comp + 0x68)
    if inst is None or ninst < 1:
        r['why'] = 'compound has no instance'
        return r
    for k in range(ninst):
        ib = inst + 0x80 * k
        rot = [pk.vec(ib + 16 * c) for c in range(3)]          # hkRotation columns
        tr = [x * SCALE for x in pk.vec(ib + 0x30)]
        sc = pk.vec(ib + 0x40)
        poly = pk.glob.get(ib + 0x50)
        if pk.cls.get(poly) != 'hknpConvexPolytopeShape':
            r['why'] = 'instance %d shape is %s' % (k, pk.cls.get(poly))
            return r
        if abs(pk.vec(poly + 0x14, 1)[0]) > 1e-6:
            r['why'] = 'convex radius'
            return r
        if any(abs(s - 1) > 1e-5 for s in sc):
            r['why'] = 'scaled instance'
            return r
        nv, ov = pk.u16(poly + 0x30), pk.u16(poly + 0x32)
        npl, opl = pk.u16(poly + 0x40), pk.u16(poly + 0x42)
        lv = [tuple(x * SCALE for x in pk.vec(poly + 0x30 + ov + 16 * i)) for i in range(nv)]
        lp = [pk.vec(poly + 0x40 + opl + 16 * i, 4) for i in range(npl)]
        for p in lp:
            support = 0
            for v in lv:
                e = p[0] * v[0] + p[1] * v[1] + p[2] * v[2] + p[3] * SCALE
                if e > TOL:
                    r['why'] = 'vertex %s outside plane (%.3g %.3g %.3g %.1f) by %.1f' % (_r(v), p[0], p[1], p[2], p[3] * SCALE, e)
                    return r
                support += abs(e) <= TOL
            if support < 3:
                r['why'] = 'plane (%.3g %.3g %.3g %.1f) touches %d vertices' % (p[0], p[1], p[2], p[3] * SCALE, support)
                return r
        wv = [tuple(rot[0][i] * v[0] + rot[1][i] * v[1] + rot[2][i] * v[2] + tr[i] for i in range(3)) for v in lv]
        wp = []
        for p in lp:
            n = tuple(rot[0][i] * p[0] + rot[1][i] * p[1] + rot[2][i] * p[2] for i in range(3))
            wp.append((n[0], n[1], n[2], p[3] * SCALE - sum(n[i] * tr[i] for i in range(3))))
        r['pieces'].append(dict(verts=wv, planes=wp))
    allv = [v for pc in r['pieces'] for v in pc['verts']]
    r['mins'] = tuple(min(v[a] for v in allv) for a in range(3))
    r['maxs'] = tuple(max(v[a] for v in allv) for a in range(3))
    r['aabbs'].append(('compound', tuple(x * SCALE for x in pk.vec(comp + 0x80)), tuple(x * SCALE for x in pk.vec(comp + 0x90))))
    data = pk.glob.get(comp + 0xc0)
    tree = []
    if pk.cls.get(data) == 'hknpDynamicCompoundShapeData':
        nodes, nn = pk.local.get(data + 0x10), pk.u32(data + 0x18)
        for i in range(nn if nodes is not None else 0):
            lo, hi = tuple(x * SCALE for x in pk.vec(nodes + 32 * i)), tuple(x * SCALE for x in pk.vec(nodes + 32 * i + 16))
            if any(x != 0 for x in lo + hi):
                tree.append(('tree%d' % i, lo, hi))
    if tree:   # child nodes cover subsets of the instances; the root covers all
        r['aabbs'].append(max(tree, key=lambda t: sum(t[2][a] - t[1][a] for a in range(3))))
    for name, lo, hi in r['aabbs']:
        if any(lo[a] > r['mins'][a] + TOL or hi[a] < r['maxs'][a] - TOL for a in range(3)):
            r['why'] = '%s aabb %s..%s does not contain the vertices %s..%s' % (name, _r(lo), _r(hi), _r(r['mins']), _r(r['maxs']))
            return r
    lo, hi = r['aabbs'][0][1], r['aabbs'][0][2]
    if any(abs(lo[a] - r['mins'][a]) > TOL or abs(hi[a] - r['maxs'][a]) > TOL for a in range(3)):
        r['why'] = 'compound aabb %s..%s != vertex bounds %s..%s' % (_r(lo), _r(hi), _r(r['mins']), _r(r['maxs']))
        return r
    r['ok'] = True
    return r


def point_in_shape(shape, local):
    """Point (game units, relative to the entity origin) inside the shape: inside the bounds and one convex piece."""
    for _, lo, hi in shape['aabbs']:
        if any(local[a] < lo[a] - TOL or local[a] > hi[a] + TOL for a in range(3)):
            return False
    return any(pc['planes'] and all(n0 * local[0] + n1 * local[1] + n2 * local[2] + d <= TOL for n0, n1, n2, d in pc['planes'])
               for pc in shape['pieces'])


def parse_ents_data(path):
    """Leading records of a ZoneTool IW7 MapEnts dump: MapEnts, TriggerModel[] (+ physics asset names), TriggerHull[]."""
    with open(path, 'rb') as f:
        d = f.read()

    def arr(p, size):
        t, ex = d[p], d[p + 1]
        if t != 8:
            raise ValueError('record type %d at %d is not an array' % (t, p))
        if not ex:
            return [], p + 2
        n = struct.unpack_from('<I', d, p + 2)[0]
        return [d[p + 6 + i * size:p + 6 + (i + 1) * size] for i in range(n)], p + 6 + n * size

    _, p = arr(0, 0x340)
    models, p = arr(p, 32)
    entries, names = ['MapEnts', 'TriggerModel[]'], []
    for _ in models:
        t = d[p]
        if t == 9:                                   # already dumped: index into the dumper's entry list
            names.append(entries[struct.unpack_from('<I', d, p + 1)[0]]); p += 9
        elif t == 7 and d[p + 1]:
            z = d.index(b'\0', p + 2)
            entries.append(d[p + 2:z].decode()); names.append(entries[-1]); p = z + 1
        elif t == 7:
            names.append(None); p += 2
        else:
            raise ValueError('bad asset record %d' % t)
    hulls, p = arr(p, 32)
    out = []
    for i, m in enumerate(models):
        contents, hc, fh, _wc, _fw, flags = struct.unpack_from('<iHHHHI', m, 0)
        out.append(dict(index=i, contents=contents & 0xffffffff, hullCount=hc, flags=flags, physicsAsset=names[i],
                        shape=struct.unpack_from('<H', m, 24)[0],
                        hulls=[dict(mid=struct.unpack_from('<3f', hulls[h], 0), half=struct.unpack_from('<3f', hulls[h], 12))
                               for h in range(fh, fh + hc)]))
    return out


KEYS = {'157': 'classname', '822': 'targetname', '820': 'target', '543': 'origin', '497': 'model',
        '636': 'script_noteworthy', '65': 'angles'}


def parse_ents(path):
    with open(path, 'rb') as f:
        text = f.read().decode('latin-1')
    ents = []
    for block in re.findall(r'\{([^{}]*)\}', text):
        e = {}
        for k, v in re.findall(r'^\s*"?([^"\s]+)"?\s+"([^"]*)"', block, re.M):
            e[KEYS.get(k, k)] = v
        ents.append(e)
    return ents


def vec3(s):
    return tuple(float(x) for x in s.split())


def in_volume(vol, p):
    return any(point_in_shape(vol['shape'], (p[0] - vol['origin'][0], p[1] - vol['origin'][1], p[2] + h - vol['origin'][2]))
               for h in PROBE_HEIGHTS)


def check(maps_dir, mapname, plan=None, require_spawners=False, gap_regions=(), check_all=False, layout=None):
    # a scene-generated map (scenegen.py) names extra volumes of one zone <zone>_<k> and may place an opening's cells
    # on either side of the wall: its layout says which zone each volume and each opening belongs to
    vol_zone = {v['name']: v['zone'] for v in (layout or {}).get('volumes', [])}
    portal_zones = {'portal:' + o['name']: set(o['zones']) for o in (layout or {}).get('openings', []) if 'zones' in o}
    base = os.path.join(maps_dir, mapname + '.d3dbsp')
    ents = parse_ents(base + '.ents')
    models = parse_ents_data(base + '.ents.data')
    with open(base + '.ents.data.hkx', 'rb') as f:
        pk = Pack(f.read())
    shapes = pk.shapes()
    rows, fails, vols = [], 0, []
    by_name = {}
    for e in ents:
        if e.get('targetname'):
            by_name.setdefault(e['targetname'], []).append(e)
    used = {}
    for i, e in enumerate(ents):
        m, cls = e.get('model', ''), e.get('classname', '')
        if not m.startswith('?') or not (check_all or cls == 'info_volume' or cls.startswith('trigger_')):
            continue
        row = dict(ent=i, classname=cls, targetname=e.get('targetname'), noteworthy=e.get('script_noteworthy'), model=m, ok=False)
        rows.append(row)
        n = int(m[1:]) if m[1:].isdigit() else -1
        if not 0 <= n < len(models):
            row['why'] = 'model %s is not one of the %d trigger models' % (m, len(models))
            continue
        tm = models[n]
        row.update(physicsAsset=tm['physicsAsset'], shape=tm['shape'])
        if not tm['physicsAsset']:
            row['why'] = 'trigger model has no physics asset: no entity body, never inside'
            continue
        if tm['shape'] >= len(shapes):
            row['why'] = 'shape %d is not one of the %d entity shapes' % (tm['shape'], len(shapes))
            continue
        used.setdefault(tm['shape'], set()).add(m)
        sh = shape_geom(pk, shapes[tm['shape']])
        row['bounds'] = (sh['mins'] and _r(sh['mins']), sh['maxs'] and _r(sh['maxs']))
        if not sh['ok']:
            row['why'] = sh['why']
            continue
        hmin = tuple(min(h['mid'][a] - h['half'][a] for h in tm['hulls']) for a in range(3))
        hmax = tuple(max(h['mid'][a] + h['half'][a] for h in tm['hulls']) for a in range(3))
        if tm['hulls'] and any(abs(hmin[a] - sh['mins'][a]) > 1 or abs(hmax[a] - sh['maxs'][a]) > 1 for a in range(3)):
            row['why'] = 'shape bounds %s..%s != trigger model bounds %s..%s' % (_r(sh['mins']), _r(sh['maxs']), _r(hmin), _r(hmax))
            continue
        row['ok'] = True
        if e.get('angles') and any(abs(x) > 1e-3 for x in vec3(e['angles'])):
            row['note'] = 'rotated entity: point tests skipped'
            continue
        vol = dict(row=row, shape=sh, origin=vec3(e.get('origin', '0 0 0')), zone=vol_zone.get(e.get('script_noteworthy'), e.get('script_noteworthy')))
        if cls == 'info_volume' and e.get('targetname') == 'spawn_volume':
            vols.append(vol)
            sp = [s for s in by_name.get(e.get('target'), []) if s.get('classname') == 'script_struct' and s.get('origin')]
            out = [s['origin'] for s in sp if not in_volume(vol, vec3(s['origin']))]
            row.update(spawners=len(sp), spawners_inside=len(sp) - len(out), spawners_outside=out)
            if out and require_spawners:
                row['ok'] = False
                row['why'] = '%d of %d spawners outside the volume' % (len(out), len(sp))
    for k, ms in used.items():
        if len(ms) > 1:
            rows.append(dict(ok=False, why='entity shape %d shared by trigger models %s' % (k, sorted(ms))))
    fails = sum(1 for r in rows if not r['ok'])
    cells_report = None
    if plan:
        zone_of = {r['name']: r['zone'] for r in plan['regions']}
        by_zone = {v['zone']: v for v in vols}
        stats = dict(cells=0, own=0, other_only=0, none=0, several=0, gaps=0)
        regions = {}
        samples = []
        for i, j, z, region in plan['cells']:
            p = ((i + 0.5) * 32, (j + 0.5) * 32, z)
            zone = zone_of.get(region)
            hits = [v['zone'] for v in vols if in_volume(v, p)]
            stats['cells'] += 1
            rs = regions.setdefault(region, dict(zone=zone, cells=0, own=0, none=0, other_only=0))
            rs['cells'] += 1
            if len(hits) > 1:
                stats['several'] += 1
            if zone in hits or portal_zones.get(region, set()) & set(hits):
                stats['own'] += 1; rs['own'] += 1
            elif region in gap_regions:
                stats['gaps'] += 1
            elif hits:
                stats['other_only'] += 1; rs['other_only'] += 1
                samples.append((p, region, zone, hits))
            else:
                stats['none'] += 1; rs['none'] += 1
                samples.append((p, region, zone, hits))
            if zone not in by_zone and zone not in ('none', None):
                rs['no_volume'] = True
        cells_report = dict(stats, regions=regions, samples=samples[:40])
        if stats['none'] or stats['other_only']:
            fails += 1
    return dict(map=mapname, trigger_models=len(models), entity_shapes=len(shapes), checked=len(rows), fails=fails,
                rows=rows, cells=cells_report)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('maps_dir')
    ap.add_argument('map')
    ap.add_argument('--plan', help='generator plan.json: nav cells with their region/zone')
    ap.add_argument('--gap-regions', default='', help='comma separated plan regions allowed outside every volume')
    ap.add_argument('--require-spawners', action='store_true', help='fail when a spawner is outside its spawn volume')
    ap.add_argument('--all', action='store_true', help='check every ?N brush entity, not only info_volume / trigger_*')
    ap.add_argument('--layout', help='generator layout.json: zone of each volume and of each opening (scene-generated maps)')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    plan = None
    if a.plan:
        with open(a.plan) as f:
            plan = json.load(f)
    layout = None
    if a.layout:
        with open(a.layout) as f:
            layout = json.load(f)
    r = check(a.maps_dir, a.map, plan, a.require_spawners, set(filter(None, a.gap_regions.split(','))), a.all, layout)
    for row in r['rows']:
        extra = ' spawners %d/%d' % (row['spawners_inside'], row['spawners']) if 'spawners' in row else ''
        print('%s %s %s %s %s shape %s bounds %s%s %s' % ('PASS' if row['ok'] else 'FAIL', row.get('classname'), row.get('targetname'),
              row.get('noteworthy'), row.get('model'), row.get('shape'), row.get('bounds'), extra, row.get('why', row.get('note', ''))))
    c = r['cells']
    if c:
        for name, rs in sorted(c['regions'].items()):
            if rs['own'] != rs['cells']:
                print('CELLS region=%s zone=%s cells=%d own=%d none=%d other_only=%d%s' % (
                    name, rs['zone'], rs['cells'], rs['own'], rs['none'], rs['other_only'], ' NO_VOLUME' if rs.get('no_volume') else ''))
        print('CELLS cells=%(cells)d own=%(own)d none=%(none)d other_only=%(other_only)d several=%(several)d gaps=%(gaps)d' % c)
    print('VOLUMECHECK map=%s checked=%d fails=%d trigger_models=%d entity_shapes=%d' % (
        r['map'], r['checked'], r['fails'], r['trigger_models'], r['entity_shapes']))
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(r, f, indent=1, default=str)
    return 1 if r['fails'] else 0


if __name__ == '__main__':
    sys.exit(main())
