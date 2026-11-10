"""Kinematic-envelope check of a generated Station Zero source: which level surfaces, collision blockers or decor stand
where a subway car runs.

usage: track_clearance.py <generated source dir> [--centre-y 1488] [--half-width 68] [--bed -384] [--height 186]
                          [--x0 -3600 --x1 2600] [--json out.json]

Envelope: x0..x1 along the track, centre-y +- half-width (car half width 64 + 4 clearance), from 1 unit above the bed to
bed + height (car roof above its rail top + rail stack). Defaults come from layout.json train_spec / track_spec when
present. Surfaces (surfaces.json quads), nav blockers (plan.json) and decor origins/clips (layout.json) intersecting it
are listed with zone, material / model and position; the train kit's own models (iwz_*) are reported apart.
Exit 1 when anything that is not the kit intersects.
"""
import argparse, json, os, sys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--centre-y', type=float)
    ap.add_argument('--half-width', type=float, default=68.0)
    ap.add_argument('--bed', type=float, default=-384.0)
    ap.add_argument('--height', type=float, default=186.0)
    ap.add_argument('--x0', type=float, default=-3600.0)
    ap.add_argument('--x1', type=float, default=2600.0)
    ap.add_argument('--json')
    ap.add_argument('--min-top', type=float, default=0.0, help='ignore surfaces whose top is below bed + this (old low track parts)')
    a = ap.parse_args(argv)
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    spec = lay.get('train_spec') or lay.get('track_spec') or {}
    cy = a.centre_y if a.centre_y is not None else (lay.get('track_spec') or {}).get('centre_y', 1512.0)
    y0, y1 = cy - a.half_width, cy + a.half_width
    z0, z1 = a.bed + 1, a.bed + a.height
    hits = []

    def inside(mn, mx):
        return mx[0] > a.x0 and mn[0] < a.x1 and mx[1] > y0 and mn[1] < y1 and mx[2] > z0 and mn[2] < z1

    for zone, mat, pts, n in json.load(open(os.path.join(a.src, 'surfaces.json')))['quads']:
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        if (n[2] > 0.9 and mx[2] <= a.bed + 1) or mx[2] < a.bed + a.min_top:        # the bed itself / low track parts
            continue
        if inside(mn, mx):
            hits.append({'kind': 'surface', 'zone': zone, 'what': mat, 'min': [round(v) for v in mn], 'max': [round(v) for v in mx]})
    plan = json.load(open(os.path.join(a.src, 'plan.json')))
    for b in plan.get('blockers', []):
        mn, mx = (b[0], b[1], b[4]), (b[2], b[3], b[5])
        if inside(mn, mx):
            hits.append({'kind': 'blocker', 'zone': '', 'what': 'nav/clip box', 'min': [round(v) for v in mn], 'max': [round(v) for v in mx]})
    for d in lay.get('decor', []):
        x, y, z = d['origin']
        hx, hy, hz = d.get('clip') or (8, 8, 8)
        mn, mx = (x - hx, y - hy, z), (x + hx, y + hy, z + 2 * hz)
        if inside(mn, mx):
            hits.append({'kind': 'decor-kit' if d['model'].startswith('iwz_') else 'decor', 'zone': d['zone'], 'what': d['model'],
                         'min': [round(v) for v in mn], 'max': [round(v) for v in mx]})
    bad = [h for h in hits if h['kind'] not in ('decor-kit',) and not (h['kind'] == 'blocker' and spec.get('cars'))]
    for h in hits:
        print('CLEARANCE %-9s %-15s %-40s %s .. %s' % (h['kind'], h['zone'], h['what'][:40], h['min'], h['max']))
    print('clearance: envelope x %g..%g y %g..%g z %g..%g; %d intersecting (%d not the train kit)'
          % (a.x0, a.x1, y0, y1, z0, z1, len(hits), len(bad)))
    if a.json:
        json.dump({'envelope': [a.x0, y0, z0, a.x1, y1, z1], 'hits': hits}, open(a.json, 'w'), indent=1)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
