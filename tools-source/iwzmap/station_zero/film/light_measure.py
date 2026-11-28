r"""light_measure: the lighting numbers of LIGHTING-GAP section 0 for game frames, ours beside stock (worker L1, 28 Nov 2026).

    python light_measure.py measure <out.json> <png or folder> [...]       numbers per frame (and medians per argument)
    python light_measure.py shoot <pass folder> <doc> [--cams a,b] [--states on] [--variant <doc> ...] [--no-start]
                                                                           one session: start, power, shots, stop

Numbers (display-encoded luminance 0..1 of the PNG, Rec.709 weights, unless named linear):
  p5, p50, p95, p99; dark = share of pixels under 0.03; clip = share at or above 0.98;
  floor = mean luminance of rows 70 to 97 % (the floor band);
  for shop-front cameras (name ends `_front`): ground = linear mean luminance of rows 80 to 97 % of the middle 50 % of the width,
  ground_br = its linear blue / red; front = the same of rows 60 to 70 % (the foot of the lit front above the ground patch; this band
  reproduces LIGHTING-GAP's front column: stock shopfronts_2 0.039 / b/r 0.87 against 0.038 / 0.71, our pass-8 pink shop 0.033 / 0.19
  against 0.033 / 0.20), front_br; g_f = ground / front. Frames whose shot answer was stale or failed are not measured by `shoot`.
The environment of `shoot`: STUDIO_ROOT (the Studio worktree), STUDIO_CONFIG, IWZ_SDK, IWZ_ZONETOOL_EXE, set by the caller.
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

FIVE = ('arc_east_long', 'arc_hole_nine_front', 'arc_copy_stop_front', 'arc_needle_drop_front', 'arc_west_long')
STOCK = r'C:\studio-data\sz\film\stockref\cp_disco'
STOCK_SETS = {'stock_subway': ['subway_east_%d.png' % k for k in range(1, 9)],
              'stock_shopfronts_2': ['shopfronts_2.png'], 'stock_shopfronts_13': ['shopfronts_13.png']}


def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def numbers(path, front=None):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float64) / 255.0
    h, w, _ = a.shape
    y = a @ np.array([0.2126, 0.7152, 0.0722])
    q = np.percentile(y, [5, 50, 95, 99])
    r = {'p5': q[0], 'p50': q[1], 'p95': q[2], 'p99': q[3], 'dark': float((y < 0.03).mean()), 'clip': float((y >= 0.98).mean()),
         'floor': float(y[int(.70 * h):int(.97 * h)].mean())}
    if front is None:
        front = os.path.splitext(os.path.basename(path))[0].endswith('_front') or 'shopfronts' in os.path.basename(path)
    if front:
        lin = _lin(a)
        for key, (r0, r1) in (('ground', (.80, .97)), ('front', (.60, .70))):
            patch = lin[int(r0 * h):int(r1 * h), int(.25 * w):int(.75 * w)].reshape(-1, 3).mean(0)
            r[key] = float(patch @ np.array([0.2126, 0.7152, 0.0722]))
            r[key + '_br'] = float(patch[2] / max(patch[0], 1e-6))
        r['g_f'] = r['ground'] / max(r['front'], 1e-6)
    return {k: round(float(v), 4) for k, v in r.items()}


def measure(out, args):
    res = {}
    for arg in args:
        if arg in STOCK_SETS:
            files = [os.path.join(STOCK, f) for f in STOCK_SETS[arg]]
        elif os.path.isdir(arg):
            files = sorted(os.path.join(arg, f) for f in os.listdir(arg) if f.endswith('.png'))
        else:
            files = [arg]
        rows = {os.path.basename(f): numbers(f) for f in files if os.path.isfile(f)}
        keys = sorted(set(k for v in rows.values() for k in v))
        med = {k: round(float(np.median([v[k] for v in rows.values() if k in v])), 4) for k in keys}
        res[arg] = {'frames': rows, 'median': med}
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
    for arg, v in res.items():
        print(arg)
        for name, row in v['frames'].items():
            print('  %-34s %s' % (name, ' '.join('%s=%s' % kv for kv in row.items())))
    return res


def studio(*args):
    root = os.environ.get('STUDIO_ROOT', r'C:\studio')
    p = subprocess.run([sys.executable, '-m', 'studio'] + list(args), cwd=root, env=dict(os.environ), capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {'ok': False, 'exit': p.returncode, 'stdout': p.stdout[-1500:], 'stderr': p.stderr[-1500:]}


def _keep_compile_log(sub):
    """the newest build's compile log (the live folder keeps only the last one) beside the variant's frames: its light slots and voxel lists"""
    import glob
    import shutil
    logs = glob.glob(os.path.join(os.environ.get('STUDIO_DATA', r'C:\studio-data'), 'live', '*', 'next', 'cp_iwz.compile.log'))
    if logs:
        shutil.copyfile(max(logs, key=os.path.getmtime), os.path.join(sub, 'compile.log'))


def clean_doc(doc):
    """after `live stop`: this document's own build server, live folder and work folder (exactly its key, `live.doc_key`), so a run of many
    one-document sessions does not fill the drive (TOOL-FAULTS L1-1). Nothing of another document is matched."""
    import shutil
    from studio import live as LV
    key = LV.doc_key(doc)
    data = os.environ.get('STUDIO_DATA', r'C:\studio-data')
    out = []
    work = os.path.join(data, 'work', key)
    p = subprocess.run(['powershell', '-NoProfile', '-Command',
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*compile.serverd*--work %s *' } "
                        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }" % work.replace("'", "''")], capture_output=True, text=True)
    out += ['server %s' % x for x in p.stdout.split()]
    time.sleep(1)
    for f in (os.path.join(data, 'live', key), work):
        if os.path.basename(f) == key and os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)
            out.append(f)
    return out


def shoot(folder, doc, cams, states, variants, start=True):
    """One session of `doc`; for each document (doc, then each variant synced into the session) and each state, the cameras."""
    os.makedirs(folder, exist_ok=True)
    log = {'doc': doc, 'variants': variants, 't0': time.time()}
    if start:
        t = time.time()
        log['start'] = studio('live', 'start', doc, '--idle-min', '30')
        log['start_s'] = round(time.time() - t, 1)
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import live as LV
    sess = LV.session_name(doc)
    log['session'] = sess
    try:
        for k, d in enumerate([doc] + list(variants)):
            sub = folder if k == 0 else os.path.join(folder, os.path.basename(os.path.normpath(d)))
            sa = [] if k == 0 else ['--session', sess]
            if k == 0 and start and not (log.get('start') or {}).get('ok'):
                log['aborted_0'] = 'start failed'
                break
            if k:
                t = time.time()
                log['sync_%d' % k] = studio('live', 'sync', d, *sa)
                log['sync_%d_s' % k] = round(time.time() - t, 1)
                if not log['sync_%d' % k].get('ok'):           # a failed sync leaves the previous document in the game: its frames would be a false null
                    log['aborted_%d' % k] = 'sync failed'
                    continue
            os.makedirs(sub, exist_ok=True)
            _keep_compile_log(sub)
            for state in states:
                os.makedirs(os.path.join(sub, state), exist_ok=True)
                log['power_%d_%s' % (k, state)] = studio('live', 'power', d, state, *sa)
                if not log['power_%d_%s' % (k, state)].get('ok'):
                    log['aborted_%d_%s' % (k, state)] = 'power failed'
                    continue
                time.sleep(10)                    # the brief's 10 s after the switch (on top of the tool's own settle)
                for c in cams:
                    r = studio('live', 'shot', d, '--clean', '--camera', c, '--out', os.path.join(sub, state, c + '.png'), '--allow-stale', *sa)
                    log['shot_%d_%s_%s' % (k, state, c)] = {x: r.get(x) for x in ('ok', 'settled', 'error', 'stale', 'stderr')}
    finally:
        if start:
            log['stop'] = studio('live', 'stop', doc)
            if os.environ.get('L1_CLEAN_AFTER'):
                log['cleaned'] = clean_doc(doc)
        log['t1'] = time.time()
        json.dump(log, open(os.path.join(folder, 'shoot.json'), 'w', encoding='utf-8'), indent=1, default=str)
    bad = [k for k, v in log.items() if k.startswith('shot_') and (not v.get('ok') or v.get('stale'))]
    for k in bad:                                  # a failed or stale frame is never measured: remove what it wrote
        _, n, state, cam = k.split('_', 3)
        sub = folder if n == '0' else os.path.join(folder, os.path.basename(os.path.normpath(variants[int(n) - 1])))
        p = os.path.join(sub, state, cam + '.png')
        if os.path.isfile(p):
            os.replace(p, p + '.rejected')
    print(json.dumps({'folder': folder, 'start_ok': (log.get('start') or {}).get('ok'), 'failed_or_stale': bad,
                      'aborted': {k: v for k, v in log.items() if k.startswith('aborted')},
                      'seconds': round(log['t1'] - log['t0'])}, indent=1))


def main(argv):
    if argv[0] == 'measure':
        measure(argv[1], argv[2:])
    elif argv[0] == 'shoot':
        a = argv[1:]
        opt = {'--cams': ','.join(FIVE), '--states': 'on'}
        variants, start = [], True
        pos = []
        i = 0
        while i < len(a):
            if a[i] in opt:
                opt[a[i]] = a[i + 1]
                i += 2
            elif a[i] == '--variant':
                variants.append(a[i + 1])
                i += 2
            elif a[i] == '--no-start':
                start = False
                i += 1
            else:
                pos.append(a[i])
                i += 1
        cams = opt['--cams'].split(',')
        if cams == ['all']:
            sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
            from studio import Map
            cams = [o['name'] for o in Map.load(pos[1]).objects() if o['kind'] == 'camera']
        shoot(pos[0], pos[1], cams, opt['--states'].split(','), variants, start)


if __name__ == '__main__':
    main(sys.argv[1:])
