"""Station Zero, zone 4: the UNDERPASS ARCADE (round 1), a Studio document in final world coordinates.

    python arcade.py [folder]          writes the standalone document (map cp_iwz) to the folder (default C:\\studio-data\\sz\\arcade\\r1\\doc)
    build_arcade(m, standalone=True)   adds the section to a studio Map (standalone=False: no start, no vestibule room, no map settings)

Units inches, z up. Corridor box x -3000..-1200, y 3500..4300, floor 0, ceiling 256 (a hung panel grid at z 180..184 under a dark ceiling);
five shop bays on its north side (320 x 300, y 4300..4600), each open to the corridor by a 232 x 120 aperture with a roller shutter half up above it
and a back room behind a walk-in doorway; D4 (east end, y 3804..3996) to the Fare Hall; D7 (west end) a closed blast door.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import Map, build as B  # noqa: E402

X0, X1, Y0, Y1, H = -3000.0, -1200.0, 3500.0, 4300.0, 256.0
WT = 16.0                                   # wall thickness inside the boxes (as examples/arcade.py)
BAY_X = [-2960.0, -2630.0, -2300.0, -1970.0, -1640.0]
BAY_W, BAY_D, BAY_H = 320.0, 300.0, 200.0
AP_W, AP_H = 232.0, 120.0                   # the aperture of a shop front
BACK_Y = 4470.0                             # the partition of every bay: back room y 4482..4584
DOOR_Y0, DOOR_Y1, DOOR_Z = 3804.0, 3996.0, 224.0

# materials (those of examples/arcade.py are proven in the game; the others are new and judged on the first frames)
WALL, CEIL = 'w/plaster_wall_01_brown', 'w/plaster_wall_04_grey_dark_02'
FLOOR = 'w/wood_rustic_floor_02'
FLOOR_B = 'w/stone_marble_tile_checker_01_brown'
SHUTTER = 'w/door_metal_rollup_grey_large_01'
BAYWALL = ['w/plaster_wall_04_turquoise', 'w/frag_brick_painted_orange', 'w/plaster_wall_04_beige', 'w/iw7_drywall_painted_blue_01', 'w/iw7_drywall_painted_red_02']
PANEL_LIVE, PANEL_DEAD = 'w/glass_led_light_diffuser_01', 'w/plastic_wall_panel_light_02_off'
BAYS = ['photo', 'heel', 'hole9', 'copy', 'needle']


def bay_box(i):
    return [BAY_X[i], Y1, 0.0, BAY_X[i] + BAY_W, Y1 + BAY_D, BAY_H]


def aperture(i):
    cx = BAY_X[i] + BAY_W / 2.0
    return cx - AP_W / 2.0, cx + AP_W / 2.0


def geometry(m, standalone=True):
    m.use('shell')
    ops = [('n', aperture(i)[0], aperture(i)[1], 0.0, AP_H) for i in range(5)]
    ops.append(('e', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z))
    B.room(m, [X0, Y0, 0.0, X1, Y1, H], WALL, FLOOR, CEIL, openings=ops, thick=WT, id='corridor')
    for i in range(5):
        a0, a1 = aperture(i)
        bx = bay_box(i)
        B.room(m, bx, BAYWALL[i], FLOOR, CEIL, openings=[('s', a0, a1, 0.0, AP_H)], thick=WT, id='bay%d' % (i + 1))
        # the partition and the walk-in doorway of the back room (zombies spawn behind it)
        dx0 = BAY_X[i] + 120.0
        B.wall(m, [BAY_X[i] + WT, BACK_Y, 0.0, BAY_X[i] + BAY_W - WT, BACK_Y + 12.0, BAY_H], BAYWALL[i], axis='x', openings=[(dx0, dx0 + 80.0, 0.0, 96.0)], id='partition%d' % (i + 1))
    if standalone:                        # the vestibule east of D4: a closed 200 deep room so that the opening is real
        B.room(m, [X1, 3780.0, 0.0, X1 + 200.0, 4020.0, H], WALL, FLOOR, CEIL, openings=[('w', DOOR_Y0, DOOR_Y1, 0.0, DOOR_Z)], thick=WT, id='vestibule')
    # the west end: D7, a closed blast door (dressing only), half wound
    m.use('dressing')


def gameplay(m, standalone=True):
    m.use('gameplay')
    B.zone(m, 'arcade', [X0, Y0, -16.0, X1, Y1 + BAY_D, H + 14.0])
    if standalone:
        B.zone(m, 'vestibule', [X1, 3780.0, -16.0, X1 + 200.0, 4020.0, H + 14.0])
        B.door(m, 'D4', [X1 - 8.0, DOOR_Y0, 0.0, X1 + 8.0, DOOR_Y1, DOOR_Z], 1000, zones=['arcade', 'vestibule'], id='door_D4')
        B.start(m, (X1 - 110.0, 3900.0, 0.0), 180.0, id='start_1')
    for i in range(5):                    # two spawners behind each doorway
        for k, dx in enumerate((62.0, 258.0)):
            B.spawner(m, (BAY_X[i] + dx, 4535.0, 0.0), 270.0, id='spawn_b%d_%d' % (i + 1, k + 1))
    B.spawner(m, (X1 - 90.0, 3640.0, 0.0), 90.0, id='spawn_c_east')
    B.spawner(m, (X0 + 100.0, 3640.0, 0.0), 0.0, id='spawn_c_west')
    # perk at the photo booth (bay 1), the wheel in Copy Stop (bay 4), two wall buys on the south wall
    B.perk(m, (BAY_X[0] + 24.0, 4385.0, 0.0), 'revive', 0.0, id='perk_photo')
    B.wheel(m, (BAY_X[3] + 28.0, 4385.0, 0.0), 0.0, id='wheel_copy')
    B.wallbuy(m, (-2560.0, Y0 + WT + 6.0, 0.0), 'smg', 1000, 90.0, id='buy_smg')
    B.wallbuy(m, (-1860.0, Y0 + WT + 6.0, 0.0), 'marksman', 1500, 90.0, id='buy_marksman')


def cameras(m):
    m.use('cameras')
    B.camera(m, 'arc_east_long', (X1 - 40.0, 3900.0, 64.0), 180.0, id='arc_east_long')
    B.camera(m, 'arc_west_long', (X0 + 40.0, 3900.0, 64.0), 0.0, id='arc_west_long')
    for i in range(5):
        cx = BAY_X[i] + BAY_W / 2.0
        B.camera(m, 'arc_bay%d' % (i + 1), (cx, Y0 + 100.0, 64.0), 90.0, pitch=-4.0, id='arc_bay%d' % (i + 1))
    B.camera(m, 'arc_south_wall', (-2100.0, 4110.0, 64.0), 270.0, id='arc_south_wall')
    B.camera(m, 'arc_d7', (X0 + 330.0, 3900.0, 64.0), 180.0, id='arc_d7')
    B.camera(m, 'arc_inside_bay3', (BAY_X[2] + 160.0, 4345.0, 62.0), 90.0, id='arc_inside_bay3')


def build_arcade(m, standalone=True, stage='full'):
    geometry(m, standalone)
    gameplay(m, standalone)
    cameras(m)
    if stage != 'A':
        import arcade_dress
        arcade_dress.dress(sys.modules[__name__], m)
    return m


EMISSIVE = {PANEL_LIVE: {'color': [0.72, 1.0, 0.78], 'strength': 1.6},
            'w/metal_light_line_lightblue_03': {'color': [0.10, 0.85, 1.0], 'strength': 2.6}, 'w/zmb_neon_orange': {'color': [1.0, 0.52, 0.08], 'strength': 2.6},
            'w/emissive_light_panel_pink': {'color': [1.0, 0.22, 0.68], 'strength': 2.6}, 'w/plastic_wall_panel_light_02_on_blue': {'color': [0.22, 0.42, 1.0], 'strength': 2.6},
            'w/plastic_wall_panel_light_02_on_red': {'color': [1.0, 0.14, 0.18], 'strength': 2.6}}
LIGHTING = {'prop_shadows': True, 'ambient': 0.006, 'bounces': 3, 'emissive': EMISSIVE}


def new_map(name='arcade_r1'):
    return Map(name, 'Underpass Arcade r1', settings={'map': 'cp_iwz', 'lighting': LIGHTING, 'fog': {'color': [0.10, 0.08, 0.12], 'max_opacity': 0.30}, 'exposure': {'adjust': -0.2}})


def main(argv=None):
    argv = argv or sys.argv[1:]
    stage = 'full'
    if '--stage-a' in argv:
        stage = 'A'
        argv.remove('--stage-a')
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r1\doc'
    m = build_arcade(new_map(), True, stage)
    m.save(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary()}, indent=1))


if __name__ == '__main__':
    main()
