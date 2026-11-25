"""arcade_dress4: the dressing and the light of the Underpass Arcade, round 4 (called by arcade4.build_arcade).

Round 3 went through a blind review (ours 4.70, stock 6.60): shop fronts black from the corridor, copy-pasted columns, an empty floor, bare walls, a bare ceiling.
Round 4 answers by weight:
  density   each shop is dressed with Studio's `P.dress_like` from a stock room (the back-wall run, tall stock shelves, is ours: the partition's face stays under half covered
            by dress_like), the corridor gets arcade cabinets, market stalls, carts, crate and barrel stacks, litter clusters and posters; no model cap, prop cap 2,600;
  surfaces  every surface from the vetted underpass list (arcade4.py);
  light     shops are the lit pockets: a wide warm key, a hue wash on the stock, an emissive light strip, a fill, and a spill on the corridor floor in front of the aperture;
            the shutters are rolled up to 20 to 35 % of the opening;
  columns    six different ones: material, wainscot, stripe, feature (poster boards, a fire cabinet, an advert light box, a subway map case);
  ceiling   cable trays, more duct and pipe runs, arrow pictogram signs (pictures, no words: any new text is the lead's).
Counters, shelves, signs, columns and islands are geometry.
"""
import math
import os
import random

import arcade_dress as R1
import arcade_dress2 as R2
import arcade_dress3 as R3
from studio import build as B, prefab as P

R1.PROP_CAP = 2600
LIGHT_CAP = 110
HUE, TUBE, M = R2.HUE, R2.TUBE, R2.M
BLACK, DARKMETAL, RUBBER = R3.BLACK, R3.DARKMETAL, R3.RUBBER
box = R2.box
SPINE_Y, COLS, GAPS, PIERS, FRONTS, HATCH = R3.SPINE_Y, R3.COLS, R3.GAPS, R3.PIERS, R3.FRONTS, R3.HATCH
POSTERS = R3.POSTERS + ['w/signage_theater_menu_01', 'w/zombies_theater_poster01', 'w/zombies_theater_poster02', 'w/signage_zmb_park_poster_03']
KEY_I = float(os.environ.get('ARC4_KEY', '1.5'))
WASH_I = float(os.environ.get('ARC4_WASH', '1.3'))
FILL_I = float(os.environ.get('ARC4_FILL', '0.35'))
SPILL_I = float(os.environ.get('ARC4_SPILL', '0.45'))
POOL_I = float(os.environ.get('ARC4_POOL', '2.2'))
M.update(arcade='park_arcade_standing_01_off', arcade2='park_arcade_standing_02_off', claw='ct_arcade_claw_machine', gum='gumball_machine_fn_01', crate2='ch_crate32x48',
         crate3='ch_crate48x64', crate1='ch_crate24x36', barrel='com_barrel_black', barrel2='com_barrel_green_rust', barrel3='com_barrel_tan_rust', cone='traffic_cone_sml_01',
         pallet='com_pallet', cart2='park_concessions_cart', ftable='com_folding_table', fchair='chair_folding', bucket='bucket_plastic', stool2='chair_bar_stool_02',
         dump='rp_dumpster_01', ladder='com_stepladder_large', fcab='furniture_filing_cabinet', speaker='speaker_public_iw6', tv='zmb_tv_crt_screen_01', film='cp_disco_film_reel_case',
         lockers='cp_disco_subway_lockers_02', clothing='bike_shop_clothing_table_01', desk='cp_town_desk_01', phone2='cp_town_desk_phone_01_black', photo1='cp_town_space_hero_photos_01',
         planter2='flower_shop_planter_04_with_plant', hydrant='vfx_fire_hydrant_stream')


def foot(D, x0, y0, x1, y1):
    D.boxes.append((x0, y0, x1, y1))


# ------------------------------------------------------------------------------------------------ pictograms (pictures, no letters): arrows on a blue board
def make_pictures(folder):
    """writes the arrow pictograms beside map.json (called after the document is saved)"""
    from PIL import Image, ImageDraw
    for name, kind in (('arrow_l.png', 'l'), ('arrow_r.png', 'r'), ('arrow_stair.png', 's')):
        im = Image.new('RGB', (256, 80), (20, 60, 150))
        d = ImageDraw.Draw(im)
        d.rectangle([4, 4, 251, 75], outline=(235, 235, 235), width=4)
        if kind in ('l', 'r'):
            sgn = -1 if kind == 'l' else 1
            cx = 128
            d.rectangle([cx - 70, 32, cx + 70, 48], fill=(240, 240, 240))
            d.polygon([(cx + sgn * 100, 40), (cx + sgn * 46, 10), (cx + sgn * 46, 70)], fill=(240, 240, 240))
        else:
            for k in range(5):
                d.rectangle([40 + k * 30, 58 - k * 11, 70 + k * 30, 66 - k * 11 + 8], fill=(240, 240, 240))
            d.polygon([(214, 14), (236, 36), (192, 36)], fill=(250, 210, 40))
        im.save('%s/%s' % (folder, name))


# ------------------------------------------------------------------------------------------------ floor and walls
def floor4(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    uv = {'top': {'tile': [40.0, 40.0]}}
    box(m, [cx0, cy0, 0.0, cx1, cy1, 1.0], A.FLOOR_SKIN, id='floor_tile', uv=uv)
    for k, (y0, y1) in enumerate(((cy0, cy0 + 26.0), (cy1 - 26.0, cy1))):
        box(m, [cx0, y0, 0.0, cx1, y1, 1.5], 'w/fac_tile_black_01', id='floor_border_%d' % k, uv={'top': {'tile': [32.0, 32.0]}})
    for k, yc in enumerate(((cy0 + 3850.0) / 2.0, (3950.0 + cy1) / 2.0)):          # a black runner down each lane with an orange line each side
        box(m, [cx0, yc - 44.0, 0.0, cx1, yc + 44.0, 1.3], 'w/beacon_lab_floor_tile_02_black', id='runner_%d' % k, uv={'top': {'tile': [24.0, 24.0]}})
        for sgn in (-1, 1):
            box(m, [cx0, yc + sgn * 44.0 - 2.0, 0.0, cx1, yc + sgn * 44.0 + 2.0, 1.6], 'w/plastic_slick_floor_01_orange', id='inlay_%d_%d' % (k, sgn), uv={'top': {'tile': [24.0, 24.0]}})
    for k in range(6):                                                              # expansion joints across the hall
        x = cx0 + 160.0 + k * 300.0
        box(m, [x - 1.0, cy0, 0.0, x + 1.0, cy1, 1.7], BLACK, id='joint_%d' % k)
    for k in range(5):
        a0, a1 = A.aperture(k)
        box(m, [a0, cy1 - 46.0, 1.0, a1, cy1 - 26.0, 1.6], 'w/fac_rubber_mat_black', id='mat_%d' % (k + 1))
        box(m, [a0 - 4.0, cy1 - 24.0, 0.0, a1 + 4.0, cy1 - 20.0, 1.8], 'w/metal_painted_scratched_yellow', id='threshold_%d' % (k + 1))
    report['floor'] = {'skin': A.FLOOR_SKIN, 'slab': A.FLOOR}


def wall_bands4(A, m, D, report):
    R3.wall_bands(A, m, D, report)                       # the wainscot (A.WALLBAND), kick plate, rail, pilasters, grime strips
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    # a painted stripe over the tile, a second one under the ceiling, on both walls (piers of the north wall only)
    box(m, [cx0, cy0 + 2.0, 106.0, cx1, cy0 + 3.5, 118.0], 'w/concrete_painted_wall_green', id='stripe_s')
    box(m, [cx0, cy0 + 2.0, 196.0, cx1, cy0 + 3.5, 204.0], 'w/plastic_slick_floor_01_orange', id='stripe_s2')
    ap = [A.aperture(i) for i in range(5)]
    x = cx0
    for k, (a0, a1) in enumerate(ap + [(cx1 + 8.0, cx1 + 8.0)]):
        x1 = a0 - 8.0
        if x1 - x > 8.0:
            box(m, [x, cy1 - 3.5, 106.0, x1, cy1 - 2.0, 118.0], 'w/concrete_painted_wall_green', id='stripe_n%d' % k)
        x = a1 + 8.0


# ------------------------------------------------------------------------------------------------ the spine: six different columns, the islands
COLSPEC = [
    dict(mat='w/ceramic_tile_01_orange', wain=('w/ceramic_tile_01_blue', 112.0), stripe=None, feature='map'),
    dict(mat='w/concrete_painted_wall_green', wain=('w/concrete_wall_panel_05', 64.0), stripe='w/metal_painted_scratched_yellow', feature='extinguisher'),
    dict(mat='w/brick_cinderblock_02_smooth_blue', wain=None, stripe='w/plastic_slick_floor_01_orange', feature='lightbox'),
    dict(mat='w/concrete_wall_panel_05', wain=('w/fac_tile_black_01', 80.0), stripe=None, feature='plain'),            # phones stand against it
    dict(mat='w/ceramic_tile_01_blue', wain=('w/ceramic_tile_01_orange', 48.0), stripe=None, feature='poster'),
    dict(mat='w/brick_cinderblock_04_beige_dirty', wain=None, stripe='w/concrete_painted_wall_green', feature='poster2'),
]


def column(A, m, D, k, x):
    spec = COLSPEC[k]
    B.column(m, (x, SPINE_Y), 0.0, 256.0, 32.0, spec['mat'], id='col_%d' % k)
    box(m, [x - 20.0, SPINE_Y - 20.0, 0.0, x + 20.0, SPINE_Y + 20.0, 48.0], BLACK, id='col_plinth_%d' % k)
    box(m, [x - 18.0, SPINE_Y - 18.0, 56.0, x + 18.0, SPINE_Y + 18.0, 64.0], RUBBER, id='col_bumper_%d' % k)
    box(m, [x - 19.0, SPINE_Y - 19.0, 200.0, x + 19.0, SPINE_Y + 19.0, 208.0], BLACK, id='col_cap_%d' % k)
    foot(D, x - 20.0, SPINE_Y - 20.0, x + 20.0, SPINE_Y + 20.0)
    if spec['wain']:
        wm, wh = spec['wain']
        top = max(wh, 70.0)
        box(m, [x - 18.0, SPINE_Y - 18.0, 64.0, x + 18.0, SPINE_Y + 18.0, top], wm, id='col_wain_%d' % k)
        box(m, [x - 19.0, SPINE_Y - 19.0, top, x + 19.0, SPINE_Y + 19.0, top + 3.0], BLACK, id='col_wcap_%d' % k)
    if spec['stripe']:
        box(m, [x - 17.0, SPINE_Y - 17.0, 150.0, x + 17.0, SPINE_Y + 17.0, 164.0], spec['stripe'], id='col_stripe_%d' % k)
    f = spec['feature']
    for sgn in (-1, 1):                                  # the two faces that look into the lanes
        yf = SPINE_Y + sgn * 16.0
        y0, y1 = (yf, yf + sgn * 2.0) if sgn > 0 else (yf + sgn * 2.0, yf)
        if f == 'map':
            box(m, [x - 13.0, y0, 88.0, x + 13.0, y1, 146.0], BLACK, id='col_mapframe_%d_%d' % (k, sgn))
            y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
            box(m, [x - 11.0, y2[0], 92.0, x + 11.0, y2[1], 142.0], 'w/zombies_underground_map', id='col_map_%d_%d' % (k, sgn))
        elif f == 'extinguisher':
            box(m, [x - 6.0, y0, 92.0, x + 6.0, y1, 126.0], 'w/iw7_drywall_painted_red_01', id='col_fire_%d_%d' % (k, sgn))
            box(m, [x - 3.0, y0, 132.0, x + 3.0, y1, 142.0], 'w/metal_painted_scratched_yellow_02', id='col_fireplate_%d_%d' % (k, sgn))
        elif f == 'lightbox':
            box(m, [x - 13.0, y0, 84.0, x + 13.0, y1, 150.0], BLACK, id='col_lbframe_%d_%d' % (k, sgn))
            y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
            box(m, [x - 11.0, y2[0], 88.0, x + 11.0, y2[1], 146.0], TUBE['photo'] if sgn > 0 else TUBE['heel'], id='col_lb_%d_%d' % (k, sgn))
        elif f in ('poster', 'poster2'):
            for j, zz in enumerate((90.0, 134.0)):
                box(m, [x - 11.0, y0, zz, x + 11.0, y1, zz + 38.0], BLACK, id='col_pframe_%d_%d_%d' % (k, sgn, j))
                y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
                box(m, [x - 9.5, y2[0], zz + 1.5, x + 9.5, y2[1], zz + 36.5], POSTERS[(k * 3 + j + (0 if sgn > 0 else 2)) % len(POSTERS)], id='col_poster_%d_%d_%d' % (k, sgn, j))


def spine4(A, m, D, report):
    m.use('dressing')
    for k, x in enumerate(COLS):
        column(A, m, D, k, x)
    report['columns'] = {'placed': list(COLS), 'kinds': [c['mat'] for c in COLSPEC]}

    def hang(x, mod, yaw, y=SPINE_Y, z_bar=168.0, w=84.0):
        box(m, [x - w / 2.0, y - 1.5, z_bar, x + w / 2.0, y + 1.5, z_bar + 3.0], BLACK, id='bar_%d' % int(x))
        for s in (-1, 1):
            box(m, [x + s * (w / 2.0 - 4.0) - 1.0, y - 1.0, z_bar + 3.0, x + s * (w / 2.0 - 4.0) + 1.0, y + 1.0, 208.0], BLACK, id='rod_%d_%d' % (int(x), s))
        mn, mx = D.bounds(M.get(mod, mod))
        D.put(M.get(mod, mod), x, y, yaw, z=z_bar - (mx[2] - mn[2]) + 6.0, ignore_keep=True, margin=0.0)

    # (ii) the kiosk at the first gap, moved 105 north of the spine line: round 3's camera arc_d7 stood INSIDE it (x -2670 against the footprint -2748..-2652)
    kx, ky = GAPS[0], SPINE_Y + 105.0
    x0, x1, y0, y1 = kx - 48.0, kx + 48.0, ky - 32.0, ky + 32.0
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
    D.tops['kiosk'] = (kx, ky, 47.0, 96.0, 64.0, 0.0)
    foot(D, x0 - 8.0, y0 - 8.0, x1 + 8.0, y1 + 8.0)
    D.put(M['news'], kx - 72.0, ky - 12.0, 0.0, tag='kiosk_news_a', margin=0.0)
    D.put(M['news'], kx - 72.0, ky + 18.0, 0.0, tag='kiosk_news_b', margin=0.0)
    D.put(M['news'], kx + 72.0, ky + 4.0, 180.0, tag='kiosk_news_c', margin=0.0)
    for k, (mod, du, dv, yw) in enumerate((('register', -22.0, 14.0, 270.0), ('coffee', 14.0, 16.0, 270.0), ('mags', 28.0, -14.0, 20.0), ('stackp', -10.0, -14.0, 60.0),
                                           ('mug', 30.0, 10.0, 0.0), ('mags', -34.0, -12.0, 100.0), ('gum', 0.0, 0.0, 0.0), ('donuts', -30.0, 6.0, 30.0))):
        D.put(M[mod], kx + du, ky + dv, yw, z=47.0, ignore_keep=True, margin=0.0)
    hang(kx, 'sign1', 0.0, y=ky, z_bar=150.0)
    # the first gap of the spine itself: a floor drain grate and a wet patch (the camera arc_d7 stands here: nothing solid)
    box(m, [kx - 30.0, SPINE_Y - 14.0, 0.0, kx + 30.0, SPINE_Y + 14.0, 1.9], 'w/metal_deck_painted_black_01', id='gap0_grate')
    # (i) two subway benches back to back with a bin
    bx = GAPS[1]
    D.put(M['bench'], bx, SPINE_Y - 21.0, 90.0, tag='bench_a', margin=0.0)
    D.put(M['bench'], bx, SPINE_Y + 21.0, 270.0, tag='bench_b', margin=0.0)
    D.put(M['bin1'], bx - 118.0, SPINE_Y, 0.0, tag='bin_i', margin=0.0)
    for j, mod in enumerate(('paper', 'cup', 'mags', 'cup', 'paper', 'chips')):
        D.put(M[mod], bx + (j - 2.5) * 30.0, SPINE_Y + (-21.0 if j % 2 == 0 else 21.0), D.rng.uniform(0, 360), on='bench_a' if j % 2 == 0 else 'bench_b', margin=0.0)
    hang(bx, 'sign2', 90.0)
    # (iii) a planter box with plants and litter
    px = GAPS[2]
    B.box(m, [px - 60.0, SPINE_Y - 20.0, 0.0, px + 60.0, SPINE_Y + 20.0, 34.0], 'w/concrete_wall_01_stained', id='planter_box')
    box(m, [px - 62.0, SPINE_Y - 22.0, 34.0, px + 62.0, SPINE_Y + 22.0, 38.0], BLACK, id='planter_rim')
    box(m, [px - 56.0, SPINE_Y - 16.0, 38.0, px + 56.0, SPINE_Y + 16.0, 39.0], 'w/dirt_stain_leaking_01', id='planter_soil')
    foot(D, px - 62.0, SPINE_Y - 22.0, px + 62.0, SPINE_Y + 22.0)
    D.tops['planter'] = (px, SPINE_Y, 39.0, 120.0, 40.0, 0.0)
    for j, du in enumerate((-44.0, -14.0, 16.0, 46.0)):                    # four different plants (round 3 had three identical)
        D.put((M['plant'], M['planter2'], 'flower_shop_planter_02', M['plant'])[j], px + du, SPINE_Y + (4.0 if j % 2 else -4.0), D.rng.uniform(0, 360), z=39.0, ignore_keep=True, margin=0.0,
              scale=(1.0, 0.8, 1.2, 1.1)[j])
    for j in range(6):
        D.put(D.rng.choice((M['cup'], M['chips'], M['paper'], M['smokes'], M['can'])), px + D.rng.uniform(-80.0, 80.0), SPINE_Y + D.rng.uniform(-34.0, 34.0), D.rng.uniform(0, 360), margin=0.0)
    hang(px, 'sign4', 90.0)
    # (iv) a pay phone pair on the column at x = -1950, a transit map case and a newspaper box beside it
    cxp = COLS[3]
    D.put(M['phone'], cxp + 16.0 + 13.0, SPINE_Y, 0.0, tag='ph_e', margin=0.0)
    D.put(M['phone'], cxp - 16.0 - 13.0, SPINE_Y, 180.0, tag='ph_w', margin=0.0)
    D.put(M['case'], GAPS[3], SPINE_Y, 0.0, tag='mapcase_i', margin=0.0)
    D.put(M['news'], GAPS[3] + 60.0, SPINE_Y - 16.0, 180.0, tag='news_iv', margin=0.0)
    D.put(M['bin2'], GAPS[3] - 60.0, SPINE_Y + 14.0, 0.0, tag='bin_iv', margin=0.0)
    D.put(M['ftable'], GAPS[3] + 20.0, SPINE_Y + 36.0, 90.0, tag='tbl_iv', margin=0.0)
    for j, mod in enumerate(('mags', 'cup', 'paper')):
        D.on('tbl_iv', M[mod], (j - 1) * 20.0, 0.0, D.rng.uniform(0, 360))
    # (v) the floor buffer with wet floor signs and a cable
    fx = GAPS[4]
    D.put(M['buffer'], fx, SPINE_Y, 20.0, tag='buffer', margin=0.0)
    D.put(M['wet'], fx - 70.0, SPINE_Y - 22.0, 30.0, tag='wet_a', margin=0.0)
    D.put(M['wet'], fx + 70.0, SPINE_Y + 24.0, 200.0, tag='wet_b', margin=0.0)
    D.put(M['mop'], fx + 40.0, SPINE_Y + 30.0, 80.0, tag='mop', margin=0.0)
    D.put(M['bucket'], fx + 62.0, SPINE_Y + 34.0, 10.0, tag='bucket_v', margin=0.0)
    D.put(M['cone'], fx - 100.0, SPINE_Y + 10.0, 0.0, tag='cone_v', margin=0.0)
    pts = [(fx + 28.0, SPINE_Y - 4.0), (fx + 60.0, SPINE_Y - 30.0), (fx + 110.0, SPINE_Y - 22.0), (fx + 140.0, SPINE_Y + 20.0), (fx + 190.0, SPINE_Y + 40.0)]
    for k in range(len(pts) - 1):
        (ax, ay), (bx2, by2) = pts[k], pts[k + 1]
        box(m, [min(ax, bx2) - 1.5, min(ay, by2) - 1.5, 0.0, max(ax, bx2) + 1.5, max(ay, by2) + 1.5, 3.0], 'w/fac_rubber_mat_black', id='cable_%d' % k)
    hang(fx, 'sign4', 90.0, z_bar=172.0)


# ------------------------------------------------------------------------------------------------ ceiling
def ceiling4(A, m, D, report):
    R3.ceiling(A, m, D, report)
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    for k, y in enumerate((3556.0, 4252.0)):                                       # cable trays with hanging rods
        box(m, [cx0, y - 14.0, 216.0, cx1, y + 14.0, 219.0], 'w/metal_painted_04', id='tray_%d' % k)
        box(m, [cx0, y - 14.0, 219.0, cx1, y - 12.0, 226.0], BLACK, id='tray_lip_a%d' % k)
        box(m, [cx0, y + 12.0, 219.0, cx1, y + 14.0, 226.0], BLACK, id='tray_lip_b%d' % k)
        x = cx0 + 60.0
        while x < cx1:
            box(m, [x - 0.6, y - 0.6, 219.0, x + 0.6, y + 0.6, 256.0], BLACK, id='tray_rod_%d_%d' % (k, int(x)))
            x += 128.0
    # arrow pictograms on bars hung over the lanes (pictures: no letters)
    for k, (x, y, img) in enumerate(((-2400.0, 3690.0, 'arrow_l.png'), (-1650.0, 3690.0, 'arrow_r.png'), (-2250.0, 4130.0, 'arrow_stair.png'), (-1950.0, 4130.0, 'arrow_r.png'))):
        box(m, [x - 52.0, y - 1.5, 176.0, x + 52.0, y + 1.5, 218.0], BLACK, id='sbar_%d' % k)
        for sgn in (-1, 1):
            box(m, [x + sgn * 48.0 - 0.8, y - 0.8, 218.0, x + sgn * 48.0 + 0.8, y + 0.8, 256.0], BLACK, id='srod_%d_%d' % (k, sgn))
        for sgn in (-1, 1):
            B.sign(m, image=img, at=(x, y + sgn * 1.5, 198.0), normal=(0.0, float(sgn), 0.0), size=(96.0, 30.0), emissive={'color': [0.55, 0.7, 1.0], 'strength': 0.9}, id='sign_arrow_%d_%d' % (k, sgn))


def ceiling_props4(A, D):
    R3.ceiling_props(A, D)
    for line, y in enumerate((3600.0, 4220.0)):                                       # a second duct and pipe pair
        x = A.X0 + 160.0
        while x < A.X1 - 90.0:
            D.ceil(M['pipe'], x, y, 90.0, 232.0)
            x += 128.0
    x = A.X0 + 220.0
    while x < A.X1 - 90.0:
        D.ceil(M['duct'], x, 4010.0, 90.0, 228.0)
        x += 256.0


# ------------------------------------------------------------------------------------------------ a shop
def hung(m, id, x, y, z, w, h, mat, ceil=200.0):
    R3.hung_sheet(m, id, x, y, z, w, h, mat, True, ceil)


SHOP_SRC = {'photo': ('cp_disco#120', 0), 'heel': ('cp_zmb#91', 0), 'hole9': ('cp_disco#59', 0), 'copy': ('cp_rave#104', 1), 'needle': ('cp_disco#39', 0)}
WAINS = {'photo': 'w/ceramic_ship_interior_tile_01', 'heel': 'w/ceramic_tile_01_orange', 'hole9': 'w/fac_tile_black_01', 'copy': 'w/ceramic_tile_01_blue', 'needle': 'w/fac_tile_black_01'}


def dress_shop(A, m, D, i, report):
    """P.dress_like into the shop's front room (x between the side walls, y from the front wall to 34 before the partition: the tall back-wall stock is ours)"""
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    left, right = s + A.WT, s + A.BAY_W - A.WT
    y0, y1 = A.Y1 + A.WT, A.BACK_Y - 34.0
    room, seed = SHOP_SRC[kind]
    m.use('dressing')
    rep = P.dress_like(m, room, [left, y0, right, y1], front='s', density=1.0, seed=seed, z=0.0, prefix='dl%d_' % (i + 1))
    removed = 0
    for pid in list(rep['ids']):
        o = m.get(pid)
        if o is None:
            continue
        if o.get('kind') == 'prop' and (o['origin'][2] < 72.0):
            bx = D.box_of(o['model'], o['origin'][0], o['origin'][1], (o.get('angles') or [0, 0, 0])[1], o.get('scale') or 1.0)
            if any(bx[0] < k[2] and bx[2] > k[0] and bx[1] < k[3] and bx[3] > k[1] for k in D.keep):
                m.remove(pid)
                removed += 1
                continue
            D.boxes.append(bx)
            D.n += 1
        elif o.get('kind') == 'prop':
            D.n += 1
    report.setdefault('dress_like', {})[kind] = {'room': room, 'placed': rep['placed'] - removed, 'removed_for_gameplay': removed, 'dropped': rep['dropped_by_reason'],
                                                'models': rep['models_needed'], 'density_per_1000': rep['density_per_1000'], 'coverage': rep['coverage']['dressed']}


def shop(A, m, D, i, report):
    s = A.BAY_X[i]
    yb = A.Y1
    kind = A.BAYS[i]
    wallb = yb + A.BAY_D - A.WT
    U = lambda u: s + u
    V = lambda v: yb + v
    yp = A.BACK_Y
    left, right = s + A.WT, s + A.BAY_W - A.WT
    hue = HUE[kind]
    brd = R3.BOARD[kind]
    lv = (24.0, 46.0, 68.0, 90.0, 112.0, 134.0, 156.0)
    D.rooms.append((left, yb + A.WT, right, yp + 10.0))                 # the stock leans on the partition: its jittered boxes may touch the partition's thickness
    D.rooms.append((left, yp + 10.0, right, wallb + 6.0))
    m.use('dressing')
    box(m, [left, yb + A.WT, 0.0, left + 2.0, wallb, 8.0], BLACK, id='skirt_l_%d' % (i + 1))
    box(m, [right - 2.0, yb + A.WT, 0.0, right, wallb, 8.0], BLACK, id='skirt_r_%d' % (i + 1))
    # the tiled wainscot of the front room (render only) and a rail
    for side, (xa, xb) in enumerate(((left, left + 1.5), (right - 1.5, right))):
        box(m, [xa, yb + A.WT, 8.0, xb, yp, 44.0], WAINS[kind], id='wain_%d_%d' % (i + 1, side))
        box(m, [xa, yb + A.WT, 44.0, xb, yp, 46.0], BLACK, id='wrail_%d_%d' % (i + 1, side))
    box(m, [left, yb + A.WT, 8.0, right, yb + A.WT + 1.5, 44.0], WAINS[kind], id='wain_f_%d' % (i + 1))
    # the stock: tall shelving on the partition's face (the back wall the inside camera sees), two units, packed
    items = {'photo': (['boxc', 'photo1', 'mags', 'crackers', 'paper', 'books', 'film'], ['film', 'boxc', 'paper', 'mags', 'photo1', 'books', 'boxa']),
             'heel': (['shoes', 'shoes', 'boxc', 'shoes', 'shoes', 'boxa', 'hook'], ['shoes', 'boxc', 'shoes', 'shoes', 'boxa', 'shoes', 'toolbox']),
             'hole9': (['crackers', 'donuts', 'mug', 'crackers', 'donuts', 'glass', 'boxc'], ['donuts', 'crackers', 'mug', 'donuts', 'glass', 'boxc', 'crackers']),
             'copy': (['ream', 'stack', 'ream', 'books', 'ream', 'stack', 'boxa'], ['ream', 'ream', 'books', 'stack', 'ream', 'boxa', 'books']),
             'needle': (['sleeve', 'sleeve', 'crate', 'sleeve', 'sleeve', 'crate', 'film'], ['sleeve', 'crate', 'sleeve', 'sleeve', 'crate', 'sleeve', 'sleeve'])}[kind]
    step = {'photo': 9.0, 'heel': 9.0, 'hole9': 9.0, 'copy': 10.0, 'needle': 5.0}[kind]
    n_stock = 0
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        sh = R2.Shelf(m, 'shelf_p%d_%d' % (side, i), (U(u0), yp - 32.0, U(u1), yp), 's', lv, board=brd, top=172.0)
        n_stock += R2.stock(D, sh, items[side], step * 1.5, yaw=270.0, jitter=14.0, skip=0.04, scale=1.5)
    # a transom shelf above the doorway, packed boxes
    sh = R2.Shelf(m, 'shelf_t_%d' % i, (U(116.0), yp - 22.0, U(204.0), yp), 's', (110.0, 134.0, 158.0), board=brd, top=172.0, clip=False)      # above the doorway (96 high): no collision
    n_stock += R2.stock(D, sh, ['boxc', 'boxa', 'boxc'] if kind != 'needle' else ['crate', 'boxa', 'crate'], 28.0, yaw=270.0, jitter=10.0, skip=0.0)
    # the hung things behind the aperture (as round 3) and the posters on both side walls
    cx = s + A.BAY_W / 2.0
    hy = V(44.0)
    if kind == 'photo':
        for k in range(9):
            hung(m, 'hg_%d_%d' % (i, k), cx - 100.0 + 25.0 * k, hy + (6.0 if k % 2 else 0.0), 58.0 + (6.0 if k % 2 else 0.0), 11.0, 22.0, ('w/zombies_blank_photo', 'w/zombies_teddy_photo')[k % 2])
    elif kind == 'heel':
        for q, ux in enumerate((-90.0, 90.0)):
            box(m, [cx + ux - 22.0, hy + 4.0, 56.0, cx + ux + 22.0, hy + 5.5, 86.0], 'w/wood_worn_painted_01_green', id='keyboard_%d_%d' % (i, q))
            R3.rod(m, 'kb_ra_%d_%d' % (i, q), cx + ux - 20.0, hy + 4.0, 86.0, 200.0)
            R3.rod(m, 'kb_rb_%d_%d' % (i, q), cx + ux + 20.0, hy + 4.0, 86.0, 200.0)
            for k in range(8):
                D.put(M['hook'], cx + ux - 18.0 + 5.0 * k, hy + 4.0, 270.0, z=60.0 + 12.0 * (k % 2) + 8.0, scale=2.5, ignore_keep=True, margin=0.0)
    elif kind == 'hole9':
        for k in range(5):
            hung(m, 'hg_%d_%d' % (i, k), cx - 90.0 + 45.0 * k, hy + (5.0 if k % 2 else 0.0), 52.0, 30.0, 26.0, 'w/signage_theater_menu_01')
    elif kind == 'copy':
        for k in range(6):
            hung(m, 'hg_%d_%d' % (i, k), cx - 100.0 + 40.0 * k, hy + (6.0 if k % 2 else 0.0), 50.0 + (8.0 if k % 2 else 0.0), 26.0, 22.0, 'w/zombies_underground_map')
    else:
        for k in range(14):
            hung(m, 'hg_%d_%d' % (i, k), cx - 104.0 + 16.0 * k, hy + (6.0 if k % 2 else 0.0), 54.0 + 8.0 * (k % 3), 12.0, 12.0,
                 ('w/zombies_theater_poster01', 'w/zombies_theater_poster02', 'w/signage_zmb_park_poster_03')[k % 3])
    for k, (zz, vv) in enumerate(((100.0, 50.0), (96.0, 96.0), (104.0, 130.0))):
        B.decal(m, POSTERS[(i + k) % len(POSTERS)], (left, V(vv), zz), (1.0, 0.0, 0.0), (26.0, 36.0), id='post_l_%d_%d' % (i, k))
        B.decal(m, POSTERS[(i + k + 3) % len(POSTERS)], (right, V(vv + 8.0), zz), (-1.0, 0.0, 0.0), (26.0, 36.0), id='post_r_%d_%d' % (i, k))
    # the emissive light strips in the shop's hue under the ceiling (they light the stock and the floor through the bake) and a black housing
    for k, vv in enumerate((58.0, 118.0)):
        box(m, [cx - 96.0, V(vv) - 3.0, 194.0, cx + 96.0, V(vv) + 3.0, 198.0], TUBE[kind], id='strip_%d_%d' % (i + 1, k))
        box(m, [cx - 98.0, V(vv) - 5.0, 198.0, cx + 98.0, V(vv) + 5.0, 200.0], BLACK, id='strip_h_%d_%d' % (i + 1, k))
    # the back room: lit, with stock (zombies spawn here: D.keep holds the spawner clearances)
    for side, ux in enumerate((62.0, 258.0)):
        sh = R2.Shelf(m, 'bs_%d_%d' % (i, side), (U(ux - 30.0), wallb - 24.0, U(ux + 30.0), wallb), 's', (24.0, 52.0, 80.0, 108.0), board=brd, top=116.0, clip=False)
        R2.stock(D, sh, ['boxc', 'boxa', 'crate2', 'bag', 'boxc'], 18.0, yaw=270.0, jitter=14.0, skip=0.05)
    D.put(M['barrel'], U(150.0), wallb - 20.0, 0.0, tag='bk_barrel_%d' % i, margin=1.0, clip=False)
    D.put(M['crate3'], U(184.0), wallb - 26.0, 8.0, tag='bk_crate_%d' % i, margin=1.0, clip=False)
    D.put(M['ladder'], U(30.0), V(240.0), 80.0, tag='bk_ladder_%d' % i, margin=1.0, clip=False)
    D.put(M['fcab'], U(290.0), V(256.0), 270.0, tag='bk_fcab_%d' % i, margin=1.0, clip=False)
    n = D.n
    dress_shop(A, m, D, i, report)
    return n_stock


# ------------------------------------------------------------------------------------------------ the corridor: density at the scale of the frame
def corridor_dense(A, m, D, report):
    m.use('dressing')
    rng = D.rng
    # an arcade bank on the south wall (the place is named for it): cabinets side by side, a claw machine and gumball machines
    x = -2700.0
    for k in range(5):
        D.wall(M['arcade'] if k % 2 == 0 else M['arcade2'], 's', x + 38.0 * k, tag='cab%d' % k)
    D.wall(M['claw'], 's', -2500.0, tag='claw0')
    D.wall(M['gum'], 's', -2530.0, tag='gum0')
    D.wall(M['gum'], 's', -2160.0, tag='gum1')
    D.wall(M['claw'], 's', -1250.0, tag='claw1')
    # market stalls in the band between the lanes' keep-outs and the spine: folding tables with goods, chairs, carts, crate stacks
    stalls = [(-2280.0, 3770.0), (-1860.0, 3790.0), (-1560.0, 3770.0), (-2560.0, 3790.0)]
    for k, (sx, sy) in enumerate(stalls):
        D.put(M['ftable'], sx, sy, 90.0 if k % 2 else 0.0, tag='stall%d' % k, margin=2.0)
        for j in range(4):
            D.on('stall%d' % k, rng.choice((M['crackers'], M['cup'], M['mags'], M['boxc'], M['mug'], M['donuts'])), (j - 1.5) * 16.0 if k % 2 == 0 else 0.0,
                 0.0 if k % 2 == 0 else (j - 1.5) * 16.0, rng.uniform(0, 360))
        D.put(M['fchair'], sx + 4.0, sy - 40.0, rng.uniform(60, 120), margin=1.0)
        D.put(M['fchair'], sx + 40.0, sy + 10.0, rng.uniform(0, 360), margin=1.0)
    for k, (cx_, cy_) in enumerate(((-2100.0, 3800.0), (-1420.0, 3800.0), (-2700.0, 3790.0))):
        D.put(M['cart2'], cx_, cy_, 90.0 + 20.0 * k, tag='cart%d' % k, margin=2.0)
    for k, (cx_, cy_) in enumerate(((-2960.0 + 50.0, 3560.0), (-1216.0 - 60.0, 3560.0), (-1980.0, 3552.0), (-2400.0, 3552.0))):     # crate and barrel stacks along the south wall
        D.put(M['crate3'], cx_, cy_, rng.uniform(-10, 10), tag='stk%d' % k, margin=1.0)
        D.put(M['crate2'], cx_ + 6.0, cy_, rng.uniform(-10, 10), on='stk%d' % k, margin=0.0)
        D.put(M['barrel'] if k % 2 else M['barrel2'], cx_ + 58.0, cy_ + 6.0, 0.0, margin=1.0)
        D.put(M['barrel3'], cx_ + 84.0, cy_ + 2.0, 0.0, margin=1.0)
    D.wall(M['dump'], 's', -2020.0, tag='dump_s')
    # north piers: cabinets, hydrant, ladders against the pilasters
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        if k in (0, 5):
            D.wall(M['fcab'], 'n', mid, tag='pier_fcab%d' % k)
        if k in (2, 4):
            D.wall(M['ladder'], 'n', mid - 20.0, tag='pier_ladder%d' % k)
            D.wall(M['bucket'], 'n', mid + 20.0, tag='pier_bucket%d' % k)
    # scatter: mid-size (stacks, cones, buckets, pallets, stools) and small litter in clusters
    mids = [M['crate1'], M['crate2'], M['cone'], M['bucket'], M['pallet'], M['stool2'], M['fchair'], M['barrel'], M['cone'], M['bucket']]
    smalls = [M['chips'], M['cup'], M['paper'], M['can'], M['smokes'], M['stackp'], M['mags'], M['mug'], M['cup'], M['paper']]
    x0, x1 = A.X0 + 50.0, A.X1 - 50.0
    bands = [(3524.0, 3588.0), (3702.0, 3860.0), (3940.0, 4128.0), (4242.0, 4276.0)]
    placed_mid = 0
    for _ in range(220):
        b = rng.choice(bands)
        if D.put(rng.choice(mids), rng.uniform(x0, x1), rng.uniform(*b), rng.uniform(0, 360), margin=3.0):
            placed_mid += 1
    clusters = 0
    for _ in range(110):                                      # litter clusters: 4 to 8 small props within 30 units
        b = rng.choice(bands + [(3590.0, 3700.0), (4130.0, 4240.0)])
        cx_, cy_ = rng.uniform(x0, x1), rng.uniform(*b)
        for _j in range(rng.randint(4, 8)):
            if D.put(rng.choice(smalls), cx_ + rng.uniform(-30.0, 30.0), cy_ + rng.uniform(-20.0, 20.0), rng.uniform(0, 360), margin=0.5, clip=False, ignore_keep=(3590.0 <= cy_ <= 3700.0 or 4130.0 <= cy_ <= 4240.0)):
                clusters += 1
    report['corridor_dense'] = {'mid': placed_mid, 'litter': clusters}
    # posters on the walls (stock poster materials: pictures, no words of ours), grime and puddle decals
    for k in range(18):
        x = A.X0 + 90.0 + k * 96.0
        B.decal(m, POSTERS[k % len(POSTERS)], (x, A.Y0 + A.WT, 150.0 + 4.0 * (k % 3)), (0.0, 1.0, 0.0), (28.0, 40.0), id='dec_post_s%d' % k)
    for k, (a, b) in enumerate(PIERS):
        B.decal(m, POSTERS[(k * 2) % len(POSTERS)], ((a + b) / 2.0 - 14.0 + (12.0 if k % 2 else 0.0), A.Y1 - A.WT, 150.0), (0.0, -1.0, 0.0), (28.0, 40.0), id='dec_post_n%d' % k)
    for k in range(12):
        x = A.X0 + 100.0 + k * 140.0
        yy = rng.choice((3610.0, 3700.0, 3830.0, 3950.0, 4090.0, 4230.0)) + rng.uniform(-25.0, 25.0)
        B.decal(m, ('w/dirt_stain_water_drips_01', 'w/wall_stain_01_dec', 'w/dirt_stain_water_drips_01')[k % 3], (x + rng.uniform(-20, 20), yy, 1.8), (0.0, 0.0, 1.0),
                (rng.uniform(36.0, 70.0), rng.uniform(36.0, 64.0)), rot=rng.uniform(0, 360), id='dec_floor_%d' % k)


# ------------------------------------------------------------------------------------------------ light
def lights4(A, m, report):
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, **k)
    for k, (x, y, single) in enumerate(A.live):
        L((x, y, 176.0), color=(1.0, 0.93, 0.78), radius=170.0, intensity=round(POOL_I * (0.55 if single else 1.0), 3), type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    for i in range(5):
        hue = HUE[A.BAYS[i]]
        s = A.BAY_X[i]
        cx = s + A.BAY_W / 2.0
        L((cx, A.Y1 + 70.0, 188.0), color=(1.0, 0.86, 0.66), radius=280.0, intensity=KEY_I, type='spot', dir=(0.0, 0.0, -1.0), inner=34.0, outer=84.0, id='light_key_%d' % (i + 1))
        for side, ux in enumerate((67.0, 253.0)):
            wp = (s + ux, A.Y1 + 40.0, 188.0)
            wt = (s + ux, A.BACK_Y - 10.0, 80.0)
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(wp, wt)))
            d = [(wt[j] - wp[j]) / dist for j in range(3)]
            L(wp, color=tuple(round(0.5 + 0.5 * c, 3) for c in hue), radius=round(dist * 1.8, 1), intensity=round(WASH_I * (dist / 200.0) ** 2, 4), type='spot', dir=d, inner=16.0, outer=46.0,
              id='light_wash_%d_%d' % (i + 1, side))
        L((cx, A.Y1 + 60.0, 140.0), color=hue, radius=200.0, intensity=FILL_I, id='light_fill_%d' % (i + 1))
        L((cx, A.Y1 - 30.0, 80.0), color=hue, radius=170.0, intensity=SPILL_I, id='light_spill_%d' % (i + 1))             # the shop's colour on the corridor floor in front of it
        L((cx, A.BACK_Y + 60.0, 150.0), color=(1.0, 0.82, 0.55), radius=150.0, intensity=0.45, id='light_back_%d' % (i + 1))
    for k, x in enumerate((-2560.0, -1860.0)):
        L((x, A.Y0 + A.WT + 14.0, 146.0), color=(1.0, 0.78, 0.45), radius=150.0, intensity=0.35, type='spot', dir=(0.0, 0.3, -1.0), inner=16.0, outer=52.0, id='light_cage_%d' % k)
    L((A.X1 - 60.0, 3900.0, 170.0), color=(1.0, 0.85, 0.55), radius=170.0, intensity=0.25, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    L((A.X0 + 70.0, 4040.0, 150.0), color=(1.0, 0.80, 0.50), radius=180.0, intensity=0.5, type='spot', dir=(0.0, -0.2, -1.0), inner=16.0, outer=52.0, id='light_d7_cage')
    L((A.X1 + 100.0, 3900.0, 200.0), color=(0.9, 0.9, 1.0), radius=160.0, intensity=0.05, id='light_vest')
    L((GAPS[0], SPINE_Y + 105.0, 118.0), color=(1.0, 0.7, 0.25), radius=190.0, intensity=0.5, id='light_kiosk')          # under the canopy
    for k, x in enumerate(COLS):                                                  # a warm wash on each column's two faces (they were flat grey)
        L((x, SPINE_Y - 40.0, 120.0), color=(1.0, 0.82, 0.6), radius=110.0, intensity=0.2, id='light_colS_%d' % k)
        L((x, SPINE_Y + 40.0, 120.0), color=(1.0, 0.82, 0.6), radius=110.0, intensity=0.2, id='light_colN_%d' % k)
    report['lights'] = n
    assert n <= LIGHT_CAP, n


# ------------------------------------------------------------------------------------------------ main
def dress(A, m, stage='full', foreign=None):
    D = R2.D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    R3.shutters(A, m, report)
    floor4(A, m, D, report)
    wall_bands4(A, m, D, report)
    R3.fronts_and_doors(A, m, D, report)
    ceiling4(A, m, D, report)
    spine4(A, m, D, report)
    R3.wall_props(A, m, D)
    report['stock'] = {}
    for i in range(5):
        report['stock'][A.BAYS[i]] = shop(A, m, D, i, report)
    R3.d7_props(A, D)
    ceiling_props4(A, D)
    corridor_dense(A, m, D, report)
    lights4(A, m, report)
    m.use('cameras')
    for k in range(5):
        a0, a1 = A.aperture(k)
        B.camera(m, 'sign_%d' % (k + 1), ((a0 + a1) / 2.0, 4090.0, 165.0), 90.0, id='sign_%d' % (k + 1))
    models = {p['model'] for p in m.flat().props}
    report['distinct_models'] = len(models)
    report.update({'props': len(m.flat().props), 'by_area': R3.counts(m, A), 'skipped': D.skipped, 'foreign_models': D.foreign, 'failed': D.failed[:80]})
    m.dress_report = report
    m.dresser = D
    return report
