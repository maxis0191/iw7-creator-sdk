"""Havok 2014 binary packfile reader (IW7: hk_2014.2.5-r1, 64-bit, little endian)."""
import struct

MAGIC = b'\x57\xe0\xe0\x57\x10\xc0\xc0\x10'

class Section:
    pass

class Packfile:
    def __init__(self, data: bytes):
        self.data = data
        assert data[:8] == MAGIC, 'not a packfile'
        (self.user_tag, self.version) = struct.unpack_from('<II', data, 8)
        self.layout = data[0x10:0x14]
        (self.num_sections, self.contents_sec, self.contents_off,
         self.contents_cn_sec, self.contents_cn_off) = struct.unpack_from('<5i', data, 0x14)
        self.contents_version = data[0x28:0x38].split(b'\0')[0].decode()
        self.flags, self.max_pred, self.pred_pad = struct.unpack_from('<Ihh', data, 0x38)
        hdr = 0x40 + (self.pred_pad if self.max_pred != -1 else 0)
        self.header_size = hdr
        self.sections = []
        for i in range(self.num_sections):
            o = hdr + i * 0x40
            s = Section()
            s.name = data[o:o+20].split(b'\0')[0].decode()
            (s.start, s.local, s.glob, s.virt, s.exports, s.imports, s.end) = struct.unpack_from('<7I', data, o + 20)
            s.body = data[s.start:s.start + s.local]
            s.locals = []
            for p in range(s.start + s.local, s.start + s.glob - 7, 8):
                a, b = struct.unpack_from('<ii', data, p)
                if a != -1: s.locals.append((a, b))
            s.globals = []
            for p in range(s.start + s.glob, s.start + s.virt - 11, 12):
                a, sec, b = struct.unpack_from('<iii', data, p)
                if a != -1: s.globals.append((a, sec, b))
            s.virtuals = []
            for p in range(s.start + s.virt, min(s.start + s.exports, len(data)) - 11, 12):
                a, sec, b = struct.unpack_from('<iii', data, p)
                if a != -1: s.virtuals.append((a, sec, b))
            self.sections.append(s)
        cn = self.sections[0]
        self.classnames = {}
        p = 0
        while p + 5 <= len(cn.body):
            h, tag = struct.unpack_from('<IB', cn.body, p)
            if tag != 0x09: break
            e = cn.body.index(b'\0', p + 5)
            self.classnames[p + 5] = (h, cn.body[p+5:e].decode())
            p = e + 1
        d = self.sections[self.contents_sec]
        self.data_sec = d
        self.ptr = {a: b for a, b in d.locals}
        self.ptr.update({a: b for a, sec, b in d.globals})
        objs = sorted((a, self.classnames[b][1]) for a, sec, b in d.virtuals)
        self.objects = []
        for i, (a, name) in enumerate(objs):
            end = objs[i+1][0] if i + 1 < len(objs) else len(d.body)
            self.objects.append((a, name, end - a))

    def u32(self, o): return struct.unpack_from('<I', self.data_sec.body, o)[0]
    def f32(self, o): return struct.unpack_from('<f', self.data_sec.body, o)[0]
    def array(self, o):
        """hkArray at data offset o -> (target offset or None, size, capflags)."""
        size, cap = struct.unpack_from('<iI', self.data_sec.body, o + 8)
        return self.ptr.get(o), size, cap

if __name__ == '__main__':
    import sys
    pf = Packfile(open(sys.argv[1], 'rb').read())
    print(pf.version, pf.contents_version, 'hdr', hex(pf.header_size), [ (s.name, hex(s.start), len(s.body), len(s.locals), len(s.globals), len(s.virtuals)) for s in pf.sections])
    print('classnames', [v[1] for v in pf.classnames.values()])
    from collections import Counter
    print(Counter(n for _, n, _ in pf.objects))
    for a, n, sz in pf.objects[:8]: print(hex(a), n, hex(sz))
