"""Section export, pure part (no bpy): the scene of one authored SECTION of an existing map in, a section folder out.

A section replaces the static shell and dressing of one zone of a generated map (`replace`), or adds a zone (`new`); the folder
it is exported to (`iwz.section/1`, docs/SECTIONS.md) is merged into the base emit by `tools-source/iwzmap/sections/section_merge.py`.

    <section>/section.json      name, replace_zones, new_zones, doors, links, spawners, interactions, lights, props, decals, signs, fx, views
    <section>/world.bin         render triangles (mapgen.write_world)
    <section>/collision.json    {"tris": [[[x,y,z] x3], ...], "tags": [int | null per triangle]}
    <section>/kit_models.json   model -> the stock zone dump it comes from
    <section>/section_report.json   counts, budgets, the validation (errors refuse the export), what was sampled
    <section>/custom_materials.json {"custom": {}, "used": [materials]}

Everything here is plain Python (numpy for the sampling checks), inches, IW7 axes. `blend2iwz.py export-section` fills the scene dict
inside Blender; the unit tests fill it by hand.

Scene dict of a section (`collect_section`): the keys of blend_core's scene (meshes, spawners, perks, wall_buys, pap, wheels, power,
lights, props, doors, zones) plus
  section {name, mode 'replace'|'new', zone <base zone id for replace>, base <emit folder>}
  decals [{zone, mat, axis, fixed, facing, s, zc, w, h}]  signs [{zone, image, center, axis, facing, size, off, hanging}]
  fx [{fx, origin, zone, repeat}]  views {zone: [[x, y, z, yaw, pitch]]}  links [[a, b]]
  props: {model, at, angles [pitch, yaw, roll], scale, static, clip (bool)}
  zones (new mode): {name, box, probe, floor, ceiling}
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IWZ = os.path.dirname(HERE)
for _p in (HERE, IWZ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402

import blend_core as BC  # noqa: E402
import mapgen  # noqa: E402
import scenegen  # noqa: E402

SCHEMA = 'iwz.section/1'
CELL = 32
DOOR_COSTS = BC.DOOR_COSTS
NAV_TOL = 2.0                  # inches: the floor under a base navigation cell must equal the cell height within this
GRID = 16.0                    # walkable floor edges on the 16 unit grid
CLEAR_DEPTH = 64.0             # clearance box in front of an interaction
CLEAR_HALF = 40.0              # half width of that box
SPAWN_CLEAR = 48.0
MACHINE_HALF_DEPTH = 24.0
HEAD = 72.0
STEP_T = 2.0                   # sampling pitch of the closure check along a wall (inches)
STEP_Z = 4.0                   # and in height
INTERACTION_FLOOR_OFFSET = {'wall_buy': 64.0, 'generator': 50.0}
CLEARED_KINDS = ('perk_machine_', 'wall_buy', 'weapon_upgrade', 'magic_wheel', 'generator')
EXCLUDED_COLLECTIONS = ('IWZ_Base', 'IWZ_Base_Replaced', 'IWZ_Gameplay')     # context only, never exported


# ------------------------------------------------------------------------------------------------ the base emit
class Base:
    """The base emit of a generated map as the section tools need it (layout.json, plan.json), read lazily"""

    def __init__(self, emit):
        self.emit = emit
        self.layout = json.load(open(os.path.join(emit, 'layout.json'), encoding='utf-8'))
        p = os.path.join(emit, 'plan.json')
        self.plan = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {'regions': [], 'cells': []}
        self.region_zone = {r['name']: r['zone'] for r in self.plan.get('regions', [])}
        self.zones = {k: v for k, v in self.layout.get('zones', {}).items()}

    def zone_box(self, zone):
        if zone not in self.zones:
            raise KeyError('zone %r is not in the base emit (zones: %s)' % (zone, ', '.join(sorted(self.zones))))
        return [float(v) for v in self.zones[zone]['box']]

    def zone_at(self, p):
        for k, z in self.zones.items():
            if BC.in_box(p, z['box']):
                return k
        return None

    def cells(self, zone=None):
        """{(i, j): z} of the navigation cells of a zone (all zones when None); a column with several floors keeps the lowest"""
        out = {}
        for i, j, z, region in self.plan.get('cells', []):
            zn = self.region_zone.get(region)
            if zone is None or zn == zone:
                out[(int(i), int(j))] = min(float(z), out.get((int(i), int(j)), 1e9))
        return out

    def openings(self, zone):
        """boxes [x0, y0, z0, x1, y1, z1] of the doors, arches and open walls of a zone, each with its name and kind: the hole each must leave"""
        out = []
        for o in self.layout.get('openings', []):
            zs = {self.region_zone.get(r) for r in o.get('walls', {})}
            if zone not in zs:
                continue
            ps = list(o['walls'].values())
            lo, hi = min(ps), max(ps)
            if hi - lo < 1:
                lo, hi = lo - 8, hi + 8
            a, b = float(o['a']), float(o['b'])
            if o['axis'] == 'x':      # the wall runs along x: the plane is y
                box = [a, lo, float(o['z0']), b, hi, float(o['z1'])]
            else:
                box = [lo, a, float(o['z0']), hi, b, float(o['z1'])]
            out.append({'name': o['name'], 'kind': o.get('kind', 'door'), 'box': box})
        return out

    def interactions(self, zone):
        out = []
        zb = self.zone_box(zone)
        for it in self.layout.get('interactions', []):
            k = it.get('kind', '')
            if not (k.startswith('perk_machine_') or it.get('groupname') == 'wall_buy' or k in ('weapon_upgrade', 'magic_wheel', 'generator')):
                continue
            if it.get('zone') == zone or BC.in_box(it['origin'], zb):
                out.append(it)
        return out

    def spawners(self, zone):
        return [s for s in self.layout.get('spawners', []) if s.get('zone') == zone]

    def starts(self, zone):
        zb = self.zone_box(zone)
        return [s for s in self.layout.get('starts', []) if BC.in_box(s, zb)]


# ------------------------------------------------------------------------------------------------ triangles
class Tris:
    """collision triangles as numpy arrays with their bounds and normals"""

    def __init__(self, tris):
        self.T = np.array([[list(p) for p in t] for t in tris], dtype=np.float64).reshape(-1, 3, 3)
        T = self.T
        self.mn = T.min(axis=1) if len(T) else np.zeros((0, 3))
        self.mx = T.max(axis=1) if len(T) else np.zeros((0, 3))
        if len(T):
            n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            ln = np.linalg.norm(n, axis=1)
            self.area2 = ln
            self.N = n / np.maximum(ln, 1e-12)[:, None]
        else:
            self.N = np.zeros((0, 3))
            self.area2 = np.zeros(0)

    def __len__(self):
        return len(self.T)

    def in_bbox(self, box, eps=0.0):
        """indices of the triangles whose bounds overlap the box (6 floats)"""
        if not len(self.T):
            return np.zeros(0, np.int64)
        m = np.all(self.mx >= np.array(box[:3]) - eps, axis=1) & np.all(self.mn <= np.array(box[3:]) + eps, axis=1)
        return np.nonzero(m)[0]


def tri_box_overlap(tri, box):
    """separating axis test (Akenine-Moeller): does the triangle intersect the axis aligned box [x0, y0, z0, x1, y1, z1]?"""
    c = [(box[i] + box[3 + i]) / 2 for i in range(3)]
    h = [(box[3 + i] - box[i]) / 2 for i in range(3)]
    v = [[tri[k][i] - c[i] for i in range(3)] for k in range(3)]
    for i in range(3):
        if min(v[k][i] for k in range(3)) > h[i] or max(v[k][i] for k in range(3)) < -h[i]:
            return False
    e = [[v[(k + 1) % 3][i] - v[k][i] for i in range(3)] for k in range(3)]
    n = [e[0][1] * e[1][2] - e[0][2] * e[1][1], e[0][2] * e[1][0] - e[0][0] * e[1][2], e[0][0] * e[1][1] - e[0][1] * e[1][0]]
    r = sum(h[i] * abs(n[i]) for i in range(3))
    d = sum(n[i] * v[0][i] for i in range(3))
    if abs(d) > r:
        return False
    for k in range(3):
        for a in range(3):
            ax = [0, 0, 0]
            ax[a] = 1
            ex = e[k]
            axis = [ax[1] * ex[2] - ax[2] * ex[1], ax[2] * ex[0] - ax[0] * ex[2], ax[0] * ex[1] - ax[1] * ex[0]]
            if abs(axis[0]) + abs(axis[1]) + abs(axis[2]) < 1e-12:
                continue
            p = [sum(axis[i] * v[q][i] for i in range(3)) for q in range(3)]
            rr = sum(h[i] * abs(axis[i]) for i in range(3))
            if min(p) > rr or max(p) < -rr:
                return False
    return True


def solid_in_box(tris, box):
    """indices of the collision triangles that really cut the box"""
    return [int(i) for i in tris.in_bbox(box) if tri_box_overlap(tris.T[i], box)]


# ------------------------------------------------------------------------------------------------ wall coverage
def wall_coverage(tris, axis, c0, c1, t0, t1, z0, z1, step_t=STEP_T, step_z=STEP_Z, openings=()):
    """Rays along `axis` (0 = x, 1 = y) through the slab c0..c1, one per sample of the (t, z) grid (t0..t1 along the other horizontal axis
    every step_t, z0..z1 every step_z). A sample is covered when a collision triangle crosses its ray inside the slab, or it lies in an
    opening box. -> (uncovered samples as [(x, y, z)], number of samples)"""
    ta = 1 - axis
    ts = np.arange(t0 + step_t / 2, t1, step_t)
    zs = np.arange(z0 + step_z / 2, z1, step_z)
    if not len(ts) or not len(zs):
        return [], 0
    TT, ZZ = np.meshgrid(ts, zs)
    tf, zf = TT.ravel(), ZZ.ravel()
    covered = np.zeros(len(tf), bool)
    box = [0.0] * 6
    box[axis], box[3 + axis] = c0, c1
    box[ta], box[3 + ta] = t0, t1
    box[2], box[5] = z0, z1
    for i in tris.in_bbox(box, 0.5):
        n = tris.N[i]
        if abs(n[axis]) < 1e-9:
            continue
        v = tris.T[i]
        a, b, c = (v[0][[ta, 2]], v[1][[ta, 2]], v[2][[ta, 2]])
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (tf - c[0]) + (c[0] - b[0]) * (zf - c[1])) / den
        l2 = ((c[1] - a[1]) * (tf - c[0]) + (a[0] - c[0]) * (zf - c[1])) / den
        l3 = 1 - l1 - l2
        e = -1e-7
        ins = (l1 >= e) & (l2 >= e) & (l3 >= e)
        if not ins.any():
            continue
        depth = v[0][axis] - (n[ta] * (tf - v[0][ta]) + n[2] * (zf - v[0][2])) / n[axis]
        covered |= ins & (depth >= c0 - 0.5) & (depth <= c1 + 0.5)
    for ob in openings:
        if ob[axis] - 1 <= c1 and ob[3 + axis] + 1 >= c0:
            covered |= (tf >= ob[ta] - 1) & (tf <= ob[3 + ta] + 1) & (zf >= ob[2] - 1) & (zf <= ob[5] + 1)
    miss = np.nonzero(~covered)[0]
    out = []
    for k in miss:
        p = [0.0, 0.0, float(zf[k])]
        p[ta] = float(tf[k])
        p[axis] = (c0 + c1) / 2
        out.append(tuple(p))
    return out, len(tf)


def _cluster(points, link=6.0, cap=6):
    """group missing samples into gaps: -> [(bbox mins, bbox maxs, count)] (largest first)"""
    pts = sorted(points)
    groups = []
    for p in pts:
        for g in groups:
            if all(g['mn'][i] - link <= p[i] <= g['mx'][i] + link for i in range(3)):
                g['mn'] = [min(g['mn'][i], p[i]) for i in range(3)]
                g['mx'] = [max(g['mx'][i], p[i]) for i in range(3)]
                g['n'] += 1
                break
        else:
            groups.append({'mn': list(p), 'mx': list(p), 'n': 1})
    groups.sort(key=lambda g: -g['n'])
    return [(g['mn'], g['mx'], g['n']) for g in groups[:cap]]


def check_openings(tris, openings):
    """every base opening (and every door of the section) must stay free: no collision inside its box"""
    out = []
    for o in openings:
        b = o['box']
        box = [b[0] + 1, b[1] + 1, b[2] + 2, b[3] - 1, b[4] - 1, b[5] - 1]
        if box[3] <= box[0] or box[4] <= box[1]:                       # a thin plane: test its middle
            box = [min(b[0] + 1, (b[0] + b[3]) / 2 - 0.5), min(b[1] + 1, (b[1] + b[4]) / 2 - 0.5), b[2] + 2,
                   max(b[3] - 1, (b[0] + b[3]) / 2 + 0.5), max(b[4] - 1, (b[1] + b[4]) / 2 + 0.5), b[5] - 1]
        hit = solid_in_box(tris, box)
        if hit:
            out.append(('WARN' if o.get('kind') == 'open' else 'ERROR', 'opening %s (%s) is blocked: %d collision triangles inside its box %s, which must stay free (the door or arch goes there)'
                        % (o['name'], o.get('kind', 'door'), len(hit), [round(v) for v in b])))
    return out


def footprint_walls(regions, zone_cells, zone, piece=8.0, chunk=32.0, floor_default=0.0):
    """Walls the floor plan of a zone asks for. `regions` are the plan.json regions ({name, zone, rect}); a piece of an edge of a region of
    the zone needs a wall when the point 1 unit outside it lies in no region (a region of another zone, a portal region of a door or arch
    and a neighbouring region of the same zone all mean open floor or an opening). -> [{axis, plane, sign, lo, hi, z}] in chunks of 32"""
    rects = [r['rect'] for r in regions]
    inside = lambda x, y: any(r[0] - 0.01 <= x <= r[2] + 0.01 and r[1] - 0.01 <= y <= r[3] + 0.01 for r in rects)
    def floor_z(x, y):
        i, j = int(math.floor(x / CELL)), int(math.floor(y / CELL))
        best = None
        for d in (0, 1, 2, 3):
            for di in range(-d, d + 1):
                for dj in range(-d, d + 1):
                    if max(abs(di), abs(dj)) == d and (i + di, j + dj) in zone_cells:
                        return zone_cells[(i + di, j + dj)]
        return floor_default
    segs = []
    for reg in regions:
        if reg['zone'] != zone or reg['name'].startswith('portal:'):
            continue
        x0, y0, x1, y1 = reg['rect']
        for axis, plane, sign, lo, hi in ((0, x0, -1, y0, y1), (0, x1, 1, y0, y1), (1, y0, -1, x0, x1), (1, y1, 1, x0, x1)):
            n = max(1, int(round((hi - lo) / piece)))
            need = []
            for k in range(n):
                a = lo + (hi - lo) * k / n
                b = lo + (hi - lo) * (k + 1) / n
                m = (a + b) / 2
                px, py = (plane + sign * 1.0, m) if axis == 0 else (m, plane + sign * 1.0)
                need.append(not inside(px, py))
            k = 0
            while k < n:
                if not need[k]:
                    k += 1
                    continue
                e = k
                while e < n and need[e]:
                    e += 1
                a = lo + (hi - lo) * k / n
                b = lo + (hi - lo) * e / n
                cnt = max(1, int(math.ceil((b - a) / chunk)))
                for q in range(cnt):
                    ca, cb = a + (b - a) * q / cnt, a + (b - a) * (q + 1) / cnt
                    m = (ca + cb) / 2
                    inx, iny = (plane - sign * 8.0, m) if axis == 0 else (m, plane - sign * 8.0)
                    segs.append({'axis': axis, 'plane': plane, 'sign': sign, 'lo': ca, 'hi': cb, 'z': floor_z(inx, iny), 'region': reg['name']})
                k = e
    return segs


def check_closure_plan(tris, segs, openings, reach=24.0, head=HEAD):
    """A replaced zone keeps the base floor plan, so its shell must stand along the outline of the plan: for each wall chunk, rays every
    STEP_T and STEP_Z through the slab that starts 2 inside the plan edge and runs `reach` outward; a sample no collision triangle
    crosses and no opening box covers is a gap"""
    gaps = []
    samples = 0
    for sg in segs:
        pl, sgn = sg['plane'], sg['sign']
        c0, c1 = (pl - 2.0, pl + reach) if sgn > 0 else (pl - reach, pl + 2.0)
        miss, ns = wall_coverage(tris, sg['axis'], c0, c1, sg['lo'], sg['hi'], sg['z'] + 2, sg['z'] + head, openings=[o['box'] for o in openings])
        samples += ns
        gaps += miss
    rows = []
    for mn, mx, n in _cluster(gaps, link=CELL):
        rows.append(('ERROR', 'gap in the shell: %d unprotected samples (every %g x %g in) around x %g..%g, y %g..%g, z %g..%g: the zone must be closed along the outline '
                     'of its floor plan (no collision wall and no door or arch opening covers it)' % (n, STEP_T, STEP_Z, mn[0], mx[0], mn[1], mx[1], mn[2], mx[2])))
    return rows, {'wall_chunks': len(segs), 'samples': samples, 'gap_samples': len(gaps)}


def check_closure_faces(tris, box, openings, floor, ceiling, window=32.0):
    """A new zone: its four side faces must be walled (collision within `window` of the face plane) from the floor to the ceiling,
    except inside the door openings"""
    pts = []
    samples = 0
    x0, y0, _, x1, y1, _ = box
    for axis, plane, lo, hi in ((0, x0, y0, y1), (0, x1, y0, y1), (1, y0, x0, x1), (1, y1, x0, x1)):
        miss, ns = wall_coverage(tris, axis, plane - window, plane + window, lo, hi, floor + 2, ceiling - 2, openings=openings)
        pts += miss
        samples += ns
    rows = []
    for mn, mx, n in _cluster(pts, link=CELL):
        rows.append(('ERROR', 'gap in the shell: %d unprotected samples (every %g x %g in) around x %g..%g, y %g..%g, z %g..%g: the new zone must be closed '
                     '(its walls have a hole that is no door)' % (n, STEP_T, STEP_Z, mn[0], mx[0], mn[1], mx[1], mn[2], mx[2])))
    return rows, {'samples': samples, 'gap_samples': len(pts)}


# ------------------------------------------------------------------------------------------------ gameplay clearances
def clearance_box(it, floor_z=None):
    """box [x0, y0, z0, x1, y1, z1] 64 deep in front of an interaction (yaw = the way it faces), 80 wide, from the floor to head height"""
    o = it['origin']
    yaw = math.radians(float(it.get('yaw', 0)))
    f = (math.cos(yaw), math.sin(yaw))
    r = (-f[1], f[0])
    fz = floor_z if floor_z is not None else o[2] - interaction_floor_offset(it)
    d0 = 0.0 if it.get('groupname') == 'wall_buy' else MACHINE_HALF_DEPTH      # a machine body is about 40 deep around its origin
    pts = [(o[0] + f[0] * d + r[0] * s, o[1] + f[1] * d + r[1] * s) for d in (d0, d0 + CLEAR_DEPTH) for s in (-CLEAR_HALF, CLEAR_HALF)]
    return [min(p[0] for p in pts), min(p[1] for p in pts), fz + 4.0, max(p[0] for p in pts), max(p[1] for p in pts), fz + HEAD]


def interaction_floor_offset(it):
    if it.get('groupname') == 'wall_buy':
        return INTERACTION_FLOOR_OFFSET['wall_buy']
    return INTERACTION_FLOOR_OFFSET.get(it.get('kind', ''), 0.0)


def spawner_box(s):
    o = s['origin']
    return [o[0] - SPAWN_CLEAR, o[1] - SPAWN_CLEAR, o[2] + 2.0, o[0] + SPAWN_CLEAR, o[1] + SPAWN_CLEAR, o[2] + HEAD]


def check_clearances(tris, interactions, spawners):
    out = []
    for it in interactions:
        hit = solid_in_box(tris, clearance_box(it))
        if hit:
            out.append(('ERROR', 'solid collision (%d triangles) in the clearance box in front of %s at %s: players must be able to stand there' %
                        (len(hit), it.get('kind', '?'), [round(float(v)) for v in it['origin']])))
    for s in spawners:
        hit = solid_in_box(tris, spawner_box(s))
        if hit:
            out.append(('ERROR', 'solid collision (%d triangles) within %g of the %s spawner at %s' % (len(hit), SPAWN_CLEAR, s.get('kind', 'ground'),
                                                                                              [round(float(v)) for v in s['origin']])))
    return out


# ------------------------------------------------------------------------------------------------ floors
def floor_at(tris, pts, zref, reach=40.0, min_nz=0.5):
    """for every point (N, 2) the height of the upward collision surface nearest to zref (N,) within `reach`; nan where there is none"""
    pts = np.asarray(pts, float).reshape(-1, 2)
    zref = np.asarray(zref, float).reshape(-1)
    best = np.full(len(pts), np.nan)
    bd = np.full(len(pts), np.inf)
    if not len(pts) or not len(tris):
        return best
    for i in np.nonzero(tris.N[:, 2] >= min_nz)[0]:
        v = tris.T[i]
        mn, mx = tris.mn[i], tris.mx[i]
        m = (pts[:, 0] >= mn[0] - 1e-6) & (pts[:, 0] <= mx[0] + 1e-6) & (pts[:, 1] >= mn[1] - 1e-6) & (pts[:, 1] <= mx[1] + 1e-6)
        if not m.any():
            continue
        idx = np.nonzero(m)[0]
        a, b, c = v[0][:2], v[1][:2], v[2][:2]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        px, py = pts[idx, 0], pts[idx, 1]
        l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
        l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
        ok = (l1 >= -1e-7) & (l2 >= -1e-7) & (1 - l1 - l2 >= -1e-7)
        if not ok.any():
            continue
        zz = l1 * v[0][2] + l2 * v[1][2] + (1 - l1 - l2) * v[2][2]
        d = np.abs(zz - zref[idx])
        upd = ok & (d <= reach) & (d < bd[idx])
        sel = idx[upd]
        bd[sel] = d[upd]
        best[sel] = zz[upd]
    return best


def check_nav_heights(tris, cells, tol=NAV_TOL):
    """the floor under every base navigation cell equals the cell height within `tol`, unless solid collision blocks the cell (the
    nav then loses that cell, which is what new solid collision does); -> (errors, stats)"""
    if not cells:
        return [], {'cells': 0}
    keys = sorted(cells)
    pts = [((i + 0.5) * CELL, (j + 0.5) * CELL) for i, j in keys]
    zs = [cells[k] for k in keys]
    fl = floor_at(tris, pts, zs, reach=40.0)
    bad, blocked, missing = [], 0, 0
    for k, p, z, f in zip(keys, pts, zs, fl):
        if not np.isnan(f) and abs(f - z) <= tol + 1e-6:
            continue
        col = [p[0] - 12, p[1] - 12, z + 18.0, p[0] + 12, p[1] + 12, z + HEAD]
        if solid_in_box(tris, col):
            blocked += 1
            continue
        if np.isnan(f):
            missing += 1
        bad.append((k, z, None if np.isnan(f) else round(float(f), 2)))
    rows = []
    if bad:
        sample = ', '.join('(%d,%d) cell z %g floor %s' % (k[0], k[1], z, 'none' if f is None else f) for k, z, f in bad[:8])
        rows.append(('ERROR', '%d base navigation cells have a floor that differs from the cell height by more than %g (or no floor), %d with no floor at all; first: %s'
                     % (len(bad), tol, missing, sample)))
    return rows, {'cells': len(keys), 'blocked_by_solid': blocked, 'bad': len(bad), 'no_floor': missing}


def floor_edges_off_grid(tris, grid=GRID, tol=0.5, min_nz=0.7):
    """boundary edges of the walkable (upward) collision triangles that are axis aligned but off the grid, or slanted; -> (off_grid, slanted)"""
    def key(p): return tuple(round(c * 8) for c in p)
    up = [i for i in range(len(tris)) if tris.N[i][2] >= min_nz]
    cnt = collections.Counter()
    rec = {}
    for i in up:
        v = tris.T[i]
        for a in range(3):
            p, q = v[a], v[(a + 1) % 3]
            k = tuple(sorted((key(p), key(q))))
            cnt[k] += 1
            rec[k] = (p, q)
    off, slanted = [], []
    for k, n in cnt.items():
        if n != 1:
            continue
        p, q = rec[k]
        dx, dy = abs(p[0] - q[0]), abs(p[1] - q[1])
        if dx < 1e-6 and dy < 1e-6:
            continue
        if dy < 1e-6:
            c = p[1]
        elif dx < 1e-6:
            c = p[0]
        else:
            slanted.append((tuple(round(float(v), 1) for v in p), tuple(round(float(v), 1) for v in q)))
            continue
        r = c % grid
        if min(r, grid - r) > tol:
            off.append((tuple(round(float(v), 1) for v in p), tuple(round(float(v), 1) for v in q)))
    return off, slanted


# ------------------------------------------------------------------------------------------------ models
_INDEX = {}


def model_index():
    """the stock dump index of the preview (the catalogue of models) or None when the dumps are not installed"""
    if 'i' not in _INDEX:
        try:
            sys.path.insert(0, os.path.join(IWZ, 'preview'))
            import iwz_assets
            _INDEX['i'] = iwz_assets.DumpIndex()
            _INDEX['a'] = iwz_assets
        except Exception:
            _INDEX['i'] = None
    return _INDEX['i']


def model_source_zone(path):
    """the stock zone dump a model file comes from: .../dump/<zone>/xmodel/<name>.xmb -> <zone>"""
    parts = path.replace('\\', '/').split('/')
    if 'xmodel' in parts:
        k = len(parts) - 1 - parts[::-1].index('xmodel')
        return parts[k - 1]
    return '?'


def model_bounds(name):
    """(mins, maxs) of a stock model in model space (inches), or None"""
    idx = model_index()
    if idx is None:
        return None
    p = idx.get('xmodel', name)
    if not p:
        return None
    try:
        import ztdump
    except ImportError:
        sys.path.insert(0, os.path.join(IWZ, 'catalog'))
        import ztdump
    try:
        m = ztdump.read_xmodel(p)
        return list(m['bounds']['mins']), list(m['bounds']['maxs'])
    except Exception:
        return None


def clip_box_of(prop, bounds):
    """world axis aligned box [x0, y0, z0, x1, y1, z1] of a prop's model bounds (yaw, scale)"""
    mn, mx = bounds
    s = float(prop.get('scale', 1.0))
    yaw = math.radians(float(prop['angles'][1]))
    c, sn = math.cos(yaw), math.sin(yaw)
    xs, ys = [], []
    for x in (mn[0], mx[0]):
        for y in (mn[1], mx[1]):
            xs.append(prop['at'][0] + (c * x - sn * y) * s)
            ys.append(prop['at'][1] + (sn * x + c * y) * s)
    return [round(min(xs), 2), round(min(ys), 2), round(prop['at'][2] + mn[2] * s, 2), round(max(xs), 2), round(max(ys), 2), round(prop['at'][2] + mx[2] * s, 2)]


# ------------------------------------------------------------------------------------------------ geometry of a box (collision)
def box_tris(b):
    return BC.box_tris(tuple(b[:3]), tuple(b[3:]))


# ------------------------------------------------------------------------------------------------ decals and signs
def resolve_material(name):
    """a decal or sign material as written in Blender (a w/... path, a Station Zero material key such as leak_stain, or a custom image
    key such as sign_generator) -> (path written to world.bin, key written to the layout rows)"""
    import sz2_materials as MT
    if name in MT.MATERIALS:
        return MT.MATERIALS[name]['path'], name
    for k, v in MT.MATERIALS.items():
        if v['path'] == name:
            return name, k
    return name, name


def plane_row(kind, bb, normal, key, image=None, off=None, hanging=False):
    """the layout.json row (station_zero2 `decal_wall` / `sign`) of a plane mesh standing on a wall, or None for a floor or ceiling plane.
    bb: world box [x0, y0, z0, x1, y1, z1] of the plane, normal: its unit normal. A decal plane sits 0.4 in front of the wall, a sign 3.6"""
    nx, ny, nz = normal
    if abs(nz) >= max(abs(nx), abs(ny)):
        return None
    if off is None:
        off = 3.6 if kind == 'sign' else 0.4
    zc = round((bb[2] + bb[5]) / 2, 2)
    h = round(bb[5] - bb[2], 2)
    if abs(ny) >= abs(nx):
        facing = 1 if ny > 0 else -1
        axis, s, w = 'x', (bb[0] + bb[3]) / 2, bb[3] - bb[0]
        fixed = (bb[1] + bb[4]) / 2 - facing * off
        center = [round(s, 2), round(fixed, 2), zc]
    else:
        facing = 1 if nx > 0 else -1
        axis, s, w = 'y', (bb[1] + bb[4]) / 2, bb[4] - bb[1]
        fixed = (bb[0] + bb[3]) / 2 - facing * off
        center = [round(fixed, 2), round(s, 2), zc]
    w = round(w, 2)
    fixed, s = round(fixed, 2), round(s, 2)
    if kind == 'decal':
        return {'zone': None, 'mat': key, 'axis': axis, 'fixed': fixed, 'facing': facing, 's': s, 'zc': zc, 'w': w, 'h': h}
    return {'zone': None, 'image': image or key, 'center': center, 'axis': axis, 'facing': facing, 'size': [w, h], 'off': off, 'hanging': bool(hanging)}


# ------------------------------------------------------------------------------------------------ the section
def door_row(d):
    """door row of section.json from a door box (thin along x -> axis 0, plane x) """
    b = d['box']
    ex, ey = b[3] - b[0], b[4] - b[1]
    if ex <= ey:
        axis, plane, lo, hi = 0, (b[0] + b[3]) / 2, b[1], b[4]
    else:
        axis, plane, lo, hi = 1, (b[1] + b[4]) / 2, b[0], b[3]
    return {'name': d['name'], 'zones': list(d.get('zones') or []), 'axis': axis, 'plane': round(plane, 2), 'lo': round(lo, 2), 'hi': round(hi, 2),
            'z0': round(b[2], 2), 'z1': round(b[5], 2), 'cost': int(d['cost'])}


def door_box(row):
    """collision-free hole of a door row: the wall plane +- 8"""
    p = row['plane']
    if row['axis'] == 0:
        return [p - 8, row['lo'], row['z0'], p + 8, row['hi'], row['z1']]
    return [row['lo'], p - 8, row['z0'], row['hi'], p + 8, row['z1']]


def interaction_rows(sc, zone_of):
    """layout.json interaction rows of the scene's entity lists"""
    E = scenegen.Emitter
    rows = []
    for p in sc.get('perks', []):
        r = {'kind': 'perk_machine_' + p['perk'], 'origin': [round(v, 2) for v in p['at']], 'yaw': float(p.get('yaw', 0)), 'zone': zone_of(p['at'])}
        if not p.get('powered'):
            r['parameters'] = 'requires_power'
        rows.append(r)
    for w in sc.get('wall_buys', []):
        org = [round(w['at'][0], 2), round(w['at'][1], 2), round(w['at'][2] + 64, 2)]
        if w.get('weapon'):
            weapon, wm = w['weapon'], w.get('model') or None
        else:
            weapon, wm = E.WALL_WEAPON[w['weapon_class']]
        r = {'kind': weapon, 'origin': org, 'yaw': float(w.get('yaw', 0)), 'zone': zone_of(org), 'groupname': 'wall_buy', 'radius': 256,
             'class': w.get('weapon_class'), 'price': int(w.get('cost') or 0) or None, 'stand_in': w.get('weapon_class') in E.STAND_IN}
        if wm:
            r['model'] = wm
        rows.append(r)
    for w in sc.get('wheels', []):
        rows.append({'kind': 'magic_wheel', 'origin': [round(v, 2) for v in w['at']], 'yaw': float(w.get('yaw', 0)), 'zone': zone_of(w['at'])})
    for p in sc.get('power', []):
        org = [round(p['at'][0], 2), round(p['at'][1], 2), round(p['at'][2] + 50, 2)]
        rows.append({'kind': 'generator', 'origin': org, 'yaw': float(p.get('yaw', 0)), 'zone': zone_of(org), 'parameters': 'power_all', 'target': 'iwz_power_switch'})
    for p in sc.get('pap', []):
        rows.append({'kind': 'weapon_upgrade', 'origin': [round(v, 2) for v in p['at']], 'yaw': float(p.get('yaw', 0)), 'zone': zone_of(p['at']),
                     'parameters': 'requires_power', 'target': 'iwz_pap_spot'})
    return rows


def light_rows(sc, zone_of):
    out = []
    for L in sc.get('lights', []):
        x, y, z = L['at']
        r = {'zone': zone_of(L['at']), 'origin': [round(x, 2), round(y, 2), round(z, 2)], 'type': L.get('type', 'omni'),
             'color': [round(float(c), 4) for c in L.get('color', (1, 0.97, 0.78))], 'radius': float(L.get('radius', 420)),
             'intensity': float(L.get('intensity', 2.0)), 'fixture': L.get('fixture') or '', 'group': L.get('group') or 'power'}
        if r['type'] == 'spot':
            r.update(dir=[round(float(c), 4) for c in L.get('dir', (0, 0, -1))], inner=float(L.get('inner', 14)), outer=float(L.get('outer', 32)))
        if L.get('name'):
            r['name'] = L['name']
        out.append(r)
    return out


def validate_section(sc, base=None):
    """Static checks of a section scene that need no triangles: -> [(severity, message)]"""
    out = []
    E = lambda m: out.append(('ERROR', m))
    W = lambda m: out.append(('WARN', m))
    s = sc.get('section') or {}
    mode = s.get('mode')
    if mode not in ('replace', 'new'):
        E('section mode %r (replace or new)' % mode)
        return out
    if not s.get('name'):
        E('the section has no name')
    if base is None:
        E('no base emit: pass --base or import the base first (scene property iwz_base_emit)')
        return out
    if mode == 'replace':
        try:
            base.zone_box(s.get('zone'))
        except KeyError as e:
            E(str(e).strip('"'))
    zones = sc.get('zones', [])
    if mode == 'new':
        if not zones:
            E('a new section needs a zone volume (entity kind zone)')
        for z in zones:
            if not BC.ZONE_NAME_OK(z['name']):
                E('zone name %r: lower case letters, digits and _' % z['name'])
            if z['name'] in base.zones:
                E('new zone %s is already a zone of the base' % z['name'])
            b = z['box']
            if not (b[3] > b[0] and b[4] > b[1] and b[5] > b[2]):
                E('zone %s: empty box' % z['name'])
            for k, bz in base.zones.items():
                if BC.box_overlap3(b, bz['box']):
                    E('new zone %s overlaps the base zone %s' % (z['name'], k))
        for i, a in enumerate(zones):
            for c in zones[i + 1:]:
                if BC.box_overlap3(a['box'], c['box']):
                    E('new zones %s and %s overlap' % (a['name'], c['name']))
        if not sc.get('doors') and not sc.get('links'):
            E('a new zone has no door and no link to the rest of the map: nobody can reach it')
    allz = set(base.zones) | {z['name'] for z in zones}
    for d in sc.get('doors', []):
        if int(d['cost']) not in DOOR_COSTS:
            E('door %s: cost %s, the stock debris purchases are %s' % (d['name'], d['cost'], DOOR_COSTS))
        zs = d.get('zones') or []
        if len(zs) != 2 or any(z not in allz for z in zs):
            E('door %s: `zones` must name two zones of the base or of this section (got %s)' % (d['name'], zs))
        b = d['box']
        if min(b[3] - b[0], b[4] - b[1]) > 48.0:
            E('door %s: the box is %.0f x %.0f, one horizontal side must be at most 48' % (d['name'], b[3] - b[0], b[4] - b[1]))
    for a, b in sc.get('links', []):
        if a not in allz or b not in allz:
            E('link %s - %s names a zone that exists nowhere' % (a, b))
    for p in sc.get('perks', []):
        if p['perk'] not in scenegen.Emitter.PERK_SCRIPTABLE:
            E('perk %r is not a stock machine' % p['perk'])
    for w in sc.get('wall_buys', []):
        if not w.get('weapon') and (w.get('weapon_class') or '') not in scenegen.Emitter.WALL_WEAPON:
            E('wall buy: class %r unknown and no weapon name' % w.get('weapon_class'))
    for sp in sc.get('spawners', []):
        if sp.get('kind', 'ground') not in ('ground', 'wall', 'ceiling'):
            E('spawner kind %r (ground, wall or ceiling)' % sp.get('kind'))
    for m in sc.get('meshes', []):
        if m.get('mode', 'both') != 'collision' and not (m.get('material') or '').startswith('w/') and not m.get('free_material'):
            E('mesh %s: material %r is not an IW7 world material (w/...)' % (m['name'], m.get('material')))
    if not any(m.get('mode', 'both') in ('both', 'render') for m in sc.get('meshes', [])):
        W('the section has no render geometry')
    return out


def _zone_locator(sc, base):
    s = sc['section']
    boxes = [(z['name'], z['box']) for z in sc.get('zones', [])]
    if s.get('mode') == 'replace':
        boxes.append((s['zone'], base.zone_box(s['zone'])))
    default = (sc.get('zones') or [{'name': s.get('zone')}])[0]['name'] if sc.get('zones') else s.get('zone')

    def zone_of(p, strict=False):
        for n, b in boxes:
            if BC.in_box(p, b, 1.0):
                return n
        return None if strict else default
    return zone_of


def build_section(sc, out, base, log=print, tpl_free=True):
    """scene dict (see the module doc) -> section folder `out` (None: validate only); raises ValueError listing the errors (nothing is
    written then); returns the report"""
    s = sc.get('section') or {}
    issues = validate_section(sc, base)
    errs = [m for sev, m in issues if sev == 'ERROR']
    if errs:
        raise ValueError('section refused:\n  ' + '\n  '.join(errs))
    mode = s['mode']
    zone_of = _zone_locator(sc, base)
    # ---- the geometry as the world builder writes it (also the collision the checks run on)
    mesh = mapgen.Mesh()
    mats = BC.material_table()
    wb = BC.WorldBuilder(mesh, scenegen.LM, mats)
    ramps, ramp_rows = BC.stair_ramps(sc.get('meshes', []))
    for rec in sc.get('meshes', []):
        wb.add(rec)
    for rec in ramps:
        wb.add(rec)
    props = []
    for p in sc.get('props', []):
        props.append(dict(p))
    # prop clip boxes are solid collision (the base decor clip blocks players, zombies and the navigation)
    clip_rows = {}
    for k, p in enumerate(props):
        if p.get('clip'):
            if isinstance(p['clip'], (list, tuple)):
                b = [float(v) for v in p['clip']]
            else:
                bd = model_bounds(p['model'])
                if bd is None:
                    issues.append(('WARN', 'prop %s: clip requested but the model bounds are unknown (no dump): no clip box written' % p['model']))
                    continue
                b = clip_box_of(p, bd)
            clip_rows[k] = b
            for t in box_tris(b):
                wb.add({'name': 'clip_%s_%d' % (p['model'], k), 'material': '', 'mode': 'collision', 'tris': [t]})
    tris = Tris(mesh.col)
    # ---- entities
    spawners = [{'zone': zone_of(sp['at']), 'origin': [round(v, 2) for v in sp['at']], 'kind': sp.get('kind', 'ground'), 'yaw': float(sp.get('yaw', 0))}
                for sp in sc.get('spawners', [])]
    interactions = interaction_rows(sc, zone_of)
    doors = [door_row(d) for d in sc.get('doors', [])]
    lights = light_rows(sc, zone_of)
    decals = [dict(r) for r in sc.get('decals', [])]
    signs = [dict(r) for r in sc.get('signs', [])]
    fx = [dict(r) for r in sc.get('fx', [])]
    for r in decals:
        pt = [r['s'], r['fixed'], r['zc']] if r['axis'] == 'x' else [r['fixed'], r['s'], r['zc']]
        r['zone'] = r.get('zone') or zone_of(pt)
    for r in signs:
        r['zone'] = r.get('zone') or zone_of(r['center'])
    for r in fx:
        r['zone'] = r.get('zone') or zone_of(r['origin'])
    views = {}
    for z, rows in (sc.get('views') or {}).items():
        for v in rows:
            views.setdefault(z or zone_of(v[:3]), []).append([round(float(c), 2) for c in v])
    for r in spawners + interactions + lights:
        if zone_of(r['origin'], strict=True) is None:
            issues.append(('ERROR', 'the %s at %s is outside every zone of this section' % (r.get('kind', r.get('type', 'entity')), [round(v) for v in r['origin']])))
    # ---- checks on the triangles
    stats = {}
    if mode == 'replace':
        zone = s['zone']
        openings = base.openings(zone)
        issues += check_openings(tris, openings)
        cells = base.cells(zone)
        zregs = [r for r in base.plan.get('regions', [])]
        segs = footprint_walls(zregs, cells, zone, floor_default=base.zone_box(zone)[2] + 16)
        r, st = check_closure_plan(tris, segs, openings)
        issues += r
        stats['closure'] = st
        r, st = check_nav_heights(tris, cells)
        issues += r
        stats['nav'] = st
        base_inter = base.interactions(zone)
        issues += check_clearances(tris, base_inter, base.spawners(zone))
    else:
        base_inter = []
        for z in sc['zones']:
            box = z['box']
            fl = float(z.get('floor', box[2])); ce = float(z.get('ceiling', box[5]))
            dopen = [door_box(d) for d in doors]
            r, st = check_closure_faces(tris, box, dopen, fl, ce)
            issues += r
            stats['closure'] = st
            nx, ny = int((box[3] - box[0]) // 32), int((box[4] - box[1]) // 32)
            pts = [(box[0] + (i + 0.5) * 32, box[1] + (j + 0.5) * 32) for i in range(nx) for j in range(ny)]
            f = floor_at(tris, pts, [fl] * len(pts), reach=6.0)
            nofl = int(np.isnan(f).sum())
            if nofl > 0.5 * len(pts):
                issues.append(('ERROR', 'zone %s: no walkable floor at %d of %d sample columns (a floor at z %g is expected)' % (z['name'], nofl, len(pts), fl)))
            elif nofl:
                issues.append(('WARN', 'zone %s: no floor at %d of %d sample columns (holes or props with a clip)' % (z['name'], nofl, len(pts))))
        issues += check_openings(tris, [{'name': d['name'], 'kind': 'door', 'box': door_box(d)} for d in doors])
    own_inter = [dict(r) for r in interactions]
    issues += check_clearances(tris, own_inter, spawners)
    off, slanted = floor_edges_off_grid(tris)
    if off:
        issues.append(('WARN', '%d walkable floor edges are off the 16 unit grid (the navigation lattice is 32, the compiler snaps to 16): first %s' %
                       (len(off), '; '.join('%s -> %s' % (a, b) for a, b in off[:4]))))
    stats['floor_edges'] = {'off_grid': len(off), 'slanted': len(slanted)}
    # ---- models
    idx = model_index()
    kit = {}
    unknown = []
    for p in props:
        if p['model'] in kit:
            continue
        if idx is None:
            kit[p['model']] = '?'
            continue
        path = idx.get('xmodel', p['model'])
        if path is None:
            unknown.append(p['model'])
        else:
            kit[p['model']] = model_source_zone(path)
    if idx is None and props:
        issues.append(('WARN', 'the stock dumps are not installed (IWZ_RUNTIME): the %d prop models were not checked against the catalogue' % len(kit)))
    for m in sorted(set(unknown)):
        issues.append(('ERROR', 'prop model %s is not in the catalogue (no stock dump holds it)' % m))
    errs = [m for sev, m in issues if sev == 'ERROR']
    if errs:
        raise ValueError('section refused:\n  ' + '\n  '.join(errs))
    # ---- write
    nv = ni = ns = 0
    if out:
        os.makedirs(out, exist_ok=True)
    if out and wb.render_tris:
        nv, ni, ns, _ = mapgen.write_world(mesh, os.path.join(out, 'world.bin'))
    elif out and os.path.isfile(os.path.join(out, 'world.bin')):
        os.remove(os.path.join(out, 'world.bin'))
    col = [[[round(c, 3) for c in p] for p in t] for t in mesh.col]
    if out:
        json.dump({'tris': col, 'tags': [mesh.col_tag.get(i) for i in range(len(col))]}, open(os.path.join(out, 'collision.json'), 'w'), separators=(',', ':'))
    prop_rows = []
    for k, p in enumerate(props):
        prop_rows.append({'zone': zone_of(p['at']), 'model': p['model'], 'origin': [round(v, 2) for v in p['at']], 'angles': [round(float(a), 3) for a in p['angles']],
                          'scale': float(p.get('scale', 1.0)), 'static': bool(p.get('static', True)), 'clip': clip_rows.get(k)})
    new_zones = [{'id': z['name'], 'box': [float(v) for v in z['box']], 'floor': float(z.get('floor', z['box'][2])), 'ceiling': float(z.get('ceiling', z['box'][5])),
                  'probe': [float(v) for v in (z.get('probe') or [0.9, 0.9, 0.95, 0.6])]} for z in sc.get('zones', [])] if mode == 'new' else []
    sec = {'schema': SCHEMA, 'name': s['name'], 'replace_zones': [s['zone']] if mode == 'replace' else [], 'new_zones': new_zones, 'doors': doors,
           'links': [list(l) for l in sc.get('links', [])], 'spawners': spawners, 'interactions': interactions, 'lights': lights, 'props': prop_rows,
           'decals': decals, 'signs': signs, 'fx': fx, 'views': views}
    if sc.get('zone_defaults'):
        sec['zone_defaults'] = sc['zone_defaults']
    used = sorted({m['material'] for m in sc.get('meshes', []) if m.get('material') and m.get('mode', 'both') != 'collision'})
    if out:
        json.dump(sec, open(os.path.join(out, 'section.json'), 'w'), indent=1, default=list)
        json.dump(kit, open(os.path.join(out, 'kit_models.json'), 'w'), indent=1, sort_keys=True)
        json.dump({'custom': {}, 'used': used}, open(os.path.join(out, 'custom_materials.json'), 'w'), indent=1)
    foreign = sorted(m for m, z in kit.items() if z not in ('cp_zmb', '?') and not z.startswith(('techsets', 'global', 'common', 'patch')))
    report = {'schema': 'iwz.section.report/1', 'name': s['name'], 'mode': mode, 'zones': sec['replace_zones'] or [z['id'] for z in new_zones],
              'budgets': {'render_triangles': wb.render_tris, 'collision_triangles': len(col), 'degenerate_dropped': wb.degenerate, 'surfaces': ns, 'vertices': nv,
                          'materials': len(used), 'props': len(prop_rows), 'distinct_models': len(kit), 'lights': len(lights), 'spawners': len(spawners),
                          'interactions': len(interactions), 'decals': len(decals), 'signs': len(signs), 'fx': len(fx),
                          'doors': len(doors), 'stairs': len(ramp_rows)},
              'checks': stats, 'kit_models_foreign': foreign, 'warnings': [m for sev, m in issues if sev == 'WARN'], 'errors': []}
    if out:
        json.dump(report, open(os.path.join(out, 'section_report.json'), 'w'), indent=1, default=list)
    log('section %s (%s): %d render tris, %d collision tris, %d props (%d models), %d lights, %d spawners, %d warnings' %
        (s['name'], mode, wb.render_tris, len(col), len(prop_rows), len(kit), len(lights), len(spawners), len(report['warnings'])))
    return report
