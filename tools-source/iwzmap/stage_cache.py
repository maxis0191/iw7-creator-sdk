#!/usr/bin/env python3
"""Stage cache of the map chain: one machine-wide folder shared by every worktree and agent.

    stages/<stage>/<key>/        the output of one build stage, stored when the stage succeeded, restored by key.

The folder is $IW7_BUILD_CACHE, default C:\\IW7-Cache (the same one the lab client packages and the mod stages use).
A key is the SHA-256 of every input of the stage. A stage whose inputs did not change is restored, not run again:

    bake      key = the render world (world.bin), the light list, the bake arguments and the bake tool files
              output = the baked source folder (lightmaps and the baked world.bin)
              A change of entities, scripts, collision, nav or any other generated file keeps the key: no new bake.
    other     any stage with a key of its own (the compile takes 7 s and the zone 41 to 63 s: not cached today)

Commands (exit 0 = done / hit, 3 = miss, 2 = bad use):
    key     --stage S [--file F]... [--tree D [--skip NAME]...]... [--text T]...   print the key
    restore --stage S --key K --dest D                                            copy the entry to D (D is replaced)
    save    --stage S --key K --src D [--info JSON]                                store D
    prune   --stage S [--max-gb N]                                                 drop least recently used entries
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time

SCHEMA = 'stage-cache/1'


def cache_root():
    root = os.environ.get('IW7_BUILD_CACHE') or 'C:\\IW7-Cache'
    root = os.path.abspath(root)
    os.makedirs(root, exist_ok=True)
    return root


def stage_dir(stage, key):
    return os.path.join(cache_root(), 'stages', stage, key)


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def tree_lines(root, skip):
    root = os.path.abspath(root)
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip]
        for n in fn:
            if n in skip:
                continue
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, root).replace('\\', '/')
            out.append('%s\t%d\t%s' % (rel, os.path.getsize(p), file_sha(p)))
    out.sort()
    return out


def make_key(files, trees, texts):
    parts = [SCHEMA]
    for f in files:
        parts.append('file\t%s' % file_sha(f))
    for root, skip in trees:
        parts.append('tree\t' + hashlib.sha256('\n'.join(tree_lines(root, skip)).encode()).hexdigest())
    for t in texts:
        parts.append('text\t%s' % t)
    return hashlib.sha256('\n'.join(parts).encode()).hexdigest()


def restore(stage, key, dest):
    src = stage_dir(stage, key)
    if not os.path.isfile(os.path.join(src, 'complete.json')):
        return False
    data = os.path.join(src, 'data')
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(data, dest)
    with open(os.path.join(src, 'used.stamp'), 'w') as f:
        f.write(str(time.time()))
    return True


def save(stage, key, src_dir, info):
    final = stage_dir(stage, key)
    if os.path.isfile(os.path.join(final, 'complete.json')):
        return
    tmp = '%s.tmp-%d' % (final, os.getpid())
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    shutil.copytree(src_dir, os.path.join(tmp, 'data'))
    info = dict(info or {})
    info.update({'key': key, 'stage': stage, 'stored': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    with open(os.path.join(tmp, 'complete.json'), 'w') as f:
        json.dump(info, f)
    if os.path.isdir(final):
        shutil.rmtree(final)
    try:
        os.rename(tmp, final)
    except OSError:
        shutil.rmtree(tmp, ignore_errors=True)


def prune(stage, max_gb):
    root = os.path.join(cache_root(), 'stages', stage)
    if not os.path.isdir(root):
        return
    items = []
    for n in os.listdir(root):
        d = os.path.join(root, n)
        if not os.path.isdir(d) or '.tmp-' in n:
            continue
        stamp = os.path.join(d, 'used.stamp')
        used = os.path.getmtime(stamp) if os.path.isfile(stamp) else os.path.getmtime(d)
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(d) for f in fs)
        items.append((used, d, size))
    items.sort()
    total = sum(i[2] for i in items)
    for used, d, size in items:
        if total <= max_gb * (1 << 30):
            break
        shutil.rmtree(d, ignore_errors=True)
        total -= size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    k = sub.add_parser('key')
    k.add_argument('--stage', required=True)
    k.add_argument('--file', action='append', default=[])
    k.add_argument('--tree', action='append', default=[])
    k.add_argument('--skip', action='append', default=[], help='file or folder names left out of every --tree')
    k.add_argument('--text', action='append', default=[])
    r = sub.add_parser('restore')
    r.add_argument('--stage', required=True)
    r.add_argument('--key', required=True)
    r.add_argument('--dest', required=True)
    s = sub.add_parser('save')
    s.add_argument('--stage', required=True)
    s.add_argument('--key', required=True)
    s.add_argument('--src', required=True)
    s.add_argument('--info', default='{}')
    p = sub.add_parser('prune')
    p.add_argument('--stage', required=True)
    p.add_argument('--max-gb', type=float, default=20)
    a = ap.parse_args(argv)
    if a.cmd == 'key':
        for f in a.file:
            if not os.path.isfile(f):
                print('stage_cache: missing input file %s' % f, file=sys.stderr)
                return 2
        print(make_key(a.file, [(t, set(a.skip)) for t in a.tree], a.text))
        return 0
    if a.cmd == 'restore':
        if restore(a.stage, a.key, a.dest):
            print('stage_cache: %s %s restored' % (a.stage, a.key[:12]))
            return 0
        return 3
    if a.cmd == 'save':
        save(a.stage, a.key, a.src, json.loads(a.info))
        print('stage_cache: %s %s stored' % (a.stage, a.key[:12]))
        return 0
    prune(a.stage, a.max_gb)
    return 0


if __name__ == '__main__':
    sys.exit(main())
