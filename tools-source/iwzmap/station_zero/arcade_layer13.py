r"""The Underpass Arcade (round 13) as a LAYER of the Station Zero document: round 11's layer (the best round, 3 readers 7.05/10) on the REGENERATED base, plus the parts of round 12 that held.

    STUDIO_ROOT=C:\studio python arcade_layer13.py [folder]     writes the document (default C:\studio-data\sz\arcade\r13\layer_doc)

What round 12 taught (numbers in C:\studio-data\sz\arcade\r12\numbers.md) and what this file does:
  1. The lit vision stays r11's AUTO exposure and the power lights stay at `darkness.lights.scale` 840 (r12's manual lit vision with scale 210 gave ON mean 0.378 against 0.239, clip 3.0 %
     against 0.57 %, and OFF frames at 0.035 against 0.089: the same scale also divides the emergency light of the dark state). Nothing of the vision is overridden here: the base's recipe is used.
  2. Signs dimmer ON than OFF (auto exposure meters the lit frame, a sign is fixed radiance: p98 0.43 -> 0.21 in arc_bay2). The neon alone gets an extra light in group `power` (on the sign,
     baked into the lit lightmap only): ON adds to the emergency light that both states have, nothing else changes.
  3. Kept from r12: the cut wall's lintel, the three conv_bench downlights. Uplights (ceiling, upper walls) at ARC13_UP (default 0.3; r12 was 1.2: top third ON 0.354).
  4. Hung graphics of bays 4 and 5 (`hg_3_*`: `w/zombies_underground_map`, a tile pattern at this size; `hg_4_*`: theater posters, dark): other materials that `store find --draw` lists.
  5. The base is `C:\studio-data\sb\base_sb` (the generator's own output: unnamed decor are static models already); arcade_base10 / base_r10 are not in the build path.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade8 as A  # noqa: E402
import arcade_dress4 as D4  # noqa: E402
import arcade_dress10 as D10  # noqa: E402
import arcade_layer8 as L8  # noqa: E402
import arcade_layer11 as L11  # noqa: E402
import arcade_layer12 as L12  # noqa: E402
from studio import build as B  # noqa: E402

BASE_EMIT = os.environ.get('ARC13_BASE', r'C:\studio-data\sb\base_sb')
UP = float(os.environ.get('ARC13_UP', '0.3'))
SIGN_ON = float(os.environ.get('ARC13_SIGN_ON', '1.8'))        # the extra ON-only sign light, times the sign's emergency light
PANEL4 = ('w/signage_theater_menu_01', 'w/signage_zmb_park_poster_04', 'w/signage_zmb_park_poster_08')
PANEL5 = ('w/signage_zmb_park_poster_05', 'w/signage_zmb_park_poster_06', 'w/signage_zmb_park_poster_07')


def uplights13(m, report):
    """r12's uplights at UP, the conv_bench downlights as they were (no softening of the column spots: round 11's)"""
    n = 0
    for k, x in enumerate(D4.GAPS):
        for j, y in enumerate((3640.0, 4160.0)):
            if (k + j) % 2:
                continue
            L12.light(m, (x, y, 140.0), 'light_up_%d_%d' % (k, j), color=(1.0, 0.9, 0.74), radius=120.0, intensity=round(UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=80.0)
            n += 1
    for k, x in enumerate(D4.COLS):
        L12.light(m, (x, 3938.0, 100.0), 'light_upc_%d' % k, color=(1.0, 0.86, 0.62), radius=120.0, intensity=round(0.9 * UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=85.0)
        n += 1
    for k, y in enumerate((3640.0, 4160.0)):
        L12.light(m, (-1290.0, y, 120.0), 'light_upw_%d' % k, color=(1.0, 0.9, 0.74), radius=135.0, intensity=round(UP, 3), type='spot', dir=(1.0, 0.0, 0.5), inner=30.0, outer=85.0)
        n += 1
    for k, (x, y) in enumerate(((-1010.0, 4060.0), (-900.0, 4180.0), (-1080.0, 4200.0))):
        L12.light(m, (x, y, 120.0), 'light_bench_%d' % k, color=(1.0, 0.9, 0.72), radius=160.0, intensity=1.4, type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
        n += 1
    report['uplights13'] = {'added': n, 'up': UP}


def signs13(m, report):
    """an extra light on each shop neon, group power: only the lit state has it"""
    ids = []
    m.use('lights')
    for i in range(1, 6):
        pid = 'fx_sign_%d_l1' % i
        if pid not in m:
            continue
        o = m.get(pid)
        kw = dict(color=o['color'], radius=o['radius'], intensity=round(o['intensity'] * SIGN_ON, 3), group='power', type=o['type'], zone=o.get('zone'), id='fx_sign_%d_on' % i)
        if o['type'] == 'spot':
            kw.update(dir=o['dir'], inner=o.get('inner'), outer=o.get('outer'))
        B.light(m, o['origin'], layer='lights', **kw)
        ids.append(kw['id'])
    report['signs13'] = {'on_lights': ids, 'factor': SIGN_ON}


def panels13(m, report):
    """the hung graphics of bays 4 and 5 with materials that draw as posters"""
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'box' and str(o['id']).startswith(('hg_3_', 'hg_4_')) and not str(o['id']).endswith(('_ra', '_rb'))]:
        i, k = str(o['id']).split('_')[1:3]
        pool = PANEL4 if i == '3' else PANEL5
        m.update(o['id'], material=pool[int(k) % len(pool)])
        n += 1
    report['panels13'] = {'updated': n}


def gameplay13(m, report):
    """DG's two fixes. FE24: the base hall bench (cp_disco_worn_subway_bench at -1138 4000) and its clip box stand in the D4 opening (y 3804-3996): removed.
    FE42: the bay spawners at y 4535 (facing south) carry the zombie's emergence up to 62 units into the partition walls (y 4470-4482): moved to y 4565."""
    m.use('arcade_door' if 'arcade_door' in m.layers else 'shell')
    B.replace(m, box=[-1170, 3900, -1, -1106, 4100, 100], what=['props'], id='clear_bench_props')
    B.replace(m, box=[-1170, 3900, 2, -1106, 4100, 100], what=['collision'], clip=True, id='clear_bench_clip')
    n = 0
    for o in [o for o in m.objects() if o['kind'] == 'spawner' and str(o['id']).startswith('spawn_b')]:
        x, y, z = o['at']
        m.update(o['id'], at=[x, 4565.0, z])
        n += 1
    report['gameplay13'] = {'bench_replace': 2, 'spawners_moved': n}


def build(name='sz_arcade_r13'):
    A.BAYWALL[2] = 'w/brick_cinderblock_04_beige_dirty'               # as round 11
    A.BAYFLOOR[2] = 'w/building_ship_hallway_floor_06_tile_gray_glossy'
    L8.BASE = BASE_EMIT
    D10.install()
    m = L8.build(name)
    rep = {}
    L11.fixes9(m, rep)
    L11.unclip_columns(m, rep)
    L11.settle(m, rep)
    L11.lights9(m, rep)
    L11.lights11(m, rep)
    L11.emergency9(m, rep)
    L11.cameras10(m, rep)
    rep['base13'] = {'emit': BASE_EMIT}
    d = m.dresser
    rep['placer'] = {'placed': d.n, 'totals': d.ledger.totals(), 'lines': d.lines(), 'clip_boxes': len(d.clip_boxes)}
    rep['dress_refusals'] = dict(D10.REPORT)
    uplights13(m, rep)
    signs13(m, rep)
    L12.cutwall12(m, rep)
    L12.cameras12(m, rep)
    panels13(m, rep)
    gameplay13(m, rep)
    m.report9 = rep
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r13\layer_doc'
    m = build()
    m.save(folder)
    json.dump(m.report9, open(os.path.join(folder, 'report13.json'), 'w'), indent=1, default=str)
    L8.D8.make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report13': {k: v for k, v in m.report9.items() if k not in ('settle_log', 'placer', 'dress_refusals')}}, indent=1, default=str)[:4000])


if __name__ == '__main__':
    main()
