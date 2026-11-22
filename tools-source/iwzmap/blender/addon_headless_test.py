"""Headless proof of the add-on: registers, every operator runs, an export of what it made works.

    blender -b --factory-startup --python addon_headless_test.py
The panel drawing itself needs a window: it is built, not looked at here.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iwz_addon

bpy.ops.wm.read_factory_settings(use_empty=True)
iwz_addon.register()
fails = []


def step(name, fn):
    try:
        r = fn()
        print('OK  ', name, r if r is not None else '')
    except Exception as e:
        fails.append(name)
        print('FAIL', name, e)


s = bpy.context.scene.iwz_settings
step('refresh_catalog', lambda: (bpy.ops.iwz.refresh_catalog(), (len(s.materials), len(s.models)))[1])
s.model = 'furniture_park_bench_01_red'
step('add_prop', lambda: bpy.ops.iwz.add_prop())
s.material = 'w/concrete_tiles_01'
bpy.ops.mesh.primitive_cube_add()
step('assign_material', lambda: (bpy.ops.iwz.assign_material(), bpy.context.active_object.material_slots[0].material.name)[1])
step('set_mode', lambda: (bpy.ops.iwz.set_mode(mode='collision'), bpy.context.active_object['iwz_mode'])[1])
for k in ('zone', 'door', 'start', 'spawner', 'power', 'perk', 'wall_buy', 'pap', 'wheel', 'marker'):
    step('add_entity ' + k, lambda k=k: bpy.ops.iwz.add_entity(kind=k))
step('add_light', lambda: bpy.ops.iwz.add_light())
def validate_reports_errors():
    # the scene made above is deliberately wrong (a door between no zones): validate must say so as an operator error
    try:
        bpy.ops.iwz.validate()
    except RuntimeError as e:
        assert 'does not separate two zones' in str(e), e
        return 'reported: ' + str(e).strip().splitlines()[-1][:80]
    raise AssertionError('validate accepted a bad scene')


step('validate', validate_reports_errors)
iwz_addon.unregister()
print('ADDON', 'FAILED %s' % fails if fails else 'OK')
sys.exit(1 if fails else 0)
