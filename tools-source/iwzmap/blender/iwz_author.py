"""Authoring library for IW7 zombies map sections (runs inside Blender, interactive or `blender -b`).

A section script (see sections/demo_replace_maint_corridor.py) imports this module, calls the helpers and exports with blend2iwz.py.
Every length is in IW7 INCHES (x east, y north, z up, yaw in degrees, 0 = +x); the helpers convert to Blender metres (1 BU = 1 m =
39.37 in). Materials are the IW7 world materials by name (`w/concrete_tiles_01`), models are stock xmodel names. Everything the helpers
make is plain custom properties (iwz_mode, iwz_kind, iwz_model, ...), so blend2iwz.py exports it without the add-on.

World geometry (collection IWZ_World; render + collision unless `mode`):
    wall(p0, p1, z0, z1, mat, thick=16, openings=(), side='center')   floor(x0, y0, x1, y1, z, mat, thick=8)   ceiling(x0, y0, x1, y1, z, mat)
    beam(p0, p1, z, w, h, mat)   column(at, z0, z1, size, mat, sides=4)   arch(p0, p1, z_spring, mat, rise, thick, segments)
    vault(x0, y0, x1, y1, z_spring, rise, mat, axis, segments)   stair(start, yaw, width, steps, rise, run, mat, name)   slab(mn, mx, mat)
Dressing:   prop(model, at, yaw, scale, clip)   prop_row(...)   prop_scatter(models, region, n, seed, avoid)
            light(kind, at, color, radius, intensity, group, fixture)   decal(material, at, normal, size, rot)   sign(image, at, normal, size)
Gameplay:   spawner(at, yaw, kind)   interaction(kind, at, yaw, **props)   zone(name, box, floor, ceiling)   door(name, zones, box, cost)
            link(a, b)   fx(name, at)   camera(name, at, yaw, pitch, zone)
Context:    clearances() -> the gameplay boxes of the imported base that props must keep free
"""
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
IWZ = os.path.dirname(HERE)
for _p in (HERE, IWZ, os.path.join(IWZ, 'preview')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

IN = 0.0254
TEXTURED = os.environ.get('IWZ_AUTHOR_TEXTURES') == '1'
_CACHE = {}


# ------------------------------------------------------------------------------------------------ scene plumbing
def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if c.name not in [x.name for x in bpy.context.scene.collection.children_recursive]:
        bpy.context.scene.collection.children.link(c)
    return c


def _link(o, cname):
    coll(cname).objects.link(o)
    return o


def _m(p):
    return (p[0] * IN, p[1] * IN, p[2] * IN)


def material(name):
    """the Blender material of an IW7 material name (plain grey by default; with textures when IWZ_AUTHOR_TEXTURES=1 and the dumps exist)"""
    m = bpy.data.materials.get(name)
    if m:
        return m
    if TEXTURED:
        try:
            import iwz_assets as A
            import iwz_preview as P
            if 'resolver' not in _CACHE:
                _CACHE['resolver'] = P.MaterialResolver(A.DumpIndex(), {}, None)
            m = _CACHE['resolver'].get(name, 'UVMap', 'lightmap', object_light=True)
            m.name = name
            return m
        except Exception:
            pass
    m = bpy.data.materials.new(name)
    h = sum(ord(c) * (i + 3) for i, c in enumerate(name)) % 997 / 997.0
    m.diffuse_color = (0.35 + 0.4 * h, 0.4 + 0.3 * ((h * 7) % 1), 0.4 + 0.3 * ((h * 13) % 1), 1.0)
    return m


def new_scene(map_name='cp_iwz'):
    """an empty scene in metres (the .blend of a section starts from import-base / new-section, which call this)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc['iwz_map'] = map_name
    return sc


def _tex_scale(mat):
    try:
        import blend_core
        return blend_core.material_table().get(mat, (128.0, 128.0))
    except Exception:
        return (128.0, 128.0)


def mesh_object(name, faces, mat, cname='IWZ_World', mode='both', **props):
    """faces: list of 3 or 4 points (inches), counter-clockwise seen from the front; one object, flat shaded, world aligned uv"""
    verts, index, polys = [], {}, []
    for f in faces:
        ids = []
        for p in f:
            k = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
            if k not in index:
                index[k] = len(verts)
                verts.append(_m(k))
            ids.append(index[k])
        polys.append(ids)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], polys)
    me.update()
    su, sv = _tex_scale(mat) if mat else (128.0, 128.0)
    uvl = me.uv_layers.new(name='UVMap')
    li = 0
    for f in faces:
        n = _normal(f)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for p in f:
            u, v = (p[1], p[2]) if ax == 0 else ((p[0], p[2]) if ax == 1 else (p[0], p[1]))
            uvl.data[li].uv = (u / su, v / sv)
            li += 1
    for pl in me.polygons:
        pl.use_smooth = False
    if mat:
        me.materials.append(material(mat))
    o = bpy.data.objects.new(name, me)
    _link(o, cname)
    o['iwz_mode'] = mode
    for k, v in props.items():
        o[k] = v
    if mode == 'collision':
        o.display_type = 'WIRE'
    return o


def _normal(f):
    a, b, c = f[0], f[1], f[2]
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


# ------------------------------------------------------------------------------------------------ boxes in a wall frame
class Frame:
    """origin p0 (x, y), unit direction u, left normal n = (-uy, ux): P(s, t, z) = p0 + u s + n t"""

    def __init__(self, p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.length = math.hypot(dx, dy)
        if self.length < 1e-6:
            raise ValueError('wall of length 0')
        self.u = (dx / self.length, dy / self.length)
        self.n = (-self.u[1], self.u[0])
        self.p0 = p0

    def P(self, s, t, z):
        return (self.p0[0] + self.u[0] * s + self.n[0] * t, self.p0[1] + self.u[1] * s + self.n[1] * t, z)

    def s_of(self, x, y):
        return (x - self.p0[0]) * self.u[0] + (y - self.p0[1]) * self.u[1]


def box_faces(F, s0, s1, t0, t1, z0, z1, skip=()):
    """the faces of a box in a frame (outward, counter-clockwise from outside); skip names faces left out: top bottom -n +n -u +u"""
    P = F.P
    faces = {
        'top': [P(s0, t0, z1), P(s1, t0, z1), P(s1, t1, z1), P(s0, t1, z1)],
        'bottom': [P(s0, t1, z0), P(s1, t1, z0), P(s1, t0, z0), P(s0, t0, z0)],
        '-n': [P(s0, t0, z0), P(s1, t0, z0), P(s1, t0, z1), P(s0, t0, z1)],
        '+n': [P(s1, t1, z0), P(s0, t1, z0), P(s0, t1, z1), P(s1, t1, z1)],
        '-u': [P(s0, t1, z0), P(s0, t0, z0), P(s0, t0, z1), P(s0, t1, z1)],
        '+u': [P(s1, t0, z0), P(s1, t1, z0), P(s1, t1, z1), P(s1, t0, z1)],
    }
    return [f for k, f in faces.items() if k not in skip]


# ------------------------------------------------------------------------------------------------ world geometry
def opening_on_wall(p0, p1, box):
    """(s0, s1, zlo, zhi) of a world box [x0, y0, z0, x1, y1, z1] seen from the wall p0 -> p1 (what `wall(openings=...)` takes)"""
    F = Frame(p0, p1)
    ss = [F.s_of(x, y) for x in (box[0], box[3]) for y in (box[1], box[4])]
    return (min(ss), max(ss), box[2], box[5])


def wall(p0, p1, z0, z1, mat, thick=16.0, openings=(), side='center', name='wall', mode='both'):
    """a wall of thickness `thick` from p0 to p1 (inches, any direction), from z0 to z1. side: which side of p0 -> p1 the thickness goes
    ('left', 'right' or 'center'). openings: (s0, s1, zlo, zhi) along the wall from p0, or world boxes (6 numbers): the wall leaves them
    free (sill below, lintel above, jambs closed)."""
    F = Frame(p0, p1)
    t0, t1 = {'left': (0.0, thick), 'right': (-thick, 0.0), 'center': (-thick / 2, thick / 2)}[side]
    ops = []
    for o in openings:
        ops.append(opening_on_wall(p0, p1, o) if len(o) == 6 else tuple(o))
    ops.sort()
    faces = []
    s = 0.0
    for (a, b, lo, hi) in ops:
        a, b = max(a, 0.0), min(b, F.length)
        if a > s:
            faces += box_faces(F, s, a, t0, t1, z0, z1, skip=('+u',) if False else ())
        if lo > z0:
            faces += box_faces(F, a, b, t0, t1, z0, lo, skip=('-u', '+u'))
        if hi < z1:
            faces += box_faces(F, a, b, t0, t1, hi, z1, skip=('-u', '+u'))
        s = max(s, b)
    if s < F.length:
        faces += box_faces(F, s, F.length, t0, t1, z0, z1)
    return mesh_object(name, faces, mat, mode=mode)


def slab(mn, mx, mat, name='slab', mode='both', skip=()):
    """an axis aligned box (inches)"""
    F = Frame((mn[0], mn[1]), (mx[0], mn[1]))
    return mesh_object(name, box_faces(F, 0, mx[0] - mn[0], 0, mx[1] - mn[1], mn[2], mx[2], skip), mat, mode=mode)


def floor(x0, y0, x1, y1, z, mat, thick=8.0, name='floor', mode='both'):
    """a floor slab whose top is at z"""
    return slab((x0, y0, z - thick), (x1, y1, z), mat, name, mode)


def ceiling(x0, y0, x1, y1, z, mat, thick=8.0, name='ceiling', mode='both'):
    """a ceiling slab whose underside is at z"""
    return slab((x0, y0, z), (x1, y1, z + thick), mat, name, mode)


def beam(p0, p1, z, w, h, mat, name='beam', mode='both'):
    """a beam from p0 to p1 (inches) of width w and height h whose underside is at z"""
    F = Frame(p0, p1)
    return mesh_object(name, box_faces(F, 0, F.length, -w / 2, w / 2, z, z + h), mat, mode=mode)


def column(at, z0, z1, size, mat, sides=4, name='column', mode='both'):
    """a column of `size` across (a square when sides is 4, a regular polygon otherwise), flat shaded"""
    pts = []
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides if sides == 4 else 2 * math.pi * k / sides
        r = size / 2 * (math.sqrt(2) if sides == 4 else 1.0)
        pts.append((at[0] + r * math.cos(a), at[1] + r * math.sin(a)))
    faces = [[(p[0], p[1], z1) for p in pts], [(p[0], p[1], z0) for p in reversed(pts)]]
    for k in range(sides):
        a, b = pts[k], pts[(k + 1) % sides]
        faces.append([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])
    return mesh_object(name, faces, mat, mode=mode)


def arch(p0, p1, z_spring, mat, rise=None, thick=16.0, segments=8, name='arch', mode='render'):
    """the curved reveal of an arched opening in a wall: a half ellipse from p0 to p1 (the opening width), springing at z_spring and
    rising `rise` (default half the width); the intrados is segmented and flat shaded, `thick` deep (the wall thickness)"""
    F = Frame(p0, p1)
    w = F.length
    rise = w / 2 if rise is None else rise
    pts = []
    for k in range(segments + 1):
        a = math.pi - math.pi * k / segments
        pts.append((w / 2 + w / 2 * math.cos(a), z_spring + rise * math.sin(a)))
    faces = []
    for (sa, za), (sb, zb) in zip(pts[:-1], pts[1:]):
        faces.append([F.P(sa, thick / 2, za), F.P(sa, -thick / 2, za), F.P(sb, -thick / 2, zb), F.P(sb, thick / 2, zb)])
    return mesh_object(name, faces, mat, mode=mode)


def vault(x0, y0, x1, y1, z_spring, rise, mat, axis='x', segments=8, name='vault', mode='render'):
    """a barrel vault ceiling over the rectangle: the half ellipse across the shorter way, springing at z_spring, `rise` high, running
    along `axis`; the segments face down and are flat shaded"""
    if axis == 'x':
        span, run, a0, b0 = y1 - y0, x1 - x0, y0, x0
    else:
        span, run, a0, b0 = x1 - x0, y1 - y0, x0, y0
    pts = [(a0 + span / 2 - span / 2 * math.cos(math.pi * k / segments), z_spring + rise * math.sin(math.pi * k / segments)) for k in range(segments + 1)]
    faces = []
    for (ta, za), (tb, zb) in zip(pts[:-1], pts[1:]):
        if axis == 'x':
            faces.append([(x0, tb, zb), (x0, ta, za), (x1, ta, za), (x1, tb, zb)])
        else:
            faces.append([(ta, y0, za), (tb, y0, zb), (tb, y1, zb), (ta, y1, za)])
    return mesh_object(name, faces, mat, mode=mode)


def stair(start, yaw, width, steps, rise, run, mat, name='flight', z_base=None, mode='both'):
    """a flight of `steps` steps climbing from `start` (x, y, z of the floor in front of the first riser, centre of the width) in the
    direction yaw. Every step is a solid from z_base (default start z) to its tread. The mesh is marked iwz_stair, so the exporter adds
    the stock clip ramp, the side walls and the rails."""
    F = Frame((start[0], start[1]), (start[0] + math.cos(math.radians(yaw)), start[1] + math.sin(math.radians(yaw))))
    zb = start[2] if z_base is None else z_base
    faces = []
    for k in range(steps):
        faces += box_faces(F, k * run, (k + 1) * run, -width / 2, width / 2, zb, start[2] + (k + 1) * rise)
    return mesh_object(name, faces, mat, mode=mode, iwz_stair=name)


# ------------------------------------------------------------------------------------------------ props
def _model_mesh(name):
    me = bpy.data.meshes.get('iwzm:' + name)
    if me is not None:
        return me
    try:
        import numpy as np
        import iwz_assets as A
        import iwz_preview as P
        idx = _CACHE.get('index') or A.DumpIndex()
        _CACHE['index'] = idx
        mdl, err = A.read_model(idx, name)
        if mdl is None:
            raise RuntimeError(err)
        sp, st, ui, mi, mats, off = [], [], [], [], [], 0
        for s in mdl['surfs']:
            sp.append(s['pos'] * P.S)
            st.append(s['tris'] + off)
            ui.append(s['uv'])
            off += len(s['pos'])
            k = s['material'] or '__none__'
            if k not in mats:
                mats.append(k)
            mi.append(np.full(len(s['tris']), mats.index(k), np.int64))
        me = P.mesh_from_arrays('iwzm:' + name, np.concatenate(sp), np.concatenate(st), [np.concatenate(ui)], ('uv',), np.concatenate(mi))
        for k in mats:
            if TEXTURED:
                if 'resolver' not in _CACHE:
                    _CACHE['resolver'] = P.MaterialResolver(idx, {}, None)
                me.materials.append(_CACHE['resolver'].get(k, 'uv', object_light=True))
            else:
                me.materials.append(material('m:' + k))
        return me
    except Exception:
        import bmesh
        me = bpy.data.meshes.new('iwzm:' + name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=0.6)
        bm.to_mesh(me)
        bm.free()
        return me


def prop(model, at, yaw=0.0, scale=1.0, clip=False, static=True, pitch=0.0, roll=0.0, name=None):
    """a stock model at `at` (inches), yaw degrees, uniform scale. clip=True: the exporter adds a solid clip box from the model bounds
    (players, zombies and the navigation are blocked by it); static=False: a script_model instead of a compiled static model"""
    o = bpy.data.objects.new(name or model, _model_mesh(model))
    o.location = _m(at)
    o.rotation_euler = (math.radians(roll), math.radians(pitch), math.radians(yaw))
    o.scale = (scale, scale, scale)
    _link(o, 'IWZ_Props')
    o['iwz_model'] = model
    if clip:
        o['iwz_clip'] = 1
    if not static:
        o['iwz_static'] = 0
    return o


def prop_row(model, start, end, n, yaw=0.0, scale=1.0, clip=False, z=None):
    """n copies of a model on the line start -> end (inclusive)"""
    out = []
    for k in range(n):
        t = k / max(1, n - 1)
        zz = start[2] if z is None and len(start) > 2 else (z or 0.0)
        out.append(prop(model, (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t, zz), yaw, scale, clip))
    return out


def clearances():
    """the clearance boxes [x0, y0, z0, x1, y1, z1] (inches) of the imported base (objects of IWZ_Gameplay with iwz_clearance): door and
    arch openings, interaction fronts, spawner radii"""
    out = []
    c = bpy.data.collections.get('IWZ_Gameplay')
    if c:
        for o in c.all_objects:
            v = o.get('iwz_clearance')
            if v is not None:
                out.append([float(x) for x in (v.to_list() if hasattr(v, 'to_list') else v)])
    return out


def prop_scatter(models, region, n, seed, avoid=None, z=0.0, min_dist=32.0, pad=24.0, scale=(1.0, 1.0), clip=False, yaw=(0.0, 360.0), tries=40):
    """n props of the given models inside `region` ((x0, y0, x1, y1), or a list of such rectangles), seeded, at least min_dist apart and
    out of every `avoid` box (default: the gameplay clearances of the imported base, grown by `pad`)"""
    rnd = random.Random(seed)
    rects = [region] if isinstance(region[0], (int, float)) else list(region)
    boxes = [list(b) for b in (clearances() if avoid is None else avoid)]
    placed, out = [], []
    for _ in range(n):
        for _t in range(tries):
            r = rnd.choice(rects)
            x, y = rnd.uniform(r[0], r[2]), rnd.uniform(r[1], r[3])
            if any(b[0] - pad <= x <= b[3] + pad and b[1] - pad <= y <= b[4] + pad for b in boxes if len(b) == 6) or \
               any(b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad for b in boxes if len(b) == 4):
                continue
            if any(math.hypot(x - q[0], y - q[1]) < min_dist for q in placed):
                continue
            placed.append((x, y))
            out.append(prop(rnd.choice(models), (x, y, z), rnd.uniform(*yaw), rnd.uniform(*scale), clip))
            break
    return out


# ------------------------------------------------------------------------------------------------ lights, decals, signs
def light(kind, at, color=(1.0, 0.86, 0.7), radius=300.0, intensity=1.0, group='power', fixture=None, dir=(0, 0, -1), inner=14.0, outer=32.0, name=None):
    """a baked light. kind 'omni' or 'spot'; group 'power' (off until the power is on), 'emergency' (always on) or 'flicker';
    fixture: the lamp model drawn at the light (stock xmodel, optional)"""
    from mathutils import Vector
    d = bpy.data.lights.new(name or 'iwz_light', 'SPOT' if kind == 'spot' else 'POINT')
    d.color = color
    d.energy = 100.0 * intensity
    o = bpy.data.objects.new(name or 'iwz_light', d)
    o.location = _m(at)
    if kind == 'spot':
        d.spot_size = math.radians(outer * 2)
        d.spot_blend = 1 - inner / max(1e-6, outer)
        o.rotation_euler = Vector((0, 0, -1)).rotation_difference(Vector(dir)).to_euler()
    o['iwz_radius'] = float(radius)
    o['iwz_intensity'] = float(intensity)
    o['iwz_group'] = group
    if fixture:
        o['iwz_fixture'] = fixture
    _link(o, 'IWZ_Entities')
    return o


def _plane(name, material_name, at, normal, size, rot, kind, off, **props):
    n = [float(c) for c in normal]
    ln = math.sqrt(sum(c * c for c in n))
    n = [c / ln for c in n]
    w, h = size
    if abs(n[2]) > 0.9:
        a = math.radians(rot)
        r = (math.cos(a), math.sin(a), 0.0)
        up = (-math.sin(a), math.cos(a), 0.0)
        if n[2] < 0:
            r = (r[0], -r[1], 0.0)
    else:
        r = (-n[1], n[0], 0.0)              # z cross n: the viewer's right
        up = (0.0, 0.0, 1.0)
    c = [at[i] + n[i] * off for i in range(3)]
    pts = [[c[i] + sx * r[i] * w / 2 + sy * up[i] * h / 2 for i in range(3)] for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    o = mesh_object(name, [pts], material_name, cname='IWZ_Decals', mode='render', iwz_uv='authored')
    me = o.data
    for k, uv in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        me.uv_layers['UVMap'].data[k].uv = uv
    o['iwz_kind'] = kind
    o['iwz_material'] = material_name
    for k, v in props.items():
        o[k] = v
    return o


def decal(material_name, at, normal, size, rot=0.0, name='decal'):
    """a decal plane on a surface: `at` is the point on the wall or floor, `normal` points into the room, size (w, h) in inches. The
    plane stands 0.4 in front of the surface; material: a stock material key (leak_stain) or w/ name"""
    return _plane(name, material_name, at, normal, size, rot, 'decal', 0.4)


def sign(image, at, normal, size, rot=0.0, name='sign', hanging=False, off=3.6):
    """a sign (custom image key such as sign_generator) on a wall at `at`, `off` inches in front of it (3.6 clears the trims)"""
    return _plane(name, image, at, normal, size, rot, 'sign', off, iwz_image=image, iwz_off=off, iwz_hanging=1 if hanging else 0)


# ------------------------------------------------------------------------------------------------ gameplay
def _empty(name, kind, at, yaw, size=0.4, **props):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'ARROWS'
    o.empty_display_size = size
    o.location = _m(at)
    o.rotation_euler = (0, 0, math.radians(yaw))
    _link(o, 'IWZ_Entities')
    o['iwz_kind'] = kind
    for k, v in props.items():
        o[k] = v
    return o


def spawner(at, yaw=0.0, kind='ground', name=None):
    """a zombie spawn (kind ground, wall or ceiling); at = the floor point"""
    return _empty(name or 'spawn', 'spawner', at, yaw, iwz_spawn=kind, iwz_vent=0 if kind != 'wall' else 1)


_INTERACTION_KINDS = {'perk': ('iwz_perk', 'revive'), 'wall_buy': ('iwz_weapon_class', 'smg'), 'pap': None, 'wheel': None, 'power': None}


def interaction(kind, at, yaw=0.0, name=None, **props):
    """a stock interaction: kind perk (perk='revive'...), wall_buy (weapon_class='smg' or weapon='iw7_..', cost=1000), pap, wheel, power;
    at = the floor point under it (a wall buy: the floor in front of its wall), yaw = the way it faces"""
    if kind not in _INTERACTION_KINDS:
        raise ValueError('interaction kind %r (perk, wall_buy, pap, wheel, power)' % kind)
    p = {}
    if kind == 'perk':
        p = {'iwz_perk': props.get('perk', 'revive'), 'iwz_powered': int(props.get('powered', 0))}
    elif kind == 'wall_buy':
        p = {'iwz_weapon_class': props.get('weapon_class', 'smg'), 'iwz_weapon': props.get('weapon', ''), 'iwz_cost': int(props.get('cost', 1000))}
    return _empty(name or kind, kind, at, yaw, **p)


def zone(name, box, floor_z=None, ceiling_z=None, probe=(0.9, 0.9, 0.95, 0.6)):
    """a zone volume (a new zone of a section): box [x0, y0, z0, x1, y1, z1] inches"""
    import iwz2blend
    o = iwz2blend.box_obj(name, box[:3], box[3:], coll('IWZ_Zones'), 'zone')
    o['iwz_floor'] = float(box[2] if floor_z is None else floor_z)
    o['iwz_ceiling'] = float(box[5] if ceiling_z is None else ceiling_z)
    o['iwz_probe'] = list(probe)
    return o


def door(name, zones, box, cost=1000):
    """a door between two zones (a thin box in the doorway, cost 750 / 1000 / 1250 / 1500)"""
    import iwz2blend
    return iwz2blend.box_obj(name, box[:3], box[3:], coll('IWZ_Zones'), 'door', iwz_cost=int(cost), iwz_zones=','.join(zones))


def link(a, b):
    """two zones joined without a door (spawners may use each other's volumes)"""
    return _empty('link_%s_%s' % (a, b), 'link', (0, 0, 0), 0, iwz_zones='%s,%s' % (a, b))


def fx(name, at, repeat=True):
    return _empty('fx_' + name.split('/')[-1], 'fx', at, 0, iwz_fx=name, iwz_repeat=int(repeat))


def camera(name, at, yaw, pitch=0.0, zone=None):
    """a look camera for the previews (at = the player origin on the floor; the eye stands 60 above): becomes a `views` row"""
    cam = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, cam)
    o.location = _m((at[0], at[1], at[2] + 60.0))
    o.rotation_euler = (math.radians(90.0 - pitch), 0.0, math.radians(yaw - 90.0))
    if zone:
        o['iwz_zone'] = zone
    _link(o, 'IWZ_Entities')
    return o
