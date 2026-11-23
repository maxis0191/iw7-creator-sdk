"""The map's own vision file (fog, tone map and exposure, colour grade, glare) from the document's light settings.

The zone build already ships `vision/<map>.vision`: assemble.py copies the stock `vision/cp_zmb.vision` under the map's name (a rawfile
row), the engine reads the vision named like the map, and the darkness route proved that editing this file changes the lit frame
(fog veil gone with fogMaxOpacity 0.03, `darkness/README.md`). A document therefore needs no new asset to set its own look: sz2_assemble.py
rewrites this one file from layout.json `lighting`:

  "vision":   {"<key>": value, ...}        any key of a stock vision file, written as it is (a number, or a list for "r g b")
  "fog":      {"color": [r,g,b], "density": d, "start": s, "max_opacity": a, "intensity": i}
              -> fogColor, fogDensity, fogStartDist, fogMaxOpacity, fogColorIntensity
  "exposure": {"auto": true|false, "value": e, "adjust": a}
              -> tonemapAuto, tonemapExposure, tonemapExposureAdjust
Convenience keys are applied first, `vision` after (it wins). A key that no stock vision file of the dump holds is refused with the nearest
names (a typo would otherwise be written and ignored by the engine). Not here: a look that changes by zone (needs a script call
`visionsetnaked` on zone entry and one rawfile per look, see docs/IWZ-EMIT-CONTRACT.md).
"""
import difflib
import glob
import os
import re

FOG = {'color': 'fogColor', 'density': 'fogDensity', 'start': 'fogStartDist', 'max_opacity': 'fogMaxOpacity', 'intensity': 'fogColorIntensity'}
EXPOSURE = {'auto': 'tonemapAuto', 'value': 'tonemapExposure', 'adjust': 'tonemapExposureAdjust'}
LINE = re.compile(r'^(\w+)\s+"(.*)"\s*$')


def fmt(v):
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, (list, tuple)):
        return ' '.join(fmt(x) for x in v)
    if isinstance(v, float):
        return '%g' % v
    return str(v)


def keys_of(text):
    return [m.group(1) for m in (LINE.match(l) for l in text.splitlines()) if m]


def known_keys(vision_dirs):
    out = set()
    for d in vision_dirs:
        for f in glob.glob(os.path.join(d, '*.vision')):
            out.update(keys_of(open(f, encoding='latin1').read()))
    return out


def edits_of(lighting):
    """{key: value text} from a layout.json `lighting` block (convenience keys first, then raw `vision`)"""
    e = {}
    for name, table in (('fog', FOG), ('exposure', EXPOSURE)):
        for k, v in (lighting.get(name) or {}).items():
            if k not in table:
                raise ValueError('lighting.%s.%s: not one of %s' % (name, k, ', '.join(sorted(table))))
            e[table[k]] = fmt(v)
    for k, v in (lighting.get('vision') or {}).items():
        e[k] = fmt(v)
    return e


def apply(text, edits, known=None):
    """-> (new text, {'changed': {key: [old, new]}, 'added': [keys]}). Unknown keys (not in `known`, when given) raise ValueError."""
    if known:
        for k in edits:
            if k not in known:
                raise ValueError('vision key %s is in no stock vision file; nearest: %s' % (k, ', '.join(difflib.get_close_matches(k, sorted(known), 4)) or '-'))
    lines = text.split('\n')
    rep = {'changed': {}, 'added': []}
    seen = set()
    for i, l in enumerate(lines):
        m = LINE.match(l)
        if m and m.group(1) in edits:
            k = m.group(1)
            rep['changed'][k] = [m.group(2), edits[k]]
            lines[i] = '%s "%s"' % (k, edits[k])
            seen.add(k)
    tail = [k for k in edits if k not in seen]
    if tail:
        while lines and lines[-1] == '':
            lines.pop()
        lines += ['%s "%s"' % (k, edits[k]) for k in tail] + ['']
        rep['added'] = tail
    return '\n'.join(lines), rep


def apply_to_zone(zone_dir, mapname, lighting):
    """rewrite <zone_dir>/vision/<mapname>.vision (never through a hardlink into a stock dump). -> report or None when there is nothing to do"""
    edits = edits_of(lighting or {})
    if not edits:
        return None
    path = os.path.join(zone_dir, 'vision', mapname + '.vision')
    if not os.path.isfile(path):
        raise FileNotFoundError('%s: the assembly did not ship the map vision (assemble.py copies the stock cp_zmb.vision under the map name)' % path)
    text = open(path, encoding='latin1').read()
    new, rep = apply(text, edits, known_keys([os.path.join(zone_dir, 'vision')]))
    os.remove(path)
    open(path, 'w', newline='\n', encoding='latin1').write(new)
    return rep
