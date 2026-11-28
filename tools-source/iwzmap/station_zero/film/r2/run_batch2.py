"""R2 batch (one background job): the 2 x 2 (probe room on/off x draft/final bake) of the control room at poses 1, 2, 5, an SSAO cell,
stock captures with and without r_ssao, one capture of ours with r_ssao. Every step continues on failure and is logged in batch.json."""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

R2 = r'C:\studio-data\sz\film\control\r2'
SDK = r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-film-control'
FILM = os.path.join(SDK, 'tools-source', 'iwzmap', 'station_zero', 'film')
os.environ.update({'STUDIO_ROOT': r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\studio-film-parity',
                   'STUDIO_CONFIG': os.path.join(R2, 'studio_r2.json'), 'IWZ_SDK': SDK, 'PYTHONIOENCODING': 'utf-8',
                   'IWZ_ZONETOOL_EXE': r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe'})
sys.path.insert(0, FILM)
sys.path.insert(0, os.environ['STUDIO_ROOT'])
import light_measure as LM  # noqa: E402

CAMS = 'ctl_subway_east_1,ctl_subway_east_2,ctl_subway_east_5'
STOCK_EYES = ['900,2380,346.12,90,0', '880,3100,346.12,-90,0', '960,2760,346.12,180,0']
OURS_EYE_1 = '-6950,-4370,-53.88,90,0'
LOG = os.path.join(R2, 'batch2.json')
log = {'t0': time.time(), 'steps': []}


def step(name, fn):
    t = time.time()
    try:
        r = fn()
    except Exception as e:  # noqa: BLE001
        r = {'ok': False, 'exception': repr(e)}
    log['steps'].append({'step': name, 's': round(time.time() - t, 1), 'result': r})
    json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
    return r


def run(argv, cwd=None, timeout=7200):
    p = subprocess.run(argv, cwd=cwd, env=dict(os.environ), capture_output=True, text=True, timeout=timeout)
    return {'exit': p.returncode, 'out': p.stdout[-3000:], 'err': p.stderr[-2000:]}


def doc(name, probe, ssao=False):
    out = os.path.join(R2, 'docs', name)
    argv = [sys.executable, os.path.join(FILM, 'control_doc.py'), '--mode', 'bounce', '--base-only', '--out', out] + ([] if probe else ['--no-probe-room'])
    r = run(argv)
    if ssao and r['exit'] == 0:
        p = os.path.join(out, 'map.json')
        m = json.load(open(p, encoding='utf-8'))
        m.setdefault('settings', {}).setdefault('live', {})['dvars_at_launch'] = {'r_ssao': 'MDAO'}
        json.dump(m, open(p, 'w', encoding='utf-8'), indent=1)
    return r


def forge(*a):
    return run([sys.executable, '-B', r'C:\forge\forge.py'] + list(a), timeout=3600)



CELLS = [('p1_draft', True, False), ('p1_final', True, False), ('p0_draft', False, False), ('p0_final', False, False), ('p1_final_ssao', True, True)]
SP = r'C:/studio-data/sz/film/stockref/plans'
step('doc p1_final_ssao', lambda: doc('p1_final_ssao', True, True))
step('sense', lambda: forge('sense'))
step('bake final p1_final_ssao', lambda: LM.studio('bake', os.path.join(R2, 'docs', 'p1_final_ssao'), '--final'))
for name, _p, _s in CELLS:
    clean = name != 'p1_final_ssao'
    step('shots ' + name, lambda n=name, c=clean: run([sys.executable, os.path.join(FILM, 'control_shots.py'), os.path.join(R2, 's_' + n),
                                                       os.path.join(R2, 'docs', n), '--cams', CAMS] + (['--clean-after'] if c else [])))
# stock frames with r_ssao=MDAO at launch, same poses
def stock_mdao():
    r = run([sys.executable, os.path.join(SP, 'make_plans.py'), '_r2', 'east_s_end_1,east_n_end_1,across_1'], cwd=SP)
    plan = os.path.join(SP, 'stockref-cp_disco_r2.json')
    out = os.path.join(R2, 'stock_mdao_run')
    r2 = forge('run', plan, '--library-dir', SP + '/lib', '--dvar-at-launch', 'r_ssao=MDAO', '--out', out, '--force-out')
    from PIL import Image
    od = os.path.join(R2, 'stock_mdao')
    os.makedirs(od, exist_ok=True)
    for n, nm in ((1, 'east_s_end_1'), (2, 'east_n_end_1'), (5, 'across_1')):
        f = os.path.join(out, 'iwz_subway_east__%s.bmp' % nm)
        if os.path.isfile(f):
            Image.open(f).convert('RGB').save(os.path.join(od, 'subway_east_%d.png' % n))
    return {'plan': r, 'run': r2, 'frames': sorted(os.listdir(od))}
step('stock frames MDAO', stock_mdao)
um = sorted(glob.glob(r'C:\studio-data\live\p1_final_ssao-*\cp_iwz'), key=os.path.getmtime)
step('capture ours ssao', lambda: forge('capture', 'run', '--usermap', um[-1], '--map', 'cp_iwz', '--cam', OURS_EYE_1, '--set', 'r_ssao=MDAO',
                                         '--fov', '65', '--hide-gun', '--hide-hud', '--also-png', '--out', os.path.join(R2, 'cap', 'ours_ssao'))
     if um else {'ok': False, 'error': 'no usermap of p1_final_ssao'})
for tag, extra in (('stock_ssao', ['--set', 'r_ssao=MDAO']), ('stock_plain', [])):
    args = ['capture', 'run', '--map', 'cp_disco', '--fov', '65', '--hide-gun', '--hide-hud', '--also-png', '--out', os.path.join(R2, 'cap', tag)]
    for e in STOCK_EYES[:1]:
        args += ['--cam', e]
    step('capture ' + tag, lambda a=args, x=extra: forge(*(a + x)))
step('clean ssao doc', lambda: LM.clean_doc(os.path.join(R2, 'docs', 'p1_final_ssao')))
step('rdoc ssao', lambda: run([sys.executable, os.path.join(R2, 'run_ssao.py')], timeout=3000))
log['t1'] = time.time()
json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print(json.dumps([(s['step'], s['s'], (s['result'] or {}).get('exit', (s['result'] or {}).get('ok'))) for s in log['steps']]))
