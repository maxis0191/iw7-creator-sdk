r"""hall_dress: the Arcade hall dressed to stock density (worker AC1, 28 Nov 2026; K1-CONSTRUCTION sections 4.2 and 5).

About 40 props a 288 bay, placed with intent: a hung-tube row with its dead ones, the cables that come down through the missing ceiling panels, the
conduit run and its outlet boxes on the south wall, speakers and exit signs, benches and bins with the litter they cause, newspaper along the path of
the last night's crowd, lost property by the lockers. Every model is one K1 looked at (parts_final.json: `store show` sheets, bounds, the yaw that puts it
to a wall). Every prop is static (no network record). Floor litter has no collision; touchable furniture carries a clip box.

Called by arcade_shell.build() after hall_life; A is the arcade_shell module.
"""
import json
import math
import os
import random

from studio import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = json.load(open(os.path.join(HERE, 'parts_final.json'), encoding='utf-8'))
LAYER = 'hall_dress'


def _rot(mins, maxs, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = [(x * c - y * s, x * s + y * c) for x in (mins[0], maxs[0]) for y in (mins[1], maxs[1])]
    return min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)


def on_wall(A, m, model, wall, along, z, id, scale=1.0, gap=0.4, clip=None):
    """a model against a wall of the hall with its back flush (the yaw store show gave for that wall), centred on `along`; wall 's' (y = YS, faces +y), 'w' (x = XW, faces +x),
    'e' (x = XE, faces -x). Returns the id"""
    p = PARTS[model]
    yaw = (p.get('against_wall') or {}).get({'s': 'wall facing +y', 'w': 'wall facing +x', 'e': 'wall facing -x'}[wall], 0.0)
    mins, maxs = [v * scale for v in p['mins']], [v * scale for v in p['maxs']]
    dx0, dx1, dy0, dy1 = _rot(mins, maxs, yaw)
    if wall == 's':
        o = (along - (dx0 + dx1) / 2.0, A.YS - dy0 + gap, z)
    elif wall == 'w':
        o = (A.XW - dx0 + gap, along - (dy0 + dy1) / 2.0, z)
    else:
        o = (A.XE - dx1 - gap, along - (dy0 + dy1) / 2.0, z)
    if clip == 'auto':
        clip = [round(dx0, 1), round(dy0, 1), 0.0, round(dx1, 1), round(dy1, 1), round(min(maxs[2], 64.0), 1)]
    return B.prop(m, model, o, yaw=yaw, scale=scale, layer=LAYER, id=id, clip=clip)


def free(A, m, model, x, y, yaw, id, z=0.0, scale=1.0, clip='auto', layer=None):
    """a model standing free with the middle of its footprint on (x, y) (the yaw in degrees, any)"""
    p = PARTS[model]
    mins, maxs = [v * scale for v in p['mins']], [v * scale for v in p['maxs']]
    dx0, dx1, dy0, dy1 = _rot(mins, maxs, yaw)
    if clip == 'auto':
        clip = [round(dx0, 1), round(dy0, 1), 0.0, round(dx1, 1), round(dy1, 1), round(min(maxs[2], 64.0), 1)]
    return B.prop(m, model, (x - (dx0 + dx1) / 2.0, y - (dy0 + dy1) / 2.0, z), yaw=yaw, scale=scale, layer=layer or LAYER, id=id, clip=clip)


class Spots:
    """rejection placement over regions: out of the avoid boxes (the document's gameplay clearances and ours), `min_dist` from each other"""

    def __init__(self, A, m, avoid):
        from studio import answers
        self.boxes = [list(r['box']) for r in answers.clearance_rows(m)] + [list(b) for b in avoid]
        self.placed = [(o['origin'][0], o['origin'][1]) for o in m.objects() if o['kind'] == 'prop']
        self.m = m

    def blocked(self, x, y, pad):
        return any(b[0] - pad <= x <= b[3] + pad and b[1] - pad <= y <= b[4] + pad for b in self.boxes if len(b) == 6) or \
            any(b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad for b in self.boxes if len(b) == 4)

    def put(self, models, region, n, seed, id, min_dist=14.0, pad=10.0, scale=(1.0, 1.0), z=0.0, tries=60, yaw=(0.0, 360.0), angles=None):
        rnd = random.Random(seed)
        got = 0
        for k in range(n):
            for _ in range(tries):
                r = rnd.choice(region) if isinstance(region[0], (list, tuple)) else region
                x, y = rnd.uniform(r[0], r[2]), rnd.uniform(r[1], r[3])
                if self.blocked(x, y, pad) or any(math.hypot(x - p[0], y - p[1]) < min_dist for p in self.placed):
                    continue
                mdl = rnd.choice(models)
                a = angles(rnd) if angles else None
                B.prop(self.m, mdl, (x, y, z), yaw=rnd.uniform(*yaw), scale=round(rnd.uniform(*scale), 3), angles=a, layer=LAYER, id='%s_%d' % (id, k))
                self.placed.append((x, y))
                got += 1
                break
        return got


def build(A, m):
    rep = A.REPORT.setdefault('dress', {})
    n0 = sum(1 for o in m.objects() if o['kind'] == 'prop')
    G, YS, XW, XE, COLS, CY = A.GRID_Z, A.YS, A.XW, A.XE, A.COLS, A.COL_Y
    # ---- the ceiling: a hung-tube row with its dead ones (one a bay), the cables through the missing panels
    tube_models = ['me_lightfluohang_damaged', 'me_lightfluohang', 'me_lightfluohang_onebulb', 'me_lightfluohang', 'me_lightfluohang_on', 'me_lightfluohang_damaged', 'me_lightfluohang',
                   'me_lightfluohang_onebulb', 'me_lightfluohang_damaged', 'me_lightfluohang_on', 'me_lightfluohang_onebulb', 'me_lightfluohang_damaged', 'me_lightfluohang']
    for k, mdl in enumerate(tube_models):
        x = -2870.0 + 135.0 * k
        B.prop(m, mdl, (x, 4132.0, G - 0.4), yaw=90.0, layer=LAYER, id='dr_tube_%d' % k)
    for k, (i, j) in enumerate(A.HOLES):
        x0, y0, x1, y1 = A.module(i, j)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        B.prop(m, 'ceiling_mob_wire_bundle_01', (cx, cy, G - 100.0), yaw=37.0 * k, scale=0.9, layer=LAYER, id='dr_bundle_%d' % k)
        if k < 3:
            B.prop(m, 'hanging_wires_01_multicolored', (cx + 10.0, cy - 6.0, G - 0.5), yaw=90.0 * k + 20.0, layer=LAYER, id='dr_wires_%d' % k)
    x0, y0, x1, y1 = A.module(*A.HOLES[1])
    B.prop(m, 'ceiling_mob_wire_bundle_01', ((x0 + x1) / 2.0 + 14.0, (y0 + y1) / 2.0 + 8.0, G - 100.0), yaw=200.0, scale=0.9, layer=LAYER, id='dr_bundle_6')   # one hole with two
    # ---- the south wall's furniture of pipes and conduit
    zc = 231.0
    skip = [(-1634.0, -1486.0)]                                                   # the directory board's cap
    k = 0
    for q in range(18):
        x = -2880.0 + 76.0 * q + 38.0
        if any(a <= x <= b for a, b in skip):
            continue
        on_wall(A, m, 'com_electrical_pipe', 's', x, zc, 'dr_conduit_%d' % q)
        if q % 2 == 0:
            on_wall(A, m, 'conduit_metal_outlet_box', 's', x + 38.0, zc - 1.0, 'dr_outlet_%d' % q)
            k += 1
    for q, x in enumerate((-2780.0, -2440.0, -2140.0, -1850.0, -1380.0)):
        on_wall(A, m, 'misc_wall_mounted_loudspeaker_01', 's', x, 190.0, 'dr_speaker_%d' % q)
    on_wall(A, m, 'sign_clock_04', 's', -2205.0, 188.0, 'dr_clock')
    on_wall(A, m, 'clk_emergency_light', 's', -2985.0 + 130.0, 176.0, 'dr_emerg_0')
    on_wall(A, m, 'clk_emergency_light', 's', -1330.0, 176.0, 'dr_emerg_1')
    on_wall(A, m, 'com_standpipe_double', 's', -1345.0, 22.0, 'dr_standpipe')
    on_wall(A, m, 'greece_elec_wire_01', 's', -2450.0, 238.0, 'dr_cable_0')
    on_wall(A, m, 'greece_elec_wire_01', 's', -1900.0, 238.0, 'dr_cable_1')
    for q, (wall, along) in enumerate((('w', YS + 20.0), ('e', YS + 22.0))):         # the risers in the south corners (scaled to the 195 under the grid)
        p = PARTS['greece_pipes_02']
        if wall == 'w':
            B.prop(m, 'greece_pipes_02', (XW + 9.0, YS + 10.0, 0.0), yaw=0.0, scale=0.82, layer=LAYER, id='dr_riser_%d' % q)
        else:
            B.prop(m, 'greece_pipes_02', (XE - 9.0, YS + 10.0, 0.0), yaw=0.0, scale=0.82, layer=LAYER, id='dr_riser_%d' % q)
    # exit signs: over D4 and the blast door (lit), and two framed ones over the shops' ends; poster cases on the end walls
    on_wall(A, m, 'signage_exit_sign_emergency_only_on', 'e', 3900.0, 233.0, 'dr_exit_0')
    on_wall(A, m, 'signage_exit_sign_emergency_only_on', 'w', 3900.0, 130.0, 'dr_exit_1')
    on_wall(A, m, 'signage_exit_sign_emergency', 's', -2600.0, 200.0, 'dr_exit_2')
    on_wall(A, m, 'signage_exit_sign_emergency', 's', -1470.0, 200.0, 'dr_exit_3')
    for q, (wall, along) in enumerate((('w', 3800.0), ('w', 4180.0), ('e', 4110.0), ('e', 4190.0))):
        on_wall(A, m, 'zmb_poster_now_playing_07', wall, along, 62.0, 'dr_case_%d' % q)
    # ---- benches (the worn subway benches of the donor kit) and news boxes at the south wall
    on_wall(A, m, 'cp_disco_street_news_vending_01', 's', -2900.0, 0.0, 'dr_news_0', clip=[-15.0, -15.0, 0.0, 15.0, 15.0, 54.0])
    on_wall(A, m, 'cp_disco_street_news_vending_01', 's', -2020.0, 0.0, 'dr_news_1', clip=[-15.0, -15.0, 0.0, 15.0, 15.0, 54.0])
    # ---- the shops' sidewalk: seven stools in front of Hole Number Nine's serving counter, the coir mat at Needle Drop's door
    for q in range(7):
        free(A, m, 'cp_disco_bar_stool_01' if q % 2 == 0 else 'cp_disco_bar_stool_02', -1938.0 + 29.0 * q, A.Y1 - 15.0, 37.0 * q, 'dr_stool_%d' % q, clip=[-7.5, -7.5, 0.0, 7.5, 7.5, 28.0])
    free(A, m, 'door_mat_coir_01', -2894.0, A.Y1 - 22.0, 90.0, 'dr_mat_nd', scale=1.7, clip=None)
    # ---- litter with a cause
    avoid = [[x - 20.0, CY - 20.0, 0.0, x + 20.0, CY + 20.0, 20.0] for x in COLS]
    sp = Spots(A, m, avoid)
    lane = [-2930.0, 4064.0, -1250.0, 4204.0]            # the lane in front of the shops: the walking path of the last crowd
    sp.put(['newspaper_single_fn_01'], lane, 14, 11, 'dr_news_sheet', min_dist=34.0, yaw=(0, 360))
    sp.put(['com_debris_paper_iw6_01', 'com_debris_paper_iw6_02'], lane, 12, 12, 'dr_papers', min_dist=40.0, scale=(0.8, 1.0))
    sp.put(['office_paper_piece01_iw6'], [lane, [-2930.0, 3770.0, -1250.0, 3840.0]], 22, 13, 'dr_loose', min_dist=22.0)
    south = [-2930.0, 3760.0, -1250.0, 3838.0]           # under the benches, phones and bins: the commuters' litter
    sp.put(['food_trash_cigarettes'], south, 14, 14, 'dr_butts', min_dist=16.0, pad=4.0)
    sp.put(['com_magazine_english_single_01_dyn'], [south, [-2930.0, 3880.0, -1250.0, 4020.0]], 10, 15, 'dr_mag', min_dist=30.0)
    sp.put(['newspaper_single_fn_01'], south, 10, 16, 'dr_news_sheet_s', min_dist=30.0)
    sp.put(['newspaper_stack_fn_01'], [[-2900.0, 3770.0, -2800.0, 3840.0], [-2060.0, 3770.0, -1980.0, 3840.0], [-1900.0, 4180.0, -1800.0, 4226.0], [-2700.0, 4180.0, -2620.0, 4226.0]],
           8, 17, 'dr_npstack', min_dist=40.0, pad=6.0)       # the bundles delivered and not collected: by the news boxes and the shop doors
    sp.put(['misc_luxury_bag_01', 'misc_luxury_bag_02', 'misc_luxury_bag_03'], [[-2560.0, 3764.0, -2380.0, 3840.0], [-1640.0, 4090.0, -1520.0, 4190.0]], 6, 18, 'dr_bag', min_dist=36.0, pad=6.0)
    sp.put(['misc_duffelbag_01'], [[-2970.0, 3770.0, -2920.0, 3830.0], [-1690.0, 3770.0, -1650.0, 3830.0]], 2, 19, 'dr_duffle', min_dist=40.0, pad=6.0)
    sp.put(['trash_can_garbagebin_trashbundle_static_no_logo'], [[-2250.0, 3764.0, -2170.0, 3840.0], [-2700.0, 3764.0, -2640.0, 3840.0], [-1450.0, 4090.0, -1380.0, 4200.0]], 5, 20, 'dr_trash', min_dist=40.0, pad=6.0)
    sp.put(['food_trash_container_02_open'], [south, lane], 8, 21, 'dr_container', min_dist=24.0)
    sp.put(['food_trash_burger_box_01_open'], [south, lane], 5, 22, 'dr_burger', min_dist=22.0)
    rep['props_added'] = sum(1 for o in m.objects() if o['kind'] == 'prop') - n0
