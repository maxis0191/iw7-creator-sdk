"""Audit of the colour map chosen for every world material of an emit (no Blender, no game).

    python iwz_audit.py --src <emit src> --out <dir>      writes material_audit.md and material_audit.json

For each material of world.bin: the image used, the evidence that it is the colour map the engine samples (the semantic
field of the material json textureTable: 14 = colour of the stock lit techsets, 2 = colour of custom / unlit / emissive
techsets, 15 = packed normal-occlusion-gloss, 5 = detail normal, 8 = specular, 9 = occlusion, 16 = packed alpha / mask), the
techset, and a verdict: STRONG (exactly one texture of the colour semantic), MEDIUM (several, the first of that semantic is
used), WEAK (more than one candidate of semantic 2 with nothing to tell them apart, or a name heuristic). A custom material
(custom_materials.json) is its TGA, or its stock base material with a tint.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iwz_assets as A  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    index = A.DumpIndex()
    world = A.read_world(os.path.join(a.src, 'world.bin'))
    cm = json.load(open(os.path.join(a.src, 'custom_materials.json')))['custom']
    customs = {v['path']: v for v in cm.values()}
    tris = {}
    for s in world['surfaces']:
        tris[int(s['mat'])] = tris.get(int(s['mat']), 0) + int(s['tc'])
    rows = []
    for i, name in enumerate(world['materials']):
        c = customs.get(name)
        row = {'material': name, 'triangles': tris.get(i, 0)}
        if c and c.get('tga'):
            row.update(image=os.path.basename(c['tga']), source='custom_materials.json: TGA', verdict='STRONG',
                       evidence='the generator writes this TGA as the colour image (semantic 2) of a clone of %s' % c['base'])
        else:
            mi, err = A.material_info(index, c['base'] if c else name) if not (c and not c.get('base')) else (None, 'no base')
            if mi is None:
                row.update(image=None, source='-', verdict='UNRESOLVED', evidence=err)
            else:
                how = mi['how']
                verdict = 'WEAK' if how.startswith('WEAK') else ('MEDIUM' if 'candidates' in how else 'STRONG')
                tt = json.load(open(mi['json'])).get('textureTable', [])
                row.update(image=mi['image'], source=('custom tint of ' + c['base'] + ' x ' + str(c.get('tint'))) if c else 'dump material json',
                           verdict=verdict, techset=mi['techset'], evidence='%s; textureTable = %s' % (how, [(t['semantic'], t['image'][:44]) for t in tt]),
                           emissive_image=mi['emissive_image'], emissive_para=mi['emissive_para'], occlusion_image=mi['occlusion_image'])
        rows.append(row)
    os.makedirs(a.out, exist_ok=True)
    json.dump(rows, open(os.path.join(a.out, 'material_audit.json'), 'w'), indent=1)
    cnt = {}
    for r in rows:
        cnt[r['verdict']] = cnt.get(r['verdict'], 0) + 1
    lines = ['# World material audit', '', 'Verdicts: %s' % cnt, '', '| material | tris | image used | verdict | evidence |', '|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | %d | %s | %s | %s |' % (r['material'], r['triangles'], (r['image'] or '-')[:60], r['verdict'], r['evidence'].replace('|', '/')))
    open(os.path.join(a.out, 'material_audit.md'), 'w').write('\n'.join(lines) + '\n')
    print(cnt)
    for r in rows:
        if r['verdict'] not in ('STRONG',):
            print(r['verdict'], r['material'], '|', r['evidence'][:200])


if __name__ == '__main__':
    main()
