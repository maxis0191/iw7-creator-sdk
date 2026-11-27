r"""goods_needle_drop: the goods of NEEDLE DROP (Gil Amory, records, tapes, video rentals), unit U1 (worker A3a).

As the keeper left it at 23:30 on 31 Dec 1984: the window dressed for New Year (the new 45s, the film's one-sheet, the Roll-In poster),
the bins full, a year of rentals on the partition shelf with the gaps of what was out that night, and on the counter the dubbing deck
beside the empty case of the party tape he carried down to car 6 (FILM-LAYER section 5). Contract: film/arcade_doc.py (one layer
`goods_needle_drop`, ids `needle_drop_*`). Ids carry the trade class of each item (goods_kit_a.py) for film/goods_score_a.py.
No light of its own (rule 9: the unit holds 4 of its 5). The jukebox is the shell's.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goods_kit_a as K  # noqa: E402
from studio import build as B  # noqa: E402

ART = K.ART


def add(m, anchors):
    s = K.Shop(m, 'needle_drop')
    window(s, anchors)
    bins(s, anchors)
    sleeve_wall(s, anchors)
    high_rails(s)
    rentals(s)
    cassettes(s)
    counter(s, anchors)
    corners(s)
    B.camera(m, 'needle_drop_counter_view', (-2900.0, 4330.0, 62.0), 30.0, pitch=4.0, layer=s.layer, id='needle_drop_P__cam_counter_view__1')
    B.camera(m, 'needle_drop_window_close', (-2751.0, 4225.0, 60.0), 90.0, pitch=6.0, layer=s.layer, id='needle_drop_P__cam_window_close__1')


def sleeve(s, k, centre, facing, cls='S'):
    return s.flat(cls, 'lp', 'nd_sleeve_%d.png' % (k % 8 + 1), 'sleeve', centre, facing, thick=0.3, mat='card')


def ledge(s, name, b, lip_axis, lip_side, mat='black', lip='orange'):
    """a shelf ledge with a lip (furniture)"""
    iid = s.item('F', name)
    s.box(iid, 'board', b, mat)
    x0, y0, z0, x1, y1, z1 = b
    if lip_axis == 'y':          # lip along x, at the y side given
        ly = (y0, y0 + 0.6) if lip_side == 's' else (y1 - 0.6, y1)
        s.box(iid, 'lip', [x0, ly[0], z1, x1, ly[1], z1 + 1.6], lip)
    else:
        lx = (x0, x0 + 0.6) if lip_side == 'w' else (x1 - 0.6, x1)
        s.box(iid, 'lip', [lx[0], y0, z1, lx[1], y1, z1 + 1.6], lip)
    return iid


# ------------------------------------------------------------------------------------------------ the window
def window(s, A):
    pl = A['needle_drop.window_plinth']['box']           # x -2836..-2662, y 4314..4340, top z 22
    z0 = pl[2]
    # the film's one-sheet and the rink's Roll-In poster, taped inside the glass at the two ends of the window (FILM-LAYER item 2)
    for name, x, f in (('one_sheet', -2820.0, os.path.join(ART, 'poster_station_zero.png')), ('rollin_poster', -2678.0, os.path.join(ART, 'lightbox_orbit.png'))):
        iid = s.item('P', name)
        s.pic(iid, 'face', f, (x, 4311.2, 72.0), 's', 'poster', glow=0.6)
    # the "new this week" stand: a two-step riser in the brand's black and orange; four new 45s in front, three LPs behind, the card on top
    iid = s.item('F', 'new_stand')
    s.box(iid, 'step1', [-2790.0, 4315.0, z0, -2712.0, 4330.0, z0 + 4.0], 'black')
    s.box(iid, 'step2', [-2790.0, 4322.0, z0 + 4.0, -2712.0, 4330.0, z0 + 14.0], 'black')
    s.box(iid, 'edge1', [-2790.0, 4314.6, z0 + 3.0, -2712.0, 4315.0, z0 + 4.0], 'orange')
    s.box(iid, 'edge2', [-2790.0, 4321.6, z0 + 13.0, -2712.0, 4322.0, z0 + 14.0], 'orange')
    s.box(iid, 'card_board', [-2733.0, 4329.0, z0 + 26.0, -2715.0, 4330.0, z0 + 42.0], 'black')
    for k, x in enumerate((-2779.0, -2765.0, -2737.0, -2723.0)):
        s.prop(s.item('S', 'single_45'), 'cp_town_45_record_0%d' % (k + 1), (x, 4318.0, z0 + 4.0 + 6.4), yaw=90.0)
    for k, x in enumerate((-2783.0, -2765.0, -2731.0)):
        sleeve(s, [1, 7, 4][k], (x, 4323.0, z0 + 14.0 + 6.3), 's')
    iid = s.item('P', 'card_new45')
    s.pic(iid, 'face', 'nd_card_1.png', (-2724.0, 4329.0, z0 + 14.0 + 20.0), 's', 'card')
    # the window rack behind the plinth: two uprights and three lipped rails of face-out sleeves
    rk = A['needle_drop.window_rack_1']['box']           # y 4332..4340
    iid = s.item('F', 'window_rack')
    for k, x in enumerate((-2806.0, -2690.0)):
        s.box(iid, 'upright%d' % k, [x - 1.0, 4336.0, z0, x + 1.0, 4340.0, 104.0], 'black')
    for r, (zc, order) in enumerate(((64.0, 'ab'), (80.0, 'ca'), (96.0, 'bc'))):
        ledge(s, 'window_rail', [-2806.0, 4334.0, zc - 7.5, -2690.0, 4340.0, zc - 6.5], 'y', 's')
        for j, xc in enumerate((-2776.0, -2720.0)):
            s.flat('S', 'lp_rail', 'nd_rail_%s.png' % order[j], 'rail', (xc, 4337.0, zc), 's', thick=0.3, mat='black')
    iid = s.item('P', 'card_rental_window')
    s.pic(iid, 'face', 'nd_card_2.png', (-2790.0, 4311.2, 104.0), 's', 'card')


# ------------------------------------------------------------------------------------------------ the record bins (the shell's island)
def bins(s, A):
    face = 0
    for b in ('needle_drop.bin_1', 'needle_drop.bin_2'):
        x0, y0, z0, x1, y1, z1 = A[b]['box']              # interior 36 x 28, floor z 18
        iid = s.item('F', 'bin_divider_centre')
        s.box(iid, 'board', [(x0 + x1) / 2 - 0.4, y0, z0, (x0 + x1) / 2 + 0.4, y1, z0 + 13.0], 'black')
        for side, cx in (('w', x0 + 6.6), ('e', x1 - 6.6)):
            # the stack: LPs standing tight, read from above by their edges
            iid = s.item('S', 'lp_stack')
            s.box(iid, 'block', [cx - 6.2, y0 + 1.5, z0, cx + 6.2, y1 - 1.5, z0 + 11.2], 'black')
            s.pic(iid, 'tops', 'nd_bin_tops.png', (cx, (y0 + y1) / 2, z0 + 11.2), 'up', 'bin_tops')
            # the first sleeve at each end, face out to the browser on that side
            sleeve(s, face, (cx, y0 + 1.2, z0 + 6.4), 's')
            sleeve(s, face + 3, (cx, y1 - 1.2, z0 + 6.4), 'n')
            face += 1
            # divider cards with an orange tab, sticking up out of the stack
            for j, fy in enumerate((y0 + 9.0 + (face % 3) * 2.0, y0 + 19.0 - (face % 2) * 3.0)):
                iid = s.item('F', 'bin_divider_card')
                s.box(iid, 'card', [cx - 6.3, fy, z0, cx + 6.3, fy + 0.15, z0 + 13.6], 'card')
                tx = cx - 4.0 + 5.0 * ((face + j) % 3)
                s.box(iid, 'tab', [tx - 1.5, fy, z0 + 13.6, tx + 1.5, fy + 0.15, z0 + 15.0], 'orange')
    # two sleeves pulled half out by the last browser
    sleeve(s, 5, (A['needle_drop.bin_1']['box'][0] + 6.6, 4405.0, 18.0 + 11.0), 's')
    sleeve(s, 2, (A['needle_drop.bin_2']['box'][3] - 6.6, 4414.0, 18.0 + 10.0), 'n')


# ------------------------------------------------------------------------------------------------ the sleeve wall (the shell's carcass on the west wall)
def sleeve_wall(s, A):
    for k in range(4):
        x0, y0, z0, x1, y1, z1 = A['needle_drop.sleeve_wall_%d' % (k + 1)]['box']    # x -2942..-2926, y 4410..4472
        flip = k % 2
        ys = (y0 + 2.0, y0 + 30.0) if not flip else (y1 - 30.0, y1 - 2.0)
        iid = s.item('S', 'lp_spines')
        s.box(iid, 'block', [x0 + 1.0, ys[0], z0, x1 - 2.0, ys[1], z0 + 12.4], 'black')
        s.pic(iid, 'spines', 'nd_spines.png', (x1 - 2.0, (ys[0] + ys[1]) / 2, z0 + 6.2), 'e', 'spines')
        for j, yc in enumerate((y1 - 22.0, y1 - 8.0) if not flip else (y0 + 8.0, y0 + 22.0)):
            sleeve(s, 2 * k + j, (x0 + 4.0 + 2.0 * j, yc, z0 + 6.4), 'e')
    for j, yc in enumerate((4424.0, 4456.0)):          # two on top of the carcass
        sleeve(s, 6 + j, (-2934.0 + 3.0 * j, yc, 118.5 + 6.4), 'e')


# ------------------------------------------------------------------------------------------------ the high display rails (west wall, partition, east wall)
def high_rails(s):
    # west wall above the carcass and the door leaf
    for r, zc in enumerate((150.0,)):
        ledge(s, 'high_rail_w', [-2944.0, 4334.0, zc - 7.5, -2939.0, 4446.0, zc - 6.5], 'x', 'e')
        for j, (yc, nm) in enumerate(((4362.0, 'a'), (4418.0, 'c'))):
            s.flat('S', 'lp_rail', 'nd_rail_%s.png' % nm, 'rail', (-2943.5, yc, zc), 'e', thick=0.3, mat='black')
    # the partition: two rails over the rental shelf and the jukebox
    for r, (zc, order) in enumerate(((152.0, 'bca'), (168.0, 'cab'))):
        ledge(s, 'high_rail_n', [-2852.0, 4475.0, zc - 7.5, -2684.0, 4480.0, zc - 6.5], 'y', 's')
        for j, xc in enumerate((-2824.0, -2768.0, -2712.0)):
            s.flat('S', 'lp_rail', 'nd_rail_%s.png' % order[j], 'rail', (xc, 4479.6, zc), 's', thick=0.3, mat='black')
    # the east wall over the counter
    ledge(s, 'high_rail_e', [-2661.0, 4397.0, 124.5, -2656.0, 4453.0, 125.5], 'x', 'w')
    s.flat('S', 'lp_rail', 'nd_rail_b.png', 'rail', (-2656.4, 4425.0, 132.0), 'w', thick=0.3, mat='black')


# ------------------------------------------------------------------------------------------------ the rental shelf on the partition
RENTAL_GAPS = {(0, 3), (0, 9), (1, 1), (1, 7), (1, 10), (2, 4), (2, 5)}      # out on rent that night


def rentals(s):
    x0, x1 = -2852.0, -2742.0
    iid = s.item('F', 'rental_shelf')
    for k, x in enumerate((x0, x1 - 1.5)):
        s.box(iid, 'end%d' % k, [x, 4470.0, 52.0, x + 1.5, 4480.0, 124.0], 'black')
    s.box(iid, 'back', [x0, 4479.0, 52.0, x1, 4480.0, 124.0], 'black')
    n = 0
    for r, zb in enumerate((60.0, 84.0, 108.0)):
        s.box(iid, 'board%d' % r, [x0, 4470.0, zb - 1.0, x1, 4480.0, zb], 'black')
        s.box(iid, 'edge%d' % r, [x0, 4469.6, zb - 1.0, x1, 4470.0, zb], 'orange')
        for c in range(12):
            if (r, c) in RENTAL_GAPS:
                continue
            x = x0 + 6.0 + c * 8.9
            pic = 'nd_tape_station_zero.png' if (r, c) == (1, 5) else 'nd_tape_%d.png' % ((n % 6) + 1)
            n += 1
            s.flat('S', 'vhs_box', pic, 'tape', (x, 4472.5, zb + 6.85), 's', thick=1.0, mat='black')
    iid = s.item('P', 'card_rental')
    s.pic(iid, 'face', 'nd_card_2.png', (-2797.0, 4479.6, 134.0), 's', 'card')


# ------------------------------------------------------------------------------------------------ the cassette racks on the east wall
def cassettes(s):
    for k, yc in enumerate((4334.0, 4362.0)):
        iid = s.flat('S', 'cassette_rack', 'nd_cassette_rack.png', 'cassette_rack', (-2659.0, yc, 61.0), 'w', thick=3.0, mat='black')
        for r in range(5):
            z = 46.0 + r * 6.0
            s.box(iid, 'lip%d' % r, [-2660.5, yc - 12.0, z, -2659.0, yc + 12.0, z + 0.8], 'chrome')
    iid = s.item('P', 'card_c90')
    s.pic(iid, 'face', 'nd_card_3.png', (-2656.0, 4348.0, 86.0), 'w', 'card')


# ------------------------------------------------------------------------------------------------ the counter
def counter(s, A):
    x0, y0, z0, x1, y1, z1 = A['needle_drop.counter_top']['box']        # x -2686..-2660, y 4380..4470, top z 40
    s.prop(s.item('T', 'register'), 'park_cash_register', (-2673.0, 4394.0, z0), yaw=270.0)
    s.prop(s.item('T', 'dubbing_deck'), 'cp_town_tape_recorder', (-2672.0, 4418.0, z0), yaw=270.0)
    # the empty case of the party tape, open, its J-card in the keeper's marker (the hidden-song trail starts here: FILM-LAYER 5)
    iid = s.item('T', 'party_tape_case')
    s.box(iid, 'base', [-2681.0, 4432.8, z0, -2676.7, 4435.6, z0 + 0.35], 'glass')
    s.box(iid, 'base_tray', [-2680.6, 4433.1, z0, -2677.1, 4435.3, z0 + 0.2], 'black')
    s.box(iid, 'lid', [-2681.0, 4435.9, z0, -2676.7, 4438.7, z0 + 0.3], 'glass')
    s.pic(iid, 'jcard', 'nd_party_jcard.png', (-2678.85, 4437.3, z0 + 0.3), 'up', 'jcard')
    s.prop(s.item('T', 'turntable'), 'cp_rave_turntable_01', (-2673.0, 4452.0, z0), yaw=180.0)
    s.prop(s.item('T', 'headphones'), 'misc_interior_headphones_01_variation', (-2669.0, 4465.0, z0), yaw=30.0)
    iid = s.item('P', 'card_used_lps')
    s.pic(iid, 'face', 'nd_card_4.png', (-2687.2, 4425.0, 24.0), 'w', 'card')


def corners(s):
    # four 45s pinned on the east wall over the cassette racks
    for k, (y, z) in enumerate(((4334.0, 98.0), (4349.0, 102.0), (4364.0, 98.0), (4379.0, 103.0))):
        s.prop(s.item('S', 'single_45_wall'), 'cp_town_45_record_0%d' % (k % 5 + 2), (-2656.4, y, z), yaw=0.0)
    # a milk crate of records in the corner by the jukebox (a crate by its model name: rule 6 filler, one)
    s.prop(s.item('X', 'record_crate'), 'cp_disco_record_milk_crate', (-2697.0, 4469.0, 0.0), yaw=12.0, clip=[-8.0, -8.0, 0.0, 8.0, 8.0, 13.0])
