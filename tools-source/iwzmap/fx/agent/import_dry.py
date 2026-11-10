import glob, os, subprocess, sys, json
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fx_import.py')
R = os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')
A = 'vfx/iw7/levels/cp_disco/amb/'
names = sys.argv[1].split(',')
args = [sys.executable, '-I', S, R + r'\iwz-stage2\level\ztwork', 'cp_iwz', '--dump',
        'cp_disco=%s;%s;%s' % (R + r'\iwz-stage2\fx\ztwork\dump\cp_disco', R + r'\iwz-stage2\kitimport\ztwork\dump\cp_disco', R + r'\iwz-stage2\level\ztwork\dump\techsets_cp_disco'),
        '--fx', ','.join('cp_disco:' + (n if '/' in n else A + n) for n in names), '--report', R + r'\iwz-stage2\fx\import_dry.json', '--dry-run']
for t in glob.glob(R + r'\iwz-map-ref-a\dump\techsets_*'):
    c = os.path.join(t, os.path.basename(t) + '.csv')
    if os.path.isfile(c): args += ['--runtime-csv', c]
print(subprocess.run(args, capture_output=True, text=True).stdout[-1500:])
d = json.load(open(R + r'\iwz-stage2\fx\import_dry.json'))
for k, v in d['fx'].items(): print(k, {a: b for a, b in v.items() if a != 'zone'})
print('missing', d['missing']); print('ncs', d['ncs_added'])
