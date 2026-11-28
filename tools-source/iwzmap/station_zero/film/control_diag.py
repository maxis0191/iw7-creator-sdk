r"""control_diag: why the lifted room's floor, vault and stair treads are not on screen (worker C1, 28 Nov 2026).

    python control_diag.py <out doc>

The control document (control_doc --base-only, bounce) shows walls, pillars, beams and props of the lifted cp_disco station, but at the
platform floor, the vault and the stair treads the frame holds the fog colour (display 1/255, untextured x12), while `studio pick` hits
the lifted floor (`w/concrete_bare_patches_clean_03`, z -114) at those pixels and the bake has its texels (E 0.142 baked). This document
adds, beside the unchanged room, probes that separate the causes in one frame of pose 1 (ctl_subway_east_1):
  slabs     B.box slabs, flat and upright, in the three materials of the missing surfaces: material / technique set
  mesh      the lifted platform-floor triangles of the sightline (x 700..1100, y 2450..2700) re-added as ONE B.mesh with their shipped UVs, 1 unit
            higher: the authored record path instead of `kind: prefab` records
  under     a lamp-material box 16 units under the platform: if the floor is not drawn, it shows through
Not testable here: a zone over the room (the Terminus, which draws its floor, has one): an island zone over the lifted room gets no
navigation cells even with a collision strip and a marker seed (ISLAND_NO_NAV, TOOL-FAULTS C1-2), and `check` refuses it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import numpy as np  # noqa: E402
from studio import build as B  # noqa: E402
from studio import prefab as P  # noqa: E402
import control_doc  # noqa: E402
import control_room as CR  # noqa: E402

MATS = ('w/concrete_bare_patches_clean_03', 'w/concrete_wall_grunge_01', 'w/dt_tile_ceramic_white')
FLOOR_Z = 286.12


def floor_mesh_tris():
    """the lifted platform-floor triangles in the sightline box, document frame, counter clockwise, with their shipped UVs"""
    pre = P.load(CR.PREFAB)
    o = np.array(CR.prefab_origin())
    tris, uvs = [], []
    for s in pre.surfaces():
        if P.render_material(pre, s['material']) != MATS[0]:
            continue
        Pp = np.array(s['pos'], float) + o
        UV = s['uv']
        for a, b, c in s['tris']:
            cc = (Pp[a] + Pp[b] + Pp[c]) / 3.0
            if not (700 <= cc[0] <= 1100 and 2450 <= cc[1] <= 2700 and abs(cc[2] - FLOOR_Z) < 3):
                continue
            t = []
            for i in (a, c, b):                    # shipped winding is clockwise: reversed
                q = CR.to_doc(Pp[i])
                t.append((q[0], q[1], q[2] + 1.0))
            tris.append(t)
            uvs.append([(UV[i][0], 1.0 - UV[i][1]) for i in (a, c, b)])
    return tris, uvs


def main(argv):
    out = argv[0]
    m, rep = control_doc.build('bounce', whole=False)
    m.name = 'sz_control_diag'
    m.use('ctl_diag')
    for k, mat in enumerate(MATS):
        x0 = 860.0 + k * 50.0
        f0, f1 = CR.to_doc((x0, 2520.0, FLOOR_Z + 2.0)), CR.to_doc((x0 + 40.0, 2560.0, FLOOR_Z + 4.0))
        B.box(m, f0 + f1, mat, mode='render', id='ctl_diag_flat_%d' % k)
        u0, u1 = CR.to_doc((x0, 2600.0, FLOOR_Z)), CR.to_doc((x0 + 40.0, 2604.0, FLOOR_Z + 48.0))
        B.box(m, u0 + u1, mat, mode='render', id='ctl_diag_up_%d' % k)
    tris, uvs = floor_mesh_tris()
    B.mesh(m, MATS[0], tris=tris, uvs=uvs, mode='render', id='ctl_diag_floor_mesh')
    a, b = CR.to_doc((760.0, 2460.0, FLOOR_Z - 20.0)), CR.to_doc((1040.0, 2700.0, FLOOR_Z - 16.0))
    B.box(m, a + b, 'w/iwz_lamp_warm', mode='render', id='ctl_diag_under')
    os.makedirs(out, exist_ok=True)
    m.save(out)
    print(json.dumps({'folder': out, 'floor_mesh_triangles': len(tris), 'summary': m.summary()}, indent=1, default=str))


if __name__ == '__main__':
    main(sys.argv[1:])
