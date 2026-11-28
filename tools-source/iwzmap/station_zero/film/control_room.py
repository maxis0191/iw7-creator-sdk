r"""control_room: a room of STOCK geometry, materials and props, unchanged, set into our map for the control experiment (worker C1, 28 Nov 2026).

The question (REVIEW-1, LIGHTING-GAP): do our frames lose to stock because of the ASSETS (box rooms, tiling textures) or because of the PIPELINE
(our probes, lightmap texel, vision, bake)? The control: cp_disco's east subway station lifted whole (Studio `prefab.lift`, box below, clipped
at the box, shipped materials, UVs, collision and static props), placed UNROTATED on an island of our map, lit by cp_disco's own light list
transcribed from the world database, built and baked by our pipeline, and photographed from the exact eyes of the stock reference frames
(C:\studio-data\sz\film\stockref\cp_disco\subway_east_*.json: eye = feet + 60, fov 80.69 solved from the engine's own projection points).

    build(m, mode='bounce')     adds layer `ctl_room` (prefab, lights, cameras; no zone); every id starts with `ctl_`
    mode 'bounce'   stock's way in our pipeline: every stock spot an engine light (row = the stock row) with its bounce baked (L1's W1 mode)
    mode 'baked'    our old way: the same lights, all baked (lightmap + light grid), no engine light

Light conversion (all 29 stock lights of the box are spots, `light_point_linear`):
  colour   stock colour / its peak channel
  intensity  peak / 27,000: a bounce light's engine row is the document intensity x 27,000 (Studio baselights.BOUNCE_ROW_PER_UNIT, measured
           by L1 against the same light baked), so the emitted row equals the stock row; the baked variant keeps the same document intensity
           (27,000 a unit is also the measured equivalence of an engine row and the baker's light)
  dir      minus the stock `dir`: the engine stores the direction TOWARD the light, Studio's `dir` is the beam (default (0, 0, -1))
  cone     acos of the stock cosHalfFov columns (half angles; the database's outer_deg / inner_deg are full angles)
  radius   the stock radius
  shadows  the stock canUseShadowMap (a shadow capable template slot and caster list; not engine verified in our compiler)
  not carried: isVolumetric (the compiler writes 0, iwzmap.cpp:1542), needsDynamicShadows, shadowSoftness / bias / area, bulb size,
           distanceFalloff, defName (the template slot's are kept)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import build as B  # noqa: E402
from studio import prefab as P  # noqa: E402

ZONE = 'cp_disco'
PREFAB = 'ctl_subway_east'
STOCK_BOX = [-150.0, 1950.0, 230.0, 1260.0, 3400.0, 760.0]     # both platforms, the track, the stairs' feet, the mezzanine edge
OFFSET = (-7850.0, -6750.0, -400.0)                          # stock -> document: a pure translation, inside the station's own bounds (the empty x gap between the Terminus and the base; z in the base's range): placed outside them (-13000, -7000, 0) the build's walk gate turned the base's own drop region (shallowest drop 40) from a warning into an error
BOUNCE_ROW_PER_UNIT = 27000.0
STOCKREF = r'C:\studio-data\sz\film\stockref\cp_disco'
POSES = ['subway_east_%d' % k for k in range(1, 9)]
EYE_HEIGHT = 60.0                                              # solved from the stock frames' projection points (346.12 - 286.12)
LAYER = 'ctl_room'


def to_doc(p):
    return [float(p[i]) + OFFSET[i] for i in range(3)]


def prefab_origin():
    """the lifted prefab's origin in stock coordinates: the centre of the box at its floor"""
    b = STOCK_BOX
    return [(b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0, b[2]]


def ensure_lift():
    """the prefab folder (lifted once; `prefab.lift` is about 5 s)"""
    path = P.prefab_path(PREFAB)
    if not os.path.isfile(os.path.join(path, 'prefab.json')):
        P.lift(ZONE, STOCK_BOX, name=PREFAB)
    return path


def stock_lights():
    """the stock lights of the lift box, in stock coordinates (the prefab keeps them relative to its origin)"""
    pre = json.load(open(os.path.join(P.prefab_path(PREFAB), 'prefab.json'), encoding='utf-8'))
    o = prefab_origin()
    out = []
    for L in pre['lights']:
        out.append(dict(L, world=[L['pos'][i] + o[i] for i in range(3)]))
    return out


def light_args(L, mode):
    c = L['color']
    peak = max(c)
    kw = dict(color=[round(v / peak, 4) for v in c], radius=float(L['radius']), intensity=round(peak / BOUNCE_ROW_PER_UNIT, 5), group='emergency')
    if L['type'] == 2:
        d = [-v for v in L['dir']]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        kw.update(type='spot', dir=[round(v / n, 5) for v in d],
                  inner=round(math.degrees(math.acos(max(-1.0, min(1.0, L['cosHalfFovInner'])))), 2),
                  outer=round(math.degrees(math.acos(max(-1.0, min(1.0, L['cosHalfFovOuter'])))), 2))
    else:
        kw['type'] = 'omni'
    if mode == 'bounce':
        kw['bake'] = 'bounce'
        if L.get('canUseShadowMap'):
            kw['shadows'] = True
    elif mode != 'baked':
        raise ValueError('control_room: mode %r is not bounce or baked' % mode)
    return kw


def stock_pose(name):
    """eye (document frame), yaw, pitch of a stock reference frame; the eye is the sidecar's feet + EYE_HEIGHT"""
    d = json.load(open(os.path.join(STOCKREF, name + '.json'), encoding='utf-8'))
    f = d['feet']
    return to_doc([f[0], f[1], f[2] + EYE_HEIGHT]), float(d['yaw']), float(d['pitch'])


PROBE_RGB_UP = (0.70, 0.65, 0.55, 0.60)                         # a room row's ambient colour and up factor, near the base's rooms (probes.txt)


def build(m, mode='bounce', probe_room=True):
    ensure_lift()
    m.use(LAYER)
    at = to_doc(prefab_origin())
    B.prefab(m, PREFAB, at=at, yaw=0.0, openings='keep', props=True, lights=False, id='ctl_prefab')
    # No zone: the room is a photograph set, not a play space. A lifted prefab makes no navigation cells on a lattice base (studio/based.py
    # _nav_lattice takes floor, room, stair and mesh objects as regions); with an island zone `check` refuses it (ISLAND_NO_NAV), and a
    # collision-only floor strip as a seed gave 141 navigation areas whose 925 cells were all dropped as unreachable. Nothing a frame shows
    # depends on navigation or zones; the bake and the lights do not read them.
    zb = None
    # ... and so the room was in no probe room: no reflection probe volume (R2, 28 Nov 2026: 10.8 % of the control build's drawn area, the whole room;
    # its floors and vaults drew black). A probe room of the box, no zone (Studio settings.build.probe_rooms; a Studio without it ignores the key)
    if probe_room:
        b = STOCK_BOX
        lo, hi = to_doc(b[:3]), to_doc(b[3:])
        m.settings.setdefault('build', {}).setdefault('probe_rooms', []).append(lo + hi + list(PROBE_RGB_UP))
    rows = []
    for k, L in enumerate(stock_lights()):
        kw = light_args(L, mode)
        B.light(m, to_doc(L['world']), id='ctl_light_%02d' % k, **kw)
        rows.append({'id': 'ctl_light_%02d' % k, 'stock_pos': [round(v, 1) for v in L['world']], 'stock_peak': round(max(L['color']), 1), **kw})
    for name in POSES:
        eye, yaw, pitch = stock_pose(name)
        B.camera(m, 'ctl_' + name, eye, yaw, pitch=pitch, id='ctl_cam_' + name.split('_')[-1])
    return {'layer': LAYER, 'prefab_at': at, 'zone': zb, 'lights': rows, 'cameras': ['ctl_' + n for n in POSES], 'mode': mode}
