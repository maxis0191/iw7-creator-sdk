"""Asset side of the Station Zero Blender preview: plain Python + numpy, no bpy, no PIL (it also runs inside Blender).

  paths        runtime / game root / dump roots, from IWZ_* environment variables (machine.ps1 conventions)
  read_world   world.bin (same layout as bake/lmbake.py read_world; copied because lmbake imports numba)
  DumpIndex    name -> file for xmodel (.xmb), xsurface (.xsb), image (.iw7Image) and material (.json) over many dumps
  image_png    an image of the dumps -> PNG in the cache: embedded pixels, or the streamed top mip read from
               imagefile<N>.pak (an 'IWC' LZ4 block stream), BC / RGBA decode by texconv
  read_model   LOD0 of an xmodel: positions, uv (two float16 in the packed vertex), triangles per surface, material names
Everything unresolved is returned as a reason string, never replaced by a fake value.
"""
import glob
import json
import os
import struct
import subprocess
import sys
import shutil
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'catalog'))
import ztdump  # noqa: E402

VD = np.dtype([('pos', '<f4', 3), ('bs', '<f4'), ('col', 'u1', 4), ('uv', '<f4', 2), ('lm', '<f4', 2), ('n', '<u4'), ('t', '<u4')])
SD = np.dtype([('mat', '<u4'), ('first', '<u4'), ('vc', '<u4'), ('base', '<u4'), ('tc', '<u4'), ('mn', '<f4', 3), ('mx', '<f4', 3)])


# ---------------------------------------------------------------------------------------------------- paths
def runtime():
    return os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')


def cache_dir():
    base = os.environ.get('IWZ_PREVIEW_CACHE') or os.path.join(
        os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'iwz-preview-cache')
    os.makedirs(base, exist_ok=True)
    return base


def texconv_exe():
    return os.environ.get('IWZ_TEXCONV') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Tools', 'texconv-may2026', 'texconv.exe')


def game_root():
    """Folder holding imagefile<N>.pak: IWZ_GAME_ROOT, else the first bench root under the runtime that has them."""
    e = os.environ.get('IWZ_GAME_ROOT')
    if e:
        return e
    for pat in ('bench/*', 'iwz-map-ref-a'):
        for d in sorted(glob.glob(os.path.join(runtime(), pat))):
            if os.path.isfile(os.path.join(d, 'imagefile19.pak')):
                return d
    return None


def dump_roots():
    """Dump folders searched, in order. IWZ_PREVIEW_DUMPS (os.pathsep list) replaces the default."""
    e = os.environ.get('IWZ_PREVIEW_DUMPS')
    if e:
        return [p for p in e.split(os.pathsep) if p]
    rt = runtime()
    tmpl = os.environ.get('IWZ_TEMPLATE_DUMP') or os.path.join(rt, 'iwz-map-ref-a', 'dump')
    kit = os.path.join(rt, 'iwz-stage2', 'kitimport', 'ztwork', 'dump')
    roots = []
    for z in ('cp_zmb', 'techsets_cp_zmb', 'techsets_global_cp', 'global_cp', 'techsets_common_cp', 'common_cp',
              'techsets_global', 'global', 'patch_cp_zmb'):
        roots.append(os.path.join(tmpl, z))
    for z in ('cp_disco', 'cp_final', 'cp_iwz', 'techsets_cp_disco', 'techsets_cp_final'):
        roots.append(os.path.join(kit, z))
    # the dump of the built map zone (our own iwz_* models and materials), searched after the stock dumps
    for sub in (('level', 'ztwork'), ('fx', 'ztwork-d')):
        roots.append(os.path.join(rt, 'iwz-stage2', *sub, 'zonetool', 'cp_iwz'))
    return [r for r in roots if os.path.isdir(r)]


# ---------------------------------------------------------------------------------------------------- world.bin
def read_world(path):
    b = open(path, 'rb').read()
    magic, ver = struct.unpack_from('<II', b, 0)
    if magic != 0x575A5749 or ver != 1:
        raise ValueError('world.bin: bad magic/version')
    off = 8
    nm, = struct.unpack_from('<I', b, off); off += 4
    mats = []
    for _ in range(nm):
        n, = struct.unpack_from('<H', b, off); off += 2
        mats.append(b[off:off + n].decode()); off += n
    nv, = struct.unpack_from('<I', b, off); off += 4
    verts = np.frombuffer(b, VD, nv, off).copy(); off += nv * VD.itemsize
    ni, = struct.unpack_from('<I', b, off); off += 4
    idx = np.frombuffer(b, '<u2', ni, off).copy(); off += ni * 2
    ns, = struct.unpack_from('<I', b, off); off += 4
    surfs = np.frombuffer(b, SD, ns, off).copy()
    return {'materials': mats, 'verts': verts, 'indices': idx, 'surfaces': surfs}


# ---------------------------------------------------------------------------------------------------- dump index
class DumpIndex:
    """name -> path for the assets of several dump roots. Built by one directory walk per root, cached as JSON."""

    def __init__(self, roots=None):
        self.roots = roots or dump_roots()
        self.maps = {'xmodel': {}, 'xsurface': {}, 'image': {}, 'material': {}}
        key = 'v3|' + str(sorted(os.path.getmtime(r) for r in self.roots)) + '|' + '|'.join(self.roots)
        cf = os.path.join(cache_dir(), 'dump_index.json')
        try:
            c = json.load(open(cf))
            if c.get('key') == key:
                self.maps = c['maps']
                return
        except (OSError, ValueError):
            pass
        for r in self.roots:
            self._walk(r)
        try:
            json.dump({'key': key, 'maps': self.maps}, open(cf, 'w'))
        except OSError:
            pass

    def _walk(self, root):
        for kind, sub, ext in (('xmodel', 'xmodel', '.xmb'), ('xsurface', 'xsurface', '.xsb'), ('image', 'images', '.iw7Image')):
            d = os.path.join(root, sub)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith(ext):
                        self.maps[kind].setdefault(f[:-len(ext)], os.path.join(d, f))
                    elif kind == 'image' and f.endswith('.dds'):         # the built zone's own images are plain DDS files
                        self.maps[kind].setdefault(f[:-4], os.path.join(d, f))
        md = os.path.join(root, 'materials')
        if os.path.isdir(md):
            for dp, _, fs in os.walk(md):
                rel = os.path.relpath(dp, md).replace('\\', '/')
                for f in fs:
                    if f.endswith('.json'):
                        k = (f[:-5] if rel == '.' else rel + '/' + f[:-5])
                        self.maps['material'].setdefault(k, os.path.join(dp, f))

    def get(self, kind, name):
        return self.maps[kind].get(name)


# ---------------------------------------------------------------------------------------------------- images
def lz4_block(src, usize):
    """LZ4 block decompress: the lz4 package when present, else pure Python.

    The package refuses a block that breaks the format's end rules (the last five bytes must be literals); the pure Python
    reader below takes it, so a refused block falls through to it instead of failing."""
    try:
        import lz4.block
    except ImportError:
        lz4 = None
    if lz4 is not None:
        try:
            return lz4.block.decompress(bytes(src), uncompressed_size=usize)
        except lz4.block.LZ4BlockError:
            pass
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        tok = src[i]; i += 1
        ll = tok >> 4
        if ll == 15:
            while True:
                b = src[i]; i += 1; ll += b
                if b != 255:
                    break
        out += src[i:i + ll]; i += ll
        if i >= n:
            break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255:
                    break
        ml += 4
        s = len(out) - off
        if off >= ml:
            out += out[s:s + ml]
        else:
            for k in range(ml):
                out.append(out[s + k])
    return bytes(out)


def iwc_unpack(buf):
    """An 'IWC' block stream (x64-zt zone.cpp compression::iwc): 4 byte header (version, 'IWC'), u64 total,
    u32 blockSize:24|type:8, then blocks of [u32 compressedSize][u64 uncompressedSize][data]."""
    if buf[1:4] != b'IWC':
        raise ValueError('not an IWC block stream')
    total, bs_type = struct.unpack_from('<QI', buf, 4)
    ctype = bs_type >> 24
    p = 16
    out = bytearray()
    while len(out) < total and p + 12 <= len(buf):
        cs, us = struct.unpack_from('<IQ', buf, p); p += 12
        chunk = buf[p:p + cs]; p = (p + cs + 3) & ~3
        if ctype == 5 or cs == us:
            out += chunk
        elif ctype in (3, 4):
            out += lz4_block(chunk, us)
        else:
            raise ValueError('compression type %d' % ctype)
    return bytes(out[:total])


BLOCK = {71: 8, 72: 8, 74: 16, 75: 16, 77: 16, 78: 16, 80: 8, 81: 8, 83: 16, 84: 16, 95: 16, 96: 16, 98: 16, 99: 16}
RAW = {28: 4, 29: 4, 87: 4, 91: 4, 61: 1, 49: 2}


def mip_bytes(fmt, w, h):
    if fmt in BLOCK:
        return ((w + 3) // 4) * ((h + 3) // 4) * BLOCK[fmt]
    if fmt in RAW:
        return w * h * RAW[fmt]
    raise ValueError('image format %d' % fmt)


def read_image_full(path):
    """GfxImage header + where the pixels are: 'embedded' bytes or 'streams' [(file, off, end, w, h)]."""
    d = open(path, 'rb').read()
    r = ztdump.Reader(d, path)
    n, h = r.array(ztdump.IMAGE_SIZE)
    if n != 1:
        raise ztdump.DumpError('no GfxImage header')
    name = r.text(ztdump.T_STRING)
    fmt, flags = struct.unpack_from('<II', h, 24)
    w, hh, depth, elems, levels, streamed = struct.unpack_from('<HHHHBB', h, 48)
    pix_ptr = struct.unpack_from('<Q', h, 64)[0]
    info = {'name': name, 'format': fmt, 'width': w, 'height': hh, 'levels': levels, 'streamed': bool(streamed),
            'semantic': h[33], 'map_type': h[32]}
    if pix_ptr:
        cnt, data = r.array(1)
        info['embedded'] = data
    streams = []
    if streamed:
        for i in range(4):
            cnt, sf = r.array(24)
            if cnt == 1:
                off, end, fi, loc = struct.unpack_from('<QQH?', sf, 0)
                if end > off:
                    sw, sh = struct.unpack_from('<HH', h, 72 + i * 8)
                    streams.append((fi, off, end, sw, sh))
    info['streams'] = streams
    return info


def _write_dds(path, fmt, w, h, data):
    hdr = bytearray(124)
    struct.pack_into('<IIIIIII', hdr, 0, 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000, h, w, len(data), 0, 1)
    struct.pack_into('<II4s', hdr, 72, 32, 0x4, b'DX10')
    struct.pack_into('<I', hdr, 104, 0x1000)
    open(path, 'wb').write(b'DDS ' + bytes(hdr) + struct.pack('<IIIII', fmt, 3, 0, 1, 0) + data)


def to_png(fmt, w, h, data, out_png):
    """Top-mip payload -> PNG with texconv (values kept as stored; colour maps are sRGB encoded)."""
    tmp = tempfile.mkdtemp(prefix='iwzpv_')
    try:
        src = os.path.join(tmp, 'i.dds')
        _write_dds(src, fmt, w, h, data[:mip_bytes(fmt, w, h)])
        cmd = [texconv_exe(), '-nologo', '-y', '-m', '1', '-ft', 'png', '-f', 'R8G8B8A8_UNORM', '-o', tmp, '--', src]
        r = subprocess.run(cmd, capture_output=True, text=True)
        p = os.path.join(tmp, 'i.png')
        if r.returncode != 0 or not os.path.isfile(p):
            raise RuntimeError('texconv: ' + (r.stdout + r.stderr)[-300:])
        os.makedirs(os.path.dirname(out_png), exist_ok=True)
        os.replace(p, out_png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def dds_to_png(dds, out_png):
    tmp = tempfile.mkdtemp(prefix='iwzpv_')
    try:
        cmd = [texconv_exe(), '-nologo', '-y', '-m', '1', '-ft', 'png', '-f', 'R8G8B8A8_UNORM', '-o', tmp, '--', dds]
        r = subprocess.run(cmd, capture_output=True, text=True)
        p = os.path.join(tmp, os.path.splitext(os.path.basename(dds))[0] + '.png')
        if r.returncode != 0 or not os.path.isfile(p):
            raise RuntimeError('texconv: ' + (r.stdout + r.stderr)[-300:])
        os.makedirs(os.path.dirname(out_png), exist_ok=True)
        os.replace(p, out_png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out_png


def image_png(index, name, game=None):
    """-> (png path or None, reason or None). Cached under <cache>/images/<name>.png."""
    out = os.path.join(cache_dir(), 'images', name.replace('/', '_').replace('$', '_').replace('&', '_') + '.png')
    if os.path.isfile(out):
        return out, None
    p = index.get('image', name)
    if not p:
        return None, 'image %s not in any dump' % name
    try:
        if p.endswith('.dds'):
            return dds_to_png(p, out), None
        im = read_image_full(p)
        fmt = im['format']
        if im.get('embedded'):
            to_png(fmt, im['width'], im['height'], im['embedded'], out)
            return out, None
        if not im['streams']:
            return None, 'image %s has no pixel data' % name
        fi, off, end, w, h = max(im['streams'], key=lambda s: s[3] * s[4])
        game = game or game_root()
        pak = os.path.join(game or '', 'imagefile%d.pak' % fi)
        if not game or not os.path.isfile(pak):
            return None, 'imagefile%d.pak not found (set IWZ_GAME_ROOT)' % fi
        with open(pak, 'rb') as f:
            f.seek(off)
            raw = f.read(end - off)
        to_png(fmt, w, h, iwc_unpack(raw), out)
        return out, None
    except Exception as e:  # report, never fake
        return None, 'image %s: %s' % (name, e)


# ---------------------------------------------------------------------------------------------------- materials
def colour_image_of(mat_json, with_evidence=False):
    """The colour map image of a material json. Evidence, in order: the texture with semantic 14 (stock lit techsets,
    '..._packed_cs'); else the only texture with semantic 2 (custom and unlit / emissive techsets); else the first
    semantic 2 when several exist (weak); else a name heuristic (weak). -> name, or (name, how) with with_evidence."""
    tt = mat_json.get('textureTable', [])
    s14 = [t['image'] for t in tt if t.get('semantic') == 14]
    s2 = [t['image'] for t in tt if t.get('semantic') == 2]
    res = (None, 'none')
    if s14:
        res = (s14[0], 'semantic 14' + (' (%d candidates)' % len(s14) if len(s14) > 1 else ''))
    elif len(s2) == 1:
        res = (s2[0], 'semantic 2')
    elif s2:
        res = (s2[0], 'WEAK: first of %d semantic 2 textures %s' % (len(s2), s2))
    else:
        for t in tt:
            n = t['image']
            if '_c_' in n or n.endswith('_col') or '_col_' in n or '_color' in n:
                res = (n, 'WEAK: name heuristic')
                break
    return res if with_evidence else res[0]


def material_info(index, name):
    """-> (dict, None) or (None, reason). dict: image (colour map), how (evidence), tint, techset, json, sort, textures,
    emissive_image + emissive_para (techset with an e0 / em0 slot: the semantic 2 map and the emissivePara constant),
    unlit (techset without lighting: colour * colorTint as light), occlusion_image (semantic 15 '..._nog' map: the
    occlusion lives in its R channel)."""
    import re
    cands = [name, name.replace('w/', '', 1) if name.startswith('w/') else 'w/' + name, 'mo/' + name]
    for c in cands:
        p = index.get('material', c)
        if p:
            m = json.load(open(p))
            tint, para = [1, 1, 1, 1], None
            for c_ in m.get('constantTable', []):
                if c_.get('name') == 'colorTint':
                    tint = c_['literal']
                elif c_.get('name') == 'emissivePara':
                    para = c_['literal'][0]
            ts = m.get('techniqueSet->name', '')
            img, how = colour_image_of(m, True)
            tt = m.get('textureTable', [])
            emi = None
            if re.search(r'[0-9_]em?0', ts) and any(t.get('semantic') == 14 for t in tt):
                emi = next((t['image'] for t in tt if t.get('semantic') == 2), None)
            occ = next((t['image'] for t in tt if t.get('semantic') == 15 and 'nog' in t['image']), None)
            return {'image': img, 'how': how, 'tint': tint, 'techset': ts, 'json': p, 'sort': m.get('sortKey'),
                    'textures': [t['image'] for t in tt], 'emissive_image': emi, 'emissive_para': para,
                    'unlit': 'unlit' in ts, 'occlusion_image': occ}, None
    return None, 'material %s not in any dump' % name


# ---------------------------------------------------------------------------------------------------- models
def _half(u16):
    return u16.astype(np.uint16).view(np.float16).astype(np.float32)


PV = np.dtype([('pos', '<f4', 3), ('sv', '<u4'), ('col', 'u1', 4), ('tc', '<u2', 2), ('n', '<u4'), ('t', '<u4')])


def read_surfs_full(path):
    """XModelSurfs -> list of {pos, tc, tris} per surface (ztdump.Reader walk that keeps faces and uv)."""
    d = open(path, 'rb').read()
    r = ztdump.Reader(d, path)
    n, h = r.array(ztdump.XSURFS_SIZE)
    r.text(ztdump.T_STRING)
    numsurfs = struct.unpack_from('<H', h, 16)[0]
    ns, sb = r.array(ztdump.XSURFACE_SIZE)
    out = []
    for i in range(numsurfs):
        s = sb[i * ztdump.XSURFACE_SIZE:(i + 1) * ztdump.XSURFACE_SIZE]
        flags, vcount, tcount, rvl, subdiv_levels = struct.unpack_from('<HHHBB', s, 0)
        subdiv_ptr = struct.unpack_from('<Q', s, 128)[0]
        nv, vb = r.array(32)
        nt, tb = r.array(6)
        nr, rb = r.array(16)
        for k in range(max(nr, 0)):
            tree_ptr = struct.unpack_from('<Q', rb, k * 16 + 8)[0]
            if rb and tree_ptr:
                _, tree = r.array(56)
                if struct.unpack_from('<Q', tree, 48)[0]:
                    r.array(2)
                if struct.unpack_from('<Q', tree, 32)[0]:
                    r.array(16)
        r.raw(); r.raw(); r.raw(); r.raw()
        if subdiv_ptr:
            _, sd = r.array(0x38)
            levels_ptr = struct.unpack_from('<Q', sd, 0)[0] if sd else 0
            if levels_ptr:
                r.array(0xE8)
                for _ in range(subdiv_levels):
                    for _ in range(10):
                        r.raw()
        if (flags & 0x500) == 0x500:
            r.array(32)
        elif flags & 0x100:
            r.array(8)
        elif flags & 0x400:
            r.array(24)
        v = np.frombuffer(vb, PV, nv)
        tris = np.frombuffer(tb, '<u2', nt * 3).reshape(-1, 3) if nt > 0 else np.zeros((0, 3), np.uint16)
        out.append({'pos': v['pos'].astype(np.float32), 'tc': v['tc'].copy(), 'tris': tris.astype(np.int64), 'flags': flags})
    return out


def unpack_uv(tc):
    """Packed texCoord (two 16 bit values at vertex offset 20) -> float32 (u, v), IEEE half floats."""
    return np.stack([_half(tc[:, 0]), _half(tc[:, 1])], 1)


def read_model(index, name):
    """-> (model dict, None) or (None, reason). LOD0: {'surfs': [{pos, uv, tris, material}], 'bounds': (mins, maxs)}"""
    p = index.get('xmodel', name)
    if not p:
        return None, 'xmodel %s not in any dump' % name
    try:
        m = ztdump.read_xmodel(p)
        lod = m['lods'][0]
        sp = index.get('xsurface', lod['surfs'])
        if not sp:
            return None, 'xsurface %s not in any dump' % lod['surfs']
        surfs = read_surfs_full(sp)
        mats = lod['materials']
        res = []
        for i, s in enumerate(surfs):
            res.append({'pos': s['pos'], 'uv': unpack_uv(s['tc']), 'tris': s['tris'],
                        'material': mats[i] if i < len(mats) else None})
        return {'name': name, 'surfs': res, 'bounds': (m['bounds']['mins'], m['bounds']['maxs']),
                'scale': m['scale']}, None
    except Exception as e:
        return None, 'xmodel %s: %s' % (name, e)
