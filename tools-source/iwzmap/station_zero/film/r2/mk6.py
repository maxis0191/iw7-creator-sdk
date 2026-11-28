import json, shutil, os
R2 = 'C:/studio-data/sz/film/control/r2'
json.dump({"sdk": "C:/Users/ezvalo/Documents/IW7-Products/worktrees/sdk-blend/tools-source/iwzmap", "data": "C:/studio-data", "forge": "C:/forge"}, open(R2 + '/studio_blend.json', 'w'))
b = open(R2 + '/run_batch2.py', encoding='utf-8').read()
head = b[:b.index("CELLS = [")]
head = head.replace("'batch2.json'", "'batch6.json'")
head = head.replace(r"'STUDIO_ROOT': r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\studio-film-parity'", "'STUDIO_ROOT': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/studio-blend'")
head = head.replace("'STUDIO_CONFIG': os.path.join(R2, 'studio_r2.json'), 'IWZ_SDK': SDK,", "'STUDIO_CONFIG': os.path.join(R2, 'studio_blend.json'), 'IWZ_SDK': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/sdk-blend', 'STUDIO_EMITCACHE': '0',")
head = head.replace(r"'IWZ_ZONETOOL_EXE': r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe'", "'IWZ_ZONETOOL_EXE': 'C:/Users/ezvalo/Documents/IW7-Products/worktrees/x64-zt-layers/build/bin/x64/Release/zonetool.exe'")
assert 'studio-blend' in head and 'x64-zt-layers' in head and 'sdk-blend' in head, 'env not replaced'
tail = '''
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
'''
open(R2 + '/run_batch6.py', 'w', encoding='utf-8').write(head + tail)
