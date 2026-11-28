r"""hall_body: the Arcade hall's body as authored meshes (worker AC1, 28 Nov 2026; K1-CONSTRUCTION sections 4.1 and 5).

Replaces arcade_shell's tile_courses / columns / ceiling and the flat floor, the flat floor borders and the plain wall faces:
  - the floor: a stock layered floor (blend material) with painted wear (a mask drawn from the plan: the walking paths, the feet of the columns, the leaks
    under the ceiling's holes, the thresholds); the floor object itself is collision only;
  - the three walls: a stock layered tile face with grime painted at the foot, skirting / band / cap-rail courses with bevels, damaged-tile patches where the
    benches and lockers stood, a kerb along the floor;
  - the colonnade: six columns to the stock column's profile, girders at underside z 161 (+ three cross girders to the south wall);
  - the suspended ceiling: one mesh of recessed panels in 48 modules, T-bars, the live / dead / missing / stained panels of arcade_shell's lists.
Every mesh is render-only; collision stays with the clip boxes and the existing wall and slab objects.
"""
import math
import os
import random

from studio import build as B

import shellparts as P

ART = r'C:\studio-data\sz\film\station\ac2\art'
WALL_FIELD = '*824n_4'                  # dt_tile_ceramic_white + stain_leak_rust_01_dec_mult (cp_disco, stride 8)
FLOOR = '*861n_280n_91'                 # stone_spanish_tile_01 + metal_painted_yellow_01_rvl + asphalt_flooring_stain_01 (cp_disco, stride 20)
GIRDER = '*1040_4'                      # metal_painted_02_dark + stain_leak_rust_01_dec_mult (cp_disco, stride 8)
MSIZE = {'w/dt_tile_ceramic_white': 64.0, 'w/dt_tile_ceramic_white_dmg': 64.0, 'w/fac_tile_black_01': 32.0, 'w/ceiling_tile_01': 96.0, '*824n_4': 64.0,
         'w/ceramic_tile_01_orange': 64.0, FLOOR: 64.0}


# ------------------------------------------------------------------------------------------------ texture coordinates
def planar_uvs(tris, size):
    """world-planar coordinates in repeats of `size` units: the dominant axis of the triangle's normal picks the plane"""
    out = []
    for t in tris:
        ux, uy, uz = (t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2])
        vx, vy, vz = (t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2])
        n = (abs(uy * vz - uz * vy), abs(uz * vx - ux * vz), abs(ux * vy - uy * vx))
        k = n.index(max(n))
        ax = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[k]
        out.append([[p[ax[0]] / size, p[ax[1]] / size] for p in t])
    return out


def put(m, mat, tris, id, layer='shell', blend=None, size=None, mode='render'):
    """one mesh object of a material (a `*` material takes the blend spec), with planar coordinates"""
    if not tris:
        return
    if blend:                       # a layered surface carries its own coordinates (the exporter's table has no size for a `*` material)
        B.mesh(m, None, tris=tris, uvs=planar_uvs(tris, size or MSIZE.get(mat, 128.0)), mode=mode, layer=layer, id=id, blend=dict(blend, material=mat))
    else:                           # a plain material: the exporter projects by its own table of sizes
        B.mesh(m, mat, tris=tris, mode=mode, layer=layer, id=id)


def put_soup(m, soup, prefix, layer='shell', cap=30000):
    n = 0
    for mat, tris in sorted(soup.t.items()):
        tag = mat.replace('w/', '').replace('*', 's')[:28]
        for k in range(0, len(tris), cap):
            put(m, mat, tris[k:k + cap], '%s_%s%s' % (prefix, tag, '' if k == 0 else '_%d' % (k // cap)), layer)
            n += 1
    return n


def spans(a0, a1, skips=()):
    out = [(a0, a1)]
    for s0, s1 in skips:
        out = [q for p in out for q in ((p[0], min(p[1], s0)), (max(p[0], s1), p[1])) if q[1] - q[0] > 1.0]
    return out


# ------------------------------------------------------------------------------------------------ the floor wear mask (a plan, north up)
def floor_mask(A, path, scale=0.5):
    """gray = the weight of the floor's dirt layer: the path from D4 along the lane to each shop door, the feet of the columns, the damp foot of the south wall,
    the leaks under the stained and missing ceiling panels, the doors' thresholds. Deterministic (seeded)"""
    from PIL import Image, ImageDraw, ImageFilter
    W, H = int((A.XE - A.XW) * scale), int((A.Y1 - A.YS) * scale)
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    rng = random.Random(1978)

    def px(x, y):
        return ((x - A.XW) * scale, (A.Y1 - y) * scale)

    def blob(x, y, r, v, n=7):
        for _ in range(n):
            ox, oy = rng.uniform(-r, r) * 0.6, rng.uniform(-r, r) * 0.6
            rr = r * rng.uniform(0.45, 0.9)
            cx, cy = px(x + ox, y + oy)
            d.ellipse([cx - rr * scale, cy - rr * scale, cx + rr * scale, cy + rr * scale], fill=v)

    def stroke(pts, w, v):
        q = [px(*p) for p in pts]
        d.line(q, fill=v, width=int(w * scale), joint='curve')
        for p in pts:
            blob(p[0], p[1], w * 0.55, v, 3)
    # the walking paths: D4 -> the lane in front of the shops -> each door
    lane_y = 4120.0
    stroke([(A.XE, 3900.0), (-1330.0, 3960.0), (-1500.0, 4060.0), (-1700.0, lane_y), (-2100.0, lane_y + 6), (-2500.0, lane_y - 4), (-2900.0, lane_y + 8)], 78.0, 150)
    for x0, x1 in A.UNITS.values():
        cx = (x0 + x1) / 2.0
        stroke([(cx, lane_y), (cx + rng.uniform(-30, 30), 4210.0), (cx, A.BULK_Y + 8.0)], 64.0, 175)
    blob(-1800.0, 4180.0, 60.0, 140, 8)
    # the thresholds: where the doors are, a worn band across the sill
    for x0, x1 in A.UNITS.values():
        stroke([(x0 + 30.0, 4258.0), (x1 - 30.0, 4258.0)], 30.0, 200)
    # the feet of the columns, a grey ring (a hand-wiped halo is the polisher's inheritance)
    for x in A.COLS:
        blob(x, A.COL_Y, 40.0, 120, 8)
    # the south wall's damp foot and its benches
    for x in range(int(A.XW) + 40, int(A.XE) - 40, 90):
        blob(float(x), A.YS + 16.0, 40.0, rng.choice((70, 110, 150)), 3)
    # the leaks: under the panels that fell, under the stained ones
    for k, (i, j) in enumerate(A.HOLES + A.STAINS[:3]):
        x0, y0, x1, y1 = A.module(i, j)
        blob((x0 + x1) / 2.0, (y0 + y1) / 2.0, 36.0, 235, 6)
    im = im.filter(ImageFilter.GaussianBlur(4.0 * scale + 1.0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return path


# ------------------------------------------------------------------------------------------------ build
def build(A, m):
    """the hall's body. A is the arcade_shell module"""
    m.use('arcade_door')
    B.doorway(m, [A.X1 - 4.0, A.DOOR_Y0, 0.0, A.X1 + 4.0, A.DOOR_Y1, A.DOOR_Z], A.MAT['tile'], id='arcade_doorway')
    B.replace(m, box=[-1170, 3900, -1, -1106, 4100, 100], what=['props'], id='clear_bench_props')           # FE24: the base bench in D4
    B.replace(m, box=[-1170, 3900, 2, -1106, 4100, 100], what=['collision'], clip=True, id='clear_bench_clip')
    m.use('shell')
    X0, X1, Y0, Y1, YS, XW, XE, H, G = A.X0, A.X1, A.Y0, A.Y1, A.YS, A.XW, A.XE, A.H, A.GRID_Z
    # the solid bodies: collision only for the floor, the walls keep their own faces (their openings and reveals), the overlays below are 0.5 proud
    B.floor(m, [X0, Y0, X1, Y1], 0.0, A.MAT['floor'], mode='collision', id='hall_floor')
    B.ceiling(m, [X0, Y0, X1, Y1], H, A.MAT['slab'], id='hall_slab')
    B.wall(m, [X0, Y0, 0.0, X1, YS, H], A.MAT['tile'], axis='x', id='wall_south')
    B.wall(m, [X0, YS, 0.0, XW, Y1, H], A.MAT['tile'], axis='y', openings=[(3852.0, 3948.0, 0.0, 112.0)], id='wall_west')
    B.wall(m, [XE, YS, 0.0, X1, Y1, H], A.MAT['tile'], axis='y', openings=[(A.DOOR_Y0, A.DOOR_Y1, 0.0, A.DOOR_Z)], id='wall_east')
    A.bx(m, 'fill_west_end', [X0, Y1, 0.0, A.UNITS['needle_drop'][0], A.YB, H], A.MAT['tile'])
    for a, b in (('needle_drop', 'copy_stop'), ('copy_stop', 'hole_nine'), ('hole_nine', 'heel_key')):
        A.bx(m, 'fill_%s_%s' % (a, b), [A.UNITS[a][1], Y1, 0.0, A.UNITS[b][0], A.YB, H], A.MAT['tile'])
    A.bx(m, 'bulkhead', [XW, A.BULK_Y, A.BULK_Z, XE, Y1, H], A.MAT['dark'])
    rep = A.REPORT.setdefault('body', {})
    n_mesh = 0
    # ---- the floor: layered stock tile, wear painted from the mask
    mask = floor_mask(A, os.path.join(ART, 'floor_wear.png'))
    fl = P.quad((XW, YS, 0.0), (XE, YS, 0.0), (XE, Y1, 0.0), (XW, Y1, 0.0))
    put(m, FLOOR, fl, 'hall_floor_render', blend={'paint': [{'type': 'mask', 'image': mask, 'rect': [XW, YS, XE, Y1], 'axis': 'z', 'grid': 24.0, 'layer': 2}], 'z0': 0.0})
    n_mesh += 1
    # AC2: the floor does not read as one repeat: a second stock layered tile (slate) laid as the doors' inlays and the patches where the floor was relaid, over the quarry-type field
    inlay = []
    for x0_, x1_ in A.UNITS.values():
        cx_ = (x0_ + x1_) / 2.0
        inlay += P.quad((cx_ - 64.0, 4176.0, 0.25), (cx_ + 64.0, 4176.0, 0.25), (cx_ + 64.0, 4236.0, 0.25), (cx_ - 64.0, 4236.0, 0.25))
    for x_, y_, w_, d_ in ((-2400.0, 4090.0, 96.0, 64.0), (-1900.0, 4010.0, 128.0, 48.0), (-2650.0, 3930.0, 64.0, 96.0), (-1500.0, 3900.0, 96.0, 96.0), (-2150.0, 3820.0, 80.0, 48.0),
                           (-2860.0, 4100.0, 72.0, 56.0), (-1760.0, 4110.0, 64.0, 64.0)):
        inlay += P.quad((x_, y_, 0.25), (x_ + w_, y_, 0.25), (x_ + w_, y_ + d_, 0.25), (x_, y_ + d_, 0.25))
    put(m, '*763n_4', inlay, 'hall_floor_inlay', blend={'paint': [], 'z0': 0.0}, size=64.0)
    n_mesh += 1
    # ---- the walls: layered tile face with the foot's grime, 0.5 proud
    south = P.wall_face('x', YS + 0.5, XW, XE, 0.0, G, +1)
    west = P.wall_face('y', XW + 0.5, YS, A.BULK_Y, 0.0, G, +1, openings=[(3852.0, 3948.0, 0.0, 112.0)])
    east = P.wall_face('y', XE - 0.5, YS, A.BULK_Y, 0.0, G, -1, openings=[(A.DOOR_Y0, A.DOOR_Y1, 0.0, A.DOOR_Z)])
    put(m, WALL_FIELD, south + west + east, 'hall_walls_render', blend={'paint': [{'type': 'foot', 'height': 10.0, 'falloff': 52.0, 'layer': 1}], 'z0': 0.0})
    n_mesh += 1
    # ---- the courses and the kerb (stock plain tile, bevelled)
    soup = P.Soup()
    west_skip, east_skip = [(3852.0 - 16.0, 3948.0 + 16.0)], [(A.DOOR_Y0 - 14.0, A.DOOR_Y1 + 14.0)]
    runs = [('s', [((XW, YS), (XE, YS))]),
            ('w', [((XW, b), (XW, a)) for a, b in spans(YS, A.BULK_Y, west_skip)]),
            ('e', [((XE, a), (XE, b)) for a, b in spans(YS, A.BULK_Y, east_skip)])]
    SKIRT = [(0.2, 0.0), (1.5, 0.0), (1.5, 8.5), (0.7, 10.0), (0.2, 10.0)]
    BAND = [(0.2, 58.0), (0.6, 58.0), (1.1, 58.5), (1.1, 73.5), (0.6, 74.0), (0.2, 74.0)]
    CAP = [(0.2, 220.0), (0.7, 220.0), (1.2, 220.5), (1.2, 227.5), (0.7, 228.0), (0.2, 228.0)]
    KERB = [(0.0, 0.0), (18.0, 0.0), (18.0, 1.2), (17.0, 2.2), (0.0, 2.2)]
    for wall, segs in runs:
        sh = -0.5 if wall == 'e' else 0.0
        for a, b in segs:
            # the profile's d is measured from the wall plane; the face overlays sit 0.5 in front of it, so the courses start at 0.2 and stand 1.1 at most
            soup.add(A.MAT['dark'], P.strip(a, b, SKIRT))
            soup.add(A.MAT['band'], P.strip(a, b, BAND))
            soup.add(A.MAT['band'], P.strip(a, b, CAP))
            soup.add(A.MAT['dark'], P.strip(a, b, KERB))
    # the shop line: the dark band under the bulkhead and a brass strip
    soup.add(A.MAT['dark'], P.strip((XW + 18.0, Y1 - 24.0), (XE - 18.0, Y1 - 24.0), [(0.0, 0.0), (24.0, 0.0), (24.0, 0.8), (22.8, 1.2), (0.0, 1.2)]))
    soup.add(A.MAT['chrome'], P.strip((XW + 18.0, Y1 - 31.0), (XE - 18.0, Y1 - 31.0), [(0.0, 0.0), (5.0, 0.0), (5.0, 0.7), (4.4, 0.95), (0.6, 0.95), (0.0, 0.7)]))
    # the bulkhead's face: a chamfered dark lip and an orange band under it
    soup.add(A.MAT['dark'], P.strip((XE, A.BULK_Y - 0.4), (XW, A.BULK_Y - 0.4), [(0.0, A.BULK_Z), (1.6, A.BULK_Z), (1.6, A.BULK_Z + 4.0), (0.0, A.BULK_Z + 4.0)], skip_caps=True))
    soup.add(A.MAT['band'], P.strip((XW, A.BULK_Y), (XE, A.BULK_Y), [(-1.0, A.BULK_Z + 4.0), (-1.0, A.BULK_Z + 10.0), (-0.2, A.BULK_Z + 10.0), (-0.2, A.BULK_Z + 4.0)], skip_caps=True))
    # the damaged tile where the benches and the lockers rubbed the wall: a rhythm along the south wall, not a scatter
    nd = 0
    for x, z0, w, h in ((-2735.0, 14.0, 44.0, 40.0), (-2640.0, 74.0, 40.0, 26.0), (-2530.0, 40.0, 24.0, 56.0), (-2470.0, 14.0, 52.0, 36.0), (-2250.0, 96.0, 36.0, 60.0),
                        (-2020.0, 20.0, 60.0, 30.0), (-1790.0, 78.0, 28.0, 48.0), (-1650.0, 14.0, 40.0, 70.0), (-1470.0, 36.0, 50.0, 40.0)):
        soup.add(A.MAT['tile_dmg'], P.strip((x - w / 2.0, YS), (x + w / 2.0, YS), [(0.2, z0), (0.9, z0 + 0.5), (0.9, z0 + h - 0.5), (0.2, z0 + h)]))
        nd += 1
    for y, z0, w, h in ((4000.0, 40.0, 50.0, 60.0), (3800.0, 120.0, 40.0, 50.0)):
        soup.add(A.MAT['tile_dmg'], P.strip((XW, y + w / 2.0), (XW, y - w / 2.0), [(0.2, z0), (0.9, z0 + 0.5), (0.9, z0 + h - 0.5), (0.2, z0 + h)]))
        nd += 1
    rep['damaged_patches'] = nd
    n_mesh += put_soup(m, soup, 'courses')
    # ---- the colonnade
    soup = P.Soup()
    cols = {role: [] for role in ('base', 'shaft', 'band', 'upper', 'upper_dmg', 'collar', 'cap')}
    for k, x in enumerate(A.COLS):
        parts = P.column_parts(x, A.COL_Y)
        for role, tris in parts.items():
            cols['upper_dmg' if role == 'upper' and k in (1, 3, 4) else role] += tris
        A.B.clip(m, [x - 17.0, A.COL_Y - 17.0, 0.0, x + 17.0, A.COL_Y + 17.0, G], layer='shell', id='col_%d_clip' % k)
    put(m, A.MAT['dark'], cols['base'], 'col_base', size=32.0)
    put(m, WALL_FIELD, cols['shaft'], 'col_shaft', blend={'paint': [{'type': 'foot', 'height': 10.0, 'falloff': 44.0, 'layer': 1}], 'z0': 12.0})
    put(m, A.MAT['band'], cols['band'], 'col_band')
    put(m, A.MAT['tile'], cols['upper'], 'col_upper')
    put(m, A.MAT['tile_dmg'], cols['upper_dmg'], 'col_upper_dmg')
    put(m, A.MAT['dark'], cols['collar'], 'col_collar', size=32.0)
    put(m, 'w/brick_wall_14_white_painted', cols['cap'], 'col_cap', size=128.0)
    n_mesh += 7
    # girders: five spans along the colonnade and three cross girders to the south wall; underside z 161, top z 240
    gs = P.Soup()
    gz0, gz1 = 161.0, 240.0
    for a, b in zip(A.COLS, A.COLS[1:]):
        p = P.ibeam((a + 16.0, A.COL_Y), (b - 16.0, A.COL_Y), gz0, gz1)
        gs.add(A.MAT['girder'], p['flange'])
        gs.add(A.MAT['girder'], p['web'])
        for xe in (a + 16.0, b - 16.0):                              # end plates 3 thick with four bolt heads each
            gs.add(A.MAT['girder_trim'], P.box(xe - 1.5, A.COL_Y - 15.0, gz0, xe + 1.5, A.COL_Y + 15.0, gz1))
    for k in (0, 2, 4):
        x = A.COLS[k]
        p = P.ibeam((x, YS + 0.6), (x, A.COL_Y - 16.0), gz0, gz1)
        gs.add(A.MAT['girder'], p['flange'])
        gs.add(A.MAT['girder'], p['web'])
    girder_tris = gs.t.pop(A.MAT['girder'])
    put(m, GIRDER, girder_tris, 'girder_blend', blend={'paint': [{'type': 'foot', 'height': 14.0, 'falloff': 46.0, 'layer': 1}], 'z0': gz0})   # rust at the underside
    n_mesh += 1 + put_soup(m, gs, 'girder')
    rep['girders'] = len(A.COLS) - 1 + 3
    # ---- the suspended ceiling
    n_mesh += ceiling(A, m)
    rep['authored_meshes'] = n_mesh
    rep['floor_mask'] = mask


def _flip(tris):
    return [[t[0], t[2], t[1]] for t in tris]


def _cavity(x0, y0, x1, y1, z0, z1, part):
    """the inside of a box open below, normals into the hole: its four reveals ('sides') or its top ('top')"""
    b = P.box(x0, y0, z0, x1, y1, z1)
    top = [t for t in b if all(abs(q[2] - z1) < 1e-6 for q in t)]
    bot = [t for t in b if all(abs(q[2] - z0) < 1e-6 for q in t)]
    sides = [t for t in b if t not in top and t not in bot]
    return _flip(top if part == 'top' else sides)


def _hanging_tile(x0, y0, x1, y1, z, deg, edge):
    """the missing panel's tile hanging from one edge of its hole (a 1.2 thick slab turned `deg` degrees about that edge)"""
    t = P.bevel_box(x0 + 0.4, y0 + 0.4, z - 1.2, x1 - 0.4, y1 - 0.4, z, c=0.5, top=0.3)
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for tri in t:
        q = []
        for (x, y, zz) in tri:
            if edge == 0:                    # hinged on the west edge: swings about the y axis
                dx, dz = x - x0, zz - z
                q.append((x0 + dx * ca + dz * sa, y, z - dx * sa + dz * ca))
            elif edge == 1:                  # east edge
                dx, dz = x1 - x, zz - z
                q.append((x1 - (dx * ca + dz * sa), y, z - dx * sa + dz * ca))
            elif edge == 2:                  # south edge
                dy, dz = y - y0, zz - z
                q.append((x, y0 + dy * ca + dz * sa, z - dy * sa + dz * ca))
            else:                            # north edge
                dy, dz = y1 - y, zz - z
                q.append((x, y1 - (dy * ca + dz * sa), z - dy * sa + dz * ca))
        out.append(q)
    return out


def ceiling(A, m):
    m.use('ceiling')
    G = A.GRID_Z
    n = 0
    live = set(A.LIVE)
    dead = set(A.DEAD)
    holes = set(A.HOLES)
    stains = set(A.STAINS)
    soup = P.Soup()
    for j in range(A.NJ):
        for i in range(A.NI):
            x0, y0, x1, y1 = A.module(i, j)
            if x1 - x0 < 2.0 or y1 - y0 < 2.0:
                continue
            ix0, iy0, ix1, iy1 = x0 + 0.8, y0 + 0.8, x1 - 0.8, y1 - 0.8
            # a recessed panel: a 3-unit bevel from the T-bar's level up 0.9 to the flat; seen from below (normals down)
            r = min(3.0, (ix1 - ix0) / 2.0 - 0.1, (iy1 - iy0) / 2.0 - 0.1)
            zo, zi = G - 0.3, G + 0.6
            outer = [(ix0, iy0, zo), (ix1, iy0, zo), (ix1, iy1, zo), (ix0, iy1, zo)]
            inner = [(ix0 + r, iy0 + r, zi), (ix1 - r, iy0 + r, zi), (ix1 - r, iy1 - r, zi), (ix0 + r, iy1 - r, zi)]
            t = []
            for k in range(4):
                k2 = (k + 1) % 4
                t += [[outer[k], outer[k2], inner[k2]], [outer[k], inner[k2], inner[k]]]
            t += [[inner[0], inner[1], inner[2]], [inner[0], inner[2], inner[3]]]
            t = P._outward(t, ((ix0 + ix1) / 2.0, (iy0 + iy1) / 2.0, G + 40.0))           # the solid lies above: normals face down
            key = (i, j)
            if key in holes:                    # AC2: a missing panel is a hole into the plenum (concrete soffit 11 above the grid, dark reveals) with the tile hanging from one edge, not a black cutout
                soup.add(A.MAT['girder'], _cavity(ix0, iy0, ix1, iy1, G - 0.3, G + 11.0, 'sides'))
                soup.add(A.MAT['hole'], _cavity(ix0, iy0, ix1, iy1, G - 0.3, G + 11.0, 'top'))
                soup.add(A.MAT['ceil'], _hanging_tile(ix0, iy0, ix1, iy1, G - 0.3, 38.0 + 9.0 * ((i + j) % 3), (i + 2 * j) % 4))
                continue
            mat = A.MAT['panel_on'] if key in live else A.MAT['panel_off'] if key in dead else A.MAT['hole'] if key in holes else A.MAT['ceil_stain'] if key in stains else A.MAT['ceil']
            soup.add(mat, t)
    # T-bars: an inverted T, a 3-wide flange 0.5 below the panels
    tb = [(-1.5, G - 0.5), (1.5, G - 0.5), (1.5, G), (-1.5, G)]
    for i in range(1, A.NI):
        x = A.GX0 + i * A.MOD
        if x < A.XE - 1:
            soup.add(A.MAT['tbar'], P.strip((x, A.YS), (x, A.BULK_Y), [(d, z) for d, z in tb]))
    for j in range(1, A.NJ):
        y = A.GY0 + j * A.MOD
        if y < A.BULK_Y - 1:
            soup.add(A.MAT['tbar'], P.strip((A.XW, y), (A.XE, y), [(d, z) for d, z in tb]))
    n += put_soup(m, soup, 'ceil')
    A.REPORT.setdefault('body', {})['ceiling_tris'] = soup.count()
    return n
