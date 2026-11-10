"""A tiny synthetic world written with the asset tool's dump conventions, for the tests.

This is an independent writer: it follows assetmanager::dumper (typed records, repeats of an earlier pointer
as type 9 + entry index + array index), not the reader's code. The struct layout engine of the reader is
reused only to place fields inside the fixed-size world structures.
"""
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import iw7_dump as D  # noqa: E402


def put(path, data, mode='wb'):
    kw = {} if 'b' in mode else {'newline': chr(10)}
    with open(path, mode, **kw) as f:
        f.write(data)


def get(path, mode='rb'):
    with open(path, mode) as f:
        return f.read()


class Dumper:
    """Mirror of assetmanager::dumper. Pointer identity is modelled by a hashable key."""

    def __init__(self):
        self.out = bytearray()
        self.entries = []  # (key, count)
        self.seen = {}

    def _repeat(self, idx, aidx):
        self.out += struct.pack('<BII', 9, idx, aidx)

    def array(self, key, data, count, elem):
        if key is not None and key in self.seen:
            self._repeat(self.seen[key], 0)
            return
        if not data or not count:
            self.out += struct.pack('<BB', 8, 0)
            return
        assert len(data) == count * elem, (key, len(data), count, elem)
        if key is not None:
            self.seen[key] = len(self.entries)
        self.entries.append((key, count))
        self.out += struct.pack('<BBI', 8, 1, count) + bytes(data)

    def absent(self):
        self.out += struct.pack('<BB', 8, 0)

    def string(self, text):
        if text is None:
            self.out += struct.pack('<BB', 6, 0)
            return
        key = ('s', text)
        if key in self.seen:
            self._repeat(self.seen[key], 0)
            return
        self.seen[key] = len(self.entries)
        self.entries.append((key, 1))
        self.out += struct.pack('<BB', 6, 1) + text.encode('latin-1') + b'\0'

    def asset(self, name):
        if not name:
            self.out += struct.pack('<BB', 7, 0)
            return
        key = ('a', name)
        if key in self.seen:
            self._repeat(self.seen[key], 0)
            return
        self.seen[key] = len(self.entries)
        self.entries.append((key, 1))
        self.out += struct.pack('<BB', 7, 1) + name.encode('latin-1') + b'\0'


def pack_unit(v):
    q = [max(0, min(1023, int(round((c + 1.0) * 511.5)))) for c in v]
    return q[0] | q[1] << 10 | q[2] << 20 | 3 << 30


def vertex(p, n, uv, lm):
    return struct.pack('<3ffI2f2fII', p[0], p[1], p[2], 1.0, 0xFFFFFFFF, uv[0], uv[1], lm[0], lm[1], pack_unit(n), pack_unit((1, 0, 0)))


def set_fields(layout_name, **fields):
    lay = D.layout(layout_name)
    buf = bytearray(lay.size)
    for path, v in fields.items():
        path = re.sub(r'__(\d+)', r'[\g<1>]', path).replace('__', '.')
        off, ch = lay.flat[path]
        struct.pack_into('<' + ch, buf, off, v)
    return bytes(buf)


# the world: three surfaces in one vertex zone (12 vertices)
#   surface 0 floor   x 0..100 y 0..100 z 0, verts 0-3 of an 8 vertex block, 2 triangles
#   surface 1 wall    x 0..100 y 0 z 0..100, verts 4-7 of the same block, 2 triangles (one half sticks out of low boxes)
#   surface 2 far     x 1000..1100 y 1000 z 0, own block (verts 8-11)
def _quad(p0, p1, p2, p3, n):
    return [vertex(p0, n, (0, 0), (0, 0)), vertex(p1, n, (1, 0), (1, 0)), vertex(p2, n, (1, 1), (1, 1)), vertex(p3, n, (0, 1), (0, 1))]


VERTS = (_quad((0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0), (0, 0, 1)) +
         _quad((0, 0, 0), (100, 0, 0), (100, 0, 100), (0, 0, 100), (0, -1, 0)) +
         _quad((1000, 1000, 0), (1100, 1000, 0), (1100, 1000, 100), (1000, 1000, 100), (0, -1, 0)))
# surface i: (material, firstVertex, vertexCount, indices relative to firstVertex)
SURFACES = [('mat_floor', 0, 8, [0, 1, 2, 0, 2, 3]),
            ('mat_wall', 0, 8, [4, 5, 6, 4, 6, 7]),
            ('mat_floor', 8, 4, [0, 1, 2, 0, 2, 3])]
# props: (model, origin, pitch, yaw, roll, scale)
PROPS = [('model_a', (10, 10, 0), 0, 0, 0, 1.0),
         ('model_a', (50, 20, 0), 0, 90, 0, 1.0),
         ('model_b', (90, 90, 10), 30, 45, 20, 2.0),
         ('model_a', (1000, 1000, 0), 0, 0, 0, 1.0)]
LIGHTS = [{'type': 3, 'origin': [20.0, 20.0, 50.0], 'radius': 300.0, 'defName': 'light_omni',
           'dir': [0.0, 0.0, -1.0], 'color': [1.0, 0.5, 0.25]},
          {'type': 2, 'origin': [1050.0, 1000.0, 50.0], 'radius': 100.0, 'defName': 'light_spot',
           'dir': [1.0, 0.0, 0.0], 'color': [0.5, 0.5, 0.5]}]
ENTS = ('{\n157 "worldspawn"\n337 "1"\n}\n'
        '{\n157 "script_struct"\n822 "spawn"\n543 "50 50 0"\n65 "0 0 0"\n}\n'
        '{\n157 "script_model"\n497 "model_a"\n543 "1000 1000 0"\n65 "0 90 0"\n}\n')


def axis_for(p, y, r):
    rad = 3.141592653589793 / 180.0
    import math
    sp, cp, sy, cy, sr, cr = math.sin(p * rad), math.cos(p * rad), math.sin(y * rad), math.cos(y * rad), math.sin(r * rad), math.cos(r * rad)
    f = (cp * cy, cp * sy, -sp)
    rt = (-sr * sp * cy + cr * sy, -sr * sp * sy - cr * cy, -sr * cp)
    u = (cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp)
    return [f, tuple(-c for c in rt), u]


def gfxmap_bytes(surface_count=None, index_count=None, header_patch=None):
    W = D.layout('GfxWorld')
    nS, nP = len(SURFACES), len(PROPS)
    indices = [i for s in SURFACES for i in s[3]]
    fields = {'bspVersion': 159, 'surfaceCount': nS if surface_count is None else surface_count, 'primaryLightCount': len(LIGHTS),
              'draw__reflectionProbeData__reflectionProbeCount': 1, 'draw__lightMapCount': 1, 'draw__transientZoneCount': 1,
              'draw__indexCount': len(indices) if index_count is None else index_count, 'modelCount': 1,
              'dpvs__smodelCount': nP, 'dpvs__staticSurfaceCount': 0, 'dpvs__surfaceVisDataCount': 0}
    for path, v in (header_patch or {}).items():
        fields[path] = v
    d = Dumper()
    d.array(None, set_fields('GfxWorld', **fields), 1, W.size)
    d.string('synth')
    d.string('synth_base')
    for _ in range(5):              # skies, planes, nodes, cellTransientInfos, cells
        d.absent()
    probe = set_fields('GfxReflectionProbe', origin__0=1.0, origin__1=2.0, origin__2=3.0)
    d.array(None, probe, 1, 48)
    d.string('probe_a')
    d.absent()                      # probeInstances
    d.asset('*reflection_probe_array')
    for _ in range(3):              # relighting, gbuffer images, probe instances
        d.absent()
    d.absent()                      # lightgrid sample data
    d.absent()
    d.absent()                      # reindex element, packed lightmap
    d.asset('*ieslookup')
    d.absent()                      # decal volumes
    d.asset(None)
    d.asset(None)
    d.array(None, struct.pack('<Q', 1), 1, 8)
    d.asset('*lightmap0')
    for i in range(32):
        d.asset('synth' if i == 0 else None)
    d.array(None, struct.pack('<%dH' % len(indices), *indices), len(indices), 2)
    d.absent()                      # volumetrics
    for _ in range(19):             # 14 light grid arrays, frustum lights, light view frustums, voxel trees, heightfields, light lists
        d.absent()
    d.array(None, set_fields('GfxBrushModel', radius=50.0, startSurfIndex=0, surfaceCount=2, bounds__mid__0=50.0, bounds__half__0=50.0), 1, 60)
    d.absent()                      # material memory
    for _ in range(4):
        d.asset(None)
    for _ in range(4):              # shadow geometry, light region, light aabb nodes, light aabb lights
        d.absent()
    d.array(None, struct.pack('<%dI' % (nP + 1), *range(nP + 1)), nP + 1, 4)       # lodData
    d.absent()                      # sortedSurfIndex
    SI = D.layout('GfxStaticModelInst')
    insts = b''
    SD = D.layout('GfxStaticModelDrawInst')
    draws = b''
    for model, o, p, y, r, sc in PROPS:
        ax = axis_for(p, y, r)
        insts += set_fields('GfxStaticModelInst', bounds__mid__0=o[0], bounds__mid__1=o[1], bounds__mid__2=o[2], bounds__half__0=5.0,
                            bounds__half__1=5.0, bounds__half__2=5.0, lightingOrigin__0=o[0], lightingOrigin__1=o[1], lightingOrigin__2=o[2])
        f = {'origin__0': o[0], 'origin__1': o[1], 'origin__2': o[2], 'scale': sc, 'cullDist': 4000, 'flags': 0x66,
             'lmIndex': -1, 'transientZone': 0}
        for a in range(3):
            for b in range(3):
                f['axis__%d' % (3 * a + b)] = ax[a][b]
        draws += set_fields('GfxStaticModelDrawInst', **f)
    d.array(None, insts, nP, SI.size)
    surf = b''
    base = 0
    for k, (m, fv, vc, idx) in enumerate(SURFACES):
        surf += set_fields('GfxSurface', tris__firstVertex=fv, tris__vertexCount=vc, tris__triCount=len(idx) // 3, tris__baseIndex=base,
                           lightmapIndex=0, flags=1, sortKey=k, transientZone=0)
        base += len(idx)
    d.array(None, surf, nS, 48)
    for m, *_ in SURFACES:
        d.asset(m)
    sb = b''
    for k in range(nS):
        sb += struct.pack('<6f3I', 50, 50, 0, 50, 50, 50, 0, 0, 0)
    d.array(None, sb, nS, 36)
    d.array(None, draws, nP, SD.size)
    for model, *_ in PROPS:
        d.asset(model)
        d.absent()                  # lighting values
    d.absent()                      # surfaceCastsSunShadow
    d.array(None, struct.pack('<%dH' % nP, *range(nP)), nP, 2)
    for _ in range(5):              # hero lights, umbra gates, tome, gates2, tome2
        d.absent()
    d.absent()                      # umbraUnkData
    return bytes(d.out)


def zone_bytes():
    d = Dumper()
    d.array(None, set_fields('GfxWorldTransientZone', vertexCount=len(VERTS), cellCount=0), 1, 80)
    d.string('synth')
    d.array(None, b''.join(VERTS), len(VERTS), 44)
    d.absent()
    d.absent()
    d.absent()
    return bytes(d.out)


def commap_json():
    out = {'isInUse': 1, 'useForwardPlus': 1, 'bakeQuality': 3, 'primaryLight': []}
    for i, L in enumerate(LIGHTS):
        item = {'primaryLightIndex': i, 'type': L['type'], 'canUseShadowMap': 1, 'needsDynamicShadows': 0, 'isVolumetric': 0,
                'exponent': 0, 'transientZoneList': 0, 'entityId': 100 + i, 'uvIntensity': 1.0, 'irIntensity': 0.0,
                'color': L['color'], 'dir': L['dir'], 'up': [0.0, 1.0, 0.0], 'origin': L['origin'], 'radius': L['radius'],
                'fadeOffsetRt': [0.0, 0.0], 'bulbRadius': 0.0, 'bulbLength': [0.0, 0.0, 0.0], 'cosHalfFovOuter': 0.5,
                'cosHalfFovInner': 0.8, 'shadowSoftness': 1.0, 'shadowBias': 0.0, 'shadowArea': 0.0, 'distanceFalloff': 0.0,
                'rotationLimit': 0.0, 'translationLimit': 0.0, 'defName': L['defName']}
        out['primaryLight'].append(item)
    out['primaryLightEnv'] = []
    return json.dumps(out, indent=4)


def write_world(root, name='synth', **kw):
    """Write the dump folder `root` (maps/, transient_zones/, xmodel/, materials/) and return its path."""
    os.makedirs(os.path.join(root, 'maps', 'x'), exist_ok=True)
    os.makedirs(os.path.join(root, 'transient_zones'), exist_ok=True)
    os.makedirs(os.path.join(root, 'xmodel'), exist_ok=True)
    os.makedirs(os.path.join(root, 'materials'), exist_ok=True)
    stem = os.path.join(root, 'maps', 'x', name + '.d3dbsp')
    put(stem + '.gfxmap', gfxmap_bytes(**kw))
    put(os.path.join(root, 'transient_zones', 'synth.gfxmap_tr'), zone_bytes())
    put(stem + '.commap.json', commap_json(), 'w')
    put(stem + '.ents', ENTS, 'w')
    put(stem + '.navmesh', b'nav')
    for m in ('model_a', 'model_b'):
        put(os.path.join(root, 'xmodel', m + '.xmb'), b'x')
    for m in ('mat_floor', 'mat_wall'):
        put(os.path.join(root, 'materials', m + '.json'), '{}', 'w')
    return root
