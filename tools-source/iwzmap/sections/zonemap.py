"""zonemap.json: which zone every render surface and every collision triangle of an emit belongs to.

Written by station_zero2.py next to world.bin / colmap.hkx; read by section_merge.py to cut whole zones out of the base
emit. Schema "iwz.zonemap/1":

  render.surfaces   one row per world.bin surface in file order: {zone, material, triangles}. A generator surface holds the
                    quads of one material and one zone (the render key is "<material>|<zone>"), so the zone is exact.
  collision         the exact collision triangles the generator encoded into colmap.hkx, with their zone and surface tag:
                    zones [names], tris [[x0,y0,z0,x1,y1,z1,x2,y2,z2] x N] in game units, tag [int|null x N],
                    zone_runs [[zone index, count], ...] (run length coded, same order as tris)
  check             collision triangles whose recorded zone was replaced by the nearest zone volume (see build())
"""
import json
import os

SCHEMA = 'iwz.zonemap/1'
CHUNK_INDICES = 30000 * 3      # mapgen.write_world: surfaces of at most 30,000 quads of 3 indices


def render_surfaces(mesh):
    """Per world.bin surface (file order): (zone, material, triangles). Mirrors mapgen.write_world's chunking."""
    out = []
    for key in mesh.materials:
        idx = mesh.by_mat[key][1]
        zone = key.split('|', 1)[1] if '|' in key else None
        base = key.split('|', 1)[0]
        start = 0
        while start < len(idx):
            end = min(len(idx), start + CHUNK_INDICES)
            out.append((zone, base, (end - start) // 3))
            start = end
    return out


def build(mesh, col_zone, zone_boxes, world_path=None):
    """mesh: mapgen.Mesh after write_world; col_zone: zone per mesh.col triangle; zone_boxes: {zone: (x0,y0,z0,x1,y1,z1)}."""
    surfaces = render_surfaces(mesh)
    if world_path:
        import struct
        b = open(world_path, 'rb').read()
        p = 8
        nm, = struct.unpack_from('<I', b, p); p += 4
        for _ in range(nm):
            ln, = struct.unpack_from('<H', b, p); p += 2 + ln
        nv, = struct.unpack_from('<I', b, p); p += 4 + 44 * nv
        ni, = struct.unpack_from('<I', b, p); p += 4 + 2 * ni
        ns, = struct.unpack_from('<I', b, p); p += 4
        tri = [struct.unpack_from('<5I', b, p + 44 * k)[4] for k in range(ns)]
        if tri != [s[2] for s in surfaces]:
            raise RuntimeError('zonemap: world.bin surfaces do not match the mesh chunking (%d vs %d)' % (len(tri), len(surfaces)))
    col_zone = list(col_zone) + [None] * (len(mesh.col) - len(col_zone))
    # The recorded zone is the generator's context (the zone of the last quad / collision call). Props, kit pieces and the
    # train are placed with their clip boxes while another zone is current, so a triangle whose centroid lies more than 48
    # units outside the volume of its recorded zone is moved to the zone whose volume is nearest (0 when inside one).
    def box_dist(bx, c):
        return sum(max(bx[a] - c[a], 0.0, c[a] - bx[a + 3]) ** 2 for a in range(3)) ** 0.5
    moved = {}
    fixed = []
    for t, z in zip(mesh.col, col_zone):
        c = [sum(p[a] for p in t) / 3 for a in range(3)]
        if z in zone_boxes and box_dist(zone_boxes[z], c) <= 48.0:
            fixed.append(z)
            continue
        if not zone_boxes:
            fixed.append(z)
            continue
        zn = min(zone_boxes, key=lambda k: (box_dist(zone_boxes[k], c), k))
        fixed.append(zn)
        key = '%s->%s' % (z, zn) if zn != z else '%s (far from its volume, kept)' % z
        moved[key] = moved.get(key, 0) + 1
    recorded = col_zone
    col_zone = fixed
    zones = []
    zi = {}
    for z in col_zone:
        if z not in zi:
            zi[z] = len(zones)
            zones.append(z)
    runs = []
    for z in col_zone:
        k = zi[z]
        if runs and runs[-1][0] == k:
            runs[-1][1] += 1
        else:
            runs.append([k, 1])
    tris = [[c for p in t for c in p] for t in mesh.col]
    tags = [mesh.col_tag.get(i) for i in range(len(mesh.col))]
    rz, cz_ = {}, {}
    for z, _, n in surfaces:
        rz[z] = rz.get(z, 0) + n
    for z in col_zone:
        cz_[z] = cz_.get(z, 0) + 1
    return {
        'schema': SCHEMA,
        'render': {'surfaces': [{'zone': z, 'material': m, 'triangles': n} for z, m, n in surfaces]},
        'collision': {'zones': zones, 'zone_runs': runs, 'tris': tris, 'tag': tags},
        'summary': {'render_triangles': rz, 'collision_triangles': cz_,
                    'render_without_zone': rz.get(None, 0), 'collision_without_zone': cz_.get(None, 0)},
        'check': {'collision_zone_moved_by_geometry': moved},
    }


def write(path, zm):
    with open(path, 'w', newline='\n') as f:
        json.dump(zm, f, separators=(',', ':'))


def read(path):
    return json.load(open(path))


def collision_zone_list(zm):
    """Expand zone_runs to one zone name per triangle."""
    zs = zm['collision']['zones']
    out = []
    for k, n in zm['collision']['zone_runs']:
        out.extend([zs[k]] * n)
    return out
