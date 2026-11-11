"""Are two built IW7 zones (.ff) the same map? Decompresses both and compares their content.

  python -I ff_compare.py <a.ff> <b.ff> [--json out.json] [--show 10]

Exit 0: same content (byte-identical, or different only in pointer residue); 1: different content; 2: unreadable.

ZoneTool writes some 8-byte fields that hold a leftover address of its own process (pointer residue: the value
of a pointer that the game rebuilds at load and never reads from the file). Their values change with the heap
layout of the run, so two builds of the same source can differ in tens of thousands of bytes with the same map
inside. A differing byte counts as residue when the aligned 8-byte word that holds it is pointer-like in both files
(the upper 32 bits equal, non-zero and below 0x8000) and the two words are within 1 GB of each other. Everything
else is a content difference and is listed with its offset in the decompressed zone.

Needs the `lz4` package (pip install lz4; the zone blocks are LZ4).
"""
import argparse, json, struct, sys

try:
    import lz4.block
except ImportError:
    sys.stderr.write('ff_compare needs the lz4 package: python -m pip install lz4\n'); sys.exit(2)


def unpack(path):
    d = open(path, 'rb').read()
    i = d.find(b'IWC')
    if i < 0:
        raise ValueError('no IWC block stream in ' + path)
    p = i + 3
    total, _ = struct.unpack_from('<QI', d, p); p += 12
    out = bytearray()
    while len(out) < total:
        cs, us = struct.unpack_from('<II', d, p); p += 12
        out += lz4.block.decompress(d[p:p + cs], uncompressed_size=us)
        p += (cs + 3) & ~3
    return bytes(out), d[p:]


def pointer_like(w):
    hi = w >> 32
    return 0 < hi < 0x8000


def compare(a_path, b_path, show=10):
    a, ta = unpack(a_path)
    b, tb = unpack(b_path)
    r = {'schema': 'iwz.ff-compare/1', 'a': a_path, 'b': b_path, 'size_a': len(a), 'size_b': len(b),
         'tail_equal': ta == tb}
    if len(a) != len(b):
        r.update(verdict='different', reason='decompressed sizes differ'); return r
    diff_bytes = residue_bytes = 0
    content = []
    words = set()
    # walk differing 8-byte words; compare in 1 MB slices to keep it quick
    step = 1 << 20
    for base in range(0, len(a), step):
        sa, sb = a[base:base + step], b[base:base + step]
        if sa == sb:
            continue
        k = 0
        n = len(sa)
        while k < n:
            if sa[k] != sb[k]:
                off = base + k
                diff_bytes += 1
                hit = None
                # zone streams are packed, not 8-aligned: any 8-byte window over the byte may hold the pointer
                for w0 in range(max(0, off - 7), min(off, len(a) - 8) + 1):
                    wa = struct.unpack_from('<Q', a, w0)[0]; wb = struct.unpack_from('<Q', b, w0)[0]
                    if pointer_like(wa) and pointer_like(wb) and (wa >> 32) == (wb >> 32) and abs(wa - wb) < (1 << 30) \
                            and (wa & 0xFFFFFFFF) >= 0x10000:
                        hit = w0; break
                if hit is not None:
                    residue_bytes += 1; words.add(hit); k += 1; continue
                if len(content) < 10000:
                    content.append(off)
            k += 1
    r.update(differing_bytes=diff_bytes, residue_bytes=residue_bytes, residue_words=len(words),
             content_bytes=diff_bytes - residue_bytes, content_offsets=content[:show],
             verdict='identical' if diff_bytes == 0 and ta == tb else ('same_content' if diff_bytes == residue_bytes and ta == tb else 'different'))
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('a'); ap.add_argument('b'); ap.add_argument('--json'); ap.add_argument('--show', type=int, default=10)
    x = ap.parse_args()
    try:
        r = compare(x.a, x.b, x.show)
    except Exception as e:
        print('unreadable: %s' % e); return 2
    if x.json:
        json.dump(r, open(x.json, 'w'), indent=1)
    print('%s: %d bytes decompressed; %d differ, %d of them pointer residue (%d words), %d content%s' % (
        r['verdict'], r['size_a'], r.get('differing_bytes', -1), r.get('residue_bytes', 0), r.get('residue_words', 0),
        r.get('content_bytes', -1), (' at ' + ', '.join(hex(o) for o in r.get('content_offsets', []))) if r.get('content_bytes') else ''))
    return 0 if r['verdict'] in ('identical', 'same_content') else 1


if __name__ == '__main__':
    sys.exit(main())
