"""ST1 (Station Zero stress number): frame times per spawn zone from gamelab runs with the perfzones step, read with the
components' client recorder reader (ops/engine-map/iw7_perf.py), and the parity of a custom map against a shipped map.

    python st1_report.py --perf <components>/ops/engine-map/iw7_perf.py LABEL=<run folder> [LABEL=<run folder> ...]
        [--base LABEL] [--json out.json] [--md out.md]

A run folder holds perf/z_<volume>_a.json and _b.json (two views a zone). Per zone the worse of the two views is kept.
Per run: the median over zones of the zone fps, the worst zone, and the worst p99 frame time. With --base, every run is
also given as a share of the base run's median zone fps (the bible's parity rule: at least 85 %).
"""
import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys


def read_run(perf_tool, folder):
    zones = {}
    for w in sorted(glob.glob(os.path.join(folder, '**', 'perf', 'z_*.json'), recursive=True)):
        m = re.match(r'^z_(.+)_([ab])\.json$', os.path.basename(w))
        if not m:
            continue
        out = subprocess.run([sys.executable, '-I', '-B', perf_tool, 'report', w, '--json'], capture_output=True, text=True)
        if out.returncode:
            continue
        f = json.loads(out.stdout)['frames']
        z = zones.setdefault(m.group(1), {'fps': None, 'median_ms': 0, 'p95_ms': 0, 'p99_ms': 0, 'low_1pct_fps': None, 'views': 0})
        z['views'] += 1
        z['fps'] = f['fps'] if z['fps'] is None else min(z['fps'], f['fps'])
        z['low_1pct_fps'] = f['low_1pct_fps'] if z['low_1pct_fps'] is None else min(z['low_1pct_fps'], f['low_1pct_fps'])
        for k in ('median_ms', 'p95_ms', 'p99_ms'):
            z[k] = max(z[k], f[k])
    fps = [z['fps'] for z in zones.values() if z['fps']]
    summary = {'zones': len(zones), 'median_zone_fps': round(statistics.median(fps), 1) if fps else None,
               'worst_zone': min(zones, key=lambda k: zones[k]['fps']) if zones else None,
               'worst_zone_fps': round(min(fps), 1) if fps else None,
               'worst_p99_ms': round(max(z['p99_ms'] for z in zones.values()), 2) if zones else None}
    return {'zones': zones, 'summary': summary}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('runs', nargs='+', help='LABEL=<run folder>')
    ap.add_argument('--perf', required=True, help="the components' ops/engine-map/iw7_perf.py")
    ap.add_argument('--base', help='label of the reference run (the shipped map)')
    ap.add_argument('--json')
    ap.add_argument('--md')
    a = ap.parse_args(argv)
    res = {}
    for r in a.runs:
        label, _, folder = r.partition('=')
        res[label] = read_run(a.perf, folder)
    base = res.get(a.base, {}).get('summary', {}).get('median_zone_fps') if a.base else None
    lines = ['| Run | zones | median zone fps | worst zone (fps) | worst p99 ms | share of %s |' % (a.base or '-'), '|---|---|---|---|---|---|']
    for label, r in res.items():
        s = r['summary']
        share = round(100.0 * s['median_zone_fps'] / base, 1) if base and s['median_zone_fps'] else None
        s['share_of_base_pct'] = share
        lines.append('| %s | %s | %s | %s (%s) | %s | %s |' % (label, s['zones'], s['median_zone_fps'], s['worst_zone'], s['worst_zone_fps'],
                                                            s['worst_p99_ms'], '%s %%' % share if share is not None else '-'))
    print('\n'.join(lines))
    if a.md:
        open(a.md, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
