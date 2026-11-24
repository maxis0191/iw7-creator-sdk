"""arcade_dress: the dressing and the light of the Underpass Arcade (round 1). Called by arcade.build_arcade after the geometry and the gameplay.

Everything here is data driven: `Dresser.put` places a model by the centre of its bounds, refuses what leaves its room, stands in a keep-clear rectangle (the two lanes,
the gameplay clearances, the path through every bay, camera eyes) or overlaps a floor prop already placed. A model of another zone than cp_zmb is placed only when
`FOREIGN` is true (one switch); every placement is counted so the report can say how many props of which zone there are.
"""
import math
import os
import random
import sys

from studio import build as B, prefab as P, answers

FOREIGN = os.environ.get('ARC_FOREIGN', '1') != '0'
PROP_CAP, LIGHT_CAP = 760, 52
MODELS_TXT = r'C:\studio-data\sz\arcade\r1\models.txt'

HUE = {'photo': (0.10, 0.85, 1.00), 'heel': (1.00, 0.52, 0.08), 'hole9': (1.00, 0.22, 0.68), 'copy': (0.22, 0.42, 1.00), 'needle': (1.00, 0.14, 0.18)}
TUBE = {'photo': 'w/metal_light_line_lightblue_03', 'heel': 'w/zmb_neon_orange', 'hole9': 'w/zmb_neon_pink', 'copy': 'w/plastic_wall_panel_light_02_on_blue', 'needle': 'w/plastic_wall_panel_light_02_on_red'}
SIGN = {'photo': 'sign_zombies_cosmic_cinema_on', 'heel': 'sign_zombies_octonian_pitstop_on', 'hole9': 'sign_zombies_crater_cakes_on', 'copy': 'sign_zombies_moon_shakes_on', 'needle': 'sign_cosmic_tunes_on'}
SIGN_OFF = ['sign_zombies_cosmic_cinema', 'sign_cosmic_tunes', 'sign_zombies_crater_cakes', 'sign_zombies_octonian_pitstop']

_zones = {}


def zones_of(model):
    if not _zones:
        for ln in open(MODELS_TXT):
            n, _, z = ln.strip().partition(' ')
            _zones[n] = set(z.split(','))
    return _zones.get(model, set())


class Dresser:
    def __init__(self, A, m):
        self.A, self.m = A, m
        self.n = 0
        self.ids = 0
        self.boxes = []                  # bounding boxes (x0, y0, x1, y1) of the floor props placed
        self.rooms = []                  # rooms a prop may stand in (x0, y0, x1, y1)
        self.keep = []                   # rectangles that stay free
        self.tops = {}                   # tag -> (x, y, top z, w, d, yaw)
        self.foreign = {}
        self.skipped = {'room': 0, 'keep': 0, 'overlap': 0, 'zone': 0}
        self.failed = []
        self.rng = random.Random(1978)

    # -------------------------------------------------------------------------------------------- one prop
    def bounds(self, model):
        return P._model_bounds(model)

    def box_of(self, model, cx, cy, yaw, scale=1.0):
        mn, mx = self.bounds(model)
        a = math.radians(yaw)
        ca, sa = math.cos(a), math.sin(a)
        xs, ys = [], []
        for px in (mn[0], mx[0]):
            for py in (mn[1], mx[1]):
                xs.append(cx + (px * ca - py * sa) * scale)
                ys.append(cy + (px * sa + py * ca) * scale)
        return min(xs), min(ys), max(xs), max(ys)

    def put(self, model, x, y, yaw=0.0, z=0.0, tag=None, scale=1.0, emissive=None, alt=None, clip='auto', on=None, margin=1.0, ignore_keep=False, zone='arcade', slide=None, reach=48.0):
        """a prop whose bounds' centre is (x, y) and whose bottom is z (default the floor), turned by yaw. on=<tag>: stands on top of that prop (z = its top). slide='x'|'y': when the
        place is refused, tries the same line at offsets up to `reach` units. Returns the record or None."""
        offs = [0.0]
        if slide:
            k = 6.0
            while k <= reach:
                offs += [k, -k]
                k += 6.0
        why = None
        for o in offs:
            xx, yy = (x + o, y) if slide == 'x' else (x, y + o) if slide == 'y' else (x, y)
            rec, why = self._put(model, xx, yy, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone)
            if rec:
                return rec
            if why in ('cap', 'zone'):
                break
        if why not in ('cap', 'zone'):
            self.skipped[why] += 1
            self.failed.append((tag or model, why, [round(x), round(y)]))
        return None

    def _put(self, model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone):
        if self.n >= PROP_CAP:
            return None, 'cap'
        zs = zones_of(model)
        if not zs:
            self.skipped['zone'] += 1
            return None, 'zone'
        if 'cp_zmb' not in zs and not FOREIGN:
            if alt and 'cp_zmb' in zones_of(alt):
                model = alt
                zs = zones_of(model)
            else:
                self.skipped['zone'] += 1
                return None, 'zone'
        mn, mx = self.bounds(model)
        c = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0)
        a = math.radians(yaw)
        ox = x - (c[0] * math.cos(a) - c[1] * math.sin(a)) * scale
        oy = y - (c[0] * math.sin(a) + c[1] * math.cos(a)) * scale
        if on:
            if on not in self.tops:
                return None, 'room'
            z = self.tops[on][2]
        oz = z - mn[2] * scale
        bx = self.box_of(model, ox, oy, yaw, scale)
        floor_level = on is None and z < 72.0
        if not on:
            if not any(r[0] - 0.5 <= bx[0] and bx[2] <= r[2] + 0.5 and r[1] - 0.5 <= bx[1] and bx[3] <= r[3] + 0.5 for r in self.rooms):
                return None, 'room'
        if floor_level and not ignore_keep:
            for k in self.keep:
                if bx[0] < k[2] and bx[2] > k[0] and bx[1] < k[3] and bx[3] > k[1]:
                    return None, 'keep'
            for o in self.boxes:
                if bx[0] < o[2] + margin and bx[2] > o[0] - margin and bx[1] < o[3] + margin and bx[3] > o[1] - margin:
                    return None, 'overlap'
        w, d, h = (mx[0] - mn[0]) * scale, (mx[1] - mn[1]) * scale, (mx[2] - mn[2]) * scale
        cb = None
        if clip == 'auto' and floor_level and z < 4.0 and max(w, d) >= 24.0 and h >= 24.0 and min(w, d) >= 6.0:
            cb = [mn[0] * scale, mn[1] * scale, mn[2] * scale, mx[0] * scale, mx[1] * scale, mx[2] * scale]
        elif isinstance(clip, (list, tuple)):
            cb = list(clip)
        self.ids += 1
        self.m.use('dressing')
        B.prop(self.m, model, (round(ox, 2), round(oy, 2), round(oz, 2)), yaw=yaw, scale=scale, clip=cb, zone=zone, emissive=emissive, id='p%03d_%s' % (self.ids, tag or model[:18]))
        self.n += 1
        if floor_level:
            self.boxes.append(bx)
        top = z + h
        rec = {'x': x, 'y': y, 'top': top, 'box': bx, 'model': model}
        if tag:
            self.tops[tag] = (x, y, top, w, d, yaw)
        for zz in zs:
            if zz != 'cp_zmb' and 'cp_zmb' not in zs:
                self.foreign[model] = sorted(zs)
        return rec, None

    def on(self, base, model, du=0.0, dv=0.0, yaw=0.0, tag=None, scale=1.0):
        """a small prop on top of a placed prop (offset from its centre)"""
        if base not in self.tops:
            return None
        bxc, byc = self.tops[base][0], self.tops[base][1]
        return self.put(model, bxc + du, byc + dv, yaw, tag=tag, scale=scale, on=base)

    def wall(self, model, side, along, z=0.0, tag=None, inset=1.5, scale=1.0, **kw):
        """flush against a wall: side 's' (south wall of the corridor, face north), 'n' (north wall), 'w'/'e' (end walls) or a ('y', value, facing) wall of a bay
        ('bay', y of the wall face, +1 / -1 normal along y). Local x is the model's front, local y its width."""
        A = self.A
        mn, mx = self.bounds(model)
        ex, ey = (mx[0] - mn[0]) * scale, (mx[1] - mn[1]) * scale
        turn = 0.0
        depth = ex
        if ey < 0.8 * ex:                      # a long thin model (a table, a console): its y is the depth, its y axis the front
            turn, depth = -90.0, ey
        # the bounds' centre sits depth/2 + (the model's back at -mn[0]) from the wall: the model's local x = 0 is its back in most stock props
        off = inset + depth / 2.0
        kw.setdefault('slide', 'x' if (isinstance(side, str) and side in ('s', 'n')) or (isinstance(side, tuple)) else 'y')
        if kw.get('ignore_keep'):
            kw['slide'] = None
        if side == 's':
            return self.put(model, along, A.Y0 + A.WT + off, 90.0 + turn, z, tag, scale, **kw)
        if side == 'n':
            return self.put(model, along, A.Y1 - A.WT - off, 270.0 + turn, z, tag, scale, **kw)
        if side == 'w':
            return self.put(model, A.X0 + A.WT + off, along, 0.0 + turn, z, tag, scale, **kw)
        if side == 'e':
            return self.put(model, A.X1 - A.WT - off, along, 180.0 + turn, z, tag, scale, **kw)
        if isinstance(side, tuple):                       # ('y', wall face y, normal +1 north / -1 south) of a bay partition or back wall
            _, yw, nrm = side
            return self.put(model, along, yw + nrm * off, (90.0 if nrm > 0 else 270.0) + turn, z, tag, scale, **kw)
        if isinstance(side, list):                        # ['x', wall face x, normal +1 east / -1 west]
            _, xw, nrm = side
            return self.put(model, xw + nrm * off, along, (0.0 if nrm > 0 else 180.0) + turn, z, tag, scale, **kw)
        raise ValueError(side)


# ------------------------------------------------------------------------------------------------ what a bay holds, in bay coordinates u (x - bay start), v (y - 4300)
def bay_geometry_extras(A, m, i):
    """the render only dressing of a bay: the shutter half up above the aperture, the neon tube round the aperture, the wall bands, a counter top"""
    m.use('dressing')
    a0, a1 = A.aperture(i)
    yw = A.Y1 - A.WT
    # roller shutter drawn half up above the aperture: the curtain z 150..198 in two thirds of the opening's width, the coil box above it, guide rails at the sides
    B.box(m, [a0 - 6.0, yw - 8.0, A.AP_H, a1 + 6.0, yw - 2.0, A.AP_H + 6.0], 'w/metal_painted_01_black', mode='render', id='shutter_frame_%d' % (i + 1))
    B.box(m, [a0, yw - 7.0, 152.0, a1, yw - 4.0, 200.0], A.SHUTTER, mode='render', id='shutter_curtain_%d' % (i + 1))
    B.box(m, [a0 - 4.0, yw - 11.0, 198.0, a1 + 4.0, yw - 1.0, 214.0], 'w/metal_painted_02_dark', mode='render', id='shutter_coil_%d' % (i + 1))
    B.box(m, [a0 - 6.0, yw - 8.0, 0.0, a0 - 2.0, yw - 2.0, A.AP_H], 'w/metal_painted_01_black', mode='render', id='rail_l_%d' % (i + 1))
    B.box(m, [a1 + 2.0, yw - 8.0, 0.0, a1 + 6.0, yw - 2.0, A.AP_H], 'w/metal_painted_01_black', mode='render', id='rail_r_%d' % (i + 1))
    # neon tube round the aperture (a lit line in the shop's hue)
    t = TUBE[A.BAYS[i]]
    B.box(m, [a0 - 10.0, yw - 3.0, A.AP_H - 6.0, a1 + 10.0, yw, A.AP_H - 2.0], t, mode='render', id='tube_top_%d' % (i + 1))
    B.box(m, [a0 - 10.0, yw - 3.0, 0.0, a0 - 6.0, yw, A.AP_H - 6.0], t, mode='render', id='tube_l_%d' % (i + 1))
    B.box(m, [a1 + 6.0, yw - 3.0, 0.0, a1 + 10.0, yw, A.AP_H - 6.0], t, mode='render', id='tube_r_%d' % (i + 1))
    # a dark wainscot round the inside of the bay
    s = A.BAY_X[i]
    for k, bx in enumerate(([s + A.WT, A.Y1 + A.WT, 0.0, s + A.WT + 3.0, A.Y1 + A.BAY_D - A.WT, 42.0], [s + A.BAY_W - A.WT - 3.0, A.Y1 + A.WT, 0.0, s + A.BAY_W - A.WT, A.Y1 + A.BAY_D - A.WT, 42.0])):
        B.box(m, bx, 'w/wood_trim_wall_01', mode='render', id='wain_%d_%d' % (i + 1, k))
    B.box(m, [s + A.WT, A.BACK_Y - 3.0, 0.0, s + A.BAY_W - A.WT, A.BACK_Y, 42.0], 'w/wood_trim_wall_01', mode='render', id='wain_p_%d' % (i + 1))


def corridor_geometry(A, m):
    """floor pattern, panel grid, shop fronts of the south wall, D4 and D7, mats"""
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    # floor: a brown and orange checker of 96 squares over the brown base (render only, 1 proud)
    k = 0
    xs = [cx0 + 96.0 * i for i in range(int((cx1 - cx0) // 96.0) + 1)]
    ys = [cy0 + 96.0 * j for j in range(int((cy1 - cy0) // 96.0) + 1)]
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if (i + j) % 2:
                B.box(m, [x, y, 0.0, min(x + 96.0, cx1), min(y + 96.0, cy1), 1.0], 'w/plastic_slick_floor_01_orange', mode='render', id='tile_%d' % k)
                k += 1
    # the wall band: wainscot and a dark base, both walls
    B.box(m, [cx0, cy0, 0.0, cx1, cy0 + 2.0, 44.0], 'w/wood_trim_wall_01', mode='render', id='wain_s')
    B.box(m, [cx0, cy1 - 2.0, 0.0, cx1, cy1, 44.0], 'w/wood_trim_wall_01', mode='render', id='wain_n')
    # the ceiling panel grid: z 178..182 under the dark ceiling at 256; half of the panels are dead; five rows
    rng = random.Random(7)
    A.live = []
    rows = [3590.0, 3745.0, 3900.0, 4055.0, 4210.0]
    cols = [A.X0 + 100.0 + 118.0 * i for i in range(15)]
    n = 0
    for ri, y in enumerate(rows):
        for ci, x in enumerate(cols):
            live = rng.random() < 0.45
            B.box(m, [x - 40.0, y - 14.0, 178.0, x + 40.0, y + 14.0, 182.0], A.PANEL_LIVE if live else A.PANEL_DEAD, mode='render', id='panel_%d_%d' % (ri, ci))
            if live:
                A.live.append((x, y))
            n += 1
        B.box(m, [cx0, y - 18.0, 183.0, cx1, y - 15.0, 188.0], 'w/metal_painted_02_dark', mode='render', id='panel_rail_a_%d' % ri)
        B.box(m, [cx0, y + 15.0, 183.0, cx1, y + 18.0, 188.0], 'w/metal_painted_02_dark', mode='render', id='panel_rail_b_%d' % ri)
    A.panels = n
    # shop fronts of the south wall, shutters down (render only boxes proud of the wall) and their headers
    for k, (x0, x1) in enumerate(((-2480.0, -2220.0), (-1790.0, -1500.0), (-1470.0, -1290.0))):
        yv = cy0
        B.box(m, [x0 - 6.0, yv, 0.0, x1 + 6.0, yv + 5.0, 128.0], 'w/metal_painted_01_black', mode='render', id='front_frame_%d' % k)
        B.box(m, [x0, yv + 5.0, 0.0, x1, yv + 8.0, 122.0], SHUT[k % len(SHUT)], mode='render', id='front_shutter_%d' % k)
        B.box(m, [x0 - 6.0, yv, 128.0, x1 + 6.0, yv + 9.0, 160.0], ('w/plaster_wall_01_brown', 'w/plaster_wall_01_orange', 'w/plaster_wall_04_beige')[k], mode='render', id='front_header_%d' % k)
    # D4: the frame of the doorway in the east wall, hazard stripe
    B.box(m, [cx1 - 4.0, A.DOOR_Y0 - 8.0, 0.0, cx1, A.DOOR_Y0, A.DOOR_Z + 8.0], 'w/metal_painted_01_black', mode='render', id='d4_frame_l')
    B.box(m, [cx1 - 4.0, A.DOOR_Y1, 0.0, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0], 'w/metal_painted_01_black', mode='render', id='d4_frame_r')
    B.box(m, [cx1 - 4.0, A.DOOR_Y0 - 8.0, A.DOOR_Z, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0], 'w/metal_painted_01_black', mode='render', id='d4_frame_t')
    B.box(m, [cx1 - 8.0, A.DOOR_Y0, A.DOOR_Z - 20.0, cx1 - 4.0, A.DOOR_Y1, A.DOOR_Z - 4.0], 'w/paint_lines_01_thick_yellow_clean', mode='render', id='d4_stripe')
    # D7: a closed blast door, half wound: the slab to 128, the coil above it, two lamps
    xw = cx0
    B.box(m, [xw, 3790.0, 0.0, xw + 4.0, 4010.0, 190.0], 'w/metal_painted_01_black', mode='render', id='d7_frame')
    B.box(m, [xw + 4.0, 3800.0, 0.0, xw + 8.0, 4000.0, 128.0], 'w/metal_door_panels_black_01', mode='render', id='d7_slab')
    B.box(m, [xw + 4.0, 3800.0, 128.0, xw + 9.0, 4000.0, 140.0], 'w/paint_lines_01_thick_yellow_clean', mode='render', id='d7_hazard')
    B.box(m, [xw + 4.0, 3796.0, 146.0, xw + 20.0, 4004.0, 176.0], 'w/metal_painted_02_dark', mode='render', id='d7_coil')
    B.box(m, [xw + 4.0, 3860.0, 56.0, xw + 9.0, 3940.0, 96.0], 'w/signage_caution_stripe_rvl_01' if False else 'w/signage_sign_caution_stripe_rvl_01', mode='render', id='d7_warn')
    # mats in front of every aperture and the carpet runner of the centre
    for i in range(A.BAYS.__len__()):
        a0, a1 = A.aperture(i)
        B.box(m, [a0, cy1 - 52.0, 0.0, a1, cy1, 1.4], 'w/fac_rubber_mat_black', mode='render', id='mat_%d' % (i + 1))
    for i in range(5):
        bay_geometry_extras(A, m, i)
    # the vestibule's floor mat
    B.box(m, [A.X1 + A.WT, 3870.0, 0.0, A.X1 + 200.0 - A.WT, 3930.0, 1.2], 'w/fac_rubber_mat_black', mode='render', id='vest_mat')


SHUT = ['w/door_metal_rollup_grey_large_01', 'w/cp_disco_metal_door_rollup_01', 'w/cp_disco_metal_door_rollup_01_green']


# ------------------------------------------------------------------------------------------------ content
def setup_rooms(A, D):
    D.rooms.append((A.X0 + A.WT, A.Y0 + A.WT, A.X1 - A.WT, A.Y1 - A.WT))
    for i in range(5):
        s = A.BAY_X[i]
        D.rooms.append((s + A.WT, A.Y1 + A.WT, s + A.BAY_W - A.WT, A.BACK_Y))
        D.rooms.append((s + A.WT, A.BACK_Y + 12.0, s + A.BAY_W - A.WT, A.Y1 + A.BAY_D - A.WT))
    D.rooms.append((A.X1 + A.WT, 3796.0, A.X1 + 200.0 - A.WT, 4004.0))
    # keep free: the two lanes, the shop apertures' fronts, the D4 and D7 approaches, the path through every bay
    D.keep.append((A.X0, 3590.0, A.X1, 3700.0))
    D.keep.append((A.X0, 4130.0, A.X1, 4240.0))
    for i in range(5):
        a0, a1 = A.aperture(i)
        s = A.BAY_X[i]
        D.keep.append((a0, 4240.0, a1, A.Y1 + 20.0))
        D.keep.append((s + 120.0, A.Y1, s + 200.0, A.BACK_Y + 30.0))
    D.keep.append((A.X1 - 200.0, 3780.0, A.X1 - 16.0, 4020.0))
    D.keep.append((A.X0, 3780.0, A.X0 + 80.0, 4020.0))
    for r in answers.clearance_rows(D.m):
        b = r['box']
        D.keep.append((b[0] - 4.0, b[1] - 4.0, b[3] + 4.0, b[4] + 4.0))
    for c in D.m.flat().cameras:
        x, y = c['origin'][0], c['origin'][1]
        D.keep.append((x - 52.0, y - 52.0, x + 52.0, y + 52.0))


def south_wall(A, D):
    P_ = D.put
    # vending along the west part of the south wall, then the row of pay phones
    for k, (mod, x) in enumerate((('park_soda_machine', -2955.0), ('cp_town_soda_machine_01', -2915.0), ('zmb_fortune_teller_machine_on', -2878.0), ('park_token_machine', -2842.0),
                                  ('zmb_souvenir_station_on', -2802.0))):
        D.wall(mod, 's', x, tag='vend%d' % k, alt='park_soda_machine')
    for k in range(4):
        D.wall('street_telephone_booth_old_iw6', 's', -2745.0 + 32.0 * k, tag='phone%d' % k, alt='zmb_atm_machine_on')
    D.wall('zmb_atm_machine_on', 's', -2640.0, tag='atm')
    # poster cases and posters between the shop fronts
    xs = (-2190.0, -2140.0, -2090.0, -2040.0, -1990.0)
    for k, x in enumerate(xs):
        D.wall('greece_display_cases_11', 's', x, tag='pcase%d' % k)
        D.wall('zmb_poster_coming_soon' if k % 2 else 'zmb_poster_now_playing_01', 's', x, z=96.0 + (k % 2) * 6.0, tag='post%d' % k, ignore_keep=True)
    for k, x in enumerate((-2440.0, -2380.0, -2320.0, -2260.0)):             # sale boards on the shutters of the blank fronts
        D.wall('zmb_poster_now_playing_01', 's', x, z=58.0, tag='sale%d' % k, ignore_keep=True)
    D.wall('sign_clock_04', 's', -2100.0, z=190.0, tag='clock_s', ignore_keep=True)
    D.wall('beacon_light_plasticcase_red_on', 's', -2005.0, z=150.0, tag='alarm_s', ignore_keep=True)
    # benches, bins and plants against the wall
    D.wall('furniture_park_bench_01_red', 's', -1700.0, tag='bench_s1', yaw_fix=None) if False else D.wall('furniture_park_bench_01_red', 's', -1700.0, tag='bench_s1')
    D.wall('fac_trash_bin', 's', -1740.0, tag='bin_s1')
    D.wall('plant_potted_palm_01', 's', -1625.0, tag='palm_s1')
    D.wall('com_trashbin_sml', 's', -1460.0, tag='bin_s2')
    D.wall('park_soda_machine', 's', -1425.0, tag='vend_e1')
    D.wall('soda_machine_zmb', 's', -1390.0, tag='vend_e2')
    for k, x in enumerate((-1330.0, -1290.0, -1250.0)):
        D.wall('park_token_machine' if k != 1 else 'zmb_fortune_teller_machine_on', 's', x, tag='vend_e%d' % (k + 3))
    # dead shop signs over the blank fronts
    for k, (mod, x) in enumerate((('sign_cosmic_tunes', -2350.0), ('sign_zombies_crater_cakes', -1645.0))):
        D.wall(mod, 's', x, z=165.0, tag='deadsign%d' % k, ignore_keep=True)
    D.wall('sign_zombies_cosmic_cinema', 's', -1380.0, z=165.0, tag='deadsign2', ignore_keep=True)
    # litter at the foot of the wall
    for k in range(10):
        x = A.X0 + 40.0 + D.rng.random() * 1650.0
        D.put(D.rng.choice(('com_trashbag2_black', 'com_trashbag2_green', 'food_trash_bag_candy_01', 'food_trash_bag_chips_01', 'cup_paper_open_iw6')), x, A.Y0 + A.WT + 14.0 + D.rng.random() * 30.0,
              D.rng.random() * 360.0, tag='lit_s%d' % k)


def north_piers(A, D):
    piers = [(-2984.0, -2916.0), (-2684.0, -2586.0), (-2354.0, -2256.0), (-2024.0, -1926.0), (-1694.0, -1596.0), (-1364.0, -1216.0)]
    for k, (a, b) in enumerate(piers):
        mid = (a + b) / 2.0
        w = b - a
        D.wall('zmb_poster_coming_soon' if k % 2 else 'zmb_poster_now_playing_01', 'n', mid, z=100.0, tag='pier_post%d' % k, ignore_keep=True)
        if w >= 90.0:
            D.wall(('furniture_park_bench_01_blue', 'furniture_park_bench_01_yellow', 'furniture_park_bench_01_red', 'furniture_park_bench_01_blue', 'furniture_park_bench_01_yellow')[k % 5], 'n', mid, tag='pier_bench%d' % k)
        if k in (0, 2, 4):
            D.wall('fac_trash_bin', 'n', a + 10.0, tag='pier_bin%d' % k)
        D.wall('misc_wall_mounted_loudspeaker_01', 'n', mid, z=196.0, tag='pier_spk%d' % k, ignore_keep=True)
    D.wall('sign_clock_04', 'n', -1290.0, z=200.0, tag='clock_n', ignore_keep=True)
    D.wall('zmb_drinking_fountain_01', 'n', -1330.0, z=26.0, tag='fountain', ignore_keep=True)
    D.wall('plant_potted_palm_01', 'n', -2960.0, tag='palm_n0')
    D.wall('com_potted_plant_small_des', 'n', -1235.0, tag='plant_n5')


def center_band(A, D):
    # the floor polisher left in the corridor with its bucket and mop and a wet floor sign
    D.put('cp_disco_floor_buffer', -2780.0, 3760.0, 25.0, tag='buffer')
    D.put('com_janitor_bucket_mop_iw6', -2735.0, 3735.0, 80.0, tag='mop')
    D.put('cart_janitor_plastic_bucket', -2812.0, 3735.0, 10.0, tag='bucket2')
    D.put('com_trashbag2_black', -2830.0, 3790.0, 40.0, tag='bag_a')
    # bench pairs with a bin and a palm between them, two of them
    for k, x in enumerate((-2540.0, -2090.0, -1700.0)):
        D.put('furniture_park_bench_01_blue' if k != 1 else 'furniture_park_bench_01_red', x, 3830.0, 0.0, tag='bench_c%da' % k)
        D.put('furniture_park_bench_01_yellow' if k != 1 else 'furniture_park_bench_01_blue', x, 3935.0, 180.0, tag='bench_c%db' % k)
        D.put('plant_potted_palm_01', x - 40.0, 3885.0, 0.0, tag='palm_c%d' % k)
        D.put('fac_trash_bin', x + 40.0, 3885.0, 0.0, tag='bin_c%d' % k)
        D.put('trashbin_01_iw6_green', x + 26.0, 3900.0, 0.0, tag='bin2_c%d' % k)
        for j in range(3):
            D.put(D.rng.choice(('magazines_01_newspaper_stack', 'com_magazine_english_stack_04', 'cup_paper_open_iw6', 'food_trash_bag_candy_01')), x + (j - 1) * 12.0, 3830.0 if j != 1 else 3935.0, D.rng.random() * 360.0,
                  on='bench_c%d%s' % (k, 'a' if j != 1 else 'b'), tag=None)
    # kiosks: a vending cart, a concessions cart with its umbrella, a lost and found desk
    D.put('park_vending_push_cart_proto', -2330.0, 3790.0, 90.0, tag='kiosk1')
    D.put('park_concessions_cart_proto', -1900.0, 3795.0, 0.0, tag='kiosk2')
    D.put('zmb_ticket_cart_sign', -1900.0, 3840.0, 0.0, z=46.0, tag='kiosk2_sign', ignore_keep=True)
    D.put('park_concessions_cart_umbrella_closed', -1880.0, 3740.0, 0.0, tag='umb', ignore_keep=False)
    D.put('lab_desk_02', -1480.0, 4090.0, 90.0, tag='desk_lf')
    D.put('cp_town_desk_phone_01_black', -1480.0, 4075.0, 20.0, on='desk_lf', tag='desk_phone')
    D.put('park_cash_register', -1480.0, 4110.0, 270.0, on='desk_lf', tag='desk_reg')
    D.put('zmb_fortune_teller_machine_on', -1560.0, 4100.0, 180.0, tag='ft1')
    D.put('park_token_machine', -1600.0, 4100.0, 180.0, tag='tk1')
    D.put('zmb_spaceland_planter_01', -2380.0, 4060.0, 0.0, tag='planter1', slide='x')
    D.on('planter1', 'plant_potted_palm_01', 0.0, 0.0)
    D.put('zmb_spaceland_planter_01', -1330.0, 3745.0, 0.0, tag='planter2', slide='x')
    D.on('planter2', 'com_potted_plant_small_des', 0.0, 0.0)
    D.put('park_air_hockey_table', -2700.0, 4075.0, 90.0, tag='hockey')


def bay(A, D, i):
    s = A.BAY_X[i]
    yb = A.Y1
    yp = A.BACK_Y
    kind = A.BAYS[i]
    hue = HUE[kind]
    wallb = A.Y1 + A.BAY_D - A.WT          # the back wall's face
    U = lambda u: s + u
    V = lambda v: yb + v
    part = ('y', yp, -1)                    # the partition's shop side, normal south
    back = ('y', wallb, -1)
    lw = ['x', s + A.WT, 1]
    rw = ['x', s + A.BAY_W - A.WT, -1]
    W = D.wall
    if kind == 'photo':
        # bay 1: the photo booth corner. The perk machine stands at the left wall; two booths against the partition on the right, a bench and a vending corner
        W('cp_disco_street_telephone_booth', part, U(236.0), tag='booth1')
        W('cp_disco_street_telephone_booth', part, U(270.0), tag='booth2')
        W('furniture_park_bench_01_blue', rw, V(70.0), tag='bench1')
        D.on('bench1', 'com_magazine_english_stack_04', 0.0, -22.0, 30.0)
        D.on('bench1', 'cup_paper_open_iw6', 0.0, 18.0)
        W('bike_shop_clothing_table_01', part, U(60.0), tag='tab1')
        D.on('tab1', 'zmb_tv_crt_01', 0.0, 0.0, 180.0)
        D.on('tab1', 'magazines_01_newspaper_stack', 22.0, 0.0)
        W('park_token_machine', lw, V(36.0), tag='tok1')
        W('cp_town_soda_machine_01', rw, V(140.0), tag='souv1')
        for k, (mdl, u) in enumerate((('zmb_poster_coming_soon', 40.0), ('zmb_poster_now_playing_01', 84.0), ('zmb_poster_coming_soon', 250.0))):
            W(mdl, part, U(u), z=104.0, tag='pp%d' % k, ignore_keep=True)
        for k in range(6):                                    # strips of photos pinned on the right wall above the bench
            W('newspaper_single_fn_01', rw, V(50.0 + 12.0 * k), z=96.0 + 5.0 * (k % 3), tag='strip%d' % k, ignore_keep=True)
    elif kind == 'heel':
        W('mp_dart_workbench_01', part, U(64.0), tag='bench_h')
        W('mp_dart_workbench_01', part, U(256.0), tag='bench_h2')
        for k, dv in enumerate((-26.0, 0.0, 26.0)):
            D.on('bench_h', 'p7_54i_gear_shoes', dv, 0.0, 40.0 * k)
        D.on('bench_h', 'dns_toolbox_small_iw6', -34.0, 6.0)
        D.on('bench_h', 'dns_tool_hammer01_iw6', 34.0, -6.0, 30.0)
        D.on('bench_h2', 'park_cash_register', -20.0, 0.0, 270.0)
        D.on('bench_h2', 'cp_town_desk_phone_01_black', 22.0, 0.0, 270.0)
        D.on('bench_h2', 'dns_tool_pliers01_iw6', 0.0, 8.0, 70.0)
        D.on('bench_h2', 'cp_disco_subway_locker_key', 34.0, -4.0)
        D.on('bench_h2', 'com_padlock', -34.0, -4.0)
        for k in range(12):                                   # key hooks on the partition above the benches
            W('cp_rave_tiki_key_hook_01', part, U((24.0 + 12.0 * k) if k < 6 else (222.0 + 12.0 * (k - 6))), z=112.0, tag='hook%d' % k, ignore_keep=True)
        for k, z in enumerate((74.0, 94.0)):
            W('fixture_greece_wood_shelf_01', part, U(64.0), z=z, tag='shelfA%d' % k, ignore_keep=True)
            W('fixture_greece_wood_shelf_01', part, U(256.0), z=z, tag='shelfB%d' % k, ignore_keep=True)
        W('ac_prs_imp_com_clothing_rack_1', lw, V(66.0), tag='shoerack')
        W('bike_shop_clothing_table_01', rw, V(66.0), tag='shoetable')
        for k, dv in enumerate((-20.0, 0.0, 20.0)):
            D.on('shoetable', 'p7_54i_gear_shoes', 0.0, dv, 20.0 * k)
        W('chair_folding_iw6', rw, V(130.0), tag='chair_h')
        D.put('neon_open_sign_on_02', U(160.0), A.Y1 + 22.0, 270.0, z=100.0, tag='open_h', ignore_keep=True, emissive={'color': list(hue), 'strength': 1.2})
    elif kind == 'hole9':
        W('cp_town_market_delicounter', part, U(64.0), scale=0.45, tag='counterL')
        W('cp_town_market_delicounter', part, U(256.0), scale=0.45, tag='counterR')
        for k, x in enumerate((40.0, 64.0, 88.0)):
            D.put('stool_bar_padded_01_green', U(x), V(122.0), 0.0, tag='stoolL%d' % k)
            D.put('stool_bar_padded_01_green', U(x + 192.0), V(122.0), 0.0, tag='stoolR%d' % k)
        D.on('counterL', 'misc_coffee_machine', -20.0, 0.0, 270.0)
        D.on('counterL', 'misc_coffee_machine_pot', 8.0, 0.0)
        D.on('counterL', 'container_coffee_mug_group_01', 28.0, 0.0, 90.0)
        D.on('counterR', 'park_cash_register', 28.0, 0.0, 270.0)
        for k, du in enumerate((-30.0, -16.0, -2.0, 12.0)):
            D.on('counterR', 'food_snacks_iw6_donutsstack01', du, 0.0)
        D.on('counterR', 'com_food_snacks_iw6_donuts_shortstack', -36.0, 0.0)
        W('greece_display_cases_08', rw, V(60.0), tag='case9')
        for k, u in enumerate((28.0, 100.0, 242.0, 292.0)):
            W('p7_cafe_wall_menu_01', part, U(u), z=112.0, tag='menu%d' % k, ignore_keep=True)
        W('table_diner_booth_01', lw, V(60.0), tag='booth9a')
        D.put('chair_folding_wood', U(60.0), V(40.0), 0.0, tag='ch9a')
        D.on('booth9a', 'p7_diner_table_napkin_clean', 0.0, 0.0)
        D.put('ma_cup_stack', U(236.0), V(40.0), 0.0, tag='cups9')
    elif kind == 'copy':
        W('cp_town_punchcard_computer_console', part, U(40.0), tag='cop1')
        W('cp_town_chem_lab_computer_01', part, U(88.0), tag='cop2')
        W('equipment_old_computer', part, U(232.0), tag='cop3')
        W('cp_town_punchcard_computer_console', part, U(276.0), tag='cop4')
        W('lab_desk_02', rw, V(70.0), tag='bp_desk')
        D.on('bp_desk', 'cp_town_blueprint_hypnosis_roll', 0.0, -26.0)
        D.on('bp_desk', 'cp_town_blueprint_teleporter_roll', 0.0, 0.0)
        D.on('bp_desk', 'cp_town_blueprint_mind_control_roll', 0.0, 26.0)
        W('cp_town_blueprint_hypnosis', part, U(64.0), z=104.0, tag='bp1', ignore_keep=True)
        W('cp_town_blueprint_mind_control', part, U(256.0), z=104.0, tag='bp2', ignore_keep=True)
        W('furniture_filing_cabinet', rw, V(130.0), tag='file1')
        W('com_filecabinetblackclosed', lw, V(30.0), tag='file2')
        D.put('com_copypaper_box', U(280.0), V(30.0), 20.0, tag='cbox1')
        D.on('cbox1', 'com_copypaper_box_open', 0.0, 0.0)
    else:  # needle
        W('cp_town_jukebox', rw, V(110.0), tag='juke')
        W('bike_shop_clothing_table_01', part, U(60.0), tag='rt0')
        W('bike_shop_clothing_table_01', part, U(256.0), tag='rt1')
        for k in range(4):
            D.on('rt0', 'cp_disco_record_milk_crate', -33.0 + 22.0 * k, 0.0)
        for k in range(3):
            D.on('rt1', 'cp_disco_record_milk_crate', -28.0 + 28.0 * k, 0.0)
        D.on('rt1', 'com_transistor_radio', 36.0, 0.0)
        W('cp_rave_turntable_01', lw, V(120.0), tag='tt')
        W('zmb_rave_boom_speaker_01', lw, V(40.0), tag='spk1')
        W('zmb_rave_boom_speaker_01', rw, V(40.0), tag='spk2')
        for k in range(6):
            D.put('cp_disco_record_milk_crate', U(30.0 + 22.0 * (k % 3)), V(70.0 + 24.0 * (k // 3)), D.rng.random() * 40.0, tag='crate%d' % k)
        for k in range(10):
            W('cp_disco_record_sleeve_01' if k % 2 else 'cp_disco_record_sleeve_02', part, U(20.0 + 14.0 * k if k < 5 else 228.0 + 14.0 * (k - 5)), z=104.0 + 14.0 * (k % 2), tag='slv%d' % k, ignore_keep=True)
        W('com_restaurantstainlessteelshelf_02', rw, V(44.0), tag='rbin2')
        W('zmb_poster_coming_soon', lw, V(44.0), z=100.0, tag='np1', ignore_keep=True)
    # the back room: the darkest place of the arcade. The spawners stand at its two ends (their clearance is the tool's 48), its middle holds a shelf and crates
    W('com_restaurantstainlessteelshelf_02', back, U(160.0), tag='bshelf%d' % i)
    for k, (mdl, du, dv) in enumerate((('ammo_crate_01_dust', -26.0, 244.0), ('lag_soda_crate', 28.0, 244.0), ('com_trashbag2_black', -22.0, 214.0), ('com_copypaper_box_open', 26.0, 214.0))):
        D.put(mdl, U(160.0 + du), V(dv), D.rng.random() * 360.0, tag='bk%d_%d' % (i, k), slide='x', reach=12.0)
    D.put('lag_portable_radio', U(160.0), V(208.0), 200.0, tag='bk_radio%d' % i, slide='x', reach=30.0)


BAYZ = 200.0


def clutter(A, D, target):
    """floor litter and small things in the corridor's central band and the shops until `target` props"""
    pool_floor = ['com_debris_paper_iw6_01', 'com_debris_paper_iw6_02', 'newspaper_single_fn_01', 'cup_paper_open_iw6', 'food_trash_bag_candy_01', 'food_trash_bag_chips_01', 'ma_cup_stack',
                  'magazines_01_newspaper_stack', 'com_magazine_english_stack_04', 'base_book_stack_01a', 'p7_diner_table_napkin_clean', 'com_copypaper_box']
    regions = [(A.X0 + 30.0, 3700.0, A.X1 - 30.0, 4130.0)]
    for i in range(5):
        s = A.BAY_X[i]
        regions.append((s + 24.0, A.Y1 + 24.0, s + A.BAY_W - 24.0, A.BACK_Y - 8.0))
        regions.append((s + 24.0, A.BACK_Y + 20.0, s + A.BAY_W - 24.0, A.Y1 + A.BAY_D - 30.0))
    tries = 0
    while D.n < target and tries < 6000:
        tries += 1
        r = D.rng.choice(regions) if D.rng.random() < 0.55 else regions[0]
        x, y = D.rng.uniform(r[0], r[2]), D.rng.uniform(r[1], r[3])
        D.put(D.rng.choice(pool_floor), x, y, D.rng.uniform(0.0, 360.0), margin=3.0)


def ceiling_props(A, D):
    """pipes, ducts, hanging cables and bulbs above the panel grid, in the dark (z 200 to 250)"""
    pipes = ['pipe_metal_painted_straight_128_red', 'pipe_metal_painted_straight_128_blue', 'pipe_metal_painted_straight_128_gray', 'pipe_metal_painted_straight_128']
    k = 0
    for line, y in enumerate((3640.0, 4180.0)):
        x = A.X0 + 80.0
        while x < A.X1 - 80.0:
            if D.n < PROP_CAP - 10:
                D.ceil(pipes[(k + line) % 4], x, y, 90.0, 234.0)
            x += 128.0
            k += 1
    x = A.X0 + 100.0
    k = 0
    while x < A.X1 - 90.0:
        D.ceil('duct_metal_rectangle_straight_128', x, 3810.0, 90.0, 228.0)
        D.ceil('hanging_wires_01' if k % 2 else 'wire_hanging_ceiling_64', x + 50.0, 3980.0, 0.0, 196.0)
        x += 260.0
        k += 1


def _ceil(self, model, x, y, yaw, zc):
    """a ceiling prop by the centre of its bounds at height zc"""
    if self.n >= PROP_CAP or not zones_of(model):
        return None
    mn, mx = self.bounds(model)
    c = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, (mn[2] + mx[2]) / 2.0)
    a = math.radians(yaw)
    ox = x - (c[0] * math.cos(a) - c[1] * math.sin(a))
    oy = y - (c[0] * math.sin(a) + c[1] * math.cos(a))
    self.ids += 1
    self.m.use('dressing')
    B.prop(self.m, model, (round(ox, 2), round(oy, 2), round(zc - c[2], 2)), yaw=yaw, zone='arcade', id='c%03d_%s' % (self.ids, model[:16]))
    self.n += 1
    return True


Dresser.ceil = _ceil


# ------------------------------------------------------------------------------------------------ light
def lights(A, m, report):
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, **k)
    # pools under the live panels: tight spots, pale green white. Twelve of the live panels (the ones nearest the lanes first)
    live = sorted(A.live, key=lambda p: min(abs(p[1] - 3650.0), abs(p[1] - 4185.0)))
    rng = random.Random(3)
    chosen = []
    for p in live:
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 230.0 for q in chosen):
            chosen.append(p)
        if len(chosen) == 12:
            break
    for k, (x, y) in enumerate(chosen):
        L((x, y, 176.0), color=(0.86, 1.0, 0.90), radius=150.0, intensity=0.62, type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    for i in range(5):
        kind = A.BAYS[i]
        hue = HUE[kind]
        s = A.BAY_X[i]
        cx = s + A.BAY_W / 2.0
        h = 176.0
        L((cx, A.Y1 + 90.0, h), color=hue, radius=max(h * 2.0, 200.0), intensity=round(0.275 * (h / 200.0) ** 2, 4), type='spot', dir=(0.0, 0.0, -1.0), inner=22.0, outer=62.0, id='light_key_%d' % (i + 1))
        wp = (cx, A.Y1 + 36.0, h)
        wt = (cx, A.BACK_Y, 95.0)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(wp, wt)))
        d = [(wt[j] - wp[j]) / dist for j in range(3)]
        L(wp, color=tuple(round(0.12 + 0.88 * c, 3) for c in hue), radius=round(dist * 1.8, 1), intensity=round(0.385 * (dist / 200.0) ** 2, 4), type='spot', dir=d, inner=14.0, outer=44.0, id='light_wash_%d' % (i + 1))
        L((cx, A.Y1 - A.WT - 70.0, 150.0), color=hue, radius=110.0, intensity=0.096, id='light_neon_%d' % (i + 1))
        L((cx, A.Y1 + 235.0, 130.0), color=tuple(round(0.5 * c, 3) for c in hue), radius=120.0, intensity=0.006, id='light_back_%d' % (i + 1))
    L((A.X1 - 60.0, 3900.0, 170.0), color=(1.0, 0.85, 0.5), radius=170.0, intensity=0.18, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    L((A.X0 + 60.0, 3900.0, 170.0), color=(1.0, 0.1, 0.05), radius=170.0, intensity=0.12, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d7')
    L((-2800.0, A.Y0 + 60.0, 120.0), color=(0.9, 0.95, 1.0), radius=120.0, intensity=0.05, id='light_vend_w')
    L((-1380.0, A.Y0 + 60.0, 120.0), color=(0.9, 0.95, 1.0), radius=120.0, intensity=0.05, id='light_vend_e')
    L((A.X1 + 100.0, 3900.0, 200.0), color=(0.9, 0.9, 1.0), radius=160.0, intensity=0.05, id='light_vest')
    report['lights'] = n
    assert n <= LIGHT_CAP, n


def dress(A, m, foreign=None):
    D = Dresser(A, m)
    A.PANEL_LIVE, A.PANEL_DEAD = A.PANEL_LIVE, A.PANEL_DEAD
    setup_rooms(A, D)
    m.use('dressing')
    corridor_geometry(A, m)
    south_wall(A, D)
    north_piers(A, D)
    center_band(A, D)
    for i in range(5):
        bay(A, D, i)
    ceiling_props(A, D)
    clutter(A, D, PROP_CAP - 14)
    report = {}
    lights(A, m, report)
    report.update({'props': D.n, 'skipped': D.skipped, 'foreign_models': D.foreign, 'panels': A.panels, 'live_panels': len(A.live)})
    report['failed_hand'] = [f for f in D.failed if not f[0] in ()]
    m.dress_report = report
    m.dresser = D
    return report
