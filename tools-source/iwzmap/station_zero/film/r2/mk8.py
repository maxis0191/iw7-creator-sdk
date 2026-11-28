import json, os, shutil
R2 = 'C:/studio-data/sz/film/control/r2'
b = open(R2 + '/run_batch7.py', encoding='utf-8').read()
head = b[:b.index("import glob\ndef mkdoc")].replace("'batch7.json'", "'batch8.json'")
tail = r'''
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
'''
open(R2 + '/run_batch8.py', 'w', encoding='utf-8').write(head + tail)
