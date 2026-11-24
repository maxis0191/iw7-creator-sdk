"""arcade_dress3: the dressing and the light of the Underpass Arcade, round 3 (called by arcade3.build_arcade).

Round 2 left an empty hall (105 props per 1000 x 1000), a flat orange floor, flat light and shops that read as small dim boxes. Round 3:
  structure  a spine of 32 x 32 columns along y = 3900 with an island between the columns, a dropped soffit over it, sign bars hung over the islands; both walls get a dark
             wainscot, a kick plate, pilasters, a grime line;
  floor      a dark tile skin, a black border, an orange inlay line down each lane;
  light      ambient 0.0028, twelve live panels in three clusters and a single, every other panel dead and dark; each shop a warm key, two washes on the stock, a hue spill
             INSIDE the shop and an emissive sign box; two caged wall lamps on the south wall;
  stock      tall shelving on every back wall filled with props, a glass display counter with lit contents, hanging objects, posters on the side walls.
Counters, shelves, booths, signs, columns and islands are GEOMETRY (they cost no model kind: a live session takes 63 to 64 distinct models, FA8).
"""
import math
import os
import random

import arcade_dress as R1
import arcade_dress2 as R2
from studio import build as B

R1.SUBST.clear()
PROP_CAP, LIGHT_CAP, MODEL_CAP = 760, 52, 63
CAL = bool(os.environ.get('ARC3_CAL'))
HUE, TUBE, M = R2.HUE, R2.TUBE, R2.M
M.update(sign1='cp_disco_sign_01', sign2='cp_disco_sign_02', sign4='cp_disco_sign_04', lamp='p7_lights_cagelight02_on')
box = R2.box
POOL_I = float(os.environ.get('ARC3_POOL', '2.8'))
KEY_I = float(os.environ.get('ARC3_KEY', '0.6'))
WASH_I = float(os.environ.get('ARC3_WASH', '0.75'))
SPILL_I = float(os.environ.get('ARC3_SPILL', '0.10'))

BLACK, DARKMETAL, RUBBER = 'w/metal_painted_01_black', 'w/metal_panel_dark_01', 'w/rubber_trim_black'
BOARD = {'photo': 'w/plaster_wall_04_turquoise', 'heel': 'w/frag_plaster_orange_dirty', 'hole9': 'w/iw7_drywall_painted_purple_02', 'copy': 'w/iw7_drywall_painted_blue_02',
         'needle': 'w/iw7_drywall_painted_red_01'}
BODY = {'photo': 'w/plaster_wall_04_turquoise', 'heel': 'w/frag_plaster_orange_dirty', 'hole9': 'w/iw7_drywall_painted_purple_02', 'copy': 'w/iw7_drywall_painted_blue_02',
        'needle': 'w/wood_worn_painted_01_red'}
POSTERS = ['w/signage_theater_menu_01', 'w/signage_zmb_park_poster_01', 'w/signage_zmb_park_poster_04', 'w/signage_zmb_park_poster_06', 'w/signage_decals_corridor_01']
NAMES = {'photo': 'PHOTOS', 'heel': 'HEEL & KEY', 'hole9': 'HOLE NUMBER NINE', 'copy': 'COPY STOP', 'needle': 'NEEDLE DROP'}
SPINE_Y = 3900.0
COLS = [-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0]
GAPS = [-2700.0, -2400.0, -2100.0, -1800.0, -1500.0]
PIERS = [(-2984.0, -2916.0), (-2684.0, -2586.0), (-2354.0, -2256.0), (-2024.0, -1926.0), (-1694.0, -1596.0), (-1364.0, -1216.0)]
FRONTS = [(-2480.0, -2220.0), (-1790.0, -1500.0), (-1470.0, -1290.0)]          # the three closed shop fronts of the south wall
HATCH = (-2130.0, -2030.0)


def foot(D, x0, y0, x1, y1):
    """a footprint of geometry the props must not stand in"""
    D.boxes.append((x0, y0, x1, y1))


# ------------------------------------------------------------------------------------------------ shutters (as round 2, one material per bay in the calibration run)
def shutters(A, m, report):
    m.use('dressing')
    yin = A.Y1 - A.WT
    info = {}
    cands = ['w/micro_metal_painted_01_dark_gray', 'w/metal_deck_painted_black_01', 'w/metal_galvanized_bare_dark_01', 'w/metal_painted_dark_blue', 'w/metal_corrugated_01']
    for i in range(5):
        a0, a1 = A.aperture(i)
        share = A.SHUT_SHARE[i]
        zb = A.AP_H * (1.0 - share)
        jam = share > 0.5
        x1 = a1 - A.SHUT_GAP if jam else a1
        mat = cands[i] if CAL else A.SHUTTER
        B.box(m, [a0, yin + 4.0, zb, x1, yin + 8.0, A.AP_H], mat, id='shutter_curtain_%d' % (i + 1))
        box(m, [a0, yin + 3.0, zb - 3.0, x1, yin + 9.0, zb], BLACK, id='shutter_bar_%d' % (i + 1))
        box(m, [a0 - 8.0, yin - 14.0, A.AP_H, a1 + 8.0, yin, A.AP_H + 24.0], BLACK, id='shutter_box_%d' % (i + 1))
        box(m, [a0 - 7.0, yin - 2.0, 0.0, a0 - 1.0, yin + 3.0, A.AP_H], BLACK, id='rail_l_%d' % (i + 1))
        box(m, [a1 + 1.0, yin - 2.0, 0.0, a1 + 7.0, yin + 3.0, A.AP_H], BLACK, id='rail_r_%d' % (i + 1))
        info[i + 1] = {'bottom_z': round(zb, 1), 'material': mat, 'jammed_gap': [round(x1, 1), round(a1, 1)] if jam else None}
    report['shutters'] = info


# ------------------------------------------------------------------------------------------------ floor and wall bands
def floor(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    uv = {'top': {'tile': [40.0, 40.0]}}
    if CAL:
        cands = ['w/fah_marble_floor_01_black', 'w/rubber_tile_bumper_car_floor', 'w/stone_floor_tiles_01', 'w/t7_brick_herringbone_dirty_02',
                 'w/clk_rubber_tiles', 'w/concrete_floor_polished_01']
        step = (cx1 - cx0) / len(cands)
        for k, mat in enumerate(cands):
            box(m, [cx0 + k * step, cy0, 0.0, cx0 + (k + 1) * step, cy1, 1.0], mat, id='floor_cal_%d' % k, uv=uv)
        report['floor_candidates'] = cands
    else:
        box(m, [cx0, cy0, 0.0, cx1, cy1, 1.0], A.FLOOR_SKIN, id='floor_tile', uv=uv)
    for k, (y0, y1) in enumerate(((cy0, cy0 + 26.0), (cy1 - 26.0, cy1))):           # the dark border
        box(m, [cx0, y0, 0.0, cx1, y1, 1.5], 'w/fac_tile_black_01', id='floor_border_%d' % k, uv={'top': {'tile': [32.0, 32.0]}})
    for k, yc in enumerate(((cy0 + 3850.0) / 2.0, (3950.0 + cy1) / 2.0)):          # the orange inlay line down each lane
        box(m, [cx0, yc - 5.0, 0.0, cx1, yc + 5.0, 1.6], 'w/plastic_slick_floor_01_orange', id='inlay_%d' % k, uv={'top': {'tile': [24.0, 24.0]}})
    for k in range(5):
        a0, a1 = A.aperture(k)
        box(m, [a0, cy1 - 46.0, 1.0, a1, cy1 - 26.0, 1.6], 'w/fac_rubber_mat_black', id='mat_%d' % (k + 1))
    report['floor'] = {'skin': 'cal' if CAL else A.FLOOR_SKIN, 'slab': A.FLOOR}


def wall_bands(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    ap = [A.aperture(i) for i in range(5)]
    # north wall: only the piers (the apertures are open)
    segs_n = []
    x = cx0
    for a0, a1 in ap:
        segs_n.append((x, a0 - 8.0))
        x = a1 + 8.0
    segs_n.append((x, cx1))
    for k, (x0, x1) in enumerate(segs_n):
        if x1 - x0 < 8:
            continue
        box(m, [x0, cy1 - 2.0, 0.0, x1, cy1, 100.0], A.WALLBAND, id='band_n%d' % k, uv={'south': {'tile': [64.0, 64.0]}})
        box(m, [x0, cy1 - 4.0, 0.0, x1, cy1 - 2.0, 40.0], DARKMETAL, id='wain_n%d' % k)
        box(m, [x0, cy1 - 5.0, 0.0, x1, cy1 - 2.0, 6.0], BLACK, id='kick_n%d' % k)
        box(m, [x0, cy1 - 5.0, 40.0, x1, cy1 - 2.0, 44.0], RUBBER, id='bump_n%d' % k)
        box(m, [x0, cy1 - 4.0, 100.0, x1, cy1 - 2.0, 104.0], BLACK, id='rail_n%d' % k)
    # south wall: whole length: the wall band (the calibration run: five candidates), the wainscot, the kick plate
    if CAL:
        cands = ['w/concrete_wall_01_stained', 'w/concrete_wall_12_lined_dirty', 'w/plaster_wall_04_grey_dark_01', 'w/fac_tile_black_01', 'w/clk_concrete_bunker_dark']
        step = (cx1 - cx0) / 5.0
        for k, mat in enumerate(cands):
            box(m, [cx0 + k * step, cy0, 0.0, cx0 + (k + 1) * step, cy0 + 2.0, 100.0], mat, id='band_s%d' % k, uv={'north': {'tile': [64.0, 64.0]}})
        report['band_candidates'] = cands
    else:
        box(m, [cx0, cy0, 0.0, cx1, cy0 + 2.0, 100.0], A.WALLBAND, id='band_s', uv={'north': {'tile': [64.0, 64.0]}})
    box(m, [cx0, cy0 + 2.0, 0.0, cx1, cy0 + 4.0, 40.0], DARKMETAL, id='wain_s')
    box(m, [cx0, cy0 + 2.0, 0.0, cx1, cy0 + 5.0, 6.0], BLACK, id='kick_s')
    box(m, [cx0, cy0 + 2.0, 40.0, cx1, cy0 + 5.0, 44.0], RUBBER, id='bump_s')
    box(m, [cx0, cy0 + 2.0, 100.0, cx1, cy0 + 4.0, 104.0], BLACK, id='rail_s')
    # pilasters: one on every pier of the north wall, three between the south fronts (render only, 10 proud)
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        w = 40.0 if b - a > 60.0 else 28.0
        box(m, [mid - w / 2.0, cy1 - 10.0, 0.0, mid + w / 2.0, cy1, 232.0], 'w/concrete_wall_panel_01', id='pil_n%d' % k)
        box(m, [mid - w / 2.0 - 2.0, cy1 - 12.0, 0.0, mid + w / 2.0 + 2.0, cy1, 12.0], BLACK, id='pil_nb%d' % k)
        box(m, [mid - w / 2.0 - 2.0, cy1 - 12.0, 220.0, mid + w / 2.0 + 2.0, cy1, 232.0], BLACK, id='pil_nc%d' % k)
        foot(D, mid - w / 2.0, cy1 - 12.0, mid + w / 2.0, cy1)
    for k, x in enumerate((-2530.0, -2176.0, -1900.0)):
        box(m, [x - 20.0, cy0, 0.0, x + 20.0, cy0 + 10.0, 232.0], 'w/concrete_wall_panel_01', id='pil_s%d' % k)
        box(m, [x - 22.0, cy0, 0.0, x + 22.0, cy0 + 12.0, 12.0], BLACK, id='pil_sb%d' % k)
        box(m, [x - 22.0, cy0, 220.0, x + 22.0, cy0 + 12.0, 232.0], BLACK, id='pil_sc%d' % k)
        foot(D, x - 22.0, cy0, x + 22.0, cy0 + 12.0)
    # the grime line where the wall meets the floor: dark, ragged strips on the floor along both walls
    rng = random.Random(21)
    x = cx0 + 30.0
    k = 0
    while x < cx1 - 60.0:
        w = rng.uniform(60.0, 160.0)
        box(m, [x, cy0 + 5.0, 0.0, min(x + w, cx1), cy0 + 5.0 + rng.uniform(5.0, 12.0), 1.7], 'w/fac_rubber_mat_black', id='grime_s%d' % k)
        box(m, [x + rng.uniform(0.0, 40.0), cy1 - 5.0 - rng.uniform(5.0, 12.0), 0.0, min(x + w, cx1), cy1 - 5.0, 1.7], 'w/fac_rubber_mat_black', id='grime_n%d' % k)
        x += w + rng.uniform(30.0, 120.0)
        k += 1


# ------------------------------------------------------------------------------------------------ the south wall's fronts, D4, D7, the ceiling
def fronts_and_doors(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    heads = ('w/plaster_wall_04_grey_dark_01', 'w/plaster_wall_04_grey_dark_02', 'w/plaster_wall_04_grey_dark_01')
    for k, (x0, x1) in enumerate(FRONTS):
        yv = cy0
        box(m, [x0 - 6.0, yv, 0.0, x1 + 6.0, yv + 5.0, 134.0], BLACK, id='front_frame_%d' % k)
        B.box(m, [x0, yv + 5.0, 0.0, x1, yv + 9.0, 124.0], A.SHUTTER, id='front_shutter_%d' % k)
        box(m, [x0 - 6.0, yv, 134.0, x1 + 6.0, yv + 8.0, 168.0], heads[k], id='front_header_%d' % k)
        box(m, [x0, yv + 8.0, 140.0, x1, yv + 9.0, 160.0], 'w/metal_painted_04', id='front_sign_dead_%d' % k)
    hx0, hx1 = HATCH
    box(m, [hx0 - 8.0, cy0, 0.0, hx1 + 8.0, cy0 + 8.0, 112.0], BLACK, id='hatch_frame')
    box(m, [hx0, cy0 + 8.0, 44.0, hx1, cy0 + 10.0, 100.0], DARKMETAL, id='hatch_dark')
    B.box(m, [hx0 - 8.0, cy0 + 8.0, 40.0, hx1 + 8.0, cy0 + 30.0, 46.0], 'w/wood_antique_panel_trim_01', id='hatch_sill')
    for k, bb in enumerate(([cx1 - 4.0, A.DOOR_Y0 - 8.0, 0.0, cx1, A.DOOR_Y0, A.DOOR_Z + 8.0], [cx1 - 4.0, A.DOOR_Y1, 0.0, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0],
                            [cx1 - 4.0, A.DOOR_Y0 - 8.0, A.DOOR_Z, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0])):
        box(m, bb, BLACK, id='d4_frame_%d' % k)
    box(m, [cx1 - 8.0, A.DOOR_Y0, A.DOOR_Z - 20.0, cx1 - 4.0, A.DOOR_Y1, A.DOOR_Z - 4.0], 'w/metal_painted_scratched_yellow', id='d4_stripe')
    xw = cx0
    zt = 176.0
    box(m, [xw, 3774.0, 0.0, xw + 14.0, 3794.0, zt + 12.0], BLACK, id='d7_post_l')
    box(m, [xw, 4006.0, 0.0, xw + 14.0, 4026.0, zt + 12.0], BLACK, id='d7_post_r')
    box(m, [xw, 3774.0, zt, xw + 14.0, 4026.0, zt + 12.0], BLACK, id='d7_head')
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 4006.0, zt], DARKMETAL, id='d7_slab')
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 12.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    box(m, [xw + 10.0, 3790.0, 88.0, xw + 13.0, 4010.0, 96.0], 'w/metal_painted_scratched_yellow_02', id='d7_band')
    for k, y in enumerate((3808.0, 3900.0, 3992.0)):
        box(m, [xw + 10.0, y - 3.0, 150.0, xw + 13.0, y + 3.0, 156.0], 'w/metal_painted_02', id='d7_bolt_%d' % k)
    box(m, [xw + 10.0, 3880.0, 40.0, xw + 12.0, 3920.0, 70.0], 'w/metal_painted_scratched_yellow_02', id='d7_plate')
    # the sign box over every shop front (render only): a black frame and an emissive face in the shop's hue
    for k in range(5):
        a0, a1 = A.aperture(k)
        box(m, [a0 - 14.0, cy1 - 16.0, 214.0, a1 + 14.0, cy1, 232.0], BLACK, id='beam_%d' % (k + 1))
        box(m, [a0, cy1 - 12.0, 150.0, a1, cy1, 190.0], BLACK, id='sign_frame_%d' % (k + 1))
        hue = HUE[A.BAYS[k]]
        B.sign(m, at=((a0 + a1) / 2.0, cy1 - 12.0, 170.0), normal=(0.0, -1.0, 0.0), size=(a1 - a0 - 8.0, 32.0), text=NAMES[A.BAYS[k]], font='impact',
               color=[min(1.0, 0.35 + 0.65 * c) for c in hue], background=[0.02, 0.02, 0.03], emissive={'color': list(hue), 'strength': 2.2}, id='sign_text_%d' % (k + 1))


def ceiling(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    rows = [3590.0, 3745.0, 4055.0, 4210.0]                     # the middle row (y 3900) is the soffit's
    cols = [A.X0 + 100.0 + 118.0 * i for i in range(15)]
    live = {(3745.0, 13), (3745.0, 14), (4055.0, 13), (4055.0, 14),         # the east entry
            (3745.0, 6), (3745.0, 7), (4055.0, 6), (4055.0, 7),             # mid hall
            (3745.0, 0), (3745.0, 1), (4055.0, 0),                          # the west end
            (3745.0, 10)}                                                   # the single between them
    rng = random.Random(11)
    cells = [(y, ci, x) for y in rows for ci, x in enumerate(cols)]
    dead = [c for c in cells if (c[0], c[1]) not in live]
    rng.shuffle(dead)
    missing = {(c[0], c[1]) for c in dead[:8]}
    A.live, A.missing = [], []
    for (y, ci, x) in cells:
        if (y, ci) in missing:
            A.missing.append((x, y))
            continue
        on = (y, ci) in live
        box(m, [x - 40.0, y - 14.0, 178.0, x + 40.0, y + 14.0, 182.0], A.PANEL_LIVE if on else A.PANEL_DEAD, id='panel_%d_%d' % (int(y), ci))
        if on:
            A.live.append((x, y, (y, ci) == (3745.0, 10)))
    for ri, y in enumerate(rows):
        box(m, [cx0, y - 18.0, 183.0, cx1, y - 15.0, 188.0], BLACK, id='panel_rail_a_%d' % ri)
        box(m, [cx0, y + 15.0, 183.0, cx1, y + 18.0, 188.0], BLACK, id='panel_rail_b_%d' % ri)
    A.panels = len(cells) - len(A.missing)
    # the dropped soffit over the spine, 48 deep, with a black lip
    box(m, [cx0, SPINE_Y - 36.0, 208.0, cx1, SPINE_Y + 36.0, 256.0], 'w/plaster_wall_04_grey_dark_01', id='soffit')
    box(m, [cx0, SPINE_Y - 38.0, 204.0, cx1, SPINE_Y - 36.0, 256.0], BLACK, id='soffit_lip_s')
    box(m, [cx0, SPINE_Y + 36.0, 204.0, cx1, SPINE_Y + 38.0, 256.0], BLACK, id='soffit_lip_n')
    report['panels'] = {'cells': len(cells), 'missing': len(A.missing), 'live': len(A.live)}


# ------------------------------------------------------------------------------------------------ the spine: columns and islands
def spine(A, m, D, report):
    m.use('dressing')
    cols = list(COLS)
    dropped = []
    if os.environ.get('ARC3_DROP_LAST'):
        dropped = [cols.pop()]
    for k, x in enumerate(cols):
        B.column(m, (x, SPINE_Y), 0.0, 256.0, 32.0, 'w/concrete_wall_01_stained', id='col_%d' % k)
        box(m, [x - 20.0, SPINE_Y - 20.0, 0.0, x + 20.0, SPINE_Y + 20.0, 48.0], BLACK, id='col_plinth_%d' % k)
        box(m, [x - 18.0, SPINE_Y - 18.0, 56.0, x + 18.0, SPINE_Y + 18.0, 64.0], RUBBER, id='col_bumper_%d' % k)
        box(m, [x - 19.0, SPINE_Y - 19.0, 200.0, x + 19.0, SPINE_Y + 19.0, 208.0], BLACK, id='col_cap_%d' % k)
        foot(D, x - 20.0, SPINE_Y - 20.0, x + 20.0, SPINE_Y + 20.0)
    report['columns'] = {'placed': cols, 'dropped': dropped}

    def hang(x, mod, yaw, z_bar=168.0, w=84.0, dz=0.0):
        """a sign bar hung from the soffit by two rods, a stock sign hanging from it"""
        box(m, [x - w / 2.0, SPINE_Y - 1.5, z_bar, x + w / 2.0, SPINE_Y + 1.5, z_bar + 3.0], BLACK, id='bar_%d' % int(x))
        for s in (-1, 1):
            box(m, [x + s * (w / 2.0 - 4.0) - 1.0, SPINE_Y - 1.0, z_bar + 3.0, x + s * (w / 2.0 - 4.0) + 1.0, SPINE_Y + 1.0, 208.0], BLACK, id='rod_%d_%d' % (int(x), s))
        mn, mx = D.bounds(M.get(mod, mod))
        h = mx[2] - mn[2]
        D.put(M.get(mod, mod), x, SPINE_Y, yaw, z=z_bar - h + 6.0 + dz, ignore_keep=True, margin=0.0)

    # (ii) the kiosk at the first gap: a 96 x 64 booth, a counter, a canopy, a lit sign box
    kx = GAPS[0]
    x0, x1, y0, y1 = kx - 48.0, kx + 48.0, SPINE_Y - 32.0, SPINE_Y + 32.0
    B.box(m, [x0, y0, 0.0, x1, y1, 44.0], 'w/wood_worn_painted_01_green', id='kiosk_base')
    box(m, [x0 - 2.0, y0 - 2.0, 44.0, x1 + 2.0, y1 + 2.0, 47.0], 'w/wood_antique_panel_trim_01', id='kiosk_counter')
    for k, (px, py) in enumerate(((x0, y0), (x1 - 4.0, y0), (x0, y1 - 4.0), (x1 - 4.0, y1 - 4.0))):
        box(m, [px, py, 47.0, px + 4.0, py + 4.0, 100.0], BLACK, id='kiosk_post_%d' % k)
    box(m, [x0, y1 - 3.0, 47.0, x1, y1, 100.0], DARKMETAL, id='kiosk_back_n')
    box(m, [x0, y0, 47.0, x1, y0 + 3.0, 100.0], DARKMETAL, id='kiosk_back_s')
    box(m, [x0 - 8.0, y0 - 8.0, 100.0, x1 + 8.0, y1 + 8.0, 106.0], 'w/metal_painted_scratched_yellow', id='kiosk_canopy')
    box(m, [x0 + 4.0, y0 - 6.0, 106.0, x1 - 4.0, y0 - 4.0, 124.0], TUBE['heel'], id='kiosk_sign_s')
    box(m, [x0 + 4.0, y1 + 4.0, 106.0, x1 - 4.0, y1 + 6.0, 124.0], TUBE['heel'], id='kiosk_sign_n')
    box(m, [x0 + 4.0, y0 - 7.0, 105.0, x1 - 4.0, y1 + 7.0, 106.0], BLACK, id='kiosk_sign_base')
    D.tops['kiosk'] = (kx, SPINE_Y, 47.0, 96.0, 64.0, 0.0)
    foot(D, x0 - 8.0, y0 - 8.0, x1 + 8.0, y1 + 8.0)
    D.put(M['news'], kx - 72.0, SPINE_Y - 12.0, 0.0, tag='kiosk_news_a', margin=0.0)
    D.put(M['news'], kx - 72.0, SPINE_Y + 18.0, 0.0, tag='kiosk_news_b', margin=0.0)
    D.put(M['news'], kx + 72.0, SPINE_Y + 4.0, 180.0, tag='kiosk_news_c', margin=0.0)
    for k, (mod, du, dv, yw) in enumerate((('register', -22.0, 14.0, 270.0), ('coffee', 14.0, 16.0, 270.0), ('mags', 28.0, -14.0, 20.0), ('stackp', -10.0, -14.0, 60.0),
                                           ('mug', 30.0, 10.0, 0.0), ('mags', -34.0, -12.0, 100.0))):
        D.put(M[mod], kx + du, SPINE_Y + dv, yw, z=47.0, ignore_keep=True, margin=0.0)
    hang(kx, 'sign1', 0.0)
    # (i) two subway benches back to back with a bin
    bx = GAPS[1]
    D.put(M['bench'], bx, SPINE_Y - 21.0, 90.0, tag='bench_a', margin=0.0)
    D.put(M['bench'], bx, SPINE_Y + 21.0, 270.0, tag='bench_b', margin=0.0)
    D.put(M['bin1'], bx - 118.0, SPINE_Y, 0.0, tag='bin_i', margin=0.0)
    for j, mod in enumerate(('paper', 'cup', 'mags', 'cup')):
        D.put(M[mod], bx + (j - 1.5) * 40.0, SPINE_Y + (-21.0 if j % 2 == 0 else 21.0), D.rng.uniform(0, 360), on='bench_a' if j % 2 == 0 else 'bench_b', margin=0.0)
    hang(bx, 'sign2', 90.0)
    # (iii) a planter box 120 x 40 with dead plants and litter
    px = GAPS[2]
    B.box(m, [px - 60.0, SPINE_Y - 20.0, 0.0, px + 60.0, SPINE_Y + 20.0, 34.0], 'w/concrete_wall_01_stained', id='planter_box')
    box(m, [px - 62.0, SPINE_Y - 22.0, 34.0, px + 62.0, SPINE_Y + 22.0, 38.0], BLACK, id='planter_rim')
    box(m, [px - 56.0, SPINE_Y - 16.0, 38.0, px + 56.0, SPINE_Y + 16.0, 39.0], 'w/dirt_stain_leaking_01', id='planter_soil')
    foot(D, px - 62.0, SPINE_Y - 22.0, px + 62.0, SPINE_Y + 22.0)
    D.tops['planter'] = (px, SPINE_Y, 39.0, 120.0, 40.0, 0.0)
    for j, du in enumerate((-40.0, 0.0, 40.0)):
        D.put(M['plant'], px + du, SPINE_Y + (4.0 if j % 2 else -4.0), D.rng.uniform(0, 360), z=39.0, ignore_keep=True, margin=0.0)
    for j in range(5):
        D.put(D.rng.choice((M['cup'], M['chips'], M['paper'], M['smokes'], M['can'])), px + D.rng.uniform(-80.0, 80.0), SPINE_Y + D.rng.uniform(-34.0, 34.0), D.rng.uniform(0, 360), margin=0.0)
    hang(px, 'sign4', 90.0)
    # (iv) a pay phone pair on the column at x = -1950 (back to back), a transit map case and a newspaper box beside it
    cxp = COLS[3]
    D.put(M['phone'], cxp + 16.0 + 13.0, SPINE_Y, 0.0, tag='ph_e', margin=0.0)
    D.put(M['phone'], cxp - 16.0 - 13.0, SPINE_Y, 180.0, tag='ph_w', margin=0.0)
    D.put(M['case'], GAPS[3], SPINE_Y, 0.0, tag='mapcase_i', margin=0.0)
    D.put(M['news'], GAPS[3] + 60.0, SPINE_Y - 16.0, 180.0, tag='news_iv', margin=0.0)
    D.put(M['bin2'], GAPS[3] - 60.0, SPINE_Y + 14.0, 0.0, tag='bin_iv', margin=0.0)
    # (v) the floor buffer with wet floor signs and a cable
    fx = GAPS[4]
    D.put(M['buffer'], fx, SPINE_Y, 20.0, tag='buffer', margin=0.0)
    D.put(M['wet'], fx - 70.0, SPINE_Y - 22.0, 30.0, tag='wet_a', margin=0.0)
    D.put(M['wet'], fx + 70.0, SPINE_Y + 24.0, 200.0, tag='wet_b', margin=0.0)
    D.put(M['mop'], fx + 40.0, SPINE_Y + 30.0, 80.0, tag='mop', margin=0.0)
    pts = [(fx + 28.0, SPINE_Y - 4.0), (fx + 60.0, SPINE_Y - 30.0), (fx + 110.0, SPINE_Y - 22.0), (fx + 140.0, SPINE_Y + 20.0), (fx + 190.0, SPINE_Y + 40.0)]
    for k in range(len(pts) - 1):
        (ax, ay), (bx2, by2) = pts[k], pts[k + 1]
        box(m, [min(ax, bx2) - 1.5, min(ay, by2) - 1.5, 0.0, max(ax, bx2) + 1.5, max(ay, by2) + 1.5, 3.0], 'w/fac_rubber_mat_black', id='cable_%d' % k)
    hang(fx, 'sign4', 90.0, z_bar=172.0)


# ------------------------------------------------------------------------------------------------ the wall furniture
def wall_props(A, m, D):
    # south wall west to east
    for k, x in enumerate((-2955.0, -2918.0)):
        D.wall(M['soda'], 's', x, tag='vend%d' % k)
    for k in range(4):
        D.wall(M['phone'], 's', -2840.0 + 34.0 * k, tag='phone%d' % k)
    D.wall(M['steel'], 's', -2165.0, tag='lp_sh1')
    D.wall(M['steel'], 's', -1995.0, tag='lp_sh2')
    for k in range(3):
        D.wall(M['locker'], 's', -2310.0 - 20.0 * k, tag='lock%d' % k)
    D.wall(M['case'], 's', -1640.0, tag='mapcase')
    D.wall(M['bin1'], 's', -2700.0, tag='bin_s0')
    D.wall(M['bin2'], 's', -2060.0, tag='bin_s1')
    D.wall(M['bin1'], 's', -1560.0, tag='bin_s2')
    D.wall(M['news'], 's', -2670.0, tag='news_s0')
    D.wall(M['turn'], 's', -1275.0, tag='turn0')
    D.wall(M['turn'], 's', -1240.0, tag='turn1')
    D.wall(M['bench'], 's', -2350.0, tag='bench_s0')
    D.wall(M['bench'], 's', -1960.0, tag='bench_s1')
    D.wall(M['wet'], 's', -2330.0, tag='wet_s')
    # north piers
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        if k in (1, 3, 4):
            D.wall(M['news'], 'n', mid - 20.0, tag='pier_news%da' % k)
            D.wall(M['news'], 'n', mid + 22.0, tag='pier_news%db' % k)
        if k in (0, 2):
            D.wall(M['bin1'], 'n', mid, tag='pier_bin%d' % k)
        if k == 2:
            D.wall(M['phone'], 'n', mid + 28.0, tag='pier_phone')
    D.wall(M['bin2'], 'n', -1250.0, tag='pier_bin5')
    D.wall(M['news'], 'n', -1330.0, tag='pier_news5')
    # the two caged wall lamps of the south wall (over the wall buys)
    for k, x in enumerate((-2560.0, -1860.0)):
        D.put(M['lamp'], x, A.Y0 + A.WT + 8.0, 90.0, z=140.0, scale=3.0, ignore_keep=True, margin=0.0, emissive={'color': [1.0, 0.72, 0.38], 'strength': 4.0})
        box(m, [x - 10.0, A.Y0 + A.WT, 128.0, x + 10.0, A.Y0 + A.WT + 4.0, 160.0], BLACK, id='lamp_plate_%d' % k)
    # the wall decals: stains (few and large, near the walls) and a pair of old bills on the south wall
    for k in range(10):
        x = A.X0 + 120.0 + k * 170.0
        wy = (A.Y0 + A.WT + 30.0) if k % 2 == 0 else (A.Y1 - A.WT - 40.0)
        B.decal(m, 'w/asphalt_flooring_stain_01' if k % 3 else 'w/fac_darkstain_01_dec', (x + D.rng.uniform(-30, 30), wy + D.rng.uniform(-8, 8), 1.8), (0.0, 0.0, 1.0), (110.0, 110.0), rot=D.rng.uniform(0, 360), id='decal_floor_%d' % k)
    for k in range(10):
        x = A.X0 + 80.0 + k * 175.0
        B.decal(m, ('w/plaster_damaged_11_crack_dec', 'w/dirt_stain_water_drips_01', 'w/wall_stain_01_dec')[k % 3], (x, A.Y0 + A.WT, D.rng.uniform(110.0, 170.0)), (0.0, 1.0, 0.0),
                (D.rng.uniform(50.0, 80.0), D.rng.uniform(50.0, 80.0)), id='decal_wall_%d' % k)


# ------------------------------------------------------------------------------------------------ one shop
def rod(m, id, x, y, z0, z1):
    box(m, [x - 0.6, y - 0.6, z0, x + 0.6, y + 0.6, z1], BLACK, id=id)


def hung_sheet(m, id, x, y, z, w, h, mat, rods=True, ceil=200.0):
    """a flat piece hung from the ceiling by a rod at each end (flat geometry carrying a poster or photo material)"""
    box(m, [x - w / 2.0, y - 0.4, z, x + w / 2.0, y + 0.4, z + h], mat, id=id)
    if rods:
        rod(m, id + '_ra', x - w / 2.0 + 1.0, y, z + h, ceil)
        rod(m, id + '_rb', x + w / 2.0 - 1.0, y, z + h, ceil)


def bay(A, m, D, i):
    s = A.BAY_X[i]
    yb = A.Y1
    kind = A.BAYS[i]
    wallb = yb + A.BAY_D - A.WT
    U = lambda u: s + u
    V = lambda v: yb + v
    yp = A.BACK_Y
    left, right = s + A.WT, s + A.BAY_W - A.WT
    hue = HUE[kind]
    brd = BOARD[kind]
    lv = (24.0, 46.0, 68.0, 90.0, 112.0, 134.0)
    box(m, [left, yb + A.WT, 0.0, left + 2.0, wallb, 8.0], BLACK, id='skirt_l_%d' % (i + 1))
    box(m, [right - 2.0, yb + A.WT, 0.0, right, wallb, 8.0], BLACK, id='skirt_r_%d' % (i + 1))
    # tall shelving along the whole back wall (partition), two units either side of the walk-in doorway
    items = {'photo': (['boxc', 'crackers', 'mags', 'crackers', 'paper', 'books'], ['crackers', 'boxc', 'paper', 'mags', 'crackers', 'books']),
             'heel': (['shoes', 'shoes', 'boxc', 'shoes', 'shoes', 'boxc'], ['shoes', 'boxc', 'shoes', 'shoes', 'boxc', 'shoes']),
             'hole9': (['crackers', 'donuts', 'mug', 'crackers', 'donuts', 'mug'], ['donuts', 'crackers', 'mug', 'donuts', 'crackers', 'boxc']),
             'copy': (['ream', 'stack', 'ream', 'books', 'ream', 'stack'], ['ream', 'ream', 'books', 'stack', 'ream', 'boxa']),
             'needle': (['sleeve', 'sleeve', 'crate', 'sleeve', 'sleeve', 'crate'], ['sleeve', 'crate', 'sleeve', 'sleeve', 'crate', 'sleeve'])}[kind]
    step = {'photo': 15.0, 'heel': 14.0, 'hole9': 15.0, 'copy': 16.0, 'needle': 8.0}[kind]
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        sh = R2.Shelf(m, 'shelf_p%d_%d' % (side, i), (U(u0), yp - 32.0, U(u1), yp), 's', lv, board=brd, top=148.0)
        R2.stock(D, sh, items[side], step, yaw=270.0, jitter=14.0, skip=0.1)
    # one side shelf (not where the perk or the wheel stands)
    if kind in ('heel', 'hole9', 'needle'):
        sh = R2.Shelf(m, 'shelf_l_%d' % i, (left, V(40.0), left + 30.0, V(148.0)), 'e', lv[:4], board=brd, top=96.0)
        R2.stock(D, sh, {'heel': ['shoes', 'boxc'], 'hole9': ['crackers', 'mug', 'donuts'], 'needle': ['crate', 'sleeve', 'sleeve']}[kind], 16.0, yaw=0.0, jitter=10.0, skip=0.1)
    else:
        sh = R2.Shelf(m, 'shelf_r_%d' % i, (right - 30.0, V(40.0), right, V(148.0)), 'w', lv[:4], board=brd, top=96.0)
        R2.stock(D, sh, ['boxc', 'paper', 'mags'] if kind == 'photo' else ['ream', 'stack', 'books'], 16.0, yaw=180.0, jitter=10.0, skip=0.1)
    # the counters: a plain one with a register, and a glass display counter with lit contents
    R2.counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), body=BODY[kind], tag='ctr_a%d' % i)
    R2.on_counter(D, 'ctr_a%d' % i, 'register', -14.0, 0.0, 270.0)
    R2.on_counter(D, 'ctr_a%d' % i, 'stack' if kind != 'hole9' else 'mug', 14.0, 0.0, 20.0)
    R2.counter(m, D, 'ctr2_%d' % i, U(208.0), V(24.0), U(270.0), V(54.0), body=BODY[kind], tag='ctr_b%d' % i)
    gx0, gx1, gy0, gy1 = U(208.0), U(270.0), V(24.0), V(54.0)
    box(m, [gx0, gy0, 44.0, gx1, gy1, 46.0], BLACK, id='glass_base_%d' % i)
    for k, (px, py) in enumerate(((gx0, gy0), (gx1 - 2.0, gy0), (gx0, gy1 - 2.0), (gx1 - 2.0, gy1 - 2.0))):
        box(m, [px, py, 46.0, px + 2.0, py + 2.0, 62.0], BLACK, id='glass_post_%d_%d' % (i, k))
    box(m, [gx0, gy0, 60.0, gx1, gy1, 62.0], 'w/glass_clear_generic_01', id='glass_top_%d' % i)
    box(m, [gx0, gy0, 46.0, gx1, gy0 + 1.0, 60.0], 'w/glass_clear_generic_01', id='glass_front_%d' % i)
    box(m, [gx0, gy1 - 1.0, 46.0, gx1, gy1, 60.0], 'w/glass_clear_generic_01', id='glass_back_%d' % i)
    box(m, [gx0 + 2.0, gy0 + 2.0, 57.0, gx1 - 2.0, gy1 - 2.0, 59.0], TUBE[kind], id='glass_light_%d' % i)
    disp = {'photo': ['mags', 'paper', 'mags'], 'heel': ['shoes', 'shoes', 'hammer'], 'hole9': ['donuts', 'donuts', 'mug'], 'copy': ['stack', 'ream', 'books'],
            'needle': ['sleeve', 'sleeve', 'sleeve']}[kind]
    for k, mod in enumerate(disp):
        R2.on_counter(D, 'ctr_b%d' % i, mod, -16.0 + 16.0 * k, 0.0, 90.0 * k)
    # the sign box of the shop's hue was drawn in the corridor geometry; hanging objects behind the aperture (rods to the ceiling at 200)
    cx = s + A.BAY_W / 2.0
    hy = V(44.0)
    if kind == 'photo':
        for k in range(9):
            hung_sheet(m, 'hg_%d_%d' % (i, k), cx - 100.0 + 25.0 * k, hy + (6.0 if k % 2 else 0.0), 58.0 + (6.0 if k % 2 else 0.0), 11.0, 22.0, ('w/zombies_blank_photo', 'w/zombies_teddy_photo')[k % 2])
    elif kind == 'heel':
        box(m, [cx - 22.0, hy, 58.0, cx + 22.0, hy + 2.0, 82.0], TUBE['heel'], id='shoe_sign_%d' % i)
        box(m, [cx - 6.0, hy - 1.0, 62.0, cx + 2.0, hy + 2.5, 78.0], BLACK, id='shoe_leg_%d' % i)
        box(m, [cx - 14.0, hy - 1.0, 62.0, cx + 2.0, hy + 2.5, 68.0], BLACK, id='shoe_foot_%d' % i)
        rod(m, 'shoe_ra_%d' % i, cx - 20.0, hy, 82.0, 200.0)
        rod(m, 'shoe_rb_%d' % i, cx + 20.0, hy, 82.0, 200.0)
        for q, ux in enumerate((-90.0, 90.0)):            # key boards: a green board with hooks
            box(m, [cx + ux - 22.0, hy + 4.0, 56.0, cx + ux + 22.0, hy + 5.5, 86.0], 'w/wood_worn_painted_01_green', id='keyboard_%d_%d' % (i, q))
            rod(m, 'kb_ra_%d_%d' % (i, q), cx + ux - 20.0, hy + 4.0, 86.0, 200.0)
            rod(m, 'kb_rb_%d_%d' % (i, q), cx + ux + 20.0, hy + 4.0, 86.0, 200.0)
            for k in range(8):
                D.put(M['hook'], cx + ux - 18.0 + 5.0 * k, hy + 4.0, 270.0, z=60.0 + 12.0 * (k % 2) + 8.0, scale=2.5, ignore_keep=True, margin=0.0)
    elif kind == 'hole9':
        for k in range(5):
            hung_sheet(m, 'hg_%d_%d' % (i, k), cx - 90.0 + 45.0 * k, hy + (5.0 if k % 2 else 0.0), 52.0, 30.0, 26.0, 'w/signage_theater_menu_01')
    elif kind == 'copy':
        for k in range(6):
            hung_sheet(m, 'hg_%d_%d' % (i, k), cx - 100.0 + 40.0 * k, hy + (6.0 if k % 2 else 0.0), 50.0 + (8.0 if k % 2 else 0.0), 26.0, 22.0, 'w/zombies_underground_map')
    else:
        for k in range(14):
            hung_sheet(m, 'hg_%d_%d' % (i, k), cx - 104.0 + 16.0 * k, hy + (6.0 if k % 2 else 0.0), 54.0 + 8.0 * (k % 3), 12.0, 12.0, ('w/zombies_theater_poster01', 'w/zombies_theater_poster02', 'w/signage_zmb_park_poster_03')[k % 3])
    # posters on both side walls
    for k, (zz, vv) in enumerate(((84.0, 60.0), (76.0, 118.0))):
        B.decal(m, POSTERS[(i + k) % len(POSTERS)], (left, V(vv), zz), (1.0, 0.0, 0.0), (26.0, 36.0), id='post_l_%d_%d' % (i, k))
        B.decal(m, POSTERS[(i + k + 2) % len(POSTERS)], (right, V(vv + 10.0), zz), (-1.0, 0.0, 0.0), (26.0, 36.0), id='post_r_%d_%d' % (i, k))
    # per-shop extras that carry the shop's name (perk, wheel stay clear)
    if kind == 'photo':
        for k, u0 in enumerate((214.0, 258.0)):
            pass
    if kind == 'needle':
        D.wall(M['juke'], ['x', right, -1], V(110.0), tag='juke') if False else None
        for k in range(6):
            D.put(M['crate'], U(228.0 + 22.0 * (k % 3)), V(110.0 + 22.0 * (k // 3)), D.rng.uniform(-10.0, 10.0), tag='crate%d_%d' % (i, k), margin=1.0)
    if kind == 'copy':
        D.wall(M['computer'], ['x', right, -1], V(110.0), tag='cop3')
        D.wall(M['file'], ['x', right, -1], V(70.0), tag='file1')
    if kind == 'heel':
        D.wall(M['rack'], ['x', right, -1], V(100.0), tag='rack_%d' % i)
    # the back room: dark: a steel shelf, a crate, a bag
    D.wall(M['steel'], ('y', wallb, -1), U(160.0), tag='bshelf%d' % i)
    D.on('bshelf%d' % i, M['boxc'], -12.0, 0.0, 90.0)
    D.on('bshelf%d' % i, M['bag'], 12.0, 0.0, 40.0)


# ------------------------------------------------------------------------------------------------ litter, ceiling props
def litter(A, D):
    kinds = [M['bag'], M['chips'], M['cup'], M['paper'], M['can'], M['pile'], M['smokes']]
    anchors = [D.tops[t] for t in list(D.tops) if t.startswith(('bin_', 'pier_bin', 'bench_', 'news_', 'pier_news', 'vend', 'phone', 'turn', 'lock', 'planter', 'kiosk_news'))]
    D.rng.shuffle(anchors)
    for (x, y, _top, w, d, _yaw) in anchors:
        for _ in range(D.rng.randint(2, 3)):
            ang = D.rng.uniform(0.0, 6.283)
            r = max(w, d) / 2.0 + D.rng.uniform(6.0, 26.0)
            D.put(D.rng.choice(kinds), x + math.cos(ang) * r, y + math.sin(ang) * r, D.rng.uniform(0.0, 360.0), margin=1.5)
        if D.n > PROP_CAP - 60:
            break
    for _ in range(16):                              # drifts along the foot of the walls
        wall_y = (A.Y0 + A.WT + 14.0) if D.rng.random() < 0.55 else (A.Y1 - A.WT - 60.0)
        x = D.rng.uniform(A.X0 + 40.0, A.X1 - 40.0)
        for _k in range(D.rng.randint(1, 3)):
            D.put(D.rng.choice(kinds), x + D.rng.uniform(-18.0, 18.0), wall_y + D.rng.uniform(0.0, 14.0), D.rng.uniform(0.0, 360.0), margin=1.5)


def ceiling_props(A, D):
    k = 0
    for line, y in enumerate((3640.0, 4180.0)):
        x = A.X0 + 80.0
        while x < A.X1 - 80.0:
            D.ceil(M['pipe'], x, y, 90.0, 236.0)
            x += 128.0
            k += 1
    x = A.X0 + 100.0
    while x < A.X1 - 90.0:
        D.ceil(M['duct'], x, 3822.0, 90.0, 230.0)
        x += 256.0
    for j, (x, y) in enumerate(A.missing):
        D.ceil(M['wire'] if j % 2 else M['wire2'], x, y, 0.0, 208.0)


def d7_props(A, D):
    xw = A.X0 + A.WT
    D.put(M['valve'], xw + 14.0, 3790.0, 90.0, z=60.0, ignore_keep=True, margin=0.0)
    D.put(M['warn'], xw + 4.0, 3764.0, 0.0, z=100.0, ignore_keep=True, margin=0.0)


# ------------------------------------------------------------------------------------------------ light
def lights(A, m, report):
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, **k)
    yin = A.Y1 - A.WT
    for k, (x, y, single) in enumerate(A.live):                      # one tight spot under every live panel
        L((x, y, 176.0), color=(1.0, 0.93, 0.78), radius=170.0, intensity=round(POOL_I * (0.55 if single else 1.0), 3), type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    for i in range(5):
        hue = HUE[A.BAYS[i]]
        s = A.BAY_X[i]
        cx = s + A.BAY_W / 2.0
        L((s + 81.0, A.Y1 + 39.0, 176.0), color=(1.0, 0.88, 0.68), radius=220.0, intensity=KEY_I, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=58.0, id='light_key_%d' % (i + 1))
        for side, ux in enumerate((67.0, 253.0)):                    # two washes on the stock of the back wall
            wp = (s + ux, A.Y1 + 30.0, 176.0)
            wt = (s + ux, A.BACK_Y - 10.0, 74.0)
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(wp, wt)))
            d = [(wt[j] - wp[j]) / dist for j in range(3)]
            L(wp, color=tuple(round(0.5 + 0.5 * c, 3) for c in hue), radius=round(dist * 1.8, 1), intensity=round(WASH_I * (dist / 200.0) ** 2, 4), type='spot', dir=d, inner=12.0, outer=38.0,
              id='light_wash_%d_%d' % (i + 1, side))
        L((cx, A.Y1 + 34.0, 100.0), color=hue, radius=130.0, intensity=SPILL_I, id='light_spill_%d' % (i + 1))         # the sign's spill, INSIDE the shop
    for k, x in enumerate((-2560.0, -1860.0)):                       # the caged wall lamps
        L((x, A.Y0 + A.WT + 14.0, 146.0), color=(1.0, 0.78, 0.45), radius=150.0, intensity=0.35, type='spot', dir=(0.0, 0.3, -1.0), inner=16.0, outer=52.0, id='light_cage_%d' % k)
    L((A.X1 - 60.0, 3900.0, 170.0), color=(1.0, 0.85, 0.55), radius=170.0, intensity=0.25, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    L((A.X0 + 70.0, 4040.0, 150.0), color=(1.0, 0.80, 0.50), radius=180.0, intensity=0.5, type='spot', dir=(0.0, -0.2, -1.0), inner=16.0, outer=52.0, id='light_d7_cage')
    L((A.X1 + 100.0, 3900.0, 200.0), color=(0.9, 0.9, 1.0), radius=160.0, intensity=0.05, id='light_vest')
    report['lights'] = n
    assert n <= LIGHT_CAP, n


def counts(m, A):
    """props per rectangle: the corridor, each bay's shop room, the back rooms"""
    out = {'corridor': 0, 'back_rooms': 0, 'vestibule': 0}
    for i in range(5):
        out['bay%d' % (i + 1)] = 0
    for p in m.flat().props:
        x, y = p['origin'][0], p['origin'][1]
        if y < A.Y1:
            out['vestibule' if x > A.X1 else 'corridor'] += 1
        elif y >= A.BACK_Y:
            out['back_rooms'] += 1
        else:
            for i in range(5):
                if A.BAY_X[i] <= x < A.BAY_X[i] + A.BAY_W:
                    out['bay%d' % (i + 1)] += 1
    return out


def dress(A, m, stage='full', foreign=None):
    D = R2.D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    shutters(A, m, report)
    floor(A, m, D, report)
    wall_bands(A, m, D, report)
    fronts_and_doors(A, m, D, report)
    ceiling(A, m, D, report)
    spine(A, m, D, report)
    wall_props(A, m, D)
    for i in range(5):
        bay(A, m, D, i)
    d7_props(A, D)
    ceiling_props(A, D)
    litter(A, D)
    lights(A, m, report)
    if CAL:
        m.use('cameras')
        B.camera(m, 'cal_floor_w', (A.X0 + 50.0, 3900.0, 150.0), 0.0, pitch=35.0, id='cal_floor_w')
        B.camera(m, 'cal_floor_e', (A.X1 - 50.0, 3900.0, 150.0), 180.0, pitch=35.0, id='cal_floor_e')
        for k in range(6):
            B.camera(m, 'cal_f%d' % k, (A.X0 + A.WT + 293.0 * (k + 0.5), 3590.0, 110.0), 90.0, pitch=50.0, id='cal_f%d' % k)
        for k, x in enumerate((-2700.0, -2100.0, -1500.0)):
            B.camera(m, 'cal_wall%d' % (k + 1), (x, 3800.0, 70.0), 270.0, id='cal_wall%d' % (k + 1))
    m.use('cameras')
    for k in range(5):                                     # close cameras on the five shop signs
        a0, a1 = A.aperture(k)
        B.camera(m, 'sign_%d' % (k + 1), ((a0 + a1) / 2.0, 4090.0, 165.0), 90.0, id='sign_%d' % (k + 1))
    models = {p['model'] for p in m.flat().props}
    report['distinct_models'] = len(models)
    report.update({'props': D.n, 'by_area': counts(m, A), 'skipped': D.skipped, 'foreign_models': D.foreign, 'failed': D.failed[:60]})
    m.dress_report = report
    m.dresser = D
    assert len(models) <= MODEL_CAP, (len(models), sorted(models))
    return report
