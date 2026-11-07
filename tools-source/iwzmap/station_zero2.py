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
    'platform_a':     {'box': (-2400, 1200, -400, 2600, 2400, 16), 'probe': (0.80, 0.98, 1.10, 0.6)},
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
     'a': 1304, 'b': 1496, 'z0': -384, 'z1': -160, 'cost': 1000, 'zones': ('platform_a', 'service_tunnel'),
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
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 112, 'tile_black', 0), (zf + 112, zf + 120, 'steel_trim', 1.5),
                (zf + 120, zc - 20, 'tile_white', 0), (zc - 20, zc, 'molding', 3)]
    if style == 'metro_cream':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 112, 'tile_green', 0), (zf + 112, zf + 120, 'steel_trim', 1.5),
                (zf + 120, zc - 20, 'tile_cream', 0), (zc - 20, zc, 'molding', 3)]
    if style == 'maint':
        return [(zf, zf + 10, 'rubber_trim', 2), (zf + 10, zf + 64, 'conc_painted', 0), (zf + 64, zf + 70, 'beam_yellow', 1),
                (zf + 70, zc, 'conc_lined', 0)]
    if style == 'old':
        return [(zf, zf + 10, 'wood_trim', 2), (zf + 10, zf + 104, 'wood_green', 0), (zf + 104, zf + 112, 'wood_trim', 2),
                (zf + 112, zc - 18, 'brick_white', 0), (zc - 18, zc, 'molding', 2.5)]
    if style == 'tunnel':
        return [(zf, zf + 32, 'conc_dark', 0), (zf + 32, zc, 'conc_seam', 0)]
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
            if pr == 0:
                B.wall_plane(zone, axis, fixed, facing, p, q, z0, z1, mat, vtop=z1 if mat.startswith('tile') else None)
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
def strip_light(zone, x0, y0, x1, y1, z, mat='lamp_cool', depth=6):
    """Ceiling fluorescent fitting: a steel housing with an emissive diffuser underneath."""
    B.box((x0 - 3, y0 - 3, z - depth), (x1 + 3, y1 + 3, z), {'side': 'steel_trim', 'top': 'steel_trim'}, zone,
          collide=False, nav=False, skip=('bottom',))
    B.quad(mat, zone, [(x0, y1, z - depth - 0.5), (x1, y1, z - depth - 0.5), (x1, y0, z - depth - 0.5), (x0, y0, z - depth - 0.5)],
           n=(0, 0, -1), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], collide=False)
    LIGHTS.append({'zone': zone, 'origin': ((x0 + x1) / 2, (y0 + y1) / 2, z - depth - 4), 'type': 'omni',
                   'color': LIGHT_COLOR.get(mat, (1, 1, 1)), 'radius': 384, 'intensity': 1.0, 'fixture': mat})


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
    LIGHTS.append({'zone': zone, 'origin': o, 'type': 'omni', 'color': LIGHT_COLOR.get(mat, (1, 1, 1)), 'radius': 320,
                   'intensity': 1.0, 'fixture': mat})


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
    B.quad(key, zone, pts, n=n, uvs=uv, collide=False)
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


def decal_floor(zone, mat, x, y, z, w, h, rot=False):
    x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h / 2, y + h / 2
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
    if rot: uv = uv[1:] + uv[:1]
    B.quad(mat, zone, [(x0, y0, z + 0.4), (x1, y0, z + 0.4), (x1, y1, z + 0.4), (x0, y1, z + 0.4)], n=(0, 0, 1), uvs=uv, collide=False)


def decal_wall(zone, mat, axis, fixed, facing, s, zc, w, h):
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
    B.box((x - half, y - half, z0 + 10), (x + half, y + half, z0 + 112), 'tile_black', zone, collide=False, nav=False, skip=('bottom', 'top'))
    B.box((x - half - 1.5, y - half - 1.5, z0 + 112), (x + half + 1.5, y + half + 1.5, z0 + 120), 'steel_trim', zone, collide=False, nav=False)
    B.box((x - half, y - half, z0 + 120), (x + half, y + half, z1 - 24), 'tile_white', zone, collide=False, nav=False, skip=('bottom', 'top'))
    B.box((x - half - 4, y - half - 4, z1 - 24), (x + half + 4, y + half + 4, z1), 'steel_trim', zone, collide=False, nav=False, skip=('top',))
    B.collision_box((x - half - 2, y - half - 2, z0), (x + half + 2, y + half + 2, z1))


def rail_run(zone, axis, s0, s1, c, z, h=36, post=96, mat='steel_trim', collide=True):
    """Handrail / safety railing: posts every `post` and a top rail; collision as a thin wall."""
    n = max(1, int(round((s1 - s0) / post)))
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
        rect(sk0, sk1, zt, 'stair_tread', False)
        # riser at sk0 facing the low end, with a steel nosing strip
        n = (-d, 0, 0) if axis == 'x' else (0, -d, 0)
        pts = [P(sk0, c0, zt - rise), P(sk0, c1, zt - rise), P(sk0, c1, zt), P(sk0, c0, zt)]
        if bk.dot(bk.cross(bk.sub(pts[1], pts[0]), bk.sub(pts[3], pts[0])), n) < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        B.quad('tile_black', zone, pts, n=n, collide=False)
    # collision: nosing line z(s) = z_lo + rise + (s - s_a) * rise / run, from s_a - run (z_lo) to s_b - run (z_hi)
    r0, r1 = s_a - run, s_b - run

    def cq(sa, sb, za, zb):
        pts = [P(sa, c0, za), P(sb, c0, zb), P(sb, c1, zb), P(sa, c1, za)]
        B.collision_quad(pts, n=(0, 0, 1))
    cq(lo_end, r0, z_lo, z_lo)
    cq(r0, r1, z_lo, z_hi)
    cq(r1, hi_end, z_hi, z_hi)

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
                lower, upper = ('tile_green', 'tile_cream') if style == 'metro_cream' else ('tile_black', 'tile_white')
                for lo_off, hi_off, mat in ((-rise - 2, 12, 'rubber_trim'), (12, 112, lower), (112, 120, 'steel_trim'),
                                            (120, head - 20, upper), (head - 20, head, 'molding')):
                    B.wall_sloped(zone, wax, cfix, facing, sa, sb, za + lo_off, zb + lo_off, za + hi_off, zb + hi_off, mat)
        # handrails 36 above the nosing line along both walls
        for cfix, sgn in ((c0, 1), (c1, -1)):
            cc = cfix + sgn * 4
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
LIGHT_COLOR = {'lamp_cool': (0.85, 0.93, 1.0), 'lamp_warm': (1.0, 0.58, 0.22), 'lamp_red': (1.0, 0.06, 0.04),
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
        strip_light(Z, x - 64, y - 8, x + 64, y + 8, 320)
for x in (-800, -400, 0):
    column(Z, x, 4000, 0, 320)
# turnstile row (y 3700) with 64-wide gates, ticket booth in the middle
TURN_Y = 3700
gates = []
x = -1168
while x < -240:
    B.box((x, TURN_Y - 32, 0), (x + 32, TURN_Y + 32, 40), {'side': 'brushed', 'top': 'steel_trim'}, Z)   # cabinet
    B.box((x + 32, TURN_Y - 2, 28), (x + 56, TURN_Y + 2, 32), 'chrome_trim', Z, collide=False, nav=False)  # arm
    gates.append(x + 64)
    x += 96
# ticket booth (-224..96, 3600..3800): counter, steel posts, glass, roof
BX0, BX1, BY0, BY1 = -224, 96, 3600, 3800
B.box((BX0, BY0, 0), (BX1, BY1, 40), {'side': 'wood_green', 'top': 'wood_trim'}, Z)
for px, py in ((BX0, BY0), (BX1, BY0), (BX0, BY1), (BX1, BY1)):
    B.box((px - 3, py - 3, 40), (px + 3, py + 3, 136), 'frame', Z, collide=False, nav=False)
B.box((BX0 - 6, BY0 - 6, 136), (BX1 + 6, BY1 + 6, 152), {'side': 'wood_green', 'top': 'steel_trim', 'bottom': 'conc_painted'}, Z, collide=True, nav=False)
for (x0_, y0_, x1_, y1_) in ((BX0, BY0, BX1, BY0), (BX0, BY1, BX1, BY1)):
    B.quad('glass', Z, [(x0_, y0_, 40), (x1_, y1_, 40), (x1_, y1_, 136), (x0_, y0_, 136)], n=(0, -1 if y0_ == BY0 else 1, 0))
for (x_, ) in ((BX0,), (BX1,)):
    B.quad('glass', Z, [(x_, BY0, 40), (x_, BY1, 40), (x_, BY1, 136), (x_, BY0, 136)], n=(-1 if x_ == BX0 else 1, 0, 0))
strip_light(Z, BX0 + 40, 3690, BX1 - 40, 3710, 136, depth=4)
# east half: railing with a service gate
rail_run(Z, 'x', 96, 260, TURN_Y, 0, h=40)
rail_run(Z, 'x', 340, 400, TURN_Y, 0, h=40)
# street exit (north): collapsed stairs up to rubble, zombie entry
room(Z, 'street', (-304, 4400, 112, 4600), 0, 320, 'metro', 'tile_floor', 'ceil_tile', skip=('south',))
for k in range(6):
    B.box((-304, 4448 + k * 24, 0), (112, 4600, 16 * (k + 1)), {'top': 'stair_tread', 'side': 'conc_painted'}, Z, collide=True, nav=True)
for k, (rx, ry, rw, rh) in enumerate([(-260, 4520, 120, 90), (-110, 4500, 140, 120), (40, 4530, 90, 70), (-200, 4570, 260, 200)]):
    B.box((rx - rw / 2, ry - 30, 0), (rx + rw / 2, ry + 30, rh), {'side': 'conc_dark', 'top': 'conc'}, Z)
sign(Z, 'sign_station_zero', 'x', 4400, -1, -700, 220, 384)
sign(Z, 'sign_network_map', 'y', 400, -1, 3950, 170, 256, 128)
sign(Z, 'sign_to_platforms', 'x', 3200, +1, -600, 268, 256)
sign(Z, 'sign_to_old_station', 'y', -1200, +1, 3304, 268, 192)
sign(Z, 'poster_station_zero', 'y', -1200, +1, 3900, 120, 96, 144)
sign(Z, 'poster_mindgap', 'y', -1200, +1, 4150, 120, 96, 144)
decal_wall(Z, 'leak_stain', 'x', 4400, -1, 300, 200, 128, 220)
hanging_sign(Z, 'sign_to_platforms', -700, 3640, 236, 256, 296)
hanging_sign(Z, 'sign_station_zero_plain', -700, 4210, 236, 320, 296)
# vending machine (east wall): red cabinet with a lit front panel
B.box((340, 4180, 0), (400, 4260, 152), {'side': 'metal_red', 'top': 'steel_trim', 'west': 'light_panel'}, Z)
decal_floor(Z, 'blood_pool', -500, 3450, 0, 96, 96)
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
# deck floor (minus the stairwells), coping and yellow safety strip at the edge
deck_x = [(-2400, -2192), (-2192, 1904), (1904, 2112), (2112, 2400)]
floor(Z, 'conc_tiles', -2400, 1760, 2400, 2400, DECK_Z)
floor(Z, 'conc_tiles', -2192, 1648, 1904, 1760, DECK_Z)
floor(Z, 'conc_tiles', 2112, 1648, 2400, 1760, DECK_Z)
floor(Z, 'yellow_grip', -2192, 1624, 1904, 1648, DECK_Z)
floor(Z, 'yellow_grip', 2112, 1624, 2400, 1648, DECK_Z)
floor(Z, 'conc_painted', -2192, 1600, 1904, 1624, DECK_Z)
floor(Z, 'conc_painted', 2112, 1600, 2400, 1624, DECK_Z)
# platform edge face (deck to pit) with a coping lip
for x0_, x1_ in ((-2192, 1904), (2112, 2400)):
    B.wall_plane(Z, 'x', 1600, -1, x0_, x1_, PIT_Z, DECK_Z, 'conc_dark')
    B.box((x0_, 1596, DECK_Z - 6), (x1_, 1600, DECK_Z), 'conc_painted', Z, collide=False, nav=False)
# stairwells into the pit (4 steps), railing on the deck side
for wname, (wx0, wy0, wx1, wy1, ddir) in WELLS.items():
    if ddir < 0:   # descends westwards: low end at wx0
        zl, _ = straight_stair(Z, wname, 'x', wx0, wx1, wy0, wy1, PIT_Z, DECK_Z, 64, 0.0001, 4, side_walls=False, ceiling=False)
        lo, hi = wx0, wx1
    else:
        zl, _ = straight_stair(Z, wname, 'x', wx1, wx0, wy0, wy1, PIT_Z, DECK_Z, 64, 0.0001, 4, side_walls=False, ceiling=False)
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
    strip_light(Z, x - 72, 2140, x + 72, 2156, PCEIL - 28)
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
B.wall_plane(Z, 'y', 2560, -1, 1216, 1584, PIT_Z, -128, 'grate', collide=True)
B.wall_plane(Z, 'y', 2591, -1, 1216, 1584, PIT_Z, -128, 'black', collide=False)
floor(Z, 'conc_dark', 2400, 1216, 2592, 1584, PIT_Z, tone='dark')
# columns every 512 on the deck
COLS = [-1792, -1280, -768, -256, 256, 768, 1280, 1792]
for x in COLS:
    column(Z, x, 2000, DECK_Z, PCEIL)
# track: sleepers, two running rails, third rail on insulators (pit, tunnel, recess)
RAIL_Y = (1484, 1540)
THIRD_Y = 1436


def track(zone, x0, x1):
    xs = x0 + 16
    while xs < x1 - 16:
        B.box((xs - 5, 1460, PIT_Z), (xs + 5, 1564, PIT_Z + 4), 'wood_planks', zone, collide=False, nav=False, skip=('bottom',))
        xs += 40
    for ry in RAIL_Y:
        B.box((x0, ry - 2, PIT_Z + 4), (x1, ry + 2, PIT_Z + 10), {'side': 'ibeam_bare', 'top': 'chrome_trim'}, zone, collide=False, nav=False, skip=('bottom',))
    xs = x0 + 64
    while xs < x1 - 32:
        B.box((xs - 4, THIRD_Y - 4, PIT_Z), (xs + 4, THIRD_Y + 4, PIT_Z + 8), 'metal_black', zone, collide=False, nav=False, skip=('bottom',))
        xs += 128
    B.box((x0, THIRD_Y - 4, PIT_Z + 8), (x1, THIRD_Y + 4, PIT_Z + 12), {'side': 'beam_yellow', 'top': 'beam_yellow'}, zone, collide=False, nav=False, skip=('bottom',))


track(Z, -2400, 2592)
# parked carriage on the track (x -416..352, y 1428..1596): walkable interior at deck level
CX0, CX1, CY0, CY1 = -416, 352, 1428, 1596
CAR_FLOOR, CAR_ROOF = DECK_Z, DECK_Z + 136
WT = 6
B.box((CX0, CY0, PIT_Z), (CX1, CY1, CAR_FLOOR - 24), {'side': 'metal_black', 'top': 'metal_black'}, Z, nav=True)   # underframe
for bx in (CX0 + 120, CX1 - 120):    # bogies
    B.box((bx - 64, 1468, PIT_Z + 10), (bx + 64, 1556, CAR_FLOOR - 8), {'side': 'metal_black', 'top': 'metal_black'}, Z, collide=False, nav=False)
floor(Z, 'rubber_mat', CX0 + WT, CY0 + WT, CX1 - WT, CY1 - WT, CAR_FLOOR + 0.5)
CAR_DOORS = [(-280, -200), (-40, 40), (200, 280)]       # x spans on the platform side (north)
CAR_WINDOWS_N = [(-392, -296), (-184, -56), (56, 184), (296, 336)]
CAR_WINDOWS_S = [(-392, -296), (-264, -136), (-104, 24), (56, 184), (216, 336)]
WIN_Z0, WIN_Z1 = CAR_FLOOR + 40, CAR_FLOOR + 96
DOOR_Z1 = CAR_FLOOR + 104


def car_side(y_out, y_in, facing_out, doors, windows):
    """Carriage side wall between y_out (outer face) and y_in (inner face): panels around doors/windows."""
    ylo, yhi = min(y_out, y_in), max(y_out, y_in)
    xs_cut = sorted(doors + windows)
    # full-height pieces between openings
    for a, b in bk.spans_minus(CX0, CX1, xs_cut):
        B.box((a, ylo, CAR_FLOOR), (b, yhi, CAR_ROOF), {'side': 'metal_silver'}, Z, collide=True, nav=False, skip=('top', 'bottom'))
    for a, b in windows:
        B.box((a, ylo, CAR_FLOOR), (b, yhi, WIN_Z0), {'side': 'metal_silver', 'top': 'steel_trim'}, Z, collide=True, nav=False, skip=('bottom',))
        B.box((a, ylo, WIN_Z1), (b, yhi, CAR_ROOF), {'side': 'metal_silver', 'bottom': 'steel_trim'}, Z, collide=True, nav=False, skip=('top',))
        # glass (collision keeps players inside)
        B.quad('glass', Z, [(a, (ylo + yhi) / 2, WIN_Z0), (b, (ylo + yhi) / 2, WIN_Z0), (b, (ylo + yhi) / 2, WIN_Z1), (a, (ylo + yhi) / 2, WIN_Z1)], n=(0, facing_out, 0))
    for a, b in doors:
        B.box((a, ylo, DOOR_Z1), (b, yhi, CAR_ROOF), {'side': 'metal_silver', 'bottom': 'steel_trim'}, Z, collide=True, nav=False, skip=('top',))
    # red livery stripe on the outer face
    y = y_out + facing_out * 0.6
    for a, b in bk.spans_minus(CX0, CX1, doors):
        if facing_out > 0:
            B.quad('carriage_red', Z, [(b, y, CAR_FLOOR + 100), (a, y, CAR_FLOOR + 100), (a, y, CAR_FLOOR + 112), (b, y, CAR_FLOOR + 112)], n=(0, 1, 0), collide=False)
        else:
            B.quad('carriage_red', Z, [(a, y, CAR_FLOOR + 100), (b, y, CAR_FLOOR + 100), (b, y, CAR_FLOOR + 112), (a, y, CAR_FLOOR + 112)], n=(0, -1, 0), collide=False)
    # skirt below the floor
    B.box((CX0, ylo, CAR_FLOOR - 24), (CX1, yhi, CAR_FLOOR), {'side': 'metal_black'}, Z, collide=False, nav=False, skip=('top',))


car_side(CY1, CY1 - WT, +1, CAR_DOORS, CAR_WINDOWS_N)
car_side(CY0, CY0 + WT, -1, [], CAR_WINDOWS_S)
for ex, inner in ((CX0, CX0 + WT), (CX1, CX1 - WT)):      # cab ends with a window
    xa, xb = min(ex, inner), max(ex, inner)
    B.box((xa, CY0, CAR_FLOOR - 24), (xb, CY1, WIN_Z0), {'side': 'metal_silver'}, Z, collide=True, nav=False, skip=('top', 'bottom'))
    B.box((xa, CY0, WIN_Z1), (xb, CY1, CAR_ROOF), {'side': 'metal_silver'}, Z, collide=True, nav=False, skip=('top', 'bottom'))
    B.box((xa, CY0, WIN_Z0), (xb, CY0 + 40, WIN_Z1), {'side': 'metal_silver'}, Z, collide=True, nav=False)
    B.box((xa, CY1 - 40, WIN_Z0), (xb, CY1, WIN_Z1), {'side': 'metal_silver'}, Z, collide=True, nav=False)
    xm = (xa + xb) / 2
    B.quad('glass', Z, [(xm, CY0 + 40, WIN_Z0), (xm, CY1 - 40, WIN_Z0), (xm, CY1 - 40, WIN_Z1), (xm, CY0 + 40, WIN_Z1)], n=(1 if ex == CX1 else -1, 0, 0))
    wall_lamp(Z, 'y', ex, 1 if ex == CX1 else -1, CY0 + 30, CAR_FLOOR + 30, mat='lamp_red', w=10, h=8)
# roof, interior ceiling with strip lights
B.box((CX0 - 4, CY0 - 4, CAR_ROOF), (CX1 + 4, CY1 + 4, CAR_ROOF + 10), {'side': 'metal_silver', 'top': 'corrugated', 'bottom': 'molding'}, Z, collide=True, nav=False)
for xx in (-300, -60, 180):
    strip_light(Z, xx - 48, 1504, xx + 48, 1520, CAR_ROOF, depth=3)
# longitudinal seats along the south wall, luggage rack above (teddy bear spot)
for a, b in [(-400, -296), (-264, -136), (-104, 24), (56, 184), (216, 336)]:
    B.box((a, CY0 + WT, CAR_FLOOR), (b, CY0 + WT + 26, CAR_FLOOR + 18), {'side': 'metal_black', 'top': 'seat_blue'}, Z, collide=True, nav=True)
    B.box((a, CY0 + WT, CAR_FLOOR + 18), (b, CY0 + WT + 6, CAR_FLOOR + 40), {'side': 'seat_blue', 'top': 'seat_blue'}, Z, collide=True, nav=False)
    B.box((a, CY0 + WT, CAR_FLOOR + 104), (b, CY0 + WT + 22, CAR_FLOOR + 106), 'chrome_trim', Z, collide=True, nav=False)
    for bx_ in (a + 4, b - 4):     # rack brackets (wall to the front rail, angled look from two short boxes)
        B.box((bx_ - 1, CY0 + WT, CAR_FLOOR + 94), (bx_ + 1, CY0 + WT + 4, CAR_FLOOR + 104), 'chrome_trim', Z, collide=False, nav=False)
        B.box((bx_ - 1, CY0 + WT + 4, CAR_FLOOR + 100), (bx_ + 1, CY0 + WT + 22, CAR_FLOOR + 104), 'chrome_trim', Z, collide=False, nav=False)
# grab poles at the doors
for a, b in CAR_DOORS:
    B.box(((a + b) / 2 - 1.5, 1540, CAR_FLOOR), ((a + b) / 2 + 1.5, 1543, CAR_ROOF), 'chrome_trim', Z, collide=False, nav=False)
TEDDY_SPOT = (-200, CY0 + WT + 11, CAR_FLOOR + 106)        # top of the rack bar (z -214), centre of its depth
region('car', Z, (CX0 + WT, CY0 + WT + 26, CX1 - WT, CY1 - WT), CAR_FLOOR)
# signs, posters, map on the platform walls
for x in (-1536, 0, 1536):
    sign(Z, 'sign_station_zero', 'x', 1200, +1, x, -150, 384)     # track wall, readable from the deck
for x in (-1024, 1024):
    sign(Z, 'sign_station_zero_plain', 'x', 2400, -1, x, -170, 320)
sign(Z, 'sign_northbound', 'x', 2400, -1, 0, -150, 256)
for x in (-1024, 1024):
    hanging_sign(Z, 'sign_station_zero_plain', x, 1880, -84, 256, PCEIL - 28)
hanging_sign(Z, 'sign_staff_only', 2250, 1800, -96, 160, PCEIL - 28, axis='y')
hanging_sign(Z, 'sign_to_old_station', -2250, 1700, -96, 192, PCEIL - 28, axis='y')
sign(Z, 'sign_network_map', 'x', 2400, -1, -1536, -200, 256, 128)
for x, p in ((-768, 'poster_lasttrain'), (512, 'poster_mindgap'), (-2048, 'poster_mindgap'), (1792, 'poster_lasttrain')):
    sign(Z, p, 'x', 1200, +1, x, -170, 96, 144)
sign(Z, 'sign_staff_only', 'y', 2400, -1, 1800, -90, 192)
for x in (-1900, -400, 900, 2000):
    decal_wall(Z, 'leak_stain', 'x', 2400, -1, x, -120, 96, 180)
decal_floor(Z, 'blood_pool', 600, 2200, DECK_Z, 96, 96)
# nav regions: deck (minus wells), coping strip, pit (around the car underframe), recess
region('deck', Z, (-2400, 1760, 2400, 2400), DECK_Z, (16, 0, 16, 16))
region('deck_mid', Z, (-2192, 1600, 1904, 1760), DECK_Z, (0, 0, 0, 0))
region('deck_east', Z, (2112, 1600, 2400, 1760), DECK_Z, (0, 0, 16, 0))
region('pit', Z, (-2400, 1200, 2400, 1600), PIT_Z, (0, 16, 0, 16))
region('recess', Z, (2400, 1216, 2560, 1584), PIT_Z, (0, 16, 16, 16))
for a, b_ in (('deck', 'deck_mid'), ('deck', 'deck_east'), ('deck', 'well_w'), ('deck', 'well_e'), ('deck_mid', 'well_w'),
              ('deck_mid', 'well_e'), ('deck_east', 'well_e'), ('pit', 'well_w'), ('pit', 'well_e'), ('pit', 'recess')):
    adjacent(a, b_)
for a, b in CAR_DOORS:     # car doors: portals between the coping and the car interior
    nm = region('portal:car%d' % a, Z, (a + 12, 1560, b - 12, 1608), DECK_Z, (0, 0, 0, 0))
    adjacent(nm, 'car'); adjacent(nm, 'deck_mid')

# ---------------------------------------------------------------- 4 maintenance corridor (L)
Z = 'maint_corridor'
room(Z, 'corridor_a', (2416, 1680, 3200, 1920), -320, -96, 'maint', 'conc_floor_gray', 'conc_dark')
room(Z, 'corridor_b', (2960, 1920, 3200, 2384), -320, -96, 'maint', 'conc_floor_gray', 'conc_dark', skip=('south',))
for (x0_, x1_, y_) in ((2416, 3200, 1696), (2416, 3200, 1904)):
    B.box((x0_, y_ - 4, -128), (x1_, y_ + 4, -120), 'metal_red', Z, collide=False, nav=False)    # pipes
for y_ in (2000, 2200):
    wall_lamp(Z, 'y', 3200, -1, y_, -150, mat='lamp_warm')
for x_ in (2600, 2900):
    wall_lamp(Z, 'x', 1920, -1, x_, -150, mat='lamp_warm')
sign(Z, 'sign_generator', 'x', 1920, -1, 2700, -170, 192)
region('corridor_a', Z, (2416, 1680, 3200, 1920), -320)
region('corridor_b', Z, (2960, 1920, 3200, 2384), -320, (16, 0, 16, 16))
adjacent('corridor_a', 'corridor_b')

# ---------------------------------------------------------------- 5 generator room (2600,2400)-(3800,3184), -320..32
Z = 'generator_room'
room(Z, 'generator', (2600, 2400, 3800, 3184), -320, 32, 'maint', 'diamond', 'conc_dark')
for x in range(2700, 3800, 200):
    B.box((x - 6, 2400, 8), (x + 6, 3184, 32), 'beam_yellow', Z, collide=False, nav=False)
for x in (2800, 3200, 3600):
    for y in (2600, 2980):
        strip_light(Z, x - 48, y - 8, x + 48, y + 8, 8, mat='lamp_warm')
# generator plinth + housing (box placeholder until the kit model), control panel for relay 3
GEN = (3300, 2800)
B.box((GEN[0] - 120, GEN[1] - 72, -320), (GEN[0] + 120, GEN[1] + 72, -304), 'conc_painted', Z)
B.box((GEN[0] - 96, GEN[1] - 56, -304), (GEN[0] + 96, GEN[1] + 56, -200), {'side': 'beam_yellow', 'top': 'diamond'}, Z)
B.box((3560, 3120, -320), (3760, 3184, -260), {'side': 'panel_dark', 'top': 'steel_trim'}, Z)       # control panel
B.box((3560, 3168, -260), (3760, 3184, -200), {'side': 'panel_dark', 'top': 'steel_trim'}, Z)
sign(Z, 'sign_signal_control', 'x', 3184, -1, 3100, -70, 192)
decal_floor(Z, 'blood_pool', 2900, 2700, -320, 96, 96)
region('generator', Z, (2600, 2400, 3800, 3184), -320)

# ---------------------------------------------------------------- 6 control room (2600,3200)-(3600,4000), -320..-32 + PaP alcove
Z = 'control_room'
room(Z, 'control', (2600, 3200, 3600, 4000), -320, -32, 'control', 'rubber_mat', 'ceil_red')
room(Z, 'pap_alcove', (2976, 4016, 3232, 4160), -320, -112, 'control', 'diamond', 'conc_dark', skip=('south',))
for x in (2750, 3100, 3450):
    for y in (3400, 3800):
        strip_light(Z, x - 32, y - 8, x + 32, y + 8, -32, mat='lamp_red')
for y_ in (3350, 3650, 3950):
    wall_lamp(Z, 'y', 2600, +1, y_, -120, mat='lamp_red', w=16, h=16)
    wall_lamp(Z, 'y', 3600, -1, y_, -120, mat='lamp_red', w=16, h=16)
# signal desks (boxes, until the kit) and the network map board
for x0_ in (2700, 3020, 3340):
    B.box((x0_, 3520, -320), (x0_ + 240, 3600, -284), {'side': 'panel_dark', 'top': 'steel_trim'}, Z)
    B.box((x0_ + 10, 3584, -284), (x0_ + 230, 3600, -250), {'side': 'panel_dark', 'top': 'steel_trim'}, Z)
decal_wall(Z, 'map_board', 'y', 3600, -1, 3600, -180, 320, 160)
sign(Z, 'sign_network_map', 'x', 4000, -1, 2800, -170, 256, 128)
B.wall_plane(Z, 'x', 4150, -1, 2976, 3232, -320, -112, 'rollup', collide=False)
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
B.box((-3590, 1440, -384), (-3560, 1580, -330), {'side': 'metal_red', 'top': 'steel_trim'}, Z)     # buffer stop
for x in range(-3400, -2416, 400):
    wall_lamp(Z, 'x', 1216, +1, x, -170, mat='lamp_warm', w=12, h=10)
for y in range(1800, 2584, 400):
    wall_lamp(Z, 'y', -3584, +1, y, -170, mat='lamp_warm', w=12, h=10)
for y_ in (1230, 1240):
    B.box((-3600, y_, -210), (-2416, y_ + 3, -206), 'metal_black', Z, collide=False, nav=False)   # cables
region('tunnel_a', Z, (-3600, 1216, -2416, 1584), -384, (16, 16, 16, 0))
region('tunnel_b', Z, (-3600, 1584, -3216, 2584), -384, (16, 0, 16, 16))
adjacent('tunnel_a', 'tunnel_b')

# ---------------------------------------------------------------- 8 platform_b (-3600,2616)-(-2064,3400), -384..-32
Z = 'platform_b'
room(Z, 'platform_b', (-3600, 2600, -2064, 3400), -384, -32, 'old', 'herringbone', 'conc_painted')
for x in range(-3500, -2064, 256):
    B.box((x - 8, 2600, -56), (x + 8, 3400, -32), 'ibeam', Z, collide=False, nav=False)
for x in (-3300, -2800, -2300):
    for y in (2800, 3200):
        strip_light(Z, x - 48, y - 6, x + 48, y + 6, -56, mat='lamp_warm')
# boarded windows on the north wall
for x in (-3400, -3000, -2600):
    B.wall_plane(Z, 'x', 3399, -1, x - 80, x + 80, -260, -120, 'black', collide=False)
    for k in range(4):
        z_ = -250 + k * 34
        B.box((x - 92, 3388, z_), (x + 92, 3398, z_ + 26), 'wood_planks', Z, collide=False, nav=False)
# abandoned kiosk and the old ticket booth (relay 2)
B.box((-2560, 2700, -384), (-2320, 2820, -344), {'side': 'wood_green', 'top': 'wood_trim'}, Z)
B.box((-2560, 2810, -344), (-2320, 2820, -232), {'side': 'wood_green'}, Z)
B.box((-2570, 2690, -232), (-2310, 2830, -220), {'side': 'wood_trim', 'top': 'wood_green', 'bottom': 'wood_trim'}, Z, collide=False, nav=False)
OLD_BOOTH = (-3480, 3200, -3300, 3380)
B.box((OLD_BOOTH[0], OLD_BOOTH[1], -384), (OLD_BOOTH[2], OLD_BOOTH[1] + 10, -200), {'side': 'wood_green'}, Z)
B.box((OLD_BOOTH[0], OLD_BOOTH[1], -384), (OLD_BOOTH[0] + 10, OLD_BOOTH[3], -200), {'side': 'wood_green'}, Z)
B.box((OLD_BOOTH[0], OLD_BOOTH[1], -200), (OLD_BOOTH[2], OLD_BOOTH[3], -188), {'side': 'wood_trim', 'top': 'wood_green', 'bottom': 'wood_trim'}, Z, collide=False, nav=False)
sign(Z, 'sign_old_station', 'x', 2600, +1, -2900, -120, 320)
sign(Z, 'sign_old_station', 'y', -3600, +1, 3000, -120, 320)
sign(Z, 'poster_lasttrain', 'x', 3400, -1, -2300, -200, 96, 144)
decal_wall(Z, 'wall_stain', 'x', 3400, -1, -3200, -150, 160, 160)
region('platform_b', Z, (-3600, 2600, -2064, 3400), -384)

# ---------------------------------------------------------------- 9 stair_b (-2048,3104)-(-1216,3400): -384 -> 0 rising east
Z = 'stair_b'
zl_b, _ = straight_stair(Z, 'stair_b', 'x', -2048, -1216, 3104, 3400, -384, 0, 48, 48, 23, style='metro_cream')
wall(Z, 'stair_b', 'y', -2048, +1, 3104, 3400, -384, -96, 'metro_cream')
wall(Z, 'stair_b', 'y', -1216, -1, 3104, 3400, 0, 288, 'metro_cream')
for x in (-1900, -1650, -1400):
    strip_light(Z, x - 8, 3236, x + 8, 3268, zl_b(x) + 288, depth=4)
sign(Z, 'sign_to_platforms', 'y', -2048, +1, 3252, -150, 192)
region('stair_b', Z, (-2048, 3104, -1216, 3400), lambda x, y: zl_b(x))

# ---------------------------------------------------------------- stock decor models (rc1-proven), clip boxes block nav
def decor(zone, model, x, y, z, yaw=0, clip=None):
    DECOR.append({'zone': zone, 'model': model, 'origin': (x, y, z), 'yaw': yaw})
    if clip:
        hx, hy, hz = clip
        B.collision_box((x - hx, y - hy, z), (x + hx, y + hy, z + 2 * hz))


if os.environ.get('IWZ_NO_DECOR') != '1':
    decor('ticket_hall', 'park_trash_can_blue_01', -1100, 4340, 0, 0, (16, 16, 24))
    decor('ticket_hall', 'park_trash_can_red_01', 360, 4100, 0, 0, (16, 16, 24))
    for x in (-950, 300):
        decor('ticket_hall', 'furniture_park_bench_01_blue', x, 4340, 0, 0, (48, 16, 20))
    for x in (-2048, -1024, 64, 1536):
        decor('platform_a', 'furniture_park_bench_01_blue', x, 2340, DECK_Z, 0, (48, 16, 20))
    for x in (-1600, 300, 2100):
        decor('platform_a', 'park_trash_can_red_01', x, 2370, DECK_Z, 0, (16, 16, 24))
    decor('maint_corridor', 'dns_locker_set_01', 2700, 1704, -320, 90, (96, 24, 48))
    decor('maint_corridor', 'pipe_metal_painted_straight_128_gray', 2600, 1690, -150, 0)
    decor('maint_corridor', 'pipe_metal_painted_straight_128_gray', 2728, 1690, -150, 0)
    decor('generator_room', 'zom_machinery_generator_portable_01', GEN[0], GEN[1], -200, 0)
    decor('generator_room', 'equipment_oxygen_tank_01', 2640, 2440, -320, 0, (14, 14, 40))
    decor('generator_room', 'equipment_oxygen_tank_01', 2672, 2440, -320, 30, (14, 14, 40))
    decor('generator_room', 'ammo_crate_01_dust', 3740, 2460, -320, 90, (24, 16, 16))
    decor('generator_room', 'fac_trash_bin', 2640, 3140, -320, 0, (20, 20, 28))
    decor('platform_b', 'park_trash_can_blue_01', -2200, 3360, -384, 0, (16, 16, 24))
    decor('platform_b', 'furniture_park_bench_01_blue', -3000, 3350, -384, 0, (48, 16, 20))
    # control room: CRT monitors on the signal desks, generator room workbench, corridor lockers
    for x0_ in (2700, 3020, 3340):
        for dx in (60, 180):
            decor('control_room', 'zmb_tv_crt_01', x0_ + dx, 3560, -284, 90)
    decor('generator_room', 'mp_dart_workbench_01', 3770, 2950, -320, 0, (16, 44, 22))
    decor('generator_room', 'dns_locker_set_01', 2780, 3172, -320, 180, (20, 10, 50))
    decor('generator_room', 'dns_locker_set_01', 2822, 3172, -320, 180, (20, 10, 50))
    decor('maint_corridor', 'dns_locker_set_01', 3188, 2100, -320, 90, (10, 20, 50))

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
cells, owner = {}, {}
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


def link(a, b):
    oa, ob = owner[a], owner[b]
    return oa == ob or frozenset((oa, ob)) in ADJ


nav, nareas = mapgen.nav_graph(cells, CELL, link)
open(os.path.join(out, 'navgraph.bin'), 'wb').write(nav)
REGION_ZONE = {r['name']: r['zone'] for r in REGIONS}

# ============================================================================ gameplay tables
K = {'classname': '157', 'targetname': '822', 'origin': '543', 'angles': '65', 'noteworthy': '638', 'target': '820',
     'area': '60666', 'parameters': '61049', 'model': '497', 'groupname': '502', 'radius': '599', 'linkname': '636',
     'animation': '60661', 'fxid': '60859', 'spawnflags': '687', 'dummy': '51961'}


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
    ('platform_a', 2520, 1300, -384, 'ground', 180), ('platform_a', 2520, 1500, -384, 'ground', 180),
    ('platform_a', -2300, 1280, -384, 'ground', 0), ('platform_a', -1600, 2352, -320, 'wall', 270),
    ('platform_a', 1600, 2352, -320, 'wall', 270), ('platform_a', 800, 2200, -320, 'ground', 270),
    ('platform_a', -1300, 1700, -320, 'ground', 90), ('platform_a', 1500, 1300, -384, 'ground', 90),
    ('maint_corridor', 3150, 2300, -320, 'ground', 270), ('maint_corridor', 2550, 1800, -320, 'ground', 0),
    ('maint_corridor', 3080, 1760, -320, 'ground', 180), ('maint_corridor', 3080, 2050, -320, 'ground', 270),
    ('maint_corridor', 2800, 1728, -320, 'wall', 90), ('maint_corridor', 3080, 2150, -96, 'ceiling', 270),
    ('generator_room', 2680, 2480, -320, 'ground', 45), ('generator_room', 3720, 2480, -320, 'ground', 135),
    ('generator_room', 2700, 3100, -320, 'ground', 315), ('generator_room', 3700, 3000, -320, 'ground', 225),
    ('generator_room', 2648, 2700, -320, 'wall', 0), ('generator_room', 3752, 2700, -320, 'wall', 180),
    ('control_room', 2680, 3300, -320, 'ground', 45), ('control_room', 3520, 3300, -320, 'ground', 135),
    ('control_room', 2700, 3900, -320, 'ground', 315), ('control_room', 3500, 3900, -320, 'ground', 225),
    ('control_room', 3100, 3800, -32, 'ceiling', 270), ('control_room', 2648, 3650, -320, 'wall', 0),
    ('service_tunnel', -3500, 1300, -384, 'ground', 0), ('service_tunnel', -2700, 1300, -384, 'ground', 180),
    ('service_tunnel', -3400, 2400, -384, 'ground', 270), ('service_tunnel', -3100, 1500, -384, 'ground', 270),
    ('service_tunnel', -3552, 1900, -384, 'wall', 0), ('service_tunnel', -3000, 1264, -384, 'wall', 90),
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
    'relay_3': {'zone': 'generator_room', 'origin': (3660, 3167, -260), 'yaw': 270, 'model_yaw': 180},  # control panel
    'pap_shutter': {'zone': 'control_room', 'origin': (3104, 4010, -320), 'yaw': 270, 'size': (256, 208)},
    'trap_third_rail_fusebox': {'zone': 'platform_a', 'origin': (-768, 1975, -300), 'yaw': 270, 'model_yaw': 180},
    'trap_third_rail_volume': {'zone': 'platform_a', 'box': (-2400, 1200, -384, 2600, 1600, -350)},
    'teddy_bear': {'zone': 'platform_a', 'origin': TEDDY_SPOT, 'yaw': 90, 'note': 'on the luggage rack above the seat x -264..-136, facing into the car'},
}

ws = mapgen.stock_worldspawn(os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.ents'))
ents, relocations, triggers = [], [], []
layout = {'zones': {}, 'doors': [], 'spawners': [], 'starts': [], 'interactions': [], 'quest': QUEST, 'lights': LIGHTS,
          'signs': SIGNS, 'props': PROPS, 'decor': DECOR}
for x, y, z, yaw in STARTS:
    ents.append(ent(classname='script_struct', targetname='default_player_start', origin=fmt((x, y, z)), angles='0 %g 0' % yaw))
    layout['starts'].append((x, y, z))
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
            B.wall_plane(zone, 'y', wx + fx * 0.6, fx, y - 28, y + 28, wz + 4, wz + 44, 'black', collide=False)
            B.slab_y(y - 32, y + 32, wx, wz + 2, wz + 46, 2, 'steel_trim', zone, fx, collide=False, nav=False)
        else:
            wy = y - fy * 48
            B.wall_plane(zone, 'x', wy + fy * 0.6, fy, x - 28, x + 28, wz + 4, wz + 44, 'black', collide=False)
            B.slab_x(x - 32, x + 32, wy, wz + 2, wz + 46, 2, 'steel_trim', zone, fy, collide=False, nav=False)
    elif kind == 'ceiling':
        B.quad('black', zone, [(x - 28, y + 28, z - 0.6), (x + 28, y + 28, z - 0.6), (x + 28, y - 28, z - 0.6), (x - 28, y - 28, z - 0.6)], n=(0, 0, -1), collide=False)
        B.box((x - 32, y - 32, z - 3), (x + 32, y + 32, z - 1), {'side': 'steel_trim', 'bottom': 'grate'}, zone, collide=False, nav=False, skip=('top',))
# render world and collision (after the entry-point vents, which are drawn from the spawner table)
nv, ni, ns, wb = mapgen.write_world(B.mesh, os.path.join(out, 'world.bin'))
col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in B.mesh.col]
blob, info = hkcm_write.encode(col, os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.colmap.hkx'), tag=382,
                               max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')))
open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)

for zone, x, y, z, kind, yaw in SPAWNERS:
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
    layout['interactions'].append({'kind': 'magic_wheel', 'scriptable': scriptable, 'origin': origin, 'yaw': yaw, 'zone': zone})
for name, q in QUEST.items():
    if 'origin' in q:
        ents.append(ent(classname='script_struct', targetname='iwz_' + name, origin=fmt(q['origin']), angles='0 %g 0' % q['yaw']))
    if 'model_yaw' in q:
        ents.append(ent(classname='script_model', targetname='iwz_' + name + '_model', model='fac_sort_machine_fuse_box_set_01',
                        origin=fmt(q['origin']), angles='0 %g 0' % q['model_yaw']))
# stock fast-travel / hidden-room init runs on every map: give its lookups parked entities so its threads idle
# instead of looping on undefined (gameplay REPORT defect 7)
for tn in ('hidden_room_portal', 'center_portal', 'fast_travel_tube_start', 'fast_travel_tube_end', 'hidden_travel_tube_start',
           'hidden_travel_tube_end'):
    ents.append(ent(classname='script_model', targetname=tn, model='tag_origin', origin='0 0 -3000', angles='0 0 0'))
ents.append(ent(classname='script_struct', targetname='hidden_room_spot', origin='0 0 -3000', angles='0 0 0'))
# PaP shutter: two rolling steel gates (stock gate_warehouse_refinery_01, 156 x 12 x 186, origin at its corner) in the
# arch between the control room and the PaP alcove, raised by the relay quest; collision from door blockers below
PAP_ARCH = OP['a_control_pap']
for gx in (PAP_ARCH['a'] - 28, PAP_ARCH['a'] - 28 + 156):
    ents.append(ent(classname='script_model', targetname='iwz_pap_shutter', model='gate_warehouse_refinery_01',
                    origin=fmt((gx, 4002, PAP_ARCH['z0'])), angles='0 0 0'))
for d in DECOR:
    ents.append(ent(classname='script_model', model=d['model'], origin=fmt(d['origin']), angles='0 %g 0' % d.get('yaw', 0)))
open(os.path.join(out, 'scriptables.txt'), 'w', newline='\n').write('\n'.join(relocations) + '\n')
open(os.path.join(out, 'ents.txt'), 'w', newline='\n').write(mapgen.ents_text(ws, ents))

# ============================================================================ lighting.txt (light grid relight for models)
light_lines = ['ambient 0.30 0.30 0.33 0.40']
for zone, zd in ZONES.items():
    x0, y0, z0, x1, y1, z1 = zd['box']
    r, g, b, up = zd['probe']
    light_lines.append('room %d %d %d %d %d %d %.3f %.3f %.3f %.2f' % (x0 - 64, y0 - 64, z0 - 64, x1 + 64, y1 + 64, z1 + 64, r, g, b, up))
open(os.path.join(out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(light_lines) + '\n')

# ============================================================================ level script with generated tables
gsc = open(os.path.join(HERE, 'cp_iwz2.gsc')).read()
door_lines = ['    doors[doors.size] = iwz_door( "%s", "%s", %d, %g, %g, %g, %g, %g );' % (d['name'], d['target'], d['axis'], d['plane'], d['lo'], d['hi'], d['z0'], d['z1'])
              for d in DOORS]
link_lines = ['    links[links.size] = [ "%s", "%s" ];' % l for l in ZONE_LINKS]
gsc = gsc.replace('//@DOORS@', '\n'.join(door_lines)).replace('//@LINKS@', '\n'.join(link_lines))
gsc = gsc.replace('//@INITIAL@', 'level.initial_active_volumes = [ %s ];' % ', '.join('"%s"' % z for z in INITIAL_ZONES))
gsc = gsc.replace('//@WHEEL@', '"%s"' % WHEELS[0][3])
tb = QUEST['trap_third_rail_volume']['box']
gsc = gsc.replace('//@TRAPMIN@', '( %g, %g, %g )' % tb[:3]).replace('//@TRAPMAX@', '( %g, %g, %g )' % tb[3:])
gsc = gsc.replace('//@TRAPRAILY@', '%g' % THIRD_Y)
open(os.path.join(out, 'cp_iwz.gsc'), 'w', newline='\n').write(gsc)

# ============================================================================ capture views, walk path, summaries
VIEWS = {   # 5 per zone: (x, y, z eye-ish origin of the player, yaw, pitch)
    'ticket_hall': [(-1100, 4300, 0, 315, 5), (300, 3300, 0, 135, 5), (-500, 3880, 0, 270, 10), (-96, 4060, 0, 90, -6), (-1100, 3300, 0, 30, 0)],
    'stair_a': [(-600, 3150, 0, 270, 20), (-600, 2460, -320, 90, -20), (-760, 2800, -160, 300, 10), (-600, 3240, 0, 270, 10), (-600, 2440, -320, 270, 0)],
    'platform_a': [(-2300, 2300, -320, 345, 5), (2300, 2300, -320, 195, 5), (-200, 2200, -320, 270, 10), (-40, 1520, -320, 0, 0), (-1500, 1300, -384, 0, -5)],
    'maint_corridor': [(2460, 1800, -320, 0, 0), (3150, 1760, -320, 90, 0), (3080, 2350, -320, 270, 0), (2900, 1720, -320, 180, 0), (3150, 2000, -320, 180, 5)],
    'generator_room': [(2660, 2440, -320, 40, 5), (3740, 3140, -320, 220, 5), (3000, 2800, -320, 0, 0), (3080, 2440, -320, 90, 0), (3600, 2500, -320, 135, 0)],
    'control_room': [(2660, 3260, -320, 45, 5), (3540, 3940, -320, 225, 5), (3104, 3300, -320, 90, 0), (3104, 3950, -320, 270, 0), (2700, 3900, -320, 330, 0)],
    'service_tunnel': [(-2460, 1400, -384, 180, 0), (-3500, 1300, -384, 0, 0), (-3400, 1700, -384, 90, 0), (-3400, 2540, -384, 270, 0), (-3000, 1500, -384, 200, 0)],
    'platform_b': [(-3540, 2660, -384, 40, 5), (-2120, 3340, -384, 220, 5), (-2800, 3000, -384, 90, 0), (-3400, 3000, -384, 0, 0), (-2120, 2700, -384, 150, 0)],
    'stair_b': [(-2020, 3250, -384, 0, -15), (-1260, 3300, 0, 180, 20), (-1700, 3250, -200, 0, -10), (-1150, 3300, 0, 180, 15), (-1600, 3150, -150, 180, 10)],
}
WALK = [   # waypoint path through every zone (doors are opened by the walk fixture first); stair points at the ramp ends
    (-528, 3880, 0), (-528, 3500, 0), (-600, 3250, 0), (-600, 3150, 0), (-600, 3088, 0), (-600, 2448, -320), (-600, 2440, -320),
    (-600, 2200, -320), (0, 2200, -320), (0, 1620, -320), (-40, 1520, -320), (0, 1620, -320), (1000, 1800, -320), (2300, 1800, -320),
    (2600, 1800, -320), (3080, 1800, -320), (3080, 2300, -320), (3080, 2500, -320), (3100, 2900, -320), (3100, 3250, -320),
    (2980, 3450, -320), (2980, 3700, -320), (3104, 3950, -320), (2980, 3700, -320), (2980, 3450, -320), (3100, 3250, -320),
    (3080, 2300, -320), (3080, 1800, -320), (2600, 1800, -320), (1880, 1800, -320), (1880, 1680, -320), (1940, 1680, -320),
    (2084, 1680, -384), (2090, 1560, -384), (2080, 1500, -384), (1000, 1300, -384), (-1500, 1300, -384), (-2350, 1400, -384),
    (-2500, 1400, -384), (-3400, 1400, -384), (-3400, 2000, -384), (-3400, 2650, -384), (-2800, 3000, -384), (-2120, 3250, -384),
    (-2032, 3250, -384), (-1296, 3250, 0), (-1250, 3300, 0), (-1150, 3300, 0), (-528, 3500, 0), (-528, 3880, 0),
]
for o in OPENINGS:
    pass
# local fixture with the capture views, walk path and zone probes baked in
fx = open(os.path.join(HERE, 'fixtures', 'sz2_local.gsc')).read()
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
fx = fx.replace('//@VIEWS@', NL.join(view_lines)).replace('//@WALK@', NL.join(walk_lines)).replace('//@PROBES@', NL.join(probe_lines))
open(os.path.join(out, 'iwzmap_sz2_local.gsc'), 'w', newline=NL).write(fx)
layout['views'] = VIEWS
layout['sign_views'] = SIGN_VIEWS
layout['sign_view_list'] = SIGN_VIEW_LIST
layout['walk'] = WALK
layout['gallery'] = {'materials': GALLERY_ITEMS, 'texels': GALLERY_TEXELS, 'views': GALLERY_VIEWS}
json.dump(layout, open(os.path.join(out, 'layout.json'), 'w'), indent=1, default=list)
json.dump({'custom': MT.CUSTOM, 'used': sorted(B.used)}, open(os.path.join(out, 'custom_materials.json'), 'w'), indent=1)
plan = {'regions': [{'name': r['name'], 'zone': r['zone'], 'rect': r['rect']} for r in REGIONS], 'adj': [sorted(a) for a in ADJ],
        'cells': [[i, j, z, owner[(i, j)]] for (i, j), z in cells.items()], 'blockers': B.blockers,
        'col_tris': len(B.mesh.col), 'bounds': wb}
json.dump(plan, open(os.path.join(out, 'plan.json'), 'w'))
print('verts', nv, 'indices', ni, 'surfaces', ns, 'quads', B.quads, 'bounds', wb, 'collision', info, 'nav areas', nareas,
      'nav bytes', len(nav), 'materials', len(B.used), 'lights', len(LIGHTS), 'signs', len(SIGNS))
