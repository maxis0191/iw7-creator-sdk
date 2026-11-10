#!/usr/bin/env python3
"""World patch: change the placed props of a studio-made map by editing a copy of its render world file.

A patch is a small JSON file (schema iw7.worldpatch/1). It is resolved against a worldkit database
(iw7_world.py build) into a deterministic plan, the plan is written into a copy of the dump's .gfxmap
without changing the file's structure (only numbers inside existing records change), and the result is
re-parsed and compared with the source byte for byte outside the planned fields.

    python -B iw7_worldpatch.py new    --db <db> [--out patch.json]
    python -B iw7_worldpatch.py plan   --patch <patch.json> --db <db> [--out plan.json] [--json]
    python -B iw7_worldpatch.py apply  --patch <patch.json> --db <db> --dump <dump folder> --out <folder> [--json]
    python -B iw7_worldpatch.py verify --plan <plan.json> --dump <dump folder> --out <folder> [--json]

Operations (applied in the order written; selectors inside one operation are combined with "and"):

    {"op": "remove", "box": [x1, y1, z1, x2, y2, z2]}          props whose origin is inside the box
    {"op": "remove", "model": "zmb_bench_*"}                    props whose model name matches (fnmatch, case kept)
    {"op": "remove", "index": [12, 13]}                         props by record index
    {"op": "remove", ..., "collision": "remove"}                also take the props out of the collision file
    {"op": "restore", ...same selectors...}                     undo an earlier remove
    {"op": "move", "index": 12, "to": [x, y, z], "yaw": 90, "scale": 1.0}
                                                                one prop to a new origin; yaw (degrees, added about
                                                                the vertical axis) and scale are optional; a moved
                                                                prop is no longer removed

"remove" writes scale 0 into the prop's draw record: measured in the running game, that hides the prop
completely. Nothing else of the record changes, so a restore is exact. Standard library only.
"""
import argparse
import fnmatch
import hashlib
import json
import math
import os
import sqlite3
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iw7_dump as D  # noqa: E402

SCHEMA = 'iw7.worldpatch/1'
PLAN_SCHEMA = 'iw7.worldpatch-plan/1'
VERSION = '1.0.0'
OPS = ('remove', 'restore', 'move')


class PatchError(Exception):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def f32(x):
    """The value a 32-bit float field holds after x is written to it."""
    return struct.unpack('<f', struct.pack('<f', x))[0]


# ---------------------------------------------------------------- database

def open_db(path):
    if not os.path.isfile(path):
        raise PatchError('no database at %s (build one with iw7_world.py build)' % path)
    c = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'), uri=True)
    c.row_factory = sqlite3.Row
    return c


def db_meta(c):
    return {k: json.loads(v) for k, v in c.execute('select key, value from meta')}


def db_fingerprint(meta):
    """The render world file the database was built from: relative name and SHA-256."""
    for f in meta.get('files', []):
        if f.get('kind') == 'gfxmap':
            return f['name'], f['sha256'], f['bytes']
    raise PatchError('the database records no render world file')


def db_props(c):
    cols = 'i, model, x, y, z, scale, a00, a01, a02, a10, a11, a12, a20, a21, a22'
    return [dict(r) for r in c.execute('select %s from smodels order by i' % cols)]


# ---------------------------------------------------------------- patch file

def load_patch(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            p = json.load(f)
    except (OSError, ValueError) as e:
        raise PatchError('cannot read patch %s: %s' % (path, e))
    return check_patch(p)


def _vec(v, n, what):
    if not isinstance(v, list) or len(v) != n or not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                                         and math.isfinite(x) for x in v):
        raise PatchError('%s must be a list of %d finite numbers' % (what, n))
    return [float(x) for x in v]


def check_patch(p):
    if not isinstance(p, dict) or p.get('schema') != SCHEMA:
        raise PatchError('not a world patch: "schema" must be "%s"' % SCHEMA)
    if not isinstance(p.get('map'), str) or not p['map']:
        raise PatchError('"map" is missing')
    if not isinstance(p.get('fingerprint'), str) or len(p['fingerprint']) != 64:
        raise PatchError('"fingerprint" must be the SHA-256 of the render world file the patch was written against')
    ops = p.get('ops')
    if not isinstance(ops, list) or not ops:
        raise PatchError('"ops" must be a non-empty list')
    for n, op in enumerate(ops):
        where = 'ops[%d]' % n
        if not isinstance(op, dict) or op.get('op') not in OPS:
            raise PatchError('%s: "op" must be one of %s' % (where, ', '.join(OPS)))
        known = {'op', 'box', 'model', 'index', 'why'} | ({'to', 'yaw', 'scale'} if op['op'] == 'move' else set())
        if op['op'] != 'restore':
            known.add('collision')
        if op.get('collision', 'keep') not in ('keep', 'remove'):
            raise PatchError('%s.collision must be "keep" or "remove"' % where)
        extra = sorted(set(op) - known)
        if extra:
            raise PatchError('%s: unknown field %s' % (where, ', '.join(extra)))
        if 'box' in op:
            _vec(op['box'], 6, where + '.box')
        if 'model' in op and (not isinstance(op['model'], str) or not op['model']):
            raise PatchError('%s.model must be a name pattern' % where)
        if op['op'] == 'move':
            if not isinstance(op.get('index'), int) or isinstance(op.get('index'), bool) or 'box' in op or 'model' in op:
                raise PatchError('%s: move takes one "index" and no other selector' % where)
            _vec(op.get('to'), 3, where + '.to')
            for k in ('yaw', 'scale'):
                if k in op and (not isinstance(op[k], (int, float)) or isinstance(op[k], bool) or not math.isfinite(op[k])):
                    raise PatchError('%s.%s must be a number' % (where, k))
            if 'scale' in op and op['scale'] <= 0:
                raise PatchError('%s.scale must be above 0 (use remove to hide a prop)' % where)
        else:
            if not ({'box', 'model', 'index'} & set(op)):
                raise PatchError('%s: give at least one of "box", "model", "index"' % where)
            if 'index' in op:
                idx = op['index']
                if isinstance(idx, int) and not isinstance(idx, bool):
                    idx = [idx]
                if not isinstance(idx, list) or not idx or not all(isinstance(i, int) and not isinstance(i, bool) for i in idx):
                    raise PatchError('%s.index must be an index or a list of indexes' % where)
    return p


def _select(op, props):
    out = props
    if 'index' in op:
        idx = op['index'] if isinstance(op['index'], list) else [op['index']]
        bad = [i for i in idx if i < 0 or i >= len(props)]
        if bad:
            raise PatchError('index %d does not exist (the map has %d props)' % (bad[0], len(props)))
        want = set(idx)
        out = [p for p in out if p['i'] in want]
    if 'box' in op:
        b = op['box']
        lo = [min(b[k], b[k + 3]) for k in range(3)]
        hi = [max(b[k], b[k + 3]) for k in range(3)]
        out = [p for p in out if lo[0] <= p['x'] <= hi[0] and lo[1] <= p['y'] <= hi[1] and lo[2] <= p['z'] <= hi[2]]
    if 'model' in op:
        out = [p for p in out if fnmatch.fnmatchcase(p['model'], op['model'])]
    return out


def _yaw_axis(axis, deg):
    """Rows forward, left, up turned by deg about the world vertical; quarter turns are exact."""
    q = deg % 360.0
    exact = {0.0: (1.0, 0.0), 90.0: (0.0, 1.0), 180.0: (-1.0, 0.0), 270.0: (0.0, -1.0)}
    c, s = exact.get(q, (math.cos(math.radians(q)), math.sin(math.radians(q))))
    out = []
    for r in range(3):
        x, y, z = axis[3 * r:3 * r + 3]
        out += [c * x - s * y, s * x + c * y, z]
    return out


def resolve(patch, props, meta):
    """The plan: one entry per changed prop (index, model, where it stands in the dump, what changes), ascending
    index. Deterministic for a given patch and database."""
    name, sha, size = db_fingerprint(meta)
    if meta.get('map_name') != patch['map']:
        raise PatchError('the patch is for map "%s", the database holds "%s"' % (patch['map'], meta.get('map_name')))
    if sha != patch['fingerprint']:
        raise PatchError('the patch was written against another dump (patch %s..., database %s...)' % (
            patch['fingerprint'][:12], sha[:12]))
    state = {}   # index -> {'removed': bool, 'move': {...} or None, 'solid': bool}
    new = lambda: {'removed': False, 'move': None, 'solid': True}  # noqa: E731
    per_op = []
    for n, op in enumerate(patch['ops']):
        if op['op'] == 'move':
            sel = _select({'index': op['index']}, props)
            st = state.setdefault(sel[0]['i'], new())
            st['removed'] = False
            st['solid'] = op.get('collision', 'keep') != 'remove'
            st['move'] = {'to': op['to'], 'yaw': float(op.get('yaw', 0.0)), 'scale': op.get('scale')}
        else:
            sel = _select(op, props)
            for p in sel:
                st = state.setdefault(p['i'], new())
                st['removed'] = op['op'] == 'remove'
                st['solid'] = not (op['op'] == 'remove' and op.get('collision', 'keep') == 'remove')
        per_op.append({'op': op['op'], 'matched': len(sel)})
    changes = []
    for i in sorted(state):
        st, p = state[i], props[i]
        if p['i'] != i:
            raise PatchError('the database props are not numbered 0..n-1')
        ch = {'i': i, 'model': p['model'], 'at': [p['x'], p['y'], p['z']]}
        if st['move']:
            mv = st['move']
            ch['origin'] = [f32(v) for v in mv['to']]
            if mv['yaw'] % 360.0:
                ch['axis'] = [f32(v) for v in _yaw_axis([p['a%d%d' % (r, k)] for r in range(3) for k in range(3)], mv['yaw'])]
            if mv['scale'] is not None and f32(mv['scale']) != p['scale']:
                ch['scale'] = f32(mv['scale'])
        if st['removed']:
            if p['scale'] != 0.0:
                ch['scale'] = 0.0
        if not st['solid']:
            ch['collision'] = 'remove'
        if len(ch) > 3:
            changes.append(ch)
    removed = sum(1 for c in changes if c.get('scale') == 0.0)
    moved = sum(1 for c in changes if 'origin' in c)
    unsolid = sum(1 for c in changes if c.get('collision') == 'remove')
    plan = {'schema': PLAN_SCHEMA, 'tool': VERSION, 'map': patch['map'], 'file': name, 'fingerprint': sha, 'bytes': size,
            'props': len(props), 'ops': per_op,
            'counts': {'changed': len(changes), 'removed': removed, 'moved': moved, 'collision_removed': unsolid},
            'changes': changes}
    if unsolid:
        col = [f for f in meta.get('files', []) if f.get('name', '').endswith('.colmap')]
        if len(col) != 1:
            raise PatchError('the database records no collision file (.colmap) for this map')
        plan['collision'] = {'file': col[0]['name'], 'fingerprint': col[0]['sha256'], 'bytes': col[0]['bytes']}
    return plan


# ---------------------------------------------------------------- writing

def _records(buf, label):
    d = D.parse_gfxmap(buf, label)
    SD, SI = D.layout('GfxStaticModelDrawInst'), D.layout('GfxStaticModelInst')
    if d.draw_insts is None or d.smodel_insts is None:
        raise PatchError('%s holds no static model records' % label)
    return d, SD, SI


def edits_for(plan, buf, label='gfxmap'):
    """Byte edits (offset, bytes) for a plan, from the record positions of a parsed file."""
    d, SD, SI = _records(buf, label)
    n = d.draw_insts.count
    if n != plan['props']:
        raise PatchError('%s holds %d props, the plan was made for %d' % (label, n, plan['props']))
    edits = []
    for ch in plan['changes']:
        i = ch['i']
        if i < 0 or i >= n:
            raise PatchError('plan index %d is outside the file' % i)
        if d.smodel_models[i] != ch['model']:
            raise PatchError('prop %d is "%s" in the file, the plan expects "%s"' % (i, d.smodel_models[i], ch['model']))
        rec = d.draw_insts.off + SD.size * i
        if 'scale' in ch:
            edits.append((rec + SD.off('scale'), struct.pack('<f', ch['scale'])))
        if 'axis' in ch:
            edits.append((rec + SD.off('axis[0]'), struct.pack('<9f', *ch['axis'])))
        if 'origin' in ch:
            old = struct.unpack_from('<3f', buf, rec + SD.off('origin[0]'))
            edits.append((rec + SD.off('origin[0]'), struct.pack('<3f', *ch['origin'])))
            delta = [ch['origin'][k] - old[k] for k in range(3)]
            inst = d.smodel_insts.off + SI.size * i
            for fld in ('bounds.mid[0]', 'lightingOrigin[0]'):
                o = inst + SI.off(fld)
                cur = struct.unpack_from('<3f', buf, o)
                edits.append((o, struct.pack('<3f', *[cur[k] + delta[k] for k in range(3)])))
    edits.sort()
    for (a, da), (b, _) in zip(edits, edits[1:]):
        if a + len(da) > b:
            raise PatchError('two planned edits overlap at byte %d' % b)
    return edits


def verify_bytes(src, out, plan, label='patched gfxmap'):
    """Re-parse the patched file and compare it with the source. Returns the measured counts."""
    if len(src) != len(out):
        raise PatchError('%s has %d bytes, the source %d' % (label, len(out), len(src)))
    edits = edits_for(plan, src, 'source gfxmap')
    d2, SD, SI = _records(out, label)      # parses to the exact end or raises
    if d2.draw_insts.count != plan['props']:
        raise PatchError('%s holds %d props after patching' % (label, d2.draw_insts.count))
    pos, differing = 0, 0
    for off, data in edits:
        if src[pos:off] != out[pos:off]:
            raise PatchError('%s differs from the source outside the planned fields, before byte %d' % (label, off))
        if out[off:off + len(data)] != data:
            raise PatchError('%s does not hold the planned value at byte %d' % (label, off))
        if src[off:off + len(data)] != data:
            differing += 1
        pos = off + len(data)
    if src[pos:] != out[pos:]:
        raise PatchError('%s differs from the source outside the planned fields, after byte %d' % (label, pos))
    sc = SD.off('scale')
    hidden = sum(1 for i in range(d2.draw_insts.count)
                 if struct.unpack_from('<f', out, d2.draw_insts.off + SD.size * i + sc)[0] == 0.0)
    hidden_src = sum(1 for i in range(d2.draw_insts.count)
                     if struct.unpack_from('<f', src, d2.draw_insts.off + SD.size * i + sc)[0] == 0.0)
    return {'records_parsed': d2.draw_insts.count, 'edits': len(edits), 'edits_differing': differing,
            'scale_zero_after': hidden, 'scale_zero_before': hidden_src,
            'bytes_changed': sum(1 for off, data in edits for k in range(len(data)) if src[off + k] != data[k])}


# ---------------------------------------------------------------- collision file
#
# The collision file (.colmap) lists every placed prop again (model, origin, inverse scaled axis), in another order
# than the render world, and then the indexes of the props that collide. Removing a prop's collision takes its index
# out of that list; the prop's record stays.

CLIPMAP_SIZE = 384
CLIP_STATIC = 64
_CM = {'planeCount': 16, 'numStaticModels': 40, 'numCollision': 56}


def parse_colmap(buf, label='colmap'):
    s = D.Stream(buf, label)
    hdr = s.array(CLIPMAP_SIZE, 1, 'clipMap_t', required=True)
    s.string('name')
    count = {k: struct.unpack_from('<I', buf, hdr.off + o)[0] for k, o in _CM.items()}
    s.array(20, count['planeCount'], 'planes')
    sm = s.array(CLIP_STATIC, count['numStaticModels'], 'static models', required=True)
    names = [s.asset('static model') for _ in range(count['numStaticModels'])]
    rec = s.p
    if rec >= len(buf) or buf[rec] != D.T_ARRAY:
        s.fail('the collision model list is not stored as an array')
    col = s.array(4, count['numCollision'], 'collision model list', required=True)
    index = list(struct.unpack_from('<%di' % col.count, buf, col.off))
    if any(k < 0 or k >= sm.count for k in index):
        s.fail('the collision model list names a prop that does not exist')
    return {'hdr': hdr.off, 'sm': sm, 'names': names, 'list_rec': rec, 'list': col, 'index': index, 'end': s.p}


def clip_records_for(plan, gfx, cm_buf, cm):
    """The collision record of each prop whose collision the plan removes: same model, same origin, nearest axis."""
    d, SD, _ = _records(gfx, 'source gfxmap')
    by_model = {}
    for k, name in enumerate(cm['names']):
        by_model.setdefault(name, []).append(k)
    taken, out = set(), []
    for ch in plan['changes']:
        if ch.get('collision') != 'remove':
            continue
        rec = d.draw_insts.off + SD.size * ch['i']
        org = struct.unpack_from('<3f', gfx, rec + SD.off('origin[0]'))
        ax = struct.unpack_from('<9f', gfx, rec + SD.off('axis[0]'))
        sc = struct.unpack_from('<f', gfx, rec + SD.off('scale'))[0] or 1.0
        want = [ax[3 * j + i] / sc for i in range(3) for j in range(3)]
        best = None
        for k in by_model.get(ch['model'], ()):
            if k in taken:
                continue
            o = cm['sm'].off + CLIP_STATIC * k
            co = struct.unpack_from('<3f', cm_buf, o + 8)
            if max(abs(co[a] - org[a]) for a in range(3)) > 0.05:
                continue
            inv = struct.unpack_from('<9f', cm_buf, o + 20)
            err = max(abs(inv[a] - want[a]) for a in range(9))
            if best is None or err < best[0]:
                best = (err, k)
        if best is None:
            raise PatchError('prop %d (%s) has no record in the collision file' % (ch['i'], ch['model']))
        taken.add(best[1])
        out.append(best[1])
    return out


def patch_colmap(cm_buf, cm, remove):
    gone = set(remove)
    keep = [k for k in cm['index'] if k not in gone]
    lst = cm['list']
    out = bytearray(cm_buf[:cm['list_rec']])
    out += bytes([D.T_ARRAY, 1]) + struct.pack('<I', len(keep)) + struct.pack('<%di' % len(keep), *keep)
    out += cm_buf[lst.off + 4 * lst.count:]
    struct.pack_into('<I', out, cm['hdr'] + _CM['numCollision'], len(keep))
    return bytes(out), keep


def verify_colmap(src, out, remove, label='patched colmap'):
    a, b = parse_colmap(src, 'source colmap'), parse_colmap(out, label)
    gone = set(remove)
    if b['index'] != [k for k in a['index'] if k not in gone]:
        raise PatchError('%s: the collision list is not the source list without the removed props' % label)
    f = a['hdr'] + _CM['numCollision']
    if src[:f] != out[:f] or src[f + 4:a['list_rec']] != out[f + 4:b['list_rec']] or src[a['end']:] != out[b['end']:]:
        raise PatchError('%s differs from the source outside the collision list' % label)
    if b['names'] != a['names'] or b['sm'].count != a['sm'].count:
        raise PatchError('%s: the prop records changed' % label)
    return {'collision_before': len(a['index']), 'collision_after': len(b['index']), 'collision_removed': len(a['index']) - len(b['index'])}


def apply_collision(plan, dump, out_dir, gfx_src):
    rel = plan['collision']['file']
    path = find_gfxmap(dump, rel)
    with open(path, 'rb') as f:
        src = f.read()
    if hashlib.sha256(src).hexdigest() != plan['collision']['fingerprint']:
        raise PatchError('the collision file of the dump is not the one the database was built from')
    cm = parse_colmap(src, 'source colmap')
    remove = clip_records_for(plan, gfx_src, src, cm)
    out, _ = patch_colmap(src, cm, remove)
    measured = verify_colmap(src, out, remove)
    dst = os.path.join(out_dir, *rel.split('/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, dst)
    measured.update({'collision_out': dst, 'collision_sha256': hashlib.sha256(out).hexdigest()})
    return measured


def find_gfxmap(dump, rel):
    path = os.path.join(dump, *rel.split('/'))
    if not os.path.isfile(path):
        raise PatchError('the dump folder holds no %s' % rel)
    return path


def apply(plan, dump, out_dir):
    src_path = find_gfxmap(dump, plan['file'])
    with open(src_path, 'rb') as f:
        src = f.read()
    sha = hashlib.sha256(src).hexdigest()
    if sha != plan['fingerprint']:
        raise PatchError('the dump is not the one the plan was made for (file %s..., plan %s...)' % (
            sha[:12], plan['fingerprint'][:12]))
    out = bytearray(src)
    for off, data in edits_for(plan, src, 'source gfxmap'):
        out[off:off + len(data)] = data
    out = bytes(out)
    measured = verify_bytes(src, out, plan)
    dst = os.path.join(out_dir, *plan['file'].split('/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.abspath(dst) == os.path.abspath(src_path):
        raise PatchError('the output folder is the dump folder; choose another one')
    tmp = dst + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, dst)
    with open(os.path.join(out_dir, 'worldpatch-plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(plan, f, indent=1, sort_keys=True)
        f.write('\n')
    measured.update({'out': dst, 'sha256': hashlib.sha256(out).hexdigest(), 'source_sha256': sha})
    if plan.get('collision'):
        measured.update(apply_collision(plan, dump, out_dir, src))
    return measured


def verify(plan, dump, out_dir):
    src_path = find_gfxmap(dump, plan['file'])
    dst = find_gfxmap(out_dir, plan['file'])
    with open(src_path, 'rb') as f:
        src = f.read()
    with open(dst, 'rb') as f:
        out = f.read()
    if hashlib.sha256(src).hexdigest() != plan['fingerprint']:
        raise PatchError('the dump is not the one the plan was made for')
    measured = verify_bytes(src, out, plan)
    measured.update({'out': dst, 'sha256': hashlib.sha256(out).hexdigest()})
    return measured


# ---------------------------------------------------------------- command line

def _print(obj, as_json, lines):
    if as_json:
        print(json.dumps(obj, indent=1, sort_keys=True))
    else:
        for line in lines:
            print(line)


def _plan_lines(plan):
    c = plan['counts']
    lines = ['map %s, %d props, file %s (%s...)' % (plan['map'], plan['props'], plan['file'], plan['fingerprint'][:12])]
    for n, op in enumerate(plan['ops']):
        lines.append('  op %d %-7s matched %d' % (n, op['op'], op['matched']))
    lines.append('plan: %d props change (%d removed, %d moved)' % (c['changed'], c['removed'], c['moved']) +
                 (', collision removed for %d' % c['collision_removed'] if c.get('collision_removed') else ''))
    return lines


def cmd_new(args):
    c = open_db(args.db)
    meta = db_meta(c)
    name, sha, _ = db_fingerprint(meta)
    patch = {'schema': SCHEMA, 'map': meta.get('map_name'), 'fingerprint': sha,
             'ops': [{'op': 'remove', 'box': [0, 0, 0, 0, 0, 0], 'why': 'replace this with your own operations'}]}
    text = json.dumps(patch, indent=1) + '\n'
    if args.out:
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('wrote %s' % args.out)
    else:
        sys.stdout.write(text)


def _resolve(args):
    patch = load_patch(args.patch)
    c = open_db(args.db)
    return resolve(patch, db_props(c), db_meta(c))


def cmd_plan(args):
    plan = _resolve(args)
    if args.out:
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(plan, f, indent=1, sort_keys=True)
            f.write('\n')
    _print(plan if args.out is None else {k: v for k, v in plan.items() if k != 'changes'}, args.json, _plan_lines(plan))


def _measured_lines(m):
    return ['wrote %s' % m['out'],
            'verified: %d records parse, %d fields written (%d differ from the source, %d bytes), nothing else changed' % (
                m['records_parsed'], m['edits'], m['edits_differing'], m['bytes_changed']),
            'props with scale 0: %d before, %d after' % (m['scale_zero_before'], m['scale_zero_after']),
            'sha256 %s' % m['sha256']] + (
        ['wrote %s' % m['collision_out'],
         'collision: %d props collide before, %d after (%d removed)' % (
             m['collision_before'], m['collision_after'], m['collision_removed'])] if 'collision_out' in m else [])


def cmd_apply(args):
    plan = _resolve(args)
    m = apply(plan, args.dump, args.out)
    _print({'plan': {k: v for k, v in plan.items() if k != 'changes'}, 'measured': m}, args.json,
           _plan_lines(plan) + _measured_lines(m))


def cmd_verify(args):
    with open(args.plan, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    if plan.get('schema') != PLAN_SCHEMA:
        raise PatchError('%s is not a world patch plan' % args.plan)
    m = verify(plan, args.dump, args.out)
    _print({'measured': m}, args.json, _measured_lines(m))


def main(argv=None):
    ap = argparse.ArgumentParser(description='change the placed props of a map dump (see the module text)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('new', help='print an empty patch carrying the fingerprint of a database')
    p.add_argument('--db', required=True)
    p.add_argument('--out')
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser('plan', help='resolve a patch against a database')
    p.add_argument('--patch', required=True)
    p.add_argument('--db', required=True)
    p.add_argument('--out')
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser('apply', help='write the patched render world file and verify it')
    p.add_argument('--patch', required=True)
    p.add_argument('--db', required=True)
    p.add_argument('--dump', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_apply)
    p = sub.add_parser('verify', help='check a patched file against its plan and the dump')
    p.add_argument('--plan', required=True)
    p.add_argument('--dump', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--json', action='store_true')
    p.set_defaults(fn=cmd_verify)
    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except (PatchError, D.WorldError) as e:
        sys.stderr.write('error: %s\n' % e)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
