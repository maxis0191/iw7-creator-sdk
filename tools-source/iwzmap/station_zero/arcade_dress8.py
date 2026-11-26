"""arcade_dress8: round 7 plus Studio's new tools (DT, 26 Nov 2026). Round 7's compile skipped 105 of 108 foreign static models (`use_kit` brings them now); its lamps and signs
were blank emissive slabs (now `B.fixture`: a stock lit model with its light); its litter was an evenly spaced grid (now `P.scatter` themes: commuter, shop spill, cleaning,
abandoned). Everything else is round 7."""
import os

import arcade_dress7 as D7
import arcade_dress4 as D4
import arcade_dress6 as D6
from studio import build as B
from studio import fixtures as F
from studio import props as P

M = D4.M
make_pictures = D7.make_pictures
SHOP_SIGN = ('neon_open', 'neon_tube', 'bulb_strip', 'neon_open', 'neon_tube')       # one stock neon per shop, in the shop's hue
LITTER = ('chips', 'cup', 'paper', 'can', 'smokes', 'stackp', 'mags', 'mug', 'crate1', 'crate2', 'cone', 'bucket', 'pallet', 'stool2', 'fchair', 'barrel')


def drop_ids(m, pred):
    n = 0
    for pid in [o['id'] for layer in m.layers.values() for o in layer if pred(o)]:
        m.remove(pid)
        n += 1
    return n


def fixtures8(A, m, report):
    """the blank emissive slabs go: ceiling strips of the shops, back wall header strips, aperture neon frames, column light boxes; stock fixtures with their light take their place"""
    gone = {}
    for pre in ('strip_h_', 'strip_', 'hdr_strip_', 'neon_top_', 'neon_l_', 'neon_r_', 'col_lbframe_', 'col_lb_'):
        gone[pre] = D6.drop(m, pre)
    for pre in ('light_neon_',):
        gone[pre] = drop_ids(m, lambda o, pre=pre: str(o['id']).startswith(pre))
    m.use('lights')
    n = []
    for i in range(5):
        a0, a1 = A.aperture(i)
        cx = (a0 + a1) / 2.0
        hue = D4.HUE[A.BAYS[i]]
        # the shop sign over the aperture, on the corridor face of the north wall
        n += F.fixture(m, SHOP_SIGN[i], (cx, A.Y1 - A.WT - 1.0, 196.0), 270.0, color=hue, group='power', zone='arcade', id='fx_sign_%d' % (i + 1))
        for dx in (-70.0, 70.0):                                          # the shop's own ceiling tubes replace the strips
            n += F.fixture(m, 'ceiling_tube', (cx + dx, A.Y1 + 70.0, A.BAY_H - 2.0), 0.0, kelvin=3600, intensity=0.7, zone='arcade', id='fx_tube_%d_%d' % (i + 1, int(dx > 0)))
        n += F.fixture(m, 'light_box', (cx, A.BACK_Y + 14.0, 118.0), 270.0, color=hue, intensity=0.8, zone='arcade', id='fx_back_%d' % (i + 1))
    for k, x in enumerate(D4.COLS):                                       # the column light boxes were blank white: a poster on each face instead (stock picture materials)
        if D4.COLSPEC[k]['feature'] == 'lightbox':
            for sgn in (-1, 1):
                B.decal(m, D4.POSTERS[(k + (2 if sgn > 0 else 0)) % len(D4.POSTERS)], (x, D4.SPINE_Y + sgn * 15.5, 118.0), (0.0, float(sgn), 0.0), (24.0, 34.0), id='fx_colposter_%d_%d' % (k, sgn > 0))
    m.use('dressing')
    report['fixtures8'] = {'dropped': gone, 'placed': len([x for x in n if not str(x).endswith(tuple('l%d' % j for j in range(1, 4)))]), 'ids': len(n)}


CANON = {'cp_disco_sign_01': 'PHOTOS', 'cp_disco_sign_02': 'HEEL & KEY', 'cp_disco_sign_04': 'COPY STOP'}   # the hanging boards carried other shops' names: our bays' own names (already on the map)


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
            B.sign(m, text=text, at=(cx, cy + sgn * 1.0, z), normal=(0.0, float(sgn), 0.0), size=(76.0, 40.0), emissive=1.2, color=(1.0, 0.82, 0.4), id='cn_%s_%d_%d' % (text[:4].strip(), k, sgn > 0))
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
        r = P.scatter(m, area, theme, density=dens, seed=80 + seed, rules=dict(extra, cap=3), zone='arcade', id_prefix='lit_' + theme.replace(' ', '_'))
        reps[theme] = {k: r[k] for k in ('clusters', 'props', 'distinct_models', 'nn_cv', 'nn_index', 'rejected')}
    report['litter8'] = {'dropped_grid_props': gone, 'themes': reps}


def dress(A, m, stage='full', foreign=None):
    report = D7.dress(A, m, stage, foreign)
    if not os.environ.get('ARC8_NOFX'):
        fixtures8(A, m, report)
    canon8(A, m, report)
    if not os.environ.get('ARC8_NOLIT'):
        litter8(A, m, report)
    F.use_kit(m)
    return report
