r"""goods_heel_key: the goods of HEEL & KEY (Tomas Brill, shoes repaired and keys cut), unit U5, a stall seen across its counter (worker A3a).

As he left it at 23:30 on 31 Dec 1984 to watch the 23:47 pull out with the handle he engraved: shoes never collected, each pair with its
paper claim tag; the key carousel and the board of blanks on the counter, one hook of the board empty and tagged "0" (FILM-LAYER: the
first sight of the quest key); on the bench under the work lamp the key machine, the grinder and the plaster mould of the Dead-Man's
Handle (authored, simple: two plaster halves, one open on its cavity). The hall reads the stall through the slot between the counter
(z 42) and the shutter (z 75): the carousel, the board, two tagged pairs, the price board and the cards on the counter's face are there.
Contract: film/arcade_doc.py (layer `goods_heel_key`, ids `heel_key_*`). No light of its own: the shell's desk lamp is the work lamp.
The marksman buy on the pegboard (x about -1420) is left clear.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goods_kit_a as K  # noqa: E402
from studio import build as B  # noqa: E402
import shellgeo as G  # noqa: E402

KEY = 'cp_disco_subway_locker_key'
SHOES = 'p7_54i_gear_shoes'
BOOTS = 'boots_civ_miner_01_static'
TIN = 'p7_jar_glass_short'


def add(m, anchors):
    s = K.Shop(m, 'heel_key')
    counter(s, anchors)
    bench(s, anchors)
    pegboard(s, anchors)
    lasts_shelf(s, anchors)
    B.camera(m, 'heel_key_counter_close', (-1480.0, 4235.0, 62.0), 90.0, pitch=7.0, layer=s.layer, id='heel_key_P__cam_counter_close__1')


def tag(s, n, at):
    iid = s.item('P', 'claim_tag')
    s.pic(iid, 'face', 'hk_tag_%s.png' % n, at, 's', 'tag')


def last(s, origin, yaw):
    iid = s.item('T', 'shoe_last')
    s.mesh(iid, 'm', 'wood', K.place(K.last_shape(), origin, yaw))


# ------------------------------------------------------------------------------------------------ the counter (what the hall sees)
def counter(s, A):
    x0, y0, z0, x1, y1, z1 = A['heel_key.counter_top']['box']          # x -1624..-1336, y 4302..4330, top z 42
    # the key carousel at the west end, stock keys on its hooks
    iid = s.item('T', 'key_carousel')
    parts, hooks = K.carousel((-1606.0, 4317.0, z0), tiers=3, r=5.5, h=29.0)
    s.mesh(iid, 'frame', 'chrome', parts)
    for k, (hx, hy, hz, ang) in enumerate(hooks):
        if k % 4 == 3:
            continue
        s.prop(s.item('S', 'key_blank'), KEY, (hx, hy, hz), yaw=ang)
    # the board of key blanks on its stand, the empty hook tagged "0"
    iid = s.item('T', 'key_blank_board')
    s.box(iid, 'back', [-1590.0, 4326.0, z0 + 1.0, -1548.0, 4328.0, z0 + 28.0], 'wood')
    s.box(iid, 'foot', [-1588.0, 4324.0, z0, -1550.0, 4329.0, z0 + 1.0], 'wood')
    s.pic(iid, 'face', 'hk_key_board.png', (-1569.0, 4326.0, z0 + 14.5), 's', 'key_board')
    # the empty hook of row 3, column 8 of the picture (x 356 / 640, y 178 / 400): the tag hangs from it
    hx, hz = -1589.0 + 40.0 * 356.0 / 640.0, z0 + 14.5 + 12.5 - 25.0 * 178.0 / 400.0
    iid = s.item('P', 'zero_tag')
    s.pic(iid, 'face', 'hk_tag_zero.png', (hx, 4325.4, hz - 4.6), 's', 'tag')
    # two pairs waiting on the counter with their tickets
    s.prop(s.item('T', 'shoes_pair'), SHOES, (-1528.0, 4316.0, z0), yaw=0.0)
    tag(s, 6, (-1521.0, 4307.6, z0 + 4.4))
    s.prop(s.item('T', 'shoes_pair'), SHOES, (-1500.0, 4317.0, z0), yaw=0.0)
    tag(s, 5, (-1493.0, 4307.6, z0 + 4.4))
    s.prop(s.item('T', 'boots_pair'), BOOTS, (-1470.0, 4317.0, z0), yaw=0.0)
    tag(s, 3, (-1463.0, 4309.4, z0 + 6.0))
    # the price board on a stand (A1's picture)
    iid = s.item('F', 'price_board_stand')
    s.box(iid, 'back', [-1431.0, 4326.0, z0 + 1.0, -1399.0, 4328.0, z0 + 25.0], 'wood')
    s.box(iid, 'foot', [-1429.0, 4324.0, z0, -1401.0, 4329.0, z0 + 1.0], 'wood')
    iid = s.item('P', 'price_board')
    s.pic(iid, 'face', os.path.join(K.ART, 'board_heel_key.png'), (-1415.0, 4326.0, z0 + 13.0), 's', 'price_board')
    # polish tins and a can of dressing at the east end
    for k, (x, y) in enumerate(((-1374.0, 4312.0), (-1367.0, 4319.0), (-1361.0, 4310.0))):
        s.prop(s.item('T', 'polish_tin'), TIN, (x, y, z0), yaw=30.0 * k)
    s.prop(s.item('T', 'dressing_can'), 'cp_town_motor_oil', (-1350.0, 4318.0, z0), yaw=0.0)
    # the four cards on the counter's face
    for k, x in enumerate((-1600.0, -1550.0, -1500.0, -1450.0)):
        iid = s.item('P', 'card')
        s.pic(iid, 'face', 'hk_card_%d.png' % (k + 1), (x, y0 - 0.1, 22.0 + (k % 2) * 2.0), 's', 'card')


# ------------------------------------------------------------------------------------------------ the bench (under the work lamp)
def bench(s, A):
    x0, y0, z0, x1, y1, z1 = A['heel_key.bench']['box']               # x -1618..-1492, y 4360..4408, top z 36
    iid = s.item('T', 'key_machine')
    for mat, parts in K.key_machine((-1600.0, 4384.0, z0), 0.0).items():
        s.mesh(iid, mat, mat, parts)
    iid = s.item('T', 'bench_grinder')
    for mat, parts in K.grinder((-1568.0, 4398.0, z0), 0.0).items():
        s.mesh(iid, mat, mat, parts)
    iid = s.item('T', 'handle_mould')
    for mat, parts in K.mould((-1512.0, 4372.0, z0), 15.0).items():
        s.mesh(iid, mat, mat, parts)
    s.prop(s.item('T', 'hammer'), 'dns_tool_hammer01_iw6', (-1548.0, 4370.0, z0), yaw=80.0)
    s.prop(s.item('T', 'pincers'), 'dns_tool_pliers01_iw6', (-1586.0, 4366.0, z0), yaw=20.0)
    s.prop(s.item('T', 'nail_jar'), 'p7_tools_jar_glass_bolts', (-1500.0, 4401.0, z0), yaw=0.0)
    s.prop(s.item('T', 'glue_brush'), 'misc_paint_brush_01', (-1560.0, 4367.0, z0 + 0.4), yaw=120.0)
    s.prop(s.item('T', 'eyelet_setter'), 'equipment_industrial_rivet_tool_01', (-1503.0, 4388.0, z0 + 0.8), yaw=200.0)


# ------------------------------------------------------------------------------------------------ the pegboard over the bench
def pegboard(s, A):
    xa, xb, wy = -1614.0, -1496.0, 4409.0
    for r, z in enumerate((54.0, 76.0, 100.0)):
        xe = -1546.0 if r == 0 else xb                    # the lowest shelf stops short of the shell's desk lamp (x -1530, up to z 56)
        iid = s.item('F', 'peg_shelf')
        s.box(iid, 'board', [xa, wy - 16.0, z - 1.0, xe, wy, z], 'wood')
        for k, x in enumerate((xa + 8.0, xe - 8.0)):
            s.prop(s.item('F', 'shelf_bracket'), 'square_hook', (x, wy, z - 1.2), yaw=270.0)
    # the lower shelf: three pairs never collected, a claim tag hanging from each
    for k, (x, model, n) in enumerate(((-1604.0, SHOES, 1), (-1583.0, BOOTS, 2), (-1559.0, SHOES, 4))):
        s.prop(s.item('T', 'shoes_pair' if model == SHOES else 'boots_pair'), model, (x, wy - 8.5, 54.0), yaw=0.0)
        tag(s, n, (x + 4.0, wy - 16.4, 54.0 - 5.0))
    # the middle shelf: a row of lasts, toes to the hall
    for k, x in enumerate((-1606.0, -1590.0, -1574.0, -1558.0, -1542.0, -1526.0)):
        last(s, (x, wy - 8.0, 76.0), 270.0 + (k % 2) * 6.0)
    # the top shelf: the drawers of heel tips (one pulled out) and the toolbox
    iid = s.item('T', 'heel_tip_drawers')
    bx0, bx1, by0, bz0 = -1604.0, -1572.0, wy - 13.0, 100.0
    s.box(iid, 'body', [bx0, by0, bz0, bx1, wy, bz0 + 16.0], 'grey')
    for r in range(2):
        for c in range(4):
            dx0 = bx0 + 1.0 + c * 7.5
            pulled = (r, c) == (1, 2)
            dy = -5.0 if pulled else 0.0
            s.box(iid, 'drawer_%d_%d' % (r, c), [dx0, by0 - 0.6 + dy, bz0 + 1.0 + r * 7.5, dx0 + 7.0, by0 + (5.0 if pulled else 0.0) + dy, bz0 + 7.5 + r * 7.5], 'red')
            s.box(iid, 'label_%d_%d' % (r, c), [dx0 + 2.0, by0 - 0.8 + dy, bz0 + 5.0 + r * 7.5, dx0 + 5.0, by0 - 0.6 + dy, bz0 + 6.5 + r * 7.5], 'chrome')
    for k in range(5):                                       # the heel tips in the pulled drawer
        tx = bx0 + 1.0 + 2 * 7.5 + 1.0 + (k % 3) * 1.9
        ty = by0 - 4.6 + (k // 3) * 2.2
        s.box(s.item('S', 'heel_tip'), 'tip', [tx, ty, bz0 + 9.0, tx + 1.6, ty + 1.8, bz0 + 9.7], 'rubber')
    s.prop(s.item('T', 'toolbox'), 'toolbox_small01_iw6', (-1540.0, wy - 7.0, 100.0), yaw=90.0)
    # laces for sale and a few blanks on hooks, on the pegboard between the bench and the rifle
    iid = s.item('S', 'laces_card')
    s.pic(iid, 'face', 'hk_laces_card.png', (-1482.0, wy, 62.0), 's', 'laces')
    for r, z in enumerate((80.0, 90.0)):
        s.prop(s.item('F', 'peg_hook'), 'cp_rave_tiki_key_hook_01', (-1482.0, wy, z), yaw=270.0)
        for k in range(3):
            s.prop(s.item('S', 'key_blank'), KEY, (-1482.0, wy - 1.2 - k * 1.1, z - 0.3), yaw=270.0)


# ------------------------------------------------------------------------------------------------ the lasts shelf (east, open to the west)
def lasts_shelf(s, A):
    x0, y0, z0, x1, y1, z1 = A['heel_key.lasts_shelf']['box']          # x -1390..-1342, y 4350..4408; boards at 6, 28.5, 51, 73.5, top 94.5
    for zb in (51.0, 73.5, 94.5):
        for k, y in enumerate((4360.0, 4376.0, 4392.0)):
            last(s, (-1368.0, y, zb), 180.0 + (k - 1) * 5.0)
    for k, y in enumerate((4358.0, 4368.0, 4378.0, 4390.0)):
        s.prop(s.item('T', 'polish_tin'), TIN, (-1372.0 + (k % 2) * 6.0, y, 28.5), yaw=25.0 * k)
    s.prop(s.item('T', 'dressing_can'), 'cp_town_motor_oil', (-1360.0, 4400.0, 28.5), yaw=0.0)
