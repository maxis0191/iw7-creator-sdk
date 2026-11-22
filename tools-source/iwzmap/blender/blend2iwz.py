"""Blender scene -> IWZ emit folder (runs inside Blender, interactive or `blender -b`).

    blender -b map.blend --python blend2iwz.py -- export --out <emit folder> [--template <dump>\\cp_zmb]
    blender -b map.blend --python blend2iwz.py -- validate

Units: 1 Blender unit = 1 metre = 39.37 IW7 inches (the preview uses the same factor). Axes are the same as IW7 (x east,
y north, z up), so nothing is swapped. Yaw is the rotation about Z in degrees (0 = +x, counter-clockwise).

What is read (no add-on needs to be registered: everything is plain custom properties, so a .blend exports from the
command line on any Blender 4/5):
  meshes in collection IWZ_World (children included)   material slot name = IW7 world material (w/...)
        obj["iwz_stair"] a stair name on every step mesh of one flight: the exporter adds the stock clip ramp sheet over the nosings
        obj["iwz_mode"]  both (default) | render | collision      obj["iwz_tag"] int (collision surface tag, experts)
        obj["iwz_uv"]    auto (default: world aligned at the material's real scale) | authored (the mesh uv map, v flipped)
  objects with obj["iwz_kind"]: zone door start spawner power perk wall_buy pap wheel marker (see README.md)
  objects with obj["iwz_model"]: static props (a stock xmodel placed; location, rotation (roll, pitch, yaw), uniform scale)
  light objects (point -> omni, spot -> spot), cameras (-> layout.json views)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

IN_PER_BU = 1.0 / 0.0254
WORLD_COLLECTION = 'IWZ_World'
EXCLUDED_COLLECTIONS = ('IWZ_Base', 'IWZ_Base_Replaced', 'IWZ_Gameplay')    # context of a section: never exported


def _bpy():
    import bpy
    return bpy


def _prop(obj, key, default=None):
    try:
        v = obj.get(key, default)
    except Exception:
        return default
    if hasattr(v, 'to_list'):
        return v.to_list()
    return v


def _in(v):
    return float(v) * IN_PER_BU


def _loc(obj):
    t = obj.matrix_world.translation
    return [_in(t.x), _in(t.y), _in(t.z)]


def _yaw(obj):
    return math.degrees(obj.matrix_world.to_euler().z) % 360.0


def _bbox_in(obj):
    """axis aligned world box of a mesh object, or of an empty drawn as a cube (display size x scale), in inches"""
    from mathutils import Vector
    if obj.type == 'MESH':
        pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    else:
        s = obj.empty_display_size
        sc = obj.matrix_world.to_scale()
        c = obj.matrix_world.translation
        pts = [Vector((c.x + sx * s * abs(sc.x), c.y + sy * s * abs(sc.y), c.z + sz * s * abs(sc.z))) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return [round(_in(min(p[i] for p in pts)), 2) for i in range(3)] + [round(_in(max(p[i] for p in pts)), 2) for i in range(3)]      # 0.01 inch: metre float noise must not move a box edge across a lattice centre


def _all_objects_of(coll):
    out = list(coll.objects)
    for c in coll.children:
        out += _all_objects_of(c)
    return out


def mesh_records(obj, depsgraph):
    """one record per material slot with triangles in world inches"""
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        me.calc_loop_triangles()
        mw = ev.matrix_world
        flip = mw.determinant() < 0
        uvl = me.uv_layers.get('UVMap') or me.uv_layers.active
        lml = me.uv_layers.get('lightmap') if str(_prop(obj, 'iwz_lm', '')) == 'keep' else None
        authored = str(_prop(obj, 'iwz_uv', 'auto')) == 'authored' and uvl is not None
        mode = str(_prop(obj, 'iwz_mode', 'both'))
        tag = _prop(obj, 'iwz_tag', None)
        stair = _prop(obj, 'iwz_stair', None)
        stair = None if stair in (None, 0, False, '') else (str(stair) if not isinstance(stair, (int, float)) else 'stair')
        slots = [(s.material.name if s and s.material else None) for s in obj.material_slots] or [None]
        by = {}
        verts = [mw @ v.co for v in me.vertices]
        for lt in me.loop_triangles:
            name = slots[lt.material_index] if lt.material_index < len(slots) else slots[0]
            r = by.setdefault(name, {'tris': [], 'uvs': [], 'lms': []})
            ids = list(lt.vertices)
            lp = list(lt.loops)
            if flip:
                ids = [ids[0], ids[2], ids[1]]; lp = [lp[0], lp[2], lp[1]]
            r['tris'].append([[_in(verts[i].x), _in(verts[i].y), _in(verts[i].z)] for i in ids])
            if authored:
                r['uvs'].append([list(uvl.data[l].uv) for l in lp])
            if lml is not None:
                r['lms'].append([list(lml.data[l].uv) for l in lp])
        out = []
        for name, r in by.items():
            out.append({'name': obj.name, 'material': name or '', 'mode': mode, 'tag': tag, 'stair': stair, 'tris': r['tris'], 'uvs': r['uvs'] or None, 'lms': r['lms'] or None})
        return out
    finally:
        ev.to_mesh_clear()


def _excluded_objects():
    """names of the objects in the context collections (IWZ_Base, IWZ_Base_Replaced, IWZ_Gameplay, children included)"""
    bpy = _bpy()
    names = set()
    for cn in EXCLUDED_COLLECTIONS:
        c = bpy.data.collections.get(cn)
        if c:
            names |= {o.name for o in _all_objects_of(c)}
    return names


def _plane_info(obj):
    """(world bounding box in inches, unit normal of the first polygon) of a plane mesh"""
    from mathutils import Vector
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    bb = [round(_in(min(p[i] for p in pts)), 3) for i in range(3)] + [round(_in(max(p[i] for p in pts)), 3) for i in range(3)]
    n = mw.to_3x3() @ Vector(obj.data.polygons[0].normal) if len(obj.data.polygons) else Vector((0, 0, 1))
    n.normalize()
    return bb, [n.x, n.y, n.z]


def collect_scene(scene=None, log=print, section=False):
    """-> scene dict of blend_core (inches); `section` also collects decals, signs, effects, links and keeps camera zones empty for the
    section exporter to fill"""
    import section_core as SC
    bpy = _bpy()
    scene = scene or bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    out = {'schema': 'iwz.blend/1', 'map': str(scene.get('iwz_map', 'cp_iwz')), 'source': os.path.basename(bpy.data.filepath) or 'unsaved.blend',
           'meshes': [], 'zones': [], 'starts': [], 'spawners': [], 'doors': [], 'power': [], 'perks': [], 'wall_buys': [], 'pap': [],
           'wheels': [], 'lights': [], 'props': [], 'markers': [], 'links': []}
    if scene.get('iwz_ambient'):
        out['ambient'] = list(scene['iwz_ambient'].to_list() if hasattr(scene['iwz_ambient'], 'to_list') else scene['iwz_ambient'])
    extra = bpy.data.texts.get('iwz_layout_extra')
    if extra:
        try:
            out['extra_layout'] = json.loads(extra.as_string())
        except ValueError as e:
            log('iwz_layout_extra is not JSON: %s' % e)
    out.update(decals=[], signs=[], fx=[], links=[])
    world = bpy.data.collections.get(WORLD_COLLECTION)
    world_objs = set(o.name for o in _all_objects_of(world)) if world else set()
    skip = _excluded_objects()
    views = {}
    for obj in scene.objects:
        if obj.name in skip:
            continue
        kind = _prop(obj, 'iwz_kind')
        if kind is None and obj.name in world_objs and obj.type == 'MESH':
            out['meshes'] += mesh_records(obj, dg)
            continue
        if kind is None and _prop(obj, 'iwz_model'):
            ang = obj.matrix_world.to_euler()
            out['props'].append({'model': str(_prop(obj, 'iwz_model')), 'at': _loc(obj), 'scale': obj.matrix_world.to_scale().x,
                                 'angles': [math.degrees(ang.y), math.degrees(ang.z) % 360.0, math.degrees(ang.x)],
                                 'static': bool(_prop(obj, 'iwz_static', 1)), 'clip': bool(_prop(obj, 'iwz_clip', 0))})
            continue
        if obj.type == 'LIGHT':
            L = obj.data
            if L.type not in ('POINT', 'SPOT'):
                continue
            rec = {'at': _loc(obj), 'type': 'spot' if L.type == 'SPOT' else 'omni', 'color': list(L.color)[:3],
                   'radius': float(_prop(obj, 'iwz_radius', _in(L.cutoff_distance) if L.use_custom_distance else 420.0)),
                   'intensity': float(_prop(obj, 'iwz_intensity', 2.0)), 'group': str(_prop(obj, 'iwz_group', '') or ''),
                   'name': str(_prop(obj, 'iwz_name', '') or ''), 'runtime': bool(_prop(obj, 'iwz_runtime', 0)),
                   'fixture': str(_prop(obj, 'iwz_fixture', '') or '')}
            if L.type == 'SPOT':
                d = obj.matrix_world.to_3x3() @ __import__('mathutils').Vector((0, 0, -1))
                rec.update(dir=[d.x, d.y, d.z], outer=math.degrees(L.spot_size) / 2, inner=math.degrees(L.spot_size) / 2 * (1 - L.spot_blend))
            out['lights'].append(rec)
            continue
        if obj.type == 'CAMERA':
            zone = str(_prop(obj, 'iwz_zone', '' if section else 'main'))
            t = obj.matrix_world.translation
            e = obj.matrix_world.to_euler()
            yaw = (math.degrees(e.z) + 90.0) % 360.0         # camera rotation (90, 0, 0) looks along +y = IW7 yaw 90
            views.setdefault(zone, []).append([_in(t.x), _in(t.y), _in(t.z) - 60.0, yaw, -(math.degrees(e.x) - 90.0)])
            continue
        if kind is None:
            continue
        kind = str(kind)
        name = str(_prop(obj, 'iwz_name', obj.name) or obj.name)
        at = _loc(obj)
        yaw = _yaw(obj)
        if kind in ('decal', 'sign') and obj.type == 'MESH':
            bb, nrm = _plane_info(obj)
            recs = mesh_records(obj, dg)
            mat = recs[0]['material'] if recs else str(_prop(obj, 'iwz_material', ''))
            path, key = SC.resolve_material(str(_prop(obj, 'iwz_material', '') or mat))
            for r in recs:
                r.update(material=path, mode='render', free_material=True)
                out['meshes'].append(r)
            row = SC.plane_row(kind, bb, nrm, key, image=str(_prop(obj, 'iwz_image', '') or key), off=float(_prop(obj, 'iwz_off', 3.6 if kind == 'sign' else 0.4)),
                               hanging=bool(_prop(obj, 'iwz_hanging', 0)))
            if row:
                out['decals' if kind == 'decal' else 'signs'].append(row)
            continue
        if kind == 'fx':
            out['fx'].append({'fx': str(_prop(obj, 'iwz_fx', '')), 'origin': [round(v, 2) for v in at], 'zone': None, 'repeat': bool(_prop(obj, 'iwz_repeat', 1))})
            continue
        if kind == 'link':
            zs = [z.strip() for z in str(_prop(obj, 'iwz_zones', '') or '').split(',') if z.strip()]
            if len(zs) == 2:
                out['links'].append(zs)
            continue
        if kind == 'zone':
            zr = {'name': name, 'box': _bbox_in(obj), 'probe': _prop(obj, 'iwz_probe', None) or [0.9, 0.9, 0.95, 0.6]}
            for k in ('floor', 'ceiling'):
                if _prop(obj, 'iwz_' + k) is not None:
                    zr[k] = float(_prop(obj, 'iwz_' + k))
            out['zones'].append(zr)
        elif kind == 'door':
            zs = [z.strip() for z in str(_prop(obj, 'iwz_zones', '') or '').split(',') if z.strip()]
            out['doors'].append({'name': name, 'cost': int(_prop(obj, 'iwz_cost', 750)), 'box': _bbox_in(obj), 'zones': zs or None})
        elif kind == 'start':
            out['starts'].append({'at': at, 'yaw': yaw})
        elif kind == 'spawner':
            out['spawners'].append({'at': at, 'yaw': yaw, 'kind': str(_prop(obj, 'iwz_spawn', 'ground')), 'vent': bool(_prop(obj, 'iwz_vent', 1))})
        elif kind == 'power':
            out['power'].append({'at': at, 'yaw': yaw})
        elif kind == 'perk':
            out['perks'].append({'at': at, 'yaw': yaw, 'perk': str(_prop(obj, 'iwz_perk', 'revive')), 'powered': bool(_prop(obj, 'iwz_powered', 0))})
        elif kind == 'wall_buy':
            out['wall_buys'].append({'at': at, 'yaw': yaw, 'weapon_class': str(_prop(obj, 'iwz_weapon_class', 'smg')) or None,
                                     'weapon': str(_prop(obj, 'iwz_weapon', '') or '') or None, 'cost': int(_prop(obj, 'iwz_cost', 1000)),
                                     'model': str(_prop(obj, 'iwz_model_name', '') or '') or None})
        elif kind == 'pap':
            out['pap'].append({'at': at, 'yaw': yaw})
        elif kind == 'wheel':
            out['wheels'].append({'at': at, 'yaw': yaw})
        elif kind == 'marker':
            out['markers'].append({'kind': str(_prop(obj, 'iwz_marker', 'marker')), 'id': name, 'at': at, 'yaw': yaw})
        else:
            log('object %s: unknown iwz_kind %r (ignored)' % (obj.name, kind))
    if views:
        if section:
            out['views'] = views
        else:
            out.setdefault('extra_layout', {}).setdefault('views', views)
    for z in out['zones']:
        z['probe'] = list(z['probe'])
    return out


def collect_section(scene=None, log=print):
    """-> section scene dict (section_core): the scene plus the section properties of the .blend (iwz_section_name, iwz_section_mode,
    iwz_zone, iwz_base_emit)"""
    bpy = _bpy()
    scene = scene or bpy.context.scene
    sc = collect_scene(scene, log, section=True)
    name = str(scene.get('iwz_section_name') or os.path.splitext(os.path.basename(bpy.data.filepath))[0] or 'section')
    sc['section'] = {'name': name, 'mode': str(scene.get('iwz_section_mode') or 'replace'), 'zone': str(scene.get('iwz_zone') or ''),
                     'base': str(scene.get('iwz_base_emit') or '')}
    return sc


def run_export_section(out_dir, base=None, log=print):
    """export the open scene as a section folder (None: validate only); raises ValueError with every error"""
    import section_core as SC
    sc = collect_section(log=log)
    base_path = base or sc['section']['base']
    if not base_path or not os.path.isfile(os.path.join(base_path, 'layout.json')):
        raise ValueError('the base emit %r has no layout.json: import the base first (iwz2blend.py import-base) or pass --base' % base_path)
    return SC.build_section(sc, out_dir, SC.Base(base_path), log)


def run_export(out_dir, template=None, log=print):
    import blend_core
    scene = collect_scene(log=log)
    issues = blend_core.validate(scene)
    for s, m in issues:
        log('%s %s' % (s, m))
    return blend_core.export_scene(scene, out_dir, template, log)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog='blend2iwz')
    ap.add_argument('cmd', choices=['export', 'validate', 'export-section', 'validate-section'])
    ap.add_argument('--out')
    ap.add_argument('--base')
    ap.add_argument('--template')
    a = ap.parse_args(argv)
    import blend_core
    if a.cmd == 'validate':
        sc = collect_scene()
        iss = blend_core.validate(sc)
        for s, m in iss:
            print(s, m)
        print('%d errors, %d warnings; %d meshes, %d zones' % (sum(1 for s, _ in iss if s == 'ERROR'), sum(1 for s, _ in iss if s == 'WARN'),
                                                                len(sc['meshes']), len(sc['zones'])))
        return 1 if any(s == 'ERROR' for s, _ in iss) else 0
    if a.cmd in ('export-section', 'validate-section'):
        if a.cmd == 'export-section' and not a.out:
            ap.error('export-section needs --out')
        try:
            rep = run_export_section(a.out if a.cmd == 'export-section' else None, a.base)
        except ValueError as e:
            print(e)
            return 1
        for w in rep['warnings']:
            print('WARN', w)
        print('budgets', json.dumps(rep['budgets']))
        return 0
    if not a.out:
        ap.error('export needs --out')
    run_export(a.out, a.template)
    return 0


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        sys.exit(main(argv))
