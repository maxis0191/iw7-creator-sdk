"""Station Zero v2 (stage 2 level design): a 1980s metro station built from textured brushes -> iwzcompile sources.

usage: station_zero2.py <template dump dir (cp_zmb)> <output source dir>

Writes world.bin, colmap.hkx, navgraph.bin, ents.txt, triggers.txt, scriptables.txt, lighting.txt, layout.json,
cp_iwz.gsc (level script with the generated door/zone tables), custom_materials.json (for sz2_assemble.py) and
plan.json (geometry/nav summary for the offline checks). Environment:
  IWZ_GALLERY=1        add the material / lightmap texel gallery room (engine verification of materials and texels)
  IWZ_LM_TABLE=<json>  measured texel table (zone -> tone -> [u, v]); default lm_table.json next to this file
  IWZ_VOLUME_MODEL=<n> use one template trigger model for every zone volume instead of generated boxes
Data tables (kept separate so other tools plug in): ZONES, OPENINGS (doors), SPAWNERS, STARTS, INTERACTIONS,
PROPS (static model kit, empty until the asset kit lands), LIGHTS (primary lights, for the light compiler),
SIGNS, VIEWS (capture set), WALK (walk-test path).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapgen, hkcm_write
import brushkit as bk
import sz2_materials as MT
import sz2_art_hooks as ART_HOOKS
ART_HOOKS.register()       # art drop-ins (sz2_art_hooks.py): present images become materials, missing ones change nothing

HERE = os.path.dirname(os.path.abspath(__file__))
GALLERY = os.environ.get('IWZ_GALLERY') == '1'

# ============================================================================ lighting texels
# measured texels of the template lightmap atlas (engine frames); tones: bright/mid/dark per zone
LM_DEFAULT = {
    'neutral': (0.8018, 0.5645), 'low': (0.3037, 0.8965), 'warm': (0.8975, 0.3965), 'teal': (0.7744, 0.5605),
}
ZONE_TONE = {   # zone -> texel family for (bright, mid, dark) until the measured table exists
    'ticket_hall': ('neutral', 'neutral', 'low'), 'stair_a': ('neutral', 'neutral', 'low'),
    'platform_a': ('teal', 'teal', 'low'), 'maint_corridor': ('warm', 'warm', 'low'),
    'generator_room': ('warm', 'warm', 'low'), 'control_room': ('warm', 'low', 'low'),
    'service_tunnel': ('low', 'low', 'low'), 'platform_b': ('neutral', 'low', 'low'),
    'stair_b': ('neutral', 'low', 'low'), 'gallery': ('neutral', 'neutral', 'neutral'),
}
LM_TABLE = {}
_lmt = os.environ.get('IWZ_LM_TABLE') or os.path.join(HERE, 'sz2_lm_table.json')
if os.path.isfile(_lmt):
    LM_TABLE = json.load(open(_lmt))


def lm(zone, tone):
    if isinstance(tone, tuple):
        return tone
    t = LM_TABLE.get(zone, {}).get(tone)
    if t:
        return tuple(t)
    fam = ZONE_TONE.get(zone, ('neutral', 'neutral', 'low'))
    idx = {'bright': 0, 'mid': 1, 'dark': 2}.get(tone, 1)
    return LM_DEFAULT[fam[idx]]


B = bk.Builder(MT.MATERIALS, lm)
WALL_T = 16       # wall thickness between neighbouring spaces (door reveals)
CELL = 32

# ============================================================================ zones (script areas)
# name: volume box (x0, y0, z0, x1, y1, z1), light grid ambient (r, g, b, up) for models, capture tint target
ZONES = {
    'ticket_hall':    {'box': (-1200, 3200, -16, 400, 4600, 336), 'probe': (1.00, 1.04, 1.12, 0.6)},
    'stair_a':        {'box': (-800, 2400, -336, -400, 3200, 304), 'probe': (0.92, 0.96, 1.04, 0.6)},
    'platform_a':     {'box': (-2400, 1200, -400, 2400, 2400, 16), 'probe': (0.80, 0.98, 1.10, 0.6)},
    'maint_corridor': {'box': (2400, 1680, -336, 3200, 2400, -80), 'probe': (1.20, 0.86, 0.50, 0.6)},
    'generator_room': {'box': (2600, 2400, -336, 3800, 3200, 48), 'probe': (1.30, 0.92, 0.52, 0.7)},
    'control_room':   {'box': (2600, 3200, -336, 3600, 4160, -16), 'probe': (1.10, 0.30, 0.26, 0.5)},
    'service_tunnel': {'box': (-3600, 1200, -400, -2400, 2600, -80), 'probe': (0.70, 0.62, 0.52, 0.5)},
    'platform_b':     {'box': (-3600, 2600, -400, -2064, 3400, -16), 'probe': (0.86, 0.94, 0.80, 0.6)},
    'stair_b':        {'box': (-2064, 3104, -400, -1200, 3400, 304), 'probe': (0.88, 0.92, 0.96, 0.6)},
}
INITIAL_ZONES = ['ticket_hall']
# zones joined without a door: activating one activates the other (level script) and they are adjacent
ZONE_LINKS = [('stair_a', 'platform_a'), ('maint_corridor', 'generator_room'), ('service_tunnel', 'platform_b'),
              ('platform_b', 'stair_b')]

# ============================================================================ openings
# axis 'x': opening in a wall running along x (wall plane y = const); 'y': wall along y (plane x = const)
# walls: space -> its wall plane coordinate; a, b: span along the wall; z0, z1: sill and top
# kind: door (debris purchase, frame, reveal), arch (free passage with frame and reveal), open (no wall at all)
OPENINGS = [
    {'name': 'd_hall_stair_a', 'kind': 'door', 'axis': 'x', 'walls': {'hall': 3200, 'stair_a': 3184},
     'a': -696, 'b': -504, 'z0': 0, 'z1': 224, 'cost': 750, 'zones': ('ticket_hall', 'stair_a'),
     'scriptable': 'pf7_auto209', 'sign': 'sign_to_platforms'},
    {'name': 'a_stair_a_platform', 'kind': 'arch', 'axis': 'x', 'walls': {'stair_a': 2416, 'platform_deck': 2400},
     'a': -784, 'b': -416, 'z0': -320, 'z1': -64},
    {'name': 'd_platform_corridor', 'kind': 'door', 'axis': 'y', 'walls': {'platform_deck': 2400, 'corridor_a': 2416},
     'a': 1704, 'b': 1896, 'z0': -320, 'z1': -112, 'cost': 1000, 'zones': ('platform_a', 'maint_corridor'),
     'scriptable': 'pf7_auto213', 'sign': 'sign_staff_only'},
    {'name': 'o_corridor_bend', 'kind': 'open', 'axis': 'x', 'walls': {'corridor_a': 1920, 'corridor_b': 1920},
     'a': 2976, 'b': 3184, 'z0': -320, 'z1': -96},
    {'name': 'a_corridor_generator', 'kind': 'arch', 'axis': 'x', 'walls': {'corridor_b': 2384, 'generator': 2400},
     'a': 2992, 'b': 3168, 'z0': -320, 'z1': -112},
    {'name': 'd_generator_control', 'kind': 'door', 'axis': 'x', 'walls': {'generator': 3184, 'control': 3200},
     'a': 3004, 'b': 3196, 'z0': -320, 'z1': -96, 'cost': 1250, 'zones': ('generator_room', 'control_room'),
     'scriptable': 'pf7_auto237', 'sign': 'sign_signal_control'},
    {'name': 'd_platform_tunnel', 'kind': 'door', 'axis': 'y', 'walls': {'pit': -2400, 'tunnel_a': -2416},
     'a': 1392, 'b': 1584, 'z0': -384, 'z1': -160, 'cost': 1000, 'zones': ('platform_a', 'service_tunnel'),
     'scriptable': 'pf7_auto238', 'sign': 'sign_to_old_station'},
    {'name': 'o_tunnel_bend', 'kind': 'open', 'axis': 'x', 'walls': {'tunnel_a': 1584, 'tunnel_b': 1584},
     'a': -3600, 'b': -3216, 'z0': -384, 'z1': -96},
    {'name': 'a_tunnel_platform_b', 'kind': 'arch', 'axis': 'x', 'walls': {'tunnel_b': 2584, 'platform_b': 2600},
     'a': -3536, 'b': -3264, 'z0': -384, 'z1': -128},
    {'name': 'a_platform_b_stair_b', 'kind': 'arch', 'axis': 'y', 'walls': {'platform_b': -2064, 'stair_b': -2048},
     'a': 3120, 'b': 3384, 'z0': -384, 'z1': -128},
    {'name': 'd_stair_b_hall', 'kind': 'door', 'axis': 'y', 'walls': {'stair_b': -1216, 'hall': -1200},
     'a': 3216, 'b': 3392, 'z0': 0, 'z1': 224, 'cost': 750, 'zones': ('stair_b', 'ticket_hall'),
     'scriptable': 'pf7_auto243', 'sign': 'sign_to_old_station'},
    {'name': 'o_hall_street', 'kind': 'open', 'axis': 'x', 'walls': {'hall': 4400, 'street': 4400},
     'a': -304, 'b': 112, 'z0': 0, 'z1': 320},
    {'name': 'a_control_pap', 'kind': 'arch', 'axis': 'x', 'walls': {'control': 4000, 'pap_alcove': 4016},
     'a': 2976, 'b': 3232, 'z0': -320, 'z1': -136},
]
OP = {o['name']: o for o in OPENINGS}


def holes_for(space, axis, fixed):
    out = []
    for o in OPENINGS:
        if o['axis'] == axis and o['walls'].get(space) == fixed:
            if o['kind'] == 'open':
                out.append((o['a'], o['b'], -1e9, 1e9))
            else:
                out.append((o['a'], o['b'], o['z0'], o['z1']))
    return out


# ============================================================================ wall styles
def bands(style, zf, zc):
    """(z0, z1, material, protrusion) from floor to ceiling."""
    if style == 'metro':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 112, 'tile_charcoal', 0), (zf + 112, zf + 120, 'steel_trim', 1.5),
                (zf + 120, zc - 20, 'tile_white', 0), (zc - 20, zc, 'molding', 3)]
    if style == 'metro_cream':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 112, 'tile_green', 0), (zf + 112, zf + 120, 'steel_trim', 1.5),
                (zf + 120, zc - 20, 'tile_cream', 0), (zc - 20, zc, 'molding', 3)]
    if style == 'maint':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 96, 'panel_dark', 0), (zf + 96, zf + 102, 'beam_yellow', 1),
                (zf + 102, zc, 'conc_seam', 0)]
    if style == 'old':
        return [(zf, zf + 10, 'wood_trim', 2), (zf + 10, zf + 104, 'wood_green', 0), (zf + 104, zf + 112, 'wood_trim', 2),
                (zf + 112, zc - 18, 'brick_white', 0), (zc - 18, zc, 'molding', 2.5)]
    if style == 'tunnel':
        return [(zf, zf + 96, 'conc_dark', 0), (zf + 96, zf + 100, 'steel_trim', 1), (zf + 100, zc, 'conc_seam', 0)]
    if style == 'control_neutral':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 96, 'panel_dark', 0), (zf + 96, zf + 104, 'steel_trim', 1.5),
                (zf + 104, zc, 'panel_wall', 0)]
    if style == 'control':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 96, 'panel_dark_red', 0), (zf + 96, zf + 104, 'steel_trim', 1.5),
                (zf + 104, zc, 'panel_wall_red', 0)]
    if style == 'track':
        return [(zf, zf + 64, 'conc_dark', 0)] + bands('metro', zf + 64, zc)
    if style == 'brick':
        return [(zf, zc, 'brick_gray', 0)]
    if style == 'plain':
        return [(zf, zc, 'conc_wall', 0)]
    raise KeyError(style)


WELD = float(os.environ.get('IWZ_WELD', '1'))      # units of overlap at module joins (0 = off)


def wall(zone, space, axis, fixed, facing, s0, s1, zf, zc, style, frame='frame'):
    """Banded wall with the openings of `space` cut out; door frames around door/arch openings on this side."""
    holes = holes_for(space, axis, fixed)
    for za, zb, mat, pr in bands(style, zf, zc):
        if zb <= za:
            continue
        cut = [(a, b) for a, b, h0, h1 in holes if h0 < zb and h1 > za]
        pieces = [(p, q, za, zb) for p, q in bk.spans_minus(s0, s1, cut)]
        for a, b, h0, h1 in holes:
            if h0 < zb and h1 > za:
                if h1 < zb:
                    pieces.append((max(a, s0), min(b, s1), max(za, h1), zb))
                if h0 > za:
                    pieces.append((max(a, s0), min(b, s1), za, min(zb, h0)))
        for p, q, z0, z1 in pieces:
            if q - p < 0.5 or z1 - z0 < 0.5:
                continue
            vtop = z1 if mat.startswith('tile') else None
            if WELD:
                p, q = (p - WELD if p <= s0 + 0.01 else p), (q + WELD if q >= s1 - 0.01 else q)
                z0, z1 = (z0 - WELD if z0 <= zf + 0.01 else z0), (z1 + WELD if z1 >= zc - 0.01 else z1)
            if pr == 0:
                B.wall_plane(zone, axis, fixed, facing, p, q, z0, z1, mat, vtop=vtop)
            else:
                if axis == 'x':
                    B.slab_x(p, q, fixed, z0, z1, pr, mat, zone, facing, collide=False, skip=('bottom',) if z0 > zf + 1 else ('bottom',))
                    B.collision_quad([(p, fixed, z0), (q, fixed, z0), (q, fixed, z1), (p, fixed, z1)], n=(0, facing, 0))
                else:
                    B.slab_y(p, q, fixed, z0, z1, pr, mat, zone, facing, collide=False, skip=('bottom',))
                    B.collision_quad([(fixed, p, z0), (fixed, q, z0), (fixed, q, z1), (fixed, p, z1)], n=(facing, 0, 0))
    # frames on this side
    for o in OPENINGS:
        if o['axis'] != axis or o['walls'].get(space) != fixed or o['kind'] == 'open':
            continue
        fw, fd = 10, 4
        a, b, z0, z1 = o['a'], o['b'], o['z0'], o['z1']
        fm = 'frame' if o['kind'] == 'door' else 'steel_trim'
        if axis == 'x':
            B.slab_x(a - fw, a, fixed, z0, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)
            B.slab_x(b, b + fw, fixed, z0, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)
            B.slab_x(a, b, fixed, z1, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)
        else:
            B.slab_y(a - fw, a, fixed, z0, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)
            B.slab_y(b, b + fw, fixed, z0, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)
            B.slab_y(a, b, fixed, z1, z1 + fw, fd, fm, zone, facing, collide=False, nav=False)


def reveal(o, zone):
    """Door reveal through the wall thickness: jamb faces, soffit and threshold floor."""
    if o['kind'] == 'open':
        return
    p0, p1 = sorted(o['walls'].values())
    a, b, z0, z1 = o['a'], o['b'], o['z0'], o['z1']
    if p1 - p0 < 0.5:
        return
    if o['axis'] == 'x':
        B.quad('conc_floor', zone, [(a, p0, z0), (b, p0, z0), (b, p1, z0), (a, p1, z0)], n=(0, 0, 1))
        B.quad('conc_painted', zone, [(a, p1, z1), (b, p1, z1), (b, p0, z1), (a, p0, z1)], n=(0, 0, -1), tone='dark')
        B.quad('conc_painted', zone, [(a, p1, z0), (a, p0, z0), (a, p0, z1), (a, p1, z1)], n=(1, 0, 0))
        B.quad('conc_painted', zone, [(b, p0, z0), (b, p1, z0), (b, p1, z1), (b, p0, z1)], n=(-1, 0, 0))
    else:
        B.quad('conc_floor', zone, [(p0, a, z0), (p1, a, z0), (p1, b, z0), (p0, b, z0)], n=(0, 0, 1))
        B.quad('conc_painted', zone, [(p0, b, z1), (p1, b, z1), (p1, a, z1), (p0, a, z1)], n=(0, 0, -1), tone='dark')
        B.quad('conc_painted', zone, [(p0, a, z0), (p1, a, z0), (p1, a, z1), (p0, a, z1)], n=(0, 1, 0))
        B.quad('conc_painted', zone, [(p1, b, z0), (p0, b, z0), (p0, b, z1), (p1, b, z1)], n=(0, -1, 0))


def floor(zone, mat, x0, y0, x1, y1, z, tone='mid', collide=True):
    B.quad(mat, zone, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], n=(0, 0, 1), tone=tone, collide=collide)


def ceiling(zone, mat, x0, y0, x1, y1, z, tone='dark'):
    B.quad(mat, zone, [(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)], n=(0, 0, -1), tone=tone)


def room(zone, space, box, zf, zc, style, floor_mat, ceil_mat, skip=(), walls=None):
    """Flat room: floor, ceiling and the four banded walls (inward)."""
    x0, y0, x1, y1 = box
    floor(zone, floor_mat, x0, y0, x1, y1, zf)
    if ceil_mat:
        ceiling(zone, ceil_mat, x0, y0, x1, y1, zc)
    sides = walls or {'south': style, 'north': style, 'west': style, 'east': style}
    if 'south' not in skip: wall(zone, space, 'x', y0, +1, x0, x1, zf, zc, sides['south'])
    if 'north' not in skip: wall(zone, space, 'x', y1, -1, x0, x1, zf, zc, sides['north'])
    if 'west' not in skip: wall(zone, space, 'y', x0, +1, y0, y1, zf, zc, sides['west'])
    if 'east' not in skip: wall(zone, space, 'y', x1, -1, y0, y1, zf, zc, sides['east'])


# ============================================================================ walkable regions (nav)
# (name, zone, (x0, y0, x1, y1), z (number or callable (x, y) -> z), margins (w, s, e, n))
REGIONS = []
ADJ = set()


def region(name, zone, rect, z, margins=(16, 16, 16, 16)):
    REGIONS.append({'name': name, 'zone': zone, 'rect': rect, 'z': z, 'm': margins})
    return name


def adjacent(a, b):
    ADJ.add(frozenset((a, b)))


def portal(o):
    """Nav region through an opening: the cells crossing the wall gap, linked to both spaces."""
    p0, p1 = sorted(o['walls'].values())
    a, b = o['a'] + 16, o['b'] - 16
    z = o['z0']
    if o['axis'] == 'x':
        rect = (a, p0 - 8, b, p1 + 8)
    else:
        rect = (p0 - 8, a, p1 + 8, b)
    return region('portal:' + o['name'], o.get('portal_zone') or SPACE_ZONE[list(o['walls'])[0]], rect, z, (0, 0, 0, 0))


# space -> zone
SPACE_ZONE = {'hall': 'ticket_hall', 'street': 'ticket_hall', 'stair_a': 'stair_a', 'platform_deck': 'platform_a',
              'pit': 'platform_a', 'car': 'platform_a', 'corridor_a': 'maint_corridor', 'corridor_b': 'maint_corridor',
              'generator': 'generator_room', 'control': 'control_room', 'pap_alcove': 'control_room',
              'tunnel_a': 'service_tunnel', 'tunnel_b': 'service_tunnel', 'platform_b': 'platform_b', 'stair_b': 'stair_b',
              'well_w': 'platform_a', 'well_e': 'platform_a', 'recess': 'platform_a'}


# ============================================================================ helpers for details
STRIP_COUNT = {}
DIM_STRONG = {'maint_corridor', 'service_tunnel', 'generator_room', 'stair_b'}
POOL_STRIP, POOL_WALL = 288, 224          # g26: tighter pools (was 384 / 320)
DIM = os.environ.get('IWZ_DIM', '1') == '1'     # g25 mood pass: half the fluorescents are dead, in clusters


def strip_light(zone, x0, y0, x1, y1, z, mat='lamp_cool', depth=6, dead=False):
    """Ceiling fluorescent fitting: a steel housing with an emissive diffuser underneath (dead: dark diffuser, no light)."""
    k_ = STRIP_COUNT[zone] = STRIP_COUNT.get(zone, -1) + 1
    dimmed = DIM and not dead and mat in ('lamp_cool', 'lamp_warm') and (
        k_ % 3 in (1, 2) if zone in DIM_STRONG else (k_ % 3 == 1 if zone.startswith('stair') else k_ % 4 in (1, 2)))
    if dimmed:
        # keeps its layout light record (intensity 0, dead): the audio layout addresses fixtures by zone index
        LIGHTS.append({'zone': zone, 'origin': ((x0 + x1) / 2, (y0 + y1) / 2, z - depth - 4), 'type': 'omni',
                       'color': LIGHT_COLOR.get(mat, (1, 1, 1)), 'radius': 384, 'intensity': 0.0, 'fixture': mat, 'dead': True})
        dead = True
    if dead:
        mat = 'panel_dark'
    B.box((x0 - 3, y0 - 3, z - depth), (x1 + 3, y1 + 3, z), {'side': 'steel_trim', 'top': 'steel_trim'}, zone,
          collide=False, nav=False, skip=('bottom',))
    B.quad(mat, zone, [(x0, y1, z - depth - 0.5), (x1, y1, z - depth - 0.5), (x1, y0, z - depth - 0.5), (x0, y0, z - depth - 0.5)],
           n=(0, 0, -1), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], collide=False)
    if dead:
        return
    coloured = mat not in ('lamp_cool', 'lamp_warm', 'light_panel')
    LIGHTS.append({'zone': zone, 'origin': ((x0 + x1) / 2, (y0 + y1) / 2, z - depth - 4), 'type': 'omni',
                   'color': LIGHT_COLOR.get(mat, (1, 1, 1)), 'radius': 96 if coloured else POOL_STRIP,
                   'intensity': 0.5 if coloured else 1.0, 'fixture': mat})


def wall_lamp(zone, axis, fixed, facing, s, z, mat='lamp_warm', w=24, h=12):
    """Wall bulkhead lamp: emissive face on a short steel box."""
    if axis == 'x':
        B.slab_x(s - w / 2 - 3, s + w / 2 + 3, fixed, z - 3, z + h + 3, 5, 'steel_trim', zone, facing, collide=False, nav=False)
        y = fixed + facing * 5.5
        pts = [(s + w / 2 * facing, y, z), (s - w / 2 * facing, y, z), (s - w / 2 * facing, y, z + h), (s + w / 2 * facing, y, z + h)]
        B.quad(mat, zone, pts, n=(0, facing, 0), uvs=[(0, 1), (1, 1), (1, 0), (0, 0)], collide=False)
        o = (s, fixed + facing * 12, z + h / 2)
    else:
        B.slab_y(s - w / 2 - 3, s + w / 2 + 3, fixed, z - 3, z + h + 3, 5, 'steel_trim', zone, facing, collide=False, nav=False)
        x = fixed + facing * 5.5
        pts = [(x, s - w / 2 * facing, z), (x, s + w / 2 * facing, z), (x, s + w / 2 * facing, z + h), (x, s - w / 2 * facing, z + h)]
        B.quad(mat, zone, pts, n=(facing, 0, 0), uvs=[(0, 1), (1, 1), (1, 0), (0, 0)], collide=False)
        o = (fixed + facing * 12, s, z + h / 2)
    coloured = mat not in ('lamp_cool', 'lamp_warm', 'light_panel')
    LIGHTS.append({'zone': zone, 'origin': o, 'type': 'omni', 'color': LIGHT_COLOR.get(mat, (1, 1, 1)), 'radius': 96 if coloured else POOL_WALL,
                   'intensity': 0.5 if coloured else 1.0, 'fixture': mat})


def sign(zone, key, axis, fixed, facing, s, zc, width, height=None, frame=True, depth=1.5):
    """Custom image sign on its own quad in front of a wall, with a thin steel frame. s: centre along the wall."""
    if height is None:
        height = width / 4.0
    a, b, z0, z1 = s - width / 2, s + width / 2, zc - height / 2, zc + height / 2
    off = depth + 0.5
    if axis == 'x':
        y = fixed + facing * off
        # viewer-right along -x when facing +y, +x when facing -y
        if facing > 0:
            pts = [(b, y, z0), (a, y, z0), (a, y, z1), (b, y, z1)]
        else:
            pts = [(a, y, z0), (b, y, z0), (b, y, z1), (a, y, z1)]
        n = (0, facing, 0)
        if frame:
            B.slab_x(a - 4, b + 4, fixed, z0 - 4, z1 + 4, depth, 'steel_trim', zone, facing, collide=False, nav=False)
    else:
        x = fixed + facing * off
        if facing > 0:
            pts = [(x, a, z0), (x, b, z0), (x, b, z1), (x, a, z1)]
        else:
            pts = [(x, b, z0), (x, a, z0), (x, a, z1), (x, b, z1)]
        n = (facing, 0, 0)
        if frame:
            B.slab_y(a - 4, b + 4, fixed, z0 - 4, z1 + 4, depth, 'steel_trim', zone, facing, collide=False, nav=False)
    flip = os.environ.get('IWZ_SIGN_FLIP', '')
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]       # bottom-left, bottom-right, top-right, top-left (texture v down)
    if 'u' in flip: uv = [(1 - u, v) for u, v in uv]
    if 'v' in flip: uv = [(u, 1 - v) for u, v in uv]
    if key == 'poster_station_zero' and ART_HOOKS.key('poster_station_zero_v2'):
        key = ART_HOOKS.key('poster_station_zero_v2')
    B.quad(key, zone, pts, n=n, uvs=uv, collide=False)
    if frame and ART_HOOKS.key('sign_grime_overlay') and not ART_HOOKS.AGED_SIGNS:
        B.quad(ART_HOOKS.key('sign_grime_overlay'), zone, [tuple(c + nc * 0.2 for c, nc in zip(p_, n)) for p_ in pts], n=n, uvs=uv, collide=False)
    SIGNS.append({'zone': zone, 'image': key, 'center': ((a + b) / 2 if axis == 'x' else fixed, fixed if axis == 'x' else (a + b) / 2, zc),
                  'axis': axis, 'facing': facing, 'size': (width, height), 'off': off, 'hanging': not frame and depth == 0.0})


def hanging_sign(zone, key, x, y, zc, width, ceil_z, axis='x', height=None):
    """Two-sided sign board hung from the ceiling on two rods; the image reads correctly from both sides."""
    height = height or width / 4.0
    t = 3.0
    if axis == 'x':      # board runs along x, faces +y and -y
        B.box((x - width / 2 - 3, y - t, zc - height / 2 - 3), (x + width / 2 + 3, y + t, zc + height / 2 + 3), 'steel_trim', zone, collide=False, nav=False)
        sign(zone, key, 'x', y + t, +1, x, zc, width, height, frame=False, depth=0.0)
        sign(zone, key, 'x', y - t, -1, x, zc, width, height, frame=False, depth=0.0)
        for rx in (x - width / 2 + 16, x + width / 2 - 16):
            B.box((rx - 1, y - 1, zc + height / 2 + 3), (rx + 1, y + 1, ceil_z), 'chrome_trim', zone, collide=False, nav=False)
    else:
        B.box((x - t, y - width / 2 - 3, zc - height / 2 - 3), (x + t, y + width / 2 + 3, zc + height / 2 + 3), 'steel_trim', zone, collide=False, nav=False)
        sign(zone, key, 'y', x + t, +1, y, zc, width, height, frame=False, depth=0.0)
        sign(zone, key, 'y', x - t, -1, y, zc, width, height, frame=False, depth=0.0)
        for ry in (y - width / 2 + 16, y + width / 2 - 16):
            B.box((x - 1, ry - 1, zc + height / 2 + 3), (x + 1, ry + 1, ceil_z), 'chrome_trim', zone, collide=False, nav=False)


def decal_fit(mat, w, h, rot=False):
    img = MT.MATERIALS.get(mat, {}).get('img')
    if not img:
        return w, h
    iw, ih = (img[1], img[0]) if rot else img
    w2 = min(w, h * iw / ih)
    return w2, w2 * ih / iw


ART_DECAL_SWAP = {'blood_pool': 'decal_blood_feathered', 'floor_stain': 'decal_grime_feathered'}


BLOOD_COUNT = [0]


def decal_floor(zone, mat, x, y, z, w, h, rot=False, mirror=False):
    if mat.startswith('blood:'):            # blood:<variant> -> art decal_blood_<variant>, else the stock pool
        mat = ART_HOOKS.key('decal_blood_' + mat[6:]) or 'blood_pool'
    elif mat == 'blood_pool' and ART_HOOKS.BLOOD_VARIANTS:
        k_ = BLOOD_COUNT[0]; BLOOD_COUNT[0] += 1
        n_ = len(ART_HOOKS.BLOOD_VARIANTS)
        mat = ART_HOOKS.BLOOD_VARIANTS[k_ % n_]
        rot, mirror = bool((k_ // n_) % 2) != rot, bool((k_ // (2 * n_)) % 2) != mirror
    else:
        mat = ART_HOOKS.key(ART_DECAL_SWAP.get(mat, '')) or mat
    w, h = decal_fit(mat, w, h, rot)
    x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h / 2, y + h / 2
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
    if rot: uv = uv[1:] + uv[:1]
    if mirror: uv = [(1 - u, v) for u, v in uv]
    B.quad(mat, zone, [(x0, y0, z + 0.4), (x1, y0, z + 0.4), (x1, y1, z + 0.4), (x0, y1, z + 0.4)], n=(0, 0, 1), uvs=uv, collide=False)


DECALS = []        # decal quads (sz2_fxcheck.py: not an opaque square)


def decal_wall(zone, mat, axis, fixed, facing, s, zc, w, h):
    w, h = decal_fit(mat, w, h)
    DECALS.append({'zone': zone, 'mat': mat, 'axis': axis, 'fixed': fixed, 'facing': facing, 's': s, 'zc': zc, 'w': w, 'h': h})
    a, b, z0, z1 = s - w / 2, s + w / 2, zc - h / 2, zc + h / 2
    if axis == 'x':
        y = fixed + facing * 0.4
        pts = [(b, y, z0), (a, y, z0), (a, y, z1), (b, y, z1)] if facing > 0 else [(a, y, z0), (b, y, z0), (b, y, z1), (a, y, z1)]
        n = (0, facing, 0)
    else:
        x = fixed + facing * 0.4
        pts = [(x, a, z0), (x, b, z0), (x, b, z1), (x, a, z1)] if facing > 0 else [(x, b, z0), (x, a, z0), (x, a, z1), (x, b, z1)]
        n = (facing, 0, 0)
    B.quad(mat, zone, pts, n=n, uvs=[(0, 1), (1, 1), (1, 0), (0, 0)], collide=False)


def column(zone, x, y, z0, z1, half=24):
    """Square tiled column: black tile base, white tile shaft, steel cap and base ring."""
    B.box((x - half - 2, y - half - 2, z0), (x + half + 2, y + half + 2, z0 + 10), 'rubber_trim', zone, collide=False, nav=False, skip=('bottom',))
    B.box((x - half, y - half, z0 + 10), (x + half, y + half, z0 + 112), 'tile_charcoal', zone, collide=False, nav=False, skip=('bottom', 'top'))
    B.box((x - half - 1.5, y - half - 1.5, z0 + 112), (x + half + 1.5, y + half + 1.5, z0 + 120), 'steel_trim', zone, collide=False, nav=False)
    B.box((x - half, y - half, z0 + 120), (x + half, y + half, z1 - 24), 'tile_white', zone, collide=False, nav=False, skip=('bottom', 'top'))
    B.box((x - half - 4, y - half - 4, z1 - 24), (x + half + 4, y + half + 4, z1), 'steel_trim', zone, collide=False, nav=False, skip=('top',))
    B.collision_box((x - half - 2, y - half - 2, z0), (x + half + 2, y + half + 2, z1))


# ============================================================================ architecture detail (art pass 3)
def floor_grid(zone, x0, y0, x1, y1, z, mat, step=480, w=12, border=24, skip=()):
    """Inlaid strips on a floor: a border along the edges and lines every `step` both ways (0.3 above the floor)."""
    zz = z + 0.3
    strips = [(x0, y0, x1, y0 + border), (x0, y1 - border, x1, y1), (x0, y0, x0 + border, y1), (x1 - border, y0, x1, y1)]
    x = x0 + step
    while x < x1 - step / 2:
        strips.append((x - w / 2, y0, x + w / 2, y1)); x += step
    y = y0 + step
    while y < y1 - step / 2:
        strips.append((x0, y - w / 2, x1, y + w / 2)); y += step
    for a, b, c, d in strips:
        # cut the strip around skipped rectangles (props, booths) along its long axis
        along_x = (c - a) >= (d - b)
        lo, hi = (a, c) if along_x else (b, d)
        cuts = [(s0, s1) if along_x else (t0, t1) for s0, t0, s1, t1 in skip if a < s1 and c > s0 and b < t1 and d > t0]
        for p0, p1 in bk.spans_minus(lo, hi, cuts):
            if p1 - p0 < 8:
                continue
            q = (p0, b, p1, d) if along_x else (a, p0, c, p1)
            B.quad(mat, zone, [(q[0], q[1], zz), (q[2], q[1], zz), (q[2], q[3], zz), (q[0], q[3], zz)], n=(0, 0, 1), collide=False)


def drains(zone, pts, z):
    for x, y in pts:
        B.quad('vent', zone, [(x - 16, y - 16, z + 0.35), (x + 16, y - 16, z + 0.35), (x + 16, y + 16, z + 0.35), (x - 16, y + 16, z + 0.35)],
               n=(0, 0, 1), uvs=[(0, 1), (1, 1), (1, 0), (0, 0)], collide=False)


def ceiling_grid(zone, x0, y0, x1, y1, z, step_x=None, step_y=None, depth=20, mat='ibeam'):
    """Beams under a ceiling: crosswise every step_x (lines of constant x) and lengthwise every step_y."""
    if step_x:
        x = x0 + step_x
        while x < x1 - 8:
            B.box((x - 7, y0, z - depth), (x + 7, y1, z), mat, zone, collide=False, nav=False); x += step_x
    if step_y:
        y = y0 + step_y
        while y < y1 - 8:
            B.box((x0, y - 7, z - depth), (x1, y + 7, z), mat, zone, collide=False, nav=False); y += step_y


def pilasters(zone, axis, fixed, facing, s0, s1, zf, zc, step=320, avoid=(), lower='tile_charcoal', upper='tile_white'):
    """Tiled pilasters with a steel capital and a rubber base every `step` along a wall, skipping `avoid` (s, half)."""
    out = []
    s = s0 + step / 2
    while s < s1 - 40:
        if not any(abs(s - a) < h for a, h in avoid):
            if axis == 'x':
                B.slab_x(s - 18, s + 18, fixed, zf, zf + 112, 8, lower, zone, facing, collide=False, nav=False)
                B.slab_x(s - 16, s + 16, fixed, zf + 112, zc - 24, 6, upper, zone, facing, collide=False, nav=False)
                B.slab_x(s - 22, s + 22, fixed, zc - 24, zc - 8, 12, 'steel_trim', zone, facing, collide=False, nav=False)
                B.slab_x(s - 20, s + 20, fixed, zf, zf + 10, 10, 'rubber_trim', zone, facing, collide=False, nav=False)
                geo_prop('pilaster', zone, (s - 18, fixed - 8, zf), (s + 18, fixed + 8, zc))
            else:
                B.slab_y(s - 18, s + 18, fixed, zf, zf + 112, 8, lower, zone, facing, collide=False, nav=False)
                B.slab_y(s - 16, s + 16, fixed, zf + 112, zc - 24, 6, upper, zone, facing, collide=False, nav=False)
                B.slab_y(s - 22, s + 22, fixed, zc - 24, zc - 8, 12, 'steel_trim', zone, facing, collide=False, nav=False)
                B.slab_y(s - 20, s + 20, fixed, zf, zf + 10, 10, 'rubber_trim', zone, facing, collide=False, nav=False)
                geo_prop('pilaster', zone, (fixed - 8, s - 18, zf), (fixed + 8, s + 18, zc))
            out.append(s)
        s += step
    return out


ADS = ['poster_lasttrain', 'poster_mindgap', 'poster_station_zero'] + [k_ for k_ in [ART_HOOKS.key('poster_illustration_2')] if k_]


def ad_frame(zone, axis, fixed, facing, s, zc, k):
    """Recessed advertising panel: dark backing, steel frame, a poster."""
    w, h = 112, 160
    if axis == 'x':
        B.wall_plane(zone, 'x', fixed + facing * 0.3, facing, s - w / 2, s + w / 2, zc - h / 2, zc + h / 2, 'metal_black', collide=False)
        for a, b, z0, z1 in ((s - w / 2 - 8, s - w / 2, zc - h / 2 - 8, zc + h / 2 + 8), (s + w / 2, s + w / 2 + 8, zc - h / 2 - 8, zc + h / 2 + 8),
                             (s - w / 2, s + w / 2, zc - h / 2 - 8, zc - h / 2), (s - w / 2, s + w / 2, zc + h / 2, zc + h / 2 + 8)):
            B.slab_x(a, b, fixed, z0, z1, 3, 'steel_trim', zone, facing, collide=False, nav=False)
    else:
        B.wall_plane(zone, 'y', fixed + facing * 0.3, facing, s - w / 2, s + w / 2, zc - h / 2, zc + h / 2, 'metal_black', collide=False)
        for a, b, z0, z1 in ((s - w / 2 - 8, s - w / 2, zc - h / 2 - 8, zc + h / 2 + 8), (s + w / 2, s + w / 2 + 8, zc - h / 2 - 8, zc + h / 2 + 8),
                             (s - w / 2, s + w / 2, zc - h / 2 - 8, zc - h / 2), (s - w / 2, s + w / 2, zc + h / 2, zc + h / 2 + 8)):
            B.slab_y(a, b, fixed, z0, z1, 3, 'steel_trim', zone, facing, collide=False, nav=False)
    ad_ = ART_HOOKS.key('ad_panel_broken') if (zone.startswith('stair') and os.environ.get('IWZ_AD_BROKEN') == '1') else None   # NOT_PROVEN lit
    sign(zone, ad_ or ADS[k % len(ADS)], axis, fixed, facing, s, zc, 96, 144, frame=False, depth=0.6)


def wall_niche(zone, axis, fixed, facing, s, z0, w=96, h=72):
    """Shallow dark niche (refuge / service recess) in a wall: black backing and a steel surround."""
    if axis == 'x':
        B.wall_plane(zone, 'x', fixed + facing * 0.4, facing, s - w / 2, s + w / 2, z0, z0 + h, 'vent', collide=False)
        B.slab_x(s - w / 2 - 6, s - w / 2, fixed, z0, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)
        B.slab_x(s + w / 2, s + w / 2 + 6, fixed, z0, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)
        B.slab_x(s - w / 2, s + w / 2, fixed, z0 + h, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)
    else:
        B.wall_plane(zone, 'y', fixed + facing * 0.4, facing, s - w / 2, s + w / 2, z0, z0 + h, 'vent', collide=False)
        B.slab_y(s - w / 2 - 6, s - w / 2, fixed, z0, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)
        B.slab_y(s + w / 2, s + w / 2 + 6, fixed, z0, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)
        B.slab_y(s - w / 2, s + w / 2, fixed, z0 + h, z0 + h + 6, 3, 'steel_trim', zone, facing, collide=False, nav=False)


def cable_tray(zone, axis, s0, s1, c, z, w=24):
    """Ceiling cable tray (steel) with a conduit beside it."""
    if axis == 'x':
        B.box((s0, c - w / 2, z - 4), (s1, c + w / 2, z), 'steel_trim', zone, collide=False, nav=False)
        B.box((s0, c + w / 2 + 6, z - 3), (s1, c + w / 2 + 9, z), 'metal_black', zone, collide=False, nav=False)
    else:
        B.box((c - w / 2, s0, z - 4), (c + w / 2, s1, z), 'steel_trim', zone, collide=False, nav=False)
        B.box((c + w / 2 + 6, s0, z - 3), (c + w / 2 + 9, s1, z), 'metal_black', zone, collide=False, nav=False)


FLICKER = []      # flickering fluorescent pairs (kit mp_dart_lightfluo_on / mp_dart_lightfluo), toggled by the level script


def flicker_lamp(zone, x, y, zc, yaw=0):
    FLICKER.append({'zone': zone, 'origin': (x, y, zc), 'yaw': yaw})
    LIGHTS.append({'zone': zone, 'origin': (x, y, zc - 8), 'type': 'omni', 'color': (0.85, 0.93, 1.0), 'radius': 300, 'intensity': 0.6,
                   'fixture': 'flicker'})


def rail_run(zone, axis, s0, s1, c, z, h=36, post=96, mat='steel_trim', collide=True):
    """Handrail / safety railing: posts every `post` and a top rail; collision as a thin wall."""
    n = max(1, int(round((s1 - s0) / post)))
    for k_ in range(int((s1 - s0) // 128) + 1):
        a_ = s0 + k_ * 128
        b_ = min(s1, a_ + 128)
        if b_ - a_ > 8:
            geo_prop('rail', zone, (a_, c - 2, z) if axis == 'x' else (c - 2, a_, z), (b_, c + 2, z + h) if axis == 'x' else (c + 2, b_, z + h))
    for k in range(n + 1):
        s = s0 + (s1 - s0) * k / n
        if axis == 'x':
            B.box((s - 1.5, c - 1.5, z), (s + 1.5, c + 1.5, z + h), mat, zone, collide=False, nav=False, skip=('bottom',))
        else:
            B.box((c - 1.5, s - 1.5, z), (c + 1.5, s + 1.5, z + h), mat, zone, collide=False, nav=False, skip=('bottom',))
    if axis == 'x':
        B.box((s0, c - 2, z + h), (s1, c + 2, z + h + 3), mat, zone, collide=False, nav=False)
        B.box((s0, c - 1, z + h / 2), (s1, c + 1, z + h / 2 + 2), mat, zone, collide=False, nav=False)
        if collide:
            B.collision_box((s0, c - 2, z), (s1, c + 2, z + h + 3))
    else:
        B.box((c - 2, s0, z + h), (c + 2, s1, z + h + 3), mat, zone, collide=False, nav=False)
        B.box((c - 1, s0, z + h / 2), (c + 1, s1, z + h / 2 + 2), mat, zone, collide=False, nav=False)
        if collide:
            B.collision_box((c - 2, s0, z), (c + 2, s1, z + h + 3))


def straight_stair(zone, space, axis, lo_end, hi_end, c0, c1, z_lo, z_hi, land_lo, land_hi, n_steps, head=288,
                   style='metro', side_walls=True, ceiling=True):
    """Stair along `axis` from lo_end (z_lo) to hi_end (z_hi); lo_end/hi_end are the end wall planes (either order).
    Render: treads and risers. Collision: low landing, smooth ramp through the nosings, high landing.
    Walls: banded side walls parallel to the slope; ceiling `head` above the nosing line."""
    d = 1 if hi_end > lo_end else -1
    s_a = lo_end + d * land_lo                  # first riser
    s_b = hi_end - d * land_hi                  # top landing edge
    run = (s_b - s_a) / n_steps
    rise = (z_hi - z_lo) / n_steps

    def P(s, c, z):
        return (s, c, z) if axis == 'x' else (c, s, z)

    def rect(s0, s1, z, mat, collide, tone='mid'):
        sa, sb = min(s0, s1), max(s0, s1)
        if axis == 'x':
            floor(zone, mat, sa, c0, sb, c1, z, collide=collide, tone=tone)
        else:
            floor(zone, mat, c0, sa, c1, sb, z, collide=collide, tone=tone)
    rect(lo_end, s_a, z_lo, 'tile_floor', False)
    rect(s_b, hi_end, z_hi, 'tile_floor', False)
    for k in range(n_steps):
        sk0, sk1 = s_a + k * run, s_a + (k + 1) * run
        zt = z_lo + (k + 1) * rise
        rect(sk0, sk1, zt, 'conc_floor', False)                                   # g26: concrete tread (stock tread art read all yellow)
        ns2_ = sk0 + d * 3 if d > 0 else sk0 - 3
        rect(min(sk0, ns2_), max(sk0, ns2_), zt + 0.2, 'steel_trim', False)           # nosing
        ns_ = sk0 + d * 4 if d > 0 else sk0 - 4
        if k in (0, n_steps - 1):
            rect(min(sk0, ns_), max(sk0, ns_), zt + 0.3, 'yellow_grip', False)     # tactile nosing: top and bottom step only
        # riser at sk0 facing the low end, with a steel nosing strip
        n = (-d, 0, 0) if axis == 'x' else (0, -d, 0)
        pts = [P(sk0, c0, zt - rise), P(sk0, c1, zt - rise), P(sk0, c1, zt), P(sk0, c0, zt)]
        if bk.dot(bk.cross(bk.sub(pts[1], pts[0]), bk.sub(pts[3], pts[0])), n) < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        B.quad('rubber_trim', zone, pts, n=n, collide=False)
    # collision: nosing line z(s) = z_lo + rise + (s - s_a) * rise / run, from s_a - run (z_lo) to s_b - run (z_hi)
    r0, r1 = s_a - run, s_b - run

    def cq(sa, sb, za, zb):
        pts = [P(sa, c0, za), P(sb, c0, zb), P(sb, c1, zb), P(sa, c1, za)]
        B.collision_quad(pts, n=(0, 0, 1))
    cq(lo_end, r0, z_lo, z_lo)
    cq(r0, r1, z_lo, z_hi)
    cq(r1, hi_end, z_hi, z_hi)
    # zombies (scripted agents) do not climb the smooth ramp: they keep their height, pass under its rising face and
    # fall out of the world (g14/g15 STAIR trails). Solid steps under the ramp (treads at their true height, risers
    # facing down the stair; all on or below the nosing line, so players and downward traces still meet the ramp first)
    # give agents 16-unit step-ups, matching the render treads.
    cq(r0, s_a, z_lo, z_lo)
    rn = (-d, 0, 0) if axis == 'x' else (0, -d, 0)
    for k in range(n_steps):
        sk0, sk1 = s_a + k * run, s_a + (k + 1) * run
        zt = z_lo + (k + 1) * rise
        B.collision_quad([P(sk0, c0, zt - rise), P(sk0, c1, zt - rise), P(sk0, c1, zt), P(sk0, c0, zt)], n=rn)
        if k < n_steps - 1:
            cq(sk0, sk1, zt, zt)

    def zline(s):
        t = (s - r0) / (r1 - r0)
        return z_lo + max(0.0, min(1.0, t)) * (z_hi - z_lo)
    # side walls (inward): walls at c0 (facing +) and c1 (facing -)
    segs = [(lo_end, r0), (r0, r1), (r1, hi_end)]
    if side_walls:
        for cfix, facing in ((c0, +1), (c1, -1)):
            wax = 'x' if axis == 'x' else 'y'
            for sa, sb in segs:
                za, zb = zline(sa), zline(sb)
                # stringer covering the step/wall junction, then tile bands parallel to the slope
                lower, upper = ('tile_green', 'tile_cream') if style == 'metro_cream' else ('tile_charcoal', 'tile_white')
                for lo_off, hi_off, mat in ((-rise - 2, 12, 'rubber_trim'), (12, 112, lower), (112, 120, 'steel_trim'),
                                            (120, head - 20, upper), (head - 20, head, 'molding')):
                    B.wall_sloped(zone, wax, cfix, facing, sa, sb, za + lo_off, zb + lo_off, za + hi_off, zb + hi_off, mat)
        # handrails 36 above the nosing line along both walls
        for cfix, sgn in ((c0, 1), (c1, -1)):
            cc = cfix + sgn * 4
            sa_ = min(r0, r1)
            while sa_ < max(r0, r1):
                sb_ = min(max(r0, r1), sa_ + 128)
                zm_ = zline((sa_ + sb_) / 2) + 34
                geo_prop('handrail', zone, P(sa_, cc - 2, zm_ - 4) if axis == 'x' else (cc - 2, sa_, zm_ - 4), P(sb_, cc + 2, zm_ + 4) if axis == 'x' else (cc + 2, sb_, zm_ + 4))
                sa_ = sb_
            p0 = (r0, zline(r0) + 34)
            p1 = (r1, zline(r1) + 34)
            pts_hi = [P(p0[0], cc - 1.5, p0[1] + 3), P(p1[0], cc - 1.5, p1[1] + 3), P(p1[0], cc + 1.5, p1[1] + 3), P(p0[0], cc + 1.5, p0[1] + 3)]
            B.quad('chrome_trim', zone, pts_hi, collide=False)
            pts_lo = [P(p0[0], cc - 1.5, p0[1]), P(p1[0], cc - 1.5, p1[1]), P(p1[0], cc - 1.5, p1[1] + 3), P(p0[0], cc - 1.5, p0[1] + 3)]
            B.quad('chrome_trim', zone, pts_lo, collide=False)
            pts_lo2 = [P(p0[0], cc + 1.5, p0[1]), P(p1[0], cc + 1.5, p1[1]), P(p1[0], cc + 1.5, p1[1] + 3), P(p0[0], cc + 1.5, p0[1] + 3)]
            B.quad('chrome_trim', zone, pts_lo2, collide=False)
    # ceiling: landings flat, slope parallel
    for sa, sb in (segs if ceiling else []):
        za, zb = zline(sa) + head, zline(sb) + head
        pts = [P(sa, c0, za), P(sa, c1, za), P(sb, c1, zb), P(sb, c0, zb)]
        nrm = bk.norm(bk.cross(bk.sub(pts[1], pts[0]), bk.sub(pts[3], pts[0])))
        if nrm[2] > 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        B.quad('ceil_tile', zone, pts, tone='dark')
    return zline, (r0, r1)


# ============================================================================ build
LIGHTS = []        # primary light records for the light compiler (origin, colour, radius); fixtures are geometry
GEO_PROPS = []     # world-geometry props checked by sz2_propcheck.py / counted by sz2_density.py (name, zone, mins, maxs)
MODELS = []        # other placed models (quest, relay, shutter, lever) for sz2_propcheck.py


def geo_prop(name, zone, mn, mx):
    GEO_PROPS.append({'name': name, 'zone': zone, 'mins': mn, 'maxs': mx})
LIGHT_COLOR = {'lamp_cool': (0.85, 0.93, 1.0), 'lamp_warm': (1.0, 0.86, 0.70), 'lamp_red': (1.0, 0.06, 0.04),
               'lamp_green': (0.1, 1.0, 0.2), 'light_panel': (1, 1, 1)}
SIGNS = []
PROPS = []         # static models from the asset kit: {'zone', 'model', 'origin', 'angles', 'scale', 'collision'}
DECOR = []         # script_model map entities (stock models placed at load)

# ---------------------------------------------------------------- 1 ticket hall  (-1200,3200)-(400,4400), z 0..320
Z = 'ticket_hall'
room(Z, 'hall', (-1200, 3200, 400, 4400), 0, 320, 'metro', 'checker', 'ceil_tile', skip=())
# ceiling: coffers made of steel beams every 400 + fluorescent strips
for x in range(-1200 + 400, 400, 400):
    B.box((x - 8, 3200, 296), (x + 8, 4400, 320), 'ibeam', Z, collide=False, nav=False)
for x in (-1000, -600, -200, 200):
    for y in (3400, 3800, 4200):
        strip_light(Z, x - 64, y - 8, x + 64, y + 8, 320, dead=(x == -600 and y == 4200))
for x in (-800, -400, 0):
    column(Z, x, 4000, 0, 320)
# turnstile row (y 3700) with 64-wide gates, ticket booth in the middle
TURN_Y = 3700
gates = []
x = -1168
# (g25) the box cabinets and the open booth pavilion are gone: kit turnstiles and the stock mobile ticket booth
# east half: railing with a service gate
rail_run(Z, 'x', 96, 260, TURN_Y, 0, h=40)
rail_run(Z, 'x', 340, 400, TURN_Y, 0, h=40)
# street exit (north): collapsed stairs up to rubble, zombie entry
room(Z, 'street', (-304, 4400, 112, 4600), 0, 320, 'metro', 'tile_floor', 'ceil_tile', skip=('south',))
for k in range(6):
    B.box((-304, 4448 + k * 24, 0), (112, 4600, 16 * (k + 1)), {'top': 'stair_tread', 'side': 'conc_painted'}, Z, collide=True, nav=True)
strip_light(Z, -160, 4500, -40, 4516, 320)
sign(Z, 'sign_station_zero', 'x', 4400, -1, -700, 220, 384)
sign(Z, 'sign_network_map', 'y', 400, -1, 3950, 170, 256, 128)
sign(Z, 'sign_to_platforms', 'x', 3200, +1, -600, 268, 256)
sign(Z, 'sign_to_old_station', 'y', -1200, +1, 3304, 268, 192)
sign(Z, 'poster_station_zero', 'y', -1200, +1, 3900, 120, 96, 144)
sign(Z, 'poster_mindgap', 'y', -1200, +1, 4150, 120, 96, 144)
sign(Z, 'poster_lasttrain', 'x', 3200, +1, -200, 120, 96, 144)
sign(Z, 'poster_lasttrain', 'y', 400, -1, 3620, 120, 96, 144)
decal_wall(Z, 'leak_stain', 'x', 4400, -1, 300, 200, 128, 220)
# blood, used sparingly and as one story (art c10c5ad): a body was dragged from the broken turnstile (x -650) to the
# stair A door, a hand slid down that door's frame
for k_, (x_, y_) in enumerate(((-650, 3610), (-628, 3500), (-606, 3390), (-590, 3290))):
    decal_floor(Z, 'blood:drag', x_, y_, 0, 104, 104, rot=bool(k_ % 2), mirror=bool(k_ // 2))
decal_wall(Z, ART_HOOKS.key('decal_blood_hand_smear') or 'blood_pool', 'x', 3200, +1, -731, 64, 44, 44)   # beside the door frame (frame x -706..-696)
floor_grid(Z, -1200, 3200, 400, 4400, 0, 'tile_black', step=400, skip=((-1168, 3660, -240, 3740), (-224, 3600, 96, 3800)))
drains(Z, [(-1000, 3400), (200, 3400), (-1000, 4250), (200, 4250)], 0)
ceiling_grid(Z, -1200, 3200, 400, 4400, 320, step_y=400, depth=24)
decal_floor(Z, 'floor_stain', -528, 3600, 0, 96, 400)
region('hall', Z, (-1200, 3200, 400, 4400), 0)
region('street', Z, (-304, 4400, 112, 4448), 0, (16, 0, 16, 0))
adjacent('hall', 'street')

# ---------------------------------------------------------------- 2 stair_a  (-800,2416)-(-400,3184), 0 -> -320 south
Z = 'stair_a'
zl_a, _ = straight_stair(Z, 'stair_a', 'y', 2416, 3184, -800, -400, -320, 0, 64, 64, 20)
wall(Z, 'stair_a', 'x', 3184, -1, -800, -400, 0, 288, 'metro')       # top end wall (door to the hall)
wall(Z, 'stair_a', 'x', 2416, +1, -800, -400, -320, -32, 'metro')    # bottom end wall (arch to the platform)
sign(Z, 'sign_to_platforms', 'x', 3184, -1, -600, 262, 192)
strip_light(Z, -640, 3120, -560, 3136, 288)
for y in (2600, 2800, 3000):
    zc = zl_a(y) + 288
    strip_light(Z, -616, y - 8, -584, y + 8, zc, depth=4)
region('stair_a', Z, (-800, 2416, -400, 3184), lambda x, y: zl_a(y))

# ---------------------------------------------------------------- 3 platform_a: deck (y 1600..2400, z -320), pit (y 1200..1600, z -384)
Z = 'platform_a'
DECK_Z, PIT_Z, PCEIL = -320, -384, 0
WELLS = {'well_w': (-2400, 1600, -2192, 1760, -1), 'well_e': (1904, 1600, 2112, 1760, +1)}   # x0,y0,x1,y1, descent dir
# IWZ_TRAIN=1 (train agent, iwz-stage2/train): the hero car stands at the platform, so the platform edge comes forward
# to EDGE_Y (car side y 1552 at track centre 1488 + BO3 mp_metro edge panel 9 deep + 5 gap); the deck overhangs the
# trackbed channel by 34 (under-platform clearance), the panel covers the face from the ballast top to the deck
TRAIN = os.environ.get('IWZ_TRAIN') == '1'
EDGE_Y = int(os.environ.get('IWZ_TRAIN_EDGE_Y', 1566)) if TRAIN else 1600
WELL_LAND, WELL_STEPS = 64, 6      # QA g24: zombies stalled at the foot (16-unit risers, players passed): 10.7-unit risers, same slope
# deck floor (minus the stairwells), coping and yellow safety strip at the edge
deck_x = [(-2400, -2192), (-2192, 1904), (1904, 2112), (2112, 2400)]
floor(Z, 'conc_tiles', -2400, 1760, 2400, 2400, DECK_Z)
floor(Z, 'conc_tiles', -2192, EDGE_Y + 48, 1904, 1760, DECK_Z)
floor(Z, 'conc_tiles', 2112, EDGE_Y + 48, 2400, 1760, DECK_Z)
floor(Z, 'yellow_grip', -2192, EDGE_Y + 24, 1904, EDGE_Y + 48, DECK_Z)
floor(Z, 'yellow_grip', 2112, EDGE_Y + 24, 2400, EDGE_Y + 48, DECK_Z)
floor(Z, 'conc_painted', -2192, EDGE_Y, 1904, EDGE_Y + 24, DECK_Z)
floor(Z, 'conc_painted', 2112, EDGE_Y, 2400, EDGE_Y + 24, DECK_Z)
for x_ in range(-2112, 2400, 384):
    floor(Z, 'conc_trim_floor', x_ - 5, EDGE_Y + 64 if TRAIN else 1760, x_ + 5, 2368, DECK_Z + 0.25, collide=False)       # expansion joint (train: across the whole deck)
for x_, y_, w_, h_ in ((-1700, 1980, 160, 120), (-860, 2140, 200, 140), (-120, 1880, 150, 110), (620, 2060, 220, 150),
                       (1380, 1920, 170, 130), (2050, 2200, 150, 120)):
    decal_floor(Z, 'floor_stain', x_, y_, DECK_Z + 0.4, w_, h_)
# platform edge face (deck to pit) with a coping lip
for x0_, x1_ in ((-2192, 1904), (2112, 2400)):
    B.wall_plane(Z, 'x', EDGE_Y, -1, x0_, x1_, PIT_Z, DECK_Z, 'conc_dark')
    if not TRAIN:       # (train) the mp_metro edge panels carry the coping
        B.box((x0_, EDGE_Y - 4, DECK_Z - 6), (x1_, EDGE_Y, DECK_Z), 'conc_painted', Z, collide=False, nav=False)
if TRAIN:
    # side faces of the deck overhang beside the two stairwells (the pit stays open in front of a well's foot)
    for xs_, fc_ in ((-2192, -1), (1904, +1), (2112, -1)):
        B.wall_plane(Z, 'y', xs_, fc_, EDGE_Y, 1600, PIT_Z, DECK_Z, 'conc_dark')
# stairwells into the pit (4 steps), railing on the deck side
for wname, (wx0, wy0, wx1, wy1, ddir) in WELLS.items():
    if ddir < 0:   # descends westwards: low end at wx0
        zl, _ = straight_stair(Z, wname, 'x', wx0, wx1, wy0, wy1, PIT_Z, DECK_Z, WELL_LAND, 0.0001, WELL_STEPS, side_walls=False, ceiling=False)
        lo, hi = wx0, wx1
    else:
        zl, _ = straight_stair(Z, wname, 'x', wx1, wx0, wy0, wy1, PIT_Z, DECK_Z, WELL_LAND, 0.0001, WELL_STEPS, side_walls=False, ceiling=False)
        lo, hi = wx1, wx0
    # well side face at wy1 (facing south into the well) from the stair line up to the deck
    segs = [(min(wx0, wx1), max(wx0, wx1))]
    xs = sorted([wx0, wx1])
    N = 8
    for k in range(N):
        sa = xs[0] + (xs[1] - xs[0]) * k / N
        sb = xs[0] + (xs[1] - xs[0]) * (k + 1) / N
        B.wall_sloped(Z, 'x', wy1, -1, sa, sb, zl(sa) - 18, zl(sb) - 18, DECK_Z, DECK_Z, 'conc_dark')
    rail_run(Z, 'x', xs[0], xs[1], wy1 + 3, DECK_Z, h=38)
    # well end faces from the track bed to the deck: close the space under the deck at both ends of the well
    # (engine walk g9: rays escaped under deck_east / the deck west end from the pit)
    B.wall_plane(Z, 'y', xs[0], +1, wy0, wy1, PIT_Z, DECK_Z, 'conc_dark')
    B.wall_plane(Z, 'y', xs[1], -1, wy0, wy1, PIT_Z, DECK_Z, 'conc_dark')
    region(wname, Z, (xs[0], wy0, xs[1], wy1), (lambda f: (lambda x, y: f(x)))(zl), (16 if ddir < 0 else 0, 0, 0 if ddir < 0 else 16, 16))
# pit floor (track bed) and track wall
floor(Z, 'conc_dark', -2400, 1200, 2400, 1600, PIT_Z, tone='dark')
wall(Z, 'pit', 'x', 1200, +1, -2400, 2400, PIT_Z, PCEIL, 'track')        # track wall (south)
# platform north wall and ceiling
wall(Z, 'platform_deck', 'x', 2400, -1, -2400, 2400, DECK_Z, PCEIL, 'metro')
ceiling(Z, 'conc_painted', -2400, 1200, 2400, 2400, PCEIL)
for x in range(-2304, 2400, 256):
    B.box((x - 8, 1200, PCEIL - 28), (x + 8, 2400, PCEIL), 'ibeam', Z, collide=False, nav=False)
for x in range(-2176, 2304, 384):
    strip_light(Z, x - 72, 2140, x + 72, 2156, PCEIL - 28, dead=(x == -1024))
    strip_light(Z, x - 72, 1844, x + 72, 1860, PCEIL - 28)
for x in range(-2176, 2304, 768):
    strip_light(Z, x - 48, 1392, x + 48, 1404, PCEIL - 28, mat='lamp_cool')
# west wall: deck part metro, pit part = bricked-up tunnel mouth with the tunnel door
wall(Z, 'platform_deck', 'y', -2400, +1, 1600, 2400, DECK_Z, PCEIL, 'metro')
wall(Z, 'pit', 'y', -2400, +1, 1200, 1600, PIT_Z, -96, 'brick')
B.wall_plane(Z, 'y', -2400, +1, 1200, 1600, -96, PCEIL, 'tile_white')
B.box((-2400, 1200, -112), (-2392, 1600, -88), 'conc_painted', Z, collide=False, nav=False)
# east wall: deck part with the corridor door, pit part = tunnel mouth recess closed by a grate
wall(Z, 'platform_deck', 'y', 2400, -1, 1600, 2400, DECK_Z, PCEIL, 'metro')
B.wall_plane(Z, 'y', 2400, -1, 1200, 1216, PIT_Z, PCEIL, 'tile_white')
B.wall_plane(Z, 'y', 2400, -1, 1584, 1600, PIT_Z, PCEIL, 'tile_white')
B.wall_plane(Z, 'y', 2400, -1, 1216, 1584, -128, PCEIL, 'tile_white')
B.box((2392, 1200, -144), (2400, 1600, -120), 'conc_painted', Z, collide=False, nav=False)
room(Z, 'recess', (2400, 1216, 2592, 1584), PIT_Z, -128, 'tunnel', 'conc_dark', 'conc_dark', skip=('west',))
B.wall_plane(Z, 'y', 2560, -1, 1216, 1584, PIT_Z, -128, 'grate', collide=False)
B.wall_plane(Z, 'y', 2410, -1, 1216, 1584, PIT_Z, -128, 'grate', collide=False)
B.collision_quad([(2410, 1216, PIT_Z), (2410, 1584, PIT_Z), (2410, 1584, -128), (2410, 1216, -128)], n=(-1, 0, 0))
geo_prop('recess_grate', Z, (2556, 1216, PIT_Z), (2564, 1584, -128))
B.wall_plane(Z, 'y', 2591, -1, 1216, 1584, PIT_Z, -128, 'conc_dark', collide=False)
floor(Z, 'conc_dark', 2400, 1216, 2592, 1584, PIT_Z, tone='dark')
# columns every 512 on the deck
COLS = [-1792, -1280, -768, -256, 256, 768, 1280, 1792]
for x in COLS:
    column(Z, x, 2000, DECK_Z, PCEIL)
# track: sleepers, two running rails, third rail on insulators (pit, tunnel, recess)
# Trackbed channel (both the platform_a pit and the service tunnel): y 1392..1584, centre 1488, floor PIT_Z. The tunnel
# door d_platform_tunnel spans exactly this channel; no wall, pier or rib stands inside it (sz2_artlint trackbed rule).
TRACK_Y0, TRACK_Y1 = 1392, 1584
TRACK_CY = (TRACK_Y0 + TRACK_Y1) / 2
GAUGE = 56.5                                   # standard gauge, inner rail faces (1 unit = 1 inch)
RAIL_Y = (TRACK_CY - GAUGE / 2, TRACK_CY + GAUGE / 2)
THIRD_Y = TRACK_CY - (57.11 if TRAIN else 60)    # conductor rail on the far side from the platform (trap line, gsc); train kit: its rail line
TRACK_SPEC = {'channels': [], 'gauge': GAUGE, 'centre_y': TRACK_CY, 'rail_y': list(RAIL_Y), 'third_rail_y': THIRD_Y,
              'floor_z': -384, 'owner': 'train agent (iwz-stage2\\train): rails, ties, third rail, buffer stop, car, platform edges',
              'note': 'clean channel; the level draws only its floor (dark concrete with a centred ballast strip)'}


def track(zone, x0, x1):
    """Clean trackbed channel x0..x1 (no rails / ties / beams: the train agent's kit). A ballast strip centred on the
    channel shows where the track goes; TRACK_SPEC records the channel for the placement spec and the lint."""
    B.quad('ballast', zone, [(x0, TRACK_CY - 64, PIT_Z + 0.4), (x1, TRACK_CY - 64, PIT_Z + 0.4), (x1, TRACK_CY + 64, PIT_Z + 0.4),
                             (x0, TRACK_CY + 64, PIT_Z + 0.4)], n=(0, 0, 1), collide=False)
    TRACK_SPEC['channels'].append({'zone': zone, 'x0': x0, 'x1': x1, 'y0': TRACK_Y0, 'y1': TRACK_Y1, 'z': PIT_Z, 'centre_y': TRACK_CY})


track(Z, -2400, 2406)
# pit cess (south of the channel): slab joints every 384 units and oil / water stains (sz2_flatness)
for x_ in range(-2208, 2400, 384):
    floor(Z, 'conc_trim_floor', x_ - 4, 1216, x_ + 4, 1388, PIT_Z + 0.25, collide=False)
for x_, y_ in ((-1900, 1320), (-260, 1290), (1100, 1330), (2050, 1300)):
    decal_floor(Z, 'floor_stain', x_, y_, PIT_Z + 0.4, 110, 220)
# (g25) the generated box carriage is gone (owner review g24: grey boxes with red tops and flat black window holes).
# The hero train is the stock cp_disco subway car (kit, IWZ_KIT), parked at the platform with see-through windows.
# The EE bear sits on the platform floor by the train doors, next to abandoned luggage (child left behind).
TEDDY_SPOT = (180, 1700, DECK_Z)
if TRAIN:
    # coordinator 2026-11-08: the bear was out in the open on the platform. It now rests on the hero car's floor at the
    # far track-side dressing anchor (car-local 220, -40; floor = rail top -356.31 + 33.3), below the window line and
    # behind a duffel bag seen from the door bay (x 142..230): a hint-sound hunt, not visible from the walkway.
    TEDDY_SPOT = (520, 1448, -356.31 + 33.3)
# signs, posters, map on the platform walls
for x in (-1536, 0, 1536):
    sign(Z, 'sign_station_zero', 'x', 1200, +1, x, -150, 384)     # track wall, readable from the deck
for x in (-1024, 1024):
    sign(Z, 'sign_station_zero_plain', 'x', 2400, -1, x, -170, 320)
sign(Z, 'sign_northbound', 'x', 2400, -1, 0, -150, 256)
hanging_sign(Z, 'sign_station_zero_plain', 0, 1880, -84, 256, PCEIL - 28)      # (g25) one, between the wall roundels
hanging_sign(Z, 'sign_to_old_station', -2250, 1700, -96, 192, PCEIL - 28, axis='y')
sign(Z, 'sign_network_map', 'x', 2400, -1, -1536, -200, 256, 128)
for x, p in ((-768, 'poster_lasttrain'), (512, 'poster_mindgap'), (-2048, 'poster_mindgap'), (1792, 'poster_lasttrain')):
    sign(Z, p, 'x', 1200, +1, x, -170, 96, 144)
sign(Z, 'sign_staff_only', 'y', 2400, -1, 1800, -90, 192)
for x in (-1900, -400, 900, 2000):
    decal_wall(Z, 'leak_stain', 'x', 2400, -1, x, -120, 96, 180)
decal_floor(Z, 'blood:pool', 600, 2200, DECK_Z, 96, 96, mirror=True)
# nav regions: deck (minus wells), coping strip, pit (around the car underframe), recess
_sign_s = [-1536, -1024, 0, 1024]
_avoid = [(s_, 170) for s_ in _sign_s] + [(s_, 60) for s_ in (-1280, 256, 1792, -768, 768, 528)] + [(600, 90), (1100, 90), (2300, 120)]
_pil = pilasters(Z, 'x', 2400, -1, -2400, 2300, DECK_Z, PCEIL, step=320, avoid=_avoid)
_k = 0
for a_, b_ in zip(_pil, _pil[1:]):
    m_ = (a_ + b_) / 2
    if b_ - a_ <= 360 and not any(abs(m_ - s_) < 260 for s_ in _sign_s) and not any(abs(m_ - s_) < 90 for s_ in (-1280, 256, 1792, -768, 768, 528, 600, 1100)):
        ad_frame(Z, 'x', 2400, -1, m_, -165, _k); _k += 1
# deck floor detail (g25, replaces the conc_trim_floor inlay that read as a smeared streak): a dark tile border along
# the back wall and around each column, floor drains between the columns
floor(Z, 'tile_black', -2400, 2368, 2400, 2400, DECK_Z + 0.3, collide=False)
for x_ in (-1792, -1280, -768, -256, 256, 768, 1280, 1792):
    for (a_, b_, c_, d_) in ((x_ - 56, 1944, x_ + 56, 1960), (x_ - 56, 2040, x_ + 56, 2056), (x_ - 56, 1960, x_ - 40, 2040), (x_ + 40, 1960, x_ + 56, 2040)):
        floor(Z, 'tile_black', a_, b_, c_, d_, DECK_Z + 0.3, collide=False)
drains(Z, [(x_, 2200) for x_ in (-2048, -1536, -1024, -512, 0, 512, 1024, 1536)], DECK_Z)
B.quad('stair_tread', Z, [(-2192, EDGE_Y + 48, DECK_Z + 0.3), (1904, EDGE_Y + 48, DECK_Z + 0.3), (1904, EDGE_Y + 64, DECK_Z + 0.3), (-2192, EDGE_Y + 64, DECK_Z + 0.3)], n=(0, 0, 1), collide=False)
B.quad('stair_tread', Z, [(2112, EDGE_Y + 48, DECK_Z + 0.3), (2400, EDGE_Y + 48, DECK_Z + 0.3), (2400, EDGE_Y + 64, DECK_Z + 0.3), (2112, EDGE_Y + 64, DECK_Z + 0.3)], n=(0, 0, 1), collide=False)
if not TRAIN:
    for x0_, x1_ in ((-2192, 1904), (2112, 2400)):
        B.box((x0_, 1588, DECK_Z - 8), (x1_, 1600, DECK_Z), {'side': 'conc_painted', 'bottom': 'conc_dark', 'top': 'conc_painted'}, Z, collide=False, nav=False)
    for x_ in (-1800, -1100, 600, 1300):
        wall_niche(Z, 'x', 1600, -1, x_, PIT_Z, w=96, h=56)
drains(Z, [(-1500, 1300), (-700, 1300), (900, 1300), (1700, 1300)], PIT_Z)
# tunnel portals at both pit ends (concrete arch frame) with signal lights
for xw_, fc_ in ((-2400, +1), (2400, -1)):
    B.slab_y(1200, 1232, xw_, PIT_Z, -96, 10, 'conc_painted', Z, fc_, collide=False, nav=False)
    B.slab_y(1584, 1600, xw_, PIT_Z, -96, 10, 'conc_painted', Z, fc_, collide=False, nav=False)     # clear of the channel
    B.slab_y(1200, 1600, xw_, -96, -72, 12, 'conc_painted', Z, fc_, collide=False, nav=False)
    for y_, lamp_ in ((1220, 'lamp_red'), (1592, 'lamp_green')):
        B.box((xw_ + fc_ * 10 - 4, y_ - 6, -150), (xw_ + fc_ * 10 + 4, y_ + 6, -118), 'metal_black', Z, collide=False, nav=False)
        wall_lamp(Z, 'y', xw_ + fc_ * 14, fc_, y_, -142, mat=lamp_, w=8, h=8)
ceiling_grid(Z, -2400, 1200, 2400, 2400, PCEIL, step_y=400, depth=28)
region('deck', Z, (-2400, 1760, 2400, 2400), DECK_Z, (16, 0, 16, 16))
region('deck_mid', Z, (-2192, EDGE_Y, 1904, 1760), DECK_Z, (0, 0, 0, 0))
region('deck_east', Z, (2112, EDGE_Y, 2400, 1760), DECK_Z, (0, 0, 16, 0))
region('pit', Z, (-2400, 1200, 2400, 1600), PIT_Z, (0, 16, 0, 16))
if TRAIN:
    # no pit cells under the deck overhang (y EDGE_Y..1600 behind the edge face); in front of the stairwells' feet the
    # pit still reaches the old face line, so the pit -> well routes are unchanged
    for x0_, x1_ in ((-2192, 1904), (2112, 2400)):
        B.blockers.append((x0_, EDGE_Y, x1_, 1600, PIT_Z, DECK_Z))

for a, b_ in (('deck', 'deck_mid'), ('deck', 'deck_east'), ('deck', 'well_w'), ('deck', 'well_e'), ('deck_mid', 'well_w'),
              ('deck_mid', 'well_e'), ('deck_east', 'well_e'), ('pit', 'well_w'), ('pit', 'well_e')):
    adjacent(a, b_)

# ---------------------------------------------------------------- 4 maintenance corridor (L)
Z = 'maint_corridor'
room(Z, 'corridor_a', (2416, 1680, 3200, 1920), -320, -96, 'maint', 'conc_dark', 'corrugated')
room(Z, 'corridor_b', (2960, 1920, 3200, 2384), -320, -96, 'maint', 'conc_dark', 'corrugated', skip=('south',))
for (x0_, x1_, y_) in ((2416, 3200, 1696), (2416, 3200, 1904)):
    B.box((x0_, y_ - 4, -128), (x1_, y_ + 4, -120), 'metal_red', Z, collide=False, nav=False)    # pipes
for y_ in (2000, 2200):
    wall_lamp(Z, 'y', 3200, -1, y_, -150, mat='lamp_warm')
for x_ in (2600, 2900):
    wall_lamp(Z, 'x', 1920, -1, x_, -150, mat='lamp_warm')
sign(Z, 'sign_generator', 'x', 1920, -1, 2700, -170, 192)
decal_wall(Z, 'top_stain', 'x', 1680, +1, 2700, -130, 192, 64)
decal_wall(Z, 'drip_stain', 'y', 3200, -1, 2050, -220, 128, 160)
decal_floor(Z, 'floor_stain', 2900, 1800, -320, 160, 128)
cable_tray(Z, 'x', 2416, 3200, 1740, -100)
cable_tray(Z, 'y', 1920, 2384, 3150, -100)
floor_grid(Z, 2416, 1680, 3200, 1920, -320, 'beam_yellow', step=1000, w=8, border=8)
for (x0_, x1_, y_, f_) in ((2416, 3200, 1680, 1), (2416, 3200, 1920, -1)):
    B.slab_x(x0_, x1_, y_, -110, -96, 4, 'steel_trim', Z, f_, collide=False, nav=False)
region('corridor_a', Z, (2416, 1680, 3200, 1920), -320)
region('corridor_b', Z, (2960, 1920, 3200, 2384), -320, (16, 0, 16, 16))
adjacent('corridor_a', 'corridor_b')

# ---------------------------------------------------------------- 5 generator room (2600,2400)-(3800,3184), -320..32
Z = 'generator_room'
room(Z, 'generator', (2600, 2400, 3800, 3184), -320, 32, 'maint', 'deck_black', 'corrugated')
for x in range(2700, 3800, 200):
    B.box((x - 6, 2400, 8), (x + 6, 3184, 32), 'beam_yellow', Z, collide=False, nav=False)
for x in (2800, 3200, 3600):
    for y in (2600, 2980):
        strip_light(Z, x - 48, y - 8, x + 48, y + 8, 8, mat='lamp_warm')
# generator plinth + housing (box placeholder until the kit model), control panel for relay 3
GEN = (3300, 2800)
B.box((GEN[0] - 120, GEN[1] - 72, -320), (GEN[0] + 120, GEN[1] + 72, -304), 'conc_painted', Z)
B.collision_box((GEN[0] - 100, GEN[1] - 50, -304), (GEN[0] + 100, GEN[1] + 50, -206))     # kit generator body (decor below)
sign(Z, 'sign_signal_control', 'x', 3184, -1, 3100, -70, 192)
decal_floor(Z, 'blood:spatter', 2900, 2700, -320, 88, 88, rot=True)
for x_ in range(2700, 3800, 300):
    for y_, f_ in ((2400, 1), (3184, -1)):
        if not (3000 <= x_ <= 3200 and y_ == 3184) and not (3000 <= x_ <= 3200 and y_ == 2400):
            B.slab_x(x_ - 10, x_ + 10, y_, -320, 32, 10, 'ibeam', Z, f_, collide=False, nav=False)
            geo_prop('rib', Z, (x_ - 10, y_ - 10, -320), (x_ + 10, y_ + 10, 32))
for y_ in (2500, 3100):
    for x_, f_ in ((2600, 1), (3800, -1)):
        B.slab_y(y_ - 10, y_ + 10, x_, -320, 32, 10, 'ibeam', Z, f_, collide=False, nav=False)
floor_grid(Z, 2600, 2400, 3800, 3184, -320, 'beam_yellow', step=400, w=10, border=16, skip=((3170, 2720, 3430, 2880),))
drains(Z, [(2800, 2800), (3600, 2600)], -320)
region('generator', Z, (2600, 2400, 3800, 3184), -320)

# ---------------------------------------------------------------- 6 control room (2600,3200)-(3600,4000), -320..-32 + PaP alcove
Z = 'control_room'
room(Z, 'control', (2600, 3200, 3600, 4000), -320, -32, 'control_neutral', 'metal_floor', 'deck_black')     # art pass 5: floor / wainscot / ceiling values apart
room(Z, 'pap_alcove', (2976, 4016, 3232, 4160), -320, -112, 'control', 'diamond', 'conc_dark', skip=('south',))
# reveal of the alcove opening through the 16-unit control-room wall: lintel underside and side reveals (sz2_seams:
# the void showed between the wall face and the alcove ceiling)
ceiling(Z, 'conc_dark', 2976, 4000, 3232, 4016, -112)
B.wall_plane(Z, 'y', 2976, +1, 4000, 4016, -320, -112, 'conc_dark')
B.wall_plane(Z, 'y', 3232, -1, 4000, 4016, -320, -112, 'conc_dark')
DESKS = [(2640, 3520), (3260, 3520), (3300, 3760)]     # (x0, y0) of 240 x 80 signal desks; lane x 2880..3260 kept clear
for x0_, y0_ in DESKS:                # cool fluorescents over the signal desks (desk light)
    strip_light(Z, x0_ + 56, y0_ + 32, x0_ + 184, y0_ + 48, -32, mat='lamp_cool')
strip_light(Z, 3100 - 32, 3792, 3100 + 32, 3808, -32, mat='lamp_red')     # red emergency accent (run g12: red dominated)
for x in (2750, 3450):
    strip_light(Z, x - 64, 3792, x + 64, 3808, -32, mat='lamp_cool')
for x in (2750, 3100, 3450):
    strip_light(Z, x - 64, 3292, x + 64, 3308, -32, mat='lamp_cool')
for y_ in (3650,):
    wall_lamp(Z, 'y', 2600, +1, y_, -120, mat='lamp_red', w=16, h=16)
    wall_lamp(Z, 'y', 3600, -1, y_, -120, mat='lamp_red', w=16, h=16)
# signal desks (boxes, until the kit) and the network map board
for x0_, y0_ in DESKS:      # (g25) stock lab desks (decor block) instead of box desks; collision for the pair
    B.collision_box((x0_ + 12, y0_ + 24, -320), (x0_ + 228, y0_ + 56, -285))
decal_wall(Z, ART_HOOKS.key('evac_signal_diagram') or 'map_board', 'y', 3600, -1, 3600, -180, 320, 160)   # Station Zero evacuation / signal diagram when delivered
sign(Z, 'sign_network_map', 'x', 4000, -1, 2800, -170, 256, 128)
B.wall_plane(Z, 'x', 4150, -1, 2976, 3232, -320, -112, 'rollup', collide=False)
ceiling_grid(Z, 2600, 3200, 3600, 4000, -32, step_y=250, depth=16, mat='steel_trim')
for x_ in (2980, 3300):
    B.box((x_ - 7, 3200, -48), (x_ + 7, 4000, -32), 'steel_trim', Z, collide=False, nav=False)
floor_grid(Z, 2600, 3200, 3600, 4000, -320, 'steel_trim', step=333, w=10, border=20, skip=tuple((x0_, y0_, x0_ + 240, y0_ + 80) for x0_, y0_ in DESKS))
region('control', Z, (2600, 3200, 3600, 4000), -320)
region('pap_alcove', Z, (2976, 4016, 3232, 4160), -320)

# ---------------------------------------------------------------- 7 service tunnel (L) z -384..-96
Z = 'service_tunnel'


def tunnel_room(space, box, skip):
    x0, y0, x1, y1 = box
    floor(Z, 'conc_dark', x0, y0, x1, y1, -384, tone='dark')
    ceiling(Z, 'conc_dark', x0, y0, x1, y1, -96)
    for side, args in (('south', ('x', y0, +1, x0, x1)), ('north', ('x', y1, -1, x0, x1)),
                       ('west', ('y', x0, +1, y0, y1)), ('east', ('y', x1, -1, y0, y1))):
        if side in skip:
            continue
        ax, fx, fc, s0, s1 = args
        wall(Z, space, ax, fx, fc, s0, s1, -384, -96, 'tunnel')


tunnel_room('tunnel_a', (-3600, 1216, -2416, 1584), ('north',))
wall(Z, 'tunnel_a', 'x', 1584, -1, -3216, -2416, -384, -96, 'tunnel')
tunnel_room('tunnel_b', (-3600, 1584, -3216, 2584), ('south',))
track(Z, -3540, -2416)
for x in range(-3400, -2416, 400):
    wall_lamp(Z, 'x', 1216, +1, x, -170, mat='lamp_warm', w=12, h=10)
for y in range(1800, 2584, 400):
    wall_lamp(Z, 'y', -3584, +1, y, -170, mat='lamp_warm', w=12, h=10)
for y_ in (1230, 1240):
    B.box((-3600, y_, -210), (-2416, y_ + 3, -206), 'metal_black', Z, collide=False, nav=False)   # cables
wall_lamp(Z, 'x', 1216, +1, -2950, -230, mat='lamp_warm', w=16, h=10)      # (g25) wall work lamps replace the park lamp posts
wall_lamp(Z, 'y', -3600, +1, 2200, -230, mat='lamp_warm', w=16, h=10)
for x_ in range(-3500, -2416, 320):               # steel ribs across the tunnel ceiling
    B.box((x_ - 6, 1216, -120), (x_ + 6, 1584, -96), 'ibeam', Z, collide=False, nav=False)
for y_ in range(1700, 2584, 320):
    B.box((-3600, y_ - 6, -120), (-3216, y_ + 6, -96), 'ibeam', Z, collide=False, nav=False)
decal_wall(Z, 'drip_stain', 'x', 1584, -1, -2900, -200, 160, 180)
decal_wall(Z, 'drip_stain', 'y', -3216, -1, 2100, -200, 160, 180)
cable_tray(Z, 'x', -3600, -2416, 1260, -122)
cable_tray(Z, 'y', 1584, 2584, -3560, -122)
floor_grid(Z, -3600, 1216, -2416, 1584, -384, 'steel_trim', step=400, w=10, border=10, skip=((-3600, 1420, -2416, 1580),))
floor_grid(Z, -3600, 1584, -3216, 2584, -384, 'steel_trim', step=400, w=10, border=10)
flicker_lamp(Z, -3100, 1400, -97)
flicker_lamp(Z, -3400, 2300, -97, 90)
region('tunnel_a', Z, (-3600, 1216, -2416, 1584), -384, (16, 16, 16, 0))
region('tunnel_b', Z, (-3600, 1584, -3216, 2584), -384, (16, 0, 16, 16))
adjacent('tunnel_a', 'tunnel_b')

# ---------------------------------------------------------------- 8 platform_b (-3600,2616)-(-2064,3400), -384..-32
Z = 'platform_b'
room(Z, 'platform_b', (-3600, 2600, -2064, 3400), -384, -32, 'old', 'herringbone', 'deck_black')
for x in range(-3500, -2064, 256):
    B.box((x - 8, 2600, -56), (x + 8, 3400, -32), 'ibeam', Z, collide=False, nav=False)
strip_light(Z, -2800 - 48, 3000 - 6, -2800 + 48, 3000 + 6, -56, mat='lamp_warm')     # the one bare light of the old station
strip_light(Z, -3300 - 48, 2800 - 6, -3300 + 48, 2800 + 6, -56, mat='lamp_warm', dead=True)
# boarded windows on the north wall
for x in (-3400, -3000, -2600):
    B.wall_plane(Z, 'x', 3399, -1, x - 80, x + 80, -260, -120, 'brick_gray', collide=False)     # bricked-up window behind the boards
    for fa_, fb_, fz0_, fz1_ in ((x - 92, x - 80, -272, -108), (x + 80, x + 92, -272, -108), (x - 80, x + 80, -272, -260), (x - 80, x + 80, -120, -108)):
        B.slab_x(fa_, fb_, 3400, fz0_, fz1_, 4, 'wood_trim', Z, -1, collide=False, nav=False)     # window frame
# abandoned kiosk and the old ticket booth (relay 2)
OLD_BOOTH = (-3480, 3200, -3300, 3380)
B.box((OLD_BOOTH[0], OLD_BOOTH[1], -384), (OLD_BOOTH[2], OLD_BOOTH[1] + 10, -200), {'side': 'wood_green'}, Z)
B.box((OLD_BOOTH[0], OLD_BOOTH[1], -384), (OLD_BOOTH[0] + 10, OLD_BOOTH[3], -200), {'side': 'wood_green'}, Z)
sign(Z, 'sign_old_station', 'x', 2600, +1, -2900, -120, 320)
sign(Z, 'sign_old_station', 'y', -3600, +1, 3000, -120, 320)
sign(Z, 'poster_lasttrain', 'x', 3400, -1, -2300, -200, 96, 144)
decal_wall(Z, 'wall_stain', 'x', 3400, -1, -3200, -150, 160, 160)
decal_wall(Z, 'drip_stain', 'y', -3600, +1, 2800, -180, 160, 200)
decal_wall(Z, 'top_stain', 'x', 2600, +1, -3200, -60, 256, 64)
decal_floor(Z, 'floor_stain', -2900, 3100, -384, 192, 160)
pilasters(Z, 'x', 2600, +1, -3600, -2064, -384, -32, step=384, avoid=((-2900, 200), (-3400, 170)), lower='wood_green', upper='brick_white')
pilasters(Z, 'x', 3400, -1, -3600, -2064, -384, -32, step=384, avoid=((-3400, 110), (-3000, 110), (-2600, 110), (-2300, 80)), lower='wood_green', upper='brick_white')
ceiling_grid(Z, -3600, 2600, -2064, 3400, -32, step_y=400, depth=24)
floor_grid(Z, -3600, 2600, -2064, 3400, -384, 'wood_trim', step=384, w=12, border=24, skip=((-3480, 3200, -3300, 3380), (-2560, 2700, -2320, 2830)))
drains(Z, [(-3300, 2700), (-2400, 3200)], -384)
flicker_lamp(Z, -2550, 3000, -57)
flicker_lamp(Z, -3050, 3000, -57)
region('platform_b', Z, (-3600, 2600, -2064, 3400), -384)

# ---------------------------------------------------------------- 9 stair_b (-2048,3104)-(-1216,3400): -384 -> 0 rising east
Z = 'stair_b'
zl_b, _ = straight_stair(Z, 'stair_b', 'x', -2048, -1216, 3104, 3400, -384, 0, 48, 48, 23, style='metro_cream')
wall(Z, 'stair_b', 'y', -2048, +1, 3104, 3400, -384, -96, 'metro_cream')
wall(Z, 'stair_b', 'y', -1216, -1, 3104, 3400, 0, 288, 'metro_cream')
for x in (-1900, -1650, -1400):
    strip_light(Z, x - 8, 3236, x + 8, 3268, zl_b(x) + 288, depth=4)
sign(Z, 'sign_to_old_station', 'y', -2048, +1, 3252, -150, 192)
region('stair_b', Z, (-2048, 3104, -1216, 3400), lambda x, y: zl_b(x))

# ---------------------------------------------------------------- art pass 4: wall structure in the service wing
# (lead 2026-11-07, contact sheet g18: corridor, generator room, control room and tunnel walls still read as plain
# plaster). Wall ribs / pilasters, a low wainscot band and an upper molding on every long wall, skipping openings,
# vents, signs and lamps; tunnel ribs close the ceiling ribs into full lining rings. Render only (no collision, no nav).
def _spans(s0, s1, avoid):
    return [(a, b) for a, b in bk.spans_minus(s0, s1, [(c - h, c + h) for c, h in avoid]) if b - a >= 12]


def wall_band(zone, axis, fixed, facing, s0, s1, z0, z1, mat, depth=3, avoid=()):
    for a, b in _spans(s0, s1, avoid):
        if axis == 'x':
            B.slab_x(a, b, fixed, z0, z1, depth, mat, zone, facing, collide=False, nav=False)
        else:
            B.slab_y(a, b, fixed, z0, z1, depth, mat, zone, facing, collide=False, nav=False)


def wall_ribs(zone, axis, fixed, facing, positions, z0, z1, mat='ibeam', w=12, depth=8, avoid=()):
    for c in positions:
        if any(abs(c - a) < h + w for a, h in avoid):
            continue
        if axis == 'x':
            B.slab_x(c - w / 2, c + w / 2, fixed, z0, z1, depth, mat, zone, facing, collide=False, nav=False)
            geo_prop('rib', zone, (c - w / 2, fixed - depth, z0), (c + w / 2, fixed + depth, z1))
        else:
            B.slab_y(c - w / 2, c + w / 2, fixed, z0, z1, depth, mat, zone, facing, collide=False, nav=False)
            geo_prop('rib', zone, (fixed - depth, c - w / 2, z0), (fixed + depth, c + w / 2, z1))


if os.environ.get('IWZ_ARCH4', '1') == '1':
    # maintenance corridor (L): ribs every 200, dark concrete plinth, steel molding under the ceiling
    Zm_ = 'maint_corridor'
    av_s = [(2800, 40)]                                            # wall vent spawner
    av_n = [(2700, 110), (2600, 30), (2900, 30), (3080, 110)]      # generator sign, lamps, corridor bend opening
    av_e = [(2000, 30), (2200, 30), (2250, 40)]                    # lamps, wall fan
    wall_ribs(Zm_, 'x', 1680, +1, range(2516, 3200, 200), -320, -96, avoid=av_s)
    wall_ribs(Zm_, 'x', 1920, -1, range(2516, 2976, 200), -320, -96, avoid=av_n)
    wall_ribs(Zm_, 'y', 3200, -1, range(1780, 2384, 200), -320, -96, avoid=av_e)
    wall_ribs(Zm_, 'y', 2960, +1, range(2020, 2384, 200), -320, -96)
    wall_band(Zm_, 'x', 1680, +1, 2416, 3200, -320, -288, 'conc_dark', avoid=av_s)
    wall_band(Zm_, 'x', 1920, -1, 2416, 2976, -320, -288, 'conc_dark')
    wall_band(Zm_, 'y', 3200, -1, 1680, 2384, -320, -288, 'conc_dark')
    wall_band(Zm_, 'y', 2960, +1, 1920, 2384, -320, -288, 'conc_dark')
    # generator room: panel wainscot, overhead pipe runs along both long walls, molding
    Zg_ = 'generator_room'
    av_gs = [(3080, 100)]                                           # arch from the corridor
    av_gn = [(3100, 104), (3660, 110), (2800, 60)]                  # door to control, control panel, lockers
    av_gw = [(2675, 75)]                                            # electrical panel + wall vent
    av_ge = [(2700, 40)]                                            # wall vent
    wall_band(Zg_, 'x', 2400, +1, 2600, 3800, -320, -272, 'panel_dark', avoid=av_gs)
    wall_band(Zg_, 'x', 3184, -1, 2600, 3800, -320, -272, 'panel_dark', avoid=av_gn)
    wall_band(Zg_, 'y', 2600, +1, 2400, 3184, -320, -272, 'panel_dark', avoid=av_gw)
    wall_band(Zg_, 'y', 3800, -1, 2400, 3184, -320, -272, 'panel_dark', avoid=av_ge)
    for y_, f_ in ((2400, 1), (3184, -1)):
        wall_band(Zg_, 'x', y_, f_, 2600, 3800, -272, -266, 'steel_trim', depth=4, avoid=av_gs if f_ > 0 else av_gn)
        for k_, (zp, mat) in enumerate(((-40, 'metal_red'), (-62, 'metal_black'))):     # pipe pair below the ceiling
            yy = y_ + f_ * (14 + 10 * k_)
            B.box((2600, yy - 4, zp - 4), (3800, yy + 4, zp + 4), mat, Zg_, collide=False, nav=False)
    # control room: panelled pilasters, wainscot and a ceiling molding
    Zc_ = 'control_room'
    av_cs = [(3100, 120)]
    av_cn = [(3104, 150), (2800, 140), (2660, 50)]
    av_cw = [(3650, 50)]
    av_ce = [(3600, 180), (3650, 40)]
    pilasters(Zc_, 'x', 3200, +1, 2600, 3600, -320, -32, step=250, avoid=av_cs, lower='panel_dark', upper='panel_wall')
    pilasters(Zc_, 'x', 4000, -1, 2600, 3600, -320, -32, step=250, avoid=av_cn, lower='panel_dark', upper='panel_wall')
    pilasters(Zc_, 'y', 2600, +1, 3200, 4000, -320, -32, step=266, avoid=av_cw, lower='panel_dark', upper='panel_wall')
    pilasters(Zc_, 'y', 3600, -1, 3200, 4000, -320, -32, step=266, avoid=av_ce, lower='panel_dark', upper='panel_wall')
    for ax_, fx_, fc_, a_, b_, av_ in (('x', 3200, 1, 2600, 3600, av_cs), ('x', 4000, -1, 2600, 3600, [(3104, 150)]),
                                      ('y', 2600, 1, 3200, 4000, av_cw), ('y', 3600, -1, 3200, 4000, [])):
        wall_band(Zc_, ax_, fx_, fc_, a_, b_, -320, -284, 'panel_dark', avoid=av_)
        wall_band(Zc_, ax_, fx_, fc_, a_, b_, -56, -44, 'steel_trim', depth=5, avoid=av_)
    # service tunnel: lining rings (the ceiling ribs continue down both walls), a painted safety line
    Zt_ = 'service_tunnel'
    wall_ribs(Zt_, 'x', 1216, +1, range(-3500, -2416, 320), -384, -96, w=12, depth=10)
    wall_ribs(Zt_, 'y', -3600, +1, range(1700, 2584, 320), -384, -96, w=12, depth=10)
    wall_ribs(Zt_, 'y', -3216, -1, range(1700, 2584, 320), -384, -96, w=12, depth=10, avoid=[(2100, 70)])
    wall_band(Zt_, 'x', 1216, +1, -3600, -2416, -384, -360, 'conc_painted')
    wall_band(Zt_, 'x', 1216, +1, -3600, -2416, -300, -294, 'beam_yellow', depth=1)
    wall_band(Zt_, 'y', -3600, +1, 1584, 2584, -384, -360, 'conc_painted')
    wall_band(Zt_, 'y', -3600, +1, 1584, 2584, -300, -294, 'beam_yellow', depth=1)


# ---------------------------------------------------------------- art pass 5 (lead review of the g24 contact sheet)
if os.environ.get('IWZ_ART5', '1') == '1':
    # generator room: maintenance catwalk on the east wall (visual: no collision, out of reach), its ladder, wall conduit
    # drops into electrical boxes, hazard markings around the generator plinth, two hanging work lights
    Zg5 = 'generator_room'
    B.box((3736, 2440, -176), (3800, 3150, -168), {'top': 'grate', 'bottom': 'grating_under', 'side': 'ibeam'}, Zg5, collide=False, nav=False)
    for y_ in range(2470, 3150, 170):
        B.box((3740, y_ - 3, -168), (3746, y_ + 3, -128), 'steel_trim', Zg5, collide=False, nav=False)        # railing posts
        B.box((3742, y_ - 2, -320), (3746, y_ + 2, -176), 'ibeam', Zg5, collide=False, nav=False)            # catwalk legs
    B.box((3740, 2440, -132), (3746, 3150, -128), 'steel_trim', Zg5, collide=False, nav=False)                # handrail
    B.box((3740, 2440, -152), (3746, 3150, -149), 'steel_trim', Zg5, collide=False, nav=False)                # mid rail
    for x_ in (2700, 3300, 3600):
        B.box((x_ - 2, 2402, -300), (x_ + 2, 2406, -60), 'metal_black', Zg5, collide=False, nav=False)       # conduit drops
    for y_ in (2550, 2950):
        B.box((2602, y_ - 2, -300), (2606, y_ + 2, -60), 'metal_black', Zg5, collide=False, nav=False)
    gx_, gy_ = GEN
    for (x0_, y0_, x1_, y1_) in ((gx_ - 150, gy_ - 100, gx_ + 150, gy_ - 92), (gx_ - 150, gy_ + 92, gx_ + 150, gy_ + 100),
                                 (gx_ - 150, gy_ - 92, gx_ - 142, gy_ + 92), (gx_ + 142, gy_ - 92, gx_ + 150, gy_ + 92)):
        B.quad('beam_yellow', Zg5, [(x0_, y0_, -319.6), (x1_, y0_, -319.6), (x1_, y1_, -319.6), (x0_, y1_, -319.6)], n=(0, 0, 1), collide=False)
    for x_, y_ in ((2900, 2700), (3600, 2950)):
        B.box((x_ - 1, y_ - 1, -60), (x_ + 1, y_ + 1, 32), 'metal_black', Zg5, collide=False, nav=False)       # chain
        B.box((x_ - 20, y_ - 12, -72), (x_ + 20, y_ + 12, -60), {'side': 'metal_black', 'top': 'metal_black', 'bottom': 'lamp_warm'}, Zg5, collide=False, nav=False)
        LIGHTS.append({'zone': Zg5, 'origin': (x_, y_, -80), 'type': 'omni', 'color': (1.0, 0.85, 0.65), 'radius': 360, 'intensity': 1.4,
                       'fixture': 'work_light'})
    # service tunnel: conduit pair along both long walls, caged wall lamps between the rings, floor drains, debris
    Zt5 = 'service_tunnel'
    for y_, f_ in ((1216, 1), (1584, -1)):
        x0_ = -3600 if f_ > 0 else -3216
        for k_, zz_ in enumerate((-250, -262) if f_ > 0 else (-150, -162)):
            yy_ = y_ + f_ * (6 + 6 * k_)
            B.box((x0_, yy_ - 2.5, zz_ - 2.5), (-2416, yy_ + 2.5, zz_ + 2.5), 'metal_black' if k_ else 'metal_red', Zt5, collide=False, nav=False)
    for x_, f_ in ((-3600, 1), (-3216, -1)):
        for k_, zz_ in enumerate((-250, -262)):
            xx_ = x_ + f_ * (6 + 6 * k_)
            B.box((xx_ - 2.5, 1584, zz_ - 2.5), (xx_ + 2.5, 2584, zz_ + 2.5), 'metal_black' if k_ else 'metal_red', Zt5, collide=False, nav=False)
    for x_ in (-3340, -3020, -2700):
        wall_lamp(Zt5, 'x', 1584 if x_ > -3216 else 1216, -1 if x_ > -3216 else +1, x_, -190, mat='lamp_warm', w=12, h=10)
    for y_ in (1860, 2180, 2500):
        wall_lamp(Zt5, 'y', -3216, -1, y_, -190, mat='lamp_warm', w=12, h=10)
    drains(Zt5, [(-3300, 1300), (-2800, 1300), (-3400, 1800), (-3400, 2300)], -384)
    # ticket hall: tiled pilasters with ad frames on the long walls, two more hanging signs, the collapsed street stair
    # dressed with boards, cones and a barrier
    Zh5 = 'ticket_hall'
    _ph = pilasters(Zh5, 'y', -1200, +1, 3200, 4400, 0, 320, step=400, avoid=((3304, 110), (3640, 60), (3900, 70), (4150, 70)))
    _pe = pilasters(Zh5, 'y', 400, -1, 3200, 4400, 0, 320, step=400, avoid=((3620, 70), (3950, 150), (3900, 60), (4050, 60), (4220, 60)))
    ad_frame(Zh5, 'y', -1200, +1, 3500, 160, 0)
    ad_frame(Zh5, 'y', 400, -1, 3400, 160, 1)
    hanging_sign(Zh5, 'sign_to_old_station', -300, 3400, 236, 256, 296)
    hanging_sign(Zh5, 'sign_northbound', 200, 4000, 236, 256, 296)
    for x_ in (-280, -140, 0):
        B.box((x_ - 40, 4442, 20 + 0), (x_ + 40, 4446, 120), 'wood_planks', Zh5, collide=False, nav=False)     # boards on the stair
    B.box((-304, 4440, 100), (112, 4444, 112), 'wood_trim', Zh5, collide=False, nav=False)


# ---------------------------------------------------------------- story pass (g25): "the last train that never left"
# Station Zero was sealed the night of the incident; the last train is still at the platform; everything stopped.
STORY_KIT = {'newspaper_stack_fn_01', 'newspaper_single_fn_01', 'cp_disco_street_barricade', 'ls_biohazard_sheet_01',
             'ls_biohazard_sheet_02', 'clk_emergency_light'}      # cp_disco dump (kit route)
if os.environ.get('IWZ_STORY', '1') == '1':
    # collapsed ceiling section in the ticket hall: torn opening, a fallen panel leaning to the floor, rubble below
    cx_, cy_ = -760, 4250
    B.quad('conc_dark', 'ticket_hall', [(cx_ - 70, cy_ + 60, 319.4), (cx_ + 70, cy_ + 60, 319.4), (cx_ + 70, cy_ - 60, 319.4), (cx_ - 70, cy_ - 60, 319.4)],
           n=(0, 0, -1), collide=False)
    for zz_, mat_, nz_ in ((0, 'ceil_tile', 1), (-6, 'conc_dark', -1)):
        pts_ = [(cx_ - 70, cy_ - 50, 4 + zz_), (cx_ + 60, cy_ - 50, 4 + zz_), (cx_ + 60, cy_ + 60, 300 + zz_), (cx_ - 70, cy_ + 60, 300 + zz_)]
        B.quad(mat_, 'ticket_hall', pts_ if nz_ > 0 else pts_[::-1], n=(0, -0.95 * nz_, 0.3 * nz_), collide=False)
    B.collision_box((cx_ - 70, cy_ - 50, 0), (cx_ + 60, cy_ + 60, 120))
    decal_floor('ticket_hall', 'floor_stain', cx_, cy_ - 80, 0, 220, 140)
    # water leaks and puddles under the wall stains
    for x_, y_, z_, zn_ in ((-1900, 2330, DECK_Z, 'platform_a'), (900, 2330, DECK_Z, 'platform_a'), (330, 4300, 0, 'ticket_hall'),
                            (-3100, 1300, -384, 'service_tunnel'), (-2900, 3200, -384, 'platform_b')):
        decal_floor(zn_, 'water_stain', x_, y_, z_, 120, 96)     # 'puddle' (rvl) renders opaque grey: sz2_materials NOTES
    # blood, sparingly: by the train doors and in the tunnel
    decal_floor('platform_a', 'blood:spatter', -150, 1640 + (EDGE_Y - 1600), DECK_Z, 80, 80, mirror=True)
    decal_floor('service_tunnel', 'blood:pool', -3380, 2380, -384, 96, 96, rot=True, mirror=True)


# ---------------------------------------------------------------- stock decor models (rc1-proven), clip boxes block nav
# IWZ_KIT=1: foreign-zone kit models (cp_disco / cp_final) imported by build-sz2 -KitModels (x64-zt and SDK
# codex/iwzmap-kit-import, 9 models proven textured in cp_iwz by the kit-import agent); KIT_MODELS goes to layout.json
KIT = os.environ.get('IWZ_KIT') == '1'
KIT_MODELS = set()


BENCH = 'cp_disco_worn_subway_bench' if KIT else 'furniture_park_bench_01_blue'
BENCH_CLIP = ((96, 20, 20), (20, 96, 20)) if KIT else ((48, 16, 20), (16, 48, 20))


def decor(zone, model, x, y, z, yaw=0, clip=None):
    DECOR.append({'zone': zone, 'model': model, 'origin': (x, y, z), 'yaw': yaw, 'clip': clip})
    if clip:
        hx, hy, hz = clip
        B.collision_box((x - hx, y - hy, z), (x + hx, y + hy, z + 2 * hz))


# ============================================================================ hero train + track kit (train agent)
# Models from x64-zt-extensions env-model ports (iwz-stage2/train/port/{banzai,kit}), imported by kit_import (zone
# "train"). Kit stack on the channel bed (z -384): ballast top -368, rail base -362.99, rail top -356.31 (= car
# origin), car floor -323 (deck -320). Rails TRACK_CY -/+ 29.61 (gauge 56.5), third rail TRACK_CY - 57.11, its top
# 3.5 above the rail top. Placement spec and evidence: the train agent's report.
TRAIN_SEG = 256
TRAIN_BED = -384
TRAIN_BALLAST_Z = TRAIN_BED + 16
TRAIN_RAIL_TOP = TRAIN_BALLAST_Z + 5.01 + 6.68
TRAIN_CARS = [(300, 0)]          # (car centre x, yaw): one BO3 mp_banzai car, its open door bay faces the platform (+y)
if os.environ.get('IWZ_TRAIN_CARS') == '2':
    TRAIN_CARS = [(300, 0), (-234, 0)]
TRAIN_CAR_HALF = (268, 66.5, 95)  # nav cut half extents (x, y, z/2 above the rail top); detailed clip from the port's boxes
TRAIN_DOOR_X = (-158, -70)       # the car's open +y door bay, car-local x
TRAIN_FLOOR = 33.3               # car floor above its origin (rail top)
TRAIN_CAR_FLOOR_TOP = 35.9       # top of the car's floor clip boxes above its origin (walk surface, deck -320.4)
TRAIN_AISLE = 24                 # aisle lane half width (the port's clip boxes leave y +-26 free above the floor)
TRAIN_AISLE_END = 224            # aisle ends at the end bulkheads (clip boxes from car-local x +-224)
TRAIN_SPEC = {}
BALLAST_TOP_HALF, BALLAST_FOOT_HALF = 62, 94


def ballast_z(y):
    d_ = abs(y - TRACK_CY)
    if d_ <= BALLAST_TOP_HALF:
        return TRAIN_BALLAST_Z
    if d_ >= BALLAST_FOOT_HALF:
        return TRAIN_BED
    return TRAIN_BALLAST_Z - (TRAIN_BALLAST_Z - TRAIN_BED) * (d_ - BALLAST_TOP_HALF) / (BALLAST_FOOT_HALF - BALLAST_TOP_HALF)


def train_kit():
    """Track segments in the platform pit and the service tunnel, buffer stop, hero car(s) with clip boxes and an
    interior flicker lamp, mp_metro platform edge panels along EDGE_Y. TRAIN_SPEC goes to layout.json."""
    cy = TRACK_CY
    bz = TRAIN_BALLAST_Z
    segs = [('platform_a', x) for x in range(-2400, 2400, TRAIN_SEG)] + \
           [('service_tunnel', -2400 - TRAIN_SEG * k) for k in range(1, 6)]
    for zone, x0 in segs:
        decor(zone, 'iwz_track_256', x0, cy, bz, 0)
    # ballast prism: flat top y +-BALLAST_TOP_HALF at the ballast top, shoulders sloping to the bed at +-BALLAST_FOOT_HALF
    # (QA g25t: a vertical 16-unit face could be stepped down but not climbed, by players or zombies)
    for x0, x1 in ((-2400, 2410), (-3600, -2400)):
        t0, t1, f0, f1 = cy - BALLAST_TOP_HALF, cy + BALLAST_TOP_HALF, cy - BALLAST_FOOT_HALF, cy + BALLAST_FOOT_HALF
        B.collision_quad([(x0, t0, bz), (x1, t0, bz), (x1, t1, bz), (x0, t1, bz)], n=(0, 0, 1))
        B.collision_quad([(x0, f0, TRAIN_BED), (x1, f0, TRAIN_BED), (x1, t0, bz), (x0, t0, bz)], n=(0, -0.45, 0.89))
        B.collision_quad([(x0, t1, bz), (x1, t1, bz), (x1, f1, TRAIN_BED), (x0, f1, TRAIN_BED)], n=(0, 0.45, 0.89))
    # buffer stop at the tunnel's west end, buffer heads facing the platform (+x)
    decor('service_tunnel', 'iwz_track_buffer_stop', -3560, cy, bz, 0)
    B.collision_box((-3560, cy - 52, bz), (-3488, cy + 52, bz + 48))
    # platform edge panels (BO3 mp_metro, 128 / 64 long, 9 deep, 48 tall; back face on EDGE_Y, top at the deck)
    for x0, x1 in ((-2192, 1904), (2112, 2400)):
        x = x0
        while x < x1:
            w = 128 if x1 - x >= 96 else 64
            decor('platform_a', 'iwz_platform_edge_%d' % w, x + w / 2, EDGE_Y - 5, DECK_Z - 48, 0)
            x += w
    cars = []
    boxes_path = os.environ.get('IWZ_TRAIN_CAR_BOXES', '')
    boxes = json.load(open(boxes_path))['boxes'] if boxes_path and os.path.isfile(boxes_path) else []
    for cx, yaw in TRAIN_CARS:
        oz = TRAIN_RAIL_TOP
        decor('platform_a', 'iwz_t7e_subway_car_a', cx, cy, oz, yaw)
        hx, hy, hz = TRAIN_CAR_HALF
        fz_ = oz + TRAIN_CAR_FLOOR_TOP
        d0_, d1_ = sorted((cx + TRAIN_DOOR_X[0], cx + TRAIN_DOOR_X[1]))
        top_ = oz + 2 * hz
        B.blockers.append((cx - hx, cy - hy, cx + hx, cy + hy, TRAIN_BED, fz_ - 2))                  # no bed / ballast nav under the car
        B.blockers.append((cx - hx, cy - hy, cx + hx, cy - TRAIN_AISLE, fz_, top_))                   # track-side seats and wall
        B.blockers.append((cx - hx, cy + TRAIN_AISLE, d0_, cy + hy, fz_, top_))                      # platform side, west of the door bay
        B.blockers.append((d1_, cy + TRAIN_AISLE, cx + hx, cy + hy, fz_, top_))                      # platform side, east of the door bay
        B.blockers.append((cx - hx, cy - TRAIN_AISLE, cx - TRAIN_AISLE_END, cy + TRAIN_AISLE, fz_, top_))   # end bulkheads
        B.blockers.append((cx + TRAIN_AISLE_END, cy - TRAIN_AISLE, cx + hx, cy + TRAIN_AISLE, fz_, top_))
        an_ = 'car_aisle_%d' % len(cars)
        dn_ = 'car_door_%d' % len(cars)
        region(an_, 'platform_a', (cx - TRAIN_AISLE_END, cy - 16, cx + TRAIN_AISLE_END, cy + 16), fz_, (0, 0, 0, 0))
        region(dn_, 'platform_a', (d0_, cy + 16, d1_, EDGE_Y), fz_, (0, 0, 0, 0))
        adjacent(an_, dn_)
        adjacent(dn_, 'deck_mid')
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for (a, b) in boxes:     # model-space clip boxes (players, bullets); yaw 0 / 180 keep them axis aligned
            xs = sorted((cx + c * a[0] - s_ * a[1], cx + c * b[0] - s_ * b[1]))
            ys = sorted((cy + s_ * a[0] + c * a[1], cy + s_ * b[0] + c * b[1]))
            B.collision_box((xs[0], ys[0], oz + a[2]), (xs[1], ys[1], oz + b[2]), nav=False)
        # interior: a flickering ceiling fluorescent (BO3 subway fixture, lit / unlit swap) and a broken one, and a
        # weak cold light pool under the lit one
        fz = oz + TRAIN_FLOOR + 118
        FLICKER.append({'zone': 'platform_a', 'origin': (cx - 120, cy, fz), 'yaw': 90,
                        'models': ('iwz_fluo_subway_on', 'iwz_fluo_subway_off')})
        decor('platform_a', 'iwz_fluo_subway_broken', cx + 120, cy, fz, 90)
        LIGHTS.append({'zone': 'platform_a', 'origin': (cx - 120, cy, fz - 20), 'type': 'omni', 'color': (0.78, 0.9, 1.0),
                       'radius': 220, 'intensity': 0.35, 'fixture': 'train_interior'})
        cars.append({'model': 'iwz_t7e_subway_car_a', 'origin': [cx, cy, oz], 'yaw': yaw,
                     'door_bay_world_x': sorted([cx + TRAIN_DOOR_X[0] * c, cx + TRAIN_DOOR_X[1] * c]),
                     'floor_z': oz + TRAIN_FLOOR, 'nav_half': list(TRAIN_CAR_HALF),
                     'dressing_anchors': [[cx + dx, cy + dy, oz + TRAIN_FLOOR] for dx, dy in
                                          ((-200, 40), (-200, -40), (-20, 45), (60, -45), (150, 40), (220, -40))]})
    TRAIN_SPEC.update({'edge_y': EDGE_Y, 'ballast_top_z': bz, 'rail_top_z': TRAIN_RAIL_TOP,
                       'rail_y': [cy - 29.61, cy + 29.61], 'third_rail_y': cy - 57.11,
                       'third_rail_top_z': TRAIN_RAIL_TOP + 3.5, 'segments': [list(s_) for s_ in segs],
                       'buffer': [-3560, cy, bz], 'cars': cars})


if os.environ.get('IWZ_NO_DECOR') != '1':
    decor('ticket_hall', 'trashbin_01_iw6', -1100, 4340, 0, 0, (16, 16, 24))
    decor('ticket_hall', 'trashbin_01_iw6', 360, 4100, 0, 0, (16, 16, 24))
    for x in (-950, 180):
        decor('ticket_hall', BENCH, x, 4340, 0, 90, BENCH_CLIP[0])
    for x in (-2048, -1024, 64, 1300):
        if KIT:     # worn subway bench (cp_disco, 40 x 192): long axis along the wall
            decor('platform_a', 'cp_disco_worn_subway_bench', x, 2350, DECK_Z, 90, (96, 20, 20))
        else:
            decor('platform_a', BENCH, x, 2340, DECK_Z, 90, BENCH_CLIP[0])
    for x in (-1750, 300, 2100):
        decor('platform_a', 'trashbin_01_iw6', x, 2370, DECK_Z, 0, (16, 16, 24))
    decor('maint_corridor', 'dns_locker_set_01', 2620, 1704, -320, 90, (96, 24, 48))
    decor('generator_room', 'equipment_oxygen_tank_01', 2640, 2440, -320, 0, (14, 14, 40))
    decor('generator_room', 'equipment_oxygen_tank_01', 2672, 2440, -320, 30, (14, 14, 40))
    decor('generator_room', 'ammo_crate_01_dust', 3740, 2460, -320, 90, (24, 16, 16))
    decor('generator_room', 'fac_trash_bin', 2640, 3140, -320, 0, (20, 20, 28))
    decor('platform_b', 'trashbin_01_iw6', -2200, 3360, -384, 0, (16, 16, 24))
    decor('platform_b', BENCH, -3000, 3350, -384, 90, BENCH_CLIP[0])
    # control room: CRT monitors on the signal desks, generator room workbench, corridor lockers
    for x0_, y0_ in DESKS:
        for dx in (60, 180):
            decor('control_room', 'zmb_tv_crt_01', x0_ + dx, y0_ + 40, -284, 90)
    decor('generator_room', 'mp_dart_workbench_01', 3770, 2950, -320, 0, (16, 44, 22))
    decor('generator_room', 'dns_locker_set_01', 2780, 3172, -320, 180, (20, 10, 50))
    decor('generator_room', 'dns_locker_set_01', 2822, 3172, -320, 180, (20, 10, 50))
    decor('maint_corridor', 'dns_locker_set_01', 3188, 2100, -320, 90, (10, 20, 50))
    if KIT:
        # parked stock subway train at the dead end of the track pit (static, scriptable mover dropped by kit_import;
        # 780 long along x after yaw 90); its clip box also cuts the pit navmesh, ~100 units stay free on each side
        pass        # (g25) hero car: train agent (TRACK_SPEC); the cp_disco kit car is no longer placed
    if TRAIN:
        train_kit()
        decor('platform_a', 'misc_zom_duffelbag_03', TEDDY_SPOT[0] - 34, TEDDY_SPOT[1] + 12, TEDDY_SPOT[2], 70, (16, 13, 8))
        # ticket hall fare line east of the booth: three turnstiles and a broken one
        for x_, m_ in ((130, 'cp_disco_subway_turnstyle_animated'), (190, 'cp_disco_subway_turnstyle_animated'),
                       (250, 'cp_disco_subway_turnstyle_animated'), (310, 'cp_disco_subway_turnstyle_missing_arm')):
            decor('ticket_hall', m_, x_, 3700, 0, 90, (18, 16, 23))
        # generator room: a second generator unit and oil drums; corridor drum
        decor('generator_room', 'clk_defend_generator_solo', 3300, 3080, -320, 0, (47, 21, 21))
        for x_, y_, a_ in ((3500, 2560, 0), (3540, 2590, 40), (3150, 1730, 15)):
            decor('generator_room' if y_ > 2400 else 'maint_corridor', 'equipment_oil_barrel_military_01', x_, y_, -320, a_, (14, 14, 22))
        # old platform: loose planks by the rubble
        for x_, y_, a_ in ((-3300, 3000, 30), (-3270, 3030, 75)):
            decor('platform_b', 'p7_zm_der_plank_wood_2x12x96', x_, y_, -384, a_)
        # story props from the cp_disco dump (newspapers, quarantine sheets, street barricades, emergency lamps)
        dec_ = lambda *a_, **k_: decor(*a_, **k_)
        dec_('platform_a', 'misc_zom_duffelbag_03', 235, 1712, DECK_Z, 20, (16, 13, 8))
        dec_('platform_a', 'zombies_backpack_dropped', 120, 1690, DECK_Z, 140)
        dec_('platform_a', 'newspaper_single_fn_01', 300, 1760, DECK_Z, 30)
        dec_('platform_a', 'cup_paper_open_iw6', 262, 1745, DECK_Z, 0)
        dec_('platform_a', 'newspaper_stack_fn_01', -1060, 2380, DECK_Z, 80)
        dec_('platform_a', 'container_coffee_mug_01', -990, 2378, DECK_Z, 10)
        # memorial by the sealed street exit: candles and belongings on the floor of the north wall
        for k_, (x_, y_) in enumerate(((-980, 4378), (-955, 4384), (-930, 4376), (-905, 4385), (-880, 4378), (-860, 4386))):
            dec_('ticket_hall', 'p7_candle_01' if k_ % 2 else 'p7_candle_02', x_, y_, 0, 15 * k_)
        dec_('ticket_hall', 'zombies_backpack_dropped_red', -1030, 4370, 0, 200)
        dec_('ticket_hall', 'newspaper_single_fn_01', -820, 4372, 0, 60)
        # quarantine: barricades either side of the street stair, biohazard sheets on the floor
        dec_('ticket_hall', 'cp_disco_street_barricade', -270, 4425, 0, 90, (49, 28, 38))
        dec_('ticket_hall', 'cp_disco_street_barricade', 80, 4425, 0, 90, (49, 28, 38))
        dec_('ticket_hall', 'ls_biohazard_sheet_01', -420, 4300, 0, 25)
        dec_('platform_a', 'ls_biohazard_sheet_02', 700, 1720, DECK_Z, 70)
        # emergency lighting in the service wing: red / amber caged lamps on the walls, each with its own small pool
        for zn_, x_, y_, z_, yaw_, col_ in (('maint_corridor', 2900, 1916, -140, 270, (1.0, 0.25, 0.08)),
                                            ('maint_corridor', 3196, 2150, -140, 180, (1.0, 0.25, 0.08)),
                                            ('generator_room', 2604, 2800, -120, 0, (1.0, 0.45, 0.1)),
                                            ('generator_room', 3200, 3180, -120, 270, (1.0, 0.25, 0.08)),
                                            ('service_tunnel', -3596, 2400, -150, 0, (1.0, 0.25, 0.08)),
                                            ('service_tunnel', -2700, 1220, -150, 90, (1.0, 0.45, 0.1)),
                                            ('ticket_hall', -1196, 3500, 250, 0, (1.0, 0.45, 0.1)),
                                            ('ticket_hall', -900, 4396, 250, 270, (1.0, 0.25, 0.08)),
                                            ('platform_a', 1500, 2396, -150, 270, (1.0, 0.45, 0.1)),
                                            ('platform_a', -1500, 2396, -150, 270, (1.0, 0.25, 0.08)),
                                            ('control_room', 3596, 3600, -100, 180, (1.0, 0.25, 0.08)),
                                            ('platform_b', -2900, 3396, -150, 270, (1.0, 0.45, 0.1)),
                                            # route to the power switch: hall -> stair_a -> platform_a east -> maint door
                                            ('ticket_hall', -380, 3204, 250, 90, (1.0, 0.25, 0.08)),
                                            ('platform_a', 2396, 1960, -150, 180, (1.0, 0.25, 0.08)),
                                            ('platform_a', 2396, 1640, -150, 180, (1.0, 0.25, 0.08))):
            dec_(zn_, 'clk_emergency_light', x_, y_, z_, yaw_)
            LIGHTS.append({'zone': zn_, 'origin': (x_, y_, z_ - 10), 'type': 'omni', 'color': col_, 'radius': 160, 'intensity': 0.6,
                           'fixture': 'emergency'})
        KIT_MODELS.update(d['model'] for d in DECOR if d['model'].startswith(('cp_disco_', 'cp_final_', 'clk_defend', 'equipment_oil_barrel', 'p7_zm_der_plank', 'iwz_')) or d['model'] in STORY_KIT)
    # asset kit (assets/kit/kit_final.json, lead 2026-11-07): free cp_zmb models only. The cp_disco / cp_final models need
    # require,techsets_cp_disco|cp_final in the zone csv, a route not built yet: they are guarded behind IWZ_KIT_DISCO.
    Zh, Zp, Zg, Zc, Zm, Zt, Zb = 'ticket_hall', 'platform_a', 'generator_room', 'control_room', 'maint_corridor', 'service_tunnel', 'platform_b'
    # (g25) stock / kit replacements for the generated box objects
    decor(Zh, 'soda_machine_zmb', 370, 4220, 0, 180, (14, 18, 20))                  # was a red box "vending machine"
    for x_ in (3585, 3735):                                                        # were box control panels (relay 3)
        decor(Zg, 'electrical_control_panel_01', x_, 3172, -320, 270, (20, 10, 40))
    decor(Zh, 'zmb_mobile_ticket_booth', -64, 3700, 0, 270, (43, 18, 23))
    for x_ in (-1130, -1050, -970, -890, -810, -730, -650, -570, -490, -410, -330):
        if KIT:
            decor(Zh, 'cp_disco_subway_turnstyle_animated' if x_ != -650 else 'cp_disco_subway_turnstyle_missing_arm', x_, 3700, 0, 90, (18, 16, 23))
        B.collision_box((x_ - 16, 3684, 0), (x_ + 16, 3716, 40))
    for x_, y_, a_ in ((-260, 4470, 30), (-120, 4520, 200), (-200, 4580, 70), (60, 4570, 300)):     # street stair collapse
        decor(Zh, 'debris_concrete_rubble_pile_01_dark', x_, y_, 0, a_)
    for x0_, y0_ in DESKS:
        for dx_ in (60, 180):
            decor(Zc, 'lab_desk_02', x0_ + dx_, y0_ + 40, -320, 90, (48, 16, 18))
    decor(Zg, 'clk_defend_generator_solo' if KIT else 'zom_machinery_generator_portable_01', GEN[0], GEN[1], -304, 0)
    # a portable set on the floor beside the plinth (the audio layout's generator hum and power cue anchor on it)
    decor(Zg, 'zom_machinery_generator_portable_01', GEN[0] + 170, GEN[1] - 110, -320, 30, (44, 28, 34))
    # ticket hall: soda + token machines on the east wall, mobile ticket booth, pedestrian barriers at the street exit,
    # rubble and trash at the collapsed street stairs
    decor(Zh, 'soda_machine_zmb', 384, 4050, 0, 180, (14, 18, 20))
    for y_ in (3880, 3920):
        decor(Zh, 'park_token_machine', 388, y_, 0, 180, (12, 12, 32))
    decor(Zh, 'zmb_mobile_ticket_booth', -1170, 3640, 0, 0, (18, 43, 23))     # clear of the west-wall posters
    decor(Zh, 'barrier_pedestrian_01', -230, 4380, 0, 0, (40, 6, 20))
    decor(Zh, 'debris_concrete_rubble_pile_01_dark', 40, 4440, 0, 200)
    decor(Zh, 'com_trashbag2_black', -1140, 4360, 0, 30, (16, 16, 20))
    decor(Zh, 'p7_box_cardboard_a_closed', -1080, 4370, 0, 70, (16, 16, 15))
    decor(Zh, 'com_debris_paper_iw6_02', -300, 3450, 0, 25)
    decor(Zh, 'traffic_cone_sml_01', -200, 4330, 0, 20)
    decor(Zh, 'traffic_cone_sml_01', 10, 4335, 0, 70)
    decor(Zh, 'pardon_our_dust_sign', -60, 4430, 0, 270)
    decor(Zh, BENCH, -1150, 4000, 0, 180, BENCH_CLIP[1])
    decor(Zh, BENCH, 350, 3520, 0, 0, BENCH_CLIP[1])
    decor('service_tunnel', 'debris_concrete_rubble_pile_01_dark', -2900, 1250, -384, 60)
    decor('service_tunnel', 'com_junktire', -3560, 2050, -384, 30, (14, 14, 6))
    decor('generator_room', 'electrical_control_box_03', 2700, 2405, -200, 90)
    decor('generator_room', 'electrical_control_box_03', 3300, 2405, -200, 90)
    decor('generator_room', 'electrical_control_box_03', 2605, 2950, -200, 0)
    decor('generator_room', 'ladder01_large_closed', 3790, 2420, -320, 180)
    decor(Zh, 'sign_clock_04', -1000, 4398, 230, 0)          # north wall: face -y
    # platform: PA speakers and clocks on the north wall, trash, paper
    for x_ in (-1536, 0, 1536):
        decor(Zp, 'misc_wall_mounted_loudspeaker_01', x_ + 256, 2398, -110, 270)
    for x_ in (-768, 768):
        decor(Zp, 'sign_clock_04', x_, 2398, -120, 0)
    decor(Zp, 'com_trashbag2_black', -2340, 2350, -320, 10, (16, 16, 20))
    decor(Zp, 'com_debris_paper_iw6_02', 900, 1900, -320, 60)
    decor(Zp, 'office_paper_stack01_iw6', -900, 2360, -320, 0)
    # generator room: control panel and wall pipes on the walls, air handler, emergency shutoff
    decor(Zg, 'electrical_control_panel_01', 2602, 2650, -320, 0, (11, 22, 41))
    decor(Zg, 'wall_mounted_pipes_01', 3796, 2600, -320, 180)
    decor(Zg, 'electrical_industrial_air_vent_box_01', 3600, 2480, -320, 0, (100, 50, 49))
    decor(Zg, 'emergency_shutoff_sm_panel_01', 3460, 2402, -260, 90)
    decor(Zg, 'equipment_old_computer', 3760, 2950, -276, 180)
    # control room: desks with test-pattern monitors, chairs, radio, filing cabinets
    for x0_, y0_ in DESKS:
        decor(Zc, 'chair_folding_iw6', x0_ + 120, y0_ - 40, -320, 90, (12, 11, 19))
        decor(Zc, 'sdf_console_control_panel_08', x0_ + 120, y0_ + 30, -284, 270)
    decor(Zc, 'com_tv2_testpattern', 3460, 3592, -250, 270)
    decor(Zc, 'zmb_frequency_device_radio', 2700, 3592, -250, 270)
    for x_ in (2640, 2680):
        decor(Zc, 'furniture_filing_cabinet', x_, 3990, -320, 270, (17, 8, 17))
    # clutter pass (lead 2026-11-07, contact sheet g18: service wing reads empty): crates, scrap and tanks along walls,
    # clear of the walk lanes, spawners (>= 80) and doors
    decor(Zt, 'ammo_crate_01_dust', -3300, 1250, -384, 10, (24, 16, 16))
    decor(Zt, 'ammo_crate_01_dust', -3250, 1252, -384, 80, (24, 16, 16))
    decor(Zt, 'p7_box_cardboard_a_closed', -3200, 1245, -384, 35, (16, 16, 15))
    decor(Zt, 'ind_debris_metal_scrap_04', -2560, 1250, -384, 120)
    decor(Zt, 'equipment_oxygen_tank_01', -3572, 2150, -384, 0, (14, 14, 40))
    decor(Zt, 'equipment_oxygen_tank_01', -3572, 2185, -384, 50, (14, 14, 40))
    decor(Zt, 'com_trashbag2_black', -3565, 2420, -384, 70, (16, 16, 20))
    decor(Zt, 'com_debris_paper_iw6_02', -3420, 2200, -384, 15)
    decor(Zg, 'ammo_crate_01_dust', 2660, 2880, -320, 0, (24, 16, 16))
    decor(Zg, 'ammo_crate_01_dust', 2660, 2925, -320, 90, (24, 16, 16))
    decor(Zg, 'p7_box_cardboard_a_closed', 2700, 2960, -320, 20, (16, 16, 15))
    decor(Zg, 'com_trashbag2_black', 3760, 2860, -320, 40, (16, 16, 20))
    decor(Zg, 'com_debris_paper_iw6_02', 3000, 3000, -320, 75)
    decor(Zm, 'p7_box_cardboard_a_closed', 2470, 1890, -320, 15, (16, 16, 15))
    decor(Zm, 'com_trashbag2_black', 3175, 2340, -320, 0, (16, 16, 20))
    decor(Zm, 'com_debris_paper_iw6_02', 2650, 1840, -320, 40)
    # maintenance corridor: duct along the ceiling, wall vents, hanging wires
    decor(Zm, 'misc_wall_mounted_fan_01', 3198, 2250, -200, 180)
    decor(Zm, 'hanging_wires_01', 3080, 2000, -96, 0)
    # service tunnel: cones and a construction sign at the buffer stop, tarp on the wall
    for x_, y_ in ((-3400, 1262), (-3370, 1290), (-3420, 1300)):     # beside the walkway, not in the track bed
        decor(Zt, 'traffic_cone_sml_01', x_, y_, -384, 0, (8, 8, 14))
    decor(Zt, 'pardon_our_dust_sign', -3240, 1300, -384, 0, (24, 14, 42))
    decor(Zt, 'dns_fence_tarp_01', -3598, 2100, -360, 90)
    # old platform: trash bags, cardboard, paper
    decor(Zb, 'com_trashbag2_black', -3550, 3350, -384, 0, (16, 16, 20))
    decor(Zb, 'p7_box_cardboard_a_closed', -2500, 3360, -384, 15, (16, 16, 15))
    decor(Zb, 'com_debris_paper_iw6_02', -2900, 2900, -384, 120)
    # ---- art pass 2 ----
    # generator room: kit generator (air handler body on the plinth, control panel, fuse boxes, red pipe runs)
    decor(Zg, 'electrical_control_panel_01', GEN[0] - 150, GEN[1] - 60, -320, 0, (11, 22, 41))
    decor(Zg, 'fac_sort_machine_fuse_box_set_01', 3000, 3182, -320, 180, (18, 7, 37))
    decor(Zg, 'fac_sort_machine_fuse_box_set_01', 3800 - 2, 3050, -320, 90, (7, 18, 37))
    decor(Zg, 'misc_wall_mounted_fan_01', 2602, 3000, -150, 0)
    # maintenance corridor: pipe clusters along both long walls, wall boxes, shutoff panels, fan, ladder, junk
    for x_ in (2560, 2880, 3120):
        decor(Zm, 'electrical_control_box_03', x_, 1681, -280, 90)
    for x_ in (2650, 3000):
        decor(Zm, 'emergency_shutoff_sm_panel_01', x_, 1918, -230, 270)
    decor(Zm, 'misc_wall_mounted_fan_01', 2850, 1918, -150, 270)
    decor(Zm, 'wall_mounted_pipes_01', 2962, 2150, -320, 180)
    decor(Zm, 'ladder01_large_closed', 3196, 2320, -320, 90)
    decor(Zm, 'hanging_wires_01', 2700, 1800, -96, 0)
    decor(Zm, 'ammo_crate_01_dust', 3110, 1700, -320, 0, (18, 30, 15))
    decor(Zm, 'p7_box_cardboard_a_closed', 3150, 1790, -320, 20, (16, 21, 15))
    # service tunnel: work lights (lights table entries below), struts, junk, rubble, cones
    decor(Zt, 'com_junktire', -2840, 1240, -372, 30, (14, 14, 6))
    decor(Zt, 'ind_debris_metal_scrap_04', -3150, 1245, -384, 70)
    decor(Zt, 'debris_concrete_rubble_pile_01_dark', -3500, 2500, -384, 20)
    for y_ in (1700, 2000, 2300):
        decor(Zt, 'electrical_control_box_03', -3599, y_, -290, 0)
    for x_ in (-3300, -2700):
        decor(Zt, 'electrical_control_box_03', x_, 1217, -290, 90)
    # old platform: kit boarded windows, rubble, a dead work light, caution signs and cones
    for x_ in (-3400, -3000, -2600):
        for dx_ in (-41, 41):
            for z_ in (-258, -190):
                decor(Zb, 'zmb_spaceland_zombie_spawn_window_01', x_ + dx_, 3394, z_, 0)
    decor(Zb, 'debris_concrete_rubble_pile_01_dark', -3450, 2700, -384, 40)
    decor(Zb, 'debris_concrete_rubble_pile_01_dark', -2250, 3300, -384, 160)
    decor(Zb, 'pardon_our_dust_sign', -2700, 2680, -384, 270, (24, 14, 42))
    for x_, y_ in ((-2780, 2700), (-2620, 2700)):
        decor(Zb, 'traffic_cone_sml_01', x_, y_, -384, 0, (8, 8, 14))
    decor(Zb, 'barrier_pedestrian_01', -3100, 2680, -384, 0, (40, 6, 20))
    decor(Zb, 'ind_debris_metal_scrap_04', -3300, 3000, -384, 20)
    # kit handrail end posts at both ends of both stair handrails
    for x_ in (-794, -406):
        decor('stair_a', 'barrier_handrail_end_01', x_, 2440, -320, 0, (4, 14, 18))
        decor('stair_a', 'barrier_handrail_end_01', x_, 3096, 0, 180, (4, 14, 18))
    for y_ in (3110, 3394):
        decor('stair_b', 'barrier_handrail_end_01', -2040, y_, -384, 90, (14, 4, 18))
        decor('stair_b', 'barrier_handrail_end_01', -1288, y_, 0, 270, (14, 4, 18))
    # bare-wall fills (sz2_density.py --debug)
    for x_ in (-2300, -1790, -1150, -380, 260, 1020, 1700, 2250):              # track wall boxes and vents
        decor(Zp, 'electrical_control_box_03', x_, 1201, -300, 90)
    for x_ in (-2000, -560, 900, 2100):
        decor(Zp, 'duct_metal_rectangle_vent', x_, 1201, -350, 90)
    decor(Zp, 'electrical_control_panel_01', -2398, 2100, -320, 0, (11, 22, 41))
    decor(Zp, 'emergency_shutoff_sm_panel_01', -2398, 1680, -280, 0)
    decor(Zp, 'electrical_control_box_03', 2398, 2200, -280, 180)
    decor(Zp, 'trashbin_01_iw6', -290, 2365, -320, 0, (17, 17, 24))
    decor(Zp, 'sign_clock_04', 528, 2398, -130, 0)
    decor(Zp, 'trashbin_01_iw6', 1430, 2365, -320, 0, (11, 13, 22))
    decor(Zb, 'com_trashbag2_black', -2110, 2800, -384, 0, (16, 16, 20))
    decor(Zb, 'sign_clock_04', -2066, 2950, -150, 270)       # east wall: face -x
    decor(Zt, 'electrical_control_box_03', -2550, 1583, -290, 270)
    for y_ in (1900, 2300):
        decor(Zt, 'electrical_control_box_03', -3217, y_, -290, 180)
    decor(Zh, BENCH, -900, 3240, 0, 180, BENCH_CLIP[1])
    decor(Zh, BENCH, 20, 3240, 0, 180, BENCH_CLIP[1])
    decor(Zh, 'trashbin_01_iw6', 250, 3236, 0, 0, (11, 13, 22))
    decor(Zh, 'trashbin_01_iw6', -460, 4380, 0, 0, (11, 13, 22))

# ---------------------------------------------------------------- reveals and portals of every opening
for o in OPENINGS:
    zone = SPACE_ZONE[list(o['walls'])[0]]
    reveal(o, zone)
    if o['kind'] == 'open':
        continue
    pr = portal(o)
    for sp in o['walls']:
        # the region names match the space names except the platform deck / pit
        rn = {'platform_deck': 'deck', 'generator': 'generator'}.get(sp, sp)
        adjacent(pr, rn)
adjacent('portal:d_platform_tunnel', 'pit')
adjacent('portal:d_platform_corridor', 'deck_east')

# ---------------------------------------------------------------- optional gallery (materials + lightmap texels)
GALLERY_ITEMS, GALLERY_TEXELS, GALLERY_VIEWS = [], [], []
if GALLERY:
    Z = 'gallery'
    GX0, GX1, GY0, GY1, GZ0, GZ1 = -1600, 1600, 200, 900, 0, 576
    floor(Z, 'conc_floor', GX0, GY0, GX1, GY1, GZ0)
    ceiling(Z, 'conc_painted', GX0, GY0, GX1, GY1, GZ1)
    for side, (ax, fx, fc, s0, s1) in {'w': ('y', GX0, 1, GY0, GY1), 'e': ('y', GX1, -1, GY0, GY1)}.items():
        B.wall_plane(Z, ax, fx, fc, s0, s1, GZ0, GZ1, 'conc_painted')
    B.wall_plane(Z, 'x', GY1, -1, GX0, GX1, GZ0, GZ1, 'com_black' if False else 'black')
    B.wall_plane(Z, 'x', GY0, +1, GX0, GX1, GZ0, GZ1, 'black')
    # material panels on the north wall: 25 columns x 3 rows of 112x112, plus each at 1 m scale reference
    keys = [k for k in MT.MATERIALS if not MT.MATERIALS[k].get('custom') or k.startswith(('lamp', 'tile_', 'metal_silver', 'carriage', 'seat'))]
    keys += [s for s in MT.SIGNS[:3]] + ['poster_mindgap']
    for idx, k in enumerate(keys):
        col, row = idx % 25, idx // 25
        cx = GX0 + 64 + col * 128
        cz = 16 + 56 + row * 128
        if row > 3:
            break
        spec = MT.MATERIALS[k]
        a, b = cx - 56, cx + 56
        y = GY1 - 1
        if spec['su'] <= 1.5:
            B.quad(k, Z, [(a, y, cz - 56), (b, y, cz - 56), (b, y, cz + 56), (a, y, cz + 56)], n=(0, -1, 0), uvs=[(0, 1), (1, 1), (1, 0), (0, 0)], collide=False)
        else:
            B.quad(k, Z, [(a, y, cz - 56), (b, y, cz - 56), (b, y, cz + 56), (a, y, cz + 56)], n=(0, -1, 0), collide=False)
        GALLERY_ITEMS.append({'key': k, 'path': spec['path'], 'center': (cx, y, cz), 'size': 112, 'su': spec['su']})
    # texel panels on the south wall: candidate lightmap texels on a white tile surface
    cands = [tuple(v) for v in LM_DEFAULT.values()]
    for gv in range(8):
        for gu in range(16):
            cands.append((round((gu + 0.5) / 16, 4), round((gv + 0.5) / 8, 4)))
    for idx, uv in enumerate(cands):
        col, row = idx % 33, idx // 33
        cx = GX0 + 48 + col * 96
        cz = 16 + 40 + row * 96
        a, b = cx - 40, cx + 40
        y = GY0 + 1
        B.mesh.quad_uv('w/dt_tile_ceramic_white|gtex', [(b, y, cz - 40), (a, y, cz - 40), (a, y, cz + 40), (b, y, cz + 40)],
                       [(0, 1), (1, 1), (1, 0), (0, 0)], (0, 1, 0), (-1, 0, 0), uv, collide=False)
        GALLERY_TEXELS.append({'uv': uv, 'center': (cx, y, cz), 'size': 80})
    for cx in (-1200, -400, 400, 1200):
        GALLERY_VIEWS.append((cx, 300, 100, 90, -6))      # look north at the material wall (yaw 90 = +y)
        GALLERY_VIEWS.append((cx, 300, 100, 90, -28))
    for cx in (-1200, -400, 400, 1200):
        GALLERY_VIEWS.append((cx, 800, 100, 270, -6))     # look south at the texel wall

# ============================================================================ write world, collision, nav
os.makedirs(sys.argv[2], exist_ok=True)
tpl, out = sys.argv[1], sys.argv[2]

# nav cells: one z per 32-unit cell from the region list (first region wins), minus solid blockers
# art drop-ins at fixed spots (sz2_art_hooks.py; each line is skipped while its image is missing)
ART_PLACE = [
    # name, kind, zone, axis, fixed, facing, s, zc, w, h    (kind: wall decal | sign = framed-less poster quad)
    ('departure_board_suspended', 'sign', 'ticket_hall', 'y', 400, -1, 3800, 200, 256, 64),
    ('notice_closed_layers', 'wall', 'platform_b', 'x', 3400, -1, -2700, -250, 96, 96),
    ('notice_closed_layers', 'wall', 'platform_b', 'x', 3400, -1, -3200, -250, 96, 96),
    ('notice_quarantine', 'sign', 'ticket_hall', 'x', 4400, -1, -480, 130, 64, 96),
    ('notice_quarantine', 'sign', 'platform_a', 'x', 2400, -1, 700, -230, 64, 96),
    ('notice_do_not_restart', 'sign', 'maint_corridor', 'x', 1680, +1, 2800, -220, 64, 96),
    ('poster_missing_1', 'sign', 'ticket_hall', 'y', -1200, +1, 3500, 130, 64, 96),
    ('poster_missing_2', 'sign', 'ticket_hall', 'y', -1200, +1, 3580, 130, 64, 96),
    ('poster_missing_3', 'sign', 'ticket_hall', 'y', -1200, +1, 3660, 130, 64, 96),
    ('poster_missing', 'sign', 'ticket_hall', 'y', -1200, +1, 3580, 130, 64, 96),
    ('poster_missing_a', 'sign', 'ticket_hall', 'y', -1200, +1, 3500, 130, 64, 96),
    ('poster_missing_b', 'sign', 'ticket_hall', 'y', -1200, +1, 3580, 130, 64, 96),
    ('poster_missing_c', 'sign', 'ticket_hall', 'y', -1200, +1, 3660, 130, 64, 96),
    ('poster_missing_b', 'sign', 'control_room', 'y', 2600, +1, 3500, -200, 64, 96),     # Daniel Malone, signal technician
    ('junction_grime', 'wall', 'ticket_hall', 'x', 4400, -1, -1000, 24, 256, 64),
    ('junction_grime', 'wall', 'ticket_hall', 'x', 4400, -1, -700, 24, 256, 64),
    ('junction_grime', 'wall', 'ticket_hall', 'x', 3200, +1, -1000, 24, 256, 64),
    ('junction_grime', 'wall', 'ticket_hall', 'x', 3200, +1, 200, 24, 256, 64),
    ('water_streak', 'wall', 'ticket_hall', 'y', -1200, +1, 4000, 230, 48, 192),
    ('water_streak', 'wall', 'platform_a', 'x', 2400, -1, -800, -150, 48, 192),
    ('water_streak', 'wall', 'platform_b', 'x', 3400, -1, -2450, -150, 48, 192),
]
_placed = set()
for n_, kind_, zn_, ax_, fx_, fc_, s_, zc_, w_, h_ in ART_PLACE:
    k_ = ART_HOOKS.key(n_)
    if not k_ or (n_ == 'poster_missing' and (ART_HOOKS.key('poster_missing_2') or ART_HOOKS.key('poster_missing_b'))):
        continue
    if kind_ == 'sign':
        sign(zn_, k_, ax_, fx_, fc_, s_, zc_, w_, h_, frame=False, depth=0.6)
    else:
        decal_wall(zn_, k_, ax_, fx_, fc_, s_, zc_, w_, h_)
    _placed.add(n_)
if ART_HOOKS.key('clock_face_stopped'):   # a stopped face 0.5 in front of every clock disc (model face at local y -3.024)
    for d_ in DECOR:
        if d_['model'] != 'sign_clock_04':
            continue
        cx_, cy_, cz_ = d_['origin']
        a_ = math.radians(d_.get('yaw', 0))
        nx_, ny_ = round(math.sin(a_)), round(-math.cos(a_))
        if nx_:
            decal_wall(d_['zone'], ART_HOOKS.key('clock_face_stopped'), 'y', cx_ + nx_ * 3.524 - nx_ * 0.4, nx_, cy_, cz_, 17, 17)
        else:
            decal_wall(d_['zone'], ART_HOOKS.key('clock_face_stopped'), 'x', cy_ + ny_ * 3.524 - ny_ * 0.4, ny_, cx_, cz_, 17, 17)
        _placed.add('clock_face_stopped')
if ART_HOOKS.key('grime_mask_floor'):     # generator room diamond plate: one large non-repeating grime / oil mask
    decal_floor('generator_room', ART_HOOKS.key('grime_mask_floor'), 3200, 2790, -320, 760, 760)
    _placed.add('grime_mask_floor')
ART_HOOK_REPORT = {'available': sorted(ART_HOOKS.AVAILABLE), 'placed': sorted(_placed), 'blood_variants': ART_HOOKS.BLOOD_VARIANTS,
                   'aged_signs': ART_HOOKS.AGED_SIGNS}

cells, owner, corner_z = {}, {}, {}
for r in REGIONS:
    x0, y0, x1, y1 = r['rect']
    mw, ms, me, mn = r['m']
    for i in range(int(math.floor(x0 / CELL)) - 1, int(math.ceil(x1 / CELL)) + 1):
        for j in range(int(math.floor(y0 / CELL)) - 1, int(math.ceil(y1 / CELL)) + 1):
            if (i, j) in cells:
                continue
            cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
            if not (x0 + mw <= cx <= x1 - me and y0 + ms <= cy <= y1 - mn):
                continue
            z = r['z'](cx, cy) if callable(r['z']) else r['z']
            blocked = False
            for bx0, by0, bx1, by1, bz0, bz1 in B.blockers:
                if bx0 - 16 < cx < bx1 + 16 and by0 - 16 < cy < by1 + 16 and bz0 < z + 60 and bz1 > z + 1:
                    blocked = True; break
            if blocked:
                continue
            cells[(i, j)] = round(z, 2)
            owner[(i, j)] = r['name']
            if callable(r['z']):
                corner_z[(i, j)] = tuple(round(r['z'](x_, y_), 2) for x_, y_ in ((i * CELL, j * CELL), ((i + 1) * CELL, j * CELL),
                                                                                  ((i + 1) * CELL, (j + 1) * CELL), (i * CELL, (j + 1) * CELL)))


def link(a, b):
    oa, ob = owner[a], owner[b]
    return oa == ob or frozenset((oa, ob)) in ADJ


# ---------------------------------------------------------------- nav seams (QA g25: zombies stood still at the pit
# side of both stairwells and at the stair A top-west corner while the offline graph was connected). The engine
# connects nav areas whose edges coincide, not only the areas the generator links: a pit cell beside the open side of
# a stairwell ramp (25..60 higher), a pit cell under the platform edge (64 lower than the deck) and a hall cell beside
# the stair A landing behind the wall (same height, no door) all became paths into a wall or a cliff, and flat cells
# 16 apart (the train ballast) can be descended but not climbed. Rules:
#   1. train ballast cells sit at the ballast top; the cess cells beside them get a sloped edge up to it (climbable);
#   2. every remaining pair of edge-sharing cells is either linked by design with matching edge corners (step <= 18)
#      or separated: the lower cell (on a tie, the cell of the larger region) is removed, leaving a 32-unit nav gap.
def cell_corners(k):
    z_ = cells[k]
    return corner_z.get(k, (z_, z_, z_, z_))


def edge_heights(k, e):
    c_ = cell_corners(k)        # corners x0y0, x1y0, x1y1, x0y1; edges 0 south (c0-c1), 1 east (c1-c2), 2 north (c2-c3), 3 west (c3-c0)
    return {0: (c_[0], c_[1]), 1: (c_[1], c_[2]), 2: (c_[3], c_[2]), 3: (c_[0], c_[3])}[e]


if TRAIN:
    # nav follows the ballast prism profile (flat top, 32-unit shoulders): centre and corner heights from ballast_z
    _chans = [(-2400, 2410), (-3600, -2400)]
    _nb = 0
    for k in list(cells):
        cx_, cy_ = (k[0] + 0.5) * CELL, (k[1] + 0.5) * CELL
        if not any(x0 <= cx_ <= x1 for x0, x1 in _chans) or abs(cells[k] - PIT_Z) >= 1 or abs(cy_ - TRACK_CY) >= BALLAST_FOOT_HALF + CELL:
            continue
        y0_, y1_ = k[1] * CELL, (k[1] + 1) * CELL
        c_ = (ballast_z(y0_), ballast_z(y0_), ballast_z(y1_), ballast_z(y1_))
        if any(abs(v - PIT_Z) > 0.01 for v in c_):
            cells[k] = round(ballast_z(cy_), 2)
            corner_z[k] = tuple(round(v, 2) for v in c_)
            _nb += 1
    NAV_SEAM_REPORT = {'ballast_cells': _nb}
else:
    NAV_SEAM_REPORT = {'ballast_cells': 0}
_region_size = {}
for k_, o_ in owner.items():
    _region_size[o_] = _region_size.get(o_, 0) + 1
_removed = {}
for _pass in range(4):
    drop = set()
    for k in sorted(cells):
        if k in drop:
            continue
        i_, j_ = k
        for e, nb in ((1, (i_ + 1, j_)), (2, (i_, j_ + 1))):
            if nb not in cells or nb in drop:
                continue
            ha, hb = edge_heights(k, e), edge_heights(nb, (e + 2) % 4)
            ok = link(k, nb) and abs(ha[0] - hb[0]) <= 18 and abs(ha[1] - hb[1]) <= 18 and abs(cells[k] - cells[nb]) <= 18
            if ok:
                continue
            za, zb = sum(ha) / 2, sum(hb) / 2
            if abs(za - zb) > 0.5:
                lo = k if za < zb else nb
            else:
                lo = k if _region_size.get(owner[k], 0) >= _region_size.get(owner[nb], 0) else nb
            drop.add(lo)
            why = '%s|%s' % tuple(sorted((owner[k], owner[nb])))
            _removed[why] = _removed.get(why, 0) + 1
    if not drop:
        break
    for k in drop:
        cells.pop(k, None); owner.pop(k, None); corner_z.pop(k, None)
NAV_SEAM_REPORT['removed'] = _removed
print('nav seams: ballast cells %d, separated %s' % (NAV_SEAM_REPORT['ballast_cells'], ', '.join('%s %d' % kv for kv in sorted(_removed.items()))))

nav, nareas = mapgen.nav_graph(cells, CELL, link, corner_z)
open(os.path.join(out, 'navgraph.bin'), 'wb').write(nav)
REGION_ZONE = {r['name']: r['zone'] for r in REGIONS}

# ============================================================================ gameplay tables
K = {'classname': '157', 'targetname': '822', 'origin': '543', 'angles': '65', 'noteworthy': '638', 'target': '820',
     'area': '60666', 'parameters': '61049', 'model': '497', 'groupname': '502', 'radius': '599', 'linkname': '636',
     'animation': '60661', 'fxid': '60859', 'spawnflags': '687', 'dummy': '51961', 'f60803': '60803'}


def ent(**kw):
    return [(K[k], str(v)) for k, v in kw.items()]


def fmt(p):
    return '%g %g %g' % tuple(p)


STARTS = [(-700, 3880, 0, 270), (-560, 3880, 0, 270), (-420, 3880, 0, 270), (-280, 3880, 0, 270)]
# spawners: (zone, x, y, z, kind, yaw); kind: ground | wall | ceiling (stock recipe, gameplay/stock-spawn-recipe.md)
SPAWNERS = [   # >= 48 from walls/props, inside the zone volume, on the navmesh (sz2_plan.py checks the last two)
    ('ticket_hall', -96, 4416, 0, 'ground', 270), ('ticket_hall', -1120, 4300, 0, 'ground', 315),
    ('ticket_hall', 320, 4320, 0, 'ground', 225), ('ticket_hall', -1100, 3480, 0, 'ground', 45),
    ('ticket_hall', -1136, 3300, 0, 'wall', 0), ('ticket_hall', 336, 3300, 0, 'wall', 180), ('ticket_hall', -400, 4300, 320, 'ceiling', 270),
    ('stair_a', -600, 2460, -320, 'ground', 90), ('stair_a', -700, 2470, -320, 'ground', 90), ('stair_a', -500, 2470, -320, 'ground', 90),
    ('stair_a', -600, 3150, 0, 'ground', 270), ('stair_a', -752, 2800, None, 'wall', 0), ('stair_a', -600, 3140, 288, 'ceiling', 270),
    ('platform_a', 2250, 2000, -320, 'ground', 180), ('platform_a', 1150, 1700, -320, 'ground', 90),
    ('platform_a', -2250, 2000, -320, 'ground', 0), ('platform_a', -1600, 2352, -320, 'wall', 270),
    ('platform_a', 1600, 2352, -320, 'wall', 270), ('platform_a', 800, 2200, -320, 'ground', 270),
    ('platform_a', -1300, 1700, -320, 'ground', 90), ('platform_a', -500, 1700, -320, 'ground', 90),
    ('maint_corridor', 3150, 2300, -320, 'ground', 270), ('maint_corridor', 2550, 1800, -320, 'ground', 0),
    ('maint_corridor', 3080, 1760, -320, 'ground', 180), ('maint_corridor', 3080, 2050, -320, 'ground', 270),
    ('maint_corridor', 2800, 1728, -320, 'wall', 90), ('maint_corridor', 3080, 2150, -96, 'ceiling', 270),
    ('generator_room', 2680, 2480, -320, 'ground', 45), ('generator_room', 3720, 2620, -320, 'ground', 135),
    ('generator_room', 2700, 3100, -320, 'ground', 315), ('generator_room', 3700, 3000, -320, 'ground', 225),
    ('generator_room', 2648, 2700, -320, 'wall', 0), ('generator_room', 3752, 2700, -320, 'wall', 180),
    ('control_room', 2680, 3300, -320, 'ground', 45), ('control_room', 3520, 3300, -320, 'ground', 135),
    ('control_room', 2700, 3900, -320, 'ground', 315), ('control_room', 3500, 3900, -320, 'ground', 225),
    ('control_room', 3100, 3800, -32, 'ceiling', 270), ('control_room', 2648, 3650, -320, 'wall', 0),
    ('service_tunnel', -3500 if not TRAIN else -3450, 1300 if not TRAIN else 1760, -384, 'ground', 0), ('service_tunnel', -2700, 1300, -384, 'ground', 180),
    ('service_tunnel', -3400, 2400, -384, 'ground', 270), ('service_tunnel', -3100 if not TRAIN else -3300, 1500 if not TRAIN else 2000, -384, 'ground', 270),
    ('service_tunnel', -3552, 1900, -384, 'wall', 0), ('service_tunnel', -3000, 1264, -384, 'wall', 90) if not TRAIN else ('service_tunnel', -3220, 2250, -384, 'wall', 180),
    ('platform_b', -3500, 2700, -384, 'ground', 45), ('platform_b', -2150, 2700, -384, 'ground', 135),
    ('platform_b', -3552, 3300, -384, 'wall', 0), ('platform_b', -2700, 3330, -384, 'ground', 270),
    ('platform_b', -2900, 2700, -384, 'ground', 90), ('platform_b', -2800, 3000, -32, 'ceiling', 270),
    ('stair_b', -1990, 3250, -384, 'ground', 0), ('stair_b', -1290, 3300, 0, 'ground', 180),
    ('stair_b', -1990, 3170, -384, 'ground', 0), ('stair_b', -1290, 3170, 0, 'ground', 180),
    ('stair_b', -1600, 3352, None, 'wall', 270), ('stair_b', -1270, 3250, 288, 'ceiling', 180),
]
DOG_SPAWNERS = {   # goon / brute landing spots (2-4 per zone)
    'ticket_hall': [(-1000, 4200), (200, 4200), (-900, 3400)], 'stair_a': [(-600, 3150)],
    'platform_a': [(-2000, 2200), (0, 2250), (2000, 2200), (1200, 1400)], 'maint_corridor': [(2700, 1800), (3080, 2200)],
    'generator_room': [(2800, 2600), (3700, 3000)], 'control_room': [(2800, 3800), (3400, 3400)],
    'service_tunnel': [(-3100, 1400), (-3400, 2000)], 'platform_b': [(-3300, 2900), (-2400, 3100)], 'stair_b': [(-1260, 3250)],
}
IDLE_SPOTS = {z: v[:2] for z, v in DOG_SPAWNERS.items()}
RESPAWNS = {'ticket_hall': [(-500, 4100, 0), (-200, 3450, 0)], 'stair_a': [(-600, 3150, 0), (-600, 2460, -320)],
            'platform_a': [(-200, 2200, -320), (1500, 2200, -320), (-1500, 2200, -320)],
            'maint_corridor': [(3080, 2200, -320), (2700, 1800, -320)], 'generator_room': [(3000, 2600, -320), (3500, 3000, -320)],
            'control_room': [(3100, 3400, -320), (2800, 3700, -320)], 'service_tunnel': [(-3000, 1400, -384), (-3400, 2200, -384)],
            'platform_b': [(-2800, 3000, -384), (-3300, 2800, -384)], 'stair_b': [(-1260, 3250, 0), (-1990, 3250, -384)]}
# interactions: perk machines (relocated stock scriptables), wall buys, magic wheels, power, PaP, quest/EE spots
PERKS = [   # (interaction, scriptable, origin, yaw, zone)
    ('perk_machine_revive', 'perk_machine_up_n_atoms_sign', (370, 3460, 0), 180, 'ticket_hall'),
    ('perk_machine_tough', 'perk_machine_tuff_nuff_sign', (1100, 2370, -320), 270, 'platform_a'),
    ('perk_machine_run', 'perk_machine_racin_stripes_sign', (2630, 2900, -320), 0, 'generator_room'),
    ('perk_machine_rat_a_tat', 'perk_machine_bang_bangs_sign', (-3570, 2800, -384), 0, 'platform_b'),
]
FX = [   # ambient kit FX (assets/kit/fx_kit.tsv, cp_zmb) kept after the engine check sz2_fxcheck.py (run g12-views-a: only
         # vfx_zb_trash_a_ch renders measurably; dust, fog, drips, generator_idle, hanging smoke and bolts were not detected)
    {'fx': 'vfx/iw7/core/zombie/environment/vfx_zb_trash_a_ch', 'origin': (-100, 4440, 10), 'zone': 'ticket_hall', 'repeat': True},
    {'fx': 'vfx/iw7/core/zombie/environment/vfx_zb_trash_a_ch', 'origin': (-2400, 1400, -374), 'zone': 'platform_a', 'repeat': True},
]
WALL_BUYS = [   # (weapon, world model, origin, yaw, zone)
    ('iw7_revolver_zm', 'weapon_kb_revolver_wm', (-1184, 4100, 64), 90, 'ticket_hall'),
    ('iw7_ump45_zml', 'weapon_ump_wm', (-784, 2600, -180), 90, 'stair_a'),
    ('iw7_m4_zm', 'weapon_kb_m4_wm', (-1250, 2384, -256), 0, 'platform_a'),
    ('iw7_sonic_zmr', 'weapon_sonic_wm', (3784, 2700, -256), 90, 'generator_room'),
    ('iw7_m1c_zm', None, (-2600, 3384, -320), 0, 'platform_b'),
]
WHEELS = [   # (template scriptable, origin, yaw, zone): first = start location
    ('pf141_auto1', (600, 2380, -320), 270, 'platform_a'),
    ('pf161_auto1', (380, 3300, 0), 180, 'ticket_hall'),
    ('pf162_auto1', (-2100, 3000, -384), 180, 'platform_b'),
]
POWER = {'origin': (3500, 2420, -270), 'yaw': 90, 'zones': list(ZONES), 'switch_model': 'icbm_electricpanel_switch_02'}
PAP = {'origin': (3104, 4100, -320), 'yaw': 270, 'zone': 'control_room'}
QUEST = {   # Pack-a-Punch relays (gameplay agent: logic), trap and EE spots (data only)
    'relay_1': {'zone': 'platform_a', 'origin': (768, 2027, -300), 'yaw': 90, 'model_yaw': 0},          # column north face
    'relay_2': {'zone': 'platform_b', 'origin': (-3390, 3211, -340), 'yaw': 90, 'model_yaw': 0},        # old booth wall
    'relay_3': {'zone': 'generator_room', 'origin': (3660, 3180, -260), 'yaw': 270, 'model_yaw': 180},  # wall between the stock control panels
    'pap_shutter': {'zone': 'control_room', 'origin': (3104, 4010, -320), 'yaw': 270, 'size': (256, 208)},
    'trap_third_rail_fusebox': {'zone': 'platform_a', 'origin': (-768, 1975, -300), 'yaw': 270, 'model_yaw': 180},
    'trap_third_rail_volume': {'zone': 'platform_a', 'box': (-2400, 1200, -384, 2600, 1600, -350)},
    'teddy_bear': {'zone': 'platform_a', 'origin': TEDDY_SPOT, 'yaw': 90, 'note': 'hero car floor, far track-side anchor, behind a duffel bag' if TRAIN else 'platform floor by the luggage'},
}

ws = mapgen.stock_worldspawn(os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.ents'))
ents, relocations, triggers = [], [], []
layout = {'zones': {}, 'doors': [], 'spawners': [], 'starts': [], 'interactions': [], 'quest': QUEST, 'lights': LIGHTS,
          'signs': SIGNS, 'props': PROPS, 'decor': DECOR, 'geo_props': GEO_PROPS, 'models': MODELS}
for x, y, z, yaw in STARTS:
    ents.append(ent(classname='script_struct', targetname='default_player_start', origin=fmt((x, y, z)), angles='0 %g 0' % yaw))
    layout['starts'].append((x, y, z))
for k in range(8):
    ents.append(ent(classname='trigger_use', targetname='player_use_trigger', origin=fmt((-1100 + 60 * k, 3750, 40)),
                    model='?%d' % (4 + k % 4), dummy='triggermodeldummydefault'))
ents.append(ent(classname='mp_global_intermission', origin='-400 3500 220', angles='10 270 0'))
vm = os.environ.get('IWZ_VOLUME_MODEL')
for k, (zone, zd) in enumerate(ZONES.items()):
    x0, y0, z0, x1, y1, z1 = zd['box']
    triggers.append('28000001 %g %g %g' % ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
    ents.append(ent(classname='info_volume', targetname='spawn_volume', origin=fmt(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)),
                    model=('?' + vm) if vm else '?IWZ%d' % k, linkname=zone, target=zone + '_spawner'))
    layout['zones'][zone] = zd
open(os.path.join(out, 'triggers.txt'), 'w', newline='\n').write('\n'.join(triggers) + '\n')


def floor_z_at(x, y, zone=None):
    i, j = int(math.floor(x / CELL)), int(math.floor(y / CELL))
    return cells.get((i, j))


for zone, x, y, z, kind, yaw in SPAWNERS:
    if kind == 'wall':
        # vent opening at the foot of the nearest wall the spawner faces away from: dark hole + steel frame + vent grille
        fx, fy = round(math.cos(math.radians(yaw))), round(math.sin(math.radians(yaw)))
        wz = floor_z_at(x, y) if z is None else z
        if fx != 0:
            wx = x - fx * 48
            B.wall_plane(zone, 'y', wx + fx * 0.6, fx, y - 28, y + 28, wz + 4, wz + 44, 'vent', collide=False)
            B.slab_y(y - 32, y + 32, wx, wz + 2, wz + 46, 2, 'steel_trim', zone, fx, collide=False, nav=False)
        else:
            wy = y - fy * 48
            B.wall_plane(zone, 'x', wy + fy * 0.6, fy, x - 28, x + 28, wz + 4, wz + 44, 'vent', collide=False)
            B.slab_x(x - 32, x + 32, wy, wz + 2, wz + 46, 2, 'steel_trim', zone, fy, collide=False, nav=False)
    elif kind == 'ceiling':
        B.quad('vent', zone, [(x - 28, y + 28, z - 0.6), (x + 28, y + 28, z - 0.6), (x + 28, y - 28, z - 0.6), (x - 28, y - 28, z - 0.6)], n=(0, 0, -1), collide=False)
        B.box((x - 32, y - 32, z - 3), (x + 32, y + 32, z - 1), {'side': 'steel_trim', 'bottom': 'grate'}, zone, collide=False, nav=False, skip=('top',))
# render world and collision (after the entry-point vents, which are drawn from the spawner table)
nv, ni, ns, wb = mapgen.write_world(B.mesh, os.path.join(out, 'world.bin'))
col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in B.mesh.col]
blob, info = hkcm_write.encode(col, os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.colmap.hkx'), tag=382,
                               max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')))
open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)

for zone, x, y, z, kind, yaw in SPAWNERS:
    if kind != 'ceiling' and floor_z_at(x, y) is not None:
        z = floor_z_at(x, y)
    if z is None:
        z = floor_z_at(x, y)
    e = dict(classname='script_struct', targetname=zone + '_spawner', noteworthy='static', angles='0 %g 0' % yaw)
    if kind == 'ground':
        e.update(origin=fmt((x, y, z + 8)), animation='spawn_ground', parameters='ground_spawn_no_boards', fxid='concrete')
    elif kind == 'wall':
        e.update(origin=fmt((x, y, z + 8)), animation='spawn_wall_low', parameters='no_boards')
    elif kind == 'ceiling':
        e.update(origin=fmt((x, y, z)), animation='spawn_ceiling', parameters='ground_spawn_no_boards', fxid='ceiling')
    ents.append(ent(**e))
    layout['spawners'].append({'zone': zone, 'origin': (x, y, z), 'kind': kind, 'yaw': yaw,
                               'on_nav': floor_z_at(x, y) is not None})
for zone, pts in DOG_SPAWNERS.items():
    for x, y in pts:
        ents.append(ent(classname='script_struct', targetname='dog_spawner', origin=fmt((x, y, (floor_z_at(x, y) or 0) + 8)),
                        angles='0 0 0', radius=66))
for zone, pts in IDLE_SPOTS.items():
    for x, y in pts:
        ents.append(ent(classname='script_struct', targetname='zombie_idle_spot', origin=fmt((x, y, (floor_z_at(x, y) or 0) + 8))))
for zone, pts in RESPAWNS.items():
    for p in pts:
        ents.append(ent(classname='script_struct', targetname='player_respawn_loc', origin=fmt(p), angles='0 0 0'))
ents.append(ent(classname='script_struct', targetname='brute_hide_org', origin='0 0 -2000'))


def istruct(kind, origin, yaw=0, **kw):
    e = dict(classname='script_struct', targetname='interaction', noteworthy=kind, origin=fmt(origin), angles='0 %g 0' % yaw)
    e.update(kw)
    ents.append(ent(**e))
    layout['interactions'].append({'kind': kind, 'origin': origin, 'yaw': yaw, **{k: v for k, v in kw.items()}})


# doors: one struct on each side; each struct's script_area is the zone on the other side
DOORS = []
for o in OPENINGS:
    if o['kind'] != 'door':
        continue
    spaces = list(o['walls'])
    za, zb = o['zones']
    mid = (o['a'] + o['b']) / 2
    p = sorted(o['walls'].values())
    plane = (p[0] + p[1]) / 2
    for sp, other_zone in ((spaces[0], zb), (spaces[1], za)):
        w = o['walls'][sp]
        side = -1 if w == p[0] else 1      # this space lies below (-1) or above (+1) the door plane
        off = plane + side * 40
        org = (mid, off, o['z0'] + 24) if o['axis'] == 'x' else (off, mid, o['z0'] + 24)
        yaw = (90 if side < 0 else 270) if o['axis'] == 'x' else (0 if side < 0 else 180)
        istruct('debris_%d' % o['cost'], org, yaw, area=other_zone, target=o['scriptable'])
    vis = (mid, plane, o['z0']) if o['axis'] == 'x' else (plane, mid, o['z0'])
    relocations.append('%s 0 %g %g %g %g' % (o['scriptable'], vis[0], vis[1], vis[2], 0 if o['axis'] == 'x' else 90))
    # the stock door purchase (interaction_openareas, started by the zombie gametype): a trigger_use 'door_buy' whose
    # target is the debris structs' target; a player's Use on it pays and calls the debris activation. Spaceland's
    # own door trigger models are reused (single box hull at the entity origin, axis aligned): ?41 half 108 x 36 x 96
    # for doors spanning x, ?52 half 30 x 134 x 96 for doors spanning y; field 60803 as on Spaceland's triggers.
    ents.append(ent(classname='trigger_use', targetname='door_buy', target=o['scriptable'], noteworthy='debris_%d' % o['cost'],
                    origin=fmt((vis[0], vis[1], o['z0'] + 96)), model='?41' if o['axis'] == 'x' else '?52',
                    dummy='triggermodeldummydefault', f60803=40))
    DOORS.append({'name': o['name'], 'target': o['scriptable'], 'cost': o['cost'], 'zones': o['zones'], 'axis': 0 if o['axis'] == 'y' else 1,
                  'plane': plane, 'lo': o['a'], 'hi': o['b'], 'z0': o['z0'], 'z1': o['z1']})
layout['doors'] = DOORS
# door blockers: every debris door (and the PaP shutter) gets collision-only script_brushmodel targets, copies of one
# kept template sub-model (sz2_submodels.json, from the compiler's IWZ_KEEP_SUBMODELS log) tiled over the opening;
# stock clear_debris does connectpaths() + notsolid() on them
SUBMODELS = []
_smj = os.environ.get('IWZ_SUBMODELS') or os.path.join(HERE, 'sz2_submodels.json')
if os.path.isfile(_smj):
    SUBMODELS = json.load(open(_smj)).get('blockers', [])
BLOCKERS = []


def door_blockers(targetname, axis, plane, a, b, z0, z1):
    """Tile the opening (span a..b along the wall, z0..z1, wall plane `plane`) with copies of the chosen sub-model."""
    if not SUBMODELS:
        return 0
    sm = SUBMODELS[0]
    (mx, my, mz), (hx, hy, hz) = sm['mid'], sm['half']
    # wide horizontal axis of the shape along the wall: yaw 0 keeps x, yaw 90 swaps
    wide_x = hx >= hy
    span, thick = (2 * hx, 2 * hy) if wide_x else (2 * hy, 2 * hx)
    height = 2 * hz
    nx = max(1, int(math.ceil((b - a + 8) / span)))
    nz = max(1, int(math.ceil((z1 - z0 + 4) / height)))
    count = 0
    for i in range(nx):
        c = a - 4 + span / 2 + i * (b - a + 8 - span) / max(1, nx - 1) if nx > 1 else (a + b) / 2
        for k in range(nz):
            zc = z0 + hz + k * (z1 - z0 + 4 - height) / max(1, nz - 1) if nz > 1 else (z0 + z1) / 2
            # the entity origin is placed so the shape's bounds centre lands on (c, plane, zc)
            if axis == 'x':          # wall along x: span along x, thin along y
                yaw = 0 if wide_x else 90
                lx, ly = (mx, my) if yaw == 0 else (-my, mx)
                org = (c - lx, plane - ly, zc - mz)
            else:                    # wall along y: span along y, thin along x
                yaw = 90 if wide_x else 0
                lx, ly = (mx, my) if yaw == 0 else (-my, mx)
                org = (plane - lx, c - ly, zc - mz)
            ents.append(ent(classname='script_brushmodel', targetname=targetname, model=sm['model'], origin=fmt(org),
                            angles='0 %g 0' % yaw, spawnflags='1', dummy=sm.get('dummy', 'ScriptBrushModelDummyFixed')))
            BLOCKERS.append({'target': targetname, 'model': sm['model'], 'origin': org, 'yaw': yaw})
            count += 1
    return count


for o in OPENINGS:
    if o['kind'] != 'door':
        continue
    p_ = sorted(o['walls'].values())
    door_blockers(o['scriptable'], o['axis'], (p_[0] + p_[1]) / 2, o['a'], o['b'], o['z0'], o['z1'])
_pa = OP['a_control_pap']
door_blockers('iwz_pap_shutter', 'x', 4008, _pa['a'], _pa['b'], _pa['z0'], _pa['z1'])
layout['blockers'] = BLOCKERS
# power
istruct('generator', POWER['origin'], POWER['yaw'], parameters='power_all', target='iwz_power_switch')
ents.append(ent(classname='script_model', targetname='iwz_power_switch', model=POWER['switch_model'], noteworthy='-pitch',
                origin=fmt((POWER['origin'][0], POWER['origin'][1] - 16, POWER['origin'][2])), angles='75 %g 0' % POWER['yaw']))
for weapon, wm, origin, yaw, zone in WALL_BUYS:
    if wm:
        istruct(weapon, origin, yaw, groupname='wall_buy', model=wm, radius=256)
    else:
        istruct(weapon, origin, yaw, groupname='wall_buy', radius=256)
for kind, scriptable, origin, yaw, zone in PERKS:
    istruct(kind, origin, yaw, parameters='requires_power')
    relocations.append('%s 0 %g %g %g %g' % (scriptable, origin[0], origin[1], origin[2], yaw))
istruct('weapon_upgrade', PAP['origin'], PAP['yaw'], parameters='requires_power', target='iwz_pap_spot')
relocations.append('pap_machine 0 %g %g %g %g' % (PAP['origin'][0], PAP['origin'][1] + 10, PAP['origin'][2], PAP['yaw']))
ents.append(ent(classname='script_struct', targetname='iwz_pap_spot', origin=fmt((PAP['origin'][0], PAP['origin'][1] + 20, PAP['origin'][2] + 14)),
                angles='0 %g 0' % PAP['yaw'], model='weapon_e_ak47_rare_wm'))
for scriptable, origin, yaw, zone in WHEELS:
    relocations.append('%s 0 %g %g %g %g' % (scriptable, origin[0], origin[1], origin[2], yaw))
    # spinner struct (stock offset: 55.6 above the base, 8 units in front) and an out_of_order stand-in
    fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    ents.append(ent(classname='script_struct', noteworthy='spinner', model='zmb_magic_wheel_spinner',
                    origin=fmt((origin[0] + 8 * fx, origin[1] + 8 * fy, origin[2] + 55.6)), angles='0 %g 0' % yaw))
    ents.append(ent(classname='script_model', noteworthy='out_of_order', model='tag_origin', origin=fmt((origin[0], origin[1], origin[2] + 37))))
    # wheel_fx_spot: the stock wheel spawns the won weapon here (Spaceland: spinner + 14 to the wheel's right, 0.4 lower)
    sx_, sy_ = origin[0] + 8 * fx, origin[1] + 8 * fy
    rx_, ry_ = math.cos(math.radians(yaw - 90)), math.sin(math.radians(yaw - 90))
    ents.append(ent(classname='script_struct', targetname='wheel_fx_spot', origin=fmt((sx_ + 14 * rx_, sy_ + 14 * ry_, origin[2] + 55.2)),
                    angles='0 %g 0' % yaw))
    layout['interactions'].append({'kind': 'magic_wheel', 'scriptable': scriptable, 'origin': origin, 'yaw': yaw, 'zone': zone})
for name, q in QUEST.items():
    if 'origin' in q:
        ents.append(ent(classname='script_struct', targetname='iwz_' + name, origin=fmt(q['origin']), angles='0 %g 0' % q['yaw']))
    if 'model_yaw' in q and not name.startswith('relay_'):
        ents.append(ent(classname='script_model', targetname='iwz_' + name + '_model', model='fac_sort_machine_fuse_box_set_01',
                        origin=fmt(q['origin']), angles='0 %g 0' % q['model_yaw']))
    if name.startswith('relay_'):
        # kit relay: wall panel icbm_electricpanel9_off (red state) / _on (green state) with a red beacon on top;
        # the panel's front is its local +x, the wall face is the quest origin
        o_ = q['origin']
        ents.append(ent(classname='script_model', targetname='iwz_' + name + '_panel', model='icbm_electricpanel9_off',
                        origin=fmt((o_[0], o_[1], o_[2] + 40)), angles='0 %g 0' % q['yaw']))
        ents.append(ent(classname='script_model', targetname='iwz_' + name + '_beacon', model='beacon_light_plasticcase_red_on',
                        origin=fmt((o_[0], o_[1], o_[2] + 54)), angles='0 %g 0' % q['yaw']))
# stock fast-travel / hidden-room init runs on every map: give its lookups parked entities so its threads idle
# instead of looping on undefined (gameplay REPORT defect 7)
for tn in ('hidden_room_portal', 'center_portal', 'fast_travel_tube_start', 'fast_travel_tube_end', 'hidden_travel_tube_start',
           'hidden_travel_tube_end'):
    ents.append(ent(classname='script_model', targetname=tn, model='tag_origin', origin='0 0 -3000', angles='0 0 0'))
ents.append(ent(classname='script_struct', targetname='hidden_room_spot', origin='0 0 -3000', angles='0 0 0'))
for f_ in FLICKER:    # flickering fluorescent: the lit model, swapped with the unlit one by the level script
    on_, off_ = f_.get('models', ('mp_dart_lightfluo_on', 'mp_dart_lightfluo'))
    kw_ = {'noteworthy': on_ + '|' + off_} if 'models' in f_ else {}
    ents.append(ent(classname='script_model', targetname='iwz_flicker', model=on_, origin=fmt(f_['origin']),
                    angles='0 %g 0' % f_['yaw'], **kw_))
    if 'models' in f_:
        ents.append(ent(classname='script_model', model=off_, origin='0 0 -3000', angles='0 0 0'))
for m_ in ('icbm_electricpanel9_on', 'beacon_light_plasticcase_red_off', 'mp_dart_lightfluo'):      # swapped models: keep them loaded
    ents.append(ent(classname='script_model', model=m_, origin='0 0 -3000', angles='0 0 0'))
# PaP shutter: two rolling steel gates (stock gate_warehouse_refinery_01, 156 x 12 x 186, origin at its corner) in the
# arch between the control room and the PaP alcove, raised by the relay quest; collision from door blockers below
PAP_ARCH = OP['a_control_pap']
for gx in (PAP_ARCH['a'] - 28, PAP_ARCH['a'] - 28 + 156):
    ents.append(ent(classname='script_model', targetname='iwz_pap_shutter', model='gate_warehouse_refinery_01',
                    origin=fmt((gx, 4002, PAP_ARCH['z0'])), angles='0 0 0'))
# IWZ_SMODELS=1: template-zone decor becomes compiled static models (smodels.txt, x64-zt codex/iwzmap-static-models
# a99270f merged in door-brushmodels bd5e7fb): drawn and bullet-blocking without entity cost; player / zombie blocking
# stays with the decor clip boxes (world collision + nav cut). Foreign-zone kit models stay script_models (kit_import).
SMODELS = os.environ.get('IWZ_SMODELS') == '1'
# compiled static models only for models that have a stock static instance in the template: the compiler gives a model
# without one another model's draw settings. g19 / g20 / g21 hit an access violation at iw7_ship+0xDCE6E7 (material #4
# of lod 0 read past a model's material list, RAX = float data) and every one of them had these borrowing models
# static: ammo_crate_01_dust, debris_concrete_rubble_pile_01_dark, ind_debris_metal_scrap_04, pardon_our_dust_sign,
# zom_machinery_generator_portable_01 (g21 had no kit model). They stay script_models. IWZ_SMODEL_STOCK_CSV: the
# static-models agent's table of the 17,010 cp_zmb static models.
SMODEL_STOCK = None
_smc = os.environ.get('IWZ_SMODEL_STOCK_CSV', r'C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\smodels\stock-smodels.csv')
# x64-zt door-brushmodels (static-model donor fix): the compiler now picks a donor with the same lod / surface layout
# and refuses a model without one, so every template model can be static again; IWZ_SMODEL_STOCK_ONLY=1 restores the
# stock-instance filter (the g22-g24 workaround).
if SMODELS and os.environ.get('IWZ_SMODEL_STOCK_ONLY') == '1' and os.path.isfile(_smc):
    import csv as _csv
    SMODEL_STOCK = set(r['model'] for r in _csv.DictReader(open(_smc)))
# models without a light grid lit template instance and without a same-layout donor: the compiler refuses them as
# static models (compile-only probe with IWZ_SMODEL_ALLOW_SHAPE_MISMATCH=1 on g25, 2026-11-08); script_models instead
SMODEL_NO_DONOR = {'pardon_our_dust_sign'}
smodel_lines = []
for d in DECOR:
    if os.environ.get('IWZ_KIT_ONLY') and d['model'] in KIT_MODELS and d['model'] != os.environ['IWZ_KIT_ONLY']:
        continue     # kit crash bisect: one imported model per build
    if os.environ.get('IWZ_KIT_BASELINE') == '1' and d['model'] in KIT_MODELS:
        continue     # kit proof baseline: the same map (placements, clips, views) without the imported models
    if SMODELS and d['model'] not in KIT_MODELS and d['model'] not in SMODEL_NO_DONOR and (SMODEL_STOCK is None or d['model'] in SMODEL_STOCK):
        x_, y_, z_ = d['origin']
        smodel_lines.append('%s %g %g %g 0 %g 0 1' % (d['model'], x_, y_, z_, d.get('yaw', 0)))
        d['static'] = True
        continue
    ents.append(ent(classname='script_model', model=d['model'], origin=fmt(d['origin']), angles='0 %g 0' % d.get('yaw', 0)))
if smodel_lines:
    open(os.path.join(out, 'smodels.txt'), 'w', newline='\n').write('\n'.join(smodel_lines) + '\n')
# IWZ_LIGHTS=1: real primary lights (lights.txt) for coloured accents the bake does not carry: the tunnel signal lamps
# throw a small red / green pool on the portal (stock intensity units: thousands; x10 of 3000 is clearly visible)
if os.environ.get('IWZ_LIGHTS') == '1':
    light_txt = []
    for l in LIGHTS:
        fx = l.get('fixture')
        if fx in ('lamp_red', 'lamp_green'):
            r_, g_, b_ = (1.0, 0.12, 0.06) if fx == 'lamp_red' else (0.12, 1.0, 0.25)
            x_, y_, z_ = l['origin']
            light_txt.append('omni %g %g %g %.2f %.2f %.2f 6000 72' % (x_, y_, z_, r_, g_, b_))
    # the EE bear on the luggage rack reads dark against the lit car ceiling (audio agent): a small warm fill light
    # in the aisle just below the rack, its radius limited to the bear
    if not TRAIN:      # the hidden bear (in the car) gets no fill light
        bx_, by_, bz_ = TEDDY_SPOT
        light_txt.append('omni %g %g %g 1.00 0.85 0.65 20000 110' % (bx_, by_ + 40, bz_ - 20))
    open(os.path.join(out, 'lights.txt'), 'w', newline='\n').write('\n'.join(light_txt) + '\n')
    # group of each lights.txt line (signal lamps: emergency; the bear fill light: power)
    json.dump({'lines': [{'line': k_, 'group': 'power' if t_.endswith(' 20000 110') else 'emergency'}
                         for k_, t_ in enumerate(light_txt)]}, open(os.path.join(out, 'lights_groups.json'), 'w'), indent=1)
open(os.path.join(out, 'scriptables.txt'), 'w', newline='\n').write('\n'.join(relocations) + '\n')
open(os.path.join(out, 'ents.txt'), 'w', newline='\n').write(mapgen.ents_text(ws, ents))

# ============================================================================ lighting.txt (light grid relight for models)
light_lines = ['ambient 0.20 0.20 0.22 0.40']     # art pass 5: lower fill for models (darker corners)
for zone, zd in ZONES.items():
    x0, y0, z0, x1, y1, z1 = zd['box']
    r, g, b, up = zd['probe']
    light_lines.append('room %d %d %d %d %d %d %.3f %.3f %.3f %.2f' % (x0 - 64, y0 - 64, z0 - 64, x1 + 64, y1 + 64, z1 + 64, r, g, b, up))
open(os.path.join(out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(light_lines) + '\n')
# reflection probe rooms for the compiler (IWZ_PROBES=neutral): one per zone, its box and ambient colour; kept apart from
# lighting.txt because a reused bake brings its own lighting.txt (thousands of chart rooms)
_pc = os.path.join(HERE, 'probe_colours.json')
PROBE_RGB = json.load(open(_pc))['zones'] if os.path.isfile(_pc) and os.environ.get('IWZ_PROBE_MEASURED', '1') == '1' else {}
open(os.path.join(out, 'probes.txt'), 'w', newline='\n').write(''.join(
    'room %d %d %d %d %d %d %.3f %.3f %.3f %.2f\n' % (*zd['box'], *(PROBE_RGB.get(zn, zd['probe'][:3])), zd['probe'][3])
    for zn, zd in ZONES.items()))

# ============================================================================ level script with generated tables
gsc = open(os.path.join(HERE, 'cp_iwz2.gsc')).read()
door_lines = ['    doors[doors.size] = iwz_door( "%s", "%s", %d, %g, %g, %g, %g, %g );' % (d['name'], d['target'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1'])
              for d in DOORS]
link_lines = ['    links[links.size] = [ "%s", "%s" ];' % l for l in ZONE_LINKS]
gsc = gsc.replace('//@DOORS@', '\n'.join(door_lines)).replace('//@LINKS@', '\n'.join(link_lines))
gsc = gsc.replace('//@INITIAL@', 'level.initial_active_volumes = [ %s ];' % ', '.join('"%s"' % z for z in INITIAL_ZONES))
gsc = gsc.replace('//@WHEEL@', '"%s"' % WHEELS[0][3])
gsc = gsc.replace('//@FXLOAD@', chr(10).join('    level._effect["iwz_fx_%d"] = loadfx( "%s" );' % (k, f['fx']) for k, f in enumerate(FX)))
gsc = gsc.replace('//@FXPLACE@', chr(10).join('    fx[fx.size] = iwz_fx( "iwz_fx_%d", ( %g, %g, %g ), %d );' % (k, *f['origin'], 1 if f['repeat'] else 0)
                                         for k, f in enumerate(FX)))
if os.environ.get('IWZ_AUDIO') == '1':     # audio module added by build-sz2.ps1 -AudioSdk (audio agent's add_audio.py)
    gsc = gsc.replace('//@AUDIO@', r'level thread scripts\cp\maps\cp_iwz\cp_iwz_audio_layout::init();')
tb = QUEST['trap_third_rail_volume']['box']
gsc = gsc.replace('//@TRAPMIN@', '( %g, %g, %g )' % tb[:3]).replace('//@TRAPMAX@', '( %g, %g, %g )' % tb[3:])
gsc = gsc.replace('//@TRAPRAILY@', '%g' % THIRD_Y)
gsc = gsc.replace('//@TRAPRAILZ@', '%g' % ((-356.31 + 3.5) if TRAIN else (PIT_Z + 12)))   # train kit third rail top / old bed line
open(os.path.join(out, 'cp_iwz.gsc'), 'w', newline='\n').write(gsc)

# ============================================================================ capture views, walk path, summaries
VIEWS = {   # 5 per zone: (x, y, z eye-ish origin of the player, yaw, pitch)
    'ticket_hall': [(-1100, 4300, 0, 315, 5), (300, 3300, 0, 135, 5), (-500, 3880, 0, 270, 10), (-96, 4060, 0, 90, -6), (-1100, 3300, 0, 30, 0)],
    'stair_a': [(-600, 3150, 0, 270, 20), (-600, 2460, -320, 90, -20), (-760, 2800, -160, 300, 10), (-600, 3240, 0, 270, 10), (-600, 2440, -320, 270, 0)],
    'platform_a': [(-2300, 2300, -320, 345, 5), (2300, 2300, -320, 195, 5), (-200, 2200, -320, 270, 10), (600, 1700, -320, 200, 6), (-1500, 1300, -384, 0, -5)],
    'maint_corridor': [(2460, 1800, -320, 0, 0), (3150, 1760, -320, 90, 0), (3080, 2350, -320, 270, 0), (2900, 1720, -320, 180, 0), (3150, 2000, -320, 180, 5)],
    'generator_room': [(2660, 2440, -320, 40, 5), (3740, 3140, -320, 220, 5), (3000, 2800, -320, 0, 0), (3080, 2440, -320, 90, 0), (3600, 2500, -320, 135, 0)],
    'control_room': [(2660, 3260, -320, 45, 5), (3540, 3940, -320, 225, 5), (3104, 3300, -320, 90, 0), (3104, 3950, -320, 270, 0), (2700, 3900, -320, 330, 0)],
    'service_tunnel': [(-2460, 1400, -384, 180, 0), (-3500, 1300, -384, 0, 0), (-3400, 1700, -384, 90, 0), (-3400, 2540, -384, 270, 0), (-3000, 1500, -384, 200, 0)],
    'platform_b': [(-3540, 2660, -384, 40, 5), (-2120, 3340, -384, 220, 5), (-2800, 3000, -384, 90, 0), (-3400, 3000, -384, 0, 0), (-2120, 2700, -384, 150, 0)],
    'stair_b': [(-2020, 3250, -384, 0, -15), (-1260, 3300, 0, 180, 20), (-1700, 3250, -200, 0, -10), (-1150, 3300, 0, 180, 15), (-1600, 3150, -150, 180, 10)],
}
# kit check views (IWZ_KIT): one view per imported model, from open floor 200+ units away, aimed at the model's middle
if KIT:
    VIEWS['kit'] = []
    _done = set()
    for d in DECOR:
        if d['model'] not in KIT_MODELS or d['model'] in _done:
            continue
        mx_, my_, mz_ = d['origin']
        c_ = d.get('clip') or (24, 24, 24)
        dist_ = max(c_[0], c_[1]) + 200
        for ang_ in (90, 270, 0, 180, 45, 135, 225, 315):
            vx_ = mx_ + dist_ * math.cos(math.radians(ang_)); vy_ = my_ + dist_ * math.sin(math.radians(ang_))
            vz_ = floor_z_at(vx_, vy_)
            if vz_ is None or abs(vz_ - mz_) > 80:
                continue
            # the camera must stand in the model's own zone (g23: the generator was viewed from the control room,
            # through the wall)
            zb_ = ZONES[d['zone']]['box']
            if not (zb_[0] + 32 <= vx_ <= zb_[3] - 32 and zb_[1] + 32 <= vy_ <= zb_[4] - 32):
                continue
            yaw_ = (ang_ + 180) % 360
            pitch_ = -math.degrees(math.atan2(mz_ + c_[2] - (vz_ + 60), dist_))
            VIEWS['kit'].append((round(vx_), round(vy_), vz_, yaw_, round(pitch_, 1)))
            _done.add(d['model'])
            break
# interaction check views (lead g24 review: doors, buys and paths must stay lit in a darker map): one view per
# interaction struct, from open floor 110 units in front of it, aimed at it; sz2_mood.py measures the centre window
VIEWS['interact'] = []
for it in layout['interactions']:
    ox_, oy_, oz_ = it['origin']
    for sgn_ in (-1, 1):
        a_ = math.radians(it.get('yaw', 0))
        vx_, vy_ = ox_ + sgn_ * 110 * math.cos(a_), oy_ + sgn_ * 110 * math.sin(a_)
        vz_ = floor_z_at(vx_, vy_)
        if vz_ is None or abs(vz_ - (oz_ - 24)) > 120:
            continue
        yaw_ = math.degrees(math.atan2(oy_ - vy_, ox_ - vx_)) % 360
        pitch_ = -math.degrees(math.atan2(oz_ - (vz_ + 60), 110))
        VIEWS['interact'].append((round(vx_), round(vy_), vz_, round(yaw_, 1), round(pitch_, 1)))
        break
WALK = [   # waypoint path through every zone (doors are opened by the walk fixture first); stair points at the ramp ends
    (-528, 3880, 0), (-528, 3500, 0), (-600, 3250, 0), (-600, 3150, 0), (-600, 3088, 0), (-600, 2448, -320), (-600, 2440, -320),
    (-600, 2200, -320), (0, 2200, -320), (0, 1700, -320), (1000, 1800, -320), (2300, 1800, -320),
    (2600, 1800, -320), (3080, 1800, -320), (3080, 2300, -320), (3080, 2500, -320), (3100, 2900, -320), (3100, 3250, -320),
    (2980, 3450, -320), (2980, 3700, -320), (3104, 3950, -320), (2980, 3700, -320), (2980, 3450, -320), (3100, 3250, -320),
    (3080, 2300, -320), (3080, 1800, -320), (2600, 1800, -320), (1880, 1800, -320), (1880, 1680, -320), (1940, 1680, -320),
    (2084, 1680, -384), (2090, 1560, -384), (2080, 1250, -384), (1000, 1250, -384), (-500, 1250, -384), (-1500, 1260, -384), (-2350, 1400, -384),
    # pit <-> deck through the west stairwell (QA g18: service_tunnel -> platform_a deck route), then into the tunnel
    (-2330, 1560, -384), (-2380, 1680, -384), (-2372, 1680, -384), (-2228, 1680, -320), (-2150, 1680, -320), (-2228, 1680, -320),
    (-2372, 1680, -384), (-2380, 1680, -384), (-2330, 1560, -384), (-2350, 1400, -384),
    (-2500, 1400, -384), (-3400, 1400, -384), (-3400, 2000, -384), (-3400, 2650, -384), (-2800, 3000, -384), (-2120, 3250, -384),
    (-2032, 3250, -384), (-1296, 3250, 0), (-1250, 3300, 0), (-1150, 3300, 0), (-528, 3500, 0), (-528, 3880, 0),
]
for o in OPENINGS:
    pass
# local fixture with the capture views, walk path and zone probes baked in
fx = open(os.path.join(HERE, 'fixtures', 'sz2_local.gsc')).read()
# walkthrough capture (coordinator 2026-11-07): nav cells on a 256-unit grid whose 5x5 cell neighbourhood is all
# walkable (camera clear of walls, review C stair_b_3 clipping), at feet height (the engine adds the eye), 4 yaws each.
# Frame names carry zone, position and yaw: wc_<zone>_<x>_<y>_y<yaw>. Captured by the fixture mode "walkcap" in parts
# (dvar paris_iwz_wc_part "k/n") so each private run stays short.
WALKCAP = []
WC_STEP = 8         # cells (8 x 32 = 256 units)
for (i, j), z in sorted(cells.items()):
    if i % WC_STEP or j % WC_STEP:
        continue
    if not all((i + di, j + dj) in cells and abs(cells[(i + di, j + dj)] - z) < 20 * max(1, abs(di), abs(dj)) for di in range(-2, 3) for dj in range(-2, 3)):
        continue
    zone = REGION_ZONE.get(owner[(i, j)], owner[(i, j)])
    x, y = (i + 0.5) * CELL, (j + 0.5) * CELL
    for yaw in (0, 90, 180, 270):
        WALKCAP.append(('wc_%s_%d_%d_y%d' % (zone, x, y, yaw), x, y, z + 1, yaw))
wc_lines = ['    wc[wc.size] = iwz_view( "%s", %g, %g, %g, %g, 0 );' % v for v in WALKCAP]
view_lines = []
for zone, vs in VIEWS.items():
    for k, (x, y, z, yaw, pitch) in enumerate(vs):
        view_lines.append('    views[views.size] = iwz_view( "%s_%d", %g, %g, %g, %g, %g );' % (zone, k, x, y, z, yaw, pitch))
# sign check views: for each sign / poster image, one wall-mounted instance seen straight on from the floor in front
SIGN_VIEWS, SIGN_VIEW_LIST, _seen = {}, [], set()
for si, sg in enumerate(SIGNS):
    if sg['image'] in _seen:
        continue
    (cx, cy, zc), (w, h) = sg['center'], sg['size']
    nx, ny = (0, sg['facing']) if sg['axis'] == 'x' else (sg['facing'], 0)
    sx, sy = (cx, cy + sg['facing'] * sg['off']) if sg['axis'] == 'x' else (cx + sg['facing'] * sg['off'], cy)
    for d in (max(160, 1.3 * w), 220, 160, 120, 300):
        vx, vy = sx + nx * d, sy + ny * d
        fz = floor_z_at(vx, vy)
        if fz is None:
            continue
        yaw = math.degrees(math.atan2(-ny, -nx)) % 360
        pitch = -math.degrees(math.atan2(zc - (fz + 60), d))
        SIGN_VIEWS[len(SIGN_VIEW_LIST)] = si
        SIGN_VIEW_LIST.append((round(vx, 1), round(vy, 1), fz, round(yaw, 2), round(pitch, 2)))
        _seen.add(sg['image'])
        break
# FX check views: one per FX, ~300 units away on the floor, looking at it (captured with the FX held, then running)
FX_VIEWS = []
for fi, f in enumerate(FX):
    fx_, fy_, fz_ = f['origin']
    for dx_, dy_ in ((300, 0), (-300, 0), (0, 300), (0, -300), (200, 200), (-200, -200), (200, -200), (-200, 200)):
        gz_ = floor_z_at(fx_ + dx_, fy_ + dy_)
        if gz_ is None:
            continue
        yaw_ = math.degrees(math.atan2(-dy_, -dx_)) % 360
        pitch_ = -math.degrees(math.atan2(fz_ - (gz_ + 60), math.hypot(dx_, dy_)))
        FX_VIEWS.append((fi, (fx_ + dx_, fy_ + dy_, gz_, round(yaw_, 2), round(pitch_, 2))))
        break
fxv_lines = ['    fxviews[fxviews.size] = iwz_view( "fx_%d", %g, %g, %g, %g, %g );' % (fi, *v) for fi, v in FX_VIEWS]
FLK_VIEWS = []     # flicker check views: lamp seen from the floor 260 units away
for li, f in enumerate(FLICKER):
    lx_, ly_, lz_ = f['origin']
    for dx_, dy_ in ((260, 0), (-260, 0), (0, 260), (0, -260), (180, 180), (-180, -180)):
        gz_ = floor_z_at(lx_ + dx_, ly_ + dy_)
        if gz_ is None:
            continue
        FLK_VIEWS.append((li, (lx_ + dx_, ly_ + dy_, gz_, round(math.degrees(math.atan2(-dy_, -dx_)) % 360, 2),
                               round(-math.degrees(math.atan2(lz_ - (gz_ + 60), math.hypot(dx_, dy_))), 2))))
        break
fxv_lines += ['    flkviews[flkviews.size] = iwz_view( "flk_%d", %g, %g, %g, %g, %g );' % (li, *v) for li, v in FLK_VIEWS]
for k, (x, y, z, yaw, pitch) in enumerate(SIGN_VIEW_LIST):
    view_lines.append('    views[views.size] = iwz_view( "sign_%d", %g, %g, %g, %g, %g );' % (k, x, y, z, yaw, pitch))
for k, (x, y, z, yaw, pitch) in enumerate(GALLERY_VIEWS):
    view_lines.append('    views[views.size] = iwz_view( "gallery_%d", %g, %g, %g, %g, %g );' % (k, x, y, z, yaw, pitch))
walk_lines = ['    walk[walk.size] = ( %g, %g, %g );' % tuple(p) for p in WALK]
probe_lines = []
for r in REGIONS:
    if r['name'].startswith('portal:') or r['zone'] == 'gallery':
        continue
    x0, y0, x1, y1 = r['rect']
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cz = floor_z_at(cx, cy)
    if cz is None:
        continue
    probe_lines.append('    probes[probes.size] = iwz_probe( "%s", %g, %g, %g );' % (r['zone'], cx, cy, cz + 40))
NL = chr(10)
fdoor_lines = ['    doors[doors.size] = iwz_door( "%s", %d, %g, %g, %g, %g, %g );' % (d['name'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1'])
               for d in DOORS]
fdoor_lines.append('    doors[doors.size] = iwz_door( "pap_shutter", 1, 4008, %g, %g, %g, %g );' % (OP['a_control_pap']['a'], OP['a_control_pap']['b'],
                                                                                              OP['a_control_pap']['z0'], OP['a_control_pap']['z1']))
fx = fx.replace('//@DOORS@', NL.join(fdoor_lines))
fx = fx.replace('//@VIEWS@', NL.join(view_lines)).replace('//@FXVIEWS@', NL.join(fxv_lines)).replace('//@WALK@', NL.join(walk_lines)).replace('//@WALKCAP@', NL.join(wc_lines)).replace('//@PROBES@', NL.join(probe_lines))
open(os.path.join(out, 'iwzmap_sz2_local.gsc'), 'w', newline=NL).write(fx)
layout['views'] = VIEWS
layout['sign_views'] = SIGN_VIEWS
layout['fx'] = FX
layout['flicker'] = FLICKER
layout['kit_models'] = sorted(m for m in KIT_MODELS if not os.environ.get('IWZ_KIT_ONLY') or m == os.environ['IWZ_KIT_ONLY'])
layout['flicker_views'] = FLK_VIEWS
layout['fx_views'] = FX_VIEWS
layout['decals'] = DECALS
layout['sign_view_list'] = SIGN_VIEW_LIST
layout['walk'] = WALK
layout['track_spec'] = TRACK_SPEC
layout['art_hooks'] = ART_HOOK_REPORT
layout['train_spec'] = TRAIN_SPEC
layout['walkcap'] = [{'name': n, 'origin': [x, y, z], 'yaw': yw} for n, x, y, z, yw in WALKCAP]
layout['gallery'] = {'materials': GALLERY_ITEMS, 'texels': GALLERY_TEXELS, 'views': GALLERY_VIEWS}
for e_ in ents:      # named placed models (quest, relays, shutter, lever) for sz2_propcheck.py
    d_ = dict(e_)
    if d_.get(K['classname']) == 'script_model' and d_.get(K['targetname'], '').startswith('iwz_') and d_.get(K['model'], 'tag_origin') != 'tag_origin':
        o_ = [float(v) for v in d_[K['origin']].split()]
        a_ = [float(v) for v in d_.get(K['angles'], '0 0 0').split()]
        if o_[2] > -2000:
            MODELS.append({'zone': None, 'model': d_[K['model']], 'origin': o_, 'yaw': a_[1], 'targetname': d_[K['targetname']]})
# light groups (darkness design, coordinator 2026-11-08): 'emergency' lamps and cues stay on in the dark bake,
# 'power' lights come on with the power switch, 'flicker' lamps flicker after power-on. The darkness agent's build
# step bakes the dark state and generates the power lights from these records.
for l_ in LIGHTS:
    fx_ = l_.get('fixture', '')
    l_['group'] = ('emergency' if fx_ in ('emergency', 'lamp_red', 'lamp_green', 'hint_glow') else
                   'flicker' if fx_ == 'flicker' else 'power')
# faint cues in the dark: a small amber glow at every buy, door, perk, wheel, PaP and the power switch
for it_ in layout['interactions']:
    ox_, oy_, oz_ = it_['origin']
    cue_ = {'zone': it_.get('zone') or it_.get('area') or '', 'origin': (ox_, oy_, oz_ + 40), 'type': 'omni',
            'color': (1.0, 0.55, 0.2), 'radius': 72 if it_['kind'] != 'generator' else 140,
            'intensity': 0.25 if it_['kind'] != 'generator' else 0.6, 'fixture': 'hint_glow', 'group': 'emergency',
            'cue': it_['kind']}
    LIGHTS.append(cue_)
layout['light_groups'] = {g_: sum(1 for l_ in LIGHTS if l_.get('group') == g_) for g_ in ('emergency', 'power', 'flicker')}
json.dump(layout, open(os.path.join(out, 'layout.json'), 'w'), indent=1, default=list)
json.dump({'custom': MT.CUSTOM, 'used': sorted(B.used)}, open(os.path.join(out, 'custom_materials.json'), 'w'), indent=1)
plan = {'regions': [{'name': r['name'], 'zone': r['zone'], 'rect': r['rect']} for r in REGIONS], 'adj': [sorted(a) for a in ADJ],
        'cells': [[i, j, z, owner[(i, j)]] for (i, j), z in cells.items()],
        'cell_corners': [[i, j, list(c_)] for (i, j), c_ in corner_z.items() if (i, j) in cells],
        'nav_seams': NAV_SEAM_REPORT, 'blockers': B.blockers,
        'col_tris': len(B.mesh.col), 'bounds': wb}
json.dump(plan, open(os.path.join(out, 'plan.json'), 'w'))
json.dump({'quads': B.records}, open(os.path.join(out, 'surfaces.json'), 'w'))
print('verts', nv, 'indices', ni, 'surfaces', ns, 'quads', B.quads, 'trim_quads', B.trim_quads, 'bounds', wb, 'collision', info, 'nav areas', nareas,
      'nav bytes', len(nav), 'materials', len(B.used), 'lights', len(LIGHTS), 'signs', len(SIGNS))
