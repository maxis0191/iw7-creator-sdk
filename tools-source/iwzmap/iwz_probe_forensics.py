#!/usr/bin/env python3
"""Probe forensics for recorded in-game zombie route probes.

A route probe spawns zombies, lets them walk toward the player and logs
their trail (`SP_T`), the outcome (`SP_END`, `SP_REACH`, `SP_GONE`) and
the navmesh samples (`SP_NAV`, `SP_AI`).  The probes themselves only
report "n of m reached".  This tool reads the trail and says *why*:
which zombies sank into the floor, fell out of the world, never moved,
were still walking when the case ended, or climbed out without being
counted.  With `--emit` every abnormal position is looked up in the
emitted collision and navmesh (iwz_emitcheck.explain), so one recorded
run answers the questions that used to need another build and launch.

Usage:
  iwz_probe_forensics.py <run dir | stairprobe.txt> [...] [--emit SRC]
                         [--json OUT] [--trails]
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCHEMA = 'iw7.iwz-probe-forensics/1'
SUNK = -12.0          # nav_off below this = body under the nav surface
SUNK_RUN = 4          # consecutive samples (1 s at 250 ms)
STILL_RUN = 8         # trailing samples without movement = stuck
VOID_Z = -2000.0      # below every authored floor
FALLING = -100.0      # this far under the nav = falling, not sunk
LEVEL = 48.0          # z change that means "changed floor"
EARLY_MS = 8000       # a case that ends sooner proved nothing

LINE = re.compile(r'SP_([A-Z_]+)\s+(.*)')
PAIR = re.compile(r'(\w+)=(\([^)]*\)(?:\|\S+)?|\S+)')
BAD = ('fell_out_of_world', 'sub_surface', 'stuck')
ARTIFACT = ('never_moved', 'still_closing', 'went_away', 'crossed_level',
            'no_trail', 'wandering')


def parse_value(text):
    """'(1, 2, -3)|tok' -> (1.0, 2.0, -3.0); '12.5' -> 12.5; else str."""
    if text.startswith('('):
        body = text[1:text.index(')')]
        try:
            return tuple(float(v) for v in body.split(','))
        except ValueError:
            return text
    try:
        return float(text)
    except ValueError:
        return text


def parse_line(line):
    """Return (kind, fields) for a probe line, or None."""
    m = LINE.search(line)
    if not m:
        return None
    return m.group(1), {k: parse_value(v) for k, v in PAIR.findall(m.group(2))}


def parse_log(lines):
    """Group probe lines by case.  Tolerates every recorded format."""
    cases = {}
    order = []
    for line in lines:
        rec = parse_line(line)
        if not rec:
            continue
        kind, f = rec
        name = f.get('case')
        if not isinstance(name, str):
            continue
        if name not in cases:
            order.append(name)
            cases[name] = {'case': name, 'trails': {}, 'reach': {},
                           'gone': {}, 'end': None, 'nav_samples': 0,
                           'ai_samples': 0}
        c = cases[name]
        n = int(f['n']) if isinstance(f.get('n'), float) else 0
        if kind == 'T' and isinstance(f.get('pos'), tuple):
            c['trails'].setdefault(n, []).append(f)
        elif kind == 'REACH':
            c['reach'][n] = f.get('t')
        elif kind == 'GONE':
            c['gone'][n] = f
        elif kind == 'END':
            c['end'] = f
        elif kind == 'NAV':
            c['nav_samples'] += 1
        elif kind == 'AI':
            c['ai_samples'] += 1
    return [cases[n] for n in order]


def dist2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def trail_metrics(trail):
    pts = [s['pos'] for s in trail]
    sane = [s['pos'] for s in trail if s['pos'][2] > VOID_Z and not (
        isinstance(s.get('nav_off'), float) and s['nav_off'] < FALLING)]
    sane = sane or [p for p in pts if p[2] > VOID_Z]
    moved = sum(dist2(a, b) for a, b in zip(sane, sane[1:]))
    offs = [s.get('nav_off') for s in trail]
    run = best = 0
    for s, off in zip(trail, offs):
        if isinstance(off, float) and FALLING <= off < SUNK and s['pos'][2] > VOID_Z:
            run += 1
            best = max(best, run)
        else:
            run = 0
    still = 0
    for p in reversed(sane[:-1]):
        if dist2(p, sane[-1]) < 2.0 and abs(p[2] - sane[-1][2]) < 2.0:
            still += 1
        else:
            break
    ds = [s['dist'] for s in trail if isinstance(s.get('dist'), float)]
    low = [off for s, off in zip(trail, offs)
           if isinstance(off, float) and off >= FALLING and s['pos'][2] > VOID_Z]
    fell = any(p[2] <= VOID_Z for p in pts) or any(
        isinstance(s.get('nav_off'), float) and s['nav_off'] < FALLING for s in trail)
    return {
        'samples': len(trail),
        'first': pts[0], 'last': pts[-1],
        'last_sane': sane[-1] if sane else None,
        'moved': round(moved, 1),
        'dz': round(sane[-1][2] - sane[0][2], 1) if sane else 0.0,
        'fell': fell,
        'sunk_run': best,
        'min_nav_off': round(min(low), 1) if low else None,
        'tail_still': still,
        'd0': ds[0] if ds else None, 'd1': ds[-1] if ds else None,
        'dmin': min(ds) if ds else None,
        't_last': trail[-1].get('t'),
    }


def classify(m, reached, gone):
    """One word for what a zombie did.  Order matters: worst first."""
    if reached:
        return 'reached'
    if m is None:
        return 'no_trail'
    last = gone.get('last') if gone else None
    if m['fell'] or (isinstance(last, tuple) and last[2] <= VOID_Z):
        return 'fell_out_of_world'
    if m['sunk_run'] >= SUNK_RUN:
        return 'sub_surface'
    if m['moved'] < 16.0:
        return 'never_moved'
    if abs(m['dz']) >= LEVEL:
        return 'crossed_level'
    d0, d1, dmin = m['d0'], m['d1'], m['dmin']
    if m['tail_still'] >= STILL_RUN and (d1 is None or d1 > 64.0):
        return 'stuck'
    if d0 is not None and d1 is not None:
        if d1 <= dmin + 16.0 and d1 < d0 - 32.0:
            return 'still_closing'
        if d1 > d0 + 64.0:
            return 'went_away'
    return 'wandering'


def departure(emit, trail):
    """First place where the body leaves the emitted walkable surface.

    Returns {'pos', 'where', 'error', 'travel', 'rise', 'emit_rise'} or None.
    'rise' is how much the body climbed over the trail, 'emit_rise' how
    much the emitted surface climbs over the same ground: when they
    differ the game is not standing the agent on the built surface.
    """
    def surface(p):
        fl = emit.col.floors(p[0], p[1])
        return min((z for z, _ in fl), key=lambda z: abs(z - p[2])) if fl else None
    pts = [s['pos'] for s in trail if s['pos'][2] > VOID_Z]
    errs = []
    for p in pts:
        z = surface(p)
        errs.append(None if z is None else p[2] - z)
    run = 0
    for i, e in enumerate(errs):
        run = run + 1 if (e is not None and FALLING <= e < SUNK) else 0
        if run >= SUNK_RUN:
            j = i - run + 1
            a, b = pts[0], pts[i]
            za, zb = surface(a), surface(b)
            return {'pos': [round(v, 1) for v in pts[j]],
                    'where': emit.where(*pts[j]),
                    'error': round(min(x for x in errs[j:] if x is not None and x >= FALLING), 1),
                    'travel': round(dist2(a, b), 1),
                    'rise': round(b[2] - a[2], 1),
                    'emit_rise': None if za is None or zb is None else round(zb - za, 1)}
    return None


def end_counts(end, zombies):
    """(reached, total) from SP_END in either recorded format."""
    if not end:
        return None, None
    r = end.get('result')
    if isinstance(r, str) and '/' in r:
        a, b = r.split('/', 1)
        try:
            return int(a), int(b)
        except ValueError:
            return None, None
    if r == 'reached':
        return 1, max(1, zombies)
    if isinstance(r, str):
        return 0, max(1, zombies)
    return None, None


def analyse_case(c, emit=None):
    import_explain = None
    if emit is not None:
        from iwz_emitcheck import explain as import_explain
    ids = sorted(set(c['trails']) | set(c['reach']) | set(c['gone']))
    end = c['end'] or {}
    old_reached = end.get('result') == 'reached'
    zombies = []
    for n in ids:
        trail = c['trails'].get(n)
        m = trail_metrics(trail) if trail else None
        reached = n in c['reach'] or (old_reached and len(ids) <= 1)
        cls = classify(m, reached, c['gone'].get(n))
        z = {'n': n, 'class': cls, 'gone': n in c['gone']}
        if m:
            z.update({k: m[k] for k in ('samples', 'first', 'last_sane', 'moved',
                                         'dz', 'sunk_run', 'min_nav_off',
                                         'tail_still', 'd0', 'd1', 't_last')})
        if import_explain and m and m['last_sane'] and cls in BAD + ('never_moved',):
            e = import_explain(emit, *m['last_sane'])
            z['emit'] = {'where': e['where'], 'verdict': e['verdict'],
                         'nav_offset': e.get('nav_offset'), 'note': e.get('note')}
            if cls == 'sub_surface':
                z['departure'] = departure(emit, trail)
        zombies.append(z)
    reached_n, total = end_counts(c['end'], len(ids))
    classes = [z['class'] for z in zombies]
    got = classes.count('reached')
    if reached_n is None:
        reached_n, total = got, len(ids)
    ms = end.get('ms') if isinstance(end.get('ms'), float) else None
    flags = []
    if c['end'] is None:
        flags.append('no_end_line')
    if ms is not None and ms < EARLY_MS and reached_n == 0:
        flags.append('ended_early')
    if 'still_closing' in classes:
        flags.append('ended_while_walking')
    if 'crossed_level' in classes:
        flags.append('changed_floor_not_counted')
    if end.get('placed') == 0.0 and total and not c['trails']:
        flags.append('no_zombie_tracked')
    if total and reached_n == total:
        verdict = 'pass'
    elif any(k in BAD for k in classes):
        verdict = 'geometry_suspect'
    elif reached_n:
        verdict = 'partial'
    elif flags or any(k in ARTIFACT for k in classes) or not classes:
        verdict = 'probe_artifact'
    else:
        verdict = 'inconclusive'
    return {'case': c['case'], 'verdict': verdict, 'reached': reached_n,
            'total': total, 'ms': ms, 'flags': flags, 'classes': classes,
            'zombies': zombies, 'nav_samples': c['nav_samples']}


def read_run(path):
    """Accept a run directory or a probe text file."""
    name = os.path.basename(os.path.normpath(path))
    file = path
    if os.path.isdir(path):
        for cand in ('stairprobe.txt', 'client.stdout.log'):
            if os.path.isfile(os.path.join(path, cand)):
                file = os.path.join(path, cand)
                break
        else:
            raise FileNotFoundError('no probe log in ' + path)
    else:
        name = os.path.basename(os.path.dirname(os.path.abspath(path))) or name
    with open(file, 'r', encoding='utf-8', errors='replace') as fh:
        return name, parse_log(fh)


def analyse(paths, emit=None):
    runs = []
    for p in paths:
        name, cases = read_run(p)
        runs.append({'run': name, 'cases': [analyse_case(c, emit) for c in cases]})
    by_case = {}
    for r in runs:
        for c in r['cases']:
            by_case.setdefault(c['case'], []).append((r['run'], c))
    cohort = []
    for case, rows in by_case.items():
        verdicts = sorted({c['verdict'] for _, c in rows})
        cohort.append({
            'case': case, 'runs': len(rows),
            'reached': sum(c['reached'] or 0 for _, c in rows),
            'total': sum(c['total'] or 0 for _, c in rows),
            'verdicts': verdicts,
            'flaky': len(rows) > 1 and 'pass' in verdicts and len(verdicts) > 1,
        })
    spots = {}
    for r in runs:
        for c in r['cases']:
            for z in c['zombies']:
                if z['class'] in BAD and z.get('last_sane'):
                    p = z['last_sane']
                    key = (round(p[0] / 64.0), round(p[1] / 64.0), round(p[2] / 32.0))
                    s = spots.setdefault(key, {'pos': [round(v) for v in p], 'n': 0,
                                               'classes': {}, 'cases': set(),
                                               'emit': z.get('emit'),
                                               'departure': z.get('departure')})
                    s['n'] += 1
                    s['classes'][z['class']] = s['classes'].get(z['class'], 0) + 1
                    s['cases'].add(c['case'])
    hot = sorted(spots.values(), key=lambda s: -s['n'])
    for s in hot:
        s['cases'] = sorted(s['cases'])
    tally = {}
    for r in runs:
        for c in r['cases']:
            tally[c['verdict']] = tally.get(c['verdict'], 0) + 1
    return {'schema': SCHEMA, 'runs': runs, 'cohort': cohort, 'hotspots': hot,
            'verdicts': tally}


def print_report(rep, trails=False):
    for r in rep['runs']:
        print('== %s' % r['run'])
        for c in r['cases']:
            kinds = {}
            for k in c['classes']:
                kinds[k] = kinds.get(k, 0) + 1
            mix = ', '.join('%s x%d' % kv for kv in sorted(kinds.items())) or 'no zombie tracked'
            print('  %-18s %-17s %s/%s  %6s ms  %s%s' % (
                c['case'], c['verdict'], c['reached'], c['total'],
                '-' if c['ms'] is None else int(c['ms']), mix,
                ('  [' + ', '.join(c['flags']) + ']') if c['flags'] else ''))
            if trails:
                for z in c['zombies']:
                    e = z.get('emit')
                    print('      n=%s %-18s moved=%s dz=%s min_nav_off=%s last=%s%s' % (
                        z['n'], z['class'], z.get('moved'), z.get('dz'),
                        z.get('min_nav_off'), z.get('last_sane'),
                        ('  emit: %s %s' % (e['where'], e['verdict'])) if e else ''))
    print('== verdicts: ' + ', '.join('%s=%d' % kv for kv in sorted(rep['verdicts'].items())))
    flaky = [c['case'] for c in rep['cohort'] if c['flaky']]
    if flaky:
        print('== same case, different outcome across runs: ' + ', '.join(sorted(flaky)))
    if rep['hotspots']:
        print('== where zombies got into trouble (64-unit cells)')
        for s in rep['hotspots'][:12]:
            e = s.get('emit')
            print('  %-22s n=%-3d %s  cases=%s%s' % (
                tuple(s['pos']), s['n'],
                ','.join('%s:%d' % kv for kv in sorted(s['classes'].items())),
                ','.join(s['cases'][:4]),
                ('\n      emit: %s, %s%s' % (
                    e['where'], e['verdict'],
                    '' if e.get('nav_offset') is None else ', body %.0f from nav' % e['nav_offset']))
                if e else ''))
            d = s.get('departure')
            if d:
                print('      leaves the built surface at %s (%s): body climbed %s over %s of travel, '
                      'built surface climbs %s' % (tuple(d['pos']), d['where'], d['rise'],
                                                   d['travel'], d['emit_rise']))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--emit', help='emit directory to explain positions against')
    ap.add_argument('--json')
    ap.add_argument('--trails', action='store_true', help='print every zombie')
    a = ap.parse_args(argv)
    emit = None
    if a.emit:
        from iwz_emitcheck import Emit
        emit = Emit.load(a.emit)
    rep = analyse(a.runs, emit)
    print_report(rep, a.trails)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(rep, fh, indent=1, default=list)
    return 0


if __name__ == '__main__':
    sys.exit(main())
