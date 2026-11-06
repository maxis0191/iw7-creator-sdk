"""Readers for IW7 ZoneTool binary dumps (assetmanager::dumper format).

Token stream (x64-zt src/zonetool/zonetool/utils/io/assetmanager.hpp):
  u8 type, then
    6 STRING / 7 ASSET : u8 exists [, NUL-terminated text]
    8 ARRAY           : u8 exists [, u32 count, count * sizeof(T) bytes]
   10 RAW             : u8 exists [, u32 size, size bytes]
    9 OFFSET          : u32 entry index, u32 array index (a pointer already written earlier)
Each existing STRING/ASSET/ARRAY/RAW is appended to the dumper's entry list, which OFFSET indexes.

Struct layouts come from x64-zt src/zonetool/zonetool/iw7/structs.hpp (XModel 0x2E0, XModelLodInfo 0x40,
XModelSurfs 0x38, XSurface 0x100, GfxPackedVertex 32, GfxImage 0x70, XStreamFile 24).
"""
import json
import os
import struct

T_STRING, T_ASSET, T_ARRAY, T_OFFSET, T_RAW = 6, 7, 8, 9, 10


class DumpError(Exception):
    pass


class Reader:
    def __init__(self, data, path=''):
        self.d = data
        self.p = 0
        self.path = path
        self.entries = []  # values of existing STRING/ASSET (text) and ARRAY/RAW (bytes) in write order

    def _type(self):
        if self.p >= len(self.d):
            raise DumpError('%s: unexpected end at %d' % (self.path, self.p))
        t = self.d[self.p]
        self.p += 1
        return t

    def _cstr(self):
        e = self.d.index(b'\0', self.p)
        s = self.d[self.p:e].decode('latin-1')
        self.p = e + 1
        return s

    def _offset(self):
        idx, arr = struct.unpack_from('<II', self.d, self.p)
        self.p += 8
        if idx >= len(self.entries):
            raise DumpError('%s: offset to unknown entry %d' % (self.path, idx))
        return ('offset', idx, arr, self.entries[idx])

    def text(self, expect=None):
        """STRING or ASSET token -> text, None (absent) or the earlier entry an OFFSET points at."""
        t = self._type()
        if t == T_OFFSET:
            v = self._offset()[3]
            return v if isinstance(v, str) else None
        if t not in (T_STRING, T_ASSET) or (expect and t != expect):
            raise DumpError('%s: expected string/asset token at %d, got %d' % (self.path, self.p - 1, t))
        exists = self.d[self.p]
        self.p += 1
        if not exists:
            return None
        s = self._cstr()
        self.entries.append(s)
        return s

    def array(self, elem_size):
        """ARRAY token -> (count, bytes) or (0, b'') when absent; OFFSET -> (count unknown -1, b'')."""
        t = self._type()
        if t == T_OFFSET:
            self._offset()
            return -1, b''
        if t != T_ARRAY:
            raise DumpError('%s: expected array token at %d, got %d' % (self.path, self.p - 1, t))
        exists = self.d[self.p]
        self.p += 1
        if not exists:
            return 0, b''
        n = struct.unpack_from('<I', self.d, self.p)[0]
        self.p += 4
        size = n * elem_size
        if self.p + size > len(self.d):
            raise DumpError('%s: array of %d x %d overruns file' % (self.path, n, elem_size))
        b = self.d[self.p:self.p + size]
        self.p += size
        self.entries.append(b)
        return n, b

    def raw(self):
        t = self._type()
        if t == T_OFFSET:
            self._offset()
            return b''
        if t != T_RAW:
            raise DumpError('%s: expected raw token at %d, got %d' % (self.path, self.p - 1, t))
        exists = self.d[self.p]
        self.p += 1
        if not exists:
            return b''
        n = struct.unpack_from('<I', self.d, self.p)[0]
        self.p += 4
        b = self.d[self.p:self.p + n]
        self.p += n
        self.entries.append(b)
        return b


def _bounds(mid, half):
    return {'mins': [round(mid[i] - half[i], 3) for i in range(3)],
            'maxs': [round(mid[i] + half[i], 3) for i in range(3)]}


# ---------------------------------------------------------------- XModel (.xmb)

XMODEL_SIZE = 0x2E0
LOD_SIZE = 0x40


def read_xmodel(path):
    d = open(path, 'rb').read()
    r = Reader(d, path)
    n, h = r.array(XMODEL_SIZE)
    if n != 1:
        raise DumpError('%s: no XModel header' % path)
    name = r.text(T_STRING)
    (has_lods, max_loaded_lod, num_lods, coll_lod, shadow_lod, char_coll) = struct.unpack_from('<?BBBBB', h, 9)
    flags = struct.unpack_from('<i', h, 16)[0]
    num_bones, num_root, num_rmp = struct.unpack_from('<BBB', h, 20)
    num_client_bones, num_surfs = struct.unpack_from('<HH', h, 24)
    scale = struct.unpack_from('<f', h, 28)[0]
    num_coll_surfs = struct.unpack_from('<H', h, 32)[0]
    contents, radius = struct.unpack_from('<if', h, 36)
    mid = struct.unpack_from('<3f', h, 44)
    half = struct.unpack_from('<3f', h, 56)
    mem_usage, phys_lod_size = struct.unpack_from('<II', h, 68)
    lods = []
    for i in range(6):
        dist, lsurfs, sidx = struct.unpack_from('<fHH', h, 224 + i * LOD_SIZE)
        lods.append({'dist': round(dist, 2), 'numsurfs': lsurfs, 'surfIndex': sidx})
    ptr = lambda off: struct.unpack_from('<Q', h, off)[0]
    has_phys_asset = ptr(632) != 0
    has_fx_shape = ptr(640) != 0
    phys_name_count = struct.unpack_from('<I', h, 656)[0]

    # sequential payload (xmodel::dump order)
    bones = num_bones + num_client_bones
    bone_names = [r.text() for _ in range(bones)]
    non_root = bones - num_root
    r.array(1)            # parentList
    r.array(8)            # tagAngles
    r.array(12)           # tagPositions
    r.array(1)            # partClassification
    r.array(32)           # baseMat
    r.array(16)           # reactiveMotionParts
    r.array(16)           # reactiveMotionTweaks (single)
    ncs, coll = r.array(36)   # collSurfs
    nbi, bone_info = r.array(28)
    r.array(2)            # invHighMipRadius
    r.array(8)            # materialHandles (pointers)
    materials = [r.text() for _ in range(num_surfs)]
    lod_surfs = [r.text() for _ in range(6)]
    physics_asset = r.text()
    physics_fx_shape = r.text()
    coll_bounds = []
    for i in range(max(ncs, 0)):
        m = struct.unpack_from('<3f', coll, i * 36)
        hs = struct.unpack_from('<3f', coll, i * 36 + 12)
        coll_bounds.append(_bounds(m, hs))
    for i, lod in enumerate(lods):
        lod['surfs'] = lod_surfs[i]
        lod['materials'] = materials[lod['surfIndex']:lod['surfIndex'] + lod['numsurfs']] if lod['numsurfs'] else []
    hkx = os.path.join(os.path.dirname(path), name.replace('/', os.sep) + '_lod.hkx')
    return {
        'name': name,
        'numLods': num_lods,
        'collLod': coll_lod,
        'flags': flags,
        'numBones': num_bones,
        'numClientBones': num_client_bones,
        'boneNames': bone_names,
        'numsurfs': num_surfs,
        'scale': round(scale, 4),
        'contents': contents,
        'radius': round(radius, 3),
        'bounds': _bounds(mid, half),
        'memUsage': mem_usage,
        'lods': lods[:max(num_lods, 1)],
        'materials': sorted(set(m for m in materials if m)),
        'numCollSurfs': num_coll_surfs,
        'collSurfBounds': coll_bounds,
        'physicsAsset': physics_asset,
        'physicsFXShape': physics_fx_shape,
        'physicsLODDataSize': phys_lod_size,
        'physicsLODDataNameCount': phys_name_count,
        'havokFile': os.path.basename(hkx) if os.path.exists(hkx) else None,
        'hasPhysicsAssetPtr': has_phys_asset,
        'hasFXShapePtr': has_fx_shape,
    }


# ---------------------------------------------------------------- XModelSurfs (.xsb)

XSURFS_SIZE = 0x38
XSURFACE_SIZE = 0x100
VERT_SIZE = 32


def read_xsurfs(path, want_verts=False):
    d = open(path, 'rb').read()
    r = Reader(d, path)
    n, h = r.array(XSURFS_SIZE)
    if n != 1:
        raise DumpError('%s: no XModelSurfs header' % path)
    name = r.text(T_STRING)
    numsurfs = struct.unpack_from('<H', h, 16)[0]
    ns, sb = r.array(XSURFACE_SIZE)
    surfs = []
    lo = [1e30] * 3
    hi = [-1e30] * 3
    all_verts = []
    for i in range(numsurfs):
        s = sb[i * XSURFACE_SIZE:(i + 1) * XSURFACE_SIZE]
        flags, vcount, tcount, rvl_count, subdiv_levels = struct.unpack_from('<HHHBB', s, 0)
        subdiv_ptr = struct.unpack_from('<Q', s, 128)[0]
        nv, vb = r.array(VERT_SIZE)
        nt, tb = r.array(6)
        nr, rb = r.array(16)
        for k in range(max(nr, 0)):
            tree_ptr = struct.unpack_from('<Q', rb, k * 16 + 8)[0]
            if rb and tree_ptr:
                _, tree = r.array(56)
                nodes_ptr = struct.unpack_from('<Q', tree, 32)[0]
                leafs_ptr = struct.unpack_from('<Q', tree, 48)[0]
                if leafs_ptr:
                    r.array(2)
                if nodes_ptr:
                    r.array(16)
        r.raw()  # blendVerts
        lmap = r.raw()  # lmapUnwrap
        r.raw()  # tensionData
        r.raw()  # tensionAccumTable
        if subdiv_ptr:
            _, sd = r.array(0x38)
            levels_ptr = struct.unpack_from('<Q', sd, 0)[0] if sd else 0
            if levels_ptr:
                r.array(0xE8)
                for _ in range(subdiv_levels):
                    for _ in range(10):
                        r.raw()
        # dump_shprobesimplexdata: SHProbeSimplexData0 (32 B), data1 (8 B) or data2 (24 B) per vertex
        if (flags & 0x500) == 0x500:
            r.array(32)
        elif flags & 0x100:
            r.array(8)
        elif flags & 0x400:
            r.array(24)
        verts = []
        for k in range(max(nv, 0)):
            x, y, z = struct.unpack_from('<3f', vb, k * VERT_SIZE)
            verts.append((x, y, z))
            if x < lo[0]: lo[0] = x
            if y < lo[1]: lo[1] = y
            if z < lo[2]: lo[2] = z
            if x > hi[0]: hi[0] = x
            if y > hi[1]: hi[1] = y
            if z > hi[2]: hi[2] = z
        if want_verts:
            all_verts.append(verts)
        surfs.append({'flags': flags, 'verts': vcount, 'tris': tcount, 'rigidVertLists': rvl_count,
                      'skinned': bool(flags & 4), 'lightmapCoords': bool(lmap), 'subdiv': bool(subdiv_ptr)})
    if r.p != len(d):
        raise DumpError('%s: parsed %d of %d bytes' % (path, r.p, len(d)))
    out = {'name': name, 'numsurfs': numsurfs, 'surfaces': surfs,
           'verts': sum(s['verts'] for s in surfs), 'tris': sum(s['tris'] for s in surfs),
           'bytes': len(d)}
    if surfs and lo[0] <= hi[0]:
        out['vertBounds'] = {'mins': [round(v, 3) for v in lo], 'maxs': [round(v, 3) for v in hi]}
    if want_verts:
        out['vertexLists'] = all_verts
    return out


# ---------------------------------------------------------------- GfxImage (.iw7Image)

IMAGE_SIZE = 0x70


def read_image(path):
    d = open(path, 'rb').read()
    r = Reader(d, path)
    n, h = r.array(IMAGE_SIZE)
    if n != 1:
        raise DumpError('%s: no GfxImage header' % path)
    name = r.text(T_STRING)
    fmt, flags = struct.unpack_from('<II', h, 24)
    map_type, semantic, category = struct.unpack_from('<BBB', h, 32)
    data_len1, data_len2 = struct.unpack_from('<II', h, 40)
    w, hh, depth, elems, levels, streamed = struct.unpack_from('<HHHHBB', h, 48)
    pix_ptr = struct.unpack_from('<Q', h, 64)[0]
    embedded = 0
    if pix_ptr:
        cnt, _ = r.array(1)
        embedded = max(cnt, 0)
    streams = []
    if streamed:
        for i in range(4):
            cnt, sf = r.array(24)
            if cnt == 1:
                off, end, fi, loc = struct.unpack_from('<QQH?', sf, 0)
                if end > off:
                    sw, sh = struct.unpack_from('<HH', h, 72 + i * 8)
                    streams.append({'fileIndex': fi, 'bytes': end - off, 'width': sw, 'height': sh})
    return {'name': name, 'format': fmt, 'semantic': semantic, 'category': category, 'width': w, 'height': hh,
            'levels': levels, 'streamed': bool(streamed), 'embeddedBytes': embedded, 'streams': streams,
            'streamBytes': sum(s['bytes'] for s in streams)}


# ---------------------------------------------------------------- Material (.json)

def read_material(path):
    m = json.load(open(path, 'rb'))
    return {'techset': m.get('techniqueSet->name'),
            'images': [{'image': t.get('image'), 'semantic': t.get('semantic')} for t in m.get('textureTable', [])],
            'surfaceTypeBits': m.get('surfaceTypeBits'), 'sortKey': m.get('sortKey')}
