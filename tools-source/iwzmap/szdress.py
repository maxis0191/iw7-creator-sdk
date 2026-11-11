"""szdress: zone dressing as described data, checked before any build.

A dressing spec (JSON, format below) says what stands in a zone and why: single pieces, vignettes (a group of
pieces, lights, solids and panels placed together and turned as one: a banquet table with its fallen chairs, a
decontamination tent), rows and seeded scatters. This tool expands it against the scene and the models' own bounds
(the worldkit database of the template map), checks it, and writes a scenegen dress file ({zone: {props, lights,
solids}}, named in the scene's `dress_files`).

  python -I -B szdress.py build  <spec.json> <scene.json> --db <cp_zmb.sqlite> --out <dress.json> [--layout <src>/layout.json] [--report r.json]
  python -I -B szdress.py plan   <dress.json> <scene.json> --db <cp_zmb.sqlite> --zone <id> --png <out.png> [--layout <src>/layout.json]
  python -I -B szdress.py report <dress.json>

Placement (every piece): "m" model (or "pick": [models] with "var": k, deterministic); position "at": [x, y] or
"wall": "north|south|east|west" with "s" (coordinate along the wall) and "gap" (default 0.5); "yaw"/"pitch"/"roll"/
"scale"; height: default the base of the model's bounds on the floor under it, "h" lifts it, "z" is absolute,
"ceil": d hangs it with the top of its bounds d below the ceiling, "on": "<id>" rests it on the top of another piece.
A wall piece with no "yaw" is turned so that the side its bounds put at the origin plane (its back) faces the wall.
"clip": "auto" (default), true, false or [hx, hy, hz]: auto gives a player-and-zombie clip box to any floor-standing
piece at least 12 units across and 20 tall (prefab props do not block by themselves, so this is how a piece blocks).

Groups: {"v": "<vignette>", "at" | "wall"/"s", "yaw"} places a vignette (its own "items", "lights", "solids",
"panels" in coordinates relative to its origin, x forward); {"row": {"n", "step": [dx, dy]}, ...piece} repeats a
piece (with "vary": {"m": [...], "yaw": [...]} cycling); {"scatter": {"n", "rect": [x0, y0, x1, y1], "pick": [...],
"seed", "min_gap"}} places small litter deterministically without overlaps.

Lights follow scenegen's zone `lights` (at, h or z, type, color, radius, intensity, dir, inner, outer, fixture).
Solids follow scenegen's solids (rect, z0, z1 or h0, h1 above the floor, mat). Panels: {"mat", "wall", "s", "h"
(bottom above the floor) or "z", "w", "ht", "gap"} become flat sign quads (the image fitted once).

Checks (ERROR stops the build): a piece outside its zone, standing across two floor heights, overlapping another piece
(3D bounds, 1 unit tolerance, unless one rests on the other or "overlap_ok"), a clipped or tall piece in an opening's
approach (the opening's span plus 32 each side, 128 deep), a clipped piece on a flight or within 40 of a spawner,
anything within 48 of an interaction or a player start; more props than the zone budget, a model used more than 25
times in a zone.
"""
import argparse, collections, json, math, os, random, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenegen as SG

TOL = 1.0
MAX_REPEAT = 25


class DressError(Exception):
    pass


# --------------------------------------------------------------------------- rotation (compiler / Quake angles)
def axes(pitch, yaw, roll):
    p, y, r = (math.radians(a) for a in (pitch, yaw, roll))
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(r), math.cos(r)
    fwd = (cp * cy, cp * sy, -sp)
    right = (-sr * sp * cy + cr * sy, -sr * sp * sy - cr * cy, -sr * cp)
    up = (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp)
    left = tuple(-c for c in right)
    return fwd, left, up


def world_box(b, pitch, yaw, roll, scale):
    """AABB (offset from the origin) of local bounds b = (x0, y0, z0, x1, y1, z1) turned and scaled"""
    f, l, u = axes(pitch, yaw, roll)
    xs, ys, zs = [], [], []
    for x in (b[0], b[3]):
        for y in (b[1], b[4]):
            for z in (b[2], b[5]):
                p = [scale * (x * f[k] + y * l[k] + z * u[k]) for k in range(3)]
                xs.append(p[0]); ys.append(p[1]); zs.append(p[2])
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def rot2(x, y, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return x * c - y * s, x * s + y * c


WALL_IN = {'north': (0, -1), 'south': (0, 1), 'east': (-1, 0), 'west': (1, 0)}   # inward normal of a zone wall


def back_yaw(b, wall):
    """yaw that turns the model's back (the local side whose bound is at the origin plane) to the wall"""
    cands = [(abs(b[0]), b[3], 0.0), (abs(b[3]), -b[0], 180.0), (abs(b[1]), b[4], 90.0), (abs(b[4]), -b[1], 270.0)]
    # (distance of the back plane from the origin, depth toward the front, local angle of the front direction)
    cands = [c for c in cands if c[1] > 0.5]
    back = min(cands, key=lambda c: (c[0], -c[1]))
    nx, ny = WALL_IN[wall]
    inward = math.degrees(math.atan2(ny, nx))
    return (inward - back[2]) % 360.0


# --------------------------------------------------------------------------- models
class Models:
    def __init__(self, db):
        c = sqlite3.connect(db)
        self.b = {r[0]: tuple(r[1:]) for r in c.execute(
            'select name, bmin_x, bmin_y, bmin_z, bmax_x, bmax_y, bmax_z from models')}

    def bounds(self, m):
        if m not in self.b:
            raise DressError('model %s is not in the template map (no static twin): not placeable' % m)
        return self.b[m]


# --------------------------------------------------------------------------- expansion
class Dresser:
    def __init__(self, spec, scene, models, layout=None):
        self.spec, self.sc, self.M, self.layout = spec, scene, models, layout
        self.vig = spec.get('vignettes', {})
        self.errors, self.notes = [], []

    def zone_wall(self, z, side, box=None):
        bs = [z.boxes[box]] if box is not None else z.boxes
        b = bs[0]
        return {'north': ('y', b[3]), 'south': ('y', b[1]), 'east': ('x', b[2]), 'west': ('x', b[0])}[side], b

    def frame(self, z, it, parent=None):
        """the placement frame of an item: (x, y, yaw) in world, from at / wall+s, under an optional parent frame"""
        yaw = float(it.get('yaw', 0.0))
        if parent is not None:
            px, py, pyaw = parent
            if 'wall' in it:
                raise DressError('wall placement inside a vignette: use at')
            dx, dy = rot2(float(it['at'][0]), float(it['at'][1]), pyaw)
            return px + dx, py + dy, (pyaw + yaw) % 360.0
        if 'at' in it:
            return float(it['at'][0]), float(it['at'][1]), yaw
        if 'wall' in it:
            (ax, plane), b = self.zone_wall(z, it['wall'], it.get('box'))
            s = float(it['s'])
            off = float(it.get('off', 0.0))
            nx, ny = WALL_IN[it['wall']]
            if ax == 'y':
                return s, plane + ny * off, yaw
            return plane + nx * off, s, yaw
        raise DressError('item without at or wall: %s' % json.dumps(it)[:120])

    def expand(self, z, items, parent=None, out=None, tag=''):
        out = out if out is not None else {'props': [], 'lights': [], 'solids': [], 'panels': []}
        for k, it in enumerate(items):
            if set(it) <= {'note'}:
                continue                       # a comment line of the spec
            if 'row' in it:
                r = it['row']
                vary = it.get('vary', {})
                base = {kk: v for kk, v in it.items() if kk not in ('row', 'vary')}
                for i in range(int(r['n'])):
                    one = dict(base)
                    if 'at' in base:
                        one['at'] = [base['at'][0] + i * r['step'][0], base['at'][1] + i * r['step'][1]]
                    else:
                        one['s'] = float(base['s']) + i * float(r['step'][0])
                    for key, vals in vary.items():
                        one[key] = vals[i % len(vals)]
                    if 'id' in base:
                        one['id'] = '%s_%d' % (base['id'], i)
                    self.expand(z, [one], parent, out, tag)
                continue
            if 'scatter' in it:
                self.scatter(z, it['scatter'], parent, out, tag)
                continue
            if 'v' in it:
                v = self.vig.get(it['v'])
                if v is None:
                    raise DressError('unknown vignette %s' % it['v'])
                fx, fy, fyaw = self.frame(z, it, parent)
                if 'wall' in it and 'depth' in v:
                    nx, ny = WALL_IN[it['wall']]
                    fx += nx * float(v['depth']); fy += ny * float(v['depth'])
                fr = (fx, fy, fyaw)
                vt = '%s%s@%d' % (tag, it['v'], k)
                self.expand(z, v.get('items', []), fr, out, vt + '/')
                for l in v.get('lights', []):
                    out['lights'].append(self.light(z, l, fr))
                for s in v.get('solids', []):
                    out['solids'].append(self.solid(z, s, fr))
                for p in v.get('panels', []):
                    out['panels'].append(dict(p, _frame=fr))
                continue
            out['props'].append(self.piece(z, it, parent, tag + str(it.get('id', k))))
        return out

    def scatter(self, z, sc, parent, out, tag):
        rnd = random.Random(int(sc.get('seed', 1)))
        x0, y0, x1, y1 = sc['rect']
        gap = float(sc.get('min_gap', 8))
        got, tries = 0, 0
        taken = []
        while got < int(sc['n']) and tries < 4000:
            tries += 1
            x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            if any((x - a) ** 2 + (y - b) ** 2 < gap * gap for a, b in taken):
                continue
            m = sc['pick'][rnd.randrange(len(sc['pick']))]
            it = {'m': m, 'at': [x, y], 'yaw': rnd.uniform(0, 360), 'clip': False, 'id': '%sscatter%d' % (tag, got)}
            try:
                p = self.piece(z, it, parent, it['id'])
            except DressError:
                continue
            b = p['box']
            if any(z.floor_at(cx, cy) is None for cx, cy in ((b[0], b[1]), (b[3], b[4]))):
                continue
            # litter keeps off what is already placed and off the places gameplay needs
            if any(min(b[3], q['box'][3]) > max(b[0], q['box'][0]) - 2 and min(b[4], q['box'][4]) > max(b[1], q['box'][1]) - 2
                   for q in out['props']):
                continue
            if any((p['x'] - o[0]) ** 2 + (p['y'] - o[1]) ** 2 < 60.0 ** 2 for o in self.keep_points(z)):
                continue
            out['props'].append(p)
            taken.append((x, y)); got += 1

    def keep_points(self, z):
        if not self.layout:
            return []
        if not hasattr(self, '_keep'):
            self._keep = {}
        if z.id not in self._keep:
            lay = self.layout
            pts = [s['origin'] for s in lay.get('spawners', []) if s.get('zone') == z.id]
            pts += [i['origin'] for i in lay.get('interactions', []) + lay.get('markers', []) if i.get('zone') == z.id and i.get('origin')]
            if self.sc.start_zone == z.id:
                pts += [s.get('origin', s) if isinstance(s, dict) else s for s in lay.get('starts', [])]
            self._keep[z.id] = pts
        return self._keep[z.id]

    def piece(self, z, it, parent, pid):
        m = it['m'] if 'm' in it else it['pick'][int(it.get('var', 0)) % len(it['pick'])]
        b = self.M.bounds(m)
        sc = float(it.get('scale', 1.0))
        x, y, yaw = self.frame(z, it, parent)
        if 'wall' in it and 'yaw' not in it:
            yaw = back_yaw(b, it['wall'])
        pitch, roll = float(it.get('pitch', 0)), float(it.get('roll', 0))
        wb = world_box(b, pitch, yaw, roll, sc)
        if 'wall' in it and parent is None:
            (ax, plane), _ = self.zone_wall(z, it['wall'], it.get('box'))
            gap = float(it.get('gap', 0.5)) + float(it.get('off', 0.0))
            nx, ny = WALL_IN[it['wall']]
            if ax == 'y':
                y = plane + ny * gap - (wb[1] if ny > 0 else wb[4])
            else:
                x = plane + nx * gap - (wb[0] if nx > 0 else wb[3])
        fz = z.floor_at(x, y)
        if fz is None:
            raise DressError('%s (%s) at %.0f,%.0f is outside zone %s' % (pid, m, x, y, z.id))
        if 'z' in it:
            zz = float(it['z'])
        elif 'ceil' in it:
            zz = z.ceiling - float(it['ceil']) - wb[5]
        else:
            zz = fz + float(it.get('h', 0.0)) - wb[2]
        return {'id': pid, 'model': m, 'x': x, 'y': y, 'z': zz, 'yaw': yaw, 'pitch': pitch, 'roll': roll, 'scale': sc,
                'box': (x + wb[0], y + wb[1], zz + wb[2], x + wb[3], y + wb[4], zz + wb[5]), 'floor': fz,
                'on': it.get('on'), 'clip': it.get('clip', 'auto'), 'overlap_ok': bool(it.get('overlap_ok')), 'near_ok': bool(it.get('near_ok')),
                'standing': 'z' not in it and 'ceil' not in it and float(it.get('h', 0)) <= 2 and not it.get('on'),
                'note': it.get('note', '')}

    def light(self, z, l, parent=None):
        out = {k: v for k, v in l.items() if k not in ('at', 'dir')}
        x, y = float(l['at'][0]), float(l['at'][1])
        d = l.get('dir')
        if parent is not None:
            dx, dy = rot2(x, y, parent[2]); x, y = parent[0] + dx, parent[1] + dy
            if d:
                ddx, ddy = rot2(d[0], d[1], parent[2]); d = [ddx, ddy, d[2]]
        out['at'] = [round(x, 2), round(y, 2)]
        if d:
            out['dir'] = d
        if 'h' in l and 'z' not in l:
            fz = z.floor_at(x, y)
            out.pop('h'); out['z'] = round(fz + float(l['h']), 2)
        if 'ceil' in l:
            out.pop('ceil'); out['z'] = round(z.ceiling - float(l['ceil']), 2)
        if 'pool' in out:
            # intensity from the wanted light on the floor straight below (baker units: E = I (100 / d)^2 at the axis)
            c = out.get('color', [1, 1, 1]); lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
            fz = z.floor_at(x, y); fz = z.floor if fz is None else fz
            d_ = max(24.0, float(out['z']) - fz)
            out['intensity'] = round(float(out.pop('pool')) * d_ * d_ / (3e4 * max(lum, 0.05)), 4)
            out.setdefault('radius', round(max(160.0, d_ * 1.6)))
        return out

    def solid(self, z, s, parent=None):
        r = [float(v) for v in s['rect']]
        if parent is not None:
            pts = [rot2(r[0], r[1], parent[2]), rot2(r[2], r[3], parent[2])]
            if abs((parent[2] % 90)) > 1e-6:
                raise DressError('a vignette with solids turns only by multiples of 90 degrees')
            r = [parent[0] + min(p[0] for p in pts), parent[1] + min(p[1] for p in pts),
                 parent[0] + max(p[0] for p in pts), parent[1] + max(p[1] for p in pts)]
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        fz = z.floor_at(cx, cy)
        if fz is None:
            raise DressError('solid at %.0f,%.0f outside zone %s' % (cx, cy, z.id))
        z0 = float(s['z0']) if 'z0' in s else fz + float(s.get('h0', 0))
        z1 = float(s['z1']) if 'z1' in s else (z.ceiling if 'h1' not in s else fz + float(s['h1']))
        out = {'rect': [round(v, 2) for v in r], 'z0': round(z0, 2), 'z1': round(z1, 2), 'mat': s.get('mat', 'conc_wall')}
        if s.get('note'):
            out['note'] = s['note']
        return out

    def panel(self, z, p):
        if p.get('ceiling'):
            # a ceiling panel (light panel, tile): flat under the ceiling, facing down
            cx, cy = float(p['at'][0]), float(p['at'][1]); w, d = float(p['w']), float(p['ht'])
            zz = z.ceiling - float(p.get('gap', 0.5))
            q = [[cx - w / 2, cy + d / 2, zz], [cx + w / 2, cy + d / 2, zz], [cx + w / 2, cy - d / 2, zz], [cx - w / 2, cy - d / 2, zz]]
            return {'quad': [[round(c, 2) for c in v] for v in q], 'normal': [0.0, 0.0, -1.0], 'mat': p['mat'], 'fit': p.get('fit', True)}
        fr = p.get('_frame') or ((0.0, 0.0, 0.0) if 'at' in p else None)
        w, ht = float(p['w']), float(p['ht'])
        if fr is not None:
            # a vignette panel: "at" [x, y] of its centre on its face, facing the vignette's +x turned by "yaw"
            cx, cy = rot2(float(p['at'][0]), float(p['at'][1]), fr[2])
            cx += fr[0]; cy += fr[1]
            ang = math.radians(fr[2] + float(p.get('yaw', 0)))
            nx, ny = math.cos(ang), math.sin(ang)
        else:
            (ax, plane), _ = self.zone_wall(z, p['wall'], p.get('box'))
            nx, ny = WALL_IN[p['wall']]
            gap = float(p.get('gap', 0.6))
            if ax == 'y':
                cx, cy = float(p['s']), plane + ny * gap
            else:
                cx, cy = plane + nx * gap, float(p['s'])
        fz = z.floor_at(cx - nx * 2, cy - ny * 2)
        if fz is None:
            fz = z.floor
        z0 = float(p['z']) if 'z' in p else fz + float(p.get('h', 0))
        tx, ty = -ny, nx          # left to right seen from the front
        a = (cx - tx * w / 2, cy - ty * w / 2)
        b = (cx + tx * w / 2, cy + ty * w / 2)
        quad = [[a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z0 + ht], [a[0], a[1], z0 + ht]]
        return {'quad': [[round(c, 2) for c in q] for q in quad], 'normal': [round(nx, 4), round(ny, 4), 0.0],
                'mat': p['mat'], 'fit': p.get('fit', True)}

    # ----------------------------------------------------------------------- checks
    def check_zone(self, z, out, budget):
        err = lambda m: self.errors.append('%s: %s' % (z.id, m))
        props = out['props']
        byid = {p['id'].split('/')[-1]: p for p in props}
        for p in props:
            b = p['box']
            corners = [(b[0] + 1, b[1] + 1), (b[3] - 1, b[1] + 1), (b[3] - 1, b[4] - 1), (b[0] + 1, b[4] - 1)]
            for (cx, cy) in corners:
                if not z.inside(cx, cy):
                    err('%s (%s) reaches outside the zone at %.0f,%.0f' % (p['id'], p['model'], cx, cy)); break
            if p['standing']:
                hs = [z.floor_at(cx, cy) for cx, cy in corners + [(p['x'], p['y'])]]
                hs = [h for h in hs if h is not None]
                if hs and max(hs) - min(hs) > 2.0 and not any(f.rect[0] <= p['x'] <= f.rect[2] and f.rect[1] <= p['y'] <= f.rect[3] for f in z.flights):
                    err('%s (%s) stands across floors %.0f..%.0f' % (p['id'], p['model'], min(hs), max(hs)))
            # clip decision
            w, d, h = b[3] - b[0], b[4] - b[1], b[5] - b[2]
            c = p['clip']
            low = p['z'] + 0 <= (p['floor'] + 24)
            if c == 'auto':
                c = bool(min(w, d) >= 12 and h >= 20 and b[2] <= p['floor'] + 24)
            p['clipbox'] = None
            if c is True:
                p['clipbox'] = [max(1.0, (w - 2) / 2), max(1.0, (d - 2) / 2), max(1.0, (b[5] - p['floor']) / 2)]
            elif isinstance(c, list):
                p['clipbox'] = [float(v) for v in c]
        # overlaps
        for i, a in enumerate(props):
            for bb in props[i + 1:]:
                if a['overlap_ok'] or bb['overlap_ok']:
                    continue
                if a['on'] and byid.get(a['on']) is bb or bb['on'] and byid.get(bb['on']) is a:
                    continue
                A, B = a['box'], bb['box']
                ov = [min(A[k + 3], B[k + 3]) - max(A[k], B[k]) for k in range(3)]
                if all(o > TOL for o in ov):
                    err('%s (%s) and %s (%s) intersect (%.0f x %.0f x %.0f)' % (a['id'], a['model'], bb['id'], bb['model'], ov[0], ov[1], ov[2]))
        # clearance against the emitted layout
        if self.layout:
            lay = self.layout
            for o in self.sc.openings():
                self.sc.locate(o)
                if z.id not in o['zones']:
                    continue
                plane, face = o['planes'][z.id], o['facing'][z.id]
                s0, s1 = o['span'][0] - 32, o['span'][1] + 32
                d0, d1 = sorted((plane, plane + face * 128))
                keep = (s0, d0, s1, d1) if o['axis'] == 'x' else (d0, s0, d1, s1)
                for p in props:
                    b = p['box']
                    if (p['clipbox'] or b[5] - b[2] > 18) and b[2] < o['top'] and \
                            b[0] < keep[2] and b[3] > keep[0] and b[1] < keep[3] and b[4] > keep[1]:
                        err('%s (%s) stands in the approach of opening %s' % (p['id'], p['model'], o['id']))
            for f in z.flights:
                r = f.rect
                for p in props:
                    b = p['box']
                    if p['clipbox'] and b[0] < r[2] + 16 and b[3] > r[0] - 16 and b[1] < r[3] + 16 and b[4] > r[1] - 16 and not p.get('flight_ok'):
                        if not (z.id == 'escalator_hall'):
                            err('%s (%s) clip box on flight %s' % (p['id'], p['model'], f.id))
            pts = []
            for s in lay.get('spawners', []):
                if s.get('zone') == z.id:
                    pts.append(('spawner %s' % s.get('kind', ''), s['origin'], 40.0, 'ceil' if s.get('kind') == 'ceiling' else True))
            for it in lay.get('interactions', []) + lay.get('markers', []):
                if it.get('zone') == z.id and it.get('origin'):
                    pts.append(('%s %s' % (it.get('kind'), it.get('id', it.get('class', ''))), it['origin'], 48.0, False))
            for st in lay.get('starts', []):
                o_ = st.get('origin', st) if isinstance(st, dict) else st
                if self.sc.start_zone == z.id:
                    pts.append(('player start', o_, 48.0, False))
            for name, o_, r, clip_only in pts:
                for s in out['solids']:
                    if clip_only is True and 'rect' in s and s['z0'] < o_[2] + 60 and s['z1'] > o_[2] + 1:
                        rr = s['rect']; dx = max(rr[0] - o_[0], 0, o_[0] - rr[2]); dy = max(rr[1] - o_[1], 0, o_[1] - rr[3])
                        if dx * dx + dy * dy < r * r:
                            err('solid %s within %g of %s at %.0f,%.0f' % (rr, r, name, o_[0], o_[1]))
                for p in props:
                    if p['near_ok']:
                        continue
                    if clip_only == 'ceil':
                        if p['box'][5] < p['floor'] + 96:
                            continue
                    elif clip_only and not p['clipbox']:
                        continue
                    b = p['box']
                    dx = max(b[0] - o_[0], 0, o_[0] - b[3]); dy = max(b[1] - o_[1], 0, o_[1] - b[4])
                    if dx * dx + dy * dy < r * r and b[5] - b[2] > 6:
                        err('%s (%s) within %g of %s at %.0f,%.0f' % (p['id'], p['model'], r, name, o_[0], o_[1]))
        n = len(props)
        if budget is not None and n > budget:
            err('%d props over the zone budget %d' % (n, budget))
        cnt = collections.Counter(p['model'] for p in props)
        for m, k in cnt.items():
            if k > MAX_REPEAT:
                err('model %s used %d times (most %d a zone)' % (m, k, MAX_REPEAT))
        return {'props': n, 'budget': budget, 'distinct_models': len(cnt), 'clipped': sum(1 for p in props if p['clipbox']),
                'lights': len(out['lights']), 'solids': len(out['solids']), 'panels': len(out['panels']),
                'most_used': cnt.most_common(5)}


def build(spec_path, scene_path, db, out_path, layout_path=None, report_path=None):
    spec = json.load(open(spec_path, encoding='utf-8'))
    sc = SG.Scene.load(scene_path)
    lay = json.load(open(layout_path)) if layout_path else None
    D = Dresser(spec, sc, Models(db), lay)
    result, report = {}, {'schema': 'iwz.dress-report/1', 'zones': {}}
    for zid, zs in spec['zones'].items():
        z = sc.zones[zid]
        out = D.expand(z, zs.get('items', []))
        for l in zs.get('lights', []):
            out['lights'].append(D.light(z, l))
        for s in zs.get('solids', []):
            out['solids'].append(D.solid(z, s))
        out['panels'] += zs.get('panels', [])
        out['panels'] = [D.panel(z, p) for p in out['panels']]
        report['zones'][zid] = D.check_zone(z, out, zs.get('budget'))
        props = []
        for p in out['props']:
            rec = {'model': p['model'], 'at': [round(p['x'], 2), round(p['y'], 2)], 'z': round(p['z'], 2),
                   'yaw': round(p['yaw'], 2), 'static': True, 'id': p['id']}
            if p['pitch']: rec['pitch'] = p['pitch']
            if p['roll']: rec['roll'] = p['roll']
            if p['scale'] != 1.0: rec['scale'] = p['scale']
            if p['clipbox']:
                # the clip box is centred on the prop's bounds, not its origin: written as its own collision solid
                b = p['box']
                cb = []
                for lo, hi in ((b[0], b[3]), (b[1], b[4])):
                    c_, h_ = (lo + hi) / 2, max(2.0, (hi - lo) / 2 - 1)      # 1 unit inside the bounds, at least 4 thick
                    cb.append((c_ - h_, c_ + h_))
                rec['clip_box'] = [round(cb[0][0], 2), round(cb[1][0], 2), round(p['floor'], 2), round(cb[0][1], 2), round(cb[1][1], 2), round(b[5], 2)]
            props.append(rec)
        result[zid] = {'props': props, 'lights': out['lights'], 'solids': out['solids'] + out['panels']}
    report['errors'] = D.errors
    report['total_props'] = sum(r['props'] for r in report['zones'].values())
    with open(out_path, 'w', encoding='utf-8') as fo:
        json.dump(result, fo, indent=0)
    if report_path:
        with open(report_path, 'w') as fo:
            json.dump(report, fo, indent=1, default=str)
    return report


# --------------------------------------------------------------------------- plan picture (pillow)
def plan(dress_path, scene_path, zid, png, layout_path=None, px=0.5):
    from PIL import Image, ImageDraw
    sc = SG.Scene.load(scene_path)
    z = sc.zones[zid]
    d = json.load(open(dress_path))[zid]
    x0, y0, x1, y1 = z.bbox()
    m = 140
    W, H = int((x1 - x0) * px) + 2 * m, int((y1 - y0) * px) + 2 * m
    im = Image.new('RGB', (W, H), (24, 24, 28))
    g = ImageDraw.Draw(im)
    P = lambda x, y: (m + (x - x0) * px, H - m - (y - y0) * px)
    for b in z.boxes:
        g.rectangle([P(b[0], b[3]), P(b[2], b[1])], outline=(200, 200, 200), fill=(48, 48, 54))
    for f in z.flights:
        r = f.rect
        g.rectangle([P(r[0], r[3]), P(r[2], r[1])], outline=(120, 120, 220))
    for s in d['solids']:
        if 'rect' in s:
            r = s['rect']; g.rectangle([P(r[0], r[3]), P(r[2], r[1])], fill=(110, 90, 70), outline=(160, 140, 110))
        else:
            q = s['quad']; g.line([P(q[0][0], q[0][1]), P(q[1][0], q[1][1])], fill=(250, 220, 60), width=3)
    for p in d['props']:
        b = p.get('clip_box')
        x, y = p['at']
        if b:
            g.rectangle([P(b[0], b[4]), P(b[3], b[1])], outline=(230, 90, 70))
        g.ellipse([P(x - 4, y + 4), P(x + 4, y - 4)], fill=(220, 220, 120))
    for l in d['lights']:
        x, y = l['at']; r = float(l.get('radius', 200)) * 0.25
        g.ellipse([P(x - r, y + r), P(x + r, y - r)], outline=tuple(int(255 * min(1, c)) for c in l.get('color', [1, 1, 1])))
    if layout_path:
        lay = json.load(open(layout_path))
        for s in lay.get('spawners', []):
            if s.get('zone') == zid:
                x, y = s['origin'][:2]; g.rectangle([P(x - 6, y + 6), P(x + 6, y - 6)], outline=(80, 220, 80))
        for it in lay.get('interactions', []) + lay.get('markers', []):
            if it.get('zone') == zid and it.get('origin'):
                x, y = it['origin'][:2]; g.ellipse([P(x - 14, y + 14), P(x + 14, y - 14)], outline=(80, 200, 255), width=2)
        for o in sc.openings():
            sc.locate(o)
            if zid in o['zones']:
                pl = o['planes'][zid]
                a, b_ = o['span']
                pts = [P(a, pl), P(b_, pl)] if o['axis'] == 'x' else [P(pl, a), P(pl, b_)]
                g.line(pts, fill=(255, 60, 255), width=5)
    g.text((10, 10), '%s: %d props, %d lights, %d solids/panels' % (zid, len(d['props']), len(d['lights']), len(d['solids'])), fill=(255, 255, 255))
    im.save(png)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('build'); p.add_argument('spec'); p.add_argument('scene'); p.add_argument('--db', required=True)
    p.add_argument('--out', required=True); p.add_argument('--layout'); p.add_argument('--report')
    p = sub.add_parser('plan'); p.add_argument('dress'); p.add_argument('scene'); p.add_argument('--db')
    p.add_argument('--zone', required=True); p.add_argument('--png', required=True); p.add_argument('--layout'); p.add_argument('--px', type=float, default=0.5)
    p = sub.add_parser('report'); p.add_argument('dress')
    a = ap.parse_args(argv)
    if a.cmd == 'build':
        try:
            r = build(a.spec, a.scene, a.db, a.out, a.layout, a.report)
        except (DressError, SG.SceneError) as e:
            print('ERROR', e); return 2
        for zid, z in r['zones'].items():
            print('%-15s props %4d / %s  distinct %3d  clipped %3d  lights %3d  solids+panels %3d' % (
                zid, z['props'], z['budget'], z['distinct_models'], z['clipped'], z['lights'], z['solids'] + z['panels']))
        for e in r['errors']:
            print('ERROR', e)
        print('total props %d, %d errors' % (r['total_props'], len(r['errors'])))
        return 1 if r['errors'] else 0
    if a.cmd == 'plan':
        plan(a.dress, a.scene, a.zone, a.png, a.layout, a.px); return 0
    if a.cmd == 'report':
        d = json.load(open(a.dress))
        for zid, z in d.items():
            print(zid, len(z['props']), 'props', len(z['lights']), 'lights', len(z['solids']), 'solids/panels')
        return 0


if __name__ == '__main__':
    sys.exit(main())
