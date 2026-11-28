r"""shop_dress: the four shops dressed with stock models of the donor kit (worker AC2, 28 Nov 2026; K1-CONSTRUCTION 4.2, REVIEW-3 "thin box of low-resolution props").

Each shop's identity stays in the goods modules (the pictures, the authored machines, the anchors); what is added here is what a real shop of the trade has around
them, as stock models at stock density: speakers, screens, crates and discs of Needle Drop; the filing cabinets, paper boxes, phones and desk lamps of Copy Stop; the
coffee machines, cups, condiments, fridge and menus of Hole Number Nine; the boots, shoes, tool jars, hammers and key tags of Heel & Key.

Every prop is static (no network record). Floor-standing furniture carries a clip box (the footprint to 64 high); things on a counter, a shelf or a wall carry none.
Orientation: a model's `back` and the yaws that put it to a wall come from `store show` (shop_parts.json); where the sheet could not say (a symmetric model) the table
below says which way it faces at yaw 0. `A` is the arcade_shell module.
"""
import json
import math
import os

from studio import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = {}
for _f in ('parts_final.json', 'shop_parts.json'):
    try:
        PARTS.update(json.load(open(os.path.join(HERE, _f), encoding='utf-8')))
    except OSError:
        pass
PARTS.setdefault('cp_disco_record_milk_crate', {'mins': [-7.936, -7.929, 0.0], 'maxs': [7.936, 7.929, 13.006], 'back': None, 'against_wall': None})     # K1 bounds (k1lib.model)
LAYER = 'shops_ac2'
COUNT = {'props': 0, 'models': set()}

# yaw 0 faces this way for models the sheets list as symmetric or plates (read from the sheets by eye); 'x' = the +x side is the front
FRONT = {'cp_disco_tv_crt': '-y', 'zmb_tv_crt_01': '-y', 'cp_town_cash_register': '-y', 'cp_disco_monitor_speaker': '+y', 'misc_coffee_machine': '+x'}


def _rot(mins, maxs, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = [(x * c - y * s, x * s + y * c) for x in (mins[0], maxs[0]) for y in (mins[1], maxs[1])]
    return min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)


def _mm(model, scale):
    p = PARTS[model]
    return [v * scale for v in p['mins']], [v * scale for v in p['maxs']]


def put(m, model, x, y, z, yaw=0.0, scale=1.0, id=None, clip=None, layer=None, **kw):
    """the middle of the model's footprint on (x, y), its lowest point on z; clip='auto' a footprint box up to 64"""
    if model not in PARTS:
        raise KeyError('shop_dress: no bounds for %s (run store show, build_shop_parts.py)' % model)
    mins, maxs = _mm(model, scale)
    dx0, dx1, dy0, dy1 = _rot(mins, maxs, yaw)
    if clip == 'auto':
        clip = [round(dx0, 1), round(dy0, 1), 0.0, round(dx1, 1), round(dy1, 1), round(min(maxs[2] - mins[2], 64.0), 1)]
    n = COUNT.setdefault('n', {})
    k = n[model] = n.get(model, 0) + 1
    COUNT['props'] += 1
    COUNT['models'].add(model)
    return B.prop(m, model, (round(x - (dx0 + dx1) / 2.0, 2), round(y - (dy0 + dy1) / 2.0, 2), round(z - mins[2], 2)), yaw=yaw, scale=scale, clip=clip, layer=layer or LAYER,
                  id=id or 'ac2_%s_%d' % (model, k), **kw)


def wall(m, model, facing, plane, along, z, scale=1.0, id=None, clip=None, gap=0.3, yaw=None, center_z=False, **kw):
    """a model with its back flush to a wall: facing = the direction the wall faces into the room ('+x' west wall, '-x' east wall, '+y' a wall at the room's south, '-y'
    the partition), plane = the wall's coordinate, along = the middle along the wall, z = its lowest point (or its middle with center_z)"""
    p = PARTS[model]
    key = 'wall facing ' + facing
    if yaw is None:
        yaw = (p.get('against_wall') or {}).get(key)
    if yaw is None:
        fr = FRONT.get(model)
        yaw = {'+x': {'+x': 0, '-x': 180, '+y': 270, '-y': 90}, '-x': {'-x': 0, '+x': 180, '-y': 270, '+y': 90}, '+y': {'+y': 0, '-y': 180, '+x': 270, '-x': 90},
               '-y': {'-y': 0, '+y': 180, '-x': 270, '+x': 90}}.get(fr or '+x', {}).get(facing, 0.0)       # the model's front goes to the room: the wall faces the way the front looks
        yaw = float(yaw)
    mins, maxs = _mm(model, scale)
    dx0, dx1, dy0, dy1 = _rot(mins, maxs, yaw)
    zb = z - ((maxs[2] - mins[2]) / 2.0 if center_z else 0.0)
    if facing == '+x':
        x, y = plane - dx0 + gap, along - (dy0 + dy1) / 2.0
    elif facing == '-x':
        x, y = plane - dx1 - gap, along - (dy0 + dy1) / 2.0
    elif facing == '+y':
        x, y = along - (dx0 + dx1) / 2.0, plane - dy0 + gap
    else:
        x, y = along - (dx0 + dx1) / 2.0, plane - dy1 - gap
    if clip == 'auto':
        clip = [round(dx0, 1), round(dy0, 1), 0.0, round(dx1, 1), round(dy1, 1), round(min(maxs[2] - mins[2], 64.0), 1)]
    n = COUNT.setdefault('n', {})
    k = n[model] = n.get(model, 0) + 1
    COUNT['props'] += 1
    COUNT['models'].add(model)
    return B.prop(m, model, (round(x, 2), round(y, 2), round(zb - mins[2], 2)), yaw=yaw, scale=scale, clip=clip, layer=LAYER, id=id or 'ac2_%s_%d' % (model, k), **kw)


# ================================================================================================ Needle Drop
def needle_drop(A, m):
    x0, x1 = A.UNITS['needle_drop']
    W, E, S, N = x0 + 16.0, x1 - 16.0, A.Y1 + 16.0, A.PART_Y
    cx = (x0 + x1) / 2.0
    # the screens and the sound: a monitor on the rental shelf's top showing the test bars, the shop's two speakers on the partition, a boombox on the counter
    put(m, 'cp_disco_tv_crt', -2797.0, 4466.0, 124.0, 0.0)
    put(m, 'cp_disco_tv_crt', -2727.0, 4468.0, 178.0, 0.0)                                  # a second, on the jukebox's high shelf
    wall(m, 'cp_disco_monitor_speaker', '-y', N, -2690.0, 160.0)
    wall(m, 'cp_disco_monitor_speaker', '-y', N, -2860.0, 176.0)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '-x', E, 4398.0, 150.0)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '-x', E, 4452.0, 150.0)
    wall(m, 'sign_clock_04', '-x', E, 4425.0, 176.0, center_z=True)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '+x', W, 4350.0, 170.0)
    put(m, 'lag_portable_radio', -2672.0, 4404.0, 40.0, 90.0)
    put(m, 'cp_rave_turntable_mixer_01', -2673.0, 4437.0, 40.0, 90.0)
    put(m, 'com_desktop_speaker', -2668.0, 4428.0, 40.0, 90.0)
    # discs and sleeves out of their jackets: on the counter, on the bins' rim, on the floor where the last customers dropped them
    for k, (x, y, z) in enumerate(((-2674.0, 4410.0, 40.4), (-2676.0, 4443.0, 40.4), (-2840.0, 4392.0, 30.4), (-2800.0, 4428.0, 30.4), (-2765.0, 4410.0, 0.3), (-2905.0, 4380.0, 0.3),
                                  (-2738.0, 4437.0, 0.3), (-2880.0, 4452.0, 0.3))):
        put(m, 'cp_disco_record_02', x, y, z, 37.0 * k)
    # milk crates of records, stacked, in the corners clear of the walking line
    put(m, 'cp_disco_record_milk_crate', -2926.0, 4344.0, 0.0, 8.0, id='ac2_crate_a', clip='auto')
    put(m, 'cp_disco_record_milk_crate', -2926.0, 4344.0, 13.0, 31.0, id='ac2_crate_b')
    put(m, 'cp_disco_record_milk_crate', -2678.0, 4352.0, 0.0, 80.0, id='ac2_crate_c', clip='auto')


# ================================================================================================ Copy Stop
def copy_stop(A, m):
    x0, x1 = A.UNITS['copy_stop']
    W, E, N = x0 + 16.0, x1 - 16.0, A.PART_Y
    cx = (x0 + x1) / 2.0
    # along the partition east of its door: the filing cabinets of the finished jobs, the paper cartons, the clipboards
    for k, x in enumerate((-2250.0, -2220.0, -2190.0, -2160.0)):
        wall(m, 'com_filecabinetblackclosed', '-y', N, x, 0.0, id='ac2_cabinet_%d' % k, clip='auto')
    put(m, 'com_copypaper_box', -2250.0, 4468.0, 50.0, 0.0)
    put(m, 'com_copypaper_box', -2220.0, 4468.0, 50.0, 15.0)
    put(m, 'com_copypaper_box_open', -2190.0, 4468.0, 50.0, 90.0)
    put(m, 'office_paper_stack01_iw6', -2160.0, 4468.0, 50.0, 0.0)
    for k, (x, y) in enumerate(((-2124.0, 4470.0), (-2112.0, 4470.0), (-2100.0, 4470.0))):
        put(m, 'com_copypaper_box', x, y, 0.0, 6.0 * k, id='ac2_ream_%d' % k)
    put(m, 'com_copypaper_box', -2118.0, 4470.0, 10.4, 20.0, id='ac2_ream_top')
    # on the service counter and the plan chest
    put(m, 'cp_town_desk_phone_01_black', -2100.0, 4392.0, 40.0, 180.0)
    put(m, 'desk_light_fn_01', -2096.0, 4380.0, 40.0, 180.0)
    put(m, 'com_clipboard', -2150.0, 4390.0, 40.0, 10.0)
    put(m, 'com_office_book_set1', -2200.0, 4388.0, 40.0, 20.0)
    put(m, 'office_paper_stack01_iw6', -2240.0, 4390.0, 40.0, 40.0)
    put(m, 'desk_light_fn_01', -2590.0, 4380.0, 36.0, 0.0)
    put(m, 'com_clipboard', -2596.0, 4366.0, 36.0, 80.0)
    # wall furniture: the clock over the counter, the staff phone, a notice of the hours
    wall(m, 'sign_clock_04', '-y', N, -2180.0, 178.0, center_z=True)
    wall(m, 'equipment_wall_mounted_phone_01_yellow', '-y', N, -2130.0, 110.0)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '-y', N, -2400.0, 190.0)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '-y', N, -2060.0, 190.0)
    # a folding table of the collating work by the east window, with cartons under it
    put(m, 'com_folding_table', -2062.0, 4460.0, 0.0, 90.0, id='ac2_collating_table', clip='auto')
    for k, x in enumerate((-2085.0, -2062.0, -2040.0)):
        put(m, 'com_copypaper_box', x, 4460.0, 33.9, 11.0 * k, id='ac2_table_box_%d' % k)
    put(m, 'furniture_filing_cabinet', -2600.0, 4472.0, 0.0, 180.0, id='ac2_cabinet_w', clip='auto')
    put(m, 'com_clipboard', -2062.0, 4448.0, 33.9, 70.0, id='ac2_table_clip')
    put(m, 'com_copypaper_box', -2610.0, 4474.0, 0.0, 90.0, id='ac2_box_w0', clip='auto')
    put(m, 'com_copypaper_box_open', -2610.0, 4474.0, 10.4, 80.0, id='ac2_box_w1')


# ================================================================================================ Hole Number Nine
def hole_nine(A, m):
    x0, x1 = A.UNITS['hole_nine']
    W, E, S, N = x0 + 16.0, x1 - 16.0, A.Y1 + 16.0, A.PART_Y
    # behind the serving counter, on the ledge by the till: the machines of the coffee and what goes with it
    put(m, 'misc_coffee_machine', -1930.0, 4462.0, 40.0, 270.0)
    put(m, 'misc_coffee_machine_pot', -1900.0, 4466.0, 40.0, 0.0)
    for k, x in enumerate((-1878.0, -1870.0, -1862.0)):
        put(m, 'ma_cup_stack', x, 4470.0, 40.0, 0.0)
    put(m, 'p7_diner_table_napkin_clean', -1850.0, 4468.0, 40.0, 0.0)
    put(m, 'p7_diner_table_ketchup', -1843.0, 4466.0, 40.0, 0.0)
    put(m, 'p7_diner_table_holder', -1836.0, 4468.0, 40.0, 0.0)
    # the fridge and the cooler against the west wall, south of the SMG board
    wall(m, 'cooler_upright_iw6', '+x', W, 4352.0, 0.0, id='ac2_cooler', clip='auto')
    wall(m, 'misc_wall_mounted_loudspeaker_01', '-x', E, 4455.0, 150.0)
    wall(m, 'sign_clock_04', '-y', N, -1700.0, 160.0, center_z=True)


# ================================================================================================ Heel & Key
def heel_key(A, m):
    x0, x1 = A.UNITS['heel_key']
    W, E, S, N = x0 + 16.0, x1 - 16.0, A.Y1 + 16.0, 4410.0
    # on the bench and the shelves: the shoes waiting, the boots, the tools of the trade in their jars
    for k, (x, y, yaw) in enumerate(((-1560.0, 4392.0, 20.0), (-1544.0, 4392.0, 160.0))):
        put(m, 'p7_54i_gear_shoes', x, y, 36.0, yaw)
    put(m, 'boots_civ_miner_01_static', -1520.0, 4382.0, 36.0, 200.0)
    for k, x in enumerate((-1608.0, -1596.0, -1584.0)):
        put(m, 'p7_tools_jar_glass_nails_screws' if k != 1 else 'p7_tools_jar_glass_bolts', x, 4402.0, 36.0, 0.0)
    put(m, 'zmb_tool_hammer_01', -1580.0, 4372.0, 36.2, 35.0)
    put(m, 'zmb_tool_pliers_01', -1568.0, 4366.0, 36.2, 80.0)
    put(m, 'toolbox_small01_iw6', -1356.0, 4376.0, 0.0, 90.0, clip='auto')
    for k, (x, y) in enumerate(((-1620.0, 4350.0), (-1612.0, 4358.0))):
        put(m, 'cp_town_nail_polish_remover', x, y, 36.0, 0.0)
    wall(m, 'misc_wall_mounted_loudspeaker_01', '+x', W, 4350.0, 190.0)
    wall(m, 'sign_clock_04', '-x', E, 4340.0, 176.0, center_z=True)


def build(A, m):
    m.use(LAYER)
    needle_drop(A, m)
    copy_stop(A, m)
    hole_nine(A, m)
    heel_key(A, m)
    return {'props': COUNT['props'], 'distinct_models': len(COUNT['models'])}
