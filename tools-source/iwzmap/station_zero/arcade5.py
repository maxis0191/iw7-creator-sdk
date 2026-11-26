"""Station Zero, zone 4: the UNDERPASS ARCADE, round 5: the hall is structured (a spine of columns with islands, wall bands, pilasters), the floor is dark, the light is
few and hard (twelve live panels in clusters, shops as the lit pockets), the shop stock is large and reads from the corridor.

    python arcade5.py [folder]            writes the standalone document (map cp_iwz) to the folder (default C:\\studio-data\\sz\\arcade\\r5\\doc)
    ARC3_CAL=1 python arcade5.py <f>      the calibration variant: six floor candidates in strips, five shutter candidates (one per bay), five wall-band candidates,
                                          two extra cameras that look at them (for the first look only, never the result)

Geometry bounds, gameplay objects and the ten cameras of round 1 are kept (constants and functions come from arcade.py via arcade2.py); this file chooses the
materials and calls arcade_dress5.dress.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r'C:\studio')
import arcade2 as R2  # noqa: E402
import arcade3 as R3  # noqa: E402
from studio import Map, build as B  # noqa: E402

for _k in ('X0', 'X1', 'Y0', 'Y1', 'H', 'WT', 'BAY_X', 'BAY_W', 'BAY_D', 'BAY_H', 'AP_W', 'AP_H', 'BACK_Y', 'DOOR_Y0', 'DOOR_Y1', 'DOOR_Z', 'BAYS', 'bay_box', 'aperture',
           'gameplay', 'cameras', 'SHUT_SHARE', 'SHUT_GAP'):
    globals()[_k] = getattr(R2, _k)

def cameras(m):
    """round 5b: the two long cameras stand in the north lane (y = 4080), off the column line; two cameras added (south lane, the kiosk island). The other ten as in round 1."""
    m.use('cameras')
    B.camera(m, 'arc_east_long', (-1290.0, 4080.0, 60.0), 180.0, id='arc_east_long')
    B.camera(m, 'arc_west_long', (-2910.0, 4080.0, 60.0), 0.0, id='arc_west_long')
    B.camera(m, 'arc_south_lane_east', (-1290.0, 3700.0, 60.0), 180.0, id='arc_south_lane_east')
    B.camera(m, 'arc_spine_island', (-2700.0 + 177.0, 3900.0 + 177.0, 60.0), 225.0, id='arc_spine_island')   # 250 units north-east of the kiosk (GAPS[0] = -2700)
    for i in range(5):
        cx = BAY_X[i] + BAY_W / 2.0
        B.camera(m, 'arc_bay%d' % (i + 1), (cx, Y0 + 100.0, 64.0), 90.0, pitch=-4.0, id='arc_bay%d' % (i + 1))
    B.camera(m, 'arc_south_wall', (-2100.0, 4110.0, 64.0), 270.0, id='arc_south_wall')
    B.camera(m, 'arc_d7', (X0 + 330.0, 3900.0, 64.0), 180.0, id='arc_d7')
    B.camera(m, 'arc_inside_bay3', (BAY_X[2] + 160.0, 4345.0, 62.0), 90.0, id='arc_inside_bay3')


# materials (round 5): every surface from the vetted underpass list C:\studio-data\w1\underpass_materials.json (29 of 30 drawn in the game by Studio's W1) or proven in earlier rounds.
# The baker guesses the albedo from the NAME (layout_lights.ALBEDO_RULES, first match: black|dark|rubber .06, white|cream|ceiling|plaster|ceramic .62, chrome|steel .45, glass .2, red .25,
# yellow .45, green|blue .3, wood .3, brick .38, concrete|stone|tile|marble|floor .4, metal .32, sign|poster .45): the notes below say which rule each name falls on.
WALL = 'w/brick_cinderblock_04_beige_dirty'                      # brick .38: the painted cinder block of the upper walls
CEIL = 'w/concrete_bare_02'                                      # concrete .4
FLOOR = 'w/concrete_floor_polished_01'                           # the slab under the tile skin: collision, and the colour of the gaps
FLOOR_SKIN = 'w/building_ship_hallway_floor_06_tile_gray_glossy'   # floor .4 (dark in the game: mean 35)
SHUTTER = 'w/micro_metal_painted_01_dark_gray'
BAYWALL = ['w/brick_cinderblock_02_smooth_blue', 'w/frag_brick_painted_orange', 'w/aq_plaster_cracked_paint', 'w/brick_wall_painted_blue_01', 'w/brick_cinderblock_02_smooth_white']
BAYFLOOR = ['w/beacon_lab_floor_tile_01', 'w/wood_rustic_floor_02', 'w/ceramic_ship_interior_tile_01', 'w/clk_rubber_tiles', 'w/beacon_lab_floor_tile_02_black']
PANEL_LIVE, PANEL_DEAD = 'w/glass_led_light_diffuser_01', 'w/concrete_wall_panel_05'
WALLBAND = 'w/ceramic_tile_01_blue'                              # ceramic .62 x blue tint: the tiled wainscot of both walls
SHUT_SHARE = {0: 0.20, 1: 0.35, 2: 0.20, 3: 0.20, 4: 0.35}      # the curtain covers this share of the opening from the lintel down (round 3: 0.3 / 0.6, shops read as slits); none is jammed

EMISSIVE = dict(R3.EMISSIVE)
EMISSIVE['w/glass_led_light_diffuser_01'] = {'color': [0.80, 1.0, 0.84], 'strength': float(os.environ.get('ARC5_PANEL', '3.5'))}
LIGHTING = {'prop_shadows': True, 'ambient': float(os.environ.get('ARC5_AMBIENT', '0.003')), 'bounces': int(os.environ.get('ARC5_BOUNCES', '2')), 'emissive': EMISSIVE}


def geometry(m, standalone=True):
    m.use('shell')
    ops = [('n', aperture(i)[0], aperture(i)[1], 0.0, AP_H) for i in range(5)]
    ops.append(('e', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z))
    B.room(m, [X0, Y0, 0.0, X1, Y1, H], WALL, FLOOR, CEIL, openings=ops, thick=WT, id='corridor')
    for i in range(5):
        a0, a1 = aperture(i)
        B.room(m, bay_box(i), BAYWALL[i], BAYFLOOR[i], CEIL, openings=[('s', a0, a1, 0.0, AP_H)], thick=WT, id='bay%d' % (i + 1))
        dx0 = BAY_X[i] + 120.0
        B.wall(m, [BAY_X[i] + WT, BACK_Y, 0.0, BAY_X[i] + BAY_W - WT, BACK_Y + 12.0, BAY_H], BAYWALL[i], axis='x', openings=[(dx0, dx0 + 80.0, 0.0, 96.0)], id='partition%d' % (i + 1))
    if standalone:
        B.room(m, [X1, 3780.0, 0.0, X1 + 200.0, 4020.0, H], WALL, FLOOR, CEIL, openings=[('w', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z)], thick=WT, id='vestibule')
    m.use('dressing')


def new_map(name='arcade_r5'):
    return Map(name, 'Underpass Arcade r5', settings={'map': 'cp_iwz', 'lighting': LIGHTING, 'fog': {'color': [0.03, 0.03, 0.03], 'max_opacity': float(os.environ.get('ARC3_FOG', '0.03'))}})


def build_arcade(m, standalone=True, stage='full'):
    geometry(m, standalone)
    gameplay(m, standalone)
    cameras(m)
    import arcade_dress5
    arcade_dress5.dress(sys.modules[__name__], m, stage)
    if os.environ.get('ARC5_DBG'):
        m.use('cameras')
        B.camera(m, 'dbg_bay3', (BAY_X[2] + 160.0, 4440.0, 62.0), 90.0, id='dbg_bay3')
        B.camera(m, 'dbg_bay3b', (BAY_X[2] + 160.0, 4400.0, 62.0), 90.0, id='dbg_bay3b')
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    stage = 'full'
    if '--stage-a' in argv:
        stage = 'A'
        argv.remove('--stage-a')
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r5\doc'
    m = build_arcade(new_map(), True, stage)
    m.save(folder)
    import arcade_dress5
    arcade_dress5.make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report': getattr(m, 'dress_report', None)}, indent=1, default=str))


if __name__ == '__main__':
    main()
