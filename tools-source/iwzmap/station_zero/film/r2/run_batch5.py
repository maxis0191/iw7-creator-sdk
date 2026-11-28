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

CAMS = 'ctl_subway_east_1,ctl_subway_east_5'
STOCK_EYES = ['900,2380,346.12,90,0', '880,3100,346.12,-90,0', '960,2760,346.12,180,0']
OURS_EYE_1 = '-6950,-4370,-53.88,90,0'
LOG = os.path.join(R2, 'batch5.json')
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






os.environ['STUDIO_EMITCACHE'] = '0'
D = os.path.join(R2, 'docs', 'u_base2')
step('shots u_base2 (keep usermap)', lambda: run([sys.executable, os.path.join(R2, 'shots_nobake.py'), os.path.join(R2, 's_u_base5'), D, '--cams', 'ctl_subway_east_5']))
um = sorted(glob.glob('C:/studio-data/live/u_base2-*/cp_iwz'), key=os.path.getmtime)
step('usermaps', lambda: um)
POSE5 = '-6890,-3990,-53.88,180,0'
step('capture pose5', lambda: forge('capture', 'run', '--usermap', um[-1], '--map', 'cp_iwz', '--cam', POSE5, '--fov', '65', '--hide-gun', '--hide-hud', '--also-png', '--out', os.path.join(R2, 'cap', 'ours_p5'))
     if um else {'ok': False})
step('clean', lambda: LM.clean_doc(D))
log['t1'] = time.time()
json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print('done')
