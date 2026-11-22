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
  props [{model,at,angles [pitch,yaw,roll],scale}]   markers [{kind,id,at,yaw}]
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


def validate(scene, materials=None):
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
        if not w.get('cost'):
            E('wall buy without a cost')
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
                for q, (u, v) in zip(p, uv):
                    wk = (key, tuple(round(c, 3) for c in q), round(u, 5), round(v, 5), tuple(round(c, 4) for c in n))
                    vi = self.weld.get(wk)
                    if vi is None:
                        vi = len(verts)
                        verts.append((tuple(round(c, 3) for c in q), u, v, self.lm, mapgen.pack_unit(n), mapgen.pack_unit(t)))
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
            above = [c for c in ceils.get(key, ()) if c > z + 1.0]
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


def try_navgen(col_tris, starts, log):
    """workstream N: navgen.generate(tris, starts=...) when the module exists -> bytes | None"""
    try:
        import navgen
    except ImportError:
        return None, 'navgen.py not present'
    try:
        r = navgen.generate(col_tris, starts=starts)
        blob = r[0] if isinstance(r, tuple) else r
        if isinstance(blob, (bytes, bytearray)):
            return bytes(blob), 'navgen.generate'
        return None, 'navgen.generate returned %s' % type(blob).__name__
    except Exception as e:                  # report, never hide
        log('navgen failed (%s): using the single layer fallback' % e)
        return None, 'navgen failed: %s' % e


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
        self.cells = {}
        self.vols = []

    # -- geometry ------------------------------------------------------------------------------------------
    def build_world(self):
        mats = material_table()
        wb = WorldBuilder(self.B.mesh, scenegen.LM, mats)
        for rec in self.scene.get('meshes', []):
            wb.add(rec)
        self.wb = wb
        return wb

    def zone_at(self, p):
        for z in self.scene.get('zones', []):
            if in_box(p, z['box']):
                return z['name']
        return None

    def floor_z(self, x, y, z):
        """nav floor (without the lift) of the column nearest to (x, y, z), else z"""
        k = (int(math.floor(x / CELL)), int(math.floor(y / CELL)))
        c = self.cells.get(k)
        if c is not None and abs(c - NAV_LIFT - z) <= 48:
            return c - NAV_LIFT
        return z

    # -- navigation ----------------------------------------------------------------------------------------
    def build_nav(self):
        col = [tuple(t) for t in self.B.mesh.col]
        starts = [tuple(s['at']) for s in self.scene.get('starts', [])]
        cells, info = nav_single_layer(col, starts)
        blob, how = try_navgen(col, starts, self.log)
        self.nav_info = dict(info, navgen=how)
        if not cells:
            raise RuntimeError('no walkable column found: the collision has no floor with 72 units of headroom reachable from a start')
        self.cells = cells
        nav_blob, _n = self.mapgen.nav_graph(cells, CELL)
        if blob:
            nav_blob = blob
            self.nav_info['used'] = 'navgen'
        else:
            self.nav_info['used'] = 'single layer fallback'
        open(os.path.join(self.out, 'navgraph.bin'), 'wb').write(nav_blob)
        self.nav_blob = nav_blob
        if info.get('dropped_upper_floors'):
            self.warnings.append('navigation: %d columns have a second floor that the single layer graph cannot hold (room over room): '
                                 'those floors have no navigation until navgen exists' % info['dropped_upper_floors'])
        if info.get('unreached_floor_samples'):
            self.warnings.append('navigation: %d floor samples (roofs and outside surfaces included) are not reachable from a player start by 18 unit steps' % info['unreached_floor_samples'])

    def cell_zone(self, k):
        x, y = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
        return self.zone_at((x, y, self.cells[k] - NAV_LIFT + 8))

    # -- entities ------------------------------------------------------------------------------------------
    def emit_scene_entities(self):
        sc, layout, mg = self.scene, self.layout, self.mapgen
        zones = sc.get('zones', [])
        ws = mg.stock_worldspawn(os.path.join(self.tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'))
        # spawn volumes: one per zone
        self.vols = []
        for z in zones:
            self.vols.append({'name': z['name'], 'zone': z['name'], 'box': [float(v) for v in z['box']]})
        starts = [dict(s) for s in sc['starts']]
        first = starts[0]['at']
        sz = self.zone_at(first)
        self.sc.start_zone = sz or zones[0]['name']
        # up to four starts: pad with the nearest free columns
        k0 = (int(math.floor(first[0] / CELL)), int(math.floor(first[1] / CELL)))
        if len(starts) < 4:
            used = {(int(math.floor(s['at'][0] / CELL)), int(math.floor(s['at'][1] / CELL))) for s in starts}
            near = sorted((k for k in self.cells if k not in used and self.cell_zone(k) == self.sc.start_zone),
                          key=lambda k: (k[0] - k0[0]) ** 2 + (k[1] - k0[1]) ** 2)
            if near:
                self.warnings.append('player starts: %d placed, padded to 4 on the nearest columns' % len(sc['starts']))
            for k in near[:4 - len(starts)]:
                starts.append({'at': ((k[0] + .5) * CELL, (k[1] + .5) * CELL, self.cells[k] - NAV_LIFT), 'yaw': starts[0].get('yaw', 0)})
        for s in starts:
            x, y, z = s['at']
            z = self.floor_z(x, y, z)
            self.ent(classname='script_struct', targetname='default_player_start', origin=self.fmt((x, y, z)), angles='0 %g 0' % s.get('yaw', 0))
            layout['starts'].append((x, y, z))
        x, y, zz = layout['starts'][0]
        for k in range(8):
            self.ent(classname='trigger_use', targetname='player_use_trigger', origin=self.fmt((x + 40 * (k - 4), y, zz + 40)),
                     model='?%d' % (4 + k % 4), dummy='triggermodeldummydefault')
        self.ent(classname='mp_global_intermission', origin=self.fmt((x, y, zz + 220)), angles='10 270 0')
        for k, v in enumerate(self.vols):
            x0, y0, z0, x1, y1, z1 = v['box']
            self.triggers.append('28000001 %g %g %g' % ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            self.ent(classname='info_volume', targetname='spawn_volume', origin=self.fmt(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)),
                     model='?IWZ%d' % k, linkname=v['name'], target=v['name'] + '_spawner')
            v['ent'] = self.ents[-1]
        for z in zones:
            b = z['box']
            layout['zones'][z['name']] = {'name': z['name'], 'box': list(b), 'boxes': [[b[0], b[1], b[3], b[4]]], 'floor': b[2], 'ceiling': b[5],
                                          'far': False, 'probe': list(z.get('probe') or (0.9, 0.9, 0.95, 0.6)), 'volumes': [z['name']]}
        self.place_scene_spawners()
        used = collections.Counter(s['volume'] for s in layout['spawners'])
        for v in self.vols:
            e = v.pop('ent')
            if not used.get(v['name']):
                e[:] = [kv for kv in e if kv[0] != '820']
            v['spawners'] = used.get(v['name'], 0)
        self.place_scene_doors()
        self.place_scene_interactions()
        for tn in ('hidden_room_portal', 'center_portal', 'fast_travel_tube_start', 'fast_travel_tube_end', 'hidden_travel_tube_start',
                   'hidden_travel_tube_end'):
            self.ent(classname='script_model', targetname=tn, model='tag_origin', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='hidden_room_spot', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='brute_hide_org', origin='0 0 -2000')
        self.place_props()
        for m in sc.get('markers', []):
            layout['markers'].append({'kind': m['kind'], 'id': m.get('id', ''), 'zone': self.zone_at(m['at']) or self.sc.start_zone,
                                      'origin': list(m['at']), 'yaw': m.get('yaw', 0)})
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
            k = (int(math.floor(x / CELL)), int(math.floor(y / CELL)))
            on_nav = k in self.cells and abs(self.cells[k] - NAV_LIFT - z) <= 48
            if not on_nav and kind == 'ground':
                self.problems.append('spawner %s at %s is on no navigation floor (a floor over another floor has none until navgen exists)' % (kind, (round(x), round(y), round(z))))
            e = dict(classname='script_struct', targetname=zone + '_spawner', noteworthy='static', angles='0 %g 0' % yaw)
            if kind == 'ground':
                e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_ground', parameters='ground_spawn_no_boards', fxid='concrete')
            elif kind == 'wall':
                e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_wall_low', parameters='no_boards')
                self.vent(zone, x, y, fz, yaw)
            else:
                e.update(origin=self.fmt((x, y, z)), animation='spawn_ceiling', parameters='ground_spawn_no_boards', fxid='ceiling')
            self.ent(**e)
            layout['spawners'].append({'zone': zone, 'volume': zone, 'origin': (x, y, z if kind == 'ceiling' else fz), 'kind': kind, 'yaw': yaw,
                                       'on_nav': on_nav, 'plate': False})
        # landing spots, idle spots and respawns: two of each per zone on its navigation columns, far from each other
        for v in self.vols:
            cand = sorted(k for k in self.cells if self.cell_zone(k) == v['zone'])
            if not cand:
                continue
            taken = [((k[0] + .5) * CELL, (k[1] + .5) * CELL) for k in []]
            chosen = []
            for n_ in range(4):
                best = max(cand, key=lambda k: min([math.hypot((k[0] - c[0]), (k[1] - c[1])) for c in chosen] or [9e9]) + 0.0001 * (-k[0]))
                chosen.append(best)
            for kk, kind in zip(chosen, ('dog', 'dog', 'resp', 'resp')):
                x, y, fz = (kk[0] + .5) * CELL, (kk[1] + .5) * CELL, self.cells[kk] - NAV_LIFT
                if kind == 'dog':
                    self.ent(classname='script_struct', targetname='dog_spawner', origin=self.fmt((x, y, fz + 8)), angles='0 0 0', radius=66)
                    self.ent(classname='script_struct', targetname='zombie_idle_spot', origin=self.fmt((x, y, fz + 8)))
                else:
                    self.ent(classname='script_struct', targetname='player_respawn_loc', origin=self.fmt((x, y, fz)), angles='0 0 0')
            layout_z = self.layout
            layout_z.setdefault('dog_spawners', {})[v['zone']] = [[(k[0] + .5) * CELL, (k[1] + .5) * CELL] for k in chosen[:2]]
            layout_z.setdefault('respawns', {})[v['zone']] = [[(k[0] + .5) * CELL, (k[1] + .5) * CELL] for k in chosen[2:]]
            layout_z.setdefault('zone_points', {})[v['zone']] = [(chosen[0][0] + .5) * CELL, (chosen[0][1] + .5) * CELL, self.cells[chosen[0]] - NAV_LIFT]
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

    def zone_adjacency(self):
        adj = set()
        for k in self.cells:
            za = self.cell_zone(k)
            for dk in ((1, 0), (0, 1)):
                k2 = (k[0] + dk[0], k[1] + dk[1])
                if k2 in self.cells and abs(self.cells[k2] - self.cells[k]) <= STEP:
                    zb = self.cell_zone(k2)
                    if za and zb and za != zb:
                        adj.add(frozenset((za, zb)))
        return adj

    def add_links(self):
        """zones with a walkable connection that is not a door are linked (spawn adjacency, activated together)"""
        door_pairs = {frozenset(o['zones']) for o in self.ops if o['kind'] == 'door'}
        explicit = {frozenset(l) for l in self.scene.get('links', [])}
        links = (self.zone_adjacency() | explicit) - door_pairs
        for pair in sorted(tuple(sorted(p)) for p in links):
            a, b = pair
            self.ops.append({'kind': 'link', 'zones': [a, b], 'door': '', 'id': 'link_%s_%s' % pair, 'price': 0, 'planes': {a: 0, b: 0},
                             'span': [0, 0], 'axis': 'x', 'sill': 0, 'top': 0, 'facing': {a: 0, b: 0}})
        self.layout['zone_adjacency'] = sorted(sorted(p) for p in self.zone_adjacency())

    def place_scene_interactions(self):
        layout = self.layout
        E = scenegen.Emitter
        zone_of = lambda p: self.zone_at(p) or self.sc.start_zone
        wheels = 0
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
            layout['interactions'][-1].update({'class': w.get('weapon_class'), 'price': int(w['cost']),
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
        if wheels:
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
            self.relocations.append('pap_machine 0 %g %g %g %g' % (org[0], org[1] + 10, org[2], yaw))
            self.ent(classname='script_struct', targetname='iwz_pap_spot', origin=self.fmt((org[0], org[1] + 20, org[2] + 14)),
                     angles='0 %g 0' % yaw, model='weapon_e_ak47_rare_wm')

    def snap(self, at):
        x, y, z = at
        return (round(x, 2), round(y, 2), round(self.floor_z(x, y, z), 2))

    def place_props(self):
        for p in self.scene.get('props', []):
            x, y, z = p['at']
            pitch, yaw, roll = p.get('angles', (0, 0, 0))
            sc_ = float(p.get('scale', 1.0))
            self.smodels.append('%s %g %g %g %g %g %g %g' % (p['model'], x, y, z, pitch, yaw, roll, sc_))
            self.layout.setdefault('decor', []).append({'zone': self.zone_at((x, y, z)) or '', 'model': p['model'], 'origin': [x, y, z],
                                                        'yaw': yaw, 'pitch': pitch, 'roll': roll, 'scale': sc_, 'clip': None, 'static': True})

    def place_lights(self):
        lines = []
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
            self.layout['lights'].append(rec)
            if L.get('runtime'):
                row = '%s %g %g %g %g %g %g %g %g' % (rec['type'], x, y, z, *rec['color'], rec['intensity'] * 1000.0, rec['radius'])
                if rec['type'] == 'spot':
                    d = rec['dir']
                    pitch = -math.degrees(math.asin(max(-1, min(1, d[2]))))
                    yaw = math.degrees(math.atan2(d[1], d[0]))
                    row += ' %g %g %g' % (pitch, yaw, rec['outer'] * 2)
                if L.get('name'):
                    row += ' name=' + L['name']
                if L.get('group'):
                    row += ' group=' + L['group']
                lines.append(row)
        if lines:
            open(os.path.join(self.out, 'lights.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')

    # -- run -----------------------------------------------------------------------------------------------
    def run(self):
        sc = self.scene
        os.makedirs(self.out, exist_ok=True)
        mats, known_ok = known_materials()
        issues = validate(sc, mats if known_ok else None)
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
            b = z['box']
            r, g, bl, up = z.get('probe') or (0.9, 0.9, 0.95, 0.6)
            row = 'room %d %d %d %d %d %d %.3f %.3f %.3f %.2f' % (b[0] - 48, b[1] - 48, b[2] - 48, b[3] + 48, b[4] + 48, b[5] + 48, r, g, bl, up)
            amb.append(row); probes.append(row)
        open(os.path.join(self.out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(amb) + '\n')
        open(os.path.join(self.out, 'probes.txt'), 'w', newline='\n').write('\n'.join(probes) + '\n')
        # plan.json: regions = zones, cells with their zone, adjacency
        owner = {k: (self.cell_zone(k) or '_outside') for k in self.cells}
        if any(v == '_outside' for v in owner.values()):
            n = sum(1 for v in owner.values() if v == '_outside')
            self.problems.append('%d navigation columns are in no zone box: zombies there are in no spawn volume' % n)
            self.regions.append({'name': '_outside', 'zone': '_outside', 'rect': [0, 0, 0, 0]})
        adj = set()
        for k in self.cells:
            for dk in ((1, 0), (0, 1)):
                k2 = (k[0] + dk[0], k[1] + dk[1])
                if k2 in self.cells and abs(self.cells[k2] - self.cells[k]) <= STEP and owner[k] != owner[k2]:
                    adj.add(frozenset((owner[k], owner[k2])))
        plan = {'regions': self.regions, 'adj': [sorted(a) for a in adj], 'cells': [[i, j, z, owner[(i, j)]] for (i, j), z in sorted(self.cells.items())],
                'cell_corners': [], 'blockers': self.B.blockers, 'col_tris': len(col), 'bounds': wbnd, 'col_walls': []}
        json.dump(plan, open(os.path.join(self.out, 'plan.json'), 'w'))
        self.layout['regions'] = len(self.regions)
        self.layout['volumes'] = self.vols
        s0 = self.sc.start_zone
        self.layout['navconn_routes'] = [[s0, z['name']] for z in sc['zones'] if z['name'] != s0 and z['name'] in set(owner.values())]
        self.layout['far_zones'] = []
        self.layout['modules'] = self.layout.get('modules', [])
        self.layout['stairs'] = []
        self.layout['blender'] = {'schema': 'iwz.blend/1', 'meshes': len(sc.get('meshes', [])), 'navigation': self.nav_info}
        for k, v in (sc.get('extra_layout') or {}).items():
            self.layout.setdefault(k, v)
        json.dump(self.layout, open(os.path.join(self.out, 'layout.json'), 'w'), indent=1, default=list)
        json.dump({'custom': {}, 'used': sorted({m['material'] for m in sc.get('meshes', []) if m.get('material')})},
                  open(os.path.join(self.out, 'custom_materials.json'), 'w'), indent=1)
        report = {'schema': 'iw7.blend2iwz/1', 'map': self.sc.map, 'zones': len(sc['zones']), 'volumes': len(self.vols),
                  'doors': len(sc.get('doors', [])), 'spawners': len(self.layout['spawners']),
                  'world': {'vertices': nv, 'indices': ni, 'surfaces': ns, 'render_triangles': wb.render_tris, 'materials': len(self.B.mesh.materials)},
                  'collision': {'triangles': len(col), 'degenerate_dropped_before': wb.degenerate, 'havok': info, 'bytes': len(blob)},
                  'navigation': self.nav_info, 'entities': self.entity_census(), 'problems': self.problems, 'warnings': self.warnings,
                  'lights': len(self.layout['lights'])}
        json.dump(report, open(os.path.join(self.out, 'scene_report.json'), 'w'), indent=1, default=list)
        self.log('blend2iwz %s: %d zones, %d doors, %d spawners, %d render triangles in %d surfaces, %d collision triangles, %d nav cells, '
                 '%d problems, %d warnings' % (self.sc.map, len(sc['zones']), len(sc.get('doors', [])), len(self.layout['spawners']), wb.render_tris,
                                                ns, len(col), len(self.cells), len(self.problems), len(self.warnings)))
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
