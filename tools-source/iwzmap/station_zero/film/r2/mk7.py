import json, shutil, os
R2 = 'C:/studio-data/sz/film/control/r2'
b = open(R2 + '/run_batch6.py', encoding='utf-8').read()
head = b[:b.index("import glob\ndef mkdoc")].replace("'batch6.json'", "'batch7.json'")
tail = b[b.index("import glob\ndef mkdoc"):b.index("os.makedirs(os.path.join(R2, 'v2'), exist_ok=True)")]
tail = tail.replace("            o['blend'] = blend\n", "            o['blend'] = blend\n            o['prefab'] = 'ctl_subway_east_lay'\n")
tail += '''os.makedirs(os.path.join(R2, 'v2'), exist_ok=True)
name = 'v3_keep'
D = os.path.join(R2, 'docs', name)
step('doc ' + name, lambda: mkdoc(name, 'keep'))
step('bake final ' + name, lambda: LM.studio('bake', D, '--final'))
step('shots ' + name, lambda: run([sys.executable, os.path.join(FILM, 'control_shots.py'), os.path.join(R2, 's_' + name), D, '--cams', CAMS]))
def chk():
    out = checks(name)
    lv = glob.glob('C:/studio-data/live/%s-*' % name)
    if lv:
        for f in glob.glob(lv[0] + '/cp_iwz.emit/world.bin') + glob.glob(lv[0] + '/cp_iwz.emit/surfaces.json'):
            shutil.copy(f, os.path.join(R2, 'v2', name + '.' + os.path.basename(f)))
        out['emit_files'] = sorted(os.listdir(lv[0] + '/cp_iwz.emit'))[:40]
        import re
        lg = os.path.join(R2, 'v2', name + '.compile.log')
        if os.path.isfile(lg):
            out['layer_lines'] = re.findall(r'layer: .*', open(lg, encoding='utf-8', errors='replace').read())[:4]
    return out
step('checks ' + name, chk)
um = sorted(glob.glob('C:/studio-data/live/%s-*/cp_iwz' % name), key=os.path.getmtime)
step('capture pose5', lambda: forge('capture', 'run', '--usermap', um[-1], '--map', 'cp_iwz', '--cam', '-6890,-3990,-53.88,180,0', '--fov', '65', '--hide-gun', '--hide-hud', '--also-png', '--out', os.path.join(R2, 'cap', name + '_p5')) if um else {'ok': False})
step('clean ' + name, lambda: LM.clean_doc(D))
log['t1'] = time.time()
json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=1, default=str)
print('done')
'''
open(R2 + '/run_batch7.py', 'w', encoding='utf-8').write(head + tail)
