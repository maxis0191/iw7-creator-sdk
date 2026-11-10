"""IW7 image and DDS helpers for the lightmap baker.

iw7Image (ZoneTool dump of a GfxImage): assetmanager stream
  [08 01][u32 1][GfxImage 0x70 bytes][06 01][name \\0][08 01][u32 length][pixels]
GfxImage fields used here (offset in the struct): imageFormat u32 @0x18, flags @0x1C, mapType u8 @0x20,
semantic u8 @0x21, category u8 @0x22 (2 = lightmap), dataLen1 @0x28, dataLen2 @0x2C, width u16 @0x30,
height u16 @0x32, depth @0x34, numElements @0x36, levelCount u8 @0x38, streamed u8 @0x39.

DDS: 'DDS ' + 124-byte header + DX10 header (dxgiFormat), single 2D surface, one mip.
Block compression goes through texconv (DirectXTex, GPU BC6H) - see encode().
"""
import os, struct, subprocess, tempfile
import numpy as np

TEXCONV = os.environ.get('IWZ_TEXCONV') or os.path.join(
    os.path.expanduser('~'), 'Documents', 'IW7-Tools', 'texconv-may2026', 'texconv.exe')

DXGI = {'R32G32B32A32_FLOAT': 2, 'R16G16B16A16_FLOAT': 10, 'R8G8_UNORM': 49, 'R8_UNORM': 61,
        'BC4_UNORM': 80, 'BC6H_UF16': 95}
BLOCK_BYTES = {80: 8, 95: 16}          # 4x4 block formats
PIXEL_BYTES = {2: 16, 10: 8, 49: 2, 61: 1}


def surface_size(fmt, w, h):
    if fmt in BLOCK_BYTES:
        return ((w + 3) // 4) * ((h + 3) // 4) * BLOCK_BYTES[fmt]
    return w * h * PIXEL_BYTES[fmt]


# ------------------------------------------------------------------ iw7Image
def read_iw7image(path):
    b = open(path, 'rb').read()
    if b[:2] != b'\x08\x01':
        raise ValueError('%s: not an iw7Image dump' % path)
    head = bytearray(b[6:6 + 0x70])
    p = 6 + 0x70
    if b[p:p + 2] != b'\x06\x01':
        raise ValueError('%s: name missing' % path)
    end = b.index(b'\x00', p + 2)
    name = b[p + 2:end].decode()
    p = end + 1
    if b[p:p + 2] != b'\x08\x01':
        raise ValueError('%s: pixel data missing' % path)
    length = struct.unpack_from('<I', b, p + 2)[0]
    data = b[p + 6:p + 6 + length]
    fmt, = struct.unpack_from('<I', head, 0x18)
    w, h = struct.unpack_from('<HH', head, 0x30)
    return {'name': name, 'header': head, 'format': fmt, 'width': w, 'height': h, 'data': data}


def write_iw7image(path, template_header, name, fmt, w, h, data):
    """Write an iw7Image with the template header (flags, semantic, category) and a new format/size/payload."""
    head = bytearray(template_header)
    if len(data) != surface_size(fmt, w, h):
        raise ValueError('payload %d bytes, expected %d' % (len(data), surface_size(fmt, w, h)))
    struct.pack_into('<I', head, 0x18, fmt)
    struct.pack_into('<II', head, 0x28, len(data), len(data))
    struct.pack_into('<HHHH', head, 0x30, w, h, 1, 1)
    head[0x38] = 1    # levelCount
    head[0x39] = 0    # not streamed
    out = bytearray(b'\x08\x01' + struct.pack('<I', 1)) + head
    out += b'\x06\x01' + name.encode() + b'\x00'
    out += b'\x08\x01' + struct.pack('<I', len(data)) + data
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, 'wb').write(out)


# ------------------------------------------------------------------ DDS
def write_dds(path, fmt, w, h, data):
    hdr = bytearray(124)
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000         # caps height width pixelformat linearsize
    struct.pack_into('<IIIIIII', hdr, 0, 124, flags, h, w, len(data), 0, 1)
    struct.pack_into('<II4s', hdr, 72, 32, 0x4, b'DX10')  # pixel format: FOURCC DX10
    struct.pack_into('<I', hdr, 104, 0x1000)               # caps: texture
    dx10 = struct.pack('<IIIII', fmt, 3, 0, 1, 0)          # dxgi format, TEXTURE2D, flags, array 1, misc
    with open(path, 'wb') as f:
        f.write(b'DDS ' + hdr + dx10 + data)


def read_dds(path):
    b = open(path, 'rb').read()
    if b[:4] != b'DDS ':
        raise ValueError('%s: not a DDS file' % path)
    h, w = struct.unpack_from('<II', b, 12)
    fourcc = b[84:88]
    if fourcc == b'DX10':
        fmt = struct.unpack_from('<I', b, 128)[0]
        off = 148
    else:
        fmt = {b'ATI1': 80, b'BC4U': 80}.get(fourcc)
        if fmt is None:
            raise ValueError('%s: unsupported legacy DDS %r' % (path, fourcc))
        off = 128
    size = surface_size(fmt, w, h)
    return fmt, w, h, b[off:off + size]


def texconv(src, fmt, outdir, extra=()):
    os.makedirs(outdir, exist_ok=True)
    cmd = [TEXCONV, '-nologo', '-y', '-dx10', '-m', '1', '-f', fmt, '-o', outdir] + list(extra) + ['--', src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + '.dds')
    if r.returncode != 0 or not os.path.isfile(out):
        raise RuntimeError('texconv failed (%d): %s %s' % (r.returncode, r.stdout[-800:], r.stderr[-800:]))
    return out


# ------------------------------------------------------------------ encode / decode
def encode(arr, fmt, work=None):
    """arr: float32 HxWxC (C = 1, 2 or 3/4). Returns the payload in the given DXGI format name."""
    h, w = arr.shape[:2]
    if fmt == 'R8G8_UNORM':
        q = np.clip(np.round(arr[..., :2] * 255.0), 0, 255).astype(np.uint8)
        return q.tobytes()
    if fmt == 'R8_UNORM':
        return np.clip(np.round(arr.reshape(h, w) * 255.0), 0, 255).astype(np.uint8).tobytes()
    tmp = work or tempfile.mkdtemp(prefix='iwzlm_')
    os.makedirs(tmp, exist_ok=True)
    if fmt == 'BC4_UNORM':
        src = os.path.join(tmp, 'enc_r8.dds')
        write_dds(src, DXGI['R8_UNORM'], w, h, encode(arr, 'R8_UNORM'))
    elif fmt == 'BC6H_UF16':
        rgba = np.zeros((h, w, 4), np.float32)
        rgba[..., :3] = np.maximum(arr[..., :3], 0.0)
        rgba[..., 3] = 1.0
        src = os.path.join(tmp, 'enc_rgba32f.dds')
        write_dds(src, DXGI['R32G32B32A32_FLOAT'], w, h, rgba.astype('<f4').tobytes())
    else:
        raise ValueError(fmt)
    out = texconv(src, fmt, os.path.join(tmp, 'bc'))
    f, ow, oh, data = read_dds(out)
    if (f, ow, oh) != (DXGI[fmt], w, h):
        raise RuntimeError('texconv wrote %s %dx%d' % (f, ow, oh))
    return data


def decode(fmt, w, h, data, work=None):
    """Payload -> float32 HxWx4 (RGBA order; R8G8 -> (r, g, 0, 1); BC4/R8 -> (r, 0, 0, 1))."""
    if fmt == 49:
        rg = np.frombuffer(data, np.uint8).reshape(h, w, 2).astype(np.float32) / 255.0
        out = np.zeros((h, w, 4), np.float32); out[..., :2] = rg; out[..., 3] = 1
        return out
    if fmt == 61:
        r = np.frombuffer(data, np.uint8).reshape(h, w).astype(np.float32) / 255.0
        out = np.zeros((h, w, 4), np.float32); out[..., 0] = r; out[..., 3] = 1
        return out
    tmp = work or tempfile.mkdtemp(prefix='iwzlm_')
    os.makedirs(tmp, exist_ok=True)
    src = os.path.join(tmp, 'dec_%d.dds' % fmt)
    write_dds(src, fmt, w, h, data)
    out = texconv(src, 'R32G32B32A32_FLOAT', os.path.join(tmp, 'f32'))
    f, ow, oh, raw = read_dds(out)
    return np.frombuffer(raw, '<f4').reshape(h, w, 4).copy()
