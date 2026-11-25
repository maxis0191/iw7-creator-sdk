"""arcade_dress2: the dressing and the light of the Underpass Arcade, round 2 (called by arcade2.build_arcade).

The place is a 1978 subway shopping underpass, abandoned: worn small tile, dim, half dead panels, five small shops behind roller shutters. The prop list is built from
zone cp_disco first (a 1970s New York map: subway bench, newspaper box, pay phone, turnstile, lockers, records), then cp_town (1950s shop kit), then neutral cp_zmb items.
Counters, shelves, the booths, the sign boxes and the shutters are GEOMETRY (they cost no model kind: a live session takes 63 to 64 distinct models, fault FA8); the
stock on them is a handful of small models repeated.
"""
import math
import random
import sys

import arcade_dress as R1
from studio import build as B, answers

R1.SUBST.clear()                         # round 1's substitutions served its 63 kind cut; round 2 chooses its own kit
PROP_CAP, LIGHT_CAP, MODEL_CAP = 760, 52, 63

HUE = {'photo': (0.30, 0.85, 1.00), 'heel': (1.00, 0.55, 0.12), 'hole9': (1.00, 0.30, 0.68), 'copy': (0.26, 0.45, 1.00), 'needle': (1.00, 0.18, 0.20)}
TUBE = {'photo': 'w/metal_light_line_lightblue_03', 'heel': 'w/plastic_wall_panel_light_03_on_orange', 'hole9': 'w/emissive_light_panel_pink', 'copy': 'w/plastic_wall_panel_light_02_on_blue',
        'needle': 'w/plastic_wall_panel_light_02_on_red'}
SIGN_TEXT = {'photo': 'PHOTO', 'heel': 'HEEL & KEY', 'hole9': 'HOLE NUMBER NINE', 'copy': 'COPY STOP', 'needle': 'NEEDLE DROP'}      # unused until the tool takes text (FA4)

# the kit, by need: model (zone it is taken from). Recorded in kit.md by `kit_report`.
M = dict(
    bench='cp_disco_worn_subway_bench', news='cp_disco_street_news_vending_01', phone='street_telephone_booth_old_iw6', bin1='cp_disco_street_trashcan_01', bin2='lv_trash_can_vegas',
    turn='cp_disco_subway_turnstyle_animated', locker='cp_disco_subway_lockers_02', buffer='cp_disco_floor_buffer', mop='com_janitor_bucket_mop_iw6', wet='sign_wet_floor',
    planter='p7_planter_concrete_box_64x32', plant='com_potted_plant_small_des', cart='cart_janitor_plastic_bucket', barrier='cp_disco_subway_construction_barrier_01',
    soda='cp_town_soda_machine_01', case='greece_display_cases_11',
    bag='com_trashbag2_black', chips='food_trash_bag_chips_01', cup='cup_paper_open_iw6', paper='newspaper_single_fn_01', can='food_trash_can_soda_01', pile='cp_disco_trash_pile_01',
    smokes='food_trash_cigarettes',
    duct='duct_metal_rectangle_straight_128', pipe='pipe_metal_painted_straight_128_gray', wire='wire_hanging_ceiling_64', wire2='hanging_wires_01',
    gondola='cp_town_store_shelves_96_01', steel='com_restaurantstainlessteelshelf_02', rack='ac_prs_imp_com_clothing_rack_1', boxa='p7_box_cardboard_a_closed',
    boxc='p7_box_cardboard_c_closed', ream='com_copypaper_box', stack='office_paper_stack01_iw6', books='office_book_set_iw6', crackers='cp_town_grocery_crackers',
    donuts='food_snacks_iw6_donutsstack01', mug='p7_cup_coffee_mug', coffee='misc_coffee_machine', register='cp_town_cash_register', shoes='p7_54i_gear_shoes',
    crate='cp_disco_record_milk_crate', sleeve='cp_disco_record_sleeve_01', turntable='cp_rave_turntable_01', juke='cp_town_jukebox', hook='cp_rave_tiki_key_hook_01',
    toolbox='dns_toolbox_small_iw6', hammer='dns_tool_hammer01_iw6', copier='cp_town_punchcard_computer_console', computer='equipment_old_computer', file='furniture_filing_cabinet',
    stool='chair_bar_stool_02', curtain='cp_disco_curtain_straight', mags='cp_rave_magazine_stack_01', stackp='newspaper_stack_fn_01',
    valve='ind_pipe_metal_hp_12_valve_01', warn='p7_caution_metal_sign_rusty', cage='p7_lights_cagelight02_on', glass='misc_bottle_wine_01',
)


class D2(R1.Dresser):
    pass


def box(m, b, mat, mode='render', **kw):
    return B.box(m, [round(v, 2) for v in b], mat, mode=mode, **kw)


# ------------------------------------------------------------------------------------------------ shutters (geometry with collision, the aperture stays walkable)
def shutters(A, m, report):
    m.use('dressing')
    yin = A.Y1 - A.WT                                   # the corridor's north wall face
    info = {}
    for i in range(5):
        a0, a1 = A.aperture(i)
        cx = (a0 + a1) / 2.0
        share = A.SHUT_SHARE[i]
        zb = A.AP_H * (1.0 - share)
        jam = share > 0.5
        x1 = a1 - A.SHUT_GAP if jam else a1
        # the curtain: a solid slatted panel from the lintel down to zb (render and collision), in the thickness of the double wall
        B.box(m, [a0, yin + 4.0, zb, x1, yin + 8.0, A.AP_H], A.SHUTTER, id='shutter_curtain_%d' % (i + 1))
        box(m, [a0, yin + 3.0, zb - 3.0, x1, yin + 9.0, zb], 'w/metal_painted_01_black', id='shutter_bar_%d' % (i + 1))      # the bottom bar of the curtain
        box(m, [a0 - 8.0, yin - 14.0, A.AP_H, a1 + 8.0, yin, A.AP_H + 24.0], 'w/metal_painted_02', id='shutter_box_%d' % (i + 1))   # the housing above the lintel
        box(m, [a0 - 7.0, yin - 2.0, 0.0, a0 - 1.0, yin + 3.0, A.AP_H], 'w/metal_painted_01_black', id='rail_l_%d' % (i + 1))
        box(m, [a1 + 1.0, yin - 2.0, 0.0, a1 + 7.0, yin + 3.0, A.AP_H], 'w/metal_painted_01_black', id='rail_r_%d' % (i + 1))
        info[i + 1] = {'bottom_z': round(zb, 1), 'clear_below': round(zb, 1), 'jammed_gap': [round(x1, 1), round(a1, 1)] if jam else None}
    report['shutters'] = info


# ------------------------------------------------------------------------------------------------ corridor shell: floor, walls, panels, fronts, doors
def corridor_shell(A, m, D, report, cal):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    tile = float(__import__('os').environ.get('ARC_TILE', '40'))
    floor_mat = __import__('os').environ.get('ARC_FLOOR', 'w/plastic_slick_floor_01_orange')
    uv = {'top': {'tile': [tile, tile]}}
    if cal:
        cands = ['w/fah_restaurant_tiles_01', 'w/stone_floor_tiles_01', 'w/clk_rubber_tiles', 'w/plastic_slick_floor_01_orange']
        step = (cx1 - cx0) / len(cands)
        for k, mat in enumerate(cands):
            box(m, [cx0 + k * step, cy0, 0.0, cx0 + (k + 1) * step, cy1, 1.0], mat, id='floor_cal_%d' % k, uv=uv)
    else:
        box(m, [cx0, cy0, 0.0, cx1, cy1, 1.0], floor_mat, id='floor_tile', uv=uv)
    # a darker border strip along both walls and the shop mats (one worn rubber), no patchwork
    for k, (y0, y1) in enumerate(((cy0, cy0 + 26.0), (cy1 - 26.0, cy1))):
        box(m, [cx0, y0, 0.0, cx1, y1, 1.5], 'w/fac_tile_black_01', id='floor_border_%d' % k, uv={'top': {'tile': [32.0, 32.0]}})
    for i in range(5):
        a0, a1 = A.aperture(i)
        box(m, [a0, cy1 - 46.0, 1.0, a1, cy1 - 26.0, 1.6], 'w/fac_rubber_mat_black', id='mat_%d' % (i + 1))
    # the lower wall: a band of worn tile (south wall whole, north wall on the piers) and a dark skirting
    band = 'w/dt_tile_ceramic_white'
    bh = 96.0
    if cal:
        third = (cx1 - cx0) / 3.0
        for k, mat in enumerate(('w/dt_tile_ceramic_white', 'w/concrete_wall_panel_01', 'w/plaster_wall_04_grey')):
            box(m, [cx0 + k * third, cy0, 0.0, cx0 + (k + 1) * third, cy0 + 2.0, bh], mat, id='wallband_cal_%d' % k, uv={'north': {'tile': [64.0, 64.0]}})
    else:
        box(m, [cx0, cy0, 0.0, cx1, cy0 + 2.0, bh], band, id='wallband_s', uv={'north': {'tile': [64.0, 64.0]}})
    box(m, [cx0, cy0, 0.0, cx1, cy0 + 3.0, 8.0], 'w/metal_painted_01_black', id='skirt_s')
    box(m, [cx0, cy1 - 3.0, 0.0, cx1, cy1, 8.0], 'w/metal_painted_01_black', id='skirt_n')
    # the hung panel grid: 75 cells, 30 live (greenish white, each with its pool), 30 dead, 15 missing (cables hang)
    rows = [3590.0, 3745.0, 3900.0, 4055.0, 4210.0]
    cols = [A.X0 + 100.0 + 118.0 * i for i in range(15)]
    cells = [(ri, ci, x, y) for ri, y in enumerate(rows) for ci, x in enumerate(cols)]
    rng = random.Random(11)
    order = list(range(len(cells)))
    rng.shuffle(order)
    live_ix, missing_ix = set(order[:30]), set(order[30:45])
    A.live, A.missing = [], []
    for k, (ri, ci, x, y) in enumerate(cells):
        if k in missing_ix:
            A.missing.append((x, y))
            continue
        live = k in live_ix
        box(m, [x - 40.0, y - 14.0, 178.0, x + 40.0, y + 14.0, 182.0], A.PANEL_LIVE if live else A.PANEL_DEAD, id='panel_%d_%d' % (ri, ci))
        if live:
            A.live.append((x, y))
    for ri, y in enumerate(rows):
        box(m, [cx0, y - 18.0, 183.0, cx1, y - 15.0, 188.0], 'w/metal_painted_02', id='panel_rail_a_%d' % ri)
        box(m, [cx0, y + 15.0, 183.0, cx1, y + 18.0, 188.0], 'w/metal_painted_02', id='panel_rail_b_%d' % ri)
    A.panels = len(cells) - len(A.missing)
    # south wall: three closed shop fronts (three widths), shutters down, headers, a lost property hatch
    for k, (x0, x1) in enumerate(((-2480.0, -2220.0), (-1790.0, -1500.0), (-1470.0, -1290.0))):
        yv = cy0
        box(m, [x0 - 6.0, yv, 0.0, x1 + 6.0, yv + 5.0, 134.0], 'w/metal_painted_01_black', id='front_frame_%d' % k)
        B.box(m, [x0, yv + 5.0, 0.0, x1, yv + 9.0, 124.0], A.SHUTTER, id='front_shutter_%d' % k)
        box(m, [x0 - 6.0, yv, 134.0, x1 + 6.0, yv + 8.0, 168.0], ('w/plaster_wall_01_brown', 'w/plaster_wall_04_beige', 'w/plaster_wall_04_grey')[k], id='front_header_%d' % k)
        box(m, [x0, yv + 8.0, 140.0, x1, yv + 9.0, 160.0], 'w/metal_painted_04', id='front_sign_dead_%d' % k)      # the dead lettering board over each front
    hx0, hx1 = -2130.0, -2030.0                                                                                       # lost property: a counter hatch in a frame
    box(m, [hx0 - 8.0, cy0, 0.0, hx1 + 8.0, cy0 + 8.0, 112.0], 'w/metal_painted_01_black', id='hatch_frame')
    box(m, [hx0, cy0 + 8.0, 44.0, hx1, cy0 + 10.0, 100.0], 'w/metal_panel_dark_01', id='hatch_dark')
    B.box(m, [hx0 - 8.0, cy0 + 8.0, 40.0, hx1 + 8.0, cy0 + 30.0, 46.0], 'w/wood_antique_panel_trim_01', id='hatch_sill')
    # D4: framed doorway, hazard stripe
    for k, bb in enumerate(([cx1 - 4.0, A.DOOR_Y0 - 8.0, 0.0, cx1, A.DOOR_Y0, A.DOOR_Z + 8.0], [cx1 - 4.0, A.DOOR_Y1, 0.0, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0],
                            [cx1 - 4.0, A.DOOR_Y0 - 8.0, A.DOOR_Z, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0])):
        box(m, bb, 'w/metal_painted_01_black', id='d4_frame_%d' % k)
    box(m, [cx1 - 8.0, A.DOOR_Y0, A.DOOR_Z - 20.0, cx1 - 4.0, A.DOOR_Y1, A.DOOR_Z - 4.0], 'w/paint_lines_01_thick_yellow_clean', id='d4_stripe')
    # D7 (west end): the blast door as a heavy framed door: deep frame, riveted slab, a hazard band, bolts, a winch wheel beside it, a warning plate
    xw = cx0
    zt = 176.0
    box(m, [xw, 3774.0, 0.0, xw + 14.0, 3794.0, zt + 12.0], 'w/metal_painted_01_black', id='d7_post_l')
    box(m, [xw, 4006.0, 0.0, xw + 14.0, 4026.0, zt + 12.0], 'w/metal_painted_01_black', id='d7_post_r')
    box(m, [xw, 3774.0, zt, xw + 14.0, 4026.0, zt + 12.0], 'w/metal_painted_01_black', id='d7_head')
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 4006.0, zt], 'w/metal_panel_dark_01', id='d7_slab')
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 12.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    box(m, [xw + 10.0, 3790.0, 88.0, xw + 13.0, 4010.0, 96.0], 'w/metal_painted_scratched_yellow_02', id='d7_band')
    for k, y in enumerate((3808.0, 3900.0, 3992.0)):
        box(m, [xw + 10.0, y - 3.0, 150.0, xw + 13.0, y + 3.0, 156.0], 'w/metal_painted_02', id='d7_bolt_%d' % k)
    box(m, [xw + 10.0, 3880.0, 40.0, xw + 12.0, 3920.0, 70.0], 'w/paint_lines_01_thick_white_clean', id='d7_plate')
    # the hung ceiling's skirt and a heavy beam over each bay front
    for k in range(5):
        a0, a1 = A.aperture(k)
        box(m, [a0 - 14.0, cy1 - 16.0, 214.0, a1 + 14.0, cy1, 232.0], 'w/metal_painted_02', id='beam_%d' % (k + 1))
    decals(A, m)
    report['floor'] = {'material': 'cal' if cal else floor_mat, 'tile_uv': tile}


def decals(A, m):
    """worn and dirty: stains on the floor at the walls and the lanes, peeling and cracks and old bills on the south wall (decals: whether they draw is judged in the frames)"""
    rng = random.Random(5)
    fl = ['w/asphalt_flooring_stain_01', 'w/fac_darkstain_01_dec']
    for k in range(26):
        x = rng.uniform(A.X0 + 60.0, A.X1 - 60.0)
        y = rng.choice((rng.uniform(A.Y0 + 30.0, A.Y0 + 140.0), rng.uniform(A.Y1 - 150.0, A.Y1 - 40.0), rng.uniform(A.Y0 + 140.0, A.Y1 - 150.0)))
        sz = rng.uniform(40.0, 90.0)
        B.decal(m, fl[k % len(fl)], (x, y, 1.6), (0.0, 0.0, 1.0), (sz, sz), rot=rng.uniform(0.0, 360.0), id='decal_floor_%d' % k)
    wl = ['w/plaster_peeling_02_grey_dec', 'w/plaster_damaged_11_crack_dec', 'w/wall_stain_01_dec', 'w/signage_decals_corridor_01', 'w/pb_plaster10_paint_decal', 'w/dirt_stain_water_drips_01']
    for k in range(22):
        x = A.X0 + 60.0 + k * 80.0 + rng.uniform(-20.0, 20.0)
        B.decal(m, wl[k % len(wl)], (x, A.Y0 + A.WT, rng.uniform(70.0, 150.0)), (0.0, 1.0, 0.0), (rng.uniform(40.0, 70.0), rng.uniform(40.0, 70.0)), id='decal_wall_%d' % k)


# ------------------------------------------------------------------------------------------------ the shop kit
class Shelf:
    """a geometry shelf unit: uprights, boards, an invisible collision box; slots() yields stock positions per level"""
    def __init__(self, m, id, rect, front, levels, board='w/wood_antique_panel_trim_01', frame='w/metal_painted_01_black', top=96.0, clip=True):
        self.rect, self.front, self.levels, self.top = rect, front, levels, top
        x0, y0, x1, y1 = rect
        if clip:
            B.clip(m, [x0, y0, 0.0, x1, y1, top], id=id + '_clip')
        for k, z in enumerate(levels):
            box(m, [x0, y0, z - 2.0, x1, y1, z], board, id='%s_b%d' % (id, k))
        # back panel and ends: thin dark
        bx = {'w': [x0, y0, 0.0, x0 + 2.0, y1, top], 'e': [x1 - 2.0, y0, 0.0, x1, y1, top], 's': [x0, y0, 0.0, x1, y0 + 2.0, top], 'n': [x0, y1 - 2.0, 0.0, x1, y1, top]}
        back = {'w': 'e', 'e': 'w', 's': 'n', 'n': 's'}[front]          # front = the side facing the room
        box(m, bx[back], frame, id=id + '_back')
        for k, (a, b) in enumerate(((x0, y0), (x1 - 2.0, y0), (x0, y1 - 2.0), (x1 - 2.0, y1 - 2.0))):
            box(m, [a, b, 0.0, a + 2.0, b + 2.0, top], frame, id='%s_up%d' % (id, k))

    def slots(self, step, margin=6.0):
        x0, y0, x1, y1 = self.rect
        out = []
        along_x = self.front in ('s', 'n')
        lo, hi = (x0, x1) if along_x else (y0, y1)
        mid = (y0 + y1) / 2.0 if along_x else (x0 + x1) / 2.0
        for z in self.levels:
            t = lo + margin
            while t <= hi - margin + 1e-6:
                out.append(((t, mid) if along_x else (mid, t), z))
                t += step
        return out


def stock(D, shelf, items, step, yaw=0.0, jitter=0.0, skip=0.0, scale=1.0):
    """fill a shelf: every slot gets items[k % len] (None = a gap), a little yaw jitter"""
    n = 0
    for k, ((x, y), z) in enumerate(shelf.slots(step)):
        mod = items[(k + int(z) // 20) % len(items)]
        if mod is None or D.rng.random() < skip:
            continue
        if D.put(M[mod] if mod in M else mod, x, y, yaw + D.rng.uniform(-jitter, jitter), z=z, ignore_keep=True, margin=0.0, scale=scale):
            n += 1
    return n


def counter(m, D, id, x0, y0, x1, y1, h=44.0, top='w/wood_antique_panel_trim_01', body='w/wood_worn_painted_01_red', tag=None):
    """a counter: body, a top slab and a kick, real collision; the top height is recorded for things placed on it"""
    B.box(m, [x0, y0, 0.0, x1, y1, h - 3.0], body, id=id + '_body')
    box(m, [x0 - 2.0, y0 - 2.0, h - 3.0, x1 + 2.0, y1 + 2.0, h], top, id=id + '_top')
    D.tops[tag or id] = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, h, x1 - x0, y1 - y0, 0.0)
    return h


def on_counter(D, tag, mod, du, dv, yaw=0.0, scale=1.0):
    x, y, h = D.tops[tag][0], D.tops[tag][1], D.tops[tag][2]
    return D.put(M.get(mod, mod), x + du, y + dv, yaw, z=h, ignore_keep=True, margin=0.0, scale=scale)


def bay(A, m, D, i):
    s = A.BAY_X[i]
    yb = A.Y1
    kind = A.BAYS[i]
    wallb = yb + A.BAY_D - A.WT
    U = lambda u: s + u
    V = lambda v: yb + v
    yp = A.BACK_Y
    left, right = s + A.WT, s + A.BAY_W - A.WT
    m.use('dressing')
    # a worn skirting round the shop and a ceiling band; the back room is plain
    box(m, [left, yb + A.WT, 0.0, left + 2.0, wallb, 8.0], 'w/metal_painted_01_black', id='skirt_l_%d' % (i + 1))
    box(m, [right - 2.0, yb + A.WT, 0.0, right, wallb, 8.0], 'w/metal_painted_01_black', id='skirt_r_%d' % (i + 1))
    if kind == 'photo':
        # two photo booths against the partition (right of the walk-in path): a dark cabinet, a curtain, a lit header, a stool; photo strips pinned on the right wall
        for k, u0 in enumerate((214.0, 258.0)):
            B.box(m, [U(u0), yp - 44.0, 0.0, U(u0 + 40.0), yp, 100.0], 'w/metal_painted_01_black', id='booth_%d' % k)
            box(m, [U(u0 + 2.0), yp - 46.0, 78.0, U(u0 + 38.0), yp - 44.0, 98.0], TUBE['photo'], id='booth_lit_%d' % k)
            D.put(M['curtain'], U(u0 + 20.0), yp - 46.0, 90.0, z=8.0, scale=0.55, ignore_keep=True, margin=0.0)
            D.put(M['stool'], U(u0 + 20.0), yp - 70.0, 0.0, ignore_keep=True, margin=0.0)
        sh = Shelf(m, 'shelf_r_%d' % i, (right - 34.0, V(34.0), right, V(150.0)), 'w', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh, ['boxc', 'crackers', 'paper', 'boxc', 'mags'], 18.0, yaw=0.0, jitter=15.0)
        sh2 = Shelf(m, 'shelf_p_%d' % i, (U(20.0), yp - 34.0, U(112.0), yp), 's', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh2, ['crackers', 'boxc', 'books', 'paper', 'stack'], 14.0, yaw=270.0, jitter=12.0)
        counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), tag='ctr_a%d' % i)
        on_counter(D, 'ctr_a%d' % i, 'register', -14.0, 0.0, 270.0)
        on_counter(D, 'ctr_a%d' % i, 'mags', 14.0, 0.0, 20.0)
        on_counter(D, 'ctr_a%d' % i, 'stack', 0.0, -8.0, 0.0)
        counter(m, D, 'ctr2_%d' % i, U(208.0), V(24.0), U(270.0), V(54.0), tag='ctr_b%d' % i)
        on_counter(D, 'ctr_b%d' % i, 'boxc', -14.0, 0.0, 10.0)
        on_counter(D, 'ctr_b%d' % i, 'paper', 12.0, 0.0, 70.0)
    elif kind == 'heel':
        sh = Shelf(m, 'shelf_l_%d' % i, (left, V(34.0), left + 34.0, V(150.0)), 'e', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh, ['shoes', 'shoes', 'shoes', 'boxc'], 13.0, yaw=0.0, jitter=25.0)
        sh2 = Shelf(m, 'shelf_p_%d' % i, (U(20.0), yp - 34.0, U(112.0), yp), 's', (30.0, 56.0, 82.0))
        stock(D, sh2, ['shoes', 'shoes', 'boxc', 'shoes'], 12.0, yaw=270.0, jitter=25.0)
        sh3 = Shelf(m, 'shelf_q_%d' % i, (U(208.0), yp - 34.0, U(300.0), yp), 's', (30.0, 56.0, 82.0))
        stock(D, sh3, ['shoes', 'boxc', 'shoes', 'shoes'], 12.0, yaw=270.0, jitter=25.0)
        for k in range(10):          # the key board: hooks on a dark board over the partition shelves
            if k < 5:
                D.put(M['hook'], U(24.0 + 16.0 * k), yp - 2.0, 270.0, z=104.0, ignore_keep=True, margin=0.0)
            else:
                D.put(M['hook'], U(212.0 + 16.0 * (k - 5)), yp - 2.0, 270.0, z=104.0, ignore_keep=True, margin=0.0)
        box(m, [U(18.0), yp - 3.0, 100.0, U(112.0), yp, 112.0], 'w/wood_worn_painted_01_green', id='keyboard_l')
        box(m, [U(206.0), yp - 3.0, 100.0, U(300.0), yp, 112.0], 'w/wood_worn_painted_01_green', id='keyboard_r')
        counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), body='w/metal_painted_04', tag='ctr_a%d' % i)
        on_counter(D, 'ctr_a%d' % i, 'register', -14.0, 0.0, 270.0)
        on_counter(D, 'ctr_a%d' % i, 'toolbox', 14.0, 0.0, 0.0)
        on_counter(D, 'ctr_a%d' % i, 'hammer', 4.0, 8.0, 20.0)
        D.wall(M['rack'], ['x', right, -1], V(100.0), tag='rack_%d' % i)
    elif kind == 'hole9':
        counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), top='w/dt_tile_ceramic_white', tag='ctr_a%d' % i)
        counter(m, D, 'ctr2_%d' % i, U(208.0), V(24.0), U(270.0), V(54.0), top='w/dt_tile_ceramic_white', tag='ctr_b%d' % i)
        for k, du in enumerate((-18.0, 0.0, 18.0)):
            on_counter(D, 'ctr_a%d' % i, 'donuts', du, 4.0 - 8.0 * (k % 2), 0.0)
            on_counter(D, 'ctr_b%d' % i, 'donuts', du, -4.0 + 8.0 * (k % 2), 180.0)
        on_counter(D, 'ctr_a%d' % i, 'coffee', 0.0, -10.0, 270.0)
        on_counter(D, 'ctr_b%d' % i, 'register', -14.0, 0.0, 270.0)
        for k in range(6):
            on_counter(D, 'ctr_a%d' % i if k < 3 else 'ctr_b%d' % i, 'mug', -22.0 + 18.0 * (k % 3), 10.0)
        sh = Shelf(m, 'shelf_l_%d' % i, (left, V(34.0), left + 34.0, V(150.0)), 'e', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh, ['crackers', 'mug', 'crackers', 'boxc'], 12.0, yaw=0.0, jitter=10.0)
        sh2 = Shelf(m, 'shelf_p_%d' % i, (U(20.0), yp - 34.0, U(112.0), yp), 's', (30.0, 56.0, 82.0))
        stock(D, sh2, ['crackers', 'donuts', 'mug', 'crackers'], 13.0, yaw=270.0, jitter=10.0)
        # a window bar along the right wall with its stools
        B.box(m, [right - 22.0, V(60.0), 0.0, right, V(146.0), 40.0], 'w/wood_worn_painted_01_red', id='bar_%d' % i)
        box(m, [right - 24.0, V(58.0), 40.0, right, V(148.0), 43.0], 'w/dt_tile_ceramic_white', id='bar_top_%d' % i)
        D.tops['bar_%d' % i] = (right - 12.0, V(103.0), 43.0, 22.0, 86.0, 0.0)
        for k in range(3):
            D.put(M['stool'], right - 46.0, V(76.0 + 28.0 * k), 0.0, ignore_keep=True, margin=0.0)
            on_counter(D, 'bar_%d' % i, 'mug', 0.0, -26.0 + 26.0 * k)
        on_counter(D, 'bar_%d' % i, 'donuts', 0.0, 0.0, 90.0)
    elif kind == 'copy':
        D.wall(M['copier'], ['x', left, 1], V(60.0), tag='cop1')
        D.wall(M['copier'], ['x', left, 1], V(100.0), tag='cop2')
        D.wall(M['computer'], ['x', right, -1], V(100.0), tag='cop3')
        D.wall(M['file'], ['x', right, -1], V(60.0), tag='file1')
        sh = Shelf(m, 'shelf_p_%d' % i, (U(20.0), yp - 34.0, U(112.0), yp), 's', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh, ['ream', 'ream', 'stack', 'books'], 14.0, yaw=270.0, jitter=8.0)
        sh2 = Shelf(m, 'shelf_q_%d' % i, (U(208.0), yp - 34.0, U(300.0), yp), 's', (22.0, 44.0, 66.0, 88.0))
        stock(D, sh2, ['ream', 'stack', 'ream', 'boxa'], 14.0, yaw=270.0, jitter=8.0)
        counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), top='w/dt_plywood_dirty', tag='ctr_a%d' % i)
        counter(m, D, 'ctr2_%d' % i, U(208.0), V(24.0), U(270.0), V(54.0), top='w/dt_plywood_dirty', tag='ctr_b%d' % i)
        on_counter(D, 'ctr_a%d' % i, 'register', -14.0, 0.0, 270.0)
        on_counter(D, 'ctr_a%d' % i, 'ream', 14.0, 4.0, 15.0)
        on_counter(D, 'ctr_b%d' % i, 'stack', -14.0, 0.0, 30.0)
        on_counter(D, 'ctr_b%d' % i, 'ream', 10.0, 0.0, 80.0)
        on_counter(D, 'ctr_b%d' % i, 'books', 22.0, 6.0, 40.0)
    else:  # needle
        sh = Shelf(m, 'shelf_p_%d' % i, (U(20.0), yp - 34.0, U(112.0), yp), 's', (30.0, 56.0, 82.0))
        stock(D, sh, ['sleeve', 'sleeve', 'sleeve', 'sleeve'], 5.0, yaw=270.0, jitter=6.0)
        sh2 = Shelf(m, 'shelf_q_%d' % i, (U(208.0), yp - 34.0, U(300.0), yp), 's', (30.0, 56.0, 82.0))
        stock(D, sh2, ['sleeve', 'sleeve', 'sleeve', 'sleeve'], 5.0, yaw=270.0, jitter=6.0)
        sh3 = Shelf(m, 'shelf_l_%d' % i, (left, V(34.0), left + 34.0, V(150.0)), 'e', (22.0, 44.0, 66.0))
        stock(D, sh3, ['sleeve', 'sleeve', 'sleeve', 'sleeve'], 5.0, yaw=0.0, jitter=6.0)
        counter(m, D, 'ctr_%d' % i, U(50.0), V(24.0), U(112.0), V(54.0), tag='ctr_a%d' % i)
        on_counter(D, 'ctr_a%d' % i, 'turntable', -12.0, 0.0, 270.0)
        on_counter(D, 'ctr_a%d' % i, 'register', 14.0, 0.0, 270.0)
        # record bins on the floor: milk crates in rows (two per stack)
        for k in range(8):
            D.put(M['crate'], U(228.0 + 22.0 * (k % 3)), V(40.0 + 24.0 * (k // 3)), D.rng.uniform(-10.0, 10.0), z=0.0, tag='crate%d_%d' % (i, k), margin=1.0)
        D.wall(M['juke'], ['x', right, -1], V(110.0), tag='juke')
        for k in range(2):
            D.put(M['sleeve'], U(60.0 + 12.0 * k), V(80.0), 20.0 * k, z=0.0, ignore_keep=True, margin=0.0)
    # the back room: the darkest place of the arcade (no light): a steel shelf, crates, a bag
    D.wall(M['steel'], ('y', wallb, -1), U(160.0), tag='bshelf%d' % i)
    D.on('bshelf%d' % i, M['boxc'], -12.0, 0.0, 90.0)
    D.on('bshelf%d' % i, M['bag'], 12.0, 0.0, 40.0)


# ------------------------------------------------------------------------------------------------ the corridor furniture
def corridor_props(A, m, D):
    P_ = D.put
    cy0 = A.Y0 + A.WT
    # south wall west to east: vending pair, pay phone row, the lost property hatch with its shelves and lockers, the map case
    for k, x in enumerate((-2955.0, -2918.0)):
        D.wall(M['soda'], 's', x, tag='vend%d' % k)
    for k in range(4):
        D.wall(M['phone'], 's', -2840.0 + 34.0 * k, tag='phone%d' % k)
    D.wall(M['steel'], 's', -2165.0, tag='lp_sh1')
    D.wall(M['steel'], 's', -1995.0, tag='lp_sh2')
    for k in range(3):
        D.wall(M['locker'], 's', -2300.0 - 20.0 * k, tag='lock%d' % k)
    D.wall(M['case'], 's', -1640.0, tag='mapcase')
    D.wall(M['planter'], 's', -1330.0, tag='planter_s')
    D.on('planter_s', M['plant'], 0.0, 0.0)
    D.wall(M['bin1'], 's', -2700.0, tag='bin_s0')
    D.wall(M['bin2'], 's', -2060.0, tag='bin_s1')
    D.wall(M['bin1'], 's', -1560.0, tag='bin_s2')
    D.wall(M['news'], 's', -2680.0, tag='news_s0')
    D.wall(M['turn'], 's', -1280.0, tag='turn0')
    D.wall(M['turn'], 's', -1240.0, tag='turn1')
    D.wall(M['bench'], 's', -2305.0, tag='bench_s0')
    D.wall(M['bench'], 's', -1975.0, tag='bench_s1')
    D.wall(M['wet'], 's', -2330.0, tag='wet_s')
    # north piers: a newspaper box row, a pair of bins, a pay phone, benches where a pier is wide, a planter with a dead plant
    piers = [(-2984.0, -2916.0), (-2684.0, -2586.0), (-2354.0, -2256.0), (-2024.0, -1926.0), (-1694.0, -1596.0), (-1364.0, -1216.0)]
    for k, (a, b) in enumerate(piers):
        mid = (a + b) / 2.0
        if k in (1, 3, 4):
            D.wall(M['news'], 'n', mid - 22.0, tag='pier_news%da' % k)
            D.wall(M['news'], 'n', mid + 22.0, tag='pier_news%db' % k)
        if k in (0, 2):
            D.wall(M['bin1'], 'n', mid, tag='pier_bin%d' % k)
        if k == 2:
            D.wall(M['phone'], 'n', mid + 30.0, tag='pier_phone')
    D.wall(M['bin2'], 'n', -1250.0, tag='pier_bin5')
    D.wall(M['news'], 'n', -1330.0, tag='pier_news5')
    D.wall(M['news'], 'n', -1290.0, tag='pier_news5b')
    # the centre band: a floor polisher left running its cord, a cleaning cart, wet floor signs, benches in pairs, a planter pair, a barrier
    D.put(M['buffer'], -2780.0, 3760.0, 25.0, tag='buffer')
    D.put(M['mop'], -2715.0, 3805.0, 80.0, tag='mop')
    D.put(M['cart'], -2860.0, 3800.0, 10.0, tag='cart')
    D.put(M['wet'], -2770.0, 3815.0, 30.0, tag='wet1')
    D.put(M['wet'], -2250.0, 4085.0, 200.0, tag='wet2')
    D.put(M['barrier'], -1560.0, 4000.0, 90.0, tag='barrier1')
    for k, x in enumerate((-2450.0, -1990.0, -1650.0)):
        D.put(M['bench'], x, 3830.0, 90.0, tag='bench_c%da' % k)
        D.put(M['bench'], x, 3935.0, 270.0, tag='bench_c%db' % k)
        D.put(M['bin1'], x + 70.0, 3885.0, 0.0, tag='bin_c%d' % k)
        D.put(M['planter'], x - 80.0, 3885.0, 90.0, tag='plant_c%d' % k)
        D.on('plant_c%d' % k, M['plant'], 0.0, 0.0)
        for j in range(2):
            D.put(D.rng.choice((M['paper'], M['cup'], M['mags'])), x + (j - 0.5) * 40.0, 3830.0 if j == 0 else 3935.0, D.rng.random() * 360.0, on='bench_c%d%s' % (k, 'a' if j == 0 else 'b'))
    D.put(M['news'], -2330.0, 3790.0, 90.0, tag='kiosk_news0')
    D.put(M['news'], -2330.0, 3822.0, 90.0, tag='kiosk_news1')
    # the kiosk: a desk, a register, a phone: a lost and found desk near D4
    D.put(M['file'], -1480.0, 4090.0, 90.0, tag='kiosk_file')
    D.put(M['register'], -1480.0, 4090.0, 270.0, on='kiosk_file')
    D.put(M['phone'], -1520.0, 4100.0, 180.0, tag='kiosk_phone')


def litter(A, D):
    """clusters against the walls, at the feet of bins and benches: never an even scatter"""
    kinds = [M['bag'], M['chips'], M['cup'], M['paper'], M['can'], M['pile'], M['smokes']]
    anchors = []
    for tag in list(D.tops):
        if tag.startswith(('bin_', 'pier_bin', 'bench_', 'news_', 'pier_news', 'vend', 'planter', 'phone', 'turn', 'lock')):
            anchors.append(D.tops[tag])
    D.rng.shuffle(anchors)
    n = 0
    for (x, y, _top, w, d, _yaw) in anchors:
        for _ in range(D.rng.randint(2, 4)):
            ang = D.rng.uniform(0.0, 6.283)
            r = max(w, d) / 2.0 + D.rng.uniform(6.0, 26.0)
            if D.put(D.rng.choice(kinds), x + math.cos(ang) * r, y + math.sin(ang) * r, D.rng.uniform(0.0, 360.0), margin=1.5):
                n += 1
        if D.n > PROP_CAP - 70:
            break
    # a few drifts along the foot of each wall
    for _ in range(18):
        wall_y = (A.Y0 + A.WT + 14.0) if D.rng.random() < 0.55 else (A.Y1 - A.WT - 60.0)
        x = D.rng.uniform(A.X0 + 40.0, A.X1 - 40.0)
        for _k in range(D.rng.randint(1, 3)):
            D.put(D.rng.choice(kinds), x + D.rng.uniform(-18.0, 18.0), wall_y + D.rng.uniform(0.0, 14.0), D.rng.uniform(0.0, 360.0), margin=1.5)
    return n


def ceiling_props(A, D):
    """pipes and ducts over the panel grid, cables hanging from the missing panels"""
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
    D.put(M['valve'], xw + 14.0, 3790.0, 90.0, z=60.0, ignore_keep=True, margin=0.0)       # the winch wheel: a valve wheel on the wall beside the door
    D.put(M['warn'], xw + 4.0, 3764.0, 0.0, z=100.0, ignore_keep=True, margin=0.0)
    D.put(M['cage'], xw + 6.0, 4040.0, 0.0, z=140.0, ignore_keep=True, margin=0.0)


# ------------------------------------------------------------------------------------------------ light
def lights(A, m, report):
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, **k)
    yin = A.Y1 - A.WT
    for k, (x, y) in enumerate(A.live):                  # a tight downward pool under every live panel
        L((x, y, 176.0), color=(0.86, 1.0, 0.90), radius=170.0, intensity=0.55, type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    for i in range(5):
        kind = A.BAYS[i]
        hue = HUE[kind]
        cx = A.BAY_X[i] + A.BAY_W / 2.0
        L((cx, yin - 26.0, A.AP_H + 40.0), color=hue, radius=110.0, intensity=0.08, id='light_neon_%d' % (i + 1))                    # the shop's one hue: the sign's spill
        L((cx, A.Y1 + 70.0, 176.0), color=(1.0, 0.88, 0.68), radius=240.0, intensity=0.2, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=58.0, id='light_key_%d' % (i + 1))
        wp = (cx, A.Y1 + 40.0, 176.0)
        wt = (cx, A.BACK_Y, 70.0)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(wp, wt)))
        d = [(wt[j] - wp[j]) / dist for j in range(3)]
        L(wp, color=(1.0, 0.92, 0.78), radius=round(dist * 1.8, 1), intensity=round(0.2 * (dist / 200.0) ** 2, 4), type='spot', dir=d, inner=14.0, outer=46.0, id='light_wash_%d' % (i + 1))
    L((A.X1 - 60.0, 3900.0, 170.0), color=(1.0, 0.85, 0.55), radius=170.0, intensity=0.25, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    L((A.X0 + 70.0, 4040.0, 150.0), color=(1.0, 0.80, 0.50), radius=180.0, intensity=0.5, type='spot', dir=(0.0, -0.2, -1.0), inner=16.0, outer=52.0, id='light_d7_cage')
    L((A.X1 + 100.0, 3900.0, 200.0), color=(0.9, 0.9, 1.0), radius=160.0, intensity=0.05, id='light_vest')
    report['lights'] = n
    assert n <= LIGHT_CAP, n


def kit_report(m, D, path):
    zs = {}
    for p in m.flat().props:
        zs.setdefault(p['model'], 0)
        zs[p['model']] += 1
    rows = sorted(zs.items(), key=lambda kv: -kv[1])
    with open(path, 'w') as f:
        f.write('| model | zone(s) | count |\n|---|---|---|\n')
        for mod, c in rows:
            f.write('| %s | %s | %d |\n' % (mod, ','.join(sorted(R1.zones_of(mod))), c))


def dress(A, m, stage='full', foreign=None):
    import os
    D = D2(A, m)
    report = {}
    R1.setup_rooms(A, D)
    cal = bool(os.environ.get('ARC_CAL'))
    shutters(A, m, report)
    if stage == 'A':
        A.live, A.missing = [], []
        m.dress_report = report
        return report
    corridor_shell(A, m, D, report, cal)
    corridor_props(A, m, D)
    for i in range(5):
        bay(A, m, D, i)
    d7_props(A, D)
    ceiling_props(A, D)
    litter(A, D)
    lights(A, m, report)
    models = {p['model'] for p in m.flat().props}
    report['distinct_models'] = len(models)
    report.update({'props': D.n, 'skipped': D.skipped, 'foreign_models': D.foreign, 'panels': A.panels, 'live_panels': len(A.live), 'missing_panels': len(A.missing)})
    report['failed'] = D.failed[:60]
    m.dress_report = report
    m.dresser = D
    assert len(models) <= MODEL_CAP, (len(models), sorted(models))
    return report
