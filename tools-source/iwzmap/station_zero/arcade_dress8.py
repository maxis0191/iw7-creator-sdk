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
SHOP_SIGN = ('neon_open', 'neon_peep', 'neon_crank', 'neon_bar', 'neon_tube')       # one stock neon per shop, in the shop's hue
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
    for k, x in enumerate(D4.COLS):
        if D4.COLSPEC[k]['feature'] == 'lightbox':
            for sgn in (-1, 1):
                n += F.fixture(m, 'light_box', (x, D4.SPINE_Y + sgn * 15.0, 118.0), 90.0 if sgn > 0 else 270.0, intensity=0.7, zone='arcade', id='fx_col_%d_%d' % (k, sgn > 0))
    m.use('dressing')
    report['fixtures8'] = {'dropped': gone, 'placed': len([x for x in n if not str(x).endswith(tuple('l%d' % j for j in range(1, 4)))]), 'ids': len(n)}


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
    fixtures8(A, m, report)
    litter8(A, m, report)
    F.use_kit(m)
    return report
