r"""arcade_layer14: the Underpass Arcade (round 14), ONE self-contained builder (rounds 1 to 13 folded in; the old arcade*.py chain is deleted).

    STUDIO_ROOT=C:\\studio python arcade_layer14.py [folder]     writes the document (default C:\\studio-data\\sz\\arcade\\r14\\doc)

The document this builder wrote before the round-14 changes was byte-identical to round 13's (`r13\\doc_e`: map.json and the seven layers).
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from arcade_dress14 import COLS, GAPS, HUE, REPORT, SPINE_Y, dress, make_pictures  # noqa: E402
from studio import Map  # noqa: E402
from studio import build as B  # noqa: E402
from studio import prefab  # noqa: E402

_SELF = sys.modules[__name__]            # the `A` of the dress functions: this module (geometry constants and aperture())
BAYWALL = ['w/brick_cinderblock_02_smooth_blue', 'w/frag_brick_painted_orange', 'w/aq_plaster_cracked_paint', 'w/brick_wall_painted_blue_01', 'w/brick_cinderblock_02_smooth_white']
BAYFLOOR = ['w/beacon_lab_floor_tile_01', 'w/wood_rustic_floor_02', 'w/ceramic_ship_interior_tile_01', 'w/clk_rubber_tiles', 'w/beacon_lab_floor_tile_02_black']
BASE = r'C:\studio-data\sz\base\emit'
BASE_EMIT = os.environ.get('ARC13_BASE', r'C:\studio-data\sb\base_sb')
X1 = -1200.0
DOOR_Y0 = 3804.0
DOOR_Y1 = 3996.0
DOOR_Z = 224.0
BAY_X = [-2960.0, -2630.0, -2300.0, -1970.0, -1640.0]
BAY_W = 320.0
AP_W = 232.0
AP_H = 120.0
X0 = -3000.0
Y0 = 3500.0
Y1 = 4300.0
H = 256.0
WALL = 'w/brick_cinderblock_04_beige_dirty'
FLOOR = 'w/concrete_floor_polished_01'
CEIL = 'w/concrete_bare_02'
WT = 16.0
BAY_D = 300.0
BAY_H = 200.0
BACK_Y = 4470.0
STOCK = re.compile(r'box_cardboard|crate|gear_shoes|toolbox|grocery|donuts|mug|cup_|bottle|glassware|ashtray|pizza|padlock|tools_nail|bag|trash|snacks|coffee|register|_mags|cigarette|speaker|tv_crt|stackp|chips|paper')
NOSETTLE = re.compile(r'hanging|fluorescent|light|lamp|hook|poster|sign|cage|neon|wall|deco')
K = float(os.environ.get('ARC9_K', '1.0'))
WARM = (1.0, 0.86, 0.66)
BAYS = ['photo', 'heel', 'hole9', 'copy', 'needle']
KE = float(os.environ.get('ARC9_KE', '1.0'))
UP = float(os.environ.get('ARC13_UP', '0.4'))
SIGN_K = float(os.environ.get('ARC13_SIGN_K', '3.5'))
PANEL4 = ('w/signage_theater_menu_01', 'w/zombies_blank_photo', 'w/signage_theater_menu_01')
PANEL5 = ('w/signage_theater_menu_01', 'w/zombies_teddy_photo', 'w/zombies_blank_photo')
FLOOR_SKIN = 'w/building_ship_hallway_floor_06_tile_gray_glossy'
PANEL_DEAD = 'w/concrete_wall_panel_05'
PANEL_LIVE = 'w/glass_led_light_diffuser_01'
SHUTTER = 'w/micro_metal_painted_01_dark_gray'
SHUT_GAP = 80.0
SHUT_SHARE = {0: 0.20, 1: 0.35, 2: 0.20, 3: 0.20, 4: 0.35}
WALLBAND = 'w/ceramic_tile_01_blue'

def build(name='sz_arcade_r13'):
    BAYWALL[2] = 'w/brick_cinderblock_04_beige_dirty'               # as round 11
    BAYFLOOR[2] = 'w/building_ship_hallway_floor_06_tile_gray_glossy'
    global BASE
    BASE = BASE_EMIT
    m = layer8_build(name)
    rep = {}
    fixes9(m, rep)
    unclip_columns(m, rep)
    settle(m, rep)
    lights9(m, rep)
    lights11(m, rep)
    emergency9(m, rep)
    cameras10(m, rep)
    rep['base13'] = {'emit': BASE_EMIT}
    d = m.dresser
    rep['placer'] = {'placed': d.n, 'totals': d.ledger.totals(), 'lines': d.lines(), 'clip_boxes': len(d.clip_boxes)}
    rep['dress_refusals'] = dict(REPORT)
    uplights13(m, rep)
    signs13(m, rep)
    cutwall12(m, rep)
    cameras12(m, rep)
    panels13(m, rep)
    gameplay13(m, rep)
    m.settings.setdefault('build', {}).setdefault('darkness', {})['power'] = {'flag': 'power_on', 'interaction': 'generator'}      # the regenerated base's recipe lacks it (base_r10 had it)
    rep['power_recipe'] = 'power_on/generator'
    m.report9 = rep
    return m


def layer8_build(name='sz_arcade_r8'):
    m = Map(name, 'Station Zero with the Underpass Arcade', base={'kind': 'emit', 'path': BASE}, settings={'map': 'cp_iwz'})
    m.use('arcade_door')
    B.doorway(m, [X1 - 4.0, DOOR_Y0, 0.0, X1 + 4.0, DOOR_Y1, DOOR_Z], 'w/dt_tile_ceramic_white', id='arcade_doorway')
    geometry(m, standalone=False)
    gameplay(m)
    cameras(m)
    dress(_SELF, m, 'full')
    m.use('cameras')                      # cut wall: from the hall side, looking west through D4; from the Arcade side, looking east at the opening
    B.camera(m, 'hall_far', (-700.0, 3900.0, 64.0), 180.0, id='hall_far')
    B.camera(m, 'hall_near', (-1050.0, 3880.0, 64.0), 180.0, id='hall_near')
    B.camera(m, 'hall_door', (-1130.0, 3900.0, 64.0), 175.0, pitch=-2.0, id='hall_door')
    B.camera(m, 'arc_cutwall', (-1450.0, 3900.0, 64.0), 0.0, id='arc_cutwall')
    B.camera(m, 'arc_cutwall_close', (-1290.0, 3880.0, 64.0), 0.0, id='arc_cutwall_close')
    return m


def geometry(m, standalone=True):
    m.use('shell')
    ops = [('n', aperture(i)[0], aperture(i)[1], 0.0, AP_H) for i in range(5)]
    ops.append(('e', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z))
    B.room(m, [X0, Y0, 0.0, X1, Y1, H], WALL, FLOOR, CEIL, openings=ops, thick=WT, id='corridor')
    for i in range(5):
        a0, a1 = aperture(i)
        B.room(m, bay_box(i), BAYWALL[i], BAYFLOOR[i], CEIL, openings=[('s', a0, a1, 0.0, AP_H)], thick=WT, id='bay%d' % (i + 1))
        dx0 = BAY_X[i] + 120.0
        B.wall(m, [BAY_X[i] + WT, BACK_Y, 0.0, BAY_X[i] + BAY_W - WT, BACK_Y + 12.0, BAY_H], BAYWALL[i], axis='x', openings=[(dx0, dx0 + 80.0, 0.0, 96.0)], id='partition%d' % (i + 1))
    if standalone:
        B.room(m, [X1, 3780.0, 0.0, X1 + 200.0, 4020.0, H], WALL, FLOOR, CEIL, openings=[('w', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z)], thick=WT, id='vestibule')
    m.use('dressing')


def aperture(i):
    cx = BAY_X[i] + BAY_W / 2.0
    return cx - AP_W / 2.0, cx + AP_W / 2.0


def bay_box(i):
    return [BAY_X[i], Y1, 0.0, BAY_X[i] + BAY_W, Y1 + BAY_D, BAY_H]


def gameplay(m):
    m.use('gameplay')
    B.zone(m, 'arcade', [X0, Y0, -16.0, X1, Y1 + BAY_D, H + 14.0])
    B.door(m, 'd_hall_arcade', [X1 - 8.0, DOOR_Y0, 0.0, X1 + 8.0, DOOR_Y1, DOOR_Z], 1000, zones=['arcade', 'ticket_hall'], id='door_D4')
    for i in range(5):
        for k, dx in enumerate((62.0, 258.0)):
            B.spawner(m, (BAY_X[i] + dx, 4535.0, 0.0), 270.0, id='spawn_b%d_%d' % (i + 1, k + 1))
    B.spawner(m, (X1 - 90.0, 3640.0, 0.0), 90.0, id='spawn_c_east')
    B.spawner(m, (X0 + 100.0, 3640.0, 0.0), 0.0, id='spawn_c_west')
    B.wallbuy(m, (-2560.0, Y0 + WT + 6.0, 0.0), 'smg', 1000, 90.0, id='buy_smg')
    B.wallbuy(m, (-1860.0, Y0 + WT + 6.0, 0.0), 'marksman', 1500, 90.0, id='buy_marksman')


def cameras(m):
    """round 8b: the two long cameras stand in the north lane (y = 4080), off the column line; two cameras added (south lane, the kiosk island). The other ten as in round 1."""
    m.use('cameras')
    B.camera(m, 'arc_east_long', (-1290.0, 4080.0, 60.0), 180.0, id='arc_east_long')
    B.camera(m, 'arc_west_long', (-2910.0, 4080.0, 60.0), 0.0, id='arc_west_long')
    B.camera(m, 'arc_south_lane_east', (-1290.0, 3700.0, 60.0), 180.0, id='arc_south_lane_east')
    B.camera(m, 'arc_spine_island', (-2700.0 + 177.0, 3900.0 + 177.0, 60.0), 225.0, id='arc_spine_island')   # 250 units north-east of the kiosk (GAPS[0] = -2700)
    for i in range(5):
        cx = BAY_X[i] + BAY_W / 2.0
        B.camera(m, 'arc_bay%d' % (i + 1), (cx, Y0 + 100.0, 64.0), 90.0, pitch=-4.0, id='arc_bay%d' % (i + 1))
    B.camera(m, 'arc_south_wall', (-2100.0, 4110.0, 64.0), 270.0, id='arc_south_wall')
    B.camera(m, 'arc_d7', (X0 + 330.0, 3900.0, 64.0), 180.0, id='arc_d7')
    B.camera(m, 'arc_inside_bay3', (BAY_X[2] + 160.0, 4345.0, 62.0), 90.0, id='arc_inside_bay3')


def fixes9(m, report):
    n = 0
    for o in m.objects():
        if o['kind'] == 'box' and o.get('material') == 'w/asphalt_flooring_01_wet':
            m.update(o['id'], material='w/aq_stone_concrete_patch02')
            n += 1
    report['lanes_retextured'] = n


def unclip_columns(m, report):
    cols = [(x, SPINE_Y) for x in COLS]
    pushed, removed = 0, 0
    for o in list(m.objects()):
        if o['kind'] != 'prop' or o['origin'][2] > 200.0 or o['id'].startswith('col_'):
            continue
        if re.search(r'column|pillar|dojo|light|extinguisher|lamp|poster|map|cabinet|sign', o['model'] or ''):
            continue
        bb = bounds_xy(o)
        if bb is None:
            continue
        for (cx, cy) in cols:
            ex0, ex1, ey0, ey1 = cx - 22.0, cx + 22.0, cy - 22.0, cy + 22.0
            if bb[0] < ex1 and bb[3] > ex0 and bb[1] < ey1 and bb[4] > ey0 and bb[5] > 4.0:
                px = min(ex1 - bb[0], bb[3] - ex0)
                py = min(ey1 - bb[1], bb[4] - ey0)
                og = list(o['origin'])
                if py <= px:
                    og[1] += (ey1 - bb[1] + 3.0) if (bb[1] + bb[4]) / 2.0 >= cy else -(bb[4] - ey0 + 3.0)
                else:
                    og[0] += (ex1 - bb[0] + 3.0) if (bb[0] + bb[3]) / 2.0 >= cx else -(bb[3] - ex0 + 3.0)
                m.update(o['id'], origin=og)
                pushed += 1
                break
    report['unclip'] = {'pushed_out_of_columns': pushed, 'removed': removed}


def bounds_xy(o):
    mn, mx = prefab._model_bounds(o['model']) or (None, None)
    if mn is None:
        return None
    s = float(o.get('scale') or 1.0)
    yaw = math.radians(float(o.get('yaw') or 0.0))
    c, sn = math.cos(yaw), math.sin(yaw)
    xs, ys = [], []
    for x in (mn[0] * s, mx[0] * s):
        for y in (mn[1] * s, mx[1] * s):
            xs.append(o['origin'][0] + x * c - y * sn)
            ys.append(o['origin'][1] + x * sn + y * c)
    z0 = o['origin'][2] + mn[2] * s
    z1 = o['origin'][2] + mx[2] * s
    return [min(xs), min(ys), z0, max(xs), max(ys), z1]


def settle(m, report):
    """small stock props float on shelf levels that are not where they were placed: each goes down onto the highest thing under its centre (a board or box of the document, the
    floor, another settled prop) within 60 units; with nothing under it within 60 it is removed"""
    surfaces = []                                               # [x0, y0, x1, y1, ztop]
    for o in m.objects():
        if o['kind'] == 'box' and 'box' in o and o['box'][5] < 230.0:
            b = o['box']
            if (b[3] - b[0]) * (b[4] - b[1]) > 20.0 and (b[5] - b[2]) > 0.2:
                surfaces.append([b[0], b[1], b[3], b[4], b[5]])
    props = [o for o in m.objects() if o['kind'] == 'prop' and o['model'] and STOCK.search(o['model']) and not NOSETTLE.search(o['model']) and o['origin'][2] > 3.0]
    models = []                                                 # non-stock props with a body (shelf models, cabinets, tables): what is inside their volume is judged by no one
    for o in m.objects():
        if o['kind'] == 'prop' and o['model'] and not STOCK.search(o['model']) and not NOSETTLE.search(o['model']):
            bb = bounds_xy(o)
            if bb and (bb[5] - bb[2]) > 30.0:
                models.append(bb)
    moved, removed, kept = 0, 0, 0
    log = []
    props.sort(key=lambda o: o['origin'][2])
    done = []                                                   # settled bounds (tops become support)
    for o in props:
        bb = bounds_xy(o)
        if bb is None:
            continue
        cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
        hx, hy = 0.0, 0.0                                           # the centre of the footprint must be over the support (items sit at a board's edge)
        z0 = bb[2]
        if any(b[0] <= cx <= b[3] and b[1] <= cy <= b[4] and b[2] + 4.0 < z0 < b[5] for b in models):
            kept += 1                                           # on a board of a shelf model: its boards are not in the bounds
            continue
        best = None
        for s in surfaces:
            if s[0] - 0.5 <= cx - hx and cx + hx <= s[2] + 0.5 and s[1] - 0.5 <= cy - hy and cy + hy <= s[3] + 0.5 and s[4] <= z0 + 1.0:
                best = s[4] if best is None else max(best, s[4])
        for b in models:                                        # a table, counter or crate model: its top is a surface
            if b[0] <= cx <= b[3] and b[1] <= cy <= b[4] and b[5] <= z0 + 3.0 and b[5] > z0 - 4.0:
                best = b[5] if best is None else max(best, b[5])
        for d in done:
            if d[0] <= cx <= d[3] and d[1] <= cy <= d[4] and d[5] <= z0 + 1.0 and (d[5] - d[2]) > 2.0:
                best = d[5] if best is None else max(best, d[5])
        if best is None:
            best = 0.0                                          # the floor: the bays' floors are at 0
            if z0 > 60.0:
                m.remove(o['id'])
                removed += 1
                log.append(('rm', o['id'], o['model'], round(z0)))
                continue
        gap = z0 - best
        if gap < 0.0:
            gap = 0.0
        if gap <= 2.0:
            kept += 1
            done.append(bb)
            continue
        if gap > 60.0:
            m.remove(o['id'])
            removed += 1
            log.append(('rm', o['id'], o['model'], round(z0)))
            continue
        og = list(o['origin'])
        og[2] -= gap
        m.update(o['id'], origin=og)
        bb = bounds_xy(m.get(o['id']))
        done.append(bb)
        moved += 1
        log.append(('mv', o['id'], o['model'], round(z0, 1), round(gap, 1)))
    report['settle_log'] = log
    report['settle'] = {'moved_down': moved, 'removed_nothing_under': removed, 'already_supported': kept, 'considered': len(props)}


def lights9(m, report):
    """Light model of the baker (bake/lmbake.py): E = I * (100/d)^2 * cos * (1 - (d/R)^4)^2, zero beyond R. Round 8's panels hung at z 176 with R 170: the floor (d >= 176) got none.
    Here every light that is meant for the floor hangs 110 to 130 above it with R 190 to 220, cones stop at 80 degrees so the ceiling gets nothing direct. The compiler's voxel
    light lists hold 65535 entries: the sum of R^3 of the document's lights was 321e6 in round 8 (built), 542e6 and 619e6 here (542 built, 619 refused), so the budget is about 560e6."""
    n = 0
    old = {o['id']: o for o in m.objects() if o['kind'] == 'light'}
    for pid, o in old.items():                                  # the twelve ceiling panels: the light sits 56 under the fixture, in its throw
        if pid.startswith('light_pool_'):
            single = o['intensity'] < 1.5
            x, y, z = o['origin']
            if x > X1 - 130.0:                                # panels 32 from an end wall blew the wall (arc_cutwall: 28 % clipped): pulled 80 inward
                x -= 80.0
            elif x < X0 + 130.0:
                x += 80.0
            m.update(pid, origin=[x, y, 120.0], radius=190.0, intensity=round(1.6 * K * (0.6 if single else 1.0), 3), inner=40.0, outer=80.0)
    for pid, o in old.items():
        if pid.startswith(('light_colS_', 'light_colN_')):      # the omnis 108 under the ceiling (the cream ceiling) go; one downward spot per column on the south side
            x, y, z = o['origin']
            m.remove(pid)
            if 'colN' in pid:
                continue
            light(m, (x, y, 120.0), pid, color=(1.0, 0.86, 0.62), radius=170.0, intensity=round(0.6 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=30.0, outer=80.0)
            n += 1
        elif pid.startswith('light_back_'):
            x, y, z = o['origin']
            m.remove(pid)
            light(m, (x, y, 120.0), pid, color=WARM, radius=170.0, intensity=round(1.3 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
            n += 1
        elif pid == 'light_kiosk':
            m.update(pid, intensity=0.35)
    for i in range(5):                                          # the back light box took the shop's hue (pink in bay 3 on a .62 albedo wall): half way to warm white
        pid = 'fx_back_%d_l1' % (i + 1)
        if pid in old:
            m.update(pid, color=list(mix(old[pid]['color'], WARM, 0.65)), intensity=round(old[pid]['intensity'] * 1.5, 3))
    m.update('light_d7_cage', origin=[X0 + 70.0, 4040.0, 120.0], intensity=round(0.6 * K, 3), radius=190.0, inner=40.0, outer=80.0)
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):      # fills in the lanes between the panel clusters
        for j, y in enumerate((3620.0, 4180.0)):
            if (k + j) % 2:
                continue
            light(m, (x, y, 110.0), 'light_fill_%d_%d' % (k, j), color=(1.0, 0.92, 0.78), radius=175.0, intensity=round(1.3 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
            n += 1
    for k, x in enumerate(GAPS):
        if k % 2:
            continue
        light(m, (x, SPINE_Y, 110.0), 'light_spine_%d' % k, color=(1.0, 0.9, 0.74), radius=190.0, intensity=round(1.2 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
        n += 1
    for k, x in enumerate((-2850.0, -2250.0, -1650.0)):         # south wall washers
        light(m, (x, 3650.0, 150.0), 'light_wash_s_%d' % k, color=(1.0, 0.9, 0.74), radius=200.0, intensity=round(1.1 * K, 3), type='spot', dir=(0.0, -0.8, -0.4), inner=20.0, outer=70.0)
        n += 1
    for i in range(5):                                          # the shop interiors, lit from inside
        cx = BAY_X[i] + BAY_W / 2.0
        hue = HUE[BAYS[i]]
        light(m, (cx, 4400.0, 130.0), 'light_in_front_%d' % (i + 1), color=mix(hue, WARM, 0.7), radius=165.0, intensity=round(1.5 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
        n += 1
    report['lights9'] = {'added': n}


def light(m, origin, id, **k):
    m.use('lights')
    return B.light(m, origin, layer='lights', id=id, **k)


def mix(c, d, t):
    return tuple(round(c[i] * (1.0 - t) + d[i] * t, 3) for i in range(3))


def lights11(m, report):
    """round 11 (FL1 fixed: the downward power spots now light the floor). Numbers: studio light --survey --zone arcade (r11a document, power on): the five `light_key_*` (R 280 in the document, 504 built)
    put 51 to 71 % of their light behind the shutters, partitions and walls; `fx_back_*` sat INSIDE the partition (y 4474.8, the wall is 4470..4482): 100 % blocked by their own wall;
    `fx_tube_*` 36 to 80 % behind geometry, 72 to 81 % of the rest on walls. r11a frames (power on, display luminance): the floor third 0.22 to 0.77 on 14 cameras, the mean 0.18 to 0.45."""
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'light']:
        pid = o['id']
        if pid.startswith('light_key_'):
            m.update(pid, radius=200.0, intensity=round(o['intensity'] * 0.8, 3)); n += 1
        elif pid.startswith('fx_back_'):
            x, y, z = o['origin']
            m.update(pid, origin=[x, 4464.0, z]); n += 1                  # out of the partition, into the shop
        elif pid.startswith('fx_tube_'):
            m.update(pid, radius=125.0); n += 1
        elif pid.startswith(('light_pool_', 'light_spine_', 'light_fill_')):
            hall_side = o['origin'][0] > -1450.0                                  # r11 frames: conv_bench and hall_far (the hall end) lost their floor light at 0.7
            m.update(pid, intensity=round(o['intensity'] * (1.2 if hall_side else 0.7), 3)); n += 1
    report['lights11'] = {'updated': n}


def emergency9(m, report):
    """group 'emergency': baked in both states and switched by nothing. Neon that stays lit, exit signs, red wall lamps, orange floor beacons, amber bay lamps"""
    ids = []

    def fx(kind, at, facing, **k):
        r = B.fixture(m, kind, at, facing, group='emergency', **k)
        ids.extend(r)
    m.use('lights')
    for i in range(5):                                       # the shop neon stays lit
        for pid in ('fx_sign_%d_l1' % (i + 1),):
            if pid in m:
                o = m.get(pid)
                m.update(pid, group='emergency', intensity=round(o['intensity'] * 3.0 * KE, 3), radius=round(o['radius'] * 1.4, 1))
    for k, x in enumerate((-2800.0, -2300.0, -1800.0, -1350.0)):     # red lamps along the south wall
        fx('emergency_wall', (x, Y0 + WT + 1.0, 150.0), 90.0, intensity=7.0 * KE, radius=1.4)
    xs = [(aperture(i)[1] + aperture(i + 1)[0]) / 2.0 for i in range(4)]            # and the piers between the shop openings, on the north wall
    for k, x in enumerate(xs):
        if k % 2:
            continue
        fx('emergency_wall', (x, Y1 - WT - 1.0, 150.0), 270.0, intensity=7.0 * KE, radius=1.4)
    fx('exit_sign', (X1 - WT - 1.0, 3900.0, 205.0), 180.0, intensity=4.0 * KE, radius=1.9)           # over D4
    fx('exit_sign', (X0 + WT + 1.0, 4040.0, 205.0), 0.0, intensity=4.0 * KE, radius=1.9)             # over D7
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):     # orange beacons on the floor of both lanes
        for j, y in enumerate((3640.0, 4170.0)):
            if (k + j) % 2 or k % 2:
                continue
            fx('emergency_beacon', (x + (60.0 if j else -60.0), y, 0.0), 0.0, intensity=2.2 * KE, radius=1.8)
    for i in range(5):                                        # an amber lamp inside each shop, on its east wall
        fx('beacon_wall', (BAY_X[i] + BAY_W - WT - 0.5, 4390.0, 165.0), 180.0, intensity=4.0 * KE, radius=1.9)
    for k, (x, y) in enumerate(((-1100.0, 3820.0), (-950.0, 3900.0), (-800.0, 4020.0))):   # the hall side of D4
        fx('emergency_beacon', (x, y, 0.0), 0.0, intensity=2.5 * KE, radius=1.9)
    report['emergency9'] = {'ids': len(ids)}


def cameras10(m, report):
    """three cameras at models that became static (the 17 of round 9 do not see them): a turnstile row, benches, the platform edge and tracks"""
    m.use('cameras')
    B.camera(m, 'conv_turnstile', (130.0, 3500.0, 64.0), 90.0, id='conv_turnstile')
    B.camera(m, 'conv_bench', (-950.0, 4120.0, 64.0), 90.0, id='conv_bench')
    B.camera(m, 'conv_platform', (-2300.0, 1900.0, -256.0), 270.0, pitch=12.0, id='conv_platform')
    report['cameras10'] = ['conv_turnstile', 'conv_bench', 'conv_platform']


def uplights13(m, report):
    """r12's uplights at UP, the conv_bench downlights as they were (no softening of the column spots: round 11's)"""
    n = 0
    for k, x in enumerate(GAPS):
        for j, y in enumerate((3640.0, 4160.0)):
            if (k + j) % 2:
                continue
            layer12_light(m, (x, y, 140.0), 'light_up_%d_%d' % (k, j), color=(1.0, 0.9, 0.74), radius=120.0, intensity=round(UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=80.0)
            n += 1
    for k, x in enumerate(COLS):
        layer12_light(m, (x, 3938.0, 100.0), 'light_upc_%d' % k, color=(1.0, 0.86, 0.62), radius=120.0, intensity=round(0.9 * UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=85.0)
        n += 1
    for k, y in enumerate((3640.0, 4160.0)):
        layer12_light(m, (-1290.0, y, 120.0), 'light_upw_%d' % k, color=(1.0, 0.9, 0.74), radius=135.0, intensity=round(UP, 3), type='spot', dir=(1.0, 0.0, 0.5), inner=30.0, outer=85.0)
        n += 1
    for k, (x, y) in enumerate(((-1010.0, 4060.0), (-900.0, 4180.0), (-1080.0, 4200.0))):
        layer12_light(m, (x, y, 120.0), 'light_bench_%d' % k, color=(1.0, 0.9, 0.72), radius=160.0, intensity=1.4, type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
        n += 1
    report['uplights13'] = {'added': n, 'up': UP}


def layer12_light(m, origin, id, **k):
    m.use('lights')
    return B.light(m, origin, layer='lights', id=id, **k)


def signs13(m, report):
    """round 13a (an extra ON-only light on the neon fixtures) washed the ceiling in the signs' colours and moved the text boards' ON p98 down (0.208 -> 0.112 in arc_bay2): the boards that are measured
    are text signs with `emissive` (cn_* 1.2, the five shop name signs strength 2.2), a fixed radiance that the auto exposure of the lit state darkens. Their emissive is multiplied by SIGN_K."""
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'sign' and o.get('emissive')]:
        e = o['emissive']
        if isinstance(e, dict):
            e = dict(e, strength=round(float(e.get('strength', 1.5)) * SIGN_K, 3))
        else:
            e = round(float(1.5 if e is True else e) * SIGN_K, 3)
        m.update(o['id'], emissive=e)
        n += 1
    report['signs13'] = {'emissive_signs': n, 'factor': SIGN_K}


def cutwall12(m, report):
    """e. a head trim over the doorway: a beam across the top of the opening, proud of the wall on both sides"""
    m.use('shell')
    B.box(m, (-1210.0, 3792.0, 214.0, -1190.0, 4008.0, 228.0), 'w/dt_tile_ceramic_white', id='cutwall_lintel')
    report['cutwall12'] = {'lintel': 'cutwall_lintel'}


def cameras12(m, report):
    """c. cameras inside the shops, at the back walls where the blue/white square patterns were seen"""
    m.use('cameras')
    for i, nm in ((3, 'chk_bay4'), (4, 'chk_bay5'), (2, 'chk_bay3')):
        cx = BAY_X[i] + BAY_W / 2.0
        B.camera(m, nm, (cx, 4310.0, 70.0), 90.0, id=nm)
    report['cameras12'] = ['chk_bay3', 'chk_bay4', 'chk_bay5']


def panels13(m, report):
    """the hung graphics of bays 4 and 5 with materials that draw as posters"""
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'box' and str(o['id']).startswith(('hg_3_', 'hg_4_')) and not str(o['id']).endswith(('_ra', '_rb'))]:
        i, k = str(o['id']).split('_')[1:3]
        pool = PANEL4 if i == '3' else PANEL5
        m.update(o['id'], material=pool[int(k) % len(pool)])
        n += 1
    report['panels13'] = {'updated': n}


def gameplay13(m, report):
    """DG's two fixes. FE24: the base hall bench (cp_disco_worn_subway_bench at -1138 4000) and its clip box stand in the D4 opening (y 3804-3996): removed.
    FE42: the bay spawners at y 4535 (facing south) carry the zombie's emergence up to 62 units into the partition walls (y 4470-4482): moved to y 4565."""
    m.use('arcade_door' if 'arcade_door' in m.layers else 'shell')
    B.replace(m, box=[-1170, 3900, -1, -1106, 4100, 100], what=['props'], id='clear_bench_props')
    B.replace(m, box=[-1170, 3900, 2, -1106, 4100, 100], what=['collision'], clip=True, id='clear_bench_clip')
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'spawner' and str(o['id']).startswith('spawn_b')]:
        x, y, z = o['at']
        m.update(o['id'], at=[x, 4565.0, z])
        n += 1
    report['gameplay13'] = {'bench_replace': 2, 'spawners_moved': n}


def main(argv=None):
    argv = argv or sys.argv[1:]
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r13\layer_doc'
    m = build()
    m.save(folder)
    json.dump(m.report9, open(os.path.join(folder, 'report13.json'), 'w'), indent=1, default=str)
    make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report13': {k: v for k, v in m.report9.items() if k not in ('settle_log', 'placer', 'dress_refusals')}}, indent=1, default=str)[:4000])

