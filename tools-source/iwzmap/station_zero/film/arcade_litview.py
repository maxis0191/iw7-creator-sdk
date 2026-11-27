r"""arcade_litview: a copy of the shell document whose dark vision is the lit one (diagnostic only).

    python arcade_litview.py [doc] [out]

Why: cp_iwz_darkness.gsc releases the dark vision only inside its loop over power banks; with every light baked (PLAN decision 3)
there is no bank, so `live power on` keeps the dark vision (TOOL-FAULTS, A2 27 Nov). This variant shows the lit look. Its frames are
labelled LIT (variant), never ON.
"""
import json
import os
import shutil
import sys

doc = sys.argv[1] if len(sys.argv) > 1 else r'C:\studio-data\sz\film\arcade\shell\doc'
out = sys.argv[2] if len(sys.argv) > 2 else r'C:\studio-data\sz\film\arcade\shell\litview'
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(doc, out)
p = os.path.join(out, 'map.json')
j = json.load(open(p, encoding='utf-8'))
a = j['settings']['build']['darkness']['args']
a[a.index('--dark') + 1] = a[a.index('--lit') + 1].replace('tonemapAdaptSpeed=0.3', 'tonemapAdaptSpeed=1')
j['name'] += '_litview'
json.dump(j, open(p, 'w', encoding='utf-8'), indent=1)
print(out, a[a.index('--dark') + 1])
