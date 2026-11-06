"""Station Zero: compact original zombies map (three zones linked by corridors) -> iwzcompile sources.

usage: station_zero.py <template dump dir (cp_zmb)> <output source dir>
Writes world.bin, colmap.hkx, navgraph.bin, ents.txt and layout.json (zones, doors, spawners, interactions)
for the level script and the probes.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapgen, hkcm_write

tpl, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
LM = (0.9408, 0.4061)          # borrowed lit texel of a stock floor near the template spawn (moonlit only)
# per-room lightmap texels of the template atlas (lightmap_read.py: secondary BC6H bottom half = baked light colour,
# primary BC4 = sun/moon visibility); IWZ_LM_<ROOM>=u,v overrides one for tuning
ROOM_LM = {
    'arrival':   (0.8018, 0.5645),   # neutral mid indirect
    'hall_ab':   (0.3037, 0.8965),   # neutral low
    'generator': (0.8975, 0.3965),   # warm
    'hall_bc':   (0.3037, 0.8965),
    'platform':  (0.7744, 0.5605),   # cool teal
}
for _room in list(ROOM_LM):
    if os.environ.get('IWZ_LM_' + _room.upper()):
        ROOM_LM[_room] = tuple(float(c) for c in os.environ['IWZ_LM_' + _room.upper()].split(','))


def room_lm(room):
    return LM if os.environ.get('IWZ_LM_GLOBAL') == '1' else ROOM_LM.get(room, LM)
DOOR_W, DOOR_H = 160, 200

M = {
    'concrete': 'w/concrete_floor_polished_01', 'panel': 'w/concrete_wall_panel_01', 'tile': 'w/ceiling_tile_01',
    'brick': 'w/frag_brick_painted_white_01', 'plate': 'w/metal_bare_diamondplate_01',
}

# rooms: name, (x0, y0, x1, y1), height, floor/wall/ceiling materials, openings {side: [(center, width)]}
ROOMS = [
    ('arrival',   (0, 4800, 1024, 5824),    288, ('concrete', 'panel', 'tile'),  {'east': [5312]}),
    ('hall_ab',   (1024, 5232, 1536, 5392), 224, ('plate', 'brick', 'tile'),     {'west': [5312], 'east': [5312]}),
    ('generator', (1536, 4928, 2304, 5696), 320, ('plate', 'panel', 'tile'),     {'west': [5312], 'north': [1920]}),
    ('hall_bc',   (1840, 5696, 2000, 6144), 224, ('plate', 'brick', 'tile'),     {'south': [1920], 'north': [1920]}),
    ('platform',  (1280, 6144, 2560, 6912), 352, ('concrete', 'brick', 'tile'),  {'south': [1920]}),
]
# props (solid boxes): room, (x0, y0, x1, y1), height, material
PROPS = [
    ('arrival',   (448, 5248, 576, 5376), 288, 'brick'),
    ('generator', (1856, 5248, 1984, 5376), 96, 'plate'),
    ('platform',  (1600, 6464, 1728, 6592), 352, 'brick'),
    ('platform',  (2112, 6464, 2240, 6592), 352, 'brick'),
]

m = mapgen.Mesh()


QUAD_SERIAL = [0]


def quad(mat, room, pts, n, t, collide=True):
    # IWZ_SURFACE_PER_QUAD: one render surface per quad (each gets its own local visibility slot)
    key = '%s|%s' % (M[mat], room)
    if os.environ.get('IWZ_SURFACE_PER_QUAD') == '1':
        QUAD_SERIAL[0] += 1
        key += '|%d' % QUAD_SERIAL[0]
    m.quad(key, *pts, n, t, room_lm(room), collide=collide)


def wall(room, side, box, h, mat, openings):
    """One inward-facing wall with door openings (full-height panels and a lintel over each opening)."""
    x0, y0, x1, y1 = box
    if side in ('south', 'north'):
        a, b, fixed = x0, x1, (y0 if side == 'south' else y1)
    else:
        a, b, fixed = y0, y1, (x0 if side == 'west' else x1)
    spans, cur = [], a
    for c in sorted(openings):
        lo, hi = c - DOOR_W / 2, c + DOOR_W / 2
        if lo > cur: spans.append((cur, lo, 0, h))
        if h > DOOR_H: spans.append((max(lo, a), min(hi, b), DOOR_H, h))
        cur = hi
    if cur < b: spans.append((cur, b, 0, h))
    for s0, s1, z0, z1 in spans:
        if s1 <= s0: continue
        if side == 'south':
            pts = [(s1, fixed, z0), (s0, fixed, z0), (s0, fixed, z1), (s1, fixed, z1)]; n, t = (0, 1, 0), (-1, 0, 0)
        elif side == 'north':
            pts = [(s0, fixed, z0), (s1, fixed, z0), (s1, fixed, z1), (s0, fixed, z1)]; n, t = (0, -1, 0), (1, 0, 0)
        elif side == 'west':
            pts = [(fixed, s0, z0), (fixed, s1, z0), (fixed, s1, z1), (fixed, s0, z1)]; n, t = (1, 0, 0), (0, 1, 0)
        else:
            pts = [(fixed, s1, z0), (fixed, s0, z0), (fixed, s0, z1), (fixed, s1, z1)]; n, t = (-1, 0, 0), (0, -1, 0)
        quad(mat, room, pts, n, t)


layout = {'rooms': {}, 'doors': [], 'spawners': [], 'starts': [], 'props': []}
for name, box, h, (fm, wm, cm), openings in ROOMS:
    x0, y0, x1, y1 = box
    quad(fm, name, [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], (0, 0, 1), (1, 0, 0))
    quad(cm, name, [(x0, y1, h), (x1, y1, h), (x1, y0, h), (x0, y0, h)], (0, 0, -1), (1, 0, 0))
    long_axis_corridor = name.startswith('hall_')
    for side in ('south', 'north', 'west', 'east'):
        ops = openings.get(side, [])
        # corridor ends are fully open (the door is the corridor cross-section)
        if long_axis_corridor and ops:
            continue
        wall(name, side, box, h, wm, ops)
    layout['rooms'][name] = {'box': box, 'height': h}

for room, (x0, y0, x1, y1), h, mat in PROPS:
    mapgen.box_faces(m, (x0, y0, 0), (x1, y1, h), {'floor': M[mat] + '|' + room, 'wall': M[mat] + '|' + room,
                                                    'ceiling': M[mat] + '|' + room}, room_lm(room), skip=('bottom',) + (('top',) if h >= 288 else ()))
    layout['props'].append({'room': room, 'box': (x0, y0, x1, y1), 'height': h})

# decor: stock models placed as script_model map entities (the engine spawns them at load), with an optional
# invisible collision box (half sizes) so players and zombies do not walk through the larger pieces
# (room, model, (x, y, z), yaw, clip half size or None)
DECOR = [
    # arrival: fluorescent hall with lockers
    ('arrival', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (256, 5056, 288), 0, None),
    ('arrival', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (768, 5056, 288), 0, None),
    ('arrival', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (256, 5568, 288), 0, None),
    ('arrival', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (768, 5568, 288), 0, None),
    ('arrival', 'dns_locker_set_01', (24, 5312, 0), 0, (24, 96, 48)),
    ('arrival', 'park_trash_can_blue_01', (60, 4860, 0), 45, (16, 16, 24)),
    ('arrival', 'park_trash_can_red_01', (964, 5764, 0), 225, (16, 16, 24)),
    ('arrival', 'pardon_our_dust_sign', (980, 5440, 0), 180, (12, 24, 32)),
    # corridor to the generator room
    ('hall_ab', 'pipe_metal_painted_straight_128_gray', (1088, 5244, 200), 0, None),
    ('hall_ab', 'pipe_metal_painted_straight_128_gray', (1216, 5244, 200), 0, None),
    ('hall_ab', 'pipe_metal_painted_straight_128_gray', (1344, 5244, 200), 0, None),
    ('hall_ab', 'pipe_metal_painted_straight_128_gray', (1472, 5244, 200), 0, None),
    # generator room: industrial lamps, the generator, tanks and crates
    ('generator', 'light_interior_ceiling_industrial_lamp_01_mounted_on', (1728, 5120, 320), 0, None),
    ('generator', 'light_interior_ceiling_industrial_lamp_01_mounted_on', (2112, 5120, 320), 0, None),
    ('generator', 'light_interior_ceiling_industrial_lamp_01_mounted_on', (1728, 5504, 320), 0, None),
    ('generator', 'light_interior_ceiling_industrial_lamp_01_mounted_on', (2112, 5504, 320), 0, None),
    ('generator', 'zom_machinery_generator_portable_01', (1920, 5312, 96), 0, None),
    ('generator', 'equipment_oxygen_tank_01', (1570, 4962, 0), 0, (14, 14, 40)),
    ('generator', 'equipment_oxygen_tank_01', (1600, 4962, 0), 30, (14, 14, 40)),
    ('generator', 'ammo_crate_01_dust', (2250, 5650, 0), 90, (24, 16, 16)),
    ('generator', 'beacon_pallet_01', (2240, 4990, 0), 0, (32, 32, 8)),
    ('generator', 'fac_trash_bin', (1580, 5650, 0), 0, (20, 20, 28)),
    # corridor to the platform
    ('hall_bc', 'pipe_metal_painted_straight_128_red', (1852, 5760, 190), 90, None),
    ('hall_bc', 'pipe_metal_painted_straight_128_red', (1852, 5888, 190), 90, None),
    ('hall_bc', 'pipe_metal_painted_straight_128_red', (1852, 6016, 190), 90, None),
    # platform: hanging lamps, benches, railing along the track edge
    ('platform', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (1472, 6336, 352), 0, None),
    ('platform', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (1920, 6336, 352), 0, None),
    ('platform', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (2368, 6336, 352), 0, None),
    ('platform', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (1472, 6720, 352), 0, None),
    ('platform', 'zmb_light_interior_hanging_ceiling_lamp_01_on', (2368, 6720, 352), 0, None),
    ('platform', 'furniture_park_bench_01_blue', (1664, 6200, 0), 0, (48, 16, 20)),
    ('platform', 'furniture_park_bench_01_blue', (2176, 6200, 0), 0, (48, 16, 20)),
    ('platform', 'park_trash_can_blue_01', (1904, 6176, 0), 0, (16, 16, 24)),
    ('platform', 'beacon_lab_railing_96', (1376, 6880, 0), 0, None),
    ('platform', 'beacon_lab_railing_96', (1472, 6880, 0), 0, None),
    ('platform', 'beacon_lab_railing_96', (2368, 6880, 0), 0, None),
    ('platform', 'beacon_lab_railing_96', (2464, 6880, 0), 0, None),
]
if os.environ.get('IWZ_NO_DECOR') == '1':
    DECOR = []
for room, model, (x, y, z), yaw, clip in DECOR:
    if clip:
        hx, hy, hz = clip
        mn, mx = (x - hx, y - hy, 0), (x + hx, y + hy, z + 2 * hz)
        # collision only: the box's triangles, outward faces
        corners = [(mn[0], mn[1]), (mx[0], mn[1]), (mx[0], mx[1]), (mn[0], mx[1])]
        for k in range(4):
            (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
            p0, p1, p2, p3 = (ax, ay, mn[2]), (bx, by, mn[2]), (bx, by, mx[2]), (ax, ay, mx[2])
            m.col += [(p0, p1, p2), (p0, p2, p3)]
        top = [(c[0], c[1], mx[2]) for c in corners]
        m.col += [(top[0], top[1], top[2]), (top[0], top[2], top[3])]
        PROPS_NAV = layout.setdefault('decor_clips', [])
        PROPS_NAV.append({'room': room, 'box': (mn[0], mn[1], mx[0], mx[1])})

nv, ni, ns, wb = mapgen.write_world(m, os.path.join(out, 'world.bin'))
col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in m.col]
blob, info = hkcm_write.encode(col, os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.colmap.hkx'), tag=382,
                               max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')))
open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)

# navmesh: 32-unit cells inside rooms (props and a 16-unit wall margin excluded); links only inside a room or
# across a door opening
CELL = 32
cells, owner = {}, {}
for name, (x0, y0, x1, y1), h, _, _ in ROOMS:
    for i in range(int(x0 // CELL), int(x1 // CELL)):
        for j in range(int(y0 // CELL), int(y1 // CELL)):
            cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
            if not (x0 + 16 <= cx <= x1 - 16 and y0 + 16 <= cy <= y1 - 16):
                if not name.startswith('hall_'):
                    continue
                # corridor cells reach their open ends
                if not (x0 <= cx <= x1 and y0 <= cy <= y1): continue
                if name == 'hall_ab' and not (y0 + 16 <= cy <= y1 - 16): continue
                if name == 'hall_bc' and not (x0 + 16 <= cx <= x1 - 16): continue
            if any(px0 - 16 < cx < px1 + 16 and py0 - 16 < cy < py1 + 16 for r, (px0, py0, px1, py1), _, _ in PROPS if r == name):
                continue
            if any(c['box'][0] - 16 < cx < c['box'][2] + 16 and c['box'][1] - 16 < cy < c['box'][3] + 16
                   for c in layout.get('decor_clips', [])):
                continue
            cells[(i, j)] = 0
            owner[(i, j)] = name


def link(a, b):
    return owner[a] == owner[b] or {owner[a], owner[b]} in ({'arrival', 'hall_ab'}, {'hall_ab', 'generator'},
                                                            {'generator', 'hall_bc'}, {'hall_bc', 'platform'})


nav, nareas = mapgen.nav_graph(cells, CELL, link)
open(os.path.join(out, 'navgraph.bin'), 'wb').write(nav)

# entities
ws = mapgen.stock_worldspawn(os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.ents'))
ents = []
for x, y in [(160, 4960), (864, 4960), (160, 5664), (864, 5664)]:
    ents.append([('157', 'script_struct'), ('822', 'default_player_start'), ('543', '%d %d 0' % (x, y)), ('65', '0 0 0')])
    layout['starts'].append((x, y, 0))
ents.append([('157', 'mp_global_intermission'), ('543', '512 5312 200'), ('65', '15 0 0')])
SPAWNERS = {
    'arrival':   [(80, 4880), (944, 4880), (80, 5744), (944, 5744)],
    'generator': [(1616, 5008), (2224, 5008), (1616, 5616), (2224, 5616)],
    'platform':  [(1360, 6224), (2480, 6224), (1360, 6832), (2480, 6832), (1920, 6832)],
}
# zone volumes (info_volume, generated trigger models): the stock zombie spawning activates the volume the
# players are in and spawns from the structs it targets
triggers = []
for k, zone in enumerate(SPAWNERS):
    x0, y0, x1, y1 = dict((r[0], r[1]) for r in ROOMS)[zone]
    h = dict((r[0], r[2]) for r in ROOMS)[zone]
    triggers.append('28000001 %g %g %g' % ((x1 - x0) / 2, (y1 - y0) / 2, h / 2))
    # IWZ_VOLUME_MODEL: reuse a template box trigger model (its entity physics shape ships with the template)
    vm = os.environ.get('IWZ_VOLUME_MODEL')
    ents.append([('157', 'info_volume'), ('822', 'spawn_volume'),
                 ('543', '%g %g %g' % ((x0 + x1) / 2, (y0 + y1) / 2, 128 if vm else h / 2)),
                 ('497', ('?' + vm) if vm else '?IWZ%d' % k), ('636', zone), ('820', zone + '_spawner')])
open(os.path.join(out, 'triggers.txt'), 'w', newline='\n').write('\n'.join(triggers) + '\n')
for zone, pts in SPAWNERS.items():
    for x, y in pts:
        ents.append([('157', 'script_struct'), ('822', zone + '_spawner'), ('638', 'static'), ('61056', 'zombie_base_normal'),
                     ('543', '%d %d 8' % (x, y)), ('65', '0 0 0')])
        layout['spawners'].append({'zone': zone, 'origin': (x, y, 0)})
for room, model, (x, y, z), yaw, clip in DECOR:
    ents.append([('157', 'script_model'), ('497', model), ('543', '%g %g %g' % (x, y, z)), ('65', '0 %g 0' % yaw)])
import sz_interactions
relocations = sz_interactions.add(ents)
open(os.path.join(out, 'scriptables.txt'), 'w', newline='\n').write('\n'.join(relocations) + '\n')
open(os.path.join(out, 'ents.txt'), 'w', newline='\n').write(mapgen.ents_text(ws, ents))
layout['doors'] = [{'from': 'arrival', 'to': 'generator', 'origin': (1024, 5312, 0), 'cost': 750},
                   {'from': 'generator', 'to': 'platform', 'origin': (1920, 5696, 0), 'cost': 1000}]
json.dump(layout, open(os.path.join(out, 'layout.json'), 'w'), indent=1)

# lighting.txt: the light grid ambient of the generated world (constant SH term per colour channel and the share
# of light coming from above); a global ambient, then one box per room (probes 256 units around each room)
# (engine check iwz-lit2 / iwz-lm2: models stayed dark at a third of these values)
AMBIENT = (0.30, 0.30, 0.33, 0.4)
ROOM_LIGHT = {
    'arrival':   (1.02, 1.05, 1.14, 0.6),   # cool fluorescent entrance hall
    'hall_ab':   (0.66, 0.60, 0.54, 0.5),
    'generator': (1.38, 0.96, 0.54, 0.7),   # warm industrial generator room
    'hall_bc':   (0.66, 0.60, 0.54, 0.5),
    'platform':  (0.72, 1.02, 1.14, 0.6),   # teal station platform
}
scale = float(os.environ.get('IWZ_AMBIENT_SCALE', '1'))
light_lines = ['ambient %.4f %.4f %.4f %.2f' % (AMBIENT[0] * scale, AMBIENT[1] * scale, AMBIENT[2] * scale, AMBIENT[3])]
for name, (x0, y0, x1, y1), h, _, _ in ROOMS:
    r, g, b, up = ROOM_LIGHT[name]
    light_lines.append('room %d %d %d %d %d %d %.4f %.4f %.4f %.2f' % (x0 - 256, y0 - 256, -256, x1 + 256, y1 + 256, h + 256,
                                                                    r * scale, g * scale, b * scale, up))
open(os.path.join(out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(light_lines) + '\n')
print('verts', nv, 'indices', ni, 'surfaces', ns, 'bounds', wb, 'collision', info, 'nav areas', nareas, 'nav bytes', len(nav))
