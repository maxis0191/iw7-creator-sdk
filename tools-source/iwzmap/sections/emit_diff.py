"""Compare two emit folders file by file (sha256): the A1 gate of the section merge.

usage: emit_diff.py <emit A> <emit B> [--ignore name ...]

plan.json is compared with its `adj` list sorted (the generator wrote it in set order, which changed from run to run).
Exit code 0 when no file differs.
"""
import hashlib
import json
import os
import sys


def walk(d):
    out = {}
    for dp, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, d).replace(os.sep, '/')] = p
    return out


def digest(path):
    if path.endswith('plan.json'):
        j = json.load(open(path))
        j['adj'] = sorted(sorted(x) for x in j['adj'])
        return hashlib.sha256(json.dumps(j, sort_keys=True).encode()).hexdigest()
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def compare(a, b, ignore=()):
    """-> (differences [(kind, file)], file count)"""
    A, B = walk(a), walk(b)
    diffs = []
    for k in sorted(set(A) | set(B)):
        if k in ignore:
            continue
        if k not in A:
            diffs.append(('only-B', k))
        elif k not in B:
            diffs.append(('only-A', k))
        elif digest(A[k]) != digest(B[k]):
            diffs.append(('differs', k))
    return diffs, len(set(A) | set(B))


def main(argv):
    ign = argv[3:] if len(argv) > 3 and argv[2] == '--ignore' else []
    diffs, n = compare(argv[0], argv[1], set(ign))
    for kind, k in diffs:
        print(kind, k)
    print('files %d, differences %d' % (n, len(diffs)))
    return 1 if diffs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
