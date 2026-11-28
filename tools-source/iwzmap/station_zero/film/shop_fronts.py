r"""shop_fronts: the K1 4.2 pieces of the shopfronts and the hall's foreground, from stock models (worker AC2, 28 Nov 2026).

  housing   the roll-shutter housing of each opening: `roll_up_door_top_02` (262 long, scaled to the opening; Copy Stop's 618 take two)
  pull      the stock door handle `cnd_handle_door_u` on each face of a door leaf
  neon      the OPEN sign `neon_open_sign_on_02` in Needle Drop's window (emissive, no light: L2 owns the lights)
  benches   `cp_disco_bus_bench` (a slatted bench with cast ends) in place of the 192-long worn slab
  buy_board the pegboard display `bike_shop_board_display_02` behind the two wall-buy outlines (the engine draws the outline; it read as cyan on a blank board)
Every model is static. A is the arcade_shell module.
"""
import shop_dress as D
from studio import build as B

HOUSING = 'roll_up_door_top_02'
PULL = 'cnd_handle_door_u'


def housing(A, m):
    n = 0
    for nm, (x0, x1) in A.UNITS.items():
        a0, a1 = x0 + 16.0, x1 - 16.0
        pieces = 2 if (a1 - a0) > 400.0 else 1
        w = (a1 - a0) / pieces
        s = w / 262.0
        for k in range(pieces):
            cx = a0 + w * (k + 0.5)
            D.put(m, HOUSING, cx, A.Y1 + 14.0 + 23.0 * s, A.HOUSING[1] - 33.0 * s + 0.5, yaw=270.0, scale=round(s, 4), id='housing_%s_%d' % (nm, k))
            n += 1
    return n


def pull(m, tag, x, y):
    """a door handle on each face of the leaf standing along y at x (stiles 3 thick)"""
    B.prop(m, PULL, (round(x + 1.5 + 2.885, 2), round(y + 2.1, 2), 62.0), yaw=0.0, layer='fronts', id='%s_pull_e' % tag)
    B.prop(m, PULL, (round(x - 1.5 - 2.885, 2), round(y - 2.1, 2), 62.0), yaw=180.0, layer='fronts', id='%s_pull_w' % tag)


def neon(A, m):
    D.put(m, 'neon_open_sign_on_02', -2740.0, 4313.0, 88.0, yaw=270.0, scale=0.9, id='nd_open_neon', emissive={'color': [1.0, 0.32, 0.2], 'strength': 1.6})


def island_bench(A, m, x, y, id):
    for k, dx in enumerate((-38.0, 38.0)):
        D.put(m, 'cp_disco_bus_bench', x + dx, y, 0.0, yaw=90.0, id='%s_%d' % (id, k), clip='auto', layer='hall')


def wall_bench(A, m, x, id):
    for k, dx in enumerate((-38.0, 38.0)):
        D.put(m, 'cp_disco_bus_bench', x + dx, A.YS + 14.5, 0.0, yaw=270.0, id='%s_%d' % (id, k), clip='auto', layer='south')


def buy_boards(A, m):
    D.put(m, 'bike_shop_board_display_02', -1490.0, 4300.4, 52.0, yaw=270.0, id='hk_buy_board')
    x0, _ = A.UNITS['hole_nine']
    D.put(m, 'bike_shop_board_display_02', x0 + 16.0 + 1.3, 4440.0, 40.0, yaw=0.0, id='h9_buy_board')
