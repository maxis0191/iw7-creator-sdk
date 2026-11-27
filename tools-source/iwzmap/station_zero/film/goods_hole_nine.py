r"""goods_hole_nine: the goods of HOLE NUMBER NINE (Dolores Kemp; pink and chocolate), worker A3b, 27 Nov 2026.

`add(m, anchors)` (contract: film/arcade_doc.py). As she left it at 23:30 on 31 December 1984 to work the gala table: a year of stale
doughnuts in the glass racks and on the rails, the urn and the pot, cups and saucers, the till, the television still on Channel 9, pink boxes
folded flat, and on the serving counter the two things that never went down: Strand's bagged order (ticket "STRAND - TO COLLECT", PLACEHOLDER
words) and the stack of gala trays (labelled with the Zero Line roundel and 047, canon).

Shell facts (arcade_shell.py): unit x -1970..-1650; serving counter x -1954..-1768, y 4302..4330, top 42 (open to the hall, the hatch head at
z 138); display case x -1880..-1780, y 4400..4424, glass top 38; ledge x -1930..-1840, y 4458..4478, top 40 (stool bases at x -1900, -1860,
y 4440); TV shelf x -1720..-1668, y 4456..4480, z 119; the SMG wall buy at (-1948, 4440) on the west wall (kept clear); back door
x -1820..-1756 in the partition y 4480; the side door's leaf open along the east wall, y 4312..4406; the OPEN neon at (-1850, 4480, 118).
No light of ours here: a fifth light would put the shop at 0.052 lights per 1,000 (QUALITY-BAR rule 9: 0.049).
"""
import math
import random

from goods_kit_b import M, art, art_b, obox, prism, paper_stack, rings, Kit
from studio import build as B
import shellgeo as G

SHOP = 'hole_nine'
PART_Y = 4480.0
DONUT = 'food_donut'          # cp_town's chocolate ring with sprinkles, 2.4 across: scaled 1.6 to a real 3.8
DONUT_K = 1.6


def stock_rings(K, kind, c0, cols, rows, pitch, seed=0, skip=()):
    rnd = random.Random(seed)
    for i in range(cols):
        for j in range(rows):
            if (i, j) in skip:
                continue
            K.prop(kind, DONUT, (c0[0] + i * pitch + rnd.uniform(-0.3, 0.3), c0[1] + j * pitch + rnd.uniform(-0.3, 0.3), c0[2] + 0.456 * DONUT_K),
                   yaw=rnd.uniform(0, 360), scale=DONUT_K)


def tray(K, kind, x0, y0, z, w, d, glaze=None, cols=0, rows=0, pitch=4.4, seed=0, skip=(), film=False, mat=None):
    """a steel tray (w x d) with rows of authored rings in a glaze of ours, or of the stock chocolate ring (glaze='choc')"""
    it = K.item(kind)
    K.box(it, 'pan', [x0, y0, z, x0 + w, y0 + d, z + 0.4], mat or M['alu'])
    if glaze:
        K.box(it, 'liner', [x0 + 0.5, y0 + 0.5, z + 0.4, x0 + w - 0.5, y0 + d - 0.5, z + 0.45], M['white'])
    for k, b in enumerate(([x0, y0, z, x0 + w, y0 + 0.3, z + 1.0], [x0, y0 + d - 0.3, z, x0 + w, y0 + d, z + 1.0],
                           [x0, y0, z, x0 + 0.3, y0 + d, z + 1.0], [x0 + w - 0.3, y0, z, x0 + w, y0 + d, z + 1.0])):
        K.box(it, 'rim%d' % k, b, mat or M['alu'])
    c0 = (x0 + (w - (cols - 1) * pitch) / 2, y0 + (d - (rows - 1) * pitch) / 2, z + 0.4)
    if glaze == 'choc':
        stock_rings(K, 'ring_choc', c0, cols, rows, pitch, seed, skip)
    elif glaze:
        K.mesh(it, 'rings', K.mat(glaze), rings(c0, cols, rows, pitch, jitter=0.25, seed=seed, skip=skip))
    if film:
        K.box(it, 'film', [x0 - 0.2, y0 - 0.2, z + 2.6, x0 + w + 0.2, y0 + d + 0.2, z + 2.7], M['glass'])
    return it


def serving_counter(K):
    """the serving counter, open to the hall, west to east: the cake stand, napkins, sugar, the bagged order, the bell, cups and saucers,
    the till, the gala trays; two window cards on its front"""
    z, yc = 42.0, 4316.0
    # round 1: from the hall the rings did not read. A countertop pastry case at the hatch, at eye height: two glass shelves of rings on
    # white liners (honey and chocolate, against the pink room), a lit strip under its top
    it = K.item('counter_case')
    cx0, cx1, cy0, cy1 = -1952.0, -1906.0, 4305.0, 4327.0
    K.box(it, 'base', [cx0, cy0, z, cx1, cy1, z + 2.0], M['chrome'])
    K.box(it, 'top', [cx0, cy0, z + 27.0, cx1, cy1, z + 28.0], M['chrome'])
    K.sign(it, 'lamp', art_b('h9_warm_strip.png'), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, z + 27.0), (0.0, 0.0, -1.0), (40.0, 6.0),
           emissive={'color': [1.0, 0.72, 0.42], 'strength': 2.0}, lift=0.1)
    K.box(it, 'back', [cx0 + 0.5, cy1 - 0.3, z + 2.0, cx1 - 0.5, cy1, z + 27.0], M['glass'])
    for k, x in enumerate((cx0, cx1 - 0.6)):
        K.box(it, 'end%d' % k, [x, cy0, z + 2.0, x + 0.6, cy1, z + 27.0], M['chrome'])
    K.box(it, 'shelf', [cx0 + 0.6, cy0 + 0.3, z + 14.0, cx1 - 0.6, cy1 - 0.3, z + 14.4], M['glass'])
    tray(K, 'ring_tray', cx0 + 2.0, cy0 + 1.5, z + 2.0, 42.0, 19.0, glaze='mat_h9_glaze_honey.png', cols=9, rows=4, pitch=4.6, seed=41, skip=((8, 0), (8, 1), (0, 3)))
    tray(K, 'ring_tray', cx0 + 2.0, cy0 + 1.5, z + 14.4, 42.0, 19.0, glaze='choc', cols=8, rows=3, pitch=5.0, seed=42, skip=((0, 0), (1, 0), (7, 2)))
    K.prop('napkin_dispenser', 'p7_diner_table_napkin_clean', (-1900.0, yc + 5.0, z), yaw=0.0)
    for k, x in enumerate((-1892.0, -1888.0)):
        it = K.item('sugar_pourer')
        K.mesh(it, 'jar', M['glass'], prism((x, yc + 3.0 - k, z), 1.4, 4.6, 10))
        K.mesh(it, 'sugar', M['white'], prism((x, yc + 3.0 - k, z + 0.1), 1.25, 2.6, 10))
        K.mesh(it, 'cap', M['chrome'], prism((x, yc + 3.0 - k, z + 4.6), 1.5, 1.6, 10))
        K.mesh(it, 'spout', M['chrome'], G.cylinder((x, yc + 3.0 - k, z + 6.1), (x + 0.6, yc + 2.4 - k, z + 7.4), 0.3, 6))
    # the order that never went down: a dozen box, the bag on it, the ticket taped to the bag
    order = K.item('strand_order')
    ox = -1876.0
    K.mesh(order, 'box', K.mat('mat_h9_box.png'), obox((ox, yc, z), (12.0, 12.0, 3.6), yaw=-4.0, fit=True))
    K.mesh(order, 'bag', K.mat('mat_h9_bag.png'), obox((ox + 0.5, yc + 1.0, z + 3.6), (7.0, 4.4, 9.5), yaw=-4.0, fit=True))
    K.mesh(order, 'bag_fold', K.mat('mat_h9_bag.png'), obox((ox + 0.5, yc + 1.0, z + 13.1), (7.0, 1.4, 1.6), yaw=-4.0, fit=False, tile=6.0))
    K.mesh(order, 'ticket', K.mat('mat_h9_ticket_PLACEHOLDER.png'), obox((ox + 0.6, yc + 1.0 - 2.25, z + 4.4), (5.0, 0.08, 7.4), yaw=-4.0, faces='s', fit=True))
    # the counter bell
    it = K.item('counter_bell')
    K.mesh(it, 'base', M['black'], prism((-1866.0, yc - 7.0, z), 2.2, 0.6, 12))
    K.mesh(it, 'dome', M['chrome'], prism((-1866.0, yc - 7.0, z + 0.6), 1.9, 1.4, 12))
    K.mesh(it, 'plunger', M['chrome'], prism((-1866.0, yc - 7.0, z + 2.0), 0.3, 0.9, 6))
    # paper cups and saucers
    for k, x in enumerate((-1862.0, -1857.5)):
        K.prop('cup_stack', 'ma_cup_stack', (x, yc + 4.0, z), yaw=40.0 * k)
    for k, (x, n) in enumerate(((-1859.0, 7), (-1859.0, 0))):
        if n:
            it = K.item('saucer_stack')
            for j in range(n):
                K.mesh(it, 's%d' % j, M['white'], prism((x, yc - 5.0, z + j * 0.55), 3.0, 0.45, 14))
    K.prop('cup', 'cup_paper_open_iw6', (-1851.0, yc - 6.0, z), yaw=120.0)
    # the till (keys to her side)
    K.prop('till', 'park_cash_register', (-1832.0, yc + 2.0, z), yaw=90.0)
    # the gala trays: four steel trays stacked, the rings under film, a card with the Zero Line roundel and 047 propped against them
    for k in range(4):
        tray(K, 'gala_tray', -1802.0, yc - 9.0, z + 3.0 * k, 26.0, 18.0, glaze=('mat_h9_glaze_pink.png' if k == 3 else None),
             cols=5, rows=3, pitch=4.6, seed=10 + k, film=True)
    for k in range(3):                                                         # the rings of the lower trays seen through their rims
        K.mesh(K.item('gala_tray_rings'), 'rings', K.mat(('mat_h9_glaze_honey.png', 'mat_h9_glaze_pink.png', 'mat_h9_glaze_honey.png')[k]),
               rings((-1798.0, yc - 6.0, z + 3.0 * k + 0.4), 5, 3, 4.6, R=1.2, r=0.5, jitter=0.2, seed=20 + k))
    lab = K.item('gala_label')
    K.sign(lab, 'card', art_b('mat_cs_programme.png'), (-1789.0, yc - 9.0, z + 7.5), (0.0, -1.0, 0.0), (5.0, 7.5), rot=4.0, lift=0.25)
    # a warm lamp strip under the hatch head over the whole counter (an emissive picture, warmer than the pink room; not a light of the count)
    lamp = K.item('hatch_lamp')
    K.box(lamp, 'housing', [-1952.0, 4306.0, 135.0, -1770.0, 4316.0, 138.0], M['chrome'])
    K.sign(lamp, 'strip', art_b('h9_warm_strip.png'), (-1861.0, 4311.0, 135.0), (0.0, 0.0, -1.0), (176.0, 6.0),
           emissive={'color': [1.0, 0.72, 0.42], 'strength': 2.2}, lift=0.1)
    # her cards on the counter's front, eye level
    for k, (x, card) in enumerate(((-1928.0, 'h9_card_1.png'), (-1846.0, 'h9_card_3.png'))):
        K.sign(K.item('window_card'), 'card', art_b(card), (x, 4302.0, 31.0), (0.0, -1.0, 0.0), (13.0, 8.1), rot=(-3.0, 2.0)[k])
    # two hanging in the hatch on strings
    for k, (x, card) in enumerate(((-1940.0, 'h9_card_2.png'), (-1782.0, 'h9_card_4.png'))):
        it = K.item('hanging_card')
        K.sign(it, 'card', art_b(card), (x, 4309.0, 126.0), (0.0, -1.0, 0.0), (13.0, 8.1), lift=0.1)
        for j, dx in enumerate((-5.0, 5.0)):
            K.box(it, 'string%d' % j, [x + dx - 0.1, 4308.9, 130.0, x + dx + 0.1, 4309.1, 138.0], M['white'])


def display(K):
    """the glass rack on the display case: three tiers of rings (chocolate on the case, pink, honey), the urn and the pot on its end"""
    x0, x1, y0, y1, z = -1878.0, -1810.0, 4401.0, 4423.0, 38.0
    it = K.item('glass_rack')
    for k, (x, y) in enumerate(((x0, y0), (x1, y0), (x0, y1), (x1, y1))):
        K.mesh(it, 'post%d' % k, M['chrome'], prism((x, y, z), 0.5, 34.0, 6))
    for k, zz in enumerate((z + 11.0, z + 22.0, z + 33.0)):
        K.box(it, 'shelf%d' % k, [x0, y0, zz, x1, y1, zz + 0.4], M['glass'])
        K.box(it, 'lip%d' % k, [x0, y0 - 0.2, zz + 0.4, x1, y0 + 0.3, zz + 1.4], M['chrome'])
    K.box(it, 'front', [x0 + 0.6, y0 - 0.4, z, x1 - 0.6, y0 - 0.1, z + 33.0], M['glass'])
    for k, x in enumerate((x0, x1)):
        K.box(it, 'side%d' % k, [x - 0.15, y0, z, x + 0.15, y1, z + 33.0], M['glass'])
    # tier 0: chocolate rings (the stock ring) on two trays on the case; tier 1 pink; tier 2 honey; a few gone
    tray(K, 'ring_tray', x0 + 2.0, y0 + 1.5, z, 30.0, 19.0, glaze='choc', cols=6, rows=4, pitch=4.6, seed=1, skip=((5, 0), (5, 1), (4, 0)))
    tray(K, 'ring_tray', x0 + 34.0, y0 + 1.5, z, 30.0, 19.0, glaze='mat_h9_glaze_honey.png', cols=6, rows=4, pitch=4.6, seed=2, skip=((0, 0),))
    tray(K, 'ring_tray', x0 + 2.0, y0 + 1.5, z + 11.4, 30.0, 19.0, glaze='mat_h9_glaze_pink.png', cols=6, rows=4, pitch=4.6, seed=3)
    tray(K, 'ring_tray', x0 + 34.0, y0 + 1.5, z + 11.4, 30.0, 19.0, glaze='mat_h9_glaze_pink.png', cols=6, rows=4, pitch=4.6, seed=4, skip=((2, 0), (3, 0), (3, 1), (5, 3)))
    tray(K, 'ring_tray', x0 + 2.0, y0 + 1.5, z + 22.4, 30.0, 19.0, glaze='mat_h9_glaze_honey.png', cols=6, rows=4, pitch=4.6, seed=5, skip=((0, 3), (1, 3)))
    tray(K, 'ring_tray', x0 + 34.0, y0 + 1.5, z + 22.4, 30.0, 19.0, glaze='choc', cols=6, rows=3, pitch=5.2, seed=6, skip=((0, 0), (1, 0)))
    tray(K, 'ring_tray', x0 + 6.0, y0 + 2.0, z + 33.4, 26.0, 18.0, glaze='mat_h9_glaze_pink.png', cols=5, rows=3, pitch=4.6, seed=7)
    # the urn: a steel drum on three legs, a spigot to the front, lid and knob, two handles
    it = K.item('coffee_urn')
    ux, uy, z = -1813.0, 4318.0, 42.0                                          # round 2: on the serving counter, the hatch's foreground
    for k in range(3):
        a = math.radians(90 + 120 * k)
        K.mesh(it, 'leg%d' % k, M['black'], prism((ux + 4.0 * math.cos(a), uy + 4.0 * math.sin(a), z), 0.5, 2.2, 6))
    K.mesh(it, 'drum', M['chrome'], prism((ux, uy, z + 2.2), 5.4, 19.0, 18))
    K.mesh(it, 'band', M['black'], prism((ux, uy, z + 4.0), 5.55, 0.8, 18))
    K.mesh(it, 'lid', M['chrome'], prism((ux, uy, z + 21.2), 4.6, 1.4, 18))
    K.mesh(it, 'knob', M['black'], prism((ux, uy, z + 22.6), 1.0, 1.4, 8))
    K.mesh(it, 'gauge', M['glass'], prism((ux + 2.6, uy - 4.9, z + 6.0), 0.5, 11.0, 6))
    K.mesh(it, 'spigot', M['chrome'], G.cylinder((ux, uy - 5.2, z + 5.0), (ux, uy - 8.0, z + 5.0), 0.6, 8))
    K.mesh(it, 'tap', M['black'], obox((ux, uy - 7.6, z + 5.6), (0.7, 0.7, 2.0), fit=False))
    for k, dx in enumerate((-6.0, 6.0)):
        K.mesh(it, 'handle%d' % k, M['black'], obox((ux + dx, uy, z + 15.0), (1.2, 2.6, 1.0), fit=False))
    K.prop('coffee_pot', 'misc_coffee_machine_pot', (-1790.0, 4410.0, 38.0), yaw=200.0)
    K.prop('cup', 'p7_cup_coffee_mug', (-1800.0, 4416.0, 38.0), yaw=30.0)


def back_wall(K):
    """the menu and today boards on the partition (seen through the hatch: z 92 to 136), the television on its shelf on Channel 9;
    a frame-sized space left between the menu and the OPEN neon for the signed publicity photograph of a later lot"""
    it = K.item('menu_board')
    K.box(it, 'frame', [-1949.0, PART_Y - 0.8, 94.0, -1897.0, PART_Y, 134.6], M['black'])
    K.sign(it, 'face', art('menu_hole_nine.png'), (-1923.0, PART_Y - 0.8, 114.3), (0.0, -1.0, 0.0), (50.0, 36.7), lift=0.15)
    it = K.item('today_board')
    K.box(it, 'frame', [-1807.0, PART_Y - 0.8, 104.0, -1769.0, PART_Y, 132.0], M['black'])
    K.sign(it, 'face', art('today_hole_nine.png'), (-1788.0, PART_Y - 0.8, 118.0), (0.0, -1.0, 0.0), (36.0, 26.4), lift=0.15)
    K.prop('television', 'zmb_tv_crt_01', (-1694.75, PART_Y - 13.7, 119.0), yaw=0.0)
    K.sign(K.item('tv_picture'), 'screen', art_b('h9_tv_screen.png'), (-1696.0, PART_Y - 24.4, 130.0), (0.0, -1.0, 0.0), (19.0, 14.25), emissive=1.5, lift=0.1)


def ledge(K):
    """the inside counter: a plate left half eaten, a mug, sugar; at its east end the pink boxes, folded flat and stacked, two made up"""
    z = 40.0
    K.prop('plate', 'ng_plate_03', (-1902.0, 4466.0, z), yaw=10.0)
    K.mesh(K.item('ring_on_plate'), 'ring', K.mat('mat_h9_glaze_pink.png'), rings((-1901.0, 4466.5, z + 0.9), 1, 1, 4.4))
    K.prop('cup', 'p7_cup_coffee_mug', (-1891.0, 4470.0, z), yaw=200.0)
    it = K.item('sugar_pourer')
    K.mesh(it, 'jar', M['glass'], prism((-1883.0, 4471.0, z), 1.4, 4.6, 10))
    K.mesh(it, 'sugar', M['white'], prism((-1883.0, 4471.0, z + 0.1), 1.25, 1.6, 10))
    K.mesh(it, 'cap', M['chrome'], prism((-1883.0, 4471.0, z + 4.6), 1.5, 1.6, 10))
    K.prop('napkin_dispenser', 'p7_diner_table_napkin_clean', (-1873.0, 4472.0, z), yaw=0.0)
    it = K.item('boxes_flat')
    for j in range(14):
        K.mesh(it, 'flat%d' % j, K.mat('mat_h9_box.png'), obox((-1853.0 + (j % 3) * 0.3, 4468.0, z + 0.45 * j), (13.0, 13.0, 0.42), yaw=(j % 4) * 1.5, fit=True))
    for k in range(2):
        K.mesh(K.item('box_made_up'), 'box', K.mat('mat_h9_box.png'), obox((-1866.0 + 0.4 * k, 4466.5, z + 3.6 * k), (12.0, 12.0, 3.6), yaw=6.0 * k, fit=True))


def rail_rack(K):
    """trays on rails: a steel bakery rack against the east wall, six rails, trays of what did not sell; made-up boxes on its top"""
    x0, x1, y0, y1 = -1692.0, -1668.0, 4410.0, 4472.0
    it = K.item('rail_rack')
    for k, (x, y) in enumerate(((x0, y0), (x1, y0), (x0, y1), (x1, y1))):
        K.mesh(it, 'post%d' % k, M['chrome'], prism((x, y, 0.0), 0.6, 74.0, 6))
    for k in range(4):
        K.mesh(it, 'caster%d' % k, M['rubber'], prism(((x0, x1)[k % 2], (y0, y1)[k // 2], 0.0), 1.0, 1.0, 8))
    K.box(it, 'top', [x0, y0, 73.0, x1, y1, 74.0], M['alu'])
    K.clip(it, [x0 - 1.0, y0 - 1.0, 0.0, x1 + 1.0, PART_Y, 90.0])
    levels = (8.0, 20.0, 32.0, 44.0, 56.0, 68.0)
    fill = ('mat_h9_glaze_honey.png', None, 'choc', 'mat_h9_glaze_pink.png', 'mat_h9_glaze_honey.png', None)
    for k, zz in enumerate(levels):
        for s, y in enumerate((y0, y1)):
            K.box(it, 'rail%d_%d' % (k, s), [x0, y - 0.5, zz - 0.8, x1, y + 0.5, zz], M['alu'])
        if fill[k] is not None:
            tray(K, 'rack_tray', x0 + 1.0, y0 + 1.0, zz, x1 - x0 - 2.0, y1 - y0 - 2.0, glaze=fill[k], cols=5, rows=13, pitch=4.6, seed=30 + k,
                 skip=tuple((i, j) for i in range(5) for j in range(13) if (i * 7 + j * 3 + k) % 9 == 0))
        elif k == 1:
            tray(K, 'rack_tray', x0 + 1.0, y0 + 1.0, zz, x1 - x0 - 2.0, y1 - y0 - 2.0)
    for k in range(3):
        K.mesh(K.item('box_made_up'), 'box', K.mat('mat_h9_box.png'), obox((-1680.0, 4426.0 + 14.0 * k, 74.0 + (3.6 if k == 1 else 0.0)), (12.0, 12.0, 3.6), yaw=3.0 * k, fit=True))


def cameras(K):
    B.camera(K.m, 'hole_nine_counter_close', (-1860.0, 4246.0, 74.0), 90.0, pitch=14.0, layer=K.layer, id='hole_nine_counter_close')
    B.camera(K.m, 'hole_nine_far', (-1830.0, 3530.0, 62.0), 90.0, pitch=-3.0, layer=K.layer, id='hole_nine_far')       # 772 from the counter
    B.camera(K.m, 'hole_nine_interior', (-1730.0, 4338.0, 66.0), 140.0, pitch=4.0, layer=K.layer, id='hole_nine_interior')
    B.camera(K.m, 'hole_nine_back_wall', (-1840.0, 4250.0, 66.0), 90.0, pitch=-8.0, layer=K.layer, id='hole_nine_back_wall')


def add(m, anchors):
    K = Kit(m, SHOP)
    serving_counter(K)
    display(K)
    back_wall(K)
    ledge(K)
    rail_rack(K)
    cameras(K)
    return K
