"""Markdown tables of a generated Station Zero v2 layout (zones, doors, interactions, spawners, quest/EE spots, lights).

usage: sz2_tables.py <generated source dir> > tables.md
"""
import collections, json, os, sys

L = json.load(open(os.path.join(sys.argv[1], 'layout.json')))
o = []
o.append('### Zones (spawn volumes, script_linkname = zone)\n\n| zone | volume box (x0 y0 z0 - x1 y1 z1) | probe ambient (r g b up) |\n| --- | --- | --- |')
for z, d in L['zones'].items():
    o.append('| %s | %s | %s |' % (z, ' '.join('%g' % v for v in d['box'][:3]) + ' - ' + ' '.join('%g' % v for v in d['box'][3:]), ' '.join('%g' % v for v in d['probe'])))
o.append('\n### Doors (debris interactions; the struct on each side opens the other zone)\n\n| door | cost | zones | target scriptable | plane | span | z |\n| --- | --- | --- | --- | --- | --- | --- |')
for d in L['doors']:
    o.append('| %s | %d | %s | %s | %s = %g | %g..%g | %g..%g |' % (d['name'], d['cost'], ' / '.join(d['zones']), d['target'], 'x' if d['axis'] == 0 else 'y',
                                                             d['plane'], d['lo'], d['hi'], d['z0'], d['z1']))
o.append('\n### Interactions\n\n| kind | origin | yaw | extra |\n| --- | --- | --- | --- |')
for it in L['interactions']:
    extra = ', '.join('%s=%s' % (k, v) for k, v in it.items() if k not in ('kind', 'origin', 'yaw'))
    o.append('| %s | %s | %g | %s |' % (it['kind'], ' '.join('%g' % v for v in it['origin']), it['yaw'], extra))
o.append('\n### Quest, trap and easter egg spots (data for the gameplay / EE agents)\n\n| name | zone | origin / box | yaw |\n| --- | --- | --- | --- |')
for n, q in L['quest'].items():
    pos = q.get('origin') or q.get('box')
    o.append('| %s | %s | %s | %s |' % (n, q['zone'], ' '.join('%g' % v for v in pos), q.get('yaw', '')))
o.append('\n### Zombie spawners (stock recipe kinds)\n\n| zone | kind | origin | yaw | on nav |\n| --- | --- | --- | --- | --- |')
for s in L['spawners']:
    o.append('| %s | %s | %s | %g | %s |' % (s['zone'], s['kind'], ' '.join('%g' % v for v in s['origin']), s['yaw'], s['on_nav']))
o.append('\n### Player starts\n\n' + ', '.join('(%g %g %g)' % tuple(p) for p in L['starts']))
c = collections.Counter((l['zone'], l['fixture']) for l in L['lights'])
o.append('\n### Light fixtures (records in layout.json `lights` for the light compiler)\n\n| zone | fixture | count |\n| --- | --- | --- |')
for (z, f), n in sorted(c.items()):
    o.append('| %s | %s | %d |' % (z, f, n))
print('\n'.join(o))
