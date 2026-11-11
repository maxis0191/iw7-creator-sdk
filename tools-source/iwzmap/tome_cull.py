#!/usr/bin/env python3
"""The generated map's culling data, checked before a build and against the game's own frames.

The game draws the static models (props) that the Umbra visibility query returns, and the query culls with the data
the map compiler writes into the world's tome: per object its bounds (frustum) and its squared cull distance. This
tool reads that data from a compiled world (`dump/<map>/maps/cp/<map>.d3dbsp.gfxmap`, 10 s after the compile step,
six minutes before the zone step) and proves it against what can be seen.

    read    <gfxmap>                                   what the tome holds (objects by class, bounds, distances)
    check   <gfxmap> --db DB --layout LAYOUT.json      structure, every prop's box against its mesh, and every door
                                                       sightline: a prop seen through a door must not be culled
    cull-distances <smodels.txt> --models DB --out F  gives every prop the distance where it covers 30 pixels\n    views   --layout LAYOUT.json --out PLAN.json       a gamelab client plan that captures the door views with depth
    frames  <run folder> --db DB --gfxmap GFXMAP       the game's depth of those captures: every prop the offline
                                                       raster sees and the tome keeps must be drawn (no popping)
    model   <gfxmap> --log CLIENT.LOG                  props each perfzones view draws under the tome (no game)

DB is the world database of the compiled map (`tools-source/worldkit/iw7_world.py build --dump <work>/dump/<map>`,
then `iw7_see.py index --db DB --dump <template dump>` for the meshes). Exit 0 pass, 1 a check failed, 2 refused.
See docs/CULLING.md. The tome layout is read from the shipped maps' own data (format 20); no library code is used.
"""
import argparse
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'worldkit'))

FLT_MAX = 3.4028234663852886e38
TAN_HALF = (0.849427, 0.477803)          # the client's 1920 x 1080 view (cg_fov 65), solved from a frame (docs/SEE.md)
CLASS = {0: 'surface', 1: 'static model', 3: 'class 3', 4: 'primary light', 5: 'probe instance'}


def crc32c(data):
    crc = 0xFFFFFFFF
    table = crc32c.table
    for b in data:
        crc = table[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def _table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ (0x82F63B78 if c & 1 else 0)
        t.append(c)
    return t


crc32c.table = _table()


class Tome:
    """The parts of a format-20 tome this tool needs: header, objects (bounds, distance boxes, user ids)."""

    def __init__(self, data, check_crc=True):
        self.data = data
        u = lambda o: struct.unpack_from('<I', data, o)[0]
        if len(data) < 0x170 or u(0) != 0xD6000014:
            raise ValueError('not a format-20 tome (magic %s)' % (hex(u(0)) if len(data) >= 4 else '-'))
        self.size_ok = u(8) == len(data)
        self.crc_ok = (crc32c(data[8:]) == u(4)) if check_crc else None
        self.count = u(0x40)
        ob, od, starts, ids = u(0x44), u(0x48), u(0x4C), u(0x50)
        self.bounds = [struct.unpack_from('<6f', data, ob + 24 * i) for i in range(self.count)]
        dd = [struct.unpack_from('<8f', data, od + 32 * i) for i in range(self.count)]
        self.far_sq = [d[7] for d in dd]
        self.dist_box = [d[0:3] + d[4:7] for d in dd]
        self.near_sq = [d[3] for d in dd]
        if starts:
            self.ids = [[u(ids + 4 * k) for k in range(u(starts + 4 * i), u(starts + 4 * i + 4))] for i in range(self.count)]
        else:
            self.ids = [[u(ids + 4 * i)] for i in range(self.count)]
        self.tiles = u(0x90)
        self.clusters = u(0x7C)
        self.gates = u(0x68)
        self.scene = (struct.unpack_from('<3f', data, 0x150), struct.unpack_from('<3f', data, 0x15C))

    def by_class(self, cls):
        """{value: object index} for the user ids of one class."""
        out = {}
        for i, ids in enumerate(self.ids):
            for x in ids:
                if x >> 28 == cls:
                    out[x & 0xFFFFFFF] = i
        return out


def write_tome(objects, scene_min, scene_max):
    """The compiler's one-tile, one-cell tome (x64-zt iwzmap build_tome), for tests and offline experiments.
    objects: [(user_id, (min3 + max3), far_squared)]."""
    data = bytearray(0x170)

    def block(n):
        while len(data) % 16:
            data.append(0)
        off = len(data)
        data.extend(b'\0' * n)
        return off

    put = lambda off, fmt, *v: struct.pack_into('<' + fmt, data, off, *v)
    n = len(objects)
    width = 1
    while width < 31 and (1 << width) < n:
        width += 1
    lo = [scene_min[a] - 64.0 for a in range(3)]
    hi = [scene_max[a] + 64.0 for a in range(3)]
    put(0, 'I', 0xD6000014)
    put(0x0C, 'f', 512.0)
    put(0x14, '3f', *lo)
    put(0x20, '3f', *hi)
    put(0x150, '3f', *lo)
    put(0x15C, '3f', *hi)
    put(0x40, 'I', n)
    put(0x54, 'I', width)
    put(0x5C, 'I', n)
    put(0x8C, 'I', 1)
    put(0x90, 'I', 1)
    b = block(24 * n)
    dd = block(32 * n)
    for i, (_, box, far) in enumerate(objects):
        put(b + 24 * i, '6f', *box)
        put(dd + 32 * i, '8f', box[0], box[1], box[2], 0.0, box[3], box[4], box[5], far)
    put(0x44, 'I', b)
    put(0x48, 'I', dd)
    ids = block(4 * n)
    for i, (uid, _, _) in enumerate(objects):
        put(ids + 4 * i, 'I', uid)
    put(0x50, 'I', ids)
    put(8, 'I', len(data))
    put(4, 'I', crc32c(bytes(data[8:])))
    return bytes(data)


def load_world(gfxmap):
    import iw7_dump as D
    rec = {}
    orig = D.Stream.array

    def array(self, elem, expected, what, required=False):
        a = orig(self, elem, expected, what, required)
        if a is not None:
            rec.setdefault(what, (a.off, a.count, elem))
        return a

    D.Stream.array = array
    try:
        buf = open(gfxmap, 'rb').read()
        d = D.parse_gfxmap(buf)
    finally:
        D.Stream.array = orig
    if 'umbraTomeData' not in rec:
        raise ValueError('%s has no tome' % gfxmap)
    off, n, _ = rec['umbraTomeData']
    W, SI, SF, SD = d.layout
    smc = d.smodel_insts.count if d.smodel_insts else 0
    smodels = []
    for k in range(smc):
        m = struct.unpack_from('<6f', buf, d.smodel_insts.off + SI.size * k)
        cull = struct.unpack_from('<H', buf, d.draw_insts.off + SD.size * k + 160)[0]
        smodels.append({'model': d.smodel_models[k], 'box': (m[0] - m[3], m[1] - m[4], m[2] - m[5], m[0] + m[3], m[1] + m[4], m[2] + m[5]),
                        'cull': cull})
    return Tome(buf[off:off + n]), smodels, d


def box_nearest_sq(box, p):
    s = 0.0
    for a in range(3):
        v = p[a]
        if v < box[a]:
            s += (box[a] - v) ** 2
        elif v > box[a + 3]:
            s += (v - box[a + 3]) ** 2
    return s


class View:
    """A camera: origin, forward/left/up, tangents of the half fields of view."""

    def __init__(self, origin, forward, left, up, tanx, tany, name=''):
        self.origin, self.forward, self.left, self.up = origin, forward, left, up
        self.tanx, self.tany, self.name = tanx, tany, name
        # inward plane normals in world space (view space f, l, u: |l| <= f tanx, |u| <= f tany)
        self.planes = []
        for nf, nl, nu in ((tanx, -1, 0), (tanx, 1, 0), (tany, 0, -1), (tany, 0, 1), (1, 0, 0)):
            self.planes.append(tuple(nf * forward[a] + nl * left[a] + nu * up[a] for a in range(3)))

    @staticmethod
    def from_yaw_pitch(origin, yaw, pitch, tanx=TAN_HALF[0], tany=TAN_HALF[1], name=''):
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        f = (cp * cy, cp * sy, -sp)
        l = (-sy, cy, 0.0)
        u = (f[1] * l[2] - f[2] * l[1], f[2] * l[0] - f[0] * l[2], f[0] * l[1] - f[1] * l[0])
        return View(origin, f, l, u, tanx, tany, name)

    def box_in(self, box):
        for n in self.planes:
            # the box corner farthest along the inward normal
            px = box[3] if n[0] >= 0 else box[0]
            py = box[4] if n[1] >= 0 else box[1]
            pz = box[5] if n[2] >= 0 else box[2]
            if (px - self.origin[0]) * n[0] + (py - self.origin[1]) * n[1] + (pz - self.origin[2]) * n[2] < 0:
                return False
        return True


def tome_keeps(tome, obj, view):
    """(in frustum, within distance) of one tome object for a camera."""
    inf = view.box_in(tome.bounds[obj])
    far = tome.far_sq[obj]
    within = far >= FLT_MAX * 0.5 or box_nearest_sq(tome.dist_box[obj], view.origin) <= far
    return inf, within


# ---------------------------------------------------------------- read
def cmd_read(a):
    tome, smodels, d = load_world(a.gfxmap)
    cls = {}
    for ids in tome.ids:
        for x in ids:
            cls[CLASS.get(x >> 28, str(x >> 28))] = cls.get(CLASS.get(x >> 28, str(x >> 28)), 0) + 1
    lo, hi = tome.scene
    scene_sized = sum(1 for b in tome.bounds if all(abs(b[k] - lo[k]) < 1 and abs(b[k + 3] - hi[k]) < 1 for k in range(3)))
    finite = sum(1 for f in tome.far_sq if f < FLT_MAX * 0.5)
    ext = sorted(max(b[3] - b[0], b[4] - b[1], b[5] - b[2]) for b in tome.bounds)
    out = {'bytes': len(tome.data), 'size_ok': tome.size_ok, 'crc32c_ok': tome.crc_ok, 'objects': tome.count, 'by_class': cls,
           'tiles': tome.tiles, 'clusters': tome.clusters, 'gates': tome.gates, 'scene_sized_objects': scene_sized,
           'distance_culled_objects': finite, 'largest_extent_median': round(ext[len(ext) // 2], 1) if ext else None,
           'static_models': len(smodels)}
    print(json.dumps(out, indent=1))
    return 0


# ---------------------------------------------------------------- check
def door_views(layout, back=(96.0, 320.0), turns=(0.0, -20.0, 20.0), eye=60.0):
    """Cameras on both sides of every opening of layout.json, looking through it."""
    zones = layout['zones']
    out = []
    for op in layout.get('openings', []):
        zs = op.get('zones') or []
        if len(zs) != 2:
            continue
        axis = op.get('axis')
        mid = 0.5 * (op['a'] + op['b'])
        zc = 0.5 * (op['z0'] + op['z1'])
        for side, other in ((zs[0], zs[1]), (zs[1], zs[0])):
            if side not in zones or side not in (op.get('walls') or {}):
                continue
            plane = op['walls'][side]
            box = zones[side]['box']
            centre = 0.5 * (box[1] + box[4]) if axis == 'x' else 0.5 * (box[0] + box[3])
            sign = 1.0 if centre > plane else -1.0
            floor = zones[side].get('floor', op['z0'])
            for d in back:
                if axis == 'x':
                    o = (mid, plane + sign * d, floor + eye)
                    yaw0 = -90.0 if sign > 0 else 90.0
                else:
                    o = (plane + sign * d, mid, floor + eye)
                    yaw0 = 180.0 if sign > 0 else 0.0
                pitch = -math.degrees(math.atan2(zc - o[2], d))
                for t in turns:
                    name = '%s_%s_%d_%+d' % (op.get('name', 'opening'), side, int(d), int(t))
                    out.append({'name': name, 'opening': op.get('name'), 'from': side, 'into': other, 'origin': o,
                                'yaw': yaw0 + t, 'pitch': max(-30.0, min(30.0, pitch))})
    return out


def cmd_check(a):
    import numpy as np
    import iw7_see as S
    tome, smodels, d = load_world(a.gfxmap)
    errors, notes = [], []
    if not tome.size_ok:
        errors.append('tome size field differs from its length')
    if tome.crc_ok is False:
        errors.append('tome CRC32C does not match')
    sm = tome.by_class(1)
    missing = [k for k in range(len(smodels)) if k not in sm]
    if missing:
        errors.append('%d static models have no tome object (first %s)' % (len(missing), missing[:5]))
    extra = [v for v in sm if v >= len(smodels)]
    if extra:
        errors.append('%d tome static model ids point past the %d static models' % (len(extra), len(smodels)))
    bad_box, bad_far, scene_sized = [], [], 0
    lo, hi = tome.scene
    for k, s in enumerate(smodels):
        if k not in sm:
            continue
        o = sm[k]
        b = tome.bounds[o]
        if all(abs(b[q] - lo[q]) < 1 and abs(b[q + 3] - hi[q]) < 1 for q in range(3)):
            scene_sized += 1
            continue
        if max(abs(x - y) for x, y in zip(b, s['box'])) > 0.05:
            bad_box.append(k)
        want = float(s['cull']) ** 2 if s['cull'] else None
        far = tome.far_sq[o]
        if want is None and far < FLT_MAX * 0.5 or want is not None and abs(far - want) > 1 + want * 1e-6:
            bad_far.append(k)
    if scene_sized and not a.allow_conservative:
        errors.append('%d static models have scene-sized tome bounds: nothing culls them (a conservative tome)' % scene_sized)
    if bad_box:
        errors.append('%d static models: tome box differs from the static model bounds (first %s)' % (len(bad_box), bad_box[:5]))
    if bad_far:
        errors.append('%d static models: tome distance differs from cullDist squared (first %s)' % (len(bad_far), bad_far[:5]))
    scene = S.Scene(a.db)
    if len(scene.p_index) != len(smodels):
        errors.append('the database holds %d props, the world %d: build the database from this compile' % (len(scene.p_index), len(smodels)))
    # every prop's mesh inside its tome box (a box too small culls a prop whose other part is on screen)
    outside = []
    if scene.have_meshes:
        for name, ks in _by_model(scene).items():
            mesh = scene.meshes.get(name)
            if mesh is None or not len(mesh[0]):
                continue
            v = mesh[0]
            for k in ks:
                wv = v @ scene.p_axis[k] * scene.p_scale[k] + scene.p_origin[k]
                i = int(scene.p_index[k])
                if i not in sm:
                    continue
                b = tome.bounds[sm[i]]
                m = max(float(b[0] - wv[:, 0].min()), float(b[1] - wv[:, 1].min()), float(b[2] - wv[:, 2].min()),
                        float(wv[:, 0].max() - b[3]), float(wv[:, 1].max() - b[4]), float(wv[:, 2].max() - b[5]))
                if m > 0.5:
                    outside.append((i, name, round(m, 2)))
        if outside:
            errors.append('%d props have mesh outside their tome box (first %s)' % (len(outside), outside[:3]))
    else:
        notes.append('no mesh cache for the database (iw7_see.py index): the mesh-in-box check did not run')
    # door sightlines: everything the offline raster sees through each opening must pass the tome
    layout = json.load(open(a.layout, encoding='utf-8'))
    views = door_views(layout)
    w, h = a.size
    per_view, frustum_fail, pops = [], [], []
    seen_total = 0
    for v in views:
        view = View.from_yaw_pitch(v['origin'], v['yaw'], v['pitch'])
        frame = _frame(view, w, h)
        z, ids = scene.render(frame, cull=False)
        u, c = np.unique(ids[ids > 0], return_counts=True)
        seen = [(int(i) - 1, int(n)) for i, n in zip(u, c) if n >= a.min_pixels]
        seen_total += len(seen)
        ff = dd = 0
        full = None
        for p, npx in seen:
            if p not in sm:
                continue
            inf, within = tome_keeps(tome, sm[p], view)
            if not inf:
                ff += 1
                frustum_fail.append((v['name'], p, scene.p_model[scene.row_of[p]], npx))
            elif not within:
                dd += 1
                dist = math.sqrt(box_nearest_sq(tome.dist_box[sm[p]], view.origin))
                if full is None:
                    # what a distance-culled prop covers is measured at the game's own size, not scaled up from the
                    # small raster (a 2-pixel prop there is anything from 0 to 60 pixels at 1080p)
                    full = scene.render(_frame(view, 1920, 1080), cull=False)[1]
                npx_1080 = int((full == p + 1).sum())
                pops.append((v['name'], p, scene.p_model[scene.row_of[p]], npx_1080, round(dist), smodels[p]['cull']))
        kept = sum(1 for i in range(len(smodels)) if i in sm and all(tome_keeps(tome, sm[i], view)))
        per_view.append({'view': v['name'], 'seen': len(seen), 'frustum_culled_while_seen': ff, 'distance_culled_while_seen': dd,
                         'tome_keeps': kept})
    if frustum_fail:
        errors.append('%d props seen through a door are outside their tome box frustum test (first %s)' % (len(frustum_fail), frustum_fail[:3]))
    # a prop beyond its cull distance that still covers pop_pixels of a 1920 x 1080 frame vanishes visibly (pops);
    # smaller ones fade out the way the shipped map's props do (Spaceland: cull distance ~174 x radius, median)
    scale = 1.0
    big = [p for p in pops if p[3] >= a.pop_pixels]
    if big and not a.allow_distance_pops:
        errors.append('%d props seen through a door on %d+ pixels (1080p) lie beyond their cull distance: they pop (first %s)' % (
            len(big), a.pop_pixels, big[:3]))
    keeps = sorted(r['tome_keeps'] for r in per_view)
    out = {'gfxmap': a.gfxmap, 'objects': tome.count, 'static_models': len(smodels), 'distance_culled_static_models':
           sum(1 for s in smodels if s['cull']), 'views': len(views), 'props_seen_in_door_views': seen_total,
           'frustum_culled_while_seen': len(frustum_fail), 'distance_culled_while_seen': len(pops), 'pops_over_threshold': len(big),
           'mesh_outside_box': len(outside), 'tome_keeps_median': keeps[len(keeps) // 2] if keeps else None,
           'tome_keeps_max': keeps[-1] if keeps else None, 'errors': errors, 'notes': notes,
           'pops': [{'view': p[0], 'prop': p[1], 'model': p[2], 'pixels_1080': round(p[3] * scale), 'distance': p[4], 'cull': p[5]} for p in sorted(pops, key=lambda p: -p[3])[:200]],
           'per_view': per_view, 'verdict': 'pass' if not errors else 'fail'}
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
    for k in ('objects', 'static_models', 'distance_culled_static_models', 'views', 'props_seen_in_door_views',
              'frustum_culled_while_seen', 'distance_culled_while_seen', 'pops_over_threshold', 'mesh_outside_box', 'tome_keeps_median', 'tome_keeps_max'):
        print('%-32s %s' % (k, out[k]))
    for e in errors:
        print('ERROR', e)
    for n in notes:
        print('NOTE ', n)
    print('VERDICT', out['verdict'])
    return 0 if not errors else 1


def _by_model(scene):
    out = {}
    for k, m in enumerate(scene.p_model):
        out.setdefault(m, []).append(k)
    return out


class _Frame:
    """The minimum of iw7_see.Frame the raster needs, for a camera that was not captured."""

    def __init__(self, view, w, h):
        import numpy as np
        self.name = view.name
        self.origin = np.array(view.origin, dtype=np.float64)
        self.forward, self.left, self.up = (np.array(x, dtype=np.float64) for x in (view.forward, view.left, view.up))
        self.rt = np.stack([self.forward, self.left, self.up], axis=1)
        self.w = self.fw = w
        self.h = self.fh = h
        self.fx, self.fy = w * 0.5 / view.tanx, h * 0.5 / view.tany
        self.cx, self.cy = w * 0.5, h * 0.5
        self.near_clip = 1.0

    def view(self, points):
        import numpy as np
        return (np.asarray(points, dtype=np.float64) - self.origin) @ self.rt


def _frame(view, w, h):
    return _Frame(view, w, h)


# ---------------------------------------------------------------- cull distances by size (no popping)
def size_cull(radius, pop_pixels=30, tanx=TAN_HALF[0], width=1920):
    """The distance beyond which a sphere of this radius covers fewer than pop_pixels of a 1920 x 1080 frame
    (pi (f r / d)^2 = pop_pixels). A prop culled there cannot vanish visibly: what is gone was smaller than that."""
    f = width * 0.5 / tanx
    return int(math.ceil(f * radius * math.sqrt(math.pi / pop_pixels)))


def cmd_cull_distances(a):
    import sqlite3
    db = sqlite3.connect(a.models)
    half = {}
    for name, x0, y0, z0, x1, y1, z1 in db.execute('SELECT name, bmin_x, bmin_y, bmin_z, bmax_x, bmax_y, bmax_z FROM models'):
        if x0 is not None:
            half[name] = 0.5 * math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
    donor = {}
    for m, c in db.execute('SELECT model, cullDist FROM smodels ORDER BY i'):
        donor.setdefault(m, c)
    out, changed, unknown, dist = [], 0, 0, []
    for line in open(a.smodels, encoding='utf-8'):
        body = line.rstrip('\n')
        parts = body.split('#')[0].split()
        if len(parts) < 8:
            out.append(body)
            continue
        flags = [f for f in parts[8:] if not f.startswith('cull=')]
        r = half.get(parts[0])
        if r is None:
            unknown += 1
            out.append(body)
            continue
        c = min(65535, size_cull(r * float(parts[7]), a.pop_pixels))
        if a.keep_longer and donor.get(parts[0]):
            c = max(c, int(donor[parts[0]]))
        dist.append(c)
        changed += 1
        out.append(' '.join(parts[:8] + flags + ['cull=%d' % c]))
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    dist.sort()
    print('%d props given a cull distance (%d without a known model kept as they were); median %d, p10 %d, p90 %d -> %s' % (
        changed, unknown, dist[len(dist) // 2] if dist else 0, dist[len(dist) // 10] if dist else 0, dist[int(len(dist) * .9)] if dist else 0, a.out))
    return 0


# ---------------------------------------------------------------- views (a client plan)
def cmd_views(a):
    layout = json.load(open(a.layout, encoding='utf-8'))
    views = [v for v in door_views(layout, back=(a.back,), turns=(0.0,))]
    if a.limit:
        step = max(1, len(views) // a.limit)
        views = views[::step][:a.limit]
    steps = [{'on': False, 'do': 'waves'}, {'on': True, 'do': 'ignore'}, {'do': 'doors'},
             {'name': 'cg_draw2D', 'value': '0', 'do': 'dvar'}, {'name': 'cg_drawGun', 'value': '0', 'do': 'dvar'}]
    for v in views:
        feet = (v['origin'][0], v['origin'][1], v['origin'][2] - 60.0)          # tp places the feet; the eye is 60 above
        steps += [{'do': 'tp', 'at': [round(x, 1) for x in feet], 'yaw': round(v['yaw'], 1), 'pitch': round(v['pitch'], 1), 'snap': False},
                  {'do': 'freeze', 'on': True}, {'do': 'wait', 's': 0.6},
                  {'do': 'capture', 'name': ('dv_%s' % re.sub(r'[^a-z0-9_]', '_', v['name'].lower()))[:40], 'depth': True, 'pause': 0.2},
                  {'do': 'freeze', 'on': False}]
    plan = {'schema': 'iw7.gamelab-plan/1', 'name': a.name, 'map': layout.get('map', 'cp_iwz'), 'resolution': [1920, 1080], 'steps': steps}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=1)
    print('%d door views -> %s' % (len(views), a.out))
    return 0


# ---------------------------------------------------------------- frames (the game's depth)
def cmd_frames(a):
    import glob
    import numpy as np
    import iw7_see as S
    tome, smodels, d = load_world(a.gfxmap)
    sm = tome.by_class(1)
    scene = S.Scene(a.db)
    cams = sorted(glob.glob(os.path.join(a.run, '**', 'see-iwz_%s*.json' % a.prefix), recursive=True))
    rows, total_exp, total_drawn, total_absent, absent_list, pops = [], 0, 0, 0, [], []
    for cpath in cams:
        try:
            fr = S.Frame(cpath)
        except S.SeeError as e:
            print('skip', cpath, e)
            continue
        if fr.z_buffer() is None:
            continue
        zs, ids = scene.render(fr, cull=False)
        ze = fr.z_buffer()
        c = S.classify(ze, zs)
        view = View(tuple(fr.origin), tuple(fr.forward), tuple(fr.left), tuple(fr.up), fr.tanx, fr.tany, fr.name)
        u = np.unique(ids[ids > 0])
        exp = drawn = absent = culled_drawn = culled = 0
        for i in u:
            p = int(i) - 1
            m = ids == i
            n = int(m.sum())
            if n < a.min_pixels:
                continue
            same = int(((c == 0) & m).sum())
            farther = int(((c == 2) & m).sum())
            keep = all(tome_keeps(tome, sm[p], view)) if p in sm else True
            # Umbra keeps or drops a whole object: a culled prop shows (almost) none of its own depth. A prop partly
            # drawn (a mesh part the offline mesh holds and the game does not) is drawn, not culled.
            is_drawn = same >= max(5, 0.02 * n)
            is_absent = not is_drawn and farther >= 0.7 * n
            if p in sm and box_nearest_sq(tome.bounds[sm[p]], view.origin) < 16.0 ** 2:
                continue          # the camera stands in or against the prop: its faces are seen from behind
            if keep:
                exp += 1
                drawn += is_drawn
                if is_absent:
                    absent += 1
                    absent_list.append({'frame': fr.name, 'prop': p, 'model': scene.p_model[scene.row_of[p]], 'pixels': n, 'farther': farther})
            else:
                culled += 1
                culled_drawn += is_drawn
                if n * (1920.0 * 1080.0) / (fr.w * fr.h) >= a.pop_pixels:
                    pops.append({'frame': fr.name, 'prop': p, 'model': scene.p_model[scene.row_of[p]], 'pixels_1080': round(n * (1920.0 * 1080.0) / (fr.w * fr.h))})
        total_exp += exp
        total_drawn += drawn
        total_absent += absent
        rows.append({'frame': fr.name, 'props_expected': exp, 'drawn': drawn, 'absent': absent, 'tome_culled_in_raster': culled,
                     'tome_culled_but_drawn': culled_drawn})
    out = {'frames': len(rows), 'props_expected': total_exp, 'drawn': total_drawn, 'absent': total_absent,
           'absent_props': absent_list[:100], 'pops': pops[:100], 'per_frame': rows,
           'verdict': 'pass' if rows and not total_absent and not pops else 'fail'}
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
    for r in rows:
        print('%-40s expected %4d drawn %4d absent %3d  tome-culled %4d (drawn anyway %d)' % (
            r['frame'], r['props_expected'], r['drawn'], r['absent'], r['tome_culled_in_raster'], r['tome_culled_but_drawn']))
    print('frames %d, props expected %d, drawn %d, absent %d, distance-culled on %d+ pixels %d' % (len(rows), total_exp, total_drawn, total_absent, a.pop_pixels, len(pops)))
    print('VERDICT', out['verdict'])
    return 0 if out['verdict'] == 'pass' else 1


# ---------------------------------------------------------------- model (perfzones views, no game)
def cmd_model(a):
    tome, smodels, d = load_world(a.gfxmap)
    sm = tome.by_class(1)
    rows = []
    for line in open(a.log, errors='replace'):
        m = re.search(r'GL PERFZONE i=\d+ name=(\S+) at=\(([-\d.]+), ([-\d.]+), ([-\d.]+)\) yaw=([-\d.]+)', line)
        if not m:
            continue
        o = (float(m.group(2)), float(m.group(3)), float(m.group(4)) + 60.0)
        for yaw, tag in ((float(m.group(5)), 'a'), (float(m.group(5)) + 180.0, 'b')):
            view = View.from_yaw_pitch(o, yaw, 0.0)
            fr = sum(1 for k in range(len(smodels)) if k in sm and view.box_in(tome.bounds[sm[k]]))
            kept = sum(1 for k in range(len(smodels)) if k in sm and all(tome_keeps(tome, sm[k], view)))
            rows.append((m.group(1) + '_' + tag, fr, kept))
    for r in rows:
        print('%-22s frustum %5d  frustum+distance %5d' % r)
    ks = sorted(r[2] for r in rows)
    print('static models %d; per view kept: median %d, max %d' % (len(smodels), ks[len(ks) // 2], ks[-1]))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('read')
    r.add_argument('gfxmap')
    c = sub.add_parser('check')
    c.add_argument('gfxmap')
    c.add_argument('--db', required=True)
    c.add_argument('--layout', required=True)
    c.add_argument('--json')
    c.add_argument('--size', type=int, nargs=2, default=(480, 270))
    c.add_argument('--min-pixels', type=int, default=2)
    c.add_argument('--pop-pixels', type=int, default=30, help='a distance-culled prop seen on this many 1080p pixels or more pops')
    c.add_argument('--allow-distance-pops', action='store_true', help='report popping props without failing')
    c.add_argument('--allow-conservative', action='store_true', help='accept scene-sized boxes (IWZ_TOME=conservative builds)')
    v = sub.add_parser('views')
    v.add_argument('--layout', required=True)
    v.add_argument('--out', required=True)
    v.add_argument('--name', default='tf5_door_views')
    v.add_argument('--back', type=float, default=160.0)
    v.add_argument('--limit', type=int, default=0)
    f = sub.add_parser('frames')
    f.add_argument('run')
    f.add_argument('--db', required=True)
    f.add_argument('--gfxmap', required=True)
    f.add_argument('--prefix', default='dv_')
    f.add_argument('--min-pixels', type=int, default=30)
    f.add_argument('--pop-pixels', type=int, default=30)
    f.add_argument('--json')
    k = sub.add_parser('cull-distances')
    k.add_argument('smodels')
    k.add_argument('--models', required=True, help='worldkit database of the template map (models table)')
    k.add_argument('--out', required=True)
    k.add_argument('--pop-pixels', type=int, default=30)
    k.add_argument('--keep-longer', action='store_true', help='keep the template instance''s cull distance when it is longer')
    m = sub.add_parser('model')
    m.add_argument('gfxmap')
    m.add_argument('--log', required=True)
    a = p.parse_args(argv)
    try:
        return {'read': cmd_read, 'check': cmd_check, 'cull-distances': cmd_cull_distances, 'views': cmd_views, 'frames': cmd_frames, 'model': cmd_model}[a.cmd](a)
    except (ValueError, OSError) as e:
        print('refused: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
