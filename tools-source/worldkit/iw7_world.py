#!/usr/bin/env python3
"""iw7_world: read the dump of a game map as a queryable scene, and lift rooms out as prefabs.

    python -B iw7_world.py build --dump <map dump folder> --db out.sqlite [--catalog models.json]
    python -B iw7_world.py stats --db out.sqlite
    python -B iw7_world.py box|near|find-model|where-model|rooms|check --db out.sqlite ...
    python -B iw7_world.py extract --db out.sqlite --box X1 Y1 Z1 X2 Y2 Z2 --name NAME --out DIR
    python -B iw7_world.py place --prefab DIR --at X Y Z [--yaw DEG] --out DIR2

Standard library only (numpy is used when importable, for speed; IW7_WORLD_NO_NUMPY=1 turns it off).
The file formats are documented in iw7_dump.py and docs/WORLDKIT.md.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import sqlite3
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iw7_dump as dump  # noqa: E402
from iw7_dump import WorldError, np  # noqa: E402

READER_VERSION = '1.0.0'
PREFAB_SCHEMA = 'iw7.prefab/1'
EXTRA_FILE = 'surfaces_extra.bin'

# counts the project's map compiler printed for the same dump (independent source), per map
GROUND_TRUTH = {'cp_zmb': {'surfaces': 10760, 'smodels': 17010, 'primaryLights': 1039, 'probes': 160, 'models': 94}}

LIGHT_TYPES = {0: 'none', 1: 'dir', 2: 'spot', 3: 'omni', 4: 'dir_shadowmap', 5: 'spot_shadowmap',
               6: 'omni_shadowmap', 7: 'spot_shadowmap_cucoloris'}
# entity field ids used by the project's entity text (tools-source/iwzmap/sz_interactions.py); other ids stay numeric
ENT_KEYS = {'157': 'classname', '822': 'targetname', '543': 'origin', '65': 'angles', '638': 'script_noteworthy',
            '820': 'target', '60666': 'area', '61049': 'parameters', '497': 'model', '502': 'groupname', '599': 'radius'}
ENT_KEY_BY_NAME = {v: k for k, v in ENT_KEYS.items()}


# ---------------------------------------------------------------- angles (the map compiler's convention)

def angles_to_axis(pitch, yaw, roll):
    """Rows forward, left, up from pitch/yaw/roll degrees: AngleVectors with left = -right, exactly as the map
    compiler's smodels.txt reader computes a static model's axis (iwzmap.cpp angles_to_axis)."""
    rad = math.pi / 180.0
    sp, cp = math.sin(pitch * rad), math.cos(pitch * rad)
    sy, cy = math.sin(yaw * rad), math.cos(yaw * rad)
    sr, cr = math.sin(roll * rad), math.cos(roll * rad)
    f = (cp * cy, cp * sy, -sp)
    r = (-sr * sp * cy + cr * sy, -sr * sp * sy - cr * cy, -sr * cp)
    u = (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp)
    return [f, (-r[0], -r[1], -r[2]), u]


def axis_to_angles(axis):
    """Inverse of angles_to_axis: pitch in [-90, 90], yaw and roll in (-180, 180]; roll is 0 at pitch = +-90."""
    f, left, up = axis
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, -f[2]))))
    if math.hypot(f[0], f[1]) > 1e-6:
        yaw = math.degrees(math.atan2(f[1], f[0]))
        roll = math.degrees(math.atan2(left[2], up[2]))
    else:
        roll = 0.0
        yaw = math.degrees(math.atan2(-left[0], left[1]))
    return pitch, yaw, roll


def max_matrix_diff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3))


def _cos_sin(deg):
    """cos/sin of a yaw in degrees, exact for multiples of 90."""
    q = deg / 90.0
    if q == round(q):
        k = int(round(q)) % 4
        return [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)][k]
    r = math.radians(deg)
    return math.cos(r), math.sin(r)


def rot_z(v, cs):
    c, s = cs
    return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def fmt(v):
    s = ('%.5f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ---------------------------------------------------------------- reading the dump folder

def find_world_files(dump_dir, map_name=None):
    maps = os.path.join(dump_dir, 'maps')
    if not os.path.isdir(maps):
        raise WorldError('no maps folder under %s' % dump_dir)
    found = {}
    for path in glob.glob(os.path.join(maps, '**', '*'), recursive=True):
        if not os.path.isfile(path):
            continue
        n = os.path.basename(path)
        for kind, suffix in (('gfxmap', '.gfxmap'), ('commap_json', '.commap.json'), ('commap', '.commap'), ('ents', '.ents')):
            if n.endswith(suffix):
                found.setdefault(kind, []).append(path)
    gfx = found.get('gfxmap', [])
    if map_name:
        gfx = [p for p in gfx if os.path.basename(p).startswith(map_name)]
    if len(gfx) != 1:
        raise WorldError('expected exactly one .gfxmap under %s, found %d' % (maps, len(gfx)))
    stem = gfx[0][:-len('.gfxmap')]
    files = {'gfxmap': gfx[0]}
    for kind, suffix in (('commap_json', '.commap.json'), ('commap', '.commap'), ('ents', '.ents')):
        if os.path.isfile(stem + suffix):
            files[kind] = stem + suffix
    return files


def parse_ents_text(data):
    """`.ents` text: blocks of `key "value"` lines between { and }. Returns a list of [(key, value)]."""
    ents, cur, off = [], None, 0
    for raw in data.split(b'\n'):
        line_off = off
        off += len(raw) + 1
        ln = raw.decode('latin-1').strip().strip('\x00').strip()
        if not ln:
            continue
        if ln == '{':
            if cur is not None:
                raise WorldError('ents: offset %d: block opened inside a block' % line_off)
            cur = []
        elif ln == '}':
            if cur is None:
                raise WorldError('ents: offset %d: block closed but none is open' % line_off)
            ents.append(cur)
            cur = None
        else:
            if cur is None:
                raise WorldError('ents: offset %d: line outside a block' % line_off)
            key, _, val = ln.partition(' ')
            val = val.strip()
            if not key or len(val) < 2 or val[0] != '"' or val[-1] != '"':
                raise WorldError('ents: offset %d: not a key "value" line' % line_off)
            cur.append((key, val[1:-1]))
    if cur is not None:
        raise WorldError('ents: offset %d: block not closed at end of file' % len(data))
    return ents


def ent_get(kvs, name):
    keys = (name, ENT_KEY_BY_NAME.get(name, name))
    for k, v in kvs:
        if k in keys:
            return v
    return None


def parse_vec3(text):
    try:
        p = [float(x) for x in text.split()]
    except ValueError:
        return None
    return tuple(p) if len(p) == 3 else None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def light_from_json(item):
    L = {k: item[k] for k in dump.LIGHT_FIELDS if k in item}
    for k, n in dump.LIGHT_ARRAYS.items():
        v = L.get(k)
        if not isinstance(v, list) or len(v) != n:
            raise WorldError('commap.json light %s: field %s is not %d numbers' % (item.get('primaryLightIndex'), k, n))
    return L


# ---------------------------------------------------------------- the database

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE smodels(i INTEGER PRIMARY KEY, model TEXT, x REAL, y REAL, z REAL,
  a00 REAL, a01 REAL, a02 REAL, a10 REAL, a11 REAL, a12 REAL, a20 REAL, a21 REAL, a22 REAL,
  pitch REAL, yaw REAL, roll REAL, scale REAL, cullDist INTEGER, flags INTEGER, lod_slot INTEGER, sorted_pos INTEGER,
  lightingHandle INTEGER, unk0 INTEGER, unk1 INTEGER, unk2 INTEGER, unk3 INTEGER, unk5 INTEGER,
  unk6_0 INTEGER, unk6_1 INTEGER, unk6_2 INTEGER, unk6_3 INTEGER, unk9 INTEGER, unk10 INTEGER, unk11 INTEGER,
  unk13 INTEGER, unk14 INTEGER, unk15 INTEGER, primaryLightEnvIndex INTEGER, reflectionProbeIndex INTEGER,
  firstMtlSkinIndex INTEGER, sunShadowFlags INTEGER, transientZone INTEGER, unk21 INTEGER,
  lmOffset_x REAL, lmOffset_y REAL, lmScale_x REAL, lmScale_y REAL, lmIndex INTEGER, numLightingValues INTEGER,
  bmid_x REAL, bmid_y REAL, bmid_z REAL, bhalf_x REAL, bhalf_y REAL, bhalf_z REAL,
  lightingOrigin_x REAL, lightingOrigin_y REAL, lightingOrigin_z REAL);
CREATE TABLE surfaces(i INTEGER PRIMARY KEY, material TEXT, vertex_count INTEGER, used_vertices INTEGER,
  tri_count INTEGER, first_vertex INTEGER, base_index INTEGER, transientZone INTEGER, lightmapIndex INTEGER,
  flags INTEGER, sortKey INTEGER, unk1 INTEGER, unk2 INTEGER, unk3 INTEGER, unk4 INTEGER, vertexLayerData INTEGER,
  maxEdgeLength REAL, minx REAL, miny REAL, minz REAL, maxx REAL, maxy REAL, maxz REAL,
  sb_minx REAL, sb_miny REAL, sb_minz REAL, sb_maxx REAL, sb_maxy REAL, sb_maxz REAL);
CREATE TABLE tris(surface INTEGER, cx REAL, cy REAL, cz REAL);
CREATE TABLE lights(i INTEGER PRIMARY KEY, type INTEGER, type_name TEXT, placed INTEGER, canUseShadowMap INTEGER,
  needsDynamicShadows INTEGER, isVolumetric INTEGER, exponent INTEGER, transientZoneList INTEGER, entityId INTEGER,
  uvIntensity REAL, irIntensity REAL, color_r REAL, color_g REAL, color_b REAL, dir_x REAL, dir_y REAL, dir_z REAL,
  up_x REAL, up_y REAL, up_z REAL, x REAL, y REAL, z REAL, radius REAL, fadeOffsetRt_0 REAL, fadeOffsetRt_1 REAL,
  bulbRadius REAL, bulbLength_x REAL, bulbLength_y REAL, bulbLength_z REAL, cosHalfFovOuter REAL, cosHalfFovInner REAL,
  outer_deg REAL, inner_deg REAL, shadowSoftness REAL, shadowBias REAL, shadowArea REAL, distanceFalloff REAL,
  rotationLimit REAL, translationLimit REAL, defName TEXT);
CREATE TABLE probes(i INTEGER PRIMARY KEY, livePath TEXT, x REAL, y REAL, z REAL, pitch REAL, yaw REAL, roll REAL,
  probeInstanceCount INTEGER);
CREATE TABLE probe_instances(i INTEGER PRIMARY KEY, livePath TEXT, livePath2 TEXT);
CREATE TABLE assets(kind TEXT, idx INTEGER, name TEXT);
CREATE TABLE brush_models(i INTEGER PRIMARY KEY, mid_x REAL, mid_y REAL, mid_z REAL, half_x REAL, half_y REAL,
  half_z REAL, radius REAL, startSurfIndex INTEGER, surfaceCount INTEGER);
CREATE TABLE ents(i INTEGER PRIMARY KEY, classname TEXT, targetname TEXT, origin_x REAL, origin_y REAL, origin_z REAL,
  model TEXT, angles TEXT);
CREATE TABLE ent_kv(i INTEGER, key TEXT, key_name TEXT, value TEXT);
CREATE TABLE models(name TEXT PRIMARY KEY, instances INTEGER, in_catalog INTEGER, category TEXT, num_lods INTEGER,
  lod0_tris INTEGER, radius REAL, bmin_x REAL, bmin_y REAL, bmin_z REAL, bmax_x REAL, bmax_y REAL, bmax_z REAL);
CREATE TABLE mesh_zones(zone INTEGER PRIMARY KEY, name TEXT, vertex_count INTEGER, offset INTEGER);
CREATE INDEX smodels_model ON smodels(model);
CREATE INDEX smodels_xy ON smodels(x, y);
CREATE INDEX tris_xy ON tris(cx, cy);
CREATE INDEX tris_surface ON tris(surface);
CREATE INDEX lights_xy ON lights(x, y);
CREATE INDEX ents_xy ON ents(origin_x, origin_y);
CREATE INDEX ent_kv_i ON ent_kv(i);
CREATE INDEX surfaces_material ON surfaces(material);
"""


def _insert(con, table, rows):
    if rows:
        con.executemany('INSERT INTO %s VALUES (%s)' % (table, ','.join('?' * len(rows[0]))), rows)


def mesh_path(db_path):
    return db_path + '.mesh'


def build(dump_dir, db_path, catalog=None, map_name=None, log=print):
    t0 = time.time()
    dump_dir = os.path.abspath(dump_dir)
    files = find_world_files(dump_dir, map_name)
    stem = os.path.basename(files['gfxmap'])
    if not map_name:
        map_name = stem.split('.')[0]
    parsed = {}
    meta_files = []

    def note(kind, path, end=None):
        size = os.path.getsize(path)
        meta_files.append({'kind': kind, 'name': os.path.relpath(path, dump_dir).replace(os.sep, '/'), 'bytes': size,
                           'sha256': sha256_file(path), 'parsed_to_end': end == size if end is not None else None,
                           'parsed_bytes': end})

    with open(files['gfxmap'], 'rb') as f:
        gbuf = f.read()
    d = dump.parse_gfxmap(gbuf, os.path.basename(files['gfxmap']))
    note('gfxmap', files['gfxmap'], d.end)
    log('gfxmap parsed to byte %d of %d: surfaces %d smodels %d primaryLights %d probes %d models %d' % (
        d.end, len(gbuf), d.header['surfaceCount'], d.header['dpvs.smodelCount'], d.header['primaryLightCount'],
        d.header['draw.reflectionProbeCount'], d.header['modelCount']))

    # transient zones: the world vertices live there
    SF, SD, SI = dump.layout('GfxSurface'), dump.layout('GfxStaticModelDrawInst'), dump.layout('GfxStaticModelInst')
    sf_fields = ['tris.vertexLayerData', 'tris.firstVertex', 'tris.maxEdgeLength', 'tris.vertexCount', 'tris.triCount',
                 'tris.baseIndex', 'lightmapIndex', 'flags', 'sortKey', 'unk1', 'unk2', 'unk3', 'unk4', 'transientZone']
    sf_st, sf_names = SF.compiled(sf_fields)
    surf_rows = [dict(zip(sf_names, sf_st.unpack_from(gbuf, d.surfaces.off + SF.size * i))) for i in range(d.surfaces.count)]
    used_zones = sorted({r['transientZone'] for r in surf_rows})
    zones = {}
    for zi in used_zones:
        zname = d.transient_zones[zi] if zi < len(d.transient_zones) else None
        if not zname:
            raise WorldError('surfaces use transient zone %d but the gfxmap names none' % zi)
        zpath = os.path.join(dump_dir, 'transient_zones', zname + '.gfxmap_tr')
        if not os.path.isfile(zpath):
            raise WorldError('missing transient zone file %s' % zpath)
        with open(zpath, 'rb') as f:
            zbuf = f.read()
        z = dump.parse_transient_zone(zbuf, os.path.basename(zpath))
        z.buf = zbuf
        z.zname = zname
        note('gfxmap_tr', zpath, z.end)
        zones[zi] = z
        log('transient zone %s parsed to byte %d of %d: %d vertices' % (zname, z.end, len(zbuf), z.vertex_count))
    indices_raw = bytes(gbuf[d.indices.off:d.indices.off + 2 * d.indices.count])

    # surfaces: bounds from the vertices the triangles use, triangle centroids
    index_oob = 0
    surfaces, tri_rows = [], []
    vpos = {}
    for zi, z in zones.items():
        raw = z.buf[z.vertices.off:z.vertices.off + z.vertex_count * dump.VERTEX_SIZE]
        if np is not None:
            vpos[zi] = np.frombuffer(raw, dtype='<f4', count=z.vertex_count * 11).reshape(z.vertex_count, 11)[:, 0:3]
        else:
            vpos[zi] = [r for r in struct.iter_unpack('<3f32x', raw)]
    idx_all = np.frombuffer(indices_raw, dtype='<u2') if np is not None else struct.unpack('<%dH' % d.indices.count, indices_raw)
    sb_st = struct.Struct('<6f')
    for i, r in enumerate(surf_rows):
        zi, fv, vc, tc, bi = r['transientZone'], r['tris.firstVertex'], r['tris.vertexCount'], r['tris.triCount'], r['tris.baseIndex']
        z = zones[zi]
        if bi + 3 * tc > d.indices.count:
            raise WorldError('gfxmap: surface %d: triangles run past the index buffer (baseIndex %d, %d triangles, %d indices)' % (i, bi, tc, d.indices.count))
        if fv + vc > z.vertex_count:
            raise WorldError('gfxmap: surface %d: vertex range %d+%d runs past the transient zone (%d vertices)' % (i, fv, vc, z.vertex_count))
        sl = idx_all[bi:bi + 3 * tc]
        if tc == 0:
            lo = hi = (0.0, 0.0, 0.0)
            used, cents = 0, []
        elif np is not None:
            if int(sl.max()) >= vc:
                index_oob += 1
                if fv + int(sl.max()) >= z.vertex_count:
                    raise WorldError('gfxmap: surface %d: a triangle index leaves the transient zone' % i)
            P = vpos[zi][fv + sl.astype(np.int64)].astype(np.float64)
            lo, hi = P.min(axis=0), P.max(axis=0)
            used = int(len(np.unique(sl)))
            cents = P.reshape(-1, 3, 3).mean(axis=1).tolist()
        else:
            if max(sl) >= vc:
                index_oob += 1
                if fv + max(sl) >= z.vertex_count:
                    raise WorldError('gfxmap: surface %d: a triangle index leaves the transient zone' % i)
            vp = vpos[zi]
            pts = [vp[fv + k] for k in sl]
            lo = tuple(min(p[a] for p in pts) for a in range(3))
            hi = tuple(max(p[a] for p in pts) for a in range(3))
            used = len(set(sl))
            cents = [tuple(sum(pts[t * 3 + k][a] for k in range(3)) / 3.0 for a in range(3)) for t in range(tc)]
        sb = (0.0,) * 6
        if d.surface_bounds:
            b = sb_st.unpack_from(gbuf, d.surface_bounds.off + 36 * i)
            sb = (b[0] - b[3], b[1] - b[4], b[2] - b[5], b[0] + b[3], b[1] + b[4], b[2] + b[5])
        lo, hi = [float(v) for v in lo], [float(v) for v in hi]
        surfaces.append((i, d.surface_materials[i], vc, used, tc, fv, bi, zi, r['lightmapIndex'], r['flags'], r['sortKey'],
                         r['unk1'], r['unk2'], r['unk3'], r['unk4'], r['tris.vertexLayerData'], r['tris.maxEdgeLength'],
                         lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]) + tuple(sb))
        tri_rows.extend((i, c[0], c[1], c[2]) for c in cents)
    log('surfaces: %d, triangles %d, indices past the stored vertex count: %d surfaces' % (len(surfaces), len(tri_rows), index_oob))

    # static models
    sd_fields = ['origin[%d]' % k for k in range(3)] + ['axis[%d]' % k for k in range(9)] + [
        'scale', 'cullDist', 'flags', 'lightingHandle', 'unk0', 'unk1', 'unk2', 'unk3', 'unk5'] + [
        'unk6[%d]' % k for k in range(4)] + ['unk9', 'unk10', 'unk11', 'unk13', 'unk14'] + [
        'unk15[%d]' % k for k in range(4)] + ['primaryLightEnvIndex', 'reflectionProbeIndex', 'firstMtlSkinIndex',
                                              'sunShadowFlags', 'transientZone', 'unk21', 'lmOffset[0]', 'lmOffset[1]',
                                              'lmScale[0]', 'lmScale[1]', 'lmIndex', 'vertexLightingInfo.numLightingValues']
    sd_st, sd_names = SD.compiled(sd_fields)
    si_st, si_names = SI.compiled(['bounds.mid[%d]' % k for k in range(3)] + ['bounds.half[%d]' % k for k in range(3)] +
                                  ['lightingOrigin[%d]' % k for k in range(3)])
    lod = struct.unpack_from('<%dI' % d.lod_data.count, gbuf, d.lod_data.off) if d.lod_data else [0] * (d.header['dpvs.smodelCount'] + 1)
    spos = [0] * d.header['dpvs.smodelCount']
    if d.sorted_smodel_indices:
        for pos_, idx_ in enumerate(struct.unpack_from('<%dH' % d.sorted_smodel_indices.count, gbuf, d.sorted_smodel_indices.off)):
            if idx_ < len(spos):
                spos[idx_] = pos_
    smodels, worst_round, worst_ortho, bad_det = [], 0.0, 0.0, 0
    for i in range(d.draw_insts.count):
        v = dict(zip(sd_names, sd_st.unpack_from(gbuf, d.draw_insts.off + SD.size * i)))
        ax = [tuple(v['axis[%d]' % (3 * a + b)] for b in range(3)) for a in range(3)]
        for p in range(3):
            for q in range(3):
                dot = sum(ax[p][k] * ax[q][k] for k in range(3))
                worst_ortho = max(worst_ortho, abs(dot - (1.0 if p == q else 0.0)))
        det = (ax[0][0] * (ax[1][1] * ax[2][2] - ax[1][2] * ax[2][1]) - ax[0][1] * (ax[1][0] * ax[2][2] - ax[1][2] * ax[2][0]) +
               ax[0][2] * (ax[1][0] * ax[2][1] - ax[1][1] * ax[2][0]))
        if det < 0:
            bad_det += 1
        pitch, yaw, roll = axis_to_angles(ax)
        worst_round = max(worst_round, max_matrix_diff(ax, angles_to_axis(pitch, yaw, roll)))
        b = dict(zip(si_names, si_st.unpack_from(gbuf, d.smodel_insts.off + SI.size * i)))
        u15 = v['unk15[0]'] | v['unk15[1]'] << 8 | v['unk15[2]'] << 16 | v['unk15[3]'] << 24
        smodels.append((i, d.smodel_models[i], v['origin[0]'], v['origin[1]'], v['origin[2]']) +
                       tuple(v['axis[%d]' % k] for k in range(9)) +
                       (pitch, yaw, roll, v['scale'], v['cullDist'], v['flags'], lod[i] if i < len(lod) else 0, spos[i],
                        v['lightingHandle'], v['unk0'], v['unk1'], v['unk2'], v['unk3'], v['unk5'],
                        v['unk6[0]'], v['unk6[1]'], v['unk6[2]'], v['unk6[3]'], v['unk9'], v['unk10'], v['unk11'],
                        v['unk13'], v['unk14'], u15, v['primaryLightEnvIndex'], v['reflectionProbeIndex'],
                        v['firstMtlSkinIndex'], v['sunShadowFlags'], v['transientZone'], v['unk21'],
                        v['lmOffset[0]'], v['lmOffset[1]'], v['lmScale[0]'], v['lmScale[1]'], v['lmIndex'],
                        v['vertexLightingInfo.numLightingValues']) +
                       tuple(b[n] for n in si_names))
    log('static models: %d, worst orthonormality %.2e, worst angle round trip %.2e, mirrored %d' % (
        len(smodels), worst_ortho, worst_round, bad_det))

    # lights
    if 'commap_json' in files:
        with open(files['commap_json'], 'rb') as f:
            raw = f.read()
        try:
            cw = json.loads(raw.decode('utf-8'))
        except ValueError as e:
            raise WorldError('%s: not valid JSON: %s' % (files['commap_json'], e))
        lights_src = [light_from_json(x) for x in cw.get('primaryLight', [])]
        note('commap_json', files['commap_json'], len(raw))
    elif 'commap' in files:
        with open(files['commap'], 'rb') as f:
            raw = f.read()
        cw = dump.parse_commap_binary(raw, os.path.basename(files['commap']))
        lights_src = cw['primaryLight']
        note('commap', files['commap'], len(raw))
    else:
        raise WorldError('no .commap.json or .commap next to %s' % files['gfxmap'])
    if len(lights_src) != d.header['primaryLightCount']:
        raise WorldError('lights: the com world holds %d primary lights but the gfx world declares %d' % (
            len(lights_src), d.header['primaryLightCount']))
    lights = []
    for i, L in enumerate(lights_src):
        o = L['origin']
        placed = int(L['type'] != 0 and any(abs(c) > 1e-6 for c in o))
        co, ci = L['cosHalfFovOuter'], L['cosHalfFovInner']
        lights.append((i, L['type'], LIGHT_TYPES.get(L['type'], str(L['type'])), placed, L['canUseShadowMap'],
                       L['needsDynamicShadows'], L['isVolumetric'], L['exponent'], L['transientZoneList'], L['entityId'],
                       L['uvIntensity'], L['irIntensity'], *L['color'], *L['dir'], *L['up'], *o, L['radius'],
                       *L['fadeOffsetRt'], L['bulbRadius'], *L['bulbLength'], co, ci,
                       math.degrees(math.acos(max(-1.0, min(1.0, co)))) * 2.0, math.degrees(math.acos(max(-1.0, min(1.0, ci)))) * 2.0,
                       L['shadowSoftness'], L['shadowBias'], L['shadowArea'], L['distanceFalloff'], L['rotationLimit'],
                       L['translationLimit'], L['defName']))

    # entities
    ents, kvs = [], []
    if 'ents' in files:
        with open(files['ents'], 'rb') as f:
            raw = f.read()
        blocks = parse_ents_text(raw)
        note('ents', files['ents'], len(raw))
        for i, kv in enumerate(blocks):
            o = parse_vec3(ent_get(kv, 'origin') or '')
            ents.append((i, ent_get(kv, 'classname'), ent_get(kv, 'targetname'), *(o if o else (None, None, None)),
                         ent_get(kv, 'model'), ent_get(kv, 'angles')))
            kvs.extend((i, k, ENT_KEYS.get(k, k), v) for k, v in kv)
    for kind, suffix in (('ents.data', '.ents.data'), ('colmap', '.colmap'), ('colmap.hkx', '.colmap.hkx'),
                         ('fxmap', '.fxmap'), ('glassmap', '.glassmap'), ('navmesh', '.navmesh'), ('aipaths', '.aipaths')):
        p = files['gfxmap'][:-len('.gfxmap')] + suffix
        if os.path.isfile(p):
            note(kind + ' (listed, not read)', p)

    # models and catalog
    cat = {}
    if catalog:
        with open(catalog, 'rb') as f:
            data = json.loads(f.read().decode('utf-8'))
        for m in data.get('models', data) if isinstance(data, dict) else data:
            if isinstance(m, dict) and 'name' in m:
                cat[m['name']] = m
    counts = {}
    for m in d.smodel_models:
        counts[m] = counts.get(m, 0) + 1
    models = []
    for name in sorted(counts):
        m = cat.get(name)
        if m:
            b = m.get('bounds') or {}
            lods = m.get('lods') or []
            mins, maxs = b.get('mins') or (None,) * 3, b.get('maxs') or (None,) * 3
            models.append((name, counts[name], 1, m.get('category'), m.get('numLods'), lods[0].get('tris') if lods else None,
                           m.get('radius'), *mins, *maxs))
        else:
            models.append((name, counts[name], 0) + (None,) * 10)

    # write the database and the side file
    if os.path.exists(db_path):
        os.remove(db_path)
    mp = mesh_path(db_path)
    with open(mp, 'wb') as mf:
        zone_rows = []
        for zi, z in sorted(zones.items()):
            zone_rows.append((zi, z.zname, z.vertex_count, mf.tell()))
            mf.write(z.buf[z.vertices.off:z.vertices.off + z.vertex_count * dump.VERTEX_SIZE])
        index_off = mf.tell()
        mf.write(indices_raw)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    _insert(con, 'smodels', smodels)
    _insert(con, 'surfaces', surfaces)
    _insert(con, 'tris', tri_rows)
    _insert(con, 'lights', lights)
    _insert(con, 'probes', [(p[0], p[1], *p[2], *p[3], p[4]) for p in d.probes])
    _insert(con, 'probe_instances', d.probe_instances)
    _insert(con, 'assets', [(k, i, n) for k, i, n in d.named_assets])
    _insert(con, 'brush_models', [(b[0], *b[1], *b[2], b[3], b[4], b[5]) for b in d.brush_models])
    _insert(con, 'ents', ents)
    _insert(con, 'ent_kv', kvs)
    _insert(con, 'models', models)
    _insert(con, 'mesh_zones', zone_rows)
    counts_meta = {'surfaces': len(surfaces), 'smodels': len(smodels), 'primaryLights': len(lights),
                   'probes': len(d.probes), 'models': len(d.brush_models), 'triangles': len(tri_rows),
                   'entities': len(ents), 'distinct_models': len(models), 'probe_instances': len(d.probe_instances),
                   'vertices': sum(z.vertex_count for z in zones.values()), 'indices': d.indices.count}
    declared = {'surfaces': d.header['surfaceCount'], 'smodels': d.header['dpvs.smodelCount'],
                'primaryLights': d.header['primaryLightCount'], 'probes': d.header['draw.reflectionProbeCount'],
                'models': d.header['modelCount']}
    meta = {'reader_version': READER_VERSION, 'dump_path': dump_dir, 'map_name': map_name, 'files': meta_files,
            'counts': counts_meta, 'declared_counts': declared, 'mesh_file': os.path.basename(mp),
            'mesh_index_offset': index_off, 'mesh_index_count': d.indices.count, 'index_oob_surfaces': index_oob,
            'worst_orthonormality': worst_ortho, 'worst_angle_roundtrip': worst_round, 'mirrored_smodels': bad_det,
            'gfx_header': d.header, 'gfx_name': d.name, 'gfx_base_name': d.base_name,
            'entries_in_gfxmap': d.entries, 'built_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'numpy': np is not None, 'build_seconds': round(time.time() - t0, 3)}
    for k, v in meta.items():
        con.execute('INSERT INTO meta VALUES(?,?)', (k, json.dumps(v)))
    con.commit()
    con.close()
    log('database %s (%d bytes) and side file %s (%d bytes) in %.1fs' % (
        db_path, os.path.getsize(db_path), mp, os.path.getsize(mp), time.time() - t0))
    return meta


# ---------------------------------------------------------------- queries

def _rows(cur):
    names = [c[0] for c in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


class World:
    def __init__(self, db_path):
        if not os.path.isfile(db_path):
            raise WorldError('database not found: %s' % db_path)
        self.path = db_path
        self.con = sqlite3.connect(db_path)
        self.meta = {k: json.loads(v) for k, v in self.con.execute('SELECT key, value FROM meta')}
        if self.meta.get('reader_version', '').split('.')[0] != READER_VERSION.split('.')[0]:
            raise WorldError('database was built by reader %s, this is %s: rebuild it' % (self.meta.get('reader_version'), READER_VERSION))

    def q(self, sql, args=()):
        return _rows(self.con.execute(sql, args))

    # -- mesh
    def surface_mesh(self, i):
        """Mesh of surface i: dict with positions, normals, uvs (texture), lmuvs (lightmap) as lists of tuples,
        tangents (decoded like the normals), signs (the raw fourth vertex float), colors (u32) and
        tris as index triples into them. Only the vertices the triangles use are returned (indices remapped).
        Normals are the 10:10:10 packed unit vectors decoded to [-1, 1] (v = bits / 511.5 - 1)."""
        rows = self.q('SELECT material, tri_count, first_vertex, base_index, transientZone FROM surfaces WHERE i=?', (i,))
        if not rows:
            raise WorldError('no surface %d' % i)
        s = rows[0]
        zrow = self.q('SELECT vertex_count, offset FROM mesh_zones WHERE zone=?', (s['transientZone'],))[0]
        n = s['tri_count'] * 3
        mesh_file = os.path.join(os.path.dirname(os.path.abspath(self.path)), self.meta['mesh_file'])
        with open(mesh_file, 'rb') as f:
            f.seek(self.meta['mesh_index_offset'] + 2 * s['base_index'])
            raw = f.read(2 * n)
            if len(raw) != 2 * n:
                raise WorldError('mesh side file is truncated (surface %d)' % i)
            idx = struct.unpack('<%dH' % n, raw)
            if not idx:
                return {'material': s['material'], 'positions': [], 'normals': [], 'uvs': [], 'lmuvs': [], 'tangents': [],
                        'signs': [], 'colors': [], 'tris': []}
            lo, hi = min(idx), max(idx)
            first = s['first_vertex'] + lo
            count = hi - lo + 1
            if first + count > zrow['vertex_count']:
                raise WorldError('surface %d: vertex range leaves the zone' % i)
            f.seek(zrow['offset'] + first * dump.VERTEX_SIZE)
            vraw = f.read(count * dump.VERTEX_SIZE)
        pos, nrm, uv, lm = dump.decode_vertices(vraw, count)
        tan, sign, col = dump.decode_vertex_extras(vraw, count)
        used = sorted(set(idx))
        remap = {v: k for k, v in enumerate(used)}
        return {'material': s['material'], 'positions': [pos[v - lo] for v in used], 'normals': [nrm[v - lo] for v in used],
                'uvs': [uv[v - lo] for v in used], 'lmuvs': [lm[v - lo] for v in used],
                'tangents': [tan[v - lo] for v in used], 'signs': [sign[v - lo] for v in used],
                'colors': [col[v - lo] for v in used],
                'tris': [(remap[idx[k]], remap[idx[k + 1]], remap[idx[k + 2]]) for k in range(0, n, 3)]}

    # -- statistics
    def stats(self):
        m = self.meta
        c, dec = m['counts'], m['declared_counts']
        gt = GROUND_TRUTH.get(m['map_name'], {})
        counts = []
        for k in ('surfaces', 'smodels', 'primaryLights', 'probes', 'models'):
            counts.append({'name': k, 'read': c[k], 'file_header': dec[k], 'ground_truth': gt.get(k)})
        bb = lambda sql: self.q(sql)[0]  # noqa: E731
        props = bb('SELECT min(x) x0, min(y) y0, min(z) z0, max(x) x1, max(y) y1, max(z) z1 FROM smodels')
        surf = bb('SELECT min(minx) x0, min(miny) y0, min(minz) z0, max(maxx) x1, max(maxy) y1, max(maxz) z1 FROM surfaces WHERE tri_count>0')
        top_models = self.q('SELECT model, count(*) n FROM smodels GROUP BY model ORDER BY n DESC, model LIMIT 20')
        top_mats = self.q('SELECT material, sum(tri_count) tris, count(*) surfaces FROM surfaces GROUP BY material '
                          'ORDER BY tris DESC, material LIMIT 20')
        return {'map': m['map_name'], 'reader_version': m['reader_version'], 'counts': counts,
                'extra': {'triangles': c['triangles'], 'vertices': c['vertices'], 'indices': c['indices'],
                          'entities': c['entities'], 'distinct_models': c['distinct_models']},
                'props_bbox': props, 'surfaces_bbox': surf, 'top_models': top_models, 'top_materials': top_mats}

    # -- spatial queries
    def box(self, b, limit=None):
        x1, y1, z1, x2, y2, z2 = (min(b[0], b[3]), min(b[1], b[4]), min(b[2], b[5]), max(b[0], b[3]), max(b[1], b[4]), max(b[2], b[5]))
        props = self.q('SELECT * FROM smodels WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ? ORDER BY i',
                       (x1, x2, y1, y2, z1, z2))
        lights = self.q('SELECT * FROM lights WHERE placed=1 AND x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ? ORDER BY i',
                        (x1, x2, y1, y2, z1, z2))
        ents = self.q('SELECT * FROM ents WHERE origin_x BETWEEN ? AND ? AND origin_y BETWEEN ? AND ? AND origin_z BETWEEN ? AND ? ORDER BY i',
                      (x1, x2, y1, y2, z1, z2))
        surfs = self.q('SELECT s.i, s.material, s.tri_count, '
                       '(SELECT count(*) FROM tris t WHERE t.surface=s.i AND t.cx BETWEEN ? AND ? AND t.cy BETWEEN ? AND ? AND t.cz BETWEEN ? AND ?) AS tris_in_box '
                       'FROM surfaces s WHERE s.tri_count>0 AND s.maxx>=? AND s.minx<=? AND s.maxy>=? AND s.miny<=? AND s.maxz>=? AND s.minz<=? ORDER BY s.i',
                       (x1, x2, y1, y2, z1, z2, x1, x2, y1, y2, z1, z2))
        touching = [s for s in surfs]
        in_box = [s for s in surfs if s['tris_in_box'] > 0]
        return {'box': [x1, y1, z1, x2, y2, z2], 'props': props, 'lights': lights, 'ents': ents, 'surfaces_touching': touching,
                'surfaces': in_box, 'triangles': sum(s['tris_in_box'] for s in in_box)}

    def near(self, p, radius, kinds=('props', 'lights', 'ents', 'surfaces')):
        b = (p[0] - radius, p[1] - radius, p[2] - radius, p[0] + radius, p[1] + radius, p[2] + radius)
        r2 = radius * radius
        out = {'point': list(p), 'radius': radius}
        dist = lambda x, y, z: math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2)  # noqa: E731
        if 'props' in kinds:
            rows = self.q('SELECT * FROM smodels WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?',
                          (b[0], b[3], b[1], b[4], b[2], b[5]))
            rows = [dict(r, dist=dist(r['x'], r['y'], r['z'])) for r in rows]
            out['props'] = sorted([r for r in rows if r['dist'] ** 2 <= r2], key=lambda r: (r['dist'], r['i']))
        if 'lights' in kinds:
            rows = self.q('SELECT * FROM lights WHERE placed=1 AND x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?',
                          (b[0], b[3], b[1], b[4], b[2], b[5]))
            rows = [dict(r, dist=dist(r['x'], r['y'], r['z'])) for r in rows]
            out['lights'] = sorted([r for r in rows if r['dist'] ** 2 <= r2], key=lambda r: (r['dist'], r['i']))
        if 'ents' in kinds:
            rows = self.q('SELECT * FROM ents WHERE origin_x BETWEEN ? AND ? AND origin_y BETWEEN ? AND ? AND origin_z BETWEEN ? AND ?',
                          (b[0], b[3], b[1], b[4], b[2], b[5]))
            rows = [dict(r, dist=dist(r['origin_x'], r['origin_y'], r['origin_z'])) for r in rows]
            out['ents'] = sorted([r for r in rows if r['dist'] ** 2 <= r2], key=lambda r: (r['dist'], r['i']))
        if 'surfaces' in kinds:
            rows = self.q('SELECT surface, count(*) tris, min(cx) x0, max(cx) x1 FROM tris WHERE cx BETWEEN ? AND ? AND cy BETWEEN ? AND ? '
                          'AND cz BETWEEN ? AND ? GROUP BY surface', (b[0], b[3], b[1], b[4], b[2], b[5]))
            mats = {r['i']: r['material'] for r in self.q('SELECT i, material FROM surfaces WHERE i IN (%s)' % ','.join(str(r['surface']) for r in rows) if rows else 'SELECT 0 i, 0 material WHERE 0')}
            out['surfaces'] = [{'i': r['surface'], 'material': mats.get(r['surface']), 'triangles_in_cube': r['tris']} for r in rows]
        return out

    def find_model(self, text):
        rows = self.q('SELECT model, count(*) n, avg(x) cx, avg(y) cy, avg(z) cz FROM smodels WHERE model LIKE ? ESCAPE ? GROUP BY model ORDER BY n DESC, model',
                      ('%' + text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%', '\\'))
        return rows

    def where_model(self, name):
        return self.q('SELECT i, model, x, y, z, pitch, yaw, roll, scale FROM smodels WHERE model=? ORDER BY i', (name,))

    def rooms(self, cell=512.0):
        cell = float(cell)
        if cell <= 0:
            raise WorldError('cell size must be positive')
        grid = {}

        def bump(x, y, key, n=1):
            k = (math.floor(x / cell), math.floor(y / cell))
            g = grid.setdefault(k, {'props': 0, 'lights': 0, 'ents': 0, 'triangles': 0})
            g[key] += n

        for x, y in self.con.execute('SELECT x, y FROM smodels'):
            bump(x, y, 'props')
        for x, y in self.con.execute('SELECT x, y FROM lights WHERE placed=1'):
            bump(x, y, 'lights')
        for x, y in self.con.execute('SELECT origin_x, origin_y FROM ents WHERE origin_x IS NOT NULL'):
            bump(x, y, 'ents')
        for x, y in self.con.execute('SELECT cx, cy FROM tris'):
            bump(x, y, 'triangles')
        out = [{'cell': [k[0], k[1]], 'x': [k[0] * cell, (k[0] + 1) * cell], 'y': [k[1] * cell, (k[1] + 1) * cell], **v}
               for k, v in grid.items()]
        out.sort(key=lambda r: (-r['props'], -r['triangles'], r['cell']))
        return {'cell': cell, 'cells': out}

    # -- sanity
    def check(self, dump_dir=None):
        dump_dir = dump_dir or self.meta['dump_path']
        parent = os.path.dirname(os.path.abspath(dump_dir))
        roots = [dump_dir] + [os.path.join(parent, n) for n in sorted(os.listdir(parent)) if os.path.join(parent, n) != dump_dir]
        xroots = [os.path.join(r, 'xmodel') for r in roots if os.path.isdir(os.path.join(r, 'xmodel'))]
        mroots = [os.path.join(r, 'materials') for r in roots if os.path.isdir(os.path.join(r, 'materials'))]
        res = {'xmodel_folders': len(xroots), 'materials_folders': len(mroots)}
        names = self.q('SELECT model, count(*) n FROM smodels GROUP BY model')
        bad_names = [r['model'] for r in names if not r['model'] or not all(32 < ord(ch) < 127 for ch in r['model'])]
        present = lambda n: any(os.path.isfile(os.path.join(x, n + '.xmb')) for x in xroots)  # noqa: E731
        missing = [r['model'] for r in names if r['model'] and not present(r['model'])]
        res['props'] = {'rows': self.meta['counts']['smodels'], 'distinct_models': len(names), 'bad_names': len(bad_names),
                        'models_with_file': len(names) - len(missing), 'models_without_file': len(missing),
                        'missing_examples': missing[:5]}

        def mat_present(n):
            rel = n.replace('*', '_') + '.json'
            return any(os.path.isfile(os.path.join(m, rel)) for m in mroots)

        mats = [r['material'] for r in self.q('SELECT DISTINCT material FROM surfaces')]
        mmiss = [n for n in mats if not n or not mat_present(n)]
        res['materials'] = {'distinct': len(mats), 'with_file': len(mats) - len(mmiss), 'without_file': len(mmiss),
                            'missing_examples': mmiss[:5]}
        lim = (-20000, 20000, -20000, 20000, -5000, 5000)
        po = self.q('SELECT count(*) n FROM smodels WHERE x NOT BETWEEN ? AND ? OR y NOT BETWEEN ? AND ? OR z NOT BETWEEN ? AND ?', lim)[0]['n']
        so = self.q('SELECT count(*) n FROM surfaces WHERE tri_count>0 AND (minx < ? OR maxx > ? OR miny < ? OR maxy > ? OR minz < ? OR maxz > ?)',
                    (-20000, 20000, -20000, 20000, -5000, 5000))[0]['n']
        res['outliers'] = {'box': 'x -20000..20000 y -20000..20000 z -5000..5000', 'props_outside': po, 'surfaces_outside': so,
                           'prop_examples': self.q('SELECT i, model, x, y, z FROM smodels WHERE x NOT BETWEEN ? AND ? OR y NOT BETWEEN ? AND ? OR z NOT BETWEEN ? AND ? LIMIT 5', lim),
                           'surface_examples': self.q('SELECT i, material, minx, miny, minz, maxx, maxy, maxz FROM surfaces WHERE tri_count>0 AND (minx < ? OR maxx > ? OR miny < ? OR maxy > ? OR minz < ? OR maxz > ?) LIMIT 5',
                                                      (-20000, 20000, -20000, 20000, -5000, 5000))}
        res['orientation'] = {'worst_orthonormality': self.meta['worst_orthonormality'], 'worst_angle_roundtrip': self.meta['worst_angle_roundtrip'],
                              'mirrored': self.meta['mirrored_smodels']}
        res['indices'] = {'surfaces_with_index_past_stored_vertex_count': self.meta['index_oob_surfaces']}
        return res


    def compare_smodels_csv(self, csv_path, tol=0.01):
        """Compare the static models with a table written independently by the map compiler's own reader
        (IWZ_DUMP_SMODELS csv: i,model,x,y,z,scale,flags,cull,lod,sortedPos,unk0,...,handle,...,tz,...,lmIdx,...).
        Returns the number of rows compared and the rows that differ."""
        import csv
        with open(csv_path, newline='') as f:
            ref = [r for r in csv.DictReader(f) if r['i'].isdigit()]
        mine = {r['i']: r for r in self.q('SELECT * FROM smodels')}
        bad, worst = [], 0.0
        for r in ref:
            m = mine.get(int(r['i']))
            if m is None:
                bad.append((r['i'], 'missing'))
                continue
            dpos = max(abs(m['x'] - float(r['x'])), abs(m['y'] - float(r['y'])), abs(m['z'] - float(r['z'])))
            worst = max(worst, dpos)
            same = (m['model'] == r['model'] and dpos <= tol and abs(m['scale'] - float(r['scale'])) <= 1e-4 * max(1.0, abs(m['scale'])) and
                    m['flags'] == int(r['flags']) and m['cullDist'] == int(r['cull']) and m['lod_slot'] == int(r['lod']) and
                    m['sorted_pos'] == int(r['sortedPos']) and m['unk0'] == int(r['unk0']) and m['lightingHandle'] == int(r['handle']) and
                    m['transientZone'] == int(r['tz']) and m['lmIndex'] == int(r['lmIdx']))
            if not same:
                bad.append((r['i'], 'differs'))
        return {'compared': len(ref), 'mine': len(mine), 'differing': len(bad), 'examples': bad[:5], 'worst_position_difference': worst}


# ---------------------------------------------------------------- prefabs

def extract(world, box, name, out_dir):
    b = world.box(box)
    x1, y1, z1, x2, y2, z2 = b['box']
    origin = ((x1 + x2) / 2.0, (y1 + y2) / 2.0, z1)
    rel = lambda p: [p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]]  # noqa: E731
    props = [{'model': r['model'], 'pos': rel((r['x'], r['y'], r['z'])), 'pitch': r['pitch'], 'yaw': r['yaw'],
              'roll': r['roll'], 'scale': r['scale'], 'flags': r['flags'], 'cullDist': r['cullDist']} for r in b['props']]
    lights = []
    for r in b['lights']:
        L = {k: r[k] for k in ('type', 'canUseShadowMap', 'needsDynamicShadows', 'isVolumetric', 'exponent', 'transientZoneList',
                               'entityId', 'uvIntensity', 'irIntensity', 'radius', 'bulbRadius', 'cosHalfFovOuter',
                               'cosHalfFovInner', 'shadowSoftness', 'shadowBias', 'shadowArea', 'distanceFalloff',
                               'rotationLimit', 'translationLimit', 'defName')}
        L['color'] = [r['color_r'], r['color_g'], r['color_b']]
        L['dir'] = [r['dir_x'], r['dir_y'], r['dir_z']]
        L['up'] = [r['up_x'], r['up_y'], r['up_z']]
        L['pos'] = rel((r['x'], r['y'], r['z']))
        L['fadeOffsetRt'] = [r['fadeOffsetRt_0'], r['fadeOffsetRt_1']]
        L['bulbLength'] = [r['bulbLength_x'], r['bulbLength_y'], r['bulbLength_z']]
        lights.append(L)
    ents = []
    for r in b['ents']:
        kv = [[r2['key'], r2['value']] for r2 in world.q('SELECT key, value FROM ent_kv WHERE i=? ORDER BY rowid', (r['i'],))]
        o = rel((r['origin_x'], r['origin_y'], r['origin_z']))
        for item in kv:
            if item[0] in ('543', 'origin'):
                item[1] = ' '.join(fmt(c) for c in o)
        ents.append({'origin': o, 'kv': kv})
    os.makedirs(out_dir, exist_ok=True)
    surfaces, blob, extra, triangles, vertices = [], bytearray(), bytearray(), 0, 0
    attrs = {r['i']: r for r in world.q('SELECT i, lightmapIndex, flags, vertexLayerData FROM surfaces')}
    for s in b['surfaces_touching']:
        mesh = world.surface_mesh(s['i'])
        keep = []
        for t in mesh['tris']:
            c = [sum(mesh['positions'][t[k]][a] for k in range(3)) / 3.0 for a in range(3)]
            if x1 <= c[0] <= x2 and y1 <= c[1] <= y2 and z1 <= c[2] <= z2:
                keep.append(t)
        if not keep:
            continue
        used = sorted({v for t in keep for v in t})
        remap = {v: k for k, v in enumerate(used)}
        a = attrs[s['i']]
        entry = {'material': mesh['material'], 'source_surface': s['i'], 'vertices': len(used), 'triangles': len(keep),
                 'offset': len(blob), 'extra_offset': len(extra), 'lightmapIndex': a['lightmapIndex'], 'flags': a['flags'],
                 'layered': bool(a['vertexLayerData'])}
        for v in used:
            extra += struct.pack('<3f', *mesh['tangents'][v])
        for v in used:
            extra += struct.pack('<fI', mesh['signs'][v], mesh['colors'][v])
        for key, comps in (('positions', 3), ('normals', 3), ('uvs', 2), ('lmuvs', 2)):
            for v in used:
                p = mesh[key][v]
                if key == 'positions':
                    p = rel(p)
                blob += struct.pack('<%df' % comps, *p)
        for t in keep:
            blob += struct.pack('<3I', remap[t[0]], remap[t[1]], remap[t[2]])
        surfaces.append(entry)
        triangles += len(keep)
        vertices += len(used)
    with open(os.path.join(out_dir, 'surfaces.bin'), 'wb') as f:
        f.write(bytes(blob))
    with open(os.path.join(out_dir, EXTRA_FILE), 'wb') as f:
        f.write(bytes(extra))
    prefab = {'schema': PREFAB_SCHEMA, 'name': name, 'source': {'map': world.meta['map_name'], 'reader_version': READER_VERSION},
              'box': [x1, y1, z1, x2, y2, z2], 'origin': list(origin), 'yaw': 0.0, 'space': 'relative',
              'counts': {'props': len(props), 'lights': len(lights), 'ents': len(ents), 'surfaces': len(surfaces),
                         'triangles': triangles, 'vertices': vertices},
              'mesh': {'file': 'surfaces.bin', 'layout': 'per surface: positions f32x3, normals f32x3, uvs f32x2, lmuvs f32x2 '
                                                         '(per vertex, arrays in that order), then triangles u32x3; little endian; origin-relative'},
              'mesh_extra': {'file': EXTRA_FILE, 'layout': 'per surface, at extra_offset: tangents f32x3 per vertex, then '
                                                           '(fourth vertex float f32, colour u32) per vertex; little endian'},
              'props': props, 'lights': lights, 'ents': ents, 'surfaces': surfaces}
    _write_prefab(out_dir, prefab)
    return prefab


def _write_prefab(out_dir, prefab):
    with open(os.path.join(out_dir, 'prefab.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(prefab, f, indent=1)
        f.write('\n')
    lines = ['%s %s %s %s %s %s %s %s' % (p['model'], fmt(p['pos'][0]), fmt(p['pos'][1]), fmt(p['pos'][2]), fmt(p['pitch']),
                                         fmt(p['yaw']), fmt(p['roll']), fmt(p['scale'])) for p in prefab['props']]
    with open(os.path.join(out_dir, 'smodels.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + ('\n' if lines else ''))


def load_prefab(prefab_dir):
    path = os.path.join(prefab_dir, 'prefab.json')
    if not os.path.isfile(path):
        raise WorldError('no prefab.json in %s' % prefab_dir)
    with open(path, 'r', encoding='utf-8') as f:
        p = json.load(f)
    if p.get('schema') != PREFAB_SCHEMA:
        raise WorldError('%s: schema is %r, expected %s' % (path, p.get('schema'), PREFAB_SCHEMA))
    return p


def read_prefab_surface(prefab_dir, prefab, k):
    """Mesh of surface k of a prefab: dict positions, normals, uvs, lmuvs, tris."""
    s = prefab['surfaces'][k]
    with open(os.path.join(prefab_dir, prefab['mesh']['file']), 'rb') as f:
        data = f.read()
    nv, nt, off = s['vertices'], s['triangles'], s['offset']
    need = off + nv * 40 + nt * 12
    if need > len(data):
        raise WorldError('prefab mesh file is truncated (surface %d)' % k)
    f32 = struct.unpack_from('<%df' % (nv * 10), data, off)
    pos = [tuple(f32[3 * i:3 * i + 3]) for i in range(nv)]
    nrm = [tuple(f32[3 * nv + 3 * i:3 * nv + 3 * i + 3]) for i in range(nv)]
    uv = [tuple(f32[6 * nv + 2 * i:6 * nv + 2 * i + 2]) for i in range(nv)]
    lm = [tuple(f32[8 * nv + 2 * i:8 * nv + 2 * i + 2]) for i in range(nv)]
    ix = struct.unpack_from('<%dI' % (nt * 3), data, off + nv * 40)
    out = {'material': s['material'], 'positions': pos, 'normals': nrm, 'uvs': uv, 'lmuvs': lm,
           'tris': [tuple(ix[3 * t:3 * t + 3]) for t in range(nt)]}
    if prefab.get('mesh_extra') and 'extra_offset' in s:
        with open(os.path.join(prefab_dir, prefab['mesh_extra']['file']), 'rb') as f:
            ex = f.read()
        eo = s['extra_offset']
        if eo + nv * 20 > len(ex):
            raise WorldError('prefab extra mesh file is truncated (surface %d)' % k)
        t32 = struct.unpack_from('<%df' % (nv * 3), ex, eo)
        out['tangents'] = [tuple(t32[3 * i:3 * i + 3]) for i in range(nv)]
        sc = struct.unpack_from('<' + 'fI' * nv, ex, eo + nv * 12)
        out['signs'] = list(sc[0::2])
        out['colors'] = list(sc[1::2])
    return out


def place(prefab_dir, at, yaw, out_dir):
    """Rotate the prefab about the vertical axis through its origin by `yaw` degrees, then put its origin at `at`.
    The result is a world-space prefab (space = "world", positions absolute, origin = `at`); a prefab that is
    already world-space is first brought back to origin-relative coordinates, so it can be placed again."""
    p = load_prefab(prefab_dir)
    cs = _cos_sin(yaw)
    at = [float(v) for v in at]
    o0 = p['origin'] if p.get('space', 'relative') == 'world' else [0.0, 0.0, 0.0]
    tr = lambda v: [a + b for a, b in zip(rot_z([v[0] - o0[0], v[1] - o0[1], v[2] - o0[2]], cs), at)]  # noqa: E731
    out = dict(p)
    out['source'] = dict(p['source'])
    out['placed_from'] = {'prefab': p['name'], 'at': at, 'yaw': yaw}
    out['space'] = 'world'
    out['origin'] = at
    out['yaw'] = (p.get('yaw', 0.0) + yaw)
    props = []
    for r in p['props']:
        ax = angles_to_axis(r['pitch'], r['yaw'], r['roll'])
        ax = [rot_z(row, cs) for row in ax]
        pitch, yw, roll = axis_to_angles(ax)
        n = dict(r)
        n.update({'pos': tr(r['pos']), 'pitch': pitch, 'yaw': yw, 'roll': roll})
        props.append(n)
    lights = []
    for r in p['lights']:
        n = dict(r)
        n['pos'] = tr(r['pos'])
        n['dir'] = list(rot_z(r['dir'], cs))
        n['up'] = list(rot_z(r['up'], cs))
        lights.append(n)
    ents = []
    for r in p['ents']:
        o = tr(r['origin'])
        kv = []
        for k, v in r['kv']:
            if k in ('543', 'origin'):
                v = ' '.join(fmt(c) for c in o)
            elif k in ('65', 'angles'):
                a = parse_vec3(v)
                if a:
                    ax = [rot_z(row, cs) for row in angles_to_axis(*a)]
                    v = ' '.join(fmt(c) for c in axis_to_angles(ax))
            kv.append([k, v])
        ents.append({'origin': o, 'kv': kv})
    out['props'], out['lights'], out['ents'] = props, lights, ents
    os.makedirs(out_dir, exist_ok=True)
    blob, extra = bytearray(), bytearray()
    new_surfaces = []
    for k, s in enumerate(p['surfaces']):
        m = read_prefab_surface(prefab_dir, p, k)
        s2 = dict(s)
        s2['offset'] = len(blob)
        if 'tangents' in m:
            s2['extra_offset'] = len(extra)
            for t in m['tangents']:
                extra += struct.pack('<3f', *rot_z(t, cs))
            for sg, c in zip(m['signs'], m['colors']):
                extra += struct.pack('<fI', sg, c)
        for pos in m['positions']:
            blob += struct.pack('<3f', *tr(pos))
        for n in m['normals']:
            blob += struct.pack('<3f', *rot_z(n, cs))
        for key in ('uvs', 'lmuvs'):
            for v in m[key]:
                blob += struct.pack('<2f', *v)
        for t in m['tris']:
            blob += struct.pack('<3I', *t)
        new_surfaces.append(s2)
    out['surfaces'] = new_surfaces
    with open(os.path.join(out_dir, out['mesh']['file']), 'wb') as f:
        f.write(bytes(blob))
    if out.get('mesh_extra'):
        with open(os.path.join(out_dir, out['mesh_extra']['file']), 'wb') as f:
            f.write(bytes(extra))
    _write_prefab(out_dir, out)
    return out


# ---------------------------------------------------------------- command line

def _f(v):
    return ('%.2f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def _emit(obj, args, text_fn):
    if getattr(args, 'json', False):
        print(json.dumps(obj, indent=1))
    else:
        text_fn(obj)


def _prop_line(r):
    return '  #%d %s (%s, %s, %s) yaw %s scale %s' % (r['i'], r['model'], _f(r['x']), _f(r['y']), _f(r['z']), _f(r['yaw']), _f(r['scale']))


def _light_line(r):
    return '  #%d %s (%s, %s, %s) r %s %s' % (r['i'], r['type_name'], _f(r['x']), _f(r['y']), _f(r['z']), _f(r['radius']), r['defName'] or '')


def _ent_line(r):
    return '  #%d %s %s (%s, %s, %s)' % (r['i'], r['classname'], r['targetname'] or '-', _f(r['origin_x']), _f(r['origin_y']), _f(r['origin_z']))


def cmd_stats(w, args):
    def text(s):
        print('map %s (reader %s)' % (s['map'], s['reader_version']))
        print('%-14s %8s %12s %13s' % ('count', 'read', 'file header', 'ground truth'))
        for c in s['counts']:
            print('%-14s %8d %12d %13s' % (c['name'], c['read'], c['file_header'], c['ground_truth'] if c['ground_truth'] is not None else 'n/a'))
        print('triangles %(triangles)d vertices %(vertices)d indices %(indices)d entities %(entities)d distinct models %(distinct_models)d' % s['extra'])
        for k in ('props_bbox', 'surfaces_bbox'):
            b = s[k]
            print('%s: x %s..%s y %s..%s z %s..%s' % (k, _f(b['x0']), _f(b['x1']), _f(b['y0']), _f(b['y1']), _f(b['z0']), _f(b['z1'])))
        print('most placed models:')
        for r in s['top_models']:
            print('  %6d %s' % (r['n'], r['model']))
        print('materials by triangles:')
        for r in s['top_materials']:
            print('  %7d tris %4d surfaces  %s' % (r['tris'], r['surfaces'], r['material']))
    _emit(w.stats(), args, text)


def _limit(rows, args):
    return rows if args.limit == 0 else rows[:args.limit]


def cmd_box(w, args):
    b = w.box(args.coords)

    def text(r):
        print('box %s' % ' '.join(_f(v) for v in r['box']))
        print('props %d, lights %d, entities %d, surfaces touching %d (%d with triangles inside), triangles inside %d' % (
            len(r['props']), len(r['lights']), len(r['ents']), len(r['surfaces_touching']), len(r['surfaces']), r['triangles']))
        for title, rows, fn in (('props', r['props'], _prop_line), ('lights', r['lights'], _light_line), ('entities', r['ents'], _ent_line)):
            if rows:
                print('%s (first %d of %d):' % (title, min(len(rows), args.limit or len(rows)), len(rows)))
                for x in _limit(rows, args):
                    print(fn(x))
        mats = {}
        for s in r['surfaces']:
            m = mats.setdefault(s['material'], [0, 0])
            m[0] += 1
            m[1] += s['tris_in_box']
        if mats:
            print('materials in the box (surfaces, triangles):')
            for k, v in sorted(mats.items(), key=lambda kv: -kv[1][1])[:args.limit or None]:
                print('  %4d %7d  %s' % (v[0], v[1], k))
    if args.json:
        for key in ('props', 'lights', 'ents'):
            b[key] = _limit(b[key], args) if args.limit else b[key]
    _emit(b, args, text)


def cmd_near(w, args):
    kinds = (args.kind,) if args.kind else ('props', 'lights', 'ents', 'surfaces')
    r = w.near(args.coords, args.radius, kinds)

    def text(r):
        print('near (%s) radius %s' % (', '.join(_f(v) for v in r['point']), _f(r['radius'])))
        for k, fn in (('props', _prop_line), ('lights', _light_line), ('ents', _ent_line)):
            if k in r:
                print('%s: %d' % (k, len(r[k])))
                for x in _limit(r[k], args):
                    print(fn(x) + '  d=%s' % _f(x['dist']))
        if 'surfaces' in r:
            print('surfaces with triangles in the cube: %d, triangles %d' % (len(r['surfaces']), sum(s['triangles_in_cube'] for s in r['surfaces'])))
    if args.json:
        for k in ('props', 'lights', 'ents'):
            if k in r:
                r[k] = _limit(r[k], args)
    _emit(r, args, text)


def cmd_find(w, args):
    rows = w.find_model(args.text)

    def text(rows):
        print('%d models contain %r' % (len(rows), args.text))
        for r in _limit(rows, args):
            print('  %5d  %s  centroid (%s, %s, %s)' % (r['n'], r['model'], _f(r['cx']), _f(r['cy']), _f(r['cz'])))
    _emit(rows, args, text)


def cmd_where(w, args):
    rows = w.where_model(args.name)

    def text(rows):
        print('%d placements of %s' % (len(rows), args.name))
        for r in _limit(rows, args):
            print(_prop_line(r))
    _emit(rows, args, text)


def cmd_rooms(w, args):
    r = w.rooms(args.cell)

    def text(r):
        print('cell %s: %d non-empty cells; sorted by props' % (_f(r['cell']), len(r['cells'])))
        print('%-12s %-24s %6s %6s %5s %8s' % ('cell', 'x..y', 'props', 'lights', 'ents', 'tris'))
        for c in _limit(r['cells'], args):
            print('%-12s x %-7s y %-8s %6d %6d %5d %8d' % ('%d,%d' % tuple(c['cell']), _f(c['x'][0]), _f(c['y'][0]), c['props'], c['lights'], c['ents'], c['triangles']))
    if args.json:
        r['cells'] = _limit(r['cells'], args)
    _emit(r, args, text)


def cmd_check(w, args):
    r = w.check(args.dump)

    def text(r):
        print(json.dumps(r, indent=1))
    _emit(r, args, text)


def cmd_compare(w, args):
    r = w.compare_smodels_csv(args.csv)

    def text(r):
        print('compared %(compared)d rows (database holds %(mine)d): %(differing)d differ, worst position difference %(worst_position_difference).4g' % r)
        for e in r['examples']:
            print('  row %s: %s' % e)
    _emit(r, args, text)
    if r['differing'] or r['compared'] != r['mine']:
        raise WorldError('static model table differs from the reference table')


def cmd_extract(w, args):
    p = extract(w, args.box, args.name, args.out)
    print('prefab %s: %s' % (args.name, ', '.join('%s %d' % kv for kv in p['counts'].items())))
    print('origin %s' % ', '.join(_f(v) for v in p['origin']))


def cmd_place(args):
    p = place(args.prefab, args.at, args.yaw, args.out)
    print('placed %s at %s yaw %s: %s' % (p['name'], ', '.join(_f(v) for v in args.at), _f(args.yaw),
                                         ', '.join('%s %d' % kv for kv in p['counts'].items())))


def cmd_build(args):
    meta = build(args.dump, args.db, args.catalog, args.map)
    print('built %s: %s' % (args.db, json.dumps(meta['counts'])))


def make_parser():
    ap = argparse.ArgumentParser(prog='iw7_world', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(p, db=True):
        if db:
            p.add_argument('--db', required=True, help='database written by build')
        p.add_argument('--json', action='store_true', help='machine readable output')
        p.add_argument('--limit', type=int, default=10, help='rows listed per section (0 = all)')

    p = sub.add_parser('build', help='read a map dump into a database')
    p.add_argument('--dump', required=True)
    p.add_argument('--db', required=True)
    p.add_argument('--catalog')
    p.add_argument('--map', help='map file stem when the dump holds several')
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser('stats')
    common(p)
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser('box')
    common(p)
    p.add_argument('coords', type=float, nargs=6, metavar=('X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2'))
    p.set_defaults(fn=cmd_box)
    p = sub.add_parser('near')
    common(p)
    p.add_argument('coords', type=float, nargs=3, metavar=('X', 'Y', 'Z'))
    p.add_argument('--radius', type=float, required=True)
    p.add_argument('--kind', choices=('props', 'lights', 'ents', 'surfaces'))
    p.set_defaults(fn=cmd_near)
    p = sub.add_parser('find-model')
    common(p)
    p.add_argument('text')
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser('where-model')
    common(p)
    p.add_argument('name')
    p.set_defaults(fn=cmd_where)
    p = sub.add_parser('rooms')
    common(p)
    p.add_argument('--cell', type=float, default=512.0)
    p.set_defaults(fn=cmd_rooms)
    p = sub.add_parser('check', help='sanity checks against the dump folder')
    common(p)
    p.add_argument('--dump', help='dump folder (default: the one recorded in the database)')
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser('compare-smodels', help='compare static models with an independently written csv table')
    common(p)
    p.add_argument('--csv', required=True)
    p.set_defaults(fn=cmd_compare)
    p = sub.add_parser('extract', help='write a prefab folder for a box')
    p.add_argument('--db', required=True)
    p.add_argument('--box', type=float, nargs=6, required=True, metavar=('X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2'))
    p.add_argument('--name', required=True)
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_extract)
    p = sub.add_parser('place', help='move and turn a prefab')
    p.add_argument('--prefab', required=True)
    p.add_argument('--at', type=float, nargs=3, required=True, metavar=('X', 'Y', 'Z'))
    p.add_argument('--yaw', type=float, default=0.0)
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_place)
    return ap


def main(argv=None):
    args = make_parser().parse_args(argv)
    try:
        if args.cmd == 'build':
            cmd_build(args)
        elif args.cmd == 'place':
            cmd_place(args)
        else:
            w = World(args.db)
            args.fn(w, args)
    except WorldError as e:
        print('iw7_world: error: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
