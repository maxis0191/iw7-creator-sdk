"""Which enemies a captured frame really shows, as data (counts engine agents drawn on the client).

The game prints where every living enemy stands at the moment of a capture (server repository gamelab library
crowd78.gsc, `cr_positions`: lines `GL CRPOS name=<set> kind=<agent|crowd> id=<n> x= y= z= yaw=`). For each enemy this
tool projects points of its upright axis (the feet origin + 20, 36, 50 and 62 units) into the frame, with the frame's
own camera, and reads the engine's depth buffer around each point (3 x 3 depth pixels):

    drawn      the depth there is the body: at most 22 units nearer than its axis (its surface toward the camera) and
               not farther than the axis plus the depth tolerance (iw7_see.tolerance)
    occluded   something nearer was drawn there (another body, a wall)
    absent     the depth is farther than the axis: nothing was drawn where the body stands

An enemy is DRAWN when one of its points is drawn in any of the frames; ABSENT when, in a frame where it stands in view,
at least three of its points are in the frame, none is drawn and none is occluded (the failure this tool exists to
find: a body the server has and the client does not draw); otherwise OCCLUDED or OUTSIDE (never in view). Positions of a
moving enemy are taken from two sets, before and after the capture: a point counts at either position.

usage:
  crowd_seen.py --log <client.stdout.log> --view <frame.bmp>:<set before>[:<set after>] [--view ...] [--json]
Exit 0; 2 with one sentence when a frame has no camera or no depth, or a set is not in the log.
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iw7_see as S  # noqa: E402
from iw7_dump import WorldError  # noqa: E402

HEIGHTS = (20.0, 36.0, 50.0, 62.0)
SURFACE = 22.0          # a body's surface toward the camera is at most this much nearer than its axis
POS = re.compile(r'GL CRPOS name=(\S+) kind=(\S+) id=(\d+) x=(\S+) y=(\S+) z=(\S+)(?: yaw=(\S+))?')


def read_positions(text):
    """{set: {(kind, id): (x, y, z)}} from the game's log text."""
    out = {}
    for m in POS.finditer(text):
        out.setdefault(m.group(1), {})[(m.group(2), int(m.group(3)))] = (float(m.group(4)), float(m.group(5)), float(m.group(6)))
    return out


def sample_state(frame, point):
    """'outside', 'behind', 'drawn', 'occluded' or 'absent' for one world point of a body's axis."""
    np = S.np
    px, py, z = frame.project(np.array(point, dtype=np.float64))
    px, py, z = float(px), float(py), float(z)
    if z <= frame.near_clip:
        return 'behind'
    if not (0 <= px < frame.w and 0 <= py < frame.h):
        return 'outside'
    zb = frame.z_buffer()
    tol = float(S.tolerance(np.array(z)))
    best = None
    xi, yi = int(math.floor(px)), int(math.floor(py))
    nearer = False
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x, y = xi + dx, yi + dy
            if not (0 <= x < frame.w and 0 <= y < frame.h):
                continue
            ze = float(zb[y, x])
            if z - SURFACE - tol <= ze <= z + tol:
                return 'drawn'
            if ze < z - SURFACE - tol:
                nearer = True
            best = ze if best is None else min(best, ze)
    return 'occluded' if nearer else 'absent'


def body_state(frame, origins):
    """One body in one frame, from one or two positions: (state, samples drawn, samples in frame)."""
    states = []
    for o in origins:
        for h in HEIGHTS:
            states.append(sample_state(frame, (o[0], o[1], o[2] + h)))
    drawn = states.count('drawn')
    inframe = sum(1 for s in states if s in ('drawn', 'occluded', 'absent'))
    if drawn:
        return 'drawn', drawn, inframe
    if inframe == 0:
        return 'outside', 0, 0
    if states.count('occluded') == 0 and inframe >= 3:
        return 'absent', 0, inframe
    return 'occluded', 0, inframe


def judge(views, positions):
    """views: [(frame, before set, after set or None)]. -> result document."""
    bodies = {}
    for frame, before, after in views:
        sets = [positions[before]] + ([positions[after]] if after else [])
        keys = set(sets[0])
        for s in sets[1:]:
            keys |= set(s)
        for k in keys:
            origins = [s[k] for s in sets if k in s]
            st, nd, nf = body_state(frame, origins)
            row = bodies.setdefault(k, {'kind': k[0], 'id': k[1], 'views': {}})
            row['views'][frame.name] = {'state': st, 'samples_drawn': nd, 'samples_in_frame': nf}
    for row in bodies.values():
        sts = [v['state'] for v in row['views'].values()]
        if 'drawn' in sts:
            row['state'] = 'drawn'
        elif 'absent' in sts:
            row['state'] = 'absent'
        elif 'occluded' in sts:
            row['state'] = 'occluded'
        else:
            row['state'] = 'outside'
    totals = {}
    for row in bodies.values():
        t = totals.setdefault(row['kind'], {'listed': 0, 'drawn': 0, 'occluded': 0, 'absent': 0, 'outside': 0})
        t['listed'] += 1
        t[row['state']] += 1
    allt = {'listed': 0, 'drawn': 0, 'occluded': 0, 'absent': 0, 'outside': 0}
    for t in totals.values():
        for k in allt:
            allt[k] += t[k]
    return {'schema': 'iw7.crowd-seen/1', 'views': [f.name for f, _, _ in views], 'total': allt, 'by_kind': totals,
            'bodies': sorted(bodies.values(), key=lambda r: (r['kind'], r['id']))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--log', required=True, help="the game's log with the GL CRPOS lines (run/client.stdout.log)")
    ap.add_argument('--view', action='append', required=True, help='<frame.bmp>:<set before>[:<set after>]')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    try:
        with open(a.log, 'r', encoding='utf-8', errors='replace') as f:
            positions = read_positions(f.read())
        views = []
        for v in a.view:
            # a Windows path has its own colon: the sets are read from the right
            m = re.match(r'^(.*\.(?:bmp|json)):([a-z0-9_]+)(?::([a-z0-9_]+))?$', v, re.I)
            if not m:
                raise S.SeeError('a view is <frame.bmp>:<set before>[:<set after>], not %s' % v)
            frame_path, before, after = m.group(1), m.group(2), m.group(3)
            for s in (before, after):
                if s and s not in positions:
                    raise S.SeeError('no GL CRPOS lines of set %s in %s' % (s, a.log))
            fr = S.Frame(frame_path)
            S.need_depth(fr)
            views.append((fr, before, after))
        r = judge(views, positions)
    except WorldError as e:
        print('crowd_seen: %s' % e, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        t = r['total']
        print('%d enemies listed: drawn %d, occluded %d, absent %d, never in view %d (views: %s)' % (
            t['listed'], t['drawn'], t['occluded'], t['absent'], t['outside'], ', '.join(r['views'])))
        for kind, k in sorted(r['by_kind'].items()):
            print('  %-6s listed %3d  drawn %3d  occluded %3d  absent %3d  never in view %3d' % (kind, k['listed'], k['drawn'], k['occluded'], k['absent'], k['outside']))
        for row in r['bodies']:
            if row['state'] in ('absent', 'occluded'):
                print('  %s %d: %s' % (row['kind'], row['id'], ', '.join('%s %s' % (n, v['state']) for n, v in row['views'].items())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
