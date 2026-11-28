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
LOG = os.path.join(R2, 'batch6.json')
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
def mkdoc(name, blend):
    d = os.path.join(R2, 'docs', name)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(R2, 'docs', 'p1_final'), d)
    p = os.path.join(d, 'layers', 'ctl_room.json')
    L = json.load(open(p, encoding='utf-8'))
    for o in L['objects']:
        if o['kind'] == 'prefab':
            o['blend'] = blend
    json.dump(L, open(p, 'w', encoding='utf-8'), indent=1)
    return {'ok': True}
def checks(name):
    import re
    out = {}
    wk = glob.glob('C:/studio-data/work/%s-*' % name)
    lv = glob.glob('C:/studio-data/live/%s-*' % name)
    if wk:
        wm = os.path.join(wk[0], 'iwz_src', 'world_materials.json')
        out['wm_path'] = wm
        txt = open(wm, encoding='utf-8').read() if os.path.isfile(wm) else ''
        out['wm_bytes'] = len(txt)
        for m in ('concrete_bare_patches_clean_03', 'linoleum_floor_tiles_noline_01', 'concrete_wall_grunge_01', 'frag_metal_door_rusty', 'dt_tile_ceramic_white'):
            out[m] = m in txt
        if txt:
            shutil.copy(wm, os.path.join(R2, 'v2', name + '.world_materials.json'))
    if lv:
        lg = glob.glob(lv[0] + '/next/cp_iwz.compile.log') + glob.glob(lv[0] + '/cp_iwz.compile.log')
        if lg:
            t = open(lg[0], encoding='utf-8', errors='replace').read()
            out['warn_not_used_by_template'] = len(re.findall(r'is not used by the template world', t))
            shutil.copy(lg[0], os.path.join(R2, 'v2', name + '.compile.log'))
        ki = lv[0] + '/next/cp_iwz.kit_import.json'
        if os.path.isfile(ki):
            k = json.load(open(ki))
            out['kit_materials_new'] = len(k['materials']['new']); out['kit_w_materials'] = sum(1 for x in k['materials']['new'] + k['materials']['shared'] if x.startswith('w/') or x.startswith('*'))
    return out
os.makedirs(os.path.join(R2, 'v2'), exist_ok=True)
for name, blend in (('v2_base', 'base'), ('v2_keep', 'keep')):
    D = os.path.join(R2, 'docs', name)
    step('doc ' + name, lambda n=name, b=blend: mkdoc(n, b))
    step('bake final ' + name, lambda d=D: LM.studio('bake', d, '--final'))
    step('shots ' + name, lambda d=D, n=name: run([sys.executable, os.path.join(FILM, 'control_shots.py'), os.path.join(R2, 's_' + n), d, '--cams', CAMS]))
    step('checks ' + name, lambda n=name: checks(n))
    if name == 'v2_keep':
        um = sorted(glob.glob('C:/studio-data/live/v2_keep-*/cp_iwz'), key=os.path.getmtime)
        step('capture keep pose5', lambda: forge('capture', 'run', '--usermap', um[-1], '--map', 'cp_iwz', '--cam', '-6890,-3990,-53.88,180,0', '--fov', '65', '--hide-gun', '--hide-hud', '--also-png', '--out', os.path.join(R2, 'cap', 'v2_keep_p5')) if um else {'ok': False})
    step('clean ' + name, lambda d=D: LM.clean_doc(d))
log['t1'] = time.time()
json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print('done')
