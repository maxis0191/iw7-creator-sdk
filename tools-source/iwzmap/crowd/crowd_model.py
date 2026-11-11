"""Crowd body models: a copy of a stock full-body model with no scriptable (package E2, Station Zero).

Why: the server links the scriptable of a model's asset (XModel + 0x58, `scriptableMoverDef`) into ONE server-wide pool
of 2,048 reserved scriptable parts, and ends the match when it is empty (server repository docs/ZOMBIE-CAPACITY.md,
section 7). The stock full-body zombie `police_officer_zombie` carries `zombie_cop_scriptable` (its dismemberment and
gore parts): 28 to 31 parts a body. A copy whose asset names no scriptable costs 0 parts by construction, so a crowd of
54 such bodies does not touch the pool. What the copy loses is exactly what the scriptable gave: dismemberment parts.

The copy is written in ZoneTool's dump format (`xmodel/<name>.xmb`, utils/io/assetmanager.hpp): an asset reference is
the byte 7 (DUMP_TYPE_ASSET), then 1 and a zero-ended name, or 0 for none; a string is 6, 1 and a zero-ended text.
The model's own name is the first string after the raw XModel struct; the scriptable is the reference that follows the
physics references and the physics LOD names (iw7/assets/xmodel.cpp, `parse`). Surfaces, materials and the physics asset
stay shared with the stock model (same asset names), so the copy adds one small asset to the zone.

usage:
  crowd_model.py make  <stock xmodel dir> <stock name> <new name> <out xmodel dir>
  crowd_model.py check <file.xmb>          prints the model name and its scriptable (or none)
"""
import os
import sys

ASSET, STRING = 7, 6


def _cstr(data, at):
    end = data.index(b'\0', at)
    return data[at:end].decode('ascii'), end + 1


def name_span(data, name):
    """(start, end) of the model's own name string record (6, 1, text, 0): the first such record holding `name`."""
    rec = bytes([STRING, 1]) + name.encode('ascii') + b'\0'
    i = data.find(rec)
    if i < 0:
        raise ValueError('the name %r is not a string record of this file' % name)
    return i, i + len(rec)


def scriptable_span(data):
    """(start, end, name) of the scriptable reference: the only asset reference whose name ends in 'scriptable', or the
    reference that a known stock scriptable name fills. Returns None when the model has none (a 7, 0 record)."""
    found = []
    i = 0
    while True:
        i = data.find(bytes([ASSET, 1]), i)
        if i < 0:
            break
        try:
            text, end = _cstr(data, i + 2)
        except ValueError:
            break
        if text and all(32 < ord(c) < 127 for c in text) and text.endswith('scriptable'):
            found.append((i, end, text))
        i += 2
    if len(found) > 1:
        raise ValueError('more than one scriptable reference: %s' % ', '.join(f[2] for f in found))
    return found[0] if found else None


def strip(data, old_name, new_name):
    """The bytes of the copy: renamed, scriptable reference replaced by 'none'."""
    s = scriptable_span(data)
    if s is None:
        raise ValueError('%s names no scriptable: a copy is not needed' % old_name)
    out = data[:s[0]] + bytes([ASSET, 0]) + data[s[1]:]
    a, b = name_span(out, old_name)
    out = out[:a] + bytes([STRING, 1]) + new_name.encode('ascii') + b'\0' + out[b:]
    return out, s[2]


def check(data):
    s = scriptable_span(data)
    return s[2] if s else None


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] not in ('make', 'check'):
        print(__doc__)
        return 2
    if argv[0] == 'check':
        data = open(argv[1], 'rb').read()
        print('%s: scriptable %s' % (os.path.basename(argv[1]), check(data) or 'none'))
        return 0
    src_dir, old, new, out_dir = argv[1:5]
    data = open(os.path.join(src_dir, old + '.xmb'), 'rb').read()
    out, removed = strip(data, old, new)
    if check(out) is not None:
        raise SystemExit('the copy still names a scriptable')
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, new + '.xmb')
    if os.path.exists(dst):
        os.remove(dst)          # may be a hard link into a stock dump: never write through it
    open(dst, 'wb').write(out)
    print('crowd model %s: copy of %s without %s (%d -> %d bytes)' % (dst, old, removed, len(data), len(out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
