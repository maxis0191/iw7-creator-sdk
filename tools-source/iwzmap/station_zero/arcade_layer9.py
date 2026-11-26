r"""The Underpass Arcade (round 9) as a LAYER of the Station Zero document: round 8's layer (arcade_layer8: shell, dressing, gameplay, cameras) plus the light and support fixes of round 9.

    STUDIO_ROOT=C:\studio python arcade_layer9.py [folder]     writes the document (default C:\studio-data\sz\arcade\r9\layer_doc)

What round 8's review (3 independent readers, mean 5.8) agreed on, and what this file does about it (every number is checked on the 17 cameras, power off and on, by
C:\studio-data\sz\arcade\r9\lumstats.py):
  1. Power on, black mid-room: the twelve ceiling panels were spots of radius 170 hung 176 above the floor (the baker's window is zero beyond the radius: no floor light at all), the
     column omnis hung 108 under the ceiling (the cream ceiling). Panels get a reach of 420 and a wide soft cone, the column and back-room omnis become downward spots, a grid of wide
     fills, south wall washers and per shop interior lights are added.
  2. Power off: a real emergency layer, group 'emergency' (baked, switched by nothing): red wall lamps, orange floor beacons, exit signs, the shop neon (group moved to emergency), amber
     bay lamps, beacons in the hall by D4.
  3. Bay 3: its pink wall and white tile floor become the beige block and the dark ship tile (the baker's albedo rule gave plaster .62 / ceramic .62), its back light is warm not pink,
     and every small stock prop (boxes, crates, bottles ...) is settled onto what is under it (a board, the floor, another prop) or removed when nothing is under it.
  4. The dark wet asphalt lane boxes (the arc_bay5 patch) get a concrete patch material; props that clip a column are pushed out of it.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade8 as A  # noqa: E402
import arcade_layer8 as L8  # noqa: E402
import arcade_dress4 as D4  # noqa: E402
from studio import build as B  # noqa: E402
from studio import prefab  # noqa: E402

K = float(os.environ.get('ARC9_K', '1.0'))                  # global multiplier of the new fills (tuning knob, 1.0 = as designed)
KE = float(os.environ.get('ARC9_KE', '1.0'))                # global multiplier of the emergency layer
WARM = (1.0, 0.86, 0.66)
STOCK = re.compile(r'box_cardboard|crate|gear_shoes|toolbox|grocery|donuts|mug|cup_|bottle|glassware|ashtray|pizza|padlock|tools_nail|bag|trash|snacks|coffee|register|_mags|cigarette|speaker|tv_crt|stackp|chips|paper')
NOSETTLE = re.compile(r'hanging|fluorescent|light|lamp|hook|poster|sign|cage|neon|wall|deco')


def light(m, origin, id, **k):
    m.use('lights')
    return B.light(m, origin, layer='lights', id=id, **k)


# ------------------------------------------------------------------------------------------------ geometry and support
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


def unclip_columns(m, report):
    cols = [(x, D4.SPINE_Y) for x in D4.COLS]
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


# ------------------------------------------------------------------------------------------------ light
def mix(c, d, t):
    return tuple(round(c[i] * (1.0 - t) + d[i] * t, 3) for i in range(3))


def lights9(m, report):
    n = 0
    old = {o['id']: o for o in m.objects() if o['kind'] == 'light'}
    # 1. the ceiling panels: spots hung 176 above the floor with a reach of 170 gave the floor nothing; reach 420, wide soft cone
    for pid, o in old.items():
        if pid.startswith('light_pool_'):
            single = o['intensity'] < 1.5
            m.update(pid, radius=420.0, intensity=round(1.5 * K * (0.6 if single else 1.0), 3), inner=36.0, outer=88.0)
    # 2. the omnis that hung 108 under the ceiling (the cream ceiling) become downward spots lower on the column, and the back room lamps too
    for pid, o in old.items():
        if pid.startswith(('light_colS_', 'light_colN_')):
            x, y, z = o['origin']
            m.remove(pid)
            light(m, (x, y, 130.0), pid, color=(1.0, 0.86, 0.62), radius=300.0, intensity=round(0.55 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=30.0, outer=85.0)
            n += 1
        elif pid.startswith('light_back_'):
            x, y, z = o['origin']
            m.remove(pid)
            light(m, (x, y, 170.0), pid, color=WARM, radius=300.0, intensity=round(1.1 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=35.0, outer=90.0)
            n += 1
        elif pid == 'light_kiosk':
            m.update(pid, intensity=0.35)
    # the light box of each back room took the shop's hue (pink in bay 3 on a .62 albedo wall): its colour is the hue half way to warm white
    for i in range(5):
        pid = 'fx_back_%d_l1' % (i + 1)
        if pid in old:
            m.update(pid, color=list(mix(old[pid]['color'], WARM, 0.65)), intensity=round(old[pid]['intensity'] * 1.5, 3))
    # the two ends: the vanishing points were the dark doorway of D4 (the hall behind it) and the plated D7
    m.update('light_d4', intensity=round(0.9 * K, 3), radius=300.0, inner=30.0, outer=85.0)
    m.update('light_d7_cage', intensity=round(1.2 * K, 3), radius=320.0, inner=30.0, outer=85.0)
    # 3. a grid of wide fills in the lanes (floor and the lower walls carry light between the panels' clusters)
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):
        for j, y in enumerate((3620.0, 4180.0)):
            light(m, (x, y, 214.0), 'light_fill_%d_%d' % (k, j), color=(1.0, 0.92, 0.78), radius=480.0, intensity=round(0.9 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=95.0)
            n += 1
    # the spine (columns, islands, kiosk): a few downward fills over its gaps
    for k, x in enumerate(D4.GAPS):
        light(m, (x, D4.SPINE_Y, 214.0), 'light_spine_%d' % k, color=(1.0, 0.9, 0.74), radius=420.0, intensity=round(0.8 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=95.0)
        n += 1
    # south wall washers (posters, wall buys, the wainscot)
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):
        light(m, (x, 3650.0, 214.0), 'light_wash_s_%d' % k, color=(1.0, 0.9, 0.74), radius=420.0, intensity=round(0.9 * K, 3), type='spot', dir=(0.0, -0.8, -0.6), inner=22.0, outer=75.0)
        n += 1
    # the ends of the corridor: the walls of D7 and D4 get a wash each
    light(m, (A.X0 + 260.0, 3900.0, 214.0), 'light_wash_w', color=(1.0, 0.88, 0.7), radius=420.0, intensity=round(0.9 * K, 3), type='spot', dir=(-1.0, 0.0, -0.45), inner=25.0, outer=80.0)
    light(m, (A.X1 - 260.0, 3900.0, 214.0), 'light_wash_e', color=(1.0, 0.88, 0.7), radius=420.0, intensity=round(0.9 * K, 3), type='spot', dir=(1.0, 0.0, -0.45), inner=25.0, outer=80.0)
    n += 2
    # 4. the shop interiors, lit from inside: a wide key at the front third, one at the back third, warm
    for i in range(5):
        cx = A.BAY_X[i] + A.BAY_W / 2.0
        hue = D4.HUE[A.BAYS[i]]
        light(m, (cx, 4395.0, 186.0), 'light_in_front_%d' % (i + 1), color=mix(hue, WARM, 0.7), radius=330.0, intensity=round(1.0 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=95.0)
        light(m, (cx, 4530.0, 186.0), 'light_in_back_%d' % (i + 1), color=mix(hue, WARM, 0.7), radius=300.0, intensity=round(0.8 * K, 3), type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=95.0)
        for sgn in (-1, 1):                                          # the stock shelves on both side walls
            light(m, (cx + sgn * 40.0, 4470.0, 150.0), 'light_in_side_%d_%d' % (i + 1, sgn > 0), color=mix(hue, WARM, 0.7), radius=260.0, intensity=round(0.5 * K, 3), type='spot',
                  dir=(sgn * 0.9, 0.0, -0.3), inner=30.0, outer=85.0)
        n += 4
    report['lights9'] = {'added': n}


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
                m.update(pid, group='emergency', intensity=round(o['intensity'] * 3.0 * KE, 3), radius=round(o['radius'] * 1.8, 1))
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):     # red lamps along the south wall
        fx('emergency_wall', (x, A.Y0 + A.WT + 1.0, 150.0), 90.0, intensity=5.0 * KE, radius=2.6)
    xs = [(A.aperture(i)[1] + A.aperture(i + 1)[0]) / 2.0 for i in range(4)]            # and the piers between the shop openings, on the north wall
    for k, x in enumerate(xs):
        fx('emergency_wall', (x, A.Y1 - A.WT - 1.0, 150.0), 270.0, intensity=5.0 * KE, radius=2.6)
    fx('exit_sign', (A.X1 - A.WT - 1.0, 3900.0, 205.0), 180.0, intensity=4.0 * KE, radius=2.5)           # over D4
    fx('exit_sign', (A.X0 + A.WT + 1.0, 4040.0, 205.0), 0.0, intensity=4.0 * KE, radius=2.5)             # over D7
    for k, x in enumerate((-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0)):     # orange beacons on the floor of both lanes
        for j, y in enumerate((3640.0, 4170.0)):
            fx('emergency_beacon', (x + (60.0 if j else -60.0), y, 0.0), 0.0, intensity=2.2 * KE, radius=2.2)
    for i in range(5):                                        # an amber lamp inside each shop, on its east wall
        fx('beacon_wall', (A.BAY_X[i] + A.BAY_W - A.WT - 0.5, 4390.0, 165.0), 180.0, intensity=4.0 * KE, radius=2.4)
    for k, (x, y) in enumerate(((-1100.0, 3820.0), (-1100.0, 3980.0), (-950.0, 3900.0), (-800.0, 3780.0), (-800.0, 4020.0))):   # the hall side of D4
        fx('emergency_beacon', (x, y, 0.0), 0.0, intensity=2.5 * KE, radius=2.4)
    report['emergency9'] = {'ids': len(ids)}


def fixes9(m, report):
    n = 0
    for o in m.objects():
        if o['kind'] == 'box' and o.get('material') == 'w/asphalt_flooring_01_wet':
            m.update(o['id'], material='w/aq_stone_concrete_patch02')
            n += 1
    report['lanes_retextured'] = n


def build(name='sz_arcade_r9'):
    A.BAYWALL[2] = 'w/brick_cinderblock_04_beige_dirty'               # bay 3: the pink plaster (.62 albedo rule) -> the beige block of the corridor
    A.BAYFLOOR[2] = 'w/building_ship_hallway_floor_06_tile_gray_glossy'   # bay 3: the white ceramic (.62) -> the dark ship tile
    m = L8.build(name)
    rep = {}
    fixes9(m, rep)
    unclip_columns(m, rep)
    settle(m, rep)
    lights9(m, rep)
    emergency9(m, rep)
    m.report9 = rep
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r9\layer_doc'
    m = build()
    m.save(folder)
    json.dump(m.report9, open(os.path.join(folder, 'report9.json'), 'w'), indent=1, default=str)
    L8.D8.make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report9': {k: v for k, v in m.report9.items() if k != 'settle_log'}}, indent=1, default=str)[:4000])


if __name__ == '__main__':
    main()
