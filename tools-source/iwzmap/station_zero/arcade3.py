"""Station Zero, zone 4: the UNDERPASS ARCADE, round 3: the hall is structured (a spine of columns with islands, wall bands, pilasters), the floor is dark, the light is
few and hard (twelve live panels in clusters, shops as the lit pockets), the shop stock is large and reads from the corridor.

    python arcade3.py [folder]            writes the standalone document (map cp_iwz) to the folder (default C:\\studio-data\\sz\\arcade\\r3\\doc)
    ARC3_CAL=1 python arcade3.py <f>      the calibration variant: six floor candidates in strips, five shutter candidates (one per bay), five wall-band candidates,
                                          two extra cameras that look at them (for the first look only, never the result)

Geometry bounds, gameplay objects and the ten cameras of round 1 are kept (constants and functions come from arcade.py via arcade2.py); this file chooses the
materials and calls arcade_dress3.dress.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r'C:\studio')
import arcade2 as R2  # noqa: E402
from studio import Map, build as B  # noqa: E402

for _k in ('X0', 'X1', 'Y0', 'Y1', 'H', 'WT', 'BAY_X', 'BAY_W', 'BAY_D', 'BAY_H', 'AP_W', 'AP_H', 'BACK_Y', 'DOOR_Y0', 'DOOR_Y1', 'DOOR_Z', 'BAYS', 'bay_box', 'aperture',
           'gameplay', 'cameras', 'SHUT_SHARE', 'SHUT_GAP'):
    globals()[_k] = getattr(R2, _k)

# materials. Names the build already drew in earlier rounds, or in the preview's dump list; the first frame of every new one is judged in the game (FA2).
# The baker guesses the albedo of a surface from its NAME (layout_lights.ALBEDO_RULES, first match): black / dark / rubber 0.06, white / plaster / ceramic 0.62, concrete / stone /
# tile / floor 0.4: a dark name returns no bounce light, which is the lever for a dark hall.
WALL = os.environ.get('ARC3_WALL', 'w/plaster_wall_04_grey_dark_01')                 # dirty plaster above the wall band
CEIL = 'w/plaster_wall_04_grey_dark_02'
FLOOR = 'w/concrete_floor_polished_01'                                        # the slab under the tile skin: collision, and the colour of the gaps
FLOOR_SKIN = os.environ.get('ARC3_FLOOR', 'w/t7_brick_herringbone_dirty_02')   # chosen from the calibration frames (report)
SHUTTER = os.environ.get('ARC3_SHUTTER', 'w/micro_metal_painted_01_dark_gray')
BAYWALL = ['w/plaster_wall_04_turquoise', 'w/frag_brick_painted_orange', 'w/iw7_drywall_painted_purple_02', 'w/iw7_drywall_painted_blue_01', 'w/iw7_drywall_painted_red_02']
BAYFLOOR = ['w/concrete_floor_polished_01', 'w/wood_rustic_floor_02', 'w/stone_floor_tiles_01', 'w/clk_rubber_tiles', 'w/wood_rustic_floor_02']
PANEL_LIVE, PANEL_DEAD = 'w/glass_led_light_diffuser_01', 'w/plastic_fiberglass_black_01'
WALLBAND = os.environ.get('ARC3_BAND', 'w/concrete_wall_01_stained')          # the lower wall of the south wall

EMISSIVE = {PANEL_LIVE: {'color': [0.80, 1.0, 0.84], 'strength': float(os.environ.get('ARC3_PANEL', '6.0'))},
            'w/metal_light_line_lightblue_03': {'color': [0.30, 0.85, 1.0], 'strength': 2.6}, 'w/plastic_wall_panel_light_03_on_orange': {'color': [1.0, 0.55, 0.12], 'strength': 2.6},
            'w/emissive_light_panel_pink': {'color': [1.0, 0.30, 0.68], 'strength': 2.6}, 'w/plastic_wall_panel_light_02_on_blue': {'color': [0.26, 0.45, 1.0], 'strength': 2.6},
            'w/plastic_wall_panel_light_02_on_red': {'color': [1.0, 0.18, 0.20], 'strength': 2.6}}
LIGHTING = {'prop_shadows': True, 'ambient': 0.0028, 'bounces': int(os.environ.get('ARC3_BOUNCES', '1')), 'emissive': EMISSIVE}      # ambient: the bottom of the range ARCADE.md round 8 used


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


def new_map(name='arcade_r3'):
    return Map(name, 'Underpass Arcade r3', settings={'map': 'cp_iwz', 'lighting': LIGHTING, 'fog': {'color': [0.03, 0.03, 0.03], 'max_opacity': float(os.environ.get('ARC3_FOG', '0.03'))}})


def build_arcade(m, standalone=True, stage='full'):
    geometry(m, standalone)
    gameplay(m, standalone)
    cameras(m)
    import arcade_dress3
    arcade_dress3.dress(sys.modules[__name__], m, stage)
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    stage = 'full'
    if '--stage-a' in argv:
        stage = 'A'
        argv.remove('--stage-a')
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r3\doc'
    m = build_arcade(new_map(), True, stage)
    m.save(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report': getattr(m, 'dress_report', None)}, indent=1, default=str))


if __name__ == '__main__':
    main()
