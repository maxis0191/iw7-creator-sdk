"""IWZ emit folder -> Blender scene (the reverse of blend2iwz.py), to author on an existing map or to prove the round trip.

    blender -b --factory-startup --python iwz2blend.py -- <emit folder> --save out.blend [--no-collision]

World: one object per world.bin surface in collection IWZ_World, mode render, authored uv (v flipped), the baked lightmap uv in a second uv
map `lightmap` (obj["iwz_lm"] = "keep": the exporter writes it back). Collision: colmap.hkx decoded (hkcm.decode_cm_data) into one
collision-only object per surface tag. Entities come from layout.json: zones (its `volumes`), doors, player starts, spawners, perk
machines, power, Pack-a-Punch, wall buys, mystery boxes, markers, lights (omni / spot), props (smodels.txt). What the exporter does not
model (layout keys such as decor, signs, quest, walk, ...) is carried through in the text `iwz_layout_extra` and merged back on export.
1 Blender unit = 1 metre = 39.37 inches.
"""
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
IWZ = os.path.dirname(HERE)
for p in (HERE, IWZ, os.path.join(IWZ, 'preview')):
    if p not in sys.path:
        sys.path.insert(0, p)

IN = 0.0254
MODELLED = {'zones', 'volumes', 'starts', 'spawners', 'doors', 'interactions', 'lights', 'markers', 'openings', 'zone_links', 'regions',
            'navconn_routes', 'far_zones', 'modules', 'blender', 'stairs'}


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def material(name, cache={}):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = (0.55, 0.55, 0.55, 1.0)
    return m


def mesh_object(name, tris, c, mode, mat=None, uvs=None, lms=None, tag=None):
    """tris: list of 3 point tuples (inches)"""
    verts, faces, uvl, lml = [], [], [], []
    for ti, t in enumerate(tris):
        base = len(verts)
        verts += [(p[0] * IN, p[1] * IN, p[2] * IN) for p in t]
        faces.append((base, base + 1, base + 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if uvs is not None:
        layer = me.uv_layers.new(name='UVMap')
        flat = [(u, 1.0 - v) for tri in uvs for (u, v) in tri]
        layer.data.foreach_set('uv', [c_ for uv in flat for c_ in uv])
    if lms is not None:
        layer = me.uv_layers.new(name='lightmap')
        layer.data.foreach_set('uv', [c_ for tri in lms for uv in tri for c_ in uv])
    if mat:
        me.materials.append(material(mat))
    o = bpy.data.objects.new(name, me)
    c.objects.link(o)
    o['iwz_mode'] = mode
    if mode == 'collision':
        o.display_type = 'WIRE'
    if uvs is not None:
        o['iwz_uv'] = 'authored'
    if lms is not None:
        o['iwz_lm'] = 'keep'
    if tag is not None:
        o['iwz_tag'] = int(tag)
    return o


def import_world(src, c, log):
    import iwz_assets as A
    import numpy as np
    w = A.read_world(os.path.join(src, 'world.bin'))
    verts, idx = w['verts'], w['indices']
    n = 0
    for si, s in enumerate(w['surfaces']):
        t = idx[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + int(s['first'])
        pos = verts['pos'][t].astype(float).tolist()
        uv = verts['uv'][t].astype(float).tolist()
        lm = verts['lm'][t].astype(float).tolist()
        mat = w['materials'][int(s['mat'])]
        mesh_object('surf_%d_%s' % (si, mat.split('/')[-1]), [[tuple(p) for p in tri] for tri in pos], c, 'render', mat, uvs=[[tuple(q) for q in tri] for tri in uv],
                    lms=[[tuple(q) for q in tri] for tri in lm])
        n += len(t)
    log('world: %d surfaces, %d triangles' % (len(w['surfaces']), n))


def import_collision(src, c, log):
    from hkpack import Packfile
    import hkcm
    pf = Packfile(open(os.path.join(src, 'colmap.hkx'), 'rb').read())
    for addr, name, _sz in pf.objects:
        if name == 'hknpCompressedMeshShapeData':
            d = hkcm.decode_cm_data(pf, addr)
            by = {}
            for t, g in zip(d['tris'], d['tags']):
                by.setdefault(g, []).append([tuple(v * 32.0 for v in p) for p in t])
            for g, tris in sorted(by.items()):
                mesh_object('collision_tag%d' % g, tris, c, 'collision', None, tag=g)
            log('collision: %d triangles, tags %s' % (len(d['tris']), {k: len(v) for k, v in by.items()}))
            return
    raise ValueError('no collision shape in colmap.hkx')


def box_obj(name, mn, mx, c, kind, **props):
    me = bpy.data.meshes.new(name)
    x0, y0, z0 = [v * IN for v in mn]
    x1, y1, z1 = [v * IN for v in mx]
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    me.from_pydata(v, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    o = bpy.data.objects.new(name, me)
    o.display_type = 'WIRE'
    c.objects.link(o)
    o['iwz_kind'] = kind
    o['iwz_name'] = name
    for k, val in props.items():
        o[k] = val
    return o


def empty(name, kind, at, yaw, c, **props):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'ARROWS'
    o.empty_display_size = 0.4
    o.location = (at[0] * IN, at[1] * IN, at[2] * IN)
    o.rotation_euler = (0, 0, math.radians(yaw))
    c.objects.link(o)
    o['iwz_kind'] = kind
    for k, v in props.items():
        o[k] = v
    return o


def import_entities(src, log):
    import scenegen
    lay = json.load(open(os.path.join(src, 'layout.json'), encoding='utf-8'))
    Z, E = coll('IWZ_Zones'), coll('IWZ_Entities')
    count = {}
    bump = lambda k: count.__setitem__(k, count.get(k, 0) + 1)
    for v in lay.get('volumes', []):
        b = v['box']
        box_obj(v['name'], b[:3], b[3:], Z, 'zone')
        bump('zone')
    for d in lay.get('doors', []):
        if d['axis'] == 1:
            mn, mx = (d['lo'], d['plane'] - 8, d['z0']), (d['hi'], d['plane'] + 8, d['z1'])
        else:
            mn, mx = (d['plane'] - 8, d['lo'], d['z0']), (d['plane'] + 8, d['hi'], d['z1'])
        box_obj(d['name'], mn, mx, Z, 'door', iwz_cost=int(d['cost']), iwz_zones=','.join(d['zones']))
        bump('door')
    for i, s in enumerate(lay.get('starts', [])):
        empty('start_%d' % i, 'start', s, 0, E)
        bump('start')
    for i, s in enumerate(lay.get('spawners', [])):
        o = s['origin']
        z = o[2] if s['kind'] == 'ceiling' else o[2]
        empty('spawn_%d' % i, 'spawner', (o[0], o[1], z), s.get('yaw', 0), E, iwz_spawn=s['kind'], iwz_vent=0)
        bump('spawner')
    perk_names = scenegen.Emitter.PERK_SCRIPTABLE
    for i, it in enumerate(lay.get('interactions', [])):
        k, o, yaw = it.get('kind', ''), it['origin'], it.get('yaw', 0)
        if k.startswith('perk_machine_') and k[13:] in perk_names:
            empty('perk_%s' % k[13:], 'perk', o, yaw, E, iwz_perk=k[13:], iwz_powered=0 if it.get('parameters') == 'requires_power' else 1); bump('perk')
        elif k == 'generator':
            empty('power_%d' % i, 'power', (o[0], o[1], o[2] - 50), yaw, E); bump('power')
        elif k == 'weapon_upgrade':
            empty('pap_%d' % i, 'pap', o, yaw, E); bump('pap')
        elif k == 'magic_wheel':
            empty('wheel_%d' % i, 'wheel', o, yaw, E); bump('wheel')
        elif it.get('groupname') == 'wall_buy':
            empty('buy_%d' % i, 'wall_buy', (o[0], o[1], o[2] - 64), yaw, E, iwz_weapon_class=it.get('class') or '', iwz_weapon=k,
                  iwz_cost=int(it.get('price') or 0), iwz_model_name=it.get('model', '')); bump('wall_buy')
    for i, m in enumerate(lay.get('markers', [])):
        if m.get('origin'):
            empty('%s_%s' % (m['kind'], m.get('id', i)), 'marker', m['origin'], m.get('yaw') or 0, E, iwz_marker=m['kind'], iwz_name=str(m.get('id', i))); bump('marker')
    for i, L in enumerate(lay.get('lights', [])):
        d = bpy.data.lights.new('light_%d' % i, 'SPOT' if L['type'] == 'spot' else 'POINT')
        d.color = L['color'][:3]
        if L['type'] == 'spot':
            d.spot_size = math.radians(L.get('outer', 32) * 2)
            d.spot_blend = 1 - L.get('inner', 14) / max(1e-6, L.get('outer', 32))
        o = bpy.data.objects.new('light_%d' % i, d)
        o.location = [c_ * IN for c_ in L['origin']]
        if L['type'] == 'spot':
            from mathutils import Vector
            dv = Vector(L.get('dir', (0, 0, -1)))
            o.rotation_euler = Vector((0, 0, -1)).rotation_difference(dv).to_euler()
        o['iwz_radius'] = float(L['radius']); o['iwz_intensity'] = float(L['intensity']); o['iwz_group'] = L.get('group', '')
        if L.get('name'):
            o['iwz_name'] = L['name']
        E.objects.link(o)
        bump('light')
    sm = os.path.join(src, 'smodels.txt')
    P = coll('IWZ_Props')
    if os.path.isfile(sm):
        for i, ln in enumerate(open(sm)):
            q = ln.split('#')[0].split()
            if len(q) >= 8:
                o = bpy.data.objects.new(q[0], None)
                o.empty_display_size = 0.2
                o.location = [float(q[1]) * IN, float(q[2]) * IN, float(q[3]) * IN]
                o.rotation_euler = (math.radians(float(q[6])), math.radians(float(q[4])), math.radians(float(q[5])))
                o.scale = (float(q[7]),) * 3
                o['iwz_model'] = q[0]
                P.objects.link(o)
                bump('prop')
    extra = {k: v for k, v in lay.items() if k not in MODELLED}
    t = bpy.data.texts.new('iwz_layout_extra')
    t.write(json.dumps(extra, default=list))
    bpy.context.scene['iwz_map'] = lay.get('map', 'cp_iwz')
    log('entities: %s; carried through: %d layout keys' % (count, len(extra)))
    return count


def import_emit(src, collision=True, log=print):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    import_world(src, coll('IWZ_World'), log)
    if collision:
        import_collision(src, coll('IWZ_World'), log)
    return import_entities(src, log)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--save')
    ap.add_argument('--no-collision', action='store_true')
    a = ap.parse_args(argv)
    import_emit(a.src, not a.no_collision)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)


if __name__ == '__main__':
    if '--' in sys.argv:
        main(sys.argv[sys.argv.index('--') + 1:])
