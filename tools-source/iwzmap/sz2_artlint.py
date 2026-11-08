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
  void-black       a world quad with the unlit `black` material (review A3/B: flat black voids in windows, panels,
                   vents, clock faces); only the gallery may use it
  uv-aspect        a stock material whose texture repeat (su/sv) differs from its measured image aspect by more than 10%
                   (material_dims.json; review A6: trims mapped square were stretched 4-16x)
  uv-sliver        (note only) a world-projected non-trim face thinner than 1/16 of a texture repeat and longer than one
                   repeat: it shows a thin band of the texture at true density, which is not a stretch
  material-role    tactile/grip paving on anything but a floor (review B: tactile strip used as wall trim)
  tone             decor from another map's identity (Spaceland park props, ride cars, Racin' Stripes) or the wood
                   mine support (review A10)
  fake-object      a generated box assembly standing in for an object that has a stock model (turnstile, desk, console,
                   booth, kiosk, generator, hvac, buffer) (review A2)
  anchor           a wall/ceiling-mounted decor model (pipes, signs, lamps, panels, lockers, cabinets, fans, speakers)
                   whose origin is more than 24 units from any world surface (review A7: floating pipes, lockers off the wall)
  intersect        two decor clip boxes overlapping by more than 30% of the smaller one, or a sign overlapping a
                   decor clip box (review A7: board through a crate, signs on lamps and pipes)
  sign-dupe        the same sign image twice within 600 units in one zone (review A8: stacked duplicate signs)
  trackbed         (layout track_spec, coordinator 2026-11-08) any level surface other than the bed floor inside a
                   trackbed channel volume (channel x/y less 4 units at its walls, 0.5..170 above the bed = car envelope: walls, piers, ribs, generated rails,
                   ties, beams, buffers), any decor inside a channel, a channel whose centre is not the middle of its
                   y range, rails not symmetric about the centre, or a tunnel door not spanning the channel
  stair-tactile    tactile paving on more than two tread heights of one stair (review C: all-yellow treads)
  decal-aspect     a stock decal (layout decals) whose w/h differs from its image aspect by more than 15% (review C)
  colour-cast      a baked coloured light (channel spread > 0.4) without a fixture or with a radius over 192
                   (reviews A9/B: red, green, pink and mustard casts with no visible source)
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
EDGE = 4.0           # trackbed: wall trims up to 4 units proud of a channel side or end wall belong to the wall
ENVELOPE = 170.0     # trackbed: car kinematic envelope above the bed (cable trays and ceiling ribs above it are fine)
TONE_BANNED = ('park_', 'spaceland', 'zmb_wood_support', '_ride_', 'ride_car', 'racin', 'astrocade', 'kepler')
TONE_OK = {'park_token_machine', 'zmb_spaceland_zombie_spawn_window_01'}   # token machine fits a hall; spawn window is gameplay
FAKE_OBJECTS = ('turnstile', 'desk', 'console', 'booth', 'kiosk', 'generator', 'hvac', 'buffer')
MOUNTED = ('pipe', 'sign', 'lamp', 'light', 'panel', 'locker', 'cabinet', 'fan', 'loudspeaker', 'control_box', 'shutoff',
           'fuse_box', 'vent', 'wires')
MOUNTED_FREE = ('standing', 'traffic', 'sign_clock', 'pardon_our_dust')   # floor-standing despite the name; clocks hang
GRIP = {'yellow_grip'}


def pt_box_dist(p, mn, mx):
    return sum(max(mn[i] - p[i], 0, p[i] - mx[i]) ** 2 for i in range(3)) ** 0.5


def box_overlap(a0, a1, b0, b1):
    v = 1.0
    for i in range(3):
        d = min(a1[i], b1[i]) - max(a0[i], b0[i])
        if d <= 0:
            return 0.0
        v *= d
    return v


def decor_box(d):
    x, y, z = d['origin']
    cx, cy, cz = d.get('clip') or (0, 0, 0)
    return (x - cx, y - cy, z), (x + cx, y + cy, z + 2 * cz)     # clip = half extents (decor() in the generator)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--json')
    a = ap.parse_args()
    quads = json.load(open(os.path.join(a.src, 'surfaces.json')))['quads']
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    fails = []
    spec = lay.get('track_spec') or {}
    channels = spec.get('channels', [])
    # train kit (IWZ_TRAIN, train agent): the platform edge comes forward to train_spec.edge_y over the channel (deck
    # overhang); the channel ends there, and the kit's own models (iwz_*) are the track, car and edge, not intruders
    tspec = lay.get('train_spec') or {}
    env_channels = [dict(ch, y1=min(ch['y1'], tspec['edge_y'] + EDGE)) for ch in channels] if tspec.get('edge_y') else channels
    for ch in channels:
        if abs(ch['centre_y'] - (ch['y0'] + ch['y1']) / 2) > 0.5:
            fails.append('trackbed %s channel off-centre: centre %g, middle %g' % (ch['zone'], ch['centre_y'], (ch['y0'] + ch['y1']) / 2))
    if spec.get('rail_y') and abs(sum(spec['rail_y']) / 2 - spec.get('centre_y', 0)) > 0.5:
        fails.append('trackbed rails not centred: %s about %s' % (spec['rail_y'], spec.get('centre_y')))
    for dr in lay.get('doors', []):
        if dr.get('name') == 'd_platform_tunnel' and channels:
            a_, b_ = dr.get('a'), dr.get('b')
            if a_ is not None and (abs(a_ - channels[0]['y0']) > 0.5 or abs(b_ - channels[0]['y1']) > 0.5):
                fails.append('trackbed: tunnel door %s..%s does not span the channel %s..%s' % (a_, b_, channels[0]['y0'], channels[0]['y1']))
    grip_treads = {}
    for zone, mat, pts, n in quads:
        if mat == 'yellow_grip' and n[2] > 0.9 and zone.startswith('stair'):
            grip_treads.setdefault(zone, set()).add(round(pts[0][2]))
    for zone, zs in grip_treads.items():
        if len(zs) > 2:
            fails.append('stair-tactile %s has tactile paving on %d tread heights' % (zone, len(zs)))
    for l in lay.get('lights', []):
        col = l.get('color', (1, 1, 1))
        if max(col) - min(col) > 0.4 and (not l.get('fixture') or l.get('radius', 384) > 192):
            fails.append('colour-cast %s light in %s at %s radius %s' % (l.get('fixture'), l['zone'], l['origin'], l.get('radius')))
    for dc in lay.get('decals', []):
        img = SM.MATERIALS.get(dc.get('mat'), {}).get('img')
        if img and not SM.MATERIALS[dc['mat']].get('custom') and dc.get('w') and dc.get('h'):
            if abs((dc['w'] / dc['h']) / (img[0] / img[1]) - 1) > 0.15:
                fails.append('decal-aspect %s %gx%g vs image %dx%d in %s' % (dc['mat'], dc['w'], dc['h'], img[0], img[1], dc['zone']))
    for k, m in SM.MATERIALS.items():
        if m.get('custom') or not m.get('img'):
            continue
        w, h = m['img']
        if abs((m['su'] / m['sv']) / (w / h) - 1) > 0.1:
            fails.append('uv-aspect %s su/sv %g/%g vs image %dx%d' % (k, m['su'], m['sv'], w, h))
    boxes = []
    notes = []
    for zone, mat, pts, n in quads:
        m = SM.MATERIALS.get(mat, {})
        if zone != 'gallery':
            boxes.append(([min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]))
        if mat == 'black' and zone != 'gallery':
            fails.append('void-black in %s at %s' % (zone, [round(c) for c in pts[0]]))
        if mat in GRIP and n[2] < 0.9:
            fails.append('material-role %s on a non-floor face in %s at %s' % (mat, zone, [round(c) for c in pts[0]]))
        if not m.get('trim') and not m.get('custom') and m.get('collide', True) and zone != 'gallery':
            e = [sum((pts[1][i] - pts[0][i]) ** 2 for i in range(3)) ** 0.5, sum((pts[3][i] - pts[0][i]) ** 2 for i in range(3)) ** 0.5]
            if 0 < min(e) < min(m.get('su', 64), m.get('sv', 64)) / 16 and max(e) > max(m.get('su', 64), m.get('sv', 64)):
                notes.append('uv-sliver %s %gx%g in %s at %s' % (mat, round(min(e), 1), round(max(e)), zone, [round(c) for c in pts[0]]))
        if str(m.get('verified', '')).startswith('FAILED'):
            fails.append('failed-material %s in %s at %s' % (mat, zone, pts[0]))
        if mat in VEHICLE_MATS:
            fails.append('fake-vehicle material %s in %s at %s' % (mat, zone, pts[0]))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        for ch in env_channels:
            if max(xs) > ch['x0'] + EDGE and min(xs) < ch['x1'] - EDGE and max(ys) > ch['y0'] + EDGE and min(ys) < ch['y1'] - EDGE \
                    and max(zs) > ch['z'] + 0.5 and min(zs) < ch['z'] + ENVELOPE and not (n[2] > 0.9 and max(zs) <= ch['z'] + 1):
                fails.append('trackbed %s (%s) inside the %s channel at %s' % (mat, zone, ch['zone'], [round(c) for c in pts[0]]))
        if n[2] > 0.9 and any(abs(zs[0] - f) < 3 for f in (0, -320, -384)):      # walkable floor planes only
            w = max(xs) - min(xs); h = max(ys) - min(ys)
            if 6 <= min(w, h) < 16 and max(w, h) > 256 and m.get('su', 0) >= 64 and not m.get('trim') and mat not in ('stair_tread', 'yellow_grip', 'steel_trim', 'rubber_trim', 'wood_trim', 'beam_yellow', 'ibeam') \
                    and not (mat == 'conc_painted' and min(ys) >= 1588 and max(ys) <= 1600):   # strip textures; beam tops at the ceiling; the platform coping
                fails.append('floor-streak %s %gx%g in %s at %s' % (mat, round(w), round(h), zone, [round(c) for c in pts[0]]))
    for d in lay.get('decor', []):
        x, y, z = d['origin']
        for ch in (env_channels if not (tspec and d['model'].startswith('iwz_')) else []):
            hx, hy = (d.get('clip') or (0, 0, 0))[:2]
            if x + hx > ch['x0'] + EDGE and x - hx < ch['x1'] - EDGE and y + hy > ch['y0'] + EDGE and y - hy < ch['y1'] - EDGE and ch['z'] - 1 <= z <= ch['z'] + ENVELOPE:
                fails.append('trackbed decor %s at (%g %g %g) inside the %s channel' % (d['model'], x, y, z, ch['zone']))
        if d['model'] in ('fake_train', 'box_train', 'box_carriage'):
            fails.append('fake-vehicle decor %s' % d['model'])
        if d['model'] not in TONE_OK and any(t in d['model'] for t in TONE_BANNED):
            fails.append('tone decor %s in %s' % (d['model'], d['zone']))
        mname = d['model']
        dboxes = [decor_box(e) for e in lay.get('decor', []) if e.get('clip') and e is not d]
        if any(t in mname for t in MOUNTED) and not any(t in mname for t in MOUNTED_FREE) and d['zone'] != 'gallery':
            dist = min((pt_box_dist(d['origin'], mn, mx) for mn, mx in boxes + dboxes), default=1e9)
            if dist > 28:
                fails.append('anchor %s in %s at %s is %d from any surface' % (mname, d['zone'], d['origin'], dist))
    for g in lay.get('geo_props', []):
        if any(t in g['name'] for t in FAKE_OBJECTS):
            fails.append('fake-object geo_prop %s in %s' % (g['name'], g['zone']))
    dec = [d for d in lay.get('decor', []) if d.get('clip')]
    for i, da in enumerate(dec):
        a0, a1 = decor_box(da)
        va = max(1e-6, (a1[0] - a0[0]) * (a1[1] - a0[1]) * (a1[2] - a0[2]))
        for db in dec[i + 1:]:
            b0, b1 = decor_box(db)
            vb = max(1e-6, (b1[0] - b0[0]) * (b1[1] - b0[1]) * (b1[2] - b0[2]))
            ov = box_overlap(a0, a1, b0, b1)
            if ov > 0.3 * min(va, vb) and 'train' not in da['model'] + db['model']:
                fails.append('intersect %s %s and %s %s' % (da['model'], da['origin'], db['model'], db['origin']))
    signs = lay.get('signs', [])
    for i, da in enumerate(signs):
        for db in signs[i + 1:]:
            if da['image'] == db['image'] and da['zone'] == db['zone'] and not (da.get('hanging') and db.get('hanging') and
                    sum((da['center'][k] - db['center'][k]) ** 2 for k in range(3)) ** 0.5 < 16) and \
                    sum((da['center'][k] - db['center'][k]) ** 2 for k in range(3)) ** 0.5 < 600:
                fails.append('sign-dupe %s in %s at %s and %s' % (da['image'], da['zone'], da['center'], db['center']))
        c = da['center']; hw = da['size'][0] / 2; hh = da['size'][1] / 2
        s0 = [c[0] - (hw if da['axis'] == 'x' else 2), c[1] - (hw if da['axis'] == 'y' else 2), c[2] - hh]
        s1 = [c[0] + (hw if da['axis'] == 'x' else 2), c[1] + (hw if da['axis'] == 'y' else 2), c[2] + hh]
        for d in dec:
            d0, d1 = decor_box(d)
            if box_overlap(s0, s1, d0, d1) > 0:
                fails.append('intersect sign %s at %s with %s %s' % (da['image'], c, d['model'], d['origin']))
    import collections
    for r, c in collections.Counter(f.split()[0] for f in fails).most_common():
        print('ARTLINT rule %-14s %d' % (r, c))
    for f in fails[:80]:
        print('ARTLINT', f)
    print('artlint notes (not failing): %d uv-sliver faces (world-projected at true density: a thin band, not a stretch)' % len(notes))
    print('artlint fails: %d' % len(fails))
    if a.json:
        json.dump({'fails': fails}, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
