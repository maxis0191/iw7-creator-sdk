"""DC1 batch: (1) identity of the decals compiler against the serve compiler on an emit with no draw_classes.txt; (2) the control room on studio-decals + sdk-decals + the decals exe."""
import glob, json, os, re, shutil, subprocess, sys, time
R2 = r'C:\studio-data\sz\film\control\r2'
SDK = r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\sdk-film-control'
FILM = os.path.join(SDK, 'tools-source', 'iwzmap', 'station_zero', 'film')
STUDIO = 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/studio-decals'
MINE = 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/x64-zt-decals/build/bin/x64/Release/zonetool.exe'
SERVE = 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/x64-zt-serve/build/bin/x64/Release/zonetool.exe'
os.environ.update({'STUDIO_ROOT': STUDIO, 'STUDIO_CONFIG': os.path.join(R2, 'studio_decals.json'), 'IWZ_SDK': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/sdk-decals',
                   'STUDIO_EMITCACHE': '0', 'PYTHONIOENCODING': 'utf-8', 'IWZ_ZONETOOL_EXE': MINE})
sys.path.insert(0, FILM); sys.path.insert(0, STUDIO)
import light_measure as LM
CAMS = 'ctl_subway_east_1,ctl_subway_east_2,ctl_subway_east_5'
LOG = os.path.join(R2, 'batch_dc.json')
log = {'t0': time.time(), 'steps': []}
def step(name, fn):
    t = time.time()
    try: r = fn()
    except Exception as e: r = {'ok': False, 'exception': repr(e)}
    log['steps'].append({'step': name, 's': round(time.time() - t, 1), 'result': r})
    json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
    return r
def run(argv, cwd=None, timeout=7200, env=None):
    p = subprocess.run(argv, cwd=cwd, env=dict(env or os.environ), capture_output=True, text=True, timeout=timeout)
    return {'exit': p.returncode, 'out': p.stdout[-2500:], 'err': p.stderr[-2500:]}
def mkdoc(name):
    d = os.path.join(R2, 'docs', name)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(R2, 'docs', 'v3_keep'), d)
    return {'ok': True}
# ---- (1) identity
ID = os.path.join(R2, 'dc_id2')
shutil.rmtree(ID, ignore_errors=True); os.makedirs(ID)
step('doc dc_id', lambda: mkdoc('dc_id2'))
E = os.path.join(ID, 'emit')
r = step('emit dc_id', lambda: run([sys.executable, '-B', '-m', 'studio', 'emit', os.path.join(R2, 'docs', 'dc_id2'), '--out', E], cwd=STUDIO))
def strip():
    out = {}
    for f in ('draw_classes.txt', 'shadow_occluders.json'):
        p = os.path.join(E, f)
        out[f] = open(p, encoding='utf-8').read()[:1500] if os.path.isfile(p) else None
        if os.path.isfile(p): shutil.copy(p, os.path.join(ID, f))
        if os.path.isfile(p): os.remove(p)
    return out
step('sidecars of the emit (kept in dc_id, removed from the emit)', strip)
for tag, exe in (('serve', SERVE), ('mine', MINE)):
    step('build ' + tag, lambda t=tag, e=exe: run([sys.executable, '-B', '-m', 'compile.build', E, '--out', os.path.join(ID, 'um_' + t), '--exe', e, '--no-art', '--oneshot'], cwd=STUDIO))
def eq():
    a = glob.glob(os.path.join(ID, 'um_serve', '*.ff')); b = glob.glob(os.path.join(ID, 'um_mine', '*.ff'))
    a = [x for x in a if 'art' not in x]; b = [x for x in b if 'art' not in x]
    if not a or not b: return {'ok': False, 'a': a, 'b': b}
    return run([sys.executable, '-B', '-m', 'compile.zone_equal', a[0], b[0]], cwd=STUDIO)
res = step('zone_equal serve vs mine', eq)
log['identity_exit'] = res.get('exit'); json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
if res.get('exit') != 0:
    step('STOP: not identical', lambda: {'ok': False}); sys.exit(0)
# ---- (2) the control room
name = 'dc1'; D = os.path.join(R2, 'docs', name)
step('doc ' + name, lambda: mkdoc(name))
step('bake final', lambda: LM.studio('bake', D, '--final'))
step('shots', lambda: run([sys.executable, os.path.join(FILM, 'control_shots.py'), os.path.join(R2, 's_' + name), D, '--cams', CAMS]))
def chk():
    out = {}
    lv = glob.glob('C:/studio-data/live/%s-*' % name)
    if lv:
        for sub in ('cp_iwz.emit',):
            for f in ('draw_classes.txt', 'shadow_occluders.json'):
                p = os.path.join(lv[0], sub, f)
                if os.path.isfile(p): shutil.copy(p, os.path.join(R2, 'dc_' + f))
        lg = glob.glob(lv[0] + '/next/cp_iwz.compile.log') + glob.glob(lv[0] + '/cp_iwz.compile.log')
        if lg:
            shutil.copy(lg[0], os.path.join(R2, 'dc1.compile.log'))
            t = open(lg[0], encoding='utf-8', errors='replace').read()
            out['draw_lines'] = [l.split(']: ', 1)[-1] for l in t.splitlines() if 'draw classes' in l][:40]
    return out
step('checks', chk)
os.makedirs(os.path.join(R2, 'm_dc'), exist_ok=True); os.makedirs(os.path.join(R2, 'm_v3keep'), exist_ok=True)
def frames():
    for k in (1, 2, 5):
        shutil.copy(os.path.join(R2, 's_' + name, 'base', 'ctl_subway_east_%d.png' % k), os.path.join(R2, 'pairs_v2', 'ours_%d_decals.png' % k))
        shutil.copy(os.path.join(R2, 's_' + name, 'base', 'ctl_subway_east_%d.png' % k), os.path.join(R2, 'm_dc', 'subway_east_%d.png' % k))
        shutil.copy(os.path.join(R2, 'pairs_v2', 'ours_%d_v3keep.png' % k), os.path.join(R2, 'm_v3keep', 'subway_east_%d.png' % k))
    return {'ok': True}
step('frames', frames)
step('metric', lambda: run([sys.executable, os.path.join(FILM, 'control_compare.py'), 'metric', os.path.join(R2, 'metric', 'm6_dc.json'), r'C:\studio-data\sz\film\stockref\cp_disco',
                             'v3keep=%s,decals=%s' % (os.path.join(R2, 'm_v3keep'), os.path.join(R2, 'm_dc'))]))
step('clean', lambda: LM.clean_doc(D))
log['t1'] = time.time(); json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print('done')
