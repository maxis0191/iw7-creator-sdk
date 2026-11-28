r"""arcade_shell: the Underpass Arcade rebuilt as architecture (worker A2, 27 Nov 2026; PLAN section 3).

    set STUDIO_ROOT=C:\studio
    python arcade_shell.py [folder]          writes the document (default C:\studio-data\sz\film\arcade\shell\doc) and anchors.json beside it

A 1978 shopping underpass of a metro station, sealed since New Year's Eve 1984: a hall of tiled walls, one colonnade at pitch 288, a
suspended ceiling with half its panels dead, and four shopfronts of four designs (Needle Drop, Copy Stop, Hole Number Nine, Heel & Key).
This builder owns the room, the fronts, the fixed joinery, the light and the gameplay objects. Goods are placed by the next workers on the
anchors written to anchors.json. Every light is baked (`group: emergency`); no runtime light.
Proven mechanics taken from the rejected round-19 builder (arcade_layer14.py): the D4 doorway cut, the door and zone, the base bench removal.
"""
import copy
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import Map  # noqa: E402
from studio import build as B  # noqa: E402
from studio import fixtures as FX  # noqa: E402
import shellgeo as G  # noqa: E402
import standins as S  # noqa: E402
import shell_hall as SH  # noqa: E402

# ------------------------------------------------------------------------------------------------ materials: ONE table (the swap to our own
# tile pictures, when B.material lands, is an edit here)
MAT = {
    'tile': 'w/dt_tile_ceramic_white',            # wall tile (the cp_disco station's own wall tile)
    'tile_dmg': 'w/dt_tile_ceramic_white_dmg',    # its damaged twin, in patches
    'band': 'w/ceramic_tile_01_orange',           # the orange band course
    'dark': 'w/fac_tile_black_01',                # skirting, column bases, bulkhead
    'floor': 'w/sz_arcade_quarry',                # the brown / burnt orange floor: OUR quarry tiles (OWN below; pass 2: the stock
                                                  # linoleum_floor_tiles_orange_01 read as large plain orange squares)
    'slab': 'w/plaster_wall_04_grey_dark_02',     # the structural soffit above the suspended ceiling
    'ceil': 'w/ceiling_tile_01',                  # ceiling panels
    'ceil_stain': 'w/ceiling_waterstains1',       # stained panels
    'panel_on': 'w/emissive_light_panel_white',   # lit panel (emissive; pass 3: plastic_wall_panel_light_02_on read dim grey)
    'panel_off': 'w/plastic_wall_panel_light_02_off',  # dead panel
    'hole': 'w/metal_painted_01_black',           # a missing panel: the black plenum
    'tbar': 'w/metal_aluminum_trim_03',           # the ceiling grid
    'alu': 'w/metal_aluminum_brushed_clearcoat',  # shopfront frames
    'alu_black': 'w/metal_painted_01_black',
    'alu_white': 'w/metal_panel_painted_01_white',
    'glass': 'w/glass_clear_generic_01',
    'shutter': 'w/cp_disco_metal_door_rollup_01',   # pass 2: door_metal_rollup_grey_large_01 read as rows of white plates
    'housing': 'w/metal_painted_wall_panel_04',
    'steel': 'w/beacon_brushedmetal_panels_green',  # Shelter 7 blast door leaf
    'steel_frame': 'w/metal_painted_04',
    'wheel': 'w/zmb_brushed_metal_01_red',
    'chrome': 'w/metal_chrome_trim_03',
    'rubber': 'w/rubber_trim_black',
    'cream_paint': 'w/metal_panel_painted_01_white',
    'back': 'w/plaster_wall_04_grey',             # back rooms
    'back_floor': 'w/concrete_tiles_01',
    'cork': 'w/wood_antique_panel_trim_01',
    'pegboard': 'w/sz_arcade_pegboard',           # OUR brown pegboard (pass 2: the stock perforated panel read cyan)
}
TILES = r'C:\studio-data\sz\film\art\arcade\tiles'        # drawn by film/tiles.py
OWN = {   # B.material: name -> its pictures; the table above names them as w/<name>
    'sz_arcade_quarry': dict(color=TILES + r'\floor_quarry2_c.png', gloss=TILES + r'\floor_quarry2_g.png', tile=384.0),   # L1 (C4): muted, see tiles.floor2
    'sz_arcade_pegboard': dict(color=TILES + r'\pegboard_c.png', gloss=0.25, tile=32.0),
}
SHOP_MAT = {   # per shop: walls, floor, ceiling, frame, fascia box, accent, joinery
    'needle_drop': dict(wall='w/plaster_wall_04_grey_dark_01', floor='w/stone_marble_tile_checker_01', ceil='w/plaster_wall_04_grey_dark_02',
                        frame=MAT['alu_black'], fascia=MAT['alu_black'], accent=MAT['band'], join=MAT['alu_black']),
    'copy_stop': dict(wall='w/plaster_wall_04_white', floor='w/linoleum_floor_tiles_02', ceil='w/ceiling_tile_01',
                      frame=MAT['alu_white'], fascia='w/zmb_brushed_metal_01_blue', accent='w/plastic_wall_plain_blue_01', join=MAT['alu_white']),
    'hole_nine': dict(wall='w/paint_pink_wall_semigloss', floor='w/stone_marble_tile_checker_01_brown', ceil='w/plaster_wall_04_beige',
                      frame=MAT['alu'], fascia='w/wood_antique_panel_trim_01', accent='w/wood_antique_panel_trim_01', join='w/wood_antique_panel_trim_01'),
    'heel_key': dict(wall='w/plaster_wall_01_beige', floor='w/wood_tile_herringbone_glossy_01', ceil='w/plaster_wall_04_beige',
                     frame=MAT['alu'], fascia='w/plastic_wall_plain_red_01', accent='w/plastic_wall_plain_red_01', join='w/wood_antique_panel_trim_01'),
}

BASE_EMIT = r'C:\studio-data\sz\film\base_lit'
RECIPE_FROM = r'C:\studio-data\sz\film\allbaked2\doc\map.json'
OUT = r'C:\studio-data\sz\film\arcade\shell\doc'

# ------------------------------------------------------------------------------------------------ the plan (PLAN section 3)
X0, X1, Y0, Y1, YB, H = -3000.0, -1200.0, 3500.0, 4300.0, 4600.0, 256.0
WT = 16.0
XW, XE, YS = X0 + WT, X1 - WT, Y0 + WT          # inner faces: west, east, south
DOOR_Y0, DOOR_Y1, DOOR_Z = 3804.0, 3996.0, 224.0
GRID_Z = 244.0                                   # the suspended ceiling (hall clear height)
BULK_Y, BULK_Z = 4232.0, 240.0                   # the bulkhead over the shop line: face y, underside z
FASCIA = (172.0, 240.0, 4268.0)                  # z0, z1, face y of the fascia boxes
HOUSING = (150.0, 172.0)                         # roll-shutter housing z
OPEN_Z = 150.0                                   # top of the shop openings
UNIT_H = 232.0
PART_Y = 4480.0                                  # partition of the back rooms
COL_Y, COL_PITCH, COL_W = 3760.0, 288.0, 40.0
COLS = [-2860.0 + COL_PITCH * k for k in range(6)]
UNITS = {   # name: (x0, x1, title)
    'needle_drop': (-2960.0, -2640.0),
    'copy_stop': (-2630.0, -1980.0),
    'hole_nine': (-1970.0, -1650.0),
    'heel_key': (-1640.0, -1320.0),
}
SHUTTER_STOP = {'needle_drop': 0.25, 'copy_stop': 0.0, 'hole_nine': 0.0, 'heel_key': 0.2}    # Heel & Key 0.5 -> 0.2 (A3a request 1: the pegboard and bench in view)    # share of the opening the curtain covers
LIGHT_K = float(os.environ.get('A2_LIGHT_K', '2.5'))      # pass 1: at 1.0 the hall read mean luma 4.5 of 255
RADIUS_K = float(os.environ.get('A2_RADIUS_K', '1.6'))

REPORT = {'standins': [], 'art': [], 'fallbacks': [], 'refused': []}
ANCHORS = []


def anchor(name, box, facing, what):
    ANCHORS.append({'name': name, 'box': [round(v, 1) for v in box], 'facing': facing, 'for': what})


def bx(m, id, box, mat, mode=None, uv=None):
    return B.box(m, box, mat, mode=mode or 'both', id=id, uv=uv)


def rbox(m, id, box, mat, uv=None):
    """a render-only skin (a tile course on a wall, a trim)"""
    return B.box(m, box, mat, mode='render', id=id, uv=uv)


def mesh(m, id, mat, parts, mode='render'):
    tris, uvs = parts
    return B.mesh(m, mat, tris=tris, uvs=uvs, mode=mode, id=id)


def picture(m, id, name, at, normal, size, **kw):
    path, stand = S.slot(name)
    (REPORT['standins'] if stand else REPORT['art']).append(name)
    return B.sign(m, image=path, at=at, normal=normal, size=size, id=id, **kw)


def picture2(m, id, name, centre, axis, size):
    """a picture hanging free (a banner across the hall): two signs back to back, 0.6 apart, readable from both sides"""
    n = (1.0, 0.0, 0.0) if axis == 'x' else (0.0, 1.0, 0.0)
    for s, tag in ((1.0, 'a'), (-1.0, 'b')):
        at = [centre[i] - s * n[i] * 3.3 for i in range(3)]
        picture(m, '%s_%s' % (id, tag), name, at, [s * n[0], s * n[1], 0.0], size)


LIGHTS = []    # (id, role) for the report


KEY_BAKE = os.environ.get('L1_KEY_BAKE', 'bounce')     # PLAN decision 3 as revised 28 Nov (LIGHTING-GAP W1): key lights are always-on runtime lights whose
#                                                        bounce is baked ('bounce'); 'baked' rebuilds the all-baked arcade of passes 1 to 8 for A/B


def fix(m, kind, at, facing=0.0, role='hall', key=False, **kw):
    """a stock fixture with its light in the emergency group: the fill baked; a key light (key=True: a shop's pool and sign lights, the directory's lamp)
    a runtime light with its bounce baked (KEY_BAKE)"""
    if 'intensity' in kw:
        kw['intensity'] = kw['intensity'] * LIGHT_K
    kw['radius'] = kw.get('radius', 1.0) * RADIUS_K      # pass 1 score: the fixture radii as given gave a median of 128 (rule 10: 175 or more)
    ids = B.fixture(m, kind, at, facing, group='emergency', bake=KEY_BAKE if key else 'baked', layer='lights', **kw)
    for lid in ids[1:]:
        LIGHTS.append((lid, role))
    return ids


def aim(m, ids, target):
    """point the spot light(s) of a fixture at a point"""
    for lid in ids[1:]:
        o = m.get(lid)
        d = [target[i] - o['origin'][i] for i in range(3)]
        ln = math.sqrt(sum(c * c for c in d))
        m.update(lid, dir=[round(c / ln, 4) for c in d])
    return ids


def lamp(m, id, origin, role, key=False, **kw):
    """a light without a fixture model of its own (a lit ceiling panel's soft spot, a machine's glow): emergency; baked, or a key light (see fix)"""
    kw['intensity'] = kw.get('intensity', 1.0) * LIGHT_K
    if key and KEY_BAKE == 'bounce':
        kw.update(runtime=True, bake='bounce')
    B.light(m, origin, group='emergency', layer='lights', id=id, **kw)
    LIGHTS.append((id, role))


# ================================================================================================ the hall
def hall(m):
    m.use('arcade_door')
    B.doorway(m, [X1 - 4.0, DOOR_Y0, 0.0, X1 + 4.0, DOOR_Y1, DOOR_Z], MAT['tile'], id='arcade_doorway')
    B.replace(m, box=[-1170, 3900, -1, -1106, 4100, 100], what=['props'], id='clear_bench_props')           # FE24: the base bench in D4
    B.replace(m, box=[-1170, 3900, 2, -1106, 4100, 100], what=['collision'], clip=True, id='clear_bench_clip')
    m.use('shell')
    B.floor(m, [X0, Y0, X1, Y1], 0.0, MAT['floor'], id='hall_floor')
    B.ceiling(m, [X0, Y0, X1, Y1], H, MAT['slab'], id='hall_slab')
    B.wall(m, [X0, Y0, 0.0, X1, YS, H], MAT['tile'], axis='x', id='wall_south')
    B.wall(m, [X0, YS, 0.0, XW, Y1, H], MAT['tile'], axis='y', openings=[(3852.0, 3948.0, 0.0, 112.0)], id='wall_west')
    B.wall(m, [XE, YS, 0.0, X1, Y1, H], MAT['tile'], axis='y', openings=[(DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z)], id='wall_east')
    bx(m, 'fill_west_end', [X0, Y1, 0.0, UNITS['needle_drop'][0], YB, H], MAT['tile'])
    for a, b in (('needle_drop', 'copy_stop'), ('copy_stop', 'hole_nine'), ('hole_nine', 'heel_key')):
        bx(m, 'fill_%s_%s' % (a, b), [UNITS[a][1], Y1, 0.0, UNITS[b][0], YB, H], MAT['tile'])
    bx(m, 'bulkhead', [XW, BULK_Y, BULK_Z, XE, Y1, H], MAT['dark'])
    rbox(m, 'bulkhead_band', [XW, BULK_Y - 0.6, BULK_Z + 4.0, XE, BULK_Y, BULK_Z + 10.0], MAT['band'])
    # the floor: a dark border along the walls and a band where the hall meets the shop line
    rbox(m, 'floor_border_s', [XW, YS, 0.0, XE, YS + 18.0, 0.25], MAT['dark'])
    rbox(m, 'floor_border_w', [XW, YS + 18.0, 0.0, XW + 18.0, Y1, 0.25], MAT['dark'])
    rbox(m, 'floor_border_e', [XE - 18.0, YS + 18.0, 0.0, XE, DOOR_Y0 - 10.0, 0.25], MAT['dark'])
    rbox(m, 'floor_border_e2', [XE - 18.0, DOOR_Y1 + 10.0, 0.0, XE, Y1, 0.25], MAT['dark'])
    rbox(m, 'floor_border_n', [XW + 18.0, Y1 - 24.0, 0.0, XE - 18.0, Y1, 0.25], MAT['dark'])
    tile_courses(m)
    columns(m)
    ceiling(m)


def tile_courses(m):
    """the dado of the five-tile kit on the three hall walls: dark skirting, white field, an orange band course, damaged patches"""
    def courses(tag, face_box, axis, skip=()):
        a0, a1 = (face_box[0], face_box[3]) if axis == 'x' else (face_box[1], face_box[4])
        spans = [(a0, a1)]
        for s0, s1 in skip:
            spans = [p for q in spans for p in ((q[0], min(q[1], s0)), (max(q[0], s1), q[1])) if p[1] - p[0] > 1.0]
        for k, (s0, s1) in enumerate(spans):
            for nm, z0, z1, mat in (('skirt', 0.0, 10.0, MAT['dark']), ('band', 58.0, 74.0, MAT['band']), ('band2', 220.0, 228.0, MAT['band'])):
                b = list(face_box)
                if axis == 'x':
                    b[0], b[3] = s0, s1
                else:
                    b[1], b[4] = s0, s1
                b[2], b[5] = z0, z1
                rbox(m, 'course_%s_%s_%d' % (tag, nm, k), b, mat)
    courses('s', [XW, YS, 0, XE, YS + 0.6, 0], 'x')
    courses('w', [XW, YS, 0, XW + 0.6, BULK_Y, 0], 'y', skip=[(3836.0, 3964.0)])
    courses('e', [XE - 0.6, YS, 0, XE, BULK_Y, 0], 'y', skip=[(DOOR_Y0 - 14.0, DOOR_Y1 + 14.0)])
    rng = random.Random(1978)
    n = 0
    for wall, (a0, a1) in (('s', (XW + 40, XE - 40)), ('w', (YS + 40, BULK_Y - 40)), ('e', (YS + 40, BULK_Y - 40))):
        for k in range({'s': 9, 'w': 3, 'e': 2}[wall]):
            w, h = rng.uniform(30, 96), rng.uniform(24, 70)
            c = rng.uniform(a0 + w, a1 - w)
            z = rng.choice((rng.uniform(12, 50), rng.uniform(80, 200)))
            if wall == 'e' and DOOR_Y0 - 40 < c < DOOR_Y1 + 40:
                continue
            if wall == 'w' and 3820 < c < 3980:
                continue
            if wall == 's':
                b = [c - w / 2, YS, z, c + w / 2, YS + 0.8, z + h]
            elif wall == 'w':
                b = [XW, c - w / 2, z, XW + 0.8, c + w / 2, z + h]
            else:
                b = [XE - 0.8, c - w / 2, z, XE, c + w / 2, z + h]
            rbox(m, 'tile_patch_%s_%d' % (wall, k), b, MAT['tile_dmg'])
            n += 1
    REPORT['tile_patches'] = n


def columns(m):
    """one row of square columns at pitch 288 on the south third, clad in the hall's own tile: dark base, white shaft, two orange bands"""
    h = COL_W / 2.0
    for k, x in enumerate(COLS):
        bx(m, 'col_%d' % k, [x - h, COL_Y - h, 0.0, x + h, COL_Y + h, H], MAT['tile'])
        rbox(m, 'col_%d_base' % k, [x - h - 1.5, COL_Y - h - 1.5, 0.0, x + h + 1.5, COL_Y + h + 1.5, 16.0], MAT['dark'])
        rbox(m, 'col_%d_band' % k, [x - h - 0.6, COL_Y - h - 0.6, 58.0, x + h + 0.6, COL_Y + h + 0.6, 74.0], MAT['band'])
        rbox(m, 'col_%d_band2' % k, [x - h - 0.6, COL_Y - h - 0.6, 196.0, x + h + 0.6, COL_Y + h + 0.6, 212.0], MAT['band'])
        if k in (1, 4):
            rbox(m, 'col_%d_dmg' % k, [x - h - 0.8, COL_Y + h, 90.0, x + 6.0, COL_Y + h + 0.8, 150.0], MAT['tile_dmg'])


# ceiling modules (48 x 48) from the south-west inner corner
GX0, GY0, MOD = XW, YS, 48.0
NI, NJ = int((XE - XW) // MOD) + 1, int((BULK_Y - YS) // MOD) + 1
LIVE = [(2, 2), (10, 2), (18, 2), (26, 2), (34, 2), (6, 12), (22, 12), (14, 6), (30, 6), (6, 9), (22, 9), (34, 12)]   # 12 pools (pass 1: 7 read as a black lid)
DEAD = [(6, 2), (14, 2), (30, 2), (2, 12), (14, 12), (18, 12), (30, 12), (10, 8), (26, 8)]
HOLES = [(14, 7), (22, 4), (31, 9), (5, 10), (35, 5), (19, 13)]                   # missing panels: the black plenum
STAINS = [(3, 5), (8, 9), (12, 3), (17, 10), (21, 6), (27, 11), (29, 3), (33, 13)]


FILL_LANE, FILL_MID, FILL_SOUTH, FILL_TUBE = (float(v) for v in os.environ.get('L1_FILL', '0.15,0.2,0.3,0.6').split(','))
FILL_VARY = (1.0, 0.7, 1.15, 0.8, 0.95, 1.1, 0.75, 1.2, 0.85, 1.0, 0.7, 0.9)     # per live panel: a failing ceiling is not even


def fill_k(k, j):
    """the ceiling fill of live panel k in row j (L1, LIGHTING-GAP C5, 28 Nov): 1.0 everywhere gave 1.8 to 1 between a shop's pool and mid hall
    (`studio light`); the rows over the shop lane (j >= 12) and the middle (j 9) are dimmest so that the fronts' pools read, the south rows a little
    more; each panel varied by FILL_VARY"""
    base = FILL_LANE if j >= 12 else FILL_MID if j >= 9 else FILL_SOUTH
    return round(base * FILL_VARY[k % len(FILL_VARY)], 3)


def module(i, j):
    x0, y0 = GX0 + i * MOD, GY0 + j * MOD
    return [x0, y0, min(x0 + MOD, XE), min(y0 + MOD, BULK_Y)]


def ceiling(m):
    """the suspended ceiling: one panel plane with a 48 grid of T-bars, lit panels (emissive), dead ones, missing ones, stained ones"""
    m.use('ceiling')
    rbox(m, 'grid_plane', [XW, YS, GRID_Z, XE, BULK_Y, GRID_Z + 1.0], MAT['ceil'],
         uv={'bottom': {'tile': [MOD, MOD], 'offset': [0.0, 0.0]}})
    for i in range(1, NI):
        x = GX0 + i * MOD
        if x < XE - 1:
            rbox(m, 'tbar_x_%d' % i, [x - 0.7, YS, GRID_Z - 1.0, x + 0.7, BULK_Y, GRID_Z], MAT['tbar'])
    for j in range(1, NJ):
        y = GY0 + j * MOD
        if y < BULK_Y - 1:
            rbox(m, 'tbar_y_%d' % j, [XW, y - 0.7, GRID_Z - 1.0, XE, y + 0.7, GRID_Z], MAT['tbar'])
    for tag, lst, mat in (('live', LIVE, MAT['panel_on']), ('dead', DEAD, MAT['panel_off']), ('hole', HOLES, MAT['hole']), ('stain', STAINS, MAT['ceil_stain'])):
        for i, j in lst:
            x0, y0, x1, y1 = module(i, j)
            rbox(m, 'panel_%s_%d_%d' % (tag, i, j), [x0 + 0.8, y0 + 0.8, GRID_Z - 0.4, x1 - 0.8, y1 - 0.8, GRID_Z - 0.05], mat)
    for k, (i, j) in enumerate(LIVE):
        x0, y0, x1, y1 = module(i, j)
        lamp(m, 'light_panel_%d' % k, ((x0 + x1) / 2, (y0 + y1) / 2, GRID_Z - 6.0), 'hall', color=(0.88, 1.0, 0.9), radius=250.0,      # the target's greenish fluorescent
             intensity=fill_k(k, j), type='spot', dir=(0.0, 0.0, -1.0), inner=50.0, outer=85.0)
    # tubes over the colonnade, between the columns, hung from the grid: three live, two dead; two dead over the north lane
    for k, x in enumerate([(a + b) / 2 for a, b in zip(COLS, COLS[1:])]):
        if k % 2 == 0:
            fix(m, 'ceiling_tube', (x, COL_Y, GRID_Z - 1.0), 0.0, role='hall', intensity=FILL_TUBE, radius=0.85)      # fill (C5)
        else:
            B.prop(m, 'cp_disco_fluorescent_light_off', (x, COL_Y, GRID_Z - 1.0), yaw=0.0, layer='ceiling', id='tube_dead_%d' % k)
    for k, x in enumerate((-2620.0, -1810.0)):
        B.prop(m, 'cp_disco_fluorescent_light_off', (x, 4120.0, GRID_Z - 1.0), yaw=0.0, layer='ceiling', id='tube_dead_n_%d' % k)


# ================================================================================================ the shop row
def unit_room(m, name, extra_openings=()):
    x0, x1 = UNITS[name]
    sm = SHOP_MAT[name]
    ops = [('s', x0 + 16.0, x1 - 16.0, 0.0, OPEN_Z)] + list(extra_openings)
    B.room(m, [x0, Y1, 0.0, x1, YB, UNIT_H], sm['wall'], sm['floor'], sm['ceil'], openings=ops, thick=16.0, id='room_%s' % name)
    # piers at the unit edges: hall tile on a dark base, standing proud of the shop line
    for side, px in (('w', x0), ('e', x1 - 16.0)):
        bx(m, 'pier_%s_%s' % (name, side), [px, Y1 - 8.0, 0.0, px + 16.0, Y1 + 18.0, BULK_Z], MAT['tile'])
        rbox(m, 'pier_%s_%s_base' % (name, side), [px - 0.8, Y1 - 8.8, 0.0, px + 16.8, Y1 + 18.0, 16.0], MAT['dark'])
        rbox(m, 'pier_%s_%s_band' % (name, side), [px - 0.6, Y1 - 8.6, 58.0, px + 16.6, Y1 + 18.0, 74.0], MAT['band'])
    # the roll-shutter housing and its curtain, stopped at the shop's own height
    a0, a1 = x0 + 16.0, x1 - 16.0
    bx(m, 'housing_%s' % name, [a0, Y1 - 6.0, HOUSING[0], a1, Y1 + 12.0, HOUSING[1]], MAT['housing'])
    share = SHUTTER_STOP[name]
    zb = OPEN_Z - share * OPEN_Z
    if share > 0:
        bx(m, 'shutter_%s' % name, [a0, Y1 - 3.0, zb, a1, Y1 - 1.0, HOUSING[0]], MAT['shutter'])
    rbox(m, 'shutter_bar_%s' % name, [a0, Y1 - 4.5, zb - 3.0, a1, Y1 + 0.5, zb], MAT['alu'])
    REPORT.setdefault('shutters', {})[name] = {'curtain_bottom_z': round(zb, 1), 'covers': share}
    return a0, a1


def fascia(m, name, parts):
    """a fascia box under the bulkhead; its face is a picture sign. parts: [(file, centre x, width)]"""
    z0, z1, fy = FASCIA
    sm = SHOP_MAT[name]
    for k, (fname, cx, w) in enumerate(parts):
        bx(m, 'fascia_%s_%d' % (name, k), [cx - w / 2 - 2.0, fy, z0, cx + w / 2 + 2.0, Y1 - 8.0, z1], sm['fascia'])
        picture(m, 'sign_fascia_%s_%d' % (name, k), fname, (cx, fy, (z0 + z1) / 2), (0.0, -1.0, 0.0), (w, z1 - z0), emissive=1.4)     # illuminated fascia boxes (pass 1: unlit plates did not read)


def frame_v(m, id, x, y, z0, z1, mat, w=3.0, d=3.0):
    rbox(m, id, [x - w / 2, y - d / 2, z0, x + w / 2, y + d / 2, z1], mat)


def glazing(m, tag, x0, x1, y, z0, z1, frame, mull=()):
    """a fixed window: frame members as thin boxes, glass in one pane per bay"""
    rbox(m, '%s_sill' % tag, [x0, y - 2.0, z0 - 3.0, x1, y + 2.0, z0], frame)
    rbox(m, '%s_head' % tag, [x0, y - 2.0, z1, x1, y + 2.0, z1 + 3.0], frame)
    xs = [x0] + list(mull) + [x1]
    for k, x in enumerate(xs):
        frame_v(m, '%s_v%d' % (tag, k), x, y, z0, z1, frame)
    for k in range(len(xs) - 1):
        bx(m, '%s_glass%d' % (tag, k), [xs[k] + 1.5, y - 0.3, z0, xs[k + 1] - 1.5, y + 0.3, z1], MAT['glass'])


def door_leaf(m, tag, hinge, length, y0, frame, swing='y', card=None, card_face=None):
    """an open glazed door leaf standing perpendicular to the front, hinged at (x, y0), swung into the shop along +y"""
    x = hinge
    rbox(m, '%s_stile_a' % tag, [x - 1.5, y0, 2.0, x + 1.5, y0 + 3.0, 138.0], frame)
    rbox(m, '%s_stile_b' % tag, [x - 1.5, y0 + length - 3.0, 2.0, x + 1.5, y0 + length, 138.0], frame)
    rbox(m, '%s_rail_t' % tag, [x - 1.5, y0, 132.0, x + 1.5, y0 + length, 138.0], frame)
    rbox(m, '%s_rail_b' % tag, [x - 1.5, y0, 2.0, x + 1.5, y0 + length, 14.0], frame)
    rbox(m, '%s_glass' % tag, [x - 0.3, y0 + 3.0, 14.0, x + 0.3, y0 + length - 3.0, 132.0], MAT['glass'])
    rbox(m, '%s_bar' % tag, [x - 2.5, y0 + 10.0, 60.0, x + 2.5, y0 + length - 10.0, 63.0], MAT['chrome'])
    if card:
        s = 1.0 if card_face == 'e' else -1.0
        picture(m, '%s_card' % tag, card, (x + s * 0.4, y0 + length * 0.5, 96.0), (s, 0.0, 0.0), (10.0, 7.0))


def partition(m, name, x0, x1, door_x, y=PART_Y, mat=None, door=True):
    ops = [(door_x, door_x + 64.0, 0.0, 96.0)] if door else []
    B.wall(m, [x0 + 16.0, y, 0.0, x1 - 16.0, y + 12.0, UNIT_H], mat or SHOP_MAT[name]['wall'], axis='x', openings=ops, id='partition_%s' % name)
    if door:
        rbox(m, 'partition_%s_frame' % name, [door_x - 3.0, y - 1.0, 96.0, door_x + 67.0, y + 13.0, 102.0], SHOP_MAT[name]['join'])
    # the back room behind it: its own floor and wall skins
    rbox(m, 'backroom_%s_floor' % name, [x0 + 16.0, y + 12.0, 0.0, x1 - 16.0, YB - 16.0, 0.3], MAT['back_floor'])


def back_spawners(m, name, x0, x1, n, y=4538.0):
    """spawners of a back room face along its length (x): the emergence carries a zombie 62.5 forward and the room is only 92 deep
    (round 1 check: SPAWN_CARRY_BLOCKED for every spawner facing the partition)"""
    xs = [(x0 + 50.0, 0.0), (x1 - 50.0, 180.0), ((x0 + x1) / 2 - 20.0, 0.0)][:n]      # 34 from the side wall in each case (round 2 check: at 18 the spawner stood on no nav cell)
    for k, (sx, yaw) in enumerate(xs):
        B.spawner(m, (sx, y, 0.0), yaw, layer='gameplay', id='spawn_%s_%d' % (name, k + 1))


def shelving(m, tag, box, shelves, mat, facing):
    """a built-in shelving carcass: back, two ends, a top and `shelves` boards, empty"""
    x0, y0, z0, x1, y1, z1 = box
    t = 1.5
    if facing in ('s', 'n'):
        by = (y1 - t, y1) if facing == 's' else (y0, y0 + t)
        rbox(m, '%s_back' % tag, [x0, by[0], z0, x1, by[1], z1], mat)
        rbox(m, '%s_end_a' % tag, [x0, y0, z0, x0 + t, y1, z1], mat)
        rbox(m, '%s_end_b' % tag, [x1 - t, y0, z0, x1, y1, z1], mat)
    else:
        bxx = (x0, x0 + t) if facing == 'e' else (x1 - t, x1)
        rbox(m, '%s_back' % tag, [bxx[0], y0, z0, bxx[1], y1, z1], mat)
        rbox(m, '%s_end_a' % tag, [x0, y0, z0, x1, y0 + t, z1], mat)
        rbox(m, '%s_end_b' % tag, [x0, y1 - t, z0, x1, y1, z1], mat)
    rbox(m, '%s_plinth' % tag, [x0, y0, z0, x1, y1, z0 + 6.0], MAT['dark'])
    solid(m, tag, box)
    levels = [z0 + 6.0 + (z1 - z0 - 6.0) * (k + 1) / (shelves + 1) for k in range(shelves)] + [z1 - t]
    for k, z in enumerate(levels):
        rbox(m, '%s_board%d' % (tag, k), [x0, y0, z - t, x1, y1, z], mat)
    return [z0 + 6.0] + levels[:-1]


def solid(m, tag, box, ztop=64.0):
    """furniture is drawn render-only and blocked by one clip box up to ztop: no navigation cell on a counter or in a trough
    (round 1 check: NAV_FLOATING on the record bins, a nav island on the pigeonhole plinth)"""
    B.clip(m, [box[0], box[1], box[2], box[3], box[4], max(ztop, box[5])], id='%s_clip' % tag)


def counter(m, tag, box, top_mat, body_mat, kick=None):
    x0, y0, z0, x1, y1, z1 = box
    rbox(m, '%s_body' % tag, [x0, y0, z0, x1, y1, z1 - 2.0], body_mat)
    solid(m, tag, box)
    rbox(m, '%s_top' % tag, [x0 - 1.0, y0 - 1.0, z1 - 2.0, x1 + 1.0, y1 + 1.0, z1], top_mat)
    if kick:
        rbox(m, '%s_kick' % tag, [x0 + 0.5, y0 - 0.4, z0, x1 - 0.5, y1 + 0.4, z0 + 5.0], kick)


def shops(m):
    m.use('fronts')
    needle_drop(m)
    copy_stop(m)
    hole_nine(m)
    heel_key(m)


def needle_drop(m):
    """U1 Needle Drop: black aluminium, door left, a window full of sleeves right, shutter a quarter down; inside: sleeve wall, bins,
    the counter and the jukebox closing the long view; spawns from the back room"""
    nm = 'needle_drop'
    x0, x1 = UNITS[nm]
    cx = (x0 + x1) / 2
    a0, a1 = unit_room(m, nm)
    fascia(m, nm, [('fascia_needle_drop.png', cx, 300.0)])
    fr = SHOP_MAT[nm]['frame']
    gy = Y1 + 10.0
    door_x0, door_x1 = a0, a0 + 100.0
    rbox(m, 'nd_door_head', [door_x0, gy - 2.0, 138.0, door_x1, gy + 2.0, OPEN_Z], fr)
    frame_v(m, 'nd_door_jamb', door_x1, gy, 0.0, 138.0, fr, w=4.0)
    rbox(m, 'nd_threshold', [door_x0, gy - 6.0, 0.0, door_x1, gy + 6.0, 0.6], MAT['alu'])
    door_leaf(m, 'nd_leaf', door_x0 + 3.0, 94.0, gy + 2.0, fr, card='door_card_needle_drop.png', card_face='e')
    rbox(m, 'nd_riser', [door_x1 + 2.0, gy - 3.0, 0.0, a1, gy + 3.0, 20.0], MAT['dark'])
    glazing(m, 'nd_win', door_x1 + 2.0, a1, gy, 20.0, 138.0, fr, mull=[door_x1 + 2.0 + (a1 - door_x1 - 2.0) / 2])
    rbox(m, 'nd_transom', [a0, gy - 2.0, 138.0, a1, gy + 2.0, OPEN_Z], fr)
    rbox(m, 'nd_plinth', [door_x1 + 8.0, gy + 4.0, 0.0, a1 - 6.0, gy + 30.0, 22.0], MAT['alu_black'])
    solid(m, 'nd_plinth', [door_x1 + 8.0, gy + 4.0, 0.0, a1 - 6.0, gy + 30.0, 22.0])
    rbox(m, 'nd_plinth_lip', [door_x1 + 8.0, gy + 3.4, 18.0, a1 - 6.0, gy + 4.0, 22.0], SHOP_MAT[nm]['accent'])
    anchor('needle_drop.window_plinth', [door_x1 + 8.0, gy + 4.0, 22.0, a1 - 6.0, gy + 30.0, 110.0], 's', 'sleeves on stands, a Roll-In poster: the window display (goods)')
    anchor('needle_drop.window_rack_1', [door_x1 + 8.0, gy + 22.0, 22.0, a1 - 6.0, gy + 30.0, 96.0], 's', 'a rack of sleeves behind the plinth, faces out')
    # sleeve wall: a built-in carcass the length of the west wall
    zs = shelving(m, 'nd_sleeve_wall', [x0 + 16.0, Y1 + 110.0, 0.0, x0 + 34.0, PART_Y - 8.0, 120.0], 3, SHOP_MAT[nm]['join'], 'e')
    for k, z in enumerate(zs):
        anchor('needle_drop.sleeve_wall_%d' % (k + 1), [x0 + 18.0, Y1 + 110.0, z, x0 + 34.0, PART_Y - 8.0, z + 26.0], 'e', 'record sleeves face out, one row a board')
    rbox(m, 'nd_wall_band', [x0 + 16.0, Y1 + 16.0, 124.0, x0 + 16.6, PART_Y, 132.0], SHOP_MAT[nm]['accent'])
    # browser bins: two empty troughs on legs down the middle
    for k, bxc in enumerate((cx - 40.0, cx)):                   # one browser island of two troughs side by side, 54 clear north and south (round 3 bisect: plinth + island cut the east half off the nav)
        b = [bxc - 20.0, Y1 + 94.0, 0.0, bxc + 20.0, Y1 + 126.0, 30.0]
        rbox(m, 'nd_bin_%d' % k, [b[0], b[1], 0.0, b[3], b[4], 18.0], SHOP_MAT[nm]['join'])
        solid(m, 'nd_bin_%d' % k, b)
        for s, (ya, yb) in enumerate(((b[1], b[1] + 1.5), (b[4] - 1.5, b[4]))):
            rbox(m, 'nd_bin_%d_end%d' % (k, s), [b[0], ya, 18.0, b[3], yb, 34.0], SHOP_MAT[nm]['join'])
        rbox(m, 'nd_bin_%d_side_a' % k, [b[0], b[1], 18.0, b[0] + 1.5, b[4], 28.0], SHOP_MAT[nm]['join'])
        rbox(m, 'nd_bin_%d_side_b' % k, [b[3] - 1.5, b[1], 18.0, b[3], b[4], 28.0], SHOP_MAT[nm]['join'])
        rbox(m, 'nd_bin_%d_trim' % k, [b[0] - 0.3, b[1] - 0.3, 14.0, b[3] + 0.3, b[4] + 0.3, 18.0], SHOP_MAT[nm]['accent'])
        anchor('needle_drop.bin_%d' % (k + 1), [b[0] + 2.0, b[1] + 2.0, 18.0, b[3] - 2.0, b[4] - 2.0, 32.0], 'up', 'LPs standing in the trough, browsed from both sides')
    # the counter at the east side, with the cassette carousel position on it
    counter(m, 'nd_counter', [x1 - 46.0, Y1 + 80.0, 0.0, x1 - 20.0, Y1 + 170.0, 40.0], MAT['alu_black'], SHOP_MAT[nm]['join'], kick=SHOP_MAT[nm]['accent'])
    anchor('needle_drop.counter_top', [x1 - 46.0, Y1 + 80.0, 40.0, x1 - 20.0, Y1 + 170.0, 70.0], 'w', 'till, the cassette carousel, rental tapes, the empty tape case of the party tape')
    # the jukebox closing the long view, against the partition, glowing
    jy = PART_Y - 0.5
    B.prop(m, 'cp_town_jukebox', (cx + 80.0, jy, 0.0), yaw=270.0, layer='fronts', id='nd_jukebox',
           emissive={'color': [1.0, 0.55, 0.2], 'strength': 1.4})
    REPORT['fallbacks'].append('nd_jukebox: stock cp_town_jukebox, static and silent (canon jukebox not usable from a layer)')
    partition(m, nm, x0, x1, x0 + 40.0)
    back_spawners(m, nm, x0, x1, 2)
    # light: warm orange, the jukebox's glow at the back
    fix(m, 'pendant_warm', (cx - 40.0, Y1 + 110.0, UNIT_H), role=nm, intensity=1.15, radius=0.75)
    fix(m, 'pendant_warm', (cx + 50.0, Y1 + 110.0, UNIT_H), role=nm, intensity=1.15, radius=0.75)
    fix(m, 'spot_can', ((door_x1 + a1) / 2, gy + 24.0, UNIT_H), role=nm, color=(1.0, 0.5, 0.16), intensity=1.4, radius=0.7)
    lamp(m, 'light_nd_jukebox', (cx + 80.0, jy - 30.0, 40.0), nm, color=(1.0, 0.52, 0.18), radius=190.0, intensity=0.9)
    # the fascia's marquee: two bulb strips under the fascia
    for k, dx in enumerate((-75.0, 75.0)):
        fix(m, 'bulb_strip', (cx + dx, Y1 - 6.0, (HOUSING[0] + HOUSING[1]) / 2), 270.0, role=nm, kelvin=2000, intensity=0.75, radius=1.0)


def copy_stop(m):
    """U2+U3 Copy Stop, one double shop: white frames, two windows and central double doors, shutter fully up; inside the blueprint bay
    (the wheel), two copiers with a green-white bar, the service counter, pigeonholes of uncollected jobs, the photo booth in the east corner"""
    nm = 'copy_stop'
    x0, x1 = UNITS[nm]
    cx = (x0 + x1) / 2
    a0, a1 = unit_room(m, nm)
    fascia(m, nm, [('fascia_copy_stop_left.png', a0 + 77.0, 150.0), ('fascia_copy_stop.png', cx, 310.0), ('fascia_copy_stop_right.png', a1 - 77.0, 150.0)])
    fr = SHOP_MAT[nm]['frame']
    gy = Y1 + 6.0
    d0, d1 = cx - 66.0, cx + 66.0
    rbox(m, 'cs_riser_w', [a0, gy - 3.0, 0.0, d0, gy + 3.0, 14.0], SHOP_MAT[nm]['accent'])
    rbox(m, 'cs_riser_e', [d1, gy - 3.0, 0.0, a1, gy + 3.0, 14.0], SHOP_MAT[nm]['accent'])
    glazing(m, 'cs_win_w', a0, d0 - 2.0, gy, 14.0, 132.0, fr, mull=[a0 + (d0 - a0) / 3, a0 + 2 * (d0 - a0) / 3])
    glazing(m, 'cs_win_e', d1 + 2.0, a1, gy, 14.0, 132.0, fr, mull=[d1 + (a1 - d1) / 3, d1 + 2 * (a1 - d1) / 3])
    rbox(m, 'cs_transom', [a0, gy - 2.0, 132.0, a1, gy + 2.0, 138.0], fr)
    bx(m, 'cs_transom_glass', [a0 + 2.0, gy - 0.3, 138.0, a1 - 2.0, gy + 0.3, OPEN_Z - 1.0], MAT['glass'])
    frame_v(m, 'cs_door_j0', d0, gy, 0.0, 132.0, fr, w=4.0)
    frame_v(m, 'cs_door_j1', d1, gy, 0.0, 132.0, fr, w=4.0)
    rbox(m, 'cs_threshold', [d0, gy - 6.0, 0.0, d1, gy + 6.0, 0.6], MAT['alu'])
    door_leaf(m, 'cs_leaf_w', d0 + 3.0, 62.0, gy + 2.0, fr, card='door_card_copy_stop.png', card_face='e')
    door_leaf(m, 'cs_leaf_e', d1 - 3.0, 62.0, gy + 2.0, fr)
    # the blueprint bay at the west: a plan chest and the wheel position against the west wall
    bay = [x0 + 16.0, Y1 + 40.0, x0 + 150.0, PART_Y - 12.0]
    rbox(m, 'cs_bay_floor', [bay[0], bay[1], 0.0, bay[2], bay[3], 0.35], 'w/linoleum_floor_tiles_02_dark')
    pc = [bay[0], bay[1], 0.0, bay[0] + 40.0, 4392.0, 36.0]                       # A3b request 3: 64 clear of the wheel                 # the plan chest against the west wall
    counter(m, 'cs_planchest', pc, MAT['alu_white'], 'w/zmb_brushed_metal_01_blue', kick=MAT['dark'])
    anchor('copy_stop.blueprint_machine', [pc[0], pc[1], 36.0, pc[3], pc[4], 70.0], 'e', 'the blueprint (diazo) machine on the plan chest, rolls of drawings')
    wx = bay[0] + 60.0                                                             # the wheel against the partition, facing the shop
    bx(m, 'cs_wheel_plinth', [wx - 32.0, PART_Y - 34.0, 0.0, wx + 32.0, PART_Y, 4.0], MAT['alu_white'])
    try:
        B.wheel(m, (wx, PART_Y - 20.0, 4.0), 270.0, layer='gameplay', id='wheel_copy_stop')
    except Exception as e:                                         # noqa: BLE001  (the tool's message goes in the report)
        REPORT['refused'].append('wheel: %s' % e)
    # copiers: two machines on the west half, each with the bar of green-white light under its lid (static: the bar does not move)
    for k, ccx in enumerate((cx - 150.0, cx - 70.0)):
        cy = Y1 + 150.0
        rbox(m, 'cs_copier_%d_body' % k, [ccx - 22.0, cy - 14.0, 0.0, ccx + 22.0, cy + 14.0, 44.0], 'w/plastic_wall_frp_01_beige')      # 44 high (A3b request 5: it hid behind the riser)
        solid(m, 'cs_copier_%d' % k, [ccx - 23.0, cy - 15.0, 0.0, ccx + 32.0, cy + 15.0, 56.0])
        rbox(m, 'cs_copier_%d_kick' % k, [ccx - 21.0, cy - 14.4, 0.0, ccx + 21.0, cy + 14.4, 4.0], MAT['dark'])
        rbox(m, 'cs_copier_%d_deck' % k, [ccx - 23.0, cy - 15.0, 44.0, ccx + 23.0, cy + 15.0, 47.0], MAT['alu_white'])
        rbox(m, 'cs_copier_%d_bar' % k, [ccx - 16.0, cy - 15.3, 47.0, ccx + 16.0, cy - 13.0, 48.4], 'w/emissive_light_panel_green')
        rbox(m, 'cs_copier_%d_lid' % k, [ccx - 18.0, cy - 12.0, 48.6, ccx + 18.0, cy + 13.0, 50.2], 'w/metal_painted_wall_panel_04')
        rbox(m, 'cs_copier_%d_feeder' % k, [ccx - 14.0, cy - 4.0, 50.2, ccx + 14.0, cy + 12.0, 56.0], 'w/plastic_wall_frp_01_beige')      # the document feeder
        rbox(m, 'cs_copier_%d_tray' % k, [ccx + 22.0, cy - 9.0, 26.0, ccx + 32.0, cy + 9.0, 27.5], MAT['alu_white'])
        lamp(m, 'light_cs_copier_%d' % k, (ccx, cy - 24.0, 50.0), nm, color=(0.72, 1.0, 0.8), radius=180.0, intensity=0.35)      # an accent: the blue-white tubes lead (pass 1 score: green led)
        anchor('copy_stop.copier_%d_top' % (k + 1), [ccx - 18.0, cy - 12.0, 50.2, ccx + 18.0, cy + 13.0, 70.0], 's', 'an original left on the glass, paper on the tray')
    REPORT['fallbacks'].append('cs_copier_*: authored static copier bodies; the green-white bar is a fixed emissive strip and a baked light (no moving scan)')
    # the service counter and the pigeonholes of uncollected jobs on the back wall
    counter(m, 'cs_counter', [cx + 40.0, Y1 + 76.0, 0.0, cx + 220.0, Y1 + 102.0, 40.0], MAT['alu_white'], 'w/zmb_brushed_metal_01_blue', kick=MAT['dark'])
    anchor('copy_stop.counter_top', [cx + 40.0, Y1 + 76.0, 40.0, cx + 220.0, Y1 + 102.0, 64.0], 's', 'the tray of uncollected jobs, the forty-copy job (Strand memo), programmes of the gala')
    pg = [x1 - 38.0, Y1 + 100.0, 0.0, x1 - 16.0, PART_Y - 8.0, 96.0]          # on the east wall north of the booth (round 3: on the partition it left a 56 corridor with no nav)
    zs = shelving(m, 'cs_pigeonholes', pg, 3, MAT['alu_white'], 'w')
    for k, z in enumerate(zs):
        anchor('copy_stop.pigeonholes_%d' % (k + 1), [pg[0], pg[1] + 2.0, z, pg[3] - 2.0, pg[4] - 2.0, z + 20.0], 'w', 'job envelopes, one per hole')
    # the photo booth in the east corner (authored 1970s booth: blue body, chrome trim, a curtain opening on its west side, a strip slot)
    photo_booth(m, a1 - 2.0, gy + 22.0)
    partition(m, nm, x0, x1, cx - 32.0)
    back_spawners(m, nm, x0, x1, 3)
    # light: cold blue-white tubes, the copier bars (above); one tube dead
    fix(m, 'ceiling_tube_blue', (cx - 110.0, Y1 + 120.0, UNIT_H), 0.0, role=nm, intensity=1.0, radius=0.8)
    fix(m, 'ceiling_tube_blue', (cx + 110.0, Y1 + 90.0, UNIT_H), 0.0, role=nm, intensity=1.0, radius=0.8)
    B.prop(m, 'cp_disco_fluorescent_light_off', (bay[0] + 70.0, Y1 + 100.0, UNIT_H), yaw=90.0, layer='fronts', id='cs_tube_dead')
    for k, dx in enumerate((-110.0, 110.0)):
        fix(m, 'wall_led', (cx + dx, Y1 - 6.0, (HOUSING[0] + HOUSING[1]) / 2), 270.0, role=nm, kelvin=6800, intensity=1.1, radius=0.8)
    # L1, goods worker's request (28 Nov): the ream wall in the west window (x -2604..-2500, y 4312..4334, boards z 16..104) read dark grey from
    # 800 (the north lane's tubes are dead). A cold spot from the hall's grid in front of the shop, aimed at the wall's face: the reams are the lit thing
    # (from y 4180 the beam crossed the fascia box: base frame of 28 Nov; from y 4000 it passes under the fascia, z 89 at its face, and through the
    # opening, z 71 at y 4300. The window glass shadows a BAKED light: only the engine light reaches the reams)
    aim(m, fix(m, 'spot_can', (-2552.0, 4000.0, GRID_Z), role=nm, key=True, color=(0.88, 0.93, 1.0), intensity=1.6, radius=1.7), (-2552.0, 4323.0, 58.0))   # the pool's blue-white: rule 12 keeps the hall at four hue classes (8500 K read 'cool', a fifth)


def photo_booth(m, xe, y0):
    """a 1970s booth body: 44 wide (x), 64 deep (y), 84 high, standing in the east corner; curtain opening on its west side"""
    x0, x1, y1 = xe - 44.0, xe, y0 + 64.0
    body, trim = 'w/zmb_brushed_metal_01_blue', MAT['chrome']
    bx(m, 'pb_back', [x0, y1 - 3.0, 0.0, x1, y1, 84.0], body)
    bx(m, 'pb_front', [x0, y0, 0.0, x1, y0 + 3.0, 84.0], body)
    bx(m, 'pb_east', [x1 - 3.0, y0, 0.0, x1, y1, 84.0], body)
    bx(m, 'pb_west_low', [x0, y0, 0.0, x0 + 3.0, y1, 8.0], body)
    bx(m, 'pb_west_jamb', [x0, y0, 8.0, x0 + 3.0, y0 + 22.0, 74.0], body)
    bx(m, 'pb_west_head', [x0, y0, 74.0, x0 + 3.0, y1, 84.0], body)
    rbox(m, 'pb_roof', [x0 - 1.0, y0 - 1.0, 84.0, x1 + 1.0, y1 + 1.0, 87.0], trim)
    rbox(m, 'pb_lightband', [x0 + 3.0, y0 - 0.6, 76.0, x1 - 3.0, y0, 83.0], MAT['panel_on'])
    rbox(m, 'pb_slot', [x0 + 14.0, y0 - 0.8, 36.0, x0 + 26.0, y0, 38.0], MAT['dark'])
    rbox(m, 'pb_sample_frame', [x0 + 8.0, y0 - 0.6, 44.0, x0 + 34.0, y0, 70.0], trim)
    solid(m, 'pb', [x0, y0, 0.0, x1, y1, 84.0])
    B.prop(m, 'cp_disco_curtain_left', (x0 - 1.5, y0 + 22.0, 74.0), yaw=0.0, scale=0.6, layer='fronts', id='pb_curtain')
    anchor('copy_stop.booth_sample_strips', [x0 + 8.0, y0 - 1.0, 44.0, x0 + 34.0, y0, 70.0], 's', 'sample strips in the frame on the booth front (Double Takes, the strip secret)')
    REPORT['fallbacks'].append('photo booth: authored static body; not usable (no interaction kind)')


def hole_nine(m):
    """U4 Hole Number Nine: a serving counter open to the hall, the door at the side, shutter up; inside: an inside counter with fixed stool
    bases, the display counter behind the serving counter; the SMG on the west side wall; the kitchen behind"""
    nm = 'hole_nine'
    x0, x1 = UNITS[nm]
    cx = (x0 + x1) / 2
    a0, a1 = unit_room(m, nm)
    fascia(m, nm, [('fascia_hole_nine.png', cx, 300.0)])
    fr = SHOP_MAT[nm]['frame']
    sm = SHOP_MAT[nm]
    door_x0 = a1 - 100.0
    counter(m, 'h9_serving', [a0, Y1 + 2.0, 0.0, door_x0 - 2.0, Y1 + 30.0, 42.0], 'w/metal_chrome_trim_03', sm['join'], kick=MAT['dark'])
    rbox(m, 'h9_serving_band', [a0 + 1.0, Y1 + 1.4, 22.0, door_x0 - 3.0, Y1 + 2.0, 28.0], sm['wall'])
    anchor('hole_nine.serving_counter', [a0, Y1 + 2.0, 42.0, door_x0 - 2.0, Y1 + 30.0, 70.0], 's', 'the gala order bagged and waiting (Strand), napkins, the bell')
    rbox(m, 'h9_hatch_head', [a0, Y1 + 8.0, 138.0, door_x0, Y1 + 12.0, OPEN_Z], fr)
    frame_v(m, 'h9_door_jamb', door_x0, Y1 + 10.0, 0.0, 138.0, fr, w=4.0)
    rbox(m, 'h9_door_head', [door_x0, Y1 + 8.0, 132.0, a1, Y1 + 12.0, OPEN_Z], fr)
    bx(m, 'h9_door_transom', [door_x0 + 2.0, Y1 + 9.7, 132.0, a1 - 2.0, Y1 + 10.3, 138.0], MAT['glass'])
    door_leaf(m, 'h9_leaf', a1 - 3.0, 94.0, Y1 + 12.0, fr, card='door_card_hole_nine.png', card_face='w')
    rbox(m, 'h9_threshold', [door_x0, Y1 + 4.0, 0.0, a1, Y1 + 16.0, 0.6], MAT['alu'])
    # the display counter behind the serving counter (glass front, built in), and the back shelving for the racks
    # round 1 check: a display counter 40 behind the serving counter left the west half without navigation (WALKABLE_OFF_NAV);
    # now the case stands free in the middle with 60 or more on every side
    dsp = [cx - 70.0, Y1 + 100.0, 0.0, cx + 30.0, Y1 + 124.0, 38.0]
    counter(m, 'h9_display', dsp, MAT['glass'], sm['join'])
    anchor('hole_nine.display_case', [dsp[0] + 2.0, dsp[1] + 2.0, 4.0, dsp[3] - 2.0, dsp[4] - 2.0, 60.0], 's', 'the racks of doughnuts in the case, the urn on its end')
    # the inside counter with fixed stool bases (ledge on the partition side, west of the kitchen door)
    counter(m, 'h9_ledge', [x0 + 40.0, PART_Y - 22.0, 0.0, x0 + 130.0, PART_Y - 2.0, 40.0], 'w/metal_chrome_trim_03', sm['join'])
    for k, sx in enumerate((x0 + 70.0, x0 + 110.0)):
        mesh(m, 'h9_stool_post_%d' % k, MAT['chrome'], G.merge(G.cylinder((sx, PART_Y - 40.0, 0.0), (sx, PART_Y - 40.0, 2.0), 8.0, 16),
                                                              G.cylinder((sx, PART_Y - 40.0, 2.0), (sx, PART_Y - 40.0, 22.0), 1.6, 12)))
        mesh(m, 'h9_stool_seat_%d' % k, 'w/plastic_wall_plain_red_01', G.cylinder((sx, PART_Y - 40.0, 22.0), (sx, PART_Y - 40.0, 26.0), 7.5, 16))
        B.clip(m, [sx - 7.0, PART_Y - 47.0, 0.0, sx + 7.0, PART_Y - 33.0, 26.0], layer='fronts', id='h9_stool_clip_%d' % k)
    anchor('hole_nine.inside_counter', [x0 + 40.0, PART_Y - 22.0, 40.0, x0 + 130.0, PART_Y - 2.0, 60.0], 's', 'cups, the sugar, a plate left half eaten')
    anchor('hole_nine.tv_shelf', [x1 - 70.0, PART_Y - 24.0, 120.0, x1 - 18.0, PART_Y - 2.0, 160.0], 's', 'the television on Channel 9 (bracket shelf high on the back wall)')
    rbox(m, 'h9_tv_shelf', [x1 - 70.0, PART_Y - 24.0, 116.0, x1 - 18.0, PART_Y, 119.0], sm['join'])
    rbox(m, 'h9_dado', [x0 + 16.0, Y1 + 16.0, 0.0, x0 + 16.6, PART_Y, 48.0], sm['accent'])
    rbox(m, 'h9_dado_e', [x1 - 16.6, Y1 + 40.0, 0.0, x1 - 16.0, PART_Y, 48.0], sm['accent'])
    # the SMG wall buy on the west side wall inside the shop
    B.wallbuy(m, (x0 + 16.0 + 6.0, Y1 + 140.0, 0.0), 'smg', 1000, 0.0, layer='gameplay', id='buy_smg_hole_nine')
    partition(m, nm, x0, x1, cx - 10.0)
    back_spawners(m, nm, x0, x1, 2)
    # light: pink neon and pink shades, one warm downlight over the till; the kitchen stays dark
    fix(m, 'neon_open', (cx - 40.0, PART_Y - 0.2, 118.0), 270.0, role=nm, intensity=1.3, radius=1.1)
    fix(m, 'pendant', (cx - 70.0, Y1 + 50.0, UNIT_H), role=nm, color=(1.0, 0.48, 0.72), intensity=0.9, radius=0.65)
    fix(m, 'pendant', (cx + 10.0, Y1 + 50.0, UNIT_H), role=nm, color=(1.0, 0.48, 0.72), intensity=0.9, radius=0.65)
    ids = fix(m, 'downlight', (cx - 20.0, Y1 + 60.0, UNIT_H), role=nm, kelvin=2700, intensity=1.2, radius=0.85)   # A3b request 4: a spot on the rack front, not a new light
    for lid in ids[1:]:
        o = m.get(lid)
        d = (0.0, (Y1 + 100.0) - o['origin'][1], 22.0 - o['origin'][2])
        ln = math.sqrt(sum(c * c for c in d))
        m.update(lid, dir=[round(c / ln, 4) for c in d])
    for k, px in enumerate((x0 + 8.0, x1 - 8.0)):
        fix(m, 'outdoor_wall', (px, Y1 - 8.0, 120.0), 270.0, role=nm, intensity=0.8, radius=0.8)


def heel_key(m):
    """U5 Heel & Key: a stall, the counter across the front, the shutter half down (not entered); the pegboard wall behind the work
    space carries the marksman rifle; the back room opens through a side door into the service passage east of the row"""
    nm = 'heel_key'
    x0, x1 = UNITS[nm]
    cx = (x0 + x1) / 2
    a0, a1 = unit_room(m, nm, extra_openings=[('e', 4500.0, 4564.0, 0.0, 96.0)])
    fascia(m, nm, [('fascia_heel_key.png', cx, 300.0)])
    sm = SHOP_MAT[nm]
    counter(m, 'hk_counter', [a0, Y1 + 2.0, 0.0, a1, Y1 + 30.0, 42.0], sm['join'], sm['accent'], kick=MAT['dark'])
    picture(m, 'hk_card', 'door_card_heel_key.png', (cx + 90.0, Y1 + 1.0, 30.0), (0.0, -1.0, 0.0), (10.0, 7.0))
    zb = OPEN_Z - SHUTTER_STOP[nm] * OPEN_Z
    B.clip(m, [a0, Y1, 42.0, a1, Y1 + 30.0, zb], layer='fronts', id='hk_stall_clip')        # the stall is not entered: nobody climbs the counter under the shutter
    anchor('heel_key.counter_top', [a0, Y1 + 2.0, 42.0, a1, Y1 + 30.0, 72.0], 's', 'the key carousel, tagged shoes waiting, the bell')
    peg_y = Y1 + 110.0
    B.wall(m, [x0 + 16.0, peg_y, 0.0, x1 - 16.0, peg_y + 12.0, UNIT_H], sm['wall'], axis='x', id='partition_heel_key')
    rbox(m, 'hk_pegboard', [x0 + 20.0, peg_y - 1.0, 40.0, x1 - 20.0, peg_y, 150.0], MAT['pegboard'])
    rbox(m, 'hk_pegboard_frame', [x0 + 18.0, peg_y - 1.6, 150.0, x1 - 18.0, peg_y, 154.0], sm['join'])
    anchor('heel_key.pegboard', [x0 + 20.0, peg_y - 8.0, 40.0, x1 - 20.0, peg_y - 1.0, 150.0], 's', 'tagged shoes never collected, key blanks; one hook tagged "0"')
    counter(m, 'hk_bench', [x0 + 20.0, Y1 + 60.0, 0.0, cx - 10.0, peg_y - 2.0, 36.0], sm['join'], sm['accent'])
    anchor('heel_key.bench', [x0 + 22.0, Y1 + 60.0, 36.0, cx - 12.0, peg_y - 2.0, 64.0], 's', 'the key machine, the lasts, the mould of the Dead-Man\'s Handle')
    shelving(m, 'hk_lasts', [x1 - 70.0, Y1 + 50.0, 0.0, x1 - 20.0, peg_y - 2.0, 96.0], 3, sm['join'], 'w')
    m.remove('hk_lasts_end_a')                                     # A3a request 3: its south end hid the lasts from the hall
    anchor('heel_key.lasts_shelf', [x1 - 70.0, Y1 + 50.0, 6.0, x1 - 22.0, peg_y - 2.0, 96.0], 'w', 'shoe lasts, polish tins, boxes of heels')
    B.wallbuy(m, (cx + 60.0, peg_y - 6.0, 0.0), 'marksman', 1500, 270.0, layer='gameplay', id='buy_marksman_heel_key')
    rbox(m, 'backroom_heel_key_floor', [x0 + 16.0, peg_y + 12.0, 0.0, x1 - 16.0, YB - 16.0, 0.3], MAT['back_floor'])
    B.spawner(m, (x0 + 50.0, 4538.0, 0.0), 0.0, layer='gameplay', id='spawn_heel_key_1')
    # light: one tungsten work lamp on the bench
    fix(m, 'desk_lamp', (cx - 50.0, Y1 + 90.0, 36.0), 0.0, role=nm, kelvin=2400, intensity=1.3, radius=1.0)
    fix(m, 'downlight', (cx, Y1 + 65.0, UNIT_H), role=nm, kelvin=2600, intensity=1.0, radius=0.9)          # A3a request 2: the stall's goods read from the hall
    for k, px in enumerate((x0 + 8.0, x1 - 8.0)):             # two caged bulkheads on the piers: the stall's front in tungsten (pass 1: its fascia was black)
        fix(m, 'bulkhead', (px, Y1 - 8.0, 140.0), 270.0, role=nm, kelvin=2500, intensity=0.9, radius=0.9)
    # L1, goods worker's request (28 Nov): the stall read "repair counter"; the tagged shoes on the pegboard (y 4410, z 40..150) must be the lit
    # thing: a tungsten spot under the stall's ceiling just behind the counter, aimed at the pegboard's middle, seen under the shutter (z 42..120)
    aim(m, fix(m, 'spot_can', (cx + 30.0, Y1 + 34.0, UNIT_H), role=nm, key=True, kelvin=2700, intensity=1.3, radius=0.8), (cx + 10.0, peg_y - 1.0, 92.0))
    # the service passage east of the row (staff door to the hall), the Heel & Key back door opens into it
    B.room(m, [-1320.0, Y1, 0.0, X1, YB, UNIT_H], MAT['back'], MAT['back_floor'], MAT['slab'],
           openings=[('s', -1300.0, -1236.0, 0.0, 96.0), ('w', 4500.0, 4564.0, 0.0, 96.0)], id='room_service')
    bx(m, 'service_pier', [-1320.0, Y1 - 8.0, 0.0, -1300.0, Y1 + 18.0, BULK_Z], MAT['tile'])
    bx(m, 'service_head', [-1300.0, Y1 - 4.0, 96.0, XE, Y1 + 16.0, BULK_Z], MAT['tile'])
    rbox(m, 'service_door_frame', [-1303.0, Y1 - 5.0, 96.0, -1233.0, Y1 - 4.0, 102.0], MAT['steel_frame'])
    B.prop(m, 'door_metal_service_01', (-1294.0, Y1 + 42.0, 0.0), yaw=0.0, layer='fronts', id='service_door_leaf')


# ================================================================================================ south wall, ends, hall objects
def south_wall(m):
    m.use('south')
    y = YS
    # four pay phones in a row
    for k in range(4):
        B.prop(m, 'cp_disco_street_telephone_booth', (-1790.0 + 34.0 * k, y + 9.6, 0.0), yaw=180.0, layer='south', id='payphone_%d' % k,
               clip=[-14.0, -16.0, 0.0, 14.0, 10.0, 84.0])
    fix(m, 'wall_lantern', (-1739.0, y + 0.5, 128.0), 90.0, role='hall', intensity=0.8, radius=1.0)
    # four advertising light boxes in modelled frames (emissive pictures)
    for k, (x, nm) in enumerate(((-2360.0, 'lightbox_orbit.png'), (-2270.0, 'lightbox_lodestar.png'), (-2020.0, 'lightbox_channel9.png'), (-1930.0, 'lightbox_zero_line.png'))):
        bx(m, 'lightbox_%d' % k, [x - 36.0, y, 60.0, x + 36.0, y + 8.0, 164.0], MAT['alu'])
        rbox(m, 'lightbox_%d_lip' % k, [x - 36.0, y + 8.0, 60.0, x + 36.0, y + 9.0, 64.0], MAT['alu_black'])
        picture(m, 'lightbox_%d_face' % k, nm, (x, y + 8.0, 112.0), (0.0, 1.0, 0.0), (64.0, 96.0), emissive=1.6)
    # the directory board, the landmark of the entrance, lit by a sign lamp bar above it
    dx = -1560.0          # pass 1: near the entrance, in the entrance view, seen through D4 from the ticket hall
    bx(m, 'directory_frame', [dx - 66.0, y, 68.0, dx + 66.0, y + 6.0, 236.0], 'w/wood_antique_panel_trim_01')
    rbox(m, 'directory_cap', [dx - 70.0, y, 236.0, dx + 70.0, y + 10.0, 240.0], MAT['alu'])
    picture(m, 'directory_face', 'directory_board.png', (dx, y + 6.0, 152.0), (0.0, 1.0, 0.0), (120.0, 160.0))
    ids = fix(m, 'wall_led', (dx, y + 0.5, 239.0), 90.0, role='hall', kelvin=4800, intensity=1.3, radius=0.7)
    for lid in ids[1:]:
        o = m.get(lid)
        org = [dx, y + 26.0, 236.0]
        d = (0.0, -(org[1] - y - 6.0), 152.0 - org[2])
        n = math.sqrt(sum(c * c for c in d))
        m.update(lid, origin=org, dir=[round(c / n, 4) for c in d])
    # a notice frame with four notices
    nx = -2880.0
    bx(m, 'notice_frame', [nx - 44.0, y, 70.0, nx + 44.0, y + 3.0, 126.0], MAT['cork'])
    rbox(m, 'notice_glass', [nx - 42.0, y + 3.0, 72.0, nx + 42.0, y + 3.4, 124.0], MAT['glass'])
    for k in range(4):
        picture(m, 'notice_%d' % (k + 1), 'notice_%d.png' % (k + 1), (nx - 30.0 + 20.0 * k, y + 3.0, 98.0 + (k % 2) * 4.0), (0.0, 1.0, 0.0), (16.0, 22.0),
                rot=(-2.0, 3.0, -1.0, 2.0)[k])
    # the poster of the film, once, in a poster frame
    px = -2140.0
    bx(m, 'poster_frame', [px - 36.0, y, 60.0, px + 36.0, y + 2.5, 164.0], MAT['alu_black'])
    picture(m, 'poster_station_zero', 'poster_station_zero.png', (px, y + 2.5, 112.0), (0.0, 1.0, 0.0), (64.0, 96.0))
    # benches and one bin
    for k, x in enumerate((-2730.0, -2470.0)):           # the second bench moved east of the lockers (round of 28 Nov)
        B.prop(m, 'street_bench_long_iw6', (x, y + 20.0, 0.0), yaw=180.0, layer='south', id='bench_%d' % k, clip=[-49.0, -19.0, 0.0, 49.0, 19.0, 20.0])
    B.prop(m, 'cp_disco_street_trashcan_01', (-2210.0, y + 16.0, 0.0), yaw=0.0, layer='south', id='bin_0', clip=[-12.0, -12.0, 0.0, 12.0, 12.0, 30.0])
    fix(m, 'emergency_wall', (-1460.0, y + 0.5, 200.0), 90.0, role='hall', intensity=0.9, radius=1.4)
    anchor('hall.south_wall_litter', [XW, YS, 0.0, XE, YS + 80.0, 4.0], 'n', 'commuter litter at the benches and the phones (studio props.scatter commuter)')


def west_end(m):
    """the Shelter 7 blast door, closed: a steel frame in the west wall, the leaf, the hand wheel (zone 5 comes later)"""
    m.use('south')
    y0, y1, zt = 3852.0, 3948.0, 112.0
    bx(m, 'blast_leaf', [X0, y0, 0.0, XW - 6.0, y1, zt], MAT['steel'])
    for nm, b in (('jamb_s', [XW - 8.0, y0 - 16.0, 0.0, XW + 6.0, y0, zt + 16.0]), ('jamb_n', [XW - 8.0, y1, 0.0, XW + 6.0, y1 + 16.0, zt + 16.0]),
                  ('head', [XW - 8.0, y0, zt, XW + 6.0, y1, zt + 16.0]), ('sill', [XW - 8.0, y0, 0.0, XW + 4.0, y1, 2.0])):
        bx(m, 'blast_%s' % nm, b, MAT['steel_frame'])
    for k, z in enumerate((18.0, 56.0, 94.0)):
        rbox(m, 'blast_rib_%d' % k, [XW - 6.0, y0 + 6.0, z, XW - 3.0, y1 - 6.0, z + 4.0], MAT['steel_frame'])
    for k, z in enumerate((30.0, 82.0)):
        rbox(m, 'blast_dog_%d' % k, [XW - 6.0, y1 - 4.0, z, XW + 2.0, y1 + 10.0, z + 8.0], MAT['steel_frame'])
    c = (XW - 1.0, (y0 + y1) / 2, 60.0)
    wheel = G.merge(G.torus(c, (1, 0, 0), 15.0, 1.4, 24, 6), G.cylinder((XW - 6.0, c[1], c[2]), (XW + 1.0, c[1], c[2]), 3.0, 12))
    for a in (0, 60, 120):
        r = math.radians(a)
        dy, dz = 15.0 * math.cos(r), 15.0 * math.sin(r)
        wheel = G.merge(wheel, G.cylinder((c[0], c[1] - dy, c[2] - dz), (c[0], c[1] + dy, c[2] + dz), 0.9, 8, caps=False))
    mesh(m, 'blast_wheel', MAT['wheel'], wheel)
    rbox(m, 'blast_hazard', [XW - 7.0, y0 - 16.0, zt + 16.0, XW + 6.5, y1 + 16.0, zt + 22.0], 'w/metal_painted_scratched_yellow')
    fix(m, 'emergency_wall', (XW + 0.5, (y0 + y1) / 2, zt + 40.0), 0.0, role='hall', intensity=0.9, radius=1.4)
    anchor('shelter7.door', [X0, y0, 0.0, XW + 6.0, y1, zt], 'e', 'zone 5 (Shelter 7) opens here later: the leaf is world geometry today')
    # D4: the exit sign over the doorway, the concertina gate folded back into the jambs
    fix(m, 'exit_sign', (XE - 0.5, 3900.0, 234.0), 180.0, role='hall', intensity=1.0, radius=1.6)
    B.prop(m, 'cp_disco_storefront_security_gate', (XE - 16.0, 3790.0, 0.0), yaw=0.0, layer='south', id='d4_gate')


def polisher(m):
    """the floor polisher in its polished circle (authored: no stock 1978 polisher exists; cp_disco_floor_buffer is the bladed trap),
    its cable run to a wall socket. Static."""
    m.use('south')
    cx, cy = -1590.0, 3850.0          # pass 1: the foreground of the entrance view, as in the target
    picture_decal(m, 'polish_circle', 'floor_polish_circle.png', (cx - 30.0, cy, 0.0), (220.0, 220.0))
    px, py, yaw = cx, cy, 160.0
    loc = G.merge(G.cylinder((0, 0, 0.0), (0, 0, 3.0), 10.0, 20), G.cylinder((0, 0, 3.0), (0, 0, 8.0), 9.4, 20))
    mesh(m, 'polisher_skirt', MAT['rubber'], (G.yaw_points(loc[0], (px, py, 0), yaw), loc[1]))
    body = G.merge(G.cylinder((0, 0, 8.0), (0, 0, 21.0), 6.5, 18), G.cylinder((0, 0, 21.0), (0, 0, 23.0), 5.0, 18))
    mesh(m, 'polisher_body', MAT['cream_paint'], (G.yaw_points(body[0], (px, py, 0), yaw), body[1]))
    band = G.cylinder((0, 0, 15.0), (0, 0, 17.0), 6.7, 18, caps=False)
    mesh(m, 'polisher_band', MAT['wheel'], (G.yaw_points(band[0], (px, py, 0), yaw), band[1]))
    steel = G.merge(G.cylinder((-4.0, 0, 18.0), (-30.0, 0, 46.0), 0.8, 8), G.cylinder((-30.0, -9.0, 46.0), (-30.0, 9.0, 46.0), 0.9, 8),
                    G.cylinder((-7.0, -6.5, 3.5), (-7.0, 6.5, 3.5), 0.6, 8, caps=False))
    mesh(m, 'polisher_handle', MAT['chrome'], (G.yaw_points(steel[0], (px, py, 0), yaw), steel[1]))
    grips = G.merge(G.cylinder((-30.0, -9.0, 46.0), (-30.0, -5.0, 46.0), 1.2, 8), G.cylinder((-30.0, 5.0, 46.0), (-30.0, 9.0, 46.0), 1.2, 8),
                    G.cylinder((-7.0, -7.5, 3.5), (-7.0, -5.0, 3.5), 3.2, 12), G.cylinder((-7.0, 5.0, 3.5), (-7.0, 7.5, 3.5), 3.2, 12))
    mesh(m, 'polisher_grips', MAT['rubber'], (G.yaw_points(grips[0], (px, py, 0), yaw), grips[1]))
    B.clip(m, [px - 11.0, py - 11.0, 0.0, px + 11.0, py + 11.0, 24.0], layer='south', id='polisher_clip')
    # the cable: from the handle down to the floor, a slack loop, then to the socket on the south wall between two columns
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    hx, hy = px + (-12.0) * c, py + (-12.0) * s
    sx = -1650.0
    pts = [(hx, hy), (hx - 10.0, hy - 40.0), (-1615.0, 3700.0), (-1640.0, 3600.0), (sx, YS + 2.0)]
    mesh(m, 'polisher_cable', MAT['rubber'], G.ribbon(pts, 0.9))
    mesh(m, 'polisher_cable_rise', MAT['rubber'], G.cylinder((sx, YS + 1.5, 0.3), (sx, YS + 1.5, 16.0), 0.45, 6, caps=False))
    B.prop(m, 'fac_outlet', (sx, YS, 18.0), yaw=180.0, layer='south', id='polisher_socket')
    REPORT['fallbacks'].append('floor polisher: authored static machine (no stock 1978 polisher; cp_disco_floor_buffer carries blades), it does not turn')


def picture_decal(m, id, name, at, size):
    path, stand = S.slot(name)
    (REPORT['standins'] if stand else REPORT['art']).append(name)
    B.decal(m, image=path, at=at, normal=(0.0, 0.0, 1.0), size=size, id=id)


def hangings(m):
    """the New Year banner and two bunting strips across the hall, hung from the grid on wires"""
    m.use('south')
    bxp = -2200.0
    picture2(m, 'banner_new_year', 'banner_new_year.png', (bxp, 3900.0, 206.0), 'x', (320.0, 48.0))
    for k, yy in enumerate((3745.0, 4055.0)):
        rbox(m, 'banner_wire_%d' % k, [bxp - 0.2, yy - 0.2, 230.0, bxp + 0.2, yy + 0.2, GRID_Z], MAT['tbar'])
    for k, (xx, yc) in enumerate(((-2620.0, 3960.0), (-1650.0, 3880.0))):
        picture2(m, 'bunting_%d' % k, 'bunting_strip.png', (xx, yc, 222.0), 'x', (256.0, 24.0))
        for j, yy in enumerate((yc - 128.0, yc + 128.0)):
            rbox(m, 'bunting_%d_wire_%d' % (k, j), [xx - 0.2, yy - 0.2, 234.0, xx + 0.2, yy + 0.2, GRID_Z], MAT['tbar'])


# ================================================================================================ gameplay and cameras
def gameplay(m):
    m.use('gameplay')
    B.zone(m, 'arcade', [X0, Y0, -16.0, X1, YB, H + 14.0])
    B.door(m, 'd_hall_arcade', [X1 - 8.0, DOOR_Y0, 0.0, X1 + 8.0, DOOR_Y1, DOOR_Z], 1000, zones=['arcade', 'ticket_hall'], id='door_D4')
    for k, (x, y) in enumerate(((-2716.0, 3640.0), (-1564.0, 3640.0))):          # two floor drains in the south lane
        B.prop(m, 'grate_industrial_64_64_02', (x + 16.0, y - 16.0, 0.3), yaw=0.0, scale=0.5, layer='south', id='drain_%d' % k)
        B.spawner(m, (x, y, 0.0), 90.0, layer='gameplay', id='spawn_drain_%d' % (k + 1))


def cameras(m):
    m.use('cameras')
    # pass 2: at y 3700 the column at x -1420 filled the middle of the entrance view
    cams = [('arc_east_long', (-1296.0, 3880.0, 60.0), 172.0, 0.0), ('arc_west_long', (-2930.0, 4060.0, 60.0), 2.0, 0.0),
            ('arc_south_wall', (-2100.0, 4160.0, 64.0), 270.0, 0.0), ('arc_directory', (-1100.0, 3930.0, 64.0), 216.0, 0.0)]
    for nm, (x0, x1) in UNITS.items():
        cx = (x0 + x1) / 2
        cams.append(('arc_%s_front' % nm, (cx, 3900.0, 60.0), 90.0, -8.0))
        dx = -320.0 if cx - 320.0 > XW + 40.0 else 320.0          # pass 1: the Needle Drop oblique stood outside the hall (x -3120)
        cams.append(('arc_%s_oblique' % nm, (cx + dx, 3960.0, 60.0), round(math.degrees(math.atan2(Y1 - 3960.0, -dx)), 1), -6.0))
        if nm != 'heel_key':
            if nm == 'hole_nine':                                       # A3b request 1: 17 behind the glass rack before
                cams.append(('arc_hole_nine_inside', (-1730.0, 4440.0, 66.0), 200.0, 0.0))
            else:
                cams.append(('arc_%s_inside' % nm, (cx + {'copy_stop': 40.0, 'needle_drop': -60.0}.get(nm, 0.0), 4440.0, 60.0), 270.0, 0.0))
    for nm, eye, yaw, pitch in cams:
        B.camera(m, nm, eye, yaw, pitch=pitch, id=nm)
    REPORT['cameras'] = [c[0] for c in cams]


# ================================================================================================ the document
def recipe():
    """the build settings of allbaked2 (same kit dumps, darkness arguments with the -5.5 dark exposure), its kit list kept"""
    src = json.load(open(RECIPE_FROM, encoding='utf-8'))
    st = copy.deepcopy(src['settings'])
    st['map'] = 'cp_iwz'
    import light_rules                        # L1 (W2, 28 Nov): the proposed lit vision
    light_rules.apply_lit(st)
    return st


def build(name='sz_arcade_shell'):
    REPORT.update({'standins': [], 'art': [], 'fallbacks': [], 'refused': []})
    ANCHORS.clear()
    LIGHTS.clear()
    m = Map(name, 'Station Zero: the Underpass Arcade (shell, A2)', base={'kind': 'emit', 'path': BASE_EMIT}, settings=recipe())
    for layer in ('arcade_door', 'shell', 'ceiling', 'fronts', 'south', 'hall', 'lights', 'gameplay', 'cameras'):
        m.add_layer(layer)
    hall(m)
    shops(m)
    south_wall(m)
    west_end(m)
    polisher(m)
    hangings(m)
    SH.hall_life(sys.modules[__name__], m)
    SH.fronts_by_models(sys.modules[__name__], m)
    gameplay(m)
    cameras(m)
    for nm, spec in OWN.items():                                   # our own tiling materials (B.material)
        B.material(m, nm, **spec, layer='shell')
    FX.use_kit(m)
    REPORT['lights'] = {'total': len(LIGHTS), 'by_role': {r: sum(1 for _, rr in LIGHTS if rr == r) for r in sorted({r for _, r in LIGHTS})}}
    REPORT['light_ids'] = LIGHTS[:]
    return m


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    folder = argv[0] if argv else OUT
    m = build()
    m.save(folder)
    side = os.path.dirname(os.path.abspath(folder))
    json.dump({'schema': 'iwz.anchors/1', 'section': 'arcade', 'units': {k: list(v) for k, v in UNITS.items()}, 'anchors': ANCHORS},
              open(os.path.join(side, 'anchors.json'), 'w', encoding='utf-8'), indent=1)
    json.dump(REPORT, open(os.path.join(folder, 'shell_report.json'), 'w', encoding='utf-8'), indent=1, default=str)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'lights': REPORT['lights'], 'standins': sorted(set(REPORT['standins'])),
                      'art': sorted(set(REPORT['art'])), 'refused': REPORT['refused'], 'anchors': len(ANCHORS)}, indent=1, default=str))


if __name__ == '__main__':
    main()
