"""Put the stock perk sounds into the map's own sound bank (perk module, after add_perks.py and add_audio.py, before buildzone).

A usermap loads its own bank (<map>.sabl / <map>.sabs, ZoneTool soundbank asset <map>.all) and the always-loaded
banks (common_cp...), not cp_zmb's or cp_disco's: the stock perk code (scripts\\cp\\zombies\\zombies_perk_machines.gsc)
then finds no mus_zmb_<perk>_attract / _purchase (soundexists 0 in game) and stays silent. This step copies the stock
alias rows unchanged (channel, curves, distances, duck: the stock ones) and their audio, read from the stock sound
asset banks, into the map's bank:

- rows: <asset root>/sound/<bank>.perks.aliases.csv, listed in the bank json's "aliases" (ZoneTool sound_bank.cpp
  aliases::parse reads every listed csv in order); the audio module's own csv is left as it is;
- audio: <asset root>/sound_assets/<File>.flac, the stock bank entry wrapped as a FLAC file (the container ZoneTool's
  flac::dump writes and flac::parse reads back to the same bytes). A primed alias needs its FULL stream (the .sabs
  entry): ZoneTool writes it to <map>.sabs and cuts the loaded head for <map>.sabl itself (flac::get_prime_size); the
  .sabl entry of a primed alias is only that head and is refused here;
- ducks the rows name (zmb_perk_machine_stinger) are copied from the template dump's sound/ducks when the asset root
  lacks them (aliases::parse fails the build on a missing duck);
- no bank yet (built without the audio module): soundbank/<bank>.json is created with empty definition tables (as
  iwz_audio_bank.py writes them) and `soundbank,<bank>` goes before the first world row of the zone csv.

ZoneTool writes one .sabl/.sabs pair per bank ZONE name (sound_bank.cpp create_path), so a second "all" bank of the
same zone would overwrite the first: the rows go into the existing bank, never into a new one.

usage: add_perk_sounds.py <zone_source csv> <asset root (zonetool/<map>)> <map>
           --aliases <stock aliases.csv> [--aliases ...]      first table defining an alias wins
           --stock-bank <.sabl|.sabs> [--stock-bank ...]       stock sound asset banks holding the audio
           [--bank <name>] [--alias <extra stock alias> ...] [--only <alias> ...] [--check-only] [--report <json>]
Files in the asset root may be hardlinks into the dumps: a file is always removed before it is written.
"""
import argparse, csv, hashlib, json, os, struct, sys

# what the stock perk code and cp_iwz_perks.gsc play for the six stock perks of this map, and is in no always-loaded
# bank (common_cp holds perk_machine_deny, perk_machine_remove_perk, perk_purchase_foley_candy_box). Tuff Nuff's
# machine plays mus_zmb_tuffnuff_purchase as its attract sound (stock default of zombies_perk_machines.gsc
# init_perk_machines_func); mus_zmb_tuffnuff_attract is played by nothing, so it is not shipped (--alias adds it).
PERK_ALIASES = [
    'mus_zmb_upnatoms_attract', 'mus_zmb_upnatoms_purchase',            # Up N Atoms      perk_machine_revive
    'mus_zmb_tuffnuff_purchase',                                        # Tuff Nuff       perk_machine_tough
    'mus_zmb_racinstripes_attract', 'mus_zmb_racinstripes_purchase',    # Racin Stripes   perk_machine_run
    'mus_zmb_bangbangs_attract', 'mus_zmb_bangbangs_purchase',          # Bang Bangs      perk_machine_rat_a_tat
    'mus_zmb_quickies_attract', 'mus_zmb_quickies_purchase',            # Quickies        perk_machine_flash
    'mus_zmb_deadeye_attract', 'mus_zmb_deadeye_purchase',              # Deadeye Dewdrops perk_machine_deadeye (cp_disco)
    'power_buy_neon_vending_turn_on',                                   # machine power-on (cp_iwz_perks.gsc machine_power; cp_disco)
]
WORLD_TYPES = ('com_map', 'navmesh', 'fx_map', 'gfx_map_trzone', 'gfx_map', 'map_ents', 'glass_map', 'aipaths', 'col_map')
DEF_KEYS = ('sendEffectParams', 'ADSRSettings', 'AmbientDefs', 'AmbientEvents', 'AmbientElements', 'FilterDefs',
            'MixDefs', 'NPCAdsrZoneEntry', 'PLRAdsrZoneEntry', 'OccludeDefs', 'ReverbDefs', 'TimescaleEntrys',
            'ZoneDefs', 'Unks', 'FullOcclusionDefs', 'PlayerBreathStateDefs')
STREAMED = ('streamed', 'primed', 'hybrid_pcm')

# ---- stock sound asset banks (same layout as asset-bridge/iw7-audio/iw7_sab.py, ZoneTool sound_bank.cpp) ----------
MAGIC = 0x23585532
HEADER = struct.Struct('<8I3Q16s512sQQ64s8s3sII5s')
ENTRY = struct.Struct('<5IQiBBBHHBBBBB')
NAME_LEN = 128


def snd_hash_name(name):
    """engine hash of alias / asset file names (ZoneTool snd_hash_name)"""
    if not name:
        return 0
    h = 5381
    for ch in name.encode('latin-1', 'replace'):
        if 65 <= ch <= 90:
            ch += 32
        h = (65599 * h + ch) & 0xFFFFFFFF
    return h or 1


class Bank:
    def __init__(self, path):
        self.path, self.streamed = path, path.lower().endswith('.sabs')
        with open(path, 'rb') as f:
            v = HEADER.unpack(f.read(HEADER.size))
        if v[0] != MAGIC or v[2] != ENTRY.size:
            raise SystemExit('%s: not an IW7 sound asset bank' % path)
        count, self.entry_offset, self.name_offset = v[5], v[9], v[14]
        with open(path, 'rb') as f:
            f.seek(self.entry_offset)
            table = f.read(ENTRY.size * count)
            names = b''
            if self.name_offset:
                f.seek(self.name_offset)
                names = f.read(NAME_LEN * count)
        self.ids = {}
        for i in range(count):
            e = ENTRY.unpack_from(table, i * ENTRY.size)
            self.ids[e[0]] = {'id': e[0], 'size': e[1], 'seek': e[2], 'frames': e[3], 'pcm': e[4], 'offset': e[5],
                              'rate': e[6], 'channels': e[7], 'looping': e[8], 'format': e[9], 'block_kb': e[16],
                              'name': names[i * NAME_LEN:(i + 1) * NAME_LEN].split(b'\0')[0].decode('latin-1')}

    def read(self, e):
        with open(self.path, 'rb') as f:
            f.seek(e['offset'])
            return f.read(e['size'] + e['seek'] + e['pcm'])


def flac_container(e, data):
    """bank FLAC frames (+ seek table) -> FLAC file, as ZoneTool flac::dump writes it"""
    block = e['block_kb'] * 1024 if e['block_kb'] else 0x400
    rate, ch, total = e['rate'], e['channels'], e['frames']
    info = struct.pack('>HH', block, block) + b'\0' * 6
    info += bytes([(rate >> 12) & 0xFF, (rate >> 4) & 0xFF, (((ch - 1) << 1) | ((rate << 4) & 0xF0)) & 0xFF])
    info += bytes([((16 - 1) << 4) | ((total >> 32) & 0x0F), (total >> 24) & 0xFF, (total >> 16) & 0xFF,
                   (total >> 8) & 0xFF, total & 0xFF]) + b'\0' * 16
    seek = e['seek'] > 0
    out = b'fLaC' + bytes([0x00 if seek else 0x80]) + len(info).to_bytes(3, 'big') + info
    if seek:
        out += bytes([0x80 | 3]) + e['seek'].to_bytes(3, 'big')
    return out + data


def prime_size(frames):
    """ZoneTool flac::get_prime_size: the loaded head of a primed sound ends at FLAC frame 48 (max 128 KB)"""
    max_size = min(len(frames), 0x20000)
    for pos in range(1, max_size):
        if pos + 4 >= len(frames):
            break
        if frames[pos] == 0xFF and frames[pos + 1] == 0xF8 and frames[pos + 2] == frames[2] and frames[pos + 4] == 48:
            return pos
    return max_size


# ---- helpers --------------------------------------------------------------------------------------------------------
def write_new(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.lexists(path):
        os.remove(path)            # never write through a hardlink into a dump
    with open(path, 'wb') as f:
        f.write(data)


def load_tables(paths):
    header, rows, origin = None, {}, {}
    for p in paths:
        with open(p, newline='', encoding='utf-8', errors='replace') as f:
            t = list(csv.reader(f))
        if header is None:
            header = t[0]
        elif t[0] != header:
            raise SystemExit('%s: alias columns differ from %s' % (p, paths[0]))
        seen = {}
        for r in t[1:]:
            if len(r) == len(header):
                seen.setdefault(r[0], []).append(r)
        for k, v in seen.items():
            if k not in rows:
                rows[k], origin[k] = v, p
    return header, rows, origin


def bank_alias_names(root, sb):
    names = set()
    for rel in sb.get('aliases', []):
        p = os.path.join(root, *rel.split('/'))
        if os.path.exists(p):
            with open(p, newline='', encoding='utf-8', errors='replace') as f:
                names.update(r[0] for r in list(csv.reader(f))[1:] if r)
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('csv')
    ap.add_argument('root')
    ap.add_argument('map')
    ap.add_argument('--aliases', action='append', required=True)
    ap.add_argument('--stock-bank', action='append', required=True)
    ap.add_argument('--bank', default='')
    ap.add_argument('--alias', action='append', default=[], help='extra stock alias to carry')
    ap.add_argument('--only', action='append', default=[], help='carry only these aliases (instead of the perk list)')
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--report', default='')
    a = ap.parse_args(argv)
    root, bank = a.root, a.bank or a.map + '.all'
    want = list(dict.fromkeys((a.only or PERK_ALIASES) + a.alias))
    header, stock, origin = load_tables(a.aliases)
    col = {n: i for i, n in enumerate(header)}
    banks = [Bank(p) for p in a.stock_bank]

    sb_path = os.path.join(root, 'soundbank', bank + '.json')
    sb = json.load(open(sb_path)) if os.path.exists(sb_path) else None
    perks_rel = 'sound/%s.perks.aliases.csv' % bank
    have = bank_alias_names(root, {'aliases': [x for x in (sb or {}).get('aliases', []) if x != perks_rel]})

    errors, rows, audio, ducks, report = [], [], {}, set(), []
    for name in want:
        if name in have:
            report.append({'alias': name, 'skipped': 'already in the bank'})
            continue
        if name not in stock:
            errors.append('%s: in none of the alias tables %s' % (name, a.aliases))
            continue
        for r in stock[name]:
            r = list(r)
            kind, f = r[col['type']], r[col['File']]
            h = snd_hash_name(f)
            # a primed/streamed sound ships its full stream (a .sabs entry), a loaded one its .sabl entry
            src = next((b for b in banks if h in b.ids and b.streamed == (kind in STREAMED)), None)
            if not src:
                errors.append('%s: %s (%s) is in none of the %s banks given' % (name, f, kind, 'streamed' if kind in STREAMED else 'loaded'))
                continue
            e = src.ids[h]
            if e['format'] != 8:
                errors.append('%s: %s is not FLAC (format %d)' % (name, f, e['format']))
                continue
            data = src.read(e)
            check = 'none'
            if kind == 'primed':
                # the head ZoneTool will cut for <map>.sabl must be the stock loaded head byte for byte
                head = data[e['seek']:][:prime_size(data[e['seek']:e['seek'] + e['size']])]
                lb = next((b for b in banks if not b.streamed and h in b.ids), None)
                if lb:
                    stock_head = lb.read(lb.ids[h])
                    if stock_head != head:
                        errors.append('%s: computed primed head (%d bytes) differs from %s (%d bytes)' % (name, len(head), lb.path, len(stock_head)))
                    check = 'head == %s entry (%d bytes)' % (os.path.basename(lb.path), len(stock_head))
                e = dict(e, head=len(head))
            if '\\t' in f or '\\n' in f:
                errors.append('%s: File %s holds a sequence ZoneTool unescapes' % (name, f))
            if r[col['duck']]:
                ducks.add(r[col['duck']])
            audio[f] = (src, e, data)
            rows.append(r)
            report.append({'alias': name, 'table': origin[name], 'file': f, 'type': kind, 'channel': r[col['channel']],
                           'bank': src.path, 'seconds': round(e['frames'] / e['rate'], 3), 'channels': e['channels'],
                           'rate': e['rate'], 'stream_bytes': e['size'] + e['seek'],
                           'head_bytes': e.get('head', e['size'] + e['seek'] if kind == 'loaded' else 0),
                           'duck': r[col['duck']], 'head_check': check})
    duck_src = {}
    for d in sorted(ducks):
        if os.path.exists(os.path.join(root, 'sound', 'ducks', d + '.duk')):
            continue
        cand = [os.path.join(os.path.dirname(os.path.abspath(p)), 'ducks', d + '.duk') for p in a.aliases]
        hit = next((c for c in cand if os.path.exists(c)), None)
        if not hit:
            errors.append('duck %s: not in the asset root nor beside %s' % (d, a.aliases))
        duck_src[d] = hit

    loaded = sum(x['head_bytes'] for x in report if 'file' in x)
    streamed = sum(x['stream_bytes'] for x in report if 'file' in x and x['type'] in STREAMED)
    pad = lambda n: (n + 0xFFF) & ~0xFFF
    summary = {'bank': bank, 'rows': len(rows), 'aliases': report, 'ducks': sorted(ducks), 'errors': errors,
               'sabl_bytes_added': sum(pad(x['head_bytes']) + 16 + 16 + NAME_LEN + ENTRY.size for x in report if 'file' in x and x['head_bytes']),
               'sabs_bytes_added': sum(pad(x['stream_bytes']) + 16 + 16 + NAME_LEN + ENTRY.size for x in report if 'file' in x and x['type'] in STREAMED),
               'audio_bytes': {'loaded_heads': loaded, 'streams': streamed}}
    if errors or a.check_only:
        print(json.dumps(summary, indent=1))
        return 1 if errors else 0

    for f, (src, e, data) in audio.items():
        write_new(os.path.join(root, 'sound_assets', *f.split('\\')) + '.flac', flac_container(e, data))
    for d, hit in duck_src.items():
        write_new(os.path.join(root, 'sound', 'ducks', d + '.duk'), open(hit, 'rb').read())
    text = []
    w = csv.writer(_Sink(text))          # csv module defaults (CRLF), as iwz_audio_bank.py writes the audio module's table
    w.writerows([header] + rows)
    write_new(os.path.join(root, *perks_rel.split('/')), ''.join(text).encode('utf-8'))
    if sb is None:
        sb = {'name': bank, 'zone': a.map, 'gameLanguage': 'all', 'soundLanguage': 'all', 'aliases': []}
        for k in DEF_KEYS:
            sb[k] = []
    if perks_rel not in sb['aliases']:
        sb['aliases'].append(perks_rel)
    write_new(sb_path, json.dumps(sb, indent=4).encode('utf-8'))

    with open(a.csv, 'rb') as fh:
        raw = fh.read().decode('ascii', 'replace')
    nl = '\r\n' if '\r\n' in raw else '\n'
    lines = raw.splitlines()
    row = 'soundbank,' + bank
    if row not in lines:
        at = next((i for i, l in enumerate(lines) if l.split(',', 1)[0] in WORLD_TYPES), len(lines))
        lines.insert(at, row)
        write_new(a.csv, (nl.join(lines) + nl).encode('ascii'))
        summary['zone_row'] = 'inserted %s at line %d' % (row, at + 1)
    else:
        summary['zone_row'] = 'present'
    summary['written'] = {'aliases_csv': perks_rel, 'bank_json': os.path.relpath(sb_path, root),
                          'flac': len(audio), 'ducks': sorted(duck_src)}
    if a.report:
        write_new(a.report, json.dumps(summary, indent=1).encode('utf-8'))
    print(json.dumps({k: v for k, v in summary.items() if k != 'aliases'}, indent=1))
    print('perk sounds: %d rows into %s (%d audio files, sabl +%d bytes, sabs +%d bytes)' % (
        len(rows), bank, len(audio), summary['sabl_bytes_added'], summary['sabs_bytes_added']))
    return 0


class _Sink:
    def __init__(self, out):
        self.out = out

    def write(self, s):
        self.out.append(s)


if __name__ == '__main__':
    sys.exit(main())
