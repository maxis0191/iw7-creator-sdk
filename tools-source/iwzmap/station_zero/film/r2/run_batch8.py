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
os.environ.update({'STUDIO_ROOT': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/studio-blend',
                   'STUDIO_CONFIG': os.path.join(R2, 'studio_blend.json'), 'IWZ_SDK': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/sdk-blend', 'STUDIO_EMITCACHE': '0', 'PYTHONIOENCODING': 'utf-8',
                   'IWZ_ZONETOOL_EXE': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/x64-zt-layers/build/bin/x64/Release/zonetool.exe'})
sys.path.insert(0, FILM)
sys.path.insert(0, os.environ['STUDIO_ROOT'])
import light_measure as LM  # noqa: E402

CAMS = 'ctl_subway_east_1,ctl_subway_east_2,ctl_subway_east_5'
STOCK_EYES = ['900,2380,346.12,90,0', '880,3100,346.12,-90,0', '960,2760,346.12,180,0']
OURS_EYE_1 = '-6950,-4370,-53.88,90,0'
LOG = os.path.join(R2, 'batch8.json')
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





import glob
STOCK = 'C:/studio-data/store/cache/cp_disco/assets/vision/cp_disco.vision'
def stock_kv():
    kv = {}
    for ln in open(STOCK, encoding='latin1'):
        ln = ln.strip()
        if ' "' in ln:
            k, v = ln.split(' "', 1)
            v = v.rstrip('"')
            if k.endswith('Image') or ';' in v:
                continue
            kv[k] = v
    return kv
def lit_arg(kv):
    return ';'.join('%s=%s' % (k, v) for k, v in kv.items())
OURS = dict(x.split('=', 1) for x in 'fogMaxOpacity=0.95;volumetricSpotBrightness=0.15;volumetricAmbientBrightness=0.2;veilStrength=0.04;tonemapAdaptSpeed=0.3;tonemapAutoExposureAdjust=-1.25;fogDensity=30;volumetricAirDensity=0.02'.split(';'))
def set_lit(doc, kv):
    p = os.path.join(doc, 'map.json')
    m = json.load(open(p, encoding='utf-8'))
    a = m['settings']['build']['darkness']['args']
    a[a.index('--lit') + 1] = lit_arg(kv)
    json.dump(m, open(p, 'w', encoding='utf-8'), indent=1)
    return {'ok': True, 'lit': lit_arg(kv)[:200]}
name = 'v4'
D = os.path.join(R2, 'docs', name)
def mk():
    shutil.rmtree(D, ignore_errors=True)
    shutil.copytree(os.path.join(R2, 'docs', 'v3_keep'), D)
    return set_lit(D, stock_kv())
step('doc v4 (stock vision)', mk)
step('bake final v4', lambda: LM.studio('bake', D, '--final'))
sys.path.insert(0, FILM)
import control_shots as CS
cams = CAMS.split(',')
step('live start', lambda: LM.studio('live', 'start', D, '--idle-min', '60'))
step('power', lambda: LM.studio('live', 'power', D, 'on'))
time.sleep(12)
def shoot(tag):
    lg = {}
    CS.shots(os.path.join(R2, 's_v4', tag), D, cams, lg, tag)
    return lg
step('shots a_stock_vision', lambda: shoot('a_stock'))
# b1: our vision, exposure of stock (0)
kv = dict(OURS); kv['tonemapAutoExposureAdjust'] = '0'
step('set b1', lambda: set_lit(D, kv))
step('sync b1', lambda: LM.studio('live', 'sync', D))
step('power b1', lambda: LM.studio('live', 'power', D, 'on'))
time.sleep(12)
step('shots b1_ours_exp0', lambda: shoot('b1_ours_exp0'))
# b2: stock vision with our exposure
kv = stock_kv(); kv['tonemapAutoExposureAdjust'] = '-1.25'
step('set b2', lambda: set_lit(D, kv))
step('sync b2', lambda: LM.studio('live', 'sync', D))
step('power b2', lambda: LM.studio('live', 'power', D, 'on'))
time.sleep(12)
step('shots b2_stock_exp-1.25', lambda: shoot('b2_stock_exp125'))
step('stop', lambda: LM.studio('live', 'stop', D))
step('clean', lambda: LM.clean_doc(D))
log['t1'] = time.time()
json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print('done')
