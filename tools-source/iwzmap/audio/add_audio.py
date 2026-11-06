"""Add the Station Zero audio pieces to an assembled zone (after assemble.py, before buildzone).

    python add_audio.py <zone csv> <zone asset root> <map> [--bank-root <iwz_audio_bank.py --out dir>] [--model-root <dir>]

- copies cp_iwz_audio.gsc to <asset root>/scripts/cp/maps/<map>/<map>_audio.gsc (rawfile, called from the
  level script as scripts\\cp\\maps\\<map>\\<map>_audio::song_ee_init(...));
- copies the sound bank sources (sound/, soundbank/, sound_assets/) and the teddy bear model sources
  (xmodel/, xsurface/, materials/, images/) into the asset root when given;
- inserts, once, `rawfile,scripts/cp/maps/<map>/<map>_audio.gsc` after the level script row, and the bank,
  material and model rows before the first world row (com_map), where buildzone expects assets the world
  does not reference.
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_ROWS = ['material,mc/mtl_p7_zm_teddybear', 'material,mc/mtl_p7_zm_teddybear_fur', 'xmodel,p7_zm_teddybear']
WORLD_TYPES = ('com_map', 'navmesh', 'fx_map', 'gfx_map_trzone', 'gfx_map', 'map_ents', 'glass_map', 'aipaths', 'col_map')
CRLF, LF = chr(13) + chr(10), chr(10)


def copy_tree(src, dst):
    for root, _, files in os.walk(src):
        for name in files:
            s = os.path.join(root, name)
            d = os.path.join(dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(s, d)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('csv')
    ap.add_argument('asset_root')
    ap.add_argument('map')
    ap.add_argument('--bank-root')
    ap.add_argument('--model-root')
    ap.add_argument('--bank', default=None, help='sound bank asset name (default <map>.all)')
    args = ap.parse_args(argv)

    script_rel = 'scripts/cp/maps/%s/%s_audio.gsc' % (args.map, args.map)
    dest = os.path.join(args.asset_root, *script_rel.split('/'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(os.path.join(HERE, 'cp_iwz_audio.gsc'), dest)
    if args.bank_root:
        for d in ('sound', 'soundbank', 'sound_assets'):
            if os.path.isdir(os.path.join(args.bank_root, d)):
                copy_tree(os.path.join(args.bank_root, d), os.path.join(args.asset_root, d))
    if args.model_root:
        for d in ('xmodel', 'xsurface', 'materials', 'images'):
            if os.path.isdir(os.path.join(args.model_root, d)):
                copy_tree(os.path.join(args.model_root, d), os.path.join(args.asset_root, d))

    with open(args.csv, 'rb') as f:
        text = f.read().decode('ascii', 'replace')
    newline = CRLF if CRLF in text else LF
    lines = text.splitlines()
    present = set(lines)
    level_row = 'rawfile,scripts/cp/maps/%s/%s.gsc' % (args.map, args.map)
    script_row = 'rawfile,' + script_rel
    if script_row not in present:
        at = lines.index(level_row) + 1 if level_row in present else len(lines)
        lines.insert(at, script_row)
    rows = ['soundbank,%s' % (args.bank or args.map + '.all')] + (MODEL_ROWS if args.model_root else [])
    rows = [r for r in rows if r not in present]
    world = next((i for i, l in enumerate(lines) if l.split(',', 1)[0] in WORLD_TYPES), len(lines))
    lines[world:world] = rows
    with open(args.csv, 'w', encoding='ascii', newline='') as f:
        f.write(newline.join(lines) + newline)
    print('audio rows: %s; script %s' % (', '.join([script_row] + rows), dest))
    return 0


if __name__ == '__main__':
    sys.exit(main())
