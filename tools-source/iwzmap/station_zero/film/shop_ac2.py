r"""shop_ac2: the AC2 round of the Arcade (worker AC2, 28 Nov 2026): shop interiors and the foreground pieces from stock models, layered stock surfaces.

Called by arcade_doc.build() after the four goods modules (A is the arcade_shell module, m the Studio Map):
  shop_surfaces  the shops' walls and floors (stock blend materials, painted wear, trims)
  shop_fronts    the K1 4.2 pieces never placed: shutter housings, door leaves, pulls, OPEN neon, poster cases, awning
  shop_dress_*   per shop, stock models at stock density (shelving, counters, registers, product, back-of-house clutter, ceiling fixtures)
  hall_fixes     the foreground: the benches, the black panels, the wall-buy boards
Every model is static (no network record); touchable furniture carries a clip box. No light is added (L2 owns the lights).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

REPORT = {}


def build(A, m):
    import shop_surfaces
    REPORT['surfaces'] = shop_surfaces.build(A, m)
    import shop_dress
    import shop_fronts
    m.use(shop_dress.LAYER)
    REPORT['housings'] = shop_fronts.housing(A, m)
    shop_fronts.neon(A, m)
    shop_fronts.buy_boards(A, m)
    REPORT['dress'] = shop_dress.build(A, m)
    return REPORT
