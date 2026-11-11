"""Read IW7 shader bytecode (.cso = DXBC, shader model 5) as text.

  python shader_read.py dis <file.cso> [--out <file.txt>]       disassembly (stock IW7 shaders carry no RDEF: no names)
  python shader_read.py chunks <file.cso>                       DXBC chunk list + stored/computed checksum
  python shader_read.py technique <file.technique>              shader hashes, decl and binding table of a technique
  python shader_read.py cbt <material.cbt>                      a material's literal constant buffers + offset maps
  python shader_read.py grep <dir> <regex> [--max N]            disassemble every .cso in <dir>, list files whose text matches

Uses C:\\Windows\\System32\\d3dcompiler_47.dll (D3DDisassemble) through ctypes. The DXBC container and its checksum are
read by dxbc.py (same folder).
"""
import argparse, ctypes, json, os, re, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxbc  # noqa: E402


def _read(path):
    with open(path, 'rb') as f:
        return f.read()

_dll = None


def _d3d():
    global _dll
    if _dll is None:
        _dll = ctypes.WinDLL(os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'd3dcompiler_47.dll'))
        _dll.D3DDisassemble.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        _dll.D3DDisassemble.restype = ctypes.c_long
    return _dll


def _blob_bytes(blob):
    vt = ctypes.cast(ctypes.cast(blob, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    ptr = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p)(vt[3])(blob)
    size = ctypes.WINFUNCTYPE(ctypes.c_size_t, ctypes.c_void_p)(vt[4])(blob)
    data = ctypes.string_at(ptr, size)
    ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vt[2])(blob)
    return data


def disassemble(data, flags=0):
    """D3DDisassemble text of a DXBC blob; raises on a malformed blob (the API refuses a bad container)"""
    buf = ctypes.create_string_buffer(bytes(data), len(data))
    out = ctypes.c_void_p()
    hr = _d3d().D3DDisassemble(buf, len(data), flags, None, ctypes.byref(out))
    if hr != 0 or not out.value:
        raise RuntimeError('D3DDisassemble failed hr=0x%08x' % (hr & 0xffffffff))
    return _blob_bytes(out.value).decode('latin-1').rstrip('\0')


_device = None


def runtime_accepts(data, stage='ps'):
    """True when a D3D11 device (WARP, software: no game, no GPU state) creates the shader from these bytes. This is
    the check the game's own CreateVertexShader/CreatePixelShader makes, checksum included."""
    global _device
    if _device is None:
        d3d11 = ctypes.WinDLL('d3d11.dll')
        dev = ctypes.c_void_p()
        hr = d3d11.D3D11CreateDevice(None, 5, None, 0, None, 0, 7, ctypes.byref(dev), None, None)  # 5 = WARP
        if hr != 0:
            raise RuntimeError('D3D11CreateDevice(WARP) failed hr=0x%08x' % (hr & 0xffffffff))
        _device = dev
    vt = ctypes.cast(ctypes.cast(_device, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    index = {'vs': 12, 'ps': 15}[stage]              # ID3D11Device::CreateVertexShader / CreatePixelShader
    fn = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                            ctypes.POINTER(ctypes.c_void_p))(vt[index])
    buf = ctypes.create_string_buffer(bytes(data), len(data))
    out = ctypes.c_void_p()
    hr = fn(_device, buf, len(data), None, ctypes.byref(out))
    if hr == 0 and out.value:
        ovt = ctypes.cast(ctypes.cast(out, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
        ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(ovt[2])(out)
        return True
    return False


ARG_KINDS ={0: 'code-buffer', 1: 'code-texture', 2: 'code-sampler', 3: 'material-constant', 5: 'material-texture',
             6: 'material-sampler'}
STAGES = {0x02: 'vs', 0x10: 'ps', 0x12: 'vs+ps'}


def technique_refs(path):
    """Names and the argument (binding) table of a ZoneTool .technique dump.

    Strings are stored 0x01-prefixed and NUL-ended: technique name, vertex shader hash, vertex declaration, pixel
    shader hash. The binding table follows the pixel shader name as an array (0x08 0x01 u32 count) of 16-byte
    records <u8 kind, u8 stage mask, u16 slot, u32 0, u32 value, u32 0>: kind 3 = material constant (value = name
    hash, slot = register of cb3), kind 5 = material texture (value = typeHash, slot = t register), kind 6 = its
    sampler (s register), kinds 0-2 = code buffers / textures / samplers (value = code id).
    Read 2026-11-11 from the lprobe_specenv weapon technique; matches the shader's own dcl_ registers."""
    raw = _read(path)
    names = [m.group(1).decode() for m in re.finditer(rb'\x01([\x20-\x7e]{4,})\x00', raw)]
    hexes = [n for n in names if re.fullmatch(r'[0-9a-f]{16}', n)]
    decl = [n for n in names if n.startswith('pp.')]
    args = []
    if hexes:
        at = raw.rfind(hexes[-1].encode() + b'\x00') + 17
        j = raw.find(b'\x08\x01', at)
        if j >= 0:
            count = struct.unpack_from('<I', raw, j + 2)[0]
            p = j + 6
            if p + 16 * count <= len(raw):
                for _ in range(count):
                    kind, stage, slot, _a, value, _b = struct.unpack_from('<BBHIII', raw, p)
                    p += 16
                    args.append({'kind': ARG_KINDS.get(kind, kind), 'stage': STAGES.get(stage, hex(stage)),
                                 'slot': slot, 'value': value})
    return {'names': names, 'shaders': hexes, 'decl': decl[:1], 'args': args}


def read_cbt(path):
    """Literal constant buffers of one material in one techset (ZoneTool techsets/constantbuffer/<ts>/<mat>.cbt):
    u8 tag 3 + u32 count, then MaterialConstantBufferDef[count] (128 bytes: 8 u32 sizes + 8 pointers), then per def
    its vs/hs/ds/ps data and the vs/hs/ds/ps offset arrays (u16 per material constant, 0xffff = not in that stage),
    each array written as 0x08 0x01 u32 count + bytes. Returns [{stage: [vec4...], stage+'Offsets': [...]}]."""
    d = _read(path)
    if d[0] != 3:
        raise ValueError('not a cbt dump')
    count = struct.unpack_from('<I', d, 1)[0]
    p = [5]

    def arr():
        if d[p[0]] != 8 or d[p[0] + 1] != 1:
            raise ValueError('array marker expected at %d' % p[0])
        n = struct.unpack_from('<I', d, p[0] + 2)[0]
        p[0] += 6
        return n
    arr()
    defs = [struct.unpack_from('<8I', d, p[0] + 128 * i) for i in range(count)]
    p[0] += 128 * count
    out = []
    for df in defs:
        rec = {}
        for k, st in enumerate(('vs', 'hs', 'ds', 'ps')):
            if df[k]:
                n = arr()
                f = struct.unpack_from('<%df' % (n // 4), d, p[0]); p[0] += n
                rec[st] = [list(f[i:i + 4]) for i in range(0, len(f), 4)]
        for k, st in enumerate(('vs', 'hs', 'ds', 'ps')):
            if df[4 + k]:
                n = arr()
                rec[st + 'Offsets'] = list(struct.unpack_from('<%dH' % n, d, p[0])); p[0] += 2 * n
        out.append(rec)
    if p[0] != len(d):
        raise ValueError('trailing bytes: %d of %d read' % (p[0], len(d)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dis'); d.add_argument('cso'); d.add_argument('--out')
    c = sub.add_parser('chunks'); c.add_argument('cso')
    t = sub.add_parser('technique'); t.add_argument('path')
    b = sub.add_parser('cbt'); b.add_argument('path')
    g = sub.add_parser('grep'); g.add_argument('dir'); g.add_argument('regex'); g.add_argument('--max', type=int, default=50)
    a = ap.parse_args(argv)
    if a.cmd == 'dis':
        text = disassemble(_read(a.cso))
        if a.out:
            open(a.out, 'w', encoding='utf-8').write(text)
            print('%s: %d lines' % (a.out, text.count('\n')))
        else:
            sys.stdout.write(text)
    elif a.cmd == 'chunks':
        blob = dxbc.Container.parse(_read(a.cso))
        print('stored  %s\ncomputed %s' % (blob.stored_checksum.hex(), dxbc.checksum(blob.raw).hex()))
        for name, body in blob.chunks:
            print('%s %6d bytes' % (name, len(body)))
    elif a.cmd == 'technique':
        t = technique_refs(a.path)
        print('names   %s\nshaders %s\ndecl    %s' % (t['names'][0] if t['names'] else '', t['shaders'], t['decl']))
        for x in t['args']:
            print('  %-17s %-5s slot %-3d %d' % (x['kind'], x['stage'], x['slot'], x['value']))
    elif a.cmd == 'cbt':
        print(json.dumps(read_cbt(a.path), indent=1))
    elif a.cmd == 'grep':
        rx = re.compile(a.regex); n = 0
        for f in sorted(os.listdir(a.dir)):
            if not f.endswith('.cso'):
                continue
            try:
                text = disassemble(_read(os.path.join(a.dir, f)))
            except RuntimeError:
                continue
            if rx.search(text):
                print(f); n += 1
                if n >= a.max:
                    break


if __name__ == '__main__':
    main()
