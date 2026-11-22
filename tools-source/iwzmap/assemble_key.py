"""The key of an incremental assembly: one SHA-256 over every input that can change what the kept tree holds.

usage: assemble_key.py [--file F]... [--tree D]... [--manifest D]... [--stamp D]... [--text T]...
       prints the key (hex) on stdout, the timing on stderr

assemble.py --incremental keeps zonetool/<map>/ from the previous build: the 135,676 stock hard links and what the module
scripts (kit, perks, effects, audio, darkness) wrote into it. That is only right while nothing that made those files has
changed. build-sz2.ps1 and build-blend.ps1 compute this key before the assembly, compare it with the one stored beside the kept
tree (zonetool/<map>/.iwz_modules.key, written only when the whole assembly succeeded) and assemble everything on a mismatch.

    --file F       content hash of one file (the compiler, assemble.py, sz2_assemble.py, kit_import.py, a kit json, an image)
    --tree D       content hash of every file below D (the module folders: perks, darkness, fx, audio; small trees)
    --manifest D   path + size + modification time of every file below D (the stock dumps: 136k files, content hashing them
                   would cost what the assembly costs). A re-dump or a replaced file changes size or time. Listing the files
                   is the cost: 12 s with 8 threads, 25 s with one, on the development machine (22 Nov 2026, warm).
    --stamp D      the quick form of --manifest for a dump that is frozen reference data (see stamp_hash): milliseconds
    --text T       any string: arguments, switches, environment values (IWZ_FULL_STOCK, IWZ_KEEP_STOCK_REFS)

Order matters (the first dump wins in assemble.py) and is part of the key. A missing path is a failure (exit 2), never an
empty input: a wrong key that matches by accident is worse than a slow build.
"""
import hashlib
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

SCHEMA = 'iwz-assemble-key/2'


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def _walk(root):
    """Files below root, sorted (compiled caches left out)."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d != '__pycache__')
        for n in fn:
            if not n.endswith('.pyc'):
                out.append(os.path.join(dp, n))
    out.sort()
    return out


def _rel(path, root):
    return os.path.relpath(path, root).replace('\\', '/')


def tree_hash(root):
    h = hashlib.sha256()
    for p in _walk(root):
        h.update(('%s\t%s\n' % (_rel(p, root), _sha_file(p))).encode())
    return h.hexdigest()


def _scan(d):
    files, dirs = [], []
    with os.scandir(d) as it:
        for e in it:
            if e.is_dir(follow_symlinks=False):
                dirs.append(e.path)
            else:
                st = e.stat(follow_symlinks=False)
                files.append((e.path, st.st_size, st.st_mtime_ns))
    return files, dirs


def manifest_hash(root):
    """Path, size and modification time of every file below root."""
    entries = []
    pending = [root]
    with ThreadPoolExecutor(8) as pool:
        while pending:
            nxt = []
            for files, dirs in pool.map(_scan, pending):
                entries += files
                nxt += dirs
            pending = nxt
    rows = sorted((_rel(p, root), size, mt) for p, size, mt in entries)
    h = hashlib.sha256()
    for rel, size, mt in rows:
        h.update(('%s\t%d\t%d\n' % (rel, size, mt)).encode())
    return h.hexdigest(), len(rows)


def stamp_hash(root):
    """Quick stand-in for manifest_hash on a dump that is frozen reference data: the files directly in root (a dump's csv is
    rewritten by every dump run) and the name and modification time of every directory directly in root. A file added, removed or
    replaced directly in such a directory moves its time; one a level deeper (materials/mo/...) does not, and neither does a file
    overwritten in place (harmless for the stock links of a kept tree: a hard link sees the new bytes). Only right for dumps
    nobody touches."""
    h = hashlib.sha256()
    with os.scandir(root) as it:
        entries = sorted(it, key=lambda e: e.name)
    for e in entries:
        st = os.stat(e.path)
        if e.is_dir(follow_symlinks=False):
            h.update(('d\t%s\t%d\n' % (e.name, st.st_mtime_ns)).encode())
        else:
            h.update(('f\t%s\t%d\t%d\n' % (e.name, st.st_size, st.st_mtime_ns)).encode())
    return h.hexdigest(), len(entries)


def make_key(parts):
    """parts: [(kind, value)] in argument order, kind one of file, tree, manifest, stamp, text. Returns (key, files listed)."""
    lines = [SCHEMA]
    files = 0
    for kind, value in parts:
        if kind == 'file':
            if not os.path.isfile(value):
                raise FileNotFoundError('input file %s' % value)
            lines.append('file\t%s' % _sha_file(value))
        elif kind == 'tree':
            if not os.path.isdir(value):
                raise FileNotFoundError('input folder %s' % value)
            lines.append('tree\t%s' % tree_hash(value))
        elif kind in ('manifest', 'stamp'):
            if not os.path.isdir(value):
                raise FileNotFoundError('input folder %s' % value)
            digest, n = (manifest_hash if kind == 'manifest' else stamp_hash)(value)
            files += n
            lines.append('%s\t%s\t%d' % (kind, digest, n))
        else:
            lines.append('text\t%s' % value)
    return hashlib.sha256('\n'.join(lines).encode()).hexdigest(), files


def main(argv):
    parts = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('--file', '--tree', '--manifest', '--stamp', '--text') and i + 1 < len(argv):
            parts.append((a[2:], argv[i + 1]))
            i += 2
        else:
            sys.stderr.write('assemble_key: bad argument %r\n' % a)
            return 2
    t0 = time.time()
    try:
        key, files = make_key(parts)
    except (FileNotFoundError, NotADirectoryError) as e:
        sys.stderr.write('assemble_key: %s\n' % e)
        return 2
    sys.stderr.write('assemble_key: %d inputs, %d files listed, %.1f s\n' % (len(parts), files, time.time() - t0))
    print(key)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
