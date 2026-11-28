"""Layer-stream layout table of the layered world techsets (docs/station-zero/redesign/BLEND-LAYERS.md sections 1.3 and 4.2 step 1).

A stock layered (`*`) world surface carries, besides its 44 byte vertices (slot 0), a per-surface layer stream (slot 1) of `stride`
bytes a vertex. Stride and content are set by the material's lit technique: ORDER from the vertex declaration string (the names after
pp, cc0, t0t0, nn, tt2; the target of a name is its last two characters: t<hex> = TEXCOORD<hex>, c<d> = COLOR<d>), SIZE from the vertex
shader input signature mask: TEXCOORD3, 4, 7 are float32 x the components used, TEXCOORD5, 6, 9, 10, 11, 13 and COLOR1 are 4 bytes (unorm8x4).

The table (data/layer_layouts.json) is extracted once from the stock dumps and shipped, so builds need no dump:
    python -B extract_layouts.py [--dump-root <ztwork/dump>] [--zones cp_disco,cp_final] [--out data/layer_layouts.json]
`supported` = the lit technique reads only TEXCOORD3, 4, 5, 6, 9: the writer can fill it (planar uv + rotation bytes). The 5- and 6-layer
techniques that also read TEXCOORD10, 11, 13 or COLOR1 are not decoded and are refused (blend_core)."""
import argparse
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE_PATH = os.path.join(HERE, 'data', 'layer_layouts.json')
DEFAULT_DUMP_ROOT = r'C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\kitimport\ztwork\dump'
SUPPORTED_TEXCOORDS = (3, 4, 5, 6, 9)
F32_TEXCOORDS = (3, 4, 7)
BASE_NAMES = {'pp', 'cc0', 't0t0', 'nn', 'tt2'}
VERSION = 1


def isgn(path):
    """input signature of a DXBC vertex shader: [(semantic, index, register, mask)]"""
    b = open(path, 'rb').read()
    if b[:4] != b'DXBC':
        raise ValueError('%s is not DXBC' % path)
    n = struct.unpack_from('<I', b, 28)[0]
    for i in range(n):
        off = struct.unpack_from('<I', b, 32 + 4 * i)[0]
        tag = b[off:off + 4]
        if tag in (b'ISGN', b'ISG1'):
            base = off + 8
            cnt = struct.unpack_from('<I', b, base)[0]
            esz = 24 if tag == b'ISGN' else 32
            out = []
            for k in range(cnt):
                e = base + 8 + esz * k
                if tag == b'ISGN':
                    no, idx, _st, _ct, reg = struct.unpack_from('<IIIII', b, e)
                    mask = b[e + 20]
                else:
                    _sn, no, idx, _st, _ct, reg = struct.unpack_from('<IIIIII', b, e)
                    mask = b[e + 24]
                out.append((b[base + no:b.index(b'\0', base + no)].decode(), idx, reg, mask))
            return out
    return None


def decl_elements(decl):
    """the vertex declaration string -> [(semantic, index, name)] of the elements after the base ones"""
    t = decl.split('.')
    names = [t[0]] + [tok[1:] for tok in t[1:]]      # token = <format of the previous element><name of the next>
    out = []
    for n in names:
        if not n or n in BASE_NAMES:
            continue
        tg = n[-2:]
        if tg[0] == 't' and re.fullmatch(r'[0-9a-f]', tg[1]):
            out.append(('TEXCOORD', int(tg[1], 16), n))
        elif tg[0] == 'c' and tg[1].isdigit():
            out.append(('COLOR', int(tg[1]), n))
        else:
            out.append((None, None, n))
    return out


def layout_from_signature(decl, sig):
    """elements of the layer record in declaration order, with sizes from the VS input signature `sig` ([(semantic, index, register, mask)])"""
    comps = {(nm, idx): bin(mask).count('1') for nm, idx, _reg, mask in sig}
    els, off = [], 0
    for sem, idx, _name in decl_elements(decl):
        c = comps.get((sem, idx), 0)
        if sem == 'TEXCOORD' and idx in F32_TEXCOORDS:
            fmt, sz = 'f32', 4 * c
        else:
            fmt, sz = 'u8x4', 4
        els.append({'sem': sem, 'idx': idx, 'comps': c, 'fmt': fmt, 'bytes': sz, 'offset': off})
        off += sz
    return els, off


def technique_supported(elements):
    """True when the lit technique reads only TEXCOORD3, 4, 5, 6, 9 (each with at least one component)"""
    return bool(elements) and all(e['sem'] == 'TEXCOORD' and e['idx'] in SUPPORTED_TEXCOORDS and e['bytes'] > 0 for e in elements)


def extract_techset(tdir, ts):
    """layout of the first lit (`lmap_`) technique of a techset in the techsets dump dir `tdir`, or None"""
    txt = os.path.join(tdir, ts + '.techset.txt')
    if not os.path.isfile(txt):
        return None
    lines = [l.split(': ', 1) for l in open(txt, encoding='utf8', errors='replace').read().splitlines() if ': ' in l]
    for n in dict.fromkeys(b for _a, b in lines if b.startswith('lmap_')):
        tp = os.path.join(tdir, n + '.technique')
        if not os.path.isfile(tp):
            continue
        s = [x.decode() for x in re.findall(rb'[\x20-\x7e]{3,}', open(tp, 'rb').read())]
        hs = [x for x in s if re.fullmatch(r'[0-9a-f]{16}', x)]
        dec = [x for x in s if x.startswith('pp.')]
        if not hs or not dec:
            continue
        vs = os.path.join(tdir, 'vs', hs[0] + '.cso')
        if not os.path.isfile(vs):
            continue
        sig = isgn(vs)
        if sig is None:
            continue
        els, stride = layout_from_signature(dec[0], sig)
        return {'technique': n, 'vs': hs[0], 'ps': hs[-1], 'decl': dec[0], 'stride': stride, 'supported': technique_supported(els), 'elements': els}
    return None


def extract_zone(dump_root, zone):
    """(materials {name: techset}, techsets {techset: layout}, unresolved [techset]) of the `*` materials of one zone dump"""
    mdir = os.path.join(dump_root, zone, 'materials')
    tdir = os.path.join(dump_root, 'techsets_' + zone, 'techsets')
    mats, tss, unresolved = {}, {}, []
    for f in sorted(os.listdir(mdir)):
        if not (f.startswith('_') and f.endswith('.json')):
            continue
        j = json.load(open(os.path.join(mdir, f), encoding='utf8'))
        ts = j.get('techniqueSet->name') or ''
        if not ts:
            continue
        mats['*' + f[1:-5]] = ts
        if ts not in tss and ts not in unresolved:
            lay = extract_techset(tdir, ts)
            if lay is None:
                unresolved.append(ts)
            else:
                tss[ts] = lay
    return mats, tss, unresolved


def build_table(dump_root, zones):
    table = {'version': VERSION, 'techsets': {}, 'materials': {}, 'unresolved': {}}
    for z in zones:
        mats, tss, unresolved = extract_zone(dump_root, z)
        table['materials'][z] = dict(sorted(mats.items()))
        for ts, lay in tss.items():
            old = table['techsets'].get(ts)
            if old is not None and {k: v for k, v in old.items() if k != 'technique'} != {k: v for k, v in lay.items() if k != 'technique'}:   # the technique file name carries a zone hash
                raise SystemExit('techset %s has two different layouts (zone %s)' % (ts, z))
            table['techsets'][ts] = lay
        if unresolved:
            table['unresolved'][z] = unresolved
    table['techsets'] = dict(sorted(table['techsets'].items()))
    return table


# ------------------------------------------------------------------------------------------- reading the shipped table
_TABLE = {}


def load_table(path=None):
    path = path or TABLE_PATH
    if path not in _TABLE:
        _TABLE[path] = json.load(open(path, encoding='utf8'))
    return _TABLE[path]


def techset_layout(techset, table=None):
    return (table or load_table())['techsets'].get(techset)


def material_layout(name, zone=None, table=None):
    """layout of a `*` material (`*387n_86n_354n_362n`) or None. A name is map-local: with `zone` that zone's material, without it the
    layout every zone that holds the name agrees on (None when none holds it or they disagree)."""
    t = table or load_table()
    zs = [zone] if zone else sorted(t['materials'])
    found = []
    for z in zs:
        ts = t['materials'].get(z, {}).get(name)
        if ts and ts in t['techsets']:
            found.append(t['techsets'][ts])
    if not found or any(f != found[0] for f in found[1:]):
        return None
    return found[0]


def encode_rotation(m00, m01, m10, m11):
    """2 x 2 UV rotation as unorm8x4: the vertex shader decodes m = byte / 127 - 1, so byte = round((m + 1) * 127): +1 -> 254, 0 -> 127, -1 -> 0"""
    return bytes(max(0, min(255, int(round((m + 1.0) * 127.0)))) for m in (m00, m01, m10, m11))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dump-root', default=DEFAULT_DUMP_ROOT)
    ap.add_argument('--zones', default='cp_disco,cp_final')
    ap.add_argument('--out', default=TABLE_PATH)
    ap.add_argument('--check', action='store_true', help='re-extract and compare with --out instead of writing it')
    a = ap.parse_args(argv)
    table = build_table(a.dump_root, [z for z in a.zones.split(',') if z])
    text = json.dumps(table, separators=(',', ':'), sort_keys=True) + '\n'
    if a.check:
        same = open(a.out, encoding='utf8').read() == text
        print('layer layouts: %s' % ('identical' if same else 'DIFFERENT'))
        return 0 if same else 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf8', newline='\n').write(text)
    for z, m in table['materials'].items():
        sup = sum(1 for ts in m.values() if table['techsets'].get(ts, {}).get('supported'))
        print('%s: %d materials, %d supported' % (z, len(m), sup))
    print('%d techsets, unresolved %s -> %s' % (len(table['techsets']), {z: len(v) for z, v in table['unresolved'].items()}, a.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
