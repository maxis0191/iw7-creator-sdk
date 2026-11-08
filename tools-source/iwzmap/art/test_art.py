"""Small self-test of the art generators (no model images needed).

usage (from tools-source/iwzmap): python -m art.test_art
Checks: determinism (same seed, same bytes), tileability of the tiling masks, feathered decals reaching alpha 0 on the
border, the DDS writer (header, mip count, byte size), and that the incident time / SERVICE SUSPENDED copy is what the
board renders.
"""
import hashlib
import os
import tempfile

import numpy as np

from . import blood, boards, masks, noise, texio


def h(a):
    return hashlib.sha256(np.ascontiguousarray(texio.to_u8(a)).tobytes()).hexdigest()


def main():
    fails = []

    def check(cond, msg):
        print(('PASS ' if cond else 'FAIL ') + msg)
        if not cond:
            fails.append(msg)

    # determinism
    a1, a2 = masks.decal_grime_feathered(128), masks.decal_grime_feathered(128)
    check(h(a1) == h(a2), 'decal_grime_feathered is deterministic')
    check(h(masks.water_streak(64, 256)) == h(masks.water_streak(64, 256)), 'water_streak is deterministic')
    # tileable masks: the wrap seam step is no larger than the interior step (ratio ~1)
    fl = masks.grime_mask_floor(256)
    sx, sy = noise.tile_seam_error(fl[..., :3])
    check(sx < 1.6 and sy < 1.6, 'grime_mask_floor tiles (seam/interior step x %.2f y %.2f)' % (sx, sy))
    jg = masks.junction_grime(256, 64)
    sx, _ = noise.tile_seam_error(jg[..., 3])
    check(sx < 1.6, 'junction_grime tiles horizontally (%.2f)' % sx)
    check(float(jg[0, :, 3].max()) < 0.02, 'junction_grime is clear on the top row')
    # feathered decals: zero alpha on the whole border
    for name, arr in [('blood_' + k, fn(128)) for k, fn in blood.VARIANTS.items()] + [
                      ('decal_grime_feathered', a1), ('water_streak', masks.water_streak(64, 256))]:
        border = np.concatenate([arr[0, :, 3], arr[-1, :, 3], arr[:, 0, 3], arr[:, -1, 3]])
        check(float(border.max()) < 0.01, '%s alpha is 0 on the border (max %.4f)' % (name, border.max()))
    # blood variants must differ in silhouette (not one blob reused): pairwise alpha IoU well below 1
    al = [fn(128)[..., 3] > 0.3 for fn in blood.VARIANTS.values()]
    ious = [float((x & y).sum()) / max(1.0, float((x | y).sum())) for i, x in enumerate(al) for y in al[i + 1:]]
    check(max(ious) < 0.5, 'blood variants have distinct silhouettes (max IoU %.2f)' % max(ious))
    # clock: alpha 0 in the corners, opaque in the centre
    ck = boards.clock_face_stopped(128)
    check(ck[0, 0, 3] == 0 and ck[64, 64, 3] > 0.99, 'clock face is a disc (corner alpha 0, centre opaque)')
    # DDS writer
    with tempfile.TemporaryDirectory() as td:
        info = texio.save_all(np.random.default_rng(1).random((64, 128, 4)), td, 't')
        di = texio.read_dds_info(os.path.join(td, 't_c.dds'))
        expect = sum(max(1, 128 >> i) * max(1, 64 >> i) * 4 for i in range(8)) + 128
        check(di['mips'] == 8 and di['width'] == 128 and di['height'] == 64 and di['bytes'] == expect,
              'DDS header and full mip chain (%s)' % di)
        check(os.path.getsize(os.path.join(td, 't_c.tga')) == 128 * 64 * 4 + 44, 'TGA is 32-bit uncompressed')
    # board copy
    check(all(r[3] == 'SERVICE SUSPENDED' for r in boards.BOARD_ROWS) and boards.INCIDENT == '23:47',
          'departure board rows all read SERVICE SUSPENDED, clock 23:47')
    print('FAILS', len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
