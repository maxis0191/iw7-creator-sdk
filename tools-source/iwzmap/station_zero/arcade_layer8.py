r"""The Underpass Arcade (round 8) as a LAYER of the Station Zero document: base = the g27r emit, layers = the Arcade's shell, dressing, gameplay, lights and cameras.

    STUDIO_ROOT=C:\studio python arcade_layer8.py [folder]     writes the document (default C:\studio-data\sz\arcade\r8\layer_doc)

Same place as round 4 (box x -3000..-1200, y 3500..4300, shops to y 4600; the door D4 is cut into the ticket hall's west wall at x = -1200). The base already holds every perk
machine and three magic wheels, so the layer holds no perk and no wheel; it holds the zone, the door, twelve spawners and two wall buys. Geometry, dressing, lights, cameras
are round 8's (arcade8 / arcade_dress8), built with standalone=False (no vestibule, no start).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade8 as A  # noqa: E402
import arcade_dress8 as D8  # noqa: E402
from studio import Map, build as B  # noqa: E402

BASE = r'C:\studio-data\sz\base\emit'


def gameplay(m):
    m.use('gameplay')
    B.zone(m, 'arcade', [A.X0, A.Y0, -16.0, A.X1, A.Y1 + A.BAY_D, A.H + 14.0])
    B.door(m, 'd_hall_arcade', [A.X1 - 8.0, A.DOOR_Y0, 0.0, A.X1 + 8.0, A.DOOR_Y1, A.DOOR_Z], 1000, zones=['arcade', 'ticket_hall'], id='door_D4')
    for i in range(5):
        for k, dx in enumerate((62.0, 258.0)):
            B.spawner(m, (A.BAY_X[i] + dx, 4535.0, 0.0), 270.0, id='spawn_b%d_%d' % (i + 1, k + 1))
    B.spawner(m, (A.X1 - 90.0, 3640.0, 0.0), 90.0, id='spawn_c_east')
    B.spawner(m, (A.X0 + 100.0, 3640.0, 0.0), 0.0, id='spawn_c_west')
    B.wallbuy(m, (-2560.0, A.Y0 + A.WT + 6.0, 0.0), 'smg', 1000, 90.0, id='buy_smg')
    B.wallbuy(m, (-1860.0, A.Y0 + A.WT + 6.0, 0.0), 'marksman', 1500, 90.0, id='buy_marksman')


def build(name='sz_arcade_r8'):
    m = Map(name, 'Station Zero with the Underpass Arcade', base={'kind': 'emit', 'path': BASE}, settings={'map': 'cp_iwz'})
    m.use('arcade_door')
    B.doorway(m, [A.X1 - 4.0, A.DOOR_Y0, 0.0, A.X1 + 4.0, A.DOOR_Y1, A.DOOR_Z], 'w/dt_tile_ceramic_white', id='arcade_doorway')
    A.geometry(m, standalone=False)
    gameplay(m)
    A.cameras(m)
    D8.dress(A, m, 'full')
    m.use('cameras')                      # cut wall: from the hall side, looking west through D4; from the Arcade side, looking east at the opening
    B.camera(m, 'hall_far', (-700.0, 3900.0, 64.0), 180.0, id='hall_far')
    B.camera(m, 'hall_near', (-1050.0, 3880.0, 64.0), 180.0, id='hall_near')
    B.camera(m, 'hall_door', (-1130.0, 3900.0, 64.0), 175.0, pitch=-2.0, id='hall_door')
    B.camera(m, 'arc_cutwall', (-1450.0, 3900.0, 64.0), 0.0, id='arc_cutwall')
    B.camera(m, 'arc_cutwall_close', (-1290.0, 3880.0, 64.0), 0.0, id='arc_cutwall_close')
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r8\layer_doc'
    m = build()
    m.save(folder)
    D8.make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report': getattr(m, 'dress_report', None)}, indent=1, default=str)[:4000])


if __name__ == '__main__':
    main()
