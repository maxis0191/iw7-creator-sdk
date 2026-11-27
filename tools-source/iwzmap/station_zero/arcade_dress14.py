r"""arcade_dress14: the Underpass Arcade's dressing, folded from rounds 1 to 13 into ONE module (the old chain arcade_dress, dress2 ... dress8, dress10 is deleted).

Generated from the live objects of the r13 build (every global a function touches resolved to its final value after the round-10 patches and the round-7 column swap),
then proven equal: the document written by `arcade_layer14.build()` before any round-14 change was byte-identical to round 13's `doc_e` (map.json and the seven layers).
Functions take `A`, the layer module (`arcade_layer14`), which carries the geometry constants (BAY_X, X0, aperture, ...).
"""
from studio import answers
from studio import build as B
from studio import fixtures as F
from studio import placer
from studio import prefab
from studio import prefab as P
from studio import props as P_props
import math
import os
import random
import sys
PROP_CAP = 2600
_zones = {}
MODELS_TXT = r'C:\studio-data\sz\arcade\r1\models.txt'

def zones_of(model):
    if not _zones:
        for ln in open(MODELS_TXT):
            n, _, z = ln.strip().partition(' ')
            _zones[n] = set(z.split(','))
    return _zones.get(model, set())


SUBST = {}

class _Pairs(list):
    """a list of (box, name) pairs that also takes the SDK's plain 4-tuples (named `<what>_<n>`)"""
    what = 'keep'

    def append(self, b):
        if len(b) == 4 and not isinstance(b[0], (list, tuple)):
            b = (tuple(b), '%s_%d' % (self.what, len(self) + 1))
        super().append(b)


class _Boxes(_Pairs):
    what = 'reserved'


class _Tops(dict):
    """the SDK's tops are 6-tuples (x, y, top, w, d, yaw); the Placer adds the prop id as a seventh"""

    def __setitem__(self, k, v):
        super().__setitem__(k, tuple(v)[:6])


FOREIGN = os.environ.get('ARC_FOREIGN', '1') != '0'

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
        if model in SUBST:
            model = SUBST[model]
            if model is None:
                return None, 'zone'
        if alt in SUBST:
            alt = SUBST[alt]
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


class PlacerDresser(placer.Placer):
    def __init__(self, A, m):
        super().__init__(m, layer='dressing', zone='arcade', prefix='p', cap=PROP_CAP, zones_of=zones_of, subst=SUBST)
        self.A = A
        self.keep, self.boxes, self.tops = _Pairs(), _Boxes(), _Tops()
        self.foreign = {}
        self.failed = []
        self.rng = random.Random(1978)

    def bounds(self, model):
        return self.bounds_of(model)

    def _put(self, model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone):
        rec, why = super()._put(model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone)
        if rec:
            zs = zones_of(rec['model'])
            if 'cp_zmb' not in zs:
                self.foreign[rec['model']] = sorted(zs)
        return rec, why

    def put(self, model, x, y, yaw=0.0, z=0.0, tag=None, scale=1.0, emissive=None, alt=None, clip='auto', on=None, margin=1.0, ignore_keep=False, zone='arcade', slide=None, reach=48.0):
        rec = super().put(model, x, y, yaw, z, tag, scale, emissive, alt, clip, on, margin, ignore_keep, zone, slide, reach)
        if rec is None:
            self.failed.append((tag or model, self._last_reason(tag or model), [round(x), round(y)]))
        return rec

    def _last_reason(self, key):
        row = self.ledger._t.get(str(key), {})
        rs = row.get('reasons') or {}
        return list(rs)[-1] if rs else 'refused'

    @property
    def skipped(self):
        out = {'room': 0, 'keep': 0, 'overlap': 0, 'zone': 0}
        for row in self.ledger._t.values():
            for reason, by in row['reasons'].items():
                out[reason] = out.get(reason, 0) + sum(by.values())
        return out

    def ceil(self, model, x, y, yaw, zc):
        """a ceiling prop by the centre of its bounds at height zc (the SDK Dresser's, counted in the ledger)"""
        model = SUBST.get(model, model)
        self.ledger.ask('ceil')
        if self.n >= PROP_CAP or not model or not zones_of(model):
            self.ledger.refuse('ceil', 'zone' if model else 'cap', model)
            return None
        mn, mx = self.bounds_of(model)
        c = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, (mn[2] + mx[2]) / 2.0)
        a = math.radians(yaw)
        ox = x - (c[0] * math.cos(a) - c[1] * math.sin(a))
        oy = y - (c[0] * math.sin(a) + c[1] * math.cos(a))
        self.ids += 1
        self.m.use('dressing')
        B.prop(self.m, model, (round(ox, 2), round(oy, 2), round(zc - c[2], 2)), yaw=yaw, zone='arcade', id='c%03d_%s' % (self.ids, model[:16]))
        self.n += 1
        self.ledger.ok('ceil')
        return True

    # the SDK Dresser.wall (Placer has no wall helper): it only calls self.put, self.bounds and self.A
    wall = Dresser.wall


SHOP_SRC = {'photo': ('cp_disco#120', 0), 'heel': ('cp_zmb#91', 0), 'hole9': ('cp_disco#59', 0), 'copy': ('cp_rave#104', 1), 'needle': ('cp_disco#39', 0)}
REPORT = {}
HUE = {'photo': (0.3, 0.85, 1.0), 'heel': (1.0, 0.55, 0.12), 'hole9': (1.0, 0.3, 0.68), 'copy': (0.26, 0.45, 1.0), 'needle': (1.0, 0.18, 0.2)}

BOARD = {'photo': 'w/metal_galvanized_bare_dark_01',
 'heel': 'w/wood_antique_panel_trim_01',
 'hole9': 'w/wood_worn_painted_01_green',
 'copy': 'w/metal_galvanized_bare_dark_01',
 'needle': 'w/wood_antique_panel_trim_01'}

BLACK = 'w/micro_metal_painted_01_dark_gray'
WAINS = {'photo': 'w/ceramic_ship_interior_tile_01', 'heel': 'w/ceramic_tile_01_orange', 'hole9': 'w/fac_tile_black_01', 'copy': 'w/ceramic_tile_01_blue', 'needle': 'w/fac_tile_black_01'}

def box(m, b, mat, mode='render', **kw):
    return B.box(m, [round(v, 2) for v in b], mat, mode=mode, **kw)


class Shelf:
    """a geometry shelf unit: uprights, boards, an invisible collision box; slots() yields stock positions per level"""
    def __init__(self, m, id, rect, front, levels, board='w/wood_antique_panel_trim_01', frame='w/metal_galvanized_bare_dark_01', top=96.0, clip=True, frame_parts=True):
        self.rect, self.front, self.levels, self.top = rect, front, levels, top
        x0, y0, x1, y1 = rect
        if clip:
            B.clip(m, [x0, y0, 0.0, x1, y1, top], id=id + '_clip')
        for k, z in enumerate(levels):
            box(m, [x0, y0, z - 2.0, x1, y1, z], board, id='%s_b%d' % (id, k))
        if not frame_parts:
            return
        # back panel and ends: thin dark
        bx = {'w': [x0, y0, 0.0, x0 + 2.0, y1, top], 'e': [x1 - 2.0, y0, 0.0, x1, y1, top], 's': [x0, y0, 0.0, x1, y0 + 2.0, top], 'n': [x0, y1 - 2.0, 0.0, x1, y1, top]}
        back = {'w': 'e', 'e': 'w', 's': 'n', 'n': 's'}[front]          # front = the side facing the room
        box(m, bx[back], frame, id=id + '_back')
        for k, (a, b) in enumerate(((x0, y0), (x1 - 2.0, y0), (x0, y1 - 2.0), (x1 - 2.0, y1 - 2.0))):
            box(m, [a, b, 0.0, a + 2.0, b + 2.0, top], frame, id='%s_up%d' % (id, k))

    def slots(self, step, margin=6.0):
        x0, y0, x1, y1 = self.rect
        out = []
        along_x = self.front in ('s', 'n')
        lo, hi = (x0, x1) if along_x else (y0, y1)
        mid = (y0 + y1) / 2.0 if along_x else (x0 + x1) / 2.0
        for z in self.levels:
            t = lo + margin
            while t <= hi - margin + 1e-6:
                out.append(((t, mid) if along_x else (mid, t), z))
                t += step
        return out


M = {'bench': 'cp_disco_worn_subway_bench',
 'news': 'cp_disco_street_news_vending_01',
 'phone': 'street_telephone_booth_old_iw6',
 'bin1': 'cp_disco_street_trashcan_01',
 'bin2': 'lv_trash_can_vegas',
 'turn': 'cp_disco_subway_turnstyle_animated',
 'locker': 'cp_disco_subway_lockers_02',
 'buffer': 'cp_disco_floor_buffer',
 'mop': 'com_janitor_bucket_mop_iw6',
 'wet': 'sign_wet_floor',
 'planter': 'p7_planter_concrete_box_64x32',
 'plant': 'com_potted_plant_small_des',
 'cart': 'park_concessions_cart',
 'barrier': 'cp_disco_subway_construction_barrier_01',
 'soda': 'cp_town_soda_machine_01',
 'case': 'greece_display_cases_11',
 'bag': 'com_trashbag2_black',
 'chips': 'food_trash_bag_chips_01',
 'cup': 'cup_paper_open_iw6',
 'paper': 'newspaper_single_fn_01',
 'can': 'food_trash_can_soda_01',
 'pile': 'cp_disco_trash_pile_01',
 'smokes': 'food_trash_cigarettes',
 'duct': 'duct_metal_rectangle_straight_128',
 'pipe': 'pipe_metal_painted_straight_128_gray',
 'wire': 'wire_hanging_ceiling_64',
 'wire2': 'hanging_wires_01',
 'gondola': 'cp_town_store_shelves_96_01',
 'steel': 'com_restaurantstainlessteelshelf_02',
 'rack': 'ac_prs_imp_com_clothing_rack_1',
 'boxa': 'p7_box_cardboard_a_closed',
 'boxc': 'p7_box_cardboard_c_closed',
 'ream': 'com_copypaper_box',
 'stack': 'office_paper_stack01_iw6',
 'books': 'office_book_set_iw6',
 'crackers': 'cp_town_grocery_crackers',
 'donuts': 'food_snacks_iw6_donutsstack01',
 'mug': 'p7_cup_coffee_mug',
 'coffee': 'misc_coffee_machine',
 'register': 'cp_town_cash_register',
 'shoes': 'p7_54i_gear_shoes',
 'crate': 'cp_disco_record_milk_crate',
 'sleeve': 'cp_disco_record_sleeve_01',
 'turntable': 'cp_rave_turntable_01',
 'juke': 'cp_town_jukebox',
 'hook': 'cp_rave_tiki_key_hook_01',
 'toolbox': 'dns_toolbox_small_iw6',
 'hammer': 'dns_tool_hammer01_iw6',
 'copier': 'cp_town_punchcard_computer_console',
 'computer': 'equipment_old_computer',
 'file': 'furniture_filing_cabinet',
 'stool': 'chair_bar_stool_02',
 'curtain': 'cp_disco_curtain_straight',
 'mags': 'cp_rave_magazine_stack_01',
 'stackp': 'newspaper_stack_fn_01',
 'valve': 'ind_pipe_metal_hp_12_valve_01',
 'warn': 'p7_caution_metal_sign_rusty',
 'cage': 'p7_lights_cagelight02_on',
 'glass': 'brokenglass_pile02',
 'sign1': 'cp_disco_sign_01',
 'sign2': 'cp_disco_sign_02',
 'sign4': 'cp_disco_sign_04',
 'lamp': 'p7_lights_cagelight02_on',
 'arcade': 'park_arcade_standing_01_off',
 'arcade2': 'park_arcade_standing_02_off',
 'claw': 'ct_arcade_claw_machine',
 'gum': 'gumball_machine_fn_01',
 'crate2': 'ch_crate32x48',
 'crate3': 'ch_crate48x64',
 'crate1': 'ch_crate24x36',
 'barrel': 'com_barrel_black',
 'barrel2': 'com_barrel_green_rust',
 'barrel3': 'com_barrel_tan_rust',
 'cone': 'traffic_cone_sml_01',
 'pallet': 'com_pallet',
 'cart2': 'park_concessions_cart',
 'ftable': 'com_folding_table',
 'fchair': 'chair_folding',
 'bucket': 'bucket_plastic',
 'stool2': 'chair_bar_stool_02',
 'dump': 'rp_dumpster_01',
 'ladder': 'com_stepladder_large',
 'fcab': 'furniture_filing_cabinet',
 'speaker': 'speaker_public_iw6',
 'tv': 'zmb_tv_crt_screen_01',
 'film': 'cp_disco_film_reel_case',
 'lockers': 'cp_disco_subway_lockers_02',
 'clothing': 'bike_shop_clothing_table_01',
 'desk': 'cp_town_desk_01',
 'phone2': 'cp_town_desk_phone_01_black',
 'photo1': 'cp_town_space_hero_photos_01',
 'planter2': 'flower_shop_planter_04_with_plant',
 'hydrant': 'vfx_fire_hydrant_stream',
 'fluo': 'cp_disco_fluorescent_light_on',
 'hang': 'hanging_light_iw6_beige',
 'debris': 'com_debris_paper_iw6_02',
 'extg': 'fac_metal_extinguisher_02',
 'ventp': 'cnd_electric_panels_vent_01_fac',
 'barrier2': 'cp_disco_subway_construction_barrier_01',
 'mopb': 'com_janitor_bucket_mop_iw6',
 'hose': 'crr_hose_slant_gray',
 'planter_w': 'container_wood_planter_01',
 'display': 'park_concessions_cart_food_display_glass',
 'sandbag': 'dns_sandbag01_singleflat_iw6',
 'sandbag2': 'dns_sandbag01_singlebent_iw6',
 'plant_big': 'com_potted_plant_small_des',
 'duct_r': 'vent_duct_round_128_md',
 'shelf_i': 'p7_shelf_industrial_gray_48',
 'cart_c': 'park_concessions_cart_cluster',
 'dojo': ('cp_disco_dojo_column_01', 'cp_disco_dojo_column_02', 'cp_disco_dojo_column_03', 'cp_disco_dojo_column_04'),
 'fluo_off': 'cp_disco_fluorescent_light_off',
 'ibeam': 'building_ibeam_large_long',
 'bracket': 'p7_ibeam_bracket_32_t_01',
 'post': 'btr_ibeam_yellow_vert_01_gray',
 'booth': 'zmb_mobile_ticket_booth',
 'awning': 'cp_disco_awnings_rounded',
 'duct_sup': 'duct_metal_rectangle_ceiling_support',
 'duct_vent': 'duct_metal_rectangle_vent',
 'duct_elb': 'duct_metal_rectangle_elbow_down_90'}

dress3_POSTERS = ['w/signage_theater_menu_01', 'w/signage_zmb_park_poster_01', 'w/signage_zmb_park_poster_04', 'w/signage_zmb_park_poster_06', 'w/signage_decals_corridor_01']
POSTERS = dress3_POSTERS + ['w/signage_theater_menu_01', 'w/zombies_theater_poster01', 'w/zombies_theater_poster02', 'w/signage_zmb_park_poster_03']

TUBE = {'photo': 'w/metal_light_line_lightblue_03',
 'heel': 'w/plastic_wall_panel_light_03_on_orange',
 'hole9': 'w/emissive_light_panel_pink',
 'copy': 'w/plastic_wall_panel_light_02_on_blue',
 'needle': 'w/plastic_wall_panel_light_02_on_red'}


CAL = bool(os.environ.get('ARC3_CAL'))
DARK = 'w/micro_metal_painted_01_dark_gray'
DARKMETAL = 'w/metal_panel_dark_01'
RUBBER = 'w/rubber_trim_black'
PIERS = [(-2984.0, -2916.0), (-2684.0, -2586.0), (-2354.0, -2256.0), (-2024.0, -1926.0), (-1694.0, -1596.0), (-1364.0, -1216.0)]
FRONTS = [(-2480.0, -2220.0), (-1790.0, -1500.0), (-1470.0, -1290.0)]
HATCH = (-2130.0, -2030.0)
NAMES = {'photo': 'PHOTOS', 'heel': 'HEEL & KEY', 'hole9': 'HOLE NUMBER NINE', 'copy': 'COPY STOP', 'needle': 'NEEDLE DROP'}
SPINE_Y = 3900.0
STEEL = 'w/metal_painted_04'
DOJO = os.environ.get('ARC7_COLUMNS', 'dojo') == 'dojo'
COL_HALF = float(os.environ.get('ARC17_COL_HALF', '9.0'))      # half the shaft of the stock dojo column (measured 8.8)
D7_WHEEL = os.environ.get('ARC17_D7_WHEEL', '0') == '1'
FLOOR_SLABS = os.environ.get('ARC17_FLOOR_SLABS', '0') == '1'
LB_FACE = os.environ.get('ARC17_LB_FACE', '0') == '1'

COLSPEC = [
    dict(mat='w/ceramic_tile_01_orange', wain=('w/ceramic_tile_01_blue', 112.0), stripe=None, feature='map'),
    dict(mat='w/concrete_painted_wall_green', wain=('w/concrete_wall_panel_05', 64.0), stripe='w/metal_painted_scratched_yellow', feature='extinguisher'),
    dict(mat='w/brick_cinderblock_02_smooth_blue', wain=None, stripe='w/plastic_slick_floor_01_orange', feature='lightbox'),
    dict(mat='w/concrete_wall_panel_05', wain=('w/fac_tile_black_01', 80.0), stripe=None, feature='plain'),            # phones stand against it
    dict(mat='w/ceramic_tile_01_blue', wain=('w/ceramic_tile_01_orange', 48.0), stripe=None, feature='poster'),
    dict(mat='w/brick_cinderblock_04_beige_dirty', wain=None, stripe='w/concrete_painted_wall_green', feature='poster2'),
]

DOJO_SCALE = 0.77
COLS = [-2850.0, -2550.0, -2250.0, -1950.0, -1650.0, -1350.0]
GAPS = [-2700.0, -2400.0, -2100.0, -1800.0, -1500.0]
POOL_I = 1.8
KEY_I = 1.0
SHOP_SIGN = ('neon_open', 'neon_tube', 'bulb_strip', 'neon_open', 'neon_tube')
CANON = {'cp_disco_sign_01': 'PHOTOS', 'cp_disco_sign_02': 'HEEL & KEY', 'cp_disco_sign_04': 'COPY STOP'}
LITTER = ('chips', 'cup', 'paper', 'can', 'smokes', 'stackp', 'mags', 'mug', 'crate1', 'crate2', 'cone', 'bucket', 'pallet', 'stool2', 'fchair', 'barrel')
STRIP_DEPTH = 30.0
SHELF = 'com_restaurantstainlessteelshelf_02'

def setup_rooms(A, D):
    D.rooms.append((A.X0 + A.WT, A.Y0 + A.WT, A.X1 - A.WT, A.Y1 - A.WT))
    for i in range(5):
        s = A.BAY_X[i]
        D.rooms.append((s + A.WT, A.Y1 + A.WT, s + A.BAY_W - A.WT, A.BACK_Y))
        D.rooms.append((s + A.WT, A.BACK_Y + 12.0, s + A.BAY_W - A.WT, A.Y1 + A.BAY_D - A.WT))
    D.rooms.append((A.X1 + A.WT, 3796.0, A.X1 + 200.0 - A.WT, 4004.0))
    D.add_keep((A.X0, 3590.0, A.X1, 3700.0), 'lane_south')
    D.add_keep((A.X0, 4130.0, A.X1, 4240.0), 'lane_north')
    for i in range(5):
        a0, a1 = A.aperture(i)
        s = A.BAY_X[i]
        D.add_keep((a0, 4240.0, a1, A.Y1 + 20.0), 'front_bay%d' % (i + 1))
        D.add_keep((s + 120.0, A.Y1, s + 200.0, A.BACK_Y + 30.0), 'path_bay%d' % (i + 1))
    D.add_keep((A.X1 - 200.0, 3780.0, A.X1 - 16.0, 4020.0), 'approach_D4')
    D.add_keep((A.X0, 3780.0, A.X0 + 80.0, 4020.0), 'approach_D7')
    for r in answers.clearance_rows(D.m):
        b = r['box']
        D.add_keep((b[0] - 4.0, b[1] - 4.0, b[3] + 4.0, b[4] + 4.0), '%s %s' % (r['kind'], r['id']))
    for c in D.m.flat().cameras:
        x, y = c['origin'][0], c['origin'][1]
        D.add_keep((x - 52.0, y - 52.0, x + 52.0, y + 52.0), 'camera %s' % c.get('id', c.get('name', '?')))


def dress_shop(A, m, D, i, report):
    """dress_like into the shop's front room, with the gameplay clearances and the named keep-outs that touch the bay; what it could not place is named in the answer"""
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    left, right = s + A.WT, s + A.BAY_W - A.WT
    y0, y1 = A.Y1 + A.WT, A.BACK_Y - 34.0
    room, seed = SHOP_SRC[kind]
    box = [left, y0, right, y1]
    keep = answers.clearance_rows(m) + [(k, n) for (k, n) in D.keep if _overlaps(box, k) and n.startswith(('camera', 'front_bay', 'path_bay'))]
    m.use('dressing')
    rep = prefab.dress_like(m, room, box, front='s', density=1.0, seed=seed, z=0.0, prefix='dl%d_' % (i + 1), keep_clear=keep, resupport=True)
    D.n += rep['placed']
    for pid in rep['ids']:
        o = m.get(pid)
        if o is not None and o.get('kind') == 'prop' and o['origin'][2] < 72.0:
            bx = D.box_of(o['model'], o['origin'][0], o['origin'][1], (o.get('angles') or [0, 0, 0])[1], o.get('scale') or 1.0)
            D.boxes.append((tuple(bx), pid))
    report.setdefault('dress_like', {})[kind] = {'room': room, 'placed': rep['placed'], 'dropped': rep['dropped_by_reason'], 'models': rep['models_needed'],
                                                'density_per_1000': rep['density_per_1000'], 'coverage': rep['coverage']['dressed'], 'resupported': rep.get('resupported'),
                                                'refusal_lines': rep.get('refusal_lines')}
    REPORT.setdefault('dress_like', {})[kind] = {'placed': rep['placed'], 'refusal_lines': rep.get('refusal_lines'), 'resupported': rep.get('resupported')}


def _overlaps(b, k):
    return b[0] < k[2] and b[2] > k[0] and b[1] < k[3] and b[3] > k[1]


def shop(A, m, D, i, report):
    s = A.BAY_X[i]
    yb = A.Y1
    kind = A.BAYS[i]
    wallb = yb + A.BAY_D - A.WT
    U = lambda u: s + u
    V = lambda v: yb + v
    yp = A.BACK_Y
    left, right = s + A.WT, s + A.BAY_W - A.WT
    hue = HUE[kind]
    brd = BOARD[kind]
    lv = (24.0, 46.0, 68.0, 90.0, 112.0, 134.0, 156.0)
    D.rooms.append((left, yb + A.WT, right, yp + 10.0))                 # the stock leans on the partition: its jittered boxes may touch the partition's thickness
    D.rooms.append((left, yp + 10.0, right, wallb + 6.0))
    m.use('dressing')
    box(m, [left, yb + A.WT, 0.0, left + 2.0, wallb, 8.0], BLACK, id='skirt_l_%d' % (i + 1))
    box(m, [right - 2.0, yb + A.WT, 0.0, right, wallb, 8.0], BLACK, id='skirt_r_%d' % (i + 1))
    # the tiled wainscot of the front room (render only) and a rail
    for side, (xa, xb) in enumerate(((left, left + 1.5), (right - 1.5, right))):
        box(m, [xa, yb + A.WT, 8.0, xb, yp, 44.0], WAINS[kind], id='wain_%d_%d' % (i + 1, side))
        box(m, [xa, yb + A.WT, 44.0, xb, yp, 46.0], BLACK, id='wrail_%d_%d' % (i + 1, side))
    box(m, [left, yb + A.WT, 8.0, right, yb + A.WT + 1.5, 44.0], WAINS[kind], id='wain_f_%d' % (i + 1))
    # the stock: tall shelving on the partition's face (the back wall the inside camera sees), two units, packed
    items = {'photo': (['boxc', 'photo1', 'mags', 'crackers', 'paper', 'books', 'film'], ['film', 'boxc', 'paper', 'mags', 'photo1', 'books', 'boxa']),
             'heel': (['shoes', 'shoes', 'boxc', 'shoes', 'shoes', 'boxa', 'hook'], ['shoes', 'boxc', 'shoes', 'shoes', 'boxa', 'shoes', 'toolbox']),
             'hole9': (['crackers', 'donuts', 'mug', 'boxc', 'glass', 'bag', 'boxa'], ['donuts', 'boxa', 'mug', 'crackers', 'glass', 'boxc', 'donuts']),
             'copy': (['ream', 'stack', 'ream', 'books', 'ream', 'stack', 'boxa'], ['ream', 'ream', 'books', 'stack', 'ream', 'boxa', 'books']),
             'needle': (['film', 'crate', 'boxa', 'crate', 'film', 'boxc', 'crate'], ['crate', 'film', 'boxc', 'crate', 'boxa', 'film', 'crate'])}[kind]       # r18: no record_sleeve model (its texture carries a garbled DISCO lettering)
    step = {'photo': 9.0, 'heel': 9.0, 'hole9': 9.0, 'copy': 10.0, 'needle': 5.0}[kind]
    n_stock = back_strips(A, m, D, i, kind, items, brd)
    # a transom shelf above the doorway, packed boxes
    sh = Shelf(m, 'shelf_t_%d' % i, (U(116.0), yp - 22.0, U(204.0), yp), 's', (110.0, 134.0, 158.0), board=brd, top=172.0, clip=False, frame_parts=False)      # above the doorway (96 high): no collision
    n_stock += stock(D, sh, ['boxc', 'boxa', 'boxc'] if kind != 'needle' else ['crate', 'boxa', 'crate'], 28.0, yaw=270.0, jitter=10.0, skip=0.0)
    for zb in (110.0, 134.0, 158.0):                                                  # r18: two brackets under each board (the boxes hovered on a bare board)
        for ub in (122.0, 198.0):
            box(m, [U(ub) - 1.0, yp - 20.0, zb - 8.0, U(ub) + 1.0, yp, zb - 2.0], BLACK, id='shelf_t_%d_br_%d_%d' % (i, int(zb), int(ub)))
    # the hung things behind the aperture (as round 3) and the posters on both side walls
    cx = s + A.BAY_W / 2.0
    hy = V(HUNG_Y)
    if kind == 'photo':
        for k in range(9):
            hung_pic(m, 'hg_%d_%d' % (i, k), cx - 100.0 + 25.0 * k, hy + (6.0 if k % 2 else 0.0), HUNG_Z + 6.0 * (k % 3), 14.0, 18.0, 'photo_%d.png' % (k % 3))
    elif kind == 'heel':
        for q, ux in enumerate((-90.0, 90.0)):
            box(m, [cx + ux - 22.0, hy + 4.0, 56.0, cx + ux + 22.0, hy + 5.5, 86.0], 'w/wood_worn_painted_01_green', id='keyboard_%d_%d' % (i, q))
            rod(m, 'kb_ra_%d_%d' % (i, q), cx + ux - 20.0, hy + 4.0, 86.0, 200.0)
            rod(m, 'kb_rb_%d_%d' % (i, q), cx + ux + 20.0, hy + 4.0, 86.0, 200.0)
            for k in range(8):
                D.put(M['hook'], cx + ux - 18.0 + 5.0 * k, hy + 4.0, 270.0, z=60.0 + 12.0 * (k % 2) + 8.0, scale=2.5, ignore_keep=True, margin=0.0)
    elif kind == 'hole9':                          # r18: the menu boards on the partition's wall above the shelf units (they hung 66 units from the chk camera and read as oversized)
        wall_pic(m, 'hg_%d_0' % i, U(67.0), yp, 86.0, 84.0, 50.0, 'menu_0.png')
        wall_pic(m, 'hg_%d_1' % i, U(253.0), yp, 90.0, 56.0, 40.0, 'menu_1.png')
        B.decal(m, image='menu_2.png', at=(right, V(104.0), 96.0), normal=(-1.0, 0.0, 0.0), size=(40.0, 28.0), id='menu_side_%d' % i)
    elif kind == 'copy':                           # r18: four pinned notices, two beside each shelf unit's top, on the wall
        for k, u in enumerate((38.0, 82.0, 238.0, 282.0)):
            wall_pic(m, 'hg_%d_%d' % (i, k), U(u), yp, 96.0 + (3.0 if k % 2 else 0.0), 24.0, 32.0, 'sheet_%d.png' % k)
    elif kind == 'needle':                         # r18: record sleeves on wall ledges, two rows of two either side of the door
        for k, (u, row) in enumerate(((42.0, 0), (70.0, 0), (42.0, 1), (70.0, 1), (250.0, 0), (278.0, 0), (250.0, 1), (278.0, 1))):
            wall_pic(m, 'hg_%d_%d' % (i, k), U(u), yp, 94.0 + 18.0 * row, 14.0, 14.0, 'sleeve_%d.png' % k, ledge=True)
    for k, (zz, vv) in enumerate(((100.0, 50.0), (96.0, 96.0), (104.0, 130.0))):
        B.decal(m, image='poster_%d.png' % ((i + k) % 6), at=(left, V(vv), zz), normal=(1.0, 0.0, 0.0), size=(26.0, 36.0), id='post_l_%d_%d' % (i, k))
        if not (kind == 'hole9' and k == 1):                       # r18: the bar's house-rules card takes that place
            B.decal(m, image='poster_%d.png' % ((i + k + 3) % 6), at=(right, V(vv + 8.0), zz), normal=(-1.0, 0.0, 0.0), size=(26.0, 36.0), id='post_r_%d_%d' % (i, k))
    # the emissive light strips in the shop's hue under the ceiling (they light the stock and the floor through the bake) and a black housing
    for k, vv in enumerate((58.0, 118.0)):
        box(m, [cx - 96.0, V(vv) - 3.0, 194.0, cx + 96.0, V(vv) + 3.0, 198.0], TUBE[kind], id='strip_%d_%d' % (i + 1, k))
        box(m, [cx - 98.0, V(vv) - 5.0, 198.0, cx + 98.0, V(vv) + 5.0, 200.0], BLACK, id='strip_h_%d_%d' % (i + 1, k))
    # the back room: lit, with stock (zombies spawn here: D.keep holds the spawner clearances)
    for side, ux in enumerate((62.0, 258.0)):
        sh = Shelf(m, 'bs_%d_%d' % (i, side), (U(ux - 30.0), wallb - 24.0, U(ux + 30.0), wallb), 's', (24.0, 52.0, 80.0, 108.0), board=brd, top=116.0, clip=False)
        stock(D, sh, ['boxc', 'boxa', 'crate2', 'bag', 'boxc'], 18.0, yaw=270.0, jitter=14.0, skip=0.05)
    D.put(M['barrel'], U(150.0), wallb - 20.0, 0.0, tag='bk_barrel_%d' % i, margin=1.0, clip=False)
    D.put(M['crate3'], U(184.0), wallb - 26.0, 8.0, tag='bk_crate_%d' % i, margin=1.0, clip=False)
    D.put(M['ladder'], U(30.0), V(240.0), 80.0, tag='bk_ladder_%d' % i, margin=1.0, clip=False)
    D.put(M['fcab'], U(290.0), V(256.0), 270.0, tag='bk_fcab_%d' % i, margin=1.0, clip=False)
    if kind in ('hole9', 'copy', 'needle'):                  # r18: the bay's walls at a correct texel size (the material's own tiling drew bricks 3 times too big and soft): render-only skins, 0.2 thick
        skin(m, i, brd_mat=A.BAYWALL[i], left=left, right=right, yb=yb + A.WT, yp=yp, s=s)
    n = D.n
    dress_shop(A, m, D, i, report)
    if kind == 'needle':                                    # r18: the stock model of the record shop's shelves carries a garbled DISCO lettering: the pictures above are the sleeves
        for o in [o for o in m.objects() if o['kind'] == 'prop' and 'record_sleeve' in str(o.get('model'))]:
            if A.BAY_X[4] <= o['origin'][0] <= A.BAY_X[4] + A.BAY_W:
                m.remove(o['id'])
    return n_stock


def stock(D, shelf, items, step, yaw=0.0, jitter=0.0, skip=0.0, scale=1.0):
    """fill a shelf: every slot gets items[k % len] (None = a gap), a little yaw jitter"""
    n = 0
    for k, ((x, y), z) in enumerate(shelf.slots(step)):
        mod = items[(k + int(z) // 20) % len(items)]
        if mod is None or D.rng.random() < skip:
            continue
        if D.put(M[mod] if mod in M else mod, x, y, yaw + D.rng.uniform(-jitter, jitter), z=z, ignore_keep=True, margin=0.0, scale=scale):
            n += 1
    return n


HUNG_Y = 76.0           # r13: 44 (34 units from the chk cameras, 41 % of their frame); the boards now hang 76 into the shop
HUNG_LAMP = False         # r15 gave every picture its own lamp (FE62); r16 (FE66: the engine's light tiles break above 177 rows of lights.txt) lights them with one lamp per group of boards (arcade_layer14.lamps16)
ARROW_LAMP = {'intensity': 1.0, 'color': [0.75, 0.85, 1.0]}
HUNG_Z = 76.0           # r13: 52 (the player's eye line, and 41 % of the chk cameras' frame); now above a standing player's head and inside the chk cameras' frame (z 70, +-31 at 66 units)


SKIN_TILE = float(os.environ.get('ARC18_SKIN_TILE', '48'))


def skin(m, i, brd_mat, left, right, yb, yp, s):
    """r18: render-only 0.2 thick skins on the partition's front face (around the doorway: x s+120..s+200 up to z 96) and on the two side walls above the wainscot, the bay's wall material tiled SKIN_TILE units
    (the exporter's own size drew the bricks of chk_bay3/4/5 about 20 units wide and soft)"""
    uv = {'*': {'tile': [SKIN_TILE, SKIN_TILE]}}
    k = i + 1
    box(m, [left, yp - 0.2, 0.0, s + 120.0, yp, 200.0], brd_mat, mode='render', id='skin_pa_%d' % k, uv=uv)
    box(m, [s + 200.0, yp - 0.2, 0.0, right, yp, 200.0], brd_mat, mode='render', id='skin_pb_%d' % k, uv=uv)
    box(m, [s + 120.0, yp - 0.2, 96.0, s + 200.0, yp, 200.0], brd_mat, mode='render', id='skin_pc_%d' % k, uv=uv)
    box(m, [left, yb, 46.0, left + 0.2, yp, 200.0], brd_mat, mode='render', id='skin_l_%d' % k, uv=uv)
    box(m, [right - 0.2, yb, 46.0, right, yp, 200.0], brd_mat, mode='render', id='skin_r_%d' % k, uv=uv)


def wall_pic(m, id, x, yp, z, w, h, picture, ledge=False):
    """r18: a picture board fixed to a wall face (y = yp, facing -y): a 3.4 deep dark backing 1 unit larger than the picture all round and the picture sign on its face (`hg_*_pic`: lamps16 lights it);
    ledge=True also a 5 deep ledge under it (a record sleeve stands on it)"""
    box(m, [x - w / 2.0 - 1.0, yp - 3.4, z - 1.0, x + w / 2.0 + 1.0, yp, z + h + 1.0], BLACK, id=id)
    if ledge:
        box(m, [x - w / 2.0 - 3.0, yp - 5.0, z - 2.5, x + w / 2.0 + 3.0, yp, z - 1.0], BLACK, id=id + '_ledge')
    B.sign(m, image=picture, at=(x, yp, z + h / 2.0), normal=(0.0, -1.0, 0.0), size=(w, h), lamp=HUNG_LAMP, id=id + '_pic')


def hung_pic(m, id, x, y, z, w, h, picture, ceil=200.0):
    """a board hung by a rod at each end: a dark backing and the picture (a file Studio draws, UV 0..1 over the whole image) 3.6 in front of it, facing the entrance"""
    box(m, [x - w / 2.0, y - 0.4, z, x + w / 2.0, y + 0.4, z + h], BLACK, id=id)
    rod(m, id + '_ra', x - w / 2.0 + 1.0, y, z + h, ceil)
    rod(m, id + '_rb', x + w / 2.0 - 1.0, y, z + h, ceil)
    B.sign(m, image=picture, at=(x, y - 0.4, z + h / 2.0), normal=(0.0, -1.0, 0.0), size=(w - 1.6, h - 1.6), lamp=HUNG_LAMP, id=id + '_pic')      # r15: lit and lamped (FE62), not emissive: an emissive picture went black with the power on


def hung(m, id, x, y, z, w, h, mat, ceil=200.0):
    hung_sheet(m, id, x, y, z, w, h, mat, True, ceil)


def hung_sheet(m, id, x, y, z, w, h, mat, rods=True, ceil=200.0):
    """a flat piece hung from the ceiling by a rod at each end (flat geometry carrying a poster or photo material)"""
    box(m, [x - w / 2.0, y - 0.4, z, x + w / 2.0, y + 0.4, z + h], mat, id=id)
    if rods:
        rod(m, id + '_ra', x - w / 2.0 + 1.0, y, z + h, ceil)
        rod(m, id + '_rb', x + w / 2.0 - 1.0, y, z + h, ceil)


def rod(m, id, x, y, z0, z1):
    box(m, [x - 0.6, y - 0.6, z0, x + 0.6, y + 0.6, z1], BLACK, id=id)


def shop10(A, m, D, i, report):
    """round 4's shop (with strips), then from rounds 5 and 6 only what does not belong to the tall units: the back room's continuous stock, the hanging lamps, the barrel and crate
    moved out of the back shelf, the back room's middle unit"""
    n = shop(A, m, D, i, report)
    s = A.BAY_X[i]
    kind = A.BAYS[i]
    wallb = A.Y1 + A.BAY_D - A.WT
    brd = BOARD[kind]
    U = lambda u: s + u
    m.use('dressing')
    sh = Shelf(m, 'bsm_%d' % i, (U(116.0), wallb - 24.0, U(204.0), wallb), 's', (22.0, 50.0, 78.0, 106.0), board=brd, top=116.0, clip=False)
    stock(D, sh, ['boxc', 'crate2', 'boxa', 'crate2', 'bag', 'boxc'], 24.0, yaw=270.0, jitter=12.0, skip=0.0, scale=1.2)
    for k, u in enumerate((60.0, 160.0, 260.0)):
        D.put(M['hang'], U(u), A.BACK_Y + 56.0, 0.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)
    for pid in [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and ('bk_barrel_%d' % i in o['id'] or 'bk_crate_%d' % i in o['id'])]:
        m.remove(pid)
    D.put(M['barrel'], U(30.0), A.BACK_Y + 36.0, 0.0, margin=1.0, clip=False)
    D.put(M['crate3'], U(290.0), A.BACK_Y + 36.0, 8.0, margin=1.0, clip=False)
    rng = random.Random(40 + i)
    placed = 0
    for z in (22.0, 50.0, 78.0, 106.0):
        t = U(122.0)
        while t < U(198.0):
            if D.put(rng.choice([M['boxc'], M['boxa'], M['crate2'], M['bag']]), t, wallb - 12.0, 270.0 + rng.uniform(-10.0, 10.0), z=z, ignore_keep=True, margin=0.0, clip=False):
                placed += 1
            t += rng.uniform(20.0, 30.0)
    return n + 1 + placed


def dress(A, m, stage='full', foreign=None):
    report = dress7_dress(A, m, stage, foreign)
    if not os.environ.get('ARC8_NOFX'):
        fixtures8(A, m, report)
    canon8(A, m, report)
    if not os.environ.get('ARC8_NOLIT'):
        litter8(A, m, report)
    F.use_kit(m)
    return report


def dress7_dress(A, m, stage='full', foreign=None):
    D = PlacerDresser(A, m)
    report = {}
    setup_rooms(A, D)
    shutters(A, m, report)
    floor7(A, m, D, report)
    wall_bands4(A, m, D, report)
    fronts_and_doors(A, m, D, report)
    ceiling7(A, m, D, report)
    spine4(A, m, D, report)
    kiosk7(A, m, D, report)
    d7_6(A, m, D, report)
    wall_props(A, m, D)
    report['stock'] = {}
    for i in range(5):
        report['stock'][A.BAYS[i]] = shop10(A, m, D, i, report)
    d7_props(A, D)
    ceiling_props(A, D)
    ducts7(A, m, D)
    for y in (3600.0, 4220.0):
        x = A.X0 + 160.0
        while x < A.X1 - 90.0:
            D.ceil(M['pipe'], x, y, 90.0, 232.0)
            x += 128.0
    stories5(A, m, D, report)
    L, n = lights7(A, m, report)
    n += shop_fixtures(A, m, D, L)
    report['lights'] = n + len(A.live)
    m.use('cameras')
    for k in range(5):
        a0, a1 = A.aperture(k)
        B.camera(m, 'sign_%d' % (k + 1), ((a0 + a1) / 2.0, 4090.0, 165.0), 90.0, id='sign_%d' % (k + 1))
    models = {p['model'] for p in m.flat().props}
    report['distinct_models'] = len(models)
    report.update({'props': len(m.flat().props), 'by_area': counts(m, A), 'skipped': D.skipped, 'foreign_models': D.foreign, 'failed': D.failed[:80]})
    m.dress_report = report
    m.dresser = D
    return report


def shutters(A, m, report):
    m.use('dressing')
    yin = A.Y1 - A.WT
    info = {}
    cands = ['w/micro_metal_painted_01_dark_gray', 'w/metal_deck_painted_black_01', 'w/metal_galvanized_bare_dark_01', 'w/metal_painted_dark_blue', 'w/metal_corrugated_01']
    for i in range(5):
        a0, a1 = A.aperture(i)
        share = A.SHUT_SHARE[i]
        zb = A.AP_H * (1.0 - share)
        jam = share > 0.5
        x1 = a1 - A.SHUT_GAP if jam else a1
        mat = cands[i] if CAL else A.SHUTTER
        B.box(m, [a0, yin + 4.0, zb, x1, yin + 8.0, A.AP_H], mat, id='shutter_curtain_%d' % (i + 1))
        box(m, [a0, yin + 3.0, zb - 3.0, x1, yin + 9.0, zb], BLACK, id='shutter_bar_%d' % (i + 1))
        box(m, [a0 - 8.0, yin - 14.0, A.AP_H, a1 + 8.0, yin, A.AP_H + 24.0], BLACK, id='shutter_box_%d' % (i + 1))
        box(m, [a0 - 7.0, yin - 2.0, 0.0, a0 - 1.0, yin + 3.0, A.AP_H], BLACK, id='rail_l_%d' % (i + 1))
        box(m, [a1 + 1.0, yin - 2.0, 0.0, a1 + 7.0, yin + 3.0, A.AP_H], BLACK, id='rail_r_%d' % (i + 1))
        info[i + 1] = {'bottom_z': round(zb, 1), 'material': mat, 'jammed_gap': [round(x1, 1), round(a1, 1)] if jam else None}
    report['shutters'] = info


def floor7(A, m, D, report):
    floor5(A, m, D, report)
    m.remove('floor_tile')
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(('wear_', 'puddle_'))]:
        k = int(pid.split('_')[-1])
        if (pid.startswith('wear_') and k >= 8) or (pid.startswith('puddle_') and k >= 4):
            m.remove(pid)
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    zones = ((cx0, -2640.0, 'w/building_ship_hallway_floor_06_tile_gray_glossy', 40.0), (-2640.0, -2280.0, 'w/beacon_lab_floor_tile_02_black', 24.0),
             (-2280.0, -1920.0, 'w/stone_floor_tiles_01', 44.0), (-1920.0, -1560.0, 'w/clk_rubber_tiles', 32.0), (-1560.0, cx1, 'w/building_ship_hallway_floor_06_tile_gray_glossy', 56.0))
    for k, (x0, x1, mat, t) in enumerate(zones):
        box(m, [x0, cy0, 0.0, x1, cy1, 1.0], mat, id='floor_zone_%d' % k, uv={'top': {'tile': [t, t]}})
        if k:
            box(m, [x0 - 3.0, cy0, 0.0, x0 + 3.0, cy1, 1.2], DARK, id='floor_zone_seam_%d' % k)
    report['floor7'] = [z[2] for z in zones]


STAIN_FILES = ['stain_0.png', 'stain_1.png', 'stain_2.png']
SOFT_STAINS = os.environ.get('ARC17_SOFT_STAINS', '1') == '1'


def soft_stain(m, k, material, at, size, rot, id):
    """a floor stain decal. r17: the stock stain materials that are not `_dec` (dirt_stain_water_drips_01, asphalt_flooring_stain_01) drew as hard-edged rectangles on the platform tiles (conv_platform, 3/3 reviewers):
    our own soft-edged picture (stain_N.png, alpha is the coverage, written by make_pictures) takes their place; a `_dec` material is a blend decal already and stays"""
    if SOFT_STAINS and not material.endswith('_dec'):
        return B.decal(m, image=STAIN_FILES[k % len(STAIN_FILES)], at=at, normal=(0.0, 0.0, 1.0), size=size, rot=rot, id=id)
    return B.decal(m, material, at, (0.0, 0.0, 1.0), size, rot=rot, id=id)


def floor5(A, m, D, report):
    m.use('dressing')
    rng = random.Random(55)
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    uv = lambda t: {'top': {'tile': [t, t]}}
    box(m, [cx0, cy0, 0.0, cx1, cy1, 1.0], A.FLOOR_SKIN, id='floor_tile', uv=uv(40.0))
    for k, (y0, y1) in enumerate(((cy0, cy0 + 26.0), (cy1 - 26.0, cy1))):
        box(m, [cx0, y0, 0.0, cx1, y1, 1.5], 'w/fac_tile_black_01', id='floor_border_%d' % k, uv=uv(32.0))
    n = 0
    for k, y0 in enumerate((cy0 + 26.0, cy1 - 70.0)):                      # a concrete edge along each wall in broken lengths
        x = cx0
        while x < cx1 - 40.0:
            w = rng.uniform(140.0, 420.0)
            box(m, [x, y0, 0.0, min(x + w, cx1), y0 + rng.uniform(22.0, 30.0), 1.25], 'w/aq_stone_concrete_patch02', id='edge_%d_%d' % (k, n), uv=uv(48.0))
            x += w + rng.uniform(0.0, 180.0)
            n += 1
    for k, yc in enumerate(((cy0 + 3850.0) / 2.0, (3950.0 + cy1) / 2.0)):  # the worn lane centres: wet asphalt, in lengths with gaps
        x = cx0 + rng.uniform(0.0, 120.0)
        while x < cx1 - 60.0:
            w = rng.uniform(180.0, 460.0)
            half = rng.uniform(30.0, 46.0)
            off = rng.uniform(-14.0, 14.0)
            if FLOOR_SLABS:                                                 # r17: off (the worn lanes were pale cracked-stone slabs with hard edges on the dark tile: 3/3 reviewers, `studio pick` lane_1_31)
                box(m, [x, yc + off - half, 0.0, min(x + w, cx1), yc + off + half, 1.3], 'w/asphalt_flooring_01_wet', id='lane_%d_%d' % (k, n), uv=uv(44.0))
            x += w + rng.uniform(50.0, 200.0)
            n += 1
        for sgn in (-1, 1):                                                 # the orange line, broken
            x = cx0
            while x < cx1 - 30.0:
                w = rng.uniform(90.0, 260.0)
                box(m, [x, yc + sgn * 52.0 - 2.0, 0.0, min(x + w, cx1), yc + sgn * 52.0 + 2.0, 1.6], 'w/plastic_slick_floor_01_orange', id='inlay_%d_%d_%d' % (k, sgn, n), uv=uv(24.0))
                x += w + rng.uniform(40.0, 130.0)
                n += 1
    for k in range(5):                                                      # the tiled apron before each shop
        a0, a1 = A.aperture(k)
        box(m, [a0 - 24.0, cy1 - 150.0, 0.0, a1 + 24.0, cy1 - 26.0, 1.35], 'w/beacon_lab_floor_tile_02_black', id='apron_%d' % (k + 1), uv=uv(32.0))
        box(m, [a0, cy1 - 46.0, 1.35, a1, cy1 - 26.0, 1.9], 'w/fac_rubber_mat_black', id='mat_%d' % (k + 1))
        box(m, [a0 - 4.0, cy1 - 24.0, 0.0, a1 + 4.0, cy1 - 20.0, 1.8], 'w/metal_painted_scratched_yellow', id='threshold_%d' % (k + 1))
    for k in range(7):                                                      # drain strips
        x = cx0 + 120.0 + rng.uniform(0.0, 1500.0)
        y = rng.choice((3560.0, 3780.0, 4020.0, 4250.0))
        box(m, [x, y, 0.0, x + rng.uniform(90.0, 150.0), y + 8.0, 1.45], 'w/metal_deck_painted_black_01', id='drain_%d' % k)
    for k in range(8):                                                      # patches of bare concrete where the tile is gone
        x, y = rng.uniform(cx0 + 40.0, cx1 - 200.0), rng.uniform(cy0 + 40.0, cy1 - 200.0)
        pw, ph = rng.uniform(40.0, 90.0), rng.uniform(30.0, 70.0)
        if FLOOR_SLABS:
            box(m, [x, y, 0.0, x + pw, y + ph, 1.15], 'w/aq_stone_concrete_patch02', id='patch_%d' % k, uv=uv(32.0))
    for k in range(10):                                                     # puddles are decals (a glossy box drew black: FE9)
        soft_stain(m, k, 'w/dirt_stain_water_drips_01', (rng.uniform(cx0 + 60.0, cx1 - 200.0), rng.choice((3640.0, 3760.0, 4000.0, 4120.0, 4200.0)) + rng.uniform(-20.0, 20.0), 1.97), (rng.uniform(60.0, 110.0), rng.uniform(40.0, 80.0)), rng.uniform(0, 360), 'puddle_%d' % k)
    for k in range(6):
        x = cx0 + 160.0 + k * 300.0
        box(m, [x - 1.0, cy0, 0.0, x + 1.0, cy1, 1.75], DARK, id='joint_%d' % k)
    for k in range(26):                                                     # wear decals
        soft_stain(m, k, ('w/dirt_stain_water_drips_01', 'w/wall_stain_01_dec', 'w/dirt_stain_water_drips_01')[k % 3],
                   (rng.uniform(cx0 + 60.0, cx1 - 60.0), rng.uniform(cy0 + 60.0, cy1 - 60.0), 1.95), (rng.uniform(40.0, 90.0), rng.uniform(36.0, 80.0)),
                   rng.uniform(0, 360), 'wear_%d' % k)
    report['floor'] = {'materials': ['gray glossy tile', 'wet asphalt', 'bare concrete', 'ceramic apron', 'black tile border', 'deck drain'], 'pieces': n}


def wall_bands4(A, m, D, report):
    wall_bands(A, m, D, report)                       # the wainscot (A.WALLBAND), kick plate, rail, pilasters, grime strips
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    # a painted stripe over the tile, a second one under the ceiling, on both walls (piers of the north wall only)
    box(m, [cx0, cy0 + 2.0, 106.0, cx1, cy0 + 3.5, 118.0], 'w/concrete_painted_wall_green', id='stripe_s')
    box(m, [cx0, cy0 + 2.0, 196.0, cx1, cy0 + 3.5, 204.0], 'w/plastic_slick_floor_01_orange', id='stripe_s2')
    ap = [A.aperture(i) for i in range(5)]
    x = cx0
    for k, (a0, a1) in enumerate(ap + [(cx1 + 8.0, cx1 + 8.0)]):
        x1 = a0 - 8.0
        if x1 - x > 8.0:
            box(m, [x, cy1 - 3.5, 106.0, x1, cy1 - 2.0, 118.0], 'w/concrete_painted_wall_green', id='stripe_n%d' % k)
        x = a1 + 8.0


def wall_bands(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    ap = [A.aperture(i) for i in range(5)]
    # north wall: only the piers (the apertures are open)
    segs_n = []
    x = cx0
    for a0, a1 in ap:
        segs_n.append((x, a0 - 8.0))
        x = a1 + 8.0
    segs_n.append((x, cx1))
    for k, (x0, x1) in enumerate(segs_n):
        if x1 - x0 < 8:
            continue
        box(m, [x0, cy1 - 2.0, 0.0, x1, cy1, 100.0], A.WALLBAND, id='band_n%d' % k, uv={'south': {'tile': [64.0, 64.0]}})
        box(m, [x0, cy1 - 4.0, 0.0, x1, cy1 - 2.0, 40.0], DARKMETAL, id='wain_n%d' % k)
        box(m, [x0, cy1 - 5.0, 0.0, x1, cy1 - 2.0, 6.0], BLACK, id='kick_n%d' % k)
        box(m, [x0, cy1 - 5.0, 40.0, x1, cy1 - 2.0, 44.0], RUBBER, id='bump_n%d' % k)
        box(m, [x0, cy1 - 4.0, 100.0, x1, cy1 - 2.0, 104.0], BLACK, id='rail_n%d' % k)
    # south wall: whole length: the wall band (the calibration run: five candidates), the wainscot, the kick plate
    if CAL:
        cands = ['w/concrete_wall_01_stained', 'w/concrete_wall_12_lined_dirty', 'w/plaster_wall_04_grey_dark_01', 'w/fac_tile_black_01', 'w/clk_concrete_bunker_dark']
        step = (cx1 - cx0) / 5.0
        for k, mat in enumerate(cands):
            box(m, [cx0 + k * step, cy0, 0.0, cx0 + (k + 1) * step, cy0 + 2.0, 100.0], mat, id='band_s%d' % k, uv={'north': {'tile': [64.0, 64.0]}})
        report['band_candidates'] = cands
    else:
        box(m, [cx0, cy0, 0.0, cx1, cy0 + 2.0, 100.0], A.WALLBAND, id='band_s', uv={'north': {'tile': [64.0, 64.0]}})
    box(m, [cx0, cy0 + 2.0, 0.0, cx1, cy0 + 4.0, 40.0], DARKMETAL, id='wain_s')
    box(m, [cx0, cy0 + 2.0, 0.0, cx1, cy0 + 5.0, 6.0], BLACK, id='kick_s')
    box(m, [cx0, cy0 + 2.0, 40.0, cx1, cy0 + 5.0, 44.0], RUBBER, id='bump_s')
    box(m, [cx0, cy0 + 2.0, 100.0, cx1, cy0 + 4.0, 104.0], BLACK, id='rail_s')
    # pilasters: one on every pier of the north wall, three between the south fronts (render only, 10 proud)
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        w = 40.0 if b - a > 60.0 else 28.0
        box(m, [mid - w / 2.0, cy1 - 10.0, 0.0, mid + w / 2.0, cy1, 232.0], 'w/concrete_wall_panel_01', id='pil_n%d' % k)
        box(m, [mid - w / 2.0 - 2.0, cy1 - 12.0, 0.0, mid + w / 2.0 + 2.0, cy1, 12.0], BLACK, id='pil_nb%d' % k)
        box(m, [mid - w / 2.0 - 2.0, cy1 - 12.0, 220.0, mid + w / 2.0 + 2.0, cy1, 232.0], BLACK, id='pil_nc%d' % k)
        foot(D, mid - w / 2.0, cy1 - 12.0, mid + w / 2.0, cy1)
    for k, x in enumerate((-2530.0, -2176.0, -1900.0)):
        box(m, [x - 20.0, cy0, 0.0, x + 20.0, cy0 + 10.0, 232.0], 'w/concrete_wall_panel_01', id='pil_s%d' % k)
        box(m, [x - 22.0, cy0, 0.0, x + 22.0, cy0 + 12.0, 12.0], BLACK, id='pil_sb%d' % k)
        box(m, [x - 22.0, cy0, 220.0, x + 22.0, cy0 + 12.0, 232.0], BLACK, id='pil_sc%d' % k)
        foot(D, x - 22.0, cy0, x + 22.0, cy0 + 12.0)
    # the grime line where the wall meets the floor: dark, ragged strips on the floor along both walls
    rng = random.Random(21)
    x = cx0 + 30.0
    k = 0
    while x < cx1 - 60.0:
        w = rng.uniform(60.0, 160.0)
        box(m, [x, cy0 + 5.0, 0.0, min(x + w, cx1), cy0 + 5.0 + rng.uniform(5.0, 12.0), 1.7], 'w/fac_rubber_mat_black', id='grime_s%d' % k)
        box(m, [x + rng.uniform(0.0, 40.0), cy1 - 5.0 - rng.uniform(5.0, 12.0), 0.0, min(x + w, cx1), cy1 - 5.0, 1.7], 'w/fac_rubber_mat_black', id='grime_n%d' % k)
        x += w + rng.uniform(30.0, 120.0)
        k += 1


def foot(D, x0, y0, x1, y1):
    """a footprint of geometry the props must not stand in"""
    D.boxes.append((x0, y0, x1, y1))


def fronts_and_doors(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    heads = ('w/plaster_wall_04_grey_dark_01', 'w/plaster_wall_04_grey_dark_02', 'w/plaster_wall_04_grey_dark_01')
    for k, (x0, x1) in enumerate(FRONTS):
        yv = cy0
        box(m, [x0 - 6.0, yv, 0.0, x1 + 6.0, yv + 5.0, 134.0], BLACK, id='front_frame_%d' % k)
        B.box(m, [x0, yv + 5.0, 0.0, x1, yv + 9.0, 124.0], A.SHUTTER, id='front_shutter_%d' % k)
        box(m, [x0 - 6.0, yv, 134.0, x1 + 6.0, yv + 8.0, 168.0], heads[k], id='front_header_%d' % k)
        box(m, [x0, yv + 8.0, 140.0, x1, yv + 9.0, 160.0], 'w/metal_painted_04', id='front_sign_dead_%d' % k)
    hx0, hx1 = HATCH
    box(m, [hx0 - 8.0, cy0, 0.0, hx1 + 8.0, cy0 + 8.0, 112.0], BLACK, id='hatch_frame')
    box(m, [hx0, cy0 + 8.0, 44.0, hx1, cy0 + 10.0, 100.0], DARKMETAL, id='hatch_dark')
    B.box(m, [hx0 - 8.0, cy0 + 8.0, 40.0, hx1 + 8.0, cy0 + 30.0, 46.0], 'w/wood_antique_panel_trim_01', id='hatch_sill')
    for k, bb in enumerate(([cx1 - 4.0, A.DOOR_Y0 - 8.0, 0.0, cx1, A.DOOR_Y0, A.DOOR_Z + 8.0], [cx1 - 4.0, A.DOOR_Y1, 0.0, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0],
                            [cx1 - 4.0, A.DOOR_Y0 - 8.0, A.DOOR_Z, cx1, A.DOOR_Y1 + 8.0, A.DOOR_Z + 8.0])):
        box(m, bb, BLACK, id='d4_frame_%d' % k)
    box(m, [cx1 - 8.0, A.DOOR_Y0, A.DOOR_Z - 20.0, cx1 - 4.0, A.DOOR_Y1, A.DOOR_Z - 4.0], 'w/metal_painted_scratched_yellow', id='d4_stripe')
    xw = cx0
    zt = 176.0
    box(m, [xw, 3774.0, 0.0, xw + 14.0, 3794.0, zt + 12.0], BLACK, id='d7_post_l')
    box(m, [xw, 4006.0, 0.0, xw + 14.0, 4026.0, zt + 12.0], BLACK, id='d7_post_r')
    box(m, [xw, 3774.0, zt, xw + 14.0, 4026.0, zt + 12.0], BLACK, id='d7_head')
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 4006.0, zt], DARKMETAL, id='d7_slab')
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 12.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    box(m, [xw + 10.0, 3790.0, 88.0, xw + 13.0, 4010.0, 96.0], 'w/metal_painted_scratched_yellow_02', id='d7_band')
    for k, y in enumerate((3808.0, 3900.0, 3992.0)):
        box(m, [xw + 10.0, y - 3.0, 150.0, xw + 13.0, y + 3.0, 156.0], 'w/metal_painted_02', id='d7_bolt_%d' % k)
    box(m, [xw + 10.0, 3880.0, 40.0, xw + 12.0, 3920.0, 70.0], 'w/metal_painted_scratched_yellow_02', id='d7_plate')
    # the sign box over every shop front (render only): a black frame and a lit face in the shop's hue
    for k in range(5):
        a0, a1 = A.aperture(k)
        box(m, [a0 - 14.0, cy1 - 16.0, 214.0, a1 + 14.0, cy1, 232.0], BLACK, id='beam_%d' % (k + 1))
        box(m, [a0, cy1 - 12.0, 150.0, a1, cy1, 190.0], BLACK, id='sign_frame_%d' % (k + 1))
        hue = HUE[A.BAYS[k]]
        B.sign(m, at=((a0 + a1) / 2.0, cy1 - 12.0, 170.0), normal=(0.0, -1.0, 0.0), size=(a1 - a0 - 8.0, 32.0), text=NAMES[A.BAYS[k]], font='impact',
               color=[min(1.0, 0.35 + 0.65 * c) for c in hue], background=[0.02, 0.02, 0.03], id='sign_text_%d' % (k + 1))      # r17: a lit sign (the facade washers `light_wash_*` are its lamps, power group). Emissive it was bright with the power off and dark with it on (auto exposure)


def ceiling7(A, m, D, report):
    ceiling4(A, m, D, report)
    ceiling6(A, m, D, report)
    m.use('dressing')
    cells = []
    for layer in m.layers.values():
        for o in layer:
            if str(o['id']).startswith('panel_') and not str(o['id']).startswith('panel_rail') and o.get('kind') == 'box':
                b = o['box']
                cells.append(((b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0, o['material'] == A.PANEL_LIVE, o['id']))
    for (_, _, _, pid) in cells:
        m.remove(pid)
    n_on = 0
    for (x, y, on, _) in cells:                                          # the panel boxes become fixtures: lit ones emit in the bake, dead ones hang dark and crooked
        if on:
            put_model(D, M['fluo'], x, y, 0.0, z=176.0, emissive={'color': [1.0, 0.95, 0.82], 'strength': 4.0})
            n_on += 1
        else:
            put_model(D, M['fluo_off'], x, y, 0.0, z=176.0)
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(('sbar_', 'srod_', 'sign_arrow_', 'beam_', 'cornice_', 'beam_rib_'))]:
        m.remove(pid)
    for k in range(5):                                                   # I-beams across the front of every shop, with brackets (the beam cuboids were black slabs)
        a0, a1 = A.aperture(k)
        cx = (a0 + a1) / 2.0
        yb = A.Y1 - A.WT - 8.0
        for dx in (-96.0, 96.0):
            put_model(D, M['ibeam'], cx + dx, yb, 90.0, z=216.0)
        for dx in (-130.0, -48.0, 48.0, 130.0):
            put_model(D, M['bracket'], cx + dx, yb, 0.0, z=210.0)
    report['ceiling7'] = {'fixtures_on': n_on, 'fixtures_off': len(cells) - n_on}


def ceiling4(A, m, D, report):
    ceiling(A, m, D, report)
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    for k, y in enumerate((3556.0, 4252.0)):                                       # cable trays with hanging rods
        box(m, [cx0, y - 14.0, 216.0, cx1, y + 14.0, 219.0], 'w/metal_painted_04', id='tray_%d' % k)
        box(m, [cx0, y - 14.0, 219.0, cx1, y - 12.0, 226.0], BLACK, id='tray_lip_a%d' % k)
        box(m, [cx0, y + 12.0, 219.0, cx1, y + 14.0, 226.0], BLACK, id='tray_lip_b%d' % k)
        x = cx0 + 60.0
        while x < cx1:
            box(m, [x - 0.6, y - 0.6, 219.0, x + 0.6, y + 0.6, 256.0], BLACK, id='tray_rod_%d_%d' % (k, int(x)))
            x += 128.0
    # arrow pictograms on bars hung over the lanes (pictures: no letters)
    for k, (x, y, img) in enumerate(((-2400.0, 3690.0, 'arrow_l.png'), (-1650.0, 3690.0, 'arrow_r.png'), (-2250.0, 4130.0, 'arrow_stair.png'), (-1950.0, 4130.0, 'arrow_r.png'))):
        box(m, [x - 52.0, y - 1.5, 176.0, x + 52.0, y + 1.5, 218.0], BLACK, id='sbar_%d' % k)
        for sgn in (-1, 1):
            box(m, [x + sgn * 48.0 - 0.8, y - 0.8, 218.0, x + sgn * 48.0 + 0.8, y + 0.8, 256.0], BLACK, id='srod_%d_%d' % (k, sgn))
        for sgn in (-1, 1):
            B.sign(m, image=img, at=(x, y + sgn * 1.5, 198.0), normal=(0.0, float(sgn), 0.0), size=(96.0, 30.0), lamp=ARROW_LAMP, id='sign_arrow_%d_%d' % (k, sgn))      # r15: lit and lamped (FE62)


def ceiling(A, m, D, report):
    m.use('dressing')
    cx0, cx1, cy0, cy1 = A.X0 + A.WT, A.X1 - A.WT, A.Y0 + A.WT, A.Y1 - A.WT
    rows = [3590.0, 3745.0, 4055.0, 4210.0]                     # the middle row (y 3900) is the soffit's
    cols = [A.X0 + 100.0 + 118.0 * i for i in range(15)]
    live = {(3745.0, 13), (3745.0, 14), (4055.0, 13), (4055.0, 14),         # the east entry
            (3745.0, 6), (3745.0, 7), (4055.0, 6), (4055.0, 7),             # mid hall
            (3745.0, 0), (3745.0, 1), (4055.0, 0),                          # the west end
            (3745.0, 10)}                                                   # the single between them
    rng = random.Random(11)
    cells = [(y, ci, x) for y in rows for ci, x in enumerate(cols)]
    dead = [c for c in cells if (c[0], c[1]) not in live]
    rng.shuffle(dead)
    missing = {(c[0], c[1]) for c in dead[:8]}
    A.live, A.missing = [], []
    for (y, ci, x) in cells:
        if (y, ci) in missing:
            A.missing.append((x, y))
            continue
        on = (y, ci) in live
        box(m, [x - 40.0, y - 14.0, 178.0, x + 40.0, y + 14.0, 182.0], A.PANEL_LIVE if on else A.PANEL_DEAD, id='panel_%d_%d' % (int(y), ci))
        if on:
            A.live.append((x, y, (y, ci) == (3745.0, 10)))
    for ri, y in enumerate(rows):
        box(m, [cx0, y - 18.0, 183.0, cx1, y - 15.0, 188.0], BLACK, id='panel_rail_a_%d' % ri)
        box(m, [cx0, y + 15.0, 183.0, cx1, y + 18.0, 188.0], BLACK, id='panel_rail_b_%d' % ri)
    A.panels = len(cells) - len(A.missing)
    # the dropped soffit over the spine, 48 deep, with a black lip
    box(m, [cx0, SPINE_Y - 36.0, 208.0, cx1, SPINE_Y + 36.0, 256.0], 'w/plaster_wall_04_grey_dark_01', id='soffit')
    box(m, [cx0, SPINE_Y - 38.0, 204.0, cx1, SPINE_Y - 36.0, 256.0], BLACK, id='soffit_lip_s')
    box(m, [cx0, SPINE_Y + 36.0, 204.0, cx1, SPINE_Y + 38.0, 256.0], BLACK, id='soffit_lip_n')
    report['panels'] = {'cells': len(cells), 'missing': len(A.missing), 'live': len(A.live)}


def ceiling6(A, m, D, report):
    m.use('dressing')
    n = 0
    for prefix, mat in (('beam_', 'w/concrete_wall_panel_05'), ('shutter_box_', STEEL), ('panel_rail_', STEEL), ('soffit_lip_', STEEL), ('tray_lip_', STEEL), ('sign_frame_', STEEL)):
        n += retex(m, prefix, mat)
    m.update('soffit', material='w/ch_concretewall06') if 'soffit' in m else None
    for k in range(5):                                         # a cornice under each beam: the header reads as built, not as a slab
        a0, a1 = A.aperture(k)
        box(m, [a0 - 16.0, A.Y1 - A.WT - 18.0, 208.0, a1 + 16.0, A.Y1 - A.WT, 214.0], 'w/metal_painted_scratched_yellow_02', id='cornice_%d' % (k + 1))
        for j in range(6):
            box(m, [a0 - 14.0 + (a1 - a0 + 28.0) * j / 5.0 - 0.8, A.Y1 - A.WT - 16.0, 214.0, a0 - 14.0 + (a1 - a0 + 28.0) * j / 5.0 + 0.8, A.Y1 - A.WT, 232.0], DARK, id='beam_rib_%d_%d' % (k + 1, j))
    # neon tube round every aperture: the source of the shop's colour
    for k in range(5):
        a0, a1 = A.aperture(k)
        t = TUBE[A.BAYS[k]]
        yw = A.Y1 - A.WT
        box(m, [a0 - 8.0, yw - 3.0, A.AP_H + 2.0, a1 + 8.0, yw, A.AP_H + 6.0], t, id='neon_top_%d' % (k + 1))
        box(m, [a0 - 8.0, yw - 3.0, 0.0, a0 - 4.0, yw, A.AP_H + 2.0], t, id='neon_l_%d' % (k + 1))
        box(m, [a1 + 4.0, yw - 3.0, 0.0, a1 + 8.0, yw, A.AP_H + 2.0], t, id='neon_r_%d' % (k + 1))
    report['ceiling6'] = {'retextured': n}


def retex(m, prefix, material):
    n = 0
    for layer in list(m.layers):
        for o in list(m.layers[layer]):
            if str(o['id']).startswith(prefix) and o.get('kind') == 'box':
                m.update(o['id'], material=material)
                n += 1
    return n


def put_model(D, model, x, y, yaw, z=0.0, scale=1.0, emissive=None):
    """a stock model by its bounds' centre, no footprint check (structure)"""
    return D.put(model, x, y, yaw, z=z, scale=scale, ignore_keep=True, margin=0.0, clip=False, emissive=emissive)


def column7(A, m, D, k, x):
    """a stock column on a clip; round 4/5's face features move out to the model's faces"""
    spec = COLSPEC[k]
    B.clip(m, [x - 20.0, SPINE_Y - 20.0, 0.0, x + 20.0, SPINE_Y + 20.0, 256.0], id='col_clip_%d' % k)
    mod = M['dojo'][k % 4]
    mn, mx = D.bounds(mod)
    sc = DOJO_SCALE
    D.put(mod, x, SPINE_Y, 90.0 * (k % 4), z=0.0, scale=sc, ignore_keep=True, margin=0.0, clip=False)
    dress4_foot(D, x - 24.0, SPINE_Y - 24.0, x + 24.0, SPINE_Y + 24.0)
    half = COL_HALF                     # r17: the shaft of the stock column is 17.6 across (`studio pick` on arc_d7: face at 8.8 from the axis at z 87 to 140), not 28: boards at 15 hung 6 units off it (the blades of arc_d7, the white boxes beside the pillars)
    f = spec['feature']
    for sgn in (-1, 1):
        yf = SPINE_Y + sgn * half
        y0, y1 = (yf, yf + 1.5) if sgn > 0 else (yf - 1.5, yf)
        if f == 'map':
            box(m, [x - 8.9, y0, 88.0, x + 8.9, y1, 146.0], DARK, id='col_mapframe_%d_%d' % (k, sgn))      # r18: 26 wide stuck out 4 beyond the 17.6 shaft (the pale slabs and the purple top of arc_cutwall); 19.2
            B.decal(m, image='transit_map.png', at=(x, y1 if sgn > 0 else y0, 117.0), normal=(0.0, float(sgn), 0.0), size=(15.6, 50.0), id='col_map_%d_%d' % (k, sgn))      # r18: the stock map material read white (p98 1.0 in arc_bay1)
        elif f == 'lightbox':
            box(m, [x - 8.9, y0, 84.0, x + 8.9, y1, 150.0], DARK, id='col_lbframe_%d_%d' % (k, sgn))
            y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
            if LB_FACE:
                box(m, [x - 11.0, y2[0], 88.0, x + 11.0, y2[1], 146.0], TUBE['photo'] if sgn > 0 else TUBE['heel'], id='col_lb_%d_%d' % (k, sgn))        # r17: off (a blank white face hid the poster decal that fixtures8 puts at the same place)
        elif f in ('poster', 'poster2'):
            for j, zz in enumerate((90.0, 134.0)):
                box(m, [x - 8.9, y0, zz, x + 8.9, y1, zz + 38.0], DARK, id='col_pframe_%d_%d_%d' % (k, sgn, j))
                y2 = (y1, y1 + 0.8) if sgn > 0 else (y0 - 0.8, y0)
                box(m, [x - 8.0, y2[0], zz + 1.5, x + 8.0, y2[1], zz + 36.5], POSTERS[(k * 3 + j + (0 if sgn > 0 else 2)) % len(POSTERS)], id='col_poster_%d_%d_%d' % (k, sgn, j))
        elif f == 'extinguisher':
            D.put(M['extg'], x, SPINE_Y + sgn * (half + 4.0), 90.0 + 90.0 * sgn, z=84.0, ignore_keep=True, margin=0.0, clip=False)
    D.put(M['cage'], x + 12.0, SPINE_Y - COL_HALF - 4.0, 270.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)          # a caged lamp on the shaft: its fixture, and the reason the column is lit
    D.put(M['cage'], x - 12.0, SPINE_Y + COL_HALF + 4.0, 90.0, z=150.0, ignore_keep=True, margin=0.0, clip=False)
    if k in (1, 4):
        for (a, b, c, d) in ((x - 34.0, SPINE_Y - 34.0, x + 34.0, SPINE_Y - 32.0), (x - 34.0, SPINE_Y + 32.0, x + 34.0, SPINE_Y + 34.0),
                             (x - 34.0, SPINE_Y - 32.0, x - 32.0, SPINE_Y + 32.0), (x + 32.0, SPINE_Y - 32.0, x + 34.0, SPINE_Y + 32.0)):
            box(m, [a, b, 22.0, c, d, 26.0], 'w/metal_painted_scratched_yellow', id='guard_%d_%d_%d' % (k, int(a), int(b)))


def dress4_foot(D, x0, y0, x1, y1):
    D.boxes.append((x0, y0, x1, y1))


def spine4(A, m, D, report):
    m.use('dressing')
    for k, x in enumerate(COLS):
        column7(A, m, D, k, x)
    report['columns'] = {'placed': list(COLS), 'kinds': [c['mat'] for c in COLSPEC]}

    def hang(x, mod, yaw, y=SPINE_Y, z_bar=168.0, w=84.0):
        box(m, [x - w / 2.0, y - 1.5, z_bar, x + w / 2.0, y + 1.5, z_bar + 3.0], BLACK, id='bar_%d' % int(x))
        for s in (-1, 1):
            box(m, [x + s * (w / 2.0 - 4.0) - 1.0, y - 1.0, z_bar + 3.0, x + s * (w / 2.0 - 4.0) + 1.0, y + 1.0, 208.0], BLACK, id='rod_%d_%d' % (int(x), s))
        mn, mx = D.bounds(M.get(mod, mod))
        D.put(M.get(mod, mod), x, y, yaw, z=z_bar - (mx[2] - mn[2]) + 6.0, ignore_keep=True, margin=0.0)

    # (ii) the kiosk at the first gap, moved 105 north of the spine line: round 3's camera arc_d7 stood INSIDE it (x -2670 against the footprint -2748..-2652)
    kx, ky = GAPS[0], SPINE_Y + 105.0
    x0, x1, y0, y1 = kx - 48.0, kx + 48.0, ky - 32.0, ky + 32.0
    B.box(m, [x0, y0, 0.0, x1, y1, 44.0], 'w/wood_worn_painted_01_green', id='kiosk_base')
    box(m, [x0 - 2.0, y0 - 2.0, 44.0, x1 + 2.0, y1 + 2.0, 47.0], 'w/wood_antique_panel_trim_01', id='kiosk_counter')
    for k, (px, py) in enumerate(((x0, y0), (x1 - 4.0, y0), (x0, y1 - 4.0), (x1 - 4.0, y1 - 4.0))):
        box(m, [px, py, 47.0, px + 4.0, py + 4.0, 100.0], BLACK, id='kiosk_post_%d' % k)
    box(m, [x0, y1 - 3.0, 47.0, x1, y1, 100.0], DARKMETAL, id='kiosk_back_n')
    box(m, [x0, y0, 47.0, x1, y0 + 3.0, 100.0], DARKMETAL, id='kiosk_back_s')
    box(m, [x0 - 8.0, y0 - 8.0, 100.0, x1 + 8.0, y1 + 8.0, 106.0], 'w/metal_painted_scratched_yellow', id='kiosk_canopy')
    box(m, [x0 + 4.0, y0 - 6.0, 106.0, x1 - 4.0, y0 - 4.0, 124.0], TUBE['heel'], id='kiosk_sign_s')
    box(m, [x0 + 4.0, y1 + 4.0, 106.0, x1 - 4.0, y1 + 6.0, 124.0], TUBE['heel'], id='kiosk_sign_n')
    box(m, [x0 + 4.0, y0 - 7.0, 105.0, x1 - 4.0, y1 + 7.0, 106.0], BLACK, id='kiosk_sign_base')
    D.tops['kiosk'] = (kx, ky, 47.0, 96.0, 64.0, 0.0)
    dress4_foot(D, x0 - 8.0, y0 - 8.0, x1 + 8.0, y1 + 8.0)
    D.put(M['news'], kx - 72.0, ky - 12.0, 0.0, tag='kiosk_news_a', margin=0.0)
    D.put(M['news'], kx - 72.0, ky + 18.0, 0.0, tag='kiosk_news_b', margin=0.0)
    D.put(M['news'], kx + 72.0, ky + 4.0, 180.0, tag='kiosk_news_c', margin=0.0)
    for k, (mod, du, dv, yw) in enumerate((('register', -22.0, 14.0, 270.0), ('coffee', 14.0, 16.0, 270.0), ('mags', 28.0, -14.0, 20.0), ('stackp', -10.0, -14.0, 60.0),
                                           ('mug', 30.0, 10.0, 0.0), ('mags', -34.0, -12.0, 100.0), ('gum', 0.0, 0.0, 0.0), ('donuts', -30.0, 6.0, 30.0))):
        D.put(M[mod], kx + du, ky + dv, yw, z=47.0, ignore_keep=True, margin=0.0)
    hang(kx, 'sign1', 0.0, y=ky, z_bar=150.0)
    # the first gap of the spine itself: a floor drain grate and a wet patch (the camera arc_d7 stands here: nothing solid)
    box(m, [kx - 30.0, SPINE_Y - 14.0, 0.0, kx + 30.0, SPINE_Y + 14.0, 1.9], 'w/metal_deck_painted_black_01', id='gap0_grate')
    # (i) two subway benches back to back with a bin
    bx = GAPS[1]
    D.put(M['bench'], bx, SPINE_Y - 21.0, 90.0, tag='bench_a', margin=0.0)
    D.put(M['bench'], bx, SPINE_Y + 21.0, 270.0, tag='bench_b', margin=0.0)
    D.put(M['bin1'], bx - 118.0, SPINE_Y, 0.0, tag='bin_i', margin=0.0)
    for j, mod in enumerate(('paper', 'cup', 'mags', 'cup', 'paper', 'chips')):
        D.put(M[mod], bx + (j - 2.5) * 30.0, SPINE_Y + (-21.0 if j % 2 == 0 else 21.0), D.rng.uniform(0, 360), on='bench_a' if j % 2 == 0 else 'bench_b', margin=0.0)
    hang(bx, 'sign2', 90.0)
    # (iii) a planter box with plants and litter
    px = GAPS[2]
    B.box(m, [px - 60.0, SPINE_Y - 20.0, 0.0, px + 60.0, SPINE_Y + 20.0, 34.0], 'w/concrete_wall_01_stained', id='planter_box')
    box(m, [px - 62.0, SPINE_Y - 22.0, 34.0, px + 62.0, SPINE_Y + 22.0, 38.0], BLACK, id='planter_rim')
    box(m, [px - 56.0, SPINE_Y - 16.0, 38.0, px + 56.0, SPINE_Y + 16.0, 39.0], 'w/dirt_stain_leaking_01', id='planter_soil')
    dress4_foot(D, px - 62.0, SPINE_Y - 22.0, px + 62.0, SPINE_Y + 22.0)
    D.tops['planter'] = (px, SPINE_Y, 39.0, 120.0, 40.0, 0.0)
    for j, du in enumerate((-44.0, -14.0, 16.0, 46.0)):                    # four different plants (round 3 had three identical)
        D.put((M['plant'], M['planter2'], 'flower_shop_planter_02', M['plant'])[j], px + du, SPINE_Y + (4.0 if j % 2 else -4.0), D.rng.uniform(0, 360), z=39.0, ignore_keep=True, margin=0.0,
              scale=(1.0, 0.8, 1.2, 1.1)[j])
    for j in range(6):
        D.put(D.rng.choice((M['cup'], M['chips'], M['paper'], M['smokes'], M['can'])), px + D.rng.uniform(-80.0, 80.0), SPINE_Y + D.rng.uniform(-34.0, 34.0), D.rng.uniform(0, 360), margin=0.0)
    hang(px, 'sign4', 90.0)
    # (iv) a pay phone pair on the column at x = -1950, a transit map case and a newspaper box beside it
    cxp = COLS[3]
    D.put(M['phone'], cxp + 16.0 + 13.0, SPINE_Y, 0.0, tag='ph_e', margin=0.0)
    D.put(M['phone'], cxp - 16.0 - 13.0, SPINE_Y, 180.0, tag='ph_w', margin=0.0)
    D.put(M['case'], GAPS[3], SPINE_Y, 0.0, tag='mapcase_i', margin=0.0)
    D.put(M['news'], GAPS[3] + 60.0, SPINE_Y - 16.0, 180.0, tag='news_iv', margin=0.0)
    D.put(M['bin2'], GAPS[3] - 60.0, SPINE_Y + 14.0, 0.0, tag='bin_iv', margin=0.0)
    D.put(M['ftable'], GAPS[3] + 20.0, SPINE_Y + 36.0, 90.0, tag='tbl_iv', margin=0.0)
    for j, mod in enumerate(('mags', 'cup', 'paper')):
        D.on('tbl_iv', M[mod], (j - 1) * 20.0, 0.0, D.rng.uniform(0, 360))
    # (v) the floor buffer with wet floor signs and a cable
    fx = GAPS[4]
    D.put(M['buffer'], fx, SPINE_Y, 20.0, tag='buffer', margin=0.0)
    D.put(M['wet'], fx - 70.0, SPINE_Y - 22.0, 30.0, tag='wet_a', margin=0.0)
    D.put(M['wet'], fx + 70.0, SPINE_Y + 24.0, 200.0, tag='wet_b', margin=0.0)
    D.put(M['mop'], fx + 40.0, SPINE_Y + 30.0, 80.0, tag='mop', margin=0.0)
    D.put(M['bucket'], fx + 62.0, SPINE_Y + 34.0, 10.0, tag='bucket_v', margin=0.0)
    D.put(M['cone'], fx - 100.0, SPINE_Y + 10.0, 0.0, tag='cone_v', margin=0.0)
    pts = [(fx + 28.0, SPINE_Y - 4.0), (fx + 60.0, SPINE_Y - 30.0), (fx + 110.0, SPINE_Y - 22.0), (fx + 140.0, SPINE_Y + 20.0), (fx + 190.0, SPINE_Y + 40.0)]
    for k in range(len(pts) - 1):
        (ax, ay), (bx2, by2) = pts[k], pts[k + 1]
        box(m, [min(ax, bx2) - 1.5, min(ay, by2) - 1.5, 0.0, max(ax, bx2) + 1.5, max(ay, by2) + 1.5, 3.0], 'w/fac_rubber_mat_black', id='cable_%d' % k)
    hang(fx, 'sign4', 90.0, z_bar=172.0)


def kiosk7(A, m, D, report):
    m.use('dressing')
    kx, ky = GAPS[0], SPINE_Y + 105.0
    gone = 0
    for prefix in ('kiosk_base', 'kiosk_counter', 'kiosk_post_', 'kiosk_back_', 'kiosk_canopy', 'kiosk_sign_', 'kseam_', 'kvert_', 'kmenu_', 'kapron', 'kcanopy_trim', 'k_', 'bar_%d' % int(kx), 'rod_%d' % int(kx)):
        gone += drop(m, prefix)
    # the old counter props at z 47 are re-placed on two stock concession carts face to face (their top is 55: the ticket booth model turned out to be a bumper car)
    old = [o['id'] for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and abs(o['origin'][0] - kx) < 62.0 and abs(o['origin'][1] - ky) < 40.0 and 40.0 < o['origin'][2] < 52.0]
    for pid in old:
        m.remove(pid)
    D.put(M['cart2'], kx, ky - 26.0, 90.0, tag='kcart_a', ignore_keep=True, margin=0.0)
    D.put(M['cart2'], kx, ky + 26.0, 270.0, tag='kcart_b', ignore_keep=True, margin=0.0)
    for k, (mod, du, dv, yw) in enumerate((('register', -20.0, 0.0, 270.0), ('coffee', 16.0, 0.0, 270.0), ('mags', 34.0, 10.0, 20.0), ('donuts', -36.0, -8.0, 30.0), ('mug', 0.0, 0.0, 0.0))):
        D.put(M[mod], kx + du, ky + (-26.0 if k % 2 == 0 else 26.0) + dv, yw, z=55.0, ignore_keep=True, margin=0.0, clip=False)
    for dx, dy in ((-58.0, -50.0), (58.0, -50.0), (-58.0, 50.0), (58.0, 50.0)):         # the striped awning on four I-beam posts
        put_model(D, M['post'], kx + dx, ky + dy, 0.0, z=0.0, scale=0.85)
    put_model(D, M['awning'], kx, ky, 0.0, z=100.0, scale=1.0)
    put_model(D, M['cage'], kx, ky, 0.0, z=94.0)
    dress4_foot(D, kx - 74.0, ky - 56.0, kx + 74.0, ky + 56.0)
    report['kiosk7'] = {'removed_box_parts': gone, 'models': ['concession cart x2', 'awning', 'post x4', 'cage lamp']}


def drop(m, prefix):
    n = 0
    for pid in [o['id'] for layer in m.layers.values() for o in layer if str(o['id']).startswith(prefix)]:
        m.remove(pid)
        n += 1
    return n


def d7_6(A, m, D, report):
    m.use('dressing')
    xw = A.X0 + A.WT
    zt = 176.0
    for pid in ('d7_slab', 'd7_foot', 'd7_band', 'd7_plate', 'd7_lamp', 'd7_label'):
        if pid in m:
            m.remove(pid)
    drop(m, 'd7_bolt_')
    drop(m, 'd7_seam_')
    drop(m, 'd7_hseam_')
    # two leaves of two materials, the right one with a wheel and a pressure plate, the left one with plate seams only: nothing mirrors
    box(m, [xw + 2.0, 3794.0, 0.0, xw + 10.0, 3902.0, zt], 'w/frag_metal_plates_rusty', id='d7_slab', uv={'east': {'tile': [64.0, 64.0]}})
    box(m, [xw + 2.0, 3902.0, 0.0, xw + 10.0, 4006.0, zt], 'w/beacon_metal_panel_wall', id='d7_slab_r', uv={'east': {'tile': [40.0, 40.0]}})
    for z in (36.0, 92.0, 140.0):
        box(m, [xw + 10.0, 3794.0, z, xw + 11.2, 3902.0, z + 2.0], DARK, id='d7_hseam_%d' % int(z))
    for k, y in enumerate((3818.0, 3846.0, 3880.0)):
        box(m, [xw + 10.0, y, 8.0, xw + 11.2, y + 2.0, zt - 6.0], DARK, id='d7_seam_%d' % k)
    box(m, [xw + 10.0, 3902.0, 0.0, xw + 12.0, 3904.0, zt], DARK, id='d7_split')
    # the wheel (a ring of boxes) and the bolts on the right leaf
    cy, cz = 3954.0, 92.0
    if D7_WHEEL:                       # r17: off (a ring of eight 6-unit boxes, a hub and five bolts drew as a pixelated black, yellow and white checker patch on the panel wall in arc_bay1, 3/3 reviewers)
        for a in range(0, 360, 45):
            r = math.radians(a)
            box(m, [xw + 10.0, cy + 18.0 * math.cos(r) - 3.0, cz + 18.0 * math.sin(r) - 3.0, xw + 15.0, cy + 18.0 * math.cos(r) + 3.0, cz + 18.0 * math.sin(r) + 3.0], 'w/metal_painted_scratched_yellow_02', id='d7_wheel_%d' % a)
        box(m, [xw + 10.0, cy - 4.0, cz - 4.0, xw + 17.0, cy + 4.0, cz + 4.0], DARK, id='d7_hub')
        for k, (dy, dz) in enumerate(((-34.0, 40.0), (34.0, 40.0), (-34.0, 140.0), (34.0, 140.0), (0.0, 150.0))):
            box(m, [xw + 10.0, cy + dy - 3.0, dz - 3.0, xw + 13.0, cy + dy + 3.0, dz + 3.0], STEEL, id='d7_nut_%d' % k)
    box(m, [xw + 10.0, 3820.0, 108.0, xw + 11.5, 3860.0, 120.0], 'w/signage_decals_corridor_01', id='d7_label')
    box(m, [xw + 10.0, 3981.0, 148.0, xw + 14.0, 3995.0, 162.0], TUBE['needle'], id='d7_lamp')
    box(m, [xw + 10.0, 3794.0, 0.0, xw + 12.0, 4006.0, 12.0], 'w/metal_painted_scratched_yellow', id='d7_foot')
    for z, mat in ((88.0, 'w/metal_painted_scratched_yellow_02'),):
        box(m, [xw + 10.0, 3790.0, z, xw + 13.0, 3902.0, z + 10.0], mat, id='d7_band')
    box(m, [xw + 9.0, 3788.0, 0.0, xw + 14.0, 3794.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_l')
    box(m, [xw + 9.0, 4006.0, 0.0, xw + 14.0, 4012.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_r')
    box(m, [xw + 9.0, 3788.0, zt, xw + 14.0, 4012.0, zt + 10.0], 'w/metal_painted_scratched_yellow', id='d7_frame_t')
    # the pillar's foot (the pillar stands 180 in front of the door): crates, barrels, sandbags, a hose, a leaning plank
    cx = COLS[0]
    rng = random.Random(99)
    D.put(M['crate3'], cx - 46.0, SPINE_Y - 22.0, 12.0, margin=0.0, ignore_keep=True)
    D.put(M['crate2'], cx - 44.0, SPINE_Y - 20.0, 30.0, z=49.0, margin=0.0, ignore_keep=True, clip=False)
    D.put(M['barrel2'], cx - 40.0, SPINE_Y + 34.0, 0.0, margin=0.0, ignore_keep=True)
    D.put(M['barrel3'], cx - 6.0, SPINE_Y + 46.0, 0.0, margin=0.0, ignore_keep=True)
    for k in range(5):
        D.put(M['sandbag'] if k % 2 else M['sandbag2'], cx + 26.0 + 8.0 * (k % 2), SPINE_Y - 30.0 + 14.0 * k, rng.uniform(0, 360), z=8.0 * (k // 3), margin=0.0, ignore_keep=True, clip=False)
    D.put(M['hose'], cx + 6.0, SPINE_Y - 44.0, 20.0, margin=0.0, ignore_keep=True, clip=False)
    D.put(M['wet'], cx - 70.0, SPINE_Y + 6.0, 80.0, margin=0.0, ignore_keep=True, clip=False)
    tp(D, 'com_wooden_pallet', cx + 40.0, SPINE_Y + 2.0, 12.0, 90.0, roll=-76.0)
    for k in range(7):
        D.put(rng.choice((M['cup'], M['can'], M['paper'], M['chips'])), cx + rng.uniform(-70.0, 60.0), SPINE_Y + rng.uniform(-60.0, 60.0), rng.uniform(0, 360), margin=0.0, ignore_keep=True, clip=False)
    # the end wall each side of the door (as round 5) and the pipes
    for s in (-1, 1):
        for z in (60.0, 124.0):
            y0, y1 = (4012.0, A.Y1 - A.WT) if s > 0 else (A.Y0 + A.WT, 3788.0)
            box(m, [xw, y0, z, xw + 5.0, y1, z + 5.0], 'w/metal_painted_scratched_yellow_02' if z < 100 else STEEL, id='d7_pipe_%d_%d' % (s, int(z)))
    for s, (y0, y1) in enumerate(((A.Y0 + A.WT + 20.0, 3770.0), (4030.0, A.Y1 - A.WT - 20.0))):
        mid = (y0 + y1) / 2.0
        box(m, [xw, mid - 40.0, 70.0, xw + 3.0, mid + 40.0, 160.0], 'w/wood_antique_panel_trim_01', id='d7_board_%d' % s)
        for j, (dy, dz) in enumerate(((-24.0, 120.0), (6.0, 128.0), (28.0, 104.0), (-8.0, 92.0))):
            B.decal(m, POSTERS[(s * 3 + j) % len(POSTERS)], (xw + 3.0, mid + dy, dz), (1.0, 0.0, 0.0), (22.0, 30.0), rot=(-3.0, 4.0, 1.0, 6.0)[j], id='d7_notice_%d_%d' % (s, j))
        box(m, [xw, y0, 0.0, xw + 1.5, y1, 40.0], 'w/ceramic_tile_01_orange', id='d7_wain_%d' % s)
        box(m, [xw, y0, 40.0, xw + 2.0, y1, 43.0], DARK, id='d7_rail_%d' % s)
    D.wall(M['lockers'], 'w', 3560.0, tag='d7_lock0')
    D.wall(M['lockers'], 'w', 3585.0, tag='d7_lock1')
    D.wall(M['fcab'], 'w', 4230.0, tag='d7_fcab')
    D.wall(M['bench'], 'w', 4180.0, tag='d7_bench')
    report['d7'] = 'two leaves of two materials, a wheel, a hazard frame, the pillar foot piled'


def tp(D, model, x, y, z, yaw, pitch=0.0, roll=0.0, scale=1.0):
    """a prop at a free angle (toppled, leaning): placed directly, no footprint check"""
    D.m.use('dressing')
    B.prop(D.m, model, (round(x, 2), round(y, 2), round(z, 2)), angles=[pitch, yaw, roll], scale=scale, zone='arcade')
    D.n += 1


def wall_props(A, m, D):
    # south wall west to east
    for k, x in enumerate((-2955.0, -2918.0)):
        D.wall(M['soda'], 's', x, tag='vend%d' % k)
    for k in range(4):
        D.wall(M['phone'], 's', -2840.0 + 34.0 * k, tag='phone%d' % k)
    D.wall(M['steel'], 's', -2165.0, tag='lp_sh1')
    D.wall(M['steel'], 's', -1995.0, tag='lp_sh2')
    for k in range(3):
        D.wall(M['locker'], 's', -2310.0 - 20.0 * k, tag='lock%d' % k)
    D.wall(M['case'], 's', -1640.0, tag='mapcase')
    D.wall(M['bin1'], 's', -2700.0, tag='bin_s0')
    D.wall(M['bin2'], 's', -2060.0, tag='bin_s1')
    D.wall(M['bin1'], 's', -1560.0, tag='bin_s2')
    D.wall(M['news'], 's', -2670.0, tag='news_s0')
    D.wall(M['turn'], 's', -1275.0, tag='turn0')
    D.wall(M['turn'], 's', -1240.0, tag='turn1')
    D.wall(M['bench'], 's', -2350.0, tag='bench_s0')
    D.wall(M['bench'], 's', -1960.0, tag='bench_s1')
    D.wall(M['wet'], 's', -2330.0, tag='wet_s')
    # north piers
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        if k in (1, 3, 4):
            D.wall(M['news'], 'n', mid - 20.0, tag='pier_news%da' % k)
            D.wall(M['news'], 'n', mid + 22.0, tag='pier_news%db' % k)
        if k in (0, 2):
            D.wall(M['bin1'], 'n', mid, tag='pier_bin%d' % k)
        if k == 2:
            D.wall(M['phone'], 'n', mid + 28.0, tag='pier_phone')
    D.wall(M['bin2'], 'n', -1250.0, tag='pier_bin5')
    D.wall(M['news'], 'n', -1330.0, tag='pier_news5')
    # the two caged wall lamps of the south wall (over the wall buys)
    for k, x in enumerate((-2560.0, -1860.0)):
        D.put(M['lamp'], x, A.Y0 + A.WT + 8.0, 90.0, z=140.0, scale=3.0, ignore_keep=True, margin=0.0, emissive={'color': [1.0, 0.72, 0.38], 'strength': 4.0})
        box(m, [x - 10.0, A.Y0 + A.WT, 128.0, x + 10.0, A.Y0 + A.WT + 4.0, 160.0], BLACK, id='lamp_plate_%d' % k)
    # the wall decals: stains (few and large, near the walls) and a pair of old bills on the south wall
    for k in range(10):
        x = A.X0 + 120.0 + k * 170.0
        wy = (A.Y0 + A.WT + 30.0) if k % 2 == 0 else (A.Y1 - A.WT - 40.0)
        soft_stain(m, k, 'w/asphalt_flooring_stain_01' if k % 3 else 'w/fac_darkstain_01_dec', (x + D.rng.uniform(-30, 30), wy + D.rng.uniform(-8, 8), 1.8), (110.0, 110.0), D.rng.uniform(0, 360), 'decal_floor_%d' % k)
    for k in range(10):
        x = A.X0 + 80.0 + k * 175.0
        B.decal(m, ('w/plaster_damaged_11_crack_dec', 'w/dirt_stain_water_drips_01', 'w/wall_stain_01_dec')[k % 3], (x, A.Y0 + A.WT, D.rng.uniform(110.0, 170.0)), (0.0, 1.0, 0.0),
                (D.rng.uniform(50.0, 80.0), D.rng.uniform(50.0, 80.0)), id='decal_wall_%d' % k)


def d7_props(A, D):
    xw = A.X0 + A.WT
    D.put(M['valve'], xw + 14.0, 3790.0, 90.0, z=60.0, ignore_keep=True, margin=0.0)
    D.put(M['warn'], xw + 4.0, 3764.0, 0.0, z=100.0, ignore_keep=True, margin=0.0)


def ceiling_props(A, D):
    k = 0
    for line, y in enumerate((3640.0, 4180.0)):
        x = A.X0 + 80.0
        while x < A.X1 - 80.0:
            D.ceil(M['pipe'], x, y, 90.0, 236.0)
            x += 128.0
            k += 1
    x = A.X0 + 100.0
    while x < A.X1 - 90.0:
        D.ceil(M['duct'], x, 3822.0, 90.0, 230.0)
        x += 256.0
    for j, (x, y) in enumerate(A.missing):
        D.ceil(M['wire'] if j % 2 else M['wire2'], x, y, 0.0, 208.0)


def ducts7(A, m, D):
    for line, y in enumerate((3770.0, 4010.0)):
        x = A.X0 + 100.0 + 128.0 * line
        k = 0
        while x < A.X1 - 90.0:
            D.ceil(M['duct'] if k % 2 == 0 else M['duct_r'], x, y, 90.0, 230.0 if k % 2 == 0 else 226.0)
            put_model(D, M['duct_sup'], x, y, 90.0, z=218.0)
            if k % 3 == 1:
                put_model(D, M['duct_vent'], x + 20.0, y, 0.0, z=205.0)
            k += 1
            x += 128.0
        put_model(D, M['duct_elb'], A.X1 - 70.0, y, 0.0, z=205.0)


def stories5(A, m, D, report):
    m.use('dressing')
    rng = D.rng
    bank = []
    for k in range(5):
        bank.append(D.wall(M['arcade'] if k % 2 == 0 else M['arcade2'], 's', -2700.0 + 38.0 * k, tag='cab%d' % k))
    D.wall(M['claw'], 's', -2500.0, tag='claw0')
    D.wall(M['gum'], 's', -2530.0, tag='gum0')
    D.wall(M['gum'], 's', -2160.0, tag='gum1')
    D.wall(M['claw'], 's', -1250.0, tag='claw1')
    D.wall(M['dump'], 's', -2020.0, tag='dump_s')

    def cluster(x, y, n, r, kinds, lane=False):
        k = 0
        for _ in range(n):
            ang = rng.uniform(0.0, 6.283)
            rr = abs(rng.gauss(0.0, r))
            if D.put(rng.choice(kinds), x + math.cos(ang) * rr, y + math.sin(ang) * rr, rng.uniform(0, 360), margin=0.5, clip=False, ignore_keep=lane):
                k += 1
        return k
    small = [M['cup'], M['can'], M['paper'], M['chips'], M['smokes'], M['mug']]
    # 1. a wet patch in the south lane with its sign, mop and bucket, drips of litter and a trail of cups
    D.put(M['wet'], -2455.0, 3702.0, 20.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['mopb'], -2380.0, 3696.0, 70.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['mop'], -2368.0, 3712.0, 10.0, margin=0.0, clip=False, ignore_keep=True)
    cluster(-2430.0, 3680.0, 5, 28.0, small, True)
    # 2. a newspaper bundle at the kiosk: a tied stack, loose sheets, a cold cup on the step
    kx, ky = GAPS[0], SPINE_Y + 105.0
    D.put(M['stackp'], kx + 70.0, ky - 52.0, 15.0, margin=0.0, clip=False)
    D.put(M['stackp'], kx + 70.0, ky - 52.0, 40.0, z=6.0, margin=0.0, clip=False, ignore_keep=True)
    cluster(kx + 82.0, ky - 70.0, 6, 22.0, [M['paper'], M['paper'], M['mags']])
    D.put(M['cup'], kx - 30.0, ky - 48.0, 0.0, margin=0.0, clip=False)
    # 3. a fallen chair group and an upset table in the north band
    tp(D, M['fchair'], -2015.0, 4062.0, 12.0, 30.0, roll=90.0)
    tp(D, M['fchair'], -1990.0, 4040.0, 12.0, 120.0, roll=88.0)
    D.put(M['fchair'], -1962.0, 4072.0, 200.0, margin=0.0, clip=False)
    tp(D, M['ftable'], -2040.0, 4025.0, 16.0, 70.0, roll=80.0)
    cluster(-2000.0, 4050.0, 5, 30.0, small)
    # 4. a stall that lost a crate: goods on the floor round it
    sx, sy = -1860.0, 3790.0
    D.put(M['ftable'], sx, sy, 0.0, tag='stallA', margin=2.0)
    for j in range(3):
        D.on('stallA', rng.choice((M['crackers'], M['donuts'], M['mug'])), (j - 1) * 20.0, 0.0, rng.uniform(0, 360))
    tp(D, M['crate1'], sx + 48.0, sy + 10.0, 12.0, 40.0, roll=90.0)
    cluster(sx + 60.0, sy + 6.0, 9, 26.0, [M['crackers'], M['donuts'], M['boxc'], M['mug'], M['chips']])
    # 5. a second stall, tidy, with its chair and a rolled-up awning pole
    D.put(M['ftable'], -2280.0, 3770.0, 90.0, tag='stallB', margin=2.0)
    for j in range(4):
        D.on('stallB', rng.choice((M['mags'], M['cup'], M['boxc'], M['books'])), 0.0, (j - 1.5) * 16.0, rng.uniform(0, 360))
    D.put(M['fchair'], -2240.0, 3772.0, 180.0, margin=0.5)
    D.put(M['cart2'], -1420.0, 3800.0, 110.0, tag='cart1', margin=2.0)
    # 6. an overflowing bin on the south wall: bags slumped, cans round it
    D.wall(M['bin1'], 's', -2800.0, tag='bin_over')
    for j in range(3):
        D.put(M['bag'], -2800.0 + rng.uniform(-30.0, 30.0), 3548.0 + rng.uniform(6.0, 28.0), rng.uniform(0, 360), scale=0.7, margin=0.0, clip=False)
    cluster(-2800.0, 3560.0, 6, 24.0, [M['can'], M['chips'], M['paper']])
    # 7. a barrier with a cone missing and a dropped tape: the north band, mid hall
    D.put(M['barrier2'], -1700.0, 4098.0, 8.0, tag='barr', margin=1.0)
    D.put(M['cone'], -1760.0, 4106.0, 0.0, margin=0.0)
    tp(D, M['cone'], -1636.0, 4080.0, 10.0, 0.0, roll=88.0)
    D.put(M['warn'], -1700.0, 4120.0, 180.0, margin=0.0, clip=False, ignore_keep=True)
    # 8. crates and a pallet against the south wall (two stacks, different), a barrel left apart
    D.put(M['crate3'], -1980.0, 3552.0, 4.0, tag='stkA', margin=1.0)
    D.put(M['crate2'], -1976.0, 3552.0, -6.0, on='stkA', margin=0.0)
    D.put(M['pallet'], -2400.0, 3556.0, 90.0, tag='palA', margin=1.0)
    D.put(M['boxc'], -2400.0, 3556.0, 20.0, on='palA', margin=0.0)
    D.put(M['boxa'], -2394.0, 3556.0, 80.0, z=44.0, margin=0.0, clip=False, ignore_keep=True)
    D.put(M['barrel2'], -1900.0, 3560.0, 0.0, margin=1.0)
    # 9. broken glass and paper drifted against the columns' feet (windward side only: west of each column)
    for k, x in enumerate(COLS):
        if k % 2 == 0:
            D.put(M['glass'], x - 30.0, SPINE_Y + rng.uniform(-24.0, 24.0), rng.uniform(0, 360), margin=0.0, clip=False)
        cluster(x - 26.0, SPINE_Y + rng.uniform(-20.0, 20.0), rng.randint(2, 5), 16.0, [M['paper'], M['cup'], M['can']])
    # 10. north piers: leaning ladder, a hose coil, a cabinet
    for k, (a, b) in enumerate(PIERS):
        mid = (a + b) / 2.0
        if k in (0, 5):
            D.wall(M['fcab'], 'n', mid, tag='pier_fcab%d' % k)
        if k == 2:
            tp(D, M['ladder'], mid - 24.0, A.Y1 - A.WT - 18.0, 0.0, 270.0, pitch=-8.0)
        if k == 4:
            D.put(M['hose'], mid, A.Y1 - A.WT - 22.0, 70.0, margin=0.0, clip=False)
    # the rest of litter: a few drifts at the foot of the walls, uneven
    for k in range(30):
        cluster(rng.uniform(A.X0 + 80.0, A.X1 - 80.0), rng.choice((3526.0, 3534.0, 4272.0, 4278.0, 3866.0, 3934.0)), rng.randint(4, 9), 30.0, small + [M['boxc'], M['bucket']])
    # eight more small stories at irregular places: a toppled barrel and its spill, stacked chairs, boxes dropped in a heap, a bucket with a leaning mop
    for k, (x, y) in enumerate(((-2860.0, 3740.0), (-2610.0, 4070.0), (-2330.0, 3960.0), (-2140.0, 3640.0), (-1790.0, 3720.0), (-1560.0, 4010.0), (-1340.0, 3760.0), (-2990.0 + 160.0, 4090.0))):
        kind = k % 4
        if kind == 0:
            tp(D, M['barrel'], x, y, 14.0, rng.uniform(0, 360), roll=90.0)
            cluster(x + 30.0, y, 6, 20.0, [M['chips'], M['can'], M['paper']])
        elif kind == 1:
            for j in range(3):
                D.put(M['fchair'], x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), rng.uniform(0, 360), margin=0.0, clip=False, ignore_keep=True, z=0.0 + 4.0 * j) if False else tp(D, M['fchair'], x, y, 2.0 + 10.0 * j, rng.uniform(0, 360), pitch=rng.uniform(-6, 6))
        elif kind == 2:
            for j in range(3):
                D.put(M['boxc'] if j % 2 else M['boxa'], x + rng.uniform(-22, 22), y + rng.uniform(-18, 18), rng.uniform(0, 360), margin=0.0, clip=False, ignore_keep=True)
            cluster(x, y, 4, 24.0, [M['paper'], M['mags']])
        else:
            D.put(M['bucket'], x, y, 0.0, margin=0.0, clip=False, ignore_keep=True)
            tp(D, M['mop'], x + 10.0, y + 6.0, 0.0, rng.uniform(0, 360), pitch=-70.0)
    # posters (stock poster materials) on both walls and column faces are in the column dressing
    for k in range(14):
        x = A.X0 + 90.0 + k * 126.0 + rng.uniform(-30.0, 30.0)
        B.decal(m, POSTERS[k % len(POSTERS)], (x, A.Y0 + A.WT, rng.uniform(130.0, 168.0)), (0.0, 1.0, 0.0), (28.0, 40.0), rot=rng.uniform(-3.0, 3.0), id='dec_post_s%d' % k)
    for k, (a, b) in enumerate(PIERS):
        B.decal(m, POSTERS[(k * 2) % len(POSTERS)], ((a + b) / 2.0 - 14.0 + (12.0 if k % 2 else 0.0), A.Y1 - A.WT, 150.0), (0.0, -1.0, 0.0), (28.0, 40.0), id='dec_post_n%d' % k)
    report['stories'] = {'props_total': len(m.flat().props)}


def lights7(A, m, report):
    """every coloured or bright light has a fixture model at its position: the live panel fixtures (ceiling7), the shops' fluorescent pairs, the neon tube round every aperture,
    the hanging lamps of the back rooms, cage lamps"""
    m.use('lights')
    n = 0

    def L(*a, **k):
        nonlocal n
        n += 1
        return B.light(m, *a, layer='lights', **k)
    for k, (x, y, single) in enumerate(A.live):
        L((x, y, 176.0), color=(1.0, 0.93, 0.78), radius=170.0, intensity=round(POOL_I * (0.55 if single else 1.0), 3), type='spot', dir=(0.0, 0.0, -1.0), inner=10.0, outer=34.0, id='light_pool_%d' % k)
    return L, n


def shop_fixtures(A, m, D, L):
    n = 0
    for i in range(5):
        s = A.BAY_X[i]
        cx = s + A.BAY_W / 2.0
        hue = HUE[A.BAYS[i]]
        for dx in (-60.0, 60.0):                                         # two fluorescent fixtures hang in the shop: the key light of the shop is at the pair
            put_model(D, M['fluo'], cx + dx, A.Y1 + 70.0, 0.0, z=186.0, emissive={'color': [1.0, 0.9, 0.74], 'strength': 4.0})
        L((cx, A.Y1 + 70.0, 184.0), color=(1.0, 0.88, 0.7), radius=280.0, intensity=KEY_I, type='spot', dir=(0.0, 0.0, -1.0), inner=34.0, outer=84.0, id='light_key_%d' % (i + 1))
        L((cx, A.Y1 - 22.0, 60.0), color=hue, radius=170.0, intensity=0.6, id='light_neon_%d' % (i + 1))        # the neon tube round the aperture is the source
        L((cx, A.BACK_Y + 60.0, 150.0), color=(1.0, 0.82, 0.55), radius=150.0, intensity=0.45, id='light_back_%d' % (i + 1))            # the hanging lamp of the back room
        n += 3
    for k, x in enumerate((-2560.0, -1860.0)):                          # the caged wall lamps of the south wall are props of wall_props
        L((x, A.Y0 + A.WT + 14.0, 146.0), color=(1.0, 0.78, 0.45), radius=150.0, intensity=0.35, type='spot', dir=(0.0, 0.3, -1.0), inner=16.0, outer=52.0, id='light_cage_%d' % k)
        n += 1
    put_model(D, M['cage'], A.X1 - 60.0, 3900.0, 0.0, z=170.0)
    L((A.X1 - 60.0, 3900.0, 168.0), color=(1.0, 0.85, 0.55), radius=170.0, intensity=0.25, type='spot', dir=(0.0, 0.0, -1.0), inner=20.0, outer=60.0, id='light_d4')
    put_model(D, M['cage'], A.X0 + 70.0, 4040.0, 0.0, z=146.0)
    L((A.X0 + 70.0, 4040.0, 148.0), color=(1.0, 0.8, 0.5), radius=180.0, intensity=0.5, type='spot', dir=(0.0, -0.2, -1.0), inner=16.0, outer=52.0, id='light_d7_cage')
    if DOJO:
        for k, x in enumerate(COLS):                                     # the lamp on each column's shaft is the fixture
            L((x + 12.0, SPINE_Y - 26.0, 148.0), color=(1.0, 0.86, 0.62), radius=150.0, intensity=0.35, id='light_colS_%d' % k)
            L((x - 12.0, SPINE_Y + 26.0, 148.0), color=(1.0, 0.86, 0.62), radius=150.0, intensity=0.35, id='light_colN_%d' % k)
            n += 2
    L((GAPS[0], SPINE_Y + 105.0, 90.0), color=(1.0, 0.75, 0.35), radius=190.0, intensity=0.5, id='light_kiosk')           # under the awning, at its cage lamp
    return n + 3


def counts(m, A):
    """props per rectangle: the corridor, each bay's shop room, the back rooms"""
    out = {'corridor': 0, 'back_rooms': 0, 'vestibule': 0}
    for i in range(5):
        out['bay%d' % (i + 1)] = 0
    for p in m.flat().props:
        x, y = p['origin'][0], p['origin'][1]
        if y < A.Y1:
            out['vestibule' if x > A.X1 else 'corridor'] += 1
        elif y >= A.BACK_Y:
            out['back_rooms'] += 1
        else:
            for i in range(5):
                if A.BAY_X[i] <= x < A.BAY_X[i] + A.BAY_W:
                    out['bay%d' % (i + 1)] += 1
    return out


def fixtures8(A, m, report):
    """the blank emissive slabs go: ceiling strips of the shops, back wall header strips, aperture neon frames, column light boxes; stock fixtures with their light take their place"""
    gone = {}
    for pre in ('strip_h_', 'strip_', 'hdr_strip_', 'neon_top_', 'neon_l_', 'neon_r_', 'col_lbframe_', 'col_lb_'):
        gone[pre] = drop(m, pre)
    for pre in ('light_neon_',):
        gone[pre] = drop_ids(m, lambda o, pre=pre: str(o['id']).startswith(pre))
    m.use('lights')
    n = []
    for i in range(5):
        a0, a1 = A.aperture(i)
        cx = (a0 + a1) / 2.0
        hue = HUE[A.BAYS[i]]
        # the shop sign over the aperture, on the corridor face of the north wall
        n += F.fixture(m, SHOP_SIGN[i], (cx, A.Y1 - A.WT - 1.0, 196.0), 270.0, color=hue, group='power', zone='arcade', id='fx_sign_%d' % (i + 1))
        for dx in (-70.0, 70.0):                                          # the shop's own ceiling tubes replace the strips
            n += F.fixture(m, 'ceiling_tube', (cx + dx, A.Y1 + 70.0, A.BAY_H - 2.0), 0.0, kelvin=3600, intensity=0.7, zone='arcade', id='fx_tube_%d_%d' % (i + 1, int(dx > 0)))
        n += F.fixture(m, 'light_box', (cx, A.BACK_Y + 14.0, 118.0), 270.0, color=hue, intensity=0.8, zone='arcade', id='fx_back_%d' % (i + 1))
    for k, x in enumerate(COLS):                                       # the column light boxes were blank white: a poster on each face instead (stock picture materials)
        if COLSPEC[k]['feature'] == 'lightbox':
            for sgn in (-1, 1):
                B.decal(m, POSTERS[(k + (2 if sgn > 0 else 0)) % len(POSTERS)], (x, SPINE_Y + sgn * (COL_HALF + 1.5 + 0.3), 118.0), (0.0, float(sgn), 0.0), (24.0, 34.0), id='fx_colposter_%d_%d' % (k, sgn > 0))
    m.use('dressing')
    report['fixtures8'] = {'dropped': gone, 'placed': len([x for x in n if not str(x).endswith(tuple('l%d' % j for j in range(1, 4)))]), 'ids': len(n)}


def drop_ids(m, pred):
    n = 0
    for pid in [o['id'] for layer in m.layers.values() for o in layer if pred(o)]:
        m.remove(pid)
        n += 1
    return n


def canon8(A, m, report):
    """stock models with words of other places go (F.READABLE_TEXT); the hanging boards become our own text signs, the awning loses its sign, the white planter model is a plant"""
    from studio import fixtures as FX
    boards, gone, n = [], 0, 0
    for o in [o for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and o['model'] in FX.READABLE_TEXT]:
        if o['model'] in CANON:
            boards.append((CANON[o['model']], o['origin']))
        m.remove(o['id'])
        gone += 1
    seen = {}
    for text, og in boards:
        k = seen[text] = seen.get(text, 0) + 1
        cx, cy, z = og[0], og[1], og[2] + 20.0
        for sgn in (-1, 1):
            B.sign(m, text=text, at=(cx, cy + sgn * 1.0, z), normal=(0.0, float(sgn), 0.0), size=(76.0, 40.0), lamp=True, color=(1.0, 0.82, 0.4), id='cn_%s_%d_%d' % (text[:4].strip(), k, sgn > 0))
            n += 1
    for o in [o for layer in m.layers.values() for o in layer if o['kind'] == 'prop' and o['model'] == 'flower_shop_planter_02']:     # no material in the game: a white block
        m.remove(o['id'])
        B.prop(m, M['plant'], o['origin'], yaw=o.get('yaw') or 0.0, zone='arcade', id=o['id'] + '_plant')
    report['canon8'] = {'removed': gone, 'text_signs': n}


def litter8(A, m, report):
    """round 7's grid litter (untagged floor props of the litter models in the corridor) goes; scatter themes with a reason take its place"""
    keep = {M[k] for k in LITTER if k in M}
    gone = drop_ids(m, lambda o: o['kind'] == 'prop' and o['model'] in keep and o['origin'][1] < A.Y1 and o['origin'][2] < 12.0 and str(o['id']).startswith('p') and str(o['id'])[1:4].isdigit())
    area = [A.X0 + 60.0, A.Y0 + 60.0, A.X1 - 60.0, A.Y1 - 60.0]
    reps = {}
    pts = []
    for i in range(5):
        a0, a1 = A.aperture(i)
        pts.append(((a0 + a1) / 2.0, A.Y1 - A.WT - 6.0, 0.0, -1.0))
    for seed, (theme, dens, extra) in enumerate((('commuter', 9.0, {}), ('shop spill', 6.0, {'points': pts}), ('cleaning', 4.0, {}), ('abandoned', 5.0, {}))):
        r = P_props.scatter(m, area, theme, density=dens, seed=80 + seed, rules=dict(extra, cap=3), zone='arcade', id_prefix='lit_' + theme.replace(' ', '_'))
        reps[theme] = {k: r[k] for k in ('clusters', 'props', 'distinct_models', 'nn_cv', 'nn_index', 'rejected')}
    report['litter8'] = {'dropped_grid_props': gone, 'themes': reps}


def _grad(size, c0, c1):
    from PIL import Image
    w, h = size
    im = Image.new('RGB', size)
    px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        col = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
        for x in range(w):
            px[x, y] = col
    return im


def shop_pictures(folder):
    """r14: the shops' hung boards and wall posters as pictures Studio draws (no store material, no letters): the store posters drew black or tiled noise at this size (FE54), and a box
    face tiles its material (a hung sheet showed a window of a poster, magnified); a sign quad carries the whole image. Drawn at 3x and reduced, 512 px wide at most (a hung board is seen
    from 40 units: about 17 px per unit on a 1280 frame)"""
    from PIL import Image, ImageDraw
    rng = random.Random(1978)
    S = 3

    def finish(im, name, size):
        im.resize(size, Image.LANCZOS).save('%s/%s' % (folder, name))

    pal = [((250, 214, 120), (178, 60, 40)), ((130, 190, 235), (24, 48, 110)), ((240, 150, 190), (92, 28, 88)), ((170, 220, 160), (22, 80, 70)), ((245, 235, 215), (120, 100, 90)), ((255, 170, 80), (70, 30, 20))]
    for k in range(6):                                    # wall posters 320 x 448: a sky gradient, a sun or moon, two rows of buildings, a white border
        w, h = 320 * S, 448 * S
        top, bot = pal[k]
        im = _grad((w, h), top, bot)
        d = ImageDraw.Draw(im)
        cx, cy, r = int(w * (0.3 + 0.4 * rng.random())), int(h * 0.34), int(w * 0.17)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 245, 220))
        for row, shade in ((0.62, 0.55), (0.76, 0.32)):
            x = 0
            col = tuple(int(c * shade) for c in bot)
            while x < w:
                bw = int(w * rng.uniform(0.07, 0.16))
                bh = int(h * rng.uniform(0.10, 0.26))
                d.rectangle([x, int(h * row) - bh, x + bw, h], fill=col)
                x += bw + int(w * rng.uniform(0.0, 0.02))
        d.rectangle([0, 0, w - 1, h - 1], outline=(240, 240, 236), width=int(14 * S / 2))
        finish(im, 'poster_%d.png' % k, (320, 448))
    for k in range(3):                                    # photo prints 240 x 320: a white margin, a scene (horizon, a figure, a window)
        w, h = 240 * S, 320 * S
        im = Image.new('RGB', (w, h), (244, 240, 230))
        d = ImageDraw.Draw(im)
        m0 = int(w * 0.07)
        sky, ground = pal[(k + 1) % 6]
        scene = _grad((w - 2 * m0, int(h * 0.74)), sky, ground)
        im.paste(scene, (m0, m0))
        d = ImageDraw.Draw(im)
        hz = m0 + int(h * 0.74 * 0.62)
        d.rectangle([m0, hz, w - m0, m0 + int(h * 0.74)], fill=tuple(int(c * 0.35) for c in ground))
        fx = int(w * (0.35 + 0.3 * rng.random()))
        d.ellipse([fx - 30 * S, hz - 80 * S, fx + 30 * S, hz - 20 * S], fill=(40, 34, 30))
        d.rectangle([fx - 34 * S, hz - 24 * S, fx + 34 * S, hz + 40 * S], fill=(40, 34, 30))
        finish(im, 'photo_%d.png' % k, (240, 320))
    T = _texts()
    menu_px = ((512, 305), (448, 320), (448, 320))                 # r18: 84 x 50, 56 x 40 and 40 x 28 units, wall-mounted
    for k, key in enumerate(('menu_main', 'menu_special', 'menu_small')):
        w, h = menu_px[k][0] * S, menu_px[k][1] * S
        hdr = ((200, 70, 50), (230, 170, 50), (60, 150, 180))[k]
        im = Image.new('RGB', (w, h), (30, 26, 24))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w - 1, int(h * 0.16)], fill=hdr)
        lines = T.get(key)
        if lines:
            _fit_text(d, lines[0], (int(w * 0.04), int(h * 0.01), int(w * 0.96), int(h * 0.15)), 'impact.ttf', (250, 240, 225), 'c')
            body = lines[1:]
            n = max(len(body), 4)
            top, bot = int(h * 0.20), int(h * 0.96)
            pitch = (bot - top) / float(n)
            fsz = int(pitch * 0.74)
            fnt = _font('arialbd.ttf', fsz)
            names = [ln.split('|')[0].rstrip() for ln in body]
            prices = [ln.split('|')[1].strip() if '|' in ln else '' for ln in body]
            while fsz > 8 and max([d.textlength(t, font=fnt) for t in names] + [1]) + max([d.textlength(t, font=fnt) for t in prices] + [0]) > w * 0.86:
                fsz -= 2
                fnt = _font('arialbd.ttf', fsz)
            for r, (nm, pr) in enumerate(zip(names, prices)):
                y = int(top + r * pitch + (pitch - fsz) * 0.35)
                d.text((int(w * 0.06), y), nm, font=fnt, fill=(235, 228, 205))
                if pr:
                    d.text((int(w * 0.94 - d.textlength(pr, font=fnt)), y), pr, font=fnt, fill=(235, 190, 90))
        else:
            for row in range(6):
                y = int(h * (0.24 + 0.12 * row))
                lw = int(w * (0.4 + 0.04 * ((row * 3 + k) % 5)))
                d.rectangle([int(w * 0.07), y, int(w * 0.07) + lw, y + int(h * 0.05)], fill=(235, 228, 205))
                d.rectangle([int(w * 0.78), y, int(w * 0.92), y + int(h * 0.05)], fill=(235, 190, 90))
        d.rectangle([0, 0, w - 1, h - 1], outline=(190, 150, 70), width=8 * S)
        finish(im, 'menu_%d.png' % k, menu_px[k])
    paper = ((70, 110, 170), (190, 80, 60), (80, 140, 100), (150, 110, 60))
    for k in range(4):                                    # r18: copy shop notices 288 x 384 (24 x 32 units)
        _paper(finish, T.get('notice_%d' % k), 'sheet_%d.png' % k, (288, 384), paper[k], S, (240, 238, 230), k)
    benchc = ((60, 100, 150), (150, 70, 50), (70, 120, 90), (120, 90, 50))
    for k in range(4):                                    # r18: ticket hall notice board, 288 x 360 (about 24 x 30 units)
        _paper(finish, T.get('bench_notice_%d' % k), 'bench_notice_%d.png' % k, (288, 360), benchc[k], S, (232, 226, 206), k)
    for k in range(8):                                    # record sleeves 256 x 256 (14 x 14 units): a colour field, a disc, the band on top and the album under it
        w = h = 256 * S
        c0, c1 = pal[k % 6]
        im = _grad((w, h), c1, c0) if k % 2 else _grad((w, h), c0, c1)
        d = ImageDraw.Draw(im)
        lines = T.get('sleeve_%d' % k)
        cx, cy, r = w // 2, int(h * (0.54 if lines else 0.5)), int(w * (0.27 if lines else 0.38))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(22, 22, 24))
        for q in range(1, 5):
            rr = int(r * (1.0 - 0.17 * q))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(70, 70, 76), width=2 * S)
        rl = int(r * 0.34)
        d.ellipse([cx - rl, cy - rl, cx + rl, cy + rl], fill=pal[(k + 2) % 6][0])
        if lines:
            d.rectangle([0, 0, w, int(h * 0.22)], fill=(16, 16, 18))
            _fit_text(d, lines[0], (int(w * 0.05), int(h * 0.02), int(w * 0.95), int(h * 0.20)), 'impact.ttf', (245, 238, 220), 'c')
            d.rectangle([0, int(h * 0.84), w, h], fill=(16, 16, 18))
            _fit_text(d, ' / '.join(lines[1:]), (int(w * 0.05), int(h * 0.86), int(w * 0.95), int(h * 0.97)), 'arial.ttf', (225, 215, 190), 'c')
        d.rectangle([0, 0, w - 1, h - 1], outline=(236, 236, 230), width=10 * S)
        finish(im, 'sleeve_%d.png' % k, (256, 256))
    w, h = 168 * S, 216 * S                               # r18: a turnstile housing panel 14 x 18 units: a green arrow, a red cross (no letters)
    im = Image.new('RGB', (w, h), (28, 30, 34))
    d = ImageDraw.Draw(im)
    d.polygon([(w // 2, int(h * 0.46)), (int(w * 0.22), int(h * 0.20)), (int(w * 0.78), int(h * 0.20))], fill=(50, 190, 90))
    d.rectangle([int(w * 0.40), int(h * 0.08), int(w * 0.60), int(h * 0.22)], fill=(50, 190, 90))
    d.line([(int(w * 0.30), int(h * 0.60)), (int(w * 0.70), int(h * 0.92))], fill=(210, 50, 40), width=10 * S)
    d.line([(int(w * 0.70), int(h * 0.60)), (int(w * 0.30), int(h * 0.92))], fill=(210, 50, 40), width=10 * S)
    d.rectangle([0, 0, w - 1, h - 1], outline=(150, 150, 150), width=4 * S)
    finish(im, 'turnstile_panel.png', (168, 216))
    w, h = 166 * S, 500 * S                               # r18: the column's transit map 16.6 x 50 units: dark navy, coloured routes and station dots (no letters); the stock map material read white
    im = Image.new('RGB', (w, h), (26, 34, 52))
    d = ImageDraw.Draw(im)
    for q, col in enumerate(((220, 70, 60), (60, 160, 220), (230, 190, 60), (80, 190, 110))):
        pts = [(int(w * (0.12 + 0.76 * ((q * 0.37 + t * 0.29) % 1.0))), int(h * (0.08 + 0.84 * t / 5.0))) for t in range(6)]
        d.line(pts, fill=col, width=4 * S)
        for pt in pts:
            d.ellipse([pt[0] - 5 * S, pt[1] - 5 * S, pt[0] + 5 * S, pt[1] + 5 * S], fill=(230, 230, 225), outline=col, width=2 * S)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 130, 150), width=3 * S)
    finish(im, 'transit_map.png', (166, 500))


TEXT_FILE = os.environ.get('ARC18_TEXT', 'C:/studio-data/sz/arcade/r18/TEXT.json')


def _texts():
    """round 18: the words of every readable picture come from TEXT.json ({surface id: [lines]}, written by the copywriter); a missing file or surface keeps the no-letter placeholder"""
    import json
    try:
        return json.load(open(TEXT_FILE, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def _font(name, size):
    from PIL import ImageFont
    for base in ('C:/Windows/Fonts/', ''):
        try:
            return ImageFont.truetype(base + name, max(int(size), 6))
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_text(d, text, box, fontname, fill, align='l'):
    """one line in box (x0, y0, x1, y1): the largest size that fits, centred vertically; whitespace is kept"""
    x0, y0, x1, y1 = box
    size = y1 - y0
    fnt = _font(fontname, size)
    while size > 8 and d.textlength(text, font=fnt) > (x1 - x0):
        size -= 2
        fnt = _font(fontname, size)
    tw = d.textlength(text, font=fnt)
    x = x0 + ((x1 - x0) - tw) / 2.0 if align == 'c' else x0
    d.text((x, y0 + ((y1 - y0) - size) * 0.4), text, font=fnt, fill=fill)


def _paper(finish, lines, name, size, hdr, S, bg, k):
    """a paper notice: a coloured header band with the title, the body lines in dark grey, a red stamp ring; no lines = the no-letter placeholder"""
    from PIL import Image, ImageDraw
    w, h = size[0] * S, size[1] * S
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, int(h * 0.18)], fill=hdr)
    if lines:
        _fit_text(d, lines[0], (int(w * 0.06), int(h * 0.02), int(w * 0.94), int(h * 0.16)), 'impact.ttf', (250, 248, 240), 'c')
        body = lines[1:]
        n = max(len(body), 5)
        top, bot = int(h * 0.23), int(h * 0.90)
        pitch = (bot - top) / float(n)
        fsz = int(pitch * 0.62)
        fnt = _font('arial.ttf', fsz)
        while fsz > 8 and max([d.textlength(t, font=fnt) for t in body] + [1]) > w * 0.86:
            fsz -= 2
            fnt = _font('arial.ttf', fsz)
        for r, t in enumerate(body):
            d.text((int(w * 0.07), int(top + r * pitch + (pitch - fsz) * 0.3)), t, font=fnt, fill=(40, 40, 44))
    else:
        y = int(h * 0.24)
        while y < h * 0.88:
            d.rectangle([int(w * 0.08), y, int(w * (0.5 + 0.08 * ((y // 7) % 5))), y + int(h * 0.016)], fill=(150, 150, 150))
            y += int(h * 0.05)
    if k % 2 == 0 and not (lines and len(lines) > 5):
        d.ellipse([int(w * 0.62), int(h * 0.76), int(w * 0.9), int(h * 0.76) + int(w * 0.28)], outline=(180, 50, 50), width=5 * S)
    d.rectangle([0, 0, w - 1, h - 1], outline=(200, 198, 190), width=3 * S)
    finish(im, name, size)


def stain_pictures(folder):
    """three soft-edged stain pictures (RGBA: the alpha is the coverage): an irregular blob, dark brown, fading to nothing before the edge of the image"""
    import numpy as np
    from PIL import Image, ImageFilter
    n = 256
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    for i, name in enumerate(STAIN_FILES):
        rs = np.random.RandomState(1700 + i)
        a = np.zeros((n, n), np.float32)
        for _ in range(7):                                                 # a few overlapping soft discs, off centre
            cx, cy = n / 2 + rs.uniform(-40, 40), n / 2 + rs.uniform(-40, 40)
            r = rs.uniform(28, 62)
            a = np.maximum(a, np.clip(1.0 - np.hypot(xx - cx, yy - cy) / r, 0.0, 1.0))
        a = np.clip(a * 1.6, 0.0, 1.0) ** 1.5                              # soft shoulder
        noise = Image.fromarray((rs.uniform(0, 255, (n // 8, n // 8))).astype(np.uint8)).resize((n, n), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
        a = a * (0.55 + 0.45 * np.asarray(noise, np.float32) / 255.0)
        edge = np.clip(1.0 - np.hypot(xx - n / 2, yy - n / 2) / (n / 2 - 2), 0.0, 1.0)       # nothing at the picture's border
        a = a * np.clip(edge * 4.0, 0.0, 1.0) * 0.8
        rgba = np.zeros((n, n, 4), np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = 28, 22, 16
        rgba[..., 3] = (a * 255).astype(np.uint8)
        Image.fromarray(rgba, 'RGBA').save('%s/%s' % (folder, name))


def make_pictures(folder):
    """writes the arrow pictograms beside map.json (called after the document is saved)"""
    from PIL import Image, ImageDraw
    shop_pictures(folder)
    stain_pictures(folder)
    for name, kind in (('arrow_l.png', 'l'), ('arrow_r.png', 'r'), ('arrow_stair.png', 's')):
        im = Image.new('RGB', (256, 80), (20, 60, 150))
        d = ImageDraw.Draw(im)
        d.rectangle([4, 4, 251, 75], outline=(235, 235, 235), width=4)
        if kind in ('l', 'r'):
            sgn = -1 if kind == 'l' else 1
            cx = 128
            d.rectangle([cx - 70, 32, cx + 70, 48], fill=(240, 240, 240))
            d.polygon([(cx + sgn * 100, 40), (cx + sgn * 46, 10), (cx + sgn * 46, 70)], fill=(240, 240, 240))
        else:
            for k in range(5):
                d.rectangle([40 + k * 30, 58 - k * 11, 70 + k * 30, 66 - k * 11 + 8], fill=(240, 240, 240))
            d.polygon([(214, 14), (236, 36), (192, 36)], fill=(250, 210, 40))
        im.save('%s/%s' % (folder, name))


def back_strips(A, m, D, i, kind, items, brd):
    """the partition's face (the back wall of the front room): two wall runs of shelf units with their stock, either side of the doorway (u 18..116 and 204..302)"""
    s, yp = A.BAY_X[i], A.BACK_Y
    stock = []
    for k in list(items[0]) + list(items[1]):
        if k in M and M[k] not in stock:
            stock.append(M[k])
    n = 0
    rows = REPORT.setdefault('strips', {}).setdefault(kind, [])
    for side, (u0, u1) in enumerate(((18.0, 116.0), (204.0, 302.0))):
        rep = prefab.dress_like(m, None, [s + u0, yp - STRIP_DEPTH, s + u1, yp], front='s', seed=10 * i + side, prefix='st%d_%d_' % (i + 1, side), keep_clear=answers.clearance_rows(m),
                                strip={'wall': 'back', 'depth': STRIP_DEPTH, 'shelf': SHELF, 'stock': stock, 'fill': 0.9})
        n += rep.get('stock', 0) or 0
        rows.append({'side': side, 'shelves': rep.get('shelves'), 'stock': rep.get('stock'), 'levels': rep.get('levels'), 'distinct_models': rep.get('distinct_models'),
                     'wall_cover': rep.get('wall_cover'), 'refusal_lines': rep.get('refusal_lines')})
        D.n += (rep.get('shelves') or 0) + (rep.get('stock') or 0)
    return n

