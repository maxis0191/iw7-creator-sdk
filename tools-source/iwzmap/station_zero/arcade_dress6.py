"""arcade_dress6: the Underpass Arcade, round 6, on top of arcade_dress5. Round 5's blind review (ours 5.9, stock 6.8; weakest: D7 4.0, inside bay 3 4.3, south wall 4.9,
spine island 5.2) named: a mirrored rusty panel behind the D7 pillar, flat pink shelves in bay 3, a big grey planter block, a kiosk of flat colour planes, black smears on the
floor, hard black ceiling slabs and flat ducts, pastel washes on the shop fronts with no source. Round 6:
  D7        an asymmetric door (a rusty plated leaf, a second leaf of another material with a wheel, a hazard door frame), the pillar's foot piled with crates, barrels, sandbags, hose;
  bay 3     shelving in real materials (steel, painted wood), a second stock row of themed models on every unit, the barrel and crate that stood in the back shelf moved out;
  planter   a stock wooden planter model with stock plants instead of a grey box;
  kiosk     cinder block body with a tile band, a corrugated roof on rafters, a fascia, a stock display case and machines on the counter;
  ceiling   the beams, rails, lips and boxes that were black are steel or concrete; ducts alternate rectangular and round, with bands and hangers;
  light     the shop colour comes from the sign, a neon tube round the aperture and the shop lamp; the washes and fills are warm white;
  floor     round 5's out-spot of every shop is a low omni again (round 4 had no smears with it), fewer wear decals.
"""
import math
import os
import random

import arcade_dress as R1
import arcade_dress2 as R2
import arcade_dress3 as R3
import arcade_dress4 as D4
import arcade_dress5 as D5
from studio import build as B

M, HUE, TUBE = D4.M, D4.HUE, D4.TUBE
box = R2.box
DARK = D5.DARK
GAPS, COLS, PIERS, SPINE_Y = D4.GAPS, D4.COLS, D4.PIERS, D4.SPINE_Y
tp = D5.tp
make_pictures = D4.make_pictures
STEEL = 'w/metal_painted_04'
M.update(planter_w='container_wood_planter_01', display='park_concessions_cart_food_display_glass', sandbag='dns_sandbag01_singleflat_iw6', sandbag2='dns_sandbag01_singlebent_iw6',
         plant_big='com_potted_plant_small_des', duct_r='vent_duct_round_128_md', shelf_i='p7_shelf_industrial_gray_48', cart_c='park_concessions_cart_cluster')
R3.BOARD.update(photo='w/metal_galvanized_bare_dark_01', heel='w/wood_antique_panel_trim_01', hole9='w/wood_worn_painted_01_green', copy='w/metal_galvanized_bare_dark_01',
                needle='w/wood_antique_panel_trim_01')
EXTRA = {'photo': ['p7_picture_frame_fancy_04', 'p7_picture_frame_modern_02', 'me_picture11', 'cp_rave_quest_photo_01', 'cp_rave_quest_photo_02', 'cp_town_videocamera', 'cp_disco_film_reel_case'],
         'heel': ['dns_locker_set_01', 'p7_54i_gear_shoes', 'dns_toolbox_small_iw6', 'p7_tools_nail', 'com_padlock', 'p7_54i_gear_shoes'],
         'hole9': ['glass_beer_bottle_fn_01_dlc1', 'p7_glassware_wine_01', 'cp_disco_pizza_box_stack', 'misc_ashtray', 'p7_bottle_glass_liquor_04', 'p7_cup_glass'],
         'copy': ['com_copypaper_box', 'office_paper_stack01_iw6', 'base_book_group_06a', 'zombies_clipboard_wpaper', 'com_office_book_red_flat', 'com_copypaper_box_open'],
         'needle': ['cp_disco_record_milk_crate', 'cp_disco_record_sleeve_02', 'lag_portable_radio', 'cp_town_tape_recorder', 'cp_disco_film_reel_case', 'cp_disco_monitor_speaker']}


def retex(m, prefix, material):
    n = 0
    for layer in list(m.layers):
        for o in list(m.layers[layer]):
            if str(o['id']).startswith(prefix) and o.get('kind') == 'box':
                m.update(o['id'], material=material)
                n += 1
    return n


def drop(m, prefix):
    n = 0
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(prefix)]:
        m.remove(pid)
        n += 1
    return n


# ------------------------------------------------------------------------------------------------ ceiling
def ceiling6(A, m, D, report):
    m.use('dressing')
    n = 0
    for prefix, mat in (('beam_', 'w/concrete_wall_panel_05'), ('shutter_box_', STEEL), ('panel_rail_', STEEL), ('soffit_lip_', STEEL), ('tray_lip_', STEEL), ('sign_frame_', STEEL)):
        n += retex(m, prefix, mat)
    m.update('soffit', material='w/ch_concretewall06') if 'soffit' in m else None
    for k in range(5):                                         # a cornice under each beam: the header reads as built, not as a slab
        a0, a1 = A.aperture(k)
        box(m, [a0 - 16.0, A.Y1 - A.WT - 18.0, 208.0, a1 + 16.0, A.Y1 - A.WT, 214.0], 'w/metal_painted_scratched_yellow_02', id='cornice_%d' % (k + 1))
        for j in range(6):
            box(m, [a0 - 14.0 + (a1 - a0 + 28.0) * j / 5.0 - 0.8, A.Y1 - A.WT - 16.0, 214.0, a0 - 14.0 + (a1 - a0 + 28.0) * j / 5.0 + 0.8, A.Y1 - A.WT, 232.0], DARK, id='beam_rib_%d_%d' % (k + 1, j))
    # neon tube round every aperture: the source of the shop's colour
    for k in range(5):
        a0, a1 = A.aperture(k)
        t = TUBE[A.BAYS[k]]
        yw = A.Y1 - A.WT
        box(m, [a0 - 8.0, yw - 3.0, A.AP_H + 2.0, a1 + 8.0, yw, A.AP_H + 6.0], t, id='neon_top_%d' % (k + 1))
        box(m, [a0 - 8.0, yw - 3.0, 0.0, a0 - 4.0, yw, A.AP_H + 2.0], t, id='neon_l_%d' % (k + 1))
        box(m, [a1 + 4.0, yw - 3.0, 0.0, a1 + 8.0, yw, A.AP_H + 2.0], t, id='neon_r_%d' % (k + 1))
    report['ceiling6'] = {'retextured': n}


def ducts6(A, m, D):
    """round 4/5 put one rectangular duct model every 256 on two lines; now rectangular and round alternate, with bands, hangers and a flange at each joint"""
    for line, y in enumerate((3770.0, 4010.0)):
        x = A.X0 + 100.0 + 128.0 * line
        k = 0
        while x < A.X1 - 90.0:
            model = M['duct'] if k % 2 == 0 else M['duct_r']
            D.ceil(model, x, y, 90.0, 230.0 if k % 2 == 0 else 226.0)
            box(m, [x - 4.0, y - 17.0, 205.0, x + 4.0, y + 17.0, 238.0], 'w/metal_painted_scratched_yellow_02' if k % 3 == 0 else STEEL, id='duct_band_%d_%d' % (line, k))
            for s in (-1, 1):
                box(m, [x + s * 40.0 - 0.6, y - 14.0, 236.0, x + s * 40.0 + 0.6, y + 14.0, 256.0], DARK, id='duct_hang_%d_%d_%d' % (line, k, s))
            x += 128.0
            k += 1


# ------------------------------------------------------------------------------------------------ the D7 end
def d7_6(A, m, D, report):
    m.use('dressing')
    xw = A.X0 + A.WT
    zt = 176.0
    for pid in ('d7_slab', 'd7_foot', 'd7_band', 'd7_plate', 'd7_lamp', 'd7_label'):
        if pid in m:
            m.remove(pid)
    drop(m, 'd7_bolt_')
    drop(m, 'd7_seam_')
    drop(m, 'd7_hseam_')
    # two leaves of two materials, the right one with a wheel and a pressure plate, the left one with plate seams only: nothing mirrors
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 3902.0, zt], 'w/frag_metal_plates_rusty', id='d7_slab', uv={'east': {'tile': [64.0, 64.0]}})
    box(m, [xw + 2.0, 3902.0, 0.0, xw + 10.0, 4006.0, zt], 'w/beacon_metal_panel_wall', id='d7_slab_r', uv={'east': {'tile': [40.0, 40.0]}})
    for z in (36.0, 92.0, 140.0):
        box(m, [xw + 10.0, 3794.0, z, xw + 11.2, 3902.0, z + 2.0], DARK, id='d7_hseam_%d' % int(z))
    for k, y in enumerate((3818.0, 3846.0, 3880.0)):
        box(m, [xw + 10.0, y, 8.0, xw + 11.2, y + 2.0, zt - 6.0], DARK, id='d7_seam_%d' % k)
    box(m, [xw + 10.0, 3902.0, 0.0, xw + 12.0, 3904.0, zt], DARK, id='d7_split')
    # the wheel (a ring of boxes) and the bolts on the right leaf
    cy, cz = 3954.0, 92.0
    for a in range(0, 360, 45):
        r = math.radians(a)
        box(m, [xw + 10.0, cy + 18.0 * math.cos(r) - 3.0, cz + 18.0 * math.sin(r) - 3.0, xw + 15.0, cy + 18.0 * math.cos(r) + 3.0, cz + 18.0 * math.sin(r) + 3.0], 'w/metal_painted_scratched_yellow_02', id='d7_wheel_%d' % a)
    box(m, [xw + 10.0, cy - 4.0, cz - 4.0, xw + 17.0, cy + 4.0, cz + 4.0], DARK, id='d7_hub')
    for k, (dy, dz) in enumerate(((-34.0, 40.0), (34.0, 40.0), (-34.0, 140.0), (34.0, 140.0), (0.0, 150.0))):
        box(m, [xw + 10.0, cy + dy - 3.0, dz - 3.0, xw + 13.0, cy + dy + 3.0, dz + 3.0], STEEL, id='d7_nut_%d' % k)
    box(m, [xw + 10.0, 3820.0, 108.0, xw + 11.5, 3860.0, 120.0], 'w/signage_decals_corridor_01', id='d7_label')
    box(m, [xw + 10.0, 3981.0, 148.0, xw + 14.0, 3995.0, 162.0], TUBE['needle'], id='d7_lamp')
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 12.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    for z, mat in ((88.0, 'w/metal_painted_scratched_yellow_02'),):
        box(m, [xw + 10.0, 3790.0, z, xw + 13.0, 3902.0, z + 10.0], mat, id='d7_band')
    box(m, [xw + 9.0, 3788.0, 0.0, xw + 14.0, 3794.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_l')
    box(m, [xw + 9.0, 4006.0, 0.0, xw + 14.0, 4012.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_r')
    box(m, [xw + 9.0, 3788.0, zt, xw + 14.0, 4012.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_t')
    # the pillar's foot (the pillar stands 180 in front of the door): crates, barrels, sandbags, a hose, a leaning plank
    cx = COLS[0]
    rng = random.Random(99)
    D.put(M['crate3'], cx - 46.0, SPINE_Y - 22.0, 12.0, margin=0.0, ignore_keep=True)
    D.put(M['crate2'], cx - 44.0, SPINE_Y - 20.0, 30.0, z=49.0, margin=0.0, ignore_keep=True, clip=False)
    D.put(M['barrel2'], cx - 40.0, SPINE_Y + 34.0, 0.0, margin=0.0, ignore_keep=True)
    D.put(M['barrel3'], cx - 6.0, SPINE_Y + 46.0, 0.0, margin=0.0, ignore_keep=True)
    for k in range(5):
        D.put(M['sandbag'] if k % 2 else M['sandbag2'], cx + 26.0 + 8.0 * (k % 2), SPINE_Y - 30.0 + 14.0 * k, rng.uniform(0, 360), z=8.0 * (k // 3), margin=0.0, ignore_keep=True, clip=False)
    D.put(M['hose'], cx + 6.0, SPINE_Y - 44.0, 20.0, margin=0.0, ignore_keep=True, clip=False)
    D.put(M['wet'], cx - 70.0, SPINE_Y + 6.0, 80.0, margin=0.0, ignore_keep=True, clip=False)
    tp(D, 'com_wooden_pallet', cx + 40.0, SPINE_Y + 2.0, 12.0, 90.0, roll=-76.0)
    for k in range(7):
        D.put(rng.choice((M['cup'], M['can'], M['paper'], M['chips'])), cx + rng.uniform(-70.0, 60.0), SPINE_Y + rng.uniform(-60.0, 60.0), rng.uniform(0, 360), margin=0.0, ignore_keep=True, clip=False)
    # the end wall each side of the door (as round 5) and the pipes
    for s in (-1, 1):
        for z in (60.0, 124.0):
            y0, y1 = (4012.0, A.Y1 - A.WT) if s > 0 else (A.Y0 + A.WT, 3788.0)
            box(m, [xw, y0, z, xw + 5.0, y1, z + 5.0], 'w/metal_painted_scratched_yellow_02' if z < 100 else STEEL, id='d7_pipe_%d_%d' % (s, int(z)))
    for s, (y0, y1) in enumerate(((A.Y0 + A.WT + 20.0, 3770.0), (4030.0, A.Y1 - A.WT - 20.0))):
        mid = (y0 + y1) / 2.0
        box(m, [xw, mid - 40.0, 70.0, xw + 3.0, mid + 40.0, 160.0], 'w/wood_antique_panel_trim_01', id='d7_board_%d' % s)
        for j, (dy, dz) in enumerate(((-24.0, 120.0), (6.0, 128.0), (28.0, 104.0), (-8.0, 92.0))):
            B.decal(m, D4.POSTERS[(s * 3 + j) % len(D4.POSTERS)], (xw + 3.0, mid + dy, dz), (1.0, 0.0, 0.0), (22.0, 30.0), rot=(-3.0, 4.0, 1.0, 6.0)[j], id='d7_notice_%d_%d' % (s, j))
        box(m, [xw, y0, 0.0, xw + 1.5, y1, 40.0], 'w/ceramic_tile_01_orange', id='d7_wain_%d' % s)
        box(m, [xw, y0, 40.0, xw + 2.0, y1, 43.0], DARK, id='d7_rail_%d' % s)
    D.wall(M['lockers'], 'w', 3560.0, tag='d7_lock0')
    D.wall(M['lockers'], 'w', 3585.0, tag='d7_lock1')
    D.wall(M['fcab'], 'w', 4230.0, tag='d7_fcab')
    D.wall(M['bench'], 'w', 4180.0, tag='d7_bench')
    report['d7'] = 'two leaves of two materials, a wheel, a hazard frame, the pillar foot piled'


# ------------------------------------------------------------------------------------------------ the spine island and the planter
def kiosk6(A, m, D, report):
    m.use('dressing')
    kx, ky = GAPS[0], SPINE_Y + 105.0
    x0, x1, y0, y1 = kx - 48.0, kx + 48.0, ky - 32.0, ky + 32.0
    for pid in ('kseam_s_14', 'kseam_s_28', 'kseam_n_14', 'kseam_n_28', 'kmenu_s', 'kmenu_n', 'kapron', 'kcanopy_trim'):
        if pid in m:
            m.remove(pid)
    drop(m, 'kvert_')
    m.update('kiosk_base', material='w/brick_cinderblock_04_beige_dirty')
    m.update('kiosk_canopy', material='w/metal_corrugated_01')
    for pid in ('kiosk_back_n', 'kiosk_back_s'):
        m.update(pid, material='w/wood_antique_panel_trim_01')
    for k in range(4):
        m.update('kiosk_post_%d' % k, material=STEEL)
    box(m, [x0 - 1.0, y0 - 1.5, 6.0, x1 + 1.0, y0, 38.0], 'w/ceramic_tile_01_orange', id='k_tile_s', uv={'south': {'tile': [24.0, 24.0]}})
    box(m, [x0 - 1.0, y1, 6.0, x1 + 1.0, y1 + 1.5, 38.0], 'w/ceramic_tile_01_orange', id='k_tile_n', uv={'north': {'tile': [24.0, 24.0]}})
    box(m, [x0 - 1.5, y0 - 2.0, 38.0, x1 + 1.5, y0, 44.0], STEEL, id='k_edge_s')
    box(m, [x0 - 1.5, y1, 38.0, x1 + 1.5, y1 + 2.0, 44.0], STEEL, id='k_edge_n')
    for k in range(6):                                      # rafters under the corrugated roof, a fascia and a drip edge
        box(m, [x0 - 8.0 + k * 38.0, y0 - 8.0, 98.0, x0 - 6.0 + k * 38.0, y1 + 8.0, 100.0], DARK, id='k_rafter_%d' % k)
    box(m, [x0 - 9.0, y0 - 9.0, 103.0, x1 + 9.0, y0 - 7.0, 112.0], 'w/metal_painted_scratched_yellow_02', id='k_fascia_s')
    box(m, [x0 - 9.0, y1 + 7.0, 103.0, x1 + 9.0, y1 + 9.0, 112.0], 'w/metal_painted_scratched_yellow_02', id='k_fascia_n')
    box(m, [x0 - 9.0, y0 - 9.0, 103.0, x0 - 7.0, y1 + 9.0, 112.0], 'w/metal_painted_scratched_yellow_02', id='k_fascia_w')
    box(m, [x1 + 7.0, y0 - 9.0, 103.0, x1 + 9.0, y1 + 9.0, 112.0], 'w/metal_painted_scratched_yellow_02', id='k_fascia_e')
    box(m, [kx - 22.0, y0 - 1.6, 56.0, kx + 22.0, y0, 94.0], 'w/signage_theater_menu_01', id='k_menu_s')
    box(m, [kx - 22.0, y1, 56.0, kx + 22.0, y1 + 1.6, 94.0], 'w/zombies_theater_poster01', id='k_menu_n')
    box(m, [x0 - 14.0, y0 - 14.0, 0.0, x1 + 14.0, y1 + 14.0, 1.3], 'w/beacon_lab_floor_tile_01', id='k_apron', uv={'top': {'tile': [32.0, 32.0]}})
    D.put(M['display'], kx + 8.0, ky - 14.0, 0.0, z=47.0, margin=0.0, ignore_keep=True, clip=False)
    D.put(M['cart_c'], x1 + 70.0, ky + 6.0, 100.0, margin=1.0)
    D.put(M['gum'], x0 - 24.0, y0 + 6.0, 0.0, margin=0.0, ignore_keep=True)
    # the planter: a stock wooden planter and stock plants instead of the grey block
    px = GAPS[2]
    for pid in ('planter_box', 'planter_rim', 'planter_soil'):
        if pid in m:
            m.remove(pid)
    plants = [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and abs(o['origin'][0] - px) < 75.0 and abs(o['origin'][1] - SPINE_Y) < 30.0
              and 37.0 <= o['origin'][2] <= 41.0]
    for pid in plants:
        m.remove(pid)
    B.prop(m, M['planter_w'], (px, SPINE_Y, 0.0), angles=[0.0, 90.0, 0.0], zone='arcade', id='planter6')
    D5.D4.foot(D, px - 78.0, SPINE_Y - 40.0, px + 78.0, SPINE_Y + 40.0)
    for j, du in enumerate((-48.0, -14.0, 20.0, 52.0)):
        D.put((M['plant_big'], M['planter2'], 'flower_shop_planter_02', M['plant_big'])[j], px + du, SPINE_Y + (6.0 if j % 2 else -6.0), 40.0 * j, z=34.0, margin=0.0, ignore_keep=True, clip=False,
              scale=(1.3, 1.0, 1.2, 1.0)[j])
    report['kiosk6'] = 'cinder block, tile band, corrugated roof; planter from a stock model (%d old plants removed)' % len(plants)


# ------------------------------------------------------------------------------------------------ the shops
def shop6(A, m, D, i, report):
    n = D5.shop5(A, m, D, i, report)
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    yp = A.BACK_Y
    wallb = A.Y1 + A.BAY_D - A.WT
    U = lambda u: s + u
    drop(m, 'p') if False else None
    for pid in [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and ('bk_barrel_%d' % i in o['id'] or 'bk_crate_%d' % i in o['id'])]:
        m.remove(pid)
    D.put(M['barrel'], U(30.0), A.BACK_Y + 36.0, 0.0, margin=1.0, clip=False)
    D.put(M['crate3'], U(290.0), A.BACK_Y + 36.0, 8.0, margin=1.0, clip=False)
    rng = random.Random(40 + i)
    models = EXTRA[kind]
    # a second row on every unit (themed stock models, both edges of the board), over the levels the first row left
    lv = (24.0, 46.0, 68.0, 90.0, 112.0, 134.0, 156.0)
    placed = 0
    for (u0, u1) in ((18.0, 116.0), (204.0, 302.0)):
        for z in lv:
            t = U(u0) + 8.0
            while t < U(u1) - 8.0:
                mod = rng.choice(models)
                yy = yp - (8.0 if rng.random() < 0.5 else 24.0)
                if rng.random() < 0.78 and D.put(mod, t, yy, 270.0 + rng.uniform(-18.0, 18.0), z=z, ignore_keep=True, margin=0.0, scale=1.25, clip=False):
                    placed += 1
                t += rng.uniform(14.0, 24.0)
    # the back-room middle unit
    for z in (22.0, 50.0, 78.0, 106.0):
        t = U(122.0)
        while t < U(198.0):
            if D.put(rng.choice(['boxc', 'boxa', 'crate2'] and [M['boxc'], M['boxa'], M['crate2'], M['bag']]), t, wallb - 12.0, 270.0 + rng.uniform(-10.0, 10.0), z=z, ignore_keep=True, margin=0.0, clip=False):
                placed += 1
            t += rng.uniform(20.0, 30.0)
    return n + placed


# ------------------------------------------------------------------------------------------------ light
def lights6(A, m, report):
    D5.lights5(A, m, report)
    for i in range(5):
        pid = 'light_out_%d' % (i + 1)
        o = m.get(pid)
        cx = A.BAY_X[i] + A.BAY_W / 2.0
        m.remove(pid)
        hue = HUE[A.BAYS[i]]
        B.light(m, (cx, A.Y1 - 36.0, 60.0), color=hue, radius=190.0, intensity=0.8, id='light_spill2_%d' % (i + 1))
    for i in range(5):                                      # washes and fills are warm white: the colour comes from the sign, the neon tube and the lamp
        for pid in ('light_wash_%d_0' % (i + 1), 'light_wash_%d_1' % (i + 1)):
            m.update(pid, color=[1.0, 0.9, 0.74])
        m.update('light_fill_%d' % (i + 1), color=[1.0, 0.88, 0.7])
        m.update('light_spill_%d' % (i + 1), intensity=0.2)
    report['lights'] = report['lights']


def dress(A, m, stage='full', foreign=None):
    D = R2.D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    R3.shutters(A, m, report)
    D5.floor5(A, m, D, report)
    drop_ids = [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(('wear_', 'puddle_'))]
    for pid in drop_ids:
        k = int(pid.split('_')[-1])
        if (pid.startswith('wear_') and k >= 8) or (pid.startswith('puddle_') and k >= 4):
            m.remove(pid)
    D4.wall_bands4(A, m, D, report)
    R3.fronts_and_doors(A, m, D, report)
    D4.ceiling4(A, m, D, report)
    ceiling6(A, m, D, report)
    D4.spine4(A, m, D, report)
    D5.pillars5(A, m, D, report)
    kiosk6(A, m, D, report)
    d7_6(A, m, D, report)
    R3.wall_props(A, m, D)
    report['stock'] = {}
    for i in range(5):
        report['stock'][A.BAYS[i]] = shop6(A, m, D, i, report)
    R3.d7_props(A, D)
    R3.ceiling_props(A, D)
    ducts6(A, m, D)
    for line, y in enumerate((3600.0, 4220.0)):
        x = A.X0 + 160.0
        while x < A.X1 - 90.0:
            D.ceil(M['pipe'], x, y, 90.0, 232.0)
            x += 128.0
    D5.fixtures5(A, D)
    D5.stories5(A, m, D, report)
    lights6(A, m, report)
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
