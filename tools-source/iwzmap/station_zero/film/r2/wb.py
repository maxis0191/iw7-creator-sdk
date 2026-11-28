import struct, numpy as np
VD = np.dtype([('pos', '<f4', 3), ('bs', '<f4'), ('col', 'u1', 4), ('uv', '<f4', 2), ('lm', '<f4', 2), ('n', '<u4'), ('t', '<u4')])
SD = np.dtype([('mat', '<u4'), ('first', '<u4'), ('vc', '<u4'), ('base', '<u4'), ('tc', '<u4'), ('mn', '<f4', 3), ('mx', '<f4', 3)])
def read_world(path):
    b = open(path, 'rb').read(); off = 8
    nm, = struct.unpack_from('<I', b, off); off += 4; mats = []
    for _ in range(nm):
        l, = struct.unpack_from('<H', b, off); off += 2; mats.append(b[off:off + l].decode()); off += l
    nv, = struct.unpack_from('<I', b, off); off += 4
    verts = np.frombuffer(b, VD, nv, off).copy(); off += nv * VD.itemsize
    ni, = struct.unpack_from('<I', b, off); off += 4
    idx = np.frombuffer(b, '<u2', ni, off).copy(); off += ni * 2
    ns, = struct.unpack_from('<I', b, off); off += 4
    surfs = np.frombuffer(b, SD, ns, off).copy(); off += ns * SD.itemsize
    return {'materials': mats, 'verts': verts, 'indices': idx, 'surfaces': surfs}
