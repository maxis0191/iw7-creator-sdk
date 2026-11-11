"""Assemble zonetool/<map>/ (hardlinks: generated world first, then stock dumps) and zone_source/<map>.csv.

usage: assemble.py <work> <map> <level script> <dump> [<dump> ...] [--incremental]

--incremental keeps the stock links of the previous assembly when it was made from the same dumps (recorded in
zonetool/<map>/.iwz_assemble.json): only the generated world files are linked again, and a stock file that an earlier
generated file had shadowed is linked back. Without the record, or with other dumps, it assembles everything.
"""
import json as _json, os, sys
argv = [a for a in sys.argv[1:] if a != '--incremental']
incremental = '--incremental' in sys.argv[1:]
work, mapname, script = argv[0], argv[1], argv[2]
dumps = argv[3:]
dst = os.path.join(work, 'zonetool', mapname)
gen = os.path.join(work, 'dump', mapname)
record_path = os.path.join(dst, '.iwz_assemble.json')
record = None
if incremental and os.path.isfile(record_path):
    record = _json.load(open(record_path))
    if record.get('dumps') != [os.path.abspath(d) for d in dumps]:
        print('incremental: the dumps differ from the recorded assembly; assembling everything')
        record = None
if incremental and record is None and os.path.isdir(dst):
    import shutil as _sh
    _sh.rmtree(dst)
os.makedirs(dst, exist_ok=True)
n = 0


def stock_source(rel):
    for d in dumps:
        p = os.path.join(d, rel)
        if os.path.isfile(p):
            return p
    return None


generated = []
for root, _, files in os.walk(gen):
    for f in files:
        generated.append(os.path.relpath(os.path.join(root, f), gen))
if record is not None:
    # take back what the previous generated world put here; the stock file it shadowed (if any) comes back
    now = set(generated)
    restored = 0
    for rel in record.get('generated', []):
        d = os.path.join(dst, rel)
        if os.path.lexists(d):
            os.remove(d)
        if rel not in now:
            s = stock_source(rel)
            if s:
                os.link(s, d); restored += 1
    for rel in generated:
        d = os.path.join(dst, rel)
        if os.path.lexists(d):
            os.remove(d)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        os.link(os.path.join(gen, rel), d); n += 1
    print('incremental: %d generated files linked, %d stock files restored, stock links kept' % (n, restored))
else:
    for src in [gen] + dumps:
        for root, _, files in os.walk(src):
            rel = os.path.relpath(root, src)
            for f in files:
                d = os.path.join(dst, rel, f)
                if os.path.exists(d):
                    if src == gen: os.remove(d)
                    else: continue
                os.makedirs(os.path.dirname(d), exist_ok=True)
                os.link(os.path.join(root, f), d); n += 1
_json.dump({'dumps': [os.path.abspath(d) for d in dumps], 'generated': generated}, open(record_path, 'w'))
sp = os.path.join(dst, 'scripts', 'cp', 'maps', mapname, mapname + '.gsc')
os.makedirs(os.path.dirname(sp), exist_ok=True)
if os.path.exists(sp): os.remove(sp)
open(sp, 'w', newline='\n').write(open(script).read())
bsp = 'maps/cp/%s.d3dbsp' % mapname
rows = ['// %s: generated world (iwzmap) + stock IW7 materials' % mapname]
# world assets go last (stock order), after every material/image/model they reference
world_rows = ['%s,%s' % (t, bsp) for t in ['com_map', 'navmesh', 'fx_map']] + ['gfx_map_trzone,' + mapname] + \
    ['%s,%s' % (t, bsp) for t in ['gfx_map', 'map_ents', 'glass_map', 'aipaths', 'col_map']]
rows.append('rawfile,scripts/cp/maps/%s/%s.gsc' % (mapname, mapname))
# CP gameplay scripts live in the map zones (stock map + its patch): carry them all
seen = set()
for d in dumps:
    csv = os.path.join(d, os.path.basename(d) + '.csv')
    if not os.path.isfile(csv): continue
    for ln in open(csv, errors='replace'):
        parts = ln.strip().split(',')
        if len(parts) == 2 and parts[0] == 'scriptfile' and parts[1] not in seen:
            seen.add(parts[1]); rows.append('scriptfile,' + parts[1])
# tables and rawfiles named after the stock map: carry them, plus a copy under the new map name
import shutil
for d in dumps:
    csv = os.path.join(d, os.path.basename(d) + '.csv')
    if not os.path.isfile(csv): continue
    for ln in open(csv, errors='replace'):
        parts = ln.strip().split(',')
        if len(parts) == 2 and parts[0] == 'rawfile' and parts[1] not in seen and not parts[1].endswith('.gsc') and parts[1] != 'cp_zmb' and os.path.isfile(os.path.join(dst, parts[1])):
            seen.add(parts[1]); rows.append('rawfile,' + parts[1]); continue
        if len(parts) != 2 or parts[0] != 'stringtable' or parts[1] in seen: continue
        seen.add(parts[1]); rows.append('stringtable,' + parts[1])
        if 'cp_zmb' in parts[1]:
            src = os.path.join(dst, parts[1]); new = parts[1].replace('cp_zmb', mapname)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(os.path.join(dst, new)), exist_ok=True)
                if not os.path.exists(os.path.join(dst, new)): shutil.copyfile(src, os.path.join(dst, new))
                rows.append('stringtable,' + new)
rows += ['rumble,%s' % r for r in ('ac130_40mm_fire', 'ground_pound_land', 'ground_pound_start', 'minigun_rumble', 'zmb_escape_velocity_rumble')]
ncs = os.path.join(dst, 'netconststrings')
if os.path.isdir(ncs):
    rows += ['netconststrings,%s' % f[:-5] for f in sorted(os.listdir(ncs)) if f.endswith('_level.json')]

# assets named in the level netconststrings: the client resolves every one of them when it joins
import json, collections
stock_types = collections.defaultdict(list)   # name -> [(type, is_reference)]
for d in dumps:
    csvp = os.path.join(d, os.path.basename(d) + '.csv')
    if not os.path.isfile(csvp): continue
    for ln in open(csvp, errors='replace'):
        q = ln.strip().split(',')
        if len(q) == 2: stock_types[q[1]].append((q[0], False))
        elif len(q) == 3 and q[1] == '': stock_types[q[2]].append((q[0], True))
SKIP = {'scriptable', 'physicsasset', 'streaminginfo', 'impactfx', 'gfx_map_trzone', 'image'}
ncs_dir = os.path.join(dst, 'netconststrings')
added = set()
if os.path.isdir(ncs_dir):
    for f in sorted(os.listdir(ncs_dir)):
        if not f.endswith('_level.json'): continue
        for name in (json.load(open(os.path.join(ncs_dir, f))).get('stringList') or []):
            kinds = stock_types.get(name, [])
            real = [t for t, ref in kinds if not ref and t not in SKIP]
            refs = [t for t, ref in kinds if ref and t not in SKIP]
            for t in (real[:1] or refs[:1]):
                key = (t, name)
                if key in added or ('%s,%s' % key) in rows: continue
                added.add(key)
                rows.append(('%s,%s' % key) if real else ('%s,,%s' % key))
print('ncs assets', len(added))

# per-map assets looked up by map name: net const baseline, visions, impact fx, streaming info
def copy_renamed(rel, newrel):
    src = os.path.join(dst, rel); new = os.path.join(dst, newrel)
    if not os.path.isfile(src): return False
    os.makedirs(os.path.dirname(new), exist_ok=True)
    if os.path.exists(new): os.remove(new)
    shutil.copyfile(src, new); return True
for rel in ['cp/constbaselines/bl_pc_cp_zmb_zombie.bin', 'vision/cp_zmb.vision', 'vision/last_stand_cp_zmb.vision']:
    new = rel.replace('cp_zmb', mapname)
    if copy_renamed(rel, new) and ('rawfile,' + new) not in rows: rows.append('rawfile,' + new)
if copy_renamed('impactfx/cp_zmb.json', 'impactfx/%s.json' % mapname): rows.append('impactfx,' + mapname)
si = os.path.join(dst, 'streaming_info', 'cp_zmb')
if os.path.isfile(si):
    data = open(si, 'rb').read(); old = b'\x06\x01cp_zmb\x00'
    if data.count(old) == 1:
        open(os.path.join(dst, 'streaming_info', mapname), 'wb').write(data.replace(old, b'\x06\x01' + mapname.encode() + b'\x00'))
        rows.append('streaminginfo,' + mapname)

# full gameplay parity with the stock map: every non-world asset of the stock zone and its patch
if os.environ.get('IWZ_FULL_STOCK', '1') == '1':
    WORLD = {'com_map', 'navmesh', 'fx_map', 'gfx_map', 'map_ents', 'glass_map', 'aipaths', 'col_map', 'gfx_map_trzone',
             'streaminginfo', 'impactfx', 'soundbank', 'netconststrings'}
    have = set(rows)
    for d in dumps:
        csvp = os.path.join(d, os.path.basename(d) + '.csv')
        if not os.path.isfile(csvp) or os.path.basename(d).startswith('techsets'): continue
        for ln in open(csvp, errors='replace'):
            q = ln.strip().split(',')
            if len(q) == 2 and q[0] not in WORLD and q[1] != 'cp_zmb':
                if q[0] == 'rawfile' and q[1].endswith('.gsc'): continue
                r = '%s,%s' % (q[0], q[1])
                if r not in have and ('%s,,%s' % (q[0], q[1])) not in have: have.add(r); rows.append(r)
            elif len(q) == 3 and q[1] == '' and q[0] not in WORLD:
                r = '%s,,%s' % (q[0], q[2])
                if r not in have and ('%s,%s' % (q[0], q[2])) not in have: have.add(r); rows.append(r)
    print('full stock rows', len(rows))
# map-owned content (tables and raw files the engine looks up by map name): content/<map>/<asset path>
content = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content', mapname)
for root, _, files in os.walk(content):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), content).replace(os.sep, '/')
        d = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d): os.remove(d)
        open(d, 'wb').write(open(os.path.join(root, f), 'rb').read())
        r = ('stringtable,' if rel.endswith('.csv') else 'rawfile,') + rel
        if r not in rows: rows.append(r)
        print('content', r)
os.makedirs(os.path.join(work, 'zone_source'), exist_ok=True)
rows += world_rows
open(os.path.join(work, 'zone_source', mapname + '.csv'), 'w', newline='\n').write('\n'.join(rows) + '\n')
print('linked', n, 'files')
