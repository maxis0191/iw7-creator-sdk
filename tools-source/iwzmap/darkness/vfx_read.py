"""Reader/patcher for ZoneTool IW7 binary particle systems (.iw7VFX, assetmanager dump format).

Format (zonetool utils/io/assetmanager.hpp): a token stream. Each token starts with a type byte:
  6 STRING  : existing u8, then NUL-terminated text
  7 ASSET   : existing u8, then NUL-terminated asset name
  8 ARRAY   : existing u8, u32 count, count * sizeof(T) raw bytes
  9 OFFSET  : u32 index, u32 array_index (reference to an earlier array/string)
Order follows zonetool iw7/assets/particle_system.cpp vfx::binary::parse.

Usage: python -I vfx_read.py <file.iw7VFX|dir> [--spot|--omni] [--json out.json]
"""
import struct, sys, os, json

SIZES = dict(system=0x80, emitter=144, state=32, group=16, module=160, linked=32, cp=16, input=48, mesh=16)
CURVES = {0x4: 2, 0x6: 4, 0x16: 1, 0x20: 8, 0x22: 2, 0x23: 2, 0x26: 2, 0x27: 2, 0x2A: 6, 0x2B: 2, 0x2C: 6,
          0x2D: 6, 0x2F: 6}
LINKED = {0x2, 0x5, 0x8, 0x9, 0xA, 0xC, 0xF, 0x14, 0x15, 0x1A, 0x1D, 0x28, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35}
NAMES = ["INIT_ATLAS", "INIT_ATTRIBUTES", "INIT_BEAM", "INIT_CAMERA_OFFSET", "INIT_CLOUD", "INIT_DECAL",
         "INIT_FLARE", "INIT_GEO_TRAIL", "INIT_LIGHT_OMNI", "INIT_LIGHT_SPOT", "INIT_MATERIAL",
         "INIT_MIRROR_TEXTURE", "INIT_MODEL", "INIT_OCCLUSION_QUERY", "INIT_ORIENTED_SPRITE", "INIT_PARTICLE_SIM",
         "INIT_PLAYER_FACING", "INIT_RELATIVE_VELOCITY", "INIT_ROTATION", "INIT_ROTATION_3D", "INIT_RUNNER",
         "INIT_SOUND", "INIT_SPAWN", "INIT_SPAWN_SHAPE_BOX", "INIT_SPAWN_SHAPE_CYLINDER",
         "INIT_SPAWN_SHAPE_ELLIPSOID", "INIT_SPAWN_SHAPE_MESH", "INIT_SPAWN_SHAPE_SPHERE", "INIT_TAIL",
         "INIT_VECTOR_FIELD", "INIT_VOLUMETRIC", "ATTRACTOR", "COLOR_GRAPH", "COLOR_LERP", "EMISSION_GRAPH",
         "EMISSIVE_GRAPH", "FORCE", "GRAVITY", "INTENSITY_GRAPH", "PARENT_VELOCITY_GRAPH", "PHYSICS_LIGHT",
         "PHYSICS_RAY_CAST", "POSITION_GRAPH", "ROTATION_GRAPH", "ROTATION_GRAPH_3D", "SIZE_GRAPH", "SIZE_LERP",
         "VELOCITY_GRAPH", "TEST_AGE", "TEST_BIRTH", "TEST_DEATH", "TEST_GRAVITY", "TEST_IMPACT", "TEST_POS"]
ELEM = ["BILLBOARD_SPRITE", "BEAM", "CLOUD", "SPARK_CLOUD", "DECAL", "FLARE", "GEO_TRAIL", "LIGHT_OMNI",
        "LIGHT_SPOT", "MODEL", "ORIENTED_SPRITE", "PARTICLE_SIM", "TAIL", "VECTOR_FIELD", "VOLUMETRIC"]
SPOT_FIELDS = ["fovOuter", "fovInner", "bulbRadius", "bulbLength", "brightness", "unk1", "intensityUV",
               "intensityIR", "shadowNearPlane", "toneMappingScaleFactor", "shadowSoftness", "shadowBias",
               "shadowArea"]
OMNI_FIELDS = ["tonemappingScaleFactor", "intensityIR", "disableVolumetric_exponent_raw"]


class R:
    def __init__(s, d):
        s.d = d; s.p = 0; s.arrays = []

    def u8(s):
        v = s.d[s.p]; s.p += 1; return v

    def u32(s):
        v = struct.unpack_from('<I', s.d, s.p)[0]; s.p += 4; return v

    def cstr(s):
        e = s.d.index(b'\0', s.p); v = s.d[s.p:e].decode('latin1'); s.p = e + 1; return v

    def array(s, size):
        t = s.u8()
        if t == 9:
            i, ai = s.u32(), s.u32(); off, cnt = s.arrays[i]
            return (off + ai * size if off is not None else None, None)
        assert t == 8, ('array token', t, s.p)
        if not s.u8():
            return (None, 0)
        n = s.u32(); off = s.p; s.p += n * size; s.arrays.append((off, n)); return (off, n)

    def string(s):
        t = s.u8()
        if t == 9:
            s.p += 8; return '<ref>'
        assert t in (6, 7), ('string token', t, s.p)
        if not s.u8():
            return None
        v = s.cstr(); s.arrays.append((None, 0)); return v


def curves(r, n):
    out = []
    for _ in range(n):
        off, cnt = r.array(SIZES['cp'])
        pts = [tuple(round(x, 4) for x in struct.unpack_from('<ff', r.d, off + 16 * k)) for k in range(cnt or 0)] \
            if off is not None else []
        out.append(pts)
    return out


def module(r, off):
    d = r.d
    mt = struct.unpack_from('<H', d, off)[0]
    m = {'type': NAMES[mt] if mt < len(NAMES) else mt, 'off': off}
    data = off + 16
    if mt == 9:
        vals = struct.unpack_from('<13f4B', d, data + 8)
        m.update({k: round(v, 4) for k, v in zip(SPOT_FIELDS, vals[:13])})
        m.update(disableVolumetric=vals[13], disableShadowMap=vals[14], disableDynamicShadows=vals[15],
                 exponent=vals[16], data_off=data)
    if mt == 8:
        vals = struct.unpack_from('<2f', d, data + 8)
        m.update({k: round(v, 4) for k, v in zip(OMNI_FIELDS, vals)}); m['data_off'] = data
    if mt == 0x1:  # INIT_ATTRIBUTES: size/colour/velocity min/max float4 at +16
        f = struct.unpack_from('<24f', d, data + 16)
        m.update(sizeMin=f[0:4], sizeMax=f[4:8], colorMin=f[8:12], colorMax=f[12:16], velMin=f[16:20], velMax=f[20:24],
                 attr_off=data + 16)
    if mt == 0x21:  # COLOR_LERP begin/end float4 at +16
        f = struct.unpack_from('<8f', d, data + 16); m.update(colorBegin=f[0:4], colorEnd=f[4:8], lerp_off=data + 16)
    if mt == 0x2D:  # SIZE_GRAPH sizeBegin/sizeEnd after 6 curves
        f = struct.unpack_from('<8f', d, data + 16 + 96); m.update(sizeBegin=f[0:4], sizeEnd=f[4:8], sg_off=data + 112)
    if mt in LINKED:
        loff, cnt = r.array(SIZES['linked'])
        names = []
        for _ in range(cnt or 0):
            if mt == 0x5:
                names += [r.string(), r.string(), r.string()]
            elif mt == 0x28:
                names += [r.string(), r.string()]
            else:
                names.append(r.string())
        m['assets'] = names
        if mt == 0x1A:
            r.array(SIZES['mesh'])
    if mt in CURVES:
        m['curves'] = curves(r, CURVES[mt])
        # ParticleCurveDef {ptr, int numControlPoints, float scale} (16 bytes) after the 8-byte ParticleModule header
        hdr = data + 16  # every graph module: 8-byte header, flag byte(s), curves 16-aligned
        m['curve_hdr'] = hdr
        m['scales'] = [round(struct.unpack_from('<f', d, hdr + 16 * k + 12)[0], 4) for k in range(CURVES[mt])]
    return m


def parse(path):
    d = open(path, 'rb').read(); r = R(d)
    soff, _ = r.array(SIZES['system'])
    name = r.string()
    nemit = struct.unpack_from('<i', d, soff + 28)[0]
    sysd = {'name': name, 'file': path, 'emitters': [], 'sys_off': soff}
    eoff, _ = r.array(SIZES['emitter'])
    for e in range(nemit):
        eo = eoff + e * SIZES['emitter']
        nst = struct.unpack_from('<i', d, eo + 8)[0]
        em = {'index': e, 'off': eo, 'states': [],
              'spawnRate': struct.unpack_from('<2f', d, eo + 12), 'life': struct.unpack_from('<2f', d, eo + 20),
              'delay': struct.unpack_from('<2f', d, eo + 28), 'countMax': struct.unpack_from('<I', d, eo + 36)[0],
              'emitterLife': struct.unpack_from('<2f', d, eo + 48)}
        stoff, _ = r.array(SIZES['state'])
        for s in range(nst):
            so = stoff + s * SIZES['state']
            et = struct.unpack_from('<I', d, so + 8)[0]
            st = {'element': ELEM[et] if et < len(ELEM) else et, 'groups': []}
            goff, _ = r.array(SIZES['group'])
            for g in range(3):
                go = goff + g * SIZES['group']
                nm = struct.unpack_from('<i', d, go + 8)[0]
                moff, _ = r.array(SIZES['module'])
                st['groups'].append([module(r, moff + k * SIZES['module']) for k in range(nm)])
            em['states'].append(st)
        curves(r, 1)  # fadeCurveDef
        sysd['emitters'].append(em)
    r.array(SIZES['input'])
    sysd['consumed'] = r.p; sysd['size'] = len(d)
    return sysd


def walk(p):
    if os.path.isfile(p):
        yield p; return
    for dp, dn, fn in os.walk(p):
        for f in fn:
            if f.endswith('.iw7VFX'):
                yield os.path.join(dp, f)


def light_states(s):
    for em in s['emitters']:
        for st in em['states']:
            if st['element'] in ('LIGHT_SPOT', 'LIGHT_OMNI'):
                yield em, st


if __name__ == '__main__':
    args = sys.argv[1:]
    spot = '--spot' in args; omni = '--omni' in args
    js = args[args.index('--json') + 1] if '--json' in args else None
    paths = [a for a in args if not a.startswith('--') and a != js]
    out = []; bad = []
    for root in paths:
        for f in walk(root):
            try:
                s = parse(f)
            except Exception as ex:
                bad.append((f, repr(ex))); continue
            types = {st['element'] for em in s['emitters'] for st in em['states']}
            if spot and 'LIGHT_SPOT' not in types: continue
            if omni and 'LIGHT_OMNI' not in types: continue
            out.append(s)
    for s in out:
        print(s['name'], 'ok' if s['consumed'] == s['size'] else 'PARTIAL %d/%d' % (s['consumed'], s['size']))
        for em, st in light_states(s):
            print('  emitter', em['index'], st['element'], 'life', em['life'], 'emitterLife', em['emitterLife'],
                  'max', em['countMax'])
            for g in st['groups']:
                for m in g:
                    mm = {k: v for k, v in m.items() if k not in ('off', 'data_off', 'curve_hdr')}
                    print('    ', json.dumps(mm)[:500])
    print('files', len(out), 'unparsed', len(bad), file=sys.stderr)
    for b in bad[:5]:
        print('  unparsed', b, file=sys.stderr)
    if js:
        json.dump(out, open(js, 'w'), indent=1)
