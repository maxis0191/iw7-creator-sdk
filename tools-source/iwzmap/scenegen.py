"""scenegen: a generated IW7 zombies map from a scene description (zones, heights, doors, flights, spawners and
interactions as data).

The scene is a JSON file (format: docs/SCENEGEN.md). This module checks it, emits the compiler sources from it and
reads the emit back:

  python -I -B scenegen.py check   <scene.json>                       scene rules, no output (exit 1 on an error)
  python -I -B scenegen.py emit    <scene.json> <cp_zmb dump> <out>   check, then world.bin, colmap.hkx, navgraph.bin,
                                                                      ents.txt, triggers.txt, scriptables.txt,
                                                                      lighting.txt, probes.txt, layout.json, plan.json,
                                                                      cp_iwz.gsc, custom_materials.json, scene_report.json
  python -I -B scenegen.py flights <out>                              navigation against the collision surface along
                                                                      every flight (fail over 6 units)
  python -I -B scenegen.py routes  <out> [--speed 190] [--md f.md]    walking-time table between zones (doors open)
  python -I -B scenegen.py pools   <out> <cp_zmb dump>                template pools and entities used by the emit

Rules the scene must obey (each one is a check): axis-aligned boxes; boxes of different zones never overlap in plan
(the navigation grid holds one height per 32-unit cell), so levels are terraces joined by flights; a door or a link
joins two zones whose boxes share an edge (wall gap 0 to 16) along the whole opening; the sill of an opening is the
floor height on both sides; a flight is in the stock stair construction (risers of about 8, treads 15 to 20, a
player and monster clip sheet over the nosings, navigation on the sheet) and its ends land on floors of its end
heights; every zone that is not a far box is reachable from the start zone through doors and links; spawn volumes do
not overlap; every requested spawner finds a place on flat navigation at least 48 from a wall.
"""
import argparse, collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CELL = 32
WALL = 16            # largest wall gap between two zones that share an edge
MARGIN = 24          # navigation keeps this far from a wall (cells on both sides of a wall never share an edge)
PORTAL = 24          # an opening's navigation reaches this far past each wall plane (= MARGIN: no cell is left between)
PORTAL_FLAT = 40     # a flight end at an opening is level this far (the portal cells reach PORTAL + half a cell)
RISE = 8.0           # stock riser height
TREAD = (14.5, 20.0)  # accepted tread depth (a 32-unit nav cell on the slope then steps at most 17.7 of the 18 allowed)
NAV_LIFT = 2.0       # navigation above the clip sheet / floor
HEAD = 96            # least headroom over any walkable point
TAG_SOLID = 382
# Stock stair surface tags (clip sheet 411, riser 387, tread 402) put several surface runs in one collision section. They
# are off by default (one solid tag, as the old map's passing stairs had). The first 19-zone build with them crashed the
# dedicated server in Havok geometry code (sub_1410AD7F0, from sub_14100D000); the build without them crashed the same way
# (W1a runs hl-a and hl-b, 11 Nov 2026), so the tags are not the cause; the crash is open. IWZ_STAIR_TAGS=stock: A/B.
if os.environ.get('IWZ_STAIR_TAGS') == 'stock':
    TAG_STAIR_CLIP, TAG_RISER, TAG_TREAD = 411, 387, 402
else:
    TAG_STAIR_CLIP = TAG_RISER = TAG_TREAD = None
LM = (0.8018, 0.5645)  # a lit texel of the template lightmap (neutral)
SIDES = ('south', 'north', 'west', 'east')


class SceneError(Exception):
    pass


# =========================================================================== geometry helpers
def rect_area(r):
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def rect_inter(a, b):
    r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    return r if r[2] > r[0] and r[3] > r[1] else None


def rect_minus(r, holes):
    """r minus the holes, as a short list of rectangles (coordinate compression, then row merge)."""
    hs = [h for h in (rect_inter(r, h) for h in holes) if h]
    if not hs:
        return [tuple(r)]
    xs = sorted({r[0], r[2]} | {h[0] for h in hs} | {h[2] for h in hs})
    ys = sorted({r[1], r[3]} | {h[1] for h in hs} | {h[3] for h in hs})
    out = []
    for j in range(len(ys) - 1):
        run = None
        for i in range(len(xs) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            free = not any(h[0] <= cx <= h[2] and h[1] <= cy <= h[3] for h in hs)
            if free:
                run = [xs[i] if run is None else run[0], ys[j], xs[i + 1], ys[j + 1]]
            elif run:
                out.append(tuple(run)); run = None
        if run:
            out.append(tuple(run))
    # vertical merge of identical x spans
    merged = []
    for r_ in sorted(out, key=lambda q: (q[0], q[2], q[1])):
        if merged and merged[-1][0] == r_[0] and merged[-1][2] == r_[2] and abs(merged[-1][3] - r_[1]) < 1e-6:
            merged[-1] = (r_[0], merged[-1][1], r_[2], r_[3])
        else:
            merged.append(r_)
    return merged


def inside_union(r, boxes):
    return not rect_minus(r, boxes)


def spans_minus(s0, s1, holes):
    out, cur = [], s0
    for a, b in sorted(holes):
        a, b = max(a, s0), min(b, s1)
        if b <= a:
            continue
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if cur < s1:
        out.append((cur, s1))
    return out


def shared_edge(a, b, gap=WALL):
    """(axis, plane_a, plane_b, lo, hi) when boxes a and b face each other across a gap of 0..gap; axis 'x' means
    the wall runs along x (plane y = const), 'y' means it runs along y (plane x = const)."""
    for (ka, kb, ax) in ((2, 0, 'y'), (0, 2, 'y'), (3, 1, 'x'), (1, 3, 'x')):
        pa, pb = a[ka], b[kb]
        d = pb - pa if ka in (2, 3) else pa - pb
        if -0.5 <= d <= gap + 0.5:
            lo, hi = (max(a[1], b[1]), min(a[3], b[3])) if ax == 'y' else (max(a[0], b[0]), min(a[2], b[2]))
            if hi > lo:
                return ax, pa, pb, lo, hi
    return None


# =========================================================================== the scene
class Flight:
    def __init__(self, zone, d):
        self.zone, self.id = zone, d['id']
        self.rect = tuple(float(v) for v in d['rect'])
        self.up = d['up']
        if self.up not in ('+x', '-x', '+y', '-y'):
            raise SceneError('flight %s: up must be +x, -x, +y or -y' % self.id)
        self.axis = self.up[1]
        self.z_lo, self.z_hi = float(d['z_lo']), float(d['z_hi'])
        x0, y0, x1, y1 = self.rect
        if self.axis == 'x':
            self.lo_end, self.hi_end = (x0, x1) if self.up[0] == '+' else (x1, x0)
            self.c0, self.c1 = y0, y1
        else:
            self.lo_end, self.hi_end = (y0, y1) if self.up[0] == '+' else (y1, y0)
            self.c0, self.c1 = x0, x1
        self.d = 1 if self.hi_end > self.lo_end else -1
        self.land_lo = float(d.get('land_lo', 56)); self.land_hi = float(d.get('land_hi', 32))
        self.n = max(1, int(round((self.z_hi - self.z_lo) / RISE)))
        self.rise = (self.z_hi - self.z_lo) / self.n
        length = abs(self.hi_end - self.lo_end)
        self.run = (length - self.land_lo - self.land_hi) / self.n
        self.s_a = self.lo_end + self.d * self.land_lo
        self.s_b = self.hi_end - self.d * self.land_hi
        self.r0, self.r1 = self.s_a - self.d * self.run, self.s_b - self.d * self.run

    def line(self, s):
        """height of the clip sheet (nosing line) at s along the flight"""
        t = (s - self.r0) / (self.r1 - self.r0) if abs(self.r1 - self.r0) > 1e-9 else 1.0
        return self.z_lo + max(0.0, min(1.0, t)) * (self.z_hi - self.z_lo)

    def z_at(self, x, y):
        return self.line(x if self.axis == 'x' else y)

    def flat_at_lo(self):
        return abs(self.r0 - self.lo_end)

    def flat_at_hi(self):
        return abs(self.hi_end - self.r1)

    def P(self, s, c, z):
        return (s, c, z) if self.axis == 'x' else (c, s, z)


class Zone:
    def __init__(self, d):
        self.d = d
        self.id = d['id']
        self.name = d.get('name', self.id)
        self.boxes = [tuple(float(v) for v in b) for b in d['boxes']]
        self.floor = float(d['floor'])
        self.ceiling = float(d['ceiling'])
        self.style = d.get('style', 'plain')
        self.floor_mat = d.get('floor_mat', 'conc_floor')
        self.ceil_mat = d.get('ceil_mat', 'conc_painted')
        self.far = bool(d.get('far'))
        self.areas = [dict(a, rect=tuple(float(v) for v in a['rect'])) for a in d.get('areas', [])]
        self.flights = [Flight(self.id, f) for f in d.get('flights', [])]
        self.solids = [dict(s, rect=tuple(float(v) for v in s['rect'])) for s in d.get('solids', [])]
        self.enclosures = [dict(e, rect=tuple(float(v) for v in e['rect'])) for e in d.get('enclosures', [])]
        self.props = d.get('props', [])       # {model, at [x, y], z (default the floor), yaw, pitch, roll, static, clip [hx, hy, hz]}
        self.spawners = d.get('spawners', {})
        self.plate = bool(d.get('plate', not self.far))
        self.probe = tuple(d.get('probe', (0.9, 0.9, 0.95, 0.6)))
        self.volumes = d.get('volumes')

    def bbox(self):
        return (min(b[0] for b in self.boxes), min(b[1] for b in self.boxes), max(b[2] for b in self.boxes), max(b[3] for b in self.boxes))

    def zmin(self):
        return min([self.floor] + [a['z'] for a in self.areas] + [f.z_lo for f in self.flights])

    def zmax(self):
        return max([self.floor] + [a['z'] for a in self.areas] + [f.z_hi for f in self.flights])

    def inside(self, x, y, pad=0.0):
        return any(b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad for b in self.boxes)

    def floor_at(self, x, y):
        """walkable height at (x, y) inside this zone: flight sheet, area, else the zone floor; None outside"""
        for f in self.flights:
            r = f.rect
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                return f.z_at(x, y)
        for a in self.areas:
            r = a['rect']
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                return float(a['z'])
        if self.inside(x, y):
            return self.floor
        return None

    def base_pieces(self):
        holes = [a['rect'] for a in self.areas] + [f.rect for f in self.flights]
        out = []
        for b in self.boxes:
            out += rect_minus(b, holes)
        return out

    def floor_pieces(self):
        """(rect, z, kind) of every flat floor of the zone"""
        return [(r, self.floor, 'base') for r in self.base_pieces()] + [(a['rect'], float(a['z']), 'area:' + a['id']) for a in self.areas]


class Scene:
    def __init__(self, d, path=''):
        self.d, self.path = d, path
        self.map = d.get('map', 'cp_iwz')
        self.zones = collections.OrderedDict()
        # props kept in their own files ({zone: [props]}, next to the scene): added to the zones' own props
        extra = collections.defaultdict(list)
        for pf in d.get('props_files', []):
            with open(os.path.join(os.path.dirname(os.path.abspath(path)) if path else '.', pf), encoding='utf-8') as f:
                for zid, items in json.load(f).items():
                    extra[zid] += items
        for zd in d['zones']:
            if extra.get(zd['id']):
                zd = dict(zd, props=list(zd.get('props', [])) + extra[zd['id']])
            z = Zone(zd)
            if z.id in self.zones:
                raise SceneError('zone %s defined twice' % z.id)
            self.zones[z.id] = z
        self.doors = d.get('doors', [])
        self.links = d.get('links', [])
        self.start_zone = d['start']['zone']
        self.starts = d['start'].get('points', [])
        self.interactions = d.get('interactions', [])
        self.markers = d.get('markers', [])

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path, encoding='utf-8')), path)

    def openings(self):
        """every opening of every door and link: dict(id, door, kind, zones, price, axis, planes, span, sill, top)"""
        out = []
        for kind_, items in (('door', self.doors), ('link', self.links)):
            for it in items:
                za, zb = it['zones']
                ops = it.get('openings') or [{k: it[k] for k in ('span', 'sill', 'height') if k in it}]
                for k, op in enumerate(ops):
                    o = {'id': it['id'] + ('' if len(ops) == 1 else '_%d' % (k + 1)), 'door': it['id'], 'zones': (za, zb),
                         'kind': 'door' if kind_ == 'door' else it.get('kind', 'arch'), 'price': it.get('price'),
                         'span': tuple(float(v) for v in op['span']), 'sill': float(op['sill']),
                         'height': float(op.get('height', 224))}
                    o['top'] = o['sill'] + o['height']
                    out.append(o)
        return out

    def locate(self, o):
        """the shared edge of an opening: fills axis, planes {zone: plane}, facing {zone: inward sign}, overlap"""
        za, zb = self.zones.get(o['zones'][0]), self.zones.get(o['zones'][1])
        if za is None or zb is None:
            raise SceneError('%s: unknown zone %s' % (o['id'], o['zones'][0] if za is None else o['zones'][1]))
        s0, s1 = o['span']
        for ba in za.boxes:
            for bb in zb.boxes:
                e = shared_edge(ba, bb)
                if not e:
                    continue
                ax, pa, pb, lo, hi = e
                if s0 >= lo - 0.5 and s1 <= hi + 0.5:
                    k = 0 if ax == 'y' else 1          # the coordinate across the wall
                    fa = 1 if (ba[k] + ba[k + 2]) / 2 > pa else -1
                    o.update(axis=ax, planes={za.id: pa, zb.id: pb}, overlap=(lo, hi), facing={za.id: fa, zb.id: -fa})
                    return o
        raise SceneError('%s: zones %s and %s do not share an edge along the opening %g..%g (doors only between rooms '
                         'that share an edge)' % (o['id'], za.id, zb.id, s0, s1))


# =========================================================================== checks on the scene (no output)
def check_scene(sc):
    """list of (severity, message); ERROR stops an emit"""
    out = []

    def err(m):
        out.append(('ERROR', m))

    def note(m):
        out.append(('NOTE', m))
    zl = list(sc.zones.values())
    for z in zl:
        for b in z.boxes:
            if not (b[2] > b[0] and b[3] > b[1]):
                err('zone %s: empty box %s' % (z.id, b))
        for i, a in enumerate(z.boxes):
            for b in z.boxes[i + 1:]:
                if rect_inter(a, b):
                    err('zone %s: boxes %s and %s overlap (boxes of one zone may only touch)' % (z.id, a, b))
        if z.ceiling - z.zmax() < HEAD:
            err('zone %s: ceiling %g leaves %g over the highest floor %g (at least %d)' % (z.id, z.ceiling, z.ceiling - z.zmax(), z.zmax(), HEAD))
        parts = [('area ' + a['id'], a['rect']) for a in z.areas] + [('flight ' + f.id, f.rect) for f in z.flights] + \
                [('solid %d' % k, s['rect']) for k, s in enumerate(z.solids)] + [('enclosure ' + e['id'], e['rect']) for e in z.enclosures]
        for n_, r in parts:
            if not inside_union(r, z.boxes):
                err('zone %s: %s %s lies outside the zone boxes' % (z.id, n_, r))
        flatparts = [p for p in parts if p[0].startswith(('area', 'flight'))]
        for i, (na, ra) in enumerate(flatparts):
            for nb, rb in flatparts[i + 1:]:
                if rect_inter(ra, rb):
                    err('zone %s: %s and %s overlap' % (z.id, na, nb))
        for k, pr in enumerate(z.props):
            x, y = pr['at'][0], pr['at'][1]
            if z.floor_at(x, y) is None and 'z' not in pr:
                err('zone %s: prop %d (%s) at (%g, %g) is outside the zone' % (z.id, k, pr.get('model'), x, y))
        for f in z.flights:
            if abs(f.rise - RISE) > 2.0:
                err('flight %s: riser %.1f (stock about 8)' % (f.id, f.rise))
            if not (TREAD[0] - 1e-6 <= f.run <= TREAD[1] + 1e-6):
                err('flight %s: tread %.1f outside %g..%g (%d risers over %g, landings %g + %g)' % (
                    f.id, f.run, TREAD[0], TREAD[1], f.n, abs(f.hi_end - f.lo_end), f.land_lo, f.land_hi))
            if f.land_lo < f.run:
                err('flight %s: low landing %g shorter than a tread %.1f' % (f.id, f.land_lo, f.run))
            if f.c1 - f.c0 < 96:
                err('flight %s: %g wide (at least 96)' % (f.id, f.c1 - f.c0))
    # plan overlap between zones: no zone above another
    for i, a in enumerate(zl):
        for b in zl[i + 1:]:
            for ra in a.boxes:
                for rb in b.boxes:
                    r = rect_inter(ra, rb)
                    if r:
                        err('zones %s and %s overlap in plan over %s (one height per navigation cell: build terraces side by side)' % (a.id, b.id, r))
    # openings
    ops = []
    for o in sc.openings():
        try:
            sc.locate(o)
        except SceneError as e:
            err(str(e)); continue
        ops.append(o)
        s0, s1 = o['span']
        if s1 - s0 < 96:
            err('%s: opening %g wide (at least 96)' % (o['id'], s1 - s0))
        mid = (s0 + s1) / 2
        for zid in o['zones']:
            z = sc.zones[zid]
            p, f = o['planes'][zid], o['facing'][zid]
            pt = (p + f * 8, mid) if o['axis'] == 'y' else (mid, p + f * 8)
            fz = z.floor_at(*pt)
            if fz is None or abs(fz - o['sill']) > 0.6:
                err('%s: sill %g but the floor of %s beside it is %s (the sill must be the floor on both sides)' % (o['id'], o['sill'], zid, fz))
            if o['top'] > z.ceiling:
                err('%s: opening top %g above the ceiling of %s (%g)' % (o['id'], o['top'], zid, z.ceiling))
    # flight ends
    for z in zl:
        for f in z.flights:
            for end, zz, flat in ((f.lo_end, f.z_lo, f.flat_at_lo()), (f.hi_end, f.z_hi, f.flat_at_hi())):
                out_d = -f.d if end == f.lo_end else f.d
                cm = (f.c0 + f.c1) / 2
                x, y = f.P(end + out_d * 8, cm, 0)[:2]
                fz = z.floor_at(x, y)
                if fz is not None and not any(f.rect[0] <= x <= f.rect[2] and f.rect[1] <= y <= f.rect[3] for f in z.flights):
                    if abs(fz - zz) > 0.6:
                        err('flight %s: end at %g lands on floor %g, not %g' % (f.id, end, fz, zz))
                    continue
                # the end is on the zone wall: it must be an opening with that sill
                hit = None
                for o in ops:
                    if z.id in o['zones'] and o['axis'] == ('y' if f.axis == 'x' else 'x') and abs(o['planes'][z.id] - end) < 0.6 \
                            and o['span'][0] < f.c1 and o['span'][1] > f.c0:
                        hit = o
                if hit is None:
                    if fz is None:
                        err('flight %s: end at %g runs into a wall with no opening' % (f.id, end))
                    continue
                if abs(hit['sill'] - zz) > 0.6:
                    err('flight %s: end at %g meets opening %s with sill %g, not %g' % (f.id, end, hit['id'], hit['sill'], zz))
                if flat < PORTAL_FLAT - 0.5:
                    err('flight %s: the flat part at its %s end is %.1f long; an opening needs %d (raise the landing)' % (
                        f.id, 'low' if end == f.lo_end else 'high', flat, PORTAL_FLAT))
    # reachability over doors and links
    g = collections.defaultdict(set)
    for o in ops:
        a, b = o['zones']
        g[a].add(b); g[b].add(a)
    if sc.start_zone not in sc.zones:
        err('start zone %s does not exist' % sc.start_zone)
    else:
        seen, todo = {sc.start_zone}, [sc.start_zone]
        while todo:
            for n in g[todo.pop()]:
                if n not in seen:
                    seen.add(n); todo.append(n)
        for z in zl:
            if not z.far and z.id not in seen:
                err('zone %s is not reachable from %s through doors and links' % (z.id, sc.start_zone))
            if z.far and z.id in seen:
                note('far zone %s is joined to the map by a door or link' % z.id)
    # interactions
    for it in sc.interactions + sc.markers:
        if it.get('zone') not in sc.zones:
            err('%s %s: unknown zone %s' % (it.get('kind'), it.get('id', ''), it.get('zone')))
    ids = collections.Counter([d['id'] for d in sc.doors + sc.links] + [z.id for z in zl])
    for k, v in ids.items():
        if v > 1:
            err('id %s used %d times' % (k, v))
    doors = [d for d in sc.doors]
    note('%d zones (%d far), %d doors for %d points, %d links, %d flights' % (
        len(zl), sum(1 for z in zl if z.far), len(doors), sum(int(d.get('price', 0)) for d in doors), len(sc.links),
        sum(len(z.flights) for z in zl)))
    return out


# =========================================================================== emit
STYLE_BANDS = {
    'metro': [(10, 'rubber_trim'), (102, 'tile_charcoal'), (8, 'steel_trim'), (None, 'tile_white')],
    'metro_cream': [(10, 'rubber_trim'), (102, 'tile_green'), (8, 'steel_trim'), (None, 'tile_cream')],
    'maint': [(10, 'rubber_trim'), (86, 'panel_dark'), (6, 'beam_yellow'), (None, 'conc_seam')],
    'old': [(10, 'wood_trim'), (94, 'wood_green'), (8, 'wood_trim'), (None, 'brick_white')],
    'tunnel': [(96, 'conc_dark'), (4, 'steel_trim'), (None, 'conc_seam')],
    'control': [(10, 'rubber_trim'), (86, 'panel_dark'), (8, 'steel_trim'), (None, 'panel_wall')],
    'brick': [(None, 'brick_gray')],
    'plain': [(None, 'conc_wall')],
    'drywall': [(10, 'rubber_trim'), (None, 'drywall_gray')],
    'plaster': [(10, 'wood_trim'), (None, 'plaster_green')],
}


def bands(style, zf, zc, zmin):
    out = []
    if zmin < zf - 0.5:
        out.append((zmin, zf, 'conc_dark'))
    z = zf
    for h, mat in STYLE_BANDS.get(style, STYLE_BANDS['plain']):
        z1 = zc if h is None else min(zc, z + h)
        if z1 > z:
            out.append((z, z1, mat))
        z = z1
    if z < zc:
        out.append((z, zc, out[-1][2] if out else 'conc_wall'))
    return out


class Emitter:
    def __init__(self, sc, tpl, out, log=print):
        import mapgen, hkcm_write, brushkit as bk, sz2_materials as MT
        self.mapgen, self.hk, self.bk, self.MT = mapgen, hkcm_write, bk, MT
        self.sc, self.tpl, self.out, self.log = sc, tpl, out, log
        self.B = bk.Builder(MT.MATERIALS, lambda zone, tone: LM)
        self.regions = []
        self.stairs = []
        self.ents, self.triggers, self.relocations = [], [], []
        self.layout = {'map': sc.map, 'scene': os.path.basename(sc.path), 'zones': {}, 'doors': [], 'spawners': [], 'starts': [],
                       'interactions': [], 'markers': [], 'stairs': self.stairs}
        self.report = {'schema': 'iw7.scenegen/1'}
        self.smodels, self.prop_ents = [], []

    # ---------------------------------------------------------------- render helpers
    def quad(self, mat, zone, pts, n, collide=True):
        self.B.quad(mat, zone, pts, n=n, collide=collide)

    def floor_quad(self, zone, mat, r, z, collide=True):
        x0, y0, x1, y1 = r
        self.quad(mat, zone, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, 1), collide)

    def ceil_quad(self, zone, mat, r, z):
        x0, y0, x1, y1 = r
        self.quad(mat, zone, [(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)], (0, 0, -1), True)

    def vquad(self, zone, mat, axis, fixed, facing, s0, s1, z0, z1, collide=True, both=False):
        if s1 - s0 < 0.01 or z1 - z0 < 0.01:
            return
        self.B.wall_plane(zone, axis, fixed, facing, s0, s1, z0, z1, mat, collide=collide)
        if both:
            self.B.wall_plane(zone, axis, fixed, -facing, s0, s1, z0, z1, mat, collide=collide)

    def sloped(self, zone, mat, axis, fixed, facing, s0, s1, za0, za1, zb0, zb1, both=True):
        """vertical quad, bottom za0 -> za1 and top zb0 -> zb1 from s0 to s1; both faces render and collide"""
        if s1 - s0 < 0.01:
            return
        for fc in ((facing, -facing) if both else (facing,)):
            self.B.wall_sloped(zone, axis, fixed, fc, s0, s1, za0, za1, zb0, zb1, mat, collide=True)

    # ---------------------------------------------------------------- zone shell
    def zone_openings(self, z):
        """openings on this zone's walls: (axis, plane, s0, s1, sill, top, kind)"""
        return [(o['axis'], o['planes'][z.id], o['span'][0], o['span'][1], o['sill'], o['top'], o['kind'])
                for o in self.ops if z.id in o['zones']]

    def wall_segments(self, z):
        """outer wall segments of a zone: (axis, fixed, facing, s0, s1), interior joins between its boxes removed"""
        segs = []
        for i, b in enumerate(z.boxes):
            x0, y0, x1, y1 = b
            for side, ax, fixed, facing, s0, s1 in (('south', 'x', y0, 1, x0, x1), ('north', 'x', y1, -1, x0, x1),
                                                     ('west', 'y', x0, 1, y0, y1), ('east', 'y', x1, -1, y0, y1)):
                cut = []
                for j, o in enumerate(z.boxes):
                    if j == i:
                        continue
                    if side == 'south' and abs(o[3] - y0) < 0.5: cut.append((o[0], o[2]))
                    if side == 'north' and abs(o[1] - y1) < 0.5: cut.append((o[0], o[2]))
                    if side == 'west' and abs(o[2] - x0) < 0.5: cut.append((o[1], o[3]))
                    if side == 'east' and abs(o[0] - x1) < 0.5: cut.append((o[1], o[3]))
                for a, c in spans_minus(s0, s1, cut):
                    segs.append((ax, fixed, facing, a, c))
        return segs

    def build_shell(self, z):
        zf, zc, zmin = z.floor, z.ceiling, z.zmin()
        ops = self.zone_openings(z)
        bl = bands(z.style, zf, zc, zmin)
        for ax, fixed, facing, s0, s1 in self.wall_segments(z):
            here = [o for o in ops if o[0] == ax and abs(o[1] - fixed) < 0.5 and o[2] < s1 and o[3] > s0]
            full = [(o[2], o[3]) for o in here if o[6] == 'open']
            holes = [o for o in here if o[6] != 'open']
            for za, zb, mat in bl:
                pieces = [(p, q, za, zb) for p, q in spans_minus(s0, s1, full + [(o[2], o[3]) for o in holes if o[4] < zb and o[5] > za])]
                for o in holes:
                    a, b = max(o[2], s0), min(o[3], s1)
                    if o[4] < zb and o[5] > za:
                        if o[5] < zb:
                            pieces.append((a, b, max(za, o[5]), zb))
                        if o[4] > za:
                            pieces.append((a, b, za, min(zb, o[4])))
                for p, q, z0, z1 in pieces:
                    self.vquad(z.id, mat, ax, fixed, facing, p, q, z0, z1)
            for o in holes:      # a steel frame round doors and arches
                a, b, top = o[2], o[3], o[5]
                slab = self.B.slab_x if ax == 'x' else self.B.slab_y
                fm = 'frame' if o[6] == 'door' else 'steel_trim'
                slab(a - 10, a, fixed, o[4], top + 10, 4, fm, z.id, facing, collide=False, nav=False)
                slab(b, b + 10, fixed, o[4], top + 10, 4, fm, z.id, facing, collide=False, nav=False)
                slab(a, b, fixed, top, top + 10, 4, fm, z.id, facing, collide=False, nav=False)
        for r, zz, kind in z.floor_pieces():
            self.floor_quad(z.id, z.floor_mat if kind == 'base' else z.d.get('area_mat', 'conc_floor_gray'), r, zz)
        for b in z.boxes:
            self.ceil_quad(z.id, z.ceil_mat, b, zc)
        # drop faces where two flat floors of the zone meet at different heights
        fp = z.floor_pieces()
        for i, (ra, za_, _ka) in enumerate(fp):
            for rb, zb_, _kb in fp[i + 1:]:
                if abs(za_ - zb_) < 0.5:
                    continue
                e = shared_edge(ra, rb, gap=0.0)
                if not e:
                    continue
                ax, pa, _pb, lo, hi = e
                lo_r = ra if za_ < zb_ else rb
                # facing: toward the lower piece
                if ax == 'y':
                    facing = 1 if lo_r[0] >= pa - 0.5 else -1
                else:
                    facing = 1 if lo_r[1] >= pa - 0.5 else -1
                self.vquad(z.id, 'conc_dark', ax, pa, facing, lo, hi, min(za_, zb_), max(za_, zb_))
        for s in z.solids:
            x0, y0, x1, y1 = s['rect']
            self.B.box((x0, y0, float(s.get('z0', z.zmin()))), (x1, y1, float(s.get('z1', z.ceiling))), s.get('mat', 'conc_wall'), z.id)
        for e in z.enclosures:
            self.build_enclosure(z, e)
        for pr in z.props:
            x, y = float(pr['at'][0]), float(pr['at'][1])
            zz = float(pr['z']) if 'z' in pr else z.floor_at(x, y)
            ang = (float(pr.get('pitch', 0)), float(pr.get('yaw', 0)), float(pr.get('roll', 0)))
            if pr.get('static', True):
                self.smodels.append('%s %g %g %g %g %g %g %g' % (pr['model'], x, y, zz, ang[0], ang[1], ang[2], float(pr.get('scale', 1))))
            else:
                self.prop_ents.append((pr['model'], (x, y, zz), ang, pr.get('targetname')))
            if pr.get('clip'):
                hx, hy, hz = (float(v) for v in pr['clip'])
                self.B.collision_box((x - hx, y - hy, zz), (x + hx, y + hy, zz + 2 * hz))
            self.layout.setdefault('decor', []).append({'zone': z.id, 'model': pr['model'], 'origin': [x, y, zz], 'yaw': ang[1],
                                                        'clip': pr.get('clip'), 'static': pr.get('static', True)})
        for f in z.flights:
            self.build_flight(z, f)

    def reveal(self, o):
        """the opening through a wall gap: floor, jambs and soffit (doors and arches); nothing for a zero gap"""
        za, zb = o['zones']
        p0, p1 = sorted((o['planes'][za], o['planes'][zb]))
        if p1 - p0 < 0.5:
            return
        a, b, z0, z1 = o['span'][0], o['span'][1], o['sill'], o['top']
        if o['axis'] == 'x':
            self.floor_quad(za, 'conc_floor', (a, p0, b, p1), z0)
            self.ceil_quad(za, 'conc_painted', (a, p0, b, p1), z1)
            self.vquad(za, 'conc_painted', 'y', a, 1, p0, p1, z0, z1)
            self.vquad(za, 'conc_painted', 'y', b, -1, p0, p1, z0, z1)
        else:
            self.floor_quad(za, 'conc_floor', (p0, a, p1, b), z0)
            self.ceil_quad(za, 'conc_painted', (p0, a, p1, b), z1)
            self.vquad(za, 'conc_painted', 'x', a, 1, p0, p1, z0, z1)
            self.vquad(za, 'conc_painted', 'x', b, -1, p0, p1, z0, z1)

    def build_enclosure(self, z, e):
        """a box room inside a zone (a car, a booth): four walls with openings, a roof; both faces solid"""
        x0, y0, x1, y1 = e['rect']
        z0, z1 = float(e.get('z0', z.floor)), float(e['z1'])
        mat, roof = e.get('mat', 'metal_silver'), e.get('roof_mat', 'metal_silver')
        op = e.get('openings', {})
        for side, ax, fixed, s0, s1 in (('south', 'x', y0, x0, x1), ('north', 'x', y1, x0, x1), ('west', 'y', x0, y0, y1), ('east', 'y', x1, y0, y1)):
            holes = [(float(h[0]), float(h[1]), float(h[2]) if len(h) > 2 else z1 - 8) for h in op.get(side, [])]
            for p, q in spans_minus(s0, s1, [(h[0], h[1]) for h in holes]):
                self.vquad(z.id, mat, ax, fixed, 1, p, q, z0, z1, both=True)
            for a, b, top in holes:
                self.vquad(z.id, mat, ax, fixed, 1, a, b, top, z1, both=True)
            # navigation: the wall cuts cells beside it except across the openings
            for p, q in spans_minus(s0, s1, [(h[0], h[1]) for h in holes]):
                bx = (p, fixed - 8, q, fixed + 8) if ax == 'x' else (fixed - 8, p, fixed + 8, q)
                self.B.blockers.append((bx[0], bx[1], bx[2], bx[3], z0, z1))
        self.floor_quad(z.id, roof, (x0, y0, x1, y1), z1)
        self.ceil_quad(z.id, roof, (x0, y0, x1, y1), z1 - 0.5)

    # ---------------------------------------------------------------- flights (stock stair construction)
    def build_flight(self, z, f):
        B, zone = self.B, z.id
        n, run, rise, d = f.n, f.run, f.rise, f.d
        P = f.P

        def rect(s0, s1, zz, mat, collide):
            sa, sb = min(s0, s1), max(s0, s1)
            r = (sa, f.c0, sb, f.c1) if f.axis == 'x' else (f.c0, sa, f.c1, sb)
            self.floor_quad(zone, mat, r, zz, collide)
        rect(f.lo_end, f.s_a, f.z_lo, 'conc_floor', False)
        rect(f.s_b, f.hi_end, f.z_hi, 'conc_floor', False)
        nr = (-d, 0, 0) if f.axis == 'x' else (0, -d, 0)
        for k in range(n):
            sk0, sk1 = f.s_a + d * k * run, f.s_a + d * (k + 1) * run
            zt = f.z_lo + (k + 1) * rise
            rect(sk0, sk1, zt, 'stair_tread', False)
            pts = [P(sk0, f.c0, zt - rise), P(sk0, f.c1, zt - rise), P(sk0, f.c1, zt), P(sk0, f.c0, zt)]
            B.quad('conc_floor', zone, pts, n=nr, collide=False)
            # collision under the sheet: solid riser, tread (clipshot / missileclip only, stock)
            B.collision_quad(pts, n=nr, tag=TAG_RISER)
            if k < n - 1:
                tq = [P(sk0, f.c0, zt), P(sk1, f.c0, zt), P(sk1, f.c1, zt), P(sk0, f.c1, zt)]
                B.collision_quad(tq, n=(0, 0, 1), tag=TAG_TREAD)

        def cq(sa, sb, za, zb, tag=None):
            B.collision_quad([P(sa, f.c0, za), P(sb, f.c0, zb), P(sb, f.c1, zb), P(sa, f.c1, za)], n=(0, 0, 1), tag=tag)
        cq(f.lo_end, f.r0, f.z_lo, f.z_lo)
        cq(f.r0, f.r1, f.z_lo, f.z_hi, tag=TAG_STAIR_CLIP)
        cq(f.r1, f.hi_end, f.z_hi, f.z_hi)
        # side faces against the neighbouring floor: trench walls (neighbour higher) or stringers (neighbour lower)
        rails = 0
        for cfix, outward in ((f.c0, -1), (f.c1, 1)):
            nb_axis = 'x' if f.axis == 'x' else 'y'
            lo_s, hi_s = sorted((f.lo_end, f.hi_end))
            s = lo_s
            step = 16.0
            while s < hi_s - 1e-6:
                s2 = min(hi_s, s + step)
                sm = (s + s2) / 2
                px, py = P(sm, cfix + outward * 8, 0)[:2]
                nz = z.floor_at(px, py)
                if nz is not None and not any(g.rect[0] <= px <= g.rect[2] and g.rect[1] <= py <= g.rect[3] for g in z.flights if g is not f):
                    la, lb = f.line(s), f.line(s2)
                    za0, za1 = min(la, nz), min(lb, nz)
                    zb0, zb1 = max(la, nz), max(lb, nz)
                    if zb0 - za0 > 0.3 or zb1 - za1 > 0.3:
                        # side plane is constant (c): axis of the plane quad runs along the flight
                        self.sloped(zone, 'conc_dark', nb_axis, cfix, outward, s, s2, za0, za1, zb0, zb1)
                    if la - nz > 18 or lb - nz > 18:
                        # a drop beside the flight: a guard rail (player and monster clip to 42 over the sheet, a steel cap)
                        for fc in (outward, -outward):
                            B.collision_quad([P(s, cfix, la), P(s2, cfix, lb), P(s2, cfix, lb + 42), P(s, cfix, la + 42)],
                                             n=(0, fc, 0) if f.axis == 'x' else (fc, 0, 0))
                        self.sloped(zone, 'steel_trim', nb_axis, cfix, outward, s, s2, la + 38, lb + 38, la + 42, lb + 42)
                        rails += 1
                s = s2
        self.stairs.append({'zone': zone, 'space': f.id, 'axis': f.axis, 'span': sorted((f.lo_end, f.hi_end)), 'c': [f.c0, f.c1],
                            'z': [f.z_lo, f.z_hi], 'steps': n, 'rise': round(rise, 3), 'tread': round(run, 3),
                            'ramp_from': [f.r0, f.z_lo], 'ramp_to': [f.r1, f.z_hi], 'style': 'stock', 'side_walls': False, 'stringers': [],
                            'rail_segments': rails})

    # ---------------------------------------------------------------- navigation
    def region(self, name, zone, rect, z, margins=(0, 0, 0, 0), kind='flat'):
        self.regions.append({'name': name, 'zone': zone, 'rect': rect, 'z': z, 'm': margins, 'kind': kind})

    def cell_on_floor(self, zobj, i, j, zz):
        """a flat cell lies whole over floor of its own height: no corner hangs over a pit, a step or a flight's slope"""
        for x, y in ((i * CELL + 0.5, j * CELL + 0.5), ((i + 1) * CELL - 0.5, j * CELL + 0.5), ((i + 1) * CELL - 0.5, (j + 1) * CELL - 0.5),
                     (i * CELL + 0.5, (j + 1) * CELL - 0.5)):
            nz = zobj.floor_at(x, y)
            if nz is not None and abs(nz - zz) > 0.5:
                return False
        return True

    def wall_margins(self, z, r, flight=None, zz=None):
        """margins (w, s, e, n) of a region rect: MARGIN where its side lies on a wall of the zone, 16 on a flight's long
        open side, else 0 (cells that would hang over a floor of another height are refused cell by cell in build_nav)"""
        segs = self.wall_segments(z)
        m = []
        for side, ax, fixed, s0, s1, out in (('west', 'y', r[0], r[1], r[3], -1), ('south', 'x', r[1], r[0], r[2], -1),
                                             ('east', 'y', r[2], r[1], r[3], 1), ('north', 'x', r[3], r[0], r[2], 1)):
            on_wall = any(sg[0] == ax and abs(sg[1] - fixed) < 0.5 and sg[3] < s1 and sg[4] > s0 for sg in segs)
            if on_wall:
                m.append(MARGIN)
                continue
            if flight is not None:
                m.append(16 if ax != ('y' if flight.axis == 'x' else 'x') else 0)      # long open sides; ends meet their floors
                continue
            m.append(0)
        return tuple(m)

    def build_nav(self):
        sc = self.sc
        for o in self.ops:
            za, zb = o['zones']
            p0, p1 = sorted((o['planes'][za], o['planes'][zb]))
            a, b = o['span'][0] + 16, o['span'][1] - 16
            r = (a, p0 - PORTAL, b, p1 + PORTAL) if o['axis'] == 'x' else (p0 - PORTAL, a, p1 + PORTAL, b)
            self.region('portal:' + o['id'], za, r, o['sill'], kind='portal')
        for z in sc.zones.values():
            for f in z.flights:
                self.region('flight:' + f.id, z.id, f.rect, (lambda x, y, f=f: f.z_at(x, y) + NAV_LIFT), self.wall_margins(z, f.rect, f), kind='flight')
            for a in z.areas:
                self.region('area:%s:%s' % (z.id, a['id']), z.id, a['rect'], float(a['z']), self.wall_margins(z, a['rect'], zz=float(a['z'])))
            for k, r in enumerate(z.base_pieces()):
                self.region('base:%s:%d' % (z.id, k), z.id, r, z.floor, self.wall_margins(z, r, zz=z.floor))
        cells, owner, corner = {}, {}, {}
        for r in self.regions:
            x0, y0, x1, y1 = r['rect']
            mw, ms, me, mn = r['m']
            for i in range(int(math.floor(x0 / CELL)) - 1, int(math.ceil(x1 / CELL)) + 1):
                for j in range(int(math.floor(y0 / CELL)) - 1, int(math.ceil(y1 / CELL)) + 1):
                    if (i, j) in cells:
                        continue
                    cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
                    if not (x0 + mw <= cx <= x1 - me and y0 + ms <= cy <= y1 - mn):
                        continue
                    zz = r['z'](cx, cy) if callable(r['z']) else r['z']
                    if r['kind'] == 'flat' and not self.cell_on_floor(self.sc.zones[r['zone']], i, j, zz):
                        continue
                    if any(bx0 - 16 < cx < bx1 + 16 and by0 - 16 < cy < by1 + 16 and bz0 < zz + 60 and bz1 > zz + 1
                           for bx0, by0, bx1, by1, bz0, bz1 in self.B.blockers):
                        continue
                    cells[(i, j)] = round(zz, 2)
                    owner[(i, j)] = r['name']
                    if callable(r['z']):
                        corner[(i, j)] = tuple(round(r['z'](x_, y_), 2) for x_, y_ in ((i * CELL, j * CELL), ((i + 1) * CELL, j * CELL),
                                                                                       ((i + 1) * CELL, (j + 1) * CELL), (i * CELL, (j + 1) * CELL)))

        def ecorn(k, e):
            z_ = cells[k]
            c_ = corner.get(k, (z_, z_, z_, z_))
            return {0: (c_[0], c_[1]), 1: (c_[1], c_[2]), 2: (c_[3], c_[2]), 3: (c_[0], c_[3])}[e]
        # seams: the engine joins nav areas whose edges coincide. Every edge-sharing pair must be a real step: one
        # region (edge within 18) or two regions whose shared edge is level (within 2). Otherwise the lower cell goes.
        adj, removed = set(), collections.Counter()
        size = collections.Counter(owner.values())
        for _ in range(6):
            drop = set()
            for k in sorted(cells):
                if k in drop:
                    continue
                for e, nb in ((1, (k[0] + 1, k[1])), (2, (k[0], k[1] + 1))):
                    if nb not in cells or nb in drop:
                        continue
                    ha, hb = ecorn(k, e), ecorn(nb, (e + 2) % 4)
                    same = owner[k] == owner[nb]
                    tol = 18.0 if same else 3.0
                    if abs(ha[0] - hb[0]) <= tol and abs(ha[1] - hb[1]) <= tol and abs(cells[k] - cells[nb]) <= 18.0:
                        if not same:
                            adj.add(frozenset((owner[k], owner[nb])))
                        continue
                    za, zb = sum(ha) / 2, sum(hb) / 2
                    lo = (k if za < zb else nb) if abs(za - zb) > 0.5 else (k if size[owner[k]] >= size[owner[nb]] else nb)
                    drop.add(lo)
                    removed['%s|%s' % tuple(sorted((owner[k], owner[nb])))] += 1
            if not drop:
                break
            for k in drop:
                cells.pop(k, None); owner.pop(k, None); corner.pop(k, None)
        # only links whose pairs survived
        adj = set()
        for k in cells:
            for nb in ((k[0] + 1, k[1]), (k[0], k[1] + 1)):
                if nb in cells and owner[nb] != owner[k]:
                    adj.add(frozenset((owner[k], owner[nb])))
        self.cells, self.owner, self.corner, self.adj = cells, owner, corner, adj
        self.seams_removed = dict(removed)
        nav, nareas = self.mapgen.nav_graph(cells, CELL, lambda a, b: True, corner)
        open(os.path.join(self.out, 'navgraph.bin'), 'wb').write(nav)
        self.report['nav'] = {'cells': len(cells), 'areas': nareas, 'bytes': len(nav), 'seam_cells_removed': sum(removed.values()),
                              'walkable_m2': round(len(cells) * CELL * CELL * 0.0254 ** 2)}

    def zone_of_cell(self, k):
        if not hasattr(self, '_rz'):
            self._rz = {rr['name']: rr['zone'] for rr in self.regions}
        return self._rz.get(self.owner.get(k))

    # ---------------------------------------------------------------- placement
    def cell_z(self, x, y):
        return self.cells.get((int(math.floor(x / CELL)), int(math.floor(y / CELL))))

    def flat_cells(self, z, wall_clear=48.0):
        """cells of zone z on flat floor, every 8-neighbour present and level, at least wall_clear from its walls"""
        segs = self.wall_segments(z)
        own = {r['name'] for r in self.regions if r['zone'] == z.id and r['kind'] in ('flat', 'flight')}   # flight landings count when level
        out = []
        for k, rn in self.owner.items():
            if rn not in own:
                continue
            zz = self.cells[k]
            if not all((k[0] + di, k[1] + dj) in self.cells and abs(self.cells[(k[0] + di, k[1] + dj)] - zz) < 1.0
                       for di in (-1, 0, 1) for dj in (-1, 0, 1)):
                continue
            cx, cy = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
            if not z.inside(cx, cy):
                continue
            if any(self.dist_seg(cx, cy, sg) < wall_clear for sg in segs):
                continue
            out.append(k)
        return sorted(out)

    @staticmethod
    def dist_seg(x, y, sg):
        ax, fixed, _f, s0, s1 = sg
        u, v = (x, y) if ax == 'x' else (y, x)
        du = 0.0 if s0 <= u <= s1 else min(abs(u - s0), abs(u - s1))
        return math.hypot(du, v - fixed)

    @staticmethod
    def farthest(cands, n, taken=(), key=None):
        """deterministic farthest-point sample of n cells from cands, away from the taken points"""
        pts = [((k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL) for k in cands]
        chosen = list(taken)
        res = []
        if not pts or n <= 0:
            return res
        dmin = [min((math.hypot(p[0] - q[0], p[1] - q[1]) for q in chosen), default=1e18) for p in pts]
        if not chosen:
            i0 = min(range(len(pts)), key=lambda i: (pts[i][0] + pts[i][1], pts[i]))
            res.append(cands[i0]); chosen.append(pts[i0])
            dmin = [math.hypot(p[0] - pts[i0][0], p[1] - pts[i0][1]) for p in pts]
        while len(res) < n:
            i = max(range(len(pts)), key=lambda i: (dmin[i], -pts[i][0], -pts[i][1]))
            if dmin[i] < 1.0:
                break
            res.append(cands[i]); chosen.append(pts[i])
            for j, p in enumerate(pts):
                dmin[j] = min(dmin[j], math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]))
        return res

    def place(self, z, it, default_off=40.0):
        """origin (x, y, z) and yaw of a placed thing: 'at' [x, y] or 'wall' side + 's' (or 't' 0..1) + 'off'"""
        if 'at' in it:
            x, y = float(it['at'][0]), float(it['at'][1])
            yaw = float(it.get('yaw', 0))
        else:
            side = it['wall']
            box = z.boxes[int(it.get('box', 0))]
            off = float(it.get('off', default_off))
            x0, y0, x1, y1 = box
            if side in ('south', 'north'):
                s = float(it['s']) if 's' in it else x0 + float(it.get('t', 0.5)) * (x1 - x0)
                x, y, yaw = s, (y0 + off if side == 'south' else y1 - off), (90 if side == 'south' else 270)
            else:
                s = float(it['s']) if 's' in it else y0 + float(it.get('t', 0.5)) * (y1 - y0)
                x, y, yaw = (x0 + off if side == 'west' else x1 - off), s, (0 if side == 'west' else 180)
        fz = z.floor_at(x, y)
        if fz is None:
            raise SceneError('%s in %s: (%g, %g) is outside the zone' % (it.get('kind'), z.id, x, y))
        return (round(x, 2), round(y, 2), round(fz, 2)), yaw

    # ---------------------------------------------------------------- entities
    def ent(self, **kw):
        K = {'classname': '157', 'targetname': '822', 'origin': '543', 'angles': '65', 'noteworthy': '638', 'target': '820',
             'area': '60666', 'parameters': '61049', 'model': '497', 'groupname': '502', 'radius': '599', 'linkname': '636',
             'animation': '60661', 'fxid': '60859', 'spawnflags': '687', 'dummy': '51961', 'f60803': '60803'}
        self.ents.append([(K[k], str(v)) for k, v in kw.items()])

    @staticmethod
    def fmt(p):
        return '%g %g %g' % tuple(round(c, 3) for c in p)

    def volumes(self):
        """spawn volumes: (linkname, zone, box6); explicit ones from the scene, else the zone's bounding box"""
        vols = []
        for z in self.sc.zones.values():
            spec = z.volumes or [list(z.bbox())]
            for k, v in enumerate(spec):
                x0, y0, x1, y1 = v[:4]
                vols.append({'name': z.id if k == 0 else '%s_%d' % (z.id, k + 1), 'zone': z.id,
                             'box': [x0, y0, z.zmin() - 16, x1, y1, z.ceiling + 16]})
        # pad each side toward a neighbour by half the wall gap (at most 8) so no walkable point is in no volume
        allpads = []
        for v in vols:
            b = v['box']
            pads = []
            for side in range(4):
                gap = 16.0
                for w in vols:
                    if w is v:
                        continue
                    c = w['box']
                    if min(b[5], c[5]) - max(b[2], c[2]) <= 0:
                        continue
                    if side == 0 and c[1] < b[4] and c[4] > b[1] and c[3] <= b[0] + 0.5: gap = min(gap, b[0] - c[3])
                    if side == 1 and c[0] < b[3] and c[3] > b[0] and c[4] <= b[1] + 0.5: gap = min(gap, b[1] - c[4])
                    if side == 2 and c[1] < b[4] and c[4] > b[1] and c[0] >= b[3] - 0.5: gap = min(gap, c[0] - b[3])
                    if side == 3 and c[0] < b[3] and c[3] > b[0] and c[1] >= b[4] - 0.5: gap = min(gap, c[1] - b[4])
                pads.append(max(0.0, gap / 2))
            allpads.append(pads)
        for v, pads in zip(vols, allpads):
            b = v['box']
            v['box'] = [b[0] - pads[0], b[1] - pads[1], b[2], b[3] + pads[2], b[4] + pads[3], b[5]]
        for i, v in enumerate(vols):
            for w in vols[i + 1:]:
                b, c = v['box'], w['box']
                if min(b[3], c[3]) - max(b[0], c[0]) > 0.5 and min(b[4], c[4]) - max(b[1], c[1]) > 0.5 and min(b[5], c[5]) - max(b[2], c[2]) > 0.5:
                    self.problems.append('spawn volumes %s and %s overlap' % (v['name'], w['name']))
        return vols

    def emit_entities(self):
        sc, layout = self.sc, self.layout
        mg = self.mapgen
        ws = mg.stock_worldspawn(os.path.join(self.tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'))
        sz = sc.zones[sc.start_zone]
        # player starts: explicit, else four on flat cells of the start zone near its middle
        starts = [tuple(p) for p in sc.starts]
        if not starts:
            fc = self.flat_cells(sz, 96)
            bx = sz.bbox(); mid = ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
            fc.sort(key=lambda k: math.hypot((k[0] + 0.5) * CELL - mid[0], (k[1] + 0.5) * CELL - mid[1]))
            starts = [((k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL, self.cells[k] - NAV_LIFT * 0, 0) for k in fc[:4]]
        for p in starts:
            x, y = p[0], p[1]
            zz = sz.floor_at(x, y)
            self.ent(classname='script_struct', targetname='default_player_start', origin=self.fmt((x, y, zz)), angles='0 %g 0' % (p[3] if len(p) > 3 else 0))
            layout['starts'].append((x, y, zz))
        x, y, zz = layout['starts'][0]
        for k in range(8):
            self.ent(classname='trigger_use', targetname='player_use_trigger', origin=self.fmt((x + 40 * (k - 4), y, zz + 40)),
                     model='?%d' % (4 + k % 4), dummy='triggermodeldummydefault')
        self.ent(classname='mp_global_intermission', origin=self.fmt((x, y, zz + 220)), angles='10 270 0')
        # spawn volumes
        self.vols = self.volumes()
        for k, v in enumerate(self.vols):
            x0, y0, z0, x1, y1, z1 = v['box']
            self.triggers.append('28000001 %g %g %g' % ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
            self.ent(classname='info_volume', targetname='spawn_volume', origin=self.fmt(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)),
                     model='?IWZ%d' % k, linkname=v['name'], target=v['name'] + '_spawner')
            v['ent'] = self.ents[-1]
        for z in sc.zones.values():
            layout['zones'][z.id] = {'name': z.name, 'box': [*z.bbox()[:2], z.zmin() - 16, *z.bbox()[2:], z.ceiling + 16],
                                     'boxes': [list(b) for b in z.boxes], 'floor': z.floor, 'ceiling': z.ceiling, 'far': z.far,
                                     'probe': list(z.probe), 'volumes': [v['name'] for v in self.vols if v['zone'] == z.id]}
        self.place_spawners()
        used = collections.Counter(s['volume'] for s in layout['spawners'])
        for v in self.vols:
            e = v.pop('ent')
            if not used.get(v['name']):
                e[:] = [kv for kv in e if kv[0] != '820']      # a volume with no spawner has no target (lint: scripted-only zone)
            v['spawners'] = used.get(v['name'], 0)
        self.place_doors()
        self.place_interactions()
        # stock systems that run on every map look these up: parked stand-ins
        for tn in ('hidden_room_portal', 'center_portal', 'fast_travel_tube_start', 'fast_travel_tube_end', 'hidden_travel_tube_start',
                   'hidden_travel_tube_end'):
            self.ent(classname='script_model', targetname=tn, model='tag_origin', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='hidden_room_spot', origin='0 0 -3000', angles='0 0 0')
        self.ent(classname='script_struct', targetname='brute_hide_org', origin='0 0 -2000')
        for model, org, ang, tn in self.prop_ents:
            kw = {'targetname': tn} if tn else {}
            self.ent(classname='script_model', model=model, origin=self.fmt(org), angles='%g %g %g' % ang, **kw)
        if self.smodels:
            open(os.path.join(self.out, 'smodels.txt'), 'w', newline='\n').write('\n'.join(self.smodels) + '\n')
        open(os.path.join(self.out, 'ents.txt'), 'w', newline='\n').write(mg.ents_text(ws, self.ents))
        open(os.path.join(self.out, 'triggers.txt'), 'w', newline='\n').write('\n'.join(self.triggers) + '\n')
        open(os.path.join(self.out, 'scriptables.txt'), 'w', newline='\n').write('\n'.join(self.relocations) + ('\n' if self.relocations else ''))

    def vol_of(self, zid, x, y):
        for v in self.vols:
            b = v['box']
            if v['zone'] == zid and b[0] <= x <= b[3] and b[1] <= y <= b[4]:
                return v['name']
        return zid

    def place_spawners(self):
        sc, layout = self.sc, self.layout
        self.problems = getattr(self, 'problems', [])
        plates = []
        for z in sc.zones.values():
            sp = z.spawners
            explicit = sp.get('points', []) if isinstance(sp, dict) else []
            want = {k: int(sp.get(k, 0)) for k in ('ground', 'wall', 'ceiling')} if isinstance(sp, dict) else {}
            avoid = [((o['span'][0] + o['span'][1]) / 2, o['planes'][z.id]) if o['axis'] == 'x' else (o['planes'][z.id], (o['span'][0] + o['span'][1]) / 2)
                     for o in self.ops if z.id in o['zones']]
            flat = [k for k in self.flat_cells(z) if all(math.hypot((k[0] + 0.5) * CELL - a[0], (k[1] + 0.5) * CELL - a[1]) >= 128 for a in avoid)]
            placed = []
            for p in explicit:
                placed.append((p['kind'], float(p['at'][0]), float(p['at'][1]), float(p.get('yaw', 0))))
            got = self.farthest(flat, want.get('ground', 0))
            for k in got:
                placed.append(('ground', (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL, 0.0))
            # wall vents: flat cells 48..80 from a solid wall segment, facing away from it
            segs = [sg for sg in self.wall_segments(z)]
            wc = []
            for k in self.flat_cells(z, 40):
                cx, cy = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
                for sg in segs:
                    dd = self.dist_seg(cx, cy, sg)
                    u = cx if sg[0] == 'x' else cy
                    if 44 <= dd <= 80 and sg[3] + 48 <= u <= sg[4] - 48 and all(math.hypot(cx - a[0], cy - a[1]) >= 160 for a in avoid):
                        wc.append((k, sg)); break
            taken = [(p[1], p[2]) for p in placed]
            gotw = self.farthest([k for k, _ in wc], want.get('wall', 0), taken)
            segof = dict(wc)
            for k in gotw:
                ax, fixed, facing = segof[k][:3]
                yaw = (90 if facing > 0 else 270) if ax == 'x' else (0 if facing > 0 else 180)
                placed.append(('wall', (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL, float(yaw)))
            taken = [(p[1], p[2]) for p in placed]
            allc = sorted(k for k, rn in self.owner.items() if self.zone_of_cell(k) == z.id and z.inside((k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL)
                          and not rn.startswith('portal:') and z.ceiling - self.cells[k] >= HEAD)
            gotc = self.farthest(allc, want.get('ceiling', 0), taken)
            for k in gotc:
                placed.append(('ceiling', (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL, 270.0))
            for kind, wnt, gt in (('ground', want.get('ground', 0), got), ('wall', want.get('wall', 0), gotw), ('ceiling', want.get('ceiling', 0), gotc)):
                if len(gt) < wnt:
                    self.problems.append('zone %s: %d of %d %s spawners found a place' % (z.id, len(gt), wnt, kind))
            first_ground = True
            for kind, x, y, yaw in placed:
                fz = self.cell_z(x, y)
                fz = (fz - NAV_LIFT) if fz is not None else z.floor_at(x, y)
                vol = self.vol_of(z.id, x, y)
                e = dict(classname='script_struct', targetname=vol + '_spawner', noteworthy='static', angles='0 %g 0' % yaw)
                if kind == 'ground':
                    e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_ground', parameters='ground_spawn_no_boards', fxid='concrete')
                elif kind == 'wall':
                    e.update(origin=self.fmt((x, y, fz + 8)), animation='spawn_wall_low', parameters='no_boards')
                    self.vent(z.id, x, y, fz, yaw)
                else:
                    e.update(origin=self.fmt((x, y, z.ceiling)), animation='spawn_ceiling', parameters='ground_spawn_no_boards', fxid='ceiling')
                    self.B.quad('vent', z.id, [(x - 28, y + 28, z.ceiling - 0.6), (x + 28, y + 28, z.ceiling - 0.6), (x + 28, y - 28, z.ceiling - 0.6),
                                              (x - 28, y - 28, z.ceiling - 0.6)], n=(0, 0, -1), collide=False)
                self.ent(**e)
                plate = False
                if kind == 'ground' and first_ground and z.plate:
                    plate, first_ground = True, False
                    plates.append({'zone': z.id, 'origin': [x, y, fz]})
                    self.ent(classname='script_struct', targetname='iwz_inspection_plate', origin=self.fmt((x, y, fz)), angles='0 0 0', area=z.id)
                    self.B.quad('steel_trim', z.id, [(x - 20, y - 20, fz + 0.3), (x + 20, y - 20, fz + 0.3), (x + 20, y + 20, fz + 0.3),
                                                    (x - 20, y + 20, fz + 0.3)], n=(0, 0, 1), collide=False)
                layout['spawners'].append({'zone': z.id, 'volume': vol, 'origin': (x, y, z.ceiling if kind == 'ceiling' else fz), 'kind': kind,
                                           'yaw': yaw, 'on_nav': self.cell_z(x, y) is not None, 'plate': plate})
            # dog spawners, idle spots, respawns: on flat cells away from the spawners
            if z.far:
                continue
            taken = [(p[1], p[2]) for p in placed]
            dogs = []
            # brute / goon landing spots: two per spawn volume (stock recipe 2 to 4 per zone), flat cells first
            for v in [v for v in self.vols if v['zone'] == z.id]:
                b = v['box']
                inv = lambda k: b[0] <= (k[0] + 0.5) * CELL <= b[3] and b[1] <= (k[1] + 0.5) * CELL <= b[4]
                cand = [k for k in flat if inv(k)] or sorted(k for k in self.flat_cells(z, 24) if inv(k)) or                     sorted(k for k, rn in self.owner.items() if self.zone_of_cell(k) == z.id and inv(k) and not rn.startswith('portal:'))
                dogs += self.farthest(cand, 2, taken + [((k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL) for k in dogs])
            for k in dogs:
                x, y = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
                fz = self.cells[k] - NAV_LIFT
                self.ent(classname='script_struct', targetname='dog_spawner', origin=self.fmt((x, y, fz + 8)), angles='0 0 0', radius=66)
                self.ent(classname='script_struct', targetname='zombie_idle_spot', origin=self.fmt((x, y, fz + 8)))
            resp = self.farthest(flat, 2, taken + [((k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL) for k in dogs])
            for k in resp:
                x, y = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
                self.ent(classname='script_struct', targetname='player_respawn_loc', origin=self.fmt((x, y, self.cells[k] - NAV_LIFT)), angles='0 0 0')
            layout.setdefault('dog_spawners', {})[z.id] = [[(k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL] for k in dogs]
            layout.setdefault('respawns', {})[z.id] = [[(k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL] for k in resp]
            # a standing point per zone (route tables, walk tests): the flat cell nearest the middle of its flat cells
            if flat:
                mx = sum(k[0] for k in flat) / len(flat); my = sum(k[1] for k in flat) / len(flat)
                kc = min(flat, key=lambda k: ((k[0] - mx) ** 2 + (k[1] - my) ** 2, k))
                layout.setdefault('zone_points', {})[z.id] = [(kc[0] + 0.5) * CELL, (kc[1] + 0.5) * CELL, self.cells[kc] - NAV_LIFT]
            # waiting places (zombies held behind a line) and the skate mask (where Rollers may skate): scene, else defaults
            layout.setdefault('waiting', {})[z.id] = z.d.get('waiting') or [[(k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL] for k in self.farthest(flat, 4)]
            layout.setdefault('skate', {})[z.id] = z.d.get('skate') or [list(r) for r, _zz, _k in z.floor_pieces()]
        layout['inspection_plates'] = plates

    def vent(self, zone, x, y, fz, yaw):
        fx, fy = round(math.cos(math.radians(yaw))), round(math.sin(math.radians(yaw)))
        B = self.B
        if fx != 0:
            wx = x - fx * 48
            B.wall_plane(zone, 'y', wx + fx * 0.6, fx, y - 28, y + 28, fz + 4, fz + 44, 'metal_black', collide=False)
            B.wall_plane(zone, 'y', wx + fx * 2.4, fx, y - 28, y + 28, fz + 4, fz + 44, 'grate', collide=False)
        else:
            wy = y - fy * 48
            B.wall_plane(zone, 'x', wy + fy * 0.6, fy, x - 28, x + 28, fz + 4, fz + 44, 'metal_black', collide=False)
            B.wall_plane(zone, 'x', wy + fy * 2.4, fy, x - 28, x + 28, fz + 4, fz + 44, 'grate', collide=False)

    def place_doors(self):
        import json as _j
        sm_path = os.environ.get('IWZ_SUBMODELS') or os.path.join(HERE, 'sz2_submodels.json')
        subs = _j.load(open(sm_path)).get('blockers', []) if os.path.isfile(sm_path) else []
        doors = []
        for o in self.ops:
            if o['kind'] != 'door':
                continue
            za, zb = o['zones']
            target = 'iwz_door_' + o['door']
            pa, pb = o['planes'][za], o['planes'][zb]
            mid = (o['span'][0] + o['span'][1]) / 2
            plane = (pa + pb) / 2
            for zid, other in ((za, zb), (zb, za)):
                side = o['facing'][zid]
                off = o['planes'][zid] + side * 40
                org = (mid, off, o['sill'] + 24) if o['axis'] == 'x' else (off, mid, o['sill'] + 24)
                yaw = (270 if side > 0 else 90) if o['axis'] == 'x' else (180 if side > 0 else 0)
                self.ent(classname='script_struct', targetname='interaction', noteworthy='debris_%d' % int(o['price']), origin=self.fmt(org),
                         angles='0 %g 0' % yaw, area=self.vol_of(other, *self.opening_point(o, other)), target=target)
                self.layout['interactions'].append({'kind': 'debris_%d' % int(o['price']), 'origin': org, 'yaw': yaw, 'area': other, 'zone': zid, 'target': target})
            vis = (mid, plane, o['sill']) if o['axis'] == 'x' else (plane, mid, o['sill'])
            self.ent(classname='trigger_use', targetname='door_buy', target=target, noteworthy='debris_%d' % int(o['price']),
                     origin=self.fmt((vis[0], vis[1], o['sill'] + 96)), model='?41' if o['axis'] == 'x' else '?52',
                     dummy='triggermodeldummydefault', f60803=40)
            nblk = self.door_blockers(subs, target, o['axis'], plane, o['span'][0], o['span'][1], o['sill'], o['top'])
            doors.append({'name': o['id'], 'door': o['door'], 'target': target, 'cost': int(o['price']), 'zones': list(o['zones']),
                          'axis': 0 if o['axis'] == 'y' else 1, 'plane': plane, 'lo': o['span'][0], 'hi': o['span'][1], 'z0': o['sill'],
                          'z1': o['top'], 'blockers': nblk})
        self.layout['doors'] = doors
        self.layout['openings'] = [{'name': o['id'], 'kind': o['kind'], 'axis': o['axis'], 'zones': list(o['zones']),
                                    'walls': {k: v for k, v in o['planes'].items()}, 'a': o['span'][0], 'b': o['span'][1],
                                    'z0': o['sill'], 'z1': o['top'], 'price': o['price']} for o in self.ops]

    def door_blockers(self, subs, target, axis, plane, a, b, z0, z1):
        if not subs:
            self.problems.append('no door blocker sub-model (sz2_submodels.json): doors have no collision until bought')
            return 0
        sm = subs[0]
        (mx, my, mz), (hx, hy, hz) = sm['mid'], sm['half']
        wide_x = hx >= hy
        span, height = (2 * hx if wide_x else 2 * hy), 2 * hz
        nx = max(1, int(math.ceil((b - a + 8) / span)))
        nz = max(1, int(math.ceil((z1 - z0 + 4) / height)))
        count = 0
        for i in range(nx):
            c = a - 4 + span / 2 + i * (b - a + 8 - span) / max(1, nx - 1) if nx > 1 else (a + b) / 2
            for k in range(nz):
                zc = z0 + hz + k * (z1 - z0 + 4 - height) / max(1, nz - 1) if nz > 1 else (z0 + z1) / 2
                if axis == 'x':
                    yaw = 0 if wide_x else 90
                    lx, ly = (mx, my) if yaw == 0 else (-my, mx)
                    org = (c - lx, plane - ly, zc - mz)
                else:
                    yaw = 90 if wide_x else 0
                    lx, ly = (mx, my) if yaw == 0 else (-my, mx)
                    org = (plane - lx, c - ly, zc - mz)
                self.ent(classname='script_brushmodel', targetname=target, model=sm['model'], origin=self.fmt(org), angles='0 %g 0' % yaw,
                         spawnflags='1', dummy=sm.get('dummy', 'ScriptBrushModelDummyFixed'))
                count += 1
        return count

    PERK_SCRIPTABLE = {'revive': 'perk_machine_up_n_atoms_sign', 'tough': 'perk_machine_tuff_nuff_sign', 'run': 'perk_machine_racin_stripes_sign',
                       'rat_a_tat': 'perk_machine_bang_bangs_sign', 'flash': 'perk_machine_quickies_sign', 'zap': 'perk_machine_blue_bolts_sign',
                       'boom': 'perk_machine_bombstoppers_sign', 'more': 'perk_machine_mule_munchies_sign', 'smack': 'perk_machine_slappy_taffy_sign',
                       'fwoosh': 'perk_machine_trail_blazers_sign'}
    WHEEL_SCRIPTABLES = ['pf141_auto1', 'pf161_auto1', 'pf162_auto1', 'pf142_auto1', 'pf154_auto1', 'pf158_auto1', 'pf160_auto1', 'pf135_auto1', 'pf165_auto1']
    # wall weapons by class: the stock weapons of Spaceland's wall-buy list (02-WORLD.md section 4); a class the list
    # lacks gets a stand-in, recorded in the layout
    WALL_WEAPON = {'pistol': ('iw7_revolver_zm', 'weapon_kb_revolver_wm'), 'revolver': ('iw7_revolver_zm', 'weapon_kb_revolver_wm'),
                   'carbine': ('iw7_m1c_zm', None), 'smg': ('iw7_ump45_zml', 'weapon_ump_wm'), 'rifle': ('iw7_m4_zm', 'weapon_kb_m4_wm'),
                   'shotgun': ('iw7_sonic_zmr', 'weapon_sonic_wm'), 'marksman': ('iw7_m1c_zm', None), 'lmg': ('iw7_ake_zml', None),
                   'heavy_shotgun': ('iw7_sonic_zmr', 'weapon_sonic_wm'), 'heavy': ('iw7_ake_zml', None)}
    STAND_IN = {'lmg', 'heavy', 'heavy_shotgun', 'marksman'}

    def place_interactions(self):
        sc, layout = self.sc, self.layout
        wheels = 0
        for it in sc.interactions:
            z = sc.zones[it['zone']]
            kind = it['kind']
            if kind == 'perk':
                org, yaw = self.place(z, it, 40)
                name = 'perk_machine_' + it['perk']
                # 'powered': on from match start, like a stock area generator that is on (the Cordon's Up 'N Atoms)
                if it.get('powered'):
                    self.istruct(name, org, yaw, z.id)
                else:
                    self.istruct(name, org, yaw, z.id, parameters='requires_power')
                self.relocations.append('%s 0 %g %g %g %g' % (self.PERK_SCRIPTABLE[it['perk']], org[0], org[1], org[2], yaw))
            elif kind == 'wall_buy':
                org, yaw = self.place(z, it, 8)
                org = (org[0], org[1], org[2] + 64)
                weapon, wm = self.WALL_WEAPON[it['class']]
                kw = {'groupname': 'wall_buy', 'radius': 256}
                if wm:
                    kw['model'] = wm
                self.istruct(weapon, org, yaw, z.id, **kw)
                layout['interactions'][-1].update({'class': it['class'], 'price': it.get('price'), 'stand_in': it['class'] in self.STAND_IN})
            elif kind == 'wheel':
                org, yaw = self.place(z, it, 40)
                sc_ = self.WHEEL_SCRIPTABLES[wheels]; wheels += 1
                self.relocations.append('%s 0 %g %g %g %g' % (sc_, org[0], org[1], org[2], yaw))
                fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
                self.ent(classname='script_struct', noteworthy='spinner', model='zmb_magic_wheel_spinner',
                         origin=self.fmt((org[0] + 8 * fx, org[1] + 8 * fy, org[2] + 55.6)), angles='0 %g 0' % yaw)
                self.ent(classname='script_model', noteworthy='out_of_order', model='tag_origin', origin=self.fmt((org[0], org[1], org[2] + 37)))
                rx, ry = math.cos(math.radians(yaw - 90)), math.sin(math.radians(yaw - 90))
                self.ent(classname='script_struct', targetname='wheel_fx_spot', origin=self.fmt((org[0] + 8 * fx + 14 * rx, org[1] + 8 * fy + 14 * ry, org[2] + 55.2)),
                         angles='0 %g 0' % yaw)
                layout['interactions'].append({'kind': 'magic_wheel', 'scriptable': sc_, 'origin': org, 'yaw': yaw, 'zone': z.id, 'first': wheels == 1})
            elif kind == 'power':
                org, yaw = self.place(z, it, 24)
                org = (org[0], org[1], org[2] + 50)
                self.istruct('generator', org, yaw, z.id, parameters=it.get('parameters', 'power_all'), target='iwz_power_switch')
                self.ent(classname='script_model', targetname='iwz_power_switch', model='icbm_electricpanel_switch_02', noteworthy='-pitch',
                         origin=self.fmt(org), angles='75 %g 0' % yaw)
            elif kind == 'pap':
                org, yaw = self.place(z, it, 40)
                self.istruct('weapon_upgrade', org, yaw, z.id, parameters='requires_power', target='iwz_pap_spot')
                self.relocations.append('pap_machine 0 %g %g %g %g' % (org[0], org[1] + 10, org[2], yaw))
                self.ent(classname='script_struct', targetname='iwz_pap_spot', origin=self.fmt((org[0], org[1] + 20, org[2] + 14)),
                         angles='0 %g 0' % yaw, model='weapon_e_ak47_rare_wm')
            elif kind == 'trap_third_rail':
                org, yaw = self.place(z, it, 24)
                org = (org[0], org[1], org[2] + 20)
                self.ent(classname='script_struct', targetname='iwz_trap_third_rail_fusebox', origin=self.fmt(org), angles='0 %g 0' % yaw)
                self.ent(classname='script_model', targetname='iwz_trap_third_rail_fusebox_model', model='fac_sort_machine_fuse_box_set_01',
                         origin=self.fmt(org), angles='0 %g 0' % ((yaw + 180) % 360))
                layout['interactions'].append({'kind': kind, 'origin': org, 'yaw': yaw, 'zone': z.id, 'box': it['box'], 'rail': it.get('rail')})
                layout['trap_third_rail'] = {'box': it['box'], 'rail': it.get('rail', [it['box'][1] + 40, it['box'][2] + 12])}
            else:
                raise SceneError('interaction kind %s is not emitted (use markers for later packages)' % kind)
        if wheels:
            first = next(i for i in layout['interactions'] if i['kind'] == 'magic_wheel')
            layout['first_wheel_zone'] = first['zone']
        for m in sc.markers:
            z = sc.zones[m['zone']]
            if 'at' in m or 'wall' in m:
                org, yaw = self.place(z, m, float(m.get('off', 40)))
            else:
                org, yaw = None, None
            layout['markers'].append(dict(m, origin=org, yaw=yaw))

    def istruct(self, kind, origin, yaw, zone, **kw):
        self.ent(classname='script_struct', targetname='interaction', noteworthy=kind, origin=self.fmt(origin), angles='0 %g 0' % yaw, **kw)
        self.layout['interactions'].append({'kind': kind, 'origin': origin, 'yaw': yaw, 'zone': zone, **kw})

    # ---------------------------------------------------------------- level script
    def level_script(self):
        gsc = open(os.path.join(HERE, 'cp_iwz3.gsc'), encoding='utf-8').read()
        door_lines = ['    doors[doors.size] = iwz_door( "%s", "%s", %d, %g, %g, %g, %g, %g );' % (
            d['name'], d['target'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1']) for d in self.layout['doors']]
        links = []
        for o in self.ops:
            if o['kind'] != 'door':
                a, b = (self.vol_of(z_, *self.opening_point(o, z_)) for z_ in o['zones'])
                if [a, b] not in links and [b, a] not in links:
                    links.append([a, b])
        for v in self.vols:          # extra volumes of one zone activate with it
            if v['name'] != v['zone']:
                links.append([v['zone'], v['name']])
        link_lines = ['    links[links.size] = [ "%s", "%s" ];' % tuple(l) for l in links]
        gsc = gsc.replace('//@DOORS@', '\n'.join(door_lines)).replace('//@LINKS@', '\n'.join(link_lines))
        init = [self.vol_of(self.sc.start_zone, *self.layout['starts'][0][:2])]
        gsc = gsc.replace('//@INITIAL@', 'level.initial_active_volumes = [ %s ];' % ', '.join('"%s"' % z for z in init))
        gsc = gsc.replace('//@WHEEL@', '"%s"' % self.layout.get('first_wheel_zone', self.sc.start_zone))
        tr = self.layout.get('trap_third_rail')
        if tr:
            b = tr['box']
            gsc = gsc.replace('//@TRAPMIN@', '( %g, %g, %g )' % tuple(b[:3])).replace('//@TRAPMAX@', '( %g, %g, %g )' % tuple(b[3:]))
            gsc = gsc.replace('//@TRAPRAILY@', '%g' % tr['rail'][0]).replace('//@TRAPRAILZ@', '%g' % tr['rail'][1])
        else:
            gsc = gsc.replace('//@TRAPMIN@', '( 0, 0, 0 )').replace('//@TRAPMAX@', '( 0, 0, 0 )').replace('//@TRAPRAILY@', '0').replace('//@TRAPRAILZ@', '0')
        prices = ['    table[table.size] = iwz_price( %s, "%s", %d );' % (self.fmt3(i['origin']), i['kind'], int(i['price']))
                  for i in self.layout['interactions'] if i.get('groupname') == 'wall_buy' and i.get('price')]
        gsc = gsc.replace('//@PRICES@', '\n'.join(prices).lstrip())
        # game-script modules (modules/*.gsc: Q1 quest, T1 Capsule Post...): tables filled, started by the level script
        import sz_modules
        mapname = self.sc.map
        mods = sz_modules.emit(os.path.join(self.out, 'modules'), self.layout['markers'],
                               [{'name': v['name'], 'zone': v['zone'], 'box': v['box']} for v in self.vols], mapname)
        gsc = gsc.replace('//@MODULES@', '\n'.join(sz_modules.calls(mods, mapname)).lstrip())
        self.layout['modules'] = mods
        self.layout['zone_links'] = links
        open(os.path.join(self.out, 'cp_iwz.gsc'), 'w', newline='\n').write(gsc)

    @staticmethod
    def fmt3(p):
        return '( %g, %g, %g )' % tuple(float(v) for v in p)

    def opening_point(self, o, zid):
        mid = (o['span'][0] + o['span'][1]) / 2
        p = o['planes'][zid] + o['facing'][zid] * 40
        return (mid, p) if o['axis'] == 'x' else (p, mid)

    # ---------------------------------------------------------------- run
    def run(self):
        sc = self.sc
        os.makedirs(self.out, exist_ok=True)
        self.problems = []
        self.ops = [sc.locate(o) for o in sc.openings()]
        for z in sc.zones.values():
            self.build_shell(z)
        for o in self.ops:
            self.reveal(o)
        self.build_nav()
        self.emit_entities()
        self.level_script()
        mg = self.mapgen
        nv, ni, ns, wb = mg.write_world(self.B.mesh, os.path.join(self.out, 'world.bin'))
        col = [tuple(tuple(c * mg.HAVOK_SCALE for c in p) for p in t) for t in self.B.mesh.col]
        blob, info = self.hk.encode(col, os.path.join(self.tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx'), tag=TAG_SOLID,
                                    max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')),
                                    # IWZ_MAX_SECTION=<units>: sections no wider than that (hkcm_write.split_sections); off by default:
                                    # the Terminus floor loss it was tried for came from the physics broadphase (map compiler)
                                    max_extent=(float(os.environ.get('IWZ_MAX_SECTION', '0')) * mg.HAVOK_SCALE) or None,
                                    tags=[self.B.mesh.col_tag.get(i, TAG_SOLID) for i in range(len(col))])
        open(os.path.join(self.out, 'colmap.hkx'), 'wb').write(blob)
        amb = ['ambient 0.30 0.30 0.32 0.50']
        probes = []
        for z in sc.zones.values():
            b = z.bbox()
            r, g, bl, up = z.probe
            row = 'room %d %d %d %d %d %d %.3f %.3f %.3f %.2f' % (b[0] - 48, b[1] - 48, z.zmin() - 64, b[2] + 48, b[3] + 48, z.ceiling + 64, r, g, bl, up)
            amb.append(row); probes.append(row)
        open(os.path.join(self.out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(amb) + '\n')
        open(os.path.join(self.out, 'probes.txt'), 'w', newline='\n').write('\n'.join(probes) + '\n')
        self.layout['regions'] = len(self.regions)
        self.layout['volumes'] = self.vols
        self.layout['navconn_routes'] = self.navconn_routes()
        self.layout['far_zones'] = [z.id for z in sc.zones.values() if z.far]
        json.dump(self.layout, open(os.path.join(self.out, 'layout.json'), 'w'), indent=1, default=list)
        json.dump({'custom': self.MT.CUSTOM, 'used': sorted(self.B.used)}, open(os.path.join(self.out, 'custom_materials.json'), 'w'), indent=1)
        col_walls = []
        for t_ in self.B.mesh.col:
            (ax_, ay_, az_), (bx_, by_, bz_), (cx_, cy_, cz_) = t_
            nx_ = (by_ - ay_) * (cz_ - az_) - (bz_ - az_) * (cy_ - ay_)
            ny_ = (bz_ - az_) * (cx_ - ax_) - (bx_ - ax_) * (cz_ - az_)
            nz_ = (bx_ - ax_) * (cy_ - ay_) - (by_ - ay_) * (cx_ - ax_)
            ln_ = (nx_ * nx_ + ny_ * ny_ + nz_ * nz_) ** 0.5
            if ln_ < 1e-6 or abs(nz_) / ln_ > 0.2:
                continue
            pts_ = sorted({(round(ax_, 1), round(ay_, 1)), (round(bx_, 1), round(by_, 1)), (round(cx_, 1), round(cy_, 1))})
            if len(pts_) >= 2:
                col_walls.append([pts_[0][0], pts_[0][1], pts_[-1][0], pts_[-1][1], round(min(az_, bz_, cz_), 1), round(max(az_, bz_, cz_), 1)])
        plan = {'regions': [{'name': r['name'], 'zone': r['zone'], 'rect': r['rect']} for r in self.regions], 'adj': [sorted(a) for a in self.adj],
                'cells': [[i, j, zz, self.owner[(i, j)]] for (i, j), zz in self.cells.items()],
                'cell_corners': [[i, j, list(c_)] for (i, j), c_ in self.corner.items() if (i, j) in self.cells],
                'blockers': self.B.blockers, 'col_tris': len(self.B.mesh.col), 'bounds': wb, 'col_walls': col_walls}
        json.dump(plan, open(os.path.join(self.out, 'plan.json'), 'w'))
        gross = sum(rect_area(b) for z in sc.zones.values() for b in z.boxes) * 0.0254 ** 2
        per_zone = collections.Counter(self.zone_of_cell(k) for k in self.cells)
        self.report.update({
            'map': sc.map, 'zones': len(sc.zones), 'volumes': len(self.vols), 'doors': len(sc.doors), 'door_points': sum(int(d.get('price', 0)) for d in sc.doors),
            'links': len(sc.links), 'flights': len(self.stairs), 'gross_m2': round(gross),
            'walkable_m2_by_zone': {z: round(n * CELL * CELL * 0.0254 ** 2) for z, n in sorted(per_zone.items())},
            'spawners': len(self.layout['spawners']), 'spawners_by_zone': dict(collections.Counter(s['zone'] for s in self.layout['spawners'])),
            'inspection_plates': len(self.layout['inspection_plates']),
            'world': {'vertices': nv, 'indices': ni, 'surfaces': ns, 'quads': self.B.quads, 'materials': len(self.B.used)},
            'collision': {'triangles': len(col), 'havok': info, 'bytes': len(blob)},
            'entities': self.entity_census(), 'problems': self.problems})
        json.dump(self.report, open(os.path.join(self.out, 'scene_report.json'), 'w'), indent=1, default=list)
        self.log('scenegen %s: %d zones, %d volumes, %d doors (%d points), %d links, %d flights, gross %d m2, walkable %d m2, '
                 '%d nav cells, %d spawners, %d surfaces, %d collision triangles, %d problems' % (
                     sc.map, len(sc.zones), len(self.vols), len(sc.doors), self.report['door_points'], len(sc.links), len(self.stairs),
                     self.report['gross_m2'], self.report['nav']['walkable_m2'], len(self.cells), len(self.layout['spawners']), ns, len(col),
                     len(self.problems)))
        for p in self.problems:
            self.log('PROBLEM ' + p)
        return self.report

    def navconn_routes(self):
        """region pairs sz2_navconn proves have a cell path: the start zone to every other non-far zone"""
        reg_of_zone, live = {}, set(self.owner.values())
        for kind in ('flat', 'flight'):
            for r in self.regions:
                if r['kind'] == kind and r['name'] in live:
                    reg_of_zone.setdefault(r['zone'], r['name'])
        s = reg_of_zone.get(self.sc.start_zone)
        return [[s, reg_of_zone[z.id]] for z in self.sc.zones.values() if not z.far and z.id != self.sc.start_zone and z.id in reg_of_zone and s]

    def entity_census(self):
        c = collections.Counter(dict(e).get('157') for e in self.ents)
        ents = sum(v for k, v in c.items() if k not in ('script_struct',))
        return {'by_class': dict(c), 'entities_excluding_structs': ents}


def emit(scene_path, tpl, out, log=print):
    sc = Scene.load(scene_path)
    errs = [m for s, m in check_scene(sc) if s == 'ERROR']
    if errs:
        raise SceneError('scene check failed:\n  ' + '\n  '.join(errs))
    return Emitter(sc, tpl, out, log).run()


# =========================================================================== reading an emit back
def check_flights(src, tol=6.0):
    """navigation corner heights against the highest collision surface under them, along every flight"""
    import iwz_emitcheck as EC
    e = EC.Emit.load(src)
    plan = json.load(open(os.path.join(src, 'plan.json')))
    corners = {(c[0], c[1]): c[2] for c in plan.get('cell_corners', [])}
    owner = {(c[0], c[1]): c[3] for c in plan['cells']}
    rows, worst = [], {}
    for (i, j), cz in corners.items():
        rn = owner.get((i, j), '')
        if not rn.startswith('flight:'):
            continue
        for (x, y), z in zip(((i * CELL, j * CELL), ((i + 1) * CELL, j * CELL), ((i + 1) * CELL, (j + 1) * CELL), (i * CELL, (j + 1) * CELL)), cz):
            # sample just inside the cell so the point is not on a triangle edge
            sx, sy = x + (0.37 if x == i * CELL else -0.37), y + (0.29 if y == j * CELL else -0.29)
            fl = [f for f, _c in e.col.floors(sx, sy) if f <= z + tol + 1.0]
            if not fl:
                d = None
            else:
                d = z - max(fl)
            k = rn[len('flight:'):]
            if d is None or abs(d) > tol:
                rows.append((k, round(x), round(y), z, d))
            w = worst.get(k, 0.0)
            worst[k] = max(w, 99.0 if d is None else abs(d))
    return {'flights': {k: round(v, 2) for k, v in sorted(worst.items())}, 'failures': rows, 'tolerance': tol}


def routes(src, speed=190.0, pairs=None):
    import iwz_emitcheck as EC
    e = EC.Emit.load(src)
    lay = e.layout
    pts = lay.get('zone_points', {})
    names = [z for z in lay.get('zones', {}) if z in pts]
    table = {}
    want = pairs or [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    for a, b in want:
        if a not in pts or b not in pts:
            continue
        pa, pb = pts[a], pts[b]
        ka, kb = e.nav.nearest(pa[0], pa[1], pa[2] + NAV_LIFT), e.nav.nearest(pb[0], pb[1], pb[2] + NAV_LIFT)
        ln, _path = e.nav.route(ka, kb)
        table[(a, b)] = None if ln is None else (round(ln), round(ln / speed, 1))
    return table


def test_args(src, inset=20.0, depth=96.0):
    """playtest dvars from an emit (iw7-paris-server ops/iwzmap/Test-IWZMapPlaytest.ps1 -ExtraArgs): a climb case up
    and down every flight (paris_iwz_pt_climbs) and a route through every door and link (paris_iwz_pt_routes): the
    player walks it both ways and a zombie follows from its start"""
    lay = json.load(open(os.path.join(src, 'layout.json')))
    pt = lambda x, y, z: '%d,%d,%d' % (round(x), round(y), round(z))
    climbs = []
    for st in lay.get('stairs', []):
        a0, a1 = st['span']
        cm = (st['c'][0] + st['c'][1]) / 2
        lo_at_a0 = abs(st['ramp_from'][0] - a0) < abs(st['ramp_from'][0] - a1)
        lo_s, hi_s = (a0 + inset, a1 - inset) if lo_at_a0 else (a1 - inset, a0 + inset)
        P = (lambda s_, z_: pt(s_, cm, z_)) if st['axis'] == 'x' else (lambda s_, z_: pt(cm, s_, z_))
        lo, hi = P(lo_s, st['z'][0]), P(hi_s, st['z'][1])
        climbs.append('%s_up=%s/%s' % (st['space'], lo, hi))
        climbs.append('%s_down=%s/%s' % (st['space'], hi, lo))
    routes = []
    for o in lay.get('openings', []):
        za, zb = o['zones']
        pa, pb = o['walls'][za], o['walls'][zb]
        sa = -1 if pb >= pa else 1          # zone a lies on this side of its wall plane
        if abs(pb - pa) < 0.5:              # zero gap: which side from the zone boxes
            b = lay['zones'][za]['box']
            k = 0 if o['axis'] == 'y' else 1
            sa = 1 if (b[k] + b[k + 3]) / 2 > pa else -1
        mid = (o['a'] + o['b']) / 2
        z = o['z0']
        q = (lambda c_: pt(c_, mid, z)) if o['axis'] == 'y' else (lambda c_: pt(mid, c_, z))
        routes.append('%s=%s/%s/%s' % (o['name'], q(pa + sa * depth), q((pa + pb) / 2), q(pb - sa * depth)))
    return {'climbs': '|'.join(climbs), 'routes': '|'.join(routes), 'climb_cases': len(climbs), 'route_cases': len(routes)}


def import_props(scene_path, old_layout, mapping, exclude=r'rubble|plank|barricade|debris', clear=96.0):
    """props for kept rooms from an older generated map's layout.json decor: compiled static models of zone A moved into
    zone B (mapping 'old=new[:dx,dy,dz]'). A prop is kept when it lands on a floor of its new zone at the height it had,
    clear of every opening and flight by `clear`, and its name does not match `exclude`. -> {zone: [props]}, report"""
    import re
    sc = Scene.load(scene_path)
    ops = [sc.locate(o) for o in sc.openings()]
    lay = json.load(open(old_layout, encoding='utf-8'))
    maps = {}
    for m in mapping:
        old, rest = m.split('=')
        new, _, off = rest.partition(':')
        maps[old] = (new, tuple(float(v) for v in off.split(',')) if off else (0.0, 0.0, 0.0))
    out, rep = collections.defaultdict(list), collections.Counter()
    for d in lay.get('decor', []):
        if d.get('zone') not in maps:
            continue
        news, (dx, dy, dz) = maps[d['zone']]
        if not d.get('static') or re.search(exclude, d['model']):
            rep['skipped: not static or excluded'] += 1
            continue
        x, y, oz = d['origin'][0] + dx, d['origin'][1] + dy, d['origin'][2] + dz
        new = next((n for n in news.split('|') if sc.zones[n].floor_at(x, y) is not None), news.split('|')[0])
        z = sc.zones[new]
        fz = z.floor_at(x, y)
        if fz is None or any(f.rect[0] - clear <= x <= f.rect[2] + clear and f.rect[1] - clear <= y <= f.rect[3] + clear for f in z.flights):
            rep['skipped: off a floor of the zone or on a flight'] += 1
            continue
        if abs(fz - oz) > 24 and abs(fz - (oz - dz)) > 24:
            rep['skipped: floor height differs'] += 1
            continue
        near = False
        for o in ops:
            if new not in o['zones']:
                continue
            p = o['planes'][new]
            u, v = (x, y) if o['axis'] == 'x' else (y, x)
            if o['span'][0] - clear <= u <= o['span'][1] + clear and abs(v - p) <= clear + 48:
                near = True
        if near:
            rep['skipped: in front of an opening'] += 1
            continue
        pr = {'model': d['model'], 'at': [round(x, 2), round(y, 2)], 'z': round(oz, 2), 'yaw': d.get('yaw', 0),
              'pitch': d.get('pitch', 0), 'roll': d.get('roll', 0), 'static': True, 'from': d['zone']}
        if d.get('clip'):
            pr['clip'] = d['clip']
        out[new].append(pr)
        rep['kept'] += 1
    return dict(out), dict(rep)


def lab_plans(src, mapname=None, per_plan=26, count=3, chase_s=45, player=True):
    """headless gamelab plans (iw7-paris-server ops/gamelab/Invoke-GameLabHeadless.ps1 -UsermapDir) from an emit:
    doors opened, then for every flight a zombie climb up and down (zombies placed at the foot or the head, the bot at
    the other end) and for every door and link a zombie crossing (zombies placed in one zone, the bot in the other);
    each case expects every zombie to arrive. The first plan also surveys the navigation from the start and counts
    the map's entities. Cases are split over plans of at most per_plan cases."""
    import re
    t = test_args(src)
    cases = []
    for c in t['climbs'].split('|') + t['routes'].split('|'):
        if not c:
            continue
        name, pts = c.split('=')
        p = [[float(v) for v in q.split(',')] for q in pts.split('/')]
        cases.append((name, p[0], p[-1], p))
    lay = json.load(open(os.path.join(src, 'layout.json')))
    mapname = mapname or lay.get('map', 'cp_iwz')
    start = lay['starts'][0]
    # the plan's spawn step takes the nearest real spawner and places its zombies; a ceiling spawner's drop animation
    # then still runs and takes them through the floor (11 Nov 2026, the Staff stair). A case starts on the side whose
    # zone has ground spawners.
    ground = {s_['zone'] for s_ in lay.get('spawners', []) if s_.get('kind') == 'ground'}

    def zone_at(p_):
        for zn, zd in lay['zones'].items():
            if any(b[0] <= p_[0] <= b[2] and b[1] <= p_[1] <= b[3] for b in zd['boxes']):
                return zn
        return None
    try:
        import iwz_emitcheck as EC
        nav = EC.Emit.load(src).nav
    except Exception:
        nav = None
    plans = [{'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1a_survey' % mapname, 'map': mapname,
              'about': 'Scene-generated map: every door opened, the navigation surveyed from the start, the entities counted.',
              'steps': [{'do': 'waves', 'on': False}, {'do': 'doors'}, {'do': 'tp', 'at': list(start)}, {'do': 'ents', 'name': 'all'},
                        {'do': 'survey', 'name': 'map', 'step': 128, 'max': 6000}]}]
    # A session holds 600 s (gamelab MAX_SESSION_S; the plan needs 75 s of start-up and 1.2 x its steps): cases are
    # packed into plans by their estimated time, at most per_plan a plan (11 Nov 2026: 8 cases with longer chases needed
    # 683 s and were refused).
    def cost(a, b, pts):
        ln = None
        if nav is not None:
            ln, _p = nav.route(nav.nearest(*a), nav.nearest(*b))
        walk = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) / 190.0 * 1.5 + len(pts) if player else 0
        return 2 * walk + count * 4.8 + max(chase_s, int(math.ceil((ln or 0) / 20.0 + 10))) + 1

    chunks, cur, t = [], [], 0.0
    for case in cases:
        ct = cost(case[1], case[2], case[3])
        if cur and (len(cur) >= per_plan or t + ct > 360):
            chunks.append(cur)
            cur, t = [], 0.0
        cur.append(case)
        t += ct
    if cur:
        chunks.append(cur)
    for chunk in chunks:
        steps = [{'do': 'waves', 'on': False}, {'do': 'doors'}]
        expects = []
        for name, a, b, pts in chunk:
            if zone_at(a) not in ground and zone_at(b) in ground:
                a, b, pts = b, a, pts[::-1]
            tag = re.sub(r'[^a-z0-9_]', '_', name.lower())[:40]
            # round-1 zombies walk about 34 units a second (measured, W1a runs hl-b, 11 Nov 2026) and start after
            # about 3 s: the chase gets the navigation length at 20 u/s plus 10 s, at least chase_s
            ln = None
            if nav is not None:
                ln, _p = nav.route(nav.nearest(*a), nav.nearest(*b))
            s = max(chase_s, int(math.ceil((ln or 0) / 20.0 + 10)))
            if player:
                # the player walks it both ways with player physics (gamelab move step), before the zombies come
                steps += [{'do': 'kill'}, {'do': 'move', 'name': tag[:36] + '_fwd', 'path': pts},
                          {'do': 'move', 'name': tag[:36] + '_bck', 'path': pts[::-1]}]
                expects += [{'do': 'expect', 'that': 'move:%s_%s.reached' % (tag[:36], w), 'eq': len(pts) - 1,
                             'why': 'the player walks %s %s' % (name, 'forward' if w == 'fwd' else 'back')} for w in ('fwd', 'bck')]
            steps += [{'do': 'kill'}, {'do': 'tp', 'at': b}, {'do': 'spawn', 'tag': tag, 'at': a, 'count': count},
                      {'do': 'chase', 'tag': tag, 's': s, 'allow_partial': True}, {'do': 'kill', 'tag': tag}]
            # allow_partial: the case is judged by its expectation below (arrivals against the number spawned), not by
            # the chase's own count, which also counts a stray of the same tag (11 Nov 2026: "2 of 3" for 2 spawned)
            # the chase also counts zombies of earlier cases that died there: the case needs as many arrivals as it spawned
            expects.append({'do': 'expect', 'that': 'chase:%s.reached' % tag, 'ge': count,
                            'why': 'every zombie gets from %s to the player at %s (%s)' % (a, b, name)})
        plans.append({'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1a_%d' % (mapname, len(plans)), 'map': mapname,
                      'about': 'Scene-generated map: zombie climbs on every flight and crossings of every door and link, '
                               'headless (scenegen.py labplans).', 'steps': steps + expects})
    return plans


def lab_report(src, runs):
    """read gamelab run folders of the lab plans: every case's zombie arrivals (SP_END lines), the verdicts, and the
    survey points per zone (which zones the navigation reaches from the start with every door open)"""
    import glob, re
    lay = json.load(open(os.path.join(src, 'layout.json')))
    cases, verdicts, survey, made, moves = {}, {}, None, {}, {}
    for run in runs:
        for log in glob.glob(os.path.join(run, '**', 'client.stdout.log'), recursive=True) + glob.glob(os.path.join(run, '**', 'server.stdout.log'), recursive=True):
            for ln in open(log, encoding='utf-8', errors='replace'):
                m = re.search(r'GL MOVE i=\d+ name=(\S+) legs=(\d+) reached=(\d+) result=(\S+)', ln)
                if m:
                    moves[m.group(1)] = (int(m.group(3)), int(m.group(2)), m.group(4))
                m = re.search(r'GL SPAWN i=\d+ tag=(\S+) made=(\d+)', ln)
                if m:
                    made[m.group(1)] = int(m.group(2))
                m = re.search(r'SP_END case=(\S+) result=(\d+)/(\d+) \S+ died=(\d+) ms=(\d+)', ln)
                if m:
                    # the chase counts every zombie alive (strays of earlier cases too): a case passes when as many
                    # arrive as the case spawned
                    cases[m.group(1)] = {'reached': int(m.group(2)), 'total': int(m.group(3)), 'died': int(m.group(4)), 'ms': int(m.group(5)),
                                         'made': made.get(m.group(1))}
        for res in glob.glob(os.path.join(run, '**', 'gamelab.result.json'), recursive=True):
            d = json.load(open(res, encoding='utf-8'))
            verdicts[os.path.basename(os.path.dirname(os.path.dirname(res)))] = d.get('verdict') or d.get('class')
        for sv in glob.glob(os.path.join(run, '**', 'survey-*.json'), recursive=True):
            survey = json.load(open(sv, encoding='utf-8'))
    zones = lay['zones']
    per_zone = collections.Counter()
    if survey:
        for _i, x, y, z, _f in survey['points']:
            hit = [n for n, zd in zones.items() if any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in zd['boxes'])]
            per_zone[hit[0] if hit else 'outside'] += 1
    expected = test_args(src)
    names = [c.split('=')[0] for c in (expected['climbs'] + '|' + expected['routes']).split('|') if c]
    tag = lambda n: re.sub(r'[^a-z0-9_]', '_', n.lower())[:40]
    rows = [(n, cases.get(tag(n))) for n in names]
    ok = lambda c: bool(c) and c['reached'] >= (c.get('made') or c['total']) > 0
    for n, c in rows:
        if c:
            c['pass'] = ok(c)
            for w in ('fwd', 'bck'):
                mv = moves.get(tag(n)[:36] + '_' + w)
                if mv:
                    c['player_' + w] = '%d/%d %s' % mv
    return {'cases': rows, 'passed': sum(1 for _n, c in rows if ok(c)),
            'run': sum(1 for _n, c in rows if c), 'expected': len(rows), 'verdicts': verdicts,
            'player_walks': {'run': len(moves), 'reached': sum(1 for v in moves.values() if v[0] == v[1])},
            'survey': {'points': len(survey['points']) if survey else 0, 'per_zone': dict(per_zone),
                       'zones_missing': [z for z, zd in zones.items() if not zd.get('far') and not per_zone.get(z)] if survey else None}}


def stress_props(scene_path, kits_path, n, seed=1, clear=96.0):
    """ST1: n stock props spread over the zones by floor area, as compiled static models of models that have a template
    twin (kit lists, template_donor: no model without a twin, so no entity and no TF10 dependency). Each stands on a flat
    floor of its zone, clear of every opening and flight. -> ({zone: [props]}, {zone: count})"""
    import random
    rnd = random.Random(seed)
    sc = Scene.load(scene_path)
    kits = json.load(open(kits_path, encoding='utf-8'))['zones']
    donors = {z: [m['name'] for m in v['models'] if m.get('template_donor')] for z, v in kits.items()}
    every = sorted({m for v in donors.values() for m in v})
    ops = [sc.locate(o) for o in sc.openings()]
    zones = [z for z in sc.zones.values() if not z.far]
    pieces = {z.id: [(r, zz) for r, zz, _k in z.floor_pieces() if rect_area(r) > 64 * 64] for z in zones}
    area = {z.id: sum(rect_area(r) for r, _zz in pieces[z.id]) for z in zones}
    total = sum(area.values())
    out, counts = {}, {}
    for z in zones:
        want = int(round(n * area[z.id] / total))
        models = donors.get(z.id) or every
        items, tries = [], 0
        while len(items) < want and tries < want * 40:
            tries += 1
            r, fz = rnd.choices(pieces[z.id], weights=[rect_area(p[0]) for p in pieces[z.id]])[0]
            x, y = rnd.uniform(r[0] + 24, r[2] - 24), rnd.uniform(r[1] + 24, r[3] - 24)
            if any(f.rect[0] - clear <= x <= f.rect[2] + clear and f.rect[1] - clear <= y <= f.rect[3] + clear for f in z.flights):
                continue
            near = False
            for o in ops:
                if z.id not in o['zones']:
                    continue
                u, v = (x, y) if o['axis'] == 'x' else (y, x)
                if o['span'][0] - clear <= u <= o['span'][1] + clear and abs(v - o['planes'][z.id]) <= clear + 48:
                    near = True
                    break
            if near:
                continue
            items.append({'model': rnd.choice(models), 'at': [round(x, 1), round(y, 1)], 'z': fz, 'yaw': rnd.randrange(0, 360, 15),
                          'static': True, 'stress': 1})
        out[z.id], counts[z.id] = items, len(items)
    return out, counts


WALK_PAIRS = [('cordon', 'converter_hall'), ('fare_hall', 'platform_west'), ('car_barn', 'exchange')]


def simplify(pts, eps):
    """Ramer-Douglas-Peucker in 3D: the points a walker steers at, at most eps units off the navigation path"""
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    ab = [b[i] - a[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in ab)) or 1e-9
    best, k = -1.0, 0
    for i in range(1, len(pts) - 1):
        ap = [pts[i][j] - a[j] for j in range(3)]
        t = max(0.0, min(1.0, sum(ap[j] * ab[j] for j in range(3)) / (L * L)))
        d = math.dist(pts[i], [a[j] + t * ab[j] for j in range(3)])
        if d > best:
            best, k = d, i
    if best <= eps:
        return [a, b]
    return simplify(pts[:k + 1], eps)[:-1] + simplify(pts[k:], eps)


def walk_paths(src, pairs=None):
    """the navigation path between zone standing points, simplified to at most 40 points: [(a, b, nav_length, points)]"""
    import iwz_emitcheck as EC
    e = EC.Emit.load(src)
    zp = e.layout.get('zone_points', {})
    out = []
    for a, b in pairs or WALK_PAIRS:
        pa, pb = zp[a], zp[b]
        ln, path = e.nav.route(e.nav.nearest(pa[0], pa[1], pa[2] + NAV_LIFT), e.nav.nearest(pb[0], pb[1], pb[2] + NAV_LIFT))
        if ln is None:
            out.append((a, b, None, []))
            continue
        pts = [list(e.nav.a[k]['c']) for k in path]
        eps, s = 12.0, simplify(pts, 12.0)
        while len(s) > 40:
            eps *= 1.5
            s = simplify(pts, eps)
        out.append((a, b, ln, [[round(p[0], 1), round(p[1], 1), round(p[2] + 8, 1)] for p in s]))
    return out


def walk_plan(src, mapname=None, pairs=None):
    """a client plan (it presses a movement key): a real player walks each route along the navigation path with the
    forward key held, so its time calibrates the walking-time table (routes) that assumed 190 units a second"""
    lay = json.load(open(os.path.join(src, 'layout.json')))
    mapname = mapname or lay.get('map', 'cp_iwz')
    steps = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}]
    expects = []
    for a, b, ln, pts in walk_paths(src, pairs):
        if not pts:
            continue
        name = ('walk_%s_%s' % (a, b))[:40]
        steps.append({'do': 'walk', 'name': name, 'path': pts, 's': min(300, int(ln / 120.0 + 20))})
        expects.append({'do': 'expect', 'that': 'walk:%s.reached' % name, 'eq': len(pts) - 1, 'why': 'a player walks from %s to %s' % (a, b)})
    # the client answers the last key release only if the session is still running (11 Nov 2026: BUTTON_NOT_PRESSED on
    # the final release of a plan that ended with the walk)
    steps.append({'do': 'wait', 's': 3})
    return {'schema': 'iw7.gamelab-plan/1', 'name': '%s_walk' % mapname, 'map': mapname,
            'about': 'Scene-generated map: a real walk (forward key held) along three routes, to calibrate the walking-time table.',
            'steps': steps + expects}


def walk_report(src, runs, pairs=None):
    """the timed walks of a walk plan against the navigation length: the measured walking speed and the factor that turns
    the routes table (nav length at 190 u/s) into real walking time"""
    import glob, re
    want = {('walk_%s_%s' % (a, b))[:40]: (a, b, ln, pts) for a, b, ln, pts in walk_paths(src, pairs)}
    got = {}
    for run in runs:
        for log in glob.glob(os.path.join(run, '**', '*.log'), recursive=True):
            for line in open(log, encoding='utf-8', errors='replace'):
                m = re.search(r'GL WALK i=\d+ seq=\d+ name=(\S+) legs=(\d+) reached=(\d+) result=(\S+) moved=(\d+) ms=(\d+) speed=(\d+)', line)
                if m:
                    got[m.group(1)] = {'legs': int(m.group(2)), 'reached': int(m.group(3)), 'result': m.group(4), 'moved': int(m.group(5)),
                                       'ms': int(m.group(6)), 'speed': int(m.group(7))}
    rows, moved, ms, navsum = [], 0, 0, 0.0
    for name, (a, b, ln, pts) in want.items():
        g = got.get(name)
        plen = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) if pts else None
        r = {'route': '%s -> %s' % (a, b), 'nav_length': round(ln) if ln else None, 'path_length': round(plen) if plen else None,
             'predicted_190_s': round(ln / 190.0, 1) if ln else None}
        if g:
            r.update({'measured_s': round(g['ms'] / 1000.0, 1), 'moved': g['moved'], 'speed': g['speed'], 'result': g['result'],
                      'reached': '%d/%d' % (g['reached'], g['legs'])})
            if g['result'] == 'reached':
                moved, ms, navsum = moved + g['moved'], ms + g['ms'], navsum + ln
        rows.append(r)
    speed = moved * 1000.0 / ms if ms else None
    return {'routes': rows, 'walk_speed': round(speed, 1) if speed else None,
            'nav_speed': round(navsum * 1000.0 / ms, 1) if ms else None,
            'note': 'walk_speed: units a second along the walked path; nav_speed: navigation length / measured time, '
                    'the speed to give scenegen routes --speed for real walking times'}


def w1b_plans(src, mapname=None, start_weapon='iw7_g18_zm'):
    """headless plans for the blockout's systems (W1b): power, perks, wall weapons, the wheel, the Third Rail trap,
    special-enemy structs and rounds, each used through the game's own interaction code (gamelab step "use") and judged
    on the game's own script state (money, perks, weapons, the power flag, the round number, entities)"""
    lay = json.load(open(os.path.join(src, 'layout.json')))
    mapname = mapname or lay.get('map', 'cp_iwz')
    its = lay['interactions']
    perks = [i for i in its if i['kind'].startswith('perk_machine_')]
    powered = [i for i in perks if i.get('parameters') != 'requires_power']
    needs = [i for i in perks if i.get('parameters') == 'requires_power']
    gen = next((i for i in its if i['kind'] == 'generator'), None)
    walls = [i for i in its if i.get('groupname') == 'wall_buy']
    wheels = [i for i in its if i['kind'] == 'magic_wheel']
    trap = next((i for i in its if i['kind'] == 'trap_third_rail'), None)
    head = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 500000}]
    a, ea = list(head), []
    ndog = sum(len(v) for v in lay.get('dog_spawners', {}).values())
    for nm, key, val, n in (('dogs', 'targetname', 'dog_spawner', ndog), ('brute', 'targetname', 'brute_hide_org', 1),
                            ('respawns', 'targetname', 'player_respawn_loc', sum(1 for v in lay.get('respawns', {}).values() for _ in v) or 1)):
        a.append({'do': 'ents', 'name': nm, 'key': key, 'value': val})
        ea.append({'do': 'expect', 'that': 'ents:%s.n' % nm, 'ge': n, 'why': 'the special-enemy and respawn structs are in the running map (%s)' % val})
    a.append({'do': 'state', 'name': 'start'})
    for p in powered:
        nm = 'pk_' + p['kind'][len('perk_machine_'):] + '_prepower'
        a.append({'do': 'use', 'name': nm[:40], 'kind': p['kind'], 'near': p['origin'], 's': 4})
        # headless: the purchase is judged by the points it took before the power. Up 'N Atoms' gesture never ends on an
        # engine bot, so the perk itself is checked with a real player in the client plan <map>_w1b_powered_client
        # (11 Nov 2026: bot 500 taken, no perk; a client player got it)
        ea += [{'do': 'expect', 'that': 'use:%s.spent' % nm[:40], 'gt': 0, 'why': '%s sells before the power (its own generator)' % p['kind']},
               {'do': 'expect', 'that': 'use:%s.power' % nm[:40], 'eq': 0, 'why': 'the main power is still off'}]
    if needs and gen:
        p = needs[0]
        nm = 'pk_%s_nopower' % p['kind'][len('perk_machine_'):]
        a.append({'do': 'use', 'name': nm[:40], 'kind': p['kind'], 'near': p['origin'], 's': 3})
        ea += [{'do': 'expect', 'that': 'use:%s.perks1' % nm[:40], 'eq': '@use:%s.perks0' % nm[:40], 'why': 'a powered perk refuses before the power'},
               {'do': 'expect', 'that': 'use:%s.spent' % nm[:40], 'eq': 0, 'why': 'a refused perk costs nothing'}]
    if gen:
        a.append({'do': 'use', 'name': 'power', 'kind': 'generator', 'near': gen['origin'], 's': 6})
        ea.append({'do': 'expect', 'that': 'use:power.power', 'eq': 1, 'why': 'the power switch (%s) turns the power on' % gen['zone']})
    for p in (needs if gen else []):
        nm = ('pk_' + p['kind'][len('perk_machine_'):])[:40]
        a.append({'do': 'use', 'name': nm, 'kind': p['kind'], 'near': p['origin'], 's': 4})
        ea += [{'do': 'expect', 'that': 'use:%s.perks1' % nm, 'gt': '@use:%s.perks0' % nm, 'why': '%s gives its perk after the power' % p['kind']},
               {'do': 'expect', 'that': 'use:%s.spent' % nm, 'gt': 0, 'why': 'a perk costs points'}]
    if wheels:
        w = next((x for x in wheels if x.get('first')), wheels[0])
        a += [{'do': 'take', 'give': start_weapon}, {'do': 'use', 'name': 'wheel', 'kind': 'magic_wheel', 'near': w['origin'], 's': 7, 'again': True}]
        ea += [{'do': 'expect', 'that': 'use:wheel.spent', 'gt': 0, 'why': 'a spin costs points'},
               {'do': 'expect', 'that': 'use:wheel.weapons1', 'gt': '@use:wheel.weapons0', 'why': 'the wheel gives a weapon (spin, then take it)'}]
        a.append({'do': 'ents', 'name': 'wheels', 'key': 'script_noteworthy', 'value': 'magic_wheel'})
        ea.append({'do': 'expect', 'that': 'ents:wheels.n', 'ge': len(wheels), 'why': 'every wheel position is a stock wheel struct'})
    if trap:
        bx = trap['box']
        mid = [round((bx[0] + bx[3]) / 2.0), round((bx[1] + bx[4]) / 2.0), bx[2]]
        # the player stands at the fuse box first: the stock cleanup recycles zombies far from every player (11 Nov 2026:
        # all four pit zombies died while the bot stood 3,500 units away at the wheel)
        a += [{'do': 'tp', 'at': trap['origin']}, {'do': 'spawn', 'tag': 'pit', 'at': mid, 'count': 4}, {'do': 'mark', 'name': 'trap_before'},
              {'do': 'use', 'name': 'trap', 'ent': 'iwz_trap_third_rail_use', 'near': trap['origin'], 's': 6},
              {'do': 'mark', 'name': 'trap_after'}, {'do': 'kill'}]
        # deaths: every death of a plan zombie, whatever killed it (the trap has no attacker); the marks also print each body
        ea += [{'do': 'expect', 'that': 'trap_before.alive', 'ge': 1, 'why': 'zombies stand in the track pit'},
               {'do': 'expect', 'that': 'trap_after.deaths', 'gt': '@trap_before.deaths', 'why': 'the Third Rail kills the zombies in the pit (those that climbed to the deck live: the marks list each body)'},
               {'do': 'expect', 'that': 'use:trap.spent', 'eq': 750, 'why': 'the trap costs 750'}]
    a.append({'do': 'state', 'name': 'end_systems'})
    plans = [{'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1b_systems' % mapname, 'map': mapname,
              'about': 'W1b: power, perks, the wheel, the Third Rail trap and the special-enemy structs, used through the stock interaction code (headless).',
              'steps': a + ea}]
    b, eb = list(head), []
    for k, w in enumerate(walls):
        nm = ('wb%02d_%s' % (k, w['zone']))[:40]
        b += [{'do': 'take', 'give': start_weapon}, {'do': 'use', 'name': nm, 'kind': w['kind'], 'near': w['origin'], 's': 2}]
        eb.append({'do': 'expect', 'that': 'use:%s.has' % nm, 'eq': 1, 'why': 'the wall weapon in %s gives %s' % (w['zone'], w['kind'])})
        if w.get('price'):
            eb.append({'do': 'expect', 'that': 'use:%s.spent' % nm, 'eq': int(w['price']), 'why': 'it costs the price of its place (%d)' % w['price']})
    plans.append({'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1b_walls' % mapname, 'map': mapname,
                  'about': 'W1b: every wall weapon bought through the stock interaction code at the price of its place (headless).',
                  'steps': b + eb})
    c = [{'do': 'ignore', 'on': True}, {'do': 'state', 'name': 'r_start'}, {'do': 'rounds', 'name': 'r', 'to': 7, 's': 380}, {'do': 'state', 'name': 'r_end'}]
    ec = [{'do': 'expect', 'that': 'rounds:r.advanced', 'ge': 5, 'why': 'rounds advance with the stock spawning'},
          {'do': 'expect', 'that': 'rounds:r.growth', 'le': 40, 'why': 'entities are cleaned up between rounds'}]
    plans.append({'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1b_rounds' % mapname, 'map': mapname,
                  'about': 'W1b: rounds 1 to 7 with the stock spawning from the start zone; the bot kills what spawns (headless).',
                  'steps': c + ec})
    if powered:
        p = powered[0]
        steps = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 500000},
                 {'do': 'take', 'give': start_weapon}, {'do': 'use', 'name': 'pk', 'kind': p['kind'], 'near': p['origin'], 's': 10},
                 {'do': 'expect', 'that': 'use:pk.perks1', 'gt': '@use:pk.perks0', 'why': 'a player gets %s before the power' % p['kind']},
                 {'do': 'expect', 'that': 'use:pk.power', 'eq': 0, 'why': 'the main power is still off'}]
        plans.append({'schema': 'iw7.gamelab-plan/1', 'name': '%s_w1b_powered_client' % mapname, 'map': mapname,
                      'about': 'W1b: the perk on its own generator, bought by a real player before the power (client).', 'steps': steps})
    return plans


def pools(src, tpl):
    """what the emit takes from the template's finite pools, and the entity count"""
    import re
    ents_t = open(os.path.join(tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'), 'rb').read().decode('latin-1')
    tb = [dict(re.findall(r'^\s*(\S+) "([^"]*)"', b, re.M)) for b in re.findall(r'\{([^{}]*)\}', ents_t)]
    lay = json.load(open(os.path.join(src, 'layout.json')))
    rep = json.load(open(os.path.join(src, 'scene_report.json')))
    scr = [ln.split()[0] for ln in open(os.path.join(src, 'scriptables.txt')) if ln.strip()]
    trig = sum(1 for ln in open(os.path.join(src, 'triggers.txt')) if ln.strip())
    tpl_wheels = len(Emitter.WHEEL_SCRIPTABLES)
    tpl_perks = len(Emitter.PERK_SCRIPTABLE)
    gens = sum(1 for e in tb if e.get('822') == 'interaction' and e.get('638') == 'generator')
    out = {
        'zone_volume_trigger_shapes': {'used': trig, 'template_usable': 54, 'note': 'IWZ_TRIGGER_SHAPES rescales unused template boxes (volumes REPORT)'},
        'magic_wheel_scriptables': {'used': sum(1 for s in scr if s in Emitter.WHEEL_SCRIPTABLES), 'template': tpl_wheels},
        'perk_scriptables': {'used': sum(1 for s in scr if s.startswith('perk_machine_')), 'template': tpl_perks,
                             'note': 'new perks (P1) and Deadeye Dewdrops have no template machine'},
        'generator_structs': {'used': sum(1 for i in lay['interactions'] if i['kind'] == 'generator'), 'template': gens},
        'debris_scriptables': {'used': 0, 'template': 14, 'note': 'doors use their own blocker brushes (stock clear_debris), no template debris pile'},
        'door_blocker_brushes': {'used': sum(d.get('blockers', 0) for d in lay['doors']), 'note': 'copies of one kept template sub-model; each is an entity'},
        'door_buy_trigger_models': {'used': len(lay['doors']), 'note': 'template models ?41 and ?52 reused by every door'},
        'switchable_light_slots': {'used': 0, 'template': 25},
        'pack_a_punch': {'used': sum(1 for i in lay['interactions'] if i['kind'] == 'weapon_upgrade'), 'template': 1},
        'entities': rep['entities'],
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('check'); p.add_argument('scene'); p.add_argument('--json')
    p = sub.add_parser('emit'); p.add_argument('scene'); p.add_argument('template'); p.add_argument('out')
    p = sub.add_parser('flights'); p.add_argument('src'); p.add_argument('--tol', type=float, default=6.0); p.add_argument('--json')
    p = sub.add_parser('routes'); p.add_argument('src'); p.add_argument('--speed', type=float, default=190.0); p.add_argument('--md')
    p.add_argument('--pairs', help='a,b;c,d (zone ids); default every pair')
    p = sub.add_parser('pools'); p.add_argument('src'); p.add_argument('template'); p.add_argument('--json')
    p = sub.add_parser('tests'); p.add_argument('src'); p.add_argument('--json')
    p = sub.add_parser('importprops'); p.add_argument('scene'); p.add_argument('old_layout'); p.add_argument('mapping', nargs='+')
    p.add_argument('--out', help='write {zone: [props]} (one prop a line); name it in the props_files of the scene')
    p = sub.add_parser('labplans'); p.add_argument('src'); p.add_argument('out'); p.add_argument('--per-plan', type=int, default=26)
    p.add_argument('--count', type=int, default=3); p.add_argument('--chase', type=int, default=45)
    p.add_argument('--no-player', action='store_true', help='zombie cases only (no player walks)')
    p = sub.add_parser('labreport'); p.add_argument('src'); p.add_argument('runs', nargs='+'); p.add_argument('--json')
    p = sub.add_parser('walkplan', help='a client plan: a real walk along three routes (calibrates the walking-time table)')
    p.add_argument('src'); p.add_argument('out'); p.add_argument('--pairs', help='a,b;c,d (zone ids)')
    p = sub.add_parser('walkreport', help='the measured walking speed from a walk plan run')
    p.add_argument('src'); p.add_argument('runs', nargs='+'); p.add_argument('--pairs'); p.add_argument('--json')
    p = sub.add_parser('w1bplans', help='headless plans for the systems: power, perks, wall weapons, wheel, trap, rounds')
    p.add_argument('src'); p.add_argument('out'); p.add_argument('--start-weapon', default='iw7_g18_zm')
    p = sub.add_parser('stressprops', help='ST1: a copy of the scene with n stock static props spread by floor area')
    p.add_argument('scene'); p.add_argument('kits'); p.add_argument('n', type=int); p.add_argument('out_scene')
    p.add_argument('--seed', type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == 'stressprops':
        props, counts = stress_props(a.scene, a.kits, a.n, a.seed)
        base = os.path.dirname(os.path.abspath(a.scene))
        d = json.load(open(a.scene, encoding='utf-8'))
        pf = os.path.splitext(os.path.abspath(a.out_scene))[0] + '_props.json'
        with open(pf, 'w', encoding='utf-8', newline=chr(10)) as f:
            json.dump(props, f)
        d['props_files'] = [os.path.join(base, x) for x in d.get('props_files', [])] + [pf]
        json.dump(d, open(a.out_scene, 'w', encoding='utf-8'), indent=1)
        print('stress props: %d placed (%s) -> %s' % (sum(counts.values()), ', '.join('%s %d' % kv for kv in counts.items()), a.out_scene))
        return 0
    pairs =[tuple(x.split(',')) for x in a.pairs.split(';')] if getattr(a, 'pairs', None) else None
    if a.cmd in ('walkplan', 'w1bplans'):
        os.makedirs(a.out, exist_ok=True)
        pls = [walk_plan(a.src, None, pairs)] if a.cmd == 'walkplan' else w1b_plans(a.src, None, a.start_weapon)
        for pl in pls:
            path = os.path.join(a.out, pl['name'] + '.json')
            json.dump(pl, open(path, 'w'), indent=1)
            print('%s: %d steps' % (path, len(pl['steps'])))
        return 0
    if a.cmd == 'walkreport':
        r = walk_report(a.src, a.runs, pairs)
        for row in r['routes']:
            print(json.dumps(row))
        print('walking speed along the path %s u/s; navigation length / time %s u/s' % (r['walk_speed'], r['nav_speed']))
        if a.json:
            json.dump(r, open(a.json, 'w'), indent=1)
        return 0 if r['walk_speed'] else 1
    if a.cmd == 'check':
        sc = Scene.load(a.scene)
        res = check_scene(sc)
        for s, m in res:
            print('%-5s %s' % (s, m))
        if a.json:
            json.dump([{'severity': s, 'message': m} for s, m in res], open(a.json, 'w'), indent=1)
        return 1 if any(s == 'ERROR' for s, _ in res) else 0
    if a.cmd == 'emit':
        try:
            rep = emit(a.scene, a.template, a.out)
        except SceneError as e:
            print(e, file=sys.stderr)
            return 1
        return 1 if rep['problems'] else 0
    if a.cmd == 'flights':
        r = check_flights(a.src, a.tol)
        for k, v in r['flights'].items():
            print('FLIGHT %-28s worst %6.2f %s' % (k, v, 'ok' if v <= a.tol else 'FAIL'))
        for f in r['failures'][:20]:
            print('  off', f)
        print('flights: %d checked, %d corners off by more than %g' % (len(r['flights']), len(r['failures']), a.tol))
        if a.json:
            json.dump(r, open(a.json, 'w'), indent=1)
        return 1 if r['failures'] or not r['flights'] else 0
    if a.cmd == 'routes':
        pairs = [tuple(p.split(',')) for p in a.pairs.split(';')] if a.pairs else None
        t = routes(a.src, a.speed, pairs)
        lines = ['| From | To | Nav length (units) | Walk at %g u/s (s) |' % a.speed, '|---|---|---|---|']
        for (x, y), v in t.items():
            lines.append('| %s | %s | %s | %s |' % (x, y, v[0] if v else 'no path', v[1] if v else '-'))
        print('\n'.join(lines))
        if a.md:
            open(a.md, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        return 1 if any(v is None for v in t.values()) else 0
    if a.cmd == 'labreport':
        r = lab_report(a.src, a.runs)
        for n, c in r['cases']:
            print('CASE %-32s %s' % (n, 'not run' if not c else '%s %d/%d reached (spawned %s), died %d, %d ms; player %s / %s' % ('PASS' if c['pass'] else 'FAIL', c['reached'], c['total'], c.get('made'), c['died'], c['ms'], c.get('player_fwd', '-'), c.get('player_bck', '-'))))
        print('verdicts', r['verdicts'])
        print('survey points %d; per zone %s; zones not reached %s' % (r['survey']['points'], r['survey']['per_zone'], r['survey']['zones_missing']))
        print('cases: %d expected, %d run, %d with every zombie arriving; player walks %d, %d reached the end' % (r['expected'], r['run'], r['passed'], r['player_walks']['run'], r['player_walks']['reached']))
        if a.json:
            json.dump(r, open(a.json, 'w'), indent=1)
        return 0 if r['passed'] == r['expected'] else 1
    if a.cmd == 'labplans':
        os.makedirs(a.out, exist_ok=True)
        lay = json.load(open(os.path.join(a.src, 'layout.json')))
        for pl in lab_plans(a.src, lay.get('map', 'cp_iwz'), a.per_plan, a.count, a.chase, not a.no_player):
            path = os.path.join(a.out, pl['name'] + '.json')
            json.dump(pl, open(path, 'w'), indent=1)
            print('%s: %d steps' % (path, len(pl['steps'])))
        return 0
    if a.cmd == 'importprops':
        props, rep = import_props(a.scene, a.old_layout, a.mapping)
        print(json.dumps(rep), {k: len(v) for k, v in props.items()})
        if a.out:
            with open(a.out, 'w', encoding='utf-8', newline=chr(10)) as f:
                f.write('{' + chr(10) + (',' + chr(10)).join(' %s: [' % json.dumps(z) + chr(10) + (',' + chr(10)).join('  ' + json.dumps(p) for p in ps) + chr(10) + ' ]' for z, ps in props.items()) + chr(10) + '}' + chr(10))
        return 0
    if a.cmd == 'tests':
        r = test_args(a.src)
        print('+set paris_iwz_pt_climbs "%s" +set paris_iwz_pt_routes "%s"' % (r['climbs'], r['routes']))
        if a.json:
            json.dump(r, open(a.json, 'w'), indent=1)
        return 0
    if a.cmd == 'pools':
        r = pools(a.src, a.template)
        print(json.dumps(r, indent=1))
        if a.json:
            json.dump(r, open(a.json, 'w'), indent=1)
        return 0


if __name__ == '__main__':
    sys.exit(main())
