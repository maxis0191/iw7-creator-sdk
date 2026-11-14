"""Deadeye Dewdrops in the game's own machine: the cp_disco scriptable zm_perk_machine_deadeye_sign on a spare template
perk scriptable instance of this map.

The template map (cp_zmb) has ten placed perk scriptables; scenegen.py relocates five of them (scriptables.txt) and the
map compiler parks the rest. The stock Deadeye machine code (init_deadeye_machines_func, stock script 3421) finds its
machine with getentitylessscriptablearrayinradius( "perk_machine_deadeye_sign", "targetname" ) and drives the part
"perk_sign" through "off" and "powered_on" (models cp_disco_perk_dewdrops_off / cp_disco_perk_dewdrops). This step,
run after assemble.py and kit_import.py (which brings the two Dewdrops xmodels) and before -buildzone:
  1. checks that the dumped Deadeye scriptable has exactly the structure of the donor template scriptable (same token
     stream once strings and dump-time pointer values are set aside: same parts, states, events, models count), and
     that every asset it names (its models) is in the zone csv;
  2. writes zonetool/<map>/scriptable/zm_perk_machine_deadeye_sign and the csv row scriptable,zm_perk_machine_deadeye_sign;
  3. in the compiled map ents (maps/cp/<map>.d3dbsp.ents.data, ZoneTool assetmanager stream) re-points the donor's
     relocated instance: its def asset token `07 01 zm_perk_machine_<donor>_sign 00` becomes the Deadeye def and its
     targetname string token `06 01 perk_machine_<donor>_sign 00` becomes perk_machine_deadeye_sign. Token streams
     refer to earlier entries by entry index (OFFSET tokens), never by byte offset, so a string of another length is
     safe (the same rule kit_import.py's drop_scriptable rests on). The local client contexts of the instance are
     OFFSET tokens to the same def entry and follow it.
Files that are hardlinks into a dump are removed before writing (never written through).

The donor instance must be relocated by scenegen (scriptables.txt line `perk_machine_<donor>_sign 0 x y z yaw`):
a parked instance has an empty targetname and is refused.

usage: add_deadeye_machine.py <zone csv> <zonetool map dir> <map> --scriptable <cp_disco dump>/scriptable/zm_perk_machine_deadeye_sign
       [--donor blue_bolts] [--dry-run] [--report out.json]
Exit 1 on any check that fails (nothing written then).
"""
import argparse, json, os, re, struct, sys

TARGET_DEF = 'zm_perk_machine_deadeye_sign'
TARGET_TN = 'perk_machine_deadeye_sign'
STR_TOKEN = re.compile(rb'([\x06\x07])\x01([\x20-\x7e]+)\x00')
WORLD_FIRST = 'com_map,'


def tokens(data):
    """(kind, name) of every string (06) and asset (07) token of an assetmanager dump"""
    return [(m.group(1)[0], m.group(2).decode()) for m in STR_TOKEN.finditer(data)]


def skeleton(data):
    return STR_TOKEN.sub(lambda m: m.group(1) + b'\x01S\x00', data)


def is_ptr(b8):
    """a dump-time heap pointer written inside a raw struct (the reader replaces it): 2^32 .. 2^47"""
    v = struct.unpack('<Q', b8)[0]
    return (1 << 32) <= v < (1 << 47)


def same_structure(a, b):
    """True when two scriptable dumps differ only in their strings and in dump-time pointer values"""
    sa, sb = skeleton(a), skeleton(b)
    if len(sa) != len(sb):
        return False, 'token stream lengths differ (%d / %d bytes without strings)' % (len(sa), len(sb))
    for i in range(len(sa)):
        if sa[i] == sb[i]:
            continue
        if not any(k >= 0 and k + 8 <= len(sa) and is_ptr(sa[k:k + 8]) and is_ptr(sb[k:k + 8]) for k in range(i - 7, i + 1)):
            return False, 'byte %d differs outside a pointer value (%s / %s)' % (i, sa[max(0, i - 8):i + 8].hex(' '), sb[max(0, i - 8):i + 8].hex(' '))
    return True, 'same structure'


def write_new(path, data):
    if os.path.exists(path):
        os.remove(path)                        # a hardlink into a dump: never write through it
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('csv'); ap.add_argument('root'); ap.add_argument('map')
    ap.add_argument('--scriptable', required=True, help='cp_disco dump: scriptable/zm_perk_machine_deadeye_sign')
    ap.add_argument('--donor', default='blue_bolts', help='spare template perk scriptable (zm_perk_machine_<donor>_sign)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--report', default='')
    a = ap.parse_args(argv)

    donor_def = 'zm_perk_machine_%s_sign' % a.donor
    donor_tn = 'perk_machine_%s_sign' % a.donor
    rep = {'donor': donor_def, 'errors': []}
    err = rep['errors']

    # 1. the Deadeye scriptable against the donor
    dead = open(a.scriptable, 'rb').read()
    donor_path = os.path.join(a.root, 'scriptable', donor_def)
    donor = open(donor_path, 'rb').read() if os.path.isfile(donor_path) else None
    toks = tokens(dead)
    rep['deadeyeTokens'] = ['%s:%s' % ('str' if k == 6 else 'asset', n) for k, n in toks]
    if not toks or toks[0] != (6, TARGET_DEF):
        err.append('%s does not start with its name token (%s)' % (a.scriptable, toks[:1]))
    if donor is None:
        err.append('donor scriptable missing: %s' % donor_path)
    else:
        ok, why = same_structure(donor, dead)
        rep['structure'] = why
        if not ok:
            err.append('Deadeye scriptable is not shaped like %s: %s' % (donor_def, why))
    lines = open(a.csv).read().splitlines()
    rows = set(lines)
    assets = sorted(set(n for k, n in toks if k == 7))
    rep['assets'] = assets
    for n in assets:
        if n == TARGET_DEF:
            continue
        if not any(r.endswith(',' + n) and r.split(',')[0] in ('xmodel', 'scriptable', 'vfx', 'xanim', 'sound', 'material')
                   for r in rows):
            err.append('asset %s of the Deadeye scriptable is not in the zone csv (kit_import --models cp_disco:%s first)' % (n, n))

    # 2./3. the compiled map ents
    ents = os.path.join(a.root, 'maps', 'cp', a.map + '.d3dbsp.ents.data')
    data = open(ents, 'rb').read()
    def_tok = b'\x07\x01' + donor_def.encode() + b'\x00'
    tn_tok = b'\x06\x01' + donor_tn.encode() + b'\x00'
    ctx = rb'(?:\x07\x00|\x09.{8})\x07\x00\x08\x00'           # a local client context: def (OFFSET or null), no model, no event buffer
    inst = re.compile(re.escape(def_tok) + rb'\x07\x00\x08\x00' + ctx + ctx + rb'(' + re.escape(tn_tok) + rb'|\x09.{8})', re.S)
    hits = list(inst.finditer(data))
    rep['donorInstances'] = len(hits)
    if data.count(def_tok) != 1 or len(hits) != 1:
        err.append('map ents: expected one instance of %s in the known layout, found %d def tokens / %d instances'
                   % (donor_def, data.count(def_tok), len(hits)))
    elif not hits[0].group(1).startswith(b'\x06'):
        err.append('map ents: the %s instance is parked (no targetname): relocate it in scriptables.txt (scenegen) first' % donor_def)
    if (b'\x07\x01' + TARGET_DEF.encode() + b'\x00') in data:
        err.append('map ents already name %s' % TARGET_DEF)

    if err:
        print('add_deadeye_machine: FAILED\n  ' + '\n  '.join(err))
        if a.report:
            json.dump(rep, open(a.report, 'w'), indent=1)
        return 1

    m = hits[0]
    seg = m.group(0)
    new_seg = seg.replace(def_tok, b'\x07\x01' + TARGET_DEF.encode() + b'\x00', 1)
    new_seg = new_seg[:len(new_seg) - len(tn_tok)] + b'\x06\x01' + TARGET_TN.encode() + b'\x00'
    new = data[:m.start()] + new_seg + data[m.end():]
    rep['entsOffset'] = m.start()
    rep['entsBytes'] = [len(data), len(new)]
    row = 'scriptable,' + TARGET_DEF
    if not a.dry_run:
        write_new(os.path.join(a.root, 'scriptable', TARGET_DEF), dead)
        write_new(ents, new)
        if row not in rows:
            at = next((i for i, l in enumerate(lines) if l.startswith(WORLD_FIRST)), len(lines))
            lines[at:at] = [row]
            open(a.csv, 'w', newline='\n').write('\n'.join(lines) + '\n')
    rep['written'] = not a.dry_run
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1)
    print('add_deadeye_machine: %s instance %s -> %s (targetname %s), models %s, ents %d -> %d bytes%s'
          % (rep['structure'], donor_def, TARGET_DEF, TARGET_TN, ','.join(n for n in assets if n != TARGET_DEF),
             len(data), len(new), ' (dry run)' if a.dry_run else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
