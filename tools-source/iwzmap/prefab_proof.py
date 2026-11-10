"""Prove a placed prefab against the room it was lifted from: the same test plan for both maps, and the comparison.

  python -I prefab_proof.py plans   <placed prefab> <spec.json> <out dir> [--map cp_pfr] [--usermap <built usermap dir>]
  python -I prefab_proof.py compare <run folder of the generated map> <run folder of the shipped map> <placed prefab>
                                    [--json out.json]
  python -I prefab_proof.py frames  <run folder of the generated map> <run folder of the shipped map>
                                    --frame-tool <iw7_frame_evidence.py of iw7-mod-components> [--json out.json]

`plans` writes two game-test plans (schema iw7.gamelab-plan/1, run by the server repository's ops/gamelab):
<out>/placed.json for the generated map and <out>/source.json for the shipped map. Every point of the spec is given
in the shipped map's coordinates and moved into the generated map for the placed plan, so both sessions stand in
the same spots and look the same way.

spec.json:
  {"poses":  [{"name": "spawn_south", "at": [x, y, z], "yaw": 270, "pitch": 0}, ...],   frames and frame rate
   "stands": [{"name": "spawn", "at": [x, y, z]}, ...],                                 does the floor hold the player
   "walks":  [{"name": "wall_east", "from": [x, y, z], "to": [x, y, z]}, ...],          does something stop the player
   "perf_seconds": 12, "dump_props": true}

`frames` measures every capture both runs hold (same name) with the project's frame tool: brightness of each frame,
how much of the picture differs, and the distance of the two perceptual hashes (0 = same layout, 64 = opposite).
It measures; whether a room looks right is for independent reviewers.

`compare` reads the two session logs: where the player stood after each teleport, how far each walk went, and
prints them side by side in the shipped map's coordinates (the generated map's positions are moved back).
"""
import argparse, json, math, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prefab_place as PP  # noqa: E402


def _plan(name, mapname, usermap, spec, move, yaw_add, tag):
    steps = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'wait', 's': 2},
             {'do': 'cmd', 'text': 'paris_world_stats'}]
    if spec.get('dump_props', True):
        steps += [{'do': 'cmd', 'text': 'paris_world_dump collect %s' % tag}, {'do': 'wait', 's': 2}]
    r = lambda p: [round(c, 2) for c in move(p)]  # noqa: E731
    for v in spec.get('poses', []):
        steps += [{'do': 'tp', 'at': r(v['at']), 'yaw': (v.get('yaw', 0) + yaw_add) % 360, 'pitch': v.get('pitch', 0)},
                  {'do': 'freeze', 'on': True}, {'do': 'wait', 's': 3},
                  {'do': 'mark', 'name': 'pose_' + v['name']},
                  {'do': 'capture', 'name': v['name'], 'pause': 2},
                  {'do': 'perf', 'name': v['name'], 's': spec.get('perf_seconds', 12)}]
    for s in spec.get('stands', []):
        at = r(s['at'])
        steps += [{'do': 'tp', 'at': [at[0], at[1], at[2] + 4], 'yaw': 0}, {'do': 'freeze', 'on': False},
                  {'do': 'mark', 'name': 'stand_%s_a' % s['name']}, {'do': 'wait', 's': 3},
                  {'do': 'mark', 'name': 'stand_%s_b' % s['name']},
                  {'do': 'expect', 'that': 'dist(stand_%s_a,stand_%s_b)' % (s['name'], s['name']), 'lt': 8,
                   'why': 'the floor holds the player'}]
    for w in spec.get('walks', []):
        a, b = r(w['from']), r(w['to'])
        yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360
        steps += [{'do': 'tp', 'at': [a[0], a[1], a[2] + 4], 'yaw': round(yaw, 1)}, {'do': 'wait', 's': 1},
                  {'do': 'mark', 'name': 'walk_%s_a' % w['name']},
                  {'do': 'walk', 'to': b, 's': w.get('s', 6)},
                  {'do': 'wait', 's': 0.5},
                  {'do': 'mark', 'name': 'walk_%s_b' % w['name']}]
    plan = {'schema': 'iw7.gamelab-plan/1', 'name': name, 'map': mapname,
            'about': 'Prefab proof: the same spots, views and walks in the generated map and in the shipped map.',
            'steps': steps}
    if usermap:
        plan['usermap'] = usermap
    return plan


def plans(prefab_dir, spec, out, mapname='cp_pfr', usermap=None):
    pre = PP.load(prefab_dir)
    os.makedirs(out, exist_ok=True)
    src_map = pre['source'].get('map') or 'cp_zmb'
    a = _plan('prefab_placed', mapname, usermap, spec, lambda p: PP.to_placed(pre, p), pre.get('yaw', 0.0), 'placed')
    b = _plan('prefab_source', src_map, None, spec, lambda p: tuple(p), 0.0, 'source')
    for name, plan in (('placed.json', a), ('source.json', b)):
        with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(plan, f, indent=1)
            f.write('\n')
    return a, b


_VEC = r'\(\s*(-?[\d.eE+-]+),\s*(-?[\d.eE+-]+),\s*(-?[\d.eE+-]+)\s*\)'


def read_log(path):
    """GL MARK / GL WALK / GL AT lines of a session log -> {'marks': {name: xyz}, 'walks': [..], 'ats': [..]}."""
    out = {'marks': {}, 'walks': [], 'ats': [], 'stats': None}
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for ln in f:
            ln = re.sub(r'\x1b\[[0-9;]*m|\^\d', '', ln)
            m = re.search(r'GL MARK i=\d+ name=(\S+) .*?origin=' + _VEC + r'.*?ground=(\d)', ln)
            if m:
                out['marks'][m.group(1)] = {'origin': tuple(float(m.group(k)) for k in (2, 3, 4)), 'ground': int(m.group(5))}
                continue
            m = re.search(r'GL WALK i=\d+ .*?from=' + _VEC + r' to=' + _VEC + r' want=' + _VEC + r' moved=(-?\d+) left=(-?\d+)', ln)
            if m:
                g = [float(m.group(k)) for k in range(1, 10)]
                out['walks'].append({'from': tuple(g[0:3]), 'to': tuple(g[3:6]), 'want': tuple(g[6:9]), 'moved': int(m.group(10)),
                                     'left': int(m.group(11))})
                continue
            m = re.search(r'GL AT i=\d+ want=' + _VEC + r' origin=' + _VEC + r' ground=(\d)', ln)
            if m:
                g = [float(m.group(k)) for k in range(1, 7)]
                out['ats'].append({'want': tuple(g[0:3]), 'origin': tuple(g[3:6]), 'ground': int(m.group(7))})
                continue
            m = re.search(r'\[Paris world\] map=(\S+) props=(\d+) surfaces=(\d+) lights=(\d+)', ln)
            if m and out['stats'] is None:
                out['stats'] = {'map': m.group(1), 'props': int(m.group(2)), 'surfaces': int(m.group(3)), 'lights': int(m.group(4))}
    return out


def _find_log(run):
    for name in ('client.stdout.log', 'console.log'):
        p = os.path.join(run, name)
        if os.path.isfile(p):
            return p
    raise PP.PrefabError('no session log in %s' % run)


def compare(run_placed, run_source, prefab_dir):
    pre = PP.load(prefab_dir)
    a, b = read_log(_find_log(run_placed)), read_log(_find_log(run_source))
    back = lambda p: PP.to_source(pre, p)  # noqa: E731
    rows = []
    for name in sorted(set(a['marks']) | set(b['marks'])):
        ma, mb = a['marks'].get(name), b['marks'].get(name)
        row = {'mark': name, 'placed': None, 'source': None, 'difference': None}
        if ma:
            row['placed'] = [round(c, 2) for c in back(ma['origin'])]; row['placed_ground'] = ma['ground']
        if mb:
            row['source'] = [round(c, 2) for c in mb['origin']]; row['source_ground'] = mb['ground']
        if ma and mb:
            row['difference'] = round(math.dist(back(ma['origin']), mb['origin']), 2)
        rows.append(row)
    walks = []
    for k in range(max(len(a['walks']), len(b['walks']))):
        wa = a['walks'][k] if k < len(a['walks']) else None
        wb = b['walks'][k] if k < len(b['walks']) else None
        walks.append({'n': k, 'placed_moved': wa and wa['moved'], 'placed_left': wa and wa['left'],
                      'source_moved': wb and wb['moved'], 'source_left': wb and wb['left'],
                      'placed_end': wa and [round(c, 1) for c in back(wa['to'])], 'source_end': wb and [round(c, 1) for c in wb['to']]})
    return {'schema': 'iw7.prefab-proof/1', 'placed_stats': a['stats'], 'source_stats': b['stats'], 'marks': rows, 'walks': walks}


def _tool(tool, args):
    r = subprocess.run([sys.executable, '-B', tool] + args, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise PP.PrefabError('frame tool failed: %s' % (r.stderr.strip() or r.stdout.strip())[:300])
    return r.stdout


def frames(run_placed, run_source, tool):
    """Per capture present in both runs: frame metrics of each and the difference (shipped = control)."""
    names = sorted(f for f in os.listdir(run_placed) if f.startswith('iwz_') and f.endswith('.bmp') and os.path.isfile(os.path.join(run_source, f)))
    rows = []
    for f in names:
        a, b = os.path.join(run_placed, f), os.path.join(run_source, f)
        with tempfile.TemporaryDirectory() as tmp:
            rep = os.path.join(tmp, 'frames.json')
            m = {}
            for key, path in (('placed', a), ('source', b)):
                _tool(tool, ['frames', path, '--json', rep])
                with open(rep, 'r', encoding='utf-8') as fh:
                    m[key] = json.load(fh)['frames'][0]
        d = json.loads(_tool(tool, ['diff', b, a]))
        ha, hb = int(m['placed']['dhash'], 16), int(m['source']['dhash'], 16)
        row = {'name': f[4:-4], 'hash_distance': bin(ha ^ hb).count('1'), 'mean_difference': d['mean_difference'],
               'changed_fraction': d['changed_fraction'], 'mean_luma_delta': d['mean_luma_delta']}
        for key in ('placed', 'source'):
            for k in ('mean_luma', 'std_luma', 'p01_luma', 'p99_luma', 'black_fraction', 'clipped_fraction', 'mean_saturation'):
                row['%s_%s' % (key, k)] = m[key][k]
        row['luma_ratio'] = round(m['placed']['mean_luma'] / m['source']['mean_luma'], 3) if m['source']['mean_luma'] else None
        rows.append(row)
    return {'schema': 'iw7.prefab-frames/1', 'placed': run_placed, 'source': run_source, 'frames': rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description='test plans and comparison for a placed prefab')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plans'); p.add_argument('prefab'); p.add_argument('spec'); p.add_argument('out')
    p.add_argument('--map', default='cp_pfr'); p.add_argument('--usermap')
    p = sub.add_parser('compare'); p.add_argument('placed'); p.add_argument('source'); p.add_argument('prefab'); p.add_argument('--json')
    p = sub.add_parser('frames'); p.add_argument('placed'); p.add_argument('source'); p.add_argument('--frame-tool', required=True)
    p.add_argument('--json')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'frames':
            rep = frames(a.placed, a.source, a.frame_tool)
            if a.json:
                with open(a.json, 'w', encoding='utf-8') as f:
                    json.dump(rep, f, indent=1)
            for r in rep['frames']:
                print('%-14s brightness generated %.4f shipped %.4f (ratio %s), contrast %.4f / %.4f, brightest 1%% %.3f / %.3f, '
                      'pixels changed %.1f%%, mean difference %.4f, hash distance %d of 64' % (
                          r['name'], r['placed_mean_luma'], r['source_mean_luma'], r['luma_ratio'], r['placed_std_luma'],
                          r['source_std_luma'], r['placed_p99_luma'], r['source_p99_luma'], 100 * r['changed_fraction'],
                          r['mean_difference'], r['hash_distance']))
        elif a.cmd == 'plans':
            with open(a.spec, 'r', encoding='utf-8') as f:
                spec = json.load(f)
            pa, pb = plans(a.prefab, spec, a.out, a.map, a.usermap)
            print('plans: %s (%d steps, map %s), %s (%d steps, map %s)' % (os.path.join(a.out, 'placed.json'), len(pa['steps']), pa['map'],
                                                                         os.path.join(a.out, 'source.json'), len(pb['steps']), pb['map']))
        else:
            rep = compare(a.placed, a.source, a.prefab)
            if a.json:
                with open(a.json, 'w', encoding='utf-8') as f:
                    json.dump(rep, f, indent=1)
            print('world: generated map %s, shipped map %s' % (rep['placed_stats'], rep['source_stats']))
            for r in rep['marks']:
                print('mark %-22s generated %s  shipped %s  difference %s' % (r['mark'], r['placed'], r['source'], r['difference']))
            for w in rep['walks']:
                print('walk %d: generated moved %s (left %s), shipped moved %s (left %s)' % (w['n'], w['placed_moved'], w['placed_left'],
                                                                                         w['source_moved'], w['source_left']))
    except (PP.PrefabError, PP.iw7_world.WorldError, OSError, ValueError) as e:
        print('prefab_proof: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
