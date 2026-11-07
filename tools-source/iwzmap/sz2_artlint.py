"""Static art lint of a generated Station Zero v2 source (surfaces.json + layout.json), run before any build is shown.

usage: sz2_artlint.py <src dir> [--json out.json]

Rules (lead / owner review of g24):
  failed-material  a world quad uses a material the engine gallery marked FAILED (sz2_materials: opaque squares)
  track-bed        anything drawn inside a track bed between the running rails (y 1464..1560 in the pits, track
                   height up to 40 above the bed) other than sleepers, rails, ballast and stains; decor models there
                   other than the parked train (fx_1: a yellow-covered "beam" lay between the rails)
  fake-vehicle     generated vehicle assemblies (car body / seat materials, or decor names of fake trains): the box
                   carriage of g24 read as grey concrete boxes; vehicles must be stock models
  floor-streak     a floor strip narrower than 16 and longer than 256 with a texture repeat >= 64 (stretched smear:
                   the deck inlay of g24, platform_a_2)
Exit status 1 when any rule fails.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sz2_materials as SM

PITS = [(-2400, 2592, -384), (-3540, -2416, -384)]          # track beds: x range, bed height (platform_a pit, tunnel)
BED_Y = (1464, 1560)
BED_OK = {'wood_planks', 'ballast', 'ibeam_bare', 'chrome_trim', 'metal_black', 'water_stain', 'floor_stain', 'blood_pool',
          'drip_stain', 'top_stain', 'vent', 'conc_dark'}
VEHICLE_MATS = {'metal_silver', 'carriage_red', 'seat_blue'}
TRAIN_OK = {'cp_disco_subway_train_bsp2xmodel'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--json')
    a = ap.parse_args()
    quads = json.load(open(os.path.join(a.src, 'surfaces.json')))['quads']
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    fails = []
    for zone, mat, pts, n in quads:
        m = SM.MATERIALS.get(mat, {})
        if str(m.get('verified', '')).startswith('FAILED'):
            fails.append('failed-material %s in %s at %s' % (mat, zone, pts[0]))
        if mat in VEHICLE_MATS:
            fails.append('fake-vehicle material %s in %s at %s' % (mat, zone, pts[0]))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        for x0, x1, zb in PITS:
            if min(xs) >= x0 - 1 and max(xs) <= x1 + 1 and min(ys) >= BED_Y[0] and max(ys) <= BED_Y[1] and min(zs) >= zb - 1 \
                    and max(zs) <= zb + 40 and mat not in BED_OK:
                fails.append('track-bed %s (%s) at %s' % (mat, zone, [round(c) for c in pts[0]]))
        if n[2] > 0.9 and any(abs(zs[0] - f) < 3 for f in (0, -320, -384)):      # walkable floor planes only
            w = max(xs) - min(xs); h = max(ys) - min(ys)
            if 6 <= min(w, h) < 16 and max(w, h) > 256 and m.get('su', 0) >= 64 and mat not in ('stair_tread', 'yellow_grip', 'steel_trim', 'rubber_trim', 'wood_trim', 'beam_yellow', 'ibeam') \
                    and not (mat == 'conc_painted' and min(ys) >= 1588 and max(ys) <= 1600):   # strip textures; beam tops at the ceiling; the platform coping
                fails.append('floor-streak %s %gx%g in %s at %s' % (mat, round(w), round(h), zone, [round(c) for c in pts[0]]))
    for d in lay.get('decor', []):
        x, y, z = d['origin']
        for x0, x1, zb in PITS:
            if x0 <= x <= x1 and BED_Y[0] <= y <= BED_Y[1] and zb - 1 <= z <= zb + 40 and d['model'] not in TRAIN_OK:
                fails.append('track-bed decor %s at (%g %g %g)' % (d['model'], x, y, z))
        if d['model'] in ('fake_train', 'box_train', 'box_carriage'):
            fails.append('fake-vehicle decor %s' % d['model'])
    for f in fails[:40]:
        print('ARTLINT', f)
    print('artlint fails: %d' % len(fails))
    if a.json:
        json.dump({'fails': fails}, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
