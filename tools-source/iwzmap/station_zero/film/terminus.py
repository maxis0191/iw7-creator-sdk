"""Station Zero, the Terminus (bible zone 19; redesign PLAN decision 4; T1, 27 Nov 2026).

The station as a timetable knows it: one platform bay of green-bar printer paper, far from the map, reached only by the trip from the
cab of car 1 (modules/terminus.gsc). The stock Pack-a-Punch machine (a film projector) stands on a red-oxide validator post where a
ticket validator would, faces across the empty track and throws the next reel onto the paper wall: the projected second platform.
No sign names the machine. Target frame: C:/studio-data/sz/film/concept/terminus.png.

    build(m)   adds the section's layers (ids and layers prefixed terminus_) to a Studio Map
    main()     writes C:/studio-data/sz/film/terminus/doc: the B1 document (base_lit_nopap + its layers and settings) + this section

    STUDIO_ROOT=C:/studio python terminus.py [--out <doc folder>] [--b1 <B1 doc folder>]
"""
import argparse
import glob
import math
import os
import shutil
import sys

STUDIO_ROOT = os.environ.get('STUDIO_ROOT') or r'C:\studio'
if STUDIO_ROOT not in sys.path:
    sys.path.insert(0, STUDIO_ROOT)
from studio import Map, build as B  # noqa: E402

ART = os.environ.get('SZ_TERMINUS_ART') or r'C:\studio-data\sz\film\art\terminus'
DERIVED = os.environ.get('SZ_TERMINUS_DERIVED') or r'C:\studio-data\sz\film\terminus\art'     # pictures this file derives from ART
B1_DOC = r'C:\studio-data\sz\film\b1\doc'
OUT_DOC = r'C:\studio-data\sz\film\terminus\doc'
# the base: B1's base_lit_nopap regenerated from THIS worktree (C:\studio-data\sz\film\terminus\regen.sh <out> IWZ_LIT_FIRST=1): 19 of 20 files equal to B1's, the
# one difference modules/cp_iwz_terminus.gsc (the Terminus vision). Studio rebuilds modules/ only when the base's module equals what this SDK emits
# (studio/basegame.py), so a module change needs its regenerated base, or the build keeps the base's old module with the markers of the layers left out.
BASE = r'C:\studio-data\sz\film\terminus\base_lit_nopap'

# ------------------------------------------------------------------------------------------------ the place
# A far box: 6,300 units west and 6,400 south of the nearest base geometry (x -4004..3809, y 1199..4601) and of every zone of the bible
# (x -5000..5300, y -400..5800); inside the light grid (x -12288..6144, y -6144..6144, z -2048..4096). Nothing above or under it.
X0, X1 = -10900.0, -9500.0          # 1,400 along the platform (x)
Y0, Y1 = -5200.0, -4300.0           # 900 across: the screen wall (south, Y0) .. the back wall (north, Y1)
YE = -4944.0                        # the platform edge; the deck is YE..Y1 (644 deep), the paper "track bed" Y0..YE (256)
ZD, ZP, ZC = 0.0, -56.0, 320.0      # deck, the drop where the track would be (56), ceiling underside (bible: 320)
T = 16.0                            # wall and slab thickness
XM = (X0 + X1) / 2                  # -10200, the split of every long piece (no piece wider than 1,024)
PITCH = 288.0                       # column pitch (QUALITY-BAR rule 23, the stock station's)
COLS_X = [XM + PITCH * (k - 2) for k in range(5)]
COL_Y, COL_W = Y1 - 72.0, 48.0
BENCH_X = [(COLS_X[k] + COLS_X[k + 1]) / 2 for k in range(4)]

# the machine: the stock projector (zmb_pap_machine_animated, 121 x 44.5 x 92) on the validator post. Measured in pass 1: the relocated scriptable lays the
# model's long axis 90 degrees from the pap yaw (yaw 270 put it along x, reels east). PAP_YAW 180 lays it along y, lens end south toward the screen, and the
# user stands at its west side, as at the stock machine. blend_core.pap_offsets puts the machine 10 behind the use point: machine at USE + (10, 0).
POST_H = 40.0
PAP_YAW = 180.0
MACH = (XM, -4640.0)
USE = (MACH[0] - 10.0, MACH[1], POST_H)
LENS = (MACH[0], MACH[1] - 64.0, POST_H + 52.0)          # the lens end of the body (+X), about 52 over its feet
SCREEN = (MACH[0], Y0, 150.0, 384.0, 216.0)              # centre x, wall y, centre z, w, h of the projected picture

ARRIVAL = (-9700.0, -4640.0, ZD)     # the marker: the module spreads four slots 48 apart along y (-72, -24, 24, 72) and faces them west
ARRIVAL_YAW = 180.0
SLOTS = [(ARRIVAL[0], ARRIVAL[1] + k * 48.0 - 72.0) for k in range(4)]
AREA = [X0, Y0, ZP - 16.0, X1, Y1, ZC]                  # the Terminus box the module reads (pause, return): the whole room, the drop included

WALL_TILE = 128.0                    # 16 bars of 64 px in a 1024 px picture: one bar = 8 units
PAPER_GLOSS = 0.12                   # matte paper

LIGHT_GROUP = 'emergency'            # lit-first base: every lamp baked (PLAN decision 3)
MACHINE_KEY = 3.0                    # baked + runtime (pass 4: 6.0 baked only, body 0.14 of the paper)
BEAM = 14.0                          # pass 3: 4.0 gave no visible warm rectangle around the picture
TUBE_INTENSITY, TUBE_RADIUS = 3.0, 2.2  # pass 1 (1.0, 1.6) read as a dim room; the bible's light is flat office fluorescent


def _p(*names):
    return os.path.join(ART, *names)


def derived_pictures():
    """the floor and ceiling paper: the same tile turned a quarter, so that the bars cross the platform (lines of constant x) as the bars of one
    fan-fold sheet laid along the platform would; written once into DERIVED"""
    from PIL import Image
    os.makedirs(DERIVED, exist_ok=True)
    out = os.path.join(DERIVED, 'paper_greenbar_tile_q.png')
    src = _p('paper_greenbar_tile.png')
    if not os.path.isfile(out) or os.path.getmtime(out) < os.path.getmtime(src):
        Image.open(src).convert('RGB').transpose(Image.Transpose.ROTATE_90).save(out)
    return {'floor': out, 'screen': screen_picture()}


def screen_picture():
    """the projected reel as light on paper, not a framed print (lead, pass 1): the art's vignetted border cropped away, the picture brightened, and an alpha
    that is the picture's own light (dark parts let the paper through) times a feather to nothing over the outer 14 % of each side"""
    import numpy as np
    from PIL import Image
    out = os.path.join(DERIVED, 'screen_second_platform_light.png')
    src = _p('screen_second_platform.png')
    if os.path.isfile(out) and os.path.getmtime(out) >= max(os.path.getmtime(src), os.path.getmtime(__file__)):
        return out
    im = Image.open(src).convert('RGB')
    w, h = im.size
    mx, my = int(w * 0.06), int(h * 0.08)
    im = im.crop((mx, my, w - mx, h - my)).resize((1024, 576), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    rgb = np.clip(a * 1.35, 0, 1)
    def ramp(n, f):
        t = np.minimum(np.arange(n) + 0.5, n - np.arange(n) - 0.5) / (n * f)
        t = np.clip(t, 0, 1)
        return t * t * (3 - 2 * t)
    feather = ramp(576, 0.14)[:, None] * ramp(1024, 0.10)[None, :]
    alpha = np.clip(0.35 + lum * 1.4, 0, 1) * feather
    rgba = np.dstack([rgb, alpha])
    Image.fromarray((rgba * 255 + 0.5).astype('uint8'), 'RGBA').save(out)
    return out


def materials(m):
    d = derived_pictures()
    wall = B.material(m, 'term_paper_wall', _p('paper_greenbar_tile.png'), gloss=PAPER_GLOSS, tile=WALL_TILE, id='terminus_mat_paper_wall')
    floor = B.material(m, 'term_paper_floor', d['floor'], gloss=PAPER_GLOSS, tile=WALL_TILE, id='terminus_mat_paper_floor')
    times = B.material(m, 'term_paper_times', _p('paper_times_column.png'), gloss=PAPER_GLOSS, tile=(COL_W, 192.0), id='terminus_mat_paper_times')
    return {'wall': wall, 'floor': floor, 'times': times, 'post': 'w/metal_painted_red_01', 'iron': 'w/metal_painted_01_black'}


# ------------------------------------------------------------------------------------------------ helpers
def _quad(a, b, c, d):
    return [[a, b, c], [a, c, d]]


def _fold(m, mat, p0, p1, n_in, up, size, id):
    """a 45 degree fold piece (render only) along the line p0 -> p1 where a floor meets a wall (up=+1) or a wall meets the ceiling (up=-1):
    it rises `size` from the floor `size` out from the wall. n_in is the unit (x, y) pointing from the wall into the room."""
    nx, ny = n_in
    z = p0[2]
    a = (p0[0] + nx * size, p0[1] + ny * size, z)
    b = (p1[0] + nx * size, p1[1] + ny * size, z)
    c = (p1[0], p1[1], z + up * size)
    d = (p0[0], p0[1], z + up * size)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / WALL_TILE
    W = size * math.sqrt(2.0) / WALL_TILE
    tris = _quad(a, b, c, d)
    uvs = [[[0, 0], [L, 0], [L, W]], [[0, 0], [L, W], [0, W]]]
    # face the room: the normal of (b - a) x (c - a) must point along n_in (and up for a floor fold, down for a ceiling fold)
    ab = [b[i] - a[i] for i in range(3)]
    ac = [c[i] - a[i] for i in range(3)]
    n = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
    if n[0] * nx + n[1] * ny + n[2] * up < 0:
        tris = [[t[0], t[2], t[1]] for t in tris]
        uvs = [[u[0], u[2], u[1]] for u in uvs]
    return B.mesh(m, mat, tris=[[list(p) for p in t] for t in tris], uvs=uvs, mode='render', id=id)


def _strip(m, at, normal, length, along, id, h=16.0):
    """sprocket-hole edge strips (paper_greenbar_edge.png, 128 x 16, alpha holes) along `length` from `at` in direction `along`"""
    n = max(1, int(round(length / 128.0)))
    w = length / n
    out = []
    for k in range(n):
        c = [at[i] + along[i] * (w * (k + 0.5)) for i in range(3)]
        rot = 0.0
        if abs(normal[2]) > 0.9 and abs(along[1]) > 0.9:
            rot = 90.0
        out.append(B.decal(m, image=_p('paper_greenbar_edge.png'), at=c, normal=normal, size=(w, h), rot=rot, id='%s_%d' % (id, k)))
    return out


# ------------------------------------------------------------------------------------------------ the section
def shell(m, mat):
    """floor, drop, walls, ceiling: one paper sheet turned up at every fold; pieces no wider than 1,024 (P1: a collision triangle wider than
    that is never split)"""
    m.use('terminus_shell')
    W, F = mat['wall'], mat['floor']
    halves = [(X0, XM, 'w'), (XM, X1, 'e')]
    for a, b, s in halves:
        # floors are `floor` objects, not boxes: on a lattice base (this one) only floor, room, stair and mesh objects are regions that get new
        # navigation cells (studio/based.py _nav_lattice), and the island needs its cells
        B.floor(m, [a, YE, b, Y1], ZD, F, thick=ZD - ZP + 8.0, id='terminus_deck_' + s)        # the deck; its south face is the edge (the sheet folds over it)
        B.floor(m, [a, Y0, b, YE], ZP, F, thick=T, id='terminus_bed_' + s)                     # beyond the edge: no track, only paper, 56 lower
        B.box(m, [a, Y0 - T, ZP - T, b, Y0, ZC + 8.0], W, id='terminus_screen_wall_' + s)       # the far wall, one tall sheet: the screen
        B.box(m, [a, Y1, ZD - 8.0, b, Y1 + T, ZC + 8.0], W, id='terminus_back_wall_' + s)
        B.box(m, [a - (T if s == 'w' else 0.0), Y0 - T, ZC, b + (T if s == 'e' else 0.0), Y1 + T, ZC + 8.0], F, id='terminus_ceiling_' + s)
    for x, s in ((X0 - T, 'w'), (X1, 'e')):
        B.box(m, [x, Y0 - T, ZP - T, x + T, Y1 + T, ZC + 8.0], W, id='terminus_end_wall_' + s)
    # the player stays on the deck: a clip along the edge (render-free, so the bake and the beam pass)
    for a, b, s in halves:
        B.clip(m, [a, YE, ZD, b, YE + 6.0, ZD + 160.0], id='terminus_edge_clip_' + s)


def folds(m, mat):
    """the paper turns where floor meets wall and wall meets ceiling: 45 degree fold pieces of 16, and a sprocket strip on each fold"""
    m.use('terminus_folds')
    W = mat['wall']
    S = 16.0
    k = 0
    for a, b, s in ((X0, XM, 'w'), (XM, X1, 'e')):
        _fold(m, W, (a, Y1, ZD), (b, Y1, ZD), (0, -1), 1, S, 'terminus_fold_back_floor_' + s)
        _fold(m, W, (a, Y0, ZP), (b, Y0, ZP), (0, 1), 1, S, 'terminus_fold_screen_floor_' + s)
        _fold(m, W, (a, Y1, ZC), (b, Y1, ZC), (0, -1), -1, S, 'terminus_fold_back_ceiling_' + s)
        _fold(m, W, (a, Y0, ZC), (b, Y0, ZC), (0, 1), -1, S, 'terminus_fold_screen_ceiling_' + s)
    for x, n, s in ((X0, (1, 0), 'w'), (X1, (-1, 0), 'e')):
        _fold(m, W, (x, YE, ZD), (x, Y1, ZD), n, 1, S, 'terminus_fold_%s_deck' % s)
        _fold(m, W, (x, Y0, ZP), (x, YE, ZP), n, 1, S, 'terminus_fold_%s_bed' % s)
        _fold(m, W, (x, Y0, ZC), (x, Y1, ZC), n, -1, S, 'terminus_fold_%s_ceiling' % s)
        k += 1
    # sprocket strips: along the platform edge (on the deck and down its face), under each wall top, above each floor fold
    L = X1 - X0
    _strip(m, (X0, YE + 8.0, ZD), (0, 0, 1), L, (1, 0, 0), 'terminus_strip_edge_top')
    _strip(m, (X0, YE, ZD - 8.0), (0, -1, 0), L, (1, 0, 0), 'terminus_strip_edge_face')
    _strip(m, (X0, Y1, ZC - S - 8.0), (0, -1, 0), L, (1, 0, 0), 'terminus_strip_back_top')
    _strip(m, (X0, Y0, ZC - S - 8.0), (0, 1, 0), L, (1, 0, 0), 'terminus_strip_screen_top')
    _strip(m, (X0, Y1, ZD + S + 8.0), (0, -1, 0), L, (1, 0, 0), 'terminus_strip_back_base')
    _strip(m, (X0, Y0, ZP + S + 8.0), (0, 1, 0), L, (1, 0, 0), 'terminus_strip_screen_base')
    for x, n, s in ((X0, (1, 0, 0), 'w'), (X1, (-1, 0, 0), 'e')):
        _strip(m, (x, Y0, ZC - S - 8.0), n, Y1 - Y0, (0, 1, 0), 'terminus_strip_%s_top' % s)
        _strip(m, (x, YE, ZD + S + 8.0), n, Y1 - YE, (0, 1, 0), 'terminus_strip_%s_base' % s)
        _strip(m, (x, Y0, ZP + S + 8.0), n, YE - Y0, (0, 1, 0), 'terminus_strip_%s_bed' % s)


def furniture(m, mat):
    """columns of times at the station's pitch, four folded paper benches between them against the back wall"""
    m.use('terminus_furniture')
    for k, x in enumerate(COLS_X):
        B.box(m, [x - COL_W / 2, COL_Y - COL_W / 2, ZD, x + COL_W / 2, COL_Y + COL_W / 2, ZC], mat['times'],
              uv={'*': {'tile': [COL_W, 192.0]}}, id='terminus_column_%d' % (k + 1))
    for k, x in enumerate(BENCH_X):
        a, b = x - 100.0, x + 100.0
        B.box(m, [a, Y1 - 40.0, ZD, b, Y1, ZD + 10.0], mat['floor'], id='terminus_bench_%d_step' % (k + 1))      # the stepped fold profile
        B.box(m, [a + 4.0, Y1 - 34.0, ZD + 10.0, b - 4.0, Y1, ZD + 18.0], mat['floor'], id='terminus_bench_%d_seat' % (k + 1))
        B.box(m, [a + 4.0, Y1 - 10.0, ZD + 18.0, b - 4.0, Y1, ZD + 44.0], mat['wall'], id='terminus_bench_%d_back' % (k + 1))


def printed(m):
    """what is printed on the sheet: footprint fields facing the edge, four fresh pairs at the arrival, the leader count 8 to 2"""
    m.use('terminus_print')
    # fields of printed pairs (96 x 96, toes toward the edge = picture top to the south: rot 180), clear of the machine and of the arrival
    rows = [YE + 100.0 + 96.0 * j for j in range(5)]
    cols = [X0 + 48.0 + 96.0 * i for i in range(14)]
    n = 0
    for y in rows:
        for x in cols:
            if math.hypot(x - MACH[0], y - MACH[1]) < 110.0:
                continue
            if abs(x - ARRIVAL[0]) < 80.0 and SLOTS[0][1] - 40.0 <= y <= SLOTS[-1][1] + 40.0:
                continue
            if abs(y - COL_Y) < 60.0 and min(abs(x - c) for c in COLS_X) < 72.0:
                continue
            n += 1
            B.decal(m, image=_p('footprints_printed.png'), at=(x, y, ZD), normal=(0, 0, 1), size=(96.0, 96.0), rot=180.0,
                    id='terminus_steps_%d' % n)
    for k, (x, y) in enumerate(SLOTS):
        B.decal(m, image=_p('footprints_fresh.png'), at=(x - 20.0, y, ZD), normal=(0, 0, 1), size=(28.0, 28.0), rot=180.0,
                id='terminus_steps_fresh_%d' % (k + 1))
    # the leader count along the edge, 8 at the east end to 2 toward the machine and the screen: never a 1
    for k, num in enumerate(range(8, 1, -1)):
        x = X1 - 60.0 - k * 190.0
        B.decal(m, image=_p('leader_%d.png' % num), at=(x, YE + 40.0, ZD), normal=(0, 0, 1), size=(32.0, 32.0), rot=180.0,
                id='terminus_leader_%d' % num)


def _hung_board(m, mat, id, c, along, w, h, rods_to=ZC):
    """a paper board hung from the ceiling on two iron rods: c its centre, `along` 'x' or 'y' (the board's long side), thickness 4"""
    x, y, z = c
    if along == 'y':
        box = [x - 2.0, y - w / 2, z - h / 2, x + 2.0, y + w / 2, z + h / 2]
        rods = [(x, y - w / 2 + 12.0), (x, y + w / 2 - 12.0)]
    else:
        box = [x - w / 2, y - 2.0, z - h / 2, x + w / 2, y + 2.0, z + h / 2]
        rods = [(x - w / 2 + 12.0, y), (x + w / 2 - 12.0, y)]
    B.box(m, box, mat['wall'], mode='render', id=id + '_board')
    for k, (rx, ry) in enumerate(rods):
        B.box(m, [rx - 0.75, ry - 0.75, z + h / 2, rx + 0.75, ry + 0.75, rods_to], mat['iron'], mode='render', id='%s_rod_%d' % (id, k + 1))
    return box


def signs_and_clock(m, mat):
    m.use('terminus_signs')
    # "047 . TERMINUS", hung across the platform near the arrival, read from both ends of the platform
    sx, sy, sz = -10480.0, -4620.0, 236.0              # pass 3: at -9900 it hung above the arrival view; here it is the far landmark of it
    bx = _hung_board(m, mat, 'terminus_sign_main', (sx, sy, sz), 'y', 224.0, 48.0)
    for nx, s in ((1, 'e'), (-1, 'w')):
        B.sign(m, image=_p('sign_terminus.png'), at=(sx + nx * 2.0 - nx * 3.4, sy, sz), normal=(nx, 0, 0), size=(216.0, 42.2), id='terminus_sign_main_' + s)
    # "FARE VALIDATION" hung over the machine, read along the platform
    fx, fy, fz = MACH[0], MACH[1], 196.0
    _hung_board(m, mat, 'terminus_sign_fare', (fx, fy, fz), 'y', 104.0, 30.0)
    for nx, s in ((1, 'e'), (-1, 'w')):
        B.sign(m, image=_p('sign_fare_validation.png'), at=(fx + nx * 2.0 - nx * 3.4, fy, fz), normal=(nx, 0, 0), size=(96.0, 24.0), id='terminus_sign_fare_' + s)
    # the station clock, hung between the two signs; double faced (two stock clock faces back to back). It does not run.
    cx, cy, cz = -10050.0, -4620.0, 236.0
    for yaw, s in ((90.0, 'e'), (270.0, 'w')):
        B.prop(m, 'sign_clock_04', (cx, cy, cz), yaw=yaw, scale=2.6, id='terminus_clock_' + s)
    B.box(m, [cx - 1.0, cy - 1.0, cz + 24.0, cx + 1.0, cy + 1.0, ZC], mat['iron'], mode='render', id='terminus_clock_rod')


def machine(m, mat):
    """the validator post (red oxide, the only saturated colour with the beam) and the stock machine on it; the use point is in front of its lens end"""
    m.use('terminus_machine')
    mx, my = MACH
    P = mat['post']
    B.box(m, [mx - 30.0, my - 30.0, ZD, mx + 30.0, my + 30.0, ZD + 5.0], P, id='terminus_post_foot')
    B.box(m, [mx - 13.0, my - 13.0, ZD + 5.0, mx + 13.0, my + 13.0, POST_H - 6.0], P, id='terminus_post_shaft')
    B.box(m, [mx - 18.0, my - 18.0, POST_H - 10.0, mx + 18.0, my + 18.0, POST_H - 6.0], P, id='terminus_post_collar')
    B.box(m, [mx - 22.0, my - 44.0, POST_H - 6.0, mx + 22.0, my + 44.0, POST_H], P, id='terminus_post_top')
    # the wordless pictogram (a ticket into a slot, out striped), once: on the post's face toward the user
    B.decal(m, image=_p('pictogram_validate.png'), at=(mx - 13.0, my, ZD + 20.0), normal=(-1, 0, 0), size=(20.0, 20.0), id='terminus_pictogram')
    B.pap(m, USE, PAP_YAW, id='terminus_pap')


def light(m, mat):
    """flat, even, shadowless office fluorescent over the paper (ceiling tubes, all baked), and the beam: the only warm light, the room's key"""
    m.use('terminus_lights')
    rows = [Y1 - 180.0, YE + 164.0, (Y0 + YE) / 2]
    for j, y in enumerate(rows):
        for k, x in enumerate(COLS_X):
            B.fixture(m, 'ceiling_tube', (x, y, ZC), facing=0.0, radius=TUBE_RADIUS, intensity=TUBE_INTENSITY, group=LIGHT_GROUP, bake='baked',
                      id='terminus_tube_%d_%d' % (j + 1, k + 1))
    # the beam: from the lens to the middle of the projected picture
    tx, ty, tz = SCREEN[0], SCREEN[1], SCREEN[2]
    d = (tx - LENS[0], ty - LENS[1], tz - LENS[2])
    ln = math.sqrt(sum(v * v for v in d))
    half = math.degrees(math.atan2(SCREEN[3] / 2, ln))
    B.light(m, LENS, color=(1.0, 0.74, 0.42), radius=ln * 1.5, intensity=BEAM, group=LIGHT_GROUP, type='spot',
            dir=[round(v / ln, 4) for v in d], inner=round(half * 0.85, 1), outer=round(half * 1.3, 1), id='terminus_beam')
    # the machine's own light (lead, pass 1: a black silhouette): one soft warm spot from above the user's side, so that its red and brass read
    # pass 4 measured the body at 0.14 of the paper behind it: a scriptable model takes baked light only through the light grid, so the key is ALSO a runtime
    # emergency light (a lights.txt row: per-pixel on models; no networked record), about 110 units above-front on the user's side as the stock key is (QUALITY-BAR A2)
    mk = (MACH[0] - 70.0, MACH[1] - 20.0, POST_H + 130.0)
    dm = (MACH[0] - mk[0], MACH[1] - mk[1], POST_H + 50.0 - mk[2])
    lm = math.sqrt(sum(v * v for v in dm))
    B.light(m, mk, color=(1.0, 0.86, 0.66), radius=lm * 2.2, intensity=MACHINE_KEY, group=LIGHT_GROUP, type='spot',
            dir=[round(v / lm, 4) for v in dm], inner=22.0, outer=48.0, runtime=True, id='terminus_machine_key')
    # the next reel on the paper: the second platform, emissive, inside the lit rectangle
    # pass 3: the emissive route ignores the picture's alpha (its feathered border drew black), so the reel is a printed-light decal on the paper: alpha
    # blended (the paper's bars show through its dark parts and its feathered edge) and lit by the beam, as light thrown on paper is
    B.decal(m, image=screen_picture(), at=(tx, ty, tz), normal=(0, 1, 0), size=(SCREEN[3], SCREEN[4]), id='terminus_screen_picture')


def gameplay(m):
    m.use('terminus_gameplay')
    B.zone(m, 'terminus', [X0, Y0, ZP - 16.0, X1, Y1, ZC], island=True, id='terminus_zone')
    B.marker(m, 'terminus_arrival', ARRIVAL, name='terminus', yaw=ARRIVAL_YAW, area=AREA, id='terminus_arrival')


def cameras(m):
    m.use('terminus_cams')
    B.camera(m, 'term_arrival', (ARRIVAL[0], ARRIVAL[1], 64.0), ARRIVAL_YAW, pitch=4.0, id='term_arrival')
    B.camera(m, 'term_long', (X1 - 40.0, YE + 120.0, 150.0), 186.0, pitch=10.0, id='term_long')
    B.camera(m, 'term_machine', (MACH[0] + 190.0, MACH[1] - 150.0, 110.0), round(math.degrees(math.atan2(150.0, -190.0)), 1), pitch=6.0, id='term_machine')
    B.camera(m, 'term_screen', (MACH[0] + 150.0, YE + 30.0, 90.0), round(math.degrees(math.atan2(Y0 - YE - 30.0, -150.0)) % 360.0, 1), pitch=-10.0,
             id='term_screen')
    B.camera(m, 'term_edge', (X1 - 30.0, YE + 70.0, 60.0), 182.0, pitch=12.0, id='term_edge')


# the Terminus's own vision: the lit keys of the station without its -2.5 EV bias, fog and veil off. Written by the darkness build as a variant under the spare stock
# vision name cp_frontend (only the frontend map uses it), which modules/terminus.gsc applies to each rider on arrival and takes off on the return.
VISION_NAME, VISION_VARIANT = 'cp_frontend', 'term'
VISION_KEYS = os.environ.get('SZ_TERMINUS_VISION') or ('fogMaxOpacity=0;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0;'
                                                       'tonemapAdaptSpeed=0.3;tonemapAutoExposureAdjust=0.7')     # pass 3 at 0: mean 0.45, bars p90 0.66


def _dark_args(m):
    return m.settings.setdefault('build', {}).setdefault('darkness', {}).setdefault('args', [])


def vision(m):
    """adds (or replaces) the Terminus variant and its alias in settings.build.darkness.args"""
    a = _dark_args(m)
    def put(flag, sep, item, key):
        if flag not in a:
            a.extend([flag, item])
            return
        i = a.index(flag) + 1
        parts = [p for p in a[i].split(sep) if p and not key(p)]
        a[i] = sep.join(parts + [item])
    put('--variants', '|', '%s:%s' % (VISION_VARIANT, VISION_KEYS), lambda p: p.split(':', 1)[0] == VISION_VARIANT)
    put('--alias', ',', '%s=%s' % (VISION_NAME, VISION_VARIANT), lambda p: p.split('=', 1)[0] == VISION_NAME)


def look_copy(m):
    """a copy of the document for the room's own frames only: the camera of `live shot` is no rider, so the lit vision itself takes the Terminus keys"""
    a = _dark_args(m)
    a[a.index('--lit') + 1] = VISION_KEYS
    m.name = m.name + '_look'


def build(m):
    """adds the Terminus section to the Studio Map m (layers terminus_*) and its vision variant; returns the layer names"""
    vision(m)
    mat = None
    m.use('terminus_materials')
    mat = materials(m)
    shell(m, mat)
    folds(m, mat)
    furniture(m, mat)
    printed(m)
    signs_and_clock(m, mat)
    machine(m, mat)
    light(m, mat)
    gameplay(m)
    cameras(m)
    return [n for n in m.order if n.startswith('terminus_')]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=OUT_DOC)
    ap.add_argument('--b1', default=B1_DOC, help='the B1 document (base_lit_nopap, its layers and build settings) the section goes on')
    ap.add_argument('--look', action='store_true', help='write the look copy (the lit vision = the Terminus vision) into <out>_look as well')
    ap.add_argument('--base', default=BASE, help='the base emit (default: base_lit_nopap regenerated from this worktree)')
    a = ap.parse_args(argv)
    m = Map.load(a.b1)
    m.base = {'kind': 'emit', 'path': a.base}
    m.name, m.title = 'sz_terminus', 'Station Zero: the Terminus on the lit-first base without Pack-a-Punch (T1)'
    for n in [n for n in m.order if n.startswith('terminus_')]:
        m.remove_layer(n)
    build(m)
    os.makedirs(a.out, exist_ok=True)
    for f in glob.glob(os.path.join(a.b1, '*.png')):          # the B1 layers' own pictures, beside map.json
        dst = os.path.join(a.out, os.path.basename(f))
        if not os.path.isfile(dst) or os.path.getsize(dst) != os.path.getsize(f):
            shutil.copy2(f, dst)
    m.save(a.out)
    print(a.out)
    if a.look:
        lk = a.out.rstrip('\\/') + '_look'
        look_copy(m)
        os.makedirs(lk, exist_ok=True)
        for f in glob.glob(os.path.join(a.out, '*.png')):
            dst = os.path.join(lk, os.path.basename(f))
            if not os.path.isfile(dst) or os.path.getsize(dst) != os.path.getsize(f):
                shutil.copy2(f, dst)
        m.path = None
        m.save(lk)
        print(lk)


if __name__ == '__main__':
    main()
