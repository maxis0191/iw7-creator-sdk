r"""l2_lights: the Arcade's light design, rebuilt to stock's measured design (worker L2, 28 Nov 2026; docs/station-zero/redesign/L2-LIGHTING.md).

A post-pass on the finished document (station_doc.build calls `apply(m)` after the goods and the Terminus are in): it only changes LIGHT records and adds
light records, by id or by the source of the fixture they belong to. It touches no geometry and no goods module, so a shop-interior worker's files never
meet it. Every number below is read off the stock control room (L2-LIGHTING.md section 1): stock lights a place with few strong, narrow, shadow casting
spots (29 engine spots in a 1,400 x 1,450 box, outer half angle 20 / 40 / 45, row 3,700 / 11,000 / 28,000) so the floor has pools and dark between
them and the ceiling stays dark; the Arcade had 12 wide (85 degree) baked ceiling fills of one strength that lit walls and ceiling as much as the floor.

    ceiling troffers   12 live panels: a narrow cone straight down, engine light with its bounce baked; a share casts shadows (the columns, benches,
                       the floor machine); a share is dim (a failing tube); the dead panels (hall_body) stay unlit
    shop pools         the four coloured pools outside the fronts: stock-scale strength, a soft cone (no hard-edged disc)
    shop spill         one engine light inside each shop at its opening, aimed out at the hall: the shop's own interior light spilling over the shutter line
                       (the baker treats glass as an occluder, so the baked interior lights never reach the hall)
    colonnade tubes, wall lanterns, emergency lamps   baked, weaker
Everything stays in group `emergency` (on in both light states of the lit-first base): the darkness logic is untouched.
"""
import math
import os

# --- knobs (the env names let a variant be built for a sweep without editing the file) ---
def _f(name, default):
    return float(os.environ.get(name, default))


TROF_ROW = _f('L2_TROF', 0.9)            # strength of a bright troffer, document units (x 27,000 = the engine row; stock median 0.41, 90th percentile 1.04)
TROF_RADIUS = _f('L2_TROF_R', 330.0)
TROF_CONE = (_f('L2_TROF_IN', 18.0), _f('L2_TROF_OUT', 46.0))
POOL_K = _f('L2_POOL_K', 0.35)           # the four pools' strength against what they were
POOL_CONE = (22.0, 58.0)
SPILL_I = _f('L2_SPILL', 0.8)
SPILL_RADIUS = _f('L2_SPILL_R', 380.0)
TUBE_K = _f('L2_TUBE_K', 0.5)
INT_K = _f('L2_INT_K', 0.85)
INT_CONE = (28.0, 62.0)

# the live panels, in arcade_shell.LIVE order: (strength factor, shadows)   dim = a failing tube, 0.3
PANEL_PLAN = [(1.0, True), (0.3, False), (1.0, True), (0.8, False), (1.0, True), (0.3, False),
              (0.9, True), (1.0, False), (0.3, False), (1.0, True), (0.8, False), (1.0, True)]

REPORT = {}


def _lights(m):
    return [o for o in m.objects() if o.get('kind') == 'light']


def _prop_source(m, light_id):
    """the fixture kind of a fixture's light ('fixture_7_l1' -> 'ceiling_tube'), else None"""
    if light_id.startswith('fixture_') and '_l' in light_id:
        pid = light_id.rsplit('_l', 1)[0]
        if pid in m:
            return (m.get(pid).get('source') or '').replace('fixture:', '')
    return None


def troffers(m):
    n = 0
    for k, (f, sh) in enumerate(PANEL_PLAN):
        lid = 'light_panel_%d' % k
        if lid not in m:
            continue
        kw = dict(intensity=round(TROF_ROW * f, 3), radius=TROF_RADIUS, inner=TROF_CONE[0], outer=TROF_CONE[1], runtime=True, bake='bounce')
        if sh:
            kw['shadows'] = True
        m.update(lid, **kw)
        n += 1
    REPORT['troffers'] = n


def pools(m):
    for nm in ('needle_drop', 'copy_stop', 'hole_nine', 'heel_key'):
        lid = 'light_pool_%s' % nm
        if lid in m:
            o = m.get(lid)
            m.update(lid, intensity=round(o['intensity'] * POOL_K, 3), inner=POOL_CONE[0], outer=POOL_CONE[1])
    REPORT['pools'] = POOL_K


def fills(m):
    """the colonnade tubes and the wall lamps: weaker baked fill"""
    n = 0
    for o in _lights(m):
        kind = _prop_source(m, o['id'])
        if kind in ('ceiling_tube', 'wall_lantern', 'emergency_wall') and o.get('group') == 'emergency' and not o.get('runtime'):
            m.update(o['id'], intensity=round(o['intensity'] * TUBE_K, 3))
            n += 1
    REPORT['fills'] = n


def interiors(m, A):
    """the shops' own fills: their wide (80 to 85 degree) spots made flat, evenly lit rooms; the cone is narrowed and a little weaker so a shop has a lit counter
    and shade at its sides. Selected by position (inside a unit, y past the shop line), not by id: a goods module's numbering is not ours"""
    n = 0
    for o in _lights(m):
        if o.get('runtime') or o.get('type') != 'spot' or o.get('origin') is None:
            continue
        x, y = o['origin'][0], o['origin'][1]
        if y > A.Y1 + 4.0 and any(x0 <= x <= x1 for x0, x1 in A.UNITS.values()) and o.get('outer', 0) >= 80.0:
            m.update(o['id'], outer=INT_CONE[1], inner=min(o.get('inner', 30.0), INT_CONE[0]), intensity=round(o['intensity'] * INT_K, 3))
            n += 1
    REPORT['interiors'] = n


def spills(m, A):
    """a shop's own light over its shutter line, aimed out at the hall"""
    import sys
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import build as B
    m.use('lights')
    cols = {'needle_drop': (1.0, 0.62, 0.3), 'copy_stop': (0.82, 0.92, 1.0), 'hole_nine': (1.0, 0.55, 0.78), 'heel_key': (1.0, 0.78, 0.5)}
    for nm, (x0, x1) in A.UNITS.items():
        cx = (x0 + x1) / 2
        org = (cx, A.Y1 + 70.0, 96.0)
        d = (0.0, -1.0, -0.12)
        ln = math.sqrt(sum(c * c for c in d))
        B.light(m, org, id='l2_spill_%s' % nm, color=cols[nm], radius=SPILL_RADIUS, intensity=SPILL_I, type='spot', dir=[round(c / ln, 4) for c in d],
                inner=30.0, outer=70.0, group='emergency', bake='bounce', layer='lights')
    REPORT['spills'] = len(A.UNITS)


def apply(m, A):
    troffers(m)
    pools(m)
    fills(m)
    interiors(m, A)
    spills(m, A)
    return dict(REPORT)
