"""Authors testmap1 in Blender the way a map author would (meshes in IWZ_World, entities as empties with custom properties),
saves the .blend and exports the emit folder.

    blender -b --factory-startup --python make_testmap1.py -- --out <folder>      # <folder>/testmap1.blend and <folder>/emit

Two ground rooms (A, B, 480 x 400 inches) joined by a door (cost 750); a flight of 17 steps in room A up to an upper floor room
over room A; a power switch, one perk machine (Up 'N Atoms), one wall buy (smg), 6 zombie spawners (2 in room A, 2 in room B,
2 on the upper floor), 2 player starts, lights. Sizes are written in IW7 inches and converted to metres (1 BU = 1 m).
"""
import os
import sys

import bpy
import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
IN = 0.0254

ROOM_H = 128          # ground rooms: floor 0, slab underside 128
SLAB = 8
UP_FLOOR = ROOM_H + SLAB          # 136
UP_H = 128


def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def material(name):
    m = bpy.data.materials.get(name)
    if not m:
        m = bpy.data.materials.new(name)
        m.diffuse_color = (0.55, 0.55, 0.52, 1.0)
    return m


def box(c, name, mn, mx, mat=None, mode='both'):
    """axis aligned box, outward faces, corners in inches"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    x0, y0, z0 = [v * IN for v in mn]
    x1, y1, z1 = [v * IN for v in mx]
    v = [bm.verts.new(p) for p in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        bm.faces.new([v[i] for i in f])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    c.objects.link(o)
    if mat:
        me.materials.append(material(mat))
    o['iwz_mode'] = mode
    return o


def volume(c, name, kind, mn, mx, **props):
    o = box(c, name, mn, mx, None, 'render')
    o.display_type = 'WIRE'
    o['iwz_kind'] = kind
    o['iwz_name'] = name
    for k, v in props.items():
        o[k] = v
    return o


def entity(c, name, kind, at, yaw=0.0, **props):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'ARROWS'
    o.empty_display_size = 0.4
    o.location = [v * IN for v in at]
    o.rotation_euler = (0, 0, yaw * 3.14159265 / 180)
    o['iwz_kind'] = kind
    for k, v in props.items():
        o[k] = v
    c.objects.link(o)
    return o


def light(c, name, at, color=(1.0, 0.82, 0.55), radius=420.0, intensity=2.0):
    d = bpy.data.lights.new(name, 'POINT')
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.location = [v * IN for v in at]
    o['iwz_radius'] = radius
    o['iwz_intensity'] = intensity
    c.objects.link(o)
    return o


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc['iwz_map'] = 'cp_iwz'
    W, E, Z = coll('IWZ_World'), coll('IWZ_Entities'), coll('IWZ_Zones')
    FLOOR, WALL, CEIL, TREAD = 'w/concrete_tiles_01', 'w/concrete_wall_12_lined_dirty', 'w/ceiling_tile_01', 'w/rubber_non_skid_stair_01'
    # ground floor slab under both rooms and the walls
    box(W, 'floor', (-16, -16, -SLAB), (992, 416, 0), FLOOR)
    # outer walls of the ground rooms (to the underside of the upper slab) and of the upper room
    top = UP_FLOOR + UP_H
    box(W, 'wall_south', (-16, -16, 0), (992, 0, top), WALL)
    box(W, 'wall_north', (-16, 400, 0), (992, 416, top), WALL)
    box(W, 'wall_west', (-16, 0, 0), (0, 400, top), WALL)
    box(W, 'wall_east_b', (976, 0, 0), (992, 400, ROOM_H + SLAB), WALL)
    # the wall between the rooms with a doorway 100 wide, 96 high (the door box stands in it)
    box(W, 'wall_mid_a', (480, 0, 0), (496, 150, top), WALL)
    box(W, 'wall_mid_b', (480, 250, 0), (496, 400, top), WALL)
    box(W, 'wall_mid_lintel', (480, 150, 96), (496, 250, top), WALL)
    # room B ceiling
    box(W, 'ceiling_b', (496, 0, ROOM_H), (976, 400, ROOM_H + SLAB), CEIL)
    # upper floor slab over room A with a stairwell (x 60..349, y 288..400)
    box(W, 'slab_a1', (0, 0, ROOM_H), (480, 288, UP_FLOOR), FLOOR)
    box(W, 'slab_a2', (0, 288, ROOM_H), (60, 400, UP_FLOOR), FLOOR)
    box(W, 'slab_a3', (349, 288, ROOM_H), (480, 400, UP_FLOOR), FLOOR)
    box(W, 'upper_ceiling', (0, 0, top), (496, 400, top + SLAB), CEIL)
    # stair: 17 steps, riser 8, tread 17, 112 wide, from x 60 (z 0) to x 349 (z 136), rising toward +x
    for i in range(17):
        box(W, 'step_%02d' % i, (60 + 17 * i, 288, 0), (60 + 17 * (i + 1), 400, 8 * (i + 1)), TREAD)
    # zones (axis aligned boxes; stacked zones split at the slab)
    volume(Z, 'room_a', 'zone', (0, 0, -16), (480, 400, 132))
    volume(Z, 'room_b', 'zone', (496, 0, -16), (976, 400, 132))
    volume(Z, 'upper', 'zone', (0, 0, 132), (480, 400, top + 8))
    volume(Z, 'door_ab', 'door', (480, 150, 0), (496, 250, 96), iwz_cost=750, iwz_zones='room_a,room_b')
    # entities
    entity(E, 'start_1', 'start', (80, 100, 0), 0)
    entity(E, 'start_2', 'start', (80, 160, 0), 0)
    entity(E, 'spawn_a1', 'spawner', (300, 60, 0), 90, iwz_spawn='ground')
    entity(E, 'spawn_a2', 'spawner', (400, 220, 0), 180, iwz_spawn='ground')
    entity(E, 'spawn_b1', 'spawner', (800, 80, 0), 90, iwz_spawn='ground')
    entity(E, 'spawn_b2', 'spawner', (900, 300, 0), 180, iwz_spawn='ground')
    entity(E, 'spawn_u1', 'spawner', (150, 100, UP_FLOOR), 0, iwz_spawn='ground')
    entity(E, 'spawn_u2', 'spawner', (400, 100, UP_FLOOR), 180, iwz_spawn='ground')
    entity(E, 'power', 'power', (20, 220, 0), 0)
    entity(E, 'perk_revive', 'perk', (900, 20, 0), 90, iwz_perk='revive')
    entity(E, 'buy_smg', 'wall_buy', (600, 20, 0), 90, iwz_weapon_class='smg', iwz_cost=1000)
    for i, (x, y, z) in enumerate([(120, 200, 100), (360, 200, 100), (620, 200, 100), (860, 200, 100), (240, 200, UP_FLOOR + 100)]):
        light(E, 'light_%d' % i, (x, y, z))
    sc['iwz_ambient'] = [0.30, 0.30, 0.32, 0.50]


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = argv[argv.index('--out') + 1] if '--out' in argv else os.path.join(os.getcwd(), 'testmap1')
    os.makedirs(out, exist_ok=True)
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'testmap1.blend'))
    import blend2iwz
    blend2iwz.run_export(os.path.join(out, 'emit'))


if __name__ == '__main__':
    main()
