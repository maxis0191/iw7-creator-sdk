r"""The Underpass Arcade (round 12) as a LAYER of the Station Zero document: round 11 (arcade_layer11) plus the look fixes of round 12.

    STUDIO_ROOT=C:\studio python arcade_layer12.py [folder]     writes the document (default C:\studio-data\sz\arcade\r12\layer_doc)

What round 11's review (3 independent readers, mean 7.05) agreed on, and what this file does about it:
  a. shop signs dimmer with power ON than OFF. The two states were shown with two different exposures: OFF a MANUAL one (`tonemapAuto 0`, adjust -3), ON the AUTO one
     (`tonemapAutoExposureAdjust -2.5`): the auto exposure meters the lit frame and darkens it, so a sign (fixed radiance) came out at 0.4 to 0.5 of its OFF display value
     (p98 of the sign pixels, r11 frames: 0.43 -> 0.21 in arc_bay2, 0.42 -> 0.17 in arc_west_long). The lit vision is now manual with the SAME exposure as the dark one
     (`tonemapAuto 0`, adjust ARC12_LITEV = -3): a sign has the same display value in both states, the baked light (emergency lights, ambient) the same too, and the power lights
     only add. The runtime power lights were tuned against the auto exposure: `darkness.lights.scale` (840) goes down by ARC12_SCALE_DIV so that the lit floor keeps its level.
  b. ceilings and the upper thirds crushed black: every light hangs at z 110 to 130 and points down. Uplights (warm spots pointing up, between the pillars and by them) give
     the ceiling and the upper wall a low light.
  d. conv_bench: the only runtime light that reached the hall floor there was light_fill_5_1 (studio light --cam conv_bench: ratio on/off 1.0): three downward spots over the benches.
  e. the cut wall: a head trim (lintel) over the doorway and uplights on the end wall (the black band above the wall was unlit wall: the spots stop at z 120).
  f. the column spots (hard cone on the pillar: nothing above their z 120) are softer (outer 95) and weaker; the uplights light the pillar above.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade8 as A  # noqa: E402
import arcade_dress4 as D4  # noqa: E402
import arcade_layer11 as L11  # noqa: E402
from studio import build as B  # noqa: E402

LITEV = float(os.environ.get('ARC12_LITEV', '-3.0'))
SCALE_DIV = float(os.environ.get('ARC12_SCALE_DIV', '4.0'))
UP = float(os.environ.get('ARC12_UP', '1.2'))
BASE_RECIPE = r'C:\studio-data\sz\base_r10\emit\build.json'


def light(m, origin, id, **k):
    m.use('lights')
    return B.light(m, origin, layer='lights', id=id, **k)


def vision12(m, report):
    """a. the lit vision manual, the dark one's exposure; the power lights' scale down by SCALE_DIV"""
    base = json.load(open(BASE_RECIPE, encoding='utf-8'))['darkness']
    args = list(base['args'])
    i = args.index('--lit')
    keep = [kv for kv in args[i + 1].split(';') if not kv.startswith('tonemapAutoExposureAdjust')]
    args[i + 1] = ';'.join(keep + ['tonemapAuto=0', 'tonemapExposureAdjust=%g' % LITEV])
    scale = round(base['lights']['scale'] / SCALE_DIV, 1)
    b = m.settings.setdefault('build', {})
    b['darkness'] = {'lights': {'scale': scale}, 'args': args}
    report['vision12'] = {'lit': args[i + 1], 'scale': scale}


def uplights12(m, report):
    """b. e. f."""
    n = 0
    for k, x in enumerate(D4.GAPS):                                # between the columns, both lanes: a low light on the ceiling
        for j, y in enumerate((3640.0, 4160.0)):
            if (k + j) % 2:
                continue
            light(m, (x, y, 140.0), 'light_up_%d_%d' % (k, j), color=(1.0, 0.9, 0.74), radius=120.0, intensity=round(UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=80.0)
            n += 1
    for k, x in enumerate(D4.COLS):                                # by each pillar, on its lane side: the pillar above z 120 and the ceiling over it
        light(m, (x, 3938.0, 100.0), 'light_upc_%d' % k, color=(1.0, 0.86, 0.62), radius=120.0, intensity=round(0.9 * UP, 3), type='spot', dir=(0.0, 0.0, 1.0), inner=30.0, outer=85.0)
        n += 1
    for k, y in enumerate((3640.0, 4160.0)):                       # the east end wall (the cut wall): its upper part
        light(m, (-1290.0, y, 120.0), 'light_upw_%d' % k, color=(1.0, 0.9, 0.74), radius=135.0, intensity=round(UP, 3), type='spot', dir=(1.0, 0.0, 0.5), inner=30.0, outer=85.0)
        n += 1
    for o in [o for o in m.objects() if o['kind'] == 'light' and o['id'].startswith('light_colS_')]:      # f. softer, weaker
        m.update(o['id'], inner=45.0, outer=95.0, intensity=round(o['intensity'] * 0.75, 3))
    for k, (x, y) in enumerate(((-1010.0, 4060.0), (-900.0, 4180.0), (-1080.0, 4200.0))):         # d. conv_bench
        light(m, (x, y, 120.0), 'light_bench_%d' % k, color=(1.0, 0.9, 0.72), radius=160.0, intensity=1.4, type='spot', dir=(0.0, 0.0, -1.0), inner=40.0, outer=80.0)
        n += 1
    report['uplights12'] = {'added': n}


def cutwall12(m, report):
    """e. a head trim over the doorway: a beam across the top of the opening, proud of the wall on both sides"""
    m.use('shell')
    B.box(m, (-1210.0, 3792.0, 214.0, -1190.0, 4008.0, 228.0), 'w/dt_tile_ceramic_white', id='cutwall_lintel')
    report['cutwall12'] = {'lintel': 'cutwall_lintel'}


def cameras12(m, report):
    """c. cameras inside the shops, at the back walls where the blue/white square patterns were seen"""
    m.use('cameras')
    for i, nm in ((3, 'chk_bay4'), (4, 'chk_bay5'), (2, 'chk_bay3')):
        cx = A.BAY_X[i] + A.BAY_W / 2.0
        B.camera(m, nm, (cx, 4310.0, 70.0), 90.0, id=nm)
    report['cameras12'] = ['chk_bay3', 'chk_bay4', 'chk_bay5']


def build(name='sz_arcade_r12'):
    m = L11.build(name)
    rep = {}
    vision12(m, rep)
    uplights12(m, rep)
    cutwall12(m, rep)
    cameras12(m, rep)
    m.report12 = rep
    m.report9.update(rep)
    return m


def main(argv=None):
    argv = argv or sys.argv[1:]
    folder = argv[0] if argv else r'C:\studio-data\sz\arcade\r12\layer_doc'
    m = build()
    m.save(folder)
    json.dump(m.report9, open(os.path.join(folder, 'report12.json'), 'w'), indent=1, default=str)
    L11.L8.D8.make_pictures(folder)
    print(json.dumps({'folder': folder, 'summary': m.summary(), 'report12': m.report12}, indent=1, default=str)[:3000])


if __name__ == '__main__':
    main()
