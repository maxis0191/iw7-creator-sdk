"""iw7_see: what a captured frame of the game shows, as data.

A lab client writes, with every frame capture, the exact camera of that frame (see-<name>.json, schema
iw7.see-camera/1) and, on request, the engine's depth buffer of the same present (<name>__z.bmp). This tool joins
them with the world database (iw7_world.py) and the models of the dump:

    index    read the models of the dump once (the props' triangles) into <db>.models.npz
    camera   the camera of a frame, and whether it agrees with the engine's own projection
    at       what is at a pixel: world position, distance, and the prop or surface (or "dynamic or unknown")
    project  where a world point falls in the frame and whether it is hidden
    visible  how many pixels of a prop, a model or a point are seen, and what fraction is hidden
    objects  the table of what the frame shows; things in front that are not in the map; things that are missing
    floor    height of a point (or of what a pixel shows) above the surface under it
    compare  what appeared or disappeared between two frames of the same camera
    fit      the depth convention measured on a frame (device depth against the database)

Conventions: world units; the camera axes are forward, left, up; a pixel (x, y) has x to the right and y down, its
centre at (x + 0.5, y + 0.5); "z" is the distance along the camera's forward axis, "distance" the straight line.
Needs numpy. Exit code 2 with a message on stderr for every refusal.
"""
import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iw7_world as world  # noqa: E402
from iw7_dump import WorldError  # noqa: E402

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

CAMERA_SCHEMAS = ('iw7.see-camera/1', 'iw7.see-camera/2')    # /1: the camera written out; /2: the engine's projection of points
# The engine's depth convention, measured on Spaceland (docs/SEE.md): device depth = DEPTH_A + DEPTH_B / z
DEPTH_A, DEPTH_B = 0.0, 3.9375
MESH_VERSION = 2
NOTHING = 0              # id buffer: 0 nothing, prop i -> i + 1, surface j -> -(j + 1)
FAR = 1e30


class SeeError(WorldError):
    pass


def need_numpy():
    if np is None:
        raise SeeError('iw7_see needs numpy')


def prop_id(i):
    return int(i) + 1


def surface_id(j):
    return -(int(j) + 1)


# ---------------------------------------------------------------- model files of a dump (rigid meshes only)
def _blob(data, off, width, what):
    """One counted array of the dump stream: kind byte 8, presence byte, u32 count, count * width bytes."""
    if off + 2 > len(data) or data[off] != 8:
        raise SeeError('%s: array marker expected at byte %d' % (what, off))
    if data[off + 1] == 0:
        return b'', 0, off + 2
    count = struct.unpack_from('<I', data, off + 2)[0]
    end = off + 6 + count * width
    if end > len(data):
        raise SeeError('%s: array of %d leaves the file' % (what, count))
    return data[off + 6:end], count, end


def read_xsb(data, what='xsb'):
    """Vertices (N, 3) and triangles (M, 3) of every surface of one model-surfaces file, joined."""
    outer, count, off = _blob(data, 0, 56, what)
    if count != 1:
        raise SeeError('%s: one surface set expected' % what)
    surfaces = struct.unpack_from('<H', outer, 16)[0]
    if data[off] != 6 or data[off + 1] != 1:
        raise SeeError('%s: name expected' % what)
    off = data.index(b'\0', off + 2) + 1
    heads, n, off = _blob(data, off, 256, what)
    if n != surfaces or not n:
        raise SeeError('%s: %d surface records for %d surfaces' % (what, n, surfaces))
    sizes = [struct.unpack_from('<HHH', heads, 256 * k) for k in range(n)]
    verts, tris, base = [], [], 0
    for k, (flags, vc, tc) in enumerate(sizes):
        sig_v = b'\x08\x01' + struct.pack('<I', vc)
        sig_t = b'\x08\x01' + struct.pack('<I', tc)
        # the arrays after the triangles of the previous surface have widths this reader does not know: find the
        # next vertex array by its count followed, exactly 32 bytes a vertex later, by the triangle array's count
        at = off
        while True:
            at = data.find(sig_v, at)
            if at < 0:
                raise SeeError('%s: vertices of surface %d not found (flags 0x%X)' % (what, k, flags))
            t_at = at + 6 + 32 * vc
            if data[t_at:t_at + 6] == sig_t and t_at + 6 + 6 * tc <= len(data):
                break
            at += 1
        v = np.frombuffer(data, dtype='<f4', count=vc * 8, offset=at + 6).reshape(vc, 8)[:, :3]
        t = np.frombuffer(data, dtype='<u2', count=tc * 3, offset=t_at + 6).reshape(tc, 3).astype(np.int32)
        if tc and int(t.max()) >= vc:
            raise SeeError('%s: surface %d has a triangle index beyond its vertices' % (what, k))
        verts.append(v.astype(np.float32))
        tris.append(t + base)
        base += vc
        off = t_at + 6 + 6 * tc
    return np.concatenate(verts), np.concatenate(tris)


def model_mesh(dump_dir, name):
    """Highest-detail mesh of a model: the first surfaces file its model file names. -> (verts, tris)."""
    path = os.path.join(dump_dir, 'xmodel', name + '.xmb')
    if not os.path.isfile(path):
        raise SeeError('no model file for %s' % name)
    with open(path, 'rb') as f:
        data = f.read()
    for m in re.finditer(rb'[\x21-\x7e]{3,}', data):
        text = m.group().decode('ascii')
        if text == name:
            continue
        surf = os.path.join(dump_dir, 'xsurface', text + '.xsb')
        if os.path.isfile(surf):
            with open(surf, 'rb') as f:
                return read_xsb(f.read(), text)
    raise SeeError('model %s names no surfaces file of the dump' % name)


def mesh_cache_path(db_path):
    return db_path + '.models.npz'


def build_index(db_path, dump_dir, log=print):
    """Reads every model the map places; writes <db>.models.npz. Returns the report."""
    need_numpy()
    w = world.World(db_path)
    names = [r['name'] for r in w.q('SELECT name FROM models ORDER BY name')]
    if not names:
        names = [r['model'] for r in w.q('SELECT DISTINCT model FROM smodels ORDER BY model')]
    cat = {r['name']: r for r in w.q('SELECT * FROM models')}
    verts, tris, table, failed, worst = [], [], [], [], (0.0, '')
    vbase = tbase = 0
    for name in names:
        try:
            v, t = model_mesh(dump_dir, name)
        except (SeeError, ValueError, struct.error, IndexError) as e:
            failed.append((name, str(e)))
            continue
        c = cat.get(name)
        if c and c.get('in_catalog') and c.get('bmin_x') is not None and len(v):
            lo, hi = v.min(0), v.max(0)
            d = max(abs(float(lo[0]) - c['bmin_x']), abs(float(lo[1]) - c['bmin_y']), abs(float(lo[2]) - c['bmin_z']),
                    abs(float(hi[0]) - c['bmax_x']), abs(float(hi[1]) - c['bmax_y']), abs(float(hi[2]) - c['bmax_z']))
            if d > worst[0]:
                worst = (d, name)
        table.append((name, vbase, len(v), tbase, len(t)))
        verts.append(v)
        tris.append(t)
        vbase += len(v)
        tbase += len(t)
    np.savez(mesh_cache_path(db_path), version=np.array([MESH_VERSION]), names=np.array([r[0] for r in table]),
             spans=np.array([r[1:] for r in table], dtype=np.int64).reshape(-1, 4),
             verts=np.concatenate(verts) if verts else np.zeros((0, 3), np.float32),
             tris=np.concatenate(tris) if tris else np.zeros((0, 3), np.int32))
    report = {'models': len(names), 'read': len(table), 'failed': [{'model': n, 'why': e} for n, e in failed],
              'vertices': vbase, 'triangles': tbase, 'worst_bounds_difference': {'units': round(worst[0], 3), 'model': worst[1]},
              'file': mesh_cache_path(db_path)}
    w.con.close()
    return report


# ---------------------------------------------------------------- the frame: camera, depth
def _rq(m):
    """m = k @ r with k upper triangular (positive diagonal) and r a rotation."""
    q, r = np.linalg.qr(np.flipud(m).T)
    k = np.fliplr(np.flipud(r.T))
    rot = np.flipud(q.T)
    sign = np.diag(np.sign(np.diag(k)))
    return k @ sign, sign @ rot


def solve_camera(pairs):
    """The camera from the engine's projection of world points ([x, y, z, screen x, screen y] rows).
    -> dict origin, forward, left, up, fx, fy, cx, cy (screen units), points, used, worst and median error in screen units."""
    pts = np.asarray(pairs, dtype=np.float64).reshape(-1, 5)
    if len(pts) < 12:
        raise SeeError('the camera file holds %d projected points; 12 or more are needed (was the client in a map?)' % len(pts))
    world, screen = pts[:, :3], pts[:, 3:5]
    wc, ws = world.mean(0), max(1.0, float(np.abs(world - world.mean(0)).max()))
    sc, ss = screen.mean(0), max(1.0, float(np.abs(screen - screen.mean(0)).max()))
    xn, un = (world - wc) / ws, (screen - sc) / ss
    keep = np.ones(len(pts), dtype=bool)
    proj = None
    for _ in range(5):
        x, u = xn[keep], un[keep]
        n = len(x)
        a = np.zeros((2 * n, 12))
        hom = np.concatenate([x, np.ones((n, 1))], axis=1)
        a[0::2, 0:4] = hom
        a[0::2, 8:12] = -u[:, 0:1] * hom
        a[1::2, 4:8] = hom
        a[1::2, 8:12] = -u[:, 1:2] * hom
        proj = np.linalg.svd(a)[2][-1].reshape(3, 4)
        hom_all = np.concatenate([xn, np.ones((len(xn), 1))], axis=1) @ proj.T
        if np.median(hom_all[keep, 2]) < 0:
            proj, hom_all = -proj, -hom_all
        with np.errstate(divide='ignore', invalid='ignore'):
            err = np.linalg.norm(hom_all[:, :2] / hom_all[:, 2:3] - un, axis=1) * ss
        err[~np.isfinite(err) | (hom_all[:, 2] <= 0)] = np.inf
        limit = max(0.05, 6.0 * float(np.median(err[keep])))
        new = err <= limit
        if new.sum() < 12 or (new == keep).all():
            break
        keep = new
    # back to world and screen units: screen = T_s^-1 . proj . T_w
    t_w = np.array([[1 / ws, 0, 0, -wc[0] / ws], [0, 1 / ws, 0, -wc[1] / ws], [0, 0, 1 / ws, -wc[2] / ws], [0, 0, 0, 1]])
    t_s = np.array([[ss, 0, sc[0]], [0, ss, sc[1]], [0, 0, 1]])
    full = t_s @ proj @ t_w
    m = full[:, :3]
    if np.linalg.det(m) < 0:
        full, m = -full, -m
    origin = -np.linalg.solve(m, full[:, 3])
    k, rot = _rq(m)
    k = k / k[2, 2]
    if np.linalg.det(rot) < 0:
        raise SeeError('the projected points do not describe a camera')
    good = err[keep]
    return {'origin': origin, 'forward': rot[2], 'left': -rot[0], 'up': -rot[1], 'fx': float(k[0, 0]), 'fy': float(k[1, 1]),
            'cx': float(k[0, 2]), 'cy': float(k[1, 2]), 'skew': float(k[0, 1]), 'points': int(len(pts)), 'used': int(keep.sum()),
            'worst': float(good.max()), 'median': float(np.median(good))}


class Frame:
    def __init__(self, path, depth_model=None):
        need_numpy()
        self.json_path = find_camera_file(path)
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.doc = json.load(f)
        if self.doc.get('schema') not in CAMERA_SCHEMAS:
            raise SeeError('%s is not a camera file (%s)' % (self.json_path, ' or '.join(CAMERA_SCHEMAS)))
        self.name = self.doc.get('name', '')
        self.fw, self.fh = int(self.doc['frame']['width']), int(self.doc['frame']['height'])
        self.near = 0.0
        self.solved = self.solved_other = None
        if self.doc['schema'].endswith('/1'):
            cam = self.doc['camera']
            self.origin = np.array(cam['origin'], dtype=np.float64)
            axis = np.array(cam['axis'], dtype=np.float64)
            tanx, tany = float(cam['tan_half_fov'][0]), float(cam['tan_half_fov'][1])
            if not (tanx > 0 and tany > 0) or abs(float(np.linalg.det(axis)) - 1.0) > 1e-3:
                raise SeeError('%s: the camera is not a camera (tangents %s, axis determinant %.4f)' % (
                    self.json_path, cam['tan_half_fov'], float(np.linalg.det(axis))))
            self.forward, self.left, self.up = axis[0], axis[1], axis[2]
            self.near = float(cam.get('z_near') or 0.0)
            # focal lengths and centre in frame pixels
            ffx, ffy, fcx, fcy = self.fw * 0.5 / tanx, self.fh * 0.5 / tany, self.fw * 0.5, self.fh * 0.5
        else:
            self.solved = solve_camera(self.doc.get('projection_at_request') or [])
            other = self.doc.get('projection_after') or []
            if len(other) >= 12:
                self.solved_other = solve_camera(other)
            c = self.solved
            self.origin, self.forward, self.left, self.up = c['origin'], c['forward'], c['left'], c['up']
            ffx, ffy, fcx, fcy = c['fx'], c['fy'], c['cx'], c['cy']
        self.rt = np.stack([self.forward, self.left, self.up], axis=1)      # world offset @ rt -> (f, l, u)
        self.depth = None
        self.depth_file = None
        rows = self.doc.get('depth') or []
        if rows:
            p = find_beside(self.json_path, rows[0]['file'])
            if p:
                self.depth, w, h = read_float_bmp(p)
                self.depth_file = p
                self.set_size(w, h, ffx, ffy, fcx, fcy)
        if self.depth is None:
            self.set_size(self.fw, self.fh, ffx, ffy, fcx, fcy)
        self._frame_lens = (ffx, ffy, fcx, fcy)
        self.depth_model = depth_model or ({'a': 0.0, 'b': self.near} if self.near > 0 else {'a': DEPTH_A, 'b': DEPTH_B})
        self.near_clip = self.depth_model['b'] if self.depth_model['b'] > 0 else 1.0
        self._z = None

    def set_size(self, w, h, ffx=None, ffy=None, fcx=None, fcy=None):
        """The pixel grid the answers are computed on (the depth buffer's, or the frame's when there is no depth)."""
        if ffx is None:
            ffx, ffy, fcx, fcy = self._frame_lens
        self.w, self.h = int(w), int(h)
        sx, sy = self.w / float(self.fw), self.h / float(self.fh)
        self.fx, self.fy, self.cx, self.cy = ffx * sx, ffy * sy, fcx * sx, fcy * sy
        self.tanx, self.tany = self.w * 0.5 / self.fx, self.h * 0.5 / self.fy

    # frame pixel -> depth-buffer pixel (the scene can be rendered at another size than the window)
    def to_depth_pixel(self, x, y):
        return x * self.w / float(self.fw), y * self.h / float(self.fh)

    def moved(self):
        """Largest change of the camera between the request and just after the frame was taken (None: not recorded)."""
        a, b = self.solved, self.solved_other
        if a is None or b is None:
            return None
        return {'origin': float(np.abs(a['origin'] - b['origin']).max()),
                'axis': float(max(np.abs(a[k] - b[k]).max() for k in ('forward', 'left', 'up')))}

    def view(self, points):
        return (np.asarray(points, dtype=np.float64) - self.origin) @ self.rt

    def project(self, points):
        """World points -> (x, y, z) in depth-buffer pixels; z <= 0 is behind the camera."""
        v = self.view(points)
        f = v[..., 0]
        safe = np.where(np.abs(f) < 1e-9, 1e-9, f)
        x = self.cx - self.fx * v[..., 1] / safe
        y = self.cy - self.fy * v[..., 2] / safe
        return x, y, f

    def ray(self, x, y):
        """Unit direction through the depth-buffer point (x, y), and the forward distance per unit of length."""
        d = self.forward + self.left * ((self.cx - x) / self.fx) + self.up * ((self.cy - y) / self.fy)
        n = float(np.linalg.norm(d))
        return d / n, 1.0 / n

    def unproject(self, x, y, z):
        return self.origin + z * (self.forward + self.left * ((self.cx - x) / self.fx) + self.up * ((self.cy - y) / self.fy))

    def z_buffer(self):
        """Forward distance per pixel from the engine's depth; FAR where nothing was drawn."""
        if self.depth is None:
            return None
        if self._z is None:
            self._z = device_to_z(self.depth, self.depth_model)
        return self._z

    def z_at(self, x, y):
        zb = self.z_buffer()
        if zb is None:
            return None
        xi, yi = int(math.floor(x)), int(math.floor(y))
        if not (0 <= xi < self.w and 0 <= yi < self.h):
            return None
        return float(zb[yi, xi])


def find_camera_file(path):
    if os.path.isdir(path):
        raise SeeError('%s is a folder; give the frame (.bmp) or its see-<name>.json' % path)
    if path.lower().endswith('.json'):
        if not os.path.isfile(path):
            raise SeeError('camera file not found: %s' % path)
        return path
    folder, stem = os.path.dirname(os.path.abspath(path)), os.path.splitext(os.path.basename(path))[0]
    for cand in (os.path.join(folder, 'see-%s.json' % stem), os.path.join(folder, 'perf', 'see-%s.json' % stem)):
        if os.path.isfile(cand):
            return cand
    raise SeeError('no camera file for %s (looked for see-%s.json beside it and in perf/). The frame was not taken '
                   'by a lab client that records the camera' % (path, stem))


def find_beside(json_path, name):
    folder = os.path.dirname(os.path.abspath(json_path))
    for cand in (os.path.join(folder, name), os.path.join(os.path.dirname(folder), name)):
        if os.path.isfile(cand):
            return cand
    return None


def read_float_bmp(path):
    """A 32-bit BMP whose four bytes per pixel are one float (the depth file). -> (array (h, w), w, h)."""
    with open(path, 'rb') as f:
        data = f.read()
    if data[:2] != b'BM' or len(data) < 54:
        raise SeeError('%s is not a BMP' % path)
    off = struct.unpack_from('<I', data, 10)[0]
    w, h = struct.unpack_from('<ii', data, 18)
    bits = struct.unpack_from('<H', data, 28)[0]
    if bits != 32 or w <= 0 or h == 0 or off + 4 * w * abs(h) > len(data):
        raise SeeError('%s is not a 32-bit depth BMP' % path)
    a = np.frombuffer(data, dtype='<f4', count=w * abs(h), offset=off).reshape(abs(h), w)
    if h > 0:
        a = a[::-1]
    return a, w, abs(h)


def write_float_bmp(path, array):
    h, w = array.shape
    head = b'BM' + struct.pack('<IHHI', 54 + 4 * w * h, 0, 0, 54) + struct.pack('<IiiHHIIiiII', 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(head + np.ascontiguousarray(array, dtype='<f4').tobytes())


def device_to_z(depth, model):
    """device = a + b / z  ->  z = b / (device - a). Values that give no positive distance become FAR."""
    d = depth.astype(np.float64) - model['a']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = model['b'] / d
    z[~np.isfinite(z) | (z <= 0) | (z > FAR)] = FAR
    return z


def z_to_device(z, model):
    with np.errstate(divide='ignore'):
        return np.where(z >= FAR, model['a'], model['a'] + model['b'] / z)


def tolerance(z):
    """Depth agreement: 2 units, or 1.5 % of the distance when that is more (precision and the engine's lower detail far away)."""
    return np.maximum(2.0, 0.015 * z)


# ---------------------------------------------------------------- the static world: surfaces and props
class Scene:
    def __init__(self, db_path, boxes=False):
        need_numpy()
        self.w = world.World(db_path)
        self.db_path = db_path
        m = self.w.meta
        mesh_file = os.path.join(os.path.dirname(os.path.abspath(db_path)), m['mesh_file'])
        zones = {r['zone']: r for r in self.w.q('SELECT zone, vertex_count, offset FROM mesh_zones')}
        raw = np.fromfile(mesh_file, dtype=np.uint8)
        size = world.dump.VERTEX_SIZE
        zone_verts = {}
        for z, r in zones.items():
            block = raw[r['offset']:r['offset'] + r['vertex_count'] * size]
            zone_verts[z] = np.frombuffer(block.tobytes(), dtype='<f4').reshape(r['vertex_count'], size // 4)[:, :3]
        idx_all = np.frombuffer(raw[m['mesh_index_offset']:].tobytes(), dtype='<u2')
        surf = self.w.q('SELECT i, material, tri_count, first_vertex, base_index, transientZone FROM surfaces ORDER BY i')
        self.materials = {s['i']: s['material'] for s in surf}
        # surfaces of the map's brush models (doors and other parts a script can move or remove); model 0 is the fixed world
        self.movable = {}
        for b in self.w.q('SELECT i, startSurfIndex, surfaceCount FROM brush_models WHERE i > 0 AND surfaceCount > 0'):
            if b['startSurfIndex'] is not None and b['startSurfIndex'] < len(surf) + 1000000:
                for j in range(b['startSurfIndex'], b['startSurfIndex'] + b['surfaceCount']):
                    self.movable[j] = b['i']
        # the sky is a surface of the map that writes no depth: it is left out, so "nothing drawn" there is expected
        self.sky = sorted(s['i'] for s in surf if is_sky(s['material']))
        tri_pos, tri_id = [], []
        for s in surf:
            n = s['tri_count'] * 3
            if not n or is_sky(s['material']):
                continue
            idx = idx_all[s['base_index']:s['base_index'] + n].astype(np.int64) + s['first_vertex']
            tri_pos.append(zone_verts[s['transientZone']][idx].reshape(-1, 3, 3))
            tri_id.append(np.full(s['tri_count'], surface_id(s['i']), dtype=np.int32))
        self.s_tris = np.concatenate(tri_pos).astype(np.float64) if tri_pos else np.zeros((0, 3, 3))
        self.s_ids = np.concatenate(tri_id) if tri_id else np.zeros(0, np.int32)
        cols = 'i, model, x, y, z, a00, a01, a02, a10, a11, a12, a20, a21, a22, scale, cullDist, bmid_x, bmid_y, bmid_z, bhalf_x, bhalf_y, bhalf_z'
        rows = self.w.con.execute('SELECT %s FROM smodels ORDER BY i' % cols).fetchall()
        self.p_index = np.array([r[0] for r in rows], dtype=np.int64)
        self.p_model = [r[1] for r in rows]
        num = np.array([r[2:] for r in rows], dtype=np.float64).reshape(len(rows), 20)
        self.p_origin = num[:, 0:3]
        self.p_axis = num[:, 3:12].reshape(-1, 3, 3)
        self.p_scale = num[:, 12]
        self.p_cull = num[:, 13]
        self.p_mid = num[:, 14:17]
        self.p_half = num[:, 17:20]
        self.p_radius = np.linalg.norm(self.p_half, axis=1)
        self.row_of = {int(i): k for k, i in enumerate(self.p_index)}
        self.meshes = {}
        self.have_meshes = False
        cache = mesh_cache_path(db_path)
        if not boxes and os.path.isfile(cache):
            z = np.load(cache, allow_pickle=False)
            if int(z['version'][0]) == MESH_VERSION:
                verts, tris = z['verts'], z['tris']
                for name, (vb, vn, tb, tn) in zip(z['names'].tolist(), z['spans'].tolist()):
                    self.meshes[name] = (verts[vb:vb + vn].astype(np.float64), tris[tb:tb + tn])
                self.have_meshes = True

    # triangles of prop rows (world space) ------------------------------------------------------------
    def prop_tris(self, rows):
        """Yields (world triangles (T, 3, 3), ids (T,)) for the given prop rows, grouped by model."""
        rows = np.asarray(rows, dtype=np.int64)
        if not len(rows):
            return
        by_model = {}
        for k in rows:
            by_model.setdefault(self.p_model[k], []).append(int(k))
        for name, ks in by_model.items():
            ks = np.array(ks, dtype=np.int64)
            mesh = self.meshes.get(name)
            if mesh is None or not len(mesh[1]):
                # no mesh: the stored world-space bounding box stands in for the prop
                for k in ks:
                    yield box_tris(self.p_mid[k], self.p_half[k]), np.full(12, prop_id(self.p_index[k]), dtype=np.int32)
                continue
            v, t = mesh
            step = max(1, 400000 // max(1, len(t)))
            for a in range(0, len(ks), step):
                kk = ks[a:a + step]
                wv = np.einsum('nk,ikj->inj', v, self.p_axis[kk]) * self.p_scale[kk][:, None, None] + self.p_origin[kk][:, None, :]
                tri = wv[:, t, :].reshape(-1, 3, 3)
                ids = np.repeat((self.p_index[kk] + 1).astype(np.int32), len(t))
                yield tri, ids

    def name_of(self, ident):
        ident = int(ident)
        if ident > 0:
            k = self.row_of.get(ident - 1)
            if k is None:
                return {'kind': 'prop', 'prop': ident - 1}
            return {'kind': 'prop', 'prop': ident - 1, 'model': self.p_model[k], 'origin': [round(float(x), 2) for x in self.p_origin[k]],
                    'mesh': 'model' if self.p_model[k] in self.meshes else 'bounding box'}
        if ident < 0:
            j = -ident - 1
            out = {'kind': 'surface', 'surface': j, 'material': self.materials.get(j)}
            if j in self.movable:
                out['movable_brush_model'] = self.movable[j]
            return out
        return {'kind': 'nothing'}

    # ray cast ------------------------------------------------------------------------------------------
    def raycast(self, origin, direction, t_max=1e9, skip=()):
        """Every hit of the ray with the static world, nearest first: [(t, id, |normal . up|)]."""
        o = np.asarray(origin, dtype=np.float64)
        d = np.asarray(direction, dtype=np.float64)
        hits = []
        t, n = moller(o, d, self.s_tris)
        ok = np.isfinite(t) & (t <= t_max)
        hits += list(zip(t[ok].tolist(), self.s_ids[ok].tolist(), n[ok].tolist()))
        rel = self.p_mid - o
        along = rel @ d
        off2 = np.einsum('ij,ij->i', rel, rel) - along * along
        cand = np.nonzero((off2 <= (self.p_radius + 1.0) ** 2) & (along > -self.p_radius) & (along - self.p_radius <= t_max))[0]
        for tri, ids in self.prop_tris(cand):
            t, n = moller(o, d, tri)
            ok = np.isfinite(t) & (t <= t_max)
            hits += list(zip(t[ok].tolist(), ids[ok].tolist(), n[ok].tolist()))
        skip = set(skip)
        hits = [h for h in hits if h[1] not in skip]
        hits.sort()
        return hits

    # raster ----------------------------------------------------------------------------------------------
    def in_view(self, frame, max_z=None):
        """Rows of the props whose bounding sphere touches the view."""
        v = frame.view(self.p_mid)
        r = self.p_radius
        f = v[:, 0]
        # the half angles, a little wider than the frame so that an off-centre view loses nothing
        tx = max(frame.cx, frame.w - frame.cx) / frame.fx
        ty = max(frame.cy, frame.h - frame.cy) / frame.fy
        kx = math.sqrt(1.0 + tx ** 2)
        ky = math.sqrt(1.0 + ty ** 2)
        ok = (f + r > frame.near_clip) & (np.abs(v[:, 1]) <= f * tx + r * kx) & (np.abs(v[:, 2]) <= f * ty + r * ky)
        if max_z is not None:
            ok &= f - r <= max_z
        return np.nonzero(ok)[0]

    def render(self, frame, skip=(), only=None, cache_dir=None, cull=True):
        """The static world drawn from the frame's camera: (z per pixel, id per pixel). `only`: prop rows to draw alone."""
        key = None
        if cache_dir and only is None:
            h = hashlib.sha256()
            h.update(repr((frame.origin.tolist(), frame.rt.tolist(), frame.fx, frame.fy, frame.cx, frame.cy, frame.near_clip, frame.w, frame.h,
                           sorted(int(s) for s in skip), bool(cull), self.have_meshes, MESH_VERSION,
                           os.path.getmtime(self.db_path))).encode())
            key = os.path.join(cache_dir, 'see-raster-%s.npz' % h.hexdigest()[:24])
            if os.path.isfile(key):
                z = np.load(key)
                return z['z'], z['ids']
        zbuf = np.full(frame.w * frame.h, FAR, dtype=np.float64)
        ibuf = np.zeros(frame.w * frame.h, dtype=np.int32)
        skip_arr = np.array(sorted(int(s) for s in skip), dtype=np.int32)
        if only is None:
            tri, ids = self.s_tris, self.s_ids
            if len(skip_arr):
                keep = ~np.isin(ids, skip_arr)
                tri, ids = tri[keep], ids[keep]
            for a in range(0, len(tri), 200000):
                raster(frame.view(tri[a:a + 200000]), ids[a:a + 200000], zbuf, ibuf, frame)
            rows = self.in_view(frame)
            if cull:
                # the engine does not draw a prop beyond its cull distance (0 = no limit)
                dist = np.linalg.norm(self.p_origin[rows] - frame.origin, axis=1)
                rows = rows[(self.p_cull[rows] <= 0) | (dist <= self.p_cull[rows])]
            if len(skip_arr):
                rows = rows[~np.isin(self.p_index[rows] + 1, skip_arr)]
        else:
            rows = np.asarray(only, dtype=np.int64)
        for tri, ids in self.prop_tris(rows):
            raster(frame.view(tri), ids, zbuf, ibuf, frame)
        zbuf, ibuf = zbuf.reshape(frame.h, frame.w), ibuf.reshape(frame.h, frame.w)
        if key:
            os.makedirs(cache_dir, exist_ok=True)
            np.savez(key, z=zbuf, ids=ibuf)
        return zbuf, ibuf


def is_sky(material):
    name = (material or '').lower()
    return name.startswith('sky') or '/sky' in name


def box_tris(mid, half):
    c = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], dtype=np.float64) * half + mid
    quads = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
    return np.array([[c[q[0]], c[q[1]], c[q[2]]] for q in quads] + [[c[q[0]], c[q[2]], c[q[3]]] for q in quads])


def moller(o, d, tri):
    """Ray against triangles (T, 3, 3), both faces. -> (t per triangle, inf where missed; |normal z| of the triangle)."""
    if not len(tri):
        return np.zeros(0), np.zeros(0)
    v0 = tri[:, 0]
    e1 = tri[:, 1] - v0
    e2 = tri[:, 2] - v0
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    with np.errstate(divide='ignore', invalid='ignore'):
        inv = 1.0 / det
        s = o - v0
        u = np.einsum('ij,ij->i', s, p) * inv
        q = np.cross(s, e1)
        v = (q @ d) * inv
        t = np.einsum('ij,ij->i', e2, q) * inv
        ok = (np.abs(det) > 1e-12) & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1.0 + 1e-9) & (t > 1e-6)
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        nz = np.where(ln > 0, np.abs(n[:, 2]) / ln, 0.0)
    return np.where(ok, t, np.inf), nz


def _clip_near(tv, ids, near):
    """Triangles in view space (f, l, u) cut at f = near."""
    inside = tv[:, :, 0] >= near
    count = inside.sum(1)
    out_t, out_i = [tv[count == 3]], [ids[count == 3]]
    for want in (1, 2):
        m = count == want
        if not m.any():
            continue
        t, ins, idm = tv[m], inside[m], ids[m]
        # rotate so that the odd vertex (the one inside for 1, the one outside for 2) comes first
        first = np.argmax(ins if want == 1 else ~ins, axis=1)
        order = (first[:, None] + np.arange(3)[None, :]) % 3
        t = np.take_along_axis(t, order[:, :, None], axis=1)
        a, b, c = t[:, 0], t[:, 1], t[:, 2]
        with np.errstate(divide='ignore', invalid='ignore'):
            tb = ((near - a[:, 0]) / (b[:, 0] - a[:, 0]))[:, None]
            tc = ((near - a[:, 0]) / (c[:, 0] - a[:, 0]))[:, None]
        ab, ac = a + (b - a) * tb, a + (c - a) * tc
        if want == 1:
            out_t.append(np.stack([a, ab, ac], axis=1))
            out_i.append(idm)
        else:
            out_t.append(np.stack([ab, b, c], axis=1))
            out_t.append(np.stack([ab, c, ac], axis=1))
            out_i += [idm, idm]
    return np.concatenate(out_t), np.concatenate(out_i)


def raster(tv, ids, zbuf, ibuf, frame, budget=1500000):
    """Draws view-space triangles into the flat z and id buffers (nearest wins). Pixel centres are sampled."""
    if not len(tv):
        return
    w, h = frame.w, frame.h
    tv, ids = _clip_near(np.asarray(tv, dtype=np.float64), ids, frame.near_clip)
    if not len(tv):
        return
    f = tv[:, :, 0]
    sx = frame.cx - frame.fx * tv[:, :, 1] / f
    sy = frame.cy - frame.fy * tv[:, :, 2] / f
    iz = 1.0 / f
    x0 = np.maximum(np.ceil(sx.min(1) - 0.5), 0)
    x1 = np.minimum(np.floor(sx.max(1) - 0.5), w - 1)
    y0 = np.maximum(np.ceil(sy.min(1) - 0.5), 0)
    y1 = np.minimum(np.floor(sy.max(1) - 0.5), h - 1)
    area = (sx[:, 1] - sx[:, 0]) * (sy[:, 2] - sy[:, 0]) - (sy[:, 1] - sy[:, 0]) * (sx[:, 2] - sx[:, 0])
    keep = (x1 >= x0) & (y1 >= y0) & (np.abs(area) > 1e-9) & np.isfinite(area)
    if not keep.any():
        return
    sx, sy, iz, ids, area = sx[keep], sy[keep], iz[keep], ids[keep], area[keep]
    x0, x1, y0, y1 = (v[keep].astype(np.int64) for v in (x0, x1, y0, y1))
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    kx = np.ceil(np.log2(bw)).astype(np.int64)
    ky = np.ceil(np.log2(bh)).astype(np.int64)
    for key in np.unique(kx * 64 + ky):
        sel = np.nonzero(kx * 64 + ky == key)[0]
        gw, gh = min(w, 1 << int(key // 64)), min(h, 1 << int(key % 64))
        ax = np.arange(gw)[None, None, :]
        ay = np.arange(gh)[None, :, None]
        step = max(1, budget // (gw * gh))
        for a in range(0, len(sel), step):
            c = sel[a:a + step]
            gx = x0[c][:, None, None] + ax
            gy = y0[c][:, None, None] + ay
            px, py = gx + 0.5, gy + 0.5
            ax_, ay_ = sx[c, 0][:, None, None], sy[c, 0][:, None, None]
            bx_, by_ = sx[c, 1][:, None, None], sy[c, 1][:, None, None]
            cx_, cy_ = sx[c, 2][:, None, None], sy[c, 2][:, None, None]
            inv = (1.0 / area[c])[:, None, None]
            wc = ((bx_ - ax_) * (py - ay_) - (by_ - ay_) * (px - ax_)) * inv
            wa = ((cx_ - bx_) * (py - by_) - (cy_ - by_) * (px - bx_)) * inv
            wb = 1.0 - wa - wc
            m = (wa >= -1e-9) & (wb >= -1e-9) & (wc >= -1e-9) & (gx <= x1[c][:, None, None]) & (gy <= y1[c][:, None, None])
            if not m.any():
                continue
            izp = wa * iz[c, 0][:, None, None] + wb * iz[c, 1][:, None, None] + wc * iz[c, 2][:, None, None]
            pix = (gy * w + gx)[m]
            zf = 1.0 / izp[m]
            idf = np.broadcast_to(ids[c][:, None, None], m.shape)[m]
            nearer = zf < zbuf[pix]
            pix, zf, idf = pix[nearer], zf[nearer], idf[nearer]
            order = np.argsort(-zf, kind='stable')          # far first: the nearest is written last and stays
            zbuf[pix[order]] = zf[order]
            ibuf[pix[order]] = idf[order]


def spread(a, fn):
    """3 by 3 neighbourhood minimum or maximum of a 2D array."""
    p = np.pad(a, 1, mode='edge')
    out = a.copy()
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            out = fn(out, p[dy:dy + a.shape[0], dx:dx + a.shape[1]])
    return out


def classify(z_engine, z_static):
    """Per pixel: 0 the static world is what was drawn, 1 something nearer was drawn, 2 something farther was drawn."""
    lo = spread(z_static, np.minimum)
    # a neighbour with nothing static in it does not widen the range: only drawn neighbours count
    hi = np.maximum(spread(np.where(z_static < FAR, z_static, -FAR), np.maximum), z_static)
    tol = tolerance(np.minimum(z_engine, hi))
    out = np.zeros(z_engine.shape, dtype=np.int8)
    out[z_engine < lo - tol] = 1
    out[z_engine > hi + tol] = 2
    return out


# ---------------------------------------------------------------- answers
def need_depth(frame):
    if frame.z_buffer() is None:
        raise SeeError('frame %s has no depth image: capture it with depth (gamelab: {"do":"capture","depth":true}; '
                       'console: paris_see_depth before capture_frame)' % frame.name)


def round3(v):
    return [round(float(x), 2) for x in v]


def nearest_entity(scene, point, radius=96.0):
    x, y, z = (float(v) for v in point)
    rows = scene.w.q('SELECT i, classname, targetname, model, origin_x, origin_y, origin_z FROM ents WHERE origin_x BETWEEN ? AND ? '
                     'AND origin_y BETWEEN ? AND ? AND origin_z BETWEEN ? AND ?', (x - radius, x + radius, y - radius, y + radius, z - radius, z + radius))
    best = None
    for r in rows:
        if r['origin_x'] is None:
            continue
        d = math.dist((x, y, z), (r['origin_x'], r['origin_y'], r['origin_z']))
        if d <= radius and (best is None or d < best['distance']):
            best = {'entity': r['i'], 'classname': r['classname'], 'targetname': r['targetname'], 'model': r['model'], 'distance': round(d, 1)}
    return best


def answer_at(scene, frame, x, y):
    """What is at frame pixel (x, y)."""
    dx, dy = frame.to_depth_pixel(x + 0.5, y + 0.5)
    direction, per = frame.ray(dx, dy)
    hits = scene.raycast(frame.origin, direction)
    hits = [(t * per, i, n) for t, i, n in hits if t * per >= frame.near_clip]
    out = {'pixel': [x, y], 'frame': frame.name}
    z = frame.z_at(dx, dy)
    if z is None:
        out['depth'] = 'not captured'
        if hits:
            out.update(scene.name_of(hits[0][1]))
            out['z'] = round(hits[0][0], 2)
            out['distance'] = round(hits[0][0] / per, 2)
            out['position'] = round3(frame.origin + direction * hits[0][0] / per)
            out['source'] = 'database ray cast only: blind to everything that is not the static map'
        else:
            out['kind'] = 'nothing'
        return out
    if z >= FAR:
        out.update({'kind': 'nothing drawn', 'note': 'no depth at this pixel: the sky, or a thing that writes no depth'})
        if hits:
            out['database_first'] = dict(scene.name_of(hits[0][1]), z=round(hits[0][0], 2))
        return out
    out['z'] = round(z, 2)
    out['distance'] = round(z / per, 2)
    out['position'] = round3(frame.unproject(dx, dy, z))
    tol = float(tolerance(np.array(z)))
    # at an edge the neighbour pixels decide which surface the sample fell on: accept a hit that matches the depth of the pixel
    match = [h for h in hits if abs(h[0] - z) <= tol]
    if match:
        best = min(match, key=lambda h: abs(h[0] - z))
        out.update(scene.name_of(best[1]))
        out['depth_minus_database'] = round(z - best[0], 2)
        out['source'] = 'depth and database agree'
        before = [h for h in hits if h[0] < best[0] - tol]
        if before:
            seen = []
            for h in before:
                if h[1] not in seen:
                    seen.append(h[1])
            out['not_drawn_in_front'] = [dict(scene.name_of(i)) for i in seen[:5]]
        return out
    out['kind'] = 'dynamic or unknown'
    behind = [h for h in hits if h[0] > z]
    if behind:
        out['in_front_of'] = dict(scene.name_of(behind[0][1]), z=round(behind[0][0], 2))
        out['source'] = 'the depth shows a thing the database does not hold, %.1f units in front of the static world' % (behind[0][0] - z)
    else:
        out['source'] = 'the depth shows a thing behind every surface the database holds'
    ent = nearest_entity(scene, out['position'])
    if ent:
        out['nearest_map_entity'] = ent
    return out


def answer_project(scene, frame, point):
    px, py, z = frame.project(np.array(point, dtype=np.float64))
    px, py, z = float(px), float(py), float(z)
    fx, fy = px * frame.fw / frame.w, py * frame.fh / frame.h
    out = {'point': round3(point), 'z': round(z, 2), 'distance': round(float(np.linalg.norm(np.array(point) - frame.origin)), 2)}
    if z <= frame.near_clip:
        out['state'] = 'behind the camera'
        return out
    out['pixel'] = [round(fx, 2), round(fy, 2)]
    if not (0 <= px < frame.w and 0 <= py < frame.h):
        out['state'] = 'outside the frame'
        return out
    ze = frame.z_at(px, py)
    if ze is None:
        direction, per = frame.ray(px, py)
        hits = [h for h in scene.raycast(frame.origin, direction) if h[0] * per < z - float(tolerance(np.array(z)))]
        out['state'] = 'occluded (database only)' if hits else 'in view (database only)'
        if hits:
            out['occluder'] = scene.name_of(hits[0][1])
        return out
    tol = float(tolerance(np.array(z)))
    out['depth_z'] = None if ze >= FAR else round(ze, 2)
    if ze < z - tol:
        out['state'] = 'occluded'
        ix, iy = min(frame.fw - 1, int(fx)), min(frame.fh - 1, int(fy))
        occ = answer_at(scene, frame, ix, iy)
        out['occluder'] = {k: occ[k] for k in ('kind', 'prop', 'model', 'surface', 'material', 'z') if k in occ}
    elif ze > z + tol:
        out['state'] = 'visible, nothing drawn there'
    else:
        out['state'] = 'visible, a surface is drawn there'
    return out


def cover(scene, frame, rows):
    """Per prop row: pixels its triangles project to, pixels where the depth is that prop, pixels where something nearer hides it."""
    need_depth(frame)
    ze = frame.z_buffer()
    out = []
    for k in rows:
        zs, _ = scene.render(frame, only=[k])
        m = zs < FAR
        total = int(m.sum())
        if not total:
            out.append({'row': int(k), 'projected': 0, 'visible': 0, 'occluded': 0, 'absent': 0})
            continue
        ys, xs = np.nonzero(m)
        ya, yb, xa, xb = max(0, int(ys.min()) - 2), int(ys.max()) + 3, max(0, int(xs.min()) - 2), int(xs.max()) + 3
        c = np.zeros(zs.shape, dtype=np.int8)
        c[ya:yb, xa:xb] = classify(ze[ya:yb, xa:xb], zs[ya:yb, xa:xb])
        vis = int(((c == 0) & m).sum())
        occ = int(((c == 1) & m).sum())
        ys, xs = np.nonzero((c == 0) & m)
        entry = {'row': int(k), 'projected': total, 'visible': vis, 'occluded': occ, 'absent': total - vis - occ,
                 'nearest_z': round(float(zs[m].min()), 1)}
        if vis:
            sx, sy = frame.fw / frame.w, frame.fh / frame.h
            entry['box'] = [int(xs.min() * sx), int(ys.min() * sy), int((xs.max() + 1) * sx), int((ys.max() + 1) * sy)]
        out.append(entry)
    return out


def answer_visible(scene, frame, prop=None, model=None, point=None, limit=10):
    if point is not None:
        return answer_project(scene, frame, point)
    if prop is not None:
        if prop not in scene.row_of:
            raise SeeError('no prop %d in the database' % prop)
        rows = [scene.row_of[prop]]
    else:
        text = model.lower()
        inview = scene.in_view(frame)
        rows = [int(k) for k in inview if text in scene.p_model[k].lower()]
        if len(rows) > 400:
            raise SeeError('%d props match %r in this view; give a longer name' % (len(rows), model))
    per = cover(scene, frame, rows)
    for e in per:
        e.update({'prop': int(scene.p_index[e.pop('row')])})
        e['model'] = scene.p_model[scene.row_of[e['prop']]]
    per.sort(key=lambda e: -e['visible'])
    tot = {k: sum(e[k] for e in per) for k in ('projected', 'visible', 'occluded', 'absent')}
    tot['fraction_occluded'] = round(tot['occluded'] / tot['projected'], 3) if tot['projected'] else None
    tot['fraction_of_frame'] = round(tot['visible'] / float(frame.w * frame.h), 5)
    return {'props_in_view': len(per), 'props_seen': sum(1 for e in per if e['visible']), 'total': tot,
            'pixels_are': '%d x %d depth-buffer pixels' % (frame.w, frame.h), 'props': per[:limit] if limit else per}


def blobs(mask, z, frame, scene, zs, min_pixels=40, limit=12):
    """Connected groups of pixels where something nearer than the static world was drawn."""
    step = 4
    small = mask[::step, ::step]
    seen = np.zeros(small.shape, dtype=bool)
    out = []
    hh, ww = small.shape
    for sy0, sx0 in zip(*np.nonzero(small)):
        if seen[sy0, sx0]:
            continue
        stack, cells = [(int(sy0), int(sx0))], []
        seen[sy0, sx0] = True
        while stack:
            cy, cx = stack.pop()
            cells.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < hh and 0 <= nx < ww and small[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        ys = np.array([c[0] for c in cells]) * step
        xs = np.array([c[1] for c in cells]) * step
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + step, int(xs.min()), int(xs.max()) + step
        sub = mask[y0:y1, x0:x1]
        count = int(sub.sum())
        if count < min_pixels:
            continue
        py, px = np.nonzero(sub)
        py, px = py + y0, px + x0
        zz = z[py, px]
        k = int(np.argmin(zz))
        zmed = float(np.median(zz))
        centre = frame.unproject(float(np.median(px)) + 0.5, float(np.median(py)) + 0.5, zmed)
        low, high = int(np.argmax(py)), int(np.argmin(py))
        lowest = frame.unproject(px[low] + 0.5, py[low] + 0.5, float(zz[low]))
        highest = frame.unproject(px[high] + 0.5, py[high] + 0.5, float(zz[high]))
        sxf, syf = frame.fw / frame.w, frame.fh / frame.h
        entry = {'pixels': count, 'box': [int(x0 * sxf), int(y0 * syf), int(x1 * sxf), int(y1 * syf)],
                 'nearest_z': round(float(zz[k]), 1), 'median_z': round(zmed, 1), 'centre': round3(centre),
                 'distance': round(float(np.linalg.norm(centre - frame.origin)), 1),
                 'lowest_point': round3(lowest), 'seen_height': round(float(highest[2] - lowest[2]), 1)}
        behind = zs[py, px]
        entry['in_front_of_static_by'] = round(float(np.median(behind[behind < FAR] - zz[behind < FAR])), 1) if (behind < FAR).any() else None
        fl = floor_under(scene, lowest)
        if fl:
            entry['lowest_point_above_floor'] = fl['height']
        ent = nearest_entity(scene, centre)
        if ent:
            entry['nearest_map_entity'] = ent
        out.append(entry)
    out.sort(key=lambda e: -e['pixels'])
    return out[:limit] if limit else out


def table(scene, frame, cache_dir, min_pixels=40):
    """The frame as objects: per static id, pixels expected and pixels where the depth agrees; and what does not fit."""
    need_depth(frame)
    ze = frame.z_buffer()
    skip, absent = set(), {}
    for _ in range(3):
        zs, ids = scene.render(frame, skip=skip, cache_dir=cache_dir)
        c = classify(ze, zs)
        flat_ids = ids.ravel()
        uniq, inv = np.unique(flat_ids, return_inverse=True)
        expected = np.bincount(inv, minlength=len(uniq))
        agree = np.bincount(inv, weights=(c.ravel() == 0), minlength=len(uniq))
        farther = np.bincount(inv, weights=(c.ravel() == 2), minlength=len(uniq))
        new = {}
        for u, e, a, fa in zip(uniq.tolist(), expected.tolist(), agree.tolist(), farther.tolist()):
            if u != NOTHING and e >= min_pixels and a < 0.3 * e and fa > 0.6 * e:
                new[u] = int(e)
        if not new:
            break
        absent.update(new)
        skip |= set(new)
    rows = []
    zmin = {}
    okmask = (c == 0)
    sel = okmask.ravel() & (flat_ids != NOTHING)
    order = np.argsort(flat_ids[sel], kind='stable')
    sid, sz = flat_ids[sel][order], zs.ravel()[sel][order]
    if len(sid):
        cut = np.nonzero(np.diff(sid))[0] + 1
        for part_id, part_z in zip(np.split(sid, cut), np.split(sz, cut)):
            zmin[int(part_id[0])] = float(part_z.min())
    for u, e, a in zip(uniq.tolist(), expected.tolist(), agree.tolist()):
        if u == NOTHING or a < 1:
            continue
        r = dict(scene.name_of(u), pixels=int(a), expected=int(e), nearest_z=round(zmin.get(u, 0.0), 1))
        r.pop('origin', None)
        rows.append(r)
    rows.sort(key=lambda r: -r['pixels'])
    total = frame.w * frame.h
    drawn = ze < FAR
    nearer = (c == 1) & drawn
    farther_m = (c == 2) & drawn
    summary = {'pixels': total, 'static_world': int((okmask & drawn).sum()), 'nearer_than_static': int(nearer.sum()),
               'farther_than_static': int(farther_m.sum()), 'nothing_drawn': int((~drawn).sum()),
               'pixels_are': '%d x %d depth-buffer pixels' % (frame.w, frame.h)}
    missing = [dict(scene.name_of(u), expected=e) for u, e in sorted(absent.items(), key=lambda kv: -kv[1])]
    for mrow in missing:
        mrow.pop('origin', None)
    return {'summary': summary, 'objects': rows, 'dynamic': blobs(nearer, ze, frame, scene, zs, min_pixels=min_pixels),
            'missing': missing, 'ids': ids, 'class': c, 'z_static': zs}


def floor_under(scene, point, reach=400.0):
    """The nearest surface facing up or down on the vertical line through the point, within reach."""
    p = np.asarray(point, dtype=np.float64)
    top = p + np.array([0.0, 0.0, reach])
    hits = scene.raycast(top, np.array([0.0, 0.0, -1.0]), t_max=2 * reach)
    best = None
    for t, ident, nz in hits:
        if nz < 0.5:
            continue
        zf = float(top[2] - t)
        h = float(p[2] - zf)
        if best is None or abs(h) < abs(best['height']):
            best = dict(scene.name_of(ident), floor_z=round(zf, 2), height=round(h, 2))
    if best:
        best.pop('origin', None)
    return best


def answer_floor(scene, frame, point=None, pixel=None):
    out = {}
    if pixel is not None:
        need_depth(frame)
        got = answer_at(scene, frame, pixel[0], pixel[1])
        if 'position' not in got:
            raise SeeError('nothing was drawn at pixel %s' % (pixel,))
        point = got['position']
        out['pixel'] = list(pixel)
        out['at_pixel'] = {k: got[k] for k in ('kind', 'prop', 'model', 'surface', 'material') if k in got}
    out['point'] = round3(point)
    fl = floor_under(scene, point)
    if not fl:
        out['floor'] = None
        out['note'] = 'no level surface within 400 units above or below the point'
    else:
        out['floor'] = fl
        out['height'] = fl['height']
        out['reading'] = ('on the surface' if abs(fl['height']) <= 1.0 else
                          'above the surface by %.1f' % fl['height'] if fl['height'] > 0 else 'below the surface by %.1f' % -fl['height'])
    if frame is not None and pixel is None:
        out['in_frame'] = answer_project(scene, frame, point)
    return out


def same_camera(a, b):
    return (float(np.abs(a.origin - b.origin).max()) < 0.05 and float(np.abs(a.rt - b.rt).max()) < 1e-4
            and abs(a.tanx - b.tanx) < 1e-4 and (a.w, a.h) == (b.w, b.h))


def answer_compare(scene, fa, fb, cache_dir, min_pixels=40, limit=20):
    ta, tb = table(scene, fa, cache_dir, min_pixels), table(scene, fb, cache_dir, min_pixels)
    out = {'same_camera': same_camera(fa, fb)}
    key = lambda r: ('prop', r['prop']) if r['kind'] == 'prop' else ('surface', r['surface'])  # noqa: E731
    pa, pb = {key(r): r for r in ta['objects']}, {key(r): r for r in tb['objects']}
    gone, came, changed = [], [], []
    # With one camera the engine's depth repeats bit for bit, so a thin thing that went (a frame flush on a wall moves
    # the depth by an inch) is still seen: per object, the share of its pixels whose depth moved by more than 0.25 units.
    moved_a, moved_b = {}, {}
    if out['same_camera']:
        za, zb = fa.z_buffer(), fb.z_buffer()
        fine = np.abs(za - zb) > np.maximum(0.25, 0.002 * np.minimum(za, zb))
        for table_, z_own, z_other, into in ((ta, za, zb, moved_a), (tb, zb, za, moved_b)):
            ids = table_['ids'].ravel()
            own = (table_['class'].ravel() == 0) & (ids != NOTHING)
            uniq, inv = np.unique(ids[own], return_inverse=True)
            total = np.bincount(inv, minlength=len(uniq))
            went = np.bincount(inv, weights=(fine.ravel()[own] & (z_other.ravel()[own] > z_own.ravel()[own])), minlength=len(uniq))
            for u, n_all, n_moved in zip(uniq.tolist(), total.tolist(), went.tolist()):
                into[('prop', u - 1) if u > 0 else ('surface', -u - 1)] = n_moved / float(n_all)
    for k, r in pa.items():
        now = pb.get(k, {}).get('pixels', 0)
        if r['pixels'] >= min_pixels and (now < 0.3 * r['pixels'] or moved_a.get(k, 0.0) >= 0.7):
            gone.append(dict(r, pixels_before=r['pixels'], pixels_after=min(now, int(r['pixels'] * (1.0 - moved_a.get(k, 0.0))))))
        elif r['pixels'] >= min_pixels and (now < 0.5 * r['pixels'] or now > 2 * r['pixels']):
            changed.append(dict(r, pixels_before=r['pixels'], pixels_after=now))
    for k, r in pb.items():
        was = pa.get(k, {}).get('pixels', 0)
        if r['pixels'] >= min_pixels and (was < 0.3 * r['pixels'] or moved_b.get(k, 0.0) >= 0.7):
            came.append(dict(r, pixels_before=min(was, int(r['pixels'] * (1.0 - moved_b.get(k, 0.0)))), pixels_after=r['pixels']))
    for rows in (gone, came, changed):
        for r in rows:
            r.pop('pixels', None)
            r.pop('expected', None)
    gone.sort(key=lambda r: -r['pixels_before'])
    came.sort(key=lambda r: -r['pixels_after'])
    out['disappeared'] = gone[:limit] if limit else gone
    out['disappeared_count'] = len(gone)
    out['appeared'] = came[:limit] if limit else came
    out['appeared_count'] = len(came)
    out['changed_count'] = len(changed)
    out['missing_only_in_b'] = [m for m in tb['missing'] if m not in ta['missing']][:limit]
    out['dynamic_a'], out['dynamic_b'] = len(ta['dynamic']), len(tb['dynamic'])
    if out['same_camera']:
        za, zb = fa.z_buffer(), fb.z_buffer()
        tol = tolerance(np.minimum(za, zb))
        moved = np.abs(za - zb) > tol
        out['pixels_whose_depth_changed'] = int(moved.sum())
        out['fraction_whose_depth_changed'] = round(float(moved.mean()), 4)
        # things that are not part of the map and came or went: the depth moved, and on that side it is nearer than the static world
        out['appeared_not_in_map'] = blobs((zb < za - tol) & (tb['class'] == 1), zb, fb, scene, tb['z_static'], min_pixels=min_pixels)
        out['disappeared_not_in_map'] = blobs((za < zb - tol) & (ta['class'] == 1), za, fa, scene, ta['z_static'], min_pixels=min_pixels)
    return out


def answer_fit(scene, frame, cache_dir):
    """device depth = a + b / z, fitted on the pixels where one model explains the static world."""
    if frame.depth is None:
        raise SeeError('frame %s has no depth image' % frame.name)
    zs, ids = scene.render(frame, cache_dir=cache_dir)
    d = frame.depth.astype(np.float64)
    lo, hi = spread(zs, np.minimum), spread(zs, np.maximum)
    flat = (hi - lo) < 0.01 * lo + 0.5                  # away from edges
    m = (zs < FAR) & flat & np.isfinite(d)
    x, y = 1.0 / zs[m], d[m]
    keep = np.ones(len(x), dtype=bool)
    a = b = 0.0
    for _ in range(6):
        A = np.stack([np.ones(keep.sum()), x[keep]], axis=1)
        (a, b), *_ = np.linalg.lstsq(A, y[keep], rcond=None)
        res = y - (a + b * x)
        s = max(np.median(np.abs(res[keep])) * 1.4826, 1e-5 * float(np.abs(y).max()), 1e-12)
        keep = np.abs(res) < 3 * s
    zfit = device_to_z(frame.depth, {'a': a, 'b': b})
    c = classify(zfit, zs)
    return {'model': 'device = a + b / z', 'a': float(a), 'b': float(b), 'default_of_the_tool': [frame.depth_model['a'], frame.depth_model['b']],
            'pixels_used': int(m.sum()), 'pixels_kept': int(keep.sum()), 'median_abs_residual_device': float(np.median(np.abs(res[keep]))),
            'device_range': [float(np.nanmin(d)), float(np.nanmax(d))],
            'with_this_fit': {'static_world': int((c == 0).sum()), 'nearer': int((c == 1).sum()), 'farther': int((c == 2).sum())}}


def answer_camera(frame):
    out = {'frame': frame.name, 'origin': [round(float(v), 3) for v in frame.origin], 'forward': [round(float(v), 6) for v in frame.forward],
           'left': [round(float(v), 6) for v in frame.left], 'up': [round(float(v), 6) for v in frame.up],
           'yaw': round(math.degrees(math.atan2(frame.forward[1], frame.forward[0])), 3),
           'pitch': round(-math.degrees(math.asin(max(-1.0, min(1.0, float(frame.forward[2]))))), 3),
           'tan_half_fov': [round(frame.tanx, 6), round(frame.tany, 6)],
           'fov_x': round(2 * math.degrees(math.atan(frame.tanx)), 3), 'fov_y': round(2 * math.degrees(math.atan(frame.tany)), 3),
           'frame_size': [frame.fw, frame.fh], 'depth_size': [frame.w, frame.h] if frame.depth is not None else None,
           'depth_file': os.path.basename(frame.depth_file) if frame.depth_file else None, 'ms': frame.doc.get('ms')}
    if frame.solved:
        c = frame.solved
        out['solved_from'] = {'points': c['points'], 'used': c['used'], 'median_error_pixels': round(c['median'], 5), 'worst_error_pixels': round(c['worst'], 5),
                              'centre_offset_pixels': [round(c['cx'] - frame.fw * 0.5, 4), round(c['cy'] - frame.fh * 0.5, 4)], 'skew': round(c['skew'], 6)}
        out['moved_between_request_and_after'] = frame.moved()
    return out


# ---------------------------------------------------------------- command line
def _name(r):
    if r.get('kind') == 'prop':
        return 'prop %d %s' % (r['prop'], r.get('model', '?'))
    if r.get('kind') == 'surface':
        return 'surface %d %s' % (r['surface'], r.get('material'))
    return r.get('kind', '?')


def _print(obj, args, text):
    if args.json:
        print(json.dumps(obj, indent=1, default=lambda o: None))
    else:
        text(obj)


def cmd_at(scene, frame, args):
    r = answer_at(scene, frame, args.x, args.y)

    def text(r):
        if 'position' in r:
            print('pixel %d,%d: %s  at %s  z %.1f  distance %.1f' % (args.x, args.y, _name(r), r['position'], r['z'], r['distance']))
        else:
            print('pixel %d,%d: %s' % (args.x, args.y, _name(r)))
        for k in ('source', 'note', 'depth'):
            if k in r:
                print('  %s: %s' % (k, r[k]))
        if 'in_front_of' in r:
            print('  in front of: %s (z %.1f)' % (_name(r['in_front_of']), r['in_front_of']['z']))
        if 'nearest_map_entity' in r:
            e = r['nearest_map_entity']
            print('  nearest map entity: %s %s %s, %.0f units away' % (e['classname'], e['targetname'] or '', e['model'] or '', e['distance']))
        for n in r.get('not_drawn_in_front', []):
            print('  in the database in front of it but not drawn: %s' % _name(n))
    _print(r, args, text)


def cmd_project(scene, frame, args):
    r = answer_project(scene, frame, args.point)
    _print(r, args, lambda r: print('point %s: %s%s  z %.1f%s' % (
        r['point'], r['state'], '  pixel %s' % r['pixel'] if 'pixel' in r else '', r['z'],
        '  hidden by %s at z %s' % (_name(r['occluder']), r['occluder'].get('z')) if 'occluder' in r else '')))


def cmd_visible(scene, frame, args):
    r = answer_visible(scene, frame, prop=args.prop, model=args.model, point=args.point, limit=args.limit)
    if args.point is not None:
        return _print(r, args, lambda r: print('point %s: %s' % (r['point'], r['state'])))

    def text(r):
        t = r['total']
        print('%d props in view, %d seen: %d pixels visible of %d projected (%s hidden by nearer things, %d not drawn); %.3f %% of the frame' % (
            r['props_in_view'], r['props_seen'], t['visible'], t['projected'],
            'none' if not t['occluded'] else '%.1f %%' % (100.0 * t['fraction_occluded']), t['absent'], 100.0 * t['fraction_of_frame']))
        for e in r['props']:
            print('  prop %d %s: visible %d of %d, hidden %d, not drawn %d%s' % (e['prop'], e['model'], e['visible'], e['projected'], e['occluded'],
                                                                             e['absent'], '  box %s' % e['box'] if 'box' in e else ''))
    _print(r, args, text)


def cmd_objects(scene, frame, args):
    r = table(scene, frame, args.cache)
    for key in ('ids', 'class', 'z_static'):
        r.pop(key)
    r['objects_total'] = len(r['objects'])
    if args.limit:
        r['objects'] = r['objects'][:args.limit]
        r['missing'] = r['missing'][:args.limit]

    def text(r):
        s = r['summary']
        print('%s: %d pixels: static world %d, nearer than the static world %d, farther %d, nothing drawn %d; %d objects seen' % (
            frame.name, s['pixels'], s['static_world'], s['nearer_than_static'], s['farther_than_static'], s['nothing_drawn'], r['objects_total']))
        for o in r['objects']:
            print('  %-58s pixels %7d of %7d  nearest z %8.1f' % (_name(o)[:58], o['pixels'], o['expected'], o['nearest_z']))
        for b in r['dynamic']:
            print('  not in the map: %d pixels, box %s, centre %s, distance %.1f, %s in front of the static world%s' % (
                b['pixels'], b['box'], b['centre'], b['distance'],
                'nothing behind it' if b['in_front_of_static_by'] is None else '%.1f' % b['in_front_of_static_by'],
                ', lowest point %.1f above the floor' % b['lowest_point_above_floor'] if 'lowest_point_above_floor' in b else ''))
        for mrow in r['missing']:
            print('  missing: %s (%d pixels expected, the depth is farther)' % (_name(mrow), mrow['expected']))
    _print(r, args, text)


def cmd_floor(scene, frame, args):
    r = answer_floor(scene, frame, point=args.point, pixel=args.pixel)
    _print(r, args, lambda r: print('point %s: %s%s' % (r['point'], r.get('reading', r.get('note')),
                                                      '  (%s, z %.2f)' % (_name(r['floor']), r['floor']['floor_z']) if r.get('floor') else '')))


def cmd_compare(scene, fa, fb, args):
    r = answer_compare(scene, fa, fb, args.cache, limit=args.limit)

    def text(r):
        print('same camera: %s; disappeared %d, appeared %d, changed %d%s' % (
            r['same_camera'], r['disappeared_count'], r['appeared_count'], r['changed_count'],
            '; depth changed on %d pixels (%.1f %%)' % (r['pixels_whose_depth_changed'], 100 * r['fraction_whose_depth_changed'])
            if 'pixels_whose_depth_changed' in r else ''))
        for o in r['disappeared']:
            print('  disappeared: %-52s pixels %d -> %d' % (_name(o)[:52], o['pixels_before'], o['pixels_after']))
        for o in r['appeared']:
            print('  appeared:    %-52s pixels %d -> %d' % (_name(o)[:52], o['pixels_before'], o['pixels_after']))
        for key, word in (('appeared_not_in_map', 'appeared'), ('disappeared_not_in_map', 'disappeared')):
            for b in r.get(key, []):
                print('  %s, not in the map: %d pixels, box %s, centre %s, distance %.1f%s, seen height %.1f' % (
                    word, b['pixels'], b['box'], b['centre'], b['distance'],
                    ', lowest point %.1f above the floor' % b['lowest_point_above_floor'] if 'lowest_point_above_floor' in b else '', b['seen_height']))
    _print(r, args, text)


def make_parser():
    ap = argparse.ArgumentParser(prog='iw7_see', description='What a captured frame shows, as data.')
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(p, frames=1):
        for k in range(frames):
            p.add_argument('frame' if frames == 1 else 'frame_%s' % 'ab'[k], help='the frame (.bmp) or its see-<name>.json')
        p.add_argument('--db', required=True, help='world database of the map (iw7_world.py build)')
        p.add_argument('--json', action='store_true')
        p.add_argument('--limit', type=int, default=15, help='rows listed (0 = all)')
        p.add_argument('--cache', default=os.path.join(tempfile.gettempdir(), 'iw7-see-cache'), help='folder for drawn views')
        p.add_argument('--boxes', action='store_true', help='ignore the model index: props are their bounding boxes')
        p.add_argument('--depth-model', help='a,b of device = a + b / z (default: the measured engine convention)')

    p = sub.add_parser('index', help='read the models of the dump into <db>.models.npz')
    p.add_argument('--db', required=True)
    p.add_argument('--dump', required=True, help='dump folder of the map (xmodel/, xsurface/)')
    p.add_argument('--json', action='store_true')
    p = sub.add_parser('camera', help='the camera of a frame')
    p.add_argument('frame')
    p.add_argument('--json', action='store_true')
    p = sub.add_parser('at', help='what is at a pixel')
    common(p)
    p.add_argument('x', type=int)
    p.add_argument('y', type=int)
    p = sub.add_parser('project', help='where a world point falls and whether it is hidden')
    common(p)
    p.add_argument('point', type=_vec)
    p = sub.add_parser('visible', help='pixels seen of a prop, a model or a point')
    common(p)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prop', type=int)
    g.add_argument('--model')
    g.add_argument('--point', type=_vec)
    p = sub.add_parser('objects', help='the table of what the frame shows')
    common(p)
    p = sub.add_parser('floor', help='height above the surface under a point or a pixel')
    common(p)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--point', type=_vec)
    g.add_argument('--pixel', type=_pix)
    p = sub.add_parser('compare', help='what appeared or disappeared between two frames')
    common(p, frames=2)
    p = sub.add_parser('fit', help='the depth convention measured on a frame')
    common(p)
    return ap


def _vec(text):
    parts = [t for t in re.split(r'[,\s]+', text.strip()) if t]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError('a point is x,y,z')
    return [float(t) for t in parts]


def _pix(text):
    parts = [t for t in re.split(r'[,\s]+', text.strip()) if t]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError('a pixel is x,y')
    return [int(t) for t in parts]


def main(argv=None):
    args = make_parser().parse_args(argv)
    try:
        if args.cmd == 'index':
            r = build_index(args.db, args.dump)
            if args.json:
                print(json.dumps(r, indent=1))
            else:
                print('models %d, read %d, failed %d; %d vertices, %d triangles; worst bounds difference %.2f units (%s); %s' % (
                    r['models'], r['read'], len(r['failed']), r['vertices'], r['triangles'], r['worst_bounds_difference']['units'],
                    r['worst_bounds_difference']['model'], r['file']))
                for f in r['failed'][:10]:
                    print('  not read: %s (%s)' % (f['model'], f['why']))
            return 0
        if args.cmd == 'camera':
            r = answer_camera(Frame(args.frame))
            print(json.dumps(r, indent=1) if args.json else '\n'.join('%s: %s' % kv for kv in r.items()))
            return 0
        model = None
        if args.depth_model:
            a, b = (float(t) for t in args.depth_model.split(','))
            model = {'kind': 'given', 'a': a, 'b': b}
        scene = Scene(args.db, boxes=args.boxes)
        if args.cmd == 'compare':
            cmd_compare(scene, Frame(args.frame_a, model), Frame(args.frame_b, model), args)
            return 0
        frame = Frame(args.frame, model)
        if args.cmd == 'at':
            if not (0 <= args.x < frame.fw and 0 <= args.y < frame.fh):
                raise SeeError('pixel %d,%d is outside the %d x %d frame' % (args.x, args.y, frame.fw, frame.fh))
            cmd_at(scene, frame, args)
        elif args.cmd == 'project':
            cmd_project(scene, frame, args)
        elif args.cmd == 'visible':
            cmd_visible(scene, frame, args)
        elif args.cmd == 'objects':
            cmd_objects(scene, frame, args)
        elif args.cmd == 'floor':
            cmd_floor(scene, frame, args)
        elif args.cmd == 'fit':
            r = answer_fit(scene, frame, args.cache)
            print(json.dumps(r, indent=1))
        return 0
    except WorldError as e:
        print('iw7_see: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
