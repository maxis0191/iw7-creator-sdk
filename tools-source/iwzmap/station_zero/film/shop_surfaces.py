r"""shop_surfaces: the shops' interior walls and floors as stock layered materials with painted wear, and bevelled trim courses (worker AC2, 28 Nov 2026).

REVIEW-3 scored the shop interiors worst (4.80 to 5.33: "flat white", "saturated flat magenta wall", "crude blocky brown mass"): the rooms were four plain
materials, one flat colour a wall. Here each front room's walls and floor are a stock `*` blend material (BLEND-LAYERS 6d: the layers draw, zero weight = the base)
with the wear painted in: the grime at the foot and at the ceiling line (layers of the material), a floor mask drawn from the room's plan (the path from the door to the
till, the damp along the walls, the corners). The shop's colour is an accent now (a painted band, the trim, a panel), not the wall.

Called by shop_ac2.build(). `A` is the arcade_shell module. Every mesh is render-only (the rooms keep their own collision and plain faces beneath, 0.5 behind).
"""
import os
import random

import hall_body as HB
import shellparts as P

ART = r'C:\studio-data\sz\film\station\ac2\art'
LAYER = 'shops_ac2'

# per shop: the wall blend (base + its dirt layer 1), the floor blend and the layer its wear is painted on, the trim table
SURF = {
    'needle_drop': dict(wall='*916n_149n', wall_size=128.0, floor='*712n_201n_89', floor_size=48.0, floor_layer=2,          # dark plaster with worn patches; black and white checker, water stain on B
                        north=4480.0, rail='band', rail_z=(122.0, 130.0), dado='dark', dado_h=36.0, skirt='dark'),
    'copy_stop': dict(wall='*1173n_106n', wall_size=64.0, floor='*678_91', floor_size=64.0, floor_layer=1,                  # white painted block, leak stain; grey lino
                      north=4480.0, rail='accent_blue', rail_z=(42.0, 47.0), dado=None, dado_h=0.0, skirt='dark'),
    'hole_nine': dict(wall='*1328n_149n', wall_size=128.0, floor='*763n_4', floor_size=64.0, floor_layer=1,                 # cream plaster, worn; slate tile
                      north=4480.0, rail='pink', rail_z=(96.0, 112.0), dado='wood', dado_h=44.0, skirt='dark'),
    'heel_key': dict(wall='*908n_149n', wall_size=64.0, floor='*1350n_89_659n', floor_size=96.0, floor_layer=1,             # warm limestone, worn plaster; wood boards with a water stain
                     north=4410.0, rail='red', rail_z=(100.0, 106.0), dado='wood', dado_h=40.0, skirt='dark'),
}
MAT = {'dark': 'w/fac_tile_black_01', 'band': 'w/ceramic_tile_01_orange', 'wood': 'w/wood_antique_panel_trim_01', 'pink': 'w/paint_pink_wall_semigloss',
       'red': 'w/plastic_wall_plain_red_01', 'accent_blue': 'w/plastic_wall_plain_blue_01', 'chrome': 'w/metal_chrome_trim_03', 'metal': 'w/metal_painted_02_dark'}
DOOR = {'needle_drop': (-2920.0, -2856.0), 'copy_stop': None, 'hole_nine': None, 'heel_key': None}     # the partition's door (x0 + 40, 64 wide); filled from A in build()


def floor_mask(A, nm, x0, y0, x1, y1, path, scale=0.5, door=None, goal=None):
    """grey = the weight of the floor's wear layer: the path from the door to the till (the trade's counter), the damp along the walls, the corners, a few leaks (seeded)"""
    from PIL import Image, ImageDraw, ImageFilter
    W, H = max(8, int((x1 - x0) * scale)), max(8, int((y1 - y0) * scale))
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    rng = random.Random(sum(ord(c) for c in nm))

    def px(x, y):
        return ((x - x0) * scale, (y1 - y) * scale)

    def blob(x, y, r, v, n=6):
        for _ in range(n):
            ox, oy = rng.uniform(-r, r) * 0.6, rng.uniform(-r, r) * 0.6
            rr = r * rng.uniform(0.45, 0.9)
            cx, cy = px(x + ox, y + oy)
            d.ellipse([cx - rr * scale, cy - rr * scale, cx + rr * scale, cy + rr * scale], fill=v)
    if door and goal:
        pts = [door, ((door[0] + goal[0]) / 2 + rng.uniform(-14, 14), (door[1] + goal[1]) / 2), goal]
        d.line([px(*p) for p in pts], fill=185, width=int(46 * scale), joint='curve')
        for p in pts:
            blob(p[0], p[1], 28.0, 185, 3)
    for k in range(10):                                                # the damp along the walls
        blob(rng.uniform(x0, x1), y1 - rng.uniform(0, 14), 20.0, rng.choice((90, 130, 170)), 2)
        blob(x0 + rng.uniform(0, 12), rng.uniform(y0, y1), 20.0, rng.choice((90, 130)), 2)
        blob(x1 - rng.uniform(0, 12), rng.uniform(y0, y1), 20.0, rng.choice((90, 130)), 2)
    for cx, cy in ((x0, y1), (x1, y1), (x0, y0), (x1, y0)):
        blob(cx, cy, 34.0, 200, 5)
    for k in range(2):                                                 # a leak or two under the ceiling
        blob(rng.uniform(x0 + 40, x1 - 40), rng.uniform(y0 + 30, y1 - 30), 26.0, 215, 5)
    im = im.filter(ImageFilter.GaussianBlur(3.0 * scale + 1.0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return path


def walls_and_floor(A, m, nm, goal):
    sp = SURF[nm]
    x0, x1 = A.UNITS[nm]
    xw, xe = x0 + 16.0, x1 - 16.0
    ys, yn = A.Y1 + 16.0, sp['north']
    top = A.UNIT_H - 1.0
    pdoor = DOOR.get(nm)
    west = P.wall_face('y', xw + 0.5, ys, yn, 0.0, top, +1)
    east = P.wall_face('y', xe - 0.5, ys, yn, 0.0, top, -1)
    north = P.wall_face('x', yn - 0.5, xw, xe, 0.0, top, -1, openings=[(pdoor[0], pdoor[1], 0.0, 96.0)] if pdoor else ())
    south = P.wall_face('x', ys + 0.5, xw, xe, A.OPEN_Z, top, +1)
    wall_paint = [{'type': 'foot', 'height': 8.0, 'falloff': 46.0, 'layer': 1},
                  {'type': 'gradient', 'axis': 'z', 'from': top - 60.0, 'to': top, 'w0': 0.0, 'w1': 150.0, 'steps': 3, 'layer': 1}]
    HB.put(m, sp['wall'], west + east + north + south, 'shop_%s_walls' % nm, layer=LAYER, size=sp['wall_size'], blend={'paint': wall_paint, 'z0': 0.0})
    mask = floor_mask(A, nm, xw, ys, xe, yn, os.path.join(ART, 'floor_%s.png' % nm), door=(xw + 60.0 if nm == 'needle_drop' else (xw + xe) / 2.0, ys + 10.0), goal=goal)
    fl = P.quad((xw, ys, 0.3), (xe, ys, 0.3), (xe, yn, 0.3), (xw, yn, 0.3))
    HB.put(m, sp['floor'], fl, 'shop_%s_floor' % nm, layer=LAYER, size=sp['floor_size'],
           blend={'paint': [{'type': 'mask', 'image': mask, 'rect': [xw, ys, xe, yn], 'axis': 'z', 'grid': 24.0, 'layer': sp['floor_layer']}], 'z0': 0.0})
    return 4


def trims(A, m, nm):
    """skirting, the dado (panel + cap rail), and the shop's accent stripe, as bevelled courses along the room's walls"""
    sp = SURF[nm]
    x0, x1 = A.UNITS[nm]
    xw, xe = x0 + 16.0, x1 - 16.0
    ys, yn = A.Y1 + 16.0, sp['north']
    pd = DOOR.get(nm)
    soup = P.Soup()
    runs = [((xw, yn), (xw, ys)),                       # west wall, south-going (the room on its left)
            ((xe, ys), (xe, yn))]                       # east wall
    north_segs = HB.spans(xw, xe, [(pd[0] - 4.0, pd[1] + 4.0)] if pd else ())
    runs += [((b, yn), (a, yn)) for a, b in north_segs]       # the partition, west-going (the room on its left)
    SKIRT = [(0.2, 0.0), (1.5, 0.0), (1.5, 6.5), (0.8, 7.5), (0.2, 7.5)]
    for a, b in runs:
        soup.add(MAT[sp['skirt']], P.strip(a, b, SKIRT))
        if sp['dado']:
            h = sp['dado_h']
            soup.add(MAT[sp['dado']], P.strip(a, b, [(0.2, 7.5), (1.9, 7.5), (1.9, h - 3.0), (0.2, h - 3.0)]))
            soup.add(MAT[sp['dado']], P.strip(a, b, [(0.2, h - 3.0), (2.5, h - 3.0), (3.0, h - 2.5), (3.0, h - 0.5), (2.5, h), (0.2, h)]))
            soup.add(A.MAT['dark'], P.strip(a, b, [(0.2, h - 3.4), (2.6, h - 3.4), (2.6, h - 3.0), (0.2, h - 3.0)]))          # a shadow line under the cap
        z0, z1 = sp['rail_z']
        soup.add(MAT[sp['rail']], P.strip(a, b, [(0.2, z0), (0.7, z0), (1.1, z0 + 0.4), (1.1, z1 - 0.4), (0.7, z1), (0.2, z1)]))
    n = HB.put_soup(m, soup, 'shop_trim_%s' % nm, layer=LAYER)
    return n, soup.count()


def build(A, m):
    """-> a report dict. A is the arcade_shell module"""
    m.add_layer(LAYER)
    pd = A.UNITS['needle_drop'][0] + 40.0
    DOOR['needle_drop'] = (pd, pd + 64.0)
    goals = {'needle_drop': (-2674.0, 4425.0), 'copy_stop': (-2150.0, 4380.0), 'hole_nine': (-1800.0, 4400.0), 'heel_key': (-1530.0, 4350.0)}
    rep = {'meshes': 0, 'trim_tris': 0}
    for nm in SURF:
        rep['meshes'] += walls_and_floor(A, m, nm, goals[nm])
        n, t = trims(A, m, nm)
        rep['meshes'] += n
        rep['trim_tris'] += t
    return rep
