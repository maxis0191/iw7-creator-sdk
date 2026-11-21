"""Station Zero lighting design pass (AAA elevation wave 1): the bible's light plan applied to the generator's lights.

Called by station_zero2.py after its light list is complete (fixtures, trims, groups, interaction cues). It never
removes or reorders a light record (the audio layout addresses fixtures by their index in a zone) and never changes
what the runtime, the darkness build or the audio layout read (type, origin, colour, radius, intensity, group). It
adds:

1. a `bake` block per light: the shape the light baker gives it (bake/layout_lights.py reads it). A fluorescent under
   its housing lights the floor and the lower walls, not the ceiling above it; a wall bulkhead lights the wall below it
   and the floor in front, not the ceiling; a saturated emergency / signal lamp keeps its colour on its own fixture
   instead of washing a room. Before this pass every light baked as a bare omni light 20 units under the ceiling: the
   ceiling and upper walls got the same direct light as the floor, which is the even, flat "showroom" fill the g27e5
   reviews scored 4 of 10 (review B item 9, items 7 and 13: maroon and red washes with no fixture to explain them).
2. motivated accent lights (bible 02-WORLD section 8: one key colour, one accent, real darkness between pools; a light
   exists only where a fixture stands): the departure board's own amber glow in the ticket hall (ZERO's face), the
   control room's test-pattern monitor. Appended at the end of the list.
3. a per-zone design record (key, accent, darkest part, the bible zone it stands for) for layout.json and the docs.

IWZ_ELEV=0 turns the pass off (A/B against the g27e5 light list with one variable).
"""
import math

# g27 zone -> the bible place it stands for and its light plan (02-WORLD section 8, adapted to the nine built zones)
ZONE_DESIGN = {
    'ticket_hall':    {'bible': 'Fare Hall', 'key': 'warm white tubes, one row in three dead',
                       'accent': "the departure board's amber glow (ZERO's face)", 'dark': 'behind the ticket booth',
                       'key_gain': 1.5, 'key_gain_why': 'the spawn hall keeps a readable floor (its old floor light was 59 % ceiling bounce)'},
    'stair_a':        {'bible': 'Escalator Hall', 'key': 'one cool strip per landing',
                       'accent': 'train light from below', 'dark': 'the foot of the flight'},
    'platform_a':     {'bible': 'Platform A East', 'key': "the 23:47's interior light, on from the start",
                       'accent': 'the east signal', 'dark': 'the tunnel beside the last car',
                       'key_gain': 1.6, 'key_gain_why': 'review B: "properly dark and moody" already; the lobes must not darken it further'},
    'maint_corridor': {'bible': 'Staff passage (Converter Hall approach)', 'key': 'caged warm bulkheads',
                       'accent': 'the DO NOT RESTART notice under its lamp', 'dark': 'between the bulkheads'},
    'generator_room': {'bible': 'Converter Hall', 'key': 'work light over the G-2',
                       'accent': 'amber emergency lamps', 'dark': 'behind G-2'},
    'control_room':   {'bible': 'Signal Cabin / Lodestar Exchange', 'key': 'cool tubes over the signal desks, low',
                       'accent': 'the test-pattern monitor; red lamps on their own walls only', 'dark': 'the filing corner'},
    'service_tunnel': {'bible': 'Car Barn approach (tunnel)', 'key': 'work lamps in pools',
                       'accent': 'the red tunnel signal', 'dark': 'between the pools'},
    'platform_b':     {'bible': 'the closed platform', 'key': 'two surviving warm lamps',
                       'accent': 'none', 'dark': 'the bricked mouth',
                       'key_gain': 1.2, 'key_gain_why': 'two surviving lamps; the platform stays readable'},
    'stair_b':        {'bible': 'Staff Stair', 'key': 'one cool strip',
                       'accent': 'none', 'dark': 'the turn',
                       'key_gain': 1.8, 'key_gain_why': 'one lit strip; the flight must stay readable'},
}

# bake lobes (directions in world space; inner / outer: full-strength and zero cone half angles, degrees)
# key_gain (ZONE_DESIGN): the level set per zone once the fittings point down; zones not named keep 1.0 (the stairs and
# the work rooms were the over-bright, flat ones in review B item 9 and get darker on purpose)
# power_scale: the housing sends down the light an omni record sent up (measured with bake_zone_contrast.py on quick
# bakes of g27e5: without it the floor lost 30 to 50 % of its light; see docs/STATION-ZERO-AAA-W1.md)
CEILING_LOBE = {'type': 'spot', 'dir': [0.0, 0.0, -1.0], 'inner': 42, 'outer': 84, 'power_scale': 1.6}
HANG_LOBE = {'type': 'spot', 'dir': [0.0, 0.0, -1.0], 'inner': 50, 'outer': 88, 'power_scale': 1.5}   # hanging: a little up-spill
WORK_LOBE = {'type': 'spot', 'dir': [0.0, 0.0, -1.0], 'inner': 35, 'outer': 70, 'power_scale': 1.4}
WALL_POWER = 1.4
ACCENT_RADIUS_SCALE = 0.6       # saturated lamps: 96 * 2.5 * 0.6 = 144 units of bake reach (was 240)
CUE_RADIUS_SCALE = 0.5          # the amber interaction cues (darkness design) stay a local glow in the lit bake


def wall_lobe(axis, facing):
    """A bulkhead on a wall plane (axis 'x': the wall runs along x, plane y = const, faces +-y): out and down."""
    out = (0.0, 0.55 * facing) if axis == 'x' else (0.55 * facing, 0.0)
    d = (out[0], out[1], -0.835)
    n = math.sqrt(sum(c * c for c in d))
    return {'type': 'spot', 'dir': [round(c / n, 4) for c in d], 'inner': 48, 'outer': 86, 'power_scale': WALL_POWER}


def _saturated(col):
    return min(col) < 0.5 * max(col)


def apply(lights, signs=(), decor=()):
    """Mutates `lights` in place (bake blocks; accents appended) and returns the report for layout.json."""
    n0 = len(lights)
    shaped = {'ceiling': 0, 'hanging': 0, 'work': 0, 'wall': 0, 'accent_clamp': 0, 'kept_omni': 0}
    for l in lights:
        fx = l.get('fixture', '')
        col = l.get('color') or (1, 1, 1)
        if fx == 'hint_glow' and l.get('intensity'):
            l['bake'] = {'radius_scale': CUE_RADIUS_SCALE}
            shaped['cue_local'] = shaped.get('cue_local', 0) + 1
            continue
        if fx == 'train_interior' or not l.get('intensity'):
            shaped['kept_omni'] += 1
            continue
        if l.get('mount') == 'ceiling':
            l['bake'] = dict(CEILING_LOBE)
            shaped['ceiling'] += 1
        elif l.get('mount') == 'wall' and l.get('wall_axis'):
            l['bake'] = wall_lobe(l['wall_axis'], l.get('wall_facing', 1))
            shaped['wall'] += 1
        elif fx == 'flicker':
            l['bake'] = dict(HANG_LOBE)
            shaped['hanging'] += 1
        elif fx == 'work_light':
            l['bake'] = dict(WORK_LOBE)
            shaped['work'] += 1
        else:
            shaped['kept_omni'] += 1
        gain = ZONE_DESIGN.get(l.get('zone', ''), {}).get('key_gain', 1.0)
        if 'bake' in l and gain != 1.0:
            l['bake']['power_scale'] = round(l['bake'].get('power_scale', 1.0) * gain, 3)
        if _saturated(col):
            l.setdefault('bake', {})['radius_scale'] = ACCENT_RADIUS_SCALE
            shaped['accent_clamp'] += 1
    accents = []
    board = next((s for s in signs if 'departure_board' in str(s.get('key', s.get('image', ''))) and s.get('zone') == 'ticket_hall'), None)
    if board:
        cx, cy, cz = board['center']
        ax = board.get('axis')
        f = board.get('facing', -1)
        o = (cx + f * 36, cy, cz - 6) if ax == 'y' else (cx, cy + f * 36, cz - 6)
        accents.append({'zone': 'ticket_hall', 'origin': o, 'type': 'omni', 'color': (1.0, 0.66, 0.30), 'radius': 150,
                        'intensity': 0.3, 'fixture': 'board_glow', 'group': 'emergency',
                        'motive': "the split-flap departure board's own glow (bible: ZERO's face, lit before power)"})
    tv = next((d for d in decor if d.get('model') == 'com_tv2_testpattern'), None)
    if tv:
        x, y, z = tv['origin']
        accents.append({'zone': tv['zone'], 'origin': (x, y, z + 30), 'type': 'omni', 'color': (0.70, 0.85, 1.0), 'radius': 90,
                        'intensity': 0.3, 'fixture': 'screen_glow', 'group': 'power',
                        'motive': 'the test-pattern monitor on the signal desk (bible: green screens of the Exchange)'})
    lights.extend(accents)
    return {'zones': ZONE_DESIGN, 'shaped': shaped, 'lights_before': n0, 'accents': [
        {k: a[k] for k in ('zone', 'origin', 'fixture', 'motive')} for a in accents]}
