"""Light-blocking boxes for the light baker from the placed models of a generator layout (layout_lights.py --occluders).

No dependency beyond the standard library (the unit tests import it without the bake environment).
"""
import json, math, os, re

SURFACE_MODELS = re.compile(r'track|platform_edge|sleepers|trackbed|ballast|rail_|_rail')


def model_bounds(paths):
    out = {}
    for p in paths:
        if p and os.path.isfile(p):
            for m in json.load(open(p)).get('models', []):
                if m.get('bounds'):
                    out.setdefault(m['name'], m['bounds'])
    return out


def occluder_boxes(lay, bounds, light_pts, inset=0.12, min_h=16.0, min_w=8.0):
    """Light-blocking boxes for the baker from the placed models of a layout (see --occluders)."""
    raw = []
    for d in lay.get('decor', []):
        if d.get('model', '').startswith('iwz_t7e_subway_car'):
            continue                                   # train cars: from train_spec below
        if SURFACE_MODELS.search(d.get('model', '')):
            continue                                   # walkable / track-bed models: a box there blackens the floor
        x, y, z = d['origin']
        b = bounds.get(d['model'])
        if d.get('boxes'):                             # ported models: the port's world collision boxes
            for bx in d['boxes']:
                raw.append(((bx[0], bx[1], bx[2]), (bx[3], bx[4], bx[5]), d['model']))
        elif b and not (d.get('pitch') or d.get('roll')):
            c, s_ = math.cos(math.radians(d.get('yaw', 0))), math.sin(math.radians(d.get('yaw', 0)))
            xs, ys = [], []
            for lx in (b['mins'][0], b['maxs'][0]):
                for ly in (b['mins'][1], b['maxs'][1]):
                    xs.append(x + c * lx - s_ * ly); ys.append(y + s_ * lx + c * ly)
            raw.append(((min(xs), min(ys), z + b['mins'][2]), (max(xs), max(ys), z + b['maxs'][2]), d['model']))
        elif d.get('clip'):
            hx, hy, hz = d['clip']
            raw.append(((x - hx, y - hy, z), (x + hx, y + hy, z + 2 * hz), d['model']))
    for car in (lay.get('train_spec') or {}).get('cars', []):
        hx, hy, hz = car.get('nav_half', (268, 66.5, 95))
        cx, cy, cz = car['origin']
        fz = car.get('floor_z', cz + 33.3)
        raw.append(((cx - hx, cy - hy, cz + 8), (cx + hx, cy + hy, fz - 1), 'train_underframe'))
        raw.append(((cx - hx, cy - hy, cz + 2 * hz - 10), (cx + hx, cy + hy, cz + 2 * hz), 'train_roof'))
    gs = lay.get('genset')
    if gs and not any(d.get('model') == gs['model'] and d.get('boxes') for d in lay.get('decor', [])):
        (x0, y0), (x1, y1) = gs['footprint']
        z = gs['origin'][2]
        raw.append(((x0, y0, z), (x1, y1, z + 96), gs['model']))
    boxes, skipped = [], {'small': 0, 'holds_light': 0}
    for mn, mx, name in raw:
        w = min(mx[0] - mn[0], mx[1] - mn[1])
        if name not in ('train_underframe', 'train_roof') and (mx[2] - mn[2] < min_h or w < min_w):
            skipped['small'] += 1; continue
        if name not in ('train_underframe', 'train_roof'):
            ix, iy, iz = (mx[0] - mn[0]) * inset / 2, (mx[1] - mn[1]) * inset / 2, (mx[2] - mn[2]) * inset / 2
            mn, mx = (mn[0] + ix, mn[1] + iy, mn[2] + 0.5), (mx[0] - ix, mx[1] - iy, mx[2] - iz)
        if any(mn[0] - 8 <= p[0] <= mx[0] + 8 and mn[1] - 8 <= p[1] <= mx[1] + 8 and mn[2] - 8 <= p[2] <= mx[2] + 8 for p in light_pts):
            skipped['holds_light'] += 1; continue
        boxes.append({'min': [round(v, 2) for v in mn], 'max': [round(v, 2) for v in mx], 'model': name})
    return boxes, skipped
