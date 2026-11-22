"""IW7 zombies map authoring add-on: sidebar panel (N key, tab "IW7") to author a map in Blender and export it.

Install: Edit > Preferences > Add-ons > Install from Disk... on a zip of this folder (zip `iwz_addon`), or keep the folder where it
sits in the repository (`tools-source/iwzmap/blender/iwz_addon`). The add-on finds the exporter (`blend2iwz.py`, `blend_core.py`)
next to its own folder, or in the folder named by IWZ_BLENDER_TOOLS. Everything it writes is plain custom properties (iwz_kind,
iwz_cost, ...), so exporting needs no add-on (`blend2iwz.py -b`). See ../README.md.
"""
bl_info = {
    'name': 'IW7 Zombies map (iwz)',
    'author': 'iw7 creator sdk',
    'version': (0, 1, 0),
    'blender': (4, 2, 0),
    'location': 'View3D > Sidebar > IW7',
    'description': 'Author an IW7 zombies map: world meshes with stock materials, props, entities, lights; validate and export',
    'category': 'Import-Export',
}

import os
import subprocess
import sys

import bpy
from bpy.props import StringProperty, CollectionProperty, PointerProperty


def tools_dir():
    for c in (os.environ.get('IWZ_BLENDER_TOOLS'), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        if c and os.path.isfile(os.path.join(c, 'blend2iwz.py')):
            return c
    return None


def _import_tools():
    d = tools_dir()
    if d and d not in sys.path:
        sys.path.insert(0, d)
    import blend2iwz
    import blend_core
    return blend2iwz, blend_core


def _preview_modules():
    d = tools_dir()
    pv = os.path.join(os.path.dirname(d), 'preview') if d else None
    if pv and pv not in sys.path:
        sys.path.insert(0, pv)
    import iwz_assets
    import iwz_preview
    return iwz_assets, iwz_preview


KINDS = [('zone', 'Zone volume'), ('door', 'Door'), ('start', 'Player start'), ('spawner', 'Zombie spawner'),
         ('power', 'Power switch'), ('perk', 'Perk machine'), ('wall_buy', 'Wall buy'), ('pap', 'Pack-a-Punch'),
         ('wheel', 'Mystery box'), ('marker', 'Marker')]
FIELDS = {
    'zone': [('iwz_name', 'Name')],
    'door': [('iwz_name', 'Name'), ('iwz_cost', 'Cost 750/1000/1250/1500'), ('iwz_zones', 'Zones a,b (empty = detect)')],
    'start': [], 'spawner': [('iwz_spawn', 'ground | wall | ceiling')], 'power': [], 'pap': [], 'wheel': [],
    'perk': [('iwz_perk', 'Perk'), ('iwz_powered', 'Powered from the start')],
    'wall_buy': [('iwz_weapon_class', 'Class'), ('iwz_weapon', 'or stock weapon'), ('iwz_cost', 'Cost')],
    'marker': [('iwz_name', 'Id'), ('iwz_marker', 'Kind')],
}
DEFAULTS = {'door': {'iwz_cost': 750, 'iwz_zones': ''}, 'spawner': {'iwz_spawn': 'ground'}, 'perk': {'iwz_perk': 'revive', 'iwz_powered': 0},
            'wall_buy': {'iwz_weapon_class': 'smg', 'iwz_weapon': '', 'iwz_cost': 1000}, 'marker': {'iwz_marker': 'marker'}}


class IWZ_Name(bpy.types.PropertyGroup):
    pass


class IWZ_Settings(bpy.types.PropertyGroup):
    materials: CollectionProperty(type=IWZ_Name)
    models: CollectionProperty(type=IWZ_Name)
    material: StringProperty(name='Material', description='IW7 world material, w/...')
    model: StringProperty(name='Model', description='stock xmodel')
    out_dir: StringProperty(name='Emit folder', subtype='DIR_PATH', default='//emit')
    template: StringProperty(name='Template dump (cp_zmb)', subtype='DIR_PATH', default='')


def settings():
    return bpy.context.scene.iwz_settings


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if c.name not in [x.name for x in bpy.context.scene.collection.children_recursive]:
        bpy.context.scene.collection.children.link(c)
    return c


def make_material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    try:
        A, P = _preview_modules()
        res = P.MaterialResolver(A.DumpIndex(), {}, None)
        m = res.get(name, 'uv', 'lightmap', object_light=True)
        m.name = name
        return m
    except Exception:                          # dumps or textures missing: a plain material, the name is what matters
        m = bpy.data.materials.new(name)
        m.diffuse_color = (0.6, 0.6, 0.6, 1.0)
        return m


class IWZ_OT_refresh(bpy.types.Operator):
    bl_idname = 'iwz.refresh_catalog'
    bl_label = 'Load stock catalog'
    bl_description = 'list the stock world materials and models from the dumps (IWZ_RUNTIME)'

    def execute(self, ctx):
        A, _ = _preview_modules()
        idx = A.DumpIndex()
        s = settings()
        s.materials.clear()
        s.models.clear()
        for n in sorted(m for m in idx.maps['material'] if m.startswith('w/')):
            s.materials.add().name = n
        for n in sorted(idx.maps['xmodel']):
            s.models.add().name = n
        self.report({'INFO'}, '%d materials, %d models' % (len(s.materials), len(s.models)))
        return {'FINISHED'}


class IWZ_OT_assign_material(bpy.types.Operator):
    bl_idname = 'iwz.assign_material'
    bl_label = 'Assign material'
    bl_description = 'put the picked IW7 material in the active slot of the active object (adds a slot when it has none)'

    def execute(self, ctx):
        o, name = ctx.active_object, settings().material
        if not o or o.type != 'MESH' or not name:
            self.report({'ERROR'}, 'pick a mesh and a material')
            return {'CANCELLED'}
        m = make_material(name)
        if not o.material_slots:
            o.data.materials.append(m)
        else:
            o.material_slots[o.active_material_index].material = m
        return {'FINISHED'}


class IWZ_OT_mode(bpy.types.Operator):
    bl_idname = 'iwz.set_mode'
    bl_label = 'Set mode'
    mode: StringProperty()

    def execute(self, ctx):
        for o in ctx.selected_objects:
            o['iwz_mode'] = self.mode
            if self.mode == 'collision':
                o.display_type = 'WIRE'
            elif o.display_type == 'WIRE':
                o.display_type = 'TEXTURED'
        return {'FINISHED'}


class IWZ_OT_mark_stair(bpy.types.Operator):
    bl_idname = 'iwz.mark_stair'
    bl_label = 'Mark selected as one stair'
    bl_description = 'the selected step meshes are one flight: the exporter adds the stock clip ramp over their nosings (walkable steps over 18 are an error without it)'
    name: StringProperty(default='flight')

    def execute(self, ctx):
        n = 0
        for o in ctx.selected_objects:
            if o.type == 'MESH':
                o['iwz_stair'] = self.name
                n += 1
        self.report({'INFO'}, '%d step meshes marked as stair %s' % (n, self.name))
        return {'FINISHED'}


class IWZ_OT_add_prop(bpy.types.Operator):
    bl_idname = 'iwz.add_prop'
    bl_label = 'Place prop'
    bl_description = 'place the picked stock model at the 3D cursor (objects of one model share one mesh)'

    def execute(self, ctx):
        name = settings().model
        if not name:
            self.report({'ERROR'}, 'pick a model')
            return {'CANCELLED'}
        me = bpy.data.meshes.get('iwzm:' + name)
        if me is None:
            try:
                import numpy as np
                A, P = _preview_modules()
                idx = A.DumpIndex()
                mdl, err = A.read_model(idx, name)
                if mdl is None:
                    raise RuntimeError(err)
                res = P.MaterialResolver(idx, {}, None)
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
                    me.materials.append(res.get(k, 'uv', object_light=True))
            except Exception as e:
                self.report({'WARNING'}, 'model %s not loaded (%s): a box stands in' % (name, e))
                import bmesh
                me = bpy.data.meshes.new('iwzm:' + name)
                bm = bmesh.new()
                bmesh.ops.create_cube(bm, size=0.8)
                bm.to_mesh(me)
                bm.free()
        o = bpy.data.objects.new(name, me)
        o.location = ctx.scene.cursor.location
        o['iwz_model'] = name
        coll('IWZ_Props').objects.link(o)
        return {'FINISHED'}


class IWZ_OT_add_entity(bpy.types.Operator):
    bl_idname = 'iwz.add_entity'
    bl_label = 'Add entity'
    kind: StringProperty()

    def execute(self, ctx):
        kind = self.kind
        n = len([x for x in bpy.data.objects if x.get('iwz_kind') == kind]) + 1
        if kind in ('zone', 'door'):
            import bmesh
            me = bpy.data.meshes.new(kind)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new('%s_%d' % (kind, n), me)
            o.display_type = 'WIRE'
            o.scale = (4, 4, 2) if kind == 'zone' else (0.4, 1.2, 1.2)
            o['iwz_name'] = o.name
            coll('IWZ_Zones').objects.link(o)
        else:
            o = bpy.data.objects.new('%s_%d' % (kind, n), None)
            o.empty_display_type = 'ARROWS'
            o.empty_display_size = 0.4
            coll('IWZ_Entities').objects.link(o)
        o.location = ctx.scene.cursor.location
        o['iwz_kind'] = kind
        for k, v in DEFAULTS.get(kind, {}).items():
            o[k] = v
        for obj in ctx.selected_objects:
            obj.select_set(False)
        o.select_set(True)
        ctx.view_layer.objects.active = o
        return {'FINISHED'}


class IWZ_OT_add_light(bpy.types.Operator):
    bl_idname = 'iwz.add_light'
    bl_label = 'Add light'

    def execute(self, ctx):
        d = bpy.data.lights.new('iwz_light', 'POINT')
        d.color = (1.0, 0.82, 0.55)
        o = bpy.data.objects.new('iwz_light', d)
        o.location = ctx.scene.cursor.location
        o['iwz_radius'] = 420.0
        o['iwz_intensity'] = 2.0
        o['iwz_group'] = ''
        coll('IWZ_Entities').objects.link(o)
        return {'FINISHED'}


class IWZ_OT_validate(bpy.types.Operator):
    bl_idname = 'iwz.validate'
    bl_label = 'Validate'

    def execute(self, ctx):
        b, c = _import_tools()
        sc = b.collect_scene()
        iss = c.validate(sc)
        for sev, msg in iss:
            self.report({'ERROR' if sev == 'ERROR' else 'WARNING'}, msg)
        ctx.scene['iwz_last_validate'] = '%d errors, %d warnings' % (sum(1 for s, _ in iss if s == 'ERROR'), sum(1 for s, _ in iss if s == 'WARN'))
        self.report({'INFO'}, 'validate: %s; %d meshes, %d zones' % (ctx.scene['iwz_last_validate'], len(sc['meshes']), len(sc['zones'])))
        return {'FINISHED'}


class IWZ_OT_export(bpy.types.Operator):
    bl_idname = 'iwz.export'
    bl_label = 'Export emit'

    def execute(self, ctx):
        b, c = _import_tools()
        s = settings()
        out = bpy.path.abspath(s.out_dir)
        try:
            rep = b.run_export(out, bpy.path.abspath(s.template) or None, log=print)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        self.report({'INFO'}, 'emit written to %s (%d problems, %d warnings)' % (out, len(rep['problems']), len(rep['warnings'])))
        return {'FINISHED'}


class IWZ_OT_preview(bpy.types.Operator):
    bl_idname = 'iwz.preview'
    bl_label = 'Preview looks'
    bl_description = 'render the look cameras of the emit with preview/iwz_preview_render.py (it reads bake.npz, so the emit must be baked)'

    def execute(self, ctx):
        s = settings()
        out = bpy.path.abspath(s.out_dir)
        pv = os.path.join(os.path.dirname(tools_dir()), 'preview', 'iwz_preview_render.py')
        dst = os.path.join(out, 'preview')
        r = subprocess.run([os.environ.get('IWZ_PYTHON', 'python'), '-B', pv, 'render', '--src', out, '--out', dst, '--views', 'all'],
                           capture_output=True, text=True)
        if r.returncode:
            self.report({'ERROR'}, 'preview failed: ' + (r.stderr or r.stdout)[-300:])
            return {'CANCELLED'}
        self.report({'INFO'}, 'frames in ' + dst)
        return {'FINISHED'}


class IWZ_PT_main(bpy.types.Panel):
    bl_label = 'IW7 map'
    bl_idname = 'IWZ_PT_main'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IW7'

    def draw(self, ctx):
        L, s = self.layout, ctx.scene.iwz_settings
        L.label(text='1 BU = 1 m = 39.37 in')
        L.operator('iwz.refresh_catalog', icon='FILE_REFRESH')
        b = L.box()
        b.label(text='World geometry (collection IWZ_World)')
        b.prop_search(s, 'material', s, 'materials', text='Material')
        b.operator('iwz.assign_material', icon='MATERIAL')
        r = b.row()
        for m, t in (('both', 'Render + collision'), ('render', 'Render only'), ('collision', 'Clip')):
            r.operator('iwz.set_mode', text=t).mode = m
        b.operator('iwz.mark_stair', icon='SORT_ASC')
        o = ctx.active_object
        if o and o.type == 'MESH' and o.get('iwz_kind') is None:
            b.label(text='%s: mode %s, uv %s' % (o.name, o.get('iwz_mode', 'both'), o.get('iwz_uv', 'auto')))
        b = L.box()
        b.label(text='Props')
        b.prop_search(s, 'model', s, 'models', text='Model')
        b.operator('iwz.add_prop', icon='OBJECT_DATA')
        b = L.box()
        b.label(text='Entities (at the 3D cursor)')
        col = b.column(align=True)
        for k, label in KINDS:
            col.operator('iwz.add_entity', text=label).kind = k
        col.operator('iwz.add_light', text='Light', icon='LIGHT')
        if o and o.get('iwz_kind') is not None:
            e = L.box()
            e.label(text='%s (%s)' % (o.name, o['iwz_kind']))
            for key, label in FIELDS.get(str(o['iwz_kind']), []):
                if key in o:
                    e.prop(o, '["%s"]' % key, text=label)
        elif o and o.type == 'LIGHT':
            e = L.box()
            e.label(text='Light')
            for key, label in (('iwz_radius', 'Radius (in)'), ('iwz_intensity', 'Intensity'), ('iwz_group', 'Group'), ('iwz_name', 'Name'),
                               ('iwz_runtime', 'Runtime light (lights.txt)')):
                if key in o:
                    e.prop(o, '["%s"]' % key, text=label)
        b = L.box()
        b.label(text='Export')
        b.prop(s, 'out_dir')
        b.prop(s, 'template')
        r = b.row()
        r.operator('iwz.validate', icon='CHECKMARK')
        r.operator('iwz.export', icon='EXPORT')
        r.operator('iwz.preview', icon='RENDER_STILL')
        if ctx.scene.get('iwz_last_validate'):
            b.label(text=str(ctx.scene['iwz_last_validate']))


CLASSES = (IWZ_Name, IWZ_Settings, IWZ_OT_refresh, IWZ_OT_assign_material, IWZ_OT_mode, IWZ_OT_mark_stair, IWZ_OT_add_prop, IWZ_OT_add_entity,
           IWZ_OT_add_light, IWZ_OT_validate, IWZ_OT_export, IWZ_OT_preview, IWZ_PT_main)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.iwz_settings = PointerProperty(type=IWZ_Settings)


def unregister():
    del bpy.types.Scene.iwz_settings
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
