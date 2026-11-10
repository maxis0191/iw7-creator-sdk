"""Static seam check of a generated Station Zero v2 source: gaps at ceiling edges that show the void (review C:
ceiling-to-wall slots in the service tunnel, a wall short of the ceiling at flk_1, a seam slit in the maint corridor,
blue lines at the platform B wall/ceiling join).

usage: sz2_seams.py <src dir> [--json out.json] [--step 32] [--tol 1.0]

For every render ceiling quad (normal z < -0.9) each edge is sampled every --step units. A sample is closed when,
just below the edge (1 unit), a vertical render quad passes through it (within --tol of its plane and inside its
extent), or when the surface continues past the edge: a ceiling quad 2 units further out at a height within 2 units,
or a sloped quad (stair ceilings). Anything else is an open seam: the void shows between the ceiling and the wall.
Exit status 1 when any seam is open.
"""
import argparse, json, math, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--json'); ap.add_argument('--step', type=float, default=32); ap.add_argument('--tol', type=float, default=1.0)
    a = ap.parse_args()
    quads = json.load(open(os.path.join(a.src, 'surfaces.json')))['quads']
    walls, ceils, slopes = [], [], []
    for zone, mat, pts, n in quads:
        if zone == 'gallery':
            continue
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        if abs(n[2]) < 0.1:
            walls.append((mn, mx, n, pts))
        elif n[2] < -0.9:
            ceils.append((zone, mat, mn, mx))
        elif n[2] < -0.1:
            slopes.append((mn, mx))

    # bucket walls by coarse xy cell for speed
    G = 256
    grid = {}
    for k, (mn, mx, n, pts) in enumerate(walls):
        for gx in range(int(math.floor(mn[0] / G)), int(math.floor(mx[0] / G)) + 1):
            for gy in range(int(math.floor(mn[1] / G)), int(math.floor(mx[1] / G)) + 1):
                grid.setdefault((gx, gy), []).append(k)

    def wall_at(x, y, z):
        for k in grid.get((int(math.floor(x / G)), int(math.floor(y / G))), []):
            mn, mx, n, pts = walls[k]
            if mn[2] - a.tol <= z <= mx[2] + a.tol and mn[0] - a.tol <= x <= mx[0] + a.tol and mn[1] - a.tol <= y <= mx[1] + a.tol:
                d = abs((x - pts[0][0]) * n[0] + (y - pts[0][1]) * n[1] + (z - pts[0][2]) * n[2])
                if d <= a.tol:
                    return True
        return False

    def ceil_at(x, y, z):
        for zone, mat, mn, mx in ceils:
            if mn[0] <= x <= mx[0] and mn[1] <= y <= mx[1] and abs(mn[2] - z) <= 2:
                return True
        for mn, mx in slopes:
            if mn[0] - 2 <= x <= mx[0] + 2 and mn[1] - 2 <= y <= mx[1] + 2 and mn[2] - 4 <= z <= mx[2] + 4:
                return True
        return False

    gaps = []
    for zone, mat, mn, mx in ceils:
        if mx[0] - mn[0] < 24 or mx[1] - mn[1] < 24:      # fixtures, trims and lamp housings are not room ceilings
            continue
        z = mn[2]
        edges = [((mn[0], mn[1]), (mx[0], mn[1]), (0, -1)), ((mn[0], mx[1]), (mx[0], mx[1]), (0, 1)),
                 ((mn[0], mn[1]), (mn[0], mx[1]), (-1, 0)), ((mx[0], mn[1]), (mx[0], mx[1]), (1, 0))]
        for (x0, y0), (x1, y1), (ox, oy) in edges:
            L = math.hypot(x1 - x0, y1 - y0)
            ns = max(1, int(L // a.step))
            for s in range(ns):
                t = (s + 0.5) / ns
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if wall_at(x, y, z - 0.25) or ceil_at(x + 2 * ox, y + 2 * oy, z):
                    continue
                gaps.append({'zone': zone, 'ceiling': mat, 'at': [round(x), round(y), round(z)], 'side': [ox, oy]})
    by_zone = {}
    for g in gaps:
        by_zone[g['zone']] = by_zone.get(g['zone'], 0) + 1
    for zn, c in sorted(by_zone.items()):
        print('SEAMS %-16s %d open samples' % (zn, c))
    for g in gaps[:40]:
        print('SEAM', g)
    print('seams open: %d (ceilings %d, walls %d)' % (len(gaps), len(ceils), len(walls)))
    if a.json:
        json.dump({'gaps': gaps, 'by_zone': by_zone}, open(a.json, 'w'), indent=1)
    sys.exit(1 if gaps else 0)


if __name__ == '__main__':
    main()
