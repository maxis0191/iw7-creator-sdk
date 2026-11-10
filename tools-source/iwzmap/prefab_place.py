"""Put a worldkit prefab (a room lifted out of one of the game's own maps) into the compile sources of a generated map.

A prefab folder (docs/WORLDKIT.md, schema iw7.prefab/1) placed with `iw7_world.py place` holds world-space props,
lights and surface meshes. This module turns it into what the map compiler takes:

  surfaces   -> render surfaces of world.bin, each with its shipped material, texture and lightmap coordinates
  props      -> smodels.txt lines (with the compiler's noshadow / cull= flags, which prefab.json carries)
  lights     -> lights.txt lines (omni / spot)
  collision  -> the shipped map's own collision triangles inside the prefab box, cut at the box and moved with the
                prefab (their surface tags kept); or, without the shipped collision file, the render triangles
  navigation -> walkable grid cells derived from the collision (floor under the cell, room to stand, no wall across)

It also checks a running map against the prefab (`props-check`) and converts camera poses between the shipped map
and the placed prefab (`pose`). Python standard library only.

  python -I prefab_place.py info        <placed prefab>
  python -I prefab_place.py collision   <placed prefab> --colmap <dump>/maps/cp/<map>.d3dbsp.colmap.hkx
  python -I prefab_place.py props-check <placed prefab> <live props json> [--tol 0.01] [--json out.json]
  python -I prefab_place.py pose        <placed prefab> x y z [yaw] [--to-source]
"""
import argparse, json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'worldkit'))
import iw7_world  # noqa: E402

HAVOK_SCALE = 1.0 / 32.0
NO_CAST_SHADOW = 0x10          # GfxStaticModelDrawInst flag
LIGHT_SPOT, LIGHT_OMNI = 2, 3
COLLISION_FILE = 'collision.bin'
COLLISION_MAGIC = 0x4C4F4350   # 'PCOL'


class PrefabError(Exception):
    pass


def load(prefab_dir):
    p = iw7_world.load_prefab(prefab_dir)
    if p.get('space') != 'world':
        raise PrefabError('%s is not placed: run "iw7_world.py place --prefab <dir> --at X Y Z --out <dir2>" first' % prefab_dir)
    return p


# ---------------------------------------------------------------- source map <-> placed prefab

def source_origin(prefab):
    x1, y1, z1, x2, y2, _z2 = prefab['box']
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0, z1)


def _cs(yaw):
    return iw7_world._cos_sin(yaw)


def to_placed(prefab, p):
    """A point of the shipped map -> the same point of the placed prefab."""
    o, at = source_origin(prefab), prefab['origin']
    r = iw7_world.rot_z((p[0] - o[0], p[1] - o[1], p[2] - o[2]), _cs(prefab.get('yaw', 0.0)))
    return (r[0] + at[0], r[1] + at[1], r[2] + at[2])


def to_source(prefab, p):
    o, at = source_origin(prefab), prefab['origin']
    r = iw7_world.rot_z((p[0] - at[0], p[1] - at[1], p[2] - at[2]), _cs(-prefab.get('yaw', 0.0)))
    return (r[0] + o[0], r[1] + o[1], r[2] + o[2])


def placed_box(prefab):
    """Axis-aligned bounds of the placed prefab box (exact for quarter turns)."""
    x1, y1, z1, x2, y2, z2 = prefab['box']
    pts = [to_placed(prefab, (x, y, z)) for x in (x1, x2) for y in (y1, y2) for z in (z1, z2)]
    return tuple(min(p[a] for p in pts) for a in range(3)) + tuple(max(p[a] for p in pts) for a in range(3))


# ---------------------------------------------------------------- render surfaces -> world.bin

def pack_unit(v, w=3):
    q = [max(0, min(1023, int(round((c + 1.0) * 511.5)))) for c in v]
    return q[0] | q[1] << 10 | q[2] << 20 | w << 30


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / l, v[1] / l, v[2] / l) if l > 1e-12 else (1.0, 0.0, 0.0)


def tangents_from_uvs(mesh):
    """Per-vertex tangent (direction of increasing u), for prefabs written before tangents were carried."""
    acc = [[0.0, 0.0, 0.0] for _ in mesh['positions']]
    P, U = mesh['positions'], mesh['uvs']
    for a, b, c in mesh['tris']:
        e1 = [P[b][k] - P[a][k] for k in range(3)]
        e2 = [P[c][k] - P[a][k] for k in range(3)]
        du1, dv1 = U[b][0] - U[a][0], U[b][1] - U[a][1]
        du2, dv2 = U[c][0] - U[a][0], U[c][1] - U[a][1]
        det = du1 * dv2 - du2 * dv1
        if abs(det) < 1e-12:
            continue
        t = [(e1[k] * dv2 - e2[k] * dv1) / det for k in range(3)]
        for v in (a, b, c):
            for k in range(3):
                acc[v][k] += t[k]
    out = []
    for v, t in enumerate(acc):
        n = mesh['normals'][v]
        d = t[0] * n[0] + t[1] * n[1] + t[2] * n[2]
        t = [t[k] - n[k] * d for k in range(3)]
        if t[0] * t[0] + t[1] * t[1] + t[2] * t[2] < 1e-12:
            t = [n[1], -n[0], 0.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0]
        out.append(_norm(t))
    return out


class WorldWriter:
    """world.bin of the map compiler: materials, 44-byte world vertices, u16 indices relative to each surface's
    first vertex, surfaces in the order they were added (the compiler draws them in that order)."""
    MAX_VERTS = 65535
    MAX_TRIS = 65535

    def __init__(self):
        self.materials, self._mat = [], {}
        self.verts = bytearray()
        self.nverts = 0
        self.indices = []
        self.surfaces = []
        self.mins = [1e30] * 3
        self.maxs = [-1e30] * 3

    def material(self, name):
        if name not in self._mat:
            self._mat[name] = len(self.materials)
            self.materials.append(name)
        return self._mat[name]

    def add(self, material, positions, normals, uvs, lmuvs, tris, tangents=None, signs=None, colors=None):
        """One mesh; split when it exceeds what one surface can hold. Returns the number of surfaces written."""
        if not tris:
            return 0
        if tangents is None:
            tangents = tangents_from_uvs({'positions': positions, 'normals': normals, 'uvs': uvs, 'tris': tris})
        n = 0
        start = 0
        while start < len(tris):
            vmap, part = {}, []
            end = start
            while end < len(tris) and len(part) < self.MAX_TRIS:
                new = [v for v in set(tris[end]) if v not in vmap]
                if len(vmap) + len(new) > self.MAX_VERTS:
                    break
                for v in tris[end]:
                    if v not in vmap:
                        vmap[v] = len(vmap)
                part.append(tuple(vmap[v] for v in tris[end]))
                end += 1
            if not part:
                raise PrefabError('a triangle cannot be placed in a surface')
            first = self.nverts
            order = sorted(vmap, key=vmap.get)
            mn, mx = [1e30] * 3, [-1e30] * 3
            for v in order:
                p = positions[v]
                for a in range(3):
                    mn[a] = min(mn[a], p[a]); mx[a] = max(mx[a], p[a])
                self.verts += struct.pack('<3ffI2f2fII', p[0], p[1], p[2], signs[v] if signs else 0.0078125,
                                          colors[v] if colors else 0xFFFFFFFF, uvs[v][0], uvs[v][1], lmuvs[v][0], lmuvs[v][1],
                                          pack_unit(normals[v]), pack_unit(tangents[v]))
            self.nverts += len(order)
            base = len(self.indices)
            for t in part:
                self.indices += t
            self.surfaces.append((self.material(material), first, len(order), base, len(part), mn, mx))
            for a in range(3):
                self.mins[a] = min(self.mins[a], mn[a]); self.maxs[a] = max(self.maxs[a], mx[a])
            start = end
            n += 1
        return n

    def add_quad(self, material, pts, normal, uv_scale=128.0, lm=(0.5, 0.5)):
        """A flat quad (pts counter-clockwise seen from the normal side), texture mapped in world units."""
        t = _norm((1.0, 0.0, 0.0) if abs(normal[2]) > 0.7 else (-normal[1], normal[0], 0.0))
        b = (normal[1] * t[2] - normal[2] * t[1], normal[2] * t[0] - normal[0] * t[2], normal[0] * t[1] - normal[1] * t[0])
        uvs = [(sum(p[a] * t[a] for a in range(3)) / uv_scale, -sum(p[a] * b[a] for a in range(3)) / uv_scale) for p in pts]
        return self.add(material, [tuple(float(c) for c in p) for p in pts], [normal] * 4, uvs, [lm] * 4, [(0, 1, 2), (0, 2, 3)],
                        tangents=[t] * 4)

    def tobytes(self):
        out = bytearray(struct.pack('<III', 0x575A5749, 1, len(self.materials)))
        for m in self.materials:
            e = m.encode()
            out += struct.pack('<H', len(e)) + e
        out += struct.pack('<I', self.nverts) + self.verts
        out += struct.pack('<I', len(self.indices)) + struct.pack('<%dH' % len(self.indices), *self.indices)
        out += struct.pack('<I', len(self.surfaces))
        for (mi, first, vc, base, tc, mn, mx) in self.surfaces:
            out += struct.pack('<5I6f', mi, first, vc, base, tc, *mn, *mx)
        out += struct.pack('<6f', *self.mins, *self.maxs)
        return bytes(out)


def read_world(data):
    """Parse a world.bin back (for checks and tests): materials, vertex count, surfaces, triangles per material."""
    magic, ver, nm = struct.unpack_from('<III', data, 0)
    if magic != 0x575A5749 or ver != 1:
        raise PrefabError('not a world.bin')
    o, mats = 12, []
    for _ in range(nm):
        l = struct.unpack_from('<H', data, o)[0]
        mats.append(data[o + 2:o + 2 + l].decode()); o += 2 + l
    nv = struct.unpack_from('<I', data, o)[0]
    vo = o + 4; o = vo + 44 * nv
    ni = struct.unpack_from('<I', data, o)[0]
    io = o + 4; o = io + 2 * ni
    ns = struct.unpack_from('<I', data, o)[0]; o += 4
    surfs = []
    for _ in range(ns):
        mi, first, vc, base, tc = struct.unpack_from('<5I', data, o)
        mn = struct.unpack_from('<3f', data, o + 20); mx = struct.unpack_from('<3f', data, o + 32)
        surfs.append({'material': mats[mi], 'first_vertex': first, 'vertices': vc, 'base_index': base, 'triangles': tc,
                      'mins': mn, 'maxs': mx})
        o += 44
    bounds = struct.unpack_from('<6f', data, o)
    if o + 24 != len(data):
        raise PrefabError('world.bin has %d trailing bytes' % (len(data) - o - 24))
    return {'materials': mats, 'vertices': nv, 'indices': ni, 'surfaces': surfs, 'bounds': bounds, 'vertex_offset': vo,
            'index_offset': io}


def add_surfaces(writer, prefab_dir, prefab):
    """Every surface mesh of the prefab, in the shipped map's own surface order (opaque, then decals, then
    translucent, as the map sorted them). Returns counts."""
    order = sorted(range(len(prefab['surfaces'])), key=lambda k: (prefab['surfaces'][k].get('source_surface', k), k))
    st = {'prefab_surfaces': len(order), 'surfaces_written': 0, 'triangles': 0, 'vertices': 0, 'materials': set(),
          'layered_surfaces': 0, 'unlightmapped_surfaces': 0, 'with_tangents': 0}
    for k in order:
        m = iw7_world.read_prefab_surface(prefab_dir, prefab, k)
        s = prefab['surfaces'][k]
        st['surfaces_written'] += writer.add(m['material'], m['positions'], m['normals'], m['uvs'], m['lmuvs'], m['tris'],
                                             m.get('tangents'), m.get('signs'), m.get('colors'))
        st['triangles'] += len(m['tris'])
        st['vertices'] += len(m['positions'])
        st['materials'].add(m['material'])
        st['layered_surfaces'] += 1 if s.get('layered') else 0
        st['unlightmapped_surfaces'] += 1 if s.get('lightmapIndex', 0) not in (0, None) else 0
        st['with_tangents'] += 1 if 'tangents' in m else 0
    st['materials'] = len(st['materials'])
    return st


def surface_triangles(prefab_dir, prefab):
    out = []
    for k in range(len(prefab['surfaces'])):
        m = iw7_world.read_prefab_surface(prefab_dir, prefab, k)
        P = m['positions']
        out += [(P[a], P[b], P[c]) for a, b, c in m['tris']]
    return out


# ---------------------------------------------------------------- props and lights

def smodel_lines(prefab, flags=True):
    """smodels.txt lines; with `flags` the compiler's optional noshadow / cull= tokens from prefab.json."""
    f = iw7_world.fmt
    lines = []
    for p in prefab['props']:
        ln = '%s %s %s %s %s %s %s %s' % (p['model'], f(p['pos'][0]), f(p['pos'][1]), f(p['pos'][2]), f(p['pitch']), f(p['yaw']),
                                          f(p['roll']), f(p['scale']))
        if flags:
            if int(p.get('flags', 0)) & NO_CAST_SHADOW:
                ln += ' noshadow'
            if p.get('cullDist') is not None:
                ln += ' cull=%d' % int(p['cullDist'])
        lines.append(ln)
    return lines


def light_lines(prefab):
    """lights.txt lines: "omni x y z r g b intensity radius" / "spot ... pitch yaw fov". The colour is split into a
    unit colour and an intensity (the compiler multiplies them back). Returns (lines, skipped light types)."""
    lines, skipped = [], []
    for L in prefab['lights']:
        c = L['color']
        inten = max(c)
        if L['type'] not in (LIGHT_SPOT, LIGHT_OMNI) or inten <= 0 or L['radius'] <= 0:
            skipped.append(L['type'])
            continue
        rgb = [v / inten for v in c]
        head = '%.3f %.3f %.3f %.5f %.5f %.5f %.3f %.3f' % (L['pos'][0], L['pos'][1], L['pos'][2], rgb[0], rgb[1], rgb[2], inten, L['radius'])
        if L['type'] == LIGHT_SPOT:
            d = _norm(L['dir'])
            # The compiler stores forward(pitch, yaw) as the light's direction, so the angles are chosen to give back
            # the shipped direction exactly. (In the shipped data that vector points from the lit side back to the
            # light: 726 of Spaceland's 893 spots store an upward one.)
            b = d
            pitch = -math.degrees(math.asin(max(-1.0, min(1.0, b[2]))))
            yaw = math.degrees(math.atan2(b[1], b[0])) if abs(b[2]) < 0.999999 else 0.0
            fov = 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, L['cosHalfFovOuter']))))
            lines.append('spot %s %.3f %.3f %.3f' % (head, pitch, yaw, fov))
        else:
            lines.append('omni ' + head)
    return lines, skipped


# ---------------------------------------------------------------- collision

def _clip(poly, axis, bound, keep_greater):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina = a[axis] >= bound if keep_greater else a[axis] <= bound
        inb = b[axis] >= bound if keep_greater else b[axis] <= bound
        if ina:
            out.append(a)
        if ina != inb:
            t = (bound - a[axis]) / (b[axis] - a[axis])
            q = [a[k] + (b[k] - a[k]) * t for k in range(3)]
            q[axis] = bound
            out.append(tuple(q))
    return out


def clip_triangle(tri, box):
    """The part of a triangle inside an axis-aligned box, as triangles with the same winding."""
    poly = [tuple(v) for v in tri]
    for axis in range(3):
        poly = _clip(poly, axis, box[axis], True)
        if len(poly) < 3:
            return []
        poly = _clip(poly, axis, box[axis + 3], False)
        if len(poly) < 3:
            return []
    out = []
    for i in range(1, len(poly) - 1):
        a, b, c = poly[0], poly[i], poly[i + 1]
        e1 = [b[k] - a[k] for k in range(3)]; e2 = [c[k] - a[k] for k in range(3)]
        cr = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        if cr[0] * cr[0] + cr[1] * cr[1] + cr[2] * cr[2] > 1e-6:
            out.append((a, b, c))
    return out


def stock_collision(colmap_path, prefab):
    """The shipped map's collision triangles inside the prefab's source box (cut at the box), moved with the
    prefab. Returns (triangles in game units, surface tag per triangle, counts)."""
    from hkpack import Packfile
    import hkcm
    pf = Packfile(open(colmap_path, 'rb').read())
    data = [a for a, n, _ in pf.objects if n == 'hknpCompressedMeshShapeData']
    if not data:
        raise PrefabError('%s holds no compressed mesh shape' % colmap_path)
    r = hkcm.decode_cm_data(pf, data[0])
    box = prefab['box']
    s = 1.0 / HAVOK_SCALE
    tris, tags = [], []
    st = {'source_triangles': len(r['tris']), 'touching': 0, 'cut': 0}
    for t, tag in zip(r['tris'], r['tags']):
        g = [(v[0] * s, v[1] * s, v[2] * s) for v in t]
        if any(max(v[a] for v in g) < box[a] or min(v[a] for v in g) > box[a + 3] for a in range(3)):
            continue
        st['touching'] += 1
        inside = all(box[a] <= v[a] <= box[a + 3] for v in g for a in range(3))
        parts = [tuple(g)] if inside else clip_triangle(g, box)
        st['cut'] += 0 if inside else 1
        for part in parts:
            tris.append(tuple(to_placed(prefab, v) for v in part))
            tags.append(tag)
    st['triangles'] = len(tris)
    st['tags'] = len(set(tags))
    return tris, tags, st


def write_collision(path, tris, tags):
    with open(path, 'wb') as f:
        f.write(struct.pack('<II', COLLISION_MAGIC, len(tris)))
        for t, tag in zip(tris, tags):
            f.write(struct.pack('<9fI', *t[0], *t[1], *t[2], tag))


def read_collision(path):
    data = open(path, 'rb').read()
    magic, n = struct.unpack_from('<II', data, 0)
    if magic != COLLISION_MAGIC or len(data) != 8 + 40 * n:
        raise PrefabError('%s is not a prefab collision file' % path)
    tris, tags = [], []
    for k in range(n):
        v = struct.unpack_from('<9fI', data, 8 + 40 * k)
        tris.append((v[0:3], v[3:6], v[6:9])); tags.append(v[9])
    return tris, tags


def prefab_collision(prefab_dir, prefab, colmap=None, default_tag=382):
    """Collision of a placed prefab: its own collision.bin when present, else cut from the shipped collision file,
    else the render triangles (every triangle solid, tag `default_tag`). Returns (tris, tags, source name)."""
    own = os.path.join(prefab_dir, COLLISION_FILE)
    if os.path.isfile(own):
        tris, tags = read_collision(own)
        return tris, tags, 'prefab collision file'
    if colmap:
        tris, tags, _st = stock_collision(colmap, prefab)
        return tris, tags, 'shipped collision'
    tris = surface_triangles(prefab_dir, prefab)
    return tris, [default_tag] * len(tris), 'render triangles'


# ---------------------------------------------------------------- navigation cells from collision

class TriGrid:
    """Triangles bucketed on an x, y grid for vertical and horizontal probes."""

    def __init__(self, tris, cell=64.0):
        self.tris, self.cell, self.b = tris, cell, {}
        for i, t in enumerate(tris):
            x0 = int(math.floor(min(v[0] for v in t) / cell)); x1 = int(math.floor(max(v[0] for v in t) / cell))
            y0 = int(math.floor(min(v[1] for v in t) / cell)); y1 = int(math.floor(max(v[1] for v in t) / cell))
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    self.b.setdefault((x, y), []).append(i)

    def near(self, x0, y0, x1, y1):
        c = self.cell
        seen = set()
        for x in range(int(math.floor(min(x0, x1) / c)), int(math.floor(max(x0, x1) / c)) + 1):
            for y in range(int(math.floor(min(y0, y1) / c)), int(math.floor(max(y0, y1) / c)) + 1):
                seen.update(self.b.get((x, y), ()))
        return seen

    def floors(self, x, y):
        """Heights of upward-facing triangles over the point (x, y)."""
        out = []
        for i in self.near(x, y, x, y):
            a, b, c = self.tris[i]
            n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
                 (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
                 (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
            l = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
            if l < 1e-9 or n[2] / l < 0.7:
                continue
            d = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(d) < 1e-9:
                continue
            u = ((x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])) / d
            v = ((b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])) / d
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            out.append(a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2]))
        return sorted(out)

    def hit(self, p, q):
        """Does the segment p-q cross any triangle (either side)?"""
        d = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
        for i in self.near(p[0], p[1], q[0], q[1]):
            a, b, c = self.tris[i]
            e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
            det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
            if abs(det) < 1e-9:
                continue
            s = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
            u = (s[0] * h[0] + s[1] * h[1] + s[2] * h[2]) / det
            if u < 0 or u > 1:
                continue
            qv = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
            v = (d[0] * qv[0] + d[1] * qv[1] + d[2] * qv[2]) / det
            if v < 0 or u + v > 1:
                continue
            t = (e2[0] * qv[0] + e2[1] * qv[1] + e2[2] * qv[2]) / det
            if 0.0 <= t <= 1.0:
                return True
        return False


def nav_cells(tris, rect, cell=32, min_z=-1e9, reach=20.0, stand=60.0, grid=None):
    """Walkable grid cells {(i, j): z} over rect (x0, y0, x1, y1): the lowest floor at or above min_z under the
    cell centre with nothing across the cell at knee and head height and nothing overhead up to `stand`."""
    g = grid or TriGrid(tris)
    cells = {}
    h = cell / 2.0
    for i in range(int(math.floor(rect[0] / cell)), int(math.ceil(rect[2] / cell))):
        for j in range(int(math.floor(rect[1] / cell)), int(math.ceil(rect[3] / cell))):
            cx, cy = (i + 0.5) * cell, (j + 0.5) * cell
            for z in g.floors(cx, cy):
                if z < min_z:
                    continue
                if g.hit((cx, cy, z + 2.0), (cx, cy, z + stand)):
                    continue
                blocked = False
                for dz in (reach, stand - 12.0):
                    if g.hit((cx - h, cy, z + dz), (cx + h, cy, z + dz)) or g.hit((cx, cy - h, z + dz), (cx, cy + h, z + dz)):
                        blocked = True
                        break
                if not blocked:
                    cells[(i, j)] = round(z, 2)
                break
    return cells


def nav_link(grid, cells, cell=32, step=18.0, heights=(20.0, 48.0)):
    """link(a, b) for mapgen.nav_graph: two neighbour cells are joined when their floors are at most `step` apart and
    nothing stands between their centres at the given heights."""
    memo = {}

    def link(a, b):
        key = (a, b) if a < b else (b, a)
        if key not in memo:
            za, zb = cells[a], cells[b]
            ok = abs(za - zb) <= step
            if ok:
                pa = ((a[0] + 0.5) * cell, (a[1] + 0.5) * cell); pb = ((b[0] + 0.5) * cell, (b[1] + 0.5) * cell)
                base = max(za, zb)
                ok = not any(grid.hit((pa[0] + e, pa[1] + e, base + h), (pb[0] + e, pb[1] + e, base + h))
                             for h in heights for e in (0.0, 0.37, -0.37))
            memo[key] = ok
        return memo[key]
    return link


def largest_island(cells, seeds=(), step=18.0, link=None):
    """Cells connected to a seed cell (or the largest connected group) through neighbours at most `step` apart in
    height (and joined by `link` when given): what a walker can reach."""
    left, groups = set(cells), []
    while left:
        k = left.pop()
        grp, todo = {k}, [k]
        while todo:
            i, j = todo.pop()
            for nb in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if nb in left and abs(cells[nb] - cells[(i, j)]) <= step and (link is None or link((i, j), nb)):
                    left.discard(nb); grp.add(nb); todo.append(nb)
        groups.append(grp)
    if not groups:
        return {}
    for grp in groups:
        if any(s in grp for s in seeds):
            return {k: cells[k] for k in grp}
    best = max(groups, key=len)
    return {k: cells[k] for k in best}


# ---------------------------------------------------------------- checks against a running map

def props_check(prefab, live, tol=0.01):
    """Compare the placed props of a running map (the live world dump, schema iw7.world-live/1) with the prefab:
    every prefab prop must have a live prop of the same model within `tol` (one to one)."""
    rows = live.get('props') or live.get('rows') or []
    by_model = {}
    for r in rows:
        name = r.get('model') or r.get('name')
        o = r.get('origin') or r.get('pos') or [r.get('x'), r.get('y'), r.get('z')]
        by_model.setdefault(name, []).append([float(o[0]), float(o[1]), float(o[2]), False, r])
    matched, worst, missing, scale_diff, axis_diff, cull_diff = 0, 0.0, [], 0, 0, 0
    for p in prefab['props']:
        best, bd = None, 1e30
        for c in by_model.get(p['model'], ()):
            if c[3]:
                continue
            d = max(abs(c[0] - p['pos'][0]), abs(c[1] - p['pos'][1]), abs(c[2] - p['pos'][2]))
            if d < bd:
                best, bd = c, d
        if best is not None and bd <= tol:
            best[3] = True
            matched += 1
            worst = max(worst, bd)
            sc = best[4].get('scale')
            if sc is not None and abs(float(sc) - p['scale']) > 1e-4:
                scale_diff += 1
            ax = best[4].get('axis')
            if ax is not None and len(ax) == 9:
                want = iw7_world.angles_to_axis(p['pitch'], p['yaw'], p['roll'])
                if max(abs(float(ax[3 * a + b]) - want[a][b]) for a in range(3) for b in range(3)) > 1e-3:
                    axis_diff += 1
            cu = best[4].get('cull')
            if cu is not None and p.get('cullDist') is not None and int(cu) != int(p['cullDist']):
                cull_diff += 1
        else:
            missing.append({'model': p['model'], 'pos': p['pos'], 'nearest': None if best is None else bd})
    extra = sum(1 for v in by_model.values() for c in v if not c[3])
    return {'prefab_props': len(prefab['props']), 'live_props': len(rows), 'matched': matched, 'missing': len(missing),
            'extra_live': extra, 'largest_position_difference': worst, 'scale_differs': scale_diff,
            'orientation_differs': axis_diff, 'cull_distance_differs': cull_diff,
            'prefab_models': len({p['model'] for p in prefab['props']}), 'live_models': len(by_model),
            'tolerance': tol, 'missing_rows': missing[:20], 'ok': matched == len(prefab['props']) and not extra}


# ---------------------------------------------------------------- command line

def main(argv=None):
    ap = argparse.ArgumentParser(description='worldkit prefab -> generated map sources')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('info'); p.add_argument('prefab')
    p = sub.add_parser('collision'); p.add_argument('prefab'); p.add_argument('--colmap', required=True)
    p = sub.add_parser('props-check'); p.add_argument('prefab'); p.add_argument('live')
    p.add_argument('--tol', type=float, default=0.01); p.add_argument('--json')
    p = sub.add_parser('pose'); p.add_argument('prefab'); p.add_argument('xyz', type=float, nargs='+')
    p.add_argument('--to-source', action='store_true')
    a = ap.parse_args(argv)
    try:
        pre = load(a.prefab)
        if a.cmd == 'info':
            lines, skipped = light_lines(pre)
            print('prefab %s at %s yaw %s: props %d (%d models), surfaces %d, lights %d (%d usable), box %s, collision file %s' % (
                pre['name'], pre['origin'], pre.get('yaw', 0), len(pre['props']), len({q['model'] for q in pre['props']}),
                len(pre['surfaces']), len(pre['lights']), len(lines), [round(v, 1) for v in placed_box(pre)],
                'yes' if os.path.isfile(os.path.join(a.prefab, COLLISION_FILE)) else 'no'))
        elif a.cmd == 'collision':
            tris, tags, st = stock_collision(a.colmap, pre)
            write_collision(os.path.join(a.prefab, COLLISION_FILE), tris, tags)
            print('collision: %d triangles (%d of %d shipped triangles touch the box, %d cut at it), %d surface tags -> %s' % (
                st['triangles'], st['touching'], st['source_triangles'], st['cut'], st['tags'], COLLISION_FILE))
        elif a.cmd == 'props-check':
            with open(a.live, 'r', encoding='utf-8') as f:
                rep = props_check(pre, json.load(f), a.tol)
            if a.json:
                with open(a.json, 'w', encoding='utf-8') as f:
                    json.dump(rep, f, indent=1)
            print('props: prefab %d, live %d, matched %d within %g (largest difference %.5f), missing %d, extra in the map %d, '
                  'models %d / %d, scale differs %d, orientation differs %d, cull distance differs %d: %s' % (
                      rep['prefab_props'], rep['live_props'], rep['matched'], rep['tolerance'],
                      rep['largest_position_difference'], rep['missing'], rep['extra_live'], rep['prefab_models'],
                      rep['live_models'], rep['scale_differs'], rep['orientation_differs'], rep['cull_distance_differs'],
                      'OK' if rep['ok'] else 'DIFFERENT'))
            return 0 if rep['ok'] else 1
        elif a.cmd == 'pose':
            if len(a.xyz) not in (3, 4):
                raise PrefabError('pose takes x y z [yaw]')
            fn = to_source if a.to_source else to_placed
            q = fn(pre, a.xyz[:3])
            yaw = pre.get('yaw', 0.0)
            out = '%g %g %g' % tuple(round(c, 4) for c in q)
            if len(a.xyz) == 4:
                out += ' %g' % ((a.xyz[3] + (-yaw if a.to_source else yaw)) % 360.0)
            print(out)
    except (PrefabError, iw7_world.WorldError, OSError, ValueError) as e:
        print('prefab_place: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
