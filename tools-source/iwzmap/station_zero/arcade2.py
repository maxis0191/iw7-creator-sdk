"""Station Zero, zone 4: the UNDERPASS ARCADE, round 2: a 1978 shopping underpass of a subway station, abandoned (the bible's place, not Spaceland's).

    python arcade2.py [folder]          writes the standalone document (map cp_iwz) to the folder (default C:\studio-data\sz\arcade\r2\doc)
    ARC_CAL=1 python arcade2.py <f>     the calibration variant (floor and wall-band candidates side by side; only for the first look, never the result)

Geometry, gameplay objects and the ten cameras of round 1 are kept (constants and functions come from arcade.py); what changes is the material of every surface, the
shutters (real geometry with collision, see `shutters`), and the whole dressing and light (arcade_dress2.py).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade as R1  # noqa: E402
from studio import Map, build as B  # noqa: E402

for _k in ('X0', 'X1', 'Y0', 'Y1', 'H', 'WT', 'BAY_X', 'BAY_W', 'BAY_D', 'BAY_H', 'AP_W', 'AP_H', 'BACK_Y', 'DOOR_Y0', 'DOOR_Y1', 'DOOR_Z', 'BAYS', 'bay_box', 'aperture',
           'gameplay', 'cameras'):
    globals()[_k] = getattr(R1, _k)

# materials: only names already dumped for the build (C:\studio-data\sz\arcade\r1\dumped_materials.txt) or proven in round 1; neutral, worn, no saturated paint
WALL = 'w/plaster_wall_01_brown'
CEIL = 'w/plaster_wall_04_grey_dark_02'
FLOOR = 'w/concrete_floor_polished_01'                 # the slab under the tile skin (collision and the colour of the gaps)
SHUTTER = 'w/door_metal_rollup_grey_large_01'
BAYWALL = ['w/plaster_wall_04_grey', 'w/plaster_wall_01_brown', 'w/plaster_wall_04_beige', 'w/iw7_drywall_painted_gray_01', 'w/plaster_wall_01_beige']
BAYFLOOR = ['w/concrete_floor_polished_01', 'w/wood_rustic_floor_02', 'w/stone_marble_tile_checker_01', 'w/clk_rubber_tiles', 'w/wood_rustic_floor_02']
PANEL_LIVE, PANEL_DEAD = 'w/glass_led_light_diffuser_01', 'w/plastic_wall_panel_light_02_off'
# the shutters: bay -> (the share of the opening's height the curtain covers, from the lintel down; None = jammed: a 152 wide curtain at 60 %, an 80 wide gap)
SHUT_SHARE = {0: 0.30, 1: 0.60, 2: 0.30, 3: 0.30, 4: 0.60}
SHUT_GAP = 80.0


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


EMISSIVE = {PANEL_LIVE: {'color': [0.80, 1.0, 0.84], 'strength': 3.2},
            'w/metal_light_line_lightblue_03': {'color': [0.30, 0.85, 1.0], 'strength': 2.4}, 'w/plastic_wall_panel_light_03_on_orange': {'color': [1.0, 0.55, 0.12], 'strength': 2.4},
            'w/emissive_light_panel_pink': {'color': [1.0, 0.30, 0.68], 'strength': 2.4}, 'w/plastic_wall_panel_light_02_on_blue': {'color': [0.26, 0.45, 1.0], 'strength': 2.4},
            'w/plastic_wall_panel_light_02_on_red': {'color': [1.0, 0.18, 0.20], 'strength': 2.4}}
LIGHTING = {'prop_shadows': True, 'ambient': 0.006, 'bounces': 3, 'emissive': EMISSIVE}


def new_map(name='arcade_r2'):
    return Map(name, 'Underpass Arcade r2', settings={'map': 'cp_iwz', 'lighting': LIGHTING, 'fog': {'color': [0.12, 0.11, 0.10], 'max_opacity': 0.12}})


def build_arcade(m, standalone=True, stage='full'):
    geometry(m, standalone)
    gameplay(m, standalone)
    cameras(m)
    import arcade_dress2
    arcade_dress2.dress(sys.modules[__name__], m, stage)
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    stage = 'full'
    if '--stage-a' in argv:
        stage = 'A'
        argv.remove('--stage-a')
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r2\doc'
    m = build_arcade(new_map(), True, stage)
    m.save(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report': getattr(m, 'dress_report', None)}, indent=1, default=str))


if __name__ == '__main__':
    main()
