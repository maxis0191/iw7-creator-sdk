"""arcade_dress5: the dressing and the light of the Underpass Arcade, round 5 (called by arcade5.build_arcade). Builds on arcade_dress4 and replaces what round 4's blind
review (ours 5.0, stock 8.0) named:
  floor      one grid -> a base tile with worn wet lane centres, a concrete edge, a tiled apron before every shop, drain strips, concrete patches, puddles (wet asphalt) and wear decals;
  props      evenly spread cones and cups -> stories with a reason (a wet patch with its sign, mop and drips; a newspaper bundle at the kiosk; a fallen chair group; a spilled stall;
             an overflowing bin; a barrier with a missing cone); toppled props are real angles;
  surfaces   kiosk, columns, the D7 door and its walls: seams, vents, conduits, plates, guard rails, notices; textured materials; the black trims are a textured dark grey;
  light      each lit shop throws a spot out of its opening onto the corridor floor (in the bake); the live panels carry real fluorescent fixtures; dead panels are pale, not black slabs;
  frames     bay 3 inside: textured walls, a continuous stocked back room, headers and dividers on the shelves; D7: a plated blast door, notice boards, pipes and lockers on its wall.
"""
import math
import os
import random

import arcade_dress as R1
import arcade_dress2 as R2
import arcade_dress3 as R3
import arcade_dress4 as D4
from studio import build as B

M, HUE, TUBE = D4.M, D4.HUE, D4.TUBE
box = R2.box
GAPS, COLS, PIERS, SPINE_Y = D4.GAPS, D4.COLS, D4.PIERS, D4.SPINE_Y
DARK = 'w/micro_metal_painted_01_dark_gray'
R3.BLACK = D4.BLACK = DARK                                   # the trims: textured dark grey instead of flat black
D4.KEY_I, D4.WASH_I, D4.FILL_I, D4.SPILL_I, D4.POOL_I = (float(os.environ.get('ARC5_KEY', '1.0')), float(os.environ.get('ARC5_WASH', '0.9')), 0.25, 0.45, 1.8)
M.update(fluo='cp_disco_fluorescent_light_on', hang='hanging_light_iw6_beige', glass='brokenglass_pile02', debris='com_debris_paper_iw6_02', extg='fac_metal_extinguisher_02',
         ventp='cnd_electric_panels_vent_01_fac', barrier2='cp_disco_subway_construction_barrier_01', mopb='com_janitor_bucket_mop_iw6', hose='crr_hose_slant_gray')
make_pictures = D4.make_pictures


def tp(D, model, x, y, z, yaw, pitch=0.0, roll=0.0, scale=1.0):
    """a prop at a free angle (toppled, leaning): placed directly, no footprint check"""
    D.m.use('dressing')
    B.prop(D.m, model, (round(x, 2), round(y, 2), round(z, 2)), angles=[pitch, yaw, roll], scale=scale, zone='arcade')
    D.n += 1


# ------------------------------------------------------------------------------------------------ floor
def floor5(A, m, D, report):
    m.use('dressing')
    rng = random.Random(55)
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    uv = lambda t: {'top': {'tile': [t, t]}}
    box(m, [cx0, cy0, 0.0, cx1, cy1, 1.0], A.FLOOR_SKIN, id='floor_tile', uv=uv(40.0))
    for k, (y0, y1) in enumerate(((cy0, cy0 + 26.0), (cy1 - 26.0, cy1))):
        box(m, [cx0, y0, 0.0, cx1, y1, 1.5], 'w/fac_tile_black_01', id='floor_border_%d' % k, uv=uv(32.0))
    n = 0
    for k, y0 in enumerate((cy0 + 26.0, cy1 - 70.0)):                      # a concrete edge along each wall in broken lengths
        x = cx0
        while x < cx1 - 40.0:
            w = rng.uniform(140.0, 420.0)
            box(m, [x, y0, 0.0, min(x + w, cx1), y0 + rng.uniform(22.0, 30.0), 1.25], 'w/aq_stone_concrete_patch02', id='edge_%d_%d' % (k, n), uv=uv(48.0))
            x += w + rng.uniform(0.0, 180.0)
            n += 1
    for k, yc in enumerate(((cy0 + 3850.0) / 2.0, (3950.0 + cy1) / 2.0)):  # the worn lane centres: wet asphalt, in lengths with gaps
        x = cx0 + rng.uniform(0.0, 120.0)
        while x < cx1 - 60.0:
            w = rng.uniform(180.0, 460.0)
            half = rng.uniform(30.0, 46.0)
            off = rng.uniform(-14.0, 14.0)
            box(m, [x, yc + off - half, 0.0, min(x + w, cx1), yc + off + half, 1.3], 'w/asphalt_flooring_01_wet', id='lane_%d_%d' % (k, n), uv=uv(44.0))
            x += w + rng.uniform(50.0, 200.0)
            n += 1
        for sgn in (-1, 1):                                                 # the orange line, broken
            x = cx0
            while x < cx1 - 30.0:
                w = rng.uniform(90.0, 260.0)
                box(m, [x, yc + sgn * 52.0 - 2.0, 0.0, min(x + w, cx1), yc + sgn * 52.0 + 2.0, 1.6], 'w/plastic_slick_floor_01_orange', id='inlay_%d_%d_%d' % (k, sgn, n), uv=uv(24.0))
                x += w + rng.uniform(40.0, 130.0)
                n += 1
    for k in range(5):                                                      # the tiled apron before each shop
        a0, a1 = A.aperture(k)
        box(m, [a0 - 24.0, cy1 - 150.0, 0.0, a1 + 24.0, cy1 - 26.0, 1.35], 'w/beacon_lab_floor_tile_02_black', id='apron_%d' % (k + 1), uv=uv(32.0))
        box(m, [a0, cy1 - 46.0, 1.35, a1, cy1 - 26.0, 1.9], 'w/fac_rubber_mat_black', id='mat_%d' % (k + 1))
        box(m, [a0 - 4.0, cy1 - 24.0, 0.0, a1 + 4.0, cy1 - 20.0, 1.8], 'w/metal_painted_scratched_yellow', id='threshold_%d' % (k + 1))
    for k in range(7):                                                      # drain strips
        x = cx0 + 120.0 + rng.uniform(0.0, 1500.0)
        y = rng.choice((3560.0, 3780.0, 4020.0, 4250.0))
        box(m, [x, y, 0.0, x + rng.uniform(90.0, 150.0), y + 8.0, 1.45], 'w/metal_deck_painted_black_01', id='drain_%d' % k)
    for k in range(8):                                                      # patches of bare concrete where the tile is gone
        x, y = rng.uniform(cx0 + 40.0, cx1 - 200.0), rng.uniform(cy0 + 40.0, cy1 - 200.0)
        box(m, [x, y, 0.0, x + rng.uniform(40.0, 90.0), y + rng.uniform(30.0, 70.0), 1.15], 'w/aq_stone_concrete_patch02', id='patch_%d' % k, uv=uv(32.0))
    for k in range(10):                                                     # puddles are decals (a glossy box drew black: FE9)
        B.decal(m, 'w/dirt_stain_water_drips_01', (rng.uniform(cx0 + 60.0, cx1 - 200.0), rng.choice((3640.0, 3760.0, 4000.0, 4120.0, 4200.0)) + rng.uniform(-20.0, 20.0), 1.97), (0.0, 0.0, 1.0), (rng.uniform(60.0, 110.0), rng.uniform(40.0, 80.0)), rot=rng.uniform(0, 360), id='puddle_%d' % k)
    for k in range(6):
        x = cx0 + 160.0 + k * 300.0
        box(m, [x - 1.0, cy0, 0.0, x + 1.0, cy1, 1.75], DARK, id='joint_%d' % k)
    for k in range(26):                                                     # wear decals
        B.decal(m, ('w/dirt_stain_water_drips_01', 'w/wall_stain_01_dec', 'w/dirt_stain_water_drips_01')[k % 3],
                (rng.uniform(cx0 + 60.0, cx1 - 60.0), rng.uniform(cy0 + 60.0, cy1 - 60.0), 1.95), (0.0, 0.0, 1.0), (rng.uniform(40.0, 90.0), rng.uniform(36.0, 80.0)),
                rot=rng.uniform(0, 360), id='wear_%d' % k)
    report['floor'] = {'materials': ['gray glossy tile', 'wet asphalt', 'bare concrete', 'ceramic apron', 'black tile border', 'deck drain'], 'pieces': n}


# ------------------------------------------------------------------------------------------------ the corridor: stories
def stories5(A, m, D, report):
    m.use('dressing')
    rng = D.rng
    bank = []
    for k in range(5):
        bank.append(D.wall(M['arcade'] if k % 2 == 0 else M['arcade2'], 's', -2700.0 + 38.0 * k, tag='cab%d' % k))
    D.wall(M['claw'], 's', -2500.0, tag='claw0')
    D.wall(M['gum'], 's', -2530.0, tag='gum0')
    D.wall(M['gum'], 's', -2160.0, tag='gum1')
    D.wall(M['claw'], 's', -1250.0, tag='claw1')
    D.wall(M['dump'], 's', -2020.0, tag='dump_s')

    def cluster(x, y, n, r, kinds, lane=False):
        k = 0
        for _ in range(n):
            ang = rng.uniform(0.0, 6.283)
            rr = abs(rng.gauss(0.0, r))
            if D.put(rng.choice(kinds), x + math.cos(ang) * rr, y + math.sin(ang) * rr, rng.uniform(0, 360), margin=0.5, clip=False, ignore_keep=lane):
                k += 1
        return k
    small = [M['cup'], M['can'], M['paper'], M['chips'], M['smokes'], M['mug']]
    # 1. a wet patch in the south lane with its sign, mop and bucket, drips of litter and a trail of cups
    D.put(M['wet'], -2455.0, 3702.0, 20.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['mopb'], -2380.0, 3696.0, 70.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['mop'], -2368.0, 3712.0, 10.0, margin=0.0, clip=False, ignore_keep=True)
    cluster(-2430.0, 3680.0, 5, 28.0, small, True)
    # 2. a newspaper bundle at the kiosk: a tied stack, loose sheets, a cold cup on the step
    kx, ky = GAPS[0], SPINE_Y + 105.0
    D.put(M['stackp'], kx + 70.0, ky - 52.0, 15.0, margin=0.0, clip=False)
    D.put(M['stackp'], kx + 70.0, ky - 52.0, 40.0, z=6.0, margin=0.0, clip=False, ignore_keep=True)
    cluster(kx + 82.0, ky - 70.0, 6, 22.0, [M['paper'], M['paper'], M['mags']])
    D.put(M['cup'], kx - 30.0, ky - 48.0, 0.0, margin=0.0, clip=False)
    # 3. a fallen chair group and an upset table in the north band
    tp(D, M['fchair'], -2015.0, 4062.0, 12.0, 30.0, roll=90.0)
    tp(D, M['fchair'], -1990.0, 4040.0, 12.0, 120.0, roll=88.0)
    D.put(M['fchair'], -1962.0, 4072.0, 200.0, margin=0.0, clip=False)
    tp(D, M['ftable'], -2040.0, 4025.0, 16.0, 70.0, roll=80.0)
    cluster(-2000.0, 4050.0, 5, 30.0, small)
    # 4. a stall that lost a crate: goods on the floor round it
    sx, sy = -1860.0, 3790.0
    D.put(M['ftable'], sx, sy, 0.0, tag='stallA', margin=2.0)
    for j in range(3):
        D.on('stallA', rng.choice((M['crackers'], M['donuts'], M['mug'])), (j - 1) * 20.0, 0.0, rng.uniform(0, 360))
    tp(D, M['crate1'], sx + 48.0, sy + 10.0, 12.0, 40.0, roll=90.0)
    cluster(sx + 60.0, sy + 6.0, 9, 26.0, [M['crackers'], M['donuts'], M['boxc'], M['mug'], M['chips']])
    # 5. a second stall, tidy, with its chair and a rolled-up awning pole
    D.put(M['ftable'], -2280.0, 3770.0, 90.0, tag='stallB', margin=2.0)
    for j in range(4):
        D.on('stallB', rng.choice((M['mags'], M['cup'], M['boxc'], M['books'])), 0.0, (j - 1.5) * 16.0, rng.uniform(0, 360))
    D.put(M['fchair'], -2240.0, 3772.0, 180.0, margin=0.5)
    D.put(M['cart2'], -1420.0, 3800.0, 110.0, tag='cart1', margin=2.0)
    # 6. an overflowing bin on the south wall: bags slumped, cans round it
    D.wall(M['bin1'], 's', -2800.0, tag='bin_over')
    for j in range(3):
        D.put(M['bag'], -2800.0 + rng.uniform(-30.0, 30.0), 3548.0 + rng.uniform(6.0, 28.0), rng.uniform(0, 360), scale=0.7, margin=0.0, clip=False)
    cluster(-2800.0, 3560.0, 6, 24.0, [M['can'], M['chips'], M['paper']])
    # 7. a barrier with a cone missing and a dropped tape: the north band, mid hall
    D.put(M['barrier2'], -1700.0, 4098.0, 8.0, tag='barr', margin=1.0)
    D.put(M['cone'], -1760.0, 4106.0, 0.0, margin=0.0)
    tp(D, M['cone'], -1636.0, 4080.0, 10.0, 0.0, roll=88.0)
    D.put(M['warn'], -1700.0, 4120.0, 180.0, margin=0.0, clip=False, ignore_keep=True)
    # 8. crates and a pallet against the south wall (two stacks, different), a barrel left apart
    D.put(M['crate3'], -1980.0, 3552.0, 4.0, tag='stkA', margin=1.0)
    D.put(M['crate2'], -1976.0, 3552.0, -6.0, on='stkA', margin=0.0)
    D.put(M['pallet'], -2400.0, 3556.0, 90.0, tag='palA', margin=1.0)
    D.put(M['boxc'], -2400.0, 3556.0, 20.0, on='palA', margin=0.0)
    D.put(M['boxa'], -2394.0, 3556.0, 80.0, z=44.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['barrel2'], -1900.0, 3560.0, 0.0, margin=1.0)
    # 9. broken glass and paper drifted against the columns' feet (windward side only: west of each column)
    for k, x in enumerate(COLS):
        if k % 2 == 0:
            D.put(M['glass'], x - 30.0, SPINE_Y + rng.uniform(-24.0, 24.0), rng.uniform(0, 360), margin=0.0, clip=False)
        cluster(x - 26.0, SPINE_Y + rng.uniform(-20.0, 20.0), rng.randint(2, 5), 16.0, [M['paper'], M['cup'], M['can']])
    # 10. north piers: leaning ladder, a hose coil, a cabinet
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        if k in (0, 5):
            D.wall(M['fcab'], 'n', mid, tag='pier_fcab%d' % k)
        if k == 2:
            tp(D, M['ladder'], mid - 24.0, A.Y1 - A.WT - 18.0, 0.0, 270.0, pitch=-8.0)
        if k == 4:
            D.put(M['hose'], mid, A.Y1 - A.WT - 22.0, 70.0, margin=0.0, clip=False)
    # the rest of litter: a few drifts at the foot of the walls, uneven
    for k in range(30):
        cluster(rng.uniform(A.X0 + 80.0, A.X1 - 80.0), rng.choice((3526.0, 3534.0, 4272.0, 4278.0, 3866.0, 3934.0)), rng.randint(4, 9), 30.0, small + [M['boxc'], M['bucket']])
    # eight more small stories at irregular places: a toppled barrel and its spill, stacked chairs, boxes dropped in a heap, a bucket with a leaning mop
    for k, (x, y) in enumerate(((-2860.0, 3740.0), (-2610.0, 4070.0), (-2330.0, 3960.0), (-2140.0, 3640.0), (-1790.0, 3720.0), (-1560.0, 4010.0), (-1340.0, 3760.0), (-2990.0 + 160.0, 4090.0))):
        kind = k % 4
        if kind == 0:
            tp(D, M['barrel'], x, y, 14.0, rng.uniform(0, 360), roll=90.0)
            cluster(x + 30.0, y, 6, 20.0, [M['chips'], M['can'], M['paper']])
        elif kind == 1:
            for j in range(3):
                D.put(M['fchair'], x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), rng.uniform(0, 360), margin=0.0, clip=False, ignore_keep=True, z=0.0 + 4.0 * j) if False else tp(D, M['fchair'], x, y, 2.0 + 10.0 * j, rng.uniform(0, 360), pitch=rng.uniform(-6, 6))
        elif kind == 2:
            for j in range(3):
                D.put(M['boxc'] if j % 2 else M['boxa'], x + rng.uniform(-22, 22), y + rng.uniform(-18, 18), rng.uniform(0, 360), margin=0.0, clip=False, ignore_keep=True)
            cluster(x, y, 4, 24.0, [M['paper'], M['mags']])
        else:
            D.put(M['bucket'], x, y, 0.0, margin=0.0, clip=False, ignore_keep=True)
            tp(D, M['mop'], x + 10.0, y + 6.0, 0.0, rng.uniform(0, 360), pitch=-70.0)
    # posters (stock poster materials) on both walls and column faces are in the column dressing
    for k in range(14):
        x = A.X0 + 90.0 + k * 126.0 + rng.uniform(-30.0, 30.0)
        B.decal(m, D4.POSTERS[k % len(D4.POSTERS)], (x, A.Y0 + A.WT, rng.uniform(130.0, 168.0)), (0.0, 1.0, 0.0), (28.0, 40.0), rot=rng.uniform(-3.0, 3.0), id='dec_post_s%d' % k)
    for k, (a, b) in enumerate(PIERS):
        B.decal(m, D4.POSTERS[(k * 2) % len(D4.POSTERS)], ((a + b) / 2.0 - 14.0 + (12.0 if k % 2 else 0.0), A.Y1 - A.WT, 150.0), (0.0, -1.0, 0.0), (28.0, 40.0), id='dec_post_n%d' % k)
    report['stories'] = {'props_total': len(m.flat().props)}


# ------------------------------------------------------------------------------------------------ pillars, kiosk, the D7 wall
def pillars5(A, m, D, report):
    m.use('dressing')
    rng = random.Random(7)
    for k, x in enumerate(COLS):
        for sgn in (-1, 1):                                  # the two faces that look along the hall (x faces): seams, vents, conduits, plates
            xf = x + sgn * 16.0
            xa, xb = (xf, xf + 1.5) if sgn > 0 else (xf - 1.5, xf)
            for z in (96.0, 134.0, 172.0):
                box(m, [xa, SPINE_Y - 16.0, z, xb, SPINE_Y + 16.0, z + 1.2], DARK, id='seam_%d_%d_%d' % (k, sgn, int(z)))
            box(m, [xa, SPINE_Y - 1.0, 64.0, xb, SPINE_Y + 1.0, 200.0], DARK, id='seam_v_%d_%d' % (k, sgn))
            kind = (k + (0 if sgn > 0 else 3)) % 4
            if kind == 0:                                    # a vent grille
                box(m, [xa, SPINE_Y - 9.0, 100.0, xb + 0.8, SPINE_Y + 9.0, 124.0], DARK, id='vent_%d_%d' % (k, sgn))
                for j in range(4):
                    box(m, [xa, SPINE_Y - 8.0, 104.0 + 5.0 * j, xb + 1.6, SPINE_Y + 8.0, 105.5 + 5.0 * j], 'w/metal_deck_painted_black_01', id='vent_s_%d_%d_%d' % (k, sgn, j))
            elif kind == 1:                                  # conduit and a junction box
                box(m, [xa, SPINE_Y + 8.0, 64.0, xb + 2.0, SPINE_Y + 10.0, 204.0], 'w/metal_painted_scratched_yellow_02', id='cond_%d_%d' % (k, sgn))
                box(m, [xa, SPINE_Y + 4.0, 120.0, xb + 3.0, SPINE_Y + 14.0, 134.0], DARK, id='junc_%d_%d' % (k, sgn))
            elif kind == 2:                                  # an enamel notice plate and a stripe
                box(m, [xa, SPINE_Y - 10.0, 120.0, xb + 0.8, SPINE_Y + 10.0, 148.0], 'w/metal_painted_scratched_yellow_02', id='plate_%d_%d' % (k, sgn))
                box(m, [xa, SPINE_Y - 12.0, 150.0, xb + 0.6, SPINE_Y + 12.0, 156.0], 'w/plastic_slick_floor_01_orange', id='pstripe_%d_%d' % (k, sgn))
            else:                                            # a stock extinguisher on a bracket
                D.put(M['extg'], xf + sgn * 6.0, SPINE_Y, 0.0 if sgn > 0 else 180.0, z=84.0, margin=0.0, ignore_keep=True, clip=False)
        if k in (1, 4):                                      # a yellow guard rail round the foot
            for (a, b, c, d) in ((x - 30.0, SPINE_Y - 30.0, x + 30.0, SPINE_Y - 28.0), (x - 30.0, SPINE_Y + 28.0, x + 30.0, SPINE_Y + 30.0),
                                 (x - 30.0, SPINE_Y - 28.0, x - 28.0, SPINE_Y + 28.0), (x + 28.0, SPINE_Y - 28.0, x + 30.0, SPINE_Y + 28.0)):
                box(m, [a, b, 22.0, c, d, 26.0], 'w/metal_painted_scratched_yellow', id='guard_%d_%d_%d' % (k, int(a), int(b)))
    # the kiosk: seams on its body, a vent, a menu board, price strips, an apron of tile at its feet
    kx, ky = GAPS[0], SPINE_Y + 105.0
    x0, x1, y0, y1 = kx - 48.0, kx + 48.0, ky - 32.0, ky + 32.0
    for z in (14.0, 28.0):
        box(m, [x0 - 0.5, y0 - 0.5, z, x1 + 0.5, y0, z + 1.2], DARK, id='kseam_s_%d' % int(z))
        box(m, [x0 - 0.5, y1, z, x1 + 0.5, y1 + 0.5, z + 1.2], DARK, id='kseam_n_%d' % int(z))
    for k in range(5):
        box(m, [x0 + 12.0 + 18.0 * k, y0 - 0.5, 0.0, x0 + 12.8 + 18.0 * k, y0, 44.0], DARK, id='kvert_%d' % k)
    box(m, [kx - 20.0, y0 - 1.5, 54.0, kx + 20.0, y0, 96.0], 'w/signage_theater_menu_01', id='kmenu_s')
    box(m, [kx - 20.0, y1, 54.0, kx + 20.0, y1 + 1.5, 96.0], 'w/zombies_theater_poster01', id='kmenu_n')
    box(m, [x0 - 14.0, y0 - 14.0, 0.0, x1 + 14.0, y1 + 14.0, 1.3], 'w/ceramic_ship_interior_tile_01', id='kapron', uv={'top': {'tile': [32.0, 32.0]}})
    box(m, [x0 + 4.0, y0 - 3.0, 100.0, x1 - 4.0, y0, 106.0], 'w/metal_painted_scratched_yellow_02', id='kcanopy_trim')
    D.put(M['ventp'], kx, ky + 31.0, 270.0, z=60.0, margin=0.0, ignore_keep=True, clip=False)
    report['pillars'] = 'seams, vents, conduits, plates, guard rails, extinguishers; kiosk seams, menus, apron'


def d7_5(A, m, D, report):
    """the D7 blast door and the wall round it (arcade_d7 looks at it from 330 units, a column in front)"""
    m.use('dressing')
    xw = A.X0 + A.WT
    zt = 176.0
    for pid in ('d7_slab', 'd7_foot', 'd7_band', 'd7_plate'):
        if pid in m:
            m.remove(pid)
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 4006.0, zt], 'w/frag_metal_plates_rusty', id='d7_slab', uv={'east': {'tile': [64.0, 64.0]}})
    for k in range(5):                                        # plate seams and rivet lines
        box(m, [xw + 10.0, 3794.0 + 44.0 * k + 22.0, 8.0, xw + 11.2, 3794.0 + 44.0 * k + 24.0, zt - 4.0], DARK, id='d7_seam_%d' % k)
    for z in (50.0, 100.0, 150.0):
        box(m, [xw + 10.0, 3794.0, z, xw + 11.2, 4006.0, z + 2.0], DARK, id='d7_hseam_%d' % int(z))
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 14.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    box(m, [xw + 10.0, 3790.0, 88.0, xw + 13.0, 4010.0, 100.0], 'w/metal_painted_scratched_yellow_02', id='d7_band')
    box(m, [xw + 10.0, 3880.0, 40.0, xw + 13.0, 3920.0, 70.0], DARK, id='d7_plate')
    box(m, [xw + 10.0, 3893.0, 120.0, xw + 14.0, 3907.0, 134.0], TUBE['needle'], id='d7_lamp')           # a status lamp (red)
    box(m, [xw + 10.0, 3890.0, 108.0, xw + 11.5, 3910.0, 116.0], 'w/signage_decals_corridor_01', id='d7_label')
    for s in (-1, 1):                                         # a pipe pair running along the wall from the door to the corners
        for z in (60.0, 124.0):
            y0, y1 = (4012.0, A.Y1 - A.WT) if s > 0 else (A.Y0 + A.WT, 3788.0)
            box(m, [xw, y0, z, xw + 5.0, y1, z + 5.0], 'w/metal_painted_scratched_yellow_02' if z < 100 else DARK, id='d7_pipe_%d_%d' % (s, int(z)))
    # the wall each side of the door: notice boards, lockers, a cabinet, a bench, hazard notices
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
    D.put(M['hose'], xw + 14.0, 3770.0, 90.0, margin=0.0, clip=False, ignore_keep=True)
    tp(D, M['ladder'], xw + 10.0, 4036.0, 0.0, 0.0, pitch=-10.0)
    for k in range(3):
        B.decal(m, 'w/signage_decals_corridor_01', (xw + 0.4, 3810.0 + 90.0 * k, 22.0), (1.0, 0.0, 0.0), (36.0, 12.0), id='d7_floor_hazard_%d' % k)
    report['d7'] = 'plated blast door, seams, status lamp, pipes, notice boards, lockers, bench'


# ------------------------------------------------------------------------------------------------ the shops: what round 4 left flat
def shop5(A, m, D, i, report):
    n = D4.shop(A, m, D, i, report)
    s = A.BAY_X[i]
    yb = A.Y1
    kind = A.BAYS[i]
    yp = A.BACK_Y
    wallb = yb + A.BAY_D - A.WT
    brd = R3.BOARD[kind]
    U = lambda u: s + u
    hue = HUE[kind]
    m.use('dressing')
    # a header board over each tall unit (the shop's colour), dividers every 24 units, a lit label strip
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        box(m, [U(u0), yp - 33.0, 172.0, U(u1), yp - 29.0, 192.0], brd, id='hdr_%d_%d' % (i + 1, side))
        box(m, [U(u0 + 4.0), yp - 34.0, 178.0, U(u1 - 4.0), yp - 33.0, 184.0], TUBE[kind], id='hdr_strip_%d_%d' % (i + 1, side))
        u = u0 + 24.0
        while u < u1 - 6.0:
            box(m, [U(u) - 0.6, yp - 32.0, 20.0, U(u) + 0.6, yp - 3.0, 170.0], DARK, id='div_%d_%d_%d' % (i + 1, side, int(u)))
            u += 24.0
    # the back room: a continuous stocked back wall (the unit in the middle faces the doorway: arc_inside_bay3 looks into it), a hanging cage lamp
    sh = R2.Shelf(m, 'bsm_%d' % i, (U(116.0), wallb - 24.0, U(204.0), wallb), 's', (22.0, 50.0, 78.0, 106.0), board=brd, top=116.0, clip=False)
    R2.stock(D, sh, ['boxc', 'crate2', 'boxa', 'crate2', 'bag', 'boxc'], 24.0, yaw=270.0, jitter=12.0, skip=0.0, scale=1.2)
    for k, u in enumerate((60.0, 160.0, 260.0)):
        D.put(M['hang'], U(u), A.BACK_Y + 56.0, 0.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)
    n += 1
    return n


# ------------------------------------------------------------------------------------------------ light
def lights5(A, m, report):
    D4.lights4(A, m, report)
    m.use('lights')
    n = report['lights']
    for i in range(5):                                       # each lit shop throws a spot out of its opening onto the corridor floor in front of it
        hue = HUE[A.BAYS[i]]
        cx = A.BAY_X[i] + A.BAY_W / 2.0
        p0 = (cx, A.Y1 + 24.0, 118.0)
        tgt = (cx, A.Y1 - 120.0, 0.0)
        d = [tgt[j] - p0[j] for j in range(3)]
        dist = math.sqrt(sum(v * v for v in d))
        d = [v / dist for v in d]
        B.light(m, p0, color=tuple(round(0.6 + 0.4 * c, 3) for c in hue), radius=380.0, intensity=1.1, type='spot', dir=tuple(d), inner=18.0, outer=58.0, id='light_out_%d' % (i + 1))
        n += 1
    report['lights'] = n
    assert n <= D4.LIGHT_CAP, n


def fixtures5(A, D):
    """a real fluorescent fixture under every live panel (the pools have an object that casts them) and a hanging lamp over the kiosk"""
    for k, (x, y, single) in enumerate(A.live):
        D.put(M['fluo'], x, y, 0.0, z=168.0, ignore_keep=True, margin=0.0, clip=False)
    D.put(M['hang'], GAPS[0], SPINE_Y + 105.0, 0.0, z=176.0, ignore_keep=True, margin=0.0, clip=False)


# ------------------------------------------------------------------------------------------------ main
def dress(A, m, stage='full', foreign=None):
    D = R2.D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    R3.shutters(A, m, report)
    floor5(A, m, D, report)
    D4.wall_bands4(A, m, D, report)
    R3.fronts_and_doors(A, m, D, report)
    D4.ceiling4(A, m, D, report)
    for k in range(4):                                       # round 4's sign bars were 42 high dark slabs: keep a thin bar at the top, the picture hangs below it
        m.remove('sbar_%d' % k)
    for k, (x, y) in enumerate(((-2400.0, 3690.0), (-1650.0, 3690.0), (-2250.0, 4130.0), (-1950.0, 4130.0))):
        box(m, [x - 52.0, y - 1.5, 216.0, x + 52.0, y + 1.5, 219.0], DARK, id='sbar_%d' % k)
    D4.spine4(A, m, D, report)
    pillars5(A, m, D, report)
    d7_5(A, m, D, report)
    R3.wall_props(A, m, D)
    report['stock'] = {}
    for i in range(5):
        report['stock'][A.BAYS[i]] = shop5(A, m, D, i, report)
    R3.d7_props(A, D)
    D4.ceiling_props4(A, D)
    fixtures5(A, D)
    stories5(A, m, D, report)
    lights5(A, m, report)
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
