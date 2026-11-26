r"""Round 10: Station Zero's base emit with its inert decor script_models turned into compiled static models (entity budget, official client cap 768).

    python arcade_base10.py [src_emit] [dst_emit]      default C:\studio-data\sz\base\emit -> C:\studio-data\sz\base_r10\emit (the source is never touched)

Why they are script_models: station_zero2.py (the generator) turns template-zone decor into smodels.txt rows only when `d['model'] not in KIT_MODELS`; every decor model that
the kit brings (foreign zones: cp_disco, cp_rave, clk_*, the train port's iwz_*) stays a `script_model` entity, one networked record each in every client snapshot. Studio's
compile brings kit models as static models since 25 Nov (`compile/build.py`, kit_import --stage-xmodels), so the rule is no longer needed for models that are never moved,
named or swapped by a script. This copy converts exactly those: an unnamed `script_model` (no targetname) of a kit model of the list below, away from the 0 0 -3000 placeholders.
Each conversion removes the block from ents.txt, appends the row to smodels.txt (model x y z pitch yaw roll 1), and marks the layout.json decor row `static`.
"""
import json
import os
import re
import shutil
import sys

SRC = r'C:\studio-data\sz\base\emit'
DST = r'C:\studio-data\sz\base_r10\emit'
# stock models of other zones (proven as static models in the Arcade layer builds), then the train port's plain environment pieces
CONVERT = ('clk_emergency_light', 'com_barrel_tan_rust', 'cp_disco_street_barricade', 'cp_disco_subway_lockers_02', 'cp_disco_subway_turnstyle_animated',
           'cp_disco_subway_turnstyle_missing_arm', 'cp_disco_worn_subway_bench', 'ls_biohazard_sheet_01', 'ls_biohazard_sheet_02', 'newspaper_single_fn_01',
           'newspaper_stack_fn_01', 'p7_zm_der_plank_wood_2x12x96',
           'iwz_platform_edge_128', 'iwz_platform_edge_64', 'iwz_track_256', 'iwz_track_256_disused', 'iwz_track_256_disused_end', 'iwz_track_256_3r_from200')
BLOCK = re.compile(r'\{\n(.*?)\n\}\n', re.S)


def fields(body):
    return dict((m.group(1), m.group(2)) for m in re.finditer(r'^(\d+) "([^"]*)"$', body, re.M))


def convert(src=SRC, dst=DST, models=CONVERT):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    text = open(os.path.join(dst, 'ents.txt'), newline='').read()
    kept, rows, per = [], [], {}
    for m in BLOCK.finditer(text):
        f = fields(m.group(1))
        if f.get('157') == 'script_model' and '822' not in f and f.get('497') in models and f.get('543') and not f['543'].startswith('0 0 -3000'):
            ang = f.get('65', '0 0 0').split()
            rows.append('%s %s %s 1' % (f['497'], f['543'], ' '.join(ang[:3])))
            per[f['497']] = per.get(f['497'], 0) + 1
        else:
            kept.append(m.group(0))
    open(os.path.join(dst, 'ents.txt'), 'w', newline='').write(''.join(kept))
    sm = open(os.path.join(dst, 'smodels.txt'), newline='').read()
    if sm and not sm.endswith('\n'):
        sm += '\n'
    open(os.path.join(dst, 'smodels.txt'), 'w', newline='').write(sm + '\n'.join(rows) + '\n')
    lay = json.load(open(os.path.join(dst, 'layout.json')))
    n = 0
    for d in lay['decor']:
        if not d.get('static') and not d.get('targetname') and d['model'] in models:
            d['static'] = True
            n += 1
    open(os.path.join(dst, 'layout.json'), 'w').write(json.dumps(lay, indent=1))
    return {'converted': len(rows), 'decor_marked': n, 'per_model': per, 'src': src, 'dst': dst}


if __name__ == '__main__':
    a = sys.argv[1:]
    print(json.dumps(convert(*(a[:2])), indent=1))
