"""arcade_dress7: the Underpass Arcade, round 7, on top of arcade_dress4/5/6. Round 6's blind review (ours 5.7, stock 6.7, a plateau; density equals stock): the gap is FORM and
surfaces: box-part pillars, ducts, beams and kiosks, floating ceiling cuboids, one floor grid, pastel washes without a source, bloom haze. Round 7:
  pillars    stock models (cp_disco_dojo_column_01..04) on an invisible collision clip, the posters, map case and light box on their faces;
  ceiling    stock fluorescent fixtures instead of the flat panel boxes (live ones emit in the bake), stock I-beams and brackets over the shop fronts instead of the black beam
             cuboids, stock duct supports, vents and elbows on the duct lines; the sign bars and their pictures (never visible) are gone;
  kiosk      two stock ticket booths back to back, a stock awning on I-beam posts, a stock cart; no box parts;
  floor      five zones of different stock tiles (tile scale differs) along the hall, so no one grid fills a view;
  light      every coloured light has a fixture model: the shop key hangs from two fluorescent fixtures, the aperture's spill is the neon tube, the back room has its hanging lamp, the
             kiosk, D4 and D7 have cage lamps; the washes, fills and the column lights (no fixture) are dropped;
  haze       the document's vision sets veilStrength 0 (the stock vision's veiling glare is 0.1), volumetricAirDensity 0.02 (0.13) and volumetricSpotBrightness 0.15 (0.8: the beams
             of every spot light), and exposure adjust -0.5.
"""
import math
import os
import random

import arcade_dress as R1
import arcade_dress2 as R2
import arcade_dress3 as R3
import arcade_dress4 as D4
import arcade_dress5 as D5
import arcade_dress6 as D6
from studio import build as B

M, HUE, TUBE = D4.M, D4.HUE, D4.TUBE
box = R2.box
DARK, STEEL = D5.DARK, D6.STEEL
GAPS, COLS, PIERS, SPINE_Y = D4.GAPS, D4.COLS, D4.PIERS, D4.SPINE_Y
tp = D5.tp
make_pictures = D4.make_pictures
M.update(dojo=('cp_disco_dojo_column_01', 'cp_disco_dojo_column_02', 'cp_disco_dojo_column_03', 'cp_disco_dojo_column_04'), fluo_off='cp_disco_fluorescent_light_off',
         ibeam='building_ibeam_large_long', bracket='p7_ibeam_bracket_32_t_01', post='btr_ibeam_yellow_vert_01_gray', booth='zmb_mobile_ticket_booth',
         awning='cp_disco_awnings_rounded', duct_sup='duct_metal_rectangle_ceiling_support', duct_vent='duct_metal_rectangle_vent', duct_elb='duct_metal_rectangle_elbow_down_90',
         cage='p7_lights_cagelight02_on', cart='park_concessions_cart')
DOJO = os.environ.get('ARC7_COLUMNS', 'dojo') == 'dojo'
DOJO_SCALE = 0.77             # 332 high -> 255.6: the column fills the hall's height


def put_model(D, model, x, y, yaw, z=0.0, scale=1.0, emissive=None):
    """a stock model by its bounds' centre, no footprint check (structure)"""
    return D.put(model, x, y, yaw, z=z, scale=scale, ignore_keep=True, margin=0.0, clip=False, emissive=emissive)


# ------------------------------------------------------------------------------------------------ pillars
def column7(A, m, D, k, x):
    """a stock column on a clip; round 4/5's face features move out to the model's faces"""
    spec = D4.COLSPEC[k]
    B.clip(m, [x - 20.0, SPINE_Y - 20.0, 0.0, x + 20.0, SPINE_Y + 20.0, 256.0], id='col_clip_%d' % k)
    mod = M['dojo'][k % 4]
    mn, mx = D.bounds(mod)
    sc = DOJO_SCALE
    D.put(mod, x, SPINE_Y, 90.0 * (k % 4), z=0.0, scale=sc, ignore_keep=True, margin=0.0, clip=False)
    D4.foot(D, x - 24.0, SPINE_Y - 24.0, x + 24.0, SPINE_Y + 24.0)
    half = 15.0                         # the shaft of the stock column is about 28 across at this scale: the boards sit on it (the footprint of the base is wider)
    f = spec['feature']
    for sgn in (-1, 1):
        yf = SPINE_Y + sgn * half
        y0, y1 = (yf, yf + 1.5) if sgn > 0 else (yf - 1.5, yf)
        if f == 'map':
            box(m, [x - 13.0, y0, 88.0, x + 13.0, y1, 146.0], DARK, id='col_mapframe_%d_%d' % (k, sgn))
            y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
            box(m, [x - 11.0, y2[0], 92.0, x + 11.0, y2[1], 142.0], 'w/zombies_underground_map', id='col_map_%d_%d' % (k, sgn))
        elif f == 'lightbox':
            box(m, [x - 13.0, y0, 84.0, x + 13.0, y1, 150.0], DARK, id='col_lbframe_%d_%d' % (k, sgn))
            y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
            box(m, [x - 11.0, y2[0], 88.0, x + 11.0, y2[1], 146.0], TUBE['photo'] if sgn > 0 else TUBE['heel'], id='col_lb_%d_%d' % (k, sgn))
        elif f in ('poster', 'poster2'):
            for j, zz in enumerate((90.0, 134.0)):
                box(m, [x - 11.0, y0, zz, x + 11.0, y1, zz + 38.0], DARK, id='col_pframe_%d_%d_%d' % (k, sgn, j))
                y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
                box(m, [x - 9.5, y2[0], zz + 1.5, x + 9.5, y2[1], zz + 36.5], D4.POSTERS[(k * 3 + j + (0 if sgn > 0 else 2)) % len(D4.POSTERS)], id='col_poster_%d_%d_%d' % (k, sgn, j))
        elif f == 'extinguisher':
            D.put(M['extg'], x, SPINE_Y + sgn * (half + 4.0), 90.0 + 90.0 * sgn, z=84.0, ignore_keep=True, margin=0.0, clip=False)
    D.put(M['cage'], x + 12.0, SPINE_Y - 17.0, 270.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)          # a caged lamp on the shaft: its fixture, and the reason the column is lit
    D.put(M['cage'], x - 12.0, SPINE_Y + 17.0, 90.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)
    if k in (1, 4):
        for (a, b, c, d) in ((x - 34.0, SPINE_Y - 34.0, x + 34.0, SPINE_Y - 32.0), (x - 34.0, SPINE_Y + 32.0, x + 34.0, SPINE_Y + 34.0),
                             (x - 34.0, SPINE_Y - 32.0, x - 32.0, SPINE_Y + 32.0), (x + 32.0, SPINE_Y - 32.0, x + 34.0, SPINE_Y + 32.0)):
            box(m, [a, b, 22.0, c, d, 26.0], 'w/metal_painted_scratched_yellow', id='guard_%d_%d_%d' % (k, int(a), int(b)))


# ------------------------------------------------------------------------------------------------ the floor: zones of different stock tiles
def floor7(A, m, D, report):
    D5.floor5(A, m, D, report)
    m.remove('floor_tile')
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(('wear_', 'puddle_'))]:
        k = int(pid.split('_')[-1])
        if (pid.startswith('wear_') and k >= 8) or (pid.startswith('puddle_') and k >= 4):
            m.remove(pid)
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    zones = ((cx0, -2640.0, 'w/building_ship_hallway_floor_06_tile_gray_glossy', 40.0), (-2640.0, -2280.0, 'w/beacon_lab_floor_tile_02_black', 24.0),
             (-2280.0, -1920.0, 'w/stone_floor_tiles_01', 44.0), (-1920.0, -1560.0, 'w/clk_rubber_tiles', 32.0), (-1560.0, cx1, 'w/building_ship_hallway_floor_06_tile_gray_glossy', 56.0))
    for k, (x0, x1, mat, t) in enumerate(zones):
        box(m, [x0, cy0, 0.0, x1, cy1, 1.0], mat, id='floor_zone_%d' % k, uv={'top': {'tile': [t, t]}})
        if k:
            box(m, [x0 - 3.0, cy0, 0.0, x0 + 3.0, cy1, 1.2], DARK, id='floor_zone_seam_%d' % k)
    report['floor7'] = [z[2] for z in zones]


# ------------------------------------------------------------------------------------------------ the ceiling
def ceiling7(A, m, D, report):
    D4.ceiling4(A, m, D, report)
    D6.ceiling6(A, m, D, report)
    m.use('dressing')
    cells = []
    for layer in m.layers.values():
        for o in layer:
            if str(o['id']).startswith('panel_') and not str(o['id']).startswith('panel_rail') and o.get('kind') == 'box':
                b = o['box']
                cells.append(((b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0, o['material'] == A.PANEL_LIVE, o['id']))
    for (_, _, _, pid) in cells:
        m.remove(pid)
    n_on = 0
    for (x, y, on, _) in cells:                                          # the panel boxes become fixtures: lit ones emit in the bake, dead ones hang dark and crooked
        if on:
            put_model(D, M['fluo'], x, y, 0.0, z=176.0, emissive={'color': [1.0, 0.95, 0.82], 'strength': 4.0})
            n_on += 1
        else:
            put_model(D, M['fluo_off'], x, y, 0.0, z=176.0)
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(('sbar_', 'srod_', 'sign_arrow_', 'beam_', 'cornice_', 'beam_rib_'))]:
        m.remove(pid)
    for k in range(5):                                                   # I-beams across the front of every shop, with brackets (the beam cuboids were black slabs)
        a0, a1 = A.aperture(k)
        cx = (a0 + a1) / 2.0
        yb = A.Y1 - A.WT - 8.0
        for dx in (-96.0, 96.0):
            put_model(D, M['ibeam'], cx + dx, yb, 90.0, z=216.0)
        for dx in (-130.0, -48.0, 48.0, 130.0):
            put_model(D, M['bracket'], cx + dx, yb, 0.0, z=210.0)
    report['ceiling7'] = {'fixtures_on': n_on, 'fixtures_off': len(cells) - n_on}


def ducts7(A, m, D):
    for line, y in enumerate((3770.0, 4010.0)):
        x = A.X0 + 100.0 + 128.0 * line
        k = 0
        while x < A.X1 - 90.0:
            D.ceil(M['duct'] if k % 2 == 0 else D6.M['duct_r'], x, y, 90.0, 230.0 if k % 2 == 0 else 226.0)
            put_model(D, M['duct_sup'], x, y, 90.0, z=218.0)
            if k % 3 == 1:
                put_model(D, M['duct_vent'], x + 20.0, y, 0.0, z=205.0)
            k += 1
            x += 128.0
        put_model(D, M['duct_elb'], A.X1 - 70.0, y, 0.0, z=205.0)


# ------------------------------------------------------------------------------------------------ the kiosk, from stock models
def kiosk7(A, m, D, report):
    m.use('dressing')
    kx, ky = GAPS[0], SPINE_Y + 105.0
    gone = 0
    for prefix in ('kiosk_base', 'kiosk_counter', 'kiosk_post_', 'kiosk_back_', 'kiosk_canopy', 'kiosk_sign_', 'kseam_', 'kvert_', 'kmenu_', 'kapron', 'kcanopy_trim', 'k_', 'bar_%d' % int(kx), 'rod_%d' % int(kx)):
        gone += D6.drop(m, prefix)
    # the old counter props at z 47 are re-placed on two stock concession carts face to face (their top is 55: the ticket booth model turned out to be a bumper car)
    old = [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and abs(o['origin'][0] - kx) < 62.0 and abs(o['origin'][1] - ky) < 40.0 and 40.0 < o['origin'][2] < 52.0]
    for pid in old:
        m.remove(pid)
    D.put(M['cart2'], kx, ky - 26.0, 90.0, tag='kcart_a', ignore_keep=True, margin=0.0)
    D.put(M['cart2'], kx, ky + 26.0, 270.0, tag='kcart_b', ignore_keep=True, margin=0.0)
    for k, (mod, du, dv, yw) in enumerate((('register', -20.0, 0.0, 270.0), ('coffee', 16.0, 0.0, 270.0), ('mags', 34.0, 10.0, 20.0), ('donuts', -36.0, -8.0, 30.0), ('mug', 0.0, 0.0, 0.0))):
        D.put(M[mod], kx + du, ky + (-26.0 if k % 2 == 0 else 26.0) + dv, yw, z=55.0, ignore_keep=True, margin=0.0, clip=False)
    for dx, dy in ((-58.0, -50.0), (58.0, -50.0), (-58.0, 50.0), (58.0, 50.0)):         # the striped awning on four I-beam posts
        put_model(D, M['post'], kx + dx, ky + dy, 0.0, z=0.0, scale=0.85)
    put_model(D, M['awning'], kx, ky, 0.0, z=100.0, scale=1.0)
    put_model(D, M['cage'], kx, ky, 0.0, z=94.0)
    D4.foot(D, kx - 74.0, ky - 56.0, kx + 74.0, ky + 56.0)
    report['kiosk7'] = {'removed_box_parts': gone, 'models': ['concession cart x2', 'awning', 'post x4', 'cage lamp']}


# ------------------------------------------------------------------------------------------------ light
def lights7(A, m, report):
    """every coloured or bright light has a fixture model at its position: the live panel fixtures (ceiling7), the shops' fluorescent pairs, the neon tube round every aperture,
    the hanging lamps of the back rooms, cage lamps"""
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, layer='lights', **k)
    for k, (x, y, single) in enumerate(A.live):
        L((x, y, 176.0), color=(1.0, 0.93, 0.78), radius=170.0, intensity=round(D4.POOL_I * (0.55 if single else 1.0), 3), type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    return L, n


def shop_fixtures(A, m, D, L):
    n = 0
    for i in range(5):
        s = A.BAY_X[i]
        cx = s + A.BAY_W / 2.0
        hue = HUE[A.BAYS[i]]
        for dx in (-60.0, 60.0):                                         # two fluorescent fixtures hang in the shop: the key light of the shop is at the pair
            put_model(D, M['fluo'], cx + dx, A.Y1 + 70.0, 0.0, z=186.0, emissive={'color': [1.0, 0.9, 0.74], 'strength': 4.0})
        L((cx, A.Y1 + 70.0, 184.0), color=(1.0, 0.88, 0.7), radius=280.0, intensity=D4.KEY_I, type='spot', dir=(0.0, 0.0, -1.0), inner=34.0, outer=84.0, id='light_key_%d' % (i + 1))
        L((cx, A.Y1 - 22.0, 60.0), color=hue, radius=170.0, intensity=0.6, id='light_neon_%d' % (i + 1))        # the neon tube round the aperture is the source
        L((cx, A.BACK_Y + 60.0, 150.0), color=(1.0, 0.82, 0.55), radius=150.0, intensity=0.45, id='light_back_%d' % (i + 1))            # the hanging lamp of the back room
        n += 3
    for k, x in enumerate((-2560.0, -1860.0)):                          # the caged wall lamps of the south wall are props of wall_props
        L((x, A.Y0 + A.WT + 14.0, 146.0), color=(1.0, 0.78, 0.45), radius=150.0, intensity=0.35, type='spot', dir=(0.0, 0.3, -1.0), inner=16.0, outer=52.0, id='light_cage_%d' % k)
        n += 1
    put_model(D, M['cage'], A.X1 - 60.0, 3900.0, 0.0, z=170.0)
    L((A.X1 - 60.0, 3900.0, 168.0), color=(1.0, 0.85, 0.55), radius=170.0, intensity=0.25, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    put_model(D, M['cage'], A.X0 + 70.0, 4040.0, 0.0, z=146.0)
    L((A.X0 + 70.0, 4040.0, 148.0), color=(1.0, 0.8, 0.5), radius=180.0, intensity=0.5, type='spot', dir=(0.0, -0.2, -1.0), inner=16.0, outer=52.0, id='light_d7_cage')
    if DOJO:
        for k, x in enumerate(COLS):                                     # the lamp on each column's shaft is the fixture
            L((x + 12.0, SPINE_Y - 26.0, 148.0), color=(1.0, 0.86, 0.62), radius=150.0, intensity=0.35, id='light_colS_%d' % k)
            L((x - 12.0, SPINE_Y + 26.0, 148.0), color=(1.0, 0.86, 0.62), radius=150.0, intensity=0.35, id='light_colN_%d' % k)
            n += 2
    L((GAPS[0], SPINE_Y + 105.0, 90.0), color=(1.0, 0.75, 0.35), radius=190.0, intensity=0.5, id='light_kiosk')           # under the awning, at its cage lamp
    return n + 3


def dress(A, m, stage='full', foreign=None):
    D = R2.D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    R3.shutters(A, m, report)
    floor7(A, m, D, report)
    D4.wall_bands4(A, m, D, report)
    R3.fronts_and_doors(A, m, D, report)
    ceiling7(A, m, D, report)
    if DOJO:                                                  # ARC7_COLUMNS=pier gives round 6's trimmed piers (not shot in round 7: the machine would not start the session)
        D4.column = column7
    D4.spine4(A, m, D, report)
    kiosk7(A, m, D, report)
    D6.d7_6(A, m, D, report)
    R3.wall_props(A, m, D)
    report['stock'] = {}
    for i in range(5):
        report['stock'][A.BAYS[i]] = D6.shop6(A, m, D, i, report)
    R3.d7_props(A, D)
    R3.ceiling_props(A, D)
    ducts7(A, m, D)
    for y in (3600.0, 4220.0):
        x = A.X0 + 160.0
        while x < A.X1 - 90.0:
            D.ceil(M['pipe'], x, y, 90.0, 232.0)
            x += 128.0
    D5.stories5(A, m, D, report)
    L, n = lights7(A, m, report)
    n += shop_fixtures(A, m, D, L)
    report['lights'] = n + len(A.live)
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
