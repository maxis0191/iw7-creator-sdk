r"""shell_hall: what breaks the Arcade hall's floor, the night it stopped, a year of abandonment, and the fronts lit by models
(worker A2, round of 28 Nov; the lead's reading of the ON frames against the stock shopfront and subway frames).

Called by arcade_shell.build() after the shell; `A` is the arcade_shell module (its constants, MAT, helpers).
Every model here was looked at with `store show` first (sheets under C:\studio-data\store\cache\show).
"""
import math
import os

from studio import build as B

import shellgeo as G

PICS = r'C:\studio-data\sz\film\arcade\shell\pictures'
ISLAND_Y = 3985.0                       # the centre line of the hall (the north lane, y 4032..4232, stays clear; AC1: 3950 -> 3985 for the colonnade line at 3860)
ISLANDS = (-2800.0, -2140.0)            # the first 89 clear of the Copy Stop oblique eye (check: it stood 21 from it at -2716)
KIOSK = (-2428.0, 3860.0)               # in the colonnade, between the columns at x -2572 and -2284
STREAMER_MATS = ('w/plastic_wall_plain_red_01', 'w/plastic_wall_plain_blue_01', 'w/plastic_wall_plain_yellow_01', 'w/plastic_wall_plain_green_01')
POOL = {   # the colour each shop throws on the tile outside its front: (rgb, intensity, radius, z) - four different rows (rule 11)
    'needle_drop': ((1.0, 0.55, 0.2), 2.6, 400.0, 158.0),        # pass 6: radius 250..280 put the pool at the falloff's edge (throw ~240);
    'copy_stop': ((0.88, 0.93, 1.0), 2.3, 420.0, 160.0),         # pass 7: at 0.8..1.1 the hall's white panels washed the colour out: doubled
    'hole_nine': ((1.0, 0.45, 0.75), 2.8, 390.0, 162.0),         # L1 (C5, 28 Nov): x1.3 with the fill lowered: pool to mid hall at least 4 to 1
    'heel_key': ((1.0, 0.72, 0.45), 2.2, 380.0, 164.0),
}


def pictograms():
    """two Halcyon Rapid Transit hanging signs, no words: an arrow ahead and a train; an arrow ahead and a stair (style of the directory:
    black field, white mark, the roundel with a bar)"""
    from PIL import Image, ImageDraw
    os.makedirs(PICS, exist_ok=True)
    out = {}
    for name in ('transit_train', 'transit_stairs', 'transit_back'):
        W, H = 512, 256
        im = Image.new('RGB', (W, H), (18, 18, 20))
        d = ImageDraw.Draw(im)
        d.rectangle([6, 6, W - 7, H - 7], outline=(230, 230, 226), width=4)
        d.ellipse([20, 20, 72, 72], outline=(236, 236, 232), width=6)                       # the roundel
        d.rectangle([30, 42, 62, 50], fill=(236, 236, 232))
        if name != 'transit_back':
            d.polygon([(150, 60), (200, 120), (168, 120), (168, 200), (132, 200), (132, 120), (100, 120)], fill=(240, 240, 236))   # arrow ahead
        if name == 'transit_train':
            d.rounded_rectangle([250, 70, 460, 180], radius=26, fill=(240, 240, 236))
            for k in range(3):
                d.rectangle([270 + 60 * k, 90, 310 + 60 * k, 125], fill=(18, 18, 20))
            for x in (290, 420):
                d.ellipse([x - 14, 168, x + 14, 196], fill=(240, 240, 236))
            d.rectangle([240, 200, 470, 208], fill=(240, 240, 236))
        elif name == 'transit_stairs':
            for k in range(5):
                d.rectangle([250 + 42 * k, 190 - 26 * k, 292 + 42 * k, 200], fill=(240, 240, 236))
        elif name == 'transit_back':
            d.rectangle([110, 120, 400, 128], fill=(120, 120, 118))
        p = os.path.join(PICS, name + '.png')
        im.save(p)
        out[name] = p
    return out


def hall_life(A, m):
    m.use('hall')
    rep = A.REPORT.setdefault('hall', {})
    # 1. bench islands on the centre line: two benches back to back, a planter with dead stems at each end, a bin beside
    for k, x in enumerate(ISLANDS):
        B.prop(m, 'street_bench_long_iw6', (x, ISLAND_Y - 20.0, 0.0), yaw=0.0, layer='hall', id='island_%d_bench_s' % k, clip=[-49.0, -19.0, 0.0, 49.0, 19.0, 20.0])
        B.prop(m, 'street_bench_long_iw6', (x, ISLAND_Y + 20.0, 0.0), yaw=180.0, layer='hall', id='island_%d_bench_n' % k, clip=[-49.0, -19.0, 0.0, 49.0, 19.0, 20.0])
        for j, dx in enumerate((-66.0, 66.0)):
            B.prop(m, 'p7_planters_taperedbox_small', (x + dx, ISLAND_Y, 0.0), yaw=90.0, layer='hall', id='island_%d_planter_%d' % (k, j), clip=[-13.0, -16.0, 0.0, 13.0, 16.0, 32.0])
            B.prop(m, 'p7_foliage_flower_bouquet_glass_dead', (x + dx + (3.0 if j else -2.0), ISLAND_Y + 2.0, 26.0), yaw=40.0 + 70.0 * j, layer='hall', id='island_%d_stems_%d' % (k, j))
        B.prop(m, 'cp_disco_street_trashcan_01', (x + 100.0, ISLAND_Y + 30.0, 0.0), yaw=20.0, layer='hall', id='island_%d_bin' % k, clip=[-12.0, -12.0, 0.0, 12.0, 12.0, 30.0])
    rep['islands'] = len(ISLANDS)
    # 2. the shuttered newsstand kiosk in the colonnade (a closed front: rule 4's rhythm)
    kiosk(A, m)
    # 3. a row of luggage lockers on the south wall between the first bench and the second
    for k in range(4):
        B.prop(m, 'cp_disco_subway_lockers_02', (-2635.4 + 29.2 * k, A.YS + 0.3, 0.0), yaw=90.0, layer='hall', id='locker_%d' % k)
    B.clip(m, [-2650.0, A.YS, 0.0, -2533.0, A.YS + 19.0, 73.0], layer='hall', id='lockers_clip')
    # 4. two hanging transit signs near the entrance, readable when walking out (their back carries the roundel only)
    pics = pictograms()
    for k, (y, nm) in enumerate(((3840.0, 'transit_train'), (3960.0, 'transit_stairs'))):
        x = -1480.0
        A.rbox(m, 'transit_%d_board' % k, [x - 1.0, y - 36.0, 196.0, x + 1.0, y + 36.0, 232.0], A.MAT['alu_black'])
        B.sign(m, image=pics[nm], at=(x - 1.0, y, 214.0), normal=(-1.0, 0.0, 0.0), size=(70.0, 34.0), layer='hall', id='transit_%d_face' % k)
        B.sign(m, image=pics['transit_back'], at=(x + 1.0, y, 214.0), normal=(1.0, 0.0, 0.0), size=(70.0, 34.0), layer='hall', id='transit_%d_back' % k)
        for j, dy in enumerate((-30.0, 30.0)):
            A.rbox(m, 'transit_%d_rod_%d' % (k, j), [x - 0.3, y + dy - 0.3, 232.0, x + 0.3, y + dy + 0.3, A.GRID_Z], A.MAT['tbar'])
    A.REPORT['art'] += ['transit_train.png (A2, PIL)', 'transit_stairs.png (A2, PIL)']
    night_it_stopped(A, m)
    abandonment(A, m)


def kiosk(A, m):
    x, y = KIOSK
    x0, x1, y0, y1 = x - 50.0, x + 50.0, y - 32.0, y + 32.0
    body, trim = 'w/zmb_brushed_metal_01_green', A.MAT['alu']
    A.bx(m, 'kiosk_body', [x0, y0, 0.0, x1, y1, 92.0], body)
    A.rbox(m, 'kiosk_plinth', [x0 - 1.0, y0 - 1.0, 0.0, x1 + 1.0, y1 + 1.0, 8.0], A.MAT['dark'])
    A.rbox(m, 'kiosk_roof', [x0 - 8.0, y0 - 8.0, 92.0, x1 + 8.0, y1 + 8.0, 98.0], trim)
    A.rbox(m, 'kiosk_fascia', [x0 - 8.0, y1 + 7.4, 98.0, x1 + 8.0, y1 + 8.0, 112.0], body)                # a blank fascia: no name of ours
    A.rbox(m, 'kiosk_housing', [x0 + 4.0, y1, 78.0, x1 - 4.0, y1 + 6.0, 90.0], A.MAT['housing'])
    A.rbox(m, 'kiosk_shutter', [x0 + 6.0, y1, 30.0, x1 - 6.0, y1 + 2.0, 78.0], A.MAT['shutter'])
    A.rbox(m, 'kiosk_ledge', [x0 + 2.0, y1, 26.0, x1 - 2.0, y1 + 10.0, 30.0], trim)
    for k, dy in enumerate((-16.0, 14.0)):                                           # magazine racks on its east side
        B.prop(m, 'misc_magazine_rack_01', (x1 + 0.7, y + dy, 8.0), yaw=0.0, layer='hall', id='kiosk_rack_%d' % k)
    B.prop(m, 'newspaper_stack_fn_01', (x1 + 14.0, y1 - 6.0, 0.0), yaw=25.0, layer='hall', id='kiosk_bundle_0')
    B.prop(m, 'newspaper_stack_fn_01', (x1 + 10.0, y1 - 24.0, 0.0), yaw=-10.0, layer='hall', id='kiosk_bundle_1')
    A.anchor('hall.kiosk_racks', [x1, y - 26.0, 8.0, x1 + 6.0, y + 26.0, 43.0], 'e', 'magazines of Dec 1984 on the two racks (goods, later)')


def streamer(A, m, id, pts, mat):
    """a paper streamer lying curled on the floor: the polyline with a wave across it (pass 6: straight 1.6 strips read as cables)"""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        steps = max(2, int(L // 6))
        for s in range(steps):
            t = s / steps
            w = 5.0 * math.sin(t * L / 9.0)
            out.append((x0 + (x1 - x0) * t + nx * w, y0 + (y1 - y0) * t + ny * w))
    out.append(pts[-1])
    A.mesh(m, id, mat, G.ribbon(out, 2.8, z=0.25))


def night_it_stopped(A, m):
    """three clusters with a reason each (not sprinkled): the gala buffet by the banner, the toast under the banner, the rush to D4"""
    n = 0
    # C1 the buffet: Hole Number Nine catered the gala; the folding table by the banner, glasses left, balloons tied to its leg
    tx, ty = -2250.0, 4040.0
    B.prop(m, 'com_folding_table', (tx, ty, 0.0), yaw=90.0, layer='hall', id='gala_table', clip=[-19.0, -41.0, 0.0, 19.0, 41.0, 34.0])
    for k, (dx, dy, mdl) in enumerate(((-30.0, -8.0, 'p7_cup_glass'), (-18.0, 6.0, 'p7_cup_glass'), (-4.0, -10.0, 'ma_cup_stack'), (12.0, 4.0, 'p7_cup_glass'),
                                       (26.0, -6.0, 'cup_paper_open_iw6'), (34.0, 8.0, 'p7_cup_glass'))):
        B.prop(m, mdl, (tx + dx, ty + dy, 33.9), yaw=17.0 * k, layer='hall', id='gala_cup_%d' % k)
        n += 1
    for k, (dx, mdl) in enumerate(((-44.0, 'balloon_on_string_1_red'), (-40.0, 'balloon_on_string_3_blue'))):
        B.prop(m, mdl, (tx + dx, ty + 16.0, 0.0), yaw=60.0 * k, layer='hall', id='gala_balloon_%d' % k)
        n += 1
    B.prop(m, 'p7_foliage_flower_bouquet_glass_dead', (tx + 52.0, ty - 30.0, 0.0), angles=[85.0, 30.0, 0.0], layer='hall', id='gala_bouquet')
    for k, pts in enumerate((((tx - 70, ty - 50), (tx - 30, ty - 62), (tx + 10, ty - 48), (tx + 60, ty - 70)), ((tx - 20, ty + 40), (tx + 30, ty + 55), (tx + 70, ty + 44)))):
        streamer(A, m, 'gala_streamer_%d' % k, pts, STREAMER_MATS[k])
    n += 3
    # C2 the toast under the banner: glasses and cups dropped round the second bench island
    ix = ISLANDS[1]
    for k, (dx, dy, mdl) in enumerate(((-30.0, -50.0, 'p7_cup_glass'), (24.0, -58.0, 'cup_paper_open_iw6'), (60.0, 46.0, 'ma_cup_stack_single_dmg'),
                                       (-62.0, 52.0, 'p7_cup_glass'), (10.0, 60.0, 'food_trash_cup_tall2'))):
        B.prop(m, mdl, (ix + dx, ISLAND_Y + dy, 0.0), angles=[90.0 if mdl == 'p7_cup_glass' else 0.0, 40.0 * k, 0.0], layer='hall', id='toast_cup_%d' % k)
        n += 1
    for k, pts in enumerate((((ix - 90, ISLAND_Y + 70), (ix - 40, ISLAND_Y + 90), (ix + 20, ISLAND_Y + 76)), ((ix + 40, ISLAND_Y - 70), (ix + 90, ISLAND_Y - 90)))):
        streamer(A, m, 'toast_streamer_%d' % k, pts, STREAMER_MATS[2 + k])
        n += 1
    # C3 the rush to D4 at 23:40: streamers trampled toward the door, a dropped bouquet, papers, a crushed cup
    # (all of it west of x -1300: the door's mouth, 90 deep, stays clear - check DOOR_MOUTH_BLOCKED)
    for k, (pts, mat) in enumerate(((((-1480, 3860), (-1420, 3880), (-1360, 3870), (-1310, 3895)), STREAMER_MATS[0]),
                                     (((-1500, 3940), (-1440, 3925), (-1380, 3945)), STREAMER_MATS[1]),
                                     (((-1460, 3990), (-1400, 4010), (-1350, 3985)), STREAMER_MATS[2]))):
        streamer(A, m, 'rush_streamer_%d' % k, pts, mat)
        n += 1
    B.prop(m, 'p7_foliage_flower_bouquet_glass_dead', (-1390.0, 3915.0, 0.0), angles=[88.0, -50.0, 0.0], layer='hall', id='rush_bouquet')
    for k, (x, y, mdl) in enumerate(((-1430.0, 3835.0, 'newspaper_single_fn_01'), (-1360.0, 3960.0, 'newspaper_single_fn_01'),
                                     (-1320.0, 3850.0, 'ma_cup_stack_single_dmg'), (-1470.0, 3995.0, 'cup_paper_open_iw6'))):
        B.prop(m, mdl, (x, y, 0.0), yaw=33.0 * k, layer='hall', id='rush_litter_%d' % k)
        n += 1
    A.REPORT['hall']['new_year_pieces'] = n + 2


def abandonment(A, m):
    """a year of dust and damp is painted into the surfaces now (AC1): the floor's wear mask and the walls' foot are layers of stock blend materials
    (hall_body), the damaged tile courses are hall_body's patches; no decal quad is placed here any more"""
    A.REPORT.setdefault('hall', {})['stains'] = 0


def fronts_by_models(A, m):
    """bulb strips under every fascia (emissive models: no light record), and one pool of the shop's own colour on the tile outside its front"""
    m.use('hall')
    n = 0
    z0 = A.FASCIA[0]
    for name, (x0, x1) in A.UNITS.items():
        if name == 'needle_drop':          # its marquee: the two bulb-strip fixtures with their lights (round 1)
            pass
        else:
            k = int((x1 - x0 - 40.0) // 104.0)
            start = (x0 + x1) / 2 - 104.0 * (k - 1) / 2
            for j in range(k):
                B.prop(m, 'cp_disco_bulb_strip_01', (start + 104.0 * j, A.FASCIA[2], z0 - 2.0), yaw=270.0, layer='hall', id='bulbs_%s_%d' % (name, j),
                       emissive={'color': [1.0, 0.82, 0.55], 'strength': 1.6})
                n += 1
        rgb, inten, rad, z = POOL[name]
        cx = (x0 + x1) / 2
        # L1 (28 Nov): a key light (engine direct, baked bounce). 32 in front of the fascia's face and just under it, a 45-degree cone: at 14 off the
        # front with a 60-degree cone the engine light hit the shutter housing 20 units away and clipped (E1 x3)
        org = (cx, A.FASCIA[2] - 32.0, z)
        d = (0.0, 4170.0 - org[1], -org[2])
        ln = math.sqrt(sum(c * c for c in d))
        A.lamp(m, 'light_pool_%s' % name, org, name, key=True, color=rgb, radius=rad, intensity=inten, type='spot', dir=[round(c / ln, 4) for c in d], inner=25.0, outer=45.0)
    A.REPORT.setdefault('hall', {})['bulb_strips'] = n
