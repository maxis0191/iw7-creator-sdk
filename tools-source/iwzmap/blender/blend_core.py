"""Blender map exporter, pure part (no bpy): a plain scene dict in, an emit folder out (docs/IWZ-EMIT-CONTRACT.md).

`blend2iwz.py` (inside Blender) turns the .blend into the scene dict (inches, IW7 axes: x east, y north, z up);
`iwz2blend.py` does the reverse. Everything that decides what the compiler reads lives here so that it is testable
with plain Python.

Scene dict (all lengths in inches; every key optional except `map`):
  map, ambient [r,g,b,up], extra_layout {}                     extra_layout keys are merged into layout.json
  meshes [{name, material 'w/...', mode 'both'|'render'|'collision', tag int|None,
           tris [[p0,p1,p2],...]  (counter-clockwise seen from the front), uvs [[uv0,uv1,uv2],...] | None (blender v, up)}]
  zones  [{name, box [x0,y0,z0,x1,y1,z1], probe [r,g,b,up]}]   axis aligned; one spawn volume each, no two may overlap
  starts [{at [x,y,z], yaw}]       spawners [{kind ground|wall|ceiling, at, yaw}]
  doors  [{name, cost 750|1000|1250|1500, box [..6], zones [a,b] | None}]
  power [{at,yaw}]  perks [{at,yaw,perk,powered}]  wall_buys [{at,yaw,weapon_class|weapon,cost,model}]
  pap [{at,yaw}]  wheels [{at,yaw}]  lights [{at,type,color,radius,intensity,dir,inner,outer,group,name,runtime}]
  props [{model,at,angles [pitch,yaw,roll],scale, emissive {color [r,g,b], strength}}]   markers [{kind,id,at,yaw}]
  lighting {prop_shadows, prop_shadow_max_extent, ambient, bounces, sky, sun, emissive {material: {color, strength}}}
           the light settings of the map: written to layout.json "lighting" and read by bake/layout_lights.py (docs/IWZ-EMIT-CONTRACT.md);
           a prop with `emissive` is added to lighting.emissive_props (the bake lights the walls near it)
"""
import collections
import json
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
IWZ = os.path.dirname(HERE)
if IWZ not in sys.path:
    sys.path.insert(0, IWZ)

import mapgen  # noqa: E402
import scenegen  # noqa: E402

CELL = 32
NAV_LIFT = scenegen.NAV_LIFT
MAX_TRIS_PER_SURFACE = 20000       # 3 unshared vertices a triangle stay far under the u16 limit of 65,535
DEG_AREA = 1e-3                    # square inches: below this a triangle is degenerate
DOOR_COSTS = (750, 1000, 1250, 1500)
ZONE_NAME_OK = lambda s: bool(s) and all(c.islower() or c.isdigit() or c == '_' for c in s) and not s[0].isdigit()
STEP = 18.0
HEAD_MIN = 72.0
WALL_CLEAR = 24.0


# ------------------------------------------------------------------------------------------------ vector helpers
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _len(a): return math.sqrt(_dot(a, a))


def tri_normal(p0, p1, p2):
    """(unit normal, double area) of a triangle, counter-clockwise = front"""
    c = _cross(_sub(p1, p0), _sub(p2, p0))
    l = _len(c)
    return ((c[0] / l, c[1] / l, c[2] / l) if l > 0 else (0.0, 0.0, 1.0)), l


def is_degenerate(p0, p1, p2):
    n, a2 = tri_normal(p0, p1, p2)
    return a2 * 0.5 < DEG_AREA


def face_tangent(n):
    import brushkit
    return brushkit.face_tangent(n)


# ------------------------------------------------------------------------------------------------ materials
def material_table():
    """path -> (su, sv) world size of one texture repeat, from the Station Zero material table (stock materials)"""
    import sz2_materials as MT
    return {v['path']: (v['su'], v['sv']) for v in MT.MATERIALS.values()}


def known_materials():
    """names a zone build can find: the material table plus the preview dump index when its dumps exist"""
    names = set(material_table())
    try:
        sys.path.insert(0, os.path.join(IWZ, 'preview'))
        import iwz_assets
        names |= {m for m in iwz_assets.DumpIndex().maps['material'] if m.startswith('w/')}
    except Exception:
        return names, False
    return names, True


# ------------------------------------------------------------------------------------------------ validation
def box_overlap3(a, b, eps=0.5):
    return all(min(a[3 + i], b[3 + i]) - max(a[i], b[i]) > eps for i in range(3))


def in_box(p, b, pad=0.0):
    return all(b[i] - pad <= p[i] <= b[3 + i] + pad for i in range(3))


def validate(scene, materials=None, steps=True):
    """-> list of (severity 'ERROR'|'WARN', message). ERROR = the export refuses."""
    out = []
    E = lambda m: out.append(('ERROR', m))
    W = lambda m: out.append(('WARN', m))
    zones = scene.get('zones', [])
    names = [z['name'] for z in zones]
    if not zones:
        E('no zone volume: add at least one IW7 zone (box) around the playable space')
    for n in names:
        if not ZONE_NAME_OK(n):
            E('zone name %r: use lower case letters, digits and _ (it becomes a script and entity name)' % n)
    for n, c in collections.Counter(names).items():
        if c > 1:
            E('zone name %s is used %d times' % (n, c))
    for i, a in enumerate(zones):
        b = a['box']
        if not (b[3] > b[0] and b[4] > b[1] and b[5] > b[2]):
            E('zone %s: empty box' % a['name'])
        for c in zones[i + 1:]:
            if box_overlap3(a['box'], c['box']):
                E('zones %s and %s overlap (stacked zones must not share height: split them at the slab)' % (a['name'], c['name']))
    if not scene.get('starts'):
        E('no player start')
    for s in scene.get('starts', []):
        if not any(in_box(s['at'], z['box']) for z in zones):
            E('player start at %s is in no zone' % (tuple(round(v) for v in s['at']),))
    for s in scene.get('spawners', []):
        if s.get('kind', 'ground') not in ('ground', 'wall', 'ceiling'):
            E('spawner kind %r (ground, wall or ceiling)' % s.get('kind'))
        if not any(in_box(s['at'], z['box']) for z in zones):
            E('spawner at %s is in no zone' % (tuple(round(v) for v in s['at']),))
    if not scene.get('spawners'):
        W('no zombie spawner')
    for d in scene.get('doors', []):
        if int(d['cost']) not in DOOR_COSTS:
            E('door %s: cost %s, the stock debris purchases are %s' % (d['name'], d['cost'], DOOR_COSTS))
        b = d['box']
        ex, ey = b[3] - b[0], b[4] - b[1]
        if min(ex, ey) > 48.0:
            E('door %s: the box is %.0f x %.0f, one horizontal side must be at most 48 (a door is thin along x or y)' % (d['name'], ex, ey))
        if b[5] - b[2] < 72:
            W('door %s is only %.0f high' % (d['name'], b[5] - b[2]))
        if d.get('zones') is None and len(door_zones(d, zones)) != 2:
            E('door %s does not separate two zones (put a zone box on each side or name them in `zones`)' % d['name'])
    for p in scene.get('perks', []):
        if p['perk'] not in scenegen.Emitter.PERK_SCRIPTABLE:
            E('perk %r is not a stock machine: %s' % (p['perk'], ', '.join(sorted(scenegen.Emitter.PERK_SCRIPTABLE))))
    if len(scene.get('perks', [])) > 6:
        W('more than 6 perk machines: the map limit of the perk module is 6')
    if len({p['perk'] for p in scene.get('perks', [])}) != len(scene.get('perks', [])):
        E('a perk machine is placed twice (each stock scriptable can be relocated once)')
    for w in scene.get('wall_buys', []):
        k = w.get('weapon_class') or ''
        if not w.get('weapon') and k not in scenegen.Emitter.WALL_WEAPON:
            E('wall buy: class %r unknown (%s) and no weapon name' % (k, ', '.join(sorted(scenegen.Emitter.WALL_WEAPON))))
    if len(scene.get('wheels', [])) > len(scenegen.Emitter.WHEEL_SCRIPTABLES):
        E('more mystery boxes than stock wheel scriptables (%d)' % len(scenegen.Emitter.WHEEL_SCRIPTABLES))
    if len(scene.get('pap', [])) > 1:
        E('more than one Pack-a-Punch')
    if len(scene.get('power', [])) > 1:
        E('more than one power switch')
    if materials is not None:
        for m in sorted({m['material'] for m in scene.get('meshes', []) if m.get('mode', 'both') != 'collision'}):
            if m not in materials:
                W('material %s is not in the stock table or the dumps: the zone build may fail on it' % m)
    for m in scene.get('meshes', []):
        if m.get('mode', 'both') != 'collision' and not (m.get('material') or '').startswith('w/'):
            E('mesh %s: material %r is not an IW7 world material (w/...)' % (m['name'], m.get('material')))
    try:
        for r in stair_ramps(scene.get('meshes', []))[1]:
            for ue in r['unrailed_edges'][:5]:
                W('stair %s: a slanted floor edge near (%d, %d) at z %g drops more than 18 into the stair and cannot be railed automatically: add your own clip rail' % ((r['stair'],) + ue))
            if r['foot_clear_depth'] < r['foot_needs']:
                W('stair %s: the foot has only %g units of clear approach in front of the lower edge (48 wanted, the stair wide): zombies and players need room to step on' % (r['stair'], r['foot_clear_depth']))
    except ValueError as e:
        E(str(e))
    if steps and scene.get('meshes') and scene.get('starts'):
        try:
            import numpy  # noqa: F401
            col = scene_collision(scene)
            st = [tuple(s['at']) for s in scene['starts']]
            st_err, st_warn = check_steps(col, st)
            for r in st_err[:10]:
                W('walkable step over 18 at (%d, %d), from %g to %g: zombies cannot climb it (a stair needs iwz_stair, its clip ramp; the export refuses steps between navigation cells)' % r)
            for r in st_warn[:10]:
                W('small step over 18 at (%d, %d), from %g to %g: zombies cannot climb it' % r)
        except ImportError:
            W('numpy missing: the step check was skipped')
        except ValueError as e:
            E(str(e))
    return out


def pad_zone_boxes(zones, max_gap=16.0):
    """zone boxes that face each other across a wall gap of at most 16 units grow by half the gap each (as scenegen does), so no
    walkable point inside the wall opening is in no volume; boxes that overlap in height only"""
    out = [dict(z, box=[float(v) for v in z['box']]) for z in zones]
    grow = [[0.0] * 4 for _ in out]
    for i, a in enumerate(out):
        for j, c in enumerate(out):
            if i == j:
                continue
            A, C = a['box'], c['box']
            if min(A[5], C[5]) - max(A[2], C[2]) <= 0:
                continue
            if min(A[4], C[4]) - max(A[1], C[1]) > 0:
                g = C[0] - A[3]
                if 0 < g <= max_gap: grow[i][2] = max(grow[i][2], g / 2)
                g = A[0] - C[3]
                if 0 < g <= max_gap: grow[i][0] = max(grow[i][0], g / 2)
            if min(A[3], C[3]) - max(A[0], C[0]) > 0:
                g = C[1] - A[4]
                if 0 < g <= max_gap: grow[i][3] = max(grow[i][3], g / 2)
                g = A[1] - C[4]
                if 0 < g <= max_gap: grow[i][1] = max(grow[i][1], g / 2)
    for z, g in zip(out, grow):
        b = z['box']
        z['box'] = [b[0] - g[0], b[1] - g[1], b[2], b[3] + g[2], b[4] + g[3], b[5]]
    return out


# ------------------------------------------------------------------------------------------------ doors
def door_zones(d, zones):
    """names of the zones on the two sides of a door box"""
    b = d['box']
    ex, ey = b[3] - b[0], b[4] - b[1]
    c = ((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, b[2] + 24)
    off = 40 + max(ex, ey) * 0 + (ey if ex >= ey else ex) / 2
    pts = [(c[0], c[1] - off, c[2]), (c[0], c[1] + off, c[2])] if ex >= ey else [(c[0] - off, c[1], c[2]), (c[0] + off, c[1], c[2])]
    found = []
    for p in pts:
        for z in zones:
            if in_box(p, z['box']):
                found.append(z['name']); break
    return [z for z in found] if len(found) == 2 and found[0] != found[1] else []


# ------------------------------------------------------------------------------------------------ world mesh
class WorldBuilder:
    """Adds free-form triangles to a mapgen.Mesh: welded vertices, flat shading frame, surfaces of at most 20,000 triangles"""

    def __init__(self, mesh, lm, mats):
        self.mesh, self.lm, self.mats = mesh, lm, mats
        self.counts = collections.Counter()      # surface key -> triangles
        self.weld = {}
        self.render_tris = 0
        self.col_tris = 0
        self.degenerate = 0
        self.charts_estimate = 0

    def _key(self, base, obj):
        k = 0
        while True:
            key = '%s|%s%s' % (base, obj, '' if k == 0 else '#%d' % k)
            if self.counts[key] < MAX_TRIS_PER_SURFACE:
                return key
            k += 1

    def add(self, rec):
        mode = rec.get('mode', 'both')
        mat = rec.get('material')
        tag = rec.get('tag')
        su, sv = self.mats.get(mat, (128.0, 128.0))
        for ti, tri in enumerate(rec['tris']):
            p = [tuple(float(c) for c in q) for q in tri]
            if is_degenerate(*p):
                self.degenerate += 1
                continue
            n, _ = tri_normal(*p)
            if mode in ('both', 'render') and mat:
                t = face_tangent(n)
                b = _cross(n, t)
                uvs = rec.get('uvs')
                if uvs:
                    uv = [(float(u), 1.0 - float(v)) for u, v in uvs[ti]]
                else:
                    uv = [(_dot(q, t) / su, -_dot(q, b) / sv) for q in p]
                key = self._key(mat, rec['name'])
                verts, idx = self.mesh.mat(key)
                ids = []
                lms = rec.get('lms')
                for qi, (q, (u, v)) in enumerate(zip(p, uv)):
                    lm = tuple(float(c) for c in lms[ti][qi]) if lms else self.lm
                    wk = (key, tuple(round(c, 3) for c in q), round(u, 5), round(v, 5), tuple(round(c, 4) for c in n), lm)
                    vi = self.weld.get(wk)
                    if vi is None:
                        vi = len(verts)
                        verts.append((tuple(round(c, 3) for c in q), u, v, lm, mapgen.pack_unit(n), mapgen.pack_unit(t)))
                        self.weld[wk] = vi
                    ids.append(vi)
                idx += ids
                self.counts[key] += 1
                self.render_tris += 1
            if mode in ('both', 'collision'):
                if tag is not None and int(tag) != scenegen.TAG_SOLID:
                    self.mesh.col_tag[len(self.mesh.col)] = int(tag)
                self.mesh.col.append(tuple(p))
                self.col_tris += 1


# ------------------------------------------------------------------------------------------------ stair ramps
def prism_tris(P, sv, cv, zbot, tops):
    """closed prism: s in sv, c in cv (P maps s, c, z to x, y, z), from zbot up to tops[i] at sv[i]; outward triangles"""
    pt = lambda i, j, k: P(sv[i], cv[j], zbot if k == 0 else tops[i])
    cen = [sum(pt(i, j, k)[m] for i in (0, 1) for j in (0, 1) for k in (0, 1)) / 8.0 for m in range(3)]
    faces = [[(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
    out = []
    for f in faces:
        q4 = [pt(*c_) for c_ in f]
        fc = [sum(p[m] for p in q4) / 4.0 for m in range(3)]
        for t in ([q4[0], q4[1], q4[2]], [q4[0], q4[2], q4[3]]):
            n_, a2_ = tri_normal(*t)
            if a2_ * 0.5 < DEG_AREA:
                continue
            if _dot(n_, _sub(fc, cen)) < 0:
                t = [t[0], t[2], t[1]]
            out.append(t)
    return out


def _in_tri2(x, y, t, eps=1e-6):
    (x0, y0, _), (x1, y1, _), (x2, y2, _) = t
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(d) < 1e-9:
        return False
    a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
    b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
    return a >= -eps and b >= -eps and 1 - a - b >= -eps


def stair_ramps(meshes):
    """The stock stair construction (scenegen.build_flight): an invisible clip sheet over the step nosings, from the floor in front
    of the first riser to the top tread, full stair width. Players and zombies walk on the sheet; navigation is made on it.
    Step meshes carry the property iwz_stair (a stair name; one name = one flight, any number of step objects).
    -> (collision-only mesh records, report rows)"""
    groups = collections.defaultdict(list)
    for m in meshes:
        if m.get('stair') and m.get('mode', 'both') != 'render':
            groups[str(m['stair'])].extend(m['tris'])
    recs, rows = [], []
    # everything that blocks: collision triangles of the other meshes (a stair's own steps are not an obstacle to itself)
    others = {n: [t for m in meshes if m.get('mode', 'both') != 'render' and str(m.get('stair') or '') != n for t in m['tris']] for n in groups}
    for name, tris in sorted(groups.items()):
        tops = collections.defaultdict(list)          # tread height -> triangles of tread tops
        for t in tris:
            n, a2 = tri_normal(*t)
            if a2 * 0.5 >= DEG_AREA and n[2] > 0.95:
                tops[round(sum(p[2] for p in t) / 3.0, 1)].append(t)
        hs = sorted(tops)
        if len(hs) < 2:
            raise ValueError('stair %s: fewer than two tread heights (mark the step meshes with iwz_stair)' % name)
        cx = {h: (sum(p[0] for t in tops[h] for p in t) / (3 * len(tops[h])), sum(p[1] for t in tops[h] for p in t) / (3 * len(tops[h]))) for h in hs}
        dx, dy = cx[hs[-1]][0] - cx[hs[0]][0], cx[hs[-1]][1] - cx[hs[0]][1]
        ax = 0 if abs(dx) >= abs(dy) else 1               # the climb runs along x (0) or y (1)
        sg = 1.0 if (dx if ax == 0 else dy) > 0 else -1.0
        def nosing(h):                                    # the lower edge of the tread, along the climb
            return min(sg * p[ax] for t in tops[h] for p in t) * sg
        ns = [nosing(h) for h in hs]
        rise = hs[1] - hs[0]
        run = abs(ns[1] - ns[0])
        slope = (hs[-1] - hs[0]) / abs(ns[-1] - ns[0]) if abs(ns[-1] - ns[0]) > 1e-6 else 0
        if slope <= 0 or slope > 1.0:
            raise ValueError('stair %s: slope %.2f is not a stair (tread nosings must climb with at most 45 degrees)' % (name, slope))
        # The sheet is the nosing line lifted by RAMP_LIFT: a sheet through the nosings leaves every step box's top front edge on
        # its surface, and zombies caught on them at the foot (Blender test map 1, 22 Nov 2026: two zombies held 40 s at the
        # first nosing). The lifted line meets the floor RAMP_LIFT / slope before the nosing line does, and the landing as much
        # before the last nosing.
        RAMP_LIFT = 2.0
        s0 = ns[0] - sg * run - sg * RAMP_LIFT / slope     # the floor in front of the first riser
        z0 = hs[0] - rise
        s1, z1 = ns[-1] - sg * RAMP_LIFT / slope, hs[-1]
        oth = 1 - ax
        c0 = min(p[oth] for t in tris for p in t)
        c1 = max(p[oth] for t in tris for p in t)
        def P(s_, c_, z_):
            return (s_, c_, z_) if ax == 0 else (c_, s_, z_)
        a, b, c, d = P(s0, c0, z0), P(s1, c0, z1), P(s1, c1, z1), P(s0, c1, z0)
        quad = [[a, b, c], [a, c, d]] if (sg > 0) == (ax == 0) else [[a, c, b], [a, d, c]]
        for t in quad:                                     # the sheet faces up whatever the climb direction
            if tri_normal(*t)[0][2] < 0:
                t[1], t[2] = t[2], t[1]
        recs.append({'name': 'ramp_' + name, 'material': '', 'mode': 'collision', 'tag': None, 'tris': quad, 'uvs': None})
        # clip walls along each long side that is not against a wall: from the floor to the ramp + 64, 8 thick, foot to top landing
        zs = lambda s_: z0 + (z1 - z0) * (s_ - s0) / (s1 - s0)
        walls = []
        lo_s, hi_s = sorted((s0, s1))
        near = [t for t in others[name] if abs(tri_normal(*t)[0][2]) < 0.7 and
                min(p[ax] for p in t) <= hi_s + 8 and max(p[ax] for p in t) >= lo_s - 8 and
                min(p[oth] for p in t) <= c1 + 12 and max(p[oth] for p in t) >= c0 - 12]
        for side, out in ((c0, -1.0), (c1, 1.0)):
            samples = [lo_s + (hi_s - lo_s) * k / 40.0 for k in range(41)]
            hit = 0
            for sm in samples:
                q = side + out * 4.0
                zr = zs(sm)
                for t in near:
                    if min(p[ax] for p in t) - 4 <= sm <= max(p[ax] for p in t) + 4 and min(p[oth] for p in t) - 4 <= q <= max(p[oth] for p in t) + 4 \
                            and min(p[2] for p in t) <= zr + 64 and max(p[2] for p in t) >= zr + 2:
                        hit += 1
                        break
            frac = hit / len(samples)
            if frac >= 0.6:
                walls.append({'side': 'xy'[oth] + ('-' if out < 0 else '+'), 'at': round(side, 2), 'against_wall': round(frac, 2), 'triangles': 0})
                continue
            # inside the stair's width, on the steps (a railing): outside it the wall left an 8-unit sliver of room floor along it
            # and reached into a slab beside a stairwell (test map 1: DROP_ONLY_REGION under the upper floor's edge)
            ca, cb = (side, side + 8.0) if out < 0 else (side - 8.0, side)
            # height max(ramp + 64, top landing + 42): flat to the crossover, then along the ramp + 64 (two convex parts)
            hflat = z1 + 42.0
            sc_ = s0 + (s1 - s0) * ((hflat - 64.0 - z0) / (z1 - z0)) if z1 > z0 else s1
            sc_ = min(max(sc_, min(s0, s1)), max(s0, s1)) if (s1 - s0) * (sc_ - s0) >= 0 else s0
            # the wall runs from the ramp foot to the top landing. Started where the ramp is 18 up, zombies stepped onto the ramp
            # from the open side off the navigation and stuck (1 to 3 of 4 a run); extended 24 onto the floor before the foot, it cut
            # the upper floor off the navigation (test map 1, 22 Nov 2026)
            sw_ = s0
            parts = [((sw_, sc_), (hflat, hflat)), ((sc_, s1), (hflat, zs(s1) + 64.0))]
            wt = []
            for sv_, tops_ in parts:
                if abs(sv_[1] - sv_[0]) > 0.01:
                    wt += prism_tris(P, sv_, (ca, cb), z0, tops_)
            recs.append({'name': 'stairclip_%s_%s' % (name, 'xy'[oth] + ('minus' if out < 0 else 'plus')), 'material': '', 'mode': 'collision', 'tag': None,
                         'tris': wt, 'uvs': None})
            walls.append({'side': 'xy'[oth] + ('-' if out < 0 else '+'), 'at': round(side, 2), 'against_wall': round(frac, 2), 'triangles': len(wt),
                          'height': 'floor %.0f to max(ramp + 64, landing + 42 = %.0f)' % (z0, z1 + 42.0), 'length': round(hi_s - lo_s, 1), 'thickness': 8})
        # rails: floors that border the stair footprint from above (an edge on or within 8 of its boundary, the stair surface more than 18
        # below it along the edge) get a solid clip rail on the floor side of the edge, floor to floor + 42, 4 thick; where the ramp
        # meets the floor (less than 18 below) the edge stays open
        step_lo = min(sg * p[ax] for t in tris for p in t) * sg if sg > 0 else max(sg * p[ax] for t in tris for p in t) * sg
        step_hi = max(sg * p[ax] for t in tris for p in t) * sg if sg > 0 else min(sg * p[ax] for t in tris for p in t) * sg
        slo, shi = sorted((s0, s1, step_lo, step_hi))[0], sorted((s0, s1, step_lo, step_hi))[-1]
        floors = [t for t in others[name] if tri_normal(*t)[0][2] >= 0.64 and max(p[2] for p in t) > z0 + 18 and
                  min(p[ax] for p in t) <= shi + 12 and max(p[ax] for p in t) >= slo - 12 and
                  min(p[oth] for p in t) <= c1 + 12 and max(p[oth] for p in t) >= c0 - 12]
        def covered(q_s, q_c, zf):
            x_, y_ = (q_s, q_c) if ax == 0 else (q_c, q_s)
            return any(abs(sum(p[2] for p in t) / 3.0 - zf) < 2.0 and _in_tri2(x_, y_, t) for t in floors)
        found = {}
        unrailed = []
        for t in floors:
            cx_ = sum(p[oth] for p in t) / 3.0
            sx_ = sum(p[ax] for p in t) / 3.0
            for e0, e1 in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                zf = (e0[2] + e1[2]) / 2.0
                if abs(e0[2] - e1[2]) > 0.5:
                    continue
                if abs(e0[oth] - e1[oth]) < 0.5:          # the edge runs along s at c = const: a long side of the footprint
                    line, kind = e0[oth], 'c'
                    near_ = [c_ for c_ in (c0, c1) if abs(c_ - line) <= 8.0]
                    lo_e, hi_e = sorted((e0[ax], e1[ax]))
                    lo_e, hi_e = max(lo_e, slo), min(hi_e, shi)
                    out_ = -1.0 if cx_ > line else 1.0       # across the edge, away from the floor
                elif abs(e0[ax] - e1[ax]) < 0.5:          # the edge runs along c at s = const: a foot or head end
                    line, kind = e0[ax], 's'
                    near_ = [s_ for s_ in (s0, s1, step_lo, step_hi) if abs(s_ - line) <= 8.0]
                    lo_e, hi_e = sorted((e0[oth], e1[oth]))
                    lo_e, hi_e = max(lo_e, c0), min(hi_e, c1)
                    out_ = -1.0 if sx_ > line else 1.0
                else:
                    # a slanted edge on the footprint boundary with a drop into the stair cannot be railed here
                    inside_ = all(slo - 8 <= p[ax] <= shi + 8 and c0 - 8 <= p[oth] <= c1 + 8 for p in (e0, e1))
                    if inside_ and zf <= z1 + 18.0 and zf - zs(min(max((e0[ax] + e1[ax]) / 2, min(s0, s1)), max(s0, s1))) > 18.0:
                        unrailed.append((round((e0[0] + e1[0]) / 2), round((e0[1] + e1[1]) / 2), round(zf, 1)))
                    continue
                if not near_ or hi_e - lo_e < 1.0:
                    continue
                n_s = max(1, int((hi_e - lo_e) / 4.0))
                ok_run = []
                for k in range(n_s + 1):
                    u = lo_e + (hi_e - lo_e) * k / n_s
                    q_s, q_c = (u, line + out_ * 2.0) if kind == 'c' else (line + out_ * 2.0, u)
                    s_at = u if kind == 'c' else line
                    drop = zf - zs(min(max(s_at, min(s0, s1)), max(s0, s1)))
                    deep = all(covered(*((s_at, line - out_ * dd) if kind == 'c' else (line - out_ * dd, u)), zf) for dd in (4.0, 20.0, 40.0))                         if True else True
                    walled = any(min(p[ax] for p in w_) - 3 <= q_s <= max(p[ax] for p in w_) + 3 and min(p[oth] for p in w_) - 3 <= q_c <= max(p[oth] for p in w_) + 3
                                 and min(p[2] for p in w_) <= zf + 42 and max(p[2] for p in w_) >= zf + 2 for w_ in near)
                    ok_run.append(18.0 < drop and zf <= z1 + 18.0 and deep and not walled and not covered(q_s, q_c, zf))
                key = (kind, round(line, 1), out_, round(zf, 1))
                lst = found.setdefault(key, [])
                k = 0
                while k <= n_s:
                    if ok_run[k]:
                        k2 = k
                        while k2 + 1 <= n_s and ok_run[k2 + 1]:
                            k2 += 1
                        lst.append((lo_e + (hi_e - lo_e) * k / n_s, lo_e + (hi_e - lo_e) * k2 / n_s))
                        k = k2 + 1
                    else:
                        k += 1
        rails = []
        for (kind, line, out_, zf), ivs in sorted(found.items()):
            merged = []
            for lo_i, hi_i in sorted(ivs):
                if merged and lo_i <= merged[-1][1] + 4.5:
                    merged[-1][1] = max(merged[-1][1], hi_i)
                else:
                    merged.append([lo_i, hi_i])
            for lo_i, hi_i in merged:
                lo_i -= 4.0
                hi_i += 4.0                                  # the rails of a corner meet
                thick = (line, line + 4.0) if out_ < 0 else (line - 4.0, line)          # on the floor side of the edge
                sv_, cv_ = ((lo_i, hi_i), thick) if kind == 'c' else (thick, (lo_i, hi_i))
                rt = prism_tris(P, sv_, cv_, zf, (zf + 42.0, zf + 42.0))
                recs.append({'name': 'stairrail_%s_%s%g' % (name, kind, line), 'material': '', 'mode': 'collision', 'tag': None, 'tris': rt, 'uvs': None})
                rails.append({'edge': '%s = %g (%s of the floor)' % ('xy'[oth] if kind == 'c' else 'xy'[ax], line, 'outside' if out_ < 0 else 'inside'),
                              'from': round(lo_i, 1), 'to': round(hi_i, 1), 'length': round(hi_i - lo_i, 1), 'floor_z': round(zf, 1), 'height': 42,
                              'thickness': 4, 'triangles': len(rt)})
        # the approach to the foot: clear depth in front of the lower edge, the stair width wide
        clear = 96.0
        for d_ in range(0, 97, 4):
            lo_ = s0 - sg * d_
            hit_ = False
            for t in others[name]:
                if max(p[2] for p in t) <= z0 + 2 or min(p[2] for p in t) >= z0 + 72:
                    continue
                if min(p[oth] for p in t) < c1 and max(p[oth] for p in t) > c0 and min(p[ax] for p in t) < max(lo_, lo_ - sg * 4) and \
                        max(p[ax] for p in t) > min(lo_, lo_ - sg * 4):
                    hit_ = True
                    break
            if hit_:
                clear = float(d_)
                break
        foot_row = {'foot_clear_depth': clear, 'foot_needs': 48}
        rows.append({'stair': name, 'axis': 'xy'[ax], 'direction': int(sg), 'steps': len(hs), 'rise': round(rise, 3), 'tread': round(run, 3),
                     'ramp_from': [round(v, 2) for v in a], 'ramp_to': [round(v, 2) for v in b], 'width': round(c1 - c0, 2),
                     'slope_deg': round(math.degrees(math.atan(slope)), 2), 'triangles': 2, 'side_walls': walls, 'rails': rails, 'unrailed_edges': sorted(set(unrailed)), **foot_row})
    return recs, rows


def scene_collision(scene):
    """collision triangles of a scene as the exporter will write them (meshes plus stair ramps)"""
    m = mapgen.Mesh()
    wb = WorldBuilder(m, scenegen.LM, {})
    ramps, _ = stair_ramps(scene.get('meshes', []))
    for rec in scene.get('meshes', []) + ramps:
        wb.add(dict(rec, mode='collision' if rec.get('mode', 'both') != 'render' else 'render'))
    return [tuple(t) for t in m.col]


# ------------------------------------------------------------------------------------------------ navigation (fallback)
def nav_single_layer(col_tris, starts, cell=CELL):
    """One floor per 32 unit column from the collision triangles (the format of mapgen.nav_graph holds one height a column).
    Floors: upward triangles of slope <= 50 degrees with 72 units of headroom, 24 units from any wall (wall = steep
    triangle reaching between floor+18 and floor+72). The floor kept per column is the lowest one reachable from a player
    start by steps of at most 18. -> (cells {(i,j): z + NAV_LIFT}, info dict)"""
    import numpy as np
    floors = collections.defaultdict(list)
    ceils = collections.defaultdict(list)
    wall = collections.defaultdict(list)
    for t in col_tris:
        p0, p1, p2 = t
        n, a2 = tri_normal(p0, p1, p2)
        if a2 * 0.5 < DEG_AREA:
            continue
        xs = (p0[0], p1[0], p2[0]); ys = (p0[1], p1[1], p2[1]); zs = (p0[2], p1[2], p2[2])
        if abs(n[2]) >= 0.5:
            i0, i1 = int(math.floor(min(xs) / cell)), int(math.floor(max(xs) / cell))
            j0, j1 = int(math.floor(min(ys) / cell)), int(math.floor(max(ys) / cell))
            ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
            cx = (ii.ravel() + 0.5) * cell; cy = (jj.ravel() + 0.5) * cell
            d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
            if abs(d) < 1e-9:
                continue
            a = ((p1[1] - p2[1]) * (cx - p2[0]) + (p2[0] - p1[0]) * (cy - p2[1])) / d
            b = ((p2[1] - p0[1]) * (cx - p2[0]) + (p0[0] - p2[0]) * (cy - p2[1])) / d
            c = 1 - a - b
            ok = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            for k in np.nonzero(ok)[0]:
                z = a[k] * p0[2] + b[k] * p1[2] + c[k] * p2[2]
                key = (int(ii.ravel()[k]), int(jj.ravel()[k]))
                if n[2] >= 0.64:
                    floors[key].append(float(z))
                elif n[2] <= -0.5:
                    ceils[key].append(float(z))
        if abs(n[2]) < 0.5 or True:
            # a steep triangle is a wall: its footprint edges, sampled every 6 units, with its height range
            if abs(n[2]) < 0.5:
                zlo, zhi = min(zs), max(zs)
                for (a_, b_) in ((p0, p1), (p1, p2), (p2, p0)):
                    L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                    m = max(1, int(L / 6.0))
                    for s in range(m + 1):
                        f = s / m
                        x = a_[0] + (b_[0] - a_[0]) * f; y = a_[1] + (b_[1] - a_[1]) * f
                        wall[(int(math.floor(x / 8)), int(math.floor(y / 8)))].append((zlo, zhi))
    R = int(math.ceil(WALL_CLEAR / 8.0))

    def wall_near(x, y, z):
        cx, cy = int(math.floor(x / 8)), int(math.floor(y / 8))
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                if dx * dx + dy * dy > (R + 0.5) ** 2:
                    continue
                for zlo, zhi in wall.get((cx + dx, cy + dy), ()):
                    if zhi > z + STEP and zlo < z + HEAD_MIN:
                        return True
        return False

    valid = {}
    for key, zl in floors.items():
        zl = sorted(set(round(z, 1) for z in zl))
        # merge floors closer than 0.5 (stacked duplicates)
        keep = []
        for z in zl:
            if keep and z - keep[-1] < 0.5:
                continue
            keep.append(z)
        for z in keep:
            above = [c for c in ceils.get(key, ()) if c > z - 0.5]
            above += [f for f in keep if f > z + 1.0]
            if above and min(above) - z < HEAD_MIN:
                continue
            x, y = (key[0] + 0.5) * cell, (key[1] + 0.5) * cell
            if wall_near(x, y, z):
                continue
            valid.setdefault(key, []).append(z)
    # breadth first search from the starts
    seeds = []
    for s in starts:
        k = (int(math.floor(s[0] / cell)), int(math.floor(s[1] / cell)))
        best = None
        for dk in [(0, 0)] + [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)]:
            kk = (k[0] + dk[0], k[1] + dk[1])
            for z in valid.get(kk, ()):
                d = abs(z - s[2])
                if d <= 36 and (best is None or d < best[0]):
                    best = (d, kk, z)
        if best:
            seeds.append((best[1], best[2]))
    seen = set(seeds)
    dq = collections.deque(seeds)
    while dq:
        k, z = dq.popleft()
        for dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            kk = (k[0] + dk[0], k[1] + dk[1])
            for z2 in valid.get(kk, ()):
                if abs(z2 - z) <= STEP and (kk, z2) not in seen:
                    seen.add((kk, z2)); dq.append((kk, z2))
    info = {'method': 'single layer height field (fallback, mapgen.nav_graph)', 'floor_samples': sum(len(v) for v in valid.values()),
            'seeds': len(seeds), 'starts': len(starts)}
    if not seeds:
        info['warning'] = 'no player start found a floor: every valid floor was kept (lowest per column)'
        seen = {(k, min(v)) for k, v in valid.items()}
    cells, dropped = {}, 0
    for (k, z) in sorted(seen, key=lambda t: (t[0], t[1])):
        if k in cells:
            dropped += 1                    # a second floor in this column (room over room): not representable
            continue
        cells[k] = round(z + NAV_LIFT, 2)
    info['cells'] = len(cells)
    info['dropped_upper_floors'] = dropped
    info['unreached_floor_samples'] = info['floor_samples'] - len(seen) if seeds else 0
    return cells, info


def find_steps(valid, seeds, cell=CELL):
    """Walkable steps over 18 (up to 40) between neighbouring columns: floors a player reaches (steps up to 40 allowed, i.e. with
    a jump) but that zombies, which climb 18, cannot. A step to a floor that is part of a large level area (a flight's treads and
    landing, a raised room: 8 cells or more joined by steps of at most 18) is an ERROR; a small one (a crate, a ledge) a warning.
    A stair under a clip ramp has no such step: the ramp surface is the only floor there. -> (errors, warnings) of
    (x, y, z_low, z_high); `cell` is the column size of `valid`"""
    nodes = [(k, z) for k, zs in valid.items() for z in zs]
    if not nodes or not seeds:
        return [], []
    idx = {n: i for i, n in enumerate(nodes)}
    parent = list(range(len(nodes)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    nb = collections.defaultdict(list)
    for (k, z) in nodes:
        for dk in ((1, 0), (0, 1)):
            k2 = (k[0] + dk[0], k[1] + dk[1])
            for z2 in valid.get(k2, ()):
                d = abs(z2 - z)
                if d <= STEP:
                    parent[find(idx[(k, z)])] = find(idx[(k2, z2)])
                if d <= 40.0:
                    nb[(k, z)].append(((k2, z2), d))
                    nb[(k2, z2)].append(((k, z), d))
    size = collections.Counter(find(i) for i in range(len(nodes)))
    seen = set(seeds)
    dq = collections.deque(seeds)
    while dq:
        n = dq.popleft()
        for m, d in nb.get(n, ()):
            if m not in seen:
                seen.add(m)
                dq.append(m)
    errs, warns = [], []
    for n in seen:
        for m, d in nb.get(n, ()):
            if d > STEP and m in seen and m[1] > n[1]:
                row = (round((m[0][0] + 0.5) * cell), round((m[0][1] + 0.5) * cell), round(n[1], 1), round(m[1], 1))
                (errs if size[find(idx[m])] >= 8 * (CELL // cell) ** 2 else warns).append(row)
    return sorted(set(errs)), sorted(set(warns))


def step_floors(col_tris, starts, res=8):
    """floors of an 8 unit grid (headroom 72, slope under 50 degrees, no wall clearance: a player walks along walls) and the seeds
    on them -> (valid {column: [z]}, seeds [(column, z)])"""
    import numpy as np
    floors = collections.defaultdict(list)
    ceils = collections.defaultdict(list)
    for t in col_tris:
        p0, p1, p2 = t
        n, a2 = tri_normal(p0, p1, p2)
        if a2 * 0.5 < DEG_AREA or abs(n[2]) < 0.5:
            continue
        xs = (p0[0], p1[0], p2[0]); ys = (p0[1], p1[1], p2[1])
        i0, i1 = int(math.floor(min(xs) / res)), int(math.floor(max(xs) / res))
        j0, j1 = int(math.floor(min(ys) / res)), int(math.floor(max(ys) / res))
        ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
        ii, jj = ii.ravel(), jj.ravel()
        cx = (ii + 0.5) * res; cy = (jj + 0.5) * res
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-9:
            continue
        a = ((p1[1] - p2[1]) * (cx - p2[0]) + (p2[0] - p1[0]) * (cy - p2[1])) / d
        b = ((p2[1] - p0[1]) * (cx - p2[0]) + (p0[0] - p2[0]) * (cy - p2[1])) / d
        c = 1 - a - b
        ok = np.nonzero((a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6))[0]
        zz = a[ok] * p0[2] + b[ok] * p1[2] + c[ok] * p2[2]
        dest = floors if n[2] >= 0.64 else (ceils if n[2] <= -0.5 else None)
        if dest is None:
            continue
        for k, z in zip(ok, zz):
            dest[(int(ii[k]), int(jj[k]))].append(float(z))
    valid = {}
    for key, zl in floors.items():
        keep = []
        for z in sorted(set(round(z, 1) for z in zl)):
            if keep and z - keep[-1] < 0.5:
                continue
            keep.append(z)
        for z in keep:
            above = [c for c in ceils.get(key, ()) if c > z - 0.5] + [f for f in keep if f > z + 1.0]
            if not above or min(above) - z >= HEAD_MIN:
                valid.setdefault(key, []).append(z)
    seeds = []
    for s in starts:
        k = (int(math.floor(s[0] / res)), int(math.floor(s[1] / res)))
        best = None
        for dk in [(a_, b_) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)]:
            for z in valid.get((k[0] + dk[0], k[1] + dk[1]), ()):
                if abs(z - s[2]) <= 36 and (best is None or abs(z - s[2]) < best[0]):
                    best = (abs(z - s[2]), (k[0] + dk[0], k[1] + dk[1]), z)
        if best:
            seeds.append((best[1], best[2]))
    return valid, seeds


def check_steps(col_tris, starts):
    """-> (errors, warnings) of find_steps on the 8 unit floors; (x, y, z_low, z_high)"""
    valid, seeds = step_floors(col_tris, starts)
    return find_steps(valid, seeds, 8)


def _plane_fit(pts):
    """least squares plane z = a x + b y + c through corners (a, b, c); flat at the mean when the corners are collinear"""
    import numpy as np
    P = np.asarray(pts, dtype=float)
    A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]
    try:
        sol = np.linalg.lstsq(A, P[:, 2], rcond=None)[0]
        if np.linalg.matrix_rank(A) < 3:
            raise np.linalg.LinAlgError
        return float(sol[0]), float(sol[1]), float(sol[2])
    except np.linalg.LinAlgError:
        return 0.0, 0.0, float(P[:, 2].mean())


def parse_polygons(data):
    """navgraph bytes -> polygon areas [{'pts': [(x, y, z)], 'nbr': [area index | None per edge], 'c': centre, 'plane': (a, b, c)}]
    (navfmt.py of the navgen branch reads the engine's graph: any graph, round 1 quads or round 2 polygons)"""
    import navfmt
    gr, _end = navfmt.parse_graph(bytes(data)[navfmt.find_graph(bytes(data)):])
    idx = {a.off: k for k, a in enumerate(gr.areas)}
    out = []
    for a in gr.areas:
        pts = [tuple(e.corner) for e in a.edges]
        out.append({'pts': pts, 'nbr': [idx.get(e.nbr) if e.nbr else None for e in a.edges], 'c': tuple(a.centre), 'plane': _plane_fit(pts)})
    return out


def try_navgen(col_tris, starts, log):
    """workstream N: navgen.generate(tris, seeds=...) when the module is importable (`IWZ_NAVGEN_DIR`, or iwzmap/ itself); round 2
    makes convex polygon areas on any number of floors, and its bytes are written as navgraph.bin unchanged.
    -> (navgraph bytes, polygons, report) or (None, None, reason)"""
    d = os.environ.get('IWZ_NAVGEN_DIR')
    if d and d not in sys.path:
        sys.path.insert(0, d)
    try:
        import navgen
    except ImportError as e:
        return None, None, 'navgen.py not importable (%s)' % e
    try:
        # areas='quads' (32-unit lattice rectangles, clipped polygons only at non-axis walkable edges): the shape proven in game on
        # 22 Nov 2026 (testmap1 9/9, zombies climb and descend the stair). Large polygons with corners on straight edges (round 2/3)
        # froze agents in place; IWZ_NAV_AREAS=stock|polygons selects the others.
        mode = os.environ.get('IWZ_NAV_AREAS', 'quads')
        kw = {'areas': mode, 'cell': 32} if mode == 'quads' else {'areas': mode}
        data, rep = navgen.generate(col_tris, seeds=[tuple(s) for s in starts] or None, **kw)
        polys = parse_polygons(data)
        if not isinstance(data, (bytes, bytearray)) or not polys:
            return None, None, 'navgen.generate gave no data or no area'
        rep = {k: v for k, v in rep.items() if k != 'cells_detail'}
        rep['navgen_file'] = os.path.abspath(navgen.__file__)
        return bytes(data), polys, rep
    except Exception as e:                  # report, never hide
        log('navgen failed (%s): using the single layer fallback' % e)
        return None, None, 'navgen failed: %s' % e


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i][0], poly[i][1]
        x1, y1 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


def poly_nodes(polys, cell=CELL):
    """what the rest of the emit needs from polygons: the 32 unit lattice centres inside each area with z from its plane, one
    node per area and floor ((i, j, z) of the lattice cell), plus the centroid cell of an area that holds no lattice centre"""
    nodes = {}
    rep = []
    for k, p in enumerate(polys):
        xs = [q[0] for q in p['pts']]; ys = [q[1] for q in p['pts']]
        a, b, c = p['plane']
        found = False
        for i in range(int(math.floor(min(xs) / cell)), int(math.floor(max(xs) / cell)) + 1):
            for j in range(int(math.floor(min(ys) / cell)), int(math.floor(max(ys) / cell)) + 1):
                x, y = (i + 0.5) * cell, (j + 0.5) * cell
                if point_in_poly(x, y, p['pts']):
                    nodes[(i, j, round(a * x + b * y + c, 2))] = k
                    found = True
        cx, cy, cz = p['c']
        key = (int(math.floor(cx / cell)), int(math.floor(cy / cell)), round(cz, 2))
        nodes.setdefault(key, k)
        rep.append(key)
    return nodes, rep


def link_steps(polys):
    """Links of a polygon graph are shared edges; the step of a link is the height difference of the two areas at that edge
    (both ends and the middle, each area's own plane and corner). -> [(x, y, z_low, z_high)] over 18"""
    out = []
    for k, p in enumerate(polys):
        for e, m in enumerate(p['nbr']):
            if m is None or m < k:
                continue
            q = polys[m]
            c0, c1 = p['pts'][e], p['pts'][(e + 1) % len(p['pts'])]
            worst = 0.0
            for t in (0.0, 0.5, 1.0):
                x, y, z = c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t, c0[2] + (c1[2] - c0[2]) * t
                za = p['plane'][0] * x + p['plane'][1] * y + p['plane'][2]
                zb = q['plane'][0] * x + q['plane'][1] * y + q['plane'][2]
                worst = max(worst, abs(za - zb), abs(z - za), abs(z - zb))
            if worst > STEP:
                zl, zh = sorted((p['plane'][2], q['plane'][2]))
                out.append((round((c0[0] + c1[0]) / 2), round((c0[1] + c1[1]) / 2), round(zl + 0, 1), round(zl + worst, 1)))
    return out


# ------------------------------------------------------------------------------------------------ the emitter
class BlendEmitter(scenegen.Emitter):
    """scenegen.Emitter with the entity placement of a Blender scene (its `ent`, `istruct`, `place_doors`, `door_blockers`,
    `level_script` and the stock tables are reused as they are)"""

    def __init__(self, scene, tpl, out, log=print):
        stub = types.SimpleNamespace(map=scene.get('map', 'cp_iwz'), path=scene.get('source', 'blender'), zones={}, start_zone='',
                                     interactions=[], markers=[])
        super().__init__(stub, tpl, out, log)
        self.scene = scene
        self.problems = []
        self.warnings = []
        self.emissive_props = []
        self.nodes = []
        self.layers = {}
        self.polys = None
        self.lift = NAV_LIFT
        self.vols = []

    # -- geometry ------------------------------------------------------------------------------------------
    def build_world(self):
        mats = material_table()
        wb = WorldBuilder(self.B.mesh, scenegen.LM, mats)
        for rec in self.scene.get('meshes', []):
            wb.add(rec)
        ramps, self.ramp_rows = stair_ramps(self.scene.get('meshes', []))
        for r in self.ramp_rows:
            if r['foot_clear_depth'] < r['foot_needs']:
                self.warnings.append('stair %s: foot clear approach %g < 48' % (r['stair'], r['foot_clear_depth']))
        for rec in ramps:
            wb.add(rec)
        self.wb = wb
        return wb

    def zone_at(self, p):
        for z in self.scene.get('zones', []):
            if in_box(p, z['box']):
                return z['name']
        return None

    def floor_z(self, x, y, z):
        """floor height (nav height without the lift) of the column nearest to (x, y, z), else z"""
        c = self.nav_floor(x, y, z)
        return c - self.lift if c is not None else z

    # -- navigation ----------------------------------------------------------------------------------------
    def build_nav(self):
        col = [tuple(t) for t in self.B.mesh.col]
        starts = [tuple(s['at']) for s in self.scene.get('starts', [])]
        blob, polys, rep = try_navgen(col, starts, self.log)
        cells_fb, info_fb = nav_single_layer(col, starts)
        info_fb['steps_error'], info_fb['steps_warn'] = check_steps(col, starts)
        self.polys = None
        nav_err = []
        if blob:
            nodes = self.set_polys(polys)
            ec = collections.Counter(len(p['pts']) for p in polys)
            self.nav_info = {'used': 'navgen polygons', 'navgen': rep, 'areas': len(polys),
                             'links': sum(1 for p in polys for m in p['nbr'] if m is not None), 'edge_histogram': dict(sorted(ec.items()))}
            nav_blob = blob
            nav_err = link_steps(polys)
        else:
            cells, info = cells_fb, info_fb
            if not cells:
                raise RuntimeError('no walkable column found: the collision has no floor with 72 units of headroom reachable from a start')
            self.lift = NAV_LIFT
            nodes = [(k[0], k[1], z) for k, z in sorted(cells.items())]
            nav_blob, _n = self.mapgen.nav_graph(cells, CELL)
            self.nav_info = dict(info, used='single layer fallback', navgen=rep)
            if info.get('dropped_upper_floors'):
                self.warnings.append('navigation: %d columns have a second floor that the single layer graph cannot hold (room over room): '
                                     'those floors have no navigation until navgen exists' % info['dropped_upper_floors'])
            if info.get('unreached_floor_samples'):
                self.warnings.append('navigation: %d floor samples (roofs and outside surfaces included) are not reachable from a player start by 18 unit steps' % info['unreached_floor_samples'])
        self.set_nodes(nodes)
        self.nav_info['nodes'] = len(nodes)
        # a step between two LINKED areas over 18 (the engine's agents climb 18): a stair without its clip ramp is refused
        err = sorted(set(nav_err))
        nav_warn = list(info_fb['steps_error'])
        if err:
            raise ValueError('scene refused: walkable steps over 18 that zombies cannot climb and no clip ramp covers (mark the step meshes '
                             'with iwz_stair so the exporter adds the stock ramp sheet): ' + '; '.join('at (%d, %d) from %g to %g' % r for r in err[:6]))
        ws = sorted(set(info_fb['steps_warn']) | set(nav_warn))
        if ws:
            r = ws[0]
            self.warnings.append('%d step edges over 18 between floors (ledges, the open side of a stair, crates; first: %g to %g at (%d, %d)): '
                                 'zombies cannot climb them' % (len(ws), r[2], r[3], r[0], r[1]))
        self.nav_info['step_errors'] = len(err)
        self.nav_info['step_warnings'] = len(ws)
        open(os.path.join(self.out, 'navgraph.bin'), 'wb').write(nav_blob)
        self.nav_blob = nav_blob

    def set_polys(self, polys):
        """the navigation is navgen's polygon areas: -> the nodes (one per area); nav_floor then reads the area planes"""
        self.lift = 0.0
        self.polys = polys
        node_map, self.area_rep = poly_nodes(polys)
        self.poly_grid = collections.defaultdict(list)
        for k, p in enumerate(polys):
            xs = [q[0] for q in p['pts']]; ys = [q[1] for q in p['pts']]
            for gx in range(int(min(xs) // 64), int(max(xs) // 64) + 1):
                for gy in range(int(min(ys) // 64), int(max(ys) // 64) + 1):
                    self.poly_grid[(gx, gy)].append(k)
        return sorted(node_map)

    def set_nodes(self, nodes):
        """the navigation nodes [(i, j, z)] the entity placement stands on (z = floor + self.lift)"""
        self.nodes = nodes
        self.layers = collections.defaultdict(list)
        for i, j, z in nodes:
            self.layers[(i, j)].append(z)
        for k in self.layers:
            self.layers[k].sort()

    def node_zone(self, n):
        return self.zone_at(((n[0] + 0.5) * CELL, (n[1] + 0.5) * CELL, n[2] - self.lift + 8))

    def nav_floor(self, x, y, z, reach=48.0):
        """nav height of the floor at (x, y) nearest to z within reach, else None (polygon graph: the area plane at the point)"""
        if getattr(self, 'polys', None):
            best = None
            for k in self.poly_grid.get((int(x // 64), int(y // 64)), ()):
                p = self.polys[k]
                if point_in_poly(x, y, p['pts']):
                    zz = p['plane'][0] * x + p['plane'][1] * y + p['plane'][2]
                    if abs(zz - z) <= reach and (best is None or abs(zz - z) < abs(best - z)):
                        best = zz
            return best
        zs = self.layers.get((int(math.floor(x / CELL)), int(math.floor(y / CELL))), ())
        best = min(zs, key=lambda c: abs(c - self.lift - z), default=None)
        return best if best is not None and abs(best - self.lift - z) <= reach else None

    # -- entities ------------------------------------------------------------------------------------------
    def start_ent(self, s):
        """a player start on the floor under it"""
        x, y, z = s['at']
        z = self.floor_z(x, y, z)
        self.ent(classname='script_struct', targetname='default_player_start', origin=self.fmt((x, y, z)), angles='0 %g 0' % s.get('yaw', 0))
        self.layout['starts'].append((x, y, z))

    def emit_volumes(self, zones, first=0):
        """one spawn volume per zone, numbered from `first` (trigger model ?IWZ<k> = line k of triggers.txt), and the zone rows of the layout;
        the volumes are added to self.vols"""
        new = [{'name': z['name'], 'zone': z['name'], 'box': [float(v) for v in z['box']]} for z in zones]
        for k, v in enumerate(new):
            self.volume_ent(first + k, v)
        self.vols += new
        for z in zones:
            b = z['box']
            self.layout['zones'][z['name']] = {'name': z['name'], 'box': list(b), 'boxes': [[b[0], b[1], b[3], b[4]]], 'floor': b[2], 'ceiling': b[5],
                                               'far': False, 'probe': list(z.get('probe') or (0.9, 0.9, 0.95, 0.6)), 'volumes': [z['name']]}
        return new

    def emit_gameplay(self):
        """the scene's spawners (with the landing, idle and respawn spots of every volume of self.vols), doors and interactions"""
        self.place_scene_spawners()
        self.drop_unused_targets()
        self.place_scene_doors()
        self.place_scene_interactions()

    def emit_markers(self):
        for m in self.scene.get('markers', []):
            self.layout['markers'].append({'kind': m['kind'], 'id': m.get('id', ''), 'zone': self.zone_at(m['at']) or self.sc.start_zone,
                                           'origin': list(m['at']), 'yaw': m.get('yaw', 0),
                                           **({'area': list(m['area'])} if m.get('area') else {})})

    @staticmethod
    def room_row(z):
        """the light grid / reflection probe room of a zone (lighting.txt, probes.txt)"""
        b = z['box']
        r, g, bl, up = z.get('probe') or (0.9, 0.9, 0.95, 0.6)
        return 'room %d %d %d %d %d %d %.3f %.3f %.3f %.2f' % (b[0] - 48, b[1] - 48, b[2] - 48, b[3] + 48, b[4] + 48, b[5] + 48, r, g, bl, up)

    def emit_scene_entities(self):
        sc, layout, mg = self.scene, self.layout, self.mapgen
        zones = sc.get('zones', [])
        ws = mg.stock_worldspawn(os.path.join(self.tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'))
        self.vols = []
        starts = [dict(s) for s in sc['starts']]
        first = starts[0]['at']
        sz = self.zone_at(first)
        self.sc.start_zone = sz or zones[0]['name']
        # up to four starts: pad with the nearest free columns
        if len(starts) < 4:
            used = {(int(math.floor(s['at'][0] / CELL)), int(math.floor(s['at'][1] / CELL))) for s in starts}
            near = sorted((n for n in self.nodes if (n[0], n[1]) not in used and self.node_zone(n) == self.sc.start_zone
                           and abs(n[2] - self.lift - first[2]) <= 48),
                          key=lambda n: ((n[0] + .5) * CELL - first[0]) ** 2 + ((n[1] + .5) * CELL - first[1]) ** 2)
            if near:
                self.warnings.append('player starts: %d placed, padded to 4 on the nearest columns' % len(sc['starts']))
            for n in near[:4 - len(starts)]:
                starts.append({'at': ((n[0] + .5) * CELL, (n[1] + .5) * CELL, n[2] - self.lift), 'yaw': starts[0].get('yaw', 0)})
        for s in starts:
            self.start_ent(s)
        x, y, zz = layout['starts'][0]
        for k in range(8):
            self.ent(classname='trigger_use', targetname='player_use_trigger', origin=self.fmt((x + 40 * (k - 4), y, zz + 40)),
                     model='?%d' % (4 + k % 4), dummy='triggermodeldummydefault')
        self.ent(classname='mp_global_intermission', origin=self.fmt((x, y, zz + 220)), angles='10 270 0')
        self.emit_volumes(zones)
        self.emit_gameplay()
        for tn in ('hidden_room_portal', 'center_portal', 'fast_travel_tube_start', 'fast_travel_tube_end', 'hidden_travel_tube_start',
                   'hidden_travel_tube_end'):
            self.ent(classname='script_model', targetname=tn, model='tag_origin', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='hidden_room_spot', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='brute_hide_org', origin='0 0 -2000')
        self.place_props()
        self.emit_markers()
        if self.smodels:
            try:
                lines = self.size_culls(self.smodels)
            except Exception as e:
                self.warnings.append('static model cull distances not set (%s)' % e)
                lines = self.smodels
            open(os.path.join(self.out, 'smodels.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')
        open(os.path.join(self.out, 'ents.txt'), 'w', newline='\n').write(mg.ents_text(ws, self.ents))
        open(os.path.join(self.out, 'triggers.txt'), 'w', newline='\n').write('\n'.join(self.triggers) + '\n')
        open(os.path.join(self.out, 'scriptables.txt'), 'w', newline='\n').write('\n'.join(self.relocations) + ('\n' if self.relocations else ''))

    def place_scene_spawners(self):
        layout = self.layout
        for sp in self.scene.get('spawners', []):
            x, y, z = sp['at']
            kind = sp.get('kind', 'ground')
            yaw = float(sp.get('yaw', 0))
            zone = self.zone_at((x, y, z))
            if zone is None:
                self.problems.append('spawner at %s is in no zone' % ((round(x), round(y), round(z)),))
                continue
            fz = self.floor_z(x, y, z)
            on_nav = self.nav_floor(x, y, z) is not None
            if not on_nav and kind == 'ground':
                self.problems.append('spawner %s at %s is on no navigation floor (a floor over another floor has none until navgen exists)' % (kind, (round(x), round(y), round(z))))
            e = dict(classname='script_struct', targetname=zone + '_spawner', noteworthy='static', angles='0 %g 0' % yaw)
            if kind == 'ground':
                e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_ground', parameters='ground_spawn_no_boards', fxid='concrete')
            elif kind == 'wall':
                e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_wall_low', parameters='no_boards')
                if sp.get('vent', True):
                    self.vent(zone, x, y, fz, yaw)
            else:
                e.update(origin=self.fmt((x, y, z)), animation='spawn_ceiling', parameters='ground_spawn_no_boards', fxid='ceiling')
            self.ent(**e)
            layout['spawners'].append({'zone': zone, 'volume': zone, 'origin': (x, y, z if kind == 'ceiling' else fz), 'kind': kind, 'yaw': yaw,
                                       'on_nav': on_nav, 'plate': False})
        # landing spots, idle spots and respawns: two of each per zone on its navigation columns, far from each other
        for v in self.vols:
            cand = sorted(n for n in self.nodes if self.node_zone(n) == v['zone'])
            if not cand:
                continue
            chosen = []
            for _ in range(4):
                chosen.append(max(cand, key=lambda n: min([math.hypot(n[0] - c[0], n[1] - c[1]) + abs(n[2] - c[2]) for c in chosen] or [9e9]) - 1e-4 * n[0]))
            for nn, kind in zip(chosen, ('dog', 'dog', 'resp', 'resp')):
                x, y, fz = (nn[0] + .5) * CELL, (nn[1] + .5) * CELL, nn[2] - self.lift
                if kind == 'dog':
                    self.ent(classname='script_struct', targetname='dog_spawner', origin=self.fmt((x, y, fz + 8)), angles='0 0 0', radius=66)
                    self.ent(classname='script_struct', targetname='zombie_idle_spot', origin=self.fmt((x, y, fz + 8)))
                else:
                    self.ent(classname='script_struct', targetname='player_respawn_loc', origin=self.fmt((x, y, fz)), angles='0 0 0')
            self.layout.setdefault('dog_spawners', {})[v['zone']] = [[(n[0] + .5) * CELL, (n[1] + .5) * CELL] for n in chosen[:2]]
            self.layout.setdefault('respawns', {})[v['zone']] = [[(n[0] + .5) * CELL, (n[1] + .5) * CELL] for n in chosen[2:]]
            self.layout.setdefault('zone_points', {})[v['zone']] = [(chosen[0][0] + .5) * CELL, (chosen[0][1] + .5) * CELL, chosen[0][2] - self.lift]
        self.layout['inspection_plates'] = []

    def place_scene_doors(self):
        ops = []
        for d in self.scene.get('doors', []):
            b = d['box']
            zs = d.get('zones') or door_zones(d, self.scene['zones'])
            if len(zs) != 2:
                self.problems.append('door %s: could not tell its two zones' % d['name'])
                continue
            za, zb = zs
            ex, ey = b[3] - b[0], b[4] - b[1]
            axis = 'x' if ex >= ey else 'y'          # axis x: the wall runs along x at y = plane
            plane = (b[1] + b[4]) / 2 if axis == 'x' else (b[0] + b[3]) / 2
            span = [b[0], b[3]] if axis == 'x' else [b[1], b[4]]
            zbox = {z['name']: z['box'] for z in self.scene['zones']}
            def side(zid):
                zb_ = zbox[zid]
                c = (zb_[1] + zb_[4]) / 2 if axis == 'x' else (zb_[0] + zb_[3]) / 2
                return 1 if c >= plane else -1
            fa, fb = side(za), side(zb)
            if fa == fb:
                self.problems.append('door %s: both zones are on the same side of the door plane' % d['name'])
                continue
            ops.append({'kind': 'door', 'zones': [za, zb], 'door': d['name'], 'id': d['name'], 'price': int(d['cost']),
                        'planes': {za: plane, zb: plane}, 'span': span, 'axis': axis, 'sill': float(b[2]), 'top': float(b[5]),
                        'facing': {za: fa, zb: fb}})
        self.ops = ops
        self.place_doors()          # scenegen: interaction structs, door_buy trigger, blocker brushes, layout doors + openings

    def node_pairs(self):
        """pairs of linked nodes: neighbouring columns with floors at most 18 apart (one layer graph), or the representative nodes
        of two linked polygon areas"""
        if getattr(self, 'polys', None):
            for k, p in enumerate(self.polys):
                for m in p['nbr']:
                    if m is not None and m > k:
                        yield self.area_rep[k], self.area_rep[m]
            return
        for n in self.nodes:
            for dk in ((1, 0), (0, 1)):
                for z2 in self.layers.get((n[0] + dk[0], n[1] + dk[1]), ()):
                    if abs(z2 - n[2]) <= STEP:
                        yield n, (n[0] + dk[0], n[1] + dk[1], z2)

    def zone_adjacency(self):
        adj = set()
        for n, m in self.node_pairs():
            za, zb = self.node_zone(n), self.node_zone(m)
            if za and zb and za != zb:
                adj.add(frozenset((za, zb)))
        return adj

    def add_links(self, touching=None, skip=()):
        """zones with a walkable connection that is not a door are linked (spawn adjacency, activated together). `touching` (zone names) keeps
        only the found connections with one of these zones (a layer on a base: the base's own pairs are the base's business); `skip` are
        pairs that are doors or links already. The scene's explicit links always stay"""
        door_pairs = {frozenset(o['zones']) for o in self.ops if o['kind'] == 'door'} | {frozenset(p) for p in skip}
        explicit = {frozenset(l) for l in self.scene.get('links', [])}
        found = self.zone_adjacency()
        if touching is not None:
            found = {p for p in found if p & set(touching)}
        links = (found | explicit) - door_pairs
        for pair in sorted(tuple(sorted(p)) for p in links):
            a, b = pair
            self.ops.append({'kind': 'link', 'zones': [a, b], 'door': '', 'id': 'link_%s_%s' % pair, 'price': 0, 'planes': {a: 0, b: 0},
                             'span': [0, 0], 'axis': 'x', 'sill': 0, 'top': 0, 'facing': {a: 0, b: 0}})
        self.layout['zone_adjacency'] = sorted(sorted(p) for p in self.zone_adjacency())

    def place_scene_interactions(self):
        layout = self.layout
        E = scenegen.Emitter
        zone_of = lambda p: self.zone_at(p) or self.sc.start_zone
        wheels = first_wheel = getattr(self, 'wheels_used', 0)      # a base that already uses stock wheel scriptables: the next free one
        for p in self.scene.get('perks', []):
            org = self.snap(p['at']); yaw = float(p.get('yaw', 0))
            name = 'perk_machine_' + p['perk']
            self.istruct(name, org, yaw, zone_of(org), **({} if p.get('powered') else {'parameters': 'requires_power'}))
            self.relocations.append('%s 0 %g %g %g %g' % (E.PERK_SCRIPTABLE[p['perk']], org[0], org[1], org[2], yaw))
        for w in self.scene.get('wall_buys', []):
            org = self.snap(w['at']); yaw = float(w.get('yaw', 0))
            org = (org[0], org[1], org[2] + 64)
            if w.get('weapon'):
                weapon, wm = w['weapon'], w.get('model') or None
            else:
                weapon, wm = E.WALL_WEAPON[w['weapon_class']]
            kw = {'groupname': 'wall_buy', 'radius': 256}
            if wm:
                kw['model'] = wm
            self.istruct(weapon, org, yaw, zone_of(org), **kw)
            layout['interactions'][-1].update({'class': w.get('weapon_class'), 'price': int(w.get('cost') or 0) or None,
                                               'stand_in': w.get('weapon_class') in E.STAND_IN})
        for w in self.scene.get('wheels', []):
            org = self.snap(w['at']); yaw = float(w.get('yaw', 0))
            sc_ = E.WHEEL_SCRIPTABLES[wheels]; wheels += 1
            self.relocations.append('%s 0 %g %g %g %g' % (sc_, org[0], org[1], org[2], yaw))
            fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            self.ent(classname='script_struct', noteworthy='spinner', model='zmb_magic_wheel_spinner',
                     origin=self.fmt((org[0] + 8 * fx, org[1] + 8 * fy, org[2] + 55.6)), angles='0 %g 0' % yaw)
            self.ent(classname='script_model', noteworthy='out_of_order', model='tag_origin', origin=self.fmt((org[0], org[1], org[2] + 37)))
            rx, ry = math.cos(math.radians(yaw - 90)), math.sin(math.radians(yaw - 90))
            self.ent(classname='script_struct', targetname='wheel_fx_spot', origin=self.fmt((org[0] + 8 * fx + 14 * rx, org[1] + 8 * fy + 14 * ry, org[2] + 55.2)),
                     angles='0 %g 0' % yaw)
            layout['interactions'].append({'kind': 'magic_wheel', 'scriptable': sc_, 'origin': org, 'yaw': yaw, 'zone': zone_of(org), 'first': wheels == 1})
        if wheels > first_wheel:
            layout['first_wheel_zone'] = next(i for i in layout['interactions'] if i['kind'] == 'magic_wheel')['zone']
        for p in self.scene.get('power', []):
            org = self.snap(p['at']); yaw = float(p.get('yaw', 0))
            org = (org[0], org[1], org[2] + 50)
            self.istruct('generator', org, yaw, zone_of(org), parameters=p.get('parameters', 'power_all'), target='iwz_power_switch')
            self.ent(classname='script_model', targetname='iwz_power_switch', model='icbm_electricpanel_switch_02', noteworthy='-pitch',
                     origin=self.fmt(org), angles='75 %g 0' % yaw)
        for p in self.scene.get('pap', []):
            org = self.snap(p['at']); yaw = float(p.get('yaw', 0))
            self.istruct('weapon_upgrade', org, yaw, zone_of(org), parameters='requires_power', target='iwz_pap_spot')
            (mx, my), (sx, sy) = self.pap_offsets(org, yaw)
            self.relocations.append('pap_machine 0 %g %g %g %g' % (mx, my, org[2], yaw))
            self.ent(classname='script_struct', targetname='iwz_pap_spot', origin=self.fmt((sx, sy, org[2] + 14)),
                     angles='0 %g 0' % yaw, model='weapon_e_ak47_rare_wm')

    @staticmethod
    def pap_offsets(org, yaw):
        """the machine (10 units) and the weapon spot (20 units) stand behind the use point, against the facing of `yaw`
        (yaw 270 faces -y: the machine at y + 10, the spot at y + 20, as every map built before 27 Nov 2026 has them)"""
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        return ((round(org[0] - 10 * fx, 2), round(org[1] - 10 * fy, 2)), (round(org[0] - 20 * fx, 2), round(org[1] - 20 * fy, 2)))

    def snap(self, at):
        x, y, z = at
        return (round(x, 2), round(y, 2), round(self.floor_z(x, y, z), 2))

    def place_props(self):
        for p in self.scene.get('props', []):
            x, y, z = p['at']
            pitch, yaw, roll = p.get('angles', (0, 0, 0))
            sc_ = float(p.get('scale', 1.0))
            self.smodels.append('%s %g %g %g %g %g %g %g' % (p['model'], x, y, z, pitch, yaw, roll, sc_))
            if p.get('emissive'):
                e = p['emissive']
                self.emissive_props.append({'model': p['model'], 'origin': [x, y, z], 'angles': [pitch, yaw, roll], 'scale': sc_,
                                            'color': [float(c) for c in e.get('color', (1.0, 1.0, 1.0))], 'strength': float(e.get('strength', 1.0))})
            self.layout.setdefault('decor', []).append({'zone': self.zone_at((x, y, z)) or '', 'model': p['model'], 'origin': [x, y, z],
                                                        'yaw': yaw, 'pitch': pitch, 'roll': roll, 'scale': sc_, 'clip': None, 'static': True})

    def place_lights(self):
        lines = []
        nrun, nshadow = {}, 0
        for L in self.scene.get('lights', []):
            x, y, z = L['at']
            rec = {'zone': self.zone_at((x, y, z)) or '', 'origin': [round(x, 2), round(y, 2), round(z, 2)], 'type': L.get('type', 'omni'),
                   'color': [round(float(c), 4) for c in L.get('color', (1, 0.97, 0.78))], 'radius': float(L.get('radius', 420)),
                   'intensity': float(L.get('intensity', 2.0)), 'fixture': ''}
            if rec['type'] == 'spot':
                rec.update(dir=[round(float(c), 4) for c in L.get('dir', (0, 0, -1))], inner=float(L.get('inner', 14)), outer=float(L.get('outer', 32)))
            if L.get('group'):
                rec['group'] = L['group']
            if L.get('name'):
                rec['name'] = L['name']
            if L.get('runtime'):
                rec['runtime'] = True
                if L.get('shadows') is not None:
                    rec['shadows'] = bool(L['shadows'])
                if L.get('bake') is False:
                    rec['bake'] = False             # a pure runtime light: bake/layout_lights.py leaves it out of the lightmap
            self.layout['lights'].append(rec)
            if L.get('runtime'):
                nrun[rec['type']] = nrun.get(rec['type'], 0) + 1
                nshadow += 1 if rec.get('shadows') else 0
                row = '%s %g %g %g %g %g %g %g %g' % (rec['type'], x, y, z, *rec['color'], rec['intensity'] * 1000.0, rec['radius'])
                if rec['type'] == 'spot':
                    d = rec['dir']
                    pitch = -math.degrees(math.asin(max(-1, min(1, d[2]))))
                    yaw = math.degrees(math.atan2(d[1], d[0]))
                    row += ' %g %g %g' % (pitch, yaw, rec['outer'] * 2)
                if L.get('shadows') is not None:
                    row += ' %d' % (1 if L['shadows'] else 0)           # lights.txt tail token: a shadow capable slot (iwzmap.cpp read_lights)
                if L.get('name'):
                    row += ' name=' + L['name']
                if L.get('group'):
                    row += ' group=' + L['group']
                lines.append(row)
        if lines:
            open(os.path.join(self.out, 'lights.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')
        # the template (cp_zmb) offers about 860 static spot and 140 static omni primary light slots and 25 scriptable ones (named lights;
        # the range grows downwards over static slots); about 459 of its 1,039 lights can use a shadow map. The compiler refuses a light
        # without a slot (iwzmap.cpp assign_light_slots) and gives a shadow request to a slot without shadow data silently.
        if nrun.get('spot', 0) > 850 or nrun.get('omni', 0) > 130:
            self.problems.append('%d runtime spot and %d runtime omni lights: the template has about 860 and 140 static slots' %
                                 (nrun.get('spot', 0), nrun.get('omni', 0)))
        if nshadow > 64:
            self.warnings.append('%d runtime lights ask for shadows: each is a shadow map pass in the engine, keep it to a few in view together' % nshadow)
        self.layout['runtime_lights'] = {'spot': nrun.get('spot', 0), 'omni': nrun.get('omni', 0), 'shadows': nshadow}

    # -- run -----------------------------------------------------------------------------------------------
    def run(self):
        sc = self.scene
        os.makedirs(self.out, exist_ok=True)
        mats, known_ok = known_materials()
        issues = validate(sc, mats if known_ok else None, steps=False)
        errs = [m for s, m in issues if s == 'ERROR']
        if errs:
            raise ValueError('scene refused:\n  ' + '\n  '.join(errs))
        self.warnings += [m for s, m in issues if s == 'WARN']
        sc['zones'] = pad_zone_boxes(sc['zones'])
        wb = self.build_world()
        if not wb.render_tris:
            raise ValueError('scene has no render triangle')
        self.build_nav()
        self.regions = [{'name': z['name'], 'zone': z['name'], 'rect': [z['box'][0], z['box'][1], z['box'][3], z['box'][4]]} for z in sc['zones']]
        self.emit_scene_entities()
        self.add_links()
        for o in self.ops:
            pass
        self.place_lights()
        # level script: no Station Zero module unless the scene folder brings its own
        import sz_modules
        mdir = sc.get('modules_dir')
        old = sz_modules.MODULES
        sz_modules.MODULES = mdir if mdir and os.path.isdir(mdir) else os.path.join(self.out, '_no_modules')
        try:
            self.level_script()
        finally:
            sz_modules.MODULES = old
        nv, ni, ns, wbnd = mapgen.write_world(self.B.mesh, os.path.join(self.out, 'world.bin'))
        col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in self.B.mesh.col]
        blob, info = self.hk.encode(col, os.path.join(self.tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx'), tag=scenegen.TAG_SOLID,
                                    max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')),
                                    max_extent=(float(os.environ.get('IWZ_MAX_SECTION', '1024')) * mapgen.HAVOK_SCALE) or None,
                                    tags=[self.B.mesh.col_tag.get(i, scenegen.TAG_SOLID) for i in range(len(col))])
        open(os.path.join(self.out, 'colmap.hkx'), 'wb').write(blob)
        amb = ['ambient %g %g %g %g' % tuple(sc.get('ambient') or (0.30, 0.30, 0.32, 0.50))]
        probes = []
        for z in sc['zones']:
            row = self.room_row(z)
            amb.append(row); probes.append(row)
        open(os.path.join(self.out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(amb) + '\n')
        open(os.path.join(self.out, 'probes.txt'), 'w', newline='\n').write('\n'.join(probes) + '\n')
        # plan.json: regions = zones, cells with their zone, adjacency
        owner = {n: (self.node_zone(n) or '_outside') for n in self.nodes}
        if any(v == '_outside' for v in owner.values()):
            n_out = sum(1 for v in owner.values() if v == '_outside')
            self.problems.append('%d navigation cells are in no zone box: zombies there are in no spawn volume' % n_out)
            self.regions.append({'name': '_outside', 'zone': '_outside', 'rect': [0, 0, 0, 0]})
        adj = set()
        for n, m in self.node_pairs():
            if owner[n] != owner[m]:
                adj.add(frozenset((owner[n], owner[m])))
        plan = {'regions': self.regions, 'adj': [sorted(a_) for a_ in adj], 'cells': [[n[0], n[1], n[2], owner[n]] for n in sorted(self.nodes)],
                'cell_corners': [], 'blockers': self.B.blockers, 'col_tris': len(col), 'bounds': wbnd, 'col_walls': []}
        json.dump(plan, open(os.path.join(self.out, 'plan.json'), 'w'))
        self.layout['regions'] = len(self.regions)
        self.layout['volumes'] = self.vols
        s0 = self.sc.start_zone
        self.layout['navconn_routes'] = [[s0, z['name']] for z in sc['zones'] if z['name'] != s0 and z['name'] in set(owner.values())]
        self.layout['far_zones'] = []
        self.layout['modules'] = self.layout.get('modules', [])
        self.layout['stairs'] = []          # the ramps are in scene_report.json `stairs`
        self.layout['blender'] = {'schema': 'iwz.blend/1', 'meshes': len(sc.get('meshes', [])), 'navigation': self.nav_info}
        lighting = dict(sc.get('lighting') or {})
        if self.emissive_props:
            lighting['emissive_props'] = list(lighting.get('emissive_props') or []) + self.emissive_props
        if lighting:
            self.layout['lighting'] = lighting
        for k, v in (sc.get('extra_layout') or {}).items():
            self.layout.setdefault(k, v)
        json.dump(self.layout, open(os.path.join(self.out, 'layout.json'), 'w'), indent=1, default=list)
        json.dump({'custom': {}, 'used': sorted({m['material'] for m in sc.get('meshes', []) if m.get('material')})},
                  open(os.path.join(self.out, 'custom_materials.json'), 'w'), indent=1)
        report = {'schema': 'iw7.blend2iwz/1', 'map': self.sc.map, 'zones': len(sc['zones']), 'volumes': len(self.vols),
                  'doors': len(sc.get('doors', [])), 'spawners': len(self.layout['spawners']),
                  'world': {'vertices': nv, 'indices': ni, 'surfaces': ns, 'render_triangles': wb.render_tris, 'materials': len(self.B.mesh.materials)},
                  'collision': {'triangles': len(col), 'degenerate_dropped_before': wb.degenerate, 'havok': info, 'bytes': len(blob)},
                  'navigation': self.nav_info, 'stairs': self.ramp_rows, 'entities': self.entity_census(), 'problems': self.problems, 'warnings': self.warnings,
                  'lights': len(self.layout['lights'])}
        json.dump(report, open(os.path.join(self.out, 'scene_report.json'), 'w'), indent=1, default=list)
        self.log('blend2iwz %s: %d zones, %d doors, %d spawners, %d render triangles in %d surfaces, %d collision triangles, %d nav cells, '
                 '%d problems, %d warnings' % (self.sc.map, len(sc['zones']), len(sc.get('doors', [])), len(self.layout['spawners']), wb.render_tris,
                                                ns, len(col), len(self.nodes), len(self.problems), len(self.warnings)))
        for p in self.problems:
            self.log('PROBLEM ' + p)
        for w in self.warnings:
            self.log('WARN ' + w)
        return report


def default_template():
    rt = os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')
    return os.path.join(os.environ.get('IWZ_TEMPLATE_DUMP') or os.path.join(rt, 'iwz-map-ref-a', 'dump'), 'cp_zmb')


def export_scene(scene, out, tpl=None, log=print):
    """scene dict -> emit folder `out`; returns the report"""
    return BlendEmitter(scene, tpl or default_template(), out, log).run()


# ------------------------------------------------------------------------------------------------ helpers for scene authors
def box_tris(mn, mx, inward=False, skip=()):
    """12 triangles of an axis aligned box (outward normals, or inward for a room seen from inside); `skip` names faces left out"""
    x0, y0, z0 = mn; x1, y1, z1 = mx
    faces = {
        'top': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        'bottom': [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        'south': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        'north': [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
        'west': [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
        'east': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    }
    out = []
    for name, q in faces.items():
        if name in skip:
            continue
        if inward:
            q = q[::-1]
        out += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    return out
