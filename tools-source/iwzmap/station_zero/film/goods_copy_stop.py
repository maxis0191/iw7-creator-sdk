r"""goods_copy_stop: the goods of COPY STOP (Ines Varga, draughtswoman; process blue and white), worker A3b, 27 Nov 2026.

`add(m, anchors)` (contract: film/arcade_doc.py). As she left it at 23:30 on 31 December 1984: the machines left running, paper everywhere,
the gala programmes she printed stacked on the counter, and in the front pigeonhole the uncollected forty-copy job (FILM-LAYER 5: the top
sheet of Dr. Strand's 1983 memo, its words not ours: typewriter texture, the LODESTAR mark, a red stamp COPY 1 OF 40 = PLACEHOLDER words).

Shell facts this module builds on (arcade_shell.py): unit x -2630..-1980, front glass y 4306, partition y 4480; the wheel at (-2554, 4460):
nothing of ours within 64 of it; the back-room door x -2337..-2273 kept clear; copiers at x -2455 and -2375 (bodies y 4435..4465);
counter x -2265..-2085, y 4376..4402, top 40; plan chest x -2614..-2574, y 4340..4420, top 36; pigeonholes x -2018..-1998, y 4402..4470;
photo booth x -2042..-1998, y 4328..4392 (front face y 4328, curtain on its west side).
"""
import math

import goods_kit_b as GK
from goods_kit_b import M, art, art_b, obox, prism, tilt, paper_stack, ream, ream_stack, Kit
from studio import build as B
import shellgeo as G

SHOP = 'copy_stop'
GY = 4306.0            # the front glass
PART_Y = 4480.0
WHEEL = (-2554.0, 4460.0)


def _far_from_wheel(x, y, r=0.0):
    assert math.hypot(x - WHEEL[0], y - WHEEL[1]) - r >= 64.0, ('within 64 of the wheel', x, y)


def window_west(K):
    """the west window, built up to eye height (round 2: the riser hides everything under z 14; the wheel's model must not be the first thing
    that reads): a wall of reams in colour blocks on open shelves (this shop's bottle wall) screening the wheel, a full-height diazo print,
    the light table with her lamp, a rack of large rolled drawings by the door, and a line of finished jobs hung across the top of the glass"""
    K.clip(K.item('window_display'), [-2606.0, GY + 1.0, 0.0, -2376.0, 4342.0, 64.0])
    # the ream wall: open white shelving, five boards, reams in blocks of colour (canary, salmon, green, blue, white), wrappers to the hall
    it = K.item('ream_wall')
    wx0, wx1, wy0, wy1 = -2604.0, -2500.0, 4312.0, 4334.0
    for k, x in enumerate((wx0, (wx0 + wx1) / 2, wx1)):
        K.box(it, 'upright%d' % k, [x - 0.8, wy0, 0.0, x + 0.8, wy1, 112.0], M['white'])
    boards = (16.0, 38.0, 60.0, 82.0, 104.0)
    for k, z in enumerate(boards):
        K.box(it, 'board%d' % k, [wx0, wy0, z - 1.0, wx1, wy1, z], M['white'])
    for k, z in enumerate(boards[1:]):                                       # round 3: shelf-light strips (pass 3: the wall read black from the hall)
        K.sign(it, 'strip%d' % k, art_b('h9_warm_strip.png'), ((wx0 + wx1) / 2, wy0 + 3.0, z - 1.0), (0.0, 0.0, -1.0), (100.0, 3.0),
               emissive={'color': [0.92, 0.96, 1.0], 'strength': 2.5}, lift=0.1)
    blocks = (('yellow', 'yellow', 'pink', 'pink', 'green', 'green', 'blue', 'blue'),
              ('pink', 'pink', None, None, 'yellow', 'yellow', 'green', 'green'),
              ('blue', 'blue', 'green', 'green', 'pink', 'pink', None, None),
              (None, None, 'yellow', 'yellow', 'blue', 'blue', 'pink', 'pink'))
    for lv, z in enumerate(boards[:4]):
        for j in range(8):
            x = wx0 + 7.5 + 12.6 * j + (1.6 if j >= 4 else 0.0)
            n = 9 if (lv + j) % 5 else 7
            ream_stack(K, (x, (wy0 + wy1) / 2 - 1.0, z), n, yaw=((j * 7 + lv) % 3) - 1.0, colour=blocks[lv][j])
    for j in range(3):                                                       # the top board: rolls of drawings lying, a few reams
        K.prop('blueprint_roll', 'cp_town_blueprint_teleporter_roll', (wx0 + 20.0 + 16.0 * j, (wy0 + wy1) / 2, 105.3), angles=[90.0, 0.0, 0.0])
    ream_stack(K, (wx1 - 14.0, (wy0 + wy1) / 2, 104.0), 3)
    # the diazo print pinned full height on a board
    it = K.item('window_print')
    px, py = -2477.0, 4318.0
    K.box(it, 'board', [px - 20.0, py, 14.0, px + 20.0, py + 1.2, 138.0], M['wood'])
    K.sign(it, 'print', art_b('cs_blueprint_tall.png'), (px, py, 76.0), (0.0, -1.0, 0.0), (36.0, 72.0), lift=0.2)
    for k, (dx, dz) in enumerate(((-16, 111), (16, 111), (-16, 41), (16, 41))):
        K.box(it, 'pin%d' % k, [px + dx - 0.6, py - 0.6, dz - 0.6, px + dx + 0.6, py, dz + 0.6], M['red'])
    # the light table: a lit top tilted toward the hall, a pencil drawing on vellum, her lamp on its side shelf (the shop's one practical)
    it = K.item('light_table')
    x0, x1, y0, y1 = -2454.0, -2412.0, 4314.0, 4338.0
    for k, (x, y) in enumerate(((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2))):
        K.box(it, 'leg%d' % k, [x - 1.2, y - 1.2, 0.0, x + 1.2, y + 1.2, 38.0 if y < 4330 else 46.0], M['grey'])
    top = obox(((x0 + x1) / 2, (y0 + y1) / 2, 0.0), (x1 - x0, y1 - y0, 1.5), faces='tnsewb', fit=False, tile=16.0)
    top = ([[[p[0], p[1], p[2] + 41.0] for p in t] for t in top[0]], top[1])
    K.mesh(it, 'frame', M['grey'], tilt(top, (0, (y0 + y1) / 2, 42.0), 20.0))
    glow = obox(((x0 + x1) / 2, (y0 + y1) / 2, 0.0), (x1 - x0 - 3, y1 - y0 - 3, 0.1), faces='t')
    glow = ([[[p[0], p[1], p[2] + 42.55] for p in t] for t in glow[0]], glow[1])
    K.mesh(it, 'glass', M['white_glow'], tilt(glow, (0, (y0 + y1) / 2, 42.0), 20.0))
    n = (0.0, -math.sin(math.radians(20.0)), math.cos(math.radians(20.0)))
    K.decal(it, 'drawing', art_b('cs_vellum_drawing.png'), ((x0 + x1) / 2, (y0 + y1) / 2 + 0.6, 42.6), n, (36.0, 18.0), lift=0.25)
    K.box(it, 'shelf', [x1 - 1.0, y0 + 4.0, 36.0, x1 + 9.0, y0 + 18.0, 37.2], M['grey'])
    K.box(it, 'shelf_leg', [x1 + 6.0, y0 + 9.0, 0.0, x1 + 8.0, y0 + 11.0, 36.0], M['grey'])
    K.prop('desk_lamp', 'p7_light_lamp_desk_vintage_01_on', (x1 + 4.0, y0 + 11.0, 37.2), yaw=200.0)
    # the shop's one practical (pass 4: the ream wall read black from the hall, the desk lamp did not reach it): a display light bar on the
    # window head over the ream wall, lighting its face (baked, emergency)
    K.fixture('window_light', 'wall_led', (-2552.0, GY + 2.0, 136.0), 90.0, kelvin=4800, intensity=1.4, radius=1.0)
    # the rack of large rolled drawings by the door: a stand, tall rolls in blue and white standing in it up to eye height
    it = K.item('roll_rack')
    c = (-2391.0, 4326.0)
    K.box(it, 'base', [c[0] - 8, c[1] - 9, 0.0, c[0] + 8, c[1] + 9, 3.0], M['wood'])
    K.box(it, 'collar', [c[0] - 8, c[1] - 9, 40.0, c[0] + 8, c[1] + 9, 42.0], M['wood'])
    for k, (dx, dy) in enumerate(((-7, -8), (7, -8), (7, 8), (-7, 8))):
        K.box(it, 'post%d' % k, [c[0] + dx - 0.8, c[1] + dy - 0.8, 3.0, c[0] + dx + 0.8, c[1] + dy + 0.8, 40.0], M['wood'])
    for k, (dx, dy) in enumerate(((-4, -5), (0, -6), (4, -4), (-5, 0), (1, 0), (5, 2), (-3, 5), (2, 6), (6, 6))):
        roll = K.item('rolled_drawing')
        K.mesh(roll, 'body', M['blue'] if k % 3 else M['white'], prism((c[0] + dx, c[1] + dy, 3.0), 1.9, 52.0 + (k * 5) % 14, 10))
    # finished jobs hung on a line across the top of the glass (copies, programmes, prints, a card), each in a bulldog clip
    it = K.item('job_line')
    ly, lz = 4319.0, 126.0
    K.box(it, 'wire', [-2602.0, ly - 0.1, lz - 0.1, -2380.0, ly + 0.1, lz + 0.1], M['black'])
    hang = (('cs_copy_page.png', 8.5, 11.0), ('mat_cs_programme.png', 6.0, 9.0), ('cs_blueprint_sheet.png', 18.0, 9.0), ('cs_copy_page.png', 8.5, 11.0),
            ('cs_card_1.png', 12.0, 7.5), ('mat_cs_programme.png', 6.0, 9.0), ('cs_vellum_drawing.png', 16.0, 12.0), ('cs_copy_page.png', 8.5, 11.0),
            ('mat_cs_programme.png', 6.0, 9.0), ('cs_blueprint_sheet.png', 18.0, 9.0), ('cs_copy_page.png', 8.5, 11.0))
    x = -2596.0
    for k, (pic, w, h) in enumerate(hang):
        x += w / 2
        K.sign(it, 'sheet%d' % k, art_b(pic), (x, ly, lz - 1.0 - h / 2), (0.0, -1.0, 0.0), (w, h), rot=((k * 37) % 7) - 3.0, lift=0.1)
        K.box(it, 'clip%d' % k, [x - 0.8, ly - 0.5, lz - 1.6, x + 0.8, ly + 0.3, lz + 0.4], M['black'])
        x += w / 2 + 6.0
    # her cards on the glass, eye level
    for k, (x, card) in enumerate(((-2560.0, 'cs_card_1.png'), (-2432.0, 'cs_card_2.png'))):
        K.sign(K.item('window_card'), 'card', art_b(card), (x, GY + 0.35, 88.0 - 3 * k), (0.0, -1.0, 0.0), (20.0, 12.5), rot=(-2.0, 1.5)[k])


def window_east(K):
    """the east window: reams along the glass, a hanging board of samples, the two remaining cards"""
    K.clip(K.item('window_sill_goods'), [-2232.0, GY + 1.0, 0.0, -2048.0, 4316.0, 40.0])
    for k, x in enumerate((-2222.0, -2210.0, -2198.0, -2120.0, -2108.0)):
        for j in range(1 + (k % 3)):
            ream(K, (x, 4311.5, 2.1 * j), yaw=90.0 + ((k + j) % 3) * 2.0 - 2.0, colour=('yellow', None, 'blue', 'pink', 'green')[k])
    # spiral-bound sample books standing open along the glass
    for k, x in enumerate((-2178.0, -2160.0, -2142.0)):
        it = K.item('sample_book')
        for s, side in enumerate((-1, 1)):
            leaf = obox((x + side * 4.3, 4312.0, 0.0), (8.5, 0.4, 11.0), yaw=side * 10.0, faces='nsew', fit=True)
            K.mesh(it, 'leaf%d' % s, K.mat('mat_cs_programme.png') if (k == 1 and s == 0) else M['white'], leaf)
        K.mesh(it, 'spine', M['black'], prism((x, 4312.0, 0.0), 0.5, 11.0, 6))
    # a board of samples hung on chains from the transom (laminated cards, a programme, copies): no floor footprint
    it = K.item('sample_board')
    bx, by = -2196.0, 4314.0
    K.box(it, 'board', [bx - 22.0, by - 0.5, 96.0, bx + 22.0, by + 0.5, 126.0], 'w/wood_antique_panel_trim_01')      # AC2: a pinboard of wood (its back, seen from inside, was the blue metal in shadow: a black cutout)
    for k, dx in enumerate((-18.0, 18.0)):
        K.box(it, 'chain%d' % k, [bx + dx - 0.2, by - 0.2, 126.0, bx + dx + 0.2, by + 0.2, 132.0], M['chrome'])
    for k, (dx, pic, w, h) in enumerate(((-13.0, 'cs_copy_page.png', 12.0, 15.5), (0.5, 'cs_card_3.png', 12.0, 7.5), (14.0, 'cs_copy_page.png', 12.0, 15.5))):
        K.sign(it, 'sample%d' % k, art_b(pic), (bx + dx, by - 0.5, 111.0 + (3.0 if k == 1 else 0.0)), (0.0, -1.0, 0.0), (w, h), rot=(-3.0, 0.0, 2.5)[k], lift=0.12 + 0.03 * k)
    K.sign(it, 'programme', art_b('mat_cs_programme.png'), (bx + 0.5, by - 0.5, 102.0), (0.0, -1.0, 0.0), (5.0, 7.5), lift=0.2)
    for k, (x, card) in enumerate(((-2072.0, 'cs_card_3.png'), (-2215.0, 'cs_card_4.png'))):
        K.sign(K.item('window_card'), 'card', art_b(card), (x, GY + 0.35, 86.0 + 2 * k), (0.0, -1.0, 0.0), (20.0, 12.5), rot=(1.5, -2.5)[k])


def blueprint_bay(K):
    """the diazo machine on the plan chest with a long print half out of it, draping down the drawers; rolls; the paper stock shelf"""
    it = K.item('blueprint_machine')
    x0, x1, y0, y1, z = -2612.0, -2590.0, 4342.0, 4390.0, 36.0
    K.box(it, 'body', [x0, y0, z, x1, y1, z + 13.0], M['beige'])
    K.box(it, 'top', [x0 - 0.5, y0 - 0.5, z + 13.0, x1 + 0.5, y1 + 0.5, z + 14.5], M['grey'])
    K.box(it, 'feed', [x1, y0 + 2.0, z + 9.0, x1 + 6.0, y1 - 2.0, z + 10.0], M['grey'])
    K.mesh(it, 'roller', M['chrome'], G.cylinder((x1 + 0.6, y0 + 2.0, z + 11.0), (x1 + 0.6, y1 - 2.0, z + 11.0), 0.9, 10))
    K.box(it, 'lamp_window', [x1 - 0.2, y0 + 6.0, z + 3.0, x1 + 0.05, y1 - 6.0, z + 6.0], M['white_glow'])
    K.box(it, 'panel', [x1 - 0.1, y0 + 2.0, z + 2.0, x1 + 0.1, y0 + 5.0, z + 8.0], M['black'])
    # the print: out of the feed onto the chest top and over its edge
    p = K.item('blueprint_print')
    K.decal(p, 'flat', art_b('cs_blueprint_sheet.png'), (x1 + 8.0, (y0 + y1) / 2, 36.0), (0.0, 0.0, 1.0), (14.0, 40.0), rot=90.0)
    K.sign(p, 'drape', art_b('cs_blueprint_sheet.png'), (-2574.0, (y0 + y1) / 2, 22.0), (1.0, 0.0, 0.0), (40.0, 26.0), lift=0.3)
    for k in range(2):                                                       # rolls of drawings on the machine
        K.prop('blueprint_roll', 'cp_town_blueprint_teleporter_roll', (x0 + 6.0 + 5 * k, (y0 + y1) / 2, z + 14.5 + 1.3), angles=[90.0, 90.0 + 4 * k, 0.0])
    # the paper stock shelf on the west wall over the chest (no floor footprint; 82 or more from the wheel)
    sh = K.item('stock_shelf')
    for k, z in enumerate((92.0, 112.0)):
        K.box(sh, 'board%d' % k, [-2614.0, 4342.0, z - 1.0, -2600.0, 4392.0, z], M['white'])
        for j, yy in enumerate((4346.0, 4386.0)):
            K.box(sh, 'bracket%d_%d' % (k, j), [-2614.0, yy - 0.5, z - 6.0, -2604.0, yy + 0.5, z - 1.0], M['grey'])
        for j in range(4):
            for h in range(1 + (j + k) % 3):
                ream(K, (-2607.5, 4348.5 + 11.5 * j, z + 2.1 * h), yaw=90.0 + ((j + h) % 2) * 2.0)
    for k in range(3):
        K.prop('blueprint_roll', 'cp_town_blueprint_teleporter_roll', (-2606.0 + (k % 2) * 3.0, 4367.0 + k * 2.0, 133.4 + (k // 2) * 2.4), angles=[90.0, 90.0, 0.0])
    _far_from_wheel(-2590.0, 4392.0)


def copiers(K):
    """the two copiers, left running: copies in the output trays, an original on the lid, reams between them, the toner drum"""
    for k, ccx in enumerate((-2455.0, -2375.0)):
        cy = 4450.0
        paper_stack(K, 'copies_out', (ccx + 27.0, cy, 21.5), (8.5, 11.0, 1.0 + 0.8 * k), yaw=90.0 + 3.0 * k, top='cs_copy_page.png')
        orig = K.item('original_on_glass')
        K.decal(orig, 'sheet', art_b('cs_copy_page.png'), (ccx - 2.0 + 3 * k, cy - 1.0, 40.0), (0.0, 0.0, 1.0), (8.5, 11.0), rot=-8.0 + 20 * k)
    K.clip(K.item('ream_pile'), [-2423.0, 4436.0, 0.0, -2398.0, 4464.0, 64.0])
    for k in range(8):                                                       # reams stacked between the copiers, the sorter's side kept free
        ream(K, (-2404.5, 4443.0 + 13.0 * (k % 2), 2.1 * (k // 2)), yaw=90.0 + (k % 3) - 1.0, colour=(None, None, 'yellow', None)[k % 4])
    # copier 1's sorter: a tower of ten bins on its east side, copies in every bin (the job was running)
    it = K.item('sorter')
    sx0, sx1, sy0, sy1 = -2423.0, -2411.0, 4440.0, 4460.0
    K.box(it, 'back', [sx1 - 1.0, sy0, 18.0, sx1, sy1, 60.0], M['beige'])
    for k, yy in enumerate((sy0, sy1 - 1.0)):
        K.box(it, 'side%d' % k, [sx0, yy, 18.0, sx1, yy + 1.0, 60.0], M['beige'])
    K.box(it, 'cap', [sx0, sy0, 58.0, sx1, sy1, 60.0], M['grey'])
    for k in range(10):
        z = 20.0 + 3.8 * k
        K.box(it, 'bin%d' % k, [sx0, sy0 + 1.0, z, sx1 - 1.0, sy1 - 1.0, z + 0.4], M['grey'])
        paper_stack(K, 'sorted_copies', ((sx0 + sx1) / 2 - 0.5, (sy0 + sy1) / 2, z + 0.4), (8.5, 11.0, 0.5 + 0.1 * (k % 4)), yaw=90.0)
    paper_stack(K, 'opened_ream', (-2404.5, 4449.0, 8.4), (8.5, 11.0, 1.4), yaw=4.0)
    it = K.item('toner_drum')
    tx, ty = -2486.0, 4436.0
    _far_from_wheel(tx, ty, 6.0)
    K.mesh(it, 'drum', M['black'], prism((tx, ty, 0.0), 6.0, 19.0, 12))
    K.mesh(it, 'lid', M['grey'], prism((tx, ty, 19.0), 6.2, 1.2, 12))
    K.sign(it, 'label', art_b('cs_toner_PLACEHOLDER.png'), (tx, ty - 6.0, 10.0), (0.0, -1.0, 0.0), (10.0, 2.5), lift=0.2)
    K.clip(it, [tx - 6.0, ty - 6.0, 0.0, tx + 6.0, ty + 6.0, 20.0])


def drawings_wall(K):
    """her drawings and prints pinned on the partition over the copiers (seen through the doors from the hall), clear of the wheel"""
    for k, (x, z, pic, w, h, rot) in enumerate(((-2452.0, 112.0, 'cs_blueprint_sheet.png', 44.0, 22.0, -1.5), (-2400.0, 104.0, 'cs_vellum_drawing.png', 36.0, 27.0, 2.0),
                                                (-2356.0, 116.0, 'cs_blueprint_sheet.png', 34.0, 17.0, 1.0))):
        it = K.item('pinned_drawing')
        K.sign(it, 'sheet', art_b(pic), (x, PART_Y, z), (0.0, -1.0, 0.0), (w, h), rot=rot, lift=0.2 + 0.05 * k)
    _far_from_wheel(-2474.0, PART_Y)


def counter(K):
    """the service counter, west to east: guillotine, binder, the gala programmes, the job tray, the stamp tree, stapler, laminator, till;
    behind it the price board and her two notices"""
    z = 40.0
    yc = 4389.0
    # guillotine cutter (blade along y, raised at the front)
    it = K.item('guillotine')
    gx = -2250.0
    K.box(it, 'base', [gx - 9.0, yc - 12.0, z, gx + 9.0, yc + 12.0, z + 1.2], M['white'])
    K.box(it, 'grid', [gx - 8.0, yc - 11.0, z + 1.2, gx + 6.0, yc + 11.0, z + 1.25], 'w/linoleum_floor_tiles_02_dark')
    K.box(it, 'fence', [gx - 9.0, yc + 10.5, z + 1.2, gx + 9.0, yc + 12.0, z + 2.6], M['alu'])
    blade = G.merge(obox((gx + 7.5, yc, z + 1.2), (1.2, 24.0, 1.6), fit=False, tile=8.0), obox((gx + 7.5, yc - 11.0, z + 2.8), (2.4, 3.0, 2.4), fit=False))
    K.mesh(it, 'blade', M['chrome'], tilt(blade, (0, yc + 11.0, z + 2.0), -32.0))
    paper_stack(K, 'cut_sheets', (gx - 2.0, yc - 1.0, z + 1.25), (8.5, 11.0, 0.8), yaw=2.0, top='cs_copy_page.png')
    # spiral binder
    it = K.item('spiral_binder')
    bx = -2230.0
    K.box(it, 'body', [bx - 7.0, yc - 6.0, z, bx + 7.0, yc + 5.0, z + 5.0], M['grey'])
    K.box(it, 'deck', [bx - 7.5, yc - 6.5, z + 5.0, bx + 7.5, yc + 5.5, z + 5.6], M['black'])
    K.mesh(it, 'lever', M['chrome'], tilt(obox((bx + 8.0, yc - 1.0, z + 3.0), (0.6, 12.0, 0.6), fit=False), (0, yc + 5.0, z + 3.0), -24.0))
    for k in range(3):
        K.mesh(it, 'comb%d' % k, 'w/plastic_wall_plain_blue_01', prism((bx - 4.0 + 4 * k, yc + 3.0, z + 5.6), 0.5, 2.0, 6))
    # the gala programmes she printed
    for k, (dx, h, yaw) in enumerate(((-2206.0, 2.4, 3.0), (-2195.0, 1.8, -7.0), (-2184.0, 3.0, 11.0))):
        paper_stack(K, 'programmes', (dx, yc - 2.0, z), (6.0, 9.0, h), yaw=yaw, top_mat=K.mat('mat_cs_programme.png'))
    paper_stack(K, 'programmes', (-2194.0, yc - 8.0, z + 0.01), (6.0, 9.0, 0.15), yaw=58.0, top_mat=K.mat('mat_cs_programme.png'))
    # the wire tray of uncollected jobs
    it = K.item('job_tray')
    jx = -2165.0
    K.box(it, 'bottom', [jx - 6.5, yc - 8.0, z, jx + 6.5, yc + 8.0, z + 0.4], M['chrome'])
    for k, b in enumerate(([jx - 6.5, yc - 8.0, z, jx - 6.2, yc + 8.0, z + 3.0], [jx + 6.2, yc - 8.0, z, jx + 6.5, yc + 8.0, z + 3.0],
                           [jx - 6.5, yc - 8.0, z, jx + 6.5, yc - 7.7, z + 3.0], [jx - 6.5, yc + 7.7, z, jx + 6.5, yc + 8.0, z + 3.0])):
        K.box(it, 'side%d' % k, b, M['chrome'])
    for k in range(3):
        j = paper_stack(K, 'job', (jx, yc, z + 0.4 + 0.9 * k), (8.5, 11.0, 0.8), yaw=(-4.0, 3.0, -1.0)[k], top='cs_copy_page.png' if k < 2 else None)
    K.decal(j, 'ticket', art_b('cs_ticket_a.png'), (jx + 1.0, yc - 3.0, z + 0.4 + 0.9 * 3), (0.0, 0.0, 1.0), (5.0, 3.1), rot=-6.0)
    # rubber stamp tree
    it = K.item('stamp_tree')
    sx, sy = -2150.0, yc + 2.0
    K.mesh(it, 'base', M['wood'], prism((sx, sy, z), 4.0, 1.0, 12))
    K.mesh(it, 'post', M['chrome'], prism((sx, sy, z + 1.0), 0.35, 10.0, 6))
    for tier, tz in enumerate((z + 6.5, z + 10.0)):
        for k in range(3):
            a = math.radians(120 * k + 60 * tier)
            ex, ey = sx + 3.2 * math.cos(a), sy + 3.2 * math.sin(a)
            K.mesh(it, 'arm%d%d' % (tier, k), M['chrome'], G.cylinder((sx, sy, tz), (ex, ey, tz), 0.2, 4, caps=False))
            K.mesh(it, 'handle%d%d' % (tier, k), M['wood'], prism((ex, ey, tz - 2.6), 0.55, 2.4, 8))
            K.mesh(it, 'die%d%d' % (tier, k), M['rubber'], obox((ex, ey, tz - 3.3), (1.6, 1.0, 0.7), yaw=120 * k, fit=False))
    # stapler
    it = K.item('stapler')
    K.mesh(it, 'base', M['black'], obox((-2140.0, yc - 4.0, z), (1.6, 6.5, 0.8), yaw=-12.0, fit=False))
    K.mesh(it, 'arm', M['chrome'], obox((-2140.0, yc - 4.0, z + 0.8), (1.4, 6.2, 1.1), yaw=-12.0, fit=False))
    # laminator with a card half out of it
    it = K.item('laminator')
    lx = -2127.0
    K.box(it, 'body', [lx - 8.0, yc + 1.0, z, lx + 8.0, yc + 9.0, z + 5.0], M['beige'])
    K.box(it, 'slot', [lx - 6.0, yc + 0.9, z + 2.0, lx + 6.0, yc + 1.0, z + 2.6], M['black'])
    K.mesh(it, 'card', M['glass'], obox((lx, yc - 2.0, z + 2.1), (9.0, 6.0, 0.15), fit=False))
    K.decal(it, 'card_face', art_b('cs_card_1.png'), (lx, yc - 2.0, z + 2.25), (0.0, 0.0, 1.0), (8.0, 5.0))
    # the till: the shop's old blue register, keys to her side
    K.prop('till', 'cp_town_cash_register', (-2100.0, 4380.0, z), yaw=-90.0)
    # behind the counter: the price board, her two notices pinned beside it
    it = K.item('price_board')
    K.sign(it, 'board', art('board_copy_stop.png'), (-2176.0, PART_Y, 78.0), (0.0, -1.0, 0.0), (44.0, 32.3), lift=0.4)
    K.box(it, 'frame', [-2199.0, PART_Y - 0.6, 61.0, -2153.0, PART_Y, 95.0], M['black'])
    for k, (x, pic) in enumerate(((-2216.0, 'cs_notice_drafting.png'), (-2136.0, 'cs_notice_paper_tray.png'))):
        K.sign(K.item('notice'), 'sheet', art_b(pic), (x, PART_Y, 80.0 - 2 * k), (0.0, -1.0, 0.0), (12.0, 16.0), rot=(2.0, -3.0)[k], lift=0.25)


def pigeonholes(K):
    """the pigeonholes of uncollected jobs (east wall, facing west): dividers, one job a hole; in the front hole the forty-copy job"""
    x0, x1 = -2018.0, -1998.0
    y0, y1 = 4402.0, 4470.0
    levels = (6.0, 28.5, 51.0, 73.5)
    it = K.item('pigeonhole_dividers')
    n = 6
    pitch = (y1 - y0) / n
    for k in range(1, n):
        y = y0 + k * pitch
        K.box(it, 'div%d' % k, [x0, y - 0.4, 6.0, x1 - 0.5, y + 0.4, 94.0], M['white'])
    import random
    rnd = random.Random(1984)
    for lv, z in enumerate(levels):
        for k in range(n):
            yc = y0 + (k + 0.5) * pitch
            if (lv, k) == (2, 0):
                continue                                                         # the front hole: the forty-copy job, below
            if rnd.random() < 0.18:
                continue                                                         # a few holes already collected
            if rnd.random() < 0.55:
                it = K.item('job_envelope')
                h = rnd.choice((0.8, 1.2, 2.0))
                K.mesh(it, 'body', K.mat('mat_cs_envelope.png'), obox((x0 + 9.5 + rnd.uniform(-1, 1), yc, z), (12.0, 9.0, h), yaw=-90.0 + rnd.uniform(-4, 4), fit=True))
            else:
                paper_stack(K, 'job', (x0 + 9.5 + rnd.uniform(-1, 1), yc, z), (8.5, 11.0, rnd.choice((0.6, 1.0, 1.6))), yaw=-90.0 + rnd.uniform(-5, 5),
                            top=rnd.choice(('cs_copy_page.png', None)))
    # the forty-copy job: forty copies and the original, squared, the top sheet the memo; her yellow ticket under its edge
    yc = y0 + 0.5 * pitch
    job = paper_stack(K, 'forty_copy_job', (x0 + 8.5, yc, levels[2]), (8.5, 11.0, 0.9), yaw=-90.0, top_mat=K.mat('mat_cs_memo_PLACEHOLDER.png'))
    K.decal(job, 'ticket', art_b('cs_ticket_b.png'), (x0 + 2.2, yc + 1.0, levels[2] + 0.95), (0.0, 0.0, 1.0), (4.2, 2.6), rot=-80.0)
    K.sign(job, 'red_tag', art_b('cs_red_tag.png'), (x0, yc, levels[2] - 3.0), (-1.0, 0.0, 0.0), (4.4, 7.0), rot=-6.0, lift=0.3)
    K.box(job, 'band', [x0 + 3.0, yc - 4.6, levels[2] + 0.2, x0 + 4.0, yc + 4.6, levels[2] + 1.0], M['red'])
    return job


def booth(K):
    """the photo booth's lettering, the sample strip by the slot, the stool inside, a strip face down on the floor"""
    x0, x1, y0 = -2042.0, -1998.0, 4328.0
    it = K.item('booth_lettering')
    K.sign(it, 'band', art_b('cs_booth_band.png'), ((x0 + x1) / 2, y0 - 0.6, 79.5), (0.0, -1.0, 0.0), (38.0, 7.1), emissive=1.3, lift=0.1)
    K.sign(it, 'band_w', art_b('cs_booth_band.png'), (x0, y0 + 32.0, 79.0), (-1.0, 0.0, 0.0), (40.0, 7.5), emissive=1.3, lift=0.1)
    K.sign(it, 'plate', art_b('cs_booth_plate.png'), ((x0 + x1) / 2, y0, 27.0), (0.0, -1.0, 0.0), (26.0, 8.1), lift=0.1)
    K.sign(K.item('booth_sample_strip'), 'strip', art_b('cs_booth_strip.png'), (x0 + 21.0, y0 - 0.6, 57.0), (0.0, -1.0, 0.0), (24.0, 24.0), lift=0.1)
    it = K.item('booth_stool')
    sx, sy = x0 + 25.0, y0 + 37.0
    K.mesh(it, 'seat', M['red'], prism((sx, sy, 20.0), 7.0, 3.0, 16))
    K.mesh(it, 'ring', M['chrome'], prism((sx, sy, 19.4), 7.3, 0.6, 16))
    it = K.item('strip_face_down')
    K.mesh(it, 'strip', M['white'], obox((x0 - 9.0, y0 + 46.0, 0.0), (1.8, 7.6, 0.06), yaw=24.0, fit=False))


def cameras(K):
    B.camera(K.m, 'copy_stop_booth_close', (-2021.0, 4246.0, 60.0), 90.0, pitch=2.0, layer=K.layer, id='copy_stop_booth_close')
    B.camera(K.m, 'copy_stop_memo_close', (-2044.0, 4409.0, 66.0), -5.0, pitch=26.0, layer=K.layer, id='copy_stop_memo_close')
    B.camera(K.m, 'copy_stop_interior', (-2150.0, 4340.0, 64.0), 168.0, pitch=4.0, layer=K.layer, id='copy_stop_interior')
    B.camera(K.m, 'copy_stop_memo_walkby', (-2150.0, 4420.0, 62.0), 0.0, pitch=4.0, layer=K.layer, id='copy_stop_memo_walkby')    # 140 from the pigeonholes
    B.camera(K.m, 'copy_stop_far', (-2360.0, 3530.0, 62.0), 90.0, pitch=-3.0, layer=K.layer, id='copy_stop_far')     # 776 from the front glass
    B.camera(K.m, 'copy_stop_window_close', (-2500.0, 4210.0, 62.0), 90.0, pitch=6.0, layer=K.layer, id='copy_stop_window_close')


def add(m, anchors):
    K = Kit(m, SHOP)
    window_west(K)
    window_east(K)
    blueprint_bay(K)
    copiers(K)
    drawings_wall(K)
    counter(K)
    pigeonholes(K)
    booth(K)
    cameras(K)
    return K
