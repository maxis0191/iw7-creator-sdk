"""Station Zero look preview inside Blender (no map build, no game).

Runs in Blender (background or interactive):

    blender -b --factory-startup --python iwz_preview.py -- load <src> [--views NAME,..|all] [--out DIR]
                [--plan PLAN.json] [--eye 60] [--fov 90] [--exposure 1.0] [--overlays] [--res 1280x720]

or, from a Blender Python console:  import iwz_preview; iwz_preview.load(r'<src>')

<src> is an emitted compiler source (world.bin, layout.json, bake.npz, smodels.txt, custom_materials.json).
Scene: collections world / props / overlays / views. Shading is unlit (emission): the engine draws albedo * lightmap
irradiance, so the preview does too. E = A + B * saturate(Dz) from bake.npz (lm_decode.py header; flat normal, so
dot(N, D) = D.z; the mean over valid texels equals bake.json mean.E). No Blender light exists.
Unresolved materials and models are magenta and listed in the report (<out>/report.json), never given a fake colour.
"""
import json
import math
import os
import re
import sys
import time

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iwz_assets as A  # noqa: E402

S = 0.0254           # inches -> metres
Y00_E = 0.886        # irradiance of the order-1 grid constant term: E = pi * L, c0 = L * 4 * pi * Y00  ->  E = 0.886 * c0
MAGENTA = (1.0, 0.0, 1.0, 1.0)


class Stages:
    def __init__(self):
        self.t = {}
        self._t0 = time.time()
        self._last = self._t0

    def mark(self, name):
        now = time.time()
        self.t[name] = round(now - self._last, 3)
        self._last = now

    def total(self):
        return round(time.time() - self._t0, 3)


# ------------------------------------------------------------------------------------------------ lightmap
def lightmap_terms(z):
    """A (non directional) and D = B * saturate(D.z) per texel (float32 H x W x 3); D.z from the rotated octahedral
    direction (lm_decode.oct_decode). E = A + D is the irradiance of a flat surface."""
    a = z['D'][..., 0] * 2 - 1
    b = z['D'][..., 1] * 2 - 1
    x = (a + b) * 0.5
    y = (a - b) * 0.5
    zz = 1 - np.abs(x) - np.abs(y)
    dz = zz / np.maximum(np.sqrt(x * x + y * y + zz * zz), 1e-8)
    return z['A'].astype(np.float32), (z['B'] * np.maximum(dz, 0)[..., None]).astype(np.float32)


def lightmap_irradiance(z):
    A_, D_ = lightmap_terms(z)
    return A_ + D_


def make_lightmap_image(E, name='iwz_lightmap'):
    H, W = E.shape[:2]
    img = bpy.data.images.new(name, W, H, float_buffer=True, alpha=False, is_data=True)
    img.colorspace_settings.name = 'Non-Color'
    px = np.ones((H, W, 4), np.float32)
    px[..., :3] = np.flipud(E)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.pack()
    return img


# ------------------------------------------------------------------------------------------------ materials
def classify(techset, path, base_techset=None):
    """-> (kind, lit): kind opaque | atest | blend | emissive, lit True when the lightmap multiplies it."""
    t = base_techset or techset or ''
    if 'multiply' in t:
        return 'multiply', False
    if 'unlit' in t or 'emissive' in path:
        return 'emissive', False
    if re.search(r'[0-9_]em0', t):
        return 'emissive', False
    if '_atest_' in t:
        return 'atest', True
    if '_blend_' in t or '_ndw_' in t:
        return 'blend', True
    return 'opaque', True


ALBEDO_PASS = False      # --albedo-pass: surfaces show albedo * tint only (no lightmap, no light grid, no emission); the base of the runtime light pass
EMISSIVE_GAIN = 20.0     # self-lit surfaces saturate in the engine (HDR + bloom); the exact value is not in the data, see README


def _load_image(path, data=False):
    """Load an image file; colour maps sRGB, data maps (occlusion) Non-Color, never premultiplied with the PNG alpha."""
    if data:
        img = bpy.data.images.load(path, check_existing=False)
        img.name = 'data_' + os.path.basename(path)
        img.colorspace_settings.name = 'Non-Color'
    else:
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = 'sRGB'
    img.alpha_mode = 'CHANNEL_PACKED'
    return img


def build_material(name, image_path, tint, kind, lit, lm_img, lm_uv_name, uv_name, emissive=0.0, object_light=False,
                   magenta=False, extra=None):
    """Unlit (emission) shading of one engine material.
    lit surfaces: albedo * tint * (A * occlusion + B * saturate(D.z))   (lm_img = (E, A, D) images; E = A + D when the
                  material has no occlusion map; occlusion = R channel of the semantic 15 '..._nog' image)
    props (object_light): albedo * tint * object colour (light grid) [+ emissive]
    emissive: strength * colour (not lit); extra['emissive_png'] * extra['emissive_para'] is added to a lit surface."""
    extra = extra or {}
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    if magenta:
        em.inputs['Color'].default_value = MAGENTA
        return mat
    col = None
    alpha = None

    def uvnode(uvname):
        n = nt.nodes.new('ShaderNodeUVMap')
        n.uv_map = uvname
        return n

    def tex(path, data=False, uvname=None, ext='REPEAT'):
        tx = nt.nodes.new('ShaderNodeTexImage')
        tx.image = _load_image(path, data)
        tx.interpolation = 'Linear'
        tx.extension = ext
        nt.links.new(uvnode(uvname or uv_name).outputs['UV'], tx.inputs['Vector'])
        return tx

    # the engine's lit shaders square the colour map (ENGINE-SHADERS.md section 2, line 9): read it as raw values, not sRGB, and square it
    square = bool((lit or object_light) and not emissive)
    if image_path:
        try:
            tx = tex(image_path, data=square)
        except RuntimeError:
            em.inputs['Color'].default_value = MAGENTA
            return mat
        col = tx.outputs['Color']
        alpha = tx.outputs['Alpha']
    tint_n = nt.nodes.new('ShaderNodeRGB')
    tint_n.outputs[0].default_value = (tint[0], tint[1], tint[2], 1.0)

    def mul(a, b, op='MULTIPLY'):
        m = nt.nodes.new('ShaderNodeMix')
        m.data_type = 'RGBA'
        m.blend_type = op
        m.inputs['Factor'].default_value = 1.0
        nt.links.new(a, m.inputs['A'])
        nt.links.new(b, m.inputs['B'])
        return m.outputs['Result']

    if square and col is not None:
        col = mul(col, col)
    base = tint_n.outputs[0] if col is None else mul(col, tint_n.outputs[0])
    if emissive > 0 and ALBEDO_PASS:
        em.inputs['Color'].default_value = (0, 0, 0, 1)
    elif emissive > 0:
        em.inputs['Strength'].default_value = emissive * EMISSIVE_GAIN
        nt.links.new(base, em.inputs['Color'])
    elif ALBEDO_PASS and (lit or object_light):
        nt.links.new(base, em.inputs['Color'])
    elif lit and lm_img is not None:
        E_img, A_img, D_img = lm_img
        occ_png = None      # the `nog` map's R channel is gloss, not occlusion (ENGINE-SHADERS.md section 2); the lightmap and ssao are the occlusion
        if occ_png:
            ot = tex(occ_png, data=True)
            sep = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(ot.outputs['Color'], sep.inputs['Color'])
            at = nt.nodes.new('ShaderNodeTexImage')
            at.image = A_img
            at.interpolation = 'Linear'
            at.extension = 'EXTEND'
            nt.links.new(uvnode(lm_uv_name).outputs['UV'], at.inputs['Vector'])
            dt = nt.nodes.new('ShaderNodeTexImage')
            dt.image = D_img
            dt.interpolation = 'Linear'
            dt.extension = 'EXTEND'
            nt.links.new(uvnode(lm_uv_name).outputs['UV'], dt.inputs['Vector'])
            occ_rgb = nt.nodes.new('ShaderNodeCombineColor')
            for ch in ('Red', 'Green', 'Blue'):
                nt.links.new(sep.outputs['Red'], occ_rgb.inputs[ch])
            amb = mul(at.outputs['Color'], occ_rgb.outputs['Color'])
            light = mul(amb, dt.outputs['Color'], 'ADD')
        else:
            lt = nt.nodes.new('ShaderNodeTexImage')
            lt.image = E_img
            lt.interpolation = 'Linear'
            lt.extension = 'EXTEND'
            nt.links.new(uvnode(lm_uv_name).outputs['UV'], lt.inputs['Vector'])
            light = lt.outputs['Color']
        base = mul(base, light)
        if extra.get('emissive_png') and extra.get('emissive_para'):
            et = tex(extra['emissive_png'])
            es = nt.nodes.new('ShaderNodeRGB')
            g = float(extra['emissive_para']) * EMISSIVE_GAIN
            es.outputs[0].default_value = (g, g, g, 1.0)
            base = mul(base, mul(et.outputs['Color'], es.outputs[0]), 'ADD')
        nt.links.new(base, em.inputs['Color'])
    elif object_light:
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        base = mul(base, oi.outputs['Color'])
        if extra.get('emissive_png') and extra.get('emissive_para'):
            et = tex(extra['emissive_png'])
            es = nt.nodes.new('ShaderNodeRGB')
            g = float(extra['emissive_para']) * EMISSIVE_GAIN
            es.outputs[0].default_value = (g, g, g, 1.0)
            base = mul(base, mul(et.outputs['Color'], es.outputs[0]), 'ADD')
        nt.links.new(base, em.inputs['Color'])
    else:
        nt.links.new(base, em.inputs['Color'])
    if kind == 'multiply':
        # unlit multiply decal (w_unlit_multiply): approximated as a black overlay with alpha = 1 - luminance of its colour
        bw = nt.nodes.new('ShaderNodeRGBToBW')
        inv = nt.nodes.new('ShaderNodeMath')
        inv.operation = 'SUBTRACT'
        inv.inputs[0].default_value = 1.0
        nt.links.new(base, bw.inputs['Color'])
        nt.links.new(bw.outputs['Val'], inv.inputs[1])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(inv.outputs[0], mix.inputs['Fac'])
        nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
        for l in list(em.inputs['Color'].links):
            nt.links.remove(l)
        em.inputs['Color'].default_value = (0, 0, 0, 1)
        nt.links.new(em.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
        mat.surface_render_method = 'BLENDED'
    elif kind in ('atest', 'blend') and alpha is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        if kind == 'atest':
            gt = nt.nodes.new('ShaderNodeMath')
            gt.operation = 'GREATER_THAN'
            gt.inputs[1].default_value = 0.5
            nt.links.new(alpha, gt.inputs[0])
            fac = gt.outputs[0]
        else:
            fac = alpha
        nt.links.new(fac, mix.inputs['Fac'])
        nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
        nt.links.new(em.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
        mat.surface_render_method = 'BLENDED'
    return mat


class MaterialResolver:
    """Resolves a world / model material name to an image + kind. Every failure is recorded with its reason."""

    def __init__(self, index, customs, lm_img):
        self.index = index
        self.customs = customs
        self.lm = lm_img
        self.cache = {}
        self.report = {'resolved': {}, 'unresolved': {}}

    def _entry(self, name):
        """-> dict(image_path, tint, kind, lit, emissive, techset) | None, reason"""
        c = self.customs.get(name)
        if c is not None:
            tint = c.get('tint') or [1, 1, 1, 1]
            emis = (c.get('emissive') or [0])[0]
            base, err = A.material_info(self.index, 'w/' + c['base']) if c.get('base') else (None, None)
            bt = base['techset'] if base else ''
            if c.get('tga'):
                if not os.path.isfile(c['tga']):
                    return None, 'custom image %s missing' % c['tga']
                kind, lit = classify(bt, name, bt)
                if kind != 'multiply' and (c['base'] == 'wall_stain_01_dec' or 'decal' in name or 'stain' in name
                                           or 'grime' in name or 'streak' in name):
                    kind, lit = 'blend', True
                return {'image': c['tga'], 'tint': tint, 'kind': kind, 'lit': lit, 'emissive': 0.0, 'techset': bt,
                        'src': 'custom tga', 'how': 'custom_materials.json tga', 'color_image': os.path.basename(c['tga']), 'extra': {}}, None
            if base is None:
                return None, err
            png, e = A.image_png(self.index, base['image']) if base['image'] else (None, None)
            if base['image'] and not png:
                return None, e
            kind, lit = classify(bt, name)
            if emis:
                kind, lit = 'emissive', False
            extra = {}
            if base.get('occlusion_image') and lit:
                op, e2 = A.image_png(self.index, base['occlusion_image'])
                if op:
                    extra['occlusion_png'] = op
            return {'image': png, 'tint': tint, 'kind': kind, 'lit': lit, 'emissive': float(emis), 'techset': bt,
                    'src': 'custom tint of ' + c['base'], 'how': base['how'], 'color_image': base['image'], 'extra': extra}, None
        mi, err = A.material_info(self.index, name)
        if mi is None:
            return None, err
        if not mi['image']:
            return None, 'material %s has no colour image (textures %s)' % (name, mi['textures'])
        png, e = A.image_png(self.index, mi['image'])
        if not png:
            return None, e
        kind, lit = classify(mi['techset'], name)
        extra = {}
        emissive, tint = 0.0, mi['tint']
        if mi['unlit'] and kind == 'emissive':
            emissive, tint = float(mi['tint'][0]), (1, 1, 1)          # colorTint of an unlit techset is its brightness
        if mi['emissive_image'] and mi['emissive_para']:
            ep, e2 = A.image_png(self.index, mi['emissive_image'])
            if ep:
                extra['emissive_png'], extra['emissive_para'] = ep, mi['emissive_para']
        if mi['occlusion_image'] and lit:
            op, e2 = A.image_png(self.index, mi['occlusion_image'])
            if op:
                extra['occlusion_png'] = op
        return {'image': png, 'tint': tint, 'kind': kind, 'lit': lit, 'emissive': emissive, 'techset': mi['techset'],
                'src': 'dump', 'how': mi['how'], 'color_image': mi['image'], 'extra': extra}, None

    def get(self, name, uv_name='uv', lm_uv='lightmap', object_light=False):
        key = (name, uv_name, object_light)
        if key in self.cache:
            return self.cache[key]
        ent, err = self._entry(name)
        if ent is None:
            self.report['unresolved'][name] = err
            m = build_material('iwz:' + name, None, (1, 1, 1), 'opaque', False, None, lm_uv, uv_name, magenta=True)
        else:
            self.report['resolved'][name] = {k: ent[k] for k in ('kind', 'techset', 'src', 'how', 'color_image')}
            self.report['resolved'][name]['extra'] = sorted(ent['extra'])
            m = build_material('iwz:' + name, ent['image'], ent['tint'], ent['kind'], ent['lit'] and not object_light,
                               self.lm, lm_uv, uv_name, ent['emissive'], object_light and ent['kind'] != 'emissive',
                               extra=dict(ent['extra'], **({'occlusion_png': None} if object_light else {})))
        self.cache[key] = m
        return m


# ------------------------------------------------------------------------------------------------ scene
def new_coll(root, name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c


def mesh_from_arrays(name, pos, tris, uvs=None, uv_names=('uv',), mat_index=None):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pos))
    me.vertices.foreach_set('co', pos.astype(np.float32).ravel())
    me.loops.add(len(tris) * 3)
    me.loops.foreach_set('vertex_index', tris.astype(np.int32).ravel())
    me.polygons.add(len(tris))
    me.polygons.foreach_set('loop_start', np.arange(0, len(tris) * 3, 3, dtype=np.int32))
    for un, uv in zip(uv_names, uvs or []):
        layer = me.uv_layers.new(name=un)
        layer.data.foreach_set('uv', (uv[tris.ravel()] * np.array([1, -1], np.float32) + np.array([0, 1], np.float32)).ravel())
    if mat_index is not None:
        me.polygons.foreach_set('material_index', mat_index.astype(np.int32))
    me.update()
    return me


def eye_view_matrix(x, y, z, yaw, pitch, eye):
    cam_loc = (x * S, y * S, (z + eye) * S)
    rot = (math.pi / 2 - math.radians(pitch), 0.0, math.radians(yaw) - math.pi / 2)
    return cam_loc, rot


def add_camera(coll, name, x, y, z, yaw, pitch, eye, hfov, res=(1280, 720)):
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'HORIZONTAL'
    cd.angle_x = math.radians(hfov)
    cd.clip_start = 0.03
    cd.clip_end = 400
    o = bpy.data.objects.new(name, cd)
    o.location, o.rotation_euler = eye_view_matrix(x, y, z, yaw, pitch, eye)
    o['iwz_view'] = [x, y, z, yaw, pitch]
    coll.objects.link(o)
    return o


def grid_light(grid):
    keep = grid[:, 7] > 0.5
    return grid[keep, :3], grid[keep, 3:6]


def load_plan_views(plan_path):
    d = json.load(open(plan_path))
    out = {}
    for st in d['steps']:
        if st.get('do') == 'tour':
            for v in st['views']:
                out[v['name']] = (v['at'][0], v['at'][1], v['at'][2], v.get('yaw', 0), v.get('pitch', 0))
    return out


def parse_smodels(path):
    rows = []
    if not os.path.isfile(path):
        return rows
    for ln in open(path, encoding='utf-8'):
        p = ln.split()
        if len(p) >= 8:
            rows.append({'model': p[0], 'origin': [float(v) for v in p[1:4]], 'angles': [float(v) for v in p[4:7]],
                         'scale': float(p[7]), 'src': 'smodels'})
    return rows


def clear_scene():
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.images):
        for d in list(datablocks):
            datablocks.remove(d)


def authored_glb(name):
    """Authored (not xmodel) models of the map: perks/machines writes <runtime>/iwz-stage2/level/p1/machines/authored/<name>.glb
    (units inches, floor centre origin, front +X). -> path or None"""
    p = os.path.join(A.runtime(), 'iwz-stage2', 'level', 'p1', 'machines', 'authored', name + '.glb')
    return p if os.path.isfile(p) else None


def import_glb_as_collection(path, name):
    """Import a glb, convert its materials to unlit colour * object light, return a (not scene linked) collection."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new('glb_' + name)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        o.parent = None if o.type != 'MESH' else o.parent
        if o.type == 'MESH':
            for slot in o.material_slots:
                m = slot.material
                if m is None or not m.use_nodes or m.get('iwz_conv'):
                    continue
                nt = m.node_tree
                pb = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if pb is None:
                    continue
                bc = pb.inputs['Base Color']
                src = bc.links[0].from_socket if bc.links else None
                dv = tuple(bc.default_value)
                out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
                em = nt.nodes.new('ShaderNodeEmission')
                oi = nt.nodes.new('ShaderNodeObjectInfo')
                mx = nt.nodes.new('ShaderNodeMix')
                mx.data_type = 'RGBA'
                mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1.0
                if src is not None:
                    nt.links.new(src, mx.inputs['A'])
                else:
                    mx.inputs['A'].default_value = dv
                nt.links.new(oi.outputs['Color'], mx.inputs['B'])
                nt.links.new(mx.outputs['Result'], em.inputs['Color'])
                nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
                m['iwz_conv'] = True
    return col


def load(src, plan=None, eye=60.0, hfov=90.0, overlays=False, game=None, log=print, prop_gain=None, power=True):
    """Build the scene. Returns the report dict (timings, material / model resolution, light grid use)."""
    st = Stages()
    if prop_gain is None:
        try:
            prop_gain = float(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'calibration.json'))).get('prop_gain', 1.0))
        except (OSError, ValueError):
            prop_gain = 1.0
    clear_scene()
    sc = bpy.context.scene
    root = sc.collection
    index = A.DumpIndex()
    st.mark('dump_index')
    world = A.read_world(os.path.join(src, 'world.bin'))
    lay = json.load(open(os.path.join(src, 'layout.json'), encoding='utf-8'))
    z = np.load(os.path.join(src, 'bake.npz'))
    cm = json.load(open(os.path.join(src, 'custom_materials.json')))
    customs = {v['path']: v for v in cm['custom'].values()}
    st.mark('read_source')

    A_lm, D_lm = lightmap_terms(z)
    E = A_lm + D_lm
    lm_img = (make_lightmap_image(E), make_lightmap_image(A_lm, 'iwz_lightmap_A'), make_lightmap_image(D_lm, 'iwz_lightmap_D'))
    valid = z['valid']
    lum = E[..., 0] * 0.2126 + E[..., 1] * 0.7152 + E[..., 2] * 0.0722
    report = {'lightmap': {'atlas': list(E.shape[:2]), 'E_mean_valid': [float(v) for v in E[valid].mean(0)],
                           'E_lum_mean': float(lum[valid].mean())}}
    st.mark('lightmap')

    resolver = MaterialResolver(index, customs, lm_img)
    wc = new_coll(root, 'world')
    verts, idx, surfs = world['verts'], world['indices'], world['surfaces']
    tris, tri_mat = [], []
    for s in surfs:
        t = idx[s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + int(s['first'])
        tris.append(t)
        tri_mat.append(np.full(len(t), s['mat'], np.int64))
    tris = np.concatenate(tris)
    tri_mat = np.concatenate(tri_mat)
    pos = verts['pos'].astype(np.float64) * S
    me = mesh_from_arrays('world', pos, tris, [verts['uv'], verts['lm']], ('uv', 'lightmap'), tri_mat)
    for m in world['materials']:
        me.materials.append(resolver.get(m, 'uv', 'lightmap'))
    wo = bpy.data.objects.new('world', me)
    wc.objects.link(wo)
    st.mark('world_mesh_and_materials')
    report['world'] = {'verts': len(pos), 'tris': len(tris), 'materials': len(world['materials'])}

    # ---- props
    pc = new_coll(root, 'props')
    # every placed model: layout decor (static models of smodels.txt are a subset, with the same origin) plus the
    # layout models that are not decor; door dressing is left out (the capture plans open the doors first)
    def key(m, o):
        return (m, round(float(o[0]), 1), round(float(o[1]), 1), round(float(o[2]), 1))
    seen = set()
    rows = []
    for d in lay.get('decor', []):
        if str(d.get('targetname') or '').startswith('iwz_doordress'):
            continue
        seen.add(key(d['model'], d['origin']))
        rows.append({'model': d['model'], 'origin': d['origin'], 'angles': [d.get('pitch', 0), d.get('yaw', 0), d.get('roll', 0)],
                     'scale': float(d.get('scale', 1.0)), 'src': 'layout decor'})
    for d in lay.get('models', []):
        if key(d['model'], d['origin']) in seen or str(d.get('targetname') or '').startswith('iwz_doordress'):
            continue
        rows.append({'model': d['model'], 'origin': d['origin'], 'angles': [0, d.get('yaw', 0), 0], 'scale': 1.0, 'src': 'layout models'})
    # power fixtures: placed by the level script when the power is switched on (the 'on' model, emissive); power='off' shows the 'off' model
    for d in lay.get('power_fixtures', []):
        rows.append({'model': d['on'] if power else d['off'], 'origin': d['origin'], 'angles': [0, d.get('yaw', 0), 0],
                     'scale': 1.0, 'src': 'layout power_fixtures (%s)' % ('on' if power else 'off')})
    for r in parse_smodels(os.path.join(src, 'smodels.txt')):      # the compiled static rows carry the scale
        if r['scale'] != 1.0:
            for q in rows:
                if key(q['model'], q['origin']) == key(r['model'], r['origin']):
                    q['scale'] = r['scale']
    gP, gC = grid_light(z['grid'])
    meshes, model_report = {}, {'resolved': {}, 'unresolved': {}}
    glb_cols, glb_inst = {}, []

    def light_at(origin):
        if len(gP):
            d2 = ((gP - np.array(origin)) ** 2).sum(1)
            k = int(d2.argmin())
            return gC[k] * Y00_E if d2[k] < (192.0 ** 2) else gC.mean(0) * Y00_E
        return np.array(E[valid].mean(0))
    n_inst = 0
    for r in rows:
        name = r['model']
        if name not in meshes and name not in glb_cols:
            gp = authored_glb(name) if index.get('xmodel', name) is None else None
            if gp:
                try:
                    glb_cols[name] = import_glb_as_collection(gp, name)
                    model_report['resolved'][name] = {'source': 'authored glb ' + gp}
                except Exception as e:
                    model_report['unresolved'][name] = 'glb import failed: %s' % e
        if name in glb_cols:
            o = bpy.data.objects.new(name, None)
            o.instance_type = 'COLLECTION'
            o.instance_collection = glb_cols[name]
            pitch, yaw, roll = r['angles']
            o.location = [v * S for v in r['origin']]
            o.rotation_euler = (math.radians(roll), math.radians(pitch), math.radians(yaw))
            o.scale = (S * r['scale'],) * 3
            e = light_at(r['origin'])
            o.color = (float(e[0]) * prop_gain, float(e[1]) * prop_gain, float(e[2]) * prop_gain, 1.0)
            pc.objects.link(o)
            glb_inst.append(o)
            n_inst += 1
            continue
        if name not in meshes:
            mdl, err = A.read_model(index, name)
            if mdl is None:
                model_report['unresolved'][name] = err
                bx = bpy.data.meshes.new('box_' + name)
                s = 16 * S
                cube = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0], [-1, -1, 2], [1, -1, 2], [1, 1, 2], [-1, 1, 2]], np.float32) * s
                quad = np.array([[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 5, 1], [0, 4, 5], [1, 6, 2], [1, 5, 6],
                                 [2, 7, 3], [2, 6, 7], [3, 4, 0], [3, 7, 4]])
                bx = mesh_from_arrays('box_' + name, cube, quad)
                bx.materials.append(resolver.get('__missing_model__:' + name, object_light=True))
                meshes[name] = bx
            else:
                sp, st_, ui, mi_ = [], [], [], []
                off = 0
                mats = []
                for s in mdl['surfs']:
                    sp.append(s['pos'] * S)
                    st_.append(s['tris'] + off)
                    ui.append(s['uv'])
                    key = s['material'] or '__none__'
                    if key not in mats:
                        mats.append(key)
                    mi_.append(np.full(len(s['tris']), mats.index(key), np.int64))
                    off += len(s['pos'])
                mesh = mesh_from_arrays('m_' + name, np.concatenate(sp), np.concatenate(st_), [np.concatenate(ui)], ('uv',),
                                        np.concatenate(mi_))
                for mn in mats:
                    mesh.materials.append(resolver.get(mn, 'uv', object_light=True))
                meshes[name] = mesh
                model_report['resolved'][name] = {'surfaces': len(mdl['surfs']), 'tris': int(sum(len(s['tris']) for s in mdl['surfs']))}
        o = bpy.data.objects.new(name, meshes[name])
        pitch, yaw, roll = r['angles']
        o.location = [v * S for v in r['origin']]
        o.rotation_euler = (math.radians(roll), math.radians(pitch), math.radians(yaw))
        o.scale = (r['scale'],) * 3
        e = light_at(r['origin'])
        o.color = (float(e[0]) * prop_gain, float(e[1]) * prop_gain, float(e[2]) * prop_gain, 1.0)
        pc.objects.link(o)
        n_inst += 1
    st.mark('props')
    model_report['instances'] = n_inst
    model_report['light'] = ('light grid (bake.npz grid: order-1 SH constant term of the %d kept cells, nearest cell within 192 '
                             'units, else the mean of the kept cells; E = 0.886 * c0, constant per instance, no direction)' % len(gP))

    # ---- views
    vc = new_coll(root, 'views')
    views = {}
    for zone, vs in lay.get('views', {}).items():
        for j, v in enumerate(vs):
            views['%s_%d' % (zone, j)] = tuple(v)
    for nm, v in (load_plan_views(plan).items() if plan else []):
        views['plan_' + nm] = v
    cams = {}
    for nm, v in views.items():
        cams[nm] = add_camera(vc, 'view_' + nm, v[0], v[1], v[2], v[3], v[4], eye, hfov)
    st.mark('views')

    # ---- overlays
    oc = new_coll(root, 'overlays')
    build_overlays(oc, lay, src, z, collision=overlays)
    oc.hide_render = not overlays
    st.mark('overlays')

    setup_render(sc)
    un = {k: v for k, v in resolver.report['unresolved'].items() if not k.startswith('__missing_model__')}
    ws = set(world['materials'])
    report['materials'] = {'resolved': len(resolver.report['resolved']), 'unresolved': len(un),
                           'world_resolved': len([m for m in ws if m in resolver.report['resolved']]),
                           'world_unresolved': len([m for m in ws if m in un]),
                           'resolved_list': resolver.report['resolved'], 'unresolved_list': un}
    report['models'] = {'resolved': len(model_report['resolved']), 'unresolved': len(model_report['unresolved']),
                        'unresolved_list': model_report['unresolved'], 'resolved_list': model_report['resolved'],
                        'instances': n_inst, 'light': model_report['light']}
    report['views'] = sorted(views)
    report['timing_s'] = dict(st.t, total=st.total())
    return report, cams


def box_mesh(name, mn, mx):
    x0, y0, z0 = [v * S for v in mn]
    x1, y1, z1 = [v * S for v in mx]
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], np.float32)
    me = bpy.data.meshes.new(name)
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    me.from_pydata(v.tolist(), edges, [])
    return me


def build_overlays(oc, lay, src, z, collision=False):
    """Hidden from render by default. Spawners, doors, blockers, zone volumes, nav cells, collision (wireframe)."""
    ov = bpy.data.materials.new('iwz:overlay')
    ov.use_nodes = True
    ont = ov.node_tree
    ont.nodes.clear()
    oo = ont.nodes.new('ShaderNodeOutputMaterial')
    oe = ont.nodes.new('ShaderNodeEmission')
    oi = ont.nodes.new('ShaderNodeObjectInfo')
    ont.links.new(oi.outputs['Color'], oe.inputs['Color'])
    ont.links.new(oe.outputs['Emission'], oo.inputs['Surface'])

    def put(name, data, loc=(0, 0, 0), color=(1, 0, 0, 1), wire=True):
        o = bpy.data.objects.new(name, data)
        o.location = loc
        o.color = color
        data.materials.append(ov)
        oc.objects.link(o)
        o.display_type = 'WIRE' if wire else 'TEXTURED'
        if wire:                                    # a wireframe modifier so the edges also render
            md = o.modifiers.new('wire', 'WIREFRAME')
            md.thickness = 0.04
            md.use_replace = True
        return o
    for i, sp in enumerate(lay.get('spawners', [])):
        e = bpy.data.objects.new('spawn_%d' % i, None)
        e.empty_display_type = 'SINGLE_ARROW'
        e.empty_display_size = 0.5
        e.location = [v * S for v in sp['origin']]
        e.rotation_euler = (math.pi / 2, 0, math.radians(sp.get('yaw', 0)) - math.pi / 2)
        oc.objects.link(e)
    for d in lay.get('doors', []):
        a = d['axis']
        lo, hi, z0, z1, pl = d['lo'], d['hi'], d['z0'], d['z1'], d['plane']
        mn = [pl - 2, lo, z0] if a == 0 else [lo, pl - 2, z0]
        mx = [pl + 2, hi, z1] if a == 0 else [hi, pl + 2, z1]
        put('door_' + d['name'], box_mesh('door', mn, mx), color=(1, 0.5, 0, 1))
    for b in lay.get('blockers', []):
        e = bpy.data.objects.new('blocker_' + b['target'], None)
        e.empty_display_type = 'CUBE'
        e.empty_display_size = 0.3
        e.location = [v * S for v in b['origin']]
        oc.objects.link(e)
    for v in lay.get('volumes', []):
        b = v['box']
        put('vol_' + v['name'], box_mesh('vol', b[:3], b[3:]), color=(0, 1, 0, 1))
    pj = os.path.join(src, 'plan.json')
    if os.path.isfile(pj):
        plan = json.load(open(pj))
        cells = plan.get('cells', [])
        cs = 32.0
        if cells:
            q = 14.0
            P, F = [], []
            for c in cells:
                x, y, zc = c[0] * cs + cs / 2, c[1] * cs + cs / 2, c[2] + 2
                b = len(P)
                P += [(x - q, y - q, zc), (x + q, y - q, zc), (x + q, y + q, zc), (x - q, y + q, zc)]
                F.append((b, b + 1, b + 2, b + 3))
            me = bpy.data.meshes.new('navcells')
            me.from_pydata((np.array(P, np.float32) * S).tolist(), [], F)
            put('navcells', me, color=(0, 0.6, 1, 1), wire=False)
    hk = os.path.join(src, 'colmap.hkx')
    if collision and os.path.isfile(hk):
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
            import hkcm
            from hkpack import Packfile
            pf = Packfile(open(hk, 'rb').read())
            for a_, n_, sz_ in pf.objects:
                if n_ == 'hknpCompressedMeshShapeData':
                    tr = hkcm.decode_cm_data(pf, a_)['tris']
                    pts = np.array(tr, np.float32).reshape(-1, 3) * S
                    me = bpy.data.meshes.new('collision')
                    me.from_pydata(pts.tolist(), [], [tuple(range(i, i + 3)) for i in range(0, len(pts), 3)])
                    put('collision', me, color=(1, 1, 0, 1))
                    break
        except Exception as e:  # overlay only: report, do not fail the scene
            print('IWZ_PREVIEW_WARN collision overlay: %s' % e)


def setup_render(sc, res=(1280, 720)):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    try:
        sc.eevee.taa_render_samples = 1
    except Exception:
        pass


def render_linear(cam, path_npy, res=(1280, 720), rgba=False):
    """Render one camera to a float EXR and save the linear RGB (H x W x 3, top row first) as .npy. -> seconds."""
    t = time.time()
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Raw'
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.image_settings.color_mode = 'RGBA' if rgba else 'RGB'
    exr = path_npy[:-4] + '.exr'
    sc.render.filepath = exr
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(exr)
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    os.remove(exr)
    np.save(path_npy, buf.reshape(h, w, 4)[::-1, :, :(4 if rgba else 3)].copy())
    return round(time.time() - t, 3)


def geometry_override(kind):
    """A material that shows the world space position or normal as colour (view layer material override, Raw view): the geometry passes of the runtime light pass."""
    mat = bpy.data.materials.new('iwz_geo_' + kind)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    # emission colour cannot be negative: position + 100 m (the map is within +-100 m, float precision 1e-5 m), normal * 0.5 + 0.5
    vm = nt.nodes.new('ShaderNodeVectorMath')
    if kind == 'pos':
        vm.operation = 'ADD'
        vm.inputs[1].default_value = (100.0, 100.0, 100.0)
        nt.links.new(geo.outputs['Position'], vm.inputs[0])
    else:
        vm.operation = 'MULTIPLY_ADD'
        vm.inputs[1].default_value = (0.5, 0.5, 0.5)
        vm.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs['Normal'], vm.inputs[0])
    nt.links.new(vm.outputs['Vector'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat


def set_camera_params(cams, eye, hfov):
    for o in cams.values():
        x, y, z, yaw, pitch = o['iwz_view']
        o.location, o.rotation_euler = eye_view_matrix(x, y, z, yaw, pitch, eye)
        o.data.angle_x = math.radians(hfov)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['load'])
    ap.add_argument('src')
    ap.add_argument('--views', default='', help='comma list of view names, "all", or a prefix ending in * (plan_lit_*)')
    ap.add_argument('--out', default='')
    ap.add_argument('--plan', default='')
    ap.add_argument('--eye', type=float, default=60.0)
    ap.add_argument('--fov', type=float, default=90.0)
    ap.add_argument('--eye-list', default='', help='sweep: render every view for each eye height (inches)')
    ap.add_argument('--fov-list', default='', help='sweep: horizontal fov degrees')
    ap.add_argument('--overlays', action='store_true')
    ap.add_argument('--prop-gain', type=float, default=None, help='scale of the light grid value of props (default: calibration.json)')
    ap.add_argument('--power', choices=['on', 'off'], default='on', help='power fixtures show their on (emissive) or off model')
    ap.add_argument('--prop-pass', action='store_true', help='render only the props (RGBA, the world is a holdout): the pixels the prop gain is fitted on')
    ap.add_argument('--res', default='1280x720')
    ap.add_argument('--albedo-pass', action='store_true', help='albedo * tint only: no lightmap, no light grid, no emission (runtime light pass)')
    ap.add_argument('--aux', action='store_true', help='also render <view>__pos.npy and <view>__nrm.npy (world position and normal, material override)')
    a = ap.parse_args(argv)
    res = tuple(int(v) for v in a.res.split('x'))
    global ALBEDO_PASS
    ALBEDO_PASS = a.albedo_pass
    report, cams = load(a.src, a.plan or None, a.eye, a.fov, a.overlays, prop_gain=a.prop_gain, power=(a.power == 'on'))
    if a.prop_pass:
        bpy.context.scene.render.film_transparent = True
        bpy.data.objects['world'].is_holdout = True
    timings = dict(report['timing_s'])
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        if a.views in ('', 'all'):
            want = list(cams)
        elif a.views.endswith('*'):
            want = [v for v in cams if v.startswith(a.views[:-1])]
        else:
            want = [v for v in a.views.split(',') if v in cams]
        eyes = [float(v) for v in a.eye_list.split(',')] if a.eye_list else [a.eye]
        fovs = [float(v) for v in a.fov_list.split(',')] if a.fov_list else [a.fov]
        t = time.time()
        rt = {}
        for eye in eyes:
            for fov in fovs:
                set_camera_params(cams, eye, fov)
                sub = a.out if (len(eyes) == 1 and len(fovs) == 1) else os.path.join(a.out, 'e%g_f%g' % (eye, fov))
                os.makedirs(sub, exist_ok=True)
                for nm in want:
                    rt['%g/%g/%s' % (eye, fov, nm)] = render_linear(cams[nm], os.path.join(sub, nm + '.npy'), res, rgba=a.prop_pass)
        if a.aux:
            vl = bpy.context.view_layer
            for kind in ('pos', 'nrm'):
                vl.material_override = geometry_override(kind)
                for nm in want:
                    render_linear(cams[nm], os.path.join(a.out, nm + '__' + kind + '.npy'), res)
            vl.material_override = None
        timings['render_each_s'] = rt
        timings['render_total_s'] = round(time.time() - t, 3)
        timings['renders'] = len(rt)
        report['timing_s'] = timings
        json.dump(report, open(os.path.join(a.out, 'report.json'), 'w'), indent=1)
    print('IWZ_PREVIEW_TIMING ' + json.dumps({k: v for k, v in report['timing_s'].items() if k != 'render_each_s'}))
    print('IWZ_PREVIEW_COUNTS materials resolved %d unresolved %d (world %d/%d) models resolved %d unresolved %d' % (
        report['materials']['resolved'], report['materials']['unresolved'], report['materials']['world_resolved'],
        report['materials']['world_unresolved'], report['models']['resolved'], report['models']['unresolved']))


if __name__ == '__main__' and '--' in sys.argv:
    main(sys.argv[sys.argv.index('--') + 1:])
