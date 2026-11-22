"""Stage 2 of the contact sheets, inside Blender: render one 3/4 view PNG tile per prepared model.

  blender -b --factory-startup --python blender_tiles.py -- <job.json>

job.json: {"res": 256, "engine": "EEVEE" | "WORKBENCH", "items": [{"name", "prep": "<prep dir>/<safe>", "out": "<png>"}]}
Writes a result list next to the job (<job>.result.json): name -> {"ok": bool, "reason": str|null, "seconds": float}.
Textures are the decoded colour maps of prep.py, a neutral grey world and one sun, no model specific light. A surface
whose material did not resolve is drawn magenta (never a fake colour); alpha tested / blended techsets use the image alpha.
"""
import json
import math
import os
import sys
import time

import bpy
import numpy as np

S = 0.0254
MAGENTA = (1.0, 0.0, 1.0, 1.0)


def setup(res, engine):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc.render.engine = 'BLENDER_EEVEE' if engine == 'EEVEE' else 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.view_settings.view_transform = 'Standard'
    sc.display_settings.display_device = 'sRGB'
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.20, 0.20, 0.21, 1)
    bg.inputs['Strength'].default_value = 1.0
    if engine == 'EEVEE':
        try:
            sc.eevee.taa_render_samples = 8
        except Exception:
            pass
    else:
        sh = sc.display.shading
        sh.light = 'STUDIO'
        sh.color_type = 'TEXTURE'
        sh.show_cavity = False
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 3.0
    so = bpy.data.objects.new('sun', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    cam = bpy.data.cameras.new('cam')
    cam.lens = 60
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    return sc, co


def make_material(name, rec, images):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    pr.inputs['Roughness'].default_value = 0.7
    nt.links.new(pr.outputs['BSDF'], out.inputs['Surface'])
    png = rec.get('png')
    if not png or not os.path.isfile(png):
        pr.inputs['Base Color'].default_value = MAGENTA
        mat['unresolved'] = rec.get('reason') or 'no image'
        return mat, False
    img = bpy.data.images.load(png, check_existing=True)
    img_name = img.name
    img.colorspace_settings.name = 'sRGB'
    # the PNG alpha of lit colour maps is a data channel (gloss), only alpha tested / blended techsets use it as opacity
    img.alpha_mode = 'CHANNEL_PACKED'
    images.append(img.name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.extension = 'REPEAT'
    tint = rec.get('tint') or [1, 1, 1, 1]
    if tuple(round(t, 3) for t in tint[:3]) != (1.0, 1.0, 1.0):
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        mix.inputs['B'].default_value = (tint[0], tint[1], tint[2], 1)
        nt.links.new(tex.outputs['Color'], mix.inputs['A'])
        nt.links.new(mix.outputs['Result'], pr.inputs['Base Color'])
    else:
        nt.links.new(tex.outputs['Color'], pr.inputs['Base Color'])
    if rec.get('alpha'):
        nt.links.new(tex.outputs['Alpha'], pr.inputs['Alpha'])
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass
    return mat, True


def build(item, images):
    base = item['prep']
    info = json.load(open(base + '.json'))
    if info.get('error'):
        return None, info['error'], []
    z = np.load(base + '.npz')
    pos, uv, tris, sid = z['pos'], z['uv'], z['tris'], z['sid']
    me = bpy.data.meshes.new(item['name'])
    me.vertices.add(len(pos))
    me.vertices.foreach_set('co', (pos * S).astype(np.float32).ravel())
    me.loops.add(len(tris) * 3)
    me.loops.foreach_set('vertex_index', tris.ravel())
    me.polygons.add(len(tris))
    me.polygons.foreach_set('loop_start', np.arange(0, len(tris) * 3, 3, dtype=np.int32))
    lay = me.uv_layers.new(name='uv')
    lay.data.foreach_set('uv', (uv[tris.ravel()] * np.array([1, -1], np.float32) + np.array([0, 1], np.float32)).ravel())
    me.polygons.foreach_set('material_index', sid)
    # the engine mesh has no valid vertex normals in this file: flat shading from the winding is enough for a tile
    me.update()
    mats, bad = [], []
    for k, mn in enumerate(info['surfaces']):
        mat, ok = make_material('%s.%d' % (item['name'], k), info['materials'][mn], images)
        if not ok:
            bad.append('%s: %s' % (mn, mat.get('unresolved')))
        me.materials.append(mat)
        mats.append(mat)
    ob = bpy.data.objects.new(item['name'], me)
    bpy.context.scene.collection.objects.link(ob)
    return (ob, z['bmin'] * S, z['bmax'] * S), None, bad


def frame(co, bmin, bmax, res):
    mid = (bmin + bmax) / 2
    r = max(float(np.linalg.norm(bmax - bmin)) / 2, 0.01)
    d = np.array([0.62, -0.74, 0.50])
    d = d / np.linalg.norm(d)
    cam = co.data
    fov = 2 * math.atan(cam.sensor_width / 2 / cam.lens)
    dist = r / math.sin(fov / 2) * 1.08
    co.location = mid + d * dist
    direction = mid - np.array(co.location)
    # look at mid: Blender camera looks down -Z, up is +Y
    from mathutils import Vector
    co.rotation_euler = Vector(direction).to_track_quat('-Z', 'Y').to_euler()
    cam.clip_start = max(dist - r * 1.5, 0.001)
    cam.clip_end = dist + r * 2


def main():
    job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
    jobpath = sys.argv[sys.argv.index('--') + 1]
    sc, co = setup(job['res'], job.get('engine', 'EEVEE'))
    results = {}
    t_all = time.time()
    for item in job['items']:
        t = time.time()
        images = []
        ob = None
        try:
            built, why, bad = build(item, images)
            if built is None:
                results[item['name']] = {'ok': False, 'reason': why, 'seconds': 0}
                continue
            ob, bmin, bmax = built
            frame(co, bmin, bmax, job['res'])
            sc.render.filepath = item['out']
            bpy.ops.render.render(write_still=True)
            results[item['name']] = {'ok': True, 'reason': '; '.join(bad[:3]) if bad else None,
                                     'unresolvedSurfaces': len(bad), 'seconds': round(time.time() - t, 3)}
        except Exception as e:
            results[item['name']] = {'ok': False, 'reason': 'blender: %s: %s' % (type(e).__name__, e), 'seconds': 0}
        finally:
            if ob is not None:
                me = ob.data
                mats = list(me.materials)
                bpy.data.objects.remove(ob)
                bpy.data.meshes.remove(me)
                for m in mats:
                    bpy.data.materials.remove(m)
            for nm in set(images):
                im = bpy.data.images.get(nm)
                if im is not None and im.users == 0:
                    bpy.data.images.remove(im)
    json.dump({'results': results, 'seconds': round(time.time() - t_all, 1)}, open(jobpath + '.result.json', 'w'))


main()
